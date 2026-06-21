# Review: `django_strawberry_framework/utils/input_values.py`

Status: verified

## DRY analysis

- None — this module *is* the consolidation point. It is the single-source set-input traversal substrate the 0.0.9 DRY pass (`docs/feedback.md` Major 1) extracted from four call sites: `filters/sets.py::FilterSet._normalize_input`, `orders/inputs.py::normalize_input_value`, and the two permission walkers (`utils/permissions.py::active_permission_field_paths` / `active_related_branches`, both now thin wrappers over `run_active_input_permission_checks`). All consume `iter_active_fields` / `SetInputTraversal` / `is_inactive_value` / `iter_input_items` from here (or re-export them via `utils/permissions.py`). The three helpers (`iter_input_items` lowest-level walk, `is_inactive_value` active-rule, `iter_active_fields` classifier) are deliberately split by abstraction level, not duplicated; folding them would merge distinct contracts (a `None`-vs-`[]` return distinction, a sentinel decision, and a leaf/related/logic dispatch). Re-consolidating the consolidation point is net-negative.

## High:

None.

## Medium:

None.

## Low:

### Nested-list recursion is unbounded but shape-unreachable

`iter_active_fields` (`utils/input_values.py::iter_active_fields #"yield from iter_active_fields(set_cls, element, config)"`) recurses per element when `config.handle_top_level_list` is set and `input_value` is a `list`. Because the recursive call again carries `handle_top_level_list=True`, a `list` *element* would itself be flattened — i.e. nested lists flatten transparently to arbitrary depth. This is correct-and-harmless today: `handle_top_level_list=True` is set only on the order side (`orders/inputs.py:301`, `orders/sets.py:363`) and threaded through the permission walkers (`utils/permissions.py:198/254/301`); the filter side leaves it `False` (`filters/sets.py:904`). The order resolver-facing argument shape is `list[<T>OrderInputType] | None`, never `list[list[...]]`, so a `list` element never occurs — each element is a dataclass or `None`. No action; the recursion termination relies on the input-shape invariant, not on a depth/type guard.

Defer until the order argument shape gains a nested-list variant (e.g. a `list[list[...]]` grouped-order input); at that point decide whether nested flattening is the intended semantics or whether the inner list should be rejected/treated as a leaf. Until then the duck-typed flatten is the minimal correct mechanic and a depth guard would be dead code (violates the 100% coverage gate).

### `field_specs.get((set_cls, python_attr))` keys off the leaf class, not the declaring class

The per-field provenance lookup keys on `(set_cls, python_attr)` (`utils/input_values.py::iter_active_fields #"spec = config.field_specs.get((set_cls, python_attr))"`), where `set_cls` is the concrete class passed by the consumer. Both `filters/inputs.py::_field_specs` (populated at `filters/inputs.py:704,747`) and `orders/inputs.py::_field_specs` (populated at `orders/inputs.py:241,252`) are keyed by the same concrete class during finalize, so the lookup hits. The miss path (`spec is None`) is handled explicitly by every consumer — the leaf permission path falls back to `fallback_path(field.python_attr)` (`utils/permissions.py::run_active_input_permission_checks`), the order normalizer `continue`s defensively (`orders/inputs.py::normalize_input_value #"Defensive -- should be impossible after a finalize."`), and `ActiveField.spec` is documented as nullable. So a key miss degrades safely rather than raising. No action; noted only because the keying assumes a flat `(class, attr)` map with no MRO walk — correct given finalize populates per concrete class, but a future subclass-without-refinalize path would silently take the fallback. No current code path produces that.

## What looks solid

### DRY recap

- **Existing patterns reused.** `iter_active_fields` is the canonical classifier consumed by all four set-input surfaces (`filters/sets.py:722`, `orders/inputs.py:304`, `utils/permissions.py:202`); `is_inactive_value` is the single active-input rule reused at `filters/sets.py:703,749`, `utils/permissions.py:125` (`extract_branch_value`), and internally; `iter_input_items` is the single dict-vs-dataclass walk re-exported through `utils/permissions.py:67` so legacy `from ..utils.permissions import iter_input_items` consumers keep working. The `LOGIC`/`RELATED`/`LEAF` kind markers are module constants compared by all consumers (`utils/permissions.py:202`, `orders/inputs.py:304`, `filters/sets.py:722`) — no stringly-typed drift (overview: 0 repeated string literals).
- **New helpers considered.** None warranted — the three-function split is by abstraction level (raw walk / active rule / classification), and the two frozen dataclasses (`SetInputTraversal` config, `ActiveField` record) already collapse what would otherwise be long positional argument lists at the call sites. The family configs (`filters/sets.py:100`, `orders/inputs.py:298`, `utils/permissions.py:193`) deliberately stay at their call sites — they reference family-specific maps / sentinels / flags and are not hoistable into the neutral module. No further extraction available without re-merging deliberately separated contracts.
- **Duplication risk in the current file.** The `is_inactive_value(input_value, ...)` whole-input guard (`:163`) and the per-field `is_inactive_value(raw_value, ...)` guard inside the loop (`:174`) look like a repeat, but they apply the same rule at two scopes (skip the entire input vs. skip one supplied field) — single-sited via the same helper, so there is no literal duplication, only two call sites of one function. Correct.

