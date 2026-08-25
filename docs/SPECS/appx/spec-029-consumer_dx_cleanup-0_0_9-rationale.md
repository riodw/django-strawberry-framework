# Rationale companion: spec-029 (`DjangoType` consumer-DX cleanup pass)

Companion to [`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029]. It carries that spec's **deliberative layer** and nothing else: the seven-revision review history that produced the contract, every Decision's justification, every alternative a Decision rejected and why it lost, and the risk / open-question deliberation that settled the card's design questions. The spec carries the contract; this file carries how the contract was arrived at. Neither duplicates the other — the text here **left** the spec.

Read this when checking a finished implementation against the reasoning that produced it, or before re-opening a settled question. Worker 2 never reads it (`docs/builder/BUILD.md` `### Who reads it, and when`).

## Provenance of this record

Created by the `029` residual-reconciliation cycle's Slice 1 (recorded in `docs/builder/bld-slice-1-029-rationale_extraction.md`). `spec-029` shipped long ago with a `-terms.csv` companion and no `-rationale.md` sibling; this file closes that gap.

Measured against the spec at `HEAD` before the move (170,042 bytes, 823 lines):

- the whole `Revision history (kept inline so the spec is self-contained):` block — its preamble plus seven `Revision N` entries over 47 lines, **17,883** bytes. It is **not** reproduced verbatim here; [Revision history](#revision-history) below is an index into the per-Decision record, and says why.
- **12** `Justification:` blocks and **12** `Alternatives considered (and rejected):` blocks, one pair under each of Decisions 1-12, carrying **33** justification bullets and **25** rejected alternatives in total (2 / 1 / 4 / 4 / 2 / 1 / 2 / 3 / 1 / 2 / 2 / 1 for Decisions 1-12), **16,278** bytes.
- the body of `## Risks and open questions` — `HEAD` lines 643-654, its preamble plus **10** items, each written as a preferred-answer / fallback pair, **6,620** bytes. That shape is a build-time deliberation instrument, not a contract, so the whole body moved and the spec keeps the heading, a pointer, and the one rule that outlives the build (see [Risks and open questions](#risks-and-open-questions) below).
- two cross-reference clauses the move itself falsified, 181 bytes: the Predecessors line's "and are flagged in Risks and open questions as the missing-glossary-heading caveat" and the Current-state glossary bullet's "and flagged in Risks and open questions". Both were **deleted, not moved** — the section they name no longer flags anything.

Those four routes account for **40,962** bytes of the pre-move spec (17,883 + 16,278 + 6,620 + 181). The move put framing back — the header pointer, twelve per-Decision `Rationale companion —` pointers, the surviving Risks rule, and fourteen new link definitions — leaving the spec at 133,839 bytes, a net drop of **36,203**; the 4,759-byte difference between those two figures is that framing plus one blank separator line inside the Risks range which the spec kept. A later pass in the same slice cut a further **126** bytes of chronology framing from four sites in the spec, so the spec on disk now measures **133,713** bytes, **36,329** below `HEAD`.

**Where the 40,781 bytes of moved sections are.** Each figure is a byte count of whole `HEAD` lines, newlines included, and each section's parts sum to that section.

- **The twelve `Justification:` / `Alternatives considered (and rejected):` blocks, 16,278 bytes.** **15,273** reproduced byte-for-byte; **660** in the 24 label lines (twelve `Justification:` at 15 bytes, twelve `Alternatives considered (and rejected):` at 40) which became `###` headings here; **345** in the one line whose in-page anchor was repointed. 15,273 + 660 + 345 = 16,278.
- **The `## Risks and open questions` body, 6,620 bytes.** Reproduced byte-for-byte, all of it.
- **The `Revision history` block, 17,883 bytes.** **2,173** — Revision 1's entry, which is already an index of the twelve Decisions — reproduced byte-for-byte, plus the 1-byte blank line after it; **1,478** in the six Revision 2-7 header lines, kept but each extended with where that round's findings landed; **14,169** in the 38 finding sub-bullets, deliberately not reproduced, because each finding is recorded under the Decision it changed; and **62** in the preamble line, deleted rather than reproduced, because its claim that the history is kept inline is exactly what this move made untrue. 2,173 + 1 + 1,478 + 14,169 + 62 = 17,883.

Everything else in this file is its own framing — the provenance above, the twelve `### Changes this Decision underwent` sections that carry the revision history's findings under the Decision each one actually changed, the `## Non-Decision deliberation` grouping for findings belonging to no Decision, and the link block.

**Kept in the spec, deliberately.** The `### Reference-package parity checkpoint` table under `## Borrowing posture` and both paragraphs around it stayed, for two different kinds of reason. **The table is mechanically forced**: it holds the **only** spec links for three terms the companion CSV requires to be linked — `RelatedFilter`, `RelatedOrder`, and `RelatedAggregate` — so moving it fails [`scripts/check_spec_glossary.py`][check-spec-glossary], and the CSV is not this slice's to edit. Removing the whole section from a scratch copy was tested and fails on exactly those three terms. **The surrounding prose is a judgement, not a constraint**: the same test with only the prose removed and the table kept passes. It stays anyway, because it scopes the card ("it does not itself port a parity surface — it hardens schema construction, adds a type-metadata inspection command, and expresses GraphQL nullability overrides through `Meta`"), which is Non-goals-shaped and therefore contract, and because its closing sentence is the table's lead-in and cannot leave without orphaning it. Only the *provenance* of the table left, as the rev5 parity-checkpoint entry under [Documentation-coherence passes](#documentation-coherence-passes).

**Not byte-verbatim in one respect.** One reproduced line — the third rejected alternative under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) — carried an in-page `#out-of-scope-explicitly-tracked-elsewhere` anchor naming a spec section this file does not have. It was repointed to the spec through a reference-style link rather than left to dangle. The `#decision-N--...` anchors and `#risks-and-open-questions` were left as they were: this file carries headings with exactly those slugs, so they resolve locally, which is where a reader of a moved sentence wants to land.

**One outbound citation this move broke, repaired in the same slice.** [`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`][spec-004-rationale] cited `` `P1.1 — stale extension-lifecycle model` `` against the spec — a string that lived only in the spec's revision history and now lives only here. Its citation was repointed at this file. No gate can see this class of breakage: [`scripts/check_citations.py`][check-citations] resolves `path::Symbol` only and puts `docs/` out of scope, and a prose citation is invisible to any link check, so the sweep for it belongs to the slice that moves the text.

**Not corrected here.** Slice 1 moved text; it did not reconcile the spec against `HEAD`. Several Decisions describe a shipped surface that later cards widened or renamed, and one Definition-of-done item is false at `HEAD`. Those are Slice 3's, and the corrections land under this file's per-Decision headings when that pass runs.

**Corrected by Slice 3.** That pass ran, and its record is the `Post-ship` bullets under Decisions 3, 4, 7, 8 and 10 plus the two under [Documentation-coherence passes](#documentation-coherence-passes). Each names the shipped behavior, the card that changed it where that is attributable, and — where a Decision's own words stopped being true — the claim it may no longer make. The corrections themselves are in the spec, stated directly and without chronology; this file is where the chronology lives. Its record is `docs/builder/bld-slice-3-029-spec_reconciliation.md`.

## Revision history

Seven revisions produced the contract. This section is the **index** to them and carries no finding text of its own: every finding is recorded in full under the Decision it changed, in that Decision's `### Changes this Decision underwent` section, or — when it belongs to no Decision — under [Non-Decision deliberation](#non-decision-deliberation). The chronology is what a reviewer of a decision's history needs; a second verbatim telling of the 38 findings would be a second thing to keep in step, so what is kept here is each round's own identity (what it reviewed, what it was checked against, how many findings it produced) and where those findings landed.

- **Revision 1** — initial draft. Pinned the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)) over the card body's stale `docs/spec-021-nullable_overrides-0_0_8.md` reference; the single-spec-covers-all-three-slices scope ([Decision 2](#decision-2--one-spec-covers-all-three-slices)); the `extensions=` instance→factory-callable migration shape ([Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form), reshaped in Revision 2); the `inspect_django_type` command shape and argument-resolution contract ([Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution)); the two-key tuple-set override form over a dict-of-name shape ([Decision 5](#decision-5--two-key-tuple-set-override-form)); the net-new `ALLOWED_META_KEYS` landing (NOT a `DEFERRED_META_KEYS` promotion) ([Decision 6](#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion)); the tri-state `force_nullable` seam threaded through [`convert_scalar`][converters] ([Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)); the validation and collision behavior — `Meta.exclude` interaction, both-sets collision, consumer-authored interaction ([Decision 8](#decision-8--override-validation-and-collision-behavior)); the choice-field interaction ([Decision 9](#decision-9--choice-field-interaction)); the scalar-only scope with relation-field overrides rejected and deferred ([Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred)); the joint-`0.0.9`-cut version-bump boundary ([Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)); and the slice-independence / Slice-3 carve-off contingency ([Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency)). Conflicts called out in [Risks and open questions](#risks-and-open-questions): the card body's stale `spec-021-nullable_overrides-0_0_8` filename, its `## [0.0.8]` CHANGELOG-heading references, and its `examples/fakeshop/tests/test_commands.py` test path (no such file exists; the on-disk convention is one file per command).
- **Revision 2** — feedback pass over rev1. Four P1 (foundational) + four P2 + one P3 findings applied; the P1s reshaped Slices 1–3 materially. Nine findings recorded in ten bullets, landing under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) (1), [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) (4), [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) (1), [Decision 8](#decision-8--override-validation-and-collision-behavior) (1), and [Non-Decision deliberation](#non-decision-deliberation) (3) — the *inspect read source* P1 was reconciled with Decision 7 as part of the finding itself, so it is recorded under both Decisions. This is the only round whose bullet count exceeds its finding count.
- **Revision 3** — second feedback pass (review of rev2), verified against the **uv.lock-resolved Strawberry `0.316.0`** and source. The conclusions held; the *mechanism* under Decision 3 and three downstream claims were corrected. Eight findings, landing under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) (3), [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) (2), and [Non-Decision deliberation](#non-decision-deliberation) (3).
- **Revision 4** — third feedback pass (review of rev3). The rev3 verdict confirmed every rev2 fix correct; this pass fixes the one new correctness problem the singleton-factory pivot introduced, plus two stale cross-references. Three findings, landing under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) (2) and [Non-Decision deliberation](#non-decision-deliberation) (1).
- **Revision 5** — fourth feedback pass (review of rev4 against the released [`django_graphene_filters`][upstream-cookbook] parity baseline). The verdict confirmed the project is on track to rebuild the old package's feature set; this pass tightened five spots so later parity cards copy the correct pattern. Five findings, landing under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) (2), [Decision 5](#decision-5--two-key-tuple-set-override-form) (1), and [Non-Decision deliberation](#non-decision-deliberation) (2).
- **Revision 6** — fifth feedback pass (review of rev5, source-verified against the uv.lock-resolved Strawberry and the released [`django_graphene_filters`][upstream-cookbook] parity baseline). Verdict: core design sound; this pass corrected the executable details before implementation. Five findings, landing under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) (1), [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) (2), and [Non-Decision deliberation](#non-decision-deliberation) (2).
- **Revision 7** — TODO-scaffold verification pass (review of rev6); the maintainer scaffolded the card with `TODO(spec-029 …)` anchors at the real sites and the review verified the spec maps to them. Tightened staging discipline and a few executable details. Eight findings, landing under [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) (1), [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) (2), [Decision 8](#decision-8--override-validation-and-collision-behavior) (1), and [Non-Decision deliberation](#non-decision-deliberation) (4).

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-029-d1].

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-029-0.0.9`, so `<NNN>` is `029` and `<0_0_X>` is `0_0_9`.
- The card body's `docs/spec-021-nullable_overrides-0_0_8.md` reference is doubly stale: `021` is a different card's NNN ([`DONE-021-0.0.7`][kanban], the apps card) and `0_0_8` predates the card's `0.0.9` retag. Per [`docs/SPECS/NEXT.md`][next], a card-body reference that conflicts with the structured-filename convention is rewritten to the canonical name in the same archive sweep (see [Risks and open questions](#risks-and-open-questions)).
- The topic slug is `consumer_dx_cleanup` — it names the card's subject (the consumer-DX cleanup pass) rather than any single slice. The whole card is three slices; a slug naming only Slice 3 (`nullable_overrides`) would mis-scope the spec.

### Alternatives considered (and rejected)

- **Honor the card body verbatim with `docs/spec-021-nullable_overrides-0_0_8.md`.** Rejected: wrong NNN, wrong version, and an unnumbered-against-its-card spec that breaks the structured-filename convention.
- **Topic slug `nullable_overrides`** (matching Slice 3, the spec's design core). Rejected: the spec covers all three slices per [Decision 2](#decision-2--one-spec-covers-all-three-slices); naming the file after one slice would imply the other two are out of scope. If Slice 3 carves off into its own follow-up card per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency), THAT follow-up spec takes the `nullable_overrides` slug.

### Changes this Decision underwent

- **rev1** — introduced. Pinned the canonical filename against the [`KANBAN.md`][kanban] card body's `docs/spec-021-nullable_overrides-0_0_8.md` reference and chose the card-scoped `consumer_dx_cleanup` slug over the Slice-3-scoped `nullable_overrides` one.
- **rev1 through rev7** — no later revision touched it. The card-body filename conflict it settles is recorded under [Risks and open questions](#risks-and-open-questions).

## Decision 2 — One spec covers all three slices

Spec: [Decision 2 — One spec covers all three slices][spec-029-d2].

### Justification (moved from the spec)

- The three slices belong to one card with one Definition of done; splitting the spec would orphan Slices 1 + 2 from any design record.
- Slices 1 + 2 are low-design (a mechanical sweep and a strict introspection reader); their spec coverage is correspondingly light. The architectural depth concentrates on Slice 3, which carries the open design questions the card body raises (dict-of-name vs tuple-set, `Meta.exclude` interaction, both-sets collision, choice-field interaction, FK / reverse-FK interaction).
- The slices ship independently (per the card's Planning note), so each slice's section is self-contained — a reader implementing only Slice 2 reads [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution) and the Slice-2 checklist / DoD items without needing the Slice-3 design.

### Alternatives considered (and rejected)

- **A spec for Slice 3 only, with Slices 1 + 2 left specless per the card body.** Rejected: the [`docs/SPECS/NEXT.md`][next] flow targets the card, not a slice; and the KANBAN spec-map would then carry a card whose spec covers only a third of its scope.

### Changes this Decision underwent

- **rev1** — introduced, against the card body's split verdict (Slice 1 "No spec", Slice 2 "Light spec or none", Slice 3 "Requires spec").
- **rev1 through rev7** — no later revision touched it.

## Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form

Spec: [Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form][spec-029-d3].

### Justification (moved from the spec)

- Under 0.316.0 the singleton-factory is strictly better than the bare instance (identical caching / concurrency, no deprecation warning) and strictly better than the bare class / constructing-`lambda` (which get a cold cache every request). It is the one form that both modernizes off the deprecated instance AND preserves the optimization the card never intended to touch.
- No plan-cache relocation is needed — the singleton-factory shares one instance per process, exactly as the bare instance does.
- Pinning the mechanism to `0.316.0` (rather than spec-004's stale `_sync` / `_async` model) keeps the argument honest against the version the repo actually runs; the conclusion holds for any version with the `get_extensions` passthrough + instance-deprecation behavior.

### Alternatives considered (and rejected)

- **Keep the bare instance and document why (the rev2 decision).** Rejected: correct on caching, but it leaves a live `DeprecationWarning` ("will be removed") on every schema built the documented way — and a singleton-factory form exists that keeps the caching AND silences the warning, so keeping the deprecated form is no longer the honest move.
- **Migrate to the bare class or constructing `lambda: DjangoOptimizerExtension()`.** Rejected: a cold `self._plan_cache` every request, in both modes, under 0.316.0 — regresses the optimization.
- **Relocate the plan cache off the instance to enable the bare class.** Rejected as unnecessary: the singleton-factory preserves the instance-bound cache with no optimizer change. Cache relocation is a separate, larger optimizer concern ([Out of scope][spec-029-out-of-scope]) but is NOT a prerequisite for this migration.
- **Suppress the warning with `warnings.filterwarnings("ignore", …)` and keep the instance.** Rejected: hides a real upstream signal the project otherwise guards against (`tests/test_scalars.py` runs a subprocess under `-W error::DeprecationWarning`); the singleton-factory removes the warning at the source instead.

### Changes this Decision underwent

- **rev1** — introduced as the card's own framing: an instance -> class / `lambda`-factory migration.
- **rev2 P1, raised by source-reading rather than by the incoming feedback** — [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]'s [Plan cache][glossary-plan-cache] is instance-bound, so the card's migration as framed would regress the async cache. The Decision was rewritten to **keep** the instance form, document why, and defer the migration until the cache was relocated. Problem statement, Current state, Goals, Borrowing posture, User-facing API, Slice checklist, Implementation plan, Test plan, Edge cases, Definition of done, Risks, and Out of scope all moved with it.
- **rev3 P1.1 — stale extension-lifecycle model** — the `_sync_extensions` / `_async_extensions` split that [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004]'s 2026-04-30 spike described no longer exists in `0.316.0`; `Schema.get_extensions` runs `[ext if isinstance(ext, SchemaExtension) else ext()]` **per request** in both modes. The mechanism was re-derived against the uv.lock-resolved version and every claim pinned to it.
- **Claim this Decision may no longer make: that the bare class form is "harmless in sync".** `0.316.0`'s `Schema.get_extensions` re-instantiates a class entry per request in **both** modes, so the `examples/fakeshop/config/schema.py` and `TODAY.md` drift is a live cold-cache regression rather than a sync-only no-op. The spec states the regression directly and no longer names the claim it replaced; the retraction is here because a contract must not carry its own chronology.
- **rev3 P1.2** — rev2's "no `DeprecationWarning` to chase" was false. `0.316.0` warns at `Schema.__init__` for any instance entry, so the Slice 1 test plan and Definition-of-done item 4 gained a no-warning assertion.
- **rev3 P1.3** — the singleton-factory satisfies both constraints at once, so the Decision **flipped back** from rev2's "keep the instance form" to "migrate", and plan-cache relocation was demoted from prerequisite to an [Out of scope][spec-029-out-of-scope] note.
- **rev4 P1** — granularity corrected from per-file to **per construction site**. rev3's "one module-level `_optimizer` per file" would have polluted [`tests/optimizer/test_extension.py`][test-extension]'s per-test `cache_info()` counters (order-dependent failures) and could not carry per-site `strictness=` ([`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] mixes `strictness="raise"` and the default in one module). The migration target widened to the **named** `extensions=[ext]` form, which also trips the deprecation warning.
- **rev4 P2** — the [Out of scope][spec-029-out-of-scope] `DjangoConnectionField` bullet still said "present the instance form too"; rewritten to the singleton-factory.
- **rev5 P1** — the top Status paragraph still carried rev2's "keep[s] the `extensions=` instance form ... migration deferred", the opposite of the rev3/rev4 design.
- **rev5 P2** — [`GOAL.md`][goal]'s astronomy schema passed **no** `extensions=` at all, so the north-star recipe silently omitted the optimizer. It joined the Slice 1 sweep.
- **rev6 P2** — the stale "~24" migration estimate was replaced by an `rg 'extensions=\['` audit finding 48 schema-construction entries across the five package test files, including two `_CaptureExt(DjangoOptimizerExtension)` subclass instances that a `DjangoOptimizerExtension()`-literal grep misses.
- **rev7 P2** — a post-migration grep for the exact forbidden forms was added on top of the broad audit, because the broad audit finds construction *sites* while the forbidden-form grep catches the specific regressions the slice removes.
- **Post-ship: the one-shot grep rotted, exactly as an ungated rule does.** rev7's post-migration grep was a build-time action with nothing standing behind it. Four later cards reintroduced both cold-cache forms across five patch releases and nothing noticed, until the `029` residual cycle re-derived the population at **25 forbidden entries in 8 files** against **81** already-correct singleton-factory entries at HEAD. The Decision's mechanism was re-verified against the then-current strawberry-graphql before the repair and held unchanged, so the repair was a repair and not a relaxation. The spec now states the gate as a standing test, [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance], and states the rule by **form** rather than by a spelling list.
- **Claim this Decision may no longer make: that a grep over a list of five literal spellings is the gate.** It is not, in two directions. Enumerating spellings under-reports: the dispatcher's sweep for `lambda: DjangoOptimizerExtension()` missed all 13 keyword-carrying variants (`strictness=`, `nested_connection_strategy=`) — the same form, a different spelling. And three of the five listed spellings are the *instance* forms, which the standing pin deliberately does not match, because Strawberry's instance-form `DeprecationWarning` meets `pytest.ini`'s `filterwarnings = error` and fails the suite on its own. The enforced contract is two forms — bare class, any constructing lambda — over a defined corpus.
- **Post-ship: the granularity example and the census figures.** The `~41`-entries figure and the `~48 across five package test files` total were measured at authoring and are long stale; the spec no longer stores either, because a count of schema-construction sites in a growing test file is stale the first time that file grows a schema, and the audit's own `rg` result is the population. The cross-module `strictness` example (one module mixing `strictness="raise"` with the default) was replaced by a strictly better one that the repair pass surfaced: [`tests/optimizer/test_extension.py::test_strictness_flags_a_relation_under_an_unplannable_root`][test-extension] builds two schemas from two differently-configured instances **inside one function**, so it rules out per-function granularity as well as per-file.

## Decision 4 — `inspect_django_type` command shape and argument resolution

Spec: [Decision 4 — `inspect_django_type` command shape and argument resolution][spec-029-d4].

### Justification (moved from the spec)

- Reusing the [`export_schema.py`][export-schema-cmd] `Command` shape means a maintainer sees one shape across both commands; the `CommandError` discipline (wrap import / type / value failures) is already established.
- Reading `__django_strawberry_definition__` / [`FieldMeta`][field-meta] makes the command a strict consumer of the existing introspection surface — no new public API, no foundation change.
- The two-step argument resolution is the minimal reconciliation of the card body's conflicting positional-name-vs-test-example signals; it adds no surface a consumer must learn (a name or a path both work).

### Alternatives considered (and rejected)

- **Dotted-path-only resolution (honor the `add_arguments` note literally).** Rejected: the card's worked test passes a bare `"BookType"`, which a dotted-path-only command would reject; the dot-dispatch (dotted → `import_string`, bare → registry) honors both signals.
- **Registry-name-only resolution (honor the test example literally).** Rejected: a dotted path is the unambiguous form when two apps register a `BookType`; dropping it would force disambiguation the consumer cannot express.
- **Resolve a bare name to the first registry match.** Rejected: import-order-dependent output; the unique-`__name__` contract above raises on ambiguity instead.
- **Build the table from the constructed `strawberry.Schema` introspection instead of `origin.__annotations__` + `DjangoTypeDefinition`.** Rejected: the card's stated value is moving the diagnostic to the *type-definition* layer; reading the finalized type's annotations + definition keeps the command usable even when full schema construction fails, and `origin.__annotations__` is already the authoritative resolved-annotation record (no second source needed).

### Changes this Decision underwent

- **rev1** — introduced.
- **rev2 P1, inspect read source** — the command reads the resolved annotation from `origin.__annotations__` (authoritative: it reflects overrides, consumer authorship, and resolved relations) and uses `selected_fields` / `field_map` only for Django-side metadata and converter classification. Re-running `convert_scalar` for nullability was explicitly rejected, and the Decision reconciled with [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) and the [Non-goals][spec-029-non-goals].
- **rev2 P1, finalized-state semantics** — `__django_strawberry_definition__` is assigned at registration, *before* finalize; finalization is the `DjangoTypeDefinition.finalized` flag. The Decision gained two distinct error branches (`definition is None` vs `not definition.finalized`).
- **rev2 P2** — dotted-path resolution pinned to Django's `import_string`, not Strawberry's `import_module_symbol` (which uses the `module:symbol` selector form).
- **rev2 P2** — a first-class `CommandError` on a non-unique bare `__name__`, resolved through `registry.iter_types()`, with package-internal coverage.
- **rev3 P2.1** — the `origin.__annotations__` read would `KeyError` on a Relay-suppressed pk; the interface-sourced `GlobalID!` special case and a `test_inspect_relay_node_pk_row` test were added.
- **rev3 P2.3** — as specified the command never finalized the registry. `--schema <dotted_path>` was added (mirroring [`export_schema.py`][export-schema-cmd]) together with `test_inspect_with_schema_option`, and the unfinalized `CommandError` was made to name `--schema`.
- **rev6 P1** — the `--schema` loader corrected to `import_module_symbol(..., default_symbol_name="schema")`. `import_string("config.schema")` reads a `schema` *attribute* off the empty `config` package and fails. `import_string` was kept for the dotted *type* argument only, dispatched on the dot, so a dotted import failure raises with the original error rather than being masked by a registry fallback. A follow-up note in the same pass propagated the dot-dispatch wording out of the Decision: the Slice 2 checklist, the Risks item, and Definition-of-done item 5 still carried the old "dotted path first, then falls back to a registry lookup" shorthand, and all three were rewritten so an implementer could not reintroduce the catch-all-fallback bug.
- **rev6 P1** — bare-name `call_command` tests only work after `config.schema` is imported and finalized, so they were placed under a registry-clear + reload fixture, with a separate cold-path `--schema` test; bare-name resolution was documented as a post-schema-import convenience rather than a cold-CLI path.
- **rev7 P1** — the cold-path `--schema` test is **not** cold in-process: `import_module_symbol` returns the cached module without re-running registration or `finalize_django_types()`, so an in-process `registry.clear()` is not a cold start. The test plan now requires a subprocess or `sys.modules` eviction, and the Decision notes the import-time-side-effect dependency.
- **rev7 P2** — the suppressed-pk exception was propagated to the Slice 2 checklist's "Ship the command" item and the implementation-plan row, not left only in this Decision and the test plan.
- **Post-ship: the loaders moved behind a shared helper.** This Decision pinned `import_string` for the dotted type argument and Strawberry's `import_module_symbol` for `--schema`, and it named them directly because at the time each command called its own importer inline. A later consolidation extracted both into [`django_strawberry_framework/management/commands/_imports.py`][commands-imports], shared with [`export_schema.py`][export-schema-cmd] and now documented as that command's own Decision 3 ([`spec-022-export_schema-0_0_7.md`][spec-022]); a subsequent fix added `::_validate_absolute_module_path`, a pre-import rejection of an empty or relative module path that **neither loader had at ship**. The dispatch-by-shape contract this Decision actually settled — dotted goes to `import_string`, bare goes to the registry, the dotted failure is never masked by a registry retry — is intact; only the call path changed, plus one new rejection.
- **Post-ship: the shipped surface is materially larger than this Decision describes, and two of the additions change what it says rather than adding to it.** Re-derived from the two test modules, the growth is: bare-name resolution matching the authoritative **SDL** name (schema `NameConverter` applied, honoring `Meta.name`) as well as the Python `__name__`, with a collision *across* those surfaces ambiguous rather than first-match, and the table titled with the SDL name; `--schema`'s imported object read for the schema's **scalar map and name converter**, not only for its registration side effect; the **file/image output converter** named as the row that fired instead of a mis-attributed `SCALAR_MAP` entry, and the `SCALAR_MAP` row named by its **matched MRO ancestor**; custom-scalar and named-union scalar naming with a `__name__` fallback; multi-member union rendering; the **connection-only relation shape**, whose list annotation the Phase-2.5 synthesizer pops, rendered from the synthesized `<rel>_connection` sibling; direct `class Foo(DjangoType, relay.Node)` inheritance recognized by the same `_is_relay_shaped` predicate synthesis uses; and malformed-path rejection from the shared loaders.
- **Claim this Decision may no longer make: that `origin.__annotations__` is the single source of truth for every field's resolved type.** It is authoritative for auto-synthesized fields and reflects the Slice 3 overrides, which is the part this Decision got right and the part [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar) depends on. It is **not** authoritative for a consumer-authored field — its entry there is a `StrawberryAnnotation` object for a `strawberry.field` assignment and an unresolved forward-ref string for an annotated relation — so those rows read the finalized `origin.__strawberry_definition__` instead, and a forward reference finalization could not resolve raises `CommandError` on Strawberry's `UNRESOLVED` sentinel rather than printing a bogus type. Nor is it authoritative for a connection-only relation, whose annotation has been deleted. The underlying principle survives intact and is what the spec now states: read the authoritative post-finalize record for that field's origin, never re-derive by re-running the converter.
- **Post-ship: the worked example's host type became Relay-shaped.** This Decision's illustrative output and its accompanying paragraph rested on `BookType` declaring no `Meta.interfaces`, so its pk rendered as a plain `Int!` and the Relay contrast had to be drawn against `GenreType`. `DONE-032-0.0.9` ([`spec-032-full_relay-0_0_9.md`][spec-032]) gave `BookType` `interfaces = (relay.Node,)`, so its pk is now suppressed and its row reads `GlobalID!` / "relay.Node id" — the spec's illustrative table and the live assertion over it both say so, and the non-Relay contrast is now drawn against `ShelfType`. The suppressed-pk contract itself is unchanged; only which fakeshop type demonstrates each side of it.

## Decision 5 — Two-key tuple-set override form

Spec: [Decision 5 — Two-key tuple-set override form][spec-029-d5].

### Justification (moved from the spec)

- The two-key tuple-set form mirrors [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] (both tuple-of-names, both expressing a per-field set membership), so it reads as native to the package's `Meta`-shaped API.
- A dict-of-name-to-bool duplicates the direction the two-key split already encodes and invites the ambiguous `{"field": False}` shape: does `False` mean "force required" or "no override"? The two-key form has no such ambiguity — membership in `nullable_overrides` means "force nullable," membership in `required_overrides` means "force required," absence from both means "honor the column."
- The two directions are genuinely distinct operations (widen `T` → `T | None` vs narrow `T | None` → `T`), so a per-direction set names each operation explicitly.

### Alternatives considered (and rejected)

- **A single `Meta.nullability = {"field": bool}` dict.** Rejected for the `{"field": False}` ambiguity above; could be added later as sugar normalized internally to the two sets if consumers ask, but the two-key form is the primary shape.
- **A single `Meta.nullable_overrides = {"field": bool}` dict (one key, dict value).** Rejected: same ambiguity, and it diverges from the tuple-of-names shape of every other field-selection `Meta` key.

### Changes this Decision underwent

- **rev1** — introduced.
- **rev5 P2** — two sites (Problem statement, Borrowing posture) still called the override surface a `Meta`-key **dict**; both were corrected to "two `Meta` tuple-set keys", the shape this Decision had already fixed.

## Decision 6 — Net-new `ALLOWED_META_KEYS` entries, not a `DEFERRED_META_KEYS` promotion

Spec: [Decision 6 — Net-new `ALLOWED_META_KEYS` entries, not a `DEFERRED_META_KEYS` promotion][spec-029-d6].

### Justification (moved from the spec)

- The deferred-key promotion gate (per [Cross-subsystem invariants][glossary-cross-subsystem-invariants]) exists because [`Meta.orderset_class`][glossary-metaorderset_class] / [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.aggregate_class`][glossary-metaaggregate_class] / [`Meta.fields_class`][glossary-metafields_class] / [`Meta.search_fields`][glossary-metasearch_fields] were **named in the `Meta` surface before their subsystems shipped** — the deferred set holds keys that are reserved-but-not-yet-functional, and the gate promotes one only when its subsystem applies it end-to-end.
- `nullable_overrides` / `required_overrides` were never reserved; they are net-new keys whose feature ships in the same card that adds them. There is no "declared against an earlier version raised `ConfigurationError`" history to honor. So they go straight into `ALLOWED_META_KEYS`; the deferred-set machinery is not involved.
- This is a real difference from the orders / filters precedent worth pinning so a future maintainer does not look for a promotion gate that was never needed.

### Alternatives considered (and rejected)

- **Add them to `DEFERRED_META_KEYS` first, then promote in the same commit.** Rejected: pointless churn — the deferred set models "reserved but not functional," which is never true for these keys.

### Changes this Decision underwent

- **rev1** — introduced.
- **rev1 through rev7** — no later revision touched it.

## Decision 7 — Tri-state `force_nullable` threaded through `convert_scalar`

Spec: [Decision 7 — Tri-state `force_nullable` threaded through `convert_scalar`][spec-029-d7].

### Justification (moved from the spec)

- The card explicitly says the implementation touches both [`types/base.py`][base] AND [`types/converters.py`][converters]'s scalar-resolution path. The tri-state threaded through `convert_scalar` is the cleanest expression of that: the converter stays the single source of truth for "what annotation does this column produce," and the override is one extra input to it.
- Rewriting the returned annotation at the call site would require unwrapping an arbitrary `T | None` Union to strip nullability (`required_overrides` on a nullable column), which is fragile — it must detect the Union, find `NoneType`, and rebuild the non-None member, with special cases for `list[T] | None` and `EnumType | None`. The tri-state computes the widening *before* it happens, so there is nothing to unwrap.
- The override applies uniformly to every branch because the widening decision is computed from one `effective_null` value — choice enums, arrays, hstore, and plain scalars all honor it without per-branch override logic ([Decision 9](#decision-9--choice-field-interaction) confirms the choice case).

### Alternatives considered (and rejected)

- **Rewrite the annotation at the `_build_annotations` call site (`ann | None` to widen; unwrap-Optional to narrow).** Rejected: the narrow direction (`required_overrides`) requires robustly unwrapping `T | None`, `list[T] | None`, and `EnumType | None` — fragile and duplicates knowledge `convert_scalar` already has.
- **A separate `convert_scalar_with_override(...)` wrapper.** Rejected: a second entry point that must stay in sync with `convert_scalar`'s branch logic; the keyword-only parameter keeps one function authoritative.

### Changes this Decision underwent

- **rev1** — introduced.
- **rev2 P1** — reconciled with [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): because the override is baked into the synthesized annotation at construction time, `origin.__annotations__` is the authoritative post-override record, which is why the inspect command reads it instead of re-deriving nullability.
- **Post-ship: the apply call site is no longer `convert_scalar` (`DONE-037-0.0.11`).** At ship, `_build_annotations`'s non-relation branch called `convert_scalar(field, cls.__name__, force_nullable=...)` directly. `DONE-037-0.0.11` ([`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037]) inserted a read-output entry point, `types/converters.py::convert_field_output`, between them: it routes a `FileField` / `ImageField` through `FIELD_OUTPUT_TYPE_MAP` to the structured output object and delegates every other column to `convert_scalar` unchanged. The file/image lookup is deliberately kept **off** `convert_scalar` / `scalar_for_field` / `SCALAR_MAP` so an output object can never reach the shared filter-input path.
- **Why that left this Decision's argument standing.** The tri-state was carried onto the new entry point rather than reimplemented beside it, and it is threaded through to `convert_scalar` unchanged, so the seam is still one parameter on one converter and there is still nothing to unwrap at the call site. Both rejected alternatives lose for the same reasons they lost originally, and the file branch makes the second one worse: rewriting the returned annotation at the call site would now have to unwrap a `DjangoFileType | None` output object as well as `T | None`, `list[T] | None`, and `EnumType | None`.
- **Claim this Decision may no longer make: that `_build_annotations` passes `force_nullable` to `convert_scalar`.** It passes it to `convert_field_output`, which applies it to a file/image output object's default-nullable annotation or hands it to `convert_scalar` for every other column. The spec states the shipped call chain; the `convert_scalar`-direct spelling and the three broken `#"substring"` citations that quoted it were retired with it.

