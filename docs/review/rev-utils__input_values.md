# Review: `django_strawberry_framework/utils/input_values.py`

Status: verified

## DRY analysis

- None — this module *is* the consolidation point. It is the single-source set-input traversal substrate the 0.0.9 DRY pass (`docs/feedback.md` Major 1) extracted from four call sites: `filters/sets.py::FilterSet._normalize_input`, `orders/inputs.py::normalize_input_value`, and the two permission walkers (`utils/permissions.py::active_permission_field_paths` / `active_related_branches`, both now thin wrappers over `active_permission_targets`). All four import `iter_active_fields` / `SetInputTraversal` / `is_inactive_value` / `iter_input_items` from here (or re-export them via `utils/permissions.py`). The three helpers (`iter_input_items` lowest-level walk, `is_inactive_value` active-rule, `iter_active_fields` classifier) are deliberately split by abstraction level, not duplicated; folding them would merge distinct contracts (a `None`-vs-`[]` return distinction, a sentinel decision, and a leaf/related/logic dispatch). Re-consolidating the consolidation point is net-negative.

## High:

None.

## Medium:

None.

## Low:

### Nested-list recursion is unbounded but shape-unreachable

`iter_active_fields` (`utils/input_values.py::iter_active_fields #"yield from iter_active_fields(set_cls, element, config)"`) recurses per element when `config.handle_top_level_list` is set and `input_value` is a `list`. Because the recursive call again carries `handle_top_level_list=True`, a `list` *element* would itself be flattened — i.e. nested lists flatten transparently to arbitrary depth. This is correct-and-harmless today: the only caller setting the flag is `orders/inputs.py::normalize_input_value`, whose resolver-facing argument shape is `list[<T>OrderInputType] | None`, never `list[list[...]]`, so a list element never occurs. Each element is a dataclass or `None`. No action; the recursion termination relies on the input-shape invariant, not on a depth/type guard.

Defer until the order argument shape gains a nested-list variant (e.g. a `list[list[...]]` grouped-order input); at that point decide whether nested flattening is the intended semantics or whether the inner list should be rejected/treated as a leaf. Until then the duck-typed flatten is the minimal correct mechanic and a depth guard would be dead code (violates the 100% coverage gate).

### `field_specs.get((set_cls, python_attr))` keys off the leaf class, not the declaring class

The per-field provenance lookup keys on `(set_cls, python_attr)` (`utils/input_values.py::iter_active_fields #"spec = config.field_specs.get((set_cls, python_attr))"`), where `set_cls` is the concrete class passed by the consumer. Both `filters/inputs.py::_field_specs` and `orders/inputs.py::_field_specs` are populated keyed by the same concrete class during finalize, so the lookup hits. The miss path (`spec is None`) is handled explicitly by every consumer — the leaf permission path falls back to `fallback_path(field.python_attr)` (`utils/permissions.py` `active_permission_targets`), the order normalizer `continue`s defensively (`orders/inputs.py::normalize_input_value #"Defensive -- should be impossible after a finalize."`), and `ActiveField.spec` is documented as nullable. So a key miss degrades safely rather than raising. No action; noted only because the keying assumes a flat `(class, attr)` map with no MRO walk — correct given the finalize populates per concrete class, but a future subclass-without-refinalize path would silently take the fallback. No current code path produces that.

## What looks solid

### DRY recap

- **Existing patterns reused.** `iter_active_fields` is the canonical classifier consumed by all four set-input surfaces (`filters/sets.py:715`, `orders/inputs.py:304`, `utils/permissions.py:199`); `is_inactive_value` is the single active-input rule reused at `filters/sets.py:742`, `utils/permissions.py:122` (`extract_branch_value`), and internally; `iter_input_items` is the single dict-vs-dataclass walk re-exported through `utils/permissions.py:67` so legacy `from ..utils.permissions import iter_input_items` consumers keep working. The `LOGIC`/`RELATED`/`LEAF` kind markers are module constants compared by all consumers (`utils/permissions.py:200,206`, `orders/inputs.py:307`) — no stringly-typed drift.
- **New helpers considered.** None warranted — the three-function split is by abstraction level (raw walk / active rule / classification), and the two frozen dataclasses (`SetInputTraversal` config, `ActiveField` record) already collapse what would otherwise be long positional argument lists at the call sites. No further extraction available without re-merging deliberately separated contracts.
- **Duplication risk in the current file.** The `is_inactive_value(input_value, ...)` whole-input guard and the per-field `is_inactive_value(raw_value, ...)` guard inside the loop look like a repeat, but they apply the same rule at two scopes (skip the entire input vs. skip one supplied field) — single-sited via the same helper, so there is no literal duplication, only two call sites of one function. Correct.

### Other positives

- **`None`-vs-`[]` return contract on `iter_input_items` is load-bearing and respected.** `None` (non-walkable input) and `[]` (walkable-but-empty) are distinct: `iter_active_fields` returns early on `items is None` and naturally yields nothing for `[]`. The docstring states both cases explicitly.
- **Inactive-value rule is sentinel-parametrized, not hardcoded.** `unset_sentinel` threads `strawberry.UNSET` (filter side) vs `None` (order side) through one helper; the order side's `None` sentinel makes the second arm a harmless `value is None` repeat rather than a special case. The decision cannot drift between normalizers, permission walkers, and `extract_branch_value`.
- **Zero Django/ORM surface.** Static overview confirms no `_meta`, no QuerySet, no reflective Django access — `getattr` calls are only the dataclass-field walk (`__dataclass_fields__`, attribute read) and the `related_attr` collection read, both duck-typed by design so the module depends on no family package (no import cycle, mirroring `utils/permissions.py` / `utils/connections.py` / `utils/inputs.py`).
- **`getattr(set_cls, config.related_attr, {}) or {}`** defends both the missing-attr and falsy-attr cases before the membership test — a class without a related collection classifies every non-logic field as a leaf rather than raising.
- **Typing is honest.** `field_specs: Mapping[Any, Any]` and `spec: Any | None` are deliberately loose because the module is family-neutral (the value is a filter or order `FieldSpec` it never introspects); `Iterator[ActiveField]` is the precise public contract.

