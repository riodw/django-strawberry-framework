# Build: Slice 1 — G1 — evaluated-queryset guard (procedural closure)

Spec reference: `docs/spec-035-optimizer_hardening-0_0_10.md` (Slice-1 checklist lines 48-51; Decision 3 lines 164-183; Slice 1 test plan lines 340-347)
Status: final-accepted

> **Procedural-closure slice (single Worker 1 pass).** G1's runtime code **and** its four tests already shipped in commit `d1dea2fd` — before this spec was finalized (spec Revision 2 documents this). Slice 1 ships **nothing new** in this card; its only remaining work (the GLOSSARY note) belongs to Slice 4. Per `docs/builder/BUILD.md` "Procedural-closure slices", this slice closes via a single Worker 1 pass: one combined Plan + Final-verification block, `Status: final-accepted` set directly, **no Worker 2 build, no Worker 3 review**. Authorizing spec clauses: Decision 3 status line ("Status: shipped in commit `d1dea2fd` (code + tests; the GLOSSARY note remains in Slice 4)", spec line 166), Revision 2 (spec line 14), and the build plan's "G1 (Slice 1) already shipped — recorded, not built" context flag.

## Plan + Final verification (Worker 1, combined)

### What the spec contract for Slice 1 is

Slice 1 is the **shipped-contract record** for G1 — the evaluated-queryset guard. Per Decision 3 (spec lines 164-183), the contract is:

- In `optimizer/extension.py::DjangoOptimizerExtension._optimize`, after the `utils/querysets.py::normalize_query_source` coercion + its `is_queryset` gate and **before** the `apply_to` plan-build-and-apply tail, return the result unchanged when `getattr(result, "_result_cache", None) is not None`.
- Read defensively with `getattr` (the package posture).
- Placement is load-bearing in two directions: **after** the Manager coercion (a coerced `.all()` is always a fresh **unevaluated** queryset, so a `Model.objects`-returning resolver still optimizes) and **before** `diff_plan_for_queryset` / `plan.apply` (a `.only()` clone of an already-evaluated queryset would re-execute the SQL).
- Scope is the `_optimize` middleware path only; the connection field's `apply_to` tail is out of scope (framework-built, never consumer-evaluated). The async path (`_async_optimize` awaits then calls `_optimize`) inherits the guard unchanged.
- No port of upstream's `is_optimized()` flag, `CONFIG_KEY`, or the `QuerySet._clone` monkeypatch — redundant under the package's O3 root gate (`info.path.prev is None`).
- Package coverage (four tests in `tests/optimizer/test_extension.py`, the `# G1 (spec-035 Slice 1)` block): pass-through one-query, same-instance return, manager-coercion-still-optimizes, async mirror.

There is **no new work to plan** — the contract is already on disk. The remaining Plan responsibility for this procedural closure is to verify, against the live checkout, that the shipped commit satisfies the contract above, which the Final verification below does.

### DRY analysis

- **Existing patterns reused.** The shipped guard reuses the shared `utils/querysets.py::normalize_query_source` Manager-coercion + is-queryset contract (`extension.py::DjangoOptimizerExtension._optimize #"normalize_query_source(result)"`) rather than re-deciding queryset-ness inline, and reuses the package's defensive `getattr(..., default)` posture (cf. `optimizer/field_meta.py::_target_pk_name`). No duplication introduced.
- **New helpers justified.** None. G1 is a single early-return guard inside one method; a helper would be premature.
- **Duplication risk avoided.** None applicable — no code is being written in this pass. The guard correctly lives only in `_optimize` and is deliberately **not** duplicated into the shared `apply_to` tail (Decision 3 alternative-rejected: guarding the shared tail would add a per-connection `getattr` check that can never fire).

### Spec slice checklist (verbatim)

Copied verbatim from the spec's `## Slice checklist` Slice 1 sub-bullets (spec lines 48-51). Each is already shipped; each box is ticked `- [x]` only after verifying the contract truly landed in the live checkout (evidence below).

- [x] Slice 1: G1 — evaluated-queryset guard — **shipped in commit `d1dea2fd`** (per [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize))
  - [x] [`optimizer/extension.py::DjangoOptimizerExtension._optimize`][extension]: after the [`utils/querysets.py::normalize_query_source`][querysets] coercion + `is_queryset` gate (a `Manager` → `.all()` coercion always yields a fresh **unevaluated** queryset, so the guard sits AFTER it) and before the `apply_to` plan-build / `diff_plan_for_queryset` tail, returns the result unchanged when `getattr(result, "_result_cache", None) is not None`. Read defensively with `getattr` per the package posture ([`optimizer/field_meta.py::_target_pk_name`][field-meta]). **Live in [`extension.py::_optimize`][extension] — the `_result_cache`-present early-return.**
  - [x] No port of upstream's `is_optimized()` flag, `CONFIG_KEY` queryset config, or the `QuerySet._clone` monkeypatch (in [`strawberry_django`][upstream-optimizer]'s `queryset` module) — those exist upstream because its optimizer can run at nested resolvers; the package's O3 root gate (`info.path.prev is None`, [`spec-002`][spec-002]) already guarantees single application, so execution-state (`_result_cache`) is the only missing check ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)). Confirmed: the shipped guard ports the execution-state half only.
  - [x] Package coverage **shipped**: [`tests/optimizer/test_extension.py`][test-opt-extension] (the `# G1 (spec-035 Slice 1)` block) ships **four** tests — the pass-through (`test_optimizer_passes_through_consumer_evaluated_queryset` — a root resolver that evaluates the queryset via `len(qs)` then returns it executes exactly one SQL query total), the same-instance return (`test_optimize_returns_same_instance_for_evaluated_queryset` — not a re-executing clone), the manager-coercion path still optimizing (`test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard`), and the async mirror (`test_resolve_async_passes_through_evaluated_queryset`). *(Remaining G1 work: only the GLOSSARY note in Slice 4 — `d1dea2fd` touched code + tests, not docs.)*

