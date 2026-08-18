# Package build plan: consumer_overrides_scalar / 0.0.6 (019)

Spec source: `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` (already archived; NOT at `docs/`)
Rationale companion (to create): `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md`
Terms companion (exists): `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-terms.csv`
Target release: `0.0.6` (shipped 2026-05-19; package is now at `0.0.14`)
Cycle type: **residual closeout cycle**, not a fresh five-slice build. Every spec slice shipped in
commit `a357c68c` ("Finish docs/spec-015-consumer_overrides_scalar-0_0_6.md" — the card was
renumbered 015 -> 019 by the 2026-07-30 board renumber). This cycle delivers the rationale extraction
that pre-flight step 7 never ran for this card, reconciles the spec to `HEAD`, and confirms nothing
was skipped in the code.
Build rule: one round at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every round must justify shared/duplicated patterns before merging.

Ownership partition: `none; single sequential round` (R1 owns the spec, the rationale file, and the
one live-doc correction named in finding 1 below; a code round is only opened if R1's verification
surfaces a real code gap).
Hot-path declaration: `none` (documentation-only cycle; no package source file is written).
Floor-verification scope: `none` (no Django / Strawberry / channels seam is touched).

Pre-flight: run 2026-08-18 against `HEAD 09003dc2`.

- **Step 1 baseline: NOT clean, and deliberately not resolved.** ~80 paths are dirty/untracked from
  the maintainer's concurrent sessions, including a live spec-018 residual cycle (`START.md`
  "Concurrent sessions"). Per `AGENTS.md` rule 34 they are out of scope: never edited, never reverted
  by this cycle. The maintainer directed this cycle to ignore concurrent work.
- **Step 2 `scripts/review_inspect.py`:** smoke invocation against
  `django_strawberry_framework/types/definition.py` with `--output-dir docs/shadow --stdout` succeeded.
- **Step 3 artifact reset: PARTIAL, deliberately.** No `build-019-*` / `bld-*spec019*` path for THIS
  cycle existed. The concurrent cycle's `docs/builder/build-018-meta_primary-0_0_6.md`,
  `bld-review-1-spec018_rationale.md`, `bld-integration.md`, and `bld-final.md` are untracked or dirty
  in the working tree, so deleting them would clobber live work; they are left in place under rule 34.
  **Consequence for naming:** this cycle's integration and final artifacts take the NNN-scoped spellings
  `bld-019-integration.md` / `bld-019-final.md` (precedent in-tree: `bld-003-final.md`,
  `bld-017-final.md`) rather than the unscoped `bld-integration.md` / `bld-final.md`, which the
  concurrent cycle owns. The spec's `-terms.csv` sibling is tracked and durable and was never a
  deletion candidate.
- **Step 4 `.gitignore`:** lists `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/`.
- **Step 5 scratch cleared: PARTIAL, deliberately.** `docs/builder/worker-memory/` holds the concurrent
  cycle's four live files (`worker-0.md` .. `worker-3.md`, written today) and was **not** cleared;
  this cycle seeds and uses four separate `spec019-worker-<N>.md` files in the same gitignored
  directory so the two cycles' notebooks cannot collide. `docs/builder/temp-tests/` (`r1`, `r1c`,
  `r2`, `r4`) and `docs/shadow/` were left intact — both are gitignored and unrecoverable once
  deleted, and the concurrent artifacts indicate a cycle may still be reading them.
