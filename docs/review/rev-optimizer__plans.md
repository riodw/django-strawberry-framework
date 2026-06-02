# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## DRY analysis

- **Defer-with-trigger.** Extract a shared `_extract_lookup_paths(entries)` helper that subsumes `lookup_paths` (`plans.py:467-471`) and the recursive `_prefetch_lookup_paths` (`plans.py:474-491`) into one entry point taking `select_related` + `prefetch_related` together. Defer until a third call site needs the same union (e.g., the deferred B8 introspection surface or a future strictness reporter). Today the two helpers are correctly factored (`lookup_paths` for the public B8/debugging surface union; `_prefetch_lookup_paths` for the recursive prefetch-only walk consumed by `_optimizer_can_absorb` at `plans.py:322`).
- **Defer-with-trigger.** Collapse the three brittle-Django-private accessors (`_lookup_path` at `plans.py:244-251`, `_consumer_prefetch_lookups` at `plans.py:254-262`, `_consumer_only_fields` at `plans.py:265-293`) into a dedicated `_django_private_accessors` namespace OR a small `consumer_query` dataclass once a fourth Django-private attribute joins them. Today all three live next to each other with consistent "Centralizes the brittle Django-private contract for ..." docstrings — premature factoring would obscure the per-attribute defensive rationale.
- **Defer-with-trigger.** Extract a shared `_consumer_owns_field(queryset, *, kind)` predicate that subsumes `_consumer_only_fields(queryset) is not None` (`plans.py:385`) and the parallel `_flatten_select_related(getattr(query, "select_related", False))` shape (`plans.py:418`) into one "did the consumer already do this work?" entry point. Defer until a third reconciliation axis lands (a likely candidate is `query.annotations` / `Subquery` cooperation for aggregate planning — see [`BACKLOG.md`][backlog] item 41 / aggregates spec). The two current axes are correctly per-attribute today because the return shapes are genuinely different (frozenset of fields vs. list of remaining names).

## High:

None.

## Medium:

### GLOSSARY drift on `Queryset diffing`: consumer-`.only()` drop rule is undocumented

`docs/GLOSSARY.md:840-853`'s `Queryset diffing` entry enumerates four cooperation rules — Queryset cooperation, Prefetch cooperation, Subtree-aware reconciliation, Plain-string absorption — but omits the consumer-`.only()`-wins drop rule that ships at `plans.py:344-355` + `plans.py:385-386` (the `drop_only_fields = bool(plan.only_fields) and _consumer_only_fields(queryset) is not None` branch and the verbatim consumer-permission-boundary rationale the docstring carries). The drop is a real consumer-visible behaviour-shape contract — a column-restricted consumer `.only(...)` survives optimizer planning instead of being silently overwritten by Django's `.only().only()` replacement semantics. The 0.0.7 CHANGELOG (`CHANGELOG.md:68`) records `_consumer_only_fields` gaining direct unit coverage, but the consumer-facing contract surface (the GLOSSARY entry) does not name the drop rule.

Same calibration as `rev-optimizer__extension.md`'s `DjangoOptimizerExtension` / `Plan cache` / `Schema audit` Medium and `rev-management__commands__export_schema.md`'s `Schema export management command` Medium — a published GLOSSARY entry that lags shipped behaviour the consumer can key against is Medium not Low because the entry IS the consumer contract surface, not internal mechanics.

Preserve verbatim replacement prose for Worker 2 to lift directly into the `Queryset diffing` entry's bulleted cooperation rules (append after the existing "Plain-string absorption" bullet):

> - **`only()` cooperation.** If your resolver already calls `.only(...)` to enforce a column-level projection (e.g., a permission boundary that restricts which columns leave the database), the optimizer drops its own `only_fields` rather than chaining a second `.only(...)` that would replace yours — Django's `QuerySet.only(...).only(...)` replaces (not merges) the deferred-field set. `.defer(...)` is not treated as a consumer projection because `.defer()` and `.only()` compose cleanly in Django.

