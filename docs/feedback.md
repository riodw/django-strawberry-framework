# Implementation review — `docs/spec-028-orders-0_0_8.md` (Ordering subsystem)

Reviewed the **shipped implementation** against the spec, against the
shipped filter subsystem it mirrors, and against the live test suite.
The spec status header (line 4) claims "shipped (2026-06-02) … cross-slice
integration pass and final test-run gate closed (2026-06-02); awaiting
maintainer commit."

**The architecture is implemented faithfully and the design is sound. But
the "final test-run gate closed" claim is not true: the full suite is red
on two counts — a 99.11% coverage gate (target 100%) and 3 failing tests.**
The coverage shortfall is entirely attributable to this card; the 3
failures are not.

Verification was run from a clean read of every on-disk source file the
spec names, plus `uv run pytest` (full suite), `uv run ruff check/format`,
and `scripts/check_spec_glossary.py`.

---

## What matches the spec (verified, no action needed)

Confirmed against the actual source, not just the spec's self-description:

- **Subpackage layout** — `django_strawberry_framework/orders/` ships all
  five files (`__init__.py`, `base.py`, `sets.py`, `factories.py`,
  `inputs.py`); `tests/orders/` carries all seven
  (`__init__.py` + 4 mirror + `test_finalizer.py` + `test_composition.py`).
- **B1 (list-shape helper)** — `orders/__init__.py::order_input_type`
  returns the element type `Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]`;
  fakeshop resolvers wrap as `list[order_input_type(...)] | None`
  (`schema.py` lines 193, 207, 221, 239). Matches Decision 11.
- **B2 (clear lifecycle)** — `clear_order_input_namespace` clears
  `_materialized_names` + `_field_specs` + `OrderArgumentsFactory.input_object_types`
  + `_type_orderset_registry` + every `OrderSet` subclass's
  `_owner_definition` / `_expanded_fields` / `_is_expanding_fields`, and
  **leaves materialized module globals parked** (no `delattr`). `registry.clear()`
  carries two separate order-side blocks (`clear_order_input_namespace`
  then `_helper_referenced_ordersets.clear()`), both `except ImportError: pass`
  + `else:`. Matches Decision 9.
- **B4 (M2M exclusion — the rev3 ground-truth fix)** —
  `inputs.py::_get_concrete_field_names_for_order` is
  `[f.name for f in model._meta.get_fields() if hasattr(f, "column") and not getattr(f, "many_to_many", False)]`.
  The `not f.many_to_many` clause that the rev3 review proved necessary on
  Django 6.0.5 (where `ManyToManyField.column is None` makes
  `hasattr(f, "column")` True) is present. `genres` is correctly excluded.
- **H1 (shared mixin home)** — `orders/base.py` imports
  `LazyRelatedClassMixin` from `..sets_mixins` (not `filters.base`);
  `orders/sets.py::OrderSet(ClassBasedTypeNameMixin, metaclass=OrderSetMetaclass)`
  inherits the name mixin from the same neutral module.
- **H2 (owner/model validation)** — `finalizer.py::_bind_orderset_owner`
  ships the first-bind model-compat check.
- **H3 (relation-level permission dispatch)** —
  `test_order_check_permission_denies_active_related_branch` is present in
  the live suite (14 tests total, confirmed by name).
- **No `apply()` dispatcher** (H1 of rev1) — `sets.py` ships only
  `apply_sync` / `apply_async`; the bare-`apply` grep returns nothing.
- **Decision 6 subpass order + the load-bearing `.orderset` walk** —
  `_bind_ordersets` runs bind → expand → orphan-validate → materialize, and
  subpass 2 explicitly reads `related.orderset` (finalizer.py ~line 703) to
  force Layer-2 resolution at the subpass-2 boundary, exactly as the spec's
  Decision 6 step 2 prescribes.
- **`Ordering.resolve()`** — the True-or-None NULLS sentinel semantics
  (Decision 5 / M4) are implemented verbatim.
- **Promotion gate** — `DEFERRED_META_KEYS` now holds only
  `{aggregate_class, fields_class, search_fields}`; `orderset_class` is in
  `ALLOWED_META_KEYS`; `_validate_orderset_class` uses the local in-function
  `from ..orders.sets import OrderSet` import (N3).
