# BACKLOG.md

## Purpose

This file tracks the strategic-differentiation design surface where `django-strawberry-framework` can be **strictly better** than both `graphene-django` and `strawberry-graphql-django` — not just on-par.

Roadmap parity with the inspirations is tracked in [`KANBAN.md`][kanban]. **`BACKLOG.md` is for strategic differentiation** — cards neither inspiration ships cleanly that we should consider pulling onto the roadmap once parity items have landed.

Each card below is **an idea, not a commitment**. No card carries a target version. Cards graduate into `KANBAN.md` when scheduled. Every card carries **Realistic** / **Impact** / **Difficulty** scores out of 10.

Cards are grouped by subsystem. Group order and card order within groups carry no priority meaning.

---

## Errors

### `typed_error_envelope_and_code_registry`

**Realistic**: 9/10 — Typed Strawberry classes + a code registry are known patterns; the spec-aligned path format is a constraint, not a risk.

**Impact**: 8/10 — Major client-DX win; the dependency hub roughly eight other cards emit into.

**Difficulty**: 3/10 — Envelope shape + registry decorator; small slice now that adapters and i18n are split out.

**Source**: item 19 (typed error-code envelope), core half.

**What we'd do**: a typed, structured error shape that every other card emits into, plus a code registry.

**Spec**:

```python path=null start=null
@strawberry.type
class FieldError:
    path: list[str | int] | None   # GraphQL-spec-aligned path segments, e.g. ["items", 0, "quantity"]
    code: str                      # "validation.unique", "permission.denied", "dst.rate_limit.exceeded"
    message: str                   # human-readable; localized via the i18n hook card
    params: JSON                   # JSON-serializable templating values ({"min": 1, "max": 99})
```

- `path` uses the GraphQL spec's error-path convention (array of string and int segments), **not** a dotted string — clients reuse their existing `errors[].path` handling code.
- Codes come from a package registry that consumers extend via `@register_error_code("payment.declined")`.
- The `dst.*` namespace is **reserved for package-emitted codes**. Consumer registration inside `dst.*` raises `ConfigurationError`. Duplicate registration of any code raises `ConfigurationError` at import time.
- `params` values must be JSON-serializable; the registry validates declared param shapes where provided.
- The mutations cluster's `errors: list[FieldError]` envelope adopts this shape; it is the single error surface for mutations, DoS rejections, rate limits, export errors, and matrix errors.

**Out of scope here**: Form/DRF adapters (`form_and_serializer_error_adapters`) and message localization (`error_message_i18n_hook`).

**Composes with**: nearly everything — `cost_limit_extension`, `depth_limit_extension`, `rate_limit_extension`, `dos_policy_stack_framework`, `tabular_export_of_list_fields`, `matrix_dimensions_and_measures`, `snapshot_token_protocol`, `drf_serializer_mutations`. Ship this card early; its `code`/`params` shape is load-bearing for all of them.

### `form_and_serializer_error_adapters`

**Realistic**: 9/10 — `form.errors.get_json_data()` and DRF `ValidationError.detail` expose everything needed.

**Impact**: 6/10 — Required for the mutations story; invisible until mutations land.

**Difficulty**: 2/10 — Two mapping functions plus nested-path handling.

**Source**: item 19, adapter half.

**What we'd do**: lossless mapping from Django Form and DRF Serializer validation errors into the `FieldError` envelope.

**Spec**:
- Django Forms: map `form.errors.get_json_data()` (which carries per-error `code`) into `FieldError`, preserving field names as path segments and `NON_FIELD_ERRORS` as `path=None`.
- DRF: map `ValidationError.detail` — including its `code` attribute, nested-serializer dicts, and `ListSerializer` index errors — into path segments (`["items", 0, "quantity"]`).
- Unknown/missing codes map to `validation.invalid` rather than inventing codes.
- Adapter functions are public (`errors_from_form(form)`, `errors_from_serializer(serializer)`) so consumer-authored mutations can reuse them.

**Composes with**: `drf_serializer_mutations` (its primary consumer), `typed_error_envelope_and_code_registry`.

### `error_message_i18n_hook`

**Realistic**: 10/10 — Django gettext is the whole mechanism.

**Impact**: 4/10 — Matters to localized products; zero cost to everyone else.

**Difficulty**: 1/10 — Lazy templates + per-request locale; near-trivial.

**Source**: item 19, localization half.

**What we'd do**: localize `FieldError.message` through Django's `gettext` per request locale.

**Spec**:
- Registry entries carry a lazy translatable message template; `params` interpolate post-translation.
- `code` and `params` are **never** localized — clients branch on `code`, render `message`.
- Locale resolution follows Django's standard request-locale machinery; no package-specific locale plumbing.

**Composes with**: `typed_error_envelope_and_code_registry`.

---

## Optimizer

### `selection_aware_annotations`

**Realistic**: 9/10 — The walker already does selection-tree injection for `only()`/`Prefetch`; annotations follow the same pattern.

**Impact**: 7/10 — Real per-query perf win for the common computed-column case; nobody else does it.

**Difficulty**: 4/10 — Three walker/plan/assembly sites plus the filter/order-aware trigger and fan-out detection; the `Info`-callable arm adds a plan-cacheability marking that reuses the existing `get_queryset` non-cacheable path.

**Source**: item 2; the `Info`-callable annotate arm + cache-preservation marking added from the competitive-parity review (2026-06-16).

**What we'd do**: declare annotations in `Meta.annotations`; the optimizer injects `.annotate()` only when the annotation is actually needed.

**Spec**:

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

- Injection triggers when the annotation is needed by **any** of: (a) the GraphQL field is in the selection set, (b) an active filter from `Meta.filterset_class` references it, (c) an active `orderBy` from `Meta.orderset_class` references it. Selection-only injection is incorrect — filtering or ordering on an unselected annotation must still inject it.
- Annotation names colliding with concrete model field names raise `ConfigurationError` at finalization.
- Fan-out detection: when an aggregate annotation crosses a many-join **and** the plan contains another multi-valued join on the same root, emit a build-time warning recommending `distinct=True` (same fan-out contract as `matrix_dimensions_and_measures`).
- Injection happens in the existing walker/plan/queryset-assembly sites alongside `only()` and `Prefetch` injection.
- **Static expressions are cacheable; `Info`-receiving callables are not — the differentiator.** Plain ORM expressions in `Meta.annotations` (`Count("reviews")`) bake into the cached plan at zero per-request cost. To reach parity with upstream's per-request `field(annotate=lambda info: …)`, also accept an `Info`-receiving callable form; any plan that resolves such a callable is marked **non-cacheable** (`plan.cacheable = False`), reusing the exact mechanism plans with a custom `get_queryset` already use. This wins both axes at once: upstream cannot cache plans *at all* partly **because** its annotate callables take `Info`, so isolating the dynamism to the callable arm keeps our plan-cache advantage for the common static case while still matching upstream's dynamic capability. The static and dynamic forms coexist in one `Meta.annotations` dict; only the presence of a resolved callable flips cacheability.

**Composes with**: shipped filter/order subsystems, `matrix_dimensions_and_measures` (shares the fan-out contract), the shipped Plan cache and `get_queryset` visibility hook (shares the non-cacheable-plan path).

### `query_time_optimizer_disable`

**Realistic**: 10/10 — One early-return branch in an existing hook; the context-key plumbing pattern is established.

**Impact**: 5/10 — Debugging and CI-baseline win; audience is maintainers and test authors.

**Difficulty**: 2/10 — ~20 lines plus the header gating; docs cost exceeds code cost.

**Source**: item 42.

**What we'd do**: a per-request escape hatch for `DjangoOptimizerExtension`. When set, `on_execute` short-circuits before computing the plan; results stay correct at N+1 cost.

**Spec**:

```python path=null start=null
# 1. Context flag — programmatic, the test/CI surface; always available
context_value = {"dst_disable_optimizer": True}

# 2. Header — debugging surface; GATED: honored only when settings.DEBUG,
#    request.user.is_staff, or a signed token matches. An open header is a DoS
#    vector — any client could force the server into N+1 mode.
# X-DST-Disable-Optimizer: 1

# 3. Settings default — global "opt-in per query" mode
DJANGO_STRAWBERRY_FRAMEWORK = {"OPTIMIZER_DEFAULT": "off"}
```

- Docs must state exactly what changes when disabled: FK-id stubs aren't built, `select_related` / `prefetch_related` aren't applied, `only()` projections aren't added.
- Distinct from shipped B3 strictness mode (detects lazy loads while the optimizer is **on**); this is the orthogonal off switch.

**Composes with**: the promoted [Optimizer explain mode][card-optimizer-explain-mode] card (the debugging pair), `anti_n1_ci_audit` (run the suite both ways and assert query counts diverge).

### `safe_prefetch_merge`

**Realistic**: 9/10 — The absorb path already exists; this extends one decision function (`plans.py::_optimizer_can_absorb`) with a trivial-queryset detector. Bounded, single-file change plus the opt-in flag.

**Impact**: 6/10 — Closes the last common-case axis where `strawberry-graphql-django` out-optimizes us; real but narrow (only bites when a consumer hand-writes a filter-less `Prefetch` *and* the optimizer would nest optimization beneath it).

