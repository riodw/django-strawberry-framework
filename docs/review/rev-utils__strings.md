# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## DRY analysis

- None — the module is the two-symbol canonical home for camelCase↔snake_case and snake_case→PascalCase conversion. `snake_case` has five call sites across `optimizer/walker.py:175,558,695` and `types/base.py:174,820` plus `types/finalizer.py:194`; `pascal_case` has one call site at `types/converters.py:292`. Both helpers are already imported from this module wherever needed (no parallel inline implementations exist in the package), and the docstring's "If a third style ever shows up we'll add it here rather than re-deriving inline at the call site" comment is the explicit DRY contract. Folder-level cross-sibling DRY (utils/relations + utils/strings + utils/typing) lands in `rev-utils.md`, not here.

## High:

None.

## Medium:

None.

## Low:

### `snake_case` empty-string edge undocumented; not test-pinned

`snake_case("")` returns `""` (the loop body never executes), parallel to the test-pinned `pascal_case("") == ""` contract at `tests/utils/test_strings.py:27`. The behavior is unreachable through the documented call chain (Strawberry never emits empty field names; Django field names are never empty), but the asymmetry with `pascal_case` — where the analogous empty-segment-collapse contract IS pinned at `tests/utils/test_strings.py:22-28` with an explicit "prevent a future filter 'fix' from silently changing generated enum names" rationale — is worth a one-line pin and a docstring sentence so the symmetry is explicit. Defer until a third invariant in this file needs pinning OR until any future direct caller surfaces; cosmetic today because no consumer feeds empty strings.

```django_strawberry_framework/utils/strings.py:38-43
    out: list[str] = []
    for i, c in enumerate(name):
        if i > 0 and c.isupper():
            out.append("_")
        out.append(c.lower())
    return "".join(out)
```

### Numeric-character behavior in `snake_case` unstated

`snake_case("field2Name")` returns `"field2_name"` and `snake_case("field2")` returns `"field2"` — digits are passed through unchanged and do not trigger boundary insertion. This matches Strawberry's default name-conversion contract (digits stay attached to the preceding word) and is correct, but the docstring only enumerates the camelCase acronym caveat and is silent on digits. Forward-looking only; defer until a Django field name with embedded digits surfaces a consumer-visible difference, OR fold into the same docstring revision as the empty-string pin above.

### `pascal_case` numeric-leading-segment behavior unstated

`pascal_case("2fa_enabled")` returns `"2faEnabled"` (no, wait — `"2fa".capitalize() == "2fa"`, so the result is `"2faEnabled"`). Per-segment `str.capitalize()` does not promote a digit to upper-case, so a snake_case segment beginning with a digit produces a lower-case-first PascalCase segment. Unreachable through the documented call chain (Django field names cannot begin with a digit per Python identifier rules), but the asymmetry with the upper-case-first contract the docstring promises is worth a sentence. Same trigger as the previous two Lows.

## What looks solid

### DRY recap

- **Existing patterns reused.** None — this IS the canonical home for the two helpers; all six in-package call sites import from `..utils.strings` (`optimizer/walker.py:15`, `types/base.py:42`, `types/converters.py:52`, `types/finalizer.py:48`, plus the `utils/__init__.py:21` re-export hub).
- **New helpers considered.** A third style (kebab-case, SCREAMING_SNAKE) is explicitly deferred-with-trigger in the module docstring (`utils/strings.py:13-15`); no candidate exists today.
- **Duplication risk in the current file.** None. Two functions, each with a single responsibility; the acronym caveat is symmetric across both docstrings by design (`snake_case` docstring at lines 26-31, `pascal_case` docstring at lines 53-61), and the symmetry is intentional rather than copy-paste drift.

### Other positives

- Module docstring frames the GraphQL/Django boundary contract precisely: `snake_case` is the inverse of Strawberry's default camelCase emitter; `pascal_case` is the enum-name builder for `<TypeName><FieldName>Enum` schema names. Consumer citation chain holds (`types/converters.py:292` matches the docstring's stated shape).
- Round-trip correctness for the documented input domain holds: `pascal_case(snake_case(camel))` is NOT identity (camelCase has no underscores to split on for pascal), but the design never asserts a full round-trip — `snake_case` is for GraphQL→Django lookups, `pascal_case` is for Django→GraphQL type-name generation. The two functions operate on disjoint input domains and the docstrings are honest about it.
- Acronym caveats are documented with the unreachable-through-documented-call-chain disclaimer on both functions; future direct callers are not surprised.
- Test file `tests/utils/test_strings.py` pins the documented contract (round-trip examples, leading/trailing/double underscore collapse, empty-segment silent-empty for `pascal_case`).
- Shadow-overview confirms zero imports, zero control-flow hotspots, zero calls of interest, zero TODO comments, zero repeated string literals — the module is minimal by design and the helper has nothing to flag.

### Summary

`utils/strings.py` is the two-symbol canonical home for case conversion at the GraphQL/Django boundary. Zero High/Medium findings: the documented input domain (strict camelCase one direction, strict snake_case the other) covers every in-package call site, the acronym caveats are explicit, and the asymmetric round-trip is honest. Three forward-looking Lows on edge-case documentation/pinning (empty-string `snake_case` parallel to the pinned `pascal_case("")` contract; numeric-character behavior in both functions) — all defer-with-trigger ("until a direct caller surfaces" OR "until a third invariant needs pinning"), cosmetic today. DRY analysis lists no opportunities because this file IS the consolidation home; cross-folder concerns route through `rev-utils.md`.

