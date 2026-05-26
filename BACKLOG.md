# BACKLOG.md
## Purpose

This file tracks the strategic-differentiation design surface where `django-strawberry-framework` can be **strictly better** than both `graphene-django` and `strawberry-graphql-django` — not just on-par.

Roadmap parity with the inspirations (filters / orders / aggregates / fieldsets / cascade permissions / connection fields, all reproducing the `django-graphene-filters` feature surface) is tracked in [`KANBAN.md`](KANBAN.md). **`BACKLOG.md` is for strategic differentiation** — ideas neither inspiration ships cleanly that we should consider pulling onto the roadmap once parity items have landed.

Each item below is **an idea, not a commitment**. No item carries a target version. Items here graduate into `KANBAN.md` cards when scheduled.

Every item carries three scores out of 10:

- **Realistic** — how likely the desired functionality is to actually ship given the tech we're building around (no rebuilding Django or Strawberry from scratch; extending Strawberry where needed is fine).
- **Impact** — how much real-world consumer pain the feature relieves.
- **Difficulty** — how big the slice is once you commit to building it.

Items are ordered primarily by **Realistic** (highest first), tiebreaking on **Impact** (descending) then **Difficulty** (ascending). The top of the file is *"likeliest valuable wins"*; the bottom is *"big bets that need careful design"*.

## Relay/interface parking lot

The package's Relay Node foundation deliberately stays limited to `Meta.interfaces`, type-level `relay.Node`, Relay `id: GlobalID!`, and the four default `resolve_*` methods. The ideas below came up while stress-testing that API and should be reconsidered once the foundation has bedded in. Some are parity or roadmap items rather than strict differentiators; keep them here until they graduate into `KANBAN.md` or a dedicated `docs/spec-<NNN>-<topic>-<0_0_X>.md`.

### Root node and connection surface
- Add a schema-level root `node(id:)` field, probably as `DjangoNodeField`, after type-level Node support is proven.
- Add `DjangoConnectionField`, edge / page-info / list-connection wiring, reverse FK and M2M connection upgrades, pagination semantics, and query-count tests under the existing connection-field roadmap.
- Keep `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, and `relay.PageInfo` out of `Meta.interfaces`; those are scalar helpers, annotations, or connection field types, not interfaces a `DjangoType` should inherit.

### Custom Relay ID ergonomics
- First document the Strawberry-native route for non-pk IDs: `id: relay.NodeID[...]` when the backing field is a slug / UUID / other stable value, or a consumer-authored `resolve_id_attr` for custom lookup.
- Reconsider a DRF-shaped `Meta.id_field = "slug"` or `Meta.relay_id_field = "slug"` only if the native route proves too noisy after real use.
- Add reusable GlobalID encode/decode test helpers once root node fields and connection fields start needing repeated round-trip assertions.

### Friendly API shortcuts to evaluate later
- Revisit `Meta.relay = True` or `Meta.node = True` as aliases for `interfaces = (relay.Node,)` only after the explicit `Meta.interfaces` contract is stable.
- Keep the current single-interface normalization (`interfaces = relay.Node` and `interfaces = (relay.Node)`) as the only convenience shortcut for now.
- Avoid new top-level public exports for Relay helpers until there is a concrete field or extension object consumers need to import.

### GlobalID stability and safety
- Treat published GraphQL type names as part of the GlobalID compatibility contract. Before the stable release, add docs or tooling for type renames so cached IDs and persisted client data do not break silently.
- Document that GlobalIDs are opaque identifiers, not secrets and not authorization. `get_queryset`, future permissions, and cascade visibility rules must still enforce access on every lookup.
- Consider migration tooling for GlobalID format changes if `Meta.primary`, composite primary keys, or multiple GraphQL types per model introduce more than one valid encoding.

### Interface validation and schema diagnostics
- Add targeted `ConfigurationError` messages when consumers put non-interface Relay helpers in `Meta.interfaces`, especially `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, and `relay.PageInfo`.
- Add earlier diagnostics for interface field mismatches and nullability conflicts before Strawberry finalization where feasible, especially for non-Relay interfaces.
- Keep string / lazy interface references out until real-world pressure justifies a resolver; eager validation is easier to reason about for the first stable interface API.

### Relay-aware permissions and cache freshness
- Integrate `resolve_node`, future root `node(id:)`, and connection lookups with cascade permissions, redaction, and optimizer `Prefetch` downgrades once the permissions slice lands.
- Pair Relay Node identity with content-versioned Node types (an item below) so clients can get both stable identity and stale-cache detection from declarative Meta options.
- Make optimizer explain output (an item below) show Relay lookup decisions, permission filters, selected primary-key columns, and any GlobalID decode path once those features exist.

### Composite primary keys and multiple type variants
- Design deterministic composite-primary-key GlobalID encoding / decoding after Django's composite-pk API stabilizes; the current behavior rejects this case loudly.
- Resolve how Node lookup chooses a GraphQL type once `Meta.primary` permits multiple `DjangoType`s for the same Django model.
- Revisit whether one model can expose multiple Relay IDs for different public/admin/list/detail variants without breaking client cache identity.

### 7. Optimizer "explain" mode as a first-class GraphQL extension

**Realistic**: 10/10 — We already stash the plan in `info.context.dst_optimizer_plan`; this is just serializing it into the response extensions.

**Impact**: 8/10 — Devtools-grade visibility for the Django ORM half of GraphQL queries; nobody else ships this.

**Difficulty**: 2/10 — Tiny slice — opt-in extension, serialize existing data, document the toggle.

**What `graphene-django` does**: nothing — you read SQL logs and reverse-engineer the plan.

**What `strawberry-graphql-django` does**: nothing — same.

**What we'd do**: promote the existing `info.context.dst_optimizer_plan` stash to a built-in `DST-Plan` extension that returns the plan in the GraphQL response (toggled per-request via a header, query param, or `@plan` directive). Output format: JSON describing `select_related`, `prefetch_related`, `Prefetch` chains, `only()` projection, hints applied, FK-id elisions, and strictness decisions.

**Why it matters**: this is GraphiQL-grade dev tooling specifically for the Django ORM half of GraphQL. Lets developers see "what did the optimizer do for this query?" without grepping logs. Nobody offers this. Particularly powerful when paired with item 1 (permissions): the explain output also shows which permission filters were applied.

### 23. Mutation transactions and idempotency

**Realistic**: 10/10 — `transaction.atomic()` is one line; idempotency-key cache lookup is a standard pattern.

**Impact**: 8/10 — Stripe-style mutation safety nobody in Django + GraphQL ships; production-table-stakes for payment / order / inventory APIs.

**Difficulty**: 3/10 — Two `Meta` keys; small slice; ~30 lines of new code once the mutation surface exists.

**What `graphene-django` does**: nothing — `transaction.atomic` is consumer responsibility; idempotency is unaddressed.

**What `strawberry-graphql-django` does**: same.

**What Stripe and similar production systems do**: every state-changing API has an idempotency-key header; retried requests within a TTL return the cached first response instead of double-executing.

**What we'd do**: two complementary `Meta` keys:

```python path=null start=null
class CreatePayment(DjangoMutation):
    class Meta:
        model = Payment
        atomic = True                      # wrap resolver in transaction.atomic()
        idempotency_key = "request_id"     # input-field name carrying the client-supplied key
        idempotency_ttl = 86400            # seconds; default 24h
```

A second mutation with the same `request_id` within the TTL returns the cached first response without re-executing. Backing store: `django.core.cache` (works with `locmem` / `redis` / `memcached` / database). Atomic-mode failures roll back the database AND skip the idempotency cache write, so retries naturally re-execute.

**Why it matters**: Stripe-style idempotency is table stakes for payment, order, and inventory mutations — exactly the kinds of Django apps that adopt GraphQL. Nobody in the Django + GraphQL ecosystem ships it. Combined with atomic transactions, this makes mutations *safe by default* rather than *safe by careful resolver authorship*. The atomic part is one line; the idempotency part is ~30 lines once a cache lookup helper exists.

### 10. Persisted queries with Django cache integration

**Realistic**: 10/10 — `django.core.cache` is mature; query hashing is a well-known pattern; Apollo Persisted Queries conventions already exist to follow.

**Impact**: 6/10 — Production hardening for query allow-listing; useful but rarely the headline ask.

**Difficulty**: 3/10 — Middleware + cache lookup + management command for rotation; small slice.

**What `graphene-django` does**: nothing first-class.

**What `strawberry-graphql-django` does**: Strawberry has persisted queries support; the Django cache integration is up to the consumer.

**What we'd do**: a `dst.persisted_queries` middleware/extension that hashes operations, stores the hash → operation map in any configured `django.core.cache` backend (`Memcached`, `Redis`, `LocMem`, etc.), and rejects unknown operations in production. Tie operation registration to the `dst diff-schema` CLI (item 5) so persisted-query rotation happens at deploy time.

**Why it matters**: production-grade GraphQL APIs allow-list operation hashes to prevent arbitrary query injection and cache responses by hash. Today this is per-team plumbing. Owning the `django.core.cache` integration is a real production-hardening story.

**Framework integration**: ships **as a standalone primitive first** — a `DjangoPersistedQueryExtension` that hashes incoming operations, looks them up in `django.core.cache`, and rejects unknown hashes in production. This item owns the hash-lookup-and-cache logic, the management-command rotation flow, and the public API for declaring persisted-query allowlists. Once **item 33** (Pluggable per-model DoS policy stack) generalizes — see the sequencing note on item 33 — this primitive folds into the stack as `PersistedQueryGate()` in the pre-parse phase, exposing the same logic through the uniform stacked-class surface. Building this item standalone produces a useful feature today; folding it into item 33's framework later produces a coherent layered defense.

### 37. Public surface promotion discipline

**Realistic**: 10/10 — It's a process rule, not code.

**Impact**: 4/10 — Keeps the package's public API clean and prevents accidental API additions; important but invisible to most consumers.

**Difficulty**: 1/10 — Documentation only; no implementation.

**What this is**: a discipline for adding symbols to the top-level package `__all__`. Every future public symbol must:

- ship implementation end-to-end before becoming public
- have tests pinning consumer-visible behavior
- be marked shipped in `docs/GLOSSARY.md`
- have a stable enough name to live with for the alpha/beta/stable arc
- update top-level `__all__` and subpackage exports together (not one without the other)
- match status markers in `README.md` / `docs/TREE.md` to actual implementation state

**Why it matters**: the current public surface is small (`DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`, `auto`, `__version__`) — keeping it disciplined as the package grows is a real maintainability win. Prevents the *"we accidentally exported a private helper and now we're stuck with it"* class of mistakes.

**Framework integration**: applies to every `BACKLOG.md` item that lands. Each one introducing a new public name (or extending an existing one) must follow this discipline. Could also live in `AGENTS.md` or a `CONTRIBUTING.md` doc — it's a process rule rather than a discrete feature.

### 36. Shared queryset introspection helpers (`utils/queryset.py`)

**Realistic**: 10/10 — Purely additive; non-blocking; no architectural changes.

**Impact**: 3/10 — Internal helpers; consumer-visible only through other features that draw on them.

**Difficulty**: 2/10 — Add helpers as specific features need them; not standalone work.

**What this is**: a place to collect queryset introspection patterns that multiple subsystems end up needing — prefetch-cache awareness (`qs._prefetched_objects_cache.get(...)`), FK-attname resolution, manager-vs-queryset detection, queryset-shape comparison. Currently these helpers are embedded in the optimizer subpackage; if/when other subsystems (mutations, exports, federation) need them, they get promoted to `utils/queryset.py` rather than re-implemented.

**Why it matters**: avoids three copies of the same private-attribute access pattern across three subpackages, and promotes shared utilities to a discoverable home. No standalone value — emerges as the package grows. Add only when at least one shipped feature needs it.

**Framework integration**: composes with any post-stable feature that touches querysets — item 28 (mutation batching), item 30 (streaming downloads), and item 32 (matrix mode) would all draw from this module.

### 38. Layered manual relation override test policy

**Realistic**: 10/10 — Testing policy, not code.

**Impact**: 3/10 — Internal test hygiene; consumer-invisible but keeps the override contract testable across Strawberry version churn.

**Difficulty**: 2/10 — Maintain the existing layering pattern; refactor only if Strawberry internals churn.

**What this is**: the test-layering policy for relation-override coverage. Two layers, both maintained:

- **Package tests** (`tests/types/test_definition_order.py`) intentionally inspect Strawberry internals (`field.base_resolver.wrapped_func.*`) to pin resolver-attachment details and fail early if Strawberry changes the underlying field shape. These are the canary; they break loudly on upstream changes.
- **HTTP tests** (`examples/fakeshop/test_query/test_library_api.py`) pin the consumer-visible contract: a consumer-authored relation resolver shapes `/graphql/` response data. These are the public contract; they survive internal refactors.

Both layers are needed. Internals tests catch breakage early; HTTP tests prove the contract holds regardless of internals.

If Strawberry internals churn becomes noisy, introduce a single named helper (production or test-only) that centralizes the `StrawberryField.base_resolver` access and documents the coupling. Revisit when the deferred `DjangoModelField` custom Strawberry field class lands — production code may need a stable resolver-introspection helper then.

**Why it matters**: the layered approach lets the package adopt Strawberry-internal patterns where useful without coupling consumer-visible behavior to those internals. Keeps test coverage robust against upstream changes.

**Framework integration**: the same policy applies when scalar overrides (BETTER item 13) land — internal tests pin the override attachment; HTTP tests pin the resulting schema shape. Could also live in `AGENTS.md` or a dedicated test-policy doc — it's an ongoing rule rather than a discrete feature.

### 19. Typed error-code envelope with i18n hooks

**Realistic**: 9/10 — Typed Strawberry classes + a code registry + `gettext` bridge are all known patterns.

**Impact**: 8/10 — Major client-DX win; matches DRF conventions; standardizes a surface every team rolls themselves.

**Difficulty**: 3/10 — Small slice — envelope shape + registry decorator + form/serializer error adapters.

**What `graphene-django` does**: errors are free-form strings under `errors[].message`; clients parse human-readable messages or invent their own conventions.

**What `strawberry-graphql-django` does**: same — Strawberry's `extensions.code` convention is freeform; no shipped registry.

**What we already plan**: the mutations cluster (`TODO-ALPHA-026`) ships an `errors: list[FieldError]` envelope with `field` and `message`.

**What we'd do**: extend the envelope to a full typed shape with code, field path, parameters, and a translation hook:

```python path=null start=null
@strawberry.type
class FieldError:
    field: str | None             # dotted path, e.g. "items.0.quantity"
    code: str                      # "validation.unique", "permission.denied", "rate_limit.exceeded"
    message: str                   # localized via Django gettext
    params: dict[str, Any]         # for client-side templating ({"min": 1, "max": 99})
```

Codes come from a package registry that consumers extend (`@register_error_code("payment.declined")`). The translation hook uses Django's `gettext` so messages localize per request locale. DRF's `ValidationError.detail` with its `code` attribute maps in directly; `form.errors.as_data()` Django-Form errors map in via `form.errors.get_json_data()`.

**Why it matters**: client-side error handling beyond *"show the string in a toast"* requires structured codes — branching logic on `code == "payment.declined"` is the table-stakes pattern, and GraphQL's missing standard pushes every team to roll their own (`extensions.code`, Apollo Error Link conventions, the `graphql-errors` package, ad-hoc string parsing). DRF has had `code` on validation errors for years; we can ship the GraphQL equivalent as a first-class envelope.

### 40. Django-model-based GlobalID encoding (instead of GraphQL-type-based)

**Realistic**: 9/10 — Drop-in replacement for the type-name-based encoder. Reuses Django's stable `_meta.label_lower` API; the decoder change is bounded. No new infrastructure; no rebuild of Strawberry's Relay layer.

**Impact**: 8/10 — Eliminates an entire class of *"we renamed a GraphQL type and now every Apollo cache entry is a miss"* production incidents. Aligns durability of GlobalIDs with durability of Django model identity — the right thing. Foundational shift, not a feature add; downstream effects are large (this is what makes item 39 sub-feature 1 a tiny helper instead of a full migration system).

**Difficulty**: 3/10 — The encode and decode functions swap their identifier source (`type._strawberry_definition.name` → `type._meta.model._meta.label_lower`). Add per-model override via `Meta.globalid_strategy` and schema-wide default via Django setting. Small slice.

**What `graphene-django` / `graphene-relay-django` does**: encodes `b64("DjangoObjectTypeName:id")` — the GraphQL type name is the identity. Renaming the GraphQL type breaks every cached client ID, and there's no upstream story for it.

**What `strawberry-graphql-django` does**: same — `b64("TypeName:id")`. Same renaming hazard, same lack of mitigation.

**What the Relay spec actually requires**: GlobalIDs must be (a) *globally unique within the schema*, (b) *opaque to clients*, and (c) *resolve correctly via `node(id:)`*. **The encoding payload is implementation-defined.** The type-name convention is cargo-culted from the Facebook reference implementation, where the GraphQL type name was the natural durable identifier. **In Django apps, it isn't** — the Django model is what's durable; the GraphQL type is a presentation-layer choice that should be free to refactor.

**What we'd do**: invert the durability assumption. Default GlobalID encoding becomes `app_label.model_name:id` (e.g., `b64("products.item:42")`). The GraphQL type name no longer participates in the encoded payload — so renaming `ItemType` → `ProductType` (or splitting one type into `PublicItemType` + `AdminItemType`) **stops breaking cached IDs entirely**. The only events that *can* invalidate an ID are Django-side data migrations (model renames, app moves), and those already require explicit developer intent.

#### Design decision 1: precedence chain

Three sources of truth, in priority order:

