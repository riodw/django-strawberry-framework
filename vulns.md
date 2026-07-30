I need you to now  investigate this:

| Rank | Hunt item | Why revisit it | What I would attack next |
|---:|---|---|---|
- [x] | 1 | [filters/sets.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/filters/sets.py) | Nearly 2,000 lines governing recursive filters, related visibility, and field-level permission gates. The first hunt already found incorrect permission invocation, proving this boundary is delicate. | Permission bypasses through nested `and`/`or`/`not`, repeated related filters, omitted inputs, shared FilterSets with multiple owners, async parity, exceptions during permission checks, and database shards.

- [x] | 2 | [mutations/resolvers.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/resolvers.py) | The central authorization and write pipeline. A flaw could permit unauthorized creation, updates, deletion, relation assignment, or partial commits. | TOCTOU races between locate/authorize/write, permission changes during execution, custom hooks with side effects, multi-database transactions, rows disappearing concurrently, and rollback after caught errors.


- [x] | 3 | [rest_framework/resolvers.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/rest_framework/resolvers.py) | Combines DRF validation, renamed sources, visibility-scoped relation querysets, save hooks, partial updates, and the shared mutation pipeline. It already contained silent client-value replacement. | `source="*"`, nested serializers, custom `create`/`update`, hidden related rows, renamed fields, injected/save kwargs, partial list relations, and serializer hooks that query or write before validation completes.


- [x] | 4 | [permissions.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/permissions.py) | Direct row-level visibility enforcement across relation graphs. Any missed edge can expose records. | Proxy models, MTI, nullable chains, GenericForeignKeys, recursive diamonds, exceptions inside visibility hooks, cross-database aliases, and concurrent ContextVar use.


- [xx] | 5 | [utils/querysets.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/utils/querysets.py) | Shared execution boundary for `get_queryset` visibility across queries, filters, mutations, Relay, forms, and DRF. A normalization mistake could bypass visibility system-wide. | Hooks returning managers, wrong-model querysets, awaitables, custom iterables, cached querysets, incorrect database aliases, and differing sync/async return shapes.
`Find in the commits a document called get_queryset-visibility-boundary-plan.md`


- [ ] | 6 | [auth/mutations.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/auth/mutations.py) | Owns credentials and session lifecycle. The ledger already records that authenticated logout over the Channels adapter cannot flush the session. | Session fixation and rotation, WebSocket logout, backend selection, inactive users, enumeration timing, concurrent login/logout, malformed credentials, and failures after authentication but before session persistence.


- [ ] | 7 | [utils/permissions.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/utils/permissions.py) | Converts HTTP and WebSocket context shapes into the request and actor used by every permission surface. It already produced the hunt’s transport-wide High-severity defect. | Crafted context mappings, stale or lazy users, absent middleware, conflicting `consumer.scope` and `scope`, WebSocket reconnects, session mutation, and request wrappers exposing multiple actor sources.


- [ ] | 8 | [forms/resolvers.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/forms/resolvers.py) | Reconstructs partial updates, decodes visible relations, authorizes, and writes transactionally. The first hunt found an actual partial-commit defect. | `to_field_name`, omitted versus cleared relations, `commit=False`/`save_m2m`, custom `perform_mutate`, form hooks with side effects, multi-database writes, and rollback after validation or save errors.

- [ ] | 9 | [relay.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/relay.py) and [types/relay.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/types/relay.py) | Global IDs are a type-confusion and existence-oracle boundary. One wrong mapping can fetch a hidden object or an object of the wrong model. | Duplicate GraphQL names, multiple types over one model, custom off-PK NodeIDs, same-PK cross-model confusion, batch ordering, hidden versus missing query parity, registry resets, and database aliases.

- [ ] | 10 | [optimizer/nested_planner.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/optimizer/nested_planner.py) | Large, newly extracted, and initially omitted from the hunt inventory. Wrong partition or attachment logic could return one parent’s rows under another parent. | PostgreSQL lateral execution, self-M2M custom through models, GenericRelations, divergent aliases, strategy refusal after partial planning, cross-parent partitioning, hidden-child visibility, and exception rollback of plan state.

- [ ] | 11 | [keyset.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/keyset.py) | Cryptographic cursor boundary. Probability is lower because the first pass was strong, but impact includes cursor tampering, replay, and disclosure of ordering values. | Cursor replay across types, fields, tenants and databases; key rotation races; malformed-ciphertext resource exhaustion; huge fallback-key lists; and schema/order changes during cursor lifetime.

- [ ] | 12 | [registry.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/registry.py) and [types/finalizer.py](/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/types/finalizer.py) | Process-global lifecycle state can create cross-schema or cross-test contamination. This area was heavily refactored while the hunt was running, and its final gate still has stale/broken coverage. | Concurrent schema construction, clear during finalization, failed-finalization retries, dynamically imported types, duplicate models across app registries, task/thread interleaving, and stale permission/type caches.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
