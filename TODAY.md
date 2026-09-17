# Today

**This file is the mile-marker.** [`GOAL.md`][goal] owns the destination: an `astronomy` app of seven files that runs verbatim at `1.0.0`. [`KANBAN.md`][kanban] owns delivery and acceptance, card by card. This file owns the current capability boundary: what a consumer can build with the package right now, where each of GOAL's eight success criteria stands, and what has to change in the `astronomy` files to run them on today's implementation. It connects the other two without repeating either. It is not the changelog; [`CHANGELOG.md`][changelog] carries history, and [`docs/GLOSSARY.md`][glossary] carries per-capability shipped / planned status.

## Snapshot contract

"Today" means **the current checkout of `main`**, not the last published release and not the board's `Done` column. Verdicts describe implementation; acceptance (the card's board state) and evidence (which live or package test pins it) are reported beside the verdict, never folded into it. The two diverge in one place at the moment: the [`DjangoListField` argument surface][kanban-list-field-args] (`offset` / `limit` / `orderBy`) is implemented and live-tested while its card is still `WIP`.

Three verdict words are used throughout:

- **Available.** Implemented in the current checkout.
- **Partially available.** Implemented for a stated subset; the boundary and the card that widens it are named.
- **Not implemented.** No code; the owning card is named.

Evidence is a live test under `examples/fakeshop/test_query/` wherever a request can reach the surface; where it cannot, the package suite under `tests/` is named instead.

The demonstration app is `examples/fakeshop/apps/products/` (`Category` / `Item` / `Property` / `Entry`, FK-only). It is the same shape as `astronomy`'s `Galaxy` / `CelestialBody`, so "products runs it" is the operational meaning of "available" for the GOAL comparison below.

## What you can build today

The maintained end-to-end walkthrough is the [Quick start in `docs/README.md`][readme-quick-start]. The compressed products-shaped version, complete enough to run, is:

```python
# apps/products/schema.py
import strawberry
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
    apply_cascade_permissions,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.orders import OrderSet, RelatedOrder

from . import models


class CategoryFilter(FilterSet):
    class Meta:
        model = models.Category
        fields = {"id": "__all__", "name": "__all__", "description": ["exact", "icontains"]}


class ItemFilter(FilterSet):
    category = RelatedFilter(CategoryFilter, field_name="category")

    class Meta:
        model = models.Item
        fields = {"id": "__all__", "name": "__all__", "category__name": ["exact"]}


class CategoryOrder(OrderSet):
    class Meta:
        model = models.Category
        fields = "__all__"


class ItemOrder(OrderSet):
    category = RelatedOrder(CategoryOrder, field_name="category")

    class Meta:
        model = models.Item
        fields = ["name"]


def _staff_or_public(cls, queryset, info):
    user = getattr(getattr(info.context, "request", None), "user", None)
    if user and user.is_staff:
        return queryset
    return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


class CategoryType(DjangoType):
    class Meta:
        model = models.Category
        fields = ("id", "name", "description", "items", "is_private")
        interfaces = (relay.Node,)
        filterset_class = CategoryFilter
        orderset_class = CategoryOrder

    get_queryset = classmethod(_staff_or_public)


class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = ("id", "name", "description", "category", "is_private")
        interfaces = (relay.Node,)
        filterset_class = ItemFilter
        orderset_class = ItemOrder

    get_queryset = classmethod(_staff_or_public)


@strawberry.type
class Query:
    all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)
    all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)


class CreateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "create"


@strawberry.type
class Mutation:
    create_item = DjangoMutationField(CreateItem)
```

```python
# config/schema.py
import strawberry
from apps.products.schema import Mutation, Query

from django_strawberry_framework import DjangoOptimizerExtension, DjangoSchema, finalize_django_types, strawberry_config

finalize_django_types()
_optimizer = DjangoOptimizerExtension()
schema = DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])
```

The two [`FilterSet`][glossary-filterset]s and two [`OrderSet`][glossary-orderset]s are inlined so the snippet registers a `DjangoType` for every model its fields and sidecars reach; `finalize_django_types()` raises `ConfigurationError` for a relation whose target model has no registered type, rather than substituting a stub. The live products sidecars in `apps/products/filters.py` / `apps/products/orders.py` span all four models and add the `check_<field>_permission` gates GOAL's `filters.py` shows.

**Read.** Every connection accepts `first` / `last` / `before` / `after`, plus a `filter:` and `orderBy:` argument synthesized from the type's sidecars (lookup names are camel-cased on the wire: `icontains` is `iContains`). The request runs the type's `get_queryset` first, then filter, then order, then a pk tiebreak, then the optimizer plan for the selected `edges { node }` tree, then the cursor slice. An anonymous caller sees no private row through any path: root connection, nested relation, or node refetch.

