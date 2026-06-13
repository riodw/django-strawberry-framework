# spec-033 build review — round 2 (post-fix, 2026-06-13)

Re-review after commit `f6d3b829` ("Enhance connection optimizer and tests for distinct
target handling"), which addresses the five findings from the round-1 review. Working tree
clean. The fix commit touched **docs + tests only** — no package source changed
(`git show f6d3b829 --stat` confirms), so the mechanism reviewed in round 1 is byte-for-byte
unchanged and the round-1 verdict (correct, high-quality, no blocking bug) stands. This pass
verifies the fixes and re-checks for anything the changes introduced.

## Verdict

**All five round-1 findings are resolved, and resolved well.** F3–F5 added genuinely
meaningful tests (not placebo coverage); F1 and F2 reconciled the spec/TREE.md to the shipped
reality. One small residual remains from the F2 reconciliation (a single stale phrase the
sweep missed, **N1** below) plus a cosmetic revision-ordering nit (**N2**). Neither blocks the
cut. Build-ready.

## Round-1 findings — fix verification

| # | Round-1 finding | Status | Evidence |
| --- | --- | --- | --- |
| F1 | `utils/connections.py` undocumented / contradicts Decision 11 | **Resolved (thorough)** | [`docs/TREE.md`](TREE.md) now lists `connections.py` in **both** `utils/` blocks and `test_connections.py` in **both** `tests/utils/` blocks, and the `utils/` summary line names the window-bounds/sidecar-kwarg contracts. The spec adds **Revision 4**, splits Decision 11 into "Source (build proper): no new module" vs "Source (post-build DRY refactor): one new module" with the cycle-safety justification, and fixes the Slice-checklist preamble + the TREE.md convention bullet. The "no mirror tension" claim is now honest. |
| F2 | Strictness message names relation field, spec said `<field>_connection` | **Resolved (spec → code)** | They took the lowest-churn option: reconcile the spec to the shipped relation-field form. [Error shapes](spec-033-connection_optimizer-0_0_9.md) (line 217) now reads `Unplanned N+1: <field>` with an explicit "NOT the generated `<field>_connection` attribute" note; Decision 8 (line 364), its fallback-reason example (line 373 → `Unplanned N+1: books (...)`), and the Decision-4 Resolver-keys bullet all updated to the relation-field vocabulary. **See N1** for the one spot the sweep missed. |
| F3 | `test_window_slice_from_variables` near-tautological | **Resolved** | Now asserts `"_DST_ROW_NUMBER" in sql`, `"<= 5" in sql` (the resolved variable value `5` bounds the window) **and** `"<= 100" not in sql` (proving it's the value, not the `relay_max_results` cap). Independently proves variable resolution drives the slice — the gap is closed. |
| F4 | `test_both_shape...` discarded its `diff_plan_for_queryset` result | **Resolved** | The delta is now captured and asserted: `delta_to_attrs` must contain **both** `None` (list sibling / absorbed consumer prefetch) and `"_dst_books_connection"` (the window), with `prefetch_through == {"books"}` for both. The B8 exact-match/absorption claim is now executed, not smoke-tested. |
| F5 | DISTINCT fallback count-correctness implied, not executed | **Resolved (strong)** | New `@pytest.mark.django_db test_distinct_target_fallback_reports_correct_total_count` + `_genres_distinct_book_schema` (a `BookType.get_queryset` doing `.filter(genres__isnull=False).distinct()`). Real fan-out: fiction holds 3 distinct books, two also in scifi → 5 pre-DISTINCT rows; the test asserts `totalCount == 3`, the true distinct count a `Count(1) OVER` would have inflated to 5. Optimizer ON so the DISTINCT guard is what routes to the counting fallback, strictness off so it doesn't raise. This is exactly the executed correctness pin the round-1 finding asked for. |

## New / residual findings

### N1 [LOW — residual F2 miss] One strictness-message reference in the spec still says "generated field name"

The F2 reconciliation updated Error shapes and Decision 8 but missed the **Slice-4 checklist
bullet** (spec line 77), which still describes `_check_n1` as "parameterized with an explicit
connection probe kind, a `to_attr` probe, **the generated field name**, and a fallback-reason
message." The shipped code passes the **relation** field name (`relation_field_name` →
`field_name` in `_check_n1`), and Decision 8 (line 364) was reconciled to say exactly that.
So the spec now contradicts itself within one document: the checklist says "generated field
name," the Decision says "relation field name." **Recommend:** change line 77 to "the relation
field name" to finish the sweep. One-word fix; purely the same F2 reconciliation, just an
unswept instance.

### N2 [TRIVIAL — cosmetic] Revision history is ordered 1, 4, 3, 2

The inline revision history now reads Revision **1, 4, 3, 2** (spec lines 13–16) — Revision 1
(initial draft) at the top, then the later revisions newest-first below it. New entries have
been inserted directly under Revision 1, pushing older ones down, which yields the mixed
order. Harmless, but a reader expecting strictly ascending or strictly descending will
stumble. **Optional:** either move Revision 1 to the bottom (full descending 4→1) or append
new revisions after the last (full ascending 1→4). Not worth a dedicated edit unless the file
is touched again.

## Re-checks (clean)

- **No behavior change.** `f6d3b829` changed only `docs/TREE.md`, the spec, `test_walker.py`,
  `test_relay_connection.py`, and `feedback.md` — zero `django_strawberry_framework/*.py`. The
  round-1 mechanism review (windowed `Prefetch` + DISTINCT guard + throwaway `sub_plan`
  isolation, the field-name-keyed `to_attr` probe, the single-sourced cursor-parity bounds,
  the forward-row-number cursor scheme, the three-condition strictness guard, the unified
  cache-key traversal) is unchanged and remains correct.
- **The three new tests don't paper over anything.** Each asserts a concrete, falsifiable
  value (`"<= 5"`/`"<= 100" not in`; both `to_attr`s surviving the delta; `totalCount == 3`),
  and the DISTINCT test in particular constructs a real fan-out where a regression (windowing
  a distinct target) would flip the assertion to 5. No skip/xfail, no loosened bound.
- **F1 doc reconciliation is internally consistent** apart from N1: Decision 11, the preamble,
  the TREE.md convention bullet, both TREE.md `utils/` source blocks, and both `tests/utils/`
  blocks all now agree the DRY refactor added exactly one module + its twin.

## Net assessment

Ship it. The five findings are closed; the two residuals (N1 a one-word spec fix, N2
cosmetic) can ride along with any next spec touch or be ignored without consequence to the
`0.0.9` cut. Nothing outstanding blocks the joint cut.
