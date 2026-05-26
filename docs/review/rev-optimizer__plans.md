# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## DRY analysis

- **Defer until a third Django-private contract centralizer lands.** `_lookup_path` (`plans.py:248-255`), `_consumer_prefetch_lookups` (`plans.py:258-266`), and `_consumer_only_fields` (`plans.py:269-297`) all share the "centralize one brittle Django-private contract here so a future rename has one fix" shape, with near-identical phrasing in their docstrings. Today three centralizers each guarding a single private attribute is the right grain (`prefetch_to`, `_prefetch_related_lookups`, `query.deferred_loading`); the call sites differ enough that a `_get_private_or_default(obj, attr, default, coerce=...)` helper would be more obfuscating than the present `getattr` literal. Defer until a fourth Django-private attribute joins the file (or until a Django version bump renames one of the three and we touch all of them at once) — at that point fold the shared docstring framing into a module-level "Django-private contract centralizers" docstring block instead of repeating it per function.
- **Defer until a second site flattens nested `Prefetch` lookups.** `_prefetch_lookup_paths` (`plans.py:479-496`) flattens `Prefetch` + plain-string entries to a set of dotted paths recursively; `lookup_paths` (`plans.py:472-476`) feeds it to expose the optimizer plan's coverage to B8/debug stashes. Today there is exactly one recursive flatten site; defer extracting a shared "walk one entry, yield each `(path, queryset)` pair" generator until a second site (e.g. a hint-validation helper that needed to enumerate hint-supplied `Prefetch` chains) lands. Trigger condition: "a second walker emerges that wants the per-entry tuples without the set collapse."
- **Defer until a fourth `Sequence/MutableSequence` plan-field mutator lands.** `append_unique` (`plans.py:215-223`), `append_unique_many` (`plans.py:226-229`), and `append_prefetch_unique` (`plans.py:232-245`) are the three dedupe mutators paired with `OptimizationPlan`'s list fields during walker construction. The trio is internally consistent — `append_unique_many` is `append_unique` in a loop, `append_prefetch_unique` swaps `value in values` for `_lookup_path`-keyed dedupe — and three is the canonical "rule of three" grain at which a shared abstraction would over-fit. Defer extracting a `_dedupe_append(values, value, *, key=...)` helper until a fourth dedupe mutator lands that needs a different `key`.

## High:

None.

## Medium:

None.

## Low:

### L1. `_db` preservation through `_diff_prefetch_related`'s queryset rewrite is unpinned by a test

`diff_plan_for_queryset` is one of two entry points the optimizer takes to apply a plan against a real queryset (the other is `OptimizationPlan.apply`). When the consumer's prefetch entries are absorbed (`_diff_prefetch_related` at `plans.py:458-467`), the function calls `queryset.prefetch_related(None)` then `new_queryset.prefetch_related(*keep)` — both `prefetch_related` calls on a `QuerySet` return a clone that preserves `_db` (Django's `_chain()` semantics), so `_db` survives in current Django. The behavior is required by `docs/GLOSSARY.md:692` axis 2 ("explicit `.using(alias)` `_db` preservation through `OptimizationPlan.apply` for root querysets") because the extension chains `diff_plan_for_queryset` then `plan.apply` at `optimizer/extension.py:618` and `:620-ish`. `tests/optimizer/test_multi_db.py:87-126` pins the consumer-hint axis 3, and `examples/fakeshop/test_query/test_multi_db.py` pins axis 2 transitively via a live `/graphql/` query — but neither test exercises the absorption-rewrite path with a `.using()`-aliased parent queryset (`Category.objects.using("shard_b").prefetch_related("items")` against an optimizer-`Prefetch("items", queryset=...)` plan entry). Today the rewrite preserves `_db` because Django's `QuerySet.prefetch_related` returns a clone via `_chain()`; if a future Django release changed `prefetch_related(None)` to construct a fresh queryset instead of cloning, the rewrite would silently drop `_db` and the absorption path would route the root query to `default`. Defer until either (a) the `BACKLOG.md` item 41 sharding-aware planning lands, OR (b) a Django version bump touches `QuerySet.prefetch_related`'s clone path — at that point add an `OptimizationPlan.diff` axis-2 test in `tests/optimizer/test_multi_db.py` along the same single-assertion shape as `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` (parent `qs = Category.objects.using("shard_b").prefetch_related("items")`, optimizer-plan `Prefetch("items", queryset=Item.objects.prefetch_related("entries"))`, assert `delta_qs._db == "shard_b"` after `diff_plan_for_queryset`).

