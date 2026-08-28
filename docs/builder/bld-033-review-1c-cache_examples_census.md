# Build: Review round 1, cohort R1c — plan-cache key hygiene, products conversion, live suites, whole-spec named-test census

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (whole file; Decision 7, Decision 10, Decision 12, Slices 3/5/6, and every `## Test plan` / `## Slice checklist` / `## Edge cases and constraints` / Decision-body / `## Definition of done` named test)
Status: review-accepted

Read-only cohort. No Worker 2 diff exists; this reviews shipped `HEAD`. Nothing in this artifact was accepted because the spec asserts it.

Raw `path:NN` line numbers appear inline alongside symbol identifiers, per `AGENTS.md` #"Source refs in docs and code comments" — permitted only in per-cycle scratchpad artifacts, which this is. Line numbers were read at the time of this pass; `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` is `M` in the working tree (Worker 1's concurrent Slice 0/2 work), so its numbers may have shifted — every spec citation below also carries a distinctive substring.

---

## Plan (Worker 1)

### Dispatched findings checklist

Not applicable in the usual sense — this cohort was dispatched with three jobs rather than a findings list. Restated as boxes and audited below.

- [x] Job 1 — Decision 7 plan-cache key hygiene verified in source and in the Slice-3 tests
- [x] Job 2 — Decision 10 products conversion + Slice 5/6 live pins verified
- [x] Job 3 — whole-spec named-test census completed and classified
- [x] Decision 12 version boundary re-read against `HEAD`
- [x] Card-number rot adjudicated against `KANBAN.md`, every site enumerated
- [x] Pre-archive-path sites enumerated (Slice-0 note, item 6)
- [x] `scripts/review_inspect.py` run on `optimizer/extension.py` with `--output-dir docs/shadow`

---

## Review (Worker 3)

### High:

None. No code defect was found. Every divergence below is spec text.

### Medium:

#### M1 — Decision 6 item 2 (divergent aliases) states the inverse of shipped behavior, in 8 spec homes

Post-ship divergence, introduced by commit `57cbd32a` ("feat: Pluggable nested-connection fetch strategies + Postgres lateral backend"), which the tests label the **"idea-#2 inversion"**. The spec says divergent-argument aliases are one of four shapes "deliberately **not** window-planned"; at `HEAD` they plan **one window per response key**.

