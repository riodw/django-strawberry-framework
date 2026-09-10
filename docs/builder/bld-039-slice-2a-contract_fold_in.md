# Build: Slice 2a — fold the shipped contract into the spec's Decisions

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (whole document)
Rationale companion: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`
Status: final-accepted

This is a **procedural-closure slice** in the shape `docs/builder/BUILD.md`
`### Procedural-closure slices` describes: a spec-only pass with no builder and no
reviewer, closed by one Worker 1 pass carrying a combined Plan + Final-verification block.
The maintainer's instruction that a spec-only change needs no builder is recorded in
`docs/builder/build-039-serializer_mutations-0_0_13.md` `## Slice 2 split, and why`.

---

## Plan (Worker 1)

### Scope and fence

**In scope:** `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`, its rationale
companion under `docs/SPECS/appx/`, and this artifact.

**Out of scope, deliberately:** every `.py` file (Slice 2b owns the comment sweep), the
`P1.x` / `P2.x` / `F<N>` / `M<N>` / `H<N>` process-label vocabulary (Slice 2b strips it,
re-points the three headings whose GitHub anchors change, and sweeps the 21 citing comment
lines), and everything the cycle fence already excludes — `KANBAN.md` / `KANBAN.html`,
`docs/GLOSSARY.md`, `docs/TREE.md`, `TODAY.md`, `README.md`, `docs/README.md`,
`CHANGELOG.md`, `GOAL.md`, kanban-DB writes.

### Input population

`53` graded-non-conformant contract rows out of the 318 the four audits graded, plus the
`8` spec deferrals `docs/builder/bld-039-slice-3-code_gaps.md`'s two
`## Final verification (Worker 1)` sections handed forward.

| Source | SPEC-STALE | DEVIATED | SUPERSEDED | PARTIAL | DROPPED |
|---|---|---|---|---|---|
| `bld-039-audit-1-converter_and_inputs.md` | 9 | 0 | 0 | — | 1 |
| `bld-039-audit-2-sets_and_bind.md` | 9 | 0 | 3 | — | 0 |
| `bld-039-audit-3-resolvers_and_live.md` | 8 | 3 | 3 | 3 | 0 |
| `bld-039-audit-4-decisions_rev6_dod.md` | 10 | 0 | 5 | — | 0 |
| **total** | **36** | **3** | **11** | **3** | **1** |

