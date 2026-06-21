# Review: `django_strawberry_framework/mutations/inputs.py`

Status: verified

## DRY analysis

- **Defer-with-trigger — `mutations/fields.py::_input_type_name` re-derives the input name out-of-band instead of consuming `mutation_input_shape(...).type_name`.** `fields.py:116-119` re-walks `editable_input_fields(meta.model, fields=, exclude=)` for the selected names AND `editable_input_fields(meta.model)` for the full set, then re-calls `mutation_input_type_name(...)` — duplicating the exact `selected` / `full_field_names` / name computation that `inputs.py::mutation_input_shape` (lines 393-427) exists to single-source as the DRY-1 descriptor. The two paths provably agree today (same inputs, same pure functions), so this is correctness-neutral. Consolidation shape: have `fields.py::_input_type_name` call `mutation_input_shape(meta.model, operation_kind, fields=meta.fields, exclude=meta.exclude).type_name` rather than re-spelling the walk. Already logged as a defer item in the `rev-mutations__fields.md` cycle; recorded here from the inputs.py side for the folder pass. Defer until `mutation_input_type_name`'s identity rule changes OR a 4th name-derivation caller lands — at which point fold all callers onto `mutation_input_shape().type_name`. Do NOT act now: forcing `fields.py` (a finalizer-free import-time factory) to build the full `MutationInputShape` for a name-only need is heavier than the current two-walk, and the merge/bind path already consumes the descriptor.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The materialize / clear lifecycle is a thin domain wrapper over the single-sited 0.0.9 mechanics: `materialize_mutation_input_class` (lines 106-125) delegates to `utils/inputs.py::materialize_generated_input_class` (pinning `module_path` / `family_label="DjangoMutation"` / `ledger`); `build_mutation_input` emits via `utils/inputs.py::build_strawberry_input_class` (line 536) and camel-aliases via `graphql_camel_name`; the GraphQL-name/identity halves mirror `orders/inputs.py` (`INPUTS_MODULE_PATH` line 62, `_materialized_names` line 103). Scalar/enum nullability is single-sourced through `types/converters.py::convert_scalar(..., force_nullable=False)` (line 301) and `scalar_for_field` (line 277); the forward-M2M predicate routes to `utils/relations.py::is_forward_many_to_many` (line 189, the `aa625fef` single-siting); Relay-shape detection routes to `types/relay.py::implements_relay_node` (lines 274, 546). `MutationInputShape` + `mutation_input_shape` (lines 362-427) is itself the DRY-1 single-source consumed by `sets.py` bind/merge (`sets.py:650,708`) for cache key + name.
- **New helpers considered.** `editable_input_fields` (lines 150-222) was evaluated against `orders/inputs.py::_get_concrete_field_names_for_order` and is correctly a genuinely-distinct selector, not a duplication: it is the deliberate OPPOSITE selection (writes EXCLUDE `editable=False` timestamps and INCLUDE forward M2M; the order side does the reverse), sharing only the documented `_meta.get_fields()` + `hasattr(f, "column")` cookbook idiom. No new helper warranted.
- **Duplication risk in the current file.** Repeated literals `DjangoMutation for` (3x, the `ConfigurationError` message prefixes), `many_to_many` (3x `getattr` probes), `DjangoMutation` (2x) are intentional: the error-prefix strings are distinct full messages sharing a brand prefix (not extractable without obscuring the message), and the `many_to_many` probes are the standard Django relation-shape attribute access at three legitimately-separate decision points (selector inclusion, annotation collection-vs-scalar, requiredness exemption).

### Other positives

