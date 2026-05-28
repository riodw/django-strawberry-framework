# Build: Cross-slice integration pass — spec-021 filters / 0.0.8

Spec reference: `docs/spec-021-filters-0_0_8.md` (build plan: `docs/builder/build-021-filters-0_0_8.md`)
Status: final-accepted

## Scope (Worker 1)

This artifact is the cross-slice DRY scan run after all six slice boxes in `build-021-filters-0_0_8.md` are `[x]`. Each per-slice artifact closed `final-accepted`; the integration pass walks the union of those artifacts (plus the shadow overviews under `docs/shadow/` and the per-file diff against the working tree) for duplicated helpers, repeated literals, sibling-boundary import drift, and silently-broadened public surface introduced by the build.

**Prior-slice artifact set walked in slice order:**

- `docs/builder/bld-slice-1-foundation.md` — Slice 1 foundation modules, primitives, FilterSet/Metaclass.
- `docs/builder/bld-slice-2-factories.md` — `FilterArgumentsFactory` BFS + dynamic-filterset cache + Layer-5 input builders.
- `docs/builder/bld-slice-3-wiring.md` — `Meta.filterset_class` promotion + finalizer phase 2.5 binding.
- `docs/builder/bld-slice-4-live_http_coverage.md` — fakeshop library filtersets + 14 live HTTP tests.
- `docs/builder/bld-slice-4a-tree_form_logic.md` — `FilterSet.filter_queryset` tree-form override.
- `docs/builder/bld-slice-5-docs_kanban_changelog.md` — GLOSSARY / KANBAN / CHANGELOG / README / docs/README / docs/TREE / GOAL / TODAY / CSV.
- `docs/builder/bld-slice-6-composition_smoke_test.md` — procedural-closure-only ("carried by sibling" per spec L161).

**Spec status-line re-verification.** `docs/spec-021-filters-0_0_8.md` L4 currently reads "core wiring shipped through Slice 3, live HTTP coverage shipped through Slice 4, tree-form logic substrate shipped through Slice 4a, docs / KANBAN / CHANGELOG shipped through Slice 5; Slice 6 composition smoke tests closed as 'carried by sibling' per the Slice-checklist conditional clause." This matches the actual build outcome — every slice ticked `[x]` reflects shipped state. No status-line edit needed in this pass.

## Static-inspection helper coverage audit

`scripts/review_inspect.py` was run during the build cycle as follows; the integration pass confirms the coverage is complete for the surfaces this build touched:

- `django_strawberry_framework/filters/__init__.py` — Slice 1 review pass ran the helper (overview at `docs/shadow/django_strawberry_framework__filters____init__.overview.md`). Re-confirmed: 1 control-flow hotspot (none in `__init__`); imports section reads `.base` + `.sets` + `.inputs.INPUTS_MODULE_PATH` (one-way only — `__init__` reads from siblings, no sibling reads from `__init__`).
- `django_strawberry_framework/filters/base.py` — Slice 1 review pass ran the helper (`docs/shadow/django_strawberry_framework__filters__base.overview.md`). No filter-package internal imports; only `django_filters` + `django.forms` + `strawberry.relay` + the package's `..exceptions`.
- `django_strawberry_framework/filters/sets.py` — Slice 1 + Slice 2 minor-delta + Slice 4a + Slice 3 / 5 updates: helper run during Slice 1 (planning), Slice 2 (review re-run threshold not hit per Worker-3 note), Slice 3 (review pass), and Slice 4a (planning + review). Latest shadow at `docs/shadow/django_strawberry_framework__filters__sets.overview.md`.
- `django_strawberry_framework/filters/inputs.py` — Slice 1 (declaration-only stub), Slice 2 (full helper run on the populated module per Worker 3), Slice 3 (`materialize_input_class` / `clear_filter_input_namespace` additions; Worker 3 re-ran), Slice 4a (no significant delta).
- `django_strawberry_framework/filters/factories.py` — Slice 2 (Worker 3 helper run). No subsequent slice added logic to factories.py.
- `django_strawberry_framework/types/finalizer.py` — Slice 3 (Worker 3 helper run for the phase-2.5 four-subpass binding addition).
- `django_strawberry_framework/types/definition.py` — Slice 3 (Worker 3 helper run for `related_target_for` and `filterset_class` slot).
- `django_strawberry_framework/types/base.py` — Slice 3 (`Meta.filterset_class` promotion from DEFERRED_META_KEYS; helper not re-run because the delta was ≤30 lines per Worker 3 — recorded skip with reason in Slice 3 review).
- `django_strawberry_framework/registry.py` — Slice 3 (`registry.clear()` extension for the filter input namespace + `_helper_referenced_filtersets` clearer; helper not re-run — Worker 3 recorded skip; delta is the inline `clear()` body, no new symbols).
- `examples/fakeshop/apps/library/schema.py` — Slice 4 (Worker 3 helper run for the six wired DjangoTypes and the six root resolvers).
- `examples/fakeshop/apps/library/filters.py` AND `filters_genre.py` — Slice 4 (Worker 3 review noted these are pure-class-definition modules — pure FilterSet subclass declarations with `Meta` blocks and `check_*_permission` / `email_must_have_at_sign` methods; recorded skip per BUILD.md "pure-class-definition module" exemption).
- `examples/fakeshop/test_query/test_library_api.py` — Slice 4 + Slice 4a delta (Worker 3 helper runs at each pass for the 14 new tests + the xfail strip).

**Coverage complete.** Every `.py` file with review-worthy logic touched by build-021 had the helper run at least once or had an explicitly-recorded skip with reason. The integration pass does not require additional helper runs because no new files are introduced by this pass itself.

