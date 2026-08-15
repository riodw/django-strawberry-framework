# Build: R3 — finish the documentation and audit the archive

Spec reference: `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` (post-R2, whole file)
Status: final-accepted

Plan source: `docs/builder/build-008-definition_order_independence-0_0_4.md` `### Residual scope`
item R3, `### Every reference TO spec-008`, `### The read-only correctness audit — findings`.
Inputs consumed: `docs/builder/bld-008-r2-spec_reconciliation.md:2409` (the deferred-work catalog) and
`docs/builder/bld-008-r2b-source_attribution.md` `### Notes for Worker 1` (its final block).

## Plan (Worker 1)

R3 is four read-only audits plus the carry-forward of the deferred-work catalog. Per plan
`### Deviation 2` the chain is **Worker 1 (perform, `planned`) -> Worker 3 (audit) -> Worker 1 (final
verification)**, unless an audit finds writable drift, in which case the full chain runs and the item
says so.

### DRY analysis

- Nothing is re-derived that a prior pass already proved *and recorded with its derivation command*.
  The catalog is carried **by reference** (`bld-008-r2-spec_reconciliation.md:2409`), not copied:
  copying it would create two catalogs that drift, and `BUILD.md` `## Final test-run gate` wants the
  live one in `bld-final.md`. What R3 adds is the R2b delta (item 4 closed, three new durable rows).
- Every count in the dispatch prompt is re-derived here with its unit and its command, per the
  cycle's signature defect (`build-008-…md #"The count-error class is this cycle's signature defect"`)
  and this worker's memory (`## Pattern notes` — twelve firings).

### Implementation steps

1. Durable-doc audit: `docs/GLOSSARY.md` `## Definition-order independence`, `` ## `finalize_django_types` ``,
   `## Schema audit`; `docs/README.md #"Schema setup boundary"` — each claim checked against package
   source at HEAD-plus-R2b.
2. Cross-reference sweep, three directions: inbound (who names spec-008), outbound (what spec-008 and
   its rationale name), and DB/CSV (kanban `SpecDoc.path`, terms CSV, glossary anchors).
3. `SpecDoc.path` / terms-CSV verification by read-only ORM query, plus
   `import_spec_terms --check` and `check_spec_glossary --spec`.
4. Staged-anchor sweep with the quote-subtraction the R2b pass warned about.

### Test additions / updates

