# Spec: Permissions subsystem — `apply_cascade_permissions` cascade visibility (sync + async), optimizer `Prefetch`-downgrade cooperation, permission-gate and connection composition, and the per-field permission surface decision

Shipped in `0.0.10` (card [`DONE-034-0.0.10`][kanban]). **This spec is the final implementation record, not an open build plan.** The card was directed to spec by the maintainer alongside [`DONE-033-0.0.9`][kanban] (connection-aware optimizer planning); the two cards are independent — this card touches no optimizer-walker seam, and the optimizer cooperation it needs (the [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] → `Prefetch` downgrade) shipped in `0.0.3` and is untouched by `033`. The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention); the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)): this card shares the `0.0.10` patch line with [`DONE-035-0.0.10`][kanban] (optimizer robustness hardening); the `pyproject.toml` / `__version__` / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.10` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.10` line and never bump the version themselves.

Status: **SHIPPED (`0.0.10`) — all five slices (cascade foundation; optimizer cooperation + N+1 audit; composition pins; products activation + live HTTP; doc updates + card-completion wrap) final-accepted.** Card [`DONE-034-0.0.10`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.10]` heading. The `0.0.10` version bump and the `CHANGELOG.md` release-heading promotion belong to the joint cut, not to this card, per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut). The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention). Five slices: Slice 1 (the **cascade foundation** — `django_strawberry_framework/permissions.py` with the sync `apply_cascade_permissions(cls, queryset, info, fields=None)` and async `aapply_cascade_permissions(...)` pair, the `ContextVar` cycle guard, single-column forward-FK / OneToOne scope, nullable-FK preservation, multi-DB alias pinning, loud `fields=` validation, and the package-root export — [Decision 4](#decision-4--public-surface-and-naming-apply_cascade_permissions--aapply_cascade_permissions-exported-from-the-package-root) / [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection)), Slice 2 (**optimizer cooperation + N+1 audit** — pins that a cascading hook rides the shipped `Prefetch` downgrade, flips plans uncacheable, and adds zero query round-trips — [Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)), Slice 3 (**composition pins** — the shipped [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] `check_<field>_permission` gates survive unchanged and compose with the cascade ([Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged)); [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoListField`][glossary-djangolistfield] all honor a cascading hook through their existing `get_queryset` application points ([Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code))), Slice 4 (**fakeshop products activation + live HTTP coverage** — the four commented cascade hooks in the products schema activate, exercised by real permission users via `services.create_users(1)` across a 2-deep FK cascade), and Slice 5 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slice 1 is foundation-first; 2 and 3 build on 1; 4 builds on 1–3; 5 lands last.

Owner: package maintainer.

Predecessors: [`spec-033-connection_optimizer-0_0_9.md`][spec-033] (the most-recently-authored spec — the canonical voice / depth / section-layout reference for this document; its Non-goals explicitly hand the permissions subsystem here and pre-pin the composition seam: "*`apply_cascade_permissions` runs inside `get_queryset`, which both the pipeline and the windowed child queryset already honor*"); [`spec-030-connection_field-0_0_9.md`][spec-030] (the connection pipeline whose visibility → filter → order composition the cascade slots into at the `get_queryset` step); [`spec-027-filters-0_0_8.md`][spec-027] / [`spec-028-orders-0_0_8.md`][spec-028] (the shipped `check_<field>_permission` denial gates with active-input-only scope that [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) reconciles against the cascade, and the child-branch visibility derivation that already routes related querysets through target `get_queryset` hooks); [`spec-015-relay_interfaces-0_0_5.md`][spec-015] (the [`SyncMisuseError`][glossary-syncmisuseerror] sync/async hook contract this card's two variants inherit). [`docs/GLOSSARY.md`][glossary] carries [`apply_cascade_permissions`][glossary-apply_cascade_permissions] as `planned for 0.0.10`; Slice 5 flips it to `shipped (0.0.10)` and re-statuses [Per-field permission hooks][glossary-per-field-permission-hooks] per [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) (see [Doc updates](#doc-updates)).

This spec's deliberative layer — the eight-revision review history that produced the contract, every Decision's justification, every alternative each Decision rejected, and the risk / open-question deliberation that settled the card's design questions — lives in the rationale companion [`docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`][spec-034-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — this card. The entry's consumer example (`return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)`) is the canonical surface this spec ships; Slice 5 flips the status and expands the body with the walk mechanism and the four invariants.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — the per-type seam the cascade composes: the helper is *called from inside* a consumer's `get_queryset`, and the per-edge target visibility it intersects is each target type's own `get_queryset`. The entry's optimizer-cooperation paragraph (the `Prefetch` downgrade) is the mechanism Slice 2 pins across the cascade.
- [Per-field permission hooks][glossary-per-field-permission-hooks] — the read-side field gates. The entry currently says `planned for 0.0.10` while hosting the hooks on [`FieldSet`][glossary-fieldset] (`planned for 0.1.1`) — the contradiction [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) resolves; Slice 5 re-statuses the entry.
- [`FieldSet`][glossary-fieldset] / [`Meta.fields_class`][glossary-metafields_class] — the `0.1.1` host of the per-field read gates; `fields_class` stays in `DEFERRED_META_KEYS` through this card ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)).
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] / [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] / [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] — the shipped input-side subsystems whose `check_<field>_permission` denial gates (active-input-only scope) compose with — and are not replaced by — the cascade ([Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged)). The filter pipeline already derives child-branch visibility from target `get_queryset` hooks, so a cascading hook narrows nested filter branches automatically.
- [`DjangoType`][glossary-djangotype] / [`Meta.primary`][glossary-metaprimary] — the cascade resolves each FK edge's target type through the registry's primary-type lookup; secondary types are never cascade targets ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [Plan cache][glossary-plan-cache] / [Queryset diffing][glossary-queryset-diffing] — the cascade requires **no optimizer change**: a type whose hook cascades is just a type with a custom `get_queryset`, so the shipped downgrade-to-`Prefetch` and the custom-hook `cacheable = False` rule both fire unchanged; Slice 2 pins both.
- [Strictness mode][glossary-strictness-mode] — the cascade composes queries, never lazy-loads, so `"raise"` runs stay silent across cascaded traversals; pinned in Slice 2.
- [Multi-database cooperation][glossary-multi-database-cooperation] — axis 2 (explicit `.using(alias)` preservation) is the contract the per-edge subquery pinning extends: every target visibility subquery is pinned to the caller's resolved alias ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)).
- [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoConnection`][glossary-djangoconnection] / [`Meta.connection`][glossary-metaconnection] — the connection pipeline applies the wrapped type's `get_queryset` first, so a cascading hook narrows connections (and their `totalCount`) with no new code; Slice 3 pins it (card DoD).
- [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield] / [Relay Node integration][glossary-relay-node-integration] — the node refetch defaults route through `get_queryset`, so a cascaded type's hidden rows refetch as `null` with no existence leak; pinned in Slice 3.
- [`DjangoListField`][glossary-djangolistfield] — the default resolver and the `Manager`/`QuerySet`-returning consumer-resolver wrap both apply the type's `get_queryset`; a cascading hook narrows root lists with no new code.
- [`SyncMisuseError`][glossary-syncmisuseerror] — the typed marker for "async `get_queryset` invoked from a sync context"; the cascade walk is the package's **third** surface that can meet an async hook synchronously, and it adopts the same contract ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
- [`ConfigurationError`][glossary-configurationerror] — unknown / non-cascadable names in `fields=` raise it ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)); no other new validation surface.
- [`finalize_django_types`][glossary-finalize_django_types] / [Definition-order independence][glossary-definition-order-independence] — the cascade walks at **call time**, after finalization, so every relation target is settled; no finalizer change.
- [Relation handling][glossary-relation-handling] / [FK-id elision][glossary-fk-id-elision] — the per-relation traversal contracts are unchanged; the cascade is row-level narrowing on the *parent* queryset, orthogonal to how a relation field resolves. FK-id elision's safety rule (no elision when a target `get_queryset` must run) already covers cascading targets.
- [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] / [`OptimizerHint`][glossary-optimizerhint] — untouched; hints shape relation planning, not the parent-row narrowing the cascade performs.
- [`DjangoMutation`][glossary-djangomutation] / [Auth mutations][glossary-auth-mutations] — the `0.0.11` write-side consumers of this card: the mutations card names "write mutations need to compose with `apply_cascade_permissions`" as a dependency; out of scope here beyond keeping the helper's contract write-friendly (it takes any queryset).
- [`AggregateSet`][glossary-aggregateset] / [`get_child_queryset`][glossary-get_child_queryset] — the `0.1.3` aggregation cascade hook is the same *pattern* at the aggregate layer; out of scope, named for the composition map.
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — "Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end" is the rule that keeps `fields_class` deferred here ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)).

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the "first line of every catalog/auth test: `seed_data(N)` or `create_users(N)`" rule (Slice 4's live tests start with `create_users(1)` per the card DoD); the no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" — Slice 5's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 4) and package-internal `tests/` where the path is unreachable from a live query.
- [`docs/TREE.md`][tree] — the target package layout already reserves `permissions.py # planned by TODO-ALPHA-034-0.0.10` at the package top level; tests mirror source one-to-one, so the flat module takes a flat `tests/test_permissions.py` ([Decision 3](#decision-3--module-and-test-locations-flat-permissionspy--teststest_permissionspy)).
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, defs at the bottom under the 10 canonical group headers); the "surface-wise we copy `django-graphene-filters`" rule — the cascade is exactly such a surface, ported at the contract level with the registry / typed-error / async adaptations the package's own architecture requires.

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices: four functional (1, then 2 and 3 on 1, 4 on 1–3) plus a doc + card-completion wrap (5).** Boxes stay unticked because the `Status:` line is the completion source of truth (the shipped-spec convention).

