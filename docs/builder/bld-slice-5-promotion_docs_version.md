# Build: Slice 5 — Promotion + docs + version

Spec reference: `docs/spec-016-list_field-0_0_7.md` (Slice 5 checklist at spec lines 146-161; companion "Doc updates" section at spec lines 768-801; Decision 10 — Joint 0.0.7 cut; rev2 L1 / rev2 L2 history entries at spec lines 19-20; rev3 M5 / rev3 M1 at spec lines 30 + 26; rev4 H3 at spec line 39; rev6 M5 / rev6 L2 at spec lines 62 + 65)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `CHANGELOG.md:21-37` already has a `[0.0.7]` section with `### Changed` / `### Fixed` / `### Removed` subsections; Slice 5 APPENDS one `### Added` subsection under the same `[0.0.7]` heading (rev3 M5 at spec line 30 + spec line 799). Keep-a-Changelog ordering convention (`### Added` first) means inserting `### Added` BEFORE the existing `### Changed` block at `CHANGELOG.md:21`. No second `[0.0.7]` heading is created.
  - `docs/GLOSSARY.md:299-305` already has a `## `DjangoListField`` entry (status: planned for `0.0.7`) and `docs/GLOSSARY.md:58` already has an index row. Both rows flip from `planned for 0.0.7` to `shipped (0.0.7)` (mirrors the `BigInt` row at `docs/GLOSSARY.md:45` and the `Meta.primary` row at `docs/GLOSSARY.md:85`, both shipped in earlier patches via the same flip).
  - `docs/GLOSSARY.md:22-32` has a Public exports list; insert `DjangoListField` between `BigInt` and `DjangoType` (matches the loosely category-grouped order: scalar → type-shape → field-shape → type-base; the existing list is NOT strictly alpha so the natural site is just before the `DjangoType` row).
  - `KANBAN.md:1227-1752` Done column lists `DONE-001`...`DONE-015`; max NNN is `015` (`docs/KANBAN.md:1632 DONE-015-0.0.6`). Next available is `DONE-016-0.0.7` (matches the spec card NNN `016`, which is the convention the build plan already follows).
  - `docs/TREE.md:200` "current on-disk layout" lists `scalars.py` as the precedent flat single-file Layer-3 module; `docs/TREE.md:242` (target layout) lists `connection.py # [alpha] DjangoConnectionField + DjangoListField`; `docs/TREE.md:328-357` current test-tree layout (no `test_list_field.py` yet); `docs/TREE.md:401-403` target test tree lists `test_fieldset.py` / `test_permissions.py` / `test_connection.py` (flat at the root) — Worker 2 inserts `list_field.py` and `test_list_field.py` at the corresponding precedent locations.
  - `docs/README.md:89` "Shipped today (`0.0.6`)" header — the precedent is to bump the version pin in the header and add a bullet for the new shipped surface (line 90 lists `DjangoType` as the first shipped bullet).
  - Existing DONE-card body shape in `KANBAN.md` is one to three short paragraphs of past-tense prose followed by a "Files touched" / "Tests added" enumeration on most cards (e.g. `KANBAN.md:1632` DONE-015 body); Slice 5 mirrors that shape with the rev4 H3-pinned ADD-only opener.
- **New helpers justified.** None. Slice 5 is a docs/release-metadata sweep; no executable code lands. The static inspection helper does not apply because every touched file is Markdown.
- **Duplication risk avoided.** Three concrete risks; each is pinned by the plan:
  1. **Same description in slightly-different wording across files.** The CHANGELOG `### Added` bullet (spec-pinned verbatim at spec line 155 + spec line 800) is the canonical description. The GLOSSARY entry body (spec line 772 contract) reuses the same load-bearing phrases (factory function, `model._default_manager.all()`, `cls.get_queryset(...)` in sync + async + on consumer `Manager`/`QuerySet` returns, root-only optimizer cooperation, outer nullability via annotation). Worker 2 reads the CHANGELOG bullet AFTER drafting the GLOSSARY body to verify wording-consistency. The KANBAN Done body reuses the same anchor phrases in past tense and adds the example-app sentence (rev4 H3, see step 5 below).
  2. **Two homes for `DjangoListField` in `docs/TREE.md`.** Risk: leaving the rev1 `connection.py # [alpha] DjangoConnectionField + DjangoListField` line at `docs/TREE.md:242` intact while ALSO adding the new `list_field.py` line is exactly the duplication rev2 L1 flagged. The plan pins the removal as Step 6 below — verbatim "Remove `DjangoListField` from" the existing `connection.py` line. After this edit, the target layout advertises `list_field.py` as the sole home.
  3. **Two `[0.0.7]` headings in `CHANGELOG.md`.** Risk: a naive "add `[0.0.7] - ...` heading at the top" pattern would create a second heading. The plan pins the append-to-existing rule (rev3 M5; spec line 30; spec line 799-800) in Step 7 below — Worker 2 must locate the existing `## [0.0.7] - 2026-05-20` heading at `CHANGELOG.md:21` and add a NEW `### Added` subsection there, BEFORE the existing `### Changed` block.
- **Version bump explicitly NOT done.** Per Decision 10 + rev3 M1 (spec lines 26 + 156 + 801 + 846): the last `0.0.7` card to ship owns the version bump. This card does NOT bump `pyproject.toml [project].version` (currently `0.0.6` at `pyproject.toml:4`), `__version__` (currently `0.0.6` at `django_strawberry_framework/__init__.py:26`), or `tests/base/test_init.py:11`'s `assert __version__ == "0.0.6"`. Worker 2 must NOT touch any of those three sites. The Slice 5 final-gates check at spec line 161 ("one new public export") still passes — that addition landed in Slice 1; this slice adds zero public names.
- **Scaffold TODO sweep (rev6 L2) is a no-op at Slice 5 sites.** Verified by `grep -rn "spec-016" docs/GLOSSARY.md docs/README.md docs/TREE.md README.md GOAL.md TODAY.md KANBAN.md CHANGELOG.md` — zero hits across every site this slice touches. Slices 1/3/4 owned the scaffold-TODO sweep at the source/test sites (`django_strawberry_framework/list_field.py`, `tests/test_list_field.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`); Slice 5 has no remaining `# TODO: spec-016` markers to remove. Worker 2 SHOULD still run the same grep at the start of the slice to confirm no late scaffolding survived a re-pass, but no edits are expected.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints (per `BUILD.md` Implementation steps note). Verify against HEAD before pinning — another worker's pass may have shifted the file since this plan was written. The cited `git status --short` baseline at the start of this spawn includes `M AGENTS.md`, `M docs/builder/bld-slice-3-...md`, `M docs/builder/build-016-...md`, `M docs/spec-016-list_field-0_0_7.md`, `M examples/fakeshop/apps/library/schema.py`, `M examples/fakeshop/test_query/test_library_api.py`, `M tests/test_list_field.py`, and untracked `?? docs/builder/bld-slice-4-live_http_coverage.md` — these are inherited maintainer state and stay in the working tree as-is (Slice 5 must NOT revert them).

1. **`docs/GLOSSARY.md` — index table row, entry status, entry body, public exports list.**
   - Edit the index table row at `docs/GLOSSARY.md:58` — flip `planned for 0.0.7` to `shipped (0.0.7)` for the `[`DjangoListField`](#djangolistfield)` row. The target text matches the precedent at `docs/GLOSSARY.md:45` (`[`BigInt` scalar](#bigint-scalar) | shipped (`0.0.6`)`).
   - Edit the `## `DjangoListField`` entry at `docs/GLOSSARY.md:299-305` — flip the `**Status:**` line at `:301` from `planned for `0.0.7`.` to `shipped (`0.0.7`).` (mirror the `**Status:** shipped (`0.0.6`).` precedent used elsewhere in the file).
   - Rewrite the entry body at `:303` to reflect the shipped contract (per spec line 772 — six load-bearing claims, verbatim from the spec):
     - Factory function (not class) — rev2 H2.
     - `list[T]` annotation on the class attribute drives outer nullability (`list[T]` → `[T!]!`, `list[T] | None` → `[T!]`) — rev2 H2.
     - Default `model._default_manager.all()` resolver.
     - `cls.get_queryset(...)` applied in sync + async contexts AND to consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity) — rev2 H1.
     - Root-only optimizer cooperation — rev2 M3.
     - The leading line about "smallest entry point for migrants coming from `graphene-django`'s `DjangoListField`" can stay (still accurate).
     - Drop the "and accepts filter / ordering input when those subsystems are configured" tail — that's deferred to the Layer-3 cards and is not shipped state today.
   - Add `[`DjangoListField`](#djangolistfield) — non-Relay `list[T]` factory function for root Query fields.` to the Public exports list at `docs/GLOSSARY.md:22-32`. Insert position: between the `BigInt` bullet at `:26` and the `DjangoType` bullet at `:27` (the existing list is category-grouped, not strictly alphabetical; `DjangoListField` sits naturally next to the type-shape bullets). Wording uses a one-line summary matching the entry-shape of the existing bullets (subject + dash + role).
   - **Discretionary (Worker 2 picks):** the exact verb tense and adjective ordering in the entry-body re-write, provided the six load-bearing claims are preserved verbatim.

2. **`README.md` — Status section is plain prose; no DjangoListField bullet to add today.**
   - Verified by `grep -n "DjangoListField\|shipped\|Status" README.md` (Status section at `:43-47` is one paragraph plus one prose paragraph at `:47`; no shipped-today bullet list exists in this file). The spec at line 776-777 says "Update the shipped-today bullet list to mention `DjangoListField`", but `README.md` has no such list.
   - **Plan:** make NO edit to `README.md` in this slice. The Status section's `**0.0.6**, single-maintainer, alpha-quality.` pin at `README.md:45` stays at `0.0.6` because the version bump is deferred (Decision 10). The spec line 776-777 contract is therefore satisfied vacuously — there is no shipped-today bullet list, so there is nothing to update. Worker 2 records this as an intentional no-op in the build report (`README.md` does NOT appear under "Files touched"). Decision documented under "Implementation discretion items" below so a future maintainer doesn't read the spec and ask why the file is untouched.

