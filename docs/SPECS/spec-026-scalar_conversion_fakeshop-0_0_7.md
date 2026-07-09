# Spec: Scalar conversion end-to-end coverage in the fakeshop example

Target release: `0.0.7` (per [KANBAN.md][kanban] card `DONE-026-0.0.7`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

This file is intentionally lightweight. It preserves the card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository file. Before implementation work starts from this file, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

## Card snapshot

- Card: `DONE-026-0.0.7`
- Status: `done` / Done
- Milestone: `alpha` / Alpha (pre-0.1.0)
- Priority: Medium
- Relative size: M
- Labels: `example-app`, `graphql-api`, `scalars`, `tests`

## Planning note

shipped

## Other

- both upstreams ship scalar conversion for the full numeric / date / JSON / UUID set; this card moves those converter rows to live `/graphql/` HTTP coverage in both nullable and non-null shapes.
- new `apps.scalars` example app (paired non-null / nullable models, self-FK + cross-model `SET_NULL` FK) + eight live HTTP tests + a real-domain `BigIntegerField` on `Patron`.
- `ScalarSpecimen` — every scalar field non-null, exposed via `ScalarSpecimenType`. Adds an intra-model self-FK `parent` (`related_name="children"`) so the example exercises self-referential FK planning under the optimizer.
- `NullableScalarSpecimen` — every scalar field nullable (`null=True, blank=True`), exposed via `NullableScalarSpecimenType`. Adds a cross-model FK `partner: ForeignKey(ScalarSpecimen, on_delete=SET_NULL, related_name="nullable_partners")` — the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app.
- The pairing is deliberate (not a single model with paired fields). It exercises **upstream code paths no other example app reaches**: Django's two-`CreateModel` initial migration path, the registry / `[finalize_django_types][glossary-finalize-django-types]()` resolving sibling [`DjangoType`][glossary-djangotype] classes in one app, Strawberry type registration across sibling types in one schema build, the optimizer planning across two managed models in one query, and `SET_NULL` ondelete behavior.
- `apps.scalars.schema` composes two root resolvers (`all_scalar_specimens`, `all_nullable_scalar_specimens`) into the project root `Query` at [`examples/fakeshop/config/schema.py`][example-schema]; `ScalarsConfig` lands in `INSTALLED_APPS` at [`examples/fakeshop/config/settings.py`][settings].
- Full non-null wire-format sweep covering every field on `ScalarSpecimen`
- Signed-negative [`BigInt`][glossary-bigint-scalar] round-trip
- `BigInt`-at-zero edge case
- Schema introspection asserting `BigInt` converter resolves correctly in both shapes (`NON_NULL` on `ScalarSpecimenType`; bare `SCALAR` on `NullableScalarSpecimenType`)
- All-NULL nullable wire format covering every nullable converter branch
- Cross-model `partner` FK linkage round-trip
- Reverse-FK `nullablePartners` exposure
- Self-FK `parent` / `children` traversal

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
