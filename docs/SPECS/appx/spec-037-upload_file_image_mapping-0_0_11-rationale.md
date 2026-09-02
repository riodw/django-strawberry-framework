# Rationale companion: spec-037 (Upload scalar and file / image field mapping)

Companion to [`docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`][spec-037].
It carries that spec's **deliberative layer** and nothing else: the authoring
revision history that produced the contract, every Decision's justification,
every alternative a Decision rejected and why it lost, the risk /
open-question deliberation that settled the card's design questions, and the
post-ship supersession narrative [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)
was carrying inline. The spec carries the contract; this file carries how the
contract was arrived at. Neither duplicates the other — the text here **left**
the spec.

Read this when checking a finished implementation against the reasoning that
produced it, or before re-opening a settled question. Worker 2 never reads it
([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

**How later passes append to this file.** Each Decision below carries a
`### Changes this Decision underwent` section. A reconciliation pass that finds
the spec stale against `HEAD` — a guard that shipped differently, a helper that
never landed where the Decision said it would, a default a later card inverted —
appends a `**Post-ship:**` bullet there, naming the shipped behavior and the card
or commit that changed it. A Decision a reconciliation checked and found still
true earns a bullet too, saying so — a measured no-change and an unexamined one
read identically otherwise. Findings belonging to no single Decision go under
[Non-Decision deliberation](#non-decision-deliberation). Nothing needs
restructuring to take an addition, and the corrections themselves always land in
the spec, stated directly and without chronology.

## Provenance of this record

Created by pre-flight step 7 of the `037` residual-reconciliation cycle, whose
plan is [`docs/builder/DONE/build-037-upload_file_image_mapping-0_0_11.md`][build-037]
and whose record of the move itself was the per-cycle artifact
`docs/builder/bld-037-slice-0-rationale_extraction.md`, retired when that cycle
closed and recoverable at
`git show f9ae3f93:docs/builder/bld-037-slice-0-rationale_extraction.md`. `spec-037` shipped in
`0.0.11` with a [`-terms.csv`][spec-037-terms] companion and no `-rationale.md`
sibling; this file closes that gap. Nothing in it is new reasoning: every passage
below was cut from the spec in the same pass that created this file, except the
framing paragraphs, the `### Changes this Decision underwent` summaries, and the
[Non-Decision deliberation](#non-decision-deliberation) entries, which are this
pass's own and say so. The `034` / `035` / `036` companions are the three
immediately-preceding executions of the same move and this file matches their
shape.

The spec was verified byte-identical to `HEAD` before the first edit
(`git show HEAD:docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` into a
scratch path outside the repo, diffed clean against the working copy) at
**116,067 bytes, 1,863 lines**. It is **97,629 bytes, 1,567 lines** after the
move: **22,016 bytes cut** by five routes, **3,578 bytes** of one-line pointers
and link definitions added back.

- **The whole `Revision history (kept inline so the spec is self-contained):`
  block** — its preamble, the blank line under it, and one `Revision 1` entry,
  42 lines, **2,756 bytes**. The entry is reproduced under
  [Revision history](#revision-history) below, byte-for-byte, **2,693 bytes** of
  it; the 62-byte preamble line was **deleted, not moved** — its claim that the
  history is kept inline is exactly what this move made untrue — and so was the
  1-byte blank line between them.
- **9 `Justification:` blocks**, one under every Decision except
  [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models),
  carrying 2 justification bullets and 8 paragraphs, **3,621 bytes**. Reproduced
  byte-for-byte under each Decision's heading; the 9 labels became `###` headings
  here — 1 stood on its own line (Decision 1) and 8 were inline prefixes stripped
  from the paragraph they introduced (Decisions 2-8, 10), which is why those
  sections open lower-case.
- **9 `Alternatives considered (and rejected):` blocks**, one under every
  Decision except
  [Decision 8](#decision-8--no-new-meta-key-no-new-setting-no-dynamic-storage-policy),
  carrying **29** rejected alternatives, **8,114 bytes**. All 9 labels stood on
  their own line and all 9 became `###` headings here. **The pairing is not
  1:1** — Decision 8 has a justification and no alternatives, Decision 9 the
  reverse — so both files carry an explicit `None.` under the missing heading
  rather than a silently absent section.
- **[Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)'s
  `> **Superseded (post-ship, 2026-06-20 round-4 review).**` block** — 16 lines,
  **1,245 bytes**. It quoted the spec's own retracted position and narrated its
  own history, which [`docs/builder/BUILD.md`][build-md]
  `## Spec rationale extraction` forbids outright. It is reproduced verbatim
  under that Decision's `### Changes this Decision underwent`. **This move did
  not rewrite the surviving Decision-9 body**, which still states the superseded
  deferral as current contract; that rewrite is the reconciliation slice's and is
  recorded in this pass's artifact.
- **The body of `## Risks and open questions`** — its preamble plus **10** items,
  each written as a preferred-answer / fallback pair, **6,280 bytes**. That shape
  is a build-time deliberation instrument, not a contract, so the body moved and
  the spec keeps the heading and a pointer here. Seven items are design questions
  a Decision answered outright and three are card-citation corrections the cut
  chose to record rather than silently reconcile.

**The census used three grammars and needed all three.** `grep -on 'Revision
[0-9]'` finds **1** occurrence and is blind to the block's own preamble
(`Revision history`, no digit). The shortest distinctive token, `evision` matched
case-insensitively (`grep -oin 'evision'`), finds **2** occurrences on 2 lines —
the true population, and the extra one is exactly that preamble. Both sit on
lines 98 and 100, which is the finding that matters: `spec-037` carried **no**
`Revision N` cross-reference anywhere outside the block itself, so the block was
lifted whole without repointing a single surviving sentence. A third sweep for 22
chronology words carrying no `revision` token at all (`superseded`, `post-ship`,
`earlier draft`, `prior draft`, `first draft`, `later changed`, `amendment`,
`review round`, `formerly`, `no longer`, `has since`, `retract`, `pre-build`,
`post-build`, `feedback`, `previously`, `used to`, `replaced by`, `reconciled`,
`originally`, `round-4`, `round 4`), run over whitespace-flattened text so a
wrapped phrase cannot hide, found **6** occurrences at `HEAD` and **3** in the
post-move spec. The 3 survivors are two `previously-`NotImplementedError``
descriptions of what the shipped code path used to do — contract, not
self-narration — and the word `post-ship` inside this move's own Decision-9
pointer.

**Every in-page anchor inside the moved text resolves locally here.** The moved
text carries **21 anchor occurrences across 11 distinct anchors**: the ten
`#decision-N--…` slugs and `#risks-and-open-questions`. This file carries
headings with exactly those slugs, so **zero** anchors needed re-pointing at the
spec — unlike the `036` execution of this move, which had to repair five uses
across four anchors naming spec sections its companion did not have.

**Held back in the spec under the implementation-relevant carve-out.** Each of
these reads as deliberation and is in fact the "why" that changes how the thing
is built; a builder who never reads one writes the defect the Decision's own
rejected alternative names. All stayed exactly where they were.

- **[Decision 3][spec-037-d3]'s "Why a separate map, not a `SCALAR_MAP` rewrite"
  paragraph.** [`SCALAR_MAP`][types-converters] is walked by the read path *and*
  by the filter-input path, so a `SCALAR_MAP[models.FileField]` returning
  `DjangoFileType` would make a [`FilterSet`][glossary-filterset] over a file
  column emit an **output** object as a GraphQL **input**. A builder who never
  reads it puts the object types in `SCALAR_MAP`.
- **[Decision 3][spec-037-d3]'s thin-wrapper paragraph and its MRO-ordering
  paragraph.** The first is why `convert_field_output` is a new read-only helper
  rather than an expansion of `convert_scalar`; the second is why `ImageField`
  must precede `FileField` in the map, since `ImageField` is a `FileField`
  subclass and the walk tests `type(field).__mro__`.
- **[Decision 3][spec-037-d3]'s `consumer_authored_fields` skip paragraph.** It
  states why the file pass's skip set is deliberately **broader** than the
  relation pass's `consumer_assigned_relation_fields`: skipping only assigned
  overrides would silently clobber an annotation-only opt-out.
- **[Decision 4][spec-037-d4]'s "The guard must live on the subfields, not the
  parent resolver" paragraph.** Strawberry resolves each selected subfield by
  `getattr` **after** and **outside** the parent resolver, so a parent
  `try/except` cannot reach the property accesses that raise. A builder who never
  reads it writes the parent-level guard — the defect the Decision's own rejected
  alternative names.
- **[Decision 4][spec-037-d4]'s `SuspiciousFileOperation` paragraph.** The
  exception is deliberately **not** caught: a path-traversal / hostile-name
  condition is a security signal, not a storage quirk, and must surface rather
  than degrade to a `null` subfield.
- **[Decision 4][spec-037-d4]'s default-nullable bullet.** The object is nullable
  **independent of `null` / `blank`** because Django stores `""` for "no file" and
  that value is reachable on a `null=False, blank=False` column, so a non-null SDL
  would turn the resolver's `None` into a top-level 500.
- **[Decision 6][spec-037-d6]'s no-new-resolver-code paragraph, its
  "Omittable is not nullable" paragraph, and its CR-6 lifting paragraph.** The
  first is why no dedicated file-assignment branch is added — Django's
  `FileField` descriptor accepts an `UploadedFile`, so the generic scalar path
  carries it. The second is the observable error contract for an explicit `null`.
  The third is what the shipped build had to remove from
  [`mutations/inputs.py`][mutations-inputs].
- **[Decision 8][spec-037-d8]'s standing architectural line.** The
  `RELAY_GLOBALID_STRATEGY`-shaped rule — normalization in [`conf.py`][conf],
  key-specific validation in the domain module, and any request-affecting setting
  resolved and stamped **once at schema build / finalization** — is a rule for
  future work, not an argument for this Decision. Only the four-line
  `Justification:` paragraph above it moved. **This is the one block whose
  measured span had to be narrowed by reading**: a naive cut from the
  `Justification` label to the next Decision heading would have taken 17 lines and
  1,130 bytes instead of 4 lines and 256 bytes.

**Two Risks items could move only because the spec already states their rules
elsewhere.** The `Storage-metadata read cost` item's "does **not** cache or batch
storage calls" rule is restated in the spec's `## Edge cases and constraints`,
and the `Image dimension dependency` item's "never a Pillow-conditional `skip`,
which would slip uncovered branches past `fail_under = 100`" rule is restated in
the spec's `## Test plan`. Both were checked before the body was cut; had either
been unique to the Risks body it would have stayed under the rule that an unclear
sentence stays.

**One moved sentence is false at `HEAD` and moved verbatim anyway.** The
`Image dimension dependency + test strategy` item says "the project does **not**
currently declare Pillow in runtime or dev dependencies"; `pyproject.toml`
declares `pillow>=10.0.0` in the `dev` group at `HEAD`, which is the item's own
*preferred* answer having been taken. The premise is gone while the moved text
keeps its wording, and the correction is recorded here rather than applied inside
moved text — the same treatment the `036` companion gave its one false Risks
premise.

**Deleted rather than moved.** Two things, 63 bytes and one link definition. The
`Revision history (kept inline so the spec is self-contained):` preamble line and
its trailing blank, falsified by this move. And the spec's
`[glossary-orderset]: ../GLOSSARY.md#orderset` link definition, whose only use
was inside the moved Risks body — it is carried here instead. No other definition
became unused: a post-move sweep of the spec found **0 dangling uses and 0 unused
definitions**.

**Not reconciled by this pass.** This move did not check the spec against `HEAD`;
a later slice of the cycle does. The divergences noticed while reading are
recorded in this pass's artifact under
`### Notes for Worker 1 (spec reconciliation)` for that slice to grade, and every
correction it produces lands in the spec stated directly and without chronology,
with what changed and why appended here as a `**Post-ship:**` bullet under the
owning Decision.

## Revision history

One revision produced the contract: `spec-037` was authored in a single drafting
pass and never went through a numbered review revision, which is why every
Decision's `### Changes this Decision underwent` section below reads "the spec
records no later revision of this Decision". The block below is the spec's own,
verbatim. The one post-ship change the spec did record — the round-4 supersession
of [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)'s
test-placement deferral — was never folded into this history and is recorded
under that Decision instead.

- **Revision 1** — initial draft authored from the
  [`TODO-ALPHA-037-0.0.11`][kanban] card body via the
  [`docs/SPECS/NEXT.md`][next] flow (2026-06-19). Pinned: the canonical
  structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the
  card-scope boundary as a file/image conversion card, not a multipart-transport
  or storage-abstraction card
  ([Decision 2](#decision-2--card-scope-boundary-fileimage-conversion-only-not-transport-or-storage-abstraction));
  the `DjangoFileType` / `DjangoImageType` output shapes mirroring
  [`strawberry-graphql-django`][upstream-field-types] with an empty-file
  resolver guard
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream));
  **storage-safe nullable subfields** (`path` / `size` / `url` / `width` /
  `height` nullable; `name` non-null) so a non-filesystem backend or a vanished
  file degrades to `null` rather than a GraphQL 500, and the default-nullable
  object shape (file/image output is `<object> | None` by default to match the
  empty-file resolver `None`)
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability));
  the `Upload` re-export from the package root — no `_PACKAGE_SCALAR_MAP` entry,
  since `Upload` is already in Strawberry's built-in scalar registry (the
  contrast with the package-custom [`BigInt`][glossary-bigint-scalar])
  ([Decision 5](#decision-5--re-export-upload-rather-than-register-it));
  the write-side seam-to-`Upload` swap and the write-resolver file assignment,
  lifting the `036` file-column merge-override exception
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload));
  the three net-new root-exported public symbols
  ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols));
  no new `DjangoType` `Meta` key or settings key
  ([Decision 8](#decision-8--no-new-meta-key-no-new-setting-no-dynamic-storage-policy));
  the synthetic-model test strategy with live coverage only where a real
  fakeshop path exists
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models));
  and **this card owning the final `0.0.11` version bump**
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
  Three card-body conflicts are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the stale `"Pairs with 028"` note, the stale
  `mutations/ (planned)` predicted-file annotation, and the stale
  `TODO-ALPHA-035-0.0.11` reference in the [`scalars.py`][scalars] docstring),
  each with a preferred reading.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-037-d1].

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN (`037`) and target
  patch (`0_0_11`) into the filename.