```graphql
{
  allItems(
    filter: {
      name: {
        iContains: "widget"
      }
    }
    orderBy: [
      {
        name: ASC
      }
    ]
    first: 10
  ) {
    edges {
      node {
        id
        name
        category {
          name
        }
      }
    }
  }
}
```

**Write.** `createItem` takes a generated `ItemInput!` whose required-ness follows the column's `default` / `blank` / `null`; the FK is `categoryId`, a `GlobalID` taken from any `id` the read side returned and type-checked against `Category` at decode. The permission boundary has two layers that never mix: a caller without the Django `products.add_item` permission (anonymous included) is refused with a top-level `GraphQLError` before any write; a caller who passes it but fails `full_clean()` or a model constraint gets a `null` node and one `FieldError` per offending field in `errors`, with `"__all__"` for multi-field constraints. The whole operation, including serialization of the returned `node`, runs inside one transaction because `DjangoSchema` installs the execution context that holds it open.

```graphql
mutation {
  createItem(
    data: {
      name: "Widget"
      categoryId: "<id from allCategories>"
    }
  ) {
    node {
      id
      name
    }
    errors {
      field
      messages
    }
  }
}
```

Live evidence for this journey: `examples/fakeshop/test_query/test_products_api.py` (reads, filters, orders, every write path and both permission layers), `test_products_visibility_api.py` (visibility through planned and unplanned relations), `test_connection_pagination_api.py` (cursor semantics), `test_mutation_atomicity.py` (the response-spanning transaction).

## GOAL success criteria, compared

| # | GOAL criterion | Today | Limitation | Evidence | Owning card |
| --- | --- | --- | --- | --- | --- |
| 1 | Rich model-backed types in one `class Meta` | Partially available | `Meta.aggregate_class`, `Meta.fields_class`, `Meta.search_fields` not accepted | `test_products_api.py`, `test_library_api.py` | [Aggregation][kanban-aggregation], [`FieldSet`][kanban-fieldset], [`search_fields`][kanban-search-fields] |
| 2 | Collections without hand-written resolvers | Available | None in implementation; the `DjangoListField` `offset` / `limit` / `orderBy` arguments are accepted and live-tested while the card is still `WIP` | `test_products_api.py`, `test_list_field_api.py` | [`DjangoListField` arguments][kanban-list-field-args] |
| 3 | Nested filtering / ordering / aggregation / search | Partially available | Filtering and ordering nested through `RelatedFilter` / `RelatedOrder`. No aggregation, no search. Filter / logic key names fixed | `test_products_api.py`, `test_scalars_filter_api.py` | [Aggregation][kanban-aggregation], [`search_fields`][kanban-search-fields], [full-text primitives][kanban-full-text-search], [filter key namespace][kanban-filter-keys] |
| 4 | Row, field, and cascade permissions, one hook for reads and writes | Partially available | Row and cascade cover connections, nested traversal, refetch, and the mutation locate. Cascade crosses forward single-column FK / O2O edges only; to-many edges are unresolved. No field-level gates | `test_products_visibility_api.py`, `test_products_api.py` | [Graph substrate][kanban-graph-substrate], [`FieldSet`][kanban-fieldset] |
| 5 | Automatic ORM optimization from one selection walk | Partially available | `select_related` / `prefetch_related` / `only()` from the selection tree, `Prefetch` downgrade for consumer querysets, FK-id elision, strictness modes. A nested connection is window-batched only when it carries no `filter:` / `orderBy:`; with either it resolves per parent row. No explain view | `test_single_parent_fastpath_api.py`, `test_optimizer_auto_api.py`, `test_connection_pagination_api.py` | [Nested sidecar batching][kanban-nested-batching], [Explain mode][kanban-explain-mode] |
| 6 | Declarative mutations from `ModelForm`, `ModelSerializer`, or generated inputs | Available | Three flavors, one envelope, `Upload`, deny-by-default, response-spanning transaction. No idempotency keys | `test_products_api.py`, `test_uploads_api.py`, `test_mutation_atomicity.py` | [Idempotency keys][kanban-idempotency] |
| 7 | Migrate from four upstream stacks without the source package | Partially available | GOAL's migration diffs run as written and the DRF `FilterSet` parent swap is real. No written guides; filter / logic key names not configurable; six small parity gaps open; cookbook port not started | GOAL diffs, `test_library_api.py` | [Migration guides][kanban-migration-guides], [filter key namespace][kanban-filter-keys], [parity-gap closure][kanban-parity-gaps], [cookbook parity][glossary-cookbook-parity] (glossary obligation, no card) |
| 8 | Internet-facing from the docs alone | Partially available | Package defaults: error masking with a correlation id, execution resource bounds, request-body cap, UTF-8 wire contract, path-free file output. Deployment-owned: rate limiting, cache policy, upload content handling, the production mount. The package describes itself as not production-ready | `test_error_policy_api.py`, `test_resource_policy_api.py`, `test_transport_api.py` | [Production security profile][readme-production-security-profile] (row-by-row enforcement is the `1.0.0` gate), [Adversarial suite][kanban-adversarial] |