Shipped shape (source-side verdict is R1a/R1b's; the test-side evidence is mine):

- `tests/optimizer/test_walker.py::test_divergent_aliases_plan_one_window_per_response_key` (3580) — docstring: "The idea-#2 inversion of the historical spec-033 Decision 6 fallback"; asserts two batched window queries, both response keys recorded as planned, legacy shared `to_attr` absent.
- The residual fallback survives only when **every** alias is itself a fallback shape: `tests/optimizer/test_walker.py::test_divergent_all_keys_fallback_stays_unplanned` (4064) asserts `plan.prefetch_related == ()` and `plan.planned_resolver_keys == ()`.
- Nine-test family at `tests/optimizer/test_walker.py` 3493-4064 plus six at `tests/test_relay_connection.py` 1181-1350.

Spec sites (all need Worker 1's Slice 2):

1. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"Four nested-connection shapes are deliberately"` (Decision 6 opener, :281) — "Four" is now three.
2. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"Aliased duplicates with divergent pagination arguments"` (Decision 6 item 2, :284) — "One `to_attr` cannot serve two windows; per-alias windows are a follow-up" is false; Django accepts multiple `Prefetch`es with distinct `to_attr`s and the shipped code uses that.
3. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"Identical-argument aliases merge; divergent ones fall back."` (`## Edge cases and constraints`, :361).
4. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"Fallback shapes per [Decision 6]"` (Slice-1 checklist, :60).
5. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"test_fallback_not_planned_sidecar_input"` (`## Test plan` Slice 1, :404) — names `..._divergent_aliases` and the "wrong `Prefetch` is absent" assertion.
6. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"leaves the four [Decision"` (DoD item 4, :509) — "leaves the four Decision 6 fallback shapes ... unplanned".
7. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"and per-alias windows"` (`## Out of scope`, :491) — "no card yet" for per-alias windows; they shipped.
8. `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md #"Per-alias windows for aliased nested connections with divergent pagination."` (:107) — a rejected alternative that was later adopted.

Also affected in the same class: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"this card strictly adds planned shapes, never changes unplanned ones"` if that monotonicity sentence is still present (Slice 0 reported it under Decision 6; it is the sentence an inverted fallback contradicts).

#### M2 — `_dst_total_count` is conditional at `HEAD`; three spec homes state it unconditionally

Post-ship divergence, same commit `57cbd32a`. Test-side proof:

- `tests/optimizer/test_walker.py::test_nested_connection_planned_as_windowed_prefetch` (2700) asserts `WINDOW_ROW_NUMBER in annotations` **and `WINDOW_TOTAL_COUNT not in annotations`** — the direct inverse of the spec's Test-plan sentence for that same test name.
- `tests/optimizer/test_plans.py::TestApplyWindowPagination::test_with_total_count_false_omits_count_annotation` and `..._with_total_count_false_reverse_branch_still_bounds` pin the conditional arm.

Spec sites:

1. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"_dst_total_count = Co"` (Decision 4 "**Window**:" bullet, :249) — states both annotations unconditionally.
2. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"whose queryset carries"` (`## Test plan` Slice 1, :390) — "whose queryset carries `_dst_row_number` / `_dst_total_count` annotations"; the shipped test asserts the count annotation is **absent** for that shape.
3. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"`_dst_row_number` / `_dst_total_count` annotations, resolver keys recorded"` (DoD item 4, :509).

Not a site: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"totalCount` (when the target's"` (:271) already states the `Meta.connection`-conditional read and is true as written.

#### M3 — the `first: 0` / overshot-`after:` fallback contract inverted; `last: 0` is the only survivor

Post-ship divergence, same commit `57cbd32a` (marker-row windows). Two spec-named tests are gone as a direct consequence, and the surviving contract is the opposite of the spec's.

Shipped shape:

- `tests/test_relay_connection.py::test_fast_path_ambiguous_empty_served_from_marker_row` (1997) — parameterized over `first: 0` and overshot `after:`; `django_assert_num_queries(2)` with the comment "the fallback never fires"; asserts the marker carries the true `totalCount` (3), byte-identical to the pipeline.
- `tests/test_relay_connection.py::test_fast_path_zero_children_parent_serves_under_ambiguous_shapes` (2123).
- The residual always-fallback shape is `last: 0`: `tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo` (2025), `::test_fast_path_last_zero_quirk_parity_via_fallback` (2062), `tests/optimizer/test_walker.py::test_last_zero_connection_left_fully_unplanned` (5460).

Spec sites:

1. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"Empty wrappers with `limit == 0` or `offset > 0` fall back per parent"` (`## Edge cases and constraints`, :365).
2. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"test_fast_path_first_zero_falls_back_for_total_count_and_pageinfo"` (`## Test plan` Slice 2, :424) — both names.
3. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"per-parent fallback for ambiguous empty windows"` (DoD item 5, :509 block).
4. Decision 5's body wherever it states the ambiguous-empty fallback (`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `### Decision 5`, :258-278).
5. `examples/fakeshop/test_query/test_library_api.py::test_nested_connection_first_zero_empty_page_live` docstring still says "fast-path -> per-parent fallback" — a **test-comment** divergence, not a spec one; recorded for the maintainer, not fixed here (the test asserts wire results only, so it stays green either way).

#### M4 — Decision 6 item 3's "neither suppress nor shape the window" is false of this card's own seam

`docs/README.md #"OptimizerHint.strategy(...)` overrides the nested-connection fetch backend"` (:177) documents a non-`SKIP` hint shape that **does** shape the window — it selects the nested-connection fetch backend for one Relay connection field, overriding `nested_connection_strategy=` on `DjangoOptimizerExtension`, the `NESTED_CONNECTION_STRATEGY` setting, or `"auto"`. The symbol exists: `django_strawberry_framework/optimizer/hints.py::OptimizerHint.strategy` (:193).

This is a **post-ship change to what this card's seam does**, not merely a later card adding adjacent surface, so `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"neither suppress nor shape the window"` (Decision 6 item 3, :287) is a false sentence about shipped behavior.

The related settings exist too and are read at fetch time:

- `django_strawberry_framework/conf.py #"NESTED_CONNECTION_STRATEGY_KEY = "` (:76) with the resolver defaulting to `"windowed"` (:481).
- `django_strawberry_framework/conf.py #"SINGLE_PARENT_FAST_PATH_KEY = "` (:84), resolver default `True` (:491), documented at `docs/README.md #"SINGLE_PARENT_FAST_PATH"` (:209).

**Verdict on the no-new-surface claim.** `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"This card adds no public symbol, no `Meta` key, and no constructor argument."` (`## User-facing API`, :159) is **still true of this card** — every symbol above post-dates it, and `git diff -- django_strawberry_framework/__init__.py` is empty (public-surface check below). Worker 1's choice is whether to leave the sentence narrow-and-true or add a `**Post-ship:**` note naming the four surfaces so a reader of the final implementation record is not misled about the seam's shipped shape. **I cannot attribute the four surfaces to a card**: no file under `docs/SPECS/` has the strategy seam as its subject, and the commit (`57cbd32a`) labels itself "idea #2" with no card id.

#### M5 — `TODO-BETA-062-0.1.5` is the correct id; **9** occurrences of `051` rot across the pair (Slice 0 measured 7)

Adjudicated against `KANBAN.md`, which settles it twice:

- `KANBAN.md #"Swept 2026-08-07: all 32 occurrences of the dead card id"` (:333) — "after confirming 062 is the natural host - its scope (node / nodes, `totalCount`, the subscription surface) covers every referencing subject."
- `KANBAN.md #"### [TODO-BETA-062-0.1.5 - Fakeshop GraphQL schema activation]"` (:1023) — the card exists under that id.
- `KANBAN.md #"### [TODO-ALPHA-051-0.0.15 - Boundary hardening and system-wide DRY squeeze]"` (:211) — `051` today names a **different, unrelated** card, so every bare `051` in this pair resolves to the wrong card rather than to nothing.

Complete site list (occurrences, not lines; measured with `grep -o` at the time of writing):

| File | Line | Spelling | Action |
|---|---|---|---|
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 534 (DoD item 11) | `` `051`'s body reconciled `` | -> `TODO-BETA-062-0.1.5` |
| `docs/SPECS/appx/…-rationale.md` | 32 (Revision 1) | `TODO-BETA-051-0.1.5` | -> `TODO-BETA-062-0.1.5` — **missed by Slice 0** (a full-id spelling, invisible to a bare-numeral grep) |
| `docs/SPECS/appx/…-rationale.md` | 223 (Decision 10 justification) | `` `051` `` ×2 | -> `TODO-BETA-062-0.1.5` |
| `docs/SPECS/appx/…-rationale.md` | 230 (rejected alternative) | `` `051` `` ×1 | -> `TODO-BETA-062-0.1.5` |
| `docs/SPECS/appx/…-rationale.md` | 279 (Risks item 2) | `` `051` `` ×3 | -> `TODO-BETA-062-0.1.5` |
| `docs/SPECS/appx/…-rationale.md` | 303 (Non-Decision deliberation) | `` `051` `` ×1 | -> `TODO-BETA-062-0.1.5`, and the bullet's claim that "the correction is Slice 2's" is still open |

Total: **9 occurrences** — 1 in the spec, 8 in the companion. The 5 spec + 3 companion `TODO-BETA-062-0.1.5` occurrences (spec :79 :127 :230 :480 :490; companion :223 :279 :303) are **correct and must not be touched**.

**Same defect class, three more populations Slice 0 did not name** (each validated by resolving every card id in the pair against `KANBAN.md`):

- `TODO-BETA-047-0.1.2` ×2 in the spec (:37 `## Key glossary references`, :493 `## Out of scope`) — the `Meta.search_fields` card is `TODO-BETA-056-0.1.2` today (`KANBAN.md` :648). Pre-renumber rot.
- `TODO-ALPHA-035-0.0.10` ×3 in the spec (:126 :231 :488) and ×2 in the companion (:207 :215), plus `TODO-ALPHA-034-0.0.10` ×1 in the spec (:128) — both cards have **shipped**; the spec itself already says `DONE-034-0.0.10` (:492) and `DONE-035-0.0.10` elsewhere, so the file contradicts itself on the same two cards. Post-ship status rot, not renumber rot.
- `WIP-ALPHA-033-0.0.9` at `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"move [`WIP-ALPHA-033-0.0.9`][kanban] to Done"` (`## Doc updates`, :480) — the move has happened (`DONE-033-0.0.9`). The companion's occurrence (:32, Revision 1 provenance) is **legitimately historical** and must not be shifted, per `KANBAN.md`'s own rule at :414 ("a sentence describing a PAST renumber is true only in the numbering of its own time").

#### M6 — Decision 12 / DoD item 12 is false as a present-tense sentence, and one of its four named artifacts no longer exists

`docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"`pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged"` (DoD item 12, :535). Read as a claim about this card's slices it is historically true; read as prose in a shipped card's **final implementation record** it is false today:

- `django_strawberry_framework/__init__.py #"__version__ = "` (:61) is `0.0.14`.
- `tests/base/test_init.py::test_version` asserts `"0.0.14"`.
- `pyproject.toml #"dynamic = [\"version\"]"` (:8) carries **no version literal at all** — hatchling derives it from `__version__` via `[tool.hatch.version]` (:106), matching `AGENTS.md` #"The release is single-sourced in". So "`pyproject.toml` … unchanged" names a file that no longer participates.
- `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"the on-disk version is still `0.0.8` at spec-authoring time"` (opener, :1) is already self-dating and is the model for the fix.

Recommended shape: date the sentence ("no slice edited …"), and drop or re-word the `pyproject.toml` clause against the single-source rule.

### Low:

#### L1 — `test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` is order-dependent and can fail spuriously

`tests/optimizer/test_extension.py::test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` (:2473) asserts the wrapped collector ran **exactly once**. It reaches the collector only on a **miss** in the module-level `_doc_key_cache` LRU (`django_strawberry_framework/optimizer/extension.py #"_doc_key_cache: \"OrderedDict"`, :530). Its document text is byte-identical to `::test_nested_pagination_variable_keys_cache` (:1671), which inserts that exact key. `pytest.ini`'s `--dist loadscope` keeps the whole module on one worker, so the two share the LRU.

Proved with a temp test rather than argued:

```
docs/builder/temp-tests/r1c/test_probe_memo_order.py
  test_a_first_populates_doc_cache        -> passes; asserts (Q, "Q") in _doc_key_cache
  test_b_memo_counter_sees_zero           -> passes; the shipped test's counter reads 0, not 1
uv run pytest docs/builder/temp-tests/r1c/test_probe_memo_order.py --no-cov -q -n 0  ->  2 passed
```

The shipped test passes today only because pytest's actual execution order runs it **before** :1671 — measured, not assumed, with a `pytest_runtest_call` wrapper printing the LRU state:

```
[PRE test_cache_key_variable_name_collection_memoized_for_nested_fallbacks] size=20 present=False
[PRE test_nested_pagination_variable_keys_cache]                            size=46 present=True
uv run pytest tests/optimizer/test_extension.py --no-cov -q -n 0  ->  166 passed
```

Direction of failure is **loud, not silent**: a reorder makes the count 0 and the test fails, so it is a flake risk rather than lost coverage. Fix: `monkeypatch.setattr(extension_module, "_doc_key_cache", OrderedDict())` at the top of the test, exactly as `::test_doc_key_cache_evicts_when_full` (:1331) already does. Not `revision-needed` on its own; recorded for Worker 1 to route.

#### L2 — `test_m2m_shared_child_partitions_per_parent` no longer exercises the shared-child scenario its spec sentence describes

`docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"two parents share one child and still receive independent per-parent pages, catching accidental child-pk partitioning"` (`## Test plan` Slice 1, :395), restated at `#"M2M shared children"` (`## Edge cases and constraints`, :363).

`tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent` (:3235) is now three lines: two `window_partition_for_prefetch(...)` equality assertions. It never builds two parents sharing a child and never asserts independent pages. A tree-wide grep for a shared-child nested-connection fixture finds none in the package tree.

The **contract is still earned**, live and elsewhere: `examples/fakeshop/test_query/test_library_api.py::test_nested_total_count_no_per_parent_count` (:5438) seeds 3 books all carrying the **same** 4 genres and asserts each parent's `genresConnection` returns `totalCount == 4` with exactly 2 edges — per-parent-correct paging over shared children. So this is a census/description defect, not lost coverage. Either re-word the two spec sentences to describe what the named test pins, or point them at the live test.

#### L3 — the spec's `relay_max_results` Slice-6 instruction rests on a premise `HEAD` no longer satisfies

`docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"for a collection *larger* than the cap — assert the capped page"` (`## Test plan` Slice 6, :463). At `HEAD` the products graph has no over-cap collection left: the spec-034 cascade activation narrowed every anonymous set under 100. The shipped test says so in its own docstring — `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` #"that pin no longer exercises the cap boundary" — and asserts `0 < visible_entries.count() <= _RELAY_MAX_RESULTS` with `expected` being the whole visible set.

Consequence: **no products live test asserts a genuinely capped page.** `::test_cascade_staff_sees_everything` (:2270) computes `min(model.objects.count(), _RELAY_MAX_RESULTS)` but also asserts `models.Category.objects.count() <= _RELAY_MAX_RESULTS`, so the `min()` never caps. The capping behavior itself is pinned in the package tree at `tests/test_connection.py::test_relay_max_results_cap` (:999), which is legitimate under the spec's own `## Test plan` intro (the cap is a `strawberry_config` property, not a fakeshop-graph property) — so this is a spec-text divergence, not a placement finding.

#### L4 — the `ValueError` half of the same sentence is now wrapped before it reaches a consumer

Same sentence (:463): "(Strawberry rejects `first:` above the cap with a `ValueError`, so the cap is a hard ceiling…)".

Floor-fact check as required: the installed Strawberry is **0.324.0**, not the locked 0.316.0 the spec source-verified against (read with `uv pip list`: `strawberry-graphql 0.324.0`, `django 6.1`, `graphql-core 3.2.8`, `channels 4.3.2`; Python 3.14.2). The raise still exists there — `.venv/lib/python3.14/site-packages/strawberry/relay/utils.py #"Argument 'first' cannot be higher than"` (:155-157) raises `ValueError` — so the claim holds **inside Strawberry**.

What changed is the consumer-visible shape: `tests/test_connection.py::test_over_cap_first_is_graphql_error` (:2104) asserts the package converts it to a `GraphQLError` and explicitly asserts `original_error` is **not** a `ValueError`. The "hard ceiling" half of the spec sentence is intact; the `ValueError` half now describes an internal, not a wire, behavior.

#### L5 — `TestDeterministicOrderHoistParity`'s parity premise is structurally unprovable at `HEAD`

`docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"the hoisted rule answers identically to the previous `connection.py` implementation"` (`## Test plan` Slice 1, :411). There is no "previous implementation" to compare against: `connection.py` re-exports the hoisted helper, and `tests/optimizer/test_plans.py::TestDeterministicOrderHoistParity::test_deterministic_order_matches_connection_reexport` (:1205) asserts `connection._ends_in_unique_column is ends_in_unique_column` — **identity of one source**, which is the correct post-hoist shape. The class docstring still restates the stale premise. Re-word the spec sentence to the single-source contract.

#### L6 — a private cross-module import in the file this cohort inspected

`django_strawberry_framework/optimizer/extension.py #"from .nested_fetch import _active_strategy as _active_nested_strategy"` (:95) consumes an underscore-private name from a sibling module. Surfaced by the static helper's Imports section. Not a correctness issue; either promote the name or record the intentional coupling.

#### L7 — four spec-named single-cardinality pins whose docstrings claim parent-count independence

Each asserts an **absolute** count derived from a real run (so it is distinguishing — an N+1 would be `1 + N`), but none varies the parent cardinality the way `BUILD.md` #"Query-shape tests must pin the load-bearing property" prefers:

- `tests/test_relay_connection.py::test_fast_path_single_query` (:1133) — `django_assert_num_queries(2)` at one cardinality (4 parents); docstring claims "independent of parent count".
- `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility` (:5513) — `len(captured) == 2` at one cardinality (2 genres); docstring claims "FLAT (parent-count-independent)".
- `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` (:1317) and `..._selects_nested_forward_fk_depth_2_over_http` (:1398) — `len(captured) == 3` at `seed_data(1)` only. These are the card's regression fence, re-pinned rather than authored, and each additionally asserts the no-JOIN / Prefetch-chain SQL shape, so the count is not the only property pinned.

Also `examples/fakeshop/test_query/test_library_api.py::test_nested_total_count_no_per_parent_count` (:5438) asserts only `len(with_captured) == len(without_captured)` — an equality with no absolute anchor. Both shapes falling back per-parent would still be equal. Its sibling `::test_nested_total_count_without_edges` (:5426) does assert `len(captured) == 2` absolutely for the same shape, so the family covers the gap; no action needed beyond noting it.

Contrast — the two pins that do it right, and are the model:

- `examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count` (:5277) runs **3 genres and 10 genres** exactly as the spec demands, resets the graph between runs, asserts `three_count == ten_count` **and** `three_count == 2`, plus per-parent page-correctness on the wire.
- `examples/fakeshop/test_query/test_library_api.py::test_list_relation_and_connection_sibling_coexist_live` (:5650) — 2 and 4 parents, equal counts, absolute `== 3`.

#### L8 — the products nested-connection pin varies child cardinality, not parent cardinality

`examples/fakeshop/test_query/test_products_api.py::test_products_categories_items_connection_fixed_query_count` (:1948) — this **is** the new pin the spec's Slice 6 promises (`docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"New: one nested relation-connection shape on the products graph"`, :465), and the spec names no test for it, so it is present under a name of the builder's choosing.

It runs `seed_data(1)` and `seed_data(3)` and asserts equal counts plus absolute `== 2`. But `examples/fakeshop/apps/products/services.py::seed_data` #"Ensures ``count`` ``Item`` instances exist" creates **one Category per Faker provider regardless of `count`** and `count` Items per provider — so the varied axis is children-per-parent, not parents. The test's own docstring states this correctly ("Both seedings hold the parent-category count fixed and grow items-per-category"). The absolute `== 2` against ~26 public parents is what rules out the per-parent fallback (the docstring records the measured fallback shape as ~52 / ~102), so the pin is sound; only the axis is worth naming.

#### L9 — five pre-archive path spellings (Slice-0 note item 6 reported three)

The spec lives at `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`; the companion at `docs/SPECS/appx/`. Sites still naming the pre-archive working location `docs/spec-033-connection_optimizer-0_0_9.md`:

| File | Line | Context |
|---|---|---|
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 218 | Decision 1 "lives at" |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 480 | `## Doc updates` KANBAN sub-bullet |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 503 | DoD item 1 — **two** occurrences: the filename and the `--spec` argument |
| `docs/SPECS/appx/…-rationale.md` | 302 | `## Non-Decision deliberation` |

**4 sites / 5 occurrences**, one of them in the companion Slice 0 did not sweep. The `--spec` argument is the load-bearing one: run at the stale path the command fails; run at the real path it passes, and its stated result has moved —

```
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md
OK: 38 terms - all have glossary entries and at least one spec link.
```

DoD item 1 says "reports `OK: <N> terms`", so only the path needs correcting; `N` is 38 if Worker 1 wants it concrete. `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-terms.csv` exists as named.

### DRY findings

- `docs/shadow/django_strawberry_framework__optimizer__extension.overview.md` reports **Repeated string literals: none** for `optimizer/extension.py`. Recorded here for the integration pass's cross-cohort comparison, which needs this section from every cohort.
- The pagination argument family has exactly one spelling: `django_strawberry_framework/optimizer/extension.py #"_PAGINATION_ARG_NAMES = frozenset("` (:136), with its comment naming the future `search:` extension as the reason it is a constant rather than an inline tuple. No duplicate spelling anywhere in the module.
- The two family wrappers `_collect_directive_var_names` (:295) and `_collect_nested_pagination_var_names` (:313) are thin projections of one `_collect_cache_var_families` (:283) traversal — the correct shape, and the docstring at :231 records the merge of the two formerly-separate walkers with the reason ("keeping them apart risked a future fragment-depth or cycle fix landing on only one path"). No existence challenge: both wrappers have real test callers, and the union collector (:333) has the production caller.
- L6 above is the only import-boundary observation.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export list are unchanged. This cohort writes no source, so the check is trivially satisfied; it is recorded because M4 raises a public-surface question, and the answer is that the four post-ship surfaces (`OptimizerHint.strategy`, `nested_connection_strategy=`, `NESTED_CONNECTION_STRATEGY`, `SINGLE_PARENT_FAST_PATH`) reach consumers through `optimizer/hints.py`, the extension constructor, and `conf.py` — not through the package root.

### CHANGELOG sanity

Not applicable; cohort did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; cohort did not modify docs/release/KANBAN/archive surfaces. `KANBAN.md` and `docs/README.md` were **read only**, to settle M5 and M4 respectively.

### Static helper use

Run as required (`BUILD.md` `### When to run the helper during build` — a file under `optimizer/`):

```
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/extension.py --output-dir docs/shadow
```

Sections walked, per the mandate:

- **Django / ORM markers — 8 entries, all justified, none a finding.** `select_related` at :99 is the `prune_unsupportable_select_related` import and at :1179 its single call site inside `apply_to`; `QuerySet` at :1117 :1121 :1492 :1496 are type annotations on `apply_to` / `apply_connection_optimization`; `field_map` at :1374 :1376 are read-only reads inside `check_schema`. This module constructs no queryset and issues no query — every ORM effect is delegated to `plans.py` / `walker.py`.
- **Repeated string literals — none.** See DRY findings.
- **Control-flow hotspots — 13 entries.** Two sit on this cohort's seam: `_walk_cache_relevant_vars` (:193, 88 lines / 9 branches) and `_freeze_variable_value` (:375, 61 / 12), plus `_build_cache_key` (:1394, 75 / 5). All three were read line by line against Decision 7 (below); the branch counts are the depth rule, the fragment cycle guard, and the container taxonomy respectively — inherent to the contract, not accidental complexity. The remaining ten are outside this cohort's scope.
- **Imports — 35.** One flagged: L6. The `..utils.querysets` / `..utils.typing` cross-folder imports are the established direction and appear throughout the package.

No skips.

### Job 1 — Decision 7 plan-cache key hygiene: what was proven

Every Decision 7 bullet holds at `HEAD`. Traced in source, not accepted on the docstrings:

- **Nested pagination variables fold into the key; root ones do not.** `django_strawberry_framework/optimizer/extension.py::_walk_cache_relevant_vars #"if depth >= 1 and isinstance(node, FieldNode)"` (:242). The walk enters at depth 0 with the `OperationDefinitionNode`, which is not a `FieldNode`, so `child_depth` stays 0 for root fields (`#"child_depth = depth + 1 if isinstance(node, FieldNode) else depth"`, :248) and their children reach depth 1. Root excluded, nested collected — correct by construction.
- **Fragment traversal preserves response-path depth.** The spread is resolved with `depth=child_depth` (:270) and the fragment definition is walked at that same depth (:277); a `FragmentDefinitionNode` is not a `FieldNode`, so its body inherits the **spread-site** depth. Root-in-a-`Query`-fragment stays root; nested-in-a-parent-fragment stays nested.
- **The cycle guard is `(name, depth)`, not name.** `django_strawberry_framework/optimizer/selections.py::resolve_unvisited_fragment #"visit_key: Any = frag_name if depth is None else (frag_name, depth)"` (:293). A name-only key would let a root-depth spread suppress a later nested spread of the same fragment and silently drop `$n` — the exact under-collection Decision 7 calls a correctness bug. Pinned by `tests/optimizer/test_extension.py::test_fragment_spread_at_two_depths_collects_nested_pagination_variable` (:1783), which runs **both** spread orders.
- **The collection is the documented syntactic superset.** `#"if arg.name.value in _PAGINATION_ARG_NAMES and isinstance(arg.value, VariableNode)"` (:244) keys off the argument **name** only, with no connection check. `tests/optimizer/test_extension.py::test_pagination_var_collection_is_syntactic_superset` (:1814) pins a plain `someField(first: $n)`; `::test_collect_nested_pagination_var_names_all_arg_names` (:1846) pins all four names and excludes a non-pagination `$lim`.
- **Memoized per operation identity — two tiers.** Per-execution: `_cache_key_parts_cache` is a `ContextVar` dict installed by `on_execute` (`#"key_parts_token = _cache_key_parts_cache.set({})"`, :997, reset in the `finally` at :1016) and read in `_build_cache_key` keyed on `id(operation)` (:1444-1460). Cross-request: `_doc_cache_entry` (:533) memoizes `(doc_key, var_names)` in a bounded LRU keyed on `(operation.loc.source.body, operation_name)`, falling back to direct computation — never caching — for a `loc`-less programmatic AST (:549-556). A nested fallback pipeline calling `_build_cache_key` once per parent row therefore walks the AST **zero** additional times after the first. Pinned by `::test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` (:2473), with the caveat at L1.
- **B1 properties unregressed.** `uv run pytest tests/optimizer/test_extension.py --no-cov -q -n 0` -> **166 passed**, including the hit/miss counters, LRU promotion, and immutability suites.

**Fail-open hunt on the cache key — clean, and clean in the severe direction.** The specific shape the prompt names (a collector that silently collects nothing on an unrecognized AST shape, producing a key that cannot distinguish two requests) does not exist here:

- `ast_child_selections` (`selections.py`:248) returns `()` only when `selection_set is None`, which for real graphql-core nodes means a leaf field — the correct answer, not a swallowed failure. The walk's only inputs are `info.operation` and `info.fragments`, both parser output.
- `node.arguments or ()` (:243) — `FieldNode.arguments` is always a tuple in graphql-core; absent means no arguments.
- `if k in variable_values` (:1456) drops a collected name the request did not supply. Not fail-open: graphql-core's `coerce_variable_values` populates defaults, so absence means the argument was genuinely not provided, and every request in that state behaves identically.
- The one clamp-shaped path is `_freeze_variable_value`'s two `except Exception` arms (:384, :428) and its non-container arm (:397). All three return `("opaque", type_id, object())` — a **fresh unique token per value**. An incoherent or hostile value therefore produces a key that can never equal another request's, i.e. a guaranteed cache **miss**. That is fail-closed in the only direction that matters for a cache key. The realistic pagination types (`int`, `str`) are in `_SAFE_CACHE_SCALAR_TYPES` (:162) and retain structural identity, so two requests sending the same `first: 2` still share a plan.
- Literals are not collected — deliberately, and correctly: `print_ast(operation)` is key component 1, so `booksConnection(first: 2)` and `(first: 5)` already differ in the document key. Pinned by `::test_collect_nested_pagination_var_names_ignores_inline_literals` (:1870).

**One precision note, no action required:** `docs/SPECS/spec-033-connection_optimizer-0_0_9.md #"two plans, two windows"` (`## Test plan` Slice 3, :432) describes `::test_nested_pagination_variable_keys_cache` as pinning two plans and two windows; the shipped test pins two **keys** (`key_two != key_five`). Key inequality is the load-bearing half at the cache boundary, and the window half is earned live by `::test_nested_connection_pagination_from_graphql_variable_live`. Worker 1 may tighten the sentence or leave it.

### Job 2 — the products conversion and the live pins: what was proven

- **Conversion is connections-only.** `examples/fakeshop/apps/products/schema.py::Query` carries four `DjangoConnectionField` class attributes (`#"all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)"` and the three siblings) and **no** list resolvers. The docstring states the cookbook mirror explicitly.
- **No `Meta.connection` `total_count` opt-in on any of the four types.** `grep -n 'connection\s*=\|total_count' examples/fakeshop/apps/products/schema.py` returns only the prose line at :240 ("This conversion intentionally adds neither"). Contrast `examples/fakeshop/apps/library/schema.py`, which carries three real `connection = {"total_count": True}` opt-ins — so the absence in products is a deliberate difference, not an artifact of the grep.
- **No root `DjangoNodeField` / `DjangoNodesField` on products.** Same grep: zero. The library schema has both (:572-574), so the fence is real and holds.
- **The three `test_products_optimizer_*` pins hold through `edges { node }` with counts intact.** `::test_products_optimizer_merges_duplicate_root_field_nodes_over_http` (:1258) — two `allItems { edges { node ... } }` selections merge into one item slice, `len(captured) == 2`, exactly one item slice, no inter-products JOIN. `::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` (:1317) — `len(captured) == 3` with the table order asserted per query. `::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` (:1398) — `len(captured) == 3`, plus `"IN (SELECT"` present and the JOIN shape asserted absent. All three additionally derive expected rows from an equivalent post-cascade ORM query (API == ORM). Single-cardinality caveat at L7.
- **`check_name_permission` denial gates re-pinned on the synthesized arguments.** Filter side: `::test_products_items_flat_category_name_permission_fires_for_anonymous` (:1558), `::test_products_items_deep_flat_category_name_permission_fires_for_anonymous` (:1580), and the staff counterparts. Order side: `::test_products_categories_order_by_name_denied_for_anonymous` (:1807) and `::test_products_categories_order_by_name_as_staff` (:1824). All spell the argument on the connection root field and assert against `edges { node }`.
- **The new reverse-FK nested-connection pin exists.** `::test_products_categories_items_connection_fixed_query_count` (:1948), with the deliberate no-sidecar comment (`#"a ``filter:`` / ``orderBy:`` sidecar on a NESTED connection diverts it to the per-parent fallback"`, :1926) that makes the test take the path it claims. See L8 for the axis note.
- **All six named Slice-5 library tests are present and pin their sentences** — see the census table. `::test_nested_books_connection_fixed_query_count` is the one that does two-cardinality + absolute-count correctly, exactly as the spec's "with 3 genres and with 10 genres" demands.

### Job 3 — the whole-spec named-test census

Population: **76 distinct test names** the spec (or its rationale, where the spec cites it) names anywhere — `## Test plan` Slices 1-6, `## Slice checklist` sub-bullets, `## Edge cases and constraints`, Decision bodies, `## Current state`, and `## Definition of done`. The spec writes several as `name` / `..._suffix` shorthands (e.g. `#"test_fallback_not_planned_sidecar_input` / `..._divergent_aliases` / `..._skip_hint` / `..._distinct_target`"`); each shorthand is expanded to its full name below. Existence was measured with `grep -rn "def <name>(" tests examples --include='*.py'` — occurrences, one pass per name, not a single long pattern.

Bucket counts:

| Bucket | Count | Names |
|---|---|---|
| present and pinning the contract | **66** | everything not listed in the other four rows (rows 1, 3-6, 9-19, 21, 23-28, 30, 32-40, 43-70, 71-75) |
| present but no longer pinning it | **3** | `test_nested_connection_planned_as_windowed_prefetch`, `test_m2m_shared_child_partitions_per_parent`, `test_version` |
| renamed | **4** | `test_window_partition_for_reverse_fk_forward_m2m_reverse_m2m`, `test_fallback_not_planned_distinct_target`, `test_apply_window_pagination_unit`, `test_deterministic_order_helper_hoist_parity` |
| absent, contract dropped | **3** | `test_fallback_not_planned_divergent_aliases`, `test_fast_path_first_zero_falls_back_for_total_count_and_pageinfo`, `test_fast_path_after_end_falls_back_for_total_count_and_pageinfo` |
| **absent, contract still stated (genuine lost coverage)** | **0** | — |

**Nothing planned in the spec was simply never implemented.** Every absent name is absent because the contract itself changed, and every renamed one resolves to a live pin. That is the answer to the cycle's central question.

**Delta against Worker 0's sample.** Worker 0 reported 6 MISSING. The complete enumeration finds **7** absent names — the seventh is `test_window_partition_for_reverse_fk_forward_m2m_reverse_m2m` (renamed, not lost). Worker 0's PRESENT set is confirmed by name, and every body was read.

Full table (one row per named test):

| # | Test name | Bucket | Evidence |
|---|---|---|---|
| 1 | `test_relation_connections_slot_recorded` | present, pinning | `tests/optimizer/test_walker.py`:2580 — asserts `genre_def.relation_connections == {"books_connection": "books"}` and the suppressed-shape case |
| 2 | `test_nested_connection_planned_as_windowed_prefetch` | **present, no longer pinning** | `tests/optimizer/test_walker.py`:2700 — pins `to_attr` + `WINDOW_ROW_NUMBER`, but asserts `WINDOW_TOTAL_COUNT **not** in annotations`, the inverse of the spec sentence. See M2 |
| 3 | `test_window_slice_from_first_after_literals` | present, pinning | `tests/optimizer/test_walker.py`:3039 — `> 2` / `<= 5` in the window SQL |
| 4 | `test_window_slice_from_variables` (spec `..._from_variables`) | present, pinning | `tests/optimizer/test_walker.py`:3129 — variables resolve; `<= 100` (the cap) absent |
| 5 | `test_window_last_only_uses_reversed_row_number` | present, pinning | `tests/optimizer/test_walker.py`:3173 — `WINDOW_ROW_NUMBER_REVERSED` in annotations and in SQL |
| 6 | `test_window_respects_relay_max_results` | present, pinning | `tests/optimizer/test_walker.py`:3207 — over-cap `first` emits no window, records the key (matches spec :402) |
| 7 | `test_window_partition_for_reverse_fk_forward_m2m_reverse_m2m` | **renamed** | Split into `tests/optimizer/test_plans.py::TestWindowPartitionForPrefetch` (:1059): `test_reverse_fk_partitions_by_child_fk_attname` (:1062), `test_forward_m2m_partitions_by_reverse_query_name` (:1067), `test_reverse_m2m_partitions_through_forward_field_name` (:1079), `test_forward_m2m_partition_diverges_from_accessor` (:1086 — the spec's `related_name`-absent divergence clause, asserting `field.remote_field.name == "books"`). Note the spec sites it in `test_walker.py`; it lives in `test_plans.py` |
| 8 | `test_m2m_shared_child_partitions_per_parent` | **present, no longer pinning** | `tests/optimizer/test_walker.py`:3235 — two `window_partition_for_prefetch` equalities only; no shared-child scenario. See L2 |
| 9 | `test_nested_connection_two_level_recursion` | present, pinning | `tests/optimizer/test_walker.py`:3247 — outer `_dst_books_connection`, inner `_dst_genres_connection` |
| 10 | `test_child_plan_projections_include_connector_and_ordering_columns` | present, pinning | `tests/optimizer/test_walker.py`:3275 — `shelf_id` in the `.only()` clause |
| 11 | `test_window_subquery_wrap_preserves_only_mask_and_child_select_related` | present, pinning | `tests/optimizer/test_walker.py`:4603 — child `select_related` and `WINDOW_ROW_NUMBER` both survive |
| 12 | `test_scalar_only_pageinfo_and_total_count_are_window_planned` | present, pinning | `tests/optimizer/test_walker.py`:3301 — planned, not a fallback; `to_attr` present, resolver key recorded |
| 13 | `test_scalar_only_window_projects_pk_connector_and_order_columns` | present, pinning | `tests/optimizer/test_walker.py`:3321 — `defer is False`, `{"id","shelf_id"} <= only_fields` |
| 14 | `test_scalar_only_window_projects_non_pk_order_column` (spec `..._non_pk_order_column`) | present, pinning | `tests/optimizer/test_walker.py`:2450 — `{"id","tag_id","title"} <= only_fields` |
| 15 | `test_windowed_prefetch_queryset_carries_deterministic_order` | present, pinning | `tests/optimizer/test_walker.py`:3380 — `order_by == ("id",)` |
| 16 | `test_windowed_prefetch_queryset_carries_non_pk_deterministic_order` (spec `..._non_pk_deterministic_order`) | present, pinning | `tests/optimizer/test_walker.py`:2421 — `order_by == ("title","id")`, the pk tiebreaker |
| 17 | `test_malformed_slice_arguments_emit_no_window_but_record_resolver_key` | present, pinning | `tests/optimizer/test_walker.py`:3411 — no prefetch, key recorded, log message carries `(malformed pagination)` and never `response key None` |
| 18 | `test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets` | present, pinning | `tests/optimizer/test_extension.py`:5015 — unions both `dst_optimizer_planned` and `dst_optimizer_fk_id_elisions` |
| 19 | `test_fallback_not_planned_sidecar_input` | present, pinning | `tests/optimizer/test_walker.py`:3469 — `prefetch_related == ()` and `planned_resolver_keys == ()` |
| 20 | `test_fallback_not_planned_divergent_aliases` | **absent, contract dropped** | Inverted by `57cbd32a`. `tests/optimizer/test_walker.py::test_divergent_aliases_plan_one_window_per_response_key`:3580 now plans one window per response key; only the all-fallback case survives (`::test_divergent_all_keys_fallback_stays_unplanned`:4064). See M1 |
| 21 | `test_fallback_not_planned_skip_hint` | present, pinning | `tests/optimizer/test_walker.py`:4095 — `OptimizerHint.SKIP` suppresses window planning |
| 22 | `test_fallback_not_planned_distinct_target` | **renamed** | Contract pinned by `tests/optimizer/test_walker.py::test_distinct_child_queryset_left_unplanned_for_correct_total_count`:4387, which the spec names separately at :405 and :371 |
| 23 | `test_distinct_child_queryset_left_unplanned_for_correct_total_count` | present, pinning | `tests/optimizer/test_walker.py`:4387 — no `_dst_books_connection` prefetch, `planned_resolver_keys == ()` |
| 24 | `test_secondary_type_relation_shapes_nested_recognition` | present, pinning | `tests/optimizer/test_walker.py`:4545 — secondary type falls back; no `_dst_books_connection` |
| 25 | `test_identical_alias_args_merge_and_plan` | present, pinning | `tests/optimizer/test_walker.py`:4188 — merged `to_attr`, `len(planned_resolver_keys) == 2` |
| 26 | `test_both_shape_connection_to_attr_coexists_with_list_and_consumer_prefetch` | present, pinning | `tests/optimizer/test_walker.py`:4294 — `None` and `_dst_books_connection` both in `to_attrs`, and both survive `diff_plan_for_queryset` |
| 27 | `test_visibility_target_window_flips_cacheable_false` | present, pinning | `tests/optimizer/test_walker.py`:4341 — `plan.cacheable is False` with the window still planned |
| 28 | `test_planned_resolver_keys_include_connection_field` | present, pinning | `tests/optimizer/test_walker.py`:4268 — exactly one key, containing `books@` (relation field name, not the generated name) |
| 29 | `test_apply_window_pagination_unit` | **renamed** | `tests/optimizer/test_plans.py::TestApplyWindowPagination` (:807), 18 methods covering annotation names, range filters, the reverse branch, the marker/probe shapes, and `.only()` composition |
| 30 | `test_applies_order_by_to_queryset_not_just_the_window` | present, pinning | `tests/optimizer/test_plans.py`:962 — `order_by == ("name","pk")` on **both** the forward and reverse branches |
| 31 | `test_deterministic_order_helper_hoist_parity` | **renamed** | `tests/optimizer/test_plans.py::TestDeterministicOrderHoistParity` (:1140), 8 methods. The parity form is now `::test_deterministic_order_matches_connection_reexport` (:1205), a single-source identity assertion. See L5 |
| 32 | `test_fast_path_single_query` | present, pinning | `tests/test_relay_connection.py`:1133 — `django_assert_num_queries(2)` over 4 parents. Cardinality caveat at L7 |
| 33 | `test_fast_path_through_schema_connection_extension` | present, pinning | `tests/test_relay_connection.py`:1159 — executes the real `relay.connection(...)` field |
| 34 | `test_fast_path_wire_parity_with_pipeline` | present, pinning | `tests/test_relay_connection.py`:1411 — `fast.data == slow.data` |
| 35 | `test_fast_path_wire_parity_last_only` | present, pinning | `tests/test_relay_connection.py`:1443 — same cursors and page flags; `fast.data == slow.data` |
| 36 | `test_fast_path_non_pk_ordering_applies_explicit_deterministic_order_by` | present, pinning | `tests/test_relay_connection.py`:1622 — asserts the outer `ORDER BY` carries a comma (the pk tiebreaker), i.e. the regression signal SQLite's window sort would mask |
| 37 | `test_fast_path_cursor_round_trips_to_fallback_after` | present, pinning | `tests/test_relay_connection.py`:1749 — fast-path `endCursor` continues on an optimizer-less execution |
| 38 | `test_fast_path_fires_for_reverse_fk_without_related_name` | present, pinning | `tests/test_relay_connection.py`:1783 — asserts the accessor is `windowbook_set` while the probe uses the field name |
| 39 | `test_fast_path_total_count_from_annotation_no_query` | present, pinning | `tests/test_relay_connection.py`:1870 — `totalCount == 5` from the annotation |
| 40 | `test_fast_path_total_count_marker_bypasses_non_queryset_guard` | present, pinning | `tests/test_relay_connection.py`:1978 — no errors, `totalCount == 3` |
| 41 | `test_fast_path_first_zero_falls_back_for_total_count_and_pageinfo` | **absent, contract dropped** | `57cbd32a` marker-row windows. Replaced by `tests/test_relay_connection.py::test_fast_path_ambiguous_empty_served_from_marker_row`:1997, which asserts **2** queries and "the fallback never fires". See M3 |
| 42 | `test_fast_path_after_end_falls_back_for_total_count_and_pageinfo` | **absent, contract dropped** | Same replacement — that test is parameterized over both the `first: 0` and overshot-`after:` shapes. See M3 |
| 43 | `test_fast_path_ignores_window_when_sidecar_kwargs_present` | present, pinning | `tests/test_relay_connection.py`:2157 — a `filter:` argument routes to the pipeline |
| 44 | `test_fallback_when_annotations_missing` | present, pinning | `tests/test_relay_connection.py`:2204 — a `to_attr` list lacking annotations is not consumed |
| 45 | `test_fallback_when_no_optimizer_installed` | present, pinning | `tests/test_relay_connection.py`:2245 — pipeline results and page flags |
| 46 | `test_outer_total_count_predicate_ignores_nested_total_count` | present, pinning | `tests/test_relay_connection.py`:2256 — nested `totalCount == 3`, no outer count fired |
| 47 | `test_nested_pagination_variable_keys_cache` | present, pinning | `tests/optimizer/test_extension.py`:1671 — `key_two != key_five`. Precision note in Job 1 |
| 48 | `test_root_pagination_variable_shares_cache` | present, pinning | `tests/optimizer/test_extension.py`:1685 — `key_two == key_five` for a root `first: $n` |
| 49 | `test_mixed_root_and_nested_pagination_variables` | present, pinning | `tests/optimizer/test_extension.py`:1698 — vary root -> equal; vary nested -> differ |
| 50 | `test_root_fragment_pagination_variable_shares_cache` | present, pinning | `tests/optimizer/test_extension.py`:1715 — root connection through a `Query` fragment keys equal |
| 51 | `test_fragment_carried_nested_pagination_variable_collected` | present, pinning | `tests/optimizer/test_extension.py`:1749 — nested connection through a parent-node fragment keys unequal |
| 52 | `test_pagination_var_collection_is_syntactic_superset` | present, pinning | `tests/optimizer/test_extension.py`:1814 — a non-connection nested `someField(first: $n)` is collected |
| 53 | `test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` | present, pinning (order-fragile) | `tests/optimizer/test_extension.py`:2473 — three `_build_cache_key` calls, collector count 1. See L1 |
| 54 | `test_strictness_raise_unplanned_nested_connection` | present, pinning | `tests/test_relay_connection.py`:2329 — `OptimizerError` with `Unplanned N+1: books` |
| 55 | `test_strictness_warn_logs_once_per_occurrence` | present, pinning | `tests/test_relay_connection.py`:2399 — warning logged, execution continues |
| 56 | `test_strictness_warn_nested_fallback_preserves_parent_plan_context` | present, pinning | `tests/test_relay_connection.py`:2423 — the sibling key is never flagged |
| 57 | `test_nested_fallback_does_not_clobber_fk_id_elisions` | present, pinning | `tests/test_relay_connection.py`:2454 — `shelf` never flagged; `genres` is |
| 58 | `test_strictness_silent_when_window_served` | present, pinning | `tests/test_relay_connection.py`:2549 — `"raise"` + window-planned -> silent |
| 59 | `test_strictness_silent_when_planned` (spec `..._when_planned`) | present, pinning | `tests/test_relay_connection.py`:2606 — planned-key short-circuit **with a counter-proof**: the same shape with the key absent raises `OptimizerError` |
| 60 | `test_strictness_silent_when_off` (spec `..._when_off`) | present, pinning | `tests/test_relay_connection.py`:2567 |
| 61 | `test_strictness_silent_no_optimizer` (spec `..._no_optimizer`) | present, pinning | `tests/test_relay_connection.py`:2587 |
| 62 | `test_sidecar_fallback_is_flagged_with_reason` | present, pinning | `tests/test_relay_connection.py`:2378 — message carries `selection carries filter/orderBy` |
| 63 | `test_nested_books_connection_fixed_query_count` | present, pinning | `examples/fakeshop/test_query/test_library_api.py`:5277 — **3 and 10 genres**, equal counts, absolute `== 2`, per-parent page correctness. The model pin |
| 64 | `test_nested_total_count_no_per_parent_count` | present, pinning | `examples/fakeshop/test_query/test_library_api.py`:5438 — with/without `totalCount` equal counts; 3 parents sharing 4 genres. Anchor caveat at L7 |
| 65 | `test_nested_window_respects_book_visibility` | present, pinning | `examples/fakeshop/test_query/test_library_api.py`:5513 — anonymous excludes the `repair` book from pages **and** count; staff sees it; `len(captured) == 2` |
| 66 | `test_list_relation_and_connection_sibling_coexist_live` | present, pinning | `examples/fakeshop/test_query/test_library_api.py`:5650 — 2 and 4 parents, equal counts, absolute `== 3`, list full-set vs windowed page both correct |
| 67 | `test_nested_connection_pagination_from_graphql_variable_live` | present, pinning | `examples/fakeshop/test_query/test_library_api.py`:5722 — `variables={"n": 2}` through the request body drives the window |
| 68 | `test_nested_connection_first_zero_empty_page_live` | present, pinning (docstring stale) | `examples/fakeshop/test_query/test_library_api.py`:5761 — empty edges, `hasNextPage` True. Wire-only, so unaffected by M3; its docstring still names the retired mechanism |
| 69 | `test_genre_books_connection_behavior` | present, pinning, unmodified | `examples/fakeshop/test_query/test_library_api.py`:4114 — the shipped `spec-032` pin, green |
| 70 | `test_book_genres_connection_sidecars_and_total_count` | present, pinning, unmodified | `examples/fakeshop/test_query/test_library_api.py`:5122 — `totalCount == 3` with sidecars |
| 71 | `test_products_optimizer_merges_duplicate_root_field_nodes_over_http` | present, pinning | `examples/fakeshop/test_query/test_products_api.py`:1258 — re-pinned through `edges { node }`, `len(captured) == 2` |
| 72 | `test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` | present, pinning | `examples/fakeshop/test_query/test_products_api.py`:1317 — `len(captured) == 3`, table order asserted |
| 73 | `test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` | present, pinning | `examples/fakeshop/test_query/test_products_api.py`:1398 — `len(captured) == 3`, no JOIN, cascade inline. The cap premise moved: L3 |
| 74 | `test_root_connection_field_queryset_prefetches_node_many_relation` | present, pinning | `tests/test_connection.py`:1339 — `## Current state` no-regression pin |
| 75 | `test_apply_connection_optimization_uses_active_optimizer_cache` | present, pinning | `tests/optimizer/test_extension.py`:4966 — shares the active extension's plan cache |
| 76 | `test_version` | **present, no longer pinning** | `tests/base/test_init.py`:18 — asserts `"0.0.14"`. Decision 12 / DoD 12 name it as "unchanged"; the sentence is now false as written. See M6 |

**Unnamed-but-promised contract, also satisfied:** the spec's Slice 6 promises "one nested relation-connection shape on the products graph … with the fixed-query-count pin" without naming a test. It shipped as `examples/fakeshop/test_query/test_products_api.py::test_products_categories_items_connection_fixed_query_count` (:1948). Worker 1 may want to name it in the spec, as every other Slice-6 pin is named.

**Test-placement check** (`AGENTS.md` test-placement rules, `examples/fakeshop/test_query/README.md` live-first rule). The spec's `## Test plan` intro pins a reason for every package-only family; each stated reason was re-read against `HEAD` and still holds:

- plan-content assertions — plans remain package-internal objects (`optimizer/plans.py`);
- the fallback non-planning matrix — `.distinct()` targets, `SKIP` hints, and divergent secondary-type `relation_shapes` still need synthetic shapes the fakeshop graph does not carry;
- cache-key identity assertions — `_build_cache_key` returns a tuple with no wire projection;
- strictness `"raise"` / `"warn"` — `examples/fakeshop/config/schema.py` still runs strictness `off`, as the products tests' own docstrings state;
- reverse-FK and `"connection"`-narrowed variants, shared-child M2M fixtures, the `_check_n1` parameterization — unchanged premises.

The one live-coverage question this cohort raises is L3 (no live capped-page assertion on products), and there the package-tree home is legitimate under the same intro. **No placement finding.**

### What looks solid

- Decision 7's implementation is the strongest part of this card's surviving surface: the depth rule, the `(name, depth)` fragment guard, the two memo tiers, and the fail-closed opaque-identity fallback all match the Decision line for line, and each has a test that would fail if the property broke — including the negative pin (`test_collect_nested_pagination_var_names_excludes_root_field`) and the both-spread-orders regression pin.
- `test_nested_books_connection_fixed_query_count` and `test_list_relation_and_connection_sibling_coexist_live` are exactly the query-shape discipline `BUILD.md` asks for: two parent cardinalities, an absolute count derived from a real run, a graph reset between runs, and a minimal query that can only take the path it claims.
- The products conversion's two fences (no `Meta.connection`, no root Node fields) are both verifiable in one grep and both hold, with the library schema next door proving the grep would have found them.
- The `to_attr` isolation contract is pinned at three levels: plan objects (`test_both_shape_connection_to_attr_coexists_with_list_and_consumer_prefetch`), the `diff_plan_for_queryset` delta in the same test, and live over `/graphql/`.
- Several tests carry deliberate right-path guards in prose next to the query — the no-sidecar comments at `test_products_api.py`:1926 and `test_library_api.py`:5518 — which is the discipline that stops a "fast path" test silently pinning the fallback.

### Temp test verification

- `docs/builder/temp-tests/r1c/test_probe_memo_order.py` — written to prove L1 mechanically rather than argue it. Demonstrates that the shipped memoization assertion reads 0, not 1, when the module-level `_doc_key_cache` already holds its document. Gitignored.
- Disposition: **noted for follow-up, not promoted.** It is a probe of a test's fragility, not of a package contract; the fix belongs in the shipped test (one `monkeypatch.setattr` line), which is Worker 2's to make if Worker 1 routes L1.
- No other temp test was needed. No transient source mutation was made: this cohort introduces no boundary, so the failability-proof carve-out is not licensed (per its dispatch) and was not used.

### Notes for Worker 1 (spec reconciliation)

Everything below is spec text. None of it is a code defect. Sites are enumerated so Slice 2 can act without re-deriving them.

1. **M1 — Decision 6 item 2 inverted (divergent aliases).** 8 sites listed under M1, spanning the Decision body, its opener's "Four", the Edge case, the Slice-1 checklist, the Test plan, DoD item 4, `## Out of scope`, and the rationale's rejected alternative. Attribution: commit `57cbd32a`, self-labelled "idea #2"; **no owning spec exists** for the strategy seam, so record the commit hash and the label, not a card id.
2. **M2 — `_dst_total_count` is conditional.** 3 sites (Decision 4 "**Window**" bullet, Test plan Slice 1, DoD item 4). Same commit. Note that Decision 5's `totalCount` bullet (:271) is already correct and must not be "fixed" into agreement with the wrong ones.
3. **M3 — ambiguous-empty fallback inverted; `last: 0` is the only survivor.** 4 spec sites plus one stale test docstring (recorded, not fixed — `.py` files are out of this cycle's fence). Same commit.
4. **M4 — Decision 6 item 3's "neither suppress nor shape the window" is false of this card's seam.** `OptimizerHint.strategy` shapes it. The `## User-facing API` no-new-surface sentence is **still true of this card** and needs no correction, but a `**Post-ship:**` note naming the four surfaces (`OptimizerHint.strategy`, `nested_connection_strategy=`, `NESTED_CONNECTION_STRATEGY`, `SINGLE_PARENT_FAST_PATH`) would stop a reader of the final record inferring the seam is argument-free. Unattributable to a card.
5. **M5 — card-number rot: `TODO-BETA-062-0.1.5` is correct; 9 occurrences to fix, not 7.** Full table under M5, including the `TODO-BETA-051-0.1.5` full-id spelling at rationale :32 that a bare-numeral grep cannot see. Three further card-id populations in the same file are named there (`TODO-BETA-047-0.1.2` -> `056`; `TODO-ALPHA-034/035-0.0.10` -> `DONE-`; the `WIP-ALPHA-033-0.0.9` Doc-updates instruction), with the one occurrence that must **not** move called out.
6. **M6 — Decision 12 / DoD 12 false as present tense**, and its `pyproject.toml` clause names a file that no longer carries a version.
7. **L9 — 5 pre-archive path occurrences across 4 sites**, one in the companion. The DoD item 1 `--spec` argument is the one that would actually fail if run; the command at the real path reports `OK: 38 terms`.
8. **L2, L5, L3, L4** — four sentences describing tests or premises that have moved: the shared-child pin, the hoist-parity premise, the over-cap products collection, and the `ValueError` wire shape.
9. **Escalated (maintainer decision, not a worker's):** the census shows **zero** genuine lost coverage but **three** dropped contracts, all from one unowned commit. Every one is a behavior change to a shipped card's surface made without a spec. The pattern — not any individual sentence — is what deserves the maintainer's attention: `spec-033` cannot be made true by editing prose alone unless someone decides where the strategy seam's contract now lives. Resolution paths: (a) record each inversion in-place under a `**Post-ship:**` heading citing `57cbd32a`, leaving the seam unowned; (b) open a card for the nested-connection strategy seam and move the three inverted contracts onto its spec, leaving `spec-033` pointing at it; (c) treat `spec-033` as a frozen historical record and add one `## Post-ship divergences` section listing all three plus M4. I have no basis to choose; (b) is what `BUILD.md`'s "every shipped surface has an owning spec" posture implies.
10. **Cross-cohort input for the integration pass:** `optimizer/extension.py`'s repeated-string-literal count is **0**. R1a and R1b own the equivalent reading for their files.

### Review outcome

`review-accepted`.

Verification is complete across all three jobs. Every divergence found is **spec text** — six Medium and nine Low findings, all documentation defects, split between build-time and post-ship as recorded per finding. No spec contract is undelivered by the code; the plan-cache key is not fail-open and is in fact fail-closed in the severe direction; the products conversion and both fences hold; the live pins are present and, in the two flagship cases, exemplary. The census answers the cycle's central question: **nothing planned was skipped** — zero names sit in the "absent, contract still stated" bucket.

`revision-needed` is not warranted. L1 is the only test-side defect, it fails loudly rather than silently, its fix is one line, and `worker-3.md`'s gate reserves `revision-needed` for a genuine code defect. It is routed to Worker 1 above rather than held here.
