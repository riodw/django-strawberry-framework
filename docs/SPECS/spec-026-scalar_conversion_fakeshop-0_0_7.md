# Spec: Scalar conversion end-to-end coverage in the fakeshop example

Target release: `0.0.7` (per [KANBAN.md][kanban] card `DONE-026-0.0.7`).
Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-026-0.0.7`.
Owner: package maintainer.

The alternatives the decisions rejected live in [`spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md`][spec-026-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout:

- [`BigInt` scalar][glossary-bigint-scalar] — the GraphQL scalar both `BigIntegerField` and `PositiveBigIntegerField` convert to. It serializes as a **decimal string**, which is the property this card's boundary values exist to prove.
- [`DjangoType`][glossary-djangotype] — the Meta-class surface the two coverage models are exposed through. This card adds two `DjangoType` subclasses and changes nothing about the class itself.
- [`finalize_django_types`][glossary-finalize-django-types] — the consumer-owned synchronization point the example project already calls in [`examples/fakeshop/config/schema.py`][example-schema]. This card adds types it resolves; it does not move or re-time the call.

## Card snapshot

- Card: `DONE-026-0.0.7`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

**What `apps.scalars` carries beyond this card.** The app is the fakeshop's converter-and-boundary workshop, and other cards own most of it: `ScalarSpecimenTag` and `ScalarSpecimen.tag` (the optimizer's `Prefetch`-downgrade substrate), `Base36Field` and `OverrideSpecimen` (consumer field overrides), `MediaSpecimen` and `migrations/0002_media_specimen_optional_files.py` (file / image conversion and the `Upload` mutation input), `filters.py`, `orders.py`, `forms.py`, the `Mutation` type, every root query field other than the two below, the `tag` entry and the `filterset_class` / `orderset_class` keys on [`ScalarSpecimenType`][scalars-schema] and `NullableScalarSpecimenType`, the live tests in [`test_query/test_scalars_api.py`][test-scalars-api] other than the nine below, and `apps/scalars/tests/test_models.py`. This card owns the paired models, their two `DjangoType`s, the two root query fields, and the live tests below.

## Problem statement

The package's converter table, [`django_strawberry_framework/types/converters.py`][converters] `SCALAR_MAP`, has twenty-six rows. Sixteen map to plain `int` or plain `str`. Fourteen of those read as a bare JSON number or a bare JSON string, and the example project's other live tests read columns of both kinds in the ordinary course of asserting anything; the other two, `FileField` and `ImageField`, keep `str` for the filter-input side only and read through the structured output objects of `FIELD_OUTPUT_TYPE_MAP` in [`converters.py`][converters], which `MediaSpecimen` covers outside this card. **Ten do not collapse** — `BigIntegerField` and `PositiveBigIntegerField` (both to [`BigInt`][glossary-bigint-scalar]), `BooleanField`, `FloatField`, `DecimalField`, `DateField`, `DateTimeField`, `TimeField`, `JSONField`, and `UUIDField` — and each of those ten produces two distinct GraphQL shapes: a `NON_NULL` wrapper when the Django column is required, and a bare `SCALAR` when it is nullable.

A package-internal test standing up a synthetic `managed = False` model can read those twenty shapes out of a schema but asserts nothing over HTTP. Pinning them that way violates the repository's live-first coverage rule ([`AGENTS.md`][agents] #"Test through real usage, prefer the example project"): a wire format reachable by a real GraphQL query against the fakeshop must be pinned by a live `/graphql/` HTTP test. A synthetic-model schema read also cannot prove the serialization survives the full request path — which for `BigInt` is the whole point, since a value past JSON's safe-integer boundary is lost the moment anything in the path treats it as a number.

## Goals

1. Each of the ten non-trivial `SCALAR_MAP` rows is exercised over live `/graphql/` HTTP in **both** shapes — the `NON_NULL` wrapper and the bare `SCALAR`.
2. The two shapes of a given row are exercised over the **same column name**, so a single introspection assertion can compare them.
3. The `BigIntegerField` -> [`BigInt`][glossary-bigint-scalar] row is additionally pinned on a real-domain model, at a value past `2**53 - 1`, so the decimal-string wire format is proved rather than assumed.
4. Two relation shapes on the coverage models are exercised under the optimizer: `ScalarSpecimen.parent`, an intra-model self-FK with its reverse `children` accessor, and `NullableScalarSpecimen.partner`, a nullable cross-model FK whose detach is observable over HTTP.
5. No package-internal test duplicates what the live coverage pins, so no assertion is paid for twice.

## Non-goals

1. **`ArrayField` and `HStoreField`.** Both are PostgreSQL-only and the fakeshop runs on SQLite, so neither can be exercised from a live fakeshop request at all. Neither has a `SCALAR_MAP` row of its own — they are sentinel-guarded branches in [`converters.py`][converters] `::convert_scalar` — and their coverage stays in `tests/` against package-internal fixtures. The exclusion is recorded in [`apps/scalars/models.py`][scalars-models]'s module docstring so the next reader of the app does not add them.
2. **The sixteen trivial-collapse rows.** A column mapped to plain `int` or plain `str` is already read over HTTP wherever the other example apps select one; adding a column per row here would buy nothing.
3. **A write, filter or order surface.** This card ships two read-only root query fields and no mutation, `FilterSet`, or `OrderSet`; the app's `Mutation`, `filters.py`, and `orders.py` belong to other cards ([Card snapshot](#card-snapshot)).
4. **Package source changes.** No file under `django_strawberry_framework/` is touched, `__all__` is unchanged, and no new public export lands.
5. **The version bump.** `0.0.7` is a joint cut; this card does not move `__version__`.

## Slice checklist

- [ ] Slice 1: the `apps.scalars` substrate and its live tests
  - [ ] New example app at `examples/fakeshop/apps/scalars/` with [`apps.py`][scalars-apps] (`ScalarsConfig`, `name = "apps.scalars"`), [`models.py`][scalars-models], [`schema.py`][scalars-schema], and `migrations/0001_initial.py`.
  - [ ] `ScalarSpecimen` — a `label` `TextField` handle plus exactly one column per each of the ten non-trivial converter rows, **none nullable**, so every one of the ten introspects with its `NON_NULL` wrapper.
  - [ ] `ScalarSpecimen.parent` — self-FK (`"self"`, `null=True`, `related_name="children"`, `on_delete=CASCADE`), per [Decision 3](#decision-3--the-two-relation-shapes-and-what-each-is-for).
  - [ ] `NullableScalarSpecimen` — the same eleven columns with `null=True, blank=True`, so the same ten rows introspect as bare `SCALAR`, per [Decision 1](#decision-1--paired-models-not-one-model-with-paired-columns).
  - [ ] `NullableScalarSpecimen.partner` — nullable cross-model FK to `ScalarSpecimen` (`on_delete=SET_NULL`, `related_name="nullable_partners"`), per [Decision 3](#decision-3--the-two-relation-shapes-and-what-each-is-for).
  - [ ] `ScalarSpecimenType` and `NullableScalarSpecimenType` in [`schema.py`][scalars-schema], each selecting every converted column; `ScalarSpecimenType` additionally selects `parent`, `children`, and `nullable_partners`.
  - [ ] Two root fields, `all_scalar_specimens` and `all_nullable_scalar_specimens`, on the app's `Query`, composed into the project root `Query` at [`examples/fakeshop/config/schema.py`][example-schema]; `ScalarsConfig` added to `INSTALLED_APPS` at [`examples/fakeshop/config/settings.py`][settings].
  - [ ] The nine live tests in [`test_query/test_scalars_api.py`][test-scalars-api] listed in the [Test plan](#test-plan).
- [ ] Slice 2: the real-domain `BigInt` row
  - [ ] `Patron.lifetime_fines_cents = BigIntegerField(default=0)` in [`apps/library/models.py`][library-models], selected in [`apps/library/schema.py`][library-schema] `::PatronType`'s `Meta.fields`.
  - [ ] One live test in [`test_query/test_library_api.py`][test-library-api] selecting `lifetimeFinesCents` at a value past `2**53 - 1`, per [Decision 4](#decision-4--bigint-is-pinned-twice).
- [ ] Slice 3: live-first posture and standing docs
  - [ ] [`tests/types/test_converters.py`][test-converters] carries no test the live pair duplicates, per [Decision 5](#decision-5--no-package-test-duplicates-the-live-coverage).
  - [ ] [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban], [`docs/TREE.md`][tree], and [`TODAY.md`][today] per [Doc updates](#doc-updates).

## Architectural decisions

### Decision 1 — Paired models, not one model with paired columns

The card ships two models over one identical set of eleven column names: `ScalarSpecimen` with every one required, `NullableScalarSpecimen` with every one `null=True, blank=True`.

The pairing is what makes the introspection assertions mean anything. Both shapes of a converter row are then produced **from the same column name by the same table row**, so `ScalarSpecimenType.signedBig` and `NullableScalarSpecimenType.signedBig` differ in exactly one respect — the `NON_NULL` wrapper — and an assertion comparing them is an assertion about the converter's nullability branch and nothing else. A schema query can also traverse both halves in one round-trip, which is what the relation in [Decision 3](#decision-3--the-two-relation-shapes-and-what-each-is-for) is for.

Rationale companion — the rejected single-model alternative: [Decision 1][spec-026-rationale-d1].

### Decision 2 — The coverage lives in the live `/graphql/` tier

The app is a real Django app in the example project's `INSTALLED_APPS`, its `Query` is composed into the project root `Query`, and every assertion is made against a response body from `/graphql/` over HTTP via `django.test.Client`. No assertion in this card is made against a locally constructed schema.

This follows [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" and is the reason the card exists rather than being a `tests/` change: a synthetic `managed = False` model has no table, so its converter row can be read out of a schema but never round-tripped through a query.

### Decision 3 — The two relation shapes, and what each is for

`ScalarSpecimen.parent` is an **intra-model** self-FK with `related_name="children"`. It gives the example a nullable forward FK, a reverse FK accessor, and recursive `select_related` / `prefetch_related` planning against a model whose relation target is itself.

`NullableScalarSpecimen.partner` is a **cross-model** nullable FK to `ScalarSpecimen` with `related_name="nullable_partners"` and `on_delete=SET_NULL`. `SET_NULL` rather than `CASCADE` because every field `NullableScalarSpecimen` declares is nullable: losing the target must clear `partner_id` and leave the mirror row in place. That end-to-end shape — the source row still present, `partner` resolving to `null` after the target is deleted — is pinned live by [`test_query/test_scalars_api.py`][test-scalars-api] `::test_scalars_set_null_ondelete_detaches_partner_in_http_query`, which belongs to a later card and is not among this card's nine tests below.

The reverse side, `ScalarSpecimenType.nullable_partners`, is selected too, so one query can traverse the link in both directions.

Rationale companion — why the edge is described locally rather than ranked in a population: [Decision 3][spec-026-rationale-d3].

### Decision 4 — `BigInt` is pinned twice

The [`BigInt`][glossary-bigint-scalar] row is exercised on this card's coverage models **and** on `apps.library`'s `Patron`, a real-domain model with a plausible reason to hold a 64-bit counter.

The coverage models prove the converter row; `Patron` proves it keeps working on a model that was not designed around it. The boundary values are chosen to sit outside JSON's safe-integer range — `9223372036854775000` in the wire-format sweep, `9007199254752336` in the library test — because inside that range a numeric round-trip and a decimal-string round-trip are indistinguishable, and the wire contract is the decimal string. Zero is the deliberate exception, pinned by its own test so that a value needing no precision at all still serializes as `"0"`.

### Decision 5 — No package test duplicates the live coverage

The `BigInt` and `JSON` field-mapping introspection and round-trip assertions live only in the live tier. [`tests/types/test_converters.py`][test-converters] stands up no synthetic `managed = False` owner model to read a `BigIntegerField`, `PositiveBigIntegerField`, or `JSONField` conversion out of a schema; its `BigInt` section keeps only the cases no real query reaches, which are not this card's.

Package coverage of the underlying rows is earned through the live tests. This is the standing live-first posture, not a coverage trade: a package test that survives its live replacement is the shape the rule exists to remove.

### Decision 6 — No package source change

Nothing under `django_strawberry_framework/` is touched by this card. It is coverage over behavior that already shipped, `__all__` is unchanged, and no consumer-visible surface moves. The version bump belongs to the last card in the joint `0.0.7` cut.

## Test plan

### `examples/fakeshop/test_query/test_scalars_api.py` (new) — nine live tests

Live `/graphql/` HTTP via `django.test.Client`, per [Decision 2](#decision-2--the-coverage-lives-in-the-live-graphql-tier).

- `test_scalar_specimen_every_field_wire_format_over_http` — the non-null sweep: every converted column on `ScalarSpecimen` selected in one query, each asserted against its expected wire form.
- `test_scalar_specimen_bigint_negative_signed_round_trip` — signed `BigInt` past the negative safe-integer floor survives as a decimal string.
- `test_scalar_specimen_bigint_zero_serializes_as_string` — the zero edge: `"0"`, not the JSON number `0`.
- `test_scalar_specimen_self_referential_parent_children_over_http` — the self-FK forward hop and the reverse `children` traversal in one response.
- `test_scalar_specimen_introspects_bigint_scalar_for_both_fields` — both halves of the `BigInt` row (`signed_big` from `BigIntegerField`, `unsigned_big` from `PositiveBigIntegerField`) introspect as `NON_NULL` over `BigInt` on `ScalarSpecimenType` and as bare `SCALAR` on `NullableScalarSpecimenType`.
- `test_scalar_specimen_introspects_json_scalar_in_both_shapes` — the same two-shape assertion for `payload` and the `JSONField` -> `JSON` row.
- `test_nullable_scalar_specimen_all_null_wire_format_over_http` — every nullable column serializes as JSON `null` when the column is `NULL`, covering the nullable branch of all ten rows in one response.
- `test_nullable_scalar_specimen_partner_fk_linkage_over_http` — the cross-model `partner` FK round-trip.
- `test_scalar_specimen_nullable_partners_reverse_relation_over_http` — the reverse side, `ScalarSpecimenType.nullable_partners`.

### `examples/fakeshop/test_query/test_library_api.py` — one added live test

- `test_library_patron_bigint_lifetime_fines_over_http` — selects `lifetimeFinesCents` on a `Patron` seeded at `9007199254752336` (past `2**53 - 1`) and asserts the response carries the decimal string, per [Decision 4](#decision-4--bigint-is-pinned-twice).

### `tests/types/test_converters.py` — nothing duplicated

No package test reads a `BigIntegerField`, `PositiveBigIntegerField`, or `JSONField` conversion out of a synthetic `managed = False` owner model, per [Decision 5](#decision-5--no-package-test-duplicates-the-live-coverage).

### No example-app test for this card

`examples/fakeshop/apps/scalars/tests/` is the app's non-live test package; this card adds nothing to it. Everything this card asserts is reachable from a real query, so the live tier is the correct and only home.

## Doc updates

- [`CHANGELOG.md`][changelog] — the `[0.0.7]` `### Added` subsection (the joint cut shares one section) carries an entry naming the three surfaces: the `apps.scalars` paired-model app and its two root fields, the reverse-FK exposure on `ScalarSpecimenType`, and `Patron.lifetime_fines_cents`.
- [`KANBAN.md`][kanban] — the card sits in Done.
- [`docs/TREE.md`][tree] — `apps/scalars/` appears in the fakeshop layout with a one-line purpose, and `test_scalars_api.py` in the live test-tree block.
- [`TODAY.md`][today] — the Scalars capability row names the scalars app as the demonstration vehicle for [`BigInt`][glossary-bigint-scalar] and the JSON / UUID / Decimal / date / time conversions.
- No [`docs/GLOSSARY.md`][glossary] status flip. This card ships no new package capability; the converter entries it covers were already `shipped`.
- No [`README.md`][readme-root] or [`docs/README.md`][readme-docs] edit. Both describe consumer-facing package surface, and this card adds none.