- **Requiredness derivation is the DRF rule, correctly implemented.** `input_field_required` (lines 225-241) returns required only when `not field.has_default()` and `not field.null` and `not field.blank` — matching the documented "required derived from default/blank/null" contract. The create-vs-partial split is clean: `build_mutation_input` consults the predicate only for the create shape (`is_create and not is_m2m and input_field_required(field)`, line 510), and PARTIAL forces every field optional. M2M is hard-coded optional even in create (line 509-510) with a precise rationale (a parent row cannot carry M2M rows until it has a pk; the resolver's replace/clear/unchanged contract needs omittability).
- **Relation mapping is correct and symmetric.** `relation_input_annotation` (lines 249-286) maps forward FK/OneToOne to `<field>_id` (single id) and M2M to `list[<id>]`, choosing `relay.GlobalID` when the related primary type is Relay-Node-shaped else the raw pk scalar via `scalar_for_field(related_model._meta.pk)`. The python-attr `<name>_id` scheme is the same one `sets.py::_accepted_input_attrs` re-derives for override validation, so consumer `input_class` naming is single-sourced.
- **`_pascalize_token` injectivity is sound.** Lines 304-323: `name.replace("_", "").capitalize()` yields a `[A-Z][a-z0-9]*` token (single leading capital, lowercased tail, underscores stripped). Because Python/Django field names always start with a letter, every token carries exactly one leading capital and no interior capital/underscore, so the sorted-token concatenation in `mutation_input_type_name` decomposes uniquely at uppercase boundaries — the `("a_b","c")→AbC` vs `("a","b_c")→ABc` distinctness the docstring claims holds, and the per-segment-capitalize collision (`ABC` for both) is correctly avoided.
- **Empty-input fail-loud at the framework boundary.** `build_mutation_input` lines 519-535 raises a framework `ConfigurationError` (naming the model + operation) when the effective field set is empty AND no overrides supply a field, rather than letting Strawberry surface a raw `ValueError` at `Schema(...)` build. The `and not overrides` guard correctly exempts a merged input whose generated remainder is empty.
- **Upload (spec-037) handling is correctly placed.** Lines 480-493: `FileField`/`ImageField` map to the `Upload` scalar with the plain field name (never `<name>_id`), falling through to the SAME override-skip / requiredness / `| None`-widening machinery as scalars — lifting the spec-036 CR-6 carve-out so file columns participate in the `Meta.input_class` merge. The `isinstance(field, (FileField, ImageField))` branch sits after the relation branch, so a file column is never mis-routed (file fields are not relations). Matches GLOSSARY (line 1361): required per the per-field rule, `Upload | None` on blank/null.
- **Payload slot is uniform, never model-derived.** `payload_object_slot` (lines 539-546) returns `"node"`/`"result"` off the Relay check; `build_payload_type` (lines 549-571) uses it for the nullable object slot + non-null `errors: list[FieldError]`, single-sited so the resolver (`resolvers.py:773,821`) agrees.
- **GLOSSARY accurate, no drift.** Input-type-generation (lines 637-644), `FieldError` envelope (495-501), `Upload` scalar (1361), and the file/image three-way split (1185, 1261) all match the implementation — per-field required rule, `_id`/`list[id]` mapping, GlobalID-vs-raw-pk, deterministic narrowed-shape name + AR-M6 collision raise, `"__all__"` sentinel via `NON_FIELD_ERROR_KEY`. Ran the GLOSSARY grep (the #4-vs-#5 separator) across all public symbols — genuine #5.

### Summary

`mutations/inputs.py` is the finalizer-free generation substrate for the write-side `<Model>Input` / `<Model>PartialInput` classes, the public `FieldError`, and the `<Name>Payload` wrapper (spec-036 Slice 1). Full first-review scrutiny of new production code found zero High/Medium/Low: the requiredness derivation matches the documented DRF rule, relation `_id`/`list[id]` mapping and GlobalID-vs-raw-pk selection are correct and symmetric with the read side, the `_pascalize_token` injectivity argument is sound, Upload typing is correctly placed and routes through the shared scalar machinery, and the `MutationInputShape` DRY-1 descriptor single-sources name/key/selected-fields for the bind and merge paths. The one DRY opportunity (`fields.py::_input_type_name` re-deriving the name out-of-band) is a correctness-neutral defer-with-trigger item already tracked from the fields.py side. The cycle diff is empty versus both the per-cycle baseline `0933d428` and HEAD (the module landed in HEAD via `aa625fef` / `7d39523b`), so this is a genuine no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (289 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- Cycle diff is empty versus BOTH the per-cycle baseline `0933d428c0b60e33a2f3d27aaec8d23989c0d243` AND HEAD; `mutations/inputs.py` is fully landed in HEAD (last touched by `aa625fef` "Single-site the forward-M2M predicate", `7d39523b` "Refactor upload/file image mapping"). Working tree carries only the unrelated concurrent `optimizer/walker.py` edit and `docs/` review-cycle scratchpads — ignored per AGENTS.md #34.
- Zero High/Medium/Low. The single DRY analysis bullet is a defer-with-trigger item (correctness-neutral, already tracked from the `rev-mutations__fields.md` side) — no action this cycle.
- No GLOSSARY-only fix in scope: ran the GLOSSARY grep across every public symbol (`FieldError`, input-type-generation, `Upload` scalar, file/image split) — all entries match the implementation, no drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits; docstrings and comments reviewed in-place and found accurate (module docstring, `editable_input_fields`, `input_field_required`, `_pascalize_token`, `build_mutation_input` Upload/empty-input comments all match behavior). No changes.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source/behavior change this cycle (empty diff vs baseline and HEAD), and AGENTS.md #21 forbids touching `CHANGELOG.md` without explicit instruction; the active plan `docs/review/review-0_0_11.md` is silent on a changelog entry for this item.

---

## Verification (Worker 3)

### Logic verification outcome

Genuine shape #5 no-source-edit cycle on NEW production code, verified with extra rigor. All High/Medium/Low `None.` are genuine — every load-bearing claim is independently confirmed against source AND pinned by a named test in `tests/mutations/test_inputs.py` (35 tests):

- **Required-vs-optional derivation.** `input_field_required` (inputs.py:225-241) returns required only when `not field.has_default() and not field.null and not field.blank` — the DRF rule. Pinned by `test_input_field_required_rule`, `test_create_input_required_and_optional_shapes`. PartialInput forces every field optional (the predicate is consulted only when `is_create`, line 510) — pinned by `test_partial_input_all_fields_optional_and_unset`.
- **Relation mapping.** Forward FK/OneToOne → `<field>_id` (single id), M2M → `list[<id>]`, GlobalID when the related primary is Relay-Node-shaped else raw pk via `scalar_for_field(related_model._meta.pk)` (`relation_input_annotation`, lines 249-286). Pinned by `test_fk_to_relay_target_uses_globalid_id`, `test_fk_to_non_relay_target_uses_raw_pk_scalar`, `test_o2o_to_relay_target_uses_globalid_id`, `test_m2m_to_relay_target_becomes_list_of_globalid`, `test_m2m_to_non_relay_target_becomes_list_of_raw_pk`. M2M hard-coded optional even in create (line 509-510) — rationale sound (no pk before insert).
- **Upload (spec-037).** `FileField`/`ImageField` → `Upload` scalar with plain field name (never `<name>_id`), after the relation branch so a file column never mis-routes (lines 480-493). Falls through to the SAME override-skip / requiredness / `| None`-widening machinery as scalars. Pinned by `test_required_file_field_maps_to_upload`, `test_required_image_field_maps_to_upload`, `test_blank_file_field_widens_to_upload_optional`, `test_null_file_field_widens_to_upload_optional`, `test_partial_input_file_field_always_optional_upload`, `test_file_field_consumer_override_skips_generated_upload_field`. Matches GLOSSARY:1361 (required per per-field rule, `Upload | None` on blank/null).
- **Empty-input fail-loud.** `build_mutation_input` (lines 519-535) raises framework `ConfigurationError` (naming model + operation) when `not triples and not overrides` — the `and not overrides` guard correctly exempts a merged input with empty generated remainder. Pinned by `test_build_empty_field_set_raises_configuration_error`.
- **Name-identity parity.** `_pascalize_token` injectivity confirmed at runtime: `("a_b","c")→AbC` vs `("a","b_c")→ABc` (DISTINCT — the per-segment-capitalize `ABC` collision is avoided). `MutationInputShape`/`mutation_input_shape` single-sources `type_name`/`cache_key`/`selected` so the all-generated and merged materialize paths derive the name from one computation. Pinned by `test_type_name_full_shape_is_canonical`, `test_type_name_narrowed_shape_is_deterministic_and_distinct`, `test_type_name_token_boundaries_do_not_collide`, `test_identical_shape_dedupes_via_ledger`, `test_distinct_shapes_colliding_on_one_name_raise_configuration_error`.
- **Converter reuse.** `convert_scalar(..., force_nullable=False)` confirmed in `types/converters.py:272-276` (tri-state, `effective_null = field.null if force_nullable is None else force_nullable` at :348) — the generator owns nullability via the required/optional rule, suppressing the column's own `field.null` widening.

No masked defect; no source edit owed.

### DRY findings disposition

The single DRY item (the `mutations/fields.py::_input_type_name` out-of-band name re-derivation) is correctly **defer-with-trigger**: verbatim trigger ("until `mutation_input_type_name`'s identity rule changes OR a 4th name-derivation caller lands"), correctness-neutral rationale (the two paths provably agree today via the same pure functions), and a sound "do NOT act now" cost argument (forcing the finalizer-free import-time `fields.py` factory to build a full `MutationInputShape` for a name-only need is heavier than the current two-walk). Cross-referenced against my own `mutations/fields.py` cycle memory: this is the same DRY-1 item logged from the fields.py side, now recorded from the inputs.py side for the folder pass — consistent, not a new claim. The identity rule the defer relies on is test-pinned (the three `mutation_input_type_name` tests above), so the trigger has a real early-warning canary.

### Temp test verification

- No temp tests needed: every claim is pinned by an existing named test in `tests/mutations/test_inputs.py`; ran a focused runtime `_pascalize_token` injectivity check (no file written).
- Disposition: n/a.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `mutations/inputs.py` checklist box `[x]` in `docs/review/review-0_0_11.md`.

Zero-edit proof (two ways): `git diff 0933d428 -- django_strawberry_framework/mutations/inputs.py` empty AND `git diff HEAD -- <target>` empty; target absent from `git diff --stat 0933d428 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` (stat empty). CHANGELOG diff empty. The only source dirt is `optimizer/walker.py` = AGENTS.md #33 concurrent-maintainer work (explicitly out of scope per dispatch). #4-vs-#5 gate: genuine #5 — the sole `docs/GLOSSARY.md` working-tree hunk is at line 305 (relation-cardinality validation = #33 concurrent work); all mutation-input GLOSSARY prose (Input type generation 639-644, `FieldError` envelope 495-499, `Upload` scalar 1357-1361, file/image split 1185/1261, `DjangoMutation` 388) reads accurate vs live source — no GLOSSARY fix owed. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."; changelog "Not warranted" cites BOTH AGENTS.md #21 and plan silence. Ruff format-check + check pass on the target.
