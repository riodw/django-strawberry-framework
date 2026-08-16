# Build: Item R2 — documentation completion and archive audit

Spec reference: `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` (whole file, 53 lines) and
`docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` (whole file, 344 lines)
Plan reference: `docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md` `### R2 findings` (F9-F11)
Predecessor artifact: `docs/builder/bld-011-r1-rationale_and_spec_reconciliation.md` (`final-accepted`)
Status: final-accepted

A **combined plan + build + final-verification pass performed by Worker 1 alone**, authorized by the
plan's `## Dispatch record` row for R2: the findings live inside the spec and its companions, and no
source or test is in the writable set. The row's escape hatch — "unless it turns up a durable-doc or
DB edit" — **fired**: this pass found two DB-backed defects in the `DONE-011-0.0.4` card body and
reports them rather than editing, per `docs/builder/BUILD.md` `### Generated docs are DB-backed: edit
the DB, then regenerate`. See `### Generated-doc edits reported, not made`.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the code sense: this item adds no Python and no
  test, so `worker-1.md` `### Package-wide helper inventory before helper planning` has no candidate
  surface. The documentary equivalent was run instead — R1's closed artifact was read in full as the
  contract it hands forward, together with both files it wrote and the terms CSV, before any check
  was designed.
- **Existing patterns reused.** The audit reuses the measurement discipline R1 established rather
  than a new one: every count is a count of **occurrences of the shortest distinctive token**, not of
  matching lines (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`), and every
  path is disk-checked from the **writing file's own directory** rather than from the repository
  root.
- **Duplication risk avoided.** The F11 write-up names surfaces and quantifies the cluster; it does
  **not** restate the renumber history R1 already recorded in the rationale's `## Scope` 2 entry, nor
  re-argue the `[backlog]` deferral R1 decided. Both are cross-referenced.
- **New shared shape justified.** None. The deliverable is this artifact.

### Implementation steps

1. Disk-check every link definition in both files, resolved from the file's own directory, and
   re-derive the masked-rot exposure independently of R1's claim to have done so.
2. Verify the link scaffold mechanically: all ten canonical group headers, in order, alphabetical
   within group, in both files; and measure which definitions are unused.
3. Run `check_spec_glossary.py` and the scaffold/ASCII checker on both files.
4. Verify the terms CSV against `import_spec_terms`'s **actual** enforced constraints, read from
   `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`, and confirm the DB
   already agrees — from a **copy** of the database in the session scratchpad, read-only.
5. Audit the durable docs named in the dispatch (`docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`,
   `CHANGELOG.md`) against what card 011 actually shipped.
6. Establish F11's true extent by measurement across the whole tree, classify every occurrence by
   which spec it means, and write it up for the deferred-work catalog.
7. Carry R1's deferred items forward so `bld-011-final.md` assembles the catalog in one read.

### Test additions / updates

None, and none is possible: this item lands no code. The read-only evidence below is verification of
documentary claims, not test coverage.

### Implementation discretion items

- Whether the rationale's two unused link definitions are removed here or catalogued. Decided at
  audit time: **catalogued**, on the measurement in `### F8 widened` — they are two instances of a
  71-definition pattern, and R1's F8 disposition plus `worker-0.md` `## Closing out a kanban card`
  both forbid partial-fixing a cross-surface pattern. Recorded as a decided answer rather than left
  silent.

### Dispatched findings checklist

- [x] **F9** — the archive move is done; what R2 owes is the audit and the new companion's own link
      hygiene. Audited; see `### 1. Archive audit`. The companion's block is correct and complete;
      its two unused definitions are dispositioned above.
- [x] **F10** — the two glossary anchors resolve and carry the right shipped versions, and
      `KANBAN.md`'s card renders both. Re-derived independently; see `### 3. Durable-doc completion`.
- [x] **F11** — the `[spec-011]` ref-id cluster. **Extent established by measurement and written up
      for the deferred-work catalog**, not fixed: the plan's five surfaces are an undercount. See
      `### 4. F11`.

---

## Final verification (Worker 1)

### 1. Archive audit of the spec and its two companions

**Every link definition resolves from the file's own directory.** Checked by `[ -e ]` after `cd` into
the defining file's directory, fragment stripped — twenty definitions across the two Markdown files,
**twenty resolve, zero missing**.

| File | Definitions | Result |
|---|---|---|
| `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` | 8 | all resolve from `docs/SPECS/` |
| `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` | 12 | all resolve from `docs/SPECS/appx/` |

**The masked-rot trap: probed, and this cluster has no instance of it.** A depth error is invisible
to an existence check when a same-named file sits at the shallower depth, so the probe is for the
*names*, not the paths. Only one name in the repository's root/`docs/` pair is duplicated —
`README.md` exists at both `./README.md` and `docs/README.md` — and **neither file links to a
`README` at all**, so the one masking pair present cannot be triggered here. The remaining
root-group names are unique: `BACKLOG.md` and `KANBAN.md` exist only at the root, `GLOSSARY.md` only
under `docs/`. Each root-group definition was then normalized to its repository-relative target and
read: `../../BACKLOG.md` and `../../KANBAN.md` from `docs/SPECS/` and `../../../…` from
`docs/SPECS/appx/` both land on the **root** files, and `../GLOSSARY.md` / `../../GLOSSARY.md` land
on `docs/GLOSSARY.md`. Intent and resolution agree in every case.

**Reference-style convention, mechanically checked.** Both files: all ten canonical group headers
present, in the exact `START.md` order (compared against the literal list, not eyeballed);
alphabetical within every group; no inline `](path)` cross-file link in either body. Subdirectory
rule respected — the companion's `docs/SPECS/appx/` definitions sit under `<!-- docs/SPECS/ -->`, no
eleventh header invented.

**In-page anchors resolve.** The companion's three anchored definitions target
`#card-snapshot` and `#scope`; the spec carries `## Card snapshot` and `## Scope`. The two glossary
fragments target `#definition-order-independence` and `#scalar-field-override-semantics`; both are
`## `-level headings in `docs/GLOSSARY.md` (lines 490 and 1785).

**Unused definitions, measured.** Spec: `[backlog]`, 0 uses — R1's F8, deliberately kept.
Companion: `[backlog]` and `[kanban]`, 0 uses each. See `### F8 widened` for the disposition and the
population this belongs to.

**Checker runs.**

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`
  -> `OK: 2 terms - all have glossary entries and at least one spec link.` **exit 0**
- `uv run python scripts/check_trailing_commas.py --check <spec> <companion>` -> **exit 0** (link-def
  scaffold in canonical order, ASCII rules)

### 2. Terms-CSV importability

`docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-terms.csv`, three lines: the header
`term,anchor,notes` and two rows.

| term | anchor |
|---|---|
| `definition-order` | `definition-order-independence` |
| `scalar-field` | `scalar-field-override-semantics` |

The constraints were read from
`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::Command._load_rows` rather
than assumed, and each is checked:

- **Anchor-uniqueness** (`raise CommandError(f"Duplicate glossary anchor …")`) — two rows, two
  distinct anchors. This is the constraint a green `check_spec_glossary` cannot see, because that
  script validates the *link* side and ignores duplicate `term` spellings.
- **Header keys** — `DictReader` reads `term`, `anchor`, `notes`; all three present, no blank
  `term`/`anchor` (a blank row is skipped, and skipping both would trip `No terms loaded`).
- **Every anchor exists as a `GlossaryTerm`** (`Missing GlossaryTerm anchor`) — both rows present in
  `glossary_glossaryterm`.
- **Path resolution** — `_resolve_spec_path` raises on an ambiguous basename;
  `find docs -name spec-011-stale_placeholder_cleanup-0_0_4.md` returns exactly one path. The stored
  `kanban_specdoc.path` for card 11 is already the archived path
  `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`, so no basename fallback is needed.
- **Companion location** — `_terms_path` prefers a sibling `…-terms.csv` beside the spec and falls
  back to `appx/`. No sibling exists at `docs/SPECS/`, so the `appx/` copy is the one that loads.
- **The DB already matches the CSV**, so a future import is a no-op rather than a repair:
  `kanban_cardglossaryterm` for card 11 is `0|definition-order-independence|definition-order` and
  `1|scalar-field-override-semantics|scalar-field`, and `glossary_glossaryspecmention` for the
  archived spec path carries the same two terms at orders 0 and 1. That is exactly what
  `_assert_plan_matches_db` compares, so `import_spec_terms --check` would pass for this card.

**No command that writes `examples/fakeshop/db.sqlite3` was run.** The database was copied to the
session scratchpad and queried with `sqlite3 -readonly`; `import_spec_terms` itself was **read, not
executed**, and no `manage.py` invocation of any kind was made.

### 3. Durable-doc completion

Reported explicitly in both directions, per the dispatch.

**Consistent, no edit owed:**

- **`docs/TREE.md`** carries all three test modules with accurate one-line descriptions —
  `tests/types/test_definition_order.py` ("Acceptance tests for definition-order-independent
  DjangoType relation finalization."), `tests/types/test_definition_order_schema.py` ("Schema-build
  tests …"), `tests/optimizer/test_definition_order.py` ("Optimizer tests for definition-order-
  independent DjangoType relation graphs."), each in both of the file's two renderings. Each line is
  character-identical to the module's own docstring, which is what the render reads, so the doc is
  not merely present but *current*. None carries staging language ("planned", "Slice N", `TODO(`),
  so `ARTIFACT.md`'s script-rendered-doc check is satisfied. The two donor files' descriptions
  (`tests/types/test_base.py`, `tests/optimizer/test_extension.py`) describe their surviving subjects
  and carry no residue of the retired placeholders.
- **`docs/GLOSSARY.md#definition-order-independence`** — `shipped (0.0.4)`, and its "Supported
  relation cycles" / "Supported forward-reference … shapes" lists cover exactly the two subjects the
  retired placeholders deferred: "forward and reverse M2M", and target types "declared before or
  after the source type" plus same-module string annotations and cross-module
  `strawberry.lazy`. The spec's `## Scope` bullets and this entry say the same thing at different
  altitudes; neither contradicts the other.
- **`docs/GLOSSARY.md#scalar-field-override-semantics`** — `shipped (0.0.6)`, matching the spec's
  closing paragraph handing the concern to `DONE-019-0.0.6`.
- **`CHANGELOG.md` `## [0.0.4] - 2026-05-08`** — card 011's contribution is folded into `### Changed`
  ("Tests were expanded across settings, registry lifecycle, … definition-order cycles, …"). Nothing
  in the entry misstates or overstates the card, and a test-only cleanup has no user-visible surface
  to add; `AGENTS.md` rule 21 forbids an unrequested changelog edit in any case. **No edit owed.**
- **The spec's one checkable negative still holds.** `grep -rEn "pytest\.mark\.(skip|xfail)"` over
  `tests/types/` and `tests/optimizer/` returns **0**; the tree-wide count under `tests/` is **1**,
  `tests/test_permissions.py:823`, a `skipif` outside both directories and outside this card's
  scope. None of the four placeholder symbol names
  (`test_relation_m2m_returns_list`, `test_forward_reference_resolves_when_target_defined_later`,
  `test_optimizer_applies_prefetch_related_for_m2m`, `test_consumer_annotation_overrides_synthesized`)
  occurs anywhere under `tests/`, `examples/`, or `django_strawberry_framework/` — **0 occurrences
  each** — and all three successor tests named by the spec exist as `def test_…` today.
- **No staged anchor from this card survives.** `grep -rn 'TODO(spec-011'` -> **0**. `spec-foundation`
  survives only as quoted history inside this cycle's own rationale and plan, and inside
  `docs/builder/DONE/`; zero hits in package source or tests.

**Not consistent — reported, not edited: see `### Generated-doc edits reported, not made`.**

### 4. F11 — the `[spec-011]` ref-id cluster, measured

**The plan's "five surfaces" is an undercount, and the cluster is not confined to documentation.**
Measured by counting **occurrences of the token `spec-011`** across every tracked file plus this
cycle's three untracked artifacts (not by counting matching lines — a line can carry the token twice,
and four do):

**99 occurrences in 17 files.** Excluding this cycle's own three files (rationale 23, plan 18, R1
artifact 12) and the spec itself (3), the standing population is **43 occurrences in 13 files**.