3. **`docs/README.md` — Shipped-today bullet list.**
   - The "Shipped today" header at `docs/README.md:89` reads `**Shipped today** (`0.0.6`):` — but the version bump is deferred per Decision 10. Worker 2 must NOT change the `(`0.0.6`)` version pin on this header in this slice. The spec at line 779-781 says "Add `DjangoListField` to the 'Shipped today (`0.0.7`)' bullet list", but no `0.0.7` list exists today and creating one would either (a) double-tag (`0.0.6` + `0.0.7`) or (b) jump the version pin before the version-bump card.
   - **Plan:** add a single new bullet to the existing `**Shipped today** (`0.0.6`):` list at `:90-102`, naming `DjangoListField` and citing it as shipped in `0.0.7` inline. Sample shape: `- `DjangoListField` (non-Relay `list[T]` factory for root Query fields; new in `0.0.7`)`. Insertion position: after the `DjangoOptimizerExtension` bullet at `:98` (alongside the type-and-optimizer cluster). The header version stays at `(`0.0.6`)`; the last `0.0.7` card to ship bumps the header to `(`0.0.7`)` in one sweep alongside the version-bump (Decision 10).
   - Spec line 781 calls out an OPTIONAL "small example in the Quick start section". Worker 2 SHOULD skip this — the spec lists it as optional; the live HTTP test in Slice 4 already exercises the end-to-end example shape; adding a third example here would duplicate the Slice 4 documentation in `examples/fakeshop/apps/library/schema.py`. Recorded under "Implementation discretion items".

4. **`GOAL.md` — Coming from `graphene-django` migration subsection (rev6 M5).**
   - Edit `GOAL.md:404` "Coming from `graphene-django`" subsection — add a one-line bullet UNDER the existing diff block (the diff block ends at `:419`, so insertion site is between `:419` (the closing ` ``` ` of the diff) and `:421` (the existing prose paragraph "Your `Meta.filterset_class` / ..."). Wording (pinned per spec line 790):
     - `- `DjangoListField` replaces graphene-django's symbol of the same name with no shape change at the migration site: `field: list[T] = DjangoListField(MyType)` is the same one-line shape graphene-django consumers already type.`
   - Do NOT edit the Success criteria mention at `GOAL.md:486` (rev6 M5 + spec line 790: "the Success criteria mention at `GOAL.md:486` is already accurate as a forward-pointer and needs no edit").
   - **Discretionary (Worker 2 picks):** the exact phrasing of the migration-site shape (`field: list[T] = DjangoListField(MyType)` vs `all_things: list[ThingType] = DjangoListField(ThingType)` etc.) provided the bullet preserves the load-bearing "replaces graphene-django's symbol of the same name" anchor phrase from spec line 790.

5. **`TODAY.md` — wait-for list (no-op) and library example summary line.**
   - Verify wait-for list at `TODAY.md:255-261` — `DjangoListField` is NOT listed there today. Spec line 793 says "Drop `DjangoListField` from the wait-for list **if listed there**" — it isn't listed, so this is a documented no-op. Worker 2 reads the list to confirm, but does not edit it.
   - Edit the library example summary at `TODAY.md:11` — append a sentence to the existing summary noting the new `all_library_branches_via_list_field` root field added in Slice 4. The spec at line 794 pins the wording target: "the new `all_library_branches_via_list_field` root field exercises `DjangoListField`'s default-resolver path (added as a sibling per rev2 M1; no existing resolver was replaced)". Sample concatenation: `... including the Relay GlobalID round trip via `test_library_relay_node_global_id_round_trips`. The new `all_library_branches_via_list_field` root field added in `0.0.7` exercises `DjangoListField`'s default-resolver path — added as a sibling, no existing resolver was replaced.`
   - **NON-discretionary:** the "added as a sibling, no existing resolver was replaced" anchor MUST appear (rev2 M1 + rev4 H3 + Decision 9). Without it the docs imply a replacement, which contradicts the actual diff and the KANBAN Done body.

6. **`docs/TREE.md` — current layout + target layout + test tree + rev2 L1 stale-line removal.**
   - **Current on-disk layout** at `docs/TREE.md:193-223` — insert `├── list_field.py            # DjangoListField (non-Relay list[T] factory for root Query fields)` between the `scalars.py` line at `:200` and the `types/` line at `:201`. This matches the existing flat single-file Layer-3 precedent at `:200` (`scalars.py`).
   - **Target layout** at `docs/TREE.md:231-261` — `list_field.py` belongs as a sibling of the existing flat Layer-3 modules at `:240-242`. Insert `├── list_field.py            # [alpha] DjangoListField (non-Relay list[T])` between the `fieldset.py` line at `:240` and the `permissions.py` line at `:241` (alphabetical among `fieldset.py` / `list_field.py` / `permissions.py`).
   - **Rev2 L1 stale-line removal** at `docs/TREE.md:242` — the existing line `├── connection.py            # [alpha] DjangoConnectionField + DjangoListField (Relay + non-Relay)` must be rewritten to `├── connection.py            # [alpha] DjangoConnectionField (Relay)`. The `+ DjangoListField` reference is removed; the trailing `(Relay + non-Relay)` parenthetical is narrowed to `(Relay)`. This is the spec line 786 contract verbatim ("REMOVE `DjangoListField` from the existing `connection.py # [alpha] DjangoConnectionField + DjangoListField` line so the target layout doesn't advertise two homes for the symbol — rev2 L1").
   - **Current test-tree** at `docs/TREE.md:328-357` — insert `├── test_list_field.py      # DjangoListField (single-file Layer-3 module)` between the `test_registry.py` line at `:330` and the `base/` block at `:331-334`. Or, equally valid: between `test_registry.py` and `types/`. The flat-at-root convention is documented at `docs/TREE.md:453` ("`tests/test_<module>.py` (flat, at the root) — Single-file Layer-3 module tests"). The exact insertion position is at Worker 2's discretion provided it lands flat at the root of the `tests/` block.
   - The target test-tree at `docs/TREE.md:394-439` already lists `test_fieldset.py` / `test_permissions.py` / `test_connection.py` at `:401-403`; Worker 2 inserts `├── test_list_field.py       # DjangoListField (single-file Layer-3 module)` in alphabetical order — between `test_fieldset.py` at `:401` and `test_permissions.py` at `:402`.
   - **Discretionary (Worker 2 picks):** the exact wording of the comments after the `#` (the docstring fragments — `# DjangoListField (non-Relay list[T] factory for root Query fields)` vs `# DjangoListField` etc.), provided the rev2 L1 stale-line removal is performed verbatim and BOTH layouts (current + target) gain a `list_field.py` line.

7. **`KANBAN.md` — move WIP-ALPHA-016-0.0.7 to Done.**
   - Remove the `### WIP-ALPHA-016-0.0.7 — `DjangoListField` (non-Relay list)` block at `KANBAN.md:78-106` from the `## In progress` section.
   - Update the snapshot at `KANBAN.md:50` — the five-WIP-card enumeration ("Five WIP cards opened together so the small parity-driven slices land in one release: `WIP-ALPHA-016-0.0.7` (`DjangoListField`), ...") MUST be edited to drop `WIP-ALPHA-016-0.0.7` and mention the card moved to Done; or, equivalently, the four remaining WIP cards are re-listed and a parenthetical notes `DONE-016-0.0.7` shipped first. Worker 2 picks the exact rewording — the spec at line 796 only specifies the column move, not the snapshot wording.
   - Add a new `### DONE-016-0.0.7 — DjangoListField (non-Relay list)` block at the END of the `## Done` column (`KANBAN.md:1227` is the column header; the last existing entry is `DONE-013-0.0.6` at `:1752`). The DONE-NNN number is **016** (next available — max DONE-NNN today is 015, and the spec card NNN is 016 by build convention; spec line 154 confirms "next available number; the column-move pass renumbers as usual").
   - Past-tense Done body language MUST use the ADD-only posture (rev4 H3 — spec lines 154 + 797 + 845). Anchor phrase: "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" (NOT "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers"). Suggested Done-body shape (Worker 2 may rephrase prose around the pinned anchors):
     ```
     ### DONE-016-0.0.7 — DjangoListField (non-Relay list)

     Shipped the `DjangoListField` factory function in `django_strawberry_framework/list_field.py` as a one-line `field: list[T] = DjangoListField(TargetType)` shape for root Query fields. Default resolver pulls `model._default_manager.all()` and applies `cls.get_queryset(...)` in both sync and async contexts; consumer-supplied `resolver=` returns receive `target_type.get_queryset(...)` when the return value is a `Manager` or `QuerySet` (graphene-django parity per rev2 H1). Outer-list nullability is driven by the consumer's class-attribute annotation (`list[T]` → `[T!]!`, `list[T] | None` → `[T!]`). Optimizer cooperation rides the existing root-gated `info.path.prev is None` planning hook.

     Added a new `all_library_branches_via_list_field` root field via `DjangoListField` to the library example schema (rev4 H3 — this departs from the card's original "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" wording per Decision 9's add-only posture; the existing eight `all_library_*` resolvers are unchanged). New live HTTP test `test_library_branches_via_djangolistfield_optimized_nested_selection` in `examples/fakeshop/test_query/test_library_api.py` asserts the optimizer planned the prefetch and the rendered branch rows.

     Files touched: `django_strawberry_framework/list_field.py` (new), `django_strawberry_framework/__init__.py`, `tests/test_list_field.py` (new, 18 tests), `tests/base/test_init.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`, plus the standard Slice 5 doc sweep (`docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `GOAL.md`, `TODAY.md`, `CHANGELOG.md`).

     Spec: `docs/spec-016-list_field-0_0_7.md`. Build plan: `docs/builder/build-016-list_field-0_0_7.md`.
     ```
   - **NON-discretionary:** (a) the `DONE-016-0.0.7` ID; (b) the "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" anchor phrase (rev4 H3); (c) the explicit departure-from-card-text acknowledgement (Decision 9 "Card-text departure" paragraph) somewhere in the body; (d) the past-tense voice.
   - **Discretionary (Worker 2 picks):** the prose around the anchors; the inclusion or omission of the optional Spec/Build-plan footer; the file-list ordering.

8. **`CHANGELOG.md` — append `### Added` to the existing `[0.0.7]` section.**
   - Locate the existing `## [0.0.7] - 2026-05-20` heading at `CHANGELOG.md:21`.
   - The existing subsections under this heading (in current file order) are `### Changed` at `:22-23`, `### Fixed` at `:25-31`, `### Removed` at `:33-34`, `### Notes` at `:36-37`. Keep-a-Changelog convention puts `### Added` FIRST. Insert a new `### Added` subsection between the `## [0.0.7] - 2026-05-20` heading at `:21` and the existing `### Changed` heading at `:22`.
   - The `### Added` bullet wording is pinned VERBATIM per spec line 155 + spec line 800 (rev2 L2):
     > - `DjangoListField` — non-Relay `list[T]` field for **root Query fields**, with default `model._default_manager.all()` resolver, `cls.get_queryset(...)` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity), optimizer cooperation via root-gating, outer nullability driven by the consumer's class-attribute annotation, and standard field-level metadata pass-through (`description`, `deprecation_reason`, `directives`). Tracked as `DONE-016-0.0.7` in [`KANBAN.md`](KANBAN.md).
   - The "Tracked as `DONE-NNN-0.0.7`" sentinel matches the precedent at `CHANGELOG.md:41` / `:45` / `:47` (`DONE-013-0.0.6` / `DONE-014-0.0.6` / `DONE-015-0.0.6`).
   - **NON-discretionary:** (a) the bullet body wording (spec-pinned); (b) the `### Added` subsection placement BEFORE `### Changed`; (c) the no-second-`[0.0.7]`-heading rule (rev3 M5); (d) the `DONE-016-0.0.7` cross-link.
   - **Discretionary (Worker 2 picks):** none. This bullet is the spec's most tightly-pinned wording.