## Decision 8 — Override validation and collision behavior

Spec: [Decision 8 — Override validation and collision behavior][spec-029-d8].

### Justification (moved from the spec)

- Fail-loud at type-creation time is the package's established posture ([`ConfigurationError`][glossary-configurationerror] for unknown `Meta` keys, invalid hints, mis-typed override targets). A silently-ignored override is the worst failure mode — the consumer believes nullability flipped and it did not.
- Validating against `selected_names` (not just model existence) catches the [`Meta.exclude`][glossary-metaexclude] interaction the card raises as an open question: an excluded field cannot be overridden because it is not in the type.
- Rejecting consumer-authored fields resolves the interaction with [Scalar field override semantics][glossary-scalar-field-override-semantics]: the two mechanisms both control nullability, and the consumer must pick one. The annotation override is strictly more powerful (it controls the whole annotation, not just nullability), so the validator points the consumer there.

### Alternatives considered (and rejected)

- **Silently no-op an override on an excluded / consumer-authored field.** Rejected: silent no-op hides a real configuration mistake; the package fails loud everywhere else.
- **Let the consumer-authored annotation win and skip the override silently.** Rejected: same silent-no-op objection; the consumer cannot tell which mechanism took effect.
- **Allow a field in both sets, with one direction winning.** Rejected: there is no non-arbitrary winner for a contradictory declaration; raising is the honest response.