## Cross-slice repeated-literal scan (Repeated string literals section across shadow overviews)

Walked `docs/shadow/django_strawberry_framework__filters__*.overview.md` and `docs/shadow/django_strawberry_framework__types__*.overview.md` Repeated-string-literals sections. The only filter-package overview that surfaced literals above threshold is `sets.py`, which lists `4x related_filters`, `2x _expanded_filters`, `2x is_relation`, `2x __dataclass_fields__`, `2x _permission`. None of these are cross-module — they are intra-file Python attribute / dunder names that consolidating would harm rather than help (they ARE the attribute names being read; you cannot factor a `getattr` target string).

The cross-module duplications that DO matter for this pass are below; the AST static helper does not report them because they appear at most once per file (so neither file's "Repeated string literals" section flags them, but the cross-file diff does).

## Cross-slice import / sibling-boundary direction check

From the shadow overviews' Imports sections, the runtime dependency direction inside `django_strawberry_framework/filters/`:

```
base.py       (leaf — no internal filter-package imports)
   ↑
inputs.py     (imports .base; .sets and .factories only in TYPE_CHECKING / local-inside-function form)
   ↑
sets.py       (imports .base AND .inputs at module top)
   ↑
factories.py  (imports .inputs AND .sets at module top)
   ↑
__init__.py   (imports .base, .sets, and .inputs)
```

This is a clean one-way dependency direction with one wrinkle: `inputs.py` carries a `if TYPE_CHECKING: from .sets import FilterSet` at line 45, plus a deferred `from .factories import FilterArgumentsFactory` and `from .sets import FilterSet` inside `clear_filter_input_namespace` (lines 753 / 766). These are intentional — Slice 2's reviewer noted they exist to (a) keep the public `FilterSet` type-annotation legible at type-check time without creating a runtime cycle, and (b) let `clear_filter_input_namespace` walk filter-input-class subclasses lazily without importing the world at module-load time. No sibling-boundary violation; the type-checking + lazy-local pattern is the right shape.

No `types/` module imports from `filters/`, and no test tree imports across slice boundaries in ways the slice plans did not authorize.

## Walk of `What looks solid` and `DRY findings` across accepted slices (deferred carry-forwards)

Pulled from each prior-slice artifact:

- **Slice 1** — `DRY findings` empty at slice boundary; review surfaced two intra-file structural duplications (`_derive_related_visibility_querysets_sync` / `_async`; `apply_sync` / `apply_async`) explicitly labelled "Not a finding — structurally necessary (Python's sync/async colored-function boundary)". Confirmed: no consolidation candidate.
- **Slice 2** — `DRY findings` named exactly the two items this integration pass folds: (a) `_LOGIC_KEYS` duplicated byte-for-byte in `sets.py` and `inputs.py`; (b) `f"{Name}InputType"` literal at five sites. Both items explicitly handed off to the integration pass with recommended-fix shape.
- **Slice 3** — `DRY findings` empty at slice boundary; surfaced one cross-cutting helper observation (`_target_type_for_related_filter` + `_resolve_relation_target_type` both ending at `registry.primary_for(model) or registry.get(model)`) — Slice 3 reviewer judged "symbol clarity at the call sites is currently fine; worth raising at integration if a third call site appears." Confirmed at the integration pass: no third call site appeared in Slices 4 / 4a / 5 / 6. **Not in scope this pass.**
- **Slice 4** — `DRY findings` flagged `_form_key_for_python_attr` and `_django_lookup_for_python_attr` as identical and consolidated within Slice 4 itself (Worker-2 collapsed the pair). No carry-forward to integration.
- **Slice 4a** — `DRY findings` empty; the tree-walker at `sets.py::FilterSet._q_for_logic_tree` consumes raw `"and" / "or" / "not"` string literals (lines 779 / 783 / 790) rather than `_LOGIC_KEYS`'s second-element values. **Observation:** once `_LOGIC_KEYS` becomes a single source-of-truth (this pass's first fold), the tree-walker could optionally consult `dict(_LOGIC_KEYS).values()` for the trio rather than hardcoding the strings — but the walker code reads more cleanly with the explicit `tree_data.get("and")` / `.get("or")` / `.get("not")` calls than it would with an indirection through the constant. **Decision: NOT in scope this pass.** The raw-string usages are exactly three call-sites in one function, all visually adjacent, and each has a distinct branch shape (AND-intersect / OR-union with separate accumulator / NOT-negate single child). Consolidation would obscure the branch semantics. The integration finding for `_LOGIC_KEYS` stays scoped to the cross-module duplication between `sets.py:53-57` and `inputs.py:108-112` only.
- **Slice 5** — `DRY findings` empty at slice boundary (doc-only slice; no Python edits).
- **Slice 6** — `DRY findings` empty (procedural-closure-only; no diff).

## Cross-slice findings

### M1: `_LOGIC_KEYS` byte-for-byte duplicated across `sets.py` and `inputs.py` (Medium)

`django_strawberry_framework/filters/sets.py::_LOGIC_KEYS` (lines 53-57) and `django_strawberry_framework/filters/inputs.py::_LOGIC_KEYS` (lines 108-112) define the same tuple value:

```python
_LOGIC_KEYS: tuple[tuple[str, str], ...] = (
    ("and_", "and"),
    ("or_", "or"),
    ("not_", "not"),
)
```

The literal IS the source of truth for the spec L1007 / H6-of-rev2 Python-attr-vs-GraphQL-name pairing (`and_` Python attr → `and` GraphQL name; same for `or` / `not`). Two definitions of the same vocabulary is exactly the "repeated tuple shape across slices" failure mode BUILD.md severity-Medium calls out: a future edit at one site (adding `xor` or renaming `not_` to `not_branch`, hypothetically) leaves the other site silently stale and the runtime would split across the two definitions in obscure ways depending on import order.