The token means two different specs depending on the reader:

**Sense A — the pre-renumber `spec-011`, which is today `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`.**

| Surface | Occ. | Form |
|---|---|---|
| `docs/SPECS/spec-020-list_field-0_0_7.md` | 8 | `[spec-011]: spec-015-relay_interfaces-0_0_5.md` + 2 ref-uses + **4 bare prose mentions** ("spec-011 Decision 9", "ports from spec-011") that no link definition covers |
| `docs/SPECS/spec-027-filters-0_0_8.md` | 2 | ref-def -> spec-015 + 1 ref-use |
| `KANBAN.md` | 2 of its 6 | `[spec-011]: docs/SPECS/spec-015-relay_interfaces-0_0_5.md` + 1 ref-use |
| `KANBAN.html` | 2 of its 5 | the same card-body markdown inside the JSON data block |
| `django_strawberry_framework/types/base.py` | 5 | **package source** — `spec-011 #"An empty tuple is the same as not declaring"`, `spec-011 #"may be a tuple/list of interface classes"`, `(spec-011 Decision 4)`, and two `spec-011 Decision 7 #"keeps every selected Django field including the primary key"` |
| `django_strawberry_framework/types/resolvers.py` | 1 | **package source** — `(spec-011 Decision 7)` |
| `tests/types/test_base.py` | 1 | `No behavior change (spec-011-era rejection)` |
| `tests/filters/test_sets.py` | 1 | `apply_interfaces (spec-011)` |
| `docs/builder/DONE/build-005-django_type_contract-0_0_3.md` | 4 | closed-cycle record; D13 attributes `_validate_interfaces` to "spec-011 (validation)" while listing spec-015 separately as "the feature" |
| `docs/builder/DONE/build-001-django_types-0_0_1.md` | 1 | closed-cycle record |