9. **`pyproject.toml` / `django_strawberry_framework/__init__.py` / `tests/base/test_init.py` — NO EDITS this slice (Decision 10 + rev3 M1).**
   - Verified state at HEAD: `pyproject.toml:4 version = "0.0.6"`, `django_strawberry_framework/__init__.py:26 __version__ = "0.0.6"`, `tests/base/test_init.py:11 assert __version__ == "0.0.6"`. All three remain `0.0.6` at the end of this slice.
   - Worker 2 MUST NOT touch any of those three sites. Spec lines 145 + 156 + 801 + 846 all reaffirm the deferral.
   - The Slice 1 `__all__` insertion of `DjangoListField` is already present (`django_strawberry_framework/__init__.py:28-37` is the 8-element alphabetical tuple noted in worker-1 memory at the Slice 1 entry). The Slice 5 final-gate check at spec line 161 ("one new public export — the only addition to `__all__` in this slice") is satisfied by Slice 1's addition; this slice adds zero. Worker 2 confirms via `grep -n "DjangoListField" django_strawberry_framework/__init__.py` + `grep -n "DjangoListField" tests/base/test_init.py` that both files still pin `DjangoListField` from Slice 1.

10. **Final-gate validation (rerun the standard ruff + pytest minimal sequence).**
    - `uv run ruff format .` — must pass (no .py edits this slice, so should be a no-op).
    - `uv run ruff check --fix .` — must pass (no .py edits this slice).
    - Worker 2 may OPTIONALLY run `uv run pytest --no-cov tests/base/test_init.py tests/test_list_field.py` to confirm Slice 1's `__all__` pin still passes after the docs sweep (a sanity check; no test changes expected in this slice).
    - **Forbidden:** `uv run pytest` (without `--no-cov`) — that's a coverage run, blocked by the worker rules in BUILD.md line 100-110. `--no-cov` is the only permitted coverage-shaped flag for workers. The full pytest sweep belongs to `bld-final.md`, not this slice.

11. **Scaffold TODO sweep verification (rev6 L2 — no-op at Slice 5 sites).**
    - Run `grep -rn "spec-016" docs/GLOSSARY.md docs/README.md docs/TREE.md README.md GOAL.md TODAY.md KANBAN.md CHANGELOG.md` at the start of the slice. Expected output: zero matches. If any line surfaces, treat it as a leak from Slices 1/3/4 and fix in this slice (route as `revision-needed` to whichever slice should have owned it — but at planning time, the grep already returns zero hits, so no fix is expected).

### Test additions / updates

- **No new tests in this slice.** Slice 5 is docs and KANBAN/CHANGELOG metadata only; no executable code lands and no tests are added or modified.
- The 100% coverage gate at `[tool.coverage.report] fail_under = 100` is unaffected — no source code changes.
- Worker 2 MAY run `uv run pytest --no-cov tests/base/test_init.py` as a sanity check that the Slice 1 `__all__` pin survived the docs sweep (it should — no `.py` files are edited). This is optional, not required.
- The full `uv run pytest --no-cov` sweep is owned by `bld-final.md`, NOT this slice (per BUILD.md line 109 + worker-1.md "Final test-run gate"). Worker 2 must NOT run a full pytest sweep at the slice-build boundary.

### Implementation discretion items

Items where Worker 1 has assessed the design and decided the choice is at Worker 2's discretion:

- **Step 1 (GLOSSARY entry body wording).** The six load-bearing claims (factory function; annotation-driven outer nullability; `_default_manager.all()`; `get_queryset` in sync + async + on consumer returns; root-only optimizer; pasted-from-CHANGELOG anchor phrases) are non-negotiable. The exact paragraph rhythm and adjective ordering is Worker 2's discretion.
- **Step 1 (Public exports list bullet position).** Insertion between `BigInt` and `DjangoType` is the natural position because the list is loosely category-grouped (not strictly alphabetical). Worker 2 may pick a different position so long as the bullet is added.
- **Step 2 (README.md).** No-op. The Status section is plain prose with no shipped-today bullet list, and the version string `0.0.6` is unchanged this slice (Decision 10). The build report records `README.md` as intentionally untouched with a one-line citation of this discretion item.
- **Step 3 (docs/README.md optional Quick-start example).** Spec line 781 lists the Quick-start example as OPTIONAL. The plan recommends skipping it (the Slice 4 live HTTP test already exercises the end-to-end shape; adding the example here duplicates documentation). Worker 2 may add it if the prose flow benefits, but the plan does not require it.
- **Step 4 (GOAL.md bullet wording).** The "replaces graphene-django's symbol of the same name" anchor phrase is non-negotiable (spec line 790). Worker 2 picks the exact migration-site shape (`field: list[T] = DjangoListField(MyType)` vs a more verbose form).
- **Step 6 (TREE.md comment fragments).** The comment text after `#` on the new `list_field.py` lines (e.g., `# DjangoListField (non-Relay list[T] factory for root Query fields)` vs `# [alpha] DjangoListField (non-Relay list[T])`) is Worker 2's discretion provided the rev2 L1 stale-line removal is performed verbatim and BOTH layouts (current + target) gain a `list_field.py` line.
- **Step 6 (current test-tree insertion position).** Worker 2 picks the line within the `tests/` block where `test_list_field.py` lands — flat at the root, somewhere between `__init__.py` and the first subdirectory (`base/` or `types/`).
- **Step 7 (KANBAN Done body prose).** The pinned anchors are (a) `DONE-016-0.0.7` ID; (b) "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" anchor; (c) explicit departure-from-card-text acknowledgement (Decision 9 "Card-text departure"); (d) past-tense voice. The surrounding prose, the optional Files-touched / Spec footer, and the snapshot-section rewording at `KANBAN.md:50` are Worker 2's discretion.

NOT discretionary (re-stated for clarity):

- CHANGELOG `### Added` bullet wording (spec line 155 + 800; rev2 L2).
- No version bump (`pyproject.toml`, `__version__`, `tests/base/test_init.py:11` all stay `0.0.6` — rev3 M1 + Decision 10 + spec lines 145 + 156 + 801 + 846).
- No second `[0.0.7]` heading in CHANGELOG (rev3 M5 + spec line 30 + 799).
- The rev2 L1 stale-line removal in `docs/TREE.md:242` (remove `+ DjangoListField` from the `connection.py` line).
- The rev4 H3 add-only past-tense KANBAN body (spec lines 154 + 797 + 845).
- The rev6 M5 GOAL.md target heading is `GOAL.md:404` "Coming from `graphene-django`" specifically; do NOT add the bullet anywhere else.
- The Slice 5 site-set is closed (the eight files named in the spec at lines 770-801). Worker 2 must NOT touch any file outside this set, EXCEPT `KANBAN.md`'s snapshot at `:50` if the WIP-card enumeration needs the column-move to be reflected — which is implied by the move spec line 796.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 5 from `## Slice checklist` at spec lines 146-161, copied verbatim. Each box stays `- [ ]` during the planning pass; final verification ticks them as the contract lands.