**Worker-2 history.** Slice 2's `### Implementation notes` explicitly documented this duplication: "the two constants are byte-for-byte identical; integration-pass DRY review will likely fold them." Slice 2's `### DRY analysis` (Risk 4) listed both options; Worker 2 chose the duplication path to avoid churning `sets.py`'s import / use site at the time. The expectation Worker 2 recorded was that the integration pass would fold to one source.

**Consolidation shape.**

1. Delete `_LOGIC_KEYS` constant from `django_strawberry_framework/filters/sets.py` lines 53-57 (including the leading docstring/comment block at lines 49-52).
2. Extend `django_strawberry_framework/filters/sets.py` line 35's existing import block:

   ```python
   from .inputs import LOOKUP_NAME_MAP, _LOGIC_KEYS, _field_specs, normalize_input_value
   ```

3. The use site at `sets.py:438` (`logic_lookup = dict(_LOGIC_KEYS)`) needs no edit — the bound name stays the same.
4. Verify no test references either `sets.py::_LOGIC_KEYS` or `inputs.py::_LOGIC_KEYS` directly (confirmed via `grep -rn "_LOGIC_KEYS" tests/ examples/` — zero hits).

**Risk surface.**

- Cycle risk: `sets.py` already imports `LOOKUP_NAME_MAP`, `_field_specs`, and `normalize_input_value` from `.inputs` at line 35 today. Adding `_LOGIC_KEYS` to the same import does NOT introduce a new cycle.
- Reverse direction: `inputs.py` does NOT import from `.sets` at module top (only under TYPE_CHECKING at line 45 and as a deferred local import at line 766); folding the duplicate into `.inputs` keeps `.inputs` as the "vocabulary owner" and preserves the one-way `sets → inputs` direction.

**Test consequence.** No new tests required; existing Slice-1 + Slice-2 tests cover `_normalize_input`'s `_LOGIC_KEYS` consumption (`test_normalize_input_maps_logical_and_python_attr_to_and_form_key` and friends) and Slice-2's `_build_logic_fields` consumption (`test_build_logic_fields_emits_three_self_referential_fields` and friends). Removing the duplicate constant does not change any observable behavior.

**Severity Medium** per BUILD.md "repeated literal / key / tuple that should be a named constant" — the entire 5-line tuple definition appears verbatim in both files.

### M2: `f"{<class>.__name__}InputType"` literal sprawl across five sites (Medium)

Spec Decision 9 (line 785 of `docs/spec-021-filters-0_0_8.md` plus the supporting passages at L1023-L1030) pins the class-derived input-type naming convention: every `FilterSet` subclass `Foo` produces a Strawberry input class named `FooInputType`. The literal `f"{<class>.__name__}InputType"` (with various local bindings for `<class>`) appears at five distinct call sites:

| # | Site | Variable | Surface |
|---|---|---|---|
| 1 | `django_strawberry_framework/filters/__init__.py:71` | `name` | Consumer-facing `filter_input_type()` annotation builder |
| 2 | `django_strawberry_framework/filters/factories.py:79` | `self.filter_input_type_name` | `FilterArgumentsFactory.__init__` — stored for `.arguments` property |
| 3 | `django_strawberry_framework/filters/factories.py:110` | `target_name` | `_ensure_built` — collision-check & cache-key for each BFS-visited filterset |
| 4 | `django_strawberry_framework/filters/factories.py:133` | `type_name` | `_build_class_type` — the actual `build_input_class` name argument |
| 5 | `django_strawberry_framework/filters/inputs.py:570` | `target_name` | `_build_input_fields` — the lazy `Annotated[...]` ref-string for a related filterset's input class |

All five derive the same canonical name. The shape was flagged by Slice 2's reviewer with exact recommended-fix language: "add a module-level `_input_type_name_for(fs_class)` helper in `inputs.py` (or as a static method on `FilterArgumentsFactory`) and route all five call sites through it. Worker 1 weighs at integration."

A sixth, structurally distinct literal exists at `inputs.py:585`:

```python
bag_name = f"{filterset_cls.__name__}{_pascal_case(python_attr)}FilterInputType"
```

This is the per-field "operator-bag" class name (one operator-bag class per scalar field per filterset) — it carries the field-name segment and is NOT the same canonical name pattern. **Out of scope for this fold;** the bag-class names already share the `_pascal_case` helper as their only common piece.

A seventh literal exists at `inputs.py:406` for the Range sub-input class:

```python
cls_name = f"{_pascal_case(field_name)}RangeInputType"
```

This is the Range-sub-input class-name-collision item Slice 2 explicitly deferred to a maintainer follow-up (spec L997-L998 "Range sub-input class-name collision"). **NOT in scope this pass** — folding it requires the spec-level decision on whether to scope by `(filterset_cls.__name__, field_name)` that Slice 2 ratified as deferred.

**Consolidation shape.**

1. Add `_input_type_name_for(filterset_class: type[FilterSet]) -> str` helper to `django_strawberry_framework/filters/inputs.py` near the other naming helpers (`_pascal_case` at line 154 / `_camel_case`). One-line body: `return f"{filterset_class.__name__}InputType"`. Docstring cites spec Decision 9 + L1023-L1030 as the source of truth for the naming convention.
2. Re-route the five call sites:
   - `__init__.py:71` — `name = _input_type_name_for(filterset_class)` (import `_input_type_name_for` from `.inputs` next to the existing `INPUTS_MODULE_PATH` import on line 32).
   - `factories.py:79` — `self.filter_input_type_name = _input_type_name_for(filterset_class)` (extend the existing line 21 import).
   - `factories.py:110` — `target_name = _input_type_name_for(fs_class)`.
   - `factories.py:133` — `type_name = _input_type_name_for(fs_class)`.
   - `inputs.py:570` — `target_name = _input_type_name_for(target_fs)` (in-module call; no import edit).
