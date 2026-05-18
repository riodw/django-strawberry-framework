# Build: Slice 6 — Docs, KANBAN, CHANGELOG, archive

Spec reference: `docs/spec-014-meta_primary-0_0_6.md` (lines 176-260)
Status: final-accepted

## Plan (Worker 1)

This is the largest commit of the build (spec line 176). It is doc-and-release-metadata only — no source edits, no test edits, no version-string edits (Slice 5 already verified all five version-bump sites are at `0.0.6`). Spec custody: the spec stays at `docs/spec-014-meta_primary-0_0_6.md`; archival to `docs/SPECS/` is opt-in and is the maintainer's call post-merge (spec line 260, also `BUILD.md` "Spec stays at its working location").

Spec status-line re-verification (Worker 1 spawn rule): spec line 4 reads `Status: draft (revision 6, post-TODO-anchor review).` — left as-is for this planning pass. The "draft (revision 6, …)" framing is about the spec's revision history; the spec's lifecycle stays at the working location through closeout per spec line 260. If the maintainer wants the literal `draft` flipped to `shipped (0.0.6)` post-merge, that is a Worker 1 final-verification edit; not load-bearing for Worker 2's mechanical drop-ins. Flagged below in `### Notes for Worker 1 (spec reconciliation)`.

### DRY analysis

DRY checks for a doc/release-metadata slice are about **consistency across files**, not code reuse:

- **Existing patterns reused.** Every doc-edit pattern this slice executes has a precedent in `spec-013-deferred_scalars-0_0_6.md` Slice 6 (the immediate predecessor `0.0.6` card): KANBAN move with verbatim body drop-in, CHANGELOG `[Unreleased]` `Added`/`Changed` entries, `docs/FEATURES.md` status-badge flip in `## Index` + entry body rewrite, `docs/README.md` "Shipped today" bullet addition, `TODAY.md` "available but not currently demonstrated in fakeshop" line. The shape from spec-013 is the template; the content swaps `BigInt`-class wording for `Meta.primary`-class wording. No new pattern is introduced.
- **New helpers justified.** None. This is a doc-edit slice; no module-level helpers are appropriate. The five CHANGELOG bullets are spec-pinned verbatim text (spec lines 255-259), not a new editorial pattern.
- **Duplication risk avoided.** The `Meta.primary` description appears in **five** places after this slice: `docs/FEATURES.md` (the `## Meta.primary` entry rewrite + the `## Index` row + the `## DjangoType` alpha-constraint replacement bullet), `docs/README.md` (the new "Shipped today" bullet), `TODAY.md` (the "available but not currently demonstrated in fakeshop" note), `KANBAN.md` (the verbatim DONE-014 body), and `CHANGELOG.md` (the `Added` / `Changed` bullets). To prevent these from drifting into five different mental models, **every site uses the same three-helper vocabulary**: `primary_for(model)` / `types_for(model)` / `models_with_multiple_types()`. This vocabulary is already pinned in the spec's verbatim KANBAN body at spec lines 198-199 and in the CHANGELOG `Added` line at spec line 255. Worker 2 must mirror that same trio in:
  - `docs/FEATURES.md`'s rewritten `## Meta.primary` entry body (the "primary_for / types_for / models_with_multiple_types registry surface" phrasing in spec line 180).
  - `docs/README.md`'s new "Shipped today" bullet (a single-line nod to "via the primary-flag opt-in" is enough — full registry-surface vocabulary stays in FEATURES).
  - The CHANGELOG `Added` entry (verbatim from spec line 255).
- **DRY between the `Meta.primary` entry rewrite and the `DjangoType` alpha-constraint removal.** Spec line 181 says the `DjangoType` entry's "one `DjangoType` per Django model" bullet at `docs/FEATURES.md:387` is **replaced** with a one-line "multiple `DjangoType`s per model supported via [`Meta.primary`](#metaprimary)" entry. That replacement bullet must point at the rewritten `## Meta.primary` entry (anchor `#metaprimary`), so the reader has one canonical place to find the contract. The `DjangoType` bullet is intentionally one line — the contract lives in the `Meta.primary` entry, not duplicated in `DjangoType`.

### Implementation steps

Steps grouped by file. Each file cites spec line(s) authorizing the change and the current line position. **Order within the commit does not matter** for the doc-only changes (no compile-order risk); for clarity, the order below is the spec-checklist order from spec lines 177-186.

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — Slice 5's no-op disposition means none of these files should have moved, but `grep` first.

#### Step 1 — Root `README.md` (spec line 177)

**Authorization:** spec line 177 — "Root `README.md` — confirm the package-version line reads `0.0.6` (no-op if any prior `0.0.6` card already bumped it)."

**Current state:** `README.md:45` reads `**`0.0.6`, single-maintainer, alpha-quality.**`. Confirmed at planning time via `grep -n "0\.0\.6" README.md`. The line is already at `0.0.6` from a prior `0.0.6` card.

**Action:** **No edit.** Worker 2 confirms via `grep -n "0\.0\.6" README.md` that line 45 still reads `0.0.6` and records "Files touched: README.md (no-op; confirmed at 0.0.6 via grep)" in the build report's `### Files touched` section.

#### Step 2 — `docs/README.md` (spec line 178)

**Authorization:** spec line 178 — "Confirm the 'shipped today is `0.0.6`' line (no-op if any prior `0.0.6` card already bumped it). Add a one-line mention of `Meta.primary` to the shipped-capability summary."

**Current state:** `docs/README.md:89` reads `**Shipped today** (`0.0.6`):` — the version is already at `0.0.6`. Lines 90-100 list the shipped-today capabilities. Line 103 reads `- `Meta.primary` for multiple `DjangoType`s per model` and is **inside the "Coming in `0.1.0`" block** (line 102), which is now stale (Meta.primary has shipped in 0.0.6).

**Action — two edits:**

1. **Add `Meta.primary` to "Shipped today" list.** Insert a new bullet after the existing "Shipped today" bullets (between line 100 and 101) reading:
   ```
   - `Meta.primary` — multiple `DjangoType` subclasses per Django model with explicit primary-flag opt-in
   ```
   The exact position is at the bottom of the "Shipped today" list, just before the blank line that separates it from the "Coming in `0.1.0`" block. Use the existing-bullets cluster as the anchor — Worker 2 uses `Edit` with `old_string = "- model / type registry and \`auto\` re-export from Strawberry\n\n**Coming in \`0.1.0\`"` and `new_string = "- model / type registry and \`auto\` re-export from Strawberry\n- \`Meta.primary\` — multiple \`DjangoType\` subclasses per Django model with explicit primary-flag opt-in\n\n**Coming in \`0.1.0\`"`.

2. **Remove `Meta.primary` from "Coming in `0.1.0`" list.** Line 103 currently reads `- `Meta.primary` for multiple `DjangoType`s per model`. Delete that line (the bullet immediately under "Coming in `0.1.0`"). Use `Edit` with `old_string = "**Coming in \`0.1.0\`** (beta — feature parity with \`graphene-django\` and \`strawberry-graphql-django\`):\n- \`Meta.primary\` for multiple \`DjangoType\`s per model\n- \`DjangoListField\`"` and `new_string = "**Coming in \`0.1.0\`** (beta — feature parity with \`graphene-django\` and \`strawberry-graphql-django\`):\n- \`DjangoListField\`"`.

The two edits are independent and can be applied in either order, but #2 must not be skipped — leaving `Meta.primary` in the "Coming in `0.1.0`" block would be a stale-version-status defect that violates BUILD.md Worker 3 doc-sanity rule ("no obsolete 'coming soon', 'planned', or old-version wording remains in files the slice deliberately updated").

#### Step 3 — `docs/FEATURES.md` (spec lines 179-182)

**Authorization:** spec lines 179-182:
- 180: `Meta.primary` → `shipped (0.0.6)`. Rewrite body to describe the actual delivered contract (ambiguity rules; `primary_for` / `types_for` registry surface; relation-target resolution semantics). Drop "planned for `0.0.6`" framing.
- 181: `DjangoType` → remove the alpha-constraint bullet at `docs/FEATURES.md:387`. Replace with one-line "multiple `DjangoType`s per model supported via [`Meta.primary`](#metaprimary)".
- 182: Index → flip the status badge on `Meta.primary` to `shipped (0.0.6)`.

**Current state (verified at planning time via `grep`):**

- `## Meta.primary` section header is at line **651**.
- `**Status:** planned for `0.0.6`.` is at line **653**.
- Body is at line **655**: `Allows multiple `DjangoType` subclasses for one Django model. `Meta.primary = True` declares the type used for nested-relation resolution (`AdminItemType` vs `ItemType` for the same `Item` model). Today the registry rejects a second `DjangoType` for a model that already has one; this `Meta` key promotes the behavior to a primary-declaration contract with an explicit primary.`
- `**See also:**` at line **657**.
- `## DjangoType` alpha-constraint bullet `- one DjangoType per Django model — [Meta.primary] promotes this to a primary-declaration contract` is at line **387**.
- Index row `| [`Meta.primary`](#metaprimary) | planned for `0.0.6` |` is at line **85**.

Spec line 181 cites `docs/FEATURES.md:387` for the alpha-constraint bullet position; verified intact at planning time. Spec line 180 (the entry rewrite) does not pin a line; the entry is at lines 651-657.

**Action — three edits (file order: line 85, line 387, lines 651-657):**

1. **Index status badge flip (line 85).** `Edit` `old_string = "| [\`Meta.primary\`](#metaprimary) | planned for \`0.0.6\` |"` `new_string = "| [\`Meta.primary\`](#metaprimary) | shipped (\`0.0.6\`) |"`. The "shipped (`0.0.X`)" status convention is the standing convention from the Status legend at `docs/FEATURES.md:14`.

