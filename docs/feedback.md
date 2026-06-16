# Review — `docs/spec-035-optimizer_hardening-0_0_10.md`

Reviewer pass: 2026-06-16. Scope: rigorous correctness/feasibility review of the G1/G2/G3 spec, verified against the live checkout (`optimizer/extension.py`, `optimizer/walker.py`, `optimizer/selections.py`, `types/definition.py`, `types/base.py`, `tests/optimizer/test_extension.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`).

## Verdict

High-quality spec. The hardest technical claims hold up under verification: G1's guard placement matches Decision 3 line-for-line; G2's cache-safety (print-AST key separates `query`/`mutation`) is sound; and the most subtle G2 claim — that `_project_scalar_only_window` applies `.only()` *directly*, so a "clear `only_fields` before finalize" sweep would miss it and the gate must be threaded through all four writers — is **correct and verified**. The card-citation corrections (manager coercion now lives in `normalize_query_source`; fragment inlining now in `selections.py`) are themselves accurate.

Two findings are worth resolving before G2/G3 build: **Major-1** (a factual mischaracterization of `definition.interfaces` that, if trusted, would let an implementer introduce a Relay-interface bug) and **Strategic-1** (G3's failure modes are not reachable through any shipped feature today, and the "verified failure modes" framing overstates that). The rest are clarity/consistency fixes.

---

## Major-1 — `definition.interfaces` is the raw `Meta.interfaces`, **not** an "injected superset"

**Where:** Key-glossary bullet (`Meta.interfaces` line), Decision 6, the "collect interface names" alternative-rejected bullet, the Edge-cases "interface-typed planning" bullet, and Risks "interface-name collection source". The spec asserts (verbatim) that `definition.interfaces` *"already carries the injected Relay [Node] interface and is a superset of the raw `Meta.interfaces` tuple."*

**What the code shows:** `django_strawberry_framework/types/base.py::_validate_interfaces` reads `getattr(meta, "interfaces", None)`, validates/normalizes it, and the result is stored verbatim as `interfaces=validated.interfaces` on the definition. `DjangoTypeDefinition.interfaces` is therefore **exactly the normalized declared `Meta.interfaces` tuple** — not a superset, and it injects nothing. Relay-shapedness is computed *separately* by `_validate_interfaces`'s caller via `_is_relay_shaped(cls, interfaces)`, which is `any(issubclass(i, relay.Node) for i in interfaces) OR issubclass(cls, relay.Node)`. The `OR issubclass(cls, relay.Node)` arm is the tell: a type can be Relay-Node-shaped **by direct class inheritance**, in which case `relay.Node` is **absent** from `definition.interfaces` and present only in `origin.__mro__`. The definition's own docstring comment confirms `interfaces` is the finalizer's *input* "source of truth for base injection," not a post-injection product.

**Why it matters:** The G3 design happens to still work — but only because the spec *also* names `origin.__mro__` as a fallback, and the MRO is what actually catches the inheritance case. The danger is the stated rationale: an implementer who trusts "`definition.interfaces` is a superset that already carries the injected Node" could reasonably drop the MRO fallback as redundant, and would then **miss every interface reached by direct inheritance** — silently skipping a fragment conditioned on an interface the planning type genuinely implements (re-introducing failure mode (a), the silent N+1, for inherited interfaces). The spec currently presents the two sources as "primary + fallback" when they are in fact **complementary and neither alone is complete**: declared interfaces live in `definition.interfaces`; inherited interfaces live only in the MRO.

**Recommended fix:** Correct the characterization throughout — `definition.interfaces` is the normalized declared `Meta.interfaces`, not an injected superset. State the accept-set as the **union** of (a) `definition.interfaces` (declared) and (b) interface classes discovered by walking `origin.__mro__` for `@strawberry.interface` / `relay.Node` bases (inherited), mapped to their GraphQL names — and pin that both arms are required (the existing `test_interface_implementor_fragment_planned`, described as "by direct class inheritance," should assert the inheritance arm specifically, and a sibling test should cover the declared arm). This is a wording/rationale fix, not a redesign; the mechanism the spec lands on is correct once neither source is framed as subsuming the other.

---

## Strategic-1 — G3's failure modes are not reachable through any shipped feature; "verified failure modes" overstates

**Where:** Problem statement ("Two **verified** failure modes on interface / union queries"), Why-it-matters ("closes the only known silent-N+1 class left in the walker"), and the parity framing.

**What the code shows:** For the optimizer to encounter a `... on SiblingConcreteType` fragment, it must walk a queryset behind an **interface/union-typed** output position with ≥2 concrete `DjangoType` members. GraphQL validation forbids `... on SiblingType` under a *concretely*-typed position, so sibling fragments are only valid under an abstract position. Surveying the shipped surface:
- `DjangoConnectionField` / `DjangoListField` / root queryset fields are **concretely typed** (no siblings possible — the validator rejects them).
- The only interface-typed fields in the example schema are the root Relay refetch fields `node`/`nodes` (`apps/library/schema.py::Query.node` / `.nodes` via `DjangoNodeField()` / `DjangoNodesField()`), and per `docs/GLOSSARY.md` (Relay Node integration) *"Optimizer-extension cooperation on the per-node `resolve_node` resolver is deferred"* — they are **not** optimizer-planned.
- The package generates **no unions** (`grep` for `strawberry.union` / generated unions: none), and `polymorphic_interface_connections` is an unscheduled `BACKLOG.md` card.

So **no shipped, optimizer-planned, validated query path produces a sibling-concrete-type fragment.** The lone "live" Slice-3 test (`test_matching_type_fragment_under_connection_plans_relation`) exercises a *matching-type* fragment (`... on GenreType` under a `GenreType` connection) — the case that **already works** and needs no narrowing; it regression-guards the accept branch, it does not reproduce either bug. The spec itself concedes G3's "union / secondary-type / strictness internals have no fakeshop shape."

**Why it matters:** This isn't an argument that G3 is wrong — it correctly hardens a consumer-constructible path (a hand-rolled `@strawberry.interface` implemented by ≥2 `DjangoType`s, exposed as a queryset-returning field, *is* buildable today and the optimizer *would* mis-walk it), and it's prudent ahead of `polymorphic_interface_connections`. But two things should be honest:
1. **Wording.** "Two *verified* failure modes" means "verified that the guard is *absent*," not "verified to reproduce against a shipped feature." Soften to "verified-absent guard / latent failure modes," and state plainly that no shipped feature triggers them today — the trigger is a consumer-authored multi-implementor interface field, and the feature that would exercise G3 end-to-end (`polymorphic_interface_connections`) is unshipped.
2. **Sequencing question for the maintainer.** G2 has a concrete, dated arrival (the `0.0.11` mutations cohort makes mutation-root-querysets mainstream — the spec's sequencing argument there is strong and correct). G3 has no such trigger in `0.0.10`–`0.1.x`. Worth an explicit decision in the spec: ship G3 now as forward hardening (current plan), **or** fold it into the `polymorphic_interface_connections` card that would actually exercise it live and give it a non-synthetic reproduction. Either is defensible; the spec should make the choice consciously rather than carrying the "closes the only known silent-N+1 class" framing, which implies a reachable defect.

---

## Medium-1 — "an optional narrowing predicate" undersells a tri-state classifier + a recursion mode

**Where:** Slice-3 checklist ("gains an optional registry-only narrowing predicate") and Decision 6.

**What the code shows:** `selections.py::included_field_selections(selections)` is today a clean boolean recursion: for each selection, `should_include` then — if `is_fragment` — `result.extend(included_field_selections(selection.selections))` (inline the body unconditionally), else append the field. Decision 6 requires **three** outcomes per fragment, not two:
- **inline fully** (condition matches planning type),
- **skip whole subtree** (known sibling concrete type),
- **recurse into nested fragments but decline the fragment's own direct fields** (unknown composite / union).

The third outcome cannot be expressed by a boolean predicate that merely filters fragments. A union fragment `... on U { fieldA ...FragB fieldC }` must **drop** `fieldA`/`fieldC` (direct fields) while still re-classifying `FragB` (nested fragment). That requires the recursive call to carry a "fragments-only" mode that skips non-fragment selections — i.e., the change is a **tri-state classifier *plus* a recursion-mode flag**, not "a predicate."

**Why it matters:** Decision 6 describes the *behavior* precisely (its four bullets are correct and complete), but the *mechanism* phrase ("an optional narrowing predicate") will mislead the implementer into a boolean-filter shape that silently can't produce the recurse-without-direct-fields case — collapsing the unknown-composite branch into either skip-whole (under-plan a valid nested match) or inline-all (the over-plan G3 removes). The `test_unknown_union_condition_recurses_without_direct_fields` pin would catch it, but only after a wrong-shaped implementation.

**Recommended fix:** In Decision 6 / the Slice-3 checklist, specify the seam concretely: the classifier returns a 3-valued result (e.g. `INLINE` / `SKIP` / `RECURSE_FRAGMENTS_ONLY`), and `included_field_selections` gains both the classifier and a `fragments_only: bool` recursion parameter (or equivalent) so the `RECURSE_FRAGMENTS_ONLY` arm recurses with non-fragment direct fields dropped. Note the signature change must propagate through the existing self-recursion at the fragment-inline site, and that the walker is the only caller that passes a non-default classifier (the cache-key walk and `node_children_with_runtime_prefix` keep today's unconditional behavior — already stated, good).

---

## Minor-1 — G1 shipped-test count is internally inconsistent (says 2, actually 4)

The Slice checklist (Slice 1, package-coverage bullet) and **Revision 2** enumerate only two shipped G1 tests (`test_optimizer_passes_through_consumer_evaluated_queryset`, `test_optimize_returns_same_instance_for_evaluated_queryset`), and the implementation-plan table row says "New tests: **2**". But `tests/optimizer/test_extension.py` actually ships **four** under the `# G1 (spec-035 Slice 1)` block: the two above **plus** `test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard` and `test_resolve_async_passes_through_evaluated_queryset`. The Slice-1 test plan, the Edge-cases bullets ("pinned by `test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard`", "pinned by an async mirror test"), and DoD item 2 ("the manager-coercion path still optimizes, and the async mirror") all correctly reference the full four — so it's Revision 2 and the two checklist/table spots that under-count. Reconcile them to four (and the table's "New tests" / line-delta to match).

## Minor-2 — "still-pending `0.0.9` cut" contradicts "the `0.0.9` cut has landed"

The intro says the on-disk version reads `0.0.9` and "the `0.0.9` cut has landed," but Decision 9 and DoD item 11 say the `0.0.10` bump "lands only after the still-pending `0.0.9` cut is taken" / "after the pending `0.0.9` cut." On-disk `django_strawberry_framework/__init__.py::__version__ == "0.0.9"` confirms the `0.0.9` cut already happened. Drop the "still-pending `0.0.9` cut" phrasing (it's stale) — the only pending act is the joint `0.0.10` cut. Left as-is it muddies the version-boundary sequencing the spec is otherwise careful about.

## Minor-3 — symbol-name drift on the fragment primitives

The spec mixes the real public names (`included_field_selections`, `named_children`, `node_children_with_runtime_prefix` — verified in `selections.py`) with underscore-prefixed spellings (`_included_field_selections`, `_named_children`, `_node_children_with_runtime_prefix`) in body prose, Current-state, and Risks. The walker calls them via an underscore-aliased import, so both spellings resolve in different files, but per `AGENTS.md`'s symbol-qualified-reference rule the spec should consistently name the **definition** symbol (no underscore) so a `::OldName` grep stays stable. Pure hygiene; the link-definition block already uses the correct public names.

## Minor-4 — pin the `info`-present-but-`info.operation`-absent case for G2 (defensive derivation)

G2 derives `enable_only` from `info.operation.operation`. `extension.py::_build_cache_key` already reads `info.operation` directly, so during real execution `info.operation` is always present — the assumption is consistent with existing code. But the spec's own G1 rationale leans on the package's defensive-`getattr` posture, and the 100% gate means every arm of the new gate needs a hit. Recommend the spec state the derivation defensively (treat a missing `info` / `info.operation` as the `QUERY`/enabled default, not just `info is None`) so a partial test-double `info` can't `AttributeError`, and confirm the three arms (no-`info` → enabled, `QUERY` → enabled, non-`QUERY` → suppressed) are each covered.

---

## Verified accurate (checked against source, no action needed)

- **G1 placement** — `extension.py::_optimize` returns unchanged on `getattr(result, "_result_cache", None) is not None`, sited **after** `normalize_query_source(result)` + the `is_queryset` gate and **before** `_resolve_model_from_return_type` / `apply_to`. Matches Decision 3 exactly; the shipped docstring even cites "G1, `spec-035` Decision 3."
- **G2 cache-safety** — `_print_operation_with_reachable_fragments` is `print_ast(operation)` (+ reachable fragments). `print_ast` emits the `mutation`/`subscription` keyword unconditionally (only anonymous queries use keyword-less shorthand), so a query and a textually-identical mutation render to different document-key strings and never share a cached plan. Build-time gating is cache-correct as claimed.
- **G2 four-writer argument** — `_project_scalar_only_window` calls `child_queryset.only(*fields)` **directly**, never touching `OptimizationPlan.only_fields`; confirms a post-hoc `only_fields` sweep would miss it and the gate must be threaded through each writer. `_record_relation_access`/`_ensure_connector_only_fields` populate `only_fields` (connector columns) independently of scalar leaves — also as the spec describes. Suppressing all four under non-`QUERY` is safe because with no `.only()` every column loads (a superset of pk/connector/order), so windows/prefetches still function.
- **Gap claims** — `grep` confirms zero `OperationType` references (G2 gap real); `type_condition` appears in `selections.py`/`extension.py` only as the inline-fragment shell + `is_fragment` duck-type + runtime-prefix clone, never matched against a planning type (G3 gap real); `_result_cache` now present in `extension.py` (G1 shipped, commit `d1dea2fd`).
- **Seam existence** — `plan_optimizations(selected_fields, model, info=None, *, ..., source_type=None)` (info optional → default-enabled is implementable; `source_type` is the real mechanism by which a *secondary* type roots the walk, validating Decision 6's secondary-`... on PrimaryType` reasoning); `_walk_selections` resolves `type_cls`/`definition` via `_resolve_field_map` and has them in hand at the `_included_field_selections(...)` inline call and the unknown-name `continue` guard; `DjangoTypeDefinition.graphql_type_name` exists (`self.name or self.origin.__name__`).
- **Baseline tests cited by Decision 8 exist** — `test_typed_inline_fragment_under_connection_field_still_resolves` (`... on GenreType` under `edges { node }`) and the `test_anonymous_inline_fragment_*` family are present in `test_library_api.py`; `Query.all_library_genres_connection = DjangoConnectionField(GenreType)` and `GenreType` (Relay-Node) exist, so the matching-type live-test premise is sound.
- **Card-citation corrections** — both are right: the manager coercion is now `utils/querysets.py::normalize_query_source` (imported + called in `_optimize`), and fragment inlining now lives in `selections.py::included_field_selections`.