- **Step 6 spec-doc consistency:** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`
  exits 0 (`OK: 15 terms`). It must still exit 0 after the rationale move.
- **Step 7 spec rationale extraction: NOT DONE — this cycle's headline deliverable.** Dispatched as
  R1 rather than as a gate before it, because the extraction IS the work rather than a precondition
  for it.

Baseline-dirty out-of-scope files (never edit, never revert): every path listed by `git status --short`
at cycle start, notably `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`,
`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`, `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`,
`docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`, `docs/SPECS/spec-018-meta_primary-0_0_6.md`,
`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`,
`docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md`,
`docs/SPECS/appx/spec-018-meta_primary-0_0_6-rationale.md`,
`docs/builder/build-017-deferred_scalars-0_0_6.md`, `docs/builder/build-018-meta_primary-0_0_6.md`,
`docs/builder/bld-final.md`, `docs/builder/bld-integration.md`,
`docs/builder/bld-review-1-spec018_rationale.md`, `docs/dry/dry-folder-types.md`,
`docs/review/review-0_0_14.md`, every untracked `docs/review/rev-*.md`, and the seventeen dirty
package-source / test files (`types/base.py` and `tests/types/test_definition_order.py` among them —
this cycle READS both and writes neither).

Tracked binary / generated files a concurrent writer can rewrite mid-cycle: `examples/fakeshop/db.sqlite3`,
`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. This cycle writes none of them; churn on any of them
is a concurrent writer's, not this cycle's output.

Build-wide context flags:

- **The spec is already archived.** It sits at `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`
  with its terms CSV at `docs/SPECS/appx/`; a later spec author's `docs/SPECS/NEXT.md` Step 8 sweep
  moved it, and its `<!-- LINK DEFINITIONS -->` block is already re-relativized (`../../AGENTS.md`,
  `../GLOSSARY.md`). So "archive the spec" is **already satisfied**; what is missing is the
  `-rationale.md` sibling in `docs/SPECS/appx/`. Nothing in this cycle moves the spec again.
- **The card is closed.** `KANBAN.md` carries `DONE-019-0.0.6` linked to the archived spec path, and
  `CHANGELOG.md`'s `## [0.0.6] - 2026-05-19` section carries the card's `Added` / `Changed` entries.
  No DB edit and no KANBAN / GLOSSARY regenerate is in scope.
- **The card shipped as `015`.** The original commit is `a357c68c "Finish
  docs/spec-015-consumer_overrides_scalar-0_0_6.md"`; the spec's own rev8 M2 test recipe, the landed
  test's `spec015_*` app labels and stub-module prefix, rev10 L2's "naming `spec-015` Slice 1", and
  `CHANGELOG.md`'s `[015-consumer_override_semantics_scalar_fields-0.0.6]` tracking label all carry
  the pre-renumber number. The 2026-07-30 board renumber moved it to `019`. Both numbers name one
  card; the rationale file records the mapping so a future reader chasing `git log` is not left
  guessing.
- **Rev11 exists because the original cycle already re-opened once.** The spec's revision history
  closes with a post-build maintainer-feedback pass routed back through the Slice 1 loop. That
  revision's own fix has since been superseded (finding 1); the rationale file must not present
  rev11 as the last word on the helper.

## Verified findings carried into R1 (Worker 0's pre-dispatch source verification)

Every item below was checked against source in the working tree at `HEAD 09003dc2` before dispatch,
per `docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`.