3. The helper is module-public-but-underscore-prefixed (single-underscore — addressable by sibling modules, not part of the consumer-facing surface).
4. Strawberry input-class registration via `materialize_input_class(name, cls)` at `inputs.py::materialize_input_class` already consumes `name` parameterized; no caller of `materialize_input_class` outside the five sites above hardcodes the format, so no additional call-site updates are needed.

**Risk surface.**

- Cycle risk: `__init__.py` already imports `INPUTS_MODULE_PATH` from `.inputs` (line 32); `factories.py` already imports `_build_input_fields` / `_build_logic_fields` / `build_input_class` from `.inputs` (line 21). Both extension imports stay in the existing import group; no cycle introduced.
- Test consequence: no test asserts the literal string text. Existing tests assert the *resulting* input class name via `input_cls.__name__ == "BookFilterInputType"` (e.g., `tests/filters/test_factories.py::test_filter_arguments_factory_builds_root_input_class`); the helper preserves that name verbatim.
- Public-surface check: zero new exports introduced; the helper is single-underscore private, not re-exported from `__init__.py::__all__`.

**Severity Medium** per BUILD.md "repeated literal / key / tuple that should be a named constant" — five concrete call sites, all derived from the same spec decision.

### Other items walked and explicitly NOT in scope

- **`_target_type_for_related_filter` + `_resolve_relation_target_type` shared tail** (`registry.primary_for(model) or registry.get(model)`). Slice 3 reviewer's "worth raising at integration if a third call site appears" condition not met — only two call sites; symbol clarity wins. **Defer to whichever future card adds a third call site.**
- **Raw `"and" / "or" / "not"` literals in the Slice-4a tree walker** at `sets.py:779/783/790`. The walker reads more cleanly with explicit branch-specific dispatch than it would routed through `dict(_LOGIC_KEYS).values()` indirection. **Decision: stay raw.** Documented above in the `What looks solid` walk.
- **`apply_sync` / `apply_async` shared body** + **`_derive_related_visibility_querysets_sync` / `_async` shared body**. Slice 1 reviewer's "structurally necessary (Python's sync/async colored-function boundary)" judgment confirmed at integration.
- **Range-sub-input class-name collision** (`inputs.py:406` `_pascal_case(field_name) + "RangeInputType"` pattern). Slice 2 ratified deferral to maintainer follow-up; spec L997-L998 carries the deferral note. **Not consolidation surface — out of scope this pass.**

## Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns no output (no top-level `__init__.py` edits across the entire build). Top-level `__all__` and re-export list unchanged from the pre-build state. The filter symbols are exported at `django_strawberry_framework.filters` per spec Decision 2, NOT at the package root. DoD item 25's "no new public exports at top-level" constraint is satisfied for the build.

The proposed `_input_type_name_for` helper is single-underscore private and is NOT added to `django_strawberry_framework/filters/__init__.py::__all__` — it stays addressable by sibling modules in the `filters/` subpackage but is not consumer-facing surface.

## Spec changes made (Worker 1 only)

No spec edits this pass. The two cross-slice DRY items are pure code-side consolidation that does not change any spec contract; the spec language (Decision 9's "class-derived name" convention; spec L1007 / H6-of-rev2's logical-keys vocabulary) is the source of truth that the consolidation honors rather than alters.

## Outcome and dispatch

`Status: planned`.

Two actionable Medium-severity DRY findings (M1 + M2) above require Worker-2 consolidation work and Worker-3 review. Worker 0 should dispatch:

1. **Worker 2 (consolidation pass)** — implement M1 (`_LOGIC_KEYS` fold to `inputs.py` only; `sets.py` imports it) AND M2 (add `_input_type_name_for(fs_class)` helper in `inputs.py`; re-route all five call sites). Single pass; no new tests required (existing tests cover both surfaces). Worker 2 sets `Status: built` on this artifact after the pass.
2. **Worker 3 (review pass)** — verify the two consolidations land cleanly, the existing test suite still passes (`uv run pytest tests/filters/ examples/fakeshop/test_query/test_library_api.py --no-cov`), no unrelated tool churn, no widened public surface. Worker 3 sets `Status: review-accepted` or `revision-needed`.
3. **Worker 1 (final-verification re-pass)** — re-walks the consolidation diff against this artifact's findings, ticks both folds as landed, sets `Status: final-accepted`.

After the consolidation loop closes, Worker 0 marks the integration checkbox `- [x]` in `build-021-filters-0_0_8.md` and dispatches Worker 1 for the final test-run gate (`bld-final.md`).

## Notes for the consolidation Worker 2 pass

- `sets.py` already imports from `.inputs` on line 35 today — extend that line rather than adding a new import statement.
- `__init__.py` already imports `INPUTS_MODULE_PATH` from `.inputs` on line 32 — add `_input_type_name_for` to the same import.
- `factories.py` already imports from `.inputs` on line 21 — add `_input_type_name_for` to the same import.
- After both folds, run `uv run ruff format .` then `uv run ruff check --fix .` per AGENTS.md; both should be no-ops aside from the edited lines.
- Run `uv run pytest tests/filters/ examples/fakeshop/test_query/test_library_api.py --no-cov` to confirm 154 passed (Slice-4a baseline) holds.
- No `CHANGELOG.md` edit needed — the consolidation is an internal refactor with no consumer-visible behavior change.

## Notes for the consolidation Worker 3 pass