### Summary

`utils/input_values.py` is the neutral set-input traversal substrate extracted by the 0.0.9 DRY pass and is byte-identical to baseline 14910230 (empty `git log 14910230..HEAD` and empty `git diff HEAD`). It is the single-source classifier for all four set-input surfaces; the three-helper-plus-two-dataclass factoring is correct and not further consolidatable without re-merging deliberately separated contracts. No High/Medium findings. Two forward-looking Lows, both correct-as-is and trigger-gated (nested-list recursion is shape-unreachable; `(set_cls, attr)` keying assumes finalize-per-concrete-class with no MRO walk). No GLOSSARY mentions of any symbol. No-source-edit cycle (Shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged.
- `uv run ruff check .` — pass; all checks passed.

### Notes for Worker 3
- Both Lows are forward-looking and trigger-gated; neither requires a source edit this cycle:
  - Nested-list recursion (`iter_active_fields`): correct-and-shape-unreachable (only `orders/inputs.py` sets `handle_top_level_list`, shape is `list[<T>] | None`, never nested). Trigger = a nested-list order-argument variant lands. A depth guard today would be dead code under the 100% coverage gate.
  - `field_specs.get((set_cls, python_attr))` keying: degrades safely (`spec is None` handled by every consumer); flat `(class, attr)` keying is correct because finalize populates per concrete class. Trigger = a subclass-without-refinalize path appears.
- No GLOSSARY-only fix in scope (no GLOSSARY mentions of any symbol in this module).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — docstrings are accurate (the `None`-vs-`[]` contract, the sentinel parametrization, the traversal-mechanics-only scope, and the no-recursion-into-children boundary are all correctly stated). No stale TODOs (overview: TODO comments none).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for review artifacts).

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit (Shape #5) cycle; H0/M0. Both Lows verified genuinely forward-looking against LIVE source, each with verbatim in-source trigger phrasing:

- **Low 1 (nested-list recursion in `iter_active_fields`):** `handle_top_level_list=True` is set only on the order side (`orders/inputs.py:301`; the three permission walkers thread it through at `utils/permissions.py:195/251/298`). The filter side explicitly leaves it `False` (`filters/sets.py:897`). The order resolver argument shape is `list[<T>OrderInputType] | None`, never `list[list[...]]`, so a `list` *element* never occurs and the per-element recursion (`input_values.py:166-167`) terminates on the dataclass/`None` leaf. A depth/type guard today would be dead code under the 100% coverage gate. Trigger = a nested-list grouped-order argument variant lands. Correct-as-is, no source-site TODO owed (gated on an unrealized future input shape, not a staged framework slice).
- **Low 2 (`field_specs.get((set_cls, python_attr))` keys off the leaf class):** both populators key by the concrete class at finalize — `filters/inputs.py:703,746` and `orders/inputs.py:241,252` all write `_field_specs[(<set>_cls, python_attr)]`. The `spec is None` miss path degrades safely: the leaf permission path falls back to `fallback_path(field.python_attr)` (`utils/permissions.py:204`), the order normalizer `continue`s defensively (`orders/inputs.py:305-306` `# Defensive -- should be impossible after a finalize.`), and `ActiveField.spec` is documented nullable. Flat `(class, attr)` keying is correct given finalize-per-concrete-class; trigger = a subclass-without-refinalize path appears. Forward-looking, no action.

No missed logic. The whole-input vs per-field `is_inactive_value` double call (`input_values.py:163` / `:174`) is one rule applied at two scopes, not duplication. The `None`-vs-`[]` `iter_input_items` contract is load-bearing and respected (early-return on `items is None` at `:170`, natural empty-yield for `[]`). Zero Django/ORM surface (shadow: Django/ORM markers None).

### DRY findings disposition
DRY None confirmed by grep: `iter_input_items` / `is_inactive_value` / `iter_active_fields` each have exactly one `def`; `SetInputTraversal` / `ActiveField` each one class def (all in `utils/input_values.py`). Consumed by all four set-input surfaces — `filters/sets.py:39`, `orders/inputs.py:31`, and `utils/permissions.py:35` (which re-exports `iter_input_items` and drives `iter_active_fields` from the three thin permission-walker wrappers over `active_permission_targets`). This module IS the single consolidation point; re-consolidating its three abstraction-level-split helpers would re-merge the deliberately separated `None`-vs-`[]`, sentinel, and leaf/related/logic contracts — net-negative. Sound.

### Temp test verification
- None — no behavior suspicion required a temp test; both Lows are statically decidable from the input-shape invariant + finalize populators.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/input_values.py` checklist box in `docs/review/review-0_0_10.md`.

Shape #5 gates all met: (a) zero this-cycle edits — `git diff HEAD -- django_strawberry_framework/utils/input_values.py` empty, last-touch `129edd98` (2026-06-13) predates HEAD `58ca2def` (prompt baseline `14910230` is stale; content verified by grep per content-not-identifier); (b) all three Worker 2 sections open `Filled by Worker 1 per no-source-edit cycle pattern.`; (c) both Lows have verbatim in-source trigger phrasing, no GLOSSARY-only fix (no GLOSSARY mentions of any symbol); (d) changelog `Not warranted` cites BOTH AGENTS.md and active-plan silence, `git diff HEAD -- CHANGELOG.md` empty; (e) `uv run ruff format --check` + `uv run ruff check` both pass on the target.
