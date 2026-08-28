# Build: Review round 1, cohort R1c — fakeshop activation, live coverage, deferred surface

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` (Slices 4 and 5; Decisions 1, 2, 13; Goals 5, 6, 8; the `Meta.fields_class` / per-field-read-gate Non-goals; the `## Test plan` Slice 4 list; the whole `## Doc updates` section; Definition of done items 10-14)
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`
Build plan: `docs/builder/build-034-permissions-0_0_10.md`
Status: final-accepted

## Plan (Worker 1)

**Not applicable.** This cohort is a read-only conformance audit at `HEAD` inside a residual-reconciliation cycle; it lands no source and no test, so the build plan dispatches it directly as a Worker 3 pass with no Worker 1 planning pass. The cohort's contract is the build plan's `## Ownership partition` R1c row plus its `## Grading rule every R1 cohort applies`.

---

## Build report (Worker 2)

**Not applicable.** No Worker 2 build pass exists for this cohort: R1 lands no source (`docs/builder/build-034-permissions-0_0_10.md` `## Ownership partition`: "Every R1 cohort is **read-only over source and tests** - it writes exactly one file, its own artifact"). There is therefore no Worker 2 diff, no Worker 2 `### Failability proofs` record to audit, no hot-path number to verify (plan declares `none` for R1), and no floor-verification scope (plan declares `none` for R1).

---

## Review (Worker 3)

Conformance audit at `HEAD`, `2026-08-28`. Working tree is legitimately dirty with a concurrent session's kanban-tooling work (the plan's baseline-dirty list); nothing in that list was edited or reverted by this pass.

### Contract census

Grades per `docs/builder/build-034-permissions-0_0_10.md` `## Grading rule every R1 cohort applies`.
Raw `path:NN` refs appear alongside symbol identifiers only because this is a per-cycle artifact (`AGENTS.md` rule 27).

#### A. Slice 4 — products activation (spec `## Slice checklist` Slice 4; DoD 10, 11; Goal 5)

| # | Contract (spec section) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| A1 | "the four commented cascade-permission `get_queryset` hooks (one per type) ... activate" (Slice 4 box 1; DoD 10) | `examples/fakeshop/apps/products/schema.py::CategoryType.get_queryset` (:90), `::ItemType.get_queryset` (:130), `::PropertyType.get_queryset` (:168), `::EntryType.get_queryset` (:205) — all four live, uncommented, `@classmethod`-decorated | CONFORMS |
| A2 | the `apply_cascade_permissions` import activates | `examples/fakeshop/apps/products/schema.py #"    apply_cascade_permissions,"` (:55) inside the live `from django_strawberry_framework import (...)` block | CONFORMS |
| A3 | "staff sees everything" | each hook: `#"if user and user.is_staff:"` -> `return queryset` (:98-99, :139-140, :176-177, :214-215) | CONFORMS |
| A4 | "**every non-staff branch — including the matching `view_<model>` permission — gets `queryset.filter(is_private=False)` plus `apply_cascade_permissions(cls, ..., info)`**" | all four hooks: the `elif user and user.has_perm("products.view_<model>")` branch AND the fall-through `return` are byte-identical `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` (:101-102, :142-143, :179-180, :217-218) | CONFORMS (see DRY finding D1 — the two branches are literally the same expression) |
| A5 | "the `view_<model>` branch cascades too, so a nested non-null FK selection can never reach a hidden target and raise `RelatedObjectDoesNotExist`" | pinned live by `examples/fakeshop/test_query/test_products_api.py::test_cascade_view_item_user_respects_category_visibility` (:2197) and `::test_cascade_view_entry_user_nested_selection_drops_hidden_targets` (:2234), both asserting `"errors" not in payload` on a non-null nested `category { name }` selection | CONFORMS |
| A6 | the `TODO-ALPHA-034-0.0.10` staging markers are removed by the slice that shipped them (`AGENTS.md` rule 26; `BUILD.md` integration-pass sweep) | `grep -ohE 'TODO-(ALPHA\|BETA\|STABLE)-034[A-Za-z0-9._-]*' examples/fakeshop/apps/products/schema.py` -> 0 occurrences | CONFORMS |
| A7 | user resolution is `info.context.request.user`, never `info.context.user` (`## User-facing API`; `## Current state` "one mechanical fix Slice 4 applied on activation") | all four hooks read `#"user = getattr(getattr(info.context, \"request\", None), \"user\", None)"` (:97, :138, :175, :213); this is `django_strawberry_framework/utils/permissions.py::request_from_info`'s path spelled inline, not a call to it (see finding L2) | CONFORMS |
| A8 | "Audit the products seeders' `is_private` defaults and re-pin every existing live assertion that counted would-be-hidden rows" (Slice 4 box 3) | re-pins present and marked: 12 test functions in `examples/fakeshop/test_query/test_products_api.py` carry an explicit activated-cascade / post-cascade re-pin note (:1164, :1195, :1233, :1264, :1324, :1399, :1638, :1731, :1768, :1792, :1894, :1963) and 2 in `examples/fakeshop/apps/products/tests/test_schema.py` (`::test_project_schema_executes_products_categories_list` :49, `::test_project_schema_traverses_products_relations` :83) | CONFORMS (the re-pins are real; the rationale's **count** of them is stale — see census row E3) |
| A9 | "Existing products live assertions that counted public-only rows keep passing" (Slice 4 box 4; DoD 11) | `uv run pytest examples/fakeshop/test_query/test_products_api.py --no-cov` — see `### Temp test verification` / mechanical runs below: green at `HEAD` | CONFORMS |
| A10 | seeders produce a deterministic split: `Category` / `Property` by `<index> % 2 == 1` | `examples/fakeshop/apps/products/services.py::seed_data #"\"is_private\": cat_index % 2 == 1,"` and `#"\"is_private\": prop_index % 2 == 1,"` | CONFORMS |
| A11 | `Item` / `Entry` `is_private` is "a per-row `random.choice([True, False])`" (rationale `## Risks and open questions` live-suite-sensitivity bullet) | `services.py::seed_data #"is_private=privacy.choice([True, False]),"` where `privacy = random.Random(PRIVACY_STREAM_SEED)` (`services.py #"PRIVACY_STREAM_SEED = 20260827"`); the module comment above it records the flip: `#"Item/Entry privacy is drawn from this fixed-seed stream rather than the process"` | SUPERSEDED — a later change replaced the process RNG with a fixed-seed stream; the superseding work names itself in the comment at `services.py #"an unseeded draw makes every derived expectation probabilistic"` |

#### B. Slice 4 — the live-test census (spec `## Test plan` `### Slice 4`; DoD 10)

Derived from the spec's own `### Slice 4` list (`docs/SPECS/spec-034-permissions-0_0_10.md`:419-425), not from a transcription. All six named tests exist under their spec names; searched with `grep -rn "def <name>" examples/ tests/`.

| # | Named test (spec) | Evidence at `HEAD` | First line | Grade |
|---|---|---|---|---|
| B1 | `test_cascade_anonymous_sees_no_entries_under_private_categories` | `examples/fakeshop/test_query/test_products_api.py`:2162 | `create_users(1)` | CONFORMS |
| B2 | `test_cascade_view_item_user_respects_category_visibility` | same file :2197 | `create_users(1)` | CONFORMS |
| B3 | `test_cascade_view_entry_user_nested_selection_drops_hidden_targets` | same file :2234 | `create_users(1)` | CONFORMS |
| B4 | `test_cascade_staff_sees_everything` | same file :2270 | `create_users(1)` | CONFORMS (exists under its spec name) — but see B4a |
| B4a | Slice 4 box 2: live coverage runs "across the products 2-deep FK chain (`Entry → Item → Category` / `Entry → Property → Category`): ... **staff sees everything**"; DoD 10's "anonymous / per-`view_<model>` / staff matrix" over the same chain | `::test_cascade_staff_sees_everything` iterates only `#"for field, model in ((\"allCategories\", models.Category), (\"allItems\", models.Item)):"` — `allEntries` and `allProperties` are never queried as staff, in this file or anywhere (`grep -rn 'allEntries' examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py tests/` -> 10 occurrences, none under a staff client). Proof P2 measures the consequence: removing `EntryType.get_queryset`'s staff branch entirely (by breaking its user read) fails **0** rows | **SKIPPED** — routes to R3. See High finding **H1** |
| B5 | `test_cascade_query_count_fixed` | same file :2301 | `create_users(1)` | CONFORMS |
| B6 | `test_cascade_composes_with_filter_and_order_live` | same file :2344 | `create_users(1)` | CONFORMS |
| B7 | "First line of every new test: `services.create_users(1)` ... per `AGENTS.md`" | all six above; the module imports the helpers by name (`test_products_api.py #"from apps.products.services import create_users, delete_data, seed_cascade_split, seed_data"`, :34) so the call reads `create_users(1)` rather than `services.create_users(1)` — the same helper from the same module, satisfying `AGENTS.md` rule 8 | CONFORMS |
| B8 | "the staff branch keys on `is_staff`, and `services.create_users` provisions each `staff_<n>` as **staff-not-superuser** (`is_staff=True` only — its docstring's 'superuser' wording is inaccurate)" | `services.py::create_users #"is_staff=True,"` under `username = f\"staff_{n}\"`, with no `is_superuser`; the docstring's `#"Also creates one ``staff_<n>`` superuser per unit for convenience."` is still inaccurate exactly as the spec says | CONFORMS (spec correctly describes `HEAD`, inaccurate docstring included) |
| B9 | a `services.seed_cascade_split` helper hosts the cascade fixture | `examples/fakeshop/apps/products/services.py::seed_cascade_split` (:459) exists and returns the eight named rows | CONFORMS |
| B10 | "seeded the deterministic private/public chains the new cascade tests need through a **module-local helper**" (rationale `## Risks and open questions`) | the helper is NOT module-local to the test file: it lives at `services.py::seed_cascade_split` and is imported into the test module | STALE-DESCRIPTION — routes to R2 |
| B11 | "Existing products live assertions are audited for private-fixture sensitivity; any that assumed un-cascaded visibility are re-pinned in the same change (**expected small** — the suite seeds public fixtures by default)" (`### Slice 4` last bullet) | the parenthetical is falsified by the rationale's own resolution ("the seeders are *not* public-only ... the re-pin was load-bearing, not minimal") and by the 14 re-pin-marked test functions measured in A8 | STALE-DESCRIPTION — routes to R2 |

#### C. Decision 2 — the forward-reserved `fields_class` slot and the per-field-gate Non-goals (Goal 6; `## Non-goals`)

| # | Contract | Evidence at `HEAD` | Grade |
|---|---|---|---|
| C1 | "`DjangoTypeDefinition.fields_class` ... is declared as an inert `type \| None = None` sidecar slot" | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"fields_class: type \| None = None"` (:175), sitting immediately after the shipped `filterset_class` / `orderset_class` slots — the structural mirror the Decision claims | CONFORMS |
| C2 | "It stays `None` and has **no populator** this card" | `grep -rn 'fields_class' django_strawberry_framework/` returns 5 occurrences across 4 lines: `exceptions.py`:261 (deferred-key error message), `definition.py`:68 / :70 (the slot's own docstring), `definition.py`:175 (the declaration), `base.py`:67 (the `DEFERRED_META_KEYS` membership). No assignment site, no `__init_subclass__` read, no finalizer binding | CONFORMS |
| C3 | "`Meta.fields_class` remains rejected at validation (still in `DEFERRED_META_KEYS`)" | `django_strawberry_framework/types/base.py #"    {\"aggregate_class\", \"fields_class\", \"search_fields\"},"` (:66-68); rejection path `base.py #"deferred = sorted(declared & DEFERRED_META_KEYS)"` (:1263); pinned by `tests/types/test_base.py`:415 ("Every key in DEFERRED_META_KEYS must raise until the spec that owns it ships") | CONFORMS |
| C4 | the Decision's own anchor `[types/base.py][types-base] #"aggregate_class"` still resolves | the substring `aggregate_class` is present at `base.py`:67 | CONFORMS |
| C5 | "`_bind_fieldsets` lands with `TODO-BETA-046-0.1.1`" | `_bind_fieldsets` exists nowhere in `django_strawberry_framework/` (correct — it is future work); but `TODO-BETA-046-0.1.1` names no live card: `grep -c '^### \[TODO-BETA-046-0.1.1' KANBAN.md` -> 0, while card 046 today is `DONE-046-0.0.14` (transport security, `KANBAN.md`:1840) and the FieldSet owner is `TODO-BETA-055-0.1.1` (`KANBAN.md`:596) with its spec on disk at `docs/SPECS/spec-055-fieldset-0_1_1.md` | RENAMED (card-id rot) — routes to R2, live name `TODO-BETA-055-0.1.1` |
| C6 | "Reserving the slot is the only `definition.py` change this card makes for per-field gates; it does not promote the key, ship a gate, or alter resolution" | confirmed by C2's enumeration; `scripts/review_inspect.py` on `definition.py` reports the slot inside no control-flow hotspot (the file's two hotspots are `related_target_for` :264 and `_resolves_id_off_pk` :407, neither reading `fields_class`) | CONFORMS |
| C7 | Non-goal: "`Meta.fields_class` stays in `DEFERRED_META_KEYS`; declaring it keeps raising `ConfigurationError`" | same evidence as C3; `exceptions.py`:261 names `fields_class` in the deferred-surface message | CONFORMS |
| C8 | Decision 2's composition rule ("a field-level gate does **not** short-circuit cascade visibility") is "recorded here and reflected into the glossary" | `docs/GLOSSARY.md`:1476 (Per-field permission hooks body) states host, signature, failure modes and the cascade-composition rule verbatim in substance | CONFORMS |

