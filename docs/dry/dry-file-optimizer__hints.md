# DRY review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## System trace

The target owns the **typed per-relation optimizer directive** used as
`DjangoType.Meta.optimizer_hints` values: frozen `OptimizerHint`, the
`SKIP` sentinel, the three factory classmethods, construction-time
conflict / type rejection (`ConfigurationError`), and the skip-shape
predicate `hint_is_skip`.

Owned responsibility:

- one consumer value type for Meta overrides (`force_select`,
  `force_prefetch`, `prefetch_obj`, `skip`, plus empty no-op);
- one Prefetch-type invariant for `prefetch_obj` / `prefetch(obj)`;
- one skip-shape dispatch for walkers and schema audit
  (`hint is SKIP` or `.skip`, never raises on unknown shapes);
- documented factories as the public construction API (direct
  construction remains possible but is not the documented surface).

Connected behavior examined:

- `types/base.py` — `_meta_optimizer_hints` / `_validate_optimizer_hints`
  own Meta mapping shape, relation-key typo/exclusion guards, and
  `isinstance(..., OptimizerHint)` value typing. Construction validity
  of each hint stays in this module.
- `types/definition.py` — stores `optimizer_hints: dict[str, OptimizerHint]`.
- `optimizer/walker.py` — `_resolve_optimizer_hints`, `_apply_hint`
  (skip → prefetch_obj → force_select → force_prefetch; empty → False
  and default cardinality). Priority order is dispatch documentation;
  conflicts are already rejected here.
- `optimizer/nested_planner.py` / `optimizer/extension.py` —
  `hint_is_skip` for nested-window skip and schema-audit skip.
- `optimizer/field_meta.py` — no hint knowledge (field snapshots only);
  correct boundary.
- Root `__init__.py` re-exports `OptimizerHint`; `optimizer/__init__.py`
  intentionally does not (sibling `__init__` review).
- Pins: `tests/optimizer/test_hints.py` (construction / factories /
  conflicts); walker / extension / types Meta pins; live HTTP
  `examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_hints_are_observable_over_http`
  (LoanType `book` force-prefetch vs `patron` SKIP).
- Baseline
  `git diff 762d3f34c5c8a6f19d491c8a94459874b38c6644 -- …/optimizer/hints.py`
  was empty before this pass. Concurrent dirty optimizer siblings left
  untouched.

## Verification

Searches:

- `OptimizerHint` / `hint_is_skip` / `optimizer_hints` across package,
  tests, examples — production skip dispatch is solely via
  `hint_is_skip` (walker, nested_planner, extension audit). No
  open-coded `hint is SKIP or hint.skip` twins remain.
- Prefetch isinstance + shared error string — duplicated in
  `prefetch()` and `__post_init__` before this pass (confirmed by
  reading both bodies).
- Optional `export_dry_review.py audit --target …/hints.py`: reverse
  imports match root / walker / extension / nested_planner / types /
  tests. Static name collisions on `select_related` /
  `prefetch_related` are Django ORM APIs, not hint factories.

Rejected / deferred candidates:

1. **Fold Meta key/value validation from `types/base.py` into this
   module.** Disproved: unknown/excluded relation keys and mapping
   shape are DjangoType Meta surface concerns; they must stay next to
   `fields` / `exclude` typo guards. This module owns value
   construction only.

2. **Collapse four flags into an enum / tagged union.** Deferred: would
   change the public consumer API and error vocabulary without a
   behavior bug. Factories already present exclusive shapes.

3. **Re-export `OptimizerHint` from `optimizer/__init__.py`.** Rejected
   (matches sibling `__init__` judgment): root export is the consumer
   path; internals import `optimizer.hints` directly.

4. **Simplify `hint_is_skip` to only `getattr(..., "skip")` (drop
   identity check).** Rejected: identity + attribute paths are the
   documented contract pinned by
   `test_hint_is_skip_handles_sentinel_record_and_unknown_shapes`;
   removing the sentinel arm is not a shared-responsibility win.

5. **Move `_apply_hint` dispatch into `OptimizerHint` methods.**
   Deferred to walker ownership: apply needs plan mutation, relation
   kind, consumer-assigned `to_attr` gates, and rebase — walker domain,
   not value-type domain. Sibling `walker.py` still open.

6. **Encode "at most one directive" as a single active-count check.**
   Rejected: distinct `ConfigurationError` messages per conflict are
   intentional consumer diagnostics; collapsing them would obscure
   ownership without removing a second implementation of the same rule.

## Opportunities

