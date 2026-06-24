# Build: Cross-slice integration pass — form_mutations / 0.0.12 (038)

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md`
Build plan: `docs/builder/build-038-form_mutations-0_0_12.md`
Status: final-accepted

Worker 1 cross-slice integration pass. All six slices (1, 2, 3, 4, 5a, 5b) are
`final-accepted`. This pass runs the six mandatory pre-write steps (BUILD.md
"Cross-slice integration pass"), the integration checks, and the per-candidate
consolidation decisions for the DRY candidates accumulated in
`docs/builder/worker-memory/worker-1.md` across the build.

**Outcome: one cross-slice DRY consolidation is worth doing now** — the
`normalize_form_field_sequence` (forms) ↔ `_normalize_field_sequence` (mutations)
verbatim-near-twin normalizers. Recorded precisely below (Finding I1). The other
accumulated candidates are assessed and accepted/rejected with recorded reasons.
Staged anchors all discharged; dependency direction one-way; exports correct.
Because I1 is a consolidate-now finding, this artifact is `revision-needed`:
Worker 0 dispatches a Worker-2 consolidation pass + Worker-3 review, then returns
to Worker 1 to re-run this integration pass.

---

## Pre-write step results (BUILD.md mandatory 1-6)

### Step 1 — read every prior `bld-slice-*.md` in slice order

Done. Read in full, in order:

- `bld-slice-1-form_converter_inputs.md` (`forms/converter.py`, `forms/inputs.py`,
  `forms/__init__.py`; the converter registry, the `FormInputFieldSpec` reverse map,
  the two input generators) — `final-accepted`.
- `bld-slice-2-form_bases_meta_validation.md` (`mutations/sets.py` seam refactor +
  `make_declaration_registry`; `forms/sets.py` two bases; `mutations/inputs.py`
  `build_payload_type(object_type=None)`; `registry.py` co-clears;
  `types/finalizer.py` bind; `__init__.py` exports) — `final-accepted`.
- `bld-slice-3-resolver_pipeline_field_exposure.md` (`forms/resolvers.py`;
  `mutations/resolvers.py` 8-helper underscore-drop promotion +
  callable `save_or_field_errors`; `mutations/fields.py` 3-axis generalization +
  `_input_type_name` twin deletion; `forms/sets.py` stub-fill / hooks / waiver /
  `_input_field_specs` stash) — `final-accepted`.
- `bld-slice-4-products_live_form_surface.md` (example-only: `products/forms.py`,
  `products/models.py` + source-only migration, `products/schema.py`,
  `test_products_api.py`; no package source) — `final-accepted`.
- `bld-slice-5-docs_version_cut.md` (Slice 5a — version quintet ex-GLOSSARY-line,
  plain docs, CHANGELOG, export-pin) — `final-accepted`.
- `bld-slice-5b-glossary_kanban_db.md` (Slice 5b — DB-backed GLOSSARY
  promote/correct + version-line BoardDoc + KANBAN card move + regenerates) —
  `final-accepted`.

### Step 2 — static-inspection helper coverage

Confirmed run / refreshed. `python scripts/review_inspect.py --all --output-dir
docs/shadow` was run for this pass (68 files; no `--cov*`). Every package `.py`
file with review-worthy logic touched by the build was inspected during its slice
(Slice-2 / Slice-3 planning ran `mutations/sets.py`, `mutations/resolvers.py`,
`mutations/fields.py`, `types/finalizer.py`; Worker 3 ran the new `forms/*.py` at
review time). Slices 4/5a/5b correctly recorded the skip (Slice 4 = example-only;
5a/5b = no package `.py` logic). Refreshed shadow output for the integration scan
covers `forms/{converter,inputs,sets,resolvers}.py` and
`mutations/{sets,inputs,fields,resolvers}.py`.

### Step 3 — "Repeated string literals" cross-comparison (cross-slice DRY signal)

Compared the shadow overviews' Repeated-string-literals sections across the
build-touched files. Cross-file literals fall into three understood classes; none
is a standing DRY defect:

- **Class-name error-message fragments:** `forms/sets.py` (`6x DjangoFormMutation`,
  `6x DjangoModelFormMutation`) vs `mutations/sets.py` (`14x DjangoMutation`) and
  `forms/inputs.py` (`3x DjangoFormMutation for`) vs `mutations/inputs.py`
  (`3x DjangoMutation for`). These are the **disjoint validation-namespace**
  messages (Decision 13): a form `Meta` and a model `Meta` are separate namespaces,
  so the messages deliberately name different bases. Not a candidate.
- **`Meta`-key vocabulary:** `form_class` / `operation` / `permission_classes`
  appear in both `forms/sets.py` and `mutations/sets.py`. These are the dict-key
  names of the validation matrices, not extractable constants (they are the literal
  `Meta` attribute names a consumer types). Not a candidate.
- **Operation verbs:** `"form"` / `"create"` / `"update"` / `"delete"` do **not**
  surface as repeated-literals in any overview (they occur below the 2+-occurrence
  threshold per file — only 3 executable occurrences total in `mutations/fields.py`).
  This is the carry-forward "bare `"form"` operation literal" candidate; see
  Finding C3 (rejected).

The genuine executable-body twin (the two field-sequence normalizers) is NOT a
repeated-string-literal — it is a near-copy of a whole function. It is surfaced by
the carry-forward DRY candidates (Finding I1), not the literal scan.

### Step 4 — "Imports" cross-comparison (dependency direction)

Compared the Imports sections. Dependency direction is **one-way**
(`forms/ → mutations/ → utils/types/registry/relay/scalars/exceptions`), never the
reverse:

- `forms/converter.py` → `..exceptions` only.
- `forms/inputs.py` → `..exceptions`, `..mutations.inputs` (`CREATE`, `PARTIAL`,
  `_pascalize_token`, `relation_input_annotation`), `..registry`, `..scalars`,
  `..types.converters`, `..types.relay`, `.converter`.
- `forms/sets.py` → `..exceptions`, `..mutations.inputs`, `..mutations.permissions`,
  `..mutations.sets` (`DjangoMutation`, `_validate_permission_classes`,
  `_ValidatedMutationMeta`, `make_declaration_registry`), `..utils.querysets`,
  `.inputs`, `.resolvers`.
- `forms/resolvers.py` → `..mutations.resolvers` (the promoted public helpers +
  `_coerce_relation_pk_or_none`), `..mutations.inputs`, `..relay`,
  `..utils.querysets`, `..registry`, `.converter`, `.inputs`.

**Reverse-dependency guard CONFIRMED CLEAN:** no module under `mutations/`,
`utils/`, or `types/` imports from `forms/`. The only `forms` tokens in
`mutations/sets.py` (line 592) and `mutations/fields.py` (lines 77/130/158/165) are
inside **docstrings/comments**, not executable imports (verified by grep).

**`mutations/fields.py` did NOT import the form bases — CONFIRMED.** Its only
imports are `..exceptions` and `.inputs` (`INPUTS_MODULE_PATH`). The Slice-3
target-check generalization is duck-typed (`_has_mutation_protocol`: a `_mutation_meta`
attr + callable `resolve_sync`/`resolve_async`/`input_type_name` + non-`None`
`input_module_path`), which is exactly what avoids the
`fields.py → forms/sets.py → mutations/sets.py → ... → fields.py` cycle. This is the
documented cycle-avoidance and it held.

### Step 5 — walk every slice's `What looks solid` + `DRY findings` for deferred follow-ups

Walked all six. Every deferred item is either (a) already governed by a recorded
decision, (b) a cross-slice DRY candidate handled below, or (c) a non-038 / cosmetic
deferral routed to the deferred-work catalog (bld-final). No deferred follow-up
that *should land in this DRY pass* was missed except the I1 normalizer
consolidation (a Slice-1/Slice-2 `Notes for Worker 3` integration-pass candidate,
landing now). Itemized:

- Slice-1 Low (`_model_less_relation_annotation` `queryset=None` → raw `AttributeError`
  instead of `ConfigurationError`): out-of-spec input shape (a plain-`Form`
  `ModelChoiceField` with no `queryset`); reviewed-and-accepted as a Low at the slice;
  → deferred-work catalog, not this pass (it is a robustness nicety, not a cross-slice
  duplication).
- Slice-2/3 `mutations/inputs.py` file-list + 3rd co-clear-row reconciliations:
  already resolved by Worker 1 spec edits at the slice (Decision 13 + impl-plan table).
- Slice-3 `"form"` literal: explicitly deferred to this pass → Finding C3.
- Slice-5a/5b: `docs/TREE.md` stale `mutations/ # planned by TODO-ALPHA-036-0.0.11`
  (spec-036 doc debt, out of 038 contract) + DONE-038 card-body free-text
  `Status: In progress` (pre-existing, cosmetic): both → deferred-work catalog /
  maintainer follow-up, NOT 038 source edits.

### Step 6 — staged-anchor sweep (this build's spec + card)

`grep -rEn 'TODO\(spec-038|TODO-(ALPHA|BETA|STABLE)-038' .` and the card-id form
`grep -rEn 'TODO-ALPHA-038-0\.0\.12' .`, excluding `KANBAN.md` / `KANBAN.html` /
`BACKLOG.md` (and `docs/builder/` / `docs/SPECS/` scratch/spec context):

**CLEAN.** No `TODO(spec-038 ...)` or `TODO-<MILESTONE>-038` anchor survives in any
shipped source / test / comment. All Slice-2/Slice-3 staged anchors were discharged
in the slice that shipped them: the four `resolve_*` `NotImplementedError` stubs, the
two `build_input` `guard_required` waiver anchors, and the `mutations/fields.py::_input_type_name`
transient-twin anchor are all gone (Slice 3 filled the stubs, wired the waiver, and
deleted the twin). Confirmed via the live grep this pass.

---

## Integration-check findings

### Finding I1 — CONSOLIDATE NOW: the two field-sequence normalizers are a verbatim executable-body twin

**Severity: Medium (redundant implementation that should be consolidated; a
near-copy of a helper across slices that will entrench).**

Two functions normalize `Meta.fields` / `Meta.exclude` into a `tuple[str, ...] | None`
with bare-string + duplicate-name fail-loud. Their **executable bodies are
byte-identical** (verified by reading both directly); they differ ONLY in the
class-name prefix interpolated into two error strings:

Site A (mutations, module-private, 2 real call sites at `mutations/sets.py:520-521`):
```
django_strawberry_framework/mutations/sets.py:319-347
def _normalize_field_sequence(value, *, label="fields"):
    ...
    if value is None: return None
    if isinstance(value, str):
        raise ConfigurationError(
            "DjangoMutation Meta.fields / Meta.exclude must be a sequence of field "
            f"names, not a bare string: {value!r}.")
    names = tuple(value)
    seen = set()
    duplicates = sorted({name for name in names if name in seen or seen.add(name)})
    if duplicates:
        raise ConfigurationError(
            f"DjangoMutation Meta.{label} declares duplicate field name(s): "
            f"{duplicates!r}. Each field may appear at most once.")
    return names
```

Site B (forms, public, 2 real call sites at `forms/inputs.py:233-234`):
```
django_strawberry_framework/forms/inputs.py:173-206
def normalize_form_field_sequence(value, *, label="fields"):
    ...
    if value is None: return None
    if isinstance(value, str):
        raise ConfigurationError(
            "DjangoFormMutation / DjangoModelFormMutation Meta.fields / Meta.exclude must be a "
            f"sequence of field names, not a bare string: {value!r}.")
    names = tuple(value)
    seen = set()
    duplicates = sorted({name for name in names if name in seen or seen.add(name)})
    if duplicates:
        raise ConfigurationError(
            f"DjangoFormMutation / DjangoModelFormMutation Meta.{label} declares duplicate field "
            f"name(s): {duplicates!r}. Each field may appear at most once.")
    return names
```

The only delta is the flavor prefix (`"DjangoMutation"` vs `"DjangoFormMutation /
DjangoModelFormMutation"`) in the two raises. The field-existence-basis divergence
the form needs (`form_class.base_fields` vs the model's editable columns) lives in a
**separate** function (`forms/inputs.py::resolve_effective_form_fields`), so the
normalizer bodies themselves carry zero behavioral divergence — they are pure twins.

**Why consolidate now (not accept):**
- The duplication is **live** (both sides have real call sites; this is not dead
  code — I greped readers per worker-1.md "grep the candidate's readers").
- A natural shared home already exists: `utils/inputs.py` is the established
  cross-family input-generation substrate (`graphql_camel_name`,
  `build_strawberry_input_class`, `materialize_generated_input_class` are already
  imported there by `mutations/`, `forms/`, `filters/`, `orders/`). The normalizer
  belongs alongside `graphql_camel_name`.
- It **will entrench**: the `0.0.13` `SerializerMutation` card
  ([`TODO-ALPHA-039-0.0.13`]) has the same `Meta.fields` / `Meta.exclude` narrowing
  surface and would spawn a THIRD verbatim copy. The integration pass is the right
  moment to single-source the body before that happens.
- It is a Slice-1 and Slice-2 `Notes for Worker 3` flag that explicitly **deferred
  the shared-`utils/` extraction to the integration pass once both sites exist and
  are accepted** ("do NOT pre-extract here ... the shared-extraction call is the
  integration pass's to make once both sites exist"). Both sites now exist and are
  `final-accepted`. This pass is that moment.

**Recommended consolidation (precise, for the Worker-2 pass):**
- Add `normalize_field_name_sequence(value, *, label="fields", flavor)` to
  `django_strawberry_framework/utils/inputs.py` (alongside `graphql_camel_name`).
  `flavor` is the human flavor label interpolated into the two raises (e.g.
  `"DjangoMutation"`, `"DjangoFormMutation / DjangoModelFormMutation"`), mirroring how
  `make_declaration_registry(label)` already parameterizes its reject message by a
  flavor label — single-source the body, keep the per-flavor wording.
- `mutations/sets.py::_normalize_field_sequence`: replace the body with a one-line
  delegation `return normalize_field_name_sequence(value, label=label,
  flavor="DjangoMutation")` (keep the private name + its call sites at lines 520-521),
  OR import the shared helper directly and update the two call sites. Keep the public
  surface unchanged (the name is module-private; either shape is fine).
- `forms/inputs.py::normalize_form_field_sequence`: same — delegate to the shared
  helper with `flavor="DjangoFormMutation / DjangoModelFormMutation"`. `forms/inputs.py`
  already imports from `utils/inputs.py`, so no new import edge.
- The existing tests pin both flavors' messages
  (`tests/mutations/test_sets.py` + `tests/forms/test_inputs.py`); the consolidation
  must keep both message wordings byte-identical so those assertions stay green. No new
  test is strictly required, but a focused `tests/utils/`-tier test of the shared helper
  (both `flavor` strings + the bare-string + duplicate raises) is the cleaner pin — at
  Worker-2 discretion.
- DRY guard: do NOT also collapse `resolve_effective_form_fields` /
  `editable_input_fields` (the field-existence-basis differs legitimately — model
  columns vs `base_fields`); the consolidation is the **normalizer body only**.

This is the single consolidation worth doing now. It is low-risk (a rename + body
move + a parameterized message), and it removes a near-copy that the next flavor card
would otherwise triple.

### Finding C2 — REJECT (keep two): `_form_shape_build_cache` ↔ `_shape_build_cache`

**Decision: accept the two disjoint caches; do NOT merge.**

- `mutations/sets.py::_shape_build_cache` — KEY `(model, operation_kind,
  frozenset(effective_field_names))`, VALUE the bare `input_cls` type.
- `forms/sets.py::_form_shape_build_cache` — KEY `(form_class, operation_kind,
  frozenset(effective_field_names))`, VALUE the `(input_cls, field_specs)` tuple.

**Reason rejected:** they are not twins. (i) Different KEY identity basis
(model vs form_class — never interchangeable). (ii) Different VALUE shape — the form
cache carries the Slice-1 `FormInputFieldSpec` reverse-map `field_specs` that the
Slice-3 decode requires (the model cache has no concept of a reverse map). Merging
the storage would force the model value to grow a `field_specs` slot it never uses,
or fork the value type behind one dict — net complexity, not net DRY. (iii) They live
in their own modules and serve their own `build_input` overrides + their own
`registry.clear()` co-clear row. This is the same legitimately-disjoint posture as the
two declaration registries (Decision 13's named over-DRY trap): the *pattern* is
deliberately mirrored and documented as such in both modules' comments; the *storage*
is correctly separate. The form cache is also load-bearing for the plain-form dedupe
(without it two plain mutations over one form trip the materialize collision). Keeping
two is the higher-quality shape.

### Finding C3 — REJECT (leave inline): the bare `"form"` / `"create"` / `"update"` / `"delete"` operation literals in `mutations/fields.py`

**Decision: leave the operation vocabulary inline; do NOT introduce a shared
operation-sentinel constant surface.**

There are exactly three executable occurrences in `mutations/fields.py`:
`"update"`/`"delete"` in `_synthesized_mutation_signature` (the `id:`-arg and
`data:`-arg gates) and `"form"` in `DjangoMutationField` (`takes_id =
... operation != "form"`). The whole `create`/`update`/`delete`/`form` vocabulary is
bare-literal in `fields.py` today.

**Reason rejected:** (i) Singling out `"form"` for a `forms/inputs.py::FORM` import
would be **asymmetric** — `"create"`/`"update"`/`"delete"` are the model vocabulary
that has always been bare-literal here, and `"form"` is just the model-less sentinel
in the same namespace. (ii) A shared operation-sentinel surface for the *whole*
vocabulary reachable without the form-base import cycle (the cycle is real only for
the form *bases*, not for a sentinel constant) would be net-new scaffolding to name
**three** short, stable literals used in one file — over-engineering against the
"maximally DRY that stays readable" bar. (iii) The model flavor never emits `"form"`,
so the literal cannot misfire; behavior is correct as shipped. (iv) The
repeated-string-literal scan (step 3) confirms none of these crosses the 2+-file
threshold — there is no cross-slice literal-drift signal here, only a single-file
inline vocabulary. The `forms/inputs.py::FORM` / `mutations/inputs.py::CREATE`,`PARTIAL`
sentinels that DO have a shared role (the input-generator kind) are already
single-sourced and imported; the `fields.py` operation gates are a separate, correct
inline use. Leaving them inline is the right call.

### Confirmation C4 — `_pascalize_token` is imported, not re-spelled

**CONFIRMED.** One definition: `mutations/inputs.py::_pascalize_token` (line 304).
Imported by `forms/inputs.py` (line 54, in the `from ..mutations.inputs import ...`
line) and called inside `forms/inputs.py::form_input_type_name`. The injective
token-name scheme is single-sourced; the form name generator reuses the primitive
rather than re-implementing it. No re-spelling anywhere in the tree.

(Note: the Slice-1 `Notes for Worker 3` floated a possible integration-pass *lift* of
`_pascalize_token` into `utils/inputs.py` alongside `graphql_camel_name`. Assessed and
**declined**: it has exactly two readers (`mutations/inputs.py` self + `forms/inputs.py`),
the cross-module import of a pure private primitive is honest and one-way, and moving it
would not reduce any duplication — it is already single-sourced. A lift would be churn
for churn's sake. If/when the `0.0.13` serializer card needs the same token scheme, the
lift becomes worthwhile; not now.)

### Confirmation C5 — `make_declaration_registry` is the single shared registry-mechanics source

**CONFIRMED.** One definition: `mutations/sets.py::make_declaration_registry(label)`
(line 138), returning a `DeclarationRegistry` NamedTuple of bound
`(register, clear, iter_, store)` callables over a fresh private `list[type]`.
Instantiated exactly twice, over disjoint stores:
- `mutations/sets.py:191` — `make_declaration_registry("DjangoMutation")` (the model
  ledger; its callables assigned to the public `register_mutation` /
  `clear_mutation_registry` / `iter_mutations` names).
- `forms/sets.py:112` — `make_declaration_registry("DjangoFormMutation")` (the plain-form
  ledger).

The dedup-by-identity / post-`mark_finalized()` reject / `.clear()` / ordered-`tuple()`
mechanics are one body; the two storage lists are disjoint (Decision 13's over-DRY trap
correctly avoided). Clean.

### Other integration checks (all clean)

- **Duplicated helpers across slices:** none beyond I1. `forms/resolvers.py` CALLS the
  8 promoted `036` helpers (`locate_instance`, `coerce_lookup_id`, `not_found_error`,
  `authorize_or_raise`, `refetch_optimized`, `build_payload`,
  `validation_error_to_field_errors`, callable `save_or_field_errors`) by import — no
  re-implementation. The genuinely net-new code (`_visible_related_object` +
  the kind-split decode + partial-update reconstruction) is the security/shape work the
  `036` pipeline does not provide, not a copy.
- **Inconsistent naming / error handling:** consistent. Both flavors raise
  `ConfigurationError` at class creation with flavor-named messages (disjoint
  namespaces); both map validation failures through the ONE
  `validation_error_to_field_errors(ValidationError(form.errors.as_data()))` →
  `FieldError` envelope; the `IntegrityError` catch is single-sourced through callable
  `save_or_field_errors` (one catch, three save paths). The promoted-helper rename was
  swept across all three test trees (Slice 3).
- **Repeated ORM/queryset patterns:** the visibility query
  (`apply_type_visibility_sync(initial_queryset(...), info)`) is the shared primitive
  reused by both the `036` `_relation_visibility_error` and the form
  `_visible_related_object`; the form decoder cannot call `_relation_visibility_error`
  (it must return the visible OBJECT for `to_field_name`, not just an error) so it reuses
  the primitives, not a parallel query. The G2 re-fetch rides the shared
  `refetch_optimized` (no new optimizer code). No centralizable repeat.
- **Misplaced responsibilities:** none. The construction hooks (`get_form_kwargs` /
  `get_form` / `perform_mutate`) live on the `forms/sets.py` bases (consumer-overridable
  instance methods); the resolver CALLS them. The reverse-map specs are stashed at bind
  (`_input_field_specs`), read at resolve. Payload lives in `mutations.inputs` for both
  flavors; the `data:` input lives in `forms.inputs` — the resolver and `fields.py`
  correctly distinguish the two namespaces.
- **Exports — re-confirmed exactly the two form bases:** `__init__.py` `__all__` adds
  exactly `DjangoFormMutation` and `DjangoModelFormMutation` (alphabetical slots: after
  `DjangoFileType`; after `DjangoListField`), and the `from .forms import ...` re-export.
  `tests/base/test_init.py::test_public_api_surface_is_pinned` mirrors the live 23-symbol
  `__all__` byte-for-byte (DoD item 8). `__version__` is `0.0.12` (Slice 5a). No
  too-broad / missing export.
- **Comments tell one coherent story:** yes. The `_form_shape_build_cache` /
  `_shape_build_cache` twin is documented as a deliberate mirror in both modules; the
  `make_declaration_registry` docstring narrates the disjoint-ledger rationale; the
  duck-typed `fields.py` target check documents the cycle-avoidance. The GLOSSARY
  `DjangoFormMutation` body correction (Slice 5b) brings the standing doc into line with
  the shipped model-less-sibling architecture (Decision 6).

---

## Per-candidate consolidation decisions (summary)

| Candidate (from worker-1 memory) | Decision | Reason |
|---|---|---|
| `normalize_form_field_sequence` ↔ `_normalize_field_sequence` | **CONSOLIDATE NOW** (I1) | Verbatim executable-body twin differing only in a message-prefix string; both live; natural `utils/inputs.py` home; will triple at the `0.0.13` serializer card. |
| `_form_shape_build_cache` ↔ `_shape_build_cache` | **REJECT / keep two** (C2) | Different KEY basis (form_class vs model) and VALUE shape (`(cls, field_specs)` vs bare `cls` — form carries the load-bearing reverse map); legitimately disjoint like the two registries. |
| bare `"form"` (+ `create`/`update`/`delete`) operation literals in `mutations/fields.py` | **REJECT / leave inline** (C3) | Whole vocab is inline in one file (3 occurrences); singling out `"form"` is asymmetric; a shared sentinel surface is over-engineering for 3 stable literals; model flavor never emits `"form"`. |
| `_pascalize_token` imported, not re-spelled | **CONFIRMED** (C4) | One definition (`mutations/inputs.py`), imported by `forms/inputs.py`. A `utils/` lift declined — already single-sourced, would be churn. |
| `make_declaration_registry` single shared source | **CONFIRMED** (C5) | One definition (`mutations/sets.py`), instantiated twice over disjoint stores (Decision 13 over-DRY trap avoided). |

---

## Staged-anchor sweep result

**CLEAN.** No `TODO(spec-038 ...)` / `TODO-<MILESTONE>-038` / `TODO-ALPHA-038-0.0.12`
anchor survives in shipped source / tests / comments (excluding `KANBAN.*` /
`BACKLOG.md` board cards). Every Slice-2/Slice-3 staged anchor was discharged in the
slice that shipped its work. No anchor to route to an owning slice.

---

## Dependency-direction confirmation

**One-way, confirmed.** `forms/ → mutations/ → utils / types / registry / relay /
scalars / exceptions`. No `mutations/`, `utils/`, or `types/` module imports from
`forms/` (the only `forms` tokens in `mutations/sets.py` / `mutations/fields.py` are in
docstrings). `mutations/fields.py` does NOT import the form bases — the duck-typed
target check (`_has_mutation_protocol`) is what avoids the cycle, exactly as the spec
documents. The public-surface boundary is intact (exactly the two form bases added to
`__all__`).

---

## Consolidation loop needed?

**Yes — one loop, for Finding I1 only.**

Worker 0: dispatch a **Worker-2 consolidation pass** to lift the shared
`normalize_field_name_sequence(value, *, label, flavor)` into `utils/inputs.py` and
delegate both `mutations/sets.py::_normalize_field_sequence` and
`forms/inputs.py::normalize_form_field_sequence` to it (keeping both message wordings
byte-identical so the existing assertions in `tests/mutations/test_sets.py` and
`tests/forms/test_inputs.py` stay green), then a **Worker-3 review pass**, then return
to **Worker 1** to re-run this integration pass. C2 / C3 are accepted-with-reason (no
work), C4 / C5 confirmed (no work). After the I1 loop is clean, the integration pass
flips to `final-accepted` and the build proceeds to the final test-run gate.

### Deferred follow-ups

These are NOT 038-contract work and are NOT routed to the I1 loop; they are recorded
for the `bld-final.md` deferred-work catalog / the next spec author / the maintainer:

- **`docs/TREE.md` stale `mutations/` line.** Both the current-on-disk and target
  layouts still render `mutations/` as `# planned by TODO-ALPHA-036-0.0.11` despite
  `mutations/` shipping in `0.0.11` (`DONE-036`). This is **spec-036 doc debt, out of
  spec-038's contract** — Worker 1 edits only the active spec, not source TREE here.
  (Flagged independently in Slices 5a and 5b.) Maintainer / next-author follow-up.
- **DONE-038 card-body free-text `Status: In progress`.** The rendered DONE-038 card
  body shows `Status: In progress` (vs sibling DONE-037's `Status: Shipped`). It was
  already `In progress` at HEAD (pre-existing free-text, independent of the workflow
  `status.key=done` which is correct); outside Slice-5b's named scope. Cosmetic; a
  one-line DB-backed `CardItem` edit + re-render if the maintainer wants the DONE-card
  convention nicety. NOT a defect.
- **Slice-1 Low: `_model_less_relation_annotation` `queryset=None` → raw
  `AttributeError`.** A plain-`Form` `ModelChoiceField` declared with no `queryset`
  raises a raw `AttributeError` instead of a `ConfigurationError`. Out-of-spec input
  shape; reviewed-and-accepted as a Low at Slice 1. Robustness nicety for a future
  slice/card; not a cross-slice duplication, so not part of the I1 loop.
- **Spec self-reference path discrepancy (`docs/spec-038-...` vs `docs/SPECS/spec-038-...`).**
  Build-plan flag; the live spec is the `docs/SPECS/` one. Cosmetic spec-internal
  self-reference inconsistency in Decision 1 / DoD item 1; Worker 1 may reconcile in a
  future spec-touching pass or leave to the next-author archive sweep. Not a build defect.

## Consolidation pass (Worker 2 — integration I1)

Lifted the verbatim-twin field-sequence normalizer into the shared input
substrate per Finding I1's recommended fix; both call sites now delegate.

### Files touched

Three package source files (slice-intended; `git status --short` classified —
the rest of the dirty tree is the concurrent build-038 working state per AGENTS.md
rule 34 and was left untouched):

- `django_strawberry_framework/utils/inputs.py` — **added** the shared helper
  `normalize_field_name_sequence(value, *, label="fields", flavor)` directly after
  `graphql_camel_name` (the home Finding I1 named — alongside the existing
  cross-family input-substrate helpers). It holds the single normalizer body
  (bare-string reject + duplicate-name reject + tuple coercion); `flavor` is the
  only parameterized divergence (the human flavor label interpolated into the two
  `ConfigurationError` raises), mirroring how `make_declaration_registry(label)`
  already parameterizes its reject wording.
- `django_strawberry_framework/mutations/sets.py` — `_normalize_field_sequence`
  body replaced with a one-line delegation
  `return normalize_field_name_sequence(value, label=label, flavor="DjangoMutation")`;
  added `from ..utils.inputs import normalize_field_name_sequence`. Private name +
  its two call sites (the `_validate_meta` `fields`/`exclude` normalization) unchanged.
- `django_strawberry_framework/forms/inputs.py` — `normalize_form_field_sequence`
  body replaced with a delegation passing
  `flavor="DjangoFormMutation / DjangoModelFormMutation"`; added
  `normalize_field_name_sequence` to the existing `from ..utils.inputs import (...)`
  block (no new import edge — `forms/inputs.py` already imported from `utils/inputs`).
  Public name + behavior unchanged; `resolve_effective_form_fields` still calls it.

### What was lifted + the shared signature

```
# django_strawberry_framework/utils/inputs.py
def normalize_field_name_sequence(
    value: Any,
    *,
    label: str = "fields",
    flavor: str,
) -> tuple[str, ...] | None
```

The field-existence-basis logic was **not** touched (it lives in
`forms/inputs.py::resolve_effective_form_fields` and the model bind's
`editable_input_fields` per the finding's DRY guard); only the normalizer body
moved. `resolve_effective_form_fields` / `editable_input_fields` were NOT collapsed
(C2-style legitimately-disjoint basis: model columns vs `base_fields`).

### Byte-identical error-message confirmation

Both flavors' `ConfigurationError` messages are **byte-identical to the
pre-refactor wording**. The shared body emits `f"{flavor} Meta.fields / Meta.exclude
must be a sequence of field names, not a bare string: {value!r}."` and `f"{flavor}
Meta.{label} declares duplicate field name(s): {duplicates!r}. Each field may appear
at most once."`; with `flavor="DjangoMutation"` and
`flavor="DjangoFormMutation / DjangoModelFormMutation"` these reconstruct the
former two-literal-split messages character-for-character (only the literal split
points differed for line length; the concatenated runtime text is unchanged).

### Validation run (in order)

1. `uv run ruff format .` → `277 files left unchanged` (my edits already conform).
2. `uv run ruff check --fix .` → `All checks passed!`.
3. `scripts/check_trailing_commas.py` (the separate enforcer) → reformatted my edited
   files to comma-layout, then `--check` clean and idempotent (`Fixed 0 file(s)`);
   re-ran `ruff format .` after → still `277 files left unchanged` (formatter-stable).
4. `git status --short` classified: the three files above are slice-intended; the rest
   of the dirty tree is concurrent build-038 state (six slices) — not touched. No tool
   churn left to revert. `examples/fakeshop/db.sqlite3`, `KANBAN.*`, `docs/GLOSSARY.md`,
   `docs/feedback.md` left in their concurrent/generated state per the pass flags.
5. `uv run pytest tests/forms/test_inputs.py tests/mutations/test_sets.py --no-cov`
   → **80 passed, 2 failed**. Both message-pinning families pass
   (`test_meta_fields_bare_string_raises`, `test_meta_fields_rejects_bare_string`,
   `test_meta_fields_rejects_duplicates`). The 2 failures
   (`test_bind_dedupes_full_set_fields_with_bare_create`,
   `test_bind_dedupes_fields_with_complementary_exclude`) are **pre-existing and
   unrelated to this consolidation** — see below.

### Pre-existing-failure verification (worker-2.md "Pre-existing claim verification")

The 2 failures are Slice-4 test-data drift: `Item` gained a nullable `attachment`
`FileField` (`examples/fakeshop/apps/products/models.py #"attachment = models.FileField"`),
so `Item`'s editable-column set is now `{name, description, category, is_private,
attachment}`. Both tests' `fields=(...)` / `exclude=(...)` lists predate that column,
so their effective set is `{name, attachment}` not `{name}` and the two narrowings no
longer dedupe (`ItemNameInput` vs `ItemAttachmentNameInput`). My change touches only
the normalizer's two message strings — it cannot affect field editability or dedup.

Verified by reverse-applying ONLY my three edits (backed up to `/tmp`, restored the
inline `_normalize_field_sequence` body + dropped the `utils.inputs` import) and
re-running the two tests:
`uv run pytest tests/mutations/test_sets.py::test_bind_dedupes_full_set_fields_with_bare_create
tests/mutations/test_sets.py::test_bind_dedupes_fields_with_complementary_exclude --no-cov`
→ **2 failed** with the byte-identical `ItemNameInput is ItemAttachmentNameInput`
assertion error. Then restored my consolidated edits from the backups (delegation +
import confirmed back in place; ruff + comma-check re-run clean). The failures are
independent of this pass.

### Dependency direction

Stays **one-way**. `utils/inputs.py` imports nothing from `forms/` or `mutations/`
(its only project import is `..exceptions`, unchanged); it is the substrate both
import FROM. `mutations/sets.py` now imports `normalize_field_name_sequence` from
`..utils.inputs` (a new `mutations/ → utils/` edge — the allowed direction);
`forms/inputs.py` reuses its existing `..utils.inputs` import. No reverse edge added.

### Notes for Worker 3

- The shared helper has 3 readers if/when the `0.0.13` serializer card lands; for now
  exactly two (the two delegations). No new `tests/utils/`-tier test was added — the
  finding marked it optional/at-discretion and both flavors' messages are already pinned
  by `tests/mutations/test_sets.py` + `tests/forms/test_inputs.py` (which exercise the
  helper through the delegations). If you want the helper pinned directly, a
  `tests/utils/test_inputs.py` case over both `flavor` strings + the two raises is the
  cleaner pin; flagged, not added, to avoid over-scoping the consolidation.
- The 2 pre-existing `test_sets.py` dedup failures (Slice-4 `Item.attachment` drift) are
  NOT mine and NOT part of the I1 loop — recorded above with verification. A separate
  background task was raised to update those two tests' field lists; route it as
  deferred-work, not an I1-loop finding.
- No `scripts/review_inspect.py` shadow file was needed for this pass (a body move +
  two delegations; both sites read directly).

## Consolidation pass (Worker 2 — integration I2)

Fixed the in-build regression I2: Slice-4 `Item.attachment` column drift had left
`tests/` package-tier fixtures hardcoding `Item`'s OLD editable-column set. This is
test-fixture staleness, NOT a production defect — the dedup / editable-field /
filter-build logic is correct; the tests pinned a column set that no longer matches
the model. Fixed in this build (the prior consolidation pass had wrongly deferred
the two `test_sets.py` dedup cases to a background task — re-routed and fixed here).

### Root cause

`examples/fakeshop/apps/products/models.py::Item` gained a nullable `attachment`
`FileField` in Slice 4 (declared between `category` and `is_private`). `Item`'s
editable-column set is therefore now, in declaration order,
`(name, description, category, attachment, is_private)`. Every package test that
hardcoded the OLD set `(name, description, category, is_private)` — whether as an
expected list, a `fields=`/`exclude=` narrowing, or an `"__all__"` sweep — went red.
The package `tests/` tree was last fully run before Slice 4, so these were uncaught
until this sweep.

### Files touched (test fixtures only — NO production change)

Three package test files:

- `tests/mutations/test_sets.py` — the two I2-named dedup tests:
  - `test_bind_dedupes_full_set_fields_with_bare_create`: added `"attachment"` to
    the `CreateFull` `fields=` tuple (declaration order, between `category` and
    `is_private`) so the effective set is the FULL editable set again → dedupes to
    the canonical `ItemInput` (was spuriously producing the narrowed
    `ItemCategoryDescriptionIsprivateNameInput`). Docstring's "full editable set"
    line updated to include `attachment`.
  - `test_bind_dedupes_fields_with_complementary_exclude`: added `"attachment"` to
    the `CreateViaExclude` `exclude=` tuple so the effective set is `{name}` again →
    both narrowings produce `ItemNameInput` and dedupe (was `ItemNameInput` vs
    `ItemAttachmentNameInput`). The 4-element tuple crossed the comma-enforcer
    explode threshold → reformatted to one-per-line by `scripts/check_trailing_commas.py`.
- `tests/mutations/test_inputs.py` — the editable-field selection tests:
  - `test_editable_fields_exclude_pk_auto_timestamps_and_reverse_relations`: added
    `"attachment"` to the expected full editable list (declaration order).
  - `test_editable_fields_narrow_by_exclude`: `exclude=("description","is_private")`
    now correctly leaves `["name", "category", "attachment"]` (intent preserved —
    drops the two named columns, keeps the rest in declaration order; updated the
    expected list to include the surviving `attachment`).
- `tests/filters/test_sets.py` — `test_filterset_get_fields_includes_pk_for_all_fields_shorthand`:
  the `fields="__all__"` sweep now raises because `django-filter` has no default
  filter for a `FileField` (`attachment`). Added `exclude=("attachment",)` to the
  FilterSet `Meta` (with an explanatory comment) so the `__all__` build succeeds —
  preserving the test's intent (the shorthand adds the PK column). This is the same
  fixture-staleness class, surfaced through `django-filter`'s field-recognition rather
  than the dedup name.

### `tests/` sweep result

`uv run pytest tests/ --no-cov` (package tree only, no `--cov*`):

- BEFORE the sweep-fixes: **3 failed, 1993 passed, 3 skipped** — the two I2-named
  `test_sets.py` dedup cases PLUS one I2-named `test_inputs.py` editable-list case were
  surfaced together (the 2nd `test_inputs.py` case + the `filters` case appeared once
  the full tree ran). Exact stale set found: `test_sets.py::test_bind_dedupes_full_set_fields_with_bare_create`,
  `test_sets.py::test_bind_dedupes_fields_with_complementary_exclude`,
  `test_inputs.py::test_editable_fields_exclude_pk_auto_timestamps_and_reverse_relations`,
  `test_inputs.py::test_editable_fields_narrow_by_exclude`,
  `filters/test_sets.py::test_filterset_get_fields_includes_pk_for_all_fields_shorthand`.
- AFTER all fixture fixes: **1996 passed, 3 skipped, 0 failed.** The package `tests/`
  tree is fully green.

### Validation run (in order)

1. `uv run ruff format .` → `277 files left unchanged`.
2. `uv run ruff check --fix .` → `All checks passed!`.
3. `scripts/check_trailing_commas.py` (separate enforcer): flagged the new 4-element
   `exclude` tuple in `test_sets.py:902` → `--fix` exploded it one-per-line; re-ran
   `ruff format .` → still `277 files left unchanged` (formatter-stable); enforcer
   `--check` then clean.
4. `git status --short` classified: the three test files above are the only
   slice-intended (I2) diff. The rest of the dirty tree is the concurrent build-038
   working state (six slices + the I1 consolidation) per AGENTS.md rule 34, untouched.
   `examples/fakeshop/db.sqlite3`, `KANBAN.*`, `docs/GLOSSARY.md`, `docs/feedback.md`
   left in their concurrent/generated state per the pass flags. No production source
   changed; the I1 consolidation files (`utils/inputs.py`, `mutations/sets.py`,
   `forms/inputs.py`) were NOT re-touched by this pass.

### Example-tree staleness noted for the final gate

The fix scope here is the package `tests/` tree. I did not run the example-project
trees (`examples/fakeshop/test_query/`) or the live tests — those are the final
gate's scope. I have NO evidence of an example-tree `Item`-column assumption broken
by `attachment` (Slice 4 added the column AND its own `examples/.../test_products_api.py`
in the same slice, so the example surface was authored against the new column). Final
gate should still run the example + live trees to confirm, but no specific example-tree
staleness is flagged from this pass.

## Review (Worker 3 — integration consolidation I1+I2)

Reviewed ONLY the I1 consolidation (`utils/inputs.py`, `mutations/sets.py`,
`forms/inputs.py` — the normalizer lift) and the I2 test-fixture fixes
(`tests/mutations/test_sets.py`, `tests/mutations/test_inputs.py`,
`tests/filters/test_sets.py`) via `git diff`. The rest of the dirty tree (the six
accepted slices' uncommitted state, the Slice-2 `make_declaration_registry` /
`_validate_meta` seam refactor that rides along in the `mutations/sets.py` and
`tests/mutations/test_sets.py` diffs, the `__init__.py` export adds + `__version__`
bump) is cumulative build-038 state out of THIS review's scope (cumulative-diff
trap — filtered via the I1/I2 Files-touched sections).

### High

None.

### Medium

None.

### Low

None.

### DRY findings

- **I1 is the correct, minimal consolidation.** The shared
  `normalize_field_name_sequence(value, *, label="fields", flavor)` in
  `utils/inputs.py` holds ONE normalizer body; both call sites delegate in one line
  (`mutations/sets.py::_normalize_field_sequence` →
  `flavor="DjangoMutation"`; `forms/inputs.py::normalize_form_field_sequence` →
  `flavor="DjangoFormMutation / DjangoModelFormMutation"`). The only pre-refactor
  divergence (the flavor prefix in the two raises) is the single hoisted parameter,
  mirroring how `make_declaration_registry(label)` parameterizes its reject wording.
  No new duplication introduced.
- **No over-DRY (DRY guard honored).** The field-existence-basis logic was NOT
  merged: `forms/inputs.py::resolve_effective_form_fields` (basis: `base_fields`)
  and the model bind's `editable_input_fields` (basis: model editable columns) are
  untouched. Confirmed only the SHAPE-validation body moved; the helper's docstring
  explicitly states the existence check "stays at each call site."
- **Readers verified live.** `grep` over `django_strawberry_framework/` confirms the
  shared helper has exactly two readers (the two delegations); the two normalizer
  entry points each have their real `Meta` call sites
  (`mutations/sets.py:507-508`, `forms/inputs.py:222-223`). Not dead code; a live
  consolidation.

### Public-surface check

**Confirmed: this consolidation changes NO public surface.** Neither the I1 nor the
I2 diff touches `django_strawberry_framework/__init__.py`, `__all__`, or
`__version__`. (The `__init__.py` working-tree delta visible in `git diff HEAD` —
the `DjangoFormMutation` / `DjangoModelFormMutation` export adds and the `0.0.11`→
`0.0.12` bump — is Slice-2 + Slice-5a cumulative state, NOT part of this
consolidation; the I1/I2 Files-touched lists exclude `__init__.py`.) The new
`utils/inputs.py::normalize_field_name_sequence` is a module-internal helper, not
re-exported.

### What looks solid

- **I1 byte-identity (both flavors), verified against pristine HEAD.** The shared
  body emits `f"{flavor} Meta.fields / Meta.exclude must be a sequence of field
  names, not a bare string: {value!r}."` and `f"{flavor} Meta.{label} declares
  duplicate field name(s): {duplicates!r}. Each field may appear at most once."`.
  With `flavor="DjangoMutation"` these reconstruct character-for-character the
  `git show HEAD:.../mutations/sets.py` originals (the bare-string + duplicate raises
  at HEAD lines 288-289 / 296-297). The form flavor's pre-refactor wording (recorded
  in Finding I1, since `forms/inputs.py` is a net-new uncommitted file with no HEAD
  rev) reconstructs identically with `flavor="DjangoFormMutation /
  DjangoModelFormMutation"`. Only the literal line-split points differed pre-refactor;
  concatenated runtime text is unchanged. The substring-matching pinning tests
  (`test_sets.py::test_meta_fields_bare_string_raises` / `test_meta_duplicate_*`;
  `test_inputs.py::test_meta_fields_rejects_bare_string` /
  `_rejects_duplicates`) all pass through the delegations for both flavors.
- **Dependency direction stays one-way.** `utils/inputs.py` imports nothing from
  `forms/` or `mutations/` (its only project import is `..exceptions`). The new
  `mutations/sets.py` → `..utils.inputs` edge is the allowed `mutations/ → utils/`
  direction; `forms/inputs.py` reused its existing `..utils.inputs` import block (no
  new edge). No reverse `utils/`→`forms/`|`mutations/` edge added.
- **I2 each fix PRESERVES INTENT (no weakened assertion; NO production change).**
  Confirmed `Item`'s current editable declaration order is `(name, description,
  category, attachment, is_private)` — `attachment` (`models.FileField`,
  `products/models.py:63`) sits between `category` (52) and `is_private` (68).
  - `test_sets.py::test_bind_dedupes_full_set_fields_with_bare_create`: `CreateFull.fields`
    now lists the FULL editable set incl. `attachment` (right slot), so it's truly
    the canonical shape — asserts `is sys.modules[INPUTS_MODULE_PATH].ItemInput`
    (genuine full-set dedupe to canonical, not a degraded assert). Docstring updated.
  - `test_sets.py::test_bind_dedupes_fields_with_complementary_exclude`: `exclude` now
    also drops `attachment`, so the complementary effective set is genuinely `{name}`
    matching `fields=("name",)` — both narrowings dedupe to the same shape-derived
    name. Genuine equal-effective-set dedupe.
  - `test_inputs.py::test_editable_fields_exclude_pk_auto_timestamps_and_reverse_relations`:
    expected full list now `[name, description, category, attachment, is_private]` —
    correct new column in the right order; the pk / auto-timestamp / reverse-FK drops
    are all still asserted.
  - `test_inputs.py::test_editable_fields_narrow_by_exclude`: `exclude=("description",
    "is_private")` → `["name", "category", "attachment"]`. NOT weakened — `attachment`
    was never excluded, so it correctly survives in declaration order; the test still
    proves exclude drops only the named columns.
  - `filters/test_sets.py::test_filterset_get_fields_includes_pk_for_all_fields_shorthand`:
    `exclude=("attachment",)` added; the PK-inclusion assertion (`pk_name in fields`)
    is unchanged. The django-filter constraint is REAL, not a dodge — verified
    `models.FileField not in django_filters.filterset.FILTER_FOR_DBFIELD_DEFAULTS`
    (and `ImageField` likewise absent), while `TextField`/`BooleanField` are present;
    a `"__all__"` sweep has no filter to assign for a `FileField` and genuinely
    raises.
  - No production source appears in the I2 diff (test fixtures only) — the dedup /
    editable-field / filter-build logic is correct; the tests pinned a stale column
    set.

### Temp test verification

No temp tests were needed. The I1 byte-identity was proven by direct source read +
`git show HEAD` of the model original; the form original is captured in Finding I1.
The I2 intent was proven by reading each assertion against `Item`'s current columns
and the `editable_input_fields` declaration-order contract. The django-filter
`FileField` constraint was confirmed with a one-shot `uv run python` introspection of
`FILTER_FOR_DBFIELD_DEFAULTS` (not persisted).

**Static-helper:** SKIPPED with reason. `utils/inputs.py` gained a single lifted
function whose executable body is ~13 statements (well under the 30-lines-of-new-logic
threshold); it is behavior MOVED from `mutations/sets.py`, not net-new logic, and the
body was read directly and verified byte-equivalent to the HEAD original. Per BUILD.md
"When to run the helper during build", recorded as a skip rather than a run. Matches
Worker 2's note that no shadow file was needed.

**Package-tree test result (no `--cov*`):**
- `uv run pytest tests/mutations/test_sets.py tests/mutations/test_inputs.py
  tests/forms/test_inputs.py tests/filters/test_sets.py --no-cov` → **211 passed**.
- `uv run pytest tests/ --no-cov` → **1996 passed, 3 skipped, 0 failed** — matches
  Worker 2's reported 1996/0 count exactly.
- Carve-outs (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`,
  `docs/GLOSSARY.md`) were already dirty (concurrent build-038 state, AGENTS.md rule
  34; `db.sqlite3` same-size 3391488→3391488 = external writer) and are NOT part of
  the I1/I2 diff — left untouched per the pass flags.

### Notes for Worker 1

- **No direct `tests/utils/`-tier pin of `normalize_field_name_sequence`** was added
  (`tests/utils/test_inputs.py` has no reference). Worker 2 flagged this as
  optional/at-discretion; both flavors' messages ARE pinned through the delegations
  (`test_sets.py` + `test_inputs.py` `forms` cases). Acceptable as-is; if you want the
  shared helper pinned in its own home before the `0.0.13` serializer card adds a
  third reader, a `tests/utils/test_inputs.py` case over both `flavor` strings + the
  two raises is the cleaner pin. Non-blocking.
- **I2 re-routed correctly.** The I2 pass folded back the two `test_sets.py` dedup
  fixes that the I1 pass had wrongly deferred to a background task, plus the two
  `test_inputs.py` cases and the `filters/test_sets.py` case surfaced by the full-tree
  sweep. All five are test-fixture staleness from Slice-4 `Item.attachment`; no
  production change. The integration pass is now clean for I1+I2 — return to the
  Worker-1 re-run of the integration pass, then the final test-run gate.
- **Example/live trees not run here** (out of this review's scope, as Worker 2 noted).
  The final gate owns `examples/fakeshop/test_query/` + live tests; no specific
  example-tree `Item`-column staleness is flagged from this pass.

### Review outcome

`review-accepted`. I1 + I2 are clean: zero High/Medium/Low findings. I1's two
`ConfigurationError` messages are byte-identical to pre-refactor for both flavors and
the dependency direction stays one-way; each of the five I2 test fixes preserves the
original test intent against `Item`'s current columns (no weakened assertion) with NO
production code change; the package `tests/` tree is green at 1996 passed / 0 failed,
matching Worker 2's count.

---

## Final integration verification (Worker 1)

The consolidation loop (I1 + I2) is landed and Worker-3-accepted. This pass
re-confirms the two findings are resolved on disk, re-runs the close-of-pass
integration checks, assembles the deferred-follow-ups catalog, and flips the
integration pass to `final-accepted`. No further consolidation loop is needed.

### Spec status-line re-verification

Read `docs/SPECS/spec-038-form_mutations-0_0_12.md` header (lines 1-5 / 42). The
status reads **IN PROGRESS** (line 42). This is correct and unchanged: the spec
flips to shipped at the build's close, not at the integration pass — Slice 5b
carries the GLOSSARY/KANBAN ship-state, and the spec status line is the
maintainer's/final-gate's to move at merge, not the integration pass's. No spec
edit this pass.

### I1 resolved — confirmed on disk (spot-checked the diff)

- **Shared helper in place.** `django_strawberry_framework/utils/inputs.py::normalize_field_name_sequence(value, *, label="fields", flavor)`
  holds the single normalizer body (bare-string reject + duplicate-name reject +
  tuple coercion), placed directly after `graphql_camel_name` (the home Finding I1
  named). Read the body directly: `flavor` is the only parameterized divergence,
  interpolated into both `ConfigurationError` raises.
- **Both call sites delegate.** `mutations/sets.py::_normalize_field_sequence`
  body is the one-line `return normalize_field_name_sequence(value, label=label,
  flavor="DjangoMutation")` (import added at `mutations/sets.py #"from ..utils.inputs import normalize_field_name_sequence"`);
  `forms/inputs.py::normalize_form_field_sequence` delegates with
  `flavor="DjangoFormMutation / DjangoModelFormMutation"` (added to the existing
  `from ..utils.inputs import (...)` block — no new import edge). Private name +
  the two `mutations/` `Meta` call sites and the public form name + its
  `resolve_effective_form_fields` caller all unchanged.
- **Messages byte-identical.** The shared body emits
  `f"{flavor} Meta.fields / Meta.exclude must be a sequence of field names, not a bare string: {value!r}."`
  and `f"{flavor} Meta.{label} declares duplicate field name(s): {duplicates!r}. Each field may appear at most once."`.
  With each flavor substituted these reconstruct the pre-refactor wording
  character-for-character (Worker 3 verified against pristine `git show HEAD` for the
  model flavor; the form flavor's pre-refactor wording is captured in Finding I1).
- **Field-existence basis NOT collapsed (DRY guard honored).**
  `forms/inputs.py::resolve_effective_form_fields` (basis `base_fields`) and the
  model bind's `editable_input_fields` (basis editable columns) are untouched — only
  the SHAPE-validation body moved.
- **Readers verified live.** The shared helper has exactly two readers (the two
  delegations) today; it will gain a third at the `0.0.13` serializer card — the
  entrench-prevention this consolidation was timed for.

### I2 resolved — confirmed on disk (5 fixture fixes, intent preserved)

`Item` gained a nullable `attachment` `FileField`
(`examples/fakeshop/apps/products/models.py #"attachment = models.FileField"`),
sitting between `category` and `is_private`, so the current editable declaration
order is `(name, description, category, attachment, is_private)`. All five package
test-fixture staleness fixes are in place and preserve intent (no weakened
assertion; NO production change):

- `tests/mutations/test_sets.py::test_bind_dedupes_full_set_fields_with_bare_create`
  — `"attachment"` added to the `CreateFull` `fields=` tuple (declaration slot);
  docstring full-editable-set line updated to include it (line ~850).
- `tests/mutations/test_sets.py::test_bind_dedupes_fields_with_complementary_exclude`
  — `"attachment"` added to the `CreateViaExclude` `exclude=` tuple so the effective
  set is genuinely `{name}` again (line ~905).
- `tests/mutations/test_inputs.py::test_editable_fields_exclude_pk_auto_timestamps_and_reverse_relations`
  — expected full editable list now includes `"attachment"` in declaration order
  (line ~132).
- `tests/mutations/test_inputs.py::test_editable_fields_narrow_by_exclude` —
  `exclude=("description","is_private")` correctly leaves
  `["name", "category", "attachment"]` (line ~156); `attachment` was never excluded,
  so it correctly survives.
- `tests/filters/test_sets.py::test_filterset_get_fields_includes_pk_for_all_fields_shorthand`
  — `exclude=("attachment",)` added to the FilterSet `Meta` with an explanatory
  comment (lines ~213-217); `django-filter` has no default filter for a `FileField`,
  so the `"__all__"` sweep would otherwise raise. The PK-inclusion assertion is
  unchanged.

I2 was a **real in-build regression** (Slice-4 `Item.attachment` blast radius into
the package `tests/` tree), correctly fixed in-build by the consolidation loop —
not deferred. The prior loop had wrongly routed two of these to a background task;
the I2 pass re-routed and fixed all five in-build. Worker 3 confirmed the full
package `tests/` tree green at **1996 passed / 3 skipped / 0 failed**.

### Re-run integration checks at the close

- **Staged-anchor sweep — CLEAN.**
  `grep -rEn 'TODO\(spec-038|TODO-(ALPHA|BETA|STABLE)-038|TODO-ALPHA-038-0\.0\.12' .`
  over shipped source/tests/examples + standing docs
  (`django_strawberry_framework/`, `tests/`, `examples/`, `README.md`,
  `docs/TREE.md`, `docs/README.md`, `CHANGELOG.md`, `TODAY.md`), excluding
  `KANBAN.*` / `BACKLOG.md`: **NONE.** The only live hits are in `docs/SPECS/`
  (spec narrative referencing the card id — expected) and `docs/builder/` (this
  build's own scratch artifacts — expected). No `TODO(spec-038 ...)` anchor
  survives in any shipped file; every Slice-2/Slice-3 staged anchor was discharged
  in the slice that shipped its work.
- **Dependency direction — one-way, confirmed at the close.** Re-greped every
  executable `forms` token in `mutations/`, `utils/`, `types/`: the two
  `mutations/` occurrences (`fields.py`, `sets.py`) are docstring/comment mentions,
  not imports. The single executable `types/ → forms/` edge is the **function-local**
  `from ..forms.sets import bind_form_mutations` inside `types/finalizer.py`'s
  phase-2.5 bind window — the documented Slice-2 / Decision-6/13 orchestration seam
  (the finalizer drives BOTH the `DjangoMutation` ledger and the disjoint plain-form
  ledger in the same window; the import is function-local and cycle-safe, mirroring
  the `bind_mutations` idiom). This is the intended orchestration edge (Step 4 listed
  `types/finalizer.py` bind as a Slice-2 deliverable), NOT a reverse-dependency
  violation. The cycle-avoidance boundary that matters — `mutations/fields.py` does
  NOT import the form bases (duck-typed `_has_mutation_protocol`) — holds.
  `utils/inputs.py` imports nothing from `forms/`/`mutations/` (only `..exceptions`):
  it is the substrate both import FROM, and the new I1 edge is the allowed
  `mutations/ → utils/` direction.
- **`__all__` — exactly the two form bases.** `__init__.py` `__all__` adds exactly
  `DjangoFormMutation` (line 44) and `DjangoModelFormMutation` (line 47) plus the
  `from .forms import ...` re-export (line 18). `__version__ = "0.0.12"` (line 37),
  matching `pyproject.toml` (line 4). No too-broad / missing export; the I1/I2
  consolidation touched no public surface (Worker 3 public-surface check confirmed).
- **No remaining cross-slice duplication.** I1 was the single consolidate-now
  finding and is landed; C2 (the two shape caches) and C3 (the inline operation
  vocabulary) are accepted-with-reason as legitimately disjoint; C4
  (`_pascalize_token`) and C5 (`make_declaration_registry`) confirmed single-sourced.
  No new duplication introduced by the consolidation.

### Spot-run (I1/I2 areas, no coverage)

`uv run pytest tests/mutations/test_sets.py tests/filters/test_sets.py --no-cov`
→ **141 passed**. Confirms the I1 message-pinning families and the I2
`test_sets.py` / `filters/test_sets.py` fixture fixes are green in this pass
(independent of Worker 3's full-tree 1996/0). Did NOT run the full suite — that is
the final test-run gate's job.

### Deferred follow-ups

Catalog for the final gate's `bld-final.md` deferred-work catalog / the next spec
author / the maintainer. None of these is 038-contract work; none was routed to the
(now-closed) consolidation loop.

- **(a) `docs/TREE.md` stale `mutations/` line.** Both current-on-disk and target
  layouts still render `mutations/` as `# planned by TODO-ALPHA-036-0.0.11` despite
  `mutations/` shipping in `0.0.11` (`DONE-036`). **spec-036 doc debt, out of
  spec-038's contract** — Worker 1 edits only the active spec, not source TREE here.
  (Flagged independently in Slices 5a + 5b.) Maintainer / next-author follow-up.
- **(b) DONE-038 card-body free-text `Status: "In progress"`.** The rendered
  DONE-038 card body shows `Status: In progress` (vs sibling DONE-037's
  `Status: Shipped`). It was already `In progress` at HEAD (pre-existing free-text,
  independent of the workflow `status.key=done`, which is correct); outside Slice-5b's
  named scope. Cosmetic. A one-line DB-backed `CardItem.text → "Shipped"` edit +
  re-render if the maintainer wants the DONE-card convention nicety. NOT a defect.
- **(c) Slice-1 Low: `_model_less_relation_annotation` `queryset=None` → raw
  `AttributeError`.** A plain-`Form` `ModelChoiceField` declared with no `queryset`
  raises a raw `AttributeError` instead of a `ConfigurationError`. Out-of-spec
  unusable input shape; reviewed-and-accepted as a Low at Slice 1. Robustness nicety
  for a future slice/card; not a cross-slice duplication, so not part of the I1 loop.
- **(d) Spec self-reference path discrepancy (`docs/spec-038-...` vs
  `docs/SPECS/spec-038-...`).** Build-plan flag; the live spec is the `docs/SPECS/`
  one. Largely reconciled in Slice 1 (Worker-1 fixed 4 `docs/` → `docs/SPECS/`
  self-refs per worker-1 memory). Residual: any remaining cosmetic spec-internal
  self-reference in Decision 1 / DoD item 1 may be reconciled in a future
  spec-touching pass or left to the next-author archive sweep (`docs/SPECS/NEXT.md`
  Step 8). Not a build defect.
- **(e) Direct `tests/utils/`-tier pin for `normalize_field_name_sequence`.**
  Worker 3's non-blocking suggestion. The shared helper has no own-home test
  (`tests/utils/test_inputs.py` has no reference); both flavors' messages ARE pinned
  through the delegations (`tests/mutations/test_sets.py` + `tests/forms/test_inputs.py`).
  Acceptable as-is. Before the `0.0.13` serializer card adds a third reader, a
  `tests/utils/test_inputs.py` case over both `flavor` strings + the bare-string +
  duplicate raises is the cleaner home-pin. Future-slice / next-card follow-up.
- **(f) I2 root-cause lesson (for the retrospective).** A model-column add
  (`Item.attachment`, Slice 4) must sweep package-test fixtures: any test hardcoding
  the model's editable-column set — as an expected list, a `fields=`/`exclude=`
  narrowing, or an `"__all__"` sweep — goes stale when a column lands. The package
  `tests/` tree was last fully run pre-Slice-4, so five fixtures (two dedup, two
  editable-field, one filter `__all__`) were uncaught until the I2 sweep. Lesson:
  pair every model-column add with a cross-tree fixture grep
  (`grep -rn <column-name>` across all three test trees) in the same slice.

### Build readiness

The integration pass is **`final-accepted`**: I1 + I2 resolved on disk, staged-anchor
sweep clean in shipped source, dependency direction one-way, exports correct, no
remaining cross-slice duplication. The build is **ready for the final test-run gate**
(`bld-final.md`): the full `uv run pytest --no-cov` sweep across all three trees +
`manage.py check` + `makemigrations --check` + the lint/format/diff gate. Note for
that gate: the example/live trees (`examples/fakeshop/test_query/`) were NOT run by
the I1/I2 loop or this pass — Slice 4 authored its own example surface against the new
`attachment` column, so no specific example-tree staleness is flagged, but the final
gate owns confirming the example + live trees.

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
