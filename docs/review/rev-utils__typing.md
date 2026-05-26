# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## DRY analysis

- **Canonical home for type-unwrapping.** This module IS the cross-cutting consolidation site for graphql-core / Strawberry / native-list peeling — module docstring (`utils/typing.py:1-9`) names the contract and `utils/__init__.py:10-14` re-exports the pair. Consumer citation chain: `unwrap_graphql_type` is used at `optimizer/extension.py:344` (inside `_walk_gql_type` for schema audit recursion) and `optimizer/extension.py:427` (inside `_resolve_model_from_return_type` for the optimizer's return-type→model lookup); `unwrap_return_type` has zero in-package consumers today and is exported for the upcoming schema-factory per `utils/__init__.py:13-14`. Zero new helper-extraction opportunities — both functions are already as small as their `of_type` / `get_origin` mechanics allow.
- **Defer until a third type-unwrap variant lands** (e.g. a full-peel native-list helper or an Optional/Union peeler) — at that point the three peelers should share a single dispatch loop with a per-flavor "stop predicate" rather than three open-coded shapes. Trigger condition: when the schema-factory consumer surfaces and a third unwrap shape lands here, fold all three through one `_peel(rt, *, predicates: tuple[...])` driver.

## High:

None.

## Medium:

None.

## Low:

### `unwrap_return_type` does not peel `Optional[list[T]]` / `list[T] | None`

`get_origin(Optional[list[int]])` is `typing.Union` (across 3.10–3.14), not `list`, so `unwrap_return_type(Optional[list[int]])` returns the `Optional[list[int]]` form unchanged rather than peeling to `int` or to `list[int]`. The module docstring (`utils/typing.py:1-9`) frames this helper as portable across Strawberry annotation forms; an Optional-wrapped list annotation is one of the most common Strawberry resolver return shapes. The current consumer chain does not exercise this path — `unwrap_graphql_type` runs against graphql-core schema types where Optional is already encoded as a `GraphQLNonNull`/absence-of-`GraphQLNonNull` rather than a `typing.Union`, and `unwrap_return_type` has no in-package consumer yet. Forward-looking: when the upcoming schema-factory consumer (named at `utils/__init__.py:13-14`) lands and calls `unwrap_return_type` against a raw Python annotation, decide whether to peel `Union[..., None]` to its non-`None` arm before the list-origin check. Defer until the schema-factory consumer's first call site lands; the consumer's return-type contract will determine whether to peel `Optional` here or to require pre-peeled input.

```django_strawberry_framework/utils/typing.py:33-65
def unwrap_return_type(rt: Any) -> Any:
    inner = getattr(rt, "of_type", None)
    if inner is not None:
        return inner
    if get_origin(rt) is list:
        ...
```

### `unwrap_return_type` `Any` sentinel for bare `list` is undocumented in the docstring

The docstring (`utils/typing.py:34-56`) lists `list[int] -> int` and `list[list[int]] -> list[int]` examples but does not name the `bare list -> Any` / `typing.List -> Any` contract that the tests pin (`tests/utils/test_typing.py:19-38`). The "unknown element type" sentinel is a real consumer-visible behavior on the public re-export; without an example line, a consumer reading only the docstring may pass bare `list` and expect a different sentinel (e.g. `object`, `None`). Add a single example line: `bare list / typing.List -> Any (unknown element type sentinel)`. Defer until the next docstring touch on this file — single-line edit, no behavior change.

### Asymmetric peel-depth contract is implicit at the module level

`unwrap_graphql_type` peels all layers (`while hasattr`); `unwrap_return_type` peels one. The function-level docstrings (`utils/typing.py:15-27` and `utils/typing.py:34-56`) state this clearly per-function, and the module docstring (`utils/typing.py:1-9`) names both contracts but does not explicitly call out the peel-depth asymmetry. The asymmetry is intentional (graphql-core wrapper stacks are unbounded; Python annotation peel is one-layer-at-a-time so callers can inspect nesting), but a reader scanning only the module docstring may miss it. Defer until a third unwrap helper lands here; at that point a "peel-depth contract" table in the module docstring earns its keep.

## What looks solid

### DRY recap

- **Existing patterns reused.** Module is a leaf utility — relies only on `typing.Any`, `get_origin`, `get_args` from the standard library (`utils/typing.py:11`). No imports from other package modules; `optimizer/extension.py:45` and `utils/__init__.py:22` are the consumer-direction imports (utils ← optimizer / utils ← utils-init), confirming one-way leaf-direction.
- **New helpers considered.** A combined "peel-and-classify" helper (return `(inner, was_list, was_of_type_wrapper)`) was considered and rejected — neither current consumer needs the classification, and the two existing helpers each have a single responsibility cleanly stated in their docstrings. A future `unwrap_optional` helper is mentioned in the Low forward-looking item; defer to that trigger.
- **Duplication risk in the current file.** `getattr(rt, "of_type", None)` (`utils/typing.py:57`) and `hasattr(gql_type, "of_type")` (`utils/typing.py:28`) both interrogate the same attribute but for different semantics — the `getattr` form preserves a falsy-but-not-None `of_type` value through the `is not None` gate (Strawberry wrappers may legally carry `of_type = None` or `of_type = Any`), while the `hasattr` loop in the GraphQL helper only needs presence/absence to terminate the recursion. The two attribute-check shapes are intentional sibling design.

### Other positives

- **Test coverage walks every branch.** `tests/utils/test_typing.py:10-102` pins eight cases: `list[T]` (line 16), bare `typing.List` (line 27), bare `list` (line 38), Strawberry `of_type` (line 50), one-layer peel of `list[Inner]` inside `of_type` (line 62), full `of_type` chain (line 81), bare class passthrough (line 90), and `None` passthrough (line 102). The `IndexError`-on-bare-`typing.List` regression risk is explicitly named in the test docstring (lines 19-26).
- **Docstring-vs-implementation honesty.** Both function docstrings explicitly enumerate the `no wrapper to peel` passthrough case (`utils/typing.py:18-22` and `utils/typing.py:36-38`), and `unwrap_return_type` documents the `of_type`-first ordering rationale (`utils/typing.py:45-48`) — the "hypothetical `StrawberryList[list[T]]`" scenario is named so a future reader does not flip the branches and silently change the contract.
- **`None` passthrough is consumer-load-bearing and test-pinned.** `tests/utils/test_typing.py:93-102` ties the `None` passthrough to the optimizer's `_walk_gql_type` recursion at `optimizer/extension.py:342-347`: the post-peel `type_name is None` gate downstream relies on the passthrough holding so the recursion terminates cleanly on missing `field_obj.type` lookups. The producer/consumer citation chain is explicit in the test docstring.
- **`hasattr` loop is termination-safe.** The `while hasattr(gql_type, "of_type")` loop in `unwrap_graphql_type` (`utils/typing.py:28-30`) terminates whenever it reaches a leaf type (no `of_type` attribute). graphql-core wrapper stacks are finite by construction; `None` passes through without entering the loop.
- **Python 3.10–3.14 compatibility.** `get_origin` / `get_args` semantics for `list[T]`, `typing.List`, and bare `list` are stable across the supported range: `get_origin(list[int])` is `list`, `get_origin(typing.List)` is `list`, `get_origin(list)` is `None`. The bare-`list` branch (`utils/typing.py:63-64`) handles the third case explicitly because it would otherwise fall through to the `return rt` line and return the bare `list` class — which is not a useful inner type for a list-shaped return.

### Summary

`utils/typing.py` is the canonical home for graphql-core / Strawberry / Python-native list unwrapping. The two helpers are intentionally asymmetric in peel-depth (full vs one-layer) for sibling-consumer reasons; both contracts are docstring-pinned and test-pinned across all eight branches that production exercises today. Zero High/Medium findings; three forward-looking Lows: the `Optional[list[T]]` / Union peel is unhandled today (forward-looking until the schema-factory consumer lands and decides whether to peel here or require pre-peeled input), the bare-`list` → `Any` sentinel is test-pinned but absent from the docstring example block (next-docstring-touch trivial edit), and the module-level peel-depth asymmetry would earn a contract-table treatment only if a third unwrap helper lands here.

---

## Fix report (Worker 2)

### Files touched
- None — consolidated single-spawn no-op. 0H/0M/3L all forward-looking with Worker 1's own deferral prose.

### Tests added or updated
- None — no source change.

### Validation run
- `uv run ruff format .` — pass / no-changes (118 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed)

### Notes for Worker 3
- No shadow file consulted; the artifact's DRY analysis + per-Low prose were sufficient.
- All three Lows carry Worker 1's verbatim forward-looking trigger phrases (preserved per pattern 14):
  - **Low #1 (`Optional[list[T]]` / `list[T] | None` peel)** trigger phrase verbatim: "Defer until the schema-factory consumer's first call site lands; the consumer's return-type contract will determine whether to peel `Optional` here or to require pre-peeled input." Producer/consumer chain: `utils/__init__.py:13-14` names the upcoming schema-factory consumer; `optimizer/extension.py:344` and `:427` are the only current call sites and run against graphql-core types where Optional is encoded as `GraphQLNonNull` absence.
  - **Low #2 (bare-`list` → `Any` sentinel undocumented in docstring)** trigger phrase verbatim: "Defer until the next docstring touch on this file — single-line edit, no behavior change." Sentinel is test-pinned at `tests/utils/test_typing.py:19-38`.
  - **Low #3 (asymmetric peel-depth contract implicit at module level)** trigger phrase verbatim: "Defer until a third unwrap helper lands here; at that point a "peel-depth contract" table in the module docstring earns its keep." Trigger shared with DRY analysis's `_peel(rt, *, predicates: tuple[...])` consolidation note.
- No false-premise rejections.
- No deferred findings beyond the three explicit forward-looking Lows.

---

## Comment/docstring pass

### Files touched
- None — structurally no-op. All three Lows are forward-looking with explicit "defer until …" prose; the logic pass made zero source edits, so there is no post-fix contract to re-describe in any docstring.

### Per-finding dispositions
- **Low #1 (Optional/Union peel)**: No edit. Worker 1's prose explicitly defers to the schema-factory consumer's first call site landing. No current consumer exercises the path (the two `optimizer/extension.py` call sites run against graphql-core types). Trigger preserved verbatim in `## Notes for Worker 3` above.
- **Low #2 (bare-`list` → `Any` sentinel docstring example)**: No edit this cycle. Worker 1's prose explicitly defers the single-line edit to "the next docstring touch on this file"; this cycle has no docstring touch, so the trigger is not satisfied. Sentinel remains test-pinned at `tests/utils/test_typing.py:19-38`.
- **Low #3 (peel-depth asymmetry at module level)**: No edit. Worker 1's prose explicitly defers the contract-table treatment until "a third unwrap helper lands here" — currently only two helpers exist (`unwrap_graphql_type`, `unwrap_return_type`). Both function-level docstrings already state their peel-depth per-function; the module-level asymmetry is only implicit but not actively misleading.

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

### Notes for Worker 3
Consolidated single-spawn no-op per `worker-2.md` "Consolidated single-spawn pass" rule: all Lows are explicitly forward-looking per Worker 1's own prose, no in-cycle edit required. Pattern 18 (folder-pass with N-Lows-all-forward-looking) and pattern 11 (Worker 1's self-assessment as strongest evidence-of-no-edit) both apply. The module is also a canonical-home utils file (per DRY analysis "This module IS the cross-cutting consolidation site for graphql-core / Strawberry / native-list peeling"), reinforcing cycle 29's pattern that canonical-home utils-folder siblings with N-Lows-all-forward-looking ship as zero-line-footprint consolidated single-spawns.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cited under AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle. Three reinforcing citations beyond the baseline rule:
1. **Zero-line source footprint.** No edit to `utils/typing.py`, no test change, no consumer-visible behaviour change. There is nothing for a CHANGELOG entry to describe.
2. **Thirty-deep 0.0.7 precedent chain.** Cycles 1-29 all closed `Not warranted`; cycle 30 (this one) extends the chain. Precedent depth itself is the strongest single argument for `Not warranted` on zero-edit spawns per memory pattern (1).
3. **Canonical-home DRY self-assertion.** The DRY analysis self-asserts `utils/typing.py` as "the cross-cutting consolidation site for graphql-core / Strawberry / native-list peeling" with zero new helper-extraction opportunities. Documentation-alignment cycles against canonical-home files inherently lack release-note surface (cycle 29's `rev-utils__strings.md` and cycle 28's `rev-utils__relations.md` set the direct sibling precedent — same canonical-home framing, same zero-line footprint).

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