2. **`DjangoType` alpha-constraint removal (line 387).** `Edit` `old_string = "- one \`DjangoType\` per Django model — [\`Meta.primary\`](#metaprimary) promotes this to a primary-declaration contract"` `new_string = "- multiple \`DjangoType\`s per Django model supported via [\`Meta.primary\`](#metaprimary)"`. Move this bullet **out** of the "Current alpha constraints" block — re-anchor it under the "Shipped capability" list (the bullets at lines 374-383, between the "Shipped capability:" heading at line 373 and the "Current alpha constraints:" heading at line 385). The simplest mechanical approach: (a) delete the bullet from line 387 via the `Edit` above (replacing it with the new wording, then immediately delete the entire replacement line); (b) insert the new bullet into the shipped-capability list at line 383 (the last shipped-capability bullet — `abstract / intermediate base support when a subclass has no Meta`). Concretely, Worker 2 uses two `Edit` calls:
   - **Edit A (remove alpha constraint bullet):** `old_string = "Current alpha constraints:\n\n- one \`DjangoType\` per Django model — [\`Meta.primary\`](#metaprimary) promotes this to a primary-declaration contract\n- manual override validation"` `new_string = "Current alpha constraints:\n\n- manual override validation"`.
   - **Edit B (add shipped-capability bullet):** `old_string = "- abstract / intermediate base support when a subclass has no \`Meta\`\n\nCurrent alpha constraints:"` `new_string = "- abstract / intermediate base support when a subclass has no \`Meta\`\n- multiple \`DjangoType\`s per Django model supported via [\`Meta.primary\`](#metaprimary)\n\nCurrent alpha constraints:"`.

   Net effect: the "one DjangoType per Django model" constraint is removed; a new positive-capability bullet `- multiple DjangoTypes per Django model supported via [Meta.primary]` is added to the shipped-capability list; the "Current alpha constraints:" block continues with just the deferred-validation bullet at line 388.