- The topic slug is `upload_file_image_mapping` — short, snake-case, and broad
  enough to name **both** halves of the card (the write-side `Upload` scalar
  *and* the read-side file/image output objects), which a slug like `uploads` or
  `upload_scalar` undersells.

### Alternatives considered (and rejected)

- **`spec-037-upload_scalar-0_0_11.md` / `spec-037-uploads-0_0_11.md`.**
  Rejected: narrows the filename to the write half, while the read-side
  `DjangoFileType` / `DjangoImageType` change is equally in the card DoD.
- **`spec-037-files-0_0_11.md`.** Rejected: too vague; it does not name the
  write-side `Upload` scalar.

### Changes this Decision underwent

- **Revision 1** pinned the canonical structured filename and the
  `upload_file_image_mapping` topic slug over the two narrower slugs the card's
  write-half framing invited.
- **Post-ship:** the spec's stated home moved from `docs/` to `docs/SPECS/`, and its
  companions to `docs/SPECS/appx/`, when a later spec's [`docs/SPECS/NEXT.md`][next]
  Step 8 archive sweep relocated every prior spec in one pass (`AGENTS.md`: the move
  happens at the *next* spec's authoring, never at the completing spec's own merge).
  The filename itself is unchanged. The Decision body had gone on naming the
  pre-archive `docs/spec-037-…` path at three sites — its own text plus two clauses of
  Definition-of-done item 1, one of them a `check_spec_glossary.py` invocation that
  would fail as written — and all three now state the archived paths directly.