1. **Per-model `Meta.globalid_strategy`** — the most specific declaration wins.
2. **Schema-wide setting `DJANGO_STRAWBERRY_FRAMEWORK["RELAY_GLOBALID_STRATEGY"]`** — the project-wide default.
3. **Package default** — `"model"` (the new convention).

This mirrors how every other Django setting works (project setting overrides package default; per-instance override beats project setting).

#### Design decision 2: three modes, plus callable

- **`"model"`** *(new default)* — encodes `app_label.model_name:id`. Example: `b64("products.item:42")`. Reads `type_cls._meta.model._meta.label_lower` for the identifier.
- **`"type"`** *(opt-in fallback)* — encodes `GraphQLTypeName:id`. Example: `b64("ItemType:42")`. Reads `type_cls._strawberry_definition.name`. For teams who want the standard Relay convention — most commonly multi-tenant setups where the GraphQL type discriminates auth scope (e.g., `PublicItemType` and `AdminItemType` should *not* share an ID space).
- **`"type+model"`** *(transitional)* — encodes `b64("ItemType|products.item:42")`. Decoder accepts either fragment for routing. Useful during a one-time migration from `"type"` to `"model"` — emit dual-encoded IDs for a deployment cycle, then switch fully to `"model"` after the old client cache has rolled over.
- **Callable** — full consumer control: `globalid_strategy = lambda type_cls, id_value: ...`. For custom encodings (HMAC-signed opaque tokens, version-prefixed IDs, namespaced multi-tenant IDs).

#### Design decision 3: routing decoded IDs

The decoded `app_label.model_name` resolves to a Django model via Django's app registry. The `registry.get_definition_for_model(model)` lookup returns the `DjangoTypeDefinition` for that model. If multiple `DjangoType`s exist for the same model (`Meta.primary` — `DONE-014-0.0.6`), the primary type wins; consumers reaching for a non-primary type use a Strawberry `... on AdminItemType { ... }` inline fragment.

This works *better* than the type-name encoding for the multi-`DjangoType`-per-model case: instead of needing a separate GlobalID for every type variant over the same model, all variants share one ID space and the schema author picks the discriminator (primary type, or explicit inline fragments).

#### Design decision 4: edge cases handled

| Case | Encoded payload | Decoded routing |
|---|---|---|
| **Standard `DjangoType`** | `b64("products.item:42")` | `apps.get_model("products", "item")` → `ItemType` |
| **Multiple `DjangoType`s per model** (`Meta.primary`) | `b64("products.item:42")` | Resolves to `Meta.primary` type; non-primary via inline fragment |
| **Proxy model** | `b64("blog.proxypost:42")` | `_meta.label_lower` distinguishes proxies even with shared `db_table` |
| **Multi-table inheritance** | `b64("blog.blogpost:42")` | Encode the concrete class; PK is unambiguous (MTI shares PK) |
| **`django-polymorphic`** | `b64("blog.blogpost:42")` | Encode the concrete class via `polymorphic_ctype`; cross-class lookup routes correctly |
| **`Meta.id_field = "slug"`** | `b64("products.item:my-cool-slug")` | Decode the configured field; reuses existing `resolve_id_attr` |
| **Composite primary keys (Django 5.2+)** | `b64("products.item:(2025, 'abc')")` | Already gated by `ConfigurationError` from the foundation slice; when supported, decode the tuple |
| **Model moved between apps** | `auth.user:42` → `accounts.user:42` | Breakage same as a Django data migration. App-rename helper from item 39 sub-feature 1 covers this rare case. |
| **Model class renamed** | `products.item:42` → `products.product:42` | Same as above; rare and intentional. App-rename helper covers it. |

#### Schema-author experience

Project-wide default (one declaration):

```python path=null start=null
# settings.py
DJANGO_STRAWBERRY_FRAMEWORK = {
    "RELAY_GLOBALID_STRATEGY": "model",   # default for every DjangoType
}
```

Per-type overrides where needed (the override is the rare case, not the rule):

```python path=null start=null
# schema.py

class ItemType(DjangoType):
    """Standard case — inherits the schema-wide 'model' strategy."""
    class Meta:
        model = Item
        interfaces = (relay.Node,)


class LegacyAdminItemType(DjangoType):
    """Multi-tenant: this type's IDs must NOT interoperate with ItemType's IDs.
    Auth scope is encoded by the type name, so we want the old behaviour here."""
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        globalid_strategy = "type"          # override: type-name encoding for this type only


class SignedItemType(DjangoType):
    """High-security namespace: IDs are HMAC-signed so consumers can't forge them."""
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        globalid_strategy = signed_globalid_factory   # callable, full custom encoding


class TransitionalType(DjangoType):
    """In the middle of migrating from 'type' to 'model' — emit both for a deployment cycle."""
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        globalid_strategy = "type+model"    # decoder accepts either; encoder emits new form
```

#### Trade-offs vs the standard convention

| Concern | Verdict |
|---|---|
| **Convention deviation** | Real but minor. The Relay spec treats GlobalIDs as opaque — Apollo / Relay Compiler / urql don't care what's inside the payload. The convention is *cargo-culted from Facebook's reference impl*, not required. Documented explicitly; teams who want the standard convention opt into `"type"` per type or project-wide. |
| **Info leak** | Slightly more Django-shape info reaches clients (`products.item` vs `ItemType`). Both base64-decode trivially with one CLI command; this is effectively a wash. Teams who want true opacity use the callable strategy with a salted HMAC. |
| **Backward compatibility** | Pre-`1.0.0` schemas may have already minted `"type"`-format IDs to clients. The `"type+model"` transitional mode lets teams roll over without a flag day. After `1.0.0`, the default is locked. |
| **Multi-tenant with scope-bound IDs** | Some teams want different GraphQL types to mint disjoint ID spaces over the same backing model. They opt into `"type"` per type. Documented as the legitimate use case for the legacy convention. |
| **Debug tooling** | Some introspection tools decode GlobalIDs to show the type name. With `"model"` encoding, they show `products.item:42` instead of `ItemType:42` — arguably more useful for Django-shop debugging. A `manage.py decode_globalid <gid>` helper covers both representations. |

#### Composition with other `BACKLOG.md` items

- **Item 39 (Relay magic)** — sub-feature 1 (GlobalID migrations) collapses to a tiny *"app-move alias helper"* once `"model"` is the default. The full migration system this item replaces was always a workaround for the type-name convention's fragility; with model identity as the durable anchor, the migration system isn't needed for the common case.
- **Item 15 (Content-versioned Node types)** — composes cleanly; content versions are computed off the row data, not the encoding strategy.
- **`BLOCKED-ALPHA-023` (Full Relay story)** — this item is the *recommended encoding strategy* for that card's `1.0.0` Relay surface. Worth pinning the decision *before* `BLOCKED-ALPHA-023` ships so client deployments are minted against the durable identifier from day one. Promoting this item to a `TODO-ALPHA-*` card before `BLOCKED-ALPHA-023` is the cleanest path.

#### Why it matters

GlobalID encoding is one of those decisions that looks like a small implementation detail and turns out to be a foundational architecture commitment. Get it right at `1.0.0` and consumers can refactor their GraphQL schemas freely forever; get it wrong and every type rename becomes a *"please flush your cache and re-login"* event in production.

The standard Relay convention encodes the *presentation layer* (GraphQL type name) into the *durable identity* (GlobalID). For Django apps — where the model is the durable thing and the GraphQL type is a refactor-friendly facade — this is exactly backward. Inverting the convention so that GlobalIDs are tied to `app_label.model_name` puts the durable identifier where it belongs: the part of the system that *already* requires explicit developer intent to change.

The headline pitch: **"Rename your GraphQL types as freely as you rename your Python classes. The Django model is what's durable; GlobalIDs follow that durability."** Nothing else in the Django + GraphQL ecosystem makes that promise.

### 17. Declarative query cost & complexity limits

**Realistic**: 9/10 — Strawberry has a complexity extension to build on; our `FieldMeta` already has the per-field data.

**Impact**: 8/10 — Production DoS protection out of the box; the single most-cited GraphQL production risk.

**Difficulty**: 4/10 — Cost mapping + budget check + typed-error integration; bounded slice.

**What `graphene-django` does**: nothing first-class — DoS via expensive queries is per-team plumbing.

**What `strawberry-graphql-django` does**: Strawberry has a query-complexity extension you can wire up; the per-field cost mapping is consumer-defined and not Django-aware.

**What we'd do**: a `DjangoComplexityExtension` that derives per-field costs from `FieldMeta` (already shipped at `B7`), with a declarative budget at schema construction:

```python path=null start=null
schema = strawberry.Schema(
    query=Query,
    extensions=[
        DjangoOptimizerExtension(),
        DjangoComplexityExtension(max_cost=1000, max_depth=15),
    ],
)
```

Cost defaults: scalar field = `1`, single relation = `5`, many relation = `10 × (limit_argument or default_page_size)`, computed field (item 14) = consumer-declared. `Meta.optimizer_hints` extends to carry per-field cost overrides. Rejections produce a typed error (item 19) with the over-budget path and the field weights that contributed.

**Why it matters**: arbitrary-shape queries are GraphQL's single most-cited production risk. A client that writes `query { allItems { category { allItems { category { ... } } } } }` can exhaust the server in one request. Both upstreams punt; we already walk the selection tree once and have field-cost metadata sitting on every `FieldMeta` instance — declaring a budget is a tiny addition that gives consumers DoS protection out of the box. Closes one of Theo's specific gripes ("GraphQL is a DoS vector by default").

**Framework integration**: ships **as a standalone primitive first** — a `DjangoCostLimitExtension` that derives per-field cost from `FieldMeta`, sums it across the selection tree, enforces a configurable budget, and a separate `DjangoDepthLimitExtension` that counts selection depth and enforces a configurable cap. This item owns the per-field cost-weight derivation, the budget arithmetic, and the depth-counting algorithm — plus the public API for declaring per-type cost weights. Once **item 33** (Pluggable per-model DoS policy stack) generalizes — see the sequencing note on item 33 — these primitives fold into the stack as `CostWeight(per_query=, per_field=)` and `DepthCap(max=)`, exposing the same logic through the uniform stacked-class surface. Shipping standalone first lets the cost-weight declaration syntax and the depth-cap configuration story shake out in real consumer use before they're locked into the stacked-class contract.

### 29. Schema usage analytics

**Realistic**: 9/10 — Strawberry extension + cache + management command + optional Prometheus / OTel export; all known patterns.

**Impact**: 8/10 — Closes the *'hidden cost / schema gravity'* visibility gap from Theo's named talks.

**Difficulty**: 4/10 — Small-to-medium slice; generalizes the deprecation-telemetry extension to all fields.

**What `graphene-django` does**: nothing — there's no visibility into which fields are actually queried, by whom, how often.

**What `strawberry-graphql-django` does**: same.

**What Theo's *"The Hidden Cost Of GraphQL And NodeJS"* names**: you can't see what's slow, what's used, what's dead weight. Schemas accrete fields; nobody knows which still matter. The hidden cost isn't just N+1 — it's the schema gravity that builds up over years and nobody can safely prune.

**What we'd do**: a `DjangoUsageExtension` that records per-field query counts, average wall-clock time, last-queried timestamp, and per-client-identity breakdown. Output through a `manage.py schema_usage` command:

```bash path=null start=null
uv run python manage.py schema_usage --since "30 days ago" --sort hits
# Item.price                14,820 hits   12ms avg   last 12 min ago
# Order.lineItems            8,330 hits   38ms avg   last 4 min ago
# Item.legacyPrice                3 hits  last 47 days ago    ← candidate for removal
# Order.expensiveAggregate        8 hits  4.2s avg            ← performance hot spot
# Customer.deprecatedTotal        0 hits  last seen 90+ days  ← safe to delete
```

Generalizes item 25 (deprecation telemetry) from `@deprecated`-only to **every** field. Backing store is `django.core.cache` with periodic flush to a small audit table. Optional Prometheus / OpenTelemetry export (composes with item 6).

**Why it matters**: directly addresses the *"hidden cost"* critique from Theo's named talk. Without usage data, *"can we delete `Order.deprecatedTotal`?"* and *"why is our schema 800 fields?"* and *"which fields drive our DB load?"* are all guesses. Owning the usage layer turns them into queries. Pairs with items 7 (explain extension), 22 (anti-N+1 CI), and 25 (deprecation telemetry) to give consumers the complete server-side observability story that neither upstream has.

### 5. Schema diff / breaking-change CLI

**Realistic**: 9/10 — `registry.iter_definitions()` gives full introspection; diff algorithms are well-trodden; output formats are well-understood.

**Impact**: 8/10 — Production CI gate for breaking-change detection — nobody in the Django + Python + GraphQL stack ships this today.

**Difficulty**: 5/10 — Comparison logic + format design + exit-code policy + CI integration docs; bounded slice.

**What `graphene-django` does**: provides `graphql_schema` management command (export only); no diff tooling.

**What `strawberry-graphql-django` does**: provides `export_schema`; no diff tooling.

**What we'd do**: ship `dst diff-schema baseline.graphql --against current` (or via Django management command) that reports breaking changes (removed fields, narrowed nullability, removed enum members, type renames, argument changes) with exit code suitable for CI gates. The package already exposes `registry.iter_definitions()` and `iter_types()` so the introspection half is free.

**Why it matters**: production GraphQL APIs need breaking-change detection on every PR. Today teams bolt on `graphql-inspector` (Node.js) or hand-rolled scripts. Nobody in the Django+Python+GraphQL stack ships this. Owning the CI gate is a real CI/CD posture for the package.

### 27. TanStack Query / React Query first-class output mode

**Realistic**: 9/10 — TanStack hook generation is straightforward; depends on item 20 for auto-invalidation but the codegen part is bounded.

**Impact**: 8/10 — Closes the *'Apollo Cache duplicates React Query'* gap that drives the Svelte / vanilla-TS crowds away.

**Difficulty**: 5/10 — Output template + small runtime + integration with item 20's invalidation block.

**What `graphene-django` does**: nothing — Apollo Client or urql is the default; React Query users wire it up manually with `useQuery(['items'], () => fetchGraphQL(...))` boilerplate.

**What `strawberry-graphql-django` does**: same.

**What `TanStack Query` / `React Query` users complain about**: *"Apollo Cache duplicates React Query."* If you already manage server state with React Query in the rest of your app, having Apollo's normalized cache for one endpoint adds complexity, bundle size, and mental-model friction for no win. Theo + t3.gg's stack documents this explicitly; the Svelte and Vue communities echo it.

**What we'd do**: extend the codegen from items 21 / 26 with a TanStack Query output mode emitting typed hook signatures:

```typescript path=null start=null
// generated by `manage.py export_schema --emit tanstack`
import { useItemsListQuery, useItemCreateMutation } from "./generated/dst-tanstack";

const { data, isLoading } = useItemsListQuery({ filter: { name: "foo" } });

const createItem = useItemCreateMutation();
await createItem.mutateAsync({ name: "bar" });
// TanStack invalidates affected queries automatically by reading
// `extensions["dst.invalidations"]` from item 20.
```

Generated hooks integrate with item 20 (mutation invalidation gossip): the wrapping `mutationFn` reads `extensions["dst.invalidations"]` and calls `queryClient.invalidateQueries(...)` for every entity the server says is affected. **No manual `onSuccess: () => queryClient.invalidateQueries(['items'])`** — the server tells the client what to invalidate.

**Why it matters**: TanStack Query is the canonical *"Apollo Cache is overkill"* alternative, and React Query users on the receiving end of an Apollo-driven GraphQL backend currently glue everything by hand. Owning the integration means consumers get React Query's simpler mental model (queryKey / staleTime / `useInfiniteQuery` / optimistic updates) without losing GraphQL's server-side wins (single endpoint, schema-validated requests, typed mutations). This is the *"GraphQL backend + React Query frontend"* configuration that opinionated frontend devs reach for today; nobody pre-wires it. Combined with item 26, our codegen output covers both the Apollo crowd and the TanStack crowd from one declaration.

### 21. Built-in TypeScript / client codegen via management command

**Realistic**: 9/10 — Codegen is a known pattern; we have introspection via `iter_definitions()`.

**Impact**: 8/10 — Closes the *'tRPC has type safety without separate codegen ceremony'* gap entirely.

**Difficulty**: 6/10 — Substantial output-template work; multiple emit modes (TypeScript / jsdoc / Dart / etc.).

**What `graphene-django` does**: nothing first-class — `graphql-codegen` (Node.js / TypeScript toolchain) is the de facto solution. Adds a separate runtime, build step, and dependency tree to every Django+GraphQL frontend.

**What `strawberry-graphql-django` does**: same — third-party codegen tooling.

**What `tRPC` does**: end-to-end type safety by sharing the TypeScript source between server and client. No codegen step. Theo's *"The Truth About GraphQL"* points at this as a major win for tRPC over GraphQL.

**What we'd do**: extend the planned `export_schema` management command (`TODO-ALPHA-018`) with `--emit` modes that produce client-ready type definitions for queries, mutations, fragments, and the typed-error envelope from item 19:

```bash path=null start=null
uv run python manage.py export_schema \
  --emit typescript \
  --output frontend/src/generated/graphql.ts

uv run python manage.py export_schema --emit jsdoc --output frontend/src/generated/graphql.js
uv run python manage.py export_schema --emit dart   --output mobile/lib/generated/graphql.dart
```

Output mirrors `graphql-codegen` conventions (TypeScript discriminated unions for unions, named-input types, branded scalar types, generated query/mutation hook signatures for Apollo / urql / SWR) but ships inside the package and runs without Node.

**Why it matters**: this is the direct answer to *"GraphQL needs a separate codegen toolchain in another language."* Theo's tRPC argument — type safety with less ceremony — only wins if you treat codegen as separate; bundling it in the management command closes that gap. Particularly powerful for the Svelte / vanilla-TypeScript communities that resist heavy Apollo tooling. Also closes the *"different per-team output conventions"* problem: every team using this package gets the same generated client shape.

