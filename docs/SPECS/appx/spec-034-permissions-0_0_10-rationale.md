# Rationale companion: spec-034 (Permissions subsystem — cascade visibility)

Companion to [`docs/SPECS/spec-034-permissions-0_0_10.md`][spec-034]. It carries that spec's **deliberative layer**: every Decision's justification, every alternative a Decision rejected and why it lost, and the standing risks with their fallbacks. The spec carries the contract; this file carries why the contract has its shape. Neither duplicates the other.

Read this when checking the implementation against the reasoning behind it, or before re-opening a settled question. Worker 2 never reads it ([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-034-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-034-0.0.10`, so `<NNN>` is `034` and `<0_0_X>` is `0_0_10`.
- The topic slug is `permissions` — the card's own suggested filename stem (`docs/spec-permissions.md`), kept because it names the subsystem precisely.

### Alternatives considered (and rejected)

- **The card's own `docs/spec-permissions.md`.** Rejected: it does not follow the structured-filename convention every spec carries.
- **Topic slug `cascade_permissions`.** Rejected: the card is the *permissions subsystem* card — the cascade is its centerpiece but the spec also pins the per-field surface decision and the gate composition; the broader slug matches the card title.

## Decision 2 — Card-scope boundary: the cascade ships end-to-end; the per-field read gate is defined here and implemented with `FieldSet` (`0.1.1`)

Spec: [Decision 2 — Card-scope boundary: the cascade ships end-to-end; the per-field read gate is defined here and implemented with `FieldSet` (`0.1.1`)][spec-034-d2].

### Justification

- **The card resolves its own tension.** The card's scope line names "per-field permission hooks declared via `Meta`", but its open question #4 locates the read gate at "`FieldSet.check_<field>_permission(info)`" under the beta FieldSet card ([`TODO-BETA-059-0.1.1`][kanban]) — the card itself files the implementation there. The board agrees: `fieldset/` is a `0.1.1` planned path in [`docs/TREE.md`][tree], the [`FieldSet`][glossary-fieldset] glossary entry is `planned for 0.1.1`, and `fields_class` sits in `DEFERRED_META_KEYS`. Per the [`docs/SPECS/NEXT.md`][next] boundary rule the card is preferred.
- **The DoD line is satisfiable under this reading and only this reading.** "Define the `Meta` surface for per-field permissions and promote keys only when applied end-to-end" — *define* (this Decision) and *don't promote early* (the invariant). Shipping gate code in `0.0.10` without `FieldSet` would require inventing a second, interim host that `0.1.1` would immediately replace.

### Alternatives considered (and rejected)

- **Ship type-level `check_<field>_permission` classmethods on `DjangoType` now, migrate to `FieldSet` later.** Rejected: creates a public surface `0.1.1` would replace, with a migration burden the package would own forever; the upstream cookbook hosts read gates on `FieldSet` (the [`GOAL.md`][goal] astronomy showcase shows exactly that split), and `START.md`'s scope-creep rule says don't quietly mix in extras that bloat the slice.
- **Pull the whole `FieldSet` forward into `0.0.10`.** Rejected: `FieldSet` is an L-sized subsystem of its own (computed fields, resolver overrides, redaction machinery); the board sequences it post-alpha, and this card is already L.
- **Ship nothing and strike the bullet.** Rejected: the card demands the surface be *defined* before the implementation pass; leaving it undefined re-opens the design in `0.1.1` with no record of the cascade-composition rule the DoD pins.

## Decision 3 — Module and test locations: flat `permissions.py` + `tests/test_permissions.py`

Spec: [Decision 3 — Module and test locations: flat `permissions.py` + `tests/test_permissions.py`][spec-034-d3].

### Justification

The card says "`django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows" — the surface is two functions and a `ContextVar`; a package is structure without content. The upstream's own `permissions.py` is a flat module. When `0.1.1` adds the FieldSet read gates the *fieldset* package grows, not this module. The redundant-alias `SyncMisuseError` re-export widens the module's import surface and not the package's (the name is already in the package-root `__all__` via `types`), so it needs no public-surface decision of its own.

### Alternatives considered (and rejected)

**`permissions/` package now, anticipating growth.** Rejected: the same speculative-structure mistake [`START.md`][start] records for `conf.py` pre-population ("add a settings key only when the feature that needs it lands" generalizes); renames later are cheap (`git mv` + import sweep) and may never be needed.

## Decision 4 — Public surface and naming: `apply_cascade_permissions` + `aapply_cascade_permissions`, exported from the package root

Spec: [Decision 4 — Public surface and naming: `apply_cascade_permissions` + `aapply_cascade_permissions`, exported from the package root][spec-034-d4].

### Justification

- **Name parity is migration surface.** The card's DoD pins the import line (`from django_strawberry_framework import apply_cascade_permissions`); [`GOAL.md`][goal]'s showcase, the glossary entry, and the products schema all use the name. A `django-graphene-filters` migrant's `get_queryset` body moves verbatim.
- **The `a`-prefix follows the asgiref/Django convention** (`aget`, `acount`, `aupdate_or_create`) that the package's own planned surfaces adopt (the [`AggregateSet`][glossary-aggregateset] entry names `compute` / `acompute`). The `apply_sync` / `apply_async` suffix pair is the *set-family classmethod* convention ([`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset]) — a different namespace with a paired-verb shape; a module-level function follows the Django convention.
- **Package-root export** matches the card DoD and the symbol's audience (every consumer writing a `get_queryset`), parallel to [`finalize_django_types`][glossary-finalize_django_types].

### Alternatives considered (and rejected)

- **`apply_cascade_permissions_async`.** Rejected: no precedent in the package or Django; verbose without adding clarity.
- **A single function with an `async_=` flag or auto-detection.** Rejected: callers must know whether to `await`; a dual-mode return type (queryset or coroutine) is the exact ambiguity [`SyncMisuseError`][glossary-syncmisuseerror] exists to kill.
- **Exporting from a `django_strawberry_framework.permissions` namespace only.** Rejected: the card DoD names the root import; subsystem-namespace imports (`from django_strawberry_framework.filters import FilterSet`) are for *family* surfaces, while this is a single helper used inside `DjangoType` bodies alongside root-exported symbols.

## Decision 5 — The cascade walk: call-time model-graph walk, registry primary lookup, every registered target composes, subquery intersection

Spec: [Decision 5 — The cascade walk: call-time model-graph walk, registry primary lookup, every registered target composes, subquery intersection][spec-034-d5].

### Justification

This is the upstream mechanism with the package's own registry and hook vocabulary substituted, tightened wherever upstream's shape fails open on a security surface:

- **Scope predicate.** `django_strawberry_framework/utils/relations.py::is_single_column_foreign_key` (`isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None`) is the forward-concrete test: it subsumes upstream's `related_model` check, excludes M2M and `GenericRelation` by type rather than by their `column = None` value, and keeps the `column` check only as a guard against a future non-single-column `ForeignKey` shape.
- **MTI parent links cascade.** Excluding the `<parent>_ptr` edge would leave a hidden MTI parent reachable through its child type — the leak the row-exclusion contract exists to close.
- **Unsupported forward relations fail closed.** Whether skipping an edge can hide a leak is the test: a `GenericRelation` selects no parent row's single target and stays skippable, but a GFK (and any forward `ForeignObject` that is not a `ForeignKey`, of any width) selects one target row, so skipping it lets a row pointing at a hidden target survive.
- **Every registered target composes.** A gate on `has_custom_get_queryset()` is a *visibility* decision wearing an optimization's clothes: a registered proxy type whose filtered `_default_manager` **is** its visibility policy declares no custom hook, so the gate would silently bypass that policy. Registration, not hook declaration, is the visibility contract.
- **Cycles fail closed.** Upstream returns the queryset un-narrowed on re-entry; a silently-broken cycle skips the re-entered type's *outgoing* visibility edges, so a root row whose hidden relation is only reachable through the re-entry would survive. The explicit zero-edge scope (`fields=[]`) is the one re-entrant shape that is provably non-recursive.
- **The root and every hook return are sealed.** The helper is called from inside a consumer-owned hook, so its root argument is untrusted query state; a consumer `QuerySet` subclass (or an instance-shadowed `filter`) must not be able to erase the cascade predicate. Delegating the per-edge hook invocation to `utils/querysets.py::apply_type_visibility_sync` gives the package one owner of the hook-result shape / concrete-table / alias contract, while the cascade's `_edge_error_renderer` / `_root_error_renderer` seams keep its own prose on every failure.
- **Hook returns are re-projected, not trusted.** The return becomes the RHS of a row-visibility `__in`, so it is re-projected to `.values(field.target_field.attname)`; the shapes where re-projection would change semantics (grouped, field-`distinct`, target-column-shadowing alias) fail closed. The alias-shadow guard carries its own security argument: Django blocks a bare `annotate(id=Value(pk))` but permits `values("x").annotate(id=Value(pk))`, which stays ungrouped and would otherwise re-project to the injected constant.

Everything else load-bearing (the `Q` shape, `_default_manager` as the base, the token-scoped `ContextVar` lifecycle) is ported because it is the proven, cookbook-documented behavior the card requires.

### Alternatives considered (and rejected)

- **Walking `registry.iter_definitions()` and matching definitions back to the model's fields.** Rejected: inverts the lookup direction for no gain — the model's `_meta.get_fields()` is the authoritative edge list, and the keyed `get(model)` is O(1) per edge over the same store the card's named surface iterates.
- **Resolving targets through each definition's relation metadata instead of `model._meta`.** Rejected: the cascade must see *model* edges, not *selected* edges — a [`Meta.fields`][glossary-metafields]-excluded FK still joins rows to a hidden target, and visibility is a row property, not a selection property.
- **Gating each edge on the target's `has_custom_get_queryset()`.** Rejected: it looks like a free optimization (an identity hook seems to narrow nothing) but bypasses a filtered default manager's policy, as above. The identity hook's `__in (SELECT pk FROM target)` is the cost of honoring that policy.
- **A finalize-time precomputed cascade plan per type.** Rejected: `fields=` is a call-site argument and hook outcomes are request-scoped, so neither can be precomputed, and a finalize step would have to know about every model the cascade might reach. What *is* stable is Django model metadata, which [`permissions.py::_edge_plan`][permissions] classifies lazily, once per model, behind a bounded `lru_cache`: nothing to invalidate (metadata is immutable after app loading), and eviction is correctness-neutral because the plan can always be recomputed.

## Decision 6 — Hidden-FK semantics: row exclusion is the cascade contract; resolver-level nulling stays the relation contract

Spec: [Decision 6 — Hidden-FK semantics: row exclusion is the cascade contract; resolver-level nulling stays the relation contract][spec-034-d6].

### Justification

- **Row exclusion is what the upstream cascade does** — the `Q(fk__in=visible) | Q(fk__isnull=True)` filter *is* row exclusion; the cookbook, the [`GOAL.md`][goal] showcase, and the glossary entry all describe this behavior. The card's "the upstream uses sentinels" sentence reads as a reference to graphene-django's *resolver-level* behavior when a relation target is individually hidden (resolve-to-`None` / sentinel at the field), which is a different layer: the cascade decides *which parent rows exist*, the relation resolver decides *what a traversed field returns*.
- **Nulling lies about data.** Serving `entry.item: null` for an existing FK teaches clients the row has no item — indistinguishable from genuine `NULL`, corrupting client caches keyed on the relation. Exclusion is honest: the parent is simply not visible *as a whole* when its identity hangs on a hidden target.
- **Sentinels are schema pollution.** A `HiddenItem` sentinel type would have to implement the target interface, appear in unions, and survive Relay refetch — a large, leaky surface for a behavior exclusion provides for free.
- **Every non-staff consumer branch cascades.** A `view_<model>` branch that filtered `is_private=False` without cascading would let a permission user see a row whose non-null forward FK target the target hook hides, and selecting that relation raises on a valid query. Only staff bypass.

### Alternatives considered (and rejected)

**null-the-FK** and **sentinel** — above. **Making the behavior configurable (`mode="exclude" | "null"`)** — rejected: two security semantics behind a flag doubles the test matrix and invites mode-mismatch bugs between types in one graph; one honest behavior, documented, is the alpha-correct call.

## Decision 7 — Cascade performance: lazy subquery composition — zero added round-trips

Spec: [Decision 7 — Cascade performance: lazy subquery composition — zero added round-trips][spec-034-d7].

### Justification

Lazy composition is upstream's actual design (its docstring's multi-DB note presumes the subquery is compiled into the outer query — "so the outer `__in` stays on a single database"); the "extra round-trip" reading would only be true if the target queryset were evaluated eagerly (e.g. `list(target_qs)`), which neither upstream nor this port does. The fixed live query count is the proof. The strictness-silence row is a different instrument: `types/resolvers.py::_check_n1` reports unplanned *relation-resolver* accesses only, so it detects an optimizer-planning regression in the composed shape, not a cascade that began evaluating its target querysets eagerly — which is why the zero-round-trip property has its own pin.

### Alternatives considered (and rejected)

- **A single annotated pass (`Exists()` per edge instead of `__in`).** Not rejected on round-trips (both are single-query) but on fidelity: `__in` against a subquery is the upstream-proven shape with known planner behavior across backends; `Exists()` is the fallback if real-world nesting depth produces measurably bad plans ([Risks and open questions](#risks-and-open-questions)).
- **Eager PK materialization (`pk__in=list(...)`)** — an actual extra round-trip per edge plus an unbounded `IN` list; strictly worse.

## Decision 8 — Multi-DB pinning: `.using(queryset.db)` — the resolved alias, not `_db`

Spec: [Decision 8 — Multi-DB pinning: `.using(queryset.db)` — the resolved alias, not `_db`][spec-034-d8].

### Justification

The upstream uses `queryset.db` (its docstring: "pinned to the caller queryset's DB alias via `queryset.db`"); the card's `_db` spelling is shorthand for the same intent. Enforcing the root alias on nested applications and hook returns, rather than only propagating it, is the same pin read in the other direction: a subquery the router would send elsewhere is precisely the cross-database `__in` the pin exists to prevent, so it raises rather than silently resolving.

### Alternatives considered (and rejected)

**`.using(queryset._db)` verbatim from the card** — under-pins the routed case (the spec's Decision body). **No pinning (let the router route each subquery)** — rejected: cross-DB `__in` is backend-undefined; the upstream invariant exists because this bit real shards.

## Decision 9 — `fields=` scoping validates loudly with `ConfigurationError`

Spec: [Decision 9 — `fields=` scoping validates loudly with `ConfigurationError`][spec-034-d9].

### Justification

Upstream silently skips non-matching names — on a security surface, a typo'd `fields=["catagory"]` silently cascades *nothing* for that edge while the call site reads as protected. The package's posture is loud validation with named remediation ([`ConfigurationError`][glossary-configurationerror]'s charter; the [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] typo guard is the direct precedent). A `fields=` name matching an unsupported forward relation gets its own message because it is a distinct mistake (naming the GFK instead of its backing FK) with a distinct recourse.

### Alternatives considered (and rejected)

**upstream's silent skip** — above. **Warning instead of raising** — rejected: warnings on security-narrowing misconfiguration get lost in request logs; this is exactly the "fail early and loudly rather than silently mutating the schema" rule, applied at the call site. **Validating only under `DEBUG`** — rejected: behavior forks between environments; the cost doesn't justify the fork.

## Decision 10 — Sync/async contract: `SyncMisuseError` on async hooks from the sync walk; the async variant wraps the walk in `sync_to_async`

Spec: [Decision 10 — Sync/async contract: `SyncMisuseError` on async hooks from the sync walk; the async variant wraps the walk in `sync_to_async`][spec-034-d10].

### Justification

The card pre-pins the `sync_to_async` design ("async variant uses `sync_to_async` around the cascade walker to stay event-loop-safe") — per the [`docs/SPECS/NEXT.md`][next] rule it is preserved as the Decision, and it is independently right: one walk implementation (no sync/async fork to drift), thread-sensitive execution (ORM-legal under Django's async rules), and the only capability it forgoes (awaiting async hooks) is one no shipped pipeline grants to nested targets either. The wrap is the shared [`utils/querysets.py::run_in_one_sync_boundary`][querysets] so the boundary has one owner. Delegating each hook call to `apply_type_visibility_sync` keeps one sync-misuse site: a visibility-hook-routing mistake is a data-leak bug, and the recourse text is surface-aware (make the target hook sync, or scope `fields=`) because pointing a cascade caller at `aapply_cascade_permissions` would send them to a wrapper of the same sync walk.

### Alternatives considered (and rejected)

- **Async-native walk awaiting async hooks edge-by-edge** (`apply_type_visibility_async` per edge). Rejected: forks the walk into two implementations around a capability with no demonstrated consumer (no fakeshop type has an async hook; the package's async-hook story is uniformly "sync paths raise `SyncMisuseError`, dedicated async paths await") — and a *mixed* graph (sync parent hook calling the sync helper, async target hook below it) still dead-ends, because the cascade is invoked from inside sync `get_queryset` bodies. The real unlock is an async-hooks-everywhere story, which is bigger than this card.
- **Wrapping each hook call individually instead of the whole walk.** Rejected: N thread hops per request instead of one; the walk is short and the wrap's purpose (off-loop execution of blocking hook code) is served strictly better by one hop.

## Decision 11 — The existing `check_<field>_permission` filter/order gates survive unchanged

Spec: [Decision 11 — The existing `check_<field>_permission` filter/order gates survive unchanged][spec-034-d11].

### Justification

- **Same-name-different-host is the upstream convention the package adopts.** The [`GOAL.md`][goal] showcase declares `check_name_permission(self, request)` on `GalaxyFilter` / `GalaxyOrder` *and* `check_updated_date_permission(self, info)` on `GalaxyFieldSet` — the host class disambiguates, exactly as `Meta.fields` means different things on a `DjangoType` and a `FilterSet`. Migrants' sidecars port verbatim.
- **Renaming breaks shipped API for a collision that doesn't exist mechanically** — the hosts are different classes; nothing dispatches across them. The `(request)` vs `(info)` signature split is principled, not accidental: input gates predate resolution and see the transport request; read gates run during resolution and see resolver info.
- **A unified shape is `1.0.0`-freeze material at the earliest**: the [Cross-subsystem invariants][glossary-cross-subsystem-invariants] entry tracks cross-layer composition as the `1.0.0` bar; unifying signatures before the third layer ships would be designing the abstraction before its third data point exists.

### Alternatives considered (and rejected)

**rename the filter/order gates** (e.g. `check_<field>_filter_permission`) — breaks `0.0.8` consumers and the migration story for a purely cosmetic disambiguation. **Deprecate toward one `check_<field>_permission(self, context)`** — collapses the input/read distinction both upstreams keep separate, and forces every gate to defend against both call shapes during a deprecation window.

## Decision 12 — Connection / node / list composition is contract-pinning, not new code

Spec: [Decision 12 — Connection / node / list composition is contract-pinning, not new code][spec-034-d12].

### Justification

The cascade is designed into the `get_queryset` seam precisely so every pipeline that honors the hook honors the cascade for free; adding cascade-specific code to any pipeline would create a second application point that could double-apply or drift. The pins are cheap and permanent: each surface gets one cascading-fixture test asserting narrowed results and (where SQL shape is observable) unchanged query counts.

### Alternatives considered (and rejected)

**a `cascade=True` option on `DjangoConnectionField` / field factories.** Rejected: relocates a type-level row rule to per-field call sites (inconsistency across fields on the same type becomes expressible — and wrong); the type's `get_queryset` is the single home the whole architecture enforces.

## Decision 13 — Version bumps are owned by the joint `0.0.10` cut

Spec: [Decision 13 — Version bumps are owned by the joint `0.0.10` cut][spec-034-d13].

### Justification

The [`docs/SPECS/NEXT.md`][next] Step 6 mandate for multi-card patch versions, the same shape [`spec-033`][spec-033] Decision 12 uses.

### Alternatives considered (and rejected)

**bump in Slice 5 since this card might land last.** Rejected: landing order between `034` and `035` is a maintainer scheduling fact, not a spec fact; the cut is a maintainer release act with its own checklist either way.

## Risks and open questions

Each item names the shipped answer and the fallback if it proves wrong.

- **Card-premise correction: "one extra round-trip per FK".** The card's open question #2 frames subquery-per-FK as round-trip-costed; lazy `__in` composition compiles into the caller's single query ([Decision 7](#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips)), so the benchmark-both gate dissolves. Fallback: if a real consumer graph produces measurably bad plans from deep subquery nesting, swap the constraint shape to per-edge `Exists()` — a contained, semantics-preserving change; the public contract names no SQL shape.
- **Card-premise correction: `.using(qs._db)`.** The private `_db` is `None` for routed querysets and would leave target subqueries to route independently ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)); the resolved `queryset.db` is the upstream-faithful pin. No fallback needed — `_db` has no advantage in any case examined.
- **The card's "upstream uses sentinels" sentence vs. the upstream cascade's row exclusion.** Read as describing graphene-django's resolver-level hidden-target behavior, not the cascade helper ([Decision 6](#decision-6--hidden-fk-semantics-row-exclusion-is-the-cascade-contract-resolver-level-nulling-stays-the-relation-contract)). Fallback: a `mode=` flag is expressible later without breaking the default; rejected per Decision 6.
- **M2M / reverse-relation cascade.** Out of scope here; the to-many design question (hide the parent vs. narrow the list) is decided by the graph-substrate card [`TODO-BETA-058-0.1.1`][kanban], whose edge-scope predicates compile child visibility.
- **Async-hooked cascade targets dead-end.** Both variants raise [`SyncMisuseError`][glossary-syncmisuseerror] for an `async def` target hook ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)); no fakeshop type declares one, and the package's other nested-visibility surfaces share the posture. Fallback: an async-native walk (`apply_type_visibility_async` per edge inside `aapply_cascade_permissions`) is additive and contained if a real consumer hits the wall — on the card that brings async hooks to the filter child-branch derivation too, since the surfaces should move together.
- **Cascade-call overhead on hot paths.** The walk runs per `get_queryset` invocation — per request on root fields, and per prefetch-child build on downgraded relations. The per-call work is set ops over the model's cached edge plan ([`permissions.py::_edge_plan`][permissions]), and the SQL the walk adds is subqueries the database deduplicates well; the live query-count pins catch regressions, and plans baking the hooks are uncacheable already. The cached plan is keyed per model, so the `fields=` validation's own per-call set diff still runs; a per-`(model, fields)` memo would absorb it. Hook outcomes are request-scoped and are never cached.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-aggregateset]: ../../GLOSSARY.md#aggregateset
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[glossary-fieldset]: ../../GLOSSARY.md#fieldset
[glossary-filterset]: ../../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../../GLOSSARY.md#finalize_django_types
[glossary-metafields]: ../../GLOSSARY.md#metafields
[glossary-metaoptimizer_hints]: ../../GLOSSARY.md#metaoptimizer_hints
[glossary-orderset]: ../../GLOSSARY.md#orderset
[glossary-syncmisuseerror]: ../../GLOSSARY.md#syncmisuseerror
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md
[spec-034]: ../spec-034-permissions-0_0_10.md
[spec-034-d1]: ../spec-034-permissions-0_0_10.md#decision-1--spec-filename-and-canonical-naming
[spec-034-d10]: ../spec-034-permissions-0_0_10.md#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async
[spec-034-d11]: ../spec-034-permissions-0_0_10.md#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged
[spec-034-d12]: ../spec-034-permissions-0_0_10.md#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code
[spec-034-d13]: ../spec-034-permissions-0_0_10.md#decision-13--version-bumps-are-owned-by-the-joint-0010-cut
[spec-034-d2]: ../spec-034-permissions-0_0_10.md#decision-2--card-scope-boundary-the-cascade-ships-end-to-end-the-per-field-read-gate-is-defined-here-and-implemented-with-fieldset-011
[spec-034-d3]: ../spec-034-permissions-0_0_10.md#decision-3--module-and-test-locations-flat-permissionspy--teststest_permissionspy
[spec-034-d4]: ../spec-034-permissions-0_0_10.md#decision-4--public-surface-and-naming-apply_cascade_permissions--aapply_cascade_permissions-exported-from-the-package-root
[spec-034-d5]: ../spec-034-permissions-0_0_10.md#decision-5--the-cascade-walk-call-time-model-graph-walk-registry-primary-lookup-every-registered-target-composes-subquery-intersection
[spec-034-d6]: ../spec-034-permissions-0_0_10.md#decision-6--hidden-fk-semantics-row-exclusion-is-the-cascade-contract-resolver-level-nulling-stays-the-relation-contract
[spec-034-d7]: ../spec-034-permissions-0_0_10.md#decision-7--cascade-performance-lazy-subquery-composition--zero-added-round-trips
[spec-034-d8]: ../spec-034-permissions-0_0_10.md#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db
[spec-034-d9]: ../spec-034-permissions-0_0_10.md#decision-9--fields-scoping-validates-loudly-with-configurationerror

<!-- docs/builder/ -->
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[permissions]: ../../../django_strawberry_framework/permissions.py
[querysets]: ../../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