## Decision 2 — Card-scope boundary: file/image conversion only, not transport or storage abstraction

Spec: [Decision 2 — Card-scope boundary: file/image conversion only, not transport or storage abstraction][spec-037-d2].

### Justification (moved from the spec)

the card is sized **S** and its DoD is a converter-table change,
a mutation-input mapping, synthetic-model tests, and glossary docs. The `0.0.14`
[`TestClient`][glossary-testclient] card already owns multipart helper
ergonomics and explicitly depends on this card for the scalar, not vice versa.
Keeping scope here small prevents a file-upload transport design from delaying
the foundational mapping ([`START.md`][start] scope-creep rule).

### Alternatives considered (and rejected)

- **Ship only the read side now, write later.** Rejected: the card pairs read
  and write (its DoD names both), and the write seam already exists as a `036`
  `NotImplementedError` waiting to be filled — splitting would leave a
  half-mapped field type and a dangling seam.
- **Add a live fakeshop file model in this card.** Rejected: a `FileField` on a
  fakeshop model needs a media-root fixture and multipart HTTP plumbing —
  heavier than an S card; synthetic-model tests give full coverage
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

### Changes this Decision underwent

- **Revision 1** drew the scope boundary at file/image *conversion* — the output
  objects, the `Upload` re-export and input mapping, and the `0.0.11` version/doc
  wrap — and pushed transport, storage policy, image processing and nested upload
  writes onto named later cards.
- **Post-ship: no change, and that is a measured result rather than an omission.**
  Every clause of the scope boundary still holds at `HEAD`. The `037` cycle's
  conformance grading resolved every `Upload` mention in the package to five known
  classes — the scalar re-export, the three write-side annotation seams (the `0.0.12`
  / `0.0.13` reusers this Decision predicted), the write-value handler, and the
  resource-policy value budget — and found no image-processing, thumbnailing,
  signed-URL or remote-storage-adapter code anywhere in
  `django_strawberry_framework/`. `MediaSpecimen` is a model added to an existing
  fakeshop app, not the "example upload app" this Decision excluded. Recorded so a
  later pass does not re-derive it.

## Decision 3 — Read-side output types: `DjangoFileType` / `DjangoImageType` mirroring upstream

Spec: [Decision 3 — Read-side output types: `DjangoFileType` / `DjangoImageType` mirroring upstream][spec-037-d3].

### Justification (moved from the spec)

structured output is the read-side parity goal and the lossy
`str` was always a placeholder; mirroring upstream's field names lets a
migrating consumer's selection port unchanged. Two distinct types keep dimension
fields off non-image files. A separate output map keeps the read change off the
shared scalar/filter surface.

### Alternatives considered (and rejected)

- **Put the object types directly in `SCALAR_MAP`.** Rejected (the P0 finding):
  a [`FilterSet`][glossary-filterset] over a file column would emit an output
  object as a filter input — an invalid schema. The read-output map keeps the
  read change off the shared scalar/filter path; a package test pins the
  filter-input scalar lookup over a synthetic `FileField` / `ImageField` to a
  scalar `str` (`scalar_for_field` and `_scalar_from_model_field` both return
  `str`, `SCALAR_MAP` rows untouched) so this cannot regress silently. (The test
  pins the delegation path the FilterSet input generator uses rather than a full
  `FilterSet.Meta.fields` materialization, because django_filter raises an
  `AssertionError` on an auto-generated bare-`FileField` filter — an
  unrecognized field type — before any package code runs; the scalar-lookup pin
  is equally distinguishing.)
