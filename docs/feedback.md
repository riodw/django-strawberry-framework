# spec-035 close-out review — (1) performance & integration, (2) test compliance

Reviewer pass: 2026-06-16. Final pass before closing `035`. Since the last review (`fd21b948`) the only change is commit `f30e1a23`: a new `scripts/bench_plan_cache.py`, a README "Why it's fast" section, and BACKLOG edits — **the optimizer source is unchanged** since the G2/Decision-5 build. So Part 1 is a performance lens over the optimizer with the recent G2/Decision-5 integration + the new benchmark in view; Part 2 is placement compliance against `examples/fakeshop/test_query/README.md`. Suite not executed (no-pytest-after-edits rule).

Verdict: **ship it.** No performance regression on the hot path; Decision-5 is itself a performance *fix*; the benchmark is methodologically sound; the README's competitive claims are now verified (the FK-id claim I previously flagged checks out). Findings are framing nits + genuine "even faster" opportunities + one Part-2 placement judgment call (G1). The team also actioned my prior competitive review into BACKLOG (`safe_prefetch_merge` card + the annotation cache-design) — both are well-formed.

---

## Part 1 — Performance & integration

### 1a. Recent-change integration (G2, Decision-5) — net perf assessment

**G2 (`enable_only` gating) is zero-cost on the hot read path.** `_enable_only_for_operation(info)` runs **once per `plan_optimizations`**, i.e. only on a cache *miss*. On a cache *hit* the plan is served from the LRU and the walker never runs, so G2 adds nothing to the steady-state query path. Under a mutation/subscription it suppresses `.only()` so full rows load — slightly more columns in one query, but that is the correct trade: it prevents the deferred-refetch storm (N extra queries) that an `.only()`-projected mutation result would trigger on field access. Net: neutral on reads, a pathology-preventer on writes. Well-integrated.

