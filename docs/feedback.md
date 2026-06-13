# spec-033 build review — post-implementation (2026-06-13)

Rigorous review of the *committed* spec-033 implementation (`4e536697` "Finish spec-033"
through `c8df425c`), working tree clean. Reviewed against
[`docs/spec-033-connection_optimizer-0_0_9.md`](spec-033-connection_optimizer-0_0_9.md)
and against the seven findings the spec absorbed in its Revision 2.

Scope read directly: `optimizer/walker.py` (recognition + `_plan_connection_relation` +
scalar projection), `optimizer/plans.py` (window helpers + `deterministic_order` +
partition), `connection.py` (resolver + fast-path consumption), `utils/connections.py`
(shared bounds), `types/resolvers.py::_check_n1`, `optimizer/extension.py` (cache-key
collection), `types/finalizer.py` / `types/definition.py` (slot + resolver call site).
Test coverage, the fakeshop conversion, and the doc sweep were audited by sub-agents and
spot-checked.

## Verdict

**The implementation is correct and high quality. No blocking correctness bug was found.**
The mechanism (windowed `Prefetch` under a reserved `to_attr`, annotation fast path,
pagination-aware cache key, strictness wiring) is faithful to the spec and in several
places *better* than the spec text it was built from. All seven Revision-2 findings are
genuinely addressed in code, not just in prose. The findings below are one
documentation-integrity gap (MED) and four LOW items (a spec/code message divergence and
three test-strength nits). None block the joint `0.0.9` cut.

## The seven prior findings — verification

| # | Finding | Status in code |
| --- | --- | --- |
| 1 | DISTINCT guard | **Done, and hardened.** `walker.py:1309` checks `child_queryset.query.distinct` and returns unplanned. The child is built against a throwaway `sub_plan` (`walker.py:1294`), so the distinct fallback leaks **no** child resolver keys / fk-id elisions / `cacheable=False` into the parent — the parent absorbs child metadata only on the success path (`walker.py:1312-1315`). Cleaner than the spec required. |
| 2 | Resolver `to_attr` identity | **Done.** `_build_relation_connection_resolver(target_type, accessor_name, relation_field_name, declaring_type)` (`connection.py:991`); `to_attr` keyed on `relation_field_name` (`connection.py:1052`), probe reads it (`connection.py:1056`). Finalizer passes `instance_accessor(field)` *and* `name` (`finalizer.py:436-454`). Reverse-FK-without-`related_name` fast path pinned with real DB models (`book` vs `book_set`). |
| 3 | Primary-type recognition | **Done + commented + tested.** Nested walk routes through `registry.get(model)` → primary type (`walker.py:192-198`); recognition reads the primary's `relation_connections` (`walker.py:205-234`). A divergent secondary type's connection is never window-planned and stays honestly flagged by strictness keyed under `type_cls` (`finalizer.py:449-453`). `test_secondary_type_relation_shapes_nested_recognition` pins it. |
| 4 | Cacheable / visibility interaction | **Done.** `has_custom_get_queryset` flips `sub_plan.cacheable=False` (`walker.py:1295`) and propagates to the parent only on success (`walker.py:1314-1315`). Slice-3 cache pins use non-visibility synthetic targets; Slice-5 uses the visibility library shape — different fixtures, as the spec now requires. |
| 5 | Products cardinality cap | **Done.** The over-cap fixture (`entries == 177 > _RELAY_MAX_RESULTS`) asserts the *capped* page with a `> _RELAY_MAX_RESULTS` guard so the fixture can't drift under the cap; full-set assertions are guarded `< _RELAY_MAX_RESULTS`. `ORDER BY pk` reasoned as a no-op where `id` is the pk. |
| 6 | Config read is safe | **Confirmed, no change needed.** `relay_max_results` is read-only off the schema config and passed explicitly into `derive_connection_window_bounds`, so plan-time and resolve-time caps are one number. |
| 7 | Cursor-parity invariant | **Done, single-sourced.** `derive_connection_window_bounds` (`utils/connections.py:84`) is the one `(offset, limit, reverse)` derivation both the walker and resolver call; `deterministic_order` (`plans.py:526`) is the one order rule both the plan-time window and `connection.py::_finalize_queryset` use (`ends_in_unique_column` hoisted, imported back). Decision 5 was reconciled during the build to the forward-row-number cursor scheme the code implements (spec line 302), so spec and code now agree. |

