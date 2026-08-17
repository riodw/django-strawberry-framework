# Build: Round R1 — rationale extraction and spec reconciliation (spec-017)

Spec reference: `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`
Rationale companion: `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` (created by this round)
Build plan: `docs/builder/build-017-deferred_scalars-0_0_6.md`
Shape: **procedural-closure** (`docs/builder/BUILD.md` `### Procedural-closure slices`) — one combined Plan + Final-verification block. No Worker 2 build and no Worker 3 review runs on this round: the whole round is spec-custodian work, which only Worker 1 is authorized to perform.
Status: final-accepted

`HEAD` at the time of this pass: `acaa6b833d836aa02487eb14a57eb1c98e93354e`.

## Plan (Worker 1) + Final verification (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in its usual form: this round writes Markdown only and proposes no helper, shared constant, validation branch, coercion utility, or test helper. The package-wide AST inventory would have nothing to prevent. The read-only source reading this round *did* perform is recorded under `### The audit` below.
- **Existing patterns reused.** The rationale companion follows `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md`'s section shape (provenance block, "what the card actually did", entries keyed to the spec by heading, reconciliation record, "what this cycle deliberately did not fix") rather than inventing one. `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md` was read as the second precedent; it is a *reconstruction* and so was not the structural model.
- **New helpers justified.** None.
- **Duplication risk avoided.** One real risk, and it is documentary: the reconciled spec must not restate what the rationale file now owns, or a reader gets two accounts of the same decision and cannot tell which is current. Prevented by the cut-not-copy rule — every passage listed under `### Spec changes made (Worker 1 only)` as *moved* exists in exactly one file. A second risk, in the audit's output: naming the four deleted `_resolve_*_field` tests as "gone" without naming their owner would invite a future reader to restore the duplication. Prevented by pointing Slices 3 and 4 at `tests/utils/test_imports.py` **as the owner**, not merely deleting the boxes.

### Boundary count

Zero. This round adds no guard, cap, rejection path, or validation branch. No split question arises.

### Hot-path declaration

