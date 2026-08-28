# Build: Review round 2, cohort R2 — `.py` comment, docstring, and test-defect repair

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (Decision 4's cursor-parity invariant and Decision 11's module map; Decision 5's ambiguous-empty and annotation-probe sentences; Decision 8's strictness mechanism; `## Test plan` Slice 1 `#"two parents share one child and still receive independent per-parent pages"`; `## Test plan` Slice 3's memoization entry)
Status: review-accepted

R2 writes only `.py` files. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` and its `appx/` rationale companion are Slice 2's, running concurrently; this pass neither read the rationale nor wrote either spec file. Raw `path:NN` refs appear inline beside symbol identifiers, which `AGENTS.md` permits in a per-cycle `docs/builder/bld-*.md` scratchpad; nothing this pass wrote **into source** carries a line number, a review-round id, or a finding id.

---

## Plan (Worker 1)

Not applicable in the usual sense: this cohort was dispatched by Worker 0 against the `build-033-connection_optimizer-0_0_9.md` `## R2 ownership partition` entry, with the seven repairs enumerated in the dispatch. The dispatched-findings checklist below is the contract.

### Dispatched findings checklist

- [x] **1.** "`tests/test_connection.py #"TODO(spec-033 Slice 1-2)"` is a live staged anchor naming this build's spec. `BUILD.md` `## Cross-slice integration pass` step 6 requires it discharged or explicitly re-classified." — `tests/test_connection.py #"root-connection no-regression fence"`
- [x] **2.** "Ten source and test sites cite the cursor-parity invariant as \"spec-033 Decision 11\"; the spec sites it on Decision 4." — `django_strawberry_framework/connection.py` x2, `django_strawberry_framework/optimizer/plans.py` x4, `tests/optimizer/test_plans.py` x2, `tests/optimizer/test_walker.py` x2
- [x] **3.** "Ten dead back-compat aliases in `optimizer/walker.py`, whose comment states a reason that is measurably false." — `django_strawberry_framework/optimizer/walker.py #"The selection-traversal primitives live in"` and `#"Aliases for private names that predate"` (comment correction only; the aliases themselves are **escalated** and were not deleted)
- [x] **4.** "L1 — a test docstring still describes the retired two-annotation probe" / "L2 — two strictness test docstrings attribute the silence to the wrong mechanism" / "`test_nested_connection_first_zero_empty_page_live` docstring still says \"fast-path -> per-parent fallback\"" — `tests/test_relay_connection.py::test_fallback_when_annotations_missing`, `::test_strictness_silent_when_off`, `::test_strictness_silent_no_optimizer`, `examples/fakeshop/test_query/test_library_api.py::test_nested_connection_first_zero_empty_page_live` **plus one parallel site the cohorts did not name** (see `### Implementation notes`)
- [x] **5.** "L7 — four spec-named single-cardinality pins whose docstrings claim parent-count independence" / "L8 — the products nested-connection pin varies child cardinality, not parent cardinality" — `tests/test_relay_connection.py::test_fast_path_single_query` and `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility` corrected. **The three `test_products_api.py` sites needed no edit** — re-measured, their prose does not make the claim; see `### Implementation notes`
- [x] **6.** "L1 — `test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` is order-dependent and can fail spuriously" — `tests/optimizer/test_extension.py::test_cache_key_variable_name_collection_memoized_for_nested_fallbacks`
- [x] **7.** "L2 — `test_m2m_shared_child_partitions_per_parent` no longer exercises the shared-child scenario its spec sentence describes" — `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent`

- [x] **Low 1** (review round 2, pass 2). "Repair 5's parallel-site population was never swept; four sites in R2's own files still make the corrected claim at one cardinality." - `tests/test_relay_connection.py::test_divergent_aliases_one_window_query_per_alias`, `examples/fakeshop/test_query/test_library_api.py::test_genre_books_connection_probe_childless_and_populated_parents`, `::test_genre_books_connection_divergent_aliases_batched_per_key`, `::test_nested_books_connection_has_next_page_without_edges`
- [x] **Low 2** (review round 2, pass 2). "`optimizer/walker.py`'s rewritten alias comment states how the change came to be." - `django_strawberry_framework/optimizer/walker.py #"Readers of the underscore aliases below"`
- [x] **Low 3** (Worker 0 mid-flight, pass 2). "Three comments cite a Decision 6 structure the spec no longer has." - `django_strawberry_framework/optimizer/nested_fetch.py::unwindowable_child_queryset_reason` (x2) and `::NestedConnectionStrategy`
- [x] **Low 4** (Worker 0 mid-flight, pass 2). "A fourth Decision 6 citation names the retired structure, in the file just repaired." - `django_strawberry_framework/optimizer/nested_fetch.py #"The private planner"` (module docstring)
- [x] **Low 5** (Worker 0 mid-flight, pass 2). "The `### Notes for Worker 1` census says two two-cardinality pins; there are three." - `docs/builder/bld-033-review-2-py_comment_repair.md` `### Notes for Worker 1 (spec reconciliation)` item 1 (note-only; no `.py` edit)

Not dispatched, and deliberately **not** acted on (`build-033-connection_optimizer-0_0_9.md` `## Escalations`): the `connection_to_attr` strictness probe's shape, `optimizer/plans.py::window_partition_for_prefetch`'s zero production callers, and the deletion of the ten dead walker aliases.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations. Nine `.py` files, all inside the declared R2 partition:

- `django_strawberry_framework/connection.py` — repair 2, two citation sites. Comment/docstring only.
- `django_strawberry_framework/optimizer/plans.py` — repair 2, four citation sites. Docstring only.
- `django_strawberry_framework/optimizer/walker.py` — repair 3, both alias comment blocks rewritten to the measured reader sets. Comment only; **no alias deleted**.
- `tests/test_connection.py` — repair 1, the fence marker re-spelled as non-`TODO` provenance. Comment only.
- `tests/test_relay_connection.py` — repairs 4 and 5, four docstrings plus one inline comment. Docstring/comment only.
- `tests/optimizer/test_plans.py` — repair 2, two citation sites (one of them the wrapped one). Docstring only.
- `tests/optimizer/test_walker.py` — repair 2 (two citation sites, docstring only) **and** repair 7 (the restored shared-child scenario, real assertions).
- `tests/optimizer/test_extension.py` — repair 6, the order-independence fix plus the strengthening call.
- `examples/fakeshop/test_query/test_library_api.py` — repairs 4 and 5, three docstrings plus two inline comments. Docstring/comment only.

Also written, all inside the partition or gitignored scratch:

- `docs/builder/bld-033-review-2-py_comment_repair.md` (this file, new).
- `docs/builder/worker-memory/worker-2.md` (appended).
- `docs/builder/temp-tests/r2/` — three proof manifests, the emitted report, and one throwaway test. Gitignored.

**Not written, and not mine:** `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` and `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` show in `git status` as the concurrent Slice 2 pass's work; `0_0_14.md` is the baseline untracked concurrent file. Three files that `git status` reported dirty at this cycle's session start (`examples/fakeshop/apps/products/services.py`, `examples/fakeshop/test_query/test_debug_extension_api.py`, `examples/fakeshop/test_query/test_products_api.py`) are clean now — a concurrent session committed them mid-cycle. Neither reverted nor edited.

### Re-measured populations

Every count below was re-derived in this pass, not carried from the dispatch.

**Repair 1 — one anchor, as stated.** `grep -rn 'TODO(spec-033' --include='*.py' .` -> exactly 1 before (`tests/test_connection.py:1588`), **0 after**.

**Repair 2 — ten sites, as stated, one of them wrapped.** A single-line `grep -rn 'spec-033 Decision 11' --include='*.py' .` finds **9**. A whitespace-normalized per-file count (`re.sub(r'\s+', ' ', source)` then count) finds **10**, the tenth being `tests/optimizer/test_plans.py::TestApplyWindowPagination::test_applies_order_by_to_queryset_not_just_the_window`, where `spec-033` ends one line and `Decision 11` begins the next. Distribution confirmed: `connection.py` x2, `optimizer/plans.py` x4, `tests/optimizer/test_plans.py` x2, `tests/optimizer/test_walker.py` x2. After the pass the same normalized sweep finds **2** `Decision 11` occurrences, both deliberate and both now paired with Decision 4 — see `### Implementation notes`. No new wrapped citation was created: the re-wrapped `test_plans.py` site keeps `spec-033 Decision 4` whole on one line.

Spec siting re-verified read-only against `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`: the invariant is stated in **Decision 4** (`#"Deterministic order (a cursor-parity invariant, not a tidiness refactor)"`), and Decision 11's own text cites Decision 4 for it. The cross-cohort pin holds.

**Repair 3 — 4 live-via-importer, 3 live-via-body, 10 dead. Confirmed, with one correction of emphasis.** Measured three ways: every occurrence of each name inside `walker.py`; every `from ... walker import` block and `walker.<name>` reference across `tests/`, `examples/`, `django_strawberry_framework/` and `scripts/`; and each name's real owner.

- Imported from `optimizer.walker` (4): `_should_include`, `_is_fragment` (`tests/optimizer/test_walker.py`'s module-level import block), `_concrete_order_columns`, `_relay_max_results_from_info` (function-local imports in the same file).
- Consumed by `walker.py`'s own bodies (3): `_is_fragment` (2 call sites), `_response_key` (4), `_response_keys` (1), `_included_field_selections` (2). `_is_fragment` is in both sets.
- Dead — assignment-only, zero readers through this module (10): `_named_children`, `_node_children_with_runtime_prefix`, `_with_runtime_prefix`, `_connection_window_slice_from_arguments`, `_extend_only_projection`, `_keyset_window_slice_from_arguments`, `_order_entry_field_name`, `_project_scalar_only_window`, `_relation_connection_to_attr`, `_relation_connection_to_attr_for_key`.

Look-alike importers confirmed to take the names from their real owners: `tests/optimizer/test_extension.py` imports `_named_children` / `_node_children_with_runtime_prefix` from `optimizer.extension` (which carries its own alias block); `tests/test_keyset_connection.py` and `django_strawberry_framework/connection.py` import `_extend_only_projection`, `_keyset_window_slice_from_arguments`, `_relation_connection_to_attr` and `_relation_connection_to_attr_for_key` from `optimizer.nested_planner`. **Correction of emphasis, not of count:** three of the ten dead names (`_connection_window_slice_from_arguments`, `_project_scalar_only_window`, and the live-elsewhere `_relay_max_results_from_info`) are *mentioned inside `walker.py` docstrings*. A docstring mention is not a reader, so the count stands at 10; the rewritten comment says "no reader" rather than "no occurrence" so it stays true of those three.

**Repair 4 — three named sites, plus a fourth the cohorts did not name.** A sweep of every `ambiguous` occurrence across the six writable test files found a **second** live-suite docstring asserting the retired per-parent fallback: `examples/fakeshop/test_query/test_library_api.py::test_nested_empty_parent_serves_zero_total_count_no_fallback_live`, whose contrast paragraph reads "that is the AMBIGUOUS empty window (`first: 0`, `limit == 0`) which falls back per parent". Same defect, same class, parallel site — fixed in this pass and flagged for Worker 1 under `### Notes for Worker 1`.

**Repair 5 — two of the five named sites needed an edit; three did not.** Re-read all five bodies and docstrings:

- `tests/test_relay_connection.py::test_fast_path_single_query` — the docstring did claim "independent of parent count" while running one cardinality (4 parents, absolute `django_assert_num_queries(2)`). **Corrected.**
- `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility` — the docstring did claim "FLAT (parent-count-independent)" while running one cardinality (2 genres, absolute `len(captured) == 2`), and two inline comments repeated it. **Corrected** (docstring + both comments).
- `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` and `::..._selects_nested_forward_fk_depth_2_over_http` — re-read: neither claims parent-count independence. "the count stays a fixed 3" and "a deterministic 3 products queries" are both scoped, in their own sentences, to the spec-034 cascade hooks adding zero round-trips, not to parent cardinality. `grep -n 'independent'` over that file returns no hit inside either docstring. **No edit warranted.**
- `examples/fakeshop/test_query/test_products_api.py::test_products_categories_items_connection_fixed_query_count` (L8) — its docstring already names the axis correctly: "Both seedings hold the parent-category count fixed and grow items-per-category". **No edit warranted.**

So the do-not-touch fence on `test_products_api.py` was never reached: no repair required a write there. Nothing is being deferred for lack of write access.

**Repairs 6 and 7** — both reproduced mechanically before editing; see `### Failability proofs`.

### Tests added or updated

- `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent[reverse_m2m]` / `[forward_m2m]` — restored to the scenario its name and the spec sentence promise. Two parents share one child; the planned windowed `Prefetch` is executed against real rows under `first: 1`; each parent's `_dst_<field>_connection` must carry the shared child. Parametrized over **both** M2M directions because they derive the partition from opposite sides of the relation (reverse `Genre.books` through the child's forward M2M field name; forward `Book.genres` through the target's reverse query name). The two pre-existing `window_partition_for_prefetch` equality assertions are **kept** — nothing was weakened. `@pytest.mark.django_db` added; the file already carries one `django_db` row, so this is not a new pattern for it.
- `tests/optimizer/test_extension.py::test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` — made order-independent by installing a fresh `_doc_key_cache` (`monkeypatch.setattr`, the shape `::test_doc_key_cache_evicts_when_full` already uses), and **strengthened**: the original `assert calls["count"] == 1` now runs mid-lifecycle, then the module LRU is cleared and a fourth `_build_cache_key` call is made inside the same `on_execute` lifecycle, with the count re-asserted at 1. Without that fourth call the assertion is satisfiable by either memo tier; with it, only the per-execution `id(operation)` memo the docstring names can hold it.

No test was removed, renamed, skipped, or weakened.

### Validation run

Ruff was scoped to this pass's own files, never `.`:

- `uv run ruff format <the 9 partition files + the temp test>` -> `1 file reformatted, 9 files left unchanged`. The one reformat is the gitignored temp test (`docs/builder/temp-tests/r2/test_repair6_order_independence.py`, an implicit string concatenation joined onto one line); **none of the nine partition files was reformatted**.
- `uv run ruff check --fix <the same files>` -> 8 errors, **all 8 in the gitignored temp test** (`ANN001`/`ANN201`/`ANN202` on a throwaway probe). Zero errors in the nine partition files. Consistent with the tree's existing state: `uv run ruff check docs/builder/temp-tests/` reports 24 errors across the three cohorts' probes, so r1b's and r1c's carry the same annotation noise. Flagged rather than annotated, so the temp directory stays uniform for `scripts/clean_up.py`.
- `uv run python scripts/check_trailing_commas.py --check <the nine partition files>` -> silent pass (ASCII-only held; every comment and docstring this pass wrote uses `-` and `->`, no em-dash and no arrow glyph).
- `git status --short` after both ruff invocations -> the nine partition files `M`; `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `M` (the concurrent Slice 2 pass); the cycle's `docs/builder/` artifacts and `docs/SPECS/appx/…-rationale.md` untracked; `0_0_14.md` untracked (baseline). **No unexpected modified file, and nothing was reverted.**

Focused runs, all without any `--cov*` flag:

- `uv run pytest tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov -q` -> **1005 passed**.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov -q` -> **224 passed**. (`test_keyset_connection.py` is included because it is one of the two files whose real importers the repair-3 comment now names.)
- `uv run pytest tests/ --no-cov -q` -> **5967 passed, 40 skipped**. Run as the `BUILD.md` `### Test staleness a focused run cannot see` sweep even though this pass changes no model field set and no wire shape: repair 7 executes a real prefetch against the library fixtures for the first time in that file.
- Repair 6's two-order check: alone -> 1 passed; with `::test_nested_pagination_variable_keys_cache` also selected -> 2 passed in both command-line orders. (pytest reorders node ids given on the command line, so CLI order does not actually control execution order here — the deterministic demonstration is the temp probe under `### Failability proofs`.)

### Failability proofs

Repairs 1-5 introduce no boundary and change no executable byte; their obligation is the **inverse** proof, recorded under `### Inverse proof` below. Repairs 6 and 7 change test behavior and owe the ordinary direction.

Emitted by `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2/proofs.json --output docs/builder/temp-tests/r2/proofs.md` (exit 0). Every field below is that run's, not prose.

- `django_strawberry_framework/optimizer/join_taxonomy.py::_partition_expr` — mutation applied: the function's `remote_field.attname or remote_field.name` body replaced by `return "pk"`, i.e. the partition derivation switched to the child pk; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/optimizer/test_walker.py -n 0`; pre-mutation state of that scope: green (`185 passed`, exit 0), 0 pre-existing failing rows differenced out; failing node ids: `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent[reverse_m2m]`, `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent[forward_m2m]`; collection/setup errors: **0**; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 12b1ede90d4b3b74... == 12b1ede90d4b3b74...` against the pre-mutation copy taken outside the repository.
- `django_strawberry_framework/optimizer/nested_fetch.py::attach_windowed_prefetch` — mutation applied: `partition_by=request.join.partition_expr` replaced by `partition_by=request.child_queryset.model._meta.pk.attname`, so the **executed** window partitions by the child pk while `optimizer/plans.py::window_partition_for_prefetch`'s derivation is left intact; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/optimizer/test_walker.py -n 0`; pre-mutation state of that scope: green (`185 passed`, exit 0), 0 pre-existing failing rows differenced out; failing node ids: `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent[reverse_m2m]`, `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent[forward_m2m]`; collection/setup errors: **0**; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 d6e349fcc8e17742... == d6e349fcc8e17742...`.

Neither entry is weakly pinned (2 rows each). Both sit inside Worker 3's mandatory independent re-run floor; re-run at the scope recorded above and compare node-id sets, not numbers.

**Counterfactual for repair 7, run as a separate manifest** (`docs/builder/temp-tests/r2/proofs-preedit-blindness.json`), because "the restored test catches it" is only half the finding. The same `attach_windowed_prefetch` mutation, with the restored test **deselected**: scope `uv run pytest --no-cov … tests/optimizer/test_walker.py --deselect tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent -n 0`; pre-mutation state: `183 passed, 2 deselected`, exit 0; failing node ids: **none**; collection/setup errors: 0; revert proved (`filecmp.cmp True`, sha256 equal). **why 0: this is a deliberate measurement of the pre-repair state, not a boundary proof** — it says that outside the restored test, no row in `tests/optimizer/test_walker.py` catches a child-pk partition in the executed window. That is exactly R1c's L2: the pre-edit body's only assertions were the two `window_partition_for_prefetch` equalities, which read the derivation shim and are untouched by a mutation at the fetch site.

**Repair 6, order-dependence demonstrated deterministically.** pytest reorders command-line node ids, so the poisoning order cannot be forced from the CLI (an attempt to do so through the proof harness returned 0 rows because pytest ran the two rows in the opposite order — recorded here so the next reader does not repeat it). The demonstration is instead a temp probe, `docs/builder/temp-tests/r2/test_repair6_order_independence.py`, which poisons the module-level `_doc_key_cache` in-process with the very document `::test_nested_pagination_variable_keys_cache` inserts, then runs the shipped test's **pre-edit** body and its **post-edit** body against that same state:

```
uv run pytest docs/builder/temp-tests/r2/test_repair6_order_independence.py --no-cov -q -n 0  ->  2 passed
  test_pre_edit_body_counter_reads_zero_under_a_poisoned_lru   -> the counter reads 0; the shipped
                                                                  pre-edit assertion was ``== 1``
  test_post_edit_body_counter_reads_one_under_the_same_poisoned_lru -> the counter reads 1
```

No production code was mutated for repair 6. No mutation is live in the tree: the scratch directory holds `pristine/` only, with neither `ACTIVE-MUTATION.json` nor `RESTORE-FAILED.json`, and both mutated production files read byte-identical to `HEAD` (`git diff --stat -- django_strawberry_framework/optimizer/nested_fetch.py django_strawberry_framework/optimizer/join_taxonomy.py` -> empty).

### Inverse proof (repairs 1-5: executable bytes unchanged)

Before-copies were taken to `<scratchpad>/before/` **outside the repository** ahead of every edit. No `git stash`, `git checkout`, `git restore` or `git worktree` was used at any point in this pass.

Instrument: parse before and after with `ast`, strip every module / class / function docstring, and compare `ast.dump(tree)` — which omits line numbers, so a pure reflow is invisible and a one-token executable change is not.

**Control, run first, both directions** (without it a blind instrument reads exactly like a passing proof):

```
dump("x = 1  # a") != dump("x = 2  # a")                     -> True   (executable change visible)
dump("x = 1  # a") == dump("x = 1  # b")                     -> True   (comment change invisible)
dump('def f():\n    """A."""\n    return 1\n')
  == dump('def f():\n    """B."""\n    return 1\n')          -> True   (docstring change invisible)
```

Result — all seven comment-only files, before-hash vs after-hash of the stripped dump:

| File | before | after | equal |
|---|---|---|---|
| `django_strawberry_framework/connection.py` | `ecc47449f5ec` | `ecc47449f5ec` | **True** |
| `django_strawberry_framework/optimizer/plans.py` | `8fb1b399480f` | `8fb1b399480f` | **True** |
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | **True** |
| `tests/test_connection.py` | `e10df5d5f0a3` | `e10df5d5f0a3` | **True** |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | **True** |
| `tests/optimizer/test_plans.py` | `809ebc71d3d8` | `809ebc71d3d8` | **True** |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | **True** |

**Confinement proof for the two files that do carry intended executable change.** Same instrument, applied per top-level node at a positional index (so a line shift cannot alias one node's key onto another's), with its own control asserted first:

```
tests/optimizer/test_walker.py:    211 -> 211 top-level nodes; differing: [(143, 'test_m2m_shared_child_partitions_per_parent')]
tests/optimizer/test_extension.py: 187 -> 187 top-level nodes; differing: [(93,  'test_cache_key_variable_name_collection_memoized_for_nested_fallbacks')]
```

Exactly one top-level node changed in each, and it is the intended one. Repair 2's two `test_walker.py` citation edits therefore changed no executable byte either.

*Instrument note, because it nearly went the other way:* a first draft of the confinement script returned `ast.walk()`'s last-yielded node instead of the node passed in, and reported "nothing changed" for both files — a clean-looking pass from an instrument that could not have failed. The control asserted above is what distinguishes the two, and is the reason it is recorded rather than merely run.

### Hot-path budget

The plan declares `connection.py`'s resolve path, `optimizer/walker.py`'s plan walk, and `optimizer/plans.py`'s window helpers **hot** — per request, per resolver, per parent row. Every edit this pass made to those three files is a comment or a docstring, so the honest number is a demonstrated **zero delta**, and the demonstration is the `### Inverse proof` table above rather than a timing run: the compiled structure of all three files is byte-for-byte the structure that was there before, so no instruction was added to any hot path and there is nothing a before/after measurement could resolve that the identity does not.

- metric: `ast.dump` of the docstring-stripped module, before vs after. Command: recorded verbatim in `### Inverse proof`. Iterations: one exact comparison per file, no statistic needed for an identity.
- before / after / delta: `ecc47449f5ec` / `ecc47449f5ec` / **0** (`connection.py`); `8fb1b399480f` / `8fb1b399480f` / **0** (`optimizer/plans.py`); `615fe2fe2be2` / `615fe2fe2be2` / **0** (`optimizer/walker.py`).

Repairs 6 and 7 are test-local: `tests/optimizer/test_extension.py` and `tests/optimizer/test_walker.py` are not runtime code and are not on any declared hot path. No production behavior changed anywhere in this pass.

### Floor verification

Not applicable; plan declares floor-verification scope `none` for this cohort, on the grounds that comment-only edits touch no Django / Strawberry / channels integration seam. That declaration survived the pass unchanged: repair 7's restoration is test-local and required **no** production change, so the plan-level drift condition the dispatch named ("if repair 7's restoration ends up requiring a production change, pause") was never reached. The shared `.venv` was not mutated and no version was stated from memory.

### Implementation notes

- **Repair 2 was judged per site, not blind-replaced.** Eight of the ten sites are sentences about plan-time and resolve-time order never disagreeing, and now cite **Decision 4** alone. The remaining two are sentences about *where the helper lives* — `connection.py #"now lives in ``optimizer/plans.py``"` and `optimizer/plans.py::ends_in_unique_column #"Hoisted from ``connection.py``"` — and legitimately keep Decision 11 for the module location while naming Decision 4 for the invariant they go on to describe. A third site, `optimizer/plans.py::effective_connection_order`, names both in one clause ("the cursor-parity invariant, spec-033 Decision 4 - this completes the Decision 11 hoist"), because that sentence genuinely asserts both facts. `connection.py::_finalize_queryset` also carries a **bare** "Decision 11" about the connection field's optimizer cooperation point; that one is correct as it stands, is not one of the ten, and was left alone.
- **Repair 3 narrowed rather than softened.** The corrected comments name the four names imported from `optimizer.walker`, the three consumed by the module's own bodies, and say plainly that the rest have no reader here — naming where the look-alike importers actually get them. No alias was deleted (escalated), and no name was renamed.
- **Repair 4 turned up a parallel site.** See `### Re-measured populations`. Fixing only the named one would have left a docstring three functions away asserting the retired per-parent fallback as the *contrast* that gives the other test its meaning, which is the shape that survives review precisely because each cohort's own list looks internally complete.
- **Repair 6's smallest order-independent fix would have weakened what it pins, so it was paired with a strengthening.** A fresh `_doc_key_cache` alone makes the first call a guaranteed miss and the count a real measurement — but `count == 1` is then satisfiable by *either* memo tier, and the docstring claims the per-execution `id(operation)` one specifically. Clearing the module LRU mid-lifecycle and calling once more isolates that tier: only the per-execution memo can answer the fourth call.
- **Repair 7 uses `first: 1`, not `first: 2`.** With two children per parent, `first: 2` admits every row under either partitioning and the mutation is invisible; `first: 1` is where a child-pk partition's second row number crosses the upper bound. The shared child is created before the unshared ones so the deterministic pk-terminal order puts it at row 1 of each partition, which is what makes the expected page a flat `[["shared"], ["shared"]]` rather than an order-sensitive set.
- **Repair 7 was parametrized to clear the weakly-pinned bar, not to pad the count.** The single-direction form measured **1** failing row against the partition mutation, which `BUILD.md` `### Acceptance rule` makes `revision-needed`; the second direction is a genuinely distinct derivation (the reverse query name versus the child's forward M2M field name) that the test's own two surviving equality assertions already assert, so exercising both is what the test's name always promised. Measured at **2** rows afterwards.

### Notes for Worker 3

- The diff to review is nine `.py` files. Seven of them are provably comment-only; the two that are not are confined to one top-level function each, and both instruments carry an asserted control (read the instrument note in `### Inverse proof` before trusting either result — the first draft of one of them was blind).
- The failability manifests are `docs/builder/temp-tests/r2/proofs.json` (the two-entry record), `…/proofs-preedit-blindness.json` (the deselect counterfactual) and `…/proofs-order-independence.json` (the CLI-ordering attempt that returned 0 rows for the reason explained above — it is **not** a boundary proof and should not be read as one). `scripts/prove_failability.py` re-runs any of them.
- The temp probe `docs/builder/temp-tests/r2/test_repair6_order_independence.py` carries 8 ruff `ANN` errors, matching the existing state of r1b's and r1c's probes (24 across the directory). Gitignored; not promoted; deliberately left uniform with its siblings.
- No shadow file was generated or read in this pass; `scripts/review_inspect.py` was not run (no new symbol, no new control flow, and every source citation here is to an original file line).

### Notes for Worker 1 (spec reconciliation)

Each amendment carries its section heading, the current wording quoted, and the recommended replacement. Line numbers are omitted deliberately: Slice 2 is editing this file concurrently.

1. **A second live-suite docstring stated the retired ambiguous-empty fallback, and it is the one that gives R1c's M3 site its contrast.** Section: `examples/fakeshop/test_query/test_library_api.py::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` (a `.py` site, already fixed in this pass — recorded here because R1c's `### Notes for Worker 1` item 3 counted "one stale test docstring" and there were two, so any spec sentence written against that census is one site short).
   - Current wording (before this pass): "The contrast with ``test_nested_connection_first_zero_empty_page_live``: that is the AMBIGUOUS empty window (``first: 0``, ``limit == 0``) which falls back per parent".
   - Landed replacement: "... that is the AMBIGUOUS empty window (``first: 0``, ``limit == 0``), served from the partition's retained marker row; this is the UNAMBIGUOUS empty window ... where the parent has no marker row to retain, so an empty ``to_attr`` list is itself conclusive".
   - No spec edit is required by this item; it is a correction to the **population** R1c reported, so that Slice 2's `**Post-ship:**` record for `57cbd32a` names the right number of `.py` homes if it names one at all.

2. **Repair 5's products half needed no `.py` edit, so the spec's Slice-6 sentence is the only surviving half of L7/L8.** Section: `## Test plan` Slice 6, `#"New: one nested relation-connection shape on the products graph"`.
   - Current wording: names no test for the products nested-connection pin.
   - Recommended replacement: name it — `examples/fakeshop/test_query/test_products_api.py::test_products_categories_items_connection_fixed_query_count` — and, if the axis is worth stating, say "at two seedings that hold the parent-category count fixed and grow items-per-category", which is what the shipped test's own docstring already says. The three products docstrings L7 and L8 flagged were re-read this pass and **make no false claim**: the two depth-2 pins scope "fixed 3" to the cascade adding zero round-trips, not to parent cardinality, and the connection pin already names its axis correctly. Recommend R1c's L7/L8 be recorded as "no `.py` defect; the spec sentence is the item".

3. **The two spec-named single-cardinality pins now say so in their own prose, which makes the spec's `## Test plan` sentences for them checkable.** Section: `## Test plan` Slice 2 (`test_fast_path_single_query`) and Slice 5 (`test_nested_window_respects_book_visibility`).
   - Current wording: describes each as pinning the fixed cost without saying at how many cardinalities.
   - Recommended replacement: state the shape the tests actually hold — "an absolute query count at one parent cardinality, with the two-cardinality form earned live by `test_nested_books_connection_fixed_query_count`". **Not** a recommendation to add cardinalities: both pins carry an absolute count derived from a real run, so neither is vacuous, and `BUILD.md` `### Query-shape tests must pin the load-bearing property` is satisfied by the family. If the maintainer nonetheless wants each pin non-vacuous standing alone, that is a scope decision, not this cohort's — flagged, not taken.

4. **`test_m2m_shared_child_partitions_per_parent` is now parametrized over both M2M directions**, so the spec's Slice-1 sentence (`#"two parents share one child and still receive independent per-parent pages, catching accidental child-pk partitioning"`) is true again — and slightly understates what the test holds.
   - Recommended replacement: "two parents share one child and still receive independent per-parent pages, in **both** M2M directions (the reverse `Genre.books` partitioning through the child's forward M2M field name, and the forward `Book.genres` through the target's reverse query name), catching accidental child-pk partitioning."
   - Worth knowing for the reconciliation: the contract is pinned **only** by that test. With it deselected, none of the other 183 rows in `tests/optimizer/test_walker.py` fails when the executed window's partition is switched to the child pk (measured; see `### Failability proofs`).

5. **`optimizer/plans.py::window_partition_for_prefetch` is measurably not the site the contract runs through.** Section: whichever Decision the reconciliation ends up siting the partition derivation on.
   - Evidence this pass adds to the standing escalation: mutating `join_taxonomy.py::_partition_expr` (which both the shim and production read) and mutating `nested_fetch.py::attach_windowed_prefetch`'s `partition_by=` (which only production reads) fail the **same two rows** — the restored test's, both times. The shim's own six-row `TestWindowPartitionForPrefetch` family in `tests/optimizer/test_plans.py` did not fail under either. That is the escalation's "zero production callers" claim measured from the other side, and it is offered as input to the maintainer decision, not as a repair.

6. **Decision 11 keeps two citations in source, deliberately.** Section: `### Decision 11 — Module and test-file locations`.
   - The eight invariant citations moved to Decision 4 as pinned. The two that remain (`connection.py`'s re-export comment and `optimizer/plans.py::ends_in_unique_column`'s docstring) cite Decision 11 for the hoist's **module location** and Decision 4 for the invariant, in the same sentence. If Slice 2 rewrites Decision 11's module map, those two source comments are the sites that will need to stay in agreement with it.

---

## Review (Worker 3)

### Mutations pre-registered before they were made

`worker-3.md` requires the source carve-out's mutations recorded here **before** the tree is touched. Both are transient, one at a time, reverted inside this pass with the revert proved by byte comparison; the loop is run through `scripts/prove_failability.py`, which enforces the anchor-check-then-copy order.

1. `django_strawberry_framework/optimizer/nested_fetch.py::attach_windowed_prefetch` — the single anchor line `#"partition_by=request.join.partition_expr,"` replaced by `partition_by=request.child_queryset.model._meta.pk.attname,`, so the **executed** window partitions by the child pk while `optimizer/plans.py::window_partition_for_prefetch`'s derivation shim is left intact. Scope as run: `tests/optimizer/test_walker.py -n 0` (Worker 2's recorded scope).
2. `django_strawberry_framework/optimizer/join_taxonomy.py::_partition_expr` — the `remote_field.attname or remote_field.name` body replaced by `return "pk"`. Same scope.
3. `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` — the anchor `#"parts = memo.get(id(operation)) if memo is not None else None"` replaced by `parts = None`, which deletes the **per-execution `id(operation)` memo tier** while leaving the cross-request `_doc_key_cache` LRU intact. This mutation is Worker 3's own: Worker 2 recorded no proof that repair 6's strengthening isolates that tier, and reading alone cannot settle it. Scope: `tests/optimizer/test_extension.py -n 0`.

All three are reverted. Post-pass byte comparison against `HEAD` (the read-only reference `BUILD.md` `## Claims are proven mechanically` allows for a boundary already present at `HEAD`): `git show HEAD:<path> | cmp -` returns exit 0 for `optimizer/nested_fetch.py`, `optimizer/join_taxonomy.py` and `optimizer/extension.py`. `scripts/prove_failability.py`'s own restore proof (`filecmp.cmp(shallow=False)` + sha256 against the pre-mutation copy taken outside the repository) passed on every entry, and no `ACTIVE-MUTATION.json` / `RESTORE-FAILED.json` marker exists anywhere in the tree. **No mutation is live.**

### Independent re-runs, and where the second pair of eyes landed

Re-run at Worker 2's recorded scope, compared as node-id **sets**.

| Boundary | W2 rows | W3 rows | Node-id sets equal | Baseline of the same scope |
|---|---|---|---|---|
| `optimizer/nested_fetch.py::attach_windowed_prefetch` | 2 | **2** | **yes** | `185 passed`, exit 0, 0 differenced out |
| `optimizer/join_taxonomy.py::_partition_expr` | 2 | **2** | **yes** | `185 passed`, exit 0, 0 differenced out |
| `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` (W3's own) | not run | **1** | n/a | `166 passed`, exit 0, 0 differenced out |

Node ids, both partition mutations, identical set both times:

- `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent[reverse_m2m]`
- `tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent[forward_m2m]`

Collection/setup errors: **0** on every run. Reports: `docs/builder/temp-tests/r2-review/w3-proofs.md`, `…/w3-proofs-repair6.md`.

**Both of Worker 2's recorded boundaries sat inside the mandatory floor (<= 3 rows) and both were re-run; nothing was accepted on Worker 2's record alone.** The third entry is Worker 3's own addition, not a re-run.

### The inverse proof survives an independent instrument

Written from scratch (`ast` parse -> strip every module / class / function docstring -> `ast.dump`, which omits line numbers), with the control **asserted** before any measurement, in five directions rather than three: an executable change is visible, an added statement is visible, an inverted guard is visible, a comment change is invisible, a docstring change is invisible. The instrument then had to report `DIFFER` for the two files known to change executably, and did — so it can fail.

Docstring-stripped `ast.dump` hash, `HEAD` copy vs working tree, all seven comment-only files:

| File | before | after | equal |
|---|---|---|---|
| `django_strawberry_framework/connection.py` | `ecc47449f5ec` | `ecc47449f5ec` | **yes** |
| `django_strawberry_framework/optimizer/plans.py` | `8fb1b399480f` | `8fb1b399480f` | **yes** |
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | **yes** |
| `tests/test_connection.py` | `e10df5d5f0a3` | `e10df5d5f0a3` | **yes** |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | **yes** |
| `tests/optimizer/test_plans.py` | `809ebc71d3d8` | `809ebc71d3d8` | **yes** |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | **yes** |

Every hash reproduces Worker 2's recorded value digit for digit. **Repairs 1-5 changed no executable byte**, and by the same identity no alias, assertion, or import was deleted anywhere in those seven files.

Confinement, per top-level node at a positional index, with its own control asserted (the instrument must report a difference for a deliberately altered copy of the same file, and did):

- `tests/optimizer/test_walker.py` — 210 -> 210 top-level nodes; differing: `[(142, 'test_m2m_shared_child_partitions_per_parent')]`
- `tests/optimizer/test_extension.py` — 186 -> 186 top-level nodes; differing: `[(92, 'test_cache_key_variable_name_collection_memoized_for_nested_fallbacks')]`

Exactly one top-level node differs in each, and it is the intended one. The node counts and indices sit one below Worker 2's (`211`/`187`, `143`/`93`) because this instrument strips the module docstring out of `body` and Worker 2's did not — a constant offset, not a disagreement. Repair 2's two `test_walker.py` citation edits therefore changed no executable byte either.

### Verdict per repair

1. **Staged `TODO` anchor — verified.** `grep -rno 'TODO(spec-033' --include='*.py'` counts **1** at `HEAD` (`tests/test_connection.py`, the fence marker) and **0** in the working tree. The replacement carries no `TODO(`. The five `TODO(` occurrences that remain across the nine files all name **`spec-035`**, an unrelated in-flight spec, and are byte-unchanged from `HEAD`.
2. **Ten `Decision 11` citations — verified, site by site, and the population re-derived.** Whitespace-normalized (`re.sub(r"\s+", " ", source)`) sweep over all 468 tracked `.py` files: `spec-033 Decision 11` **10 -> 2**, `spec-033 Decision 4` **22 -> 30**. Distribution at `HEAD` confirms the dispatch exactly — `connection.py` x2, `optimizer/plans.py` x4, `tests/optimizer/test_plans.py` x2, `tests/optimizer/test_walker.py` x2. The 8 that lost Decision 11 gained `spec-033 Decision 4`; the 2 that kept it gained a bare `Decision 4` in the same sentence, which is why the Decision 4 delta is +8 and not +10. **No new wrapped citation:** the single-line grep and the normalized sweep now agree on both tokens (2 and 30), which they did not at `HEAD` (9 vs 10). I read all ten sentences against the spec: `### Decision 4` states the invariant in its own words (`#"Deterministic order (a cursor-parity invariant, not a tidiness refactor)"`, including `#"This invariant is named here (not buried in the module-location decision)"`), and `### Decision 11` is the module map. Eight sentences assert only the invariant and correctly cite Decision 4 alone; `connection.py #"now lives in ``optimizer/plans.py``"` and `optimizer/plans.py::ends_in_unique_column #"Hoisted from ``connection.py``"` assert both and correctly cite both; `optimizer/plans.py::effective_connection_order` names both because its clause asserts both. The four remaining bare `Decision 11` occurrences in the nine files are **not** cursor-parity sentences and were correctly left alone: `connection.py::_finalize_queryset` step 6 (the connection field's optimizer cooperation point), `tests/optimizer/test_extension.py` x2 (the `apply_to` extraction and the plan-cache-reuse route), and `tests/test_relay_connection.py`'s module docstring (which cites **spec-032**, a different spec).
3. **Walker alias comment — verified by my own measurement, not Worker 2's.** An AST pass over `walker.py` enumerated **17** module-level underscore aliases, then measured each one's `ast.Name` LOAD sites inside `walker.py` (excluding its own assignment target) and every `from …walker import` / `walker.<name>` across all 468 `.py` files. Result: **10 dead**, and the dead set is character-for-character the set the rewritten comment names. Live-via-importer (4): `_should_include`, `_is_fragment`, `_concrete_order_columns`, `_relay_max_results_from_info` — every one of them imported by `tests/optimizer/test_walker.py`, as the comment says. Live-via-own-body (4): `_is_fragment`, `_response_key`, `_response_keys`, `_included_field_selections` — as the comment says. The look-alike claims check out too: `tests/optimizer/test_extension.py` imports `_named_children` / `_node_children_with_runtime_prefix` from `optimizer.extension`, which carries its own alias pair; `connection.py` and `tests/test_keyset_connection.py` import the four `_relation_connection_to_attr` / `_extend_only_projection` / `_keyset_window_slice_from_arguments` / `_relation_connection_to_attr_for_key` names from `optimizer/nested_planner.py` directly. **No alias was deleted** — the `ast.dump` identity for `walker.py` proves it, which is a stronger statement than a diff read. The "no reader" wording is the right one: three of the ten dead names are mentioned in `walker.py` docstrings, so "no occurrence" would have been false.
4. **Four stale docstrings — verified true after repair, and my own sweep found no fifth.** The production mechanism the repaired text now describes is real: `utils/connections.py::is_ambiguous_empty_window` + `window_range_plan #"add_marker_rows"` plan the marker, `connection.py #"marker rows directly serve ``first: 0``, overshot offset ``after:``"` consumes it. `tests/test_relay_connection.py::test_fallback_when_annotations_missing` — verified against `connection.py::_window_rows_are_annotated`, which probes `WINDOW_ROW_NUMBER` only and explicitly does not probe `_dst_total_count`; the new docstring is accurate. `::test_strictness_silent_when_off` and `::test_strictness_silent_no_optimizer` — verified against `types/resolvers.py::_check_n1`, whose prelude reads strictness **first** (`#"Strictness gates everything below, so read it FIRST"`) and returns before the `DST_OPTIMIZER_PLANNED` read and before any `to_attr` probe, and against `optimizer/extension.py #"strictness_token = _begin_strictness(self.strictness)"` at `on_execute` entry, which is unconditional and therefore arms `"off"` too. The old docstrings named the wrong mechanism; the new ones name the live one. My independent sweep for a fifth site: every `.py` line in the tree matching `ambiguous|first: ?0|overshot|overshoot|limit == 0` whose +/-4-line window also matches fall-back vocabulary, then every `ambiguous` occurrence in the ten connection-domain test files read by hand. **No fifth stale site.** Every cross-referenced test name in the new text resolves on disk (`::test_nested_ambiguous_empty_served_from_marker_in_fixed_queries`, `::test_genre_connection_first_zero_empty_edges`, `::test_nested_books_connection_fixed_query_count`, `::test_synthesized_connection_per_parent_query_cost`).
5. **Two corrected, three correctly left alone — Worker 2's re-measurement is right, but the population is not.** `tests/test_relay_connection.py::test_fast_path_single_query` runs 4 genres under `django_assert_num_queries(2)` at one cardinality: the old "independent of parent count" did overclaim and the new absolute-count wording is accurate. `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility` runs 2 genres under `len(captured) == 2` at one cardinality: same, and both inline comments were corrected with the docstring. `examples/fakeshop/test_query/test_products_api.py` is **byte-identical to `HEAD`** (`git show HEAD:… | cmp -`, exit 0) — the do-not-touch fence held, and I confirmed by reading that none of its three named docstrings claims parent-count independence. But see **Low 1**: the same claim survives at four further sites inside R2's own writable files.
6. **Order-independence and the strengthening — both verified, the second one by a mutation Worker 2 never ran.** Worker 2's substitution of an in-process probe for the failability harness is **sound**, and I confirmed its premise rather than taking it: running the two node ids in both command-line orders shows pytest executing them in file-definition order both times, so the poisoning order genuinely cannot be forced from the CLI. That leaves the strengthening's claim untested, so I mutated the production tier out (`parts = None`, killing the per-execution `id(operation)` memo while leaving the `_doc_key_cache` LRU intact) and ran it against **both** bodies in one scope: the shipped post-edit row **FAILED**; a verbatim copy of the `HEAD` pre-edit body, added as a temp row, **PASSED**. That is the strengthening measured rather than argued — the pre-edit `== 1` was satisfiable by the document LRU alone, and the post-edit one is not. It also proves the test pins memoization rather than "ran at most once": the fresh `_doc_key_cache` makes the first call a guaranteed miss, so `== 1` fails at 0 as well as at 2. The 1-row count on that mutation is **not** the weakly-pinned acceptance rule biting — the memo tier is shipped production code, not a boundary this diff introduces — but it is worth Worker 1 knowing that this one row is the whole of its pinning (see `### Notes for Worker 1`).
7. **Restored scenario — verified, strictly stronger, not weakly pinned.** Both pre-existing `window_partition_for_prefetch` equality assertions survive verbatim (`Genre._meta.get_field("books") == "genres"`, `Book._meta.get_field("genres") == "books"`); the new body adds a `to_attr` assertion and an executed-prefetch page assertion on top. Nothing was weakened anywhere in the diff — the confinement proof bounds the change to this one function, and inside it the assertion set only grows. The parametrization is not padding: the two directions derive the partition from opposite sides of the same relation, which the two surviving equalities already assert separately. My re-run measures **2** rows against both mutations, clearing the weakly-pinned bar at the recorded scope.

### High:

None.

### Medium:

None.

### Low:

#### Low 1 — repair 5's parallel-site population was never swept, and four sites in R2's own files still make the corrected claim

Worker 2 swept for repair 4's parallel sites and found one; it did not run the equivalent sweep for repair 5, and reported repair 5's population as the five sites the cohorts named. A tree-wide sweep of `.py` for `independent of (the )?(parent|N|row) ?count | parent-count-independent | regardless of parent | independent of the number of parent` finds the claim alive at four further sites, all inside R2's declared writable partition, each running a **single** parent cardinality:

- `tests/test_relay_connection.py::test_divergent_aliases_one_window_query_per_alias #"independent of parent count, and each alias serves ITS OWN page bound"` (`tests/test_relay_connection.py:1194`) — 4 genres, `django_assert_num_queries(3)`. This one sits ~50 lines below `::test_fast_path_single_query`, which repair 5 corrected, and makes the identical claim in the identical grammar.
- `examples/fakeshop/test_query/test_library_api.py::test_genre_books_connection_probe_childless_and_populated_parents #"in the fixed two-query cost regardless of parent count"` (`examples/fakeshop/test_query/test_library_api.py:4287`) — 2 genres.
- `examples/fakeshop/test_query/test_library_api.py::test_genre_books_connection_divergent_aliases_batched_per_key #"one window per alias - independent of parent count"` (`examples/fakeshop/test_query/test_library_api.py:4452`) — 2 genres, `len(captured) == 3`.
- `examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_has_next_page_without_edges #"``booksConnection`` prefetch), independent of parent count"` (`examples/fakeshop/test_query/test_library_api.py:5349`) — 3 genres, `len(captured) == 2`.

Two further sites carry the same phrase and are **correct** — do not touch them: `::test_nested_books_connection_fixed_query_count` (3 and 10 genres) and `::test_list_relation_and_connection_sibling_coexist_live` (2 and 4 genres) genuinely run two cardinalities and earn it.

Why it matters: this is the exact shape the cohorts graded as L7 and Worker 2 accepted as a defect at two sites. Fixing two of six occurrences of one claim and leaving four leaves the file internally inconsistent — a later reader finds the corrected and the uncorrected wording side by side and cannot tell which is the convention. No statement here is false *about the package* (the property is real and is earned by the two-cardinality pins), which is why this is Low and not Medium.

Recommended change: apply repair 5's own correction shape to the four — name the absolute count and the seeded cardinality, and, where useful, point at the two-cardinality pin that earns the general property — **or** record an explicit deferral naming these four so Worker 1 can weigh it at final verification. Either resolution closes the finding. No test expectation changes; these are docstring and comment edits with no executable byte.

#### Low 2 — `optimizer/walker.py`'s rewritten alias comment states how the change came to be

`django_strawberry_framework/optimizer/walker.py #"Readers of the underscore aliases below, measured rather than assumed"` (`django_strawberry_framework/optimizer/walker.py:50`). "measured rather than assumed" says nothing about the code; it says something about how this comment was authored, and it only parses at all against the prior comment's wrongness, which a reader of the shipped package cannot see. `AGENTS.md`'s standing rule is that a comment states the technical invariant and nothing about how the change came to be. The rest of the same comment is exactly right — it names the readers, which is the invariant.

Recommended change: delete the three words. `# fragment/directive/response-key implementation. Readers of the underscore aliases` … reads correctly without them. Comment-only; the `ast.dump` identity must still hold afterwards.

### DRY findings

None introduced. The three production files' repeated-string-literal sections are recorded below for the integration pass's cross-cohort comparison; all of them are pre-existing, since the diff proves those files' compiled structure unchanged.

- `django_strawberry_framework/optimizer/walker.py` — 3x `prefetch`, 3x `connection`, 3x `arguments`, 2x `operation`, 2x `_optimizer_runtime_prefixes`, 2x `prefetch_through`, 2x `selections`.
- `django_strawberry_framework/optimizer/plans.py` — 2x `prefetch_to`, 2x `queryset`, 2x `descending`, 2x `nulls_first`, 2x `nulls_last`.
- `django_strawberry_framework/connection.py` — 3x `total_count`, 2x `_dst_node_type`, 2x `is_relation`.

The two standing existence challenges in this area (`optimizer/plans.py::window_partition_for_prefetch`'s zero production callers, and the ten dead walker aliases) are already on `build-033-connection_optimizer-0_0_9.md` `## Escalations` as maintainer decisions. R2 acted on neither, which is correct. Worker 3 adds one measurement to the first of them under `### Notes for Worker 1`; it is not re-raised as a new finding.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty and the file is not in `git status --porcelain`. `__all__` and the re-export list are unchanged. No new public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The two `docs/SPECS/` files dirty in the tree belong to the concurrent Slice 2 pass and were neither read as R2's output nor touched.

### Static helper use

Run on all three production files R2 touched, every invocation with `--output-dir docs/shadow`, no skips:

- `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow`
- `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/plans.py --output-dir docs/shadow`
- `uv run python scripts/review_inspect.py django_strawberry_framework/connection.py --output-dir docs/shadow`

Sections walked, per `BUILD.md`: Django / ORM markers, repeated string literals (recorded under `### DRY findings`), control-flow hotspots, imports. Nothing in the diff adds a symbol, an import, or a branch to any of the three — the `ast.dump` identity is the formal statement of that, and the helper's own counts agree (`walker.py` 24 imports / 37 symbols / 8 hotspots; `plans.py` 11 / 46 / 9; `connection.py` 33 / 50 / 15). `walker.py`'s "TODO comments: 2" are the two `spec-035` anchors, unchanged. The hotspots worth carrying forward are pre-existing and belong to no finding here: `connection.py::_resolve_from_window` at 323 lines / 26 branch nodes, `optimizer/plans.py::apply_window_pagination` at 202 / 14, `optimizer/walker.py::_walk_selections` at 212 / 20. Shadow-file line numbers are not cited anywhere in this review; every citation above is an original-source line beside its symbol.

### Hot-path budget verification

The plan declares `connection.py`'s resolve path, `optimizer/walker.py`'s plan walk and `optimizer/plans.py`'s window helpers hot. The build report **carries** a number for all three, and it is **reproducible as recorded**: my independent instrument returns the same before/after hashes (`ecc47449f5ec`, `8fb1b399480f`, `615fe2fe2be2`) and therefore the same zero delta. `BUILD.md` makes existence-and-reproducibility the obligation and leaves the size to the maintainer; there is nothing to leave, because a docstring-stripped AST identity means no instruction was added to any hot path. Repairs 6 and 7 are test-local and touch no declared hot path.

### Floor verification

Plan-declared scope `none`, and the diff does not falsify it. Checked against the actual diff, not the plan's prose: the three production files' compiled structure is byte-identical, so no Django / Strawberry / channels integration seam moved; repairs 6 and 7 are test-local and required no production change, so the dispatch's drift condition ("if repair 7's restoration ends up requiring a production change, pause") was never reached. The shared `.venv` was not mutated by this review — `uv pip install` was never invoked; the failability harness only rewrites source files in place and restores them. For the record, and read rather than remembered: `uv pip list` in `.venv` reports `django 6.1`, `strawberry-graphql 0.324.0`, `channels 4.3.2`, `pytest 9.0.3` — which is **not** the supported floor (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0), as expected, and is the reason a `none` scope is a declaration and not a measurement.

### What looks solid

- The seven-file inverse proof is the strongest artifact in this cohort, and it survives an instrument built without sight of Worker 2's. Its recorded instrument note — the first confinement script returned `ast.walk()`'s last node and reported "nothing changed" for two files it had just rewritten — is the reason the record is trustworthy: a pass that names its own near-miss is a pass that ran a control.
- Repair 2 was judged per site. A blind replace would have broken two sentences that legitimately assert the module location, and a blind acceptance would have missed that the spec text explicitly refuses to bury the invariant in Decision 11. Both readings survive independent checking.
- Repair 3's comment is now true in a way that is mechanically checkable, and the wording choice ("no reader" over "no occurrence") is exactly right for the three dead names that appear in docstrings. Every claim in it reproduces from an AST pass.
- Repair 7 restores a test whose name had outlived its body, and the counterfactual is the part that makes it worth having: with that test deselected nothing in the remaining 183 rows notices a child-pk partition in the executed window.
- Repair 6's strengthening turns out to be more valuable than its own artifact claims. It is the only row anywhere in `tests/optimizer/test_extension.py` that pins the per-execution memo tier at all; before this pass, deleting that tier failed nothing.
- Gates: `uv run ruff check` and `ruff format --check` clean on all nine files, `scripts/check_trailing_commas.py --check` silent (ASCII held; `grep -P '[^\x00-\x7F]'` returns 0 on every one of the nine). No raw `path:NN` reference appears on any added source line.
- All three of Worker 2's recorded suite runs reproduce exactly: `tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov` -> **1005 passed**; `examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov` -> **224 passed**; `tests/ --no-cov` -> **5967 passed, 40 skipped**. No `--cov*` flag was used at any point in this review.
- Partition discipline held. `git status --porcelain` shows exactly the nine R2 files plus the two Slice 2 spec files; `examples/fakeshop/test_query/test_products_api.py` is byte-identical to `HEAD`; nothing was reverted; `0_0_14.md` and `docs/builder/bld-003-final.md` were not touched.
- On the one thing that looked like a rule breach and is not: `tests/test_connection.py #"spec-033 Slices 1-2 (DONE-033-0.0.9)"` introduces a kanban card id into source. I measured the anchor rather than the distance before flagging it — `DONE|TODO|BETA|WIP-NNN-x.y.z` occurs **46** times across 12 `.py` files at `HEAD`, including two spellings of `DONE-033-0.0.9` in this very card's own source (`django_strawberry_framework/connection.py`, `django_strawberry_framework/types/finalizer.py`). It is a live convention, not a novelty, and this is its 47th occurrence.

### Temp test verification

- `docs/builder/temp-tests/r2-review/test_repair6_preedit_counterfactual.py` — the `HEAD` pre-edit body of repair 6's test, run as a second row under the live memo mutation so the "satisfiable by either tier" claim is measured in the same process as the post-edit row. Disposition: **not promoted.** It is a snapshot of code the repair deliberately replaced; keeping it permanently would pin the weaker assertion the repair exists to remove. It caught no bug — it confirmed the repair.
- `docs/builder/temp-tests/r2-review/w3-proofs.json`, `…/w3-proofs-repair6.json`, `…/w3-proofs-repair6b.json` and the emitted `…/w3-proofs.md`, `…/w3-proofs-repair6.md` — this review's own failability manifests and reports. Gitignored; cleared per cycle by `scripts/clean_up.py`.

### Notes for Worker 1 (spec reconciliation)

1. **The per-execution cache-key memo is pinned by exactly one row, and only since this pass.** Measured: mutating `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`'s `#"parts = memo.get(id(operation)) if memo is not None else None"` to `parts = None` fails `tests/optimizer/test_extension.py::test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` and nothing else in that file's 166 rows; the `HEAD` body of that same test passes under the mutation. Decision 7's per-execution memo is therefore a real contract with a one-row guard. Not a defect in this diff — repair 6 is what created the guard — but a spec reconciliation that states Decision 7's two-tier caching should know that the tiers are pinned very unequally.
2. **`Escalated:` the `window_partition_for_prefetch` existence challenge, with one more measurement.** Both partition mutations — `join_taxonomy.py::_partition_expr` (read by the shim and by production) and `nested_fetch.py::attach_windowed_prefetch`'s `partition_by=` (read only by production) — fail the **same two rows**, the restored test's, and neither fails any row of the six-row `TestWindowPartitionForPrefetch` family in `tests/optimizer/test_plans.py`. Independently reproduced this pass. Resolution paths are unchanged and are the maintainer's: keep the shim and site the derivation on it in the spec, or delete it and site the derivation on `join_taxonomy.py::classify_relation_join`. Worker 3 does not hold this cohort at `revision-needed` on it.
3. **Repair 5's population is larger than any cohort reported** — see Low 1. R1c's L7/L8 named five sites; the claim's actual `.py` population is ten occurrences, six of which sit at one cardinality and four of which are still uncorrected. If Slice 2 writes a `## Test plan` sentence against the cohort census, that census is four sites short.
4. Worker 2's own six notes for Worker 1 were read and are not restated here; nothing in them is contradicted by this review.

### Review outcome

`revision-needed`.

Everything load-bearing in this cohort is verified and **is not to be re-litigated on the re-pass**: the inverse proof reproduces under an independent instrument, all ten citations are correctly re-sited, the walker comment is true by my own measurement, the four repaired docstrings are true and there is no fifth, both partition boundaries re-run to identical node-id sets at 2 rows, no mutation is live, no assertion was weakened, no file was written outside the partition, and repair 6's strengthening is real — proved by a mutation Worker 2 did not run.

The two open items are both one-line comment edits inside R2's existing partition, and neither touches an executable byte:

1. **Low 1** — apply repair 5's own correction shape to the four unswept sites named above (`tests/test_relay_connection.py::test_divergent_aliases_one_window_query_per_alias`, `examples/fakeshop/test_query/test_library_api.py::test_genre_books_connection_probe_childless_and_populated_parents`, `::test_genre_books_connection_divergent_aliases_batched_per_key`, `::test_nested_books_connection_has_next_page_without_edges`), leaving the two genuinely two-cardinality sites alone — **or** record an explicit deferral naming all four so Worker 1 owns it at final verification. Either closes it.
2. **Low 2** — delete "measured rather than assumed" from `django_strawberry_framework/optimizer/walker.py #"Readers of the underscore aliases below"`.

Re-run the seven-file `ast.dump` identity afterwards; both edits must leave it unchanged.

---

## Build report (Worker 2, pass 2)

Closes the two Low findings Worker 3 left open, plus one finding Worker 0 added mid-flight. The seven repairs of pass 1 are verified and were not re-opened: nothing in this pass's diff touches any of them, and the three files pass 1 proved comment-only carry byte-identical `ast.dump` digests here (`### Inverse proof`, below).

### Worker-0 mid-flight instruction (recorded per `worker-0.md` `### Mid-flight instructions are mirrored into the artifact`)

Worker 0 sent a scope addition after this pass started, and it is recorded here because a contract that lives only in the dispatch transcript leaves the artifact describing work that was not built:

- **Added to the writable list:** `django_strawberry_framework/optimizer/nested_fetch.py`.
- **Added finding, Low 3:** three comments in that file cite a `### Decision 6` structure the spec no longer has. A Worker 1 reconciliation pass rewrote Decision 6 from four numbered fallback shapes into nine refusal arms with no ordinals and renamed the heading while this cohort's first pass was running, so the rot is this cycle's own. One of the three cites `shape 4`, an ordinal that no longer exists.
- **Everything else unchanged:** same comment-only proof obligation (the docstring-stripped AST identity must hold for `nested_fetch.py` too, from an instrument shown capable of failing), same ASCII / ruff / trailing-comma gates, same ban on writing a review-round or finding id into source. `nested_fetch.py` is hot-path, so its zero-delta identity is also its hot-path record.

The current `### Decision 6` was read directly from `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` before any wording was written; nothing below is taken from the instruction's paraphrase, from pass 1's text, or from memory.

### Files touched

Grounded in `git status --short` after both ruff invocations. Four `.py` files, all inside the declared R2 partition as extended by the mid-flight instruction:

- `tests/test_relay_connection.py` - Low 1, one docstring.
- `examples/fakeshop/test_query/test_library_api.py` - Low 1, three docstrings.
- `django_strawberry_framework/optimizer/walker.py` - Low 2, one comment block (three words deleted, block reflowed).
- `django_strawberry_framework/optimizer/nested_fetch.py` - Low 3, two docstrings (three citation sites).

Also written, inside the partition: `docs/builder/bld-033-review-2-py_comment_repair.md` (this section, plus `Status:` and three checklist boxes) and `docs/builder/worker-memory/worker-2.md` (appended). No temp test was needed; `docs/builder/temp-tests/r2b/` was never created, because this pass adds no boundary and its whole proof is an identity over files copied outside the repository.

`examples/fakeshop/test_query/test_products_api.py` was not written and does not appear in `git status --short`. The six other `.py` files pass 1 touched were not written either.

### Re-measured populations

Both counts below were re-derived in this pass with a whitespace-normalized, occurrence-counting instrument (`re.sub(r"\s+", " ", source)` per file, then `re.findall`), never a single-line `grep` - a claim wrapped across two lines is invisible to a line-oriented sweep, and an occurrence count is not a matching-line count.

**Low 1 - six occurrences before, two after, and the two survivors are the two that earn the claim.** The sweep ran over every `.py` in the tree except `.venv/`, `__pycache__/` and `docs/shadow/`, with Worker 3's pattern widened by seven further spellings so a differently-worded variant could not hide from a phrase grep:

```
independent of (the )?(parent|N|row) ?count | parent-count-independent
| parent count independent | regardless of (the )?parent
| independent of (the )?number of parent | irrespective of (the )?parent
| no matter (how many|the number of) parent | does not (scale|grow) with (the )?parent
| independent of how many parent | per-parent[- ]count[- ]independent
| constant in (the )?parent count | flat in (the )?parent count      (case-insensitive)
```

Before: **6 occurrences in 2 files** - `examples/fakeshop/test_query/test_library_api.py` 5, `tests/test_relay_connection.py` 1. That is exactly the four uncorrected sites plus the two correct ones; pass 1's own two corrections no longer match, which is why the tree-wide number is 6 and not the 10 Worker 3 measured against the pre-pass-1 text. After: **2 occurrences**, both in `test_library_api.py`, both at the two-cardinality pins.

A second, independent widening cross-checked the phrase grep from the other direction: every `.py` occurrence of the bare word `independent`, and separately of `regardless of` / `no matter how many` / `irrespective of` / `does not grow with`, read by hand for a parent-cardinality claim. It surfaced exactly one further candidate and it is **not** the same shape - `django_strawberry_framework/optimizer/plans.py #"regardless of N - so it is set generously (1024)"` is about a linked-list cycle terminating in N iterations, not about a query count over parent rows. No edit; recorded so the next reader does not re-flag it.

**Low 3 - three occurrences in `nested_fetch.py`.** Normalized counts for that file: `Decision 6` **3**, `Decision 9` **0**, ordinal `shape <N>` vocabulary **1** (the `shape 4` site). After the pass: `Decision 6` **3** (all three re-worded to the contract the spec states today), `Decision 9` **0**, ordinal vocabulary **0**. **This count is right for the string it sought and wrong about the file: the file carried a fourth citation spelled `Decision-6`, which neither the unhyphenated phrase nor the ordinal sweep could see.** That site is repaired under `### Low 4`; the instrument failure is recorded under `### Low 5 - the two measurements that did not reproduce`.

The tree-wide context, measured but deliberately not acted on. **Both figures in this paragraph were re-measured after the fact and are corrected here in place; the original wording and what was wrong with each are recorded in `### Low 5 - the two measurements that did not reproduce`.** With hyphenation normalized (`Decision-6` folded into `Decision 6`) and attribution taken from the nearest `spec-0NN` marker within 70 characters, `spec-033 Decision 6` occurs **27** times across `.py` - `tests/optimizer/test_walker.py` 12, `optimizer/nested_planner.py` 4, `optimizer/walker.py` 4, `optimizer/nested_fetch.py` 3, `test_library_api.py` 2, `connection.py` 1, `optimizer/lateral_fetch.py` 1 - of which **3** are in `nested_fetch.py` itself, so **24** are elsewhere. `spec-033 Decision 9` occurs **1** time (`tests/optimizer/test_walker.py`, a helper-move reference). Every one was read against the current spec text: they cite the Decision by number for contracts it still states (refusal / fallback discipline, alias merging, the scalar-only projection, the no-leakage rule, the helper consolidation), and none of them names a retired ordinal. A tree-wide sweep for retired ordinal vocabulary (`shape <N>`, `arm <N>`, `first/second/third/fourth shape`, `four numbered shapes`) returned exactly one spec-033 hit, the `nested_fetch.py` one this pass fixed. `examples/fakeshop/test_query/test_library_api.py #"Third shape of the same collapse"` matches the pattern but is the test suite's own enumeration of three sibling collapse scenarios, not a spec ordinal - no edit. **No site outside the writable list needed a write**, so nothing was widened and there is nothing to stop-and-report.

### Sites corrected, before and after

Low 1 uses pass 1's own correction shape - name the absolute count and the seeded cardinality instead of claiming a property the body does not exercise, and point at the two-cardinality pin that does earn it. Pass 1's two corrected sites (`tests/test_relay_connection.py::test_fast_path_single_query` and `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility`) were read first so all six sites now read as one convention.

1. `tests/test_relay_connection.py::test_divergent_aliases_one_window_query_per_alias` - 4 genres, two aliases, `django_assert_num_queries(3)`.
   - before: "so the count is FIXED (1 parent + 2 windows) independent of parent count, and each alias serves ITS OWN page bound."
   - after: "so the cost is ONE window PER ALIAS on top of the parent list, and each alias serves ITS OWN page bound. Pinned at ONE cardinality, with the ABSOLUTE count that makes it distinguishing: 4 parent genres, two aliases, and exactly 3 queries (1 parent list + 2 windows), where a per-parent pipeline would pay 1 + 4 x 2. The two-cardinality form of the parent-count property is earned live by `examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count`."
   - The retained general claim is the one the body does exercise: at one cardinality, 3 = 1 + 2 is exactly "one window per alias on top of the parent list". The parent-count half is handed to the pin that runs two cardinalities.

2. `examples/fakeshop/test_query/test_library_api.py::test_genre_books_connection_probe_childless_and_populated_parents` - 2 genres, `len(captured) == 2`.
   - before: "and in the fixed two-query cost regardless of parent count."
   - after: "and at an ABSOLUTE two-query cost - one root query + one windowed prefetch - at the seeded 2 parent genres. One cardinality, so the count is what distinguishes the window from a per-parent fallback here, not a comparison across cardinalities; the two-cardinality form of that property lives at `::test_nested_books_connection_fixed_query_count`."

3. `::test_genre_books_connection_divergent_aliases_batched_per_key` - 2 genres, two aliases, `len(captured) == 3`.
   - before: "Pinned: the fixed 3-query cost (root genres + one window per alias - independent of parent count), each alias's OWN page bound and ..."
   - after: "Pinned: the ABSOLUTE 3-query cost at the seeded 2 parent genres (root genres + one window per alias, never one per parent) - one cardinality, so the absolute count is the distinguishing measurement and the two-cardinality form of the parent-count property lives at `::test_nested_books_connection_fixed_query_count`; each alias's OWN page bound and ..."

4. `::test_nested_books_connection_has_next_page_without_edges` - 3 genres, `len(captured) == 2`.
   - before: "in the same fixed two-query window (root genres-connection + one `booksConnection` prefetch), independent of parent count."
   - after: "in the same ABSOLUTE two-query window (root genres-connection + one `booksConnection` prefetch) at the seeded 3 parent genres. One cardinality, so the count is the distinguishing measurement here; the two-cardinality form of the parent-count property lives at `::test_nested_books_connection_fixed_query_count`."

**The two correct sites were verified two-cardinality by reading their bodies, and left untouched.** `examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count` defines `_run(genre_count)` and calls `_run(3)` then `_run(10)`, asserting `three_count == ten_count` and `three_count == 2`. `::test_list_relation_and_connection_sibling_coexist_live` calls `_run(2)`, deletes every seeded row, calls `_run(4)`, and asserts `two_count == four_count` and `two_count == 3`. Both genuinely compare across cardinalities, so both earn the general property, and all four corrected sites now point at the first of them.

**Low 2**, `django_strawberry_framework/optimizer/walker.py`: the three words were deleted and the block re-wrapped to the 99-column layout. Before: "Readers of the underscore aliases below, measured rather than assumed: `_is_fragment`, ..."; after: "Readers of the underscore aliases below: `_is_fragment`, ...". The reader sets themselves are unchanged, character for character. The rest of the block was re-read for provenance phrasing of the same kind and carries none: the second alias block's "private names that predate the connection-planner extraction" states why a back-compat alias exists at all, which is a fact about the aliases rather than about how any comment was authored, and Worker 3 verified that block's content. No other sentence in either block refers to a prior version, a measurement act, or a review.

**Low 3**, `django_strawberry_framework/optimizer/nested_fetch.py`, each re-worded against the current `### Decision 6`:

1. `::unwindowable_child_queryset_reason #"distinct"` - before: "the window `Count(1) OVER` would over-count pre-DISTINCT rows (the historical spec-033 Decision 6 shape 4 guard, now centralized here)." The ordinal is retired and "historical ... now centralized here" is change history rather than an invariant. After: "SQL evaluates window functions BEFORE `DISTINCT`, so the `_dst_total_count` `Count(1) OVER` annotation would over-count a de-duplicated child queryset. The correctness-critical reason of the five (spec-033 Decision 6, the unwindowable-child-queryset refusal arm): a silently wrong `totalCount` is worse than a per-parent count that is right." That is the mechanism the current spec states, and the arm is named by content, not by ordinal, so a renumbering cannot rot it again.

2. `::unwindowable_child_queryset_reason #"The walker treats any reason as a"` - before: "a fully-unplanned spec-033 Decision 6 fallback". After: "a WHOLE-RELATION refusal (spec-033 Decision 6): the relation is left unplanned for every response key". The current Decision states non-planning at two granularities, per-response-key and whole-relation, and names this arm whole-relation; "fully-unplanned" was the pre-rewrite vocabulary and no longer distinguishes the two.

3. `::NestedConnectionStrategy` - before: "the spec-033 Decision 6 fallback discipline". After: the behavior sentence stands on its own, and the citation now carries the contract the spec states for a strategy refusal: "A strategy that refuses every response key is a whole-relation refusal that leaks no resolver key, fk-id elision or `cacheable` flip into the parent plan (spec-033 Decision 6)."

No source line this pass wrote carries a line number, a review-round id, a finding id, or a build-plan step.

### Tests added or updated

None. All three findings are comment and docstring edits; no test expectation, assertion, fixture, cardinality, or node id changed anywhere in this pass's diff. No assertion was weakened and no cardinality was added to make a claim true.

### Validation run

Ruff scoped to this pass's own four files, never `.`:

- `uv run ruff format tests/test_relay_connection.py examples/fakeshop/test_query/test_library_api.py django_strawberry_framework/optimizer/walker.py django_strawberry_framework/optimizer/nested_fetch.py` -> **4 files left unchanged**.
- `uv run ruff check --fix <the same four>` -> **All checks passed!**
- `uv run python scripts/check_trailing_commas.py --check <the same four>` -> silent pass.
- ASCII-only, per file: `LC_ALL=C grep -c '[^ -~\t]'` -> **0** on all four. Every character this pass wrote is plain ASCII; `-` and `->` throughout, no em-dash and no arrow glyph.
- `git status --short` after both ruff invocations -> the ten R2 partition files `M` (the nine from pass 1 plus `optimizer/nested_fetch.py`), `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `M` (the concurrent Slice 2 pass), the cycle's `docs/builder/` artifacts and `docs/SPECS/appx/…-rationale.md` untracked, `0_0_14.md` untracked (baseline). **No unexpected modified file. Nothing was reverted.** Three files that were dirty at this pass's start (`examples/fakeshop/apps/products/services.py`, `examples/fakeshop/test_query/test_debug_extension_api.py`, `examples/fakeshop/test_query/test_products_api.py`) are no longer listed, a concurrent session having committed them; that is other work and was neither read as this pass's output nor touched.

Focused runs, every one without any `--cov*` flag and with the required `--no-cov`:

- `uv run pytest tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov -q` -> **1005 passed** (matches pass 1 exactly).
- `uv run pytest examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov -q` -> **224 passed** (matches pass 1 exactly).
- `uv run pytest tests/ --no-cov -q` -> **5967 passed, 40 skipped** (matches pass 1 exactly). Run as the staleness sweep even though a comment-only diff cannot change a model field set or a wire shape - `optimizer/nested_fetch.py` is production code imported across the optimizer suites, so the whole package tree was re-run rather than only the four files' own tests.

The first two scopes cover both files that import the changed production surface as well as the two edited test files, per `worker-2.md` `## Apply-changes verification scope`.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. It adds no branch, no raise, no assertion and no executable byte - the obligation it owes instead is the **inverse** proof below.

### Inverse proof (all four files: executable bytes unchanged)

Before-copies of all four files were taken to `<scratchpad>/before/` **outside the repository** before any edit, with `shasum -a 256` recorded on the copy and the original at copy time. The baseline is the working tree as found - **not** `HEAD` - so pass 1's verified repairs are inside the baseline and are proved to have survived. No `git stash`, `git checkout`, `git restore` or `git worktree` was used at any point.

Instrument: parse before and after with `ast`, strip every module / class / function docstring (replacing an emptied body with `Pass`), and compare `ast.dump(tree)`, which omits line numbers - so a reflow is invisible and a one-token executable change is not. Digest is the first 12 hex of the dump's sha256.

**Controls, asserted before any file was compared** (a blind instrument reads exactly like a passing proof, and pass 1's first confinement script was blind):

```
assert dump("x = 1  # a") != dump("x = 2  # a")                  # executable change VISIBLE
assert dump("x = 1  # a") == dump("x = 1  # b")                  # comment change invisible
assert dump('def f():\n """A."""\n return 1\n')
    == dump('def f():\n """B."""\n return 1\n')                  # docstring change invisible
assert dump('def f():\n """A."""\n return 1\n')
    != dump('def f():\n """A."""\n return 2\n')                  # body change under a docstring VISIBLE
-> control: 4/4 asserted OK
```

**Live-file control, run against a file the instrument had just cleared** - the synthetic control proves the algorithm, this proves it on the real 5000-line input: a single `_PROBE_SENTINEL = 1` statement inserted into the in-memory text of `tests/test_relay_connection.py` changes its digest. Asserted, not printed:

```
assert digest(mutated) != digest(source), "instrument blind to a real executable change"
-> live-file control: a one-statement insert into tests/test_relay_connection.py IS seen -> instrument can fail
```

The instrument also demonstrated it fails loudly on a bad input rather than passing quietly: its first invocation raised `FileNotFoundError` on a mis-derived before-copy path and produced no result row at all.

Result - all four files, before-digest vs after-digest of the docstring-stripped dump:

| File | before | after | equal |
|---|---|---|---|
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | **True** |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | **True** |
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | **True** |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `302fbecdcc8d` | `302fbecdcc8d` | **True** |

The first three digests are **identical to the values pass 1 recorded and Worker 3 independently reproduced** (`e357f45d6f2a`, `b5918390baa8`, `615fe2fe2be2`), which is a third instrument agreeing with both and confirms the baseline is the same working tree.

`nested_fetch.py` additionally has no pass-1 change to separate out: `git show HEAD:django_strawberry_framework/optimizer/nested_fetch.py` written to a scratch path outside the repository is **byte-identical** to this pass's before-copy (`cmp` silent), so this pass is that file's only modification and the identity is against `HEAD` as well as against the working tree.

### Hot-path budget

The plan declares `optimizer/walker.py`'s plan walk hot - per request, per resolver, per parent row - and the mid-flight instruction declares `optimizer/nested_fetch.py` hot on the same terms. Both edits are comment-only, so the honest number is a demonstrated **zero delta**, and the `### Inverse proof` identity above **is** the hot-path record rather than a timing run: the compiled structure of both modules is byte-for-byte the structure that was there before, so no instruction was added to either path and there is nothing a before/after measurement could resolve that the identity does not.

- metric: `ast.dump` of the docstring-stripped module, before vs after. Command: recorded verbatim in `### Inverse proof`. Iterations: one exact comparison per file; an identity needs no statistic.
- before / after / delta: `615fe2fe2be2` / `615fe2fe2be2` / **0** (`optimizer/walker.py`); `302fbecdcc8d` / `302fbecdcc8d` / **0** (`optimizer/nested_fetch.py`).

`tests/test_relay_connection.py` and `examples/fakeshop/test_query/test_library_api.py` are test files and sit on no declared hot path.

### Floor verification

Not applicable; plan declares floor-verification scope `none` for this cohort, and the mid-flight instruction left that declaration unchanged. The declaration survived this pass: no edit changed an executable byte, so no Django / Strawberry / channels integration seam moved and the plan-level drift condition ("if any edit turns out to change an executable byte, pause") was never reached. The shared `.venv` was not mutated - `uv pip install` was never invoked - and no version is stated from memory anywhere in this report.

### Implementation notes

- **The general property was not deleted from the four docstrings, it was re-homed.** Each corrected site states what its own body measures (an absolute count at a named cardinality) and then names the sibling that runs two cardinalities. Deleting the property outright would have left a reader unable to tell whether parent-count independence is contracted at all; pointing at the pin that earns it keeps the contract visible and attributes it to the row that can fail if it breaks.
- **Site 1 keeps a general clause because its body earns that one.** "one window per alias on top of the parent list" is exactly what `3 == 1 + 2` at two aliases measures. The clause that did not survive is the parent-count one, which four genres at a single cardinality cannot distinguish from a coincidence.
- **The corrected sites in `test_library_api.py` use the bare `::name` form** for the same-file two-cardinality pin, matching pass 1's correction at `::test_nested_window_respects_book_visibility`; the cross-file site in `tests/test_relay_connection.py` uses the full `path::name` form, matching pass 1's correction at `::test_fast_path_single_query`. Both are `AGENTS.md` source-reference spellings.
- **Low 3's citations now name the arm by content, not by position.** "the unwindowable-child-queryset refusal arm" and "a strategy that refuses every response key" survive a renumbering of Decision 6's arms; "shape 4" did not survive one. The `distinct` bullet also gained the mechanism sentence (window functions evaluate before `DISTINCT`) so the comment is checkable against SQL semantics rather than only against a spec heading.
- **Low 3's third site drops the citation from the behavior sentence and attaches it to the contract sentence.** The strictness-visibility clause reads correctly with no Decision reference; the no-leakage clause is the one the spec actually states, so that is where the reference belongs.
- **No `docs/builder/temp-tests/r2b/` directory was created.** It was offered as scratch; a pass whose entire proof is an identity over copies held outside the repository has nothing to put in it, and creating an empty directory would leave a false trace for `scripts/clean_up.py`.

### Low 4 - the module docstring's ownership sentence (added after the sections above were written)

Worker 0 dispatched a fourth finding against this same cohort while this report was being appended, and it is recorded inside this pass rather than as a third report because it lands in a file this pass had already opened. The current `### Decision 6` was re-read from `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` before any wording was written, and every ownership claim below was checked against `optimizer/nested_planner.py::plan_connection_relation`'s own body, not against the finding's paraphrase and not against the three sites repaired earlier in this pass.

The site is `django_strawberry_framework/optimizer/nested_fetch.py #"The private planner"`, in the **module docstring** - about 80 lines above `::unwindowable_child_queryset_reason`, whose two citations this pass had already re-worded. Before:

> ... owns everything strategy-independent - recognition, the Decision-6 fallback shapes (sidecar, `OptimizerHint.SKIP`, DISTINCT, malformed slice, unwindowable partition), the divergent-alias per-response-key scheme ...

Three separate wrongnesses, all comment-only, each verified rather than accepted:

1. **Retired vocabulary.** "fallback shapes" is the pre-rewrite heading's noun; the current Decision reads "Refusal arms, divergent aliases, hints, and scalar-only connections" and says "refusal arms" throughout its body. A tree-wide `.py` sweep for the phrase found **3** occurrences before this edit and **2** after - the two remaining are outside this pass's writable partition and are recorded for the integration pass below.
2. **The enumeration matched neither structure.** Five items against a Decision that now states **nine** refusal arms. A closed list of an open set is what rots, so the replacement does not restate the set: it names examples behind "among them", which stays true when a tenth arm lands.
3. **The ownership claim was false in three of its five items,** and the source is what settles it, not the spec's prose. Read directly from `optimizer/nested_planner.py::plan_connection_relation`: the planner itself decides the unresolvable field map (`if django_field is None`), conflicting per-key argument payloads (`if response_key_arguments_conflict(sel)`), `OptimizerHint.SKIP` (`if hint_is_skip(...)`), `related_model is None`, the unwindowable relation kind, and the every-key strategy refusal; sidecar input and `last: 0` are decided by `::_divergent_key_windows` in the same module. But the malformed window is raised by `utils/connections.py::derive_connection_window_bounds`, the relation kind is *classified* by `optimizer/join_taxonomy.py::classify_relation_join`, and DISTINCT is classified by `unwindowable_child_queryset_reason` - **a function in this very module**, whose docstring this pass had just rewritten to say exactly that. The old sentence therefore contradicted a sibling docstring eighty lines below it.

After:

> ... owns everything strategy-independent - recognition, the refusal arms decided in its own module (among them sidecar input, `OptimizerHint.SKIP`, conflicting per-key argument payloads, an unwindowable relation kind, and an unresolvable field map), the divergent-alias per-response-key scheme ... Not every refusal is the planner's own: a window the slice arithmetic cannot express is raised by `utils/connections.py::derive_connection_window_bounds`, the relation kind is classified by `optimizer/join_taxonomy.py::classify_relation_join`, and an unwindowable child queryset is classified by `unwindowable_child_queryset_reason` in THIS module.

Three shape choices, each aimed at the rot rather than only at the sentence:

- **No Decision reference at all here.** The three sites repaired earlier in this pass cite Decision 6 by arm name because each one *is* a single arm's contract; this sentence is a module-ownership boundary that reads correctly without a spec reference, and adding one would invite a reader to re-check a list the sentence deliberately does not close. `Decision 6` occurrences in the file: **3** before this edit, **3** after - the same three arm-named citations, none of them this one.
- **"among them" makes the list open.** A future tenth arm cannot falsify an open list; it falsified the closed one.
- **The negative half is the load-bearing half.** Naming the three refusals decided outside the planner is what stops the ownership sentence being read as exhaustive, and it removes the contradiction with `unwindowable_child_queryset_reason`'s own docstring.

**One site inside the partition was considered and deliberately left.** `tests/optimizer/test_walker.py::test_refusing_nested_fetch_strategy_leaves_selection_unplanned #"behaves exactly like the other fallback shapes"` carries the same retired noun, but it is a prose comparison inside a test docstring ("even a callback that mutates every plan field behaves exactly like the other fallback shapes"), not a citation: it points at sibling test scenarios, resolves without consulting the spec, and its own sentence already cites the Decision correctly one line above. Rewriting it would be a cosmetic churn in a file whose one executable change this pass must not disturb. Considered, judged not worth a write, and recorded here so the next reader knows it was weighed rather than missed.

### Low 4 - validation, identity, and hot-path record

Gates, on the one file this finding touched:

- `uv run ruff format django_strawberry_framework/optimizer/nested_fetch.py` -> **1 file left unchanged**; `uv run ruff check --fix` -> **All checks passed!**; `uv run python scripts/check_trailing_commas.py --check` -> silent pass; `LC_ALL=C grep -c '[^ -~\t]'` -> **0**.
- Retired-vocabulary re-sweep of the file, whitespace-normalized: `fallback shapes` **0**, `Decision-6` **0**, ordinal `shape <N>` **0**, `Decision <N>` **3** (the three arm-named citations).

Identity, same instrument and same before-copy as `### Inverse proof` - the baseline is still the working tree as this pass found it, so the digest below is the same one the earlier sections recorded and the sentence's rewrite is proved against both:

| File | before | after | equal |
|---|---|---|---|
| `django_strawberry_framework/optimizer/nested_fetch.py` | `302fbecdcc8d` | `302fbecdcc8d` | **True** |

The other three files were re-run in the same invocation and are unchanged from the table above (`e357f45d6f2a`, `b5918390baa8`, `615fe2fe2be2`).

**The instrument was shown capable of failing on this file specifically, not only on the earlier one.** The generic live-file control's anchor is `import pytest`, which `nested_fetch.py` does not contain - so the control's own anchor-presence assertion **fired and aborted the run** rather than silently skipping, which is the behavior the discipline exists for and is recorded here as evidence the control is real:

```
AssertionError: CONTROL SETUP FAILED: probe anchor absent
```

A dedicated control was then run against an anchor the file does have:

```
anchor = "from __future__ import annotations"      # asserted present BEFORE mutating
assert digest(mutated) != digest(source)
-> live-file control on nested_fetch.py: a one-statement insert IS seen -> 302fbecdcc8d != 4e4ee66b45aa
-> on-disk file untouched by the control: True
```

The mutation was applied to an in-memory copy only; the on-disk file was never written, so no mutation was live at any point and no restore was owed.

**Hot-path budget.** `optimizer/nested_fetch.py` is hot - per request, per resolver, per parent row. The edit is a module docstring, so the number is a demonstrated **zero delta**, and the identity above is the record: metric `ast.dump` of the docstring-stripped module, one exact comparison, before `302fbecdcc8d` / after `302fbecdcc8d` / delta **0**. No instruction was added to the path.

**Focused runs**, all with the required `--no-cov` and no `--cov*` flag anywhere: `tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py` -> **1005 passed**; `examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py` -> **224 passed**; `tests/` -> **5967 passed, 40 skipped**. Identical to the three scopes recorded above and to pass 1.

**Concurrent work appeared in `git status --short` during this addendum and was left alone.** `README.md`, `docs/builder/ARTIFACT.md`, `docs/builder/BUILD.md`, `docs/builder/worker-1.md`, `docs/builder/worker-2.md`, `docs/builder/worker-3.md` and `examples/fakeshop/db.sqlite3` are now `M` and none of them is this pass's: the only docs this pass writes are this artifact (untracked) and `docs/builder/worker-memory/worker-2.md` (gitignored via `.gitignore:188`, which is why it never appears in `git status` at all). `docs/builder/worker-2.md` is the **role** file, not the memory file - a one-line change by another session, not by this one. Reported, not reverted, per `AGENTS.md` rule 34. The ten R2 partition files plus the concurrent Slice 2 spec file are otherwise exactly as recorded in `### Validation run`, and `examples/fakeshop/test_query/test_products_api.py` is still absent from the list.


### Low 5 - the two measurements that did not reproduce, and the pin that three sweeps missed

Three numbers this pass recorded were re-derived from scratch. Two of them were wrong. No conclusion changes - every judgement they supported survives re-measurement - but the numbers themselves were handed forward as recommendations, and a wrong number offered as "measurable rather than remembered" is the shape that gets trusted.

**1. The two-cardinality census was short by one, and the miss was an adjective.** `### Notes for Worker 1` item 1 said **two** `.py` sites earn parent-count independence in general terms. There are **three**. The third is `examples/fakeshop/test_query/test_library_api.py::test_nested_empty_parent_serves_zero_total_count_no_fallback_live`, whose docstring says the captured count is "INDEPENDENT of the number of empty parents". Every phrase list used anywhere in this cycle - the four-alternative one, and this pass's twelve-spelling widening - required `parent` to follow `number of` immediately, so the intervening word **"empty"** hid it from all of them. The note has been corrected in place and names all three pins.

All three were re-verified by **reading their bodies**, not by trusting the correction:

| Pin | cardinalities | the assertion that compares them |
|---|---|---|
| `::test_nested_books_connection_fixed_query_count` | `_run(3)`, `_run(10)` | `three_count == ten_count`, `three_count == 2` |
| `::test_list_relation_and_connection_sibling_coexist_live` | `_run(2)`, `_run(4)` | `two_count == four_count`, `two_count == 3` |
| `::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` | `_run(3)`, `_run(8)`, all parents childless | `three_count == eight_count` |

The third is the only one covering the empty-parent shape, which makes it the least redundant of the three rather than a duplicate that happened to be missed.

**The instrument that found it, and the one that should have.** A phrase list enumerates spellings; the working instrument enumerates a **vocabulary class inside a character window**, so an unanticipated word between the two halves cannot hide a site:

```
(independent|independence|regardless|irrespective|no matter|does not scale
 |does not grow|constant|flat in|unchanged by|same for)[^.]{0,60}?parents?\b
| parents?\b[^.]{0,60}?(same class)                       (case-insensitive,
                                                           whitespace normalized)
```

Run tree-wide over `.py` it returns **15** matches, of which the five in `test_library_api.py` resolve to exactly the three pins above (two of them match twice, in a docstring and in the assertion comment beneath it). The other ten are unrelated uses of the same words ("the content type is a constant", "Independent per-parent") and were read and discarded. The four sites corrected under Low 1 no longer match any member of the class, which is the intended post-state.

**2. The `spec-033 Decision 6` tree-wide figure was right in its digits and wrong in its subject.** The original wording said the Decision is cited at "**27** further `.py` sites". Re-measured with hyphenation normalized and attribution taken from the nearest `spec-0NN` marker within 70 characters: **27 occurrences in total**, of which **3** are in `nested_fetch.py` itself, so **24** are *further* / elsewhere. 27 was the total, not the remainder; the word "further" is what made it false. Distribution is now stated per file in `### Re-measured populations`. Every one of the 24 was read against the current spec and cites a contract the spec still states, so the conclusion the number supported is unchanged.

**3. The file-scoped count that cleared `nested_fetch.py` missed a citation over one character.** `Decision 6` **3** was correct for the string sought; the file carried a fourth spelled **`Decision-6`**. The hyphenated spelling is not rare - `Decision-<N>` occurs **38** times across `.py` in 25 files, and `Decision-6` specifically **8** times in 5 files after this pass's repair (`optimizer/nested_planner.py` 2, `tests/test_relay_connection.py` 3, `utils/connections.py` 1, `tests/optimizer/test_extension.py` 1, `tests/optimizer/test_walker.py` 1). The retired-*ordinal* sweep could not see it either, because the site names the retired *heading text* rather than an ordinal. Two blind spots, one site, and it sat in the file this pass had already opened.

**This is the third distinct grammar to defeat a count in this cycle**, and the three share one cause worth stating once: a count is only as wide as the grammar of the thing it searches for. A citation **wrapped across two lines** (pass 1: read 9 where it was 10). A **full-id spelling** where a bare numeral was sought (an earlier cohort: 7 where it was 9). And now a **hyphenated spelling** plus an **intervening adjective** (3 where it was 4, and 2 where it was 3). Whitespace normalization defeats the first; hyphenation normalization defeats the second; only a vocabulary class inside a character window defeats the third, and it is the instrument every population sweep in this area should use from here.

No `.py` file was edited for this finding. The corrections are to `### Notes for Worker 1` item 1 and to the two figures in `### Re-measured populations`, all made in place with the original wording and its defect recorded here rather than silently overwritten.

### Notes for Worker 3

- The diff to review in this pass is four `.py` files and is provably comment-only in all four - the identity, its four asserted synthetic controls and its asserted live-file control are in `### Inverse proof`. Re-run it against your own instrument; three of the four digests are already double-attested by pass 1 and your own round-1 re-run.
- Nothing from pass 1 was re-opened. `tests/test_connection.py`, `tests/optimizer/test_plans.py`, `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`, `django_strawberry_framework/connection.py` and `django_strawberry_framework/optimizer/plans.py` are untouched by this pass and still carry pass-1 content only.
- The Low 1 population instrument is a whitespace-normalized occurrence count over `.py` files, deliberately not a `grep`, and it was cross-checked from the opposite direction by a bare-word `independent` read. Both numbers are in `### Re-measured populations`. If you re-derive it, count occurrences rather than matching lines - the two differ whenever a claim wraps.
- The 27 further `spec-033 Decision 6` citations tree-wide were read against the current spec and left alone deliberately; the reasoning and the retired-ordinal sweep that clears them are recorded in `### Re-measured populations`. That is the finding most likely to be re-raised, so it is measured rather than asserted.

### Notes for Worker 1 (spec reconciliation)

Each amendment carries its section heading, the current wording quoted, and a recommended replacement.

1. **`## Test plan`, if it states the parent-count-independence census. Corrected below - the first wording of this amendment said two pins and there are three.** Worker 3's round-2 note 3 said a census written against the cohorts' five named sites would be four sites short. The number to write against is measurable rather than remembered, and re-measured with a vocabulary-class instrument rather than a phrase list (see `### Low 5`): after this pass, exactly **three** `.py` sites claim parent-count independence in general terms, and all three genuinely run two cardinalities -
   - `examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count` - 3 and 10 genres, `three_count == ten_count` and `== 2`;
   - `::test_list_relation_and_connection_sibling_coexist_live` - 2 and 4 genres, `two_count == four_count` and `== 3`;
   - `::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` - 3 and 8 **empty** parents, `three_count == eight_count`. The only one of the three covering the empty-parent shape, so it is the least redundant of them, and the one every phrase-list sweep in this cycle missed.

   Six further sites pin an absolute count at one named cardinality and point at the first of the three. Recommended replacement, wherever the test plan describes the fixed-query-count pins: "The general parent-count-independence property is earned by three live two-cardinality pins, one of which covers the empty-parent shape; every other fixed-cost pin states an absolute count at its own seeded cardinality and defers the general property to them." No spec sentence is currently known to be wrong - this is the wording to use if one is written.

2. **`### Decision 6 - Refusal arms, divergent aliases, hints, and scalar-only connections`.** The Decision's arms are numbered 1-9 in the rewritten text, and `optimizer/nested_fetch.py`'s comments previously cited one of them by ordinal ("shape 4") - an ordinal from the pre-rewrite structure that survived the rewrite as a live, wrong citation because no gate reads prose ordinals. Current wording, arm 6: "**An unwindowable child queryset** - *whole relation*, classified before the child plan is applied by [`optimizer/nested_fetch.py::unwindowable_child_queryset_reason`][nested-fetch], which names five reasons: `sliced`, `select_for_update`, `combined`, `distinct`, `values`." Recommended replacement: leave the arm's content exactly as it stands and add, at the end of the Decision's introductory paragraph, one sentence: "The arms are enumerated for readability; source comments cite them by name (`the unwindowable-child-queryset arm`), never by ordinal, so a renumbering cannot silently falsify a citation." The three `nested_fetch.py` comments already follow that rule; the spec sentence is what would stop the next rewrite from re-creating the rot.

3. **No third amendment.** The 27 remaining `spec-033 Decision 6` citations and the 1 `Decision 9` citation across `.py` were each read against the current spec text and are true as written; the renamed headings did not break them because none cites a heading string or an ordinal.

4. **Two sibling sites carry the retired "fallback shapes" vocabulary and are OUTSIDE this cohort's writable partition.** Both were verified against the current `### Decision 6` and neither was written; the integration pass owns them.
   - `django_strawberry_framework/optimizer/lateral_fetch.py #"The walker-owned fallback shapes (sidecar, SKIP, DISTINCT, malformed slice, unwindowable join)"` - the same five-item closed list, one word different from the one repaired here, and carrying the same false ownership claim (DISTINCT is classified in `optimizer/nested_fetch.py`, the malformed window in `utils/connections.py`, the join kind in `optimizer/join_taxonomy.py`). Recommended replacement, mirroring the repaired sentence: "The refusal arms the walker and planner decide before any strategy runs (among them sidecar input, `OptimizerHint.SKIP`, and an unwindowable relation kind) leave the relation unplanned; an unwindowable child queryset and a window the slice arithmetic cannot express are classified elsewhere."
   - `django_strawberry_framework/optimizer/nested_planner.py #"# (b) Fallback shapes detectable before any queryset is built -> UNPLANNED."` - an inline section marker, not a citation, but it is the retired noun sitting directly above the arm the current Decision calls "one response key carrying two conflicting argument payloads". Recommended replacement: `# (b) Refusal arms detectable before any queryset is built -> UNPLANNED.`

5. **One in-partition site was considered and deliberately left**, recorded so it is not re-raised as a miss: `tests/optimizer/test_walker.py #"behaves exactly like the other fallback shapes"`. Reasoning in `### Low 4 - the module docstring's ownership sentence`. If Worker 1 disagrees, it is a one-word docstring edit with no executable byte.

6. **The rot's mechanism is worth one spec sentence, and it is the same one recommended in amendment 2.** Four `.py` sites in this cohort's neighbourhood cited Decision 6 by its retired heading noun or by an ordinal, and no gate could see any of them: `scripts/check_citations.py` validates `path::Symbol` references, not spec-heading nouns or prose ordinals. Naming the citation convention inside the Decision is the only instrument available.

---

## Review (Worker 3, pass 2)

A fresh reviewer with no in-context memory of pass 1. This section grades **pass 2's diff** — the apply-changes pass that closed Low 1, Low 2 and Worker 0's mid-flight Low 3 — and confirms it disturbed nothing pass 1 established. Pass 1's `## Review (Worker 3)` above is not re-litigated except where pass 2 could have regressed it.

**Concurrency note, recorded because it changed a finding.** This artifact was first read at the start of this pass when it ended at pass 1's `### Review outcome`: `Status:` read `built`, the three new checklist boxes were ticked, and **`## Build report (Worker 2, pass 2)` did not yet exist**. It landed while this review was in flight (artifact mtime `19:49:36`, after every one of pass 2's four source writes at `19:31:26`-`19:32:08`). A Medium finding drafted against its absence has been withdrawn, and every claim in it is graded below on its merits. Nothing was overwritten: this section was appended after re-reading, and the build report is intact at `docs/builder/bld-033-review-2-py_comment_repair.md:406-596`. The lesson is the repo's standing one — in a tree with concurrent sessions, an artifact read is a snapshot, and a "missing section" finding needs a re-read immediately before it is written.

### The baseline claim, verified rather than assumed

Pass 2's `### Inverse proof` states its baseline as "the working tree as found - **not** `HEAD`", with before-copies taken to a scratch path outside the repository ahead of every edit. That is the correct reference for this cohort, and it checks out from its own results, which is the only way an outside reviewer can check it:

- Three of its four before-digests (`e357f45d6f2a`, `b5918390baa8`, `615fe2fe2be2`) are **pass 1's post-repair digests**, recorded before pass 2 ran. A baseline taken at `HEAD` could not have produced them, because pass 1's repairs are comment-only and `HEAD`'s digests for those three files are identical — so this test does not distinguish the two on its own. What does distinguish them is the fourth: pass 2 reports `nested_fetch.py`'s before-copy as byte-identical to `git show HEAD:` output, which is only true because **pass 1 left that file untouched**, and pass 1 recorded exactly that twice (`git diff --stat` empty, and `git show HEAD:<path> | cmp -` exit 0). The two statements are consistent only under a working-tree baseline taken after pass 1 and before pass 2.
- Independently: I re-derived all four digests from `git show HEAD:` copies held outside the repository and got the same four values, and pass 1's recorded values reproduce digit for digit **after** pass 2 ran. Three instruments now agree.

I have also established pass 2's file set independently of the report's `### Files touched`, and it matches exactly: `tests/test_relay_connection.py` `19:31:26`, `examples/fakeshop/test_query/test_library_api.py` `19:31:40`, `django_strawberry_framework/optimizer/walker.py` `19:31:54`, `django_strawberry_framework/optimizer/nested_fetch.py` `19:32:08` — four files, one contiguous minute, all inside the partition as extended by the mid-flight instruction. Every other cohort `.py` file is stamped `<= 19:00:43` (pass 1); `examples/fakeshop/test_query/test_products_api.py` is stamped `17:26:13`, the concurrent session's pre-cycle commit.

No `git stash`, `git checkout`, `git restore` or `git worktree` was used at any point in this review. `HEAD` references were obtained with `git show HEAD:<path>` into a scratch tree **outside** the repository.

### The inverse proof, rebuilt again from scratch

A third independent instrument, written without reading Worker 2's or pass 1's: `ast.parse` -> strip every module / class / function docstring (substituting `Pass()` where a body would empty) -> `ast.dump`, which omits line numbers.

**Failability asserted before any measurement, in eight directions** — four the instrument must SEE and four it must NOT:

```
must see:      x = 1        vs x = 2                     -> DIFFER
               x = 1        vs x = 1; y = 2              -> DIFFER   (added statement)
               if a < b     vs if a > b                  -> DIFFER   (inverted guard)
               assert x; return 1 vs return 1            -> DIFFER   (deleted assertion)
must not see:  # a          vs # b                       -> SAME     (comment)
               """A."""     vs """B."""                  -> SAME     (docstring)
               f(a, b)      vs f(\n a,\n b,\n)           -> SAME     (pure reflow)
               """M1."""    vs """M2."""                 -> SAME     (module docstring)
controls: 8/8 asserted OK
```

It then had to report `DIFFER` for the two files known to change executably, and did. A control that cannot fail reads exactly like a passing proof; this one fails on demand in four distinct ways, two of which (added statement, deleted assertion) are the specific shapes a comment-only claim must exclude.

Docstring-stripped `ast.dump` hash, `HEAD` copy vs working tree, **after** pass 2:

| File | pass-1 recorded | pass-2 recorded | measured now | equal | pass 2 wrote it? |
|---|---|---|---|---|---|
| `django_strawberry_framework/connection.py` | `ecc47449f5ec` | — | `ecc47449f5ec` | **yes** | no |
| `django_strawberry_framework/optimizer/plans.py` | `8fb1b399480f` | — | `8fb1b399480f` | **yes** | no |
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | `615fe2fe2be2` | **yes** | **yes** (Low 2) |
| `tests/test_connection.py` | `e10df5d5f0a3` | — | `e10df5d5f0a3` | **yes** | no |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | `e357f45d6f2a` | **yes** | **yes** (Low 1) |
| `tests/optimizer/test_plans.py` | `809ebc71d3d8` | — | `809ebc71d3d8` | **yes** | no |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | `b5918390baa8` | **yes** | **yes** (Low 1) |
| `django_strawberry_framework/optimizer/nested_fetch.py` | (byte-identical to `HEAD`) | `302fbecdcc8d` | `302fbecdcc8d` = `HEAD` | **yes** | **yes** (Low 3) |

Every pass-1 hash reproduces digit for digit **after** pass 2, every pass-2 hash reproduces under an instrument built without sight of it, and `nested_fetch.py` is AST-identical to `HEAD` after an edit that changed its bytes. **Pass 2 changed no executable byte anywhere.** By the same identity no alias, assertion, import, or branch was added or deleted in any of the eight.

Confinement for the two files carrying pass 1's intended executable change, per top-level node at a positional index, with its own control asserted:

- `tests/optimizer/test_walker.py` — 210 -> 210 top-level nodes; differing: `[(142, 'test_m2m_shared_child_partitions_per_parent')]`
- `tests/optimizer/test_extension.py` — 186 -> 186 top-level nodes; differing: `[(92, 'test_cache_key_variable_name_collection_memoized_for_nested_fallbacks')]`

Identical to pass 1's result, node index for node index. **Pass 2 did not touch either file**, and the two pass-1 repairs it was told not to disturb stand exactly as accepted. The four other pass-1 files it was told not to touch (`connection.py`, `optimizer/plans.py`, `tests/test_connection.py`, `tests/optimizer/test_plans.py`) hold their pass-1 hashes above. Pass 2's `### Notes for Worker 3` claims exactly this about all six; it is confirmed mechanically, not accepted.

### No live mutation; nothing written outside the partition

- `git show HEAD:<path> | cmp -` exits 0 for `django_strawberry_framework/optimizer/join_taxonomy.py`, `django_strawberry_framework/optimizer/extension.py` and `examples/fakeshop/test_query/test_products_api.py` — **byte-identical to `HEAD`**. The first two are pass 1's own mutation targets (both reverted); the third is the do-not-touch fence, and it held through pass 2 as it held through pass 1.
- No `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` anywhere in the tree.
- This review made **no** source mutation, and the failability re-run set for pass 2 is **legally empty**: the diff introduces no boundary, guard, gate or rejection path that meets `docs/builder/worker-3.md`'s floor — a claim the `ast.dump` identity proves rather than asserts. Pass 2's `### Failability proofs` says the same and is correct. Pass 1's two boundaries were already re-run to identical 2-row node-id sets; both their files are byte-identical to `HEAD` today. The source carve-out was not exercised this pass.
- `git status --porcelain` shows exactly the ten cohort `.py` files plus the two Slice-2 spec files. `0_0_14.md` and `docs/builder/bld-003-final.md` untouched. Nothing reverted.

### Verdict per finding

**Low 1 — CLOSED. The four sites are corrected in substance and both named-correct sites are untouched; the population is one site larger than pass 2 measured (`### Low 5`).**

Population re-derived from scratch, not accepted from either pass. Instrument: whitespace-normalize each tracked `.py` file (so a claim **wrapped across two lines** is visible), then take any independence-vocabulary token — `independent|independence|regardless|irrespective|no matter|whatever the|does not (grow|scale|vary|change)|constant in|invariant (to|in)|O(1)` — within 90 characters of `parent`. Occurrences, not matching lines. Deliberately a **vocabulary class** rather than a phrase list, because a phrase list is what both prior measurements used.

**Failability of this instrument:** run against the `HEAD` copies it returns **11 occurrences across 9 test functions** in the two writable test files; run against the working tree it returns **4 across 3**. It distinguishes the two states of the exact population under review.

At `HEAD`, the nine functions:

| # | Site | Cardinalities run | Claim earned? | Disposition |
|---|---|---|---|---|
| 1 | `tests/test_relay_connection.py::test_fast_path_single_query` | 1 (4 genres, `django_assert_num_queries(2)`) | no | corrected **pass 1** |
| 2 | `tests/test_relay_connection.py::test_divergent_aliases_one_window_query_per_alias` | 1 (4 genres, 2 aliases, `django_assert_num_queries(3)`) | no | corrected **pass 2** |
| 3 | `…test_library_api.py::test_genre_books_connection_probe_childless_and_populated_parents` | 1 (2 genres, `len(captured) == 2`) | no | corrected **pass 2** |
| 4 | `…::test_genre_books_connection_divergent_aliases_batched_per_key` | 1 (2 genres, `len(captured) == 3`) | no | corrected **pass 2** |
| 5 | `…::test_nested_books_connection_has_next_page_without_edges` | 1 (3 genres, `len(captured) == 2`) | no | corrected **pass 2** |
| 6 | `…::test_nested_window_respects_book_visibility` (2 occ) | 1 (2 genres, `len(captured) == 2`) | no | corrected **pass 1** |
| 7 | `…::test_nested_books_connection_fixed_query_count` (2 occ) | **2** (3 and 10 genres) | **yes** | **untouched** — correct |
| 8 | `…::test_list_relation_and_connection_sibling_coexist_live` | **2** (2 and 4 genres) | **yes** | **untouched** — correct |
| 9 | `…::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` | **2** (3 and 8 empty parents) | **yes** | **untouched** — correct |

All four dispatched sites are corrected. **Both sites the dispatch named as correct are untouched, verbatim** — read by body, not by name: site 7 runs `_run(3)` / `_run(10)` and asserts equal counts; site 8 runs `_run(2)` / `_run(4)` after deleting every seeded row and asserts equal counts. Neither was damaged, and pass 2's own body-level verification of both is accurate.

Each of the four repairs applies repair 5's own correction shape — absolute count, seeded cardinality, and a pointer to the two-cardinality pin — and each number in the new prose checks out against the body:

- `::test_divergent_aliases_one_window_query_per_alias` "4 parent genres, two aliases, and exactly 3 queries": `for gi in range(4)`, aliases `a:` / `b:`, `django_assert_num_queries(3)`. ✓
- `::test_genre_books_connection_probe_childless_and_populated_parents` "ABSOLUTE two-query cost … at the seeded 2 parent genres": `Genre("Populated")` + `Genre("Empty")`, `assert len(captured) == 2`. ✓
- `::test_genre_books_connection_divergent_aliases_batched_per_key` "ABSOLUTE 3-query cost at the seeded 2 parent genres". ✓
- `::test_nested_books_connection_has_next_page_without_edges` "ABSOLUTE two-query window … at the seeded 3 parent genres", `len(captured) == 2`. ✓

Every cross-reference resolves on disk. No assertion changed — the `ast.dump` identity is the formal statement of that, and pass 2's `### Tests added or updated` ("None") is correct.

**Low 2 — CLOSED.**

`django_strawberry_framework/optimizer/walker.py #"Readers of the underscore aliases below"` (`django_strawberry_framework/optimizer/walker.py:50`) now reads "Readers of the underscore aliases below: …". A tree-wide occurrence sweep for `measured rather than assumed` finds it only at `django_strawberry_framework/_request_body.py`, the pre-existing seekability statement, which is out of scope and is a genuine technical claim.

The rest of the comment — the actual invariant — survives, and I re-derived it rather than reading it, because pass 2 rewrote the sentence structure around the deletion and re-wrapped the block. AST instrument over `walker.py`: enumerate module-level underscore aliases, count each one's `ast.Name` LOAD sites inside the module, and resolve every `ImportFrom` whose module ends `optimizer.walker` across all tracked `.py` files (**by AST, not by regex** — see the trap note under `### What looks solid`). Controls asserted first: a module-level import must be seen, a **function-local** import must be seen, a known-dead name must not be. 3/3.

- 17 module-level underscore aliases.
- live via own body (4): `_is_fragment`, `_response_key`, `_response_keys`, `_included_field_selections` — exactly the four the comment names.
- live via importer (4): `_should_include` + `_is_fragment` (`tests/optimizer/test_walker.py:31`, module-level), `_concrete_order_columns` (`:2490`), `_relay_max_results_from_info` (`:3114`) — both function-local, both from `optimizer.walker`, exactly as the comment says.
- **dead (10)**, character-for-character the set the two blocks name: block 1's three (`_named_children`, `_node_children_with_runtime_prefix`, `_with_runtime_prefix`) and block 2's seven. The comment's "the other seven" is arithmetic on block 2's nine minus its two live ones — correct.
- Look-alike attribution verified: `django_strawberry_framework/optimizer/extension.py:124-125` carries its own `_named_children` / `_node_children_with_runtime_prefix` pair, which `tests/optimizer/test_extension.py:59-60` imports; `django_strawberry_framework/connection.py:75` and `tests/test_keyset_connection.py:43` import the four `nested_planner` names from `optimizer/nested_planner.py` directly. The comment names "the first two" for the `extension.py` case, which is precise — `_with_runtime_prefix` has no look-alike importer.
- No alias deleted, no name renamed: the `ast.dump` identity proves it and my own count returns all 17. Escalation 3 was not acted on. ✓

Pass 2 additionally re-read the second alias block for provenance phrasing and cleared "private names that predate the connection-planner extraction". I agree: that states why a back-compat alias exists, which is a property of the alias, not of how the comment was written.

**No new provenance phrasing anywhere in pass 2's diff.** Every added line across all ten modified `.py` files, swept for `measured rather|rather than assumed|previously|used to (be|say|read)|this pass|this change|review round|apply-changes|worker N|finding|R1[abc]|pass [12]|the old |formerly|as authored|no longer says|we (now|found)|I (found|measured)`: **zero hits**. Also zero `TODO(` on any added line, zero `path:NN` raw refs on any added line, and `TODO(spec-033` is still **0** tree-wide.

**Low 3 — the three named sites are CLOSED and correct against today's spec; a fourth citation in the same file is not (`### Low 4`).**

Graded against `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `### Decision 6 — Refusal arms, divergent aliases, hints, and scalar-only connections` as it stands now, read in full. `HEAD`'s version carries the retired form (`### Decision 6 — Fallback shapes: …`, "Four nested-connection shapes", shape 4 = `.distinct()`), which is what the citations were written against.

1. `optimizer/nested_fetch.py::unwindowable_child_queryset_reason #"``distinct``: SQL evaluates window functions BEFORE ``DISTINCT``"` — the retired "the historical spec-033 Decision 6 shape 4 guard, now centralized here" is gone, and with it a second defect pass 2 spotted on its own: "historical … now centralized here" was itself change history. The replacement cites "spec-033 Decision 6, **the unwindowable-child-queryset refusal arm**" — a name, not an ordinal, matching the spec's own bolded arm text ("**An unwindowable child queryset**"). "The correctness-critical reason of **the five**" matches both the spec ("names five reasons: `sliced`, `select_for_update`, `combined`, `distinct`, `values`" … "The `distinct` reason is the correctness-critical one") **and the function body**, which returns exactly those five strings. ✓
2. `::unwindowable_child_queryset_reason #"The walker treats any reason as a WHOLE-RELATION refusal"` — "the relation is left unplanned for every response key" is Decision 6's own new two-granularity vocabulary, stated in its preamble; arm 6 is marked *whole relation*; strictness visibility is likewise the preamble's. ✓
3. `::NestedConnectionStrategy` — "A strategy that refuses every response key is a whole-relation refusal that leaks no resolver key, fk-id elision or ``cacheable`` flip into the parent plan (spec-033 Decision 6)" is arm **9** restated without its ordinal, near-verbatim including the no-leakage triple. ✓

Pass 2's own framing is the right one and worth keeping: the arms are now cited **by content**, so a renumbering cannot rot them again. That is the durable fix, not a re-numbering.

**Retired-structure sweep, tree-wide, whitespace-normalized over 468 tracked `.py` files** (a citation wrapped across two lines is invisible to a single-line grep):

| Pattern | Occurrences | Reading |
|---|---|---|
| `[Ss]hapes? \d` | 1 | `tests/test_views.py` — spec-046 Decision 9's "non-UTF-8 wire **shape 400s**". Unrelated. **Zero spec-033 shape ordinals survive.** Pass 2's own ordinal sweep reaches the same result by a different pattern set. |
| `consolidate into the walker` (retired D9 heading) | 0 | clean |
| `Decision[ -]9` naming a retired D9 structure | 0 | `tests/optimizer/test_walker.py #"Helper-move (spec-033 Decision 9) no-regression lives in test_extension.py"` is the only spec-033 D9 citation, and "helper move" is still exactly what the renamed Decision 9 states. ✓ |
| `[Ff]allback shapes` (retired D6 heading text) | **4** | one is a live citation — `### Low 4`; three carry the vocabulary with no Decision reference, two of them outside R2's partition |
| `spec-033 Decision 6` | 24 | all 24 read correctly against the new text |
| `Decision-6` (**hyphenated**) | **9** | eight are informal arm vocabulary ("a Decision-6 fallback", "each Decision-6 fallback shape") with no ordinal and no heading string; the ninth is `### Low 4` |
| `spec-033 Decision 11` / `spec-033 Decision 4` | 2 / 30 | unchanged from pass 1's accepted values; single-line grep and normalized sweep agree on both, so no wrapped citation was created |

Escalations untouched, verified mechanically: `types/resolvers.py` is absent from `git status` (escalation 1); `optimizer/plans.py` is AST-identical to `HEAD` and `window_partition_for_prefetch` still exists (escalation 2); `walker.py` still carries all 17 aliases (escalation 3).

### Dispatched findings checklist — all ten boxes walked

| Box | Fix in the diff? | Verified how |
|---|---|---|
| 1. staged `TODO(spec-033` anchor | yes | `grep -rno 'TODO(spec-033' --include='*.py'` -> **1** at `HEAD`, **0** now |
| 2. ten `Decision 11` cursor-parity citations | yes | normalized sweep, 10 -> **2**, `Decision 4` 22 -> **30**; all ten sentences read against `### Decision 4` / `### Decision 11` |
| 3. walker alias comment | yes | independent AST pass: 17 aliases, **10 dead**, dead set matches the comment character for character |
| 4. four stale docstrings + one parallel site | yes | new text verified against `connection.py::_window_rows_are_annotated`, `types/resolvers.py::_check_n1` and the marker-row planner; my own sweep found no fifth |
| 5. two single-cardinality pins (three products sites needed none) | yes | corrected sites verified against bodies; `test_products_api.py` **byte-identical to `HEAD`** |
| 6. order-dependent memo test | yes | `tests/optimizer/test_extension.py` confinement unchanged at node 92; pass 1 measured the strengthening by mutation |
| 7. restored shared-child scenario | yes | `tests/optimizer/test_walker.py` confinement unchanged at node 142; both pre-existing equality assertions survive |
| Low 1. four unswept parallel sites | yes | all four corrected in repair 5's shape; three two-cardinality sites untouched — but see `### Low 5` |
| Low 2. provenance phrase in the alias comment | yes | phrase gone tree-wide except the out-of-scope `_request_body.py` site; invariant re-derived and true |
| Low 3. three retired-`Decision 6` citations | yes | all three restate arms 6 and 9 as the current spec states them — but see `### Low 4` |

No box is unaddressed and no box is ticked without a matching fix. Two boxes are ticked on a **population** that is short by one site each, which is what `### Low 4` and `### Low 5` are.

### High:

None.

### Medium:

None.

### Low:

#### Low 4 — a fourth Decision 6 citation names the retired structure, in the same file Low 3 repaired, and the count that cleared the file missed it because of a hyphen

`django_strawberry_framework/optimizer/nested_fetch.py` module docstring (`django_strawberry_framework/optimizer/nested_fetch.py:7`), `#"the Decision-6 fallback shapes"`:

> The private planner (``optimizer/nested_planner.py::plan_connection_relation``) owns everything strategy-independent - recognition, **the Decision-6 fallback shapes (sidecar, ``OptimizerHint.SKIP``, DISTINCT, malformed slice, unwindowable partition)**, the divergent-alias per-response-key scheme …

Low 3 named three sites in this file and pass 2 fixed all three correctly. This is a fourth, in the same file, inside the writable partition, and it is the same defect class the dispatch opened Low 3 for — **the spec moved under the citation**. Three ways it is now wrong:

1. **It cites Decision 6 by its retired heading.** "Fallback shapes" was `### Decision 6 — Fallback shapes: …` at `HEAD`; the current heading is `### Decision 6 — Refusal arms, …` and the body's vocabulary is "refusal arms" throughout. A reader following this citation finds no "fallback shapes". Pass 2 removed exactly this word from `::unwindowable_child_queryset_reason` ("fully-unplanned … fallback" -> "WHOLE-RELATION refusal") and left it standing eighty lines above, in the same docstring pass its own report calls "read directly from the spec before any wording was written".
2. **The enumeration matches neither structure.** It names five items; the retired Decision 6 had four numbered shapes and the current one has **nine** refusal arms. It is a stale partial list of a list that has since more than doubled.
3. **The ownership claim is falsified by the current spec.** The sentence says the private planner *owns* those shapes. Decision 6 sites three of the five elsewhere: the malformed window on `utils/connections.py::derive_connection_window_bounds` (arm 2), the unwindowable relation kind on `optimizer/join_taxonomy.py::classify_relation_join` (arm 7), and — most pointedly — DISTINCT on `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` (arm 6), **a function in this very module**, whose own docstring pass 2 just rewrote to say so.

**Why the pass's own instrument cleared the file: a hyphen.** `### Re-measured populations` states "Low 3 - three occurrences in `nested_fetch.py`, zero elsewhere in that file. Normalized counts for that file: `Decision 6` **3**." That count is correct for the string `Decision 6` and the file carries **four** citations, because this one is spelled `Decision-6`. Measured tree-wide: `Decision[ -]6` in `nested_fetch.py` is `3 + 1`. The hyphenated spelling is not rare — it occurs **9** times across `.py`, in six files. The pass also swept for retired *ordinal* vocabulary and correctly found only the site it fixed, but it did not sweep for the retired *heading text*, and the dispatch's own framing is that "a citation by heading text is as broken as one by ordinal". This is the cycle's recurring structural cause in its second spelling: a differently-spelled variant is invisible to a phrase grep, and here the variant is one character.

Why it is Low and not Medium: nothing here is false about the *runtime* — the five shapes named do reach a fallback, and the planner does own the strategy-independent half. The falsity is in the citation and the ownership attribution, it is comment-only, and it costs a reader one confused lookup rather than a wrong belief about behavior.

Recommended change: replace "the Decision-6 fallback shapes (sidecar, `OptimizerHint.SKIP`, DISTINCT, malformed slice, unwindowable partition)" with wording that names what the planner actually owns without re-enumerating a nine-arm list — e.g. "the strategy-independent refusal arms it decides itself (sidecar input, `OptimizerHint.SKIP`, conflicting per-key arguments, an unwindowable relation kind, and an unresolvable field map)" — and either drop the Decision reference (the sentence reads correctly without one) or cite Decision 6 by arm name, as the three repaired sites now do. **Or** record an explicit deferral naming this site so Worker 1 owns it at final verification. Either closes it. Comment-only; `nested_fetch.py` must still read `302fbecdcc8d` afterwards.

The other eight `Decision-6` occurrences were each read and are **not** this defect: "a Decision-6 fallback" / "each Decision-6 fallback shape" / "the other Decision-6 fallbacks" at `optimizer/nested_planner.py` (x2), `utils/connections.py`, `tests/test_relay_connection.py` (x3), `tests/optimizer/test_extension.py` and `tests/optimizer/test_walker.py` are informal vocabulary for the arms, carrying no ordinal and no heading string. Three further sites carry `fallback shapes` with no Decision reference at all — `optimizer/lateral_fetch.py #"The walker-owned fallback shapes (sidecar, SKIP, DISTINCT, malformed slice, unwindowable join)"` (the same stale five-item list, one word different), `optimizer/nested_planner.py #"# (b) Fallback shapes detectable before any queryset is built"`, and `tests/optimizer/test_walker.py #"behaves exactly like the other fallback shapes"`. The first two are **outside R2's partition** and are escalated under `### Notes for Worker 1`; the third is a simile, not a citation, and is not worth a write.

#### Low 5 — pass 2's recommended `## Test plan` census says two two-cardinality pins; there are three

`### Notes for Worker 1 (spec reconciliation)` item 1 states: "after this pass, exactly **two** `.py` sites claim parent-count independence in general terms … and both run two cardinalities", and offers a spec sentence to be written against it — "The general parent-count-independence property is earned by **two** live two-cardinality pins". The number is wrong, and it is offered specifically as "measurable rather than remembered", so it will be trusted.

There are **three**, all in `examples/fakeshop/test_query/test_library_api.py`, all genuinely two-cardinality and all correctly untouched by both passes:

- `::test_nested_books_connection_fixed_query_count` — `_run(3)` / `_run(10)` genres, `three_count == ten_count`.
- `::test_list_relation_and_connection_sibling_coexist_live` — `_run(2)` / `_run(4)` genres, `two_count == four_count`.
- `::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` — `_run(3)` / `_run(8)` **empty** parents, `assert three_count == eight_count`, docstring `#"the captured count is INDEPENDENT of the number of empty parents"`.

The third has been invisible to every measurement in this cycle, for two independent reasons, both of them the phrase-grep failure mode: pass 1's pattern `independent of (the )?number of parent` is defeated by the intervening word "**empty**", and pass 2's widened pattern set inherits the same shape (its `independent of (the )?number of parent` and `no matter (how many|the number of) parent` alternatives all require `parent` to follow immediately). My own sweep found it only because it matched a **vocabulary class** near the word `parent` rather than a phrase. The same blind spot also hides site 7's second occurrence, which spells the claim as the noun "**independence**" — which is why my tree count is **11 occurrences across 9 functions** at `HEAD` where pass 1 recorded 10 across 8, and why pass 2's post-pass count of "2 occurrences" is really 4 across 3 functions.

Why it matters: no `.py` file is false, and no repair is owed — the third site is correct and was correctly left alone by everyone. But a `## Test plan` sentence written against "two" would be false the day it lands, and the third pin is the **only** one that exercises the empty-parent shape across cardinalities, which is the shape Decision 5's "Parents with no related rows" edge case turns on. This cycle has already produced six wrong counts; this is the seventh, caught before it reached the spec.

Recommended change: correct the recommended wording to name three pins and their axes — "(3 and 10 genres; 2 and 4 genres; 3 and 8 **empty** parents)" — **or** record an explicit deferral so Worker 1 re-derives the census at final verification rather than adopting this number. No source edit is required or wanted; this is a correction to a note, not to code.

### DRY findings

None introduced, and none possible: the `ast.dump` identity proves pass 2 added no symbol, no branch, no literal and no import to any of the four files it wrote.

Repeated string literals for the integration pass's cross-cohort comparison, from this pass's own helper runs on the two production files pass 2 touched (all pre-existing, by the same identity):

- `django_strawberry_framework/optimizer/nested_fetch.py` — 2x `select_for_update`, 2x `distinct`, 2x `windowed`. All three are the reason-string / strategy-name vocabulary the module is *for*; `distinct` and `select_for_update` each appear once in the docstring bullet list and once as the returned reason string, which is the pairing `unwindowable_child_queryset_reason` exists to keep honest. No consolidation target.
- `django_strawberry_framework/optimizer/walker.py` — 3x `prefetch`, 3x `connection`, 3x `arguments`, 2x `operation`, 2x `_optimizer_runtime_prefixes`, 2x `prefetch_through`, 2x `selections`. Byte-identical to pass 1's recorded set.

The two standing existence challenges (`optimizer/plans.py::window_partition_for_prefetch`'s zero production callers; the ten dead walker aliases) remain on `build-033-connection_optimizer-0_0_9.md` `## Escalations` as maintainer decisions. Pass 2 acted on neither, which is correct — and my own AST pass independently re-derives the dead-alias count as **10 of 17**, unchanged.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty and the file is absent from `git status --porcelain`. `__all__` and the re-export list are unchanged. No new public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The two `docs/SPECS/` files dirty in the tree are Slice 2's, read here **read-only** as the contract Low 3 is graded against, and not written.

### Static helper use

Run on the two production files pass 2 wrote, both with `--output-dir docs/shadow`:

- `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/nested_fetch.py --output-dir docs/shadow`
- `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow`

**Recorded skips, with reasons:** `django_strawberry_framework/connection.py` and `django_strawberry_framework/optimizer/plans.py` were **not** re-run this pass. Pass 2 did not write either file, both hold their pass-1 `ast.dump` hashes, and pass 1 already walked all four sections on them and recorded the output. Re-running would reproduce a recorded reading of an unchanged file. Stated rather than silently omitted. (Pass 2 itself ran no helper; for a diff whose formal statement is an AST identity that is defensible, but the two hot-path production files it wrote are exactly the ones `BUILD.md` wants walked, so the walk is done here.)

All four required sections walked on both files:

- **Django / ORM markers.** `nested_fetch.py`: 14 markers, all pre-existing — `QuerySet` / `Prefetch` at the import and on `RecognizedFetchQuerySet`, `OptimizationPlan` on the four `plan()` signatures, and the one real ORM write at `django_strawberry_framework/optimizer/nested_fetch.py::attach_windowed_prefetch #"Prefetch("` feeding `plan.prefetch_related`. That is the hot-path site pass 1 mutated for its failability proof; it is byte-identical to `HEAD` now. `walker.py`: unchanged from pass 1's reading.
- **Repeated string literals.** Recorded under `### DRY findings` for the cross-cohort comparison.
- **Control-flow hotspots.** `nested_fetch.py`: 2 — `unwindowable_child_queryset_reason` (52 lines / 6 branch nodes; the six branches are exactly the five reason returns plus the `values` iterable check, so the branch count *is* the contract, and it is the number the repaired docstring's "the five" has to agree with — it does) and `attach_windowed_prefetch` (42 / 1). Neither is a concern. `walker.py`: 8, led by `_walk_selections` (212 / 20), `_apply_hint` (141 / 8) and `_merge_aliased_selections` (77 / 12) — identical to pass 1's numbers, so pass 2's comment edit grew nothing.
- **Imports.** `nested_fetch.py`: 18, of which five are deliberate function-local imports breaking the documented `lateral_fetch` / `single_parent_fetch` / `conf` cycles, each with an adjacent comment saying so. `walker.py`: 24. Both unchanged; the AST identity is the formal statement.

Quick-scan counts: `walker.py` 24 imports / 37 symbols / 8 hotspots / **2** TODO comments (both `spec-035` anchors, unchanged and unrelated) — identical to pass 1's. `nested_fetch.py`: 18 / 18 / 2 / **0** TODO comments.

No shadow-file line number is cited anywhere in this section; every citation is an original-source line beside its symbol.

### Hot-path budget verification

The build plan's standing declaration makes `optimizer/walker.py`'s plan walk hot, and Worker 0's mid-flight instruction extends the same terms to `optimizer/nested_fetch.py` — per request, per resolver, per parent row — binding any repair landing there to a before/after number "whatever its size". Pass 2 landed in both.

**The number exists and reproduces.** Pass 2's `### Hot-path budget` carries it with a named metric, the command, an iteration count, and both before/after values:

| File | pass-2 recorded before / after / delta | my independent measurement |
|---|---|---|
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` / `615fe2fe2be2` / **0** | `615fe2fe2be2` / `615fe2fe2be2` / **0** |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `302fbecdcc8d` / `302fbecdcc8d` / **0** | `302fbecdcc8d` / `302fbecdcc8d` / **0** |

Reproduced digit for digit under an instrument built without sight of pass 2's. A docstring-stripped AST identity means no instruction was added to either hot path, so there is nothing a timing run could resolve that the identity does not — the same argument pass 1 made for its three files and had accepted. `BUILD.md` makes existence-and-reproducibility the obligation and leaves the size to the maintainer; there is no size to leave. `tests/test_relay_connection.py` and `examples/fakeshop/test_query/test_library_api.py` are test files on no declared hot path, correctly excluded.

### Floor verification

Plan-declared scope `none`, and I checked it against the actual diff rather than against the declaration. Pass 2's four files are all AST-identical to their pre-pass-2 state, so no Django / Strawberry / channels integration seam moved — no `ConnectionExtension` hook, no queryset-compilation call, no ASGI surface. The declaration is not falsified, and the plan's drift condition (a repair that turns out to change an executable byte) was never reached.

The shared `.venv` was not deliberately mutated: no `uv pip install` was invoked at any point in this pass. Read rather than remembered (`uv pip list`): `django 6.1`, `strawberry-graphql 0.324.0`, `channels 4.3.2`, `pytest 9.1.1`. That is **not** the supported floor (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0), as expected, which is why a `none` scope is a declaration and not a measurement. One note for the record: `pytest` read `9.0.3` in pass 1's artifact and reads `9.1.1` now; the change came from `uv run`'s own project-environment sync mid-pass, not from any install this pass issued — `uv.lock` and `pyproject.toml` are both clean in `git status`. The focused suite was re-run after the sync and returns the identical `1005 passed`.

### What looks solid

- **Pass 2 is a genuinely surgical diff.** Four files, one contiguous minute, zero executable bytes, all inside the partition, and the two pass-1 files carrying real executable change were not reopened — their confinement result is node-index-identical to pass 1's. The hardest thing to get right about an apply-changes pass on an already-accepted cohort is not breaking what was accepted, and it did not.
- **Its inverse proof adds a control neither earlier instrument had.** Beyond the synthetic four, it mutates the **real 5000-line input** (`_PROBE_SENTINEL = 1` inserted into `tests/test_relay_connection.py`'s in-memory text) and asserts the digest changes. A synthetic control proves the algorithm; a live-file control proves it on the input that actually matters, and it is the cheap answer to "the algorithm is fine but is it being fed the right file". Worth carrying into the next inverse proof in this repo.
- **Low 1's repairs re-home the general property rather than deleting it.** Each corrected site states what its own body measures and then names the sibling that earns the general claim. Deleting the claim outright would have left a reader unable to tell whether parent-count independence is contracted at all; pointing at the pin that can fail if it breaks keeps the contract attributable. That reasoning is recorded in `### Implementation notes` and is right.
- **Low 3's rewrites cite the arms by content, not by position** — "the unwindowable-child-queryset refusal arm", "a strategy that refuses every response key". "shape 4" did not survive one renumbering; a content citation survives the next one. That is the durable repair, and the added SQL-semantics sentence makes the `distinct` bullet checkable against the database rather than only against a heading.
- The walker comment is true under a from-scratch AST measurement of all 17 aliases, and "no reader" remains the right wording for the three dead names that appear in docstrings.
- Gates all clean on all ten files: `ruff format --check` -> `10 files already formatted`; `ruff check` -> `All checks passed!`; `scripts/check_trailing_commas.py --check` -> rc 0. ASCII-only holds (`LC_ALL=C grep -c '[^ -~\t]'` returns 0 on every one of the ten).
- All three of pass 1's recorded suite results reproduce exactly: `tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov` -> **1005 passed**; `examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov` -> **224 passed**; `tests/ --no-cov` -> **5967 passed, 40 skipped**. No `--cov*` flag was used at any point in this review.
- **The trap I nearly published as a finding.** My first alias instrument resolved importers by regex over whitespace-normalized source and reported **12** dead aliases against the comment's 10 — a two-name disagreement that would have read as a false comment. The regex was blind to a *function-local* `from … import X` whose capture group ran on past the import into the following statement. Re-implemented against `ast.ImportFrom` with a control asserting a function-local import is visible, it returns 10 and the comment is exact. A population is only ever as good as its instrument's blind spot, and the second-cheapest thing available — a plain `grep -rn` on the two disputed names — is what caught it.
- `$FILES` unquoted in zsh collapsed ten paths into one argument again — `ruff format --check` reported "No such file or directory", `check_trailing_commas.py` reported "read error … NOT checked", and a naive `echo "rc=$?"` read the exit of the pipeline's `tail` as `0`. Re-run with `set --` / `"$@"` (`argc=10`) all three gates genuinely pass. This is the third time this shape is recorded in this repo's worker memory; printing `argc` before trusting a multi-file gate is the cheap habit.

### Temp test verification

**No temp test was created this pass, and none was needed.** `docs/builder/temp-tests/r2b-review/` was not created. Pass 2's diff changes no executable byte anywhere — the AST identity across all eight comment-only files is the proof — so there is no assertion whose distinguishing power could be in question, no boundary to mutate, and nothing a temp row could measure that the identity does not already settle. Pass 2 declined to create `…/r2b/` for the same reason and said so; I agree, and an empty directory would be a false trace for `scripts/clean_up.py`. Pass 1's temp artifacts under `docs/builder/temp-tests/r2/` and `…/r2-review/` are left in place, gitignored.

### Notes for Worker 1 (spec reconciliation)

1. **The parent-count-independence census is three pins, not two — see `### Low 5`.** Pass 2's item 1 offers a `## Test plan` sentence built on "two live two-cardinality pins"; the third is `examples/fakeshop/test_query/test_library_api.py::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` (3 and 8 **empty** parents), and it is the only one exercising Decision 5's "Parents with no related rows" edge case across cardinalities. Recommended wording if the sentence is written at all: "The general parent-count-independence property is earned by three live two-cardinality pins (3 and 10 genres; 2 and 4 genres; 3 and 8 empty parents); every other fixed-cost pin states an absolute count at its own seeded cardinality and defers the general property to them." Tree-wide measurement backing it: **11 occurrences across 9 test functions** at `HEAD` in the two writable files, **4 across 3** now.
2. **`Escalated:` the retired-`Decision 6`-vocabulary population extends outside R2's partition.** `### Low 4` covers the one site inside it. Outside it: `django_strawberry_framework/optimizer/lateral_fetch.py #"The walker-owned fallback shapes (sidecar, SKIP, DISTINCT, malformed slice, unwindowable join)"` and `django_strawberry_framework/optimizer/nested_planner.py #"# (b) Fallback shapes detectable before any queryset is built"`. The `lateral_fetch.py` one repeats the same stale five-item enumeration `### Low 4` faults, one word different (`join` for `partition`). Neither carries a `Decision 6` reference, so neither is a broken citation in the strict sense, and neither is in any declared partition. Resolution paths, both the maintainer's: fold them into a follow-on `.py` cohort with its own partition, or accept "fallback shapes" as surviving informal module vocabulary and record in Decision 6 that the renamed arms are also called fallbacks in source prose. Worker 3 does not hold R2 at `revision-needed` on either.
3. **Pass 2's recommended Decision 6 amendment (its item 2) is worth taking, and this pass is the evidence for it.** It proposes one sentence in Decision 6's introduction: source comments cite the arms by name, never by ordinal, so a renumbering cannot silently falsify a citation. `### Low 4` is the case for widening it by one clause — **nor by heading text**. Both retired spellings produced live rot this cycle, the ordinal at three sites and the heading string at one, and only the ordinal had a sweep pointed at it.
4. **`spec-033 Decision 9`'s single `.py` citation survives the rename intact.** `tests/optimizer/test_walker.py #"Helper-move (spec-033 Decision 9) no-regression lives in test_extension.py (unmodified)"` — the renamed Decision 9 still states a helper consolidation, and the citation names no ordinal and no heading text. Nothing to do; recorded so the reconciliation does not go looking.
5. **The `Decision 11` / `Decision 4` split pass 1 accepted is stable after pass 2**: 2 and 30 occurrences respectively, whitespace-normalized over all tracked `.py` files, with the single-line grep now agreeing with the normalized sweep on both tokens (it did not at `HEAD`: 9 vs 10). If Slice 2 rewrites Decision 11's module map, the two surviving sites are still `connection.py #"now lives in ``optimizer/plans.py``"` and `optimizer/plans.py::ends_in_unique_column`.
6. **One count in pass 2's report does not reproduce and should not be propagated.** `### Re-measured populations` states "`spec-033 Decision 6` is cited at **27** further `.py` sites (`optimizer/nested_planner.py` 7, `optimizer/walker.py` 4, `optimizer/lateral_fetch.py` 1 …)". My whitespace-normalized occurrence count over all tracked `.py` gives **24 total**, i.e. 21 outside `nested_fetch.py`, distributed `tests/optimizer/test_walker.py` 11, `optimizer/walker.py` 4, `optimizer/nested_planner.py` 2, `test_library_api.py` 2, `connection.py` 1, `optimizer/lateral_fetch.py` 1. The `walker.py` and `lateral_fetch.py` figures agree; `nested_planner.py` does not under either the `spec-033`-prefixed spelling (2) or the bare one (6). The **conclusion** pass 2 drew from the 27 — that every one of them reads correctly against the current spec — I independently confirm across all 24, so nothing is wrong in the tree. But the number itself is not reproducible and no spec sentence should be written against it. Pass 1's own notes and Worker 2's pass-1 notes were read; nothing else in either is contradicted by this review.

### Review outcome

`revision-needed`.

**Nothing about pass 2's work is wrong, and none of the following is to be re-litigated on the re-pass:** all four Low 1 sites are corrected in repair 5's own shape and every number in the new prose checks out against the body; all three genuinely two-cardinality sites are untouched; "measured rather than assumed" is gone and the alias comment is true under a from-scratch AST measurement of all 17 aliases; Low 3's three rewrites restate Decision 6's arms 6 and 9 as the spec states them today, by name rather than ordinal; **no executable byte changed anywhere in pass 2** under an independently-built instrument asserted failable in four directions; the two pass-1 executable repairs are node-index-identical to their accepted state; the six untouchable pass-1 files hold their hashes; `test_products_api.py` is byte-identical to `HEAD`; no mutation is live; no file was written outside the partition; no escalation was acted on; the hot-path number exists for both hot files and reproduces digit for digit; the floor `none` declaration is not falsified by the diff; and all three suite results reproduce exactly.

Two items are open. Both are population misses of one site each, both were caused by a phrase grep where a vocabulary class was needed, and **neither touches an executable byte**.

1. **Low 4** — repair or explicitly defer `django_strawberry_framework/optimizer/nested_fetch.py #"the Decision-6 fallback shapes"` (`django_strawberry_framework/optimizer/nested_fetch.py:7`), the fourth Decision 6 citation in the file Low 3 repaired. It cites Decision 6 by its retired heading, enumerates five items where the current Decision has nine arms, and attributes to the private planner a set the spec sites partly on `utils/connections.py`, `optimizer/join_taxonomy.py`, and on `::unwindowable_child_queryset_reason` in this same module. The pass's own file-scoped count read `Decision 6` **3** where the file carries four, because this one is spelled `Decision-6`. A recorded deferral naming the site closes it equally.
2. **Low 5** — correct or explicitly defer `### Notes for Worker 1` item 1's census: it names **two** two-cardinality parent-count pins where there are **three**, the third being `examples/fakeshop/test_query/test_library_api.py::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` (3 and 8 empty parents), which is the only one covering the empty-parent shape. No `.py` edit is required or wanted — the note is what is wrong, and it is offered to Worker 1 as the number to write a spec sentence against.

Re-run the eight-file `ast.dump` identity afterwards; a Low 4 repair must leave `django_strawberry_framework/optimizer/nested_fetch.py` at `302fbecdcc8d`, and Low 5 touches no `.py` at all.

---

## Review (Worker 3, pass 3)

A fresh reviewer with no in-context memory of passes 1-3. This section grades **pass 3's diff** - the one-file addendum that closed the pass-2 review's `#### Low 4` and `#### Low 5` - and confirms it disturbed nothing passes 1 and 2 established. The two prior review sections (`## Review (Worker 3)`, `## Review (Worker 3, pass 2)`) and all build-report sections are intact and are not re-litigated except where pass 3 could have regressed them.

Every number below was measured in this pass with an occurrence-counting, whitespace-normalized instrument over the 434 tracked `.py` files (`git ls-files '*.py'`; 0 untracked `.py` exist, so the population is complete). Where the text is a **comment**, the instrument also joins `\n\s*#\s?` continuations before matching - see `### Low 9`, which is the grammar that beat my own first sweep.

### Mutations pre-registered before they were made

**None on disk.** Pass 3's diff introduces no boundary, guard, gate or rejection path - it changes no executable byte anywhere - so the failability re-run floor (`worker-3.md` `### Reading is necessary, not sufficient: the failability proof`) is met by an **empty re-run set**, which is legal here because the diff introduces no boundary that meets the floor. The obligation pass 3 owes instead is the **inverse** proof, and that is what I rebuilt.

One control below mutates `django_strawberry_framework/optimizer/nested_fetch.py` **in memory only**; the on-disk bytes and mtime were asserted unchanged after it ran. No source file was written by this review. No `git stash`, `git checkout`, `git restore` or `git worktree` was used at any point; `HEAD` copies were extracted with `git show HEAD:<path>` into a scratch tree **outside** the repository.

### The inverse proof, rebuilt from scratch under a fourth instrument

Written from the recorded algorithm, not from pass 3's script (which I did not read): parse with `ast`, strip every module / class / function docstring (replacing an emptied body with `Pass`), `ast.dump` (line numbers omitted), digest = first 12 hex of the dump's sha256.

**Eight synthetic controls, all asserted before any file was compared** - four of them are the four pass 3 recorded, four are additional directions:

```
executable change VISIBLE          x = 1  vs  x = 2
comment change invisible           # a    vs  # b
docstring swap invisible           """A"""vs  """B"""
body under a docstring VISIBLE     return 1 vs return 2
deleted statement VISIBLE          return 1 vs pass
statement reorder VISIBLE          a=1;b=2  vs  b=2;a=1
operator flip VISIBLE              and    vs  or
added argument VISIBLE             f(x)   vs  f(x, y)
-> 8/8 asserted OK
```

**Must-see control on a real multi-thousand-line input, not a synthetic string:** `tests/optimizer/test_walker.py` at `HEAD` (`5e9799a71eee`) versus the working tree (`1311b82c4ceb`) - a pair I know differs executably because pass 1's repair 7 rewrote that file's m2m shared-child scenario. The instrument sees it. **A blind instrument would have printed `True` for every row of the table below**, so this assertion is what makes the table evidence.

Result over the whole ten-file R2 partition, `HEAD` versus working tree:

| File | `HEAD` | worktree | equal |
|---|---|---|---|
| `tests/test_connection.py` | `e10df5d5f0a3` | `e10df5d5f0a3` | **True** |
| `tests/optimizer/test_plans.py` | `809ebc71d3d8` | `809ebc71d3d8` | **True** |
| `tests/optimizer/test_walker.py` | `5e9799a71eee` | `1311b82c4ceb` | False (pass 1 repair 7, executable by design) |
| `tests/optimizer/test_extension.py` | `349aa5422d06` | `bd92ca53429b` | False (pass 1 repair 6, executable by design) |
| `django_strawberry_framework/connection.py` | `ecc47449f5ec` | `ecc47449f5ec` | **True** |
| `django_strawberry_framework/optimizer/plans.py` | `8fb1b399480f` | `8fb1b399480f` | **True** |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | **True** |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | **True** |
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | **True** |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `302fbecdcc8d` | `302fbecdcc8d` | **True** |

**All four digests pass 3 recorded reproduce digit for digit** - `e357f45d6f2a`, `b5918390baa8`, `615fe2fe2be2`, `302fbecdcc8d` - now under a fourth independent instrument, and the first three are additionally the values pass 1, pass 2 and the pass-2 reviewer each recorded. Two of these files are declared hot path (`optimizer/walker.py`, `optimizer/nested_fetch.py`) and both hold.

The table is stated against `HEAD` rather than against a pass-3 before-copy on purpose: it is the **stronger** statement. `HEAD` has moved since pass 3 wrote (`db7ecb1a` -> `b759c72f`, concurrent dependency and lint commits), and no concurrent commit touched any partition file, so `HEAD` is still the pre-cohort baseline for all ten. Eight of the ten are executably identical to `HEAD`; the two that are not are exactly pass 1's two declared executable repairs. **There is therefore no executable byte anywhere in this cohort's three passes that is not one of those two, and nothing pass 3 did moved either of them.**

### The two controls pass 3 reported, reproduced

Both were re-run against `nested_fetch.py` specifically, in memory:

- **The anchor-abort.** The generic live-file control's anchor `import pytest` is confirmed **absent** from `nested_fetch.py`, so an anchor-presence assertion must raise rather than skip. This is the behavior worth confirming: a control whose setup silently no-ops reads exactly like a passing proof, and this cohort has already been bitten once by a blind confinement script (pass 1). Firing loudly is correct.
- **The dedicated control.** `from __future__ import annotations` asserted present *before* mutating; a `_PROBE_SENTINEL = 1` insert after it changes the digest `302fbecdcc8d` -> **`4e4ee66b45aa`**. Pass 3 recorded exactly this pair. Reproducing the *mutant* digit for digit, not only the clean one, means my instrument and pass 3's are algorithmically identical rather than merely agreeing on a null result. On-disk bytes and mtime asserted unchanged after the control: **True**.

### Verdict per finding

#### Low 4 - `nested_fetch.py`'s module-docstring ownership sentence: **closed, and the judgement is right**

I graded the judgement, not the landing. `### Decision 6 - Refusal arms, divergent aliases, hints, and scalar-only connections` was read directly from `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, and every ownership claim was traced in source rather than taken from pass 3's account.

**Every arm the new sentence claims for the planner is decided in `optimizer/nested_planner.py`, verified in `::plan_connection_relation`'s own body** (the original defect was an ownership claim taken on trust, so this is the check that matters):

| Claimed arm | Decided at | Spec arm |
|---|---|---|
| an unresolvable field map | `::plan_connection_relation #"if django_field is None:"` and `#"if django_field.related_model is None:"` | 8 |
| conflicting per-key argument payloads | `::plan_connection_relation #"if response_key_arguments_conflict(sel):"` | 4 |
| `OptimizerHint.SKIP` | `::plan_connection_relation #"if hint_is_skip(hints_map.get(relation_field_name)):"` | 5 |
| an unwindowable relation kind | `::plan_connection_relation #"if not join.windowable:"` | 7 |
| sidecar input | `::_divergent_key_windows #"sidecar arguments"`, same module | 1 |

**The three it disclaims are decided where it says.** `utils/connections.py::derive_connection_window_bounds` carries two `raise UnwindowableConnection` sites (spec arm 2). `optimizer/join_taxonomy.py::classify_relation_join` returns the `windowable` flag and its own docstring says "the caller decides" (spec arm 7). `unwindowable_child_queryset_reason` is in `nested_fetch.py` itself (spec arm 6). The decides / classifies split the sentence draws is **the spec's own verb choice**, not a hedge: arm 7 reads "on a `join.windowable` of `False` from `classify_relation_join`". The old sentence's contradiction with the sibling docstring eighty lines below is gone.

The two arms the sentence does not name (arm 3 `last: 0`, arm 9 the every-key strategy refusal) are both decided in the planner's own module, so `among them` covers them correctly rather than concealing a miss.

**Dropping the Decision citation is right, and it is right for a stronger reason than the one recorded.** Pass 3's argument - a module-ownership boundary reads correctly without a spec reference, and a reference invites re-checking a deliberately open list - holds. But the decisive point is mechanical: the rewrite **replaced a citation no gate can read with two that a gate does read**. `scripts/check_citations.py` matches `([\w][\w./]*\.py)::([A-Za-z_][\w.]*)`; the module docstring carried **7** such citations at `HEAD` and carries **9** now, the two added being `utils/connections.py::derive_connection_window_bounds` and `optimizer/join_taxonomy.py::classify_relation_join`. `uv run python scripts/check_citations.py --check` -> `OK: 819 citations resolve (738 in 431 .py files, 81 in KANBAN.md)`. A `Decision 6` reference would have been prose no instrument validates; the two symbol references break loudly if either function moves or is renamed. This is a sentence that reads correctly without a reference **and** gained two better ones - not a dodge.

One incompleteness, cosmetic and recorded rather than held: the negative half names `derive_connection_window_bounds` but not its keyset twin `::derive_keyset_window_bounds`, which spec arm 2 names in the same breath and which is the site that raises for every backward keyset shape. The sentence is true as written (the named function does raise it); it is one clause short of the spec's own statement. `### Notes for Worker 1` item 3.

File-scoped post-state, whitespace- and hyphenation-normalized: `Decision 6` **3** (the three arm-named citations pass 2 wrote), `Decision-6` **0**, `shape <N>` **0**, `fallback shapes` **0**. All reproduce.

#### Low 5 - the census that was short by one: **closed; all three pins verified by body**

I read all three bodies rather than accepting the corrected number, because accepting a corrected count on trust is the same defect one level up.

| Pin (`examples/fakeshop/test_query/test_library_api.py`) | line | cardinalities | comparing assertion |
|---|---|---|---|
| `::test_nested_books_connection_fixed_query_count` | 5284 | `_run(3)`, `_run(10)` | `three_count == ten_count`; `three_count == 2` |
| `::test_list_relation_and_connection_sibling_coexist_live` | 5664 | `_run(2)`, delete every seeded row, `_run(4)` | `two_count == four_count`; `two_count == 3` |
| `::test_nested_empty_parent_serves_zero_total_count_no_fallback_live` | 5823 | `_run(3)`, `_run(8)`, every parent childless | `three_count == eight_count` |

All three genuinely run two cardinalities and compare them. The third seeds books carrying **zero** genres and is the only one exercising the empty-parent shape, so it is the least redundant of the three - as pass 3 says. `### Notes for Worker 1` item 1 now names all three with correct cardinalities and correct assertions.

**The recommended sentence is true as written**, with one scoping caveat for whoever writes it into the spec (`### Notes for Worker 1` item 2). "Three live two-cardinality pins, one of which covers the empty-parent shape" is exact. "Every other fixed-cost pin states an absolute count at its own seeded cardinality and defers the general property to them" is exact **for this contract's pins**: `test_nested_books_connection_fixed_query_count` is named at **7** sites in 2 files - its own `def`, plus **6** deferral pointers (4 in `test_library_api.py`, 2 in `tests/test_relay_connection.py`), which is precisely the six sites passes 1 and 2 corrected. Read tree-wide, though, the package has many `django_assert_num_queries` / `CaptureQueriesContext` pins that neither claim the property nor defer it, so the sentence needs "every other **nested-connection** fixed-cost pin" when it lands in prose.

**The instrument reproduces and so does its conclusion.** Pass 3's vocabulary-class-inside-a-character-window pattern, run tree-wide over all 434 tracked `.py`:

```
(independent|independence|regardless|irrespective|no matter|does not scale
 |does not grow|constant|flat in|unchanged by|same for)[^.]{0,60}?parents?\b
| parents?\b[^.]{0,60}?(same class)        (case-insensitive, whitespace normalized)
```

I get **14** matches in 10 files where pass 3 recorded 15; the one-match difference is entirely inside the bucket both of us read and discarded as unrelated, and I state my own number rather than adopting theirs. What matters is identical: **exactly 5 matches land in `test_library_api.py`, and all 5 resolve to the three pins above** - lines 5285, 5288 and 5335 in `::test_nested_books_connection_fixed_query_count`, line 5678 in `::test_list_relation_and_connection_sibling_coexist_live`, line 5843 in `::test_nested_empty_parent_serves_zero_total_count_no_fallback_live`. No fourth pin is hiding. (Pass 3's parenthetical "two of them match twice" is one off in the other direction: the first pin matches three times, the other two once each. The resolved set is what the finding turns on, and it is right.)

#### The two re-measured figures: **both settled, one against the pass-2 reviewer**

- **`spec-033 Decision 6` = 27 total, 24 elsewhere.** Reproduced exactly, and **file by file**, with hyphenation normalized (`Decision-6` folded in) and attribution by nearest `spec-0NN` marker within 70 characters: `tests/optimizer/test_walker.py` 12, `optimizer/nested_planner.py` 4, `optimizer/walker.py` 4, `optimizer/nested_fetch.py` 3, `test_library_api.py` 2, `connection.py` 1, `optimizer/lateral_fetch.py` 1 = **27**, minus the 3 in `nested_fetch.py` = **24 elsewhere**. **Pass 3 is right and the pass-2 reviewer's 24/21 was wrong**, and the arithmetic says exactly why: that reviewer did not normalize hyphenation, and `nested_planner.py` carries 2 `Decision-6` occurrences (4 vs its 2) while `tests/optimizer/test_walker.py` carries 1 (12 vs its 11). 2 + 1 = the 3-occurrence gap, with no residue. The word "further" was the false part of the original sentence, exactly as pass 3 records.
- **`Decision-<N>` hyphenated = 38 occurrences in 25 files.** Reproduced exactly, both figures.
- **`Decision-6` = 8 occurrences.** The occurrence count reproduces exactly, and so does every entry of the distribution. The **file** count does not - see `### Low 6`.

#### The deliberately-left simile: **I agree, and it should be left**

`tests/optimizer/test_walker.py::test_refusing_nested_fetch_strategy_leaves_selection_unplanned #"behaves exactly like the other fallback shapes"` (`tests/optimizer/test_walker.py:5137`). Read in full: the docstring's own sentence at `:5135` reads "The seam's spec-033 Decision 6 discipline (``optimizer/nested_fetch.py``)", which is a correct citation of the current Decision, and the retired noun appears two lines later inside a simile that resolves against sibling scenarios without consulting the spec. It carries no ordinal, no heading reference, and no Decision number of its own. Rewriting it would put a cosmetic churn into the one partition file carrying an executable repair this cohort must not disturb. **Deliberate, recorded, and the right call.** My only amendment is scope: it is not a singleton to be weighed on its own, it is 1 of 13 `fallback shape(s)` occurrences tree-wide, and it should be retired with them or not at all (`### Low 7`, `### Notes for Worker 1` item 4).

### Dispatched findings checklist - all twelve boxes walked

Each tick was verified against the `HEAD`-versus-worktree diff, not against the build reports' prose. No box is ticked without a matching landed fix, and no box is unaddressed without a recorded deferral.

1. **[x]** `tests/test_connection.py` - `TODO(spec-033 Slice 1-2)` **1 -> 0**; `#"root-connection no-regression fence"` present **1**; zero `TODO(` anchors remain in the file. Landed.
2. **[x]** cursor-parity re-siting - `spec-033 Decision 11` **3 surviving occurrences in 2 files**, and I read all three: `connection.py #"now lives in ``optimizer/plans.py`` (spec-033 Decision 11 sites the hoist"`, `optimizer/plans.py::ends_in_unique_column`, `optimizer/plans.py::effective_connection_order`. **Every one is a module-map / hoist-location claim - which is what Decision 11 states - and every one names Decision 4 for the invariant in the same sentence.** No cursor-parity claim survives on Decision 11. `spec-033 Decision 4` is now at 32 occurrences in 9 files. Landed and complete. (A fourth, *unattributed* `Decision 11` in the same `connection.py` docstring is spec-030's and was correctly not in this box's ten - `### Low 9`.)
3. **[x]** `optimizer/walker.py` alias comment - `HEAD`'s vague "keep this module's bodies ... working unchanged" **1 -> 0**, replaced by the per-alias reader inventory **0 -> 1**. The 17 aliases are unchanged (8 + 9, byte-identical name lists at `HEAD` and now), so the escalated deletion was not performed. Landed.
4. **[x]** retired-probe / wrong-mechanism docstrings - the five named sites plus the one unnamed parallel site are corrected in `tests/test_relay_connection.py` and `test_library_api.py`. Landed.
5. **[x]** parent-count-independence, pass-1 half - `#"independent of parent"` in `tests/test_relay_connection.py` **2 -> 0**, in `test_library_api.py` **3 -> 1**, the survivor being `::test_list_relation_and_connection_sibling_coexist_live`, which earns it. `ABSOLUTE` **0 -> 2** and **0 -> 4** respectively. Landed. `test_products_api.py`'s three sites needed no edit and got none.
6. **[x]** `tests/optimizer/test_extension.py` memoization order-independence - executable, present, digest differs from `HEAD` as designed. Landed.
7. **[x]** `tests/optimizer/test_walker.py` m2m shared child - executable, present, digest differs from `HEAD` as designed. Landed.
8. **[x] Low 1** - all four sites carry pass 1's correction shape and point at `::test_nested_books_connection_fixed_query_count`; 6 deferral pointers measured. Landed.
9. **[x] Low 2** - `#"measured rather than assumed"` is **0** in `optimizer/walker.py`. Tree-wide it survives exactly **1** time, in `django_strawberry_framework/_request_body.py #"Seekability, measured rather than assumed"`, an unrelated module's section heading about stream seekability, not provenance prose about a change, out of partition and pre-existing. Landed.
10. **[x] Low 3** - the three `::unwindowable_child_queryset_reason` / `::NestedConnectionStrategy` citations re-worded, all naming the arm by content. `shape <N>` in the file **1 -> 0**. Landed.
11. **[x] Low 4** - graded above. Landed.
12. **[x] Low 5** - `### Notes for Worker 1` item 1 names all three pins. Landed (note-only, no `.py` edit, and `nested_fetch.py` is still `302fbecdcc8d` as pass 2's review required).

### No-regression obligations

- **`examples/fakeshop/test_query/test_products_api.py` is byte-identical to `HEAD`** - `cmp` against `git show HEAD:` into a scratch path outside the repository is silent, and `git diff HEAD --` is empty. It is absent from `git status --short`; a concurrent session committed the unrelated edit that was dirty at pass 3's start, which is that session's work, not this cohort's.
- **All three escalations are untouched.** (1) `django_strawberry_framework/types/resolvers.py` has an empty diff against `HEAD`, so `::_check_n1`'s probe shape did not move. (2) `optimizer/plans.py::window_partition_for_prefetch` is still defined and still has **zero production callers** - every reader is a test or a comment in `exceptions.py` / `join_taxonomy.py`. (3) The ten dead `walker.py` aliases were **not** deleted: the module-level alias name lists at `HEAD` and now are identical.
- **Both review sections and all three build reports are intact.** `## Plan (Worker 1)` :10, `## Build report (Worker 2)` :34, `## Review (Worker 3)` :232, `## Build report (Worker 2, pass 2)` :408, `## Review (Worker 3, pass 2)` :713, 1036 lines, and the pass-2 review's `### Review outcome` still reads `revision-needed` as it did when written. `Status:` is flipped to `built` at :4. Nothing was clobbered. The **placement** of pass 3's own report is a finding - `### Low 8`.
- **Recorded suite results, all reproduced exactly, every run with `--no-cov` and no `--cov*` flag anywhere:**
  - `uv run pytest tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov -q` -> **1005 passed**
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov -q` -> **224 passed**
  - `uv run pytest tests/ --no-cov -q` -> **5967 passed, 40 skipped**
- **Gates re-run on the one file pass 3 wrote:** `uv run ruff format --check` -> `1 file already formatted`; `uv run ruff check` -> `All checks passed!`; `uv run python scripts/check_trailing_commas.py --check` -> silent pass; `LC_ALL=C grep -c '[^ -~\t]'` -> **0**.
- **No live mutation and no `ACTIVE-MUTATION.json`** anywhere in the tree. The one control that mutates does so in memory and asserts the on-disk bytes and mtime unchanged.
- **No source line this cohort wrote carries a line number, a review-round id, a finding id, or a build-plan step.** The `path::Symbol` and `path #"substring"` forms are the only source references, and the citation gate resolves all 819 of them.

### High:

None.

### Medium:

None.

### Low:

Five, all cosmetic, none touching an executable byte, and **none of them a reason to hold this cohort**. Three (`Low 6`, `Low 7`, `Low 9`) are population or count residue with a named owner in `### Notes for Worker 1`; one (`Low 8`) is an artifact-structure observation; one (`Low 7`) also names a live site in a file this cohort repaired.

#### Low 6 - the `Decision-6` file count is self-falsified by its own adjacent enumeration

`docs/builder/bld-033-review-2-py_comment_repair.md` `### Low 5 - the two measurements that did not reproduce` states `Decision-6` occurs "**8** times in 6 files after this pass's repair (`optimizer/nested_planner.py` 2, `tests/test_relay_connection.py` 3, `utils/connections.py` 1, `tests/optimizer/test_extension.py` 1, `tests/optimizer/test_walker.py` 1)".

The enumeration lists **five** files and sums to 2+3+1+1+1 = **8**. My independent measurement gives **8 occurrences in 5 files**, matching the distribution entry for entry. The occurrence count - the load-bearing one, and the one the finding turns on - is right; the file count contradicts the list printed beside it.

Why it is only Low: nothing depends on "6 files", and the number is not handed forward - `### Notes for Worker 1` never repeats it. Why it is worth writing down at all: this is the same shape as the defect the section is *reporting* (a count right in its digits, wrong in its subject), and the falsifying evidence was already in the sentence. **Recommended change:** none required in source; if the section is ever quoted, quote "8 occurrences in 5 files".

#### Low 7 - the retired `fallback shapes` noun survives 13 times in 6 files, once inside the file pass 3 repaired, and the sweep that cleared it sought only the plural

`django_strawberry_framework/optimizer/nested_fetch.py:214` (`::NestedConnectionRequest`, module docstring of the dataclass) reads `#"Built only AFTER every strategy-independent fallback shape has been ruled out"`. Pass 3's own `### Low 4 - validation, identity, and hot-path record` records a "Retired-vocabulary re-sweep of the file, whitespace-normalized: `fallback shapes` **0**", which is true for the **plural** and clears a file that still carries the **singular**.

The wider claim is also off in its subject: `### Low 4` states "A tree-wide `.py` sweep for the phrase found **3** occurrences before this edit and **2** after - the two remaining are outside this pass's writable partition." Measured tree-wide over all 434 tracked `.py`:

- plural `fallback shapes`: **4** before, **3** after. The third survivor is `tests/optimizer/test_walker.py #"behaves exactly like the other fallback shapes"` - **inside** the partition, and pass 3 names and reasons about it two paragraphs later. The sweep's number silently excluded a site the same section discusses.
- singular *and* plural `fallback shape(s)`: **13 occurrences in 6 files** - `optimizer/nested_planner.py` 4, `optimizer/nested_fetch.py` 1, `optimizer/lateral_fetch.py` 1, `tests/optimizer/test_walker.py` 3, `tests/test_relay_connection.py` 3, `tests/optimizer/test_nested_fetch.py` 1.

**Why it is Low and not Medium: no comment is false.** "every strategy-independent fallback shape has been ruled out" is a true statement about the request's construction order, and none of the 13 except the one in `### Low 8`'s sibling finding carries a Decision reference. This is retired *vocabulary*, not broken *citation*. **Recommended change:** none inside this cohort; retire the noun tree-wide in one pass or accept it as informal module vocabulary, as a single decision covering all 13. `### Notes for Worker 1` item 4.

#### Low 8 - pass 3's build report is nested inside pass 2's and placed before the review it answers

`docs/builder/ARTIFACT.md` `## Re-pass sections` is explicit: "Each Worker 2 re-pass appends `## Build report (Worker 2, pass <N>)` at the same top level (NOT nested)... The artifact reads as a linear pass / review / pass / review sequence; never edit prior entries."

Pass 3's work is recorded as `### Low 4 - the module docstring's ownership sentence`, `### Low 4 - validation, identity, and hot-path record` and `### Low 5 - the two measurements that did not reproduce` at H3, **inside** `## Build report (Worker 2, pass 2)` (:408) and **above** `## Review (Worker 3, pass 2)` (:713), which is the review those sections answer. It also edits two prior-entry passages in place - pass 2's `### Re-measured populations` figures and its `### Notes for Worker 1` item 1.

**Why it is only Low.** Nothing is lost and nothing is concealed: each in-place correction is disclosed with its original wording and its defect in `### Low 5`, the Notes correction was the literal instruction Low 5 dispatched, and the pass-2 review is completely intact. The cost is legibility - a reader walking the file top-down meets pass 3's fix before the finding that asked for it, under a heading naming pass 2. **Recommended change:** none worth a fourth round-trip. Worker 1 should read `### Low 5` alongside pass 2's `### Re-measured populations`, because the latter now carries pass-3 text under a pass-2 heading.

#### Low 9 - a correct bare `Decision 11` became ambiguous *because of* this cohort's adjacent re-siting

`django_strawberry_framework/connection.py::_finalize_queryset #"the connection field's own cooperation point, Decision 11"` (`django_strawberry_framework/connection.py:1581`, step 6 of the numbered pipeline docstring).

That reference is **correct**: `docs/SPECS/spec-030-connection_field-0_0_9.md` `### Decision 11 - The connection field owns its optimizer cooperation point` is exactly what the sentence claims. But it carries no `spec-0NN` prefix, and box 2 changed step 5 of the *same docstring*, two list items above, from `spec-033 Decision 11` to `spec-033 Decision 4`. A reader now meets an explicit `spec-033 Decision 4` and then a bare `Decision 11` in one docstring, and will resolve the bare one against spec-033, whose Decision 11 is a module map that says nothing about cooperation points.

It was correctly outside box 2's ten sites (it never made a cursor-parity claim), so this is not an unaddressed dispatched finding. It is residue this cohort's own edit created. **Recommended change:** one word - `spec-030 Decision 11` - in a comment, which cannot move `connection.py` off `ecc47449f5ec`. `### Notes for Worker 1` item 5.

### DRY findings

None requiring a change, and no existence challenge this pass: the diff adds no helper, registry, token or indirection layer - it adds no code at all.

Cross-cohort duplication is not applicable in the usual sense (R2 is one cohort), but the convergent-shape check does apply to the *prose* this round produced and it comes out clean: the six parent-count deferral sites now use one correction shape (absolute count + seeded cardinality + a pointer at the two-cardinality pin), which is a consolidation rather than six near-copies of a claim. The four re-worded `Decision 6` citations likewise all use one shape (name the arm by content, never by ordinal).

Recorded from `scripts/review_inspect.py` for the integration pass, not recommended for extraction: `optimizer/nested_fetch.py`'s repeated string literals are `select_for_update` x2, `distinct` x2, `windowed` x2. The first two are `::unwindowable_child_queryset_reason`'s reason strings, which the function's own docstring declares "stable, test/telemetry-friendly" - they are a wire contract, and hoisting them into constants would hide that. Left alone deliberately.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export list are unchanged. Consistent with `### Decision 11`'s "**Public surface: none.** Not one of the modules above is re-exported from the package root; the whole contract is internal."

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Verified rather than assumed: `git diff HEAD --stat` over `CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html` and `TODAY.md` is empty. The two spec files are Slice 2's and were read but not written by this review.

### Static helper use

`uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/nested_fetch.py --output-dir docs/shadow` - run, not skipped. Wrote `docs/shadow/django_strawberry_framework__optimizer__nested_fetch.stripped.py` and `…overview.md`. All four required sections walked; shadow line numbers are not cited anywhere in this review.

- **Django / ORM markers (14).** `QuerySet` / `Prefetch` / `OptimizationPlan` / `prefetch_related`, at original-source lines 74, 80, 137, 163, 170, 277, 299, 331, 332, 360, 364, 372, 394. **Not one sits on a line pass 3 changed** - the whole diff lives in the module docstring (lines 1-63), `::unwindowable_child_queryset_reason`'s docstring (84-121) and `::NestedConnectionStrategy`'s (263-273). This is the independent confirmation of the floor declaration below: no Django integration seam moved.
- **Control-flow hotspots (2).** `::unwindowable_child_queryset_reason` at :83, 52 lines / 6 branch nodes; `::attach_windowed_prefetch` at :297, 42 lines / 1 branch node. Both are unchanged executably (the AST identity is the proof), so both read exactly as they would at `HEAD`. Neither is near the file's next-largest structure; no consolidation candidate.
- **Repeated string literals (3).** Recorded above under `### DRY findings` for the integration pass.
- **Imports (18).** Five are function-local - `.lateral_fetch` at :184, `.single_parent_fetch` at :364, `.lateral_fetch` at :398 and :411, `..conf` at :426 - each with a comment naming the intentional import cycle it breaks. All five are pre-existing; the diff adds and removes none. No import-boundary finding.

### Hot-path budget verification

`optimizer/nested_fetch.py`'s fetch path is declared hot (per request, per resolver, per parent row) and `optimizer/walker.py`'s plan walk with it. **The number exists and reproduces as recorded**, which is the whole of my obligation here:

- metric: `ast.dump` of the docstring-stripped module. before / after / delta: `302fbecdcc8d` / `302fbecdcc8d` / **0** (`optimizer/nested_fetch.py`); `615fe2fe2be2` / `615fe2fe2be2` / **0** (`optimizer/walker.py`).
- For a comment-only edit the honest number **is** the demonstrated zero delta, and the identity is the record - a timing run would measure the harness, not the change. What makes this a record rather than an assertion is the must-see control: the same instrument reports a difference for `tests/optimizer/test_walker.py` and for a one-statement insert into `nested_fetch.py` itself (`302fbecdcc8d` != `4e4ee66b45aa`). No instruction was added to either path.

### Floor verification

Plan declares floor-verification scope `none`, and **the declaration is not falsified by the actual diff**, checked rather than accepted: no executable byte changed in any of the ten partition files beyond pass 1's two declared test repairs, and the static helper's Django/ORM marker walk above confirms no marker line moved in the hot module. No Django / Strawberry / channels integration seam is touched, so there is nothing to verify at the floor.

The shared `.venv` was not mutated: no `uv pip install` was invoked at any point in this review, and no version is stated from memory anywhere above. The supported floor per `docs/builder/BUILD.md` `## Floor verification` is Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0; no reading of `.venv`'s versions was needed, because a comment-only diff has no seam to check against them.

### What looks solid

- **The ownership rewrite is the strongest single edit of this cohort.** It replaced a false five-item closed list with an open list plus an explicit negative half, and the negative half is what does the work - it is what removes the contradiction with `::unwindowable_child_queryset_reason`'s own docstring eighty lines below, and it is what a reader needs in order to know the sentence is not exhaustive. Every one of its eight claims traces to source.
- **Dropping the Decision reference traded prose no gate reads for two symbol references a gate does.** That is a strictly better citation posture, and it is a generalizable move: when a sentence's content is *where something lives*, `path::Symbol` beats `Decision N` because one of them breaks loudly.
- **The anchor-absent control aborted instead of skipping.** This is the failure mode that has already cost this cohort one pass, and pass 3 hit it, reported the `AssertionError` text, and then built a dedicated control on an anchor the file actually has. Reporting a control that *fired* is worth more than a page of clean results.
- **Three numbers were re-derived from scratch and two were reported wrong by their own author, with unchanged conclusions stated separately from the corrected digits.** Separating "the number was wrong" from "the judgement it supported still holds" is exactly right, and it is why `Low 6` and `Low 7` are cosmetic rather than substantive.
- **The `27` figure settles against a reviewer, with the arithmetic to prove it.** Pass 3's number is right, the pass-2 reviewer's 24/21 was short by exactly the hyphenated spellings, and the 3-occurrence gap decomposes with no residue.
- **The two executable repairs from pass 1 are provably untouched**, against a `HEAD` that has moved twice under this cohort.

### Temp test verification

**No temp test was created and none was needed.** `docs/builder/temp-tests/r2c-review/` was not created. Pass 3's diff changes no executable byte, so there is no assertion whose distinguishing power is in question and no boundary to mutate; every claim in this review is settled by reading source against the spec, by an AST identity, or by an occurrence count. Creating an empty directory would leave a false trace for `scripts/clean_up.py`. Pass 1's temp artifacts under `docs/builder/temp-tests/r2/` and `…/r2-review/` are left in place, gitignored.

### Notes for Worker 1 (spec reconciliation)

Pass 2's and pass 3's own six notes stand; I re-derived every number in them and only item 6's `27` needed the correction pass 3 already made. Five additions:

1. **The parent-count census is confirmed at three pins by body-reading, not by count.** All three verified at `examples/fakeshop/test_query/test_library_api.py:5284` (3 / 10 genres), `:5664` (2 / 4 genres) and `:5823` (3 / 8 empty parents). Pass 3's recommended wording is safe to use.
2. **Scope the recommended `## Test plan` sentence to nested-connection pins.** "Every other fixed-cost pin states an absolute count at its own seeded cardinality and defers the general property to them" is exactly true of the **six** sites that name `::test_nested_books_connection_fixed_query_count`, which are the six this cohort corrected. It is not true of the package's `django_assert_num_queries` pins generally, which neither claim nor defer the property. Write "every other **nested-connection** fixed-cost pin".
3. **`### Decision 6` arm 2 names two sites; the repaired `nested_fetch.py` sentence names one.** The module docstring's negative half says a window the slice arithmetic cannot express "is raised by `utils/connections.py::derive_connection_window_bounds`"; the Decision adds "(and its keyset twin `::derive_keyset_window_bounds`)", which is the site that raises for every backward keyset shape. True as written, one clause short of the spec. Either add the twin to the source sentence or leave it - the maintainer's call, and no citation is broken either way.
4. **`Escalated:` the `fallback shapes` retirement is 13 occurrences in 6 files, not 2, and one of them is a live citation carrying both retired spellings.** Pass 3's item 4 names two out-of-partition sites; the population is wider, and it includes one site its list does not: `django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation #"for each Decision-6 fallback shape so the strictness contract still sees"`. That single site carries **both** spellings this cycle proved invisible - the hyphenated ordinal *and* the retired heading noun - and unlike the two pass 3 named, it **is** a Decision citation, so it is the closest surviving twin of the `### Low 4` defect. Full population: `optimizer/nested_planner.py` 4, `tests/optimizer/test_walker.py` 3, `tests/test_relay_connection.py` 3, `optimizer/nested_fetch.py` 1 (`:214`), `optimizer/lateral_fetch.py` 1, `tests/optimizer/test_nested_fetch.py` 1. Resolution paths, both the maintainer's: retire the noun across all 13 in one `.py` cohort with its own partition, or accept it as informal module vocabulary and record in `### Decision 6` that the renamed arms are still called fallbacks in source prose - but **fix `nested_planner.py::plan_connection_relation`'s docstring either way**, because it is a citation and the others are not. Worker 3 does not hold R2 at `revision-needed` on any of them: only one is in the partition (the `test_walker.py` simile, deliberately left with my agreement), and none is false.
5. **One bare `Decision 11` in `connection.py` should gain a `spec-030` prefix** - `django_strawberry_framework/connection.py::_finalize_queryset #"the connection field's own cooperation point, Decision 11"` (`:1581`). It correctly cites `spec-030-connection_field-0_0_9.md` `### Decision 11 - The connection field owns its optimizer cooperation point`, but box 2 re-sited a `spec-033 Decision 11` two list items above it in the same docstring, so the bare one now reads as spec-033's module map. One word, no executable byte, and `connection.py` stays at `ecc47449f5ec`. Detail in `### Low 9`.
6. **Pass 3's report is nested inside pass 2's `## Build report (Worker 2, pass 2)` and sits above the review it answers**, and it corrects two of pass 2's figures in place. Read `### Low 5 - the two measurements that did not reproduce` alongside `### Re-measured populations`; the latter now carries pass-3 text under a pass-2 heading. Detail in `### Low 8`.

### The counting lesson, with a fifth grammar

Four spellings defeated a measurement in this cycle: a **wrapped citation** (9 where it was 10), a **full-id spelling** (7 where it was 9), a **hyphenated** `Decision-6` (3 where it was 4), and an **intervening adjective** (2 where it was 3). A fifth defeated *me*, in this pass, and it is worth adding to the list because whitespace normalization does not cover it:

**A comment wrapped across two lines is not fixed by normalizing whitespace, because the continuation line carries a `#`.** My first box-3 sweep for `#"Readers of the underscore aliases below"` returned **0 at `HEAD` and 0 now** - which would have read as "the alias comment was never written" - purely because `re.sub(r"\s+", " ")` turns `Readers of the underscore\n    # aliases below` into `Readers of the underscore # aliases below`. Joining `\n\s*#\s?` **before** normalizing whitespace returns 0 at `HEAD` and 1 now, which is the truth. Docstrings do not have this problem; comments always do, and every retired-vocabulary sweep in this cohort ran over comment text.

Every count in this section was measured with that join in place, over occurrences rather than matching lines, with hyphenation folded, and - where the target is a claim rather than a token - with a vocabulary class inside a character window rather than a phrase list.

### Review outcome

`review-accepted`.

Both dispatched findings are closed on their merits, not merely landed. **Low 4's judgement is right**: every arm the new sentence claims for the planner is decided in `nested_planner.py`'s own body, the three it disclaims are decided where it says, the decides / classifies split is the spec's own, and dropping the `Decision 6` reference traded prose no instrument validates for two `path::Symbol` citations the shipped gate resolves - a strictly stronger citation posture, not a dodge. **Low 5's correction is right**: all three pins were verified by reading their bodies and their comparing assertions, the note names all three, and the recommended sentence is true as written subject to one scoping word.

Both re-derived measurements reproduce - `Decision-<N>` at 38 occurrences in 25 files exactly, and `spec-033 Decision 6` at 27 total / 24 elsewhere **file by file**, settling it against the pass-2 reviewer's 24/21 with arithmetic that decomposes the gap to the hyphenated spellings with no residue. All four `ast.dump` digests reproduce under a fourth independently-written instrument shown failable in ten directions, eight synthetic and two on real files, including reproduction of the *mutant* digest `4e4ee66b45aa` rather than only the clean one. The anchor-absent control genuinely fires rather than skipping. The hot-path number exists for both hot modules and reproduces as a demonstrated zero delta. Twelve of twelve checklist boxes have a matching landed fix; `test_products_api.py` is byte-identical to `HEAD`; all three escalations are untouched; both prior reviews and all three build reports are intact; no mutation is live; nothing was written outside the partition; the floor `none` declaration is not falsified by the diff; and all three suite scopes reproduce exactly (1005; 224; 5967 passed, 40 skipped).

Five Low findings are open and **every one is routed to `### Notes for Worker 1` rather than back to Worker 2**. None touches an executable byte, none makes any comment false, and none is a dispatched finding left unaddressed: two are count-subject residue inside this artifact (`Low 6`, `Low 8`), one is a tree-wide vocabulary population whose only in-partition member was deliberately and correctly left (`Low 7`), one is a one-word citation prefix in a file this cohort edited (`Low 9`), and the `Decision 6` arm-2 clause is a spec-versus-source completeness question the maintainer owns. This cohort has run three build passes; none of these is worth a fourth, and all five have a named owner at the integration pass.

**Closed.**

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