## Definition of done

The card is complete when all of the following are true:

1. `examples/fakeshop/apps/scalars/` exists with [`apps.py`][scalars-apps] (`ScalarsConfig`), [`models.py`][scalars-models], [`schema.py`][scalars-schema], and `migrations/0001_initial.py`.
2. `ScalarSpecimen` declares one column per each of the ten non-trivial `SCALAR_MAP` rows and none of its scalar columns is nullable.
3. `NullableScalarSpecimen` declares the same column names with `null=True, blank=True`; every field it declares is nullable.
4. `ScalarSpecimen.parent` is a self-FK with `null=True`, `related_name="children"`, `on_delete=CASCADE`.
5. `NullableScalarSpecimen.partner` is a cross-model FK to `ScalarSpecimen` with `null=True`, `on_delete=SET_NULL`, `related_name="nullable_partners"`.
6. `ScalarSpecimenType` and `NullableScalarSpecimenType` select every converted column; `ScalarSpecimenType` additionally selects `parent`, `children`, and `nullable_partners`.
7. `all_scalar_specimens` and `all_nullable_scalar_specimens` are composed into the project root `Query` at [`examples/fakeshop/config/schema.py`][example-schema].
8. `ScalarsConfig` is listed in `INSTALLED_APPS` at [`examples/fakeshop/config/settings.py`][settings].
9. The nine tests named in the [Test plan](#test-plan) exist in [`test_query/test_scalars_api.py`][test-scalars-api] and are collected by the live suite.
10. `Patron.lifetime_fines_cents` exists, is selected in [`apps/library/schema.py`][library-schema] `::PatronType`'s `Meta.fields`, and is pinned live past `2**53 - 1` by [`test_query/test_library_api.py`][test-library-api] `::test_library_patron_bigint_lifetime_fines_over_http`.
11. [`tests/types/test_converters.py`][test-converters] reads no `BigIntegerField`, `PositiveBigIntegerField`, or `JSONField` conversion out of a synthetic `managed = False` owner model.
12. No file under `django_strawberry_framework/` is changed by this card, and `__all__` is unchanged.
13. [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban], [`docs/TREE.md`][tree], and [`TODAY.md`][today] carry the card per [Doc updates](#doc-updates).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md
[readme-root]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[readme-docs]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-026-rationale]: appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md
[spec-026-rationale-d1]: appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md#decision-1--paired-models-not-one-model-with-paired-columns
[spec-026-rationale-d3]: appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md#decision-3--the-two-relation-shapes-and-what-each-is-for

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converters]: ../../django_strawberry_framework/types/converters.py

<!-- tests/ -->
[test-converters]: ../../tests/types/test_converters.py

<!-- examples/ -->
[example-schema]: ../../examples/fakeshop/config/schema.py
[library-models]: ../../examples/fakeshop/apps/library/models.py
[library-schema]: ../../examples/fakeshop/apps/library/schema.py
[scalars-apps]: ../../examples/fakeshop/apps/scalars/apps.py
[scalars-models]: ../../examples/fakeshop/apps/scalars/models.py
[scalars-schema]: ../../examples/fakeshop/apps/scalars/schema.py
[settings]: ../../examples/fakeshop/config/settings.py
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py
[test-scalars-api]: ../../examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
