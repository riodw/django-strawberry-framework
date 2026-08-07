# Spec: Optimizer O4 — Nested Prefetch Chains

Deliberation for this spec lives in its companion [rationale file][spec-003-rationale]: the implementation shapes it proposed and where the shipped code departed from each, the pre-O4 code it quoted, the per-file insertion-point guidance it carried for its builder, the staging convention its TODO anchors served, the documentation obligations it declared and discharged, and — where the package later corrected or outgrew something it asserted — what replaced that assertion and which alternative replacement lost. Read the spec for what holds; read that file for why it holds. Why the O4 record was split out of `docs/SPECS/spec-002-optimizer-0_0_2.md` at all is that spec's own deliberation and is recorded in [its rationale file][spec-002-rationale], not restated here.

## Problem statement
`docs/SPECS/spec-002-optimizer-0_0_2.md` rebuilds the optimizer around a root-gated selection-tree walk. O1, O2, O3, O5, and O6 make that walk effective for depth-1 relation selections; by itself it plans the relation it is looking at and stops there. O4 is the slice that plans nested relation paths, so a query like `{ allCategories { items { entries { value } } } }` is optimized at the root instead of falling back to per-row lazy loads at the second relation level.

The walk carries a Django lookup `prefix` so a nested plan entry can name its path from the root. O4's change is to recurse into a relation's own child selections instead of collecting only their scalar leaves, and to emit depth > 1 relation chains out of that recursion.

## End-goal context
`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` treats O4 as the last foundation slice. B1 plan caching, B7 field metadata, B3 strictness, B4 optimizer hints, B5 context stashing, B2 [FK-id elision][glossary-fk-id-elision], and B6 [schema audit][glossary-schema-audit] all build on the optimizer's planning surface — the `OptimizationPlan` the walk produces, the planning type's field metadata the walk plans against, or both — so O4 extends the planner without breaking these contracts:

- Cached plans must remain reusable; request-dependent nested `Prefetch` querysets must set `plan.cacheable = False`.
- The planning type's field map (B7) is re-resolved at every recursion level — the walk opens each entry by resolving the field map for the model it is descending into, so a nested branch plans against its own target's metadata. Recursion must preserve that property rather than carrying the root's map down.
- [`Meta.optimizer_hints`][glossary-metaoptimizer-hints] (B4) must apply at nested levels, not only root fields.
- `get_queryset` downgrades (O6) must compose with nested child plans.
- B2 FK-id elisions and B3 strictness sentinels must use walker-produced branch-sensitive resolver keys, because nested paths make a bare field name ambiguous; Django lookup paths are only for debugging/B8 (see "Lookup paths vs resolver sentinel keys" below).
- B8 [queryset diffing][glossary-queryset-diffing] normalizes `select_related` paths and `Prefetch.prefetch_to` paths, so O4 must preserve stable lookup identities.

## Plan shape
`OptimizationPlan` carries the directives one queryset needs. The bags O4 owns are:

- `select_related`: single-valued relation paths for `QuerySet.select_related`.
- `prefetch_related`: strings or `Prefetch` objects for `QuerySet.prefetch_related`.
- `only_fields`: scalar paths for `QuerySet.only`, relative to the queryset this plan applies to — not to the root — so a child plan's paths are queryset-local.
- `fk_id_elisions`: branch-sensitive resolver keys whose selected target primary key can be served from the source row. Bare relation paths are not sufficient (see "Resolver sentinel keys" below).
- `planned_resolver_keys`: the resolver keys B3 strictness may treat as covered by this plan.
- `cacheable`: whether the plan can be stored in the extension [plan cache][glossary-plan-cache].

The plan carries further fields that later slices added — per-path resolver-key ledgers for B8 reconciliation, and the frozen membership sets computed when the plan is finalized at handoff. Those belong to `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` and `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` and are not restated here.

