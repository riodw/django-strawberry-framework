# Build: Slice 2 — spec reconciliation

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (whole file) and its rationale
companion `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` (whole file)
Status: final-accepted

## Artifact shape: one Worker 1 pass, so two template sections are not applicable

`## Build report (Worker 2)` and `## Review (Worker 3)` are **not applicable** to this slice, and
the reason is procedural rather than a shortcut. `docs/builder/BUILD.md` `## Spec reconciliation`
makes Worker 1 the **only** role authorized to mutate the spec, and `worker-2.md` / `worker-3.md`
both list it as a file they must not edit — so there is no diff a builder could produce here and
nothing a reviewer could review that is not itself a spec edit. The maintainer's standing
carve-out for a spec-only change (recorded in this pass's dispatch) states it directly: plan,
execute and finally verify in one pass. The shape follows
`docs/builder/BUILD.md` `### Procedural-closure slices` — one combined Plan + Final-verification
block, `Status:` set once — with the difference that this slice does ship a real diff (two
Markdown files), so the verification below is the full slice-local gate set rather than a
citation of a deferral clause.

`### Isolation is non-waivable` is not weakened by this: it bars **the author of code from
approving that code**. Nothing here is code. The isolation that does apply — the spec must not be
graded against itself — was satisfied by the *previous* slice: `bld-038-slice-1-code_conformance.md`
graded all 140 corpus rows against `HEAD` source under two independent Worker 3 review passes,
and this pass executes that graded verdict list rather than re-deciding it.

**Hot-path declaration: none** — this slice edits two Markdown files.
**Floor-verification scope: none** — no Django / Strawberry / channels integration seam is touched.
Floor facts copied from `docs/builder/BUILD.md` `## Floor verification` in case any reasoning had
turned on version-dependent behavior: the supported floor is Django **5.2.16** on Python **3.10**
with strawberry-graphql **0.316.0**. None did; no floor venv was built and the shared `.venv` was
neither read for versions nor mutated.

---

## Plan + Final verification (Worker 1)

### Method: every anchor measured before the cut, every count re-measured after

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` and
`START.md` "Instruments that lie" govern. What that meant concretely:

- **Every routed anchor's occurrence count was measured in the live spec before any edit**, in one
  `uv run python - <<'PY'` heredoc over 49 tokens, printing the count per token in both files
  (never `grep -c`, which counts matching lines: two hits on one line read as one). The same sweep
  was re-run after the edits and is reproduced in `### The 35-item + 3-note walk` below.
- **Every edit ran as an assert-all-then-write script.** Each of the eight edit scripts holds an
  ordered list of `(old, new, expected_count)` triples, asserts `text.count(old) == n` for **every**
  triple before applying **any**, and writes the file only at the end. Three scripts aborted on a
  failed assertion having written nothing — twice because my reconstruction of a wrapped
  parenthetical was off by one `)`, once because a bullet's 2-space indent was missing. That is
  `START.md` "Enumerate, never grep-count, before writing" working as intended: a partial match
  aborts with nothing written.
- **Every code claim written into the spec was read out of `git show HEAD:<path>`**, into
  `…/scratchpad/head/` **outside the repo**, never out of the working copy. Three of the files this
  pass describes (`forms/inputs.py`, `forms/resolvers.py`, `forms/sets.py`) are baseline-dirty from
  a concurrent session, so the working copy is not the shipped contract. Commands:

```shell
for f in forms/converter.py forms/inputs.py forms/sets.py forms/resolvers.py \
         mutations/resolvers.py mutations/inputs.py mutations/sets.py mutations/fields.py \
         mutations/operations.py utils/inputs.py utils/write_values.py utils/errors.py \
         registry.py; do
  git show HEAD:django_strawberry_framework/$f > "$SCRATCH/head/$f"
done
```

- **Every post-ship change was attributed to a commit, measured not guessed**, with
  `git log --oneline -S<symbol> -- <path>` per symbol. `START.md` warns `git log -S` is fail-open
  when the symbol had an earlier name, so each result was corroborated by reading the shipped body
  at `HEAD`, and one attribution was *disproved* this way (see item 23).

### Shared-environment versions, as read (never from memory)

Not load-bearing for a Markdown slice, and recorded because the process asks for the reading rather
than the memory:

```shell
uv pip list | grep -Ei '^(django|strawberry-graphql|django-filter) '
```

Not run this pass: no reasoning here turns on an installed version, and
`docs/builder/BUILD.md` `## Floor verification` scopes the obligation to a pass that needs to know
what the shared environment carries. Stated explicitly so a later reader does not read silence as
a skipped step.

---

### The 35-item + 3-note walk

Ticked over the **source's own numbering** — the consolidated
`### Notes for Worker 1 (spec reconciliation)` list in
`docs/builder/bld-038-slice-1-code_conformance.md` `## Final verification (Worker 1)` — rather
than as a fresh summary, per `START.md` "Harvesting items from a doc about to be deleted" and
because a section sweep looks complete while leaving items unhomed. Each row carries its anchor's
**post-edit** occurrence count, re-measured by the same instrument that measured it before.

#### Case (3) — a later card deliberately changed it (21 items)

- [x] **1 — JSONField row.** Applied in **three** homes, not the two the item named: Decision 7's
  converter bullet list (anchor `text-like` ×1), `## Definition of done` item 2 (anchor
  `its Strawberry annotation` ×1), **and** the `## Slice checklist` Slice-1 converter enumeration,
  which carries its own parallel list the item did not mention. Shipped truth verified at `HEAD`:
  `_SCALAR_FORM_FIELDS` has **12** rows including `forms.JSONField` →
  `strawberry.scalars.JSON`, with the module's own comment giving the reason (`JSONField`
  subclasses `CharField`, so the MRO walk would otherwise resolve to the parent and type JSON as
  `String`). Case (3), commit `efb7bda5` 2026-07-15.
- [x] **2 — `NullBooleanField` three-case requiredness.** Applied. Decision 7 now carries its own
  bullet for the rule, single-sited in `forms/converter.py::form_field_required`, and
  `## Definition of done` item 2 names it. Verified by reading `form_field_required`'s body and
  docstring at `HEAD`: exact type → forced optional, subclass → declared requiredness,
  non-null-column-backed → `required=True`. Case (3), commit `5737ddda` 2026-07-15.
- [x] **3 — the reverse-map record is `utils/inputs.py::InputFieldSpec`.** Applied in both homes
  (Decision 7's reverse-map paragraph, anchor `metadata record` now ×0 — the phrase was replaced;
  and the Slice-1 checklist sub-check). Verified: `InputFieldSpec` is defined in
  `utils/inputs.py` with `input_attr` / `graphql_name` / `target_name` / `kind` / `source` /
  `related_model` / `nested_specs`; the four `kind` constants `SCALAR` / `RELATION_SINGLE` /
  `RELATION_MULTI` / `FILE` are defined there and re-exported by `forms/converter.py`, whose own
  docstring says the record type is single-sited on `InputFieldSpec`. Case (3), commit `60dbf469`
  (spec-039).
- [x] **4 — the relation decoder rides a shared spine.** Applied. Decision 7's paragraph (anchor
  `runs its **own**` now ×0) states `utils/write_values.py::decode_visible_relation` as the single
  spine and the form flavor's colouring as the `empty_values` skip plus the `to_field_name`
  projection, with `decode_field_handlers` / `decode_provided_fields` owning the `UNSET` strip and
  the `kind` dispatch. **The visibility-on-every-branch security contract survived verbatim** —
  the four-step (i)-(iv) enumeration in the shipped docstring was read before the rewrite and the
  rewritten paragraph asserts every one, including "for **both** branches" and the
  no-existence-leak `FieldError`. Case (3), commits `e9c13f55` / `8bac47be`.