**Sense A is provable, not inferred.** The three quoted substrings the source comments pin against
exist verbatim in `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` — lines 324, 323, and 361 — and
spec-015's `### Decision 4: validation` and `### Decision 7: optimizer and projection invariants` are
the decisions named. Spec-020's "spec-011 Decision 9 (async `get_queryset` shape)" likewise matches
spec-015's `### Decision 9: async resolver support`. So six occurrences in **package source and
tests** carry a spec number that today resolves to an unrelated spec. `AGENTS.md` rule 27 permits a
spec-Decision pointer in a code comment, which makes these load-bearing provenance refs rather than
scratch — and therefore worth correcting, not deleting.

**Sense B — this card's spec, `spec-011-stale_placeholder_cleanup-0_0_4.md`.** `KANBAN.md` lines 136
and 4565 (inline links, correct), `KANBAN.html`'s three matching strings, this cycle's own files, and
`docs/builder/DONE/build-007-…md` line 254 (a byte-count comparison — correct).

**The actively-wrong links are two files, not one.** Every `[spec-011]` **definition** in the tree:

| File | Definition target | Verdict |
|---|---|---|
| `KANBAN.md:5253` | `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` | resolves correctly; the **ref-id** is the stale part |
| `docs/SPECS/spec-020-list_field-0_0_7.md:894` | `spec-015-relay_interfaces-0_0_5.md` | same |
| `docs/SPECS/spec-027-filters-0_0_8.md:1264` | `spec-015-relay_interfaces-0_0_5.md` | same |
| `docs/SPECS/appx/spec-011-…-rationale.md:325` | `../spec-011-stale_placeholder_cleanup-0_0_4.md` | correct; this cycle's own file, sense B throughout |
| `docs/SPECS/spec-032-full_relay-0_0_9.md:750` | `spec-011-stale_placeholder_cleanup-0_0_4.md` | **wrong.** Line 87's prose attributes the `Meta.interfaces` rejection to "[`spec-011`][spec-011]-era behavior" — sense A — so the link sends a reader to a test-cleanup card that shipped no package source. The plan named this one. |
| `docs/SPECS/appx/spec-005-…-rationale.md:693` | `../spec-011-stale_placeholder_cleanup-0_0_4.md` | **wrong, and the plan did not name it.** Line 262 lists `spec-011` among the siblings that "superseded a claim here", beside `spec-015` as a separate entry; card 011 superseded no spec-005 claim, having shipped no source. The same misattribution as spec-032, inherited from `build-005`'s D13. |