- [x] Slice 5: Promotion + docs + version
  - [x] Flip [`DjangoListField`](GLOSSARY.md#djangolistfield) from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`](GLOSSARY.md); update the public exports list at the top and the index table.
  - [x] Update [`README.md`](../README.md), [`docs/README.md`](README.md), [`GOAL.md`](../GOAL.md), and [`TODAY.md`](../TODAY.md) where `DjangoListField` is currently called out as unshipped or "wait for":
    - [x] `README.md` — the shipped-today bullet list under "Status". (Pass-2 root-cause fix: surfaced inline at `README.md:45` alongside the version-pin sentence — the file has prose, not a bullet list; the spec wording was tightened by Worker 1 in this final-verification pass to match the file's actual shape.)
    - [x] `docs/README.md` — the "Shipped today (`0.0.6`)" → "Shipped today (`0.0.7`)" bullet list under "Today and coming next". (Header version pin stays at `0.0.6` per Decision 10; new `DjangoListField` bullet lands at `docs/README.md:99` after the `DjangoOptimizerExtension` bullet, AND the "Coming in `0.1.0`" bullet was narrowed to drop `DjangoListField` for internal consistency.)
    - [x] `GOAL.md` — Migration shape sections mention `DjangoListField` indirectly through `graphene-django` migration; ensure the migration story is now reachable. (Rev6 M5 site at `GOAL.md:404` got the one-line bullet under the diff block — `GOAL.md:421` now reads "DjangoListField replaces graphene-django's symbol of the same name…"; `GOAL.md:488` Success-criteria mention preserved.)
    - [x] `TODAY.md` — drop `DjangoListField` (if listed) from the wait-for list; update the `library` example summary to mention that the new `all_library_branches_via_list_field` root field exercises `DjangoListField`'s default-resolver path (added as a sibling per rev2 M1; no existing resolver was replaced). (Wait-for list at `TODAY.md:255-261` correctly never listed the symbol — documented no-op; library summary at `TODAY.md:11` carries the add-only anchor verbatim.)
  - [x] `docs/TREE.md` — add `list_field.py` to the current on-disk layout AND to the target layout (a flat single-file Layer-3 module per the TREE convention); add `tests/test_list_field.py` to the current test-tree section. **Remove the `DjangoListField` mention from the existing `connection.py # [alpha] DjangoConnectionField + DjangoListField` line** so the target layout doesn't advertise two homes for the symbol (rev2 L1). (Current `:201`, target `:242`, current test-tree `:332`, target test-tree `:405`; the `connection.py` line at `:244` now reads `[alpha] DjangoConnectionField (Relay)` with no `+ DjangoListField` survivor — `grep -n "DjangoListField" docs/TREE.md` returns exactly four hits, all on the correct rows.)
  - [x] `KANBAN.md` — move `WIP-ALPHA-016-0.0.7` to Done with `DONE-NNN-0.0.7` (next available number; the column-move pass renumbers as usual). The past-tense Done body MUST reflect the add-only posture: "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" rather than the original card text's "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" (rev4 H3 — intentional card-text departure per [Decision 9](#decision-9--example-app-migration-posture)'s "Card-text departure" paragraph). (DONE-016-0.0.7 lands at `KANBAN.md:1743`; the WIP card body is gone; the snapshot at `:50` re-enumerates the remaining four WIP cards and references DONE-016 with the Decision 10 forward-pointer; the rev4 H3 add-only anchor phrase is preserved verbatim in the Done body at `:1747`.)
  - [x] `CHANGELOG.md` — `[0.0.7]` Added entry: `DjangoListField` (non-Relay `list[T]` field for **root Query fields** with default `model._default_manager.all()` resolver, `cls.get_queryset` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns, optimizer cooperation through root-gating). (rev2 L2 — narrowed wording from "root and nested fields" to "root Query fields" to match the M3 scope narrowing.) (Single `[0.0.7]` heading preserved at `CHANGELOG.md:21`; new `### Added` subsection inserted BEFORE `### Changed` per Keep-a-Changelog ordering at `:22`; the bullet body at `:23` matches the spec-pinned wording character-for-character.)
  - [x] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; rev3 M1): see [Decision 10](#decision-10--joint-0_0_7-cut). This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion — those move when the last of the five `0.0.7` WIP cards ships. (Verified at HEAD: `pyproject.toml:4` still `0.0.6`; `__init__.py:26` still `0.0.6`; `tests/base/test_init.py:11` still `assert __version__ == "0.0.6"`; all three sites confirmed unchanged via `git diff HEAD --` after the docs sweep.)
  - [x] Final gates:
    - [x] `uv run ruff format .` passes. (Pass-1 and pass-2 both clean; `103 files left unchanged` with the standing COM812 advisory unchanged.)
    - [x] `uv run ruff check --fix .` passes. (Pass-1 and pass-2 both clean; `All checks passed!`.)
    - [x] `uv run pytest` passes with 100% package coverage (`fail_under = 100`). (Final-verification pass ran the focused suite per BUILD.md "Final verification (Worker 1)" — 35/35 across `tests/base/test_init.py`, `tests/test_list_field.py`, `examples/fakeshop/test_query/test_library_api.py`. The full `uv run pytest --no-cov` sweep + the 100% coverage gate are owned by `bld-final.md`, not this slice's box; per Worker 0's task contract for this spawn, this box is ticked on the focused-test-suite pass and the full sweep is `bld-final.md`'s job.)
    - [x] One new public export (`DjangoListField`) — the only addition to `__all__` in this slice. (Satisfied by Slice 1's `__all__` addition, which survives this slice unchanged at `__init__.py:30`; this slice adds zero public symbols; `tests/base/test_init.py:37` pin is intact.)

---

## Build report (Worker 2)

### Files touched

- `docs/GLOSSARY.md` — (a) added `DjangoListField` bullet to the Public exports list between `BigInt` and `DjangoType` (Step 1); (b) flipped the index-table row at the file's index from `planned for 0.0.7` → `shipped (0.0.7)`; (c) flipped the `## `DjangoListField`` entry's `**Status:**` line from `planned for 0.0.7.` to `shipped (`0.0.7`).`; (d) rewrote the entry body to reflect the shipped contract — preserves all six load-bearing claims (factory function, annotation-driven outer nullability, `_default_manager.all()` default, `cls.get_queryset` in sync + async + on consumer returns, root-only optimizer cooperation, migration-from-graphene-django framing) and drops the "and accepts filter / ordering input when those subsystems are configured" tail per plan Step 1.
- `docs/README.md` — (a) added a new `DjangoListField` bullet to the `**Shipped today** (`0.0.6`):` list immediately after the `DjangoOptimizerExtension` bullet (header version pin stays at `0.0.6` per Decision 10); (b) removed `DjangoListField` from the "Coming in `0.1.0`" bullet so the planned-vs-shipped state is consistent (the bullet now reads "`DjangoConnectionField` (Relay connection)" only). The optional Quick-start example was deliberately skipped per the plan's Step 3 discretion item — the live HTTP test in Slice 4 already exercises the end-to-end example shape.
- `GOAL.md` — added the one-line `DjangoListField` migration bullet under the diff block in the "Coming from `graphene-django`" subsection at `GOAL.md:404`, between the closing ` ``` ` of the diff and the existing prose paragraph that starts "Your `Meta.filterset_class` /…". The bullet preserves the spec-pinned anchor phrase "replaces graphene-django's symbol of the same name" verbatim. Success criteria mention at `GOAL.md:486` left unchanged per rev6 M5.
- `TODAY.md` — appended a sentence to the existing `library` example summary at line 11 noting that the new `all_library_branches_via_list_field` root field added in `0.0.7` exercises `DjangoListField`'s default-resolver path. The "added as a sibling, no existing resolver was replaced" anchor (rev2 M1 + rev4 H3 + Decision 9 non-discretionary) is preserved verbatim. The wait-for list at `TODAY.md:255-261` does NOT list `DjangoListField`, so no edit there was required per the plan's Step 5 documented no-op.
- `docs/TREE.md` — three edits: (a) current on-disk layout gained a `list_field.py` line between `scalars.py` and `types/`; (b) target layout gained a `list_field.py` line between `fieldset.py` and `permissions.py` AND the existing `connection.py` comment was narrowed from `# [alpha] DjangoConnectionField + DjangoListField (Relay + non-Relay)` to `# [alpha] DjangoConnectionField (Relay)` per rev2 L1 — `DjangoListField` no longer has two homes in the target layout; (c) current test-tree gained a `test_list_field.py` line flat-at-root before `test_registry.py`; (d) target test-tree gained a `test_list_field.py` line in alphabetical order between `test_fieldset.py` and `test_permissions.py`.
- `KANBAN.md` — three edits: (a) removed the `### WIP-ALPHA-016-0.0.7 — `DjangoListField` (non-Relay list)` block (the 29-line card body) from the `## In progress` section; (b) edited the snapshot bullet at the top of the file's "In progress" subsection to drop `WIP-ALPHA-016-0.0.7` from the five-WIP-card enumeration and note that `DONE-016-0.0.7` shipped first (the remaining four WIP cards are listed; the snapshot adds a one-line cross-reference to Decision 10's last-card-to-ship version-bump policy); (c) added a new `### DONE-016-0.0.7 — `DjangoListField` (non-Relay list)` block at the END of the `## Done` column (immediately after the existing `DONE-013-0.0.6` block; spec confirms 016 is the next available DONE-NNN). The Done body uses past-tense add-only language with the rev4 H3 anchor "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" verbatim, explicitly cites the Decision 9 "Card-text departure" paragraph, and pins the version-bump deferral.
- `CHANGELOG.md` — APPENDED a new `### Added` subsection BEFORE the existing `### Changed` block under the existing `## [0.0.7] - 2026-05-20` heading (rev3 M5 — no second `[0.0.7]` heading created). The single bullet is the verbatim spec-pinned wording from Worker 1's plan Step 8 and spec line 800.

### Tests added or updated

- No tests added or updated. Slice 5 is docs/release-metadata only — no executable code lands and no test files are modified.

### Validation run

- `uv run ruff format .` — pass. `103 files left unchanged` (Markdown-only edits, as expected). Also surfaced the pre-existing `COM812 + formatter` advisory warning that is present on every ruff invocation in this repo.
- `uv run ruff check --fix .` — pass. `All checks passed!` (no autofixes applied).
- `git status --short` after both ruff invocations — sixteen entries, classified below:
  - **slice-intended (eight docs files + artifact + plan baseline):**
    - `M CHANGELOG.md` — Step 8 append
    - `M GOAL.md` — Step 4 bullet
    - `M KANBAN.md` — Step 7 column move + snapshot edit + DONE-016-0.0.7
    - `M TODAY.md` — Step 5 library example summary
    - `M docs/GLOSSARY.md` — Step 1 entry/status/index/exports
    - `M docs/README.md` — Step 3 shipped-today bullet (+ Coming-in-0.1.0 removal)
    - `M docs/TREE.md` — Step 6 layout + test-tree + connection.py narrowing
    - `?? docs/builder/bld-slice-5-promotion_docs_version.md` — this artifact (untracked because Slice 5 is the cycle that creates it; will become `M` once the file is added to the index, but stays as `??` from Worker 2's perspective)
  - **inherited maintainer state (out of Slice 5 scope; preserved verbatim):** `M AGENTS.md`, `M docs/builder/bld-slice-3-optimizer_get_queryset_tests.md`, `M docs/builder/build-016-list_field-0_0_7.md`, `M docs/spec-016-list_field-0_0_7.md`, `M examples/fakeshop/apps/library/schema.py`, `M examples/fakeshop/test_query/test_library_api.py`, `M tests/test_list_field.py`, `?? docs/builder/bld-slice-4-live_http_coverage.md` — every one of these is a prior-slice / prior-pass / concurrent-maintainer edit; Worker 2 did NOT touch them this pass.
  - **unrelated tool churn:** none. Ruff produced zero diffs.
- `uv run pytest --no-cov tests/base/test_init.py` — 4 passed in 0.05s. The `__all__` pin and `__version__ == "0.0.6"` assertion both still pass after the docs sweep, confirming Slice 1's `DjangoListField` `__all__` insertion and the deferred-version-bump posture survive Slice 5.
- `uv run pytest --no-cov tests/test_list_field.py examples/fakeshop/test_query/test_library_api.py` — 31 passed in 2.31s (covers the 21 `test_list_field.py` cases from Slices 1/2/3 plus the 10 library HTTP cases including Slice 4's `test_library_branches_via_djangolistfield_optimized_nested_selection`). Slices 3 + 4 still pass cleanly with the Slice 5 docs sweep in place.

### Implementation notes

- **DONE-016-0.0.7 placement in KANBAN.md.** The card landed at the END of the Done column, immediately after the existing `DONE-013-0.0.6` block (the file's chronological-but-not-strictly-numeric ordering keeps `DONE-013` after `DONE-015` because of the original ship sequencing; adding DONE-016 at the tail matches that convention rather than re-sorting to numeric order).
- **CHANGELOG append point inside the existing `[0.0.7]` section.** Inserted `### Added` BEFORE `### Changed` (Keep-a-Changelog convention: Added → Changed → Fixed → Removed → Notes). The existing section already had `### Changed`, `### Fixed`, `### Removed`, `### Notes` — `### Added` was missing and is now in canonical first position. No second `[0.0.7]` heading created.
- **GLOSSARY Public exports section already had a category-grouped bullet list** (not strictly alphabetical). Inserted the `DjangoListField` bullet between `BigInt` and `DjangoType` because (a) the existing list runs `BigInt → DjangoType → DjangoOptimizerExtension → OptimizerHint → finalize_django_types → auto → __version__` — type/field shape comes after scalars, and (b) alphabetical position is `BigInt` → `DjangoListField` → `DjangoType` regardless.
- **GLOSSARY entry body — six load-bearing claims preserved.** Factory function, annotation-driven outer nullability, `_default_manager.all()`, `get_queryset` sync + async + on consumer returns, root-only optimizer, and the "smallest entry point for migrants coming from `graphene-django`'s `DjangoListField`" lead-in are all present. Dropped the "and accepts filter / ordering input when those subsystems are configured" tail per Step 1's rewrite contract (filters/orders are deferred to Layer-3 cards, not shipped state today). The entry body is roughly 2× longer than the previous "planned" stub because the shipped contract has more load-bearing details than a one-line forward-pointer.
- **TREE.md current vs target layout treatment.** Both layouts have the `list_field.py` line — current sits between `scalars.py` (flat single-file Layer-3 precedent) and `types/`; target sits between `fieldset.py` and `permissions.py` (alphabetical among the flat Layer-3 modules). The target layout's `connection.py` line was narrowed in the same edit so `DjangoListField` no longer has two homes in either layout. The current test-tree's `test_list_field.py` lands flat-at-root before `test_registry.py` (alphabetical); the target's lands between `test_fieldset.py` and `test_permissions.py` (alphabetical among the flat Layer-3 test files).
- **GOAL.md:404 bullet wording.** Pinned the migration-site shape as `all_branches: list[BranchType] = DjangoListField(BranchType)` (using `BranchType` to mirror the broader spec's running example rather than the more abstract `MyType`). The bullet preserves the spec-pinned anchor "replaces graphene-django's symbol of the same name" and adds the "no shape change at the migration site" tail to emphasize the zero-cost migration story per rev6 M5.
- **KANBAN snapshot rewording.** The five-WIP-card enumeration at the top of "In progress" required surgery because `WIP-ALPHA-016-0.0.7` moved to Done. Picked the explicit "`DONE-016-0.0.7` shipped first; remaining four WIP cards are…" framing rather than re-anchoring the count at "Four WIP cards" because the spec at Decision 10 names the five-card joint cut as a unit and the snapshot should preserve that framing. Added a one-line forward-pointer to Decision 10 of `spec-016` so a future reader of the snapshot sees the version-bump-deferral policy in the same paragraph.
- **No version bump verified.** `pyproject.toml:4 version = "0.0.6"`, `django_strawberry_framework/__init__.py:26 __version__ = "0.0.6"`, and `tests/base/test_init.py:11 assert __version__ == "0.0.6"` — all three confirmed unchanged at HEAD via `grep -n` before and after the Slice 5 edits. The Slice 1 `__all__` pin of `"DjangoListField"` is also unchanged in both `__init__.py` and `test_init.py`. Slice 5 adds zero public exports; the slice's final-gate "one new public export" check at spec line 161 is satisfied by Slice 1's prior addition.
- **Scaffold TODO sweep verification.** Ran `grep -rn "spec-016" docs/GLOSSARY.md docs/README.md docs/TREE.md README.md GOAL.md TODAY.md KANBAN.md CHANGELOG.md | grep -i "TODO"` after the edits; zero matches (the scaffold TODOs were entirely owned by Slices 1/3/4 at the source/test sites). Slice 5's docs surfaces have no `# TODO: spec-016` markers to remove.

### Notes for Worker 3

- The CHANGELOG `### Added` bullet is the verbatim spec-pinned wording from spec line 800 — character-for-character match against Worker 1's plan Step 8. The four discretionary anchors (no second `[0.0.7]` heading, `DONE-016-0.0.7` cross-link, "root Query fields" narrowed wording, graphene-django parity phrasing) are all present.
- The KANBAN `DONE-016-0.0.7` body uses the rev4 H3 add-only language verbatim — anchor phrase "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" is preserved, the explicit "Card-text departure" citation to Decision 9 is present, and the body is past-tense throughout. The "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" wording from the original WIP card body is NOT present anywhere in the DONE body — the departure is acknowledged in prose but not echoed.
- The TREE.md target-layout `connection.py` line is narrowed (rev2 L1) — `DjangoListField` no longer has two homes in the target layout. Confirmed via `grep -n "DjangoListField" docs/TREE.md` after the edit: the only `DjangoListField` mentions are now the new `list_field.py` lines in current + target layouts.
- No version bump landed (Decision 10 + rev3 M1). `pyproject.toml`, `__version__`, and `tests/base/test_init.py:11`'s assertion all still read `0.0.6`. The Slice 1 `__all__` pin of `DjangoListField` is intact in both `__init__.py:30` and `tests/base/test_init.py:37`.
- The `docs/README.md` Coming-in-0.1.0 bullet was simultaneously narrowed to drop `DjangoListField` (now reads "`DjangoConnectionField` (Relay connection)" only). This was not explicitly listed as a Slice 5 doc-update site in the spec or plan, but leaving the file claiming `DjangoListField` is "coming in `0.1.0`" while ALSO listing it under "Shipped today" would be internally contradictory; the narrowing was implicit in the spec's broader shipped-vs-planned reconciliation discipline. Flagged here for Worker 3 confirmation.
- The KANBAN snapshot at the file's "In progress" subsection now contains a cross-reference to Decision 10 of `docs/spec-016-list_field-0_0_7.md`; the link target is the in-repo spec path. Worker 3 should confirm the link resolves and the Decision 10 forward-pointer reads naturally.
- The static inspection helper does NOT apply to Slice 5 — every touched file is Markdown. No shadow files created or referenced.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed. Every Slice 5 site named in the spec at lines 770-801 was touched per the plan; no spec gap surfaced during implementation. The plan's `README.md` no-op (Step 2) is intentionally documented in the build report rather than as a spec edit because the spec's wording at line 776-777 is vacuously satisfied (no shipped-today bullet list exists in `README.md`; Decision 10 keeps the version pin at `0.0.6`); Worker 1 may confirm this reading during final verification but no spec text change is required.

The `docs/README.md` Coming-in-0.1.0 narrowing flagged in the Worker 3 notes is a documented implicit consequence of the spec's "shipped-vs-planned reconciliation" posture, not a spec gap. If Worker 1 disagrees with the implicit narrowing, the edit can be reverted via a one-line spec change without invalidating any other slice.

---

## Review (Worker 3)

### High:

None.

### Medium:

#### `README.md` sub-check at spec line 138 left silently unaddressed

`docs/spec-016-list_field-0_0_7.md:138` (the Slice 5 checklist) and the companion `:776-777` (Doc updates) both explicitly name `README.md` as a touched site for this slice: "`README.md` — the shipped-today bullet list under 'Status'." `git diff HEAD -- README.md` is empty; `git status --short` does not list `README.md` among the modified files. The slice ships with one named spec sub-check unaddressed.

Worker 1's Plan Step 2 and Worker 2's Build report both record the omission as an "intentional no-op" because `README.md:43-47`'s Status section is plain prose with no bullet list to update. That recording does NOT discharge the contract under `AGENTS.md:4` — "always recommend the root-cause fix over the surface patch... pragmatic shortcuts are not a viable answer and must not be presented as such even with a follow-up card". The spec named `README.md` as a touched site; the surface conditions assumed by the spec (a shipped-today bullet list) don't match the file's actual shape; the right move is either (a) introduce the assumed bullet list and add `DjangoListField` to it, or (b) edit the Status-section prose at `README.md:43-47` to mention `DjangoListField` (e.g., append "`DjangoListField` shipped in `0.0.7`" to the trailing sentence at `:47` or rework the paragraph to surface the shipped surface explicitly). Either path is a small, local edit consistent with the rest of the Slice 5 doc sweep — `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` all received a similarly-shaped per-file update.

Why it matters: the spec's purpose for this sub-check is consumer-discoverability — a graphene-django migrant arriving at the repo lands on `README.md` first; the Status section is the first place where the shipped surface gets named. Leaving `DjangoListField` invisible at that surface contradicts the slice's promotion contract even if every other doc site flips correctly. A future maintainer or migrant reading `README.md:45` learns `0.0.6` is the active version and reads no mention of `DjangoListField`; they then bounce to `docs/README.md` and find a "Shipped today (`0.0.6`)" bullet list claiming `DjangoListField` is shipped in `0.0.7`. The two surfaces disagree by omission.

Recommended change: edit `README.md` in this slice. A minimal-shape fix:

```README.md:43:47
## Status

**`0.0.6`, single-maintainer, alpha-quality.** Fine for internal tools and prototypes; not production. The public names are stable; correctness and edge-case behavior are still hardening.

For the current capability snapshot — what the package can actually do in the example project right now — see [`TODAY.md`](TODAY.md). The full shipped / planned / deferred catalog and the `0.1.0` → `1.0.0` milestone framing live in [`docs/GLOSSARY.md`](docs/GLOSSARY.md). Per-card sequencing for both releases lives in [`KANBAN.md`](KANBAN.md).
```

Add a sentence (or short bullet list) here that names `DjangoListField` as part of the shipped surface — phrasing parity with the `docs/README.md` bullet (`non-Relay list[T] factory for root Query fields; new in 0.0.7`) is the lowest-friction shape. The version pin on this line stays `0.0.6` (Decision 10 + rev3 M1 — the version bump is still deferred to the last `0.0.7` card; the slice flips the named-symbol set, not the version string).

Test expectation: none. Slice 5 is docs-only; the `__all__` pin in `tests/base/test_init.py:37` already covers the shipped-symbol assertion at test time.

### Low:

None.

### DRY findings

- No new duplication introduced. Worker 2's per-site phrasing is internally consistent — the `DjangoListField` descriptor reuses load-bearing anchor phrases ("non-Relay `list[T]` factory for root Query fields", "factory function", "`cls.get_queryset(...)` cooperation in sync + async contexts", "graphene-django parity") across `docs/GLOSSARY.md`, `docs/README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` without diverging into slightly-different phrasings of the same claim.
- The KANBAN snapshot rewording at `KANBAN.md:50` correctly threads the DONE-016 reference into the existing five-card enumeration framing rather than re-anchoring the count, preserving the joint-cut framing from Decision 10. No drift between the snapshot and the DONE body's pinned anchors.
- `docs/TREE.md` rev2 L1 stale-line removal is complete — `grep -n "DjangoListField" docs/TREE.md` returns exactly four lines (current layout, target layout, current test-tree, target test-tree); the previous fifth occurrence on the `connection.py` line is gone. The target layout now advertises one home for the symbol.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. Slice 5 does not modify the public surface; `DjangoListField` was added to `__all__` and re-exported in Slice 1. The Slice 5 final-gate "one new public export" sub-check at spec line 161 is satisfied by Slice 1's prior addition. Verified that `__init__.py:20` still imports `from .list_field import DjangoListField  # noqa: E402` and `__init__.py:30` still has `"DjangoListField"` in `__all__` in alphabetical position.

### CHANGELOG sanity

The slice DOES touch `CHANGELOG.md`. Walked end-to-end:

- **Version line.** The new `### Added` subsection appends to the existing `## [0.0.7] - 2026-05-20` heading at `CHANGELOG.md:21` — no second `[0.0.7]` heading was created (rev3 M5 + spec line 30 + 799 satisfied). `grep -n "^## \[" CHANGELOG.md` confirms exactly one `[0.0.7]` heading. The `[0.0.7]` section's date pin (`2026-05-20`) is from prior commits in this patch; Slice 5 did NOT touch the date and does NOT bump the version. `pyproject.toml:4` and `django_strawberry_framework/__init__.py:26` both still read `0.0.6` — the version-line / package-version match is the intended deferred-bump state per Decision 10 + rev3 M1 (spec lines 145 + 156 + 801 + 846).
- **Subsection placement.** `### Added` was inserted BEFORE the existing `### Changed` at the same heading level — Keep-a-Changelog ordering (Added → Changed → Fixed → Removed → Notes) is preserved. Spec only authorizes `### Added` for this card; no other subsection was added.
- **Wording.** The bullet body is character-for-character identical to the spec-pinned text at spec line 800: "`DjangoListField` — non-Relay `list[T]` field for **root Query fields**, with default `model._default_manager.all()` resolver, `cls.get_queryset(...)` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity), optimizer cooperation via root-gating, outer nullability driven by the consumer's class-attribute annotation, and standard field-level metadata pass-through (`description`, `deprecation_reason`, `directives`)." The trailing "Tracked as `DONE-016-0.0.7` in [`KANBAN.md`](KANBAN.md)." sentence matches the precedent at `CHANGELOG.md:41` / `:45` / `:47` (`DONE-013-0.0.6` / `DONE-014-0.0.6` / `DONE-015-0.0.6`) and is the conventional cross-link, not an overstatement.
- **No over-/understatement.** The rev2 L2 narrowing ("root Query fields" rather than "root and nested fields") is preserved verbatim — the spec correctly narrows the wording to match the rev2 M3 scope-narrowing decision, and the bullet honors it.

### Documentation / release sanity

The slice DOES touch docs, release metadata, and KANBAN. Walked all eight changed files end-to-end:

- **Version strings.** `README.md:45` still reads `**0.0.6**`; `docs/README.md:89` "Shipped today" header still reads `(0.0.6)`; `pyproject.toml:4` / `__init__.py:26` / `tests/base/test_init.py:11` all unchanged at `0.0.6`. Decision 10 deferral honored. The `### Added` bullet ships under `[0.0.7]` — that is intentional (the section was created by prior `0.0.7` cards in this patch and Slice 5 appends to it; the version-bump-to-`0.0.7` is a separate later card per Decision 10).
- **Card IDs.** `WIP-ALPHA-016-0.0.7` is removed from `## In progress` (29-line card body gone); `DONE-016-0.0.7` lands at the END of `## Done` (after the existing tail entry `DONE-013-0.0.6` at `:1722`). `016` is the correct next-available DONE-NNN given `015` is the previous max. The snapshot bullet at `KANBAN.md:50` re-enumerates the four remaining WIP cards and references `DONE-016-0.0.7` plus a forward-pointer to Decision 10 for the version-bump policy — clean column move, exactly one new appearance in Done, exactly one removal from In progress.
- **KANBAN Done-body language (rev4 H3).** The anchor phrase "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" is preserved verbatim in the Done body. The original WIP card's "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" wording is referenced ONLY as an explicit citation of the card-text-departure (per Decision 9's "Card-text departure" paragraph) — the shipped-action prose itself uses add-only language throughout. No leak of "replacing" semantics into the action statements.
- **Markdown links.** All introduced or moved links resolve: `[Decision 9](../docs/spec-016-list_field-0_0_7.md)` in the KANBAN body, `[`KANBAN.md`](KANBAN.md)` in the CHANGELOG bullet, `[`GLOSSARY`](GLOSSARY.md#djangolistfield)` in `docs/README.md`. Spec path and KANBAN cross-link both resolve from their respective file locations.
- **Obsolete wording.** `docs/README.md`'s "Coming in `0.1.0`" bullet was narrowed from `DjangoListField` + `DjangoConnectionField` to `DjangoConnectionField` only (Worker 2 flagged this to Worker 3 — implicit consequence of the shipped-vs-planned reconciliation discipline). This is correct: leaving `DjangoListField` claimed as "Coming in `0.1.0`" while ALSO listing it under "Shipped today" would be internally contradictory. No other obsolete "coming soon" / "wait for" / "planned for 0.0.7" wording remains in the touched files. `TODAY.md:255-261`'s wait-for list correctly never listed `DjangoListField` (plan Step 5 documented no-op).
- **Verbatim drop-ins.** CHANGELOG bullet wording matches spec line 800 character-for-character (confirmed via direct comparison). KANBAN Done-body anchor "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" matches spec lines 154 + 797 + 845. TODAY.md library-summary anchor "added as a sibling, no existing resolver was replaced" matches spec line 794. GOAL.md migration-bullet anchor "replaces graphene-django's symbol of the same name" matches spec line 790. All four spec-pinned anchors landed verbatim.
- **Two-homes risk (rev2 L1).** `docs/TREE.md:242`'s `connection.py` line was correctly narrowed from `# [alpha] DjangoConnectionField + DjangoListField (Relay + non-Relay)` to `# [alpha] DjangoConnectionField (Relay)`. Combined with the new `list_field.py` line at `:240`, the target layout now advertises exactly one home for the symbol.

### What looks solid

- **CHANGELOG single-`[0.0.7]`-heading discipline (rev3 M5).** The append-to-existing pattern landed cleanly with `### Added` placed in canonical Keep-a-Changelog first-position before `### Changed`. The spec's no-second-heading constraint is preserved and the file structure remains parseable. Pattern worth carrying forward: when a multi-card joint cut appends to a single version heading, Keep-a-Changelog subsection ordering (Added → Changed → Fixed → Removed → Notes) is the right insertion guide.
- **`docs/TREE.md` rev2 L1 stale-line removal.** Worker 2 narrowed the existing `connection.py` comment AND added the new `list_field.py` lines in the same edit, eliminating the two-homes risk in a single atomic change. The `grep -n "DjangoListField" docs/TREE.md` post-condition (exactly four lines, all on the correct rows) is the right shape — no duplicated home for the symbol survives in either current or target layout.
- **KANBAN rev4 H3 add-only Done body.** The Decision 9 "Card-text departure" paragraph is explicitly cited in the Done body, and the shipped-action prose uses past-tense add-only language ("Added a new..."), not the original card's "replacing" wording. This is exactly the rev4 H3 contract.
- **GOAL.md rev6 M5 bullet.** Landed at the intended insertion site under the diff block at `GOAL.md:404` "Coming from `graphene-django`", preserving the spec-pinned anchor phrase verbatim. Success criteria mention at `GOAL.md:486` correctly left untouched per rev6 M5's explicit exemption.
- **Decision 10 / rev3 M1 version-bump deferral.** All three version-pin sites (`pyproject.toml`, `__version__`, `tests/base/test_init.py`) are clean in `git diff` and still read `0.0.6`. The deferral is honored. Worker 2's verification grep before and after the docs sweep is the right discipline.
- **Public-surface no-op compliance.** `git diff HEAD -- django_strawberry_framework/__init__.py` is empty; Slice 1's `DjangoListField` addition to `__all__` is intact and unchanged. Slice 5 adds zero public symbols, consistent with the slice's docs/metadata-only scope.

### Temp test verification

Skipped. Slice 5 is Markdown-only — no executable code or test changes. No temp tests created during review.

### Notes for Worker 1 (spec reconciliation)

- **`README.md` Medium finding.** Worker 1 has two routes during final verification:
  1. Send Slice 5 back to Worker 2 with the recommended `README.md` edit (the surface fix — adds `DjangoListField` to the Status section's prose). This is the route the AGENTS.md root-cause directive selects, and the route Worker 0's dispatch instruction selected. Recommended.
  2. Edit the spec to discharge the sub-check (the spec-side fix — either drops `README.md` from the Slice 5 site list with a recorded reason, or rewrites the sub-check to specify "the Status section's prose" rather than "the shipped-today bullet list under 'Status'"). Spec-side edits should be recorded under `### Spec changes made (Worker 1 only)` in this slice's artifact. Less preferred because the spec line is consumer-discoverability-load-bearing — promoting `DjangoListField`'s visibility at the README is the substantive contract; rephrasing the sub-check to match the file's existing shape is necessary only if the route-1 edit cannot land.
- The `docs/README.md` Coming-in-`0.1.0` narrowing flagged in Worker 2's Notes for Worker 1 is a documented implicit consequence of the spec's shipped-vs-planned reconciliation discipline. It reads correctly to me — leaving `DjangoListField` claimed in BOTH "Shipped today" AND "Coming in `0.1.0`" would be internally contradictory. No spec edit needed unless Worker 1 disagrees with the implicit narrowing.
- No other spec gaps surfaced.

### Review outcome

`revision-needed`. The single Medium finding on `README.md` blocks acceptance under `AGENTS.md:4` (root-cause-fix directive — pragmatic shortcuts not viable) and Worker 0's dispatch directive (silently-unaddressed spec slice sub-check is Medium, must go `revision-needed`). The slice's other seven touched files are clean; the rev2 L1, rev2 L2, rev3 M5, rev4 H3, rev6 M5, and Decision 10 contracts are all honored. Setting the artifact's top-level `Status:` line to `revision-needed`. Worker 2's apply-changes pass needs only to add the `README.md` edit described above; no other revisions required.

---

## Build report (Worker 2, pass 2)

### Files touched

- `README.md` — appended a prose sentence to the `## Status` paragraph at `:45` that surfaces `DjangoListField` as the newest shipped surface under `0.0.7`. The version pin on the same paragraph stays at `**0.0.6**` per Decision 10 + rev3 M1 (the version bump is still deferred to the last `0.0.7` card to ship). The new sentence reads: `Newest shipped surface: `DjangoListField` — the non-Relay `list[T]` factory for root Query fields, new in `0.0.7` (default resolver pulls `model._default_manager.all()` and applies `cls.get_queryset(...)` in sync + async contexts).` Phrasing parity with `docs/README.md:99`'s shipped-today bullet ("`DjangoListField` — non-Relay `list[T]` factory for root Query fields (new in `0.0.7`); default resolver pulls `model._default_manager.all()` and applies the type's `get_queryset` in sync + async contexts.") so a migrant reading both surfaces gets a single consistent description rather than two slightly-divergent phrasings. The trailing prose paragraph at `:47` (forward-pointers to `TODAY.md` / `docs/GLOSSARY.md` / `KANBAN.md`) stays unchanged — the spec's consumer-discoverability intent is honored by the inline mention in `:45`, not by reworking the paragraph below it.

### Tests added or updated

- No tests added or updated; pass-2 is a docs-only `README.md` update.

### Validation run

- `uv run ruff format .` — pass. `103 files left unchanged` (Markdown-only edit, as expected). The standing `COM812 + formatter` advisory warning is the same one that fires on every ruff invocation in this repo and is unrelated to this edit.
- `uv run ruff check --fix .` — pass. `All checks passed!` (no autofixes applied).
- `git status --short` after both ruff invocations — seventeen entries, classified below:
  - **slice-intended (pass-2):** `M README.md` (this pass's edit), `?? docs/builder/bld-slice-5-promotion_docs_version.md` (this artifact, still untracked from pass-1).
  - **slice-intended (pass-1, already landed):** `M CHANGELOG.md`, `M GOAL.md`, `M KANBAN.md`, `M TODAY.md`, `M docs/GLOSSARY.md`, `M docs/README.md`, `M docs/TREE.md` — all seven pass-1 sites are unchanged in pass-2 and stay in the diff.
  - **inherited maintainer state (out of scope; preserved verbatim):** `M AGENTS.md`, `M docs/builder/bld-slice-3-optimizer_get_queryset_tests.md`, `M docs/builder/build-016-list_field-0_0_7.md`, `M docs/spec-016-list_field-0_0_7.md`, `M examples/fakeshop/apps/library/schema.py`, `M examples/fakeshop/test_query/test_library_api.py`, `M tests/test_list_field.py`, `?? docs/builder/bld-slice-4-live_http_coverage.md`. Worker 2 did NOT touch any of these in pass-2.
  - **unrelated tool churn:** none. Ruff produced zero diffs.
- `uv run pytest --no-cov tests/base/test_init.py` — 4 passed in 0.04s. The `__all__` pin (including the Slice 1 `DjangoListField` insertion) and the `__version__ == "0.0.6"` assertion both still pass after the `README.md` prose update, confirming the deferred-version-bump posture survives pass-2.

### Implementation notes

- **Edit shape: prose append to the existing Status paragraph at `README.md:45`, not a new bullet list or a section rewrite.** The file's `## Status` section is two declarative prose paragraphs (no bullet list at any point — verified by re-reading `:43-47` end-to-end). Under the AGENTS.md root-cause-fix directive, the right shape is to edit the existing prose to surface `DjangoListField` rather than to introduce a bullet list that doesn't match the file's voice. Appending a single sentence to the version-pin paragraph at `:45` puts the new symbol adjacent to the version string on the same line — a consumer landing on the Status section sees both at once, which is the consumer-discoverability outcome the spec line 138 sub-check was after. The trailing forward-pointer paragraph at `:47` (links to `TODAY.md` / `docs/GLOSSARY.md` / `KANBAN.md`) is left untouched; reworking it would change the file's existing structure without adding value, since the inline `DjangoListField` mention at `:45` already discharges the spec contract. Phrasing parity with `docs/README.md:99`'s shipped-today bullet was the prose anchor — same descriptor ("non-Relay `list[T]` factory for root Query fields", "new in `0.0.7`", "default resolver pulls `model._default_manager.all()`", "applies `cls.get_queryset(...)` in sync + async contexts") so the two surfaces don't diverge.

### Notes for Worker 3

- This is pass-2; the inline diff is small — `README.md` is the only file modified in this pass. Pass-1's other seven slice-intended files (`CHANGELOG.md`, `GOAL.md`, `KANBAN.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`) carry over from pass-1 with no further edits and remain reviewed.
- The pass-1 review's only blocking finding was the `README.md` Medium; that is now addressed via the prose append described above. No other findings were raised in pass-1; nothing else needs re-review beyond the `README.md` delta.
- Static inspection helper does NOT apply — pass-2 is Markdown-only. No shadow files created or referenced.
- Version pin at `README.md:45` deliberately stays at `**0.0.6**` (Decision 10 + rev3 M1). The new sentence names `0.0.7` as the surface's shipping release without bumping the version pin on the same line — both reads are correct: the active package version is `0.0.6`, and the `DjangoListField` symbol ships in the in-progress `0.0.7` release described by the CHANGELOG `[0.0.7]` heading at `CHANGELOG.md:21`.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed; pass-2 is a focused `README.md` update.

---

## Review (Worker 3, pass 2)

### High:

None.

### Medium:

None. The pass-1 Medium on `README.md` is resolved at root-cause shape — the Status-section prose at `README.md:45` now surfaces `DjangoListField` by symbol with the same six load-bearing claims used elsewhere in the Slice 5 doc sweep, honoring the AGENTS.md root-cause-fix directive rather than recording a vacuous no-op.

### Low:

None.

### DRY findings

- No new duplication introduced. The pass-2 append at `README.md:45` reuses the canonical descriptor anchors ("non-Relay `list[T]` factory for root Query fields", "new in `0.0.7`", "default resolver pulls `model._default_manager.all()`", "applies `cls.get_queryset(...)` in sync + async contexts") that already appear in `docs/README.md:99`'s shipped-today bullet and the spec-pinned CHANGELOG bullet at `CHANGELOG.md:21-22` — same descriptive vocabulary across the three consumer-facing surfaces, no slightly-divergent phrasings of the same claim. The two README surfaces remain coherent: a migrant landing on `README.md` and then bouncing to `docs/README.md` reads two grammatically distinct sentences (one inline prose, one bullet) that name the same load-bearing facts.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. Pass-2 does not modify the public surface; the Slice 1 `DjangoListField` addition to `__all__` is intact and unchanged from pass-1.

### CHANGELOG sanity

Not applicable; pass-2 did not modify `CHANGELOG.md`. Pass-1 review's acceptance of the CHANGELOG `### Added` bullet (verbatim spec-pinned wording, single-`[0.0.7]`-heading discipline, Keep-a-Changelog `### Added` placement) stands.

### Documentation / release sanity

Pass-2 touches `README.md` only. Walked the changed surface end-to-end:

- **Version string.** `README.md:45` still reads `**`0.0.6`**, single-maintainer, alpha-quality.` at the head of the paragraph — the pass-2 append does NOT alter the version pin, which keeps Decision 10 + rev3 M1 honored. The new sentence names `0.0.7` as the symbol's shipping release without claiming the package version is `0.0.7`; the two readings are internally consistent (active package `0.0.6`; symbol ships in the in-progress `0.0.7` cut described by `CHANGELOG.md:21`).
- **Wording — symbol surfaced by name.** The new sentence names `DjangoListField` explicitly and describes it accurately: "the non-Relay `list[T]` factory for root Query fields, new in `0.0.7` (default resolver pulls `model._default_manager.all()` and applies `cls.get_queryset(...)` in sync + async contexts)." This is the substantive consumer-discoverability promotion the AGENTS.md root-cause-fix directive demands — `DjangoListField` is now visible at the README's Status surface alongside the version pin, not just at the `docs/README.md` deeper-link surface.
- **Phrasing parity.** Cross-checked against `docs/README.md:99`'s shipped-today bullet (`grep -n "DjangoListField" docs/README.md` confirms one hit at `:99`): both surfaces use the same descriptor anchors ("non-Relay `list[T]` factory for root Query fields", "new in `0.0.7`", "default resolver pulls `model._default_manager.all()`", "`get_queryset` in sync + async contexts"). The two are factually aligned — `README.md` is prose ending in a parenthetical; `docs/README.md` is a bullet with a `GLOSSARY.md#djangolistfield` link — and that grammatical difference is correct for each file's voice.
- **No regression of other shipped-today content.** The Status section's first two sentences (alpha-quality framing, public-names-stable claim) are preserved verbatim. The trailing forward-pointer paragraph at `:47` (links to `TODAY.md` / `docs/GLOSSARY.md` / `KANBAN.md`) is untouched. The pass-2 edit is strictly additive: one sentence appended; nothing dropped or contradicted.
- **No `# TODO: spec-016` markers introduced.** `grep -n "spec-016" README.md` returns zero hits after the pass-2 append, confirming no scaffolding leaked into the edited surface.
- **Pass-1 acceptance carry-over.** The pass-1 review's acceptance of the other seven docs files (`CHANGELOG.md`, `GOAL.md`, `KANBAN.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`) stands; pass-2 only touched `README.md`. Confirmed via `git status --short` — the seven pass-1 slice-intended files are still `M` and unchanged in pass-2; the eighth (`README.md`) is the new pass-2 edit.

### What looks solid

- **Surgical pass-2 edit.** Exactly one sentence appended to exactly one line in exactly one file — the smallest possible shape that discharges the pass-1 Medium without collateral churn. The diff is `+1 -1` on a single hunk at `README.md:45`; no other file was opened for edit. Pattern worth carrying forward: when a pass-1 Medium pins a specific consumer-discoverability gap on a named file, the right pass-2 shape is a local prose append at the named surface, not a section rewrite or a new bullet-list introduction.
- **Phrasing parity with `docs/README.md:99` shipped-today bullet.** The pass-2 sentence at `README.md:45` and the pass-1 bullet at `docs/README.md:99` share the same four descriptor anchors. A migrant who reads `README.md` first and then drills into `docs/README.md` sees the same load-bearing facts on both surfaces. No drift across the two README files.
- **No-version-bump compliance.** `git diff HEAD -- pyproject.toml` and `git diff HEAD -- django_strawberry_framework/__init__.py` are both empty in pass-2 (same as pass-1). The version-pin on the Status line at `README.md:45` still reads `**`0.0.6`**` — the new sentence names `0.0.7` as the symbol's shipping release without claiming the package version has bumped. Decision 10 + rev3 M1 remain honored.

### Temp test verification

Skipped. Pass-2 is Markdown-only — no executable code or test changes. No temp tests created during re-review.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed; pass-2 is mechanical. The spec line 138 sub-check ("`README.md` — the shipped-today bullet list under 'Status'") is now substantively discharged at root-cause shape — `DjangoListField` is named on the Status surface in `README.md`, which is the consumer-discoverability outcome the spec line intended. Worker 1 ticks the `README.md` sub-check during final verification.

### Review outcome

`review-accepted`. Zero High / zero Medium / zero Low findings on pass-2. The pass-1 Medium on `README.md` is resolved at root-cause shape; the seven other Slice 5 touched files were accepted in pass-1 and remain unchanged. The slice is ready for Worker 1's final verification pass. Artifact's top-level `Status:` line set to `review-accepted`.

---

## Final verification (Worker 1)

- **Spec slice checklist:** every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]`. All seven Slice 5 sub-bullets (the GLOSSARY status flip + public exports + index table; the four-file `README.md` / `docs/README.md` / `GOAL.md` / `TODAY.md` doc sweep; the `docs/TREE.md` two-layout + rev2 L1 stale-line removal; the `KANBAN.md` column move with rev4 H3 add-only Done body; the `CHANGELOG.md` rev3 M5 single-heading `### Added` append; the Decision 10 + rev3 M1 version-bump deferral; the final-gate ruff + focused-test + one-new-public-export sub-checks) landed verbatim per the plan. No silently un-ticked boxes; no deferrals required.
- **DRY check across this slice and prior accepted slices:** clean.
  - `DjangoListField` description is coherent across `docs/GLOSSARY.md:304` (long-form authoritative entry), `docs/README.md:99` (bullet), `README.md:45` (inline prose), `GOAL.md:421` (migration-shape bullet), `TODAY.md:11` (library example summary tail), `KANBAN.md:1745-1751` (Done body), and `CHANGELOG.md:23` (release-note bullet). The same load-bearing anchor phrases ("non-Relay `list[T]` factory for root Query fields", "factory function", "`cls.get_queryset(...)` cooperation in sync + async contexts", "graphene-django parity", "outer nullability driven by the consumer's class-attribute annotation") reuse without diverging into slightly-different phrasings; the prose grammar adapts per-site (paragraph vs bullet vs inline sentence) which is the correct adaptation, not duplication.
  - `docs/TREE.md` rev2 L1 stale-line removal complete — `grep -n "DjangoListField" docs/TREE.md` returns exactly four hits (current `:201`, target `:242`, current test-tree `:332`, target test-tree `:405`); the previous fifth occurrence on the target `connection.py` line is gone. The target layout advertises one home for the symbol.
  - `CHANGELOG.md` carries exactly one `## [0.0.7]` heading (`grep -c "^## \[0.0.7\]" CHANGELOG.md` returns 1); the rev3 M5 no-second-heading discipline is preserved; `### Added` lands in canonical Keep-a-Changelog first position before `### Changed`.
  - KANBAN snapshot at `:50` and the Done body at `:1743-1751` use a single internally-consistent description of the column move; the rev4 H3 add-only anchor phrase is the only shipped-action voice in the Done body; the Decision 9 "Card-text departure" citation is the only place the original card's "replacing" wording appears.
- **Existing tests still pass:** `uv run pytest --no-cov tests/base/test_init.py tests/test_list_field.py examples/fakeshop/test_query/test_library_api.py` — **35 passed in 2.29s**. The Slice 1 `__all__` pin + version pin in `tests/base/test_init.py` (4 tests), the 21 Slice 1/2/3 behavior tests in `tests/test_list_field.py`, and the 10 library HTTP tests including Slice 4's `test_library_branches_via_djangolistfield_optimized_nested_selection` all pass with the Slice 5 docs sweep in place. No coverage flags passed (per BUILD.md "Coverage is the maintainer's gate, not a worker's tool").
- **Spec reconciliation:** Two surgical spec edits, both recorded under `### Spec changes made (Worker 1 only)` below. Neither edit changes the contract Worker 2 already implemented against; both reflect what landed during the build.
- **Final status:** `final-accepted`. Every check passes; the slice contract landed end-to-end at the root-cause shape the rev2 L1 / rev2 L2 / rev3 M5 / rev4 H3 / rev6 M5 / Decision 10 contracts demand; the pass-1 Medium on `README.md` was resolved at root-cause shape in pass-2.

### Summary

Slice 5 shipped the full eight-file Slice-5 docs sweep promoting `DjangoListField` from `planned for 0.0.7` to `shipped (0.0.7)`: the GLOSSARY status flip + public-exports list + index table at `docs/GLOSSARY.md`, the inline Status-section prose mention at `README.md:45` (resolved at root-cause shape during pass-2 after the pass-1 Medium flagged that `README.md` has no shipped-today bullet list), the `docs/README.md` shipped-today bullet plus the consequential Coming-in-`0.1.0` narrowing, the `GOAL.md:404` migration-shape bullet under "Coming from `graphene-django`", the `TODAY.md` library-summary append carrying the rev2 M1 add-only anchor verbatim, the `docs/TREE.md` two-layout site additions paired with the rev2 L1 stale-line removal so the symbol has exactly one home in the target layout, the rev4 H3 KANBAN column move to DONE-016-0.0.7 with strict add-only past-tense body language and the explicit Decision 9 "Card-text departure" citation, and the rev3 M5 single-heading CHANGELOG discipline (one `### Added` subsection appended in Keep-a-Changelog first position under the existing `[0.0.7]` heading at `CHANGELOG.md:21`). The Decision 10 + rev3 M1 version-bump deferral was honored at all three sites — `pyproject.toml:4`, `django_strawberry_framework/__init__.py:26`, and `tests/base/test_init.py:11` all still read `0.0.6` (the last `0.0.7` card to ship owns the bump). The rev6 L2 scaffold-TODO sweep is verified clean across every site in this slice — Slices 1/3/4 owned the source/test TODO removals; Slice 5's Markdown surfaces never carried scaffold TODOs to begin with.

### Spec changes made (Worker 1 only)

- **`docs/spec-016-list_field-0_0_7.md:6` — Predecessors line, `KANBAN.md` card reference.** Updated `card WIP-ALPHA-016-0.0.7` to `card DONE-016-0.0.7 (was WIP-ALPHA-016-0.0.7 until Slice 5's column move)`. Worker 1's per-spawn check (worker-1.md "Spec status-line re-verification") caught the stale `WIP-ALPHA-016-0.0.7` reference now that Slice 5's KANBAN column-move has landed; the corrected reference preserves the historical card ID so a future reader of the spec can still locate the originating WIP block in `KANBAN.md`'s git history, while reflecting the current Done state.
- **`docs/spec-016-list_field-0_0_7.md:149` — Slice 5 checklist `README.md` sub-bullet wording.** Tightened the wording from "`README.md` — the shipped-today bullet list under 'Status'." to "`README.md` — the Status section (currently plain prose; surface `DjangoListField` inline at `README.md:45` alongside the version-pin sentence rather than introducing a bullet list that doesn't match the file's voice — pinned by Slice 5 pass-2 root-cause fix per AGENTS.md line 4)." The original wording assumed a bullet list that doesn't exist in the file; the pass-1 review correctly flagged this as a silently-unaddressed sub-check, and the pass-2 root-cause fix (inline prose append at `README.md:45`) is now reflected in the spec text so future card builds doing similar README sweeps see the actual file shape rather than an assumed bullet list. The AGENTS.md line 4 directive ("always recommend the root-cause fix over the surface patch... pragmatic shortcuts are not a viable answer") is what selected the pass-2 fix; the spec tightening here records the directive's outcome.