#### D. Decision 13 and Goal 8 — the version boundary (DoD 13)

Graded as claims **about this card**, not about the current version number.

| # | Contract | Evidence at `HEAD` | Grade |
|---|---|---|---|
| D1 | "No slice edits `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, or `uv.lock`" | `pyproject.toml` carries no version literal at all (`#"dynamic = [\"version\"]"`, :8; `[tool.hatch.version]`, :95) so there is nothing for a slice to edit there; `django_strawberry_framework/__init__.py #"__version__ = \"0.0.14\""` (:61) and `tests/base/test_init.py::test_version #"assert __version__ == \"0.0.14\""` (:21) both read `0.0.14`, i.e. they have moved four patch releases past `0.0.10` under later cuts, not under this card | CONFORMS (as a card-scoped claim) |
| D2 | "The exports pin in `tests/base/test_init.py` *does* grow in Slice 1 (two new `__all__` members)" | `django_strawberry_framework/__init__.py`:35-36 imports and :157-158 `__all__` entries for `aapply_cascade_permissions` / `apply_cascade_permissions`; `git diff -- django_strawberry_framework/__init__.py` is empty at `HEAD` | CONFORMS (Slice 1 surface; R1a owns the test-side pin) |
| D3 | "The `0.0.10` patch line is shared with `TODO-ALPHA-035-0.0.10`" (Decision 13 body) | card 035 is `DONE-035-0.0.10` today, and the spec's **own** opener spells it that way twice — the file contradicts itself between :3/:5 and :319 | RENAMED (card-id rot) — routes to R2; **already homed** on the board (`KANBAN.md`:398 names this exact site as `spec-034`'s single class-(c) clean prefix flip, `#"The \`0.0.10\` patch line is shared with"`) |
| D4 | "no `CHANGELOG.md` release heading is promoted (the joint `0.0.10` cut owns the bump)"; "CHANGELOG bullets land under `[Unreleased]`" | `CHANGELOG.md`:75 now reads `## [0.0.10] - 2026-06-16` and carries the card's bullets at :80 (`apply_cascade_permissions` pair) and :81 (products cascade activation). The heading promotion is the joint cut's, exactly as the Decision assigns it | CONFORMS (as a card-scoped claim); the spec's own `Status:` line at :5 already records the released heading, so nothing is stale here |
| D5 | Goal 8 "Keep package version state owned by the joint `0.0.10` cut" | same as D1 | CONFORMS |
| D6 | Spec opener: "the on-disk version reads `0.0.9` as of this writing — the `0.0.9` cut has landed" (:3) | on-disk version is `0.0.14` | Dated observation, explicitly framed "as of this writing" — **not** graded a defect; flagged to R2 only as a judgement call (see notes) |

#### E. Slice 5 and `## Doc updates` — read-only audit (DoD 12)

**This cycle edits none of these files** (`docs/builder/build-034-permissions-0_0_10.md` `## Maintainer-set scope for this cycle`). Rows record whether the Slice 5 edit landed, nothing more.

