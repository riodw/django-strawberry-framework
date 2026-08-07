# Package build plan: django_types / 0.0.1 (001)

Spec source: `docs/SPECS/spec-001-django_types-0_0_1.md` (**already archived** — the spec, its `-terms.csv`, the `SpecDoc.path` row, and every inbound cross-reference all sit at their post-archive locations; item R3 verifies rather than performs the move)
Target release: `0.0.1` (**shipped long ago** — card `DONE-001-0.0.1`, `target_version.number` `0.0.1`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-06
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other.
Ownership partition: none; sequential residual items.
Hot-path declaration: none. No residual item changes package source, so no item runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam — the cycle edits the spec, its rationale sibling, cross-references, and (only if the audit finds drift) DB-rendered docs.
Pre-flight: passed on 2026-08-06 with **three** recorded deviations (below); baseline: two concurrent-session entries on the spec-048 surface; cleanup: **deliberately not performed** — see Deviation 1.

## This is a residual-completion cycle, not a fresh build

Every slice spec-001 declares was built and released at `0.0.1`, five years of package history ago in version terms. What remains is the deliverable set the shipped cycle never produced, plus the reconciliation that fifty-odd later specs made necessary. The maintainer scoped it in three sequential items: the missing `-rationale.md`, the spec-versus-HEAD reconciliation, then the documentation and archive audit.

### Already-shipped spec slices — verified delivered at HEAD (no build cycle dispatched)

Not checkboxes: Worker 0 may only tick a box after a Worker 1 final verification, and these slices predate this plan by the entire life of the package. They are evidence, pre-verified by Worker 0 at pre-flight so no worker re-derives them.

| Spec slice | Delivered at HEAD — evidence |
|---|---|
| Slice 1 — scaffolding (`exceptions.py`, `registry.py`, `py.typed`, re-exports, package logger) | `django_strawberry_framework/exceptions.py` (`DjangoStrawberryFrameworkError`, `ConfigurationError`, `OptimizerError` + two later subclasses), `registry.py::TypeRegistry`, `py.typed` all present |
| Slice 2 — `DjangoType` with scalar conversion | `django_strawberry_framework/types/base.py::DjangoType`, `types/converters.py::convert_scalar` |
| Slice 3 — relation conversion (FK / reverse / M2M) | `types/converters.py::resolved_relation_annotation`, `types/relations.py::PendingRelation` |
| Slices 4-6 — optimizer | **superseded before they shipped** — moved to the `spec-002` family by the spec's own text; `django_strawberry_framework/optimizer/` is the delivered surface |
| Slice 7 — choice-field enum generation | `types/converters.py::convert_choices_to_enum`, naming rule `f"{type_name}{pascal_case(field.name)}Enum"` unchanged from the spec |

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped cycle predates the rule. Worker 1 is the only role that may perform it. Spec-001 is unusually rich in deliberative layer for its size: `## Scope creep into the N+1 problem` is 100% deliberation, and the slice-status annotations, "Deviation from earlier draft" paragraphs, `## Open questions`, and `## Post-slice-7 future work` are the spec narrating its own history — exactly what `BUILD.md` says a spec must never do.
- **R2 — reconcile the spec with what landed and what later specs corrected.** The maintainer's framing: *make sure the spec matches what actually exists, and where later updates corrected what landed, the spec reflects that; the explanation of the change goes in the rationale, never in the spec.* Fifteen verified drift items are tabled below. Worker 1 is the only role that may edit the spec.
- **R3 — finish the documentation and audit the archive.** Verify the durable docs (`docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`) describe the spec-001 surface as shipped, and verify the already-performed archive is complete in all three cross-reference directions, in the kanban DB, and in the terms-CSV importability chain.

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → two entries, both on the spec-048 surface: `M docs/SPECS/spec-048-secure_output_defaults-0_0_14.md` and `?? docs/SPECS/appx/spec-048-secure_output_defaults-0_0_14-rationale.md`. A concurrent session is running the same shape of cycle on spec-048. `AGENTS.md` rule 34 applies. See the baseline-dirty list below.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/types/converters.py --output-dir docs/shadow --stdout` emitted its overview (15 imports, 21 symbols, 4 control-flow hotspots). Working.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-001*`, no `docs/builder/bld-001*`, no `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATION 1, see below.** Deliberately not cleared.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md` → `OK: 21 terms - all have glossary entries and at least one spec link.` Exit 0. Baseline for the constraint in `### The 21-anchor constraint` below.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the slices whose spawns the gate protects were built and released before this plan existed, so there is no builder left to protect. R1 runs first regardless, so every later spawn in this cycle reads the smaller spec exactly as the rule intends.

### Deviation 1 — the prior cycles' artifacts, memory, shadow, and temp-tests are PRESERVED

Pre-flight steps 3 and 5 delete old `build-*.md` / `bld-*.md` and clear the three scratch paths. Not performed, deliberately:

- The 30 artifacts under `docs/builder/` belong to the spec-044 through spec-049 cycles and are **committed**. A concurrent session is additionally mid-cycle on spec-048 right now (baseline dirty, above), so a blanket artifact delete would destroy live work.
- `docs/builder/worker-memory/` (four files, 22KB) and `docs/builder/temp-tests/` (two cycle directories) are **gitignored**, so deleting them is unrecoverable, and `worker-0.md` `## Closeout job` steps 2 and 5 read exactly those files.
- The reasoning is `BUILD.md`'s own, under `### Cohorting, naming, and closure` ("Pre-flight for a round"): when the input to a cycle is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-001-`-prefixed, and none of those paths exists. The maintainer's dispatch instruction required exactly this ("use file naming to not conflict with existing concurrent bld work").
- Consequence for dispatch: each worker's memory file opens with earlier cycles' entries. Dispatch prompts say so and require this cycle's entries to be appended under a `## spec-001 residual cycle` heading, so the cycles stay distinguishable at the next closeout.

### Deviation 2 — artifact filenames carry the `001` card number

`## Build artifact naming` gives `bld-slice-<N>-<short_slug>.md`; the surviving spec-046 set already occupies `bld-slice-1..5-*`, `bld-integration.md`, and `bld-final.md`. This cycle uses `bld-001-<item>-<slug>.md` and `bld-001-final.md` — still `docs/builder/bld-`-prefixed, and unambiguous about which cycle each artifact records. The items are also not spec slices (the spec's slices shipped at `0.0.1`), so an `N` mirroring a slice number would misdescribe them.

### Deviation 3 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Items **R1 and R2** have no Worker 2 role that could set it:

- **R1** — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.
- **R2** — `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate the spec. R2's entire deliverable is spec edits.

So for R1 and R2 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on those artifacts as "dispatch Worker 3", not Worker 2. Declared here, before dispatch, so no pass improvises the mapping.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review and as the pass that checks the finished implementation against it. A rewrite performed by the author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut. **R3 has real Worker 2 work** (durable-doc and, if drift is found, DB edits) and runs the full unmodified chain.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34):

- `docs/SPECS/spec-048-secure_output_defaults-0_0_14.md` — modified by a concurrent session.
- `docs/SPECS/appx/spec-048-secure_output_defaults-0_0_14-rationale.md` — untracked, being written by that same concurrent session.

Both are the spec-048 surface, and this cycle touches no spec-048 file. If either changes again mid-cycle that is the concurrent session, not this build.

**Grew during item R1** (reported by Worker 1, not reverted). The concurrent session ran its spec-048 **card wrap** while R1 was in flight, which writes the kanban DB and regenerates from it:

- `examples/fakeshop/db.sqlite3`
- `KANBAN.md`, `KANBAN.html`
- `docs/SPECS/appx/spec-027-filters-0_0_8-terms.csv`
- `docs/SPECS/appx/spec-048-secure_output_defaults-0_0_14-terms.csv`

Attribution is positive rather than inferred: R1's writable list contains no DB, KANBAN, or CSV path, and the only two DB-touching commands R1 ran (`import_spec_terms --check`, the card/SpecDoc read) are read-only.

**Cleared during R1's final verification.** The concurrent session committed its spec-048 card wrap at `b29b851e`, and every path above went clean. `git status --short` at the close of R1 showed **only this cycle's four paths**.

**Dirty again during item R2**, and this is now the standing baseline for R3 and the final gate. The concurrent session opened a **spec-049 cycle** and wrapped card `DONE-049-0.0.14` while R2 ran (`import_spec_terms --check` moved from `48 done cards` to `49` mid-pass, exit 0 on both sides). Its files, none of which this cycle writes:

- `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` — the card wrap and its three regenerates
- `docs/spec-049-dependency_ci_hardening-0_0_14.md`, `SECURITY.md`, `TODAY.md`, `uv.lock`

**Consequence for item R3, which the earlier text of this plan got wrong.** `## Concurrent-writable tracked binary / generated files` below says a `docs/GLOSSARY.md` diff "means drift to investigate, not build output". That is no longer safe to read literally: a glossary diff right now is most likely the concurrent card wrap. R3 **attributes semantically before concluding** — compare against a fresh regenerate and check whether the changed entries belong to card 49 — and it may not verify any DB-backed work of its own by "`git diff` is clean" (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). If R3 writes the DB at all it applies its writes **on top** of the concurrent state without reverting, verifies by two-consecutive-regenerate byte-stability plus spot-checks, and hands the mixed diff to the maintainer.

**Baseline exception for the final test-run gate, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured:** `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see any concurrent-session churn. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). All four are **clean at baseline**, so no concurrent card-wrap is in flight:

- `examples/fakeshop/db.sqlite3` — the maintainer runs parallel sessions against this file. **No residual item is expected to write it**: card 1 is already Done and its `SpecDoc.path` already points at the archived location (verified below). A write happens only if R3's audit finds real drift. Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html` — regenerated from that DB only if R3 writes it.
- `docs/GLOSSARY.md` — DB-rendered; **no residual item is expected to change it.** A diff here means drift to investigate, not build output.

## Build-wide context flags

- **`0.0.1` shipped and the version quintet is at `0.0.14`.** No residual item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`.
- **No source or test file changes in this cycle.** Package source, `tests/`, and `examples/` code are read-only throughout. R3 may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2.
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs: no residual item edits it. A stale spec-001 path found there is reported to the maintainer, never edited.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared as a Worker-1-owned final-verification step. There is no move: `docs/SPECS/spec-001-django_types-0_0_1.md` and `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv` are already at their archived paths, `SpecDoc.path` already reads `docs/SPECS/spec-001-django_types-0_0_1.md`, and both `KANBAN.md` references already point there. **R1's new rationale file is therefore written directly to `docs/SPECS/appx/`** — the archived-companion location `AGENTS.md` rule 26 names — never to `docs/` first and moved after.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

`worker-0.md` `## Closing out a kanban card` requires the live DB references be verified before a card/glossary edit is planned, because plan and spec text can carry stale ones. Read-only queries, run 2026-08-06:

- `Card.objects.get(number=1)` → `card_id` `DONE-001-0.0.1`, `status.key` `done`, `target_version.number` `0.0.1`, title `DjangoType core foundation`. The card is **already Done**; no status flip is in scope, and the 2026-07-30 card renumber left 001 untouched (it rotated 045-068 only).
- `SpecDoc` for card 1 → name `spec-001-django_types-0_0_1`, **`path` already `docs/SPECS/spec-001-django_types-0_0_1.md`**. No repoint needed. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it — assigning `url=` raises.)
- `card.glossary_links.count()` → 21, matching the 21 rows in the terms CSV.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 48 done cards have glossary links.` Exit 0. **This is the baseline both R1 and R2 must not break.**
- Spec byte count before R1: **52,341 bytes** (`docs/SPECS/spec-001-django_types-0_0_1.md`). Worker 1 reports the after-count in the R1 artifact.

### The 21-anchor constraint — the trap in this cycle

`docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv` carries 21 anchors, and `check_spec_glossary.py` passes today because **each of the 21 has at least one link in the spec body**. Both R1 (which moves text out of the spec) and R2 (which rewrites text) can silently drop the last remaining link for an anchor. The failure is not cosmetic: `import_spec_terms` is what a DONE card's glossary-link set is rebuilt from, so a dropped anchor breaks the card-wrap chain for card 1.

The 21 anchors: `aggregateset`, `apply_cascade_permissions`, `bigint-scalar`, `configurationerror`, `definition-order-independence`, `djangoconnectionfield`, `djangooptimizerextension`, `djangotype`, `filterset`, `metachoice_enum_names`, `metadescription`, `metaexclude`, `metafields`, `metainterfaces`, `metamodel`, `metaname`, `only-projection`, `orderset`, `per-field-permission-hooks`, `relay-node-integration`, `scalar-field-conversion`.

**Every pass that writes the spec re-runs `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md` and quotes the result in its artifact.** A rewrite that drops an anchor keeps the anchor's link by re-siting it in the surviving contract prose — never by re-adding narration the item just removed, and never by editing the CSV.

### Verified spec-versus-HEAD drift — R2's input, verified by Worker 0 against source

Read at HEAD on 2026-08-06 with the symbol-qualified paths given. Each row is a claim the spec makes that HEAD falsifies. **A prescribed correction is not included: how the spec should read is Worker 1's call, and the alternatives it rejects belong in the rationale file.** Worker 1 re-verifies each row rather than trusting this table.

| # | Spec-001 claim | HEAD reality | Later spec that moved it |
|---|---|---|---|
| D1 | Module layout is flat: `types.py`, `converters.py`, `optimizer.py`, `registry.py` | `django_strawberry_framework/types/` package (`base.py`, `converters.py`, `definition.py`, `finalizer.py`, `relations.py`, `relay.py`, `resolvers.py`) and `optimizer/` package; `registry.py` stayed flat | spec-009 / spec-010 restructure |
| D2 | `registry.lazy_ref(model)` is exposed, with three candidate resolution approaches | no `lazy_ref` anywhere in `django_strawberry_framework/registry.py`; the surviving `_lazy_ref` symbols are unrelated (`mutations/fields.py`) | spec-008 |
| D3 | "Slice 3 shipped eager-only … consumers must declare related `DjangoType`s in dependency order" | false at HEAD — `registry.py::TypeRegistry.add_pending_relation` / `iter_pending_relations` plus `types/finalizer.py::finalize_django_types` resolve order-independently | spec-008 |
| D4 | Deferred-key rejection covers `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields` | `types/base.py::DEFERRED_META_KEYS` is `{aggregate_class, fields_class, search_fields}`; `filterset_class` and `orderset_class` are in `ALLOWED_META_KEYS` | spec-027, spec-028 |
| D5 | `Meta.interfaces` is "accepted by validation but not yet wired … subclass `relay.Node` directly" | wired — `types/relay.py::install_is_type_of` and the Relay-Node integration path | spec-015 |
| D6 | "Registering the same model twice should raise `ConfigurationError` by default" | `registry.py::TypeRegistry.register` accepts multiple types per model; `Meta.primary` flags the relation-resolution target; the collision rules are narrower (reverse-collision, duplicate-primary, primary-flag flip) | spec-018 |
| D7 | `BigInt`, `ArrayField → list[inner]`, `JSONField`/`HStoreField → JSON` are "spec'd but not implemented" | all shipped | spec-017 |
| D8 | `FileField` / `ImageField` → `str` (URL/path) | read output is `DjangoFileType` / `DjangoImageType` via `types/converters.py::FIELD_OUTPUT_TYPE_MAP`; `SCALAR_MAP`'s `str` survives **only** for the filter / scalar-input path, and the comment at `SCALAR_MAP` says so | spec-037; `Meta.filesystem_path_fields` from spec-048 |
| D9 | `AutoField` / `BigAutoField` / `SmallAutoField` → `int`; relay `GlobalID` remapping is an open question | Relay Node integration and `GlobalID` shipped, with a model-label default payload and `Meta.globalid_strategy` | spec-015, spec-031, spec-032 |
| D10 | Tests land in `tests/test_django_types.py`, `tests/test_optimizer.py`, `tests/test_choice_enums.py` | `tests/types/test_base.py`, `tests/types/test_converters.py`, `tests/optimizer/*`; none of the three named files exists | spec-014 |
| D11 | Example paths are `examples/fakeshop/fakeshop/products/…` | `examples/fakeshop/apps/products/…` | later example restructure |
| D12 | `convert_choices_to_enum` rejects grouped choices and sanitizes values | still true and the **naming rule is unchanged** (`f"{type_name}{pascal_case(field.name)}Enum"`), but HEAD adds a third rejection the spec never mentions: two choice values that sanitize to the same member name raise, and the build core is shared with the serializer `ChoiceField` path (`types/converters.py::convert_choices_to_enum`, `build_enum_from_choices`) | later hardening |
| D13 | "no fakeshop model declares an M2M field, so the dedicated test placeholder stays skipped" | M2M coverage shipped | spec-013 |
| D14 | `examples/fakeshop/…/products/schema.py` is a commented-out aspirational block awaiting an uncomment | the fakeshop schema is live and serves `/graphql/` | spec-011 |
| D15 | O6 flips the sentinel with `if "get_queryset" in cls.__dict__` in `__init_subclass__` | `types/base.py::DjangoType.__init_subclass__` calls `_detect_custom_get_queryset(cls)` so the flag inherits through an abstract base that declares `get_queryset` without a `Meta`; the resolved value is also carried on `types/definition.py::DjangoTypeDefinition.has_custom_get_queryset` | later hardening |

Two things the drift table deliberately does **not** say. First, that every row must change the spec: some rows are the spec being *superseded* rather than *wrong*, and the spec-002 family already owns the optimizer text by the spec's own declaration — Worker 1 decides per row whether the contract is restated, pointed elsewhere, or dropped to the rationale. Second, that the list is exhaustive; it is Worker 0's verified floor, and R2 owns the full sweep.

### Every reference TO spec-001 (verified by grep, 2026-08-06)

The archive already landed, so this table is R3's **verification** list, not a rewrite list. Every entry already reads correctly; R3 confirms and reports, and only edits if one is wrong.

| Location | Current text | Status |
|---|---|---|
| `KANBAN.md:146`, `KANBAN.md:4891` (+ `KANBAN.html`) | `docs/SPECS/spec-001-django_types-0_0_1.md` | **Generated** — already correct; never hand-edit |
| `docs/SPECS/spec-002-optimizer-0_0_2.md:9`, `:56`, `:57`, `:80` | inline code-span `spec-001-django_types-0_0_1.md` | Sibling in the same directory — correct as a bare filename |
| `docs/SPECS/spec-005-django_type_contract-0_0_3.md:5`, `:107`, `:109`, `:122` | inline prose + one `docs/SPECS/spec-001-…` path | Correct |
| `docs/SPECS/spec-006-public_surface-0_0_3.md:134` | inline code-span | Correct |
| `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md:1830` | `[spec-001]: spec-001-django_types-0_0_1.md` | Reference definition, sibling — correct |
| `docs/SPECS/spec-001-…md:47` (inside the spec) | self-reference ``This document is `spec-001-django_types-0_0_1.md` `` | Inside `## Scope creep into the N+1 problem`, which R1 moves — the self-reference travels with it or is dropped |

No hit in `CHANGELOG.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, or `docs/README.md`. The sweep is re-run by R3, not trusted from this table.

**The direction this table cannot show** is the one inside the new file: R1's rationale lands at `docs/SPECS/appx/`, two levels below `docs/`, so its link definitions need `../../GLOSSARY.md` for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling. The archived siblings (`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`) show the shape.

## Artifact list

- `docs/builder/bld-001-r1-rationale_move.md`
- `docs/builder/bld-001-r2-spec_reconciliation.md`
- `docs/builder/bld-001-r3-doc_completion_archive.md`
- `docs/builder/bld-001-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded in — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R3, and the cross-artifact read runs in the final gate. Naming one `bld-integration.md` would also collide with the preserved spec-046 artifact.

## Checklist

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` (Worker 1 performs the move; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-001-r1-rationale_move.md`
- [x] R2: Reconcile the spec with HEAD — every claim the package falsifies is restated as the contract that actually holds, or handed to the spec that now owns it; the explanation of each change lands in the rationale, never in the spec -> `docs/builder/bld-001-r2-spec_reconciliation.md`
- [x] R3: Finish the documentation and audit the archive — durable-doc audit of the spec-001 surface, the three-direction cross-reference sweep, `SpecDoc.path` / terms-CSV verification, and the `TODO(spec-001` / `TODO-ALPHA-001` staged-anchor sweep -> `docs/builder/bld-001-r3-doc_completion_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-001-final.md`

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