None. R3 writes no source and no test; `## Build-wide context flags` keeps `tests/` and `examples/`
read-only, and R2b (the cycle's only source item) is closed.

### Implementation discretion items

None material: every step is a fixed verification with a prescribed command.

### Spec slice checklist (verbatim)

The plan's checklist row for R3, expanded to its four named audits. Ticked by Worker 1 in the same
pass that performed them (R3 has no Worker 2 — see `### R3's shape` below); Worker 3 audits the ticks.

- [x] durable-doc audit against the shipped relation graph
- [x] the cross-reference sweep in all three directions
- [x] `SpecDoc.path` / terms-CSV verification
- [x] the `TODO(spec-008` / `TODO-<MILESTONE>-008` staged-anchor sweep

---

## Audit 1 — durable docs against the shipped relation graph

**Result: accurate and complete. No durable-doc edit is owed.** Worker 0's pre-flight finding
(`build-008-…md #"The durable docs are accurate and complete"`) is confirmed by re-derivation, not
assumed. Four surfaces read end-to-end and checked claim-by-claim against package source.

`docs/GLOSSARY.md` is DB-generated (`scripts/build_glossary_md.py` from `examples/fakeshop/db.sqlite3`),
so a needed change would be an ORM edit plus a regenerate against a concurrently-written DB — the
plan's `## Concurrent-writable tracked binary / generated files` escalation path. **It was not
needed**; nothing was written and no escalation is raised.

### `docs/GLOSSARY.md` `## Definition-order independence` (heading at line 490 as read; cite by heading)

| Claim | Verification at HEAD+R2b | Verdict |
|---|---|---|
| Collection is split from finalization; class creation records Django metadata + pending relation targets | `types/base.py::DjangoType.__init_subclass__` registers then appends pending records; `types/relations.py::PendingRelation` | holds |
| `finalize_django_types()` resolves pending relations, attaches generated relation resolvers, decorates with `strawberry.type` | `types/finalizer.py::finalize_django_types` — resolve loop, `_attach_relation_resolvers`, `strawberry.type(type_cls, …)` | holds |
| Six relation cycles + multi-cycle graphs | `types/converters.py::resolved_relation_annotation` dispatches on the Django field kind; fakeshop exposes all six | holds |
| Six forward-reference / manual-override shapes, annotation-only override keeps the generated resolver, `strawberry.field(resolver=…)` keeps the consumer resolver | `types/base.py::_build_annotations` (consumer-authored skip) and the Phase-2 skip sets — relation pass skips `consumer_assigned_relation_fields`, file pass skips the broader `consumer_authored_fields` | holds |
| Unresolved targets fail during finalization with an error naming source model, source field, target model | `types/finalizer.py::_format_unresolved_targets_error` emits `"  - {source_model}.{field_name} -> {related_model} (no registered DjangoType)"` — three elements present | holds |
| "Validation that a manual relation annotation matches the Django relation cardinality is deferred." | `grep -rniE 'cardinalit' django_strawberry_framework/` -> **9 occurrences, 0 of them a validator**: 4 are resolver/converter shape-dispatch comments, 5 are `filters/sets.py` lookup-cardinality selection. No consumer-annotation-vs-Django-cardinality check exists | holds (still deferred) |

### `docs/GLOSSARY.md` `` ## `finalize_django_types` ``

The entry's **seven-step phase order** is the strongest claim in the durable set and the one most
likely to have rotted, so it was walked against the function body statement by statement rather than
spot-checked. **All seven map, in order:**

1. audit primary ambiguity + resolve every pending relation failure-atomically -> `_audit_primary_ambiguity(multi_type_models)`, then the `unresolved` collection loop and `raise ConfigurationError(...)` **before** the annotation-rewrite loop mutates any class.
2. attach generated relation and file resolvers -> `_attach_relation_resolvers` + `_attach_file_resolvers` in one Phase-2 loop.
3. apply interfaces, install Relay defaults, validate keyset cursor columns -> `apply_interfaces`, `_check_composite_pk_for_relay_node` / `install_relay_node_resolvers` / `install_globalid_typename_resolver`, then `keyset::validate_cursor_field_columns` under `definition.cursor_field is not None`.
4. synthesize relation connections -> `_synthesize_relation_connections()`.
5. audit GlobalID routing, reset generated emit namespaces, then bind auth, mutations, forms, filtersets, ordersets -> `_audit_model_label_routing` (+ `_warn_model_label_secondary_collapse`), `for clear in iter_subsystem_clears(before_bind=True)`, `bind_auth_mutations` (guarded `loaded_attr`), `bind_mutations()`, `bind_form_mutations()`, `_bind_filtersets()`, `_bind_ordersets()`.
6. audit the complete field surface after synthesis and sidecar binding -> the `_audit_field_surface` loop.
7. apply `strawberry.type(...)`, mark each definition finalized, then mark the registry finalized -> the final loop plus `registry.mark_finalized()` as the last statement.

Also confirmed: **"calling it a second time is a no-op"** (`if registry.is_finalized(): return` entry
guard); **declaring a new concrete `DjangoType` after finalization raises `ConfigurationError`**
(`types/base.py` #"already ran; cannot register"); and the dependency sentence the entry states as a
build contract (keyset validation ahead of connection synthesis, synthesis ahead of sidecar binding,
field-surface audit last) is exactly the statement order above.

The entry's rerun/recovery prose agrees with `types/finalizer.py`'s module docstring
(fine-grained per-entry `definition.finalized` guards; `registry.clear()` the recommended path only
when the type cannot be fixed in place). This is the contract R2 already amended spec-010 to match
under `#### Maintainer decision 5`; the glossary needed no change and gets none.

### `docs/GLOSSARY.md` `## Schema audit`

`optimizer/extension.py::DjangoOptimizerExtension.check_schema` — walks schema-reachable types,
reports relation targets without registered `DjangoType`s as **warnings** (never raises), dedupes
identical `(model, field_name)` pairs through a `seen` set, and skips hidden / `OptimizerHint.SKIP`
fields. Every clause of the entry is present in the implementation. **holds.**

### `docs/README.md #"Schema setup boundary"`

Documents the explicit-call contract with both the correct and the incorrect ordering, and names no
auto-trigger. Re-derived the D3 negative that makes this correct:
`grep -rn 'finalize_django_types()' django_strawberry_framework/` -> **46 matching lines, 0 call
sites** (unit: matching lines; every hit is a docstring, comment, error string, or the `def` at
`types/finalizer.py:664` — `DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` still do
not call it). **holds.**

---

## Audit 2 — cross-reference sweep, three directions

**Result: the archive is complete and consistent in all three directions. No edit is owed.** One
generated-file staleness is **recorded, not fixed** (`KANBAN.md:248`), exactly as the plan directs.

### Direction 1 — inbound (who names spec-008)

`grep -rln 'spec-008' . --exclude-dir=.git` -> **14 files**. Occurrence counts below are
`grep -oF 'spec-008' <file> | wc -l` (unit: **occurrences**, not matching lines — `grep -c` on
`KANBAN.md` reports 5 lines for 7 occurrences, which is this cycle's signature unit trap in miniature).

| File | Occurrences | Status |
|---|---|---|
| `KANBAN.md` | 7 (on 5 lines) | Generated. `:139` and `:4746` are the card's spec link, already the archived path; `:248` is the board item below; `:325` / `:331` are unrelated board items naming the appx rationale convention | 
| `KANBAN.html` | 6 (on 1 line — the whole `window.KANBAN_DATA` payload) | Generated data block; never hand-edited |
| `docs/SPECS/spec-009-…md` | 1 (`:6`, "The narrow definition-order problem is documented in …") | Consistent; verify-only, unchanged |
| `docs/SPECS/spec-010-foundation-0_0_4.md` | 7 (on 4 lines) | `:5` description, `:48` and `:408` the two **now heading-anchored** citations, `:557` the `## References` pointer. See below |
| `docs/builder/build-001-*.md`, `build-002-*.md`, `build-006-*.md` | 2 / 1 / 3 | Closed or concurrent cycles' records; **never edited**. `build-006` is a new inbound namer since the plan's table was written (it records this cycle starting) — recorded, not touched |
| this cycle's `build-008-*` + four `bld-008-*` | 52 / 44 / 158 / 9 / 4 | This cycle's own artifacts |

**`docs/SPECS/spec-001-django_types-0_0_1.md` no longer names spec-008 at all** — partition Edit 1
landed: `:66` now reads "`spec-010-foundation-0_0_4.md` owns that pass; this spec owns what subclass
creation collects." The plan's `### Every reference TO spec-008` table row for spec-001 is therefore
discharged, not merely verified.

**Decision 3's two line-range citations are gone.**
`grep -nE 'spec-008[^ ]*\.md.? \([0-9]+-[0-9]+\)' docs/SPECS/spec-010-foundation-0_0_4.md` -> **0
matches**. `:48` now cites `#"### The finalization trigger"` and `:408` cites `#"### The shape that
shipped"`. Edit 3 landed at `:65` ("No shipped helper auto-triggers finalization: `DjangoSchema`,
`DjangoConnectionField`, and `DjangoNodeField` do not call `finalize_django_types()`…"), with the
spec-009 `(670-687)` range restored exactly as Edit 3 prescribes.

**`KANBAN.md:248` — recorded for the maintainer, not fixed.** The board item lists spec-008 among the
specs "still naming `convert_relation`". `grep -oF convert_relation` per file (unit: occurrences):
spec-008 **0** (R2 removed both), spec-009 **3**, spec-010 **2**, spec-019 **3**. So the item has
**one fewer target** than it names. `KANBAN.md` is DB-generated, so this is a record, not an edit.

One nuance worth pinning so a later pass does not "correct" the board in the wrong direction:
`docs/SPECS/spec-018-meta_primary-0_0_6.md` also contains `convert_relation` **2** times, but both are
explicitly historical ("was historically referenced as `convert_relation`"), which is not the
present-tense survival the board item sweeps. Its omission from the list is correct.

### Direction 2 — outbound (what spec-008 and its rationale name)

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-…md` -> `OK: 10 terms -
  all have glossary entries and at least one spec link.` (exit 0)
- `uv run python scripts/check_trailing_commas.py --check` over the spec, the rationale, and this
  artifact -> exit 0 (link-definition scaffold and the ten canonical group headers intact).
- **Every link definition resolves on disk.** Non-URL, non-in-page defs walked and existence-checked
  relative to each file's own directory: spec **22/22 present, 0 missing**; rationale **29/29 present,
  0 missing** (unit: link-definition lines).
- **The `README.md` masking trap (`build-008-…md #"masks depth rot"`) is not live here**: neither file
  defines a `README.md` target at any depth. The rationale's only root/`docs/`-ward def is
  `[glossary]: ../../GLOSSARY.md`, which resolves to `docs/GLOSSARY.md` — the intended file, and there
  is no same-named decoy one level up.

### Direction 3 — DB and CSV

Covered in full by Audit 3 below: `SpecDoc.path` reads the archived path, and the card's ten glossary
links match the ten CSV rows one-for-one.

---

## Audit 3 — `SpecDoc.path` / terms-CSV verification

**Result: correct and importable. Nothing written to the DB.** All queries read-only.

- `Card.objects.get(number=8)` -> `card_id` **`DONE-008-0.0.4`**, `status.key` `done`,
  `target_version.number` `0.0.4`, title `Definition-order independence design`. Unchanged from
  pre-flight.
- `SpecDoc` for card 8 -> `path` **`docs/SPECS/spec-008-definition_order_independence-0_0_4.md`** —
  already the archived path, no repoint. (`url` is the read-only derived property and reads
  consistently.)
- `card.glossary_links.count()` -> **10** (unit: rows). Terms CSV
  `docs/SPECS/appx/spec-008-…-terms.csv` -> **10 data rows** (`tail -n +2 … | wc -l`) and **10
  distinct anchors** (`cut -d, -f2 | sort -u | wc -l`). **10 rows / 10 anchors / 10 links — one row per
  anchor, which is the property that makes the CSV importable**, and the property `worker-0.md`
  `### DONE-card invariants` warns a green `check_spec_glossary` does not prove.
- Anchor-by-anchor cross-check of CSV against the card's links: `configurationerror`,
  `definition-order-independence`, `djangoconnectionfield`, `djangonodefield`, `djangotype`,
  `finalize_django_types`, `metafields`, `metaprimary`, `relay-node-integration`, `schema-audit` —
  **exact set match, both directions**.
- Every one of the ten anchors is a live target inside `docs/GLOSSARY.md` (each is referenced by at
  least 4 in-glossary `(#anchor)` links; range 4-54).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have
  glossary links.`** (exit 0)

**Card 8's two incomplete `Verified in upstream` `CardItem`s** (catalog item 6) are confirmed still
`is_complete = False`, alongside three `Scope` rows and one `Note` at `True` — **six `CardItem`s
across three sections**, exactly as pre-flight recorded. They cite upstream symbols in a section that
is not a `Definition of done`, so the mark-every-DoD convention does not reach them. **Observation for
the maintainer; no DB write.**

---

## Audit 4 — the staged-anchor sweep

**Result: zero real staged anchors, tree-wide.** Confirmed for the third time in this cycle (Worker 0
at pre-flight, R2b as a by-product, R3 here), and re-derived rather than inherited.

Prescribed command, run from the repo root:

```
grep -rEn 'TODO\(spec-008|TODO-(ALPHA|BETA|STABLE)-008' . \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md --exclude-dir=.git
```

-> **6 matching lines** (unit: matching lines). **The subtraction the R2b pass warned about**: the
sweep's own documentation matches the sweep's pattern, so the raw hit count is never the anchor count.

| Hits | Source | Real anchor? |
|---|---|---|
| 3 | `build-008-…md:27`, `:395`, `:431` — the plan describing the sweep | no |
| 2 | `bld-008-r2b-source_attribution.md:1643`, `:1646` — R2b quoting the sweep | no |
| 1 | `bld-008-r3-doc_completion_archive.md:55` — **this artifact's own checklist box** | no |

**6 documentation quotes - 6 = 0 real anchors.** No package source, test, example, or durable doc
carries one.

Two derivation notes so the number is reproducible rather than merely repeated:

- **The binary hit belongs to the loose pattern, not the prescribed one.** `grep -acE` for the
  prescribed pattern against `examples/fakeshop/db.sqlite3` -> **0**. R2b's binary hit came from its
  looser probe `TODO-.*-008`, which matches unrelated card text inside the payload. Both readings are
  correct about their own pattern; the prescribed pattern has no DB hit at all.
- **The loose-probe figures have grown since R2b, and the growth is entirely artifacts.** Tree-wide,
  including the three excluded files: `grep -rn 'TODO(spec-008' .` -> **6 matching lines** (R2b: 3)
  and `grep -rn 'TODO-.*-008' .` -> **8** (R2b: 5). Every added line is a `docs/builder/` artifact
  written since — this file and R2b's own closing block. **A rising count here is the sweep
  documenting itself, never new staged work**, which is precisely why the raw figure must never be
  reported as the verdict.

---

## Deferred work catalog — carried forward for `bld-final.md`

**Carried by reference, not copied.** The catalog lives at
`docs/builder/bld-008-r2-spec_reconciliation.md:2409`, under `**For R3's \`### Deferred work
catalog\`:**`. Structure re-derived here (third independent derivation, after R2's and R2b's):
**ten numbered entries — items 1-8 are the catalog, and items 9-10 sit under a separate
`**Standing, for whoever runs the remaining rounds:**` sub-heading and are process carry-forward, not
deferred work. Ten numbers, eight items.**

Disposition after R3, so `bld-final.md` can carry it forward cleanly:

| # | Item (abbreviated) | Disposition after R3 |
|---|---|---|
| 1 | `spec-010 #"exactly as required by"`'s `spec-009 (1076-1077)` citation is stale (target is 8 lines earlier, at spec-009 `### Decision 6: fail loudly`) | **OPEN** — stale at HEAD, independent of this cycle; belongs to a spec-009 residual cycle |
| 2 | spec-009 `### Layer 3: Finalization trigger` now carries **two** inbound citations to reconcile — `(670-687)` at spec-010 `:65` (restored by Edit 3) and `(1076-1077)` at `:408` | **OPEN** — both to the same future spec-009 cycle. Both verified present at HEAD this pass |
| 3 | spec-010's rule-27 debt | **OPEN** — see the framing below; the largest item |
| 4 | `testing/relay.py`'s `(or build the schema)` string | **CLOSED by R2b.** Dispatched under decision 8, delivered, and pinned. Not deferred work |
| 5 | `spec-010:513`'s phase-2/3 partial-mutation contract, read and deliberately **left** | **CLOSED as not-a-defect** — recorded so it is not re-flagged. Partial mutation is still real; only the *recovery* claim was stale, and R2 fixed that |
| 6 | Card 8's two incomplete `Verified in upstream` `CardItem`s | **OPEN as a maintainer observation** — verified this pass (Audit 3), no DB write |
| 7 | `KANBAN.md:248`'s board item has one fewer target | **OPEN as a maintainer observation** — verified this pass with counts (Audit 2). Generated from the DB; not hand-editable |
| 8 | `docs/review/` holds an open maintainer escalation | **OPEN and unresolved** — see below |
| 9 | *(Standing)* the recurring failure mode: pointer names the right target, anchor lands on prose that does not carry the claim; the two separating tests are **subject match** and **explicit forwarding by name** | Process carry-forward |
| 10 | *(Standing)* baseline-dirty count | Process carry-forward; **re-derived below** |

### Added by R2b, and by this pass

- **M1 is NOT a deferral.** It was authorized and implemented inside this cycle as an R2b addendum and
  lives at `tests/testing/test_relay.py:186`. Catalogue it as *where it landed*, never as open.
- **Durable rule — the source-vs-runtime divergence in `testing/relay.py::global_id_for`'s message.**
  Two phrases are split across adjacent string literals, so **a source grep returns 0 occurrences for
  text that is present in the raised string**. **Any future audit or assertion about this message runs
  against the runtime (assembled) value, never the source text.** Five instruments now rest on that
  rule (`ast.Raise` walk x2, `compile()` + `co_consts`, the `JoinedStr` reconstruction, and the
  permanent assertion).
- **`#### Maintainer decision 6`'s spec-009 deferral is present in the catalog** — R2b asked R3 to
  confirm this, and it is: catalog items 1 and 2 are exactly the spec-009 residue, and decision 6's
  own text routes Layer 3's auto-trigger prose here. Confirmed present; nothing to add.
- **Not a deferral, closed so it is not re-opened:** the `_PendingRelationAnnotation` /
  `PendingRelationAnnotation` spelling difference between spec-010's pseudocode and the shipped
  symbol. Examined at both R2b reviews and both final verifications.

### Item 3 in full — spec-010's rule-27 debt

Carried with its framing intact, because the number alone would misrepresent the work:

**42 occurrences on 30 lines**, of which **20 occurrences on 15 lines** are in-repo rule-27 violations
and **22 occurrences on 15 lines** are pinned third-party prior art. Two of the in-repo refs
(`spec-010:299`, `:383`) sit inside pseudocode comment lines. **`spec-010 #"## Note on source line
references"` institutionalizes the practice**, so closing this is a conversion **plus a section
retirement** — and it **needs a maintainer decision authorizing spec-010 edits outside the sites
decisions 1-8 name**. It is not a find-and-replace, and R3 deliberately does not start it: this
cycle's writable surface in spec-010 is closed.

### Item 8 in full — the `docs/review/` escalation

**OPEN and unresolved.** Five `rev-*.md` were deleted, and two of those later returned modified
(`rev-_cross_web_patches.md` during the spec-007 cycle, `rev-_django_patches.md` during this one).
Two files coming *back* is not what a stray `rm` looks like, so the evidence points to a REVIEW cycle
regenerating its own artifacts rather than an `AGENTS.md` rule 22 violation — **but that remains
evidence, not a conclusion, and only the maintainer can confirm the intent.** No pass in this cycle
touched, restored, or reverted anything under that directory, and **R3 did not either**. Nobody
touches it.

**New evidence this pass, which strengthens the reading without closing the escalation.** At R3's
working-tree read, **all five** of the originally-deleted `rev-*.md` are back on disk as ` M`:
`rev-_django_patches.md` (returned during this cycle, already recorded), plus
`rev-_strawberry_patches.md`, `rev-apps.md`, and `rev-conf.md`, which were ` D` at R2's final
verification and are ` M` now. The escalated set therefore reads **five modifications, zero
deletions** — every deleted file returned. That is what regeneration looks like and not what a stray
`rm` looks like. **Still evidence; the escalation stays open until the maintainer confirms.**

---

## Working-tree baseline at R3 (catalog item 10 re-derived)

`git status --short | wc -l` -> **49 entries** (unit: status lines), up from R2's 43. `HEAD` has not
moved: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`. **Nothing was reverted and nothing outside R3's
writable set was written.**

The six new entries since R2's count, all attributable and none this pass's:

- `django_strawberry_framework/conf.py`, `tests/base/test_conf.py` (`M`) — the concurrent
  transport/config source session, now its seventh and eighth files.
- `docs/review/rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md` — ` D` -> ` M` (the
  regeneration evidence above); the entries are not new, their **states** changed.
- `docs/builder/bld-008-r3-doc_completion_archive.md` (`??`) — **this artifact**, the only entry R3
  added.

R2b's four files (`types/relations.py`, `types/base.py`, `testing/relay.py`,
`tests/testing/test_relay.py`) are present and `M`, as expected for a closed-but-uncommitted item.

---
## R3's shape

**Procedural closure** (`BUILD.md` `### Procedural-closure slices`), stated explicitly as the plan's
`### Deviation 2` requires.

All four audits are read-only and **all four found nothing writable**. In particular:

- No durable-doc edit is owed, so no ORM edit and no `build_glossary_md.py` regenerate is needed —
  which is the outcome that keeps this pass off the concurrently-written `examples/fakeshop/db.sqlite3`
  entirely. **No escalation to Worker 0 is raised.**
- The one live edit the plan reserved for R3 as a contingency — `#### Maintainer decision 3`'s two
  spec-010 citations — **was folded into R2 and has landed**, verified above (0 remaining raw
  line-range citations to spec-008 in spec-010). R3 inherits no edit from it.
- R2b closed with **no spec amendment owed**, so R3 inherits none from that direction either.

R3's diff is therefore exactly one new file: this artifact. The chain is
**Worker 1 (perform, `planned`) -> Worker 3 (audit) -> Worker 1 (final verification)**.

## Counts re-derived in this pass, with units and commands

Every figure the dispatch carried was re-derived rather than trusted. The unit trap has now fired
**twelve** times in this cycle (ten of the line-vs-other-unit shape, one plain miscount, one false
positive); nothing below is inherited.

| Claim | Unit | Command | Result |
|---|---|---|---|
| catalog structure | numbered entries / catalog items | read `bld-008-r2-…md:2409` block | **10 numbers, 8 items** (9-10 under `Standing,`) — matches R2b |
| card 8 glossary links | DB rows | `card.glossary_links.count()` | **10** |
| terms-CSV rows | CSV data rows | `tail -n +2 … \| wc -l` | **10** |
| terms-CSV anchors | distinct anchors | `cut -d, -f2 \| sort -u \| wc -l` | **10** — one row per anchor |
| card 8 `CardItem`s | rows | `CardItem.objects.filter(card=c)` | **6** (3 `Scope` True, 2 `Verified in upstream` False, 1 `Note` True) |
| staged anchors (prescribed pattern) | matching lines | the `grep -rEn` above | **6 lines, 6 documentation quotes, 0 real anchors** |
| staged anchors in `db.sqlite3` | matching lines | `grep -acE '<prescribed>' examples/fakeshop/db.sqlite3` | **0** (R2b's binary hit belongs to its looser `TODO-.*-008` probe) |
| loose probes tree-wide | matching lines | `grep -rn 'TODO(spec-008' .` / `grep -rn 'TODO-.*-008' .` | **6** / **8** (R2b: 3 / 5; all growth is `docs/builder/` artifacts) |
| inbound spec-008 namers | files | `grep -rln 'spec-008' . --exclude-dir=.git` | **14** |
| `spec-008` in `KANBAN.md` | occurrences (**not** lines) | `grep -oF 'spec-008' KANBAN.md \| wc -l` | **7 occurrences on 5 lines** |
| `convert_relation` per spec | occurrences | `grep -oF convert_relation <file> \| wc -l` | spec-008 **0**, spec-009 **3**, spec-010 **2**, spec-018 **2** (historical), spec-019 **3** |
| spec-010 raw range citations to spec-008 | matches | `grep -nE 'spec-008[^ ]*\.md.? \([0-9]+-[0-9]+\)'` | **0** |
| link definitions resolving | link-def lines | per-file walk, existence-checked from each file's own dir | spec **22/22**, rationale **29/29**, **0 missing** |
| `finalize_django_types()` in package | matching lines / call sites | `grep -rn 'finalize_django_types()' django_strawberry_framework/` | **46 lines, 0 call sites** |
| cardinality validators | occurrences / validators | `grep -rniE 'cardinalit' django_strawberry_framework/` | **9 occurrences, 0 validators** |
| working-tree baseline | status lines | `git status --short \| wc -l` | **49** (R2: 43) |

Two of the dispatch's own figures are confirmed exactly as given and are recorded as confirmed rather
than silently reused: the **ten CSV rows / ten glossary links** pairing, and spec-010's rule-27 debt
(**42 occurrences on 30 lines**; **20 / 15** in-repo, **22 / 15** third-party) — the latter carried
from R2's artifact unmodified because re-deriving it would mean sweeping a file this cycle may not
edit, and the figure's *framing* (institutionalized by a section that must be retired) is the
load-bearing part, not the integer.

## Validation run

- No `ruff` run: R3's diff contains no `.py` file.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-…md` -> `OK: 10 terms` (exit 0).
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>` -> exit 0.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have glossary links.` (exit 0).
- `git status --short` after the pass: **49 entries**, of which exactly one — this artifact — is R3's.
  Every other entry is a concurrent session's or an earlier item's, and **none was edited or reverted**.
- No `pytest` run: R3 changes no code, and `--cov*` flags are banned regardless.

## Failability proofs / hot-path budget / floor verification

**Not applicable, declared rather than omitted.** R3 is a read-only audit item: no boundary, guard,
gate, or rejection path was introduced (boundary count **0**), no runtime code runs per request, and
no executable line changed in any file — so the plan's `Hot-path declaration: none` and
`Floor-verification scope: none` are both undisturbed, including the conditional form R2b's plan
attached to them (the condition is "no executable line changes"; R3 changes none, in package source
or anywhere else).

## Findings for the maintainer

Neither is a defect this cycle may fix; both are recorded so the final gate can carry them.

1. **`KANBAN.md:248`'s board item names one spec too many** — spec-008 no longer contains
   `convert_relation`. DB-generated; it corrects itself when that board item's own card is next
   regenerated. Do **not** add spec-018 to the list: its two occurrences are explicitly historical.
2. **Card 8's two `Verified in upstream` `CardItem`s remain `is_complete = False`.** They cite
   upstream symbols in a non-`Definition of done` section, so no convention requires them ticked; the
   observation stands from pre-flight and is unchanged.

## Notes for Worker 3

- **This artifact is R3's entire diff.** Nothing else in the working tree is R3's; the other 48
  `git status` entries belong to concurrent sessions or to closed items R1 / R2 / R2b.
- **The catalog is carried by reference on purpose.** R2's artifact holds the live text at
  `bld-008-r2-spec_reconciliation.md:2409`; duplicating it here would create the second copy that goes
  stale. What R3 adds is the disposition column, the three R2b additions, and item 4's closure.
- **Every count above carries its unit and its command.** Please re-derive them; twelve unit-trap
  firings in this cycle were all found by someone re-running someone else's grep, and three of those
  were the auditor's own.
- **The one judgement call worth a second opinion** is Audit 2's spec-018 nuance: `KANBAN.md:248` lists
  four specs, disk shows spec-018 also contains the token, and I ruled its omission *correct* because
  both occurrences are explicitly marked historical. If you read that differently, the board item has
  two errors rather than one — still a record-only finding either way.
- **`docs/review/` was not touched, read for content, restored, or reverted.** Its state change (three
  more files returning) was observed through `git status` alone.

## Notes for Worker 1 (spec reconciliation)

None owed. R3 found no spec defect and no durable-doc defect, so the spec and rationale were not
opened for edit; the cycle's spec surface closed with R2.

## Status

> Not the artifact's status. The canonical `Status:` line is the header block above (line 4), and it
> is the only line Worker 0 reads to drive dispatch (`ARTIFACT.md:3`, `:181`). This block records one
> pass's transition at the moment that pass wrote it.

`Status: planned` — set by Worker 1 on creation and performance. Per plan `### Deviation 2`, `planned`
on an R-item with no Worker 2 routes to **Worker 3 for the audit**, then back to Worker 1 for final
verification.

---

## Review (Worker 3)

R3 is a read-only audit item whose entire deliverable is its own recorded evidence, so the review is
the evidence audit: every one of the four audits' load-bearing claims was **re-derived from disk**,
not read for plausibility. All four **conclusions hold**. Three recorded figures do not, and one of
them carries a false absolute in the row that is the evidence for a durable-doc verdict.

Re-derivation environment: `HEAD` = `947f74948c16b20b0c15ff359bb53fbe462d4b8c` (unmoved since R3's
read), working tree **51** `git status --short` entries (R3 read 49; see `### Working-tree delta`).

### High:

None.

### Medium:

#### M1 — Audit 1's `cardinalit` row is wrong by a factor of ~4.7 and asserts a false absolute

`## Audit 1` records, as the evidence for the glossary's deferral sentence:

```docs/builder/bld-008-r3-doc_completion_archive.md:80
`grep -rniE 'cardinalit' django_strawberry_framework/` -> **9 occurrences, 0 of them a validator**:
4 are resolver/converter shape-dispatch comments, 5 are `filters/sets.py` lookup-cardinality selection.
```

Re-derived with the cited command, verbatim, from the repo root:

| Quantity | Unit | Command | R3 | Disk |
|---|---|---|---|---|
| `cardinalit` hits | matching lines | `grep -rniE 'cardinalit' django_strawberry_framework/ \| wc -l` | 9 | **42** |
| same | occurrences | `grep -rnoiE 'cardinalit[a-z]*' django_strawberry_framework/ \| wc -l` | 9 | **42** |
| same | files | `grep -rliE 'cardinalit' django_strawberry_framework/ \| wc -l` | (9 implied across 2) | **12** |

The two units coincide here (one hit per line), so this is **not** the line-vs-occurrence shape that
has fired ten times this cycle — it is shape (2), a correctly-named unit that was simply not measured.
The sub-enumeration does not reconcile with itself either: `types/resolvers.py` 3 + `types/converters.py` 1
= the claimed 4, but `filters/sets.py` alone carries **11** matching lines, not 5, and the row omits
`optimizer/field_meta.py` (8), `optimizer/walker.py` (2), `optimizer/hints.py` (2),
`optimizer/extension.py` (1), `optimizer/join_taxonomy.py` (1), `utils/relations.py` (6),
`types/base.py` (2), `management/commands/inspect_django_type.py` (3),
`extensions/resource_policy.py` (1). No scoping of the command to a subdirectory reproduces 9
(`types/` alone gives 6; `filters/` gives 11).

**"0 of them a validator" is false as written.** `django_strawberry_framework/types/base.py:1523` sits
inside the docstring of the `Meta.relation_shapes` target validator and reads "Cardinality is read from
``FieldMeta.is_many_side`` (the same single-source classifier the generated relation resolvers and the
Phase-2.5 synthesis key on), so the validator and the synthesis can never disagree" — a validator, and
one that reads cardinality.

**Why the durable verdict nevertheless survives, and why this is still Medium.** I read all 42 hits.
That validator rejects illegal `Meta.relation_shapes` **keys** (a `"connection"` shape on a
single-valued relation); it does not compare a consumer's **manual relation annotation** against the
Django relation's cardinality, which is what the glossary sentence defers. Every other hit is
classification (`utils/relations.py`, `optimizer/field_meta.py`), lookup-primitive selection
(`filters/sets.py`), or narrative comment. So `docs/GLOSSARY.md` `## Definition-order independence`
**#"Validation that a manual relation annotation matches the Django relation cardinality is deferred."**
is **accurate**, and Audit 1's verdict stands.

It is Medium rather than Low because of what R3 is. For R1/R2 the artifact was scratchpad and the spec
was the deliverable, which is why a prior artifact-only count error was correctly filed Low
(`bld-008-r2-…md` L9/L10). **R3 ships no durable file at all** — its recorded evidence *is* the
product, and it is what `bld-final.md` carries forward under `BUILD.md` `## Final test-run gate`. A row
that states a figure the cited command cannot produce, plus an absolute the package contradicts, is the
same defect class this cycle rejected R1 pass 1 for, in the one pass whose own preamble says "Every
figure the dispatch carried was re-derived rather than trusted." The dispatch prompt carried the
`9 / 0 validators` pair too, so this is a figure that travelled un-re-derived through two hops.

**Recommended change** (Worker 1, per plan `### Deviation 2`): correct the row to **42 matching lines
across 12 files, one occurrence per line**; replace "0 of them a validator" with the narrower,
true claim — *no check compares a consumer-authored relation annotation against the Django relation's
cardinality; the one cardinality-reading validator (`types/base.py::_validate_relation_shape_targets`)
validates `Meta.relation_shapes` keys, a different surface* — and keep the verdict `holds (still
deferred)`, which is unchanged. No durable doc is touched; no re-audit is owed.

**Test expectation:** none; no behavior is affected.

### Low:

#### L1 — `finalize_django_types()` package count is 46; disk and HEAD both read 45

`## Audit 1` `### docs/README.md` and the counts table both record **46 matching lines**.

- working tree: `grep -rn 'finalize_django_types()' django_strawberry_framework/ | wc -l` -> **45**
- HEAD (so this is not concurrent drift): `git grep -c 'finalize_django_types()' HEAD -- django_strawberry_framework/` summed -> **45**
- occurrences (`grep -rno`) -> **45**; one per line, so again not the unit shape

**The load-bearing half is independently confirmed.** `grep -rnE '^\s*(await )?(\w+\.)?finalize_django_types\(\)' django_strawberry_framework/`
-> **no match, exit 1**: the only non-string, non-comment occurrence in the package is the `def` at
`types/finalizer.py:664`. `DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` still do not
call it, so `docs/README.md #"Schema setup boundary"` **holds** and D3's negative is intact. Fix the
integer in both places.

#### L2 — Audit 4's own writing moved the number it reports, and the self-citation is off by one

The prescribed sweep now returns **8** matching lines, not 6:

```
grep -rEn 'TODO\(spec-008|TODO-(ALPHA|BETA|STABLE)-008' . \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md --exclude-dir=.git
```

The two additions are `bld-008-r3-doc_completion_archive.md:251` and `:384` — **R3's own derivation
note and its own counts table**, both of which quote the pattern. R3 named this mechanism precisely
("the sweep's own documentation matches the sweep's pattern, so the raw hit count is never the anchor
count") and then reported the figure it measured *before* writing those two lines, without saying the
figure was taken mid-write. The table's six rows are all still correct as rows; only the total moved.
Separately, the row citing "this artifact's own checklist box" gives `:55`; the box is at **`:56`**.

**The verdict is independently confirmed and unchanged: 0 real anchors.** All 8 hits are prose in
`docs/builder/` (3 build plan, 2 R2b, 3 this artifact). No package source, test, example, durable doc,
or spec carries one. `grep -acE '<prescribed pattern>' examples/fakeshop/db.sqlite3` -> **0**,
confirming R3's separation of the prescribed pattern from R2b's looser `TODO-.*-008` probe. Recommend
recording the count as **"8 as re-derived at review, self-inflating by one per artifact paragraph that
quotes the pattern; 0 real anchors"** rather than a bare integer — a figure that a pass changes by
writing it down should never be reported as a bare integer.

### DRY findings

None. R3 introduces no abstraction, no helper, and no code. The one structural DRY decision — carrying
the deferred-work catalog **by reference** to `bld-008-r2-spec_reconciliation.md:2409` rather than
copying it — is correct and is the right call under the existence challenge: a second copy of a
ten-entry catalog in a cycle with an active `bld-final.md` ahead of it is exactly the duplication that
goes stale. The disposition table adds only the delta (dispositions + three R2b additions), which is
the minimum non-duplicating shape.

### Catalog integrity — re-derived against the source block

Read `bld-008-r2-spec_reconciliation.md:2409` end-to-end and structurally parsed rather than skimmed.

- **10 numbered entries; items 1-8 under `**For R3's \`### Deferred work catalog\`:**`; items 9-10
  under the separate `**Standing, for whoever runs the remaining rounds:**` sub-heading.** R3's
  "**ten numbers, eight items**" is exact. (The block also carries a *separate* 1-4 list for R2b above
  it, which is not part of this catalog and is correctly not counted.)
- **Every one of the ten appears in R3's disposition table, in order, with no silent drop.** I walked
  source-item -> table-row one at a time; the abbreviations are faithful to the source text.
- Dispositions checked individually:
  - **1** (spec-010 `#"exactly as required by"` -> `spec-009 (1076-1077)` stale): OPEN. Verified
    present at HEAD — `spec-010:408` carries the citation verbatim. Correct.
  - **2** (spec-009 Layer 3, two inbound citations): OPEN. Both verified on disk — `(670-687)` at
    `spec-010:65` and `(1076-1077)` at `:408`. Correct.
  - **3** (rule-27 debt): OPEN, carried with framing. See below.
  - **4** (`testing/relay.py`'s `(or build the schema)`): R2 wrote **DISPATCHED, not deferred**; R3
    writes **CLOSED by R2b**. Not a drop — a state advance, and the stronger of the two. Verified: the
    string is gone from `testing/relay.py` and the corrected message is pinned at
    `tests/testing/test_relay.py:186`.
  - **5** (`spec-010:513` phase-2/3 partial mutation): CLOSED as not-a-defect, with the distinction
    R2 drew (partial mutation real; only the *recovery* claim was stale) preserved intact. Correct.
  - **6** (card 8's two `Verified in upstream` `CardItem`s): OPEN as maintainer observation —
    **re-verified by read-only ORM query this review**, see Audit 3 below.
  - **7** (`KANBAN.md:248` one target too many): OPEN as maintainer observation — **re-verified with
    counts**, see Audit 2 below.
  - **8** (`docs/review/` escalation): OPEN and unresolved. Untouched.
  - **9 / 10**: correctly separated as process carry-forward, not deferred work; 10 is re-derived
    rather than restated, which is what its own text asks for.
- **The four required additions are all present and all verified:**
  - **M1 is catalogued as landed, not deferred** — `tests/testing/test_relay.py:186` reads
    `assert "first (directly, or by importing a schema module that calls it)" in message`. Confirmed
    on disk, and it is the clause's **only** occurrence in `tests/`.
  - **The durable runtime-value rule** is stated and is itself true: `testing/relay.py:73-74` splits
    the message across adjacent literals, and `grep -c 'importing a schema module' django_strawberry_framework/testing/relay.py`
    -> **0** for text that is present in the raised string. The rule ("audit the assembled value, never
    the source text") is correctly generalized.
  - **Decision 6's spec-009 deferral is present** — plan `#### Maintainer decision 6` defers spec-009's
    Layer 3 auto-trigger prose, and catalog items 1 and 2 are both anchored on spec-009's
    `### Layer 3: Finalization trigger`. R3's "confirmed present; nothing to add" is right.
  - **Item 3's framing survives intact** — R3 carries 42 / 30, 20 / 15 in-repo, 22 / 15 third-party,
    the two pseudocode sites (`:299`, `:383`), **and** the load-bearing half: `spec-010:554`
    `## Note on source line references` *institutionalizes* the practice, so closure is a conversion
    **plus a section retirement** and needs a maintainer decision authorizing spec-010 edits outside
    decisions 1-8. I confirmed `## Note on source line references` exists at `spec-010:554`. R3's stated
    reason for not re-deriving the integers — re-sweeping a file this cycle may not edit, when the
    framing rather than the integer is load-bearing — is a legitimate and *declared* non-derivation, not
    a silent one, and it is the correct call.

**Catalog verdict: intact.** Nothing dropped, nothing double-counted, every disposition defensible.
`bld-final.md` can carry it forward as written.

### Audit verdicts

#### Audit 1 — durable docs: **conclusion CONFIRMED**, one Medium and one Low in its evidence

**The seven-phase mapping was re-derived independently**, statement by statement, from
`types/finalizer.py::finalize_django_types` (`:664`-`:971`) against `docs/GLOSSARY.md`
`` ## `finalize_django_types` ``. It is the load-bearing claim and it **holds in full**:

| Glossary phase | Statement(s) in source, in body order | Order |
|---|---|---|
| 1. audit primary ambiguity + resolve pending failure-atomically | `_audit_primary_ambiguity(multi_type_models)`; the `unresolved`/`resolved`/`consumer_authored` collection loop; `if unresolved: raise ConfigurationError(_format_unresolved_targets_error(...))` **before** the `__annotations__` rewrite loop; `registry.discard_pending(...)` | 1 |
| 2. attach generated relation and file resolvers | one loop: `_attach_relation_resolvers(..., skip_field_names=definition.consumer_assigned_relation_fields)` then `_attach_file_resolvers(..., skip_field_names=definition.consumer_authored_fields)` | 2 |
| 3. interfaces, Relay defaults, keyset cursor columns | next loop: `apply_interfaces` -> `_check_composite_pk_for_relay_node` / `install_relay_node_resolvers` / `install_globalid_typename_resolver` -> `validate_cursor_field_columns` under `if definition.cursor_field is not None` | 3 |
| 4. synthesize relation connections | `_synthesize_relation_connections()` | 4 |
| 5. audit GlobalID routing, reset emit namespaces, bind auth/mutations/forms/filtersets/ordersets | `_audit_model_label_routing` + `_warn_model_label_secondary_collapse`; `for clear in iter_subsystem_clears(before_bind=True): clear()`; `bind_auth_mutations` (guarded `loaded_attr`); `bind_mutations()`; `bind_form_mutations()`; `_bind_filtersets()`; `_bind_ordersets()` | 5 |
| 6. audit the complete field surface | the `_audit_field_surface(type_cls, definition)` loop | 6 |
| 7. `strawberry.type(...)`, mark each definition finalized, then mark the registry finalized | final loop `strawberry.type(...)` + `definition.finalized = True`; `registry.mark_finalized()` as the **last** statement | 7 |

**Independently confirmed alongside it:**

- **No-op re-entry:** `if registry.is_finalized(): return` is the function's first statement.
- **Post-finalization registration raises:** `types/base.py:532` — `f"finalize_django_types() already ran; cannot register {cls.__name__} "`.
- **The three dependency claims the entry states as a build contract all hold in the body order:**
  keyset validation (phase 3) precedes `_synthesize_relation_connections()` (phase 4); synthesis
  precedes `_bind_filtersets()` / `_bind_ordersets()` (phase 5); `_audit_field_surface` (phase 6) runs
  after every declared, converted, synthesized and sidecar-derived field is visible and before phase 7
  freezes the class.
- **The unresolved-target error names all three elements:** `finalizer.py:97` emits
  `"… {pending.related_model.__name__} (no registered DjangoType)"` on a line carrying source model,
  field name, and target model.
- **`## Schema audit`:** `optimizer/extension.py::DjangoOptimizerExtension.check_schema` warns (never
  raises), dedupes `(model, field_name)` via a `seen` set, skips hidden and `OptimizerHint.SKIP`
  fields. Every clause present.

**One observation, not a finding.** Three statements sit between the seven phases and are unmentioned
by both the glossary and R3: the `_validated_globalid_setting()` snapshot and its
mixed-strategy `ConfigurationError` (before phase 1), and the `_node_fields_declared` no-Node-types
check (between phases 3 and 4). The glossary entry is an ordering **contract**, not a statement
inventory, and it says so ("New finalization work must enter the phase that preserves those
dependencies"), so nothing in it is wrong. But R3's claim is "walked *statement by statement*", and
three statements were not placed. Worth naming so a future audit that finds them does not read them as
drift.

**Concurrency note that does not disturb the audit.** `docs/GLOSSARY.md` is now ` M` (it was clean at
R3's read). `git diff -U0 -- docs/GLOSSARY.md` -> **4 hunks, +5/-1, all between lines 27 and 63** —
the re-exported-symbols index gaining `DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY`,
`DjangoMutationExecutionContext`, `DjangoSchema`, and a `__version__` anchor. A concurrent
transport/config session's work; it touches **none** of the three audited entries (`:490`, `:900`,
`:1801`). Audit 1's conclusions are unaffected. Not R3's, not touched, not reverted.

#### Audit 2 — cross-reference sweep: **CONFIRMED in full, every figure exact**

Both *discharges* re-derived rather than accepted:

- **spec-001 no longer names spec-008.** `grep -c 'spec-008' docs/SPECS/spec-001-django_types-0_0_1.md`
  -> **0**. `:66` reads "`spec-010-foundation-0_0_4.md` owns that pass; this spec owns what subclass
  creation collects." Edit 1 landed; the plan's table row is discharged, exactly as R3 says.
- **spec-010's two line-range citations are gone.**
  `grep -nE 'spec-008[^ ]*\.md.? \([0-9]+-[0-9]+\)' docs/SPECS/spec-010-foundation-0_0_4.md` -> **0
  matches (exit 1)**. `:48` cites `#"### The finalization trigger"`, `:408` cites
  `#"### The shape that shipped"`. Edit 3 is at `:65` with the `spec-009 … (670-687)` range restored.

| Claim | Unit | Re-derived |
|---|---|---|
| inbound namers | files | **14** — exact, and the file list matches R3's table one-for-one |
| `KANBAN.md` | occurrences / lines | **7 on 5** — the unit distinction R3 drew is correct |
| `KANBAN.html` | occurrences / lines | **6 on 1** |
| `spec-010` | occurrences / lines | **7 on 4** (`:5`, `:48`, `:408`, `:557`) |
| `spec-009` | occurrences | **1** |
| `build-001` / `-002` / `-006` | occurrences | **2 / 1 / 3** |
| `convert_relation` per spec | occurrences | spec-008 **0**, spec-009 **3**, spec-010 **2**, spec-018 **2**, spec-019 **3** |
| link defs resolving | link-def lines | spec **22/22**, rationale **29/29**, **0 missing** (re-walked with a parser, each path existence-checked from its own file's directory) |
| `check_spec_glossary --spec` | — | `OK: 10 terms - all have glossary entries and at least one spec link.` exit 0 |

**`KANBAN.md:248` sanity-check (record-only, correctly not fixed).** The board item's parenthetical
reads "the present-tense survivals in shipped specs (`spec-008`, `spec-009`, `spec-010`, `spec-019` all
still name …" — spec-008 is at **0**, so the item names one spec too many. Generated from the DB;
recording is the right disposition.

**R3's flagged judgement call — I agree with it.** `spec-018-meta_primary-0_0_6.md` carries
`convert_relation` twice, at `:139` ("was historically referenced as `convert_relation`") and `:527`
("(was historically `convert_relation`)"). Both are explicitly past-tense provenance, not the
present-tense survival the board item sweeps, so its omission from the list is **correct** and the
board item has exactly **one** error, not two. Do not add spec-018.

#### Audit 3 — `SpecDoc.path` / terms CSV: **CONFIRMED in full; nothing written**

All queries read-only (`manage.py shell -c` with reads and one `--check` command; no `save()`, no
`create()`, no migration, no regenerate).

- `SpecDoc.objects.filter(card=Card.objects.get(number=8))` -> `['docs/SPECS/spec-008-definition_order_independence-0_0_4.md']`
  — already the archived path, no repoint. `Card` reads `DONE-008-0.0.4` / `done` / `0.0.4` /
  "Definition-order independence design".
- **10 / 10 / 10, and the one-row-per-anchor property holds.** CSV data rows (`tail -n +2 | wc -l`)
  **10**; distinct anchors (`cut -d, -f2 | sort -u | wc -l`) **10**; `card.glossary_links.count()`
  **10**. Because rows == distinct anchors, no anchor is duplicated — which is the importability
  property `worker-0.md` `### DONE-card invariants` warns a green `check_spec_glossary` does not prove.
  R3 named exactly that, and it is true.
- **Exact set match, both directions**, computed as a set difference rather than eyeballed:
  `set(db) - set(csv)` = `set()` and `set(csv) - set(db)` = `set()` over
  `configurationerror`, `definition-order-independence`, `djangoconnectionfield`, `djangonodefield`,
  `djangotype`, `finalize_django_types`, `metafields`, `metaprimary`, `relay-node-integration`,
  `schema-audit`.
- **All ten are live targets in `docs/GLOSSARY.md`**, counting `(#anchor)` references: 54 / 7 / 22 / 9 /
  37 / 18 / 8 / 4 / 18 / 6 — min 4, max 54, matching R3's stated "range 4-54".
- `import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0.
- **Card 8's `CardItem`s: 6 rows across 3 sections** — 3 `Scope` `is_complete=True`, **2
  `Verified in upstream` `is_complete=False`**, 1 `Note` `True`. Catalog item 6 re-verified exactly as
  recorded, and the two incomplete rows are indeed in a section that is not a `Definition of done`.
  **No DB write.**

#### Audit 4 — staged anchors: **conclusion CONFIRMED (0 real anchors)**, count stale per L2

Covered under L2. The subtlety R3 identified is real and correctly handled; only the reported total was
taken mid-write.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are byte-unchanged from HEAD. R3 touches no `.py` file at all, so no public-surface change is possible.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md` (`git diff -- CHANGELOG.md` -> empty).

### Documentation / release sanity

R3's diff is a single new `docs/builder/` artifact and modifies no documentation, release metadata,
KANBAN, or archived-spec surface. The checks that *do* apply to what R3 audited are discharged above:
version strings and card IDs match (`DONE-008-0.0.4` / `0.0.4`); no KANBAN card moved; every link
definition in the spec and rationale resolves on disk (22/22, 29/29); the archival preserves the
historical record with the live follow-up source of truth in the durable docs; and no obsolete
"planned"/"coming soon" wording remains in the audited entries. The `README.md`-masking trap is
correctly reported as not live — neither file defines a `README.md` target at any depth, and the
rationale's only upward def, `[glossary]: ../../GLOSSARY.md`, resolves to `docs/GLOSSARY.md` with no
same-named decoy one level up. Re-verified.

### Failability proofs / hot-path budget / floor verification

**Correctly declared not-applicable, and the declaration is auditable rather than asserted.** R3
introduces no boundary, guard, gate, or rejection path (boundary count **0**) because its diff contains
no executable line in any tree — `git status --short` shows its single entry as an untracked `.md`.
The conditional form R2b attached to the plan's `Hot-path declaration: none` and
`Floor-verification scope: none` ("the condition is no executable line changes") is therefore
undisturbed. My mandatory re-run floor is empty **legally**: the diff introduces no boundary that meets
it. No source mutation was made or needed.

### What looks solid

- **The seven-phase mapping is genuinely verified, not skimmed.** This was the claim most likely to be
  a rubber stamp and it survived an independent statement-by-statement walk with all three of its
  dependency corollaries. That is the audit's centre of gravity and it is sound.
- **Audit 2 and Audit 3 are exact.** Every one of ~20 figures re-derived to the digit, including the
  two unit distinctions (7-occurrences-on-5-lines; occurrences vs. matching lines) that the cycle's
  signature defect exists to catch, and the set-difference-both-directions anchor check.
- **The spec-018 judgement call was flagged for a second opinion and is correct.** Volunteering the one
  ruling that could go either way, with the evidence to overturn it, is the right instinct.
- **The R2b/prescribed-pattern separation in Audit 4** correctly attributes a prior binary hit to a
  looser probe instead of leaving two passes contradicting each other — and `grep -acE` of the
  prescribed pattern against `db.sqlite3` really is **0**.
- **Carrying the catalog by reference** rather than copying it, with a disposition column as the only
  addition, is the right DRY shape for a cycle that still has `bld-final.md` ahead of it.
- **`docs/review/` was observed through `git status` alone** and nothing was touched, restored, or
  reverted. The new evidence is reported as evidence with the escalation explicitly left open, which is
  the correct posture.

### Working-tree delta since R3's read

`git status --short | wc -l` -> **51** (R3 recorded 49); `HEAD` unmoved at
`947f74948c16b20b0c15ff359bb53fbe462d4b8c`. Every delta is a concurrent session's, none is R3's, and
**nothing was edited or reverted by this review**:

- new ` M`: `django_strawberry_framework/_request_body.py`, `connection.py`, `docs/GLOSSARY.md`,
  `tests/test_connection.py` — the concurrent transport/config session, consistent with the
  re-export-index hunks in the `GLOSSARY.md` diff above.
- new `??`: `docs/review/rev-_request_body.md`, `rev-connection.md` — the same session's review
  artifacts.
- `docs/review/` state as stated in dispatch is confirmed: **five ` M`, zero ` D`** across
  `rev-_cross_web_patches.md`, `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`,
  `rev-conf.md`. Observed via `git status` only; not read for content, not touched.

**Scope confirmed: R3's diff is exactly one file** —
`?? docs/builder/bld-008-r3-doc_completion_archive.md`. No spec, no rationale, no durable doc, no
source, no test, no `KANBAN*`, and no DB write is attributable to R3. Every other entry traces to
R1/R2/R2b or to a concurrent session.

### Temp test verification

None used. `docs/builder/temp-tests/spec-008-r3/` was not created; every question this review raised
was settled by `grep`, a link-def parser, a read-only ORM query, and reading
`types/finalizer.py::finalize_django_types` end to end. No `pytest` run (R3 changes no code), and no
`--cov*` flag anywhere.

### Notes for Worker 1 (spec reconciliation)

- **No spec defect and no durable-doc defect was found.** I agree with R3: the spec surface closed with
  R2 and nothing here reopens it. M1, L1, and L2 are all corrections **inside this artifact**; none
  requires touching `docs/GLOSSARY.md`, `docs/README.md`, any spec, or the DB, and none changes an
  audit verdict. The fix is arithmetic plus one narrowed sentence.
- **Carry to `bld-final.md`:** the catalog is intact at ten numbers / eight items with the dispositions
  above; item 3's institutionalizing framing must survive the copy, and item 8 stays open.
- **For the final gate's own count discipline:** the `cardinalit` figure travelled un-re-derived from
  the pre-flight through the dispatch prompt into the artifact. When `bld-final.md` restates a figure it
  did not measure, mark it as *carried* the way R3 correctly marked the rule-27 integers, rather than
  letting it read as re-derived.

### Review outcome

`revision-needed`. One Medium (M1) and two Lows (L1, L2), none of which changes an audit verdict and
all of which are corrections to this artifact's recorded evidence. **All four audits' conclusions are
confirmed by independent re-derivation, the deferred-work catalog is intact, and procedural closure is
earned on the substance** — R3's diff really is one new file, nothing writable was owed, and no
durable surface is wrong. What is not yet earned is the *record*: a read-only audit's product is its
evidence, and three figures in it do not survive re-derivation, one of them carrying a false absolute.
Per plan `### Deviation 2` this routes to **Worker 1**, which sets `planned` again and returns the
artifact to the `planned` -> Worker 3 mapping.

---

## Build report (Worker 1, R3 pass 2 — evidence corrections)

Scope: Worker 3's M1, L1, L2. **No audit was re-run** — all four conclusions were confirmed by
independent re-derivation and no re-audit is owed. Nothing outside this artifact was written; the
diff of this pass is this block plus the header `Status:` field.

Prior blocks are left byte-intact (`ARTIFACT.md:187`, "never edit prior entries"); the corrections
below **supersede** the corresponding rows above. This block is appended at the end of the file, so
every line citation written above it — `:239`, `:485`, `:566`, and the checklist box itself — keeps
its target; no shift arithmetic is owed.

Re-derivation environment: `HEAD` = `947f74948c16b20b0c15ff359bb53fbe462d4b8c` (unmoved through all
three passes); working tree **52** `git status --short` entries at the start of this pass (`git status
--short | wc -l`; unit: status lines), up from Worker 3's 51 and R3's 49. Every count in the dispatch
prompt, including Worker 0's 42 / 12, was re-derived from disk before being written here.

### Superseding counts table

| Figure | Unit | Derivation command (run from the repo root) | Superseded value | Corrected value |
|---|---|---|---|---|
| `cardinalit` in the package | matching lines | `grep -rniE 'cardinalit' django_strawberry_framework/ \| wc -l` | 9 | **42** |
| same | occurrences | `grep -roiE 'cardinalit' django_strawberry_framework/ \| wc -l` | 9 | **42** (one per line — the two units coincide) |
| same | files | `grep -rliE 'cardinalit' django_strawberry_framework/ \| wc -l` | (unstated) | **12** |
| `finalize_django_types()` in the package | matching lines | `grep -rn 'finalize_django_types()' django_strawberry_framework/ \| wc -l` | 46 | **45** |
| same, at HEAD | matching lines | `git grep -c 'finalize_django_types()' HEAD -- django_strawberry_framework/` summed | 46 | **45** (so not concurrent drift) |
| same | call sites | `grep -rnE '^\s*(await )?(\w+\.)?finalize_django_types\(\)' django_strawberry_framework/` | 0 | **0** — unchanged, exit 1, no match |
| staged anchors outside `docs/builder/` | matching lines | the prescribed `grep -rEn` below, piped to `grep -cv '^docs/builder/'` | (not measured) | **0** — the edit-stable form; see below |
| this artifact's checklist-box self-citation | line number | `grep -n 'TODO(spec-008' <this file>` | `:55` | **`:56`** |

### M1 — the `cardinalit` row of Audit 1, corrected

**Corrected figure: 42 matching lines across 12 files, one occurrence per line.**
Derivation, all three units, run from the repo root:

- `grep -rniE 'cardinalit' django_strawberry_framework/ | wc -l` -> **42** (unit: matching lines)
- `grep -roiE 'cardinalit' django_strawberry_framework/ | wc -l` -> **42** (unit: occurrences)
- `grep -rliE 'cardinalit' django_strawberry_framework/ | wc -l` -> **12** (unit: files)

Occurrences and matching lines coincide, so this is **not** the line-vs-occurrence unit trap that has
fired repeatedly in this cycle; it is a figure that was named with a correct unit and never measured.
No sub-scoping of the command reproduces 9 (`types/` alone -> 6, `filters/` alone -> 11).

Per-file distribution (`grep -rciE 'cardinalit' django_strawberry_framework/ | grep -v ':0$'`; unit:
matching lines per file), which sums to 42 and is the check the superseded row's sub-enumeration
failed:

| File | Lines | What the mentions are |
|---|---|---|
| `filters/sets.py` | 11 | lookup-primitive / filter-class selection by relation cardinality |
| `optimizer/field_meta.py` | 9 | the single-source cardinality classifier and its nullable gate |
| `utils/relations.py` | 6 | the shared relation classifier |
| `types/resolvers.py` | 3 | generated-resolver shape dispatch |
| `management/commands/inspect_django_type.py` | 3 | introspection output |
| `optimizer/walker.py` | 2 | join-strategy dispatch |
| `optimizer/hints.py` | 2 | `force_select` / `force_prefetch` override docs |
| `types/base.py` | 2 | `_validate_relation_shape_targets`'s docstring (`:1513`, `:1523`) |
| `types/converters.py` | 1 | annotation-construction narrative |
| `optimizer/join_taxonomy.py` | 1 | taxonomy table |
| `optimizer/extension.py` | 1 | cache-key sizing (unrelated sense) |
| `extensions/resource_policy.py` | 1 | input-argument bounds (unrelated sense) |

**"0 of them a validator" was false and is withdrawn.** It is false twice over, and the second reason
is the durable one: **all 42 hits are comment or docstring text — the token `cardinalit*` appears in
zero executable statements in the package** (every line listed by the command above is inside a `#`
comment or a `"""` docstring). A word-grep therefore cannot decide whether a validator exists; a
validator is found by what it *reads*. `django_strawberry_framework/types/base.py::_validate_relation_shape_targets`
is one: its docstring says so at `:1523` ("Cardinality is read from ``FieldMeta.is_many_side``…") and
its executable test is at `:1556`, `if not field_map[snake_case(name)].is_many_side:` raising
`ConfigurationError`.

**Corrected row for Audit 1's `docs/GLOSSARY.md` `## Definition-order independence` table** (this row
supersedes the one at `:80`):

| Claim | Verification at HEAD+R2b | Verdict |
|---|---|---|
| "Validation that a manual relation annotation matches the Django relation cardinality is deferred." | `grep -rniE 'cardinalit' django_strawberry_framework/` -> **42 matching lines across 12 files (`grep -rliE … \| wc -l` -> 12), one occurrence per line, every one of them comment or docstring text**. Exactly one validator reads relation cardinality: `types/base.py::_validate_relation_shape_targets` (`:1523` docstring, `:1556` test), and it checks **`Meta.relation_shapes` keys** against the relation's cardinality — a different surface. **No check compares a consumer-authored relation annotation against the Django relation's cardinality.** | holds (still deferred) |

The narrowed sentence, stated once so it can be quoted: *no check compares a consumer-authored
relation annotation against the Django relation's cardinality; the one cardinality-reading validator,
`types/base.py::_validate_relation_shape_targets`, validates `Meta.relation_shapes` keys, which is a
different surface.*

**`docs/GLOSSARY.md` is untouched and is correct as written** — the deferral sentence is accurate, the
narrowing is to *this artifact's evidence*, not to the durable claim. (It is DB-generated regardless,
so an edit there would be an ORM change plus a regenerate, which this cycle does not own.) Audit 1's
verdict is unchanged: **accurate and complete; no durable-doc edit is owed.**

### L1 — `finalize_django_types()` package count is 45, not 46

Supersedes both recorded sites (Audit 1's `docs/README.md` paragraph and the counts table row).

- `grep -rn 'finalize_django_types()' django_strawberry_framework/ | wc -l` -> **45** (unit: matching lines)
- `grep -rno 'finalize_django_types()' django_strawberry_framework/ | wc -l` -> **45** (unit: occurrences; one per line)
- `git grep -c 'finalize_django_types()' HEAD -- django_strawberry_framework/`, summed -> **45** — the
  same at HEAD, so the correction is arithmetic, not concurrent drift.

**The load-bearing half is unchanged and re-confirmed.**
`grep -rnE '^\s*(await )?(\w+\.)?finalize_django_types\(\)' django_strawberry_framework/` -> **no
match, exit 1**: **0 call sites** (unit: call sites). The only non-string, non-comment occurrence is
the `def` at `types/finalizer.py:664` (`grep -rn 'def finalize_django_types' django_strawberry_framework/`).
`DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` still do not call it, so
`docs/README.md #"Schema setup boundary"` **holds** and D3's negative is intact.

### L2 — the staged-anchor sweep, restated in a form that survives this edit

The prescribed sweep, run from the repo root:

```
grep -rEn 'TODO\(spec-008|TODO-(ALPHA|BETA|STABLE)-008' . \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md --exclude-dir=.git
```

**The raw total is not a reportable figure, and reporting one is the defect repeating.** This
artifact's own text matches the sweep's pattern, so every paragraph that quotes the pattern — Worker
3's review block, and this correction block — raises the total. R3 named that mechanism and then
published a bare integer taken mid-write (6); Worker 3 re-derived 8 at review; this block adds more
again. A number that its own publication changes cannot be the verdict.

**The edit-stable derivation, which no amount of writing about the sweep can move:**

```
grep -rEn 'TODO\(spec-008|TODO-(ALPHA|BETA|STABLE)-008' . \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md --exclude-dir=.git \
  | grep -cv '^docs/builder/'
```

-> **0** (unit: matching lines outside `docs/builder/`). **That is the anchor count: 0 real staged
anchors, tree-wide.** No package source, test, example, spec, or durable doc carries one. The
complement is definitionally the cycle's own paperwork, and `grep -rEl` for the same pattern returns
exactly three files, all of them `docs/builder/` artifacts of this cycle:
`build-008-definition_order_independence-0_0_4.md`, `bld-008-r2b-source_attribution.md`, and this
file.

Snapshot totals, useful only as history and each stamped with when it was taken (unit: matching lines):
**6 as R3 wrote it**, **8 as Worker 3 re-derived it at review**, and a larger figure the moment this
block lands. Every increment is `docs/builder/` prose. `grep -acE '<prescribed pattern>'
examples/fakeshop/db.sqlite3` -> **0**, re-confirmed this pass, so R3's separation of the prescribed
pattern from R2b's looser `TODO-.*-008` probe stands. The two loose probes are likewise not
edit-stable and are recorded only as snapshots: at this pass `grep -rn 'TODO(spec-008' . | wc -l` ->
**8** and `grep -rn 'TODO-.*-008' . | wc -l` -> **15** (R3 recorded 6 / 8), the second inflated
further by unexcluded generated files.

**Self-citation corrected:** the sweep table's row for "this artifact's own checklist box" cites
`:55`; the box is at **`:56`** (`grep -n 'TODO(spec-008' docs/builder/bld-008-r3-doc_completion_archive.md`
-> `56`, plus `:251` and `:384`, the other two self-matching lines that produced Worker 3's 8).

**Proof that the form survives its own publication**, run after this block was written to disk: the
raw total moved **8 -> 11** (unit: matching lines) purely from the paragraphs above, while the
edit-stable derivation `... | grep -cv '^docs/builder/'` read **0** both before and after. That is the
whole argument for reporting the second number and not the first.

**Audit 4's conclusion is unchanged and independently re-confirmed: 0 real staged anchors.**

### The class this pass records: a read-only audit's product IS its evidence

R3 is the clearest instance in this cycle, so it is worth stating as a rule rather than as three
corrections. For R1 and R2 the artifact was scratchpad and the spec was the deliverable, which is why
an artifact-only count error there was correctly filed Low. **R3 ships no durable file at all.** Its
four audits changed nothing; the entire product is the recorded evidence, and that evidence is what
`bld-final.md` carries forward under `BUILD.md` `## Final test-run gate`. So a figure that fails
re-derivation is **not a cosmetic slip in the packaging of a correct conclusion — it is a defect in
the deliverable itself**, indistinguishable in kind from shipping a wrong line of code. "The verdict
still holds" is exactly as much comfort as "the feature still works" is for a wrong implementation:
true, and beside the point.

The mechanism that produced it is worth naming too. **The `9 occurrences / 0 validators` pair
travelled un-re-derived through three hops** — Worker 0's pre-flight finding, the R3 dispatch prompt
that quoted it, and this artifact, whose own preamble reads "Every figure the dispatch carried was
re-derived rather than trusted." Each hop's reader treated the previous hop's confidence as the
derivation. A figure inherited three times is not three times verified; it is one unverified figure
with three witnesses. The countermeasure is the one this cycle already writes down and this block
applies literally: **every count carries its unit and the command that produced it**, and the command
is re-run at the hop that publishes it — including, and especially, when the figure arrives already
stated with confidence.

The `0 validators` half adds a second lesson, narrower and reusable: **an absolute proved by a
keyword grep is only as good as the assumption that the thing being denied would contain the
keyword.** All 42 `cardinalit*` hits are comments and docstrings; the validator that reads cardinality
does so through `FieldMeta.is_many_side` and would never have appeared in that grep's output at all.
An absence claim needs an instrument aimed at the mechanism, not at the vocabulary.

### Spec slice checklist

Unchanged and still correct: all four boxes at `:53`-`:56` are `- [x]`, all four audits were performed
in the original pass, and Worker 3 confirmed all four conclusions. Nothing in this pass un-ticks a box.

### Validation run

- No `ruff` run: this pass's diff contains no `.py` file.
- No `pytest` run: no code changed; `--cov*` flags are banned regardless.
- `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-008-r3-doc_completion_archive.md`
  -> recorded below with its result.
- `git status --short` after the pass: re-derived below; this artifact is the only entry attributable
  to R3, and **nothing outside R3's writable set was written, edited, or reverted** — in particular
  nothing under `docs/review/` (still five ` M`, zero ` D`, observed through `git status` alone) and
  not `docs/GLOSSARY.md`, which is ` M` from a concurrent session's re-export-index change and was
  left exactly as found.

### Failability proofs / hot-path budget / floor verification

**Not applicable, declared rather than omitted**, on the same grounds as the original pass and
undisturbed by it: no boundary, guard, gate, or rejection path was introduced (boundary count **0**),
and no executable line changed in any tree, so the plan's `Hot-path declaration: none` and
`Floor-verification scope: none` — including the conditional form R2b attached ("the condition is no
executable line changes") — both still hold.

### Notes for Worker 3

- **M1, L1, L2 are all corrected above, each with its unit and its derivation command inline**, so
  every figure can be re-derived without reconstructing my reasoning. Please re-run them; that is how
  all three of these were found.
- **L2's figure is deliberately not an integer.** The reportable quantity is `... | grep -cv
  '^docs/builder/'` -> **0**, which your own review block and this one cannot move. The totals 6 / 8 /
  more are recorded as timestamped snapshots only.
- **Your M1 sub-enumeration has one arithmetic slip that does not affect the finding**: it lists
  `optimizer/field_meta.py` at 8; `grep -rciE` reads **9**. With 8 the per-file list sums to 41, with 9
  it sums to 42 and closes exactly. The corrected per-file table above is the one to carry.
- **Your `two hops` for the `9 / 0 validators` figure is one short** — Worker 0's pre-flight is the
  origin, the dispatch prompt is the second carrier, the artifact the third. Recorded above as three,
  because the count is the point of the lesson.
- **No audit was re-run and no verdict moved.** Audits 1-4 stand exactly as accepted.

### Notes for Worker 1 (spec reconciliation)

None owed, unchanged. No spec, rationale, durable doc, source file, test, `KANBAN*`, or DB row was
opened by this pass.

### Header status transition

Header `Status:` (line 4) set to **`planned`** in the same action as this block, per the standing fix
for the R2 five-pass header drift. `planned` on an R-item with no Worker 2 routes to **Worker 3** for
re-review, then back to Worker 1 for final verification.

---

## Review (Worker 3, pass 2)

Scope as dispatched: confirm the three evidence corrections and nothing more. **The four audits'
conclusions were settled at pass 1 and were not re-run.** Every figure below was re-derived from disk
with the command Worker 1 recorded, run verbatim from the repo root, before being written here.

Re-derivation environment: `HEAD` = `947f74948c16b20b0c15ff359bb53fbe462d4b8c` (unmoved through all
four passes; `git rev-parse HEAD`); working tree **52** `git status --short` entries (unit: status
lines) — identical to Worker 1's reading at the start of pass 2, up from my 51 and R3's 49.

### High:

None.

### Medium:

None. **M1 is closed at the root**, on both halves.

### Low:

None. **L1 and L2 are both closed.**

### M1 — confirmed, including the per-file table's arithmetic and the universal negative

**The three figures re-derive exactly.**

| Quantity | Unit | Command | Corrected value | Re-derived |
|---|---|---|---|---|
| `cardinalit` hits | matching lines | `grep -rniE 'cardinalit' django_strawberry_framework/ \| wc -l` | 42 | **42** |
| same | occurrences | `grep -roiE 'cardinalit' django_strawberry_framework/ \| wc -l` | 42 | **42** |
| same, greedy form | occurrences | `grep -rnoiE 'cardinalit[a-z]*' django_strawberry_framework/ \| wc -l` | (implied 42) | **42** |
| same | files | `grep -rliE 'cardinalit' django_strawberry_framework/ \| wc -l` | 12 | **12** |
| sub-scoping | matching lines | `grep -rniE 'cardinalit' django_strawberry_framework/{types,filters}/` | 6 / 11 | **6 / 11** |

**Verdict on the per-file table's arithmetic: it closes, to the digit, and so does its membership.**
`grep -rciE 'cardinalit' django_strawberry_framework/ | grep -v ':0$'` returns exactly the twelve
files of the published table with exactly its twelve per-file figures — `filters/sets.py` 11,
`optimizer/field_meta.py` **9**, `utils/relations.py` 6, `types/resolvers.py` 3,
`management/commands/inspect_django_type.py` 3, `types/base.py` 2, `optimizer/walker.py` 2,
`optimizer/hints.py` 2, `types/converters.py` 1, `optimizer/join_taxonomy.py` 1,
`optimizer/extension.py` 1, `extensions/resource_policy.py` 1. Sum: 11+9+6+3+3+2+2+2+1+1+1+1 = **42**
(unit: matching lines), and the file set is the same set, not merely the same size — so the table is
not just internally consistent, it is the command's own output.

**The slip Worker 1 reports in my predecessor's list is real, and I confirm the arithmetic it
implies.** The pass-1 enumeration at `:502` lists `optimizer/field_meta.py` at 8; disk reads 9. Summing
that list as written — 4 (`types/resolvers.py` 3 + `types/converters.py` 1) + 11 + 8 + 2 + 2 + 1 + 1 +
6 + 2 + 3 + 1 — gives **41** against its own stated total of 42. With 9 it closes at 42. A per-file
table is worth exactly its arithmetic, and this one is the first version of the figure in this cycle
that can be checked against itself; it is also what made the slip visible at all.

**Verdict on the "zero executable statements" universal negative: CONFIRMED, by a different instrument
than the one that produced it.** This is a universal claim over 42 hits and the load-bearing half of
the correction, so an eyeball pass over the grep output is not enough evidence for it. I tokenized
instead: for every `.py` file under `django_strawberry_framework/`, `tokenize.tokenize` collected the
line spans of every `COMMENT` and `STRING` token whose text matches `cardinalit` (case-insensitive),
and `ast.parse` collected the line spans of every module / class / function docstring; each of the 42
matching lines was then classified.

- total matching lines classified: **42** (the parser's own count, matching the grep)
- **docstring: 32**
- **comment: 10**
- **executable statements: 0**
- non-docstring string literals (an error message, a dict key, a default): **0**

So the claim holds in its strong form: the token occurs in zero executable statements *and* in zero
runtime string values — every one of the 42 is `#` comment text or `"""` docstring text, exactly as
Worker 1 states. That is what makes the withdrawal of "0 validators" the *deeper* correction rather
than a hedge: a word-grep over this package structurally cannot answer "does a cardinality validator
exist", because the mechanism (`FieldMeta.is_many_side`) shares no token with the vocabulary.

**Both cited lines are exact.** `types/base.py:1523` is the docstring sentence "Cardinality is read
from ``FieldMeta.is_many_side``…", and `:1556` is `if not field_map[snake_case(name)].is_many_side:`
raising `ConfigurationError` — checked by `grep -n`, both inside
`types/base.py::_validate_relation_shape_targets` (`def` at `:1500`).

**Verdict on the narrowed sentence: exactly true, neither overclaiming nor vacuous.** I tested it
against the mechanism rather than the vocabulary, since that is the lesson the correction itself
draws: `is_many_side` has readers in 10 files. The one in `types/base.py` is the
`Meta.relation_shapes` key validator above; `types/finalizer.py:542` is Phase-2.5 synthesis, which
reads cardinality to *select* fields and then **skips** `definition.consumer_authored_fields` at
`:544` rather than validating them; the rest (`filters/sets.py`, `optimizer/*`, `types/resolvers.py`,
`types/converters.py`, `utils/relations.py`, `inspect_django_type.py`) are classification, lookup
selection, join strategy, and introspection. Nothing anywhere compares a consumer-authored relation
annotation to the Django relation's cardinality. The sentence's second clause is also true and is not
a weakening: the validator genuinely *does* read cardinality, and it genuinely *is* a different
surface — it rejects a `"connection"` shape on a single-valued relation, which is a `Meta` key check.
`docs/GLOSSARY.md` `## Definition-order independence` #"Validation that a manual relation annotation
matches the Django relation cardinality is deferred." remains accurate and untouched; Audit 1's
verdict `holds (still deferred)` is unchanged.

### L1 — confirmed; all three derivations agree at 45, and 0 call sites re-confirmed

| Quantity | Unit | Command | Corrected | Re-derived |
|---|---|---|---|---|
| working tree | matching lines | `grep -rn 'finalize_django_types()' django_strawberry_framework/ \| wc -l` | 45 | **45** |
| working tree | occurrences | `grep -rno 'finalize_django_types()' django_strawberry_framework/ \| wc -l` | 45 | **45** |
| HEAD | matching lines | `git grep -c … HEAD -- django_strawberry_framework/`, summed with `awk` | 45 | **45** |
| call sites | call sites | `grep -rnE '^\s*(await )?(\w+\.)?finalize_django_types\(\)' django_strawberry_framework/` | 0 | **0** — no match, **exit 1** |

Three independent derivations at 45 with HEAD agreeing is what makes this arithmetic rather than
concurrent drift, and it is stated that way. The `def` is at `types/finalizer.py:664`
(`grep -rn 'def finalize_django_types'`, single hit) — the only non-string, non-comment occurrence.
`docs/README.md #"Schema setup boundary"` holds and D3's negative is intact.

### L2 — confirmed; the edit-invariant form is the right reportable figure, and I walked into the trap it guards

The prescribed sweep, run verbatim from the repo root, **before** this block was written to disk:

- raw total -> **11** matching lines. This equals Worker 1's post-publication reading, and confirms
  their "8 -> 11" claim end-to-end: my pass-1 review measured 8, their correction block added 3.
- `... | grep -cv '^docs/builder/'` -> **0** (unit: matching lines outside `docs/builder/`).

**The filter form matters and the prompt's warning is accurate.** The same pipeline written as
`grep -cv '^\./docs/builder/'` returns **11**, not 0: `grep -rn .` in this environment emits
`docs/builder/…` with no `./` prefix, so the leading-`./` anchor matches nothing and the filter
silently passes everything through. I ran both forms rather than only the recorded one, precisely so
the 0 is a measurement and not a formatting coincidence.

**Every remaining hit really is `docs/builder/` self-documentation.** I did not take the filter's word
for it — `grep -rEl` for the same pattern returns exactly three files
(`build-008-definition_order_independence-0_0_4.md` 3 hits, `bld-008-r2b-source_attribution.md` 2,
this artifact 6), all of them this cycle's own scratchpads, and `cut -d: -f1 | sort | uniq -c` over
the raw hits accounts for all 11. No package source, test, example, spec, durable doc, `KANBAN*`, or
DB row carries one. `grep -acE '<prescribed pattern>' examples/fakeshop/db.sqlite3` -> **0**,
re-confirmed.

**The claim that the form survives its own publication is the point and it is proved twice over.** My
own block quotes the pattern again, so the raw total will move again while the invariant stays 0; the
snapshot to carry is therefore **"11 as re-derived at re-review pass 2, pre-publication of this
block"**, and the reportable figure is **0 real staged anchors, tree-wide**. Worker 1's loose-probe
snapshots are likewise correctly labelled snapshot-only: they read **11** and **19** at my pass
(Worker 1 recorded 8 / 15, R3 6 / 8), which is the expected monotone growth and not drift.

**Self-citation `:55` -> `:56` confirmed.** `grep -n 'TODO(spec-008' docs/builder/bld-008-r3-doc_completion_archive.md`
puts the staged-anchor checklist box at **`:56`**; `:55` is the `SpecDoc.path` / terms-CSV box. The
sweep table's row at `:239` still reads `:55` and is superseded, correctly, rather than edited.

**No line citation shifted.** Appending pass 2 at the end cannot move an earlier line by construction,
and I confirmed it by reading rather than assuming: `:53`-`:56` are still the four checklist boxes in
order, `:80` is still the `cardinalit` row, `:239` the self-citing sweep row, `:485` the fenced
`…:80` quotation, `:566` the "two additions" sentence. Every citation written above the new block
still lands on its stated target.

### The recorded class — accurate, and it earns its length

**"A read-only audit ships no durable file, so its evidence IS its deliverable" is stated accurately.**
It reproduces the inversion correctly in both directions: for R1/R2 the spec was the product and an
artifact-only count error was rightly Low; R3 changes nothing, so its recorded evidence is the whole
product and `bld-final.md` carries it forward under `BUILD.md` `## Final test-run gate`. That is the
same reasoning my pass-1 Medium rested on, restated as a rule rather than as three corrections, which
is the more useful form. The "true, and beside the point" framing of "the verdict still holds" is fair
rather than rhetorical: all four verdicts *did* hold, and the pass was still rejected.

**The three-hop note is accurate as far as disk can settle it, and the correction of my predecessor's
"two hops" is right.** The `9 / 0 validators` pair appears nowhere in
`build-008-definition_order_independence-0_0_4.md` (Worker 0's written pre-flight carries the
cardinality *question* at `:361`/`:377` but no such figure) and nowhere else in `docs/builder/` except
this artifact, so the origin hop is not disk-checkable — but it is not disputable either: the figure
reached the artifact from somewhere upstream of the dispatch, my own pass-1 memory entry independently
recorded the chain as "pre-flight -> dispatch prompt -> artifact" while the artifact text said two,
and counting the origin is the half that makes the lesson land. **A figure inherited three times is not
three times verified; it is one unverified figure with three witnesses** is the sentence worth carrying
to `bld-final.md`.

**The second lesson is the one I would keep if only one survived:** an absolute proved by a keyword
grep is only as good as the assumption that the denied thing would contain the keyword. My tokenize
result is that lesson's proof — 42/42 hits are prose, so the instrument was aimed at the vocabulary
while the mechanism (`is_many_side`) was never in its output. That is reusable well beyond this cycle
and is not bulk.

### DRY findings

None. No abstraction, no helper, no code; the correction block adds a superseding table plus three
keyed sections and does not restate the audits. Carrying the deferred-work catalog by reference is
unchanged and remains the right shape.

### Hygiene

- **Prior blocks byte-intact per `ARTIFACT.md:187`.** The artifact is untracked (`??`), so no `git
  diff` is available; I verified structurally instead, which for an append is decisive: the file's
  prior 1092 lines are unchanged in content at every one of the eight line numbers cited across the
  passes (`:53`-`:56`, `:80`, `:239`, `:251`, `:384`, `:485`, `:566`), the pass-2 block begins at
  `:861` after the `---` at `:859`, and every superseded figure is left in place with a superseding
  pointer rather than rewritten. `:868`'s blanket clause plus a figure-keyed superseding table covers
  the counts-table rows at `:382`/`:384`/`:390`/`:391` as well as the two sites L1 names explicitly.
- `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-008-r3-doc_completion_archive.md`
  -> **exit 0**.
- **R3's diff is still exactly one new untracked file** plus the gitignored memory file:
  `?? docs/builder/bld-008-r3-doc_completion_archive.md`
  (`git check-ignore -v docs/builder/worker-memory/spec-008-worker-3.md` -> `.gitignore:188`). No
  spec, rationale, durable doc, source, test, DB, or `KANBAN*` entry is attributable to R3; every
  other status entry traces to the spec-006/007/008 cycles or to a concurrent session.
- **`docs/GLOSSARY.md` is ` M` from the concurrent session and was neither edited nor reverted** by
  this pass — observed only.
- **Nothing under `docs/review/` was touched.** State re-confirmed: **five ` M`**
  (`rev-_cross_web_patches.md`, `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`,
  `rev-conf.md`), **zero ` D`**, plus four `??` (`rev-_boundary_ordering.md`, `rev-_request_body.md`,
  `rev-connection.md`, `review-0_0_14.md`). Observed through `git status` alone; the escalation
  (catalog item 8) stays open.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty** (0 lines). `__all__` and the
re-export list are byte-unchanged. This pass touches no `.py` file.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable to this pass; its diff is one `docs/builder/` scratchpad block and modifies no
documentation, release metadata, KANBAN, or archived-spec surface. The applicable checks were
discharged at pass 1 and no audit was re-run.

### Failability proofs / hot-path budget / floor verification

Not applicable, and the declaration remains auditable rather than asserted: boundary count **0**, no
executable line changed in any tree, so the plan's `Hot-path declaration: none` and
`Floor-verification scope: none` (with R2b's conditional form, "the condition is no executable line
changes") both still hold. My mandatory re-run floor is empty **legally** — the diff introduces no
boundary that meets it. No source mutation was made or needed. `scripts/review_inspect.py` not run:
no `.py` file is touched.

### What looks solid

- **The per-file table is the right instrument, not just a bigger number.** Replacing a bare total
  with a distribution is what made a wrong figure *checkable*, and it immediately paid for itself by
  surfacing the `field_meta.py` 8-vs-9 slip in my own predecessor's list — a correction pass finding
  a defect in the review that commissioned it is the behaviour the re-derivation rule exists to
  produce, and it was reported rather than quietly absorbed.
- **The deeper reason for withdrawing "0 validators" is the correct one.** "The claim was false"
  would have closed the finding; "the instrument could never have answered the question" closes the
  class. It survived a tokenizer check I ran specifically to try to break it.
- **The narrowing did not overshoot.** The easy failure here was hedging the durable sentence into
  vacuity to be safe; instead the durable sentence is left untouched and correct, and the narrowing is
  applied to the artifact's evidence, which is where the error was.
- **L2's edit-invariant restatement is the right generalization** of a defect my pass-1 review could
  only describe. A figure that its own publication moves is not a figure; subtracting the paperwork is
  the fix, and the "8 -> 11 while the invariant read 0 both times" proof is exactly the demonstration
  the claim needed.
- **The unit and derivation command are attached to every figure in the block**, including the ones
  that did not change (`0` call sites, `0` in the DB binary), so `bld-final.md` can carry them without
  re-deriving my reasoning.

### Temp test verification

None used. `docs/builder/temp-tests/spec-008-r3/` was not created. Every question this pass raised was
settled by `grep`, a `tokenize` + `ast` classifier run through `uv run python`, and reading
`types/base.py::_validate_relation_shape_targets` and `types/finalizer.py` #"is_many_side" in place.
No `pytest` run, and no `--cov*` flag anywhere.

### Notes for Worker 1 (spec reconciliation)

- **Nothing owed.** No spec, rationale, durable doc, source file, test, `KANBAN*`, or DB row is opened
  by this pass or by pass 2. `docs/GLOSSARY.md`'s deferral sentence is correct as written and stays.
- **Carry to `bld-final.md`, in this form:** `cardinalit` = **42 matching lines / 42 occurrences / 12
  files, all comment or docstring text, 0 executable statements**; `finalize_django_types()` = **45
  matching lines, 0 call sites**; staged anchors = **0 outside `docs/builder/`** (never the raw total).
  The catalog is intact at ten numbers / eight items; item 3's institutionalizing framing must survive
  the copy and item 8 stays open.
- **One observation, not a finding:** M1's correction names `:80` as the row it supersedes, while L1
  names both of its sites explicitly. The counts-table row at `:391` (`9 occurrences, 0 validators`)
  is covered by `:868`'s blanket clause and by the figure-keyed superseding table, so nothing is
  ambiguous — but when `bld-final.md` quotes a figure, quote it from the superseding table at `:879`
  rather than from any row above `:861`.

### Review outcome

`review-accepted`. **All three corrections confirmed, none rejected.** M1's per-file table sums to 42
and matches the command's own output file-for-file; the "zero executable statements" universal
negative holds under an independent tokenizer classification (32 docstring + 10 comment + 0
executable + 0 runtime string literal, over all 42 hits); the narrowed sentence is exactly true and
was tested against the mechanism (`is_many_side` readers in 10 files) rather than the vocabulary. L1's
three derivations all read 45 with HEAD agreeing, and the load-bearing 0 call sites re-confirmed at
exit 1. L2's edit-invariant form reads 0 with the recorded filter and 11 with the leading-`./` variant
— I ran both, and every remaining hit is one of exactly three `docs/builder/` files of this cycle; the
`:55` -> `:56` self-citation is right and no earlier line citation shifted. Prior blocks are intact,
`check_trailing_commas --check` exits 0, and R3's diff is still one untracked `.md`. Nothing
unresolved remains; this routes to **Worker 1** for final verification.

---

## Final verification (Worker 1)

Confirm-and-close pass. **No audit was re-run and no figure was re-litigated** — the four conclusions
were confirmed at Worker 3 pass 1, the three evidence corrections were confirmed at Worker 3 pass 2,
and nothing was rejected. This block verifies five things only: R3's shape and its record, the
deferred-work catalog's integrity, the figure-sourcing note, the `### Spec changes made` determination,
and the three `none` declarations against R3's final diff.

Re-derivation environment: `git rev-parse HEAD` -> `947f74948c16b20b0c15ff359bb53fbe462d4b8c`
(unmoved across all five passes). `git status --short | wc -l` -> **52** (unit: status lines),
identical to Worker 1 pass 2's and Worker 3 pass 2's readings. Every figure stated below was re-derived
from disk in this pass with the command shown; nothing is inherited from the dispatch prompt.

### 1. R3's shape — procedural closure, correctly recorded, with one precision worth stating

**Confirmed. R3's diff is exactly one new file plus a gitignored notebook.**

- `git status --short` attributable to R3: **1 entry** (unit: status lines) —
  `?? docs/builder/bld-008-r3-doc_completion_archive.md`. The other 51 trace to concurrent sessions
  or to closed items R1 / R2 / R2b.
- `git check-ignore -v docs/builder/worker-memory/spec-008-worker-1.md` -> `.gitignore:188`; the
  memory files are outside the diff by construction.

**No durable-doc edit was owed** — all four audits found nothing writable, and Worker 3 confirmed all
four conclusions across two passes. **None was made**, verified positively rather than asserted:

- `git status --short docs/README.md docs/TREE.md` -> **0 entries**. Both clean at HEAD.
- `docs/GLOSSARY.md` is ` M`, and the change is not this cycle's: `git diff -U0 docs/GLOSSARY.md |
  grep '^@@'` -> four hunks, `-26,0 +27,2`, `-38,0 +41`, `-44,0 +48`, `-59 +63` — every one inside the
  `#"Symbols re-exported from"` index at lines 27-63, and none within `## Definition-order
  independence` or `` ## `finalize_django_types` ``, the two sections Audit 1 read. Observed only;
  neither edited nor reverted.
- The contingency edit `#### Maintainer decision 3` reserved for R3 was folded into R2 and has landed:
  `grep -cE 'spec-008[^ ]*\.md.? \([0-9]+-[0-9]+\)' docs/SPECS/spec-010-foundation-0_0_4.md` -> **0**,
  exit 1. R3 inherited no edit from it, and none from R2b either.

**The artifact states the shape**, at `## R3's shape` (`:351`), naming `BUILD.md`
`### Procedural-closure slices` and the plan's `### Deviation 2`, as the plan requires ("Worker 1 says
which shape R3 took in the artifact"). **Precision, recorded so a later reader does not mis-cite it:**
`BUILD.md` `### Procedural-closure slices` in its strict form is a *single* Worker 1 pass that sets
`final-accepted` directly, with no Worker 2 build **and no Worker 3 review**. R3 took the plan's
`### Deviation 2` chain instead — Worker 1 (perform, `planned`) -> Worker 3 (audit) -> Worker 1 (final
verification) — which skips only the Worker 2 build, because Deviation 2 makes the Worker 3 audit
non-skippable in this cycle. The artifact names that exact chain in the same paragraph as the citation,
twice (`:351` block and `### Header status transition`), so nothing is ambiguous on disk. **The
substantive property `### Procedural-closure slices` exists to record — nothing shipped, so no builder
was dispatched — holds exactly.** Not a defect; recorded because "procedural closure" is now used in
this cycle in the looser Deviation-2 sense and the next cycle should inherit the distinction, not the
word.

### 2. Deferred-work catalog — walked source-item to row, independently, and intact

Source read end-to-end: `docs/builder/bld-008-r2-spec_reconciliation.md:2409`
(`grep -n "For R3" …` -> `2409`), the block headed ``**For R3's `### Deferred work catalog`:**``.

**Structure re-derived (fourth independent derivation, after R2's, R2b's, R3's, and Worker 3's):
ten numbered entries — 1-8 under that heading, 9-10 under the separate
`**Standing, for whoever runs the remaining rounds:**` sub-heading. Ten numbers, eight items.**
The 1-4 list immediately *above* the heading is R2b's dispatch scope, not this catalog, and is
correctly excluded. My walk, one source item to one table row, in order — **no silent drop, no
double-count, no invented row**:

| Source item at `:2409` | R3 row | Disposition | Verified this pass |
|---|---|---|---|
| 1 — `spec-009 (1076-1077)` citation stale | 1 | **OPEN** | source and row agree; the citation is at `spec-010:408` and was not opened by this cycle |
| 2 — spec-009 Layer 3 carries two inbound citations | 2 | **OPEN** | source and row agree; `(670-687)` restored by Edit 3, `(1076-1077)` left, both to one future spec-009 cycle |
| 3 — spec-010's rule-27 debt | 3 | **OPEN**, largest item | row carries the framing verbatim in `### Item 3 in full`, including the institutionalizing half |
| 4 — `(or build the schema)`, "DISPATCHED, not deferred" | 4 | **CLOSED by R2b** | a state advance on the source, not a drop: R2 said dispatched, R2b delivered and pinned it |
| 5 — `spec-010:513` partial-mutation contract, deliberately left | 5 | **CLOSED as not-a-defect** | source asks only that R3 not re-flag it; the row records the reason so it stays closed |
| 6 — card 8's two `Verified in upstream` `CardItem`s | 6 | **OPEN**, maintainer observation | source assigns verification to R3; Audit 3 performed it read-only, no DB write |
| 7 — `KANBAN.md:248` names one spec too many | 7 | **OPEN**, maintainer observation | source says record, do not regenerate; the row does exactly that |
| 8 — `docs/review/` escalation | 8 | **OPEN and unresolved** | row adds new evidence and explicitly declines to close it |
| 9 — *(Standing)* pointer-vs-anchor failure mode | 9 | process carry-forward | correctly separated from the eight |
| 10 — *(Standing)* baseline-dirty count | 10 | process carry-forward, re-derived | re-derived three times since (49 / 52 / 52) |

**Catalog verdict: complete and correctly dispositioned. 10 rows for 10 source entries; 8 items, of
which 2 are closed (4, 5) and 6 are open (1, 2, 3, 6, 7, 8); 2 standing.** This is the version
`bld-final.md` lifts, and it lifts cleanly: every row names its state, and the two closures each carry
the reason they are closures rather than omissions — which is what stops a `### Deferred work catalog`
in the gate from silently shrinking to six.

Item 8's underlying evidence moved again and is re-derived here rather than restated:
`git status --short docs/review/ | awk '{print $1}' | sort | uniq -c` -> **5 ` M`, 4 `??`, 0 ` D`**
(unit: status lines). All five originally-deleted `rev-*.md` are back. That strengthens the
regeneration reading and closes nothing: **only the maintainer can confirm the intent.** Nothing under
that directory was opened, touched, restored, or reverted by this pass either.

### 3. Worker 3's non-blocking note — DECISION: name the row explicitly

**Decision: yes. `bld-final.md` gets an explicit do-not-quote list, not a blanket clause.**

The stale rows and their pointers, all four re-read this pass:

| Site | Content | Superseded by | Individually named before this pass? |
|---|---|---|---|
| `:80` | `9 occurrences, 0 of them a validator` (Audit 1 table row) | M1's corrected row at `:936` (announced at `:931`-`:932`) | **yes** — M1 names it |
| `:382` / `:384` | staged-anchor snapshots (`6 lines` / `6` / `8`) | L2's edit-stable form at `:964` | no — blanket clause only |
| `:390` | `46 lines, 0 call sites` (counts table) | L1 at `:948` | **yes** — L1 names "the counts table row" |
| `:391` | `9 occurrences, 0 validators` (counts table) | the superseding table at `:879` | **no** |

`:391` is the one stale figure in the file with no individual pointer: M1 names `:80` and stops, L1
names its two sites, and `:868`'s blanket clause plus the figure-keyed table at `:879` are what cover
`:391`. Worker 3 is right that nothing is *ambiguous*. **The reason to name it anyway is that the gate
lifts figures by copying them.** A blanket clause is a rule the copier has to remember at the moment of
the copy; a named row is one they trip over. `:391` is additionally the most quotable-looking row in the
file — a tidy counts table, one line, two integers — and the figure it carries (`9 / 0 validators`) is
the exact one that already travelled three un-re-derived hops into this artifact. A figure with that
history should not be left to a general rule.

**The rule handed to the gate, stated once so it can be copied verbatim:** *when `bld-final.md` quotes
a figure from this artifact, quote it from the superseding counts table at `:879` or from the keyed
correction sections below it; never from any row above `:861`. The four superseded sites are `:80`,
`:382`/`:384`, `:390`, and `:391` — `:391` (`9 occurrences, 0 validators`) is the one no correction
names individually and is the one most likely to be lifted by mistake.*

### 4. The three `none` declarations, against R3's final diff

All three hold, re-checked against the diff as it now stands and not against the plan's prediction:

- **Failability proofs — `None; this pass introduced no new boundary`, boundary count 0.** R3's diff
  is one `.md` file. No guard, gate, rejection path, or `raise` was introduced anywhere.
- **Hot path — `Not applicable; plan declares no hot path`.** The plan's preamble declares
  `Hot-path declaration: none`; R3 adds no executable line, so nothing runs per request, resolver,
  row, connection, or outbound message.
- **Floor — `Not applicable; plan declares floor-verification scope none`.** The plan's `none` is
  **conditional**, in the form R2b attached: it holds while no executable line changes. R3's diff
  contains **zero `.py` files** — not package source, not tests, not the example project — so the
  condition is not merely satisfied, it is untested. The tripwire ("if the diff turns out to touch an
  executable line, the item re-loops with floor scope declared") is not triggered.

`### Spec slice checklist (verbatim)` audited as the last act rather than assumed:
`grep -cE '^\s*- \[x\]'` -> **4**, `grep -cE '^\s*- \[ \]'` -> **0** (unit: matching lines). All four
boxes are `- [x]`, all four audits were performed in the original pass, and Worker 3 confirmed all four
conclusions. No box is over-ticked, none is silently un-ticked, and **no deferral reason is owed**.

One independent re-derivation of the load-bearing conclusion, run because a confirm-and-close pass
still owes one instrument: the staged-anchor sweep's edit-stable form,
`grep -rEn 'TODO\(spec-008|TODO-(ALPHA|BETA|STABLE)-008' . --exclude=KANBAN.md --exclude=KANBAN.html
--exclude=BACKLOG.md --exclude-dir=.git | grep -cv '^docs/builder/'` -> **0** (unit: matching lines
outside `docs/builder/`), with the raw total at **12** at this reading (unit: matching lines; snapshot
only, and it will move again the moment this block lands). Fifth derivation, same answer: **0 real
staged anchors, tree-wide.** The `./`-prefix trap the prompt warns about is real and was checked —
the raw 12 all match `^docs/builder/` with no `./`, so the filter measured something.

### Summary

R3 shipped nothing durable, by design, and that is its delivered contract. Four read-only audits —
durable docs against the shipped relation graph, the three-direction cross-reference sweep, the
`SpecDoc.path` / terms-CSV chain, and the staged-anchor sweep — found no writable drift; Worker 3
confirmed every conclusion, and a second pass corrected three evidence figures (`cardinalit` 9 -> 42,
`finalize_django_types()` 46 -> 45, and the staged-anchor total replaced by its edit-stable form) which
Worker 3 then re-confirmed, including the "zero executable statements" universal negative under an
independent `tokenize` + `ast` classification (32 docstring + 10 comment + 0 executable + 0
non-docstring literal, over all 42 hits). No verdict moved. The deferred-work catalog is carried by
reference at `bld-008-r2-spec_reconciliation.md:2409`, intact at ten numbers / eight items, with two
items closed in-cycle and six open. R3's entire diff is this artifact plus a gitignored notebook.
The cycle's spec surface closed with R2; its source surface closed with R2b.

### Spec changes made (Worker 1 only)

**None, and the determination is stated rather than left to the empty section.** R3 amends no spec.
Two duties are discharged here, both explicitly:

1. **No spec or rationale edit was made, and none was owed.** The four audits found no spec defect;
   Worker 3's `### Notes for Worker 1` reads "Nothing owed" at both passes; `#### Maintainer decision 3`'s
   contingency edit landed in R2 (verified above at 0 remaining raw range citations); R2b closed with
   no amendment owed. `docs/SPECS/spec-008-…md`, its rationale sibling, and `docs/SPECS/spec-010-…md`
   are ` M` from R1 / R2 / R2b and were **not opened by R3 or by this pass**.
2. **No deferral reason is owed**, because no checklist box is `- [ ]` — `grep -cE '^\s*- \[ \]'` -> 0.
   All four are `- [x]` and all four landed.

### Notes for Worker 1 (spec reconciliation)

What `bld-final.md` must carry. Written for the gate to lift, not to re-derive.

**A. The deferred-work catalog, by reference with its dispositions.** Source of truth stays
`docs/builder/bld-008-r2-spec_reconciliation.md:2409`; the disposition table is `### Deferred work
catalog` above, as corrected by `### 2` in this block. Carry the shape explicitly — **ten numbers,
eight items; 4 and 5 CLOSED with their reasons; 1, 2, 3, 6, 7, 8 OPEN; 9 and 10 standing** — because a
catalog that arrives at the gate as a bare list of six open items has silently lost the two closures
that explain why it is not eight. **Item 3's framing must survive the copy**: the number alone
misrepresents the work, since `spec-010 #"## Note on source line references"` institutionalizes the
practice and closure is a conversion *plus* a section retirement.

**B. The figure-sourcing rule.** Verbatim, from `### 3` above: when quoting a figure from
`bld-008-r3-doc_completion_archive.md`, quote from the superseding counts table at `:879` or the keyed
correction sections below it — **never from any row above `:861`**. The four superseded sites are
`:80`, `:382`/`:384`, `:390`, `:391`; **`:391` (`9 occurrences, 0 validators`) is named explicitly**
because no correction section names it individually and its tidy two-integer form makes it the row most
likely to be lifted by mistake. The figures as they should appear in the gate: `cardinalit` = **42
matching lines / 42 occurrences / 12 files, every one comment or docstring text, 0 executable
statements**; `finalize_django_types()` = **45 matching lines, 0 call sites**; staged anchors = **0
outside `docs/builder/`**, never the raw total.

**C. The gate's baseline exception — load-bearing here, quote it into `bld-final.md`.** The plan
records it at `build-008-definition_order_independence-0_0_4.md:285`, which `BUILD.md` `## Final
test-run gate` requires in the preamble for it to be honoured. `uv run pytest --no-cov`,
`ruff format --check .`, `ruff check .`, and `git diff --check` all read the **whole tree**, and the
tree is not this cycle's. Baseline re-derived at this pass (`git status --short | wc -l` -> **52**
status lines; `HEAD` `947f7494`, unmoved):

- **6 concurrent package sources** — `git status --short django_strawberry_framework/` -> 9 ` M`, minus
  R2b's three (`testing/relay.py`, `types/base.py`, `types/relations.py`) = **6**: five transport-surface
  (`_boundary_ordering.py`, `_cross_web_patches.py`, `_request_body.py`, `connection.py`,
  `middleware/request_body.py`) plus `conf.py`. *(The plan's preamble says "five concurrently-edited
  source files"; it was written before `conf.py` and `_request_body.py`/`connection.py` appeared. The
  exception's scope is "a file this cycle never wrote", not a frozen list — the count moved, the
  exception did not.)*
- **4 concurrent test files** — `tests/base/test_conf.py`, `tests/test_connection.py`,
  `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py` (`tests/testing/test_relay.py`
  is R2b's and is in-cycle).
- **`docs/GLOSSARY.md`** ` M` from the concurrent re-export-index change, four hunks inside lines 27-63.
- **`docs/review/`** — 5 ` M`, 4 `??`, 0 ` D`.
- Plus `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, and the spec-006 / spec-007 cycles'
  uncommitted output.

**The rule, stated the way the gate must apply it: a failure attributable to a file this cycle never
wrote does not block `final-accepted` and does not re-loop an item — it is reported to the maintainer.
The gate still records every real result honestly; the exception governs what a result *blocks*, never
whether it is reported.** Attribution is positive, per file, against the list above — never "probably
not ours".

**D. Four still-open escalations for the maintainer.** None is fixable inside this cycle; all four are
carried, not closed.

1. **Spec-010's rule-27 debt needs a maintainer decision** (catalog item 3). 42 occurrences on 30 lines;
   20 on 15 in-repo violations, 22 on 15 pinned third-party prior art; two in-repo refs (`spec-010:299`,
   `:383`) sit inside pseudocode comments. `spec-010 #"## Note on source line references"`
   **institutionalizes** the practice, so closing it is a conversion **plus a section retirement**, and it
   needs authorization for spec-010 edits outside the sites decisions 1-8 name. Not a find-and-replace.
2. **The stale `spec-009 (1076-1077)` citation in spec-010** (catalog item 1), at `spec-010:408`. It
   resolves to the multiple-`DjangoType`s question; the error requirement it is cited for is at
   spec-009 `### Decision 6: fail loudly`, 8 lines earlier. **Stale at HEAD and independent of this
   cycle** — do not present it as damage this cycle caused. It belongs with catalog item 2 to one future
   spec-009 residual cycle.
3. **`KANBAN.md:248` names one spec too many** (catalog item 7) — spec-008 no longer contains
   `convert_relation`. **Record only**: the file is DB-generated and corrects itself when that board
   item's card is next regenerated. **Do not add spec-018 to the list** — its two occurrences are
   explicitly marked historical, which is why its absence is correct.
4. **The `docs/review/` escalation** (catalog item 8) — **open and unresolved**. State now: **five ` M`,
   zero ` D`** (plus four `??`); all five previously-deleted `rev-*.md` have returned modified, which
   strengthens the reading that a REVIEW cycle regenerated its own artifacts rather than an `AGENTS.md`
   rule 22 violation. **That remains evidence, not a conclusion — only the maintainer can confirm the
   intent.** No pass in this cycle touched, read for content, restored, or reverted anything under that
   directory; the state was observed through `git status` alone.

**E. One process note worth a line in the gate.** "Procedural closure" is used in this cycle in the
plan's `### Deviation 2` sense — no Worker 2 build — not `BUILD.md` `### Procedural-closure slices`'
strict sense, which additionally skips the Worker 3 review. R3 ran the full Worker 3 audit, twice. See
`### 1` above; nothing on disk is ambiguous, but the next cycle should inherit the distinction rather
than the word.

### Final status

**`final-accepted`.** R3's contract is delivered: four read-only audits performed and confirmed, three
evidence corrections landed and re-confirmed, the deferred-work catalog complete and correctly
dispositioned at ten numbers / eight items, no durable-doc edit owed and none made, all four checklist
boxes truly landed, and the three `none` declarations undisturbed by a diff that contains no `.py`
file. Header `Status:` (line 4) set to `final-accepted` in the same action as this block, per the
standing fix for the R2 five-pass header drift. Worker 0 marks R3's checklist box; the cycle's
remaining work is the final test-run gate, which lifts sections A-E above.