**None.** This round writes Markdown only. (Build plan's declaration, unchanged.)

### Floor-verification scope

**None.** This round touches no Django / Strawberry / channels integration seam. The floor, quoted from `docs/builder/BUILD.md` `## Floor verification` rather than from memory, is **Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0**. No pass in this round needed the shared `.venv`'s own versions, so none were read or restated.

### Failability proofs

None; this round introduced no new boundary.

### Dispatched findings checklist

Worker 0's eight pre-dispatch findings, each **re-derived at this working tree** rather than accepted. Ticked when re-derived; the disposition is recorded, not the agreement.

- [x] **F1 — the deprecation suppression is gone.** Re-derived. `django_strawberry_framework/scalars.py #"BigInt = NewType(\"BigInt\", int)"` followed by `scalars.py #"_BIGINT_SCALAR_DEFINITION: ScalarDefinition = strawberry.scalar("` (the `name=`-only overload, no `cls` argument) and `scalars.py #"_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]"`, exposed through `django_strawberry_framework/scalars.py::strawberry_config`. There is no `catch_warnings` and no `import warnings` anywhere in the file. Confirmed as the migration `DONE-025-0.0.7` shipped: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` Decision 6 is titled "Remove the `warnings.catch_warnings()` suppression block". **Disposition (b).**
- [x] **F2 — `_resolve_array_field()` / `_resolve_hstore_field()` do not exist.** Re-derived, and the attribution corrected — see `### Corrections to the pre-dispatch findings`. `django_strawberry_framework/types/converters.py #"_ARRAY_FIELD_CLS: type[models.Field] | None = import_attr_if_importable"`. Both branches the four deleted tests covered are covered at the shared helper; see the dedicated verification below. **Disposition (b).**
- [x] **F3 — the nine schema-execution tests were promoted, not dropped.** Re-derived **per test**; the full mapping is below and in the rationale companion. **Disposition (b) for all nine, no (c).**
- [x] **F4 — the error-message construction changed.** Re-derived. `converters.py::_field_label` and `converters.py::_field_has_choices` exist and are what `convert_scalar`'s `ArrayField` / `HStoreField` branches call; no `field.model.__name__` interpolation and no bare `if field.choices:` survives in those branches. **Disposition (b).**
- [x] **F5 — `convert_scalar` gained `force_nullable`.** Re-derived; the *source* card was mis-attributed and is corrected below. `converters.py::convert_scalar #"force_nullable: bool | None = None"`, `#"effective_null = field.null if force_nullable is None else force_nullable"`, and the recursion at `#"inner = convert_scalar(field.base_field, type_name)"` deliberately passes no `force_nullable`. **Disposition (b).**
- [x] **F6 — Slice 5 / Slice 6's version work is superseded.** Re-derived: `pyproject.toml #"version = \"0.0.14\""` and `django_strawberry_framework/__init__.py #"__version__ = \"0.0.14\""` both read `0.0.14`; `tests/base/test_init.py #"assert __version__ =="` pins `"0.0.14"`. The quintet's *sites* are still correct; the literal `0.0.5` -> `0.0.6` targets are historical. **Disposition (b).**
- [x] **F7 — the follow-up card is named three ways.** Re-derived: `WIP-ALPHA-020-0.0.7`, `TODO-ALPHA-045`, and `DONE-025-0.0.7` all appeared in the pre-edit spec. `DONE-025-0.0.7` is the card that shipped (`KANBAN.md`'s live card; `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`'s own `Predecessors:` line). The Slice 6 `DONE-017-0.0.6` -> `DONE-017-0.0.6` self-contradiction was present as described. **Disposition (b); both reconciled.**
- [x] **F8 — the archive already happened.** Re-derived: the spec is at `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` and its terms CSV at `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-terms.csv` (16 rows, one per anchor). **No move was performed by this round.** **Disposition (b).**

### The audit — every spec item's disposition

Walked: `## Slice checklist` (Slices 1-6, every nested sub-check), `## Goals` (8 bullets), `## User-facing API` (10 table rows), `## Test plan` (categories 1-19), `## Definition of done` (13 items). Every item resolved to (a) or (b). **No (c) was found: nothing the spec planned was skipped in the code, and no defect was found in what shipped.** No contingent R2 round is owed.

**(a) Shipped and present at `HEAD` — the substantive contract.**

| Spec item | Citation |
|---|---|
| `scalars.py` with `_parse_bigint` / `_serialize_bigint` and the pinned regex | `django_strawberry_framework/scalars.py #"_BIGINT_STRING_PATTERN = re.compile(r\"^(0\|-?[1-9][0-9]*)$\")"`, `scalars.py::_parse_bigint`, `scalars.py::_serialize_bigint` |
| `BigInt` re-exported; `__all__` tuple pinned | `django_strawberry_framework/__init__.py #"from .scalars import BigInt, Upload, strawberry_config"`; `tests/base/test_init.py #"\"BigInt\","` |
| `BigIntegerField: BigInt` | `converters.py #"models.BigIntegerField: BigInt,"` |
| `PositiveBigIntegerField: BigInt` (the changed mapping) | `converters.py #"models.PositiveBigIntegerField: BigInt,"` |
| `SCALAR_MAP` value type widened to `Any` (Decision 8) | `converters.py #"SCALAR_MAP: dict[type[models.Field], Any] = {"` |
| `BigAutoField` preserved as `int` | `converters.py #"models.BigAutoField: int,"` |
| `JSONField -> strawberry.scalars.JSON` | `converters.py #"models.JSONField: strawberry.scalars.JSON,"` |
| `ArrayField` branch: nested rejection, outer-`choices` rejection, `base_field` recursion, `list[inner]` | `converters.py::convert_scalar #"Nested ArrayField on"`, `#"declares choices on the outer "`, `#"inner = convert_scalar(field.base_field, type_name)"` |
| `HStoreField` branch: outer-`choices` rejection, returns `JSON`; NOT in `SCALAR_MAP` | `converters.py::convert_scalar #"HStore stores a dict[str, str \| None] with no enum-able shape"`; `HStoreField` absent from the `SCALAR_MAP` literal |
| Both sentinel branches run before the `SCALAR_MAP` MRO walk | `converters.py::convert_scalar` — both `isinstance` guards precede `#"py_type = scalar_for_field(field)"` |
| All TODO comments for deferred scalars removed | `grep -n "TODO" django_strawberry_framework/types/converters.py` returns nothing |
| No staged anchors survive | `grep -rn "TODO(spec-017"` returns only this cycle's own build plan; `TODO-(ALPHA\|BETA\|STABLE)-017` returns nothing outside `KANBAN.md` |
| 31 of 31 `tests/test_scalars.py` names; 15 of 15 sentinel-branch names; both optional gated postgres tests | each confirmed by `grep -rn "def <name>"` returning exactly one hit |
| Slice 6 doc surfaces | `docs/TREE.md #"scalars.py"` (both layouts); `docs/GLOSSARY.md #"BigInt` scalar"` at `shipped (0.0.6)`; `TODAY.md #"PositiveBigIntegerField` switched from `int`"`; `CHANGELOG.md #"## [0.0.6] - 2026-05-19"`; `README.md #", single-maintainer, alpha-quality."`; `docs/README.md #"**Shipped today**"`; `KANBAN.md`'s `DONE-017-0.0.6` card |

**(b) Shipped, then deliberately superseded by later work.**

| Spec item | Superseded by | Where the replacement lives |
|---|---|---|
| Decision 1's `warnings.catch_warnings()`-wrapped `BigInt`; Decision 6's import-time warning posture; the Goals bullet; the API-table footnote; the Risks bullet; the `CHANGELOG` `Notes` entry | `DONE-025-0.0.7` (`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` Decisions 3 and 6) | `django_strawberry_framework/scalars.py #"BigInt = NewType(\"BigInt\", int)"` + `::strawberry_config` |
| Decision 4's `_resolve_array_field()` / `_resolve_hstore_field()`; Slices 3/4's four helper-resolver test boxes; Test-plan category 12 | commit `17995323` (2026-07-08) | `django_strawberry_framework/utils/imports.py::import_attr_if_importable`; branch coverage at `tests/utils/test_imports.py` |
| Decisions 2 and 5's `field.model.__name__}.{field.name` interpolation and bare `field.choices` test | commit `62ae8404` (2026-08-16) | `converters.py::_field_label`, `converters.py::_field_has_choices` |
| Decision 2's `return result \| None if field.null else result` | `DONE-029-0.0.9` (`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` Decision 7) | `converters.py::convert_scalar #"effective_null = field.null if force_nullable is None else force_nullable"` |
| Slice 1/2's nine schema-execution test boxes | the live-first migration | `examples/fakeshop/test_query/test_scalars_api.py` (per-test table below) |
| Slice 5/6's `0.0.5` -> `0.0.6` literals | the `0.0.7`-through-`0.0.14` cuts | `pyproject.toml`, `__init__.py`, `tests/base/test_init.py` all at `0.0.14` |
| Slice 6's archive step and the matching DoD item | already performed at an earlier archive pass | `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`, `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-terms.csv` |
| Risks' "`BigAutoField` … no current-day recourse" | `DONE-019-0.0.6`, the sibling card in the same release | `docs/GLOSSARY.md#scalar-field-override-semantics`, `shipped (0.0.6)` |

**(c) Never shipped.** **None.**

### F3 verified per test, not in aggregate

Establishing the population first: all 75 `test_*` tokens in the pre-edit spec were extracted and each grepped as `def <name>` across `tests/` and `examples/`. Sixty are file/app-label fragments or exist under their own name. Fourteen are genuinely absent: the nine below, the four `_resolve_*_field` tests (F2), and `test_bigint_scalar_definition_emits_strawberry_deprecation_warning` — the last of which the spec itself records as replaced during authoring, never shipped under that name, and therefore not a gap.

Every one of the nine has a live-tier equivalent pinning the same contract. Not one is a (c).

| Absent spec-named test | Contract | Live-tier test that pins it |
|---|---|---|
| `test_big_integer_field_maps_to_bigint_in_schema` | annotation shape via introspection | `test_scalars_api.py::test_scalar_specimen_introspects_bigint_scalar_for_both_fields` — asserts `signedBig` is `NON_NULL` over `{"name": "BigInt", "kind": "SCALAR"}` |
| `test_big_integer_field_nullable_in_schema` | nullable widening | same test — `NullableScalarSpecimenType.signedBig` asserts bare `{"name": "BigInt", "kind": "SCALAR", "ofType": None}` |
| `test_positive_big_integer_field_maps_to_bigint_in_schema` | the changed mapping | same test — `unsignedBig` (`PositiveBigIntegerField`) in both shapes |
| `test_bigint_serializes_query_result_as_string_via_schema_execution` | wire round-trip | `::test_scalar_specimen_every_field_wire_format_over_http` — `row["signedBig"] == "9223372036854775000"`, a value past `2**53 - 1` chosen so only decimal-string serialization survives JSON |
| `test_bigint_parses_string_argument_via_schema_execution` | string-form argument parsing | `::test_scalar_specimen_bigint_input_decimal_string_argument_over_http` |
| `test_bigint_parses_int_argument_via_schema_execution` | int-form argument parsing | `::test_scalar_specimen_bigint_input_int_literal_argument_over_http` |
| `test_json_field_maps_to_json_scalar_in_schema` | annotation shape via introspection | `::test_scalar_specimen_introspects_json_scalar_in_both_shapes` — `payload` is `NON_NULL` over `{"name": "JSON", "kind": "SCALAR"}` |
| `test_json_field_nullable_in_schema` | nullable widening | same test — `NullableScalarSpecimenType.payload` asserts bare `SCALAR` |
| `test_json_field_round_trips_dict_via_schema_execution` | JSON dict round-trip | `::test_scalar_specimen_every_field_wire_format_over_http` — `row["payload"] == _JSON_PAYLOAD`, a mixed-primitive dict (string, int, list, JSON `null`, nested bool) |

Corroboration independent of my mapping: three of the live tests name the migration in their own docstrings ("Migrated from these tests in `tests/types/test_converters.py`: …"), and `test_scalars_api.py #"_JSON_PAYLOAD = {"`'s preceding comment names `test_json_field_round_trips_dict_via_schema_execution` explicitly. The owner columns exist as claimed: `examples/fakeshop/apps/scalars/models.py #"signed_big = models.BigIntegerField(default=0)"`, `#"unsigned_big = models.PositiveBigIntegerField(default=0)"`, `#"payload = models.JSONField(default=dict)"`, and their `null=True` twins on `NullableScalarSpecimen`.

### F2 verified: both branches, not one

The deleted `_resolve_*_field` tests covered an importable branch and an unimportable branch. Both are covered at the shared helper, and a third branch the hand-rolled helpers never had is covered too:

- importable — `tests/utils/test_imports.py::test_import_attr_if_importable_returns_the_attribute_on_an_importable_module`
- unimportable — `::test_import_attr_if_importable_returns_none_when_the_module_is_unimportable`, forced with `monkeypatch.setitem(sys.modules, "dsf_absent_optional_module", None)`, the same `sys.modules`-sentinel technique the spec's own deleted tests used
- importable-but-missing-attribute — `::test_import_attr_if_importable_raises_when_importable_module_lacks_the_attr` (`AttributeError`), a branch the spec's helpers did not have

`git show 17995323` proves the deletion and the expansion landed in the **same commit**, so the coverage moved rather than lapsing. Branch coverage went up, not down.

### Corrections to the pre-dispatch findings

Both were re-derived and both changed the attribution, not the conclusion. Recorded because the rationale companion cites them and a later pass must not re-derive them from the build plan.

1. **`force_nullable` came from `DONE-029-0.0.9`, not `DONE-019-0.0.6`.** The build plan's Finding 5 attributes it to `DONE-019-0.0.6`. `grep -rln "force_nullable" docs/SPECS/*.md` returns `spec-029-consumer_dx_cleanup-0_0_9.md` and `spec-037-upload_file_image_mapping-0_0_11.md` — **not** `spec-019`. `spec-029`'s Decision 7 is titled "tri-state `force_nullable` threaded through `convert_scalar`" and its Slice 1 spells the `effective_null` formula verbatim. `spec-019`'s contract is the *annotation* override, which bypasses `convert_scalar` entirely (its own Decision 7a calls the bypass out). The two are different mechanisms from different cards. The rationale companion credits `DONE-029-0.0.9`.
2. **The `import_attr_if_importable` consolidation landed 2026-07-08 in commit `17995323`, before `0.0.14`.** The build plan credits `DONE-041-0.0.14`. `spec-041` *documents* `utils/imports.py` as the single optional-import owner, which is why the attribution is understandable, but `git log -S"import_attr_if_importable" -- django_strawberry_framework/types/converters.py` shows the converter's migration in `17995323`, whose message names the removal of the `_resolve_*_field` tests. The rationale companion cites the commit, which is re-derivable, rather than a card number I could not prove.

### Focused test runs

No `--cov*` flag was passed in any invocation. Recorded per `## Final verification job` step 5 — whether they run, not a coverage claim.

- `uv run pytest tests/test_scalars.py tests/utils/test_imports.py tests/base/test_init.py --no-cov -q` — **67 passed**.
- `uv run pytest examples/fakeshop/test_query/test_scalars_api.py tests/types/test_converters.py --no-cov -q` — **105 passed**.

### Verification of the move itself

Per `docs/builder/worker-1.md` `### Performing the rationale move` rule 3 — verified, not assumed:

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-017-deferred_scalars-0_0_6.md` -> exit 0, `OK: 16 terms - all have glossary entries and at least one spec link.` Two terms (`strawberry_config`, `Upload`) lost their only body carrier to the move and were re-homed in reconciled prose before the check was re-run.
- Every in-page `](#anchor)` in the reconciled spec resolves to a heading, checked mechanically with code-fences stripped. The one apparent miss, `#specialized-scalar-conversions`, sits inside the verbatim `docs/GLOSSARY.md` entry-text drop-in and is meant to resolve in `GLOSSARY.md`; it was already so before this pass.
- No surviving cross-reference points into moved text without naming the rationale file: the header carries the pointer, and every Decision whose deliberation moved reads as a self-contained current contract.
- `uv run python scripts/check_trailing_commas.py --check` -> exit 0 on both files (link-def scaffold intact; all ten canonical group headers present in the new file).
- Every reference-style link definition in the new file was resolved against the filesystem: 11 of 11 exist.
- **Byte counts, measured with `wc -c`, never estimated, and re-measured at the close of the MF-3 correction pass rather than carried forward.** Spec: **84,488 -> 62,804**. Rationale companion: **0 (did not exist) -> 44,338**. The companion's own table states the same two pairs; its self-referential figure was iterated to a joint fixed point rather than guessed. The R1 pass recorded 62,677 / 41,323 — both taken mid-pass, and both superseded here. The final gate's independent re-measure of the companion at 41,325 is consistent with that: the file grew after R1 read it.

### Spec changes made (Worker 1 only)

All changes are to `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`, all triggered by round R1. Passages marked **MOVED** were cut into the rationale companion; **DELETED** means the current contract falsifies them and git preserves the history (`worker-1.md` rule 2); the rest are reconciliations.

| Spec passage | Change | Reason |
|---|---|---|
| `Status:` line | DELETED + reconciled | Read `draft (revision 10, post-feedback2 re-review)` on a shipped card; now `shipped in 0.0.6`, plus a pointer to the rationale file |
| `Revision history` block, revisions 1-10 | MOVED (39 lines) | A spec must never narrate its own history (`BUILD.md` `## Spec rationale extraction`) |
| `## Current state` | MOVED | Described the `0.0.5` baseline; every sentence now false |
| `## Key glossary references`, the override-semantics bullet | Reconciled | `planned for 0.0.6 (WIP-ALPHA-015)` -> the sibling card `DONE-019-0.0.6`, which shipped |
| Slice 1's `catch_warnings()` instruction | DELETED + reconciled | The suppression does not exist; the *goal* (a warning-free import) is restated |
| Slice 1's "Deprecation suppression (B1 coverage)" heading and its bullet | Reconciled | Retitled "Warning-free import"; the test's purpose restated against the shipped mechanism |
| Slice 1 (six boxes) and Slice 2 (three boxes) | Reconciled | Repointed at the live-tier tests that pin the same contracts, path-qualified; surviving package-tier boxes path-qualified so the two tiers are distinguishable |
| Slices 3 and 4's `_resolve_*_field()` instructions | Reconciled | Replaced by the shared soft-import owner |
| Slices 3 and 4's four helper-resolver test boxes | DELETED + reconciled | Replaced by a pointer naming `tests/utils/test_imports.py` as the owner, so the duplication is not "restored" later |
| Slice 5 preamble | MOVED (partly) | The "controlled inconsistency" narration moved; the version sites and the publish gate stayed |
| Slice 6 (whole) | MOVED + reconciled | Two verbatim KANBAN bodies, the NNN-renumber parenthetical, and the archive-time stripping step moved; the `DONE-017-0.0.6` -> `DONE-017-0.0.6` self-contradiction DELETED; the generated-doc procedure stated for `GLOSSARY.md`/`KANBAN.md`; the follow-up named `DONE-025-0.0.7`; version literals de-pinned; the archive step extended to name the `appx/` companions |
| `## Problem statement` constraint 4 | Reconciled | From "the deprecation is suppressed" to "the package must define `BigInt` on the non-deprecated path" |
| `## Goals`, the `BigInt` bullet | Reconciled | Suppression replaced by the non-deprecated registration path |
| `## Non-goals`, the `scalar_map` bullet | Reconciled | `No StrawberryConfig.scalar_map integration` is false; restated as the scope boundary that actually holds, pointing at `spec-025` |
| Decision 1's `catch_warnings()` block and its 11-line comment | DELETED + reconciled | Replaced with the shipped `NewType` + `ScalarDefinition` + `_PACKAGE_SCALAR_MAP` shape and a comment explaining why the bare `NewType` is required |
| Decision 1's three "Why the …" paragraphs | MOVED (2) + kept-reshaped (2) | The rejected alternatives (`parse_value=int`, `serialize=str`) and the whole suppression argument moved; the *implementation-relevant* halves — check `bool` before `int`; the serializer must be as strict as the parser — stayed, per `worker-1.md`'s carve-out |
| Decision 2 pseudocode | Reconciled | `_field_label(field)`, `_field_has_choices(field)`, `effective_null`; a new paragraph states why the guarded readers exist and a second states the `force_nullable` tri-state and the deliberately-unset recursion |
| Decision 4 (heading and body) | DELETED + reconciled | Both function bodies deleted; retitled "Soft import via module-level sentinels"; the shared helper's fail-loud contract stated; the anchor updated at both referencing sites |
| Decision 5 pseudocode and its four-bullet "Why reject" list | MOVED + reconciled | Pseudocode reconciled like Decision 2's; three of four bullets moved, the one carrying non-derivable information (Django's `choices` on HStore is form-only) kept as one sentence |
| Decision 6 (whole) | MOVED + reconciled | Retitled "…public-export status and registration contract"; the two-state migration contract and the whole "Recommended starting point" paragraph moved; replaced with the single shipped contract, a consumer example, and the `Unexpected type '...BigInt'` consequence promoted from a probe result to a normative sentence |
| Decision 7's helper-resolver test block | MOVED + reconciled | Replaced with a statement that this module owns no soft-import branch and must not grow a second copy of that coverage |
| Decision 7's deprecation-test paragraph | Reconciled | The `importlib.reload` trap explanation kept (it is why the test can fail at all) and rewritten so it no longer presumes a suppression block |
| `## User-facing API` closing note | Reconciled | Suppression footnote replaced by the `config=strawberry_config()` requirement |
| `## Implementation plan` Slice 1 file list | Reconciled | Dropped "`warnings.catch_warnings()`-wrapped"; added the live-tier test file |
| `## Edge cases`, the `BigAutoField` bullet | Reconciled | "No current-day recourse" is false since `DONE-019-0.0.6` |
| `## Edge cases`, the `from_db_value` bullet | Reconciled | Same card-name correction |
| `## Test plan` preamble and categories 12, 17 | Reconciled | Two-file preamble expanded to three with the live tier named and the postgres-only carve-out explained; category 12 repointed at the shared helper; category 17 retitled |
| `## Risks and open questions` (whole section) | MOVED (13 bullets) | Every risk is settled or superseded; the section's one live claim (`BigAutoField` recourse) was false |
| `## Out of scope` | Reconciled | The `scalar_map` line restated as the factory's own surface, owned by `spec-025`; a line added for future package scalars, carrying the `Upload` glossary term whose only carrier the move removed |
| `## Doc updates` | Reconciled | No longer claims the KANBAN body is drafted inline; states why it must not be |
| `## Definition of done` | Reconciled | Archive item extended to name the companions; the suppression item retitled |
| Link scaffold | Reconciled | Added `[spec-017-rationale]` and `[spec-025]` under `<!-- docs/SPECS/ -->` |