Two choices worth calling out as *improvements* over the spec as authored: the
throwaway-`sub_plan` isolation on the DISTINCT path (finding 1), and the forward-cursor
scheme for reversed `last`-only windows — `apply_window_pagination` keeps `_dst_row_number`
forward in both branches and uses a separate `_dst_row_number_reversed` only for the
plan-time `__lte` filter (`plans.py:627-657`), consumed as the uniform `_dst_row_number - 1`
(`connection.py:226-255`). This is the upstream-faithful, byte-parity-correct scheme; the
spec text was updated to match it.

## Findings

### F1 [MED — documentation integrity] The new module `utils/connections.py` is undocumented and contradicts Decision 11

The DRY refactor (`c8df425c`) extracted `django_strawberry_framework/utils/connections.py`
(the `ConnectionWindowBounds` / `derive_connection_window_bounds` cursor-parity contract and
the `CONNECTION_SIDECAR_KWARGS` family). The extraction is the **right call** — it makes the
plan/resolve window agreement a single source of truth, which is exactly what the
cursor-parity invariant needs. But the spec was never reconciled:

- Decision 11 still asserts **"no new module"** and enumerates only the six touched modules
  (spec ~lines 398-406); the Slice-checklist preamble repeats "this card adds **no new
  source module**" (spec line 50). Both are now false.
- [`docs/TREE.md`](TREE.md) does **not** list `utils/connections.py` in either `utils/`
  block (lines ~62-66 / ~133-137), and its `utils` summary line doesn't mention the
  connection-window-bounds / sidecar-kwarg contracts. TREE.md also asserts tests mirror
  source one-to-one; the twin `tests/utils/test_connections.py` **does** exist (good), but
  is likewise undocumented.

A build-deviates-from-its-own-spec gap, not a code defect. **Recommend:** update Decision 11
to record the justified module addition (or, if the bounded-extension pin is contractual,
note the exception explicitly), and add `utils/connections.py` + `tests/utils/test_connections.py`
to TREE.md. Cheap, and it keeps the DoD's "every edit lands in an existing module / no mirror
tension" claim honest.

### F2 [LOW — spec/code divergence] Strictness message names the relation field, not the generated connection field

`_check_n1` raises `OptimizerError(f"Unplanned N+1: {field_name}{suffix}")` where
`field_name` is the *relation* field name, so a flagged nested connection reads
`Unplanned N+1: books (not window-planned: selection carries filter/orderBy; resolving
per-parent)` (`resolvers.py:188`; pinned by `test_relay_connection.py:1660`). The spec's
Decision 8 example and Error-shapes section both specify the **generated** field name —
`Unplanned N+1: books_connection` / `<field>_connection` (spec ~lines 214, 365).

Code and tests are internally consistent, and using the relation-field vocabulary matches
what list relations emit and what the planned `resolver_key` is built from — a defensible
choice. But a consumer wrote `booksConnection` and gets told `books`, which is marginally
less actionable, and it diverges from the spec's literal text. **Recommend:** reconcile —
either update the spec to the relation-field form (lowest churn, keeps list/connection
messages uniform), or include the generated connection name in connection-kind flags. Decide
and pin it.

### F3 [LOW — weak test] `test_window_slice_from_variables` is near-tautological

