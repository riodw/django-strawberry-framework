# Feedback: `docs/spec-019-multi_db-0_0_7.md` (rev4)

Second-pass review against the spec at rev4 (post-rev3 V1–V8 corrections). Surfaced by staging the pre-build TODO scaffolds in `tests/optimizer/test_multi_db.py`, `tests/types/test_resolvers.py` (extension), and `examples/fakeshop/test_query/test_multi_db.py` — pseudo-coding each test against the spec's pinned contract turned up one High-severity cross-reference bug the rev3 reviewer (and the rev4 author's V7 catalog sweep) missed, plus two Medium hazards Worker 2 will hit during implementation if not pre-flagged.

Verified against the live codebase as of 2026-05-22:

- `django_strawberry_framework/optimizer/plans.py:122` (`OptimizationPlan.apply`), `:140-149` (`resolver_key`), `:152-180` (`runtime_path_from_info` / `runtime_path_from_path`)
- `django_strawberry_framework/optimizer/walker.py:28-32` (`plan_optimizations` signature), `:119-126` (`_resolve_optimizer_hints`), `:129-144` (`_build_child_queryset`), `:503-532` (`_prefetch_hint_for_path`)
- `django_strawberry_framework/types/resolvers.py:70-83` (`_build_fk_id_stub`), `:86-101` (`_will_lazy_load_single`), `:119-154` (`_check_n1`)
- `django_strawberry_framework/utils/relations.py:7-19` (`RelationKind` literal + `MANY_SIDE_RELATION_KINDS`)
- `tests/types/test_resolvers.py:44-49` (existing `_isolate_registry` autouse fixture)
- `examples/fakeshop/test_query/test_library_api.py:17-43` (the reload fixture body Slice 2 copies)

---

## High

### H1 — Decision 3 axis-to-test letter cross-references are off-by-one (rev3 R2 strictness relocation didn't propagate)

The Test plan's authoritative letter mapping (per Goals item 2 + the Test plan section) is:

| Letter | File | Test name | Decision 3 axis |
|---|---|---|---|
| (a) | `tests/types/test_resolvers.py` | `test_fk_id_elision_stub_sets_state_db_via_router_db_for_read` | axis 1 |
| (b) | `tests/types/test_resolvers.py` | `test_fk_id_elision_router_call_passes_parent_row_as_instance` | axis 1 |
| (c) | `tests/types/test_resolvers.py` | `test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state` | axis 1 |
| (d) | `tests/types/test_resolvers.py` | `test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router` | axis 1 |
| (e) | `tests/types/test_resolvers.py` | `test_strictness_check_is_connection_agnostic_under_non_default_alias` | **axis 4** |
| (f) | `tests/optimizer/test_multi_db.py` | `test_optimization_plan_apply_preserves_explicit_using_alias` | **axis 2** |
| (g) | `tests/optimizer/test_multi_db.py` | `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` | **axis 3** |

But Decision 3's per-axis verification cross-references at spec lines 267-269 carry the rev2-era numbering — rev2 had the strictness test in `tests/optimizer/test_multi_db.py` as (g), the apply-preserves test as (e), and the consumer-Prefetch test as (f). Rev3 R2 relocated the strictness test to `tests/types/test_resolvers.py`, which shifted the optimizer-plan-file letters up by one (rev2's (e) → rev3's (f); rev2's (f) → rev3's (g); rev2's (g) → rev3's (e), in the OTHER file). The Slice checklist (line 74), Goals item 2 (line 126), Test plan (lines 491-508), and DoD item 2 (line 601) all use the correct post-rev3 numbering. **Decision 3 axes 2/3/4 still use the pre-rev3 numbering.**

The three concrete misreferences:

- **Line 267 (axis 2)**: "Verified by Slice 1's optimizer-plan test **(e)** per [Test plan]." There is no test (e) in `tests/optimizer/test_multi_db.py` — (e) is the strictness test, which lives in `tests/types/test_resolvers.py`. **Should say "optimizer-plan test (f)"**.
- **Line 268 (axis 3)**: "Verified by Slice 1's optimizer-plan test **(f)** per [Test plan]." (f) is the apply-preserves test (axis 2), not the consumer-Prefetch test (axis 3). **Should say "optimizer-plan test (g)"**.
- **Line 269 (axis 4)**: "Verified by Slice 1's optimizer-plan test **(g)** per [Test plan]." (g) is the consumer-Prefetch test (axis 3), and it lives in `tests/optimizer/test_multi_db.py`. The strictness test (axis 4) is (e) and lives in `tests/types/test_resolvers.py` per rev3 R2. **Should say "resolver-level test (e) in `tests/types/test_resolvers.py`"** (note: drop the "optimizer-plan" modifier — the strictness test is no longer at that layer).