#### Correction pass — MF-3, found by the final test-run gate, not by R1

The final gate closed `final-accepted` on the cycle but surfaced one defect in this round's own output. The round is **not reopened**; this is a custodian correction landing against it, and `Status:` stands at `final-accepted`.

| Spec passage | Change | Reason |
|---|---|---|
| Decision 1, "Target Django fields", the `BigAutoField` bullet | Reconciled | Read `No current-day consumer recourse for the 2**31 boundary — wait for [Scalar field override semantics]`. **False on the day `0.0.6` shipped**: the sibling card `DONE-019-0.0.6` landed consumer annotation overrides in the same release. Rewritten to state the current contract directly, in the vocabulary `## Non-goals` and `## Edge cases and constraints` already use, so all three read as one contract. The mapping is unchanged and was never wrong — `BigAutoField` stays `int` for PK wire-format stability. **Found by the final test-run gate as MF-3, not by R1.** |
| `## Key glossary references`, the override-semantics bullet | Reconciled | Read "The `BigAutoField` deferral depends on that contract." A deferral already discharged is a recourse, not a dependency; reworded to say the card *supplies* the recourse for the mapping this card leaves at `int`. Found in the same pass. |

**Why R1 missed it, and the method that closed it.** R1 fixed the three sites it had read and never established the population. Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, the population is established by searching the **shortest distinctive token** and counting **occurrences, not matching lines**. Two independent tokens now agree and every occurrence has been read:

| Site | Text | Disposition |
|---|---|---|
| `## Key glossary references` | "the `BigAutoField` deferral depends on that contract" | **Corrected this pass** — reworded to a discharged recourse |
| Slice 6, the verbatim `docs/GLOSSARY.md` entry-text drop-in | "(not `BigAutoField`)" | **Unchanged, true.** A scope statement about which fields `BigInt` maps, carrying no recourse claim. Verified character-identical to the shipped `docs/GLOSSARY.md #"(not `BigAutoField`)"`; a drop-in whose whole purpose is matching the rendered entry must not be paraphrased |
| `## Non-goals` | "the consumer recourse … is the annotation override shipped by the sibling card `DONE-019-0.0.6`" | **Unchanged, already corrected by R1** |
| Decision 1, "Target Django fields" | was "No current-day consumer recourse … wait for" | **Corrected this pass (MF-3)** |
| `## User-facing API` table row | "`int` (unchanged) — Preserved for PK wire-format stability" | **Unchanged, true.** States the mapping only; no recourse claim |
| `## Edge cases and constraints` | "A PK past the `2**31` boundary is handled by the consumer annotation override (`DONE-019-0.0.6`), not by this card" | **Unchanged, already corrected by R1** |
| `## Out of scope (explicitly tracked elsewhere)` | "`BigAutoField` → `BigInt`." | **Unchanged, true at `HEAD`** — `converters.py #"models.BigAutoField: int,"`, so the mapping change is still out of scope. Read, not assumed. One observation recorded rather than acted on: this is the only bullet in a section headed "explicitly tracked elsewhere" that names no tracking card. Left alone rather than inventing a pointer I cannot prove exists — noting it for the deferred-work catalog |