- [ ] Slice 1: cascade foundation — `django_strawberry_framework/permissions.py` + package-root export (per [Decision 4](#decision-4--public-surface-and-naming-apply_cascade_permissions--aapply_cascade_permissions-exported-from-the-package-root) / [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection))
  - [ ] `permissions.py` ships `apply_cascade_permissions(cls, queryset, info, fields=None)`: a call-time walk of `cls`'s model single-column concrete forward relations (`isinstance(field, models.ForeignKey)` AND `getattr(field, "column", None) is not None` — the forward-concrete test, which covers `OneToOneField` and the MTI `<parent>_ptr` parent link and excludes M2M, reverse FK, reverse OneToOne, `GenericRelation`, and multi-column `ForeignObject` relations by construction), resolving each edge's target type via the registry primary lookup ([`registry.py::TypeRegistry.get`][registry]), running **every registered target's** `get_queryset` (identity hooks included — a registered proxy type's filtered `_default_manager` *is* its visibility policy) and skipping only edges whose target model has no registered type, and intersecting `Q(<field>__in=<target visible rows>)` — plus `| Q(<field>__isnull=True)` when the edge is nullable — into the caller's queryset with the target subquery pinned to `queryset.db` ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)). A `GenericForeignKey` or composite / multi-column forward relation is **unsupported**, not skipped: a full walk over a model carrying one fails closed before any hook runs ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection)).
  - [ ] Cycle detection via a module-level `ContextVar` holding a frozen `_TraversalState` (root DB alias, active-type tuple, edge-path frames): re-entry into a type already on the active tuple raises a path-rich [`ConfigurationError`][glossary-configurationerror] rendering the edge path (`AType.b -> BType.a -> AType`), and the one permitted re-entrant shape is an explicit zero-edge scope (`fields=[]`). Every root, edge, and nested frame installs a new state with a token and resets it in a `finally`, so request isolation holds under both WSGI and ASGI.
  - [ ] `fields=` validation: a bare string is rejected up front by an `isinstance(fields, str)` guard (so `fields="item"` fails loudly instead of validating its characters); a non-iterable value and non-string entries raise [`ConfigurationError`][glossary-configurationerror] naming the field-name-iterable contract rather than escaping as a raw `TypeError`; a name matching an unsupported forward relation raises the dedicated no-cascade-semantics error naming the backing-FK recourse; and other unknown or known-but-non-cascadable names (M2M, reverse relations, virtual fields) raise [`ConfigurationError`][glossary-configurationerror] naming the field, the model, and the cascadable set ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)).
  - [ ] Sync misuse contract: the per-edge target-hook invocation is delegated whole to [`utils/querysets.py::apply_type_visibility_sync`][querysets], so a hook returning any awaitable disposes it (a coroutine is closed, a future cancelled) and raises [`SyncMisuseError`][glossary-syncmisuseerror] ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
  - [ ] `aapply_cascade_permissions(cls, queryset, info, fields=None)` runs the sync walk through [`utils/querysets.py::run_in_one_sync_boundary`][querysets] — the package's shared `sync_to_async(thread_sensitive=True)` primitive — so blocking consumer-hook work (e.g. `user.has_perm(...)`'s permission-table reads) stays off the event loop ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
  - [ ] Both symbols export from the package root (`from django_strawberry_framework import apply_cascade_permissions` — the card DoD's import line) and join `__all__`; the public-exports pin in [`tests/base/test_init.py`][test-base-init] grows accordingly (the version pin in the same file is untouched, [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).
  - [ ] Package coverage: new `tests/test_permissions.py` per the [Test plan](#test-plan) — including the card's four dedicated upstream-invariant pins (cycle guard; single-column scope; alias pinning; nullable-FK preservation).
- [ ] Slice 2: optimizer cooperation + N+1 audit (per [Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips))
  - [ ] No optimizer source change. Pins: a relation whose target type's hook cascades still downgrades `select_related` → `Prefetch` (the type reports `has_custom_get_queryset() is True`, so [`optimizer/walker.py::_target_has_custom_get_queryset`][walker] fires the shipped rule); plans embedding a cascading hook are `cacheable = False` ([`optimizer/walker.py::_plan_prefetch_relation`][walker] flips the flag on the mere **presence** of a custom `get_queryset`, regardless of whether the hook reads the request); the cascade itself adds **zero** query round-trips (the `__in` subqueries compile into the caller's single `SELECT`, pinned by an absolute query count); a [Strictness mode][glossary-strictness-mode] `"raise"` run across a cascaded 2-deep traversal stays silent, which pins that the composed shape stays fully planned (strictness reports unplanned *relation-resolver* accesses, so it is the optimizer-planning detector for the cascaded shape, not a second reading of the zero-round-trip property).
  - [ ] Package coverage: `tests/test_permissions.py` query-count and SQL-shape pins + [`tests/optimizer/test_extension.py`][test-opt-extension] downgrade/cacheability pins per the [Test plan](#test-plan).
- [ ] Slice 3: composition pins — gates, connections, nodes, lists (per [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) / [Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code))
  - [ ] No new code in `filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py`. Pins: composition order is **cascade narrows first, gates judge input second** — a `get_queryset` that cascades runs at the visibility step of every pipeline, then the active-input-only `check_<field>_permission` gates fire from `FilterSet.apply_*` / `OrderSet.apply_*` exactly as shipped; a field denial does not leak existence (denied-filter errors and hidden-row-empty results are produced by independent layers); a [`DjangoConnectionField`][glossary-djangoconnectionfield] over a cascading type narrows `edges` and `totalCount` together; [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield] refetch of a cascade-hidden row returns `null` with no existence leak; [`DjangoListField`][glossary-djangolistfield]'s default resolver narrows.
  - [ ] Package coverage: `tests/test_permissions.py` (composition fixtures) + [`tests/test_connection.py`][test-connection] / [`tests/test_relay_node_field.py`][test-relay-node-field] / [`tests/test_list_field.py`][test-list-field] additions per the [Test plan](#test-plan).
- [ ] Slice 4: fakeshop products activation + live HTTP coverage
  - [ ] [`examples/fakeshop/apps/products/schema.py`][products-schema]: the four commented cascade-permission `get_queryset` hooks (one per type, already correctly marked `TODO-ALPHA-034-0.0.10` — only the uncomment remains) activate: staff sees everything; **every non-staff branch — including the matching `view_<model>` permission — gets `queryset.filter(is_private=False)` plus `apply_cascade_permissions(cls, ..., info)`** so rows pointing at hidden targets drop out (the `view_<model>` branch cascades too, so a nested non-null FK selection can never reach a hidden target and raise `RelatedObjectDoesNotExist`).
  - [ ] [`examples/fakeshop/test_query/test_products_api.py`][test-products]: live `/graphql/` coverage with **real permission users** — first line `services.create_users(1)` per [`AGENTS.md`][agents] (never hand-rolled users, card DoD) — across the products 2-deep FK chain (`Entry → Item → Category` / `Entry → Property → Category`): an anonymous request sees no entry whose item's category is private; a `view_item` user sees only non-private items whose category is visible (items under a private category drop) and selecting their nested `category` never errors; a `view_entry` user selecting `item { category }` drops entries under hidden targets rather than erroring; staff sees everything; the per-request query count is pinned fixed (no per-row cascade queries).
  - [ ] **Audit the products seeders' `is_private` defaults and re-pin every existing live assertion that counted would-be-hidden rows.** Activating the four hooks flips anonymous-request visibility across the *entire* products live suite, not just the new tests — this is the single most likely source of churn when the card lands, so it is a load-bearing setup step, not a contingency. Confirm the default seed paths produce public (`is_private=False`) rows, enumerate every assertion whose count would change once anonymous requests stop seeing private-target rows, and re-pin them in this same change.
  - [ ] Existing products live assertions that counted public-only rows keep passing — the activation must be observable only where private fixtures exist; the suite seeds the private/public split it needs through the established service helpers.
- [ ] Slice 5: doc updates + card-completion wrap (per [Doc updates](#doc-updates))
  - [ ] [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog] (the explicit permission grant), [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render). No version-file edits ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

## Problem statement

The package's row-level visibility story is per-type and stops at the type boundary. A consumer writes one [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] per [`DjangoType`][glossary-djangotype] — staff sees everything, others see `is_private=False` — and the shipped machinery honors it everywhere that *resolves that type*: root lists, connections, node refetch, relation traversal under the optimizer's `Prefetch` downgrade, nested filter branches. What nothing does today is make one type's visibility *reach through foreign keys into another type's rows*. An `Entry` whose `Item` is private is still a perfectly visible `Entry`: the entry row itself carries no `is_private` flag that knows about its parent, and `EntryType.get_queryset` has no vocabulary for "drop rows whose FK targets someone else's hook would hide". Every consumer that needs cascading visibility hand-writes the subqueries — per FK, per type, per app — exactly the kind of schema machinery the package exists to generate ([`GOAL.md`][goal] #"The project misses the goal if users must routinely hand-build the same schema machinery the package is supposed to generate").

The upstream reference solved this with a single composable helper. `django_graphene_filters`'s `apply_cascade_permissions(node_class, queryset, info, fields=None)` ([`django_graphene_filters/permissions.py::apply_cascade_permissions`][upstream-permissions]) walks the model's single-column FK / OneToOne edges at call time, runs each target node's `get_queryset` against the target model's rows, and intersects `Q(<fk>__in=<visible>) | Q(<fk>__isnull=True)` into the caller's queryset — cycle-guarded by a `ContextVar` seen-set, pinned to the caller's DB alias, preserving nullable-FK rows. The cookbook line `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` is the entire consumer surface, and it is already the shape this package's own documentation promises: [`GOAL.md`][goal]'s astronomy showcase composes it in both node types, and the fakeshop products schema carries four commented copies of that exact line waiting for this card.

The card's parity claim makes this **Required graphene-django parity**: graphene_django's `DjangoObjectType.get_queryset` is applied to related-field resolution by `converter.py`'s `CustomField.wrap_resolve` (with `bypass_get_queryset` as the explicit per-resolver escape hatch) — a per-relation visibility contract that this card's cascade automates *across* the model graph. The package already ships the per-relation half (the optimizer's downgrade keeps target hooks effective under joins); the cascade is the missing graph-level half. It is also the gate for the rest of the roadmap: the `0.0.11` mutations cohort names composition with `apply_cascade_permissions` as a dependency (write mutations must not return rows the read side would hide), the `0.1.3` aggregation card mirrors the same pattern via [`get_child_queryset`][glossary-get_child_queryset], and the card body is blunt about the stakes: permissions/visibility is security-relevant and blocks the fakeshop real-usage story.

## Current state

A true description of the repo as of this writing (the plan is written against it):

- **`permissions.py` shipped in Slice 1.** As authored, no permissions module existed; [`docs/TREE.md`][tree]'s target layout reserves the flat top-level `permissions.py` for this card. Slice 1 has since landed the module — `apply_cascade_permissions` / `aapply_cascade_permissions` with the `ContextVar` cycle guard, single-column forward-FK / OneToOne scope, nullable-FK preservation, multi-DB alias pinning, loud `fields=` validation, and the package-root export — so `permissions.py` now exists and both symbols import from the package root, and Slice 4 has activated the four products-schema hooks that call it.
- **The per-type visibility hook and its cooperation surface are fully shipped.** [`types/base.py::DjangoType.get_queryset`][types-base] defaults to identity; `has_custom_get_queryset()` reports overrides (including through abstract bases) via the class-creation sentinel; the optimizer downgrades `select_related` → `Prefetch` when a relation target reports a custom hook ([`optimizer/walker.py::_target_has_custom_get_queryset`][walker]) and marks any plan that bakes a custom hook `cacheable = False`. A type whose hook *calls the cascade* is indistinguishable from any custom-hook type to all of this machinery — which is precisely why Slices 2–3 are pins, not features.
- **Every read pipeline already applies `get_queryset` at a single seam.** Root Relay refetch: the [`utils/querysets.py::apply_type_visibility_sync`][querysets] / `apply_type_visibility_async` helpers (which own the `SyncMisuseError` / await contract this card reuses), called from the `types/relay.py` node-refetch defaults. Connections: [`connection.py`][connection]'s sync and async pipelines call those same helpers before `filter:` / `orderBy:` apply. Root lists: [`list_field.py`][list-field]'s default resolver and consumer-resolver wrap. Filter branches: [`filters/sets.py`][filters-sets] derives child visibility querysets from each active [`RelatedFilter`][glossary-relatedfilter] branch's target hook. The cascade needs **no change at any of these seams** — it runs *inside* the consumer's hook, upstream of all of them.
- **The registry can answer the cascade's lookups.** [`registry.py::TypeRegistry.get`][registry] returns the registered type for a model honoring [`Meta.primary`][glossary-metaprimary] (the same lookup auto-synthesized relations resolve through); `iter_definitions()` (shipped `0.0.4`, named by the card) is the underlying registration-order surface. Both are post-finalization stable.
- **The async pattern is established.** [`filters/sets.py`][filters-sets] routes blocking filter work through `sync_to_async(thread_sensitive=True)`; [`SyncMisuseError`][glossary-syncmisuseerror] (multiple-inheriting [`ConfigurationError`][glossary-configurationerror] and `RuntimeError`) is raised by both shipped surfaces that can meet an async hook from a sync context, with the unawaited coroutine closed first.
- **The input-side permission gates are shipped and tested.** `FilterSet` / `OrderSet` `check_<field>_permission(self, request)` denial gates fire with active-input-only scope (plus active-branch double-dispatch for `RelatedOrder`); the fakeshop products app wires a real `check_name_permission` on `CategoryFilter` / `CategoryOrder` with live coverage. These gates are the subject of the card's fourth open question; [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) answers it.
- **The fakeshop activation site is live.** [`examples/fakeshop/apps/products/schema.py`][products-schema] carries the `apply_cascade_permissions` import and four `get_queryset` cascade hooks, one per type, and no `TODO-ALPHA-034-0.0.10` staging marker (the marker ids the hooks were staged behind were already correct; the staged body text encoded the contract this spec ships, save for one mechanical fix Slice 4 applied on activation: the user read changed from `getattr(info.context, "user", None)` to `getattr(getattr(info.context, "request", None), "user", None)` because the live `StrawberryDjangoContext` exposes no `.user` — see the [User-facing API](#user-facing-api) note, so the activation was an uncomment **plus** that uniform one-line correction, not a pure uncomment). All four products models carry `is_private`; the FK graph is the 2-deep `Entry → Item/Property → Category` chain the card's live-coverage DoD names; [`apps/products/services.py`][products-services]'s `create_users` provisions the staff / no-perm / per-`view_<model>` users the live tests must use (`create_users(1)` first line, per [`AGENTS.md`][agents]).
- **Glossary state.** [`apply_cascade_permissions`][glossary-apply_cascade_permissions] is `planned for 0.0.10` with the composition sentence this spec implements. [Per-field permission hooks][glossary-per-field-permission-hooks] is `planned for 0.0.10` but hosts its hooks on [`FieldSet`][glossary-fieldset] (`planned for 0.1.1`) — an internal contradiction the board resolves in `0.1.1`'s favor (the `fieldset/` package and its card live in the beta column; `fields_class` sits in `DEFERRED_META_KEYS` in [`types/base.py`][types-base]). [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) pins the resolution; Slice 5 corrects the entry.
- **The card's hard dependency is satisfied**: [`DONE-030-0.0.9`][kanban] (`DjangoConnectionField`) shipped, so the connection-composition DoD item is testable now. [`DONE-033-0.0.9`][kanban] is independent — the cascade composes with *whatever* the connection pipeline does at its `get_queryset` step, windowed or per-parent.

## Goals

1. **Ship the cascade.** `apply_cascade_permissions(cls, queryset, info, fields=None)` — one composable, registry-driven helper a consumer calls inside `get_queryset` to make every single-column FK / OneToOne edge respect its target type's visibility, with the four upstream invariants intact and tightened where upstream failed open: `ContextVar` cycle guard (a cycle fails closed with a path-rich [`ConfigurationError`][glossary-configurationerror] naming the edge path), single-column concrete forward scope, nullable-FK preservation, caller-alias pinning (Slice 1, [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection)).
2. **Ship both execution contexts.** The sync helper rejects async target hooks with [`SyncMisuseError`][glossary-syncmisuseerror]; `aapply_cascade_permissions` wraps the walk in `sync_to_async(thread_sensitive=True)` so async resolvers compose without blocking the event loop (Slice 1, [Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
3. **Keep cascaded relations N+1-safe with zero optimizer changes.** The shipped `get_queryset` → `Prefetch` downgrade, the `cacheable = False` custom-hook rule (it flips on the *presence* of a custom hook, not on whether the hook reads `info.context.user`), and strictness silence across cascaded traversals are pinned, and the cascade itself is proven by an absolute query count to add no query round-trips (Slice 2, [Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)).
4. **Answer the composition questions with pins, not new machinery.** The shipped `check_<field>_permission` filter/order gates survive unchanged and compose with the cascade in a fixed order (cascade narrows rows, gates judge input); connections, node refetch, and root lists all honor a cascading hook through their existing seams (Slice 3, [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) / [Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code)).
5. **Make the fakeshop real-usage story true.** The four products cascade hooks activate and are exercised live by real permission users (`create_users(1)`) across a 2-deep FK cascade with fixed query counts (Slice 4).
6. **Define the per-field permission surface without shipping it early.** The read-side field gate's home, signature, and failure modes are pinned here as the contract the `0.1.1` [`FieldSet`][glossary-fieldset] card implements; `Meta.fields_class` stays deferred per the end-to-end promotion rule (no slice, [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)).
7. **Keep composable rules visible from the owning type** (card scope): the cascade is declared inside the owning type's `get_queryset` — no global registry of permission rules, no schema-level configuration; reading a type's class body shows its entire row-visibility story.
8. **Keep package version state owned by the joint `0.0.10` cut**: no slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` (Slice 5, [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

## Non-goals

- **Per-field read gates (redaction / denial on field access).** Defined here as a contract ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)), implemented by the `0.1.1` [`FieldSet`][glossary-fieldset] card. `Meta.fields_class` stays in `DEFERRED_META_KEYS`; declaring it keeps raising [`ConfigurationError`][glossary-configurationerror].
- **M2M and reverse-relation cascade visibility.** The upstream cascade explicitly skips them (no single FK column to intersect on); this card preserves that scope and defers the extension whole — the many-side question ("hide the parent, or just narrow the related list?") has a different answer shape than the FK question and the related-list half is *already* solved per-relation by the shipped `Prefetch` downgrade. No follow-up card exists yet; surfaced for the maintainer at wrap time ([Risks and open questions](#risks-and-open-questions)).
- **Mutations composition.** The `0.0.11` cohort ([`DjangoMutation`][glossary-djangomutation] et al.) consumes the helper for post-write refetch visibility; nothing mutation-shaped lands here.
- **Aggregation cascade** ([`get_child_queryset`][glossary-get_child_queryset]) — `0.1.3`.
- **Object-level / guardian-style permission backends.** `strawberry-graphql-django` ships a `permissions.py` of field extensions plus a guardian integration; both are decorator-shaped and out of scope ([Borrowing posture](#borrowing-posture)).
- **A `bypass_get_queryset` escape hatch.** graphene-django's per-resolver bypass exists to *undo* its always-on related-field visibility; the package's cascade is opt-in per type, so the inverse escape hatch has no role. A consumer who wants one relation un-cascaded scopes with `fields=`.
- **Async-native cascade walking** (awaiting `async def` target hooks edge-by-edge). The async variant is `sync_to_async` around the sync walk per the card; async target hooks raise [`SyncMisuseError`][glossary-syncmisuseerror] from both variants in `0.0.10` ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async); the recourse is a sync hook, the same posture as the synthesized relation connections).
- **New settings keys.** No `DJANGO_STRAWBERRY_FRAMEWORK` entry is needed; the cascade is configured at the call site ([`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands").
- **A version bump.** Owned by the joint `0.0.10` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test, cascading visibility is **Required graphene-django-lineage parity with a strawberry-side gap**: the per-type `get_queryset` visibility contract on related fields is graphene_django core, and the cascade helper itself is the `django-graphene-filters` extension of it — the package's working feature-complete reference. `strawberry-graphql-django`'s per-field permission story is field-extension-shaped (the card tags it 🍓 parity-adjacent); nothing is borrowed from it here.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| graphene_django: `types.py::DjangoObjectType.get_queryset` applied to FK/O2O resolution by `converter.py::CustomField.wrap_resolve` (escape hatch: `utils/utils.py::bypass_get_queryset`) — per-relation visibility | shipped since `0.0.1`/`0.0.3`: the [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] + the optimizer's `Prefetch` downgrade keep target hooks effective under joins | shipped — pre-existing parity |
| django_graphene_filters: `permissions.py::apply_cascade_permissions` — graph-level cascade (ContextVar cycle guard, single-column scope, nullable preservation, alias pinning) | `permissions.py::apply_cascade_permissions` ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection)) | **this card (`0.0.10`) — required parity (helper-level; the consumer `view_<model>` branch intentionally diverges — see Decision 6)** |
| (no async variant upstream — graphene runs sync) | `aapply_cascade_permissions` via `sync_to_async` ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)) | this card — beyond parity, required by the package's dual-context resolver story |
| strawberry_django: `permissions.py` field extensions + `integrations/guardian.py` | — | 🍓 parity-adjacent (decorator-shaped; explicitly not borrowed) |
| django_graphene_filters: `FieldSet` per-field `check_<field>_permission` read gates | contract defined here ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)); implementation `0.1.1` | deferred to the [`FieldSet`][glossary-fieldset] card |

### From `django-graphene-filters` — borrow the contract and the invariants

The helper is ported at the contract level: same signature shape (`cls`, queryset, `info`, optional `fields=`), the same four invariant *axes* (a `ContextVar` cycle guard with `finally` reset; single-column forward scope; nullable-FK preservation via the `__isnull=True` disjunct; alias pinning via the caller's resolved DB), same recursion-by-composition model — the walk itself is depth-1, and *cascading* depth emerges because each target's `get_queryset` may itself call the helper, which is exactly what the traversal state guards ([`upstream permissions.py`][upstream-permissions] #"Cycle detection via context-var seen set").

Three of those four axes carry a package tightening where upstream's shape fails open on a security surface: the cycle guard **raises** instead of returning an un-narrowed queryset (a silently-broken cycle skips the re-entered type's outgoing visibility edges); the scope predicate is the forward-concrete `isinstance(field, models.ForeignKey)` test rather than a `related_model`-plus-`column` pair, so MTI parent links cascade and an uncomposable forward relation fails the walk closed rather than being skipped; and the `__isnull=True` disjunct composes only for a nullable edge, so a non-nullable edge emits the bare membership test. Alias pinning is ported unchanged and extended with an explicit cross-alias rejection ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)).

### Explicitly do not borrow

- **The graphene registry lookup.** Upstream resolves `registry.get_type_for_model(...)` against graphene's global registry; the package resolves through its own [`registry.py::TypeRegistry.get`][registry], which carries [`Meta.primary`][glossary-metaprimary] semantics graphene has no equivalent of.
- **The silent skip of an uncomposable forward relation.** Upstream's two-predicate scope test drops a `GenericForeignKey` or composite forward relation out of the walk without comment, so a row pointing at a hidden polymorphic target survives. The package classifies such an edge **unsupported**: a full walk over a model carrying one fails closed before any hook runs, and naming one in `fields=` fails at validation ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection)).
- **The silent `fields=` filter.** Upstream silently ignores a `fields=` name that matches nothing — a typo silently disables a security narrowing. The package raises [`ConfigurationError`][glossary-configurationerror] ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)).
- **`strawberry_django`'s permission field extensions** (`HasPerm`, `IsAuthenticated`, … applied per-field as Strawberry extensions) and the guardian integration — decorator-first surface, the explicit reason this package exists ([`AGENTS.md`][agents] #"DRF first strawberry second").

## User-facing API

Two new public symbols, no new `Meta` key, no constructor argument. The canonical consumer surface is the cookbook line, declared inside the owning type:

```python
from django_strawberry_framework import DjangoType, apply_cascade_permissions


class EntryType(DjangoType):
    class Meta:
        model = models.Entry
        fields = ("id", "value", "item", "property", "is_private")

    @classmethod
    def get_queryset(cls, queryset, info):
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

The request user is resolved through `info.context.request.user`, not `info.context.user`: the live `strawberry.django.context.StrawberryDjangoContext` is a dataclass exposing only `request` / `response` (no `.user`), so the package's canonical request resolution reads the user off the request — the same path `utils/permissions.py::request_from_info` and the shipped `FilterSet` / `OrderSet` `check_<field>_permission` gates take. A hook that reads `getattr(info.context, "user", None)` against the stock context binds `None` for every request, silently collapsing the staff / `view_<model>` branches to the anonymous public-only path — so the canonical consumer form resolves through `request`.

With `ItemType` / `PropertyType` / `CategoryType` declaring their own hooks, the one call makes `allEntries` (and every connection, node refetch, list field, and nested filter branch that resolves `EntryType`) drop rows whose `item` / `property` points at a row those types' hooks hide — and because each target's hook *also* cascades, visibility composes transitively (`Entry → Item → Category`) with the `ContextVar` traversal state failing a cycle closed.

Scoping to specific edges:

```python
return apply_cascade_permissions(cls, qs, info, fields=["item"])  # cascade item, leave property alone
```

Async resolvers use the `a`-prefixed twin:

```python
qs = await aapply_cascade_permissions(cls, qs, info)
```

### Error shapes

This is the helper's complete error inventory. Every entry is a fail-closed rejection: the cascade is a row-visibility predicate, so a shape it cannot compose correctly raises rather than composing something weaker.

**`fields=` validation** ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)) — all [`ConfigurationError`][glossary-configurationerror]:

- An **unknown or non-cascadable** name, naming the offending entry, the model, and the cascadable field set.
- A **bare string** (`fields="item"` instead of `fields=["item"]`), rejected up front — a string is itself an iterable of characters, so without the guard the walk would validate `'i'`, `'t'`, `'e'`, `'m'` as field names and emit a misleading "`'i'` is not cascadable" error; the guard rejects it with a message naming the non-string-iterable requirement instead.
- A **non-iterable** `fields=` (`fields=1`) or **non-string entries** (`fields=[1]`, `fields=[["item"]]`), naming the field-name-iterable contract rather than escaping as a raw `TypeError` from `set(...)`.
- A name matching an **unsupported forward relation** (`GenericForeignKey` / composite), which gets its own message pointing at the real backing FK (for a GFK, the `content_type` edge) rather than the generic not-cascadable one.

**Walk preconditions** — all [`ConfigurationError`][glossary-configurationerror], raised before any visibility hook runs:

- A **full walk** (`fields=None`) over a model carrying an unsupported forward relation: the walk can neither compose that edge nor safely skip it, so it preflights closed and names `fields=` as the recourse.
- A **root queryset** that is not a `QuerySet` over the type's concrete table, or whose query state cannot be sealed into a framework-owned execution queryset (a foreign `Query` class, a foreign row iterable, an unresolved deferred filter). A `.values()` root *is* supported input.
- A **sliced** root (`queryset[:N]`) or a **combined** root (`union()` / `intersection()` / `difference()`): the walk narrows by `.filter(...)`, which Django refuses on either shape — cascade first and slice after, or cascade each branch before combining.
- A **nested application on a different DB alias** from the root call's: a cascade cannot compose cross-database subqueries ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)).
- A **cycle**: re-entry into a type already on the traversal state's active tuple raises with the full edge path rendered (`AType.b -> BType.a -> AType`). An explicit zero-edge scope (`fields=[]`) is the one permitted re-entrant shape and the documented recourse for a recursive graph.

**Target-hook return contract** — all [`ConfigurationError`][glossary-configurationerror] ([Edge cases](#edge-cases-and-constraints)):

- A return that is not a `QuerySet` over the edge target's concrete table (a `Manager` is coerced through `.all()`; proxy and concrete siblings are compatible, unrelated models and MTI children are not), one whose query state cannot be sealed, or one **explicitly routed off the root alias** (an *unrouted* return is repinned onto it).
- A return that is **sliced**, **combined**, **grouped** (aggregate `annotate` / `values()` grouping), carries a field-specific **`distinct(...)`**, or carries an **`annotate(...)` / `extra(select=...)` alias shadowing the edge's target column** — each is a shape where the cascade's re-projection to the target column would change the query's semantics rather than only its selected column.

**Sync/async** ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)):

- A target type whose `get_queryset` returns an awaitable raises [`SyncMisuseError`][glossary-syncmisuseerror] (the awaitable disposed first — a coroutine closed, a future cancelled, so no `RuntimeWarning`) from **both** variants, since the async twin wraps the same sync walk. The message names the two recourses that work: make the target type's `get_queryset` sync, or pass `fields=` to skip the async-hooked edge.

**What never raises:**

- Hidden targets never raise and never leak existence: a row pointing at a hidden target and a row pointing at a deleted target are equally just *absent* from the result ([Decision 6](#decision-6--hidden-fk-semantics-row-exclusion-is-the-cascade-contract-resolver-level-nulling-stays-the-relation-contract)).
- An edge whose target model has no registered type is skipped silently — there is no visibility policy to apply. Naming such an edge in `fields=` is likewise accepted and contributes nothing.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/SPECS/spec-034-permissions-0_0_10.md`** (this document), with its `-terms.csv` and `-rationale.md` companions under `docs/SPECS/appx/`.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 1][rationale-d1].

### Decision 2 — Card-scope boundary: the cascade ships end-to-end; the per-field read gate is defined here and implemented with `FieldSet` (`0.1.1`)

This card ships `apply_cascade_permissions` / `aapply_cascade_permissions` end-to-end (implementation, optimizer pins, composition pins, live fakeshop activation). For **per-field permission hooks**, this card ships the *surface definition* — the following contract, recorded here and reflected into the glossary — and explicitly does **not** ship the implementation:

- **Host**: read-side per-field gates live on [`FieldSet`][glossary-fieldset], wired via [`Meta.fields_class`][glossary-metafields_class] — the `0.1.1` card's deliverable.
- **Signature**: `check_<field>_permission(self, info)` on the `FieldSet` (`info`-shaped — a *read* gate runs per resolved field with resolver info; the filter/order gates are `(self, request)`-shaped because they judge *input*).
- **Failure modes**: denial (raise `GraphQLError`, response carries an `errors` entry for that path) and redaction (safe-value fallback) — the two modes the glossary entry already names.
- **Composition rule with the cascade** (the card's DoD bullet, pinned now so `0.1.1` builds against it): a field-level gate does **not** short-circuit cascade visibility — the cascade narrows the queryset first, field gates run on whatever rows survive; a field denial therefore never leaks the existence of a cascade-hidden row (null fields and denials are indistinguishable from hidden rows only in that neither ever surfaces them).
- **Promotion rule**: `Meta.fields_class` stays in `DEFERRED_META_KEYS` ([`types/base.py`][types-base] #"aggregate_class") until `0.1.1` applies it end-to-end — the [Cross-subsystem invariants][glossary-cross-subsystem-invariants] rule and the card's own DoD line ("promote keys only when applied end-to-end").
- **Forward-reserved slot (no behavior)**: `DjangoTypeDefinition.fields_class` ([`types/definition.py`][definition]) is declared as an inert `type | None = None` sidecar slot — the structural mirror of the shipped `filterset_class` / `orderset_class` slots — so the `0.1.1` [`FieldSet`][glossary-fieldset] binding has a stable home to populate. It stays `None` and has **no populator** this card: `Meta.fields_class` remains rejected at validation (still in `DEFERRED_META_KEYS`), and `_bind_fieldsets` lands with `TODO-BETA-046-0.1.1`. Reserving the slot is the only `definition.py` change this card makes for per-field gates; it does not promote the key, ship a gate, or alter resolution.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 2][rationale-d2].

### Decision 3 — Module and test locations: flat `permissions.py` + `tests/test_permissions.py`

- **Source:** `django_strawberry_framework/permissions.py` — a flat top-level module, exactly the path [`docs/TREE.md`][tree]'s target layout reserves for this card. Contents: the two public functions, the module-level `ContextVar`, the private walk/validation helpers, and a redundant-alias re-export of [`SyncMisuseError`][glossary-syncmisuseerror] so the cascade's own error surface imports from this module without reaching into the private `utils` package (the name is already in the package-root `__all__` via `types`, so the re-export widens the module's import surface and not the package's). No new subpackage.
- **Tests:** new `tests/test_permissions.py` (the card DoD names it), mirroring the flat source module per the one-to-one rule; composition pins that belong to other surfaces' contracts extend those surfaces' existing files ([`tests/test_connection.py`][test-connection], [`tests/test_relay_node_field.py`][test-relay-node-field], [`tests/test_list_field.py`][test-list-field], [`tests/optimizer/test_extension.py`][test-opt-extension]); live coverage extends [`test_products_api.py`][test-products].

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 3][rationale-d3].

### Decision 4 — Public surface and naming: `apply_cascade_permissions` + `aapply_cascade_permissions`, exported from the package root

The sync helper keeps the upstream's exact name and signature — `apply_cascade_permissions(cls, queryset, info, fields=None)` — and the async variant is `aapply_cascade_permissions(cls, queryset, info, fields=None)`. Both are re-exported from `django_strawberry_framework/__init__.py` and join `__all__`.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 4][rationale-d4].

### Decision 5 — The cascade walk: call-time model-graph walk, registry primary lookup, every registered target composes, subquery intersection

Per call, the helper first **seals its root**, then walks `cls`'s model edges and intersects one visibility constraint per qualifying edge.

**Root sealing (before any step below).** The helper is called from inside a consumer-owned `get_queryset`, so its root argument is untrusted query state even when it claims to be a `QuerySet`. It is validated and **rebuilt** through the shared visibility boundary ([`utils/querysets.py`][querysets]'s source seal, with `require_model_rows=False` so a `.values()` root stays supported input) before any `.filter(...)` is dispatched: a consumer `QuerySet` subclass — or an instance-shadowed `filter` on an exact `QuerySet` — must not be able to erase the cascade predicate and hand an apparently-valid but unfiltered query back to the outer hook-result seal. The cascade therefore returns a framework-owned plain `QuerySet`, not the caller's object. Sliced and combined roots are rejected on the sealed source ([Error shapes](#error-shapes)).

1. **Edge scope** — `model._meta.get_fields()` entries satisfying `isinstance(field, models.ForeignKey)` AND `getattr(field, "column", None) is not None`: exactly the single-column concrete forward FK / forward OneToOne set. The `isinstance` test is the forward-concrete predicate and subsumes upstream's `related_model`-presence check — `OneToOneField` subclasses `ForeignKey`, while reverse FK / reverse OneToOne (`ForeignObjectRel`), M2M (join-table-backed), `GenericForeignKey` (virtual, polymorphic), `GenericRelation` (a `ForeignObject` but not a `ForeignKey`), and plain multi-column `ForeignObject` relations are all excluded by construction, not by enumeration. The `column`-value check guards the single-column contract against a future `ForeignKey` shape whose value is not one concrete column. **MTI parent links are in scope**: an MTI child's auto-generated `<parent>_ptr` `OneToOneField(parent_link=True)` is a real single-column concrete forward edge, and a child row whose MTI parent the parent type hides must drop with it ([Edge cases](#edge-cases-and-constraints)).
   A forward relation that is neither cascadable nor outside parent-row semantics — a `GenericForeignKey`, or a composite / multi-column `ForeignObject` — is **unsupported**, not skipped: it cannot be expressed as a one-column `__in` subquery, and silently skipping it would let a row pointing at a hidden target survive. A full walk over a model carrying one fails closed before any hook runs; naming one in `fields=` fails at validation; the GFK's *backing* `content_type` FK is an ordinary edge and may be selected explicitly.
2. **Target resolution** — [`registry.py::TypeRegistry.get`][registry]`(field.related_model)`: the primary-type lookup, the same one auto-synthesized relation fields resolve through. No registered type → edge skipped (an unexposed model has no GraphQL visibility contract to cascade). The card names `iter_definitions()` as the walk surface; `get(model)` is the keyed lookup over the same registration store — used because [`Meta.primary`][glossary-metaprimary] semantics (primary wins, secondaries never auto-resolve) must hold for cascade targets exactly as they hold for relation targets.
3. **Every registered target composes** — the walk runs each resolved target type's `get_queryset`, identity hooks included, and gates on nothing but registration. A hook gate keyed on `has_custom_get_queryset()` would look like a free optimization (an identity hook seems to narrow nothing) and is not one: a registered proxy type whose filtered `_default_manager` **is** its visibility policy declares no custom hook, so gating on the hook silently bypasses that policy. Registration is the visibility contract; only an edge whose target model has no registered type sits outside it.
4. **Constraint** — the per-edge hook invocation is delegated whole to [`utils/querysets.py::apply_type_visibility_sync`][querysets] over `related_model._default_manager.using(<root alias>).all()` (`_default_manager`, not `.objects`, so renamed default managers keep working — upstream's own note), which owns the sync-misuse contract ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)) and the hook result's shape / concrete-table / alias contract, rendered through the cascade's own per-edge error prose. The accepted return is then validated for SQL composability and **re-projected** to `.values(field.target_field.attname)`, so the membership test always binds the FK's actual target column — a consumer `.values(...)` / `.values_list(...)` projection is overridden rather than trusted, and a `ForeignKey(to_field=...)` edge compares its `to_field` column rather than a stray pk projection. The composed constraint is `Q(**{f"{field.name}__in": subquery})`, with `| Q(**{f"{field.name}__isnull": True})` added **only when `field.null`** — a non-nullable edge composes the bare membership test, which narrows the emitted SQL without changing the nullable-preservation invariant.
5. **Cycle guard** — a module-level `ContextVar` holding a frozen `_TraversalState` (root DB alias, active-type tuple, edge-path frames). Every root, edge, and nested application installs a **new** state object with a token and resets it in a `finally`, so state cannot leak across calls, tasks, threads, or exceptions (request isolation under WSGI and ASGI). Re-entry into a `cls` already on the active tuple **raises** a path-rich [`ConfigurationError`][glossary-configurationerror] rendering the edge path: returning the queryset un-narrowed instead would let a recursive graph skip the re-entered type's *outgoing* visibility edges, so a root row whose hidden relation was only reachable through the re-entry could survive. Recursive graphs are a consumer error; the recourse is `fields=` scoping on one participating hook, and an explicit zero-edge scope (`fields=[]`) is the one permitted re-entrant shape — it walks nothing and composes nothing, so the enclosing edge still binds the hook's direct narrowing. A frame carries only its own ancestry, so two sibling edges to one target both cascade. Recursion *depth* is not a walk property — the walk is depth-1, and transitive cascade emerges when target hooks themselves call the helper (the composition model upstream pins and the card's "composable permission rules" scope line demands).

Rationale companion — this Decision's justification and its four rejected alternatives: [Decision 5][rationale-d5].

### Decision 6 — Hidden-FK semantics: row exclusion is the cascade contract; resolver-level nulling stays the relation contract

When a parent row's FK points at a target row the target type's hook hides, the cascade **excludes the parent row** (the card's open question #1, first option). Nulling the FK field and sentinel values are rejected for the cascade.

- **No existence leak**: hidden-target and missing-target rows are equally absent; nothing distinguishes "you may not see this" from "this does not exist" — the same property the node refetch contract pins.
- **The layers stay independent**: a consumer who declines to cascade keeps today's per-relation behavior (hidden forward-FK target under the `Prefetch` downgrade surfaces as an unloadable relation at the field level, per the shipped [Relation handling][glossary-relation-handling] contract). The cascade is the tool that makes the *parent queryset* consistent up front.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 6][rationale-d6].

**Consumer-recipe divergence (cookbook `view_<model>`).** Parity is at the *helper*
level. The cookbook's consumer hooks (`recipes/schema.py::ObjectNode.get_queryset`
and siblings) keep the middle `has_perm("recipes.view_<model>")` branch as a bare
`queryset.filter(is_private=False)` and lean on the resolver-level sentinel
(`django_graphene_filters/object_type.py::AdvancedDjangoObjectType.get_node` /
`django_graphene_filters/object_type.py::AdvancedDjangoObjectType._make_sentinel`,
`is_redacted=True`) to mask a hidden non-null FK target without dropping the row.
This package deliberately did not port that sentinel tier. Its relation resolvers
re-check a forward FK through the target type's own visibility hook
([`django_strawberry_framework/types/resolvers.py::_visible_related_object`][resolvers],
reached whenever
[`types/resolvers.py::_custom_visibility_type`][resolvers] resolves a registered
target with a custom hook), so a hidden target resolves to `None` at the field —
and a **non-null** FK field cannot return `None` without a null violation
([Edge cases](#edge-cases-and-constraints)). Row exclusion at the cascade layer is
therefore the only honest answer for such an edge; there is no sentinel to fall
back on.
The fakeshop hooks therefore cascade in every non-staff branch, including
`view_<model>` (`examples/fakeshop/apps/products/schema.py::ItemType.get_queryset`
and siblings). Consequence: a `products.view_item` grant does not let
a user see an item whose `category` is hidden; the row drops, where upstream
`view_object` would keep the row and sentinel the FK. This is a taxonomy-consistent
choice, not a parity break: relation visibility is handled by row-narrowing, while
`TODO-BETA-046-0.1.1` codifies `FieldSet` as the field-level tier. There is no
node-sentinel tier; the sentinel is a deliberate non-goal, not a deferral.

### Decision 7 — Cascade performance: lazy subquery composition — zero added round-trips

The cascade composes unevaluated `__in` subqueries into the caller's queryset. Django compiles an unevaluated queryset inside `__in` as a nested `SELECT` in the **same** query — the cascade therefore adds zero round-trips per FK, and the card's open question #2 premise ("subquery-per-FK (one extra round-trip per FK in the cascade)") does not hold for this implementation: there is nothing to benchmark *against* single-pass annotation, because subquery composition already executes in a single pass. The benchmark gate dissolves; Slice 2 pins the property directly with query-count assertions (a cascaded 2-deep traversal executes in the same query count as its uncascaded shape).

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 7][rationale-d7].

### Decision 8 — Multi-DB pinning: `.using(queryset.db)` — the resolved alias, not `_db`

Every per-edge target subquery is built from `related_model._default_manager.using(queryset.db).all()` — `queryset.db`, the public resolved-alias property, not the private `_db` attribute the card's scope bullet names.

`queryset.db` resolves to `_db` when an explicit `.using(alias)` was applied **and falls back to router resolution when it was not**; `_db` is `None` in the routed case, and `.using(None)` would leave the target subquery to route *independently* — a router that routes the two models differently would then compose a cross-database `__in`, exactly the failure the pin exists to prevent.

This extends [Multi-database cooperation][glossary-multi-database-cooperation] axis 2 (explicit-alias preservation) to the cascade: a sharded caller's explicit `.using("shard_b")` propagates into the cascade subqueries of that **direct** call, because `queryset.db` reads the alias the caller resolved. The propagation is scoped to the queryset the helper is handed — see the Sharded-callers edge case for the one path (optimizer-built prefetch children) where the handed queryset carries its own per-model routed alias instead.

The root alias is then enforced rather than merely propagated, in both directions:

- A **nested** cascade application whose queryset runs on a different alias from the root call's fails closed with a [`ConfigurationError`][glossary-configurationerror] naming both aliases — a cascade cannot compose cross-database subqueries, and the check fires before the cycle check so a genuine cross-DB nesting is not masked by a cycle error.
- A **target hook return** explicitly routed off the root alias fails closed the same way, while an *unrouted* return is repinned onto the root alias by the shared visibility boundary. Composing a subquery the router would send elsewhere is precisely the failure this pin exists to prevent, so it raises rather than silently resolving.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 8][rationale-d8].

### Decision 9 — `fields=` scoping validates loudly with `ConfigurationError`

`fields=` accepts an iterable of model field names and scopes the walk to those edges. A bare string is rejected first, before any name lookup: `isinstance(fields, str)` raises [`ConfigurationError`][glossary-configurationerror] naming the non-string-iterable requirement — a string iterates as its characters, so `fields="item"` would otherwise validate `'i'`, `'t'`, `'e'`, `'m'` one by one and surface a misleading "`'i'` is not a cascadable field" message that hides the real mistake (the missing brackets). A non-iterable `fields=` and non-string entries are likewise rejected as [`ConfigurationError`][glossary-configurationerror] naming the field-name-iterable contract, rather than escaping as a raw `TypeError` from `set(...)`. Then every supplied name must be a cascadable edge (single-column concrete forward relation per [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection) step 1). A name matching an **unsupported forward relation** (`GenericForeignKey` / composite) raises a dedicated error naming the real backing FK as the recourse — a distinct mistake from naming a non-relation, and worth a distinct message; any other unknown name, scalar name, or known-but-non-cascadable name (M2M, reverse relation, `GenericRelation`) raises [`ConfigurationError`][glossary-configurationerror] naming the entry, the model, and the model's cascadable set. A name whose edge is cascadable but whose target model has no registered type is **accepted and skipped** (it scopes correctly; there is simply nothing to intersect — consistent with `fields=None` semantics over the same edge).

The check is a set comparison per call — negligible against the queryset work the call already does. It *is* technically redundant per request: a `fields=` argument at a call site is a compile-time constant and the model's cascadable set is stable post-finalize, so the validation result never changes across requests. The redundancy is bounded (a small set diff, no I/O) and would be absorbed for free by the per-`(model, fields)` edge-list memo recorded as the [Risks](#risks-and-open-questions) overhead fallback — called out here so it reads as a known, measured cost rather than an oversight.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 9][rationale-d9].

### Decision 10 — Sync/async contract: `SyncMisuseError` on async hooks from the sync walk; the async variant wraps the walk in `sync_to_async`

- **Sync helper**: each target-hook invocation is **delegated whole** to [`utils/querysets.py::apply_type_visibility_sync`][querysets], so the package has one place that runs a sync `get_queryset` and rejects an async one — a visibility-hook-routing mistake is a data-leak bug, and the routing is not re-decided per surface. The guard tests `inspect.isawaitable`, so any awaitable is rejected and disposed (a coroutine closed, a future cancelled) before [`SyncMisuseError`][glossary-syncmisuseerror] is raised. The message names the target type and the two recourses that work: make that target type's `get_queryset` sync, or pass `fields=` to skip the async-hooked edge. It does **not** point at `aapply_cascade_permissions`, which wraps this same sync walk and raises identically (see the third bullet). The cascade is the package's third sync surface with this contract (Relay node defaults; `FilterSet.apply` sync dispatch).
- **Async helper**: `aapply_cascade_permissions` runs the sync walk through [`utils/querysets.py::run_in_one_sync_boundary`][querysets], the package's shared `sync_to_async(thread_sensitive=True)` primitive — one walk implementation, one thread hop, and one owner of the boundary's semantics. The wrap exists for **blocking consumer-hook work**: queryset *composition* is lazy and cheap, but consumer hooks routinely call `user.has_perm(...)` / `user.is_authenticated` paths that read the permission tables — real I/O that must not run on the event loop. The `ContextVar` traversal state survives this async→sync boundary intact because `asgiref` copies the calling context into the worker thread (`contextvars.copy_context()` semantics) — so the walk both *sees* a clean state and *contains* its install/reset to the copied context, never leaking back into the event-loop task.
- **Consequence, documented**: an `async def` target hook raises `SyncMisuseError` from **both** variants in `0.0.10` (inside the wrapped thread there is still no awaiting context). The recourse is a sync hook on cascade-target types — the same posture the synthesized relation connections shipped with ([`Meta.relation_shapes`][glossary-metarelation_shapes]'s `SyncMisuseError` caveat), and the same escape hatch shape (narrow with `fields=` to skip the async-hooked edge). Async-native walking is a recorded follow-up ([Risks and open questions](#risks-and-open-questions)).

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 10][rationale-d10].

### Decision 11 — The existing `check_<field>_permission` filter/order gates survive unchanged

The card's open question #4, answered: the shipped [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] `check_<field>_permission(self, request)` denial gates keep their names, signatures, active-input-only scope, and semantics. No rename, no deprecation, no unified dispatcher. The three permission layers are distinct by *what they judge*:

| Layer | Host | Signature | Judges | Ships |
| --- | --- | --- | --- | --- |
| Row visibility (incl. cascade) | `DjangoType.get_queryset` | `(cls, queryset, info, **kwargs)` | which rows exist | shipped / this card |
| Input gates | `FilterSet` / `OrderSet` | `check_<field>_permission(self, request)` | whether *this request's input* may reference a field | shipped (`0.0.8`) |
| Read gates | [`FieldSet`][glossary-fieldset] | `check_<field>_permission(self, info)` | whether a resolved field's value may be read | `0.1.1` ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)) |

Composition order, pinned by Slice 3 tests: **cascade narrows first, gates judge input second** — every pipeline applies `get_queryset` (where the cascade lives) before `FilterSet.apply_*` / `OrderSet.apply_*` (where the gates live), so a gate denial is independent of row visibility and a gate that passes operates only on rows the cascade left visible. A denial therefore cannot leak hidden-row existence: the error fires on *input shape* alone, identically whether hidden rows exist or not.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 11][rationale-d11].

### Decision 12 — Connection / node / list composition is contract-pinning, not new code

The card's connection DoD ("a connection field whose wrapped type's `get_queryset` calls `apply_cascade_permissions` produces a Relay connection where every edge's nested relations respect the same cascade rule") is satisfied by the shipped seams, and Slice 3's job is to *pin* that, not to build it:

- [`DjangoConnectionField`][glossary-djangoconnectionfield]'s pipelines call [`utils/querysets.py::apply_type_visibility_sync`][querysets] / `apply_type_visibility_async` on the wrapped type before `filter:` / `orderBy:` / slicing — a cascading hook narrows the connection's row set, its `totalCount` (counted post-visibility), and its cursor space in one place.
- **Edges' nested relations** respect the *targets'* hooks via the optimizer's `Prefetch` downgrade (each nested target with a custom hook gets its visibility baked into the prefetch child queryset) — and when those targets' hooks also cascade, the cascade applies transitively. This is the composition sentence [`spec-033`][spec-033]'s Non-goals pre-pinned for this card. **Verified dependency to protect**: this transitivity works *only* because the prefetch child is built with the live request `info` — [`optimizer/walker.py::_build_child_queryset`][walker] #"queryset = field.related_model._default_manager.all()" builds the child from the target model's default manager and, when the target reports a custom hook, runs it through `apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)`, threading the *same* `info` from the root walk (the `allow_sliced=True` argument is the sealed-boundary concession a nested-connection child needs, per [`spec-045`][spec-045]). A future optimizer refactor that dropped `info` from that call would silently break cascade transitivity (the nested hook would have no `info.context.user`), so Slice 2's downgrade pin asserts the nested cascade narrows with the request user, not just that a `Prefetch` is planned.
- [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield] resolve through `resolve_node` / `resolve_nodes` defaults that apply `get_queryset` — a cascade-hidden row refetches as `null`, indistinguishable from missing (the no-existence-leak contract, now extended across FK edges).
- [`DjangoListField`][glossary-djangolistfield] applies the type's hook in its default resolver and around `Manager`/`QuerySet`-returning consumer resolvers.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 12][rationale-d12].

### Decision 13 — Version bumps are owned by the joint `0.0.10` cut

No slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. CHANGELOG bullets land under `[Unreleased]`. The `0.0.10` patch line is shared with [`TODO-ALPHA-035-0.0.10`][kanban] (optimizer robustness hardening); the version bump belongs to the **joint cut** that releases both cards. The exports pin in [`tests/base/test_init.py`][test-base-init] *does* grow in Slice 1 (two new `__all__` members) — exports are card-owned surface; the version constant is cut-owned.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 13][rationale-d13].

## Implementation plan

The card ships as **four functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; 1 is foundation, 2–3 build on 1, 4 builds on 1–3. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — cascade foundation | `django_strawberry_framework/permissions.py` (new), `django_strawberry_framework/__init__.py` (exports), [`tests/base/test_init.py`][test-base-init] (exports pin), `tests/test_permissions.py` (new) | ~19–23 (walk + invariants ×4 + `fields=` validation + `SyncMisuseError` + async variant + export pins + MTI / secondary-root / target-contract / empty-fields edge pins) | `+520 / -5` |
| 2 — optimizer cooperation + N+1 audit | no source change; `tests/test_permissions.py` + [`tests/optimizer/test_extension.py`][test-opt-extension] (extend) | ~6 (downgrade pin, `cacheable = False` pin, zero-extra-queries pin, strictness silence, FK-id-elision fallback pin, diff no-regression) | `+170 / -0` |
| 3 — composition pins | no source change; `tests/test_permissions.py`, [`tests/test_connection.py`][test-connection], [`tests/test_relay_node_field.py`][test-relay-node-field], [`tests/test_list_field.py`][test-list-field] (extend) | ~8 (gate-order composition ×2, connection narrow + `totalCount`, node/nodes `null`, list field narrow, transitive 2-deep, cycle A↔B live shape) | `+220 / -0` |
| 4 — products activation + live HTTP | [`products-schema`][products-schema] (uncomment the four hooks), [`test_products_api.py`][test-products] (extend) | ~6 live (anon / `view_item` / staff visibility matrix across `Entry → Item → Category`, query-count pin, filter+order+cascade composition) | `+190 / -40` |
| 5 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+110 / -50` |

Total expected delta: ~1,100 lines net-positive — consistent with the card's L sizing. No version-file edits ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

Staged-but-not-implemented seams follow the [`AGENTS.md`][agents] design-doc anchor discipline: a source-site `TODO(spec-034 Slice N)` comment naming this spec and the owning slice, paired with `NotImplementedError` where a call path must fail loudly, removed in the change that ships the slice. (Slice 1 ships the whole runtime surface, so no cross-slice seams are expected; the discipline applies if review splits a slice.)

## Edge cases and constraints

- **Nullable FK rows are preserved** — the `__isnull=True` disjunct keeps rows whose FK is `NULL`: a null reference points at no hidden target (card scope; dedicated invariant test).
- **Empty visible set** — a target hook that hides everything yields `fk__in (empty)`: every non-null-FK row drops, null-FK rows survive. No error, no existence leak.
- **Self-referential FK** (`parent = FK("self")`) — a type whose own cascading hook is reached through its self-edge is a recursive graph, and the walk **fails closed**: the nested application re-enters a type already on the active tuple and raises the path-rich cycle error. The recourse is `fields=` scoping on the participating hook — `fields=[]` on the self-edge's own application is the documented shape, and it still binds the hook's direct narrowing through the enclosing edge.
- **Mutual cascade A↔B** — `ItemType.get_queryset` cascades (touching `CategoryType`), `CategoryType.get_queryset` cascades back: the walk **fails closed** with the full path rendered (`ItemType.category -> CategoryType.<edge> -> ItemType`). Returning each direction's partial narrowing instead would skip the re-entered type's outgoing edges, so a row whose hidden relation was only reachable through the re-entry would survive. Pinned by a dedicated fixture, and by a longer cycle whose path string is asserted in full.
- **Frame-exit discard** — a frame carries only its own ancestry and unwinds on exit, so two sibling FK edges to the same target both cascade (the guard keys on *ancestry*, not *visit count*).
- **`ContextVar` isolation** — every root, edge, and nested frame installs a new immutable state with a token and resets it in `finally`, so a request-handler exception cannot leak stale traversal state into the next request sharing the context (upstream contract; pinned). Under the async variant this isolation holds because `asgiref`'s `sync_to_async` propagates a *copy* of the context into the worker thread, so the install/reset is scoped to that copy and never escapes to the event-loop task — verified behavior, pinned by `test_aapply_runs_walk_off_event_loop`.
- **Unregistered target model** — edge skipped: no `DjangoType`, no visibility contract. A model exposed *only* through a secondary type ([`Meta.primary`][glossary-metaprimary] semantics make the single registered type primary) cascades through that type.
- **Secondary types are never cascade targets** — `registry.get(model)` returns the primary; a stricter hook on a secondary type does not cascade (relation fields never auto-resolve to secondaries either — same rule, pinned and documented).
- **A secondary type *as the root* narrows transitive re-reaches through the primary.** A consumer can legally declare `get_queryset` (and call the cascade) on a *secondary* type, making it the walk root. If the transitive walk later re-reaches that same model through another edge, it resolves the target with `registry.get(model)` → the **primary**, so the re-reach narrows by the primary's hook, not the rooting secondary's. The cycle guard keys on the class object, so `secondary ≠ primary` on the active tuple and the primary joins it on its own first visit — a self-edge rooted on the secondary therefore terminates by raising the path-rich cycle error naming both types, not by silently un-narrowing. This is the intended "secondaries don't auto-resolve" semantics applied consistently — a model's transitive row-visibility is always its primary type's, regardless of which type rooted the call. Pinned by a fixture; documented so the asymmetry is not mistaken for a bug.
- **[`Meta.fields`][glossary-metafields]-excluded FK edges still cascade** — visibility is a row property, not a selection property: a hidden-target row is hidden even if the schema never exposes the FK field ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection); the rejected alternative of resolving targets through selection metadata instead is in the rationale companion under [Decision 5][rationale-d5]). `fields=` is the scoping tool for consumers who disagree per call site.
- **Non-nullable forward-FK target hidden → the parent row drops, not a nested `null`** — "every edge's nested relations respect the same cascade" ([Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code)) resolves two ways by FK shape. A **to-many** nested relation (`Category → items`) narrows its nested LIST when the target type's hook hides rows — an empty/narrowed list is well-formed. A **forward non-nullable FK** (`Item.category`, `null=False`) cannot null-resolve at the field: a non-null GraphQL field returning `None` is a null-violation, and `Meta.nullable_overrides` is scalar-only (spec-029 Decision 10), so the FK field cannot be forced nullable. The cascade's row-exclusion contract ([Decision 6](#decision-6--hidden-fk-semantics-row-exclusion-is-the-cascade-contract-resolver-level-nulling-stays-the-relation-contract)) is therefore the correct (and only honest) shape for such an edge — the **parent row drops** via its own cascade rather than the FK appearing to point at nothing. Slice 3's nested-transitivity pin exercises the to-many shape (`test_nested_relation_traversal_respects_target_cascade`); the parent-drop shape is exercised by the connection / node / list pins.
- **Composite-PK / composite-FK targets** (Django 5.2 `CompositePrimaryKey`) — a multi-column `ForeignObject` is not a `ForeignKey`, so it is never cascadable; unlike M2M it is also not outside parent-row semantics, so it is classified **unsupported** and preflights the whole walk closed rather than being skipped ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection) step 1).
- **`GenericForeignKey` / `GenericRelation`** — split by whether skipping them can hide a leak. A `GenericRelation` is a virtual one-to-many and is skipped like any reverse relation: it selects no parent row's single target. A `GenericForeignKey` *is* a forward relation selecting one target row, polymorphically, so it has no single visibility policy to compose and cannot be silently skipped either — it is **unsupported** and fails a full walk closed, while its backing `content_type` FK stays an ordinary selectable edge and `object_id` is a scalar that is never an edge ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection) step 1); consistent with the type system's GFK rejection posture.
- **Multi-table-inheritance parent link — cascades.** An MTI child model carries an auto-generated `<parent>_ptr` `OneToOneField(parent_link=True)`, which is a real single-column concrete forward edge and cascades like any other OneToOne: a child row whose MTI parent the parent type's hook hides is dropped. Excluding it would leave a hidden parent reachable through its child type, which is the leak the row-exclusion contract exists to close. No fakeshop model uses MTI, so this is asserted by a synthetic-graph pin plus row-level pins for the single-level, multi-level, and multiple-parent-link shapes, not by live coverage.
- **Cascade-target hook return contract.** The helper composes each target hook's return value as the right-hand side of an `__in` subquery (`Q(<fk>__in=target_qs)`) — a row-visibility predicate — so every return shape that would compare the wrong column **fails closed before composition** rather than being tolerated as a consumer bug. The shared visibility boundary owns the shape / concrete-table / alias contract (a `Manager` is coerced through `.all()`; an unrelated model or MTI-child queryset, an unsealable query state, and an explicitly off-alias return each raise). What is cascade-local is the SQL-composability battery around the re-projection: **sliced**, **combined**, **grouped**, field-**`distinct(...)`**, and **target-column-shadowing** (`annotate(...)` / `extra(select=...)`) returns each raise with their own message. Everything accepted is re-projected to `.values(field.target_field.attname)`, so a consumer `.values("name")` / `.values_list(...)` projection is overridden rather than trusted and a `ForeignKey(to_field=...)` edge compares its `to_field` column. The alias-shadow check is the security-critical one: Django blocks a bare `annotate(id=Value(pk))` but permits `values("x").annotate(id=Value(pk))`, which stays ungrouped and would otherwise re-project to the injected constant and let a row pointing at a hidden target survive. Re-projection is sound only where `.values(...)` changes the *selected column*; the rejected shapes are the ones where it would change the query's *semantics*. The contract is documented in the GLOSSARY body (Slice 5).
- **Abstract-base hooks** — a cascade target participates on registration alone, so a target whose hook lives on a shared abstract base participates exactly as one declaring its own does, and so does one declaring none at all ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection) step 3).
- **The helper narrows a sealed rebuild of the queryset it is handed** (root list, connection pre-slice, node refetch, filter child branch, a future mutation's post-write refetch). It never evaluates and never reorders, and its own composition is pure `.filter(...)`, so [`only()` projection][glossary-only-projection] and downstream ordering survive it. Three consequences follow from the seal and are contract, not accident: the return is a framework-owned plain `QuerySet` rather than a consumer `QuerySet` subclass; a **sliced** root is rejected (cascade first, slice after); and a **combined** root is rejected (cascade each branch before combining). A `.values()` root is supported input.
- **Plan-cache interaction** — a type whose hook cascades carries a custom `get_queryset`, and the shipped rule marks any plan baking a custom hook `cacheable = False` ([`optimizer/walker.py`][walker]'s coarser custom-hook rule — it flips on the *presence* of a custom hook, not on whether the hook reads `info.context.user`). The cascade adds no new cache key dimension; pinned in Slice 2.
- **FK-id elision interaction** — elision already falls back when a target hook must run ([FK-id elision][glossary-fk-id-elision] safety property); cascading targets therefore never elide. No change; pinned.
- **Strictness interaction** — the cascade composes SQL; it cannot lazy-load, so [Strictness mode][glossary-strictness-mode] `"raise"` stays silent across cascaded shapes. The Slice 2 silence pin detects an **optimizer-planning** regression in the composed shape (strictness reports unplanned *relation-resolver* accesses, so it fires when a cascaded relation stops being planned); the cascade's own no-round-trip property is pinned separately and directly by the absolute query count in `test_cascaded_traversal_adds_zero_queries`. The two are complementary and neither substitutes for the other. An *uncascaded* hidden-target traversal is unchanged from today.
- **Sharded callers — alias propagation is per-handed-queryset, not global.** On a **direct** call, `.using("shard_b")` on the caller propagates into the cascade subqueries via `queryset.db` ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)). But when the cascade runs inside an **optimizer-built prefetch child**, the queryset it receives is `field.related_model._default_manager.all()` ([`optimizer/walker.py::_build_child_queryset`][walker]), whose `.db` is that model's *router-resolved* alias — **not** the root request's explicit `.using("shard_b")`. So in the prefetch path the cascade pins to the prefetch child's own per-model routing, which is the correct behavior (each model routes itself) but means "the caller's alias reaches every subquery" holds only for the direct call. Sharded-specific live coverage stays behind `FAKESHOP_SHARDED` per [`AGENTS.md`][agents].
- **Re-entrancy / idempotence** — calling the helper twice on the same queryset double-applies the same filters (Django dedupes identical `Q` trees poorly but the result set is unchanged); harmless, documented, not guarded.
- **`fields=` accepted-and-skipped names** — a cascadable edge whose target model lacks a registered type validates fine and contributes nothing ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)); non-cascadable names and unsupported forward relations raise.
- **`fields=[]` (empty iterable) is a defined no-op, and the one permitted re-entrant shape** — an empty list/tuple validates clean (`set() - cascadable == ∅`) and the walk cascades nothing; it is **distinct from `fields=None`**, which cascades every qualifying edge. Unlike the bare-string case ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)), an empty iterable is well-formed and its meaning is unambiguous (zero edges), so it is *not* raised — it supports programmatically-built edge sets that legitimately resolve to empty. It carries a second role: because it walks nothing and composes nothing, a re-entrant application of it is provably non-recursive, so it is the **one shape exempt from the fail-closed cycle guard** and the documented recourse for a recursive graph ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection) step 5). Documented as a contract so a consumer who passes `[]` expecting "cascade all" learns the rule (they want `None`).

## Test plan

Tests live across the package-internal `tests/` tree and the `examples/fakeshop/test_query/` tree, per [`docs/TREE.md`][tree], [`AGENTS.md`][agents], and the coverage rule in [`examples/fakeshop/test_query/README.md`][test-query-readme]: any package coverage line reachable by a real GraphQL query against the fakeshop schema MUST be earned in `test_query/` — and most of `permissions.py`'s happy path is exactly that (it runs inside products `get_queryset` hooks during live queries). Package-only families carry their unreachability reason: the four invariant pins need synthetic graphs (cycles, sharded aliases, async hooks) the fakeshop schema doesn't carry; validation and misuse errors need direct calls; optimizer plan content is package-internal.

### Slice 1 — `tests/test_permissions.py` (new)

The card's four dedicated upstream-invariant pins, first:

- `test_mutual_cycle_fails_closed_with_path` — an A↔B mutual cascade raises the path-rich cycle error rather than terminating with a partial narrow, and the rendered path names every edge; `test_longer_cycle_renders_full_path` and `test_cyclic_diamond_fails_closed` extend it, and the autouse traversal-state fixture asserts the `ContextVar` is clean after every test (including on exception).
- `test_single_column_scope_skips_m2m_reverse_and_generic` — M2M, reverse FK, reverse OneToOne, and `GenericRelation` are all skipped; forward FK and forward OneToOne are cascaded. `test_gfk_default_walk_preflights_closed` and `test_gfk_explicit_selection_rejected_backing_fk_supported` pin the unsupported-forward-relation half (the preflight fires before any hook runs, so the walk emits no SQL).
- `test_mti_parent_link_edge_included` — a multi-table-inheritance child's `<parent>_ptr` `OneToOneField(parent_link=True)` *is* walked, so a child row whose MTI parent is hidden drops; `test_mti_single_level_parent_visibility_hides_child_rows`, `test_mti_multi_level_parent_links_cascade_transitively`, and `test_mti_multiple_parent_links_both_cascade` pin the row-level shapes. Synthetic MTI graph — no fakeshop model uses MTI.
- `test_multi_db_subquery_pinned_to_caller_alias` — a `.using("other")` caller produces cascade subqueries on `"other"` (asserted by observing the alias the walk hands the target hook, not by reconstructing a queryset); a router-divergent model pair stays single-DB. **Harness note**: the default package settings define only `"default"`; the second alias (`shard_b`) is `FAKESHOP_SHARDED`-gated in [`examples/fakeshop/config/settings.py`][fakeshop-settings], so this pin is *not* runnable under a bare `uv run pytest` and runs on the CI matrix's sharded axis instead. Borrow the in-test alias / router pattern established by [`tests/optimizer/test_multi_db.py`][test-opt-multi-db] rather than reinventing one or quietly skipping the pin; the pin itself lives beside the rest of the cascade's coverage in `tests/test_permissions.py`.
- `test_nested_application_off_root_alias_fails_closed` — a nested cascade application on an alias other than the root call's raises rather than composing a cross-database subquery.
- `test_nullable_fk_rows_preserved` — `NULL`-FK rows survive a cascade that hides every target row.

Then the remaining contract:

- `test_cascade_excludes_rows_with_hidden_targets` / `test_hidden_and_missing_targets_indistinguishable`.
- `test_transitive_cascade_two_deep` — `Entry → Item → Category` with hooks cascading at each level.
- `test_identity_hook_targets_compose_default_manager` — an identity-hook target still contributes its `_default_manager` subquery (SQL string assertion counting the composed `IN (SELECT` clauses); `test_proxy_target_filtered_default_manager_composes` pins the case that motivates it.
- `test_unregistered_target_model_skipped` / `test_secondary_type_never_cascade_target`.
- `test_secondary_root_self_edge_reaches_primary_then_fails_closed` — a cascade rooted on a *secondary* type re-reaching its own model through another edge narrows by the **primary** hook, and the walk terminates by raising the path-rich cycle error naming both types (the guard keys on the class).
- `test_hook_return_rejections_fail_closed` / `test_hook_values_and_values_list_projections_are_normalized` / `test_to_field_edge_compares_target_column` / `test_hook_manager_return_is_coerced` / `test_unpinned_hook_return_is_repinned_to_root_alias` — the hook-return battery: sliced / combined / grouped / field-`distinct` returns raise, a `Manager` is coerced, an unrouted return is repinned to the root alias, and every accepted return is re-projected to the edge's target column.
- `test_annotation_alias_shadow_cannot_bypass_visibility` / `test_annotation_alias_shadow_to_field_cannot_bypass_visibility` — the security-critical alias-shadow rejection, on both the pk and `to_field` edge shapes.
- `test_root_queryset_shape_rejections` / `test_values_root_is_supported_input` / `test_root_queryset_filter_override_is_neutralized_by_sealing` / `test_unsealable_root_query_class_fails_closed_with_cascade_prose` — the root seal: sliced and combined roots raise, a `.values()` root is accepted, a consumer-supplied `filter` override cannot erase the cascade predicate, and an unsealable query state raises in the cascade's own prose.
- `test_fields_scopes_walk` / `test_fields_unknown_name_raises` / `test_fields_non_cascadable_name_raises` / `test_fields_valid_but_unregistered_target_accepted` (messages name field, model, cascadable set).
- `test_fields_bare_string_raises` — `fields="item"` raises [`ConfigurationError`][glossary-configurationerror] from the `isinstance(fields, str)` guard (the message names the non-string-iterable requirement, not a per-character `'i'` lookup).
- `test_fields_empty_list_cascades_nothing` — `fields=[]` validates clean and cascades zero edges (a defined no-op, distinct from `fields=None` cascading all); no raise.
- `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` — coroutine closed (no `RuntimeWarning`), message names the type and both recourses.
- `test_aapply_runs_walk_off_event_loop` — the walk runs off the event loop, and the `ContextVar` seen-set installed inside the wrapped thread does not leak back into the calling async context (asgiref copies the context into the worker thread) — `test_aapply_async_target_hook_still_raises` (the documented [Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async) consequence).
- `test_self_referential_cascading_hook_fails_closed` — a self-edge into a cascading hook raises the path-rich cycle error; `test_self_referential_fields_scoping_breaks_recursion` pins the documented `fields=` recourse.
- Export pins in [`tests/base/test_init.py`][test-base-init]: both symbols importable from the package root and present in `__all__`.

### Slice 2 — `tests/test_permissions.py` + `tests/optimizer/test_extension.py` (extend)

- `test_cascaded_traversal_adds_zero_queries` — the cascaded 2-deep shape executes in the same query count as its uncascaded twin ([Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)'s proof).
- `test_cascading_target_downgrades_join_to_prefetch` — a relation whose target hook cascades plans a `Prefetch` (not `select_related`), with the cascade baked into the child queryset **using the live request user** (asserts the prefetch child narrows by `info.context.user`, not just that a `Prefetch` is planned — the [Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code) `_build_child_queryset(..., info)` dependency).
- `test_plan_with_cascading_hook_uncacheable` — `cacheable = False`; B1 hit/miss counters unaffected for non-cascading types.
- `test_fk_id_elision_falls_back_for_cascading_target` (re-affirmation of the shipped safety rule against the new hook shape).
- `test_strictness_raise_silent_across_cascaded_shape`.
- Queryset-diff no-regression: a consumer `select_related` on a cascading relation still reconciles per B8 (existing suites stay green).

### Slice 3 — `tests/test_permissions.py` + `tests/test_connection.py` + `tests/test_relay_node_field.py` + `tests/test_list_field.py` (extend)

- `test_cascade_then_filter_gate_composition` — a request whose filter input names a gated field is denied by `check_<field>_permission` regardless of cascade state; with passing input, filters operate on cascade-narrowed rows only (both shapes pinned, per the card DoD's "tests pin both shapes").
- `test_cascade_then_order_gate_composition` — same matrix for `OrderSet` gates.
- `test_gate_denial_no_existence_leak` — identical denial error with and without hidden rows present.
- `test_connection_over_cascading_type_narrows_edges_and_total_count` — [`DjangoConnectionField`][glossary-djangoconnectionfield] edges and `totalCount` reflect the cascade; cursors stay consistent.
- `test_node_refetch_of_cascade_hidden_row_returns_null` / `test_nodes_batch_holes_for_cascade_hidden_rows` — no existence leak through [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield].
- `test_list_field_default_resolver_applies_cascade`.
- `test_nested_relation_traversal_respects_target_cascade` — the connection-DoD sentence's "every edge's nested relations" half, via the `Prefetch` downgrade.

### Slice 4 — `examples/fakeshop/test_query/test_products_api.py` (extend; live)

First line of every new test: `services.create_users(1)` (and `seed_data(N)` where catalog rows are needed) per [`AGENTS.md`][agents] — real permission users, never mocked `info.context.user` (card DoD). Fixture note: the staff branch keys on `is_staff`, and [`services.create_users`][products-services] provisions each `staff_<n>` as **staff-not-superuser** (`is_staff=True` only — its docstring's "superuser" wording is inaccurate), so the staff-sees-everything assertions must not assume `is_superuser`.

- `test_cascade_anonymous_sees_no_entries_under_private_categories` — the 2-deep live pin: a private `Category` hides its `Item`s' `Entry`s from anonymous users even when the entries themselves are public.
- `test_cascade_view_item_user_respects_category_visibility` — the `view_item` user's `ItemType` branch cascades, so it sees only non-private items whose `category` is visible (items under a private category drop) and selecting the non-null `category { name }` resolves instead of raising `RelatedObjectDoesNotExist`.
- `test_cascade_view_entry_user_nested_selection_drops_hidden_targets` — a `view_entry` user selecting `item { name category { name } }` drops entries whose `item`/`property` target is hidden, with no resolver error.
- `test_cascade_staff_sees_everything` — parametrized over all four products root connection fields (`allCategories` / `allItems` / `allProperties` / `allEntries`), so each field is its own row: staff's page **is** the unfiltered page, pinned as an id **list** against the model's own rows in pk order truncated to the connection page cap. A count comparison is not enough — `Property` and `Entry` sit at the cap under this fixture volume, where `min(count, cap)` collapses to the cap constant and stops distinguishing the staff page from a narrowed one. Carries the asserted precondition that rows the cascade would hide exist, so the equality cannot pass vacuously.
- `test_cascade_staff_sees_private_rows_hidden_from_non_staff` — the differential half of the same four-field matrix: one private row is **in** staff's page and **absent** from both the anonymous page and the `view_<model>` page, with both non-staff pages asserted non-empty (an empty page satisfies every absence assertion and pins nothing) and the row asserted to fall inside the returned page (so a pagination miss cannot masquerade as a permission result). The subject is one row's membership, not a subset relation: at the seeded `Property` / `Entry` volume the three actors' pages are windows over different row sets, so `set(anonymous) < set(staff)` is not a sound invariant.
- `test_cascade_query_count_fixed` — the cascaded `allEntries { value item { name category { name } } }` shape executes in a fixed query count (cascade adds zero; optimizer plans the traversal).
- `test_cascade_composes_with_filter_and_order_live` — `filter:` + `orderBy:` + cascade in one request; the `check_name_permission` gates keep firing per their shipped live pins.
- Existing products live assertions are audited for private-fixture sensitivity; any that assumed un-cascaded visibility are re-pinned in the same change. **The re-pin is load-bearing, not incidental**: the seeders are not public-only — `seed_data` splits `Category` / `Property` `is_private` deterministically by index parity and draws `Item` / `Entry` privacy from a fixed-seed stream — so assertions that counted full sets or first-by-id rows churn once the hooks narrow to `is_private=False` plus cascade. Each at-risk assertion is re-pinned either to a staff client (where the test's subject is SQL-shape / optimizer / ordering mechanics, orthogonal to visibility) or to a post-cascade ORM-derived expectation (where the subject is root-field row content), and each carries an in-docstring note saying which, so a later reader can tell a re-pin from an original pin.

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 5's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 5 grants that permission**; the Slice 5 maintainer prompt must name the `CHANGELOG.md` edits explicitly so an agent does not infer permission from a standing document.

- **Slice 5 — GLOSSARY**
  - [`docs/GLOSSARY.md`][glossary]: flip [`apply_cascade_permissions`][glossary-apply_cascade_permissions] to `shipped (0.0.10)` and rewrite the body (the walk mechanism, the four invariants, `fields=` validation, the sync/async pair, the composition rule with gates and pipelines) — **correcting the current body's "FK / M2M" scope to forward-FK / OneToOne only, since M2M is out of scope** ([Non-goals](#non-goals)); re-status [Per-field permission hooks][glossary-per-field-permission-hooks] to `planned for 0.1.1` with a body note recording the [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) contract (host, signature, failure modes, cascade-composition rule); cross-reference the cascade from the [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] entry; update the Index rows and the Public exports list (two new symbols). **Net-new entries: none** — `aapply_cascade_permissions` is documented inside the existing [`apply_cascade_permissions`][glossary-apply_cascade_permissions] entry (one concept, two execution contexts; precedent: the `testing.relay` helpers share entries).
- **Slice 5 — package docs**
  - [`docs/README.md`][docs-readme]: the "Coming next" `0.0.10` line shrinks to the `035` remainder; the shipped-today list gains the permissions bullet.
  - [`docs/TREE.md`][tree]: `permissions.py` moves from "planned by TODO-ALPHA-034-0.0.10" to its real one-line description; `tests/test_permissions.py` joins the test tree.
  - [`TODAY.md`][today]: the products demonstration sections gain the activated cascade hooks (the "What products is still waiting for" list drops permissions and its stale `TODO-ALPHA-033-0.0.10` card id); the commented-hook caveat in the visibility section rewrites to the live shape.
  - [`README.md`][readme]: the status paragraph's newest-shipped-surface line gains the permissions subsystem; the "Coming next" roadmap line for `0.0.10` updates.
  - [`CHANGELOG.md`][changelog]: `### Added` bullets under `[Unreleased]` for `apply_cascade_permissions` / `aapply_cascade_permissions` and the products cascade activation. No version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).
  - [`GOAL.md`][goal] *(ratified at Slice-5 final verification — Worker 1)*: correct the cascade showcase's user read from the broken `getattr(info.context, "user", None)` (the stock `StrawberryDjangoContext` exposes no `.user`, so it binds `None` and silently collapses every staff/permission branch to anonymous) to the canonical `getattr(getattr(info.context, "request", None), "user", None)` form fixed centrally in Slice 4 ([User-facing API](#user-facing-api)). Three sites: the two showcase `get_queryset` bodies and the shared `_user(info)` helper (fixing the helper corrects all its call sites at once). **Rationale for the ratification:** GOAL.md sits outside this section's originally-named Slice-5 doc list, but the identical broken form was already in-scope for the GLOSSARY rewrite above; leaving the flagship permissions showcase factually wrong (its cascade hooks would bind `None` for every request) while correcting GLOSSARY would itself be the cross-surface inconsistency the build discipline forbids. Pure doc-accuracy, no contract change.
- **Slice 5 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`TODO-ALPHA-034-0.0.10`][kanban] to Done with the next `DONE-NNN-0.0.10` id; confirm the spec reference points at this spec file (a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`, not a hand edit); surface the unowned M2M / reverse-relation cascade follow-up to the maintainer for a new card ([Risks and open questions](#risks-and-open-questions)). No version-file edits.

## Risks and open questions

Every question this card opened is answered by a Decision above. The deliberation that answered them — each question's preferred answer for the cut, its fallback if implementation proved the preferred answer wrong, and the two card-premise corrections the cut chose to record rather than silently reconcile — is recorded in the rationale companion under [Risks and open questions][rationale-risks].

## Out of scope (explicitly tracked elsewhere)

- **`FieldSet` / `Meta.fields_class` / per-field read-gate implementation** — the `0.1.1` FieldSet card; the contract is pinned in [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011).
- **M2M / reverse-relation cascade visibility** — deferred whole; no card yet, surfaced for the maintainer at wrap time ([Risks and open questions](#risks-and-open-questions)).
- **Mutations composition with the cascade** — the `0.0.11` mutations cohort ([`DjangoMutation`][glossary-djangomutation] and its dependency note on this card); [Auth mutations][glossary-auth-mutations] likewise.
- **Aggregation cascade** — [`get_child_queryset`][glossary-get_child_queryset] / [`AggregateSet`][glossary-aggregateset], `0.1.3`.
- **[Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]** — [`DONE-033-0.0.9`][kanban], independent; the cascade composes through `get_queryset` regardless of how connections plan.
- **Optimizer robustness guards (G1–G3)** — [`DONE-035-0.0.10`][kanban], the joint-cut sibling.
- **Object-level permission backends (guardian-style) and per-field permission *extensions*** — strawberry_django's decorator-shaped surface; not on the roadmap (post-`1.0.0` differentiation would go through [`BACKLOG.md`][backlog]).
- **Version bump** — owned by the joint `0.0.10` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all four functional slices' items plus the wrap are satisfied. The card's own DoD bullets map onto items 1 (spec), 2–5 (helper + exports + invariants), 6–7 (optimizer / N+1), 8–9 (gate + connection composition), 10–11 (fakeshop live coverage), and 12–13 (docs + version boundary).

**Spec + companion CSV**

1. `docs/SPECS/spec-034-permissions-0_0_10.md` (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion `docs/SPECS/appx/spec-034-permissions-0_0_10-terms.csv` anchoring every project-specific term that has a [`docs/GLOSSARY.md`][glossary] heading; `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md` reports `OK: <N> terms`. The card introduces one net-new public symbol pair documented under the existing [`apply_cascade_permissions`][glossary-apply_cascade_permissions] entry, so no new glossary heading is required.

**Slice 1 — cascade foundation**

2. `django_strawberry_framework/permissions.py` ships `apply_cascade_permissions(cls, queryset, info, fields=None)` with the walk of [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection) (root sealing, single-column concrete forward scope with the unsupported-relation preflight, registry primary lookup, every registered target composing, validated-and-re-projected hook returns, `Q(__in)` intersection with the `Q(__isnull)` disjunct on nullable edges, `_default_manager`).
3. The four upstream invariants are each pinned by a dedicated test (card DoD): `ContextVar` cycle guard with `finally` reset and a fail-closed, path-rich cycle break; single-column concrete FK/O2O scope; multi-DB pinning to the caller's resolved alias ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)); nullable-FK preservation.
4. `fields=` validates loudly per [Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror); the sync helper raises [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed) for async target hooks; `aapply_cascade_permissions` runs the walk through `sync_to_async(thread_sensitive=True)` per [Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async).
5. Both symbols are exported from the package root (`from django_strawberry_framework import apply_cascade_permissions` works — card DoD), present in `__all__`, and pinned by the grown exports test in [`tests/base/test_init.py`][test-base-init].

**Slice 2 — optimizer cooperation + N+1 audit**

6. All permission-related ORM paths are checked for N+1 behavior (card DoD): the cascaded 2-deep shape adds zero query round-trips; a cascading relation target still downgrades to `Prefetch`; plans baking cascading hooks are `cacheable = False`; FK-id elision falls back; strictness `"raise"` stays silent across cascaded shapes.
7. No regression in the optimizer suites (B1–B8 plan-cache / queryset-diff coverage untouched and green).

**Slice 3 — composition pins**

8. The open question on gate composition is resolved and pinned (card DoD): the shipped `check_<field>_permission` filter/order gates survive unchanged ([Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged)); tests pin both shapes (denial on gated input regardless of cascade; gate-passing input operating on cascade-narrowed rows); a denial leaks no existence.
9. Cascade composes with [`DjangoConnectionField`][glossary-djangoconnectionfield] (card DoD): a connection over a cascading type narrows edges and `totalCount`, and every edge's nested relations respect the same cascade rule via the `Prefetch` downgrade; node refetch returns `null` for cascade-hidden rows; [`DjangoListField`][glossary-djangolistfield] narrows.

**Slice 4 — fakeshop activation + live coverage**

10. The four products cascade hooks are active (uncommented — their `TODO-ALPHA-034-0.0.10` markers are already correct), and live HTTP coverage in [`test_query/test_products_api.py`][test-products] exercises real fakeshop permission users via `services.create_users(1)` across the 2-deep `Entry → Item → Category` cascade — anonymous / per-`view_<model>` / staff matrix, with a fixed query-count pin (card DoD: real users, not mocked `info.context.user`).
11. The pre-existing products live suite stays green (re-pins only where a test seeded private fixtures).

**Slice 5 — doc + card-completion wrap**

12. [`docs/GLOSSARY.md`][glossary] flips [`apply_cascade_permissions`][glossary-apply_cascade_permissions] to shipped and re-statuses [Per-field permission hooks][glossary-per-field-permission-hooks] per [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011); [`docs/README.md`][docs-readme] / [`docs/TREE.md`][tree] / [`TODAY.md`][today] / [`README.md`][readme] reflect the shipped surface and the activated products hooks; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the bullets (the explicit per-card permission grant named in the Slice 5 maintainer prompt); [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.10` with the spec reference pointing at this file (kanban DB + re-render) and the M2M/reverse follow-up surfaced.
13. **No version bump lands in this card** per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut): `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.10` cut owns the bump).
14. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"No pytest after edits"; worker-local validation is `uv run ruff format .` and `uv run ruff check --fix .`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: ../GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangonodesfield]: ../GLOSSARY.md#djangonodesfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-get_child_queryset]: ../GLOSSARY.md#get_child_queryset
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-metaconnection]: ../GLOSSARY.md#metaconnection
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metafields_class]: ../GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metaoptimizer_hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-metarelation_shapes]: ../GLOSSARY.md#metarelation_shapes
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../GLOSSARY.md#relatedorder
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale-d10]: appx/spec-034-permissions-0_0_10-rationale.md#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async
[rationale-d11]: appx/spec-034-permissions-0_0_10-rationale.md#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged
[rationale-d12]: appx/spec-034-permissions-0_0_10-rationale.md#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code
[rationale-d13]: appx/spec-034-permissions-0_0_10-rationale.md#decision-13--version-bumps-are-owned-by-the-joint-0010-cut
[rationale-d1]: appx/spec-034-permissions-0_0_10-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-034-permissions-0_0_10-rationale.md#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011
[rationale-d3]: appx/spec-034-permissions-0_0_10-rationale.md#decision-3--module-and-test-locations-flat-permissionspy--teststest_permissionspy
[rationale-d4]: appx/spec-034-permissions-0_0_10-rationale.md#decision-4--public-surface-and-naming-apply_cascade_permissions--aapply_cascade_permissions-exported-from-the-package-root
[rationale-d5]: appx/spec-034-permissions-0_0_10-rationale.md#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection
[rationale-d6]: appx/spec-034-permissions-0_0_10-rationale.md#decision-6--hidden-fk-semantics-row-exclusion-is-the-cascade-contract-resolver-level-nulling-stays-the-relation-contract
[rationale-d7]: appx/spec-034-permissions-0_0_10-rationale.md#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips
[rationale-d8]: appx/spec-034-permissions-0_0_10-rationale.md#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db
[rationale-d9]: appx/spec-034-permissions-0_0_10-rationale.md#decision-9--fields-scoping-validates-loudly-with-configurationerror
[rationale-risks]: appx/spec-034-permissions-0_0_10-rationale.md#risks-and-open-questions
[spec-015]: spec-015-relay_interfaces-0_0_5.md
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-030]: spec-030-connection_field-0_0_9.md
[spec-033]: spec-033-connection_optimizer-0_0_9.md
[spec-034-rationale]: appx/spec-034-permissions-0_0_10-rationale.md
[spec-045]: spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[definition]: ../../django_strawberry_framework/types/definition.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[list-field]: ../../django_strawberry_framework/list_field.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py
[types-base]: ../../django_strawberry_framework/types/base.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-connection]: ../../tests/test_connection.py
[test-list-field]: ../../tests/test_list_field.py
[test-opt-extension]: ../../tests/optimizer/test_extension.py
[test-opt-multi-db]: ../../tests/optimizer/test_multi_db.py
[test-relay-node-field]: ../../tests/test_relay_node_field.py

<!-- examples/ -->
[fakeshop-settings]: ../../examples/fakeshop/config/settings.py
[products-schema]: ../../examples/fakeshop/apps/products/schema.py
[products-services]: ../../examples/fakeshop/apps/products/services.py
[test-products]: ../../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-permissions]: https://github.com/riodw/django-graphene-filters/blob/master/django_graphene_filters/permissions.py
