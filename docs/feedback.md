# Review: spec-033 follow-up fixes

## Findings

### P3 - Line-number source references still remain in standing docs and code comments

The latest patch removed the direct `docs/feedback.md` references, and the new tests use stable `spec-033 Decision ... / Revision 3` wording. However, the AGENTS.md source-reference rule is broader than "do not cite feedback.md": standing docs and code comments should use stable symbol/section references instead of line-number references. There are still several rot-prone references in the touched area: `docs/spec-033-connection_optimizer-0_0_9.md:5` says "see line 3"; `django_strawberry_framework/optimizer/walker.py:782`, `django_strawberry_framework/optimizer/walker.py:810`, and `django_strawberry_framework/optimizer/walker.py:1341` cite "spec line 63"; `tests/optimizer/test_walker.py:2583` cites "spec line 63"; and `tests/test_relay_connection.py:942` / `tests/test_relay_connection.py:1455` cite "spec line 68" and "Edge case line 456". These can drift the next time the spec is edited, and they do not comply with the repo rule. Replace them with stable section/decision references, e.g. `spec-033 Decision 4 scalar-only connection contract`, `spec-033 Decision 5 fast path`, or a symbol-qualified code reference where the comment is pointing at source behavior.

## Verified Fixes

The prior spec-drift finding is resolved. `docs/spec-033-connection_optimizer-0_0_9.md` now documents the minimal pk / connector / deterministic-order projection for scalar-only windows, and it documents the malformed-slice error-locality rule where the walker emits no window prefetch but still records the connection resolver key.

The prior non-pk ordering coverage gap is resolved. `tests/optimizer/test_walker.py` now pins both non-pk deterministic `Prefetch.queryset.order_by == ("title", "id")` and scalar-only projection of the non-pk order column; `tests/test_relay_connection.py` adds a through-schema fast-path test that captures the window SQL and checks that the outer `ORDER BY` includes the deterministic tiebreaker shape.

Test placement is consistent with AGENTS.md: the new synthetic optimizer coverage lives under `tests/`, and no catalog/auth example tests were added without the required seed helpers.

## Not Run

Per AGENTS.md, I did not run pytest. After replacing this file I ran the required formatting/lint commands.
