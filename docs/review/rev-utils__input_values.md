# Review: `django_strawberry_framework/utils/input_values.py`

Status: verified

## DRY analysis

- None — this module IS the DRY consolidation (the 0.0.9 `docs/feedback.md` Major 1 pass): it single-sites the set-input traversal mechanics (`iter_input_items` dict/dataclass walk, `is_inactive_value` `None`/`UNSET` rule, `iter_active_fields` leaf/related/logic classifier) that were previously re-spelled at four call sites (`filters/sets.py::FilterSet._normalize_input`, `orders/inputs.py::normalize_input_value`, `utils/permissions.py::active_permission_field_paths` / `active_related_branches`). All four consumers verified to drive the shared walker via `SetInputTraversal` config and filter the yielded `ActiveField` by `kind` (filters/sets.py:700-713, orders/inputs.py:298-319, permissions.py:160-169 / 204-217); the `is_inactive_value` rule is additionally reused inline at the operator-bag site (filters/sets.py:733). There is nothing left to consolidate — the file depends on no family package, so both families import it cycle-free. No further extraction candidate; deferring any further factoring would only add indirection.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical home that other surfaces now reuse: `filters/sets.py:700-713` and `orders/inputs.py:298-319` drive `iter_active_fields` with a `SetInputTraversal`; `utils/permissions.py:160-169` (`active_related_branches`) and `:204-217` (`active_permission_field_paths`) do the same, keeping only `RELATED` / `LEAF` records respectively; `permissions.py::extract_branch_value` (:106) and the filter operator-bag site (`filters/sets.py:733`) reuse `is_inactive_value` directly. `iter_input_items` is re-exported from `utils/permissions.py` (:34-52) so the legacy `from ..utils.permissions import iter_input_items` import path (filters/sets.py:51) keeps working — backward-compat re-export, not a duplicate.
- **New helpers considered.** None warranted. The two frozen dataclasses (`SetInputTraversal` config-in, `ActiveField` record-out) already give the cleanest neutral-walker contract; collapsing them would force the walker to know family leaf semantics, which the module deliberately refuses to do.
- **Duplication risk in the current file.** The `is_inactive_value` sentinel arm (`value is unset_sentinel`) degenerates to a second `value is None` test on the order side (default `unset_sentinel=None`); this is documented as a "harmless `value is None` repeat" (input_values.py:79-84) and is the single-sourcing point that prevents the `UNSET`/`None` decision from drifting across families — intentional, not a defect.

### Other positives