```django_strawberry_framework/optimizer/plans.py:343:355
``only_fields`` — dropped entirely when the consumer already
applied ``.only(...)`` to the queryset (detected via
``query.deferred_loading`` with ``defer_flag is False`` and a
non-empty field set). Django's ``QuerySet.only(...).only(...)``
chaining *replaces* the previous deferred-field set rather than
merging, so applying the optimizer's ``only_fields`` on top of a
consumer ``.only()`` would silently drop the consumer's projection
— including columns the consumer may have restricted to enforce a
permission boundary. The conservative consumer-wins choice is to
drop the optimizer's ``only_fields`` whenever the consumer has
already restricted columns; ``.defer(...)`` is not treated as a
consumer projection because ``.defer()`` and ``.only()`` compose
cleanly in Django.
```

## Low:

### Cache invariant on `cacheable` is documented but not enforced post-`finalize()`

`plans.py:45-52`'s `OptimizationPlan` docstring frames the cache invariant uniformly ("once a plan has been handed off ... it must not be mutated in place. Use `dataclasses.replace` to derive a modified plan."), and `finalize()` (`plans.py:97-120`) swaps list fields to tuples so post-handoff `plan.prefetch_related.append(...)` raises `AttributeError`. But `cacheable` is a plain `bool` attribute (not a sequence) and remains settable after finalisation — `walker.py:342` and `walker.py:442` already mutate `plan.cacheable = False` on the *pre-finalize* plan, which is intentional, but the post-finalize cache invariant is enforced ONLY on the list fields. A regression that flips `cached_plan.cacheable = False` post-handoff would silently poison subsequent cache reads for that key (the cache returns the same finalized object across requests; the next read sees the mutated flag).

Two reasonable shapes for the fix:

- Tighten the docstring at `plans.py:45-52` to call out that finalisation enforces immutability on the *list* fields specifically and the `cacheable` flag still relies on convention. Cite `walker.py::plan_optimizations` as the only writer.
- Or move to `@dataclass(frozen=True)` on `OptimizationPlan` (Worker 2 cost: walker-side construction switches from in-place mutation to `replace(plan, ...)` at every helper call). This is real surface tightening, not cosmetic. Defer the frozen-dataclass option until a second cacheable-flag-flip writer lands or a real cache-poisoning incident surfaces; today the docstring tightening alone is the right shape.

Low severity because no current writer mutates `cacheable` post-finalize and tests don't pin the invariant for the bool field.

### `is_empty` exclusion of `cacheable` is correct but the docstring under-promises

`plans.py:82-95`'s `is_empty` docstring says "`cacheable` is metadata about cache reuse and is excluded from the emptiness check" — accurate, but it doesn't name the consequence: an `OptimizationPlan(cacheable=False)` with no other directives reports `is_empty=True` (test pin: `test_cacheable_flag_does_not_affect_empty_state` at `tests/optimizer/test_plans.py:51-53`). Resolvers that key off `is_empty` for a "skip optimizer" early-out won't know the plan also carries an uncacheable-flag signal. Defer-with-trigger: address when a resolver-side callsite reads `is_empty` AND `cacheable` together for a logic decision. Today only `apply()` is empty-tolerant and the extension's `plan_relation` / `_optimize` paths don't branch on `is_empty`.

### `_consumer_prefetch_lookups`'s `or ()` defensive coda is dead code under stock Django

`plans.py:262` reads `list(getattr(queryset, "_prefetch_related_lookups", ()) or ())`. The `or ()` handles a falsy value other than the missing-attribute branch (e.g., the attribute is present but `None`). Stock Django's `QuerySet._prefetch_related_lookups` is always a tuple — `prefetch_related(None)` resets to `()`, not `None`. The `or ()` survives as a paranoid guard for non-`QuerySet` inputs whose `_prefetch_related_lookups` attribute exists but is `None` (e.g., a test double or a non-`QuerySet` manager). Same severity calibration as the per-Django-version defensive guards in `_consumer_only_fields`; defer-with-trigger until a real consumer surfaces a `None` lookups attribute. Worth a one-line comment naming the non-`QuerySet` test-double case so the next reviewer doesn't propose dropping it.

### Audit-trail anchors (`P1`/`P2`/`M1`) survive without a docs target