Planning starts from the root selection set with an empty Django lookup prefix and with the runtime response path of the root field being planned — `("allEntries",)` for a query rooted at `allEntries`, and empty only for a caller that supplies no `info` at all. Every nested walk extends both. A nested walk on the same query extends the Django prefix (`item__category`); a walk across a prefetch boundary resets it (see "Prefetch-boundary recursion" below). The root runtime path is the root field's own response key because the resolver side reconstructs the same path from `info.path`, which includes the field it is resolving: a walker that started from an empty path would key every elision one segment short of what the resolver asks for, and no elision would ever match. The pre-O4 dispatch shape, and where the shipped walker departed from it, are in the [rationale file][spec-003-rationale].

`OptimizationPlan.prefetch_related` accepts `Prefetch` objects. `docs/SPECS/spec-002-optimizer-0_0_2.md` describes O4 as emitting `prefetch_related("items__entries")` style chains; this spec narrows that to nested `Prefetch` objects whenever a child queryset needs its own optimization (custom `get_queryset`, child `only_fields`, child FK-id elisions, or further nested branches). Plain string lookups remain valid only when the child branch carries no per-queryset state.

## Desired behavior
Each query count and plan shape below assumes no type on the chain overrides `get_queryset`. A single-valued link to a type that does is downgraded by O6 and leaves the `select_related` chain for a `Prefetch` of its own, so both the shape and the count change for it. What the downgrade does not change is O4's dispatch: the relation is planned by the same recursion whichever of the two branches it takes.

Depth-2 many-side chain:

- GraphQL: `{ allCategories { items { entries { value } } } }`
- Root queryset: `Category.objects...`
- SQL target: 3 queries total with optimizer enabled — categories, prefetched items, prefetched entries.
- Plan shape: root prefetch covers the full `items__entries` path, expressed as `Prefetch("items", queryset=Item.objects.prefetch_related(Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))))` for the query shown. If scalar fields on `items` are also selected, those fields and the outer connector (`category_id`) belong to the `Item` child queryset, not the root `Category` queryset.

Depth-3 single-valued chain:

- GraphQL: `{ allEntries { item { category { name } } } }`
- Root queryset: `Entry.objects...`
- SQL target: 1 query total with optimizer enabled via `select_related("item__category")`.
- Plan shape: root `select_related` includes the nested path and `only_fields` includes the FK columns and selected scalar columns needed to hydrate the joined rows: `["item_id", "item__category_id", "item__category__name"]`.

Mixed chain:

- GraphQL: `{ allCategories { items { category { id } entries { property { name } } } } }`
- The prefetch branch must optimize the `Item` queryset internally:
  - `items.category` is a forward FK on `Item` and the only target selection is `id`, so the **child** plan should record an FK-id elision on `category` (resolved against `Item.category_id` without a JOIN).
  - `items.entries` is a reverse FK; the child plan emits a nested `Prefetch("entries", queryset=...)` whose inner plan select-relates `property`.
- Net result: 1 query for `Category`, 1 prefetch for `items` (no `category` JOIN), 1 prefetch for `entries` with `property` joined in. Three queries.

This example exercises the contract that nested branches inherit the same dispatch logic the root walker uses, including B2.

## Implementation design
O4 splits recursion into two cases, reached from one selection-walk entry point: the dispatch decision lives in the relation branch, and both the cardinality verdict and the two hint overrides below route through it, so a relation is planned the same way however it was decided. A nested Relay connection selection is a third case and is not O4's: it is recognized before the relation branch and planned by `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`.

### Same-query recursion for single-valued paths
Forward FK and forward OneToOne relations that remain `select_related` stay in the root query. Recursing through these paths keeps using the Django lookup `prefix`:

- Add the source FK column to `only_fields` using the current prefix.
- Apply the FK-id elision check at this level; B2 short-circuits before recursion. The FK-column append above must stay **ahead** of this short-circuit: an elided branch returns without planning a join, and the resolver that serves it reads the source row's FK column, so appending the column after the short-circuit would leave it unprojected and silently reintroduce the N+1 the elision exists to remove. Nothing enforces the order but the order itself.
- Add the selected relation path to `select_related`.
- Recurse into the related model with the prefix extended by that path. The recursive call handles scalars and nested relations together — a scalar-only collection step at this position drops every nested relation silently.