- **Reject file/image filters with `ConfigurationError` and route reads through
  a renamed converter.** Considered: cleaner once file filtering has a
  deliberate contract, but it is a behavior change for any consumer filtering on
  a file column's stored name today. Deferred — file columns keep their scalar
  `str` filter mapping until a file-filter contract is designed
  ([Risks](#risks-and-open-questions)).
- **Leave output as `str` and ship only `Upload`.** Rejected: fails the
  read-side DoD and leaves consumers hand-rolling file metadata.
- **Map output to `str | None` but document custom resolvers for metadata.**
  Rejected: preserves the weak contract and ignores the upstream parity target.
- **One `DjangoFileType` with nullable `width` / `height`.** Rejected: a
  non-image `FileField` has no dimensions; the `DjangoImageType` subclass scopes
  them to images, matching upstream.
- **Add a settings flag to keep `str` globally.** Rejected: a settings key for a
  one-line per-field override is over-engineering ([`AGENTS.md`][agents]); the
  annotation override is the finer-grained opt-out.

### Changes this Decision underwent

- **Revision 1** pinned the `FIELD_OUTPUT_TYPE_MAP` / [`SCALAR_MAP`][types-converters]
  split, the MRO-ordered `ImageField`-before-`FileField` rows, the read-only
  `convert_field_output` wrapper, and the `consumer_authored_fields` skip on the
  generated file resolver.
- **Post-ship:** `spec-048` (Secure output defaults, `0.0.14`, commit `567cc6d0`)
  removed `path` from the default `DjangoFileType` / `DjangoImageType` output and put
  it behind a per-column `Meta.filesystem_path_fields` opt-in, which swaps the column
  onto the new `DjangoFilePathType` / `DjangoImagePathType`. The reason is that the
  server's absolute filesystem path is deployment metadata — it can leak usernames,
  release directories, container mounts and tenant layout — and no client needs it to
  render a file. What it replaced: a four-subfield default of
  `name` / `path` / `size` / `url`, adopted field-for-field from upstream. The same
  card added a fourth parameter, `expose_filesystem_path`, to
  `convert_field_output`, so the three-parameter signature the Decision quoted is
  also superseded. The spec now states the three-subfield default, the opt-in
  siblings and the four-parameter signature directly; **the `path` claim had spread
  to twenty sites across nine sections**, three of which — two `path: String` lines
  inside the SDL example fences and one `` `path: str | None` `` in the Slice-1
  checklist — were invisible to the code-span grep that established the population,
  and were caught only by sweeping the bare token.

## Decision 4 — Read-side resolution: empty file as `null` and storage-safe subfield nullability

Spec: [Decision 4 — Read-side resolution: empty file as `null` and storage-safe subfield nullability][spec-037-d4].

### Justification (moved from the spec)

a file field with no file must resolve to `null`, not raise; a
storage quirk on one property must not take down the query; and the guard must
sit where the raising access happens (the subfield), which the parent resolver
cannot reach. The narrow catch list keeps the guard from swallowing genuine
resolver bugs and from masking security-relevant path errors. `name` is reliably
present whenever the object exists (the object is `null` for an absent file), so
it stays non-null.

### Alternatives considered (and rejected)

- **Guard only in the parent resolver (return the `FieldFile`, catch there).**
  Rejected (the P0 finding): subfield property access happens later, in
  Strawberry's default per-field resolution, outside the parent's `try/except`;
  a blank or vanished-file selection of `{ url }` would still 500. The guard
  must be at the field level.
- **A wrapper object whose properties perform the catch.** Considered and
  equivalent; resolver-backed `@strawberry.field`s on the two types are the
  chosen shape because they keep the guard in the type definition and need no
  extra wrapper class. Either satisfies the field-level requirement.
- **Match upstream's all-non-null subfields and document the `path` caveat.**
  Rejected: it leaves a latent 500 on non-filesystem storage / vanished files;
  the nullable-subfield contract is the safer engineering choice and the SDL
  divergence is small and documented.
- **Widen the object on `field.null` only — or on `null` / `blank`.** Rejected:
  the resolver returns `None` for *any* empty `FieldFile`, including on a
  `null=False, blank=False` column (legacy rows, direct `Model.objects.create()`,
  fixtures, and manual SQL all store `""`), so keying nullability on the column
  flags at all leaves a guaranteed non-null violation. The object is **nullable
  by default**; `required_overrides` is the explicit opt-in to a non-null
  contract.
- **Catch a broad `Exception` (or fold `SuspiciousFileOperation` into the
  guard) by default.** Rejected: it would hide real bugs and mask path-traversal
  signals; the catch list is narrowed to storage-shaped errors.

### Changes this Decision underwent

- **Revision 1** pinned the two-layer nullability contract — the parent resolver's
  empty-`FieldFile`-to-`None` rule and the default-nullable object shape, plus the
  per-subfield `_safe_file_attr` guard with its narrow catch list and the deliberate
  `SuspiciousFileOperation` carve-out.
- **Post-ship:** the subfield-nullability half is narrowed by `spec-048`'s default-`path`
  removal (see [Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)):
  `path` is still nullable and still guarded by `_safe_file_attr`, but only on the
  opt-in `DjangoFilePathType` / `DjangoImagePathType`, so every spec sentence
  promising a nullable `path` subfield on the default output now carries that
  qualifier. Nothing about the parent-level empty-`FieldFile` rule, the narrow catch
  list, or the `SuspiciousFileOperation` carve-out changed.
- **Post-ship:** the `required_overrides` opt-in clause was correct and executing at
  `HEAD` but had **no end-to-end test** — the only pin sat on
  `convert_field_output(force_nullable=…)`, one layer below the contract's own
  spelling, so nothing exercised `Meta` reaching the file branch. The
  `037` residual-reconciliation cycle closed it with three rows in
  `tests/types/test_base.py`
  (`::test_meta_required_overrides_forces_non_null_file_output`,
  `::test_meta_required_overrides_forces_non_null_image_output`,
  `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op`), each carrying an
  un-overridden sibling column in the same type as its control. That is the cycle's
  only code change. The mis-homing that let the gap survive is recorded under
  [Non-Decision deliberation](#non-decision-deliberation).

## Decision 5 — Re-export `Upload` rather than register it

Spec: [Decision 5 — Re-export `Upload` rather than register it][spec-037-d5].

### Justification (moved from the spec)

registering `Upload` in `_PACKAGE_SCALAR_MAP` would be redundant
(it already resolves) and misleading (it would imply a binding requirement that
does not exist). [`strawberry-graphql-django`][upstream-field-types] takes
exactly this approach — its `input_field_type_map` maps `FileField` /
`ImageField` to the bare `Upload` `NewType` with no custom scalar registration,
relying on the built-in registry. Re-using Strawberry's scalar also keeps
multipart-request parsing on the engine.

### Alternatives considered (and rejected)

- **Add `Upload` to `_PACKAGE_SCALAR_MAP` for symmetry with `BigInt`.**
  Rejected: redundant (the default registry already resolves it) and
  misleading; it would also manufacture an `extra_scalar_map={Upload: ...}`
  collision contract for a scalar the package does not own.
- **Define a wrapper `NewType` instead of re-exporting Strawberry's `Upload`.**
  Rejected: a second upload scalar would be incompatible with the engine's
  built-in multipart conventions and force clients to special-case it.
- **Do not export `Upload` at all; let consumers import it from Strawberry.**
  Rejected: generated inputs reference `Upload`, and a consumer hand-writing an
  upload field should reach for it at the package root alongside
  [`BigInt`][glossary-bigint-scalar] — re-export is the public-surface
  convenience ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)).

### Changes this Decision underwent

- **Revision 1** pinned re-export over registration, and the
  [`BigInt`][glossary-bigint-scalar] contrast that explains why a structurally
  identical scalar needs a `_PACKAGE_SCALAR_MAP` entry and `Upload` does not.
- **Post-ship: no change to the Decision.** Both halves hold at `HEAD` —
  `scalars.py` re-exports `Upload` and `UploadDefinition` and keeps `Upload` out of
  `_PACKAGE_SCALAR_MAP`. One instruction *attached* to it did change: the Slice-2
  sub-check told `scalars.py` to re-point its stale `TODO-ALPHA-035-0.0.11` docstring
  anchor to `TODO-ALPHA-037-0.0.11`. The shipped code **removed** the anchor instead,
  which is what [`docs/builder/BUILD.md`][build-md] `## Cross-slice integration pass`
  step 6 requires once the seam it stages ships — so the sub-check as written would
  today create the very finding that step exists to catch. The sub-check now says
  remove.
- **Post-ship:** the Decision's re-export sentence claimed [`scalars.py`][scalars]
  **and the package root** re-export `Upload` *and* `UploadDefinition`. True of
  `scalars.py`, false of the root: `scalars.py:25` is
  `from strawberry.file_uploads.scalars import Upload, UploadDefinition` and lists both
  in its `__all__`, while [`__init__.py`][init] imports and exports `Upload` alone —
  `grep -c 'UploadDefinition' django_strawberry_framework/__init__.py` is **0** at
  `HEAD`, against **2** for `scalars.py`. No contract moved: the root never carried
  `UploadDefinition`, so this was a false description of the shipped surface rather
  than a later card's deliberate change, and the sentence now states the split — both
  modules re-export `Upload`, `UploadDefinition` stops at `scalars.py`. The spec's own
  `## Slice checklist` Slice-2 sub-check had scoped the `UploadDefinition` re-export to
  `scalars.py` correctly all along, which is the internal evidence that only the
  Decision-5 sentence was wrong, and is why the bullet above graded both halves
  conformant while citing `scalars.py` alone.

## Decision 6 — Write-side input mapping: the mutation seam becomes `Upload`

Spec: [Decision 6 — Write-side input mapping: the mutation seam becomes `Upload`][spec-037-d6].

### Justification (moved from the spec)

the seam was built for exactly this card; reusing the generator
prevents a second write-input path just for uploads and keeps custom-input merge
consistent with every other scalar.

### Alternatives considered (and rejected)

- **Keep the `NotImplementedError` and require `Meta.exclude`.** Rejected: that
  was the staging guard before `037`; after this card it would make the card a
  no-op for generated mutation inputs.
- **Require a consumer-authored `input_class` for upload fields.** Rejected:
  violates the generated-input goal and creates a bespoke escape hatch where the
  core package should know the mapping.
- **Represent uploads as `str` paths.** Rejected: unsafe and not a GraphQL
  upload contract; the client sends multipart upload values, not server paths.
- **Add a dedicated file-assignment branch in the write resolver up front.**
  Rejected by default (the P2 finding): the existing scalar `setattr` /
  `model(**attrs)` path already assigns an `UploadedFile`, so a branch is added
  only if a test proves the generic path fails — avoiding a divergent write path
  for files.

### Changes this Decision underwent

- **Revision 1** pinned the seam-to-`Upload` swap, the omittable-is-not-nullable rule,
  the verify-before-branching instruction for the write resolver, and the lifting of
  the [`spec-036`][spec-036] CR-6 file-column merge-override exception.
- **Post-ship: no contract change.** The write side is conformant in every clause —
  `model_column_write_kind` returns `FILE` for both field classes,
  `model_column_write_annotation` returns `Upload`, the Python attribute is the plain
  field name, `mutations/resolvers.py` routes `FILE` to the generic scalar handler
  with no file-specific assignment branch (the "verify, do not add" instruction was
  followed), and no `NotImplementedError` seam survives. What changed is only how the
  spec *cites* that seam: three sentences carried a
  `#"Upload staged seam (TODO-ALPHA-037-0.0.11)"` substring anchor that resolves to
  nothing at `HEAD`, and now name the live symbol
  `mutations/inputs.py::model_column_write_annotation` instead. The fourth site, in
  `## Current state`, is a dated observation of the pre-build repo where the seam
  genuinely existed, and stands.

## Decision 7 — Public surface: three net-new root-exported symbols

Spec: [Decision 7 — Public surface: three net-new root-exported symbols][spec-037-d7].

### Justification (moved from the spec)

root export matches the audience — `Upload` is referenced
wherever a consumer hand-writes an input field, and the two output types are the
field types a consumer names in custom resolvers / `strawberry.field`
annotations; all belong at the root alongside [`BigInt`][glossary-bigint-scalar]
/ [`DjangoType`][glossary-djangotype], parallel to how
[`BigInt`][glossary-bigint-scalar] ([`spec-017`][spec-017]) is root-exported.
These are **framework-provided generated / helper output types**, not a new
consumer-authored decorator API — they stay within the package's `class
Meta`-driven, DRF-first posture ([`GOAL.md`][goal]) and add no decorator-first
consumer surface.

### Alternatives considered (and rejected)

- **Export only from a `scalars` / `types` namespace.** Rejected: the symbols
  are referenced inside schema modules alongside root-exported types; the
  package's settled posture is to root-export consumer-facing scalars and types.
- **Do not export the output types (auto-generated, never named).** Rejected: a
  consumer overriding a file field's resolver, or annotating a computed file
  field, must be able to name them; the glossary already lists them as public.

### Changes this Decision underwent

- **Revision 1** pinned the three net-new root exports and the argument that they are
  framework-provided output types rather than a decorator-first consumer API.
- **Post-ship:** two further file/image symbols are root-exported —
  `DjangoFilePathType` and `DjangoImagePathType`, from the same `spec-048` commit
  `567cc6d0` — so five are exported in total. The Decision's own count was **not**
  changed: "three net-new" is a statement about what *this card* added, of the same
  class as [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)'s
  `0.0.11` cut, and a card-scoped completion claim stays true however many symbols a
  later card adds. What did change is the `## User-facing API` sentence that read as a
  claim about the surface rather than about the card.

## Decision 8 — No new `Meta` key, no new setting, no dynamic storage policy

Spec: [Decision 8 — No new `Meta` key, no new setting, no dynamic storage policy][spec-037-d8].

### Justification (moved from the spec)

the repository rule is explicit — add settings keys only when the
feature needs them ([`AGENTS.md`][agents]). The file/image mapping has no
project-wide policy knob; the existing scalar-override semantics already provide
the escape hatch.

### Alternatives considered (and rejected)

None. The spec recorded no rejected alternative under this Decision; its
no-new-key boundary is argued from the repository rule alone.

### Changes this Decision underwent

- **Revision 1** pinned the no-new-`Meta`-key / no-new-setting boundary. The Decision's
  standing architectural line for a hypothetical future file/image setting —
  [`conf.py`][conf] owns normalization, a domain module owns key-specific validation,
  and any request-affecting setting is resolved and stamped once at finalization —
  was **held back in the spec** as implementation-relevant instruction; only the
  four-line justification paragraph moved here.
- **Post-ship:** the "no new `Meta` key" half is now false as a standing statement
  about the surface, though it remains true of this card: `spec-048` added
  `filesystem_path_fields` to `types/base.py::ALLOWED_META_KEYS`. The "no new setting"
  half still holds outright — `DJANGO_STRAWBERRY_FRAMEWORK` carries nine feature keys
  at `HEAD` and none is file- or image-related, and no query-time settings read was
  introduced. The heading and opening sentence were therefore kept (card-scoped, like
  [Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)'s
  count) and the standing enumeration underneath rewritten, since it had presented
  `Meta.fields` / `Meta.exclude` / `nullable_overrides` / `required_overrides` as the
  complete set of `Meta` keys touching file/image conversion. **The claim had two
  sites, not one:** the second is `## Edge cases and constraints`' final bullet, which
  asserted `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` are "byte-unchanged" — flatly
  false at `HEAD`, and the site a Decision-only fix would have left standing.

## Decision 9 — Test placement: package tests own synthetic file/image models

Spec: [Decision 9 — Test placement: package tests own synthetic file/image models][spec-037-d9].

### Justification (moved from the spec)

None. The spec recorded no `Justification:` block under this Decision; its
reasoning is carried by the Decision body — which stays in the spec — and by the
two rejected alternatives below.

### Alternatives considered (and rejected)

- **Add a live fakeshop file model + multipart HTTP test now.** Rejected: out of
  scope for an S converter card.
- **Mock the storage backend instead of a real `tmp_path` storage.** Rejected: a
  real temp-dir storage exercises `FieldFile.path` / `.size` / `.url` honestly;
  mock only the non-filesystem-`path` case, where a real backend is impractical,
  to cover the
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)
  guard.

