# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: `_camel_case(name)` helper duplicated byte-for-byte at `django_strawberry_framework/filters/inputs.py:783-789` and `django_strawberry_framework/orders/inputs.py:164-170`.** Both bodies read `parts = [part for part in name.split("_") if part]; if not parts: return name; head, *rest = parts; return head + "".join(part.capitalize() for part in rest)` — the only delta is the docstring example (`galaxy_name` vs `shelf_code`). `utils/strings.py` is the canonical home for case-conversion helpers (it already hosts `snake_case` and `pascal_case` per the module docstring at `utils/strings.py:1-16`'s "Kept minimal on purpose. If a third style (kebab-case, SCREAMING_SNAKE) ever shows up we'll add it here rather than re-deriving inline at the call site" prose), and a third style HAS now shown up at two sibling sites. Defer until the 0.0.8 cycle (`orders/` is concurrent spec-028 maintainer work landing post-baseline `02ed085` and is NOT in the 0.0.7 review plan); when the 0.0.8 review opens, fold both `_camel_case` helpers through a new `utils/strings.py::camel_case(name)` and update `utils/__init__.py::__all__` to re-export it. The trigger is satisfied today (two sites exist); the deferral is for cycle-boundary hygiene, not factoring uncertainty. Per the "Cross-folder DRY landings — second-closing folder rule" memory calibration, the cycle that closes `orders/` second owns the extraction.

## High:

None.

## Medium:

None.

## Low:

### L1 — `snake_case("id") == "id"` field-map quirk is load-bearing for the optimizer but undocumented in the helper's docstring

`snake_case`'s body at `utils/strings.py:38-43` returns `"id"` unchanged for the single-segment lowercase input `"id"`, which is consumed by `optimizer/walker.py:178` (`django_name = snake_case(sel.name)`) where the next ten lines (`walker.py:184-185`) carry the comment `# snake_case("id") does not match the field-map …` — i.e. the walker has a load-bearing workaround for what the helper produces on this specific input. The helper's docstring at `utils/strings.py:20-37` documents the acronym caveat (`"HTMLParser"` → `"h_t_m_l_parser"`) but never mentions that `"id"` round-trips unchanged, which is the input that motivates `walker.py:184-185`'s special-case. Today the test at `tests/optimizer/test_walker.py:179` carries the inline comment naming the contract — and the helper's body is bit-correct — so the helper's docstring silence is citation-hygiene-only. Defer until the helper grows a second optimizer-side consumer where the `"id"`-passthrough behaviour matters; at that point, append a one-line `"\"id\" round-trips unchanged (single-segment lowercase input); the optimizer relies on this at \`walker.py::_walk_selections\`."` note to the docstring's caveats paragraph. Citation hygiene only — behaviour preserved.

### L2 — `pascal_case` empty-string return is pinned by a test but undocumented as the silent-empty contract in the helper's docstring

`pascal_case`'s body at `utils/strings.py:70` returns `""` when `name.split("_")` produces only empty segments (inputs `""`, `"_"`, `"__"`, etc.), and `tests/utils/test_strings.py:22-28` pins this contract explicitly (`test_pascal_case_empty_output_edges`: `pascal_case("") == ""`, `pascal_case("_") == ""`) with an inline comment naming the failure mode the pin protects against ("a future filter 'fix' from silently changing generated enum names"). The helper's docstring at `utils/strings.py:47-69` documents the underscore-collapse behaviour ("Adjacent / leading / trailing underscores collapse to nothing") and the acronym caveat, but never mentions the silent-empty fall-through. The sibling `filters/inputs.py::_pascal_case:162-185` raises `ConfigurationError` for the same empty-output edge per `rev-filters__inputs.md` Medium #1's "the guard's docstring explicitly says it's there to prevent 'a generic ``FilterInputType``' " precedent — but `utils/strings.py::pascal_case` is the canonical helper that `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` consumes (the canonical-fix path landed in the cycle that produced `rev-filters__inputs.md`), and the canonical helper is silent-empty by design. Defer until a third caller of `utils/strings.py::pascal_case` lands; at that point, append `"Empty input or all-underscore input (\`\"\"\`, \`\"_\"\`, \`\"__\"\`) returns the empty string by design; callers that need a configuration error on empty output raise their own at the call site (see `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` and `filters/inputs.py::_pascal_case`)."` to the docstring's caveats paragraph. Citation hygiene only — behaviour preserved.