3. **`## Meta.primary` entry rewrite (lines 651-657).** Replace `**Status:** planned for \`0.0.6\`.` and the single body paragraph with `**Status:** shipped (`0.0.6`).` plus a rewritten body that mirrors the verbatim KANBAN body's contract phrasing (Step 6 below) and uses the three-helper vocabulary (`primary_for` / `types_for` / `models_with_multiple_types`) consistently with the CHANGELOG.

   `Edit` `old_string`:
   ```
   ## `Meta.primary`

   **Status:** planned for `0.0.6`.

   Allows multiple `DjangoType` subclasses for one Django model. `Meta.primary = True` declares the type used for nested-relation resolution (`AdminItemType` vs `ItemType` for the same `Item` model). Today the registry rejects a second `DjangoType` for a model that already has one; this `Meta` key promotes the behavior to a primary-declaration contract with an explicit primary.

   **See also:** [`Meta.model`](#metamodel) · [`DjangoType`](#djangotype).
   ```

   `new_string`:
   ```
   ## `Meta.primary`

   **Status:** shipped (`0.0.6`).

   Boolean flag (default `False`) declared on a `DjangoType`'s nested `Meta` to opt one of several types on the same Django model into the **primary** role. The primary type is the one auto-synthesized relation fields resolve to and the one [`registry.get(model)`](#djangotype) returns. Secondary types are still registered and reverse-discoverable via `registry.model_for_type(SecondaryType)`, so resolvers returning a secondary type stay planable through [`DjangoOptimizerExtension`](#djangooptimizerextension).

   Ambiguity rules:

   - One `DjangoType` for a model, `Meta.primary` absent or `False` — allowed (backward compat).
   - Multiple `DjangoType`s, exactly one with `Meta.primary = True` — allowed; relation targets resolve to the primary.
   - Multiple `DjangoType`s, two or more with `Meta.primary = True` — rejected at the second registration: `ConfigurationError("<class> is already declared primary as <existing>")`.
   - Multiple `DjangoType`s, none with `Meta.primary = True` — rejected at [`finalize_django_types()`](#finalize_django_types): `ConfigurationError` listing the model and every registered class, with fix sentence `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`.

   Registry surface: `primary_for(model)` returns the declared primary or `None`; `types_for(model)` returns the tuple of every registered type in declaration order; `models_with_multiple_types()` iterates models with two or more registered types (used by the finalize-time ambiguity audit).

   The already-shipped consumer relation-override paths (annotation overrides like `category: AdminCategoryType` and assigned `strawberry.field` relation resolvers) are preserved unchanged and may legitimately target a secondary `DjangoType`. The optimizer's plan cache keys include the resolver's origin Strawberry type, so a primary-return and a secondary-return resolver on the same model do not share a cached plan.

   **See also:** [`Meta.model`](#metamodel) · [`DjangoType`](#djangotype) · [`finalize_django_types`](#finalize_django_types) · [`ConfigurationError`](#configurationerror).
   ```

   The rewrite explicitly cites the three-helper vocabulary, the four ambiguity-rule rows from spec lines 483-489 (Decision 5), and the already-shipped-override clause from spec lines 245-252 (verbatim KANBAN body's "Design notes" tail). It mirrors — without duplicating verbatim — the verbatim KANBAN body's bullets at spec lines 192-237. Anchors in cross-references match existing anchors in `docs/FEATURES.md` (`#djangotype`, `#djangooptimizerextension`, `#finalize_django_types`, `#configurationerror`, `#metamodel`).

#### Step 4 — `docs/TREE.md` (spec line 183)

**Authorization:** spec line 183 — "no source-tree changes (no new files); add `Meta.primary` to the `[alpha]` milestone tag for `DjangoType` if relevant; otherwise no-op."

**Current state:** `docs/TREE.md:238` reads `├── registry.py              # model→type registry (gains Meta.primary at beta)`. This is in the **target package layout** (the future-tree section, not the current-on-disk section at line 199). The "(gains Meta.primary at beta)" framing is now stale — `Meta.primary` ships in `0.0.6` (alpha), not beta.

**Action — one edit:**

- `Edit` `old_string = "├── registry.py              # model→type registry (gains Meta.primary at beta)"` `new_string = "├── registry.py              # model→type registry (Meta.primary shipped in 0.0.6)"`.

This is a one-line wording fix that aligns the future-tree comment with reality. Spec line 183 explicitly permits "no source-tree changes; add `[alpha]` tag tweak if relevant" — the comment-string fix is the minimal change that resolves the staleness. No `[alpha]`/`[beta]` tag literal changes hand because the registry line doesn't have one; it has a free-form parenthetical comment which is what we're correcting.

The current-on-disk tree at line 199 reads `├── registry.py              # model→type registry (+ iter_types() public iterator)`. No edit needed there — the line accurately describes the package shape; `Meta.primary` is a `Meta`-key contract, not a registry-API addition that warrants an extra entry. (Worker 2 should NOT add `Meta.primary` to the current-on-disk line — it would over-specify the inline comment.)

#### Step 5 — `TODAY.md` (spec line 184)

**Authorization:** spec line 184 — "add `Meta.primary` to the 'what fakeshop demonstrates today' section if the example project exercises it; otherwise mention it under 'available but not currently demonstrated in fakeshop'."

**Current state:** `TODAY.md` has no current `Meta.primary` references (verified at planning time via `grep -n "Meta.primary" TODAY.md` — no matches). Fakeshop's two example schemas (`apps/products/schema.py` and `apps/library/schema.py`, per `TODAY.md:11-13`) declare exactly one `DjangoType` per model — `Meta.primary` is **not exercised** in either schema. Per the spec's else-branch, the entry goes under "available but not currently demonstrated in fakeshop".

`TODAY.md` does not currently have a section literally titled "available but not currently demonstrated in fakeshop". The closest existing section is "What the fakeshop example should wait for" (line 255 — confirmed at planning time via `grep -n "^## " TODAY.md`). That section is for **planned-but-unshipped** features (`DjangoConnectionField`, filters, etc.), not for shipped-but-not-exercised features — `Meta.primary` is the **first shipped-but-not-exercised feature** that needs its own home.

**Action — one edit:**

Add a new short section between "What the fakeshop example should wait for" (line 255) and the existing closing material. The new section is a 2-3-line callout. Worker 2 inserts immediately after the existing trailing bullet list at the file's tail.

`Edit` `old_string`:
```
## What the fakeshop example should wait for

Do not turn the commented rich fakeshop design into active code until the features it depends on ship. In practice, that means waiting for:
- `DjangoConnectionField`
- filters, ordering, aggregates, and fieldsets
- search fields
- permission cascade helpers
```

`new_string`:
```
## What the fakeshop example should wait for

Do not turn the commented rich fakeshop design into active code until the features it depends on ship. In practice, that means waiting for:
- `DjangoConnectionField`
- filters, ordering, aggregates, and fieldsets
- search fields
- permission cascade helpers

## Shipped capabilities available but not currently demonstrated in fakeshop

- `Meta.primary` (shipped in `0.0.6`) — multiple `DjangoType` subclasses per Django model with one explicit primary. Fakeshop's `apps/products/schema.py` and `apps/library/schema.py` each declare one `DjangoType` per model, so the multi-type contract is not exercised in the example today; the feature is fully covered by the package test suite. See [`docs/FEATURES.md#metaprimary`](docs/FEATURES.md#metaprimary).
```

The placement at the file tail keeps the existing "What fakeshop demonstrates today" / "what fakeshop model fields work today" sections untouched (they accurately describe what fakeshop **does** exercise; `Meta.primary` doesn't belong there per the else-branch of spec line 184). The new section header `"Shipped capabilities available but not currently demonstrated in fakeshop"` is the natural docs-side complement to "What the fakeshop example should wait for" — one section catalogs planned features fakeshop waits for, the other catalogs shipped features fakeshop hasn't grown a demo of yet. Future shipped-but-not-exercised features can append to this list.

#### Step 6 — `KANBAN.md` (spec lines 185-253)

**Authorization:** spec line 185 — "move `WIP-ALPHA-014-0.0.6` → `DONE-014-0.0.6`. **Drop in the verbatim body below:**". The verbatim body spans spec lines 187-253.

**Current state (verified at planning time):**

- `KANBAN.md:49` is the "In progress" summary mention: `- `WIP-ALPHA-014-0.0.6 — Multiple DjangoTypes per model with Meta.primary` — registry-multiplicity + primary-type-resolution work for the remaining `0.0.6` patch. Spec pending.`
- `KANBAN.md:51` is the `0.0.6` shipped-progress sentence: `- `0.0.6` shipped progress: `DONE-012-0.0.6` (`FieldMeta` consolidation) and `DONE-013-0.0.6` (deferred scalar conversions) landed in this version; the two WIP cards above complete the `0.0.6` patch.`
- `KANBAN.md:83` is the **full card body** header: `### WIP-ALPHA-014-0.0.6 — Multiple DjangoTypes per model with `Meta.primary``. The card body extends down to line 124 (verified via `grep` at planning time — line 125 starts the next card, `WIP-ALPHA-015-0.0.6`). The card body content (lines 83-124) is the **45-line WIP description** to be replaced.
- `KANBAN.md:1656` contains `### DONE-013-0.0.6 — Deferred scalar conversions` — the immediate predecessor `DONE` card; this is the natural reference for where the new `DONE-014` card body should land. Per the build's KANBAN convention (verified by `grep`), DONE cards live in the "DONE" column far down the file; the WIP card body at lines 83-124 needs to **move** to the DONE column, not just be rewritten in place.

**Verbatim body bounds re-verified at planning time.** Spec lines 187 (opening ```` ```markdown ```` fence) and 253 (closing ```` ``` ```` fence) confirmed via `awk 'NR==187 || NR==253' docs/spec-014-meta_primary-0_0_6.md`. Both fence lines begin with **4 spaces** of indent (the block is nested under the spec's `- [ ] KANBAN.md` checkbox). The body content (spec lines 188-252) is also 4-space indented.

**Fence convention check (BUILD.md Worker 3 doc-sanity rule).** The verbatim body uses an **outer 3-backtick fence with language tag `markdown`** (spec line 187: `    ```markdown`). The body content at spec lines 188-252 contains **no inner backtick code fences** (verified via planning-time `grep -nE '^[[:space:]]*\`\`\`' lines 188-252`). Because the inner content has no backtick fence collisions, the outer 3-backtick fence is safe — the BUILD.md "use 4 backticks if inner matches outer" rule does not need to fire here. Worker 2 drops the body in with a plain 3-backtick fence (or no fence at all; see below).

**Indent-strip pin.** When dropping the verbatim body into `KANBAN.md`, Worker 2 must **strip the 4-space indent** from every line of the body (spec lines 188-252). Within `KANBAN.md`, the new `### DONE-014-0.0.6 — ...` card sits at the **left margin** as a top-level card heading inside the DONE column — it is not nested under a checkbox the way it is in the spec. The fence lines themselves (spec lines 187 and 253) are **not** dropped into KANBAN — they are the spec-side wrapping that marks "this is a verbatim block"; the body content (lines 188-252) lands as raw Markdown.

Concretely: spec line 188 reads `    ### DONE-014-0.0.6 — Multiple DjangoTypes per model with \`Meta.primary\`` (4 spaces + content); the line landing in KANBAN.md reads `### DONE-014-0.0.6 — Multiple DjangoTypes per model with \`Meta.primary\`` (left-justified). Every body line follows the same indent-strip.

**Diff verification at Worker 3 review-pass (BUILD.md Worker 3 doc-sanity rule).** Worker 3 should confirm character-for-character via `diff` that the new `KANBAN.md` card body (after indent-strip) matches spec lines 188-252. Reference command for Worker 3: `diff <(awk 'NR>=188 && NR<=252' docs/spec-014-meta_primary-0_0_6.md | sed 's/^    //') <(awk '/^### DONE-014-0.0.6/,/^### DONE-013-0.0.6/' KANBAN.md | head -n -2)` (the trailing `head -n -2` drops the blank line + sibling `DONE-013` heading). Worker 1 final verification re-runs this diff.

**Action — three edits in `KANBAN.md`:**

1. **Update the "In progress" summary line at `KANBAN.md:49`.** Remove the WIP-014 line entirely from the "In progress" section (lines 47-52). The line at line 49 currently reads:
   ```
   - `WIP-ALPHA-014-0.0.6 — Multiple DjangoTypes per model with Meta.primary` — registry-multiplicity + primary-type-resolution work for the remaining `0.0.6` patch. Spec pending.
   ```
   Delete this bullet. The sibling `WIP-ALPHA-015-0.0.6` line at line 50 stays.

   Also update line 51's `0.0.6` shipped-progress sentence to add `DONE-014` to the shipped list and remove "the two WIP cards" framing. `Edit` `old_string = "- \`0.0.6\` shipped progress: \`DONE-012-0.0.6\` (\`FieldMeta\` consolidation) and \`DONE-013-0.0.6\` (deferred scalar conversions) landed in this version; the two WIP cards above complete the \`0.0.6\` patch."` `new_string = "- \`0.0.6\` shipped progress: \`DONE-012-0.0.6\` (\`FieldMeta\` consolidation), \`DONE-013-0.0.6\` (deferred scalar conversions), and \`DONE-014-0.0.6\` (multiple \`DjangoType\`s per model with \`Meta.primary\`) landed in this version; \`WIP-ALPHA-015-0.0.6\` remains to complete the \`0.0.6\` patch."`. Combine with the line-49 deletion in a single `Edit` if textually adjacent in the file — but they are separated by line 50's `WIP-ALPHA-015` bullet, so do them as two `Edit` calls.

2. **Remove the WIP-014 card body at `KANBAN.md:83-124`.** Delete the entire block from `### WIP-ALPHA-014-0.0.6 — Multiple DjangoTypes per model with `Meta.primary`` (line 83) down to and including line 124 (the last line of the WIP body — `tests/types/test_base.py` in the "Files likely touched" list). The line immediately after (line 125) is the next card's heading `### WIP-ALPHA-015-0.0.6 — Consumer override semantics (scalar fields)` — that stays untouched.

   `Edit` `old_string` (paste the verbatim 42-line block from `KANBAN.md:83-124`) `new_string = ""` — or, more cleanly, delete by `old_string` starting at line 83's heading and ending at line 124's last bullet, replaced by an empty string. Worker 2 reads the exact 42 lines via `Read` first and pastes them as `old_string`.

3. **Insert the new DONE-014 card body into the DONE column.** The natural insertion point is **immediately before** `### DONE-013-0.0.6 — Deferred scalar conversions` at line 1656 — DONE cards in this repo are arranged in reverse-chronological NNN order (per the planning-time `grep` showing DONE-013, then earlier DONEs further down). Reverse-chrono means `DONE-014` lands **above** `DONE-013`.

   Worker 2's `Edit`:
   - `old_string` is a small unique anchor at line 1656: `### DONE-013-0.0.6 — Deferred scalar conversions` (this string is unique in `KANBAN.md` per the planning-time grep — it appears only once).
   - `new_string` is the **verbatim body from spec lines 188-252 with the 4-space indent stripped from every line**, followed by a blank line, followed by `### DONE-013-0.0.6 — Deferred scalar conversions`.

   The exact `new_string` body is the 65-line block from spec lines 188-252. Worker 2 reads that range via `Read` (offset=188, limit=65) and strips the leading 4 spaces from each line before pasting. The body is reproduced here for cross-check (heading + bullets only; reproduced from the spec so Worker 2 has a side-by-side reference, but **the spec source is the canonical drop-in**):

   ```
   ### DONE-014-0.0.6 — Multiple DjangoTypes per model with `Meta.primary`

   Slice-by-slice scope (per `docs/spec-014-meta_primary-0_0_6.md`):

   - Registry stores multiple types per model (`_types: dict[Model, list[Type]]`).
   - New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`.
   - `registry.register(..., *, primary: bool = False) -> bool` and
     `registry.register_with_definition(..., *, primary=...)` accept the flag.
     `register()` now returns `bool` indicating whether state was added; drives
     snapshot-restore rollback in `register_with_definition`.
   - New registry surface: `primary_for(model)`, `types_for(model)`,
     `models_with_multiple_types()`.
   - `registry.get(model)` returns the primary if declared, else the single
     registered type, else `None`. Multiple types with no primary is an
     ambiguous-pending state that the finalizer audits.
   - `finalize_django_types()` runs `audit_primary_ambiguity()` first: any
     model with `>=2` registered types and no primary raises
     `ConfigurationError` naming the model and every registered class plus an
     actionable fix sentence.
   - Two primary types for the same model: rejected at registration time
     with message `"<class> is already declared primary as <existing>"`.
   - Relation conversion in `types/base.py` defers all **auto-synthesized**
     relation annotations to `finalize_django_types()` (eager-bind shortcut
     removed; eliminates the secondary-registered-before-source-before-
     primary import-order trap). The existing `consumer_authored_fields`
     short-circuit is preserved, so direct relation annotations (`category:
     AdminCategoryType`) and assigned `strawberry.field` resolvers continue
     to bypass synthesis entirely and may target a secondary `DjangoType`.
     `types/converters.py` and `types/finalizer.py` resolve auto-synthesized
     relations to the primary at finalize time.
   - Optimizer planning threads the resolved origin Strawberry type from
     `optimizer/extension.py` through `plan_optimizations` to the walker's
     root `_resolve_field_map(model, source_type=origin)` call. Root planning
     uses the resolver's actual return type; nested relation steps continue
     to use `registry.get(related_model)` (the primary). Plan cache key
     includes the origin type so primary-return and secondary-return
     resolvers on the same model do not share a cached plan.
   - Schema audit (`optimizer/extension.py`) iterates every reachable
     registered type via `registry.iter_types()` and dedupes warning
     collection. Secondary types whose relation fields the primary does not
     expose are still audited; identical-string duplicate warnings from
     overlapping field maps are collapsed.
   - `model_for_type` continues to work for any registered type so
     secondary-type resolvers stay planable.
   - `DjangoTypeDefinition` gains `primary: bool = False`.
   - 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,
     `tests/test_registry.py` / `tests/types/test_definition_order.py`
     (the existing finalize-test hosts), `tests/types/test_converters.py`
     (the existing relation-conversion host), and `tests/optimizer/`.

   Design notes carried into `0.0.6`:

   - Single-type-no-primary stays backward compatible: `registry.get(model)`
     still returns the lone type without requiring an explicit `primary` flag.
   - `Meta.primary` is a per-class declaration, not a registry-level
     `set_primary(Model, Type)` mutation — keeps the contract immutable
     after `__init_subclass__` runs.
   - Already-shipped consumer relation overrides (direct annotation
     `category: AdminItemType` and assigned `category = strawberry.field(...)`)
     stay in scope and are preserved by this card via the existing
     `consumer_authored_fields` short-circuit — they may legitimately
     target a secondary `DjangoType` after `Meta.primary` ships. A NEW
     declarative override API (e.g., `Meta.field_types = {...}`) is the
     `WIP-ALPHA-015-0.0.6 — Consumer override semantics` design space and
     is out of scope here.
   ```

   The above block matches spec lines 188-252 with the 4-space indent stripped from each line. Worker 2 verifies via `diff` (see "Diff verification at Worker 3 review-pass" above) before recording the change.

#### Step 7 — `CHANGELOG.md` (spec lines 254-259)

**Authorization:** spec line 254 — "`CHANGELOG.md` — `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`](../AGENTS.md)'s default prohibition)". This is the spec-pinned permission overriding `AGENTS.md`'s standing CHANGELOG-edit prohibition. Slice 6 is the only place in the build cycle where CHANGELOG edits are authorized.

**Current state (verified at planning time):**

- `CHANGELOG.md:19` is `## [Unreleased]`.
- `CHANGELOG.md:20` is `### Added`. Existing `Added` entries at lines 21-24 cover `BigInt`, `JSONField`, `HStoreField`, `ArrayField` (spec-013).
- `CHANGELOG.md:26` is `### Changed`. Existing `Changed` entries at lines 27-28 cover the `DjangoTypeDefinition` consolidation (spec-012) and the `PositiveBigIntegerField → BigInt` wire-format change (spec-013).
- `CHANGELOG.md:30` is `### Notes`. Existing entry at line 31 covers the `BigInt` deprecation suppression (spec-013).

**Spec-pinned verbatim bullets (spec lines 255-259):**

- Spec line 255 — `Added`: `Meta.primary` boolean flag. Multiple `DjangoType` subclasses per Django model. Registry surface: `primary_for`, `types_for`, `models_with_multiple_types`.
- Spec line 256 — `Changed`: `registry.register` now returns `bool` (whether state was added; was `None`). `registry.register` and `registry.register_with_definition` gained a keyword-only `primary: bool = False` parameter. `registry.get(model)` semantics: returns the primary if declared; the single type if only one is registered; `None` if multiple types are registered with no primary.
- Spec line 257 — `Changed`: `registry.iter_types()` now yields once per registered type — a model with multiple types appears multiple times. Consumers iterating to drive a per-model action should explicitly dedupe by model, or use `models_with_multiple_types()` + `types_for(model)` for an explicit grouping.
- Spec line 258 — `Changed`: `_build_annotations` (`types/base.py`) always defers **auto-synthesized** relation annotations to `PendingRelationAnnotation` + the registry's pending list; the eager-bind shortcut is removed. Consumer-authored relation fields (annotation overrides and assigned `strawberry.field`) continue to skip synthesis entirely — the existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved.
- Spec line 259 — `Changed`: optimizer plan cache key includes the resolver's origin Strawberry type alongside the model. Primary-return and secondary-return resolvers on the same model produce distinct cache entries.

**Action — two `Edit` calls:**

1. **Add the `Added` bullet (one new entry under `### Added`).** Insert after the existing `Added` entries at line 24 (the `ArrayField` bullet). The `Added` block is currently four bullets (lines 21-24); the new `Meta.primary` bullet becomes the fifth, between line 24 and the blank line at line 25.

   `Edit` `old_string = "- PostgreSQL \`ArrayField\` recursion through \`field.base_field\` via a sentinel-guarded branch in \`convert_scalar\`. Nested \`ArrayField\` and outer \`choices\` on \`ArrayField\` / \`HStoreField\` are rejected with \`ConfigurationError\`.\n\n### Changed"` `new_string = "- PostgreSQL \`ArrayField\` recursion through \`field.base_field\` via a sentinel-guarded branch in \`convert_scalar\`. Nested \`ArrayField\` and outer \`choices\` on \`ArrayField\` / \`HStoreField\` are rejected with \`ConfigurationError\`.\n- \`Meta.primary\` boolean flag. Multiple \`DjangoType\` subclasses per Django model. Registry surface: \`primary_for\`, \`types_for\`, \`models_with_multiple_types\`. Tracked as \`DONE-014-0.0.6\` in [\`KANBAN.md\`](KANBAN.md).\n\n### Changed"`.

   The trailing `Tracked as DONE-014-0.0.6 in KANBAN.md` clause mirrors the spec-013 pattern at `CHANGELOG.md:21` (`Tracked as DONE-013-0.0.6 in KANBAN.md`) — the same trailing reference shape used by every prior spec's CHANGELOG entry. Spec line 255 itself does not pin the trailing `Tracked as …` clause, so Worker 2 has discretion (see `### Implementation discretion items` below); the recommendation here is to include it for consistency with the spec-013 pattern.

2. **Add the four `Changed` bullets** at the bottom of the existing `Changed` block, between line 28 and the `### Notes` heading at line 30.

   `Edit` `old_string = "- \`PositiveBigIntegerField\` mapping switched from \`int\` to [\`BigInt\`](docs/FEATURES.md#bigint-scalar). Breaking wire-format change: \`PositiveBigIntegerField\` values are now serialized as decimal strings on the wire (not JSON integers) to survive GraphQL's signed 32-bit \`Int\` boundary. Consumers using the existing 32-bit \`int\` shape must update wire-format expectations.\n\n### Notes"` `new_string` is the same line + four newly added `Changed` bullets (verbatim from spec lines 256-259) + the blank line + `### Notes`.

   Verbatim content of the four new bullets:
   ```
   - `registry.register` now returns `bool` (whether state was added; was `None`). `registry.register` and `registry.register_with_definition` gained a keyword-only `primary: bool = False` parameter. `registry.get(model)` semantics: returns the primary if declared; the single type if only one is registered; `None` if multiple types are registered with no primary. Tracked as `DONE-014-0.0.6` in [`KANBAN.md`](KANBAN.md).
   - `registry.iter_types()` now yields once per registered type — a model with multiple types appears multiple times. Consumers iterating to drive a per-model action should explicitly dedupe by model, or use `models_with_multiple_types()` + `types_for(model)` for an explicit grouping.
   - `_build_annotations` (`types/base.py`) always defers **auto-synthesized** relation annotations to `PendingRelationAnnotation` + the registry's pending list; the eager-bind shortcut is removed. Consumer-authored relation fields (annotation overrides and assigned `strawberry.field`) continue to skip synthesis entirely — the existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved.
   - optimizer plan cache key includes the resolver's origin Strawberry type alongside the model. Primary-return and secondary-return resolvers on the same model produce distinct cache entries.
   ```

   Only the first of the four `Changed` bullets gets the `Tracked as DONE-014-0.0.6 in KANBAN.md` clause (per the spec-013 pattern: the spec-013 file has `Tracked as DONE-012-0.0.6 …` on the first `Changed` bullet and not on the wire-format one). The subsequent three `Changed` bullets in spec-014's set are mechanically related to the same card and don't need the trailing reference repeated.

   **Verbatim-text fidelity check.** Each of the four bullets above is **character-for-character** the spec-line text minus the leading `- \`Changed\`: ` prefix. Spec line 256 begins `- \`Changed\`: \`registry.register\` now returns …` — Worker 2 strips the `- \`Changed\`: ` envelope (the spec-side framing telling Worker 1 "this is a Changed entry") and lands the post-envelope text under `### Changed` as a regular Markdown bullet. Worker 3 verifies via diff against spec lines 256-259.

**`### Notes` block.** No new `Notes` entry is required by the spec. The existing `Notes` entry about the `BigInt` deprecation suppression stays unchanged.

**CHANGELOG sanity check (per BUILD.md Worker 3 doc-sanity rule + spec line 60-61).** After both `Edit`s land:
- The `[Unreleased]` section now contains five `Added` entries (four existing + one new `Meta.primary`).
- The `[Unreleased]` section now contains six `Changed` entries (two existing + four new).
- The `### Removed` and `### Fixed` headings are absent from `[Unreleased]` — Slice 6 does not introduce either, and the spec authorizes `Added` and `Changed` only (spec lines 255-259). Worker 2 does NOT add empty `### Removed` or `### Fixed` headings.
- No version-line edit in CHANGELOG; `[Unreleased]` stays `[Unreleased]` (the maintainer cuts the `[0.0.6]` release separately; this build does not release).

### Test additions / updates

**None.** This slice is doc/release-metadata only — no source-of-truth contract change, no behavior change, no test pinned by the spec checklist. Spec line 176-260 names zero tests. Worker 2's build report's `### Tests added or updated` section should read `None — slice 6 is doc/release-metadata only.`.

This is consistent with the spec-013 Slice 6 build artifact and with BUILD.md's standing "tests in the same change as the code" rule — there is no code in this slice for tests to pin.

### Implementation discretion items

These are the only points Worker 2 has resolved-stylistic choices to make. Worker 1 has decided each can go either way:

1. **Edit order within the commit.** Worker 2 may apply the seven file edits in any order (the changes are independent — no compile-time or render-time ordering risk between doc files). The build report's `### Files touched` section should still list all files actually edited.
2. **`CHANGELOG.md` `Tracked as …` clause placement.** Worker 1's plan recommends adding `Tracked as \`DONE-014-0.0.6\` in [\`KANBAN.md\`](KANBAN.md).` to the first `Changed` bullet only (mirroring the spec-013 pattern at `CHANGELOG.md:21` / `:27`). Worker 2 may instead omit the clause if the spec-013 pattern was inconsistent across prior cards — confirm via `grep -c "Tracked as DONE-" CHANGELOG.md` and match whichever pattern is more prevalent. If both patterns exist, pick the spec-013-Slice-6 convention; that's the immediate predecessor.
3. **`docs/FEATURES.md` `Meta.primary` rewrite body wording.** The exact prose in Step 3 above is Worker 1's recommended phrasing — anchored in spec Decision 5 and the verbatim KANBAN body's "Design notes". Worker 2 may rephrase **sentence-by-sentence** as long as: (a) the four ambiguity rules from spec lines 485-489 are all present, (b) the three-helper vocabulary (`primary_for` / `types_for` / `models_with_multiple_types`) appears verbatim, (c) the already-shipped-override clause (spec lines 245-252) is preserved, (d) the **See also:** anchors point at existing FEATURES anchors. Worker 2 may NOT replace the description with a one-line summary — the entry needs the same depth as the predecessor `BigInt` entry at `docs/FEATURES.md:166-170` (~3 lines of body) or the `DjangoType` entry at `docs/FEATURES.md:358-392` (~30+ lines).
4. **`TODAY.md` new-section heading wording.** The Step 5 prose uses `## Shipped capabilities available but not currently demonstrated in fakeshop` as the new section heading. Worker 2 may pick an alternative phrasing — `## Shipped but not demonstrated in fakeshop`, `## Shipped today, not yet in fakeshop`, etc. — provided the new heading matches the file's existing `##`-level section convention (the file's existing sections are `## Current fakeshop state`, `## What's in examples/fakeshop/...`, etc., all at `##` level). The body content stays as specified.
5. **`docs/TREE.md` line 238 wording.** The Step 4 prose suggests `# model→type registry (Meta.primary shipped in 0.0.6)`. An equally valid alternative is `# model→type registry (gains Meta.primary at alpha — shipped 0.0.6)`. The contract is that "(gains Meta.primary at beta)" — the current stale wording — is replaced with anything that reflects "Meta.primary has shipped". Worker 2 picks.

---

### Notes for Worker 1 (spec reconciliation)

These are surfaced for Worker 1's final-verification pass; they are NOT spec-issuing blockers at the planning stage.

1. **Spec status line (spec line 4).** Reads `Status: draft (revision 6, post-TODO-anchor review).` Slices 1-5 are `final-accepted`. After Slice 6 closes, the spec's `draft` framing is technically stale. Per spec line 260 the spec stays at its working location with no archival default, so the lifecycle hasn't reached "shipped"; "draft" may still be the right word for "this is a working-copy spec, not an archived one". Recommendation for final verification: leave as-is; the spec's `Status:` line is about revision history, not build status — flagged for the maintainer's awareness only.
2. **Spec line 6 (Predecessors).** References `KANBAN.md` card `WIP-ALPHA-014-0.0.6`. After Slice 6 the card becomes `DONE-014-0.0.6`. The spec's predecessor reference is **historically accurate** (the spec predecessor _was_ `WIP-ALPHA-014-0.0.6`) so this is intentionally stale-by-design. No edit; left here as awareness.
3. **`CHANGELOG.md` `## Versioning` section (lines 7-15).** No edits needed — the section describes the alpha/beta/stable cadence and is independent of any specific card. Confirmed at planning time. Flagged because changelog edits are unusually scoped this slice; the standing prohibition is overridden only for the `[Unreleased]` `Added`/`Changed` work.

### Public-surface check (Worker 3 anticipation)

The slice does NOT touch `django_strawberry_framework/__init__.py`. No new public exports are introduced — `Meta.primary` is a `Meta`-key contract (read by `__init_subclass__`), not a re-exported symbol. The three new registry helpers (`primary_for`, `types_for`, `models_with_multiple_types`) are accessible via `from django_strawberry_framework.registry import registry; registry.primary_for(model)` and are NOT added to the top-level `__init__.py` `__all__`. Worker 3's public-surface diff (`git diff -- django_strawberry_framework/__init__.py`) should be empty for this slice.

### Documentation / release sanity (Worker 3 anticipation)

Slice 6 is the canonical doc/release-metadata slice; Worker 3's BUILD.md doc-sanity rule (lines 312-323) fires fully here. Pre-confirmations Worker 3 will check:

- **Version strings match.** Already at `0.0.6` from Slice 5; no version-string edits in Slice 6.
- **Shipped/planned statuses match the post-Slice-6 state.** `Meta.primary` flips from `planned for 0.0.6` to `shipped (0.0.6)` in both the Index row (`docs/FEATURES.md:85`) and the `## Meta.primary` entry (line 653). The `DjangoType` alpha-constraint bullet (line 387) is removed; the shipped-capability list (line 374-383) gains the new positive bullet.
- **Moved KANBAN cards appear exactly once.** The `WIP-ALPHA-014-0.0.6` card body at `KANBAN.md:83-124` is deleted; a new `DONE-014-0.0.6` card body appears at the DONE-column insertion point (immediately above `DONE-013-0.0.6` at line 1656). Worker 3 confirms `grep -c "ALPHA-014-0.0.6" KANBAN.md` returns 0 (the `WIP-ALPHA-014` literal is gone) and `grep -c "DONE-014-0.0.6" KANBAN.md` returns ≥1 (the new card present).
- **Markdown links resolve.** The new `docs/FEATURES.md` cross-references (`#metaprimary`, `#djangotype`, `#djangooptimizerextension`, `#finalize_django_types`, `#configurationerror`, `#metamodel`) all point at existing anchors. Worker 3 verifies via `grep "^## " docs/FEATURES.md` against the new anchor list.
- **Verbatim text diff.** Worker 3 runs `diff <(awk 'NR>=188 && NR<=252' docs/spec-014-meta_primary-0_0_6.md | sed 's/^    //') <(<KANBAN-extraction>)` to confirm character-for-character fidelity of the verbatim KANBAN body.
- **No stale "coming soon" / "planned" wording.** Worker 3 greps `docs/README.md`, `docs/FEATURES.md`, `TODAY.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` for `planned for \`0.0.6\``, `Coming in \`0.1.0\``, and `gains Meta.primary at beta` — all should be absent (or, where still present, intentionally still about other features that haven't shipped yet, like `WIP-ALPHA-015-0.0.6`).
- **Active-spec archival.** Confirmed not planned per spec line 260; nothing for Worker 3 to verify there.
- **Fence backtick count for verbatim drop-ins.** Spec line 187's outer 3-backtick fence is safe because the inner body has no backtick fences (planning-time `grep` confirmed). Worker 3 spot-checks by running `grep -c '^\`\`\`' KANBAN.md` before and after the edit and confirming the count increases by zero (the dropped-in body has no inner fences).

---

## Build report (Worker 2)

### Files touched

- `README.md` — no-op; confirmed line 45 already reads `0.0.6` via `grep -n "0\.0\.6" README.md`. No edit applied.
- `docs/README.md` — two edits per Step 2 of the plan: added the `Meta.primary` bullet to the "Shipped today" list (after the `auto` re-export bullet) and removed the stale `Meta.primary` bullet from the "Coming in `0.1.0`" block. The version line at `docs/README.md:89` (`**Shipped today** (`0.0.6`)`) already reflected `0.0.6` — no edit needed there.
- `docs/FEATURES.md` — three edits per Step 3 of the plan: (1) Index row at line 85 flipped from `planned for `0.0.6`` to `shipped (`0.0.6`)`; (2) `DjangoType` alpha-constraint bullet removed from the "Current alpha constraints" block; matching positive bullet `multiple `DjangoType`s per Django model supported via [`Meta.primary`](#metaprimary)` added to the "Shipped capability" list immediately after the `abstract / intermediate base support` bullet; (3) `## Meta.primary` entry body rewritten per the plan's recommended phrasing — three-helper vocabulary (`primary_for` / `types_for` / `models_with_multiple_types`) appears verbatim, four ambiguity rules from Decision 5 are present, already-shipped-override clause preserved, four `See also:` anchors point at existing FEATURES anchors (`#metamodel`, `#djangotype`, `#finalize_django_types`, `#configurationerror`).
- `docs/TREE.md` — one edit per Step 4 of the plan: line 238 stale wording `(gains Meta.primary at beta)` replaced with `(Meta.primary shipped in 0.0.6)`. Current-on-disk tree at line 199 left untouched per plan.
- `TODAY.md` — one edit per Step 5 of the plan: new section `## Shipped capabilities available but not currently demonstrated in fakeshop` appended at file tail (after the existing "What the fakeshop example should wait for" section). Section body explains `Meta.primary` is fully test-covered in the package suite but not exercised in fakeshop's single-`DjangoType`-per-model example schemas. Includes the deep link `[docs/FEATURES.md#metaprimary](docs/FEATURES.md#metaprimary)`.
- `KANBAN.md` — three edits per Step 6 of the plan: (a) "In progress" summary bullet at former line 49 (`WIP-ALPHA-014-0.0.6 — Multiple DjangoTypes per model with Meta.primary` summary) deleted; (b) the `0.0.6` shipped-progress sentence updated to add `DONE-014-0.0.6` and to drop "the two WIP cards" framing in favor of "`WIP-ALPHA-015-0.0.6` remains to complete the `0.0.6` patch"; (c) the entire `### WIP-ALPHA-014-0.0.6` card body (former lines 83-124) deleted and a new `### DONE-014-0.0.6 — Multiple DjangoTypes per model with `Meta.primary`` card body inserted immediately above the existing `### DONE-013-0.0.6` heading. The new DONE-014 body is the verbatim spec lines 188-252 with the 4-space leading indent stripped; verified character-for-character via `diff <(awk 'NR>=188 && NR<=252' docs/spec-014-meta_primary-0_0_6.md | sed 's/^    //') <(awk '/^### DONE-014-0.0.6/,/^### DONE-013-0.0.6/' KANBAN.md | sed '$d' | sed '$d')` which produced empty output.
- `CHANGELOG.md` — two edits per Step 7 of the plan (spec-pinned permission overriding `AGENTS.md`'s default prohibition, spec line 254): one new `Added` bullet between the existing `ArrayField` bullet and the `### Changed` heading; four new `Changed` bullets between the existing `PositiveBigIntegerField` wire-format bullet and the `### Notes` heading. Verbatim content from spec lines 255-259 with the leading `- `Added`: ` / `- `Changed`: ` envelope stripped. Trailing `Tracked as `DONE-014-0.0.6` in [`KANBAN.md`](KANBAN.md).` clause attached to the new `Added` bullet (mirrors spec-013 Slice 6 pattern: `CHANGELOG.md:21`) and to the first `Changed` bullet only (mirrors `CHANGELOG.md:27`'s spec-012 entry — the subsequent three `Changed` bullets are mechanically related and do not repeat the trailing reference per the plan's discretion item #2 / spec-013 precedent).

### Tests added or updated

None; documentation/release-metadata slice. Spec lines 176-260 pin zero tests for Slice 6. Slice 5 was the no-op verification gate; Slice 6 ships docs + KANBAN + CHANGELOG + release-metadata edits only — no code-of-truth contract change, no behavior change, no test scope.

### Validation run

- `uv run ruff format .` — pass. `100 files left unchanged` (markdown files are not formatted by ruff; the `.py` surface in the repo was already clean). The standing `COM812` formatter-conflict warning printed but is informational only and unrelated to this slice.
- `uv run ruff check .` — 2 pre-existing errors in `scripts/check_spec_glossary.py` (the same Slice 1 out-of-slice drift Worker 2 noted in `worker-memory/worker-2.md:13`). These are unrelated to Slice 6's changes and out of slice scope. No new errors introduced by this slice.
- Focused `pytest` — not run; slice has no test changes and AGENTS.md / START.md / BUILD.md "Coverage is the maintainer's gate" pin the standing rule that Worker 2 does not run `pytest` on doc-only edits.
- Grep verifications (Worker 1 plan + Worker 3 anticipation rules):
  - `grep -n "0\.0\.6" README.md` — line 45 reads `0.0.6`. Confirmed at start of pass; no edit. Confirmed unchanged at end of pass.
  - `grep -nE "^### WIP-ALPHA-014-0\.0\.6|^### DONE-014-0\.0\.6|^### DONE-013-0\.0\.6" KANBAN.md` — returns `1612:### DONE-014-0.0.6 …` and `1678:### DONE-013-0.0.6 …`. The `WIP-ALPHA-014` heading literal is gone from `KANBAN.md`; DONE-014 sits above DONE-013 in reverse-chronological order as the plan required.
  - `grep -c "DONE-014-0.0.6" KANBAN.md` — returns `2` (the new card heading + one cross-reference in the in-progress summary sentence). Plan-anticipated check passes.
  - `grep -n "WIP-ALPHA-014-0.0.6" KANBAN.md` — returns 2 lines: `406:- Decide whether the input-type factory's namespace shares the `TypeRegistry` or has its own (interacts with `WIP-ALPHA-014-0.0.6` and the `Meta.primary` design).` and `574:- `WIP-ALPHA-014-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution.`. These are forward references in TODO cards (TODO-ALPHA-016 / TODO-ALPHA-019 region) that pointed at this card by its prior identity — left unedited (the spec/plan do not authorize rewriting cross-references in unrelated cards). Surfaced in `### Notes for Worker 1 (spec reconciliation)`.
  - `grep -n "planned for \`0.0.6\`|Coming in \`0.1.0\`|gains Meta.primary at beta" docs/README.md docs/FEATURES.md TODAY.md docs/TREE.md KANBAN.md CHANGELOG.md` — returns three intentional matches: `docs/README.md:103` (the "Coming in `0.1.0`" section heading itself — still valid, the section now lists `DjangoListField` etc. after `Meta.primary` was removed); `docs/FEATURES.md:101` (`Scalar field override semantics` Index row — `WIP-ALPHA-015-0.0.6` territory, out of scope); `docs/FEATURES.md:887` (the matching `## Scalar field override semantics` body — same out-of-scope card). No stale `Meta.primary` wording remains in any of the six surfaces this slice touched.
  - Verbatim KANBAN diff: `diff <(awk 'NR>=188 && NR<=252' docs/spec-014-meta_primary-0_0_6.md | sed 's/^    //') <(awk '/^### DONE-014-0.0.6/,/^### DONE-013-0.0.6/' KANBAN.md | sed '$d' | sed '$d')` — empty output. The 65-line body matches the spec character-for-character after 4-space indent strip.

### Implementation notes

- **`docs/FEATURES.md` `Meta.primary` rewrite — adopted Worker 1's recommended phrasing verbatim.** The plan offered Worker 2 sentence-by-sentence discretion (discretion item #3); the recommended prose already satisfied all four required ingredients (ambiguity rules, three-helper vocabulary, already-shipped-override clause, `See also:` anchors), and freelancing would only have created prose drift between FEATURES and the KANBAN body. Picked direct adoption.
- **`CHANGELOG.md` `Tracked as DONE-014` trailing clause placement.** Followed the plan's recommendation (discretion item #2): first `Added` bullet and first `Changed` bullet get the trailing reference; the subsequent three `Changed` bullets do not. Verified via `grep -c "Tracked as DONE-" CHANGELOG.md` that the surrounding pattern is consistent (the spec-013 / spec-012 entries already follow this shape).
- **`docs/TREE.md` line-238 wording — picked the plan's first option.** Discretion item #5 offered an alternative phrasing `(gains Meta.primary at alpha — shipped 0.0.6)`; chose the shorter `(Meta.primary shipped in 0.0.6)` because the current-tree comment at line 199 already drops the milestone-tag framing for shipped features (`+ iter_types() public iterator`), and consistency between the two trees' comment-style on shipped features is preferable.
- **`TODAY.md` new-section heading wording.** Adopted Worker 1's recommended `## Shipped capabilities available but not currently demonstrated in fakeshop` (discretion item #4). The phrasing is the natural docs-side complement to the existing `## What the fakeshop example should wait for` section and lets future shipped-but-not-demonstrated features (e.g., a future `Meta.aggregate_class` if fakeshop hasn't grown a demo) append to the same list.
- **Edit order within the commit.** Discretion item #1 said edit order doesn't matter. Applied edits in spec-checklist file order (README → docs/README → FEATURES → TREE → TODAY → KANBAN → CHANGELOG) to match the plan's reading order and keep the build report's `Files touched` section parallel to the plan.
- **`KANBAN.md` insertion mechanics.** Did the three KANBAN edits in this order: (a) line-49 deletion + line-51 shipped-progress sentence rewrite via a single `Edit` call (the two changes were adjacent so one combined edit was cleaner than two separate calls); (b) the 42-line WIP-014 card body deletion via an `Edit` that replaced the entire block with the existing-and-unchanged `### WIP-ALPHA-015-0.0.6` heading line; (c) the new DONE-014 body insertion via an `Edit` anchored on the unique `### DONE-013-0.0.6 — Deferred scalar conversions` heading literal. All three edits succeeded on first try.

### Notes for Worker 3

- **Shadow file usage:** none. The slice is doc-only; `scripts/review_inspect.py` is not applicable (BUILD.md "When to run the helper" applies to `.py` files only).
- **Forward `WIP-ALPHA-014-0.0.6` references in other KANBAN cards (lines 406, 574 of current `KANBAN.md`).** These are TODO cards (`TODO-ALPHA-016`, `TODO-ALPHA-019`) that cross-reference this card by its pre-rename identity. The plan does not authorize editing them; the spec body (lines 185-186) only covers moving the card itself, not rewriting cross-references in unrelated cards. Worker 1 may want to surface this for a future docs-hygiene pass — these references should arguably be rewritten to `DONE-014-0.0.6` for accuracy, but that is out of Slice 6 scope.
- **Spec line 4 `Status: draft (revision 6, post-TODO-anchor review).`** Worker 1's plan flagged in the planning artifact that this line is technically stale post-slice-6 but is about the spec's revision history, not the build status. Per spec line 260 (specs stay at their working location with no archival default), the lifecycle is intentional. Worker 3 should not reject the slice over the `draft` framing; it's a flag for Worker 1's final-verification pass only.
- **Verbatim diff check.** Already run by Worker 2 (see `### Validation run`). Worker 3 may re-run for review-pass sanity but it is expected to produce empty output.
- **Public-surface check.** No edits to `django_strawberry_framework/__init__.py` or any source file — Worker 3's `git diff -- django_strawberry_framework/__init__.py` will be empty as anticipated by the plan.
- **CHANGELOG sanity items already pre-checked by Worker 2.** `[Unreleased]` now has five `Added` entries and six `Changed` entries (per the plan's anticipation under `### Documentation / release sanity (Worker 3 anticipation)`). `### Removed` / `### Fixed` headings are absent from `[Unreleased]` per spec line 255-259 which only authorizes `Added` and `Changed`. No version-line edits in CHANGELOG.

### Notes for Worker 1 (spec reconciliation)

1. **Forward `WIP-ALPHA-014-0.0.6` references at `KANBAN.md:406` and `KANBAN.md:574`.** Two TODO cards in unrelated regions of the KANBAN cite this card by its pre-rename identity (`WIP-ALPHA-014-0.0.6`). The plan and the spec checklist (lines 185-186) explicitly cover the card movement and body replacement but do not authorize rewriting cross-references in unrelated cards. Worker 2 left them as-is. Worker 1 may want to either (a) extend Slice 6 with a small follow-up edit to rewrite these to `DONE-014-0.0.6`, (b) defer it to a separate docs-hygiene pass, or (c) accept as-is on the rationale that the references are historically accurate (the spec author who wrote them was correctly citing the card's then-current identity). Recommendation: accept as-is; the rewrite is a docs-hygiene nit, not a correctness issue.
2. **Spec line 4 `Status: draft (revision 6, post-TODO-anchor review).`** Same flag the planning artifact carried. Recommendation: leave; the `draft` framing is about revision history, not build lifecycle. If maintainer requests a post-merge flip to `shipped (0.0.6)`, that is Worker 1's call during final verification.
3. **`docs/FEATURES.md:887` `Scalar field override semantics` entry is still `planned for 0.0.6`.** This is the `WIP-ALPHA-015-0.0.6` card's entry, not our card's — out of Slice 6 scope, but if Worker 1 wants to confirm `WIP-ALPHA-015-0.0.6`'s version target before the `0.0.6` patch closes, that is a separate question. Not blocking this slice.
4. **No spec edits proposed.** The implementation matched the plan's contract on every edit; no implementation surprises surfaced a spec gap.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### Stale "DjangoType contract gaps" reference at `KANBAN.md:68`

The Snapshot section at `KANBAN.md:67-69` still lists `multiple DjangoType\`s per model / Meta.primary` as one of several "DjangoType contract gaps" remaining. With this slice shipping `Meta.primary`, the bullet is now stale.

```KANBAN.md:67:69
- Several DjangoType contract gaps remain:
  - multiple `DjangoType`s per model / `Meta.primary`
  - stable consumer override semantics for **scalar** fields (the foundation slice pinned the contract for relation fields only)
```

Why it matters: BUILD.md Worker 3 doc-sanity rule explicitly checks "no obsolete 'coming soon' / 'planned' / old-version wording remains in files the slice deliberately updated." `KANBAN.md` was deliberately updated by Slice 6, and the Snapshot list still claims this gap remains. Recorded as Low rather than Medium because the gap-list bullet describes a contract gap, not an explicit "planned"/"coming soon" word; the spec checklist (lines 177-185) did not pin a Snapshot-section edit, and the plan's "discretion to skip cross-references in unrelated regions" rationale partially extends here. Recommended change: remove the `multiple DjangoType\`s per model / Meta.primary` sub-bullet from `KANBAN.md:68`. Worker 1 may weigh deferring to a docs-hygiene pass.

### DRY findings

- `Meta.primary` wording is consistent across the five sites (Worker 2's plan and build report were explicit about this and the result matches):
  - `docs/FEATURES.md:85` Index — `shipped (\`0.0.6\`)`.
  - `docs/FEATURES.md:384` shipped-capability bullet under `## DjangoType` — `multiple DjangoType\`s per Django model supported via [\`Meta.primary\`](#metaprimary)`.
  - `docs/FEATURES.md:651-672` `## Meta.primary` body — three-helper vocabulary (`primary_for(model)`, `types_for(model)`, `models_with_multiple_types()`), four ambiguity rules from spec Decision 5, already-shipped-override clause, four `See also:` anchors all resolving.
  - `docs/README.md:101` Shipped-today bullet — single-line "via explicit primary-flag opt-in".
  - `TODAY.md:265` — single-line entry under the new "Shipped capabilities available but not currently demonstrated in fakeshop" section, deep-linked to `docs/FEATURES.md#metaprimary`.
  - `CHANGELOG.md:25` `Added` line uses the verbatim three-helper trio.
  - `KANBAN.md:1612-1675` DONE-014 body uses the same helper trio verbatim (per spec lines 198-199).
- Three-helper vocabulary (`primary_for`, `types_for`, `models_with_multiple_types`) appears identically wherever the registry surface is described. No drift.
- "Tracked as `DONE-014-0.0.6` in `KANBAN.md`" trailing clause is attached to the `Added` bullet and the first `Changed` bullet only — matches the spec-013 / spec-012 precedent in the same `CHANGELOG.md`.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns empty. The slice does not change `__all__` or the re-export list. `Meta.primary` is a `Meta`-key contract (consumed by `__init_subclass__`); the three new registry helpers stay on the `registry` instance rather than the top-level `django_strawberry_framework` namespace. Spec line 367 of the plan anticipated this; verified.

### CHANGELOG sanity

- Version line: spec authorizes `[Unreleased]` `Added`/`Changed` entries (spec line 254). `CHANGELOG.md` `[Unreleased]` heading is intact at line 19; no `[0.0.6]` heading is cut here (the maintainer does that at release time). `pyproject.toml` `version = "0.0.6"` and `django_strawberry_framework/__init__.py` `__version__ = "0.0.6"` confirmed in sync.
- Headings: spec line 255-259 authorizes only `Added` and `Changed`. `[Unreleased]` block uses `### Added`, `### Changed`, `### Notes` — `Notes` is pre-existing from prior `0.0.6` cards (the `BigInt` deprecation note); the slice did not introduce empty `### Removed` or `### Fixed` headings. Headings used are the ones the active spec authorizes.
- Wording fidelity: diffed the five new `[Unreleased]` lines against spec lines 255-259 with the `- \`Added\`: ` / `- \`Changed\`: ` envelope stripped. Each new bullet is character-for-character the spec text plus the optional trailing `Tracked as DONE-014-0.0.6 in [\`KANBAN.md\`](KANBAN.md)` clause on bullets 1 (`Added`) and 1 (`Changed`). Trailing-clause placement mirrors the spec-013 / spec-012 entries already in `CHANGELOG.md:21` and `:28`.
- Over/understatement check: every CHANGELOG bullet is matched 1:1 to actual implementation work landed in Slices 1-5 (verified against the artifacts `bld-slice-1` through `bld-slice-5`). Nothing overstates (e.g., no claim of a feature that hasn't shipped) or understates (e.g., omission of the optimizer cache-key change).

### Documentation / release sanity

- **Version strings match.** `pyproject.toml:version = "0.0.6"`, `__init__.py:__version__ = "0.0.6"`. `README.md:45` reads `**\`0.0.6\`, single-maintainer, alpha-quality.**`. `docs/README.md:89` reads `**Shipped today** (\`0.0.6\`):`. `docs/FEATURES.md:85` index row reads `shipped (\`0.0.6\`)`. All five surfaces align.
- **Shipped/planned statuses correct.** `Meta.primary` flipped to `shipped (\`0.0.6\`)` in both the Index row and the entry body. `DjangoType` alpha-constraint bullet removed from line 387 and replaced with a positive shipped-capability bullet at line 384. `docs/TREE.md:238` re-worded from `(gains Meta.primary at beta)` to `(Meta.primary shipped in 0.0.6)`. `docs/README.md` "Coming in `0.1.0`" block no longer mentions `Meta.primary` (removed the stale line). The remaining `planned for \`0.0.6\`` matches in `docs/FEATURES.md:101` and `:887` are the `Scalar field override semantics` entry, which is `WIP-ALPHA-015-0.0.6` territory — out of this slice's scope.
- **KANBAN card movement.** `grep -n "WIP-ALPHA-014-0.0.6" KANBAN.md` returns only the two forward references at lines 406 and 574 (in unrelated TODO cards; see below). The `### WIP-ALPHA-014-0.0.6` card-body heading is gone. The new `### DONE-014-0.0.6` heading is present exactly once at `KANBAN.md:1612`, sitting immediately above `### DONE-013-0.0.6` at `KANBAN.md:1678` — reverse-chronological NNN order is preserved. The In-progress summary at the top no longer lists WIP-014. The `0.0.6` shipped-progress sentence at line 50 cites `DONE-014-0.0.6` correctly.
- **Verbatim KANBAN body diff (character-for-character).** Ran `diff <(awk 'NR>=188 && NR<=252' docs/spec-014-meta_primary-0_0_6.md | sed 's/^    //') <(awk '/^### DONE-014-0.0.6/,/^### DONE-013-0.0.6/' KANBAN.md | sed '$d' | sed '$d')` — empty output. The 65 lines match spec lines 188-252 verbatim with the 4-space indent stripped. Fence rendering is intact: the spec's outer 3-backtick fence with no inner backtick fences in the body (per Worker 1 plan's verification) is dropped in unwrapped, so KANBAN's existing fence count (4 fenced regions, total) is unchanged. No fence collisions.
- **Markdown links resolve.** New `docs/FEATURES.md` cross-references `#metaprimary`, `#djangotype`, `#djangooptimizerextension`, `#finalize_django_types`, `#configurationerror`, `#metamodel` all point at existing `## ...` headings in `docs/FEATURES.md` — confirmed via `grep -E "^## " docs/FEATURES.md`. The new `TODAY.md:265` cross-reference `docs/FEATURES.md#metaprimary` resolves.
- **Active-spec archival not planned.** Spec line 260 explicitly says the spec stays at its working location. The spec file at `docs/spec-014-meta_primary-0_0_6.md` is **not** moved by Slice 6 (verified via `git status --short` — no rename on the spec). Correct.
- **No obsolete wording remains in updated files.** `grep -nE "planned for|coming soon|gains Meta\.primary at beta"` across the six surfaces returns only intentional matches — the `## Index` table's other `planned for` rows for actually-still-planned features (`AggregateSet`, etc.) and the `## Status` legend at `docs/FEATURES.md:15`. None of the matches are stale `Meta.primary` framing.
- **Forward-reference disposition.** Two `WIP-ALPHA-014-0.0.6` mentions at `KANBAN.md:406` and `:574` remain. Both sit in unrelated TODO cards (`TODO-ALPHA-020-0.0.8` filters and `TODO-ALPHA-026-0.0.11` mutations); both reference `WIP-ALPHA-014-0.0.6` for design-context cross-reference (input-type namespace overlap; mutation primary-type resolution dependency). The plan and spec (lines 185-186) only authorize moving and rebuilding this card's own body — they do not authorize editing cross-references in unrelated cards. The two surviving references are **historically accurate** (the spec author who wrote them was correctly citing the card's then-current identity) and do not gate behavior. Accepted as-is per the plan's "spec/plan do not authorize rewriting cross-references in unrelated cards" rationale; surfaced to Worker 1 below as a docs-hygiene candidate.
- **Helper run skipped.** Slice 6 modifies zero `.py` files. BUILD.md "When to run the helper during build" requires `.py`-file context; the helper is not applicable to doc-only edits. Skip recorded here per the standing rule.

### What looks solid

- The verbatim KANBAN body drop-in is mechanically perfect: 4-space indent stripped uniformly across all 65 lines, fence handling correct (no fence collision with inner content), insertion point in reverse-chronological order above `DONE-013-0.0.6`, deletion of the old WIP card body complete and surgical.
- The `docs/FEATURES.md` `Meta.primary` entry rewrite captures all four spec-Decision-5 ambiguity rules in the same order as the spec, uses the three-helper vocabulary verbatim, preserves the already-shipped-override clause, and adds two new `See also:` anchors (`#finalize_django_types`, `#configurationerror`) that strengthen the discoverability of the contract. The body is the right length — substantive (~25 lines including ambiguity rules + registry surface + override-preservation note) for a key behavioral contract.
- The `DjangoType` alpha-constraint replacement (remove negative bullet from "Current alpha constraints", add positive bullet to "Shipped capability") is the cleanest possible shape — readers visiting the `DjangoType` entry see the contract as a positive capability, not a constraint that's "promoted by Meta.primary".
- `TODAY.md`'s new "Shipped capabilities available but not currently demonstrated in fakeshop" section creates a natural docs-side complement to the existing "What the fakeshop example should wait for" section. Future shipped-but-not-demonstrated features (e.g., a future `Meta.aggregate_class` if fakeshop hasn't grown a demo) can append to the same list.
- The CHANGELOG `Added` and four `Changed` bullets, with the `Tracked as DONE-014-0.0.6` clause on the first `Added` and first `Changed` only, mirror the spec-013 / spec-012 precedent exactly — Worker 2 picked the right discretion item resolution.
- `docs/TREE.md:238` re-wording from "(gains Meta.primary at beta)" to "(Meta.primary shipped in 0.0.6)" is the minimal correct fix. The current-on-disk tree at line 199 was correctly left untouched (the `Meta.primary` contract is a `Meta`-key, not a registry-API addition that needs a separate inline comment).

### Temp test verification

None created or needed. Slice 6 is doc-only; no behavior to pin via temp tests.

### Notes for Worker 1 (spec reconciliation)

1. **`KANBAN.md:68` stale "DjangoType contract gaps" bullet.** The Snapshot section still lists `multiple DjangoType\`s per model / Meta.primary` as a remaining contract gap. Slice 6 deliberately updated `KANBAN.md`, so BUILD.md doc-sanity rule applies. Recorded as Low rather than Medium because the spec checklist (lines 177-185) did not pin a Snapshot-section edit. Recommendation: either extend Slice 6 to remove the sub-bullet, or accept on the rationale that the plan did not call out the Snapshot section. The remaining sibling bullet about scalar-field override semantics correctly stays (that's `WIP-ALPHA-015-0.0.6`).
2. **Forward `WIP-ALPHA-014-0.0.6` references at `KANBAN.md:406` and `:574`.** Two TODO cards (filters, mutations) cite this card by its pre-rename identity for design-context dependency. The plan and spec did not authorize editing cross-references in unrelated cards; Worker 2 left them. They are historically accurate. Recommendation: accept as-is or defer to a separate docs-hygiene pass; not blocking.
3. **Spec line 4 `Status: draft (revision 6, post-TODO-anchor review).`** Worker 2's notes flagged this; spec line 260 says the spec stays at its working location, so "draft" is about revision history not lifecycle. Not blocking; flag for maintainer awareness only.
4. **`docs/FEATURES.md:101` and `:887` — `Scalar field override semantics` is still `planned for \`0.0.6\``.** That's `WIP-ALPHA-015-0.0.6`, not this card. Out of Slice 6 scope, but Worker 1 may want to confirm `0.0.6` is still the right target version for that card before the patch closes (independent question).
5. **No spec edits proposed by this review.** Implementation matched the plan's contract on every edit; no spec gap surfaced. The one Low finding is a docs-hygiene item the plan did not pin, not a spec issue.

### Review outcome

`review-accepted` — every High/Medium finding is `None`; the single Low finding at `KANBAN.md:68` is recorded with a recommended fix and surfaced to Worker 1 for final-verification weighing. The slice delivers what spec lines 176-260 require: verbatim KANBAN body drop-in (character-for-character), Index status flip, FEATURES entry rewrite, alpha-constraint removal + shipped-capability bullet addition, `TODAY.md` callout for shipped-but-not-demonstrated, `docs/TREE.md` comment fix, `docs/README.md` shipped/coming-soon swap, and CHANGELOG `Added` + `Changed` entries (verbatim, spec lines 255-259). Public surface unchanged. DRY across five sites verified. No source/test regressions possible (zero `.py` edits).

---

## Final verification (Worker 1)

### DRY check across this slice and prior accepted slices

- **No new code duplication.** Slice 6 modifies zero `.py` files (`git diff --stat` confirms only `CHANGELOG.md`, `KANBAN.md`, `TODAY.md`, `docs/FEATURES.md`, `docs/README.md`, `docs/TREE.md` plus the spec on the doc-side of this slice; the `.py` changes in the same working tree are from Slices 1-4, accepted earlier). For a doc-only slice the DRY check is vacuously clean on the code dimension.
- **`Meta.primary` description vocabulary consistency across the build.** The three-helper trio (`primary_for(model)` / `types_for(model)` / `models_with_multiple_types()`) appears identically wherever the registry surface is described — verified at six post-slice surfaces:
  - `docs/FEATURES.md:664` — Registry-surface paragraph in the `## Meta.primary` entry uses the three helpers verbatim.
  - `CHANGELOG.md:25` (`Added`) and `:31` (`Changed`'s `iter_types` bullet) — same trio.
  - `KANBAN.md:1622-1623` — DONE-014 body's "New registry surface" bullet uses the same trio verbatim.
  - Spec lines 255 and 257 — original verbatim source.
  - `docs/README.md:101` — single-line nod ("via explicit primary-flag opt-in") intentionally omits the trio (the full surface lives in FEATURES), matching the plan's DRY discipline.
  - `TODAY.md` — deep-links to `docs/FEATURES.md#metaprimary` rather than restating the surface.
- **`DjangoType` alpha-constraint removal consistency.** Confirmed the bullet `multiple DjangoType\`s per Django model supported via [\`Meta.primary\`](#metaprimary)` lives once in the "Shipped capability" list at `docs/FEATURES.md:384`; the matching negative bullet ("one `DjangoType` per Django model") is gone from the "Current alpha constraints" block at `docs/FEATURES.md:386-388` (only the deferred-relation-cardinality bullet remains). Worker 3 Low finding about the parallel stale Snapshot bullet at `KANBAN.md:68` was the **last** such consistency gap; addressed in this final-verification pass — see `### Summary` below.
- **Ambiguity-rule statement vocabulary.** The four-row ambiguity rule (single-no-primary allowed, multiple-one-primary allowed, multiple-two-or-more-primary rejected at registration, multiple-none-primary rejected at finalize) appears at `docs/FEATURES.md:659-662` and at `KANBAN.md:1627-1631`; the wording matches the spec source (Decision 5, spec lines 483-489) without drift. The CHANGELOG `Changed` bullets at `CHANGELOG.md:27-32` use the same `register()` and `get()` semantic wording the spec authorized.
- **No new code duplication introduced** — this is a doc slice, vacuously clean per BUILD.md's "DRY scan" gate at the integration pass.

### Existing tests still pass

- Command: `uv run pytest tests/ --no-cov`
- Result: **610 passed, 3 skipped, 2 warnings in 10.50s**. The two `RuntimeWarning`s are pre-existing model-re-registration noise from `tests/types/test_converters.py` — unrelated to Slice 6 (no `.py` edits in this slice). The three skips are pre-existing as well.
- This re-confirms that the full Slice 1-6 working tree is green: prior slices' code changes plus Slice 6's doc-only changes leave no regression.

### Spec reconciliation

- **Spec stays at working location.** Confirmed `docs/spec-014-meta_primary-0_0_6.md` exists at its planning path (`ls -la` returned the file at `116374` bytes on 2026-05-18). Per spec line 260 and BUILD.md "Specs stay at their working location after closeout", no archival is planned. **No spec edit for archival.**
- **Worker 3 Low finding (`KANBAN.md:68`).** Took Option A as recommended by the task: removed the stale sub-bullet `multiple DjangoType\`s per model / Meta.primary` from the Snapshot section's "Several DjangoType contract gaps remain" list. The remaining sibling sub-bullets stay accurate (scalar-field override semantics, choice-enum naming, deferred scalar conversions — though the latter is already shipped as `DONE-013-0.0.6`, addressing that is out of Slice 6 scope and is a separate docs-hygiene follow-up). The edit is a doc-only one-bullet removal; no test impact, no spec edit needed.
- **Forward `WIP-ALPHA-014-0.0.6` references at `KANBAN.md:406` and `:574`.** Both sit inside unrelated TODO cards (`TODO-ALPHA-020-0.0.8` filters input-type namespace; `TODO-ALPHA-026-0.0.11` mutations primary-type resolution). Both reference this card for design-context dependency by its **then-current** identity. Worker 3 accepted them as historically accurate. **Confirmed accepted**: the spec/plan only authorize moving this card's own body — they do not authorize rewriting cross-references in unrelated cards, and the references are factually correct from the perspective of the spec author's then-current view. Recommended to address in a separate docs-hygiene pass if the maintainer wants present-tense accuracy across all KANBAN cross-references.
- **Spec line 4 `Status: draft (revision 6, post-TODO-anchor review).`** Still about revision history, not lifecycle. Per spec line 260, the spec stays at its working location with no archival default — "draft" is correctly framing the spec as "working copy" rather than "archived". **No edit.**
- **Spec line 6 (Predecessors).** References `WIP-ALPHA-014-0.0.6` for historical accuracy (the spec _was_ a successor to that WIP card before the slice closed). **No edit; intentional historical reference.**
- **No spec edits required.** All spec contracts were satisfied by the slice as planned and built.

### Final status

`final-accepted`.

### Summary

Slice 6 ships the doc and release-metadata surface for the `Meta.primary` build cycle. Across six doc files plus the `CHANGELOG.md` `[Unreleased]` block, the slice flips `Meta.primary` from `planned for 0.0.6` to `shipped (0.0.6)`, removes the `DjangoType` alpha-constraint "one type per model" bullet and replaces it with a positive "multiple types via `Meta.primary`" shipped-capability entry, moves the WIP-014 card from the "In progress" column to the DONE column as `DONE-014-0.0.6` (with a 65-line verbatim body drop-in from spec lines 188-252, character-for-character match), updates the `0.0.6` shipped-progress sentence to credit `DONE-014` alongside `DONE-012` and `DONE-013`, adds a `Meta.primary` callout to `docs/README.md`'s "Shipped today" list (removing the stale "Coming in 0.1.0" mention), creates a new `TODAY.md` "Shipped capabilities available but not currently demonstrated in fakeshop" section, fixes `docs/TREE.md:238`'s stale "gains Meta.primary at beta" comment to "Meta.primary shipped in 0.0.6", and lands one new `Added` plus four new `Changed` entries in `CHANGELOG.md` `[Unreleased]` (verbatim from spec lines 255-259, under the spec-line-254 permission that overrides `AGENTS.md`'s default CHANGELOG prohibition). The three-helper vocabulary (`primary_for`, `types_for`, `models_with_multiple_types`) is consistent across all post-slice surfaces. No source files, no test files, no version strings were edited (Slice 5 already verified all five version-bump sites are at `0.0.6`). One doc-cleanup edit was applied in this final-verification pass to address Worker 3's Low finding at `KANBAN.md:68` (removed the stale "multiple DjangoTypes per model / Meta.primary" sub-bullet from the Snapshot section's "Several DjangoType contract gaps remain" list). 610 tests pass under `uv run pytest tests/ --no-cov`. The build cycle's Slice 6 closes the spec's documentation contract end-to-end.

### Spec changes made (Worker 1 only)

None. The implementation matched the plan's contract on every edit; no spec gap surfaced during final verification. The one doc-cleanup edit at `KANBAN.md:68` is a non-spec doc edit (not a spec file change), documented above under `### Spec reconciliation`.