**Difficulty**: 4/10 — The trivial-queryset detection is the subtle part (it must conservatively reject every shape the optimizer's `Prefetch` would silently drop); opt-in plumbing and the strictness-workflow docs are the rest.

**Source**: competitive-parity review (2026-06-16) "the one deliberate trade-off worth re-examining: prefetch merging"; the deferred note in [spec-035][spec-035] ("revisited only behind a strict no-custom-filter merge precondition").

**What we'd do**: an **opt-in** safe prefetch-merge. When both the consumer and the optimizer target the same relation subtree with a `Prefetch` and the consumer's `Prefetch` queryset is *trivial* (row-set-identical to a bare-string prefetch), absorb it the way we already absorb a bare string — merging the optimizer's nested `select_related` / `only()` in — instead of the current B8 consumer-wins **drop**. Upstream's `PrefetchInspector.merge` does this unconditionally; we do it only behind the no-custom-filter precondition so the permission-boundary guarantee is never weakened.

**Spec**:

- **Opt-in only; default is unchanged.** The shipped consumer-wins drop (B8, `plans.py::diff_plan_for_queryset`) stays the default — it is a deliberate permission-boundary stance, not an oversight. Merge is enabled explicitly. (Open question for the spec: `DjangoOptimizerExtension(prefetch_merge=True)` kwarg vs. a `DJANGO_STRAWBERRY_FRAMEWORK = {"OPTIMIZER_PREFETCH_MERGE": True}` setting vs. per-type `Meta` — pin one, reject the others with reasons.)
- **Trivial-queryset precondition (the safety crux).** A consumer `Prefetch` queryset qualifies for merge **only** when it carries no row-set or shape semantics the optimizer's `Prefetch` would silently discard: no `.filter()` / `.exclude()` (`query.where` empty), no custom-manager `get_queryset` boundary, no annotations / `extra`, no slicing, no `.distinct()`, no non-default ordering, no `.using()` to a different alias, and no `to_attr`. Any of these → consumer wins (drop), exactly as today. When in doubt, do **not** merge.
- **Why `.filter()` is the boundary.** The optimizer's `Prefetch` carries column/join shape (`select_related` / `only()`) but represents the *full* related set. Absorbing a filtered consumer `Prefetch` would either silently widen the consumer's restricted row set — the exact permission-boundary violation B8 exists to prevent — or force us to reconstruct their filter. Restricting to trivial querysets sidesteps both: the rows are provably identical, so the merge only ever adds columns and joins.
- **Strictness is how you find the sites.** With merge off, the dropped-then-N+1 case is already visible under `strictness="raise"`; that is the signal a consumer uses to discover a relation that *would* benefit from merge. Document the workflow (run strict → find the drop → opt into merge), so the trade-off is observable rather than silent.
- **`only()` merge semantics.** The merged nested `only()` must union the FK-connector / pk columns the plan needs and never narrow below what a downstream resolver reads — the same projection contract the walker already enforces for its own `Prefetch` querysets.

**Composes with**: `query_time_optimizer_disable` and `anti_n1_ci_audit` (strictness surfaces the affected sites), the shipped Queryset diffing (B8) and Strictness mode subsystems.

### `plan_cache_key_memoization`

**Realistic**: 6/10 — A bounded `WeakKeyDictionary` layer over the existing key build *if* the precondition holds; but the whole win is gated on Strawberry yielding a stable operation-node identity across requests. If it re-parses per request, node-keyed memoization buys nothing and the card is dead — verify first.

**Impact**: 5/10 — Real hot-path latency win that the plan cache does *not* already remove, scaling with query depth (deep operations print a large AST); but pure latency, smaller than the selection-tree walk the cache eliminates, and no new capability.

**Difficulty**: 4/10 — The memoization itself is a few lines; the subtlety is proving cross-request node identity and getting weak-key lifetime / invalidation right so a reused node can never serve a stale key.

**Source**: spec-035 close-out review (2026-06-16), Part 1d-1 ("the next real per-request win after the walk").

**What we'd do**: kill the residual per-request `print_ast` on the cache-**hit** path. On every hit, `extension.py::_get_or_build_plan` → `_build_cache_key` → `_print_operation_with_reachable_fragments` → `print_ast(operation)` still runs once per request (memoized only *within* a request by the `_printed_ast_cache` ContextVar keyed on `id(operation)`, which is reset each request). If Strawberry's document/validation cache hands back the **same** operation-node object across requests for an identical query, memoize the printed-AST key on that node via a module-level `WeakKeyDictionary`, turning a cache hit into a near-free dict lookup instead of a fresh full-AST print + hash.

**Spec**:

- **Precondition is the gate (verify before building).** Confirm Strawberry reuses the same `OperationDefinitionNode` object across requests for an identical query string (its parsed/validated-document cache), not a freshly parsed node each time. graphql-core's `parse` produces fresh nodes, so the entire win rests on Strawberry's caching layer above it — if it re-parses, node identity is unstable and this approach yields zero. Spec this verification as step one; the card does not proceed if it fails.
- **Mechanism.** A module-level `WeakKeyDictionary[OperationDefinitionNode, str]` mapping the operation node to its printed, reachable-fragment-aware key component. Weak keys so a node collected with its document drops its entry automatically — no unbounded growth, no manual eviction, no invalidation pass.
- **Only the printed-AST component is memoized, not the whole key.** The full cache key stays `(printed-AST, frozenset vars, model, path tuple, origin)`; variables, model, path, and origin still vary per request and are combined fresh. This card removes only the `print_ast` cost, which is the request-invariant part for a given node.
- **Correctness.** The printed key already folds in reachable fragments, and a reused node identity *is* the same document — so its printed form is invariant and the memo can never go stale for a live node. The per-execution `_printed_ast_cache` ContextVar stays as the within-request memo; this adds a cross-request layer above it.
- **Measure it.** Extend [`scripts/bench_plan_cache.py`](scripts/bench_plan_cache.py) to isolate key-build time on the hit path (as it already isolates the walk via warm-vs-cold), so the win is quantified rather than asserted — the residual after the walk is exactly what this targets.

**Composes with**: the shipped Plan cache (B1) and `cache_info()` (this is the next per-request win after the walk the cache already eliminates), and `scripts/bench_plan_cache.py` (the measurement harness).

### `computed_fields_binding`

**Realistic**: 9/10 — Python property binding is straightforward; the loud-error-on-missing-annotation rule removes the inference risk.

**Impact**: 5/10 — Boilerplate reduction for a common pattern; workaroundable today.

**Difficulty**: 3/10 — Binding + type inference from return annotations; hints split out.

**Source**: item 14, binding half.

**What we'd do**: `Meta.computed_fields = ("display_name",)` auto-binds a model `@property` or `@cached_property` to the GraphQL type.

**Spec**:
- GraphQL type inferred from the property's return-type annotation. A property **without** a return annotation raises `ConfigurationError` at finalization — no inference guesswork.
- `@cached_property` binds identically; the cache lives on the row instance, scoped to the request's object lifetime.
- Methods with no required arguments are bindable; methods with required arguments are out of scope (write a resolver).

**Out of scope here**: optimizer-dependency hints (`computed_field_optimizer_hints`).

### `computed_field_optimizer_hints`

**Realistic**: 8/10 — Hint syntax mirrors shipped `OptimizerHint`; the `only()` extension is incremental walker work.

**Impact**: 6/10 — Closes the silent lazy-load/deferred-load trap that makes computed fields N+1 today.

**Difficulty**: 4/10 — Two plan halves (relations and projection) plus strictness-mode reporting.

**Source**: item 14, hints half.

**What we'd do**: `Meta.computed_field_hints` declares what a computed field reads, so the plan covers it.

**Spec**:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        computed_fields = ("country", "summary")
        computed_field_hints = {
            "country": {"select_related": ["address"]},
            "summary": {"only": ["description", "name"]},
        }
```

- Hints extend **both** halves of the plan: relation traversals extend `select_related` / `prefetch_related`, **and column reads extend the `only()` projection**. A property reading `self.description` under a plan that projected `description` away triggers a deferred-field load — an N+1 that relation hints alone cannot catch. Both dependency kinds are first-class.
- Hint syntax mirrors the shipped `OptimizerHint` keys.
- Under strictness mode, an unhinted lazy load inside a computed field reports the property name and the hint that would fix it.

**Composes with**: `computed_fields_binding` (prerequisite), shipped strictness mode, `anti_n1_ci_audit`.

### `soft_delete_cooperation`

**Realistic**: 8/10 — Integration patterns for the soft-delete packages are well-trodden; the explicit flag removes detection fragility.

**Impact**: 6/10 — Common Django pattern (GDPR / audit / undo); leaking through Prefetch is a recurring real bug.

**Difficulty**: 4/10 — Visibility combinator applied at root + every Prefetch, plus the join contract.

**Source**: item 12.

**What we'd do**: first-class cooperation with `django-safedelete` / `django-softdelete` so soft-deleted rows don't leak through the optimizer's plans.

**Spec**:
- Explicit `Meta.soft_delete = True` flag only. **No manager auto-detection** — custom managers make detection fragile and silent misdetection is worse than one line of declaration.
- The visibility filter applies to the root queryset **and inside every `Prefetch(queryset=...)` the optimizer builds**. The related-side Prefetch is the actual leak site today; filtering only the root queryset is the bug, not the fix.
- Cooperates with `get_queryset` and (when it lands) `cascade_permission_prefetch_enforcement` via the same visibility-combinator seam.
- Joins (`select_related` across a soft-deleting relation) document the contract: the row appears with the relation nulled vs. excluded, configurable per type.

**Composes with**: `cascade_permission_prefetch_enforcement`.

### `anti_n1_ci_audit`

**Realistic**: 7/10 — Schema enumeration via the registry is doable; pairwise coverage bounds the combinatorial blowup.

**Impact**: 7/10 — Turns the optimizer's promise into an enforceable CI contract; only an optimizer-owner can ship it.

**Difficulty**: 6/10 — Query generator + seeding-contract validation + reporter + command; medium slice.

**Source**: item 22.

**What we'd do**: a management command that turns the optimizer's "no avoidable N+1s" promise into an enforceable CI contract.

**Spec**:

```bash path=null start=null
uv run python manage.py audit_n1 --depth 3 --fail-on-warn
uv run python manage.py audit_n1 --depth 5 --include-mutations --seed fakeshop
```

1. Enumerate reachable query paths via `registry.iter_definitions()`.
2. Generate synthetic queries using **pairwise relation coverage**, not exhaustive depth-N enumeration — exhaustive combination counts explode combinatorially; pairwise covers the interaction bugs at tractable cost. `--exhaustive` opt-in for small schemas.
3. Execute against a seeded test database with `OptimizerHint.strictness="raise"`.
4. Fail CI on any unplanned lazy load, reporting the resolver path and the `OptimizerHint` that would fix it.

- **Seeding contract**: every relation must have ≥2 rows on the many side. N+1s do not manifest with one row; a thin seed silently passes everything. The command validates the seed and refuses to certify a run whose seed violates the contract.

**Composes with**: `query_time_optimizer_disable` (run both ways, assert divergence), `schema_diff_cli` (detect "new relation field, no hint" on PRs).

### `otel_span_integration`

**Realistic**: 9/10 — OTel Python SDK is mature; plan metadata already sits in `info.context`.

**Impact**: 6/10 — Production observability win; non-OTel shops still wire their own.

**Difficulty**: 3/10 — Wrap existing plan phases + per-relation spans; small slice with the no-scalar-spans rule.

**Source**: item 6.

**What we'd do**: `DjangoOptimizerExtension(otel=True)` wraps plan work in OpenTelemetry spans.

**Spec**:
- Spans: `dst.optimizer.walk`, `dst.optimizer.queryset`, and one span per **resolved relation**.
- Explicitly **no span per scalar field** — per-field spans in GraphQL are high-cardinality and the overhead routinely exceeds the work measured. Relations and plan phases only; scalars ride inside their parent.
- Span attributes: prefetched fields, `only()` projection, FK-id elision decisions, Relay lookup decisions where applicable.
- OTel SDK is a soft dependency; lazy import, no-op when absent.

**Composes with**: `field_usage_and_deprecation_telemetry` (separate concerns: spans are per-request traces; telemetry is aggregates).

---

## DoS & protection

Sequencing rule for this group: the five primitive cards (`cost_limit_extension`, `depth_limit_extension`, `rate_limit_extension`, `circuit_breaker_extension`, `persisted_query_allowlist`) ship **standalone first**, each with its own settled API from real consumer use. The stack framework generalizes them afterward — locking hook signatures and error codes before the primitives have been pressure-tested is the trap DRF avoided by letting `permission_classes` emerge from individual permissions.

### `cost_limit_extension`

**Realistic**: 9/10 — Strawberry has a complexity extension to build on; `FieldMeta` already carries per-field data.

**Impact**: 8/10 — Out-of-the-box DoS protection for the most-cited GraphQL production risk.

**Difficulty**: 3/10 — Cost mapping + budget check + typed-error integration; the reject-unbounded rule simplifies, not complicates.

**Source**: item 17, cost half.

**What we'd do**: `DjangoCostLimitExtension` derives per-field costs from `FieldMeta` (shipped at B7), sums across the selection tree, and enforces a budget.

**Spec**:

```python path=null start=null
schema = strawberry.Schema(
    query=Query,
    extensions=[
        DjangoOptimizerExtension(),
        DjangoCostLimitExtension(max_cost=1000),
    ],
)
```

- Cost defaults: scalar field = `1`, single relation = `5`, many relation = `10 × (limit_argument or default_page_size)`, computed field = consumer-declared.
- **Unbounded many-relations are rejected, not estimated.** When a many-relation has neither a limit argument nor a default page size, its cost is treated as over-budget by definition. The unbounded case is precisely the dangerous one; a finite fallback guess defeats the extension.
- **Cost sums per alias occurrence**, not per field name. Fifty aliases of one expensive field cost fifty times the weight — alias duplication is the standard cost-limit bypass.
- `Meta.optimizer_hints` extends to carry per-field cost overrides.
- Rejection emits a typed error with the over-budget path and the contributing field weights.

**Composes with**: `typed_error_envelope_and_code_registry`, `depth_limit_extension` (the pair covers shape), `rate_limit_extension` (covers frequency), `matrix_dimensions_and_measures` (matrix cost model plugs into the same budget). Folds into the stack later via `dos_primitive_fold_in` as `CostWeight(...)`.

### `depth_limit_extension`

**Realistic**: 10/10 — AST depth counting after fragment expansion is a solved problem.

**Impact**: 6/10 — Half of the shape defense; cheap insurance every production schema wants.

**Difficulty**: 2/10 — Counter + introspection-allowance decision + typed error.

**Source**: item 17, depth half.

**What we'd do**: `DjangoDepthLimitExtension(max_depth=15)` counts selection depth pre-execution and rejects pathological nesting.

**Spec**:
- Depth counted on the parsed AST after fragment expansion (a fragment chain must not hide depth).
- Introspection queries are naturally deep: either a documented introspection allowance or pairing with `IntrospectionLockdown` (from `dos_builtin_guard_policies`) — the spec must pick one; silently rejecting introspection in dev is a support-ticket generator.
- Rejection emits a typed error with the offending path and measured depth.

**Composes with**: `cost_limit_extension`, `typed_error_envelope_and_code_registry`. Folds into the stack later as `DepthCap(max=)`.

### `rate_limit_extension`

**Realistic**: 9/10 — Django cache + interceptor pattern is standard; rate-limit math is well-known.

**Impact**: 7/10 — Field-level limits beat endpoint-level ones; closes a real DoS gap.

**Difficulty**: 3/10 — Limit logic + per-scope keys + per-occurrence counting; modest slice.

**Source**: item 24, rate-limit half.

**What we'd do**: `Meta.rate_limit` for types (per-resolver) and mutations, backed by `django.core.cache`.

**Spec**:

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

- Scopes: per-user / per-IP / per-tenant / global; key derivation is public and overridable.
- **Counting is per occurrence, not per field name** — fifty aliases of `generateReport` in one document consume fifty hits. Same aliasing contract as `cost_limit_extension`.
- Cache-backend accuracy contract documented: `LocMem` counts per-process and inflates apparent budgets; Redis-backed cache recommended for accuracy under multiple workers.
- Rejection emits `code="dst.rate_limit.exceeded"` with a retry-after timestamp in `params`.

**Composes with**: `typed_error_envelope_and_code_registry`, `cost_limit_extension`. Folds into the stack later as `RateLimit(anon=, user=, staff=)`.

### `circuit_breaker_extension`

**Realistic**: 8/10 — Closed/open/half-open is a known state machine; the cache backend carries the state.

**Impact**: 5/10 — Aggregate-abuse auto-pause matters most to public surfaces; narrower than per-field limits.

**Difficulty**: 4/10 — Cross-worker state accuracy is the concentrated difficulty.

**Source**: item 24, circuit-breaker half.

**What we'd do**: `DjangoCircuitBreakerExtension` — aggregate auto-pause when a type's global request rate exceeds a threshold.

**Spec**:
- State backed by `django.core.cache`; same multi-worker accuracy contract as `rate_limit_extension` (Redis for correctness; `LocMem` per-process for dev).
- State machine: closed → open (threshold exceeded) → half-open (probe window) → closed. Thresholds and windows configurable per type.
- Open-circuit rejections emit a typed error distinct from rate-limit rejections (`code="dst.circuit.open"`).

**Composes with**: `rate_limit_extension`, `typed_error_envelope_and_code_registry`. Folds into the stack later as `CircuitBreaker(global_rate=)`.

### `persisted_query_allowlist`

**Realistic**: 10/10 — `django.core.cache` is mature; hashing is well-known; the allowlist posture removes the APQ ambiguity.

**Impact**: 6/10 — Production hardening for query allow-listing; useful but rarely the headline ask.

**Difficulty**: 3/10 — Extension + cache lookup + rotation command tied to the schema CLI.

**Source**: item 10.

**What we'd do**: a persisted-query extension that **allowlists** operations — only deploy-time-registered hashes execute in production.

**Spec**:
- This is the **allowlist** posture, explicitly not APQ. Apollo's automatic persisted queries let clients register hashes at runtime — a bandwidth optimization an attacker bypasses by registering arbitrary operations. The production-hardening claim only holds for allowlist mode; the spec must not conflate the two. (APQ-style runtime registration may ship later as a separately named, separately documented mode.)
- Hash → operation map stored in any configured `django.core.cache` backend.
- Registration happens at deploy time, wired through the `schema_diff_cli` / `export_schema` toolchain; a management command rotates the allowlist.
- Unknown hashes rejected in production; configurable pass-through in `DEBUG`.

**Composes with**: `schema_diff_cli`, `graphql_over_http_compliance` (persisted hashes are the GET path), `typed_error_envelope_and_code_registry`. Folds into the stack later as `PersistedQueryGate()`.

### `dos_policy_stack_framework`

**Realistic**: 8/10 — A standard Strawberry extension walking a policy list; the hard pieces are bounded and named.

**Impact**: 8/10 — The DRF-shaped composition surface is the headline answer to 'GraphQL DoS is hard'.

**Difficulty**: 5/10 — Hook dispatch + composition semantics + plan-time hoisting + conflict handling; framework only, primitives excluded.

**Source**: item 33, framework half.

**What we'd do**: borrow DRF's stacked-class pattern for DoS protection. `Meta.dos_classes` per type/mutation; `DjangoDoSExtension(global_dos_classes=[...])` schema-wide; each policy is a small class implementing a subset of lifecycle hooks.

**Spec**:

```python path=null start=null
class DoSPolicy:
    """Base class — override the hooks your policy needs. All optional."""

    def check_pre_parse(self, request) -> None: ...
    def check_pre_execute(self, info, query_ast) -> None: ...
    def evaluate_cost(self, info, field, args) -> int: ...
    def check_per_field(self, info, field, args) -> None: ...
    def wrap_execution(self, info, execute): ...
    def short_circuit(self, info) -> bool: ...
```

- Effective stack at request time: `global_dos_classes + meta.dos_classes`, walked in declaration order at each phase.
- Short-circuit semantics: a per-model `AdminBypass()` skips remaining **per-model** policies; global policies have already run. Full global bypass requires `AdminBypass(global_too=True)` declared in the global stack.
- **Plan-time hoisting for `check_per_field`**: the hook is evaluated once per field-in-the-plan, **not** once per field instance per row. Without hoisting, a 10k-row list response under a 14-policy stack executes 140k policy checks. This constrains the hook contract: `check_per_field` may depend on the field, its arguments, and request identity — never on row values. The constraint is documented in the base class.
- Conflict handling: contradictory declarations (two `RateLimit`s with different caps) warn at schema-build time; stricter wins by default; `on_conflict="warn" | "error" | "stricter_wins"`.
- Slow-policy detection: per-policy timing with a warning when policy overhead is disproportionate.
- Stack length capped (default 50); exceeding is a hard schema-build error.
- `Meta.dos_classes = []` opts out of model-level policies but keeps global ones; `Meta.dos_classes = None` opts out of both (rare; flagged by `audit_dos_command`).
- Abstract-base inheritance: a base class's `dos_classes` are inherited and additive with each subclass's own.
- Test toggle: `DjangoDoSExtension(enabled=...)`.

**Sequencing**: ships only after 3–4 primitives have settled in real use. See the group note above.

**Composes with**: every card in this group, `typed_error_envelope_and_code_registry` (every rejection is a typed error with the policy class and threshold in `params`), `graphql_over_http_compliance` (rejection → HTTP status mapping lives in one place: 413 body size, 429 rate limit with Retry-After, 403 CSRF, 404 persisted-query miss).

### `dos_builtin_guard_policies`

**Realistic**: 9/10 — Nine mostly 20-30 line classes; `WallClockBudget` cancellation is the one bounded hard piece.

**Impact**: 7/10 — Completes the layered-defense catalog beyond what the primitives cover.

**Difficulty**: 4/10 — Small classes plus the ordering convention and template generator.

**Source**: item 33, built-in catalog minus the policies realized by the standalone primitives.

**What we'd do**: the nine policy classes that have no standalone-primitive precursor.

**Spec**:

| Class | Phase | Purpose |
| --- | --- | --- |
| `BodyMaxSize(megabytes)` | pre-parse | Reject oversized request bodies |
| `BatchOperationCap(max)` | pre-parse | Reject multi-operation arrays above N |
| `CSRFRequired()` | pre-parse | Require Django CSRF token |
| `IntrospectionLockdown(allow_for)` | pre-execute | Disable introspection except for the given auth tier |
| `AliasCap(max)` | pre-execute | Reject queries with more than N aliases |
| `FragmentExpansionCap(max)` | pre-execute | Reject fragment expansions above N |
| `PaginationCap(max_first=, max_last=)` | check_per_field | Reject pagination args above max |
| `WallClockBudget(seconds)` | wrap_execution | Abort if execution exceeds time budget |
| `AdminBypass(global_too=False)` | short_circuit | Skip remaining policies for staff users |

- `WallClockBudget`: async paths use Strawberry's async cancellation; sync resolvers can't be interrupted mid-call, so the budget is checked at field boundaries. Documented as fail-fast-at-next-field for sync code.
- `AdminBypass` declared anywhere but the top of its stack only skips policies after it — documented gotcha; `audit_dos_command` warns.
- Recommended ordering convention (the template generator emits it): bypass → cheap pre-parse → auth gates → pre-execute AST analysis → cost → per-field runtime → execution wrapping. The framework doesn't enforce ordering.

**Composes with**: `dos_policy_stack_framework` (prerequisite), `audit_dos_command`.

### `dos_primitive_fold_in`

**Realistic**: 9/10 — Adapter shims over already-shipped, already-settled logic.

**Impact**: 5/10 — Coherence win — one uniform surface — rather than new capability.

**Difficulty**: 2/10 — Five wrappers plus the coexistence/deprecation story.

**Source**: item 33, composition contract.

**What we'd do**: wrap the five shipped standalone primitives as stacked policy classes exposing the same logic through the uniform surface.

**Spec**:
- `persisted_query_allowlist` → `PersistedQueryGate()` (pre-parse)
- `cost_limit_extension` → `CostWeight(per_query=, per_field=)` (evaluate_cost)
- `depth_limit_extension` → `DepthCap(max=)` (pre-execute)
- `rate_limit_extension` → `RateLimit(anon=, user=, staff=)` (check_per_field)
- `circuit_breaker_extension` → `CircuitBreaker(global_rate=)` (check_per_field)
- The primitives own their logic (hash lookup, budget arithmetic, key derivation, state machine); this card owns only the adapter shims and the deprecation/coexistence story for consumers already on the standalone extensions. Standalone extensions keep working; the stack is the recommended surface after fold-in.

**Composes with**: `dos_policy_stack_framework` (prerequisite), all five primitives (prerequisites).

### `audit_dos_command`

**Realistic**: 10/10 — A linter over declarations the framework already holds.

**Impact**: 4/10 — Keeps production posture honest; invisible when everything is configured well.

**Difficulty**: 2/10 — Checks + exit codes; small slice.

**Source**: item 33, tooling.

**What we'd do**: `manage.py audit_dos` — a linter for DoS posture.

**Spec**:
- Warns when: no `DjangoDoSExtension` configured in production settings; `AdminBypass` not first in its stack; `Meta.dos_classes = None` opt-outs exist; stack ordering deviates from the recommended convention; mutually contradictory policies detected.
- Exit code suitable for CI.

**Composes with**: `dos_policy_stack_framework` (prerequisite).

---

## Observability

### `field_usage_and_deprecation_telemetry`

**Realistic**: 9/10 — Extension + buffered cache flush + management commands; all known patterns.

**Impact**: 8/10 — Closes the 'hidden cost / schema gravity' visibility gap; deprecation answers become queries.

**Difficulty**: 4/10 — Buffering, plan-level timing attribution, identity/retention controls, two report commands.

**Source**: items 25 and 29, merged — deprecation telemetry is the same store and extension as general usage telemetry, restricted to `@deprecated` fields; one card, two report commands.

**What we'd do**: a `DjangoUsageExtension` recording per-field query counts, last-queried timestamps, and per-client-identity breakdowns, surfaced through management commands.

**Spec**:

```bash path=null start=null
uv run python manage.py schema_usage --since "30 days ago" --sort hits
# Item.price                14,820 hits   last 12 min ago
# Item.legacyPrice                3 hits  last 47 days ago    ← candidate for removal
# Customer.deprecatedTotal        0 hits  last seen 90+ days  ← safe to delete

uv run python manage.py deprecation_report --since "30 days ago"
# per-deprecated-field: top consumers, last-seen, total hits
```

- Counters buffer **in-process** and flush periodically to `django.core.cache`, with a periodic drain to a small audit table. No synchronous cache write on the hot path.
- **Timing is attributed at the plan/query level, not per-field wall-clock.** Under the optimizer, prefetch work is batched at the plan: root fields look expensive and leaf fields look free regardless of which selections drove the DB cost, so per-field timing is fiction. The store records per-operation DB time keyed to the plan; per-field data is hits and recency only.
- Client identity is configurable (header, auth subject, anonymous) and **documented as a privacy/GDPR surface**: retention window setting, anonymization option, and a note that per-user query logs may constitute personal data.
- Deprecated fields with zero usage for N days are **flagged** as safe-to-delete. **No auto-removal**: a schema whose shape depends on runtime cache state is non-deterministic across builds and environments. Flag-only is the ceiling.
- Optional periodic email/webhook for product owners.

**Composes with**: `telemetry_prometheus_otel_export`, `dos_policy_stack_framework` (policy decisions — pass/reject/which threshold — record into the same store, so "which fields are getting throttled?" is a query).

### `telemetry_prometheus_otel_export`

**Realistic**: 9/10 — Read-side exporters over an existing store; both SDKs are mature.

**Impact**: 5/10 — Plugs the store into dashboards teams already run.

**Difficulty**: 2/10 — Exporters only; no new collection.

**Source**: item 29, export half.

**What we'd do**: optional Prometheus / OpenTelemetry metric export over the usage-telemetry store.

**Spec**:
- Exposes the same counters (hits, last-seen, per-operation DB time, policy decisions) as Prometheus metrics and/or OTel metrics; soft dependencies, lazy import.
- No new collection — read-side only over `field_usage_and_deprecation_telemetry`'s store.

**Composes with**: `field_usage_and_deprecation_telemetry` (prerequisite), `otel_span_integration` (spans and metrics are complementary, not shared code).

---

## Schema tooling

### `schema_diff_cli`

**Realistic**: 9/10 — graphql-core gives schema comparison primitives; SDL-file-vs-file removes the environment dependency.

**Impact**: 8/10 — Breaking-change CI gate nobody in the Django + Python + GraphQL stack ships today.

**Difficulty**: 4/10 — Comparison logic + taxonomy + exit-code policy; file-based diff trims the original scope.

**Source**: item 5.

**What we'd do**: `dst diff-schema baseline.graphql --against current.graphql` reporting breaking changes with CI-suitable exit codes.

**Spec**:
- **Diffs two SDL files via graphql-core** — not the live registry. File-vs-file means CI needs no Django settings, no DB, no app import; `export_schema` produces the files. (A convenience mode may export-then-diff in one invocation when a Django environment is available.)
- Breaking-change taxonomy: removed fields, narrowed nullability, removed enum members, type renames, argument type changes, **and added required arguments without defaults** — additive-looking but breaking.
- Classifications: `breaking` / `dangerous` / `safe`; exit code policy configurable (`--fail-on breaking` default, `--fail-on dangerous` opt-in).
- Output formats: human, JSON, GitHub-annotation.

**Composes with**: `persisted_query_allowlist` (rotation at deploy time keys off the diff), `anti_n1_ci_audit` ("new relation field with no optimizer hint" detection).

---

## Transport & caching

### `graphql_over_http_compliance`

**Realistic**: 9/10 — Strawberry's view largely supports the spec; this is Django-adapter polish.

**Impact**: 7/10 — Spec-correct status codes and the GET path are table stakes for serious deployments.

**Difficulty**: 3/10 — View rewrite + content negotiation; caching split out.

**Source**: item 18, spec-compliance half.

**What we'd do**: a Django-aware GraphQL view fully implementing the GraphQL-over-HTTP spec.

**Spec**:
- `GET` accepted for safe queries via persisted-query hashes (CDN-cacheable, browser-cacheable, replay-safe). URL-length limits make raw-query GET a documented non-goal; the GET story is the persisted-hash story.
- Status codes: `400` for parse/validation failures, `401`/`403` for **request-level** auth failures only. **Field-level auth failures stay `200`** with errors in the body — partial data is legal GraphQL and per-field status codes don't exist; conflating the two breaks spec-compliant clients.
- Content negotiation per the spec, including `Accept: application/graphql-response+json`.

**Composes with**: `persisted_query_allowlist` (the GET path), `http_cache_headers_and_etag`, `dos_policy_stack_framework` (rejection → status mapping), `tabular_export_of_list_fields` (Accept negotiation shares this view's machinery).

### `http_cache_headers_and_etag`

**Realistic**: 8/10 — Header emission is mechanical once compliance and versions exist; the private/Vary rule is policy, not research.

**Impact**: 7/10 — CDN-friendliness closes one of the biggest GraphQL-vs-REST objections.

**Difficulty**: 3/10 — TTL composition + ETag glue over two prerequisite cards.

**Source**: item 18, caching half.

**What we'd do**: `Cache-Control` and `ETag` emission so responses cache at the CDN edge, the browser, and the client — three caches deep, keyed on operation hash and version.

**Spec**:
- `Cache-Control` derived from `Meta.cache_ttl` on queried types. **Multi-type queries take the minimum TTL across all selected types** — the most volatile type governs.
- **Authenticated responses emit `Cache-Control: private` plus appropriate `Vary`.** Without it, a shared cache serves one user's data to another. This is the card's single most important line.
- `ETag` computed from content-version hashes when `content_versioned_nodes` is active; `If-None-Match` short-circuits to `304`.
- Anonymous + idempotent + persisted-hash GET is the fully CDN-cacheable configuration; the docs spell out exactly which combination unlocks it.

**Composes with**: `graphql_over_http_compliance` (prerequisite), `content_versioned_nodes`, `persisted_query_allowlist`.

### `content_versioned_nodes`

**Realistic**: 9/10 — Hashing a fixed declared field set is trivial; the tuple default has no projection impact.

**Impact**: 6/10 — Declarative freshness from one Meta key; the gossip extension carries the rest of the original impact.

**Difficulty**: 3/10 — Meta key + field injection + fixed-set auto resolution.

**Source**: item 15, Meta/field half.

**What we'd do**: a declarative `Meta.version` key that adds a `version: String!` freshness field to Relay-Node-shaped types.

**Spec**:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        version = ("updated_at",)        # tuple of fields to hash — the recommended default
        # version = "auto"               # hash a FIXED declared set: all concrete scalar
        #                                #   model fields minus version_exclude
        # version = lambda row: ...      # fully custom callable
```

- Default impl: short SHA-256 of the joined values of the declared fields.
- **`"auto"` hashes a fixed, declared field set — never the selection set.** Hashing "selected scalar fields" means the same row yields different versions under different selections, which manufactures false staleness for every client comparing versions across queries. Auto mode resolves to the concrete scalar model fields minus `Meta.version_exclude = (...)`, fixed at finalization.
- The tuple form (`("updated_at",)`) is the documented recommendation: near-zero cost and no projection impact. Value-hashing forms force the hashed columns into the `only()` projection — the docs state this optimizer interaction explicitly.
- `version` is a regular `String!`; stock clients see a normal field. Per-type opt-out: omit `Meta.version` or set `None`.

**Composes with**: `version_gossip_extension`, `http_cache_headers_and_etag` (ETag source), shipped Relay Node foundation.

### `version_gossip_extension`

**Realistic**: 8/10 — Extensions-block emission is straightforward; the permission-scope opt-out leans on the permissions cards.

**Impact**: 6/10 — Freshness for unselected objects is the half normalized caches can't get any other way.

**Difficulty**: 4/10 — Six opt-out layers + visibility integration.

**Source**: item 15, extension half.

**What we'd do**: an opt-in `DjangoVersionExtension` that emits `extensions["dst.versions"] = {globalid: version}` for every Node in the response — freshness info even for objects whose `version` field wasn't selected.

**Spec**:
- Opt-in at every layer; a consumer who never installs the extension sees zero behavior change.
- Server-side opt-outs: per-schema (omit the extension), per-request directive (`@dstNoVersions`), per-request header (`X-DST-Versions: off`), per-resolver (`@no_version` decorator for ephemeral objects), per-permission scope (gossip respects row/field visibility — a viewer who can't see a row never sees its version).
- The `extensions` block is the GraphQL spec's vendor envelope; spec-compliant clients that ignore it pay only payload bytes, which the opt-outs control.

**Composes with**: `content_versioned_nodes` (prerequisite), `apollo_link_client_sdk`, `declarative_row_and_field_permissions`.

### `mutation_invalidation_gossip`

**Realistic**: 8/10 — Declarative path walking + extensions emission; the cap/fallback rule bounds the worst case.

**Impact**: 7/10 — Server-declared blast radius attacks the single biggest front-end GraphQL bug class.

**Difficulty**: 4/10 — Path resolver + action defaults + cap/coarse-fallback machinery; client SDKs split out.

**Source**: item 20, server half.

**What we'd do**: every mutation response includes `extensions["dst.invalidations"]` listing the GlobalIDs the mutation affected; mutations declare their blast radius.

**Spec**:

```python path=null start=null
class UpdateOrder(DjangoMutation):
    class Meta:
        model = Order
        invalidates = ("self", "self.items", "self.customer.orders")
```

- `self` resolves to the mutation's primary target; path notation walks relations. Defaults: `create` → `("self",)`, `update` → `("self",)`, `delete` → `("self", "self.<all reverse relations>")`.
- **Declared-not-observed contract, documented loudly**: the gossip reflects the declaration, not runtime observation. A mutation whose `post_save` signal mutates other rows invalidates entities the declaration never names; the package does not trace side effects.
- **ID-list cap with coarse fallback**: enumerating reverse relations of a hot row (delete a category with 100k items) would emit a megabytes-scale gossip block. Above a configurable cap, the entry degrades to a type-level invalidation (`{"type": "ItemType"}`) meaning "evict all cached objects/lists of this type" — which normalized caches support natively and which is always correct, just less surgical.

**Composes with**: `apollo_link_client_sdk`, `tanstack_output_mode`, `content_versioned_nodes` (versions answer "is my copy stale?", invalidations answer "what did this mutation change?"), `snapshot_token_protocol` (write mutations list stale download tokens in a sibling extensions key).

### `apollo_link_client_sdk`

**Realistic**: 8/10 — Public `evict`/`modify` API only; small by design.

**Impact**: 7/10 — The piece that turns both gossip blocks into zero-boilerplate cache correctness.

**Difficulty**: 3/10 — One Link, two extension readers, three policies; separate ecosystem is the only friction.

**Source**: items 15 and 20, client halves merged — one Link, two extension blocks.

**What we'd do**: a single small Apollo Link that reads `extensions["dst.versions"]` and `extensions["dst.invalidations"]` and acts on the cache.

**Spec**:
- Invalidations: surgical `cache.evict()` per GlobalID; type-level entries evict by `__typename`.
- Versions: compare against cached versions; on mismatch apply the configured policy.
- Config: `policy: "evict" | "refetch" | "warn"`; `types: [...]` selective subscription; per-operation context flag (`context: { dstVersions: false }`).
- Small by design (the original ~30-line estimate per half is the right order of magnitude); no Apollo cache internals beyond the public `evict`/`modify` API.

**Composes with**: `version_gossip_extension`, `mutation_invalidation_gossip` (either suffices; both supported).

---

## Mutations

### `drf_serializer_mutations`

**Realistic**: 8/10 — DRF exposes `is_valid()`/`save()` cleanly; serializer-field mapping is a known pattern; UNSET is the one subtle seam.

**Impact**: 10/10 — The killer migration story — hundreds of battle-tested serializers move to GraphQL without redeclaring validation.

**Difficulty**: 6/10 — Input/payload split, recursive nesting, absent-vs-null correctness battery, context wiring.

**Source**: item 3.

**What we'd do**: reuse DRF Serializers as the source of truth for input shape **and** validation; auto-generate Strawberry input types; wire `is_valid()` / `save()` into the mutation lifecycle.

**Spec**:

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

- **One serializer yields two GraphQL types**: `write_only` fields appear only on the generated input type; `read_only` fields (and `SerializerMethodField`, which is output-only by construction) appear only on the payload type. The input/payload split is structural, not a filter.
- **Partial updates hinge on absent-vs-null.** DRF's `partial=True` treats *absent* as "don't touch" and `null` as an explicit value; GraphQL inputs must preserve that distinction via Strawberry's `UNSET`. `action="update"` generates all-optional inputs defaulting to `UNSET`; `UNSET` fields are excluded from the data passed to the serializer; explicit `null` passes through. Getting this wrong nulls fields the client didn't send — this is the card's correctness crux and gets its own test battery.
- Nested serializers generate nested input types recursively; `many=True` nests as lists with index-bearing error paths.
- Serializer context wiring: `{"request": ..., "view": None}`-shaped context populated from `info.context` so validators reading `self.context["request"].user` work unmodified.
- Validation failures map through `form_and_serializer_error_adapters` into the typed envelope.
- DRF is a soft dependency: lazy import, clear `ImportError` hint when `serializer_class` is declared without DRF installed.

**Composes with**: the mutations cluster (prerequisite surface), `form_and_serializer_error_adapters`, `typed_error_envelope_and_code_registry`.

### `transactional_mutation_documents`

**Realistic**: 9/10 — The spec already serializes root mutation fields; `transaction.atomic()` is the Django convention.

**Impact**: 7/10 — All-or-nothing mutations with zero new protocol — most of the 'mutations don't compose' answer.

**Difficulty**: 2/10 — One extension + rollback marker + opt-out directive.

**Source**: item 28, reduced to the smallest correct slice.

**What we'd do**: an extension wrapping all root mutation fields of a single GraphQL document in one `transaction.atomic()` block.

**Spec**:
- The GraphQL spec already executes root mutation fields **serially**; wrapping the document's execution in `atomic()` yields all-or-nothing semantics with zero new endpoint, zero dependency DSL, and full compatibility with existing GraphQL clients, validation, and tooling.
- Any root field's failure rolls back the whole document; the response carries the typed-error envelope per failed field and a document-level `code="dst.transaction.rolled_back"` marker on the sibling fields that succeeded-then-rolled-back.
- Opt-in per schema (`DjangoTransactionalMutationsExtension`) with per-document opt-out directive for mutations that intentionally commit independently.

**Composes with**: `typed_error_envelope_and_code_registry`, the promoted [Mutation transactions and idempotency][card-mutation-transactions-and-idempotency] card, `batch_mutation_endpoint` (which ships only if demand survives this card).

### `batch_mutation_endpoint`

**Realistic**: 7/10 — Transaction wrapping is easy; the path-expression resolver is real but bounded work.

**Impact**: 5/10 — Exists only for cross-referencing cases document-level atomicity can't express; demand-gated.

**Difficulty**: 6/10 — Dependency-graph resolver + batch executor + error mapping, outside standard GraphQL validation.

**Source**: item 28, full slice — explicitly sequenced **after** `transactional_mutation_documents`, and only if real demand remains.

**What we'd do**: a dedicated `/graphql/batch` endpoint accepting an ordered list of mutation operations in one `transaction.atomic()` block, with cross-operation result references.

**Spec**:

```typescript path=null start=null
const result = await client.batch([
    { op: "items.create",     input: { name: "Order #1" },                 alias: "order" },
    { op: "lineItems.create", input: { order: "$order.id", product: 42 } },
    { op: "lineItems.create", input: { order: "$order.id", product: 43 } },
]);
```

- `$alias.path` expressions reference earlier results; the executor resolves the dependency graph before execution and rejects cycles.
- Known cost, stated up front: the endpoint bypasses standard GraphQL document validation and client tooling — operations are named references, not GraphQL documents. This is why `transactional_mutation_documents` ships first; this card exists for the cross-referencing case that document-level atomicity cannot express.
- Responses carry the shared typed-error envelope and the `dst.invalidations` block so client invalidation still works.

**Composes with**: `transactional_mutation_documents` (prerequisite, demand gate), `mutation_invalidation_gossip`, `invokable_typescript_client` (the `client.batch` surface).

---

## Codegen & clients

### `selection_set_strategy_spec`

**Realistic**: 10/10 — It's a design document; the work is deciding, not building.

**Impact**: 7/10 — Unblocks the invokable client and pins a versioning-hazard decision before it calcifies.

**Difficulty**: 2/10 — Hard thinking, no code.

**Source**: item 26, extracted design prerequisite.

**What this is**: a design spec, not a feature — it answers the question the invokable-client idea cannot ship without: **what does a generated call select?**

**Spec questions to resolve**:
- tRPC procedures return whatever the server defines; GraphQL requires the client to choose a selection set. `client.queries.items.list()` must bake one in.
- If the default is "all scalars," payloads silently grow as the schema grows — reintroducing the overfetching GraphQL exists to prevent, and changing wire payloads on schema-only changes (a versioning hazard for generated clients).
- Candidate resolution: full-scalar default **pinned at generation time** (regeneration is the explicit consent to payload change), plus an optional typed `select` argument for narrowing, plus a generated per-field "fragment" constant for reuse. Depth policy for relations (default: FK-id stubs only; relations opt-in via `select`).
- The decision must cover: stability across regenerations, interaction with `persisted_query_allowlist` (every distinct selection is a distinct hash), and interaction with cost limits (the default selection must not trip its own server's budget).

**Composes with**: `invokable_typescript_client` (hard prerequisite), `typescript_type_emission`, `persisted_query_allowlist`, `cost_limit_extension`.

### `typescript_type_emission`

**Realistic**: 9/10 — Codegen is a known pattern; introspection comes from the registry; TS-only trims the treadmill.

**Impact**: 7/10 — Closes the separate-Node-toolchain objection for the type-safety half.

**Difficulty**: 5/10 — Output templates, discriminated unions, deterministic emission.

**Source**: item 21, narrowed to TypeScript only.

**What we'd do**: extend the planned `export_schema` management command with `--emit typescript`, producing client-ready type definitions without a Node toolchain.

**Spec**:

```bash path=null start=null
uv run python manage.py export_schema --emit typescript --output frontend/src/generated/graphql.ts
```

- Output mirrors `graphql-codegen` conventions: discriminated unions for GraphQL unions, named input types, branded scalar types, and types for the `FieldError` envelope.
- **TypeScript only.** The originally sketched `--emit jsdoc` / `--emit dart` modes are cut: each output language is a permanent maintenance treadmill, and no demand signal exists. Revisit only on concrete consumer request.
- Deterministic output (stable ordering, no timestamps) so generated files diff cleanly in consumer repos.

**Composes with**: `invokable_typescript_client`, `tanstack_output_mode`, `schema_diff_cli` (same export machinery).

### `invokable_typescript_client`

**Realistic**: 8/10 — Typed wrappers over fetch are well-trodden; the streaming iterator rides a protocol two other cards define.

**Impact**: 9/10 — The direct answer to 'I just want to call a function' — dissolves the strongest tRPC argument.

**Difficulty**: 6/10 — Generated functions + ~2KB runtime + hash dispatch + resume-capable iterator.

**Source**: item 26, plus the streaming-iterator client wrapper folded in from item 30.

**What we'd do**: `--emit typescript-client` produces invokable typed functions — one per GraphQL field — over a tiny fetch wrapper.

**Spec**:

```typescript path=null start=null
import { client } from "./generated/dst";

const items   = await client.queries.items.list({ filter: { name: "foo" } });
const created = await client.mutations.items.create({ name: "bar" });

// Streaming downloads surface as a typed async iterator over the snapshot protocol:
const stream = await client.streams.orders.list({ filter: { createdAfter: "2026-01-01" } });
for await (const order of stream) { await processOrder(order); }
// Auto-resumes on connection drop; verifies the final checksum; re-initiates on token
// expiry (or throws under { strict: true }).
```

- Selection sets follow `selection_set_strategy_spec` — that card resolves first; this card implements its decision.
- Each generated function carries its operation hash, so `persisted_query_allowlist` and the GET transport work out of the box.
- Runtime wrapper stays small (~2KB target): fetch, error-envelope decoding, persisted-hash dispatch, and the streaming iterator. No normalized cache — that's the point.
- The streaming iterator speaks the `snapshot_token_protocol` / `ndjson_streaming_view` wire: token from `extensions["dst.download"]`, `Range` resume, checksum verification.

**Composes with**: `selection_set_strategy_spec` (hard prerequisite), `typescript_type_emission`, `persisted_query_allowlist`, `snapshot_token_protocol`, `ndjson_streaming_view`, `batch_mutation_endpoint`.

### `tanstack_output_mode`

**Realistic**: 8/10 — Hook generation is bounded; the entity-to-query-key registry is the named, owned hard part.

**Impact**: 7/10 — Closes the 'Apollo Cache duplicates React Query' gap with server-driven invalidation.

**Difficulty**: 6/10 — Hooks + the GlobalID-per-query registry + invalidation translation.

**Source**: item 27.

**What we'd do**: a TanStack Query output mode emitting typed hooks wired to server-driven invalidation.

**Spec**:

```typescript path=null start=null
import { useItemsListQuery, useItemCreateMutation } from "./generated/dst-tanstack";

const { data, isLoading } = useItemsListQuery({ filter: { name: "foo" } });
const createItem = useItemCreateMutation();
await createItem.mutateAsync({ name: "bar" });
// invalidation driven by extensions["dst.invalidations"] — no manual onSuccess lists
```

- **The hard part is the entity→query-key registry, and this card owns it.** TanStack caches by query key, not normalized entities; translating "GlobalID X changed" into "invalidate these query keys" requires the runtime to track which active queries returned which GlobalIDs. The generated wrapper records GlobalIDs per query result (from the response or the versions gossip) into a registry; mutation responses consult it to call `queryClient.invalidateQueries(...)` for affected keys. Type-level invalidation entries map to type-prefixed query-key predicates.
- Hooks generated per field: `useXQuery`, `useXInfiniteQuery` for connections, `useXMutation`.
- Builds on the invokable client's transport; no second runtime.

**Composes with**: `invokable_typescript_client` (prerequisite), `mutation_invalidation_gossip` (prerequisite for auto-invalidation), `version_gossip_extension` (optional registry feed).

---

## Relay

### `stable_cursor_field`

**Realistic**: 8/10 — Keyset pagination is a known technique; HMAC opacity is standard crypto plumbing.

**Impact**: 8/10 — Cursor drift on inserts/deletes is where Relay teams give up; this is the fix.

**Difficulty**: 4/10 — Tuple-comparison decode + enforced order_by + opaque payload + pageInfo recomputation.

**Source**: item 39, sub-feature 3.

**What we'd do**: declarative stable cursors that survive inserts and deletes.

**Spec**:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        cursor_field = ("created_at", "id")    # stable cursor; survives inserts/deletes
```

- The cursor encodes the row's `(created_at, id)` tuple; decoding produces a `WHERE (created_at, id) > (value, value)` tuple-comparison filter — insert-safe and delete-safe.
- The connection machinery enforces a matching `order_by` on the queryset so cursor order and result order can't diverge; a final unique tiebreak column (pk) is required and validated at finalization.
- **The cursor payload is opaque to clients: HMAC-signed (tamper-evident) and optionally encrypted.** A cleartext cursor encoding `created_at` discloses column data from the row it points at — including rows a different viewer shouldn't see when cursors leak across contexts. Opacity is part of the contract, not a hardening afterthought.
- When `cursor_field` is unset, the default opaque-offset behavior applies; stability is opt-in.

**Composes with**: shipped `DjangoConnectionField`, `permission_aware_cursor_decoding`.

### `permission_aware_cursor_decoding`

**Realistic**: 9/10 — Apply the decode filter to `get_queryset` output instead of the raw table; small change.

**Impact**: 7/10 — Closes a real cross-viewer row-leak privacy bug.

**Difficulty**: 2/10 — One decode-path change plus the documented residual.

**Source**: item 39, sub-feature 6.

**What we'd do**: cursor decode that re-applies row visibility, so a cursor minted under one user's visibility doesn't leak rows under another's.

**Spec**:
- The decode filter is applied to `cls.get_queryset(qs, info)` — never to the raw table. A cursor minted under admin privileges and replayed by a regular user paginates only the rows that user can see: no row leak, no inconsistent pagination.
- Documented residual: position-based information (how many rows precede the cursor) is inherently visibility-relative and recomputed per viewer; combined with `stable_cursor_field`'s opaque payloads, neither values nor positions disclose hidden rows.

**Composes with**: `stable_cursor_field`, `declarative_row_and_field_permissions`, shipped `get_queryset` hook.

### `globalid_alias_map`

**Realistic**: 10/10 — A dict lookup at decode time; ~30 lines.

**Impact**: 4/10 — Covers the rare model-move/rename case the shipped encoding leaves open.

**Difficulty**: 1/10 — Alias map + expiry command.

**Source**: item 39, sub-feature 1, plus the parking lot's GlobalID-stability notes.

**What we'd do**: a thin alias helper for the rare GlobalID-breaking events that remain after the shipped model-anchored encoding — moving a model between apps or renaming the model class.

**Spec**:

```python path=null start=null
DJANGO_STRAWBERRY_FRAMEWORK = {
    "RELAY_GLOBALID_ALIASES": [
        # old -> new; decoder accepts either, encoder emits new
        ("auth.user",     "accounts.user"),
        ("products.item", "products.product"),
    ],
}
```

- Decoder consults the alias map at decode time (a dict lookup, ~30 lines); new IDs are minted against the new identifier.
- The map is append-only over the project's lifetime; `manage.py expire_globalid_aliases --before=YYYY-MM-DD` drops entries once no client can still hold the old format.
- GraphQL type renames are already a non-event under the shipped model-anchored encoding — this card covers only Django-side moves/renames, which already require a Django migration; the GlobalID breakage is symmetric and this is the opt-out.

**Composes with**: shipped [Django-model-based GlobalID encoding][card-django-model-based-globalid-encoding], `composite_pk_globalid`.

### `polymorphic_interface_connections`

**Realistic**: 7/10 — Builds on shipped `is_type_of` injection; per-concrete-type prefetch needs real optimizer cooperation.

**Impact**: 8/10 — Single-connection polymorphic feeds are a canonical wall teams hit today.

**Difficulty**: 7/10 — Interface dispatch + per-type planning + cursor-column validation across concrete types.

**Source**: item 39, sub-feature 2.

**What we'd do**: native `Connection[Interface]` — edges can be any concrete type implementing the interface. Canonical case: a feed where `Post`, `Photo`, `Repost`, `Poll` all implement `FeedItem`.

**Spec**:
- `DjangoConnectionField` accepts an interface type; resolution walks the polymorphic queryset (cooperating with `django-polymorphic` when present, `ContentType` lookups otherwise), dispatches each row through the shipped `is_type_of` injection to its concrete `DjangoType`, and emits the right `__typename` per edge.
- The optimizer's walker recognizes the interface-edge shape and plans per-concrete-type prefetches for the relations each concrete type's selections need.
- Cursor semantics inherit from the connection foundation; `stable_cursor_field` declarations on the interface require the cursor columns to exist on every concrete type (validated at finalization).

**Composes with**: `django_polymorphic_union_types` (shared dispatch machinery — that card is the non-Relay half), shipped Node foundation, `stable_cursor_field`.

**Carries forward (spec-035 G3 deferral)**: this card is the scheduled home for the deferred **G3 — fragment type-condition narrowing** from [spec-035][spec-035] (Decisions 6–7). G3 is parity (`strawberry-graphql-django` narrows fragment planning to concrete types), but it has **no reachable trigger until this card's per-concrete-type optimizer cooperation exists**: today an interface / union root field never enters the walker, because `DjangoOptimizerExtension._resolve_model_from_return_type` resolves the abstract `origin` (the interface / union class, not a registered `DjangoType`) and `registry.model_for_type(origin)` returns `None`, so `_optimize` passes the queryset through before any planning runs. G3 therefore ships *with* this card, never before it. Carry-forward requirements distilled from the spec's analysis:

- **R1 — abstract-return entry contract (the precondition).** Define how an interface / union return resolves its target model(s), its origin / plan-cache identity (the key is `(document, target_model, origin)` — an abstract origin needs a defined identity or a per-concrete fan-out), and its possible-concrete-type enumeration — registry-only, with **no per-request graphql-core introspection** (the B7 invariant). This is the "per-concrete-type prefetch" Spec bullet above, made concrete; it is the bulk of the work and the gate on everything else.
- **R2 — both walker inliner consumers use the classifier.** The narrowing must thread through *both* `optimizer/walker.py::_walk_selections` **and** `optimizer/walker.py::_selected_scalar_names` (the FK-id-elision-safety analyzer is a second `included_field_selections` consumer) — otherwise elision decisions get made from sibling / unknown-composite fragments the main walk would have skipped.
- **R3 — non-Relay name resolution + fail-closed ambiguity.** "Known sibling concrete type" needs a lookup over all `registry.iter_definitions()` by `graphql_type_name` (the existing `registry.definition_for_graphql_name` is Relay-Node-only and raises on miss / ambiguity). Duplicate GraphQL names must fail closed (treat as the recurse-only outcome, or raise loudly in tests) — never an implicit first-match. Interface names come from Strawberry definition metadata (honoring `Meta.name` / `@strawberry.interface(name=...)`), collected as the **union** of declared `definition.interfaces` and MRO-inherited bases — neither source alone is complete (a directly-inherited `relay.Node` lives only in the MRO, never in `definition.interfaces`).
- **Classifier shape.** A tri-state classifier (`INLINE` / `SKIP` / `RECURSE_FRAGMENTS_ONLY`) plus a `fragments_only` recursion flag on `included_field_selections` — not a boolean filter — so an unknown union recurses into nested matching fragments while dropping its own direct fields. Full design, edge cases, and test plan are retained verbatim in [spec-035][spec-035] (Decision 6 / Decision 7 / the deferred Slice 3 test plan).

### `refetchable_container_support`

**Realistic**: 8/10 — Schema metadata emission over the shipped `node(id:)` foundation.

**Impact**: 5/10 — Removes a client-side Relay wall; narrow but sharp audience.

**Difficulty**: 3/10 — Directive/hint emission + shape-pinning finalization check.

**Source**: item 39, sub-feature 5.

**What we'd do**: declarative schema-side support for Relay's `useRefetchableFragment`.

**Spec**:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        interfaces = (relay.Node,)
        refetchable = True
```

- Emits the right schema metadata (the `@refetchable` directive when the consumer's Strawberry version supports it; a documented introspection hint otherwise).
- The shipped root `node(id:)` resolver is guaranteed to return the same shape the consumer queried — no field-set drift between the connection edge and the refetched object; a finalization check pins this.

**Composes with**: shipped root node fields (0.0.9), shipped `DjangoConnectionField`.

### `interface_misuse_diagnostics`

**Realistic**: 10/10 — Finalization-time checks over declarations already in hand.

**Impact**: 4/10 — Better errors prevent a class of confused issue reports.

**Difficulty**: 2/10 — Targeted `ConfigurationError` messages + earlier mismatch checks.

**Source**: Relay/interface parking lot.

**What we'd do**: targeted, early diagnostics for interface misconfiguration.

**Spec**:
- `ConfigurationError` with a corrective message when consumers put non-interface Relay helpers in `Meta.interfaces` — specifically `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo` (scalar helpers, annotations, or field types — not interfaces).
- Earlier diagnostics for interface field mismatches and nullability conflicts before Strawberry finalization where feasible, especially for non-Relay interfaces.
- String / lazy interface references stay out until real-world pressure justifies a resolver; eager validation remains the contract.

**Composes with**: shipped `Meta.interfaces` foundation.

---

## Polymorphism

### `django_polymorphic_union_types`

**Realistic**: 7/10 — `django-polymorphic` integration is workable; the registry already knows the union targets.

**Impact**: 7/10 — Polymorphic models are everywhere in real Django apps; both upstreams punt.

**Difficulty**: 5/10 — Union generation + ctype select_related + large-scan patterns.

**Source**: item 4, polymorphic half.

**What we'd do**: `Meta.polymorphic = True` for `django-polymorphic` integration.

**Spec**:
- Generates a Strawberry union of all registered concrete-subclass `DjangoType`s (the registry already knows the target list).
- Optimizer cooperation: `select_related("polymorphic_ctype")` injected automatically; documented `iterator()` patterns for large polymorphic scans.
- `django-polymorphic` is a soft dependency; the flag without the package raises `ConfigurationError` with an install hint.

**Composes with**: `polymorphic_interface_connections` (the Relay-shaped sibling), `generic_foreign_key_support`.

### `generic_foreign_key_support`

**Realistic**: 7/10 — Django 5.0's `GenericPrefetch` natively solves the heterogeneous-prefetch half.

**Impact**: 8/10 — Audit logs, comments, attachments, reactions — GFKs block adoption today and we raise `ConfigurationError`.

**Difficulty**: 5/10 — Union dispatch + per-target plan shapes + fallback contract; far smaller post-`GenericPrefetch`.

**Source**: item 4, GFK half.

**What we'd do**: replace today's `ConfigurationError` on `GenericForeignKey` with a real resolver returning a union of registered target types.

**Spec**:
- Built on Django 5.0's `GenericPrefetch`, which natively solves heterogeneous-queryset-per-content-type prefetching — the optimizer supplies one queryset per registered target type, each carrying that type's `select_related` / `only()` shape. This removes most of the hand-rolled `ContentType` batching the original item scoped.
- The union's member list comes from the registry (every `DjangoType` whose model appears as a GFK target); unregistered targets resolve to a documented fallback (`null` + warning, or `ConfigurationError` in strict mode).
- Minimum Django version gate for this feature is 5.0; on older Django the existing loud `ConfigurationError` stands.

**Composes with**: `django_polymorphic_union_types`, the optimizer walker.

---

## Permissions

### `permission_redaction_nullability_spec`

**Realistic**: 10/10 — A decision document over known candidates.

**Impact**: 8/10 — Pins an irreversible published-contract decision every permission card hangs on.

**Difficulty**: 2/10 — Hard thinking, no code.

**Source**: item 1, extracted design prerequisite.

**What this is**: a design spec, not a feature — it pins the decision every permission card hangs on: **what does a denied field resolve to?**

**Spec questions to resolve**:
- Candidates: `null` (breaks non-null fields), a GraphQL error (breaks partial-response ergonomics and leaks which fields are gated), a redaction sentinel (the `django-graphene-filters` `is_redacted` lineage — explicit but schema-visible).
- Whatever is chosen, **permission-gated fields are effectively nullable in the schema** — the gate changes the published contract, and that is not reversible after consumers depend on it. Finalization should enforce (or auto-apply, with a loud note) nullability on gated fields.
- Row-level denial is settled (the row is absent — `get_queryset` semantics); this spec is about field-level and about the cascade boundary (does a denied relation read as `null`, empty list, or redacted?).
- Decide existence-leak posture: denied-vs-missing must be indistinguishable, matching the shipped Relay node contract ("returns null for hidden and missing rows with no existence leak").

**Composes with**: `declarative_row_and_field_permissions` (hard prerequisite), `cascade_permission_prefetch_enforcement`, `version_gossip_extension`.

### `declarative_row_and_field_permissions`

**Realistic**: 8/10 — Row is sugar over `get_queryset`; field gating follows the spec card's decision.

**Impact**: 7/10 — Removes the `get_queryset` boilerplate every team writes; near-parity positioning is honest.

**Difficulty**: 4/10 — Meta key + composition order + three permission value kinds.

**Source**: item 1, row + field halves.

**What we'd do**: one `Meta.permissions` key combining row and field permissions declaratively.

**Spec**:

```python path=null start=null
class ItemType(DjangoType):
    class Meta:
        model = Item
        permissions = {
            "row": "items.view_item",
            "fields": {"price": "items.view_price"},
        }
```

- Row permissions compose with (not replace) `get_queryset`: declaration is sugar over the queryset hook, applied before consumer hooks run.
- Field permissions gate at resolution per the decision in `permission_redaction_nullability_spec`.
- Permission values: Django permission strings, callables `(user, info) -> bool`, or permission-class instances — matching the surrounding ecosystem's expectations.
- Honest positioning note carried in the docs: row + field permissions are near-parity with `strawberry-graphql-django`'s `permission_classes`; the differentiation lives in the cascade card.

**Composes with**: `permission_redaction_nullability_spec` (prerequisite), `cascade_permission_prefetch_enforcement`, `role_scoped_schema_variants`.

### `cascade_permission_prefetch_enforcement`

**Realistic**: 7/10 — Registry, walker hooks, and `_attach_relation_resolvers` skip-sets give the integration points; downgrade machinery is owned.

**Impact**: 9/10 — Visibility that holds across joins at planning time — the slice neither upstream can ship without rebuilding.

**Difficulty**: 7/10 — Boundary detection + filtered Prefetch everywhere + select_related downgrade + Relay surface coverage.

**Source**: item 1, cascade half — the differentiator slice.

**What we'd do**: `permissions = {"cascade": True}` — visibility enforced across joins, inside the optimizer's plans, so permission boundaries hold at planning time, not just resolution time.

**Spec**:
- Every `Prefetch(queryset=...)` the optimizer builds for a relation whose target type declares row permissions gets the target's visibility filter applied — the same seam as `soft_delete_cooperation`.
- `select_related` joins that would cross a permission boundary downgrade to a filtered `Prefetch` (the optimizer already owns the downgrade machinery); the plan records the downgrade reason for explain output.
- Integration points: the walker (boundary detection), `_attach_relation_resolvers` skip-set semantics (denied relations), and the `get_queryset` visibility hook (filter composition).
- Relay surfaces inherit it: `resolve_node`, root `node(id:)` / `nodes(ids:)`, and connection lookups all pass through the same visibility combinator (per the parking lot's Relay-aware-permissions note).
- Inherits `django-graphene-filters`' `apply_cascade_permissions` semantics as the behavioral baseline.

**Composes with**: `declarative_row_and_field_permissions` (prerequisite), `soft_delete_cooperation` (shared combinator seam), the promoted [Optimizer explain mode][card-optimizer-explain-mode] card (plans show permission filters and downgrade reasons), `permission_aware_cursor_decoding`.

### `role_scoped_schema_variants`

**Realistic**: 7/10 — The registry/finalizer architecture supports a scope argument; the LRU bound contains the runtime cost.

**Impact**: 6/10 — Different schemas per role is hand-rolled today; the roles-only narrowing keeps it honest.

**Difficulty**: 6/10 — Finalizer parametrization + per-scope visibility evaluation + cache invalidation.

**Source**: item 11, narrowed.

**What we'd do**: `finalize_django_types(scope=...)` / `schema_for(role)` produces a role-scoped subset of the registered types — different schemas for different **roles**.

**Spec**:
- Scope: a small, bounded role set (admin / staff / partner / public — single digits). Built schemas are LRU-cached; Strawberry schema objects are heavy and the cache bound is the feature's safety rail.
- **Tenant-scale variants are explicitly out of scope.** Schema-per-tenant at thousands of tenants is a memory problem, not a feature; that use case is runtime visibility filtering via the permissions cards. The card's docs route tenant-shaped requests there.
- Field/relation visibility per role is declared through the same `Meta.permissions` vocabulary, evaluated at finalization for the scope rather than at request time.
- Per-scope schema export composes with `schema_diff_cli` (diff the public schema against the admin schema; diff a role's schema across releases).

**Composes with**: `declarative_row_and_field_permissions` (shared vocabulary), `schema_diff_cli`, the registry/finalizer architecture.

---

## Bulk & reporting

### `tabular_export_of_list_fields`

**Realistic**: 9/10 — Content negotiation + row flattening over the shipped list/connection machinery; all streaming-friendly formats.

**Impact**: 9/10 — The 'just give me a CSV of this query' ask is the single most common export need; one header, no parallel endpoint.

**Difficulty**: 4/10 — Negotiation precedence + flattening/explode semantics + three line-oriented writers.

**Source**: item 32, the "regular list export" sub-section promoted to its own card — it ships **before** any matrix work.

**What we'd do**: any `DjangoListField` or `DjangoConnectionField` query becomes a tabular download via content negotiation. *"Give me a CSV of all my orders with their customer's email and total"* is a regular GraphQL query with `Accept: text/csv` — no matrix declaration needed.

**Spec**:

```bash path=null start=null
curl -H "Accept: text/csv" \
     -d '{"query": "{ allOrders { id total status customer { country email } } }"}' \
     https://api.example.com/graphql/
# id,total,status,customer_country,customer_email
# 1001,99.99,PAID,US,user@example.com
```

- Formats in this card: `text/csv`, `text/tab-separated-values`, `application/x-ndjson`. All three stream line-by-line. (XLSX / Parquet / Arrow are their own cards.)
- Format negotiation, in priority order: `Accept` header → `?format=csv` URL param (browser downloads) → `@tabular(format: "csv")` operation directive.
- Column flattening: selected scalars become columns; relation traversals flatten (`customer.country` → `customer_country`).
- Nested lists: one row per nested item with parent columns repeated (pandas `explode` semantics), configurable per field via `Meta.tabular = {"explode": ["line_items"]}`.
- Unconfigured/unknown format requests produce a typed error (`code="dst.export.format_unavailable"`).

**Composes with**: `graphql_over_http_compliance` (shares the negotiation machinery), `typed_error_envelope_and_code_registry`, `xlsx_export_format`, `parquet_arrow_export_formats`, `snapshot_token_protocol` (large exports stream via the download protocol).

### `xlsx_export_format`

**Realistic**: 9/10 — `openpyxl` write_only streaming is documented territory.

**Impact**: 6/10 — Finance-team Excel downloads are a perennial ask.

**Difficulty**: 3/10 — Streaming writer + row-limit behavior config.

**Source**: item 32, format catalog.

**What we'd do**: XLSX as an additional negotiated tabular output.

**Spec**:
- `openpyxl` soft dependency; lazy import; missing dep produces the typed `format_unavailable` error with a `pip install openpyxl` hint.
- Streaming via `openpyxl` `write_only` mode; the ZIP container builds incrementally.
- Excel's 1,048,576-row limit: automatic multi-sheet split **or** fallback to CSV with a warning in response extensions, configurable via `Meta.xlsx_row_limit_behavior`.

**Composes with**: `tabular_export_of_list_fields` (prerequisite), `matrix_pivot_mode` (pivot values become real XLSX columns).

### `parquet_arrow_export_formats`

**Realistic**: 8/10 — `pyarrow` handles the containers; the scalar-type mapping is the real spec work.

**Impact**: 6/10 — Feeds data lakes and pandas/Spark/DuckDB pipelines straight from the API.

**Difficulty**: 4/10 — Row-group/batch streaming + the type-mapping table.

**Source**: item 32, format catalog.

**What we'd do**: Parquet and Arrow IPC as negotiated tabular outputs for analytical pipelines.

**Spec**:
- `pyarrow` soft dependency; same lazy-import / typed-error contract as XLSX.
- Parquet streams per row-group (configurable size, default 10,000 rows); Arrow streams per record-batch (configurable batch size).
- Media types: `application/vnd.apache.parquet`, `application/vnd.apache.arrow.stream`.
- GraphQL scalar → Arrow type mapping is part of this card's spec (decimals, datetimes with timezones, JSON columns), since pandas/Spark/DuckDB consumers will hold it to account.

**Composes with**: `tabular_export_of_list_fields` (prerequisite), `snapshot_token_protocol` + `ndjson_streaming_view` (resume semantics; Parquet/Arrow/XLSX restart a fresh stream at the row offset since their containers don't append cleanly).

### `matrix_dimensions_and_measures`

**Realistic**: 7/10 — Django ORM aggregation is robust; the matrix surface is custom but achievable; fan-out-as-error simplifies correctness.

**Impact**: 8/10 — Group-by reporting is the #1 reason teams bolt a parallel endpoint onto GraphQL.

**Difficulty**: 6/10 — Dimension/Measure surface + planner fan-out detection + backend gating + cost model; pivot and formats split out.

**Source**: item 32, the `DjangoMatrix` core.

**What we'd do**: a tabular query surface returning flat rows with declarative *dimensions* (group-by axes) and *measures* (aggregations) — the right shape for *"sum revenue by country by year, top 100 rows."*

**Spec**:

```python path=null start=null
from django_strawberry_framework import DjangoMatrix, Dimension, Measure

class OrderMatrix(DjangoMatrix):
    class Meta:
        model = Order
        dimensions = {
            "country": Dimension("customer__country"),
            "year":    Dimension("created_at__year"),
            "month":   Dimension("created_at", trunc="month"),
            "status":  Dimension("status"),
        }
        measures = {
            "revenue":     Measure("total", agg="sum"),
            "order_count": Measure("id", agg="count", distinct=True),
            "avg_value":   Measure("total", agg="avg"),
        }
        filterset_class = filters.OrderFilter   # reused from the DjangoType
        cost = {"per_dimension": 5, "per_measure": 3, "per_filter": 1}
```

- Response shape: flat `rows: [Row]` (`{dimension_a, dimension_b, measure_x}` records) plus optional `totals`. No nesting, no edge wrappers — directly serializable by the tabular-export cards.
- Unused dimensions/measures cost nothing; they're ORM expressions evaluated only when selected. `Dimension` wraps a field path with optional `trunc`/`extract`; `Measure` wraps an aggregation.
- **JOIN fan-out is a planner error by default, not a warning.** Aggregating across a many-side relation alongside another multi-valued join multiplies counts — for a *reporting* surface, silently multiplied revenue is the worst possible failure. The planner detects fan-out paths and refuses unless the measure declares `distinct=True` or the type opts down to warning mode.
- **Per-backend aggregate gating.** `agg="percentile"` (`percentile_cont`) exists in PostgreSQL, not MySQL/SQLite; each aggregate declares backend availability and an unavailable aggregate on the active backend is a finalization-time `ConfigurationError`, not a runtime SQL error.
- Cost model: `total = n_dimensions × per_dimension + n_measures × per_measure + n_filters × per_filter`, combined with projected row count (`EXPLAIN` estimate on PostgreSQL, `COUNT(*)` fallback elsewhere), enforced pre-execution against the schema budget; rejection is typed (`code="dst.matrix.cost_exceeded"`) listing the contributing components.
- Errors: `validation.matrix.unknown_dimension` / `unknown_measure` with the available names in `params`.

**Composes with**: `cost_limit_extension`, `tabular_export_of_list_fields` (export of matrix rows), `selection_aware_annotations` (shared fan-out contract), the planned aggregation subsystem (`AggregateSet` ships the single-row surface first; the matrix generalizes it to group-by — the same `measures` dict can drive both).

### `matrix_pivot_mode`

**Realistic**: 7/10 — Pivot over the matrix core is bounded; the GraphQL cell shape sidesteps dynamic fields.

**Impact**: 6/10 — The dashboard pivot-table use case; valuable but optional atop the core.

**Difficulty**: 5/10 — Pivot rotation + cardinality cap + null strategy + export column expansion.

**Source**: item 32, pivot half.

**What we'd do**: rotate one dimension into dynamic columns — the spreadsheet pivot table.

**Spec**:
- GraphQL shape (GraphQL can't do dynamic top-level fields): `pivotKeys` (ordered column headers) + `rows { <dimension> cells { pivotValue <measures> } }` + `totals`. Tabular exports get the *actual* pivot shape — pivot values become real columns — since CSV/XLSX/Parquet support dynamic columns natively.
- `pivot_cardinality_cap` (default 200) bounds the dynamic column set; exceeding it is a typed error with the projected column count, suggesting a filter on the pivot dimension.
- Null pivot values: grouped as `"(no value)"` by default; `Meta.pivot_null_strategy = "skip" | "group_as" | "error"`.
- Cardinality drift across rows (some products have January data, others don't): cells are emitted for the union of pivot values with `null` measures where absent.
- Pivot carries its own cost weight (`per_pivot`, expensive by default) in the matrix cost model.

**Composes with**: `matrix_dimensions_and_measures` (prerequisite), `xlsx_export_format`, `tabular_export_of_list_fields`.

### `snapshot_token_protocol`

**Realistic**: 7/10 — Snapshot + token bookkeeping is real architecture, but the chunked ID store and pinned ordering remove the two failure modes.

**Impact**: 8/10 — The foundation of the 'GraphQL doesn't do bulk' answer; everything streaming stands on it.

**Difficulty**: 6/10 — Segmented ID store, ordering pin, token lifecycle, initiation guards.

**Source**: item 30, snapshot + token half.

**What we'd do**: durable point-in-time snapshots with opaque download tokens — the foundation under resumable bulk export.

**Spec**:
- Default `"ids"` snapshot mode: at initiation, materialize the matching primary keys to a token-scoped store plus a `snapshot_at` timestamp; chunk requests fetch live rows by ID. Deleted rows during the download produce per-chunk `missing_ids: [...]` metadata (default: skip + log; opt-in: error). Column updates show through — documented as the mode's contract.
- **The ID list is stored chunked, never as one cache entry.** At the scales this protocol targets (the cap defaults to 50M rows), a single ID-list entry is hundreds of MB — over most cache backends' value limits and a serialization stall besides. IDs persist in fixed-size segments (e.g. 100k IDs per segment) keyed by token + segment index; chunk serving reads only the segments it needs.
- **Initiation pins a deterministic ordering**: the snapshot captures an explicit `order_by` ending in a unique tiebreak (pk appended when absent). Resume-by-row-index is meaningless without it — an unpinned order silently skips or duplicates rows across resumes.
- Token contents (opaque to the client): requesting user, queryset hash, snapshot mode, snapshot pointer, `snapshot_at`, chunk size, total count, expiry.
- TTL: sliding window (default 2h from last activity, hard 24h cap). Expired-token requests → `410 Gone`, `code="dst.download.expired"`.
- Initiation guards: `max_snapshot_size` refusal (`code="dst.download.too_large"`); auth captured at initiation, with opt-in `recheck_auth_per_chunk` re-running `get_queryset` per chunk.
- `Meta.streamable = True` (or the rich dict: `chunk_size`, `snapshot_mode`, `ttl`, `max_snapshot_size`, `auto_stream_above`) enables the protocol; above `auto_stream_above`, a connection query returns the token in `extensions["dst.download"]` instead of inlined edges.

**Composes with**: `ndjson_streaming_view`, `per_chunk_streaming_optimizer_plan`, `full_and_pg_cursor_snapshot_modes`, `mutation_invalidation_gossip` (mutations list now-stale tokens), `rate_limit_extension` (concurrent-download and volume caps), `field_usage_and_deprecation_telemetry` (per-token row count / bytes / duration logging).

### `ndjson_streaming_view`

**Realistic**: 8/10 — Chunked HTTP + Range arithmetic + checksums; standard HTTP throughout by design.

**Impact**: 7/10 — The resume-after-drop DX nobody in the GraphQL ecosystem ships.

**Difficulty**: 4/10 — Download view + two resume forms + metadata frames + cancellation handling.

**Source**: item 30, transport half.

**What we'd do**: the download view — NDJSON over chunked HTTP with `Range` resume and integrity checksums.

**Spec**:
- Wire: newline-delimited JSON, one complete GraphQL row object per line (matching the initiating query's selection set), gzip-encoded over chunked transfer. Browser-friendly via `ReadableStream`; `curl --no-buffer | jq` works; a 20-line client in any language can speak it.
- Resume: `GET /graphql/download/<token>` with `Range: items=12000-`, or path-based `/graphql/download/<token>/from/12000` for browser-driven downloads. Resume past the final row → `416 Range Not Satisfiable`.
- Per-chunk metadata frame identifies the row-index range that follows; the final chunk carries `final: true` plus a SHA-256 checksum of the concatenated NDJSON body.
- Why not GraphQL multipart (`@defer`/`@stream` framing): sparse client tooling and no resume semantics in the spec — a custom resume layer is needed either way, so the simpler base protocol wins. Why not SSE: event-shaped reconnection semantics don't match request-driven bulk download.
- Client cancellation: the request-aborted signal stops the chunk loop; the token TTL keeps ticking so retry-within-TTL resumes.

**Composes with**: `snapshot_token_protocol` (prerequisite), `graphql_over_http_compliance` (`Cache-Control: private, no-store` on download streams), `invokable_typescript_client` (the typed async-iterator wrapper), `tabular_export_of_list_fields` (CSV/TSV ride the same view; Parquet/Arrow/XLSX restart fresh at the row offset on resume).

### `per_chunk_streaming_optimizer_plan`

**Realistic**: 8/10 — Reuses the existing selection-tree walk per ID-chunk; the loop is mechanical.

**Impact**: 7/10 — Flat memory across million-row exports is what makes the protocol production-real.

**Difficulty**: 4/10 — Plan-mode switch + per-chunk prefetch/discard cycle.

**Source**: item 30, optimizer half.

**What we'd do**: a streaming-mode optimizer plan that keeps memory flat across million-row exports.

**Spec**:
1. Pull the next `chunk_size` primary keys from the snapshot.
2. Build a one-shot queryset filtered to those IDs carrying the **same** `select_related` / `prefetch_related` / `only()` shape the non-streaming plan would have used (derived from the same selection-tree walk).
3. Iterate, serialize each row to one NDJSON line, flush.
4. Discard the chunk's prefetch cache and loop.

- The materialize-everything plan is correct for paginated queries and memory-blowing for streams; plan selection is automatic when a request arrives through the download protocol.
- All shipped `OptimizerHint` keys (`prefetch_related`, `select_related`, `SKIP`) apply unchanged inside each chunk; strictness mode applies per chunk.

**Composes with**: `snapshot_token_protocol` (prerequisite), `ndjson_streaming_view`, the shipped walker/plan machinery.

### `full_and_pg_cursor_snapshot_modes`

**Realistic**: 6/10 — Blob storage and WITH HOLD cursors are known tools; the consistency contracts need careful docs.

**Impact**: 5/10 — Stricter-consistency niches beyond the default mode.

**Difficulty**: 5/10 — Two backends + per-token serialization for cursor mode.

**Source**: item 30, additional snapshot modes.

**What we'd do**: the two stricter-consistency snapshot modes beyond default `"ids"`.

**Spec**:
- `"full"`: on initiation, write the complete result set to blob storage (S3 / GCS / Django default-storage) as gzipped NDJSON; chunk requests stream from the blob. Strictly consistent regardless of source-table mutations; expensive for huge datasets; the *"last night's full export for the warehouse load"* mode.
- `"pg_cursor"`: PostgreSQL `DECLARE ... WITH HOLD CURSOR`. Point-in-time strict, but holds a database connection for the snapshot lifetime — short-lived high-consistency exports only. Concurrent chunk requests for the same token are serialized in this mode (cursors are connection-bound); the other modes serve concurrent chunks freely.
- Mode selection via `Meta.streamable["snapshot_mode"]`; each mode's consistency contract is documented side by side so consumers pick on facts.

**Composes with**: `snapshot_token_protocol` (prerequisite), `ndjson_streaming_view`.

---

## Async & realtime

### `opt_in_async_resolvers`

**Realistic**: 7/10 — Django 4.2+ native async ORM covers most operations; gaps have documented sync fallbacks.

**Impact**: 7/10 — Async-first positioning + real perf for ASGI; the opt-in framing contains the risk.

**Difficulty**: 5/10 — Async variants per resolver template + `aprefetch_related_objects` plumbing + dual-mode test matrix.

**Source**: item 9, first half.

**What we'd do**: opt-in async variants for every generated resolver, cooperating with Django's native async ORM.

**Spec**:
- Behind an explicit flag (per schema or per type), generated resolvers go async, using `aget` / `aiter` / `acount` / `aexists` / `aupdate` / `adelete` and `aprefetch_related_objects` for the optimizer's prefetch step.
- Sync fallback (via `sync_to_async`) only for the ORM operations without native async equivalents, each documented.
- The Relay-specific async slice (sync/async `_resolve_node_default` / `_resolve_nodes_default`) already shipped with the Node foundation; this card is the broader push across every generated resolver.
- The test matrix runs both modes for every resolver template — the cost is real and budgeted into the card, not discovered later.

**Composes with**: shipped Relay async paths, `async_by_default_flip`, `signal_wired_subscriptions` (async transport).

### `async_by_default_flip`

**Realistic**: 7/10 — Mostly a default change after the opt-in card soaks; the work is migration notes and matrix coverage.

**Impact**: 5/10 — Positioning win; sync-WSGI shops are unaffected by design.

**Difficulty**: 3/10 — Default flip + pinning escape hatch + migration docs.

**Source**: item 9, second half — a separate, later card by design.

**What we'd do**: flip the default so every generated resolver is async unless opted out.

**Spec**:
- Sequenced strictly after `opt_in_async_resolvers` has soaked for at least a release or two in real ASGI deployments. "Async by default" on day one doubles the support surface before the async paths have proven out; opt-in-first is the explicit strategy, the flip is the destination.
- Ships with migration notes for sync-WSGI deployments (what changes, what doesn't, how to pin sync mode).

**Composes with**: `opt_in_async_resolvers` (hard prerequisite).

### `signal_wired_subscriptions`

**Realistic**: 5/10 — Channels integration is well-trodden but Channels is complex; signal-to-push at scale has fan-out and ordering gotchas even with `on_commit` settled.

**Impact**: 7/10 — Real-time SaaS use case both upstreams punt on.

**Difficulty**: 8/10 — Transport + subscription machinery + permission integration + signal lifecycle; substantial.

**Source**: item 8.

**What we'd do**: declarative `Meta.subscriptions = ("post_save", "post_delete", "m2m_changed")` auto-wiring a type into Channels with filtered, permission-respecting pushes.

**Spec**:
- **Every push routes through `transaction.on_commit`.** `post_save` fires *inside* the transaction; pushing on the signal directly sends phantom events for writes that subsequently roll back. This is the classic bug of the feature class and the non-negotiable line of the spec.
- Subscription visibility runs through `get_queryset` (and the permission cards when they land): a subscriber receives only events for rows they could query.
- **Documented coverage gap, stated loudly**: Django signals do not fire on `queryset.update()`, `bulk_update`, `bulk_create(ignore_conflicts=...)`, or raw SQL. The feature is "signal-wired", not "change-data-capture"; consumers needing completeness for bulk paths are pointed at explicit publish hooks.
- Transport: Channels as the first-class backend (soft dependency); the signal→publish seam is transport-agnostic so other async backends can plug in.
- Subscription-time policy checks happen at subscription open; a per-event-flood defense (e.g. a `SubscriptionConcurrencyCap` policy) belongs to the DoS stack.

**Composes with**: `opt_in_async_resolvers`, `declarative_row_and_field_permissions`, `dos_policy_stack_framework`.

---

## Federation

### `apollo_federation_meta_surface`

**Realistic**: 5/10 — Federation 2 is well-spec'd and the sub-graph surface is bounded, but the gateway is operationally external.

**Impact**: 6/10 — Narrow audience with an 'of course this works' expectation; invisible otherwise.

**Difficulty**: 8/10 — Federated type generation + entity resolution + directive support through the Meta surface.

**Source**: item 34.

**What we'd do**: a `federation/` subpackage mirroring `strawberry-django`'s federation contract, driven by Meta declarations instead of decorators.

**Spec**:

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

- Federation 2 directives (`@key`, `@shareable`, `@tag`) emitted from the Meta dict; entity-resolution endpoint generated per keyed type.
- **Entity resolution runs through the type's `get_queryset`** — federated lookups respect the same row visibility as every other read path; no permission bypass via the gateway.
- The Apollo Gateway itself is out of scope (operational, external); the card ships the sub-graph side plus composition docs.

**Composes with**: `declarative_row_and_field_permissions`, `typed_error_envelope_and_code_registry` (federated error semantics), `dos_policy_stack_framework` (entity-resolution endpoints carry their own rate/cost policies).

---

## Parked

Cards in this section are intentionally unscheduled — kept for design context, pulled forward only on concrete demand.

### `sharding_aware_optimizer`

**Realistic**: 3/10 — Cross-shard joins are genuinely hard and Django's ORM doesn't help; the planning seam must be invented.

**Impact**: 4/10 — Strong for sharded-Django shops; invisible to everyone else, but that audience has nowhere else to go.

**Difficulty**: 8/10 — Cross-shard planning, shard-aware Prefetch reconciliation, cross-shard aggregate composition.

**Source**: item 41.

**What we'd do**: a multi-database story beyond the shipped polite cooperation ([019-multi_database_cooperation_contract-0.0.7][card-multi-database-cooperation-contract]) — first-class shard-aware planning.

**Spec**:
- The optimizer detects when a planned join would cross shards and downgrades to a routed `Prefetch` instead of failing or N+1ing.
- `Meta.preferred_database = "shard_b"` declares a type's home shard so routing is automatic without `.using()` boilerplate; the routing decision may also live in `Meta.get_queryset` per type.
- Multi-shard aggregates compose per-shard results (count/sum/min/max trivially; avg and group-by need explicit reduce semantics).
- M2M through-tables respect routing for the through-table's database; sharded connections paginate within a shard, not across (cooperating with [024-connection_aware_optimizer_planning-0.0.9][card-connection-aware-optimizer-planning]).
- Cross-shard routing failures surface through the typed error envelope with a stable code.

**Composes with**: shipped multi-database cooperation contract, `dos_policy_stack_framework` (per-shard budgets), `generic_foreign_key_support` / `django_polymorphic_union_types` (targets on different shards).

### `proto_migrations_system`

**Realistic**: 7/10 — Mirrors the Django-migrations pattern; bounded generator + checker commands.

**Impact**: 3/10 — No in-package consumer after the gRPC strike; design value and third-party value only.

**Difficulty**: 5/10 — Field-number history + reserved-range tracking + CI checker.

**Source**: extracted from struck item 31 — the one piece worth keeping independent of any gRPC transport.

**What we'd do**: a Django-migrations-style history for protobuf field numbers, for any future or external `.proto` surface derived from `DjangoType` declarations.

**Spec**:
- `manage.py makeprotos` generates a migration capturing the current schema's field numbers, deletions (as `reserved` ranges), and oneofs; history lives in `proto_migrations/`, checked in; applied state writes canonical `.proto` files to `proto/`.
- `manage.py checkprotos` runs in CI and fails on: a removed field whose number wasn't reserved, a reused number, a type with no assigned numbers. `--reserve-removed` mode handles removals automatically.
- The schema author never picks field numbers; the migration system assigns on first appearance and locks forever.
- Parked because it has no in-package consumer after item 31's strike; it stands alone as a design, and would also serve third parties generating protos from the registry.

### `composite_pk_globalid`

**Realistic**: 4/10 — Blocked on Django's composite-pk API stabilizing; nothing to build against yet.

**Impact**: 3/10 — Unblocks a small set of schemas; loud rejection is acceptable meanwhile.

**Difficulty**: 6/10 — Deterministic encoding + multi-type dispatch resolution.

**Source**: Relay/interface parking lot.

**What we'd do**: deterministic composite-primary-key GlobalID encoding/decoding, once Django's composite-pk API stabilizes.

**Spec**:
- Current behavior (loud rejection) stands until Django's composite-pk surface is stable enough to encode against.
- The encoding must be order-deterministic and round-trip-safe; the multi-encoding question (composite pk + `Meta.primary` multiple types per model) routes through `globalid_alias_map`'s machinery if more than one valid encoding ever exists.
- Node lookup with [multiple `DjangoType`s per model][card-multiple-djangotypes-per-model-with-metaprimary] must resolve which GraphQL type a decoded ID dispatches to; that resolution rule is part of this card.

**Composes with**: shipped model-anchored GlobalID encoding, `globalid_alias_map`.

### `relay_meta_alias_shortcut`

**Realistic**: 10/10 — An alias over a shipped contract.

**Impact**: 2/10 — Pure ergonomics; one line saved per type.

**Difficulty**: 1/10 — Trivial once the contract is stable.

**Source**: Relay/interface parking lot.

**What we'd do**: `Meta.relay = True` (or `Meta.node = True`) as an alias for `interfaces = (relay.Node,)`.

**Spec**:
- Reconsidered only after the explicit `Meta.interfaces` contract has been stable across several releases; the current single-interface normalization (`interfaces = relay.Node` without a tuple) remains the only convenience shortcut until then.
- No new top-level exports ride along with it.

**Composes with**: shipped `Meta.interfaces` foundation.

---

## Struck

Per this file's policy, rejected differentiators are struck with a one-line reason, not deleted.

- ~~`rest_escape_hatch` (item 16: REST endpoints from the same `DjangoType` declarations)~~ — struck: the target audience identified by `drf_serializer_mutations` already runs DRF and therefore already has REST; building a parallel HTTP stack duplicates DRF for an audience that owns it. Demoted to a documentation pattern ("mounting DRF viewsets alongside your DjangoTypes").
- ~~`grpc_sibling_protocol` (item 31: gRPC from the same declarations)~~ — struck: the cost lives outside Python (HTTP/2 lifecycle, Envoy/gRPC-Web bridging, multi-language codegen), and proto3's absent-collapses-to-zero semantics conflict with GraphQL's nullable-by-default fields in every generated message. The salvageable piece is extracted as `proto_migrations_system` (parked).
- ~~`connection_auto_upgrade_threshold` (item 39, sub-feature 4: per-request list→connection upgrade above a row-count threshold)~~ — struck: the server cannot change the response shape of a field the client already selected, so a per-request threshold can't do what the sketch described; the useful half (declare both shapes, recommend the connection) already shipped in 0.0.9 as `Meta.relation_shapes` / the `"both"` default.

---

## Moved out of this file

Items 36, 37, and 38 were process rules, not feature cards; they move to `AGENTS.md` / `CONTRIBUTING.md`:

- **Public surface promotion discipline** (item 37) — the checklist for adding symbols to `__all__`.
- **Shared queryset introspection helpers** (item 36) — promote embedded helpers to `utils/queryset.py` only when a second subsystem needs them.
- **Layered manual relation override test policy** (item 38) — internals tests as the canary, HTTP tests as the contract.

Item 13 (`Meta.field_overrides` for scalar fields) is already promoted as `KANBAN.md` `READY-003` and carries no card here. Parking-lot entries covered by shipped 0.0.9 work (root node fields, `DjangoConnectionField`, GlobalID test helpers, the model-anchored encoding) are likewise retired.

---

## How to use this file

- When scheduling a slice after parity items land, pull a `BACKLOG.md` card that isn't already on `KANBAN.md`.
- Promote it to a `KANBAN.md` `TODO-*` card (or `BACKLOG-*` if it's not committed to a milestone yet).
- Sanity-check the card's **Realistic** / **Impact** / **Difficulty** scores at promotion time; re-score if the landscape has moved.
- Respect each card's stated prerequisites (`Composes with` lines marked *prerequisite*) and the DoS group's primitives-first sequencing rule.
- Write its `docs/spec-<NNN>-<topic>-<0_0_X>.md` and follow the existing slice cadence.
- When the slice ships, cross-reference the `BACKLOG.md` card from the new `KANBAN.md` `DONE-*` card so the differentiation story stays traceable.

If a card turns out to be wrong (the upstream packages ship it, real-world adopters don't want it, or the architectural cost is too high), strike it through with a one-line note explaining why; do not delete it. The history of rejected differentiators is itself useful design context — see the Struck section.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[card-optimizer-explain-mode]: KANBAN.md#optimizer_explain_mode
[card-django-model-based-globalid-encoding]: KANBAN.md#django_model_based_globalid_encoding
[card-connection-aware-optimizer-planning]: KANBAN.md#connection_aware_optimizer_planning
[card-full-relay-story-node-connection-root-validation]: KANBAN.md#full_relay_story_node_connection_root_validation
[card-multi-database-cooperation-contract]: KANBAN.md#multi_database_cooperation_contract
[card-multiple-djangotypes-per-model-with-metaprimary]: KANBAN.md#multiple_djangotypes_per_model_with_metaprimary
[card-mutation-transactions-and-idempotency]: KANBAN.md#mutation_transactions_and_idempotency
[kanban]: KANBAN.md

<!-- docs/ -->
[spec-035]: docs/spec-035-optimizer_hardening-0_0_10.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