### Other positives

- **Family-neutral contract holds at every call site.** Each consumer drives the same `iter_active_fields` with a distinct `SetInputTraversal` and partitions by `.kind`: filter uses `logic_keys=_LOGIC_PYTHON_ATTRS` + `unset_sentinel=UNSET` (`filters/sets.py:100`); order uses empty `logic_keys` + default `None` sentinel + `handle_top_level_list=True` (`orders/inputs.py:298`); the permission walkers use field-spec-less / logic-key-less configs threaded through `run_active_input_permission_checks` (`utils/permissions.py:193`). The walker knows none of the family leaf semantics (operator bags, `Ordering` directions, `RangeFilter` patch, per-class `check_*` dedup) — those stay at the call sites exactly as the module docstring promises.
- **Classification order is provably safe.** Logic-vs-related test order is immaterial because the logical-operator python-attrs and the related-collection names are disjoint key spaces; the comment at `:41-47` documents this and states logic is tested first only to mirror `FilterSet._normalize_input`'s original branch order. `python_attr in config.logic_keys` (`:177`) and `python_attr in related` (`:179`) cannot both be true.
- **`None`-vs-`[]` return contract on `iter_input_items` is load-bearing and respected.** `None` (non-walkable input) and `[]` (walkable-but-empty) are distinct: `iter_active_fields` returns early on `items is None` (`:170`) and naturally yields nothing for `[]`. The docstring states both cases explicitly.
- **Inactive-value rule is sentinel-parametrized, not hardcoded.** `unset_sentinel` threads `strawberry.UNSET` (filter side) vs `None` (order side) through one helper; the order side's `None` sentinel makes the second arm a harmless `value is None` repeat rather than a special case. The decision cannot drift between normalizers, permission walkers, and `extract_branch_value`.
- **Zero Django/ORM surface.** Static overview confirms no `_meta`, no QuerySet, no reflective Django access — `getattr` calls are only the dataclass-field walk (`__dataclass_fields__` at `:68`, attribute read at `:71`) and the `related_attr` collection read (`:172`), both duck-typed by design so the module depends on no family package (no import cycle, mirroring `utils/permissions.py` / `utils/connections.py` / `utils/inputs.py`).
- **`getattr(set_cls, config.related_attr, {}) or {}`** (`:172`) defends both the missing-attr and falsy-attr cases before the membership test — a class without a related collection classifies every non-logic field as a leaf rather than raising.
- **Typing is honest.** `field_specs: Mapping[Any, Any]` and `spec: Any | None` are deliberately loose because the module is family-neutral (the value is a filter or order `FieldSpec` it never introspects); `Iterator[ActiveField]` is the precise public contract.

### Summary

`utils/input_values.py` is the neutral set-input traversal substrate extracted by the 0.0.9 DRY pass. It is byte-identical to the cycle baseline `8fb4f27c` (`git diff 8fb4f27c -- <target>`, `git diff HEAD -- <target>`, and `git log 8fb4f27c..HEAD -- <target>` all empty). It is the single-source classifier for all four set-input surfaces; the three-helper-plus-two-dataclass factoring is correct and not further consolidatable without re-merging deliberately separated contracts. No High/Medium findings. Two forward-looking Lows, both re-confirmed correct-as-is and trigger-gated (nested-list recursion is shape-unreachable; `(set_cls, attr)` keying assumes finalize-per-concrete-class with no MRO walk). No GLOSSARY entry exists for any symbol (all dotted-path imports, none in `utils/__init__.py.__all__`) — absence is correct. No-source-edit cycle (Shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged`.
- `uv run ruff check --fix .` — `All checks passed!`.

### Notes for Worker 3
- Both Lows are forward-looking and trigger-gated; neither requires a source edit this cycle:
  - Nested-list recursion (`iter_active_fields`): correct-and-shape-unreachable (only `orders/inputs.py:301` / `orders/sets.py:363` set `handle_top_level_list=True` plus the permission walkers `utils/permissions.py:198/254/301`; filter side leaves it `False` at `filters/sets.py:904`; shape is `list[<T>] | None`, never nested). Trigger = a nested-list order-argument variant lands. A depth guard today would be dead code under the 100% coverage gate.
  - `field_specs.get((set_cls, python_attr))` keying: degrades safely (`spec is None` handled by every consumer); flat `(class, attr)` keying is correct because finalize populates per concrete class (`filters/inputs.py:704,747`; `orders/inputs.py:241,252`). Trigger = a subclass-without-refinalize path appears.
- No GLOSSARY-only fix in scope: `grep -ni` over `docs/GLOSSARY.md` returns zero hits for `iter_active_fields` / `is_inactive_value` / `iter_input_items` / `SetInputTraversal` / `ActiveField` / `input_values`. All symbols are dotted-path imports, none in `utils/__init__.py.__all__` (`utils/__init__.py:33-41`); the line-16 reference is module-docstring prose, not an export. Absence is correct, no drift.
- Cycle diff empty: `git diff 8fb4f27c -- <target>`, `git diff HEAD -- <target>`, and `git log 8fb4f27c..HEAD -- <target>` all empty; the module is fully cumulative-in-HEAD.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — docstrings are accurate (the `None`-vs-`[]` contract, the sentinel parametrization, the traversal-mechanics-only scope, and the no-recursion-into-children boundary are all correctly stated and verified against the three consumer call sites). No stale TODOs (overview: TODO comments none). The `LOGIC`/`RELATED`/`LEAF` marker comment block (`:41-47`) correctly documents the disjoint-key-space rationale for classification order.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_11.md`, which is silent on changelog edits for review artifacts).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle, terminal-verify. No High/Medium to address. Both Lows independently re-confirmed correct-as-is and trigger-gated:

- **Nested-list recursion (`iter_active_fields #"yield from iter_active_fields(set_cls, element, config)"`):** the recursive call re-carries `config` (so `handle_top_level_list` stays `True` for elements). `grep -rn handle_top_level_list` confirms `=True` is set ONLY on the order side (`orders/inputs.py:301`, `orders/sets.py:363`) and threaded through the three permission walkers (`utils/permissions.py:198/254/301`); the filter side leaves it `False` (`filters/sets.py:904` docstring). Order argument shape is `list[<T>] | None`, never `list[list[...]]`, so a `list` element never occurs -> shape-unreachable today. Trigger (a nested-list order-argument variant) is valid and forward-looking; a depth guard would be dead code under the 100% gate. Accept.
- **`field_specs.get((set_cls, python_attr))` leaf-class keying (`#"spec = config.field_specs.get((set_cls, python_attr))"`):** `grep '_field_specs\['` confirms both maps are populated keyed by the concrete class at finalize (`filters/inputs.py:704,747`; `orders/inputs.py:241,252`), so the flat `(class, attr)` lookup hits with no MRO walk. The miss path (`spec is None`) is carried on the `ActiveField` record and handled by every consumer (leaf fallback / order defensive `continue` / nullable `ActiveField.spec`), so a key miss degrades safely rather than raising. Trigger (subclass-without-refinalize) is valid. Accept.

Family-neutral contract independently confirmed: `iter_active_fields` is driven by all four set-input surfaces (`filters/sets.py:722`, `orders/inputs.py:304`, both permission walkers via `run_active_input_permission_checks` at `utils/permissions.py:202`), each with a distinct `SetInputTraversal` and partition by `.kind`; `is_inactive_value` is the single active-input rule reused at the filter normalizer, `extract_branch_value` (`utils/permissions.py:125`), and internally. `handle_top_level_list` path verified (`input_values.py:165-167`). The walker carries no family leaf semantics.

### DRY findings disposition
DRY-None genuine: this module IS the consolidation point (0.0.9 DRY pass, `docs/feedback.md` Major 1). The three-helper-plus-two-dataclass factoring splits by abstraction level (raw walk / active rule / classification) with distinct contracts (`None`-vs-`[]` return, sentinel decision, leaf/related/logic dispatch); re-merging would re-couple deliberately separated contracts. No carry-forward.

### Temp test verification
None used — no-source-edit cycle, both Lows shape-unreachable/trigger-gated, no behavior to prove.

### GLOSSARY / shape gate
`grep -ni` over `docs/GLOSSARY.md` returns ZERO hits for every symbol (`iter_active_fields` / `is_inactive_value` / `iter_input_items` / `SetInputTraversal` / `ActiveField` / `input_values`). The `utils/__init__.py:15-16` reference is module-docstring prose, NOT `__all__` (the `__all__` tuple at `:33-41` contains none of these symbols — all consumers use dotted-path imports). Absence of a GLOSSARY entry is correct -> genuine #5, not a #4-disguised-as-#5. No GLOSSARY-only fix present. All three Worker 2 sections open with the no-source-edit gate line.

### Validation
- Zero-edit proof clean on all axes: `git diff 8fb4f27c -- <target>`, `git diff HEAD -- <target>`, `git log 8fb4f27c..HEAD -- <target>` all empty; owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty; no sibling-cycle attribution needed.
- Changelog `Not warranted`: `git diff -- CHANGELOG.md` empty; disposition cites BOTH `AGENTS.md` and active-plan silence; internal-only framing matches zero diff scope.
- `uv run ruff format --check` -> 2 files already formatted; `uv run ruff check` -> All checks passed!

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/input_values.py` checklist box in `docs/review/review-0_0_11.md`.
