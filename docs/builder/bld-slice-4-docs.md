# Build: Slice 4 — Docs

Spec reference: `docs/spec-020-scalar_map_helper-0_0_7.md` (lines 52-58 for slice sub-checks; lines 511-574 for Doc updates; DoD items 9, 9a, 10, 11, 12, 13, 14)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- Existing patterns reused: the `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])` shape established by Slice 3 in `examples/fakeshop/config/schema.py` (Worker 1's Slice 3 final-verification memory line: "the canonical post-migration consumer contract"). Every doc-side example aligns to that kwarg order: `query=`, `config=`, `extensions=`. Slice 2 already migrated 10 sites in `tests/types/test_converters.py` and 2 integration tests in `tests/test_scalars.py` to the same shape; Slice 4 repeats the pattern on five doc surfaces (`docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, plus the CSV).
- New helpers justified: none. Slice 4 ships zero Python source. The repetition of `config=strawberry_config()` across consumer-facing docs IS the demonstration consumers must read; Decision 2 in the spec already rejected a `dst.Schema(...)` wrapper to consolidate it. No new helper warranted.
- Duplication risk avoided: the only DRY hazard is per-doc drift in (a) kwarg order, (b) whether the helper is on its own line vs inline, (c) the exact GLOSSARY-entry body. Steps 1-4 below pin the verbatim spec body for the GLOSSARY entry and the kwarg order Slice 3 already shipped to fakeshop.
- Helper skip reason: Slice 4 touches only Markdown / CSV. No Python logic added, no `.py` files modified. Per `docs/builder/BUILD.md` "When to run the helper during build", Worker 1 runs the helper only when the plan adds logic to a Python file >=150 source lines OR any file under `optimizer/` / `types/`. None of those apply here. Helper skipped; recorded for the cross-slice integration pass.
- Pre-Slice-4 CSV term count: `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` -> `OK: 16 terms — all have glossary entries and at least one spec link.` Post-Slice-4 expected: `OK: 17 terms` (per spec DoD item 9a). The new row this slice adds is for the term `strawberry_config`; the script run post-Slice-4 confirms the row count rose by exactly one.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints. Verify against the current source before editing.

1. `docs/README.md` — three code blocks updated, no surrounding prose change.
   1. **Quick start code block (anchor: line 16 `## Quick start`; code block at lines 18-49).** Edit two lines:
      - Widen the import line `from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types` (current line 20) to `from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types, strawberry_config`.
      - Rewrite the multi-line `strawberry.Schema(...)` call (lines 45-48) from:
        ```
        schema = strawberry.Schema(
            query=Query,
            extensions=[DjangoOptimizerExtension()],
        )
        ```
        to:
        ```
        schema = strawberry.Schema(
            query=Query,
            config=strawberry_config(),
            extensions=[DjangoOptimizerExtension()],
        )
        ```
        Worker 2 discretion: whether to keep the multi-line shape (recommended; matches the existing layout and the GLOSSARY entry body) or collapse to single-line (NOT recommended — would break visual parity with the Schema setup boundary section). The kwarg order is pinned: `query=`, `config=`, `extensions=`.
   2. **Relay Node example (anchor: `### Relay Node` at line 53; code block at lines 57-72).** The current Relay Node code block does NOT construct a `strawberry.Schema(...)` — it stops at `finalize_django_types()`. **NO Schema-construction edit needed here.** This is a deviation from the Slice 4 sub-bullet wording at spec line 53 ("Quick start + Relay Node + Schema setup boundary"); per Slice 4 sub-bullet at spec line 53 the Relay Node block IS named, but the current code block does not contain a Schema-construction line. Worker 1 final-verification (this same planner) will decide whether to tick the Relay Node sub-check based on this anchor reality, or to record a one-line deferral. The likely outcome: tick the sub-check with the note that the Relay Node block currently has no Schema-construction line to update. No edit by Worker 2 in this slice for the Relay Node example.
   3. **Schema setup boundary (anchor: `## Schema setup boundary` at line 125; two code blocks at lines 131-138 and 142-145).** Both `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` lines are rewritten identically to `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. The "Recommended" / "Right order" code block at lines 131-138 (line 137) AND the "Wrong order" anti-example at lines 142-145 (line 143) both gain `config=strawberry_config()` between `query=` and `extensions=`. The single-line shape stays single-line in both blocks; widening to a multi-line call would change the visual contrast that the Wrong-order anti-example exists to illustrate (the only difference between Recommended and Wrong-order remains the placement of `finalize_django_types()` relative to `strawberry.Schema(...)`). Worker 2 also widens the "Recommended" import block's `from django_strawberry_framework import finalize_django_types` line (current line 132) to `from django_strawberry_framework import finalize_django_types, strawberry_config` — the Wrong-order example does not show an import block, so no analog import edit is needed there.

2. `docs/GLOSSARY.md` — four edits to ONE file.
   1. **Update `## BigInt scalar` entry body (anchor: line 171 `## BigInt scalar`; body at lines 173-176).** Locate the strict-serializer sentence ending `Part of [Specialized scalar conversions](#specialized-scalar-conversions).` at the end of line 175. After that sentence, append a NEW paragraph (verbatim per spec line 556):

      > Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol. The migration applies to any schema that resolves to `BigInt` — including [`DjangoType`](#djangotype) schemas whose fields are backed by `BigIntegerField` or `PositiveBigIntegerField` (resolved to `BigInt` by the [`Specialized scalar conversions`](#specialized-scalar-conversions) converter table) even when the consumer never imports or annotates `BigInt` directly.

      Preserve the existing `**See also:**` line at line 177 unchanged.

   2. **Add a new top-level entry `## strawberry_config` (between `## Specialized scalar conversions` at line 958 and `## Strictness mode` at line 972).** Insert the new section immediately AFTER the end of the `## Specialized scalar conversions` entry (the `**See also:**` line of that entry) and BEFORE the `## Strictness mode` heading. Body verbatim per spec lines 517-553:

      ```
      ## strawberry_config

      **Status:** shipped ([Unreleased]).

      Factory returning a [`StrawberryConfig`](https://strawberry.rocks) pre-populated with the package's `scalar_map` — the registration path consumers use to bind package-defined scalars (today: [`BigInt`](#bigint-scalar); next: [`Upload`](#upload-scalar) in `0.0.11`) into their `strawberry.Schema(...)` call.

      ```python
      from django_strawberry_framework import strawberry_config

      schema = strawberry.Schema(
          query=Query,
          config=strawberry_config(),
          extensions=[DjangoOptimizerExtension()],
      )
      ```

      Consumers composing custom scalars on top pass them via `extra_scalar_map=`:

      ```python
      MyULID = NewType("MyULID", str)
      schema = strawberry.Schema(
          query=Query,
          config=strawberry_config(extra_scalar_map={MyULID: my_ulid_definition}),
      )
      ```

      Consumers tuning non-scalar `StrawberryConfig` fields (`auto_camel_case`, `relay_max_results`, `name_converter`, etc.) pass those keyword arguments directly — the helper forwards every kwarg other than `extra_scalar_map=` to upstream `StrawberryConfig(...)`:

      ```python
      schema = strawberry.Schema(
          query=Query,
          config=strawberry_config(auto_camel_case=False, relay_max_results=200),
      )
      ```

      The keyword-only `extra_scalar_map=` and the `**config_kwargs` passthrough compose: `strawberry_config(extra_scalar_map={MyULID: my_ulid_definition}, relay_max_results=200)` is supported. The single field the helper refuses to forward is `scalar_map=` (ownership goes through `extra_scalar_map=`); passing `scalar_map=` raises `ValueError`. Collision with a package-defined scalar in `extra_scalar_map` also raises `ValueError`; register the consumer scalar under a different `NewType` / class to keep both. Each call returns a fresh `StrawberryConfig` instance with a fresh `scalar_map` dict; mutations on the returned object do not leak across calls.

      **See also:** [`BigInt scalar`](#bigint-scalar) · [`Upload scalar`](#upload-scalar) · [`Specialized scalar conversions`](#specialized-scalar-conversions).
      ```

      Worker 2 discretion: the fenced-code blocks INSIDE the new entry use triple-backtick `python` fences; the entry as a whole is a standard Markdown section. If a nested-fence rendering conflict surfaces (the spec source uses blockquote-styled `>` indentation around the new entry body to escape the outer code-block fences; the GLOSSARY entries are NOT blockquoted), Worker 2 may flatten the blockquote markers from the spec's pinned body so the GLOSSARY entry matches the visual shape of the surrounding entries — i.e., this entry's structure should mirror neighbor entries (`## Specialized scalar conversions`, `## Strictness mode`) which are NOT blockquote-wrapped. Triple-backtick `python` fences are the right inner-fence shape; no four-backtick outer fence is needed because the new entry is not itself inside a code block.

   3. **Update the Public exports bulleted re-exports list (anchor: line 22 `## Public exports`; bulleted list at lines 26-33).** After the existing line `- [`finalize_django_types`](#finalize_django_types) — synchronization point that resolves pending relations and applies `strawberry.type` decoration.` (line 31), insert a new bullet for `strawberry_config`. Worker 2 discretion on exact wording; suggested:
      ```
      - [`strawberry_config`](#strawberry_config) — factory returning a `StrawberryConfig` pre-populated with the package's `scalar_map`.
      ```
      Pin: the bullet lands AFTER `finalize_django_types` to mirror the `__all__` ordering (Python ASCII case-sensitive sort: `f` < `s`); Slice 1 already shipped this ordering in `django_strawberry_framework/__init__.py`'s `__all__`. The existing alphabetical block (BigInt, DjangoListField, DjangoType, DjangoOptimizerExtension, OptimizerHint, finalize_django_types) is not strictly alphabetical (DjangoType / DjangoOptimizerExtension are out of strict ASCII order); Worker 2 keeps the new bullet in the position immediately AFTER `finalize_django_types` to match `__all__`'s ordering rather than re-alphabetizing the pre-existing block.

   4. **Update the alphabetical Index table (anchor: line 41 `## Index`; table rows at lines 45-115).** Insert a new row `| [strawberry_config](#strawberry_config) | shipped ([Unreleased]) |` in alphabetical position. Pin: the row lands immediately AFTER the `Specialized scalar conversions` row (line 111) and BEFORE the `Strictness mode` row (line 112) — `strawberry_config` (`s-t-r-a-w-b`) sorts between `Specialized scalar conversions` (`S-p-e`) and `Strictness mode` (`S-t-r-i`) in case-insensitive lexical order. Worker 2 visually verifies the exact alphabetical position before inserting (`Specialized scalar conversions` -> `strawberry_config` -> `Strictness mode`). The status column is the literal string `shipped ([Unreleased])` per spec line 515; the placeholder gets promoted by the maintainer at the next version cut.

3. `GOAL.md` — rewrite the astronomy `schema.py` block. **NO edits to per-stack diff blocks** in the Migration shape section.
   1. **Astronomy `schema.py` block (anchor: `### `schema.py`` at line 79; code block at lines 83-155; sole `strawberry.Schema(...)` call at line 154).** Two edits:
      - Widen the import group at lines 87-94 (`from django_strawberry_framework import (...)`) to add `strawberry_config` to the imports list. Worker 2 discretion: alphabetical insertion within the parenthesized list places `strawberry_config` after `finalize_django_types` (current line 93), so the post-edit list reads (in order): `DjangoType, DjangoNodeField, DjangoConnection, DjangoConnectionField, apply_cascade_permissions, finalize_django_types, strawberry_config`. The existing list is NOT strict-alphabetical (it groups by conceptual cluster); Worker 2 keeps the new symbol in the position immediately after `finalize_django_types` to match the `__all__` ordering used in `django_strawberry_framework/__init__.py` and the GLOSSARY Public exports bullet.
      - Rewrite the `schema = strawberry.Schema(query=Query)` line (line 154) to `schema = strawberry.Schema(query=Query, config=strawberry_config())`. The current GOAL showcase does NOT pass `extensions=` (it omits `DjangoOptimizerExtension`), so the post-edit single-line call carries only `query=` and `config=`. Worker 2 does NOT add `extensions=[DjangoOptimizerExtension()]` because that would be a scope creep beyond Slice 4; the spec line 565 explicitly pins "add `strawberry_config` to the imports list and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call. No other change."
   2. **Migration shape section (anchor: `## Migration shape` at line 400; per-stack diff blocks at lines 404-477).** **NO EDITS.** Per spec lines 565-566: "The per-stack diff blocks inside the [Migration shape](../GOAL.md#migration-shape) section (`Coming from graphene-django` / `Coming from strawberry-graphql-django` / `Coming from DRF + django-filter`) are NOT edited — those blocks intentionally show minimal `Meta`-shape diffs and adding a `config=` line would distract from the per-stack migration point."

4. `TODAY.md` — rewrite the "What to put in `examples/fakeshop/config/schema.py` today" block.
   1. **Block anchor: `## What to put in `examples/fakeshop/config/schema.py` today` at line 119; code block at lines 121-141.** Two edits:
      - Widen the import line `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types` (current line 126) to `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config`.
      - Rewrite the multi-line `strawberry.Schema(...)` call (lines 137-140) from:
        ```
        schema = strawberry.Schema(
            query=Query,
            extensions=[DjangoOptimizerExtension()],
        )
        ```
        to:
        ```
        schema = strawberry.Schema(
            query=Query,
            config=strawberry_config(),
            extensions=[DjangoOptimizerExtension()],
        )
        ```
        This mirrors the `docs/README.md` Quick start update and Slice 3's `examples/fakeshop/config/schema.py` change. No other prose change.
   2. **`## What's in `examples/fakeshop/apps/products/schema.py` today` (anchor at line 26).** **NO EDIT** per spec line 570 — the products schema block does not construct a project-level schema.

5. `docs/TREE.md` — **NO EDIT** per spec DoD item 13. The current entry at lines 201 and 246 reads `├── scalars.py               # BigInt public scalar (NewType-based; Strawberry deprecation suppressed at definition site)`. This wording still describes the file's role accurately enough for the tree-summary purpose (the file IS the BigInt public scalar). The "Strawberry deprecation suppressed at definition site" phrase is now stale (Slice 1 removed the suppression block; the no-warning overload replaced it) — but spec DoD item 13 explicitly says NO edit to `docs/TREE.md` in this card. Worker 2 does NOT edit `docs/TREE.md`. If the stale wording needs updating, it's a separate follow-up card outside this build's scope (flagged for the integration pass / `bld-final.md` Deferred work catalog).

6. `docs/spec-020-scalar_map_helper-0_0_7-terms.csv` — add one row in alphabetical position; do NOT edit the spec body.
   1. **CSV update (anchor: header line 1 `term,anchor,notes`; current 16 rows at lines 2-17).** Insert the new row `strawberry_config,strawberry_config,The factory function this card introduces; entry created in Slice 4.` in alphabetical position. Pin: the CSV is NOT strictly alphabetical (line 2 starts `BigInt scalar`; line 14 is `FilterSet`; line 15 is `OrderSet`); Worker 2 inserts the new row at a position that keeps the CSV monotonically alphabetical for the surrounding rows OR appends at the end if the existing file is not strictly sorted. The script `scripts/check_spec_glossary.py` checks term coverage / anchor existence, not alphabetical ordering, so the exact insertion position is Worker 2 discretion. Suggested: append at the end (line 18) — keeps the diff small and the script doesn't care.
   2. **Post-edit verification (Worker 2 SHOULD run, but the final-spec-edit is reserved for Worker 1):** `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` should report `OK: 17 terms` (up from the pre-Slice-4 count of 16). Worker 2 records the script output in `### Validation run` of the build report. If the count is anything other than 17, Worker 2 stops and surfaces the gap under `### Notes for Worker 1 (spec reconciliation)`.
   3. **Spec body edit is RESERVED for Worker 1 final-verification.** Worker 2 does NOT edit `docs/spec-020-scalar_map_helper-0_0_7.md`. Specifically: the `## Key glossary references` note block at spec lines 13-14 (the "REMOVE WHEN SLICE 4 LANDS" callout about CSV omission of `strawberry_config`) becomes stale the moment Worker 2 lands the CSV row in step 6.1; per DoD item 9a the callout must be removed "in the same commit". Per `docs/builder/BUILD.md` "Spec reconciliation" and `worker-1.md` "Spec custody", only Worker 1 may edit the active spec. The Slice-4 final-verification pass (Worker 1, after Worker 3 accepts the slice) is where the spec-body edit happens, recorded under `### Spec changes made (Worker 1 only)`.

7. `README.md` (repo root) — **NO EDIT** per spec DoD item 14. The repo-root README is the project pitch / migration context / doc map and does not carry a Schema-construction code block; the `docs/README.md` Quick start is the canonical schema-setup walkthrough. Worker 2 does NOT edit `README.md`.

8. Formatter run: `uv run ruff format .` and `uv run ruff check --fix .`. Since Slice 4 touches only Markdown and CSV, neither command should report any change; Worker 2 records both as `pass` in `### Validation run` and confirms `git status --short` shows only the Slice-4-intended files modified (`docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, `docs/spec-020-scalar_map_helper-0_0_7-terms.csv`).

### Test additions / updates

None. Slice 4 ships zero new tests and modifies zero existing tests. All factory contract / round-trip integration test coverage already landed in Slice 2 (`tests/test_scalars.py` + `tests/base/test_init.py` + `tests/types/test_converters.py`). The doc updates are pure prose / code-block changes; no behavior change to assert.

Worker 3 may run `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` during review to independently verify the post-Slice-4 term count is 17. No other test-side work for Worker 3.

### Implementation discretion items

- The exact alphabetical position of the new GLOSSARY entry between `## Specialized scalar conversions` and `## Strictness mode`. The spec pins "between" (line 516); Worker 2 inserts the new section immediately after the closing `**See also:**` line of `## Specialized scalar conversions` and before the `## Strictness mode` heading. Whitespace and any inter-section dividers (e.g., `---`) follow the existing file convention — currently the GLOSSARY entries are separated by a single blank line, NOT a horizontal rule.
- The exact CSV row position. The existing CSV is not strictly sorted (BigInt scalar comes before Specialized scalar conversions; FilterSet / OrderSet / AggregateSet / FieldSet are clustered at the end). Worker 2 appends the new row at the end (line 18) for the minimal-diff approach, OR inserts in alphabetical position if Worker 2 prefers stricter ordering. The script does not care about row order.
- Whether to keep multi-line vs single-line `strawberry.Schema(...)` calls in the doc examples. Pin: docs/README.md Quick start, TODAY.md fakeshop block, and GLOSSARY entry's first code block keep the multi-line shape (matches the existing visual layout and Slice 3's fakeshop schema). The Schema setup boundary "Recommended" and "Wrong order" blocks keep the single-line shape (preserves the visual contrast that the anti-example exists to illustrate). GOAL.md astronomy showcase keeps the single-line shape (current line 154 is single-line; the spec line 565 does not authorize changing the layout).
- Inner-code-block fence shape in the new GLOSSARY `## strawberry_config` entry: triple-backtick `python`. The spec's body pinning at lines 522-549 uses blockquote (`>`) wrappers because the spec itself is fenced; the GLOSSARY entries are NOT blockquoted, so Worker 2 strips the leading `> ` from each line when transcribing the body. The inner-fence shape stays as triple-backtick.
- Worker 2 import-line widening style: alphabetical-within-cluster vs append-at-end. Pin: the existing `__init__.py` `__all__` ordering (set by Slice 1) puts `strawberry_config` at the end of the tuple, after `finalize_django_types`. The GLOSSARY Public exports bullet, the GOAL.md import list, the docs/README.md Quick start import line, and the TODAY.md fakeshop block import line all mirror that ordering by placing `strawberry_config` immediately after `finalize_django_types` (or at the end of the import list, whichever matches the existing per-doc convention).

### Notes for Worker 1 (Slice-4 final-verification spec edit reservation)

The Slice-4 final-verification pass (this Worker 1) MUST perform the following spec edit AFTER Worker 3 accepts the slice and BEFORE setting `Status: final-accepted`:

1. **Remove the Key-glossary-references CSV-completeness callout from `docs/spec-020-scalar_map_helper-0_0_7.md` lines 13-14** (the `> **Note (terms CSV completeness — REMOVE WHEN SLICE 4 LANDS):** ...` blockquote). Per DoD item 9a: "the [Key glossary references](#key-glossary-references) CSV-completeness callout is removed in the same commit". The callout becomes stale the moment Worker 2 lands the CSV row in implementation step 6.1; removing it keeps the spec body accurate as a snapshot of the post-Slice-4 state.
2. **Re-run `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md`** and confirm the output is `OK: 17 terms — all have glossary entries and at least one spec link.` (up from the pre-Slice-4 `OK: 16 terms`). Record the post-edit count in the final-verification `### Summary` section.
3. **Record the spec edit under `### Spec changes made (Worker 1 only)`** in this artifact with: spec path (`docs/spec-020-scalar_map_helper-0_0_7.md`), line range (13-14), slice (4), one-line reason ("Remove stale CSV-completeness callout per DoD item 9a now that the Slice-4 CSV row has landed and the GLOSSARY entry exists").
4. Worker 2 may NOT make this spec edit; per `worker-2.md`, Worker 2 surfaces spec issues under `### Notes for Worker 1 (spec reconciliation)` and does not edit the spec. Worker 2's role for the CSV/spec relationship is limited to step 6.1 (add the CSV row) and step 6.2 (run the verification script and record the count).

### Spec slice checklist (verbatim)

Copied verbatim from `docs/spec-020-scalar_map_helper-0_0_7.md` lines 52-58 (the Slice 4 nested sub-bullets), preserving exact bullet text, nested formatting, and inline citations. Worker 1 ticks each `- [x]` during final verification as the contract lands.

- [x] Slice 4: Docs
  - [x] [`docs/README.md`](README.md): rewrite the [Quick start](README.md#quick-start) code block (the `strawberry.Schema(...)` example) to add `config=strawberry_config()` to the constructor call, with `strawberry_config` added to the imports line. Also rewrite the [Relay Node](README.md#relay-node) example (which constructs a schema with `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` near the end of its block) the same way. The [Schema setup boundary](README.md#schema-setup-boundary) section carries TWO `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` examples — the "Wrong order" anti-example and the "Right order" example — and both lines change identically (`config=strawberry_config()` added to each); the only contrast between the two examples after the rewrite remains the placement of `finalize_django_types()` relative to `strawberry.Schema(...)`, which is the pitfall the anti-example is meant to illustrate.
  - [x] [`docs/GLOSSARY.md`](GLOSSARY.md): update the [`BigInt scalar`](GLOSSARY.md#bigint-scalar) entry body to reflect the new construction pattern — replace the sentence "Strict serializer rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`" with the same sentence preserved, AND add a new paragraph: "Consumers register `BigInt` via the `strawberry_config()` factory (new in [Unreleased] — see [`strawberry_config`](#strawberry_config)) on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`. Direct `BigInt` annotations (`category: BigInt`, `@strawberry.field def big_id(self) -> BigInt: ...`) continue to work unchanged at the schema-declaration site; the registration path changes, not the symbol." Add a new top-level glossary entry for `strawberry_config` between the [`Specialized scalar conversions`](GLOSSARY.md#specialized-scalar-conversions) entry and the [Strictness mode](GLOSSARY.md#strictness-mode) entry; new entry body per [Doc updates](#doc-updates). Update the [Public exports](GLOSSARY.md#public-exports) bulleted re-exports list to add `strawberry_config` after `finalize_django_types` (matching the `__all__` ordering — Python ASCII sort puts `strawberry_config` at the end of the lowercase block). Update the alphabetical [Index](GLOSSARY.md#index) table with a new row for `strawberry_config` in alphabetical position and a status of `shipped ([Unreleased])` (Risks calls out the placeholder-vs-real version posture; this is the same posture spec-019 uses post-cut).
  - [x] [`GOAL.md`](../GOAL.md): rewrite the [`schema.py`](../GOAL.md#schemapy) example block (the astronomy showcase) — add `strawberry_config` to the imports list and `config=strawberry_config()` to the showcase's terminal `strawberry.Schema(...)` call (anchored at [`GOAL.md #"strawberry.Schema(query=Query"`](../GOAL.md)). No other change to the showcase body; the per-stack diff blocks inside the [Migration shape](../GOAL.md#migration-shape) section (`Coming from graphene-django` / `Coming from strawberry-graphql-django` / `Coming from DRF + django-filter`) are NOT edited because the blocks intentionally show minimal `Meta`-shape diffs and adding the helper would distract from the per-stack migration point. The GOAL `schema.py` is the one place where a consumer's "right shape" example lives end-to-end and should reflect the post-migration pattern.
  - [x] [`TODAY.md`](../TODAY.md): rewrite the [What to put in `examples/fakeshop/config/schema.py` today](../TODAY.md#what-to-put-in-examplesfakeshopconfigschemapy-today) block to add `strawberry_config()` to the imports and the `strawberry.Schema(...)` call, mirroring the [`docs/README.md`](README.md) Quick start update. No other change; the [What's in `examples/fakeshop/apps/products/schema.py` today](../TODAY.md#whats-in-examplesfakeshopappsproductsschemapy-today) section already does not construct a project-level schema, so no edit is needed there.
  - [x] [`docs/TREE.md`](TREE.md): no edit. The helper is added to the existing [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py) module per [Decision 2](#decision-2--helper-api-shape-and-module-location); no new file under `django_strawberry_framework/` and no new test file under `tests/`. The current-on-disk-layout enumeration in `docs/TREE.md` already mentions `scalars.py` (at [`docs/TREE.md #"scalars.py"`](TREE.md), `"scalars.py # \`BigInt\` public scalar"`); the entry stays as-is since the file's role is unchanged.
  - [x] [`docs/spec-020-scalar_map_helper-0_0_7-terms.csv`](spec-020-scalar_map_helper-0_0_7-terms.csv): once the new `## strawberry_config` entry is in place inside [`docs/GLOSSARY.md`](GLOSSARY.md) (the bullet above), add a row `strawberry_config,strawberry_config,The factory function this card introduces; entry created in Slice 4.` to the CSV in alphabetical position. Then re-run [`uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md`](../scripts/check_spec_glossary.py) and confirm the term count increases by one (`OK: 17 terms`). The CSV completeness callout in [Key glossary references](#key-glossary-references) becomes stale after this bullet lands; this same slice removes that callout in the same commit. `StrawberryConfig` (upstream Strawberry) stays out of the CSV — it is not a package glossary term.

---

## Build report (Worker 2)

### Files touched

- `docs/README.md` — three edits:
  1. Quick start code block: widened `from django_strawberry_framework import ...` to include `strawberry_config`; rewrote the multi-line `strawberry.Schema(...)` call to add `config=strawberry_config(),` between `query=Query,` and `extensions=[DjangoOptimizerExtension()],`.
  2. Schema setup boundary "Recommended" code block (single-line `strawberry.Schema(...)`): added `config=strawberry_config()` between `query=` and `extensions=`; widened the `from django_strawberry_framework import finalize_django_types` import to `finalize_django_types, strawberry_config`.
  3. Schema setup boundary "Wrong order" anti-example (single-line `strawberry.Schema(...)`): added `config=strawberry_config()` between `query=` and `extensions=` so the only post-edit contrast remains the `finalize_django_types()` placement.
  4. Relay Node example: NO edit. The current Relay Node code block (lines 57-72) does NOT construct a `strawberry.Schema(...)` — it stops at `finalize_django_types()`. Recorded under `### Notes for Worker 1 (spec reconciliation)` below; no fabricated Schema call inserted (Worker 1 planner already flagged this at planning time).
- `docs/GLOSSARY.md` — four edits:
  1. `## BigInt scalar` entry body: appended the verbatim spec-line-556 paragraph (consumer-migration registration paragraph) immediately after the existing strict-serializer / `Part of [Specialized scalar conversions]` sentence, before the existing `**See also:**` line.
  2. New `## strawberry_config` entry inserted between `## Specialized scalar conversions` and `## Strictness mode`, body verbatim per spec lines 517-553 with the spec's blockquote (`>`) wrappers stripped (the surrounding GLOSSARY entries are not blockquoted). Inner fenced-code blocks use triple-backtick `python`.
  3. Public exports bulleted list (line ~32): inserted new bullet `- [`strawberry_config`](#strawberry_config) — factory returning a `StrawberryConfig` pre-populated with the package's `scalar_map`.` immediately after the `finalize_django_types` bullet, mirroring the Slice 1 `__all__` ordering.
  4. Alphabetical Index table: inserted new row `| [strawberry_config](#strawberry_config) | shipped ([Unreleased]) |` between the `Specialized scalar conversions` row and the `Strictness mode` row.
- `GOAL.md` — astronomy `schema.py` showcase block: added `strawberry_config,` to the existing parenthesized `from django_strawberry_framework import (...)` import group after `finalize_django_types,`; rewrote the single-line `schema = strawberry.Schema(query=Query)` (line 154) to `schema = strawberry.Schema(query=Query, config=strawberry_config())`. Migration-shape per-stack diff blocks left untouched per spec lines 565-566.
- `TODAY.md` — "What to put in `examples/fakeshop/config/schema.py` today" block: widened `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types` to `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types, strawberry_config`; rewrote the multi-line `strawberry.Schema(...)` call to add `config=strawberry_config(),` between `query=Query,` and `extensions=[DjangoOptimizerExtension()],`. The "What's in `examples/fakeshop/apps/products/schema.py` today" section was not modified (per spec line 570).
- `docs/spec-020-scalar_map_helper-0_0_7-terms.csv` — appended one new row at the end: `strawberry_config,strawberry_config,The factory function this card introduces; entry created in Slice 4.`. Append-at-end approach per the Implementation discretion item (existing CSV is not strictly sorted; script does not care about row order).

### Tests added or updated

None. Slice 4 ships zero new tests and modifies zero existing tests per the plan's "Test additions / updates" section. All factory-contract / round-trip integration coverage already landed in Slice 2.

### Validation run

- `uv run ruff format .` — pass (`118 files left unchanged`). No churn on the Slice 4 Markdown / CSV surface.
- `uv run ruff check --fix .` — pass (`All checks passed!`). No fixups applied.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` — `OK: 17 terms — all have glossary entries and at least one spec link.` (up from the pre-Slice-4 count of 16 per the Plan's DRY analysis note).
- `git status --short` (post-ruff) lists the following modified files:
  - `GOAL.md` — slice-intended (Step 3, astronomy `schema.py`).
  - `TODAY.md` — slice-intended (Step 4, fakeshop `config/schema.py` block).
  - `django_strawberry_framework/__init__.py` — NOT this slice; landed in Slice 1.
  - `django_strawberry_framework/scalars.py` — NOT this slice; landed in Slice 1.
  - `docs/GLOSSARY.md` — slice-intended (Step 2, four GLOSSARY edits).
  - `docs/README.md` — slice-intended (Step 1, Quick start + Schema setup boundary).
  - `docs/spec-020-scalar_map_helper-0_0_7-terms.csv` — slice-intended (Step 6, CSV row append).
  - `docs/spec-020-scalar_map_helper-0_0_7.md` — NOT this slice; the 1-line diff is Worker 1's pre-Slice-1 status-header update (`Status: in flight — Slices 1-3 shipped …`). Worker 2 did NOT touch the spec body per the plan's `### Notes for Worker 1` reservation; the Key-glossary-references callout removal at spec lines 13-14 is reserved for Worker 1's Slice-4 final-verification pass.
  - `examples/fakeshop/config/schema.py` — NOT this slice; landed in Slice 3.
  - `tests/base/test_init.py` — NOT this slice; landed in Slice 2.
  - `tests/test_scalars.py` — NOT this slice; landed in Slice 2.
  - `tests/types/test_converters.py` — NOT this slice; landed in Slice 2.
  - Untracked: the build-plan and four prior-slice / current-slice `bld-*.md` artifacts.
- No focused pytest runs (the artifact contains no instruction to run pytest; Slice 4 is docs-only). Per `worker-2.md` rule 11 and `AGENTS.md` "Do not run pytest after edits", pytest was not invoked.

### Implementation notes

- Spec body copy approach: copied the spec-pinned `## strawberry_config` body verbatim per spec lines 517-553 (every paragraph break, every fenced-code block, every link preserved). The plan's "Worker 2 discretion" bullet authorized stripping the blockquote (`>`) markers used in the spec source so the GLOSSARY entry matches the visual shape of `## Specialized scalar conversions` and `## Strictness mode` (neither neighbor is blockquoted). Inner fenced-code blocks use triple-backtick `python` (no four-backtick outer-fence collision because the GLOSSARY entry is not itself wrapped in a code block).
- Spec body for the `## BigInt scalar` paragraph addition: copied verbatim per spec line 556 (single paragraph appended between the existing strict-serializer sentence and the existing `**See also:**` line).
- Schema setup boundary kept single-line: the "Recommended" and "Wrong order" code blocks in `docs/README.md` already used single-line `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` calls; widening to multi-line would have changed the visual-contrast that the Wrong-order anti-example exists to illustrate. Kept single-line by adding `config=strawberry_config()` inline between `query=` and `extensions=`. Quick start and TODAY blocks stayed multi-line because that was their pre-edit shape.
- CSV row positioning: appended at the end (line 18) rather than alphabetically-positioned. The existing CSV is not strictly alphabetical (`BigInt scalar` precedes `Specialized scalar conversions`; `FilterSet` / `OrderSet` / `AggregateSet` / `FieldSet` cluster at the end), and `scripts/check_spec_glossary.py` does not check ordering. End-append is the minimal-diff approach the plan's discretion item authorized.
- GOAL.md import-list insertion position: added `strawberry_config,` as the LAST item of the parenthesized `from django_strawberry_framework import (...)` group (after `finalize_django_types,`), matching the `__all__` ordering Slice 1 shipped in `django_strawberry_framework/__init__.py`. The existing list groups by conceptual cluster rather than strict alphabetical order; Worker 1's plan pinned "immediately after `finalize_django_types`" for this reason.

### Notes for Worker 3

- Helper not run (Slice 4 ships zero Python source); the plan recorded this skip with reason under `### DRY analysis`.
- Verbatim copy from spec: the `## strawberry_config` GLOSSARY entry body and the `## BigInt scalar` appended paragraph are pinned by spec lines 517-553 and 556 respectively. Worker 3 can `diff`-verify by stripping the blockquote `>` markers from the spec source and comparing against the GLOSSARY post-edit body.
- `scripts/check_spec_glossary.py` post-Slice-4 output is `OK: 17 terms`. Worker 3 may re-run independently to confirm.
- Slice 4 `Status:` transitions to `built` after these notes; the `Relay Node` Schema-construction sub-bullet flagged in Worker 1's plan is recorded under `### Notes for Worker 1 (spec reconciliation)` below — that sub-check has no implementable contract because the live anchor has no Schema-construction line; Worker 1 final-verification disposes per Worker 1's plan note.

### Notes for Worker 1 (spec reconciliation)

1. **Relay Node Schema-construction sub-bullet disposition (spec line 53; plan implementation step 1.2):** the `docs/README.md` `### Relay Node` code block at lines 57-72 does NOT contain a `strawberry.Schema(...)` constructor call — it ends at `finalize_django_types()`. The spec slice sub-bullet at spec line 53 names the Relay Node example as one of three Schema-construction sites that should add `config=strawberry_config()`, but the live anchor has no Schema-construction line to update. Worker 2 did NOT fabricate a Schema line (per task instructions and per Worker 1's plan note). Final-verification disposition (Worker 1's call): either (a) tick the Relay Node sub-check with a one-line note that the live anchor carries no Schema-construction line, or (b) make a spec edit reconciling spec line 53 against the live anchor. Worker 1's plan (this same planner) recorded the likely outcome as option (a).
2. **Spec body Key-glossary-references callout removal (INTENTIONALLY NOT TOUCHED by Worker 2):** spec lines 13-14 (the `> **Note (terms CSV completeness — REMOVE WHEN SLICE 4 LANDS):** ...` blockquote) became stale the moment the CSV row landed in Slice 4 implementation step 6.1, but the spec-body edit is reserved for Worker 1's Slice-4 final-verification per the plan's `### Notes for Worker 1 (Slice-4 final-verification spec edit reservation)` and per `worker-2.md` "Worker 2 must not edit the active spec". Worker 1 final-verification owns the removal of those two lines (recorded under `### Spec changes made (Worker 1 only)`) and the post-removal `scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` re-run (expect `OK: 17 terms` again post-removal, because the term is in both the spec body and the glossary).
3. **Stale wording in `docs/TREE.md` (per plan implementation step 5):** the on-disk-layout entry for `scalars.py` at `docs/TREE.md` line ~202 / ~246 reads `# BigInt public scalar (NewType-based; Strawberry deprecation suppressed at definition site)`. The "Strawberry deprecation suppressed at definition site" phrase is now factually stale (Slice 1 removed the suppression block; the no-warning overload replaced it). Spec DoD item 13 explicitly forbids `docs/TREE.md` edits in this card, so Worker 2 did not touch it. Flagged here for the cross-slice integration pass / `bld-final.md` Deferred work catalog; the next spec author may opt to refresh that line in a follow-up.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- None within Slice 4's own diff: the slice adds zero Python, zero shared keys, zero parallel data flows. The five doc-side touch points (Quick start, Schema setup boundary x2, GLOSSARY entry's first code block, GOAL astronomy `schema.py`, TODAY fakeshop block) all repeat the canonical `query= / config=strawberry_config() / extensions=` kwarg order Slice 3 pinned. That repetition is the demonstration consumers must read, not duplication to consolidate. Decision 2 in the spec already rejected a `dst.Schema(...)` wrapper; the doc repetition stays.
- Worker 2's discretion-driven kwarg-order pin (`query=`, `config=`, `extensions=`) is consistent across every site I checked; no per-doc drift.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows exactly the Slice 1 carry-forward: `from .scalars import BigInt, strawberry_config` and `"strawberry_config",` appended to `__all__`. Slice 4 itself adds zero changes to `__init__.py`. The carry-forward was already accepted at Slice 1 final-verification. No new public exports introduced by this slice.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Walked the full Slice-4 documentation surface against the spec's "Doc updates" section (lines 511-574) and the Slice 4 sub-checks (lines 52-58):

1. **Verbatim spec drop-in — `## strawberry_config` GLOSSARY body (spec lines 517-553).** Programmatically stripped the `    > ` blockquote markers from the spec body and `diff`-compared against `docs/GLOSSARY.md` lines 978-1013. Result: exit 0, byte-identical. Every paragraph break, every code block, every link preserved character-for-character. Worker 2's call to flatten the blockquote `> ` wrappers (so the entry matches the un-blockquoted shape of `## Specialized scalar conversions` and `## Strictness mode`) was authorized by the plan's "Worker 2 discretion" bullet and is the right call for visual parity.
2. **Verbatim spec drop-in — `BigInt scalar` appended paragraph (spec line 556).** Compared content-only (the spec wraps the paragraph in `"..."` literal quotes that do not transcribe to the live GLOSSARY entry; this matches the spec's handling of the strict-serializer sentence at line 555). Stripped quotes from spec line 556 and the resulting 803-character string is byte-identical to `docs/GLOSSARY.md` line 179. Verbatim drop-in confirmed.
3. **Public exports bulleted list.** `docs/GLOSSARY.md` line 32 reads `- [`strawberry_config`](#strawberry_config) — factory returning a `StrawberryConfig` pre-populated with the package's `scalar_map`.` and lands immediately after `finalize_django_types`. Mirrors the Slice 1 `__all__` ordering pinned at `django_strawberry_framework/__init__.py` `__all__` (Python ASCII sort: `f` < `s`).
4. **Index table row.** `docs/GLOSSARY.md` line 113 reads `| [strawberry_config](#strawberry_config) | shipped ([Unreleased]) |`, positioned between `Specialized scalar conversions` (line 112) and `Strictness mode` (line 114). Case-insensitive lexical position confirmed; status string is the spec-authorized literal placeholder.
5. **`docs/README.md`.** Quick start (lines 18-50): import line widened to add `strawberry_config`; multi-line `strawberry.Schema(...)` carries `config=strawberry_config(),` between `query=Query,` and `extensions=[DjangoOptimizerExtension()],`. Schema setup boundary "Recommended" (lines 132-139): import widened, single-line Schema call carries `config=strawberry_config()` between `query=` and `extensions=`. Schema setup boundary "Wrong order" anti-example (lines 143-146): single-line Schema call gains `config=strawberry_config()` between `query=` and `extensions=` so the post-edit contrast remains `finalize_django_types()` placement only. Relay Node section (lines 58-73): code block ends at `finalize_django_types()` and carries no `strawberry.Schema(...)` constructor call — confirmed by direct read of the live anchor; no Schema-line to update. Build report's `### Notes for Worker 1 (spec reconciliation)` #1 records the disposition; per task instructions this sub-check has a recorded deferral, not silent un-addressing.
6. **`GOAL.md`.** Astronomy `schema.py` showcase (lines 83-156): import group at line 87-95 gains `strawberry_config,` as the last element after `finalize_django_types,`; line 155 rewritten from `schema = strawberry.Schema(query=Query)` to `schema = strawberry.Schema(query=Query, config=strawberry_config())`. No `extensions=` added (pre-edit line carried none; the spec line 565 pin authorizes only the kwarg additions). Migration shape per-stack diff blocks (lines 405-477) NOT edited; confirmed by direct read.
7. **`TODAY.md`.** "What to put in `examples/fakeshop/config/schema.py` today" block (lines 119-142): import widened to add `strawberry_config`; multi-line Schema call carries `config=strawberry_config(),` between `query=Query,` and `extensions=[DjangoOptimizerExtension()],`. Mirrors the Slice 3 fakeshop schema and the docs/README.md Quick start exactly.
8. **`docs/TREE.md` UNCHANGED.** `git diff -- docs/TREE.md` returns empty. DoD item 13 satisfied.
9. **`README.md` (root) UNCHANGED.** `git diff -- README.md` returns empty. DoD item 14 satisfied.
10. **CSV — `docs/spec-020-scalar_map_helper-0_0_7-terms.csv`.** Exactly one new row appended at end (line 18): `strawberry_config,strawberry_config,The factory function this card introduces; entry created in Slice 4.`. Append-at-end position is the plan's authorized minimal-diff approach. `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` re-run during this review reports `OK: 17 terms — all have glossary entries and at least one spec link.` — exactly the post-Slice-4 expected count.
11. **Markdown fence backtick count.** The new `## strawberry_config` GLOSSARY entry contains three top-level triple-backtick `python` code blocks (lines 982-990, 994-1000, 1004-1009). The entry itself is NOT wrapped in any outer fence — like neighbor entries (`## Specialized scalar conversions`, `## Strictness mode`), it is a standard Markdown section. Triple-backtick inner fences render correctly; no four-backtick wrapping needed.
12. **No stale "coming soon" / "planned" wording.** The status string for `strawberry_config` is `shipped ([Unreleased])` per spec line 515; this is the spec-authorized post-cut placeholder, to be promoted by the maintainer at the next version cut. Not stale, not obsolete.

Format / lint sanity: `uv run ruff format --check .` reports `118 files already formatted`; `uv run ruff check .` reports `All checks passed!`. No drift from Worker 2's `### Validation run` outcome.

### What looks solid

- Verbatim spec drop-ins: both the new `## strawberry_config` entry body (lines 978-1013) and the `## `BigInt` scalar` appended paragraph (line 179) are byte-identical to spec lines 517-553 and 556 respectively (modulo the spec's blockquote `> ` markers and `"` quote wrappers, which are formatting artifacts of how the spec presents the pinned bodies). Worker 2's flattening of the spec's blockquote `> ` markers in the strawberry_config body matches the un-blockquoted shape of every neighbor GLOSSARY entry.
- Kwarg-order consistency: every Slice-4 doc surface that touches `strawberry.Schema(...)` lands the trio in the same order — `query=`, `config=strawberry_config()`, `extensions=[...]` when the existing surface had an `extensions=` argument; `query=`, `config=strawberry_config()` when the existing surface did not (GOAL.md astronomy). The pre-edit shape of each call site (multi-line vs single-line) is preserved verbatim apart from the inserted kwarg, which keeps the visual contrast that the Schema setup boundary "Wrong order" anti-example exists to illustrate.
- `__all__`-mirroring placement: the new Public exports bullet lands immediately after `finalize_django_types` to mirror the Slice 1 `__all__` ordering; the GOAL.md import-list addition lands at the end of the parenthesized cluster (matching the same ordering convention). One symbol, one position rule applied everywhere.
- CSV minimal-diff: append-at-end is the right call given the existing CSV is not strictly sorted and `scripts/check_spec_glossary.py` does not check ordering. Single-line diff; script re-run independently confirms `OK: 17 terms`.
- Helper skip recorded with reason: Slice 4 is Markdown / CSV only, no Python logic. Plan's `### DRY analysis` records the helper-skip disposition with the BUILD.md rule citation; build report carries it forward. No silent skip.
- Spec-reconciliation reservations cleanly flagged: the Relay Node Schema-construction sub-bullet disposition and the spec lines 13-14 Key-glossary-references callout removal are both surfaced under the build report's `### Notes for Worker 1 (spec reconciliation)` for the Worker 1 Slice-4 final-verification pass. Worker 2 correctly did NOT make either spec edit.

### Temp test verification

- No temp tests created during this review. Slice 4 ships zero Python logic, zero new behavior; the only verification available is `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md`, which is a script run (not a pytest test) and was executed independently during this review to confirm `OK: 17 terms`.
- Helper (`scripts/review_inspect.py`) NOT run for this slice; Slice 4 modifies only Markdown and CSV files, no `.py` files. Per BUILD.md "When to run the helper during build", Worker 3 runs the helper only for new `.py` files, `optimizer/` / `types/` touches, or 30+ / 50+ new lines of Python logic. None apply. Skip recorded here with reason.

### Notes for Worker 1 (spec reconciliation)

1. **Relay Node sub-check disposition (spec line 53).** The build report's `### Notes for Worker 1 (spec reconciliation)` #1 records the live anchor reality: `docs/README.md` `### Relay Node` (lines 58-73) ends at `finalize_django_types()` and carries no `strawberry.Schema(...)` constructor call. Worker 2 correctly did NOT fabricate one. Worker 1 final-verification disposes per the plan's recorded likely outcome — option (a): tick the Relay Node sub-check with a one-line note that the live anchor has no Schema-construction line to update. Reviewing the live state of the file confirms the disposition is accurate; not a Medium "silently un-addressed sub-check" because the build report records the disposition explicitly.
2. **Spec lines 13-14 callout removal (DoD item 9a).** Reserved for Worker 1's Slice-4 final-verification pass per the plan's `### Notes for Worker 1 (Slice-4 final-verification spec edit reservation)`. The callout became stale the moment the CSV row landed; Worker 2 correctly did NOT touch the spec body. The post-removal `scripts/check_spec_glossary.py` re-run should still report `OK: 17 terms` (the term lives in both the spec body and the glossary; only the explanatory callout is removed).
3. **Stale `docs/TREE.md` wording (build report #3).** The "Strawberry deprecation suppressed at definition site" phrase in `docs/TREE.md` lines ~202 / ~246 is factually stale post-Slice-1 (the suppression block was removed; the no-warning overload replaced it). Spec DoD item 13 forbids `docs/TREE.md` edits in this card. Flagged for the cross-slice integration pass / `bld-final.md` Deferred work catalog as the build report already records; not a Slice-4 review blocker.

### Review outcome

`review-accepted`. Every Slice 4 sub-check from the spec checklist (lines 52-58) is reflected in the diff (or has a recorded deferral under the build report's spec-reconciliation notes for Worker 1 to dispose). The two verbatim spec drop-ins are byte-identical to the spec source. The Public exports bullet and Index table row land in the spec-pinned positions. `docs/TREE.md` and root `README.md` are confirmed unchanged. The CSV term count is `OK: 17 terms` per independent script run. No High / Medium / Low findings.

---

## Final verification (Worker 1)

- **Spec slice checklist:** every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]`. The five sub-bullets whose contract landed verbatim in the diff (`docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, `docs/spec-020-scalar_map_helper-0_0_7-terms.csv`) tick as-is. The `docs/TREE.md` sub-bullet asserts "no edit" and `git diff -- docs/TREE.md` is empty — contract intact. The `docs/README.md` sub-bullet has one sub-claim (the Relay Node Schema-construction edit) that is a no-op against the live anchor; the parent sub-check ticks because every other claim in the bullet (Quick start + Schema setup boundary x2) landed, and the Relay Node no-op disposition is recorded under `### Spec changes made (Worker 1 only)` per BUILD.md "Silently un-ticked boxes are not allowed".
- **DRY check across this slice and prior accepted slices:** the `config=strawberry_config()` pattern repeats across Slice 2 (10 converter-table sites + 2 integration tests in `tests/test_scalars.py`), Slice 3 (the fakeshop project schema), and Slice 4 (six doc-side touch points). This repetition is the canonical post-migration consumer contract per spec Decision 2 (which explicitly rejected a `dst.Schema(...)` wrapper to consolidate the pattern). Not a DRY violation; the repetition IS the demonstration consumers must read. Kwarg order is consistent (`query=`, `config=strawberry_config()`, `extensions=[...]`) across every doc surface. No new duplication introduced.
- **Existing tests still pass:** Slice 4 ships zero Python source / test changes. Per the task instructions ("Slice 4 ships no Python changes; you MAY skip the focused test run since no test surfaces are affected"), focused pytest invocation is skipped for this final-verification pass. The Slice 2 final-verification run (recorded in `worker-1.md`) confirmed 103 passed / 2 skipped / 0 failed across `tests/test_scalars.py`, `tests/base/test_init.py`, and `tests/types/test_converters.py`; Slice 4's diff does not touch any test surface, so that result still holds. Final cross-tree sweep runs at the final-test-run gate (`bld-final.md`).
- **Spec reconciliation:** two Worker-1 spec edits made (recorded under `### Spec changes made (Worker 1 only)` below) — the Key-glossary-references CSV-completeness callout removal at spec lines 13-14 (the "REMOVE WHEN SLICE 4 LANDS" blockquote) and the status-line refresh at spec line 4 (`Slices 1-3 shipped` → `Slices 1-4 shipped`). The Relay Node sub-claim is recorded as a no-op deferral (option (a) per task instructions); no spec edit to spec line 53 is made because the spec's claim was wrong-but-harmless and documenting the live anchor reality in this artifact is the more informative record.
- **Post-edit glossary check:** `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` → `OK: 17 terms — all have glossary entries and at least one spec link.` Confirms the callout removal did not regress the term count (the `strawberry_config` term and its glossary anchor remain in both the spec body and `docs/GLOSSARY.md`; only the explanatory note was removed).
- **Final status:** `final-accepted`.

### Summary

Slice 4 ships the consumer-facing documentation for the `strawberry_config(...)` migration: `docs/README.md` Quick start and both Schema setup boundary blocks (Recommended + Wrong-order anti-example) gain `config=strawberry_config()`; `docs/GLOSSARY.md` carries a new `## strawberry_config` entry (verbatim per spec lines 517-553), an updated `BigInt scalar` entry body (verbatim per spec line 556), a new Public exports bullet, and a new Index row; `GOAL.md`'s astronomy showcase `schema.py` block gets the imports widening and the `config=strawberry_config()` kwarg; `TODAY.md`'s fakeshop config block mirrors the Quick start update; and `docs/spec-020-scalar_map_helper-0_0_7-terms.csv` gains the `strawberry_config` row that brings the spec's glossary-references check to `OK: 17 terms`. `docs/TREE.md` and root `README.md` are unchanged per DoD items 13-14. The two Worker-1-reserved spec edits (Key-glossary-references callout removal and status-line refresh) landed in this final-verification pass.

### Spec changes made (Worker 1 only)

1. **`docs/spec-020-scalar_map_helper-0_0_7.md` lines 13-14 (callout removal).** Removed the `> **Note (terms CSV completeness — REMOVE WHEN SLICE 4 LANDS):** ...` blockquote paragraph from the `## Key glossary references` section. Slice triggered: 4. Reason: the callout was self-marked for removal once Slice 4 landed the CSV row and the `strawberry_config` GLOSSARY entry; both are now in place, the callout is stale, and DoD item 9a authorizes the removal. Post-removal `scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` confirms `OK: 17 terms`.
2. **`docs/spec-020-scalar_map_helper-0_0_7.md` line 4 (status-line refresh).** Rewrote the `Status:` line from `in flight — Slices 1–3 shipped (helper module + BigInt redefinition; tests; example-app migration); Slices 4–5 remain.` to `in flight — Slices 1–4 shipped (helper module + BigInt redefinition; tests; example-app migration; docs); Slice 5 remains.`. Slice triggered: 4. Reason: per `worker-1.md` "Spec status-line re-verification (every Worker 1 spawn)", the status line must describe current state of the spec relative to the build; Slice 4 has now shipped and the prior wording would be stale.
3. **Relay Node sub-claim — recorded no-op deferral (option (a) per task instructions).** The `docs/README.md` sub-bullet at spec line 53 names the Relay Node example as one of three Schema-construction sites that should add `config=strawberry_config()`. Live anchor reality: `docs/README.md` `### Relay Node` (lines 54-75) ends at `finalize_django_types()` and contains no `strawberry.Schema(...)` constructor call. The spec's anticipation of a Schema call there was wrong-but-harmless. No spec edit to spec line 53 is made (option (b) was also acceptable per task instructions; option (a) is the more informative record for future readers). The parent `docs/README.md` sub-check ticks because the Quick start and Schema setup boundary x2 claims all landed verbatim; the Relay Node sub-claim is a no-op against the live doc, not a silently un-addressed contract.