### L3 — Submodule has no `__all__`; mirrors the sibling `utils/relations.py` forward-looking gap

`utils/strings.py` exposes `snake_case` and `pascal_case` to the wildcard surface (no `__all__` gate). `utils/__init__.py:21, 24-32` re-exports both via the package-level `__all__` curation; the module-level docstring at `utils/__init__.py:7-9` names them as the public surface. `rev-utils__relations.md::L3` (verified) records the same forward-looking gap for the sibling submodule with the trigger "sibling utils submodules grow an `__all__` or when a fourth public symbol lands here." Per the memory calibration "when reviewing `utils/strings.py` and `utils/typing.py` next, check whether `__all__` is present at the submodule level — if neither has one, L3 here is correctly forward-looking with the trigger 'sibling utils submodules grow an `__all__`.'": neither has one today, so this Low confirms `rev-utils__relations.md::L3`'s defer-with-trigger phrasing as the canonical handling for the whole `utils/` folder. Defer until any sibling utils submodule adopts `__all__` (which forces parity across all three), or when a third public symbol lands in `utils/strings.py`. Citation hygiene only — behaviour preserved.

### L4 — Module docstring's "If a third style (kebab-case, SCREAMING_SNAKE) ever shows up we'll add it here" framing is mildly contradicted by the existing `_camel_case` duplication elsewhere

`utils/strings.py:13-15`'s closing paragraph reads "Kept minimal on purpose. If a third style (kebab-case, SCREAMING_SNAKE) ever shows up we'll add it here rather than re-deriving inline at the call site." The framing is correct in spirit — the module IS the canonical home — but a `_camel_case` helper has already shown up in two sibling files (`filters/inputs.py:783-789` and `orders/inputs.py:164-170`, the latter post-baseline concurrent maintainer work per spec-028 Slice 3) without landing here, which makes the "third style ever shows up" framing read as forward-looking when it's actually already-arrived. Once the deferred DRY extraction in `## DRY analysis` lands (folding `_camel_case` through `utils/strings.py::camel_case`), this docstring will become bit-correct again. Defer until the DRY extraction lands; at that point, update the docstring to drop "kebab-case, SCREAMING_SNAKE" or replace the parenthetical with the actual third style (`camelCase`). Citation hygiene only — behaviour preserved; the docstring claim is aspirational not normative.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical home for case-conversion at the GraphQL/Django boundary; every documented consumer imports from here rather than re-deriving inline — `optimizer/walker.py:15` (3 call sites at `:178`, `:585`, `:726`), `types/base.py:42` (2 call sites at `:237`, `:917`), `types/finalizer.py:56` (1 call site at `:209`), `types/converters.py:52` (1 call site at `:326`), `sets_mixins.py:34` (1 call site at `:76`, the canonical-fix path landed in `rev-filters__inputs.md` Medium #1's Option A). The `from .utils.strings import {snake_case|pascal_case}` import pattern is uniform; no consumer re-derives the case-conversion logic at the call site.
- **New helpers considered.** Considered pulling the `for part in name.split("_") if part` filter shape (used at `pascal_case:70`) into a `_non_empty_segments(name: str) -> list[str]` helper for reuse with a potential `camel_case`; rejected — even if `camel_case` lands per the DRY analysis bullet, the segment-filter shape is a one-liner that reads more clearly inline at each site, and the helper indirection would obscure the segment-collapse semantics each case-converter encodes. Considered folding `snake_case` and `pascal_case` through a single dispatch `convert_case(name, *, to: Literal["snake", "pascal", "camel"])`; rejected — the two helpers operate in opposite directions (GraphQL→Django vs Django→GraphQL) and consumers want the direction explicit at the call site for readability. Both rejections are recorded with reasoning; neither survives as defer-with-trigger.
- **Duplication risk in the current file.** None. The two helpers are independent direction-specific converters with no shared logic beyond the trivial `name.split("_")` iteration in `pascal_case`. The four `out.append(...)` / `c.lower()` / `c.isupper()` lines in `snake_case` are a single straight-line loop; collapsing through any factoring would obscure the per-character boundary detection.

