# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## DRY analysis

- **None — the two helpers are independent direction-specific converters with no shared logic, and the only historically-flagged cross-file DRY (a local `_camel_case` body) no longer exists.** The prior-cycle (0.0.7) artifact deferred folding a "byte-for-byte duplicated `_camel_case`" from `filters/inputs.py` and `orders/inputs.py` into a new `utils/strings.py::camel_case`. That opportunity is now **MOOT**: live source has `_camel_case = graphql_camel_name` at `filters/inputs.py #"_camel_case = graphql_camel_name"` and `orders/inputs.py #"_camel_case = graphql_camel_name"` — both are alias re-exports of a single shared strawberry helper (`graphql_camel_name`), not local re-derivations. The 0.0.9 DRY pass already single-sited the camelCase direction through that strawberry helper, so there is no local body to consolidate and `utils/strings.py` is no longer the correct home for a camel converter. The sibling `filters/inputs.py::_pascal_case` is likewise NOT a copy of `pascal_case`: it adds `.replace("__", "_")` normalization and a `ConfigurationError` raise-on-empty guard (`filters/inputs.py::_pascal_case`), an intentionally distinct raise-on-empty variant of this module's silent-empty `pascal_case` — see DRY recap. No act-now or defer-with-trigger candidate remains.

## High:

None.

## Medium:

None.

## Low:

### L1 — `snake_case("id") == "id"` field-map passthrough is load-bearing for the optimizer but not surfaced in the helper docstring

`snake_case` (`utils/strings.py::snake_case`) returns single-segment lowercase input unchanged, so `"id"` round-trips to `"id"`. The optimizer relies on this exact behaviour and carries a load-bearing workaround for it at `optimizer/walker.py::_plan_select_field #"snake_case(\"id\") == \"id\""` (Decision 7: when a Relay `DjangoType` uses a custom pk attname like `uuid`, `snake_case("id")` does not match the field-map key, so the walker resolves the configured `id_attr` instead of triggering an N+1 lazy load). The helper docstring (`utils/strings.py::snake_case`) documents the acronym caveat (`"HTMLParser"` → `"h_t_m_l_parser"`) but never mentions the `"id"` passthrough that motivates the walker special-case. Behaviour is bit-correct and the contract is pinned by `tests/optimizer/test_walker.py #"snake_case(\"id\")"` plus `tests/utils/test_strings.py::test_snake_case_round_trips_camel_case`. Citation hygiene only — defer until the helper grows a second optimizer-side consumer that depends on the `"id"` passthrough; then append a one-line note to the caveat paragraph cross-referencing `walker.py`. Behaviour preserved.

### L2 — `pascal_case` silent-empty contract (`""`/`"_"`/`"__"` -> `""`) is test-pinned but not stated in the docstring

`pascal_case` (`utils/strings.py::pascal_case`) returns `""` when `name.split("_")` yields only empty segments. `tests/utils/test_strings.py::test_pascal_case_empty_output_edges` pins this explicitly with an inline comment naming the failure mode it guards ("prevents a future filter 'fix' from silently changing generated enum names"). The docstring documents the underscore-collapse and acronym caveats but not the silent-empty fall-through. The sibling `filters/inputs.py::_pascal_case` deliberately diverges here — it *raises* `ConfigurationError` on the same empty-output edge — so the silent-vs-raise split is intentional per-call-site design, not an inconsistency to reconcile in this helper. Citation hygiene only — defer until a third caller of `pascal_case` lands; then append an "empty / all-underscore input returns the empty string by design; callers needing a config error raise at their own call site" note cross-referencing `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` and `filters/inputs.py::_pascal_case`. Behaviour preserved.

### L3 — Submodule has no `__all__`; mirrors the sibling `utils/` forward-looking gap

`utils/strings.py` exposes `snake_case` and `pascal_case` to the wildcard surface without a module-level `__all__`. The package-level `utils/__init__.py` curates both into its own `__all__` and names them in the module docstring (`utils/__init__.py #"case conversion"`), so the public surface is fully controlled one level up. This is the same forward-looking gap the sibling submodules carry. Citation hygiene only — defer until any `utils/` submodule adopts a module-level `__all__` (forcing parity across the folder) or a third public symbol lands here. Behaviour preserved.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical home for GraphQL/Django-boundary case conversion; every consumer imports from here rather than re-deriving. `snake_case` consumers: `optimizer/walker.py` (`:286`, `:728`, `:924`), `types/base.py` (`:488`, `:1388`, `:1572`), `types/finalizer.py` (`:417`, `:597`), `management/commands/inspect_django_type.py:192`. `pascal_case` consumers: `types/converters.py:357` (enum naming), `sets_mixins.py:91` (input-class name segments). The `from ..utils.strings import {snake_case|pascal_case}` import pattern is uniform; no consumer re-implements either converter.
- **New helpers considered.** Considered extracting the `name.split("_")` non-empty-segment filter (used in `pascal_case`) into a shared helper for reuse with a hypothetical `camel_case`; rejected — the one-liner reads more clearly inline and the camel direction now routes through strawberry's `graphql_camel_name` (aliased as `_camel_case` in `filters/inputs.py` and `orders/inputs.py`), so no second consumer of the segment-filter exists. Considered folding both helpers through a single `convert_case(name, *, to=...)` dispatch; rejected — they run in opposite directions (GraphQL→Django vs Django→GraphQL) and explicit per-direction names read better at call sites.
- **Duplication risk in the current file.** None. The two helpers share no logic beyond the trivial `name.split("_")` iteration in `pascal_case`. `snake_case`'s per-character boundary loop is a single straight-line pass; any factoring would obscure the boundary detection. The sibling `filters/inputs.py::_pascal_case` is NOT a duplicate of `pascal_case` — it adds `.replace("__", "_")` normalization and a raise-on-empty `ConfigurationError` guard, an intentionally distinct strict variant of this module's silent-empty converter.