```django_strawberry_framework/optimizer/plans.py:458-467
    new_queryset = queryset
    if paths_to_strip:
        keep = tuple(entry for entry in consumer_pf if _lookup_path(entry) not in paths_to_strip)
        # ``prefetch_related(None)`` clears the prefetch list on the
        # queryset; subsequent ``prefetch_related(*keep)`` rebuilds it
        # from the surviving consumer entries.  This is the documented
        # Django reset idiom for prefetch lookups.
        new_queryset = queryset.prefetch_related(None)
        if keep:
            new_queryset = new_queryset.prefetch_related(*keep)
```

### L2. `apply` order docstring under-explains why `only()` precedes `select_related`

`OptimizationPlan.apply` (`plans.py:122-137`) applies `only()` → `select_related()` → `prefetch_related()`. The docstring says "the order matters because `select_related` may narrow `only()` column lists and `prefetch_related` may carry nested `Prefetch` objects whose inner querysets already have their own `only()` applied." Read literally, the first half is backwards from the actual mechanic: Django's `QuerySet.select_related(*names)` does not narrow the existing `only()` set — it composes via `_chain()` and Django's compiler at evaluation time decides which columns to fetch given both the deferred-loading set and the select_related dict (the walker already includes FK attnames in `only_fields` per the module docstring `plans.py:11-13` so no narrowing is needed at the `apply` call site). The current order is still correct (`only()` first means `select_related`'s clone inherits the deferred-loading state with the FK columns the walker added; reversing it would still work in current Django but would semantically obscure the "the walker already arranged the column list to include select_related's required FKs"-invariant). Defer until either (a) a consumer files a "why does the optimizer call `only()` before `select_related`?" question, OR (b) the next major Django release touches `QuerySet.select_related`'s clone semantics — at that point rewrite the docstring to "`only()` first because the walker has already included FK columns required by `select_related` in `only_fields` (see module docstring); `prefetch_related` last because nested `Prefetch` objects carry their own pre-built inner querysets with `.only()` already applied."

```django_strawberry_framework/optimizer/plans.py:122-137
    def apply(self, queryset: Any) -> Any:
        """Apply the plan to a ``QuerySet`` and return the optimized copy.

        Applies in order: ``only()`` → ``select_related()`` →
        ``prefetch_related()``. The order matters because
        ``select_related`` may narrow ``only()`` column lists and
        ``prefetch_related`` may carry nested ``Prefetch`` objects whose
        inner querysets already have their own ``only()`` applied.
        """
```

### L3. `OptimizationPlan` is a mutable `@dataclass` with no `__hash__` despite the "Immutable-ish bag" docstring

`OptimizationPlan` (`plans.py:38-137`) is decorated with the bare `@dataclass` (mutable, no `eq=True, frozen=True`). The class docstring (`plans.py:40-52`) calls it an "Immutable-ish bag" and `finalize()` (`plans.py:97-120`) swaps mutable list fields for tuples so post-handoff `.append(...)` raises `AttributeError`. The intentional shape is: the dataclass itself stays assignable so the walker can mutate fields during construction, but after `finalize()` the *contents* are tuples so child-of-field mutation is blocked. The shape is correctly load-bearing (consumer code in `optimizer/extension.py:_compute_plan` builds the plan, then the walker mutates `select_related` / `prefetch_related` in place via `append_unique` / `append_prefetch_unique`, then `finalize()` publishes the immutable shape). A `frozen=True` dataclass would force `replace(plan, select_related=[...])` for every walker append, which is the wrong factoring. Defer until either (a) a third dataclass in the package gains the same "mutable-during-construction, immutable-after-handoff" shape and a shared `Finalizable[T]` protocol would beat the per-class `finalize()`, OR (b) a consumer files a bug where they reassigned a top-level field (`plan.select_related = [...]`) on a finalized plan post-handoff and silently broke the cache — at that point either freeze the dataclass via a separate frozen sibling class returned by `finalize()`, or document the "top-level reassignment is also undefined behaviour on a finalized plan" rule explicitly in the class docstring. The current shape is intentional and the docstring's "Immutable-ish" phrasing captures the mid-state correctly; this Low is forward-looking only.

### L4. `runtime_path_from_path` silently coerces `int`-keyed list indexes via `isinstance(key, int)`, masking `bool` subclass values

`runtime_path_from_path` (`plans.py:165-179`) walks a GraphQL `path` linked-list and skips integer keys via `if not isinstance(key, int) and key is not None`. Python's `bool` is a subclass of `int`, so a synthetic test double passing `True`/`False` as a `path.key` would be silently filtered as a list index (graphql-core only ever passes `str` for selection keys and `int` for list indices, so the current behavior is correct against the real GraphQL contract). The defensive shape is the right one — a future test double that accidentally passed `True` would be silently dropped rather than corrupting the runtime path. Defer until either (a) graphql-core changes its `path.key` contract to allow `bool` keys (unlikely), OR (b) a test author files a bug where their `SimpleNamespace(key=True)` test double caused a surprise dropped key — at that point tighten to `isinstance(key, int) and not isinstance(key, bool)` per the standard Python idiom. The current shape is correct against the documented graphql-core contract and the docstring at `plans.py:166-172` ("list indexes stripped") frames the integer-skip as the design intent; this Low is forward-looking only.

## What looks solid

### DRY recap

- **Existing patterns reused.** `OptimizationPlan` (`plans.py:38-137`) uses `dataclasses.field(default_factory=list)` to side-step the mutable-default footgun consistently across all five list fields (`plans.py:54, 57, 66, 68, 70`). `finalize()` (`plans.py:97-120`) uses `dataclasses.replace` to publish the tuple-backed plan rather than mutating in place, matching the docstring contract. `diff_plan_for_queryset` (`plans.py:330-410`) also routes through `dataclasses.replace(...).finalize()` (`plans.py:402-409`) so derived plans honor the "immutable-after-handoff" invariant. The three "centralize one brittle Django-private contract here" helpers (`_lookup_path` at `plans.py:248-255`, `_consumer_prefetch_lookups` at `plans.py:258-266`, `_consumer_only_fields` at `plans.py:269-297`) all use the same `getattr(obj, "private_attr", default)`-then-coerce shape and all carry a "Centralizes the brittle Django-private contract..." docstring opener so a future Django rename has a single greppable handhold per private attribute.
- **New helpers considered.** A consolidated `_dedupe_append(values, value, *, key=...)` helper covering `append_unique` / `append_unique_many` / `append_prefetch_unique` was considered and deferred (see DRY analysis bullet 3) — the three-site grain is the canonical "rule of three" sweet spot and a shared `key=` parameter would obscure rather than clarify the `value in values` vs `_lookup_path`-keyed dedupe split. A "Django-private contract centralizer" decorator (or a `_get_private(obj, attr, default, coerce=...)` helper) was considered for the three private-attribute readers and deferred (see DRY analysis bullet 1) — the three call sites differ enough in their coerce step (`coerce=list(... or ())`, `coerce=frozenset` with shape-tuple guard, `coerce=identity`) that a shared helper would push the divergent logic into per-call kwargs.
- **Duplication risk in the current file.** Two intentional "duplications" pass review: (a) the recursive `_walk` helper inside `_flatten_select_related` (`plans.py:204-209`) and the recursive `_prefetch_lookup_paths` (`plans.py:479-496`) both flatten nested-shape data structures to a set of dotted paths, but operate on incompatible inputs (Django's `select_related` dict vs `Prefetch | str` entries) — pulling them through a shared "tree-to-paths" abstraction would obscure the two distinct Django private contracts being centralized; (b) the `for opt_entry in plan_prefetch_related` loop body in `_diff_prefetch_related` (`plans.py:444-456`) reads `_lookup_path` and walks the `consumer_by_path` dict in a shape that superficially resembles the simpler `append_prefetch_unique` (`plans.py:232-245`) dedupe loop, but the ancestry-aware subtree-match logic is distinct from the lookup-path-set dedupe — the two reads of `_lookup_path` are intentional siblings, not factoring drift.

### Other positives

- **Cache-invariant honesty.** The class docstring (`plans.py:40-52`) calls out the "immutable-after-handoff" cache invariant explicitly, naming the two situations that publish a plan (walker return, extension cache stash) and the only mutation API that's safe (`dataclasses.replace`). `finalize()`'s docstring (`plans.py:97-120`) repeats the rationale and calls out the `AttributeError` that catches in-place `append` attempts on a finalized tuple field — and `tests/optimizer/test_plans.py:155-163` pins the `pytest.raises(AttributeError)` shape.
- **Consumer-wins reconciliation.** `diff_plan_for_queryset` (`plans.py:330-410`) and its helpers `_diff_select_related` / `_diff_prefetch_related` honor the "consumer wins on collision" rule explicitly: `_optimizer_can_absorb` (`plans.py:300-327`) only returns `True` when all three lossless-absorption conditions hold (optimizer entry is a `Prefetch` with a queryset, every consumer entry is a bare string, every consumer descendant is covered by the optimizer's own subtree), and the "else: consumer wins on this subtree; optimizer dropped." comment at `plans.py:456` makes the dropped-optimizer branch self-documenting. The four-bullet reconciliation-rules docstring at `plans.py:330-389` carries the canonical contract.
- **`only_fields` drop is permission-boundary-aware.** `diff_plan_for_queryset`'s `only_fields` reconciliation (`plans.py:392-393` and `plans.py:407`) drops the optimizer's `only_fields` entirely when the consumer applied `.only(...)` — the docstring at `plans.py:355-362` calls out the specific failure mode ("applying the optimizer's `only_fields` on top of a consumer `.only()` would silently drop the consumer's projection — including columns the consumer may have restricted to enforce a permission boundary") and explains why `.defer(...)` is not treated as a consumer projection. `tests/optimizer/test_plans.py:449-501` pins all five branches (drop on `only()`, keep when no projection, keep under `defer()`, drop under chained `only().only()`, original-plan-untouched).
- **Defensive `getattr` discipline.** Every Django-private attribute read (`plans.py:255, 266, 285, 286, 322, 424` and `:425, :487, :492`) goes through `getattr(obj, attr, default)` so a non-`QuerySet` test double or a future Django version that drops one of these attributes degrades to the documented default (empty set for `select_related`, empty list for `_prefetch_related_lookups`, `None` for `deferred_loading`, `False` for absorption-check) instead of crashing. The pattern is consistent enough that the docstring at `plans.py:420-423` calls it out by name ("Defensive: a queryset-shaped object without `.query` is treated as having no existing select_related, matching the rest of the file's defensive `getattr` style").
- **Test coverage matches the file's branches.** `tests/optimizer/test_plans.py` has dedicated `Test*` classes for every public surface (`TestOptimizationPlanIsEmpty`, `TestLookupPaths`, `TestOptimizationPlanApply`, `TestOptimizationPlanFinalize`, `TestPlanHelperRelocations`, `TestFlattenSelectRelated`, `TestConsumerOnlyFields`, `TestDiffPlanForQueryset`) plus 16 test methods under `TestDiffPlanForQueryset` covering absorption, wildcard-`select_related`-no-overlap, partial overlap, consumer-`Prefetch`-with-queryset, optimizer-can-absorb-only-when-covered, `only_fields`-permission-boundary-drop, and the original-plan-untouched cache invariant. Worker 1 has nothing to add here.

### Summary

`plans.py` is the canonical data-shape module for the optimizer subsystem: `OptimizationPlan` (a mutable-during-construction, immutable-after-handoff dataclass), `resolver_key` / `runtime_path_from_info` / `runtime_path_from_path` (shared with `types/resolvers.py` for branch-sensitive resolver-key construction), and the `diff_plan_for_queryset` reconciliation layer that lets the optimizer cooperate with consumer-applied `select_related` / `prefetch_related` / `only()` without colliding. No High/Medium findings. Four trigger-gated Lows: (L1) `_db` preservation through `_diff_prefetch_related`'s absorption-rewrite is correct against current Django but unpinned by an axis-2 test — defer until sharding-aware planning or a Django `QuerySet.prefetch_related` clone-semantics bump; (L2) `apply`'s order docstring frames the `only()`→`select_related` ordering as "select_related narrows only" which is mechanically backwards, but the ordering is correct because the walker pre-includes FK columns — defer until a consumer asks; (L3) `OptimizationPlan` is intentionally a bare `@dataclass` (not `frozen=True`) so the walker's mutate-then-finalize pattern works, and the "Immutable-ish" docstring captures the mid-state honestly — defer until a third Finalizable-shape dataclass joins the package or a consumer reassigns a top-level field post-handoff; (L4) `runtime_path_from_path`'s `isinstance(key, int)` filter is correct against graphql-core's documented contract but masks `bool` subclass values — defer until graphql-core changes its `path.key` contract. Three DRY-analysis bullets are all defer-with-trigger (private-contract-centralizer helper at 4th site; recursive `_prefetch_lookup_paths` flatten at 2nd site; `_dedupe_append(values, value, *, key=...)` at 4th mutator).

---

## Fix report (Worker 2)

### Files touched
- None — this cycle is a consolidated no-op pass. 0H/0M findings; L1–L4 are all explicitly forward-looking trigger-gated per Worker 1's own prose (each cites "Defer until …" with concrete trigger conditions). The three DRY-analysis bullets are likewise defer-with-trigger and require no in-cycle edit.

### Tests added or updated
- None.

### Validation run
- `uv run ruff format .` — pass / no-changes (`118 files left unchanged`).
- `uv run ruff check --fix .` — pass / no-changes (`All checks passed!`).
- No focused pytest run (per `START.md`: formatting only on no-source-edit cycles; the standing fail-under=100 gate already pins the file via `tests/optimizer/test_plans.py`'s dedicated `Test*` classes per Worker 1's "What looks solid" recap).

### Notes for Worker 3
- Shadow file used: none (no source-edit required; Worker 1's overview at `docs/shadow/plans.overview.md` was the basis for re-confirming the no-op disposition).
- Intentionally-rejected findings with contradicting evidence: none. All four Lows accepted as forward-looking-only per Worker 1's verbatim "Defer until …" framing.
- Deferred findings and their trigger conditions (verbatim from Worker 1, for greppable carry-forward):
  - **L1**: "Defer until either (a) the `BACKLOG.md` item 41 sharding-aware planning lands, OR (b) a Django version bump touches `QuerySet.prefetch_related`'s clone path".
  - **L2**: "Defer until either (a) a consumer files a 'why does the optimizer call `only()` before `select_related`?' question, OR (b) the next major Django release touches `QuerySet.select_related`'s clone semantics".
  - **L3**: "Defer until either (a) a third dataclass in the package gains the same 'mutable-during-construction, immutable-after-handoff' shape and a shared `Finalizable[T]` protocol would beat the per-class `finalize()`, OR (b) a consumer files a bug where they reassigned a top-level field (`plan.select_related = [...]`) on a finalized plan post-handoff".
  - **L4**: "Defer until either (a) graphql-core changes its `path.key` contract to allow `bool` keys (unlikely), OR (b) a test author files a bug where their `SimpleNamespace(key=True)` test double caused a surprise dropped key".
  - **DRY-1**: "Defer until a fourth Django-private attribute joins the file (or until a Django version bump renames one of the three and we touch all of them at once)".
  - **DRY-2**: "Defer until a second site flattens nested `Prefetch` lookups" — trigger: "a second walker emerges that wants the per-entry tuples without the set collapse."
  - **DRY-3**: "Defer extracting a `_dedupe_append(values, value, *, key=...)` helper until a fourth dedupe mutator lands that needs a different `key`."
- Consolidated-single-spawn justification: artifact qualifies under the "all Lows are explicitly forward-looking per Worker 1's own prose" branch of `worker-2.md`'s consolidated-spawn criteria — no in-cycle edit, no logic / docstring change, both ruff runs no-changes.

---

## Comment/docstring pass

### Files touched
- None.

### Per-finding dispositions
- **Low 1** (`_db` preservation absorption-rewrite axis-2 gap): no docstring edit. Worker 1's framing is "Defer until either (a) the `BACKLOG.md` item 41 sharding-aware planning lands, OR (b) a Django version bump touches `QuerySet.prefetch_related`'s clone path"; both triggers are external to this cycle, and the docstring at `plans.py:330-389` already covers the four-bullet reconciliation contract that L1 sits inside. The axis-2 test is the artifact's recommended fix surface, not a docstring change.
- **Low 2** (`apply` order docstring under-explains why `only()` precedes `select_related`): no docstring edit. Worker 1 explicitly defers the docstring rewrite to "either (a) a consumer files a 'why does the optimizer call `only()` before `select_related`?' question, OR (b) the next major Django release touches `QuerySet.select_related`'s clone semantics" — both triggers are external. The current docstring is mechanically imprecise but functionally correct; rewriting it absent a trigger would invent the precise post-trigger wording prematurely.
- **Low 3** (`OptimizationPlan` is mutable `@dataclass` with "Immutable-ish" docstring): no docstring edit. Worker 1's own assessment is "The current shape is intentional and the docstring's 'Immutable-ish' phrasing captures the mid-state correctly; this Low is forward-looking only." That is a zero-edit disposition by Worker 1's own prose.
- **Low 4** (`runtime_path_from_path`'s `isinstance(key, int)` masks `bool`): no docstring edit. Worker 1's own assessment is "The current shape is correct against the documented graphql-core contract and the docstring at `plans.py:166-172` ('list indexes stripped') frames the integer-skip as the design intent; this Low is forward-looking only." Zero-edit disposition.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

### Notes for Worker 3
- Every Low's deferral is anchored in Worker 1's verbatim prose; the trigger-condition citations in `## Fix report (Worker 2) > Notes for Worker 3` are grep-discoverable against this artifact.
- No comment pass edit was warranted because the consolidated-spawn precondition holds: zero logic-pass edits ⇒ no post-edit docstring contract to re-describe (per the cycle-14 `rev-optimizer__hints.md` precedent in `worker-memory/worker-2.md`).

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Two-citation bar per `worker-2.md` "Not warranted" dicta:
1. `AGENTS.md` line 21: "Do not update CHANGELOG.md unless explicitly instructed."
2. The active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle (the plan's per-cycle entries name the artifact and the cycle ordinal, not a changelog-edit authorization).

Strengthened by the 0.0.7 precedent chain: this is the fifteenth consecutive 0.0.7 cycle to close `Not warranted` (cycles 1–14 covered `_django_patches`, `apps`, `conf`, `exceptions`, `list_field`, `registry`, `scalars`, `management__commands__export_schema`, `management__commands`, `management`, `optimizer___context`, `optimizer__extension`, `optimizer__field_meta`, `optimizer__hints` — all `Not warranted`). Additionally, no source / test / docstring edit was made this cycle (consolidated no-op), so there is by construction no consumer-visible behaviour change that could warrant a release-note entry.

### What was done
No `CHANGELOG.md` edit.

#### Suggested CHANGELOG entry (safety net, per the cycles 2–12 carry-forward pattern)
None — no source / test / docstring edit was made this cycle, so there is no behaviour, no contract, and no maintainer-paste-ready text to derive. If a future cycle reverses this disposition (e.g. the cycle-1 maintainer reversal precedent), the four trigger-gated Lows above each cite their precise trigger condition and their recommended in-source change inline, so a future maintainer can lift the wording from those artifact bullets directly without re-derivation.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

---

## Verification (Worker 3)

### Logic verification outcome
Empty source diff for `django_strawberry_framework/optimizer/plans.py` confirmed via `git diff --stat HEAD -- django_strawberry_framework/optimizer/plans.py`. Zero High, zero Medium. L1–L4 are all forward-looking-only per Worker 1's verbatim "Defer until …" framing; Worker 2's `### Notes for Worker 3` carries the verbatim trigger phrasing for each Low and each of the three DRY-analysis bullets — both arms preserved for all multi-arm disjunctive triggers (L1 BACKLOG-item-41 OR Django-prefetch_related-clone-path; L2 consumer-question OR Django-select_related-clone-semantics; L3 third-Finalizable-dataclass OR consumer-top-level-reassignment-bug; L4 graphql-core-bool-key OR test-double-bool-key-bug; DRY-1 fourth-private-attribute OR Django-rename). No intentionally-rejected findings.

### DRY findings disposition
Three DRY-analysis bullets are all defer-with-trigger and require no in-cycle edit per Worker 1's prose. Worker 2's `### Notes for Worker 3` carries verbatim trigger phrasing for DRY-1/DRY-2/DRY-3 (DRY-2 trigger condition "a second walker emerges that wants the per-entry tuples without the set collapse" preserved; DRY-3 fourth-dedupe-mutator trigger preserved).

### Temp test verification
- None used (consolidated no-op).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks `docs/review/review-0_0_7.md:110`.

### Changelog disposition verification
`git diff -- CHANGELOG.md` empty; matches `Not warranted` framing. Two-citation bar cleared (AGENTS.md line 21 + active-plan silence) and strengthened by the fifteen-cycle 0.0.7 precedent chain. No source / test / docstring edit this cycle, so no consumer-visible behaviour delta could warrant an entry.

### Validation
- `uv run ruff format .` — 118 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

---

## Iteration log

(No re-passes — consolidated single-spawn closed the cycle in one shot.)
