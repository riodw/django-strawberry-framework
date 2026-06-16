# Optimizer review — `django-strawberry-framework` vs `strawberry_django` (competitive parity)

Reviewer pass: 2026-06-16. Goal per the maintainer: *"we want to be the best."* This is a head-to-head of our optimizer against `~/projects/strawberry-django-main/strawberry_django` (the `🍓` reference). Every claim is anchored to a file:line on both sides and the high-stakes ones were verified directly against source (not inferred). Code is unchanged since the last review (`fd21b948`); the G2 / Decision-5 / G3-deferral conclusions from that pass still hold and are not re-litigated here.

Headline: **on the mainstream path (concretely-typed schemas) we are already ahead** — we hold four advantages upstream simply does not have. **Upstream is ahead on capability breadth for advanced/polymorphic schemas** — five gaps, all already on our `BACKLOG.md`, none yet shipped. To be *unambiguously* best, close the breadth gaps in the priority order below without regressing the four wins (some of which are in tension with the gaps — see the cache/dynamism note).

## Scoreboard

| Capability | Us | Upstream | Winner | Evidence |
| --- | --- | --- | --- | --- |
| **Cross-request plan cache** | 256-entry LRU keyed by printed-AST + vars + model + path + origin; `cache_info()` | **none** — re-walks selections every request (per-request `cache` dict discarded) | **US (big)** | ours `optimizer/extension.py::_get_or_build_plan` / `_plan_cache`; upstream `optimizer.py:1206` `cache = cache or {}`, `:1580 optimize()`, no `lru_cache`/`OrderedDict` anywhere |
| **Strictness / N+1 detection** | off / warn / raise (`OptimizerError`) on unplanned lazy load | **none** — preventive only, never detective | **US (big)** | ours `extension.py` `strictness=`; upstream: no `OptimizerError`, the only `strict=` is `get_object_definition(strict=True)`, "n+1" only in a comment `optimizer.py:1382` |
| **FK-id join elision** | `{ rel { id } }` reads `<fk>_id` off the parent, **no join/prefetch**, resolver synth-stubs from `__dict__` | ensures the FK column is in `.only()` so the join/prefetch doesn't lazy-load — **still joins/prefetches** | **US (likely)** — *verify before headline* | ours `walker.py::_can_elide_fk_id` + `plan.fk_id_elisions`; upstream `optimizer.py:402-425` `inspector.only |= missing` (column inclusion, not elision) |
| **Field-metadata precompute** | `FieldMeta` frozen at **class-creation**, read from `definition.field_map` | `functools.lru_cache` on `get_model_fields` — cached but computed on **first request** | **US (modest)** | ours `field_meta.py::FieldMeta`; upstream `utils/inspect.py:49` |
| Windowed nested-prefetch pagination + `totalCount` window | yes (RowNumber/Count windows, deterministic order) | yes | **even** | ours `plans.py::apply_window_pagination`; upstream `pagination.py:209-282` |
| `select_related`/prefetch chains, `only()`, connector columns | yes | yes | even | both |
| `get_queryset` visibility → `Prefetch` downgrade | yes | yes (`run_type_get_queryset`) | even | ours `walker.py::_target_has_custom_get_queryset`; upstream `optimizer.py:549-557` |
| Async, multi-DB `.using()` passthrough, `.distinct()` guard | yes | yes | even | both |
| **Annotation hints** (`Meta.annotations` / `field(annotate=…)`, Info callables) | **none** | yes, incl. per-request `annotate=lambda info: …` | **UPSTREAM** | upstream `optimizer.py:103,130,155`, `with_resolved_callables`; ours: `OptimizerHint` is SKIP/select/prefetch/custom-Prefetch only |
| **GenericForeignKey** reads | **rejected** at `DjangoType` creation (`ConfigurationError`); `GenericRelation` *is* supported | resolved via `prefetch_related` + `GenericPrefetch` + content-type column inclusion | **UPSTREAM** | upstream `optimizer.py:1164-1168, 408-411`; ours: type-layer rejection (`tests/types/test_generic_foreign_key.py`) |
| **django-polymorphic / `select_subclasses`** | none | yes (poly prefix re-walk, `InheritanceManager`) | **UPSTREAM** | upstream `optimizer.py:843-850, 1056-1057, 1253-1267` |
| **Interface/union concrete-type narrowing (G3)** | **deferred** (no abstract optimizer entry; abstract return → `model_for_type` None → pass-through) | yes (`get_possible_concrete_types` + per-concrete re-walk) | **UPSTREAM** | upstream `utils/inspect.py:206-245`, `optimizer.py:1646-1661`; ours: `walker.py` `TODO(spec-035 Slice 3)` |
| **Per-request optimizer-off hatch** | none | `DjangoOptimizerExtension.disabled()` contextvar | **UPSTREAM** | upstream `optimizer.py:1730,1775,1798` |
| **Prefetch merging** (both-have-Prefetch) | **consumer-wins drop** (B8) — we do not merge | `PrefetchInspector.merge` unions `.only()`, merges querysets (`_optimizer_sentinel`, `allow_unsafe_ops`) | **trade-off** (see below) | ours `plans.py::diff_plan_for_queryset`; upstream `utils/inspect.py:248-387` |
| Model-property auto-optimization (`@model_cached_property` hints) | none | yes (`only`/`select_related`/`prefetch_related`/`annotate` on properties) | UPSTREAM | upstream `descriptors.py:55-58`, `optimizer.py:808-830` |
| Granular `enable_*` config toggles | strictness + per-relation hints | `OptimizerConfig.enable_only/select_related/prefetch_related/annotate/nested` | upstream (minor) | upstream `optimizer.py:106-132` |

