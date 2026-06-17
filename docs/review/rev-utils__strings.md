# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## DRY analysis

- None — this module IS the single-source for the GraphQL↔Django name-case boundary. `snake_case` is imported never-respelled by `optimizer/walker.py:23`, `types/finalizer.py:66`, `types/base.py:56`, and `management/commands/inspect_django_type.py:52`; `pascal_case` by `sets_mixins.py:49`, `filters/inputs.py:43`, and `types/converters.py:52`. The two `filters/inputs.py` wrapper (`_pascal_case`, line 165) and the module docstring's "add a third style here rather than re-deriving inline" note are explicit anti-duplication design (every consumer delegates here, nobody re-implements casing). Re-consolidating a consolidation point is net-negative; folding the two functions into one parametrized helper would couple two opposite transforms (camel→snake split-on-uppercase vs snake→pascal split-on-underscore) behind a flag. Correct as two functions.

## High:

None.

## Medium:

None.

## Low:

### `snake_case` is `lru_cache`-memoized but `pascal_case` is not — document the asymmetry's rationale (deferred, correct as-is)

The +9 change wrapped `snake_case` in `@functools.lru_cache(maxsize=2048)` (commit 79b74b46) and added a docstring paragraph justifying it (per-request, per-selection, fixed-vocabulary hot path in the optimizer walker). `pascal_case` is *not* cached. The asymmetry is correct: `pascal_case` is called only at schema-build time (`types/converters.py:357` enum naming, `filters/inputs.py` / `sets_mixins.py` input-type naming) — a one-time cost during type finalization, not a per-request hot path, so caching would only retain entries with no hit-rate benefit. The asymmetry is self-evident from the docstrings (`snake_case` explains "every request"; `pascal_case` describes build-time enum/type naming) but is not stated as an explicit *contrast*. Defer: add a one-line "build-time only, so not memoized" note to `pascal_case` only if a future caller moves `pascal_case` onto a per-request path; until then the existing docstrings carry enough signal and an explicit cross-reference would be noise.

### Cache-size constant `2048` is an unexplained magic number (deferred, correct as-is)

`maxsize=2048` is a bounded LRU over the schema's finite GraphQL-field-name vocabulary; 2048 comfortably exceeds any realistic single-schema field-name count, so the cache effectively never evicts in steady state while staying bounded against a pathological direct caller passing unbounded distinct strings. The value is sound. Defer documenting the derivation inline until a real schema approaches the bound (the cache stays correct under eviction regardless — `snake_case` is pure, so an evicted entry simply recomputes); a comment now would be speculative.

## What looks solid

### DRY recap

