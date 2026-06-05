# Feedback — `spec-029-consumer_dx_cleanup-0_0_9.md` (review of Revision 3)

Reviewed 2026-06-04 against the repo at HEAD, the locked Strawberry `0.316.0`, and source.
Priority convention matches the spec's: **P1** = foundational, **P2** = correctness/completeness
gap, **P3** = accuracy/polish.

**Verdict:** Revision 3 landed cleanly. All eight Revision-2 findings were addressed, and I
re-verified the fixes against source — they're not just present, they're *correct* (see
[Confirmed fixed](#confirmed-fixed)). The notable change is that Slice 1 flipped from "keep the
instance form" to **adopting the singleton-factory** (my P1.3) — a good call, and the mechanism
is described accurately. But that pivot is now load-bearing across ~24 sites, and it introduced
**one real new correctness problem** (the "one module-level `_optimizer` per file" instruction
breaks the optimizer suite's per-test cache isolation) plus **two stale cross-references** the
incomplete rewrite left behind. None is hard to fix; the P1 needs fixing before Slice 1 is
implemented or the test suite will fail.

---

## P1 — new: "one module-level `_optimizer` per file" breaks per-test cache & strictness isolation

The Slice-1 checklist (line 78) and Decision 3 (line 293) instruct: *"one module-level
`_optimizer` per file … `_optimizer = DjangoOptimizerExtension(...)` (one per module)."* Applied
literally to `tests/optimizer/test_extension.py` this **breaks tests**, and it contradicts the
spec's own "behavior-preserving" claim (lines 514, 516). Three concrete reasons, all verified:

1. **The cache tests need a fresh instance per test.** `test_cache_hit_on_repeated_query`
   (`test_extension.py:728-748`) does `ext = DjangoOptimizerExtension(); … extensions=[ext]` and
   asserts `ext.cache_info().misses == 1`, `hits == 1`, `size == 1`. Those counters/`_plan_cache`
   live on the **instance** (`extension.py:493-497,647,661`). A single module-level `_optimizer`
   shared across the file's ~19 schema-building tests would accumulate cache state **across
   tests** → `misses==1`/`size==1` get polluted → order-dependent failures.

2. **The cache-hit test also pins the upper bound — it must be the *same* instance across two
   executes, but *not* shared beyond the test.** It calls `schema.execute_sync(query)` twice and
   asserts the second is a hit. This rules out the constructing factory the spec (correctly)
   rejects: `extensions=[lambda: DjangoOptimizerExtension()]` would build a fresh instance per
   execute → second call is a **miss** → test fails. The *only* correct form is
   `extensions=[lambda: ext]` where `ext` is that test's local instance — a **function-local**
   singleton-factory, not a module-level one.

3. **`strictness` varies per site.** `test_relay_id_projection.py:80` is
   `extensions=[DjangoOptimizerExtension(strictness="raise")]` while lines 51 and 157 in the same
   file use the default. One module-level `_optimizer` cannot carry two strictness values.

**Fix:** change the instruction from "one module-level `_optimizer` per file" to **per
construction site** — wrap each existing instance as `extensions=[lambda: <that site's
instance>]`, function-local where the test holds a reference (the cache tests) and module-level
only where there's genuinely one schema per module (`config/schema.py`, the doc snippets). The
"module-level singleton" framing is right for the consumer/example case (one schema per module)
but does not generalize to the multi-schema test modules.

**Related scope gap:** the migration targets named in lines 77-78 are
`extensions=[DjangoOptimizerExtension()]` (anonymous) and `extensions=[DjangoOptimizerExtension]`
(class). But the cache tests use the **named** form `ext = DjangoOptimizerExtension();
extensions=[ext]`, which *also* trips 0.316.0's `Schema.__init__` `DeprecationWarning`. For DoD
item 4 ("the instance-form `DeprecationWarning` … is **gone** after the migration") to hold, the
named-instance sites must be in scope too. Either widen the migration target description to "any
`extensions=[<instance>]` entry" or DoD item 4 is unachievable as written.

---

## P2 — regression: a stale cross-reference still tells the connection-field card to use the instance form

The Decision-3 rewrite updated most call sites but missed **Out of scope, line 593**:

> **`DjangoConnectionField`** … Slice 1 **keeps and documents the `extensions=` instance form**, so
> this card's new schema-construction surfaces should **present the instance form too**…

This directly contradicts the revised Decision 3 (migrate to the singleton-factory) and its own
matching bullet at line 60, which *was* updated ("Slice 1 migrates … to the singleton-factory, so
the connection field's new schema-construction surfaces should present the same singleton-factory
form"). Left as-is, line 593 would steer the sibling `WIP-ALPHA-030-0.0.9` connection-field
implementer to adopt the **deprecated, cold-cache-prone** instance form — the exact regression this
card exists to remove. **Fix:** rewrite line 593 to point at the singleton-factory, mirroring line 60.

---

## P3 — minor accuracy / polish

- **Stale heading (line 162).** `### Slice 1 — `extensions=` construction (the instance form is
  intentional)` — the body beneath it now recommends the singleton-factory and marks the instance
  form DEPRECATED. The parenthetical contradicts its own section. Retitle to "(the singleton-factory
  form)" or similar.
- **Stale Non-goals wording (line 138).** "Slice 1 **only documents** the construction snippet" — under
  Revision 3 Slice 1 *migrates* ~24 sites, it doesn't just document. The actual non-goal (no
  filter/order/nullability argument injection) is intact; only the "only documents" lead-in is stale.
- **`test_query/README.md` not in the migration list.** Current state (line 122) names
  `examples/fakeshop/test_query/README.md` as an instance-form site, but the Slice-1 migration list
  (line 78) and DoD items 2-3 omit it. Confirm whether that snippet is intentionally left on the old
  form or should migrate with the rest (it's prose, so not test-breaking either way — just name the
  intent so it isn't silently skipped).
- **No-warning test robustness (line 516).** `warnings.catch_warnings(record=True)` only records if
  the filter lets the warning through; add `warnings.simplefilter("always")` inside the context so a
  previously-emitted `DeprecationWarning` (Python dedupes by default) can't produce a false green.
  Implementation detail, not a spec change — worth a parenthetical in the test plan.

---

## Confirmed fixed (re-verified against source)

Each Revision-2 finding was addressed, and I checked the fix is correct — not just inserted:

- **P1.1 (stale `_sync`/`_async` model)** — Decision 3 (lines 287-291), Current state (line 123), and
  a new Risks bullet (line 587) re-derive the behavior against `Schema.get_extensions`
  (`schema.py:388`, the per-request `[ext if isinstance(ext, SchemaExtension) else ext()]`), pinned
  to the locked `0.316.0`. Accurate.
- **P1.2 (instance form does warn)** — corrected throughout; the no-warning assertion is now a Slice-1
  test (line 516) and DoD item 4 (line 616). The warning's trigger is described correctly: the
  `any(isinstance(ext, SchemaExtension))` check at `Schema.__init__` (`schema.py:270`), which a
  lambda entry evades. Accurate.
- **P1.3 (singleton-factory resolves the conflict)** — adopted as the decision; the concurrency
  rationale ("per-request state on `ContextVar`s, not `self`") matches `extension.py:281,293,518`
  (`_optimizer_active` / `_printed_ast_cache`). The "identical to the bare instance" claim is right.
  (The granularity of *how* to apply it across test files is the new P1 above.)
- **P2.1 (Relay-suppressed pk)** — Decision 4 (line 318) adds the interface-sourced `GlobalID!`
  special-case and calls out the `KeyError` the naive `origin.__annotations__[pk_name]` read would
  raise; `test_inspect_relay_node_pk_row` (line 526) covers it on `GenreType`. Correct — `GenreType`
  is the only Relay-Node type (`apps/library/schema.py:119`).
- **P2.2 (BookType not Relay-shaped)** — the example output now shows `id → BigAutoField → Int! →
  SCALAR_MAP[BigAutoField]` (line 205) and a `GenreType` Relay-pk note (line 214). **Verified
  accurate:** `BigAutoField` maps to `int` (`converters.py:56`), so a non-null pk renders `Int!`, and
  BookType's `Meta` declares no `interfaces`. `test_inspect_by_registered_name` (line 521) pins the
  non-Relay `Int!`.
- **P2.3 (cold CLI invocation)** — Decision 4 adds the `--schema <dotted_path>` import (line 320),
  the unfinalized `CommandError` now names `--schema` (line 324), and `test_inspect_with_schema_option`
  (line 523) covers it. The reasoning (importing one module registers but doesn't finalize) is correct.
- **P2.4 (schema-wide assertions)** — a verification step is in the Slice-3 test plan (line 555) with
  a grep result; the "re-run at implementation time" hedge is the right posture.
- **P3.1 (NEXT.md wording)** — softened to "Step 7 *defers* glossary anchoring … it does not forbid
  authoring an entry" (line 579). Accurate.

Also still-clean from the Revision-2 pass (spot-checked, unchanged): the Decision-3 heading rename
left **no broken anchors** (zero references to the old `#decision-3--slice-1-keeps-…` slug); the
three-stage validation ordering, `convert_scalar` tri-state, `DjangoTypeDefinition`/`FieldMeta`
shape, registry methods, glossary anchors, and the companion CSV all remain as previously verified.

---

## Edit map

- **Slice 1 checklist (line 78) + Decision 3 (line 293):** replace "one module-level `_optimizer`
  per file" with "per construction site (function-local `lambda: <instance>` where a test holds a
  reference)"; widen the migration target to include named `extensions=[<instance>]` sites (P1).
- **Out of scope (line 593):** rewrite to the singleton-factory, mirroring line 60 (P2).
- **User-facing API heading (line 162), Non-goals (line 138), Current state vs. migration-list
  (lines 122/78):** clear the stale "instance form" / "only documents" wording (P3).
- **Slice 1 test plan (line 516):** note `simplefilter("always")` for the no-warning assertion (P3).