### Other positives

- **Stale-artifact supersede confirmed.** The on-disk 0.0.7 artifact (`Status: verified`, drifted line cites such as `walker.py:178`/`base.py:237`/`converters.py:326`) was superseded wholesale. Its headline defer-with-trigger DRY (fold a duplicated local `_camel_case` body into a new `utils/strings.py::camel_case`) is now resolved-and-moot: live `_camel_case` is an alias of strawberry's `graphql_camel_name` in both inputs files, not a local body — re-raising it would be the resolved-DRY trap. Its L4 (docstring "third style ever shows up" framing) is consequently no longer contradicted and was dropped, not re-raised.
- **Logic verified correct, all branches.** `snake_case`: leading-uppercase guarded by `i > 0` (`"Name"` → `"name"`, no spurious leading `_`); interior uppercase triggers a boundary (`"isPrivate"` → `"is_private"`); single-segment lowercase passes through (`"id"` → `"id"`). `pascal_case`: `if part` drops empty segments so adjacent/leading/trailing underscores collapse (`"_leading"`/`"trailing_"`/`"double__underscore"`); all-empty input yields `""`; `str.capitalize()` lowercases interior chars (documented acronym caveat, unreachable from Django field names). The two are not exact round-trip inverses (camel↔snake vs snake↔pascal are different boundaries) — correct, since there is no `camel_case` here and the camel direction lives in strawberry's helper.
- **Coverage discipline.** `tests/utils/test_strings.py` pins three `snake_case` shapes (`test_snake_case_round_trips_camel_case`), the six docstring-enumerated `pascal_case` shapes (`test_pascal_case_handles_snake_case_inputs`), and the silent-empty contract for `""`/`"_"` (`test_pascal_case_empty_output_edges`) with an inline comment naming the failure mode the pin protects. Every public symbol and every branch is exercised.
- **GLOSSARY drift quick-check.** Grep of `docs/GLOSSARY.md` for `snake_case` / `pascal_case` / `camelCase` returns no case-conversion-helper entries (only `auto_camel_case` as an unrelated `StrawberryConfig` kwarg at `GLOSSARY.md:1239`/`:1244`). `snake_case`/`pascal_case` are internal mechanics consumed by the optimizer field-map lookup, the choice-to-enum converter, the relation binder, and the input-class namer; their symbol names are not part of the published consumer contract, so GLOSSARY absence is correct convention — no drift, no forward.
- **No import surface.** Zero module-level imports (confirmed by the shadow overview). Pure-Python string manipulation with no Django/Strawberry/first-party dependency — correct for a leaf `utils/` submodule consumed across `optimizer/`, `types/`, `filters/`, and `sets_mixins.py`; zero circular-import risk.
- **Docstring discipline.** The module docstring distinguishes both directions and names the upstream Strawberry behaviour each helper interacts with; both per-helper docstrings document the acronym caveat for inputs unreachable through the framework's own call chain, framed "documented here so a future direct caller is not surprised" — appropriate since both are public symbols re-exported from `utils/__init__.py`.

### Summary

`utils/strings.py` is a focused 70-line leaf module hosting two direction-specific case converters: `snake_case` (reverses Strawberry's camelCase GraphQL names to Django snake_case for field-map lookup) and `pascal_case` (builds GraphQL type/enum name segments from Django snake_case). Logic is bit-correct across every branch, fully test-pinned, and the module is the uniform canonical home for both — no consumer re-derives. The 0.0.7 on-disk artifact was superseded wholesale; its headline `_camel_case` DRY is now moot (the camel direction was single-sited through strawberry's `graphql_camel_name` alias in the 0.0.9 pass, leaving no local body to fold), and the sibling `filters/inputs.py::_pascal_case` is an intentionally distinct raise-on-empty variant, not a duplicate. Zero High, zero Medium, three citation-hygiene Lows (L1 `"id"` passthrough docstring silence, L2 silent-empty docstring silence, L3 no module `__all__`) all forward-looking-without-edit, no GLOSSARY edit, no source edit. Shape #5 (no-source-edit cycle) qualifies.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, no changes (1 file would be left unchanged / project-wide unchanged).
- `uv run ruff check --fix .` — pass, no changes (All checks passed).

