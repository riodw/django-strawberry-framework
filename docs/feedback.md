# Feedback: `docs/spec-019-multi_db-0_0_7.md` (rev3)

Reviewer pass against the spec as it stands at rev3 (post-rev2 R1–R10 corrections). Verified against the live codebase as of 2026-05-22:

- `django_strawberry_framework/types/resolvers.py` (full read)
- `django_strawberry_framework/utils/relations.py` (full read — `RelationKind` enum + `MANY_SIDE_RELATION_KINDS` set)
- `django_strawberry_framework/optimizer/walker.py` (lines 1-170 + 460-540 — `plan_optimizations` signature, `_build_child_queryset`, `_prefetch_hint_for_path`)
- `django_strawberry_framework/optimizer/plans.py` (lines 95-160 — `OptimizationPlan.apply`)
- `django_strawberry_framework/optimizer/hints.py` (full read — `OptimizerHint.prefetch(obj)` factory)
- `pyproject.toml` (lines 95-115 — `per-file-ignores` block)
- `examples/fakeshop/test_query/test_library_api.py` (lines 17-43 — autouse reload fixture)

Three High findings (H1-H3) are correctness blockers — Worker 2 following the rev3 wording literally would write tests that either raise `TypeError` at call time or assert against the wrong code path. Two Medium findings (M1-M2) are doc/wording drift that the rev3 narrative does not catch. Three Low findings (L1-L3) are polish.

---

## High

### H1 — `plan_optimizations()` signature drift in Slice 1 test (f)