### Other positives

- **Coverage discipline.** `tests/utils/test_strings.py:6-9` pins three `snake_case` shapes (`name`, `isPrivate`, `createdDate`); `:12-19` pins the six `pascal_case` shapes the docstring's Examples block enumerates (`status`, `is_active`, `payment_method`, `_leading`, `trailing_`, `double__underscore`); `:22-28` pins the silent-empty contract for `""` and `"_"` with the inline comment naming the failure mode the pin protects against ("Pin the silent-empty contract: every segment filtered out by `if part` collapses to `\"\"`. Unreachable through the documented call chain (Django field names are never empty and never `\"_\"`); pinning prevents a future filter 'fix' from silently changing generated enum names."). Every public surface symbol is pinned; every branch in both helpers is covered.
- **Static helper not run as mandatory.** The module is 70 lines (below the 150-line `REVIEW.md` "Static review helper" threshold) and not under `optimizer/` or `types/`, so the helper invocation is optional. I ran it for shadow-overview parity with the folder pass (`docs/shadow/django_strawberry_framework__utils__strings.overview.md`); the overview confirms 0 imports, 2 symbols, 0 control-flow hotspots, 0 reflective access calls of interest, 0 TODO comments, 0 repeated string literals. No control-flow attention warranted at this size.
- **GLOSSARY drift quick-check.** Grep on `docs/GLOSSARY.md` returns zero matches for backticked `snake_case`, `camelCase`, or `pascal_case` as case-conversion helper names. Per the memory calibration "Internal-mechanics GLOSSARY absence is correct convention": `snake_case` / `pascal_case` are internal mechanics consumed by the optimizer's field-map lookup (`walker.py:178, 585, 726`), the type-converter's enum naming (`converters.py:326`), the relation-binder's field resolution (`finalizer.py:209`), the field-map builder (`base.py:237, 917`), and the FilterSet input-class naming pipeline (`sets_mixins.py:76`). Consumer contract surfaces through documented umbrella entries (`auto_camel_case` as a `StrawberryConfig` kwarg at `GLOSSARY.md:1085, 1090`; type-name conventions per `FilterSet.type_name_for` documented at `GLOSSARY.md:432` indirectly). The helper symbol names themselves are not part of the published consumer contract, so absence is correct convention — not a forward.
- **Module docstring discipline.** `utils/strings.py:1-16` distinguishes the two directions explicitly ("Both directions are needed at the GraphQL/Django boundary"), names the upstream Strawberry behaviour each helper interacts with (the camelCase default name converter; choice-to-enum naming), and closes with the canonical-home framing ("Kept minimal on purpose. If a third style … ever shows up we'll add it here"). The L4 mild-contradiction note above is bookkeeping, not a docstring quality concern; the framing as authored was load-bearing forward guidance.
- **Per-helper docstring discipline.** Both `snake_case:20-37` and `pascal_case:47-69` document the acronym caveat for inputs unreachable through the documented call chain ("`HTMLParser`" → "`h_t_m_l_parser`"; "`my_HTTP_response`" → "`MyHttpResponse`") with the "documented here so a future direct caller is not surprised" framing. This is exactly the contract-and-edge-case style established by the sibling `rev-utils__relations.md` calibration "Test-double surfaces are documented" — even though the unreachable-input case is unreachable from the framework's own call chain, the helper IS a public symbol (`utils/__init__.py:27`) and a consumer who imports it directly would otherwise be surprised. Both docstrings have the same edge-case-aware shape.
- **`from __future__ import annotations` not needed.** Both helpers use only `str` parameter / return annotations and the type checker resolves them as built-in `str` regardless. Per the memory calibration "`get_type_hints` / `from __future__ import annotations` discipline": modules with no internal-type forward references and no `TYPE_CHECKING`-guarded imports do not need the future-annotations directive. `utils/relations.py` and `utils/typing.py` do need it (Protocol bases, `Literal` aliases); `utils/strings.py` does not.
- **No import surface.** Zero imports at the module level (the static helper overview's "Imports: None"). The two helpers are pure-Python string manipulation; no Django, Strawberry, or first-party dependency. This is the right factoring for a `utils/` submodule consumed across `optimizer/`, `types/`, `filters/`, and `sets_mixins.py` — zero risk of circular-import drift.

### Summary

`utils/strings.py` is a focused 70-line module hosting the two-direction case conversion helpers (`snake_case` reverses Strawberry's camelCase GraphQL field names back to Django snake_case; `pascal_case` builds GraphQL-friendly type / enum names from Django snake_case field names) consumed across `optimizer/walker.py`, `types/{base, finalizer, converters}.py`, and `sets_mixins.py`. The module is the canonical home — every consumer imports from here. Four forward-looking Lows covering (L1) the `snake_case("id")` field-map quirk's docstring silence, (L2) the `pascal_case` silent-empty contract's docstring silence, (L3) the submodule `__all__` gap mirroring the sibling `rev-utils__relations.md::L3`, and (L4) the module docstring's "third style ever shows up" framing being mildly contradicted by the existing `_camel_case` duplication elsewhere. One defer-with-trigger DRY opportunity (folding `_camel_case` from `filters/inputs.py` and `orders/inputs.py` through a new `utils/strings.py::camel_case`) gated on the 0.0.8 cycle's `orders/` review per the second-closing-folder calibration. Zero High, zero Medium, zero GLOSSARY-only edits, zero source edits. Shape #5 (no-source-edit cycle) qualifies — every Low is forward-looking-without-edit and the DRY bullet defers with explicit trigger.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- Shadow file regenerated this cycle at `docs/shadow/django_strawberry_framework__utils__strings.overview.md` (`scripts/review_inspect.py` invocation): 0 imports, 2 symbols, 0 control-flow hotspots, 0 reflective access, 0 repeated literals — overview confirms the focused-helper review surface.
- L1 (`snake_case("id")` passthrough docstring silence): deferred-with-trigger per `## Low` body verbatim ("Defer until the helper grows a second optimizer-side consumer where the `\"id\"`-passthrough behaviour matters"). Behaviour bit-preserved; the docstring is silent on a contract the consumer relies on but pins via inline comment at `walker.py:184-185`.
- L2 (`pascal_case` silent-empty contract docstring silence): deferred-with-trigger per `## Low` body verbatim ("Defer until a third caller of `utils/strings.py::pascal_case` lands"). Two callers today (`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` and `types/converters.py:326`'s enum-name builder); the silent-empty contract is pinned by `tests/utils/test_strings.py:22-28` but not in the docstring.
- L3 (submodule `__all__` gap): deferred-with-trigger per `## Low` body verbatim ("Defer until any sibling utils submodule adopts `__all__` … or when a third public symbol lands in `utils/strings.py`"). Mirrors `rev-utils__relations.md::L3`'s identical deferral; the folder pass `rev-utils.md` is the natural site to confirm both deferrals coordinate.
- L4 (module docstring's "third style" framing): deferred-with-trigger per `## Low` body verbatim ("Defer until the DRY extraction lands"). The framing becomes bit-correct again once `camel_case` lands in `utils/strings.py`.
- DRY analysis bullet (cross-folder `_camel_case` extraction): defer-with-trigger gated on the 0.0.8 cycle's `orders/` review. The `orders/` subpackage is concurrent spec-028 Slice 3 maintainer work landing post-baseline (commit `b8fbd74`) and is NOT in the 0.0.7 review plan per `docs/review/review-0_0_7.md:1-99`. Per the memory calibration "Cross-folder DRY landings — second-closing folder rule", the cycle that closes `orders/` second owns the extraction.
- No GLOSSARY-only fix in scope. `snake_case` / `pascal_case` are internal-mechanics helpers correctly absent from `docs/GLOSSARY.md` per the memory calibration "Internal-mechanics GLOSSARY absence is correct convention."
- Concurrent maintainer activity: `orders/` subpackage landed post-baseline per `git log --oneline -5 -- django_strawberry_framework/orders/` (`b8fbd74 orders: ship Slices 1-3 of spec-028 — foundation, factories, finalizer binding`, `f3a0777 docs: stage spec-028 orders-0.0.8 subsystem prep`). Per `AGENTS.md` #33 ("unexpected file modifications [...] are presumptively the maintainer's or another dev's in-progress work [...] ignore them as out-of-scope"). Left untouched; flagged in the DRY analysis bullet as the trigger condition.
- `uv.lock` unchanged.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Per-finding dispositions
- Low 1: deferred-with-trigger per `## Low` body verbatim (second optimizer-side consumer of `snake_case("id")` passthrough).
- Low 2: deferred-with-trigger per `## Low` body verbatim (third caller of `pascal_case`).
- Low 3: deferred-with-trigger per `## Low` body verbatim (sibling `utils/` submodule adopts `__all__`, or third public symbol lands here).
- Low 4: deferred-with-trigger per `## Low` body verbatim (DRY `camel_case` extraction lands).

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
Same as Fix report's Notes for Worker 3.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

### State
Not warranted.

### Reason
Cites BOTH halves required by the worker-2 rule for `Not warranted`: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle. Zero source edits, zero test edits, zero GLOSSARY edits, zero docstring edits — no consumer-visible behaviour change, no public-API surface change, no exception message substring change.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle. Every Low is forward-looking-without-edit with verbatim trigger phrasing in the body:

- L1 (`snake_case("id")` field-map quirk docstring silence): defer-with-trigger ("Defer until the helper grows a second optimizer-side consumer where the `\"id\"`-passthrough behaviour matters"). Source spot-check: helper body at `utils/strings.py:38-43` returns `"id"` unchanged for single-segment lowercase input (per-character loop emits `_` only when `i > 0 and c.isupper()`); consumer workaround at `optimizer/walker.py:184-185` confirmed via grep with matching comment `# snake_case("id") does not match the field-map …`. Docstring caveats paragraph at `utils/strings.py:26-31` is silent on the `"id"` passthrough as the artifact reports.
- L2 (`pascal_case` silent-empty contract docstring silence): defer-with-trigger ("Defer until a third caller of `utils/strings.py::pascal_case` lands"). Source spot-check: helper body at `utils/strings.py:70` collapses to `""` via the `if part` segment filter; pinning test at `tests/utils/test_strings.py:22-28` (`test_pascal_case_empty_output_edges`) confirmed present with the inline rationale comment ("a future filter 'fix' from silently changing generated enum names") matching the artifact's quoted prose char-for-char. Sibling `filters/inputs.py::_pascal_case` `ConfigurationError` precedent acknowledged per `rev-filters__inputs.md` Medium #1; canonical helper is silent-empty by design.
- L3 (submodule `__all__` gap mirroring `rev-utils__relations.md::L3`): defer-with-trigger ("Defer until any sibling utils submodule adopts `__all__` … or when a third public symbol lands in `utils/strings.py`"). Cross-artifact verification: `rev-utils__relations.md` is `Status: verified` with the identical defer-with-trigger phrasing on its L3, so this Low correctly confirms the canonical handling for the whole `utils/` folder. Both sibling submodules lack `__all__` today; the folder pass `rev-utils.md` will be the natural coordination site per Worker 2's Notes.
- L4 (module docstring "third style" framing): defer-with-trigger ("Defer until the DRY extraction lands"). Source spot-check: `utils/strings.py:13-15` carries the "Kept minimal on purpose. If a third style (kebab-case, SCREAMING_SNAKE) ever shows up we'll add it here rather than re-deriving inline at the call site." prose verbatim; once `camel_case` lands per the DRY extraction, the parenthetical becomes bit-correct.

### DRY findings disposition
Single DRY bullet: cross-folder `_camel_case` extraction folding the duplicated helper from `filters/inputs.py:783-789` and `orders/inputs.py:164-170` through a new `utils/strings.py::camel_case`. Defer-with-trigger gated on the 0.0.8 cycle's `orders/` review per the second-closing-folder calibration. `orders/` is concurrent spec-028 Slice 3 maintainer work landing post-baseline (per Worker 2's Notes citing `b8fbd74`) and explicitly out of the 0.0.7 review plan. Recorded as future-cycle candidate; the trigger is the cycle that closes `orders/` second owning the extraction.

### Temp test verification
- None — no-source-edit cycle; no temp tests needed.

### Shape #5 five-check audit
1. **In-scope diff stat empty.** `git diff --stat HEAD -- django_strawberry_framework/utils/strings.py tests/utils/test_strings.py CHANGELOG.md` returns empty. The `docs/GLOSSARY.md` working-tree carries two hunks at `:940` (Relay Node integration Shipped-behavior `SyncMisuseError` bullet) and `:1106` (`Strictness mode` `RuntimeError` → `OptimizerError` one-token swap) plus a new top-level `## SyncMisuseError` entry at `:1114-1124`. All three hunks attribute char-for-char to the immediately-prior verified sibling cycles `rev-types__relay.md` (M1 GLOSSARY drift on `SyncMisuseError`) and `rev-types__resolvers.md` (M1 `Strictness mode` swap) — both `Status: verified` with `[x]` checkboxes at `docs/review/review-0_0_7.md` per worker-3 memory entries under `## types/relay.py` and `## types/resolvers.py`. Same dirty-tree-from-verified-sibling attribution pattern recorded across `management/commands/`, `management/`, `optimizer/`, and `testing/` folder cycles. The cycle's own "Files touched: None" claim holds.
2. **Worker 2 sections boilerplate.** `## Fix report (Worker 2)`, `## Comment/docstring pass`, `## Changelog disposition` all open with `Filled by Worker 1 per no-source-edit cycle pattern.` verbatim.
3. **No GLOSSARY-only fixes.** Every Low is forward-looking-without-edit and each carries verbatim "Defer until …" trigger phrasing in its body (enumerated above). The DRY bullet is also defer-with-trigger, not act-now.
4. **Changelog `Not warranted` with both citations.** Disposition cites both AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND active plan `docs/review/review-0_0_7.md` silence on changelog authorization for this cycle. `git diff -- CHANGELOG.md` returns empty.
5. **Ruff plausible.** Spot-verified: `uv run ruff format --check django_strawberry_framework/utils/strings.py tests/utils/test_strings.py` → "2 files already formatted"; `uv run ruff check django_strawberry_framework/utils/strings.py tests/utils/test_strings.py` → "All checks passed!".

### `What looks solid` spot-verify
- Module docstring discipline at `utils/strings.py:1-16` matches the artifact's quoted "Both directions are needed at the GraphQL/Django boundary" framing and the "Kept minimal on purpose…" closing prose verbatim.
- Per-helper docstring acronym caveats at `:26-31` (`"HTMLParser"` → `"h_t_m_l_parser"`) and `:53-61` (`"my_HTTP_response"` → `"MyHttpResponse"`) match the artifact's quoted "documented here so a future direct caller is not surprised" framing on both helpers.
- Coverage pins at `tests/utils/test_strings.py:6-9, 12-19, 22-28` confirmed present with the silent-empty-contract inline rationale comment matching the artifact's quoted prose char-for-char.
- Zero module-level imports per `utils/strings.py:1-16`; the static helper overview's "Imports: None, 2 symbols, 0 control-flow hotspots" framing is consistent with the 70-line single-helper-pair surface.

### Verification outcome
cycle accepted; verified.