### Changes this Decision underwent

- **Revision 1** pinned the synthetic-model test strategy, the `schema_editor()`
  fixture shape, and the deferral of a live fakeshop upload surface to
  [`TODO-BETA-066-0.1.5`][kanban].
- **Post-ship:** a round-4 review on 2026-06-20 reversed the live-coverage half of that
  deferral, and the spec recorded the reversal as a `> **Superseded (post-ship, …)**`
  block quoting its own retracted position — the one shape
  [`docs/builder/BUILD.md`][build-md] `## Spec rationale extraction` forbids outright
  (the spec "never narrates its own history"). The block is reproduced below,
  verbatim but for the fakeshop-activation card id, which carries its current
  spelling; its `below` and `follows` references point at the Decision-9 body it used
  to precede in the spec, not at anything in this file.
- **Post-ship, the direct-contract rewrite.** Removing that block was correct and left
  a worse defect behind: the block had been the **only** signal that the body under it
  was retracted, so a self-contradictory Decision became a uniformly wrong one, which
  is harder to notice. Decision 9's body now states the shipped two-tier split
  directly and without chronology — live `/graphql/` tests own the read output
  objects, the SDL shapes, the `path` opt-in's absence and presence, and a real
  multipart upload; the synthetic-model package tests own the storage-backend fault
  injection and corrupt-dimension edges a live request cannot reach. What it replaced:
  "No fakeshop model has a file/image field", "live `/graphql/` tests are added
  **only** if implementation naturally exposes a file/image field", and the deferral
  of a live upload surface to [`TODO-BETA-066-0.1.5`][kanban] — all three false since
  this card's own final commit `4dca5ec9`. **The falsified deferral had five sites,
  not the two the finding first named:** Decision 9's body, `## Out of scope`,
  `## Non-goals` bullet 2, `## Test plan`'s "Live HTTP tests" bullet, and — found only
  by re-deriving the population rather than trusting the list — the `## Test plan`
  preamble's "with no live fakeshop surface". Half the population shares no grep
  token, so a token-only sweep under-counts it by more than half.