[Test plan](#test-plan) `tests/optimizer/test_multi_db.py` test (f) `test_optimization_plan_apply_preserves_explicit_using_alias` says:

> Builds a fixture `DjangoType` with one FK relation; constructs a plan via `plan = plan_optimizations(selections, model, parent_type)`; applies it via `result = plan.apply(Model.objects.using("shard_b").all())`; asserts `result._db == "shard_b"`.

The actual signature at `django_strawberry_framework/optimizer/walker.py:28-32` is:

```python
def plan_optimizations(
    selected_fields: list[Any],
    model: type[models.Model],
    info: Any | None = None,
    *,
    source_type: type | None = None,
) -> OptimizationPlan:
```

There is no `parent_type` positional argument. The third positional is `info` (a GraphQL info or `None`); the resolver-type pin is the keyword-only `source_type`. Worker 2 writing `plan_optimizations(selections, model, parent_type)` produces a call that binds `parent_type` to `info` — which works only by accident (the body's `info=None` default is replaced by a class object, which the walker then passes to `runtime_path_from_info` at `plans.py:152` and which dies as soon as the walker calls `info.path`).

Fix: rewrite the call shape in test (f) to one of:

- `plan = plan_optimizations(selected_fields, model)` — simplest, ignores the source-type lookup since the test does not exercise per-type optimizer-hints (those are exercised by test (g) instead).
- `plan = plan_optimizations(selected_fields, model, source_type=parent_type)` — pins the keyword-only argument explicitly if the test wants the resolver-type lookup.

Also rename the first arg in the spec from `selections` to `selected_fields` to match the live parameter name. The rev2 H3 fix correctly identified that `plan_optimizations` takes selections + model (not a queryset), but the rev3 wording did not propagate the keyword-only `source_type` rename.

This is the same surface that motivated the rev2 H3 correction; the leftover argument shape is the residual that rev3 did not catch.

---

### H2 — `kind="many_to_one"` is not a valid `RelationKind`

[Test plan](#test-plan) `tests/types/test_resolvers.py` test (e) `test_strictness_check_is_connection_agnostic_under_non_default_alias` says:

> exercises `_check_n1(info, root, field_name, parent_type, kind="many_to_one")` …

The live `RelationKind` literal at `django_strawberry_framework/utils/relations.py:7-12` allows exactly four values:

```python
RelationKind: TypeAlias = Literal[
    "many",
    "reverse_many_to_one",
    "reverse_one_to_one",
    "forward_single",
]
```

`"many_to_one"` is not one of them. Worker 2 writing `kind="many_to_one"` would get past `_check_n1`'s body without a type-check failure (the runtime accepts any string), but:

- `is_many_side_relation_kind("many_to_one")` returns `False` (the membership set is `{"many", "reverse_many_to_one"}` per `utils/relations.py:14-19`), so the lazy-load detector falls through to `_will_lazy_load_single`, NOT the many-side path the test setup implies (see H3).
- The string `"many_to_one"` advertises a relation shape Django's docs use for forward FK, but the package's classifier uses `"forward_single"` for that shape (verified at `utils/relations.py:63-71`). A future grep for "is this test still aligned with the classifier?" would mislead.

Fix: change `kind="many_to_one"` to `kind="forward_single"` in [Goals](#goals) item 2 (e), [Slice checklist](#slice-checklist), and [Test plan](#test-plan). The semantic the test pins (FK lazy-load on a `_state.db = "shard_b"` row → `OptimizerError("Unplanned N+1: shelf")`) maps cleanly to `"forward_single"`.

Companion check: search the rest of the spec for any `"many_to_one"` literal to ensure no other reference was added in rev3 and missed here.

---

### H3 — Setup mismatch: `_prefetched_objects_cache = {}` on a non-many-side `kind`

Same test (e) [Test plan](#test-plan) wording (carried over from rev2 H6 and not adjusted in rev3 R2):

> exercises `_check_n1(info, root, field_name, parent_type, kind="many_to_one")` with `info.context` carrying `DST_OPTIMIZER_STRICTNESS = "raise"`, a non-empty planned set that does NOT include the resolver_key, and `root._prefetched_objects_cache = {}` so the lazy-load detector trips …

`_check_n1` at `types/resolvers.py:119-154` branches on `is_many_side_relation_kind(kind)`:

```python
if is_many_side_relation_kind(kind):
    lazy = _will_lazy_load_many(root, field_name)   # reads _prefetched_objects_cache
else:
    lazy = _will_lazy_load_single(root, field_name)  # reads __dict__ + _state.fields_cache
```

The single-valued path at `_will_lazy_load_single` (`types/resolvers.py:86-101`) inspects:

```python
if field_name in getattr(root, "__dict__", {}):
    return False
state = getattr(root, "_state", None)
fields_cache = getattr(state, "fields_cache", {})
return field_name not in fields_cache
```

`_prefetched_objects_cache` is irrelevant on this path. After H2's fix (`kind="forward_single"`), the spec's pinned setup `root._prefetched_objects_cache = {}` does nothing — the test would still happen to pass if the synthetic test double happens not to populate `__dict__` or `_state.fields_cache` for the field name, but the setup steps are misleading and the next maintainer reading the test will not understand what trips the detector.

Fix: rewrite the setup pin to be consistent with the chosen `kind`. Two coherent options:

- (Recommended, paired with H2's `kind="forward_single"`): "Ensure `field_name not in root.__dict__` and `field_name not in root._state.fields_cache` so `_will_lazy_load_single` reports the relation is unloaded; set `root._state.db = 'shard_b'` to prove the connection-agnostic shape; do NOT set `root._prefetched_objects_cache` — the single-valued path does not consult it."
- (Alternative): switch the test's framing to a many-side relation by pinning `kind="many"` or `kind="reverse_many_to_one"`. Keep `root._prefetched_objects_cache = {}` because the many-side path consults it. This is a coherent shape but loses the "FK on shard_b" intuition the rev3 R8 narrative pinned.

Recommend Option 1 because the FK lazy-load shape is the natural illustration of "row from shard_b, descriptor would route through the parent's `_state.db`, strictness blocks the load and surfaces the same error class as single-DB."

---

## Medium

### M1 — KANBAN Done-body summary count contradicts rev3 R2

[Doc updates](#doc-updates) → [`KANBAN.md`](../KANBAN.md) Done-body wording at line 545 still says:

> Tests in [`tests/types/test_resolvers.py`](tests/types/test_resolvers.py) (four resolver-level tests against `_build_fk_id_stub`, hermetic via mocked router) and [`tests/optimizer/test_multi_db.py`](tests/optimizer/test_multi_db.py) (three optimizer-plan-level tests against `OptimizationPlan.apply` and `OptimizerHint.prefetch` round-trip and `_check_n1`) …

This is the rev2-era split (4 + 3). Rev3 R2 moved the strictness test to `tests/types/test_resolvers.py`, making the split **five** resolver-level (the four FK-id tests + strictness) and **two** optimizer-plan-level. The Slice 3 KANBAN edit lands directly from this spec text, so the post-ship card body would document the wrong count.

Fix: rewrite the parenthetical to:

> Tests in [`tests/types/test_resolvers.py`](tests/types/test_resolvers.py) (five resolver-level tests against `_build_fk_id_stub` and `_check_n1` — four FK-id elision branches plus the strictness connection-agnostic shape; FK-id tests hermetic via mocked router) and [`tests/optimizer/test_multi_db.py`](tests/optimizer/test_multi_db.py) (two optimizer-plan-level tests against `OptimizationPlan.apply` and `OptimizerHint.prefetch` round-trip).

Remove the trailing "and `_check_n1`" from the optimizer-plan parenthetical — `_check_n1` is no longer exercised in that file post-rev3 R2.

Cross-check: the CHANGELOG entry at line 552 carries the same split-by-file framing ("resolver-level FK-id elision unit tests … optimizer-plan-level `apply` / hint / strictness shape"); the "/ strictness shape" mention there is also stale post-rev3 R2. Rewrite to "optimizer-plan-level `apply` / `OptimizerHint.prefetch` round-trip."

---

### M2 — Plan-cache and consumer-provided `Prefetch` aliases: clarify the bound-by-type guarantee

[Edge cases and constraints](#edge-cases-and-constraints) item "Optimizer plan cache key does NOT include the database alias" says:

> Per the shipped [`Plan cache`](GLOSSARY.md#plan-cache) entry, cache keys include the operation AST, target model, and root runtime path — not the queryset's `_db`. Two resolvers on the same model targeting different shards share a cached plan; correct, because the plan is selection-shaped, not connection-shaped.

This is correct **for generated `prefetch_related` lookups** (string lookups carry no queryset), but the spec also commits (Decision 3 axis 3 + test (g)) that consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=using("shard_b").all()))` round-trips with the queryset's `_db` intact. The cached plan therefore contains a `Prefetch` object bound to `shard_b`. If two resolvers on the same model share the cache key but one wants `shard_a` rows on its child relation, the second resolver would silently get a `shard_b`-bound `Prefetch`.

In practice this is safe because `Meta.optimizer_hints` is per-`DjangoType` (not per-resolver-call), and the cache key includes the parent type via `resolver_key(parent_type, …)` at `plans.py:140-149`. Two distinct `DjangoType` classes that declare different hints get different cache entries; two resolvers using the same `DjangoType` necessarily share the same hint config and therefore the same `Prefetch(queryset=…)` choice.

Fix: add one sentence to the edge-case clarification:

> Cache keys do not include the queryset's `_db`, but consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…using…))` hints are bound to the parent `DjangoType` via `Meta.optimizer_hints` (per [`OptimizerHint`](GLOSSARY.md#optimizerhint)), so two resolvers that use the same parent type necessarily share the same consumer-provided alias choice. The cache invariant holds: a single cached plan is selection-shaped + type-scoped, not connection-shaped, and the consumer's `_db` choice is a per-type decision rather than a per-call one.

Tracked here rather than as a new test because the existing test (g) already pins the round-trip for the hint-bound case; adding a "two resolvers on the same model share or do not share the hint" test would be over-coverage of consumer-shaped configuration.

---

## Low

### L1 — [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) header imports: explicitly justify `importlib` / `sys`

The pinned module header at lines 326-350 imports `importlib`, `os`, `sys`, `pytest` at the top — but the excerpt does not show where `importlib` and `sys` are used. Verified at `examples/fakeshop/test_query/test_library_api.py:17-43`: the copied autouse fixture uses `sys.modules.get(...)`, `importlib.reload(...)`, `importlib.import_module(...)`, and `clear_url_caches()`. The imports are necessary; the spec could state this in a one-line annotation so the next reader does not flag them as unused.

Suggested annotation under the pinned-shape block:

> The top-block `importlib` / `sys` imports support the copied autouse reload fixture (per Decision 7) — it uses `sys.modules.get(...)` + `importlib.reload(...)` / `importlib.import_module(...)` to recreate `apps.library.schema`, `config.schema`, and `config.urls` after the registry is cleared.

Not a blocker; Worker 2 can figure this out from the fixture body.

---

### L2 — Implementation-plan table line-delta does not reflect rev3 R2 split

[Implementation plan](#implementation-plan) row 1 says "five in `tests/types/test_resolvers.py` … plus two in `tests/optimizer/test_multi_db.py`" — correct counts, but the rev2 H4 annotation in the same cell still names "split from rev1's single-file framing" without the rev3 R2 callout ("strictness test relocated here from `tests/optimizer/test_multi_db.py` because `_check_n1` lives in `types/resolvers.py`"). The body of the spec's [Slice checklist](#slice-checklist) carries the rev3 R2 annotation correctly; the table row is the one place it slipped.

Suggested fix: append "; rev3 R2 — strictness test relocated from the optimizer-plan file" to the table-row annotation list.

---

### L3 — `pytest.skip(allow_module_level=True)` cited line numbers vs. actual

Live `examples/fakeshop/test_query/test_library_api.py:17-43` does NOT contain a module-level `pytest.skip(allow_module_level=True)` call — that fixture is for registry-clear-reload, not the env-var gate. Spec [Decision 7](#decision-7--reuse-the-test_library_api-reload-fixture-verbatim) is correctly framed (it copies the reload fixture, not a skip-block). But spec [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) bullet 2 says "The pattern mirrors `examples/fakeshop/test_query/test_library_api.py`'s autouse fixture shape (Slice 2 copies that fixture) but with an additional early-module-skip guard." That is accurate.

No code change needed; flagged because the rev3 reviewer might double-take seeing "mirrors test_library_api.py" + "module-level pytest.skip" together — the skip is additive over the fixture, not from the fixture. The wording already says "additional" — that is clear enough on a second read. No fix; tracked here so a rev4 author does not "simplify" this clause.

---

## What looks solid

- The four-axis [Decision 3](#decision-3--the-cooperation-contract-four-axes) narrowing (rev2 H2/H6 → rev3 R1) is internally consistent and verifiable against `types/resolvers.py:82` (axis 1), `optimizer/plans.py:122` (axis 2), `optimizer/walker.py:129` + `optimizer/hints.py:118` (axis 3), and `types/resolvers.py:119-154` (axis 4). The "what's NOT in scope" list (cross-shard joins, multi-shard aggregates, routing policy, default-database selection) is a clean fence.
- The rev3 R4/R5 holder-pattern URLConf + per-test-fixture-after-autouse-reload design correctly resolves the rev2 H7 / Decision 7 conflict. Worker 2 has a concrete pattern to land.
- The rev2 H4 mirror-rule split (`tests/types/test_resolvers.py` for resolver-level + `tests/optimizer/test_multi_db.py` for optimizer-plan-level) honors `docs/TREE.md`'s contract and matches the source-mirror placement of `_build_fk_id_stub` (`types/resolvers.py`) and `OptimizationPlan.apply` (`optimizer/plans.py`). Rev3 R2's strictness-test relocation is the right call for the same reason.
- The rev2 H5 null-FK / parent-lacks-`_state` split into two tests catches a real code-path distinction at `types/resolvers.py:74-76` (early return) vs `:81` (`hasattr(root, "_state")` fallback). The two tests pin different branches and a regression in either is a different bug.
- The joint-`0.0.7` cut policy in [Decision 9](#decision-9--joint-0_0_7-cut) restates the spec-016 Decision 10 policy verbatim and is consistent with the live `CHANGELOG.md` `[0.0.7]` heading + the unbumped `pyproject.toml` / `__init__.py` / `tests/base/test_init.py` triplet. The version-bump-deferred posture is the right one.
- The "zero new public exports" pin + the no-edit list for `README.md` / `GOAL.md` / `TODAY.md` / `docs/TREE.md` ([Decision 8](#decision-8--no-readme--goal--today-edits)) matches the shipped spec-017 and spec-018 posture for plumbing-only cards.
- The companion CSV at `docs/spec-019-multi_db-0_0_7-terms.csv` correctly excludes `Meta.preferred_database` (rev2 S12) and anchors every other term used in the spec body to a real glossary heading.

---

## Notes for the spec author (rev4 candidates)

- H1 / H2 / H3 are correctness blockers and should land in the rev4 spec edit before Worker 0 spawns Slice 1.
- M1 / M2 are doc-edit-only fixes that catch wording drift; they do not block Slice 1 but should land in the same rev4 pass so Slice 3's KANBAN/CHANGELOG copies pull from the corrected text.
- L1-L3 are polish; safe to address inline during the rev4 pass or to defer to Worker 1 planning notes.
- After applying H1-M2 fixes, do a final consistency sweep on every occurrence of these strings in the spec to ensure none were missed:
  - `plan_optimizations(` (must take `selected_fields, model[, info][, *, source_type]`)
  - `kind="many_to_one"` → `kind="forward_single"`
  - `_prefetched_objects_cache` (must only appear in many-side test setup)
  - `four resolver-level tests` / `three optimizer-plan-level tests` → `five` / `two`
  - `and `_check_n1`)` (in the optimizer-plan parenthetical — should be removed)

End of feedback.