**Result on the load-bearing question: NOTHING WAS SKIPPED IN THE CODE.** All five slices shipped.
Every one of the 19 Slice-1 test names the spec's `## Slice checklist` and `## Test strategy` pin
exists in the tree under its own name (checked per name across `tests/` and `examples/`, zero
misses): the 4 core, the 4 converter-bypass (with
`test_annotation_override_of_arrayfield_with_nested_array_is_allowed` in
`tests/types/test_converters.py` per the rev6 L3 placement and the other 18 in
`tests/types/test_definition_order.py` per rev10 L1), and the 11 Relay-collision tests. Slice 2's
`test_consumer_annotation_overrides_synthesized` is absent from the whole tree (deleted, as the rev6
L3 default directed). Slice 3's four-corner matrix docstring is live on
`django_strawberry_framework/types/base.py::_consumer_assigned_fields`. Slice 4's version quintet is
long past `0.0.6`. Slice 5's docs half holds: `docs/GLOSSARY.md` carries `Scalar field override
semantics` at `shipped (0.0.6)` with the converter-bypass, Relay-collision, and metadata-limitation
paragraphs, the index badge is flipped, `Scalar field conversion`'s MRO-walk paragraph names the
annotation override as a parallel recourse to `Meta.exclude`, `docs/README.md` line 111 and
`TODAY.md` line 377 both carry the capability, and `CHANGELOG.md` carries all five entries. The
rev10 L2 temporary `[tool.ruff.lint.per-file-ignores]` ERA001 entry for `types/base.py` /
`types/definition.py` was removed as specified — `pyproject.toml` carries no ERA001 ignore for any
package path.

What the spec says and `HEAD` does not — the reconciliation list. All documentation-only except
finding 1's live-doc half:

1. **The `relay.NodeID` detection mechanism was rewritten, and the spec is the only surviving
   description of the retired one — plus one live doc.** The spec (`## Goals` bullet 5,
   `### Decision 7`'s detection subsection and pseudocode, the Slice 1 module-scope-helpers checkbox,
   the `## Edge cases and constraints` `relay.Node` bullet, the `## Test strategy` coverage
   paragraph, the Slice 5 verbatim KANBAN body, and the Slice 5 verbatim CHANGELOG `Added` entry) all
   describe detection via `typing.get_type_hints(cls, include_extras=True)` inside a
   `try` / `except (NameError, AttributeError)` with two named "fail-soft sub-cases". `HEAD`
   (`django_strawberry_framework/types/base.py::_id_annotation_is_relay_node_id`) calls
   `get_type_hints` **not at all**: it reads `cls.__annotations__["id"]` directly and dispatches on
   `isinstance(raw, str)` — string form to the `_NODEID_STRING_RE` token match, resolved form to
   `_has_node_id_marker`. Changed by commit `2bcd7f96` ("refactor: simplify
   `_id_annotation_is_relay_node_id` function for clarity and consistency - this fixes a coverage
   difference on Python3.10"), whose docstring records the reason: `get_type_hints` handles nested
   forward references differently on 3.10 vs 3.11+, leaving a branch reachable only on the newer
   interpreter. **The observable contract is unchanged** — every one of the 11 Relay tests still pins
   the same accept/reject verdicts, and the two "fail-soft sub-cases" collapse into the two arms of
   the `isinstance(raw, str)` dispatch, which is why no test name moved. What is retired is the
   mechanism, the whole "fail-soft" vocabulary, the `NameError` / `AttributeError` framing, and
   rev11 M1's `hints.get("id")` delegation (rev11's own fix is now moot — the `hints` path is gone).
   The **live** half: `CHANGELOG.md`'s `## [0.0.6]` `Added` Relay-guard entry still states
   "Detection uses `typing.get_type_hints(cls, include_extras=True)` with a fail-soft fallback…",
   which is a false claim about shipped code in a shipped doc. `docs/GLOSSARY.md`'s `Scalar field
   override semantics` entry names no mechanism and is therefore correct as written.
2. **`_is_relay_shaped` is a named module-scope helper.** The spec's Decision 7 and Slice 1 checkbox
   describe the Relay-shape predicate inline as
   `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`, computed at
   the guard. `HEAD` extracts `django_strawberry_framework/types/base.py::_is_relay_shaped`, whose
   docstring names itself the single source of truth for both the collision guard and
   `_build_annotations`'s `suppress_pk_annotation`; commit `74d4a5b7` added a third consumer in the
   connection-validation path. The predicate is byte-equivalent; the single-siting is a later DRY
   improvement the spec should name rather than contradict.
3. **The `consumer_annotated_*` comprehensions carry an `auto_annotated_fields` exclusion.** Decision
   1's post-Slice-1 sample and the Slice 1 checkbox both show
   `field.is_relation and field.name in consumer_annotations`. `HEAD` adds
   `and field.name not in auto_annotated_fields` to **both** comprehensions — an `auto`-typed
   annotation is a request for the model-inferred type, not a consumer override, so it must not enter
   `consumer_authored_fields`. Landed with the later `auto`-typed-annotations card. This card's
   contract is unchanged; the spec's sample is stale.
4. **`_consumer_assigned_fields` takes `cls`, not `cls.__dict__`.** The spec's `## Current state`
   block and Decision 6's prose both show `_consumer_assigned_fields(cls.__dict__, fields)` and
   describe the helper as walking `cls.__dict__`. `HEAD`'s signature is
   `_consumer_assigned_fields(cls: type, fields: tuple[Any, ...])`. Decision 6's responsibility split
   is otherwise intact.