Worker 2 reading "Decision 3 axis 4 is verified by optimizer-plan test (g)" would either (a) put the strictness test back in `tests/optimizer/test_multi_db.py` (silently undoing rev3 R2's mirror-rule fix) or (b) realize the cross-reference is wrong and have to chase three different sections of the spec to reconstruct the intended mapping. Either path costs Worker 2 review-cycle time that the spec's whole job is to prevent.

This is the same drift class rev4 V7 catalogged for the Implementation-plan table row — V7 confirmed the table row was already correct; the V7 sweep did not extend to Decision 3 axis cross-references. Treat this finding as the V7 sweep's missed scope.

**Fix:** rewrite the three "Verified by" sentences:

- Line 267: "Verified by Slice 1's optimizer-plan-level test (f) — `test_optimization_plan_apply_preserves_explicit_using_alias` in `tests/optimizer/test_multi_db.py` — per [Test plan](#test-plan)."
- Line 268: "Verified by Slice 1's optimizer-plan-level test (g) — `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` in `tests/optimizer/test_multi_db.py` — per [Test plan](#test-plan)."
- Line 269: "Verified by Slice 1's resolver-level test (e) — `test_strictness_check_is_connection_agnostic_under_non_default_alias` in `tests/types/test_resolvers.py` — per [Test plan](#test-plan) (rev3 R2 — relocated from the rev2 `tests/optimizer/` framing per the [`docs/TREE.md`](TREE.md) mirror rule; this verification cross-reference is rev5-corrected to match)."

The longer "Verified by …test (X) — `<test_name>` in `<file>`" form is heavier on prose but kills the off-by-one bug class outright by naming the test rather than relying on a positional letter that drifts across revisions.

---

## Medium

### M1 — Edge case bullet "Consumer-provided Prefetch _db round-trip" cites the wrong test letter (same drift as H1)

Spec line 483:

> Slice 1's optimizer-plan test **(f)** introspects the post-plan `_prefetch_related_lookups` to assert the package round-trips that intact …

The consumer-`Prefetch` round-trip introspection is test (g), not test (f). Test (f) is the apply-preserves test (axis 2), which asserts `result._db == "shard_b"` on the parent queryset — a different assertion shape that does NOT introspect `_prefetch_related_lookups`.

Fix: change "test (f)" to "test (g)" in this bullet.

### M2 — Risks/open-questions bullet "Consumer-provided Prefetch _db round-trip under Django version changes" has the same drift

Spec line 580:

> The Slice 1 optimizer-plan test **(f)** pins the package's cooperation by introspecting the post-plan `_prefetch_related_lookups` …

Same bug class as M1. Fix: change "test (f)" to "test (g)".

After H1/M1/M2 are landed, recommend a final consistency sweep with `grep -n "test ([a-g])" docs/spec-019-multi_db-0_0_7.md` to confirm no other letter cross-reference slipped past the rev3 R2 relocation.

---

## Low

### L1 — Decision 6 pinned import block carries names the test module doesn't directly use (F401 risk)

Spec line 357 pins the test-module imports below the skip block as:

```python
from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
```

But the pseudocode that follows (lines 366-391 — the holder pattern + `_build_test_schema` fixture) uses only `DjangoOptimizerExtension`. `DjangoType` and `finalize_django_types` are not referenced in the harness, the fixture, or either test body — `BookType` is imported from `apps.library.schema` INSIDE the per-test fixture (rev3 R4) and is already a finalized `DjangoType`, so the test module itself never declares a `DjangoType` subclass or calls `finalize_django_types()`.

When Worker 2 lands the file, ruff will flag `DjangoType` and `finalize_django_types` as F401 unused imports. The pinned shape gives Worker 2 conflicting signals: keep the spec-pinned imports (and add `# noqa: F401`, violating the Slice 2 checklist "no `# noqa` suppressions" rule) OR drop the unused imports (and diverge from the spec's pinned header).

Fix: trim the line-357 import to:

```python
from django_strawberry_framework import DjangoOptimizerExtension
```

And add a brief annotation under the pinned-shape block: "The test module imports only `DjangoOptimizerExtension` from the package because `BookType` (the `DjangoType` subclass under test) is imported inside the `_build_test_schema` per-test fixture after the autouse reload (rev3 R4), and `finalize_django_types()` is called by the reloaded `apps.library.schema` module — neither needs a top-level import here." That short note matches the rev4 V6 annotation style for `importlib` / `sys` and prevents Worker 2 from re-adding the unused imports.

### L2 — Slice 1 FK-id-elision tests do not pin the `FieldMeta` construction shape

`tests/types/test_resolvers.py` tests (a)-(d) all need to construct a `FieldMeta` instance to pass to `_build_fk_id_stub(root, field_meta)`. The Test plan section is silent on which `FieldMeta` constructor arguments are required vs optional — Worker 2 has to read `django_strawberry_framework/optimizer/field_meta.py` to know the dataclass shape and which fields have defaults.

This is not a correctness bug (Worker 2 can chase down the answer); it's an implementer-friction note. Two sentences in the spec's `### tests/types/test_resolvers.py` Test plan section would resolve it:

> Each test constructs a `FieldMeta` directly (not via `FieldMeta.from_django_field`) because the test goal is to spy on `_build_fk_id_stub`'s router-call shape, not to exercise the Django-field-introspection pipeline. The required arguments for the FK-id-elision path are `name`, `is_relation=True`, `related_model`, and `attname`; every other field on the `FieldMeta` dataclass has a default sufficient for this test surface.

Tracked here so the next maintainer reading the spec doesn't have to reverse-engineer it.

### L3 — Slice 1 optimizer-plan tests do not pin the synthetic `selected_fields` shape

`plan_optimizations(selected_fields, model, ...)` accepts a list of GraphQL selection-tree nodes. Worker 2 needs to construct a synthetic version of those nodes — and the walker reads at minimum `.name`, `.selections`, and probably `.alias` / `.directives` (via `_included_field_selections` + `_merge_aliased_selections` at `walker.py:174`). The Test plan section doesn't tell Worker 2 which shape to use; the spec's pseudocode (where present) doesn't pin it either.

The existing `tests/optimizer/test_plans.py` and `tests/optimizer/test_walker.py` modules already exercise `plan_optimizations` with synthetic selection nodes and have a working fixture pattern. The spec's `### tests/optimizer/test_multi_db.py` section should add one sentence pointing at the precedent:

> Worker 2 mirrors the synthetic-`SelectedField` fixture pattern from `tests/optimizer/test_walker.py` (the `SimpleNamespace`-based selection builders) so the new tests stay shape-compatible with `_walk_selections`' assumptions about `.name` / `.alias` / `.directives` / `.selections`. Inventing a new fixture shape risks subtle mismatches with `_included_field_selections` and `_merge_aliased_selections`.

Not a blocker; helps Worker 2 land Slice 1 in one pass instead of two.

---

## What looks solid

- The rev4 V1-V3 corrections fully address the H1/H2/H3 findings from the previous feedback round. `plan_optimizations` call shape is correct everywhere it's pinned in the prose, `kind="forward_single"` matches the `RelationKind` literal, and the test (e) setup pin correctly inhabits the single-valued lazy-load branch (`__dict__` + `_state.fields_cache`, no `_prefetched_objects_cache`).
- The rev4 V5 plan-cache + consumer-`Prefetch` interaction clarifier in Edge cases (line 485) is exactly the right shape: it pins the type-scoped binding via `Meta.optimizer_hints` and `resolver_key(parent_type, …)`, and explains why no per-resolver-call leak is possible. The wording matches the realization at `plans.py:140-149`.
- Decision 6's holder-pattern URLConf (rev3 R4) + per-test `_build_test_schema` fixture-after-autouse-reload pattern is internally consistent and matches how the existing `test_library_api.py` reload fixture works. Staging the harness scaffold confirmed every moving part has a place: module-level holder dict, closure-bound view, module-level `urlpatterns`, per-test fixture rebuilding the schema, `override_settings(ROOT_URLCONF=__name__)` per rev3 R5.
- The rev4 V6 annotation justifying the `importlib` / `sys` top-block imports in the Decision 6 pinned header lands cleanly — staging that header without the annotation would have looked like dead-code imports.
- `runtime_path_from_info(info)` at `plans.py:152-164` is None-safe along both branches: `info is None` returns `()` immediately, and `info.path is None` falls through `runtime_path_from_path(None)` which returns `()` because its `while path is not None` loop exits at first iteration. Test (e)'s synthetic `info = SimpleNamespace(context={...}, path=None)` works without further setup. (Initially flagged as a hazard; resolved on closer reading of `plans.py:152-180`.)
- The `tests/types/test_resolvers.py` autouse `_isolate_registry` fixture (lines 44-49) calls `registry.clear()` on entry and exit. Slice 1 tests (a)-(e) inherit this fixture but don't depend on registered `DjangoType` classes (the FK-id tests construct `FieldMeta` directly; the strictness test constructs a synthetic parent type). No conflict; the autouse pattern keeps Slice 1 tests order-independent.

---

## Notes for the rev5 spec author

The rev5 sweep checklist (extending the rev4 author's V8 catalog):

- **Mandatory grep**: `grep -n "test ([a-g])\|optimizer-plan test" docs/spec-019-multi_db-0_0_7.md` to enumerate every test-letter cross-reference. Every match must be checked against the Test plan letter mapping (see the H1 table). After H1/M1/M2 fixes land, the grep should return zero "optimizer-plan test (e)" results and the (f)/(g) references should align with the rev3 R2 numbering.
- **Pseudocode-time hazards** (L2/L3): adding the two pinned sentences to the Test plan section costs <20 words and saves Worker 2 a round-trip read of `field_meta.py` / `test_walker.py`.
- **L1 import-list trim**: the Decision 6 pinned shape is a load-bearing contract — Worker 2 will copy it verbatim. Trim it to what the test module actually uses.
- **No spec edits needed for the strictness test setup**: rev4 V3's "do NOT set `root._prefetched_objects_cache`" pin is correct and the synthetic `info.path = None` shape is None-safe per `plans.py:152-164`. The scaffold pseudocode confirmed both work.

H1 is a correctness blocker for the Worker 2 dispatch — Worker 0 should land the rev5 fix before spawning Slice 1's planning pass. M1/M2 are doc-edit-only and can ride in the same rev5 pass. L1-L3 are polish; safe to defer to Worker 1 planning notes if rev5 is held off.

End of feedback.
