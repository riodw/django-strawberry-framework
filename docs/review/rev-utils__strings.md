# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## DRY analysis

- None — the module is itself the single source of truth for case conversion at the GraphQL↔Django name boundary. `snake_case` is imported and called by every reverse-direction consumer (`types/base.py:56,488,1389,1581`, `types/finalizer.py:66,417,597`, `optimizer/walker.py:23,333,847,1049`, `management/commands/inspect_django_type.py:52,192`) with zero re-spellings; `pascal_case` is imported and called by every forward-direction consumer (`sets_mixins.py:49,91`, `filters/inputs.py:44,183`, `types/converters.py:73,549`). The two thin call-site wrappers that exist (`filters/inputs.py::_pascal_case`, `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`, `mutations/inputs.py::_token_for_field` at `:323`) deliberately do NOT re-implement the conversion — they delegate to or contrast against this module and add only a local guard / a uniquely-decomposable token shape. Those wrappers are intentional sibling design (distinct collision/empty-input contracts), not duplication to fold here.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module reuses only stdlib `functools.lru_cache` (`strings.py:21`). It is the canonical helper that other modules reuse, not a reuser itself.
- **New helpers considered.** No third case style (kebab-case, SCREAMING_SNAKE) has a consumer yet; the module docstring (`strings.py:13-15`) explicitly defers adding one until a real call site appears, which is the correct YAGNI posture. No new helper warranted.
- **Duplication risk in the current file.** The two functions share the conceptual "case conversion" role but no code — `snake_case` is a char-by-char boundary scan, `pascal_case` is a segment split-capitalize-join. They are inverse-ish but not symmetric (snake does not collapse underscores; pascal does), so a shared internal primitive would be a false abstraction. Correct as two independent functions.

### Other positives

- **Every docstring claim is verifiably exact.** All worked examples reproduce against the implementation: `snake_case` — `"name"→"name"`, `"isPrivate"→"is_private"`, `"createdDate"→"created_date"`, and the documented acronym caveat `"HTMLParser"→"h_t_m_l_parser"`; `pascal_case` — `"is_active"→"IsActive"`, `"status"→"Status"`, `"payment_method"→"PaymentMethod"`, `"_leading"→"Leading"`, `"double__underscore"→"DoubleUnderscore"`, and the acronym caveat `"my_HTTP_response"→"MyHttpResponse"`. The empty/underscore-only inputs (`""`, `"_"`, `"__"`) return `""` exactly as the downstream `filters/inputs.py::_pascal_case` guard docstring (`filters/inputs.py:170-172`) asserts.
- **Cross-module comments are accurate, not self-asserting fiction.** `mutations/inputs.py:314` claims `pascal_case` "collapses underscores across the whole name" — true (`split("_")` drops empty segments). `filters/inputs.py:161` and `sets_mixins.py:69` both name `utils.strings.pascal_case` as the single source of truth and only layer their own guards — verified at source; neither re-implements the conversion. The `_token_for_field` (`mutations/inputs.py:305-323`) deliberately uses `.replace("_","").capitalize()` (a DIFFERENT, uniquely-decomposable shape) and the docstring correctly explains WHY it is *not* `pascal_case` — no drift, no mis-claim.
- **`lru_cache` justified and safe.** `snake_case` is memoized (`maxsize=2048`) because the optimizer walker reverses the same small fixed GraphQL-field vocabulary every request; pure `str→str` so caching is always sound. `pascal_case` is intentionally NOT cached — it runs at type-build time (enum/input-class naming), not per-request per-selection, so a cache would only retain garbage. The asymmetry is correct, not an oversight.
- **Acronym/edge caveats documented for future direct callers.** Both functions note the strict-case-only limitation and that the unhandled-acronym path is unreachable through the documented Strawberry/Django call chain, pre-empting surprise for a future direct caller. Good defensive documentation discipline.

### Summary