This is the path that makes `entry > item > category` collapse into one SQL query. The shape this branch was proposed in, and where the shipped code departed from it, are in the [rationale file][spec-003-rationale].

### Prefetch-boundary recursion for many-side and downgraded paths
Reverse FK, M2M, and O6-downgraded forward relations cross a queryset boundary. Child scalar [`only()`][glossary-only-projection] paths must not be pushed into the root queryset. Instead:

- Add the source FK column to the **parent** plan's `only_fields` using the current prefix, exactly as the same-query branch does. Guard the append on the relation carrying a source-row attribute name (`attname`) at all: the reverse descriptors — reverse FK, reverse OneToOne, reverse M2M — carry none, so nothing is appended for them. The case that makes the append load-bearing is a forward FK or OneToOne that reaches this branch instead of the same-query one, whether downgraded to a `Prefetch` by O6 or forced across by a `force_prefetch` hint: Django matches those prefetched rows by reading that column off each parent, so omitting it from the parent projection costs a deferred load per parent row and reintroduces on this branch the N+1 the slice exists to remove.
- Build a child queryset for the related model, based on that model's own default manager. When O6 requires the target type's `get_queryset(queryset, info)`, invoke it through the framework's shared visibility boundary rather than calling the hook directly, so sealing, degradation, and the sliced-queryset allowance are decided at one seam instead of per caller; that boundary's own rules are `docs/SPECS/spec-045-visibility_boundary-0_0_14.md`'s and are not restated here.
- `plan_relation` decides the traversal kind and constructs nothing. Queryset construction belongs to a single child-queryset seam, so a custom `get_queryset` runs exactly once per prefetched relation and the prefetch branch owns applying the child plan.
- Build a child `OptimizationPlan` from the relation's child selections using the related model as the child root and an empty prefix.
- Treat the relation's lookup path as relative to the plan/queryset currently being built. A root plan may legitimately hold a lookup such as `category__properties` after same-query recursion crosses into a later prefetch boundary, but once a child `Prefetch` queryset is created, that child plan resets its prefix to empty and inner `Prefetch` objects use queryset-local paths such as `entries`, not root-global paths such as `items__entries`.
- Add connector columns to the child plan **after** walking (the walker only knows about selected columns; the connector columns must be present even if the schema does not expose them). Inject nothing at all when the child plan appended no `only_fields`: with no child projection Django fetches full rows and the connectors come for free, so an unconditional inject would turn that full-row fetch into a one-column projection. Otherwise, per cardinality:
  - reverse FK or reverse OneToOne (`one_to_many` / `reverse_one_to_one`): the forward FK back to the parent — `parent_field.field.attname` (e.g. `Item.category_id` when prefetching `Category.items`). The walker starts from the reverse `ManyToOneRel` / `OneToOneRel`, so `.field` is the access path to the actual `ForeignKey` / `OneToOneField`.
  - forward FK / OneToOne demoted to Prefetch by O6: the target field Django will match against — `parent_field.target_field.attname`. This is usually the target PK but must preserve `to_field` correctness.
  - M2M (`many_to_many`): the target PK — `parent_field.related_model._meta.pk.attname`. Django handles the through-table query.
- Apply the child plan to the child queryset.
- Wrap the result in a `Prefetch` whose lookup segment is the relation's **instance accessor**, not its field name, prefixed by the current lookup prefix. Django's `prefetch_related` resolves a lookup by `getattr` on the instance, so a reverse relation declared without `related_name` — field name `book`, accessor `book_set` — is reachable only under the accessor; planning the field name raises `AttributeError: ... invalid parameter to prefetch_related()` on every optimized query over such a relation. Only the string Django consumes uses the accessor: plan keys, resolver identities, and `select_related` paths stay in field-name vocabulary.
- Append the `Prefetch` to the parent plan.
- If the child queryset came from a custom `get_queryset` *or* the child plan has any nested `Prefetch` whose inner queryset is request-dependent, propagate `cacheable=False` to the parent plan. Set the flag for the custom-`get_queryset` case **before** the child queryset is built, so it survives a child build that degrades instead of completing.

