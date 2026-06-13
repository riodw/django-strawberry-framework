# Review: spec-033 connection optimizer implementation

## Findings

### P1 - Windowed prefetches compute row numbers in deterministic order but do not order the prefetched rows

`django_strawberry_framework/optimizer/walker.py:1244-1257` computes the shared deterministic `order_by` tuple and passes it into `apply_window_pagination`, but `django_strawberry_framework/optimizer/plans.py:614-643` only uses that tuple inside `ROW_NUMBER() OVER (...)`; it never applies `QuerySet.order_by(*order_by)` to the child queryset. SQL window ordering determines annotation values, not the order in which Django hands prefetched model instances to `to_attr`. The fast path then consumes `rows` as already-forward-ordered in `django_strawberry_framework/connection.py:220-245`, using `rows[0]`, `rows[-1]`, and edge iteration order for cursors and `pageInfo`.

This can make the fast path diverge from the fallback pipeline whenever DB return order is not already the desired connection order. The current parity tests seed titles in insertion order (`tests/test_relay_connection.py:972-993`), so they do not expose the difference.

Root-cause fix: after computing `order_by`, apply the same deterministic order to the windowed child queryset, not just to the window expression. Keep the window row-number order and final queryset order sourced from the same tuple. Add a regression that seeds child rows in a non-sorted insertion order and asserts optimizer-on and optimizer-off wire results are identical; also assert the generated `Prefetch.queryset.query.order_by` carries the deterministic tuple.

### P2 - Strictness can mask malformed-pagination error locality

`django_strawberry_framework/optimizer/walker.py:1117-1126` catches `SliceMetadata` `ValueError` / `TypeError` and returns `None`, and `_plan_connection_relation` leaves that selection unplanned at `django_strawberry_framework/optimizer/walker.py:1198-1200` specifically for fallback error locality. Under strictness `"raise"`, though, the resolver calls `_check_n1` before the per-parent pipeline in `django_strawberry_framework/connection.py:1015-1051`. Because no window `to_attr` exists and no planned resolver key was recorded, malformed cursors / invalid pagination can surface as `OptimizerError("Unplanned N+1...")` instead of the connection/pagination validation error the spec says should own that path.

Root-cause fix: distinguish validation-fallback unplanned paths from real N+1 fallback paths. Either record a strictness-suppression/planned sentinel for malformed-slice fallbacks so the resolver lets the connection pipeline raise its original error, or otherwise defer the strictness raise until after pagination validation has had a chance to fail. Add a through-schema strictness `"raise"` test with an invalid nested `after:` cursor and assert the error is not an `OptimizerError`.

### P2 - Scalar-only nested connections are planned but still fetch full child rows

The scalar-only branch is recognized (`django_strawberry_framework/optimizer/walker.py:1212-1225`), but it passes an empty node selection into `_build_prefetch_child_queryset`. That builds an empty child plan, then `_ensure_connector_only_fields` returns immediately when `plan.only_fields` is empty (`django_strawberry_framework/optimizer/walker.py:733-736`), so `OptimizationPlan.apply` never adds `.only()` (`django_strawberry_framework/optimizer/plans.py:238-245`). The resulting `pageInfo`-only / `totalCount`-only window fetches full model rows even though the connection only needs pk, connector, and ordering columns plus annotations.

This conflicts with the spec checklist that says scalar-only selections are planned with pk/connector/order-only projection (`docs/spec-033-connection_optimizer-0_0_9.md:63`) and weakens the optimizer's main performance goal. The current test only proves the selection is planned (`tests/optimizer/test_walker.py:2450-2465`); it does not assert the projection.

Root-cause fix: seed a minimal child `only_fields` set for scalar-only connection windows before applying the child queryset: target pk, relation connector column, and any concrete ordering columns needed by the deterministic order. Add tests that inspect `Prefetch.queryset.query.deferred_loading` for scalar-only `pageInfo` and `totalCount` selections.

### P3 - Touched code still cites replaceable review artifacts

`django_strawberry_framework/connection.py` contains production comments/docstrings that cite `docs/feedback.md` directly at lines 367, 465, 491, 720, and 1114. There are also test docstrings/comments with the same pattern in `tests/optimizer/test_walker.py:179`, `tests/optimizer/test_walker.py:222`, and `examples/fakeshop/test_query/test_products_api.py:162`. `AGENTS.md:27` requires stable source references in docs and code comments; `docs/feedback.md` is intentionally replaced each review cycle and is not a durable source of truth.

Root-cause fix: replace those references with stable spec decision references or symbol-qualified source references, or remove them when the surrounding explanation already stands on its own. Do not add new `docs/feedback.md` references in production comments.

## Notes

I did not run pytest. `AGENTS.md` explicitly says not to run pytest after edits unless asked.
