# Spec: `FieldSet` — declarative field-level behavior via `Meta.fields_class`

Planned for `0.1.1` (card `TODO-BETA-048-0.1.1`); **this card is the only
non-Done card at `0.1.1` and owns the version bump**
([Decision 10](#decision-10--lone-card-at-011--this-slice-owns-the-version-cut)).
First Beta-line feature card: the Strawberry port of graphene-django's
`AdvancedFieldSet` (from `django-graphene-filters`), the declarative
field-level behavior layer the cookbook drives via `Meta.fields_class`. A
consumer-authored `class GalaxyFieldSet(FieldSet)` carries three flavors of
declaration ([Decision 2](#decision-2--the-three-declaration-contract)):
`resolve_<field>(self, root, info)` content overrides,
`check_<field>_permission(self, info)` denial gates that run before resolve,
and class-level Strawberry annotations
(`display_name: str | None = strawberry.field(...)`) for computed fields the
Django model does not have. Pointed at by
`Meta.fields_class = GalaxyFieldSet` on the owning [`DjangoType`][glossary-djangotype]
and wired at [`finalize_django_types`][glossary-finalize-django-types]
phase 2.5 — the same seam `filterset_class` / `orderset_class` use
([Decision 4](#decision-4--phase-25-binding-via-a-dedicated-_bind_fieldsets)).
This is the smallest Layer-3 surface by file count but the most novel by
semantic surface area: the resolver-override contract, the
redaction-vs-denial split, and the computed-field annotation discipline all
live here.

Status: **PLANNED — no slice built yet.**
Five slices: Slice 1 (**`fieldset/` package core** — `FieldSet` +
metaclass discovery/validation + unit tests), Slice 2 (**phase-2.5 binding +
resolver wiring** — `_bind_fieldsets`, the wrapper cascade,
`Meta.fields_class` promotion), Slice 3 (**computed-field transplant +
optimizer `Meta.depends_on`**), Slice 4 (**live fakeshop coverage +
composability tests**), Slice 5 (**docs + the `0.1.1` version cut + card
wrap**).

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
without explicit permission; this spec's Slice 5 grants that permission for
the `0.1.1` entry, and no earlier slice touches it.

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`FieldSet`][glossary-fieldset] — planned for `0.1.1`; **this card ships it.**
- [`Meta.fields_class`][glossary-metafields-class] — planned for `0.1.1`;
  promoted out of `DEFERRED_META_KEYS` by this card
  ([Decision 8](#decision-8--metafields_class-promotes-in-this-card)).
- [Per-field permission hooks][glossary-per-field-permission-hooks] — planned
  for `0.1.1`; the `check_<field>_permission(self, info)` signature was
  pinned by [`spec-034`][spec-034] Decision 2 and is **not re-litigated
  here** ([Decision 3](#decision-3--denial-raises-redaction-returns--no-deny-value-table)).
- [`DjangoType`][glossary-djangotype] — shipped; the owning type whose
  resolver chain the FieldSet customizes.
- [`Meta.fields`][glossary-metafields] — shipped; stays the single source of
  truth for which model fields surface
  ([Decision 6](#decision-6--the-owning-types-metafields-stays-the-single-source-of-truth)).
- [`finalize_django_types`][glossary-finalize-django-types] — shipped; the
  phase-2.5 window hosts `_bind_fieldsets`.
- [`Meta.filterset_class`][glossary-metafilterset-class] /
  [`Meta.orderset_class`][glossary-metaorderset-class] — shipped (`0.0.8`);
  the binding-precedent surfaces this card's wiring mirrors.
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] —
  shipped (`0.0.8`); composability-test counterparts.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — shipped
  (`0.0.9`); the card's declared dependency (`DONE-030-0.0.9`) — FieldSet
  composes on top of the shipped connection-field surface.
- [`apply_cascade_permissions`][glossary-apply-cascade-permissions] — shipped
  (`0.0.10`); cascade narrows rows first, field gates run on survivors
  ([Decision 9](#decision-9--cascade-first-composition--field-gates-never-see-hidden-rows)).
- [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] —
  shipped; row-level visibility, orthogonal to field-level behavior.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] /
  [`only()` projection][glossary-only-projection] — shipped; the seam
  `Meta.depends_on` feeds
  ([Decision 7](#decision-7--metadepends_on-is-an-explicit-declaration-auto-introspection-rejected)).
- [`Meta.optimizer_hints`][glossary-metaoptimizer-hints] /
  [`OptimizerHint`][glossary-optimizerhint] — shipped; the existing
  consumer-side projection-widening precedent `Meta.depends_on` mirrors.
- [`ConfigurationError`][glossary-configurationerror] — shipped; the raise
  type for every finalize-time validation this spec adds.
- [`Meta.aggregate_class`][glossary-metaaggregate-class] /
  [`Meta.search_fields`][glossary-metasearch-fields] — planned (`0.1.3` /
  `0.1.2`); stay in `DEFERRED_META_KEYS`, untouched by this card.
- [`AggregateSet`][glossary-aggregateset] — planned (`0.1.3`); named here
  only as the remaining sidecar sibling.
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] —
  governs where Slice 4's tests land.
- [Joint version cut][glossary-joint-version-cut] — the release rule that
  makes this card the `0.1.1` cut owner.
- [Cookbook parity][glossary-cookbook-parity] — the borrowing discipline for
  the `recipes/fields.py` migration claim.
- [`FieldError` envelope][glossary-fielderror-envelope] — shipped; named for
  contrast only (mutation-side errors; field denial uses `GraphQLError`, not
  the envelope).
- [Schema audit][glossary-schema-audit] — shipped; `_audit_field_surface` is
  the collision-check precedent computed-field transplant extends.

---

## Slice checklist

- [ ] **Slice 1 — `fieldset/` package core.** `django_strawberry_framework/fieldset/`
  (package, mirroring the `filters/` shape) with `base.py` (`FieldSet` +
  `FieldSetMetaclass`: discovery of `check_<field>_permission` /
  `resolve_<field>` / computed-field annotations, [`Meta.model`][glossary-metamodel] +
  `Meta.depends_on` validation). Unit tests under `tests/fieldset/`
  mirroring the source one-to-one.
- [ ] **Slice 2 — phase-2.5 binding + resolver wiring.** `factories.py`
  (resolver-binding factory), `_bind_fieldsets` in `types/finalizer.py`
  phase 2.5, `DjangoTypeDefinition.fields_class` slot population,
  `Meta.fields_class` promotion from `DEFERRED_META_KEYS` to
  `ALLOWED_META_KEYS`, wrapper cascade (gate → override → original
  resolver), `skip_field_names` extension so FieldSet resolvers win over
  auto-generated scalar resolvers.
- [ ] **Slice 3 — computed fields + optimizer cooperation.** Class-level
  annotation transplant onto the owning type (fail-closed validation),
  `Meta.depends_on` merged into the optimizer's `only()` projection for the
  owning type's plan.
- [ ] **Slice 4 — live coverage + composability.** Fakeshop fieldsets +
  live HTTP tests under `examples/fakeshop/test_query/`: tiered visibility
  (staff / perm-holder / authenticated / anonymous), redaction
  (`is_private → False`), denial (anonymous raises on `updated_date`),
  computed field (`display_name`). Composability: FieldSet + FilterSet,
  FieldSet + OrderSet, FieldSet + `apply_cascade_permissions`. This slice
  activates the already-staged FieldSet classes in
  `examples/fakeshop/apps/products/fields.py` and owns the stale-comment sweep
  that activation implies: retarget every pre-renumber `TODO-BETA-046-0.1.1`
  fieldset comment in `apps/products/schema.py` (7 occurrences) to the shipped
  `048` id; the sibling search / aggregate comment IDs stay for cards 049 / 051.
- [ ] **Slice 5 — docs + version cut + card wrap.** GLOSSARY status flips
  (DB + regen), `docs/README.md` / `README.md` / `GOAL.md` / `TODAY.md`
  touch-ups where the surface change is reflected, `docs/TREE.md` regen,
  `CHANGELOG.md` `0.1.1` entry, the version quintet, KANBAN card flip
  (DB + regen).

---

## Problem statement

Filter, order, and cascade permissions all narrow **rows** — they remove
whole objects from the result set. Field-level visibility is the one
cookbook surface where a row stays visible but a single field must be either
**redacted** (return a safe value — non-staff sees `is_private = False`) or
**denied** (raise an error — anonymous cannot read `updated_date` at all).
Without `FieldSet`, the cookbook's `is_private` / `description` /
tiered-date patterns are not portable: the framework today has no
declarative home for per-field gates, per-field content overrides, or
computed fields, short of hand-authoring resolvers on the `DjangoType`
subclass itself — which defeats the package's Meta-driven,
migration-friendly posture.

Three concrete patterns from the cookbook anchor (`GOAL.md`'s `fields.py`
example and `django-graphene-filters`'
`examples/cookbook/cookbook/recipes/fields.py`) must work cleanly:

1. **Tiered visibility** — `resolve_created_date` returns full datetime for
   staff, day precision for `view_<model>` perm-holders, month precision for
   authenticated users, year precision for anonymous.
2. **Redaction vs denial** — `resolve_is_private` returns `False` for
   non-staff (redaction: safe value, stable response shape);
   `check_updated_date_permission` raises `GraphQLError` for anonymous
   (denial: an `errors` entry for that path).
3. **Computed fields** — `display_name: str | None = strawberry.field(...)`
   declares a field the Django model does not have, paired with
   `resolve_display_name`.

## Current state

- `DjangoTypeDefinition.fields_class` exists as an inert forward-reserved
  sidecar slot (`types/definition.py #"fields_class: type | None = None"`,
  declared by [`spec-034`][spec-034] Decision 2 as the structural mirror of
  the shipped `filterset_class` / `orderset_class` slots). It has no
  populator and stays `None`.
- `Meta.fields_class` sits in `DEFERRED_META_KEYS`
  (`types/base.py #"aggregate_class", "fields_class", "search_fields"`) —
  declaring it on a `DjangoType` today raises the deferred-surface
  `ConfigurationError`.
- The `check_<field>_permission(self, info)` read-gate **signature** is
  already pinned ([`spec-034`][spec-034] Decision 2, mirrored in the
  glossary's [Per-field permission hooks][glossary-per-field-permission-hooks]
  entry): an `info`-shaped gate that runs per resolved field, deliberately
  distinct from the `(self, request)`-shaped input gates on
  `FilterSet` / `OrderSet` that judge filter / order *input*.
- The phase-2.5 binding infrastructure is shipped and DRY:
  `types/finalizer.py::_bind_sidecar_sets` runs the ordered owner-bind →
  expand → orphan-audit → materialize subpasses for the filter and order
  families, with `types/finalizer.py::_bind_set_owner_common` as the shared
  owner-binding skeleton.
- Resolver attachment already carries the consumer-win mechanism this card
  extends: `types/resolvers.py::_attach_relation_resolvers` and the scalar
  attachment path both accept a `skip_field_names` frozenset
  (`DjangoTypeDefinition.consumer_authored_fields`) so consumer-authored
  fields are not clobbered by generated resolvers.
- The optimizer's per-type plan carries `only_fields`
  (`optimizer/plans.py #"only_fields: Sequence[str]"`) applied as
  `queryset.only(*names)`; `Meta.optimizer_hints` is the shipped
  consumer-side projection-widening surface.
- Upstream, the full surface exists and is verified readable at
  `/Users/riordenweber/projects/django-graphene-filters`:
  `django_graphene_filters/fieldset.py::AdvancedFieldSet` +
  `FieldSetMetaclass`, the wiring in
  `django_graphene_filters/object_type.py::_wrap_field_resolvers` (plus its
  `_get_deny_value` cache), and the upstream design doc
  `docs/spec-fields_class.md`.

## Goals

1. Ship `django_strawberry_framework/fieldset/` with the consumer-facing
   `FieldSet` base class: `class Meta: model = Foo` (+ optional
   `depends_on`), method-based declarations, computed-field annotations.
2. Wire `Meta.fields_class = FooFieldSet` end-to-end: validation at
   type-creation time, binding at phase 2.5, resolver cascade active on the
   live schema — consumers never subclass the type or hand-attach
   decorators.
3. Promote `Meta.fields_class` from `DEFERRED_META_KEYS` to
   `ALLOWED_META_KEYS`.
4. Preserve the optimizer contract: a `resolve_<field>` that reads ORM
   columns declares them via `Meta.depends_on`; the optimizer widens the
   `only()` projection so no managed resolver triggers a deferred-field
   fetch.
5. Compose correctly with the shipped row-level machinery: cascade narrows
   first, field gates run on survivors; FieldSet-gated fields remain
   filterable / orderable for authorized users.
6. Cookbook parity: the `GOAL.md` `fields.py` example runs verbatim against
   the shipped surface.

## Non-goals

- **Node-level sentinel redaction.** Upstream's
  `django_graphene_filters/object_type.py::AdvancedDjangoObjectType.get_node`
  / `_make_sentinel` (`is_redacted=True`) masks a hidden non-null FK target
  in place instead of dropping the row. The package deliberately did not
  adopt this tier (spec-034 Decision 6 chose row-exclusion) and `FieldSet`
  does not revive it. The redaction taxonomy stays two-tier: relation/row
  visibility = queryset narrowing
  ([`apply_cascade_permissions`][glossary-apply-cascade-permissions]), field
  visibility = `FieldSet` (redact value / deny). The opt-in third tier is
  tracked as its own card, `TODO-BETA-053-0.1.4` (`Meta.redaction_mode`),
  which explicitly amends this Non-goal as its realized form — `FieldSet`
  redaction runs only on fields of rows that already survived the cascade.
- **Schema-shape control.** `FieldSet` never adds or removes model fields
  from the GraphQL type (that is `Meta.fields` / [`Meta.exclude`][glossary-metaexclude]'s job) and
  never hides fields from introspection (per-role schema generation is
  upstream's explicitly-rejected Hasura alternative; resolve-time
  enforcement is the pinned posture). The single schema-shape effect it has
  is additive: computed-field annotations
  ([Decision 5](#decision-5--computed-fields-transplant-onto-the-owning-type-fail-closed)).
- **Per-field *input* gates.** `check_<field>_permission` on
  `FilterSet` / `OrderSet` (the `(self, request)`-shaped gates judging
  filter/order input) already shipped in `0.0.8` and are untouched.
- **`Meta.search_fields` / `Meta.aggregate_class`.** The other two deferred
  Layer-3 keys stay deferred (`TODO-BETA-049-0.1.2` /
  `TODO-BETA-051-0.1.3`-line cards own them).
- **The generalized Meta-key promotion machinery.** `TODO-BETA-052-0.1.3`
  (Layer 3 Meta key promotion) owns the dispatched binding form; this card
  ships the direct `_bind_fieldsets` and promotes only its own key
  ([Decision 8](#decision-8--metafields_class-promotes-in-this-card)).

## Borrowing posture

[Single-upstream parity][glossary-single-upstream-parity] surface:
`graphene-django`'s cookbook layer via
`django-graphene-filters` (there is no `strawberry-graphql-django`
counterpart to reconcile — its field-level story is per-field
`strawberry.Private` / hand-authored resolvers, not a declarative sidecar).
Borrowed, engine-adapted, and deliberately diverged:

- **Borrowed verbatim** — the three-declaration contract and its discovery
  metaclass (`fieldset.py::FieldSetMetaclass`: `check_` / `_permission`
  affix stripping, `resolve_` prefix stripping, `dir(new_class)` walk so
  mixin/base declarations inherit); the cascade order (gate → override →
  default); the zero-overhead posture (only managed fields get wrapped —
  unmanaged fields keep their untouched resolvers); the
  original-resolver-preserving wrapper shape
  (`object_type.py::_wrap_field_resolvers` captures and delegates to the
  prior resolver as the cascade's step 3); the warning-not-error stance for
  a FieldSet method targeting a field absent from the owning type's surface
  (a FieldSet may be intentionally shared across types with different
  `Meta.fields`).
- **Engine-adapted** — graphene's `UnmountedType` class-attribute scan for
  computed fields becomes a Strawberry annotation scan
  (`display_name: str | None = strawberry.field(...)`); graphene's
  `__init_subclass_with_meta__` wiring becomes phase-2.5 finalizer binding
  (the package's definition-order-independent seam); camelCase/snake_case
  double-lookup is unnecessary (the framework owns its field surface pre-
  schema, keyed by snake_case).
- **Deliberately diverged** — upstream's deny-value machinery
  (`object_type.py::_get_deny_value`: swallow the gate's exception, return a
  cached type-appropriate default — `None` / `""` / `False` / epoch) is
  **rejected**; a raising gate propagates as a `GraphQLError`
  ([Decision 3](#decision-3--denial-raises-redaction-returns--no-deny-value-table)).
  Upstream's own design doc treats the null-substitution as pragmatic
  compromise; this package's taxonomy (pinned in the glossary since
  `0.0.10`) makes denial *visible by design* and expresses redaction through
  `resolve_<field>` instead.

## User-facing API

Exactly the `GOAL.md` cookbook shape (import path mirrors
`django_strawberry_framework.filters`; no root re-export, matching
`FilterSet` / `OrderSet` precedent):

```python
import strawberry
from graphql import GraphQLError

from django_strawberry_framework.fieldset import FieldSet

from . import models


class GalaxyFieldSet(FieldSet):
    display_name: str | None = strawberry.field(description="Computed: '{id} - {name}'")

    class Meta:
        model = models.Galaxy
        depends_on = {
            "resolve_display_name": ("id", "name"),
        }

    def resolve_description(self, root, info):
        """Staff sees description; everyone else gets an empty string."""
        user = _user(info)
        return root.description if user and user.is_staff else ""

    def resolve_display_name(self, root, info):
        """Computed field — visible to all signed-in users."""
        user = _user(info)
        return f"{root.id} - {root.name}" if user and user.is_authenticated else None

    def check_updated_date_permission(self, info):
        """Anonymous users cannot see updated_date at all — denial gate before resolve."""
        user = _user(info)
        if not user or not user.is_authenticated:
            raise GraphQLError("Login required to view updated date.")

    def resolve_updated_date(self, root, info):
        return _resolve_date(root.updated_date, info, "astronomy.view_galaxy")


class GalaxyType(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = "__all__"
        fields_class = GalaxyFieldSet
```

Contract summary:

| Declared on the FieldSet | Behavior at resolve time |
|---|---|
| Only `check_<field>_permission` | Gate runs; raise propagates as a `GraphQLError` for that path; no raise → generated resolver |
| Only `resolve_<field>` | Override replaces the generated resolver (redaction / tiering / masking live here) |
| Both | Gate first, then override (the override may assume the gate passed) |
| Class-level annotation + `resolve_<field>` | Computed field: annotation transplants onto the owning type; the override is its resolver |
| Class-level annotation without `resolve_<field>` | `ConfigurationError` at finalize time ([Decision 5](#decision-5--computed-fields-transplant-onto-the-owning-type-fail-closed)) |
| Neither | Field untouched — zero overhead |

## Architectural decisions

### Decision 1 — Package shape mirrors `filters/`: `fieldset/` with `base.py` + `factories.py`

`django_strawberry_framework/fieldset/` is a package (not a single module),
per the card's DoD: `base.py` carries `FieldSet` + `FieldSetMetaclass`
(declaration discovery and Meta validation at class-creation time);
`factories.py` carries the resolver-binding factory that phase 2.5 drives
(wrapper construction, computed-field transplant, `depends_on` handoff).
Import path `django_strawberry_framework.fieldset.FieldSet` — subpackage
import, no root re-export, mirroring `filters.FilterSet` / `orders`.

*Alternative rejected:* a single `fieldset.py` module (upstream's shape).
Rejected because the package's sidecar families are all packages
(`filters/` with `base.py` / `factories.py` / `inputs.py` / `sets.py`), the
card's DoD names the package shape explicitly, and the binding factory is a
distinct concern from the consumer-facing class. `fieldset/` has no
`inputs.py` — the family generates no GraphQL input types
(see [Decision 4](#decision-4--phase-25-binding-via-a-dedicated-_bind_fieldsets)).

### Decision 2 — The three-declaration contract

`FieldSetMetaclass` discovers, at class-creation time (upstream
`fieldset.py::FieldSetMetaclass` parity):

1. **Gates** — methods matching `check_<field>_permission`; `<field>` must
   name a concrete model field of `Meta.model`, else the method is recorded
   for the finalize-time surface audit (see Edge cases).
2. **Overrides** — methods matching `resolve_<field>`; `<field>` may name a
   model field (content override) or a computed field (paired with an
   annotation) — model validation is deliberately skipped for overrides,
   upstream parity.
3. **Computed fields** — class-level Strawberry annotations
   (`name: <type> = strawberry.field(...)` or a bare annotation); collected
   with the same inheritance-aware walk as methods so mixin-declared
   computed fields work.

The metaclass stores the discovered sets (`_field_permissions`,
`_field_resolvers`, `_computed_fields`, and their union `_managed_fields`)
as class attributes — the binding factory's entire input. `Meta.model` is
required on concrete consumer subclasses (the abstract `FieldSet` base
itself carries none); a missing/non-model `Meta.model` raises
[`ConfigurationError`][glossary-configurationerror] at class-creation time,
matching the `FilterSet` fail-at-declaration posture rather than upstream's
silent skip.

*Alternative rejected:* declaration objects
(`name = FieldPermission(...)`-style, django-filter's declarative-attribute
idiom). Rejected: the method-naming convention is the cookbook contract
being ported — consumers migrating from `django-graphene-filters` rename
the base class and keep every method verbatim.

### Decision 3 — Denial raises, redaction returns — no deny-value table

A `check_<field>_permission` that raises propagates the exception into
GraphQL execution: the response carries an `errors` entry for that exact
path, and the field's value is `null` (nullable field) or nulls cascade up
per the GraphQL spec (non-null field). The framework performs **no**
exception swallowing and **no** type-appropriate default substitution.

This deliberately diverges from upstream, whose wrapper calls
`check_field()` (swallowing every exception into `False`) and substitutes a
cached deny value (`object_type.py::_get_deny_value`: `None` / `""` /
`False` / epoch datetime). Rationale:

- The package's taxonomy has been pinned since `0.0.10` (glossary
  [Per-field permission hooks][glossary-per-field-permission-hooks]):
  **redaction** = silent safe value, **denial** = visible `errors` entry.
  Upstream's deny-value table collapses the two — a denied non-nullable
  `DateTime` silently becomes epoch, which is indistinguishable from real
  data on the wire. That is a redaction outcome delivered by a denial
  declaration; the consumer who wants it writes `resolve_<field>` returning
  the safe value instead, which is exactly what the cookbook's
  `resolve_is_private` does.
- Wire honesty: a client integrating against a denial gate needs the
  `errors` entry to distinguish "no permission" from "value is null/empty".
- Simplicity: no deny-value cache, no per-model-field default inference, no
  epoch sentinel to document.

Consequence for non-nullable fields (upstream's own risk item): denying a
non-null field nulls its enclosing object per GraphQL bubbling. This is the
correct, spec-mandated behavior and is documented as an edge case with the
same guidance upstream gives — make the field nullable, or gate at the row
level instead.

*Alternatives rejected:* (a) upstream's swallow-plus-deny-value —
see above; (b) returning `None` without an error (silent denial) —
indistinguishable from redaction, breaks the taxonomy; (c) routing denial
through the [`FieldError` envelope][glossary-fielderror-envelope] — that
envelope is the *mutation* validation contract; read-side field denial is a
standard `GraphQLError` per the pinned glossary entry.

### Decision 4 — Phase-2.5 binding via a dedicated `_bind_fieldsets`

`types/finalizer.py` gains `_bind_fieldsets()`, called in the pinned
phase-2.5 window alongside `_bind_filtersets()` / `_bind_ordersets()`
(after primary-type state settles, before `strawberry.Schema(...)`). It
reuses `types/finalizer.py::_bind_set_owner_common` for the owner-binding
skeleton (wire `fields_class._owner_definition`, validate owner model
matches `Meta.model`, reject double-wiring) and runs the family's own
subpasses: per-type declaration-surface audit, computed-field transplant,
resolver wrapping.

It does **not** route through
`types/finalizer.py::_bind_sidecar_sets` / `_SidecarBindingSpec`.
That driver's subpass sequence is factory-shaped — expand (input-class
construction), orphan-audit against a helper ledger, materialize input
classes as module globals. The FieldSet family generates **no input types**
and has **no helper-reference ledger** (there is no `fieldset_input_type`
helper for a consumer to orphan against); forcing it through the spec
object would mean null-object `expand` / `materialize` / `factory_cls`
stubs — machinery pretending to be shared. `TODO-BETA-052-0.1.3` (Layer 3
Meta key promotion) owns whatever dispatched generalization later absorbs
all three families; this card keeps the direct form and shares only the
genuinely-common owner skeleton.

Idempotence: like the shipped binders, `_bind_fieldsets` skips
already-finalized definitions so the documented re-call-after-fixable-
failure contract of `finalize_django_types` holds; wrapping is applied once
per (type, field) — the wrapper marks wrapped resolvers so a rerun is a
no-op.

*Alternative rejected:* eager wiring at type-creation time (upstream's
`__init_subclass_with_meta__` moment). Rejected: the package's
[definition-order independence][glossary-definition-order-independence]
posture requires deferring cross-object wiring to the finalizer; a
FieldSet declared after its owning type (or in another module) must work.

### Decision 5 — Computed fields transplant onto the owning type, fail-closed

At bind time, each discovered computed-field annotation is transplanted
onto the owning `DjangoType`'s Strawberry field surface (annotation +
`strawberry.field(...)` descriptor), with its `resolve_<field>` override
installed as the field's resolver. Validation is fail-closed, all raising
[`ConfigurationError`][glossary-configurationerror] at finalize time:

1. A computed-field annotation with **no** matching `resolve_<field>` on the
   FieldSet raises (upstream merely documents "must be declared on the
   ObjectType"; the framework can enforce it because it owns the
   transplant).
2. A computed-field name colliding with the owning type's existing field
   surface (model-backed, consumer-authored, or relation-synthesized)
   raises — routed through the same surface audit family as
   `types/finalizer.py::_audit_field_surface` so camelCase collisions are
   caught too.
3. A computed field paired with a `check_<field>_permission` gate is legal —
   the gate wraps the transplanted resolver like any managed field.

The transplanted field lands in
`DjangoTypeDefinition.consumer_authored_fields`' skip-set so downstream
attachment passes treat it exactly like a consumer-authored field on the
type body.

*Alternative rejected:* requiring the consumer to declare the annotation on
the `DjangoType` body and only the resolver on the FieldSet (upstream's
split). Rejected: it splits one logical declaration across two classes; the
cookbook shape (`GOAL.md` `fields.py`) puts the annotation on the FieldSet,
and the framework's finalizer owns the type surface pre-schema, so the
transplant is safe and single-sourced.

### Decision 6 — The owning type's `Meta.fields` stays the single source of truth

`FieldSet` carries **no** `Meta.fields`. Which model fields surface is
decided exclusively by the owning `DjangoType`'s
`Meta.fields` / `Meta.exclude`; the FieldSet only customizes resolution /
permission for fields already surfaced, plus declares computed fields. A
FieldSet method targeting a model field the owning type does not surface is
a **warning, not an error** (upstream parity, and for the same reason: one
FieldSet may be shared across multiple types with different field lists) —
emitted once per (type, field) at bind time via `warnings.warn`, naming
both classes.

*Alternative rejected:* fail-closed here too. Considered for consistency
with Decision 5, but rejected because the shared-FieldSet use case is
legitimate and upstream-documented; a hard error would force per-type
FieldSet duplication. The asymmetry is principled: a computed field without
its resolver is *always* a bug; a gate on an unsurfaced field is *sometimes*
intentional.

### Decision 7 — `Meta.depends_on` is an explicit declaration; auto-introspection rejected

The FieldSet declares which model columns its overrides read via
`Meta.depends_on = {"resolve_<field>": ("col", ...)}` — keyed by method
name, valued by concrete-column tuples (the card's pre-pinned shape,
preserved verbatim). At bind time the union of declared columns is recorded
on the owning definition; the optimizer merges it into the type's plan
`only_fields` (`optimizer/plans.py #"only_fields: Sequence[str]"`) whenever
a managed field is selected, so an override reading `root.name` never
triggers a deferred-field fetch. This mirrors the shipped
[`Meta.optimizer_hints`][glossary-metaoptimizer-hints] /
[`OptimizerHint`][glossary-optimizerhint] posture: the consumer states the
dependency; the planner honors it.

The card's alternative — "auto-introspection if reliably available" — is
**rejected**: overrides are arbitrary Python; static `root.<attr>` analysis
misses indirection (helper functions like the cookbook's `_resolve_date`,
`getattr`, comprehensions) and produces false confidence exactly where it
matters. A missing `depends_on` entry is correctness-preserving — Django
transparently fetches the deferred column with one extra query — so the
contract is a *performance* contract, not a safety gate, and an explicit
declaration with an honest failure mode beats a lying inference. Validation:
`depends_on` keys must name discovered `resolve_<field>` methods and values
must name concrete columns of `Meta.model`; violations raise
`ConfigurationError` at class-creation time (typo guard, same posture as
the Meta-key typo guard).

### Decision 8 — `Meta.fields_class` promotes in this card

`fields_class` moves from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` in
Slice 2, because this card is what makes the pipeline apply end-to-end —
the promotion criterion the card's DoD states. Promotion includes the
type-creation-time validation the allowed key needs: the value must be a
`FieldSet` subclass (mirroring the `filterset_class` check), and the
definition slot `DjangoTypeDefinition.fields_class` gets its populator.
`aggregate_class` and `search_fields` stay in `DEFERRED_META_KEYS`.

The card's DoD line reads "…only when the resolver-binding pipeline applies
end-to-end (**per `TODO-BETA-052-0.1.3`**)". The parenthetical is read as
pointing at card 052's *generalized promotion machinery* (the dispatched
binding form), not as deferring this key's promotion to 052 — the card's
own Foundation-slice seam says "This card's `_bind_fieldsets` is what
populates the slot and promotes the key end-to-end", and a shipped
`FieldSet` whose Meta key still raises would be unusable. The residual
ambiguity is recorded in Risks.

### Decision 9 — Cascade-first composition — field gates never see hidden rows

Ordering is pinned: [`apply_cascade_permissions`][glossary-apply-cascade-permissions]
(and the [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook]
generally) narrows the queryset **first**; FieldSet gates and overrides run
only on rows that survived. A field gate cannot short-circuit or widen
cascade visibility, and a field denial never leaks the existence of a
cascade-hidden row — the hidden row produces no node at all, so there is no
path for a field-level `errors` entry to attach to. (On *surviving* rows,
denial is visible by design per
[Decision 3](#decision-3--denial-raises-redaction-returns--no-deny-value-table);
the card's "null fields and denials look identical" phrasing is about
hidden rows, and the glossary's pinned framing — "a field denial never
leaks the existence of a cascade-hidden row" — is the operative contract.)

Independence of layers (upstream's five-layer table, ours minus the
unshipped aggregate layer): a field with a FieldSet read gate remains
filterable via `FilterSet` and orderable via `OrderSet` for users those
layers authorize — the layers compose by intersection of independent
checks, never by implication. Slice 4's composability tests pin all three
pairings.

### Decision 10 — Lone card at `0.1.1` — this slice owns the version cut

Card 048 is the only non-Done card at `0.1.1` (`TODO-BETA-049` is `0.1.2`,
`TODO-BETA-052` is `0.1.3`, …), so per the
[joint version cut][glossary-joint-version-cut] rule this spec's Slice 5
owns the version quintet: `pyproject.toml` `version`, the package
`__version__`, `tests/base/test_init.py`, the GLOSSARY package-version row,
and the root entry in `uv.lock` — mirroring the lone-card Decision shape of
[`spec-038`][spec-038] Decision 14 / [`spec-046`][spec-046] Decision 11.
`0.1.1` is a routine patch on the beta line, **not** a milestone `.0` cut —
none of the milestone-cut extras from [`spec-047`][spec-047] apply.

### Decision 11 — Wrapper preserves the generated resolver and its asyncness

The resolver wrapper captures the original (generated or transplanted)
resolver and delegates to it as cascade step 3, exactly like upstream's
`make_wrapper` — so FK/relation resolvers, converter output
(`types/converters.py::convert_field_output`), and optimizer-planned
resolution all keep working under a gate-only declaration. When the wrapped
resolver is async (`utils/typing.py::is_async_callable`), the wrapper is
async and awaits it; gates and overrides themselves are sync-signature
(`(self, info)` / `(self, root, info)`, per the pinned cookbook contract) —
they run per-field-per-row and must not do I/O, which the docs state
explicitly. Async gate/override support is deferred until a real consumer
need appears (Risks).

## Implementation plan

| Slice | Files touched | Delta |
|---|---|---|
| 1 | `django_strawberry_framework/fieldset/__init__.py`, `fieldset/base.py`, `tests/fieldset/test_base.py` | `FieldSet` + `FieldSetMetaclass`: declaration discovery (gates / overrides / computed annotations, inheritance-aware), `Meta.model` + `Meta.depends_on` validation, `ConfigurationError` paths; unit tests one-to-one |
| 2 | `fieldset/factories.py`, `types/finalizer.py` (`_bind_fieldsets`, phase-2.5 call), `types/base.py` (key promotion + `fields_class` value validation), `types/definition.py` (slot populator docs), `tests/fieldset/test_factories.py`, `tests/types/…` | Owner binding via `_bind_set_owner_common`, wrapper cascade construction, `skip_field_names` extension, promotion out of `DEFERRED_META_KEYS`, idempotent rerun marking |
| 3 | `fieldset/factories.py`, `types/finalizer.py`, `optimizer/plans.py` (or the plan-construction seam that merges per-type extra columns), `tests/fieldset/test_depends_on.py`, `tests/optimizer/…` | Computed-field transplant + fail-closed audits (Decision 5), `depends_on` union → `only_fields` merge (Decision 7) |
| 4 | `examples/fakeshop/apps/products/fields.py` (activate the already-staged FieldSet classes — repoint the `AdvancedFieldSet` base to `FieldSet`; not a new file), fakeshop schema wiring, `examples/fakeshop/test_query/test_fieldset*.py`, `tests/fieldset/test_composability.py` | Live HTTP: tiered visibility / redaction / denial / computed field across the four user tiers; composability with `FilterSet` / `OrderSet` / cascade |
| 5 | `docs/GLOSSARY.md` (DB + regen), `docs/README.md`, `docs/TREE.md` (regen), `README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`/`KANBAN.html` (DB + regen), `CHANGELOG.md`, `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock` | Status flips, new `Meta.depends_on` glossary entry, `0.1.1` entry + version quintet, card wrap |

## Helper-reuse obligations (DRY)

- `types/finalizer.py::_bind_set_owner_common` — the owner-binding skeleton;
  `_bind_fieldsets` MUST reuse it rather than re-deriving owner validation
  (Decision 4).
- `types/finalizer.py::_audit_field_surface` family — computed-field
  collision checks route through the existing surface-audit machinery, not a
  parallel name check (Decision 5).
- `types/resolvers.py` `skip_field_names` /
  `DjangoTypeDefinition.consumer_authored_fields` — the existing
  consumer-win mechanism is extended, not duplicated, for FieldSet-managed
  fields (Decision 5, Decision 11).
- `utils/typing.py::is_async_callable` — asyncness detection in the wrapper
  (Decision 11).
- `exceptions.py::ConfigurationError` + the deferred-surface message shape —
  every new finalize-time raise uses the uniform error family.
- Upstream-shape reuse ledger: `mixins.py::get_concrete_field_names` has no
  direct import (upstream is not a dependency); its role — concrete-field
  enumeration for gate validation — is filled by the package's existing
  model-introspection helpers used by `Meta.fields` resolution; do not write
  a third field-lister.

## Edge cases and constraints

- **Non-null denial bubbles.** Denying a non-null field nulls the enclosing
  object per GraphQL spec bubbling (Decision 3). Documented with the
  upstream-parity guidance: make the field nullable, or move the restriction
  to row level.
- **Gate exceptions are not classified.** Any raise from a gate propagates;
  `GraphQLError` renders cleanly, other exceptions follow the schema's
  standard error masking. The docs steer consumers to `GraphQLError`.
- **Shared FieldSet across types.** Legal; unsurfaced-field targets warn
  per-pair (Decision 6). The warning text names the FieldSet, the field,
  and the owning type — upstream's message shape.
- **Inheritance.** Declarations on FieldSet mixins/bases are discovered
  (`dir()`-walk parity); a subclass overriding a gate/override wins by
  normal MRO.
- **`resolve_field` name is reserved.** Upstream excludes its own
  `resolve_field` dispatcher from discovery; the framework's `FieldSet`
  keeps instance-level helpers non-discoverable by using the same exclusion
  set for any framework-owned method matching the prefix.
- **Per-row instantiation.** The FieldSet instantiates per resolution
  (upstream parity — it needs `info`); gates must stay cheap and I/O-free.
  Worst case (1000 rows × 3 managed fields = 3000 method calls) is
  documented as negligible-but-real, upstream's own benchmark note.
- **Optimizer interplay with `only()`.** Without `depends_on`, an override
  reading an unprojected column costs one deferred-fetch query per row —
  correctness preserved, N+1 reintroduced. The docs make `depends_on` the
  loud, first-class fix (Decision 7). FieldSet wrapping must not disturb
  [FK-id elision][glossary-fk-id-elision] or
  [connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]
  for unmanaged fields — zero-overhead means byte-identical behavior off
  the managed set.
- **Computed fields and the optimizer.** A computed field's GraphQL
  selection maps to no model column; its column needs come entirely from
  `depends_on`. This is the primary `depends_on` consumer (the
  `display_name` reads `id` + `name` case).
- **Relay/connection surfaces.** Managed-field wrapping applies identically
  under [`DjangoConnectionField`][glossary-djangoconnectionfield],
  [`DjangoListField`][glossary-djangolistfield], and
  [Relay Node][glossary-relay-node-integration] refetch — the wrap happens
  on the type's field surface, not per entry point. Slice 4 covers the
  connection path (the card's dependency edge).
- **Concurrent fakeshop writers.** Slice 4's fakeshop edits observe the
  standing repo constraint: never reset `examples/fakeshop/db.sqlite3`;
  schema-module lists in every test harness must include any newly-wired
  module (the recurring cross-test pollution class).

## Test plan

Unit (`tests/fieldset/`, mirroring source one-to-one per the card DoD):

1. Metaclass discovery: gates / overrides / computed annotations, affix
   stripping, inheritance, `resolve_field` exclusion, `_managed_fields`
   union.
2. Validation raises: missing `Meta.model`; non-model `Meta.model`;
   `depends_on` keying a nonexistent override; `depends_on` naming a
   non-concrete column; computed annotation without resolver; computed name
   collision; non-`FieldSet` `Meta.fields_class` value.
3. Wrapper cascade order: gate-only, override-only, both, neither
   (untouched-resolver identity check); original-resolver delegation; async
   original preserved; denial propagation shape (nullable → `null` +
   `errors`; non-null → bubble).
4. Binding: phase-2.5 idempotence (double `finalize_django_types`), owner
   mismatch raise, warning for unsurfaced targets, promotion (declaring
   `fields_class` no longer raises deferred-surface; `aggregate_class` /
   `search_fields` still do).
5. Optimizer: `depends_on` columns appear in `only_fields` when a managed
   field is selected; absent when not; deferred-fetch count assertion for
   the undeclared case (documents the failure mode).

Live (`examples/fakeshop/test_query/`, per the
[live-first coverage mandate][glossary-live-first-coverage-mandate]):

6. Tiered visibility across four user tiers (staff / perm-holder /
   authenticated / anonymous) on a datetime field — full / day / month /
   year precision on the wire.
7. Redaction: non-staff reads `isPrivate` as `false` with **no** `errors`
   entry; staff reads the real value.
8. Denial: anonymous query selecting `updatedDate` gets `null` + an
   `errors` entry with the gate's message; authenticated gets data.
9. Computed field: `displayName` resolves for authenticated, `null` for
   anonymous; query-count assertion proving `depends_on` kept it
   deferred-fetch-free under the optimizer.
10. Composability: gated field still filterable (FieldSet + `FilterSet`)
    and orderable (FieldSet + `OrderSet`) by authorized users; cascade
    narrows first (FieldSet + `apply_cascade_permissions`) — a
    cascade-hidden row yields no node and no field-level error, proving the
    no-existence-leak contract.

Coverage holds at 100% (package `fail_under=100` posture); every new module
is live-tier-first with pure-function unit tests only where the live tier
cannot reach.

## Doc updates

- `docs/GLOSSARY.md` (DB + regen, Slice 5): flip
  [`FieldSet`][glossary-fieldset],
  [`Meta.fields_class`][glossary-metafields-class], and
  [Per-field permission hooks][glossary-per-field-permission-hooks] from
  `planned for 0.1.1` to `shipped (0.1.1)` with the as-built contract; add a
  new `Meta.depends_on` entry (new heading — fold-in is this shipping
  slice's job, not authoring-time).
- `docs/README.md`: capability snapshot gains the field-level behavior row.
- `docs/TREE.md`: regen (new `fieldset/` package; module docstrings
  required by the renderer).
- `README.md` / `GOAL.md` / `TODAY.md`: `GOAL.md`'s "the shipped surface
  already does all but three" paragraph loses the fieldset item;
  `TODAY.md`'s "What products is still waiting for" drops field-level
  redaction/denial; README feature list gains `FieldSet`.
- `KANBAN.md` / `KANBAN.html`: card flip + spec link (DB + regen at wrap).
- `CHANGELOG.md`: `0.1.1` entry (Slice 5 permission grant).

## Risks and open questions

- **Promotion-owner ambiguity (card-text conflict).** The DoD's "(per
  `TODO-BETA-052-0.1.3`)" parenthetical could be read as deferring the
  `Meta.fields_class` promotion to card 052, but the same card's
  Foundation-slice seam says this card "populates the slot and promotes the
  key end-to-end". **Preferred answer (pinned, Decision 8):** promote here;
  052 owns only the later dispatch generalization. **Fallback:** if the
  maintainer reads 052 as the promotion owner, Slice 2 ships the binding
  behind the deferred key and 052 flips it — one-line change, tests keyed on
  a constant.
- **Stale card reference — `BACKLOG.md` item 38.** The card's
  Foundation-slice seam cites "BACKLOG.md item 38 for the `DjangoModelField`
  custom Strawberry field class", but item 38 in today's `BACKLOG.md` is
  the layered manual-relation-override *test policy*; no `DjangoModelField`
  entry exists anywhere in the file. The open question it anchored —
  custom field class vs `strawberry.field(permission_classes=...)` vs
  resolver wrapping — is answered by this spec without it: **resolver
  wrapping** (upstream-parity, zero-config, zero-overhead on unmanaged
  fields). Mapping onto Strawberry's `permission_classes` is rejected —
  `BasePermission.has_permission(source, info, **kwargs)` is
  class-per-policy with a fixed message contract, cannot host the
  gate→override cascade ordering, and would synthesize a permission class
  per managed field for zero consumer benefit; a custom `DjangoModelField`
  field class is unnecessary machinery for the same reason. Recorded here
  per the conflict rule rather than silently reconciled.
- **`check_permissions` naming disambiguation (inherited from card 034's
  open question).** The `(self, request)`-shaped input gates on
  `FilterSet` / `OrderSet` and the new `(self, info)`-shaped read gate share
  the `check_<field>_permission` name. [`spec-034`][spec-034] Decision 2
  pinned both signatures as-is; this spec keeps them (no rename, no
  deprecation) — the classes they live on differ, and the cookbook uses the
  shared name deliberately. Risk is consumer confusion only; mitigated in
  the glossary entries and the fieldset docs' contrast table.
- **`Meta.depends_on` granularity.** Keying by method name (card shape)
  rather than field name means a gate-only field cannot declare
  dependencies. Gates are documented I/O-free so this should never matter;
  if a real case appears, the dict accepts `check_<field>_permission` keys
  as a backward-compatible widening. Preferred: ship method-name keys only.
- **Async gates/overrides.** Deferred (Decision 11). If an async consumer
  needs an async gate, the wrapper already branches on asyncness for the
  original resolver; extending discovery to async methods is additive.
  Preferred: sync-only for `0.1.1`, revisit on demand.
- **Per-row wrapper overhead.** Method-call-only per managed field per row;
  upstream flags the same. Slice 4's query-count tests double as a smoke
  benchmark; no optimization work planned for `0.1.1`.
- **Fakeshop app choice.** Settled: the `products` app already stages the
  four FieldSet classes in `examples/fakeshop/apps/products/fields.py`
  (dormant — the classes subclass an `AdvancedFieldSet` name the framework
  does not ship, and `apps/products/schema.py`'s import of the module is
  commented out; Slice 4 activates them). No new app is added, avoiding the
  recurring schema-module-list pollution class. If a new app ever proves
  necessary, every private schema-module tuple across the test tree must be
  synced (standing repo constraint).

## Out of scope (explicitly tracked elsewhere)

- `Meta.search_fields` — `TODO-BETA-049-0.1.2` ([`spec-049`][spec-049]).
- `AggregateSet` / `Meta.aggregate_class` — the `0.1.3` aggregate card.
- Layer-3 Meta key promotion machinery (dispatched binding form) —
  `TODO-BETA-052-0.1.3`.
- Opt-in node-sentinel redaction tier (`Meta.redaction_mode`) —
  `TODO-BETA-053-0.1.4`; this card's Non-goal note is the seam it amends.
- Product-catalog Layer-3 HTTP GraphQL sweep — `TODO-BETA-056-0.1.5`
  (Slice 4 ships the fieldset-focused live tests; the catalog-wide sweep is
  056's).
- [`Meta.choice_enum_names`][glossary-metachoice-enum-names] — the `0.1.4`-line key, untouched.

## Definition of done

- [ ] `django_strawberry_framework/fieldset/` ships `FieldSet` +
  `FieldSetMetaclass` (`base.py`) and the resolver-binding factory
  (`factories.py`); public import path
  `django_strawberry_framework.fieldset.FieldSet`.
- [ ] `FieldSet` accepts `class Meta: model = Foo` (+ optional
  `depends_on`); declarations are method-based plus class-level
  computed-field annotations; no `Meta.fields` on the FieldSet itself.
- [ ] `Meta.fields_class = FooFieldSet` binds at phase 2.5
  (`_bind_fieldsets`), populates `DjangoTypeDefinition.fields_class`, and
  wires every gate/override/computed field into the owning type's resolver
  chain — no type subclassing, no hand-attached decorators.
- [ ] `Meta.fields_class` is promoted from `DEFERRED_META_KEYS` to
  `ALLOWED_META_KEYS` with `FieldSet`-subclass value validation;
  `aggregate_class` / `search_fields` remain deferred.
- [ ] Denial raises and surfaces as a per-path `errors` entry; redaction is
  a `resolve_<field>` safe value; no deny-value substitution exists in the
  package.
- [ ] `Meta.depends_on` columns merge into the optimizer's `only()`
  projection; the fakeshop computed-field test proves
  deferred-fetch-freedom by query count.
- [ ] Tests under `tests/fieldset/` mirror the source one-to-one; live HTTP
  coverage under `examples/fakeshop/test_query/` exercises tiered
  visibility, redaction, denial, and a computed field across the four user
  tiers; composability tests cover FieldSet + `FilterSet`, + `OrderSet`,
  and + `apply_cascade_permissions` (no existence leak). Coverage holds at
  100%.
- [ ] `GOAL.md`'s `fields.py` cookbook example runs against the shipped
  surface as written.
- [ ] Doc updates land per the Doc-updates section (GLOSSARY via DB + regen
  including the new `Meta.depends_on` entry; TREE regen; KANBAN card wrap
  via DB + regen).
- [ ] `CHANGELOG.md` gains the `0.1.1` entry (Slice 5 permission).
- [ ] The `0.1.1` version quintet lands: `pyproject.toml`, `__version__`,
  `tests/base/test_init.py`, the GLOSSARY package-version row, `uv.lock`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[backlog]: ../BACKLOG.md

<!-- docs/ -->
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply-cascade-permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize-django-types]: GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-get-queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-metaaggregate-class]: GLOSSARY.md#metaaggregate_class
[glossary-metachoice-enum-names]: GLOSSARY.md#metachoice_enum_names
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields-class]: GLOSSARY.md#metafields_class
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metafilterset-class]: GLOSSARY.md#metafilterset_class
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaoptimizer-hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset-class]: GLOSSARY.md#metaorderset_class
[glossary-metasearch-fields]: GLOSSARY.md#metasearch_fields
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-optimizerhint]: GLOSSARY.md#optimizerhint
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-schema-audit]: GLOSSARY.md#schema-audit
[glossary]: GLOSSARY.md
[spec-045]: spec-045-debug_extraction-0_0_15.md
[spec-046]: spec-046-boundary_dry_squeeze-0_0_16.md
[spec-047]: spec-047-beta_release-0_1_0.md
[spec-049]: spec-049-search_fields-0_1_2.md

<!-- docs/SPECS/ -->
[spec-034]: SPECS/spec-034-permissions-0_0_10.md
[spec-038]: SPECS/spec-038-form_mutations-0_0_12.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