5. **`consumer_authored_fields` is no longer `_build_annotations`'s exclusive consumer.** Decision 2
   states it is "the only short-circuit input to `_build_annotations`" and argues against passing the
   four sets separately. At `HEAD` the same union is additionally passed to
   `_validate_nullability_override_targets`, `_validate_filesystem_path_targets`, and
   `_validate_relation_shape_targets` (later `0.0.9` / `0.0.14` cards). Decision 2's *conclusion* —
   one union rather than four sets — held up and was reused; only its exclusivity claim rotted.
6. **Slice 5's KANBAN instruction is self-referential.** It reads "move `DONE-019-0.0.6` →
   `DONE-019-0.0.6`"; the renumber rewrote both halves of a `WIP-…-015` → `DONE-015` instruction into
   the same string. `## Definition of done` carries the matching artifact: "`KANBAN.md` shows
   `DONE-019-0.0.6` …; `DONE-019-0.0.6` is no longer present." Same defect class the spec-017 and
   spec-018 residual cycles each found in their own Slice-5/6 bodies.
7. **Slice 5's archive bullet is stale.** It says the spec stays at its working location and archival
   is "the maintainer's call"; the spec is archived, and the link-definition block is already
   re-relativized for `docs/SPECS/`.
8. **The CHANGELOG target section moved.** Slice 5 and the Definition of done both say the five
   entries land under `[Unreleased]`; they now sit under `## [0.0.6] - 2026-05-19`. Expected after
   the release cut, but the spec is the last carrier of the pre-release framing.
9. **The Prior-`0.0.6`-card note names pre-renumber FILENAMES.** Slice 4's note reads "`0.0.6`
   carries three cards (`spec-013-deferred_scalars`, `spec-014-meta_primary`, this card)". Today
   `spec-013` is the archived real-M2M stub and `spec-014` is the testing-shift spec; the intended
   files are `spec-017-deferred_scalars-0_0_6.md` and `spec-018-meta_primary-0_0_6.md`, and the
   `0.0.6` line actually carries **four** cards (`DONE-016` .. `DONE-019`). `KANBAN.md`'s `spec-011`
   renumber-sweep bullet tracks this exact occurrence and records that **the spec-018 residual cycle
   already reconciled its own copy of this note to post-renumber card ids rather than filenames**,
   removing spec-018 from the cluster. R1 applies the same fix here — card ids, not filenames — which
   makes this surface correct rather than divergently wrong, and reports the removal so the sweep
   card's population can be re-derived. This is the one item where `worker-0.md`'s
   "do not partial-fix a multi-surface cluster" rule needs the 018 precedent to authorize the edit;
   it is authorized because the fix retires the occurrence rather than rewording it.
10. **The landed tests bake the pre-renumber number into identifiers.**
    `tests/types/test_definition_order.py` uses `app_label = "test_spec015_unsupported"`,
    `"test_spec015_grouped_choices"`, `"test_spec015_co_resident"`, and
    `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"` — matching the spec's rev8 M2
    recipe verbatim, which itself names `spec015_…`. These are test-local synthetic identifiers with
    no cross-file consumer; renaming them is a code edit with no correctness payoff and real
    collision risk against the concurrent session's dirty copy of that file. **Do not rename.** R1
    records the spelling as the landed one and routes the question to the deferred-work catalog.

