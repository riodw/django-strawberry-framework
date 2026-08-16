# DRY review: `django_strawberry_framework/utils/input_values.py`

Status: verified

## System trace

`utils/input_values.py` owns the **read-side set-input traversal substrate**
shared by FilterSet and OrderSet. Charter: mechanics only — dict-vs-dataclass
walk, `None` / family-`unset_sentinel` active-input rule, per-field `FieldSpec`
lookup, and leaf / related / logic classification. Family leaf semantics stay
at the call sites.

**Definitions:**

| Symbol | Role |
| --- | --- |
| `LOGIC` / `RELATED` / `LEAF` | mutually exclusive kind markers |
| `iter_input_items` | lowest walk: dict → `.items()`, dataclass → `__dataclass_fields__` |
| `input_field_value` | single-field sibling of the walk (`.get` / `getattr`) |
| `is_inactive_value` | identity-based inactive rule (`None` or `unset_sentinel`) |
| `SetInputTraversal` | frozen family config for the classifier |
| `ActiveField` | one active top-level field + kind + optional related obj |
| `iter_active_fields` | classifier: inactive skip, optional top-level list flatten, classify |

**Confirmed consumers (already delegated):**

- `filters/sets.py::FilterSet._normalize_input` — module singleton
  `_NORMALIZE_TRAVERSAL` (`related_filters`, `_LOGIC_PYTHON_ATTRS`,
  `unset_sentinel=UNSET`); dispatches by `kind` (LOGIC wire-key copy, RELATED
  strip, LEAF operator-bag / range normalize).
- `orders/inputs.py::normalize_input_value` — per-call
  `SetInputTraversal(related_orders, handle_top_level_list=True)`; RELATED
  recurses with path prefix, LEAF appends `(django_source_path, Ordering)`.
- `utils/permissions.py::active_permission_targets` (and thin wrappers
  `active_permission_field_paths` / `active_related_branches`) — one
  `iter_active_fields` walk partitioned by kind; filter/order sets pass family
  config through.
- `utils/permissions.py::extract_branch_value` — composes
  `input_field_value` + `is_inactive_value` (does not re-sniff shape).
- `filters/inputs.py::normalize_input_value` — defensive
  `is_inactive_value(..., unset_sentinel=UNSET)` at leaf-coerce entry.
- Re-export: `utils/permissions.py` re-exports `iter_input_items` so existing
  `from ..utils.permissions import iter_input_items` import paths keep working;
  `FilterSet._iter_input_items` is a thin classmethod delegate (logic-shape
  validation + operator-bag dataclass fallthrough).

**Does not recurse** into child set inputs — RELATED records carry raw child
values; consumers re-enter their own entry points.

Item baseline `a33b348ccab8c66d59cd6767bc9d6acf334b4271`: target hash matches
baseline (empty item-scoped diff for the target). No production edits.

## Verification

Searches across `django_strawberry_framework/`:

- `iter_active_fields` / `SetInputTraversal` / `is_inactive_value` /
  `iter_input_items` / `input_field_value` — every production site routes
  through this module (or the permissions re-export of `iter_input_items`).
- `__dataclass_fields__` — sole runtime sniff is
  `utils/input_values.py::iter_input_items`. The only other hit is a **stale
  docstring** in `FilterSet._operator_bag_items` that still narrates an inline
  sniff while the body delegates via `_iter_input_items` (deferred docstring
  drift; not a second implementation).
- `isinstance(..., dict)` + walk patterns — only this module and the
  filter-family operator-bag / range **disambiguation** in
  `_operator_bag_items` / `filters/inputs.py` range helpers (lookup-key
  semantics, not set-input classification).
- Write-flavor walks — `utils/inputs.py::iter_provided_input_fields` (and
  mutations / forms / DRF / `write_values` consumers) use
  `__strawberry_definition__.fields` + UNSET-only strip; see rejected
  candidates.
- Permissions absorption — traced
  `active_permission_field_paths` / `active_related_branches` /
  `extract_branch_value` as evidence only; they already consume this
  substrate. No absorb into this file (permissions remains its own DRY item).

No scratch experiments: call-graph + contract divergence were decisive.
Permanent pins already live in `tests/utils/test_input_values.py` (walk,
inactive identity-not-truthiness, classification, list flatten, inactive top
level). Family suites cover consumer behavior. Pytest deferred per cycle
policy.

Strongest rejected candidates:

1. **Fold write-flavor `iter_provided_input_fields` into this substrate.**
   Different contract on every axis: walks `__strawberry_definition__.fields`
   (not `__dataclass_fields__` / raw dict), strips **only** `strawberry.UNSET`
   while **keeping explicit `None`** (write tri-state: omitted vs null vs
   value), yields `(python_name, value, field)` for decode routing, and has no
   leaf/related/logic classification or `unset_sentinel` parameter. Unifying
   would need mode flags — forbidden by DRY.md for distinct rules. Owner stays
   `utils/inputs.py`.

2. **Move `extract_branch_value` / absorb permission walkers into this file.**
   `extract_branch_value` is already a thin composition of this module's
   primitives living next to permission recursion; relocating it is re-homing,
   not removing a second implementation. Permission walkers own check-method
   dedup, parent/child double dispatch, and related-depth caps — out of this
   charter. Assignment: do not absorb unless this file is the true owner;
   it is not for those policies.