| # | Claimed edit (`## Doc updates`) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| E1 | GLOSSARY: flip `apply_cascade_permissions` to `shipped (0.0.10)` | `docs/GLOSSARY.md`:269 `**Status:** shipped (\`0.0.10\`).`; index row :94 `\| shipped (\`0.0.10\`) \|` | CONFORMS |
| E2 | GLOSSARY: "correcting the current body's 'FK / M2M' scope to forward-FK / OneToOne only" | `docs/GLOSSARY.md`:271 reads "**single-column concrete forward FK / OneToOne edges** ... M2M ... stay out of scope"; `grep -n 'FK / M2M' docs/GLOSSARY.md` -> no match | CONFORMS |
| E3 | GLOSSARY: re-status `Per-field permission hooks` to `planned for 0.1.1` with the Decision 2 body note | `docs/GLOSSARY.md`:185 index row `planned for \`0.1.1\``; body :1467-1480 carries host / signature / failure modes / cascade-composition rule | CONFORMS |
| E4 | GLOSSARY: cross-reference the cascade from the `get_queryset` visibility hook entry | `docs/GLOSSARY.md`:1001 ("A type's `get_queryset` is also the seam `apply_cascade_permissions` composes ...") and the :1003 See-also | CONFORMS |
| E5 | GLOSSARY: "update the Index rows and the Public exports list (two new symbols)"; "**Net-new entries: none** — `aapply_cascade_permissions` is documented inside the existing entry" | `docs/GLOSSARY.md`:58 and :59 — both symbols listed, `aapply_cascade_permissions` pointing at `#apply_cascade_permissions` (shared entry, no new heading) | CONFORMS |
| E6 | `docs/README.md`: "the shipped-today list gains the permissions bullet" | `docs/README.md`:122 (`apply_cascade_permissions` / `aapply_cascade_permissions` (new in `0.0.10`) — cascade-permissions subsystem ...) | CONFORMS |
| E7 | `docs/README.md`: "the 'Coming next' `0.0.10` line shrinks to the `035` remainder" | not re-derivable at `HEAD`: the package is at `0.0.14`, so the "Coming next" section has been rewritten by four later cuts. Not a `034` gap | SUPERSEDED (by later releases) — no action |
| E8 | `docs/TREE.md`: "`permissions.py` moves from 'planned by TODO-ALPHA-034-0.0.10' to its real one-line description" | `docs/TREE.md`:207 `permissions.py  # Call-time cascade visibility: ``apply_cascade_permissions`` (sync + async).`; `grep -c 'TODO-ALPHA-034' docs/TREE.md` -> 0 | CONFORMS |
| E9 | `docs/TREE.md`: "`tests/test_permissions.py` joins the test tree" | `docs/TREE.md`:470 `test_permissions.py  # Cascade-permission tests - ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.` | CONFORMS |
| E10 | `TODAY.md`: products sections gain the activated cascade hooks; the commented-hook caveat rewrites to the live shape | `TODAY.md`:324 describes the four live hooks, the two 2-deep chains, and the anonymous / staff / `view_<model>` matrix | CONFORMS |
| E11 | `TODAY.md`: "the 'What products is still waiting for' list drops permissions and its stale `TODO-ALPHA-033-0.0.10` card id" | `grep -c 'TODO-ALPHA-033' TODAY.md` -> `0` | CONFORMS |
| E12 | `README.md`: the status paragraph's newest-shipped-surface line gains the permissions subsystem | `README.md`:77 (`0.0.10` — cascade visibility permissions ...) | CONFORMS |
| E13 | `CHANGELOG.md`: `### Added` bullets for the helper pair and the products cascade activation | `CHANGELOG.md`:80 and :81, both under the `## [0.0.10]` heading | CONFORMS |
| E14 | `KANBAN.md`: card moved to Done as `DONE-NNN-0.0.10`; spec reference points at the spec file | `KANBAN.md`:113 `\| \`DONE-034-0.0.10\` - Permissions subsystem \| [spec-034-permissions-0_0_10.md](docs/SPECS/spec-034-permissions-0_0_10.md) \|` — Done, and the reference resolves (to the **archived** path, which is correct post-archive; the spec's instruction text still names the pre-archive path — see F2) | CONFORMS |
| E15 | `KANBAN.md`: "surface the unowned M2M / reverse-relation cascade follow-up to the maintainer for a new card" | not established by this cohort — the board's cascade-follow-up rows are outside R1c's territory and the concurrent session is mid-edit on `KANBAN.md` | **Not graded** — recorded for R2 rather than asserted |
| E16 | `GOAL.md` (ratified at Slice-5 final verification): correct the cascade showcase's user read at three sites — the two showcase `get_queryset` bodies and the shared `_user(info)` helper | `GOAL.md`:116 and :141 (the two showcase bodies) and `GOAL.md::_user`:328-329, all three reading `getattr(getattr(info.context, "request", None), "user", None)`; `grep -c 'getattr(info.context, "user"' GOAL.md` -> 0 | CONFORMS |

#### F. Decision 1 and the spec's own path claims

| # | Contract | Evidence at `HEAD` | Grade |
|---|---|---|---|
| F1 | Decision 1: "The spec file lives at **`docs/spec-034-permissions-0_0_10.md`** (this document)" (:190) | the file is at `docs/SPECS/spec-034-permissions-0_0_10.md`; `ls docs/spec-034-permissions-0_0_10.md` -> `No such file or directory` | STALE-DESCRIPTION — routes to R2 |
| F2 | DoD 1's verification command: `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` reports `OK: <N> terms` (:464) | executed at `HEAD`: `error: missing file: docs/spec-034-permissions-0_0_10.md`, **exit 2**. The same command against the archived path is green (`OK: 42 terms`, exit 0 — recorded in the build plan's pre-flight step 6) | STALE-DESCRIPTION, **and the only spec claim in this cohort's territory that is executably false** — routes to R2 |
| F3 | `## Doc updates` :441: "confirm the spec reference points at `docs/spec-034-permissions-0_0_10.md`" | the board points at `docs/SPECS/spec-034-permissions-0_0_10.md` and is correct; the spec's instruction names the pre-archive path | STALE-DESCRIPTION — routes to R2 |

Population of the pre-archive path spelling in the spec: **4 occurrences on 3 lines** (`grep -o 'docs/spec-034-permissions-0_0_10.md' | wc -l` -> 4) — :190, :441, and :464 twice (once as the path, once inside the command). Every reference-style **link definition** was re-pointed by the archive sweep, so no link is broken; the rot is confined to literal in-prose path spellings.

#### G. Card-id rot — the population, spec and source recorded separately

Measured with the shortest distinctive token and counted as **occurrences** (`grep -ohE 'TODO-(ALPHA|BETA|STABLE)-[0-9]{3}[A-Za-z0-9._-]*' <file> | sort | uniq -c`), never matching lines.

**G-i. Spec body** (`docs/SPECS/spec-034-permissions-0_0_10.md`), R1c territory unless noted:

| Spelling | Occurrences | Sites | Live referent | Note |
|---|---|---|---|---|
| `TODO-BETA-046-0.1.1` | 2 | :203 (Decision 2 — R1c), :257 (Decision 6 consumer-recipe divergence — R1a) | `TODO-BETA-055-0.1.1` | **already homed** — `KANBAN.md`:367 and :398 both carry the four-citation `spec-034` clause (3 live-claim repoints + 1 revision-log decided-non-edit) |
| `TODO-ALPHA-035-0.0.10` | 1 | :319 (Decision 13 — R1c) | `DONE-035-0.0.10` | **already homed** — `KANBAN.md`:398 names this exact site |
| `TODO-ALPHA-034-0.0.10` | 6 | :42 (project conventions, quoting `docs/TREE.md`'s old predicted-path row), :64 (Slice 4 box 1 — R1c), :89 (`## Current state` — R1c), :435 (`## Doc updates`, quoting the same TREE row — R1c), :441 (`## Doc updates` card-wrap instruction — R1c), :485 (DoD 10 — R1c) | `DONE-034-0.0.10` | `KANBAN.md`:398 grades this class: :42 and :435 are class-(b) verbatim quotations of text that has since changed (leave verbatim), :441 is class-(a) card-wrap slice-instruction history (de-tense), :64/:89/:485 are the live-claim sites |

**G-ii. Rationale companion** (`docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`): 3 occurrences of `TODO-BETA-046-0.1.1`, all at :40, :72, :84 — every one inside a `- **Revision N**` log bullet or its cross-reference, i.e. the decided-non-edit class (true as history: `046` was the live id on 2026-06-14).

**One consequence of Slice 0's move that R2 must know**: `KANBAN.md`:398's homed item cites the bare-numeral falsehood as `docs/SPECS/spec-034-permissions-0_0_10.md #"but the live kanban card is"`. That sentence no longer lives in the spec — Slice 0 moved it into the rationale companion, where it now sits at `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`:72. The board's citation is now dangling. Nothing in this cycle may edit `KANBAN.md`, so this is a maintainer note, not work.

**G-iii. Source, R1c territory** — measured per file:

| File | Rotted occurrences | Breakdown | Live referent |
|---|---|---|---|
| `examples/fakeshop/apps/products/schema.py` | **18** | `TODO-BETA-046-0.1.1` ×7 (:22 module docstring, :37 future-import, :87, :127, :165, :202 the four commented `fields_class` lines, :189 the `description`-field note), `TODO-BETA-047-0.1.2` ×5 (:85, :125, :163, :200 the four commented `search_fields` lines — and :22 module docstring), `TODO-BETA-049-0.1.3` ×6 (:36 future-import, :86, :126, :164, :201 the four commented `aggregate_class` lines, :22 module docstring) | FieldSet `TODO-BETA-055-0.1.1`; search `TODO-BETA-056-0.1.2` (`KANBAN.md`:677); aggregates `TODO-BETA-058-0.1.3` (`KANBAN.md`:857) |
| `examples/fakeshop/apps/products/schema.py` | 1 **correct** | `TODO-BETA-062-0.1.5` (:238, `Query` docstring) — card 062 is live under exactly that id (`KANBAN.md`:1052). **Do not sweep it.** | — |
| `django_strawberry_framework/types/definition.py` | **1** | `TODO-BETA-046-0.1.1` at :69, inside the `fields_class` slot docstring | `TODO-BETA-055-0.1.1` — **already homed**, `KANBAN.md`:250 carries this exact site with its remedy and its "fold into whichever WP batch legitimately opens `types/definition.py`" boundary |
| `examples/fakeshop/apps/products/services.py`, `filters.py`, `orders.py`, `models.py`, `apps/products/tests/test_schema.py`, `tests/test_services.py` | 0 | — | — |
| `examples/fakeshop/test_query/test_products_api.py` | 0 rotted, 1 correct | `TODO-BETA-062-0.1.5` | — |

**The source-side spelling is the one no existing card covers.** `KANBAN.md`:250 homes only the `types/definition.py` site; :367/:398 home only the spec-side citations. The **18 occurrences in `examples/fakeshop/apps/products/schema.py`** are, as far as this cohort can establish, unowned — and `KANBAN.md`:398 explicitly warns that 4 spec sites are class-(b) "verbatim quotations of products-schema markers", so a spec-only correction would diverge from the un-edited source it quotes. That is the "worse than uniformly-wrong" shape the cohort brief names. Recorded as finding **M2**.

#### H. `## Current state` — clause-by-clause (per `BUILD.md` `### `## Current state`: observations stand, predictions do not`)

| # | Clause | Truth at `HEAD` | Grade |
|---|---|---|---|
| H1 | ":83 — "**`permissions.py` shipped in Slice 1.** As authored, no permissions module existed"" | dated observation of the pre-build repo | stands |
| H2 | ":83 — "Slice 1 has since landed the module ... so `permissions.py` now exists and both symbols import from the package root"" | true (`django_strawberry_framework/__init__.py`:35-36, :157-158) | stands |
| H3 | ":83 — "**The four products-schema hooks that call it remain comments (Slice 4's uncomment).**"" | **FALSE.** All four are live classmethods (census A1). This is a present-tense claim about the build's own outcome, i.e. the prediction class, and it is contradicted by the spec's own `Status:` line, Slice-checklist Slice 4, and DoD 10 | **must be rewritten** — routes to R2 |
| H4 | ":89 — "**The fakeshop activation site is staged.** `examples/fakeshop/apps/products/schema.py` carries a commented `apply_cascade_permissions` import and four commented `get_queryset` cascade hooks — one per type, each behind a `TODO-ALPHA-034-0.0.10` marker"" | **FALSE in its present-tense clause**: the import is live (:55), the hooks are live (:90/:130/:168/:205), and the `TODO-ALPHA-034` markers are gone (0 occurrences) | **must be rewritten** — routes to R2 |
| H5 | ":89 — "(the comment id is already correct; ... save for one mechanical fix Slice 4 applied on activation: the user read changed from `getattr(info.context, "user", None)` to `getattr(getattr(info.context, "request", None), "user", None)` ... so the activation was an uncomment **plus** that uniform one-line correction, not a pure uncomment)"" | true and load-bearing — the correction is present at all four sites (census A7) | stands; keep when H4 is rewritten |
| H6 | ":89 — "All four products models carry `is_private`"" | true: `examples/fakeshop/apps/products/models.py`:26 (`Category`), :68 (`Item`), :108 (`Property`), :153 (`Entry`) | stands |
| H7 | ":89 — "`apps/products/services.py`'s `create_users` provisions the staff / no-perm / per-`view_<model>` users"" | true: `services.py::create_users` creates `staff_<n>`, `regular_<n>`, and one user per entry in `#"VIEW_PERMISSIONS = ["` | stands |
| H8 | ":90 — "`fields_class` sits in `DEFERRED_META_KEYS` in `types/base.py`"" | true (census C3) | stands |
| H9 | ":90 — "the `fieldset/` package and its card live in the beta column"" | true in substance; the card is `TODO-BETA-055-0.1.1`, not `046` | stands (no id named in this clause) |

A slice-checklist box or DoD item gets no such licence, and none in this cohort's territory carries a stale figure: Slice 4's four boxes and DoD 10-14 all describe the shipped state accurately (census A, B, D, E).

#### I. Goals in territory

| # | Goal | Grade |
|---|---|---|
| I1 | Goal 5 "Make the fakeshop real-usage story true. The four products cascade hooks activate and are exercised live by real permission users (`create_users(1)`) across a 2-deep FK cascade with fixed query counts" | CONFORMS — census A1, B1-B7, and `::test_cascade_query_count_fixed` asserting `len(captured) == 3` |
| I2 | Goal 6 "Define the per-field permission surface without shipping it early ... `Meta.fields_class` stays deferred" | CONFORMS — census C1-C8 |
| I3 | Goal 8 "Keep package version state owned by the joint `0.0.10` cut" | CONFORMS — census D1, D5 |

#### Census totals

Enumerated per bucket so the totals are re-derivable rather than asserted.

- **CONFORMS — 47**: A1-A10 (10), B1-B9 (9), C1-C4 and C6-C8 (7), D1, D2, D4, D5 (4), E1-E6, E8-E14 and E16 (14), I1-I3 (3) — 10+9+7+4+14+3 = 47.
- **SKIPPED — 1**: B4a.
- **SUPERSEDED — 2**: A11, E7.
- **STALE-DESCRIPTION — 5**: B10, B11, F1, F2, F3.
- **RENAMED — 2**: C5, D3.
- **Not graded — 1**: E15 (outside R1c's reach).
- **Dated observation, not a defect — 1**: D6.

47 + 1 + 2 + 5 + 2 + 1 + 1 = **59 rows**, which re-derives from the section sizes independently: A 11, B 12, C 8, D 6, E 16, F 3, I 3 = 59. The `## Current state` clause table (H1-H9) contributes **9 further graded clauses** on `BUILD.md`'s own observation-versus-prediction axis (7 stand, 2 must be rewritten) and is counted separately, not folded into the five buckets.

**SKIPPED — one row, B4a**, enumerated by name rather than counted:

- **B4a — "staff sees everything" is unasserted over the `Entry` chain.** Spec Slice 4 box 2 states the live matrix runs across the 2-deep chain the sentence names, and DoD 10 restates it; the shipped `::test_cascade_staff_sees_everything` asserts it for `allCategories` and `allItems` only. **Proven negative:** searched `grep -rn 'allEntries' examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py tests/` (shortest distinctive token, 10 occurrences) and read each — none runs under a logged-in staff client; then measured it mechanically, since a read cannot prove a *row* is missing: proof P2 removed `EntryType.get_queryset`'s staff branch outright and **0 of 125 rows failed** at a scope covering both products test files, against a green pre-mutation baseline with 0 collection errors. Nothing pins it. Routes to **R3**; High finding **H1**.

Every other negative in this cohort's territory was established per contract, not assumed:

- the four hooks — searched `grep -n 'def get_queryset' examples/fakeshop/apps/products/schema.py`, 4 matches, all live classmethods; the inverse search `grep -c 'TODO-ALPHA-034' examples/fakeshop/apps/products/schema.py` -> 0 confirms no staged remnant;
- the six named live tests — searched `grep -rn "def <name>" examples/ tests/` per name (six separate searches, listed in census B), all six found in one file under the spec's own names, so neither an absence nor a RENAMED;
- `seed_cascade_split` — searched `grep -n 'def seed_cascade_split' examples/fakeshop/apps/products/services.py`, found at :459;
- the `fields_class` slot — searched `grep -rn 'fields_class' django_strawberry_framework/`, the declaration found at `definition.py`:175 and its absence-of-populator established by enumerating all 5 occurrences (census C2);
- every `## Doc updates` target — one grep per claimed edit, enumerated in census E; the two rows that did not resolve (E7, E15) are graded SUPERSEDED and not-graded respectively, neither being a `034` omission.

### High:

#### H1 — `EntryType.get_queryset`'s staff branch is pinned by nothing: removing it fails 0 rows

Measured, not read. Proof **P2** below replaced `EntryType.get_queryset`'s user read with the broken `getattr(info.context, "user", None)` form — the exact regression the spec's `## User-facing API` note warns about, which "binds `None` for every request, silently collapsing the staff / `view_<model>` branches to the anonymous public-only path". Result: **0 failing rows out of 125**, at a scope covering `examples/fakeshop/test_query/test_products_api.py` and `examples/fakeshop/apps/products/tests/test_schema.py`, against a green pre-mutation baseline (`125 passed`, exit 0) with **0** collection or setup errors.

**why 0: weakly pinned, not harness-impossible.** The harness can exhibit the failure trivially — `::test_cascade_staff_sees_everything` already logs in a staff client and asserts full-ORM-count equality; it simply never asks for `allEntries`:

```examples/fakeshop/test_query/test_products_api.py:2283:2286
    for field, model in (("allCategories", models.Category), ("allItems", models.Item)):
        response = _post_graphql(
            f"query {{ {field} {{ edges {{ node {{ id }} }} }} }}",
            client=client,
```

So `BUILD.md` `### Harness-impossible interleavings` does not apply and a production-call-site invariant assertion is not the remedy. The remedy is rows.

**Why the two non-staff branches cannot cover for it.** All three non-staff paths in every hook are the same expression (finding M1), so a user bound to `None` produces a queryset byte-identical to the `view_entry` branch's. The mutation is therefore invisible to `::test_cascade_view_entry_user_nested_selection_drops_hidden_targets` and to every anonymous row; only the staff branch distinguishes it, and nothing exercises the staff branch on `EntryType`. `allProperties` is in the same position: no test queries it as staff either.

**Why it is High rather than Medium.** `BUILD.md` `### Fail-open shapes` sets the floor at High "when the decision is a security or data-isolation boundary", and this is the row-visibility boundary itself. The specific mutation happens to fail *closed* (everyone gets the anonymous narrowing), so it is not a live leak today — but the assertion set cannot tell the direction: the same unpinned branch would equally not catch a hook rewritten so the permissive path is the default, and the spec records this exact user-read defect having shipped once already, in `GOAL.md` and in the pre-activation hook comments. A boundary that has already regressed once and is now pinned by zero rows is the definition of a High-severity gap.

**Recommended change** (R3): extend `::test_cascade_staff_sees_everything`'s loop to all four root fields — `allEntries` / `models.Entry` and `allProperties` / `models.Property` alongside the two present — so each of the four hooks' staff branches carries at least one row. **Test expectation:** with the loop extended, re-running proof P2 must fail at least the `allEntries` row (and the equivalent `PropertyType` mutation the `allProperties` row), while the unmutated suite stays green. Note the existing `expected = min(model.objects.count(), _RELAY_MAX_RESULTS)` cap already handles `Entry`'s much larger seeded volume, so the extension is mechanical.

Contrast with **P1**, which is the control that says this measurement means something: removing the *cascade* from `ItemType.get_queryset` at the same scope fails **11** rows, so the scope is far from inert.

### Medium:

#### M1 — the `view_<model>` branch is a dead branch: identical to the fall-through it precedes

All four hooks spell the `elif` branch and the fall-through `return` as the **same expression**, so the `elif` can never change the result:

```examples/fakeshop/apps/products/schema.py:138:143
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        elif user and user.has_perm("products.view_item"):
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

This is spec-conformant behavior (Slice 4 box 1 demands that *every* non-staff branch cascade, and Decision 6's consumer-recipe-divergence note is explicit that the `view_<model>` grant deliberately does not exempt a viewer), so it is **not** a correctness defect and the fix is not to change behavior. It matters for two reasons:

1. **It hides the fail-open shape the spec records happening once already, and on `EntryType` it hides it completely.** Because all three non-staff paths are identical, a regression in the user read — the `getattr(info.context, "user", None)` form the `## User-facing API` note warns about — is observable *only* through the staff branch. The `view_<model>` live tests (`::test_cascade_view_item_user_respects_category_visibility`, `::test_cascade_view_entry_user_nested_selection_drops_hidden_targets`) keep passing with the user bound to `None` for every request, because the anonymous path they fall into produces the identical queryset. Proof P2 measured this and found the staff branch is not covering for them either on `EntryType`: **0 of 125 rows fail**. That measurement is finding **H1**; M1 is why H1 has no second line of defence.
2. **32 lines across four hooks carry one three-line policy.** The `elif` adds a `has_perm` database read per request per type (four permission-table lookups on a query touching all four types) for a branch whose result is already the fall-through's.

Recommended change (maintainer's call — it is a fakeshop *demonstration* surface and the branch may exist to show the shape a consumer would write): either collapse each hook to `if staff -> queryset; return apply_cascade_permissions(...)`, or make the `view_<model>` branch do something the fall-through does not. Test expectation if collapsed: the six cascade live tests and the 12 re-pinned tests stay green unchanged, and `::test_cascade_staff_sees_everything` — once H1's extension lands — becomes the row that distinguishes the branches for all four types. **Order matters: H1's rows should land before any M1 collapse**, so the collapse is performed against a suite that can actually detect a mistake in it.

Routed to the maintainer through `### Notes for Worker 1` with an `Escalated:` prefix — it is a contract-level question about what the demonstration surface should teach, not a worker's call, and this cohort writes no source in any case.

#### M2 — 18 rotted card-id occurrences in `examples/fakeshop/apps/products/schema.py` are unowned, and the spec quotes them

Census G-iii. `TODO-BETA-046-0.1.1` ×7, `TODO-BETA-047-0.1.2` ×5, `TODO-BETA-049-0.1.3` ×6 — every one naming a number that today belongs to a shipped `DONE-*-0.0.14` card with an unrelated subject (`KANBAN.md`:1840, :1743, :1554), while the live referents are `TODO-BETA-055-0.1.1` / `-056-0.1.2` / `-058-0.1.3`.

Why it is Medium rather than Low: `KANBAN.md`:398 records that four of the spec's own card-id sites are **verbatim quotations of these products-schema markers**, and rules them class (b) "leave verbatim" precisely because the source still reads the old id. A spec-side correction taken without the source-side one inverts that ruling and leaves the quotation falsely attributed. The two halves have to move together or neither moves.

Recommended change: none in this cycle (this cohort writes no source and the cycle's scope excludes board edits). Route to the maintainer as a new item for whichever card next legitimately opens `examples/fakeshop/apps/products/schema.py`, alongside the already-homed `types/definition.py`:69 site (`KANBAN.md`:250) so the two land in one pass.

### Low:

#### L1 — `services.py::seed_cascade_split` has no per-app test

`examples/fakeshop/apps/products/tests/test_services.py` covers every other public helper in the module (`seed_data` ×3, `create_users` ×2, `delete_users` ×3, `delete_data` ×4, `discover_providers` ×4, `_is_safe_generator` ×3, `_fake_value` ×1) and none for `seed_cascade_split`. The helper is exercised indirectly by the six live cascade tests, and example apps sit outside the `fail_under = 100` gate, so this is not a coverage gap — it is an asymmetry in the app's own test surface, which `AGENTS.md` rule 7 says exists so "deleting an app loses only its tests".

Recommended change: a per-app test asserting the eight returned rows and their `is_private` split. Not this cycle's work.

#### L2 — the four hooks inline `request_from_info`'s path rather than calling it

`django_strawberry_framework/utils/permissions.py::request_from_info` is the package's canonical request resolution, and the `## User-facing API` note names it as the path the hooks take. The hooks instead spell `getattr(getattr(info.context, "request", None), "user", None)` inline, four times.

This is correct and deliberate: `request_from_info` is not in `__all__`, and the spec's canonical consumer surface (the cookbook line at `## User-facing API`, reproduced verbatim in `docs/GLOSSARY.md`:274-280 and `GOAL.md`:116/:141) is exactly the inline form — a consumer example must not import a private helper. Recorded only so the spec sentence "the same path `utils/permissions.py::request_from_info` and the shipped `FilterSet` / `OrderSet` gates take" is read as *the same path*, not *the same call*. No change recommended.

#### L3 — `services.py::create_users`'s docstring still says "superuser"

`#"Also creates one ``staff_<n>`` superuser per unit for convenience."` while the code sets `is_staff=True` with no `is_superuser`. The spec's `### Slice 4` fixture note already calls this out as inaccurate, so the spec is right and the docstring is wrong. Not a `034` regression (the docstring predates the card) and outside this cycle's edit scope.

### DRY findings

- **Four near-identical `get_queryset` bodies.** `examples/fakeshop/apps/products/schema.py::CategoryType.get_queryset` / `::ItemType.get_queryset` / `::PropertyType.get_queryset` / `::EntryType.get_queryset` differ only in the permission codename string (`products.view_category` / `_item` / `_property` / `_entry`) and their docstrings. `scripts/review_inspect.py` reports 8 `getattr()` calls across the four (2 each) and 4 `get_queryset` Django/ORM markers. **Deliberately not flagged as a consolidation target**: the spec's Goal 7 is "Keep composable rules visible from the owning type ... reading a type's class body shows its entire row-visibility story", and a shared `_visibility(cls, queryset, info, codename)` helper would defeat exactly the property the fakeshop schema exists to demonstrate. The `elif`-equals-fall-through duplication *inside* each body is a different question and is finding M1.
- **The existence challenge, `DjangoTypeDefinition.fields_class`.** A slot with zero readers and zero writers is the shape `worker-3.md` `### The existence challenge` names. It survives the challenge on the spec's own recorded reasoning (Decision 2: the structural mirror of `filterset_class` / `orderset_class`, so the `0.1.1` binding has a stable home) and on evidence: `KANBAN.md`:643 records the slot as realized by `DONE-034-0.0.10` and names `TODO-BETA-055-0.1.1`'s `_bind_fieldsets` as its populator, so the reader is scheduled, not hypothetical. **Not escalated** — the question is answered on the record, and re-raising an answered existence challenge is the rubber stamp `worker-3.md` warns against.
- **Repeated string literals** (`scripts/review_inspect.py`, `examples__fakeshop__apps__products__schema.overview.md`): `description` ×4, `is_private` ×4, `created_date` ×4, `updated_date` ×4, `category` ×2 — all inside the four `Meta.fields` tuples. Declarative per-type field selection; each type must name its own set and a shared constant would make the four schemas indistinguishable in the SDL. No finding.
- **`definition.py` repeated literals**: `GraphQL type name for` ×3, `resolve_id` ×2, `__func__` ×2 — none inside or adjacent to the `fields_class` slot; all belong to `related_target_for` / `_resolves_id_off_pk`, which are `spec-031`/`spec-011` surface and outside this cohort. No finding.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** at `HEAD`: `__all__` and the re-export list are unchanged by this cohort (which writes no source). Both `034`-owned exports are present and correct — `django_strawberry_framework/__init__.py`:35-36 (imports) and :157-158 (`__all__` members), matching Decision 4 and DoD 5. No new public export is introduced by this pass.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify `CHANGELOG.md`. (`CHANGELOG.md` is audited read-only under `### Documentation / release sanity` below as part of the `## Doc updates` census.)

### Documentation / release sanity

**This cycle edits none of `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `TODAY.md`, `README.md`, `CHANGELOG.md`, `KANBAN.md`, or `KANBAN.html`.** They are audited read-only, per the build plan's `## Maintainer-set scope for this cycle`. Two of them (`KANBAN.md`, `README.md`) are additionally on the plan's baseline-dirty list and were neither edited nor reverted.

Result of the `## Doc updates` audit (full rows in census E):

- **Landed, verified:** GLOSSARY status flip + body rewrite + "FK / M2M" scope correction + `Per-field permission hooks` re-status + `get_queryset` cross-reference + index rows + exports list (E1-E5); `docs/README.md` shipped-surface bullet (E6); `docs/TREE.md` `permissions.py` description and `tests/test_permissions.py` row (E8, E9); `TODAY.md` live-hook rewrite and the stale-card-id drop (E10, E11); `README.md` status line (E12); `CHANGELOG.md` bullets (E13); `KANBAN.md` card at Done with a resolving spec reference (E14); `GOAL.md`'s three ratified user-read corrections (E16).
- **Not re-derivable / superseded:** `docs/README.md`'s "Coming next `0.0.10` line shrinks to the `035` remainder" (E7) — rewritten by four later cuts; not a `034` gap.
- **Not established by this cohort:** the `KANBAN.md` M2M/reverse follow-up surfacing (E15).
- **Version strings and card IDs:** `django_strawberry_framework/__init__.py::__version__` and `tests/base/test_init.py::test_version` both read `0.0.14`; `pyproject.toml` carries no second literal (`dynamic = ["version"]` + `[tool.hatch.version]`), consistent with `AGENTS.md` rule 31. Decision 13's card-scoped claims hold (census D). The card id in `KANBAN.md`:113 is `DONE-034-0.0.10` and matches the spec's `Status:` line.
- **Markdown links:** every reference-style definition in the spec resolves post-archive (the archive sweep re-pointed them); the rot is confined to **4 literal in-prose path spellings** of `docs/spec-034-permissions-0_0_10.md` (census F), one of which is an executable command that exits 2.
- **Script-rendered docs:** `docs/TREE.md` is rendered from module docstrings and carries no staging language for `permissions.py` (`grep -c 'TODO-ALPHA-034' docs/TREE.md` -> 0), so no docstring scrub is owed. `docs/GLOSSARY.md` and `KANBAN.md` are DB-generated and were not touched.

### What looks solid

- **The activation itself.** All four hooks live, the import live, the `TODO-ALPHA-034-0.0.10` staging markers fully discharged (0 occurrences), and the user read corrected at every one of the four sites to the `info.context.request.user` form the spec's `## User-facing API` note requires. The one thing this cohort was told to suspect — that the hooks "remain comments" — is false about the code and true only of the spec sentence.
- **The Slice 4 live census is complete at the file level.** All six spec-named tests exist under their spec names, in the spec-named file, each with `create_users(1)` as its literal first statement, and all six pass at `HEAD` (`uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov -q -p no:randomly` -> `6 passed in 5.45s`). No named test is absent and none was renamed. The one gap is *inside* a present test rather than a missing one — `::test_cascade_staff_sees_everything` covers two of the four root fields (finding H1), which reading alone would not have caught and the failability proof did.
- **`test_cascade_query_count_fixed` pins the load-bearing property, not observability.** It asserts an **absolute** count (`len(captured) == 3`), asserts `"IN (SELECT"` appears in the composed SQL so the row cannot pass on a fall-through that skipped the cascade, and asserts the *absence* of a products-table JOIN so it cannot pass on a `select_related` that never downgraded. That is three independent failure modes closed on one row — the shape `BUILD.md` `### Query-shape tests must pin the load-bearing property` asks for.
- **The Slice 4 re-pins are real and self-documenting.** 14 test functions across the two files carry an explicit "activated cascade (spec-034)" note in their docstring explaining *why* the expectation is now ORM-derived or staff-clienced, so the next reader can tell a re-pin from an original pin. `examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations` re-derives both the forward-FK and reverse-FK expectations from post-cascade ORM queries rather than hard-coding counts.
- **Decision 2's forward-reserved slot is genuinely inert.** Five occurrences of `fields_class` in the whole package, and not one of them is an assignment, a read, or a binding. The deferral is enforced by a live gate (`DEFERRED_META_KEYS` + `tests/types/test_base.py`:415), not by convention.
- **The `## Doc updates` section shipped essentially whole** — 14 of 16 claimed edits verified landed, the two exceptions being a superseded roadmap line and one board-surfacing claim outside this cohort's reach.
- **`seed_cascade_split` is the right shape.** A named services helper returning the eight key rows by identity, so the live tests assert against `chain["entry_under_private"].value` rather than against counts — the assertions survive any change to `seed_data`'s row volume.

### Failability proofs (Worker 3 independent runs)

`BUILD.md` `### Who performs it` assigns proof authorship to Worker 2 and auditing plus an independent subset re-run to Worker 3. **This cohort has no Worker 2 record to audit** — R1 lands no source, so the diff introduces no boundary and `worker-3.md`'s mandatory re-run floor ("re-run every boundary whose recorded failing-row count is 3 or fewer, and every boundary on a security or data-isolation decision") is computed over an empty set and is legally empty.

Two proofs were nevertheless run, because the cohort brief directs the audit at a **data-isolation** surface and at the fail-open shape the spec records happening once already, and because a conformance audit that only reads cannot tell whether a passing live suite could have failed. Both are recorded here **before** the mutation per `worker-3.md`, executed through `scripts/prove_failability.py` (which enforces the anchor-check-first ordering, the outside-the-repo scratch root, the pre-mutation baseline, and the byte-comparison restore), and reverted inside this pass.

- **P1 — `examples/fakeshop/apps/products/schema.py::ItemType.get_queryset`** (data-isolation boundary): remove the cascade from both non-staff branches, i.e. replace each `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` with `return queryset.filter(is_private=False)`, leaving the `is_private` narrowing but deleting the cross-type cascade. Anchored on the unique `products.view_item` block so exactly one hook is mutated.
- **P2 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`** (the fail-open shape `BUILD.md` `### Fail-open shapes` catalogues and the `## User-facing API` note names by hand): replace the user read `user = getattr(getattr(info.context, "request", None), "user", None)` with the broken `user = getattr(info.context, "user", None)`, which binds `None` against the stock `StrawberryDjangoContext` and collapses every branch to the anonymous path. Anchored on the unique `products.view_entry` block so exactly one hook is mutated.

#### Proof results

Both entries ran through `uv run python scripts/prove_failability.py docs/builder/temp-tests/034-r1c/proofs.json --output docs/builder/temp-tests/034-r1c/proofs-report.md`, scratch root **outside the repository** at `/private/tmp/claude-501/.../scratchpad/failability-034-r1c`. The anchor check ran first and standalone (`--check-anchors-only`, exit 0): both anchors matched **exactly once**, which is also the evidence that the tree carried no prior live mutation. One boundary live at a time, each restored before the next.

Scope as run, identical for both entries and for both baselines:

```
uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE \
  examples/fakeshop/test_query/test_products_api.py \
  examples/fakeshop/apps/products/tests/test_schema.py
```

**P1 — `examples/fakeshop/apps/products/schema.py::ItemType.get_queryset`** (data-isolation boundary; re-run at the cohort's own initiative, no Worker 2 record exists)

- Mutation applied: both non-staff branches' `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` replaced by `return queryset.filter(is_private=False)` — the cross-type cascade removed, the `is_private` narrowing left intact so nothing but the boundary is gone.
- Pre-mutation state of this scope: `125 passed`, pytest exit 0. Pre-existing failing rows differenced out: **0**.
- Collection / setup errors: **0**. Mutant pytest exit code: 1 (`11 failed, 114 passed`).
- Failing node ids (**11**; the count is `len()` of this list):
  - `examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations`
  - `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http`
  - `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http`
  - `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`
  - `examples/fakeshop/test_query/test_products_api.py::test_products_items_order_by_name_asc`
  - `examples/fakeshop/test_query/test_products_api.py::test_products_items_order_by_name_desc`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_view_item_user_respects_category_visibility`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_query_count_fixed`
  - `examples/fakeshop/test_query/test_products_api.py::test_visibility_scoped_update_delete_hidden_private_row_is_not_found`
  - `examples/fakeshop/test_query/test_products_api.py::test_update_item_via_form_visibility_scoped_hidden_private_row_is_not_found`
  - `examples/fakeshop/test_query/test_products_api.py::test_update_item_via_serializer_visibility_scoped_hidden_row_is_not_found`
- Verdict: **pinned**, well above the weakly-pinned threshold and above the mandatory re-run floor.
- Restore proved by byte comparison: `filecmp.cmp(shallow=False)` -> `True`; `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` against the pre-mutation copy.
- **What the node-id set also establishes, beyond the boundary itself:** six of the eleven are Slice 4 re-pinned rows (census A8), so the re-pins are load-bearing rather than cosmetic — they would fail if the cascade were withdrawn. Three more are `0.0.11`/`0.0.12`/`0.0.13` mutation-visibility rows, which is independent evidence that `update`/`delete` lookups route through the cascading `get_queryset` exactly as Decision 12 and the mutations cards claim.

**P2 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`** (the fail-open user read)

- Mutation applied: `user = getattr(getattr(info.context, "request", None), "user", None)` replaced by `user = getattr(info.context, "user", None)`.
- Pre-mutation state of this scope: `125 passed`, pytest exit 0. Pre-existing failing rows differenced out: **0**.
- Collection / setup errors: **0**. Mutant pytest exit code: **0** (`125 passed`) — a valid run, not a scope error.
- Failing node ids: **none** (0 rows).
- **why 0: weakly pinned.** Not a harness-impossible interleaving — the harness already logs in a staff client in `::test_cascade_staff_sees_everything` and could exhibit the failure with one more root field in its loop. Full reasoning and the remedy are finding **H1**.
- Restore proved by byte comparison: `filecmp.cmp(shallow=False)` -> `True`; `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` against the pre-mutation copy.

**Tree state after both proofs**, verified independently of the tool: `git diff --stat -- examples/fakeshop/apps/products/schema.py` is empty and `git status --short examples/fakeshop/apps/products/schema.py` reports nothing, so the file is byte-identical to `HEAD`. The scratch root holds only `pristine/` — **no `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json`**. `git checkout` / `git restore` / `git stash` were never invoked.

**Where the second pair of eyes landed.** Both boundaries above were run by this cohort. No boundary was accepted on a Worker 2 record, because none exists — R1 lands no source.

### Temp test verification

- No temp test was written. Every suspicion this cohort carried about *presence* was decidable by grep plus a focused read; the one that was not — whether the live rows can fail — was settled by mutating the shipped code under `scripts/prove_failability.py` rather than by adding a file, which is the stronger instrument here: a new temp test proves only that a new assertion passes, whereas the mutation proves what the *existing* assertions cannot see.
- Files used: `docs/builder/temp-tests/034-r1c/proofs.json` (the proof manifest) and `docs/builder/temp-tests/034-r1c/proofs-report.md` (the tool's emitted record, transcribed into `#### Proof results` above).
- Disposition: both are per-cycle scratch under the gitignored `docs/builder/temp-tests/`, cleared by `scripts/clean_up.py`. **Nothing to promote as a temp test** — but the gap the proof exposed is not scratch: it is finding **H1**, and its remedy is a permanent-suite change to `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything`, recorded for R3 rather than left as a proof artifact (`worker-3.md` `## Temp test rules`: do not leave a temp instrument as the only record of shipped behavior).

Mechanical runs performed by this pass (all read-only, none with a `--cov*` flag):

- `uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov -q -p no:randomly` -> `6 passed in 5.45s`.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` -> `error: missing file`, exit 2 (census F2).
- `uv run python scripts/review_inspect.py django_strawberry_framework/types/definition.py --output-dir docs/shadow` and the same for `examples/fakeshop/apps/products/schema.py` — both wrote their `.overview.md` / `.stripped.py` pair; findings walked under `### DRY findings` and census C6.
- `scripts/prove_failability.py` runs recorded under `#### Proof results`.

### Static helper use

Run as `BUILD.md` `### When to run the helper during build` requires (a file under `types/`, plus the file this cohort reads hardest):

- `docs/shadow/django_strawberry_framework__types__definition.overview.md` — **Django/ORM markers** (7): `OptimizerHint` import, the `DjangoTypeDefinition` class line, `field_map`, `optimizer_hints`, `has_custom_get_queryset`, the `related_target_for` return annotation, and `self.model._meta.get_field(field_name)` at :309. None is a `fields_class` reader; all belong to shipped surface outside this cohort. **Control-flow hotspots** (2): `related_target_for` (:264, 85 lines / 19 branch nodes) and `_resolves_id_off_pk` (:407, 31 lines / 8 branch nodes) — both `spec-031`/`spec-011` surface, neither touching the Decision 2 slot; recorded, no finding. **Repeated literals** (3) and **Imports** (15, all standard / django / strawberry / same-package relative, no cross-folder import out of `types/`): no finding.
- `docs/shadow/examples__fakeshop__apps__products__schema.overview.md` — **Django/ORM markers** (9): four `class <X>Type(DjangoType)` declarations, four `def get_queryset(cls, queryset, info)` definitions, and the `DjangoType` import. Each is exactly the surface Slice 4 activates; justified, no finding. **Control-flow hotspots: 0** — the four hooks are three-branch bodies below the helper's threshold, which is itself the signal behind finding M1 (a branch that cannot change the answer does not register as complexity). **Calls of interest**: 8 `getattr()`, two per hook at :97, :138, :175, :213 — the doubled `getattr` is the `info.context.request.user` chain, i.e. census A7's evidence, not a fail-open default (the *absence* of the request is meant to bind `None` and route to the anonymous path). **Repeated string literals** (5) and **Imports** (4): walked under `### DRY findings`, no finding.
- No skip taken. Shadow files are read-only scratch; no line number from them is cited anywhere in this artifact.

### Notes for Worker 1 (spec reconciliation)

**Behaviour / description findings — sentences R2 must rewrite.** Each gives the sentence, what is true at `HEAD`, and the attribution R2 needs for the rationale's `**Post-ship:**` bullet.

- `docs/SPECS/spec-034-permissions-0_0_10.md`:83 — "The four products-schema hooks that call it remain comments (Slice 4's uncomment)." **True at `HEAD`:** all four are live classmethods (`examples/fakeshop/apps/products/schema.py::CategoryType.get_queryset` / `::ItemType.get_queryset` / `::PropertyType.get_queryset` / `::EntryType.get_queryset`). **Attribution:** Slice 4 of this card; no post-ship work involved — the sentence was already falsified by the build that the same file's `Status:` line records as complete. This is the prediction class in `BUILD.md` `### `## Current state`: observations stand, predictions do not`, so it is rewritten, not dated.
- `docs/SPECS/spec-034-permissions-0_0_10.md`:89 — "**The fakeshop activation site is staged.** ... carries a commented `apply_cascade_permissions` import and four commented `get_queryset` cascade hooks — one per type, each behind a `TODO-ALPHA-034-0.0.10` marker". **True at `HEAD`:** the import is live at :55, the four hooks are live, and `TODO-ALPHA-034` has 0 occurrences in the file. **Attribution:** same as above. **Keep** the bullet's parenthetical about the user-read correction (census H5) — it is the only record of *why* the activation was not a pure uncomment, and it is still true.
- `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`:312 — "`Item` / `Entry` `is_private` a per-row `random.choice([True, False])`". **True at `HEAD`:** `examples/fakeshop/apps/products/services.py::seed_data` draws both from `privacy = random.Random(PRIVACY_STREAM_SEED)`, a fixed-seed stream. **Attribution:** the superseding change names itself in the source — `services.py #"Item/Entry privacy is drawn from this fixed-seed stream rather than the process"` / `#"an unseeded draw makes every derived expectation probabilistic, and a run"` — a later determinism hardening of the seeder, post-`034`.
- `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`:312 — "seeded the deterministic private/public chains the new cascade tests need through a **module-local helper**". **True at `HEAD`:** the helper is `examples/fakeshop/apps/products/services.py::seed_cascade_split`, a services-module helper imported by the test file, not module-local to it. **Attribution:** either the fixture moved into `services.py` post-ship, or the rationale sentence was wrong when written; either way `AGENTS.md` rule 8's "seed-helper tests are the only exception" carve-out and rule 7's per-app placement both favour the current home, so the spec text is what changes.
- `docs/SPECS/spec-034-permissions-0_0_10.md`:425 — "Existing products live assertions are audited for private-fixture sensitivity; any that assumed un-cascaded visibility are re-pinned in the same change (**expected small** — the suite seeds public fixtures by default)." **True at `HEAD`:** the parenthetical is falsified by the rationale's own resolution ("the seeders are *not* public-only ... the re-pin was load-bearing, not minimal") and by 14 re-pin-marked test functions. **Attribution:** Slice 4's own build; the correction already exists in the rationale and only the spec's `### Slice 4` bullet still carries the wrong expectation.
- `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`:312 — "it re-pinned each at-risk assertion (**12** across `test_products_api.py` and the in-process `test_schema.py`)". **Re-derivation at `HEAD`:** searching the shortest distinctive tokens (`activated cascade`, `post-cascade`, `spec-034`) and attributing each hit to its enclosing `def test_`, `examples/fakeshop/test_query/test_products_api.py` alone carries **12** re-pin-marked test functions (excluding the six new cascade tests), and `examples/fakeshop/apps/products/tests/test_schema.py` carries **2** more — 14 across the two files the sentence names. The figure matches only if its subject is `test_products_api.py` alone. **This is a count right in its digits and wrong in its subject** — the R2 fix is to state the enumeration or drop the number, not to change 12 to 14 (later cards may have added marked sites, and the original population was assertions rather than test functions, which is a third number nobody has measured).
- `docs/SPECS/spec-034-permissions-0_0_10.md`:190 (Decision 1) — "The spec file lives at **`docs/spec-034-permissions-0_0_10.md`**". **True at `HEAD`:** `docs/SPECS/spec-034-permissions-0_0_10.md`. **Attribution:** the `docs/SPECS/NEXT.md` Step 8 archive sweep that moved every prior spec; the sweep re-pointed reference-style link definitions but not literal in-prose path spellings.
- `docs/SPECS/spec-034-permissions-0_0_10.md`:464 (DoD 1) — the command `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md`. **True at `HEAD`:** exits **2** with `error: missing file`; the archived path is green at `OK: 42 terms`. **This is the single executably-false claim in this cohort's territory** and the highest-priority R2 repair here. Same attribution as Decision 1.
- `docs/SPECS/spec-034-permissions-0_0_10.md`:441 (`## Doc updates`) — "confirm the spec reference points at `docs/spec-034-permissions-0_0_10.md`". **True at `HEAD`:** `KANBAN.md`:113 points at `docs/SPECS/spec-034-permissions-0_0_10.md` and is correct; the spec's instruction names the pre-archive path. Same attribution.
- `docs/SPECS/spec-034-permissions-0_0_10.md`:3 — "the on-disk version reads `0.0.9` as of this writing". **True at `HEAD`:** `0.0.14`. **R2 judgement, not a finding:** the clause is explicitly self-dating ("as of this writing") and sits in the spec's identity paragraph rather than in `## Current state`. Flagged only so R2 decides deliberately whether a self-dating clause outside the vintage-framed section keeps its licence.

**Card-id rot — separate remedy, kept apart from the behaviour findings above.**

- `docs/SPECS/spec-034-permissions-0_0_10.md`:203 (Decision 2) — `_bind_fieldsets` lands with `TODO-BETA-046-0.1.1`. **Live name:** `TODO-BETA-055-0.1.1` (`KANBAN.md`:596; spec on disk at `docs/SPECS/spec-055-fieldset-0_1_1.md`). **Already homed** — `KANBAN.md`:367 and :398 carry the four-citation `spec-034` clause (3 live-claim repoints + 1 revision-log decided-non-edit) and explicitly say "do not re-raise them". Recorded here for completeness, not as new work.
- `docs/SPECS/spec-034-permissions-0_0_10.md`:319 (Decision 13) — `TODO-ALPHA-035-0.0.10`, while the same file's opener spells `DONE-035-0.0.10` twice. **Already homed** — `KANBAN.md`:398 names this exact site as `spec-034`'s single clean prefix-flip.
- `docs/SPECS/spec-034-permissions-0_0_10.md` — `TODO-ALPHA-034-0.0.10` ×6 (:42, :64, :89, :435, :441, :485). `KANBAN.md`:398's grading applies per site: :42 and :435 quote `docs/TREE.md`'s superseded predicted-path row (class (b), leave verbatim), :441 is a card-wrap slice instruction true only in its own tense (class (a), de-tense), and :64 / :89 / :485 are live-claim sites. Note that :89's fix is the H4 rewrite above, so the two remedies collide on one sentence — do them together.
- **NEW, unowned: `examples/fakeshop/apps/products/schema.py` carries 18 rotted card-id occurrences** — `TODO-BETA-046-0.1.1` ×7, `TODO-BETA-047-0.1.2` ×5, `TODO-BETA-049-0.1.3` ×6 — plus one **correct** `TODO-BETA-062-0.1.5` that must not be swept. Live referents: `TODO-BETA-055-0.1.1`, `TODO-BETA-056-0.1.2`, `TODO-BETA-058-0.1.3`. `KANBAN.md`:250 homes the sibling `django_strawberry_framework/types/definition.py`:69 site but nothing homes the products-schema 18, and `KANBAN.md`:398 rules four spec sites "leave verbatim" *because* the source still reads the old id — so the spec-side and source-side halves are coupled. **Escalated:** this cycle writes no source and edits no board, so the resolution paths are (a) fold both halves into whichever card next legitimately opens `examples/fakeshop/apps/products/schema.py`, or (b) let the FieldSet / search / aggregates cards each retarget their own citations as they land. Finding M2.
- **A citation Slice 0's own move broke.** `KANBAN.md`:398 cites the bare-numeral falsehood as `docs/SPECS/spec-034-permissions-0_0_10.md #"but the live kanban card is"`. Slice 0 moved that sentence into the rationale companion; it now lives at `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`:72 and the board's citation is dangling. Nothing in this cycle may edit `KANBAN.md`; recorded for the maintainer.

**The one SKIPPED contract — routes to R3, not R2.**

- `docs/SPECS/spec-034-permissions-0_0_10.md`:65 (Slice 4 box 2) and :485 (DoD 10) state the live matrix as "anonymous / per-`view_<model>` / **staff**" across the 2-deep `Entry → Item → Category` / `Entry → Property → Category` chain. **True at `HEAD`:** the staff half of that matrix is asserted for `allCategories` and `allItems` only; `EntryType`'s and `PropertyType`'s staff branches are exercised by no row anywhere. **This is a code (test) gap, not a spec defect** — the spec states the right contract and the suite does not pin it, so it routes to `docs/builder/bld-034-review-3-code_repair.md` rather than to the reconciliation pass. **Proven, not inferred:** proof P2 removed `EntryType.get_queryset`'s staff branch and 0 of 125 rows failed, against a green baseline with 0 collection errors; the control (P1) fails 11 rows at the same scope. Finding **H1** carries the remedy and the test expectation. This is the artifact that makes R3 conditional-no-longer: the build plan's `## Artifact list` says `bld-034-review-3-code_repair.md` is "created only if R1 confirms a contract the spec states, the maintainer has not superseded, and the code does not implement" — R1c confirms one.

**Escalated (Medium, needs contract context this cohort cannot supply):**

- **Escalated: M1, the dead `view_<model>` branch.** All four hooks spell the `elif user and user.has_perm("products.view_<model>")` branch and the fall-through identically, so the `elif` cannot change the result and costs one permission-table read per request per type. It is spec-conformant (Slice 4 box 1 and Decision 6's consumer-recipe-divergence note both demand it) and proof P2 below shows it hides a fail-open regression from every non-staff live row. Resolution paths for Worker 1 / the maintainer: **(a)** keep as-is and record in the spec *why* the redundant branch exists (it demonstrates the shape a consumer would write, and the Decision 6 divergence is easier to read with the branch present); **(b)** collapse each hook to `if staff -> queryset; return apply_cascade_permissions(...)` and add a spec sentence saying the `view_<model>` grant is deliberately not a branch; **(c)** give the `view_<model>` branch different behavior, which would reverse Decision 6's recorded divergence and is therefore a maintainer decision, not a worker's. This cohort writes no source in any case.
- **Escalated: M2**, above.

**Out of this cohort's territory, one bullet each (recorded, not audited):**

- `docs/GLOSSARY.md`'s `apply_cascade_permissions` entry at `HEAD` describes a materially different cascade contract from the one the spec states — cycles raise a path-rich `ConfigurationError` rather than partial-narrowing, identity-hook targets compose rather than being skipped, MTI `<parent>_ptr` edges cascade rather than being excluded, `GenericForeignKey` fails a full walk closed, the `__isnull` disjunct is conditional on nullability, and hook returns run a validation/normalization pass. This is R1a's territory (the build plan's "Known-live divergence class") and is flagged only to confirm the glossary is the surface carrying the newer contract; the census graded the *Slice 5 edit* as landed (E1-E5), not the current body as spec-conformant.
- `docs/SPECS/spec-034-permissions-0_0_10.md` Decision 12 and the Sharded-callers edge case cite `walker.py:212` / `(walker.py:212-214)` — raw `path:NN` in a standing doc, which `AGENTS.md` rule 27 permits only in per-cycle scratch. R1b's territory.
- The spec's `### Slice 1` multi-DB harness note cites `examples/fakeshop/config/settings.py` "line ~116" — same rule-27 shape. R1a's territory.

### Review outcome

`review-accepted`. The audit is complete and its findings are recorded: every contract in R1c's territory is graded, the one SKIPPED row is named and its negative proven mechanically rather than asserted, and the two Medium findings are escalated with resolution paths.

`revision-needed` is deliberately **not** set, and the reasoning is worth stating because H1 is a High finding on a data-isolation boundary measured at 0 rows — normally the textbook `revision-needed` trigger (`BUILD.md` `### Acceptance rule: weakly pinned is revision-needed`). Three things distinguish this case:

1. **That acceptance rule binds a boundary the pass under review introduced.** It is the gate Worker 3 applies to Worker 2's diff, and the transition it drives is "Worker 0 re-spawns Worker 2". This cohort has no Worker 2 and no diff (R1 is read-only by the build plan's own partition), so there is no pass to send back and nothing a re-pass could change.
2. **The cohort brief scopes the flag explicitly:** set `revision-needed` "only if you find something that blocks the audit itself from being trustworthy". H1 does not block the audit — H1 *is* the audit's principal result, and the measurement that produced it is recorded in full with its control, its baseline, its zero error count and its byte-compared restore.
3. **The repair has a declared home.** The build plan routes a confirmed SKIPPED contract to `docs/builder/bld-034-review-3-code_repair.md`, whose conditional creation this finding now triggers. Holding R1c open would delay that dispatch rather than accelerate it.

Worker 1 owns the disposition of every finding here at the R2 reconciliation pass and the now-unconditional R3 repair pass.

---

## Final verification (Worker 1)

Performed by the R2 spec-reconciliation pass (`docs/builder/bld-034-review-2-spec_reconciliation.md`). Appended only; nothing this cohort wrote was altered.

**The census is sound.** The 59 rows re-derive two independent ways — by bucket (47 + 1 + 2 + 5 + 2 + 1 + 1) and by section size (A 11, B 12, C 8, D 6, E 16, F 3, I 3) — and the nine `## Current state` clauses are correctly counted separately, on `docs/builder/BUILD.md`'s observation-versus-prediction axis rather than folded into the five grading buckets. That separation is what makes the H3 / H4 findings actionable: seven clauses stand because the header dates them, two are predictions about the build's own outcome, which nothing dates. This cohort's `revision-needed` reasoning is accepted as written — the weakly-pinned acceptance rule binds a boundary the pass under review *introduced*, and R1 introduces none, so there was no pass to send back.

**The one SKIPPED contract is confirmed and correctly routed.** Finding **B4a** / **H1** — the live staff matrix loops `allCategories` and `allItems` only, so `EntryType`'s and `PropertyType`'s staff branches are pinned by nothing — needs **no spec edit**: the spec already states the four-root matrix correctly in `## Slice checklist` Slice 4 box 2 and `## Definition of done` item 10, so R3 makes the code match the spec rather than the other way round. Both those sites were read in R2 and deliberately left unchanged. The negative was proven rather than assumed (proof P2: 0 of 125 rows fail against a green baseline with 0 collection errors, restore byte-compared), and the control that makes the zero mean something (P1: 11 rows at the same scope) is what distinguishes it from a dead scope. R1c's ordering constraint is carried into the deferred-work catalog: **H1's rows should land before any M1 collapse**, so the collapse is performed against a suite that can detect a mistake in it.

**Discharged in the spec by R2 — 8.** H3 and H4 (both falsified predictions, rewritten to the live shape — H5's user-read parenthetical kept, since it is the only record of why the activation was not a pure uncomment, and the escalated `TODO-ALPHA-034-0.0.10` spelling preserved by naming the marker as one the file does *not* carry, which is a present-tense observation). B11 (the "expected small" re-pin parenthetical, falsified by the rationale's own resolution text). F1, F2 and F3 (the pre-archive path in Decision 1, DoD item 1 twice, and the `## Doc updates` card-wrap instruction — **DoD item 1's command now exits 0 where it exited 2**, the only executably-false claim in this territory). D6 (the opener's self-dating `0.0.9` clause, which R1c flagged as a judgement call rather than a finding: judged and removed, because the version-boundary sentence it supported is complete without it and it sat in the identity paragraph rather than in the vintage-framed section). B10 and A11 went to the rationale companion, where the sentences live — the "module-local helper" claim, which contradicted the same file's own Revision 8, and the `random.choice` description, superseded by a fixed-seed stream that names itself in the source.

**The re-pin count.** R1c's diagnosis — right in its digits, wrong in its subject — is confirmed and its recommendation followed. Re-derivation at `HEAD` with a three-token grammar returns **13** in `test_products_api.py` and **2** in `test_schema.py`, against R1c's 12 and 2, and the sentence's *original* subject was at-risk assertions rather than test functions. Three numbers for one population is the argument for stating the population, which is what the rationale now does; the fix was not `12` → `14`.

**Routed to the deferred-work catalog, not fixed — 4.** M1 (the dead `view_<model>` branch, contract-level and escalated with three resolution paths). M2 (the 18 rotted card ids in `examples/fakeshop/apps/products/schema.py`, coupled to four spec sites `KANBAN.md`:398 rules "leave verbatim" *because the source still reads the old id*). L1 (`seed_cascade_split` has no per-app test). E15 (the board's M2M/reverse follow-up surfacing, unreachable from this cycle). **C5 and D3** — the `TODO-BETA-046-0.1.1` and `TODO-ALPHA-035-0.0.10` sites — are frozen by the same escalation; every card-id spelling in the spec survives R2 byte-identical, verified against R1c's own census.

**The citation this cohort found that Slice 0 broke is confirmed and widened.** R1c reported `KANBAN.md`:398 citing `#"but the live kanban card is"` against the spec, where that sentence no longer lives. R2's before-and-after foreign-citation sweep found **two more** of the same class from the same board item — `#"Stale card-id reference in `TODAY.md`"` and `#"so `<NNN>` is"` — both likewise carried into the rationale companion by Slice 0's move. All three are catalogued together; none is repairable here.

**Finding L2 verified and rejected as R1c recommended.** The hooks inline `request_from_info`'s path rather than calling it, deliberately: a consumer example must not import a private helper, and the spec sentence says the same *path*, not the same *call*. No spec edit; recorded so it is not re-raised.

Status set to `final-accepted`.