None of the ten is a code defect. **No code round is opened unless R1's own verification finds one.**
Finding 1's live-doc half (`CHANGELOG.md`) is a documentation correction inside the scope this spec's
Slice 5 explicitly grants ("permission granted by this spec, overriding `AGENTS.md`'s default
prohibition") and is R1's to make.

## Artifact list

**All three were deleted at closeout**, leaving this plan as the cycle's only surviving build document. All three are recoverable in full from commit `435e190e`, which added them. Load-bearing content was resolved into surviving files before each deletion rather than left to the commit — see `### Closeout artifact deletion` below.

- `docs/builder/bld-review-1-spec019_rationale.md` — R1: rationale extraction + spec reconciliation. **Deleted at closeout.**
- `docs/builder/bld-019-integration.md` — cross-round integration pass. **Deleted at closeout.**
- `docs/builder/bld-019-final.md` — final gate. **Deleted at closeout.**

## Checklist

- [x] R1: Rationale extraction + spec-to-HEAD reconciliation -> `docs/builder/bld-review-1-spec019_rationale.md` (deleted at closeout; in `435e190e`)
- [x] Cross-slice integration pass -> `docs/builder/bld-019-integration.md` (deleted at closeout; in `435e190e`)
- [x] Final test-run gate -> `docs/builder/bld-019-final.md` (deleted at closeout; in `435e190e`)

## Closeout record

### Deferred-work homing (2026-08-18, after the gate closed)

All four items of the final gate's `### Deferred work catalog` are homed on the board. Recorded here because the catalog's own targets read "maintainer follow-up, or any future card that opens that file" for items 1 and 2, which is not a card until a card says so. **The board is now the sole source of truth for all four** — the catalog that measured them was deleted at closeout, so cards 051 and 052 carry both the item and its measurement.

- **Catalog items 1 and 2 -> `TODO-ALPHA-051-0.0.15`, one new `scope` bullet** (`CardItem` 1370, order 34). Both populations live in one file, `tests/types/test_definition_order.py`, so they are homed in one bullet: a single WP batch opening that file retires both or neither. The bullet carries (a) the retired fail-soft vocabulary — four occurrences across three tests, with the two test *names* enumerated and the not-greppable-by-its-own-vocabulary trap stated — and (b) the four `spec015_*` synthetic identifiers, enumerated verbatim, with the licensed leave-as-landed disposition named as a decision the owning batch must make rather than sweep. Card 051 is the right home because its `_optimizer_field_map`, `convert_relation` and `[spec-011]` bullets already establish the fold-into-whichever-WP-batch-opens-the-file convention for exactly this shape, and its WP batches open the test tree.
- **Catalog items 3 and 4 -> `TODO-ALPHA-052-0.1.0`, an amendment to the existing `[spec-011]` / `[spec-013]` cluster bullet** (`CardItem` 1345, 3,571 -> 4,632 bytes). Item 3 was the bullet naming this spec as still carrying the pre-renumber filenames `spec-013-deferred_scalars` / `spec-014-meta_primary`; spec-019 has left that population, so it is now recorded alongside spec-018's identical departure rather than as a live carrier. Item 4, `CHANGELOG.md`'s `[015-consumer_override_semantics_scalar_fields-0.0.6]` tracking label, is added as the cluster's fifth surface beside the `[013-…]` label already there — same shape, same two reasons for landing on 052 (rule 21 closes `CHANGELOG.md` to a build cycle; half-fixing a cluster leaves it divergently rather than uniformly wrong).

**One population figure deliberately not decremented.** The bullet's opening `43 standing occurrences across 13 files` counts the `[spec-011]` label, and neither spec-018 nor spec-019 was ever in that half — `grep -c 'spec-011'` returns 0 for both before and after their cycles. Their departures are from the `spec-013` / `spec-014` filename sibling only. The amendment states this explicitly, because the standing hazard on this board is a sweeper adjusting a total measured by a different instrument (compare the same card's `71` -> `70` unused-link-definition bullet, which forbids exactly that overwrite).

**Re-derivation performed before writing, not carried from the catalog.** Both test populations were measured at `HEAD` *and* in the working tree and are identical in content, differing only in line number — which is why the bullet gives no `path:NN` citation. The three test names were confirmed to exist verbatim (1 occurrence each, both revisions); the two cited substrings were confirmed unique in their file, as rule 27 requires. The `CHANGELOG.md` label and its resolving reference-style definition were read directly. `grep -c` on spec-019 for `spec-011` / `spec-013` / `spec-014` returns `0 / 0 / 0` in the working tree against `0 / 1 / 1` at `HEAD`, confirming this cycle is what removed the two filename occurrences and that it never held a `[spec-011]` one.

### Paths this homing changed

| Path | State | What it is |
|---|---|---|
| `examples/fakeshop/db.sqlite3` | ` M` | The two `CardItem` writes, in one transaction. |
| `KANBAN.md` | ` M` | `scripts/build_kanban_md.py` regenerate. |
| `KANBAN.html` | ` M` | `scripts/build_kanban_html.py` regenerate. |