3. **Remove `FilterSet._normalize_input`'s early inactive / non-walkable
   short-circuit** as "duplicate of `iter_active_fields`." Behaviorally
   redundant for classification, but it **avoids `get_filters()`** on empty /
   non-walkable input. That is a cheap consumer short-circuit, not a second
   owner of the walk rule. Leaving it preserves the performance edge without
   re-spelling classification.

4. **Hoist orders `SetInputTraversal(...)` to a module singleton** like
   `_NORMALIZE_TRAVERSAL`. Same pattern of request-independent config, but
   rebuilding a tiny frozen dataclass is not duplicated *policy*. Optional
   micro-optimization, not a DRY consolidation.

5. **Collapse `FilterSet._iter_input_items` / permissions re-export.** Thin
   family / compatibility delegates; tests and call sites address them by name.
   Removing would churn import paths without collapsing a second walk body.

## Opportunities

None — the four historical inline copies (filter normalizer, order normalizer,
two permission walkers) already converge on this module. Remaining similar-
looking walks are either write-flavor UNSET-strip (`iter_provided_input_fields`)
or filter leaf-shape disambiguation (operator bag vs range dict), both with
distinct contracts and change axes.

## Judgment

Proved zero-edit. `utils/input_values.py` is already the single source of truth
for set-input traversal mechanics; consumers hold only family leaf semantics
and permission dispatch. Strongest near-miss is the write-flavor provided-field
walk, correctly owned elsewhere. Ready for Worker 2.

Deferred findings (not blocking; not production consolidations):

- Stale `_operator_bag_items` docstring still describes an inline
  `__dataclass_fields__` sniff after the body delegated to `_iter_input_items`.
- `_normalize_input` docstring / comments still say `_iter_input_items`
  delegates to `utils/permissions.py::iter_input_items` rather than naming
  `utils/input_values.py` as the true owner (permissions is a re-export).
- `input_field_value` has no direct unit pin in `tests/utils/test_input_values.py`
  (covered indirectly via `extract_branch_value` / permission tests).
- Pytest for this item: deferred until maintainer authorizes the cycle gate.

Item-scoped diff vs `a33b348ccab8c66d59cd6767bc9d6acf334b4271`: empty for
production / test paths; this artifact only
(`docs/dry/dry-file-utils__input_values.md`).

## Independent verification (Worker 2)

Re-traced set-input traversal ownership independently against present-day
`utils/input_values.py`, FilterSet / OrderSet normalizers, permission walkers,
write-flavor `iter_provided_input_fields`, and package-wide searches for leftover
inline classifiers.

**Zero-edit confirmed.** Item-scoped
`git diff a33b348ccab8c66d59cd6767bc9d6acf334b4271 -- django_strawberry_framework/utils/input_values.py`
is empty (195 lines match baseline).

**Substrate ownership holds; no leftover classifiers.** Production
`iter_active_fields` / `SetInputTraversal` / `is_inactive_value` /
`iter_input_items` / `input_field_value` consumers are exactly:

- `filters/sets.py::_normalize_input` via `_NORMALIZE_TRAVERSAL`
- `orders/inputs.py::normalize_input_value` (per-call config,
  `handle_top_level_list=True`)
- `utils/permissions.py::active_permission_targets` (+ thin wrappers) and
  `extract_branch_value` (composes `input_field_value` + `is_inactive_value`)
- `filters/inputs.py::normalize_input_value` defensive inactive guard
- `FilterSet._iter_input_items` thin delegate; permissions re-exports
  `iter_input_items` for import compatibility

Package-wide `__dataclass_fields__` runtime sniff is sole-sited in
`iter_input_items`; the only other hit is the stale
`FilterSet._operator_bag_items` docstring (body already delegates via
`_iter_input_items`). Schema-time `related_filters` / `related_orders` walks in
finalizer / factories are bind-time collection, not runtime set-input
classification.

**Rejected candidates challenged and upheld.**

1. Fold write-flavor `iter_provided_input_fields`: walks
   `__strawberry_definition__.fields`, strips **only** `strawberry.UNSET`,
   **keeps explicit `None`**, yields `(python_name, value, field)` with no
   leaf/related/logic classification. Distinct UNSET/None tri-state and change
   axis from read-side set inputs — unifying would need mode flags. Owner stays
   `utils/inputs.py`.

2. Absorb `extract_branch_value` / permission walkers: already thin consumers of
   this substrate; permission ownership (check-method dedup, parent/child
   dispatch, related-depth caps) is out of this charter. Re-homing ≠ collapsing
   a second walk body.

3. Drop `_normalize_input` early inactive / non-walkable short-circuit: sits
   **before** `get_filters()`; `iter_active_fields` would skip the same inputs
   but still force the filter-map build. Cheap consumer short-circuit, not a
   second classifier.

4. Hoist orders `SetInputTraversal(...)` to a module singleton: request-
   independent frozen config rebuild is micro-optimization, not duplicated
   policy.

5. Collapse `_iter_input_items` / permissions re-export: thin delegates; no
   second walk implementation.

**Independent consolidation search.** No additional production consolidation
warranted. Deferred (non-blocking) items from Worker 1 remain valid: stale
`_operator_bag_items` / `_iter_input_items` ownership docstrings; missing direct
`input_field_value` unit pin in `tests/utils/test_input_values.py` (indirect
coverage via permissions / `extract_branch_value` only); pytest gate deferred.

Verdict: **verified**. Plan checkbox marked `[x]`.