1. **Repeated responsibility:** Prefetch-type rejection
   (`isinstance(..., Prefetch)` + identical `ConfigurationError`
   message) lived in both `OptimizerHint.prefetch` and
   `__post_init__`.
   **Sites:** `hints.py` factory; `hints.py::__post_init__` (direct
   `prefetch_obj=`).
   **Evidence:** Same invariant, same message, same change axis; factory
   call remains required so `prefetch(None)` cannot become the empty
   no-op (`None` is the field default).
   **Owner:** module-private `_require_prefetch`.
   **Consolidation:** Both sites call `_require_prefetch`; factory
   returns `cls(prefetch_obj=_require_prefetch(obj))`.
   **Proof:** Existing
   `tests/optimizer/test_hints.py::TestPrefetchFactory::test_none_rejected`
   and `TestInvalidStatesRejected::test_prefetch_obj_rejects_non_prefetch_value`
   cover factory and direct-construction paths; live HTTP hint
   observability unchanged (behavior-preserving extract).
   **Risks / non-goals:** Do not remove the factory-side call; do not
   move Meta key validation here.

## Judgment

The module is already the clear owner of hint value construction and
skip-shape dispatch. Cross-package consumers correctly separate Meta
surface validation (`types/base`) from plan application (`walker`). The
only confirmed consolidation was the duplicated Prefetch-type invariant
inside this file; that is now single-sited at `_require_prefetch`.

## Implementation (Worker 1)

- **Owner chosen:** `django_strawberry_framework/optimizer/hints.py::_require_prefetch`
- **Migrated sites:** `OptimizerHint.prefetch`; `OptimizerHint.__post_init__`
  Prefetch-type arm (conflict check with force flags kept adjacent).
- **Behavior kept separate:** Meta mapping/key validation in
  `types/base.py`; plan dispatch in `walker._apply_hint`; skip predicate
  API of `hint_is_skip` unchanged.
- **Tests / docs:** No new permanent test required — existing unit pins
  already exercise both entry points; live library HTTP test already
  covers SKIP vs force-prefetch. No glossary/changelog edit (internal
  helper; no public contract change). Changelog: no.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .`
  clean for this change. Full pytest not run (per DRY worker rules).
- **Item-scoped diff:** only
  `django_strawberry_framework/optimizer/hints.py` (+ this artifact).
  Concurrent dirty optimizer / other paths preserved.

## Independent verification (Worker 2)

Re-traced `hints.py` as the value-construction owner through
`types/base.py::_validate_optimizer_hints` (Meta mapping/keys),
`types/definition.py` storage, `walker._apply_hint` /
`hint_is_skip` consumers (`walker`, `nested_planner`, schema audit in
`extension`), root `__init__` re-export, and pins in
`tests/optimizer/test_hints.py`, extension skip/hint_is_skip tests,
walker hint planning, and live
`examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_hints_are_observable_over_http`.
Item-scoped diff is only the `_require_prefetch` extract (+ docs).

**Finding 1 (`_require_prefetch`) — disposed: accepted.** Factory and
`__post_init__` share one Prefetch-type invariant and one
`ConfigurationError` message; both entry points remain load-bearing
because `None` is a legitimate field default (factory must reject
before construction) while direct `prefetch_obj=` still needs the
check. Happy-path double-call is harmless. Scratch confirmed
`prefetch(None)` raises, factory/direct non-Prefetch messages match,
and `OptimizerHint.prefetch(Prefetch(...))` preserves object identity.
Permanent pins:
`TestPrefetchFactory::test_none_rejected`,
`TestInvalidStatesRejected::test_prefetch_obj_rejects_non_prefetch_value`
(both arms). Focused run: 28 passed
(`test_hints.py` + hint_is_skip/SKIP routing + library HTTP).

**Rejected candidates — disposed: stand.**

1. Fold Meta key/value validation into `hints.py` — Meta typo/exclusion
   surface stays with `fields`/`exclude` in `types/base.py`; this module
   owns value construction only.
2. Enum / tagged union — public API / vocabulary change without a
   behavior bug; factories already encode exclusive shapes.
3. Re-export from `optimizer/__init__.py` — `__all__` is
   `(DjangoOptimizerExtension, logger)` only; root export remains the
   consumer path; internals import `optimizer.hints` directly.
4. Drop `hint is SKIP` from `hint_is_skip` — not a consolidation;
   identity + `getattr` is the documented contract pinned by
   `test_hint_is_skip_handles_sentinel_record_and_unknown_shapes`
   (non-sentinel `skip=True` still needs the attribute arm).
5. Move `_apply_hint` onto `OptimizerHint` — apply mutates plan,
   relation kind, `to_attr` / consumer-assigned gates, rebase; walker
   domain (sibling still open).
6. Collapse conflicts to an active-count — distinct per-conflict
   `ConfigurationError` messages are intentional diagnostics; no second
   implementation of the exclusivity rule elsewhere.

**Missed opportunities:** None material. Production skip dispatch is
solely `hint_is_skip` (no open-coded `hint is SKIP or hint.skip`
twins). Prefetch-type rejection for hints is single-sited at
`_require_prefetch`. Error text naming `OptimizerHint.prefetch(obj)`
on the direct-construction path is pre-existing consumer vocabulary,
not a second invariant.

**Blockers:** None.

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