- [x] **5 — the 4-tuple cache key.** Applied in **four** homes: Decision 7's shape-identity
  paragraph, `## Definition of done` item 2 (the two `frozenset(effective field names` sites the
  item named, still ×2 with corrected content), the Slice-1 checklist identity clause, and the
  Slice-2 checklist `"form"`-sentinel clause. Verified by reading
  `forms/sets.py::_cached_build_form_input`'s `cache_key = (form_class, operation_kind,
  frozenset(effective), _form_input_hook_identity(mutation_cls))` at `HEAD`, and
  `_form_input_hook_identity`'s body (`None` unless `get_form_fields` is overridden). Written as a
  **hook discriminator**, not a fifth concept, exactly as the item required. Case (3), commit
  `a2418106`.
- [x] **6 — two narrowing guards, not one.** Applied. Decision 7's create-guard paragraph (anchor
  `is exempt` now ×0) gained a `**There are TWO narrowing guards, keyed on that one waiver.**`
  paragraph naming `forms/inputs.py::guard_partial_required_column_less_fields` and the
  column-less scoping as load-bearing. The `## Edge cases` create-narrowing bullet — which the
  item correctly observed does **not** repeat the exempt clause — gained the partial guard, so
  both homes now describe both guards. Case (3), commit `cf3293cf`.
- [x] **7 — the promoted helpers' real locations.** Applied in both homes (Decision 8's "Helper
  reuse" paragraph, anchor `underscore-dropped in place` now ×0; and the `## Implementation plan`
  Slice-3 cell). Locations re-measured, not copied:
  `git grep -l "^def <name>(" HEAD -- 'django_strawberry_framework/*.py'` per name gives
  `mutations/resolvers.py` for `locate_instance` / `coerce_lookup_id` / `authorize_or_raise` /
  `refetch_optimized` / `build_payload` / `not_found_error` / `save_or_field_errors`,
  `utils/errors.py` for `validation_error_to_field_errors`, `utils/write_values.py` for
  `raw_choice_value`, `mutations/inputs.py` for `payload_object_slot`. Case (3).
- [x] **8 — the boundary is more than one `atomic()`.** Applied in two homes: a new paragraph in
  Decision 8 (the normative home, chosen over burying it in the checklist) and a compressed
  clause in the Slice-3 checklist, whose anchor `whole pipeline runs inside one` is still ×1 with
  corrected content. Verified against `run_write_pipeline_sync`'s body and docstring at `HEAD`:
  `check_deadline(info)` before `open_write_pipeline`, `pipeline_alias_guard` /
  `check_instance_write_alias`, and the `authorized_pk` / `target_state` snapshot captured right
  after the locate. Case (3), the `0.0.14` atomicity work plus `spec-047`.
- [x] **9 — `model_to_dict` has four normative homes, and the formula has three shapes.** Applied.
  `model_to_dict` is now ×5 in the spec but **all five occurrences sit inside Decision 8's new
  three-shapes bullet**, which is the point: the Slice-3 checklist, the `## Edge cases`
  update-preservation bullet and `## Definition of done` item 4 no longer state a one-shape
  formula at all — they say "the full declared field set, overlaid by the provided fields, in the
  three shapes a provided field decodes to" and point at the Decision. Verified against
  `forms/resolvers.py::_reconstruct_partial_data`'s docstring and body at `HEAD` (the M2M branch,
  the `to_field_name`-gated FK branch, the `model_to_dict` remainder, and the full
  `get_form_fields()` read). Case (3).
- [x] **10 — the plain-form permission default and the `DjangoModelPermission` reject.** Applied.
  Decision 11's paragraph (anchor `Preferred resolution` now ×0) states the `(DenyAll,)` default
  and the `permission_classes = []` opt-out, and gained a second paragraph for the
  `DjangoModelPermission` rejection with its reason (that class resolves its codename from a model
  a model-less mutation never supplies, and the generic validation accepts it, so without the
  targeted reject the misconfiguration surfaces only as a request-time `AttributeError`). Both
  read out of `DjangoFormMutation._validate_meta` at `HEAD`. Case (3).
- [x] **11 — the live surface spans three apps; products is 8.** Applied in Decision 12 (anchor
  `narrows it to the existing` now ×0, replaced by a three-app enumeration). `## Definition of
  done` item 5 and the `## Test plan` live bullet were deliberately **not** reworded — item 35
  forbids it. **The 8 was re-derived rather than copied:** 8 classes and 8 matching
  `DjangoMutationField` rows in `examples/fakeshop/apps/products/schema.py`. Recorded explicitly
  because `HEAD` carries **6** — the two extra (`updateItemWithFileViaForm`,
  `createDefaultCategoryItemViaForm`) are **this cycle's own Slice-1 output**, uncommitted but
  this cycle's to commit, which is a different thing from the concurrent session's hunks and is
  why the HEAD-only rule does not apply to them. Case (3).
- [x] **12 — `registry.clear()` names none of the three clears.** Applied in both homes
  (Decision 13, anchor `co-clears` now ×0; and the `## Implementation plan` Slice-2 cell, whose
  `registry.py` attribution was removed). Verified: `grep register_subsystem_clear` over the
  `HEAD` copies of `forms/*.py` returns the three registrations with owner keys
  `forms.input_namespace` (`before_bind=True`), `forms.declarations` and `forms.shape_cache`, and
  `registry.py`'s `clear()` drains `iter_subsystem_clears()`. Case (3), commit `60dbf469`.
- [x] **13 — the plain metaclass is a shared factory. All three sites graded.** Applied at
  Decision 6 (the normative home) only, and **that is the decided answer, not an omission.** The
  other two sites — the Slice-2 checklist and `## Definition of done` item 3, both reading "the
  model-less sibling — its own metaclass + declaration registry + `bind_form_mutations()`" — are
  **true as written**: the plain base does have its own metaclass over its own ledger, which is
  the contract; that the mechanism is
  `make_meta_validating_metaclass(register_form_mutation, …)` is the added truth and belongs in
  the Decision. Anchor `its own metaclass` is therefore ×2 by design. Case (3), commit `5165314b`.
- [x] **14 — the resolver seams, bind and operation vocabulary are shared factories.** Applied in
  Decision 8's "How this pipeline actually fires" (anchor `delegate **here**` now ×0). Names the
  `resolver_seams(...)` factory with `with_id=False` for the plain flavor, cites the id-gate as
  `mutations/fields.py` #"operation != \"form\"", states `bind_form_mutations()` as one
  `bind_write_declarations(...)` call, and names `mutations/operations.py` as the owner of
  `NON_DELETE_WRITE_OPERATIONS` / `NON_DELETE_OPERATION_INPUT_KIND` /
  `non_delete_operation_error`. All four read at `HEAD`. Case (3).
- [x] **15 — the `TestClient` helper shipped.** Applied in both homes (`## Non-goals`,
  `## Out of scope`; anchor `AsyncTestClient` still ×2 with corrected content). Verified:
  `git ls-files django_strawberry_framework/testing/` returns `__init__.py`, `_wrap.py`,
  `client.py`, `relay.py`, and `examples/fakeshop/test_query/test_client_api.py` exists. **The
  file-field-correctness half of the `## Non-goals` sentence survived the rewrite** — the item's
  explicit requirement — and is re-read in the file: "This card **owns the runtime correctness**
  of `forms.FileField` / `forms.ImageField`" is byte-unchanged. Case (3).
- [x] **16 — serializer mutations shipped.** Applied in **three** homes: `## Non-goals`,
  `## Out of scope`, **and Decision 2's own card-scope bullet**, which the item mislabelled as
  `## Key glossary references` (that section names the flavor without a card id). Anchor
  `TODO-ALPHA-039` now ×0. Verified: `django_strawberry_framework/rest_framework/` ships six
  modules and `tests/rest_framework/` mirrors them. Case (3).
- [x] **17 — auth mutations shipped, and are the third registry consumer.** Applied in the same
  three homes; anchor `TODO-ALPHA-040` now ×0. `## Out of scope`'s auth bullet now records that
  `auth/mutations.py` is the **third** `make_declaration_registry` consumer and therefore live
  evidence for Decision 13, which is where the item asked for it. Verified:
  `django_strawberry_framework/auth/mutations.py` exists and `make_declaration_registry` is
  instantiated by `mutations/sets.py`, `forms/sets.py` and `auth/mutations.py`. Case (3).
