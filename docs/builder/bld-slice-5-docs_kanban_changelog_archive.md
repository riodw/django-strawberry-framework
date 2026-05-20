# Build: Slice 5 — Docs, KANBAN, CHANGELOG, archive

Spec reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md` (lines 132-272)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

Slice 5 touches no `.py` files; the helper rule does not apply and is skipped (BUILD.md "When to run the helper during build" triggers on Python files only). The DRY concern here is "no contradictory narratives" across the three audiences this slice writes to (GLOSSARY.md entry body for the developer-glossary audience, KANBAN body for the per-card-history audience, CHANGELOG entries for the release-notes audience). The three texts are intentionally separate voices of the same story and are NOT to be deduplicated.

- **Existing patterns reused.** The "shipped today" / `KANBAN.md` "move WIP → DONE" / `CHANGELOG.md [Unreleased]` shape was established by `DONE-014-0.0.6` (`bld-slice-X` for spec-014 — current artifact directory only retains the Slice 4 / Slice 5 / etc. for spec-015 after spec-014's archive; precedent visible in `KANBAN.md:1609-1673` which is the on-disk DONE-014 body the Slice 5 move mirrors). The verbatim KANBAN body comes from the spec (lines 145-265) and the verbatim CHANGELOG entries come from spec lines 267-271. The `docs/README.md` "Shipped today" bullet pattern lives at `docs/README.md:89-101`. The `TODAY.md` "Shipped capabilities available but not currently demonstrated in fakeshop" subsection lives at `TODAY.md:263-265`.
- **New helpers justified.** None. Slice 5 is mechanical transcription from the spec into the durable docs / KANBAN / CHANGELOG.
- **Duplication risk avoided.** The risk is *narrative drift* between the three audiences, not code duplication. Cross-check against the canonical four-corner docstring on `_consumer_assigned_fields` (which landed in Slice 3, `types/base.py:_consumer_assigned_fields`) — the GLOSSARY.md `Scalar field override semantics` body, the KANBAN body, and the CHANGELOG `Changed` entry for converter bypass should all be consistent with the docstring's framing. Pre-plan grep verified the three voices use consistent terminology (consumer-authoritative, four-corner override matrix, parallel recourses).

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

**Pre-plan grep snapshot (recorded for Worker 2's situational awareness):**

- `README.md:45` → `**\`0.0.6\`, single-maintainer, alpha-quality.**` ✓ (no edit needed)
- `docs/README.md:89` → `**Shipped today** (\`0.0.6\`):` ✓ (no edit needed to the version string itself; a new bullet must be added to the list — see step 2)
- `docs/GLOSSARY.md:20` → `Current package version: \`0.0.6\`.` ✓ (no edit needed to the version line; the index status badge at `:101` and the entry body at `:885-891` both require updates)
- `KANBAN.md:79-119` → `### WIP-ALPHA-015-0.0.6 — Consumer override semantics (scalar fields)` (the body to be moved). Position of `DONE-014-0.0.6` at `KANBAN.md:1609`. Snapshot bullets at `KANBAN.md:49-50` and `KANBAN.md:67` reference the WIP card.
- `CHANGELOG.md:19-37` → `## [Unreleased]` section with existing `### Added`, `### Changed`, and `### Notes` subheadings. The five new entries from the spec append to the existing subheadings (three to `Added`, two to `Changed`).
- `docs/TREE.md:337` → already reads `consumer override contract (four-corner matrix) + definition-order-independent relation finalization`. Spec line 141 says "no further changes needed" and confirmed by grep: no stale "definition-order-independent relation finalization" string remains as a sole description.
- `TODAY.md:263-265` → "Shipped capabilities available but not currently demonstrated in fakeshop" subsection exists; the `Meta.primary` bullet at `:265` is the precedent shape for a new "scalar override semantics" bullet.

**Numbered implementation steps:**

1. **`README.md` (root) — package-version line verify-and-no-op.** Confirm `README.md:45` reads `**\`0.0.6\`, single-maintainer, alpha-quality.**` exactly. No edit needed (current state confirmed at pre-plan grep). The spec line 133 explicitly frames this as "no-op if any prior `0.0.6` card already bumped it" — and the prior `0.0.6` cards (013, 014) did bump it.