**Decision-5 is a performance *fix*, not a cost.** The consumer-`.only()`-defers-FK guard converts a *silent per-row lazy load* (a real N+1 that strictness couldn't even see, because the relation was recorded as planned) into a loud, strictness-visible fallback. That is a latent-N+1 elimination. The per-row cost it adds is minimal: `_fk_attname_is_deferred` short-circuits on `attname in root.__dict__` (the loaded common case — one dict membership), and only reaches `get_deferred_fields()` on the rare deferred path. The hot path is guarded correctly.
- **Micro-opt (optional, low value):** on the common path `_build_fk_id_stub` touches `root.__dict__` twice — once for the `in` membership check (inside `_fk_attname_is_deferred`) and again for `getattr(root, attname)`. Fusing them (`val = root.__dict__.get(attname, _MISSING); if val is _MISSING: <deferred-check>`) would halve the per-row dict access. Nanoseconds per row; mentioned only for completeness — correctness already dominates.

### 1b. The benchmark script — methodologically sound, with framing caveats

`scripts/bench_plan_cache.py` is a genuine asset and the methodology is right: in-memory DB (never touches the tracked fixture), warm-vs-cold isolates the walk (`cold - warm` cancels identical DB + parse time), median (outlier-robust), discarded warmup, `cache_info()` as independent proof, and it honestly reports the non-cacheable shape (custom-`get_queryset` → 0 hits) rather than hiding it. Good.

Three caveats to record so the numbers aren't challengeable:
- **"Cold" measures *our* walk, not upstream's.** The script clears *our* cache to force *our* walker to re-run — a fair proxy for "the per-request walk the cache eliminates" and a real advantage (upstream has no cache, so it pays a per-request walk by construction). But `cold - warm` is *our* walk cost, **not a measured upstream delta** — upstream's walker is a different (plausibly heavier) implementation. The docstring is careful about this; the README's "~115 µs walk eliminated … over `strawberry-graphql-django`" risks reading as a head-to-head measurement. Tighten to "the per-request walk our cache eliminates (which upstream pays on every request)" — true, conservative, unchallengeable.
- **`speedup` is dataset-dependent; `walk µs` is the honest metric.** With `seed=3` the warm baseline is tiny, so `cold/warm` looks large; on production-sized data DB time dominates both and the ratio shrinks. The absolute `walk µs` is row-count-independent (it's the README's headline — correct). Just don't let the `speedup` column get quoted.
- **The README's "2,099/2,100 hits" doesn't reproduce from the default invocation** (`--iterations 1000 --warmup 50` → 1 miss + 1049 hits = ~1049/1050 per query). 2,100 implies ~2,050 iterations. Pin the exact command that produced the published numbers so they reproduce.

### 1c. The README "Why it's fast" claims — verified

- **FK-id join elision claim is correct** (this resolves my prior "verify before headline" caveat). Upstream resolves a forward FK with `OptimizerStore.with_hints(only=[path], select_related=[path])` (`optimizer.py:915-918`) — it **always `select_related`s (joins)** the related table, with no parent-FK-column short-circuit for an id-only selection. We read the parent's existing `<fk>_id` column and skip the join. So "we elide, upstream joins" is substantively true. **Wording nit:** upstream doesn't "load the FK column" — it joins the related row; say "upstream resolves it with a `select_related` JOIN; we read the parent's existing FK column and skip the join." (Magnitude is modest — one saved join per id-only FK — but real and it compounds.)
- **Cache claim is correct and is the crown jewel** (verified last pass: upstream re-walks every request, no LRU). Keep leading with it.

### 1d. Genuine "even faster" opportunities (not defects)

1. **The cache eliminates the walk but *not* the per-request key-build.** On every cache *hit*, `_get_or_build_plan` still calls `_build_cache_key` → `_print_operation_with_reachable_fragments` → `print_ast(operation)` before the lookup. It's memoized **per execution** (`_printed_ast_cache` ContextVar keyed by `id(operation)`), so it runs once per request for the first root resolver — but it runs *every request*, and the key is the full printed string (hashed in full on each fresh string). For deep queries `print_ast` of the whole operation is a non-trivial residual the cache does not remove. **Opportunity:** if Strawberry's document/validation cache yields a stable operation-node identity across requests for the same query (worth verifying), memoize the printed-AST key on the node via a `WeakKeyDictionary` so the per-request `print_ast` disappears too — turning a cache hit into a near-free lookup. This is the next real per-request win after the walk.
2. **Cache concurrency is correct but counters are approximate — credit + caveat.** The `move_to_end`-after-`get` race is explicitly `suppress(KeyError)`-guarded (good — they thought about it), and individual `OrderedDict` ops are GIL-atomic, so no corruption/crash under threaded/ASGI load. Residuals: `_cache_hits/_cache_misses += 1` are unlocked read-modify-writes (so `cache_info()` can under-count under concurrency — benign), and two threads on the miss path can both run the eviction quarter-sweep (benign over-eviction → a few extra misses). Fine for the GIL'd supported configs; worth a one-line docstring note that `cache_info()` is best-effort under concurrency, and a future flag for free-threaded (PEP 703) builds where dict-op atomicity no longer holds.
3. **Mutation plans are cached but rarely re-hit.** G2 builds a distinct (empty-`only_fields`) plan per mutation selection shape and caches it under the `mutation`-keyword key. Correct, but mutation operations vary more by shape than queries, so the mutation half of the cache will mostly miss — not a problem, just don't expect the cache hit-rate story to extend to the write side once `0.0.11` lands.

### 1e. BACKLOG perf cards (actioned from the prior review) — sound

Both new cards are well-specced; I validated their crux:
- **`selection_aware_annotations`** now carries the static-cacheable / `Info`-callable-non-cacheable design — exactly the way to add annotations without losing the cache (mark `plan.cacheable = False` for the callable arm, reusing the `get_queryset` path). This is the design that wins both axes; keep it.
- **`safe_prefetch_merge`** correctly gates merge on a *trivial* consumer `Prefetch` queryset (no filter/exclude/annotations/slicing/distinct/non-default-ordering/`.using()`/`to_attr`). One refinement to pin when it's specced: a consumer `.only()`/`.defer()` on the `Prefetch` queryset is row-set-identical (so it'd qualify) but interacts with the merged projection — make the `only()`-union rule explicit for that case (union, never narrow below what a downstream resolver reads), since the precondition list is framed around row-set semantics and `.only()` is a column concern.

---

## Part 2 — Test compliance with `test_query/README.md`

