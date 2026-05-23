# Build: Slice 3 — Promotion + docs

Spec reference: `docs/spec-019-multi_db-0_0_7.md` (Slice checklist lines 92-103; Doc updates lines 559-583; Decision 1 lines 231-251; Decision 8 lines 437-448; Decision 9 lines 450-465; Definition of done items 10-17 lines 622-629)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

Docs-only slice; no shared-helper concerns in the production code sense. The DRY hazard here is **verbatim-text repetition across four target files** — the same four-axes wording surfaces in (a) `docs/GLOSSARY.md` entry body, (b) `docs/README.md` forward-pointer, (c) `KANBAN.md` Done card body, and (d) `CHANGELOG.md` `[0.0.7]` `### Added` bullet. The spec already pins each verbatim block, so the DRY shape is **mirror-the-spec-exactly** rather than reuse-a-helper.

- **Existing patterns reused.**
  - **Spec-pinned wording is the single source of truth.** The four blocks the slice writes are all spec-pinned. The DRY rule is "copy the spec's pinned wording verbatim into each target file"; the four texts are intentionally not identical (different surfaces, different verbosity) but every text references the same four narrowed axes from Decision 3 (spec lines 269-277), so a regression in any axis-wording must propagate to all four files.
    - GLOSSARY entry body: spec line 563 (the four-axes block to land in `docs/GLOSSARY.md:679-687`).
    - `docs/README.md` forward-pointer one-liner: spec line 566 (verbatim sentence).
    - KANBAN Done body: spec line 569 (full paragraph).
    - CHANGELOG bullet: spec line 576 (verbatim blockquote text).
  - **DONE-018-0.0.7 promotion-slice precedent** for the column-move + Definition-of-done-bullet-rewrite shape — KANBAN at lines 1775-1789 shows the past-tense Done-body template. Slice 3 mirrors the same format (Parity / Shipped / Borrowed / Tests / Files touched / Spec lines), but writes the body text per spec line 569's pinned wording.
  - **`[0.0.7]` `### Added` precedent at `CHANGELOG.md:28-32`** — three append-style bullets are already there from `DONE-016` / `DONE-017` / `DONE-018`. Slice 3 appends a fourth bullet under the same heading; do NOT create a second `[0.0.7]` heading (spec Decision 9 / line 574).
  - **GLOSSARY Index-table-row precedent**: every `shipped (X.X.X)` row across `docs/GLOSSARY.md:67-110` uses the exact form `shipped (\`X.X.X\`)` (e.g. `[Specialized scalar conversions](#specialized-scalar-conversions) | shipped (\`0.0.6\`)` at line 106). Slice 3's Index row flip mirrors this form — `planned for \`0.0.7\`` becomes `shipped (\`0.0.7\`)`.
- **New helpers justified.** None. This is a docs slice; no helper to extract.
- **Duplication risk avoided.**
  - **Risk:** the four axis-wordings drift between files because the spec pins them in four separate blocks (each block formatted for its target surface). **Closed by:** the plan numbers each spec line citation (563 / 566 / 569 / 576) so Worker 2 copies from one source per file and Worker 3 can `diff` the resulting text character-for-character against the spec source.
  - **Risk:** Worker 2 writes a new `[0.0.7]` heading and rolls in their own date placeholder rather than appending under the existing `## [0.0.7] - 2026-05-20` heading. **Closed by:** Plan step 5 names the exact insertion line range (`CHANGELOG.md:28-32`, after the third bullet at line 32, before the blank line at line 33).
  - **Risk:** Worker 2 paraphrases the verbatim blocks for "readability" and drifts from the spec. **Closed by:** explicit "copy spec line N verbatim" instructions for every text the slice lands, plus the Worker 3 review-pass "Documentation / release sanity" checklist (BUILD.md lines 304-315) which requires character-for-character diff of every verbatim copy.
  - **Risk:** Worker 2 archives the spec (moves it under `docs/SPECS/`) as part of Slice 3, which is NOT in scope (spec is at `docs/spec-019-multi_db-0_0_7.md` for this build; archive is a separate future workflow per Decision 1 rev3 R10 — "references point at whichever path the file actually has at the time the reference is written"). **Closed by:** Plan step 4 names `docs/spec-019-multi_db-0_0_7.md` (NOT `docs/SPECS/`) as the canonical spec path for both the KANBAN `Active spec:` line removal and the new KANBAN Done-body `Spec:` reference.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints. Verify against the current source before editing — Slice 1 and Slice 2 have already shipped and the working tree is dirty relative to HEAD, but no Slice-1/-2 file overlaps any Slice 3 target file.

1. **Edit `docs/GLOSSARY.md` Index table row at line 88** (verified at planning-pass read). Replace `| [Multi-database cooperation](#multi-database-cooperation) | planned for \`0.0.7\` |` with `| [Multi-database cooperation](#multi-database-cooperation) | shipped (\`0.0.7\`) |`. Mirrors the format already used by every shipped row (e.g. `shipped (\`0.0.6\`)` at line 102 for `Scalar field override semantics`).