- **Existing patterns reused.** Module is the canonical case-conversion surface; consumers import the two functions directly and never re-implement (`filters/inputs.py:165` `_pascal_case` is a thin validating wrapper over `pascal_case`, not a re-derivation). Re-exported once from `utils/__init__.py:30` and listed in `__all__` (lines 36, 38), matching the package docstring bullet at `utils/__init__.py:9`.
- **New helpers considered.** A single parametrized `convert_case(name, style)` was considered and rejected: the two transforms are inverse directions with disjoint split rules (uppercase-boundary insertion vs underscore-segment join) and no shared body — a dispatch flag would add a branch and obscure two trivially-readable loops. The module docstring already commits to "add a third style here" as the extension path, which is the right granularity.
- **Duplication risk in the current file.** None. Two short pure functions, zero repeated literals (confirmed by the static overview's "Repeated string literals: 0"), no shared internal helper to extract.

### Other positives

- **Cache safety is genuinely sound, not just asserted.** `snake_case` is a pure deterministic `str -> str` with no mutable state, no Django/ORM access (static overview: zero Django markers, zero calls of interest), and returns an immutable `str`, so `lru_cache` cannot leak request-scoped state or alias a mutable result. The docstring's "Pure `str -> str`, so caching is always safe" is accurate.
- **Producer/consumer key symmetry is correct by construction.** The optimizer/type layers build `field_map` via `snake_case(f.name)` on already-snake_case Django field names (`types/base.py:488`) and look up via `snake_case(sel.name)` on camelCase GraphQL names (`walker.py:332,846,1068`; `finalizer.py:417,597`; `base.py:1388,1572`). Both converge on the same key because `snake_case` is **idempotent on already-snake_case input**: an all-lowercase string inserts no boundaries (`c.isupper()` never fires) and `.lower()` is identity on lowercase, so `snake_case(snake) == snake`. This idempotency is the load-bearing invariant making the cache and the field-map keying agree; it holds for the lone uppercase-free Django-name domain. The `snake_case("id") != "uuid"` custom-pk mismatch is the one case where the keys legitimately diverge, and it is explicitly handled out-of-band at `walker.py:358-374` (Decision 7), not papered over.
- **`pascal_case` edge cases are exhaustively pinned.** `tests/utils/test_strings.py` covers leading (`_leading`→`Leading`), trailing (`trailing_`→`Trailing`), double (`double__underscore`→`DoubleUnderscore`) underscores, and the silent-empty contract (`""`→`""`, `"_"`→`""`) with a comment explaining why the empty contract is pinned (guard a future filter "fix" from changing generated enum names). `snake_case` round-trips (`name`, `isPrivate`, `createdDate`) are pinned too.
- **Acronym/edge-case caveats are documented for future direct callers.** Both docstrings flag that strict casing is assumed and acronyms are not preserved (`HTMLParser`→`h_t_m_l_parser`; `my_HTTP_response`→`MyHttpResponse`), explicitly noting these are unreachable through the documented Strawberry/Django call chain but documented so a direct caller is not surprised. This matches the AGENTS.md "highest standard" bar — the boundary behavior is stated, not left implicit.
- **Digit handling is correct for the live domain.** `snake_case` treats digits as lowercase-passthrough (no boundary, since `"5".isupper()` is `False`), so `createdAt2` → `created_at2`; `pascal_case` capitalizes the segment's first char and leaves digits (`status_2` → `Status2`). Neither inserts spurious boundaries around digits — correct for Django identifiers.

### Summary

A 79-line two-function module that is the single canonical home for GraphQL↔Django name-case conversion. The +9 change (the only since-baseline edit, commit 79b74b46, already merged into HEAD) added `@functools.lru_cache(maxsize=2048)` to `snake_case` plus a justifying docstring paragraph; this-cycle `git diff HEAD` is empty. The cache is provably safe (pure, immutable-return, no Django access) and well-motivated (per-request optimizer hot path over a fixed vocabulary). The load-bearing correctness property — `snake_case` idempotency on already-snake_case input, which keeps producer-built and consumer-looked-up `field_map` keys in agreement — holds, and the one legitimate divergence (custom-pk `id`/`uuid`) is handled out-of-band by the walker. Both functions' edge cases (empty, underscores, acronyms, digits) are either pinned in `tests/utils/test_strings.py` or documented as out-of-domain. DRY is None (consolidation point). No High/Medium; two forward-looking, correct-as-is Lows. No GLOSSARY mentions of either symbol. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 270 files left unchanged.
- `uv run ruff check .` — pass, all checks passed.

### Notes for Worker 3
- Shadow overview used: `docs/shadow/django_strawberry_framework__utils__strings.overview.md` (0 markers, 0 calls of interest, 0 repeated literals — confirms pure-function module).
- This-cycle `git diff HEAD -- django_strawberry_framework/utils/strings.py` is empty; the +9 `lru_cache` change (commit 79b74b46) is already in HEAD.
- Low 1 (memoization asymmetry doc): forward-looking; act only if `pascal_case` moves onto a per-request path. No edit this cycle.
- Low 2 (magic `2048`): forward-looking; act only if a real schema approaches the bound. Cache stays correct under eviction (pure fn). No edit this cycle.
- No GLOSSARY-only fix in scope (grep of `docs/GLOSSARY.md` for `snake_case`/`pascal_case`/`PascalCase`/`strings.py` returned zero hits).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted — the `lru_cache` rationale, acronym caveats, and the silent-empty contract are already documented accurately; both Lows are deferred forward-looking documentation, not stale-comment fixes.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (empty `git diff HEAD`); AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` are silent on changelog entries for review-only cycles.

---

## Verification (Worker 3)

### Logic verification outcome

No-source-edit cycle (shape #5). H0/M0/L2 (both forward-looking). Per-item zero-edit proof: `git diff HEAD -- django_strawberry_framework/utils/strings.py` is empty; the +9 `lru_cache` change is in HEAD via `79b74b46` (`git diff 14910230..HEAD` shows exactly the `import functools` + `@functools.lru_cache(maxsize=2048)` + the memoization docstring paragraph). Last-touch `79b74b46` (2026-06-15).

- **(a) Cache safety — `snake_case` is a pure deterministic `str -> str`.** Re-derived from live source (strings.py:47-52): body reads only the `name` arg, builds a fresh `list`, returns an immutable `str`; zero Django/`_meta`/ORM access, no mutable arg, no closure state. A cache over an impure fn would be a HIGH — not the case here. Temp test confirms `cache_info().maxsize == 2048`, cache hits serve the identical value, and the cached result equals an inline un-cached reference impl across `["", "X", "isPrivate", "HTMLParser", "createdAt2", "id"]` (lru_cache changed no semantics). Cache-clear→recompute returns the same value (pure, so eviction is harmless).
- **(b) Idempotency on already-snake_case input holds.** Re-derived: an all-lowercase string never fires `c.isupper()` so no boundary is inserted, and `.lower()` is identity on lowercase → `snake_case(snake) == snake`. Temp test pins it across `["name","is_private","created_date","created_at2","first_name","payment_method","legacy_id","uuid","id","a","a_b_c_d"]`. Producer/consumer key symmetry confirmed by grep: producer keys `field_map` via `snake_case(f.name)` on already-snake_case Django names (base.py:488); consumers look up via `snake_case(sel.name)` on camelCase GraphQL names (walker.py:332/846/1068, finalizer.py:417/597, base.py:1388/1572, inspect_django_type.py:192). Both converge on the same key. The one legitimate divergence (`snake_case("id") != "uuid"`, custom pk) is handled out-of-band at walker.py:358-374 — confirmed by the live comment at walker.py:363 (`"snake_case(\"id\") == \"id\" does not match the field-map"`). A divergence would silently drop fields/permissions; idempotency closes that.
- **(c) `pascal_case` / `camel_case` edge cases correct.** Temp test verifies empty (`""`→`""`), `"_"`→`""`, `"__"`→`""`, leading (`_leading`→`Leading`), trailing (`trailing_`→`Trailing`), double (`double__underscore`→`DoubleUnderscore`), digits (`status_2`→`Status2`, `createdAt2`→`created_at2` passthrough), and the acronym caveat (`HTMLParser`→`h_t_m_l_parser`, `my_HTTP_response`→`MyHttpResponse`). The silent-empty contract, leading/trailing/double-underscore collapse, and round-trips are pinned in the permanent suite `tests/utils/test_strings.py` (`test_pascal_case_handles_snake_case_inputs` :17-19, `test_pascal_case_empty_output_edges` :27-28, `test_snake_case_round_trips_camel_case` :6) — so the temp test corroborates rather than being the sole proof.
- **(d) Both Lows forward-looking.** L1 (memoization-asymmetry doc note): `pascal_case` is build-time only (converters.py:357 enum naming, sets_mixins.py:91, filters/inputs.py:525 via `_pascal_case`), not a per-request hot path — caching it would retain entries with no hit-rate benefit; trigger = a future caller moving `pascal_case` onto a per-request path. L2 (magic `2048`): bounded LRU over a finite field-name vocabulary; correct under eviction because the fn is pure; trigger = a real schema approaching the bound. Both gated on a future/upstream change, not a staged framework slice → no source-site TODO/NotImplementedError owed.

### DRY findings disposition

DRY None — consolidation-point file, carried as-is. Verified by grep: `snake_case` and `pascal_case` are each exactly one `def` (strings.py); every consumer imports and delegates, nobody re-implements. `filters/inputs.py:165 _pascal_case` is a thin validating wrapper over `pascal_case` (calls it at :182), not a re-derivation. Re-exported once from `utils/__init__.py:30` and in `__all__` (:36,:38). Folding the two functions into one parametrized helper would couple two inverse transforms behind a flag — net-negative. Correct as two functions.

### Temp test verification
- Temp test used: `docs/review/temp-tests/utils/test_strings_cache.py` (gitignored — confirmed via `git check-ignore`). 11 tests, all passed (`uv run pytest ... --no-cov`): cache-wrapping, purity/determinism, idempotency-on-snake, camel round-trips, custom-pk divergence, acronym caveat, empty/single, pascal edge cases, cache-clear-recompute, and cached-vs-reference equivalence.
- Disposition: deleted at cycle closeout by Worker 0. No new behavior bug or uncovered edge case surfaced — the permanent `tests/utils/test_strings.py` already pins the load-bearing edges, so no promotion-to-permanent finding is owed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/strings.py` checklist box. Shape #5 checklist met: per-item HEAD diff empty; each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.`; both Lows forward-looking (no GLOSSARY-only fix — grep returned zero); changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan silence, and `git diff HEAD -- CHANGELOG.md` is empty; ruff format-check (`1 file already formatted`) + check (`All checks passed!`) pass.

---

## Iteration log