- **Decision 10 (version-bump boundary)** — `pyproject.toml`,
  `__version__`, and `tests/base/test_init.py` are at `0.0.8`, but that came
  from a **separate maintainer release commit** (`171a9bc release: bump to
  0.0.8, retire joint-cut convention`), NOT from this card's Slice 5. This
  is exactly what Decision 10 prescribes; no violation.
- **Docs** — GLOSSARY Index flips all five ordering symbols to
  `shipped (0.0.8)`; `docs/TREE.md` lists `orders/` on-disk; KANBAN records
  `DONE-028-0.0.8` with the past-tense body.
- `ruff check` / `ruff format --check` pass on all order sources.
- `scripts/check_spec_glossary.py` reports `OK: 44 terms`.

---

## Blocking

### B1. The 100% coverage gate is RED — 99.11%, and the orders subsystem is the sole cause

`uv run pytest` (full suite) ends with:

```
TOTAL                                          3484     31    99%
FAIL Required test coverage of 100.0% not reached. Total coverage: 99.11%
```

All 31 uncovered lines are in `orders/*` — every other package module
(including the filter subsystem this card mirrors) hits 100% in the full
run. Per-module:

| Module | Cov | Uncovered lines |
| --- | --- | --- |
| `orders/base.py` | 94% | 82 (`orderset.setter` body) |
| `orders/factories.py` | 98% | 138 (`if os_class in seen: continue` — BFS cycle guard) |
| `orders/inputs.py` | 93% | 168, 222, 336, 344, 352, 410, 461-462, 476-477 |
| `orders/sets.py` | 95% | 184, 269, 271, 318, 329, 331, 346, 535, 571, 579 |

This directly contradicts (a) the spec status header's "final test-run gate
closed (2026-06-02)" claim and (b) DoD item 26 ("Package coverage stays at
100% … verified by CI's `fail_under = 100` gate"). The gate is the
acceptance criterion; it is not met.

The uncovered lines fall into three buckets, each with a clear close:

1. **Defensive `except ImportError: pass` partial-load guards**
   (`inputs.py:461-462, 476-477`). The shipped filter side's
   `clear_filter_input_namespace` has the structurally-identical guards and
   `filters/inputs.py` reaches **100%** in the full suite — so these are
   coverable, not inherently unreachable. Mirror whatever the filter side
   does (a `test_*_clear_works_without_*_imported`-style subprocess test, or
   a monkeypatched-`sys.modules` unit test). Do NOT reach for
   `# pragma: no cover` until you confirm the filter side needed it; it
   didn't.
2. **No-op / early-return fast paths** (`sets.py:318, 329, 535, 571, 579`;
   `inputs.py:336`). These are the empty-input / `None`-direction / empty-list
   branches. The live suite has `test_library_branches_order_empty_list_and_null_direction_no_op`,
   but it evidently does not drive every one of these early returns at the
   unit level. Add focused `tests/orders/test_sets.py` /
   `test_inputs.py` cases that hit each branch directly.