`utils/strings.py` is a tight, pure, well-documented two-function module that single-sources case conversion across the GraphQL↔Django name boundary. Both diffs against the per-cycle baseline (`d2cb8348`) and HEAD are empty, with no commits touching the file since baseline. Every docstring example and acronym caveat reproduces exactly against the implementation, and every cross-module comment naming this module is accurate at source. `snake_case` and `pascal_case` are re-exported from the `utils` subpackage `__all__` but not from the package root, and carry no GLOSSARY entry — consistent with every other internal `utils.` cross-cutting helper (e.g. `relation_kind`, type-unwrap), so the absence is correct. No High, Medium, or Low findings, and no actionable DRY opportunity (the module IS the dedup source). Genuine no-source-edit (shape #5) cycle.

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
- Both `git diff d2cb8348 -- utils/strings.py` and `git diff HEAD -- utils/strings.py` are empty; `git log d2cb8348..HEAD -- utils/strings.py` returns nothing. Nothing to fix.
- No High, no behaviour-changing Medium; all severity sections `None.` DRY is a single `None —` (module is the single source of truth).
- No GLOSSARY-only fix in scope: `snake_case`/`pascal_case` are `utils`-subpackage `__all__` exports but NOT package-root exports and carry no GLOSSARY entry, matching every other internal `utils.` helper — absence is correct, no drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

- No comment/docstring edits warranted. Every docstring example and acronym caveat was reproduced against the implementation and matches exactly; every cross-module comment referencing this module (`mutations/inputs.py:314`, `filters/inputs.py:161`, `sets_mixins.py:69`) is accurate at source. No stale or restating comments.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

- **Not warranted.** No source, test, or doc edits were made this cycle. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`) which is silent on any changelog requirement for review cycles, no changelog entry is warranted.

---

## Verification (Worker 3)

### Logic verification outcome
All severity sections are `None.`; nothing to address or reject. Independently confirmed the `None.` findings are genuine by reproducing every documented conversion at runtime (`uv run python`):
- `snake_case`: `"name"→"name"`, `"isPrivate"→"is_private"`, `"createdDate"→"created_date"`, and the acronym caveat `"HTMLParser"→"h_t_m_l_parser"` (each upper-case char triggers a boundary, as documented).
- `pascal_case`: `"is_active"→"IsActive"`, `"status"→"Status"`, `"payment_method"→"PaymentMethod"`, `"_leading"→"Leading"`, `"trailing_"→"Trailing"`, `"double__underscore"→"DoubleUnderscore"`, and the acronym caveat `"my_HTTP_response"→"MyHttpResponse"` (per-segment `str.capitalize()` lower-cases interior upper-case, as documented).
- Empty/underscore-only edges: `pascal_case("")==""`, `pascal_case("_")==""`, `pascal_case("__")==""` — the silent-empty contract `filters/inputs.py::_pascal_case` relies on holds.
All three claims match the existing tests in `tests/utils/test_strings.py` (round-trip camel, snake inputs incl. collapse edges, empty-output edges); the suite passes (3 passed) and `strings.py` reports 100% line coverage on the focused run.

### DRY findings disposition
DRY is a single `None —`: the module IS the single source of truth for case conversion at the GraphQL↔Django boundary, reused by reverse-direction consumers (`snake_case`) and forward-direction consumers (`pascal_case`); the call-site wrappers (`filters/inputs.py::_pascal_case`, `sets_mixins.py`, `mutations/inputs.py::_token_for_field`) delegate-or-contrast rather than re-implement. No actionable opportunity; nothing forwarded.

### Temp test verification
- None — no temp tests created. The existing permanent suite (`tests/utils/test_strings.py`) plus runtime reproduction was sufficient; not the only proof of shipped behavior.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/strings.py` checklist box.

Shape #5 gates all hold:
1. `git diff d2cb8348 -- utils/strings.py`, `git diff HEAD -- utils/strings.py`, and `git log d2cb8348..HEAD -- utils/strings.py` are all empty; owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) is empty — no sibling-cycle attribution needed.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`
3. All severities `None.`; no GLOSSARY-only fix. `snake_case`/`pascal_case` are `utils`-subpackage `__all__` exports (`utils/__init__.py:36,38`) but absent from the package root `__init__.py` and carry zero GLOSSARY entry — consistent with every other private `utils.` cross-cutting helper, so absence is correct, not drift → genuine #5 not missed #4.
4. Changelog `Not warranted` cites BOTH `AGENTS.md` and the active plan's silence; `git diff -- CHANGELOG.md` empty.
5. `uv run ruff format --check` ("1 file already formatted") + `uv run ruff check` ("All checks passed!") pass on the target.