---

## Fix report (Worker 2)

### Files touched
- None — consolidated no-op pass. 0H/0M/3L all forward-looking per Worker 1's own prose ("Defer until a third invariant in this file needs pinning OR until any future direct caller surfaces"; "Forward-looking only; defer until a Django field name with embedded digits surfaces a consumer-visible difference"; "Same trigger as the previous two Lows"). DRY analysis self-asserts canonical-home status ("the module is the two-symbol canonical home"; "None. Two functions, each with a single responsibility").

### Tests added or updated
- None.

### Validation run
- `uv run ruff format .` — pass / no-changes (118 files left unchanged).
- `uv run ruff check --fix .` — pass / no-changes (All checks passed!).
- No pytest per `START.md` standing rule (no source edit, no test change).

### Notes for Worker 3
- Shadow file used: none (no source edit; the existing `docs/shadow/utils__strings.overview.md` artifact aligns with Worker 1's "zero imports, zero control-flow hotspots, zero calls of interest, zero TODO comments, zero repeated string literals" recap).
- No intentionally-rejected findings.
- Deferred findings and verbatim trigger conditions:
  - **Low 1 (`snake_case("")` empty-string edge undocumented; not test-pinned)** — Trigger phrase verbatim: "Defer until a third invariant in this file needs pinning OR until any future direct caller surfaces; cosmetic today because no consumer feeds empty strings." Both disjunctive arms preserved.
  - **Low 2 (Numeric-character behavior in `snake_case` unstated)** — Trigger phrase verbatim: "Forward-looking only; defer until a Django field name with embedded digits surfaces a consumer-visible difference, OR fold into the same docstring revision as the empty-string pin above." Both disjunctive arms preserved.
  - **Low 3 (`pascal_case` numeric-leading-segment behavior unstated)** — Trigger phrase verbatim: "Same trigger as the previous two Lows." Aliased reference to L1+L2 trigger blocks whose verbatim phrasing is preserved above.

---

## Comment/docstring pass

Consolidated into this single spawn per `worker-2.md` consolidated-single-spawn shape: "All Lows are explicitly forward-looking per Worker 1's own prose … no in-cycle edit required."

### Files touched
- None.

### Per-finding dispositions
- **Low 1**: no edit — Worker 1's verbatim deferral prose ("Defer until a third invariant in this file needs pinning OR until any future direct caller surfaces; cosmetic today because no consumer feeds empty strings") self-adjudicates the in-cycle question. The asymmetry-with-`pascal_case("")`-pin observation is recorded in the artifact body for the next cycle that satisfies a trigger.
- **Low 2**: no edit — Worker 1's verbatim deferral prose ("Forward-looking only; defer until a Django field name with embedded digits surfaces a consumer-visible difference, OR fold into the same docstring revision as the empty-string pin above") self-adjudicates and explicitly couples this Low to L1's fix surface so no independent in-cycle action is warranted.
- **Low 3**: no edit — Worker 1's verbatim deferral prose ("Same trigger as the previous two Lows") aliases to L1+L2 dispositions; same per-finding outcome.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

### Notes for Worker 3
Comment pass is structurally a no-op (pattern 18: 0H/0M/N-Lows-all-with-Worker-1's-verbatim-deferral-prose). Trigger phrases preserved verbatim above so a future trigger-satisfying cycle can grep-discover the routing decision.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- `AGENTS.md` line 21: "Do not update CHANGELOG.md unless explicitly instructed."
- The active review plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle (cycle 29 in the 0.0.7 release pass).
- Reinforcing citations: (a) zero-line source footprint — this cycle made no source edit at all, so there is no consumer-visible behaviour to note; (b) twenty-nine-deep precedent chain across the 0.0.7 release pass (cycles 1–28 all closed `Not warranted`); (c) `utils/strings.py` self-asserts canonical-home DRY status with zero edits across the release boundary — pattern (f) from cycles 23-28 (utils-style canonical-home file's self-asserted DRY status is a reinforcing citation under AGENTS.md + plan silence).

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

---

## Verification (Worker 3)

### Logic verification outcome
0H/0M/3L all forward-looking with Worker 1's verbatim deferral prose preserved. L1 trigger ("Defer until a third invariant in this file needs pinning OR until any future direct caller surfaces; cosmetic today because no consumer feeds empty strings") — both disjunctive arms preserved. L2 trigger ("Forward-looking only; defer until a Django field name with embedded digits surfaces a consumer-visible difference, OR fold into the same docstring revision as the empty-string pin above") — both disjunctive arms preserved. L3 trigger ("Same trigger as the previous two Lows") — alias to L1+L2, both alias targets verbatim. No intentionally-rejected findings, so the false-premise rule is not engaged.

### DRY findings disposition
Self-asserted canonical-home status accepted ("the module is the two-symbol canonical home"; six in-package call sites all importing from `..utils.strings`; folder-level cross-sibling DRY explicitly routed to `rev-utils.md`). No DRY observations to forward.

### Temp test verification
- Temp test files used: none.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — `git diff -- django_strawberry_framework/utils/strings.py` empty; `git diff -- CHANGELOG.md` empty matching `Not warranted` framing with AGENTS.md:21 + plan silence + twenty-eight-cycle precedent chain (all three legs honest); ruff format + check clean on touched file. Sets top-level `Status: verified` AND marks `review-0_0_7.md:127`.