### Changes this Decision underwent

- **rev1** — introduced as a single `_validate_nullability_overrides(meta, selected_names, consumer_authored_fields, model)` helper called from [`_validate_meta`][base].
- **rev2 P1, Slice 3 validation flow** — that signature is **not implementable**: `_validate_meta` runs before `_select_fields`, before `consumer_authored_fields` is computed, and before Relay-pk suppression is known, so neither `selected_names` nor `consumer_authored_fields` exists at that point. The Decision was split into the three stages it now carries (shape / normalize / collision -> target-validate -> apply).
- **rev7 P2** — the *unknown* and *excluded* paths were split into two separately derived name sets (`model._meta.get_fields()` names versus the post-[`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] selected set) so the `Meta.exclude` contract is not collapsed into "unknown".
- **Post-ship: the helper's shipped name, and the planned name that never existed.** The stage-2 helper shipped as `types/base.py::_validate_nullability_override_targets` — the name rev2's three-stage split implied and the name Decision 8 and Definition-of-done item 11 already used. The rev1 name `_validate_nullability_overrides` survived in one `## Current state` bullet, which went on calling it "Slice 3's new helper" while this Decision said the shape it names is not implementable. No helper of that name is in the package; the spec no longer predicts one.
- **Post-ship: its signature, and why `relay_shaped` rather than a pk name.** The shipped parameters are keyword-only — `model`, `selected_fields`, `consumer_authored_fields`, `relay_shaped`, `nullable_overrides`, `required_overrides`. Passing `relay_shaped: bool` rather than a pre-computed `relay_pk_name` lets the helper derive `model._meta.pk.name` itself, and only when the type is Relay-shaped, so no caller can hand it a pk name computed under a different Relay predicate than the one synthesis used.
- **Post-ship: the unknown/excluded half became shared, which retired this Decision's structural-template framing.** rev1 modelled the validator on `_validate_filterset_class`. That template describes the *shape check*, not the target check, and it stopped describing even the neighbourhood once a second `Meta` key needed the same unknown/excluded derivation: `Meta.relation_shapes` (`DONE-032-0.0.9`, [`spec-032-full_relay-0_0_9.md`][spec-032]) arrived two days before the common half was extracted into `types/base.py::_selected_meta_targets`, routing the unknown path through the shared `_format_unknown_fields_error` so its consumer-visible shape matches the `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` typo guards. `Meta.filesystem_path_fields` (`DONE-048-0.0.14`, [`spec-048-secure_output_defaults-0_0_14.md`][spec-048]) became the third caller. What stays per-key is exactly the per-name remainder — rules 3-5.
- **Claim this Decision may no longer make: that the rejection order is unknown, excluded, consumer-authored, relation, Relay-pk.** The shipped order checks the Relay-suppressed pk **before** the relation rule, so a name that is both — a relation pk such as `OneToOneField(primary_key=True)` on a Relay type — is reported with the Relay reason. The spec lists the shipped order, and so do the two source sites that state it: `types/base.py::_validate_nullability_override_targets`'s docstring, which also carries the reason Relay-pk precedes relation, and `types/base.py::_validate_meta`'s target-check comment.

## Decision 9 — Choice-field interaction

Spec: [Decision 9 — Choice-field interaction][spec-029-d9].

### Justification (moved from the spec)

- [Decision 7](#decision-7--tri-state-force_nullable-threaded-through-convert_scalar)'s single `effective_null` computation sits at the post-choice-substitution widening point, so the choice case is covered for free.
- This resolves the card's "choice-field interaction" open question: the override flips the enum's nullability, not its members; the stored-DB-value member naming ([Choice enum generation][glossary-choice-enum-generation]) is untouched.

### Alternatives considered (and rejected)

- **Reject overrides on choice fields.** Rejected: there is no reason a choice field's GraphQL nullability should be less overridable than a plain scalar's; the widening point already handles it uniformly.

### Changes this Decision underwent

- **rev1** — introduced.
- **rev1 through rev7** — no later revision touched it.

## Decision 10 — Non-relation scope; relation-field overrides rejected and deferred

Spec: [Decision 10 — Non-relation scope; relation-field overrides rejected and deferred][spec-029-d10].

### Justification (moved from the spec)

- The scalar-resolution path ([`convert_scalar`][converters]) is the only path Slice 3 threads `force_nullable` through; relation fields take the `field.is_relation` branch in [`_build_annotations`][base] → `PendingRelation` / `resolved_relation_annotation`, an entirely separate annotation path the override does not touch.
- Relation nullability override is a genuinely harder design: a forward single-valued relation (`TargetType | None` ↔ `TargetType`) would thread an override into `resolved_relation_annotation`, but a many-side relation ([Relation handling][glossary-relation-handling] reverse-FK / M2M) renders as `list[TargetType]` (`[T!]!`) where "make it nullable" is ambiguous — does it mean the list is nullable (`[T!]`) or the element (`[T]!`)? Resolving that ambiguity is its own card.
- Scoping to scalars keeps Slice 3 bounded and ships the common case (a `NOT NULL` text column the consumer wants optional in GraphQL) without inventing the many-side list-vs-element semantics.

### Alternatives considered (and rejected)

- **Include forward single-valued FK / OneToOne overrides in `0.0.9`** (thread `force_nullable` into `resolved_relation_annotation`, reject only many-side overrides). Viable; rejected for `0.0.9` to keep the slice bounded and the validation rule simple ("relation = rejected"). This is the natural first extension if relation override demand surfaces — see the fallback in [Risks and open questions](#risks-and-open-questions).
- **Silently ignore relation override-targets.** Rejected: silent no-op (see [Decision 8](#decision-8--override-validation-and-collision-behavior)).

### Changes this Decision underwent

- **rev1** — introduced.
- **rev1 through rev7** — no later revision touched it.
- **Post-ship widening (`DONE-037-0.0.11`).** The scope this Decision fixed for the shipping cut was *scalar columns only*, and at `0.0.9` that was an accurate word rather than a narrow one: `_build_annotations` called `convert_scalar` directly for every non-relation column, so "non-relation" and "scalar" named the same set. `DONE-037-0.0.11` ([`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037]) split them. It routed the read side through `types/converters.py::convert_field_output`, which sends a `FileField` / `ImageField` to the structured `DjangoFileType` / `DjangoImageType` output object and delegates every other column to `convert_scalar`, and it threaded `force_nullable` through both. From that release a non-relation column can resolve to something that is not a scalar, and the override reaches it: because that output object is nullable by **default** — the generated parent resolver returns `None` for an empty `FieldFile`, reachable even on a `null=False, blank=False` column — `required_overrides` on a file column is the documented opt-in to `DjangoFileType!`, a capability [`docs/README.md`][docs-readme] and the [`Meta.required_overrides`][glossary-metarequired_overrides] glossary entry both already describe.
- **What did not move: the boundary.** The override still reaches exactly one annotation path, and a relation field still takes `field.is_relation` to `PendingRelation` / `resolved_relation_annotation`, which the override does not touch. A relation override-target is still rejected at type-creation time, and the many-side list-vs-element ambiguity is still the reason the deferral stands. Both rejected alternatives below are therefore untouched by the widening — including the forward-single-valued-FK extension, which remains the natural first step if relation-override demand surfaces.
- **Claim this Decision may no longer make: that the overrides are scalar-only.** They apply to non-relation model fields — scalar columns and file/image output objects alike — and the discriminator is the annotation path, not the column's storage class. The spec states that scope directly, under a heading renamed from "Scalar-only scope" to "Non-relation scope" (this file's heading follows it, as the two are kept character-identical so their anchors match in both directions), and it names neither the widening nor the card that caused it: a contract must not carry its own chronology, so the pointer is here.

## Decision 11 — Version bumps are owned by the joint `0.0.9` cut

Spec: [Decision 11 — Version bumps are owned by the joint `0.0.9` cut][spec-029-d11].

### Justification (moved from the spec)

- A feature card mutating shared release state would race the three sibling cards for "who owns the `0.0.9` bump"; centralizing the bump in the joint cut removes the race.
- Keeping version edits command-gated prevents an implementer from touching `pyproject.toml` / `__version__` / the pinned version test while implementing a DX slice.

### Alternatives considered (and rejected)

- **Bump to `0.0.9` in this card (it is the lowest-NNN `0.0.9` card).** Rejected: lowest-NNN is not "owns the release"; whichever card lands last, or an explicit maintainer cut, owns the bump. Encoding "lowest NNN bumps" is an implicit-bump rule the package's [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] Decision 10 already rejected.
- **Append CHANGELOG bullets under `## [0.0.8]` per the card body.** Rejected: `0.0.8` is shipped; appending to a shipped heading would mis-attribute `0.0.9` work.

### Changes this Decision underwent

- **rev1** — introduced.
- **rev1 through rev7** — no later revision touched it.

## Decision 12 — Slice independence and the Slice-3 carve-off contingency

Spec: [Decision 12 — Slice independence and the Slice-3 carve-off contingency][spec-029-d12].

### Justification (moved from the spec)

- The card body states the slices "ship in any order" and that Slice 3 "carves off as its own follow-up card" if deferred; this Decision records that as the operating contract.
- Independence means each slice's PR is reviewable in isolation; a reviewer of the Slice 2 command does not need the Slice 3 override design loaded.

### Alternatives considered (and rejected)

- **Enforce a strict slice order (1 → 2 → 3).** Rejected: there is no dependency to enforce; an artificial order would block Slice 2 behind Slice 1 for no reason.

### Changes this Decision underwent

- **rev1** — introduced.
- **rev1 through rev7** — no later revision touched it.

## Non-Decision deliberation

Findings that changed the spec without belonging to any one Decision. They left the spec with the revision history above; grouped here by what they were about.

### The Slice 3 acceptance surface

- **rev2 P2, live-HTTP host** — a dedicated acceptance-only secondary [`DjangoType`][glossary-djangotype] on `library.Book` (`Meta.primary = False`, with `BookType` marked primary) was pinned instead of mutating the `scalars` app's baseline assertions. The [`Meta.primary`][glossary-metaprimary] interaction became part of the plan rather than an accident of it.
- **rev6 P2, `required_overrides` data safety** — fakeshop seeds `Book(subtitle=None)`, so an SDL-only test could pass while a `subtitle` query violated the declared `String!` contract. The acceptance resolver became `Book.objects.exclude(subtitle__isnull=True)`, a live data-query test asserting no `errors` was added, and a new Edge case recorded that `required_overrides` changes the GraphQL contract, not the column or the runtime values.
- **rev7 P2, acceptance resolver ordering** — `.order_by("id")` was appended across the Slice 3 checklist, the test plan, and Definition-of-done item 13, so the data-query assertion cannot go flaky on response order.
- **rev3 P2.4, schema-wide assertions** — before declaring the suite undisturbed, a `grep` confirmed `examples/fakeshop/test_query/` carries no full-SDL snapshot and no registered-type count, so a new reachable type and root field disturb nothing. The verification step stayed in the spec's test plan; only its provenance left.

### The illustrative `inspect_django_type` output

- **rev2 P3** — the worked example and happy-path test moved off the non-existent `PatronType.membership_status` onto real `BookType` fields (`title` / `subtitle` / `circulation_status` / `shelf` / `genres` / `loans`).
- **rev3 P2.2** — `BookType` is **not** Relay-shaped, so the illustrative `id -> GlobalID!` row was wrong. It became `id -> Int!`, a `GenreType` Relay-pk note was added, and the non-Relay-pk assertion was pinned in `test_inspect_by_registered_name`.
- **Claim this section may no longer make: that `BookType` is not Relay-shaped.** `DONE-032-0.0.9` gave it `interfaces = (relay.Node,)` after ship, reversing rev3 P2.2's premise — the pk row reads `GlobalID!` again and the non-Relay contrast is drawn against `ShelfType`. The rev3 record above stands as the chronology it is; the current output is recorded under [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution), "Post-ship: the worked example's host type became Relay-shaped".

### Staging discipline for the scaffolded card

The maintainer scaffolded this card with `TODO(spec-029 ...)` anchors at the real sites, and rev7 verified the spec mapped to them. Four rules came out of that pass; all four stayed in the spec's [Implementation scaffolding & staging notes][spec-029-scaffolding], because each one changes how a slice is built rather than why.

- **rev7 P1** — Django command discovery imports every module under `management/commands/` and expects a `Command` class, so a comment-only `inspect_django_type.py` `AttributeError`s at discovery. Either the file does not exist until the body is written, or it lands as a minimal fail-loud shell.
- **rev7 P2** — command discovery and `manage.py help` working is **not** Slice 2 completion; `handle()` must resolve, read a finalized definition, and print.
- **rev7 P3** — `docs/TREE.md` describes shipped reality rather than a scaffold; a `CHANGELOG.md` `TODO` anchor is not a release note; and Python `TODO` pseudocode must dodge Ruff's `ERA001`.
- **rev6 P3** — the Current-state section's raw `(line N)` source references were replaced with counts plus substring / symbol references, per the standing-doc reference convention.

### Documentation-coherence passes

- **rev5 P2, parity checkpoint** — the `### Reference-package parity checkpoint` table was added to the Borrowing posture so the "on track to rebuild the old package's feature set" claim is auditable from inside the spec. The table stayed; this is the record that it was a review response rather than an original section.
- **rev5 P3, title** — `Meta.required_overrides` was added to the title parenthetical (it was under-named) and the Slice-1 topic became "`extensions=` singleton-factory".
- **rev4 P3, polish** — the Slice 1 User-facing-API heading was retitled "(the singleton-factory form)", the Non-goals lead-in corrected from "only documents" to "migrates (form only)", [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] added to the migration list, and `warnings.simplefilter("always")` noted for the no-warning assertion.
- **rev3 P3.1, wording** — "NEXT.md forbids creating glossary entries" was softened to "[NEXT.md][next] Step 7 *defers* glossary anchoring", which is what that step actually says.
- **rev2 P2, CSV honesty** — [Definition-of-done][spec-029-dod] item 1 was made to state that the companion CSV is intentionally incomplete on the three net-new symbols until their glossary headings land. That deferral was discharged after ship, so the item is one of the things Slice 3 reconciles.
- **Post-ship: that deferral is discharged, and the item said otherwise for years.** All three symbols carry a [`docs/GLOSSARY.md`][glossary] heading and a row in [`spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms], and [`scripts/check_spec_glossary.py`][check-spec-glossary] reports `OK: 44 terms`, so item 1's "intentionally NOT in the CSV ... honestly incomplete" claim was false at HEAD. Its `(per Risks and open questions)` pointer had also stopped leading anywhere useful: the section it names now carries only the derivation-baseline rule, the rest of its body having moved into this file. Both were fixed in one edit rather than repointing a sentence about to be rewritten. What the item states now is the *rule* the original deferral was an instance of — a term whose glossary heading does not exist yet cannot be in the CSV without failing the checker, so heading and row land together — which is why nothing is lost by dropping the snapshot.
- **Post-ship: which stale figures were kept and which were removed.** `## Current state` is framed by the spec's own header as "the repo as of this spec's authoring, before the build", so its `48 actual schema-construction entries across the five package test files` census stands as the historical measurement it is; removing it would not make the section more accurate, only less specific about what was audited. The identical figures in *completion* claims did not get that licence — a Slice-checklist box and a Definition-of-done item assert a finished state, so a stale number there is a false completion claim rather than a dated observation. Those were replaced by the audit that produces the population (`rg 'extensions=\['` over the named files) instead of a stored count. The same reasoning removed Decision 3's `~41`.
- **The rule that governs both dispositions, stated once so the next sweep can apply it rather than re-derive it.** `## Current state`'s vintage framing licenses dated **observations** of the pre-build repo; it does not license **predictions** about what the build would do. A falsified observation stays (it was true when written and the header dates it); a falsified prediction is rewritten, because nothing in this spec dates a claim about the build's outcome. That is one rule with two outcomes: the census above is an observation and stands, while the same bullet-set's forward-looking clauses are predictions and were rewritten wherever the build falsified one — the `_validate_nullability_overrides` helper name and the per-key-`_validate_*`-helper shape. Every other forward-looking clause in the section is a prediction the build **fulfilled** (no `nullable_overrides` slot on `DjangoTypeDefinition`; `import_string` for dotted paths; the three glossary entries authored during implementation; [`GOAL.md`][goal] gaining the `extensions=` recipe; the dedicated acceptance-only secondary type with `Meta.primary = False`), so none was owed an edit and the rule opens no further population.

## Risks and open questions

The spec's `## Risks and open questions` body, verbatim, its own preamble included. The preferred-answer / fallback shape that preamble describes is what makes the section a build-time instrument rather than a contract, which is why the whole body moved. Three of the ten items are the [`KANBAN.md`][kanban] card-body conflicts the Decisions reconcile, and the spec's Slice checklist, [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution), [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut), and Definition-of-done item 1 all point here for that record.

**One rule inside these items stayed in the spec.** The derivation-baseline pin under "The Strawberry extension lifecycle is version-dependent" is a live maintenance trigger, not a build-time question: a supported Strawberry version that stops calling the `extensions=` factory per request requires [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form) to be re-derived by executing against that version. The spec restates that rule under the surviving heading; the preferred-answer / fallback framing around it is below.

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **GLOSSARY has no entry yet for the three new symbols.** `Meta.nullable_overrides`, `Meta.required_overrides`, and the `inspect_django_type` command have no [`docs/GLOSSARY.md`][glossary] heading at spec-authoring time ([`docs/SPECS/NEXT.md`][next] Step 7 *defers* glossary anchoring to the companion CSV until the heading ships — it does not forbid authoring an entry; the entries simply land with the implementation, not the spec). Preferred answer: the three entries are authored during implementation (Slice 2 and Slice 3's doc-update steps) and are therefore **omitted from the companion [`spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms]** so [`scripts/check_spec_glossary.py`][check-spec-glossary] stays green (the checker requires every CSV term to resolve to a real glossary heading). Fallback: if the maintainer wants the glossary entries to exist before implementation, a separate doc-only change adds the three `planned for 0.0.9` headings, after which the CSV can carry the three rows and the checker still passes.
- **Card body names a stale spec filename.** The card's Slice 3 "Requires spec" line names `docs/spec-021-nullable_overrides-0_0_8.md` (wrong NNN, wrong version). Preferred answer per [Decision 1](#decision-1--spec-filename-and-canonical-naming): this spec is `docs/spec-029-consumer_dx_cleanup-0_0_9.md`; the card-body reference is rewritten to the canonical name in the [`docs/SPECS/NEXT.md`][next] Step-8 archive sweep / card-completion wrap. Fallback: none — the structured-filename convention is unambiguous.
- **Card body names a stale CHANGELOG heading.** The card's per-slice Definition-of-done text says CHANGELOG entries go under `## [0.0.8]`. Preferred answer per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut): `0.0.8` is shipped; new work accumulates under `[Unreleased]` and is promoted at the joint `0.0.9` cut. Fallback: if the maintainer has already opened a `## [0.0.9]` heading by implementation time, append there instead of `[Unreleased]`.
- **Card body names a non-existent test file.** The card says Slice 2's test lives at `examples/fakeshop/tests/test_commands.py`; no such file exists (the only `test_commands.py` is per-app at `apps/products/tests/`). Preferred answer per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): the test lands at [`examples/fakeshop/tests/test_inspect_django_type.py`][fakeshop-tests-inspect], mirroring the one-file-per-command convention of [`examples/fakeshop/tests/test_export_schema.py`][fakeshop-tests-export]. Fallback: if the maintainer prefers a single `test_commands.py` aggregating all example-project command tests, the inspect tests move there and `test_export_schema.py` is folded in too — but the per-command split is the existing pattern.
- **`inspect_django_type` argument resolution conflict.** The card body says positional `type_dotted_path` but its test passes a bare `"BookType"`. Preferred answer per [Decision 4](#decision-4--inspect_django_type-command-shape-and-argument-resolution): **dispatch by shape** — a dotted argument uses Django's `import_string` (a dotted import failure raises `CommandError` with the original error, never masked by a registry fallback); a bare name uses a unique-`__name__` registry lookup (ambiguous bare names raise `CommandError` listing candidates); and `--schema` (loaded via `import_module_symbol`, like `export_schema`) populates + finalizes the registry first. The `--schema` loader is `import_module_symbol` (the `module` / `module:symbol` selector forms), distinct from the type argument's `import_string`. Fallback: if the bare-name convenience proves error-prone, drop it and require the dotted path.
- **Relation-field nullability override deferred.** Preferred answer per [Decision 10](#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred): scalar-only for `0.0.9`; relation override-targets raise. Fallback: if relation override demand surfaces, the natural first extension is forward single-valued FK / OneToOne override (thread `force_nullable` into `resolved_relation_annotation`), with the many-side list-vs-element nullability ambiguity ([Relation handling][glossary-relation-handling]) staying out until its own design lands.
- **Dict-of-name vs tuple-set form.** Preferred answer per [Decision 5](#decision-5--two-key-tuple-set-override-form): two-key tuple-set. Fallback: a single `Meta.nullability = {"field": bool}` dict could be added later as sugar normalized to the two sets if consumers find two keys verbose; the tuple-set form stays the primary shape.
- **Consumer-authored-field override rejection false-positive.** Preferred answer per [Decision 8](#decision-8--override-validation-and-collision-behavior): naming a consumer-authored field in an override set raises (the annotation already controls nullability). Fallback: if a real pattern surfaces where a consumer wants the override to apply *on top of* a partial annotation override, the rule relaxes to "annotation wins, override is a documented no-op for that field" — but fail-loud is the default until that demand is concrete.
- **The Strawberry extension lifecycle is version-dependent; the spec pins claims to the uv.lock-resolved `0.316.0`.** Preferred answer per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form): the module-level-singleton factory preserves the instance-bound [Plan cache][glossary-plan-cache] and emits no `DeprecationWarning` under 0.316.0's per-request `get_extensions`. The package's declared floor is open-ended, so the *mechanism* (not the conclusion) can drift across the supported range — spec-004's `_sync` / `_async` model was accurate at its 2026-04-30 spike and is already stale. Fallback: if a supported Strawberry version stops calling the factory per request, re-derive Decision 3 against that version; the singleton-factory's "one shared instance, no instance-deprecation warning" property holds for any version with 0.316.0's `isinstance`-passthrough + instance-deprecation behavior.
- **`config/schema.py` / `TODAY.md` class-form drift is a live cold-cache regression, not harmless.** Preferred answer: Slice 1 migrates both to the singleton-factory — under 0.316.0 the bare class re-instantiates per request (cold plan cache, sync included), so it is a real (if silent) regression today. Fallback: none — the migration restores caching and removes no functionality.

<!-- LINK DEFINITIONS -->
<!-- Root -->
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md

<!-- docs/ -->
[docs-readme]: ../../README.md
[glossary-choice-enum-generation]: ../../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangooptimizerextension]: ../../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-metaaggregate_class]: ../../GLOSSARY.md#metaaggregate_class
[glossary-metaexclude]: ../../GLOSSARY.md#metaexclude
[glossary-metafields]: ../../GLOSSARY.md#metafields
[glossary-metafields_class]: ../../GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: ../../GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: ../../GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../../GLOSSARY.md#metaprimary
[glossary-metarequired_overrides]: ../../GLOSSARY.md#metarequired_overrides
[glossary-metasearch_fields]: ../../GLOSSARY.md#metasearch_fields
[glossary-plan-cache]: ../../GLOSSARY.md#plan-cache
[glossary-relation-handling]: ../../GLOSSARY.md#relation-handling
[glossary-scalar-field-override-semantics]: ../../GLOSSARY.md#scalar-field-override-semantics
[glossary]: ../../GLOSSARY.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-004-rationale]: spec-004-optimizer_beyond-0_0_3-rationale.md
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-022]: ../spec-022-export_schema-0_0_7.md
[spec-028]: ../spec-028-orders-0_0_8.md
[spec-029-d10]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-10--non-relation-scope-relation-field-overrides-rejected-and-deferred
[spec-029-d11]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-11--version-bumps-are-owned-by-the-joint-009-cut
[spec-029-d12]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-12--slice-independence-and-the-slice-3-carve-off-contingency
[spec-029-d1]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-1--spec-filename-and-canonical-naming
[spec-029-d2]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-2--one-spec-covers-all-three-slices
[spec-029-d3]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-3--slice-1-adopts-the-singleton-factory-extensions-form
[spec-029-d4]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-4--inspect_django_type-command-shape-and-argument-resolution
[spec-029-d5]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-5--two-key-tuple-set-override-form
[spec-029-d6]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion
[spec-029-d7]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-7--tri-state-force_nullable-threaded-through-convert_scalar
[spec-029-d8]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-8--override-validation-and-collision-behavior
[spec-029-d9]: ../spec-029-consumer_dx_cleanup-0_0_9.md#decision-9--choice-field-interaction
[spec-029-dod]: ../spec-029-consumer_dx_cleanup-0_0_9.md#definition-of-done
[spec-029-non-goals]: ../spec-029-consumer_dx_cleanup-0_0_9.md#non-goals
[spec-029-out-of-scope]: ../spec-029-consumer_dx_cleanup-0_0_9.md#out-of-scope-explicitly-tracked-elsewhere
[spec-029-scaffolding]: ../spec-029-consumer_dx_cleanup-0_0_9.md#implementation-scaffolding--staging-notes
[spec-029-terms]: spec-029-consumer_dx_cleanup-0_0_9-terms.csv
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md
[spec-032]: ../spec-032-full_relay-0_0_9.md
[spec-037]: ../spec-037-upload_file_image_mapping-0_0_11.md
[spec-048]: ../spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
[base]: ../../../django_strawberry_framework/types/base.py
[commands-imports]: ../../../django_strawberry_framework/management/commands/_imports.py
[converters]: ../../../django_strawberry_framework/types/converters.py
[export-schema-cmd]: ../../../django_strawberry_framework/management/commands/export_schema.py
[field-meta]: ../../../django_strawberry_framework/optimizer/field_meta.py

<!-- tests/ -->
[test-ci-governance]: ../../../tests/test_ci_governance.py
[test-extension]: ../../../tests/optimizer/test_extension.py
[test-relay-id-projection]: ../../../tests/optimizer/test_relay_id_projection.py

<!-- examples/ -->
[fakeshop-test-query-readme]: ../../../examples/fakeshop/test_query/README.md
[fakeshop-tests-export]: ../../../examples/fakeshop/tests/test_export_schema.py
[fakeshop-tests-inspect]: ../../../examples/fakeshop/tests/test_inspect_django_type.py

<!-- scripts/ -->
[check-citations]: ../../../scripts/check_citations.py
[check-spec-glossary]: ../../../scripts/check_spec_glossary.py

<!-- .venv/ -->
<!-- External -->
[upstream-cookbook]: https://github.com/riodw/django-graphene-filters