**Provenance, carried from R1.** `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` was created
at `81e4704d` (2026-06-01) by the archive-and-renumber pass, while `docs/spec-011-relay_interfaces-0_0_5.md`
had held the number since `df13b644` (2026-05-17) and is now `spec-015-relay_interfaces-0_0_5.md`.
Everything written before the renumber that says "spec-011" means the relay spec; everything written
after means this card. The ref-ids and the source comments are the residue.

**Not fixed, and deliberately.** The cluster spans package source, two test modules, four archived
specs, two closed build records, and two DB-generated files. Correcting the one file this cycle owns
would leave it *divergently* wrong. It goes to the deferred-work catalog whole.

### 5. Deferred items carried forward from R1

For `bld-011-final.md`'s `### Deferred work catalog`, so it assembles in one read.

#### F8 widened — unused link definitions

R1's measurement stands and was re-run unchanged: R1's own command over `docs/SPECS/*.md` +
`appx/*.md` still lists exactly **eight** files whose only `[backlog]` occurrence is the definition —
`spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-054`. **The
plan's figure of fifteen does not reproduce.**

This pass widens the frame rather than re-litigating it. `[backlog]` is one ref-id of a general
pattern: across every tracked `.md` carrying a link-definition block, plus this cycle's companion,
**23 files carry 71 definitions that no body reference uses.** The largest are `KANBAN.md` (28 —
DB-generated), `spec-051` (6), `spec-050` and `spec-054` (5 each), `CHANGELOG.md` (5). Nothing in the
tooling catches them: `check_trailing_commas.py` enforces only the header scaffold
(`_SCAFFOLD_MARKERS` / `LINK_DEF_CATEGORIES`), and `check_spec_glossary.py` only checks glossary
terms. A sweep therefore needs a new check or a one-off script, which is itself an argument for doing
it once rather than eight times.