For a default branch with no child plan and no child `only()` projection, a plain string lookup is still acceptable — but the simplest implementation always emits a `Prefetch`, which is semantically equivalent. Prefer `Prefetch` for uniformity with B8 diffing (which inspects `prefetch_to`).

The shape this branch and its two helpers were proposed in, and where the shipped code departed from each, are in the [rationale file][spec-003-rationale].

### Hints are leaf operations
[`OptimizerHint`][glossary-optimizerhint]`.prefetch(obj)` lets the consumer hand in their own `Prefetch` instance. O4 must not recurse into that relation's child selections — the consumer's queryset is the source of truth, including any `only()` and nested prefetches it carries. A hint-supplied `Prefetch` is a leaf.

`OptimizerHint.prefetch_related()` (no `obj`) and `OptimizerHint.select_related()` both route through the two recursive paths above, so nested selections under a hinted relation are optimized exactly as an unhinted relation's are. A hint decides which of the two paths a relation takes; it never changes what that path does.

## Lookup paths vs resolver sentinel keys
O4 makes bare field-name sentinels insufficient.

Keep two identities separate:

- **Django lookup paths**: strings such as `items__entries` or `item__category`. These are useful for debug output and B8 queryset diffing.
- **Resolver sentinel keys**: branch-sensitive identities used by B2 FK-id elision and B3 strictness when a resolver runs. These must distinguish aliases, sibling branches, parent types, and root fields.

Do not try to derive resolver sentinel keys from `Prefetch` objects after planning. A `Prefetch` only carries Django lookup strings and a queryset; it does not retain the parent [`DjangoType`][glossary-djangotype], GraphQL response aliases, or selection-branch identity. The walker has that information while it traverses the selection tree, so it should record resolver keys as part of planning.

### Lookup-path flattening
B8 needs a helper that flattens relation lookup paths, and it lives in `plans.py`. It recurses through the lookups attached to a nested `Prefetch`'s own queryset to arbitrary depth, not just one child level, and it returns the union of the plan's `select_related` strings and every flattened prefetch path, each nested level joined onto its parent under Django's lookup separator. The shape it was proposed in, and where the shipped helper departed from it, are in the [rationale file][spec-003-rationale].

### Resolver sentinel keys
A bare field name is not a usable elision key. If two unrelated parent types both expose a `category` field and only one of them elides, both forward resolvers see `"category"` in `info.context.dst_optimizer_fk_id_elisions` and the wrong one serves a stub. Nesting compounds it: `category` selections at different depths, under aliases, on sibling branches, and under different parent types all collide on one name.

Parent-type + field-name is necessary but not sufficient: it fixes unrelated parent-type collisions, but it still leaks when two sibling/root branches resolve the same `DjangoType.field` with different selection sets. The resolver key therefore needs both:

- the parent type and Django field name, which the resolver closure can know because relation resolvers are attached per type and each closure binds its own;
- the GraphQL response path branch, with list indexes stripped, so aliases and sibling root fields stay distinct.

Thread the runtime response path through the walk alongside the Django `prefix`, taking each segment from a selection's alias or, where it has none, its name. Duplicate selections of one field are merged by underlying field name before planning, so the merge must preserve every response key the merged node represents: a selection reachable under more than one response key carries one resolver identity per key, never a single identity for the merged node. (`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` multiplies the same fan-out over nested-connection runtime prefixes.) Do not collapse two branches into one elision key unless their selection sets are equivalent for that optimization.