3. **Defensive `continue` / `return` inside the parse + BFS**
   (`factories.py:138`; `sets.py:269, 271, 331, 346`; `inputs.py:344, 352,
   410`). `factories.py:138` is the BFS already-seen cycle guard —
   `test_factories.py` should construct an `A → B → A` orderset cycle and
   assert the factory terminates (the spec's Edge-cases "Circular
   `RelatedOrder` cycles" bullet promises this is tested). The others are
   per-branch coverage in `get_flat_orders` / `normalize_input_value`.

`base.py:82` (the `orderset.setter`) and `inputs.py:168, 222` are trivially
coverable with a one-line assignment / kwarg-pass test each.

**Root-cause fix:** the orders modules must reach 100% the same way the
filter modules do — through `tests/orders/` unit coverage plus the live
HTTP suite — before the card is done. The status header should not say
"final test-run gate closed" until `uv run pytest` exits 0.

### B2. Three tests fail in the working tree (not caused by orders, but the gate is still red)

```
FAILED examples/fakeshop/test_query/test_glossary_api.py::test_filter_glossary_terms_by_status_key
FAILED examples/fakeshop/test_query/test_glossary_api.py::test_filter_glossary_terms_by_spec_mention_and_select_edges
FAILED examples/fakeshop/test_query/test_glossary_api.py::test_glossary_documents_are_shared_board_docs_scoped_to_glossary_namespace
```

All three raise `IntegrityError: UNIQUE constraint failed:
kanban_boarddockind.key` and reproduce when `test_glossary_api.py` is run
**in isolation** (3 failed in 2.06s), so this is not a test-ordering flake —
it is a genuine fixture/seeding defect in the kanban `BoardDocKind` setup.

This is **not** the ordering card's doing: the order subsystem touches
nothing under `apps/kanban/` or `test_glossary_api.py`, and `git status`
shows an independent, uncommitted kanban workstream
(`apps/kanban/{admin,models}.py`, `apps/kanban/tests/*`) as the likely
source. I'm flagging it because:

- the spec status header claims the "final test-run gate closed," which is
  false while these fail; and
- whoever commits this card should not do so on a red suite. Resolve the
  kanban `BoardDocKind` double-seed separately (looks like a
  `get_or_create` / unique-key collision in a kanban test fixture or
  migration-data step) before the ordering commit lands on a green tree, or
  explicitly scope it to a sibling task.

---

## Medium

### M1. Status header overstates the gate state

Line 4 asserts "cross-slice integration pass and final test-run gate closed
(2026-06-02)." Given B1 (coverage red) and B2 (3 failures), this sentence is
inaccurate. Once B1 is fixed and B2 is resolved/scoped-out, restate it
precisely — e.g. "all `tests/orders/` + 14 live order tests pass; full-suite
coverage gate green" — or, if committing before the kanban failures are
fixed, say so explicitly rather than claiming a closed gate.

---

## Nit

### N1. KANBAN snapshot paragraph still carries the retired joint-cut convention

`KANBAN.md` line 74 reads: "The last `0.0.8` card to ship owns the version
bump from `0.0.7` per Decision 10 of `docs/SPECS/spec-020-list_field-0_0_7.md`."
That is the **old joint-cut convention** that this spec's Revision 5
explicitly retired (Decision 10 is now "version bumps are
maintainer-commanded"). The version was in fact bumped by a standalone
maintainer release commit, consistent with the new convention — so the
snapshot sentence describes a policy that no longer governs. Minor
doc-consistency drift; the card's own KANBAN edits (the `DONE-028-0.0.8`
move + Done body) are correct. Worth a one-line update to the snapshot
paragraph if KANBAN edits are in scope, otherwise leave for the maintainer.

### N2. CHANGELOG `[Unreleased]` heading not promoted despite version files at 0.0.8

`pyproject.toml` / `__version__` are at `0.0.8`, but `CHANGELOG.md` still
heads the section `## [Unreleased]` (no `## [0.0.8]`), with both the
Filtering and Ordering bullets under it. This card **correctly** does not
promote the heading (Decision 10 / DoD item 23 gate that on the explicit
version-bump command). Flagging only so the maintainer closes the loop —
the standalone release commit that bumped `pyproject.toml` should have also
promoted the CHANGELOG heading; that promotion is the maintainer's to make,
not this card's.

---

## Summary

The implementation is a clean, faithful port: every Blocking/High finding
from the four prior spec-review rounds (B1 list-shape, B2 clear lifecycle,
B3 NULLS test field, B4 M2M exclusion, H1 sets_mixins home, H2 owner/model
check, H3 relation-permission dispatch, H4 enum casing) is present and
correct in the shipped code, the subpass order and the load-bearing
subpass-2 `.orderset` walk match Decision 6, ruff is clean, and the glossary
checker is green.

The one card-owned blocker is **B1: the 100% coverage gate is not met
(99.11%, all 31 missing lines in `orders/*`)** — the filter subsystem the
card mirrors reaches 100%, so the bar is achievable and the gap is closable
with targeted `tests/orders/` cases (plus, if the filter side did, a
partial-load guard test). **B2** (3 kanban-seeding test failures) is not the
card's fault but blocks a green commit and falsifies the "test-run gate
closed" status line. Fix B1, resolve or explicitly scope B2, and correct the
status header (M1); N1/N2 are doc-consistency cleanups for the maintainer.

The card is **not done** until `uv run pytest` exits 0.