- **`BigAutoField` — 7 occurrences in the spec, on 7 distinct lines.** This is the population-defining token, and all seven are dispositioned in the table above.
- **`no current-day` — 0 occurrences. `wait for` — 0 occurrences.** These are the distinctive phrases of the false clause itself, and both reaching zero is the proof it is fully retired rather than merely reworded at the sites I read.
- **`recourse` is a poor corroborating token and is recorded here as such**, because measuring it exposed a second instance of the same error. Post-correction it stands at 4 occurrences, and the sites are NOT the ones a first draft of this table asserted: `## Key glossary references` `#"Meta.exclude"` uses it for `Meta.exclude`'s *unrelated* unsupported-field recourse, and `## Edge cases and constraints` does not contain the word at all (it says "is handled by"). A token shared with a different claim samples vocabulary rather than establishing a population — the exact failure `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` names. The two zero-count phrases above are the sound corroboration; `recourse` is not.
- A fourth carrier of the claim existed and is gone: the `## Risks and open questions` bullet, closed by R1 when the whole section was cut.

**Rationale-companion corrections in the same pass.** MF-3 falsified two of the companion's own sentences, and both are now true:

- The `**Deleted outright rather than moved**` paragraph claimed "none is restored anywhere as live text" while the claim survived as live spec text in Decision 1. Rewritten to say no carrier survives as live spec text, and that the state was reached in **two** passes, pointing at the new Decision 1 sub-entry.
- The `## Risks and open questions` entry said "the spec's Risks bullet was not [updated], which is why it is deleted rather than moved", naming one site of the four the claim actually occupied. Rewritten to name all four.
- A new sub-entry keyed to **Decision 1** by heading records the false clause verbatim, the four-site population, the pass that closed each, and the occurrence-counting method — so a future reader can look the claim up by the decision it belongs to, per `docs/builder/BUILD.md` `## Spec rationale extraction`.

