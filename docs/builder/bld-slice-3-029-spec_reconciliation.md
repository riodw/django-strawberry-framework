# Build: Slice 3 — Spec reconciliation with HEAD

Spec reference: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` (whole file)
Companion: `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` (whole file)
Status: final-accepted

## Plan (Worker 1)

This slice has no Worker 2 (build plan `## Dispatch-shape deviation`): only Worker 1 may mutate a
spec or its rationale companion, so a builder has nothing it is permitted to write. Worker 1 plans
and performs in one pass and sets `Status: planned`; Worker 3 reviews off `planned`. Both the plan
and the full report of what was performed are below, so Worker 3 can review the work against the
stated intent rather than only against the diff.

### Scope declarations

- **Hot-path declaration:** `none`. Two documentation files; no line of executable code is touched.
- **Floor-verification scope:** `none`. No framework surface.
- **Failability proofs: not applicable, considered and dismissed.** `BUILD.md`
  `### What needs, and what does not` scopes the obligation to a **new boundary, guard, gate, or
  rejection path a slice introduces**. This slice introduces none: it corrects prose describing
  boundaries that already exist and are already pinned (the standing governance pin Slice 2 shipped,
  the type-creation validators, the command's `CommandError` branches). Recording that the obligation
  was weighed and does not attach, rather than manufacturing a proof for a documentation edit.
- **Coverage:** no `pytest` run is owed and none was made against the package suite. One focused
  run and two live command invocations were used as *measurements*, listed under
  `### Instruments and their controls`.

### DRY analysis

- **Helper inventory checked.** Not applicable in its usual form and the reason is recorded rather
  than skipped: `### Package-wide helper inventory before helper planning` exists to stop a plan
  proposing a **new helper** when one exists. This slice proposes no code and may write no `.py`.
  The equivalent duty here — *do not state a shape the package no longer has* — was discharged by
  reading the shipped helpers the spec names before rewriting any sentence about them:
  `types/base.py::_validate_nullability_override_targets`, `::_selected_meta_targets`,
  `::_format_unknown_fields_error`, `::_normalize_sequence_spec`, `::_build_annotations`,
  `types/converters.py::convert_field_output`, `::convert_scalar`,
  `management/commands/_imports.py` (whole file), and
  `management/commands/inspect_django_type.py` (whole file). Shapes searched for: `validate`,
  `normalize`, `selected`, `unknown`, `convert`, `import`, `force_nullable`.
- **Existing patterns reused.** The correction reuses the *shipped code's own vocabulary* rather
  than inventing spec-side names: "read-output entry point", "non-relation model fields", "matched
  MRO ancestor", "authoritative post-finalize record". Where the shipped docstrings and the
  `docs/GLOSSARY.md` entries already state a contract precisely (the file/image default-nullable
  rule, the command's three-way read source), the spec now says the same thing in the same terms, so
  a future reader comparing spec to glossary to source finds one description, not three.
- **New helpers justified.** None. Two documentation files.
- **Duplication risk avoided.** The dominant one here is **saying the same corrected fact in the
  spec and again in the companion**, which is the failure the rationale move exists to prevent. The
  split held to: the spec states the current contract with no chronology and never names the card
  that changed it; the companion carries the chronology, the attribution, and the retracted claim,
  and states the contract only as far as needed to say what it replaced. Verified by sweep — the
  spec contains no `spec-03x` / `spec-04x` reference and no `0.0.11` (see
  `### Instruments and their controls`, sweep 3).
- The second risk is **restating a claim at one site and not its sibling** — the dominant defect
  class in this repo's residual cycles. Every divergence below was swept for its full population
  before any site was edited, in both polarities where the claim has one. That is what turned
  divergence 6's two sites into three and surfaced two divergences the build plan did not list.

### Dispatched findings checklist

A residual cycle has no spec `## Slice checklist` for this slice, so `BUILD.md`
`### Dispatched findings checklist` applies. One box per build-plan section-C divergence, plus the
two this pass found itself. Boxes are `- [ ]` at planning and audited at final verification.

- [x] **C1** — scope widened past "scalar-only"; restate as the current contract per maintainer
      decision **D2** (non-relation model fields: scalar columns and file/image output objects,
      relations still rejected), with the widening, its card, and the retracted claim in the
      companion and **not** in the spec.
- [x] **C2** — the apply call site is `types/converters.py::convert_field_output`, not
      `convert_scalar`.
- [x] **C3** — three `#"substring"` citations resolve to zero at HEAD; re-derive each with
      `grep -cF` **and** against whitespace-flattened text (the wrap hazard), then repair.
- [x] **C4** — helper name, signature, and structure: `_validate_nullability_override_targets`
      (keyword-only, `relay_shaped: bool`), the shared `_selected_meta_targets` /
      `_format_unknown_fields_error` consolidation, the shipped check order, and the `## Current
      state` bullet still predicting `_validate_nullability_overrides`.
- [x] **C5** — Definition-of-done item 1's CSV claim is false at HEAD; fix the claim **and** its
      stale `## Risks and open questions` pointer in one edit.
- [x] **C6** — Definition-of-done item 4's forbidden-form claim, reconciled against what Slice 2
      landed. **BLOCKING: restate every site, not one.**
- [x] **C7** — Slice 2's shipped command surface is materially larger than Decision 4 describes;
      re-derive the list from the two test modules, not from the build plan's.
- [x] **C8** — both loaders route through `management/commands/_imports.py`, which adds a shared
      absolute-module-path rejection neither loader had at ship.
- [x] **C9** — stale census figures; decide per site whether the `## Current state` vintage framing
      licenses them, and say why in the companion.
- [x] **C10** (found by this pass) — `BookType` is Relay-Node-shaped at HEAD; the illustrative
      output, the paragraph under it, and a Test-plan assertion all say it is not.
- [x] **C11** (found by this pass) — six inline self-reference path literals still name the spec's
      pre-archive `docs/` location.

### Implementation steps

1. Re-verify the spec's status/header lines (`worker-1.md` `## Spec status-line re-verification`).
2. Re-derive each divergence against HEAD source before editing anything, on a controlled
   instrument. Record any that does not hold as rejected-with-reason.
3. Sweep each surviving divergence for its **full population** in both polarities before editing
   the first site.
4. Correct the spec: contract stated directly, no chronology, no amendment block, no "as of card N".
5. Append the record to the companion under the Decision each correction belongs to, by heading and
   anchor, carrying the change, its card where attributable, and the claim the Decision may no
   longer make.
6. Re-run the three gates, re-derive the markdown-link ordering by hand (`check_trailing_commas
   --check` validates the group headers but **not** the sort), and validate every anchor in both
   directions.

### Implementation discretion items

None. This slice has no second worker to delegate a choice to.

---

## Report of work performed (Worker 1)

### Spec status-line re-verification

Header lines 1-11 re-read in full. Two claims the build had falsified, both corrected (recorded
under `### Spec changes made`): the Predecessors line's `spec-027` clause, which called
`_validate_filterset_class` "the structural template for Slice 3's `Meta`-key validation" (C4), and
its closing claim that `docs/GLOSSARY.md` "has **no entry yet**" for the card's three net-new
symbols (false at HEAD; all three carry headings and CSV rows — C5's sibling site, found by sweeping
C5's population rather than editing the one site the build plan named). The `Status:` line, the
version-boundary paragraph, and the `## Current state` vintage framing at `:3` are accurate and were
left alone; that framing is load-bearing for C9's disposition.

### Instruments and their controls

Four measurements this pass depends on would have read identically whether or not they measured
anything. Each was controlled before its reading was believed, and **one control changed a result**.

1. **Citation resolver** (C3). Substring containment over whitespace-flattened file text, not a
   line-wise `grep`, so a citation wrapped across two lines cannot read as absent. Controls: two
   positives (`def _validate_nullability_override_targets` in `base.py` -> 1;
   `DjangoOptimizerExtension` in `test_extension.py` -> 125) and one negative
   (`ZZZ_this_string_does_not_exist_ZZZ` -> 0). Raw and flattened counts agreed on every row, which
   is itself the finding: the three broken citations are broken by **content drift, not by wrapping**.
2. **Anchor / link validator** (both files). **Its first version failed.** The slug function stripped
   `_` along with backticks, so every anchor containing an underscore read as missing — 50 false
   breakages, including `decision-4--inspect_django_type-...`. Caught by a positive control, not by
   the output looking wrong. GitHub's slugger keeps `_` (it is a `\w` character). The corrected
   version was re-controlled with **6 positive** cases (two of them underscore-bearing, one the
   renamed Decision 10 slug in each file) and **3 negative** (the retired `decision-10--scalar-only-
   scope-...` slug included, so the control proves the rename actually took). This is the second time
   in this cycle an instrument has died on delimiter handling and the second time only a positive
   control caught it.
3. **Chronology-leakage sweep** (the framing rule). `grep -nE` over the spec for
   `spec-03[0-9]|spec-04[0-9]|spec-05[0-9]|DONE-03|DONE-04|0\.0\.1[0-9]|later card|since ship|no
   longer|used to |previously|as of card|widened`. Every hit is pre-existing and legitimate —
   sibling-card references (`DONE-030`/`031`/`032`), parity-table status columns (`0.0.10`), the
   deliberately-kept derivation-baseline pin, and two slice-local "before the migration" statements.
   **No hit is mine**, and in particular the spec names neither `spec-037` nor `0.0.11`, which is
   maintainer decision D2's explicit constraint.
4. **Scope and gate polarity sweeps.** C1 was swept positively (`scalar-only`, `scalar column[s]
   only`, `scalar-column-only`, `scalar field names`, `applies to scalar`) and C6 both ways
   (`forbidden-form grep`, `finds zero hits`, `exact forbidden`). Both return zero after the edits;
   both returned a population before them. A sweep that returns zero on an un-edited file is the
   reading that means nothing, so each was run first against HEAD to confirm it fires.

Two further measurements are live rather than static and are recorded because a claim rests on each:
`uv run python examples/fakeshop/manage.py inspect_django_type BookType --schema config.schema` and
the same for `ShelfType` (C10, and the `SCALAR_MAP[BigAutoField]` row); and
`uv run python -m pytest tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form --no-cov`
-> `1 passed` (C6's zero-violation claim, checked rather than inherited from Slice 2's prose).

**One claim I wrote and then measured was wrong.** Correcting C10 I wrote that a non-Relay
`BigAutoField` pk reports converter `SCALAR_MAP[AutoField]`, reasoning from the MRO-ancestor rule.
Running the command against `ShelfType` returned `SCALAR_MAP[BigAutoField]` — `BigAutoField` is its
own `SCALAR_MAP` key, so the walk stops before `AutoField`. Fixed before the sentence stood.
Recorded because it is the exact failure mode `BUILD.md` warns about: a number (or a name) asserted
in the same breath as the rule it illustrates.

### Divergences, each with a verdict

**C1 — scope widened past "scalar-only". CORRECTED (maintainer decision D2).**
Holds. `types/base.py::_validate_nullability_override_targets` #"(scalar columns and file/image
output objects)" is the shipped rejection text, and `types/converters.py::convert_field_output`
takes `force_nullable`, applying it to the file/image output object's own default-nullable
annotation (`file_effective_null = True if force_nullable is None else force_nullable`) — so
`required_overrides` opts a `FileField` into `DjangoFileType!`. `docs/README.md:120` and the
`Meta.nullable_overrides` / `Meta.required_overrides` glossary entries already document exactly this
scope, so the spec was the only surface still saying scalar-only.
Population swept, **11 sites**, not the four the build plan named: Decision 10's *heading* and body,
`## Non-goals`, the Slice-3 checklist rule (d), `## Key glossary references`, Goal 3, the two
User-facing-API key descriptions, the `## User-facing API` error-shapes list, Decision 8's rule 4,
the Test plan, and `## Doc updates`. All 11 restated to **non-relation model fields**.
The heading was renamed `Scalar-only scope` -> `Non-relation scope`, which is the half that is easy
to skip and the half that a reader scanning the contents sees first. The rename moved
**6 in-page anchors + 1 link definition in the spec and 3 anchors + 1 heading + 1 link text in the
companion**, all re-verified. `## Edge cases and constraints` gained the file/image bullet it never
had (the widening's observable consequence: `nullable_overrides` on a file column is the redundant
no-op, `required_overrides` is the meaningful direction).
Companion: Decision 10 gains the widening, `DONE-037-0.0.11` as its cause, the fact that the
*boundary* never moved, and the retracted claim. The spec names neither card nor version — both
alternatives the maintainer rejected under D2.

**C2 — the apply call site is no longer `convert_scalar`. CORRECTED.**
Holds. `base.py::_build_annotations` #"annotations[field.name] = convert_field_output(" is the
shipped call. Population: the Slice-3 checklist bullet (with its broken citation, C3), Decision 7's
opening and its threading paragraph, Decision 8's stage 3, DoD items 10 and 11, the implementation-
plan row, and the `Scalar field conversion` glossary-reference bullet — **8 sites**.
Decision 7's *argument* survives the change intact and the companion says why: the tri-state was
carried onto the new entry point rather than reimplemented beside it, so there is still one
parameter on one converter and still nothing to unwrap at the call site — and the file branch makes
the rejected call-site-rewrite alternative worse, not better, since it would now have to unwrap a
`DjangoFileType | None` as well.

**C3 — three broken citations. CORRECTED; all three confirmed broken by content, not by wrapping.**
Measured raw and flattened (instrument 1). `[base] #"Meta.exclude must be a non-string sequence"`
-> 0 (the shipped message is the f-string
`f"Meta.{key} must be a non-string sequence or set of field names"`);
`[base] #"annotations[field.name] = convert_scalar(field, cls.__name__)"` -> 0 (C2);
`[test-extension] #"extensions=[_CaptureExt()]"` -> 0 (both sites are now
`extensions=[lambda: capture_ext]`). The build plan's other two rows re-derived and confirmed still
resolving.
Repairs, each chosen so the *fact* the citation supported survives:
- the `Meta.exclude` guard -> a `path::Symbol` link to `::_normalize_sequence_spec`, plus the two
  contract facts the rewrite exposed and the spec did not carry: the normalizer now **accepts a set
  or frozenset** (order carries no meaning for these keys) and rejects a non-`str` **entry**
  separately;
- the apply site -> `::_build_annotations #"annotations[field.name] = convert_field_output("`;
- the `_CaptureExt` sites -> the two enclosing test symbols
  (`::test_b8_consumer_prefetch_object_suppresses_optimizer_entry` and
  `::test_b8_consumer_plain_string_upgraded_to_optimizer_prefetch`), because no substring of those
  sites is unique and `path::Symbol` is the convention's answer for that.
**One more, not on the list.** `[base] #"suppress_pk_annotation"` resolves — three times. A
citation that resolves three times is not the `#"unique substring"` the convention specifies, and
the sentence was already being rewritten, so it was tightened to
`::_build_annotations #"if suppress_pk_annotation and field.name == pk_name:"`. The spec now carries
**5** such citations, each verified to resolve **exactly once**.

**C4 — helper name and structure. CORRECTED.**
Every part holds. Shipped name `_validate_nullability_override_targets`; parameters keyword-only,
taking `relay_shaped: bool` and deriving `model._meta.pk.name` itself; the unknown/excluded half
delegated to `_selected_meta_targets` + `_format_unknown_fields_error`. The build plan said that
helper is shared with `Meta.filesystem_path_fields` and `Meta.relation_shapes` — re-derived and
**confirmed at three callers** (`_validate_nullability_override_targets`,
`_validate_filesystem_path_targets`, `_validate_relation_shape_targets`), which is worth stating
because the helper's own docstring names only two of the three.
Shipped check order re-derived from the loop body: unknown -> excluded -> consumer-authored ->
Relay-pk -> relation. Decision 8 listed relation before Relay-pk; corrected, in Decision 8's rule
list, its stage-2 sentence, and the Slice-3 checklist's (d)/(e) pair.
Slice 1's specific hand-down closed: `## Current state` no longer predicts a
`_validate_nullability_overrides` helper. The bullet's *first* half is a true description of the
pre-build repo and stays; only its forward-looking last sentence was rewritten, which is the
distinction Slice 1's final verification asked for. Decision 8's structural-template framing is
replaced in three places (Predecessors, `## Current state`, Decision 8) by what actually shipped.

**C5 — DoD item 1's CSV claim. CORRECTED, claim and pointer in one edit.**
Holds. The CSV carries all three symbols (rows 18, 44, 45 of 45 lines = 44 terms + header) and
`check_spec_glossary` reports `OK: 44 terms`. Item 1 rewritten to state the *rule* the original
deferral was an instance of — a term whose glossary heading does not exist yet cannot be in the CSV
without failing the checker, so heading and row land together — which removes the false snapshot
without losing why the snapshot existed. Its `(per [Risks and open questions])` pointer went with
it, in the same edit, per Slice 1's instruction not to repoint a sentence about to be rewritten.
The item's `check_spec_glossary` command also carried the pre-archive path; corrected (C11).
**Sweeping C5's population found a second site the build plan did not name**: the Predecessors
line's "`docs/GLOSSARY.md` has **no entry yet** for ..." makes the same false claim about the same
three symbols. Both restated. This is the parallel-site class arriving on a divergence that had not
been flagged as having one.

**C6 — the forbidden-form gate. CORRECTED at all THREE sites (the blocking item).**
Both inherited sites verified present and restated: `## Definition of done` item 4 and the
`## Slice checklist` `#"Post-migration forbidden-form gate:"` bullet. **A third site exists** and
was found by sweeping for the gate's vocabulary rather than for its framing: the implementation-plan
row for Slice 1 asserts that `optimizer/extension.py`'s "module + class docstring `extensions=`
examples carry the forbidden instance/class form the forbidden-form gate requires zero of in active
source" — **false at HEAD**, where all three of that file's `extensions=[` occurrences are the
singleton-factory form. Restated to what that file's docstrings are actually for.
The replacement text states the rule **by form** — bare class, any constructing lambda, keyword-
carrying variants included — names
`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` as
the gate, and defines "active first-party source" exactly as Slice 2 handed down (the four
`check_citations.SOURCE_TREES` plus `EXTRA_SOURCE_FILES`, with the gitignored `docs/*/temp-tests/`
excluded by construction). It also records what Slice 2's inheritance list did **not** say and what
reading the pin's own docstring settles: the pin deliberately does **not** match the three *instance*
spellings the old list enumerated, because `pytest.ini`'s `filterwarnings = error` makes Strawberry's
instance-form `DeprecationWarning` fatal already. Restating the old five-spelling list under the new
gate would therefore have been wrong in a new way — it would have claimed pin coverage the pin does
not have. Of Worker 3's three resolution paths this is (a), applied to all three sites.
The `[test-ci-governance]` link definition Slice 2 flagged as absent was added, under `<!-- tests/ -->`;
`[check-citations]` was added with it, since the corrected text names that module's corpus.
Slice 2's measured population (25 -> 0 against 81 already-correct, 106 after) is **not** written into
the spec: it is a point-in-time census, which is precisely what C9 says a completion claim may not
carry. It lives in the companion instead.

**C7 — Slice 2's shipped surface. CORRECTED; list re-derived, and larger than the plan's.**
Re-derived from the two test modules (11 example tests, 25 package tests) and from the command's own
module docstring and `_resolve_row` dispatch, not copied. Everything the build plan listed holds.
Beyond it: `--schema`'s imported object is read for the schema's **scalar map and name converter**,
not only for its registration side effect; bare-name matching is against the **SDL name or** the
Python `__name__`, with a cross-surface collision ambiguous rather than first-match, and the table
**titled** with the SDL name; the `SCALAR_MAP` row is named by its **matched MRO ancestor**; the
ambiguity error lists **copyable dotted paths**; direct `class Foo(DjangoType, relay.Node)`
inheritance is recognized by the same `_is_relay_shaped` predicate synthesis uses.
**One item in this group is a correction, not an addition, and it is the important one.** Decision 4
claimed `origin.__annotations__` is "the single source of truth" for every field's resolved type and
that it "already reflects ... consumer-authored annotations". At HEAD a consumer-authored field's
entry there is a `StrawberryAnnotation` object or an *unresolved forward-ref string*, so those rows
read `origin.__strawberry_definition__` instead, and an unresolvable forward reference raises
`CommandError` on Strawberry's `UNRESOLVED` sentinel. A connection-only relation's annotation has
been deleted outright by the Phase-2.5 synthesizer. Decision 4's output-contract paragraph is
rewritten as the four-way most-specific-first dispatch the command performs; its underlying
principle — read the authoritative post-finalize record, never re-derive by re-running the converter
— is unchanged and is stated as such. DoD items 5 and 6 and the Slice-2 checklist bullets follow.

**C8 — both loaders route through `_imports.py`. CORRECTED.**
Holds. `inspect_django_type.py` imports `import_module_symbol_or_command_error` and
`import_string_or_command_error`; both call `_validate_absolute_module_path`, which rejects an empty
or relative module path **before any import is attempted**, and `import_or_command_error`, which
preserves the original message as the `CommandError`'s `__cause__`. Attribution re-derived from git
rather than assumed: `inspect_django_type.py` was added 2026-06-05, `_imports.py` extracted
2026-06-17, `_validate_absolute_module_path` added 2026-07-13 — so the helper is a post-029
consolidation, and its contract is now documented as `spec-022`'s Decision 3. The dispatch-by-shape
contract is intact and is stated as intact. The new rejection is a seventh `CommandError` mode in
Decision 4's list and in DoD item 6.

**C9 — stale census figures. CORRECTED, split by site type, with the reasoning recorded.**
Both halves of the build plan's hypothesis hold. Re-measured: `test_extension.py` carries **67**
lines containing `extensions=[` against the spec's 41, and the five named package test files total
**74** against the spec's 48 — and the `extensions=[` surface now spans 18 package test files and 8
example files, so the "five package test files" framing is stale in its shape as well as its
arithmetic.
Disposition, per site: `## Current state`'s census **stands**. The spec's own header frames that
section as "the repo as of this spec's authoring, before the build", so the figure is a dated
observation, and deleting it would make the section vaguer without making it truer. The identical
figures in **completion** claims do not get that licence — a Slice-checklist box and a Definition-of-
done item assert a finished state, so a stale number there is a false completion claim. Those three
(`## Slice checklist` code-sites bullet, DoD item 2, the implementation-plan row) now name the audit
that *produces* the population, `rg 'extensions=\['` over the named files, instead of storing a
count. Decision 3's `~41` went the same way.
Decision 3's granularity example was also replaced, per Slice 2's Amendment 3: the cross-module
`strictness` example became
`tests/optimizer/test_extension.py::test_strictness_flags_a_relation_under_an_unplannable_root`,
which builds two differently-configured schemas **inside one function** — a strictly better argument,
because it rules out per-function granularity and not merely per-file.

**C10 — `BookType` is Relay-Node-shaped at HEAD. CORRECTED. Not in the build plan's list.**
Found by running the command instead of reading the spec's illustrative table. `BookType.Meta`
declares `interfaces = (relay.Node,)` (`DONE-032-0.0.9`), so its pk row reads `GlobalID!` /
`relay.Node id`. The spec asserted the opposite in **three** places: the illustrative output's `id`
row, the paragraph under it ("`BookType` is **not** Relay-shaped (its `Meta` declares no
`interfaces`)"), and the Test plan's `test_inspect_by_registered_name` bullet ("including the
**non-Relay** pk `id` -> `Int!`"). The shipped test asserts `GlobalID!` and carries a comment saying
why. All three corrected; the illustrative table is now the command's real output, and the non-Relay
contrast is drawn against `ShelfType`, a type that is genuinely non-Relay at HEAD. Two further
render facts the old table got wrong were fixed with it: rows come out in `selected_fields` order,
and the "django field type" column is `type(field).__name__` verbatim (`ManyToOneRel`, plain
`CharField`), not a prettified label.

**C11 — stale pre-archive self-reference paths. CORRECTED. Not in the build plan's list.**
Six inline literals still named `docs/spec-029-consumer_dx_cleanup-0_0_9.md` / `...-terms.csv`,
where the files live at `docs/SPECS/` and `docs/SPECS/appx/`. The reference-style *link definitions*
were re-relativized by the archive sweep; the inline label text was not — the exact class my own
standing note calls out about archive moves. One of the six is a command a reader is meant to run
(DoD item 1's `check_spec_glossary` invocation), which is what makes this more than cosmetic.
Corrected, with Decision 1 noting the archive location rather than pretending the authoring location
is current. **Deliberately not touched**: the `docs/spec-021-nullable_overrides-0_0_8.md` references,
which quote the KANBAN card body's stale name and are the subject of Decision 1, and
`docs/spec-029b-nullable_overrides-0_0_9.md`, a hypothetical future spec that would correctly be
authored under `docs/`.

**No divergence was rejected.** All nine held on re-derivation, and two more were found. Recorded
plainly because the opposite outcome would also have been worth recording: the dispatcher's model of
the code was accurate this time, and under-inclusive in the same direction twice (C1's population,
C6's site count).

### Spec changes made (Worker 1 only)

Cited by heading, since line numbers move as the file is edited. Each carries its divergence.

| Spec heading | Change | Divergence |
|---|---|---|
| Header, Predecessors line | `spec-027` clause restated: the sidecar validators establish the per-`Meta`-key `_validate_*` pattern; Slice 3's target validation is a different shape | C4 |
| Header, Predecessors line | "GLOSSARY has no entry yet for the three symbols" -> all three carry headings and CSV rows | C5 |
| `## Key glossary references` | `Scalar field conversion` bullet names the `convert_field_output` read-output entry point | C2 |
| `## Key glossary references` | `Relation handling` bullet: scalar columns -> non-relation model fields | C1 |
| `## Slice checklist`, Slice 1 code-sites | stored census replaced by the audit that produces the population | C9 |
| `## Slice checklist`, Slice 1 gate bullet | one-shot grep over five spellings -> the standing pin, stated by form, with its corpus | C6 |
| `## Slice checklist`, Slice 2 ship bullet | shared `_imports.py` loaders + pre-validation; two-surface bare-name match; `--schema` supplies naming config; converter column widened | C7, C8 |
| `## Slice checklist`, Slice 2 error bullet | malformed-path and unresolved-forward-ref `CommandError` modes added; ambiguity restated | C7, C8 |
| `## Slice checklist`, Slice 3 validate bullet | check order corrected to unknown / excluded / consumer-authored / Relay-pk / relation | C4 |
| `## Slice checklist`, Slice 3 apply bullet | `convert_scalar` -> `convert_field_output`; broken citation replaced | C2, C3 |
| `## Slice checklist`, Slice 3 rules bullet | rule (d)/(e) reordered; "scalar-only scope" -> "non-relation scope" | C1, C4 |
| `## Current state`, validators bullet | no longer predicts a `_validate_nullability_overrides` helper | C4 |
| `## Current state`, census bullet | broken `_CaptureExt` citation -> two enclosing test symbols; census figures kept (vintage framing) | C3, C9 |
| `## Goals` item 3 | scalar field -> non-relation field | C1 |
| `## Non-goals`, relation bullet | scalar-column-only -> non-relation model fields only; `for 0.0.9` dropped | C1 |
| `## User-facing API`, Slice 2 output block | illustrative table replaced by the command's real output; render-order and column notes added | C10 |
| `## User-facing API`, Slice 2 paragraph | `BookType` is Relay-shaped; non-Relay contrast drawn against `ShelfType` | C10 |
| `## User-facing API`, Slice 3 keys | scalar field names -> non-relation field names; file/image `required_overrides` opt-out named | C1 |
| `## User-facing API`, error shapes | Relay-suppressed-pk shape added (was absent); relation shape -> non-relation scope | C1, C4 |
| `### Decision 3`, granularity bullet | `~41` dropped; same-function `strictness` pair replaces the cross-module example | C9 |
| `### Decision 4`, command shape | shared `_imports.py` paragraph added | C8 |
| `### Decision 4`, argument resolution | "different loader" -> "different importer"; shared-helper routing | C8 |
| `### Decision 4`, bare-name lookup | two-surface match, `iter_definitions`, copyable-dotted-path candidates | C7 |
| `### Decision 4`, output contract | rewritten as the four-way most-specific-first dispatch; `origin.__annotations__`-is-the-single-source claim retired | C7 |
| `### Decision 4`, finalized registry | `--schema` also supplies scalar map + name converter | C7 |
| `### Decision 4`, failure modes | 5 -> 7 modes (malformed path, unresolved forward ref) | C7, C8 |
| `### Decision 7`, opening | both converter entry points carry the tri-state | C2 |
| `### Decision 7`, threading | `convert_field_output` dispatch spelled out; file/image default-nullable rule stated | C1, C2 |
| `### Decision 8`, stage 1 | shape check named as the shared `_normalize_sequence_spec` | C3, C4 |
| `### Decision 8`, stage 2 | shipped symbol, keyword-only signature, `relay_shaped: bool` | C4 |
| `### Decision 8`, stage 3 | applies via `convert_field_output` | C2 |
| `### Decision 8`, rule list | `_selected_meta_targets` sharing paragraph added; Relay-pk rule added as 4; 5 rules -> 6 | C1, C4 |
| `### Decision 10` (heading) | `Scalar-only scope` -> `Non-relation scope`; 6 in-page anchors + 1 link def follow | C1 |
| `### Decision 10`, body | non-relation scope stated; the boundary named as the annotation path | C1 |
| `### Decision 1`, body | archive location named | C11 |
| `## Implementation plan`, Slice 1 row | census dropped; the false `optimizer/extension.py` forbidden-form claim corrected | C6, C9 |
| `## Implementation plan`, Slice 3 row | converters cell names both entry points | C2 |
| `## Edge cases and constraints` | file/image override bullet added | C1 |
| `## Edge cases and constraints` | non-sequence bullet: broken citation -> `::_normalize_sequence_spec`; set/frozenset acceptance and per-entry rejection stated | C3 |
| `## Test plan`, Slice 2 example tests | pk assertion corrected to `GlobalID!`; `test_inspect_by_meta_name`, consumer-authored and BigInt rows added | C7, C10 |
| `## Test plan`, Slice 2 package tests | renamed ambiguity test corrected; malformed-path, forward-ref, naming, converter and rendering groups added | C7, C8 |
| `## Test plan`, Slice 3 | "scalar-only scope" -> "non-relation scope" | C1 |
| `## Doc updates`, Slice 3 | "scalar-only scope" -> "non-relation scope" | C1 |
| `## Definition of done` item 1 | CSV claim and stale pointer replaced in one edit; command path corrected | C5, C11 |
| `## Definition of done` item 2 | stored census -> the audit that produces the population | C9 |
| `## Definition of done` item 4 | one-shot grep -> the standing pin, by form, with its corpus and the `filterwarnings` division of labour | C6 |
| `## Definition of done` item 5 | shared loaders, two-surface bare name, per-origin authoritative record | C7, C8 |
| `## Definition of done` item 6 | 5 -> 7 `CommandError` modes | C7, C8 |
| `## Definition of done` item 10 | `convert_field_output` carries the same tri-state | C2 |
| `## Definition of done` item 11 | shipped symbol, signature, check order, shared helpers, `convert_field_output` | C2, C4 |
| `<!-- LINK DEFINITIONS -->` | `[commands-imports]`, `[test-ci-governance]`, `[check-citations]` added | C6, C8 |
| 4x `[spec-029]` + 1x `[spec-029-terms]` link labels | pre-archive paths corrected | C11 |

**Companion changes** (`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`), all
appended under the Decision each belongs to, by heading and anchor:

| Companion heading | Entries appended |
|---|---|
| `## Provenance of this record` | a "Corrected by Slice 3" paragraph closing Slice 1's forward-looking "Not corrected here" note and pointing at this artifact |
| `## Decision 3` `### Changes this Decision underwent` | the one-shot grep's rot and the measured repair; the retracted five-spelling-grep claim; the census and granularity-example replacements |
| `## Decision 4` | the `_imports.py` consolidation with its dates; the re-derived surface growth; the retracted single-source-of-truth claim; the `BookType` Relay flip |
| `## Decision 7` | the `convert_field_output` insertion; why the Decision's argument survives it; the retracted `convert_scalar` call-site claim |
| `## Decision 8` | the shipped name vs the rev1 name; why `relay_shaped` not a pk name; the `_selected_meta_targets` consolidation retiring the structural-template framing; the retracted rejection order |
| `## Decision 10` | the `DONE-037-0.0.11` widening; what did not move; the retracted scalar-only claim |
| `## Non-Decision deliberation` `### Documentation-coherence passes` | the discharged CSV deferral and its stale pointer; the kept-vs-removed reasoning for the stale figures |
| `## Decision 10` heading | renamed in lockstep with the spec's, keeping all 12 titles character-identical |
| `<!-- LINK DEFINITIONS -->` | `[docs-readme]`, `[glossary-metarequired_overrides]`, `[spec-022]`, `[spec-032]`, `[spec-037]`, `[spec-048]`, `[commands-imports]`, `[test-ci-governance]` |

### The spec grew, and by how much

**+19,478 bytes** (133,713 -> 153,191), +38 lines (679 -> 717). Stated, not buried: this was a
correctness pass, not a size pass, and a corrected claim is routinely longer than the false one it
replaces. The growth concentrates where the shipped surface outgrew its description — Decision 4's
output contract went from one paragraph asserting a single source of truth to a four-way dispatch
that is what the command does; the Slice-2 test-plan list went from 5 failure modes to the shipped
population; DoD item 4 went from a five-item spelling list to a rule stated by form plus the two
mechanisms that enforce it.

The figure is re-derivable in the only form available, and the arithmetic closes on it: HEAD is
`170,042` (`git show HEAD:<spec> | wc -c`), the file on disk is `153,191` (`wc -c`), and Slice 1's
twice-verified figure for its own close is `133,713`. `170,042 - 133,713 = 36,329`, matching Slice
1's recorded drop exactly; `153,191 - 133,713 = 19,478` is this slice; `36,329 - 19,478 = 16,851` is
the net against HEAD, which `170,042 - 153,191` confirms. Slice 1's `133,713` is cited as **its**
measurement, not re-derived here — its state is not in git and the working tree now carries this
slice on top of it — and the sum closing is the check available.

Companion: **58,950 -> 75,296 bytes** (+16,346), 428 -> 457 lines. Same reason, plus the fact that
the rationale is where every removed chronology went.

### Structural invariants held

Verified against `git show HEAD:` rather than assumed: **25** slice-checklist boxes (all `- [ ]`,
the shipped-spec convention), **18** Definition-of-done items, **12** Decisions — all three
unchanged. All **12** Decision titles are character-for-character identical between spec and
companion, which is the property the whole `[rationale-dN]` / `[spec-029-dN]` pointer chain rests on
and which the Decision 10 rename was the standing risk to.

### Gates

| Check | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | `OK: 44 terms` |
| `uv run python scripts/check_citations.py` | `OK: 789 citations resolve` |
| `uv run python scripts/check_trailing_commas.py --check` | pass |
| Link defs, both files: used-but-undefined / defined-but-unused | `[]` / `[]` |
| Link defs, both files: every path disk-exists-checked | no misses |
| Link-def ordering, re-derived by hand | the three groups I inserted into are in order under **both** live conventions; the two pre-existing out-of-order groups (`docs/` in the spec, `docs/` and `docs/SPECS/` in the companion) are HEAD's own and untouched — confirmed by diffing the spec's link block against HEAD, where my only additions are the three new defs |
| In-page + cross-file anchors, both files, controlled instrument | 0 broken |
| `#"substring"` citations in the spec | 5, each resolving **exactly once** |
| `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form --no-cov` | `1 passed` |

`check_trailing_commas --check` validates the ten group headers and **not** the within-group sort,
so the ordering row above is a hand re-derivation, not that gate's result.

### Notes for Worker 1 (spec reconciliation)

Carried to final verification. Nothing here was fixed in this pass.

1. **Two `.py` docstring defects found while re-deriving, both outside the editable surface.**
   `types/base.py::_selected_meta_targets`'s docstring says it is "shared by
   `_validate_nullability_override_targets` and `_validate_relation_shape_targets`" — there are
   **three** callers; `_validate_filesystem_path_targets` is missing. And
   `::_validate_nullability_override_targets`'s docstring gives its check order as
   "unknown -> excluded -> (consumer-authored / relation / Relay-pk)" while its own loop checks
   Relay-pk **before** relation. Neither is a behavior defect and neither is this cycle's to edit
   (this slice writes no `.py`); both belong in `bld-final-029.md`'s `### Deferred work catalog`.
2. **A Decision rename must land in both files, and this slice performed one.** Decision 10 is now
   `Non-relation scope; relation-field overrides rejected and deferred` in the spec and in the
   companion, character-identical, with every anchor re-verified. Any later rename of any Decision
   carries the same obligation, and no gate checks it.
3. **`## Current state`'s census is deliberately stale and must not be "fixed" later.** Its 48/41
   figures are dated observations the spec's own header licenses. A future pass sweeping for stale
   numbers will find them; the reason they stand is recorded in the companion under
   `### Documentation-coherence passes`, so the decision can be read rather than re-litigated.
4. **The spec deliberately names no post-029 card.** That is maintainer decision D2, applied beyond
   D2's own divergence to every correction in this slice. A reviewer looking for "later widened by
   card N" in the spec will correctly find nothing; every such pointer is in the companion.
5. **Two divergences (C10, C11) were found by this pass, not dispatched to it.** Both are recorded
   with verdicts above and both are corrected. Flagged because the build plan's section C is the
   canonical work-list and now under-describes what this slice did.

### Final status

`Status: planned`, per the build plan's `## Dispatch-shape deviation`, so Worker 0 dispatches Worker
3 for the independent review.

---

## Review (Worker 3)

Dispatched off `Status: planned` per the build plan's `## Dispatch-shape deviation`; a
`revision-needed` routes back to **Worker 1**, never Worker 2.

### Scope obligations considered

- **Failability proofs: not applicable — considered and dismissed, and I re-derived the reason
  rather than accepting Worker 1's.** `BUILD.md` `### What needs, and what does not` scopes the
  obligation to a new boundary, guard, gate or rejection path a slice introduces. The diff is two
  `.md` files; `git status` shows no `.py` in this slice's ownership column, and the public-surface
  check below confirms zero package-source bytes. There is nothing to mutate. No proof was
  manufactured and no re-run set is owed (`empty re-run set is legal only when the diff introduces
  no boundary that meets the floor` — it introduces none).
- **`scripts/review_inspect.py`: skipped.** Recorded with its reason: the slice contributes zero
  `.py` bytes, so there is no file with review-worthy logic for the helper to parse. No shadow file
  was read or produced by this pass.
- **Hot-path budget: `none`** (plan preamble and artifact both declare it; two documentation files,
  no executable line). **Floor-verification scope: `none`** (no Django / Strawberry / channels seam).
- **Coverage:** no `--cov*` flag was used. One focused `pytest` run with `--no-cov` and two live
  management-command invocations were used as measurements; both are listed below.

### Instruments, and the controls that licensed each reading

Four of my readings would have been indistinguishable from a passing proof had the instrument been
broken, so each was controlled before it was believed. **One control caught a dead instrument.**

1. **Heading slugger / anchor validator** (both files). Controlled with **four positives** — two
   underscore-bearing (`decision-4--inspect_django_type-…`,
   `decision-6--net-new-allowed_meta_keys-entries-not-a-deferred_meta_keys-promotion`), one the
   renamed Decision 10 slug — and one **negative** that renders the *retired* slug
   (`decision-10--scalar-only-scope-…`), which is what proves the rename actually took rather than
   that my slugger is permissive. Written independently of Worker 1's; it keeps `_` because `_` is
   a `\w` character, the exact trap Worker 1 disclosed.
2. **`#"substring"` citation resolver.** Counts occurrences **raw and whitespace-flattened**
   separately (the wrap hazard), controlled at 1 (`def _validate_nullability_override_targets`) and
   0 (`ZZZ_does_not_exist_ZZZ`).
3. **Restored-deliberation detector** (8-word-gram set overlap, spec-added-lines vs companion).
   Controlled with a real companion sentence (**0.50** overlap) and an invented one (**0.00**).
4. **`path::Symbol` resolver over both `.md` files.** Its first version reported four breakages;
   the control showed the failure was mine — `check_citations.py::suffix_index` resolves a citation
   by **trailing sub-path**, so `types/base.py::…` and `_imports.py::…` are conformant short forms.
   Re-derived with suffix resolution: all four targets exist and each suffix is **unique** in the
   corpus. **This class is validated by no gate at all** — `check_citations` scans `.py` files and
   `KANBAN.md` only (`OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)`), so the
   spec's 25 and the companion's 6 `path::Symbol` citations are checked by nothing but this pass.

A grep of mine also died silently and was caught by its own oddity: `^## Meta.nullable_overrides`
returned nothing against `docs/GLOSSARY.md` because the heading is backtick-wrapped
(`` ## `Meta.nullable_overrides` ``). Both override headings exist. A "no match" from a
hand-written grep is not a measurement until something known-present has been through the same pipe.

### High:

None.

### Medium:

#### M1 — C4's parallel-site population is short by one, and the fourth site is a false structural claim

`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:33` (`## Key glossary references`):

```docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:33
- [`Meta.filterset_class`][…] / [`Meta.orderset_class`][…] — the two shipped sidecar keys whose
  `_validate_*_class` validators ([`base.py`][base]) are the structural template for Slice 3's
  `Meta`-key validation (a new `_validate_*` helper called from `_validate_meta`).
```

The report states C4's structural-template framing "is replaced in **three places** (Predecessors,
`## Current state`, Decision 8) by what actually shipped". `:33` is a fourth, and it is the one that
states the retired shape as a *mechanism*, not merely as a framing.

Re-derived against source, both halves are false at HEAD:

- there is **no** `_validate_*` helper for these keys called from `_validate_meta`. The shape check
  is an inline `_normalize_sequence_spec(getattr(meta, "nullable_overrides", None),
  "nullable_overrides")` call in `types/base.py::_validate_meta`, exactly as `Meta.exclude` does,
  and the both-sets collision is raised there directly;
- the only helper that exists, `types/base.py::_validate_nullability_override_targets`, is called
  from `__init_subclass__`, not from `_validate_meta` — which is precisely what Decision 8 stage 2
  and the companion's rev2 P1 entry ("that signature is **not implementable**") say.

`:33` carries no vintage framing. The spec's header licenses only `## Current state` as "the repo
as of this spec's authoring"; `## Key glossary references` reads as current contract, so a reader
who trusts it goes looking for a helper the package does not have — the same reader Decision 8 then
contradicts two sections later. This is the parallel-site skip class landing a **third** time in
this one cycle (C1's population, C6's site count, now C4's), and it is the class the dispatch named
as dominant.

**Recommended change.** Restate `:33` to the shipped shape and keep the sidecar keys' real role, on
the lines of: the two sidecar keys' `_validate_*_class` validators establish the "shape gates run
once in `_validate_meta`" invariant Slice 3's two keys follow — they shape-check through the shared
`_normalize_sequence_spec` there, and target-validate later in `__init_subclass__` via
`_validate_nullability_override_targets` (see Decision 8).

**Re-check the two siblings in the same edit**, because the same wording survives at both and the
population is a set, not a site: `:9` (Predecessors) and `:98` (`## Current state`) each say Slice
3's shape check "follows" the *"one `_validate_*` helper per `Meta` key, called from
`_validate_meta`"* pattern. At HEAD no per-key helper exists for these keys, so the claim is true
only of the `_validate_meta` **location**, not of the per-key-helper **shape** the sentence names.
`:98` is vintage-framed and may stand on that licence; `:9` is not, and should say what `:33` will
say. No behavior claim elsewhere in the spec depends on this, so the edit is contained.

**Test expectation:** none — documentation only. The verification is a re-read of
`types/base.py::_validate_meta` against the corrected sentence.

### Low:

#### L1 — DoD item 4 attributes `EXTRA_SOURCE_FILES` to the wrong module; its own sibling site does not

`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:558` — "the four
[`scripts/check_citations.py`][check-citations] `SOURCE_TREES` plus the tracked `.py` files outside
them that **its** `EXTRA_SOURCE_FILES` carries back". Measured: `scripts/check_citations.py`
contains **0** occurrences of `EXTRA_SOURCE_FILES`; its module-level constants are `REPO_ROOT`,
`SOURCE_TREES`, `PACKAGE_ROOT`, `MARKDOWN_SOURCES`, `UPSTREAM_PREFIXES`, `SYNTHETIC_SOURCES`,
`FAMILY_SUFFIXES`, `CITATION_RE`. The constant is `tests/test_ci_governance.py::EXTRA_SOURCE_FILES`
(`("conftest.py", "docs/dry/export_dry_review.py", "line_count.py")`) — the pin's own module.

The Slice-checklist restatement of the identical fact at `:60` has no possessive and is correct.
So C6's two surviving restatements of one gate-corpus fact have already drifted by one word, in the
same slice that added them. **Fix:** drop `its`, or name the owning module explicitly.

#### L2 — C11's population stops at the spec; the companion carries the same class

`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md:368` renders
``[`docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`][spec-029-terms]`` — the visible label names
the **pre-archive** path while the definition resolves to `appx/spec-029-…-terms.csv`, so label and
target disagree. `:369` carries `docs/spec-029-consumer_dx_cleanup-0_0_9.md` in prose.

Both sit inside the verbatim-moved `## Risks and open questions` body, which makes `:369`'s
historical reading defensible (it records the rev1 preferred answer, given at a time the file was at
`docs/`). A link whose label contradicts its own target is not defensible on that ground. The
companion is in this slice's writable set, and C11's stated class is "inline self-reference path
literals", so the sweep should have crossed the file boundary. The four
`docs/spec-021-nullable_overrides-0_0_8.md` occurrences at `:42/:57/:62/:67/:369` are correctly left
alone — they quote the KANBAN card body's stale name, the same deliberate exclusion the spec makes.

#### L3 — the companion's own illustrative-output section still asserts the fact C10 reversed

`…-rationale.md:339` (`## Non-Decision deliberation` → `### The illustrative inspect_django_type
output`): "**rev3 P2.2** — `BookType` is **not** Relay-shaped, so the illustrative `id -> GlobalID!`
row was wrong. It became `id -> Int!` …". True as chronology, and chronology is what this file is
for. But it is the section a reader looking for "the illustrative output" lands on, and it carries
no pointer to `## Decision 4`'s `Post-ship: the worked example's host type became Relay-shaped`
entry that reverses it. A one-clause forward pointer closes it; no text needs deleting.

#### L4 — the artifact's link-def ordering row mis-states its own population

`### Gates` says "the two pre-existing out-of-order groups (`docs/` in the spec, `docs/` and
`docs/SPECS/` in the companion)" — that is three groups called two, and it omits a fourth. Measured
across both files under both live conventions (ref-id sort and full-def-line sort), the groups that
are out of order under one convention are: spec `docs/` (full-line: `[glossary]` before
`[glossary-aggregateset]`), **spec `docs/SPECS/`** (ref-id: `rationale-d12` > `rationale-d1`,
`spec-029-terms` > `spec-029`), companion `docs/`, companion `docs/SPECS/`.

The row's **conclusion is correct and I re-derived it independently**: the ten canonical headers are
present and in order in both files; every group is sorted under at least one convention; and the
three groups Slice 3 inserted into (`django_strawberry_framework/`, `tests/`, `scripts/`) are sorted
under **both**. Only the stated population is wrong, and a stated population that does not re-derive
is the exact shape this cycle exists to catch.

### DRY findings

- **No duplication introduced.** The dominant risk on this slice — stating a corrected fact in the
  spec and again in the companion — was tested rather than assumed. Of the **99** substantive lines
  the spec adds against HEAD, only **2** cross a 30% 8-gram overlap with the companion, and both
  overlap solely on the long `#decision-10--non-relation-scope-…` anchor slug, not on prose. The
  spec contains `Justification:` **0** times, `Alternatives considered` **0** times, `Revision
  history` **0** times; its 12 `rejected alternative` hits are the 12 designed pointer lines. No
  deliberation was restored.
- **Existence challenge: raised and dismissed on evidence.** The candidate was the spec's
  `## Risks and open questions`, now reduced to one rule plus a pointer. It earns its place: the
  derivation-baseline rule is a standing contract constraint (a supported Strawberry version that
  stops calling the `extensions=` factory per request invalidates Decision 3), not deliberation, and
  it is load-bearing for the C6 repair's premise. Deleting the section would relocate a live rule
  into a Decision that does not otherwise discuss the supported range. Nothing else in either file
  is an abstraction with one caller.
- **Out of fence, route to `### Deferred work catalog` — the terms CSV still says scalar-only.**
  `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv:44` describes
  `Meta.nullable_overrides` as "forcing a **scalar** field nullable … **scalar-only**, validated at
  type creation", and `:45` as "forcing a **scalar** field required". That is C1's retired claim
  surviving on a third surface. The CSV is explicitly outside this cycle's writable set, so this is
  **not** a finding against the slice — but C1's population sweep should have surfaced it, and the
  artifact's `### Notes for Worker 1` does not name it. `docs/GLOSSARY.md` is already correct (both
  headings say "**non-relation** field names"), so the CSV is the only stale surface left anywhere.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**; `git diff --stat` on that path
reports nothing. `__all__` and the re-export list are unchanged. The slice touches no package source
at all, which is also what discharges the failability-proof obligation above.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The slice modifies documentation, so this section applies and was performed end-to-end.

- **Version strings / card IDs.** The spec names no post-029 card and no post-`0.0.9` version — the
  constraint maintainer decision **D2** imposed, applied beyond D2's own divergence. Verified by
  sweep: zero occurrences of `rev[0-9]`, `Revision [0-9]`, `P1.`/`P2.`/`P3.`, `amendment`,
  `as of card`, `later card` anywhere in the spec. `spec-037` and `0.0.11` appear only in the
  companion. Both alternatives the maintainer rejected under D2 (leave Decision 10 as a `0.0.9`
  snapshot; name the widening card inline) are absent.
- **Chronology, swept in both polarities.** Beyond the negative vocabulary I ran the positive
  spelling (`now`, `since`, `currently`, `today`, `already`, `still`, `later`, `previously`,
  `originally`, `formerly`, `at ship`, `post-ship`, `widened`, `renamed`, `retired`, `retracted`).
  Every hit is pre-existing and describes the migration's *before* state inside the Slice checklist,
  `## Current state`, Decision 3, or DoD item 3 — the pre-build framing Slice 1's accepted pass left
  standing. Cross-checked against the HEAD diff: none of them is among the 99 lines this slice
  added. **Slice 3 reintroduced no chronology site.**
- **Links.** Ten canonical group headers present and in exact order in **both** files. Used-but-
  undefined `[]` and defined-but-unused `[]` in both. Every link-def target disk-exists-checked and,
  where it carries a fragment, anchor-checked: **0 broken** across both files. In-page anchors:
  **0 broken** (spec 41 headings / 19 distinct anchors used; companion 57 / 16). Within-group sort
  re-derived by hand under both conventions — see L4; the three groups this slice wrote are clean.
  `[test-ci-governance]` landed under `<!-- tests/ -->` in correct position
  (`test-base-init` < `test-ci-governance` < `test-converters`), as the inherited hand-down required.
- **Link-block diff against HEAD** confirms the slice added exactly three definitions
  (`[commands-imports]`, `[test-ci-governance]`, `[check-citations]`) and touched nothing else in
  the block — which is what makes L4's pre-existing-inversion claim provable rather than asserted.
- **No obsolete "planned" wording** in surfaces the slice deliberately updated. No script-rendered
  doc is touched (`docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md` all outside the fence and
  unmodified). No spec archival is performed by this slice.

### What looks solid

Every claim below was re-derived by this pass, not read off the report.

- **C10 is exact, and it is the strongest item in the slice.** I ran the command rather than reading
  it: `inspect_django_type BookType --schema config.schema` piped to `diff` against the spec's
  fenced block at `:200-209` reports **IDENTICAL** — all seven rows, column widths included. The
  `ShelfType` contrast is real (`id  BigAutoField  Int!  no  SCALAR_MAP[BigAutoField]`), so the
  disclosed `SCALAR_MAP[AutoField]` self-catch is fixed in the shipped bytes. `BookType.Meta`
  carries the Relay shape, and the live assertion at
  `examples/fakeshop/tests/test_inspect_django_type.py:91-94` asserts `GlobalID!` + `relay.Node id`
  with a comment naming spec-032. The two render facts added with it (rows in `selected_fields`
  order; `type(field).__name__` verbatim) are both visible in the real output.
- **C6's third site is real and the correction is right.** `optimizer/extension.py` has exactly
  three `extensions=[` occurrences; two are `extensions=[lambda: _optimizer]` and the third is a
  prose comment. The spec's retired claim that its docstrings carry the forbidden form was false at
  HEAD. **I hunted a fourth and found none** — sweeping the gate's vocabulary (`forbidden`, `zero
  hits`, `zero violation`, `one-shot`, `grep`, `rg '`, `gate`) returns the three restated sites
  (`:60`, `:411`, `:558`) and nothing else that makes a gate claim.
- **The pin-vs-`filterwarnings` division of labour is true, and it was worth checking rather than
  inheriting.** `pytest.ini` carries `filterwarnings = error`; `check_citations.SOURCE_TREES` is a
  4-tuple; `EXTRA_SOURCE_FILES` exists and carries three files back. Restating the old five-spelling
  list under the new pin would indeed have claimed coverage the pin does not have. The gate itself
  passes: `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form
  --no-cov` → `1 passed`.
- **C1's population is closed and the lockstep holds mechanically.** Zero `scalar-only` /
  `scalar column(s) only` / `scalar-column-only` / `scalar field names` / `applies to scalar`
  occurrences remain in the spec. The shipped rejection text
  (`types/base.py::_validate_nullability_override_targets`) says "non-relation model fields only
  (scalar columns and file/image output objects)" — the spec now matches it word for word.
  **All 12 Decision titles are character-for-character identical between spec and companion**,
  verified by extracting both heading sets and comparing; the renamed Decision 10 slug resolves in
  both files and the retired slug resolves in neither.
- **C2 / C4 / C8 verified at source.** `convert_field_output(field, type_name, *, force_nullable:
  bool | None = None, expose_filesystem_path: bool = False)` with `file_effective_null = True if
  force_nullable is None else force_nullable`; `convert_scalar` keyword-only with
  `effective_null = field.null if force_nullable is None else force_nullable`;
  `_validate_nullability_override_targets` keyword-only taking `relay_shaped: bool` and deriving
  `model._meta.pk.name` itself; its loop order **consumer-authored → Relay-pk → relation**, which is
  the order Decision 8 rules 3/4/5 now list; `_selected_meta_targets` shared at three callers;
  `_imports.py` exporting `import_or_command_error`, `_validate_absolute_module_path`,
  `import_module_symbol_or_command_error`, `import_string_or_command_error`, with
  `inspect_django_type.py` importing the latter two.
- **C5, C7, C9 re-measured.** CSV rows 18 / 44 / 45 of 45 lines carry the three symbols and
  `check_spec_glossary` reports `OK: 44 terms`; all three glossary headings exist. **All 25** test
  names the reconciled Test plan adds exist in the two modules (each exactly once). The census
  re-derives digit-for-digit: `tests/optimizer/test_extension.py` **67**, five package test files
  **74** — and neither figure is stored in a completion claim any more, while `## Current state`'s
  dated 48/41 stands on the header's own vintage licence. Slice 2's point-in-time census (25 / 81 /
  106) correctly appears nowhere in the spec.
- **The byte arithmetic closes on measured values.** `git show HEAD:<spec> | wc -c` = **170,042**;
  `wc -c` on disk = **153,191**; companion **75,296** / **457** lines. 170,042 − 133,713 = 36,329;
  153,191 − 133,713 = 19,478; 36,329 − 19,478 = 16,851 = 170,042 − 153,191. Slice 1's 133,713 is the
  one cited rather than re-derived figure, and the sum closing on three independently measured
  numbers is the available check.
- **Structural invariants hold against HEAD, not against the report:** 25 checklist boxes, 18
  Definition-of-done items, 12 Decisions in both the HEAD copy and the working copy.
- **The five `#"substring"` citations each resolve exactly once**, raw *and* whitespace-flattened —
  so none is a wrap-hazard false green. The three broken ones are gone, and the tightened
  `#"if suppress_pk_annotation and field.name == pk_name:"` resolves once where the old
  `#"suppress_pk_annotation"` resolved three times.
- **The companion is keyed as `BUILD.md` requires.** Every entry sits under a `## Decision N`
  heading whose title matches the spec's, or under `## Non-Decision deliberation`; each post-ship
  entry names the shipped behavior, its card where attributable, and the claim the Decision may no
  longer make. The C1 rename orphaned nothing.

### Temp test verification

- Directory created: `docs/builder/temp-tests/slice-3-029/` — **no temp test was written**. Nothing
  in this slice is a behavior suspicion; every question was answerable by reading source, running
  the shipped command, or running one existing test. Scratch instruments (the slugger/anchor
  validator, the citation resolver, the gram-overlap detector, the ordering checker, the symbol
  resolver) were written **outside the repository**, under the session scratchpad, and produced no
  tracked file.
- Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **The eleven `### Dispatched findings checklist` boxes are all `- [ ]`** while the report records
   all eleven as corrected. That matches this artifact's own stated discipline ("Boxes are `- [ ]`
   at planning and audited at final verification") given Worker 1 planned and performed in one pass,
   so it is not a finding — but final verification owes the audit-and-tick, and C10 / C11 need boxes
   that the build plan's section C does not contain.
2. **`Escalated:` the terms CSV is the last surface still saying scalar-only.**
   `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv:44-45`. Out of the maintainer's
   fence for this cycle, so it belongs in `bld-final-029.md`'s `### Deferred work catalog`, not in a
   re-loop. Resolution paths: (a) catalog it for the next cycle that may edit the CSV; (b) escalate
   to the maintainer now as a one-line fence exception, since the row is two words and the claim it
   makes is one this cycle formally retired. I recommend (a) — the fence is explicit and the CSV
   description is not a contract surface a consumer reads.
3. **The two `.py` docstring defects are confirmed and I did not act on them**, per the dispatch:
   `types/base.py::_selected_meta_targets` names two of its three callers, and
   `::_validate_nullability_override_targets`'s docstring gives its per-name order as
   "(consumer-authored / relation / Relay-pk)" while its loop checks Relay-pk first. Both re-read at
   source this pass. Worker 0 owns them in a separate code slice; they are not re-filed here.
4. **No gate validates a `path::Symbol` citation inside a `.md` file.** `check_citations` reports
   `712 in 426 .py files, 77 in KANBAN.md` — `docs/` is out of scope by design. The spec's 25 and
   the companion's 6 were resolved by hand this pass (all clean, all suffixes unique). A future
   rename of any of those symbols breaks these silently, exactly as the `#"substring"` class does.
   Worth a line in the deferred catalog as a standing blind spot, not a defect of this slice.
5. **Decision 10's rename obligation is discharged and I confirmed it mechanically**, so note 2 of
   the Worker-1 report stands as written: the retired slug
   `decision-10--scalar-only-scope-relation-field-overrides-rejected-and-deferred` resolves in
   neither file, and the new slug resolves in both.

### Review outcome

`revision-needed`.

One Medium (**M1**) and four Lows (**L1-L4**), none with a recorded rejection reason, so the
acceptance gate is not met. Routing is to **Worker 1** per the build plan's
`## Dispatch-shape deviation` — Worker 2 may not write a spec.

**What closes it:** M1 restated at `:33` with `:9` re-checked in the same edit; L1's `its` dropped
or re-attributed at `:558`; L2's `:368` label repointed to the archived path in the companion;
L3 given a forward pointer at `:339`; L4's ordering row corrected to the population I measured.
L2-L4 are one-line edits and L1 is one word; M1 is the only item requiring judgement, and the
recommended wording above is a proposal, not an instruction.

The slice's substance is sound and I want that recorded alongside the verdict: all nine dispatched
divergences held on independent re-derivation, C10 and C11 were genuine finds, the C10 correction is
byte-exact against a live command run, no chronology was reintroduced, no deliberation was restored,
and the Decision-title lockstep the rename put at risk holds at 12 of 12. The rejection is about a
fourth parallel site and four record-level slips, not about the reconciliation.

---

## Apply-changes report (Worker 1, pass 2)

Closing Worker 3's `revision-needed`: one Medium (**M1**) and four Lows (**L1-L4**). Routed to Worker 1
per the build plan's `## Dispatch-shape deviation` — only Worker 1 may mutate a spec or its rationale
companion. Nothing Worker 3 verified as correct was touched; no `.py` file was written.

### Scope declarations (re-confirmed, not re-manufactured)

- **Hot-path declaration:** `none`. **Floor-verification scope:** `none`. Both carried forward from
  the plan preamble unchanged; this pass edits two `.md` files and contributes zero executable lines.
- **Failability proofs: not applicable.** Both prior passes recorded the dismissal with its reason
  (`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a **new** boundary
  a slice introduces). I confirmed those records exist rather than writing a third — the plan's
  `### Scope declarations` bullet and Worker 3's `### Scope obligations considered` bullet both carry
  it, so the obligation is discharged on the record and manufacturing a proof for a prose edit would
  be the failure the section warns about.
- **Coverage:** no `pytest` run was made and none is owed; no `--cov*` flag was used anywhere.

### Instruments and their controls

Every reading below is from an instrument that was controlled in **both** directions first, because a
control that did not run reads identically to a passing proof.

1. **Link-def ordering checker** (L4). Parses the block, checks the ten canonical headers against the
   fixed order, and sorts each group under **both** live conventions (bare `ref-id`, full def line).
   Controlled on three synthetic files outside the repo: a sorted one (`refid_sorted=True
   fullline_sorted=True`, headers `True`), a deliberately unsorted group (`False` / `False`, flagged
   `OUT OF ORDER UNDER BOTH`), and a header-swapped one (headers `False`, listing the observed order).
   All three fired as expected, so a `True` here is a reading rather than a default.
2. **Anchor / link-def validator** (both files). Slug function keeps `_` (a `\w` character) — the trap
   that produced 50 false breakages in this cycle. Positive controls: the underscore-bearing
   `decision-4--inspect_django_type-command-shape-and-argument-resolution` resolves in **both** files
   (it is the anchor L3's new pointer targets); the retired
   `decision-10--scalar-only-scope-...` slug resolves in **neither**. Negative control: a fabricated
   anchor in a synthetic file was reported `BROKEN` — so the detector fires, which is the half a
   `total broken: 0` cannot establish on its own.
3. **`#"substring"` citation resolver.** Counts raw **and** whitespace-flattened occurrences
   separately. Controlled at 1/1 (`def _validate_nullability_override_targets` in `base.py`), 0/0
   (`ZZZ_nope_ZZZ`), and — the control that matters for the wrap hazard — a deliberately line-wrapped
   copy of a real `AGENTS.md` citation, which reads **raw=0 flat=1**, proving the flattening arm can
   distinguish a wrapped citation from an absent one.
4. **Label-vs-target checker** (L2). Walks every `[label][ref]` whose label reads as a path and
   compares it against the resolved definition target. Its output is dominated by conformant
   `path::Symbol` labels and short-form suffix paths, which is the expected shape; the one stale
   *directory* claim it surfaced is L2's, and it is now gone.
5. **8-gram overlap detector** (restored-deliberation check on my own additions). Controlled at
   **1.00** on a real companion sentence and **0.00** on an invented one.

### Findings, each with what changed

#### M1 — C4's structural-template population. CORRECTED at the named site and at BOTH siblings.

Re-derived before editing, on a sweep keyed on the **claim** (what Slice 3's `Meta`-key validation is
modelled on, and where it is called from) rather than on the prior pass's wording. Terms swept in both
files: `structural template`, `template`, `pattern`, `modelled` / `modeled`, `mirrors`, `follows it`,
`helper per`, `per-`Meta`-key`, `_validate_meta`, `__init_subclass__`, `_normalize_sequence_spec`,
`_validate_filterset_class`, `_validate_orderset_class`, `sidecar`.

**The population is three spec sites, and zero companion sites.** Listed rather than counted:

- `:9` (Predecessors) — claimed `_validate_filterset_class` establishes the "one `_validate_*` helper
  per `Meta` key, called from `_validate_meta`" pattern **"Slice 3's shape check follows"**. Half
  false: Slice 3's keys hold the *location* invariant and not the per-key-helper *shape*.
- `:33` (`## Key glossary references`) — Worker 3's named site. Fully false in both halves.
- `:98` (`## Current state`) — same half-false sentence as `:9`.
- Decision 8 (`:352`-`:358`), DoD item 11 (`:571`), the Slice-3 checklist bullet (`:69`) and the
  implementation-plan row (`:413`) all state the shipped staging correctly and were left alone.
- Companion `:244` already carries "**Post-ship: the unknown/excluded half became shared, which
  retired this Decision's structural-template framing**", so no companion edit is owed for M1.

**On `:98` I departed from Worker 3's disposition, deliberately.** Worker 3 wrote that `:98` "is
vintage-framed and may stand on that licence". The spec's header licenses `## Current state` as *"the
repo as of this spec's authoring, before the build"* — a licence for a dated **observation**. "Slice
3's shape check follows it" is not an observation of the pre-build repo; it is a **prediction about
the build**, and it is the same class the prior pass was told by Slice 1 to rewrite in this very
bullet (the `_validate_nullability_overrides` prediction, whose first half stayed because it *was* a
true pre-build description). Leaving a falsified prediction under a vintage licence would extend that
licence from "what the repo was" to "what the build would do", which is not what the header says.
The bullet's true pre-build half — the two validators, the local in-function import, the
`ConfigurationError` — is untouched.

Ground truth re-derived at source before any sentence was written:
`types/base.py::_validate_meta` calls `_validate_filterset_class` and `_validate_orderset_class`
(so the per-key-helper pattern is real for the sidecar keys), and shape-checks the two override keys
through **inline** `_normalize_sequence_spec(getattr(meta, "<key>", None), "<key>")` calls, raising
the both-sets collision there directly; `_validate_nullability_override_targets` is called from
`DjangoType.__init_subclass__`, not from `_validate_meta`.

All three sites now state the same shipped shape: the sidecar validators hold the "shape gates run
once in `_validate_meta`" invariant, Slice 3's two keys hold to that invariant **without** a per-key
`_validate_*` helper (shape-checking through the shared `_normalize_sequence_spec`), and their target
validation runs later, from `__init_subclass__` via `_validate_nullability_override_targets`.

#### L1 — `EXTRA_SOURCE_FILES` mis-attributed. CORRECTED; population re-derived and it is one site.

Re-measured rather than inherited: `scripts/check_citations.py` contains **0** occurrences of
`EXTRA_SOURCE_FILES`; the constant is defined once, at
`tests/test_ci_governance.py::EXTRA_SOURCE_FILES` (`("conftest.py",
"docs/dry/export_dry_review.py", "line_count.py")`), and a repo-wide `--include='*.py'` grep outside
`.venv` returns hits in that one file only.

The claim's population in the writable set is **two** sites — spec `:60` and `:558` — and **zero** in
the companion. Only `:558` carried the possessive `its`, which attached the constant to
`check_citations.py`; it now names the owner explicitly, as
"the pin's own `tests/test_ci_governance.py::EXTRA_SOURCE_FILES`" carrying the
`[test-ci-governance]` reference. `:60`
names the constant with no possessive and no owner claim, so it was correct and is untouched, per the
instruction not to disturb what Worker 3 verified. **No third restatement exists.**

#### L2 — the companion's stale pre-archive label. CORRECTED; population re-derived across both files.

Re-derived with a path sweep rather than by trusting the finding's single citation: occurrences of the
pre-archive form `docs/spec-...` across both files are spec `:79`, `:257`, `:401`, `:522`, `:526` and
companion `:42`, `:57`, `:62`, `:67`, `:368`, `:369`. Dispositions:

- companion `:368` — **fixed.** The visible label read
  `` `docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` `` while `[spec-029-terms]` resolves to
  `spec-029-consumer_dx_cleanup-0_0_9-terms.csv` (relative to `docs/SPECS/appx/`). Label and target
  disagreed. It now matches the sibling use at `:357`, which already carried the bare filename.
- companion `:369` and spec `:257` / `:522` / `:526` — **left alone.** All quote the KANBAN card
  body's stale `spec-021` name or the rev-time preferred answer inside the verbatim-moved
  `## Risks and open questions` body; the same deliberate exclusion the prior pass recorded and
  Worker 3 confirmed.
- spec `:79` / `:401` — **left alone.** `docs/spec-029b-nullable_overrides-0_0_9.md` is a
  hypothetical future spec, which would correctly be authored under `docs/`.

After the fix, the label-vs-target checker reports **no remaining label that claims a directory its
own definition contradicts** in either file.

#### L3 — the companion's reversed illustrative-output claim. CORRECTED by pointer, nothing deleted.

The companion's `### The illustrative ...` subsection under `## Non-Decision deliberation` gains one bullet in the
companion's own convention for a claim it may no longer make — the same
`**Claim … may no longer make: …**` form Decisions 3, 4, 7, 8 and 10 already use — naming
`DONE-032-0.0.9` as the cause, saying the rev3 P2.2 record stands as chronology, and pointing at
`## Decision 4`'s `Post-ship: the worked example's host type became Relay-shaped` entry by heading and
anchor. The anchor `#decision-4--inspect_django_type-command-shape-and-argument-resolution` was
confirmed resolvable **in the companion** (it is the file the pointer lives in) by the controlled
validator, not assumed.

#### L4 — the artifact's ordering row. CORRECTED here, and the population re-measured, not accepted.

Worker 3's own caution applies to Worker 3's finding, so I re-derived the ordering from scratch with
the controlled checker above rather than copying its figures. The measurement agrees with Worker 3's
and **not** with the prior pass's row.

Groups out of order under exactly one convention — enumerated, so the count is `len()` of the list:

| File | Group | `ref-id` sorted | full-def-line sorted | first divergence |
|---|---|---|---|---|
| spec | `<!-- docs/ -->` (48 defs) | yes | **no** | `[glossary]: ../GLOSSARY.md` |
| spec | `<!-- docs/SPECS/ -->` (23 defs) | **no** | yes | `rationale-d10` before `rationale-d1` |
| companion | `<!-- docs/ -->` (19 defs) | **no** | yes | `glossary-choice-enum-generation` before `glossary` |
| companion | `<!-- docs/SPECS/ -->` (26 defs) | **no** | yes | `spec-004-rationale` before `spec-004` |

**Four groups, not two.** The prior pass's `### Gates` row named three of them and called them "two",
and omitted spec `<!-- docs/SPECS/ -->` entirely. That row is a prior pass's record and is left
standing rather than rewritten; **this table supersedes it.** The row's *conclusion* is unchanged and
independently re-derived here: the ten canonical headers are present and in the fixed order in both
files; **every** group is sorted under at least one live convention, so zero groups are out of order
under both; and the three groups Slice 3 wrote into (`django_strawberry_framework/`, `tests/`,
`scripts/`) are sorted under **both**. This pass added no link definition to either file, so the
block is byte-identical to the one Worker 3 measured.

### Spec changes made (Worker 1 only)

| Spec heading | Change | Finding |
|---|---|---|
| Header, Predecessors line (`:9`) | the `spec-027` clause now states the "shape gates run once in `_validate_meta`" invariant Slice 3's keys hold to, and says explicitly they have no per-key `_validate_*` helper — the shape check is the shared `_normalize_sequence_spec`, the target check runs from `__init_subclass__` | M1 |
| `## Key glossary references` (`:33`) | same correction; the sidecar bullet no longer calls the `_validate_*_class` validators the structural template for "a new `_validate_*` helper called from `_validate_meta`", a helper that does not exist at HEAD | M1 |
| `## Current state` (`:98`) | the bullet's forward-looking half no longer predicts that Slice 3's shape check follows the per-key-helper pattern; its true pre-build description of the two sidecar validators is untouched | M1 |
| `## Definition of done` item 4 (`:558`) | "its `EXTRA_SOURCE_FILES`" -> "the pin's own `tests/test_ci_governance.py::EXTRA_SOURCE_FILES`" (carrying the `[test-ci-governance]` reference), ending the mis-attribution to `check_citations.py` | L1 |

**Companion changes** (`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`):

| Companion heading | Change | Finding |
|---|---|---|
| `## Risks and open questions`, GLOSSARY bullet (`:368`) | link label `docs/spec-029-…-terms.csv` -> `spec-029-…-terms.csv`, so label and definition target agree | L2 |
| `## Non-Decision deliberation` -> the illustrative-output subsection | one `**Claim this section may no longer make …**` bullet added, pointing at `## Decision 4`'s post-ship entry; the rev3 P2.2 chronology is kept verbatim | L3 |

No `Status:` line, no checklist box, and no other section of this artifact was altered. No `.py` file
was touched: the two `.py` docstring defects (`_selected_meta_targets` naming 2 of its 3 callers;
`_validate_nullability_override_targets`'s stated check order contradicting its own loop) remain the
separate code slice's, and nothing written above describes them as anything but confirmed and owned
elsewhere. The terms CSV (`…-terms.csv` rows 44-45) stays outside the fence and stays routed to
`bld-final-029.md`'s `### Deferred work catalog`.

### Byte counts, measured

| File | Before this pass | After | Delta | Lines |
|---|---|---|---|---|
| `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | 153,191 | **153,989** | **+798** | 717 -> 717 |
| `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` | 75,296 | **75,807** | **+511** | 457 -> 458 |

Both "before" figures were re-measured on disk at the start of this pass (`wc -c`) and match the prior
pass's recorded close exactly, so the two records join without an unverified hop. The spec's HEAD
figure is unchanged at 170,042 (`git show HEAD:<spec> | wc -c`), so the net against HEAD is now
`170,042 - 153,989 = 16,053`. The companion does not exist at HEAD (`git status` reports it `??`),
which is why it has no HEAD figure in any pass's arithmetic.

### Gates, re-run after the last edit

| Check | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | `OK: 44 terms` (exit 0) |
| `uv run python scripts/check_citations.py` | `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)` (exit 0) |
| `uv run python scripts/check_trailing_commas.py --check` | exit 0 |
| `#"substring"` citations in the spec | **5**, each resolving **exactly once** raw *and* whitespace-flattened; **0** in the companion |
| In-page anchors + link-def fragments + every def path disk-exists, both files | `total broken: 0`, on a detector proved to fire |
| Ten canonical group headers, both files | present and in the fixed order |
| Within-group sort, both files, both conventions | re-derived by hand — see L4; zero groups unsorted under both; the three groups this slice wrote are sorted under both |
| Link-def block vs the version Worker 3 measured | unchanged; this pass added no definition |
| Structural invariants vs the prior pass | 25 checklist boxes, 18 Definition-of-done items, 12 Decisions — all unchanged |
| Decision-title lockstep spec <-> companion | **12 of 12 character-identical** |
| Chronology / retraction / amendment in the four edited spec lines | none. The only hits from the negative-and-positive vocabulary sweep are `later` / `still` describing **construction-flow ordering** ("runs later, from `__init_subclass__`") and a pre-existing `already` in `:9`'s untouched spec-019 clause |
| Restored deliberation: 8-gram overlap of each edited spec line against the companion | **0.000** on all four, on a detector controlled at 1.00 / 0.00 |

### Notes for Worker 1 (spec reconciliation)

Carried forward; nothing here was fixed in this pass.

1. **The eleven `### Dispatched findings checklist` boxes are still `- [ ]`,** as this artifact's own
   stated discipline requires at planning. Final verification owes the audit-and-tick, and C10 / C11
   need boxes the build plan's section C does not contain — Worker 3's note 1, unchanged and still
   open.
2. **`Escalated:` the terms CSV rows 44-45 remain the last surface saying "scalar-only".** Outside the
   maintainer's fence; belongs in `bld-final-029.md`'s `### Deferred work catalog`, not a re-loop.
3. **The two `.py` docstring defects are confirmed and untouched**, owned by a separate code slice.
4. **No gate validates a `path::Symbol` citation inside a `.md` file.** `check_citations.py` scans
   `.py` files and `KANBAN.md` only. The one such citation this pass added
   (`tests/test_ci_governance.py::EXTRA_SOURCE_FILES`) was resolved by hand against source; the
   standing blind spot is Worker 3's note 4, still open for the deferred catalog.
5. **`:98`'s disposition is a deliberate departure from Worker 3's recommendation**, argued under M1
   above. If the re-review disagrees, the disagreement is about how far `## Current state`'s vintage
   licence reaches — not about the fact, which both passes measured the same way.

### Final status

`Status: planned`, so Worker 0 re-dispatches Worker 3 for the re-review.

---

## Review (Worker 3, pass 2)

Re-review of Worker 1's apply-changes pass. Dispatched off `Status: planned` per the build plan's
`## Dispatch-shape deviation`; a `revision-needed` would route back to **Worker 1**, never Worker 2.
Fresh subagent, no memory of pass 1 — every claim below was re-derived from the artifact chain, the
files on disk, and source.

### Scope obligations considered

- **Failability proofs: not applicable — considered and dismissed, re-derived rather than inherited.**
  `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a **new** boundary,
  guard, gate or rejection path a slice introduces. This pass's whole diff is four in-place spec line
  rewrites and one companion bullet plus a five-byte label fix. `git status` shows no `.py` in Slice
  3's ownership column and the public-surface check below confirms zero package-source bytes, so
  there is nothing to mutate. **Empty re-run set is legal here** — the diff introduces no boundary
  that meets the mandatory floor. No proof was manufactured.
- **`scripts/review_inspect.py`: skipped**, reason recorded: the slice contributes zero `.py` bytes,
  so there is no file with review-worthy logic for the helper to parse. No shadow file read or
  produced.
- **Hot-path budget: `none`. Floor-verification scope: `none`.** Both carried by the plan preamble
  and re-confirmed by the apply pass; two documentation files, no executable line.
- **Coverage:** no `--cov*` flag was used anywhere in this pass. No `pytest` run was owed and none
  was made.
- **Concurrent work, not judged:** `docs/review/**`, `tests/mutations/test_operations.py`, and
  Slice 2's eight `.py` files are dirty in the tree and are outside this slice's ownership column.
  `git status` is not a reading of this diff; attribution is by the build plan's ownership table.

### Instruments, and the controls that licensed each reading

Five readings would have been indistinguishable from a passing proof had the instrument been broken.
Each was written independently of Worker 1's and controlled in **both** directions before belief.
**One of my own instruments died silently and the control caught it.**

1. **Label-vs-target checker** (L2). Walks every `[label][ref]` whose label reads as a file path,
   resolves the definition relative to the source file, and compares basename **and** directory
   claim. Controlled on a synthetic copy of the companion placed at the same relative depth, with
   **two** injected faults: a basename contradiction (`docs/WRONGNAME.md` -> `../../GLOSSARY.md`)
   and a directory contradiction (`docs/spec-029-…-terms.csv` -> `spec-029-…-terms.csv`). **Both
   fired.** Live reading on both real files: zero contradictions.
2. **Anchor / link-def validator.** Slugger keeps `_` (a `\w` character — the trap that produced 50
   false breakages earlier in this cycle) and skips fenced blocks. Controlled with two injected
   faults on a synthetic copy: a fabricated in-page anchor (`#decision-8--ZZZ-does-not-exist`) and a
   fabricated def fragment (`GLOSSARY.md#zzz-no-such-heading`). **Both fired.** Live: `0 broken`
   across in-page anchors, link-def fragments and def paths in both files.
3. **Link-def ordering checker** (L4). Parses the block, checks the ten canonical headers against the
   fixed order, sorts each group under **both** live conventions. Controlled with a two-def swap
   inside a currently-sorted group (correctly flagged `<!-- tests/ -->` as unsorted under both) and a
   header swap (correctly reported headers out of canonical order). Both fired.
4. **`#"substring"` citation resolver.** Counts raw **and** whitespace-flattened occurrences.
   Controlled at 1/1 (`def _validate_nullability_override_targets`), 0/0 (`ZZZ_nope_ZZZ`), and — the
   arm that matters — a deliberately line-wrapped real citation reading **raw=0 flat=1**.
5. **Claim-keyed structural sweep** (M1), run **twice with disjoint vocabularies** so the population
   is not the instrument's vocabulary. Pass A keyed on wording (`structural template`, `template`,
   `pattern`, `modelled`/`modeled`, `mirror`, `precedent`, `analog`, `follows`, `per-key`,
   `helper per`, `_validate_*`, `sidecar`, `_validate_meta`, `__init_subclass__`,
   `_normalize_sequence_spec`, `_validate_filterset_class`, `_validate_orderset_class`). Pass B
   keyed on nothing of the sort: every fence-stripped **sentence** mentioning an override key
   **and** a validation verb (35 sentences), read individually. Both landed on the same population.

**My own dead instrument, disclosed.** My first citation resolver matched `path.py::Sym #"…"` as a
literal path and returned **0 citations in both files** — a clean-looking reading that measured
nothing, because this spec spells its citations as reference links (``[`_build_annotations`][base]
#"…"``). Caught only because 0 was implausible against the artifact's claim of 5. Re-run on the raw
`#"` marker: 5 in the spec, 1 in the companion (and that one is the literal phrase `#"substring"`
used as a term, not a citation — so **0 companion citations** is right).

### High:

None.

### Medium:

None.

### Low:

None.

### Verdict on each prior finding

**M1 — C4's structural-template population. CLOSED.**

Ground truth re-derived at source myself before grading the sentences, and Worker 1's account of it
is exact: `types/base.py::_validate_meta` calls `_validate_filterset_class` (`base.py:1277`) and
`_validate_orderset_class` (`:1278`), so the per-key-helper pattern **is** real for the sidecar keys;
the two override keys shape-check through **inline** `_normalize_sequence_spec(getattr(meta,
"<key>", None), "<key>")` calls at `:1299`-`:1305` with the both-sets collision raised at `:1307`
directly in `_validate_meta`; and `_validate_nullability_override_targets` is called at `:672`,
inside `DjangoType.__init_subclass__` (`:566`), not from `_validate_meta`.

Population re-derived independently on **two disjoint instruments** (5 above): **three spec sites
(`:9`, `:33`, `:98`), zero companion sites.** All three now state the shipped shape and each is true
at HEAD. Everything Worker 1 reports as already-correct-and-left-alone I read and confirm correct:
the Slice-3 checklist bullet (`:69`), Decision 8 (`:352`-`:360`), the implementation-plan row
(`:413`) and DoD item 11 (`:571`) all describe the shipped staging; Decision 8's `:352` even states
the negative directly ("it cannot be collapsed into one helper called from `_validate_meta`").
Companion `:244` already carries the retirement, so no companion edit was owed.

Pass B — the sentence-level sweep that shares no vocabulary with the finding's wording — surfaced
**no fourth site**. This is the first sweep in this cycle where a re-derivation on a second
independent instrument did not grow the population, and that is the reason I am willing to call the
class closed rather than "closed so far".

**Ruling on the `:98` disagreement: Worker 1 is right; my predecessor's vintage licence does not
reach it.** Stating the rule so a future reader inherits one precedent, not two:

> **`## Current state`'s vintage licence covers dated OBSERVATIONS of the pre-build repo. It does not
> cover PREDICTIONS about what the build would do.** A falsified observation stays (it was true when
> written and the header dates it); a falsified prediction is rewritten, because no framing in this
> spec dates a claim about the build's outcome.

Three things make that the right line rather than a convenient one. (a) The spec's header licenses
the section as *"the repo as of this spec's authoring, before the build"* and the section itself as
*"a true description of the repo as of this writing"* — both are about the repo, neither about the
build. (b) It is the line Slice 1's final verification already drew **in this same bullet**, keeping
its true pre-build half (the two validators, the local in-function import, the `ConfigurationError`)
and rewriting the `_validate_nullability_overrides` prediction; extending the licence to predictions
would have contradicted an accepted precedent from earlier in the same cycle. (c) It keeps C9
coherent rather than breaking it: the 48/41 census is a dated **observation**, so it stands under the
same rule that requires `:98`'s prediction to go. One rule, both dispositions.

I then tested the rule against the rest of the section rather than only against the site that
prompted it, because a new rule that opens an unswept population is worse than no rule. Every other
forward-looking clause under `## Current state` is a prediction the build **fulfilled**, so none is
falsified and none is owed an edit: `:101`'s "Slice 3 does NOT need a `nullable_overrides` slot on
the definition" holds (`types/definition.py` carries no such field at HEAD); `:105`'s "the three
glossary entries are authored during implementation" holds; `:106`'s "Slice 2 instead uses Django's
`import_string`" holds (`_imports.py:7` imports it and `:54` calls it — the `_imports.py` wrapper C8
documents routes through it rather than replacing it). The ruling closes at one site.

**L1 — `EXTRA_SOURCE_FILES` attribution. CLOSED.** Re-measured, not inherited: `scripts/
check_citations.py` contains **0** occurrences of `EXTRA_SOURCE_FILES`; a repo-wide
`--include='*.py'` grep outside `.venv` returns it in exactly one file,
`tests/test_ci_governance.py`, where it is defined at `:420`. `check_citations.py:54`'s
`SOURCE_TREES` **is** the 4-tuple the sentence claims, and `tests/test_ci_governance.py:37` imports
it precisely so the two cannot drift, with `_sweep_corpus()` (`:474`) unioning it with
`EXTRA_SOURCE_FILES` — so the corrected `:558` text is accurate in both halves, not just in its
attribution. `:60` re-read and confirmed to make no ownership claim.

*Observed and deliberately not filed:* `:60`'s parallel construction ("the four `check_citations.py`
`SOURCE_TREES` plus the tracked `.py` files outside them that `EXTRA_SOURCE_FILES` carries back")
still lets a fast reader carry the attribution across the "plus". It asserts nothing false, pass 1
verified it, and re-opening a verified-correct site to tighten a reading would be manufacturing a
finding. Recorded so the next reader knows it was examined and passed, not missed.

**L2 — the pre-archive label, and the triage. CLOSED, and I checked the triage rather than the
fix.** The convenient-exemption risk is real, so I did not grade "legitimately quotes a stale name"
on argument. I swept **every** `docs/…` path literal in both files (54 in the spec, 21 in the
companion) and then ran the controlled label-vs-target checker over both: **zero labels claim a
directory their own definition contradicts.** Each survivor re-read individually:

- spec `:79` / `:401` — `docs/spec-029b-nullable_overrides-0_0_9.md`, a hypothetical follow-up spec
  that *would* be authored under `docs/`. Correct as written.
- spec `:257` / `:522` / `:526` and companion `:42` / `:57` / `:62` / `:67` / `:370` —
  `docs/spec-021-nullable_overrides-0_0_8.md`, quoting the KANBAN card body's stale reference, which
  is the **subject** of Decision 1. Rewriting the quotation would destroy the thing Decision 1 is
  about.
- companion `:370`'s `docs/spec-029-consumer_dx_cleanup-0_0_9.md` is the one I pushed hardest on,
  since it names *this* spec at its pre-archive path. It survives on its own sentence, not on the
  exemption: it is a rev-time preferred answer inside the verbatim-moved `## Risks and open
  questions` body, and the very next clause says the reference is rewritten "in the `docs/SPECS/
  NEXT.md` Step-8 archive sweep" — the sweep that produced the current location. The record is
  internally coherent and names its own supersession. It is also a plain code span, not a link whose
  target contradicts it, which is the distinction that made `:368` a defect and this not one.

**L3 — the reversed illustrative-output claim. CLOSED.** The bullet is at companion `:340`, in the
file's own `**Claim … may no longer make: …**` convention, naming `DONE-032-0.0.9`, keeping the rev3
P2.2 chronology verbatim at `:339`, and pointing at `## Decision 4`'s entry **by heading and
anchor**. I verified the pointer rather than reading it: the target heading string
`Post-ship: the worked example's host type became Relay-shaped` exists verbatim at companion `:157`,
and the anchor `#decision-4--inspect_django_type-command-shape-and-argument-resolution` resolves in
the companion (the file the pointer lives in) on the controlled validator.

*Existence / proportionality challenge raised on this bullet and dismissed on measurement.* The
prior finding prescribed "a one-clause forward pointer"; 515 bytes is more than one clause, and it
restates three facts `:157` already carries — the duplication risk this slice itself named as
dominant. But the file's convention is not a bare pointer: all six sibling bullets state the
retracted claim and the corrected fact before pointing, and at 449 / 478 / 589 / 618 / 720 / 1095
bytes the new bullet sits mid-range. Following the convention is the better answer than the
prescription's letter, and the restatement is a retraction under the affected section rather than a
second copy of a contract.

**L4 — the ordering row, and the artifact discipline. CLOSED, and the discipline is right.**
Re-derived from scratch on my own controlled checker, agreeing with Worker 1's table group-for-group
and direction-for-direction: **four** groups out of order under exactly one convention — spec
`<!-- docs/ -->` (48 defs, ref-id sorted, full-line not), spec `<!-- docs/SPECS/ -->` (23, full-line
sorted, ref-id not), companion `<!-- docs/ -->` (19, full-line sorted, ref-id not), companion
`<!-- docs/SPECS/ -->` (26, full-line sorted, ref-id not). **Zero** groups unsorted under both. Ten
canonical headers present and in the fixed order in both files. The three groups this slice wrote
into are sorted under **both** conventions.

Leaving the prior pass's wrong row standing and superseding it is not merely acceptable, it is what
`ARTIFACT.md` `## Re-pass sections` requires — *"The artifact reads as a linear pass / review / pass
/ review sequence; never edit prior entries."* Rewriting it would have destroyed the evidence that a
stated population failed to re-derive, which is the record this cycle exists to keep.

### DRY findings

- **No duplication introduced by this pass.** The spec's four rewrites and the companion's one
  bullet each state a fact once in the file that owns it. Measured rather than asserted: 8-gram
  overlap of each edited spec line against the whole companion is 0.070 / 0.034 / 0.027 / 0.048
  (`:9` / `:33` / `:98` / `:558`) on my instrument, controlled at **1.00** on a real companion
  sentence and **0.00** on an invented one. I inspected every shared gram: **all 41 are identifier
  tokens** — anchor slugs (`decision-8--override-validation-and-collision-behavior`), archived spec
  filenames, and the pin's symbol path
  (`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`).
  **Zero prose overlap. No deliberation was restored.**
  *Instrument note, not a finding:* the apply report records **0.000** on all four. My instrument
  does not strip code spans and link targets before graming, so it scores identifiers; theirs
  evidently does. The figures differ, the conclusion is identical, and I re-derived the conclusion
  by reading every shared gram rather than by trusting either number. A future reader comparing the
  two should know the difference is a definition, not a disagreement.
- **Existence challenge: raised, and it resolves in favour of keeping.** The candidate is the
  companion's `### The illustrative inspect_django_type output` subsection — the one section in this
  pass's diff whose entries sit under `## Non-Decision deliberation` rather than under a Decision,
  which strains `BUILD.md`'s rule that "an entry naming no decision cannot be looked up". Deleting it
  is the wrong fix and this pass applied the right one: the added bullet gives the subsection the
  Decision key it lacked, by heading and anchor. Nothing else in either file is an abstraction with
  one caller. No existence challenge is escalated.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**; `git diff --stat` on that path
reports nothing. `__all__` and the re-export list are unchanged. The slice touches no package source
at all — which is also what discharges the failability-proof obligation above. (`types/base.py` is
Slice 4's and is not modified in the tree as of this pass.)

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The slice modifies documentation, so this section applies and was performed end-to-end on the file
state this pass produced, not on the prior pass's.

- **Gates, all re-run by me after the last edit.**
  `check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` ->
  `OK: 44 terms` (exit 0); `check_citations.py` ->
  `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)` (exit 0);
  `check_trailing_commas.py --check` -> exit 0.
- **Citations.** **5** `#"substring"` citations in the spec (`:46`, `:71`, `:305`, `:507`, `:580`),
  each resolving **exactly once** raw *and* whitespace-flattened against its target. **0** in the
  companion. The tightened `#"if suppress_pk_annotation and field.name == pk_name:"` resolves once.
- **Anchors and links.** In-page anchors, link-def fragments and every def path disk-exists: `0
  broken` across both files, on a detector proved to fire in both directions. Ten canonical group
  headers present and in exact order in both. Within-group sort re-derived by hand — see L4.
- **Link-def block containment, proved against HEAD rather than asserted.** HEAD carries 96 defs, the
  working copy 113: **17 added, 0 removed, 0 retargeted.** Fourteen are Slice 1's rationale pointers
  (`rationale-d1`..`d12`, `rationale-risks`, `spec-029-rationale`); **exactly three are Slice 3's**
  (`check-citations`, `commands-imports`, `test-ci-governance`). That independently confirms this
  pass added no definition, which is what makes L4's pre-existing-inversion claim provable.
- **Structural invariants, measured against HEAD and on disk.** 25 slice-checklist boxes (all
  `- [ ]`, the shipped-spec convention), 18 Definition-of-done items, 12 Decisions — unchanged. All
  **12** Decision titles character-for-character identical between spec and companion, extracted and
  compared. The retired Decision 10 slug resolves in **neither** file; the new slug resolves in
  **both**.
- **Chronology, swept in BOTH polarities over the whole spec, not only the edited lines.** Negative
  vocabulary (`amendment`, `retract`, `retired`, `as of card`, `later card`, `no longer`, `used to`,
  `previously`, `superseded`, `revision histor`, `rev[0-9]`, `P[123].[0-9]`, `DONE-0[3-9][0-9]`,
  `spec-0[3-9][0-9]`, `0.0.1[0-9]`, `widened`, `formerly`): **not one hit falls on an edited line.**
  Every hit is pre-existing and legitimate — sibling `0.0.9` cards, a parity-table `0.0.10` status
  column, the deliberately-kept `spec-004` derivation-baseline pin, and two "before the migration"
  statements. Positive vocabulary on the four edited lines returns `later` / `still` describing
  **construction-flow ordering** ("their target validation runs later still, from
  `__init_subclass__`") and one pre-existing `already` in `:9`'s untouched spec-019 clause. **No
  chronology, retraction, amendment block, review-finding tag or post-029 card id was reintroduced.**
- **Maintainer decision D2 still holds after this pass:** `0.0.11` / `spec-037` / `DONE-037` occur
  **0** times in the spec and **3** times in the companion, which is exactly the split D2 ordered.
  C1's closure also survives: **0** occurrences of `scalar-only` / `scalar column(s) only` /
  `scalar-column-only` / `scalar field names` anywhere in the spec.
- **Byte arithmetic re-derived, and the companion's decomposes exactly.** On disk: spec **153,989**
  bytes / **717** lines; companion **75,807** / **458**. Against the prior review's independently
  measured close (153,191 / 717 and 75,296 / 457) that is **+798** and **+511**, matching the apply
  report. The companion's delta is not merely consistent, it **sums**: the new `:340` bullet is 515
  bytes + 1 newline = 516, less the 5 bytes the L2 label fix removed (`docs/`) = **+511 exactly** —
  which also proves nothing else in the companion changed. The spec's +798 lands on four in-place
  line rewrites with the line count unchanged at 717, and every added byte I read is a corrected
  claim: three restatements of the shipped validation shape and one attribution repair. Growth is
  not the finding; restored deliberation would have been, and the gram check above says there is
  none. HEAD is unchanged at 170,042, so the net against HEAD is 16,053.
- **No script-rendered doc, KANBAN, CHANGELOG, terms CSV or `.py` file is touched by this slice**, and
  no spec archival is performed. No obsolete "planned" wording in surfaces the slice updated.

### What looks solid

Every item was re-derived by this pass, not read off the report.

- **The M1 correction is true at source in all three sentences**, and the two facts it turns on are
  the ones that are easy to get backwards: the per-key-helper pattern **is** real for the sidecar
  keys (so the corrected text does not overshoot into denying it), and the target validator runs from
  `__init_subclass__` (so the corrected text does not under-claim by leaving it unlocated).
- **The apply pass corrected more than the review named and stopped where it should have.** M1's
  finding named one site; the pass found the population is three and left four correctly-stated sites
  alone. I checked the left-alone set specifically — `:69`, Decision 8, `:413`, `:571` — because
  over-correction is the failure mode a widened sweep invites, and none of them was disturbed.
- **The pass re-measured rather than inherited on every finding**, including L4, which was a finding
  about a *number* and where copying the reviewer's figures would have been the cheap move. Its table
  disagrees with the prior pass's row and agrees with mine, arrived at independently.
- **The gate corpus described at `:558` is accurate in substance, not just in attribution** —
  `tests/test_ci_governance.py` imports `SOURCE_TREES` from `check_citations` by design (`:37`, with
  the comment saying why) and unions it with `EXTRA_SOURCE_FILES` in `_sweep_corpus()`.
- **The L3 pointer chain is real in both directions** — the anchor resolves, and the named heading
  string exists verbatim at the target.
- **Nothing this pass wrote weakened anything the prior pass verified.** The five citations, the 12
  Decision titles, the zero broken anchors, the D2 constraint and C1's closure were all re-measured
  at the new file state and all still hold.

### Temp test verification

- Directory created: `docs/builder/temp-tests/slice-3-029/` — **no temp test was written.** Nothing
  in this pass is a behavior suspicion; every question was answerable by reading source or by a
  scratch instrument. All five instruments and their synthetic controls were written **outside the
  repository**, under the session scratchpad, along with the read-only `git show HEAD:<spec>` copy.
  No tracked file was produced.
- Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **The eleven `### Dispatched findings checklist` boxes are still `- [ ]`,** as this artifact's own
   planning discipline requires. Final verification owes the audit-and-tick, and **C10 / C11 need
   boxes the build plan's section C does not contain.** Open since pass 1, unchanged.
2. **`Escalated:` the terms CSV rows 44-45 remain the last surface saying "scalar-only."**
   `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`. Outside the maintainer's fence;
   belongs in `bld-final-029.md`'s `### Deferred work catalog`, not a re-loop. Resolution paths
   unchanged from pass 1: (a) catalog it, or (b) a one-line fence exception. I concur with (a).
3. **The two `.py` docstring defects are confirmed and owned by Slice 4**, which is running
   concurrently under the plan's declared partition. Not re-filed here. One cross-slice check the
   integration pass should make and no one else can: companion `:245` states that
   `_validate_nullability_override_targets`'s docstring "still lists the three per-name rules in the
   rev1 order" and routes it to the deferred catalog. **Slice 4 is fixing exactly that docstring**,
   so once Slice 4 lands, that parenthetical becomes false in the companion. It is the same
   cross-file class as C11 and no gate sees it.
4. **`:98`'s disposition is settled, and the rule is written down above** so a future pass inherits
   one precedent rather than two: the `## Current state` vintage licence covers dated observations of
   the pre-build repo, not predictions about the build. I ruled for Worker 1 against my predecessor.
   Worth carrying into the final gate's record, because the section will attract a stale-number sweep
   again and the rule is what tells that sweep which hits to leave alone (note 3 of the pass-1
   report).
5. **No gate validates a `path::Symbol` citation inside a `.md` file.** `check_citations.py` scans
   `.py` files and `KANBAN.md` only (`712 in 426 .py files, 77 in KANBAN.md`), so the spec's and
   companion's `path::Symbol` citations are checked by a reviewer or by nobody. Standing blind spot
   for the deferred catalog, not a defect of this slice. Open since pass 1.

### Review outcome

`review-accepted`.

**M1, L1, L2, L3 and L4 are each closed**, every one re-derived on an instrument I wrote and
controlled in both directions rather than on the apply report's readings. No High, Medium or Low
finding remains. The `:98` disagreement is ruled in Worker 1's favour with the governing rule stated
above, and that rule was tested against the rest of `## Current state` rather than only against the
site that prompted it — it opens no new population.

Two record-level observations are deliberately **not** filed as findings, and are recorded above so
the next reader can see they were examined: the 8-gram `0.000` does not re-derive on a
non-identifier-stripping instrument (the conclusion does, by reading every shared gram), and `:60`'s
parallel construction lets the `EXTRA_SOURCE_FILES` attribution be carried across a "plus" while
asserting nothing false. Neither blocks acceptance and neither is worth a third loop on a slice that
has already consumed two Worker 1 passes and a review.

The parallel-site class that produced M1 came up short three times in this cycle. This pass is the
first where re-deriving the population on a **second instrument sharing no vocabulary with the first**
did not grow it — which is the evidence I accepted the class as closed on, rather than the pass's
own account of its sweep.

---

## Final verification (Worker 1)

Fresh spawn. Worker 3 set `review-accepted` with no open findings, so this pass is the slice-local
final check, not a re-litigation. **Every figure below was re-measured on my own instrument**; where
an instrument could have read identically whether or not it measured anything, it was controlled
first. One control caught my own dead instrument, and the substantive audit found **one defect in
the shipped bytes** plus **one durable-record gap**. Both are fixed here and recorded under
`### Spec changes made (Worker 1 only)`.

### Scope obligations: the dismissals were recorded, not manufactured

- **Failability proofs: not applicable, and I confirmed the RECORD exists rather than writing a
  fourth.** `worker-1.md` `### Failability and fail-open checks` makes my duty confirming the record,
  and four passes carry it with its `BUILD.md` `### What needs a proof, and what does not` citation:
  the plan's `### Scope declarations`, Worker 3 pass 1's `### Scope obligations considered`, the
  apply pass's `### Scope declarations (re-confirmed, not re-manufactured)`, and Worker 3 pass 2's.
  No pass manufactured a proof for a prose edit. The slice introduces no boundary: `git diff` shows
  zero package-source bytes in Slice 3's ownership column, so there is nothing to mutate.
- **Fail-open shapes: none possible.** The diff contributes no executable line in either direction.
- **Hot-path budget `none`, floor-verification scope `none`** — both declared in the build plan
  preamble and carried unchanged by every pass. Two documentation files, no framework seam.
- **Coverage:** no `--cov*` flag was used in this pass. The one `pytest` run below took `--no-cov`.

### Gates, re-run by me rather than inherited

| Check | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | `OK: 44 terms` (exit 0) |
| `uv run python scripts/check_citations.py` | `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)` (exit 0) |
| `uv run python scripts/check_trailing_commas.py --check` | exit 0 |
| `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form --no-cov` | `1 passed` |

All four re-run again after my two edits; all four still green.

### Instruments, and the one of mine that died

**My anchor validator's first version was broken, and the control caught it — not the output.** Its
slug function stripped `_` along with the backticks, so 46 spec anchors and 26 companion anchors read
as broken. That is the *third* independent occurrence of this exact delimiter trap in this cycle
(Worker 1's pass-1 slugger, then mine), which is itself the finding: the trap is in the character
class, and every fresh author reaches for `[`*_~]`. `_` is a `\w` character and GitHub's slugger
keeps it. Corrected, the reading is `0 broken` in both files.

**Proved to fire, not merely proved to pass.** I mirrored both files into a scratch tree outside the
repo and injected two faults — a fabricated in-page anchor (`#decision-99--zzz-does-not-exist`) and a
fabricated link-def fragment (`../GLOSSARY.md#zzz-no-such-heading`). **Both were reported.** A
`broken=0` from a detector that has not been shown to fire is indistinguishable from a detector that
returns zero unconditionally.

Other instruments and their controls: citation resolver (raw **and** whitespace-flattened counts;
positive `def _validate_nullability_override_targets` → 1/1, negative `ZZZ_not_present_ZZZ` → 0/0);
link-def differ against a read-only `git show HEAD:<spec>` copy in scratch; used-but-undefined /
defined-but-unused reference scanner; and the two gram instruments below.

### Did Slice 3 deliver its contract? C1-C11 re-derived against SOURCE

The obligation is that the spec describes the code at HEAD. I checked the load-bearing divergences
against the source files, not against the artifact's account of them.

| # | Verdict recorded | What I re-derived at source |
|---|---|---|
| C1 | CORRECTED | `types/base.py:1544-1551` raises "nullability overrides apply to non-relation model fields only (scalar columns and file/image output objects)"; `converters.py:561` `file_effective_null = True if force_nullable is None else force_nullable`. Spec matches the shipped wording. **0** occurrences of `scalar-only` / `scalar column(s) only` / `scalar-column-only` / `scalar field names` / `applies to scalar` remain in the spec |
| C2 | CORRECTED | `base.py:1947` `annotations[field.name] = convert_field_output(`; `convert_field_output(field, type_name, *, force_nullable=None, expose_filesystem_path=False)` at `converters.py:509-515`; `convert_scalar` keyword-only at `:362-367` with `effective_null = field.null if force_nullable is None else force_nullable` |
| C3 | CORRECTED | **5** `#"substring"` citations in the spec (`:46`, `:71`, `:305`, `:507`, `:580`), **4 distinct**, each resolving **exactly once** raw *and* flattened on a two-way-controlled resolver. **0** in the companion |
| C4 | CORRECTED | `_validate_meta` calls `_validate_filterset_class`/`_validate_orderset_class` (`:1277`/`:1278`); the two override keys shape-check through **inline** `_normalize_sequence_spec` (`:1300`/`:1304`); `_validate_nullability_override_targets` is called at `:672` inside `__init_subclass__` (`:566`), keyword-only, taking `relay_shaped: bool`, deriving `model._meta.pk.name` itself (`:1529`); loop order consumer-authored (`:1531`) → Relay-pk (`:1538`) → relation (`:1544`) |
| C5 | CORRECTED | CSV rows 18 / 44 / 45 of 45 lines carry the three symbols; all three `docs/GLOSSARY.md` headings exist (`:1260`, `:1356`, `:1824`); `OK: 44 terms` |
| C6 | CORRECTED | `optimizer/extension.py` has exactly three `extensions=[` occurrences — `:8` and `:873` singleton-factory, `:917` a prose comment — so the spec's retired claim was false at HEAD. `EXTRA_SOURCE_FILES` occurs **0** times in `scripts/check_citations.py` and is defined at `tests/test_ci_governance.py:420`; `SOURCE_TREES` is the 4-tuple the sentence claims (`check_citations.py:54-59`). The pin passes |
| C7 | CORRECTED | Six of the reconciled Test plan's names spot-checked across the two modules: each resolves **exactly once**, and each in the module the plan assigns it to |
| C8 | CORRECTED | `_imports.py` defines `import_or_command_error`, `_validate_absolute_module_path`, `import_module_symbol_or_command_error`, `import_string_or_command_error`; both public helpers call `_validate_absolute_module_path` **before** any import; `inspect_django_type.py:57-60` imports the latter two |
| C9 | CORRECTED | Census re-derives digit-for-digit on my own run: `test_extension.py` **67**, five package files **67+3+1+2+1 = 74**. Neither figure is stored in a completion claim; `## Current state`'s dated 48/41 stands |
| C10 | CORRECTED | **I ran the command.** `inspect_django_type BookType --schema config.schema` diffed against the spec's fenced block is **byte-identical** — all seven rows, column widths included. `ShelfType`'s pk row really is `Int!` / `SCALAR_MAP[BigAutoField]`, so the disclosed self-catch is fixed in the shipped bytes |
| C11 | CORRECTED | **0** `docs/spec-029-…` self-references remain in either file. The survivors are exactly the two documented exclusion classes (`spec-029b`, a hypothetical future spec; `spec-021`, the quoted KANBAN card-body name that is Decision 1's subject) plus companion `:370`'s rev-time answer inside the verbatim-moved Risks body |

**All eleven have a recorded verdict and all eleven hold.** The `### Dispatched findings checklist`
boxes are ticked accordingly (11 of 11), which is this pass's audit, not Worker 2's tick.

Structural invariants re-measured on disk and against HEAD: **25** slice-checklist boxes (all
`- [ ]`, the shipped-spec convention), **18** Definition-of-done items, **12** Decisions, and all
**12** Decision titles character-for-character identical between the two files (extracted and
`diff`ed — `IDENTICAL`). Link-def containment against HEAD: **96 → 113, 17 added, 0 removed, 0
retargeted**, of which 14 are Slice 1's `rationale-d*` / `rationale-risks` / `spec-029-rationale`
pointers and exactly **3** are Slice 3's. Staged-anchor sweep for `TODO(spec-029` / `TODO-*-029`:
**no live anchor** — every hit is prose *about* the scaffold, matching Slices 1 and 2's sweeps.

### The one defect: `:197` still stated the claim C7 retired

**Found, and it is the failure mode this pass exists to be the last line against.** The spec quotes
one contract sentence in two places. Decision 4 at `:305` states it as *"every selected field, with
its resolved GraphQL type and nullability, in selection order."* The `## User-facing API`
illustrative-output intro at `:197` stated it as *"every selected field, with its resolved GraphQL
type and nullability **read from `origin.__annotations__`**"* — which is verbatim the claim the
companion at `:156` formally records as one Decision 4 **may no longer make** ("that
`origin.__annotations__` is the single source of truth for every field's resolved type").

It is false at HEAD in the strongest available way: the illustrative block `:197` introduces carries
an `id  GlobalID!  relay.Node id` row that is sourced from the interface **because the pk is absent
from `origin.__annotations__`**, and the paragraph at `:214` says exactly that, sixteen lines below
the sentence claiming otherwise. Decision 4's corrected `:300`-`:303` spell out the four-way
dispatch. `## User-facing API` carries no vintage framing, so it reads as current contract.

Both spellings pre-date this cycle (`git show HEAD:` finds each once), so this is not an edit Slice 3
made wrongly — it is a **parallel site C7's population sweep did not reach**, the sixth instance of
that class in this cycle. C7 was swept on Decision 4 / DoD / Test-plan vocabulary; the surviving site
is a parenthetical in a *different section* that happens to quote the same contract string.

**Population enumerated on three disjoint vocabularies before editing**, so the fix is not one more
site-shaped repair: `every selected field` (3 hits — `:65` makes no read-source claim, `:197`, `:305`),
`single source of truth` (2 hits, both companion, both the retraction record), and the structural
`the contract is "…"` quoted-string sweep (exactly 2 hits — `:197` and `:305`). **The population is
one site.** Corrected to `:305`'s already-accepted wording, so the two spellings of the quoted
contract are now identical. −14 bytes, no line-count change, arithmetic exact
(`" read from \`origin.__annotations__\`"` = 35 bytes out, `", in selection order."` = 21 in).

### The `:98` precedent: the ruling holds, its test was under-enumerated, and it now has a durable home

**The rule is right and I am not re-opening it.** Worker 3 ruled that `## Current state`'s vintage
licence covers dated **observations** of the pre-build repo and not **predictions** about what the
build would do. I re-derived the two grounds: the spec's header frames the section as "the repo as of
this spec's authoring, before the build" and its own lead-in at `:95` as "a true description of the
repo as of this writing" — both about the repo, neither about the build.

**Its test held, but its enumeration did not.** Worker 3 tested the rule against `:101`, `:105` and
`:106`. Re-enumerating the section myself on a forward-looking-clause sweep rather than on Worker 3's
list, the forward-looking clauses are at **`:98`, `:101`, `:102`, `:103`, `:105`, `:106` — five
besides the corrected one, not three**, and Worker 3's `:106` description ("Slice 2 instead uses
Django's `import_string`") is actually `:102`'s text, so `:103` and the real `:106` were never
separately graded. **The conclusion survives the correction** — every one is a prediction the build
fulfilled, so none is falsified and none is owed an edit:

- `:101` — no `nullable_overrides` / `required_overrides` slot on `DjangoTypeDefinition`: **0**
  occurrences in `types/definition.py`; `FieldMeta` carries the read surface the bullet names.
- `:102` — `import_string` for dotted paths: `_imports.py:7` imports it, `:54` calls it.
- `:103` — "which Slice 1 corrects": `GOAL.md:161` now carries `extensions=[lambda: _optimizer]`.
- `:105` — the three glossary entries authored during implementation: all three headings exist.
- `:106` — the dedicated acceptance-only secondary type: `NullabilityOverrideBookType` exists with
  `primary = False`, `BookType` carries `primary = True`, and the root resolver is present.

**The ruling opens no new population — confirmed on a wider enumeration than the one that produced
it.** That is a stronger result than Worker 3 had, because two of the sites it rests on were not in
Worker 3's list.

**Routed, because it lived only in an artifact that closes with the build.** The rule governs *both*
dispositions — the census stands, the prediction goes — and the companion's
`### Documentation-coherence passes` bullet at `:359` recorded only the KEEP half. A future
stale-number sweep reading that bullet would learn why the census stays and not why `:98`'s clause
was rewritten, which is the asymmetry the rule exists to explain. One bullet added to that section
stating the rule once, with the fulfilled-prediction list as its evidence that it closes. That is the
durable home: the companion is tracked, committed, and keyed to this spec. The **generalization** to
`BUILD.md` / `worker-1.md` is outside the maintainer's fence for this cycle and is carried below.

### The 8-gram disagreement: confirmed on the grams, on a third instrument

The apply pass read `0.000`; Worker 3 read 0.027-0.070 on an instrument that does not strip code
spans and link targets. **Neither number is the evidence, so I re-derived the conclusion twice.**

1. **Whitespace-token longest-shared-run instrument** (a third definition — a *run*, not a ratio):
   **0** shared runs of ≥8 words between each of the four edited spec lines and the whole companion.
   Controlled at 1 run on a real companion sentence and 0 on an invented one.
2. **Worker 3's definition reproduced** (`[a-z0-9_]+` tokens): ratios 0.049 / 0.039 / 0.030 / 0.000,
   **16 distinct shared grams**. I printed and read **every one**. All 16 are identifier fragments —
   anchor slugs (`decision 8 override validation and collision behavior`, `decision 11 version bumps
   are owned by the joint 009 cut`), archived spec filenames (`docs specs spec 028 orders 0_0_8 md`),
   the terms-CSV filename, and one `[label][ref-id]` pair whose label and ref-id are the same words
   (`scalar field override semantics glossary scalar field override semantics`). **Zero prose grams.**

Corroborated on the negative vocabulary: the spec contains `Justification:` **0**,
`Alternatives considered` **0**, `Revision history` **0**, `Amendment`/`amendment` **0**,
`retracted` **0**, `superseded` **0**, `rev1`/`rev2`/`rev3` **0**, `as of card` **0**,
`later card` **0**. **No deliberation was restored.** The two instruments differ by a *definition*,
not by a disagreement, and the conclusion does not depend on which one you pick.

### The spec still reads as a clean current contract

Swept in **both** polarities over the whole file, not only the edited lines. Negative vocabulary: the
markers above, all zero. Post-029 card / version leakage: 8 hits, **every one legitimate** — the
sibling `DONE-030/031/032-0.0.9` cards that share this card's patch line, and two parity-table
`0.0.10` status cells. Maintainer decision **D2** holds exactly as ordered: `spec-037` **0** in the
spec / **3** in the companion, `0.0.11` **0** / **3**, `DONE-037` **0** / **2**. No chronology,
retraction, amendment block or review-finding tag survives anywhere in the spec, and my own two edits
introduced none (the spec edit removes a clause; the companion edit is in the file chronology belongs
in).

### DRY check against prior accepted slices

No new duplication. My spec edit **removes** a divergent second spelling of a sentence the file
already carried correctly elsewhere, which is a de-duplication. My companion edit states a rule that
existed nowhere durable; it names `## Decision 8`'s two retirement entries by content rather than
restating them, and it sits in the section that already discusses this exact question, so it is not a
second copy of a contract. The `[definition]` reference I first reached for turned out to be
**undefined in the companion**; rather than add a link definition I matched the file's own existing
convention for that symbol (a plain code span at `:139` and `:145`). Used-but-undefined and
defined-but-unused are `[]` / `[]` in both files after the edits.

### Byte counts, measured, and the deltas decompose

| File | Before this pass | After | Delta | Lines |
|---|---|---|---|---|
| `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | 153,989 | **153,975** | **−14** | 717 → 717 |
| `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` | 75,807 | **77,006** | **+1,199** | 458 → 459 |

Both "before" figures re-measured on disk at pass start and matching the re-review's independently
measured close exactly, so the records join with no unverified hop. The spec's −14 is the clause
swap, arithmetic above. The companion's +1,199 **sums**: the new `:360` bullet is 1,198 bytes + 1
newline, and nothing else in the file changed — which the one-line line-count rise independently
confirms. HEAD is unchanged at 170,042, so the net against HEAD is now **16,067**. The companion has
no HEAD figure: it does not exist at HEAD (`git cat-file -e` → absent), as every prior pass recorded.

### Concurrent activity, observed and not judged

`git status` is not a reading of this slice's diff. Attributing by the build plan's ownership table:
`docs/review/**` and `tests/mutations/test_operations.py` are an unrelated session's and were neither
read for judgement nor touched; Slice 2's eight `.py` files and `spec-004-…-rationale.md` are prior
slices'; **`django_strawberry_framework/types/base.py` is Slice 4's and its edits are already on disk**
(see the carry-forward below). I wrote no `.py` file and touched nothing outside my three paths.

### Summary

Slice 3 delivered its contract. All eleven divergences hold on independent re-derivation against
source — including the two the slice found itself — the C10 correction is byte-exact against a live
command run I made myself, the spec reads as a clean current contract in both sweep polarities, no
deliberation was restored, and the Decision-title lockstep the C1 rename put at risk holds at 12 of
12. One surviving instance of a retired claim was found at `:197` and fixed; the `:98` precedent was
verified, found to rest on an under-enumerated test whose conclusion survives a wider enumeration,
and given a durable home in the companion.

### Spec changes made (Worker 1 only)

| File / heading | Change | Reason |
|---|---|---|
| spec `## User-facing API`, illustrative-output intro (`:197`) | the quoted contract's tail `read from \`origin.__annotations__\`` → `, in selection order.`, matching Decision 4's already-corrected `:305` | Final verification found the one surviving instance of the claim C7 retired and companion `:156` records as un-makeable. It contradicted the illustrative block it introduces and the paragraph at `:214`. Population enumerated on three vocabularies first: one site |
| companion `## Non-Decision deliberation` → `### Documentation-coherence passes` (`:360`) | one bullet added stating the observation-vs-prediction rule that governs `## Current state`, with the five fulfilled predictions as evidence that it opens no further population | The rule Worker 3's pass-2 ruling established lived only in this artifact, which closes with the build; `:359` recorded only the half that keeps the census. Durable, tracked, keyed to the spec |

Neither edit changes a contract Worker 2 implemented against — Slice 3 has no Worker 2, and both
edits correct descriptions of already-shipped code.

### Notes for Worker 1 (spec reconciliation)

Carried to the integration pass and to `bld-final-029.md`. Nothing here was fixed in this pass.

1. **The docstring-falsification population is ONE passage, not two — and it is already false on
   disk.** The dispatch to this pass named two: `## Decision 8`'s "outside this cycle's editable
   surface … routed to the final gate's deferred catalog" parenthetical, and `:245`'s "still lists
   the three per-name rules in the rev1 order". **They are the same sentence.** Companion `:245`'s
   trailing parenthetical carries both clauses; there is no second passage. Enumerated on three
   disjoint vocabularies — defer/fence words (`deferred catalog`, `editable surface`, `out of fence`,
   `not fixed`, `unfixed`, `routed to`, `final gate`), artefact words (`docstring`, `source-comment`,
   `comment defect`), and a currency-negation sweep (`still`, `not yet`, `remains`, `has not`,
   `left`, `survives`) intersected with source/comment/cycle/fence terms. **All three land on
   companion `:245` and nothing else.** No spec site exists, and no passage anywhere asserts the
   `_selected_meta_targets` caller-count defect is unfixed — companion `:244` already names
   `Meta.filesystem_path_fields` as "the third caller", so that half was never wrong in these files.
   **So the integration pass owes one sentence, not a two-site sweep** — but it should re-derive the
   population itself rather than take this count, for the reason this note exists.
2. **`Status` reality the dispatch did not have: Slice 4's bytes are ALREADY in the working tree.**
   `git diff -- django_strawberry_framework/types/base.py` shows 13 insertions / 10 deletions, and
   the docstring at `types/base.py:1486` now reads "Check order: unknown -> excluded ->
   consumer-authored -> Relay-pk -> relation" — the rev1 order is gone. `_selected_meta_targets`'s
   docstring now says "shared by every `Meta` key whose value is a set of field names". Slice 4's
   artifact is `Status: built`, not `final-accepted`. **All three clauses of `:245`'s parenthetical
   are therefore false on disk right now**, not "once Slice 4 lands". I did not correct it: the build
   plan's `## Cross-slice conflict created by Slice 4` assigns the correction to the integration pass
   precisely so it lands after Slice 4 is accepted, and a `revision-needed` on Slice 4 could still
   move the wording. But the integration pass must not treat this as a future condition to check —
   it is a present falsehood to repair, and the only thing gating it is Slice 4's acceptance.
3. **Terms CSV rows 44-45 — outside the fence, and they carry MORE than the hand-down says.**
   `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv`. Enumerated rather than restated:
   row 44 carries C1's retired scope claim **twice** ("forcing a **scalar** field nullable" and
   "**scalar-only**, validated at type creation") **and** describes the apply mechanism as "via the
   `convert_scalar` `force_nullable` tri-state", which is true for scalar columns but is the
   narrow half of what C2 widened; row 45 carries the scope claim once ("forcing a **scalar** field
   required"). `docs/GLOSSARY.md` is already correct on both headings, so the CSV is the only stale
   surface left anywhere. Deferred catalog, not a re-loop — the maintainer's fence is explicit.
4. **No gate validates a `path::Symbol` citation inside a `.md`.** `check_citations.py` reports
   `712 in 426 .py files, 77 in KANBAN.md`; `docs/` is out of scope by design. The spec's and
   companion's `path::Symbol` citations are checked by a reviewer or by nobody, and a symbol rename
   breaks them silently exactly as the `#"substring"` class does. Standing blind spot for the
   deferred catalog, open since review pass 1.
5. **The `## Current state` observation-vs-prediction rule now has a durable home in the companion
   (`:360`), but its GENERALIZATION is unrouted.** The rule is not spec-029-specific: any spec with a
   vintage-framed section will meet it. `BUILD.md` / `worker-1.md` are outside this cycle's fence and
   are corpus-ratchet-bound, so this is a **maintainer proposal**, not a worker edit: it would have
   to name the bytes it retires. Recorded so the next cycle does not re-derive it from scratch.
6. **The build plan's section C under-describes this slice and I may not edit it.** It lists nine
   divergences; the slice discharged eleven (C10 and C11 were this slice's own finds) and this pass
   added a twelfth site under C7. `build-029-consumer_dx_cleanup-0_0_9.md` is Worker 0's file. The
   artifact's checklist is the complete record.
7. **The underscore-stripping slugger trap has now killed three instruments in this cycle**, mine
   included, and each author reached for the same `[`*_~]` character class independently. It is not a
   lesson that transmits by being written in an artifact — it transmits by a positive control on an
   underscore-bearing anchor. Worth one line wherever anchor-checking is described.

### Final status

`Status: final-accepted`.

All eleven divergence boxes audited and ticked, every load-bearing claim re-derived at source rather
than read off the report, all four gates re-run green after the last edit, and the two defects this
pass found are fixed in the shipped bytes and recorded above. Worker 0 may mark the slice's checkbox.