2. **`docs/README.md` — "shipped today" version verify + add a scalar-override-symmetry bullet.**
   - Confirm `docs/README.md:89` reads `**Shipped today** (\`0.0.6\`):` exactly. No edit to the version string (already bumped by prior `0.0.6` cards).
   - Add one new bullet to the "Shipped today" list (lines 89-101). Insert position: after the existing `Meta.primary` bullet at `docs/README.md:101`, mirroring the spec's ordering (newest shipped 0.0.6 capability last in the list).
   - Exact bullet text (mechanical wording, mirrors the relation-override path the existing line 95 bullet already names):

     ```
     - annotation-only and `strawberry.field` consumer overrides for scalar fields, symmetric with the shipped relation-override contract (consumer overrides bypass `convert_scalar` validations; `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time)
     ```

3. **`docs/GLOSSARY.md` entries updated.** Multiple edits to GLOSSARY.md, in declared order:

   3a. **Index status badge** at `docs/GLOSSARY.md:101`. Replace `| [Scalar field override semantics](#scalar-field-override-semantics) | planned for \`0.0.6\` |` with `| [Scalar field override semantics](#scalar-field-override-semantics) | shipped (\`0.0.6\`) |`.

   3b. **`Scalar field override semantics` entry body** at `docs/GLOSSARY.md:885-891`. Replace the entire entry (the `## Scalar field override semantics` heading line stays; the body underneath is rewritten). Source-of-truth: spec line 136 prescribes the rewrite contents in narrative form. The rewrite below transcribes the spec's prescription into the FEATURES entry shape used by sibling entries (`Status:` line, body paragraphs, `**See also:**` line). The body must say:

     - **Status line:** Replace `**Status:** planned for \`0.0.6\`.` with `**Status:** shipped (\`0.0.6\`).`
     - **Body paragraphs (rewrite).** The body must cover (in this order, one paragraph per topic, all wording transcribed directly from spec line 136's content into FEATURES-style prose):
       1. The four-corner override matrix landed: annotation-only + assigned-`strawberry.field` × scalar + relation. The consumer's annotation or assigned field wins over the auto-synthesized one via the unified `consumer_authored_fields` short-circuit in `DjangoType.__init_subclass__` and `_build_annotations`.
       2. Opt-out continues via [`Meta.exclude`](#metaexclude); field metadata (description, deprecation, default) continues via the assigned `strawberry.field(...)` path that shipped in `0.0.5`.
       3. **Converter validations are bypassed for overridden fields.** Naming the three behavior changes worth highlighting per spec line 136: (a) unsupported-scalar-field override (an `IntegerField` subclass with no registered ancestor that would otherwise raise [`ConfigurationError`](#configurationerror) — overrideable now); (b) grouped-choices override (a `choices=[("g1", [...])]` field that would otherwise raise — overrideable now); (c) nested-`ArrayField` override (`ArrayField(ArrayField(...))` that would otherwise raise — overrideable now). [`Meta.exclude`](#metaexclude) and annotation override are now parallel recourses for unsupported scalar fields (see [Scalar field conversion](#scalar-field-conversion)).
       4. **`relay.Node` `id` collision rejected at type-creation time.** Two sub-restrictions: (1) assigned `id = <StrawberryField>` overrides are uniformly rejected on Relay-Node-shaped types; the supported alternatives are `relay.NodeID[<pk_type>]` for a custom id annotation, `@classmethod resolve_id` for a custom id resolver, and a **resolver-backed sibling field** (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) for the field-level GraphQL metadata use case. A metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance. (2) Inherited `id` annotations on a Relay-Node-shaped subclass slip past the guard at class-creation time and are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry sees no `id` annotation on the child, applies the Relay-supplied `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`. Annotation `id: relay.NodeID[...]` is accepted in direct, PEP 563 / stringified, and mixed (resolved-id-with-unresolved-sibling) forms; non-`id` overrides are accepted unchanged.
       5. **Field-level GraphQL metadata on the Relay-supplied `id` field is not configurable in `0.0.6`** (per spec's Definition-of-done line 789). The documented workaround is the resolver-backed sibling field named in paragraph 4 above; a metadata-only sibling without a resolver is NOT recommended.
     - **`**See also:**` line.** Keep the existing line: `**See also:** [\`DjangoType\`](#djangotype) · [Definition-order independence](#definition-order-independence).`

     Worker 2 transcribes the five paragraphs faithfully from the spec line 136 wording. Worker 1 has chosen the paragraph order (matrix → opt-out → bypass → relay collision → metadata limitation) to match the spec's emphasis sequence.

   3c. **`Scalar field conversion` (H2 fix) at `docs/GLOSSARY.md:879`.** The current "Subclass MRO walk" sentence (`docs/GLOSSARY.md:879`) names only `Meta.exclude` as the consumer recourse for unsupported subclasses: *"with `Meta.exclude` named as the consumer recourse"*. Per spec line 137, update this and any sibling sentences about grouped-choices / `ArrayField` shape rejection to add annotation override as a parallel recourse. Specifically:

     - At `docs/GLOSSARY.md:879`, replace the trailing `(with \`Meta.exclude\` named as the consumer recourse)` with `(with [\`Meta.exclude\`](#metaexclude) or a consumer annotation override — see [Scalar field override semantics](#scalar-field-override-semantics) — named as the consumer recourses)`.
     - At `docs/GLOSSARY.md:874-875` (the `ArrayField` and `HStoreField` bullets), the `(... rejected with [\`ConfigurationError\`](#configurationerror))` parenthetical does NOT currently name `Meta.exclude` as a recourse — it just names the error. Per spec line 137 ("parallel update to any sibling sentences that mention grouped-choices rejection or `ArrayField` shape rejection — those continue to raise for the non-override path, but the override path is now also a recourse"), Worker 1 has decided NOT to expand those parentheticals: they describe the rejection contract, not the recourse menu, and the new MRO-walk sentence (now naming both recourses) is the single recourse home. The "Choice enum generation" entry (separate H2 section) is not touched by this slice — it does not currently mention grouped-choices rejection in a way that would need parallel update.
     - **Decision rationale.** Worker 1 has surveyed the GLOSSARY.md `Scalar field conversion` entry end-to-end (lines 857-883) per spec line 137's "Worker 1 reads the whole entry during planning to find all affected sentences" instruction. The MRO-walk sentence at `:879` is the only one that explicitly names `Meta.exclude` as a recourse; updating just that sentence covers the contract change without bloating sibling bullets that have a different rhetorical purpose.

   3d. **`Definition-order independence` at `docs/GLOSSARY.md:241`.** Remove the trailing sentence: `Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships.` The sentence before it (`Validation that a manual relation annotation matches the Django relation cardinality is deferred.`) stays. The result: line 241 ends after `... is deferred.` and no trailing sentence about scalar overrides.

   3e. **`DjangoType` "Current alpha constraints" at `docs/GLOSSARY.md:386-388`.** Per spec line 139, verify the bullet list at `:386-388` has no scalar-override-related entry. Pre-plan grep confirms the current state: only one bullet at `:388` (`manual override validation for relation cardinality is deferred; the package trusts relation-field annotations supplied by the consumer`). This is the relation-cardinality deferral, NOT a scalar-override entry. **No edit needed at `:386-388`.** Recorded explicitly so Worker 2 confirms the verification but does not delete the relation-cardinality bullet (which stays).

4. **`docs/TREE.md` — verify no changes needed.** Per spec line 141, pre-plan grep confirms `docs/TREE.md:337` already reads the broadened description and no stale "definition-order-independent relation finalization" string survives as a sole description. **No edit needed.** Worker 2 confirms via the grep recorded in step 1's pre-plan snapshot.

5. **`TODAY.md` — add scalar override semantics.** Per spec line 142, add a new bullet to the `## Shipped capabilities available but not currently demonstrated in fakeshop` subsection at `TODAY.md:263-265`. Position: append after the existing `Meta.primary` bullet at `:265`. Exact bullet text (parallel shape to the `Meta.primary` bullet — names the capability, names a fakeshop-state caveat, and cross-references the GLOSSARY.md entry):

   ```
   - Consumer override semantics for scalar fields (shipped in `0.0.6`) — annotation-only and `strawberry.field` scalar overrides bypass `convert_scalar` validations, and `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time. Fakeshop's `apps/products/schema.py` and `apps/library/schema.py` exercise the relation-override path (`Branch.shelves` in library) but no scalar override; the four-corner override matrix is fully covered by the package test suite. See [`docs/GLOSSARY.md#scalar-field-override-semantics`](docs/GLOSSARY.md#scalar-field-override-semantics).
   ```

6. **`KANBAN.md` — WIP → DONE move, plus Snapshot updates.**

   6a. **Remove the WIP card body.** Delete the entire `### WIP-ALPHA-015-0.0.6 — Consumer override semantics (scalar fields)` section at `KANBAN.md:79-119` (inclusive of the section heading at `:79` and the final "Files likely touched" bullet list ending at `:119`). The blank line after the deletion absorbs into the section above; verify the resulting `## In progress` section reads (post-edit):

     ```
     ## In progress

     ## To Do - Alpha (0.1.0)
     ```

     i.e., the `## In progress` heading has no body and is immediately followed by the next `## To Do - Alpha (0.1.0)` heading. Worker 2 may add a single placeholder sentence under `## In progress` like `*No cards currently in progress.*` if the empty section looks broken in the rendered KANBAN, BUT the standing convention (verified against `DONE-014-0.0.6`'s archive commit at `KANBAN.md` history) was to leave the section empty. **Default: leave it empty.** Discretion item for Worker 2 only if the rendered output is visually broken; otherwise no placeholder.

   6b. **Insert the DONE body.** Insert the verbatim `### DONE-015-0.0.6 — Consumer override semantics (scalar fields)` block (spec lines 145-265, between the outer triple-backtick fences which are NOT part of the body) into the `## Done` section. Position: per the on-disk ordering, the most-recently-shipped `0.0.6` cards go in NNN-ascending-within-version order with `DONE-014-0.0.6` at `KANBAN.md:1609` (between `DONE-012` at `:1568` and `DONE-013` at `:1675`). **Position decision: insert `DONE-015-0.0.6` immediately after `DONE-014-0.0.6` ends and before `### DONE-013-0.0.6 — Deferred scalar conversions` at `:1675`.** This matches the existing within-`0.0.6` order (012, 014, ..., 013). The 4-space indentation that wraps the spec's verbatim block (per spec source) must be STRIPPED — the markdown body is indented 4 spaces in the spec because the spec wrapped it inside a nested list bullet. The destination is a top-level `KANBAN.md` section, NOT a list-bullet child. Worker 2 strips the leading 4-space indent from every body line and the body's outer triple-backtick fences (spec `:145` and `:265`) are NOT included.

     **Source-of-truth for the verbatim body:** spec lines 145-265, with the outer ` ```markdown ` fence at `:145` and closing ` ``` ` at `:265` excluded, and a 4-space indent strip applied to every interior line (`:146-264`). The expected character-for-character KANBAN body after indent strip is preserved exactly — Worker 3's documentation/release sanity check will `diff` against the spec source with indent-strip applied per BUILD.md "Documentation / release sanity" verbatim-text rule.

   6c. **Update Snapshot bullets in the `## Snapshot` section** (this is the implicit follow-on to the WIP → DONE move that the spec's Slice 5 checklist does not literally enumerate, but Worker 3's "Documentation / release sanity" check requires for "no obsolete 'coming soon', 'planned', or old-version wording remains in files the slice deliberately updated"). Three Snapshot edits:

     - At `KANBAN.md:49`, **remove** the bullet `- \`WIP-ALPHA-015-0.0.6 — Consumer override semantics (scalar fields)\` — extends the \`DONE-006-0.0.4\` relation-field override contract to scalar fields. Spec pending.`
     - At `KANBAN.md:50`, **replace** the existing bullet text. Current text reads: `- \`0.0.6\` shipped progress: \`DONE-012-0.0.6\` (\`FieldMeta\` consolidation), \`DONE-013-0.0.6\` (deferred scalar conversions), and \`DONE-014-0.0.6\` (multiple \`DjangoType\`s per model with \`Meta.primary\`) landed in this version; \`WIP-ALPHA-015-0.0.6\` remains to complete the \`0.0.6\` patch.`

       Replace with: `- \`0.0.6\` shipped progress: \`DONE-012-0.0.6\` (\`FieldMeta\` consolidation), \`DONE-013-0.0.6\` (deferred scalar conversions), \`DONE-014-0.0.6\` (multiple \`DjangoType\`s per model with \`Meta.primary\`), and \`DONE-015-0.0.6\` (consumer override semantics for scalar fields) landed in this version; the \`0.0.6\` patch is complete.`
     - At `KANBAN.md:67`, **remove** the bullet `- stable consumer override semantics for **scalar** fields (the foundation slice pinned the contract for relation fields only)`. The parent bullet at `:66` (`Several DjangoType contract gaps remain:`) now has only one remaining child bullet at `:68` (`stable choice-enum naming override, because the first \`DjangoType\` to read a choice field currently wins the enum name`); keep the parent bullet intact since one child remains.

   6d. **Verify the `DONE-014-0.0.6` cross-reference at `KANBAN.md:1669-1673`.** The "Design notes" section of `DONE-014-0.0.6` references `WIP-ALPHA-015-0.0.6 — Consumer override semantics` as a forward-looking design space at `:1672`. **Decision: leave this reference unchanged.** The text describes the *design context* at the time DONE-014 shipped — it is a historical note, not a live reference. Editing settled `DONE-*` bodies retroactively is out of scope and out of pattern with how the maintainer has handled prior DONE bodies. Recorded explicitly so Worker 2 does not "tidy" this reference.

7. **`CHANGELOG.md` — `[Unreleased]` entries.** Per spec lines 266-271 (explicit permission grants in the spec body — overrides AGENTS.md's default prohibition on CHANGELOG edits). Add five new entries to the existing `## [Unreleased]` section at `CHANGELOG.md:19-37`:

   - Three `Added` entries (spec lines 267, 268, 270) appended to the existing `### Added` subheading at `CHANGELOG.md:20`. The existing `Added` block has bullets at lines 21-26; Worker 2 appends the three new bullets at the end of that block (immediately before `### Changed` at `:28`).
   - Two `Changed` entries (spec lines 269, 271) appended to the existing `### Changed` subheading at `CHANGELOG.md:28`. The existing `Changed` block has bullets at lines 29-34; Worker 2 appends the two new bullets at the end of that block (immediately before `### Notes` at `:36`).

   **Verbatim source-of-truth for the five entries** — Worker 2 transcribes from the spec lines 267-271 mechanically. Each bullet is one paragraph as written in the spec; line-wrapping is the consumer of Worker 2's text editor, not a content decision. The order inside `Added` (per spec ordering: line 267 first, line 268 second, line 270 third) and the order inside `Changed` (per spec ordering: line 269 first, line 271 second) must match the spec.

   **Important — order inside CHANGELOG `Added` vs the spec's interleaved order.** The spec lists the entries in the order: line 267 `Added` (annotation-only), line 268 `Added` (introspection field), line 269 `Changed` (converter bypass), line 270 `Added` (Relay annotation guard), line 271 `Changed` (assigned-id rejection). The Keep-a-Changelog convention used by CHANGELOG.md groups all `Added` under one heading and all `Changed` under another heading. Worker 2 preserves the spec's emit ORDER within each subheading group:
     - `### Added` final order after Worker 2's append: existing 6 bullets (lines 21-26 of current CHANGELOG.md) + spec line 267 + spec line 268 + spec line 270 (three new bullets, in that order).
     - `### Changed` final order after Worker 2's append: existing 6 bullets (lines 29-34 of current CHANGELOG.md) + spec line 269 + spec line 271 (two new bullets, in that order).

8. **Spec archival — opt-OUT (per spec sub-check 8 + BUILD.md "Spec stays at its working location").** Per spec line 272: "the spec stays at its working location per `docs/builder/BUILD.md` 'Specs stay at their working location after closeout'. Opt-in archival to `docs/SPECS/` is the maintainer's call; the Definition of done does not gate on it." **Decision: do NOT archive the spec as part of Slice 5.** The spec stays at `docs/spec-015-consumer_overrides_scalar-0_0_6.md` after the build closes. The maintainer may opt in to archival separately, outside this build cycle. Recorded explicitly so Worker 2 does not attempt to move the spec file.

9. **Validation.** Slice 5 touches no `.py` files; `uv run ruff format .` and `uv run ruff check --fix .` are still run per standing protocol but expected to be no-ops (markdown is not formatted by ruff). Worker 2 reports the per-command outcome under `### Validation run`.

### Test additions / updates

**None.** Slice 5 is documentation, KANBAN, and CHANGELOG edits only. No new tests, no test edits. The contract that the GLOSSARY.md / KANBAN.md / CHANGELOG.md narratives describe is already pinned by the Slice 1-3 tests (the 19-test cluster at `tests/types/test_definition_order.py` and `tests/types/test_converters.py` per spec Definition-of-done line 782).

State recorded explicitly so Worker 3's "Documentation / release sanity" pass does not expect test deltas.

### Implementation discretion items

Worker 2 has the following items genuinely at discretion (Worker 1 has assessed and decided each falls within Worker 2's mechanical-transcription mandate):

- **Whitespace inside the `KANBAN.md` `## In progress` section after WIP card removal.** Default: leave the section empty (per the `DONE-014-0.0.6` archive precedent). If the rendered KANBAN markdown looks visually broken, Worker 2 may add `*No cards currently in progress.*` as a placeholder bullet. This is a typographic choice, not a content choice.

- **Line-wrapping of long CHANGELOG bullets.** The spec entries at lines 267-271 are unwrapped paragraphs (no soft line breaks in the source). Worker 2's text editor may wrap them visually at the 110-column line length per `AGENTS.md`; this is a transcription mechanism choice, not a content choice. Worker 3's verbatim-diff check applies after unwrapping.

- **Position of the new `docs/README.md:101` bullet vs. existing bullet ordering.** Worker 1 has decided the new bullet appends after `Meta.primary` (the prior `0.0.6` shipped capability). If Worker 2 finds the surrounding ordering does not match the spec's emphasis (e.g., the existing bullets are not strictly version-ordered), Worker 2 may flag under `### Notes for Worker 1 (spec reconciliation)`. The default append-at-end position lands.

Everything else (line numbers, exact wording, placement order in CHANGELOG, KANBAN insert position) is resolved in the plan body above. Worker 2 transcribes mechanically.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 5 from `## Slice checklist`, copied verbatim with sub-bullet structure preserved. Spec source: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:132-272`.

- [x] Root `README.md` — confirm the package-version line reads `0.0.6` (no-op if any prior `0.0.6` card already bumped it).
- [x] `docs/README.md` — confirm the "shipped today is `0.0.6`" line (no-op if any prior `0.0.6` card already bumped it). Add a one-line mention of scalar override symmetry to the shipped-capability summary.
- [x] `docs/GLOSSARY.md` entries updated:
  - [`Scalar field override semantics`](GLOSSARY.md#scalar-field-override-semantics) → `shipped (0.0.6)`. Rewrite the body to describe the actual delivered contract: annotation-only and assigned-`strawberry.field` scalar overrides both supported, with the same `consumer_authored_fields` short-circuit; opt-out via `Meta.exclude`; field metadata via the assigned-`strawberry.field(...)` path; **converter validations bypassed for overridden fields** (consumer-authoritative contract — name unsupported-scalar override, grouped-choices override, and nested-`ArrayField` override as the three behavior changes worth highlighting); **`relay.Node` `id` collision rejected at type-creation time**, with two sub-restrictions: (1) assigned `id = <StrawberryField>` overrides are uniformly rejected on Relay-Node-shaped types (the supported alternatives are `relay.NodeID[<pk_type>]` for a custom id annotation, `@classmethod resolve_id` for a custom id resolver, and a **resolver-backed sibling field** — `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case, since the rev6 M1 + rev7 M2 ban removes the only path for attaching `description`/`deprecation_reason`/`directives` to the Relay-supplied `id`; a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned model instance); (2) inherited `id` annotations on a Relay-Node-shaped subclass slip past the guard at class-creation time, and `_build_annotations`'s pk-suppression branch silently handles them — Strawberry sees no `id` annotation on the child, applies the Relay-supplied `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"` (rev7 M1 correction; the rev6 framing of "Strawberry's downstream `ValueError` is the acknowledged failure mode" was wrong — schema construction actually succeeds). Annotation `id: relay.NodeID[...]` is accepted in direct, PEP 563 / stringified, and mixed (resolved-id-with-unresolved-sibling) forms; non-`id` overrides are accepted unchanged. Drop the "planned for `0.0.6`" framing.
  - [`Scalar field conversion`](GLOSSARY.md#scalar-field-conversion) (H2 fix) — the "Subclass MRO walk" paragraph and surrounding text frame unsupported scalar fields as `ConfigurationError` cases with `Meta.exclude` as the consumer recourse. Update to add annotation-only override as a parallel recourse: "or supply a consumer annotation override (see [Scalar field override semantics](#scalar-field-override-semantics))". Parallel update to any sibling sentences that mention grouped-choices rejection or `ArrayField` shape rejection — those continue to raise for the non-override path, but the override path is now also a recourse. Worker 1 reads the whole entry during planning to find all affected sentences.
  - [`Definition-order independence`](GLOSSARY.md#definition-order-independence) → remove the "Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships." closing sentence; the contract is now part of the foundation.
  - [`DjangoType`](GLOSSARY.md#djangotype) — review the "Current alpha constraints" bullet list (`docs/GLOSSARY.md:386-388`) and remove any scalar-override-related entry. Today the list only has the relation-cardinality-validation deferral; the spec author should verify nothing scalar-shaped is in there to drop.
  - [Index](GLOSSARY.md#index) → flip the status badge on `Scalar field override semantics` to `shipped (0.0.6)`.
- [x] `docs/TREE.md` — no further changes needed. The source-tree section's `types/base.py` and `types/definition.py` per-file annotations don't need updating: the new `consumer_annotated_scalar_fields` field on `DjangoTypeDefinition` is part of the same internal-metadata shape, and the existing `DjangoTypeDefinition` annotation in `definition.py` already reads "canonical per-type metadata with [Meta.primary](GLOSSARY.md#metaprimary) flag and forward-reserved Layer-3 slots" (post-DONE-014). The test-tree section's `tests/types/test_definition_order.py` description was broadened pre-Slice-1 from "definition-order-independent relation finalization" to "consumer override contract (four-corner matrix) + definition-order-independent relation finalization" to reflect the file's role as the override-contract host (the four-corner matrix has lived there since `0.0.5`); Worker 1 verifies via `grep` that no stale "definition-order-independent relation finalization" string remains as a sole description.
- [x] `TODAY.md` — add scalar override semantics to the "shipped today" section. The fakeshop example does not currently exercise scalar annotation overrides; mention under "available but not currently demonstrated in fakeshop" if that subsection exists.
- [x] `KANBAN.md` — move `WIP-ALPHA-015-0.0.6` → `DONE-015-0.0.6`. **Drop in the verbatim body below:**

  ````markdown
  ### DONE-015-0.0.6 — Consumer override semantics (scalar fields)

  Slice-by-slice scope (per `docs/spec-015-consumer_overrides_scalar-0_0_6.md`):

  - `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields`
    parallel to `consumer_annotated_relation_fields`. Annotation-only scalar
    overrides (e.g., `description: int` shadowing an auto-synthesized `str`)
    are added to the unified `consumer_authored_fields` frozenset and skip
    auto-synthesis in `_build_annotations`'s scalar branch via the existing
    `if field.name in consumer_authored_fields: continue` short-circuit.
  - `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]`.
  - The previously-skipped `test_consumer_annotation_overrides_synthesized`
    landed as `test_annotation_only_scalar_field_override_wins_over_synthesized`
    in `tests/types/test_definition_order.py` alongside the three relation
    overrides and the assigned-scalar override. The four-corner matrix
    (relation × annotation, relation × assigned, scalar × annotation,
    scalar × assigned) is symmetric and complete.
  - End-to-end test pinned the override surviving `strawberry.type(...)`
    decoration and showing up in the GraphQL schema with the consumer's type
    (unwrapped through `NON_NULL` for non-nullable Django columns).
  - **Consumer annotation overrides are authoritative.** `_build_annotations`'s
    scalar short-circuit bypasses every `convert_scalar` validation and side
    effect for an overridden field: unsupported-field-type rejection,
    grouped-choices rejection, `ArrayField` nested-array / outer-`choices`
    rejection, `null=True` widening, and choice-enum registration into the
    shared `(model, field_name)` cache. The contract matches the existing
    relation-annotation override path (which also bypasses `convert_relation`
    entirely) and treats annotation override as the consumer's escape from
    auto-conversion. `Meta.exclude` and annotation override are now parallel
    recourses for unsupported scalar fields. Cross-type cache behavior was
    pinned by an explicit test: two `DjangoType`s on the same `choices=`
    column where one overrides and one does not get the fresh enum from
    the non-overriding type alone (the overriding type's GraphQL surface
    uses the consumer's annotation; the cache is populated only by the
    non-overriding type's `convert_scalar` call).
  - **`relay.Node` `id` collision rejected at type-creation time.** A consumer
    who writes `id: <T>` (where `<T>` is not `relay.NodeID[...]`) or assigns
    any `id = <StrawberryField>` on a `DjangoType` with
    `Meta.interfaces = (relay.Node,)` now raises `ConfigurationError` from
    `__init_subclass__`. The annotation-side error points at
    `relay.NodeID[<pk_type>]` and `GlobalID`; the assigned-side error
    points at `relay.NodeID[<pk_type>]`, `@classmethod resolve_id`, and a
    **resolver-backed sibling-field workaround** (e.g.,
    `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`
    for the field-level GraphQL metadata use case — the rev4 M1 ban on
    `id = <StrawberryField>` on Relay-Node-shaped types eliminated the
    only path for attaching `description`/`deprecation_reason`/
    `directives` to the Relay-supplied `id` field; rev6 M1 documented
    the sibling-field workaround and rev7 M2 corrected the example
    from the metadata-only `display_id: ID = strawberry.field(description="…")`
    shape — which would build but fail at query time because Strawberry's
    default resolver looks up `display_id` as an attribute on the
    returned Django model instance — to the resolver-backed form that
    carries the metadata AND defines a value source). Without the guard
    the consumer would have seen a Strawberry-side `ValueError` only at
    `strawberry.Schema(...)` construction, which obscured the source.
    The guard is narrow: it fires only when the consumer authored an
    `id` entry on a Relay-Node-shaped type AND the annotation is not a
    `relay.NodeID[...]`-marked annotation. Detection uses
    `typing.get_type_hints(cls, include_extras=True)` so direct, PEP
    563 / `from __future__ import annotations`, and explicit-string
    forms are all resolved against the consumer's module globals; the
    fail-soft branch covers two sub-cases — id-itself-failed-to-
    resolve (rev7 H1: accept only when the raw string matches the
    token-shaped regex `(?:^|\.)NodeID\[`, so prefixed-substring
    lookalikes like `"NotNodeID[int]"` are rejected) and id-resolved-
    but-sibling-failed (rev6 H1: fall back to `_has_node_id_marker(raw)`
    on the already-resolved object so directly-resolved `id:
    relay.NodeID[int]` alongside a forward-referenced relation
    annotation is accepted). The fail-soft accept window for unresolved
    NodeID-shaped strings is package-level suppression only; Strawberry's
    downstream schema construction also resolves the string and may
    still error if the consumer's module globals don't expose `relay`
    (rev7 H1). `id: relay.NodeID[int]` and `id: "relay.NodeID[int]"`
    (the documented escape hatch in direct and stringified forms, with
    `relay` importable at module scope) are accepted end-to-end; non-
    `id` consumer scalar overrides (e.g., `description: int`, or `code:
    str` on a model with `code` as pk) pass through unchanged;
    **inherited `id` annotations on a subclass slip past the guard at
    class-creation time and are silently handled by `_build_annotations`'s
    pk-suppression branch** (rev6 L1 + rev7 M1: the guard does not
    walk the MRO, but pk-suppression strips the synthesized `id`
    annotation for any Relay-Node-shaped type and the post-merge
    reassignment leaves the child without an `id` key; Strawberry
    applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()`
    falls back to `"pk"` — schema construction succeeds).
  - No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
    / removal continues to go through `Meta.exclude`. Field description /
    deprecation / default continues to go through the assigned
    `strawberry.field(...)` path that shipped in `0.0.5`.
  - 100% coverage was reached across `tests/types/test_definition_order.py`
    (the override-contract host, where the core + Relay-collision +
    cross-type-cache tests live) and `tests/types/test_converters.py`
    (the converter test host, where the nested-`ArrayField` bypass test
    lives by default per the rev6 L3 placement decision).

  Design notes carried into `0.0.6`:

  - The four `consumer_*_fields` sets on `DjangoTypeDefinition`
    (`consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`,
    `consumer_annotated_scalar_fields`, `consumer_assigned_scalar_fields`) are
    the introspection surface. The unified `consumer_authored_fields` is the
    single short-circuit input for `_build_annotations`.
  - Resolver / metadata overrides for scalars stay on the assigned
    `strawberry.field(...)` path — the consumer writes
    `description = strawberry.field(resolver=..., description="...", deprecation_reason=...)`
    and `_consumer_assigned_fields` already routes it through the
    `consumer_assigned_scalar_fields` short-circuit. Field-level GraphQL
    metadata on the Relay-supplied `id` field is **not** configurable in
    `0.0.6` (the rev4 M1 / rev6 M1 / rev7 M2 assigned-`id` ban applies
    uniformly); the documented workaround is a **resolver-backed sibling
    field** (`@strawberry.field(description="…") def display_id(self) ->
    strawberry.ID: return str(self.pk)`) carrying both the metadata and
    a value source.
  - Type-annotation overrides are the consumer's responsibility for runtime
    correctness. `description: int` against a `CharField` will surface a
    Strawberry-side serialization error at query time if the database returns
    a non-integer value; the package does not pre-check annotation/field-type
    compatibility (out of scope for this card).
  ````
- [x] `CHANGELOG.md` — `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`](../AGENTS.md)'s default prohibition):
  - `Added`: Annotation-only scalar field overrides on `DjangoType`. Writing `description: int` (or any other class-level scalar annotation that shadows a Django scalar column selected via [`Meta.fields`](GLOSSARY.md#metafields)) is now a stable public contract — the consumer's annotation wins over the auto-synthesized one and survives `finalize_django_types()` / `strawberry.type(...)` decoration. Mirrors the annotation-only relation-override path that has shipped since `0.0.4` (`DONE-006-0.0.4`).
  - `Added`: `DjangoTypeDefinition.consumer_annotated_scalar_fields: frozenset[str]` — introspection surface for the new override path; symmetric with the existing `consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`, and `consumer_assigned_scalar_fields` sets.
  - `Changed`: Annotation-only and assigned scalar field overrides bypass `convert_scalar` validations and side effects for the overridden field — unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are skipped. The consumer's annotation is authoritative. `Meta.exclude` and annotation override are now parallel consumer recourses for unsupported scalar fields.
  - `Added`: `ConfigurationError` raised at `DjangoType.__init_subclass__` time when a consumer authors an `id` annotation on a `Meta.interfaces = (relay.Node,)`-shaped type that is not a `relay.NodeID[...]`-marked annotation. Points at `strawberry.relay.NodeID[<pk_type>]` as the supported escape hatch. Replaces the downstream Strawberry-side `ValueError` ("Interface field Node.id expects type ID! but ...") that surfaced only at `strawberry.Schema(...)` construction. Narrow guard: `id: relay.NodeID[int]` is accepted in direct, stringified / PEP 563 / `from __future__ import annotations`, and mixed (directly-resolved `id` alongside other unresolved annotations on the same class) forms; non-`id` consumer scalar overrides on Relay-Node-shaped types (including custom-named primary keys like `code: str` on `models.CharField(primary_key=True)`) are accepted; inherited `id` annotations on a Relay-Node-shaped subclass also pass through at class-creation time (the guard does not walk the MRO) and are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds. Detection uses `typing.get_type_hints(cls, include_extras=True)` with a fail-soft fallback for unresolved forward references that distinguishes "id itself failed to resolve" (accept only when the raw string matches the token-shaped regex `(?:^|\.)NodeID\[`, so prefixed-substring lookalikes like `"NotNodeID[int]"` are rejected) from "id is directly resolved but another annotation failed" (inspect the resolved object via `_has_node_id_marker`). The fail-soft accept window for unresolved NodeID-shaped strings is package-level guard suppression only — Strawberry's downstream resolution against `cls`'s module globals still applies.
  - `Changed`: `id = <StrawberryField>` assignment on a `Meta.interfaces = (relay.Node,)`-shaped `DjangoType` now raises `ConfigurationError` at `__init_subclass__` time. Previously consumers could write `@strawberry.field def id(self) -> relay.GlobalID: ...` (or `id = strawberry.field(description="…")`) and the resulting schema would build because the assigned-field type matched `Node.id: ID!`; this card uniformly rejects assigned `id` overrides on Relay-Node-shaped types for consistency with the annotation-side guard. The supported alternatives are `@classmethod resolve_id` (custom id resolver), `id: relay.NodeID[<pk_type>]` (custom id annotation), and a **resolver-backed sibling field** for the field-level GraphQL metadata use case (declare a separate field with a resolver — e.g., `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — carrying the metadata AND a value source; the Relay-supplied `id` stays undecorated). Field-level metadata on the Relay-supplied `id` field is not configurable in `0.0.6`; the resolver-backed sibling-field is the documented alternative. **Note**: a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance and does not find it.
- [x] **Before archiving**, the spec stays at its working location per [`docs/builder/BUILD.md`](builder/BUILD.md) "Specs stay at their working location after closeout". Opt-in archival to `docs/SPECS/` is the maintainer's call; the [Definition of done](#definition-of-done) does not gate on it.

---

## Build report (Worker 2)

### Files touched

- `README.md` — verified at `:45` (`**\`0.0.6\`, single-maintainer, alpha-quality.**`); no edit applied. Per the spec sub-check "no-op if any prior `0.0.6` card already bumped it" — verification only.
- `docs/README.md` — added one new bullet after the `Meta.primary` bullet (`:101`) to the "Shipped today" list: the scalar-override-symmetry sentence prescribed by the plan. Version-string at `:89` already reads `0.0.6` from prior `0.0.6` cards; no edit needed there.
- `docs/GLOSSARY.md` — four edits:
  - Index badge at `:101`: flipped `planned for \`0.0.6\`` → `shipped (\`0.0.6\`)`.
  - "Subclass MRO walk" sentence at `:879`: replaced the trailing `(with \`Meta.exclude\` named as the consumer recourse)` with the linked dual-recourse phrasing per the plan and spec line 137.
  - "Definition-order independence" trailing sentence at `:241`: removed the closing scalar-override-implementation-detail sentence; kept the relation-cardinality sentence intact.
  - `Scalar field override semantics` entry body at `:885-891`: replaced status line + body with the five-paragraph rewrite (matrix → opt-out → bypass → relay collision → metadata limitation) prescribed by the plan; preserved the existing `**See also:**` line verbatim.
- `TODAY.md` — appended a new bullet after the `Meta.primary` bullet (`:265`) in the "Shipped capabilities available but not currently demonstrated in fakeshop" subsection. Parallel shape to the existing `Meta.primary` bullet.
- `KANBAN.md` — four edits:
  - Removed the entire `### WIP-ALPHA-015-0.0.6 — Consumer override semantics (scalar fields)` body at `:79-119` (inclusive of heading and final "Files likely touched" list). The `## In progress` section is now empty (no placeholder added; default per `DONE-014-0.0.6` precedent).
  - Inserted the verbatim `### DONE-015-0.0.6 — Consumer override semantics (scalar fields)` body between `DONE-014-0.0.6` (ends at the original `:1631`) and `### DONE-013-0.0.6` (originally at `:1675`, now at `:1753`). Body is from spec lines 146-264 with 4-space indent stripped; outer ` ```markdown ` and ` ``` ` fences excluded. Verbatim diff against the spec source confirmed clean (no output from `diff -u <(sed -n '146,264p' docs/spec-... | sed 's/^    //') <(sed -n '1633,1751p' KANBAN.md)`). Single occurrence of `DONE-015-0.0.6` in KANBAN.md confirmed via `grep -c`.
  - Snapshot bullet at `:49` (WIP-ALPHA-015 listing) removed.
  - Snapshot bullet at `:50` (0.0.6 shipped progress) replaced with the patch-complete phrasing per the plan; now describes all four 0.0.6 cards (012, 013, 014, 015) with "the `0.0.6` patch is complete."
  - "Still not implemented" sub-bullet at `:67` (`stable consumer override semantics for **scalar** fields ...`) removed; the parent `Several DjangoType contract gaps remain:` bullet still has the choice-enum-naming child bullet so the parent stays intact.
- `CHANGELOG.md` — appended five new bullets to the `[Unreleased]` section:
  - Three new bullets in `### Added` (after the existing six bullets, before `### Changed`): spec line 267 (annotation-only scalar overrides), spec line 268 (`consumer_annotated_scalar_fields` introspection), spec line 270 (Relay `id` annotation guard).
  - Two new bullets in `### Changed` (after the existing six bullets, before `### Notes`): spec line 269 (converter validation bypass), spec line 271 (assigned-`id` rejection).
  - Order within each subheading matches the spec's emit order. Verbatim diff against the spec source (after stripping `    - \`Added\`: ` / `    - \`Changed\`: ` prefix) confirmed clean for all five entries.

### Tests added or updated

None. Slice 5 is documentation, KANBAN, and CHANGELOG edits only. Plan and artifact contract both pin "no new tests, no test edits"; the underlying behavior is already pinned by the Slice 1-3 test cluster (the 19-test additions to `tests/types/test_definition_order.py` and `tests/types/test_converters.py`).

### Validation run

- `uv run ruff format .` — **pass** (100 files left unchanged; no `.py` changes in this slice, expected no-op).
- `uv run ruff check --fix .` — **pass** (all checks passed).
- `git status --short` after both ruff invocations:
  ```
   M CHANGELOG.md
   M KANBAN.md
   M TODAY.md
   M django_strawberry_framework/types/base.py
   M django_strawberry_framework/types/definition.py
   M docs/GLOSSARY.md
   M docs/README.md
   M pyproject.toml
   M tests/types/test_base.py
   M tests/types/test_converters.py
   M tests/types/test_definition_order.py
  ?? docs/builder/bld-slice-1-annotation_scalar_overrides.md
  ?? docs/builder/bld-slice-2-unskip_consumer_annotation_test.md
  ?? docs/builder/bld-slice-3-document_override_contract.md
  ?? docs/builder/bld-slice-4-version_bump_quintet.md
  ?? docs/builder/bld-slice-5-docs_kanban_changelog_archive.md
  ?? docs/builder/build-015-consumer_overrides_scalar-0_0_6.md
  ```
  Classification:
  - Slice-intended (Slice 5 diff): `CHANGELOG.md`, `KANBAN.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/README.md`, and the artifact file `docs/builder/bld-slice-5-docs_kanban_changelog_archive.md`.
  - Carry-over from prior Slices 1-3 (not authored or touched by Slice 5; appear in the working tree because the maintainer has not yet committed earlier slices): `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `tests/types/test_base.py`, `tests/types/test_converters.py`, `tests/types/test_definition_order.py`. Carry-over from Slice 4 (atomic version-bump quintet; verify-and-no-op landed earlier but the prior `0.0.6` cards' version bumps appear in `pyproject.toml`): `pyproject.toml`. None modified by Slice 5; left untouched.
  - Slice-intended new artifacts (build cycle records, gitignored vs tracked per `BUILD.md`): `docs/builder/build-015-consumer_overrides_scalar-0_0_6.md`, `docs/builder/bld-slice-1-...md`, `bld-slice-2-...md`, `bld-slice-3-...md`, `bld-slice-4-...md`. These are tracked permanent records authored by prior workers.
- No focused `pytest` required for a docs-only slice; not run.

### Implementation notes

- **Snapshot Item Removed for In Progress section.** The plan section 6a allowed Worker 2 discretion to insert a `*No cards currently in progress.*` placeholder if the empty section looks visually broken. Decision: left empty, per the `DONE-014-0.0.6` archive precedent. Rendering check: the `## In progress` heading is immediately followed by `## To Do - Alpha (0.1.0)` with one blank line between them, matching the rest of the file's section spacing.
- **GLOSSARY.md `Scalar field override semantics` body shape.** Plan section 3b prescribed the five-paragraph body. Chose to render the contract as five separate paragraphs (`Status:` line; matrix paragraph; opt-out / metadata paragraph; **bold-led** converter bypass paragraph; **bold-led** Relay collision paragraph; **bold-led** metadata-limitation closing paragraph) rather than a single bullet list. The sibling FEATURES entries (e.g., `## Definition-order independence`, `## Scalar field conversion`) use prose paragraphs for narrative content and bullet lists for shipped-feature inventories; the body is narrative contract description, so paragraph form is the matched shape. The `**See also:**` line at the end follows the existing convention.
- **MRO sentence linking.** The plan section 3c prescribed `[\`Meta.exclude\`](#metaexclude) or a consumer annotation override — see [Scalar field override semantics](#scalar-field-override-semantics) — named as the consumer recourses`. Worker 2 transcribed this verbatim; the link to `#scalar-field-override-semantics` already resolves because the section heading exists in the same file. Anchors verified by inspection.
- **KANBAN body indentation strip.** Used `sed 's/^    //'` to mechanically strip the 4-space indent from spec lines 146-264 before inserting into KANBAN.md. The closing ` ```` ` markdown-block-close at spec line 273 (` ```` `) and the `` ```markdown `` opening at spec line 145 are both excluded (they are spec presentation, not body content). Result confirmed verbatim by `diff -u`.
- **CHANGELOG ordering note.** Plan section 7 made the within-subheading order explicit. Spec emit order is 267 → 268 → 269 → 270 → 271. Mapping to CHANGELOG: `Added` gets 267, 268, 270 (in that order, all after existing `Added` bullets); `Changed` gets 269, 271 (in that order, all after existing `Changed` bullets). Verbatim diff confirmed each of the five entries character-for-character against the spec source.

### Notes for Worker 3

- **This slice will trip the CHANGELOG sanity check and the Documentation / release sanity check** in Worker 3's review per `BUILD.md`. Worker 3 must verify verbatim character-for-character match between the inserted KANBAN body / CHANGELOG entries / GLOSSARY.md `Scalar field override semantics` body and the spec source. Recommended diff approach for the KANBAN move: `diff -u <(sed -n '146,264p' docs/spec-015-consumer_overrides_scalar-0_0_6.md | sed 's/^    //') <(sed -n '1633,1751p' KANBAN.md)` — Worker 2 ran this during the build and confirmed empty output (perfect match). The five CHANGELOG entries were verified one-by-one with `diff <(sed -n 'NNNp' spec... | sed 's/^    - \`Added\`: //') <(sed -n 'MMMp' CHANGELOG.md | sed 's/^- //')` — all confirmed empty output.
- **`scripts/review_inspect.py` not run.** This slice touches no `.py` files; the helper rule from `BUILD.md` triggers on Python files only. Recorded explicitly so Worker 3 does not expect a shadow file.
- **Carry-over files in the working tree.** Slices 1-4 left source/test/pyproject changes uncommitted (maintainer commits at slice boundaries). Slice 5's `git status --short` therefore lists 6 carry-over files in addition to the 5 slice-intended files. Worker 3's diff against `HEAD` will show all of them, but the *Slice 5 contract* is the 5 slice-intended files. Per `BUILD.md` "the slice diffs and review prompts are only useful when everyone agrees which changes predate the build" — the maintainer has committed nothing since the build started, so the carry-over is well-understood; the artifact lists it explicitly above.
- **`docs/TREE.md` not edited.** Plan section 4 confirmed verify-and-no-op per spec line 141. Pre-plan grep at the planning pass found `docs/TREE.md:337` already broadened (`consumer override contract (four-corner matrix) + definition-order-independent relation finalization`). Worker 2 re-ran the grep during the build pass and confirmed the same on-disk state: no stale "definition-order-independent relation finalization" string remains as a sole description.
- **Spec stays at `docs/spec-015-consumer_overrides_scalar-0_0_6.md`.** Per plan section 8 + spec sub-check 8 + `BUILD.md` "Spec stays at its working location": archival is opt-out by default. Worker 2 did not move the spec.

### Notes for Worker 1 (spec reconciliation)

None. The five verbatim blocks (KANBAN body, three CHANGELOG `Added`, two CHANGELOG `Changed`) were transcribed character-for-character from the spec source and verified clean by `diff`. The five-paragraph FEATURES body was a narrative rewrite from the spec sub-check at spec line 136; Worker 1 has the discretion to keep, edit, or refine the wording during final verification. The body paragraph order matches the plan section 3b's prescribed sequence (matrix → opt-out → bypass → relay collision → metadata limitation).

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- No code-level DRY findings (the slice touches no `.py` files). The narrative-DRY concern raised in Worker 1's planning ("no contradictory narratives across the three audiences") was addressed: the four-corner override matrix language, the converter-bypass framing ("Meta.exclude and annotation override are now parallel recourses for unsupported scalar fields"), the resolver-backed sibling-field workaround example, and the rev6 H1 / rev7 H1 / rev7 M1 fail-soft and pk-suppression specifics appear consistently across the docs/GLOSSARY.md `Scalar field override semantics` body, the KANBAN `DONE-015-0.0.6` body (verbatim from spec), the CHANGELOG `Added`/`Changed` entries (verbatim from spec), the docs/README.md "Shipped today" bullet, and the TODAY.md "available but not currently demonstrated in fakeshop" bullet. Cross-checked the `_consumer_assigned_fields` docstring framing from the Slice 3 carry-over and confirmed no contradiction.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returned **zero bytes**. `__all__` and the re-export list are unchanged. The Slice 5 spec does not authorize any new public exports; the result is correct.

### CHANGELOG sanity

The slice's diff appends five new bullets to `CHANGELOG.md`'s `## [Unreleased]` section (three to `### Added` at the existing `[Unreleased]` `### Added` block, two to `### Changed` at the existing `[Unreleased]` `### Changed` block). End-to-end walk:

- **Version line alignment.** The CHANGELOG header is `## [Unreleased]` (line 19), not a versioned `## [0.0.6]` header — the entries are deliberately staged for an eventual `0.0.6` release line cut. `pyproject.toml:4` reads `version = "0.0.6"`, `django_strawberry_framework/__init__.py:25` reads `__version__ = "0.0.6"`. Both agree with the staged `[Unreleased]` block; no version-line drift.
- **Heading authorization.** Spec line 266 authorizes `Added` (× 3) and `Changed` (× 2) under `[Unreleased]`. The diff appends exactly three `Added` entries and two `Changed` entries to the existing same-named subheadings. No `Fixed` / `Removed` headings introduced. Authorization confirmed.
- **Canonical phrasing — byte-for-byte match.** Verified all five entries against the spec source:
  - `diff <(sed -n '267p' spec | sed 's/^    - \`Added\`: //') <(sed -n '27p' CHANGELOG.md | sed 's/^- //')` → empty (perfect match).
  - `diff <(sed -n '268p' spec | sed 's/^    - \`Added\`: //') <(sed -n '28p' CHANGELOG.md | sed 's/^- //')` → empty.
  - `diff <(sed -n '269p' spec | sed 's/^    - \`Changed\`: //') <(sed -n '38p' CHANGELOG.md | sed 's/^- //')` → empty.
  - `diff <(sed -n '270p' spec | sed 's/^    - \`Added\`: //') <(sed -n '29p' CHANGELOG.md | sed 's/^- //')` → empty.
  - `diff <(sed -n '271p' spec | sed 's/^    - \`Changed\`: //') <(sed -n '39p' CHANGELOG.md | sed 's/^- //')` → empty.
- **No over/understatement.** The annotation-only-scalar entry, the introspection-field entry, the converter-bypass entry, the Relay annotation guard entry, and the assigned-`id` rejection entry each describe behavior that is pinned by the Slice 1-3 implementation (the 19-test cluster Worker 3 reviewed at Slice 1; the docstring narrative consolidated at Slice 3). The Relay guard fail-soft branching language (rev7 H1 token regex, rev6 H1 resolved-object fallback) matches the actual `_id_annotation_is_relay_node_id` helper landed in Slice 1.

### Documentation / release sanity

The slice's diff modifies `docs/README.md`, `docs/GLOSSARY.md`, `TODAY.md`, and `KANBAN.md` (plus the `CHANGELOG.md` covered above). End-to-end walk:

- **Version strings.** `README.md:45` (`**\`0.0.6\`, single-maintainer, alpha-quality.**`), `docs/README.md:89` (`**Shipped today** (\`0.0.6\`):`), `docs/GLOSSARY.md:20` (`Current package version: \`0.0.6\`.`), and `pyproject.toml:4` / `__init__.py:25` all read `0.0.6`. The Slice 5 diff does not modify any version string; Worker 2's verify-and-no-op was the correct disposition.
- **Shipped status badges.** `docs/GLOSSARY.md:101` now reads `| [Scalar field override semantics](#scalar-field-override-semantics) | shipped (\`0.0.6\`) |` (flipped from `planned for \`0.0.6\``). Matches the spec sub-check at line 140.
- **Card IDs.** The card moved from `WIP-ALPHA-015-0.0.6` to `DONE-015-0.0.6`. `grep -c "^### DONE-015-0.0.6"` in KANBAN.md returns `1` (exactly one DONE heading). `grep -c "^### WIP-ALPHA-015-0.0.6"` returns `0`. Three remaining `WIP-ALPHA-015-0.0.6` mentions are all inside earlier DONE bodies (DONE-007 at `:1416`, `:1423`; DONE-014 at `:1628`) — historical design-context references intentionally preserved per plan section 6d.
- **KANBAN move.** WIP card body removed from `## In progress` (lines 79-119 in pre-edit shape). DONE-015-0.0.6 body inserted between DONE-014-0.0.6 (ends `:1629`) and DONE-013-0.0.6 (now at `:1751`). Single occurrence of `### DONE-015-0.0.6` heading. The `## In progress` board column (line 75) is now empty; the Snapshot's "In progress" sub-section (line 47) lost the WIP bullet and the line 50 bullet was rewritten to describe all four 0.0.6 cards as shipped with "the `0.0.6` patch is complete." The "Still not implemented" sub-bullet about scalar override semantics was removed from line 67 (parent `Several DjangoType contract gaps remain:` retained with the remaining choice-enum-naming child). All consistent with the plan.
- **Verbatim text from spec — full diff.** Ran `diff -u <(sed -n '146,264p' docs/spec-015-consumer_overrides_scalar-0_0_6.md | sed 's/^    //') <(sed -n '1631,1749p' KANBAN.md)` and received **empty output** — perfect character-for-character match between the spec's verbatim KANBAN body block (after 4-space indent strip) and the inserted DONE-015-0.0.6 body in KANBAN.md.
- **Outer fence backtick count.** The spec's KANBAN drop-in uses a triple-backtick outer fence with `markdown` identifier (spec line 145). No inner fenced code blocks exist inside the spec's body block (lines 146-264) — the contents are bullets and prose, not nested code fences. The triple-backtick outer fence is sufficient and matches BUILD.md "Documentation / release sanity" guidance. The slice artifact (`bld-slice-5-...md`) uses four-backtick outer fence at lines 153/273 to embed the spec's triple-backtick drop-in — also correct, mirroring BUILD.md's example.
- **Markdown links.** New links introduced or moved:
  - `docs/GLOSSARY.md:879`: `[\`Meta.exclude\`](#metaexclude)` and `[Scalar field override semantics](#scalar-field-override-semantics)` — both anchors exist (`#metaexclude` at `Meta.exclude` heading; `#scalar-field-override-semantics` at `docs/GLOSSARY.md:885`).
  - `docs/GLOSSARY.md:893` (new bypass paragraph): `[\`ConfigurationError\`](#configurationerror)`, `[\`Meta.exclude\`](#metaexclude)`, `[Scalar field conversion](#scalar-field-conversion)` — all in-file anchors that resolve.
  - `docs/GLOSSARY.md:899` (See also): `[\`DjangoType\`](#djangotype)`, `[Definition-order independence](#definition-order-independence)` — both resolve.
  - `TODAY.md:266`: `[\`docs/GLOSSARY.md#scalar-field-override-semantics\`](docs/GLOSSARY.md#scalar-field-override-semantics)` — resolves via the GLOSSARY.md anchor.
  - No broken or stale links observed.
- **Active-spec archival.** Per spec sub-check 8 (line 272) — archival is opt-OUT for this card. Worker 2 did NOT move the spec to `docs/SPECS/`. Confirmed: `ls docs/spec-015* docs/SPECS/spec-015* 2>&1` shows the spec at `docs/spec-015-consumer_overrides_scalar-0_0_6.md` (and the terms CSV), and no `docs/SPECS/spec-015*` exists. Correct disposition per BUILD.md "Spec stays at its working location after closeout".
- **No obsolete framing.** The "planned for `0.0.6`" status badge was flipped to "shipped (`0.0.6`)" at `docs/GLOSSARY.md:101` (Index) and at `:887` (entry body). The "planned for `0.0.6`" framing was removed from the entry's body and replaced with the shipped-contract description. The `Definition-order independence` entry at `:241` had its closing "Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics] ships." sentence removed; only the relation-cardinality deferral sentence remains. The DjangoType `Current alpha constraints` bullet list at `:386-388` still contains only the relation-cardinality deferral — no scalar-override entry was present pre-Slice-5 and none was added. No stale "coming soon" wording remains.

### What looks solid

- **Verbatim transcription discipline.** Every one of the six verbatim blocks (KANBAN body via the 4-space-indent strip; five CHANGELOG bullets via the heading-prefix strip) diffs clean against the spec source. The transcription is mechanically perfect.
- **KANBAN move semantics.** The WIP card was removed from the `## In progress` board column AND from the Snapshot's `### In progress` recap; the DONE card was inserted into the `## Done` column in within-version order (DONE-014 → DONE-015 → DONE-013, matching the existing precedent that within-`0.0.6` cards appear in shipping order). The Snapshot's `## Still not implemented` sub-section correctly lost the scalar-overrides bullet while preserving the parent `Several DjangoType contract gaps remain:` heading and its remaining child (choice-enum naming).
- **No misplaced changes.** The carry-over Slice 1-3 source files (`types/base.py`, `types/definition.py`, the three test files) and the carry-over Slice 4 file (`pyproject.toml`) are all out of scope for Slice 5; Worker 2 correctly did not touch them. The Slice 5 diff is bounded to the five documentation files plus the slice artifact.
- **GLOSSARY.md narrative rewrite.** The five-paragraph rewrite at `:885-899` (status line, four-corner matrix, opt-out/metadata, converter-bypass, Relay collision, metadata-limitation closing) faithfully transcribes spec line 136's prescription into the existing FEATURES entry shape (`Status:` line, body paragraphs, `**See also:**`). The `**See also:**` line at `:899` was preserved verbatim from pre-Slice-5 state.
- **Cross-file consistency.** The resolver-backed-sibling-field workaround example (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) appears consistently in the KANBAN DONE body, the GLOSSARY.md entry, the CHANGELOG `Changed` entry, and is also captured in the spec's "design notes carried into `0.0.6`" block. The rev7 M2 correction (resolver-backed vs the buggy metadata-only `display_id: ID = strawberry.field(description="…")` form) is consistently surfaced.

### Temp test verification

Not applicable; no temp tests for this docs slice.

### Notes for Worker 1 (spec reconciliation)

None. The slice landed the spec contract end-to-end with no observed gaps or ambiguities. Two minor implementation discretions that fell to Worker 2 per the plan — (a) leaving the `## In progress` board column empty (no placeholder bullet) per the DONE-014 precedent; (b) rendering the GLOSSARY.md `Scalar field override semantics` body as five paragraphs rather than a bullet list — both match the conventions of sibling FEATURES entries and are inside the plan's stated discretion-item envelope. No spec edits warranted.

### Review outcome

`review-accepted`. Every spec sub-check at lines 132-272 is reflected in the diff; the verbatim-text contracts (KANBAN body and five CHANGELOG entries) match byte-for-byte against the spec source; the KANBAN WIP-to-DONE move is clean (one DONE-015 heading; zero live WIP-015 mentions; Snapshot updates landed); no obsolete planning-language remains in files the slice touched; no public-surface changes; no DRY, narrative-consistency, or correctness findings at any severity.

---

## Final verification (Worker 1)

- **Spec slice checklist:** every `- [ ]` in `### Spec slice checklist (verbatim)` is now `- [x]`. All eight top-level sub-checks verified against on-disk state:
  - Root `README.md` — verified `README.md:45` still reads `**\`0.0.6\`, single-maintainer, alpha-quality.**` (verify-and-no-op).
  - `docs/README.md` — verified `:89` (`**Shipped today** (\`0.0.6\`):`) plus the new scalar-override-symmetry bullet at `:102`.
  - `docs/GLOSSARY.md` entries (five sub-edits) — verified all five: Index badge at `:101` flipped to `shipped (\`0.0.6\`)`; entry body at `:885-899` rewritten as five-paragraph contract; `Scalar field conversion` MRO sentence at `:879` named both recourses; `Definition-order independence` at `:241` closes after the relation-cardinality sentence; `DjangoType` "Current alpha constraints" at `:386-388` retains only the relation-cardinality bullet (no scalar-override entry to drop).
  - `docs/TREE.md` — verified verify-and-no-op; pre-Slice-1 broadening of `tests/types/test_definition_order.py` description holds; `grep` confirmed no stale "definition-order-independent relation finalization" sole-description string.
  - `TODAY.md` — verified new bullet at `:266` under "Shipped capabilities available but not currently demonstrated in fakeshop".
  - `KANBAN.md` WIP→DONE — verified single `### DONE-015-0.0.6` heading at `:1631`; zero live `### WIP-ALPHA-015-0.0.6` headings (three historical references inside earlier DONE bodies intentionally preserved); `diff -u <(sed -n '146,264p' docs/spec-015-consumer_overrides_scalar-0_0_6.md | sed 's/^    //') <(sed -n '1631,1749p' KANBAN.md)` → empty output (perfect verbatim match). Snapshot updates landed at `:49` (WIP bullet removed) and `:50` (rewritten to "0.0.6 patch is complete"); the "Still not implemented" scalar-override sub-bullet at the prior `:67` removed.
  - `CHANGELOG.md` `[Unreleased]` entries — verified all five appended in spec emit order: three `Added` (lines 27, 28, 29) and two `Changed` (lines 38, 39); byte-for-byte verbatim against spec lines 267-271. Heading authorization (`Added`, `Changed`) matches spec line 266. Version line `## [Unreleased]` aligns with `pyproject.toml:4` and `__init__.py:25` (`0.0.6`).
  - Spec archival sub-check (sub-check 8): the act of NOT archiving satisfies it per BUILD.md "Spec stays at its working location" default + the spec's own opt-out language (`Definition of done does not gate on it`). The spec remains at `docs/spec-015-consumer_overrides_scalar-0_0_6.md`; no `docs/SPECS/spec-015*` exists. Rationale: opt-in archival is the maintainer's call, not part of the closeout contract. **Pass.**
- **DRY check across this slice and prior accepted slices:** doc-only slice. The narrative-DRY concern (no contradictory voices across GLOSSARY.md / KANBAN / CHANGELOG / TODAY / docs/README.md) was confirmed by Worker 3 and re-spot-checked: the four-corner matrix language, the converter-bypass framing ("Meta.exclude and annotation override are now parallel recourses"), the resolver-backed sibling-field workaround example, and the rev7 H1 token-regex / rev6 H1 / rev7 M1 pk-suppression specifics appear consistently. No code-level DRY findings. **Pass.**
- **Existing tests still pass:** `uv run pytest tests/types/ tests/base/ --no-cov -q` → **259 passed, 2 skipped** in 3.54s. The two skips are pre-existing `test_converters` skips (unrelated to spec-015). No regressions from any slice in the build. **Pass.**
- **Spec reconciliation:** None expected and none made. The Slice 5 contract is mechanical transcription from the spec into the durable docs / KANBAN / CHANGELOG — every verbatim block diffs clean; the narrative paragraphs in GLOSSARY.md `Scalar field override semantics` faithfully transcribe spec line 136's prescription. The spec's narrative is fully reflected in the now-merged docs/KANBAN/CHANGELOG. **Pass.**
- **Spec status-line check:** `docs/spec-015-consumer_overrides_scalar-0_0_6.md:4` reads `Status: draft (revision 10, post-rev9 review).` — accurate through Slice 5's verification (Slice 5 is the closing slice of the build; integration pass and final test-run gate remain). The line will be revisited by Worker 1 at the integration pass and the final test-run gate; per worker-1 memory, the convention is to leave this status line as "draft (revision N)" through the entire build cycle. **No edit.**
- **Final status:** `final-accepted`.

### Summary

Slice 5 closes out spec-015: the closeout slice landed the consumer-facing narrative for `DONE-015-0.0.6` across five durable surfaces. `docs/GLOSSARY.md` `Scalar field override semantics` flipped from `planned for 0.0.6` to `shipped (0.0.6)` with a five-paragraph contract body covering the four-corner matrix, the `convert_scalar` validation bypass (three new behavior changes: unsupported-scalar / grouped-choices / nested-`ArrayField` overrides), and the `relay.Node` `id` collision guard's two sub-restrictions (assigned-id rejection + inherited-id pk-suppression silence). `docs/README.md` gained a scalar-override-symmetry bullet; `TODAY.md` gained a "shipped capabilities available but not currently demonstrated in fakeshop" bullet; `docs/GLOSSARY.md` had four other narrative edits (`Scalar field conversion` MRO sentence linking, `Definition-order independence` trailing-sentence removal, Index badge flip, `Current alpha constraints` verify-no-op); `KANBAN.md` moved the `WIP-ALPHA-015-0.0.6` card body to `DONE-015-0.0.6` (verbatim-from-spec) and refreshed the Snapshot to record `0.0.6` as complete; `CHANGELOG.md` `[Unreleased]` gained five new entries (three `Added` + two `Changed`) verbatim from the spec. The spec stays at its working location per BUILD.md default; archival remains an opt-in maintainer call. The `0.0.6` patch's three-card cluster (012, 013, 014, 015) is now consistently documented as shipped across every reader surface.

### Spec changes made (Worker 1 only)

None.

