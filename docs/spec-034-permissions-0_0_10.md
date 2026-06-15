# Spec: Permissions subsystem — `apply_cascade_permissions` cascade visibility (sync + async), optimizer `Prefetch`-downgrade cooperation, permission-gate and connection composition, and the per-field permission surface decision

Planned for `0.0.10` (card [`TODO-ALPHA-034-0.0.10`][kanban]). **This spec is an open build plan, not a shipped record.** The card was directed to spec by the maintainer while [`WIP-ALPHA-033-0.0.9`][kanban] (connection-aware optimizer planning) remains in progress; the two cards are independent — this card touches no optimizer-walker seam, and the optimizer cooperation it needs (the [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] → `Prefetch` downgrade) shipped in `0.0.3` and is untouched by `033`. The [Slice checklist](#slice-checklist) below stays unticked as the contract record; the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)): this card shares the `0.0.10` patch line with [`TODO-ALPHA-035-0.0.10`][kanban] (optimizer robustness hardening); the `pyproject.toml` / `__version__` / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.10` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.10` line and never bump the version themselves (the on-disk version is still `0.0.8` at spec-authoring time; the `0.0.9` cut is also still pending on `033`).

Status: planned — no slice has started. Five slices: Slice 1 (the **cascade foundation** — `django_strawberry_framework/permissions.py` with the sync `apply_cascade_permissions(cls, queryset, info, fields=None)` and async `aapply_cascade_permissions(...)` pair, the `ContextVar` cycle guard, single-column forward-FK / OneToOne scope, nullable-FK preservation, multi-DB alias pinning, loud `fields=` validation, and the package-root export — [Decision 4](#decision-4--public-surface-and-naming-apply_cascade_permissions--aapply_cascade_permissions-exported-from-the-package-root) / [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection)), Slice 2 (**optimizer cooperation + N+1 audit** — pins that a cascading hook rides the shipped `Prefetch` downgrade, flips plans uncacheable, and adds zero query round-trips — [Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)), Slice 3 (**composition pins** — the shipped [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] `check_<field>_permission` gates survive unchanged and compose with the cascade ([Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged)); [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoListField`][glossary-djangolistfield] all honor a cascading hook through their existing `get_queryset` application points ([Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code))), Slice 4 (**fakeshop products activation + live HTTP coverage** — the four commented cascade hooks in the products schema activate, exercised by real permission users via `services.create_users(1)` across a 2-deep FK cascade), and Slice 5 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slice 1 is foundation-first; 2 and 3 build on 1; 4 builds on 1–3; 5 lands last.

Owner: package maintainer.

Predecessors: [`spec-033-connection_optimizer-0_0_9.md`][spec-033] (the most-recently-authored spec — the canonical voice / depth / section-layout reference for this document; its Non-goals explicitly hand the permissions subsystem here and pre-pin the composition seam: "*`apply_cascade_permissions` runs inside `get_queryset`, which both the pipeline and the windowed child queryset already honor*"); [`spec-030-connection_field-0_0_9.md`][spec-030] (the connection pipeline whose visibility → filter → order composition the cascade slots into at the `get_queryset` step); [`spec-027-filters-0_0_8.md`][spec-027] / [`spec-028-orders-0_0_8.md`][spec-028] (the shipped `check_<field>_permission` denial gates with active-input-only scope that [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) reconciles against the cascade, and the child-branch visibility derivation that already routes related querysets through target `get_queryset` hooks); [`spec-015-relay_interfaces-0_0_5.md`][spec-015] (the [`SyncMisuseError`][glossary-syncmisuseerror] sync/async hook contract this card's two variants inherit). [`docs/GLOSSARY.md`][glossary] carries [`apply_cascade_permissions`][glossary-apply_cascade_permissions] as `planned for 0.0.10`; Slice 5 flips it to `shipped (0.0.10)` and re-statuses [Per-field permission hooks][glossary-per-field-permission-hooks] per [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) (see [Doc updates](#doc-updates)).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`TODO-ALPHA-034-0.0.10`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-12), maintainer-directed at the To Do card while `033` remains WIP. Pinned: the canonical spec filename (the card's `docs/spec-permissions.md` name predates the structured convention); the **per-field-hooks scope boundary** ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)) resolving the card/glossary tension (read gates are hosted on [`FieldSet`][glossary-fieldset], a `0.1.1` deliverable; this card defines the surface and keeps `fields_class` deferred); the four upstream invariants ported verbatim (cycle guard, single-column scope, nullable preservation, alias pinning); two card-premise corrections recorded rather than silently reconciled — the subquery-per-FK "one extra round-trip per FK" premise (lazy `__in` subqueries compile into the caller's single query, [Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)) and the `.using(qs._db)` spelling (the resolved `queryset.db` property is the correct pin, [Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)); the loud `fields=` validation posture; the `SyncMisuseError` / `sync_to_async` async contract; the gates-survive-unchanged answer to the card's `check_permissions` open question; and the joint-cut version boundary shared with [`TODO-ALPHA-035-0.0.10`][kanban].
- **Revision 2** — accuracy pass from the pre-build review (`docs/feedback.md`, 2026-06-14), every finding verified against the live checkout before applying: **(H1)** the five `types/relay.py::_apply_get_queryset_sync` / `_apply_get_queryset_async` citations were repointed to their post-`0.0.9`-DRY home [`utils/querysets.py::apply_type_visibility_sync`][querysets] / `apply_type_visibility_async` (the old symbols exist nowhere in the package; `relay.py` only imports them), and the link reference was added; **(H2)** the "stale `TODO-ALPHA-027-0.0.10` marker" premise was corrected — the products-schema hooks already read the correct `TODO-ALPHA-034-0.0.10`, so Slice 4 only *uncomments*; only [`TODAY.md`][today]'s `TODO-ALPHA-033-0.0.10` is genuinely stale; **(M1/M2)** the pre-existing GLOSSARY "FK / M2M" scope error and the companion-CSV present-vs-future async-twin note were folded into Slice 5's GLOSSARY work and the [Risks](#risks-and-open-questions) ledger; **(L1)** the FieldSet card number was pinned to the live `TODO-BETA-046-0.1.1` (the card body's open question still quotes the older `044`); **(L2)** a Slice 4 fixture note records that `create_users` makes `staff_<n>` staff-not-superuser; **(L3)** the plan-cache cacheability reason was reworded from "reads `info.context.user`" to the coarser shipped rule (any custom `get_queryset` flips the plan uncacheable). No design change — all fixes are citation/accuracy tightenings.
- **Revision 3** — second pre-build review (`docs/feedback.md`, 2026-06-14): approval with three Low refinements, all verified. Folded in the one net-new item — a bare-string guard on `fields=` (`isinstance(fields, str)` rejected up front so `fields="item"` fails loudly rather than validating its characters), reflected in [Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror), the [Error shapes](#error-shapes), the Slice 1 checklist, and a dedicated `test_fields_bare_string_raises`. The other two findings needed no change: the per-model cascadable-field memo is already the recorded fallback in [Risks](#risks-and-open-questions) ("Cascade-call overhead on hot paths"), and the composite-PK skip is already cataloged in [Edge cases](#edge-cases-and-constraints).
- **Revision 4** — third pre-build review (`docs/feedback.md`, 2026-06-15): applied only the accurate refinement (L1) — a note in [Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async) and the [`ContextVar` isolation edge case](#edge-cases-and-constraints) that the async variant's request isolation holds because `asgiref` copies the calling context into the `sync_to_async` worker thread (verified empirically; `test_aapply_runs_walk_off_event_loop` extended to pin no-leak). Two findings were **declined after verification**: the "sliced target queryset raises `NotSupportedError`" claim (M1) is backwards — Django's `allow_sliced_subqueries_with_in` defaults to `True` (SQLite, the package's backend, and PostgreSQL both compile `IN (SELECT … LIMIT n)` fine; only MySQL sets it `False`), so there is no universal raise to document; the hardcoded upstream path (H1) is an established convention across the whole `docs/SPECS/` corpus, left unchanged here pending a maintainer decision on whether to repoint all specs to the public `github.com/riodw/django-graphene-filters` URL.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — this card. The entry's consumer example (`return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)`) is the canonical surface this spec ships; Slice 5 flips the status and expands the body with the walk mechanism and the four invariants.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — the per-type seam the cascade composes: the helper is *called from inside* a consumer's `get_queryset`, and the per-edge target visibility it intersects is each target type's own `get_queryset`. The entry's optimizer-cooperation paragraph (the `Prefetch` downgrade) is the mechanism Slice 2 pins across the cascade.
- [Per-field permission hooks][glossary-per-field-permission-hooks] — the read-side field gates. The entry currently says `planned for 0.0.10` while hosting the hooks on [`FieldSet`][glossary-fieldset] (`planned for 0.1.1`) — the contradiction [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) resolves; Slice 5 re-statuses the entry.
- [`FieldSet`][glossary-fieldset] / [`Meta.fields_class`][glossary-metafields_class] — the `0.1.1` host of the per-field read gates; `fields_class` stays in `DEFERRED_META_KEYS` through this card ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)).
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] / [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] / [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] — the shipped input-side subsystems whose `check_<field>_permission` denial gates (active-input-only scope) compose with — and are not replaced by — the cascade ([Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged)). The filter pipeline already derives child-branch visibility from target `get_queryset` hooks, so a cascading hook narrows nested filter branches automatically.
- [`DjangoType`][glossary-djangotype] / [`Meta.primary`][glossary-metaprimary] — the cascade resolves each FK edge's target type through the registry's primary-type lookup; secondary types are never cascade targets ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [Plan cache][glossary-plan-cache] / [Queryset diffing][glossary-queryset-diffing] — the cascade requires **no optimizer change**: a type whose hook cascades is just a type with a custom `get_queryset`, so the shipped downgrade-to-`Prefetch` and the request-scope `cacheable = False` rule both fire unchanged; Slice 2 pins both.
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

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the "first line of every catalog/auth test: `seed_data(N)` or `create_users(N)`" rule (Slice 4's live tests start with `create_users(1)` per the card DoD); the no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — Slice 5's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 4) and package-internal `tests/` where the path is unreachable from a live query.
- [`docs/TREE.md`][tree] — the target package layout already reserves `permissions.py # planned by TODO-ALPHA-034-0.0.10` at the package top level; tests mirror source one-to-one, so the flat module takes a flat `tests/test_permissions.py` ([Decision 3](#decision-3--module-and-test-locations-flat-permissionspy--teststest_permissionspy)).
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, defs at the bottom under the 10 canonical group headers); the "surface-wise we copy `django-graphene-filters`" rule — the cascade is exactly such a surface, ported at the contract level with the registry / typed-error / async adaptations the package's own architecture requires.

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices: four functional (1, then 2 and 3 on 1, 4 on 1–3) plus a doc + card-completion wrap (5).** Boxes are unticked because the work has not started.

- [ ] Slice 1: cascade foundation — `django_strawberry_framework/permissions.py` + package-root export (per [Decision 4](#decision-4--public-surface-and-naming-apply_cascade_permissions--aapply_cascade_permissions-exported-from-the-package-root) / [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection))
  - [ ] `permissions.py` ships `apply_cascade_permissions(cls, queryset, info, fields=None)`: a call-time walk of `cls`'s model single-column forward relations (`field.related_model` present AND `hasattr(field, "column")` — the upstream scope test, which excludes M2M, reverse FK, reverse OneToOne, `GenericForeignKey`, and `GenericRelation` precisely), resolving each edge's target type via the registry primary lookup ([`registry.py::TypeRegistry.get`][registry]), skipping targets without a custom hook (`has_custom_get_queryset()` is `False` — the identity default adds nothing), and intersecting `Q(<field>__in=<target visible pks>) | Q(<field>__isnull=True)` into the caller's queryset with the target subquery pinned to `queryset.db` ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)).
  - [ ] Cycle detection via a module-level `ContextVar` seen-set (the upstream `_cascade_seen` shape verbatim): re-entry on a type already in the set returns the partially-narrowed queryset without raising; the root call resets the var in a `finally` so request isolation holds under both WSGI and ASGI.
  - [ ] `fields=` validation: a bare string is rejected up front by an `isinstance(fields, str)` guard (so `fields="item"` fails loudly instead of validating its characters), and unknown names and known-but-non-cascadable names (M2M, reverse relations, virtual fields) raise [`ConfigurationError`][glossary-configurationerror] naming the field, the model, and the cascadable set ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)).
  - [ ] Sync misuse contract: a target hook returning a coroutine during the sync walk closes the coroutine and raises [`SyncMisuseError`][glossary-syncmisuseerror], reusing the probe shape of [`utils/querysets.py::apply_type_visibility_sync`][querysets] ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
  - [ ] `aapply_cascade_permissions(cls, queryset, info, fields=None)` wraps the sync walk in `sync_to_async(thread_sensitive=True)` (the [`filters/sets.py`][filters-sets] precedent) so blocking consumer-hook work (e.g. `user.has_perm(...)`'s permission-table reads) stays off the event loop ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
  - [ ] Both symbols export from the package root (`from django_strawberry_framework import apply_cascade_permissions` — the card DoD's import line) and join `__all__`; the public-exports pin in [`tests/base/test_init.py`][test-base-init] grows accordingly (the version pin in the same file is untouched, [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).
  - [ ] Package coverage: new `tests/test_permissions.py` per the [Test plan](#test-plan) — including the card's four dedicated upstream-invariant pins (cycle guard; single-column scope; alias pinning; nullable-FK preservation).
- [ ] Slice 2: optimizer cooperation + N+1 audit (per [Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips))
  - [ ] No optimizer source change. Pins: a relation whose target type's hook cascades still downgrades `select_related` → `Prefetch` (the type reports `has_custom_get_queryset() is True`, so [`optimizer/walker.py::_target_has_custom_get_queryset`][walker] fires the shipped rule); plans embedding a cascading hook are `cacheable = False` (the shipped rule marks **any** plan baking a custom `get_queryset` uncacheable — [`optimizer/walker.py::_target_has_custom_get_queryset`][walker] — regardless of whether the hook reads the request); the cascade itself adds **zero** query round-trips (the `__in` subqueries compile into the caller's single `SELECT`); a [Strictness mode][glossary-strictness-mode] `"raise"` run across a cascaded 2-deep traversal stays silent.
  - [ ] Package coverage: `tests/test_permissions.py` query-count and SQL-shape pins + [`tests/optimizer/test_extension.py`][test-opt-extension] downgrade/cacheability pins per the [Test plan](#test-plan).
- [ ] Slice 3: composition pins — gates, connections, nodes, lists (per [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) / [Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code))
  - [ ] No new code in `filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py`. Pins: composition order is **cascade narrows first, gates judge input second** — a `get_queryset` that cascades runs at the visibility step of every pipeline, then the active-input-only `check_<field>_permission` gates fire from `FilterSet.apply_*` / `OrderSet.apply_*` exactly as shipped; a field denial does not leak existence (denied-filter errors and hidden-row-empty results are produced by independent layers); a [`DjangoConnectionField`][glossary-djangoconnectionfield] over a cascading type narrows `edges` and `totalCount` together; [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield] refetch of a cascade-hidden row returns `null` with no existence leak; [`DjangoListField`][glossary-djangolistfield]'s default resolver narrows.
  - [ ] Package coverage: `tests/test_permissions.py` (composition fixtures) + [`tests/test_connection.py`][test-connection] / [`tests/test_relay_node_field.py`][test-relay-node-field] / [`tests/test_list_field.py`][test-list-field] additions per the [Test plan](#test-plan).
- [ ] Slice 4: fakeshop products activation + live HTTP coverage
  - [ ] [`examples/fakeshop/apps/products/schema.py`][products-schema]: the four commented cascade-permission `get_queryset` hooks (one per type, already correctly marked `TODO-ALPHA-034-0.0.10` — only the uncomment remains) activate: staff sees everything; a user with the matching `view_<model>` permission sees all non-private rows; everyone else gets `queryset.filter(is_private=False)` **plus** `apply_cascade_permissions(cls, ..., info)` so rows pointing at hidden targets drop out.
  - [ ] [`examples/fakeshop/test_query/test_products_api.py`][test-products]: live `/graphql/` coverage with **real permission users** — first line `services.create_users(1)` per [`AGENTS.md`][agents] (never hand-rolled users, card DoD) — across the products 2-deep FK chain (`Entry → Item → Category` / `Entry → Property → Category`): an anonymous request sees no entry whose item's category is private; the `view_item` user sees non-private items but still loses entries under private categories (the cascade composes per edge); staff sees everything; the per-request query count is pinned fixed (no per-row cascade queries).
  - [ ] Existing products live assertions that counted public-only rows keep passing — the activation must be observable only where private fixtures exist; the suite seeds the private/public split it needs through the established service helpers.
- [ ] Slice 5: doc updates + card-completion wrap (per [Doc updates](#doc-updates))
  - [ ] [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog] (the explicit permission grant), [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render). No version-file edits ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

## Problem statement

The package's row-level visibility story is per-type and stops at the type boundary. A consumer writes one [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] per [`DjangoType`][glossary-djangotype] — staff sees everything, others see `is_private=False` — and the shipped machinery honors it everywhere that *resolves that type*: root lists, connections, node refetch, relation traversal under the optimizer's `Prefetch` downgrade, nested filter branches. What nothing does today is make one type's visibility *reach through foreign keys into another type's rows*. An `Entry` whose `Item` is private is still a perfectly visible `Entry`: the entry row itself carries no `is_private` flag that knows about its parent, and `EntryType.get_queryset` has no vocabulary for "drop rows whose FK targets someone else's hook would hide". Every consumer that needs cascading visibility hand-writes the subqueries — per FK, per type, per app — exactly the kind of schema machinery the package exists to generate ([`GOAL.md`][goal] #"The project misses the goal if users must routinely hand-build the same schema machinery the package is supposed to generate").

The upstream reference solved this with a single composable helper. `django_graphene_filters`'s `apply_cascade_permissions(node_class, queryset, info, fields=None)` ([`/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/permissions.py::apply_cascade_permissions`][upstream-permissions]) walks the model's single-column FK / OneToOne edges at call time, runs each target node's `get_queryset` against the target model's rows, and intersects `Q(<fk>__in=<visible>) | Q(<fk>__isnull=True)` into the caller's queryset — cycle-guarded by a `ContextVar` seen-set, pinned to the caller's DB alias, preserving nullable-FK rows. The cookbook line `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` is the entire consumer surface, and it is already the shape this package's own documentation promises: [`GOAL.md`][goal]'s astronomy showcase composes it in both node types, and the fakeshop products schema carries four commented copies of that exact line waiting for this card.

The card's parity claim makes this **Required graphene-django parity**: graphene_django's `DjangoObjectType.get_queryset` is applied to related-field resolution by `converter.py`'s `CustomField.wrap_resolve` (with `bypass_get_queryset` as the explicit per-resolver escape hatch) — a per-relation visibility contract that this card's cascade automates *across* the model graph. The package already ships the per-relation half (the optimizer's downgrade keeps target hooks effective under joins); the cascade is the missing graph-level half. It is also the gate for the rest of the roadmap: the `0.0.11` mutations cohort names composition with `apply_cascade_permissions` as a dependency (write mutations must not return rows the read side would hide), the `0.1.3` aggregation card mirrors the same pattern via [`get_child_queryset`][glossary-get_child_queryset], and the card body is blunt about the stakes: permissions/visibility is security-relevant and blocks the fakeshop real-usage story.

## Current state

A true description of the repo as of this writing (the plan is written against it):

- **No `permissions.py` exists.** `django_strawberry_framework/` has no permissions module; [`docs/TREE.md`][tree]'s target layout reserves the flat top-level `permissions.py` for this card. Nothing imports or stubs the symbol; the four products-schema hooks that would call it are comments.
- **The per-type visibility hook and its cooperation surface are fully shipped.** [`types/base.py::DjangoType.get_queryset`][types-base] defaults to identity; `has_custom_get_queryset()` reports overrides (including through abstract bases) via the class-creation sentinel; the optimizer downgrades `select_related` → `Prefetch` when a relation target reports a custom hook ([`optimizer/walker.py::_target_has_custom_get_queryset`][walker]) and marks plans that bake request-scoped hooks `cacheable = False`. A type whose hook *calls the cascade* is indistinguishable from any custom-hook type to all of this machinery — which is precisely why Slices 2–3 are pins, not features.
- **Every read pipeline already applies `get_queryset` at a single seam.** Root Relay refetch: the [`utils/querysets.py::apply_type_visibility_sync`][querysets] / `apply_type_visibility_async` helpers (which own the `SyncMisuseError` / await contract this card reuses), called from the `types/relay.py` node-refetch defaults. Connections: [`connection.py`][connection]'s sync and async pipelines call those same helpers before `filter:` / `orderBy:` apply. Root lists: [`list_field.py`][list-field]'s default resolver and consumer-resolver wrap. Filter branches: [`filters/sets.py`][filters-sets] derives child visibility querysets from each active [`RelatedFilter`][glossary-relatedfilter] branch's target hook. The cascade needs **no change at any of these seams** — it runs *inside* the consumer's hook, upstream of all of them.
- **The registry can answer the cascade's lookups.** [`registry.py::TypeRegistry.get`][registry] returns the registered type for a model honoring [`Meta.primary`][glossary-metaprimary] (the same lookup auto-synthesized relations resolve through); `iter_definitions()` (shipped `0.0.4`, named by the card) is the underlying registration-order surface. Both are post-finalization stable.
- **The async pattern is established.** [`filters/sets.py`][filters-sets] routes blocking filter work through `sync_to_async(thread_sensitive=True)`; [`SyncMisuseError`][glossary-syncmisuseerror] (multiple-inheriting [`ConfigurationError`][glossary-configurationerror] and `RuntimeError`) is raised by both shipped surfaces that can meet an async hook from a sync context, with the unawaited coroutine closed first.
- **The input-side permission gates are shipped and tested.** `FilterSet` / `OrderSet` `check_<field>_permission(self, request)` denial gates fire with active-input-only scope (plus active-branch double-dispatch for `RelatedOrder`); the fakeshop products app wires a real `check_name_permission` on `CategoryFilter` / `CategoryOrder` with live coverage. These gates are the subject of the card's fourth open question; [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) answers it.
- **The fakeshop activation site is staged.** [`examples/fakeshop/apps/products/schema.py`][products-schema] carries a commented `apply_cascade_permissions` import and four commented `get_queryset` cascade hooks — one per type, each behind a `TODO-ALPHA-034-0.0.10` marker (the comment id is already correct; the body text is exactly the contract this spec ships). All four products models carry `is_private`; the FK graph is the 2-deep `Entry → Item/Property → Category` chain the card's live-coverage DoD names; [`apps/products/services.py`][products-services]'s `create_users` provisions the staff / no-perm / per-`view_<model>` users the live tests must use (`create_users(1)` first line, per [`AGENTS.md`][agents]).
- **Glossary state.** [`apply_cascade_permissions`][glossary-apply_cascade_permissions] is `planned for 0.0.10` with the composition sentence this spec implements. [Per-field permission hooks][glossary-per-field-permission-hooks] is `planned for 0.0.10` but hosts its hooks on [`FieldSet`][glossary-fieldset] (`planned for 0.1.1`) — an internal contradiction the board resolves in `0.1.1`'s favor (the `fieldset/` package and its card live in the beta column; `fields_class` sits in `DEFERRED_META_KEYS` in [`types/base.py`][types-base]). [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) pins the resolution; Slice 5 corrects the entry.
- **The card's hard dependency is satisfied**: [`DONE-030-0.0.9`][kanban] (`DjangoConnectionField`) shipped, so the connection-composition DoD item is testable now. [`WIP-ALPHA-033-0.0.9`][kanban] remains open but is independent — the cascade composes with *whatever* the connection pipeline does at its `get_queryset` step, windowed or per-parent.

## Goals

1. **Ship the cascade.** `apply_cascade_permissions(cls, queryset, info, fields=None)` — one composable, registry-driven helper a consumer calls inside `get_queryset` to make every single-column FK / OneToOne edge respect its target type's visibility, with the four upstream invariants intact: `ContextVar` cycle guard (partial-narrow on cycle break, never a raise), single-column forward scope, nullable-FK preservation, caller-alias pinning (Slice 1, [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection)).
2. **Ship both execution contexts.** The sync helper rejects async target hooks with [`SyncMisuseError`][glossary-syncmisuseerror]; `aapply_cascade_permissions` wraps the walk in `sync_to_async(thread_sensitive=True)` so async resolvers compose without blocking the event loop (Slice 1, [Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
3. **Keep cascaded relations N+1-safe with zero optimizer changes.** The shipped `get_queryset` → `Prefetch` downgrade, the `cacheable = False` request-scope rule, and strictness silence across cascaded traversals are pinned, and the cascade itself is proven to add no query round-trips (Slice 2, [Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)).
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
- **New settings keys.** No `DJANGO_STRAWBERRY_FRAMEWORK` entry is needed; the cascade is configured at the call site ([`AGENTS.md`][agents] #"Add settings keys only when the feature that needs them lands").
- **A version bump.** Owned by the joint `0.0.10` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test, cascading visibility is **Required graphene-django-lineage parity with a strawberry-side gap**: the per-type `get_queryset` visibility contract on related fields is graphene_django core, and the cascade helper itself is the `django-graphene-filters` extension of it — the package's working feature-complete reference. `strawberry-graphql-django`'s per-field permission story is field-extension-shaped (the card tags it 🍓 parity-adjacent); nothing is borrowed from it here.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| graphene_django: `types.py::DjangoObjectType.get_queryset` applied to FK/O2O resolution by `converter.py::CustomField.wrap_resolve` (escape hatch: `utils/utils.py::bypass_get_queryset`) — per-relation visibility | shipped since `0.0.1`/`0.0.3`: the [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] + the optimizer's `Prefetch` downgrade keep target hooks effective under joins | shipped — pre-existing parity |
| django_graphene_filters: `permissions.py::apply_cascade_permissions` — graph-level cascade (ContextVar cycle guard, single-column scope, nullable preservation, alias pinning) | `permissions.py::apply_cascade_permissions` ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection)) | **this card (`0.0.10`) — required parity** |
| (no async variant upstream — graphene runs sync) | `aapply_cascade_permissions` via `sync_to_async` ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)) | this card — beyond parity, required by the package's dual-context resolver story |
| strawberry_django: `permissions.py` field extensions + `integrations/guardian.py` | — | 🍓 parity-adjacent (decorator-shaped; explicitly not borrowed) |
| django_graphene_filters: `FieldSet` per-field `check_<field>_permission` read gates | contract defined here ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)); implementation `0.1.1` | deferred to the [`FieldSet`][glossary-fieldset] card |

### From `django-graphene-filters` — borrow the contract and the invariants

The helper is ported at the contract level: same signature shape (`cls`, queryset, `info`, optional `fields=`), same four invariants (cycle guard via `ContextVar` seen-set with `finally` reset; single-column scope via the `related_model`-plus-`column` test; nullable-FK preservation via the `__isnull=True` disjunct; alias pinning via the caller's resolved DB), same recursion-by-composition model — the walk itself is depth-1, and *cascading* depth emerges because each target's `get_queryset` may itself call the helper, which is exactly what the seen-set guards ([`upstream permissions.py`][upstream-permissions] #"Cycle detection via context-var seen set").

### Explicitly do not borrow

- **The graphene registry lookup.** Upstream resolves `registry.get_type_for_model(...)` against graphene's global registry; the package resolves through its own [`registry.py::TypeRegistry.get`][registry], which carries [`Meta.primary`][glossary-metaprimary] semantics graphene has no equivalent of.
- **The unconditional target call.** Upstream invokes every target's `get_queryset` — graphene's base class always defines one, so identity hooks generate dead `__in (SELECT …)` clauses. The package skips targets whose `has_custom_get_queryset()` is `False`: same semantics, no dead SQL ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection)).
- **The silent `fields=` filter.** Upstream silently ignores a `fields=` name that matches nothing — a typo silently disables a security narrowing. The package raises [`ConfigurationError`][glossary-configurationerror] ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)).
- **`strawberry_django`'s permission field extensions** (`HasPerm`, `IsAuthenticated`, … applied per-field as Strawberry extensions) and the guardian integration — decorator-first surface, the explicit reason this package exists ([`AGENTS.md`][agents] #"DRF first, strawberry second").

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
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

With `ItemType` / `PropertyType` / `CategoryType` declaring their own hooks, the one call makes `allEntries` (and every connection, node refetch, list field, and nested filter branch that resolves `EntryType`) drop rows whose `item` / `property` points at a row those types' hooks hide — and because each target's hook *also* cascades, visibility composes transitively (`Entry → Item → Category`) with the `ContextVar` seen-set breaking cycles.

Scoping to specific edges:

```python
return apply_cascade_permissions(cls, qs, info, fields=["item"])  # cascade item, leave property alone
```

Async resolvers use the `a`-prefixed twin:

```python
qs = await aapply_cascade_permissions(cls, qs, info)
```

### Error shapes

- `fields=` naming an unknown or non-cascadable field raises [`ConfigurationError`][glossary-configurationerror] naming the offending entry, the model, and the cascadable field set ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)).
- `fields=` passed a **bare string** (`fields="item"` instead of `fields=["item"]`) raises [`ConfigurationError`][glossary-configurationerror] up front — a string is itself an iterable of characters, so without the guard the walk would validate `'i'`, `'t'`, `'e'`, `'m'` as field names and emit a misleading "`'i'` is not cascadable" error; the guard rejects it with a message naming the non-string-iterable requirement instead ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)).
- A target type whose `get_queryset` is `async def` reached from the **sync** helper raises [`SyncMisuseError`][glossary-syncmisuseerror] (coroutine closed first, no `RuntimeWarning`), pointing the consumer at `aapply_cascade_permissions` or a sync hook rewrite — the same message discipline as the Relay node defaults ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
- Cycles never raise: re-entry returns the partially-narrowed queryset (the upstream contract, card scope).
- Hidden targets never raise and never leak existence: a row pointing at a hidden target and a row pointing at a deleted target are equally just *absent* from the result ([Decision 6](#decision-6--hidden-fk-semantics-row-exclusion-is-the-cascade-contract-resolver-level-nulling-stays-the-relation-contract)).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-034-permissions-0_0_10.md`** (this document).

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `TODO-ALPHA-034-0.0.10`, so `<NNN>` is `034` and `<0_0_X>` is `0_0_10`.
- The topic slug is `permissions` — the card's own suggested filename stem (`docs/spec-permissions.md`), kept because it names the subsystem precisely.

Alternatives considered (and rejected):

- **The card's own `docs/spec-permissions.md`.** Rejected: predates the structured-filename convention; [`spec-033`][spec-033] Decision 1 (and `spec-032` before it) set the precedent of preferring the convention and recording the card's older name.
- **Topic slug `cascade_permissions`.** Rejected: the card is the *permissions subsystem* card — the cascade is its centerpiece but the spec also pins the per-field surface decision and the gate composition; the broader slug matches the card title.

### Decision 2 — Card-scope boundary: the cascade ships end-to-end; the per-field read gate is defined here and implemented with `FieldSet` (`0.1.1`)

This card ships `apply_cascade_permissions` / `aapply_cascade_permissions` end-to-end (implementation, optimizer pins, composition pins, live fakeshop activation). For **per-field permission hooks**, this card ships the *surface definition* — the following contract, recorded here and reflected into the glossary — and explicitly does **not** ship the implementation:

- **Host**: read-side per-field gates live on [`FieldSet`][glossary-fieldset], wired via [`Meta.fields_class`][glossary-metafields_class] — the `0.1.1` card's deliverable.
- **Signature**: `check_<field>_permission(self, info)` on the `FieldSet` (`info`-shaped — a *read* gate runs per resolved field with resolver info; the filter/order gates are `(self, request)`-shaped because they judge *input*).
- **Failure modes**: denial (raise `GraphQLError`, response carries an `errors` entry for that path) and redaction (safe-value fallback) — the two modes the glossary entry already names.
- **Composition rule with the cascade** (the card's DoD bullet, pinned now so `0.1.1` builds against it): a field-level gate does **not** short-circuit cascade visibility — the cascade narrows the queryset first, field gates run on whatever rows survive; a field denial therefore never leaks the existence of a cascade-hidden row (null fields and denials are indistinguishable from hidden rows only in that neither ever surfaces them).
- **Promotion rule**: `Meta.fields_class` stays in `DEFERRED_META_KEYS` ([`types/base.py`][types-base] #"aggregate_class") until `0.1.1` applies it end-to-end — the [Cross-subsystem invariants][glossary-cross-subsystem-invariants] rule and the card's own DoD line ("promote keys only when applied end-to-end").

Justification:

- **The card resolves its own tension.** The card's scope line names "per-field permission hooks declared via `Meta`", but its open question #4 locates the read gate at "`FieldSet.check_<field>_permission(info)`" under the beta FieldSet card ([`TODO-BETA-046-0.1.1`][kanban]; the card body's open question still quotes the older `044`, but the live kanban card is `046`) — the card itself files the implementation under that card. The board agrees: `fieldset/` is a `0.1.1` planned path in [`docs/TREE.md`][tree], the [`FieldSet`][glossary-fieldset] glossary entry is `planned for 0.1.1`, and `fields_class` sits in `DEFERRED_META_KEYS` today. The only artifact claiming `0.0.10` for the hooks is the [Per-field permission hooks][glossary-per-field-permission-hooks] glossary status tag — which contradicts its own body (it hosts the hooks on a `0.1.1` class). Per the [`docs/SPECS/NEXT.md`][next] boundary rule the card is preferred and the conflict is recorded ([Risks and open questions](#risks-and-open-questions)); Slice 5 re-statuses the glossary entry to `planned for 0.1.1`.
- **The DoD line is satisfiable under this reading and only this reading.** "Define the `Meta` surface for per-field permissions and promote keys only when applied end-to-end" — *define* (this Decision) and *don't promote early* (the invariant). Shipping gate code in `0.0.10` without `FieldSet` would require inventing a second, interim host that `0.1.1` would immediately supersede.

Alternatives considered (and rejected):

- **Ship type-level `check_<field>_permission` classmethods on `DjangoType` now, migrate to `FieldSet` later.** Rejected: creates a soon-to-be-superseded public surface with a migration burden the package would own forever; the upstream cookbook hosts read gates on `FieldSet` (the [`GOAL.md`][goal] astronomy showcase shows exactly that split), and `START.md`'s scope-creep rule says don't quietly mix in extras that bloat the slice.
- **Pull the whole `FieldSet` forward into `0.0.10`.** Rejected: `FieldSet` is an L-sized subsystem of its own (computed fields, resolver overrides, redaction machinery); the board sequenced it post-alpha deliberately, and this card is already L.
- **Ship nothing and strike the bullet.** Rejected: the card demands the surface be *defined* before the implementation pass; leaving it undefined re-opens the design in `0.1.1` with no record of the cascade-composition rule the DoD pins.

### Decision 3 — Module and test locations: flat `permissions.py` + `tests/test_permissions.py`

- **Source:** `django_strawberry_framework/permissions.py` — a flat top-level module, exactly the path [`docs/TREE.md`][tree]'s target layout reserves for this card. Contents: the two public functions, the module-level `ContextVar`, and the private walk/validation helpers. No new subpackage.
- **Tests:** new `tests/test_permissions.py` (the card DoD names it), mirroring the flat source module per the one-to-one rule; composition pins that belong to other surfaces' contracts extend those surfaces' existing files ([`tests/test_connection.py`][test-connection], [`tests/test_relay_node_field.py`][test-relay-node-field], [`tests/test_list_field.py`][test-list-field], [`tests/optimizer/test_extension.py`][test-opt-extension]); live coverage extends [`test_products_api.py`][test-products].

Justification: the card says "`django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows" — the `0.0.10` surface is two functions and a `ContextVar`; a package is structure without content. The upstream's own `permissions.py` is a flat module. When `0.1.1` adds the FieldSet read gates the *fieldset* package grows, not this module.

Alternatives considered (and rejected): **`permissions/` package now, anticipating growth.** Rejected: the same speculative-structure mistake [`START.md`][start] records for `conf.py` pre-population ("add a settings key only when the feature that needs it lands" generalizes); renames later are cheap (`git mv` + import sweep) and may never be needed.

### Decision 4 — Public surface and naming: `apply_cascade_permissions` + `aapply_cascade_permissions`, exported from the package root

The sync helper keeps the upstream's exact name and signature — `apply_cascade_permissions(cls, queryset, info, fields=None)` — and the async variant is `aapply_cascade_permissions(cls, queryset, info, fields=None)`. Both are re-exported from `django_strawberry_framework/__init__.py` and join `__all__`.

Justification:

- **Name parity is migration surface.** The card's DoD pins the import line (`from django_strawberry_framework import apply_cascade_permissions`); [`GOAL.md`][goal]'s showcase, the glossary entry, and the products schema comments all already use the name. A `django-graphene-filters` migrant's `get_queryset` body moves verbatim.
- **The `a`-prefix follows the asgiref/Django convention** (`aget`, `acount`, `aupdate_or_create`) that the package's own planned surfaces already adopt (the [`AggregateSet`][glossary-aggregateset] entry names `compute` / `acompute`). The `apply_sync` / `apply_async` suffix pair is the *set-family classmethod* convention ([`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset]) — a different namespace with a paired-verb shape; a module-level function follows the Django convention.
- **Package-root export** matches the card DoD and the symbol's audience (every consumer writing a `get_queryset`), parallel to [`finalize_django_types`][glossary-finalize_django_types].

Alternatives considered (and rejected):

- **`apply_cascade_permissions_async`.** Rejected: no precedent in the package or Django; verbose without adding clarity.
- **A single function with an `async_=` flag or auto-detection.** Rejected: callers must know whether to `await`; a dual-mode return type (queryset or coroutine) is the exact ambiguity [`SyncMisuseError`][glossary-syncmisuseerror] exists to kill.
- **Exporting from a `django_strawberry_framework.permissions` namespace only.** Rejected: the card DoD names the root import; subsystem-namespace imports (`from django_strawberry_framework.filters import FilterSet`) are for *family* surfaces, while this is a single helper used inside `DjangoType` bodies alongside root-exported symbols.

### Decision 5 — The cascade walk: call-time model-graph walk, registry primary lookup, `has_custom_get_queryset()` gate, subquery intersection

Per call, the helper walks `cls`'s model edges and intersects one visibility constraint per qualifying edge:

1. **Edge scope** — `model._meta.get_fields()` entries with `related_model` present AND `hasattr(field, "column")`: exactly the single-column forward FK / forward OneToOne set (the upstream test, ported verbatim). M2M (join-table-backed, no `column`), reverse FK / reverse OneToOne (`ForeignObjectRel`, no `column`), `GenericForeignKey` (`related_model` absent), and `GenericRelation` (virtual, no `column`) are all excluded by construction, not by enumeration.
2. **Target resolution** — [`registry.py::TypeRegistry.get`][registry]`(field.related_model)`: the primary-type lookup, the same one auto-synthesized relation fields resolve through. No registered type → edge skipped (an unexposed model has no GraphQL visibility contract to cascade). The card names `iter_definitions()` as the walk surface; `get(model)` is the keyed lookup over the same registration store — used because [`Meta.primary`][glossary-metaprimary] semantics (primary wins, secondaries never auto-resolve) must hold for cascade targets exactly as they hold for relation targets.
3. **Hook gate** — target type's `has_custom_get_queryset()` must be `True`; the identity default contributes nothing, so the edge is skipped with zero SQL emitted (the dead-`__in` clause upstream tolerates).
4. **Constraint** — `target_qs = TargetType.get_queryset(related_model._default_manager.using(queryset.db).all(), info)` (sync-misuse-probed per [Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)), then `queryset = queryset.filter(Q(**{f"{field.name}__in": target_qs}) | Q(**{f"{field.name}__isnull": True}))`. `_default_manager`, not `.objects`, so renamed default managers keep working (upstream's own note).
5. **Cycle guard** — a module-level `ContextVar[set | None]` seen-set: root call installs and clears it in `finally` (request isolation under WSGI and ASGI); re-entry on a `cls` already in the set returns the queryset unchanged (partial narrow, never a raise); each frame discards its own class on exit so siblings re-visit legally. Recursion *depth* is not a walk property — the walk is depth-1, and transitive cascade emerges when target hooks themselves call the helper (the composition model upstream pins and the card's "composable permission rules" scope line demands).

Justification: this is the upstream mechanism with the package's own registry and hook vocabulary substituted — every deviation (primary lookup, custom-hook gate) tightens semantics without changing the contract; everything load-bearing (scope test, Q-shape, manager choice, guard lifecycle) is ported verbatim because it is the proven, cookbook-documented behavior the card requires.

Alternatives considered (and rejected):

- **Walking `registry.iter_definitions()` and matching definitions back to the model's fields.** Rejected: inverts the lookup direction for no gain — the model's `_meta.get_fields()` is the authoritative edge list, and the keyed `get(model)` is O(1) per edge over the same store the card's named surface iterates.
- **Resolving targets through each definition's relation metadata instead of `model._meta`.** Rejected: the cascade must see *model* edges, not *selected* edges — a [`Meta.fields`][glossary-metafields]-excluded FK still joins rows to a hidden target, and visibility is a row property, not a selection property. (Whether an *unexposed* edge should cascade when its target type exists is pinned as an edge case below: it does — same reasoning.)
- **Calling every target's `get_queryset` unconditionally (upstream behavior).** Rejected: identity hooks generate `__in (SELECT pk FROM target)` clauses that constrain nothing and cost real SQL; `has_custom_get_queryset()` is the package's existing, tested sentinel for exactly this distinction (the optimizer's downgrade rule rides it).
- **A finalize-time precomputed cascade plan per type.** Rejected: the walk reads only stable post-finalize state, but `fields=` is a call-site argument and the hook outcomes are request-scoped; precomputing buys one loop over `get_fields()` per call at the cost of a cache layer with invalidation semantics. Measure first ([Risks and open questions](#risks-and-open-questions)).

### Decision 6 — Hidden-FK semantics: row exclusion is the cascade contract; resolver-level nulling stays the relation contract

When a parent row's FK points at a target row the target type's hook hides, the cascade **excludes the parent row** (the card's open question #1, first option). Nulling the FK field and sentinel values are rejected for the cascade.

Justification:

- **Row exclusion is what the upstream cascade does** — the `Q(fk__in=visible) | Q(fk__isnull=True)` filter *is* row exclusion; the cookbook, the [`GOAL.md`][goal] showcase, and the glossary entry all describe this behavior. The card's "the upstream uses sentinels" sentence reads as a reference to graphene-django's *resolver-level* behavior when a relation target is individually hidden (resolve-to-`None` / sentinel at the field), which is a different layer: the cascade decides *which parent rows exist*, the relation resolver decides *what a traversed field returns*. The conflict reading is recorded in [Risks and open questions](#risks-and-open-questions) per the [`docs/SPECS/NEXT.md`][next] rule.
- **Nulling lies about data.** Serving `entry.item: null` for an existing FK teaches clients the row has no item — indistinguishable from genuine `NULL`, corrupting client caches keyed on the relation. Exclusion is honest: the parent is simply not visible *as a whole* when its identity hangs on a hidden target.
- **Sentinels are schema pollution.** A `HiddenItem` sentinel type would have to implement the target interface, appear in unions, and survive Relay refetch — a large, leaky surface for a behavior exclusion provides for free.
- **No existence leak**: hidden-target and missing-target rows are equally absent; nothing distinguishes "you may not see this" from "this does not exist" — the same property the node refetch contract pins.
- **The layers stay independent**: a consumer who declines to cascade keeps today's per-relation behavior (hidden forward-FK target under the `Prefetch` downgrade surfaces as an unloadable relation at the field level, per the shipped [Relation handling][glossary-relation-handling] contract). The cascade is the tool that makes the *parent queryset* consistent up front.

Alternatives considered (and rejected): **null-the-FK** and **sentinel** — above. **Making the behavior configurable (`mode="exclude" | "null"`)** — rejected: two security semantics behind a flag doubles the test matrix and invites mode-mismatch bugs between types in one graph; one honest behavior, documented, is the alpha-correct call.

### Decision 7 — Cascade performance: lazy subquery composition — zero added round-trips

The cascade composes unevaluated `__in` subqueries into the caller's queryset. Django compiles an unevaluated queryset inside `__in` as a nested `SELECT` in the **same** query — the cascade therefore adds zero round-trips per FK, and the card's open question #2 premise ("subquery-per-FK (one extra round-trip per FK in the cascade)") does not hold for this implementation: there is nothing to benchmark *against* single-pass annotation, because subquery composition already executes in a single pass. The benchmark gate dissolves; Slice 2 pins the property directly with query-count assertions (a cascaded 2-deep traversal executes in the same query count as its uncascaded shape).

Justification: lazy composition is upstream's actual design (its docstring's multi-DB note presumes the subquery is compiled into the outer query — "so the outer `__in` stays on a single database"); the "extra round-trip" reading would only be true if the target queryset were evaluated eagerly (e.g. `list(target_qs)`), which neither upstream nor this port does. Recording the correction here, with the query-count pin as proof, is the honest resolution of the open question.

Alternatives considered (and rejected):

- **A single annotated pass (`Exists()` per edge instead of `__in`).** Not rejected on round-trips (both are single-query) but on fidelity: `__in` against a subquery is the upstream-proven shape with known planner behavior across backends; `Exists()` is the documented *fallback* if real-world nesting depth produces measurably bad plans — recorded in [Risks and open questions](#risks-and-open-questions), not scoped.
- **Eager PK materialization (`pk__in=list(...)`)** — an actual extra round-trip per edge plus an unbounded `IN` list; strictly worse.

### Decision 8 — Multi-DB pinning: `.using(queryset.db)` — the resolved alias, not `_db`

Every per-edge target subquery is built from `related_model._default_manager.using(queryset.db).all()` — `queryset.db`, the public resolved-alias property, not the private `_db` attribute the card's scope bullet names.

Justification: `queryset.db` resolves to `_db` when an explicit `.using(alias)` was applied **and falls back to router resolution when it was not**; `_db` is `None` in the routed case, and `.using(None)` would leave the target subquery to route *independently* — a router that routes the two models differently would then compose a cross-database `__in`, exactly the failure the pin exists to prevent. The upstream uses `queryset.db` (its docstring: "pinned to the caller queryset's DB alias via `queryset.db`"); the card's `_db` spelling is shorthand for the same intent, recorded as a premise correction in [Risks and open questions](#risks-and-open-questions). This extends [Multi-database cooperation][glossary-multi-database-cooperation] axis 2 (explicit-alias preservation) to the cascade: a sharded caller's `.using("shard_b")` propagates into every cascade subquery.

Alternatives considered (and rejected): **`.using(queryset._db)` verbatim from the card** — above (under-pins the routed case). **No pinning (let the router route each subquery)** — rejected: cross-DB `__in` is backend-undefined; the upstream invariant exists because this bit real shards.

### Decision 9 — `fields=` scoping validates loudly with `ConfigurationError`

`fields=` accepts an iterable of model field names and scopes the walk to those edges. A bare string is rejected first, before any name lookup: `isinstance(fields, str)` raises [`ConfigurationError`][glossary-configurationerror] naming the non-string-iterable requirement — a string iterates as its characters, so `fields="item"` would otherwise validate `'i'`, `'t'`, `'e'`, `'m'` one by one and surface a misleading "`'i'` is not a cascadable field" message that hides the real mistake (the missing brackets). Then every supplied name must be a cascadable edge (single-column forward relation per [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection) step 1); an unknown name, a scalar name, or a known-but-non-cascadable name (M2M, reverse relation, generic) raises [`ConfigurationError`][glossary-configurationerror] naming the entry, the model, and the model's cascadable set. A name whose edge is cascadable but whose target has no registered type or no custom hook is **accepted and skipped** (it scopes correctly; there is simply nothing to intersect — consistent with `fields=None` semantics over the same edge).

Justification: upstream silently skips non-matching names — on a security surface, a typo'd `fields=["catagory"]` silently cascades *nothing* for that edge while the call site reads as protected. The package's posture is loud validation with named remediation ([`ConfigurationError`][glossary-configurationerror]'s charter; the [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] typo guard is the direct precedent). The check is a set comparison per call — negligible against the queryset work the call already does.

Alternatives considered (and rejected): **upstream's silent skip** — above. **Warning instead of raising** — rejected: warnings on security-narrowing misconfiguration get lost in request logs; this is exactly the "fail early and loudly rather than silently mutating the schema" rule, applied at the call site. **Validating only under `DEBUG`** — rejected: behavior forks between environments; the cost doesn't justify the fork.

### Decision 10 — Sync/async contract: `SyncMisuseError` on async hooks from the sync walk; the async variant wraps the walk in `sync_to_async`

- **Sync helper**: each target-hook invocation is probed with the [`utils/querysets.py::apply_type_visibility_sync`][querysets] shape — `inspect.iscoroutine(result)` → close the coroutine, raise [`SyncMisuseError`][glossary-syncmisuseerror] with a message naming the target type and the two recourses (`aapply_cascade_permissions`, or a sync hook rewrite). The cascade becomes the package's third sync surface with this contract (Relay node defaults; `FilterSet.apply` sync dispatch).
- **Async helper**: `aapply_cascade_permissions = sync_to_async(thread_sensitive=True)`-wrapped execution of the sync walk (the card's pre-pinned direction, the [`filters/sets.py`][filters-sets] precedent). The wrap exists for **blocking consumer-hook work**: queryset *composition* is lazy and cheap, but consumer hooks routinely call `user.has_perm(...)` / `user.is_authenticated` paths that read the permission tables — real I/O that must not run on the event loop. The `ContextVar` seen-set survives this async→sync boundary intact because `asgiref` copies the calling context into the worker thread (`contextvars.copy_context()` semantics) — so the walk both *sees* a clean seen-set and *contains* its mutations to the copied context, never leaking back into the event-loop task.
- **Consequence, documented**: an `async def` target hook raises `SyncMisuseError` from **both** variants in `0.0.10` (inside the wrapped thread there is still no awaiting context). The recourse is a sync hook on cascade-target types — the same posture the synthesized relation connections shipped with ([`Meta.relation_shapes`][glossary-metarelation_shapes]'s `SyncMisuseError` caveat), and the same escape hatch shape (narrow with `fields=` to skip the async-hooked edge). Async-native walking is a recorded follow-up ([Risks and open questions](#risks-and-open-questions)).

Justification: the card pre-pins the `sync_to_async` design ("async variant uses `sync_to_async` around the cascade walker to stay event-loop-safe") — per the [`docs/SPECS/NEXT.md`][next] rule it is preserved as the Decision, and it is independently right: one walk implementation (no sync/async fork to drift), thread-sensitive execution (ORM-legal under Django's async rules), and the only capability it forgoes (awaiting async hooks) is one no shipped pipeline grants to nested targets either.

Alternatives considered (and rejected):

- **Async-native walk awaiting async hooks edge-by-edge** (`apply_type_visibility_async` per edge). Rejected for `0.0.10`: forks the walk into two implementations around a capability with no demonstrated consumer (no fakeshop type has an async hook; the package's async-hook story is uniformly "sync paths raise `SyncMisuseError`, dedicated async paths await") — and a *mixed* graph (sync parent hook calling the sync helper, async target hook below it) still dead-ends, because the cascade is invoked from inside sync `get_queryset` bodies. The real unlock is an async-hooks-everywhere story, which is bigger than this card.
- **Wrapping each hook call individually instead of the whole walk.** Rejected: N thread hops per request instead of one; the walk is short and the wrap's purpose (off-loop execution of blocking hook code) is served strictly better by one hop.

### Decision 11 — The existing `check_<field>_permission` filter/order gates survive unchanged

The card's open question #4, answered: the shipped [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] `check_<field>_permission(self, request)` denial gates keep their names, signatures, active-input-only scope, and semantics. No rename, no deprecation, no unified dispatcher. The three permission layers are distinct by *what they judge*:

| Layer | Host | Signature | Judges | Ships |
| --- | --- | --- | --- | --- |
| Row visibility (incl. cascade) | `DjangoType.get_queryset` | `(cls, queryset, info)` | which rows exist | shipped / this card |
| Input gates | `FilterSet` / `OrderSet` | `check_<field>_permission(self, request)` | whether *this request's input* may reference a field | shipped (`0.0.8`) |
| Read gates | [`FieldSet`][glossary-fieldset] | `check_<field>_permission(self, info)` | whether a resolved field's value may be read | `0.1.1` ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)) |

Composition order, pinned by Slice 3 tests: **cascade narrows first, gates judge input second** — every pipeline applies `get_queryset` (where the cascade lives) before `FilterSet.apply_*` / `OrderSet.apply_*` (where the gates live), so a gate denial is independent of row visibility and a gate that passes operates only on rows the cascade left visible. A denial therefore cannot leak hidden-row existence: the error fires on *input shape* alone, identically whether hidden rows exist or not.

Justification:

- **Same-name-different-host is the upstream convention the package already adopted.** The [`GOAL.md`][goal] showcase declares `check_name_permission(self, request)` on `GalaxyFilter` / `GalaxyOrder` *and* `check_updated_date_permission(self, info)` on `GalaxyFieldSet` — the host class disambiguates, exactly as `Meta.fields` means different things on a `DjangoType` and a `FilterSet`. Migrants' sidecars port verbatim.
- **Renaming breaks shipped API for a collision that doesn't exist mechanically** — the hosts are different classes; nothing dispatches across them. The `(request)` vs `(info)` signature split is principled, not accidental: input gates predate resolution and see the transport request; read gates run during resolution and see resolver info.
- **A unified shape is `1.0.0`-freeze material at the earliest**: the [Cross-subsystem invariants][glossary-cross-subsystem-invariants] entry already tracks cross-layer composition as the `1.0.0` bar; unifying signatures now, before the third layer ships, would be designing the abstraction before its third data point exists.

Alternatives considered (and rejected): **rename the filter/order gates** (e.g. `check_<field>_filter_permission`) — breaks `0.0.8` consumers and the migration story for a purely cosmetic disambiguation. **Deprecate toward one `check_<field>_permission(self, context)`** — collapses the input/read distinction both upstreams keep separate, and forces every gate to defend against both call shapes during a deprecation window.

### Decision 12 — Connection / node / list composition is contract-pinning, not new code

The card's connection DoD ("a connection field whose wrapped type's `get_queryset` calls `apply_cascade_permissions` produces a Relay connection where every edge's nested relations respect the same cascade rule") is satisfied by the shipped seams, and Slice 3's job is to *pin* that, not to build it:

- [`DjangoConnectionField`][glossary-djangoconnectionfield]'s pipelines call [`utils/querysets.py::apply_type_visibility_sync`][querysets] / `apply_type_visibility_async` on the wrapped type before `filter:` / `orderBy:` / slicing — a cascading hook narrows the connection's row set, its `totalCount` (counted post-visibility), and its cursor space in one place.
- **Edges' nested relations** respect the *targets'* hooks via the optimizer's `Prefetch` downgrade (each nested target with a custom hook gets its visibility baked into the prefetch child queryset) — and when those targets' hooks also cascade, the cascade applies transitively. This is the composition sentence [`spec-033`][spec-033]'s Non-goals pre-pinned for this card.
- [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield] resolve through `resolve_node` / `resolve_nodes` defaults that apply `get_queryset` — a cascade-hidden row refetches as `null`, indistinguishable from missing (the no-existence-leak contract, now extended across FK edges).
- [`DjangoListField`][glossary-djangolistfield] applies the type's hook in its default resolver and around `Manager`/`QuerySet`-returning consumer resolvers.

Justification: the cascade was *designed into* the `get_queryset` seam precisely so every pipeline that honors the hook honors the cascade for free; adding cascade-specific code to any pipeline would create a second application point that could double-apply or drift. The pins are cheap and permanent: each surface gets one cascading-fixture test asserting narrowed results and (where SQL shape is observable) unchanged query counts.

Alternatives considered (and rejected): **a `cascade=True` option on `DjangoConnectionField` / field factories.** Rejected: relocates a type-level row rule to per-field call sites (inconsistency across fields on the same type becomes expressible — and wrong); the type's `get_queryset` is the single home the whole architecture already enforces.

### Decision 13 — Version bumps are owned by the joint `0.0.10` cut

No slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. CHANGELOG bullets land under `[Unreleased]`. The `0.0.10` patch line is shared with [`TODO-ALPHA-035-0.0.10`][kanban] (optimizer robustness hardening); the version bump belongs to the **joint cut** that releases both cards — and lands only after the still-pending `0.0.9` cut (gated on [`WIP-ALPHA-033-0.0.9`][kanban]) is taken. The exports pin in [`tests/base/test_init.py`][test-base-init] *does* grow in Slice 1 (two new `__all__` members) — exports are card-owned surface; the version constant is cut-owned.

Justification: the exact precedent of [`spec-033`][spec-033] Decision 12 and the [`docs/SPECS/NEXT.md`][next] Step 6 mandate for multi-card patch versions.

Alternatives considered (and rejected): **bump in Slice 5 since this card might land last.** Rejected: landing order between `034` and `035` is a maintainer scheduling fact, not a spec fact; the cut is a maintainer release act with its own checklist either way.

## Implementation plan

The card ships as **four functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; 1 is foundation, 2–3 build on 1, 4 builds on 1–3. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — cascade foundation | `django_strawberry_framework/permissions.py` (new), `django_strawberry_framework/__init__.py` (exports), [`tests/base/test_init.py`][test-base-init] (exports pin), `tests/test_permissions.py` (new) | ~14 (walk + invariants ×4 + `fields=` validation + `SyncMisuseError` + async variant + export pins) | `+520 / -5` |
| 2 — optimizer cooperation + N+1 audit | no source change; `tests/test_permissions.py` + [`tests/optimizer/test_extension.py`][test-opt-extension] (extend) | ~6 (downgrade pin, `cacheable = False` pin, zero-extra-queries pin, strictness silence, FK-id-elision fallback pin, diff no-regression) | `+170 / -0` |
| 3 — composition pins | no source change; `tests/test_permissions.py`, [`tests/test_connection.py`][test-connection], [`tests/test_relay_node_field.py`][test-relay-node-field], [`tests/test_list_field.py`][test-list-field] (extend) | ~8 (gate-order composition ×2, connection narrow + `totalCount`, node/nodes `null`, list field narrow, transitive 2-deep, cycle A↔B live shape) | `+220 / -0` |
| 4 — products activation + live HTTP | [`products-schema`][products-schema] (uncomment the four hooks), [`test_products_api.py`][test-products] (extend) | ~6 live (anon / `view_item` / staff visibility matrix across `Entry → Item → Category`, query-count pin, filter+order+cascade composition) | `+190 / -40` |
| 5 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+110 / -50` |

Total expected delta: ~1,100 lines net-positive — consistent with the card's L sizing. No version-file edits ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

Staged-but-not-implemented seams follow the [`AGENTS.md`][agents] design-doc anchor discipline: a source-site `TODO(spec-034 Slice N)` comment naming this spec and the owning slice, paired with `NotImplementedError` where a call path must fail loudly, removed in the change that ships the slice. (Slice 1 ships the whole runtime surface, so no cross-slice seams are expected; the discipline applies if review splits a slice.)

## Edge cases and constraints

- **Nullable FK rows are preserved** — the `__isnull=True` disjunct keeps rows whose FK is `NULL`: a null reference points at no hidden target (card scope; dedicated invariant test).
- **Empty visible set** — a target hook that hides everything yields `fk__in (empty)`: every non-null-FK row drops, null-FK rows survive. No error, no existence leak.
- **Self-referential FK** (`parent = FK("self")`) — the type cascades into itself; the seen-set breaks the recursion at depth 1 per call frame (the *constraint* still applies — parent must be visible by the target hook's own narrowing — but the target hook's nested cascade call returns un-narrowed rather than recursing forever).
- **Mutual cascade A↔B** — `ItemType.get_queryset` cascades (touching `CategoryType`), `CategoryType.get_queryset` cascades back: the seen-set breaks the loop with the partially-narrowed queryset; both directions still apply each other's *direct* narrowing. Pinned by a dedicated fixture.
- **Frame-exit discard** — each frame removes its own class from the seen-set on exit, so two sibling FK edges to the same target both cascade (the set guards *ancestry*, not *visit count*).
- **`ContextVar` isolation** — the root call resets the var in `finally`, so a request-handler exception cannot leak a stale seen-set into the next request sharing the context (upstream contract; pinned). Under the async variant this isolation holds because `asgiref`'s `sync_to_async` propagates a *copy* of the context into the worker thread, so the seen-set's install/reset is scoped to that copy and never escapes to the event-loop task — verified behavior, pinned by `test_aapply_runs_walk_off_event_loop`.
- **Unregistered target model** — edge skipped: no `DjangoType`, no visibility contract. A model exposed *only* through a secondary type ([`Meta.primary`][glossary-metaprimary] semantics make the single registered type primary) cascades through that type.
- **Secondary types are never cascade targets** — `registry.get(model)` returns the primary; a stricter hook on a secondary type does not cascade (relation fields never auto-resolve to secondaries either — same rule, pinned and documented).
- **`Meta.fields`-excluded FK edges still cascade** — visibility is a row property, not a selection property: a hidden-target row is hidden even if the schema never exposes the FK field ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection) alternatives). `fields=` is the scoping tool for consumers who disagree per call site.
- **Composite-PK / composite-FK targets** (Django 5.2 `CompositePrimaryKey`) — no single `column`; skipped by the scope test exactly as M2M is (card scope: "relations without a single-column `column` attribute … are skipped explicitly").
- **`GenericForeignKey` / `GenericRelation`** — excluded by the same two-predicate scope test (`related_model` absent / `column` absent); consistent with the type system's GFK rejection posture.
- **Abstract-base hooks** — `has_custom_get_queryset()` reports overrides inherited through abstract bases (the shipped sentinel discipline), so a cascade target whose hook lives on a shared base participates.
- **The helper is queryset-polymorphic** — it narrows whatever queryset it is handed (root list, connection pre-slice, node refetch, filter child branch, a future mutation's post-write refetch); it never evaluates, never reorders, never projects — pure `.filter(...)` composition, so it composes with [`only()` projection][glossary-only-projection] and ordering downstream.
- **Plan-cache interaction** — a type whose hook cascades carries a custom `get_queryset`, and the shipped rule marks any plan baking a custom hook `cacheable = False` ([`optimizer/walker.py`][walker]'s coarser custom-hook rule — it flips on the *presence* of a custom hook, not on whether the hook reads `info.context.user`). The cascade adds no new cache key dimension; pinned in Slice 2.
- **FK-id elision interaction** — elision already falls back when a target hook must run ([FK-id elision][glossary-fk-id-elision] safety property); cascading targets therefore never elide. No change; pinned.
- **Strictness interaction** — the cascade composes SQL; it cannot lazy-load, so [Strictness mode][glossary-strictness-mode] `"raise"` stays silent across cascaded shapes (pinned). An *uncascaded* hidden-target traversal is unchanged from today.
- **Sharded callers** — `.using("shard_b")` on the caller propagates into every cascade subquery via `queryset.db` ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)); sharded-specific live coverage stays behind `FAKESHOP_SHARDED` per [`AGENTS.md`][agents].
- **Re-entrancy / idempotence** — calling the helper twice on the same queryset double-applies the same filters (Django dedupes identical `Q` trees poorly but the result set is unchanged); harmless, documented, not guarded.
- **`fields=` accepted-and-skipped names** — a cascadable edge whose target lacks a registered type or custom hook validates fine and contributes nothing ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)); only *non-cascadable* names raise.

## Test plan

Tests live across the package-internal `tests/` tree and the `examples/fakeshop/test_query/` tree, per [`docs/TREE.md`][tree], [`AGENTS.md`][agents], and the coverage rule in [`examples/fakeshop/test_query/README.md`][test-query-readme]: any package coverage line reachable by a real GraphQL query against the fakeshop schema MUST be earned in `test_query/` — and most of `permissions.py`'s happy path is exactly that (it runs inside products `get_queryset` hooks during live queries). Package-only families carry their unreachability reason: the four invariant pins need synthetic graphs (cycles, sharded aliases, async hooks) the fakeshop schema doesn't carry; validation and misuse errors need direct calls; optimizer plan content is package-internal.

### Slice 1 — `tests/test_permissions.py` (new)

The card's four dedicated upstream-invariant pins, first:

- `test_cycle_guard_contextvar_breaks_mutual_cascade` — A↔B mutual cascade terminates; both directions apply direct narrowing; the `ContextVar` is reset after the root call (including on exception).
- `test_single_column_scope_skips_m2m_reverse_and_generic` — M2M, reverse FK, reverse OneToOne, `GenericForeignKey`, `GenericRelation`, and a composite-FK shape are all skipped; forward FK and forward OneToOne are cascaded.
- `test_multi_db_subquery_pinned_to_caller_alias` — a `.using("other")` caller produces cascade subqueries on `"other"` (assert via captured queries per alias / `queryset.db` on the composed SQL); a router-divergent model pair stays single-DB.
- `test_nullable_fk_rows_preserved` — `NULL`-FK rows survive a cascade that hides every target row.

Then the remaining contract:

- `test_cascade_excludes_rows_with_hidden_targets` / `test_hidden_and_missing_targets_indistinguishable`.
- `test_transitive_cascade_two_deep` — `Entry → Item → Category` with hooks cascading at each level.
- `test_identity_hook_targets_skipped_no_sql` — a target without a custom hook contributes no subquery (SQL string assertion).
- `test_unregistered_target_model_skipped` / `test_secondary_type_never_cascade_target`.
- `test_fields_scopes_walk` / `test_fields_unknown_name_raises` / `test_fields_non_cascadable_name_raises` / `test_fields_valid_but_hookless_name_accepted` (messages name field, model, cascadable set).
- `test_fields_bare_string_raises` — `fields="item"` raises [`ConfigurationError`][glossary-configurationerror] from the `isinstance(fields, str)` guard (the message names the non-string-iterable requirement, not a per-character `'i'` lookup).
- `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` — coroutine closed (no `RuntimeWarning`), message names the type and both recourses.
- `test_aapply_runs_walk_off_event_loop` — the walk runs off the event loop, and the `ContextVar` seen-set installed inside the wrapped thread does not leak back into the calling async context (asgiref copies the context into the worker thread) — `test_aapply_async_target_hook_still_raises` (the documented [Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async) consequence).
- `test_self_referential_fk_cascades_once`.
- Export pins in [`tests/base/test_init.py`][test-base-init]: both symbols importable from the package root and present in `__all__`.

### Slice 2 — `tests/test_permissions.py` + `tests/optimizer/test_extension.py` (extend)

- `test_cascaded_traversal_adds_zero_queries` — the cascaded 2-deep shape executes in the same query count as its uncascaded twin ([Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)'s proof).
- `test_cascading_target_downgrades_join_to_prefetch` — a relation whose target hook cascades plans a `Prefetch` (not `select_related`), with the cascade baked into the child queryset.
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
- `test_cascade_view_item_user_matrix` — the `view_item` user sees non-private items regardless of category privacy per `ItemType`'s own rule, but entries still drop when the *entry-level* cascade reaches a hidden category through `item` (the per-edge composition the card's hook bodies encode).
- `test_cascade_staff_sees_everything`.
- `test_cascade_query_count_fixed` — the cascaded `allEntries { value item { name category { name } } }` shape executes in a fixed query count (cascade adds zero; optimizer plans the traversal).
- `test_cascade_composes_with_filter_and_order_live` — `filter:` + `orderBy:` + cascade in one request; the `check_name_permission` gates keep firing per their shipped live pins.
- Existing products live assertions are audited for private-fixture sensitivity; any that assumed un-cascaded visibility are re-pinned in the same change (expected small — the suite seeds public fixtures by default).

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 5's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 5 grants that permission**; the Slice 5 maintainer prompt must name the `CHANGELOG.md` edits explicitly so an agent does not infer permission from a standing document.

- **Slice 5 — GLOSSARY**
  - [`docs/GLOSSARY.md`][glossary]: flip [`apply_cascade_permissions`][glossary-apply_cascade_permissions] to `shipped (0.0.10)` and rewrite the body (the walk mechanism, the four invariants, `fields=` validation, the sync/async pair, the composition rule with gates and pipelines) — **correcting the current body's "FK / M2M" scope to forward-FK / OneToOne only, since M2M is out of scope** ([Non-goals](#non-goals)); re-status [Per-field permission hooks][glossary-per-field-permission-hooks] to `planned for 0.1.1` with a body note recording the [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011) contract (host, signature, failure modes, cascade-composition rule); cross-reference the cascade from the [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] entry; update the Index rows and the Public exports list (two new symbols). **Net-new entries: none** — `aapply_cascade_permissions` is documented inside the existing [`apply_cascade_permissions`][glossary-apply_cascade_permissions] entry (one concept, two execution contexts; precedent: the `testing.relay` helpers share entries).
- **Slice 5 — package docs**
  - [`docs/README.md`][docs-readme]: the "Coming next" `0.0.10` line shrinks to the `035` remainder; the shipped-today list gains the permissions bullet.
  - [`docs/TREE.md`][tree]: `permissions.py` moves from "planned by TODO-ALPHA-034-0.0.10" to its real one-line description; `tests/test_permissions.py` joins the test tree.
  - [`TODAY.md`][today]: the products demonstration sections gain the activated cascade hooks (the "What products is still waiting for" list drops permissions and its stale `TODO-ALPHA-033-0.0.10` card id); the commented-hook caveat in the visibility section rewrites to the live shape.
  - [`README.md`][readme]: the status paragraph's newest-shipped-surface line gains the permissions subsystem; the "Coming next" roadmap line for `0.0.10` updates.
  - [`CHANGELOG.md`][changelog]: `### Added` bullets under `[Unreleased]` for `apply_cascade_permissions` / `aapply_cascade_permissions` and the products cascade activation. No version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).
- **Slice 5 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`TODO-ALPHA-034-0.0.10`][kanban] to Done with the next `DONE-NNN-0.0.10` id; confirm the spec reference points at `docs/spec-034-permissions-0_0_10.md` (a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`, not a hand edit); surface the unowned M2M / reverse-relation cascade follow-up to the maintainer for a new card ([Risks and open questions](#risks-and-open-questions)). No version-file edits.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **The per-field-hooks status contradiction (card + glossary vs. board).** The [Per-field permission hooks][glossary-per-field-permission-hooks] glossary entry says `planned for 0.0.10` while hosting the hooks on the `0.1.1` [`FieldSet`][glossary-fieldset]; the card's scope line claims the hooks while its open question #4 files the read gate under the FieldSet card. Preferred answer ([Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011)): define the surface here, implement in `0.1.1`, re-status the glossary in Slice 5. Fallback: if the maintainer wants runnable per-field gates in `0.0.10`, the recorded contract makes pulling the gate-dispatch half of `FieldSet` forward a scoped, separately-decidable addition — but it should be its own card, not a quiet slice graft.
- **Card-premise correction: "one extra round-trip per FK".** The card's open question #2 frames subquery-per-FK as round-trip-costed; lazy `__in` composition compiles into the caller's single query ([Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)), so the benchmark-both gate dissolves. Preferred answer: ship subquery composition with the Slice 2 query-count pin as proof. Fallback: if a real consumer graph produces measurably bad plans from deep subquery nesting, swap the constraint shape to per-edge `Exists()` — a contained, semantics-preserving change; the public contract names no SQL shape.
- **Card-premise correction: `.using(qs._db)`.** The private `_db` is `None` for routed querysets and would leave target subqueries to route independently ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)); the resolved `queryset.db` is the upstream-faithful pin. Preferred answer: `queryset.db`, with the sharded test proving alias propagation. Fallback: none needed — `_db` has no advantage in any case examined.
- **The card's "upstream uses sentinels" sentence vs. the upstream cascade's row exclusion.** Read as describing graphene-django's resolver-level hidden-target behavior, not the cascade helper ([Decision 6](#decision-6--hidden-fk-semantics-row-exclusion-is-the-cascade-contract-resolver-level-nulling-stays-the-relation-contract)); the helper this card ports performs row exclusion, verbatim from source. Preferred answer: row exclusion. Fallback: a `mode=` flag is expressible later without breaking the default; rejected now per Decision 6.
- **M2M / reverse-relation cascade has no follow-up card.** The card says "if deferring, name the follow-up card in the spec" — none exists. Preferred answer: Slice 5's wrap surfaces the gap to the maintainer for a new TODO card (the many-side design question — hide the parent vs. narrow the list — deserves its own card body; the [`spec-033`][spec-033] precedent for unowned follow-ups). Fallback: if the maintainer wants it pre-named, a placeholder card under To Do – Beta with the two-question body is a five-minute kanban DB insert at wrap time.
- **Async-hooked cascade targets dead-end in `0.0.10`.** Both variants raise [`SyncMisuseError`][glossary-syncmisuseerror] for an `async def` target hook ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)). No fakeshop or test fixture currently declares one, and the package's other nested-visibility surfaces share the posture. Preferred answer: document the recourses (sync hook; `fields=` narrowing) and hold. Fallback: an async-native walk (`apply_type_visibility_async` per edge inside `aapply_cascade_permissions`) is additive and contained if a real consumer hits the wall — record it on the card that brings async hooks to the filter child-branch derivation too, since the surfaces should move together.
- **Stale card-id reference in `TODAY.md`.** [`TODAY.md`][today] cites `TODO-ALPHA-033-0.0.10` for this card — a pre-renumbering id (card numbers are explicitly unstable; [`apps/kanban/models.py::Card`][kanban-models] documents number recomputation). The products schema's commented hooks already cite the correct `TODO-ALPHA-034-0.0.10`, so no schema-comment correction is needed (only the uncomment). Preferred answer: Slice 5 corrects `TODAY.md`. Fallback: none needed.
- **Pre-existing glossary / tooling drift (corrected, not introduced).** Two doc-side inaccuracies predate this card and are cleaned up by Slice 5, not caused by it: (a) the [`apply_cascade_permissions`][glossary-apply_cascade_permissions] glossary body describes the cascade reaching "through FK / M2M", but M2M is out of scope ([Non-goals](#non-goals)) — Slice 5's body rewrite drops the M2M claim; (b) `scripts/check_spec_glossary.py` passes clean while silently accepting the two companion-CSV rows that share the single `apply_cascade_permissions` anchor (the async-twin share is intentional — no own heading by design — but the checker has no dedup/collision warning, so the CSV note's accuracy is eye-checked, not tool-enforced). Preferred answer: fix both in Slice 5; neither is a scope change. Fallback: none needed.
- **Cascade-call overhead on hot paths.** The walk runs per `get_queryset` invocation — per request on root fields, and per prefetch-child build on downgraded relations. The work is one `get_fields()` loop plus set ops; the SQL it adds is subqueries the database deduplicates well. Preferred answer: ship; the Slice 2/4 query-count pins catch regressions, and plans baking the hooks are uncacheable already. Fallback: a per-`(model, fields)` walk-result memo (the edges, not the querysets) — cheap to add behind the same public surface; deferred per the measure-first discipline ([Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection) alternatives).
- **Live-suite sensitivity to newly-activated hooks.** Activating four `get_queryset` hooks changes anonymous-request visibility across the whole products live suite, not just the new tests. Preferred answer: the existing suite runs against public-only seeded fixtures (the seeders default `is_private=False` paths), so churn should be minimal; any assertion that seeded private rows re-pins in Slice 4. Fallback: if churn is larger than expected, seed the private fixtures only inside the new cascade tests and keep the legacy seed paths public-only — fixture-scoping, not contract change.

## Out of scope (explicitly tracked elsewhere)

- **`FieldSet` / `Meta.fields_class` / per-field read-gate implementation** — the `0.1.1` FieldSet card; the contract is pinned in [Decision 2](#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011).
- **M2M / reverse-relation cascade visibility** — deferred whole; no card yet, surfaced for the maintainer at wrap time ([Risks and open questions](#risks-and-open-questions)).
- **Mutations composition with the cascade** — the `0.0.11` mutations cohort ([`DjangoMutation`][glossary-djangomutation] and its dependency note on this card); [Auth mutations][glossary-auth-mutations] likewise.
- **Aggregation cascade** — [`get_child_queryset`][glossary-get_child_queryset] / [`AggregateSet`][glossary-aggregateset], `0.1.3`.
- **[Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]** — [`WIP-ALPHA-033-0.0.9`][kanban], independent; the cascade composes through `get_queryset` regardless of how connections plan.
- **Optimizer robustness guards (G1–G3)** — [`TODO-ALPHA-035-0.0.10`][kanban], the joint-cut sibling.
- **Object-level permission backends (guardian-style) and per-field permission *extensions*** — strawberry_django's decorator-shaped surface; not on the roadmap (post-`1.0.0` differentiation would go through [`BACKLOG.md`][backlog]).
- **Version bump** — owned by the joint `0.0.10` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all four functional slices' items plus the wrap are satisfied. The card's own DoD bullets map onto items 1 (spec), 2–5 (helper + exports + invariants), 6–7 (optimizer / N+1), 8–9 (gate + connection composition), 10–11 (fakeshop live coverage), and 12–13 (docs + version boundary).

**Spec + companion CSV**

1. `docs/spec-034-permissions-0_0_10.md` (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion `spec-034-permissions-0_0_10-terms.csv` anchoring every project-specific term that has a [`docs/GLOSSARY.md`][glossary] heading; `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` reports `OK: <N> terms`. The card introduces one net-new public symbol pair documented under the existing [`apply_cascade_permissions`][glossary-apply_cascade_permissions] entry, so no new glossary heading is required.

**Slice 1 — cascade foundation**

2. `django_strawberry_framework/permissions.py` ships `apply_cascade_permissions(cls, queryset, info, fields=None)` with the walk of [Decision 5](#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-has_custom_get_queryset-gate-subquery-intersection) (single-column forward scope, registry primary lookup, custom-hook gate, `Q(__in) | Q(__isnull)` intersection, `_default_manager`).
3. The four upstream invariants are each pinned by a dedicated test (card DoD): `ContextVar` cycle guard with `finally` reset and partial-narrow cycle break; single-column FK/O2O scope; multi-DB pinning to the caller's resolved alias ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)); nullable-FK preservation.
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
13. **No version bump lands in this card** per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut): `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.10` cut owns the bump, after the pending `0.0.9` cut).
14. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; worker-local validation is `uv run ruff format .` and `uv run ruff check --fix .`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoconnection]: GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-djangonodesfield]: GLOSSARY.md#djangonodesfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-get_child_queryset]: GLOSSARY.md#get_child_queryset
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-metaconnection]: GLOSSARY.md#metaconnection
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metaoptimizer_hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-metarelation_shapes]: GLOSSARY.md#metarelation_shapes
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-optimizerhint]: GLOSSARY.md#optimizerhint
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-queryset-diffing]: GLOSSARY.md#queryset-diffing
[glossary-relatedfilter]: GLOSSARY.md#relatedfilter
[glossary-relatedorder]: GLOSSARY.md#relatedorder
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-015]: SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-027]: SPECS/spec-027-filters-0_0_8.md
[spec-028]: SPECS/spec-028-orders-0_0_8.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-033]: SPECS/spec-033-connection_optimizer-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py
[filters-sets]: ../django_strawberry_framework/filters/sets.py
[list-field]: ../django_strawberry_framework/list_field.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[registry]: ../django_strawberry_framework/registry.py
[types-base]: ../django_strawberry_framework/types/base.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-connection]: ../tests/test_connection.py
[test-list-field]: ../tests/test_list_field.py
[test-opt-extension]: ../tests/optimizer/test_extension.py
[test-relay-node-field]: ../tests/test_relay_node_field.py

<!-- examples/ -->
[kanban-models]: ../examples/fakeshop/apps/kanban/models.py
[products-schema]: ../examples/fakeshop/apps/products/schema.py
[products-services]: ../examples/fakeshop/apps/products/services.py
[test-products]: ../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-permissions]: /Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/permissions.py