### 2. Selection-aware queryset annotations

**Realistic**: 9/10 — Optimizer walker already does selection-tree walking and injects `select_related` / `only()` into the plan; annotation injection follows the same pattern.

**Impact**: 7/10 — Real per-query perf win for the common case of computed columns that aren't always selected — a common Django pattern.

**Difficulty**: 4/10 — Three integration sites in the walker / plan / queryset assembly; well-scoped slice.

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

The optimizer already walks the selection tree (`optimizer/walker.py::_walk_selections`) — it can inject `annotate()` calls into the plan exactly like it injects `only()` and `Prefetch` today.

**Why it matters**: annotations are the most common ORM-side computation, and forcing them to always run is a real performance hit for queries that don't select them. Neither competitor does this; the package's optimizer-first foundation makes it almost free architecturally.

### 18. HTTP-spec-compliant transport (GET + caching headers + status codes)

**Realistic**: 9/10 — Strawberry's view largely supports GraphQL-over-HTTP; we polish the Django adapter and add `Cache-Control` / `ETag` glue.

**Impact**: 7/10 — CDN-friendliness is a real frontend win; closes one of the biggest GraphQL-vs-REST objections.

**Difficulty**: 4/10 — View rewrite + content negotiation + persisted-query GET path + ETag composition; modest slice.

**What `graphene-django` does**: `POST` only by default; arbitrary `200 OK` even on validation failure; no `Cache-Control` / `ETag` / content negotiation. Effectively un-cacheable at any HTTP layer.

**What `strawberry-graphql-django` does**: Strawberry's view supports the [GraphQL-over-HTTP spec](https://graphql.github.io/graphql-over-http/) — `GET` for safe queries, status codes for parse/validation failures, content negotiation. The Django adapter inconsistently wires these.

**What we'd do**: ship a Django-aware GraphQL view that:
- accepts `GET` for safe queries with persisted-query hashes (CDN-cacheable, browser-cacheable, replay-safe)
- returns proper HTTP status codes (`400` for parse/validation, `401` / `403` for auth failures, `200` only for successful execution)
- sets `Cache-Control` based on a `Meta.cache_ttl` declared on the top-level queried types
- emits `ETag` from the content-versioned-node hash when item 15 is active, enabling `If-None-Match` short-circuits
- respects `Accept: application/graphql-response+json` content negotiation per the GraphQL-over-HTTP spec

**Why it matters**: CDN-unfriendly `POST`-only transport is one of the most-cited frontend complaints about GraphQL. Apollo Persisted Queries solves the safe-query-via-GET half client-side; we can solve the whole thing server-side once for everyone. Ties together item 10 (persisted queries) and item 15 (content-versioned nodes) so a single response can be cached at the CDN edge, the browser, and the Apollo client — three caches deep — keyed on the operation hash and version.

### 24. Per-resolver rate limiting

**Realistic**: 9/10 — Django cache + interceptor pattern is standard; rate-limit math is well-known.

**Impact**: 7/10 — Field-level rate limits are more useful than endpoint-level; closes a real DoS gap.

**Difficulty**: 4/10 — Rate-limit logic + per-scope keys + typed-error integration; modest slice.

**What `graphene-django` does**: nothing — middleware can rate-limit the `/graphql` endpoint as a whole, but not per-field.

**What `strawberry-graphql-django` does**: same.

**What we'd do**: `Meta.rate_limit` for both types (per-resolver) and mutations:

```python path=null start=null
class HeavyReport(DjangoType):
    class Meta:
        model = ReportSnapshot
        rate_limit = {"user": "10/min", "global": "100/min"}


class GenerateReport(DjangoMutation):
    class Meta:
        model = ReportSnapshot
        action = "create"
        rate_limit = {"user": "1/hour"}
```

Backed by `django.core.cache`. Rejections produce a typed error (item 19) with `code="rate_limit.exceeded"` and a retry-after timestamp. Per-resolver / per-user / per-IP / per-tenant scopes.

**Why it matters**: GraphQL's *"client picks the shape"* model means individual fields can be very expensive — and endpoint-level rate limiting can't distinguish a cheap `currentUser` query from an expensive `generateReport`. Field-level limits are far more useful. Pairs with item 17 (cost analysis) for layered DoS protection: cost limit rejects pathological *shapes*; rate limit rejects pathological *frequency*.

**Framework integration**: ships **as a standalone primitive first** — a `DjangoRateLimitExtension` exposing per-resolver rate-limit decorators / `Meta` keys (anonymous tier, authenticated tier, staff tier) and a separate `DjangoCircuitBreakerExtension` for aggregate auto-pause when global rates exceed a threshold. This item owns the cache-backed rate-limit math, the per-scope key derivation, and the circuit-breaker state machine — plus the public API for declaring per-type and per-field rate budgets. Once **item 33** (Pluggable per-model DoS policy stack) generalizes — see the sequencing note on item 33 — these primitives fold into the stack as `RateLimit(anon=, user=, staff=)` and `CircuitBreaker(global_rate=)` in the check_per_field phase, exposing the same logic through the uniform stacked-class surface. Shipping standalone first means the rate-limit declaration syntax and the per-tier key derivation get to settle on real production deployments before they're absorbed into the stacked-class contract.

### 6. Built-in OpenTelemetry / span integration

**Realistic**: 9/10 — OTel Python SDK is mature; we already stash plan metadata in `info.context`.

**Impact**: 6/10 — Production observability win, but DataDog/Sentry users will still wire their own tooling for non-OTel paths.

**Difficulty**: 3/10 — Wrap existing plan phases in spans plus per-resolved-relation spans; small slice.

**What `graphene-django` does**: nothing first-class; consumers wire DataDog / Sentry / OTEL by hand around the view.

**What `strawberry-graphql-django` does**: Strawberry has tracing extensions; the Django ORM half is invisible (you see "GraphQL operation" spans but not the prefetch chain).

**What we'd do**: a `DjangoOptimizerExtension(otel=True)` mode that wraps each plan phase (`dst.optimizer.walk`, `dst.optimizer.queryset`, `dst.resolver.<field>`) plus each resolved relation in OTEL spans, with attributes describing the prefetched fields, projection, and FK-id elision decisions.

**Why it matters**: production observability for GraphQL on Django is a known pain point. We already stash plan metadata on `info.context.dst_optimizer_plan`; promoting that to spans is a small, targeted win competitors cannot match without rebuilding their optimizer.

### 25. Field-level deprecation telemetry

**Realistic**: 9/10 — Strawberry extension that counts hits + cache persistence + management command; all known patterns.

**Impact**: 6/10 — Closes the deprecation loop — turns *'is anyone still using this field?'* into a query.

**Difficulty**: 3/10 — Small slice — extension + cache layer + report command.

**What `graphene-django` does**: `@deprecated` annotations exist; nobody tracks whether deprecated fields are still in use.

**What `strawberry-graphql-django` does**: same — `deprecation_reason` shows up in introspection, but field-usage is invisible.

**What we'd do**: a `DjangoDeprecationTelemetryExtension` that counts hits on every `@deprecated`-marked field, keyed by client identity (configurable: header, auth subject, anonymous), and exposes:
- a management command (`manage.py deprecation_report --since "30 days ago"`) showing top consumers of each deprecated field, with last-seen timestamp and total hit count
- a periodic email / webhook for product owners
- an opt-in auto-removal gate: deprecated fields whose usage stays at zero for N days get flagged as safe-to-delete (or, with maximum boldness, removed automatically on the next schema build)

**Why it matters**: deprecation is the GraphQL-recommended migration path (additive schema evolution, mark old, add new), but nobody actually tracks adoption. Teams either remove deprecated fields blind and break clients, or never remove them and accumulate schema cruft. Owning the telemetry closes that loop and turns *"is anyone still using `Order.deprecatedTotal`?"* from a guessing game into a query.

### 3. DRF `Serializer`-driven mutations

**Realistic**: 8/10 — DRF exposes `.is_valid()` / `.save()` cleanly; serializer-field-to-Strawberry-input mapping is a known pattern.

**Impact**: 10/10 — The killer migration story for graphene-django + DRF teams — existing Serializers move to GraphQL without re-declaring validation.

**Difficulty**: 6/10 — Soft-dep import handling + input-type generation + mutation lifecycle wiring; modest slice once the mutation surface exists.

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

### 26. tRPC-style invokable-function client codegen

**Realistic**: 8/10 — Codegen of typed wrappers around fetch is a known pattern; runtime wrapper is small (~2KB).

**Impact**: 10/10 — The deepest response to Theo's *'I just want to call a function'* critique; dissolves the strongest tRPC argument.

**Difficulty**: 7/10 — Output formats + transport wrapper + per-language targets; substantial output work.

**What `graphene-django` does**: nothing — frontends write `gql\`...\`` strings and `useQuery(GET_ITEMS, { variables: ... })` boilerplate. Type safety requires a separate `graphql-codegen` toolchain.

**What `strawberry-graphql-django` does**: same.

**What `tRPC` does**: server routers export their own TypeScript types; clients call `await client.items.list({ filter })` directly — no codegen step, no query strings, no fragments to manage. **This is the specific ergonomic Theo names in *"I Am Done With GraphQL After 6 Years"* as the reason he picks tRPC for new projects.**

**What we'd do**: extend the codegen from item 21 to emit not just type definitions but **invokable typed functions** — one per GraphQL field. Generated module:

```typescript path=null start=null
// generated by `manage.py export_schema --emit typescript-client`
import { client } from "./generated/dst";

const items   = await client.queries.items.list({ filter: { name: "foo" } });
const order   = await client.queries.orders.byId(orderId);
const created = await client.mutations.items.create({ name: "bar" });
```

Each function bundles the operation string and the variables shape; a tiny (~2KB) fetch wrapper sends it as a GraphQL request. No Apollo, no urql, no fragments, no manual variable typing. Type errors surface at the call site. Each generated function carries the operation hash too, so item 10 (persisted queries) and item 18 (HTTP-spec transport) work out of the box.

**Why it matters**: this is the direct response to Theo's *"I just want to call a function and get typed data back"* — the deepest complaint in *"I Am Done With GraphQL After 6 Years"*. tRPC wins on this exact ergonomic and on nothing else. Owning the invokable-client surface means the consumer's frontend DX is `await client.queries.items.list(...)` — **indistinguishable from tRPC** — while the wire protocol is still GraphQL with all the cost-analysis, persisted-query, CDN-caching, schema-evolution benefits intact (items 17 / 10 / 18 / 25). This single feature dissolves the strongest argument Theo and `t3.gg` make against GraphQL.

### 33. Pluggable per-model DoS policy stack

**Realistic**: 8/10 — The framework itself is a standard Strawberry extension that walks a list of policy classes and dispatches hooks; the 14 built-in policy classes are mostly 20-30 line patches each. The harder pieces (`WallClockBudget` cancellation, `CircuitBreaker` global state) are bounded.

**Impact**: 10/10 — Per-model declarative DoS protection is what every Django + GraphQL team eventually rolls themselves. Owning the stacked-DRF-style mental model is the headline answer to *"GraphQL DoS protection is hard"* and the comprehensive security-positioning win on the list.

**Difficulty**: 7/10 — Framework + 14 policy classes is meaningful surface; total LOC is moderate-large but no single piece is intractable. Most difficulty is concentrated in two policies (`WallClockBudget` cancellation, `CircuitBreaker` cross-worker coordination).

**Sequencing**: this item is the *late-stage generalization*, not the next slice. Land items 10 (Persisted queries), 17 (Cost & complexity limits), 24 (Per-resolver rate limiting), and 29 (Schema usage analytics) as **independent primitives first**, each with its own clear win and its own settled API surface from real consumer use. Once 3-4 primitives have shipped and the patterns have shaken out, generalize them into the stacked-class architecture described below. At that point the catalog of 14 policy classes in "Design decision 4" maps to *already-shipped behavior wrapped in a uniform composition surface* — not to greenfield design. Shipping the policy stack first locks in API shape (hook signatures, ordering semantics, error-code identifiers) before any of the underlying primitives have been pressure-tested in production, which is exactly the trap DRF avoided by letting `permission_classes` emerge from individual `IsAuthenticated` / `IsAdminUser` / etc. before there was a stacked pattern at all.

**What `graphene-django` does**: nothing — DoS defense is entirely per-team plumbing. Teams roll their own depth limiters, alias counters, and rate limiters from scratch.

**What `strawberry-graphql-django` does**: Strawberry has a query-complexity extension that can be wired globally; everything else is per-team. No per-type scoping for any defense.

**What `DRF` does** (the inspiration): `permission_classes = [IsAuthenticated, IsOwner]` is the canonical Django-shaped *stacked, composable, declarative* policy pattern. Each permission is a small focused class; classes compose via list order; per-view override is one line.

**What we'd do**: borrow DRF's stacked-class pattern for DoS protection. A `Meta.dos_classes` list on each `DjangoType` (and `DjangoMutation`) declares the per-model defense stack. A schema-construction-time `global_dos_classes` list declares the operation-wide defaults. Each policy is a small focused class implementing one or more hook methods; a `DjangoDoSExtension` walks the stack in declaration order and dispatches each hook at the appropriate phase of the request lifecycle. Ship 14 built-in policy classes covering the major attack vectors; consumers extend with custom subclasses for niche needs.

#### Design decision 1: stacked classes, not a single sidecar