- This is a pure-DRY consolidation pass; finding shape should focus on (a) whether both folds are mechanically clean and (b) whether any net-new duplication was introduced incidentally. No new tests are expected.
- Verify `git diff -- django_strawberry_framework/__init__.py` (the top-level one) remains empty.
- Verify `_input_type_name_for` is NOT added to `django_strawberry_framework/filters/__init__.py::__all__`.
- Re-run `scripts/review_inspect.py` against `sets.py` + `inputs.py` + `factories.py` + `__init__.py` after the consolidation — confirm the repeated-string-literals sections do not surface either `(("and_", "and"), ("or_", "or"), ("not_", "not"))` shape or the `InputType` literal at multiple sites in any single file.

---

## Build report (Worker 2)

### Findings addressed

- **M1 — `_LOGIC_KEYS` duplication.** Folded into `inputs.py` as the single source of truth; `sets.py` now imports it from `.inputs`. Deleted the 5-line constant body (and the 4-line preceding comment block) from `sets.py` at the position immediately above the `FilterSetMetaclass` definition. The `_LOGIC_KEYS` docstring in `inputs.py` was rewritten to reflect single-source ownership (no longer "mirror of the constant in sets.py").
- **M2 — `f"{<class>.__name__}InputType"` sprawl.** Added private `_input_type_name_for(filterset_class: type[FilterSet]) -> str` helper to `inputs.py` immediately after `_pascal_case`. All five derivation sites now call the helper: `__init__.py::filter_input_type` (1 call), `factories.py::FilterArgumentsFactory.__init__` (1 call), `factories.py::FilterArgumentsFactory._ensure_built` (1 call), `factories.py::FilterArgumentsFactory._build_class_type` (1 call), `inputs.py::_build_input_fields` (1 call for `target_fs`). The four other `*InputType`-containing literals in the package (`factories.py:76` docstring example; `inputs.py:_input_type_name_for` body — the helper itself; `inputs.py:423` Range sub-input; `inputs.py:602` operator-bag) stay as-is per the integration plan: docstring example is documentation of the format, Range + operator-bag are out-of-scope distinct shapes (the Range item is the Slice-2-deferred maintainer follow-up).

### Files touched

- `django_strawberry_framework/filters/sets.py` — M1 fold: deleted local `_LOGIC_KEYS` constant + preceding 4-line comment; extended existing `from .inputs import ...` line to pull `_LOGIC_KEYS` (ruff reordered the import so `_LOGIC_KEYS` sorts before `LOOKUP_NAME_MAP` per its underscore-first lexical order; use-site `dict(_LOGIC_KEYS)` unchanged).
- `django_strawberry_framework/filters/inputs.py` — M1 docstring polish on `_LOGIC_KEYS` (now describes single-source ownership and `sets.py` as the importer); M2 new private helper `_input_type_name_for` near `_pascal_case`; M2 routed `target_name = _input_type_name_for(target_fs)` inside `_build_input_fields`.
- `django_strawberry_framework/filters/factories.py` — M2 extended `from .inputs import ...` to include `_input_type_name_for`; routed three call sites (`__init__`, `_ensure_built`, `_build_class_type`).
- `django_strawberry_framework/filters/__init__.py` — M2 extended `from .inputs import INPUTS_MODULE_PATH` to also import `_input_type_name_for`; routed the `filter_input_type` call site.

### Tests added or updated

- None. Per Worker 1's plan ("no new tests required") and per AGENTS.md "Test placement" rules, the consolidation does not change observable behavior. Existing Slice 1 + 2 + 3 + 4 + 4a tests cover both the `_LOGIC_KEYS` consumption paths (`tests/filters/test_sets.py::test_normalize_input_maps_logic_keys_to_short_form` and the Slice-2 `_build_logic_fields` family) and the `*InputType` naming surface (`tests/filters/test_factories.py` collision tests; `tests/filters/test_inputs.py::test_filter_input_type_*`; `examples/fakeshop/test_query/test_library_api.py` live-HTTP coverage).

### Validation run