The one DROPPED row (1a's D6, the DRY import guard) was closed in code by Slice 3; what
this pass owes it is the spec sentence that described the guard as a grep.

### Governing rule

`docs/builder/BUILD.md` `## Spec rationale extraction`: the spec states the corrected
contract directly, with no chronology, no amendment block, and no "as of round N" hedge;
what changed, why, and what it replaced goes in the rationale companion, keyed to the
Decision it belongs to. Applied literally throughout — every `**Post-ship:**` entry in the
companion has a corresponding present-tense rewrite in the spec, and no rewritten spec
passage names a date, a round, or a revision.

### The hardening fold — the pass's largest item

The spec carried a **178-line** `> **Post-ship hardening revision (2026-07-15, on `main`
after `0.0.13`).**` blockquote (spec lines 55–232 at pass start) and, inside the Slice-3
checklist, a bracketed `**[superseded by the 2026-07-15 hardening revision — …]**` clause.
Both are chronology in framing. Both were, in substance, the **only** statement in the
spec of the current hook contract, the alias guard, the phase separation, the drift
snapshot, the relation-intent ledger, and the post-save attestation — while Decisions 7, 8
and 12 still asserted the superseded shape.

So the plan is a **fold, never a deletion**: each bullet's contract moves into the Decision
body that owns it, rewritten in the present tense as the rule; then the blockquote and the
bracketed clause go; then the rationale records what the hardening changed and why. Audit
3's 20-row mapping table is the assignment; the two rows it marks **nowhere** and the two
whole modules it marks **zero spec mentions** get a home written from `HEAD`.

### Method

1. Read every input artifact and the whole spec.
2. Re-derive every figure from `HEAD` (or the worktree for
   `rest_framework/resolvers.py`, which carries this cycle's uncommitted Slice-3 change)
   before writing it — `docs/builder/BUILD.md` `## Claims are proven mechanically`. No
   number was carried forward from an artifact.
3. Cross-check the **five homes** (`START.md`) for every contract touched: Decision, slice
   checklist, `## Edge cases`, `## Test plan`, `## Definition of done`. Two disagreeing is
   the defect; this cross-check is the instrument no single slice runs, and it is what
   found the three-homes-three-states split on the hook contract.
4. Audit link definitions in both directions and in-page anchors after the last edit.
5. Run the three gates.

### Deferred by construction

No `.py` edit. No process-label edit. Anything either would require is recorded under
`### Notes for Worker 1 (spec reconciliation)` below.

---

## Final verification (Worker 1)

### Discharge accounting

**53 of 53** graded-non-conformant rows discharged. **8 of 8** Slice-3 deferrals
discharged (deferral 8 was "no change owed", recorded and confirmed rather than edited).
**0 deferred.**

Byte / line count, measured after the last edit:

| File | Before (post-Slice-0) | After |
|---|---|---|
| `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | 296,665 B / 3,725 L | 316,338 B / 3,944 L |
| `docs/SPECS/appx/…-rationale.md` | 95,992 B / 1,390 L | 122,960 B / 1,717 L |

The spec grew despite losing a 179-line block because the fold replaced one narrated
blockquote with contract prose distributed across six Decision steps, and because eleven
mechanisms that had **no** statement anywhere now have one. The corpus ratchet
(`docs/builder/BUILD.md` `## The corpus ratchet`) governs `BUILD.md` / `ARTIFACT.md` /
`worker-*.md` only; no file under that ratchet was touched.

### Gate results

| Gate | Command | Result |
|---|---|---|
| source layout | `uv run python scripts/check_trailing_commas.py docs/SPECS/spec-039-serializer_mutations-0_0_13.md docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` | **pass** — `Fixed 0 file(s).` (explicit paths only; never repo-wide) |
| spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | **pass** — `OK: 38 terms - all have glossary entries and at least one spec link.` (unchanged) |
| citations | `uv run python scripts/check_citations.py --check` | **pass** — `OK: 963 citations resolve (808 in 442 .py files, 155 in KANBAN.md)` (unchanged; no reduction) |

**Three checks the gates cannot perform, run by hand:**

- **Every `path::Symbol` in the spec resolves.** `check_citations.py` reads `.py` and
  `KANBAN.md` only, so it sees none of the spec's. An AST pass over
  `django_strawberry_framework/`, `tests/` and `examples/` resolved all **43** distinct
  `path::Symbol` citations in the spec, allowing the spec's `serializer_converter.py::X` /
  `inputs.py::X` shorthand for `rest_framework/`. Before the fixes below it reported **9**
  unresolved.
- **Link definitions, both directions, in both files.** `0` undefined refs and `0` orphan
  definitions in the spec and in the companion, after stripping fenced blocks. Four new
  definitions were added to the spec (`rf-hook-context`, `utils-write-transaction`,
  `test-dry-ratchet`, `test-soft-dependency`) and one to the companion
  (`mutations-inputs`), each in its target's canonical group header and alphabetical
  within it.
- **In-page anchors.** `20` in the spec and `18` in the companion, `0` dangling in either;
  `0` dangling cross-file anchors into the spec from any tracked `.md`. One heading's text
  changed (rev6 #14's title), and nothing links to it by anchor.

**Process labels are intact.** Instrument:
`(?:^|[^A-Za-z0-9_])((?:P|F|M|H|D)[0-9]+(?:[.-][0-9A-Za-z]+)?)`, the same one Worker 0
published. **37 distinct tokens**, matching Worker 0's measured 37 exactly (`P1`,
`P1.1`–`P1.7`, `P2`, `P2.1`–`P2.7`, `P3`, `F1`–`F11`, `M1`–`M5`, `H2`, `H3`, `H5`, `H6`);
no token was lost. Occurrences moved 175 → **186**, upward, because several rewrites cite a
promotion the prose previously left implicit. Slice 2b's population is therefore intact and
slightly larger, never smaller.

### Spec changes made (Worker 1 only)

Grouped by driving finding. Every row names the spec heading, the reason, and the audit row
or deferral behind it.

#### A. The hardening fold (audit 3 Notes item 1; audit 3 rows A1g, B1.4, D4; the 20-row mapping table)

| # | Spec heading | Change | Driven by |
|---|---|---|---|
| A1 | document head, lines 55–232 | Deleted the 179-line `> Post-ship hardening revision` blockquote after folding every bullet into a Decision body. | audit 3 Notes 1 |
| A2 | `### Decision 8`, preamble | New: the pipeline alias guard (no read/write classification, rejection before execution), the authorization phase's database-enforced read-only barrier and fail-closed backend rule, the trust boundary it does **not** claim, and the pinned-connection phase separation with the `serializer.save()` savepoint. Also names `utils/write_values.py` and `utils/errors.py`, which the spec mentioned **zero** times. | audit 3 mapping rows 14, 20, 21 |
| A3 | `### Decision 8` step 1 | New: the post-locate `authorized_pk` / `target_state` snapshot, by-value capture of mutable containers and `FieldFile`, and `pks_match` canonicalization. | audit 3 mapping row 13 |
| A4 | `### Decision 8` step 4 | Rewritten end to end. Framework-built `data`; the constructor-only hook; the frozen `SerializerHookContext` / `UploadMetadata` view and its recursive, cycle-rejecting, fail-closed freeze; the `_hook_mapping` typed boundary; reserved keys checked by omission sentinel + identity with **any** `instance` refused; the agreement guards; the runtime writable-`source` walk; relation-queryset scoping. | audit 3 B1.4 + mapping rows 1–8 |
| A5 | `### Decision 8` step 5 | New: the relation-intent ledger's record-and-assert-by-identity contract, `_pin_validator_querysets`, and the flattener's iterative / cycle-rejecting / budget-capped shape. | audit 3 mapping rows 9, 16 + Medium-3 |
| A6 | `### Decision 8` step 6 | New: drift rejection before `save()`, the pre-save M2M snapshot, the write witness with its signal-time pk snapshot, and `_checked_saved_result`'s six conditions. | audit 3 mapping rows 10–12 |
| A7 | `## Slice checklist` → Slice 3 resolver bullet | Deleted the bracketed `[superseded by …]` clause and rewrote the construct step to the shipped contract. | audit 3 A1g |
| A8 | `## Definition of done` item 4 | Same rewrite; it was the third home, and the only one carrying **no** marker at all. | audit 3 D4 |
| A9 | `## Edge cases` → `get_serializer_kwargs` (H3) | Removed the inline `(the 2026-07-15 hardening revision made …)` parenthetical; the clause states the ownership directly. | audit 3 E3 |
| A10 | `### rev6 #12` | Same, for the "widened this from input-spec names" clause. | audit 3 E3 class |

#### B. The `register_subsystem_clear` row shape — four homes (audit 1b A18 / A19 / G8 / H1)

| # | Spec heading | Change |
|---|---|---|
| B1 | `## Slice checklist` → Slice 2 finalizer sub-block | Zero-argument callable + stable `owner` + `before_bind`; string rejected; laziness from the registration site. |
| B2 | `### Decision 6`, cross-flavor paragraph | Same contract, one sentence. |
| B3 | `## Definition of done` item 3 | Same contract. |
| B4 | `### Cross-flavor reuse…` → **P1.6** table cell | Same contract in the "Promote to" and "Serializer obligation" columns. |
| B5 | `## Implementation plan` Slice-2 row | Same contract. |

Measured at `HEAD`: `registry.py::register_subsystem_clear(clear, *, owner, before_bind=False)`
raises `TypeError` on a non-callable. Superseding commit `48f9f65d` recorded in the
companion under Decision 6, never in the spec.

#### C. "One net-new public symbol" is seven (audit 1b A22 / B1; audit 4 escalation 11)

| # | Spec heading | Change |
|---|---|---|
| C1 | `### Decision 5` | Enumerates all seven `_DRF_SOFT_EXPORTS` names, each pointed at the rev6 item or hook contract that introduced it, with the lazy / guarded / out-of-`__all__` contract kept verbatim. Audit 4's escalation offered (a) enumerate or (b) scope to `SerializerMutation`; **(a)** taken, reasoning recorded in the companion. |
| C2 | `## Slice checklist` → Slice 2 `__init__.py` bullet | Points at `_DRF_SOFT_EXPORTS` as the enumeration. |
| C3 | `## Definition of done` item 8 | Lists all seven; its substantive clause survives verbatim. |
| C4 | `### Decision 12` import table + F1 paragraph | Both rows and the `__all__` paragraph now speak of the seven soft exports, not one name. |

#### D. `_validate_meta` scope and the allowed-key set (audit 1b A8 / A41 / G4)

| # | Spec heading | Change |
|---|---|---|
| D1 | `### Decision 6` closing line | Enumerates the shipped validator: `serializer_class`, `optional_fields`, `injected_fields`, `select_for_update`, `nested_fields`, schema-field-map validation, fingerprint capture, recursive writable-`source` walk. |
| D2 | `## Slice checklist` → Slice 2 `**DRY / reuse**` | The near-identical second home, same enumeration. |
| D3 | `### Cross-flavor reuse…` → **P2.5** | Same; also drops the deleted `_normalize_field_sequence` precedent. |
| D4 | `## Slice checklist` → Slice 2 `sets.py` bullet | Allowed-key set restated as `MODEL_BACKED_WRITE_META_KEYS` + `serializer_class` / `optional_fields` / `injected_fields` / `nested_fields`. |
| D5 | `### Cross-flavor reuse…` → **P2.7** | Same set. |
| D6 | `## Definition of done` item 3 | The `Meta` matrix widened by the five checks it omitted. |

#### E. `FieldError` is additive, not frozen (audit 4 High-3)

`## Non-goals` bullet 2, `### Decision 2`, `## Goals` item 3, the document head's
"byte-identical" opener, the `## Key glossary references` envelope bullet, and the
`## User-facing API` comparison row. The same bullet's false second clause ("does not
re-open `mutations/inputs.py`") is corrected in the same edit — that is where `codes` /
`path` and the shared leaf live.

#### F. Decision 7's six corrections (audit 1a E9 / E2 / E15 / A8 / B5 / B6)

| # | Spec heading | Change |
|---|---|---|
| F1 | `### Decision 7` → "Nullability and defaults (M2)" first bullet | Nullable when `allow_null=True` **or** optional, with an `UNSET` default; only `required=True, allow_null=False` emits the bare non-null annotation. The highest-value rewrite in the set: the old sentence, implemented, emits non-null optional inputs, which GraphQL treats as required. |
| F2 | `### Decision 7` → converter dispatch paragraph | The ordered six-entry precheck table, the nested-serializer-first rule, and the broad-`RelatedField`-then-reject-non-PK contract the spec stated nowhere. |
| F3 | `### Decision 7` → model-column overlap | New paragraph: relation cardinality agreement and kind re-derivation from the serializer field. |
| F4 | `### Decision 7` → "Reverse map" **and** `## Slice checklist` Slice 1 converter bullet | Nine axes, six kinds, `InputFieldSpec`. |
| F5 | `### Decision 7` → "Shape identity…" **and** the Slice-1 inputs bullet | Descriptor carries `descriptions` as an independent axis and the post-widening annotation repr. |
| F6 | `### Decision 7` → "Naming + dedupe" | Canonical name granted only on identity with the default no-arg discovery. |
| F7 | `## Edge cases` → two-writable-`source` row | Uniqueness spans inputs **and** `Meta.injected_fields`, plus the runtime re-check. |

#### G. Symbol names that do not exist (audit 3 "Stale symbol names the citation gate cannot see"; audit 4 Medium-1 / Medium-2)

| # | Sites | Change |
|---|---|---|
| G1 | 11 occurrences of `_visible_related_object` | → `utils/querysets.py::visible_related_object`, with the batched `visible_related_objects` named where rev6 #3 uses it. |
| G2 | `### rev6 #2` | `_assert_injected_field_agreement` (0 occurrences) → the unified `_write_surface_specs` walk through `_assert_schema_runtime_agreement`. |
| G3 | `### rev6 #3` | `_type_check_relation_id` → `utils/write_values.py::type_check_relation_id`. |
| G4 | `### Decision 4` "Shared-helper homes" | `visible_related_object`'s real home; the non-delete ops constant → `mutations/operations.py`; `mutations/bind_helpers.py` (never created) dropped; `utils/write_values.py`, `utils/errors.py` and `FieldConversionBase` added. |
| G5 | `### Decision 4` module list | `rest_framework/__init__.py` and `hook_context.py` added. |
| G6 | 4 P-table cells | `_VALID_FORM_OPERATIONS`, the model id-set decoder + its four error helpers, the form's own model-backed sync pipeline, and `FormInputFieldSpec` — all deleted by the promotions the table describes — restated by content rather than by dead symbol name. |
| G7 | **P2.3** ×3, **P2.5**, **P1.2** ×2, `## Slice checklist` ×2, `### Decision 10` | `_pascalize_token` → `utils/inputs.py::pascalize_token`; `_normalize_field_sequence` / `normalize_form_field_sequence` (both deleted) → the one `normalize_field_name_sequence`; `NON_DELETE_WRITE_OPERATIONS` → `mutations/operations.py` via `require_non_delete_operation`. |
| G8 | `### Small reuses to pin (P3)` | `graphql_camel_name` is in `utils/strings.py`, not `utils/inputs.py`; `pascal_case` added; the `utils/relations.py` trio replaced by what is actually imported; `convert_choices_to_enum` → `build_enum_from_choices`; the "`utils/strings.py` deliberately NOT applicable" bullet narrowed to `snake_case`, since it falsified the pin two paragraphs above it. |

#### H. `run_write_pipeline_sync` is universal (audit 3 High-2, rows B1.11 / A6)

`### Decision 8` DRY paragraph, the **P1.5** table cell, and the Slice-3 DRY bullet. All
three said "scoped to model-backed create/update only … not a universal write skeleton
(**F6**)". `HEAD`'s own docstring says "the shared write orchestration every mutation
flavor rides"; delete, the model-less plain form, and the auth flavor all ride it. Rewritten
to the three seams (`decode_step` / `write_step` / `tail_step`) and the `{ ok: true }` tail;
the F6 reversal is recorded in the companion.

#### I. `save_or_field_errors` (audit 3 Medium-2, rows A1i / B1.6 / E10 / E11)

Four homes said the serializer write is wrapped by that `036` mapper; the serializer does
not import it. All four now name `utils/errors.py::integrity_error_field_errors`, and the
step-6 body explains why the deviation exists (the wrapper's shape assumes a caller holding
the instance, and the savepoint containment needs the return value).

#### J. rev6 items (audit 4 High-1 / High-2 / Low-1; deferral 6)

| # | Spec heading | Change |
|---|---|---|
| J1 | `### rev6 #14` | Retitled off "Optional"; default is `True`, opt-out is `False`, shared across all three model-backed flavors through one validator; `locate_instance`'s keyword default corrected. |
| J2 | `### rev6 #12` | Signature `(self, info, *, data, hook_context)`; **both** guards named; `owner=request.user` replaced (it is now rejected); the live fixture corrected to `stamp` — `topic` is the *negative* fixture. |
| J3 | `### rev6 #1` | The unified `_write_surface_specs` walk; the requiredness and annotation-`repr` drift arms; the meta arm stated as a **raise** under both incoherent spellings, with the `operation` + `optional_fields` snapshot requirement as a contract sentence (deferral 6). |
| J4 | `### rev6 #17` | Empty-declaration carve-out. |

#### K. The DoD check the spec described as a grep (audit 1a D6; deferrals 1–3)

`## Slice checklist` → Slice 1 `**DRY / reuse**`. Replaced "A grep guard … is the DoD
check" with the shipped object-identity ratchet at
`tests/rest_framework/test_dry_import_ratchet.py`, its parametrized
`(consumer, symbol, owner)` manifest and `__code__`-identity second manifest, the
population stated explicitly instead of by the pronoun "these" — including **P2.1's both
shapes** — and the interned-`str` ceiling on the four kind-constant rows stated honestly.
Population transcribed from the shipped 19-row + 2-row manifest, re-read this pass.

#### L. The import manifest (audit 1a F1 / F2; audit 1b G7; audit 1c C4; deferrals 4–5)

`### Import manifest` rewritten from per-symbol to **per-module** granularity, plus a
per-module "substrate it must not re-implement" column. Audit 1c escalated three resolution
paths and left the choice to Worker 1; **(b)** taken — module granularity — because all
four rows were stale at once, a re-derived per-symbol list goes stale again on the next
legitimate move *inside* a permitted module, and the per-symbol obligation that genuinely
needs a ratchet already has an executable one. Rows measured from the actual relative
imports of all six `rest_framework/` modules. Retiring the manifest was rejected: the DoD
cites it. The `### Confirmed reuse` bullet was corrected in the same pass — the serializer
imports `run_write_pipeline_sync` + `make_resolver_entries`, not the eleven `036` helpers
it named, and reaches the rest *through* the skeleton, which is the point of P1.5.

#### M. DRF-absent simulation (audit 4 High-4)

`### Decision 12` item 3 and the `## Test plan` DRF-absent bullet. Both prescribed
monkeypatching `builtins.__import__`. `START.md` bans it and the guards use
`importlib.import_module`, so the patch leaves the guard unreached and the test passes
without exercising anything. Both now name
`tests/_soft_dependency.py::simulated_absence`'s `sys.modules[…] = None` sentinel, say why
the `__import__` patch does not intercept, and record the fresh-subprocess root-import
check the spec never described.

#### N. Archived paths (audit 4 Medium-3; audit 4 Notes 7)

`### Decision 1` states the stem convention and the archived location; `## Definition of
done` item 1's command was unrunnable as written and now names `docs/SPECS/` /
`docs/SPECS/appx/` and records the measured `OK: 38 terms`.

#### O. Present-tense claims that became claims about today (audit 4 Low-3, Notes 8–9)

`## Goals` item 8 (re-tensed, prediction held), `## Out of scope`'s `TestClient` row and
version-bump row, `## Edge cases` row 24's "byte-unchanged", `## Edge cases` row 11's
"still await the `0.0.14` TestClient" (which contradicted its own slice's checklist), the
`many=True` row's "verify against the installed DRF when Slice 1 lands" hedge, the F4
paragraph's twin hedge, and the head paragraph's "`docs/GLOSSARY.md` carries … as `planned
for 0.0.13`". **All eleven `## Current state` observation clauses stay verbatim**, per
`docs/builder/BUILD.md` `### '## Current state': observations stand, predictions do not` —
including CS-6b, which dates itself in-clause.

#### P. Remaining audit-3 rows (E4, E8, D5) and the G2 tier split (deferral 7)

| # | Spec heading | Change |
|---|---|---|
| P1 | `## Edge cases` → `read_only` / `HiddenField` | Adds the shadow guard's coverage of a `HiddenField`'s validated-data key (E4). |
| P2 | `## Edge cases` → relation visibility | Adds the second gate: runtime relation querysets composed as author ∩ visibility before `is_valid()` (E8). |
| P3 | `## Definition of done` item 5, `## Test plan` preamble | The live tier is the aggregate `/graphql/` schema across every `test_query/` module, not `test_products_api.py` alone (D5; audit 4 Notes 13). |
| P4 | `## Slice checklist` Slice 3 live bullet, `## Test plan` live bullet, DoD items 4 and 5 | The G2 tier split, both tests cited by `path::QualifiedName`, in agreement with `tests/rest_framework/test_resolvers.py`'s module docstring (deferral 7). |
| P5 | `### Decision 8` error-keying paragraph | Re-keying happens at **every** depth via `_rekey_segment` over the recursive child maps, not only the root segment. |

#### Q. Deferral 8 — no change owed

`## Edge cases` row 7 / `## Test plan`: the tolerance arm of the H3 request-actor guard is
now pinned by Slice 3. Re-read this pass and confirmed the spec text already states the
contract correctly. **No edit made**; recorded so the integration pass does not re-raise it.

### Rationale companion changes (Worker 1 only)

Append-only, per `docs/builder/BUILD.md` `## Spec rationale extraction` rule 4. Every entry
names the Decision it belongs to and lands under that Decision's existing
`### Changes this Decision underwent`.

- **`**Post-ship:**` entries under Decisions 1, 2, 4, 5, 6, 7, 8, 10, 12, 14** — what
  changed, why, and what it replaced, for every corresponding spec rewrite. Decision 8's
  is the longest: it records the fold bullet by bullet, the authorization bypass the
  hardening closed, and three design choices with the plausible weaker alternative each
  rejected (identity-not-deep-equality; no read/write classification; fail-closed on an
  opaque leaf).
- **Checked-and-unchanged entries under Decisions 3, 9, 11, 13** — the file's own rule
  ("a Decision a reconciliation checked and found still true earns a bullet too — a
  measured no-change and an unexamined one read identically otherwise").
- **`### Post-ship changes to individual `rev6` items`** — #14, #12, #2, #1, #3, #17.
- **`### Post-ship findings that belong to no single Decision`** — the "byte-identical"
  opener; why `## Current state` survives verbatim; the import-manifest granularity choice
  with its two rejected alternatives; why identity beats a grep and why the ratchet's
  ceiling is stated rather than closed; the four dead-symbol P-table cells; and the status
  of the three obligations Slice 0 logged for this slice.
- One link definition added (`mutations-inputs`).

### Notes for Worker 1 (spec reconciliation)

Deliberately left, each with a named owner.

**For Slice 2b (`.py`, in fence, comment-only):**

1. `django_strawberry_framework/rest_framework/inputs.py` #"The row is a static STRING
   pair, so" — asserts the superseded `register_subsystem_clear` row shape, immediately
   above a line that calls the new form. Exactly one occurrence. (audit 1a Notes 9)
2. `django_strawberry_framework/rest_framework/__init__.py` #"(place 2 of the
   three-places-that-must-agree: place 1 is the" — its "place 3 is the spec **Risks**
   note" is now wrong twice: place 3 is Decision 12, and Slice 0 moved
   `## Risks and open questions` into the companion. The floor value itself is correct in
   all three real places. (audit 4 Low-2)
3. The 21 label-carrying `spec-039` comment lines across 8 `.py` files, and the three
   headings whose GitHub anchor slugs the label strip changes. Unchanged by this pass; the
   spec's label token set is intact at 37 distinct tokens, measured above.

**For the cross-slice integration pass:**

4. Two duplications in `django_strawberry_framework/rest_framework/inputs.py` — the
   nested-serializer message tail, and the twice-derived provisional input-type name.
   (audit 1a `### DRY findings`)
5. The `f"SerializerMutation {…}: "` message-prefix duplication (~30 error strings) in
   `rest_framework/resolvers.py`. Audit 3 routes it to its own card rather than into this
   cycle; the integration pass is where that card is confirmed to exist.
6. `tests/rest_framework/test_dry_import_ratchet.py:3-8`'s ragged docstring wrap, carried
   from Slice 3 to `bld-039-final.md`'s `### Deferred work catalog`.

**For the maintainer — contract-level, not custodial:**

7. **Escalation A (carried, still open).** Whether the DRY import ratchet should hold the
   spec's **named promotions** or the **whole measured shared substrate**, and — the axis
   pass 2 of Slice 3 added — whether it should cover the forms flavor too, since
   `forms/converter.py` binds the same `FieldConversionBase` and no ratchet covers it. The
   spec now states the shipped population explicitly, so it is auditable either way; a
   widening would be a spec edit plus a manifest edit, not a rewrite.
8. **Escalation B (carried).** The `isinstance` tightening on the tolerated `_mutation_meta`
   shape is a seam-support question. The spec now states the snapshot requirement as a
   contract, which is what makes the question answerable rather than implicit.
9. **Escalation C (carried).** `HEAD` is red from `spec-050` at `4c483b6b` in four modules
   this cycle does not touch. `bld-039-final.md` cannot record a green full sweep until
   that is resolved.
10. **The DRY existence challenge on `mutations/sets.py::cached_build_input`** (audit 1b
    Notes 8) — a promoted helper with one real caller, since `spec-039` rules the serializer
    out of it. Audit 1b recommends keeping it; no spec row is held on the answer, and this
    pass made no change either way.

**Judged in-scope and decided rather than escalated**, recorded so the integration pass can
see the reasoning: the import-manifest granularity choice (L above) and the
public-surface-enumeration choice (C1). Both were framed as escalations by their audits;
both turn on how to state an **existing** contract accurately rather than on which contract
the package should offer, which `docs/builder/BUILD.md`
`### Contract-level findings are escalated as maintainer decisions before dispatch` puts on
the custodian's side of the line.

### Summary

The spec now describes the tree. The 179-line hardening blockquote and the bracketed
superseded clause are gone and every one of their contracts has a home in the Decision that
owns it, stated in the present tense with no chronology; eleven shipped mechanisms and two
whole modules that the spec named nowhere have one; and the five-homes cross-check found
and closed three separate three-home splits (the hook contract, the clear-seam row shape,
the public-surface count). Fifty-three graded rows and eight deferrals are discharged, none
deferred. All three gates pass with the citation and glossary counts unchanged, and Slice
2b's label population is intact at 37 distinct tokens.

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
