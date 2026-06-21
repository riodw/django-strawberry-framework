# Review: `django_strawberry_framework/optimizer/selections.py`

Status: verified

## DRY analysis

- None — this module IS the DRY resolution for the optimizer's selection traversal, not a candidate for further consolidation. Its whole reason for existing is to single-source the two selection shapes (graphql-core AST and Strawberry converted) that previously lived split between `extension.py` and `walker.py` with `extension` importing edge-node helpers back from `walker` (see module docstring `optimizer/selections.py #"it previously lived split between them"`). The shared discriminators (`is_fragment`, `should_include`) are each defined once here and imported by all three consumers (`optimizer/walker.py:40,45`, the converted helpers, and `direct_child_selected` for `connection.py`), so the "recurse through fragments only" / directive-gate rules cannot drift. The two adapters are deliberately kept explicit (not merged into one polymorphic walker) per the cited review note; that is a correctness/readability decision, not duplication. The fragment-resolution split between the flat `resolve_unvisited_fragment` here and the depth-aware sibling in `extension.py:220` is intentional (different cycle-detection semantics), documented at the call site, and not a fold candidate.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `is_fragment` (`optimizer/selections.py::is_fragment`) is the single fragment-vs-field discriminator, consumed by `optimizer/walker.py:1046` (aliased `_is_fragment`), every converted-selection helper in this file, and `direct_child_selected`. `should_include` (`optimizer/selections.py::should_include`) is the single `@skip`/`@include` gate, reused by `included_field_selections`, `named_children`, `node_children_with_runtime_prefix`, and `direct_child_selected._check`, plus `optimizer/walker.py:55` aliases it as `_should_include`. `directive_variable_names` single-sources the `("skip", "include")` membership + `VariableNode` check for the AST cache-key walk (`optimizer/extension.py:168`). `ast_child_selections` centralizes the `getattr(node, "selection_set", None)` + `selections or ()` shape for the AST walkers (`optimizer/extension.py:85` alias `_child_selections`).
- **New helpers considered.** A single polymorphic walker over both selection shapes was considered and explicitly rejected by the original review quoted in the module docstring ("Keep the adapters explicit, but share the recursion and directive/fragment policies so the contracts cannot drift") — explicit adapters with shared policy primitives are the chosen shape. Folding `resolve_unvisited_fragment` (flat, this file) into `extension.py:220`'s depth-aware sibling was considered and rejected: they carry distinct cycle-detection semantics and the difference is documented at the sibling's definition.
- **Duplication risk in the current file.** Repeated literals flagged by the static overview are intentional: `"selections"` (10x) and `"directives"` (4x) are Django/graphql-core/Strawberry attribute names read off heterogeneous duck-typed objects (AST nodes, Strawberry dataclasses, `SimpleNamespace` shells) via `getattr` — they are protocol field names, not a dispatch key that could be hoisted. `"selected_fields"` (2x) is the Strawberry `cached_property` slot name used once to guard and once to populate in `prime_selected_fields`; both reads must name the same slot and live two lines apart, so a constant would not improve safety.

### Other positives

- **`ast_to_converted_selections` faithful-mirror discipline.** The docstring is explicit that this is a byte-identical mirror of Strawberry's `convert_selections` except for the one anonymous-inline-fragment branch (`type_condition=None` instead of dereferencing the missing condition at line `:116`), and that the identity is load-bearing because `prime_selected_fields` seeds the result into `info.selected_fields`. The output is built from Strawberry's own `SelectedField` / `FragmentSpread` / `InlineFragment` dataclasses so `isinstance`-based Strawberry consumers (`relay.utils.should_resolve_list_connection_edges`) keep working. Correct root-cause fix for the spec-valid anonymous inline fragment that Strawberry's `InlineFragment.from_node` crashes on.
- **`prime_selected_fields` fail-soft coupling is documented, not hidden.** The function honestly documents that it couples to two Strawberry internals (`Info._raw_info` and the `cached_property` dict-slot) and that a future Strawberry rename would SILENTLY no-op rather than fail loud, naming the live `test_anonymous_inline_fragment_*` regression net that would catch it on a version bump. Idempotent (`"selected_fields" in info.__dict__` guard) and a no-op when there are no field nodes — never overwrites a consumer that legitimately read the property first.
- **`direct_child_selected` recursion correctness.** Recurses only through `is_fragment` wrappers, not into a regular field's sub-selections, so a deeply nested `totalCount` inside `edges { node { ... } }` does not trip the OUTER connection's count predicate (`connection.py:390`). Gated on `should_include` so `totalCount @skip(if: true)` (or a `@skip`-ped fragment wrapping it) correctly suppresses the `COUNT`. Reflective-access audit clean: every `getattr` carries an `or ()`/`or []`/`or {}` default and there is no `setattr`/mutation of consumer objects (the only mutation is `visited_fragments.add` in `resolve_unvisited_fragment`, documented as the shared cycle-detection set).
- **Cycle-safe imports.** `walker.py` and `extension.py` both import from here; this module imports neither and depends only on graphql-core AST node types + stdlib (`SimpleNamespace`, `typing`) at module top, with the one `strawberry.types.nodes` import deferred inside `ast_to_converted_selections` to keep the substrate import-light. Verified: `grep` shows no first-party import from this file.

### Summary

