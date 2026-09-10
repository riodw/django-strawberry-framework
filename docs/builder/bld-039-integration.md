# Build: cross-slice integration pass (`spec-039` residual-reconciliation cycle)

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (whole document)
Rationale companion: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`
Build plan: `docs/builder/build-039-serializer_mutations-0_0_13.md`
Status: final-accepted

This is the `docs/builder/BUILD.md` `## Cross-slice integration pass` for a
**reconciliation** cycle: three passes (2a, 2b, 2c) rewrote the same two documents in
sequence, so the pass's centre of gravity is the **divergence inventory** — the places two
of `START.md`'s five homes disagree — rather than the ordinary cross-slice DRY scan.
`START.md`: *"Reconciliation slice introduces contradictions it can't see. Integration pass
owes the divergence INVENTORY, not the consistency of the discharging text."*

Combined Plan + Final-verification pass by Worker 1 (`docs/builder/BUILD.md`
`### Procedural-closure slices`); no builder, no reviewer. **No executable change was made
in this pass** — every edit is to the spec and its companion.

Required reading done in slice order, all nine prior artifacts in full:
`bld-039-slice-0-rationale_extraction.md`, `bld-039-audit-1-converter_and_inputs.md`,
`bld-039-audit-2-sets_and_bind.md`, `bld-039-audit-3-resolvers_and_live.md`,
`bld-039-audit-4-decisions_rev6_dod.md`, `bld-039-slice-3-code_gaps.md`,
`bld-039-slice-2a-contract_fold_in.md`, `bld-039-slice-2b-label_strip_and_citers.md`,
`bld-039-slice-2c-rev6_retirement.md`. Spec status/header lines re-verified per
`docs/builder/worker-1.md` `## Spec status-line re-verification`: the opener's
`Shipped in 0.0.13` / `DONE-039-0.0.13` claim, the `Status: **SHIPPED (0.0.13)**` line and
the predecessor pointers all still describe the tree. No status-line edit owed.

---

## Divergence inventory

Every place two of the five homes (Decision · slice checklist · `## Edge cases` ·
`## Test plan` · `## Definition of done`) disagreed, whether or not it was fixed. Two
further homes turn out to carry contract prose in this spec and belong in the cross-check:
the **document head / title** and the **`## Implementation plan` table**. Both produced
divergences no per-slice pass could see, because no slice owned them.

### D1 — the `FieldError` envelope: seven homes said frozen, three said additive. FIXED

The dispatch named the head opener. Measured, the population was **seven**, not one:

| Site | Claim before |
|---|---|
| document **title** (line 1) | "reusing the **frozen** `FieldError` envelope" |
| head opener (line 22) | "The flavor reuses, **byte-identical**, the contracts `036` froze … the shared `errors: list[FieldError]` envelope" |
| `## Key glossary references` envelope bullet | "the shared error contract `spec-036` **defined and froze** for this card" |
| `## Borrowing posture` → graphene `serializer.errors` row | "here it maps onto the **`036`-frozen** `FieldError`" |
| `## Borrowing posture` → rejected "second envelope shape" | "the `036` `FieldError` is **reused unchanged**" |
| `### Decision 5` | "returns the **frozen** `FieldError` envelope" |
| `### Decision 8` flattener section ×2 | "while the **frozen** `FieldError` is flat"; "both terminate in the same **frozen** envelope" |

Against them: `## Non-goals` bullet 2, `### Decision 2`, `## Goals` item 3 and the
`## User-facing API` parity row all say the envelope is **additive, not frozen** — this
card adds `codes` / `path`. `KANBAN.md` and `mutations/inputs.py::FieldError`'s own
docstring say additive too. Slice 2a's `#### E` table **claims** the head opener was among
the sites it fixed; it was not, and the title, Decision 5, and the four `## Borrowing
posture` / flattener sites were never in its list at all.

Two instruments, so the population is not one glob's: `grep -n frozen` (23 hits, 7 of them
envelope-bearing) cross-checked against `grep -n 'byte-identical'` (which finds line 22 and
nothing else in the spec) and `grep -n 'reused unchanged'` (which finds only the
rejected-alternative bullet). No single pattern reaches all seven.