The README's coverage ladder: **(1) live `/graphql/` HTTP (`test_query/`) is mandatory if the line is reachable by a real query against the fakeshop schema → (2) in-process fakeshop (`examples/fakeshop/tests/`) → (3) package-internal (`tests/`) only when genuinely unreachable.** Mock only when impossible. Assessed per guard:

**G2 — compliant.** The QUERY path (`enable_only=True`, normal projection) is exercised by **every existing live optimizer test** in `test_query/` — so G2's live-reachable half is already earned live (implicitly). The mutation/subscription half (`enable_only=False`) is **genuinely unreachable**: the fakeshop schema ships no mutations until `0.0.11`. Package-internal placement (`tests/optimizer/test_walker.py` + `test_extension.py`) is correct, and the spec records the mandatory live-test handoff to the first mutation card. No action.

**Decision-5 — compliant.** The loaded-FK common path (`_fk_attname_is_deferred → False`) is exercised by every existing live FK-id-elision query (e.g. `test_scalars_api.py`, `test_library_api.py`). The consumer-`.only()`-defers-FK path is **unreachable against the current fakeshop schema** — confirmed: there is **no `.only()` in any fakeshop `schema.py`/`services.py`**. So the deferred-FK tests are correctly package-internal (`tests/types/test_resolvers.py`, beside the existing B2 elision unit tests). *Minor note:* the QUERY arm of `test_fk_id_elision_falls_back_when_consumer_only_defers_fk` is the one piece that *could* be made live by adding a fakeshop resolver returning `Model.objects.only("name")` with a `{ rel { id } }` selection — but a consumer that projects away an FK then asks for its id is contrived enough that the package-internal placement is defensible. Optional, not required.

**G1 — the one placement flag.** The G1 *pass-through* behavior (the new `_result_cache is not None → return` guard's **TRUE** branch) is tested only with a **synthetic in-process resolver** (`schema.execute_sync` + `django_assert_num_queries`) in the **package-internal** tree (`tests/optimizer/test_extension.py`), *not* over `/graphql/`. The guard's FALSE branch (normal, not-yet-evaluated) is covered live by every existing query, but the TRUE branch — the actual new behavior — is **reachable in principle**: a one-line fakeshop resolver that does `qs = Item.objects.all(); len(qs); return qs` would let a `client.post("/graphql/")` + `CaptureQueriesContext(1)` earn it live, exactly the README's "first place to add a test" intent. The pure-unit assertion (`_optimize` returns the same instance) correctly belongs package-internal; it's the *behavioral num-queries* assertion that is a tier-1/tier-2 candidate. **Recommendation:** either add a minimal fakeshop "evaluate-then-return" resolver + a live `CaptureQueries` test, or record an explicit waiver in the spec/test that evaluate-then-return is a consumer anti-pattern not worth a permanent fakeshop surface. Today it sits between the two without the rule's preferred live coverage and without a recorded waiver — that's the gap to close before sign-off.

**`test_library_api.py +6`** is the deferred-G3 carry-forward TODO comment (not a test) — consistent with the spec's "no new live test in this card." Fine.

### Part-2 bottom line

G2 and Decision-5 placements are README-compliant (live half covered by existing live tests; the synthetic-only half is genuinely unreachable). **G1 is the single open item:** its pass-through behavior is live-reachable with a trivial fakeshop resolver, so the README prefers a live test — add one or record the waiver. Everything else is clean.

---

## Close-out checklist

- [ ] G1: add a live `/graphql/` "evaluate-then-return → one query" test against a minimal fakeshop resolver, **or** record an explicit waiver (Part 2).
- [ ] README: tighten the FK-id wording ("`select_related` JOIN", not "loads the FK column") and the cache-benchmark framing ("the walk our cache eliminates, which upstream pays per request"); pin the exact `bench_plan_cache.py` invocation behind the published hit numbers (Part 1c).
- [ ] (Optional) `cache_info()` docstring: note counters are best-effort under concurrency (Part 1d-2).
- [ ] (Optional, future win) memoize the printed-AST cache key across requests if Strawberry's document cache gives stable node identity (Part 1d-1).
- [ ] Run the optimizer suite at the 100% gate before the joint `0.0.10` cut (not done in this review).

No blocker for closing `035`'s functional scope — G2 + Decision-5 are correct and performant. The G1 live-test/waiver decision is the only thing the README rule strictly wants resolved.