### Notes for Worker 1 (spec reconciliation)

**For R3 — standing-doc staleness found and deliberately not fixed here.** These are documentation surfaces, R3's scope per the build plan; three of the five are generated from `examples/fakeshop/db.sqlite3` and are not hand-editable.

- **`KANBAN.md`, the `DONE-017-0.0.6` card body — two false sentences.** Its `#### Note` block still reads "Public `BigInt` scalar (…, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` **suppressed at the definition site** so consumers see no warning at import time", and a second bullet repeats "suppressed at the definition site (tight `warnings.catch_warnings()` filter)". The same sentence is also the body of a `Card references` row linking to `DONE-025-0.0.7`. All false since `DONE-025-0.0.7`. DB-backed: edit the kanban tables, then regenerate. Note the same card body was *already* corrected once on a different point (`BigAutoField` "no override recourse at the time; annotation-override recourse now available via `DONE-019-0.0.6`"), so this card has a precedent for exactly this kind of amendment.
- **`KANBAN.md`, the same card's `#### Test plan` block** repeats "Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions **to the suppression** are explicit". The test survives; what it guards is no longer a suppression.
- **`docs/GLOSSARY.md`** — check the `Public exports` and `BigInt scalar` entries for suppression wording carried over from Slice 6's drop-in text. DB-backed.
- **`CHANGELOG.md`** — the `[0.0.6]` `Notes` line was removed by `DONE-025-0.0.7` Slice 5 as planned, so this one appears clean; confirm rather than assume.
- **`docs/README.md` / `TODAY.md`** — both read current on the scalar surface at a spot check; R3 owns the full sweep.

