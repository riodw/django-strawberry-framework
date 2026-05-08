# BETTER.md
## Purpose
This file tracks the post-`0.0.5` design surface where `django-strawberry-framework` can be **strictly better** than both `graphene-django` and `strawberry-graphql-django` — not just on-par. Each item here is **explicitly out of scope for `0.0.5`** (`docs/spec-relay_interfaces.md`), which is locked to Relay interfaces, `Meta.interfaces`, and the four `relay.Node` resolver defaults.

Roadmap parity with the inspirations (filters / orders / aggregates / fieldsets / cascade permissions / connection fields, all reproducing the `django-graphene-filters` feature surface) is already tracked in `KANBAN.md` `READY` and `NEXT` columns. **`BETTER.md` is for strategic differentiation** — features neither inspiration ships cleanly that we should pull onto the roadmap once parity items have landed. Items here graduate into `KANBAN.md` cards as they get scheduled.

For each item: what `graphene-django` does, what `strawberry-graphql-django` does, what we'd do differently, why it matters, and a suggested target slice.
## Why these belong in `BETTER.md` and not in `docs/spec-relay_interfaces.md`
The Relay slice has an explicit Goal #4: "Stay tight: no `DjangoConnectionField`, no cascade permissions, no FK redaction sentinels, no node-aware filters, and no broad node-aware optimizer feature work beyond preserving primary-key projection for Relay `id`." None of the items below are part of the Relay machinery; each is a self-contained slice with its own design surface. Putting them in the Relay spec would expand its scope past "make `Meta.interfaces` and Relay Node work" and risks shipping nothing on time.

The one async-related item that **does** have a Relay-specific angle (sync/async support for the four new `resolve_*` defaults) was added to the Relay spec as Decision 9. The broader async-native ORM posture is described below as item 9, because it touches every resolver in the package, not just the Relay ones.
## Tier 1: differentiators no competitor ships cleanly
### 1. Unified declarative permission system in `Meta`
**What `graphene-django` does**: row-level visibility by overriding `get_queryset`; field-level via decorators on resolvers; cascade is a manual permission filter at every relation boundary the consumer writes.

**What `strawberry-graphql-django` does**: `permission_classes=` on individual fields; row-level in queryset hooks; cascade behavior is up to the consumer.

**What `django-graphene-filters` does today**: cascade through `apply_cascade_permissions` plus `is_redacted` sentinels; row/field permission hooks per filter / order / aggregate.

**What we'd do**: one `Meta.permissions` key that combines row, field, and cascade in a single declarative shape, cooperating with the existing optimizer `Prefetch` downgrade so visibility holds across joins:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        permissions = {
            "row": "items.view_item",
            "fields": {"price": "items.view_price"},
            "cascade": True,
        }
```

**Why it matters**: combines `django-graphene-filters` cascade with `strawberry-graphql-django`-style field permissions under one Meta key, with Prefetch-downgrade enforcement neither package provides today. Eliminates the `get_queryset` boilerplate every Django+GraphQL team writes for the common cases. Lets the optimizer reason about the permission boundary at planning time.

**Suggested target**: `0.0.8` — `KANBAN.md` `NEXT-006` already reserves the slot.
### 2. Selection-aware queryset annotations
**What `graphene-django` does**: nothing declarative — consumers add `.annotate()` manually in resolvers and accept that the annotation runs even when not selected.

**What `strawberry-graphql-django` does**: same — manual `.annotate()` in resolvers; the optimizer does not inject annotations.

**What we'd do**: declare annotations in `Meta.annotations` and have the optimizer extension add `.annotate()` only when the corresponding GraphQL field is in the selection set:

```python path=null start=null
from django.db.models import Avg, Count

class ItemType(DjangoType):
    class Meta:
        model = Item
        annotations = {
            "review_count": Count("reviews"),
            "avg_rating": Avg("reviews__rating"),
        }