- **Post-ship:** the fixture-shape paragraph's claim of "**no** fakeshop app churn"
  went with it; the paragraph now scopes itself to the fault-injection tier, which is
  what it actually describes.

> **Superseded (post-ship, 2026-06-20 round-4 review).** A live fakeshop
> file/image acceptance surface was added after all. The `scalars` app gained a
> `MediaSpecimen` model (`FileField` + `ImageField`), a `MediaSpecimenType`, and a
> file-backed `createMediaSpecimen` mutation, with live `/graphql/` tests in
> `examples/fakeshop/test_query/test_uploads_api.py`: the read output objects, the
> default-nullable SDL shape (a *required* column rendering nullable), the
> empty-file object-`null` case, the `Upload` input SDL, and a **real multipart
> upload** (the fakeshop `GraphQLView` enables `multipart_uploads_enabled=True`).
> The [`examples/fakeshop/test_query/README.md`][test-query-readme] live-coverage
> rule prevailed over the "prefer the card" deferral recorded below: file/image
> output IS SQLite-reachable, so its public HTTP contract must be earned live. The
> synthetic-model package tests below **remain** for the storage-backend
> fault-injection and corrupt-image-dimension edges, which need a mocked
> non-filesystem backend and so are genuinely unreachable from a live request. The
> broader products/fakeshop activation stays [`TODO-BETA-066-0.1.5`][kanban]. The
> original (now-historical) deferral rationale follows.

## Decision 10 — This card owns the final `0.0.11` version bump

Spec: [Decision 10 — This card owns the final `0.0.11` version bump][spec-037-d10].

### Justification (moved from the spec)

`037` closes the `0.0.11` feature set, so it owns the cut —
exactly the card `036` Decision 13 deferred to. The bump moves only after the
mapping, tests, and docs are complete (Slice 4), never in Slice 1.

### Alternatives considered (and rejected)

- **Defer again to a separate release-alignment card.** Rejected: no such WIP
  card exists, and `036` already deferred to this joint cut; a second deferral
  would orphan the bump.
- **Treat `036` (DONE) as a co-WIP card and defer per the multi-card rule.**
  Rejected: the NEXT.md rule keys on the `## In progress` column, where `037`
  stands alone; a DONE card is not a WIP co-owner.
- **Bump in Slice 1.** Rejected: the version should move only after the feature
  and docs are complete.

### Changes this Decision underwent

- **Revision 1** pinned this card as the joint `0.0.11` cut that [`spec-036`][spec-036]
  Decision 13 deferred to, and the five-file version quintet Slice 4 aligns.
- **Post-ship: deliberately not updated.** `__version__` is `0.0.15` at `HEAD`, four
  patch releases past this card's target. The Decision and Definition-of-done item 7
  describe a cut that **happened**, so a shipped-version statement about the release
  this card closed is correct as it stands and is never "refreshed" to the current
  version. Recorded because the sentence reads stale at a glance and invites exactly
  that edit.