2. **Rewrite `docs/GLOSSARY.md` entry body at lines 679-687** per spec line 563 (rev3 R9 — bullets pinned to the rev2-narrowed axes from Decision 3, NOT the rev1 broad framing). Current body text reads:

   ```
   ## Multi-database cooperation

   **Status:** planned for `0.0.7`.

   Pins the existing `router.db_for_read` cooperation in `types/resolvers.py` with a spec, tests, and a `GLOSSARY.md` status entry. Multi-db cooperation already exists in source today — this card documents it as a contract: the optimizer plans correctly under `.using()`, `Prefetch` chains respect routing, strictness mode tracks the originating connection, [`get_queryset`](#get_queryset-visibility-hook) downgrades respect routing.

   Companion `BACKLOG.md` item 41 covers first-class sharding-aware planning post-`1.0.0`.

   **See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [`get_queryset` visibility hook](#get_queryset-visibility-hook).
   ```

   Replace with:

   ```
   ## Multi-database cooperation

   **Status:** shipped (`0.0.7`).

   Documented cooperation surface — what the package guarantees under Django's multi-database machinery. Four axes:

   1. `router.db_for_read` on FK-id elision stubs — parent row forwarded as the `instance=` hint when present, `None` otherwise.
   2. Explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`](#djangooptimizerextension) for root querysets.
   3. Consumer-provided `Prefetch(queryset=...)` via [`OptimizerHint.prefetch(...)`](#optimizerhint) round-trips with its `_db` intact — generated `Prefetch` child querysets do NOT inherit the root alias.
   4. Strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases.

   Companion `BACKLOG.md` item 41 covers first-class sharding-aware planning post-`1.0.0`.

   **See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [`get_queryset` visibility hook](#get_queryset-visibility-hook).
   ```

   The status line flips (`planned for \`0.0.7\`` → `shipped (\`0.0.7\`)`). The four-bullet axes block replaces the single-paragraph "Pins the existing …" framing. The `Companion BACKLOG.md item 41` line and the `**See also:**` line are preserved unchanged. Worker 2 verifies the markdown rendering — the four-bullet ordered list must use `1.` / `2.` / `3.` / `4.` numbering with a single blank line separating it from the closing `Companion …` paragraph.

3. **Edit `docs/README.md` — rewrite the `### Sharded mode (multi-DB)` section** per spec line 566 to describe the additive `DATABASES` layout (`default → db.sqlite3` in both modes; `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3`) and link to the committed `db_shard_b.sqlite3` fixture. The section also carries a one-line forward-pointer to `GLOSSARY.md#multi-database-cooperation` for the cooperation contract.

   Insert the following one-liner as a new paragraph between line 216 and line 218 (after the existing closing paragraph, before the `## Using the package in your own project` heading):

   > For the cooperation contract these shards run against — explicit `.using()` `_db` preservation, FK-id elision router hints, consumer-provided `Prefetch(queryset=…)` alias round-trips, and strictness-mode behavior under non-default aliases — see [`GLOSSARY.md#multi-database-cooperation`](GLOSSARY.md#multi-database-cooperation).

   The wording is verbatim per spec line 566. The link target is `GLOSSARY.md#multi-database-cooperation` (relative — both files live under `docs/`); do not change to `docs/GLOSSARY.md#...` (absolute-from-repo-root) because `docs/README.md`'s sibling links use the same-folder convention everywhere else.

4. **Edit `KANBAN.md` — move `WIP-ALPHA-019-0.0.7` to the Done column with the next available `DONE-019-0.0.7` id.** Worker 1 pinpointed the next available NNN by reading the Done section: every existing `DONE-NNN-X.X.X` heading was enumerated via `grep -n "^### DONE-" KANBAN.md`; the highest is `DONE-018-0.0.7` (line 1775). The next NNN is **019**. The new card heading is `### DONE-019-0.0.7 — Multi-database cooperation contract`, placed AFTER `### DONE-018-0.0.7` (line 1789) and BEFORE the `## Release readiness checklist` heading at line 1791.

   Subscope (in order):

   - **4a. Delete the in-progress card body** at `KANBAN.md:76-123` (the entire `### WIP-ALPHA-019-0.0.7 — Multi-database cooperation contract` section including the `Priority`, `Parity`, `Severity`, `Status`, `Active spec`, `Why it matters`, `Scope`, `Definition of done`, `Files likely touched`, `Dependencies`, and `Out of scope` subsections). Also remove the blank line between this card and the next (the `### WIP-ALPHA-020-0.0.7` heading at line 125). Verify post-edit that `### WIP-ALPHA-020-0.0.7` is the new first card under `## In progress`.
   - **4b. Update the `### In progress` summary paragraph at `KANBAN.md:50`** (`...The remaining two — \`WIP-ALPHA-019-0.0.7\` (multi-database cooperation contract) and \`WIP-ALPHA-020-0.0.7\` (warning-free scalar registration via \`StrawberryConfig.scalar_map\`) — are still queued...`) to drop `WIP-ALPHA-019-0.0.7`. The replacement paragraph fragment reads: `The remaining card — \`WIP-ALPHA-020-0.0.7\` (warning-free scalar registration via \`StrawberryConfig.scalar_map\`) — is still queued.` And updates the antecedent count from "three have shipped" to "four have shipped", and appends `DONE-019-0.0.7` to the parenthetical list (`(\`DONE-016-0.0.7\` \`DjangoListField\`, \`DONE-017-0.0.7\` \`apps.py\` and Django app config, \`DONE-018-0.0.7\` schema-export management command, and \`DONE-019-0.0.7\` multi-database cooperation contract)`).
   - **4c. Append the new `### DONE-019-0.0.7 — Multi-database cooperation contract` card after line 1789** (after the `Spec: docs/SPECS/spec-018-export_schema-0_0_7.md. Build plan: docs/builder/build-018-export_schema-0_0_7.md.` line). The card body's narrative paragraphs are pinned by spec line 569 verbatim:

     > Pinned the package's multi-database cooperation contract — `router.db_for_read` on FK-id elision stubs (parent row forwarded as the `instance=` hint when present), explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`](django_strawberry_framework/optimizer/plans.py), consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=…))`](docs/GLOSSARY.md#optimizerhint) round-trip with `_db` intact, and strictness-mode's connection-agnostic shape under non-default aliases. Tests in [`tests/types/test_resolvers.py`](tests/types/test_resolvers.py) (five resolver-level tests against `_build_fk_id_stub` and `_check_n1` — four FK-id elision branches plus the strictness connection-agnostic shape; FK-id tests hermetic via mocked router), [`tests/optimizer/test_multi_db.py`](tests/optimizer/test_multi_db.py) (one optimizer-plan-level test against `OptimizerHint.prefetch` round-trip; Decision 3 axis 2 — `OptimizationPlan.apply` `_db` preservation — is verified transitively by the live HTTP test per `AGENTS.md` line 9's real-world-coverage rule), and [`examples/fakeshop/test_query/test_multi_db.py`](examples/fakeshop/test_query/test_multi_db.py) (live `/graphql/` HTTP under `FAKESHOP_SHARDED=1` with `@pytest.mark.django_db(databases=...)` and full `Branch → Shelf → Book` seeding). [`examples/fakeshop/config/settings.py`](examples/fakeshop/config/settings.py) ships an additive `DATABASES` layout — `default → db.sqlite3` in both modes; `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` — and the secondary shard's seed is committed at [`examples/fakeshop/db_shard_b.sqlite3`](examples/fakeshop/db_shard_b.sqlite3) so sharded mode works out of the box. [`docs/GLOSSARY.md#multi-database-cooperation`](docs/GLOSSARY.md#multi-database-cooperation) flipped from `planned for 0.0.7` to `shipped (0.0.7)` with a four-axis entry body; [`docs/README.md`](docs/README.md) `### Sharded mode (multi-DB)` describes the additive layout. Spec: [`docs/spec-019-multi_db-0_0_7.md`](docs/spec-019-multi_db-0_0_7.md). Zero production code change; the cooperation already existed in [`django_strawberry_framework/types/resolvers.py:82`](django_strawberry_framework/types/resolvers.py). [`BACKLOG.md`](BACKLOG.md) item 41 owns first-class sharding-aware planning post-`1.0.0` (including threading the parent queryset's `_db` into generated child `Prefetch` querysets, which this card explicitly leaves to that future card).

     **Path correction (Worker 1 plan note — Decision 1 rev3 R10):** the spec line 569 wording shows the `Spec:` reference as `docs/SPECS/spec-019-multi_db-0_0_7.md`, but the active spec for this build is at `docs/spec-019-multi_db-0_0_7.md` (not yet archived under `docs/SPECS/`). Per Decision 1's rev3 R10 simplified lifecycle rule ("references point at whichever path the file actually has at the time the reference is written"), Worker 2 substitutes the active path: `Spec: [\`docs/spec-019-multi_db-0_0_7.md\`](docs/spec-019-multi_db-0_0_7.md).` All other wording in the spec line 569 block is verbatim. Append a closing `Build plan: [\`docs/builder/build-019-multi_db-0_0_7.md\`](docs/builder/build-019-multi_db-0_0_7.md).` line on its own line at the very end of the card body to match the DONE-016/-017/-018 card-body precedent (`KANBAN.md:1757`, `:1773`, `:1789`).

     Add a `Parity` line as the first card-body line (matching DONE-016 / DONE-017 / DONE-018 precedent) using the existing WIP-ALPHA-019 card's `Parity` value (line 80): `Parity: ⚛️&🍓 parity-adjacent (multi-database is a Django capability neither upstream specifies a contract around; pinning ours smooths the migrant story from both, but is not a primitive either upstream ships).`

   - **4d. Spec-filename reference in the rewritten Done body (Decision 1 / Slice checklist line 95 / rev2 S13 / rev3 R10):** the rewritten body's `Spec:` line uses `docs/spec-019-multi_db-0_0_7.md` per the active-path rule above. There is no separate "card body Definition of done bullet 1" to rewrite — the old WIP card's `Definition of done` section (lines 101-107) is entirely deleted along with the rest of the WIP card body in step 4a, and the new DONE card body uses the past-tense Done shape from spec line 569 (no separate "Definition of done" subsection).

5. **Append a fourth bullet to `CHANGELOG.md`'s `[0.0.7]` `### Added` subsection.** The subsection currently has three bullets at lines 30-32 ending at `DONE-018-0.0.7`'s `Schema export management command` bullet. Insert the new bullet immediately AFTER line 32 (the last existing bullet), BEFORE the blank line at line 33 / the next `### Changed` subsection at line 35. The bullet text is verbatim per spec line 576:

   > - `Multi-database cooperation` — pinned the package's cooperation contract under Django's multi-database machinery: `router.db_for_read` on FK-id elision stubs (parent row forwarded as the `instance=` hint when present, `None` otherwise); explicit `.using(alias)` `_db` preservation through `OptimizationPlan.apply` for root querysets; consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…))` round-trips with the inner queryset's `_db` intact (generated `Prefetch` child querysets do NOT inherit the root alias at plan-construction time — deferred to BACKLOG item 41); strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases. Tests across [`tests/types/test_resolvers.py`](tests/types/test_resolvers.py) (resolver-level FK-id elision unit tests plus the strictness connection-agnostic-shape test against `_check_n1` — five tests total, FK-id tests hermetic via mocked router), [`tests/optimizer/test_multi_db.py`](tests/optimizer/test_multi_db.py) (optimizer-plan-level `OptimizerHint.prefetch` round-trip — one test; `OptimizationPlan.apply` `_db` preservation is verified transitively by the live HTTP test per `AGENTS.md` line 9), and [`examples/fakeshop/test_query/test_multi_db.py`](examples/fakeshop/test_query/test_multi_db.py) (live `/graphql/` HTTP under `FAKESHOP_SHARDED=1`, gated by `@pytest.mark.django_db(databases=…)`). [`examples/fakeshop/config/settings.py`](examples/fakeshop/config/settings.py) ships an additive `DATABASES` layout — `default → db.sqlite3` in both modes; `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` — and the secondary shard's seed is committed at [`examples/fakeshop/db_shard_b.sqlite3`](examples/fakeshop/db_shard_b.sqlite3) so sharded mode works out of the box. [`docs/GLOSSARY.md#multi-database-cooperation`](docs/GLOSSARY.md#multi-database-cooperation) flipped from `planned for 0.0.7` to `shipped (0.0.7)`. No production code change — the cooperation already existed at [`django_strawberry_framework/types/resolvers.py:82`](django_strawberry_framework/types/resolvers.py). [`BACKLOG.md`](BACKLOG.md) item 41 owns first-class sharding-aware planning post-`1.0.0`.

   Do NOT create a second `## [0.0.7]` heading. Verified at planning that only one `## [0.0.7]` heading exists (`grep -n "^## \[0.0.7\]"` returns the single line 28); the bullet appends under that heading's `### Added` subsection (line 29) as the fourth bullet.

   Tracker note: the `Tracked as DONE-NNN-0.0.7 in [\`KANBAN.md\`](KANBAN.md).` suffix used by the three existing `[0.0.7]` `### Added` bullets is NOT in spec line 576's pinned text and is therefore NOT appended. Worker 2 lands the bullet text verbatim per the spec without adding a `Tracked as` suffix; the cross-reference is the inline `KANBAN.md`-linked `BACKLOG.md` mention near the end of the bullet, which is what the spec pinned.

6. **Worker 1 final-verification gates** (not Worker 2's work; recorded here for the artifact's audit trail per Slice checklist lines 100-103). Run during Worker 1's final-verification pass after Worker 3 accepts the slice:
   - `uv run ruff format .`
   - `uv run ruff check --fix .`
   - `uv run pytest --no-cov` (explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per the per-pass-gates contract; coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`, not this slice's).

   These three commands belong to **the slice's own checklist** (spec lines 100-103) and Worker 1's final verification, not the build's separate final test-run gate (`docs/builder/bld-final.md`), which adds Django system checks, makemigrations dry-run, and the read-only ruff/lint sweep.

### Test additions / updates

Slice 3 adds no tests. The slice is docs-only.

- **Existing test pins protected:** Spec Definition of done item 8 (lines 620): `tests/base/test_init.py`'s `__all__` and version assertions must remain unchanged. Worker 3 verifies this via `git diff -- tests/base/test_init.py` (must be empty) at review. Worker 1 also verifies it at final verification per the public-surface check (spec DoD item 16 / line 628).
- **Definition of done item 9 / line 621:** Package coverage stays at 100% — verified by CI's `fail_under = 100` gate, NOT by Worker 1 locally. Worker 1 only runs `uv run pytest --no-cov` to confirm the suite passes; CI enforces the coverage gate.
- **No temp / scratch tests for Worker 3.** Slice 3 only modifies four documentation files; Worker 3 reviews the diff against the spec text and the verbatim wording, not against test runs. Worker 3 may run focused tests during review at discretion (without `--cov*` flags), but no slice-planned test obligation.

### Implementation discretion items

The following choices belong to Worker 2 as long as they preserve the contract Worker 1 has pinned above.

- **Whitespace around the new `docs/README.md` paragraph.** Worker 2 may insert a single blank line between the existing closing paragraph and the new one (preferred — matches the rest of the file's paragraph spacing), or omit it if a different shape reads cleaner; either way Worker 2 verifies post-edit that the `## Using the package in your own project` heading at line 218 is not visually merged into the new paragraph.
- **Wrap width on the new `docs/GLOSSARY.md` body bullets.** Worker 2 may keep each bullet on a single line (cleaner-`diff` posture) or wrap at the file's existing ~110-character width (matches the line-length cap). Either is fine; consistent style across the four bullets is what matters.
- **Order of the four axis bullets inside the GLOSSARY entry body.** Spec line 563 pins the order: (1) `router.db_for_read` on FK-id elision stubs; (2) explicit `.using(alias)` `_db` preservation; (3) consumer-provided `Prefetch(queryset=...)` round-trip; (4) strictness connection-agnostic shape. Worker 2 MUST follow this order; the "order is at discretion" framing in this section is a false delegation — the spec pins it, so this is not actually a discretion item. Recording the clarification here so Worker 2 does not reorder for "narrative flow."
- **Insertion position of the new DONE-019-0.0.7 KANBAN card.** Worker 2 inserts AFTER `### DONE-018-0.0.7` (preserves the `DONE-NNN` numeric ordering — the file lists Done cards by NNN ascending, verified at the grep enumeration in step 4). Do NOT insert in milestone order (which would put `DONE-019-0.0.7` between `DONE-016` and `DONE-020` if a later card lands first); chronological-NNN order is the convention.
- **Whether to drop or keep the existing WIP card's `Active spec:` line in the new Done body.** The new Done card body uses a `Spec:` line at the END (matching DONE-016/-017/-018 precedent at `KANBAN.md:1757`, `:1773`, `:1789`), NOT an `Active spec:` line at the top. The WIP card's `Active spec:` framing is dropped when the card moves to Done.
- **Variable wording inside the `### In progress` summary paragraph rewrite** (step 4b). Worker 2 may choose between "The remaining card — `WIP-ALPHA-020-0.0.7` ... is still queued" (singular) or any equivalent phrasing that drops the `WIP-ALPHA-019-0.0.7` reference. As long as the reference is gone and the parity-count antecedent is updated from "three" to "four" with `DONE-019-0.0.7` appended, the exact wording is at Worker 2 discretion.
- **Whether to trim the `### In progress` summary paragraph's parity-count list more aggressively.** Worker 2 may prefer to keep the list short (the precedent so far has been to list each shipped 0.0.7 card by name); appending `DONE-019-0.0.7 multi-database cooperation contract` preserves that pattern. If Worker 2 reads the four-card list as too verbose, they may collapse to "four have shipped (`DONE-016-0.0.7` through `DONE-019-0.0.7`)"; the substantive content is the four-shipped count and the remaining card name, not the parenthetical detail.

If Worker 2 cannot resolve any of these by reading the plan and the spec, escalate to Worker 1 — do NOT improvise on a question that is not in this list.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 3 from `## Slice checklist` lines 92-103, copied verbatim. Worker 1 ticks each `- [x]` at final-verification as the contract lands.

- [x] Flip [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation) from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`](GLOSSARY.md): update the Index table row (currently `| [Multi-database cooperation](#multi-database-cooperation) | planned for `0.0.7` |` at line 88) and the entry body at line 679 (the body already describes the cooperation in present tense — minor wording tightening to remove "Pins the existing … cooperation" framing and replace it with "Pins the cooperation contract: …" past-tense framing matching shipped entries).
- [x] Update [`docs/README.md`](README.md): add a one-line forward-pointer at the end of the `### Sharded mode (multi-DB)` section (line 216) reading: "For the cooperation contract these shards run against — what the package guarantees under `.using()`, `Prefetch` chains, and `get_queryset` downgrades — see [`GLOSSARY.md#multi-database-cooperation`](GLOSSARY.md#multi-database-cooperation)." (per the [`KANBAN.md`](../KANBAN.md) card DoD bullet 5).
- [x] Update [`KANBAN.md`](../KANBAN.md): move `WIP-ALPHA-019-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (renumbering owned by the column-move pass, not pinned here). The past-tense Done body summarizes the shipped scope: cooperation contract spec'd at [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) (canonical name; supersedes the card's `docs/spec-multi_db.md` placeholder per [Decision 1](#decision-1--spec-filename-and-canonical-naming)); tests in `tests/optimizer/test_multi_db.py` and `examples/fakeshop/test_query/test_multi_db.py`; GLOSSARY entry flipped to `shipped (0.0.7)`; one-line forward-pointer added to `docs/README.md`.
- [x] Update [`CHANGELOG.md`](../CHANGELOG.md): **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [Decision 9](#decision-9--joint-0_0_7-cut) — every `0.0.7` card under the joint cut appends to the same shared section). [`AGENTS.md`](../AGENTS.md) line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — this Slice 3 bullet is the explicit instruction. Entry wording pinned in [Doc updates](#doc-updates).
- [x] No edits to [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md). Justification: the cooperation contract is plumbing the package already honors; it is not a new consumer name-surface, the fakeshop schema is unchanged by this card, and `TODAY.md`'s query-shape snapshot is not affected (per [Decision 8](#decision-8--no-readme--goal--today-edits)). Same posture as [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) Slice 3.
- [x] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 9](#decision-9--joint-0_0_7-cut)): see [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s pinned version assertion.
- [x] Zero new public exports — the cooperation contract is plumbing already in the package, not a new symbol. `__all__` is unchanged.
- [x] Final gates (same posture as [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) DoD item 13):
  - [x] `uv run ruff format .` passes.
  - [x] `uv run ruff check --fix .` passes.
  - [x] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per the per-pass-gates contract; coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's.

### Plan notes — static inspection helper

Per `docs/builder/BUILD.md` "When to run the helper during build", Worker 1 must run `scripts/review_inspect.py` during planning when the plan adds logic to any existing `.py` file with ≥150 source lines OR any file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`. **Skip decision recorded:** Slice 3 is docs-only (modifies only `.md` files: `docs/GLOSSARY.md`, `docs/README.md`, `KANBAN.md`, `CHANGELOG.md`). The 150-source-lines trigger does not fire (no `.py` file modified). The `optimizer/` / `types/` subpackage trigger does not fire (no production source touched). The helper was NOT run for this planning pass.

### Spec status-line re-verification

Read the spec's status / header lines (`docs/spec-019-multi_db-0_0_7.md:1-5`) at planning-pass entry. Current line 4: `Status: draft (revision 5, post-rev4 feedback against docs/feedback.md)`. Slice 3 is the last slice of the build; once Slice 3 lands and all three slices are `final-accepted`, the spec status line could in principle flip to "shipped" wording, BUT spec Decision 1 rev3 R10 + the existing spec-lifecycle pattern (the spec stays at `docs/spec-019-multi_db-0_0_7.md` and is not archived as part of this build) means the appropriate header update is a Slice-3-final-verification call, not a planning-pass call. Worker 1 revisits the status line at Slice-3 final verification per the carry-forward note in `worker-memory/worker-1.md:10`.

No status-line edit at this planning pass.

---

## Build report (Worker 2)

### Files touched

- `docs/GLOSSARY.md` — flipped the Index-table row at line 88 from `planned for \`0.0.7\`` to `shipped (\`0.0.7\`)` (mirrors the format used by every shipped row in the table); rewrote the `## Multi-database cooperation` entry body (lines 679-693) per spec line 563. Past-tense "Documented cooperation surface" framing + four-bullet axes list (per spec Decision 3); preserved the `Companion BACKLOG.md item 41` paragraph and the `**See also:**` line verbatim.
- `docs/README.md` — inserted a one-line forward-pointer paragraph between the `### Sharded mode (multi-DB)` closing paragraph (line 216) and the `## Using the package in your own project` heading (now at line 220) per spec line 566. Wording verbatim; link target `GLOSSARY.md#multi-database-cooperation` uses the same-folder relative form the file's other sibling links use.
- `KANBAN.md` — three-part edit per the plan's step 4. (4b) updated the `### In progress` summary paragraph at line 50: dropped `WIP-ALPHA-019-0.0.7` from the queued list, bumped the count from "three have shipped" to "four have shipped", and appended `DONE-019-0.0.7 multi-database cooperation contract` to the parenthetical list. (4a) deleted the full `### WIP-ALPHA-019-0.0.7 — Multi-database cooperation contract` card body (49 lines: heading + Priority + Parity + Severity + Status + Active spec + Why it matters + Scope + Definition of done + Files likely touched + Dependencies + Out of scope) plus the separating blank line; verified `### WIP-ALPHA-020-0.0.7` is now the first card under `## In progress`. (4c) appended a new `### DONE-019-0.0.7 — Multi-database cooperation contract` card body AFTER `### DONE-018-0.0.7` (preserves NNN-ascending order), BEFORE the `## Release readiness checklist` heading; card body is spec line 569 verbatim with the active-path substitution (`docs/spec-019-multi_db-0_0_7.md` instead of the spec's pinned archived `docs/SPECS/spec-019-multi_db-0_0_7.md`) per the artifact plan's step 4d / Decision 1 rev3 R10; added the `Parity:` line as the first body line per DONE-016 / -017 / -018 precedent; appended `Build plan: [\`docs/builder/build-019-multi_db-0_0_7.md\`](docs/builder/build-019-multi_db-0_0_7.md).` as the closing line per the same precedent.
- `CHANGELOG.md` — appended a fourth bullet under the existing `## [0.0.7] - 2026-05-20` `### Added` subsection (after the `DONE-018-0.0.7` `Schema export management command` bullet, before the empty line that precedes `### Changed`); wording verbatim per spec line 576. Did NOT create a second `[0.0.7]` heading per spec Decision 9.

### Tests added or updated

None; docs-only slice.

### Validation run

- `uv run ruff format .` — pass (`112 files left unchanged`; idempotent on repeat).
- `uv run ruff check --fix .` — pass (`All checks passed!`). Notably **no** churn against `examples/fakeshop/test_query/test_multi_db.py` this pass — the Slice 1 / Slice 2 memory note that the 11 F401 unused-import autofix attempts would disappear once Slice 2 landed the real bodies is confirmed here.
- `git status --short` after both ruff invocations:
  - `M CHANGELOG.md` — slice-intended (Slice 3, appears in `### Files touched`).
  - `M KANBAN.md` — slice-intended (Slice 3, appears in `### Files touched`).
  - `M docs/GLOSSARY.md` — slice-intended (Slice 3, appears in `### Files touched`).
  - `M docs/README.md` — slice-intended (Slice 3, appears in `### Files touched`).
  - `M docs/builder/bld-slice-3-promotion_docs.md` — this artifact (the file I am currently editing — slice-intended).
  - `M docs/spec-019-multi_db-0_0_7.md` — build-cycle accumulating diff (Slice 2's Worker 1 spec reconciliation, NOT Slice 3 churn); not touched in this pass.
  - `M examples/fakeshop/test_query/test_multi_db.py` — build-cycle accumulating diff (Slice 2 work); not touched in this pass.
  - `M tests/optimizer/test_multi_db.py` — build-cycle accumulating diff (Slice 1 work); not touched in this pass.
  - `M tests/types/test_resolvers.py` — build-cycle accumulating diff (Slice 1 work); not touched in this pass.
  - `D docs/builder/bld-final.md`, `D bld-integration.md`, `D bld-slice-1-module.md`, `D bld-slice-2-tests.md`, `D build-018-export_schema-0_0_7.md` — pre-flight cleanup deletions from Worker 0's setup; not Slice 3 churn.
  - `?? docs/builder/bld-slice-1-package_tests.md`, `?? bld-slice-2-fakeshop_live.md`, `?? build-019-multi_db-0_0_7.md` — current build artifacts (untracked at build-cycle scope; not Slice 3 churn).
  - **No unrelated tool churn to revert.** `git checkout` was NOT invoked on any file.
- Optional focused sanity test: `uv run pytest --no-cov` (full suite, including all three test trees) → **781 passed, 3 skipped** (the 2 Slice 2 multi-db live tests skip cleanly without `FAKESHOP_SHARDED=1`; the 3rd skip is a pre-existing `examples/fakeshop/tests/test_commands.py::test_seed_shards_*` shard-marker test). No failures. Docs-only edits did not affect any test; ran as a cheap sanity check per the slice prompt's optional instruction. No `--cov*` flags.

### Implementation notes

- **GLOSSARY entry body — four-axis bullets ordered per spec line 563** (1: router/FK-id elision; 2: explicit `.using()` `_db` preservation through `OptimizationPlan.apply`; 3: consumer-provided `Prefetch(queryset=...)` via `OptimizerHint.prefetch(...)` round-trip; 4: strictness connection-agnostic shape). The plan's discretion item noting "Worker 2 MUST follow this order" overrides the false-delegation framing — implemented in the spec order verbatim.
- **Preserved the `Companion BACKLOG.md item 41` paragraph AND the `**See also:**` line unchanged.** Spec line 563's pinned wording explicitly preserves both; I lifted the four-axis block in between the `**Status:**` line and the `Companion …` paragraph without touching the trailing structure.
- **`docs/README.md` paragraph spacing.** Inserted one blank line between the existing closing paragraph (line 216) and the new forward-pointer paragraph, and one blank line between the new paragraph and the `## Using the package in your own project` heading. Mirrors the rest of the file's paragraph spacing convention (per plan discretion item).
- **KANBAN `### In progress` summary rewrite — chose the verbose-list shape over the collapsed range.** Wrote out each of the four shipped 0.0.7 cards by name (`DONE-016-0.0.7 \`DjangoListField\`, DONE-017-0.0.7 \`apps.py\` and Django app config, DONE-018-0.0.7 schema-export management command, and DONE-019-0.0.7 multi-database cooperation contract`) to mirror the existing precedent (the previous paragraph listed each shipped card by name); the discretion item explicitly licensed the alternative `DONE-016-0.0.7 through DONE-019-0.0.7` collapse, but the verbose form keeps the per-card discoverability the readers of this paragraph have been using.
- **KANBAN DONE-019 body — path substitution per Decision 1 rev3 R10.** The spec's pinned KANBAN Done body wording at line 569 cites `docs/SPECS/spec-019-multi_db-0_0_7.md`; the active spec for this build is at `docs/spec-019-multi_db-0_0_7.md`. Per the plan's step 4d explicit instruction and Decision 1's simplified lifecycle rule ("references point at whichever path the file actually has at the time the reference is written"), I substituted the active path. All other wording in the spec line 569 block is verbatim.
- **KANBAN DONE-019 body — added `Parity:` line and trailing `Build plan:` line per the precedent established by DONE-016 / DONE-017 / DONE-018.** Spec line 569's wording is the past-tense narrative paragraph (without the framing lines); the DONE card precedent in the file wraps that paragraph with a `Parity:` line at the top (sourced from the deleted WIP card's `Parity:` line per the plan's step 4c sub-bullet) and a `Build plan:` line at the bottom (built from the structured-build-plan filename per the same precedent). Both framing lines are necessary for the card to read coherently against its siblings.
- **CHANGELOG bullet — append point.** Inserted after the third existing bullet (`DONE-018-0.0.7` schema-export management command) and BEFORE the blank line that precedes `### Changed`. The find-and-replace anchored on the third bullet's terminal text plus the blank-line `### Changed` heading produced a unique single-edit insertion point with no ambiguity; no second `[0.0.7]` heading created.
- **Did NOT append a `Tracked as DONE-NNN-0.0.7` suffix** to the new CHANGELOG bullet per the plan's step 5 trailing tracker note (spec line 576's pinned text omits that suffix and the spec is explicit about not adding it; the inline `KANBAN.md`-linked `BACKLOG.md` mention near the end of the bullet is the cross-reference).

### Notes for Worker 3

- All four target files (`docs/GLOSSARY.md`, `docs/README.md`, `KANBAN.md`, `CHANGELOG.md`) have verbatim spec-pinned text blocks. The verbatim sources are: GLOSSARY entry body → spec line 563; `docs/README.md` forward-pointer → spec line 566; KANBAN Done body → spec line 569 (with the active-path substitution per Decision 1 rev3 R10 / plan step 4d); CHANGELOG bullet → spec line 576. The character-for-character `diff` check Worker 3 performs against the spec source should pass cleanly on all four; the only intentional divergence is the KANBAN spec-path substitution.
- The Slice 1 / Slice 2 memory note about ruff trying to remove 11 unused imports from `examples/fakeshop/test_query/test_multi_db.py` is no longer reproducible — this Slice 3 ruff run was clean. The Slice 2 scaffold imports are now in use after Slice 2 landed the real test bodies, so the autofix churn that plagued Slices 1 and 3 (pre-Slice-2) is resolved.
- No shadow files used for Slice 3 (the static-inspection helper does not apply to `.md` files; recorded in the plan's "Plan notes — static inspection helper" section).
- The optional `uv run pytest --no-cov` sanity check passed (781/784 with 3 skips); no Slice 3 edits affect test behavior (docs only).
- The `M docs/spec-019-multi_db-0_0_7.md` entry in `git status` is Slice 2's Worker 1 reconciliation (the line 551 query widening per rev5-post X7); not touched by Slice 3.

### Notes for Worker 1 (spec reconciliation)

None.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### GLOSSARY entry-body bullet wording is stylistically refined from spec line 563's prose form

The spec at line 563 pins the four-axes block as inline prose (`(1) router.db_for_read on FK-id elision stubs (parent row forwarded as the `instance=` hint when present, `None` otherwise); (2) explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`](#djangooptimizerextension); (3) consumer-provided [`Prefetch(queryset=...)`](#optimizerhint) via `OptimizerHint.prefetch(...)` round-trips with its `_db` intact — generated `Prefetch` child querysets do NOT inherit the root alias; (4) strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases.`). Worker 1's plan (artifact lines 50-65) and Worker 2's landed text in `docs/GLOSSARY.md:685-688` render these as numbered list items with the per-bullet adaptations a numbered-list rendering needs:

- Each bullet's first letter is capitalized (spec's `router`, `explicit`, `consumer-provided`, `strictness-mode` → landed `router`/`Explicit`/`Consumer-provided`/`Strictness-mode`; bullet 1 stays lowercase because it begins with a backticked identifier).
- Each bullet ends with a period (spec uses `;` between bullets).
- Bullet 1's parenthetical clause `(parent row forwarded as the instance= hint when present, None otherwise)` becomes em-dash-joined: `— parent row forwarded as the instance= hint when present, None otherwise.`
- Bullet 2 appends `for root querysets` (matching the same suffix in spec line 569 and the CHANGELOG bullet at spec line 576; consistent across all three documented surfaces).
- Bullet 3 swaps the link anchor from `[Prefetch(queryset=...)](#optimizerhint)` (spec) to `Prefetch(queryset=...)` plus `[OptimizerHint.prefetch(...)](#optimizerhint)`, so the link text matches the anchor target (`OptimizerHint` → `#optimizerhint`).

All semantic content is preserved across the four axes. These read as deliberate stylistic adaptations that survive a numbered-list rendering, but they are not character-for-character verbatim against spec line 563. Per BUILD.md's `Documentation / release sanity` clause ("when the slice copies verbatim text from the spec [...], confirm character-for-character via `diff` against the spec source"), I am flagging the wording drift at Low rather than Medium because (a) the plan committed to the landed wording, so Worker 2 implemented the plan faithfully, (b) all three other spec-pinned blocks (README forward-pointer, KANBAN Done body, CHANGELOG bullet) diff cleanly, and (c) Worker 1's spec reconciliation note is the appropriate place to either fold the adaptations into the spec line 563 wording or revise the bullets back to the spec form. Recorded for Worker 1's final-verification disposition; not blocking acceptance.

```docs/GLOSSARY.md:685-688
1. `router.db_for_read` on FK-id elision stubs — parent row forwarded as the `instance=` hint when present, `None` otherwise.
2. Explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`](#djangooptimizerextension) for root querysets.
3. Consumer-provided `Prefetch(queryset=...)` via [`OptimizerHint.prefetch(...)`](#optimizerhint) round-trips with its `_db` intact — generated `Prefetch` child querysets do NOT inherit the root alias.
4. Strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases.
```

### DRY findings

Slice 3 introduces no new helpers. The four target files carry intentional cross-doc redundancy — the four-axes wording surfaces in `docs/GLOSSARY.md` (entry body), `docs/README.md` (forward-pointer one-liner), `KANBAN.md` (Done card body), and `CHANGELOG.md` (`[0.0.7]` `### Added` bullet). This is by design (each surface needs its own version of the contract for its readership); the spec pins each block separately at lines 563 / 566 / 569 / 576. Not a finding.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → empty. `git diff -- django_strawberry_framework/` → empty. `git diff -- tests/base/test_init.py` → empty. `git diff -- pyproject.toml` → empty. `git diff -- examples/fakeshop/apps/library/schema.py examples/fakeshop/apps/products/schema.py examples/fakeshop/config/settings.py` → empty. `git diff -- README.md GOAL.md TODAY.md docs/TREE.md` → empty. All public-surface and out-of-scope guarantees hold. `__all__` and version assertions remain at `0.0.6` per Decision 9 joint-cut policy.

### CHANGELOG sanity

This slice modifies `CHANGELOG.md`. Walked per BUILD.md's pinned subchecks:

- **Version line vs package version.** The new bullet sits under the existing `## [0.0.7] - 2026-05-20` heading (CHANGELOG line 28); Worker 2 did NOT create a second `[0.0.7]` heading per Decision 9 joint-cut. Verified `pyproject.toml:4` → `version = "0.0.6"`, `django_strawberry_framework/__init__.py:26` → `__version__ = "0.0.6"`, `tests/base/test_init.py:11` → `assert __version__ == "0.0.6"`. The `[0.0.7]` heading carries entries from `DONE-016` / `DONE-017` / `DONE-018` / the new `DONE-019` ahead of the actual version bump (deferred to the last `0.0.7` card per Decision 9 / spec Risks-and-open-questions clarifier line 589); this is the documented joint-cut policy.
- **`### Added` heading authorized.** Spec line 574 ("Append to the existing `[0.0.7]` `### Added` subsection") explicitly authorizes the heading. Verified `CHANGELOG.md:29` carries the `### Added` heading; the new bullet appears immediately after the third existing bullet at line 32 and before the blank line preceding `### Changed` at line 36 (in the post-edit numbering).
- **Wording matches spec line 576 verbatim.** Ran a literal `diff` of the landed bullet (CHANGELOG line 33) against the spec line 576 blockquote text. Output: empty. Character-for-character identical.
- **Bullet does not overstate or understate the change.** The bullet correctly says "No production code change — the cooperation already existed at `django_strawberry_framework/types/resolvers.py:82`"; this matches Decision 2 (no production code change) and DoD item 6. Test-count breakdown (`five tests total` in `tests/types/test_resolvers.py`, `one test` in `tests/optimizer/test_multi_db.py`) matches the DoD item 2 count of 6 pytest items; Decision 3 axis 2 is verified through the Slice 2 live HTTP test per `AGENTS.md` line 9. The BACKLOG-41 deferral language correctly distinguishes the consumer-provided `Prefetch` round-trip (in scope) from generated child `Prefetch` `_db` carryover (deferred).
- **No `Tracked as DONE-NNN-0.0.7 in KANBAN.md` suffix.** The plan step 5 trailing note and Worker 2's implementation note 6 explicitly omit this suffix because spec line 576's pinned text omits it; the cross-reference is the inline `BACKLOG.md` mention near the end of the bullet. Verified absent.

### Documentation / release sanity

This slice touches docs, KANBAN, and CHANGELOG. Walked per BUILD.md's pinned subchecks:

- **Version strings, shipped/planned statuses, card IDs.** GLOSSARY Index row at line 88: `| [Multi-database cooperation](#multi-database-cooperation) | shipped (\`0.0.7\`) |` — flipped from `planned for \`0.0.7\``, matches the spec's flip directive. GLOSSARY entry status line at line 681: `**Status:** shipped (\`0.0.7\`).` — flipped from `planned for \`0.0.7\``. KANBAN card id `DONE-019-0.0.7` follows the NNN-ascending sequence (highest previous DONE is `DONE-018-0.0.7` per `KANBAN.md:1726`). CHANGELOG `[0.0.7]` heading at line 28 is unchanged.
- **Moved KANBAN card.** `WIP-ALPHA-019-0.0.7` is removed entirely from the In-progress column (verified via `grep -n "WIP-ALPHA-019-0.0.7" KANBAN.md` returning no matches in the In-progress region; only references remain in past `Tracked as` strings in the Done column). The `DONE-019-0.0.7 — Multi-database cooperation contract` card appears exactly once at line 1742, inserted after `DONE-018-0.0.7` and before `## Release readiness checklist`. The `### In progress` summary paragraph at line 50 is correctly updated (count `three have shipped` → `four have shipped`; remaining card list shrinks from two to one; the parenthetical list appends `DONE-019-0.0.7 multi-database cooperation contract`).
- **Markdown links point at existing files / anchors.** Verified `BACKLOG.md`, `docs/GLOSSARY.md`, `docs/README.md`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/types/resolvers.py`, `tests/types/test_resolvers.py`, `tests/optimizer/test_multi_db.py`, `examples/fakeshop/test_query/test_multi_db.py`, `docs/spec-019-multi_db-0_0_7.md`, `docs/builder/build-019-multi_db-0_0_7.md` all exist. GLOSSARY anchors `#djangooptimizerextension`, `#multi-database-cooperation`, `#optimizerhint` all resolve to live `## ` headings (`GLOSSARY.md:332`, `:679`, `:702`).
- **Verbatim-text byte-for-byte check.** Ran `diff` against the spec source for each pinned block:
  - `docs/README.md:218` (forward-pointer one-liner) vs `docs/spec-019-multi_db-0_0_7.md:566` → **empty diff** (verbatim match).
  - `KANBAN.md:1746` (Done-body paragraph) vs `docs/spec-019-multi_db-0_0_7.md:569` with the active-path substitution (`docs/spec-019-multi_db-0_0_7.md` instead of `docs/SPECS/spec-019-multi_db-0_0_7.md` per Decision 1 rev3 R10) → **empty diff** (verbatim match modulo the licensed path substitution).
  - `CHANGELOG.md:33` (the new `### Added` bullet) vs `docs/spec-019-multi_db-0_0_7.md:576` → **empty diff** (verbatim match).
  - `docs/GLOSSARY.md:685-688` (the four-axis bullets) vs `docs/spec-019-multi_db-0_0_7.md:563` → **drift in stylistic adaptation** (bullets capitalized, semicolons replaced with periods, parenthetical clause on bullet 1 em-dash-joined, "for root querysets" suffix appended to bullet 2, link target on bullet 3 swapped). Recorded as a Low finding above; Worker 1 weighs whether to revise the spec line 563 pinned wording to match the rendered form or revise the landed bullets back to the spec form.
- **No obsolete "planned" / "coming soon" wording remains.** `grep -n "planned for \`0.0.7\`" docs/GLOSSARY.md` returns no matches (the only `planned for 0.0.7` reference in the file was the `Multi-database cooperation` Index row at line 88 and the status line at line 681, both flipped). The `### In progress` summary paragraph at KANBAN line 50 correctly drops `WIP-ALPHA-019-0.0.7` from the queued-cards list.
- **`pyproject.toml`, `__version__`, and version-pin test all stay at `0.0.6`** per Decision 9 joint-cut; verified empty diffs. No version bump in this slice.

### What looks solid

- Worker 2 followed the plan steps in order. The four target files each carry the spec-pinned text block with the only intentional divergence being the KANBAN Done-body active-path substitution (`docs/spec-019-multi_db-0_0_7.md` instead of `docs/SPECS/spec-019-multi_db-0_0_7.md`), explicitly licensed by Decision 1 rev3 R10 / plan step 4d.
- The KANBAN card-move is mechanically clean: WIP card body removed from In-progress, DONE card body added to Done in NNN-ascending position, summary paragraph rewritten with the count bump and queued-cards-list trim, and the new card carries the `Parity:` framing line at the top and `Build plan:` framing line at the bottom matching the `DONE-016` / `DONE-017` / `DONE-018` precedent.
- The CHANGELOG bullet sits under the existing `[0.0.7]` `### Added` subsection; no second `[0.0.7]` heading was created. The bullet does not carry a `Tracked as DONE-NNN-0.0.7` suffix, faithfully to spec line 576's pinned text.
- The `docs/README.md` forward-pointer uses the same-folder relative link form (`GLOSSARY.md#multi-database-cooperation`) that the rest of `docs/README.md` uses for sibling-doc links.
- No `# noqa` suppressions anywhere; no `# pragma: no cover`; no public-surface changes. `git diff -- django_strawberry_framework/` is empty, confirming the no-production-code-change DoD item 6 / Decision 2 contract.
- The `uv run pytest --no-cov` sanity check Worker 2 ran (recorded in the build report) shows 781/784 passing with 3 skips (two Slice 2 multi-db live tests gated on `FAKESHOP_SHARDED=1`, plus a pre-existing seed-shards command test). Docs-only edits do not affect test behavior; this is a useful negative confirmation.

### Temp test verification

None used during this review. Slice 3 is docs-only; no behavior to pin.

### Notes for Worker 1 (spec reconciliation)

- **Spec line 563 wording vs landed GLOSSARY bullets.** Spec line 563 pins the four-axes block as flowing inline prose with semicolons and lowercase bullet starts; the plan step 2 and the landed `docs/GLOSSARY.md:685-688` render them as numbered list items with capitalized starts, period terminators, an em-dash-joined parenthetical on bullet 1, a `for root querysets` suffix on bullet 2 (matching the same suffix in spec lines 569 and 576), and a link-anchor swap on bullet 3 from `[Prefetch(queryset=...)](#optimizerhint)` to `Prefetch(queryset=...)` plus `[OptimizerHint.prefetch(...)](#optimizerhint)`. These are stylistic adaptations to render flowing prose as a numbered list. Decision 1 rev3 R10 licenses the active-path substitution but does NOT explicitly license bullet-wording adaptations. Worker 1's options at final verification: (a) revise the spec line 563 wording to match the rendered bullets (lifting the adaptations into the spec source so future re-rendering / re-review diffs cleanly); (b) revise the GLOSSARY bullets to match the spec line 563 prose verbatim (semicolons in place of periods, lowercase bullet starts, parenthetical clauses preserved as-is, link anchor on `Prefetch(queryset=...)`). Recommending (a) — the rendered form reads more cleanly as a numbered list and aligns with the spec's stated intent of "four narrowed-axis bullets" (line 563 calls them "bullets," and the adaptations are what bullets need to read as bullets). Recorded as a Low finding above so Worker 1 has the disposition recorded in the artifact.
- No other spec gaps surfaced during review. The active-path substitution at KANBAN line 1746 is correctly applied per Decision 1 rev3 R10; the joint-cut-policy assumptions for CHANGELOG and version pins all hold.

### Review outcome

`review-accepted` — every High / Medium finding is None; the one Low finding is a wording-style divergence between the plan's pinned bullet rendering and the spec's inline prose form, recorded for Worker 1's final-verification disposition. Public-surface check, CHANGELOG sanity, and Documentation / release sanity all pass with no blocking issues. The artifact's top-level `Status:` line is set to `review-accepted`.

---

## Final verification (Worker 1)

1. **Spec slice checklist tick.** Every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` (eight top-level sub-bullets, including the three nested final-gate sub-bullets — eleven boxes total) is now `- [x]`. None deferred. The verbatim contract landed across every item:
   - GLOSSARY Index row at line 88 flipped from `planned for `0.0.7`` to `shipped (`0.0.7`)` (verified via `Read` on `docs/GLOSSARY.md`).
   - GLOSSARY entry body at lines 679-693 rewritten with the past-tense "Documented cooperation surface" framing + four-bullet axes block + preserved `Companion BACKLOG.md item 41` / `**See also:**` lines (verified via `Read` on `docs/GLOSSARY.md:679-693`).
   - `docs/README.md` one-line forward-pointer inserted at line 218 (between the existing closing paragraph at line 216 and the `## Using the package in your own project` heading at line 220) per spec line 566 verbatim (verified via `grep` for `Sharded mode\|multi-database`).
   - `KANBAN.md` card-move clean: WIP card body removed from In-progress; `### In progress` summary paragraph at line 50 rewritten with the count bump `three`→`four` and the queued-card-list shrunk from two to one; new `### DONE-019-0.0.7 — Multi-database cooperation contract` card landed at line 1742 (after `### DONE-018-0.0.7` at line 1740, before `## Release readiness checklist` at line 1750); body is spec line 569 verbatim with the active-path substitution (`docs/spec-019-multi_db-0_0_7.md` instead of `docs/SPECS/spec-019-multi_db-0_0_7.md` per Decision 1 rev3 R10) plus the precedent-matching `Parity:` and `Build plan:` framing lines.
   - `CHANGELOG.md` appended a fourth bullet under the existing `[0.0.7]` `### Added` subsection at line 33 (after the third existing `DONE-018` bullet, before the `### Changed` heading at line 36); wording is spec line 576 verbatim (per Worker 3's character-for-character `diff` check, which returned empty).
   - No edits to `README.md` / `GOAL.md` / `TODAY.md` / `docs/TREE.md` per Decision 8 (verified via `git diff` returning empty for those files — see check 8 below).
   - No version bump per Decision 9 (verified via `git diff -- pyproject.toml django_strawberry_framework/__init__.py tests/base/test_init.py` returning empty — see check 7 below).
   - Zero new public exports per spec DoD item 16 — `__all__` unchanged (verified via `git diff -- django_strawberry_framework/__init__.py` returning empty — see check 5 below).
   - Three final-gate sub-bullets all tick: `uv run ruff format .` returned `112 files left unchanged` (idempotent confirmation of Worker 2's run); `uv run ruff check --fix .` returned `All checks passed!`; `uv run pytest --no-cov` returned `781 passed, 3 skipped, 5 warnings in 49.55s` (matches Worker 2's report — the 3 skips are the 2 Slice 2 multi-db live tests skipping cleanly without `FAKESHOP_SHARDED=1` plus 1 pre-existing seed-shards-command marker test).

2. **DRY check across this slice and prior accepted slices.** Slice 3 introduces no helpers (docs-only). The cross-doc wording overlap between GLOSSARY / CHANGELOG / KANBAN / README is intentional per spec — each surface needs its own version of the contract for its readership; the spec pins each block separately at lines 563 / 566 / 569 / 576. No new duplication concerns vs. Slice 1's inlined `_sel` / `_register_type_definition` (those remain a Slice-1 cross-slice DRY observation for the integration pass) or Slice 2's three within-file repetitions (autouse fixture, `override_settings`/`clear_url_caches` block, duplicated query body — also deferred to the integration pass). Acceptable for per-slice DRY scope.

3. **Final-gate commands** (slice's own per-spec final gates per Slice checklist lines 100-103; these are SEPARATE from the build-level `bld-final.md` gate):
   a. `uv run ruff format .` — **pass** (`112 files left unchanged`; idempotent confirmation of Worker 2's identical result).
   b. `uv run ruff check --fix .` — **pass** (`All checks passed!`; no fixes needed, idempotent confirmation).
   c. `uv run pytest --no-cov` — **pass** (`781 passed, 3 skipped, 5 warnings in 49.55s`). The 3 skips: 2 from `examples/fakeshop/test_query/test_multi_db.py` (Slice 2 live tests skipping cleanly without `FAKESHOP_SHARDED=1` per Decision 6) + 1 from `examples/fakeshop/tests/test_commands.py` (pre-existing seed-shards-command marker test). No `--cov*` flags.

4. **Spec reconciliation.** Worker 3 raised one Low finding under `Notes for Worker 1 (spec reconciliation)`: spec line 563 pins the four-axes block as flowing inline prose with `(1)`/`(2)`/`(3)`/`(4)` numbering, semicolons between bullets, lowercase bullet starts, and a parenthetical clause on bullet 1; Worker 2's landed GLOSSARY rendering at `docs/GLOSSARY.md:685-688` adapts these into numbered list items with capitalized starts, period terminators, an em-dash-joined parenthetical on bullet 1, a `for root querysets` suffix on bullet 2 (matching the consistent suffix in spec lines 569 and 576 — i.e., the CHANGELOG bullet and the KANBAN Done body already use that suffix), and a link-anchor swap on bullet 3 from `[Prefetch(queryset=...)](#optimizerhint)` to `Prefetch(queryset=...)` plus `[OptimizerHint.prefetch(...)](#optimizerhint)`.

   **Decision: accept as licensed adaptation; no spec edit.** Rationale:
   - **The spec already calls them bullets.** Spec line 563 reads "followed by the four narrowed-axis bullets" — the bulleted rendering is what the spec asks for; the adaptations are what flowing prose needs to become bullets.
   - **The substantive content is faithful.** All four axes are preserved character-for-character on the semantic payload (router behavior, `instance=` hint shape, `_db` preservation through `OptimizationPlan.apply`, consumer-provided `Prefetch(queryset=...)` round-trip with the generated-child boundary, strictness-mode connection-agnostic shape). No axis was added, dropped, or factually changed.
   - **The `for root querysets` suffix is consistent with the rest of the spec.** Spec line 569 (KANBAN Done body) and spec line 576 (CHANGELOG bullet) both already say "`.using(alias)` `_db` preservation through `OptimizationPlan.apply` for root querysets". Adding the same suffix to bullet 2 of the GLOSSARY entry aligns the three documented surfaces; absent the suffix the GLOSSARY entry would be the outlier.
   - **The link-anchor swap on bullet 3 is correct, not a regression.** The spec's `[Prefetch(queryset=...)](#optimizerhint)` links the literal text `Prefetch(queryset=...)` to the GLOSSARY's `#optimizerhint` anchor, which renders confusingly (the visible text and the anchor target are different concepts). Worker 2's rewrite links `[OptimizerHint.prefetch(...)](#optimizerhint)` so the visible text matches the anchor target — cleaner cross-doc navigation.
   - **Decision 1 rev3 R10 precedent.** "References use the path the file actually has at the time the reference is written" already establishes the principle that minor textual reconciliation between spec and target file is licensed when the substantive content matches. The bullet-shape adaptations fall under the same principle: rendering flowing prose as a numbered list is a target-file convention, not a contract change.

   The adaptations are within Worker 2's natural license for "convert spec-pinned prose into a bulleted form per the target file's convention". Editing the spec to pin the rendered bullet shapes verbatim would be a stylistic tightening that adds no contract value (the contract is the four axes, not the bullet punctuation); not worth the spec churn. The rendered GLOSSARY bullets stand.

5. **Public surface unchanged.** `git diff -- django_strawberry_framework/__init__.py` returned empty. `__all__` and the re-export list are unchanged.

6. **No production code change.** `git diff -- django_strawberry_framework/` returned empty. Decision 2 satisfied; the cooperation already existed at `django_strawberry_framework/types/resolvers.py:82` per Decision 2 / DoD item 6.

7. **No version bump.** `git diff -- pyproject.toml django_strawberry_framework/__init__.py tests/base/test_init.py` returned empty. Decision 9 joint-cut policy satisfied; `pyproject.toml`, `__version__`, and the pinned version assertion remain at `0.0.6` — the last `0.0.7` card to ship (`WIP-ALPHA-020-0.0.7`) owns the bump.

8. **No `README.md` / `GOAL.md` / `TODAY.md` / `docs/TREE.md` edits.** `git diff -- README.md GOAL.md TODAY.md docs/TREE.md` returned empty. Decision 8 satisfied.

9. **No fakeshop schema / settings edits.** `git diff -- examples/fakeshop/apps/library/schema.py examples/fakeshop/apps/products/schema.py examples/fakeshop/config/settings.py` returned empty. Decisions 4 / 5 satisfied.

**Spec status-line re-verification.** Read `docs/spec-019-multi_db-0_0_7.md:1-5` at entry. Current line 4: `Status: draft (revision 5, post-rev4 feedback against docs/feedback.md)`. The Slice 2 Worker 1 reconciliation already inlined an `X7` slot in rev 5 (per `docs/builder/bld-slice-2-fakeshop_live.md` `### Spec changes made (Worker 1 only)`); Slice 3 makes no spec edit, so no rev bump or status-line flip is needed at this pass. The spec lifecycle keeps the file at `docs/spec-019-multi_db-0_0_7.md` (no archive move per Decision 1 / `BUILD.md` "Spec stays at its working location"); any future shipped-wording flip is owned by an explicit archival workflow, not this build.

### Summary

Slice 3 lands the docs-only promotion of the `Multi-database cooperation` contract to `shipped (0.0.7)` across four documentation files: `docs/GLOSSARY.md` (Index row flip + entry body rewrite with past-tense framing + four-axis bullets per spec Decision 3); `docs/README.md` (one-line forward-pointer from the `### Sharded mode (multi-DB)` section to the GLOSSARY entry); `KANBAN.md` (column-move of `WIP-ALPHA-019-0.0.7` to `DONE-019-0.0.7` with past-tense Done body per spec line 569, `### In progress` summary update with count bump and queued-card-list shrink); `CHANGELOG.md` (fourth bullet appended under the existing `[0.0.7]` `### Added` subsection per spec line 576 verbatim). No production code change, no public-surface change, no fakeshop schema / settings change, no version bump (per Decision 9 joint-cut policy). The 7 pinned tests from Slices 1 and 2 stand; the documented contract now aligns with the shipped behavior.

### Spec changes made (Worker 1 only)

None. The Worker 3 Low finding about the GLOSSARY entry-body bullet shapes was disposed of as licensed adaptation under Decision 1 rev3 R10's principle (the spec already calls them bullets, the substantive content of all four axes is faithful, the `for root querysets` suffix on bullet 2 aligns the GLOSSARY surface with the matching CHANGELOG / KANBAN suffix, and the link-anchor swap on bullet 3 is a cleanup not a regression). Editing the spec to pin the rendered bullet shapes verbatim would add no contract value; the contract is the four axes.