## Where we already beat upstream — protect these

These are real, verified, and they are the *common-case* axes (any concretely-typed schema, which is the large majority of real Django GraphQL apps):

1. **Global plan cache (B1) is the crown jewel.** Upstream recomputes the entire selection-tree walk on *every request* (`optimize()` → `_get_model_hints()` with a throwaway per-request `cache` dict, `optimizer.py:1206/1580`). We walk once and serve from a 256-entry LRU forever after, with `cache_info()` for observability. For any high-RPS API serving repeated query shapes this is a categorical advantage, not a marginal one. **Recommendation:** lead the README/positioning with it — it is the single clearest "we are faster than `strawberry_django`" claim, and it's defensible with `cache_info()` numbers.
2. **Strictness / N+1 detection (B3).** Upstream has *no* detective mode — it cannot turn "no avoidable N+1s" into a CI gate. We can (`strictness="raise"`). This is a unique selling point; pair it with the `disabled()` hatch (gap #3 below) and you get the `audit_n1`-style "run both ways, assert query counts diverge" story upstream structurally cannot offer.
3. **FK-id join elision (B2).** We appear to actually *skip* the join for `{ rel { id } }` and synth a stub from the parent's `<fk>_id` in `__dict__`; upstream only guarantees the FK column is present so its join/prefetch doesn't lazy-load. **Caveat:** verify upstream truly never elides the relation before making this a headline marketing claim — the upstream mechanism at `optimizer.py:402-425` is column-inclusion (`inspector.only |= missing`), which strongly implies it keeps the relation, but confirm there's no id-only short-circuit elsewhere.
4. **Class-creation-time metadata precompute (B7).** Modest but real: ours is frozen at type creation; upstream's `lru_cache` warms on first request.

## Where upstream beats us — the gap list (all already on `BACKLOG.md`)

Ranked by impact × reachability for "be the best." Each maps to an existing backlog card, so this is sequencing, not new design.

1. **Annotation hints — highest impact.** `BACKLOG.md` `selection_aware_annotations` (+ `computed_field_optimizer_hints`). Computed/aggregate DB columns (`review_count = Count("reviews")`, `avg_rating = Avg(...)`) are extremely common; upstream injects `.annotate()` selectively *and* supports per-request `annotate=lambda info: …`. We have **no annotate path** — consumers must hand-write resolvers and lose optimizer cooperation. This is the gap most likely to lose us a head-to-head eval. **Design note (important for staying best):** upstream can't cache plans partly *because* annotate callables receive `Info` (per-request dynamic). Add annotations the cache-preserving way: static `Meta.annotations` expressions bake into the cached plan; `Info`-receiving callables mark the plan **non-cacheable** exactly like our `get_queryset` plans already do (`walker.py` marks `plan.cacheable = False` for custom `get_queryset`). That wins both axes — upstream gets neither.
2. **GenericForeignKey reads.** `BACKLOG.md` `generic_foreign_key_support`. Audit logs, comments, attachments, reactions — GFK is everywhere, and we *hard-reject* it at `DjangoType` creation today. Django 5.0's `GenericPrefetch` makes the heterogeneous-prefetch half tractable, and our floor is `Django>=5.2`, so the hard part is already solved upstream of us. High adoption value.
3. **Per-request optimizer-off hatch — best ROI (cheapest win).** `BACKLOG.md` `query_time_optimizer_disable`. Upstream's `disabled()` is a `ContextVar` + one early-return in the resolve hook (`optimizer.py:1775,1798`). For us it's ~20 lines and it composes with our strictness to deliver the "assert optimized vs unoptimized query counts diverge" CI test upstream can't write. **Ship this first** — lowest effort, immediate DX/CI payoff, and it's a visible parity checkbox.
4. **Abstract-return entry + interface/union narrowing (G3) — biggest, already scoped.** Upstream optimizes interface/union/polymorphic feeds (`get_possible_concrete_types` + per-concrete re-walk); we can't even *enter* the walker for an abstract return type (`_resolve_model_from_return_type` → `model_for_type` None → pass-through, per the spec-035 reachability proof). G3's deferral was correct — but note this is the *same* gap as polymorphic feeds and `polymorphic_interface_connections`. Closing the "abstract-return optimizer entry" card unlocks G3, polymorphic connections, and union types together. Our advantage when we build it: do the registry-only narrowing (not upstream's per-concrete-type re-walk) so it composes with the plan cache — the carry-forward requirements in spec-035 Decision 6/7 already pin this.
5. **django-polymorphic / `select_subclasses`.** `BACKLOG.md` `django_polymorphic_union_types`. Pairs with #4; same machinery.

## The one deliberate trade-off worth re-examining: prefetch merging

This is the most interesting "are we actually best?" question. When **both** the consumer and the optimizer target the same relation with a `Prefetch`, upstream *merges* — it adds the optimizer's deeper nested `select_related`/`only()` into the consumer's `Prefetch` (`PrefetchInspector.merge`, `utils/inspect.py:248-387`, with `_optimizer_sentinel`/`allow_unsafe_ops` to permit safe aggressive unions of its own prefetches). We do **consumer-wins drop** (B8, `plans.py::diff_plan_for_queryset`): the consumer's `Prefetch` wins outright and we add nothing under it.

Our stance is defensible as a permission-boundary safety choice (a consumer `Prefetch(queryset=…filter(...))` is a security scope we must not silently widen) — and spec-035 records it as deliberate. **But** for the common case where the consumer's prefetch queryset carries *no* custom filter (just `Prefetch("items")` or `Prefetch("items", queryset=Item.objects.all())`), dropping our nested plan means the consumer pays N+1 *below* their prefetch — exactly where upstream would have merged the optimization in. That is a real spot where "consumer-wins drop" is not "best."

**Recommendation:** add an opt-in *safe merge* — when the consumer's prefetch queryset has no `.filter()`/`.exclude()`/custom `get_queryset` boundary, merge our nested `select_related`/`only()` in rather than dropping (strictness can flag the dropped-and-now-N+1 case to find the affected sites). The spec already anticipates exactly this: *"revisit only behind a strict no-custom-filter merge precondition."* Promoting that to a card would close the last common-case spot upstream out-optimizes us, while keeping the safety guarantee where it matters.

## Suggested "be the best" sequence

1. **`disabled()` hatch** — cheapest, composes with our unique strictness story (quick win, parity checkbox).
2. **Annotation hints (static-cacheable + Info-callable-bypass)** — highest eval impact; the design that keeps our cache advantage intact.
3. **Safe prefetch-merge (no-filter precondition)** — closes the last common-case optimization gap; small, high-value.
4. **GenericForeignKey reads** — removes a hard adoption blocker; Django 5.0 `GenericPrefetch` does the heavy lifting.
5. **Abstract-return optimizer entry → G3 + polymorphic/union connections** — the big one; unlocks three backlog cards at once; build the narrowing registry-only so it composes with the plan cache.

Land #1–#3 and we are best-in-class on the mainstream path *and* have closed the cheap breadth gaps; land #4–#5 and there is no schema shape where `strawberry_django` optimizes and we don't.

## Caveats on this review

- The suite was **not** executed (no-pytest-after-edits rule); this is a static + source-comparison review.
- The FK-id-elision win (#3 in "where we beat") rests on upstream's mechanism being column-inclusion-not-elision — strongly indicated by `optimizer.py:402-425` but worth one direct confirmation before it becomes a public claim.
- Upstream line numbers are from the local checkout (`strawberry_django/optimizer.py`, 1823 lines, dated Apr 28); they drift with upstream releases — the *behavior* is the contract, the lines are evidence.