```

The optimizer already walks the selection tree (`optimizer/walker.py:91`) — it can inject `annotate()` calls into the plan exactly like it injects `only()` and `Prefetch` today.

**Why it matters**: annotations are the most common ORM-side computation, and forcing them to always run is a real performance hit for queries that don't select them. Neither competitor does this; the package's optimizer-first foundation makes it almost free architecturally.

**Suggested target**: `0.0.6` (low cost, optimizer already does the structural work).
### 3. DRF `Serializer`-driven mutations
**What `graphene-django` does**: ships `DjangoModelFormMutation` and `DjangoSerializerMutation` (uses ModelForm or DRF Serializer); behavior is opinionated and does not compose well with the rest of the package's `Meta` shape.

**What `strawberry-graphql-django` does**: provides its own input types and mutation generation; consumers must redeclare validation that already exists in DRF Serializers.

**What we'd do**: reuse DRF Serializers as the source of truth for input shape **and** validation; auto-generate Strawberry input types from the Serializer; wire `is_valid()` / `save()` into the mutation lifecycle:

```python path=null start=null
class CreateItem(DjangoMutation):
    class Meta:
        serializer_class = ItemSerializer
        action = "create"


class UpdateItem(DjangoMutation):
    class Meta:
        serializer_class = ItemSerializer
        action = "update"
        lookup = "id"