**Deferred-work catalog input for the final gate.** `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` refers to spec-017 through the ref-id `[spec-013]` in five places — a pre-renumber artifact whose *definition* resolves correctly, so the links work and only the label is wrong. `KANBAN.md` line 349 already records the whole multi-surface cluster as carded onto `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0`. **Unchanged by this round**, per the maintainer's instruction and `worker-0.md`'s rule against correcting one surface of a multi-surface wrong reference: a partial fix would leave the cluster divergently rather than uniformly wrong.

**No R2 round is owed.** The audit found no (c) and no defect. If Worker 0 opens one anyway, the files it would have to touch are none — there is no code finding to act on.

**Concurrent work.** The tree carried a concurrent session's spec-016 residual cycle and review cycle throughout this pass. Nothing on the build plan's `## Baseline-dirty out-of-scope files` list was edited or reverted. `examples/fakeshop/db.sqlite3` was neither written nor read for a regenerate.

### Summary

Created the missing rationale companion by **moving** spec-017's deliberative layer into it (spec 84,488 -> 62,804 bytes; companion 0 -> 44,338, both re-measured at the close of the MF-3 correction), audited every spec item against `HEAD` and found **no gap and no defect** — all dispositions (a) or (b), no (c) — and reconciled the spec so a reader with no knowledge of this cycle reads the contract that actually holds: the bare-`NewType` + `strawberry_config()` registration path, the shared soft-import owner, the guarded `_field_label` / `_field_has_choices` diagnostics, the `force_nullable` tri-state, and an archive that is already done. Worker 0's eight pre-dispatch findings were all re-derived; two carried mis-attributed source cards, corrected above. The nine "promoted" tests were verified per test, and the four subsumed helper-resolver tests were verified as a two-branch-plus-one gain, not a loss.

Final status: **`final-accepted`**.