The "Owning card" column names the card that widens the row; it is not a claim that the card alone completes the criterion.

## Running `astronomy` today

What changes in GOAL's seven files to run them on the current implementation, and nothing else:

| GOAL file | Today | Adaptation |
| --- | --- | --- |
| `models.py` | Available | None. The `TextChoices` column becomes an enum ([choice enum generation][glossary-choice-enum-generation]); the enum's name is not yet overridable ([naming override][kanban-choice-enum-naming]) |
| `schema.py` | Partially available | Drop the `aggregates` and `fields` imports and the three `Meta` keys `aggregate_class` / `fields_class` / `search_fields`. Everything else runs: `fields = "__all__"`, `relay.Node`, both sidecar keys, `get_queryset` with `apply_cascade_permissions`, `DjangoNodeField`, `DjangoConnectionField`, `finalize_django_types`, `DjangoSchema`, `DjangoOptimizerExtension(strictness="raise")`, `strawberry_config` |
| `mutations.py` | Available | None |
| `filters.py` | Available | None. Dict-form `Meta.fields`, per-field `"__all__"`, `RelatedFilter` by class or string, `queryset=` scope boundary, relation-path keys, `check_<field>_permission` |
| `orders.py` | Available | None. `"__all__"` or explicit list, `RelatedOrder` by class or string, `check_<field>_permission` |
| `aggregates.py` | Not implemented | Delete the file until [Aggregation subsystem][kanban-aggregation] ships |
| `fields.py` | Not implemented | Delete the file until [`FieldSet`][kanban-fieldset] ships |

Products is this adaptation plus two local choices: its `Query` is connections-only with no `DjangoNodeField` roots (the library app runs `node` / `nodes` live; products adopts them on the [activation card][kanban-fakeshop-activation]), and its project schema runs the optimizer at the default strictness rather than GOAL's `"raise"`.

## Other available capabilities

Shipped surfaces that products' FK-only, text / boolean / datetime / one-file model shape does not reach. Each links its glossary entry; the sibling app named is where it runs live, otherwise the package suite under `tests/` covers it.

- **Relations.** Forward and reverse `OneToOneField` / `ManyToManyField`; every to-many relation as a `<field>Connection` by default with the raw list as an opt-in through `Meta.relation_shapes`. Library app. [Relation handling][glossary-relation-handling].
- **Scalars.** `BigInt`, `Decimal`, `UUID`, `JSON`, PostgreSQL `ArrayField` / `HStoreField`, date / time types, structured file and image output with the filesystem path as a per-column opt-in. Scalars app. [Scalar field conversion][glossary-scalar-field-conversion].
- **Type configuration.** `Meta.primary`, `Meta.exclude`, `Meta.name` / `Meta.description`, `Meta.nullable_overrides` / `Meta.required_overrides`, `Meta.connection` for `totalCount`, `Meta.globalid_strategy`, `Meta.optimizer_hints`. Library app. [`DjangoType`][glossary-djangotype].
- **Root refetch.** `DjangoNodeField` / `DjangoNodesField`. Library app. [`DjangoNodeField`][glossary-djangonodefield].
- **Model-less forms.** `DjangoFormMutation` over a plain `Form` shares the `FieldError` envelope and the deny-by-default posture (`DenyAll` when `Meta.permission_classes` is unset) but has no model row to locate or re-fetch; the model-backed flavors share the full write pipeline. Products app. [`DjangoFormMutation`][glossary-djangoformmutation].
- **Session auth.** `login` / `logout` / `register` and the `me` query from the `auth` submodule. Accounts app. [Auth mutations][glossary-auth-mutations].
- **Multiple databases.** Router-aware reads, one write alias per mutation; fakeshop's sharded mode behind `FAKESHOP_SHARDED=1`. [Multi-database cooperation][glossary-multi-database-cooperation].
- **Transport.** The Channels ASGI router for WebSocket subscriptions; no example app, since fakeshop is WSGI-only. [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter].
- **Development tooling.** Response debug extension, debug-toolbar middleware, `TestClient` / `GraphQLTestCase`, each behind a leaf import. [`DjangoDebugExtension`][glossary-djangodebugextension], [debug-toolbar middleware][glossary-debug-toolbar-middleware], [`TestClient`][glossary-testclient].