```

**Why it matters**: real Django teams have **hundreds** of DRF Serializers with battle-tested validation. Requiring them to redeclare it in GraphQL inputs is a major migration tax that nobody else removes. This is a unique migration story for graphene-django + DRF teams — both move to GraphQL without touching their validation layer.

**Suggested target**: `0.0.9` (after permissions land, since mutations need permission hooks).
### 4. First-class polymorphic and `GenericForeignKey` support
**What `graphene-django` does**: punts on GFK; polymorphic models require manual union types and per-resolver dispatch.

**What `strawberry-graphql-django` does**: same — GFK is unsupported; polymorphic is via Strawberry unions plus consumer dispatch.

**What we'd do today**: we raise `ConfigurationError` on GFK (`types/base.py:417-422`), matching the competitors. We could ship:
- `Meta.polymorphic = True` for `django-polymorphic` integration, generating a Strawberry union of all known concrete subclasses with optimizer-aware `select_related("polymorphic_ctype")` and `iterator()` patterns.
- A GFK resolver that returns a Strawberry union of registered target types, using `ContentType` lookups with prefetched generic relations.

**Why it matters**: GFK and polymorphic models are extremely common in real Django apps (audit logs, comments, attachments, reactions, tagging). Both competitors leaving this on the floor is a real adoption blocker. The package's registry already knows about every `DjangoType`, so the union-target list is free.

**Suggested target**: `0.1.0` (production-grade differentiator; needs careful design).
### 5. Schema diff / breaking-change CLI
**What `graphene-django` does**: provides `graphql_schema` management command (export only); no diff tooling.

**What `strawberry-graphql-django` does**: provides `export_schema`; no diff tooling.

**What we'd do**: ship `dst diff-schema baseline.graphql --against current` (or via Django management command) that reports breaking changes (removed fields, narrowed nullability, removed enum members, type renames, argument changes) with exit code suitable for CI gates. The package already exposes `registry.iter_definitions()` and `iter_types()` so the introspection half is free.

**Why it matters**: production GraphQL APIs need breaking-change detection on every PR. Today teams bolt on `graphql-inspector` (Node.js) or hand-rolled scripts. Nobody in the Django+Python+GraphQL stack ships this. Owning the CI gate is a real CI/CD posture for the package.

**Suggested target**: `0.1.0` or earlier as a standalone management command.
## Tier 2: quality-of-life nobody nails
### 6. Built-in OpenTelemetry / span integration
**What `graphene-django` does**: nothing first-class; consumers wire DataDog / Sentry / OTEL by hand around the view.

**What `strawberry-graphql-django` does**: Strawberry has tracing extensions; the Django ORM half is invisible (you see "GraphQL operation" spans but not the prefetch chain).

**What we'd do**: a `DjangoOptimizerExtension(otel=True)` mode that wraps each plan phase (`dst.optimizer.walk`, `dst.optimizer.queryset`, `dst.resolver.<field>`) plus each resolved relation in OTEL spans, with attributes describing the prefetched fields, projection, and FK-id elision decisions.

**Why it matters**: production observability for GraphQL on Django is a known pain point. We already stash plan metadata on `info.context.dst_optimizer_plan`; promoting that to spans is a small, targeted win competitors cannot match without rebuilding their optimizer.

**Suggested target**: `0.1.x` (ergonomic, not blocking).
### 7. Optimizer "explain" mode as a first-class GraphQL extension
**What `graphene-django` does**: nothing — you read SQL logs and reverse-engineer the plan.

**What `strawberry-graphql-django` does**: nothing — same.

**What we'd do**: promote the existing `info.context.dst_optimizer_plan` stash to a built-in `DST-Plan` extension that returns the plan in the GraphQL response (toggled per-request via a header, query param, or `@plan` directive). Output format: JSON describing `select_related`, `prefetch_related`, `Prefetch` chains, `only()` projection, hints applied, FK-id elisions, and strictness decisions.

**Why it matters**: this is GraphiQL-grade dev tooling specifically for the Django ORM half of GraphQL. Lets developers see "what did the optimizer do for this query?" without grepping logs. Nobody offers this. Particularly powerful when paired with item 1 (permissions): the explain output also shows which permission filters were applied.

**Suggested target**: `0.0.7` (low cost, builds on shipped infrastructure).
### 8. Subscriptions wired to Django signals
**What `graphene-django` does**: Channels integration via `graphene-subscriptions` (third-party, partial); subscriptions are not first-class.

**What `strawberry-graphql-django` does**: Strawberry supports subscriptions; the Django half (signal → push) is up to the consumer.

**What we'd do**: declarative `Meta.subscriptions = ("post_save", "post_delete", "m2m_changed")` that auto-wires the type into Channels (or another async transport) and pushes filtered events to subscribers. Combine with `get_queryset` so subscription visibility respects the same row-level filters that REST/GraphQL queries apply.

**Why it matters**: real-time updates are a common Django+SaaS requirement. Both competitors punt; we can be the package that makes Django GraphQL subscriptions trivial.

**Suggested target**: `0.2.x` (significant; needs Channels or alternative async transport choice).
### 9. Async-native ORM as the default path (broader than the `0.0.5` slice)
**Note**: the Relay-specific async slice (sync/async paths for `_resolve_node_default` and `_resolve_nodes_default`) is already pinned in the Relay spec as Decision 9. This item is the broader push.

**What `graphene-django` does**: bolted-on async via `sync_to_async` everywhere; sync is the default.

**What `strawberry-graphql-django` does**: partial async support; sync is still the most common path in real codebases.

**What we'd do**: every generated resolver is async-by-default; cooperate with Django's native async ORM (`aiter`, `aget`, `acount`, `aupdate`, `adelete`, `aexists`) since 4.2; sync fallback only for ORM operations that don't yet have native async equivalents.

**Why it matters**: the Django + GraphQL stack is becoming async-first (ASGI, Channels, FastAPI-influenced patterns). Owning the canonical "Django GraphQL with native async ORM" surface is a real position to take.

**Suggested target**: incremental — async support is added per slice as Django's async ORM matures. Full async-by-default lands around `0.1.0`.
## Tier 3: production hardening neither addresses well
### 10. Persisted queries with Django cache integration
**What `graphene-django` does**: nothing first-class.

**What `strawberry-graphql-django` does**: Strawberry has persisted queries support; the Django cache integration is up to the consumer.

**What we'd do**: a `dst.persisted_queries` middleware/extension that hashes operations, stores the hash → operation map in any configured `django.core.cache` backend (`Memcached`, `Redis`, `LocMem`, etc.), and rejects unknown operations in production. Tie operation registration to the `dst diff-schema` CLI (item 5) so persisted-query rotation happens at deploy time.

**Why it matters**: production-grade GraphQL APIs allow-list operation hashes to prevent arbitrary query injection and cache responses by hash. Today this is per-team plumbing. Owning the `django.core.cache` integration is a real production-hardening story.

**Suggested target**: `0.1.x` (production hardening; not blocking the parity roadmap).
### 11. Per-tenant / per-role schema variants
**What `graphene-django` does**: nothing — one schema per process.

**What `strawberry-graphql-django` does**: same.

**What we'd do**: parametrize the registry: `schema_for(tenant)` or `schema_for(user_role)` produces a tenant- or role-scoped subset of `DjangoType`s, with field/relation visibility filtered by the same `permissions` system from item 1. Schema-per-tenant is the natural pairing for multi-tenant SaaS.

**Why it matters**: multi-tenant SaaS is a major Django use case. "Different schemas for different roles" is currently a hand-rolled exercise. The registry-and-finalizer architecture from `0.0.4` already supports this — `finalize_django_types()` could take a scope argument. Nobody else has the architectural seam to do this cleanly.

**Suggested target**: `0.2.x` (needs item 1 permissions to land first).
### 12. Soft-delete cooperation
**What `graphene-django` does**: nothing first-class — consumers handle in `get_queryset`.

**What `strawberry-graphql-django` does**: same.

**What we'd do**: first-class integration with `django-safedelete` / `django-softdelete` so soft-deleted rows don't leak through the optimizer's `select_related` / `Prefetch` plans. A `Meta.soft_delete = True` flag (or auto-detection from soft-delete manager) plus a visibility combinator that cooperates with `get_queryset` and the cascade permission system.

**Why it matters**: soft-delete is a common Django pattern (audit requirements, undo, GDPR right-to-erasure with soft-delete-then-hard-delete). Both competitors punt; soft-deleted rows leaking through prefetches is a recurring real bug.

**Suggested target**: `0.1.x` (ergonomic; cooperates with permissions slice).
## Tier 4: ergonomic wins
### 13. `Meta.field_overrides` for scalar fields
**Status**: this is `KANBAN.md` `READY-003` and is mentioned in the Relay spec's "Out of scope" section. Captured here because the design itself will benefit from being framed as a differentiator.

**What `graphene-django` does**: consumers redeclare the field with `graphene.String()` etc.; the framework respects the override but ergonomics are basic.

**What `strawberry-graphql-django` does**: decorator-style field overrides; works but is decorator-heavy.

**What we'd do**: a clean `Meta.field_overrides = {"name": strawberry.field(...)}` key that survives Strawberry's annotation rewrite and presents a stable contract neither package fully exposes today. The relation-field override contract from `0.0.4` is the architectural template (`DjangoTypeDefinition.consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`).

**Why it matters**: scalar overrides are the single most common consumer customization. Today both competitors require knowledge of internals; we can ship a one-line declarative path.

**Suggested target**: `0.0.7` (`READY-003` is already on the board).
### 14. `Meta.computed_fields` for property/method exposure
**What `graphene-django` does**: requires defining a resolver method on the type, e.g. `def resolve_display_name(...)`.

**What `strawberry-graphql-django` does**: same — decorator-driven resolver methods.

**What we'd do**: `Meta.computed_fields = ("display_name",)` auto-binds a model `@property` or `@cached_property` to the GraphQL type, with type inference from the property's return-type annotation. Optionally with `Meta.computed_field_hints` for optimizer hints (e.g. "this property reads `category.name`, prefetch it").

**Why it matters**: every Django app has model properties that should be exposed in GraphQL. Both competitors require boilerplate. We can make this declarative, and the optimizer-hint integration means computed fields don't trigger N+1.

**Suggested target**: `0.0.7` or `0.0.8` (composes with item 13).
## Suggested sequencing
For maximum strategic impact after `0.0.5` (Relay) ships:

1. `0.0.6` — Filters / Orders / Aggregates / FieldSets / Connection field. Parity with `django-graphene-filters` / `KANBAN.md` `NEXT-001` through `NEXT-005`. **No `BETTER.md` items yet** — first reach roadmap parity.
2. `0.0.7` — `Meta.field_overrides` (item 13), `Meta.computed_fields` (item 14), Selection-aware annotations (item 2), Optimizer "explain" extension (item 7). Low-cost ergonomic wins that make `0.0.6` parity feel polished.
3. `0.0.8` — Unified permission system (item 1). `KANBAN.md` `NEXT-006` slot.
4. `0.0.9` — DRF Serializer-driven mutations (item 3). The killer migration story for graphene-django + DRF teams.
5. `0.1.0` — Polymorphic + GFK support (item 4) + Schema diff CLI (item 5). Production-grade differentiation; first stable release.
6. `0.1.x` — Soft-delete (item 12), Persisted queries (item 10), OpenTelemetry (item 6), broader Async-native push (item 9).
7. `0.2.x` — Subscriptions (item 8), Multi-tenant schema variants (item 11). Big bets that need the rest of the foundation.

Items 1, 3, 4, and 5 are the four that, combined, make this package **strictly better** than both competitors rather than just on-par. Everything else is incremental polish layered on top.
## How to use this file
- When scheduling the next slice after parity items land, pull the highest-priority `BETTER.md` item that isn't already on `KANBAN.md`.
- Promote it to a `KANBAN.md` `NEXT-NNN` or `READY-NNN` card.
- Write its `docs/spec-<topic>.md` and follow the existing slice cadence.
- When the slice ships, cross-reference the `BETTER.md` item from the new `KANBAN.md` `DONE-NNN` card so the differentiation story stays traceable.

If a `BETTER.md` item turns out to be wrong (the upstream packages ship it, real-world adopters don't want it, or the architectural cost is too high), strike it through with a one-line note explaining why; do not delete it. The history of rejected differentiators is itself useful design context.