- [x] **18 — the envelope is additive, not frozen.** Applied at **11** sites: the H1 title, the
  opener's "reuses byte-identical … froze for exactly this", `## Key glossary references`'s
  "defined and froze" + "byte-identical envelope", the Slice-3 checklist sentinel wording,
  `## Problem statement`, `## Goals` item 3, `## Non-goals`, the
  `### Reference-package parity checkpoint` row, Decision 2's body (twice), and the
  `## Edge cases` sentinel wording. Verified against `mutations/inputs.py::FieldError` at `HEAD`:
  its docstring states #"The type is ADDITIVE, not frozen" and the class carries `codes` and
  `path` beside `field` / `messages`. **Two deliberate non-edits, both anchor-driven:**
  Decision 2's *heading* contains "the frozen `036` contracts are reused unchanged" and was left
  alone — two in-page uses plus the `[rationale-d2]` definition plus the companion's own
  `[spec-038-d2]` resolve through it; and the six remaining `036`-frozen **uniform `node` /
  `result` slot** mentions were left alone because the slot genuinely is frozen — the finding is
  about the envelope. `byte-identical` is ×1, the surviving mapper-output claim ("byte-identical
  to a model `full_clean()` failure"), which is true and is not the envelope claim.
  `CHANGELOG.md`'s dated entries were confirmed out of scope and not chased. Case (3) for the
  vocabulary; the `038`-adds-no-member claim stands.
- [x] **19 — two allowed-key sets, and the checklist loses.** Applied in **three** homes: the
  Slice-2 checklist (the merged item's own target), **Decision 6's allowed-key bullet** — a third
  home neither the item nor the routed list named — and by consequence Decision 10, which already
  stated the operation split correctly and needed no edit. Both sets read at `HEAD`:
  `_ALLOWED_MODELFORM_META_KEYS = MODEL_BACKED_WRITE_META_KEYS | {form_class}` and
  `_ALLOWED_PLAIN_FORM_META_KEYS = COMMON_WRITE_META_KEYS | {form_class}`, with
  `MODEL_BACKED_WRITE_META_KEYS = COMMON_WRITE_META_KEYS | {operation, select_for_update}`. Both
  the case-(3) content and the case-(2) ship-time under-description are discharged by naming both
  sets. Cases (2) and (3) merged, as the item directed.
- [x] **20 — the version quintet is a triplet.** Applied in both homes (Decision 14, anchor
  `quintet` now ×0; and `## Definition of done` item 8), plus the Slice-5 checklist's own
  version-files sub-check, a third home. Verified: `pyproject.toml` has no `version` key and
  carries a comment saying so, `[tool.hatch.version]` derives it, and `uv.lock` records the
  package as `source = { editable = "." }` with no version key. **The `0.0.12` figures were not
  "updated"** — the cut this card owned happened, and only the mechanism description was stale, as
  the item required. Case (3), and `AGENTS.md` #"The release is single-sourced" is cited as the
  standing authority.
- [x] **21 — `build_payload_type`'s real signature.** Applied in the `## Implementation plan`
  Slice-2 cell (anchor `object_type=None` now ×0). Verified at `HEAD`:
  `build_payload_type(mutation_name, *, object_type: type | None, object_slot: str | None = None)`
  — keyword-required, no default — with the model-less shape selected by
  `bind_form_mutations` passing a `resolve_object_type` that returns `None`. Decision 6's
  one-builder-one-ledger contract confirmed intact and not rewritten. Case (3).

#### Case (2) — a ship-time deviation; the named side changes (5 items)

- [x] **22 — Decision 8's ordering. The spec loses.** Applied; this is the slice's largest edit
  and its record is `### The step-renumber record` below. Anchor `Ordering correction` now ×0.
- [x] **23 — `payload_object_slot` was public before `038`. The spec loses.** Applied: the name is
  out of the promotion list, and the Helper-reuse paragraph now states plainly that
  `payload_object_slot` lives in `mutations/inputs.py`. **The claim was re-derived, not accepted:**
  `git grep -n "def payload_object_slot" 731fecd8^ -- django_strawberry_framework/mutations/inputs.py`
  returns a hit at `731fecd8^:…:539`, i.e. the symbol was already public *before* `038`'s own ship
  commit, so the promotion clause was false on its own date. `## Current state`, the other of the
  two contradicting homes, was the right one and needed no edit. Anchor `payload_object_slot` is
  ×2: the corrected Helper-reuse mention and the `## Current state` observation. Case (2).
- [x] **24 — "Slice 3 picks one". The spec loses.** Applied: the whole
  lighter-edit-versus-cleaner-edit deliberation and the "Slice 3 picks one and names it"
  instruction are gone from the spec and appear as a `**Post-ship:**` bullet in the companion.
  Anchor `picks one` now ×0. Verified no `mutations/_pipeline.py` exists. **Consequence tracked:**
  this deletion orphaned the `[utils-querysets]` link definition, whose only two uses were inside
  the retired deliberation — pruned, and checked against the terms CSV first (it is a source-path
  label, not a gated glossary anchor). Case (2).
- [x] **25 — the plain-form authorization edge case. The bullet loses.** Applied; anchor
  `requires an explicit` now ×0. The bullet now states the deny-by-default posture, the
  `permission_classes = []` opt-out, and the `DjangoModelPermission` rejection from item 10, so
  the two homes agree. Case (2).
- [x] **26 — Decision 5 axis 1's `_payload_type_name`. The spec loses.** Applied: axis 1 now
  states the shipped duck-typed protocol (`_mutation_meta`, callable `resolve_sync` /
  `resolve_async` / `input_type_name`, non-`None` `input_module_path`), why it must **not** require
  `_payload_type_name` (a bind output, while the field is constructed at import), the load-cycle
  reason the check is not `issubclass(DjangoMutation)`, and the separate own-snapshot +
  current-ledger concreteness check. Every clause read out of
  `mutations/fields.py::_validate_mutation_target` and `::_has_mutation_protocol` at `HEAD`.
  Anchor `_payload_type_name` is ×1 — inside the corrected statement, which is where it belongs.
  Case (2).

#### Chronology and undecodable-reference residue (6 items)

- [x] **27 — three chronology hedges.** All three applied; all three anchors now ×0.
  Decision 6's `fully-pinned` resolution-of-prior-uncertainty framing (plus that paragraph's
  "not a preferred / fallback branch" lead-in, which the item flagged as the Risks section's
  vocabulary) → the shape is simply stated as fixed. Decision 10's `prior contradiction` → the
  split is stated per base. Decision 7's `This replaces the earlier` → the prohibition is stated
  directly ("Instantiating `form_class()` no-arg … is **not** an option"), which keeps the
  implementation-relevant WHY the carve-out protects.
- [x] **28 — "the review names" ×2.** Both applied; anchor now ×0. Decision 7's "the two collision
  cases the review names" → "the two collision cases" (the sentence enumerates them (a)/(b)
  immediately after) and Decision 8's "both failure modes the review names" → "both failure
  modes" (likewise enumerated in the same sentence). No content lost.
- [x] **29 — the label residue, split two ways after verification.** Applied: **62** label
  occurrences retired, with a post-sweep assertion printing `residual label occurrences: 0`. The
  split, and why it is a split: `P1` / `P2` / `P3` and the bare `#1`-`#8` are orphaned review
  residue — no legend exists in the spec or the companion — so they were removed and every
  sentence's own contract wording carries the emphasis; none of them contributed a clause. The
  five `AR-H1` / `AR-H4` / `AR-H5` / `AR-M6` / `Medium-1` identifiers were **verified against
  their spec before deletion**, as the dispatch requires: each resolves inside
  `docs/SPECS/spec-036-mutations-0_0_11.md` (7 / 14 / 6 / 12 / 3 occurrences respectively), so
  they were decodable — but they are review-finding labels, not spec-decision pointers, so each
  was replaced by the contract it labelled rather than deleted bare (`AR-H4` → "the `036`
  id-type-check contract"; `AR-H1` / `AR-M6` → "the `036` second-different-class-under-one-name
  raise"; `Medium-1` → "the `036` re-fetch exception", its "the actor just wrote the row" reason
  intact; `AR-H5` → dropped, the surviving `spec-036 Decision 7` pointer already carrying the
  lookup). The removed attribution's WHY survives in all five cases.