**This cycle's companion contributes two of the 71** — `[backlog]` and `[kanban]`, both unused in
`spec-011-…-rationale.md`. Left in place as a decided disposition, not an oversight: removing them
would make this cycle's file the single exception in a 23-file pattern, which is the shape
`worker-0.md` `## Closing out a kanban card` rejects, and R1 settled the identical question for the
spec. If the maintainer prefers the opposite call, deleting two lines from the companion is the whole
change.

#### The plan's two corrected figures — do not re-copy from the plan

- **`[backlog]`-carrying stubs: eight, not the plan's "fifteen."** Re-verified above.
- **`a357c68c`'s replacement siblings: eighteen added `def test_` lines, not the plan's "six."**
  R1's measurement; corroborated by the TODO block deleted inside the placeholder itself, which
  predicted "18 sibling tests".

#### Archived stubs still carrying the boilerplate preamble

`spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026` — five of the seven spec-007 measured,
each awaiting its own residual cycle. spec-007 and spec-011 are the two whose cycles have run.

#### F11

The whole cluster, as measured in section 4 above. A maintainer / next-spec-author item, and the
only catalog entry that reaches package source.

### Generated-doc edits reported, not made

`KANBAN.md` and `KANBAN.html` render from `examples/fakeshop/db.sqlite3` and are never hand-edited
(`START.md` `## Rendered docs`, `BUILD.md` `### Generated docs are DB-backed`). The `DONE-011-0.0.4`
card body carries two defects this audit found. **Reported for Worker 0 to re-partition with a
Worker 2 pass** (ORM edit + `build_kanban_md.py` regenerate + `KANBAN.html` data-block regenerate);
no DB write was made here.

1. **The card's `#### Scope` bullet 2 is the falsified tense R1 removed from the spec.** It reads
   "Kept the remaining scalar override skip documented as a separate scalar-field concern under
   `DONE-019-0.0.6`." That is finding F6 verbatim, still live on the board: the skip
   (`tests/types/test_base.py::test_consumer_annotation_overrides_synthesized`) was retired at
   `0.0.6` by `a357c68c`, and **0 occurrences** of the name survive anywhere in the tree. The spec
   now states the standing division of concerns instead; the card still claims a placeholder stands.
   The card's `#### Card references` block re-renders the same sentence, so one field edit fixes both
   renderings. Suggested replacement, matching the reconciled spec's altitude: *"Scalar field
   override semantics is a separate concern from definition order and is owned by `DONE-019-0.0.6`,
   which ships it at `0.0.6`."*