The other `*_class` Meta keys (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`) each encapsulate **a single coherent concern** — one `FilterSet`, one `OrderSet`. They're sidecars because their concern is conceptually unified.

DoS protection isn't one thing. It's a layered defense composed of: pre-parse checks (body size, batch cap), pre-execute checks (alias cap, depth cap, fragment expansion), per-field checks (rate limit, pagination cap), execution wrappers (wall-clock budget), bypass policies (admin skip), cost contributions (per-query weighting). Forcing all of these into one `WeatherDoS` class either bloats the class or pushes composition back onto the consumer. Stacked classes compose for free.

#### Design decision 2: hook architecture

Each policy class implements a subset of these hooks; the framework calls whatever's defined and skips the rest:

```python path=null start=null
class DoSPolicy:
    """Base class — override the hooks your policy needs. All optional."""

    def check_pre_parse(self, request) -> None:
        """Before GraphQL parsing. Raise to reject. Use for body-size, batch-cap, etc."""

    def check_pre_execute(self, info, query_ast) -> None:
        """After parse, before execution. Raise to reject. Use for alias-cap, depth-cap, etc."""

    def evaluate_cost(self, info, field, args) -> int:
        """Contribute to the static cost analysis budget. Return 0 if not applicable."""

    def check_per_field(self, info, field, args) -> None:
        """Run for each resolved field. Raise to reject. Use for rate limits, pagination caps."""

    def wrap_execution(self, info, execute):
        """Wrap the whole execution. Use for wall-clock budgets, instrumentation."""

    def short_circuit(self, info) -> bool:
        """Return True to skip all subsequent policies in the stack. Use for AdminBypass."""
```

The framework walks the stack in declaration order at each phase. A pre-execute phase visits every policy's `check_pre_execute`; a per-field phase visits every policy's `check_per_field`; etc. Short-circuit policies stop the stack at that phase only — `AdminBypass` in `check_per_field` doesn't skip the already-completed pre-parse checks.

#### Design decision 3: schema-wide defaults + per-model overrides

Two levels of declaration:

- **Schema-wide** (via `DjangoDoSExtension(global_dos_classes=[...])`): applies to every operation. Use for cross-cutting policies (body size, batch cap, introspection lockdown).
- **Per-model** (via `Meta.dos_classes` on each `DjangoType` / `DjangoMutation`): applies only to operations on that type. Use for type-specific tuning (low limits on expensive types, generous limits on cheap ones).

The two stacks compose additively at request time:

```
effective_stack = global_dos_classes + meta.dos_classes
```

A per-model `AdminBypass()` at the top of `dos_classes` short-circuits before any per-model policy runs — but **it does not short-circuit *global* policies** (those have already run by then). This is the sensible default: *"admin bypasses model-level cost checks but still respects the schema-wide body-size limit."* For full bypass of global policies, declare `AdminBypass(global_too=True)` in the *global* stack itself, before all other global policies.

#### Design decision 4: the built-in policy class catalog

Ship a complete set out of the box; consumers compose them like DRF permissions:

| Class | Phase | Purpose | Common stacking |
|---|---|---|---|
| `BodyMaxSize(megabytes)` | pre-parse | Reject oversized request bodies | schema-wide |
| `BatchOperationCap(max)` | pre-parse | Reject multi-operation arrays above N | schema-wide |
| `CSRFRequired()` | pre-parse | Require Django CSRF token | per-mutation |
| `PersistedQueryGate()` | pre-parse | Only accept persisted-query hashes — **realization of item 10** | schema-wide |
| `IntrospectionLockdown(allow_for)` | pre-execute | Disable introspection except for the given auth tier | schema-wide |
| `DepthCap(max)` | pre-execute | Reject queries deeper than N — **realization of item 17 (depth half)** | schema-wide |
| `AliasCap(max)` | pre-execute | Reject queries with more than N aliases | schema-wide |
| `FragmentExpansionCap(max)` | pre-execute | Reject fragment expansions above N | schema-wide |
| `CostWeight(per_query=, per_field=)` | evaluate_cost | Static cost contribution — **realization of item 17 (cost half)** | per-model |
| `PaginationCap(max_first=, max_last=)` | check_per_field | Reject pagination args above max | per-model |
| `RateLimit(anon=, user=, staff=)` | check_per_field | Per-tier frequency cap — **realization of item 24 (rate-limit half)** | per-model + schema |
| `CircuitBreaker(global_rate=)` | check_per_field | Auto-pause type when aggregate rate exceeds threshold — **realization of item 24 (circuit-breaker half)** | per-model |
| `WallClockBudget(seconds)` | wrap_execution | Abort if execution exceeds time budget | per-model |
| `AdminBypass(global_too=False)` | short_circuit | Skip remaining policies for staff users | per-model or schema |

#### Design decision 5: ordering semantics

Stack order matters — the framework walks declaration order at each phase. The recommended convention (the template generator emits stacks in this order):

1. **Bypass policies first** (`AdminBypass`) — fast skip for trusted users
2. **Cheap pre-parse checks** (`BodyMaxSize`, `BatchOperationCap`) — reject before parsing
3. **Auth gates** (`CSRFRequired`, `PersistedQueryGate`) — fail fast on unauthorized requests
4. **Pre-execute analysis** (`DepthCap`, `AliasCap`, `FragmentExpansionCap`, `IntrospectionLockdown`) — reject pathological ASTs before any resolver runs
5. **Static cost analysis** (`CostWeight`) — predict execution cost from the AST
6. **Per-field runtime checks** (`RateLimit`, `PaginationCap`, `CircuitBreaker`) — during execution
7. **Execution wrapping** (`WallClockBudget`) — outermost

The framework doesn't enforce ordering — consumers compose freely — but the default `Meta.dos_classes` template generator and a `manage.py audit_dos` linter emit stacks in this order and warn on unusual layouts.

#### Schema-author experience

```python path=null start=null
from django_strawberry_framework.dos import (
    AdminBypass, CostWeight, RateLimit, WallClockBudget,
    PaginationCap, CircuitBreaker, CSRFRequired,
)


class TimeType(DjangoType):
    """Cheap, called constantly — generous limits."""
    class Meta:
        model = ClockTick
        dos_classes = [
            CostWeight(per_query=1),
            RateLimit(anon="100/min", user="1000/min"),
        ]


class WeatherType(DjangoType):
    """Expensive external call, slow — strict limits."""
    class Meta:
        model = WeatherSnapshot
        dos_classes = [
            AdminBypass(),                              # staff skip the rest
            CostWeight(per_query=50),
            RateLimit(anon="2/min", user="20/min"),
            PaginationCap(max_first=100),
            WallClockBudget(seconds=5),
        ]


class CreatePayment(DjangoMutation):
    """Money — paranoid defaults."""
    class Meta:
        model = Payment
        dos_classes = [
            CSRFRequired(),
            RateLimit(user="3/min"),
            WallClockBudget(seconds=10),
            CircuitBreaker(global_rate="100/min"),     # auto-pause on aggregate abuse
        ]
```

Schema-wide construction:

```python path=null start=null
from django.conf import settings
from django_strawberry_framework.dos import (
    DjangoDoSExtension,
    BodyMaxSize, BatchOperationCap, AliasCap, FragmentExpansionCap,
    DepthCap, IntrospectionLockdown, PersistedQueryGate,
)


schema = strawberry.Schema(
    query=Query,
    extensions=[
        DjangoOptimizerExtension(),
        DjangoDoSExtension(
            global_dos_classes=[
                # Reject obviously-bad requests before parsing
                BodyMaxSize(megabytes=1),
                BatchOperationCap(max=5),

                # Reject pathological ASTs before execution
                AliasCap(max=10),
                FragmentExpansionCap(max=20),
                DepthCap(max=12),

                # Production lockdown
                IntrospectionLockdown(allow_for="staff"),

                # Persisted queries only in production
                *([PersistedQueryGate()] if not settings.DEBUG else []),
            ],
            cost_budget=1000,                  # per request
            anonymous_budget_multiplier=0.1,   # anon gets 10% of the cost budget
        ),
    ],
)
```

Sensible defaults: if a `DjangoType` declares no `Meta.dos_classes`, the global stack still applies. If a schema is built without `DjangoDoSExtension`, no DoS protection is active — consumers opt in explicitly. The package ships a `manage.py audit_dos` command that warns on schemas with no DoS extension configured in production.

#### Composition with other `BACKLOG.md` items

**This item is the architectural seam** through which several other items deliver their concrete behavior. The relationship is *additive, not replacement*: items 10 / 17 / 24 remain meaningful standalone designs — they describe **what** the policy does; this item describes **how** policies plug together. Building any one of them in isolation produces a useful feature; building all three through the framework produces a *coherent* defense.

- **Item 10 (Persisted queries with Django cache integration)** — ships as the `PersistedQueryGate()` policy class. Item 10 owns the hash-lookup-and-cache logic; this item owns the hook timing and the per-model / global stack composition.
- **Item 17 (Declarative query cost & complexity limits)** — ships as `CostWeight(...)` (the cost half) and `DepthCap(...)` (the depth half). Item 17 owns the per-field cost-weight derivation from `FieldMeta` and the budget arithmetic; this item owns the per-model / global stack composition.
- **Item 24 (Per-resolver rate limiting)** — ships as `RateLimit(...)` (the rate-limit half) and `CircuitBreaker(...)` (the circuit-breaker half). Item 24 owns the cache-backed rate-limit math and the per-scope key derivation; this item owns the hook timing and per-model composition.

Beyond the three subsumed items, the framework composes with:

- **Item 19 (Typed error-code envelope)** — every policy rejection emits a typed error: `code="dos.body_too_large"`, `code="dos.rate_limit_exceeded"`, `code="dos.cost_exceeded"`, `code="dos.csrf_missing"`, etc., with the offending policy class and its threshold in `params`.
- **Item 18 (HTTP-spec-compliant transport)** — `BodyMaxSize` rejections return `413 Payload Too Large`; `RateLimit` rejections return `429 Too Many Requests` with `Retry-After`; `CSRFRequired` failures return `403 Forbidden`; `PersistedQueryGate` failures return `404 Not Found`. The framework owns the GraphQL-error-to-HTTP-status mapping in one place.
- **Item 29 (Schema usage analytics)** — the framework records every policy decision (pass / reject / which policy / which threshold) into the usage telemetry, so `manage.py schema_usage` can answer *"which fields are getting throttled?"* and *"who is hitting our circuit breaker?"*
- **Item 25 (Field-level deprecation telemetry)** — a `DeprecationStricter()` policy can be composed on deprecated fields to ratchet rate limits down over time, nudging migrations.
- **Item 8 (Subscriptions via Django signals)** — long-running subscriptions check policies at subscription open (not per-event); a `SubscriptionConcurrencyCap(max_per_user=)` policy would be the right defense for the per-event-flood case.
- **Item 28 (Mutation batching with transactional semantics)** — each mutation in a batch runs its own `Meta.dos_classes` stack independently; the batch endpoint inherits the global stack.
- **Item 30 (Resumable streaming downloads)** — streamable types compose `WallClockBudget` with the snapshot expiry; `RateLimit` applies per concurrent download.

#### Failure modes and edge cases

- **Mutually contradictory policies** (e.g., two `RateLimit` declarations with different caps) — framework warns at schema-build time; the *more restrictive* limit wins by default. Configurable via `DjangoDoSExtension(on_conflict="warn" | "error" | "stricter_wins")`.
- **Slow policy itself** (a custom policy that does a network call inside `check_per_field`) — framework times each policy and emits a warning when total per-policy overhead exceeds the request budget. Suggests caching the policy's state or moving the work to a less hot phase.
- **`WallClockBudget` interrupts mid-resolver** — uses Strawberry's async cancellation for async paths; sync resolvers can't be interrupted mid-call, so the budget is checked at field boundaries. Documented: `WallClockBudget` is fail-fast at the next field for sync code, not mid-resolver.
- **`CircuitBreaker` state across multiple workers** — backed by `django.core.cache`; for accuracy under high concurrency, use a Redis-backed cache. `LocMem` works for dev but counts per-process and produces inflated apparent budgets.
- **`AdminBypass` placement** — if declared anywhere other than the top of a stack, it only skips policies declared *after* it. Documented gotcha; the template generator and `manage.py audit_dos` emit a warning if `AdminBypass` isn't first in its stack.
- **Per-model `dos_classes` on an abstract base class** — inherited by every concrete subclass and additive with each subclass's own declarations. Common pattern: *"all models in this app share these defaults; this specific model adds more."*
- **Empty `dos_classes` on a `DjangoType`** — explicit empty list means *"this type opts out of model-level policies but still gets global ones."* `Meta.dos_classes = None` means *"this type opts out of model-level AND global policies"* (rare; flagged by the audit command).
- **Policy stack length** — framework caps per-stack length at a configurable default (50) to prevent accidental performance issues from over-stacking. Exceeding the cap is a hard schema-build error.
- **Test environments** — `DjangoDoSExtension(enabled=settings.DOS_ENABLED)` toggle so tests can run without rate-limit interference. Default `enabled=not settings.TESTING` if Django's test runner sets that flag.

**Why it matters**: DoS protection is consistently named as the *single biggest GraphQL production risk* — across Theo's talks, the OWASP GraphQL cheat-sheet, every Apollo/Hasura/AWS production-deployment guide, and every team that's ever taken a GraphQL endpoint to a public surface. The standard advice is *"layer multiple defenses"*; the missing piece is **how to declare those defenses ergonomically per model**. Borrowing DRF's stacked-class pattern gives Django developers exactly the mental model they already use for permissions, applied to a defense surface that nobody in the Django + GraphQL ecosystem owns today.

The headline pitch: **"DoS protection composes like DRF permissions — one declaration per model, one composable list, sensible defaults."** That's a sentence no competitor can say. Combined with items 10 / 17 / 24 / 19 / 18 / 29, the layered defense story becomes the most comprehensive in the Django + GraphQL ecosystem.

### 20. Mutation invalidation gossip (companion to content-versioned nodes)

**Realistic**: 8/10 — Server-side declarative `invalidates` + extensions-block emission is straightforward; client SDK (Apollo Link + TanStack helper) is the longer half but well-trodden.

**Impact**: 8/10 — Closes the biggest Apollo Cache pain point — *'why is my list still showing the deleted item?'*

**Difficulty**: 6/10 — Server-side blast-radius tracking + path notation + client SDKs in two ecosystems.

**What `graphene-django` does**: nothing — client cache invalidation after mutation is per-team plumbing.

**What `strawberry-graphql-django` does**: same.

**What Apollo Client and similar normalized caches do**: every team writes `refetchQueries`, `update` callbacks, or `cache.modify(...)` per mutation. The single biggest source of front-end bugs in GraphQL apps is *"why is my list still showing the deleted item?"*

**What we'd do**: every mutation response includes an `extensions["dst.invalidations"]` block listing the GlobalIDs of entities the mutation affected. Mutations declare their blast radius declaratively:

```python path=null start=null
class UpdateOrder(DjangoMutation):
    class Meta:
        model = Order
        invalidates = ("self", "self.items", "self.customer.orders")
```

`self` resolves to the mutation's primary target. Path notation walks relations. Defaults: `create` → `("self",)`, `update` → `("self",)`, `delete` → `("self", "self.<all reverse relations>")`. An opt-in Apollo Link reads the gossip and surgically evicts those cache entries — no manual `refetchQueries` lists, no `cache.modify` boilerplate.

**Why it matters**: pairs with item 15 (content-versioned nodes) to solve both *"is my cached copy stale?"* (versions) and *"what did this mutation change?"* (invalidations) from a single declarative source. This is the front-end side of Theo's *"GraphQL adds complexity without solving the hard problems"* critique: caching is the hard problem, and the GraphQL ecosystem has been silent on the server side of it for a decade.

### 13. `Meta.field_overrides` for scalar fields

**Realistic**: 8/10 — We have the foundation-slice override contract for relation fields; extending it to scalars is incremental work, not rebuilding Strawberry.

**Impact**: 7/10 — Most common consumer customization; closes a small but constant friction point.

**Difficulty**: 5/10 — Strawberry's annotation rewrite timing is the tricky part; need to preserve consumer overrides across `strawberry.type()`.

**Status**: this is `KANBAN.md` `READY-003` and is mentioned in the Relay spec's "Out of scope" section. Captured here because the design itself will benefit from being framed as a differentiator.

**What `graphene-django` does**: consumers redeclare the field with `graphene.String()` etc.; the framework respects the override but ergonomics are basic.

**What `strawberry-graphql-django` does**: decorator-style field overrides; works but is decorator-heavy.

**What we'd do**: a clean `Meta.field_overrides = {"name": strawberry.field(...)}` key that survives Strawberry's annotation rewrite and presents a stable contract neither package fully exposes today. The shipped relation-field override contract is the architectural template (`DjangoTypeDefinition.consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`).

**Why it matters**: scalar overrides are the single most common consumer customization. Today both competitors require knowledge of internals; we can ship a one-line declarative path.

### 12. Soft-delete cooperation

**Realistic**: 8/10 — `django-safedelete` / `django-softdelete` integration patterns are well-trodden; manager detection is straightforward.

**Impact**: 6/10 — Common Django pattern (GDPR / audit / undo); upstream silence here is a real recurring-bug source.

**Difficulty**: 4/10 — Manager detection + queryset filtering across joins + cascade interaction; small-to-medium slice.

**What `graphene-django` does**: nothing first-class — consumers handle in `get_queryset`.

**What `strawberry-graphql-django` does**: same.

**What we'd do**: first-class integration with `django-safedelete` / `django-softdelete` so soft-deleted rows don't leak through the optimizer's `select_related` / `Prefetch` plans. A `Meta.soft_delete = True` flag (or auto-detection from soft-delete manager) plus a visibility combinator that cooperates with `get_queryset` and the cascade permission system.

**Why it matters**: soft-delete is a common Django pattern (audit requirements, undo, GDPR right-to-erasure with soft-delete-then-hard-delete). Both competitors punt; soft-deleted rows leaking through prefetches is a recurring real bug.

### 14. `Meta.computed_fields` for property/method exposure

**Realistic**: 8/10 — Python `@property` / `@cached_property` binding is straightforward; optimizer-hint integration is the harder half.

**Impact**: 6/10 — Boilerplate reduction for a common pattern; modest impact since consumers can already work around it.

**Difficulty**: 5/10 — Type inference from return annotations + optimizer-hint cooperation + cache-key handling.

**What `graphene-django` does**: requires defining a resolver method on the type, e.g. `def resolve_display_name(...)`.

**What `strawberry-graphql-django` does**: same — decorator-driven resolver methods.

**What we'd do**: `Meta.computed_fields = ("display_name",)` auto-binds a model `@property` or `@cached_property` to the GraphQL type, with type inference from the property's return-type annotation. Optionally with `Meta.computed_field_hints` for optimizer hints (e.g. "this property reads `category.name`, prefetch it").

The optimizer-hints half deserves a closer look: properties that traverse relations (`@property def country(self): return self.address.country`) silently trigger lazy-loads under the optimizer's normal plan because the walker never sees the access. `Meta.computed_field_hints = {"country": ["address"]}` declares the dependency so the optimizer's `select_related` / `prefetch_related` plan covers the property's reads. The hint syntax mirrors `OptimizerHint.select_related(...)` / `OptimizerHint.prefetch_related(...)` patterns from the shipped optimizer surface.

**Why it matters**: every Django app has model properties that should be exposed in GraphQL. Both competitors require boilerplate. We can make this declarative, and the optimizer-hint integration means computed fields don't trigger N+1 — even when properties traverse relations the walker can't see by static analysis.

### 16. REST / tRPC escape hatch from the same `DjangoType` declarations

**Realistic**: 7/10 — REST endpoint generation is well-trodden (DRF patterns); main challenge is keeping the declaration DRY without duplicating filter/order/permission logic.

**Impact**: 10/10 — Boldest differentiator on the list — directly answers the *'just use REST'* critique that drives migrants away from GraphQL.

**Difficulty**: 8/10 — Basically a parallel HTTP stack — router, serializer, mutation handler, content negotiation, URL routing.

**What `graphene-django` does**: nothing — REST and GraphQL are separate concerns; teams running both maintain parallel layers.

**What `strawberry-graphql-django` does**: same.

**What `DRF` does today**: REST only; no GraphQL story. Teams running both write their serializers twice.

**What we'd do**: every `DjangoType` declaration can optionally expose a matching DRF-style REST endpoint set, with `Meta.filterset_class`, `Meta.orderset_class`, and `Meta.search_fields` reused as the REST filter/order/search surface. Mutations from `forms/` and `rest_framework/` (`TODO-ALPHA-028`, `TODO-ALPHA-029`) reuse their existing validation chain for `POST` / `PUT` / `PATCH` / `DELETE`. The same declaration powers `/graphql/` and `/api/<name>/`.

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = "__all__"
        filterset_class = filters.ItemFilter
        orderset_class = orders.ItemOrder
        rest = True   # exposes /api/items/ and /api/items/<pk>/ alongside the GraphQL type
```

**Why it matters**: this is the direct response to *"just use REST"* / *"just use tRPC"* (Theo's framing in [The Truth About GraphQL](https://www.youtube.com/results?search_query=theo+the+truth+about+graphql)). The strongest argument against GraphQL is that REST/tRPC give similar product value with less ceremony for most teams. Owning both endpoint shapes from one declaration removes that argument entirely: consumers who want GraphQL get GraphQL; consumers who want REST get REST; the declaration is the same. Nobody in the Django GraphQL space offers this — `graphene-django` + `DRF` users today maintain two parallel object/serializer hierarchies.

### 32. Matrix-mode queries with tabular export formats (CSV / XLSX / Parquet / Arrow)

**Realistic**: 7/10 — Django ORM aggregation is robust; matrix surface is a custom but achievable layer; streaming XLSX / Parquet has soft-dep complexity but no rebuild required.

**Impact**: 10/10 — Closes the *'GraphQL doesn't do reporting'* objection; major BI / dashboard / export use case nobody owns.

**Difficulty**: 8/10 — Multiple sub-features (matrix surface, pivot mode, four export formats, streaming-format integration); substantial slice.

**What `graphene-django` does**: nothing. Tabular reporting is a parallel hand-rolled REST endpoint that generates CSV / Excel by hand.

**What `strawberry-graphql-django` does**: same.

**What `DRF` does**: REST returns nested JSON; CSV requires the third-party `djangorestframework-csv` renderer; no native matrix / pivot semantics. XLSX and Parquet are out of scope entirely.

**What `pandas` / `Metabase` / `Apache Superset` / custom BI backends do**: tabular data with `groupby` / `pivot_table` is what these tools exist for. Every Django + GraphQL team that needs a "revenue by region by month" report either: (a) builds a separate REST endpoint that hits pandas, (b) maintains a parallel BI backend with its own schema, (c) tells consumers to use GraphQL nested queries and pivot client-side (expensive over the wire, slow on the client), or (d) exports a CSV nightly from a cron job.

**What we'd do**: ship a tabular-data subsystem that does two things in one slice — because **they are the same problem** (tabular data shape; streaming friendly; one source of truth for dimensions + measures):

1. **`DjangoMatrixField`** — a new query surface that returns flat tabular rows with declarative *dimensions* (group-by axes) and *measures* (aggregations), with optional pivot rotation.
2. **Tabular export formats** — content-negotiated output of any tabular response (matrix OR regular list / connection) as CSV, XLSX, Parquet, Apache Arrow IPC, or NDJSON. Streaming-aware via item 30.

#### Design decision 1: matrix query shape vs the existing tree shape

GraphQL is tree-shaped. A `DjangoConnectionField` returning orders with their customers and line items is a tree of nested JSON. That's the right shape for *"render this product detail page"* but the wrong shape for *"sum revenue by country by year and give me the top 100 rows."*

A `DjangoMatrixField` query returns:
- a flat `rows: [Row]` list where each row is a record of `{dimension_a, dimension_b, measure_x, measure_y}`
- an optional `totals` block for grand totals across all rows
- an optional `pivotKeys` block when pivot mode is in use

No nesting, no `edges { node { … } }` wrappers. The shape is directly serializable to CSV / XLSX / Parquet without a flattening pass.

#### Design decision 2: dimensions, measures, and the Meta surface

Schema authors declare the available dimensions and measures up front; consumers pick subsets per query. The cost of unused dimensions is zero — they're only evaluated when selected:

```python path=null start=null
from django_strawberry_framework import DjangoMatrix, Dimension, Measure

class OrderMatrix(DjangoMatrix):
    class Meta:
        model = Order
        dimensions = {
            "country":   Dimension("customer__country"),
            "region":    Dimension("customer__country__region"),
            "year":      Dimension("created_at__year"),
            "month":     Dimension("created_at", trunc="month"),       # date_trunc
            "quarter":   Dimension("created_at", trunc="quarter"),
            "status":    Dimension("status"),
            "category":  Dimension("items__category__name"),
        }
        measures = {
            "revenue":      Measure("total",  agg="sum"),
            "order_count":  Measure("id",     agg="count", distinct=True),
            "avg_value":    Measure("total",  agg="avg"),
            "p95_value":    Measure("total",  agg="percentile", args={"p": 0.95}),
            "unique_users": Measure("customer_id", agg="count", distinct=True),
        }
        filterset_class    = filters.OrderFilter   # reused from the DjangoType
        export_formats     = ["csv", "xlsx", "parquet", "ndjson", "arrow"]
        cost = {
            "per_dimension": 5,
            "per_measure":   3,
            "per_pivot":     20,                    # pivot is expensive
            "per_filter":    1,
        }
        auto_stream_above  = 50_000                 # rows; composes with item 30
        pivot_cardinality_cap = 200                 # max distinct values in a pivot dimension
```

The dimensions and measures are just Django ORM expressions under the hood; `Dimension` wraps a field path (with optional `trunc` / `extract`), and `Measure` wraps an aggregation. We reuse the same filterset / orderset that drives the regular `DjangoType` queries.

#### Design decision 3: pivot mode

Pivot rotates one dimension into dynamic columns — the classic spreadsheet pivot table. *"Revenue by product"* with a pivot on `month` becomes:

| product | 2025-01 | 2025-02 | 2025-03 |
|---|---|---|---|
| Widget A | 12,500 | 14,200 | 11,900 |
| Widget B | 8,300  | 9,100  | 8,800  |

The pivoted column set is dynamic (driven by the actual values present in the data); we cap it via `pivot_cardinality_cap` so a typo in a query doesn't produce a 10,000-column response.

GraphQL shape for pivot mode is a nested cell list (rather than truly dynamic top-level fields, which GraphQL doesn't natively support):

```graphql path=null start=null
query SalesByProductByMonth {
  orderMatrix(
    dimensions: [{name: "category"}]
    pivot:       {name: "month"}
    measures:    [{name: "revenue"}, {name: "order_count"}]
    filter:      {createdAfter: "2025-01-01"}
  ) {
    pivotKeys                  # ordered list of pivot column headers
    rows {
      category                 # the non-pivot dimension
      cells {                  # one cell per pivot column
        pivotValue
        revenue
        orderCount
      }
    }
    totals {                   # grand totals across all cells
      revenue
      orderCount
    }
  }
}
```

CSV / XLSX / Parquet exports get the *actual* pivot shape (pivot values become real columns) because those formats support dynamic columns natively.

#### Design decision 4: tabular export formats

Output format is negotiated three ways (in priority order):

1. **`Accept` header** — `text/csv`, `text/tab-separated-values`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX), `application/vnd.apache.parquet`, `application/vnd.apache.arrow.stream`, `application/x-ndjson`, `application/json` (default GraphQL response).
2. **URL query param** — `?format=csv` (for browser-driven downloads where the user can't easily set headers).
3. **GraphQL directive** — `query @tabular(format: "csv") { … }` (for tooling that wants the format in the operation).

The supported formats and their characteristics:

| Format | Streaming | Browser-friendly | Use case |
|---|---|---|---|
| `application/json` | no (default GraphQL) | yes | Programmatic clients; small results |
| `application/x-ndjson` | yes | yes (with `ReadableStream`) | Streaming JSON; composes with item 30 |
| `text/csv` | yes (line-by-line) | yes (browser auto-downloads) | Excel / Sheets imports |
| `text/tab-separated-values` | yes | yes | Sheets paste-friendly |
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX) | partial | yes (Excel opens it) | Native Excel; formatted exports |
| `application/vnd.apache.parquet` | row-group streaming | no (binary) | Analytics pipelines; pandas / Spark / DuckDB |
| `application/vnd.apache.arrow.stream` | record-batch streaming | no (binary) | High-throughput analytical pipelines; ADBC clients |

Soft dependencies: `openpyxl` (XLSX), `pyarrow` (Parquet + Arrow). Each is a soft dep — the package imports lazily and produces a typed error (item 19) with `code="dst.export.format_unavailable"` plus an install hint when an unconfigured format is requested.

#### Design decision 5: streaming integration with item 30

When a matrix query's projected row count exceeds `auto_stream_above`, the server **does not** materialize the full result — it returns a download token using item 30's protocol. The format chosen at initiation determines the streamer:

- **CSV / NDJSON / TSV** stream line-by-line; minimal memory.
- **Parquet** writes per-row-group; configurable row-group size (default 10,000 rows).
- **Arrow IPC** writes per-record-batch; configurable batch size.
- **XLSX** uses a streaming-XLSX writer (`openpyxl`'s `write_only` mode); the ZIP is built incrementally.

Resume semantics from item 30 apply unchanged: dropped connection mid-export → client retries with `Range: items=<row-index>-`, server resumes from that row index in the matrix's snapshot. The snapshot mode (`"ids"` / `"full"` / `"pg_cursor"`) determines whether the underlying queryset's data is point-in-time or live.

#### Design decision 6: cost analysis (composes with item 17)

Matrix queries are *trivially* expensive — three dimensions × five measures over 100 million rows is a SQL request that can saturate a database. The cost model is explicit in `Meta.cost`:

`total_cost = (n_dimensions × per_dimension) + (n_measures × per_measure) + (per_pivot if pivot else 0) + (n_filters × per_filter)`

Combined with the projected row count (estimated via `EXPLAIN` for PostgreSQL, falling back to `COUNT(*)` for other backends), the request is rejected pre-execution if it exceeds the schema-wide budget. The error is typed (`code="dst.matrix.cost_exceeded"`) and includes the offending dimensions / measures so the client can adjust.

#### Schema-author + client experience

Define once:

```python path=null start=null
class OrderMatrix(DjangoMatrix):
    class Meta:
        model = Order
        dimensions = {...}
        measures   = {...}
        export_formats = ["csv", "xlsx", "parquet", "ndjson", "arrow"]
        auto_stream_above = 50_000
```

GraphQL query (JSON response):

```graphql path=null start=null
query SalesByCountry {
  orderMatrix(
    dimensions: [{name: "country"}, {name: "year"}]
    measures:   [{name: "revenue"}, {name: "orderCount"}]
    filter:     {createdAfter: "2025-01-01"}
    orderBy:    ["-revenue"]
    limit:      100
  ) {
    rows { country year revenue orderCount }
    totals { revenue orderCount }
  }
}
```

Browser CSV download (one-click from a UI button):

```bash path=null start=null
curl -H "Accept: text/csv" \
     -d '{"query": "{ orderMatrix(dimensions: [{name:\"country\"}], measures: [{name:\"revenue\"}]) { rows { country revenue } } }"}' \
     https://api.example.com/graphql/

# country,revenue
# USA,1250000.00
# UK,340000.00
# DE,290000.00
```

Or via REST-style URL (the simplest possible Excel-friendly export endpoint):

```bash path=null start=null
curl "https://api.example.com/graphql/matrix/order?dimensions=country,year&measures=revenue&format=xlsx" \
     -o sales-by-country-year.xlsx
```

Streaming Parquet for analytics pipelines:

```python path=null start=null
import pyarrow.parquet as pq
import requests

with requests.post(
    "https://api.example.com/graphql/",
    json={"query": "{ orderMatrix(...) { rows { ... } } }"},
    headers={"Accept": "application/vnd.apache.parquet"},
    stream=True,
) as r:
    table = pq.read_table(r.raw)
    df    = table.to_pandas()
# 10M rows of pre-aggregated revenue data — pandas DataFrame in one call.
```

tRPC-style client (item 26) exposes the matrix as typed function calls:

```typescript path=null start=null
// Generated by `manage.py export_schema --emit typescript-client`
const data    = await client.matrices.order.query({
  dimensions: ["country", "year"],
  measures:   ["revenue", "orderCount"],
});

// Or directly to a downloadable Blob
const csvBlob = await client.matrices.order.export({
  dimensions: ["country", "year"],
  measures:   ["revenue"],
  format:     "csv",
});
```

#### CSV / XLSX export of a regular list field (no matrix needed)

The export-format layer is not matrix-only. Any `DjangoListField` or `DjangoConnectionField` can be exported in tabular form: the selected scalar fields become columns; relation traversals become flattened columns (`customer.country` → `customer_country`). This means *"give me a CSV of all my orders with their customer's email and total"* is a regular GraphQL query with `Accept: text/csv` — no matrix declaration needed.

```bash path=null start=null
curl -H "Accept: text/csv" \
     -d '{"query": "{ allOrders { id total status customer { country email } } }"}' \
     https://api.example.com/graphql/

# id,total,status,customer_country,customer_email
# 1001,99.99,PAID,US,user@example.com
# 1002,149.50,SHIPPED,UK,buyer@example.co.uk
```

For nested lists (e.g. `allOrders { lineItems { … } }`), the row is "one line per line-item" with the parent order's columns repeated — same row-flattening semantics pandas uses for `explode`. Configurable per-field via `Meta.tabular = {"explode": ["line_items"]}`.

#### Composition with other `BACKLOG.md` items

- **Item 17 (cost & complexity limits)** — `Meta.cost` budget enforced pre-execution; rejections produce `code="dst.matrix.cost_exceeded"`.
- **Item 18 (HTTP-spec transport)** — `Accept` negotiation is exactly the HTTP-semantic path item 18 already documents; `Cache-Control` on idempotent matrix queries lets CDNs cache aggregated reports.
- **Item 19 (typed error envelope)** — `dst.matrix.*` and `dst.export.*` codes (unknown dimension, pivot cap exceeded, format unavailable, XLSX row limit exceeded).
- **Item 21 / 26 / 27 (codegen)** — `client.matrices.order.query(...)` and `client.matrices.order.export({format})` are first-class generated functions; TanStack hooks (item 27) get `useOrderMatrix` + `useOrderMatrixExport`.
- **Item 29 (schema usage analytics)** — track which dimensions / measures / formats consumers query, drives matrix-surface deprecation decisions.
- **Item 30 (resumable streaming downloads)** — the wire is the same: matrix exports above `auto_stream_above` use item 30's snapshot + token + resume protocol; the format chooser picks the streaming serializer.
- **Item 31 (gRPC)** — matrix RPCs become server-streaming methods with `Order` (proto message) frames; Arrow IPC over gRPC is the canonical analytical-pipeline transport.
- **`TODO-BETA-038` (Aggregation subsystem)** — the matrix layer is the natural evolution of the planned `AggregateSet` work. Aggregates ship a single-row aggregation surface first; the matrix layer (this item) generalizes it to multi-row group-by + pivot. Same `Meta.measures` dict can drive both.

#### Failure modes and edge cases

- **Unknown dimension or measure** → `validation.matrix.unknown_dimension` / `validation.matrix.unknown_measure` with the available names listed in `error.params`.
- **Pivot cardinality exceeds `pivot_cardinality_cap`** → typed error with the projected column count and the cap, suggesting the user filter the pivot dimension or raise the cap.
- **Cost budget exceeded** → typed error with the contributing components (n_dimensions × per_dimension, etc.).
- **Format unavailable (soft dep missing)** → typed error with `pip install` hint (`pip install pyarrow` for Parquet/Arrow, `pip install openpyxl` for XLSX).
- **XLSX row count exceeds Excel's 1,048,576-row limit** → automatic split into multiple sheets *or* fallback to CSV with a warning in the response extensions; configurable via `Meta.xlsx_row_limit_behavior`.
- **Pivot dimension contains nulls** → grouped as `"(no value)"` by default; configurable via `Meta.pivot_null_strategy = "skip" | "group_as" | "error"`.
- **Streaming aborted mid-export** (network drop, client close) → snapshot + resume from item 30; on resume, format writer reopens at the appropriate row offset (CSV / NDJSON / TSV: trivial; Parquet / Arrow / XLSX: write a fresh stream restarting at the offset, since their container formats don't append cleanly).
- **Pivot dimension cardinality drift between rows** (some products have January data, others don't) → cells are emitted for the union of pivot values, with `null` measures where the data is absent.
- **Aggregation on a many-side relation without de-duplication** → SQL `JOIN` fan-out can multiply counts; per-measure `distinct=True` is the documented mitigation, flagged automatically when the planner detects a fan-out path.

**Why it matters**: tabular data is the **single biggest use case** the GraphQL ecosystem doesn't address. *"BI / reporting / exports"* are the #1 reason teams add a parallel REST endpoint, a hand-rolled CSV view, or an external BI backend to a GraphQL service. The pain points are uniform across the industry:

- *"Give the analytics team a CSV of orders by region by month."*
- *"Let the finance team download last quarter's revenue as XLSX."*
- *"Feed our data lake with hourly Parquet snapshots of new sign-ups."*
- *"Let our dashboard pivot product-by-month without 10 round-trips."*

Today every team writes their own version of every one of these. Owning the matrix surface (with CSV / XLSX / Parquet / Arrow output) makes them disappear — *one Django Meta declaration drives the GraphQL surface, the CSV export, the XLSX export, the streaming Parquet ingestion endpoint, and the analytical dashboard's query API.*

Combined with item 30 (streaming) and item 31 (gRPC), the full transport matrix becomes:

| Use case | Wire |
|---|---|
| Product UI (React/Vue/Svelte) | GraphQL JSON or tRPC-style typed client |
| Mobile / polyglot service-to-service | gRPC + protobuf |
| Bulk export (browser-friendly) | NDJSON / CSV with resume via HTTP `Range` |
| Bulk export (analytical pipelines) | Parquet / Arrow over the same resume protocol |
| Internal Django service-to-service | REST or gRPC |
| Analyst CSV / Excel download | `Accept: text/csv` or `?format=xlsx` on any list / matrix query |

**One Django `Meta` declaration produces all six.** No competitor in any ecosystem covers this surface from one source of truth.

### 1. Unified declarative permission system in `Meta`

**Realistic**: 7/10 — Registry, optimizer hooks, and `_attach_relation_resolvers`' skip-set semantics give us the integration points; cascade enforcement across `Prefetch` downgrade is real architecture but feasible without rebuilding Django or Strawberry.

**Impact**: 9/10 — Every Django + GraphQL team writes `get_queryset` boilerplate for the common cases today. Closing it under one declarative Meta key removes a class of repeated code.

**Difficulty**: 7/10 — Single `Meta.permissions` dict drives row + field + cascade across joins; multiple integration points across resolver, walker, and prefetch downgrade.

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

### 39. Relay magic: GlobalID migrations, polymorphic connections, stable cursors, refetchable containers

**Realistic**: 7/10 — Each sub-feature is bounded. GlobalID migration mirrors a Django-`makemigrations`-style history (same pattern as gRPC item 31's protobuf migrations). Polymorphic connections build on the shipped `is_type_of` injection from the Node foundation. Stable cursors are a known pagination technique. The largest unknown is downstream Relay-client compatibility — we ship the server side and document client integration paths.

**Impact**: 9/10 — Relay is GraphQL's hardest spec to implement correctly. The "magic" features below (cursor stability, GlobalID lifecycle, polymorphic edges, refetchable containers) are where most teams give up and roll their own. Owning these closes one of the deepest GraphQL adoption gaps and turns *"we tried Relay but the cursors kept breaking"* into *"the package handles it."*

**Difficulty**: 8/10 — Six sub-features under one umbrella. The GlobalID migration system carries the bulk of the work (a Django-migrations-style history + multi-decoder); polymorphic connections need optimizer cooperation across `is_type_of` dispatch; cursor stability needs an opt-in ordering contract and `pageInfo` recomputation.

**What `graphene-django` / `graphene-relay-django` does**: ships `Node` + `Connection` primitives but punts on type-rename migrations, first-class polymorphic edges, declarative cursor-field stability, and refetchable container support. Teams routinely hit the wall on one of these and fork the package.

**What `strawberry-graphql-django` does**: `strawberry-django.relay` provides cursor-connection support but no migration tooling for type renames, no first-class polymorphic connections, no declarative cursor field, no refetchable container metadata. Each gap is per-team plumbing.

**What we'd do**: ship six Relay-specific extensions, all opt-in, all composable with the shipped `Meta.interfaces = (relay.Node,)` foundation and the `1.0.0` Connection surface (`BLOCKED-ALPHA-023`).

#### Sub-feature 1: GlobalID model-rename / app-move helper

**Note**: this sub-feature shrinks dramatically once item 40 (Django-model-based GlobalID encoding) is adopted. With `app_label.model_name:id` as the durable identifier, GraphQL type renames no longer break IDs at all — the type name was never in the encoded payload to begin with. The full Django-migrations-style history described in earlier drafts of this item is unnecessary in the common case.

The remaining failure mode is far rarer: **moving a Django model between apps** (`auth.user` → `accounts.user`) or **renaming the model class itself** (`products.item` → `products.product`). Both events already require a Django data migration; the GlobalID breakage is symmetric and intentional. But for the rare case where a consumer needs old-format IDs to keep working after a model move, ship a thin alias helper:

```python path=null start=null
# Django setting or schema-construction option
DJANGO_STRAWBERRY_FRAMEWORK = {
    "RELAY_GLOBALID_ALIASES": [
        # old -> new; decoder accepts either, encoder emits new
        ("auth.user",     "accounts.user"),
        ("products.item", "products.product"),
    ],
}
```

The decoder consults the alias list at decode time and routes `b64("auth.user:42")` to the new `accounts.user` model. New IDs are minted against the new identifier; the alias map is append-only over the project's lifetime; consumers can drop entries via a future `manage.py expire_globalid_aliases --before=YYYY-MM-DD` command once they're confident no client still holds the old format.

This is ~30 lines of code (a dict lookup at decode time) rather than the multi-hundred-line migration-system originally scoped here. The bulk of that work moved to item 40, which restructures the encoding itself so the migrations aren't needed.

#### Sub-feature 2: Polymorphic connections (`Connection[Interface]`)

`Connection[Interface]` where edges can be any concrete type implementing the interface. The canonical case is a social feed: `Post`, `Photo`, `Repost`, `Poll` all implement `FeedItem`, and the feed is a single connection.

Teams currently work around this by either (a) expressing the feed as three separate `Connection[Post]` / `Connection[Photo]` / `Connection[Repost]` endpoints and joining on the client, or (b) hand-rolling a single-table polymorphic backing model.

We'd ship native interface-connection support. The `DjangoConnectionField` accepts an interface type; at resolution time, it walks the polymorphic queryset (cooperating with `django-polymorphic` if available, or `ContentType` lookups if not), dispatches each row through `is_type_of` to its concrete `DjangoType`, and emits the right `__typename` per edge. The optimizer's selection-tree walker recognizes the interface-edge shape and prefetches the right relations for each concrete type.

#### Sub-feature 3: `Meta.cursor_field` for stable cursors

Relay cursors default to opaque base64(offset) — fast, but unstable: insert a row at the start of the queryset and every cursor in flight points one row off. Delete the row a cursor points to and the next page is silently wrong.

We'd ship declarative stable-cursor support:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        cursor_field = ("created_at", "id")    # stable cursor; survives inserts/deletes
```

The cursor encodes the `(created_at, id)` tuple of the row. Decoding produces a `WHERE (created_at, id) > (value, value)` filter against the queryset — insert-safe and delete-safe. The connection-field machinery enforces a matching `order_by` on the queryset so cursor order and result order can't diverge.

When `cursor_field` is unset, the default opaque-offset behavior applies. This is opt-in stability for the teams that need it.

#### Sub-feature 4: Auto-upgrade reverse FK / M2M to Connection

Reverse-FK relations (`category.items`) and M2M relations are exposed as `list[T]` by the shipped foundation. That's fine when the count is small and breaks when it grows. Today teams either (a) keep them as lists and pray no one queries a hot row, or (b) hand-promote them to connections everywhere preemptively.

We'd ship a declarative threshold:

```python path=null start=null
class CategoryType(DjangoType):
    class Meta:
        model = Category
        connection_threshold = 100   # if .items count > 100, expose as Connection; else list
```

The connection-threshold check is per-request: if the type's selected relation row count exceeds the threshold, the optimizer plans a Connection-shaped fetch; otherwise it stays as a plain list. The schema declares **both** shapes (`items: list[Item]` and `itemsConnection: ItemConnection`) and the client picks which to query — but the package documents the *recommendation* of always using the connection form once the threshold is set on the type.

#### Sub-feature 5: Refetchable container support

Relay's `useRefetchableFragment` requires the schema to mark fragments as refetchable — specifically, the fragment must be on a `Node`-implementing type with a stable ID, AND the schema must advertise a `node(id:)` resolver path that returns that exact fragment shape. Most teams hit the wall in the client and rewrite the schema once they realize.

We'd ship the schema-side support declaratively:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        refetchable = True   # advertises this type as a Relay refetchable container target
```

The package emits the right schema metadata (the `@refetchable` directive when present in the consumer's Strawberry version; a documented introspection hint otherwise), and the `node(id:)` root resolver (shipped in `BLOCKED-ALPHA-023`) is guaranteed to return the same shape the consumer queried — no field-set drift between the connection edge and the refetched object.

#### Sub-feature 6: Permission-aware cursor decoding

A cursor minted under one user's `get_queryset` (admin sees all rows) shouldn't reveal rows hidden under another user's (regular user sees only public rows). The naive cursor decode is `WHERE (col, id) > (cursor_value, cursor_id)` against the full table — which leaks the existence of restricted rows by their cursor positions.

We'd ship cursor decode that re-runs `get_queryset` at decode time. The cursor encodes the row's position; the decode filter is applied to `cls.get_queryset(qs, info)`, not to the raw table. A cursor minted under admin privileges and replayed under a regular user produces a queryset that respects the regular user's visibility — no row leak, no inconsistent pagination.

This is a small change but a real privacy bug we'd close.

#### Why it matters

Relay is the canonical GraphQL pagination + identity spec. It's also where teams burn out. The six features above target the specific pain points that drive teams to either *(a)* abandon Relay for hand-rolled offset pagination, or *(b)* stay on Relay but accept a permanent layer of bug reports about *"the cursors are wrong again."* Nobody in the Django + GraphQL ecosystem ships a coherent solution to any one of these, let alone all six.

The headline pitch: *"Relay just works — type renames don't break IDs, cursors don't drift on inserts, polymorphic feeds use one connection, permissions are honored across pagination."* Combined with the shipped `Meta.interfaces = (relay.Node,)` foundation and the `1.0.0` Connection surface, this completes the *"Relay is the easiest part of our package, not the hardest"* story.

**Framework integration**: composes with `BLOCKED-ALPHA-023` (Full Relay story, the `1.0.0` connective tissue) — this item is the *post-stable* expansion of that card. Composes with item 15 (content-versioned Node types) for per-Node freshness gossip. Composes with item 33 (DoS policy stack) since stable cursors and polymorphic connections need their own cost weights. Composes with item 4 (polymorphic / `GenericForeignKey` support) — sub-feature 2 (polymorphic connections) is the *Relay-shaped* version of the same underlying machinery item 4 introduces for non-Relay polymorphic types.

### 15. Content-versioned Node types with response-extensions gossip

**Realistic**: 7/10 — Hashing is trivial; permission integration + extensions-block emission + optional Apollo Link is more involved but well-scoped.

**Impact**: 8/10 — Unique cache-freshness story for normalized clients; pairs with Relay Node identity from the foundation work.

**Difficulty**: 7/10 — Multi-layer feature (per-type Meta + server extension + optional client SDK); each layer composable but the total surface is substantial.

**What `graphene-django` does**: nothing first-class. Consumers add `version` or `etag` fields manually if they want them; cache invalidation is per-team plumbing.

**What `strawberry-graphql-django` does**: same — nothing declarative. `version` is just a regular field consumers wire up themselves.

**What we'd do**: a declarative `Meta.version` key plus an opt-in Strawberry extension that emits per-Node freshness gossip in the spec-blessed `extensions` envelope. The GlobalID stays stable for identity (Relay-compliant). The `version` field answers "is my cached copy stale?" without breaking any client.

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        version = ("updated_at",)        # tuple of fields to hash, or
        # version = "auto"               # hash all selected scalar fields, or
        # version = lambda row: ...      # fully custom callable
```

Behavior:
- Auto-adds `version: String!` to the Strawberry type.
- Default impl: short SHA-256 of the joined values of declared fields (`updated_at` ISO is fine, content hash is fine, monotonic version column is fine).
- Optional `DjangoVersionExtension` populates `extensions["dst.versions"] = {globalid: version}` for every Node in the response, so freshness info is available even for objects whose `version` field wasn't selected.
- Optional 30-line Apollo Link reads `extensions["dst.versions"]` and surgically evicts stale cache entries via `cache.evict()`.

**Spec compliance**: the `version` field is a regular `String!`. The `extensions` block is the GraphQL spec's documented vendor extension envelope. Stock Apollo Client without any custom config sees a normal field and a normal response.

**Why it matters**: Apollo and other normalized caches solve "is this the same object?" with `id`. They do not solve "is my cached version stale?" — that's still per-team plumbing. Declarative content versioning is a real production concern that nobody in the Django + GraphQL stack ships first-class. Combined with the shipped Relay Node foundation, this gives consumers automatic identity *and* automatic freshness from one Meta declaration.

**Server-side opt-out (the feature is off by default at every layer; it must be turned on intentionally)**:
- **Per-type**: omit `Meta.version` entirely or set `Meta.version = None`. No `version` field is added; that type is skipped in the extensions gossip even when the extension is installed.
- **Per-field hash exclusion**: `Meta.version = "auto"` plus `Meta.version_exclude = ("last_login", "view_count")` to skip noisy fields that would make every row look stale every minute.
- **Per-schema (extension)**: omit `DjangoVersionExtension` from `extensions=[...]`. The `version` field on individual types still works for clients that explicitly query it; no `extensions["dst.versions"]` block is emitted.
- **Per-request directive**: a `@dstNoVersions` operation directive turns the gossip off for one query. Saves payload bytes for one-shot queries that don't care about freshness.
- **Per-request header**: `X-DST-Versions: off` for clients that can't easily add operation directives.
- **Per-resolver**: a `@no_version` decorator on a custom resolver suppresses gossip for that response branch (useful for ephemeral or generated objects that shouldn't pollute the cache).
- **Per-permission scope**: gossip respects the same field/row visibility filters from item 1; a viewer who can't see a row never sees its version.

**Client-side opt-out (default zero-cost; consumers add features as they need them)**:
- **Default behavior**: don't query `version`. Standard GraphQL field selection — cost zero, no bytes on the wire, no client work.
- **Don't install the Apollo Link**: the `extensions["dst.versions"]` block is in the response but Apollo ignores it. The only cost is the response payload size, which can be turned off server-side per the above.
- **Selective subscription**: the Apollo Link can be configured with `types: ["ItemType", "OrderType"]` to act on specific types only.
- **Operation-scoped opt-in**: the Link reads a context flag (`context: { dstVersions: false }`) so list/feed queries can skip eviction even when the Link is installed globally.
- **Eviction policy**: the Link supports `policy: "evict" | "refetch" | "warn"` so consumers choose between dropping the cache entry, re-issuing the query, or just logging the staleness.

Defaults at every layer: feature is **opt-in**. A consumer who never declares `Meta.version` and never installs the extension sees zero behavior change. A consumer who declares `Meta.version` but never installs the extension just gets a queryable `version` field. A consumer who installs the extension but never adds the Apollo Link gets the gossip on the wire but no client-side action. Each layer composes independently so consumers can dial in exactly the cost/benefit they want.

### 9. Async-native ORM as the default path

**Realistic**: 7/10 — Django 4.2+ has native async ORM for most operations; per-resolver-site work; sync fallback for the few gaps.

**Impact**: 7/10 — Async-first positioning + real perf for ASGI deployments; not game-changing for sync-WSGI shops.

**Difficulty**: 6/10 — Each resolver template gets async/sync variants; test matrix grows; release-by-release rollout.

**Note**: the Relay-specific async slice (sync/async paths for `_resolve_node_default` and `_resolve_nodes_default`) is already covered by the shipped Relay Node foundation. This item is the broader push across every resolver in the package.

**What `graphene-django` does**: bolted-on async via `sync_to_async` everywhere; sync is the default.

**What `strawberry-graphql-django` does**: partial async support; sync is still the most common path in real codebases.

**What we'd do**: every generated resolver is async-by-default; cooperate with Django's native async ORM (`aiter`, `aget`, `acount`, `aupdate`, `adelete`, `aexists`) since 4.2; sync fallback only for ORM operations that don't yet have native async equivalents.

**Why it matters**: the Django + GraphQL stack is becoming async-first (ASGI, Channels, FastAPI-influenced patterns). Owning the canonical "Django GraphQL with native async ORM" surface is a real position to take.

### 22. Anti-N+1 CI mode and schema fuzz tester

**Realistic**: 7/10 — Schema enumeration is doable; query-generation at depth has combinatorial blowup concerns we'll need to bound.

**Impact**: 7/10 — Turns the optimizer's *'no avoidable N+1s'* promise into an enforceable CI contract.

**Difficulty**: 6/10 — Test data seeding + query generator + reporter + management command; medium slice.

**What `graphene-django` does**: nothing.

**What `strawberry-graphql-django` does**: nothing.

**What we ship today**: strictness mode (`OptimizerHint.strictness="raise"`) raises on accidental lazy loads at request time. Useful in dev/test; ad-hoc to integrate into CI.

**What we'd do**: a management command that:
1. enumerates every reachable query path in the schema (using `registry.iter_definitions()`)
2. constructs synthetic queries at depth N (default 3) covering all relation combinations
3. executes each against a seeded test database with the optimizer in `raise` strictness mode
4. fails CI on any unplanned lazy load, reporting the resolver path and the `OptimizerHint` that would fix it

```bash path=null start=null
uv run python manage.py audit_n1 --depth 3 --fail-on-warn
uv run python manage.py audit_n1 --depth 5 --include-mutations --seed fakeshop
```

Pairs with item 5 (schema diff CLI) to also detect *"PR added a new relation field but no optimizer hint"* regressions before merge.

**Why it matters**: today every Django+GraphQL team writes one-off integration tests answering *"did we introduce an N+1 on this PR?"* — and they're never exhaustive. Owning the CI gate turns the optimizer's promise (*"no avoidable N+1s"*) into an enforceable contract, not aspirational text. This is the kind of feature that only makes sense for a package that already owns the optimizer; the upstreams can't ship it without rebuilding their planner first.

### 28. Mutation batching with transactional semantics

**Realistic**: 7/10 — Transaction wrapping is easy; cross-mutation path-expression resolution is real but doable without engine changes.

**Impact**: 7/10 — Closes the *'mutations don't compose'* critique that PrimeTime and Theo both name.

**Difficulty**: 6/10 — Path-expression resolver + batch executor + error mapping; modest slice.

**What `graphene-django` does**: GraphQL accepts multiple operations in one document, but Django ORM treats them as independent operations — partial failures leave half-done state, no rollback.

**What `strawberry-graphql-django` does**: same — multi-operation requests are not transactional by default.

**What `REST` and `tRPC` users complain about**: *"Mutations don't compose."* PrimeTime and Theo both name this — you want to create an order with three line items as a single atomic operation, and GraphQL gives you three separate mutations with no guarantee they all succeed or all fail together.

**What we'd do**: a dedicated `/graphql/batch` endpoint accepting an ordered list of mutation operations and running them in a single `transaction.atomic()` block. Any operation's failure rolls back the entire batch. Operations can reference earlier results via path expressions:

```typescript path=null start=null
const result = await client.batch([
    { op: "items.create",     input: { name: "Order #1" },                       alias: "order" },
    { op: "lineItems.create", input: { order: "$order.id", product: 42 } },
    { op: "lineItems.create", input: { order: "$order.id", product: 43 } },
]);
// Either all three succeeded or none did. result.order, result.lineItems[0], result.lineItems[1] all populated.
```

`$order.id` references the first mutation's result; the batch executor resolves the dependency graph before execution. Batch responses carry the shared `errors: list[FieldError]` envelope (item 19) and `extensions["dst.invalidations"]` block (item 20) so client invalidation still works.

**Why it matters**: *"Mutations don't compose / don't transact"* is one of the most-cited GraphQL critiques. REST's *"one transaction per route"* handles this naturally; tRPC users compose calls inside a single procedure with database transactions; GraphQL's *"each mutation is independent"* model has no answer. Owning a transactional batch endpoint gives consumers the most-requested missing GraphQL feature in a Django-native way — `transaction.atomic()` is already the Django convention, we just wire it through. Pairs with item 23 (single-mutation transactions and idempotency).

### 30. Resumable streaming downloads for large querysets

**Realistic**: 6/10 — Snapshot semantics + per-chunk optimizer mode + HTTP `Range` resume + multi-format encoding is real architecture; doable but the biggest design surface on the read/write list.

**Impact**: 10/10 — Closes the *'GraphQL doesn't do bulk'* objection; would be a README-screenshot feature.

**Difficulty**: 9/10 — Largest slice in this cluster — multiple coordinated subsystems (snapshot, streaming, resume, optimizer mode, format chooser).

**What `graphene-django` does**: nothing — large list queries are either truncated by pagination or block until the full materialized response can be serialized. There is no spec-blessed *"stream me 10 million rows"* path; teams bolt on REST endpoints, signed S3 URLs, or hand-rolled chunked views.

**What `strawberry-graphql-django` does**: same — Strawberry supports the `@defer` / `@stream` GraphQL spec directives at the protocol level, but the Django adapter doesn't offer a snapshot/resume contract on top.

**What `DRF` does**: streaming via Django's `StreamingHttpResponse` is possible but pagination-only; resumability is consumer-implemented.

**What Apollo's `@defer` / `@stream` directives solve**: server pushes list items as they resolve, so the client sees data faster. They **do not** solve resume-after-drop: an interrupted stream restarts from scratch on retry, re-executing the entire query and re-walking the entire queryset.

**What Mega / Google Drive / S3 multipart / BigQuery exports do**: durable download tokens, snapshot semantics, HTTP `Range` resumes, automatic checksum/retry on the client side. The user's expectation when downloading 50 GB from Google Drive is *"if my Wi-Fi drops, the download picks up where it left off."* That expectation does not exist anywhere in the GraphQL ecosystem today.

**What we'd do**: ship a streaming-download protocol layered on top of GraphQL connection fields — durable point-in-time snapshots, NDJSON chunked transport, HTTP-`Range`-resumable, optimizer-aware per-chunk prefetch. The schema author flips a Meta switch; the package handles the snapshot, token issuance, resume bookkeeping, and per-chunk ORM behavior.

#### Design decision 1: snapshot strategy

Three modes, picked per type via `Meta.streamable["snapshot_mode"]`:

- **`"ids"` (default)** — at initiation, materialize the matching primary keys to a token-scoped store (`django.core.cache` with a redis or DB backing) plus a `snapshot_at` ISO timestamp. Subsequent chunk requests fetch rows from the live table by ID. Cheap (just the ID list, typically ~8 bytes per row). Deleted rows during the download produce a per-chunk `missing_ids: [...]` metadata block — the client decides whether to error or skip. Column updates during the download show through; this is documented as the contract.
- **`"full"`** — on initiation, write the full result set to blob storage (S3 / GCS / Django default-storage backend) as gzipped NDJSON. Subsequent chunk requests stream from the blob. Strictly consistent, regardless of source-table mutations. Expensive for huge datasets; appropriate for *"give me last night's full export of 10M orders for the warehouse load."*
- **`"pg_cursor"`** — PostgreSQL `DECLARE ... WITH HOLD CURSOR`. Connection-bound, point-in-time strict, but holds a database connection for the snapshot lifetime. Suited for short-lived high-consistency exports where the cost of a held connection is acceptable.

The default `"ids"` matches the *"my Wi-Fi dropped, give me what I haven't seen"* use case at the lowest cost. The other two modes opt in to stricter consistency.

#### Design decision 2: streaming wire format

**NDJSON (newline-delimited JSON) over chunked HTTP transfer.** One row per line, gzip-encoded. Browser-friendly via `ReadableStream` + `TextDecoderStream`, works out of the box with `curl --no-buffer | jq`, easy for a Python or Go client to consume, no GraphQL-multipart-response client library required. Each line is a complete GraphQL row object matching the selection set from the initiating query.

Why not GraphQL multipart response (the `@defer` / `@stream` spec format)? Two reasons: client tooling is sparser (most HTTP clients don't speak it), and resumability isn't part of the spec — we'd be inventing a custom resume layer anyway, so the simpler base protocol wins.

Why not Server-Sent Events? SSE is event-shaped and assumes server-pushed events with reconnection IDs; bulk-download is request-driven and the resume semantics differ. NDJSON+`Range` reuses standard HTTP throughout.

#### Design decision 3: resume protocol

The initial GraphQL response carries a download token plus a resume URL in `extensions["dst.download"]`. The token is opaque to the client and encodes server-side: requesting user, queryset hash, snapshot mode, snapshot ID (pointer to the cached ID list / blob path / PG cursor name), `snapshot_at`, chunk size, total count, and expiry.

Two ways to resume:

- **HTTP `Range` header**: `GET /graphql/download/<token>` with `Range: items=12000-`. The server resumes from the 12,000th row of the snapshot.
- **Path-based**: `GET /graphql/download/<token>/from/12000`. Equivalent semantics, simpler for browser-driven downloads where `Range` is awkward.

Per-chunk responses include a small metadata frame at the start identifying which row index range follows. Final chunk includes `final: true` plus a checksum (SHA-256 of the concatenated NDJSON body) so the client can verify integrity.

Token TTL is sliding-window (default 2 hours from last activity, with a hard 24-hour cap). A resume request against an expired token returns `410 Gone` with a typed error (item 19) carrying `code="dst.download.expired"` so the client can decide to re-initiate.

#### Design decision 4: optimizer integration

Streaming mode is a new optimizer plan. The shipped plan walker materializes everything via `Prefetch` and `select_related` — fine for paginated queries, memory-blowing for streaming a million rows. The streaming plan instead does **per-chunk prefetch**:

1. Pull the next `chunk_size` primary keys from the snapshot.
2. Build a one-shot queryset filtered to those IDs with the same `select_related` / `prefetch_related` shape the non-streaming plan would have used (derived from the same selection-tree walk that `optimizer/walker.py` already does).
3. Iterate, serialize each row to one NDJSON line, flush.
4. Discard the chunk's prefetch cache and loop.

The schema author flips this on with `Meta.streamable = True` (or the rich dict form below); the optimizer auto-detects streaming requests and switches plans. The existing `OptimizerHint` keys (`prefetch_related`, `select_related`, `SKIP`) all apply unchanged inside each chunk.

#### Schema-author experience

```python path=null start=null
from datetime import timedelta

class OrderType(DjangoType):
    class Meta:
        model = Order
        fields = "__all__"
        filterset_class = filters.OrderFilter
        orderset_class  = orders.OrderOrder
        streamable = {
            "chunk_size": 1000,
            "snapshot_mode": "ids",          # "ids" | "full" | "pg_cursor"
            "ttl": timedelta(hours=2),
            "max_snapshot_size": 50_000_000, # refuses initiation above this; error code="dst.download.too_large"
            "auto_stream_above": 10_000,     # automatic streaming when result count exceeds this
        }
```

Auto-stream behavior: when a connection-field query result count exceeds `auto_stream_above`, the response automatically returns a download token instead of inlining the full edges. Consumers who want a single forced-streaming entry point can also use a `@stream` directive on the field, or call `client.streams.orders.list(...)` from the codegen client (item 26).

#### Initial response shape

```json path=null start=null
{
  "data": {
    "allOrders": {
      "totalCount": 1500000,
      "edges": null
    }
  },
  "extensions": {
    "dst.download": {
      "token": "dl_5f3a8c2b9d4e1f6a",
      "chunks": 1500,
      "chunk_size": 1000,
      "total_rows": 1500000,
      "snapshot_at": "2026-05-15T10:00:00Z",
      "expires_at": "2026-05-15T12:00:00Z",
      "next_url": "/graphql/download/dl_5f3a8c2b9d4e1f6a",
      "resume_with": "Range: items=<row-index>-",
      "encoding": "application/x-ndjson",
      "checksum_algorithm": "sha256"
    }
  }
}
```

#### Client experience

The tRPC-style codegen (item 26) wraps the entire protocol in a typed async iterator. The client never thinks about tokens, `Range` headers, or chunk metadata:

```typescript path=null start=null
const stream = await client.streams.orders.list({
  filter: { createdAfter: "2026-01-01" },
  orderBy: "createdAt",
});

for await (const order of stream) {
  await processOrder(order);
}
// Auto-resumes on connection drop. Auto-verifies the final checksum.
// If the token expires mid-stream, the iterator re-initiates from the last received row
// (accepting the snapshot-drift contract) or throws if the caller passed { strict: true }.
```

For non-TS clients (Python `httpx`, Go, `curl` + `jq` shell pipelines), the protocol is plain HTTP + NDJSON: a 20-line library can speak it without any GraphQL client library at all.

#### Composition with other `BACKLOG.md` items

- **Item 17 (query cost & complexity limits)** — a result-count over `max_snapshot_size` is its own typed rejection; cost analysis runs on the *streaming plan*, not the materialized one, so query cost stays bounded.
- **Item 18 (HTTP-spec transport)** — `Range` header support and `Cache-Control: private, no-store` on download streams come for free from the same view rewrite.
- **Item 20 (mutation invalidation gossip)** — write mutations include the active download tokens whose snapshots are now stale in `extensions["dst.download_invalidations"]`, so client wrappers can decide whether to abort the resume and re-initiate.
- **Item 21 (TypeScript codegen)** + **item 26 (tRPC client)** — generate the streaming-iterator wrapper alongside the regular query/mutation functions.
- **Item 24 (per-resolver rate limits)** — `rate_limit` extends to streamable types: *"max 3 concurrent downloads per user, max 100 GB/day per tenant."*
- **Item 29 (schema usage analytics)** — every download token is logged with row count, total bytes, duration; *"who is exporting our entire orders table every hour?"* becomes a queryable fact.

#### Failure modes and edge cases

- **Token expired mid-resume** → `410 Gone`, `code="dst.download.expired"`. Client decides between re-initiate (cheap re-snapshot, drift accepted) and abort.
- **Snapshot rows deleted** (`"ids"` mode only) → per-chunk `metadata.missing_ids: [...]`. Default: skip + log; opt-in: error.
- **Snapshot too large** → reject at initiation with `code="dst.download.too_large"` and the configured `max_snapshot_size`.
- **Authorization changed mid-download** → tokens are scoped to the issuing user; default behavior caches the auth-at-initiation; opt-in `Meta.streamable["recheck_auth_per_chunk"] = True` re-runs `get_queryset` for each chunk.
- **Client cancellation** → Django request-aborted signal stops the per-chunk loop; token TTL still ticks, so a retry within TTL resumes; expired token requires re-initiation.
- **Resume from beyond final row** → `416 Range Not Satisfiable`.
- **Concurrent chunk requests for the same token** → cheap (`"ids"` and `"full"` modes); for `"pg_cursor"` mode, we serialize per-token requests since cursors are connection-bound.

**Why it matters**: this is the *"why are we still using REST for bulk exports?"* problem in the Django + GraphQL stack. Every team that hits the wall on a large export today writes a separate REST/CSV endpoint, signs an S3 URL, builds a pre-generated nightly dump, or accepts a 15-minute timeout. None of those are GraphQL solutions — they're admissions that GraphQL doesn't do bulk. Shipping a first-class streaming-download protocol with the *"my Wi-Fi dropped and the download just kept going"* DX from Google Drive / Mega closes one of the biggest *"GraphQL is for product APIs, not data plane"* objections. Combined with the REST escape hatch (item 16) and the tRPC client (item 26), one `DjangoType` declaration covers product reads, write mutations, bulk exports, and REST consumers — the entire data-access surface of a Django app.

No competitor ships any of this. Apollo's `@stream` solves the first chunk arriving sooner; nobody solves resumability.

### 4. First-class polymorphic and `GenericForeignKey` support

**Realistic**: 6/10 — `django-polymorphic` integration is workable; GFK with optimizer-aware prefetch needs more design but doesn't require rebuilding Django.

**Impact**: 8/10 — Audit logs, comments, attachments, reactions — every real Django app has GFKs or polymorphic models, and the upstreams punt on both.

**Difficulty**: 7/10 — Strawberry union generation + ContentType lookups + optimizer cooperation across `polymorphic_ctype`; substantial design surface.

**What `graphene-django` does**: punts on GFK; polymorphic models require manual union types and per-resolver dispatch.

**What `strawberry-graphql-django` does**: same — GFK is unsupported; polymorphic is via Strawberry unions plus consumer dispatch.

**What we'd do today**: we raise `ConfigurationError` on GFK (`types/base.py::_build_annotations #"GenericForeignKey or other"`), matching the competitors. We could ship:
- `Meta.polymorphic = True` for `django-polymorphic` integration, generating a Strawberry union of all known concrete subclasses with optimizer-aware `select_related("polymorphic_ctype")` and `iterator()` patterns.
- A GFK resolver that returns a Strawberry union of registered target types, using `ContentType` lookups with prefetched generic relations.

**Why it matters**: GFK and polymorphic models are extremely common in real Django apps (audit logs, comments, attachments, reactions, tagging). Both competitors leaving this on the floor is a real adoption blocker. The package's registry already knows about every `DjangoType`, so the union-target list is free.

### 11. Per-tenant / per-role schema variants

**Realistic**: 6/10 — Registry + finalizer architecture supports it; `finalize_django_types(scope=...)` is real work; runtime cost concerns when tenant count grows.

**Impact**: 7/10 — Multi-tenant SaaS killer feature for teams that need it; narrow audience.

**Difficulty**: 8/10 — Substantial finalizer + registry refactor; permission integration; cache invalidation per scope.

**What `graphene-django` does**: nothing — one schema per process.

**What `strawberry-graphql-django` does**: same.

**What we'd do**: parametrize the registry: `schema_for(tenant)` or `schema_for(user_role)` produces a tenant- or role-scoped subset of `DjangoType`s, with field/relation visibility filtered by the same `permissions` system from item 1. Schema-per-tenant is the natural pairing for multi-tenant SaaS.

**Why it matters**: multi-tenant SaaS is a major Django use case. "Different schemas for different roles" is currently a hand-rolled exercise. The shipped registry-and-finalizer architecture already supports this — `finalize_django_types()` could take a scope argument. Nobody else has the architectural seam to do this cleanly.

### 8. Subscriptions wired to Django signals

**Realistic**: 5/10 — Channels integration is well-trodden but Channels itself is complex; signal-handler-to-push at scale has gotchas (blocking handlers, fan-out costs, broadcast ordering).

**Impact**: 7/10 — Real-time SaaS use case; nice positioning but not blocking for most adoption.

**Difficulty**: 8/10 — Async transport choice + subscription type machinery + permission integration + signal-handler lifecycle; substantial.

**What `graphene-django` does**: Channels integration via `graphene-subscriptions` (third-party, partial); subscriptions are not first-class.

**What `strawberry-graphql-django` does**: Strawberry supports subscriptions; the Django half (signal → push) is up to the consumer.

**What we'd do**: declarative `Meta.subscriptions = ("post_save", "post_delete", "m2m_changed")` that auto-wires the type into Channels (or another async transport) and pushes filtered events to subscribers. Combine with `get_queryset` so subscription visibility respects the same row-level filters that REST/GraphQL queries apply.

**Why it matters**: real-time updates are a common Django+SaaS requirement. Both competitors punt; we can be the package that makes Django GraphQL subscriptions trivial.

### 34. Apollo Federation support

**Realistic**: 5/10 — Federation 2 protocol is well-spec'd and the entity-resolution + `@key` directive surface is bounded, but the Apollo Gateway is operationally complex and external to our scope. Schema-stitching coordination across teams is a deployment concern we can't fully own.

**Impact**: 6/10 — Niche audience (multi-team gateway setups, Apollo Studio users); not most consumers. Important when you need it; invisible when you don't.

**Difficulty**: 8/10 — Federated type generation, entity-resolution endpoint, federation directive support, sub-graph composition. The full `federation/` subpackage shape mirrors `strawberry-django`'s, but reimplemented through the DRF-style Meta surface.

**What `graphene-django` does**: nothing — Federation is a separate undertaking entirely.

**What `strawberry-graphql-django` does**: ships a `federation/` subpackage (`field.py`, `resolve.py`, `type.py`) with `@key` directive support and entity resolution. Decorator-driven, like the rest of their surface.

**What we'd do**: ship a `django_strawberry_framework/federation/` subpackage that mirrors `strawberry-django`'s federation contract but is driven by Meta declarations:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        federation = {
            "keys": ["id", "sku"],                # @key fields (entity identifiers)
            "shareable": ["name", "category"],    # @shareable fields
            "tag": "internal",                    # @tag for access control
        }
```

Generates federation-compatible schemas with entity-resolution endpoints wired through the type's `get_queryset` — federated entity lookups respect permission filters automatically.

**Why it matters**: Apollo Federation is the canonical microservice GraphQL pattern at large scale (LinkedIn, GitHub, Netflix all run it). The audience is narrow but the operational expectation is *"of course this works."* Owning the Meta-class-driven version closes a real gap for teams already on the Apollo Gateway stack and gives sub-graph authors a Django-native path that `strawberry-django` decorators don't quite match.

**Framework integration**: composes with item 31 (gRPC sibling protocol) since both rely on the same Meta-declaration-to-multiple-transports infrastructure. Composes with item 33 (DoS policy stack) since federation entity-resolution endpoints need their own rate-limit + cost policies. Composes with item 19 (typed error envelope) for federated error semantics.

### 31. gRPC sibling protocol from the same `DjangoType` declarations

**Realistic**: 4/10 — Protobuf field-number migrations + HTTP/2 deployment + gRPC-Web bridge + Envoy proxy story is substantial infrastructure cost; the *least* realistic on the list because so much lives outside Python / Django.

**Impact**: 8/10 — Powerful for polyglot microservice fleets and mobile binary clients; narrower audience than the read/write transport items.

**Difficulty**: 10/10 — Largest slice in the file — protobuf migration system, HTTP/2 lifecycle, browser proxy, multi-language codegen.

**What `graphene-django` does**: nothing — gRPC and GraphQL are completely separate. Teams running both maintain a Django GraphQL service and a parallel Go/Rust/Python gRPC service with independent schemas.

**What `strawberry-graphql-django` does**: same.

**What `DRF` does**: REST only. Two third-party packages (`django-grpc-framework`, `django-grpc`) exist, but they live in isolation from any DRF serializer / `DjangoType` / GraphQL schema — adopting them means maintaining a third schema definition.

**What Google / Uber / Netflix / Stripe internally do**: gRPC is the de facto protocol for service-to-service traffic in polyglot microservice fleets. `.proto` is the source of truth; each language generates strongly-typed clients via `protoc`; field-number-based schema evolution makes it safe to add and deprecate fields without breaking older clients.

**What we'd do**: generate a `.proto` schema and a running gRPC server alongside `/graphql/` from the same `DjangoType` declarations. Same `Meta.filterset_class` / `Meta.orderset_class` / `Meta.search_fields` drive the gRPC `ListXRequest` shape. Same mutation classes (form / serializer / raw) drive the gRPC unary RPCs. Same streamable types (item 30) drive the gRPC server-streaming RPCs. One Meta declaration produces a Django ORM model, a GraphQL type, a REST endpoint (item 16), a tRPC client (item 26), TanStack hooks (item 27), a streaming download endpoint (item 30), **and now a typed protobuf service**.

#### Design decision 1: protobuf field-number stability

The hardest part of shipping gRPC isn't running an HTTP/2 server — it's maintaining stable field numbers across schema evolution. Protobuf wire compatibility is keyed on field numbers, not names. Renaming a GraphQL field is free; removing one means **the number is reserved forever**; adding one means **a new number is allocated and never reused**.

We'd ship a Django-migrations-style protobuf history:

- `./manage.py makeprotos` generates a new migration capturing the current schema's field numbers, deletions (as `reserved` ranges), and any oneofs.
- The migration history lives in `proto_migrations/` and is checked into the repo.
- The applied state writes the canonical `.proto` files to `proto/` (also checked in — this is what consumers `protoc` against).
- `./manage.py checkprotos` runs in CI and fails on inconsistencies (a removed field whose number was not reserved, a type with no assigned numbers, a number reused, etc.).

The schema author never picks field numbers by hand; the migration system assigns them on first appearance and locks them forever.

#### Design decision 2: HTTP/2 deployment

gRPC mandates HTTP/2. Django's default sync WSGI doesn't speak HTTP/2. We'd:

- Ship a `./manage.py rungrpc` command that starts a `grpcio`-backed HTTP/2 server bound to its own port (default `50051`), separate from the Django HTTP server.
- Document the production pattern: gRPC server runs in its own process (or container) sharing the same Django settings + database; reverse proxy (nginx / Envoy / Cloudflare) routes `grpc+proto` content-type traffic to the gRPC port and `application/json` to the GraphQL/REST port.
- For dev, an opt-in ASGI lifespan mode runs the gRPC server inside the same process as `daphne` / `uvicorn`, so `./manage.py runserver --grpc` works for a one-command dev loop.
- `grpcio` is a heavy C-extension; soft dependency like `channels`. The package imports lazily and raises `ImportError` with an install hint when gRPC is actually configured.

#### Design decision 3: browser story (gRPC-Web)

Browsers cannot speak native gRPC — they can't access HTTP/2 framing from JavaScript. The standard workaround is gRPC-Web: same protobuf wire format, tunneled through ordinary `fetch()` calls. A small proxy translates between the two.

We'd ship two paths:

- **In-process proxy (dev / small deployments)**: a Django view at `/grpc-web/<service>/<method>` that translates gRPC-Web requests to native gRPC and forwards them to the in-process gRPC server. Slow but zero-infrastructure for development and small apps.
- **Envoy / Cloudflare config snippet (production)**: documented config that consumers drop into their existing proxy layer. The package generates a starter `envoy.yaml` from the registered gRPC services as part of `./manage.py makeprotos`.

Browser-facing TypeScript codegen (items 21 / 26 / 27) gains a `--emit grpc-web` mode that produces clients compatible with `@improbable-eng/grpc-web` or the official `grpc/grpc-web` library.

#### Design decision 4: RPC mode selection

Each GraphQL surface maps to a gRPC RPC shape:

| GraphQL surface | gRPC RPC mode |
|---|---|
| `Query` returning a single object | Unary (`rpc GetX(GetXRequest) returns (X)`) |
| `Query` returning a list (`DjangoListField`) | Unary or server-streaming based on `Meta.grpc["mode"]`; default unary if `auto_stream_above` not set |
| `Query` returning a connection (`DjangoConnectionField`) | Unary that returns one paginated response |
| `Mutation` (any flavor) | Unary |
| `Subscription` (item 8) | Server-streaming |
| Streamable type (item 30) | Server-streaming — snapshot/resume semantics carried in gRPC trailers and metadata |

The schema author overrides per-field via `Meta.grpc = {"list_mode": "stream"}` when the default unary list response is too large. Bidirectional and client-streaming modes are reserved for custom RPCs declared via a future `@grpc_only` decorator — they don't have a clean GraphQL analog.

#### Design decision 5: auth and request context bridging

Django auth lives in middleware that produces `request.user`; gRPC uses **interceptors** with channel-level **metadata** (similar to HTTP headers).

We'd ship a `DjangoAuthInterceptor` that:

- Reads `authorization` metadata (`Bearer <token>`, `Session <cookie>`, or a custom resolver hook).
- Resolves the token to a `User` via Django's standard auth backends.
- Attaches the resolved user + a Django-shaped request-like context to the per-RPC ContextVar.
- Resolvers access it via the same `info.context.user` pattern they use under GraphQL.

The same `apply_cascade_permissions` (item 1 / `TODO-ALPHA-025`) and `Meta.rate_limit` (item 24) and typed error envelope (item 19) apply unchanged — they read from `info.context`, not from a request-shaped object, so the gRPC interceptor stack populates the same fields the Django HTTP middleware does.

#### Schema-author experience

```python path=null start=null
class OrderType(DjangoType):
    class Meta:
        model = Order
        fields = "__all__"
        filterset_class = filters.OrderFilter
        orderset_class  = orders.OrderOrder
        rest = True
        grpc = {
            "service": "orders.v1.OrdersService",   # protobuf service path
            "list_mode": "stream",                   # unary | stream
            "mutations": "all",                       # all | none | ["create", "update"]
        }
        streamable = {"chunk_size": 1000}           # composes with item 30 over gRPC
```

`./manage.py makeprotos` writes `proto_migrations/0001_initial.py` and `proto/orders/v1/orders.proto`. CI runs `./manage.py checkprotos`. Production runs `./manage.py rungrpc --port 50051`.

#### Generated `.proto` example

```protobuf path=null start=null
// proto/orders/v1/orders.proto — generated; do not edit by hand
syntax = "proto3";

package orders.v1;

import "google/protobuf/timestamp.proto";

service OrdersService {
  rpc GetOrder       (GetOrderRequest)        returns (Order);
  rpc ListOrders     (ListOrdersRequest)      returns (stream Order);          // streamable + list_mode="stream"
  rpc CreateOrder    (CreateOrderInput)       returns (Order);
  rpc UpdateOrder    (UpdateOrderInput)       returns (Order);
  rpc DeleteOrder    (DeleteOrderRequest)     returns (DeleteOrderResponse);
  rpc StreamOrders   (StreamOrdersRequest)    returns (stream Order);          // item 30 streaming download
}

message Order {
  int64                       id          = 1;
  string                      reference   = 2;
  OrderStatus                 status      = 3;
  google.protobuf.Timestamp   created_at  = 4;
  // reserved 5;  // ← removed Order.legacyTotal in proto_migrations/0007
  int64                       customer_id = 6;
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING     = 1;
  ORDER_STATUS_PAID        = 2;
  ORDER_STATUS_SHIPPED     = 3;
  ORDER_STATUS_CANCELLED   = 4;
}
```

#### Client experience

Same backend serves four polyglot clients identically:

```go path=null start=null
// Go service-to-service call
client := orders.NewOrdersServiceClient(conn)
order, err := client.GetOrder(ctx, &orders.GetOrderRequest{Id: 42})
```

```rust path=null start=null
// Rust binary client (no JSON, no GraphQL)
let mut client = OrdersServiceClient::connect("https://api.example.com:50051").await?;
let order = client.get_order(GetOrderRequest { id: 42 }).await?;
```

```python path=null start=null
# Internal Python service-to-service call (no Django runtime needed in the caller)
import grpc
from generated import orders_pb2_grpc, orders_pb2

with grpc.insecure_channel("orders-service:50051") as channel:
    stub  = orders_pb2_grpc.OrdersServiceStub(channel)
    order = stub.GetOrder(orders_pb2.GetOrderRequest(id=42))
```

```typescript path=null start=null
// Browser via grpc-web (generated by `--emit grpc-web`)
import { OrdersServiceClient } from "./generated/grpc-web/orders/v1/orders";

const client = new OrdersServiceClient("https://api.example.com");
const order  = await client.getOrder({ id: 42 });
```

#### Composition with other `BACKLOG.md` items

- **Item 17 (cost & complexity limits)** — gRPC requests carry the same cost-budget logic via the same selection walker; rejections become `RESOURCE_EXHAUSTED` gRPC status with the typed error envelope from item 19 in the trailers.
- **Item 18 (HTTP-spec transport)** — N/A; gRPC has its own HTTP/2 semantics. Caching headers don't apply, but item 15's content-versioned-node hashes can ride in gRPC response metadata for client-side caches.
- **Item 19 (typed error envelope)** — `FieldError` maps onto `google.rpc.Status` + `google.rpc.BadRequest.FieldViolation` (the protobuf-standard error detail format). The same `code` / `field` / `message` / `params` survive the protocol switch.
- **Item 20 (mutation invalidation gossip)** — `extensions["dst.invalidations"]` becomes gRPC response trailer `dst-invalidations` (gzipped protobuf payload listing affected entity IDs).
- **Items 21 / 26 / 27 (codegen)** — `./manage.py export_schema --emit grpc-web` produces a TypeScript client targeting `@improbable-eng/grpc-web`. The tRPC-style invokable surface (item 26) gains a transport switch so the same call site (`client.queries.orders.get({ id: 42 })`) can dispatch over GraphQL OR gRPC OR REST based on a build-time config.
- **Item 24 (per-resolver rate limits)** — rate limiting happens in a `RateLimitInterceptor`, populated from the same `Meta.rate_limit` declarations.
- **Item 28 (mutation batching with transactional semantics)** — gRPC client streaming (many requests → one response) is the natural protocol fit. The batch endpoint becomes `rpc BatchMutations(stream MutationOp) returns (BatchResponse)`.
- **Item 29 (schema usage analytics)** — gRPC interceptors record per-RPC hits exactly the way the GraphQL extension records per-field hits; the management command (`./manage.py schema_usage`) shows both surfaces side-by-side.
- **Item 30 (resumable streaming downloads)** — *this is the natural protocol for streaming*. gRPC server-streaming is binary, multiplexed, native HTTP/2. Item 30's NDJSON-over-HTTP becomes the browser default; gRPC server-streaming becomes the high-throughput default for backend / mobile / polyglot consumers. Same token, same snapshot semantics, same resume contract — different framing.

#### Failure modes and edge cases

- **HTTP/2 not available** (deployment misconfiguration, downgraded proxy) — `rungrpc` startup fails loudly; the in-process gRPC-Web bridge returns a typed error explaining the misconfiguration rather than serving over HTTP/1.1.
- **Field-number conflict during schema evolution** — `./manage.py makeprotos` refuses to run if a previously-assigned number would be reused; `./manage.py checkprotos` blocks CI for the same reason.
- **GraphQL field added but proto migration not run** — `checkprotos` fails CI with the missing field name and a suggested `makeprotos` invocation.
- **GraphQL field removed without proto reservation** — `checkprotos` fails CI with the reserved-number requirement. Migration generator can run in `--reserve-removed` mode to handle this automatically.
- **Browser client without gRPC-Web proxy** — browser request hits the bare gRPC port, fails. The in-process bridge at `/grpc-web/` is the documented fallback.
- **Auth metadata missing on a non-public RPC** — interceptor returns `UNAUTHENTICATED`; same code path as the GraphQL extension's auth failure.
- **Long-running server stream cancelled by client** — `grpcio` raises a cancellation signal; the per-chunk loop from item 30 detects it on the next yield and stops cleanly.
- **Protobuf message size limit (4 MB default)** — large connections-of-large-objects can exceed gRPC's default message size. The streaming mode is the answer for connections > 4 MB; the unary mode is documented as "use for bounded responses only."
- **Type renamed via `Meta.name = "X"`** — proto migration tracks both the GraphQL alias and the protobuf message name independently; the protobuf message name is stable even when the GraphQL name changes.

**Why it matters**: this closes the *"we cover GraphQL + REST + tRPC + TanStack"* (items 16, 26, 27) story into *"we cover GraphQL + REST + tRPC + TanStack + gRPC + streaming downloads"* — every viable wire shape from one declaration. Two distinct audiences pick this up:

1. **Polyglot microservice teams**. Internal service-to-service traffic between Django and Go / Rust / Java / C++ services stops needing a hand-maintained `.proto` schema and a parallel gRPC service. Same Django model + Meta declaration drives all wires; the gRPC server starts with one management command.
2. **Mobile clients**. iOS / Android / Flutter clients that care about bytes-on-the-wire and battery life can drop a generated gRPC client and stop sending JSON. The package's existing optimizer, permissions, error envelope, and rate-limit machinery apply unchanged.

Nothing in the Django ecosystem does this today. `django-grpc-framework` ships gRPC but doesn't share a schema with anything; the GraphQL + DRF + gRPC tri-stack is currently maintained by hand at every team that needs it.

### 41. First-class multi-database / sharding-aware optimizer

**Realistic**: 3/10 — Multi-database is a niche Django facility most teams don't reach for. Cross-shard joins are genuinely hard and Django's ORM doesn't help — there's no built-in cross-shard `JOIN`, so any first-class story has to invent the planning seam itself.

**Impact**: 4/10 — Strong differentiator for the narrow audience that runs sharded Django (large multi-tenant SaaS, fintech with data-residency requirements, Instagram-scale read-heavy apps). Invisible to most consumers, but the audience that needs it has nowhere else to go.

**Difficulty**: 8/10 — Cross-shard queryset planning, shard-aware `Prefetch` reconciliation, and cross-shard aggregate composition. The hard cases (FK from shard A pointing into shard B) require schema-aware routing decisions the optimizer doesn't currently make. Concentrating the routing decision behind `Meta.preferred_database` keeps the consumer-facing surface small, but the optimizer-internal work is substantial.

**What this is**: a multi-database story that goes beyond polite cooperation (which the package already does — see [`KANBAN.md`](KANBAN.md) `WIP-ALPHA-019-0.0.7` for the contract that pins today's `router.db_for_read` cooperation, strictness-mode routing, and `.using()` plan correctness). First-class means:

- the optimizer detects when a planned join would cross shards and falls back to a routed `Prefetch` instead
- `Meta.preferred_database = "shard_b"` declares a `DjangoType`'s home shard so the optimizer can route automatically without `.using()` boilerplate everywhere
- multi-shard aggregates compose results from each shard (count / sum / min / max are trivial; avg and group-by need explicit reduce semantics)
- M2M through-tables respect routing for the through-table's database
- connection pagination (`TODO-ALPHA-024` Connection-aware optimizer planning) respects shard locality — sharded connections paginate within a shard, not across

**Why it matters**: apps that run sharded Django today (Instagram-shape large multi-tenants, fintech with per-region data residency, multi-tenant SaaS with isolated tenant DBs) currently hand-roll their queryset routing. They write `.using(tenant_db)` everywhere and the optimizer doesn't help them — it just gets out of the way. First-class support means GraphQL queries against routed types automatically plan against the right database, cross-shard relations downgrade to a `Prefetch` instead of failing or N+1ing, and the response shape stays consistent with the single-DB case. Nobody else in the Django GraphQL ecosystem is even close.

**Framework integration**: builds on the shipped cooperation contract from `WIP-ALPHA-019-0.0.7`. Composes with `Meta.get_queryset` (the routing decision could live there per-type, in tandem with the explicit `Meta.preferred_database`). Composes with `TODO-ALPHA-024` (Connection-aware optimizer — sharded connection pagination). Composes with item 33 (DoS policy stack — per-shard rate limits and cost budgets). Composes with item 19 (typed error envelope — surfacing cross-shard routing errors with a stable error code). Composes with item 4 (polymorphic / `GenericForeignKey`) when the polymorphic targets live on different shards.

## How to use this file
- When scheduling a slice after parity items land, pull a high-`Realistic` `BACKLOG.md` item that isn't already on `KANBAN.md`.
- Promote it to a `KANBAN.md` `TODO-*` card (or `BACKLOG-*` if it's not committed to a milestone yet).
- Write its `docs/spec-<NNN>-<topic>-<0_0_X>.md` and follow the existing slice cadence.
- When the slice ships, cross-reference the `BACKLOG.md` item from the new `KANBAN.md` `DONE-*` card so the differentiation story stays traceable.

If a `BACKLOG.md` item turns out to be wrong (the upstream packages ship it, real-world adopters don't want it, or the architectural cost is too high), strike it through with a one-line note explaining why; do not delete it. The history of rejected differentiators is itself useful design context.