## Remaining distance, by population

Three different populations, kept apart:

**Literal `astronomy` gaps.** The three unshipped sidecars: [`FieldSet`][kanban-fieldset], [`Meta.search_fields`][kanban-search-fields] with its [Postgres primitives][kanban-full-text-search], and the [Aggregation subsystem][kanban-aggregation].

**Success-criterion gaps beyond the seven files.** [Graph substrate][kanban-graph-substrate] (to-many cascade semantics, row-preserving predicate composition), [nested sidecar batching][kanban-nested-batching], [filter / logic key namespace][kanban-filter-keys], [migration guides][kanban-migration-guides], [node-sentinel redaction][kanban-redaction], [explain mode][kanban-explain-mode], [idempotency keys][kanban-idempotency], [adversarial suite][kanban-adversarial], and the cookbook port ([cookbook parity][glossary-cookbook-parity], a glossary obligation proven at `1.0.0` with no owning card today).

**Release and acceptance work.** The `WIP` [`DjangoListField` arguments][kanban-list-field-args], the alpha `To Do` column through the [beta release card][kanban-beta-release] (parity-gap closure, the debug-extension extraction, boundary hardening, the conversion registry, federation, documentation-debt discharge), and on the beta line the [fakeshop activation][kanban-fakeshop-activation] and [product-catalog Layer 3 tests][kanban-layer3-tests] that turn shipped capability into products-level acceptance. The authoritative order is the board itself.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: CHANGELOG.md
[goal]: GOAL.md
[kanban]: KANBAN.md
[kanban-adversarial]: KANBAN.html#adversarial_non_live_test_suite
[kanban-aggregation]: KANBAN.html#aggregation_subsystem
[kanban-beta-release]: KANBAN.html#beta_release_cleanup_verification_alpha_beta
[kanban-choice-enum-naming]: KANBAN.html#stable_choice_enum_naming_override
[kanban-explain-mode]: KANBAN.html#optimizer_explain_mode
[kanban-fakeshop-activation]: KANBAN.html#fakeshop_graphql_schema_activation
[kanban-fieldset]: KANBAN.html#fieldset_declarative_field_level_behavior_metafields_class
[kanban-filter-keys]: KANBAN.html#configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key
[kanban-full-text-search]: KANBAN.html#postgres_full_text_search_filter_primitives
[kanban-graph-substrate]: KANBAN.html#graph_substrate_shared_graph_policy_and_dependency_planning
[kanban-idempotency]: KANBAN.html#mutation_idempotency_keys
[kanban-layer3-tests]: KANBAN.html#product_catalog_layer_3_http_graphql_tests
[kanban-list-field-args]: KANBAN.html#djangolistfield_argument_surface_offset_limit_and_orderby
[kanban-migration-guides]: KANBAN.html#migration_and_adoption_guides
[kanban-nested-batching]: KANBAN.html#structural_optimization_templates_and_nested_sidecar_batching
[kanban-parity-gaps]: KANBAN.html#upstream_parity_gap_closure
[kanban-redaction]: KANBAN.html#opt_in_node_sentinel_redaction_tier_metaredaction_mode
[kanban-search-fields]: KANBAN.html#metasearch_fields_support

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
[glossary-auth-mutations]: docs/GLOSSARY.md#auth-mutations
[glossary-choice-enum-generation]: docs/GLOSSARY.md#choice-enum-generation
[glossary-cookbook-parity]: docs/GLOSSARY.md#cookbook-parity
[glossary-debug-toolbar-middleware]: docs/GLOSSARY.md#debug-toolbar-middleware
[glossary-djangodebugextension]: docs/GLOSSARY.md#djangodebugextension
[glossary-djangoformmutation]: docs/GLOSSARY.md#djangoformmutation
[glossary-djangographqlprotocolrouter]: docs/GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangonodefield]: docs/GLOSSARY.md#djangonodefield
[glossary-djangotype]: docs/GLOSSARY.md#djangotype
[glossary-filterset]: docs/GLOSSARY.md#filterset
[glossary-multi-database-cooperation]: docs/GLOSSARY.md#multi-database-cooperation
[glossary-orderset]: docs/GLOSSARY.md#orderset
[glossary-relation-handling]: docs/GLOSSARY.md#relation-handling
[glossary-scalar-field-conversion]: docs/GLOSSARY.md#scalar-field-conversion
[glossary-testclient]: docs/GLOSSARY.md#testclient
[readme-production-security-profile]: docs/README.md#production-security-profile
[readme-quick-start]: docs/README.md#quick-start

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