### Final verification evidence (live checkout)

**Runtime guard — placement contract satisfied (Decision 3).** In `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`:

- `normalize_query_source` coercion + `is_queryset` gate land first (`extension.py::DjangoOptimizerExtension._optimize #"result, is_queryset = normalize_query_source(result)"` and `#"if not is_queryset:"`).
- The G1 early-return lands AFTER that gate and BEFORE the `apply_to` tail (`extension.py::DjangoOptimizerExtension._optimize #"if getattr(result, \"_result_cache\", None) is not None:"`, returning `result`). The docstring step 3 and the inline comment both cite "G1, `spec-035` Decision 3" and state the AFTER-coercion / BEFORE-clone placement reasoning verbatim.
- `_resolve_model_from_return_type` + `self.apply_to(...)` follow the guard (`extension.py::DjangoOptimizerExtension._optimize #"return self.apply_to(resolved.origin, resolved.model, result, info)"`), so the guard is strictly between the coercion gate and the plan-build tail.
- The signal is `is not None` (allocation-free, matching upstream) read via `getattr` (defensive), exactly as Decision 3 prescribes — `is_optimized` flag / `_clone` monkeypatch confirmed absent.

**Tests — four named tests present and green.** `tests/optimizer/test_extension.py` carries the `# G1 (spec-035 Slice 1)` block with all four spec-named tests:

- `test_extension.py::test_optimizer_passes_through_consumer_evaluated_queryset` — pins exactly one SQL query (`django_assert_num_queries(1)`) and `cache_info().misses == 0` (guard short-circuited before plan build).
- `test_extension.py::test_optimize_returns_same_instance_for_evaluated_queryset` — pins `ext._optimize(qs, SimpleNamespace()) is qs` (same instance, `info` never touched).
- `test_extension.py::test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard` — pins that a `Model.objects` resolver still builds a plan (`cache_info().misses == 1`) — the AFTER-coercion placement.
- `test_extension.py::test_resolve_async_passes_through_evaluated_queryset` — async mirror via `_async_optimize`; a `_resolve_model_from_return_type` tripwire proves the guard short-circuits before return-type resolution.

**Focused test run (optional confirmation, no `--cov`):**

- `uv run pytest tests/optimizer/test_extension.py -k "evaluated or _result_cache or manager_after" --no-cov` → **4 passed, 129 deselected**.

**DRY check across this slice and prior accepted slices.** Slice 1 is the first slice; no prior accepted slices. The guard introduces no duplication (single early-return, reuses `normalize_query_source` and the `getattr` posture).

**Spec status-line re-verification.** Spec header lines 1-9 already describe G1 as shipped in `d1dea2fd` and Slice 1 as recorded-not-built; Decision 3's status line (spec line 166) and Revision 2 (spec line 14) are accurate against the live checkout. No staleness — no edit needed.

**Spec reconciliation.** None required. The shipped code matches the Decision 3 contract line for line; spec Revision 2 already reconciled the G1-already-shipped reality. No contradiction found between the shipped code and the spec contract.

### Summary

Slice 1 records the shipped-contract closure for **G1, the evaluated-queryset guard**. The runtime guard — a `getattr(result, "_result_cache", None) is not None` early-return in `optimizer/extension.py::DjangoOptimizerExtension._optimize`, placed after the `normalize_query_source` Manager-coercion + `is_queryset` gate and before the `apply_to` plan-build tail — and its four package-internal tests (`test_optimizer_passes_through_consumer_evaluated_queryset`, `test_optimize_returns_same_instance_for_evaluated_queryset`, `test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard`, `test_resolve_async_passes_through_evaluated_queryset`) all shipped in commit `d1dea2fd` and are verified present, correctly placed, and green against the live checkout. The guard ports only upstream's execution-state half (no `is_optimized` flag / `_clone` monkeypatch — redundant under the O3 root gate). All three Slice-1 spec sub-checks are confirmed landed and ticked `- [x]`. No source/test/spec file was modified in this pass. G1's only remaining work is the GLOSSARY note, owned by Slice 4. Status set to `final-accepted`.

### Spec changes made (Worker 1 only)

None. The shipped code satisfies the Decision 3 contract exactly; spec Revision 2 already reconciled the G1-already-shipped reality, so no spec edit was warranted. All three Slice-1 spec sub-checks landed in `d1dea2fd` — none deferred.

<!-- LINK DEFINITIONS -->
<!-- Root -->
<!-- docs/ -->
[spec-002]: ../spec-002-optimizer-0_0_2.md
<!-- docs/SPECS/ -->
<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
[extension]: ../../django_strawberry_framework/optimizer/extension.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
<!-- tests/ -->
[test-opt-extension]: ../../tests/optimizer/test_extension.py
<!-- examples/ -->
<!-- scripts/ -->
<!-- .venv/ -->
<!-- External -->
[upstream-optimizer]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/optimizer.py