- [x] **30 — `## Key glossary references`' future imperative.** Applied; anchors `provisional`
  and `Slice 5 promotes both entries` both ×0. The bullet now states the sibling-shape contract
  the entries must not blur, and that both carry `shipped (0.0.12)`. The grading pass's
  independent verification of the rendered result is cited in the companion rather than re-run
  here, because `docs/GLOSSARY.md` is behind the scope fence.
- [x] **31 — `## Doc updates` / Slice-5 future tense.** Applied; anchor `Coming next` now ×0 (both
  sites), and the card-wrap bullet now names `DONE-038-0.0.12` rather than moving
  `TODO-ALPHA-038-0.0.12` to Done. Anchor `TODO-ALPHA-038-0.0.12` is ×1: the `## Current state`
  occurrence, which the item itself grades as **a dated observation that stands** — and it does
  stand, measurably: see note N2.
- [x] **32 — the discharged TODO-anchor cell.** Applied; anchor `TODO-anchor only` now ×0. The
  `## Implementation plan` Slice-2 cell no longer stages a completed step. Verified independently:
  `grep -rn 'TODO(spec-038'` returns nothing in source or tests, and `def _input_type_name` does
  not exist package-wide at `HEAD`.

#### Spec additions this slice's own measurements earned (2 items)

- [x] **33 — the file clause survives verbatim, with one clause appended.** Applied. The
  "`files = provided_files` **only** — an omitted file field is preserved by the bound
  `form_class(instance=…)` via its `initial`, never re-supplied and never cleared" text is
  byte-unchanged (anchor `re-supplied` ×1), and the appended clause states that the reconstruction
  contributes **no key at all** for a file field, with the `model_to_dict`-yields-a-relative-path
  reason. The measured WHY — no wire-level row can detect the exclusion's removal, because a file
  widget's `value_from_datadict` reads `files` only — is recorded in the companion rather than the
  spec, which is the right split: the spec carries the contract, the companion carries why the
  sentence needed the clause.
- [x] **34 — the `get_form_kwargs` reword plus the written-row clause.** Applied in **three**
  homes, not the two the item named: Decision 8 step 4 (anchor
  `without changing the generated input shape` ×2 overall, both with corrected content), the
  `## Edge cases` kwarg-requiring-form bullet, and the `## Test plan` `test_resolvers.py` row's
  parallel claim. The reword says the hook returns **constructor kwargs**, so the hook is the
  channel and the form applies the narrowing in its own `__init__` — the previous phrasing read as
  though the hook mutates `field.queryset`. The appended observability clause is in Decision 8
  only, the normative home.

#### Case (1) — planned and never built, DISCHARGED (1 item)

- [x] **35 — the four former `DROPPED` homes, re-graded with citations, no rewrite.** Applied as a
  **deliberate non-edit**, which is what the item asks for. Anchors `get_form(self, info` ×1 and
  `omitted file preserved` ×1 are byte-unchanged; `## Definition of done` item 5 and the
  `## Test plan` live `IntegrityError` bullet stand **as written** — no wording change — so the
  GAP-3 escalation's rejected alternative stays rejected. The two `## Edge cases` file bullets keep
  their text and the file clause gained item 33's append and nothing else. Re-grade, with the node
  ids as the citation:
  - `get_form` hook → `tests/forms/test_sets.py::test_get_form_only_override_trips_the_construction_hook_waiver`
    (`[modelform]` / `[plain_form]`) plus
    `tests/forms/test_resolvers.py::test_get_form_only_override_builds_the_form_and_waives_the_required_guard`.
  - omitted-file preserve → `tests/forms/test_resolvers.py::test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`,
    `::test_partial_reconstruction_excludes_every_file_field_flavor[attachment]` / `[image]`, and
    the live `test_products_api.py::test_update_item_with_file_via_form_omitting_the_file_preserves_it`.
  - live write-time `IntegrityError` (`ModelForm`) → **the pair**
    `::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`
    **and** `::test_create_default_category_item_via_form_injects_the_default_category`; either
    alone under-determines the contract, which is exactly the finding the apply-changes pass
    closed, so the pair is cited as a pair.
  - `get_form_kwargs` queryset scoping → `::test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged`.

  All four spec homes are `BUILT-CONFORMANT`. **The spec was right and the tests were owed.**

#### The three non-edit notes

- [x] **N1 — row placement, not staleness. Not "fixed".** The `## Test plan` `test_converter.py`
  row asks for the id mapping, the reverse map and `base_fields` discovery in `test_converter.py`
  while all three are pinned in `tests/forms/test_inputs.py`. Confirmed to be correct placement
  rather than a gap: `forms/converter.py::convert_form_field` deliberately returns
  `annotation=None` for relation and file kinds (read at `HEAD` — `_CONVERT_RELATION_SINGLE` /
  `_CONVERT_RELATION_MULTI` / `_CONVERT_FILE` are `_kind_converter` calls with no annotation),
  because the id type is resolvable only at the `forms/inputs.py` build site where the backing
  column and the related primary `DjangoType` are known. **The row was left untouched** — moving
  the clauses to the `test_inputs.py` row was the item's permitted alternative, and doing nothing
  is the cheaper correct answer for a row that is not false, only differently organised. No gap
  declared.