`plans.py:418` (`P2:` via comment in `_diff_select_related` is at `tests/optimizer/test_plans.py:218` + `:311`, not the source), `plans.py:445-451` (`# else: consumer wins on this subtree; optimizer dropped.`), and the source/test comment pairs `P1 case 1`, `P1 case 2`, `P1 follow-up`, `P2`, `M1` (`tests/optimizer/test_plans.py:218`, `:311`, `:356`, `:372`, `:387`, `:429`, `:458`) are paired audit-trail anchors between source and tests but resolve to no live spec heading — `grep -rn "^### P1\|^### P2\|^### M1" docs/SPECS/` returns nothing matching the prefetch-reconciliation rules these anchors tag. Same calibration as the `rev-registry.md` rev-anchor citation hygiene Low: an internal anchor that is paired between source and tests but lacks a docs target is audit-trail not link-rot, because the anchors function as inter-file labels for the reviewer. Defer-with-trigger: when a Q-series or P-series spec is authored for the queryset-diffing subsystem (e.g., a "Queryset cooperation contract" spec authored for `0.0.9+`), promote the anchors into a heading there OR drop them from the source comments entirely; today the anchors are correct audit-trail and Worker 2 should NOT propose a rename or removal without that spec landing.

## What looks solid

### DRY recap