`optimizer/selections.py` is the single-home selection-traversal substrate, unchanged since the baseline (`git diff 026de7d0 -- optimizer/selections.py` and `git diff HEAD -- optimizer/selections.py` both empty; prior artifact was `verified`). It is the resolution of a prior cross-module duplication (edge-node helpers no longer round-trip between `extension` and `walker`), so DRY is correctly a single `None —`. No logic defects: the anonymous-inline-fragment mirror, the documented fail-soft `prime_selected_fields` coupling, and the fragment-only recursion in `direct_child_selected` are all correct and well-justified. The TODO at `:315` is a properly anchored BACKLOG card (`polymorphic_interface_connections`) with an explicit reachability argument and is AGENTS.md-exempt. No GLOSSARY drift — these are private optimizer symbols with no `__all__` export, so absence of a GLOSSARY entry is correct (the "selection" prose in GLOSSARY refers to FieldSet / connection-planning / only-projection contracts, none of which name these helpers). The module docstring's `docs/feedback.md Major 2` reference resolves (the file exists on disk). Genuine no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged".
- `uv run ruff check --fix .` — pass; "All checks passed!".

### Notes for Worker 3
- No GLOSSARY-only fix in scope (no public symbol from this file appears in `docs/GLOSSARY.md`; absence is correct for private optimizer substrate with no `__all__`).
- DRY analysis is a single `None —`: the module IS the dedupe source (single-homed selection traversal; the edge-node helper round-trip between `extension`/`walker` was removed by this module's existence). No DRY items forwarded.
- All severities `None.` — no per-Low dispositions required.
- Baseline `026de7d0` and `HEAD` (`d63d77f8`) diffs for the target are both empty; prior artifact was `verified` and was overwritten cleanly (old Worker 3 banner intentionally dropped per the shape-#5 pattern).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring changes — logic review surfaced no stale or inaccurate comments. The module/function docstrings accurately describe the faithful-mirror contract, the fail-soft coupling, and the fragment-only recursion; the `docs/feedback.md Major 2` cross-reference resolves to an on-disk file; the `:315` TODO is correctly BACKLOG-anchored.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, or doc edits this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` is silent on any changelog entry for this item).

---

## Verification (Worker 3)

### Logic verification outcome
All severities are `None.`; no findings to dispose. Independently confirmed the artifact's `What looks solid` claims against live source:
- **AST/converted adapters genuine.** `ast_to_converted_selections` faithful-mirror with the single deviation `type_condition=(condition.name.value if condition is not None else None)` (`selections.py::ast_to_converted_selections._convert` #"if condition is not None else None"); built from Strawberry's own `SelectedField`/`FragmentSpread`/`InlineFragment` dataclasses (deferred import, keeps substrate import-light). `prime_selected_fields` idempotent + fail-soft: `if not field_nodes or "selected_fields" in info.__dict__: return` (:185) guards both no-nodes and already-primed; couples to `_raw_info` + dict-slot, documented as silently no-op on a Strawberry rename with the `test_anonymous_inline_fragment_*` net named (exists at `examples/fakeshop/test_query/test_library_api.py`, `test_glossary_api.py`).
- **Fragment/inline discriminators single-homed.** `is_fragment` duck-types on `type_condition` (:284); `should_include` is the single `@skip`/`@include` gate (:287-300, skip→if True / include→if False). Both aliased in walker.py:55-56 (`_should_include`/`_is_fragment`, used at :1046) and consumed by extension.py + connection.py.
- **Field-name resolution + reflective access clean.** `response_key` alias-or-name (:305); every `getattr` carries an `or ()`/`or []`/`or {}` default; the only mutation is `visited_fragments.add` in `resolve_unvisited_fragment` (:238), the documented shared cycle-detection set.
- **`direct_child_selected` fragment-only recursion.** `_check` recurses only through `is_fragment` wrappers, returns `getattr(child,"name",None)==name` for regular fields (:431-433) — pinned by `test_direct_child_selected_ignores_nested_field_selections` and `_honors_skip_include` (test_selections.py:242, :192).
- **Single-homed traversal consumed without drift.** Confirmed selections.py imports only stdlib + graphql-core AST (no first-party import). walker.py:38 and extension.py:67 both import from it; neither is imported back (cycle-safe claim holds). connection.py:67 imports `direct_child_selected` + `prime_selected_fields`, consumed at :390 / :442. All converted helpers aliased once per consumer (walker.py:55-62, extension.py:85-89) so the three consumers cannot drift.
- **Cited cross-refs resolve.** `docs/feedback.md` on disk; `test_walk_cache_relevant_vars_ignores_non_directive_objects` at test_extension.py:1434; `:315` TODO BACKLOG-anchored (`polymorphic_interface_connections`) with reachability argument, ERA001-exempt per AGENTS.md.

### DRY findings disposition
DRY is a single `None —` and that is correct: this module IS the dedupe resolution (single-homed selection traversal; the edge-node round-trip between extension/walker is removed by its existence). Grep confirms exactly two first-party importers (walker.py, extension.py) plus connection.py for the two public count/prime helpers, with no straggler at any old call site. Nothing forwarded.

### Temp test verification
None — no temp tests needed; behavior verified by grep + reading the named permanent tests in tests/optimizer/test_selections.py (14 tests covering every helper) and the cited extension/test_query regression nets.

### Shape #5 gates
- `git diff 026de7d0 -- …/selections.py` empty; `git diff HEAD -- …/selections.py` empty; owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty — no sibling attribution required.
- Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."
- All severities `None.`; no per-Low dispositions; no GLOSSARY-only fix (private symbols, no `__all__`, zero GLOSSARY matches — absence correct, not drift).
- Changelog `Not warranted` cites BOTH AGENTS.md and active-plan silence; `git diff -- CHANGELOG.md` empty. Internal-only framing matches the (empty) diff scope.
- Ruff format-check + check pass per the recorded validation log.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/selections.py` checkbox in `docs/review/review-0_0_11.md`.
