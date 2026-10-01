# Rationale: spec-026 — Scalar conversion end-to-end coverage in the fakeshop example (rejected alternatives)

Deliberative companion to [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026]. The spec is the contract; this file records the alternatives its decisions rejected and why each lost. Each entry is keyed to the spec heading it belongs to.

## Decision 1 — Paired models, not one model with paired columns

**Keys to:** [`### Decision 1 - Paired models, not one model with paired columns`][spec-026-decision-1].

What the pairing buys is the **per-column nullable / non-null converter mirror**: an all-nullable twin of an all-required model over an identical column set, so both branches of one `SCALAR_MAP` row — the `NON_NULL` wrapper and the bare `SCALAR` — are exercised by live round-trips against the same column name.

That mirror is the whole reason for the second model. The registry, [`finalize_django_types`][glossary-finalize-django-types] resolving sibling `DjangoType` classes in one app, Strawberry registration across sibling types in one schema build, and optimizer planning across related managed models are reached by [`apps/library`][library-schema] and `apps/products` as well, so none of them is a reason for the pairing.

### Alternatives rejected

- **One model with paired `_required` / `_nullable` columns per scalar.** Lost because the two shapes would then differ in column name as well as in nullability, so a comparison between them no longer isolates the converter's nullability branch. The mirror over identical column names is what makes the introspection assertions mean one thing.

## Decision 3 — The two relation shapes, and what each is for

**Keys to:** [`### Decision 3 - The two relation shapes, and what each is for`][spec-026-decision-3].

Decision 3 states what the `partner` edge itself does — `SET_NULL` clears `partner_id` and leaves the source row in place — and names the live test that pins it. It never ranks the edge in a population ("the only `SET_NULL` in the example tree", "the only cross-model FK in the app"). A census over a population the app does not own is falsified by growth in an unrelated app: [`apps/scalars/models.py`][scalars-models]'s own `ScalarSpecimen.tag` and the `kanban` and `library` models carry `SET_NULL` foreign keys too.

### Alternatives rejected

- **A narrower census** ("the only cross-model `SET_NULL` under the optimizer", "the only `SET_NULL` exposed through a `DjangoType` relation field", "the only `SET_NULL` whose detach any test exercises"). Lost because each is the same shape of claim — a quantifier over a population the sentence does not own — whether or not it measures true today. A locally verifiable statement quantifies over nothing outside `apps/scalars`, so nothing outside it can falsify it.

## Non-goal 1 — the PostgreSQL-only exclusion

**Keys to:** [`## Non-goals`][spec-026-non-goals], item 1.

`ArrayField` and `HStoreField` are absent from the coverage models on purpose. Both are PostgreSQL-only, the fakeshop's default database is SQLite, and a column the example database cannot create is a column no live `/graphql/` request can reach. Their coverage stays in `tests/` against package-internal fixtures. The spec states the exclusion as a non-goal, beside the module docstring of [`apps/scalars/models.py`][scalars-models], so it does not read as an oversight to fix.

Neither field has a `SCALAR_MAP` row. Both are dispatched by sentinel-guarded branches in [`converters.py`][converters] `::convert_scalar` that run **before** the table's MRO walk, because neither type can be imported unconditionally; "their converter rows" would send a reader looking for two table entries that do not exist.

### Alternatives rejected

- **Add the two columns and skip the tests off a Postgres marker.** Lost because a model field that cannot be created is not skippable at the test layer: the migration itself fails on SQLite, and the app is in the default `INSTALLED_APPS`.
- **Say nothing, since the source docstring says it.** Lost because the spec is where scope is audited.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-finalize-django-types]: ../../GLOSSARY.md#finalize_django_types

<!-- docs/SPECS/ -->
[spec-026-decision-1]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#decision-1--paired-models-not-one-model-with-paired-columns
[spec-026-decision-3]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#decision-3--the-two-relation-shapes-and-what-each-is-for
[spec-026-non-goals]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#non-goals
[spec-026]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converters]: ../../../django_strawberry_framework/types/converters.py

<!-- tests/ -->

<!-- examples/ -->
[library-schema]: ../../../examples/fakeshop/apps/library/schema.py
[scalars-models]: ../../../examples/fakeshop/apps/scalars/models.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