- **Three-way mutual-exclusion classification is correct and order-robust.** `iter_active_fields` (input_values.py:177-182) tests `logic_keys` first, then `related` membership, then falls through to `LEAF`. The module comment (input_values.py:41-47) correctly asserts logic attrs are never related names and vice-versa, so the logic-first ordering is cosmetic (mirrors `FilterSet._normalize_input`'s original branch order) rather than load-bearing. Order side passes `logic_keys=frozenset()` (default), so every non-related field falls to `LEAF` — matching "ordering has no logical operator bag."
- **Inactive-input skip applied at both granularities.** `is_inactive_value` gates the whole input (input_values.py:163) and each field (:174). The whole-input gate runs BEFORE the `handle_top_level_list` check, and a `list` is never `None`/sentinel, so a top-level order list is never spuriously skipped; recursion per element (`yield from iter_active_fields(...)`, :166-167) re-applies both gates to each element. Correct.
- **`iter_input_items` sniff is faithful to the package-wide convention.** dict → `.items()`; else `getattr(__dataclass_fields__, None)` duck-type (faster than `dataclasses.is_dataclass`, matches upstream Strawberry introspection); non-walkable → `None`; walkable-but-empty → `[]`. The `None`-vs-`[]` distinction is preserved by every consumer (`items is None: return {}` at filters/sets.py:683, `items is None: return` at :170 inside the walker).
- **`spec` / `related_obj` record fields are honestly optional.** `ActiveField.spec` is `None` when `field_specs` has no entry; `permissions.active_related_branches` deliberately passes `field_specs={}` (permissions.py:161) because it only reads `related_obj` / `raw_value` — the `None` spec never reached. `orders/inputs.py:305` skips defensively on `spec is None`; the filter leaf path falls back to `_form_key_for_python_attr` (filters/sets.py:722); `active_permission_field_paths` falls back to `fallback_path` (permissions.py:212-214). All four downstream `spec is None` handlings are consistent with the record's documented contract.
- **No import-time side effects, no Django/ORM access, no cycle risk.** Imports are stdlib-only (`collections.abc`, `dataclasses`, `typing`); zero Django/ORM markers in the shadow overview; both family packages import it without a cycle exactly as the docstring claims (same shape as `utils/permissions.py` / `utils/connections.py` / `utils/inputs.py`).
- **Frozen dataclasses** (`SetInputTraversal`, `ActiveField`) are immutable config/record carriers — no mutable shared state, safe to construct per-call.

### Summary

`utils/input_values.py` is a new 0.0.9 file and the realized form of `docs/feedback.md` Major 1: it single-sites the set-input traversal that FilterSet and OrderSet had independently grown, exposing a neutral `iter_active_fields` walker driven by a frozen `SetInputTraversal` config and yielding classified `ActiveField` records. All four documented consumers (two filter/order normalizers, two permission walkers) were verified at source to drive the walker as described and to handle the `spec is None` / `kind` dispatch consistently; the `is_inactive_value` rule is the single sentinel-decision point that the operator-bag site reuses too. The sentinel-arm degeneracy on the order side is documented and intentional, the inactive-skip is correctly applied at whole-input and per-field granularity (with the top-level-list flattening safely ordered after the whole-input gate), and the three-way classification is genuinely mutually exclusive. No High / Medium / Low findings; no GLOSSARY entry exists or is expected for an internal traversal substrate (consistent with prior-cycle calibration that internal scaffolding gets no GLOSSARY entry). Module is ruff-clean. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/utils/input_values.py` — `1 file already formatted` (pass; the COM812-formatter-conflict warning is the repo-wide standing config notice per AGENTS.md, not a finding).
- `uv run ruff check django_strawberry_framework/utils/input_values.py` — `All checks passed!`

### Notes for Worker 3
- No High / Medium / Low findings; nothing to disposition.
- No GLOSSARY-only fix in scope: grep of `docs/GLOSSARY.md` for every backticked symbol in this file (`input_values`, `iter_active_fields`, `iter_input_items`, `is_inactive_value`, `SetInputTraversal`, `ActiveField`, `extract_branch_value`) returns zero hits. Correct — this is an internal traversal substrate, not a public-contract symbol; no entry expected (consistent with prior-cycle calibration for internal scaffolding, e.g. `types/relations.py`).
- Cross-file consumer verification was performed read-only against `filters/sets.py`, `orders/inputs.py`, `utils/permissions.py` to confirm the documented four-consumer contract; no edits made to any of them.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. Docstrings and the `ActiveField.kind`-markers comment (input_values.py:41-47) are accurate, current, and cite the real `docs/feedback.md` Major 1 provenance (verified to exist at `docs/feedback.md:33`). The module/symbol docstrings correctly name the four live call sites and the kept-at-consumer leaf semantics. No comment edits warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (review-only), and AGENTS.md instructs not to update `CHANGELOG.md` unless explicitly instructed; the active plan (`docs/review/review-0_0_9.md`) is silent on a changelog edit for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to disposition (all None). Shape #5 no-source-edit cycle. Cycle diff for `django_strawberry_framework/utils/input_values.py` is EMPTY: tracked at baseline `0872a20`, `git diff 0872a20 HEAD -- <path>` empty AND worktree diff empty (byte-identical), file absent from `git status --short` — "Files touched: None" holds.

Independently drove the three contract claims LIVE (`uv run python`, stdlib-only module; no DB) rather than trusting prose:
- **`is_inactive_value` sentinel** — identity-based (`value is None or value is unset_sentinel`), NOT equality. Verified: order side (default `unset_sentinel=None`) skips only `None`; filter side (`unset_sentinel=UNSET`) skips both `None` and `UNSET`; falsy-but-supplied values `0`/`""`/`False`/`[]` are NOT skipped; an UNSET-like object is NOT skipped under the default `None` sentinel (no magic global); an adversarial `__eq__`-returns-True-for-None object is NOT skipped (proves `is` not `==`). The order-side sentinel-arm degeneracy to a second `value is None` is confirmed harmless and is the single sentinel-decision point.
- **Whole-input skip BEFORE `handle_top_level_list`** — `None` top-level list input with `handle_top_level_list=True` returns `[]` (the whole-input gate at :163 fires first; no crash, no spurious iteration); a genuine top-level `list` IS flattened element-by-element with per-element gates re-applied (`list` is never `None`/sentinel so the gate passes through to the list branch at :165); empty list yields nothing. Source-order assertion confirms the `is_inactive_value(input_value)` line precedes the `handle_top_level_list and isinstance(...list)` branch.
- **Three-way classification + 4-consumer consistency** — LOGIC/RELATED/LEAF mutually exclusive and config-driven; filter config (`logic_keys={and_}`, `unset_sentinel=UNSET`) classifies title→LEAF, and_→LOGIC, rel→RELATED (carrying `related_obj`), UNSET field skipped; order config (empty `logic_keys`) sends an `and_`-named attr to LEAF (no logic bag); non-walkable input (int) yields nothing; falsy related-collection (`related_orders=None`) handled via `or {}` at :172. Read all four consumers read-only: `filters/sets.py::FilterSet._normalize_input` (:700-713 + operator-bag `is_inactive_value` reuse :733), `orders/inputs.py::normalize_input_value` (:298-319, `handle_top_level_list=True`), `permissions.py::active_related_branches` (:160-169, keeps RELATED) and `active_permission_field_paths` (:204-217, keeps LEAF). All drive the walker via `SetInputTraversal` and dispatch on `kind`; the `spec is None` fallback is consistent (filter `_form_key_for_python_attr`, order defensive skip, permissions `fallback_path`).

### DRY findings disposition
None to action — this module IS the 0.0.9 DRY consolidation (`docs/feedback.md` Major 1). The artifact's "nothing left to consolidate" assessment holds; the two frozen dataclasses and the neutral walker are the correct single-site.

### Temp test verification
- Temp probe at `docs/review/temp-tests/utils__input_values/probe.py` drove all three contracts (sentinel grid, ordering, classification). All passed.
- Disposition: deleted (shipped behavior is already covered by the four live consumers and their tests; the probe was a verification aid, not new coverage).

### Sibling-cycle attribution
Every dirty path in the baseline diff stat attributes to a CLOSED sibling cycle (conf, connection, exceptions, filters.factories/sets, list_field, inspect_django_type, optimizer.extension/selections/walker, orders.factories/inputs, types.*, GLOSSARY re-export roster) all `Status: verified` + `[x]`, or is concurrent-maintainer work (db.sqlite3 artifact; feedback2/3.md delete = AGENTS #33; feedback4.md untracked). `input_values.py` itself byte-unchanged.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box. CHANGELOG diff empty (Not warranted, both citations present); ruff format-check + check pass (COM812 = standing repo config notice).