Verified after the regenerate: both renders are byte-stable across two consecutive runs; `scripts/check_trailing_commas.py --check KANBAN.md` exits 0; no `{{...}}` placeholder survives resolution; `scripts/build_kanban_tracked_path_constants.py` leaves `examples/fakeshop/apps/kanban/constants.py` identical to `HEAD`, so the tracked-path pre-commit hook has nothing to stash-conflict over.

**A concurrent session's board work rides along and cannot be separated.** `KANBAN.md`'s third hunk against `HEAD` is the spec-018 cycle's `DONE-018-0.0.6` bullet edit (`CardItem` 1369, DB-written 04:59 UTC today). It was already rendered into the dirty working-tree copy before this homing ran — that copy's line measured 2,362 bytes against `HEAD`'s 2,216, and this regenerate reproduced 2,362 byte-identically, so nothing of theirs was lost or altered. A binary SQLite file and its two renders cannot be split by author; the immediately preceding commit `1b286483` resolved the same situation the same way and said so in its message.

### Commits

The cycle landed in two commits, split on the spec-018 precedent (`b5b2af81` / `1b286483`) rather than as one:

- **`435e190e`** `docs(specs,builder): complete the spec-019 residual closeout cycle` — 7 paths, +1439/-477: the rationale companion, the reconciled spec, the one authorized `CHANGELOG.md` sentence, and all four builder artifacts.
- **`8a80218e`** `docs(kanban): home the spec-019 cycle's deferred board work on cards 051 and 052` — 3 paths: `examples/fakeshop/db.sqlite3` and both renders.

Neither commit carries anything belonging to the concurrent sessions. Their two staged artifact deletions (`docs/builder/bld-017-final.md`, `docs/builder/bld-018-final.md`) were sitting in the shared index and were **unstaged, not restored**, before the first commit — index-only, so their deletions survive on disk and simply are not authored here.

### Closeout artifact deletion

The two round artifacts were deleted after the commits, on the maintainer's instruction, keeping only this plan and the final gate. Deleting a cited artifact is a known pointer-breaking hazard on this board — the spec-017 closeout needed a whole follow-up commit (`09003dc2`) to repair what its own deletion broke — so every inbound reference was enumerated first and resolved rather than left dangling.

Three files cited the deleted pair. The one that mattered is `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md`, a permanent shipped document, which deferred its authoritative byte figures to R1's artifact on the sound reasoning that a byte count written into the file it measures is a count of a file still being written. That reasoning is spent once both files are final, so the figures are now **inlined** there, with the two measurement points kept separate rather than collapsed: 47,488 / 151,505 / -29,568 at R1's close, and 48,834 / 152,851 / -28,222 at commit `435e190e`, the 1,346-byte difference being the integration pass's custodial corrections. Its second pointer, at the 25-entry spec-edit enumeration, now names the commit; its `[bld-r1]` link definition was removed rather than left unused, since unused link definitions are themselves a tracked defect class on card 052.

The final gate was then deleted too, on the same instruction, leaving this plan alone. Its own content was audited section by section first, and **nothing was folded in, deliberately.** Everything unique to it was gate and process record rather than a spec or code fix: the six gate-command results at `HEAD 1b286483` (`6161 passed, 40 skipped` — 37 Postgres-tier, 3 `FAKESHOP_SHARDED` — plus clean `manage.py check`, `makemigrations --check`, `ruff format --check`, `ruff check`, `git diff --check`); the four-level re-derivation that killed R1's false fifth deferral about the live `DONE-019-0.0.6` card body; and the supersession note that R1 had undercounted the fail-soft population. The first is re-runnable and pins a commit, not a contract. The second is a measured non-defect whose only consumer, R1's artifact, is itself deleted — and card 051's bullet already records the corrected count and that it was first understated, which carries the third. All three remain in `435e190e`.

Everything this plan cites that no longer exists on disk is marked deleted-at-closeout with the recovering commit named. Nothing points at a vanished path without saying so, and this plan cites no artifact as live.