## Risks and open questions

The spec's whole `## Risks and open questions` body. It is a build-time
deliberation instrument — each item pairs a preferred answer for the `0.0.11` cut
with a fallback if implementation proved the preferred answer wrong — so the body
moved and the spec keeps the heading and a pointer here. Nothing was held back:
every rule any item states is also stated by the Decision that answered it, by
the spec's `## Edge cases and constraints`, or by its `## Test plan`, so no item
carries a sentence the implementation depends on. It moved verbatim and stays
verbatim; the one premise that is false at `HEAD` (the Pillow dependency claim)
is corrected under [Provenance of this record](#provenance-of-this-record) rather
than edited inside moved text.

Each item names a preferred answer for the `0.0.11` cut and a fallback if
implementation reveals it is wrong.

- **Clearing an existing file via mutation input.** Preferred answer
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)):
  omitted upload leaves unchanged; provided upload replaces; an explicit `null`
  on a `null=False` file column is already a field-keyed `FieldError`
  (`_explicit_null_error`), so it can never be an accidental clear; clearing is
  not promised unless a `null=True` field plus `null` assignment already works
  through the shipped mutation pipeline. Fallback: add an explicit clear-file
  sentinel in a future form/serializer flavor if real users need it — do not
  overload empty upload values in this card.
- **Output subfield nullability vs upstream parity.** Preferred answer
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)):
  `path` / `size` / `url` / `width` / `height` nullable (storage-safe), `name`
  non-null — a deliberate, documented divergence from upstream's all-non-null
  `path: str`. Fallback: if nullable subfields prove awkward in
  Strawberry/Django, keep `path` nullable at minimum and document
  local-storage-only behavior for the others, but never let an empty/unreadable
  file descriptor raise.
- **Where to define `DjangoFileType` / `DjangoImageType`.** Preferred answer
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)):
  define them in [`types/converters.py`][types-converters], where the
  field-class mapping lives, and root-export them. Fallback: a tiny
  `types/files.py` module if importing them from `converters.py` creates a cycle
  — do not create a broad `fields/` package that collides conceptually with the
  planned `FieldSet`.
- **Image dimension dependency + test strategy.** Production `width` / `height`
  stay nullable and resolve from Django's image-file object
  (`ImageFieldFile.width` / `.height`) through the same `_safe_file_attr` guard.
  The card must pick a *test* strategy up front, because Django's **model**
  `ImageField` and its dimension accessors require Pillow, and the project does
  **not** currently declare Pillow in runtime or dev dependencies. **Preferred
  answer: add Pillow as a dev/test-only dependency** — it joins `pytest-django`
  in the dev extras (the package itself never imports it, so no runtime surface
  changes) — and exercise `width` / `height` against a tiny valid in-memory image
  (a few-byte PNG) over the synthetic-model `tmp_path` storage. Fallback: if
  adding Pillow is undesirable, keep the production fields nullable and unit-test
  the resolver logic with a lightweight stand-in object exposing `width` /
  `height`, marking real image parsing out of scope. Either way, do **not**
  `pytest.skip` the dimension tests when Pillow is absent: under
  `fail_under = 100` a conditional skip would let the gate pass over uncovered
  dimension branches. Pillow (preferred) or the stand-in (fallback) makes the
  coverage unconditional.
- **File-column filtering contract.** Preferred answer
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)):
  file columns keep their scalar `str` filter mapping in `SCALAR_MAP` (no
  regression) — i.e. filtering the stored **name / path string**, not file
  metadata (`url` / `size` / `width` / `height`) — and the read-output objects
  live in a separate `FIELD_OUTPUT_TYPE_MAP`, so no output type leaks into a
  [`FilterSet`][glossary-filterset] input. Fallback: if string-filtering a file
  column proves meaningless, reject file/image filters with a
  [`ConfigurationError`][glossary-configurationerror] once a deliberate
  file-filter contract is designed — a follow-up, not this card.
- **Path-safety exception policy.** Preferred answer
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)):
  `SuspiciousFileOperation` is **not** folded into the `_safe_file_attr`
  degrade-to-`null` catch; it propagates as a top-level error so a
  path-traversal / hostile-name condition stays visible. Fallback: if operators
  prefer graceful degradation, add it to the catch set — but the default is
  visibility.
- **Storage-metadata read cost.** Preferred answer
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)):
  selecting `size` / `url` / `width` / `height` asks Django storage for metadata
  per selected object and subfield; the framework guards storage-shaped failures
  but does **not** cache or batch storage calls in this card, and the optimizer
  cannot prefetch object-store metadata. Fallback: a batching / caching layer (or
  a storage-metadata dataloader) is a follow-up if profiling shows it matters —
  not this card.
- **Card conflict — stale `"Pairs with 028"` note.** The card's "Other" section
  says "Pairs with 028", but `028` is the
  [ordering subsystem][glossary-orderset] (`DONE-028-0.0.8`), unrelated to
  uploads. Preferred reading: the genuine pairing is with the mutations card
  [`DONE-036-0.0.11`][kanban] (whose input seam this card fills) — the `028`
  reference is a stale copy-paste. Recorded per the [`docs/SPECS/NEXT.md`][next]
  "prefer the card, surface the conflict" rule.
- **Card conflict — stale `mutations/ (planned)` predicted file.** The card's
  "Predicted files" annotates
  `django_strawberry_framework/mutations/ (planned)`, but `mutations/` shipped
  with [`DONE-036-0.0.11`][kanban]. Preferred reading: the directory exists;
  this card edits [`mutations/inputs.py`][mutations-inputs] /
  [`mutations/resolvers.py`][mutations-resolvers] in place.
- **Card conflict — stale `TODO-ALPHA-035-0.0.11` in the `scalars.py`
  docstring.** [`scalars.py`][scalars] #"Future scalars (e.g. ``Upload`` per TODO-ALPHA-035-0.0.11) land here."
  names `035`, but `035` is the
  optimizer-hardening card; the real `Upload` owner is this card, `037`.
  Preferred reading: a stale number — Slice 2 corrects the docstring to
  `TODO-ALPHA-037-0.0.11`. (The [`mutations/inputs.py`][mutations-inputs] seam
  already names `037` correctly.)

## Non-Decision deliberation

Findings and provenance that belong to no single Decision.