- `uv run ruff format .` — pass (148 files unchanged after both passes; idempotent).
- `uv run ruff check --fix .` — pass (1 auto-fix on first invocation reordering the new `_LOGIC_KEYS` import in `sets.py` to alphabetical order; second invocation reported `All checks passed!`).
- `git status --short` after both ruff invocations — every modified file classified: the four pass-specific source files (`filters/__init__.py`, `filters/factories.py`, `filters/inputs.py`, `filters/sets.py`) carry only the intentional consolidation edits; every other tracked-but-modified file (`CHANGELOG.md`, `GOAL.md`, `KANBAN.md`, `TODAY.md`, `filters/base.py`, `registry.py`, `types/base.py`, `types/definition.py`, `types/finalizer.py`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/spec-021-filters-0_0_8-terms.csv`, `docs/spec-021-filters-0_0_8.md`, `examples/fakeshop/apps/library/models.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/types/test_base.py`, `tests/types/test_definition_order.py`) is prior-slice work that landed across Slices 1-5 (not drift). The untracked entries (`docs/builder/bld-*.md`, `docs/builder/build-021-*.md`, `examples/fakeshop/apps/library/filters*.py`, `examples/fakeshop/apps/library/migrations/0004_patron_email.py`, `tests/filters/`, `tests/types/fixtures/`, `tests/types/test_definition_relations.py`) are likewise prior-slice deliverables. `docs/feedback.md` and `KANBAN.md` are maintainer in-progress (recorded in the build plan's preamble and the task contract). No tool churn requiring revert.
- `uv run pytest tests/filters/ --no-cov` — pass (128 passed in 0.53s).
- `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_scalars_api.py --no-cov` — pass (47 passed in 2.41s).

### Implementation notes

- **`_input_type_name_for` signature uses `type[FilterSet]`.** `FilterSet` is imported under `TYPE_CHECKING` in `inputs.py:45`, and `from __future__ import annotations` is active at the top of `inputs.py`, so the annotation is a string at runtime — no runtime import cycle introduced. Matches the same shape used elsewhere in the module (e.g. the `_field_specs` dict's `tuple[type[FilterSet], str]` key annotation at line 137).
- **`_LOGIC_KEYS` import ordering in `sets.py`.** Ruff's import sorter chose to place `_LOGIC_KEYS` before `LOOKUP_NAME_MAP` in the alphabetical sort (underscore-prefixed name sorts before letters under ruff's default isort config). This is a one-time auto-fix; subsequent ruff runs are idempotent. The bound name in the use site (`logic_lookup = dict(_LOGIC_KEYS)` inside `_normalize_input`) does not need editing — it reads the imported symbol.
- **Helper placement (near `_pascal_case`).** Worker 1's plan said "near the other naming helpers"; I placed `_input_type_name_for` immediately after `_pascal_case` (the only other naming helper in the module — `_camel_case` lives later inside the `_build_input_fields` body region). One-line body keeps the helper readable at the call sites.
- **`_LOGIC_KEYS` docstring rewrite in `inputs.py`.** The pre-pass docstring said "Logical-operator keys (mirror of the constant in `sets.py`)" — that text became actively misleading once the mirror was deleted. I rewrote the docstring to describe `inputs.py` as the source of truth and `sets.py` as the importer. Comment-only edit; no semantic change.
- **`factories.py:76` docstring example NOT routed.** The docstring `f"{filterset_class.__name__}InputType"` example documents the resulting format for consumers reading the API contract. It is a description of the convention, not a runtime literal that would drift; rewriting it to reference `_input_type_name_for` would make the docstring harder to scan ("the generated GraphQL type name is whatever `_input_type_name_for` returns" is less informative than the literal example). Worker 1's plan listed exactly five runtime call sites; this docstring was not among them.

### Notes for Worker 3

- M1 + M2 land in five files total (`sets.py`, `inputs.py`, `factories.py`, `__init__.py`, and the artifact itself). The diff per file is minimal — best read by looking at each `from .inputs import ...` line and the call-site swaps.
- Public-surface check: `git diff -- django_strawberry_framework/__init__.py` returns empty (top-level package `__init__` not edited); `git diff -- django_strawberry_framework/filters/__init__.py::__all__` is unchanged (the `_input_type_name_for` helper is single-underscore private and is NOT added to `__all__`). Worker 1's plan's public-surface constraint is satisfied.
- The Slice-4a tree walker's raw `"and" / "or" / "not"` literals at `sets.py::FilterSet._q_for_logic_tree` are intentionally NOT routed through `_LOGIC_KEYS` per Worker 1's plan's `What looks solid` walk — branch-specific dispatch reads more cleanly than indirection through the constant.
- No shadow files were re-run during this pass; per BUILD.md the integration consolidation does not introduce new files. Re-running `scripts/review_inspect.py` against `sets.py` / `inputs.py` / `factories.py` / `__init__.py` is suggested in the plan's "Notes for the consolidation Worker 3 pass" and is Worker 3's call.

### Notes for Worker 1 (spec reconciliation)

- No spec gap or conflict surfaced during the consolidation. The two folds honor the spec's pre-existing decisions (Decision 9 class-derived naming; spec L1007 / H6-of-rev2 logical-keys vocabulary) rather than altering them. Worker 1's integration plan's `Spec changes made (Worker 1 only)` section already records "No spec edits this pass"; that judgment holds.
- The `_LOGIC_KEYS` docstring in `inputs.py` now describes single-source ownership, but this is package-internal documentation — no spec edit is needed to reflect it.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

Worker 1's integration-pass plan named exactly two cross-slice DRY items (M1 + M2); Worker 2's consolidation diff folded both at the recommended shape. No incidental duplication introduced during the pass:

- **M1 (`_LOGIC_KEYS`) — landed cleanly.** Single grep across the package confirms exactly one definition site (`django_strawberry_framework/filters/inputs.py:112`), one importer (`django_strawberry_framework/filters/sets.py:35`), one use site (`django_strawberry_framework/filters/sets.py:427` in `_normalize_input`). The constant body and its docstring rewrite (now describing single-source ownership rather than "mirror of the constant in sets.py") match the consolidation contract.
- **M2 (`_input_type_name_for`) — landed cleanly.** Helper defined at `django_strawberry_framework/filters/inputs.py:163` with a one-line body `return f"{filterset_class.__name__}InputType"` and a docstring that cites the spec source-of-truth (Decision 9 + lines 1023-1030). All five named call sites route through the helper: `__init__.py:71`, `factories.py:79`, `factories.py:110`, `factories.py:133`, `inputs.py:587`. No sixth runtime literal of the canonical pattern remains. The two structurally-distinct literals at `inputs.py:423` (`<Field>RangeInputType` — Slice 2 deferral) and `inputs.py:602` (`<Class><Field>FilterInputType` operator-bag) were correctly left out of scope.
- **No reintroduced duplication.** The `factories.py:76` docstring example (`f"{filterset_class.__name__}InputType"`) stays as documentation of the resulting format — not a runtime literal. Worker 2's `### Implementation notes` justifies the choice; agreed (the documented example reads more clearly than "whatever `_input_type_name_for` returns").
- **No new cycle.** `inputs.py` carries `from __future__ import annotations` + a `TYPE_CHECKING`-gated `from .sets import FilterSet`; the new helper's `type[FilterSet]` parameter annotation is a string at runtime. The sibling-boundary direction documented in the Worker 1 plan (`base → inputs → sets → factories → __init__`) is preserved.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns empty — the top-level package init was untouched by this pass and stays untouched. `git diff -- django_strawberry_framework/filters/__init__.py` shows only the cumulative Slice-1-onward content; the `__all__` tuple in the current file enumerates 16 names (`ArrayFilter`, `ArrayFilterMethod`, `Filter`, `FilterSet`, `FilterSetMetaclass`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, `LazyRelatedClassMixin`, `ListFilter`, `ListFilterMethod`, `RangeField`, `RangeFilter`, `RelatedFilter`, `TypedFilter`, `filter_input_type`, `validate_range`) — same shape Slice 1 accepted, no new entries added by the consolidation. `_input_type_name_for` is correctly absent from `__all__`: single-underscore private, addressable by sibling modules in the `filters/` subpackage only. Spec Decision 9 + Worker 1's integration plan both pin "no new public exports introduced"; satisfied.

### CHANGELOG sanity

Not applicable; integration consolidation pass did not modify `CHANGELOG.md`. The `M CHANGELOG.md` line in `git status` is Slice 5's already-accepted cumulative diff (per Worker 2's `### Validation run` explicit classification), not a change introduced by this pass.