### Notes for Worker 3
- L1, L2, L3 are all forward-looking citation-hygiene Lows with explicit triggers; no edit in scope this cycle.
- No GLOSSARY-only fix in scope: `snake_case`/`pascal_case` have no GLOSSARY entries (internal mechanics; correct convention).
- Stale 0.0.7 artifact superseded wholesale; its `_camel_case` DRY bullet is resolved-and-moot (live `_camel_case` is a `graphql_camel_name` alias, not a local body) and was NOT re-raised.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — the L1/L2/L3 docstring notes are forward-looking with unmet triggers; no rot in the current docstrings.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (AGENTS.md: do not update CHANGELOG.md unless explicitly instructed; the active plan `docs/review/review-0_0_9.md` records no changelog directive for this item).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle, terminal-verify. Logic independently re-verified LIVE (`uv run python` probe at `docs/review/temp-tests/utils_strings/probe.py`, plus the 3 existing pins in `tests/utils/test_strings.py` — 3 passed):
- `snake_case`: `"id"`→`"id"` (L1 load-bearing passthrough, walker special-case anchored at `optimizer/walker.py #"snake_case(\"id\") == \"id\""` and pinned in `tests/optimizer/test_walker.py:182`), `"Name"`→`"name"` (leading-upper `i>0` guard, no spurious leading `_`), `"isPrivate"`→`"is_private"`, `"HTMLParser"`→`"h_t_m_l_parser"` (acronym caveat), `"user2Name"`→`"user2_name"` / `"user2name"`→`"user2name"` (digit-then-upper boundary), `"_leading"`→`"_leading"` (leading underscore preserved), `"already_snake"` passthrough, `""`→`""`.
- `pascal_case`: silent-empty `""`/`"_"`/`"__"`→`""` (L2 contract, pinned by `test_pascal_case_empty_output_edges`), `"payment_method"`→`"PaymentMethod"`, `"_leading"`→`"Leading"`, `"trailing_"`→`"Trailing"`, `"double__underscore"`→`"DoubleUnderscore"`, `"my_HTTP_response"`→`"MyHttpResponse"` (per-segment `capitalize()` lowercases interior). Confirmed digit-head `"2legacy"`→`"2legacy"` is `str.capitalize` semantics (leading non-cased char), not a defect.
- 3 Lows (L1 `"id"` docstring silence, L2 silent-empty docstring silence, L3 no module `__all__`) all carry verbatim trigger phrasing and are forward-looking-without-edit; triggers genuinely unmet (no second optimizer consumer of the `"id"` passthrough; no third `pascal_case` caller; no sibling `utils/` submodule adopts `__all__`). No GLOSSARY-only fix present.

### DRY findings disposition
Confirmed the stale 0.0.7 "fold duplicated local `_camel_case` body into `utils/strings.py::camel_case`" DRY is MOOT and correctly NOT re-raised: live source has `_camel_case = graphql_camel_name` at `filters/inputs.py:58` and `orders/inputs.py:51` — alias re-exports of a single shared `graphql_camel_name` helper (defined at `utils/inputs.py:53`), not local bodies. Re-raising would be the resolved-DRY trap. Sibling `filters/inputs.py::_pascal_case` (def at `:161`) is an intentionally distinct raise-on-empty variant (`ConfigurationError` at `:180` + `.replace("__","_")`), not a duplicate of `pascal_case`. (Note: artifact prose calls `graphql_camel_name` "strawberry's"; it is actually package-local in `utils/inputs.py` — harmless imprecision, does not affect the moot-DRY conclusion.) All 7 cited consumers import uniformly via `utils.strings` (greps confirm: `sets_mixins.py`, `types/converters.py`, `types/base.py`, `types/finalizer.py`, `optimizer/walker.py`, `management/commands/inspect_django_type.py`, `utils/__init__.py`). No consumer re-derives either converter.

### Temp test verification
- Temp test used: `docs/review/temp-tests/utils_strings/probe.py` (21 assertions, all passed under `uv run python`).
- Disposition: deleted at cycle closeout (gitignored); behaviour fully covered by the 3 permanent pins in `tests/utils/test_strings.py`. No new edge case warranting promotion — every probe assertion is either already pinned or is documented unreachable-caveat behaviour.

### Shape #5 checks
1. `git diff --stat 0872a20fcbecf870b3669742f108364202709e26 -- django_strawberry_framework/utils/strings.py` EMPTY (byte-unchanged); `CHANGELOG.md` diff EMPTY. GLOSSARY.md is dirty but `grep snake_case|pascal_case docs/GLOSSARY.md` returns NONE — the hunk does not touch this cycle's symbols and attributes to sibling cycles. "Files touched: None" holds.
2. Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
3. Every Low has verbatim trigger phrasing; no GLOSSARY-only fix — confirmed.
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence — confirmed; diff empty; cycle is internal-only (zero source change) so framing is correct.
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (All checks passed) on `strings.py` — pass. COM812 notice is standing/expected.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