**Fixed, all seven.** Post-fix the spec's only `frozen`-plus-envelope sentences are the two
that assert the additive contract. Deliberately **not** changed, with the reason recorded in
the companion: the two "`spec-036` **froze** X" sentences (they describe the predecessor's
act, and Decision 2 carries this card's carve-out), and `### Decision 2`'s own heading, whose
`…the-frozen-036-contracts…` slug is the target of 20+ `#decision-2--…` anchors across both
files — rewriting it to fix a word would strand every one of them.

### D2 — the reverse map: two homes said nine axes, three said a three-tuple. FIXED

`### Decision 7` "**Reverse map**" and the Slice-1 `serializer_converter.py` checklist
bullet both state `utils/inputs.py::InputFieldSpec`'s **nine** axes and `kind`'s **six**
members (Slice 2a's `#### F` row F4 corrected exactly those two). Three other homes still
carried the pre-build `input_attr → (serializer_field_name, source, kind)` triple:

- `## Definition of done` item 2 (a DoD item is the one place a stale figure is a false
  completion claim);
- `## Test plan` → `test_converter.py` bullet;
- `## Implementation plan` table, Slice-1 row.

Audit 1a graded this row **A8 SPEC-STALE** naming two homes; the other three were outside
every audit's enumerated population. **Fixed, all three**, by content (`the nine-axis
utils/inputs.py::InputFieldSpec reverse map`) rather than by re-transcribing nine axes into
three more places that would then have to be kept in step. Post-fix count of the triple:
**0**.

### D3 — `partial` in a hook return: Decision 8 vs the Test plan. FIXED

`## Test plan` said *"an override that returns `partial=False` (or `partial=True` on create)
raises `ConfigurationError`"* — which licenses `partial=True` on update. `HEAD` is
`rest_framework/resolvers.py::_merged_serializer_kwargs` #"if \"partial\" in kwargs:", an
unconditional rejection on **key presence**, whatever the value. `### Decision 8` step 4 was
not wrong but was silent on the rejection: it said only that the resolver sets `partial=True`
for update and never for create, while stating the parallel `instance` rule as *"**any**
returned `instance` key is rejected outright"*.

**Fixed both**: the Test plan row now says a `partial` key at all raises; Decision 8 step 4
now states the rejection in the same shape as its `instance` sibling.

### D4 — `_validate_meta`'s scope: three homes enumerate the shipped validator, DoD item 3 did not. FIXED

Audit 1b's finding 3 (rows A41 / A8 / G4) put this sentence in three homes; Slice 2a's
`#### D` rows D1 / D2 / D3 corrected `### Decision 6`, the Slice-2 `**DRY / reuse**` bullet
and the P2.5 table cell, and row **D6 claims** it also widened `## Definition of done`
item 3. Measured: item 3's `Meta` matrix listed only the original eight checks and named
none of `Meta.injected_fields`, `Meta.select_for_update`, `Meta.nested_fields`, the
`get_serializer_for_schema()` field-map validation, the fingerprint capture, or the
recursive writable-`source` walk. **Fixed** — item 3 now carries all six, pointing at
Decision 6 as the owning statement.

### D5 — the hook signatures: three sites dropped `self`. FIXED

`SerializerMutation.get_serializer_kwargs`, `::get_serializer_injected_data` and
`::get_serializer_save_kwargs` are all **instance methods** at `HEAD`
(`rest_framework/sets.py:923`, `:966`, `:990`). The spec spelled the same contract two ways:
`(self, info, *, data, hook_context)` at the `## Borrowing posture` parity row,
`### Decision 8` step 4 and the save-kwargs improvement item, and `(info, *, data,
hook_context)` in the Slice-3 checklist (twice) and `## Definition of done` item 4.
**Fixed, all three** to the shipped spelling. Small, but it is the same class as the
`instance=None` residue audit 3 caught in A1g: a signature in a shipped spec is copied.

### D6 — `## Test plan` DRF-absent bullet: unbalanced parenthesis. FIXED

Slice 2a's rewrite (`#### M`) left the bullet with one `)` more than it opened, so the
sentence reads as though the eviction discipline were inside the "never a
`builtins.__import__` patch" aside. Repaired with a colon; the content is unchanged and
still correct.

### Divergences graded and deliberately NOT fixed

- **`## Definition of done` item 2's descriptor-identity clause is weaker than
  `### Decision 7`'s, not false.** It says the identity is "the emitted field specs +
  normalized `optional_fields`"; Decision 7 and the Slice-1 checklist add the emitted
  **descriptions** as an independent axis and the **post-widening** annotation repr
  (audit 1a B5). A DoD item stating a subset of a Decision's enumeration is an
  under-enumeration; widening it would put a fourth copy of a five-part tuple in the
  document. Recorded so the next reader knows it was measured rather than missed.
- **Nine `TODO-ALPHA-040-0.0.13` card ids in this spec name a card that is
  `DONE-040-0.0.13` today.** Not this cycle's to flip: `KANBAN.md:618` carries a measured,
  owned work item for exactly this population across `spec-034`…`spec-039`, and it rules
  that the class splits three ways with only one third mechanical. Editing nine sites here
  would pre-empt that card's classification pass. **Record only.**
- **`### Decision 2`'s heading and two "`spec-036` froze X" sentences** — see D1.

## Plan (Worker 1)

### Cross-slice DRY scan

`docs/builder/BUILD.md` `## Cross-slice integration pass` steps 2-5.

**Step 2 — static inspection helper.** Discharged for every file with review-worthy logic
the cycle touched, either run or explicitly skipped with a reason on disk: audit 1a ran it
on `rest_framework/serializer_converter.py` and `rest_framework/inputs.py`; audit 1c on
`rest_framework/resolvers.py`; Slice 3's plan re-ran it on `resolvers.py`. Audits 1b and 1d
and Slice 3's Worker 2 / Worker 3 passes each recorded an explicit skip with the trigger
that did not fire. Slices 0 / 2a / 2b / 2c touch no `.py` executable surface. The cycle's
**only** production edit is inside `resolvers.py`, which the helper covered twice.

**Step 3 — repeated string literals across files.** Run as a fresh AST census rather than by
comparing the shadow overviews' per-file sections, because the audits' file-partitioned
scope is exactly what hid the cross-module duplication (see F1). Instrument: every
non-docstring `str` constant of ≥ 25 characters and ≥ 4 words in the six
`rest_framework/` modules, keyed by value.

- **4 literals appear in two or more modules** — all four are nested-serializer
  configuration diagnostics shared by `inputs.py` and `sets.py` (F1).
- **3 literals repeat within one module** — `serializer_converter.py` #"Registered
  serializer-field converter for " (3×, one message assembled three ways) and two
  `resolvers.py` message fragments (2× each) that audit 1c already recorded under its
  message-prefix finding.

**Step 4 — imports and boundary direction.** The spec's `### Import manifest` is now
per-**module** (Slice 2a's choice `#### L`), which makes it mechanically checkable for the
first time. Checked **both directions** against the AST of all six `rest_framework/`
modules' relative imports:

```
serializer_converter.py: extra=[] manifest-lists-but-unimported=[]
inputs.py:               extra=[] manifest-lists-but-unimported=[]
sets.py:                 extra=[] manifest-lists-but-unimported=[]
resolvers.py:            extra=[] manifest-lists-but-unimported=[]
__init__.py:             extra=[] manifest-lists-but-unimported=[]
hook_context.py:         extra=[] manifest-lists-but-unimported=[]
```

No module imports outside its permitted set, and no permitted package is listed for a module
that does not import it. Dependency direction is one-way: only `resolvers.py` and `sets.py`
reach `.inputs` / `.serializer_converter`, `hook_context.py` imports nothing first-party.
The manifest was rewritten from measurement in 2a and is still exact.

**Step 5 — deferred follow-up in prior artifacts' `What looks solid` / `DRY findings`.**
Walked all nine. Live items are F1-F3 below plus the four carries in
`### Notes for Worker 1 (spec reconciliation)`. Nothing else was left open.

### Staged-anchor sweep (`docs/builder/BUILD.md` step 6)

```shell
grep -rEn 'TODO\(spec-039|TODO-(ALPHA|BETA|STABLE)-039' . \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**Population printed, not counted blind: 11 hits, 0 in shipped source or tests.** Breakdown:
2 in `spec-039` prose (one *describing* the `TODO(spec-<NNN> Slice N)` convention, one a
`## Current state` observation quoting the pre-build card id), 1 in the Slice-4 card-wrap
row, 2 in the rationale companion (the revision-1 provenance line and a prose description of
the convention), 3 in sibling specs' own prose (`spec-036`, its companion, `spec-038`'s
companion), and 3 in this cycle's own `bld-039-*` records of the sweep. **Zero `.py` files
appear.** No anchor is discharged-but-present; nothing routes back to a slice.

### Existence challenge — `mutations/sets.py::cached_build_input`

Raised by audit 1b (`### DRY findings`, Notes 8) on the grounds `docs/builder/worker-3.md`
prescribes: a promoted helper with one real caller.

**Answer: keep it. The measurement resolves the question without a contract change, so it
does not need to go to the maintainer.**

Readers measured across `django_strawberry_framework/`, `tests/` and `examples/` (population
printed, 11 hits):

- **1 executable caller** — `forms/sets.py` #"return cached_build_input(".
- **6 in-code citations by name, in four other modules**, each explaining its own behavior
  *relative to* this helper: `rest_framework/sets.py` ×3 (the `SerializerMutation.build_input`
  docstring's statement of why the serializer does **not** ride it), `rest_framework/inputs.py`
  ×2 (the post-build descriptor key contrasted with the form's pre-build key),
  `utils/inputs.py` ×1 (the get-or-store spine's own layering note), plus `forms/sets.py`'s
  call-site comment and `tests/utils/test_inputs.py`'s docstring naming it as one of the
  three riders of one get-or-store.

The two candidate answers and what each loses:

- **(a) Keep** — *loses:* one indirection layer over a two-statement body stays. *Gains:* the
  guard-before-cache-lookup ordering keeps a named home. That ordering is a real invariant
  with its own tests on **both** sides (`tests/rest_framework/test_sets.py::test_build_input_runs_required_guard_per_declaration`
  for the serializer's inline equivalent; the form suite for the helper's own), and
  `spec-039`'s promotion-table cell defines the serializer's divergence *by reference to it*.
- **(b) Inline into `forms/sets.py`** — *loses:* six in-code citations in four modules go
  dangling, `spec-039`'s promotion table and Decision 6's cross-flavor paragraph lose their
  referent, and the only named statement of an ordering invariant two flavors depend on
  dissolves into a comment in one of them. *Gains:* one fewer function.

It is not the dead-code case `docs/builder/worker-1.md` `## Integration pass` warns about
(zero readers → delete-and-trim): there is one live caller and six live citers. And the
reason it will not gain a second caller is itself a shipped contract — `spec-039` rules the
serializer out on a stated mechanical ground (its cache key is only knowable *after* the
build), not by preference. **(a).** No spec change owed; the spec already states the
divergence and the reason for it.

### Findings that need Worker 2 (this is why `Status: revision-needed`)

**F1 — the nested-serializer schema-time diagnostics are spelled three times across two
modules.** Audit 1a routed this as "spelled twice inside `rest_framework/inputs.py`" from
`review_inspect.py`'s per-file repeated-literal section. Both halves of that figure are
wrong, in opposite directions, and the reason is instrumental:

- The audit's own fragment matches **once** at the working tree, because the two sites wrap
  the implicit string concatenation at different columns. A whitespace-normalising
  instrument (join adjacent literals, collapse runs) measures **2** inside `inputs.py`.
- The population is not one file. `rest_framework/sets.py::_validate_serializer_nested_fields`
  carries a **third** copy — a six-line `except ConfigurationError: raise / except Exception:
  raise ConfigurationError(...)` block that differs from `inputs.py`'s only in one identifier
  (`child_class` vs `nested_class`). The audits were partitioned per file, so no audit could
  see it; this is the cross-slice scan's own finding.

Full measured population, four shared fragments:

| fragment | sites |
|---|---|
| `". A nested serializer opted in via Meta.nested_fields must expose a stable, request-independent no-arg .fields (override get_serializer_for_schema() on the mutation to return a stable field map)."` | `inputs.py::_fingerprint_nested`, `inputs.py::_resolve_nested_field`, `sets.py::_validate_serializer_nested_fields` |
| `"Could not read .fields from nested serializer "` | `inputs.py`, `sets.py` |
| `".Meta.nested_fields must be a mapping of {field_name: NestedSerializerConfig}; got "` | `inputs.py`, `sets.py` |
| `"] must be a NestedSerializerConfig; got "` | `inputs.py`, `sets.py` |

Why it matters rather than being cosmetic: these are the messages a consumer reads to fix an
opted-in nested serializer, and the three copies of the long sentence are the *same*
instruction. A wording change to one is invisible to every test — the two rows that pin it
(`tests/rest_framework/test_inputs.py:1667`, `tests/rest_framework/test_sets.py:2100`) both
match only the shared **prefix** `"Could not read .fields from nested serializer"`, so
either module's tail can drift silently.

Shape to build: one module-level raise/message helper in `rest_framework/inputs.py` (which
`sets.py` already imports from, so the dependency direction the manifest permits is
unchanged), interpolating the serializer class name. **Preserve every byte of the current
text** — both `pytest.raises(match=…)` rows must pass unedited, and that is the acceptance
condition.

**F2 — the provisional input-type name is derived twice, and a shared deriver already
exists.** `rest_framework/inputs.py::resolve_injected_field_specs` (`:775`) and
`::build_serializer_input_class` (`:1639`) each spell
`f"{serializer_class.__name__}{'PartialInput' if <partial test> else 'Input'}"`, with
different partial tests (`operation_kind == PARTIAL` vs `is_partial`). They **must** agree:
`resolve_injected_field_specs`'s own docstring records that an operation-blind provisional
would make `resolvers.py::_assert_field_agreement` raise on every invocation of a valid
update declaration, so a divergence is a live failure mode rather than an inconsistency.

Audit 1a noted `utils/inputs.py::generated_input_type_name` "does not cover the
provisional". Measured, it does: read at `HEAD`, its body is `suffix = "PartialInput" if
is_partial else "Input"` then `if is_full_shape: return f"{base_name}{suffix}"`, so
`generated_input_type_name(serializer_class.__name__, is_partial=…, is_full_shape=True,
token="")` returns the identical string. This is a two-call-site change against an existing
shared helper, **not** a new abstraction — the cheapest kind of consolidation and the one
`docs/builder/worker-1.md` prefers.

**F3 — routed onward, deliberately NOT dispatched here: the
`f"SerializerMutation {…}"` message prefix.** Audit 1c published **40** occurrences in
`rest_framework/resolvers.py` and routed it to its own card. Re-measured across the
subpackage: **61** `f"SerializerMutation {` sites (`resolvers.py` 40, `sets.py` 16,
`inputs.py` 5) and **70** `"SerializerMutation "` literals in total (43 / 16 / 14), plus a
fourth spelling in `utils/permissions.py::request_from_info(family_label="SerializerMutation")`.
The published 40 was right in every digit and wrong in subject — it was one file's count
presented as the population. A 70-site message refactor inside a reconciliation cycle is the
"while I'm here" this repo refuses, and several of the strings are `pytest.raises(match=…)`
anchors, so it wants its own card with its own review. **Owner: the maintainer**, carried
into `docs/builder/bld-039-final.md`'s `### Deferred work catalog` so it does not die
unowned.

### DRY findings that stand clean

- **No new duplication from this cycle's code.** The only production edit is six lines inside
  `resolvers.py::_assert_field_agreement`; the only new file is a test manifest. Item 1's two
  halves assert different properties, item 3's manifest is one table in one file covering both
  consumer modules, item 4 reuses its rejection twin's scaffolding.
- **The DRY import ratchet's shipped population matches the spec's stated one, row for row.**
  Re-derived rather than accepted: the Slice-1 `**DRY / reuse**` bullet enumerates four
  dispatch-skeleton symbols, both P2.1 shapes, the one-ledger trio, the shape-build cache
  pair, the suffix helper, the four input-kind constants, `build_strawberry_input_class`,
  `normalize_field_name_sequence`, and `graphql_camel_name` in both consumer modules — which
  sums to **19 identity rows**, exactly `SHARED_BINDINGS`, plus the **2** `__code__` rows in
  `SHARED_CLOSURE_BODIES`. `Escalation A`'s auditability condition is met: the spec states the
  shipped population explicitly enough that either maintainer answer is checkable against it.
- **Comments tell one story across the cycle's `.py` surface.** Sweep for `.py` prose still
  asserting a contract the spec now corrects: 1 hit,
  `auth/mutations.py` #"user ``DjangoType`` + the frozen ``errors`` envelope" — `spec-040`'s
  file, and defensible against `mutations/inputs.py::FieldError`'s own docstring, which uses
  "frozen" in the additive sense ("a member may be added … never removed"). Not this cycle's
  and not a finding.

---

## Final verification (Worker 1)

### Gate results

| Gate | Command | Result |
|---|---|---|
| source layout | `uv run python scripts/check_trailing_commas.py <spec> <companion>` (explicit paths, never a bare `.`) | **pass** — `Fixed 0 file(s).` |
| spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | **pass** — `OK: 38 terms` (unchanged across the whole cycle) |
| citations | `uv run python scripts/check_citations.py --check` | **pass** — `OK: 963 citations resolve (808 in 442 .py files, 155 in KANBAN.md)` — unchanged, no reduction |
| ruff format / check | not run — **no `.py` file touched**, so the scoped-invocation rule has no files to scope to | n/a |

**Checks no gate performs, run by hand.**

- **Spec-side `path::Symbol` resolution.** `check_citations.py` reads `.py` and `KANBAN.md`
  only, so it sees none of a spec's citations. An AST index over
  `django_strawberry_framework/`, `tests/`, `examples/` and `scripts/` resolved **54**
  distinct citations in the spec and **13** in the companion. **One reported unresolved, and
  it was my instrument, not the spec:** `utils/write_transaction.py::WriteAliasContext.authorized_pk`
  is assigned as an instance attribute in `__init__` (`write_transaction.py:166`), which the
  walker did not visit. Verified present by reading before filing anything — fourth time this
  cycle a resolver's blind spot presented as a finding. Genuine unresolved: **0** in both files.
- **Link definitions and anchors, both directions, both files.** Spec: 185 in-page anchors,
  **0** dangling; 115 definitions / 115 used labels, **0** undefined, **0** orphan; every
  definition target present on disk. Companion: 89 / 0 / 60 / 60 / 0 / 0, same. The anchor
  count rose 183 → 185: the two `[Decision 2]` / `[Decision 6]` in-page links this pass added.
- **Line length.** Every line over 110 characters in the spec is an unwrappable
  `](#decision-N--…)` anchor, which the file's own convention and `START.md` both forbid
  wrapping. Two paragraphs the edits left ragged were re-flowed to the file's ~92-column style.

### Before / after

| File | Before (post-2c) | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | 314,984 B / 3,952 L | **316,238 B / 3,965 L** | +1,254 B / +13 L |
| `docs/SPECS/appx/…-rationale.md` | 126,064 B / 1,760 L | **126,826 B / 1,769 L** | +762 B / +9 L |

The corpus ratchet (`docs/builder/BUILD.md` `## The corpus ratchet`) governs `BUILD.md` /
`ARTIFACT.md` / `worker-*.md`; no file under it was opened.

### Working-tree discipline

`git status --short` after the pass: the only file this pass modified is
`docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (tracked) plus the untracked companion
and this artifact. `git diff --stat` over `docs/SPECS/` and `docs/SPECS/appx/` names the spec
alone. Everything else dirty is a prior slice's accepted work or the concurrent `spec-050`
session's — `list_field.py`, `orders/sets.py`, `resource_policy.py`, `_strawberry_patches.py`,
`utils/querysets.py`, `docs/spec-050-*`, `docs/builder/bld-final.md`, `docs/feedback.md` and
their tests — **neither edited nor reverted** (`AGENTS.md` rule 34). The two MIXED files
Slice 2b enumerated (`rest_framework/resolvers.py`, `utils/querysets.py`) were not opened.

No `pytest` was run: this pass ships no executable change, and no `--cov*` flag was used
anywhere.

### Summary

The spec's five (in this document, seven) homes now agree on every contract this pass could
cross-check. Six divergences were found and fixed — the envelope's frozen-versus-additive
split across **seven** sites where the dispatch named one, the reverse map stated as a
three-tuple in three homes after two were corrected to nine axes, the `partial`-key rejection
missing from Decision 8 and mis-scoped in the Test plan, `_validate_meta`'s shipped scope
absent from `## Definition of done` item 3, three hook signatures spelled without `self`, and
an unbalanced parenthesis Slice 2a's rewrite left behind. Three were sites Slice 2a's own
change table **claims** to have fixed, which is the reconciliation-pass failure mode
`START.md` names: a discharging text that reports a wider fix than it made. Two were in homes
no slice owned (the document title, the `## Implementation plan` table).

Two DRY findings need a builder and set the status: the nested-serializer diagnostics
duplicated three ways across two modules — a cross-module population no file-partitioned
audit could see, and larger than the two-site figure audit 1a routed — and the provisional
input-type name derived twice where a shared deriver already exists and a divergence is a
live failure mode. The `"SerializerMutation "` message prefix is re-measured at 70 sites
across four modules (published as 40 in one file) and routed to the maintainer with a named
home rather than folded in. The existence challenge on `mutations/sets.py::cached_build_input`
is answered — keep — on one executable caller plus six in-code citations in four modules, and
needs no contract decision. The staged-anchor sweep is clean at zero live anchors in source,
the per-module import manifest verifies exact in both directions, and all three gates pass
with the glossary and citation counts unchanged.

### Spec changes made (Worker 1 only)

All to `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` unless noted. Every one states
the current contract directly; no chronology entered the spec.

| # | Home | Change | Driving divergence |
|---|---|---|---|
| 1 | document title (line 1) | "reusing the **frozen** `FieldError` envelope" → "the **shared** `FieldError` envelope" | D1 |
| 2 | head opener | "reuses, **byte-identical**, the contracts …" → "reuses the contracts …", and the envelope item now carries the additive carve-out plus a `[Decision 2]` in-page link | D1 (the dispatch's named item) |
| 3 | `## Key glossary references` envelope bullet | "the shared error contract `spec-036` **defined and froze** for this card" → "**defined for this card**, and which this card extends additively with `codes` / `path`" | D1 |
| 4 | `## Borrowing posture`, graphene `serializer.errors` row | "maps onto the `036`-**frozen** `FieldError`" → "maps onto the one **shared** `FieldError` `036` defined" | D1 |
| 5 | `## Borrowing posture`, rejected "second envelope shape" | "is **reused unchanged**" → "is reused **rather than forked** (extended additively, never duplicated)" | D1 |
| 6 | `### Decision 5` | "returns the **frozen** `FieldError` envelope" → "returns the one **shared** envelope (additively extended, above)" | D1 |
| 7 | `### Decision 8` flattener section, 2 sites | "the **frozen** `FieldError` is flat" → "the **shared** `FieldError` is flat"; "terminate in the same **frozen** envelope" → "the same **shared** envelope" | D1 |
| 8 | `## Definition of done` item 2 | the reverse map restated as the nine-axis `utils/inputs.py::InputFieldSpec`, `kind` over the six members Decision 7 names | D2 |
| 9 | `## Test plan` → `test_converter.py` bullet | same restatement | D2 |
| 10 | `## Implementation plan` table, Slice-1 row | same restatement | D2 |
| 11 | `## Test plan` → `get_serializer_kwargs` precedence row | "returns `partial=False` (or `partial=True` on create) raises" → a `partial` key **at all**, whatever its value, on either operation, raises | D3 |
| 12 | `### Decision 8` step 4 | added the explicit `partial`-key rejection, in the same shape as the sentence's `instance` sibling | D3 |
| 13 | `## Definition of done` item 3 | `Meta` matrix widened by the six shipped checks it omitted (`injected_fields`, `select_for_update`, `nested_fields` + its override requirement, the schema field-map validation, the fingerprint capture, the recursive writable-`source` walk), pointing at Decision 6 | D4 |
| 14 | Slice-3 checklist ×2, `## Definition of done` item 4 | `get_serializer_kwargs(info, …)` / `get_serializer_injected_data(info, …)` → the shipped `(self, info, *, data, hook_context)` | D5 |
| 15 | `## Test plan` DRF-absent bullet | unbalanced `)` repaired with a colon; content unchanged | D6 |
| 16 | two paragraphs across the edited regions | re-flowed after the edits left ragged wraps | wrap defect, not content |

### Rationale companion changes (Worker 1 only)

One entry, under the existing
`### Post-ship findings that belong to no single Decision` heading, extending the bullet that
already recorded the "byte-identical" falsification: the measured population was **seven**
sites rather than two, all seven now state the additive contract, and the two
"`spec-036` **froze** X" sentences plus `### Decision 2`'s heading are recorded as **graded
non-edits** with the reason (a predecessor's act; an anchor 20+ references depend on). No
link definition was added or removed.

### Notes for Worker 1 (spec reconciliation)

Each item has a named owner; nothing is routed forward unowned.

**For Worker 2 (a consolidation pass; Worker 3 reviews) — this is the re-loop:**

1. **F1**, the nested-serializer diagnostics: three copies of one instruction sentence plus
   three more shared fragments across `rest_framework/inputs.py`
   (`::_fingerprint_nested`, `::_resolve_nested_field`) and
   `rest_framework/sets.py::_validate_serializer_nested_fields`. One helper in `inputs.py`;
   **byte-preserve the message text** so
   `tests/rest_framework/test_inputs.py:1667` and `tests/rest_framework/test_sets.py:2100`
   pass unedited. Both files carry Slice 2b's accepted comment-only edits, so `HEAD` is not
   the reference for either — Slice 2b's per-file docstring-stripped AST digest is superseded
   by this pass and the re-loop owes its own.
2. **F2**, the twice-derived provisional input-type name at
   `rest_framework/inputs.py::resolve_injected_field_specs` and
   `::build_serializer_input_class`: route both through the existing
   `utils/inputs.py::generated_input_type_name(base_name, is_partial=…, is_full_shape=True,
   token="")`, which returns the identical string. No new abstraction.

Neither finding needs a spec edit: the spec describes the messages' contract, not their
spelling, and the type-name derivation is already spec'd as one shared deriver.

**For the maintainer — contract-level, carried unchanged:**

3. **Escalation A** — should the DRY import ratchet hold the spec's **named promotions**
   (shipped), the **whole measured shared substrate**, or the `### Import manifest`
   population; and should it cover the **forms** flavor, which binds the same
   `FieldConversionBase` and has no ratchet at all. Not decided here. **Confirmed
   auditable either way:** the spec now enumerates the shipped population explicitly and it
   sums to the shipped manifest row for row (19 + 2), so "is the manifest complete under
   answer X" is answerable by reading rather than by re-running a census.
4. **Escalation B** — the `isinstance(meta, _ValidatedMutationMeta)` tightening is a
   seam-support question (whether a duck-typed `_mutation_meta` is supported at that seam).
   Decided-as-shipped in Slice 3; not re-litigated.
5. **Escalation C** — `HEAD` is red from the concurrent `spec-050` work at `4c483b6b` in four
   modules this cycle does not touch. `docs/builder/bld-039-final.md` cannot record a green
   full sweep until it is resolved. Carried, not fixed.
6. **F3**, the `f"SerializerMutation {…}"` message prefix: **70** `"SerializerMutation "`
   literals across `rest_framework/{resolvers,sets,inputs}.py` (61 f-prefixed) plus
   `utils/permissions.py`'s `family_label`. Its own card. Named home meanwhile:
   `docs/builder/bld-039-final.md`'s `### Deferred work catalog`.

**Out of fence — record only, no edit made:**

7. **`BACKLOG.md:31`** still reads
   `` (`mutations/inputs.py::FieldError`, spec-036 Decision 7 + spec-039 rev6 #4/#13) `` — a
   live stranded ordinal, and now the last `spec-039` `rev6`-vocabulary citer in the tree.
   Repair recorded by Slice 2c: `spec-039 rev6 #4/#13` → *`spec-039`'s error-envelope
   `codes` / `path` improvements*. `BACKLOG.md` is outside the maintainer-set fence.
   **Owner: the maintainer.**
8. **`spec-036`'s severity-ordinal labels: the carried figure is right in arithmetic and
   wrong in subject.** Slice 2b published **146**; measured this pass with two instruments,
   the both-bounded population is **147** occurrences over 14 distinct tokens and the
   left-bounded one is **169** — the 22-hit delta is **entirely `M2M`**, the same false
   positive this cycle has now hit three times. More important than the ±1: **31 of the 147
   are `G2` plus one `G2-handoff`**, `spec-035`'s goal vocabulary cited from `spec-036`,
   which every prior strip deliberately **kept** as foreign-spec. So `spec-036`'s **own-voice**
   population — the only figure that bears on "does it owe the same strip" — is **115**
   occurrences over 12 tokens (`H1`-`H5`, `M1`-`M7`). The maintainer is being asked about 115
   sites, not 146. **Owner: the maintainer**; whether `spec-036` gets the strip is a scope
   question.
9. **`KANBAN.md:375`'s `spec-039` inventory is discharged and the board does not know.**
   19 stranded-ordinal sites in 10 package modules, measured by the `spec-038` cycle; all 19
   are gone, and the same item's claim that `spec-039` "has no rationale companion" was
   falsified by Slice 0. Kanban DB writes are outside the fence. **Owner: the maintainer.**
10. **`examples/fakeshop/apps/kanban/constants.py` goes stale the moment
    `tests/rest_framework/test_dry_import_ratchet.py` is staged.** Verified live: `:243-248`
    lists six `tests/rest_framework/` files and not the new one, and the
    `kanban-tracked-path-constants` hook reads `git ls-files`, so a green `uvx pre-commit`
    today is `START.md`'s documented fail-open rather than coverage. Remedy at commit time:
    `uv run python scripts/build_kanban_tracked_path_constants.py` after `git add`, landed as
    a constants-only sync commit (the hook's `files:` pattern does not match that module, so
    it cannot roll itself back). **Owner: commit time.**
11. **Nine `TODO-ALPHA-040-0.0.13` card ids in this spec** name a card that is
    `DONE-040-0.0.13`. Already an owned, measured board population (`KANBAN.md:618`) whose
    ruling is that the class splits three ways with only one third mechanical. **Owner: that
    card.** Not pre-empted here.
12. **`tests/rest_framework/test_dry_import_ratchet.py:3-8`'s ragged docstring wrap** —
    cosmetic, no gate sees it, and Worker 1 may not edit tests. If Worker 0 dispatches the F1
    / F2 consolidation pass, fold the re-wrap into that diff; otherwise it stays in
    `bld-039-final.md`'s deferred catalog.

**Prior-artifact records that are now inaccurate and are deliberately left alone.** Slice 2a's
`#### E` and `#### D` change tables list the head opener and `## Definition of done` item 3
among the sites they corrected; measured, neither edit landed. Per-cycle artifacts are
records of what a pass believed when it ran and are never edited after the fact
(`START.md` "Per-cycle scratch closes w/ cycle"; `docs/builder/ARTIFACT.md`
`## Re-pass sections`). The correction of record is this artifact's `## Divergence inventory`
D1 and D4.

### Final status

`revision-needed`. Every divergence this pass found is fixed in the spec and the companion,
all three gates pass with the glossary and citation counts unchanged, the staged-anchor sweep
is clean, and the existence challenge is answered. The status is set by **F1** and **F2**:
two live DRY consolidations in `rest_framework/inputs.py` and `rest_framework/sets.py` that
Worker 1 may not implement (`docs/builder/worker-1.md` `## Scope`: no source edits) and that
`docs/builder/BUILD.md` `## Cross-slice integration pass` routes through a Worker 2
consolidation pass plus a Worker 3 review, after which this pass re-runs.

---

## Build report (Worker 2)

The F1 / F2 consolidation the integration pass routed here. **F3 was not dispatched and
was not touched.** No message text changed: every one of the seven consumer-facing strings
this pass re-homed is proved byte-identical below, and the three re-pointed type-name
derivations are proved to return the identical string.

### Files touched

Grounded in `git status --short`, diffed against copies taken **before** this pass
(`git show HEAD:` is not the reference — both source files carried Slice 2b's accepted
comment-only edits at pass start, and `resolvers.py` / `utils/querysets.py` are MIXED).

- `django_strawberry_framework/rest_framework/inputs.py` — added the single-sited
  `NESTED_STABLE_FIELDS_INSTRUCTION` constant and three shared helpers
  (`read_nested_serializer_fields`, `require_nested_fields_mapping`,
  `require_nested_serializer_config`); re-pointed `::_fingerprint_nested`,
  `::_resolve_nested_field` and `::validate_nested_config_keys` at them; re-pointed
  `::resolve_injected_field_specs`, `::build_serializer_input_class` and
  `::describe_serializer_input` at `utils/inputs.py::generated_input_type_name`.
- `django_strawberry_framework/rest_framework/sets.py` — imports the three new helpers
  from `.inputs` (the direction the per-module import manifest already permits, and the
  direction `raise_writable_source_ownership_errors` already travels); re-pointed
  `::_validate_serializer_nested_fields` (two sites) and
  `::_assert_schema_source_ownership` (one site) at them.
- `tests/rest_framework/test_inputs.py` — the prefix-only pin at
  `::test_nested_serializer_fields_access_exception_raises_configuration_error` strengthened
  to full-message equality.
- `tests/rest_framework/test_sets.py` — the prefix-only pin at
  `::test_validate_nested_fields_child_serializer_errors` strengthened the same way.
- `docs/builder/bld-039-integration.md` — this section; `Status:` set to `built`.
- `docs/builder/temp-tests/039-integration/proofs.json` + `proofs.md` (untracked scratch) —
  the failability manifest and its emitted record.

### Two population corrections, measured before editing

Both findings' site lists were re-derived rather than accepted, and both were off.

- **F1's third copy is not where the finding says it is.** The routing names
  `rest_framework/sets.py::_validate_serializer_nested_fields` as the carrier of the
  six-line `except ConfigurationError: raise / except Exception: raise
  ConfigurationError(...)` block. That block lives in
  `rest_framework/sets.py::_assert_schema_source_ownership`
  (`sets.py` #"child_fields = dict(child_serializer.fields)" at pass start).
  `_validate_serializer_nested_fields` is a real F1 site, but for the OTHER two fragments
  (the `must be a mapping of` and `must be a NestedSerializerConfig` messages). Both
  functions were consolidated; the count of fragments and of sites is unchanged, only the
  symbol name in the routing.
- **F2's provisional-name derivation is spelled four times, not twice.** Instrument: the
  shortest distinctive token, `PartialInput` as an executable literal, counted as
  occurrences over the whole package — **5 hits**, one of them the owner
  (`utils/inputs.py::generated_input_type_name` #"suffix = \"PartialInput\" if is_partial else \"Input\"").
  The four duplicates:

  | site | partial test | in this pass's fence |
  |---|---|---|
  | `rest_framework/inputs.py::resolve_injected_field_specs` | `operation_kind == PARTIAL` | yes — re-pointed |
  | `rest_framework/inputs.py::build_serializer_input_class` | `is_partial` | yes — re-pointed |
  | `rest_framework/inputs.py::describe_serializer_input` | `shape.operation_kind == PARTIAL` | yes — re-pointed |
  | `rest_framework/resolvers.py::_assert_field_agreement` | `operation == "update"` | **no** — MIXED file, outside the writable list |

  The fourth is the one that matters most and is the one this pass may not touch: it is
  the RUNTIME re-derivation whose disagreement with the schema-time provisional is the live
  failure mode the finding describes, it spells the partial test a third way, and it sits on
  the per-request path. Routed to Worker 1 below.

### Tests added or updated

No new test row. Two existing rows strengthened from a shared-prefix `match=` to full-message
equality — the exact gap the finding names ("either tail can drift silently and no test would
notice"):

- `tests/rest_framework/test_inputs.py::test_nested_serializer_fields_access_exception_raises_configuration_error`
  — pins the whole message the input build publishes, aggregation prefix (`child: `) included.
- `tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors`
  — pins the whole message the schema-time ownership walk publishes.

Between them they pin the complete text of `NESTED_STABLE_FIELDS_INSTRUCTION` from **both**
call sites of the shared reader, in both consuming modules. The failability entries below
show these are the only two rows in either suite that can see a tail drift.

### Byte-identity proof of every relocated message

`docs/builder/BUILD.md` `## Claims are proven mechanically` — "I only moved it" proved by
execution, not by reading. An instrument outside the repo drives all **seven** message sites
and the four type-name witnesses, capturing each string exactly; it was run against the tree
**before** the edit and again after.

Sites captured (label -> raising symbol):

| label | site |
|---|---|
| F1-a | `rest_framework/inputs.py::_fingerprint_nested` (via `serializer_schema_fingerprint`) |
| F1-b | `rest_framework/inputs.py::_resolve_nested_field` (via `build_serializer_input_class`) |
| F1-c | `rest_framework/sets.py::_assert_schema_source_ownership` |
| F1-d | `rest_framework/inputs.py::validate_nested_config_keys` — non-mapping |
| F1-e | `rest_framework/inputs.py::validate_nested_config_keys` — wrong config type |
| F1-f | `rest_framework/sets.py::_validate_serializer_nested_fields` — non-mapping |
| F1-g | `rest_framework/sets.py::_validate_serializer_nested_fields` — wrong config type |
| F2-a/b | generated type name + the choice-enum name derived from the provisional, and `describe_serializer_input`'s canonical-vs-derived verdict, for create AND partial |
| F2-c | `resolve_injected_field_specs`'s emitted `annotation_repr` (the enum name is the provisional's witness), create AND partial |
| F2-d | inline-vs-helper derivation over a 4 base names x 2 partial-flag matrix |

```
cmp messages-before.txt messages-after.txt   -> exit 0
wc -c: 4097 == 4097
md5:   653c723dd393344f917a5d6f67be8f95 (identical)
```

**The instrument carries its own negative control**, because a comparison that cannot fail is
indistinguishable from one that passed. With the tree in its post-edit state, one clause of
`NESTED_STABLE_FIELDS_INSTRUCTION` was transiently altered (`.fields` -> `.FIELDS`); anchor
asserted to match exactly once BEFORE the copy was taken:

```
grep -c 'request-independent no-arg .fields (override get_serializer_for_schema() on the ' \
    django_strawberry_framework/rest_framework/inputs.py     -> 1
cmp messages-before.txt messages-control.txt  -> exit 1, "differ: char 322, line 2"
diff | grep -c '^[<>]'                        -> 6   (3 changed lines, both sides)
```

Three sections moved, which is the independent confirmation that all three sentence sites now
flow from the one constant. Reverted from the pre-mutation copy and the revert proved:
`cmp django_strawberry_framework/rest_framework/inputs.py <copy>` -> exit 0.

### Validation run

- `uv run ruff format <the four files this pass touched>` — **pass** (`2 files left
  unchanged` on each of the two invocations; source and tests run separately). Scoped, never
  `.`.
- `uv run ruff check --fix <the same four files>` — **pass** (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py <the same four files>` — **pass**
  (`Fixed 0 file(s).`), explicit paths.
- `uv run python scripts/check_citations.py --check` — **pass**,
  `OK: 965 citations resolve (810 in 442 .py files, 155 in KANBAN.md)`. The integration pass
  recorded 963; the +2 are this pass's two new docstring `path::Symbol` references, and both
  resolve.
- `git status --short` after both ruff invocations, differenced against the list captured at
  pass start: **exactly one line added**, `M tests/rest_framework/test_inputs.py`. The other
  three files this pass edited were already dirty at pass start. **No unexpected churn, so
  nothing to stop-and-report and nothing reverted.** Everything else dirty is the concurrent
  `spec-050` session's or a prior slice's, untouched (`AGENTS.md` rule 34); `git stash` /
  `checkout` / `restore` / `worktree` were not used anywhere in this pass.
- Focused runs, no `--cov*` flag anywhere:
  - `uv run pytest tests/rest_framework/ tests/mutations/ tests/utils/test_inputs.py tests/forms/ --no-cov`
    — **1221 passed**. The sibling scope is deliberate: `sets.py` now imports three more
    symbols from `.inputs`, and `forms/` + `mutations/` are the other two flavors riding the
    same substrate.
  - `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov`
    — **195 passed**. The live tier is where a serializer mutation is actually driven.
- Test-staleness sweep (`docs/builder/BUILD.md` `### Test staleness a focused run cannot
  see`): **not owed**. This pass changes no example-model field set and no wire shape — the
  SDL is byte-identical by the F2-a/F2-b captures above.

### Failability proofs

Two entries, both run through `uv run python scripts/prove_failability.py
docs/builder/temp-tests/039-integration/proofs.json --output
docs/builder/temp-tests/039-integration/proofs.md`; **exit 0**. The tool asserts each anchor
matches exactly once before taking its copy, runs the scope unmutated first, and proves each
restore by `filecmp.cmp(shallow=False)` plus SHA-256. Full emitted record on disk at
`docs/builder/temp-tests/039-integration/proofs.md`.

Entry 1 is the proof owed for the strengthened assertions; entry 2 proves the boundary the
consolidation single-sited is pinned from both of its call sites.

- `django_strawberry_framework/rest_framework/inputs.py::NESTED_STABLE_FIELDS_INSTRUCTION` —
  **mutation applied:** the constant's closing clause altered
  (`"mutation to return a stable field map)."` ->
  `"mutation to return a stable field map). Drifted tail."`), so every site publishing the
  sentence drifts at the TAIL while the shared prefix the old assertions matched is untouched;
  **scope as run:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE
  tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py`;
  **pre-mutation state of that scope:** green — `189 passed`, pytest exit 0, 0 pre-existing
  failing rows differenced out; **failing node ids:**
  `tests/rest_framework/test_inputs.py::test_nested_serializer_fields_access_exception_raises_configuration_error`,
  `tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors`;
  **collection/setup errors:** 0 (pytest exit 1, a valid count);
  **revert proved by byte-comparison:** `filecmp.cmp(shallow=False)` True and
  `sha256 4d7b61b9e6b9ba04... == 4d7b61b9e6b9ba04...` against the pre-mutation copy.
- `django_strawberry_framework/rest_framework/inputs.py::read_nested_serializer_fields` —
  **mutation applied:** the whole `except Exception as exc: raise ConfigurationError(...) from
  exc` translation replaced by `except Exception: raise`, so an unreadable nested `.fields`
  leaks the raw consumer exception instead of the typed configuration error (the boundary is
  removed, not perturbed); **scope as run:** identical to entry 1;
  **pre-mutation state of that scope:** green — `189 passed`, pytest exit 0, 0 rows
  differenced out; **failing node ids:**
  `tests/rest_framework/test_inputs.py::test_nested_serializer_fields_access_exception_raises_configuration_error`,
  `tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors`;
  **collection/setup errors:** 0 (pytest exit 1);
  **revert proved by byte-comparison:** same, exit-0 byte compare.

Neither entry is zero-row, so no **why 0** judgement is owed. Both sit at 2 rows — above the
weakly-pinned threshold and inside Worker 3's mandatory independent re-run floor; re-run at
the scope recorded above and compare node-id **sets**, not counts.

The two entries returning the identical node-id pair is itself the finding's measurement: in
two whole test modules, exactly two rows can observe this message text at all, and before this
pass both of them saw only its prefix.

### Hot-path budget

**Not applicable; plan declares no hot path for this pass — and the judgement was made rather
than inherited.** Every call this pass added or re-pointed was traced to its phase:

| call added / re-pointed | reached from | phase |
|---|---|---|
| `read_nested_serializer_fields` (2 sites) | `_resolve_nested_field`; `_assert_schema_source_ownership` <- `_validate_meta` | input build / class creation |
| `require_nested_fields_mapping`, `require_nested_serializer_config` (4 sites) | `validate_nested_config_keys`; `_validate_serializer_nested_fields` <- `_validate_meta` | input build / class creation |
| `generated_input_type_name` (3 sites) | `resolve_injected_field_specs` <- `_validate_meta`; `build_serializer_input_class` <- `_serializer_input_shape_for`; `describe_serializer_input` (diagnostic, reached from a materialize-collision error or a consumer call) | class creation / schema build / diagnostic |

None runs per request, per resolver, per row, per connection or per outbound message.
`_validate_meta` runs once per mutation class at import; the input build runs once per shape
behind the shape cache. The added cost is one Python call per site at schema-build time, which
this pass does not attempt to quantify because it is not on a measured path.

The one derivation of this string that **is** per-request —
`rest_framework/resolvers.py::_assert_field_agreement`, once per write-surface field per
mutation invocation — was **not touched** (out of fence), so this pass adds nothing to it and
removes nothing from it. It is routed to Worker 1 below on correctness grounds, not cost.

### Floor verification

Run, though the plan's declaration scopes the obligation to Slice 3. The declaration's own
words are that "any change inside `rest_framework/resolvers.py` or `rest_framework/sets.py`
touches the DRF / Strawberry integration seam and owes a focused floor run", and this pass
changes `rest_framework/sets.py`. Running it costs minutes and removes the "a planned floor
verification no pass ran" failure mode; the shared `.venv` was never mutated.

- scratch venv (outside the repo): `<session scratchpad>/dsf-floor`, built with
  `uv venv … --python 3.10`, then `uv pip install --python <venv>/bin/python -e . --group dev`
  and `uv pip install --python <venv>/bin/python 'django==5.2.16'
  'strawberry-graphql==0.316.0'` — the floor `docs/builder/BUILD.md` `## Floor verification`
  records, taken from there and not restated from memory.
- resolved versions as read by `uv pip list --python <venv>/bin/python`: Python **3.10.19**,
  `django 5.2.16`, `strawberry-graphql 0.316.0`, `djangorestframework 3.18.0`,
  `django-filter 26.1`, `pytest 9.1.1`, `pytest-django 4.14.0`.
- focused scope: `<venv>/bin/python -m pytest tests/rest_framework/ --no-cov -q
  -p no:cacheprovider` — **pass, 497 passed**.

### Implementation notes

- **Four shared fragments, three shared pieces — not one helper per fragment.** The routing
  says "one module-level raise/message helper". Measured, the two byte-identical `Could not
  read .fields` sites are not just a shared message but a shared six-line
  read-and-translate BLOCK, so the DRYer shape is a helper that owns the **read**
  (`read_nested_serializer_fields`) rather than one that only owns the raise: it retires the
  duplicated `try` / `except ConfigurationError: raise` / `except Exception` scaffolding as
  well as the string. The two `Meta.nested_fields` type rejections likewise duplicate their
  `isinstance` predicate along with their message, so they became `require_*` guards rather
  than bare raisers — matching the `require_one_segment_source` / `require_subclass` /
  `require_model_class` naming already in this subpackage.
- **The instruction sentence stayed a constant, not a helper.** Its third site
  (`_fingerprint_nested`) deliberately publishes a DIFFERENT prefix — it names the determinism
  fingerprint, not the input build — and that distinction is load-bearing at class validation.
  Only the closing instruction is shared, so only the closing instruction was single-sited.
  Folding the fingerprint's raise into `read_nested_serializer_fields` would have required
  parameterizing the prefix, which buys nothing and hides the message at its raise site.
- **`read_nested_serializer_fields` derives the class name internally** (`type(serializer)`)
  rather than taking it as an argument. Both former sites computed exactly
  `type(child_serializer)`, so this removes the one identifier the two copies differed in
  (`child_class` vs `nested_class`) instead of preserving it as a parameter that could be
  passed inconsistently.
- **The three `generated_input_type_name` calls each pass `is_full_shape=True, token=""`
  inline** rather than through a new one-line wrapper. The routing is explicit that no new
  abstraction is warranted, and `rest_framework/inputs.py::serializer_input_type_name` already
  calls the same helper the same way, so the file now has one spelling of the derivation
  rather than one plus three.
- **The audit was wrong and the integration pass was right about
  `generated_input_type_name`.** Verified independently rather than taken from either: read at
  the working tree its body is `suffix = "PartialInput" if is_partial else "Input"` then
  `if is_full_shape: return f"{base_name}{suffix}"`, and the F2-d matrix executes both
  spellings over 8 (base, partial) pairs with `equal=True` on every row.
- **Owner-name asymmetry preserved, not fixed.** `require_nested_fields_mapping` /
  `require_nested_serializer_config` render `SerializerMutation {owner_name}.Meta…`, and the
  two callers pass different things: `sets.py` passes the MUTATION class name, `inputs.py`
  passes the SERIALIZER class name. That is pre-existing behavior, visible in the F1-d/F1-e vs
  F1-f/F1-g captures (`PlainParent` vs `M`), and changing it would be a behavior change wearing
  a consolidation's diff. Recorded for Worker 1 below; not touched here.

### Notes for Worker 3

- **Re-run scope for the failability audit:** `tests/rest_framework/test_inputs.py
  tests/rest_framework/test_sets.py`, exactly as recorded. Both entries are at 2 rows, inside
  the mandatory floor, so both are re-runnable; compare node-id sets.
- **The byte-identity instrument is not in the repo** (it drives Django and imports the
  package, so it is a measuring script, not a test). It lives in the session scratchpad
  alongside `messages-before.txt` / `messages-after.txt` / `messages-control.txt`. To
  re-derive independently: exercise the seven sites in the table above and compare against a
  copy of the pre-pass files. The negative control above is what shows the comparison can
  fail.
- **No `__init__.py` re-export changed.** `git diff -- django_strawberry_framework/__init__.py`
  is empty for this pass; the three new helpers are subpackage-internal and are imported only
  by `rest_framework/sets.py`.
- `scripts/review_inspect.py` was **not run by this pass** — Worker 2's use of it is
  discretionary (`docs/builder/worker-2.md` `## Static helper use`) and refreshed AST output
  would not have changed a three-helper extraction. **Your trigger does fire**, so run it:
  measured line deltas against the pre-pass copies are `rest_framework/inputs.py` **+87 / -29**
  (net +58, of which roughly a third is the constant's comment and the three new docstrings)
  and `rest_framework/sets.py` **+6 / -21** (net -15). That clears
  `docs/builder/BUILD.md` `### When to run the helper during build`'s "adds 30+ lines of new
  logic to any file under `django_strawberry_framework/`" threshold for `inputs.py`. No new
  `.py` file was added and nothing under `optimizer/` or `types/` was touched.
- **Net effect on the repeated-literal census the integration pass ran:** the four
  cross-module fragments it measured are now one site each. Re-running that instrument should
  report **0** literals of >= 25 characters and >= 4 words shared between
  `rest_framework/inputs.py` and `rest_framework/sets.py`. The two `resolvers.py` intra-module
  fragments and the `serializer_converter.py` triple are F3 / audit-1c territory and are
  untouched.

### Notes for Worker 1 (spec reconciliation)

No spec edit is owed by the consolidation itself — the spec describes the messages' contract,
not their spelling, and the type-name derivation is already spec'd as one shared deriver.
Four items for the custodian, in descending order of consequence:

1. **F2 is two-thirds retired, and the remaining third is the per-request one.**
   `rest_framework/resolvers.py::_assert_field_agreement` #"'PartialInput' if operation ==
   'update' else 'Input'" is a fourth inline spelling of the derivation, with a THIRD partial
   test (`operation == "update"`, where the schema-time sites use `operation_kind == PARTIAL`
   and `is_partial`). It is the runtime half of the very pair F2 says "must agree", it runs
   per write-surface field per mutation invocation, and `resolvers.py` is a MIXED file outside
   this pass's writable list, so it could not be touched here.
   **Recommended replacement** for the F2 entry in `### Findings that need Worker 2`, whose
   current wording is *"the provisional input-type name is derived twice"*: **the provisional
   input-type name is derived four times outside its owner — three at schema time in
   `rest_framework/inputs.py` and once per request in
   `rest_framework/resolvers.py::_assert_field_agreement`, the last spelling the partial test a
   third way.** Route the resolvers site to a pass that owns that file.
2. **F1's third-copy site name is wrong in `### DRY findings` and in
   `### Notes for Worker 1` item 1.** Current wording: *"`rest_framework/sets.py::_validate_serializer_nested_fields`
   carries a **third** copy — a six-line `except ConfigurationError: raise / except Exception:
   raise ConfigurationError(...)` block"*. **Recommended replacement:**
   *"`rest_framework/sets.py::_assert_schema_source_ownership` carries a **third** copy — a
   six-line … block"*, leaving `_validate_serializer_nested_fields` named as the carrier of the
   other two fragments (the `must be a mapping of` and `must be a NestedSerializerConfig`
   messages). The fragment table itself is correct; only the symbol attribution is not. Per
   `docs/builder/ARTIFACT.md` `## Re-pass sections` this pass did not edit the prior section —
   the correction of record is here.
3. **The DRY import ratchet's manifest does not cover `generated_input_type_name`, which this
   pass made load-bearing at three more sites.** `tests/rest_framework/test_dry_import_ratchet.py`
   #"SHARED_BINDINGS" carries 19 rows and none of them is `generated_input_type_name`, though
   `rest_framework/inputs.py` imports it from `utils/inputs.py` and now routes four call sites
   through it. Whether it earns a row is exactly the scope question `Escalation A` puts to the
   maintainer (named promotions vs. the whole measured shared substrate), so this pass added no
   row: the test file is outside its writable list, and pre-empting the escalation would decide
   it. **No recommended spec wording** — this one belongs to `Escalation A`'s answer, and it is
   named here so the answer has one more concrete row to weigh.
4. **The two `Meta.nested_fields` type rejections render a different subject on each side of
   the same sentence.** `SerializerMutation {X}.Meta.nested_fields must be a mapping…` renders
   the MUTATION class name from `rest_framework/sets.py` and the SERIALIZER class name from
   `rest_framework/inputs.py` — both pre-existing, both preserved byte-for-byte here because
   changing one would be a behavior change hidden inside a consolidation
   (`docs/builder/BUILD.md`: not a behavior change). It is a real, small consumer-facing
   inconsistency: the same `SerializerMutation <name>` slot names two different classes
   depending on which depth of the opt-in tree rejected. Worth a decision; not worth a silent
   fix.

---

## Review (Worker 3)

Reviewing the F1 / F2 consolidation in `## Build report (Worker 2)`. Worker 2's diff, by
content: `django_strawberry_framework/rest_framework/inputs.py`,
`django_strawberry_framework/rest_framework/sets.py`, `tests/rest_framework/test_inputs.py`,
`tests/rest_framework/test_sets.py`. Every other dirty path was attributed by diff content and
excluded — the label-strip hunks inside those same two source files (`P2.2`, `Md5`, `M2 / High`,
`H3`, `D8`, `D1`, `P1.7`, `P2.7`, `Medium`) are Slice 2b's accepted work, and the
`spec-050` cycle's modules were not opened.

### Failability mutations recorded BEFORE they were made

`docs/builder/worker-3.md` `## Scope` requires the record to precede the mutation. Both
entries are at 2 rows in Worker 2's record, so both are inside the mandatory re-run floor and
the subset is **all of them**. Both mutation SHAPES are deliberately different from Worker 2's,
so a shape-specific blind spot in its instrument cannot survive into mine.

Preconditions asserted first: no `ACTIVE-MUTATION.json` anywhere in the tree; each anchor
matches exactly once; `shasum -a 256 django_strawberry_framework/rest_framework/inputs.py` =
`4d7b61b9e6b9ba046287f99f2632ed947a68abf4249a236854f38edb1b46a953` — whose leading
`4d7b61b9e6b9ba04` is byte-for-byte Worker 2's recorded restore digest, which corroborates that
both passes mutated the same pristine bytes (a check row counts alone cannot make).

1. `rest_framework/inputs.py::NESTED_STABLE_FIELDS_INSTRUCTION` — mutate an **interior** clause
   of the sentence (`.fields` -> `.FIELDS`), not the closing clause Worker 2 appended to. A
   drift past the shared prefix but *before* the tail is the case an assertion could still miss
   if it only pinned prefix and tail.
2. `rest_framework/inputs.py::read_nested_serializer_fields` — delete the **whole** read-or-reject
   boundary (the `try` / `except ConfigurationError: raise` / `except Exception` translation) and
   leave the bare `return dict(serializer.fields)`. Worker 2's `except Exception: raise` keeps the
   scaffolding; this removes it.

Manifest: `docs/builder/temp-tests/039-integration/w3-proofs.json`, run through
`scripts/prove_failability.py`, one boundary at a time, restore proved by byte comparison.

### Independent re-derivations, before the findings

Every claim below was re-measured rather than read, and every instrument carries a control,
because a comparison that cannot fail is indistinguishable from one that passed.

**F1's population correction is right, and the integration pass's attribution was wrong.**
Read at `HEAD` (`git show HEAD:` into a scratch path outside the repo; no `stash` /
`checkout` / `restore` / `worktree` anywhere in this pass), the six-line
`except ConfigurationError: raise` / `except Exception` read-and-translate block sits at
`sets.head.py:444`, inside `_assert_schema_source_ownership` — not inside
`_validate_serializer_nested_fields`, which carried the OTHER two fragments
(`sets.head.py:324` the mapping rejection, `:361` the config-type rejection). Worker 2's
correction of record is accurate in both halves.

**F1's four cross-module fragments are retired to zero.** Re-ran the integration pass's own
census as a fresh AST instrument (non-docstring `str` constants, >= 25 characters and
>= 4 words, over all six `rest_framework/` modules, keyed by value):

| run | cross-module shared literals | intra-`inputs.py` repeats |
|---|---|---|
| positive control, the two files at `HEAD` | **4** — exactly the four fragments the pass tabled | **1** (the instruction sentence, 2x) |
| working tree, post-consolidation | **0** | **0** |

The three literals that still repeat within one module are
`serializer_converter.py` #"Registered serializer-field converter for " (3x) and two
`resolvers.py` fragments (2x each) — F3 / audit-1c territory, untouched, as intended.
`scripts/review_inspect.py --output-dir docs/shadow` was run on
`rest_framework/inputs.py` (its "adds 30+ lines" trigger fires at +103/-45); its
**Repeated string literals** section no longer lists the instruction sentence at all, and
what remains is the `SerializerMutation` prefix (14x) F3 owns.

**F2 is derived four times, not two — verified, and three of the four are retired.** Census:
executable (non-docstring) `str` constants containing `PartialInput`, over the whole package.

| run | population |
|---|---|
| the two files at `HEAD` | `inputs.head.py` **3** (`:775` `resolve_injected_field_specs`, `:871` `describe_serializer_input`, `:1639` `build_serializer_input_class`); `sets.head.py` **0** |
| whole package, working tree | **2** — `utils/inputs.py:1015` (the owner) and `resolvers.py:1213` (`_assert_field_agreement`) |

So five sites at `HEAD`, one of them the owner; four duplicates, three retired. The
integration pass's "derived twice" missed `describe_serializer_input` and the resolvers
site; Worker 2's re-derivation is right, and the site it identifies as the one that matters
most — per-request, third spelling of the partial test, MIXED file outside the writable list
— is confirmed present and untouched (`git diff -- rest_framework/resolvers.py` contains no
hunk naming `PartialInput`, `generated_input_type_name`, or any of the three new helpers).

**Byte identity of every relocated message, re-derived at a wider population than Worker 2's
seven sites.** Instrument: render **every** `ConfigurationError(...)` first argument in both
modules from the AST into a template, inlining module-level `str` constants by value and
normalising only renamed receivers and parameters (`type(serializer).__name__` /
`child_class.__name__` / `nested_class.__name__` -> one token; `owner_name` / `name` /
`serializer_class.__name__` -> one token; the loop key and the `_safe_arg_repr` argument
likewise). Compare the SET across both files, so a message MOVING from `sets.py` to
`inputs.py` is invisible while a reworded one is not.

```
HEAD messages: 31   working: 31   SET EQUAL: True
lost: []   added: []
```

Negative control, on a copy taken **outside** the repo (the repo was never mutated for this
check): anchor asserted to match exactly once, then one clause of
`NESTED_STABLE_FIELDS_INSTRUCTION` altered (`.fields` -> `.FIELDS`):

```
NEGATIVE CONTROL - SET EQUAL: False    lost 2, added 2
  + ...get_serializer_for_schema() on the mutation to return a stable field map). Drifted.
```

Two templates move because `inputs.py` holds two sites that publish the sentence; the third
is in `sets.py`, which the control left alone. The comparison can fail, so its passing is
evidence. Worker 2's own instrument (seven driven sites, `cmp` exit 0, 4097 bytes, identical
md5, control differing at char 322) is corroborated at a strictly wider population: **31
distinct message templates**, not seven, with zero lost and zero added.

The two receiver renames are byte-safe rather than merely plausible:
`_resolve_nested_field` #"nested_class = type(child_serializer)" and
`_assert_schema_source_ownership` #"child_class = type(child_serializer)" both bind the class
the helper now derives internally as `type(serializer)`, so the `!r` name is the same object's
in all three spellings.

**The type-name re-point is a textual identity, not an approximation.**
`utils/inputs.py::generated_input_type_name` reads `suffix = "PartialInput" if is_partial
else "Input"` then `if is_full_shape: return f"{base_name}{suffix}"`, so with
`is_full_shape=True, token=""` it returns `f"{base_name}{suffix}"` — character-for-character
the three retired inline spellings. Worker 2's F2-d 8-row matrix is confirmed by reading the
owner's body.

**Failability re-run: node-id SETS matched, at Worker 2's recorded scope.** Both recorded
entries are at 2 rows, so both are inside the mandatory floor and the re-run subset is **all
of them** — nothing was accepted on Worker 2's record alone. Both mutation shapes were
deliberately different from Worker 2's (interior clause instead of appended tail; whole
boundary deleted instead of `except Exception: raise`), so a shape-specific blind spot could
not survive into this pass.

| entry | Worker 2 | this pass | node-id set |
|---|---|---|---|
| `inputs.py::NESTED_STABLE_FIELDS_INSTRUCTION` | 2 rows, 0 errors, pre-mutation `189 passed` | **2 rows, 0 errors**, pre-mutation `189 passed` | **identical** |
| `inputs.py::read_nested_serializer_fields` | 2 rows, 0 errors, pre-mutation `189 passed` | **2 rows, 0 errors**, pre-mutation `189 passed` | **identical** |

Both sets are
`tests/rest_framework/test_inputs.py::test_nested_serializer_fields_access_exception_raises_configuration_error`
and
`tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors`.
The two entries returning the same pair is not the suspicious coincidence it looks like: in
those two whole modules exactly two rows can observe this message text at all, which is the
finding's own measurement. Restores proved by `filecmp.cmp(shallow=False)` plus SHA-256; the
target's digest `4d7b61b9e6b9ba04...` was identical before the first mutation, between
entries, and after the last, and its leading bytes match Worker 2's recorded restore digest —
corroboration that both passes mutated the same pristine bytes, which row counts alone cannot
give. No `ACTIVE-MUTATION.json` exists anywhere in the tree, and
`git diff --stat -- rest_framework/inputs.py` reads `103 insertions, 45 deletions` after the
run, exactly as before it.

**Hot-path judgement: verified, no number owed.** Traced every re-pointed call to its only
callers rather than accepting the table. `_assert_schema_source_ownership` is called from
`_validate_meta` #"_assert_schema_source_ownership(" and recursively from itself — nowhere
else in the package or the tests. `resolve_injected_field_specs` has exactly one caller
(`sets.py` #"cls._injected_field_specs = resolve_injected_field_specs("), on the bind seam.
`build_serializer_input_class` is called from `sets.py::build_input`, from
`_resolve_nested_field`, and from the canonical-name re-walk — all schema-build. No module on
the per-request path (`rest_framework/resolvers.py`) imports or calls any of the three new
helpers or `generated_input_type_name`. The one per-request derivation stays in
`resolvers.py::_assert_field_agreement`, unaltered.

**Citations 963 -> 965, both attributable and both resolving.** `uv run python
scripts/check_citations.py --check` -> `OK: 965 citations resolve (810 in 442 .py files, 155
in KANBAN.md)`. Attributed by differencing citation tokens against the `HEAD` copies rather
than by trusting the delta: `inputs.py` 15 -> 17, `sets.py` 4 -> 4, and the two added are
`rest_framework/sets.py::_assert_schema_source_ownership` and
`rest_framework/sets.py::_validate_serializer_nested_fields`. Both name the DEFINING symbol
(`sets.py:396` and `sets.py:314` respectively), not a caller.

**No process provenance in the new code.** Swept the 150 added lines across all four files
for severity labels, worker / round / finding numbering, slice numbers, DRY-pass vocabulary,
`previously`, and `as of 0.0.N`: **0 hits**. Positive control — the same pattern over the 89
removed lines fires **24** times (`M2` 4, `High` 4, `H3` 4, `P2.7` 3, `P1.7` 2, `Medium` 2,
`D8` 2, `P2.2`, `Md7`, `Md5`, `Md1`, `F1`, `D1`), which is Slice 2b's label strip and
confirms the instrument can see what it is looking for. The surviving `spec-039` pointers in
the new comments are `START.md`-kept vocabulary (spec decision pointers), not provenance.

**Focused runs re-run, not read.** `uv run pytest tests/rest_framework/ tests/mutations/
tests/utils/test_inputs.py tests/forms/ --no-cov` -> **1221 passed**;
`uv run pytest examples/fakeshop/test_query/test_products_api.py
examples/fakeshop/apps/products --no-cov` -> **195 passed**. Both figures match Worker 2's
exactly. `uv run ruff format --check` and `uv run ruff check` over the four files, read-only
and scoped: `4 files already formatted`, `All checks passed!`.

**Tree condition.** Confirmed only what the dispatch asks: `grep -l rest_framework` over the
four `spec-050` red files (`tests/test_list_field.py`, `tests/utils/test_querysets.py`,
`tests/orders/test_sets.py`, `examples/fakeshop/test_query/test_list_field_api.py`) returns
**nothing** — no traceback in that population can name a file in Worker 2's diff.

### High:

None.

### Medium:

#### The consolidated helper's pass-through arm is pinned by a substring `match=` that survives its removal — 0 rows

`django_strawberry_framework/rest_framework/inputs.py::read_nested_serializer_fields` has two
arms. Worker 2 proved the `except Exception` **translation** arm at 2 rows. The
`except ConfigurationError: raise` **pass-through** arm — whose contract the new docstring
states outright, *"A ``ConfigurationError`` raised from deeper in the nested tree propagates
UNWRAPPED, so a specific nested config error is never shadowed by this one"* — is pinned by
nothing that can detect its absence.

Measured, not reasoned. Removing ONLY that arm and leaving the translation in place:

```
scope:  uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE \
          tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py
pre-mutation: 189 passed (exit 0), 0 rows differenced out
mutant:       189 passed (exit 0)   -> failing node ids: NONE
rows failed:  0     collection/setup errors: 0
restore:      filecmp.cmp(shallow=False) True; sha256 4d7b61b9e6b9ba04... == 4d7b61b9e6b9ba04...
```

**Why 0: weakly pinned, not harness-impossible.** The harness exhibits the case fine — three
existing rows drive it. The two rows that should catch it use a SUBSTRING `match=`, and with
the arm gone the specific message is *wrapped inside* the generic one, so the substring is
still present and the regex still matches. The two sites are three lines apart from the two
assertions this very pass strengthened:

```tests/rest_framework/test_sets.py:2092
    with pytest.raises(ConfigurationError, match="Explicit config error in child fields"):
        class _Mut1(SerializerMutation):   # BrokenConfigChild raises ConfigurationError
    ...
    with pytest.raises(ConfigurationError) as exc:      # <- strengthened this pass
        class _Mut2(SerializerMutation):   # BrokenExcChild raises RuntimeError
```

```tests/rest_framework/test_inputs.py:1755
    with pytest.raises(ConfigurationError, match="Explicit config error in child fields"):
        build_serializer_input_class(Parent, operation_kind="create", ...)
```

This is the same defect the pass exists to close, in the same test function, left in place:
Worker 2 strengthened the `RuntimeError` block of
`test_validate_nested_fields_child_serializer_errors` and left the `ConfigurationError` block
above it matching a substring. It matters more after the consolidation than before it, because
the two copies of this arm became **one** — `sets.py`'s copy is gone, so both modules' nested
reads now depend on the single unpinned arm in `inputs.py`.

**Recommended change, with the exact expected text measured rather than guessed** (temp test
`docs/builder/temp-tests/039-integration/test_w3_arm_messages.py` captured each site's real
message):

- `tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors`,
  first block -> `assert str(exc.value) == "Explicit config error in child fields"`
- `tests/rest_framework/test_inputs.py::test_build_nested_serializer_spec_child_fields_configuration_error`
  -> `assert str(exc.value) == "child: Explicit config error in child fields"` (the
  aggregation prefix the input build adds is real and measured)

**The fix is proven distinguishing, not merely proposed.** Re-ran the same arm-removal mutation
with those two assertions present as temp rows:

```
rows failed: 2   (was 0)    collection/setup errors: 0    pre-mutation 192 passed
  docs/builder/temp-tests/039-integration/test_w3_arm_strengthened.py::test_sets_path_arm_is_unwrapped
  docs/builder/temp-tests/039-integration/test_w3_arm_strengthened.py::test_inputs_path_arm_is_unwrapped
restore: sha256 identical
```

2 rows clears the weakly-pinned threshold. Both files are already in this pass's writable
list, so the change is one line in each and needs no spec context.

### Low:

#### `_fingerprint_nested`'s own pass-through arm is unpinned the same way — out of the consolidation's fence, one line to close

`rest_framework/inputs.py::_fingerprint_nested` keeps its own copy of the arm (deliberately —
its prefix names the determinism fingerprint, and Worker 2's implementation note gives the
right reason for not parameterising it). Its pinning row,
`tests/rest_framework/test_inputs.py::test_fingerprint_propagates_nested_configuration_error_unwrapped`,
uses `match="a specific nested config error"`, which the double-wrap also survives. Measured:
removing that arm alone fails **0** rows, 0 collection errors, pre-mutation `189 passed`,
restore proved by SHA-256. Recommended:
`assert str(exc.value) == "a specific nested config error"` (measured). Graded Low rather than
Medium because that arm was neither consolidated nor touched by this pass; it is named here
because it is one line in a file the pass already owns and the same reading found it.

#### F3's published population moved as a side effect of F1, so the deferred catalog's figure is now stale

F1 retired two `f"SerializerMutation {…}"` sites from `sets.py`. Measured with the integration
pass's own two patterns, against the `HEAD` copies and the working tree:

| pattern | `inputs.py` | `sets.py` | `resolvers.py` | total |
|---|---|---|---|---|
| `f"SerializerMutation {`, `HEAD` | 5 | 16 | 40 | **61** |
| `f"SerializerMutation {`, now | 5 | **14** | 40 | **59** |
| `"SerializerMutation "`, `HEAD` | 14 | 16 | 43 | **73** |
| `"SerializerMutation "`, now | 14 | **14** | 43 | **71** |

No F3 work was done and no F3 site was edited — the reduction is purely F1's consequence. But
`### Notes for Worker 1` item 6 and the artifact's `### Summary` both publish **70** for the
second pattern, which measures **73** at `HEAD` and **71** now, so the figure carried to
`bld-039-final.md`'s `### Deferred work catalog` is wrong in the third digit and about to go
stale in the second. Recommend the catalog carry the post-consolidation figure with its
pattern stated as a parameter (`START.md`: state the PATTERN as a parameter of any published
figure).

### DRY findings

- **F1 discharged in full, verified against a controlled census.** 4 cross-module fragments ->
  **0**; the intra-`inputs.py` duplicate of the instruction sentence -> **0**. The positive
  control at `HEAD` reproduces the integration pass's own 4 and 2 exactly, so the zero is a
  measurement and not an empty grep.
- **F2 discharged for three of its four duplicates.** The fourth
  (`resolvers.py::_assert_field_agreement`) is correctly out of fence and correctly routed to
  Worker 1; the per-request placement and the third spelling of the partial test are both
  confirmed.
- **F3 untouched, as contracted.** No hunk in `resolvers.py`'s dirty diff names the prefix,
  the helpers, or `generated_input_type_name`.
- **Existence challenge on the four new module-level names: all four should exist.** Grepped
  the readers rather than assuming, population printed:

  | name | live callers | where |
  |---|---|---|
  | `NESTED_STABLE_FIELDS_INSTRUCTION` | 2 reads | `read_nested_serializer_fields`, `_fingerprint_nested` |
  | `read_nested_serializer_fields` | 2 | `inputs.py::_resolve_nested_field`, `sets.py::_assert_schema_source_ownership` |
  | `require_nested_fields_mapping` | 2 | `inputs.py::validate_nested_config_keys`, `sets.py::_validate_serializer_nested_fields` |
  | `require_nested_serializer_config` | 2 | the same two |

  None is the one-real-caller indirection `docs/builder/worker-3.md` `### The existence
  challenge` hunts, and none is the dead constant/helper pair whose fix is deletion: each has
  a live caller in **each** of the two modules, which is exactly the duplication being
  retired. Four names for four duplications is a 1:1 trade with no surplus abstraction, and the
  alternative — one parameterised raiser — was correctly rejected in the implementation notes
  (folding `_fingerprint_nested`'s different prefix in would have required passing the prefix,
  hiding the message from its raise site).

- **Single responsibility, judged per helper.** `read_nested_serializer_fields` owns read +
  translate, which is one responsibility because the two are inseparable — the translation
  exists only to name the read's failure, and splitting them would leave the `try` scaffolding
  duplicated, which is half of what F1 measured. The two `require_*` guards own
  predicate + message, which is the shape this subpackage already uses
  (`mutations/sets.py::require_subclass`, `::require_model_class`,
  `serializer_converter.py::require_one_segment_source`, `sets_mixins.py::require_re_readable_field_declaration`),
  so the naming is precedent-following rather than invented.
- **Import direction is the one the package already uses.** `sets.py` already imported 15
  symbols from `.inputs` at `HEAD`, `raise_writable_source_ownership_errors` among them; the
  three new names were added to that existing statement, so no new edge was created and the
  integration pass's per-module manifest verification stands unchanged. Nothing in `inputs.py`
  imports from `sets.py`, so the one-way direction is intact.
- **No new duplication introduced.** The three `generated_input_type_name` call sites each pass
  `is_full_shape=True, token=""` inline rather than through a new wrapper, matching
  `inputs.py::serializer_input_type_name`'s existing call, so the file now has one spelling of
  the derivation rather than four.
- **The owner-name asymmetry was right to preserve.** `require_nested_fields_mapping` renders
  the MUTATION class name from `sets.py` and the SERIALIZER class name from `inputs.py`; that
  is pre-existing, it is visible in the byte-identity captures, and changing it inside a
  consolidation would be a behavior change wearing a refactor's diff. Correctly routed to
  Worker 1 as a decision rather than fixed silently.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (0 bytes) — `__all__` and
the re-export list are unchanged, so no spec authorization is needed. The three new helpers
and the new constant are subpackage-internal: their only importer is
`rest_framework/sets.py`, and neither the root lazy-export table nor
`rest_framework/__init__.py`'s export surface names them (the `rest_framework/__init__.py`
churn in `git status` is Slice 2b's docstring label strip, attributed by diff content — its
diff contains no code line). `describe_serializer_input` IS a root lazy export and its
derivation changed, but its returned string is proved character-identical above, so the public
behavior is unchanged.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Checked rather than
assumed that no consumer doc owes an update: `docs/README.md` names none of `nested_fields`,
`get_serializer_for_schema`, or `describe_serializer_input`, and
`examples/fakeshop/test_query/README.md` names no serializer suite. No message text changed, so
no doc quoting one can have gone stale.

Test-staleness sweep, run independently of the slice's file list per
`docs/builder/worker-3.md` `## Review job`: `git diff --stat -- 'examples/fakeshop/apps/*/models.py'`
is empty (no example-model field set moved) and no hunk in the two source files touches
`edges` / `node` / `Connection` / `graphql_name=` / a `strawberry.field` declaration (no
wire-shape conversion). Neither trigger in `docs/builder/BUILD.md` `### Test staleness a
focused run cannot see` fires.

### What looks solid

- **The strengthening does exactly what the finding asked and no more.** Both new assertions
  are full-message equality, and they detect drift anywhere in the string, not just at the tail
  Worker 2 mutated — my entry-1 mutation moved an INTERIOR clause (`.fields` -> `.FIELDS`),
  past the old shared prefix but before the tail, and both rows still fired. They also do not
  over-pin: the text they hard-code is a consumer-facing error message, which is contract, so a
  future wording change SHOULD fail them, and it fails them for exactly the right reason (the
  message changed) rather than an incidental one.
- **The population corrections were the valuable part of the pass.** Both findings' site lists
  were wrong as routed, in opposite directions, and both corrections re-derive cleanly. A
  widened population that is wrong costs more than the original finding; neither of these is.
- **The out-of-fence discipline held.** The one derivation that matters most for correctness
  (`resolvers.py::_assert_field_agreement`, per-request, third spelling) sits in a MIXED file
  and was left alone with a recommended replacement wording for the F2 entry, rather than
  reached for. `git stash` / `checkout` / `restore` / `worktree` appear nowhere in the pass,
  and `git status --short` differencing was used instead of reverting unexpected churn.
- **The floor run was volunteered and is recorded properly** — scratch venv outside the repo,
  explicit `--python`, resolved versions read from `uv pip list` rather than restated, focused
  scope, `497 passed`. The plan scoped the obligation elsewhere; running it removes the "a
  planned floor verification no pass ran" failure mode at the cost of minutes.
- **The implementation notes answer the questions a reviewer would otherwise reverse-engineer**
  — why three pieces and not four, why the fingerprint's prefix stays separate, why the class
  name is derived internally rather than passed, why no wrapper around
  `generated_input_type_name`. Each is checkable and each checked out.

### Temp test verification

Under `docs/builder/temp-tests/039-integration/` (gitignored; `git check-ignore -v` confirms
`.gitignore:192`), all created by this pass:

- `test_w3_arm_messages.py` — captured each pass-through arm's exact published message
  (`"Explicit config error in child fields"`, `"child: Explicit config error in child fields"`,
  `"a specific nested config error"`), so the Medium and Low recommendations carry measured
  text rather than guessed text. **Disposition: keep for the re-pass, then delete with the
  cycle.** Not promoted — it asserts nothing, it only prints.
- `test_w3_arm_strengthened.py` — the recommended assertions as full-message equality, used to
  prove the fix turns the arm's proof from 0 rows to 2. **Disposition: Worker 2 promotes its
  two in-fence rows by editing the two existing test functions named in the Medium finding —
  not by adding this file, which duplicates fixtures the permanent suite already has.** Delete
  with the cycle once those two assertions land.
- `w3-proofs.json` / `.md`, `w3-proofs-arm.json` / `.md`, `w3-proofs-arm2.json` / `.md`,
  `w3-proofs-fp.json` / `.md` — this pass's four `scripts/prove_failability.py` manifests and
  emitted records, kept distinct from Worker 2's `proofs.json` / `proofs.md` so neither pass's
  record overwrites the other's. **Disposition: delete with the cycle.**

No temp test caught a behavior bug in shipped production code; the Medium and the Low are both
test-pinning gaps, and neither is left resting on a temp test.

### Notes for Worker 1 (spec reconciliation)

1. **The four items Worker 2 raised are all accurate as written** — F2's fourth site and its
   recommended replacement wording, F1's third-copy symbol misattribution and its recommended
   replacement, the DRY import ratchet's silence on `generated_input_type_name`, and the
   owner-name asymmetry. All four were re-derived here and none needs correcting before the
   custodian acts on it. On the third: `generated_input_type_name` now carries **four**
   `rest_framework/inputs.py` call sites (three added this pass plus the pre-existing
   `serializer_input_type_name`), which is one more concrete row for `Escalation A` to weigh
   than the note states.
2. **Escalated: the same substring-`match=` defect class this pass exists to close survives at
   three more sites, two of them in the pass's own fence.** The Medium and the Low above are
   both instances. Resolution paths: (a) fold all three one-line assertions into the re-pass
   (recommended — the two in-fence ones are three lines from assertions the pass already
   rewrote, and the third is in the same file); (b) fold the two in-fence ones and route the
   `_fingerprint_nested` one to whichever card owns that arm; (c) accept all three as
   pre-existing and record the reason. Path (c) leaves the newly single-sited pass-through arm
   with nothing that can detect its removal, which is why this pass sets `revision-needed`
   rather than escalating and accepting.
3. **No spec edit is owed by the consolidation, and I agree with Worker 2's reasoning for
   that** — the spec describes the messages' contract, not their spelling, and states the
   type-name derivation as one shared deriver. Independently: the spec's `### Import manifest`
   is per-**package**, not per-symbol, so adding three names to an existing `from .inputs
   import (...)` statement leaves it exact, and the manifest verification the integration pass
   ran in both directions still holds.
4. **The `70` figure for F3 needs correcting before it reaches `bld-039-final.md`'s
   `### Deferred work catalog`** — see the Low finding. It measures 73 at `HEAD` and 71 now
   under the pattern the note names, and F1 is why it moved.

### Review outcome

`revision-needed`.

The consolidation itself is sound and better than routed: F1's four cross-module fragments are
retired to a measured zero, three of F2's four duplicate derivations are retired against an
existing owner with the type name proved character-identical, all 31 `ConfigurationError`
message templates across both modules are set-identical to `HEAD` with a working negative
control, both recorded failability entries reproduce node-id-set-identically at Worker 2's own
scope, the hot-path judgement holds under an independent caller trace, the four new
module-level names each retire a real two-module duplication rather than adding an
abstraction, the public surface is untouched, the two new citations resolve and name defining
symbols, and the 150 added lines carry zero process provenance under a control that fires 24
times on the removed lines.

The status is set by one Medium: the consolidated helper's `except ConfigurationError: raise`
pass-through arm — the arm whose contract the new docstring asserts, and the arm the
consolidation reduced from two copies to one — fails **0** rows when removed, because the two
tests that should catch it use a substring `match=` the resulting double-wrap survives. One of
those two assertions sits three lines above an assertion this same pass strengthened. The fix
is one line in each of two files the pass already owns, its expected text is measured, and it
is proven to move the arm from 0 rows to 2. Accepting a pass whose thesis is that
prefix-matching assertions hide message drift, while it leaves an adjacent substring match
hiding a wrap on the boundary it just single-sited, is not a call I can make on a recorded
rejection reason.

---

## Build report (Worker 2, pass 2)

Scope: the Medium and the two Lows in `## Review (Worker 3)`. **No production source changed.**
`shasum -a 256 django_strawberry_framework/rest_framework/inputs.py` reads
`4d7b61b9e6b9ba046287f99f2632ed947a68abf4249a236854f38edb1b46a953`, byte-for-byte the digest
Worker 3 recorded before its own mutations and identical after this pass's two, so the two
modules under review are the same bytes Worker 3 read. Both pass-through arms were closed
test-side, which is what the dispatch prefers and what the findings ask for.

### Files touched

Grounded in `git status --short` differenced against the list captured at pass start:
**the two lists are identical** (`diff` exit 0), because both files this pass edits were
already dirty from pass 1. Nothing else in the tree moved, so there is nothing to
stop-and-report and nothing was reverted. `git stash` / `checkout` / `restore` / `worktree`
appear nowhere in this pass.

- `tests/rest_framework/test_sets.py` — `test_validate_nested_fields_child_serializer_errors`'s
  FIRST block: the substring `match="Explicit config error in child fields"` replaced by
  `pytest.raises(ConfigurationError) as config_exc` plus a full-message equality assertion.
  This is the block three lines above the assertion pass 1 strengthened, in the same function.
- `tests/rest_framework/test_inputs.py` — three changes:
  `test_build_nested_serializer_spec_child_fields_configuration_error` and
  `test_fingerprint_propagates_nested_configuration_error_unwrapped` both moved from a
  substring `match=` to full-message equality, and one new row,
  `test_fingerprint_propagates_deep_nested_configuration_error_unwrapped`, was added because
  the Low's arm measured **1 row — weakly pinned** with only the existing row strengthened
  (see `### The Low that came back weakly pinned` below).
- `docs/builder/bld-039-integration.md` — this new top-level section, and `Status:`
  `revision-needed` -> `built`. No prior section edited.
- Untracked scratch, `docs/builder/temp-tests/039-integration/`: `pass2-proofs.json` /
  `pass2-proofs.md` (this pass's manifest and emitted record, named distinctly so neither
  Worker 3's four records nor pass 1's `proofs.json` is overwritten).

### Tests added or updated

- `tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors` —
  `assert str(config_exc.value) == "Explicit config error in child fields"`. Pins that a
  `ConfigurationError` raised by an opted-in nested serializer's `.fields` reaches the
  consumer UNWRAPPED through the schema-time ownership walk.
- `tests/rest_framework/test_inputs.py::test_build_nested_serializer_spec_child_fields_configuration_error`
  — `assert str(exc.value) == "child: Explicit config error in child fields"`. Same contract
  through the input build, including the field-name aggregation prefix that path adds.
- `tests/rest_framework/test_inputs.py::test_fingerprint_propagates_nested_configuration_error_unwrapped`
  — `assert str(exc.value) == "a specific nested config error"`. Same contract through the
  determinism fingerprint.
- `tests/rest_framework/test_inputs.py::test_fingerprint_propagates_deep_nested_configuration_error_unwrapped`
  — **new row.** A two-level opt-in tree (`Parent.child` -> `Middle.grandchild`, the deeper
  level opted in via `NestedSerializerConfig(nested_fields={...})`) whose GRANDCHILD's
  `get_fields()` raises; asserts the grandchild's own message arrives unchanged. The recursion
  reads each level's `.fields` inside that level's own guard, so unwrapped propagation is a
  per-LEVEL contract and a top-level row structurally cannot observe the arm at depth 2.

### The exact message text, re-measured rather than carried

Worker 3's Medium supplies measured text; carrying a number or a string on someone else's
measurement is the failure mode this cycle keeps hitting, so all three were re-measured here
before any assertion was written, by running Worker 3's capture probe
(`docs/builder/temp-tests/039-integration/test_w3_arm_messages.py`) under
`uv run pytest ... -n0 -s`:

```
SETS-PATH ARM MESSAGE >>>Explicit config error in child fields<<<
INPUTS-PATH ARM MESSAGE >>>child: Explicit config error in child fields<<<
FINGERPRINT-PATH ARM MESSAGE >>>a specific nested config error<<<
```

All three agree with the finding, `child: ` prefix included.

### The Low that came back weakly pinned, and how it was closed

The first run of this pass's manifest, with all three assertions strengthened and no new row:

| entry | rows failed | verdict |
|---|---|---|
| `inputs.py::read_nested_serializer_fields` (the Medium) | **2** | above the threshold |
| `inputs.py::_fingerprint_nested` (Low 1) | **1** | **WEAKLY PINNED** |

So Worker 3's figure for Low 1 does not carry: the one-line assertion it recommends moves
that arm from 0 rows to 1, and 1 row is `revision-needed` by the same acceptance rule that
sent this pass back. `docs/builder/worker-2.md` `### Failability self-proof before handoff`
makes it this pass's to fix, and the fix is a better-targeted row, never a weaker boundary:
the fingerprint's arm sits inside a RECURSION, so the row the existing test could never be
was one at depth 2. With
`test_fingerprint_propagates_deep_nested_configuration_error_unwrapped` added, the same
mutation fails 2 rows. Re-measuring rather than assuming the figure carried is what caught
this; a bare count re-used across passes would not have.

### Judgement on the hard-coded-text trade

Worker 3 warns that hard-coding the current text can make a legitimate future message change
fail for the wrong reason. Full equality is still right here, and the trade is smaller than
it looks, because of **who owns the string**:

- In all three assertions the pinned text is the text the TEST's own fixture raises
  (`raise ConfigurationError("Explicit config error in child fields")` inside the test
  function). The assertion therefore does not hard-code a framework message at all — it
  asserts the framework transported the child's message unchanged. A future rewording of any
  framework message cannot break these rows, because no framework wording is in them.
- The one framework-owned fragment across the three is the seven-character `child: `
  aggregation prefix in the input-build row. That prefix is the consumer-facing shape of a
  per-field error and is contract, not incidental, so a change to it SHOULD fail a row — and
  it fails for exactly the right reason (the prefix changed) rather than an incidental one.
- The alternative Worker 3 correctly rules out is widening the regex, which is the one move
  the dispatch forbids: `match=` cannot distinguish "propagated" from "wrapped, and the
  substring is still in there", so any regex that keeps matching after the wrap is
  non-distinguishing by construction. Equality is the only assertion shape that reads the
  difference, and the measurements above are what say so rather than the argument.

So: full equality, deliberately, with the note that these three rows carry almost no
framework wording at all.

### Re-measured `"SerializerMutation "` census (Low 2), with the pattern as a parameter

Re-measured while writing the figure, not carried. Instrument: Python `str.count` over source
TEXT (occurrences, not matching lines — two hits on one line read as one under `grep -c`),
`HEAD` obtained read-only as `git show HEAD:<path>` into a scratch path outside the repo.
The two patterns, spelled out because the published figure moves with them:

- **P1** = the 20 characters `"SerializerMutation ` — a double quote, `SerializerMutation`, a space.
- **P2** = the 22 characters `f"SerializerMutation {`. P2 is a subset of P1.

| population | P1 at `HEAD` | P1 now | P2 at `HEAD` | P2 now |
|---|---|---|---|---|
| `rest_framework/{resolvers,sets,inputs}.py` (the published subject) | **72** | **71** | **60** | **59** |
| all six `rest_framework/*.py` (adds `__init__.py`: 1 / 0) | 73 | 72 | 60 | 59 |
| whole package, working tree (adds `utils/inputs.py`: 1 / 0) | — | **73** | — | **59** |

Per-file, for auditability: `resolvers.py` 42 -> 43 (P1), 39 -> 40 (P2); `sets.py` 16 -> 14,
16 -> 14; `inputs.py` 14 -> 14, 5 -> 5.

Three corrections to the figure carried into `bld-039-final.md`'s `### Deferred work catalog`:

1. The catalog should carry **71** for P1 and **59** for P2 over the three named modules — the
   post-consolidation figures. Both `70` (`### Notes for Worker 1` item 6, `### Summary`) and
   Worker 3's `73` for `HEAD` are wrong for that subject.
2. **`HEAD` for the three named modules is 72 / 60, not 73 / 61.** Worker 3's `HEAD` row reuses
   the WORKING-TREE `resolvers.py` figures (43 / 40) in both of its rows; `resolvers.py` is a
   MIXED file and reads 42 / 39 at `HEAD`. Its `now` row (71 / 59) is right and reproduces here
   exactly.
3. **Three different populations all produce a 73**, which is why the pattern and the
   population have to travel with the number: P1 at `HEAD` over six modules, P1 now over the
   whole package, and Worker 3's mis-derived three-module `HEAD`. `START.md`'s "count right in
   every digit, wrong in SUBJECT" is live here.

**Attribution of the delta, since it is not all F1's.** F1 retired exactly 2 P1 sites and 2 P2
sites, both in `sets.py` (16 -> 14 under each pattern). `resolvers.py` GAINED one P1 and one
P2 occurrence — differenced by value, it is
`"SerializerMutation {mutation_cls.__name__}: field {target!r} carries a schema` — which is
Slice 3's work in that MIXED file, not this consolidation's. Net three-module movement is
therefore -1, made of F1's -2 and an out-of-fence +1.

Instrument control: respelling three P1 occurrences of `sets.py` in memory only (the repo was
never touched) drops its count 14 -> 11, so the census can report a different number and its
figures are measurements rather than an empty pattern.

### Validation run

- `uv run ruff format tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py`
  — **pass** (`2 files left unchanged`). Scoped, never `.`.
- `uv run ruff check --fix <the same two files>` — **pass** (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py <the same two files>` — **pass**
  (`Fixed 0 file(s).`), explicit paths.
- `git status --short` after both ruff invocations, differenced against the pass-start
  capture — **identical, `diff` exit 0**. No unexpected churn.
- Focused runs, no `--cov*` flag anywhere:
  - `uv run pytest tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py --no-cov`
    — **190 passed** (189 before this pass; the +1 is the new depth-2 row).
  - `uv run pytest tests/rest_framework/ tests/mutations/ tests/utils/test_inputs.py tests/forms/ --no-cov`
    — **1222 passed** (pass 1 recorded 1221; same +1). The sibling scope is
    `docs/builder/worker-2.md` `## Apply-changes verification scope`: every tree importing the
    surface the strengthened rows observe.
  - `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov`
    — **195 passed**, unchanged from pass 1.
- Test-staleness sweep (`docs/builder/BUILD.md` `### Test staleness a focused run cannot
  see`): **not owed** — this pass changes no example-model field set and no wire shape, and
  changes no production byte at all (digest above).

### Failability proofs

Both entries run through `uv run python scripts/prove_failability.py
docs/builder/temp-tests/039-integration/pass2-proofs.json --output
docs/builder/temp-tests/039-integration/pass2-proofs.md`; **exit 0**, no entry weakly pinned.
Preconditions asserted BEFORE any copy, in the order `docs/builder/BUILD.md`'s fenced loop
gives: no `ACTIVE-MUTATION.json` anywhere in the tree (`find . -name ACTIVE-MUTATION.json`
empty), and each anchor block counted independently in Python — **exactly 1 occurrence each**,
against a file that carries exactly **2** `except ConfigurationError:` / `raise` arms in total,
so the two anchors partition them. `--check-anchors-only` was run first and agreed. Full
emitted record on disk at `docs/builder/temp-tests/039-integration/pass2-proofs.md`.

- `django_strawberry_framework/rest_framework/inputs.py::read_nested_serializer_fields` —
  **mutation applied:** ONLY the pass-through arm removed
  (`except ConfigurationError:` / `raise` deleted), the `except Exception` translation left in
  place, so a `ConfigurationError` raised deeper in the nested tree is DOUBLE-WRAPPED and its
  own message is shadowed by the generic read failure. That is the boundary removed, not
  perturbed: it is precisely the clause the docstring asserts cannot happen;
  **scope as run:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE
  tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py`;
  **pre-mutation state of that scope:** green — `190 passed`, pytest exit 0, 0 pre-existing
  failing rows differenced out; **failing node ids:**
  `tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors`,
  `tests/rest_framework/test_inputs.py::test_build_nested_serializer_spec_child_fields_configuration_error`;
  **collection/setup errors:** 0 (pytest exit 1, a valid count);
  **revert proved by byte-comparison:** `filecmp.cmp(shallow=False)` True and
  `sha256 4d7b61b9e6b9ba04... == 4d7b61b9e6b9ba04...` against the pre-mutation copy.
  Was 0 rows before this pass.
- `django_strawberry_framework/rest_framework/inputs.py::_fingerprint_nested` —
  **mutation applied:** the fingerprint read's own pass-through arm removed the same way, so a
  deeper `ConfigurationError` is double-wrapped in the determinism-fingerprint materialization
  message; **scope as run:** identical to the entry above;
  **pre-mutation state of that scope:** green — `190 passed`, pytest exit 0, 0 rows
  differenced out; **failing node ids:**
  `tests/rest_framework/test_inputs.py::test_fingerprint_propagates_nested_configuration_error_unwrapped`,
  `tests/rest_framework/test_inputs.py::test_fingerprint_propagates_deep_nested_configuration_error_unwrapped`;
  **collection/setup errors:** 0 (pytest exit 1);
  **revert proved by byte-comparison:** same, `filecmp.cmp(shallow=False)` True plus identical
  SHA-256. Was 0 rows before this pass and **1 row** with only the existing row strengthened.

Neither entry is zero-row, so no **why 0** judgement is owed. Both sit at 2 rows — above the
weakly-pinned threshold and inside Worker 3's mandatory independent re-run floor; re-run at
the scope recorded above and compare node-id **sets**, not counts. After the last entry, the
target compares byte-identical to BOTH pristine copies the run took (`cmp` exit 0 against
each) and its digest is unchanged from before the first mutation.

### Hot-path budget

**Not applicable; plan declares no hot path for this pass** — and this pass changes no
production code at all, so it can add no cost to any path. The two files it edits are test
modules.

### Floor verification

Run, though the plan's declaration scopes the obligation to Slice 3 and this pass changes no
package source. The reason to spend the minutes: this pass's assertions are full-message
EQUALITY, and an equality assertion is the shape most exposed to an interpreter- or
dependency-version difference in rendered text. It passes at the floor.

- scratch venv (outside the repo): `<session scratchpad>/dsf-floor-pass2`, built with
  `uv venv … --python 3.10`, then
  `uv pip install --python <venv>/bin/python -e . --group dev` and
  `uv pip install --python <venv>/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'`
  — the floor `docs/builder/BUILD.md` `## Floor verification` records, taken from there.
  The shared `.venv` was never mutated (explicit `--python` on both installs).
- **The venv was verified to BE a venv before it was trusted**: `pyvenv.cfg` present and
  `sys.prefix` inside the scratch path, `sys.base_prefix` outside it. This is not ceremony —
  see `### Notes for Worker 1 (spec reconciliation)` item 2.
- resolved versions as read by `uv pip list --python <venv>/bin/python`: Python **3.10.19**,
  `django 5.2.16`, `strawberry-graphql 0.316.0`, `djangorestframework 3.18.1`,
  `django-filter 26.1`, `pytest 9.1.1`, `pytest-django 4.14.0`.
- focused scope: `<venv>/bin/python -m pytest tests/rest_framework/ --no-cov -q
  -p no:cacheprovider` — **pass, 498 passed** (pass 1 recorded 497; the +1 is the new row).

### Implementation notes

- **`config_exc`, not a second `exc`.** The strengthened first block in
  `test_validate_nested_fields_child_serializer_errors` binds `config_exc` because the
  function's second block already binds `exc` (pass 1's assertion). Two same-named bindings in
  one function would read as one, and the failure output would not say which block moved.
- **The new row is a depth-2 fixture, not a second depth-1 fixture.** A second top-level row
  would have been cheaper and worth nothing: it would duplicate what the existing row already
  observes and would leave the recursion — the reason this arm exists at all — unpinned. The
  grandchild raises from `get_fields()`, so the error surfaces inside the DEEPER level's own
  guard, which is the case the shallow row structurally cannot reach.
- **All four assertions read `str(exc.value)`, not `exc.value.args`.** `str()` is what the
  consumer sees, and the aggregation prefix the input build adds is only visible through it.
- **No source-side change for Low 1.** The dispatch prefers a test-side fix and one is
  sufficient: the arm's problem was never the arm, it was that nothing could observe its
  absence.

### Notes for Worker 3

- **Re-run scope for the failability audit:** `tests/rest_framework/test_inputs.py
  tests/rest_framework/test_sets.py`, exactly as recorded. Both entries are at 2 rows, inside
  the mandatory floor, so both are re-runnable; compare node-id sets. Manifest at
  `docs/builder/temp-tests/039-integration/pass2-proofs.json`.
- **The interesting re-run is Low 1's**, because its recorded history within this one pass is
  0 -> 1 -> 2 rows. If your independent mutation shape reports 1, check whether the depth-2
  row collected before concluding the arm is weakly pinned.
- **`scripts/review_inspect.py` was not run and its triggers do not fire**: no new `.py` file,
  nothing under `optimizer/` or `types/`, and zero lines of production logic changed (the
  source digest is identical to the one you recorded). The diff is +66 / -6 across two test
  modules, of which this pass owns +38 / -3.
- **Worker 3's `test_w3_arm_strengthened.py` was NOT promoted as a file**, per your own
  disposition: its two rows landed as assertions inside the two existing test functions
  instead. It and `test_w3_arm_messages.py` can be deleted with the cycle; the messages probe
  was re-run once here as the measurement above.
- **No process provenance added.** The four new comment blocks and the new test name state the
  invariant (unwrapped propagation, per-level contract) and carry no severity label, worker or
  round number, pass number, or finding id. One pre-existing `spec-039` docstring pointer in
  `test_sets.py` is `START.md`-kept vocabulary and was not touched by this pass.

### Notes for Worker 1 (spec reconciliation)

1. **No spec edit is owed by this pass.** It adds no behavior and changes no message: the spec
   states the unwrapped-propagation contract for a nested `ConfigurationError`, and these rows
   are the first assertions that can actually detect its absence. Nothing in the spec describes
   the assertion shape.
2. **A recorded floor-verification claim in this artifact cannot be re-derived at its stated
   path, and the reason is worth one line.** `<session scratchpad>/dsf-floor` — the path pass 1
   and the earlier passes record — is on disk but is **not a virtual environment**: it has no
   `pyvenv.cfg`, its `bin/python` is a bare symlink to uv's managed CPython 3.10, and
   `uv pip install --python <that path>/bin/python` now refuses with
   *"This Python installation is managed by uv and should not be modified."* Its
   `site-packages` still holds ~102 distributions, which is consistent with a genuine install
   whose `pyvenv.cfg` was later reaped from `/private/tmp` — so this is **not** evidence that
   the earlier run was false, and I am not claiming it was. It IS evidence that a floor record
   naming only a scratch path is not re-derivable later, since scratch decays. This pass built
   a fresh venv at `dsf-floor-pass2` and asserted `pyvenv.cfg` plus `sys.prefix` before
   trusting it; recording that assertion alongside the resolved versions is the cheap fix, and
   `docs/builder/BUILD.md` `### How to build the floor venv` currently does not ask for it.
   Flagged for the corpus ratchet's judgement, not edited — process docs are not this pass's
   to write, and one is mid-cycle.
   A second, smaller hazard from the same episode: `uv venv … 2>&1 | tail -3 && …` reports the
   pipe's exit status, so a refused venv creation and two refused installs read as `exit 0`
   with the failure text scrolled past. `START.md` "Instruments that lie" has the general form;
   this is a fresh instance of it inside a floor run specifically.
3. **The `70` figure needs correcting to 71 with its pattern and population attached, and
   Worker 3's `73` for `HEAD` needs correcting to 72** before either reaches
   `bld-039-final.md`'s `### Deferred work catalog`. Full table, per-file breakdown, and the
   attribution of the -1 (F1's -2 plus an out-of-fence +1 in a MIXED file) are in this pass's
   re-measured census section above (the one whose heading names Low 2 and the pattern
   parameter). **Recommended replacement** for `### Notes for Worker 1` item 6's current wording
   *"**70** `"SerializerMutation "` literals across `rest_framework/{resolvers,sets,inputs}.py`
   (61 f-prefixed)"*: **71 occurrences of the source text `"SerializerMutation ` across
   `rest_framework/{resolvers,sets,inputs}.py` (59 of them the `f"SerializerMutation {`
   spelling), counted as occurrences rather than matching lines; 72 / 60 at `HEAD`.**
4. **Worker 3's Low 1 figure did not carry, and the recommended one-line fix was not
   sufficient.** Its measurement (0 rows before) is right, but the arm reaches only 1 row —
   still `revision-needed` — with the recommended assertion alone; a second row at nesting
   depth 2 is what clears the threshold. Recorded here because it is the second time this
   cycle a figure re-used across a pass boundary needed re-measuring, and the standing lesson
   is the one `docs/builder/BUILD.md` `### What gets recorded` already states about counts
   versus node-id sets.
---

## Review (Worker 3, pass 2)

Re-reviewing `## Build report (Worker 2, pass 2)`. Scope as dispatched: the pass's diff is
**test-only**.

**Verified first, because a production-source move would mean the pass exceeded its scope.**
`shasum -a 256 django_strawberry_framework/rest_framework/inputs.py` =
`4d7b61b9e6b9ba046287f99f2632ed947a68abf4249a236854f38edb1b46a953`, byte-for-byte the digest
this reviewer recorded in `## Review (Worker 3)` before its own pass-1 mutations, and
`git diff --numstat` over that file reads `103 45` — the same insertion/deletion pair pass 1
recorded. `rest_framework/sets.py` is `24 37`, unchanged, and its mtime (Sep 5 12:24) predates
pass 1's review entirely, so it cannot have moved in pass 2. **No production source moved.**
Attribution of the rest of the tree is by diff CONTENT: the only non-strengthening hunk in the
two test files is a severity-label strip in a `test_sets.py` docstring
(`spec-039 Medium` -> `spec-039`), which is Slice 2b's work and **provably pre-dates pass 2** —
pass 1's provenance control counted `Medium` twice across the four files, the two source files'
diff carries exactly one such removed line, so the second was already in a test file when pass 1
read it. Worker 2's `### Files touched` list is therefore complete for what pass 2 owns.

### Failability mutations recorded BEFORE they were made

`docs/builder/worker-3.md` `## Scope` requires the record to precede the mutation. Both of
Worker 2's entries are at 2 rows, so both are inside the mandatory re-run floor and the
subset is **all of them**; nothing is accepted on Worker 2's record alone.

Both mutation SHAPES are deliberately different from Worker 2's *and* from pass 1's. Worker 2
DELETED the `except ConfigurationError:` / `raise` lines; pass 1 deleted the whole boundary.
This pass **inverts the arm order** instead — `except Exception` is moved ABOVE
`except ConfigurationError`, so every line of both arms survives and only the ordering that
constitutes the boundary is gone. A deletion-shaped blind spot (an anchor that matched the
wrong block, a replacement that changed indentation) cannot survive into a re-run that deletes
nothing.

1. `rest_framework/inputs.py::read_nested_serializer_fields` — swap the two `except` arms so
   the generic translation shadows the pass-through.
2. `rest_framework/inputs.py::_fingerprint_nested` — the same swap on the fingerprint read's
   own arm.

Two further entries exist to settle the **independence** of the depth-2 row (dispatch item 2),
not to prove a boundary. Both apply mutation 2 and narrow the scope to ONE node id, so each
fingerprint row is asked whether it detects the removal on its own:

3. mutation 2, scope `test_fingerprint_propagates_nested_configuration_error_unwrapped` only.
4. mutation 2, scope `test_fingerprint_propagates_deep_nested_configuration_error_unwrapped`
   only.

And one **discrimination probe**, which ADDS a wrap rather than removing a boundary and is
labelled as such: wrap `_fingerprint_nested`'s recursive `_fingerprint_field_map(...)` call —
the call that today sits OUTSIDE the arm's `try` — in a `ConfigurationError` re-wrap. A
top-level nested failure never passes through that call, so this probe should fail the depth-2
row and leave the depth-1 row green. That asymmetry is the only evidence that can distinguish
"a second row" from "a second reason".

Manifests: `docs/builder/temp-tests/039-integration/w3p2-proofs.json` (entries 1-2),
`w3p2-solo-shallow.json`, `w3p2-solo-deep.json`, `w3p2-discriminate.json`, each run through
`scripts/prove_failability.py`, one boundary at a time, restore proved by byte comparison.

### Independent re-derivations, before the findings

Every figure below was re-measured in this pass. Where an instrument could only ever agree,
it carries a control.

**Pass 1's Medium is closed, and the node-id sets match at Worker 2's own scope.** Both of
Worker 2's entries are at 2 rows, so both are inside the mandatory floor and the re-run
subset is **all of them** — nothing accepted on its record alone. Preconditions asserted
first: no `ACTIVE-MUTATION.json` anywhere in the tree, both anchors matching exactly once
(`--check-anchors-only` on Worker 2's own manifest agrees, so its manifest still describes
the current bytes), and `shasum -a 256` on the target reading `4d7b61b9e6b9ba04...` before
the first mutation, between entries, and after the last.

| entry | Worker 2 | this pass (arm-order SWAP) | node-id set |
|---|---|---|---|
| `inputs.py::read_nested_serializer_fields` | 2 rows, 0 errors, pre-mutation `190 passed` | **2 rows, 0 errors**, pre-mutation `190 passed` | **identical** |
| `inputs.py::_fingerprint_nested` | 2 rows, 0 errors, pre-mutation `190 passed` | **2 rows, 0 errors**, pre-mutation `190 passed` | **identical** |

Set 1 is
`tests/rest_framework/test_sets.py::test_validate_nested_fields_child_serializer_errors` +
`tests/rest_framework/test_inputs.py::test_build_nested_serializer_spec_child_fields_configuration_error`.
Set 2 is
`tests/rest_framework/test_inputs.py::test_fingerprint_propagates_nested_configuration_error_unwrapped`
+ `::test_fingerprint_propagates_deep_nested_configuration_error_unwrapped`. The arm this
pass exists to close went **0 -> 2** and the fingerprint arm **0 -> 1 -> 2**; the mutation
that measured 0 in pass 1 now measures 2 under a mutation shape that deletes nothing.

`scripts/prove_failability.py` exit 0 on every run; restores proved by
`filecmp.cmp(shallow=False)` plus SHA-256 against a pre-mutation copy taken outside the repo.
`git stash` / `checkout` / `restore` / `worktree` appear nowhere in this pass. Records at
`docs/builder/temp-tests/039-integration/w3p2-proofs.md` and the three narrowed reports.

**The arm population claim is right under the predicate it states, and the obvious grep
disagrees with it.** Worker 2 records "exactly **2** `except ConfigurationError:` / `raise`
arms in total, so the two anchors partition them". `grep -c "except ConfigurationError:"`
over the same file returns **3** — lines 305, 470 and **1617**. The third is
`except ConfigurationError:` / `return None` inside
`inputs.py::_build_default_canonical_shape_parts`, a deliberate swallow the surrounding
docstring specifies ("when it cannot be built it simply does not reserve it"), not a
pass-through. So the record's population is correct because `raise` is half its predicate; a
later auditor reaching for the one-line grep gets 3 and needs the pairing to reconcile it.
Recorded here so the reconciliation does not have to be done twice.

**The depth-2 row is a second detector, not a second copy — proved by asymmetry, not argued.**
Three extra runs, each recorded before it was made:

| run | scope | rows failed | which |
|---|---|---|---|
| arm SWAP, narrowed to the depth-1 row alone | 1 node id | **1 of 1** | the shallow row |
| arm SWAP, narrowed to the depth-2 row alone | 1 node id | **1 of 1** | the deep row |
| **discrimination probe** — wrap the RECURSIVE `_fingerprint_field_map(...)` call, which today sits OUTSIDE the arm's `try` | both test modules, `190 passed` clean | **1 of 190** | **the deep row only; the shallow row stayed green** |

The first two say each row detects the arm's removal on its own, so neither is riding the
other's failure. The third is the one that settles the dispatch's question: a mutation at the
recursion seam fails the depth-2 row and **cannot** fail the depth-1 row, because a top-level
nested failure is raised in `_fingerprint_nested`'s own frame and never passes through that
call at all. The two rows therefore have different reach, not merely different fixtures, and
they share no fixture to retire together — each defines its serializer classes inside its own
function body. Verdict: the depth-2 fixture **genuinely clears the threshold**; Worker 2's
stated reason for choosing it over a second top-level row ("a top-level row structurally
cannot observe the arm at depth 2") is exactly what the probe measures.

(The `WEAKLY PINNED` label the script prints on those three narrowed runs is the 0-or-1 rule
applied mechanically to a one-row scope. It is not a verdict about the boundary: the boundary's
own record is the two-module run above, at 2 rows.)

**Four assertions became full-message equality, and the trade is smaller than Worker 2 claims.**
Read at each site rather than taken from the report:

| row | pinned text | who owns the string |
|---|---|---|
| `test_sets.py::test_validate_nested_fields_child_serializer_errors` (first block) | `Explicit config error in child fields` | the test's own `BrokenConfigChild` raise |
| `test_inputs.py::test_build_nested_serializer_spec_child_fields_configuration_error` | `child: Explicit config error in child fields` | the test's own `BrokenChild` raise, under the framework's per-field prefix |
| `test_inputs.py::test_fingerprint_propagates_nested_configuration_error_unwrapped` | `a specific nested config error` | the test's own `BadConfigChild` raise |
| `test_inputs.py::test_fingerprint_propagates_deep_nested_configuration_error_unwrapped` | `a specific deep nested config error` | the test's own `BadConfigGrandchild` raise |

So the judgement holds for **four** rows, not the three Worker 2 argues (the new depth-2 row's
text is fixture-owned too). And the one framework-owned fragment is smaller than the
"seven-character `child: ` prefix" the report names: the prefix is built at
`inputs.py::_walk_serializer_fields` #"field_errors.append(f\"{name}: {exc}\")", where `name`
is the field name **the test's own `Parent` declares**, so the framework owns `": "` and the
ordering, not `child`. Worker 2's judgement is conservative in the right direction.

Against my own pass-1 warning about hard-coding current text: the warning stands and these
rows do not trip it. A `pytest.raises(match=...)` substring cannot distinguish "propagated
unwrapped" from "wrapped, and the substring is still in there" — that is the defect this pass
closes, and it is a property of the assertion SHAPE, so no regex satisfies both. Equality is
the only shape that reads the difference, which is why the recommendation was equality and not
a widened pattern. The residual exposure is one two-character framework fragment plus a
single-problem aggregate; `inputs.py::_aggregate_field_problems` raises a lone problem
**verbatim**, so the `child: ...` row is stable as long as its fixture yields one bad field,
which it does by construction.

**The census, re-derived, and the disagreement settled against me.** Instrument: Python
`str.count` over source text (occurrences, not matching lines), `HEAD` read as
`git show HEAD:<path>` into a scratch path outside the repo — necessary here because
`resolvers.py` is a MIXED file. Patterns as parameters: **P1** = the 20 characters
`"SerializerMutation ` (quote, the word, one space); **P2** = the 22 characters
`f"SerializerMutation {`, a subset of P1.

| population | P1 `HEAD` | P1 now | P2 `HEAD` | P2 now |
|---|---|---|---|---|
| `rest_framework/{resolvers,sets,inputs}.py` — the published subject | **72** | **71** | **60** | **59** |
| all six `rest_framework/*.py` (adds `__init__.py` 1 / 1) | 73 | 72 | 60 | 59 |
| whole package (adds `utils/inputs.py` 1 / 1) | 74 | **73** | 60 | **59** |

Per file: `resolvers.py` 42 -> 43 (P1) and 39 -> 40 (P2); `sets.py` 16 -> 14 / 16 -> 14;
`inputs.py` 14 -> 14 / 5 -> 5.

**Worker 2 is right and my `73` for `HEAD` was wrong.** The three-module figure at `HEAD` is
**72 / 60**. What my pass-1 row actually measured was the **pre-consolidation working tree**
(`resolvers.py` 43 / 40 plus `sets.py` at its unedited 16 / 16), for which 73 / 61 is the
correct pair — a count right in every digit and wrong in its subject, which is the failure
`START.md` names and which I then attributed to `HEAD`.

The `70` has a separate cause, and it is arithmetic: `### Findings that need Worker 2` F3
publishes its own per-file breakdown as "(43 / 16 / 14)", which sums to **73**, beside a total
of **70**. No population I can construct produces 70, at `HEAD` or now, under either pattern
or under `grep -c`. Its companion `61` is internally consistent (40 + 16 + 5).

Attribution of the movement, differenced **by value** rather than by delta: `sets.py` lost
exactly the two fragments F1 promoted —
`f"SerializerMutation {name}.Meta.nested_fields must be a mapping of ` and
`f"SerializerMutation {name}.Meta.nested_fields[{field_name!r}] must be a ` — and
`resolvers.py` gained exactly one,
`f"SerializerMutation {mutation_cls.__name__}: field {target!r} carries a schema`, which is
Slice 3's work in that MIXED file. Net -1 = F1's -2 plus an out-of-fence +1. Worker 2's
attribution reproduces exactly.

Instrument note, since it is the kind of coincidence that becomes a rule: `grep -c` (matching
lines) returns the same numbers as `str.count` on this corpus, because every occurrence happens
to sit on its own line. That is a property of these three files today, not of the instrument,
so the published figure still owes "counted as occurrences".

**Settled figure for `bld-039-final.md`'s `### Deferred work catalog`:** **71** occurrences of
the source text `"SerializerMutation ` across `rest_framework/{resolvers,sets,inputs}.py` in
the working tree, of which **59** are the `f"SerializerMutation {` spelling; **72 / 60** at
`HEAD` (`4c483b6b`); counted as occurrences, not matching lines. Worker 2's recommended
replacement wording says exactly this and can be used verbatim.

**No production source moved, re-verified three ways.** SHA-256 identical to pass 1's recorded
digest; `git diff --numstat` on `inputs.py` reading `103 45`, the same pair pass 1 recorded;
`sets.py` at `24 37` with an mtime predating pass 1's review. After all five of this pass's
mutate/restore cycles the digest and the numstat are unchanged, and `git status --short`
compares **byte-identical** to Worker 2's own end-of-pass-2 capture.

**Style, swept independently of the report's claim.** Provenance sweep (severity labels,
`P<n>` / `H<n>` / `M<n>` / `F<n>` ids, slice and pass numbering, worker/round/review/finding
vocabulary, `previously`, `as of 0.0.N`) over the **66 added lines** in the two test files:
**0 hits**, across the new test name, its docstring, its fixtures, and all five new comment
blocks. Positive control, the same pattern over the 6 removed lines: **1 hit**, the
`spec-039 Medium` -> `spec-039` docstring strip — so the instrument can see what it is looking
for. That one hit is also how the strip hunk's attribution was settled: pass 1's control
counted `Medium` twice across four files and the two source files carry exactly one such
removed line, so the second was already in a test file when pass 1 read it. Slice 2b's, not
pass 2's.

**Recorded numbers re-run, not read.** `tests/rest_framework/test_inputs.py
tests/rest_framework/test_sets.py --no-cov` -> **190 passed**;
`tests/rest_framework/ tests/mutations/ tests/utils/test_inputs.py tests/forms/ --no-cov` ->
**1222 passed**. Both match Worker 2 exactly, including the +1 over pass 1's 189 / 1221.
Read-only lint over the two files: `ruff format --check` `2 files already formatted`,
`ruff check` `All checks passed!`, `check_trailing_commas.py --check` exit 0. The floor run
was reproduced independently in Worker 2's own scratch venv:
`dsf-floor-pass2/bin/python -m pytest tests/rest_framework/ --no-cov` -> **498 passed**, with
`uv pip list` reading Python 3.10.19 / `django 5.2.16` / `strawberry-graphql 0.316.0` /
`djangorestframework 3.18.1` / `django-filter 26.1` — the versions recorded.

**Tree condition.** Confirmed only what the dispatch asks. Population of four `spec-050` red
files printed, each grepped for `rest_framework` and `SerializerMutation`: **0 hits each**,
so no traceback in that population can name a file in this diff.

**The two instrument warnings, measured.**

*The decayed floor path.* `<scratchpad>/dsf-floor` is on disk with 100 distributions in
`lib/python3.10/site-packages` (`django-5.2.16`, `strawberry_graphql-0.316.0`,
`djangorestframework-3.18.0`, `django_strawberry_framework-0.0.15`), no `pyvenv.cfg`, and
`bin/python` a bare symlink into uv's managed CPython. Run today it reports
`sys.prefix` = the **managed interpreter**, `dsf-floor` absent from `sys.path`, and
`import django` -> `ModuleNotFoundError`. **That answer is the reassuring one**, and it is why
no recorded floor claim is thereby unverifiable: a floor invocation at a decayed path fails
**loudly at the first import**, never silently green, so a record of `497 passed` at that path
could not have been produced by the decayed state — the `pyvenv.cfg` must have existed when it
ran and was reaped afterwards. The claim's substance is separately re-derivable by
reconstruction, which is what pass 2 did (`498 passed` = 497 + the new row, reproduced above).
What genuinely does not survive is the record's **identity**: a scratch path is not an
instrument identity, and the surviving `site-packages` shows a soft dep that moved between the
two builds (`djangorestframework` 3.18.0 -> 3.18.1). Root cause is one line up from Worker 2's
framing: `docs/builder/BUILD.md` `## Floor verification`'s fenced recipe prescribes
`/tmp/dsf-floor` — a bare `/tmp` path, which `START.md` "Session rules you will forget" already
forbids for temp files and which is exactly what the OS reaper visits. Routed to Worker 1.

*The pipe's exit status.* Confirmed with a control rather than reasoned: `false | tail -3`
exits **0** here and its `&&` successor **runs**; `set -o pipefail` makes the same pipe exit 1.
So a refused `uv venv` and two refused installs can read as a clean run with the failure text
scrolled past. No recorded number in this cycle was corrupted by it — a failed install shows up
as a failed pytest at the end of the same recipe, and pass 2 asserted `pyvenv.cfg` plus
`sys.prefix` before trusting its venv — but the hazard is real and the recipe is where it lives.
Note the pipe is the **caller's** addition to trim output; `BUILD.md`'s fenced recipe has no
pipe, so the corpus-level gap is the missing "assert it IS a venv" step, not a pipe to remove.
Routed to Worker 1, unedited: process docs are not a reviewer's to write and one is mid-cycle.

### High:

None.

### Medium:

None. Pass 1's single Medium is closed: the `except ConfigurationError: raise` pass-through arm
in `read_nested_serializer_fields` now fails **2 rows** on removal, node-id-set-identical to
Worker 2's record at Worker 2's own scope, under a mutation shape that deletes nothing.

### Low:

None. Low 1 is closed at 2 rows with the second row proved independent by the discrimination
probe above. Low 2's figure is settled and its correction is routed to Worker 1, which is the
right owner: the wrong number lives in `### Notes for Worker 1` item 6 and `### Summary`, both
Worker 1's own prior sections, which pass 2 correctly did not edit.

### DRY findings

- **Nothing new was introduced.** The pass changes no production byte (digest above) and adds
  no helper, constant, fixture module, or indirection. There is no abstraction to challenge:
  `docs/builder/worker-3.md` `### The existence challenge` has no target in a diff whose whole
  content is four assertions and one test function.
- **The new depth-2 row is a near-copy of its shallow sibling by shape, and correctly not
  consolidated.** Both declare local serializer classes and call
  `serializer_schema_fingerprint`. Parametrising them was considered and is wrong twice over:
  the fixtures differ structurally (two classes and a flat `nested_configs` versus three
  classes and a nested `NestedSerializerConfig` tree), so the parameter would be the whole
  fixture, and the discrimination probe shows the rows have different reach — collapsing them
  into one id would trade two detectors for one, which is the direction the failability floor
  exists to prevent.
- **The two full instruction-sentence equalities duplicate `NESTED_STABLE_FIELDS_INSTRUCTION`
  verbatim in two test files, and that duplication is load-bearing.** It looks like a
  regression against F1's single-siting and is the opposite: a row that asserted against the
  imported constant would move with any reword of it and detect nothing — the self-falsifying
  instrument this cycle's memory already names. Consumer-facing text has to be spelled out at
  the assertion. (Pass 1's work, re-checked here because F1 makes it look wrong.)
- **The five new explanatory comments are five near-copies of one sentence, and each is
  site-specific.** Two say "never a substring of it", two "never its prefix", and each names
  its own site's hazard (the double-wrap, the drifting tail, the aggregation prefix, the
  per-level contract). Consolidating them would move the rationale away from the assertion it
  justifies. Observed and accepted, not a finding.
- **F1 / F2 / F3 fences all still hold.** No hunk in `resolvers.py`'s dirty diff names the
  three new helpers, `generated_input_type_name`, or the `SerializerMutation` prefix work; the
  one out-of-fence P1/P2 addition in that file was differenced by value and is Slice 3's.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (0 bytes): `__all__` and the
re-export list are unchanged, so no spec authorization is needed. This pass touches only two
test modules, so it cannot move a public surface; the check is run anyway because
`docs/builder/worker-3.md` requires it on every review.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces — the only
documentation change is this artifact, which is per-cycle scratch. Checked rather than assumed
that no consumer doc owes an update: no message text and no production behavior changed, so no
doc quoting either can have gone stale.

Test-staleness sweep, run independently of the pass's own file list per
`docs/builder/worker-3.md` `## Review job`:
`git diff --stat -- 'examples/fakeshop/apps/*/models.py'` is empty (no example-model field set
moved) and no hunk in either test file touches `edges` / `node` / `Connection` /
`graphql_name=` / a `strawberry.field` declaration (no wire-shape conversion). Neither trigger
in `docs/builder/BUILD.md` `### Test staleness a focused run cannot see` fires.

Test-tier placement checked against `AGENTS.md` rules 7 and 10 rather than inherited from the
sibling rows: the new row asserts a schema-build-time rejection reached at class definition, so
a live `/graphql` fixture would have to compose a deliberately broken nested serializer into the
example schema and would break every other suite in that module. Package tier is correct, and
it matches where its three siblings already live. `pytest.ini` `testpaths` names
`tests examples/fakeshop/{tests,test_query,apps}` only, so nothing under
`docs/builder/temp-tests/` is ever collected by a bare `uv run pytest` — the temp rows below
cannot leak into a suite figure.

### What looks solid

- **The fix went to the assertion, never to the boundary.** The dispatch's own preferred shape,
  and the one `docs/builder/BUILD.md` demands: nothing in production moved, and the arm that
  measured 0 rows in pass 1 measures 2 because two rows can now see it, not because it got
  easier to satisfy.
- **Re-measuring instead of carrying is what caught Low 1's shortfall.** Pass 1's recommended
  one-liner really does stop at 1 row, and the report says so in its own voice before anyone
  asked. Two figures in two passes now needed re-measurement rather than reuse, and both times
  the re-measurement was the builder's own. That is the habit this cycle has been trying to
  install.
- **The chosen second row is the expensive one, not the cheap one.** A second top-level fixture
  would have reached 2 rows in a third of the work and pinned nothing new; the depth-2 tree
  pins the recursion, which is the reason the arm exists. The discrimination probe above turns
  that from a plausible claim into a measured one.
- **The census section states its pattern, its population, and its arithmetic per file**, names
  three different populations that each yield a 73, and differences the delta **by value**
  rather than by subtraction — which is how the out-of-fence +1 in a MIXED file was separated
  from F1's -2 instead of being absorbed into it.
- **`config_exc` rather than a second `exc`.** Two same-named bindings in one function would
  read as one and the failure output would not say which block moved. Small, and exactly the
  kind of thing that makes a two-block regression legible a year later.
- **The two instrument hazards were raised, not acted on.** Both bear on evidence already
  recorded in this cycle and both are corpus-level; flagging them mid-cycle with the measurement
  attached, while explicitly not editing a process doc another worker may be reading, is the
  right call under `docs/builder/BUILD.md`'s corpus ratchet.

### Temp test verification

Under `docs/builder/temp-tests/039-integration/` (gitignored; `git check-ignore -v` resolves it
to `.gitignore:192`), and never collected by a bare `uv run pytest` per the `testpaths` check
above:

- `w3p2-proofs.json` / `.md` — this pass's two-entry independent re-run (arm-order swap).
  **Disposition: delete with the cycle.**
- `w3p2-solo-shallow.json` / `.md`, `w3p2-solo-deep.json` / `.md` — the per-row narrowed runs
  that prove each fingerprint row detects the removal alone. **Disposition: delete with the
  cycle.**
- `w3p2-discriminate.json` / `.md` — the discrimination probe (wraps the recursion seam; fails
  the deep row only). This is the record behind the independence verdict. **Disposition: delete
  with the cycle**; its result is quoted in full above so nothing rests on the file surviving.
- `test_w3_arm_messages.py` (pass 1's print-only capture probe) — **kept**. Worker 2 re-ran it
  to re-measure all three strings before writing any assertion, which is the cheapest way to
  re-derive them; it asserts nothing, so it is not promotable. Delete with the cycle.
- `test_w3_arm_strengthened.py` (pass 1's) — **deleted in this pass.** Its purpose was
  discharged the moment its two rows landed as assertions inside the two existing test
  functions, which is the disposition pass 1 recorded and Worker 2 followed. Verified present
  at both permanent sites before deleting.
- Pass 1's `w3-proofs*.{json,md}` and Worker 2's `proofs.*` / `pass2-proofs.*` are left
  untouched; each pass's record is named distinctly so none overwrites another's.

No temp test caught a behavior bug in shipped production code, and no shipped behavior rests on
a temp test.

### Notes for Worker 1 (spec reconciliation)

1. **No spec edit is owed, and I agree with Worker 2's reasoning.** The spec states the
   unwrapped-propagation contract; it says nothing about assertion shape, and these rows are the
   first that can detect the contract's absence. Independently checked: the spec's
   `### Import manifest` is per-package, and this pass adds no import at all.
2. **Escalated (figure correction, Worker 1 owns the text): the `70` in
   `### Notes for Worker 1` item 6 and `### Summary` must not reach `bld-039-final.md`'s
   `### Deferred work catalog`.** Settled figure, re-derived twice and agreeing: **71**
   occurrences of `"SerializerMutation ` across `rest_framework/{resolvers,sets,inputs}.py`, of
   which **59** are `f"SerializerMutation {`; **72 / 60** at `HEAD` (`4c483b6b`); counted as
   occurrences, not matching lines. My own pass-1 `73` was wrong for `HEAD` — it is the correct
   figure for the pre-consolidation working tree, mislabelled — and the `70` is a mis-addition
   of F3's own per-file row (43 + 16 + 14 = 73). Worker 2's recommended replacement wording is
   accurate and can be lifted verbatim. Resolution paths: (a) carry 71 / 59 with the pattern and
   population attached, which is what `START.md` asks; (b) carry both the `HEAD` and
   working-tree pairs if the catalog wants a before/after. Nothing here needs Worker 2.
3. **Escalated (corpus, not this cycle's to fix): the floor recipe's scratch path and its
   missing venv assertion.** `docs/builder/BUILD.md` `## Floor verification` prescribes
   `/tmp/dsf-floor`, a bare `/tmp` path `START.md` already forbids for temp files, and asks for
   no proof that the directory IS a virtual environment. Both halves of the decay this cycle
   observed follow from that one line. Measured consequences are in the re-derivations above,
   including the reassuring half: a decayed path fails loudly at the first import, so no
   recorded floor claim in this cycle is falsified or unverifiable — the earlier `497 passed`
   could not have come from the decayed state, and pass 2's reconstruction reproduces it as
   `498`. Resolution paths: (a) recipe writes to the session scratchpad and asserts
   `pyvenv.cfg` + `sys.prefix` before trusting the venv, recording the assertion beside the
   resolved versions; (b) record resolved versions and a `pyvenv.cfg` hash so a later reader can
   audit a decayed run; (c) accept that floor records are point-in-time and say so in the
   template. Corpus ratchet applies either way, and no process doc was edited by this pass.
4. **The pipe-exit hazard is real but corrupted nothing here.** `false | tail -3` exits 0 and
   runs its `&&` successor (controlled above). The pipe is the caller's, not the recipe's, and a
   refused install still surfaces as a failed pytest at the end of the same recipe, so this is a
   documentation hardening rather than a re-audit of any recorded figure.
5. **One prose imprecision in pass 2's own report, no action needed.** Its hard-coded-text
   judgement argues over "three" assertions and there are four; the fourth (the new depth-2 row)
   is fixture-owned text too, so the argument gets stronger, not weaker. Likewise the
   "seven-character `child: ` prefix" is really `": "` plus the field name the test's own
   `Parent` declares. Both errors run in the conservative direction.
6. **Nothing further from the F1 / F2 / F3 dispatch is outstanding.** F1's four cross-module
   fragments stay retired to zero and F2's three in-fence duplicates stay retired against
   `utils/inputs.py::generated_input_type_name`, both re-verified in pass 1 and unaffected by a
   test-only pass; F2's fourth site (`resolvers.py::_assert_field_agreement`) and F3 remain
   deliberately out of fence and already routed to you.

### Review outcome

`review-accepted`.

Pass 1's Medium and both Lows are closed, and the closure is measured rather than asserted:
the newly single-sited pass-through arm goes 0 -> 2 rows with a node-id set identical to
Worker 2's at Worker 2's own scope under a mutation shape that deletes nothing; the fingerprint
arm goes 0 -> 1 -> 2, and the row that clears it is proved a **second detector rather than a
second copy** by a probe at the recursion seam that fails the depth-2 row and cannot fail the
depth-1 row. No production byte moved — SHA-256, `git diff --numstat` and mtime all agree — so
the pass stayed inside the scope the dispatch set, and `git status --short` after five
mutate/restore cycles is byte-identical to Worker 2's own end-of-pass capture. The four
equality assertions pin fixture-owned text in every case, leaving `": "` as the only
framework-owned fragment in any of them, so the over-pinning my pass-1 review warned about does
not materialise. `190` / `1222` / `498` all reproduce, lint is clean read-only, the 66 added
lines carry zero process provenance under a control that fires, and the four red `spec-050`
files name nothing in this diff.

The census is settled against my own pass-1 figure: **71 / 59** now, **72 / 60** at `HEAD`,
over `rest_framework/{resolvers,sets,inputs}.py`, counted as occurrences. Worker 2's correction
was right in both halves, the `70` is a mis-addition of F3's own per-file row, and the movement
differences by value into F1's -2 plus one out-of-fence +1. The remaining items — that figure
reaching the deferred catalog, and the two corpus-level instrument hazards — are Worker 1's or
the maintainer's to land and are escalated with their measurements attached; none of them is
Worker 2's, and none of them warrants holding a diff that changes no production code.

---

## Final verification (Worker 1, pass 2)

The final-verification pass over the consolidation loop `## Final verification (Worker 1)`
opened: Worker 2's two build reports, Worker 3's two reviews (pass 2 `review-accepted`, no
High and no Medium), and the diff as it stands. Every figure below was re-measured in this
pass; where an instrument could only agree with itself it carries a control and its
population is printed.

Spec status/header lines re-verified per `docs/builder/worker-1.md`
`## Spec status-line re-verification`: line 1's title now reads "the **shared** `FieldError`
envelope" (D1's fix), the opener's `Shipped in 0.0.13` / `DONE-039-0.0.13` claim and
`Status: **SHIPPED (0.0.13)**` (spec:58) all still describe the tree. No status-line edit
owed.

### F1, F2, F3 — landing graded against the routing, not against the reports

**F1 landed, and wider than the routing specified.** My own routing said "one module-level
raise/message helper in `rest_framework/inputs.py`"; what landed is one constant plus three
helpers. Re-derived the whole census rather than reading the claim — instrument: every
non-docstring `str` constant of >= 25 characters and >= 4 words in the six
`rest_framework/` modules, whitespace-normalized, keyed by value, run over the working tree
and over `git show HEAD:` copies taken to a scratch path outside the repo:

| population | cross-module shared | intra-module repeats |
|---|---|---|
| `HEAD` (positive control) | **4** | 4, one of them the instruction sentence 2x inside `inputs.py` |
| working tree | **0** | 3, all of them F3 / audit-1c territory (`resolvers.py` 2x2, `serializer_converter.py` 3x) |

The `HEAD` row reproduces the integration pass's own 4 and 2 exactly, so the zero is a
measurement and not an empty grep. The routing's "one helper" was an under-specification
rather than a contract: the two `Could not read .fields` sites shared a six-line
read-and-translate block and the two `Meta.nested_fields` rejections shared their
`isinstance` predicate, so a message-only helper would have left the scaffolding duplicated —
which is half of what F1 measured. Each of the four new names has a live caller in **each**
of the two modules (16 references across `django_strawberry_framework/`, `tests/`,
`examples/`, printed), and `require_*` is the naming 14 prior helpers in this package
already use. Accepted as a widening toward the DRYer shape.

**My routing's symbol attribution was wrong and Worker 2's correction is right.** Resolved
by AST rather than by reading either report: `sets.py:434` — the `read_nested_serializer_fields`
call that replaced the six-line block — is inside `_assert_schema_source_ownership`
(`sets.py:396-451`), while `sets.py:326` and `:358` are inside
`_validate_serializer_nested_fields` (`:295-393`) and carry the two `require_*` rejections.
The fragment table in `### Findings that need Worker 2` is correct; only its symbol name is
not. Per `docs/builder/ARTIFACT.md` `## Re-pass sections` the prior section stands unedited —
this is the correction of record, and it supersedes the F1 wording in
`### Findings that need Worker 2` and in `### Notes for Worker 1` item 1.

**F2 landed for its three in-fence sites, and the spec already required it.** Instrument:
`PartialInput` as an executable literal over the whole package. **1 executable occurrence
outside its owner** (`utils/inputs.py:1015`), and it is `resolvers.py:1213` — so all three
`rest_framework/inputs.py` spellings are gone. `generated_input_type_name` now carries four
`rest_framework/inputs.py` call sites (`:838`, `:938`, `:1105`, `:1692`). Worth recording
because no pass named it: the spec's `### Import manifest` (spec:2723) **already** lists
`generated_input_type_name` in the substrate `inputs.py` "must not re-implement", so the
three inline derivations were a live violation of a shipped contract and F2 brought the code
into conformance with an existing spec statement rather than needing a new one.

**F3 stayed undispatched and untouched.** `git diff --numstat` on
`django_strawberry_framework/utils/permissions.py` is empty (the fourth `family_label`
spelling never moved); `resolvers.py` reads `23 12`, and the census below differences its
`+1` **by value** to Slice 3's raise rather than to any prefix work. No prefix helper exists
anywhere in the package.

### The pass-1 Medium and both Lows

Closed, verified against the files rather than the reports.

- Four full-message equality assertions present: `test_sets.py:2103`, `test_inputs.py:1656`,
  `:1684`, `:1795`. The new depth-2 row `test_inputs.py:1659`
  (`::test_fingerprint_propagates_deep_nested_configuration_error_unwrapped`) exists.
- **Zero surviving substring `match=` on any of the three arms** —
  `grep -n 'match="Explicit config error\|match="a specific nested\|match="a specific deep'`
  over both test modules returns nothing. That is the population the Medium and Low 1 named.
- Low 1's shortfall was real and is settled: Worker 3's recommended one-liner reaches 1 row
  (`revision-needed` by the acceptance rule), and the depth-2 fixture is what clears it,
  proved a second **detector** rather than a second **copy** by Worker 3's discrimination
  probe at the recursion seam. Worker 2 re-measured rather than carrying the figure, which
  is what caught it; I am not re-running a fifth mutation over a boundary two independent
  mutation shapes already agree on at 2 rows with identical node-id sets.
- Low 2 is a figure correction in **my own** prior sections and is settled below.
- **No production byte moved since the accepted review.** `shasum -a 256` on
  `rest_framework/inputs.py` reads `4d7b61b9e6b9ba046287f99f2632ed947a68abf4249a236854f38edb1b46a953`,
  byte-for-byte the digest Worker 3 recorded before its own pass-1 mutations;
  `git diff --numstat` reads `103 45` on that file and `24 37` on `sets.py`, the same pairs
  both reviews recorded.

### DRY check across this consolidation and every prior slice of the cycle

- **Cross-module repeated literals: 0**, against a `HEAD` control that reports 4 (above).
- **No cross-flavor duplication introduced.** The nested opt-in surface is DRF-only —
  `NestedSerializerConfig` / `nested_fields` appear in exactly three package modules plus
  the root lazy-export table and `mutations/sets.py`'s `Meta` slot, and neither `forms/` nor
  `mutations/` carries a nested-read translator the three new helpers could have duplicated.
- **No duplication against the cycle's other code changes.** The cycle's only other
  production edit is Slice 3's `_assert_field_agreement` fail-open fix in `resolvers.py`;
  its only new file is `tests/rest_framework/test_dry_import_ratchet.py`, a manifest table.
  Neither shares a shape with the consolidation.
- **No fail-open shape landed.** Read for the shape per
  `docs/builder/BUILD.md` `### Fail-open shapes` over the diff's added lines rather than
  trusting the suite; population printed (197 `^+` lines across the four files). Pattern
  `max(|min(|getattr(|\bor\b|except:|except Exception` returns 3 hits: two are the word "or"
  inside docstrings, and the third is `read_nested_serializer_fields`'s
  `except Exception as exc:`, which **raises** a typed `ConfigurationError` — it converts
  "the read blew up" into "rejected", the inverse of the catalogued shape. No clamp, no
  `getattr` default, no `or` fallback, no truthiness-on-absent among the added lines.
- **Failability records exist and carry every field `### What gets recorded` requires**, the
  byte-comparison revert included, for both passes' entries; neither is zero-row, so no
  **why 0** judgement is owed. Confirmed the record exists rather than re-deriving it.

### Gate and test results

| Gate | Command | Result |
|---|---|---|
| spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | **pass** — `OK: 38 terms`, unchanged across the whole cycle |
| citations | `uv run python scripts/check_citations.py --check` | **pass** — `OK: 965 citations resolve (810 in 442 .py files, 155 in KANBAN.md)`, the figure the consolidation raised it to; no reduction |
| source layout | not re-run — **this pass edits no file but this artifact**, and the consolidation's own four files were run explicitly by both builder passes | n/a |
| ruff format / check | not run — no `.py` file touched by this pass; the scoped-invocation rule has no files to scope to | n/a |

Focused runs, no `--cov*` flag anywhere (`--no-cov` on every one, required because
`pytest.ini` auto-applies `--cov`):

- `uv run pytest tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py --no-cov`
  — **190 passed**.
- `uv run pytest tests/rest_framework/ tests/mutations/ tests/utils/test_inputs.py tests/forms/ --no-cov`
  — **1222 passed**.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov`
  — **195 passed**.

All three reproduce both builder passes and Worker 3's re-runs exactly, the `+1` over pass
1's 189 / 1221 included. No full sweep was run here: `HEAD` is red from the concurrent
`spec-050` work at `4c483b6b` (Escalation C, carried), and the full sweep belongs to the
final gate in any case.

**Plan checkboxes.** This artifact carries **0** `- [ ]` boxes — a procedural-closure
integration pass states its findings as F1 / F2 / F3 prose rather than a
`### Dispatched findings checklist`, so the audit reduces to the three landings graded above.
The build plan's own two open boxes (`build-039-…:248-249`) are Worker 0's to mark and were
not touched.

### The settled census, re-derived once more with its pattern and population beside it

Five census errors have now occurred in this cycle, so this figure is derived from scratch
rather than confirmed. Instrument: Python `str.count` over source **text** — occurrences, not
matching lines — with `HEAD` obtained read-only as `git show HEAD:<path>` into a scratch path
outside the repo (necessary because `resolvers.py` is MIXED). Patterns spelled out as
parameters of the figure:

- **P1** = the **20** characters `"SerializerMutation ` — a double quote, the word, one space.
- **P2** = the **22** characters `f"SerializerMutation {`. P2 is a subset of P1.

| population | P1 at `HEAD` | P1 now | P2 at `HEAD` | P2 now |
|---|---|---|---|---|
| **`rest_framework/{resolvers,sets,inputs}.py` — the published subject** | **72** | **71** | **60** | **59** |
| all six `rest_framework/*.py` (adds `__init__.py` 1 / 1, 0 / 0) | 73 | 72 | 60 | 59 |
| whole package (adds `utils/inputs.py` 1 / 1, 0 / 0) | 74 | 73 | 60 | 59 |

Per file: `resolvers.py` 42 -> 43 (P1) and 39 -> 40 (P2); `sets.py` 16 -> 14 and 16 -> 14;
`inputs.py` 14 -> 14 and 5 -> 5.

**The figure the deferred catalog carries: 71 occurrences of the source text
`"SerializerMutation ` across `rest_framework/{resolvers,sets,inputs}.py` in the working
tree, of which 59 are the `f"SerializerMutation {` spelling; 72 / 60 at `HEAD`
(`4c483b6b`); counted as occurrences rather than matching lines.** That is Worker 3's settled
pair and Worker 2's recommended wording, and it reproduces here independently.

Two controls, because a census that can only agree with itself is not a measurement:

- **The instrument moves.** Respelling three P1 occurrences of `sets.py` in memory only (the
  repo was never touched) drops its count 14 -> 11.
- **Occurrences equal lines on this corpus today.** `grep -o … | wc -l` and `grep -c` both
  return 43 / 14 / 14, so every occurrence happens to sit on its own line. That is a property
  of these three files at this commit, not of the instrument, which is exactly why the
  published figure still owes "counted as occurrences" — the same trap Slice 2c's line-count
  figure fell into in the other direction.

Superseded by this section, and left unedited in place per `## Re-pass sections`: the **70**
in `### Notes for Worker 1` item 6 and in `### Summary` (a mis-addition — F3's own per-file
row 43 + 16 + 14 sums to 73, and no population yields 70), and Worker 3's pass-1 **73** for
`HEAD` (the correct pair for the pre-consolidation **working tree**, mislabelled).

### The fourth provisional-name derivation — decision: route to a card with F3

`rest_framework/resolvers.py:1213` spells
`f"{type(serializer).__name__}{'PartialInput' if operation == 'update' else 'Input'}"` on the
per-request path, once per write-surface field per mutation invocation. It is the only
executable `PartialInput` literal left outside `utils/inputs.py::generated_input_type_name`.
**Decision: not folded into this cycle; routed to a card, the same card that owns F3.** The
reason is not the fence — `resolvers.py` is a `.py` file and so inside the maintainer's fence,
though outside my own role scope (`docs/builder/worker-1.md` `## Scope`: no source edits) —
it is that the fix is **not mechanical**, and reading the code is what shows it:

1. **The duplication is not the suffix.** Routing this site through
   `generated_input_type_name(type(serializer).__name__, is_partial=operation == "update", …)`
   returns the identical string, so it retires one line and leaves both real hazards standing:
   the derivation reads the **runtime** serializer's class name where the schema-time sites
   read the **Meta** serializer class, and `operation == "update"` is an inline **rebuild of
   `mutations/operations.py::NON_DELETE_OPERATION_INPUT_KIND`** rather than a read of it.
   Measured: that map is `{create: CREATE, update: PARTIAL}`, so the inline test is correct
   today and silently wrong the day the operation table grows a third input-bearing entry.
2. **A correct fix needs an import edge the spec does not grant.** `resolvers.py`'s manifest
   row (spec:2725) permits 13 packages and its AST imports are exactly those 13 — verified in
   both directions. `NON_DELETE_OPERATION_INPUT_KIND` is re-exported through
   `mutations/sets.py`, which that row does **not** permit; `mutations/inputs.py`, which it
   does permit, exports only the `CREATE` / `PARTIAL` constants and not the map. So reading
   the shared table from `resolvers.py` is a manifest amendment, i.e. a contract change.
3. **The manifest is silent exactly where the fourth derivation lives.** `inputs.py`'s row
   names `generated_input_type_name` in the substrate it must not re-implement;
   `resolvers.py`'s row does not. That asymmetry is why the site is not covered by the
   prohibition the other three violated, and it is what the card must close **in the same
   change as the code** — writing the prohibition into a `SHIPPED` spec while the code
   violates it would convert a silent gap into a false completion claim, which is the
   divergence this integration pass exists to eliminate (`START.md`: amend the card, never
   let the spec silently demand the opposite).
4. **F3 is in the same file and is already card-owned**, and 40 of the 59 P2 occurrences are
   in it. One pass that owns `resolvers.py` should do both; two loops over one MIXED file is
   the more expensive and less reviewable split.

Restated at its measured width for the catalog, replacing the F2 entry's "derived twice":
**the provisional input-type name is derived four times outside its owner — three at schema
time in `rest_framework/inputs.py`, now retired against
`utils/inputs.py::generated_input_type_name`, and once per request in
`rest_framework/resolvers.py::_assert_field_agreement`, which spells the partial test a third
way by rebuilding `NON_DELETE_OPERATION_INPUT_KIND` inline and derives the name from the
runtime rather than the Meta serializer class.**

### `rest_framework/inputs.py:1617` — verdict: a deliberate swallow, not a fail-open

Confirmed intentional on three independent readings, so the reconciliation Worker 3 recorded
does not have to be done a third time.

1. **Its result routes the caller onto the restrictive branch.**
   `_default_full_shape_identity` returns `None`, and at `inputs.py:1738` that makes
   `is_full_shape = False`, so the shape takes a **descriptor-derived** name and the canonical
   `<Serializer>Input` name stays unreserved. "Cannot determine the default identity" therefore
   **exits** the canonical-name path instead of being coerced onto it — which is literally the
   corrected shape `docs/builder/BUILD.md` `### Fail-open shapes` prescribes, not the defect it
   catalogues. A fail-open needs a permit on the far side of the `except`; there is none here.
2. **The catch is typed, not bare.** `except ConfigurationError` catches the framework's own
   configuration signal; it is neither a bare `except` nor `except Exception`, so it is not the
   "a check blew up therefore it passed" form.
3. **The enclosing docstring specifies it as contract**, naming the reason the default shape
   must not reject a valid hook-provided one ("The default shape exists ONLY to reserve the
   canonical name; when it cannot be built it simply does not reserve it") and stating that
   EVERY step is deliberately inside the guard.

And the population reconciliation stands as Worker 3 recorded it:
`grep -c 'except ConfigurationError:'` over that file returns **3** (`:305`, `:470`, `:1617`)
where the `/ raise` predicate returns **2**, because the third arm is this `return None`
swallow. The two failability anchors partition the two pass-through arms exactly.

### Instrument hazards — measured, and routed rather than edited

Both are `docs/builder/BUILD.md` edits, which this cycle's fence excludes, and the corpus
ratchet governs them. Recorded with the correction each needs and with a population Worker 3's
routing under-counted.

**Hazard 1 — the bare-`/tmp` scratch path. The population is three recipes in two standing
docs, not one.** Printed:

| site | lines | recipe |
|---|---|---|
| `docs/builder/BUILD.md:528-531, 536` | 5 | floor venv (the one Worker 3 named) |
| `docs/builder/BUILD.md:228, 231, 232` | 3 | failability-proof copy / restore / byte-compare |
| `START.md:96-99` | 4 | the **same** floor recipe, second copy |

`START.md:42` forbids bare `/tmp` for temp files in the same document that then prescribes it
four lines at a time — and repairing only `BUILD.md` leaves `START.md`'s copy live, which is
`START.md`'s own "sweep both files of a pair". `scripts/prove_failability.py:86` carries a
fourth site, but in a docstring example only: its code resolves
`tempfile.gettempdir()` (`:565`), which honors `TMPDIR`, so the executable is already correct.
**Correction needed:** each recipe writes to the session scratchpad; `BUILD.md`'s floor recipe
is the canonical one and `START.md`'s fence collapses to the pointer it already carries
("Floor values from BUILD.md at run time"), which is where the ratchet's retired bytes come
from.

**Hazard 2 — the missing "prove it IS a venv" step, and the pipe's exit status.** Confirmed
with a control rather than reasoned: `false | tail -3` exits **0** here and its `&&` successor
**runs**; `set -o pipefail` makes the same pipe exit 1. So a refused `uv venv` plus two refused
installs can read as a clean run with the failure text scrolled past. Two things separate the
halves of this hazard:

- The pipe is the **caller's** addition to trim output; no `tail -` appears anywhere in
  `BUILD.md`, so there is no pipe in the corpus to remove.
- The corpus-level gap is the missing assertion. `grep -n 'pyvenv\|sys.prefix'` across
  `BUILD.md`, `ARTIFACT.md` and all four `worker-*.md` returns **0** — nothing asks a floor run
  to prove its directory is a virtual environment before trusting it. **Correction needed:**
  `### How to build the floor venv` asserts `pyvenv.cfg` present and `sys.prefix` inside the
  scratch path (with `sys.base_prefix` outside it) and records that assertion beside the
  resolved versions, so a scratch path that later decays is still auditable.

**No recorded floor claim in this cycle is falsified**, and I agree with Worker 3's measurement
of why: a floor invocation at a decayed path fails loudly at the first `import django`, never
silently green, so the recorded `497 passed` could not have been produced by the decayed state
— and pass 2's independent rebuild reproduces it as `498` (497 plus the new row). What does not
survive is the record's **identity**: a scratch path is not an instrument identity, which is
the whole reason hazard 2's assertion is worth its bytes.

### Spec reconciliation — no spec edit owed by the consolidation

Decided by reading the spec against the diff rather than by accepting three passes' agreement.
Every candidate and why it needs nothing:

- **The messages.** The spec states the nested-serializer opt-in contract and the override
  requirement, never a message's spelling. Every relocated string is proved byte-identical.
- **The `### Import manifest` (spec:2709-2727).** Module granularity, so adding three symbols
  to `sets.py`'s existing `from .inputs import (…)` statement leaves it exact. Re-verified in
  both directions by AST over all six modules; `sets.py` already imports from `.inputs` and
  `inputs.py` imports nothing from `sets.py`, so the one-way direction is intact. And the row
  that matters most already names `generated_input_type_name` — the spec was ahead of the code,
  not behind it.
- **Every spec citation of an affected symbol still resolves and still asserts a true
  property.** `_resolve_nested_field` (spec:3783), `build_serializer_input_class` (spec:1753,
  :3626), `describe_serializer_input` (spec:1342, :3467, :3627), `_assert_field_agreement`
  (spec:2008, :3580) — nothing was renamed or deleted, only re-pointed, and
  `describe_serializer_input`'s returned string is proved character-identical. `OK: 965`
  independently.
- **The two DoD-adjacent contracts the consolidation touches** — the unwrapped-propagation
  guarantee and the canonical-name reservation — are both stated in the spec already and are
  now, for the first time, pinned by assertions that can detect their absence. A spec that gains
  a test does not gain a sentence.

The one place a spec edit is *tempting* is `resolvers.py`'s manifest row, and taking it would
be the defect: see the fourth-derivation decision above.

### Summary

The consolidation loop closes accepted. F1's four cross-module fragments are retired to a
measured **0** against a `HEAD` control that reports **4**, in a shape wider than my own
routing specified and better for it — the shared `try` / `except` block and the shared
`isinstance` predicates went with the strings, and each of the four new names has a live caller
in both modules. F2's three schema-time derivations are retired against
`utils/inputs.py::generated_input_type_name`, which the spec's own import manifest had already
named as substrate `inputs.py` must not re-implement, so the consolidation closed a live
violation of a shipped contract rather than inventing one. F3 stayed undispatched and
untouched, differenced by value. The pass-1 Medium and both Lows are closed with zero surviving
substring `match=` on the three arms, four equality assertions in place, and a depth-2 row
proved a second detector rather than a second copy; no production byte moved since the accepted
review, by digest and numstat. Gates hold at `OK: 38 terms` and `OK: 965`, and 190 / 1222 / 195
reproduce.

The census is settled at **71 / 59** in the working tree and **72 / 60** at `HEAD`, with the
20- and 22-character patterns and the three-module population travelling beside the number and
two controls under it. My own prior **70** was a mis-addition and stands unedited per the
append-only rule; the correction of record is here. The fourth provisional-name derivation is
routed to F3's card rather than folded in, because the real duplication is an inline rebuild of
`NON_DELETE_OPERATION_INPUT_KIND` whose correct fix needs an import edge the manifest does not
grant — and writing that prohibition into a `SHIPPED` spec ahead of the code would be a false
completion claim. `inputs.py:1617` is confirmed a deliberate deny-shaped swallow, not a
fail-open, on three independent readings. Both instrument hazards are routed with their
corrections and with a bare-`/tmp` population of three recipes across two standing docs where
the escalation named one; neither falsifies a recorded floor claim in this cycle.

### Spec changes made (Worker 1 only)

**None.** The consolidation obliges no spec edit — every candidate is enumerated with its
reason under `### Spec reconciliation` above, and the one tempting edge case (adding
`generated_input_type_name` to `resolvers.py`'s manifest row) is deliberately withheld to the
card that will fix the code in the same change. The spec and its companion are byte-unchanged
by this pass; the only files it writes are this artifact and
`docs/builder/worker-memory/039-worker-1.md`.

No slice checklist box is deferred: this artifact carries none.

### Routed to `bld-039-final.md`'s `### Deferred work catalog`

Every item has a named owner. Items 1-2 are the same card.

1. **F3 — the `SerializerMutation ` message prefix.** **71** occurrences of the source text
   `"SerializerMutation ` across `rest_framework/{resolvers,sets,inputs}.py` (per file 43 / 14
   / 14), of which **59** are `f"SerializerMutation {` (40 / 14 / 5); **72 / 60** at `HEAD`
   (`4c483b6b`); counted as occurrences, not matching lines. Plus a fourth spelling in
   `utils/permissions.py::request_from_info(family_label="SerializerMutation")`. Several are
   `pytest.raises(match=…)` anchors. **Owner: the maintainer**, own card.
2. **The fourth provisional-name derivation**, `rest_framework/resolvers.py::_assert_field_agreement`
   — per-request, third spelling of the partial test, inline rebuild of
   `NON_DELETE_OPERATION_INPUT_KIND`, and derived from the runtime rather than the Meta
   serializer class. Needs an import-manifest amendment, so it is a contract change, not a
   consolidation. Same file and same card as item 1; the manifest row must move in the same
   change as the code. **Owner: the maintainer.**
3. **Escalation A** — should the DRY import ratchet hold the spec's named promotions, the whole
   measured shared substrate, or the `### Import manifest` population; and should the **forms**
   flavor get one. Two concrete rows for the answer to weigh, neither added by this cycle:
   `utils/inputs.py::generated_input_type_name`, now load-bearing at four
   `rest_framework/inputs.py` call sites and absent from `SHARED_BINDINGS`' 19 rows; and the
   three new `rest_framework/inputs.py` helpers, which `sets.py` now imports and which
   `sets.py`'s manifest column does not name. **Owner: the maintainer**, contract-level.
4. **Escalation C** — `HEAD` is red from the concurrent `spec-050` cycle at `4c483b6b` in four
   modules this cycle does not touch, and this cycle did not make it red. The final gate cannot
   record a green full sweep until it is resolved. **Owner: the maintainer.**
5. **Instrument hazard: bare `/tmp` in three recipes across two standing docs.**
   `docs/builder/BUILD.md:528-531,536` (floor venv), `:228,231,232` (failability proof), and
   `START.md:96-99` (a second copy of the floor recipe). `START.md:42` forbids it. Correction
   and the ratchet's retirement route are in `### Instrument hazards` above. `scripts/prove_failability.py:86`
   is a docstring-only fourth site; its code already honors `TMPDIR`. **Owner: the maintainer**,
   corpus ratchet applies.
6. **Instrument hazard: no recipe asks a floor run to prove its directory is a venv**
   (`pyvenv.cfg` + `sys.prefix`; 0 hits across `BUILD.md`, `ARTIFACT.md`, all four
   `worker-*.md`), and `uv venv … | tail -3 && …` reports the pipe's exit status — controlled:
   `false | tail -3` exits 0 and its successor runs. No recorded floor claim in this cycle is
   falsified. **Owner: the maintainer**, corpus ratchet applies.
7. **The owner-name asymmetry in the two `Meta.nested_fields` rejections.** The same
   `SerializerMutation <name>` slot renders the MUTATION class name from `sets.py` and the
   SERIALIZER class name from `inputs.py`, depending on which depth of the opt-in tree
   rejected. Pre-existing, preserved byte-for-byte because changing it inside a consolidation
   would be a behavior change wearing a refactor's diff. **Owner: the maintainer**, worth a
   decision.
8. **`BACKLOG.md:31`** still reads `spec-039 rev6 #4/#13`, the last `rev6`-vocabulary citer in
   the tree; repair text recorded by Slice 2c. Outside the fence. **Owner: the maintainer.**
9. **`spec-036`'s severity-ordinal labels: 115 own-voice occurrences over 12 tokens**
   (`H1`-`H5`, `M1`-`M7`), not the 146 first published — 31 of the 147 both-bounded population
   are `G2` / `G2-handoff`, `spec-035`'s goal vocabulary that every strip deliberately kept as
   foreign-spec. Whether `spec-036` owes the same strip is a scope question. **Owner: the
   maintainer.**
10. **`KANBAN.md:375`'s `spec-039` inventory is discharged and the board does not know** (all
    19 stranded-ordinal sites gone; the same item's "no rationale companion" claim falsified by
    Slice 0). Kanban DB writes are outside the fence. **Owner: the maintainer.**
11. **Nine `TODO-ALPHA-040-0.0.13` card ids in this spec** name a card that is
    `DONE-040-0.0.13`. Already an owned, measured board population (`KANBAN.md:618`) whose
    ruling is that the class splits three ways with only one third mechanical. **Owner: that
    card**; not pre-empted here.
12. **`examples/fakeshop/apps/kanban/constants.py` is stale for
    `tests/rest_framework/test_dry_import_ratchet.py`** — verified live: `:243-248` lists six
    `tests/rest_framework/` files and not the new one, and the `kanban-tracked-path-constants`
    hook reads `git ls-files`, so today's green `uvx pre-commit` is `START.md`'s documented
    fail-open. Remedy: `uv run python scripts/build_kanban_tracked_path_constants.py` after
    `git add`, landed as a constants-only sync commit. **Owner: commit time.**
13. **`tests/rest_framework/test_dry_import_ratchet.py:3-8`'s ragged docstring wrap** — still
    present, cosmetic, no gate sees it, and Worker 1 may not edit tests. No consolidation pass
    remains to fold it into. **Owner: the maintainer**, or the next pass that opens that file.

Recorded so it is **not** re-derived a fourth time, and not a deferral:
`rest_framework/inputs.py:1617`'s `except ConfigurationError: return None` is a deliberate,
deny-shaped swallow specified by its own docstring, which is why a bare
`grep -c 'except ConfigurationError:'` returns 3 where the `/ raise` predicate returns 2.

### Final status

`final-accepted`.

The consolidation the integration pass routed landed in full and measurably: F1 to a controlled
zero, F2 against an owner the spec had already named, F3 untouched, the pass-1 Medium and both
Lows closed with no surviving substring `match=`, no production byte moved since the accepted
review, both gates unchanged, and 190 / 1222 / 195 reproducing. The census is settled with its
pattern and population attached and two controls under it. No spec edit is owed and none was
made. Every residual item carries a named owner and none needs Worker 2: the fourth
provisional-name derivation and F3 route to one card over `resolvers.py`, Escalations A and C
and both instrument hazards route to the maintainer, and the rest are the standing carries.

The build cycle's remaining step is the final test-run gate (`docs/builder/bld-039-final.md`),
which cannot record a green full sweep while Escalation C stands.

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