The key format is `<ParentType>.<field>@<a.b.c>`: the parent type's `__name__`, a `.`, the Django field name, an `@`, then the runtime-path segments joined on `.`. Where there is no parent type the key drops that prefix and reads `<field>@<a.b.c>`. It is one stable identity that survives nesting, aliases, sibling branches, and parent-type collisions. The resolver side reconstructs the same key when it runs and tests membership in `info.context.dst_optimizer_fk_id_elisions`. The two shapes this key and its resolver-side check were proposed in are in the [rationale file][spec-003-rationale].

The resolver side derives its half of the key by walking `info.path` back to the root, dropping numeric list indexes and keeping response keys, aliases included. The walker side must use the same response-key convention.

B3 strictness reads a resolver-key collection of its own, `OptimizationPlan.planned_resolver_keys`, populated by the walker alongside the lookup-path collection. Never answer a resolver strictness check from flattened lookup paths; lookup paths and resolver keys answer different questions.

The two sides of this protocol are asymmetric in their inputs and identical in their output. The walker is the only code that can see merged GraphQL selections before planning; the resolver is the only code that can reconstruct the runtime response branch from `info.path`. That asymmetry is in what each side reads, not in how the key is spelled, so the key format and the runtime-path derivation are ONE shared implementation both sides import — never two mirrored private copies held in step by an instruction to keep them matching.

## Interactions with shipped beyond slices
### B1 plan cache
Nested `Prefetch` objects that embed request-dependent `get_queryset(queryset, info)` results are not cacheable. Any recursive branch that calls a custom `get_queryset` must set the root plan's `cacheable` to `False`. A child plan's own `cacheable` propagates upward with the rest of its resolver metadata when the parent absorbs it, and that propagation belongs to the single absorb step rather than to each call site, so a later third absorb site cannot forget it.

### B3 strictness
Strictness must treat nested optimized relations as planned. Querying `items { entries { value } }` does not warn or raise for `entries`, because the resolver key for that `entries` branch is covered by the root plan. The extension stashes the walker-produced resolver-key set for B3, and separately stashes the flattened lookup paths for introspection/debugging.

### B4 optimizer hints
Hints are honored at every recursion level:

- `OptimizerHint.SKIP` suppresses planning for the nested relation branch (no recursion).
- `force_select` takes the same-query recursion for a single-valued relation, and is rejected outright for a many-side one, which Django cannot `select_related` at all. It still yields to O6: a target type that overrides `get_queryset` crosses the prefetch boundary despite the hint, because the hint chooses between the two paths and cannot suppress a visibility hook.
- `force_prefetch` creates a prefetch boundary even when the cardinality dispatch would select; it follows the same prefetch-boundary recursion path as a natural many-side prefetch, and it is the second route by which a forward relation reaches that branch.
- `prefetch(obj)` is a leaf — do not walk the relation's child selections.

### B2 FK-id elision
FK-id elision can fire inside nested child querysets, but only with the branch-sensitive resolver-key identity above and the same four safety guards the depth-1 elision holds: target primary key selection only, FK points at the target primary key, no custom `get_queryset`, and no custom id/PK resolver.

The prefetch-boundary case is interesting: a forward FK *inside* a prefetched child queryset can still elide because the child queryset already loaded the source row's `<field>_id`. The recursive walk on the child plan handles this naturally — it dispatches through the same B2 branch.

### B8 queryset diffing
B8 diffs plan output against optimization already on the consumer's queryset. O4 keeps nested lookup normalization straightforward by giving B8 the flattening helper above to flatten:

- `select_related` strings such as `item__category`;
- plain prefetch strings such as `items__entries`;
- nested `Prefetch` objects by combining the outer `prefetch_to` with inner queryset `_prefetch_related_lookups`.

## Test plan
Walker unit tests in `tests/optimizer/test_walker.py`:

- `test_plan_emits_nested_prefetch_chain_depth_2` for `Category > items > entries` — assert the outer entry is a `Prefetch("items", queryset=...)` whose inner queryset's `_prefetch_related_lookups` contains an `entries` `Prefetch`.
- `test_plan_emits_nested_select_related_chain_depth_2` for `Entry > item > category` — assert `select_related` covers exactly `item` and `item__category`, and `only_fields` covers `item_id`, `item__category_id`, `item__category__name`.
- `test_plan_combines_prefetch_boundary_with_inner_select_related` for `Category > items > category` — outer `Prefetch("items", ...)`, inner queryset's plan select-relates `category` (or, when `{ id }` only, records an FK-id elision instead).
- `test_plan_propagates_uncacheable_nested_custom_get_queryset` — nested target type overriding `get_queryset` flips root plan's `cacheable` to `False`.
- `test_plan_honors_optimizer_hints_at_nested_depth` — `OptimizerHint.SKIP` on a depth-2 relation suppresses its branch entirely.
- `test_plan_honors_prefetch_obj_hint_does_not_walk_inner_selections` — explicit `prefetch_obj` is appended verbatim regardless of selections under it.
- `test_plan_records_nested_fk_id_elision_with_resolver_key` — id-only nested forward FK lands in `fk_id_elisions` keyed by parent type, field name, and runtime branch.
- Fragment, alias, and directive variants for a nested relation branch, reusing the existing synthetic selection helpers (`_sel`, `_inline_fragment`, `_fragment_spread`).

Extension integration tests in `tests/optimizer/test_extension.py`:

- `test_optimizer_strictness_accepts_nested_planned_relation`: strictness `"raise"` does not raise for a nested relation covered by O4.
- `test_optimizer_nested_prefetch_with_custom_get_queryset_marks_uncacheable`: the combined O6 + O4 path flips the cache flag.

The query-count rows belong to the live tier, because they are reachable through a real query against the example project (`AGENTS.md` "Test through real usage"); a package-level stand-in for a live-reachable row is retired by the live row that replaces it:

- a depth-2 reverse-FK chain, `{ allCategories { items { entries { value } } } }`, executes in 3 queries over `/graphql/`;
- a depth-2 forward-FK chain, `{ allEntries { item { category { name } } } }`, executes in 1 query where no type on the chain overrides `get_queryset`, and pays one round trip per O6-downgraded link where one does. Pin whichever count the example project's own types produce, and derive it from a real run.
- a nested id-only branch does not elide a same-name relation branch elsewhere. Cover both leak axes: a sibling *root* field, and a different *parent type*.

Use the real fakeshop service seeders (`services.seed_data(n)`) for database tests. The four-model graph `Category → Item → Entry → Property` covers every cardinality the spec exercises.

Resolver-focused tests in `tests/types/test_resolvers.py`:

- The B2 stub/null tests key on branch-sensitive resolver keys, not bare field names.
- `test_b2_forward_fk_id_elision_does_not_leak_across_parent_types` for the parent-type leak a bare field name allowed.
- A runtime-path helper test that proves numeric list indexes are stripped and aliases/response keys are preserved.

## Definition of done
O4 is complete when:

- Depth > 1 many-side traversal is optimized from the root queryset.
- Nested single-valued traversal emits `select_related` chains, planned by the same recursive walk that plans the root rather than by a scalar-only collection step that drops nested relations.
- Prefetch boundaries carry child queryset optimization without pushing invalid child `only()` paths onto the root queryset, and connector FK columns are injected automatically.
- O6 custom `get_queryset` branches compose with nested child plans and correctly mark plans uncacheable.
- B2 and B3 context sentinels use branch-sensitive resolver identities (parent type + field + runtime response path, or an equivalent scheme) and do not leak across siblings, parent types, aliases, or root fields.
- The `lookup_paths` flattening helper exists on `plans.py` for B8/debugging, recurses through nested `Prefetch` objects to arbitrary depth, and is kept separate from resolver strictness keys.
- The walker, extension, live, and resolver tests above pass.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-metaoptimizer-hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit

<!-- docs/SPECS/ -->
[spec-002-rationale]: appx/spec-002-optimizer-0_0_2-rationale.md
[spec-003-rationale]: appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