The test passes an already-resolved `int` and asserts only `prefetch.to_attr ==
"_dst_books_connection"` — by its own docstring it exercises the *same* code path as the
literals test and asserts no offset/limit bound. The literals sibling
(`test_window_slice_from_first_after_literals`) does the real `"> 2"` / `"<= 5"` SQL-bound
assertion, so this is not a coverage hole — just a redundant test that doesn't independently
prove variable resolution drives the window. Optional: assert the resolved bound, or drop it
as redundant.

### F4 [LOW — weak test] `test_both_shape...` discards its `diff_plan_for_queryset` result

The B8-coexistence test asserts the plan shape well (`None` + `_dst_books_connection` both in
`to_attrs`, `prefetch_throughs == {"books"}`) but the closing `diff_plan_for_queryset(...)`
call discards its result — a no-error smoke check, not an assertion that the consumer
accessor prefetch and the `_dst_` window both *survive* the delta un-merged (the
exact-match/absorption claim the spec edge case makes). Optional: assert the delta keeps both
lookups.

### F5 [LOW — optional coverage] DISTINCT fallback count-correctness is implied, not executed

`test_distinct_child_queryset_left_unplanned_for_correct_total_count` firmly asserts the
no-window half (`planned_resolver_keys == ()`, no `_dst_books_connection` prefetch). The
"…for correct total count" half — that the per-parent fallback returns the right `totalCount`
for a `.distinct()` target — is structurally implied (falls through to the shipped pipeline)
but not executed anywhere, because no fakeshop target distincts. The spec only promised a
live pin "if any library/products target distincts," so this is acceptable. Optional: add a
package-level test with a `.distinct()` `get_queryset` asserting the fallback `totalCount` is
correct, so the test name's second clause is earned.

## Adjacent areas — assessed clean

- **Fakeshop (Slices 5–6):** Decision 10 honored exactly (four `DjangoConnectionField` attrs
  replace four list resolvers; no root Node fields, no `Meta.connection` added). The three
  `test_products_optimizer_*` pins keep **exact** `==` query counts through the connection
  wrapper (1 / 3 / 1). `test_library_api` fixed-query-count pins are real: run at 3 vs 10
  genres and assert `three_count == ten_count == 2`; nested `totalCount` adds zero queries;
  the visibility window honors `BookType.get_queryset`. No skip/xfail anywhere.
- **Cache key (Slice 3):** single unified AST traversal (`extension.py:105`), depth model
  correct (root pagination stays out at depth 0; nested collected at depth ≥ 1; fragment
  spreads keep spread-site depth), memoized per `id(operation)`. Superset rule and
  root-in-fragment / fragment-carried-nested cases all pinned.
- **Strictness (Slice 4):** three-condition guard exact (`planned` present, key absent,
  `to_attr` absent → flag); `connection_to_attr` probe correct (`resolvers.py:173-176`);
  union-publish prevents a nested fallback from clobbering the parent's planned set / fk-id
  elisions (pinned). List-relation `_check_n1` no-regression preserved.
- **Doc sweep (Slice 7):** GLOSSARY entry flipped to `shipped (0.0.9)` with the mechanism +
  fallback matrix + `.distinct()`/window-backend caveats; stale `DjangoConnectionField` /
  `Meta.relation_shapes` / Strictness / Plan-cache caveats swept; README / docs/README
  updated; CHANGELOG bullets under `[Unreleased]`; **no version bump** (`pyproject.toml` /
  `__version__` still `0.0.8`, Decision 12 honored). Companion terms CSV present.
- **No leftover staged seams:** no `TODO(spec-033 …)` / `NotImplementedError` anchors remain
  in package source.

## Net assessment

Build-ready. Fix **F1** (a one-paragraph spec edit + two TREE.md lines) and **decide F2**
(message wording) before the cut so the spec doesn't ship internally inconsistent with the
shipped module set and error text. F3–F5 are test-strength polish that can land in the `035`
hardening pass. Nothing here argues against cutting `0.0.9`.