### Documentation / release sanity

Not applicable; integration consolidation pass did not modify docs / KANBAN / spec archival / release metadata. The doc-file modifications visible in `git status` (`GOAL.md`, `KANBAN.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/spec-021-filters-0_0_8.md`, `docs/spec-021-filters-0_0_8-terms.csv`) are all Slice 5's already-accepted cumulative diff. Worker 2's build report classifies each as prior-slice work; confirmed by spot-checking that none of the touched files appear in Worker 2's `### Files touched` list.

### What looks solid

- The helper placement (immediately after `_pascal_case` at `inputs.py:158`) is the right home: `_pascal_case` and `_input_type_name_for` are the two naming-convention helpers in the module, and reading them in sequence makes the per-FilterSet vs. per-field naming distinction visually obvious.
- The import-line extensions are surgical: `sets.py:35`, `__init__.py:32`, and `factories.py:21` each extend an existing `from .inputs import ...` line rather than introducing a new import statement — matches Worker 1's "extend the existing line" guidance in the plan's `### Notes for the consolidation Worker 2 pass`.
- The `_LOGIC_KEYS` docstring rewrite is the right scope: previously the constant body in `sets.py` was preceded by a comment block saying "mirror of the constant in `sets.py`" which became actively misleading once the mirror was deleted. Worker 2 rewrote the docstring in `inputs.py` to describe `inputs.py` as the source of truth and `sets.py` as the importer; correct.
- The Slice-4a tree walker's raw `"and" / "or" / "not"` literals at `sets.py::FilterSet._q_for_logic_tree` correctly stay raw — Worker 1's plan walked the trade-off explicitly (branch-specific dispatch reads more cleanly than indirection through `dict(_LOGIC_KEYS).values()`) and Worker 2 honored it.
- The `factories.py:76` docstring example (`f"{filterset_class.__name__}InputType"`) was deliberately not routed through the helper. Worker 2's `### Implementation notes` justifies this with the right reasoning: docstring examples document the resulting format for API consumers, not runtime literals; routing it would replace concrete clarity with a sibling-helper reference.

### Temp test verification

No temp tests created during this review. The consolidation is mechanically simple (delete a constant, add a one-line helper, route five call sites through it); existing test coverage at `tests/filters/` + `examples/fakeshop/test_query/test_library_api.py` + `examples/fakeshop/test_query/test_scalars_api.py` is sufficient to prove no observable behavior changed.

### Static-inspection helper

Skipped. Per BUILD.md "When to run the helper during build", the trigger thresholds for Worker 3 during a review pass are: a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+ lines of new logic in any file under `django_strawberry_framework/`. The integration consolidation pass:

- introduces no new `.py` file
- touches no file under `optimizer/` or `types/`
- adds approximately 12 lines of new logic across the four touched files (1-line helper body + ~10-line docstring in `inputs.py`; one-line edits at each of the 5 call sites + 4 import-line extensions); well below the 30-line threshold
- DELETES 5 lines (the `_LOGIC_KEYS` body in `sets.py`) plus its 4-line preceding comment

Net new logic across the pass is on the order of single digits; helper run not required.

### Notes for Worker 1 (spec reconciliation)

No spec gap or conflict surfaced during review. The two folds honor pre-existing spec contracts (Decision 9 class-derived naming; spec L1007 / H6-of-rev2 logical-keys vocabulary) rather than altering them. Worker 1's integration plan's `## Spec changes made (Worker 1 only)` section already records "No spec edits this pass"; that judgment holds. The `_LOGIC_KEYS` docstring rewrite in `inputs.py` is package-internal documentation and does not require a spec edit.

For Worker 1 final-verification: the two prior-recorded deferrals remain deferred and out of scope for this pass:

- `_target_type_for_related_filter` + `_resolve_relation_target_type` shared tail (Slice 3) — third-call-site condition still not met.
- Range-sub-input class-name collision at `inputs.py:423` (`f"{_pascal_case(field_name)}RangeInputType"`) — Slice 2 ratified deferral to maintainer follow-up; spec L997-L998 carries the deferral note.

### Validation reproduced