- **The spec's `## Current state` was graded clause by clause, and one clause of
  one bullet was rewritten.** [`docs/builder/BUILD.md`][build-md]
  `### `## Current state`: observations stand, predictions do not` licenses a
  dated **observation** of the pre-build repo to stand while a falsified
  **prediction** is rewritten, and one bullet can carry both. The borderline case
  is the last bullet, "No example app uses a file/image column", which pairs a
  reproducible command (`grep -rln "FileField\|ImageField" examples/`) with an
  inference. Graded: the heading claim, the command and its reported output, and
  the inference that "the read-side break invalidates no in-repo schema" are all
  dated observations of the repo as the spec was authored — the section header
  dates them, and a reader who re-runs the grep today is measuring a different
  repo, not catching an error. They stand, command included. The fourth clause,
  "the card's 'synthetic-model tests' scoping is **sufficient** for coverage", is
  a **prediction about this build's outcome**, nothing dates it, and the build
  itself falsified it by adding `MediaSpecimen` and live `/graphql/` tests. That
  clause was rewritten to point at
  [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models),
  which now carries the settled placement. Every other `## Current state` bullet
  is observation throughout and was left untouched.
- **The ten `Decision N` anchors survived the move untouched, and that is a
  measured result rather than an assumption.** `spec-036`'s execution of this move
  had to repair a broken slug with 16 uses and re-point five uses across four
  anchors naming spec sections its companion lacked. `spec-037` carried neither
  defect: all 21 anchor occurrences in the moved text resolve locally here.
- **The ten surviving `[Risks](#risks-and-open-questions)` uses were re-pointed at
  this file, deliberately.** The move left them resolving in two hops: they landed
  on a spec heading that now contains only a pointer here. Every one of the ten
  sentences promises the reader *deliberation* — a settled dependency, a fallback,
  an item deferred — and that deliberation is here, so the destination and the
  promise now agree in one hop. The alternative considered and rejected was leaving
  them: it keeps ten contract sentences untouched, but it makes the two-hop
  indirection permanent and leaves a reader who follows one at a stub. The spec
  keeps its `## Risks and open questions` heading and its pointer paragraph; it
  simply has no inbound in-page anchors any more.
- **`## Test plan`'s converter bullet mis-homed the `Meta`-level requirement, and
  that mis-homing is why the gap survived to the `037` cycle.** The bullet asked
  for "`Meta.nullable_overrides` / `Meta.required_overrides` still win" inside the
  `tests/types/test_converters.py` bullet — but that file tests
  `convert_field_output`, whose parameter is `force_nullable`; `Meta` never
  reaches it. A builder reading the sentence satisfies it literally, at the
  converter seam, and the contract's own spelling goes unpinned. The clause is now
  split: the `force_nullable` half stays on `tests/types/test_converters.py`, and
  a new bullet homes the `Meta.*_overrides` half on `tests/types/test_base.py`,
  citing the three node ids that discharge it by name rather than re-describing
  the requirement — so the sentence and its pin cannot drift apart again. This is
  the single highest-value edit in the reconciliation, because it is the sentence
  that, written correctly, would have prevented the gap.
- **The same bullet spelled the filter-input pin two ways, and the narrower
  spelling is the correct one.** `## Test plan` asked for "a `FilterSet` over a
  synthetic `FileField`"; the Slice-1 sub-check narrowed it to the *delegation
  path* because django_filter's auto `Meta.fields` filter for a bare `FileField`
  raises an `AssertionError` before any package code runs. The narrowed form is
  what shipped and is equally distinguishing. `## Test plan` was reconciled to the
  delegation spelling; the `FilterSet` form was **not** restored.
- **`TestClient`'s forward-looking tense was falsified across seven sites, and
  five were rewritten.** `spec-043` shipped the `0.0.14` multipart helper, and
  `examples/fakeshop/test_query/test_uploads_api.py` imports and drives it. The
  `## Edge cases` bullet promising consumers hand-rolled multipart handling
  "until the `0.0.14` `TestClient` helper lands", the `## Non-goals` bullet calling
  it "the future card", and the `## Out of scope` entry citing it by the
  now-`DONE` card id `TODO-ALPHA-043-0.0.14` were all rewritten to the settled
  ownership split. Two further sites were left: they describe the *wording* Slice 4
  put into `README.md` / `docs/README.md`, where scoping the claim to the scalar
  rather than to full multipart ergonomics is still exactly right.
- **The `Justification:` / `Alternatives considered (and rejected):` pairing is
  not 1:1, and the two gaps are real rather than an extraction artifact.**
  Decision 8 has a justification and no rejected alternative; Decision 9 has two
  rejected alternatives and no justification block. Both gaps are recorded
  explicitly with a `None.` under the missing heading in this file, so a later
  reader cannot mistake a genuine absence for a chunk this move dropped.
- **Routed to the maintainer, out of the reconciliation cycle's reach.** The cycle
  was fenced to spec files and package `.py` source, so no closeout-agentflow doc
  was touched. Two consequences are worth a maintainer's eye, neither a defect
  found in this spec: `docs/GLOSSARY.md`'s `DjangoFileType` / `DjangoImageType`
  entries and its `Meta.required_overrides` entry are the published home of the
  contracts this pass corrected here, and the two path-bearing siblings
  `DjangoFilePathType` / `DjangoImagePathType` are root-exported symbols whose
  glossary and `docs/TREE.md` presence this cycle could not verify or fix.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-bigint-scalar]: ../../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-filterset]: ../../GLOSSARY.md#filterset
[glossary-orderset]: ../../GLOSSARY.md#orderset
[glossary-testclient]: ../../GLOSSARY.md#testclient

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-017]: ../spec-017-deferred_scalars-0_0_6.md
[spec-036]: ../spec-036-mutations-0_0_11.md
[spec-037-d10]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-10--this-card-owns-the-final-0011-version-bump
[spec-037-d1]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-1--spec-filename-and-canonical-naming
[spec-037-d2]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-2--card-scope-boundary-fileimage-conversion-only-not-transport-or-storage-abstraction
[spec-037-d3]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream
[spec-037-d4]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability
[spec-037-d5]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-5--re-export-upload-rather-than-register-it
[spec-037-d6]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload
[spec-037-d7]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-7--public-surface-three-net-new-root-exported-symbols
[spec-037-d8]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-8--no-new-meta-key-no-new-setting-no-dynamic-storage-policy
[spec-037-d9]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-9--test-placement-package-tests-own-synthetic-fileimage-models
[spec-037-terms]: spec-037-upload_file_image_mapping-0_0_11-terms.csv
[spec-037]: ../spec-037-upload_file_image_mapping-0_0_11.md

<!-- docs/builder/ -->
[build-037]: ../../builder/DONE/build-037-upload_file_image_mapping-0_0_11.md
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[conf]: ../../../django_strawberry_framework/conf.py
[init]: ../../../django_strawberry_framework/__init__.py
[mutations-inputs]: ../../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../../django_strawberry_framework/mutations/resolvers.py
[scalars]: ../../../django_strawberry_framework/scalars.py
[types-converters]: ../../../django_strawberry_framework/types/converters.py

<!-- tests/ -->

<!-- examples/ -->
[test-query-readme]: ../../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-field-types]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/types.py