2. **`#### Scope` carries a duplicate row.** Bullet 3, "replace stale M2M / forward-reference skips
   with definition-order tests.", is a lowercase restatement of bullet 1, "Replaced stale M2M and
   forward-reference skips with definition-order tests." This is the duplicate the rationale's
   `## Other` entry dispositioned as "a restatement of `## Scope` bullet 1" — it is not only in the
   retired `Other` render, it is a live `Scope` item. One of the two rows should be deleted.

A third, minor and optional: `#### Files likely touched` names only the three replacement modules and
never `tests/types/test_base.py` or `tests/optimizer/test_extension.py`, the two files the
placeholders were **removed from**. The reconciled spec names all five. Adding the two donor paths
would make the board agree with the spec; leaving them is a board-fidelity question, not a
correctness one, since "likely touched" is a planning-time field.

`docs/GLOSSARY.md` needs **no** edit: both anchors are accurate and carry the right shipped versions
(section 3).

### Verification commands run

- `check_spec_glossary.py --spec docs/SPECS/spec-011-…md` -> `OK: 2 terms` (exit 0)
- `check_trailing_commas.py --check <spec> <companion>` -> exit 0
- per-definition `[ -e ]` disk check after `cd` into each file's own directory -> 20/20 resolve
- Python re-derivation of the scaffold: ten canonical headers, exact order, alphabetical within group
  -> both files pass; unused-definition counts as reported
- `sqlite3 -readonly` against a **scratchpad copy** of `examples/fakeshop/db.sqlite3` for the
  glossary terms, the card's glossary links, the spec mentions, and `kanban_specdoc.path`
- token-occurrence sweep for `spec-011` over `git ls-files` + this cycle's untracked artifacts
- `grep -rEn "pytest\.mark\.(skip|xfail)"`, the four placeholder-symbol sweeps, `TODO(spec-011`,
  and `spec-foundation`
- **No `pytest` run**: this item has no test, and the plan declares floor-verification scope `none`
  and hot-path `none` (Markdown only). No `--cov*` flag was used anywhere.

### Working-tree discipline

No file outside this item's writable set was modified. `git status --porcelain` counts **119** dirty
paths at the end of this pass — up from R1's 111 and the plan's 95, the moving baseline the plan
warns about — and **not one was edited, reverted, staged, or `git checkout`-ed** (`AGENTS.md` rule
34). `docs/SPECS/spec-009-*`, `spec-010-*`, their companions, and the concurrent sessions' plans and
artifacts were not opened for writing. No generated doc and no database was written.

### Summary

The archive is clean. Both files' link definitions resolve from their own directories, the scaffold
is canonical in both, the glossary and scaffold checkers exit 0, and the masked-rot trap has no
instance in this cluster — the one masking pair the repository contains (`README.md` at two depths)
is not linked by either file. The terms CSV is importable against the constraints read out of
`import_spec_terms` itself, and the database already matches it row for row, so a future import is a
no-op. The spec's checkable negative and all three of its successor-test claims re-derive at this
working tree.

Two durable-doc defects were found, both DB-backed and both in the `DONE-011-0.0.4` card body: the
falsified kept-skip sentence R1 removed from the spec is still live on the board, and `#### Scope`
carries a duplicate row. They are reported for a Worker 2 ORM pass, not edited.

F11 is larger than the plan recorded. Measured by token occurrence, `spec-011` appears 99 times in 17
files; 43 of those, in 13 files, are the standing cluster, and it reaches **package source and two
test modules**, not only documentation. Two files — `spec-032` and `spec-005`'s rationale — define
`[spec-011]` pointing at this card while their prose means the pre-renumber relay spec, and the
source comments' quoted substrings prove that referent is `spec-015` Decisions 4, 7, and 9. The whole
cluster goes to the deferred-work catalog with every surface named.

### Spec changes made (Worker 1 only)

**None.** The audit found no broken link, no scaffold violation, and no claim in either file that
does not hold, so neither file was opened for writing. The one candidate — the companion's two unused
link definitions — is dispositioned under `### F8 widened` as an instance of a 71-definition
repo-wide pattern rather than a defect to partial-fix, consistent with R1's accepted F8 disposition.
R1's dispositions were not re-litigated.

### Final status

`final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