- `uv run pytest tests/filters/ --no-cov` — `128 passed in 0.71s` (matches Worker 2's `128 passed in 0.53s` baseline; timing variance, no test-count change).
- `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_scalars_api.py --no-cov` — `47 passed in 3.17s` (matches Worker 2's `47 passed in 2.41s` baseline; same).

### Review outcome

`review-accepted`. Both M1 and M2 land mechanically clean, no new findings, no incidental duplication, public surface unchanged, tests pass. Worker 0 should dispatch Worker 1 for final-verification on the integration pass.

---

## Final verification (Worker 1)

- **Spec status-line re-verification.** Re-read `docs/spec-021-filters-0_0_8.md:1-7`. The L4 status line already describes the shipped reality (core wiring / live HTTP / tree-form logic / docs all shipped through their respective slices; Slice 6 closed as carried-by-sibling). No edit needed in this pass — the integration consolidation is mechanical and does not change any shipped surface.
- **M1 confirmation — `_LOGIC_KEYS`.** `grep -rn "_LOGIC_KEYS" django_strawberry_framework/ tests/ examples/` returns exactly three hits across the package: definition at `django_strawberry_framework/filters/inputs.py:112`, import at `django_strawberry_framework/filters/sets.py:35` (`from .inputs import _LOGIC_KEYS, LOOKUP_NAME_MAP, _field_specs, normalize_input_value`), use site at `django_strawberry_framework/filters/sets.py:427` (`logic_lookup = dict(_LOGIC_KEYS)`). Zero hits in `tests/` or `examples/`. The pre-pass byte-for-byte duplication between `sets.py:53-57` and `inputs.py:108-112` is gone; single source of truth in `inputs.py`. The fold matches the consolidation shape in the integration plan exactly.
- **M2 confirmation — `_input_type_name_for`.** `grep -rn "_input_type_name_for\|InputType\"" django_strawberry_framework/` confirms: helper defined at `django_strawberry_framework/filters/inputs.py:163` with body `return f"{filterset_class.__name__}InputType"` at line 173; all five named runtime call sites route through the helper — `__init__.py:71`, `factories.py:79`, `factories.py:110`, `factories.py:133`, `inputs.py:587`. The two structurally distinct literals at `inputs.py:423` (`<Field>RangeInputType` — Slice 2 deferral to maintainer follow-up) and `inputs.py:602` (`<Class><Field>FilterInputType` operator-bag — distinct shape with per-field segment) correctly stay raw. The `factories.py:76` docstring example (`f"{filterset_class.__name__}InputType"`) stays as documentation of the resulting format, not a runtime literal — agrees with Worker 2's `### Implementation notes` justification and Worker 3's `### What looks solid` walk.
- **No new duplication introduced.** Walked the four touched files (`filters/__init__.py`, `filters/sets.py`, `filters/inputs.py`, `filters/factories.py`) for any incidental near-copies introduced by the fold. None observed: the helper has a single one-line body, the import lines are surgical extensions of existing imports, and the call sites swap a literal for a function call without restructuring surrounding code.
- **Public-surface check.** `git diff -- django_strawberry_framework/__init__.py` returns empty — top-level package init untouched by this pass. The `_input_type_name_for` helper is single-underscore private and is NOT added to `django_strawberry_framework/filters/__init__.py::__all__` (verified: the `__all__` tuple at `filters/__init__.py:83-100` enumerates 16 names, the same 16 Slice 1 accepted; no new export).
- **Sibling-boundary direction preserved.** The fold-into-`inputs.py` direction confirms `base → inputs → sets → factories → __init__` one-way dependency. `inputs.py` carries `from __future__ import annotations` + a `TYPE_CHECKING`-gated `from .sets import FilterSet`, so the helper's `type[FilterSet]` parameter annotation is a string at runtime — no new runtime cycle introduced. Matches the documented architecture from the Worker 1 integration plan's "Cross-slice import / sibling-boundary direction check" section.
- **Existing tests still pass.** Ran `uv run pytest tests/filters/ tests/types/ examples/fakeshop/test_query/ --no-cov` (per task contract; broader scope than the consolidation-only `tests/filters/` slice but still focused — final test-run gate next will sweep the full suite). Result: `421 passed, 3 skipped, 48 warnings in 6.49s`. No regressions; the 3 skips are pre-existing (Slice-4a deferred-work catalog item plus the two unrelated test-suite skips that predate this build). NO coverage flag was used.
- **Carried-forward deferrals.** Confirmed the two prior-recorded deferrals (Slice-3 `_target_type_for_related_filter` + `_resolve_relation_target_type` shared tail; Slice-2 Range-sub-input class-name collision at `inputs.py:423`) remain explicitly out-of-scope for this pass — neither triggering condition was met (no third call site; no spec edit on the collision question). Both remain in the final-test-run-gate deferred-work catalog Worker 1 will surface in `bld-final.md`.

### Summary

The cross-slice integration pass closes the build's two named cross-module DRY items end-to-end: `_LOGIC_KEYS` folds into `inputs.py` as the single source of truth (deleting the duplicate from `sets.py`), and `_input_type_name_for` becomes the single naming-helper that all five `f"{<class>.__name__}InputType"` call sites route through. The consolidation is mechanical, public-surface-neutral, sibling-boundary-preserving, and behavior-preserving — every existing test in the focused scope passes unchanged. No new spec edits this pass; the folds honor pre-existing spec decisions (Decision 9 class-derived naming; spec L1007 / H6-of-rev2 logical-keys vocabulary) rather than altering them.

### Spec changes made (Worker 1 only)

None this pass. The two folds are pure code-side consolidations that honor pre-existing spec contracts; the spec language is the source of truth that the consolidation respects rather than alters. The L4 status line already describes the shipped reality and needs no edit.

`Status: final-accepted`. Worker 0 may now mark the integration checkbox `- [x]` in `build-021-filters-0_0_8.md` and dispatch Worker 1 for the final test-run gate (`bld-final.md`).