---

## Verification (Worker 3)

### Logic verification outcome
0H/0M; three Lows all forward-looking with Worker 1's verbatim "Defer until …" trigger phrasing preserved verbatim by Worker 2 in `### Notes for Worker 3` (lines 78-80): Low #1 "Defer until the schema-factory consumer's first call site lands; the consumer's return-type contract will determine whether to peel `Optional` here or to require pre-peeled input."; Low #2 "Defer until the next docstring touch on this file — single-line edit, no behavior change."; Low #3 "Defer until a third unwrap helper lands here; at that point a \"peel-depth contract\" table in the module docstring earns its keep." Grep-verified against artifact prose. No false-premise rejections. `git diff -- django_strawberry_framework/utils/typing.py` empty; `git status` shows no entries under `django_strawberry_framework/utils/` or `tests/utils/`. Re-read of `utils/typing.py:1-65` confirms the two helpers' asymmetric peel-depth contracts hold per the docstrings; the two `optimizer/extension.py` consumer call sites (`:344`, `:427`) operate on graphql-core types so Low #1 truly has no current consumer.

### DRY findings disposition
Two DRY observations all forward-looking. Worker 1's "Zero new helper-extraction opportunities" self-assessment and the canonical-home framing (the cross-cutting consolidation site for graphql-core / Strawberry / native-list peeling) reinforce the consolidated-no-op disposition. The `_peel(rt, *, predicates: tuple[...])` consolidation note is structurally fused with Low #3's trigger ("a third unwrap helper lands here") — single deferral gate, no double-count.

### Temp test verification
- None used; the artifact's per-Low prose and existing test pins (`tests/utils/test_typing.py:10-102` walking all eight branches) were sufficient.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — empty source diff, three Lows' verbatim trigger phrasing preserved, empty `git diff -- CHANGELOG.md` matching `Not warranted` three-leg framing (AGENTS.md:21 + plan silence + thirty-deep 0.0.7 precedent chain), `uv run ruff format --check .` reports 118 files already formatted, `uv run ruff check .` reports All checks passed.

---

## Iteration log

(none — single-spawn consolidated pass)