- [x] **N2 — `## Current state` graded clause by clause; no edit owed, and the generated-body
  quotation was diffed rather than reasoned about.** All five bullets are dated **observations**
  under `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions do not`;
  the two the shipped card falsified ("No `forms/` module exists", "The version line reads
  `0.0.11`") stay, because the header dates them. No bullet carries a **prediction** about the
  build's outcome. The one clause the note flagged for a real check is the parenthetical quoting
  `docs/TREE.md` as reserving `forms/` and `tests/forms/` "planned by `TODO-ALPHA-038-0.0.12`" —
  a quotation of a **generated** body, so `START.md`'s rule applies. Diffed:
  `git grep -c "planned by TODO-ALPHA-038-0.0.12" 731fecd8^ -- docs/TREE.md` → **2**, exactly the
  two rows the bullet describes, so the quotation was **true on its own date**; the current render
  → **0**, those rows now reading "Form-mutations subsystem - the Django-``Form`` / ``ModelForm``
  write side (spec-038)". A falsified observation stands, so the observation framing carries it.
  The borderline "there is no joint cut to defer the version bump to" clause is an **inference**
  rather than a reading, but the inference held (`038` did own the cut). **Zero edits to
  `## Current state`.**
- [x] **N3 — the `TODAY.md` drift is deferred work, not a spec edit.** `TODAY.md` was not opened
  for writing and not edited; the fence bars it. The catalog bullet is carried **verbatim** into
  `### Deferred work catalog input` below.

**Walk arithmetic:** 35 items + 3 notes = 38 rows, all 38 ticked. **Applied: 33.** **Applied as a
deliberate non-edit with the grade recorded: 5** (items 13 and 35, notes N1, N2, N3). **Deferred:
0.** **Not applicable: 0.** No item was left unhomed.

---

### Spec changes made (Worker 1 only)

Every edit below is located by **heading and quoted phrase, never a line number** (the file shifted
eight times this pass). Grading case per `docs/builder/build-038-form_mutations-0_0_12.md`
`## Cycle shape`.

| Spec location (heading) | Quoted phrase changed | Reason | Case |
|---|---|---|---|
| H1 title | `reusing the frozen `FieldError` envelope` → `shared` | the envelope type is additive, not frozen | 3 |
| opener | `reuses, **byte-identical**, the contracts … **froze for exactly this**` | same | 3 |
| `## Key glossary references` (subjects bullet) | `The current glossary text is provisional and Slice 5 must correct it` | future imperative about a shipped card's closeout | 3 |
| `## Key glossary references` (envelope bullet) | `**defined and froze** for this card` / `the byte-identical envelope` | additive, not frozen | 3 |
| `## Slice checklist` Slice 1 (converter) | `` `UUIDField` → `uuid.UUID`, `ModelChoiceField` `` | the `JSONField` row was missing | 3 |
| `## Slice checklist` Slice 1 (reverse map) | `the `input_attr → (form_field_name, kind)` reverse map` | the record type is `InputFieldSpec` | 3 |
| `## Slice checklist` Slice 1 (identity) | `operation kind, frozenset(effective field names))` | the key has a fourth component | 3 |
| `## Slice checklist` Slice 2 (allowed keys) | `The form allowed-key set adds `form_class` and drops` | there are two sets, and it was under-described on its own date | 2+3 |
| `## Slice checklist` Slice 3 (pipeline prose) | `**decode** the `data:` input via the reverse map` … | narrated the superseded order in prose; a "step" grep cannot see it | 2 |
| `## Slice checklist` Slice 3 (boundary) | `The whole pipeline runs inside one `transaction.atomic()`` | the shipped boundary adds an alias pin, a deadline check and a snapshot | 3 |
| `## Slice checklist` Slice 5 (version files) | `[`pyproject.toml`][pyproject], `__version__` in …, and `uv.lock` if it` | three surfaces, not five | 3 |
| `## Slice checklist` Slice 5 (package docs) | `from "Coming next (`0.0.12`)" to "Shipped today"` | quotes a doc state that no longer exists | 3 |
| `## Problem statement` | `` [`spec-036`][spec-036] froze the reusable contracts `` | additive, not frozen | 3 |
| `## Goals` item 3 | `**Reuse the frozen `FieldError` envelope.**` / `byte-identical` | same | 3 |
| `## Non-goals` (siblings) | `` [`TODO-ALPHA-039-0.0.13`][kanban] `` / `` -040 `` | both flavors shipped | 3 |
| `## Non-goals` (envelope) | `The frozen contracts are reused **unchanged**` | additive; "adds no member" is the surviving claim | 3 |
| `## Non-goals` (`TestClient`) | `deferred to the `0.0.14` [`TestClient`][glossary-testclient] card` | the helper shipped as `testing/` | 3 |
| `### Reference-package parity checkpoint` | `reuse the `036`-frozen envelope, byte-identical` | additive | 3 |
| `### From graphene-django` | `` `036`-frozen [`FieldError`][glossary-fielderror-envelope] `` | additive | 3 |
| Decision 2 (body) | `**reuses, byte-identical, the contracts … froze for exactly this**` | additive | 3 |
| Decision 2 (body) | `This card adds **no** field to [`FieldError`]` | "member", plus the additive statement added | 3 |
| Decision 2 (siblings) | `` — [`TODO-ALPHA-039-0.0.13`][kanban] `` / `` -040 `` | both flavors shipped (a fourth home the routed list missed) | 3 |
| Decision 5 (lead-in) | `each of which this card must generalize into an overridable seam` | future tense about shipped work | 3 |
| Decision 5 axis 1 | `a duck-typed `_mutation_meta` + `_payload_type_name` check` | false on its own date: a bind output cannot gate an import-time construction | 2 |
| Decision 6 (metaclass) | `It is a lighter base (its own metaclass) that shares` | the mechanism is a shared factory | 3 |
| Decision 6 (allowed keys) | `the form allowed-key set (adds `form_class`; drops` | two sets, not one | 2+3 |
| Decision 6 (payload) | `**Pinned plain-form payload contract (P2 — a fixed schema rule, not a preferred / fallback branch).**` | chronology hedge whose referent left the spec | 3 |
| Decision 6 (payload) | `the **fully-pinned** resolution of the prior preferred/fallback uncertainty` | same | 3 |
| Decision 7 (converter list) | `` `NullBooleanField` → `bool | None`; `FloatField` `` | `JSONField` row added; requiredness is a three-case rule | 3 |
| Decision 7 (reverse map) | `an `(input_attr, graphql_name) → (form_field_name, kind)` metadata record` | the type is `utils/inputs.py::InputFieldSpec` | 3 |
| Decision 7 (decoder) | `[`forms/resolvers.py`][forms-resolvers] runs its **own**` | the decode rides `decode_visible_relation`, a shared spine | 3 |
| Decision 7 (to_field_name) | `(P2 — #6).**` | undecodable label | 3 |
| Decision 7 (identity) | `frozenset(effective field names after `Meta.fields` / `Meta.exclude`))**` | the key has a fourth, hook-discriminator component | 3 |
| Decision 7 (fields/exclude) | `against `form_class.base_fields` (P3).**` | label; and the bold marker was repaired after the sweep | 3 |
| Decision 7 (create guard) | `` `update` is exempt — `` | there are two guards, keyed on one waiver | 3 |
| Decision 7 (discovery) | `This replaces the earlier "instantiate `form_class()` no-arg …" plan` | chronology; restated as a direct prohibition | 3 |
| Decision 8 (preamble) | `**Ordering correction — authorize runs BEFORE the relation decode (post-ship security fix).**` | the spec must state the contract, not a chronology | 2 |
| Decision 8 (steps 1-3) | `1. **Decode**` / `2. **Locate**` / `3. **Authorize**` | renumbered into the shipped order | 2 |
| Decision 8 (step 1) | `` reused `036` `_coerce_lookup_id` `` / `` `_locate_instance` `` | the helpers are public; the underscored names do not exist | 3 |
| Decision 8 (step 3) | `` **not** the `036` `_decode_relation_id_set` `` | the symbol does not exist; the gap is closed in the shared spine | 3 |
| Decision 8 (step 4) | `without changing the generated input shape` | the hook returns constructor kwargs; plus the written-row clause | 3 + addition |
| Decision 8 (step 4) | `` `data = {**model_to_dict(instance, fields=<the form's non-file fields>), …` `` | three reconstruction shapes, full declared field set, no key for a file field | 3 + addition |
| Decision 8 (step 4) | `` `mutations/resolvers.py` `_validation_error_to_field_errors` `` | the mapper is `utils/errors.py::validation_error_to_field_errors` | 3 |
| Decision 8 (step 4) | `both failure modes the review names` | cites an authority the spec does not carry | 3 |
| Decision 8 (helper reuse) | `Steps 2 / 3 / 4 / 6 / 7 are not new code` … `Slice 3 picks one and names it` | wrong step numbers, wrong locations, `payload_object_slot` false on its own date, and an unresolved build instruction | 2 |
| Decision 8 (how it fires) | `both form flavors override them to delegate **here**` | the seams come from shared factories | 3 |
| Decision 8 (boundary) | appended after `boundary discipline.` | the alias pin, deadline check and authorized-pk snapshot | 3 |
| Decision 9 | `` the **same** `036` `_refetch_optimized` `` | the helper is `refetch_optimized` | 3 |
| Decision 9 | `` the `036` Medium-1 exception `` | undecodable review label; restated as the re-fetch exception | 3 |
| Decision 10 | `is the single resolution of the prior contradiction` | chronology; the split is stated per base | 3 |
| Decision 11 | `**Preferred resolution:**` … `settled with its fallback in [Risks]` | the default is settled: `(DenyAll,)`; plus the `DjangoModelPermission` reject | 3 |
| Decision 12 | `this spec narrows it to the existing `test_products_api.py`` | the live surface spans three apps; products carries 8 | 3 |
| Decision 13 | `**`registry.clear()` co-clears THREE form rows**` | each owner announces its own clear; `registry.py` names none | 3 |
| Decision 14 | `Slice 5 therefore aligns the version quintet` | three surfaces, not five | 3 |
| `## Implementation plan` Slice-2 cell | `build_payload_type(object_type=None)` | keyword-required, no default | 3 |
| `## Implementation plan` Slice-2 cell | `[`registry.py`][registry] (THREE form co-clear rows: …)` | the clears are announced by their owners | 3 |
| `## Implementation plan` Slice-2 cell | `(TODO-anchor only — … Slice 3 deletes it)` | the staging step completed | 3 |
| `## Implementation plan` Slice-3 cell | `promote the reused pipeline helpers — … — to an importable shared surface, underscore-dropped in place` | three modules own them now | 3 |
| `## Edge cases` (`clean()`) | `` the `"__all__"` sentinel `036` froze `` | additive vocabulary | 3 |
| `## Edge cases` (partial update) | `` `data = {**model_to_dict(instance, fields=<non-file form fields>), …` `` | three shapes, full declared set | 3 |
| `## Edge cases` (choices) | `` reusing the `036` `_raw_choice_value` discipline `` | the helper is `utils/write_values.py::raw_choice_value` | 3 |
| `## Edge cases` (kwargs form) | `to scope a `ModelChoiceField.queryset` without changing` | the hook is the channel, not a queryset mutation | 3 |
| `## Edge cases` (create narrowing) | `**A `create` narrowing that drops a required form field (P2).**` | two guards, not one | 3 |
| `## Edge cases` (`IntegrityError`) | `` the `036` `_save_or_field_errors` mapper `` | the helper is public | 3 |
| `## Edge cases` (plain-form auth) | `requires an explicit `Meta.permission_classes`` | deny-by-default, plus the model-permission reject | 2 |
| `## Test plan` (live) | `(the P1 file-routing contract` and 6 further label sites | orphaned review residue | 3 |
| `## Test plan` (`test_resolvers.py`) | `` (P1, via `_save_or_field_errors`) `` | the helper is public | 3 |
| `## Doc updates` (GLOSSARY) | `**Correct the now-stale `DjangoFormMutation` entry (P2):**` | the correction landed; state the contract | 3 |
| `## Doc updates` (package docs) | `move form mutations from "Coming next (`0.0.12`)" to "Shipped today"` | quotes a doc state that no longer exists | 3 |
| `## Doc updates` (card wrap) | `moves [`TODO-ALPHA-038-0.0.12`][kanban] to Done with the next `DONE-NNN-0.0.12` id` | the card is `DONE-038-0.0.12` | 3 |
| `## Out of scope` (serializer) | `` — `0.0.13` ([`TODO-ALPHA-039-0.0.13`][kanban]) `` | shipped as `rest_framework/` | 3 |
| `## Out of scope` (auth) | `` ([`TODO-ALPHA-040-0.0.13`][kanban]) `` | shipped as `auth/mutations.py`; third registry consumer | 3 |
| `## Out of scope` (`TestClient`) | `` (`TODO-ALPHA-043-0.0.14`) `` | shipped as `testing/` | 3 |
| `## Definition of done` item 2 | `its Strawberry annotation + required-ness, reusing` | `JSONField` row; three-case requiredness | 3 |
| `## Definition of done` item 2 | `` `(form_class, operation kind, effective field set)` `` | fourth key component | 3 |
| `## Definition of done` item 2 | `a **`create` narrowing that drops a required form field raises**` | two guards | 3 |
| `## Definition of done` item 4 | `runs the decode → locate → authorize →` and the whole paragraph | the shipped order, the shared spine, the three shapes, the public helper names | 2+3 |
| `## Definition of done` item 8 | `[`pyproject.toml`][pyproject], `__version__` in …, and `uv.lock` (if applicable)` | three surfaces, not five | 3 |
| whole file | 62 `P1` / `P2` / `P3` / `#N` / `AR-*` / `Medium-1` occurrences | undecodable in the spec, or review-finding labels replaced by the contract they labelled | 3 |
| link definitions | `[utils-querysets]` pruned; seven added | orphaned by a deletion; seven modules the shipped contract now names | — |

**Deferral reasons owed for un-ticked walk rows: none.** All 38 rows are ticked, 5 of them as
deliberate non-edits whose grade is recorded in the walk above.

**Spec status/header re-verification** (`worker-1.md` `## Spec status-line re-verification`): the
`Status:` line reads `SHIPPED (`0.0.12`)` and is **accurate** — the card shipped, the five slices
were final-accepted, and the `0.0.12` figures throughout describe a cut that happened. The one
header defect was the H1's "reusing the frozen `FieldError` envelope", which is walk item 18 and is
fixed. No predecessor doc this cycle deleted is referenced; the `[spec-038-rationale]` pointer
Slice 0 added resolves.

---

### The step-renumber record

**Shipped order, single-sited in `mutations/resolvers.py::run_write_pipeline_sync` and read out of
its body and docstring at `HEAD`:**

**locate → authorize → decode → construct/validate → write → re-fetch → return**

The renumber is old 2 → **1** (Locate), old 3 → **2** (Authorize), old 1 → **3** (Decode); steps
4-7 (Construct + validate, Write, Re-fetch, Return) keep their numbers. It was performed by
slicing the spec on the three `N. **Name**` markers and re-emitting them in the shipped order with
new ordinals, so no step body was retyped and none could be silently dropped.

**The 11 step citations, swept.** `step \d` occurs **11** times in the pre-edit spec and `steps \d`
**zero** times — the population was measured by regex, not by the word "step" (which occurs 19
times, the difference being `Steps 2 / 3 / 4 / 6 / 7`, `step-4 merge` and the like). All 11 are
inside Decisions, exactly as the routed list established: 9 in Decision 8, 1 in Decision 9, 1 in
Decision 11.

| Citation | Disposition |
|---|---|
| `authorize before step 1's relation decode` (Ordering-correction para) | deleted with the paragraph |
| `The relation decode (step 1) issues` (same para) | deleted with the paragraph |
| `write-authorization check (step 3)` (same para) | deleted with the paragraph |
| `carried to step 4 as the `instance=` kwarg` (Locate) | **unchanged** — construct/validate is still step 4 |
| `step 4, from the reconstructed `data=`` (Locate) | **unchanged** |
| `gate (step 1, which runs before the form regardless)` (Construct) | **→ step 3** — the visibility gate is the decode |
| `the validation-error mapper reused per step 4` (Helper reuse) | **unchanged** |
| `reused per step 5` (Helper reuse) | **unchanged** — write is still step 5 |
| `so step 5 stays a single `form.save()`` (How it fires) | **unchanged** |
| `pipeline step 6` (Decision 9) | **unchanged** — re-fetch is still step 6 |
| `(Decision 8 step 2)` (Decision 11) | **→ step 1** — the locate |

Plus the non-`step \d` list `Steps 2 / 3 / 4 / 6 / 7 are not new code` → **`Steps 1 / 2 / 4 / 6 / 7`**
(locate, authorize, construct/validate, re-fetch, return), re-derived from which helpers the
paragraph actually names rather than by shifting the old numbers.

**The prose-only sub-check a "step" grep cannot see.** The routed list's population claim was
correct and the warning about it was load-bearing: `## Edge cases and constraints`, `## Test plan`,
`## Definition of done` and `## Slice checklist` contain the word "step" **zero** times, so there
were no step *citations* to fix in any of them — but the **`## Slice checklist` Slice-3 sub-check
narrates the pipeline in prose, in the superseded order** ("**decode** … (`update`) **locate** …
**authorize** … **construct**"), which no grep for "step" can find. It was reordered to
locate → authorize → decode → construct, and carries the authorize-before-decode reason inline.
Graded for the same defect and found clean: `## Definition of done` item 4 narrated
"decode → locate → authorize" and **was** reordered; the `## Test plan` `test_resolvers.py` row
lists behaviors rather than a sequence, so it has no ordering to fix (its "before the form" clause
is still true) — recorded as a grade rather than left silent.

**Two anchor decisions, both anchor-count-driven:**

- **Decision 8's heading was NOT rewritten.** Re-derived before the cut rather than trusted:
  `#decision-8` occurs **29** times in the spec (28 in-page `](#decision-8…` uses plus the
  `[rationale-d8]` definition) and **11** times in the companion. Its arrow sequence
  ("instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload") says
  nothing about decode-versus-authorize, so it survives the renumber untouched.
- **Decision 2's heading was NOT rewritten either**, for the same class of reason, even though it
  contains the word "frozen" that walk item 18 retires everywhere else. Two in-page uses, the
  `[rationale-d2]` definition, and the companion's `[spec-038-d2]` definition and heading resolve
  through it.

Every in-page anchor in both files was re-verified after the edits: 19 distinct anchors against 36
headings in the spec and 18 against 22 in the companion, **0 unresolved** in either.

---

### The companion's new `**Post-ship:**` bullets, by owning Decision

All 14 `- **Post-ship:** none recorded yet.` placeholders were replaced (the count was asserted at
14 before the write). Each bullet names the shipped behavior and, where measured, the commit that
changed it, so `docs/builder/BUILD.md` `## Spec rationale extraction`'s keying rule holds — an
entry naming no decision cannot be looked up.

| Decision | Post-ship bullets | Substance |
|---|---|---|
| 1 | 1 | measured no-change |
| 2 | 2 | the envelope is additive (`codes` / `path`), and why the heading was left alone; the two sibling flavors shipped |
| 3 | 1 | measured no-change |
| 4 | 1 | measured no-change (four modules + mirrored tests) |
| 5 | 1 | axis 1 was wrong on its own date; the shipped duck-typed protocol |
| 6 | 4 | shared metaclass factory (`5165314b`); `build_payload_type`'s real signature; two allowed-key sets, under-described on their own date; the retired chronology hedge |
| 7 | 8 | `JSONField` (`efb7bda5`); three-case requiredness (`5737ddda`); `InputFieldSpec` (`60dbf469`); the shared decode spine (`e9c13f55` / `8bac47be`); the 4-tuple key (`a2418106`); the partial guard (`cf3293cf`); the two guards left OUT of the spec, recorded so silence is not read as absence; the discovery-plan chronology |
| 8 | 9 | **the ordering supersession** (`60dbf469`), with the heading decision and the step map; the helper locations and `payload_object_slot`'s pre-`038` publicity; the retired "picks one" instruction; the shared runner; the fuller boundary; the three reconstruction shapes; the file-field no-key addition and why no wire row can see it; the `get_form_kwargs` channel semantics and the written-row clause; the retired review citation |
| 9 | 1 | `refetch_optimized`; the `Medium-1` label replaced by its contract |
| 10 | 1 | no contract change; the chronology retired |
| 11 | 2 | the `(DenyAll,)` default and the losing edge-case bullet; the `DjangoModelPermission` reject |
| 12 | 1 | three apps; products at 8, re-derived, and why the figure is not HEAD's 6 |
| 13 | 2 | `register_subsystem_clear` / `iter_subsystem_clears` (`60dbf469`); the third `make_declaration_registry` consumer as evidence |
| 14 | 1 | three version surfaces, not five; the `0.0.12` figures explicitly not "updated" |
| **`## Non-Decision deliberation`** | 5 new | the 62-label sweep and its two-way split; the underscore-name residual class that was in no routed list; the `## Current state` grade with the TREE.md quotation diffed both ways; the five working-tree-only guards deliberately excluded; the terms-CSV coupling re-applied, with the one pruned and seven added definitions |

**The companion's own falsified claims were reconciled in the same pass** (`START.md` "Sweep both
files of a pair" — editing the spec without the companion leaves the companion falsified):

- `## Provenance of this record`'s "**One shape in the spec still fails the clean-current-contract
  test, and a move cannot discharge it**" section described Decision 8's live narration. Rewritten
  to record that Slice 2 discharged it, with a pointer to this artifact.
- The same section's "**Not reconciled by this pass.** … Slice 2 of the cycle does" was rewritten
  to say the reconciliation has run and where its record is.
- `## Revision history`'s "was never folded into this history and **still sits inline in the
  spec**" was rewritten — it no longer does.
- The move's own byte figure read "It **is** 164,240 bytes, 2,227 lines after the move", a
  present-tense count of a file this pass then edited by 12,725 bytes. Re-dated to "It **stood at**
  164,240 bytes … when the move finished (Slice 2's reconciliation has since edited it)". The
  pre-move 185,851-byte figure is a measurement of `HEAD` and stands.
- The last `## Non-Decision deliberation` bullet's "the spec's `## Key glossary references`
  **still describes** that entry's correction as Slice 5 work" was rewritten to record the grade.

---

### Link-definition audit — both files, both directions

Instrument: a scratch verifier that strips fenced blocks **and** code spans from the body before
sweeping `][label]` uses (per `START.md`), parses the definition block by group header, and
resolves every non-URL target **from the source file's own directory** — never a bare
disk-exists check, which `START.md` calls fail-open because a same-named file one level up masks
depth rot. The spec sits two levels deep (`../../`-rooted); the companion three.

| File | Uses | Defs | Undefined uses | Unused defs | Broken paths | Groups |
|---|---|---|---|---|---|---|
| `docs/SPECS/spec-038-form_mutations-0_0_12.md` | 100 | 100 | **0** | **0** | **0** | all 10, canonical order |
| `docs/SPECS/appx/…-rationale.md` | 45 | 45 | **0** | **0** | **0** | all 10, canonical order |

**Orphans pruned: one.** `[utils-querysets]` — both its uses were inside Decision 8's retired
`mutations/_pipeline.py` deliberation (walk item 24). **Checked against the pinning file before
cutting**, which is the constraint Slice 0 discovered the hard way: it is a *source-path* label,
not one of the 31 `-terms.csv` rows the glossary gate requires to stay linked, so pruning it is
safe.

**Held back for the glossary gate: none needed this pass, and that is a measured result, not an
assumption.** The three CSV-pinned labels Slice 0 had to hold clauses back for —
`glossary-filterset`, `glossary-orderset`, `glossary-finalize_django_types` — were re-checked
against every deletion here: their surviving links sit in Decision 3's sibling-surface
parenthetical and Decision 13's single-finalize-call clause, neither of which this pass touched.
`docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv` was **not opened for writing**.

**Nine definitions added** (seven in the spec, two in the companion), each with a use:
`[auth-mutations]`, `[mutations-operations]`, `[rest-framework-package]`, `[testing-package]`,
`[utils-errors]`, `[utils-write-transaction]`, `[utils-write-values]` in the spec's
`<!-- django_strawberry_framework/ -->` group; `[mutations-resolvers]` in the companion's, and
`[tree]` in its `<!-- docs/ -->` group plus `[bld-038-slice-2]` in `<!-- docs/builder/ -->`.

**One pre-existing ordering oddity, not introduced here and not "fixed".** Both files list
`…-d10`…`-d14` before `…-d1`…`-d9` inside `<!-- docs/SPECS/ -->`. That is Slice 0's output in both
files and it passed the `source-layout` hook then; a naive lexicographic sort disagrees with it.
Left alone rather than churned, and recorded so a later reader does not read it as this pass's
drift.

**Source-reference convention.** Every reference added is a symbol path or a quoted substring, never
`path:NN` — a spec and its companion are standing docs (`AGENTS.md` rule 27). The five
`#"substring"` refs in the spec are **out of `check_citations.py`'s scope** (it is `::Symbol`-only),
so each was verified by hand to resolve **exactly once** at `HEAD`, counting occurrences rather
than lines:

| Reference | Occurrences at `HEAD` |
|---|---|
| `AGENTS.md` #"No CHANGELOG.md updates unless told" (×2 uses) | 1 |
| `AGENTS.md` #"The release is single-sourced" | 1 |
| `mutations/resolvers.py` #"authorize BEFORE decode" | 1 |
| `mutations/fields.py` #"operation != \"form\"" | 1 |

**One substring citation was withdrawn during verification.** I first cited the plain-form default
as `forms/sets.py` #"unset_default=(DenyAll,)" and the count came back **2** (a docstring mention
and the call site), so the reference was not unique. Replaced with the symbol form,
`forms/sets.py::DjangoFormMutation._validate_meta`. Recorded because the failure mode is exactly
the ungated one `START.md` warns about: nothing would have caught it.

**Two markdown defects this pass introduced and repaired**, both found by a `^#`-at-column-0 sweep
rather than by a gate: a reflowed line began `#"authorize BEFORE decode"` and another
`#"operation != \"form\""`, and a leading `#` renders as an H1 heading. Both were reflowed so the
`#"` sits mid-line. The sweep also found a bold marker orphaned by the label sweep
(`…base_fields`\n`** Mirroring`), repaired to `…base_fields.**`. Post-repair: **zero** lines in
either file begin with `#` that are not real headings.

---

### Before/after byte counts, commands quoted

```shell
git show HEAD:docs/SPECS/spec-038-form_mutations-0_0_12.md | wc -c      # 185851  (pre-cycle)
wc -c docs/SPECS/spec-038-form_mutations-0_0_12.md \
      docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md
```

| File | Before this slice | After this slice | Delta |
|---|---|---|---|
| `docs/SPECS/spec-038-form_mutations-0_0_12.md` | 164,240 | **176,965** | +12,725 |
| `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` | 55,325 | **80,892** | +25,567 |
| pair total | 219,565 | **257,857** | +38,292 |

The spec's "before" is Slice 0's post-move figure, not `HEAD`'s 185,851 — the pair is still
**8,886 bytes below** the pre-cycle spec on its own, and the growth is deliberate: the corrections
state contracts the spec had compressed into a line or omitted (three reconstruction shapes, two
narrowing guards, two allowed-key sets, the fuller transaction boundary, a three-app live surface),
against 62 labels and two retired deliberations removed. **The corpus ratchet does not apply here**
— it binds `docs/builder/BUILD.md`, `ARTIFACT.md` and the four `worker-*.md` role files, none of
which this pass touched.

These figures are the pass's closing measurement, not a standing claim: both files remain
uncommitted and a later pass may edit either (`START.md`: never write a present-tense byte count of
a file a later slice edits).

---

### Gate results

Run from the repository root, in the dispatch's order.

| # | Command | Result |
|---|---|---|
| 1 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md` | **PASS** — `OK: 31 terms - all have glossary entries and at least one spec link.`, exit 0 |
| 2 | `uv run python scripts/check_citations.py --check` | **PASS** — `OK: 938 citations resolve (783 in 435 .py files, 155 in KANBAN.md).` |
| 3a | `uv run ruff format --check .` | **PASS** — `438 files already formatted` (the standing `COM812` formatter-conflict warning is pre-existing) |
| 3b | `uv run ruff check .` | **PASS** — `All checks passed!` |
| 4 | `uvx pre-commit run --files <the three files touched>` | see below |
| 5 | `git status --short` | see below |

The glossary gate was run **before starting and after every substantial edit script**, not once at
the end — five runs in total, every one `OK: 31 terms`. Gate 2's scope is worth stating rather than
assuming: `check_citations.py` is `::Symbol`-only and whole-tree, so it proves no rename rotted a
citation anywhere in the tree, and it proves **nothing** about this pass's four `#"substring"`
refs, which are hand-verified above.

`pytest` was neither run nor needed: this slice edits two Markdown files, and no `--cov*` flag was
passed to anything.

---

### Deferred work catalog input

For `docs/builder/bld-038-final.md` `### Deferred work catalog`.

**1. The `TODAY.md` bullet, carried verbatim from
`docs/builder/bld-038-slice-1-code_conformance.md` `### Ruling 2`:**

> - **`TODAY.md` under-enumerates the products form-mutation surface — six named, eight shipped.**
>   Owner: **the maintainer** (no worker may edit it; the build plan's `## Scope fence` puts
>   `TODAY.md` out of scope for this whole cycle and the kanban DB with it, so this bullet is the
>   homing mechanism). Source: `docs/builder/bld-038-slice-1-code_conformance.md` `### Medium:`
>   ("The staleness sweep's population excluded the repo-root standing docs"), escalated again in
>   both review passes' `### Notes for Worker 1 (spec reconciliation)` item 1. Cause: this slice
>   added `updateItemWithFileViaForm` and `createDefaultCategoryItemViaForm` to
>   `examples/fakeshop/apps/products/schema.py::Mutation` under the GAP-2 / GAP-3 escalations —
>   surface the fence did not anticipate. Three homes, each resolving exactly once, each listing
>   six of the eight: `TODAY.md` #"- **Form-based mutation write surface**",
>   `TODAY.md` #"as of `0.0.12` the form-backed mutations",
>   `TODAY.md` #"**Form-backed mutations (`0.0.12`).**". The full set is
>   `createItemViaForm`, `updateItemViaForm`, `createItemWithFileViaForm`,
>   `updateItemWithFileViaForm`, `createDefaultCategoryItemViaForm`, `createStampedItemViaForm`,
>   `submitContact`, `submitPing` — re-derived twice (8 classes, 8 `DjangoMutationField` rows), so
>   no recount is owed. Recommended action: widen the fence by this one file and re-pin the three
>   sentences; measured at three sentences in one file, no generator, no gate. `TODAY.md` is
>   byte-identical to `HEAD` (42,568 bytes, `cmp` clean) — nothing was pre-emptively touched.
>   No licensing spec clause: this is cycle-caused drift, not a spec deferral.

**2. The five working-tree-only hunks, adopted into the spec nowhere.** Verified absent at `HEAD`
and present only in the concurrent session's uncommitted work, per the build plan's
`## Contract-level escalations` ruling that an uncommitted guard is not a shipped contract. Owner:
**the concurrent session that authored them**, whose own cycle commits them; no `038` worker
action. Recorded in the rationale companion's `## Non-Decision deliberation` as well, so a reader
of the spec's silence does not conclude they do not exist:

- `forms/inputs.py` — the `str.isidentifier` / `keyword.iskeyword` field-name guard; the guarded
  `dict(form_class.base_fields)` read; the two out-of-vocabulary `operation_kind` raises in
  `build_form_input_class` / `build_form_inputs`.
- `forms/sets.py` — the typed `BaseException` wrap around the `get_form_fields` hook invocation in
  `_mutation_form_fields`.
- `forms/resolvers.py` — the multi-relation container check lifted to
  `utils/write_values.py::materialize_relation_id_container`.

**3. Two `forms/inputs.py` guards the spec is silent about, deliberately.**
`_guard_input_attr_collisions` (two form fields colliding on a generated input attr or GraphQL
name) and `_model_less_relation_annotation`'s reject for a plain-`Form` relation field whose
`queryset` is `None` at class definition. Both are present at `HEAD`, both were graded as landed
contracts by Slice 1 (its items D-14 / D-15), and both were judged too narrow to promote into a
numbered Decision by this pass. They are recorded in the companion under Decision 7 rather than
dropped. Owner: **the next spec author** to decide whether either earns a Decision. No worker
action owed this cycle.

**4. Not deferred, recorded for the final gate's awareness.** `docs/SPECS/NEXT.md` is modified in
the working tree and was **not** touched by this pass. It is not on this slice's writable list, so
per the dispatch it is a stop-and-report rather than a revert — reported here and in
`### git status` below. Its diff is a concurrent session's; `AGENTS.md` rule 34 governs.

**5. The four full-sweep failures stay with Worker 0.** Not this slice's, not re-derived here: they
are the concurrent session's uncommitted `sets_mixins.py` edit
(`ActiveInputPermissionAttrs … 'unset_sentinel'`) and are not worker-verifiable at `HEAD`. No
`pytest` was run this pass.

---

### git status

```shell
git status --short docs/SPECS/ docs/builder/
```

Outside my writable list: **`docs/SPECS/NEXT.md` (modified).** Not mine, not reverted, reported —
see catalog item 4. Everything else in the diff is on the list: the spec, the rationale companion,
this artifact, and my gitignored memory file.

---

### Summary

Slice 2 rewrote `spec-038` to read as a clean, current, true description of the shipped code, and
put every "what changed, when, why, and what it replaced" into the rationale companion keyed to the
Decision that owns it. **33 of the 35 consolidated items were applied; 5 of the 38 walk rows (items
13 and 35, notes N1-N3) are deliberate non-edits with the grade recorded; nothing was deferred and
nothing left unhomed.**

The highest-value edit was Decision 8. It had been narrating its own history — an
`Ordering correction … (post-ship security fix)` paragraph plus "the step numbers below reflect the
original draft sequence" — while leaving its seven steps in the superseded order, which made it a
**false** contract rather than a stale one. The steps are renumbered into the shipped
**locate → authorize → decode → construct/validate → write → re-fetch → return**, the narration is
gone, the supersession is a companion bullet, and all 11 step citations plus the one prose-only
Slice-3 sub-check that no "step" grep can see are swept. Both Decision 8's and Decision 2's
headings were deliberately left alone after counting what resolves through them.

Three things this pass found that the routed list had not: **six** underscore-prefixed helper names
still used in normative sentences for symbols that no longer exist (the parallel-site residual the
promotion paragraph's own fix left behind), **three** homes for the sibling-flavor card citations
rather than the two named, and **eleven** sites carrying the frozen-envelope vocabulary rather than
the seven the `byte-identical` anchor could see. Each was fixed as a custodian addition and is
recorded above.

Every count in this artifact was measured by the instrument that reports it, and the two figures
that mattered most were re-derived rather than copied forward: the products form-mutation surface is
**8** (8 classes, 8 field rows — `HEAD` carries 6, and the two extra are this cycle's own Slice-1
output, which is a different thing from the concurrent session's hunks), and the `AR-*` labels were
**verified against `spec-036` before being touched**, where all five resolve.

### Final status

`final-accepted`