- **Existing patterns reused.** `OptimizationPlan`'s mutable-to-tuple `finalize()` shape mirrors registry's snapshot pattern (`registry.py::clear` and `register_with_definition` rollback per `rev-registry.md`'s carry-forward note about intentional divergence — same calibration applies here for the walker-side mutation vs. handoff-side immutability split). `_lookup_path` (`plans.py:244-251`) centralizes the `prefetch_to` accessor in one site so the four call sites (`plans.py:239`, `:432`, `:438`, `:455`) share one Django-private contract — same shape as `_context.py::DST_OPTIMIZER_*` key consolidation per `rev-optimizer___context.md`'s "single home for X dispatch" calibration.
- **New helpers considered.** Considered extracting `_drop_only_fields(plan, queryset)` to mirror `_diff_select_related` / `_diff_prefetch_related` — rejected because the only-fields reconciliation is a one-line boolean (`plans.py:385-386`), shorter than the helper signature it would carry, and the parallel structure would obscure that the only-fields rule is genuinely simpler than the per-entry prefetch walk. Same calibration as the `hints.py` "already at the consolidation point" Low recorded in `rev-optimizer__hints.md`.
- **Duplication risk in the current file.** `_flatten_select_related._walk` at `plans.py:200-205` and `_prefetch_lookup_paths` at `plans.py:474-491` are both recursive lookup-path flatteners over Django relation trees, but the input shapes (dict-of-dicts for select_related vs. iterable-of-(str|Prefetch) for prefetch_related) and output shapes (dotted strings via `__`) are deliberately separated. Folding through a shared `_flatten_relation_tree` would force a discriminated-union input type and obscure the per-walker structural rationale (select_related's `True`/`False`/`dict` ternary vs. prefetch_related's iterable-of-objects).

### Other positives

- `OptimizationPlan` carries per-field docstrings (`plans.py:55`, `:58-64`, `:67`, `:69`, `:71`, `:73-80`) — every field has a one-line or paragraph explanation including the `O6` spec anchor on `cacheable`, the `B3` spec anchor on `planned_resolver_keys`, and the verbatim Django API surface (`QuerySet.select_related` / `.prefetch_related` / `.only`) the field maps to. Field-level dataclass docstrings are not auto-rendered by stock Python but survive in source and are picked up by AST-based doc tooling.
- `finalize()` is idempotent and uses `dataclasses.replace` rather than in-place mutation, so even the construction-time path produces a new instance — the test `test_finalize_is_idempotent` at `tests/optimizer/test_plans.py:166-170` and `test_finalize_preserves_values_and_cacheable_flag` at `:150-154` pin both contracts. The walker's `plan_optimizations` return at `walker.py:58` (`return plan.finalize()`) and `diff_plan_for_queryset`'s `replace(plan, ...).finalize()` at `plans.py:395-401` both rely on this idempotency.
- `_optimizer_can_absorb` (`plans.py:296-323`) carries a three-rule contract docstring that names the failure mode being prevented ("optimizer `Prefetch("items", queryset=Item.objects.only("name"))` cannot absorb consumer `"items__entries"`") and the silently-drop-data risk it averts. Same shape-of-contract clarity as `rev-optimizer__extension.md`'s `check_schema` audit.
- `_diff_prefetch_related` at `plans.py:422-464` carries a load-bearing comment block at `:456-459` explaining the `prefetch_related(None)` reset idiom — the exact "Django reset idiom for prefetch lookups" reference that protects future readers from "why are we passing None?" confusion.
- Defensive private-attribute access: every Django-private contract (`_prefetch_related_lookups`, `query.deferred_loading`, `query.select_related`, `Prefetch.prefetch_to`, `Prefetch.queryset`) is reached via `getattr(..., default)` with a documented brittle-contract rationale. The `_consumer_only_fields` `try/except (TypeError, ValueError)` defensive shape at `plans.py:285-288` survives a future Django that changes the 2-tuple shape.
- Test surface: `tests/optimizer/test_plans.py` carries 30+ tests across 7 test classes (`TestOptimizationPlanIsEmpty`, `TestLookupPaths`, `TestOptimizationPlanApply`, `TestOptimizationPlanFinalize`, `TestPlanHelperRelocations`, `TestFlattenSelectRelated`, `TestConsumerOnlyFields`, `TestDiffPlanForQueryset`) covering every public surface and every defensive branch. The `TestConsumerOnlyFields` class explicitly pins the three defensive branches the 0.0.7 release added direct coverage for.
- GLOSSARY alignment: `OptimizationPlan` is correctly absent as a dedicated entry per `optimizer/__init__.py:14-17`'s explicit "internal implementation details consumed by `extension.py` and tests, not consumer-facing API" framing. The only cross-reference (`docs/GLOSSARY.md:742` in `Multi-database cooperation`) is current — `.using(alias)` `_db` preservation through `OptimizationPlan.apply` for root querysets is the shipped 0.0.7 behaviour and the entry was authored at version-bump time.
- Spec anchor citations: `B1` (cache integrity, `plans.py:330`), `B3` (strictness mode, `plans.py:71`), `B8` (queryset diffing, `plans.py:468`), `O6` (Prefetch downgrade for `get_queryset`, `plans.py:75`) all resolve to live spec headings under `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` and `docs/SPECS/spec-002-optimizer-0_0_2.md` and `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — they are file-path-agnostic rev-anchors that survive the docs/SPECS/NEXT.md Step 8 archive sweep. Same shape as the citation-hygiene calibration recorded in `rev-registry.md`.
- Static helper output cross-check: `docs/shadow/django_strawberry_framework__optimizer__plans.overview.md` reports 2 control-flow hotspots (`diff_plan_for_queryset` 78 lines / 4 branches; `_diff_prefetch_related` 43 lines / 6 branches) both UNDER the 8-branch Medium-tier threshold. The `getattr` density (12 calls) is correct shape — every call resolves a documented Django-private attribute with a known-brittle contract.

### Summary

`optimizer/plans.py` is a well-shaped 491-line plan-and-reconciliation module: `OptimizationPlan` carries per-field docstrings and an idempotent `finalize()` that enforces tuple-immutability on list fields; `diff_plan_for_queryset` and its two private helpers (`_diff_select_related`, `_diff_prefetch_related`) reconcile plan vs. queryset across four cooperation axes (select_related overlap, prefetch_related subtree absorption, consumer-`.only()` drop, plain-string-vs-Prefetch absorption) with the original plan never mutated. Zero High; one Medium — the `Queryset diffing` GLOSSARY entry at `docs/GLOSSARY.md:840-853` does not document the consumer-`.only()`-wins drop rule shipped via `_consumer_only_fields` in `0.0.7`, even though the per-`plans.py:343-355` docstring frames the rule as a permission-boundary contract a consumer can key against. Four Lows are all comment / convention items (cache-invariant docstring scope; `is_empty` consequence; `_consumer_prefetch_lookups` `or ()` defensive coda; paired-but-unanchored `P1`/`P2`/`M1` audit-trail tags). Shape #4 qualifier — GLOSSARY Medium requires a real edit per `worker-1.md` "GLOSSARY-only fixes do NOT qualify [for shape #5] — they need a real edit; route through shape #4". Standard three-spawn cycle collapses to consolidated single-spawn at Worker 2 per shape #4.

---

## Fix report (Worker 2)

Consolidated single-spawn pass per shape #4 (GLOSSARY Medium + 4 defer-with-trigger comment-tightening Lows; no source logic change; no test added).

### Files touched
- `docs/GLOSSARY.md` `Queryset diffing` section — appended fifth cooperation bullet (`only()` cooperation) verbatim from the artifact's recommended prose between the existing "Plain-string absorption" bullet and the "See also:" line. Documents the consumer-`.only()`-wins drop rule shipped at `plans.py::diff_plan_for_queryset #"drop_only_fields = bool(plan.only_fields)"` and `plans.py::_consumer_only_fields`.
- `django_strawberry_framework/optimizer/plans.py::OptimizationPlan` (class docstring) — appended trigger paragraph naming the post-`finalize()` immutability scope (list-fields-only via tuple swap; `cacheable` bool remains a settable attribute) and the trigger for moving to `@dataclass(frozen=True)` (second `cacheable` writer or cache-poisoning incident). Cites `walker.py::plan_optimizations` as the only pre-finalize writer. Low #1.
- `django_strawberry_framework/optimizer/plans.py::OptimizationPlan.is_empty` (docstring) — named the consequence (`OptimizationPlan(cacheable=False)` with no other directives reports `is_empty=True`), cited the existing pinning test by `path::test_name`, and recorded the trigger (a resolver-side call site reads `is_empty` and `cacheable` together for a logic decision). Low #2.
- `django_strawberry_framework/optimizer/plans.py::_consumer_prefetch_lookups` (docstring) — added the one-line paranoid-guard rationale for the trailing `or ()` naming the non-`QuerySet` test-double / custom-manager case the artifact called out (stock Django stores tuples; `prefetch_related(None)` resets to `()`), with the trigger for revisiting removal (a real consumer surfaces `None` lookups or the test-double case is retired). Low #3.

### Tests added or updated
- None. All edits are docstring tightening that captures defer-with-trigger conditions; no behaviour change, no contract change.

### Validation run
- `uv run ruff format .` — pass (211 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)

### Notes for Worker 3
- Shadow file: `docs/shadow/django_strawberry_framework__optimizer__plans.overview.md` referenced by the artifact (used for the control-flow / `getattr` density cross-check); no shadow lines cited in edits.
- Low #4 (`P1`/`P2`/`M1` audit-trail anchors) — **defer-with-trigger; no source edit this cycle**. Source scan: `grep -n "P1\|P2\|M1" plans.py` returned no matches, so the anchors live in test comments (`tests/optimizer/test_plans.py:218`, `:311`, `:356`, `:372`, `:387`, `:429`, `:458`) and as the paired `# else: consumer wins on this subtree; optimizer dropped.` at `plans.py::_diff_prefetch_related #"# else: consumer wins on this subtree"`. The artifact's explicit instruction is "Worker 2 should NOT propose a rename or removal without that spec landing"; trigger condition is a Q-series or P-series spec authored for the queryset-diffing subsystem (e.g., a "Queryset cooperation contract" spec for `0.0.9+`). Captured here so the trigger isn't lost on the next pass.
- DRY analysis (three `Defer-with-trigger` items: shared `_extract_lookup_paths`, `_django_private_accessors` namespace, shared `_consumer_owns_field` predicate) — no in-cycle edit; all three are correctly factored today per Worker 1's framing.
- Consolidated single-spawn pass: logic + comment + changelog disposition collapsed into one spawn per shape #4 qualifier (GLOSSARY Medium with verbatim replacement prose pre-derived by Worker 1; remaining items all defer-with-trigger per Worker 1's own prose).
- `uv.lock` not touched.

---

## Verification (Worker 3)

### Logic verification outcome
Consolidated single-spawn (shape #4) terminal-verify. All Medium + Lows addressed or deferred-with-trigger per artifact authorization:
- Medium (`Queryset diffing` GLOSSARY drift): verified — fifth bullet at `docs/GLOSSARY.md:852` matches Worker 1's verbatim "Recommended replacement prose" block char-for-char, inserted after the "Plain-string absorption" bullet and before the existing "See also:" line. No other GLOSSARY hunk in this cycle's scope.
- Low #1 (`cacheable` cache invariant scope): verified — `OptimizationPlan` class docstring at `plans.py:52-63` adds the post-`finalize()` scope paragraph naming the five list fields, the `cacheable` bool convention exception, cites `walker.py::plan_optimizations` as the only pre-finalize writer, and records the `@dataclass(frozen=True)` trigger (second `cacheable` writer or cache-poisoning incident).
- Low #2 (`is_empty` consequence under-promised): verified — `is_empty` docstring at `plans.py:99-108` names the consequence (`OptimizationPlan(cacheable=False)` reports `is_empty=True`), cites `tests/optimizer/test_plans.py::test_cacheable_flag_does_not_affect_empty_state` (grep-confirmed at line 51), and records the trigger (resolver-side call site reads `is_empty` and `cacheable` together).
- Low #3 (`_consumer_prefetch_lookups`'s `or ()` defensive coda): verified — docstring at `plans.py:281-289` names the non-`QuerySet` test-double / custom-manager case, notes stock Django always stores tuples (`prefetch_related(None)` resets to `()`), and records the removal trigger.
- Low #4 (`P1`/`P2`/`M1` audit-trail anchors): correctly deferred per artifact's explicit "Worker 2 should NOT propose a rename or removal without that spec landing" instruction; trigger captured in Notes for Worker 3.

No source-logic changes — `git diff -- django_strawberry_framework/optimizer/plans.py` is exclusively docstring lines inside the three named symbols (no function-body, no `return`, no condition change).

### DRY findings disposition
Three `Defer-with-trigger` items (shared `_extract_lookup_paths`, `_django_private_accessors` namespace, shared `_consumer_owns_field` predicate) correctly carried forward — all three are correctly factored today per Worker 1's framing and no edit was warranted this cycle.

### Temp test verification
None used. Verification was source-spot-check + grep-confirm of the cited test name; no behavior change to pin.

### Verification outcome
cycle accepted; verified

---

## Iteration log

---

## Comment/docstring pass

Folded into the consolidated single-spawn `## Fix report (Worker 2)` above per shape #4. All edits this cycle are docstring/GLOSSARY prose.

### Files touched
- `docs/GLOSSARY.md` — `Queryset diffing` fifth bullet (Medium).
- `django_strawberry_framework/optimizer/plans.py` — `OptimizationPlan` class docstring (Low #1), `is_empty` docstring (Low #2), `_consumer_prefetch_lookups` docstring (Low #3).

### Per-finding dispositions
- Medium (`Queryset diffing` GLOSSARY drift): applied — verbatim replacement prose lifted into `docs/GLOSSARY.md` after the existing "Plain-string absorption" bullet.
- Low #1 (`cacheable` cache invariant scope): applied as docstring tightening per the artifact's recommended shape (option (a) — docstring tightening; option (b) frozen-dataclass deferred per artifact's own trigger).
- Low #2 (`is_empty` consequence under-promised): applied as docstring tightening that names the consequence and the trigger; no logic change.
- Low #3 (`_consumer_prefetch_lookups`'s `or ()` defensive coda): applied as a one-line comment naming the non-`QuerySet` test-double case per the artifact's recommendation; the guard remains in the source.
- Low #4 (`P1`/`P2`/`M1` audit-trail anchors): deferred-with-trigger; no source edit per the artifact's explicit "Worker 2 should NOT propose a rename or removal without that spec landing" instruction. Trigger captured in Notes for Worker 3.

### Validation run
- `uv run ruff format .` — pass (211 files unchanged)
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Same notes as the Fix report above; no additional comment-pass material.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cited per `worker-2.md`'s three-state-disposition gate, BOTH halves required:

- `AGENTS.md` #21 — "Do not update CHANGELOG.md unless explicitly instructed."
- The active plan `docs/review/review-0_0_7.md` is silent on changelog authorisation for the `optimizer/plans.py` cycle item; the dispatch prompt explicitly directs `Not warranted` (internal documentation polish).

This cycle's edits are exclusively internal documentation polish — one GLOSSARY entry append, three docstring tightening passes capturing defer-with-trigger conditions, zero source logic change, zero test added, zero consumer-visible behaviour change. The shipped behaviour the GLOSSARY bullet now documents (consumer-`.only()`-wins drop rule) was already released in `0.0.7` (per the existing `CHANGELOG.md:68` entry referenced in the artifact's Medium body), so the catch-up GLOSSARY work does not warrant a separate CHANGELOG bullet.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (211 files unchanged)
- `uv run ruff check --fix .` — pass

---

## Iteration log
