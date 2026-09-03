# Package build plan: form_mutations / 0.0.12 (038)

Spec source: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (ARCHIVED — the spec shipped in `0.0.12` and was moved to `docs/SPECS/` by a later spec's NEXT.md Step 8 sweep; it is the cycle's contract in place)
Target release: `0.0.12` (shipped; the on-disk package is `0.0.15`)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential slices. Re-declared per slice if a code gap sends a builder in.
Hot-path declaration: none. No slice in this cycle adds runtime cost — the cycle's writable surface is the spec, its new rationale companion, and (only if a conformance gap is proven) package `.py` source.
Floor-verification scope: none by default. No slice is planned to change a Django / Strawberry integration seam; if Slice 1 proves a code gap and a builder lands source, Worker 1 re-declares the scope in that slice's artifact before the final gate.
Pre-flight: passed with recorded deviations on 2026-09-02 (see `## Pre-flight record`).

> **Cycle artifacts retired.** The five per-round `bld-038-*.md` artifacts this plan names were
> deleted when the cycle closed; only this plan and the final report
> `docs/builder/bld-038-final.md` survive on disk. All five read `Status: final-accepted` before
> deletion and every one is recoverable in full from the cycle's commit:
> `git show cce37373:<path>`. Treat every retired `bld-038-*.md` path below as
> **commit-resolvable rather than disk-resolvable** -- they are retired records, not dead links.
> The retired five are `bld-038-slice-0-rationale_extraction.md`,
> `bld-038-slice-1-code_conformance.md`, `bld-038-slice-2-spec_reconciliation.md`,
> `bld-038-integration.md` and `bld-038-review-1-citation_residue.md`. The
> cycle-scoped worker-memory files are git-ignored scratch and were not preserved.

## Cycle shape: a residual-reconciliation cycle, not a feature build

`spec-038` is **shipped**. Its five slices were built and final-accepted at `0.0.12`. This
cycle discharges the two obligations that were never closed:

1. The spec has a `…-terms.csv` companion at
   `docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv` but **no `…-rationale.md`
   sibling**. `docs/builder/BUILD.md` `## Spec rationale extraction` makes that file the first
   substantive action of every build; `spec-038` predates the rule's enforcement. Slice 0
   closes the gap, matching the shape of the `034` / `035` / `036` / `037` companions.
2. Nobody has checked the shipped spec against `HEAD`. The `0.0.13`–`0.0.15` cards
   (`039` serializer mutations, `040` auth mutations, and the `0.0.15` DRY / extraction
   cards) refactored the exact seams `spec-038` landed — the pipeline helpers it promoted,
   the converter dispatch it built, the reverse-map record it introduced, and the
   `registry.clear()` co-clear wiring it named. None of them edited the spec. The spec is
   therefore a false description of the code in at least the helper-location and
   co-clear-mechanism claims, and possibly elsewhere.

The cycle's question is the maintainer's, stated as three tests every finding is graded
against:

- **Was anything in the spec never built?** A Decision, a Slice-checklist sub-check, or a
  Definition-of-done item with no counterpart in `django_strawberry_framework/` is a
  **dropped feature** and the code is what changes.
- **Did the code deviate from the spec at ship time?** The spec is the contract; a divergence
  the build introduced is graded on which one is right, and the losing side changes.
- **Did a later card change the contract deliberately?** Then the code stands and the **spec
  is rewritten to state the shipped contract directly** — no amendment block, no "as of
  spec-053" hedge (`docs/builder/BUILD.md` `## Spec rationale extraction`: the spec is a
  contract, not a changelog). *What* changed, *why*, and *what it replaced* land in the
  rationale companion as a `**Post-ship:**` bullet under the owning Decision.

**Scope fence (maintainer-set, this cycle only).** The writable surface is **spec files and
package `.py` source**. No closeout-agentflow edits: `docs/GLOSSARY.md`, `KANBAN.md`,
`KANBAN.html`, `docs/TREE.md`, `CHANGELOG.md`, `TODAY.md`, `README.md`, `GOAL.md`, the kanban
DB and `docs/builder/BUILD.md` / `worker-*.md` are **out of scope** and no worker touches them.
No closeout retrospective runs. Every artifact this cycle creates carries `038` in its
filename.

## Pre-flight record

Run 2026-09-02 against `docs/builder/worker-0.md` `## Pre-flight procedure`.

| Step | Result |
| --- | --- |
| 1. Working-tree baseline explicit | **Deviation recorded, not resolved.** 116 paths dirty at start, none this cycle's; the maintainer's dispatch instruction is to ignore concurrent work. See `## Baseline-dirty out-of-scope files`. |
| 2. `scripts/review_inspect.py` runs | Pass. `uv run python scripts/review_inspect.py django_strawberry_framework/forms/converter.py --output-dir docs/shadow --stdout` exit 0, overview emitted. |
| 3. Build artifacts reset | **Deviation.** No `build-038-*` / `bld-038-*` path exists (all six verified free before creation). `docs/builder/bld-003-final.md` is a **committed** artifact of the `spec-003` residual cycle and was **left in place** — deleting a committed record of another cycle is the one irreversible pre-flight mistake the step warns about, and the maintainer's fence bars non-spec / non-`.py` edits anyway. |
| 4. `.gitignore` lists the scratch paths | Pass. `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/` all listed. |
| 5. Scratch directories cleared | Pass. All three emptied; `docs/builder/worker-memory/worker-0.md` … `worker-3.md` seeded empty. |
| 6. Spec-doc consistency check | Pass. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md` → `OK: 31 terms - all have glossary entries and at least one spec link.` |
| 7. Spec rationale extracted | **Open — this is Slice 0.** The whole reason the cycle exists. No later slice dispatches until Slice 0 is `final-accepted`. |

## Baseline-dirty out-of-scope files

116 paths were already modified or untracked when this cycle began, from a concurrent session
(the shape — hardening guards and typed-boundary wraps across `django_strawberry_framework/`
plus matching `tests/` additions — reads as a bug-hunt / hardening pass). **No worker edits or
reverts any of them**, and no worker treats their churn as this cycle's output.

**Three of them are files this cycle reads for conformance.** `forms/inputs.py`,
`forms/resolvers.py` and `forms/sets.py` each carry uncommitted hunks:

- `forms/inputs.py` — a `keyword.iskeyword` / `str.isidentifier` guard on the field-name
  basis, a guarded `base_fields` read, and two out-of-vocabulary `operation_kind` raises.
- `forms/resolvers.py` — the multi-relation container check lifted to
  `utils/write_values.py::materialize_relation_id_container`.
- `forms/sets.py` — a typed wrap around the `get_form_fields` hook invocation.

**Consequence for conformance grading.** Every conformance claim about those three files is
stated against `git show HEAD:<path>` into a scratch path **outside** the repo, with the
command quoted (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on
prose`). The **landed contract is HEAD**, not the working copy: an uncommitted guard is not a
shipped contract and must not be written into the spec as one. Where a working-tree hunk would
change a spec statement, Slice 2 records it in the deferred-work catalog instead of adopting
it. `forms/converter.py`, `forms/__init__.py`, `mutations/fields.py` (dirty),
`mutations/sets.py` (dirty), `mutations/inputs.py` (dirty), `types/base.py` (clean),
`types/finalizer.py` (dirty), `registry.py` (clean), `utils/inputs.py` (dirty),
`utils/converters.py` (dirty), `utils/errors.py` (dirty), `utils/write_values.py` (dirty) —
grade each against `HEAD` unless it is clean.

The list is dated and the population will grow while this cycle runs. The fence covers whatever
the concurrent session owns at the moment a worker reads it, not a frozen list.

## Worker-0 verification pass (findings carried into dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`
— every finding below was read out of source before this plan was written, so no worker
re-derives it. Each is a **verified observation**, not an instruction: the grading is Worker 1's.

**Built and conformant (no code change owed).**

- **D4 (module layout).** `django_strawberry_framework/forms/` ships exactly the four named
  modules plus `__init__.py`: `converter.py`, `inputs.py`, `sets.py`, `resolvers.py`.
  `tests/forms/` mirrors them with `test_converter.py` / `test_inputs.py` / `test_sets.py` /
  `test_resolvers.py`.
- **D5 (public surface).** `django_strawberry_framework/__init__.py` imports both bases from
  `.forms` and lists `"DjangoFormMutation"` / `"DjangoModelFormMutation"` in `__all__`;
  `tests/base/test_init.py` pins both in the `__all__` surface assertion and asserts the root
  export is the same object as the submodule export.
- **D5 axis 1 + 3 (target check, `data:` ref).** `mutations/fields.py::_has_mutation_protocol`
  is the duck-typed family check — `_mutation_meta` plus callable `resolve_sync` /
  `resolve_async` / `input_type_name` and a non-`None` `input_module_path` — with no
  `issubclass(DjangoMutation)` and no form-base import.
  `mutations/fields.py::_synthesized_mutation_signature` consults
  `mutation_cls.input_type_name(meta)` + `mutation_cls.input_module_path`, and the transient
  `fields.py::_input_type_name` twin is gone (no `def _input_type_name` anywhere in the
  package).
- **D5 axis 2 (resolver dispatch).** `mutations/fields.py` `_resolve` calls
  `mutation_cls.resolve_async` / `mutation_cls.resolve_sync`, not the hardcoded
  `mutations/resolvers.py` import.
- **D7 (converter fail-loud dispatch).** `forms/converter.py::convert_form_field` registers
  each supported class individually in `_SCALAR_FORM_FIELDS`, resolves by
  `type(field).__mro__` walk, handles `type(field) is forms.Field` → `str` as an explicit
  exact-type precheck returning `MRO_CONTINUE` for subclasses
  (`forms/converter.py::_bare_form_field`), registers **no** base-`forms.Field` catch-all, and
  raises `ConfigurationError` from `forms/converter.py::_unsupported_form_field` on the
  fallthrough. The relation / file / multi-choice `isinstance` prechecks run before the scalar
  walk exactly as the Decision requires.
- **D7 (`to_field_name`).** `forms/resolvers.py::_to_form_key_value` reads the form field's
  `to_field_name` and returns `obj.serializable_value(to_field_name)`, else `obj.pk`.
- **D7 / D8 (raw-pk relation visibility).** `tests/forms/test_resolvers.py` carries
  `test_relation_visibility_raw_pk_single_hidden_rejected` and
  `test_relation_visibility_raw_pk_multi_hidden_rejected` — the non-Relay branch the `036`
  helper left unscoped is pinned on both cardinalities.
- **D10 / D13 (`operation` split, bind wiring).** `forms/sets.py` instantiates
  `_form_mutation_declaration_registry = make_declaration_registry("DjangoFormMutation")`,
  exposes `clear_form_mutation_registry`, defines `bind_form_mutations()`, and
  `types/finalizer.py` imports and calls `bind_form_mutations()` in the phase-2.5 window.
  `make_declaration_registry` is single-sited and instantiated by `mutations/sets.py`,
  `forms/sets.py` and `auth/mutations.py` — the shared-mechanics-disjoint-ledgers shape
  Decision 13 prescribed, now with a third consumer the spec could not have named.
- **D13 (model-less payload from one builder).** `mutations/inputs.py::build_payload_type`
  takes `object_type: type | None` and its docstring cites `spec-036 Decision 7 / spec-038
  Decision 6` — one builder, one ledger, the model branch preserved.
- **D13 (no `DjangoType` `Meta` key).** `types/base.py` carries zero occurrences of
  `form_class`; `DEFERRED_META_KEYS` is unchanged and its own comment states so.
- **D6 (`Meta.return_field_name` not adopted).** Zero occurrences of `return_field_name`
  anywhere in `django_strawberry_framework/`.
- **D12 / DoD 5 (live surface).** `examples/fakeshop/apps/products/forms.py` ships
  `ItemModelForm` (with `clean_name`), `ContactForm`, `PingForm`, `StampedItemModelForm`
  (kwarg-requiring, for the `get_form_kwargs` case) and `ItemFileModelForm` (the file column);
  `products/schema.py` exposes six form mutations. `test_products_api.py` carries the whole
  DoD-5 row set as named tests: happy paths, `categoryId`-through-form, partial-update
  preservation, the unique-constraint `"__all__"` envelope, `clean_<field>` field-keying,
  anonymous + missing-perm denial, the visibility-scoped update, the hidden-`Category`
  field-keyed `FieldError`, a raw multipart upload over HTTP, the `get_form_kwargs`
  user-injection case, and the plain-form success / validation-failure / denied-by-default
  shapes.
- **D14 (version cut).** The `0.0.12` cut happened; the package is now `0.0.15`. A
  shipped-version statement about the release this card closed is **not** stale and no worker
  "updates" it to `0.0.15`.
- **Staged anchors discharged.** `grep -rn 'TODO(spec-038'` over source and tests returns
  nothing; the only hits are in `docs/dry/dry-0_0_12.md` (a closed cycle's scratchpad,
  describing the anchors' removal) and the spec's own prose describing the anchor discipline.

**Deviations from the spec, verified at source, for Worker 1 to grade.**

- **D-1 — the promoted pipeline helpers no longer all live where Decision 8 says.** Decision 8's
  "Helper reuse" paragraph names nine helpers promoted "underscore-dropped in place" in
  `mutations/resolvers.py`. Three have since moved:
  `validation_error_to_field_errors` → `utils/errors.py`, `raw_choice_value` →
  `utils/write_values.py`, `payload_object_slot` → `mutations/inputs.py`. Six remain in
  `mutations/resolvers.py` (`locate_instance`, `coerce_lookup_id`, `authorize_or_raise`,
  `refetch_optimized`, `build_payload`, `not_found_error`, `save_or_field_errors`). Third
  grading case (a later card's deliberate consolidation) — code stands, spec rewritten.
- **D-2 — the form pipeline is no longer a per-flavor body calling helpers by name.**
  `forms/resolvers.py` imports `make_resolver_entries` and `run_write_pipeline_sync` from
  `mutations/resolvers.py` plus `pipeline_write_phase` from `utils/write_transaction.py`, i.e.
  the seven-step sequence Decision 8 enumerates is now a **shared pipeline runner** the form
  flavor parameterizes rather than a form-local body. Decision 8's step list still describes
  the observable contract correctly; its implementation prose ("the form pipeline **calls** the
  shipped `036` pipeline helpers by name") describes a shape that no longer exists.
- **D-3 — the decode primitives moved to `utils/write_values.py`.** `forms/resolvers.py`
  imports `decode_field_handlers`, `decode_provided_fields`, `decode_visible_relation` and
  `materialize_relation_id_container` from `utils/write_values.py`. Decision 7 / Decision 8
  describe a decoder `forms/resolvers.py` "runs its **own**" over `036` primitives; the
  visibility-on-every-branch contract is intact, but the code is a shared substrate the
  serializer flavor also uses.
- **D-4 — the reverse-map record is single-sited on `utils/inputs.py::InputFieldSpec`.**
  Decision 7 says `forms/inputs.py` "retains, per generated input field, an `(input_attr,
  graphql_name) → (form_field_name, kind)` metadata record"; `forms/converter.py`'s docstring
  now states the record type is `utils/inputs.py::InputFieldSpec` (`target_name` = form field
  name) and that this module owns only the kind constants. The four kind constants
  `SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE` are defined in `utils/inputs.py`
  and re-exported by `forms/converter.py`.
- **D-5 — the converter rides a shared dispatch skeleton.** `forms/converter.py` builds its
  dispatch from `utils/converters.py`'s `convert_with_mro` / `finish_field_conversion` /
  `make_scalar_converter` / `make_kind_converter` / `MRO_CONTINUE`, and its conversion record
  subclasses `utils/inputs.py::FieldConversionBase`. The spec describes a self-contained
  registry.
- **D-6 — `registry.clear()` no longer carries three hard-coded form rows.** Decision 13 states
  "**`registry.clear()` co-clears THREE form rows**" and the Implementation-plan table names
  `registry.py` as the file that gains them. `registry.py` contains zero `clear_form`
  occurrences: the three clears are now **announced by their owning module** via
  `register_subsystem_clear(...)` and consumed by `registry.clear()`'s
  `for clear in iter_subsystem_clears()` loop. The three clears exist and are all registered
  (`forms/inputs.py::clear_form_input_namespace`, `forms/sets.py`'s
  `clear_form_mutation_registry` under owner `"forms.declarations"`, and
  `clear_form_shape_build_cache` under owner `"forms.shape_cache"`); the mechanism changed, not
  the contract.
- **D-7 — the converter table carries a row the spec's enumeration omits.**
  `_SCALAR_FORM_FIELDS` includes `forms.JSONField` → `strawberry.scalars.JSON`, with a comment
  explaining that without the explicit row the `CharField` parent would type JSON payloads as
  `String`. Decision 7's bullet list and DoD item 2 enumerate the supported classes and name no
  `JSONField`. Whether this is a later addition or an unrecorded ship-time inclusion is
  Worker 1's to establish from history.
- **D-8 — `NullBooleanField` requiredness is a three-case rule the spec states as one.**
  Decision 7 lists `NullBooleanField → bool | None`. The shipped
  `forms/converter.py::form_field_required` is the single requiredness decision across the
  column-backed and column-less paths: an exact `NullBooleanField` is forced optional, a
  **subclass** keeps its declared requiredness (and so gets a non-null `bool`), and a
  **non-null-column-backed** field keeps `required=True`. The spec's one-line mapping is true
  of the common case and silent on the other two.
- **D-9 — Decision 8 narrates its own history in the spec body.** Decision 8 opens with
  "**Ordering correction — authorize runs BEFORE the relation decode (post-ship security
  fix).**", says "The step numbers below reflect the original draft sequence", and then leaves
  the seven numbered steps in the superseded order. `docs/builder/BUILD.md` `## Spec rationale
  extraction` forbids exactly that shape: the Decision states the current contract directly
  and the supersession narrative moves to the rationale companion. The steps must be
  renumbered into the shipped order (locate → authorize → decode → construct/validate → write
  → re-fetch → return), and every cross-reference to a step number swept.
- **D-10 — the deliberative layer has never been extracted.** Fourteen `Justification:` blocks,
  fourteen `Alternatives considered (and rejected):` blocks, a `## Risks and open questions`
  body written as preferred-answer/fallback pairs (most entries already carrying a
  `RESOLVED` marker that belongs in the companion), the "Rejected (recorded, not silently
  dropped)" paragraph inside Decision 6, and an inline `Revision history (kept inline so the
  spec is self-contained):` block are all still in the spec. Slice 0 moves them; the counts
  here are Worker 0's grep and Worker 1 re-measures.
- **D-11 — the live surface is wider than Decision 12 and DoD 5 describe.** Both name products
  as the live home. Two more example apps now expose form mutations against this card's bases:
  `examples/fakeshop/apps/library/` (`ShelfRelationsForm`, `BookGenresModelForm`,
  `BranchWithShelfForm`, `BranchPairForm`; four mutations incl. two plain-form
  `perform_mutate` overrides) and `examples/fakeshop/apps/scalars/`
  (`MediaSpecimenImageForm`, one `DjangoModelFormMutation`). Decision 12's narrowing to
  products was faithful when written; as a standing description of the live surface it is now
  incomplete.
- **D-12 — DoD 5's live write-time `IntegrityError` row is pinned in `test_library_api.py`, not
  `test_products_api.py`.** The package tier pins both halves
  (`tests/forms/test_resolvers.py` — the `form.save()` race and the plain-form
  `perform_mutate` race). The live row named in DoD item 5 has no `IntegrityError` test inside
  `test_products_api.py`'s form block; the live coverage sits in `test_library_api.py`.
  Worker 1 grades whether that is a relocated row (spec updated) or an unpinned live contract
  (a test owed).

**Net-new landed boundaries the spec never names — verified present at `HEAD`.** Each was
confirmed against `git show HEAD:django_strawberry_framework/forms/<file>` written to a
scratch path outside the repo, so none is the concurrent session's uncommitted work. These are
the "implemented later, or to optimize for later features" class: the code stands and the spec
gains the contract.

- **D-13 — the partial side has a required-column-less-field guard the spec says does not
  exist.** `forms/inputs.py::guard_partial_required_column_less_fields` rejects an `update`
  narrowing that drops a **required column-less** form field, because
  `model_to_dict` cannot reconstruct it from the row. Decision 7's create-guard paragraph
  states "`update` is exempt", and the `## Edge cases` create-narrowing bullet repeats it.
  Both are false at `HEAD`: there are **two** narrowing guards, keyed on the same
  waiver (`forms/sets.py::_form_kwargs_overridden`).
- **D-14 — an input-attribute collision guard.** `forms/inputs.py::_guard_input_attr_collisions`
  raises `ConfigurationError` when two form fields' generated input attributes collide — a
  form declaring both `category` (a `ModelChoiceField`, which emits `category_id`) and a
  literal `category_id` field. The spec's collision discipline covers only two *generated
  input class names* colliding; a within-one-input attribute collision is unmentioned.
- **D-15 — a plain-`Form` relation field whose `queryset` is `None` at class definition is
  rejected.** `forms/inputs.py::_model_less_relation_annotation` raises naming the form and
  field, because schema-time discovery reads `base_fields` without instantiating, so a
  queryset assigned in `__init__` is invisible. Decision 7 states the model-less relation
  basis is `field.queryset.model` and is silent on the `None` case.
- **D-16 — the plain-form allowed-key set is narrower than the spec's one rule.** The Slice-2
  checklist gives one sentence for both flavors ("adds `form_class` and drops `model` /
  `input_class` / `partial_input_class`"). At `HEAD` there are two sets:
  `forms/sets.py::_ALLOWED_MODELFORM_META_KEYS` = `MODEL_BACKED_WRITE_META_KEYS | {form_class}`
  = `{fields, exclude, permission_classes, operation, select_for_update, form_class}`, and
  `forms/sets.py::_ALLOWED_PLAIN_FORM_META_KEYS` = `COMMON_WRITE_META_KEYS | {form_class}` =
  `{fields, exclude, permission_classes, form_class}` — the plain flavor additionally drops
  `operation` (Decision 10, correctly) **and** `select_for_update`. `select_for_update` is a
  post-`038` row-locking key the spec cannot mention; that the `ModelForm` flavor accepts it
  and the plain flavor rejects it is a landed contract with no spec statement.
- **D-17 — the plain base rejects a `DjangoModelPermission` entry in `Meta.permission_classes`.**
  `forms/sets.py::DjangoFormMutation._validate_meta` raises when an entry is a
  `DjangoModelPermission` subclass, since a model-less mutation cannot resolve the write
  permission. Decision 11 settles the plain-form *default* (an unset `permission_classes`
  denies — confirmed at `HEAD` as `_validate_permission_classes(..., unset_default=(DenyAll,))`)
  but says nothing about an explicitly-set model-permission class.
- **D-18 — the runtime input-shape cache key is a 4-tuple, not the spec's 3-tuple.**
  Decision 7 pins the identity `(form_class, operation kind, frozenset(effective field
  names))`. `forms/sets.py::_cached_build_form_input` keys on that plus a fourth element,
  `forms/sets.py::_form_input_hook_identity(mutation_cls)` — `None` unless the mutation
  overrides `get_form_fields`, in which case two mutations over one form with different
  overrides must not dedupe to one input. The conceptual identity is unchanged; the shipped
  key has a component the spec's tuple omits.
- **D-19 — the plain-form metaclass, registry bind, and resolver seams are all shared
  factories.** Decision 6 says the plain form has "its own metaclass"; at `HEAD` it is
  `make_meta_validating_metaclass(register_form_mutation, …)` from `mutations/sets.py`.
  `bind_form_mutations()`'s whole body is one `bind_write_declarations(...)` call, and both
  flavors' `resolve_sync` / `resolve_async` come from a `resolver_seams(...)` factory
  (`with_id=False` for the plain flavor, matching the `mutations/fields.py`
  `operation != "form"` id-gate). A `mutations/operations.py` module now owns the canonical
  operation vocabulary (`NON_DELETE_WRITE_OPERATIONS`,
  `NON_DELETE_OPERATION_INPUT_KIND`, `non_delete_operation_error`) the spec spells inline.

**Working-tree-only, NOT to be written into the spec.** Verified absent at `HEAD` and present
only in the concurrent session's uncommitted hunks. Slice 2 records these in the deferred-work
catalog and adopts none of them:

- `forms/inputs.py` — the `str.isidentifier` / `keyword.iskeyword` field-name guard; the
  guarded `dict(form_class.base_fields)` read; the two out-of-vocabulary `operation_kind`
  raises in `build_form_input_class` / `build_form_inputs`.
- `forms/sets.py` — the typed `BaseException` wrap around the `get_form_fields` hook
  invocation in `_mutation_form_fields`.
- `forms/resolvers.py` — the multi-relation container check lifted to
  `utils/write_values.py::materialize_relation_id_container`.

**Not a finding.** `__version__` is `0.0.15`, three patch releases past this card's `0.0.12`
target, and `tests/base/test_init.py` pins `0.0.15`. Decision 14 and DoD items 7–8 describe a
cut that **happened**.

## Contract-level escalations

`docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions
before dispatch`. Three questions in this cycle turn on which contract the package should
offer rather than on a defect. All three were settled by the maintainer's own framing of the
task:

- **Does a later card's deliberate change make the code wrong, or the spec stale?** Settled:
  the spec is updated to match, and the explanation goes to the rationale companion, never into
  the spec. Rejected alternative: leave the spec as the historical `0.0.12` record and let the
  glossary carry the current shape — rejected because a spec that describes a helper layout the
  code has not had since `0.0.15` is read as a contract and mis-teaches every future reader.
- **May this cycle change package source?** Settled: yes, but only to close a **proven** gap
  between the spec and the code — a feature planned and never built, or built wrong. Rejected
  alternative: treat the cycle as spec-only and route every code finding to a follow-up card —
  rejected because a dropped feature is exactly what the cycle exists to find.
- **Is the concurrent session's uncommitted hardening of `forms/` part of the landed
  contract?** Settled: **no.** The maintainer's instruction is to ignore concurrent work, and
  `AGENTS.md` rule 34 bars editing or reverting it. The spec is reconciled against `HEAD`;
  a working-tree-only guard is recorded in the deferred-work catalog, never written into the
  spec as a shipped contract. Rejected alternative: reconcile against the working tree so the
  spec matches the tree at commit time — rejected because the hunks may be revised or dropped
  before their own cycle commits, which would leave the spec describing a contract that never
  shipped.

### Escalation raised by Slice 1 and settled at dispatch (GAP-3)

`docs/builder/bld-038-slice-1-code_conformance.md` `#### GAP-3` escalates one contract choice:
DoD item 5 and the `## Test plan` live bullet both name a **write-time `IntegrityError` for the
`ModelForm` flavor, proven live**. That row was never built — not at ship time, not since. The
only `ModelForm` coverage is a package row reaching the path by
`mock.patch.object(forms.ModelForm, "save", side_effect=IntegrityError)`; the live coverage that
exists is the **plain-form** `perform_mutate` path in `test_library_api.py`. The question is
whether the package's contract is "the envelope holds at write time, proven live once per
flavor" or "proven live for the `ModelForm` flavor specifically".

**Settled: build the test.** The maintainer was not reachable at dispatch, and three standing
authorities decide it without a new contract choice being made:

- The cycle's own charter is to find what was planned and never built. A DoD item naming a live
  row, with no live row, is that finding — deciding it away would make the cycle worthless.
- `AGENTS.md` rule 10 makes the live `/graphql/` tier mandatory for any line a real request
  reaches, and permits a mock "only when the real path is impossible". Slice 1 proved the real
  path is **possible** — narrowing `Meta.fields` past a unique-constraint co-member and
  injecting it through `get_form_kwargs` drives a genuine post-validation `IntegrityError` — so
  the existing mock is not licensed by that exception.
- `AGENTS.md` rule 5 bars defer-the-real-fix sequencing and follow-up cards as substitutes.

**Rejected alternative:** build no test and have Slice 2 rewrite DoD 5 and the Test-plan bullet
to cite the existing plain-form library live row plus the mocked package row. Rejected because
it weakens a written contract to match the coverage that happens to exist, and because the
`ModelForm` `form.save()` wrap and the plain-form `perform_mutate` wrap are two distinct call
sites in `forms/resolvers.py` — a live row over one does not exercise the other.

The decision is **reversible**: it adds test rows and example-app surface, no package behavior.
If the maintainer prefers the narrower contract, Slice 2 rewrites the two homes and the rows
come back out.

## Review round 1 — citation residue (Worker-0 dispatched, 2026-09-02)

Input: the integration pass's own finding, not a maintainer review document.
`docs/builder/BUILD.md` `## Review rounds` governs. The fence holds unchanged (spec files and
`.py` source only; every created filename carries `038`).

### The finding, verified by Worker 0 before dispatch

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`.

Slice 2 removed spec-038's `P1` / `P2` / `P3` labels — the spec now carries **0**, down from
**88** at `HEAD` (`git show HEAD:docs/SPECS/spec-038-form_mutations-0_0_12.md | grep -oE '\bP[123]\b' | wc -l`).
Package source still cites them. **11 lines across 4 package files** name the label explicitly
as `spec-038 Decision 7 P<N>`:

| File | Lines carrying an explicit `spec-038 … P<N>` citation |
| --- | --- |
| `django_strawberry_framework/forms/converter.py` | 2 |
| `django_strawberry_framework/forms/inputs.py` | 5 |
| `django_strawberry_framework/forms/sets.py` | 3 |
| `django_strawberry_framework/mutations/sets.py` | 1 |

That is a **false citation in shipped source**: a reader following it finds no such label.
`AGENTS.md` rule 27 states the rule it breaks directly — cite a contract by **content**, never
by ordinal, because a heading or label rewrite strands every ordinal.

**The population is wider and subtler than 11, which is why this is Worker 1's to scope rather
than a mechanical sweep.** A repo-wide count finds **41** P-label lines in package source
(measured over 111 package `.py` files). They belong to at least three different label
vocabularies:

- **spec-038's, explicitly qualified** — the 11 above.
- **spec-038's, unqualified** — bare `P1` / `P2` in `forms/` bodies with no spec named, e.g.
  `forms/sets.py #"the P1 reverse map"`, `forms/inputs.py #"the kwarg-requiring-form fix"`,
  `forms/resolvers.py #"the prior P1 fix"`. Same defect, invisible to a `spec-038` grep.
- **not spec-038's, and not this cycle's** — spec-039's live vocabulary (`P1.5`, `P2.2`, `P2.7`,
  `P1.7`) in `rest_framework/` and `utils/`, and spec-030's `P1-B` in `orders/sets.py`. Some sit
  in the **same files** as spec-038's, including `forms/inputs.py`, which carries both.

### Contract-level question, settled before dispatch

**Which side is wrong — Slice 2 for stripping the labels, or the source for citing them?**
Settled: **the source.** Slice 2 stands.

The evidence is the repo's own direction of travel. Every spec whose residual cycle has already
run carries **zero** P-labels (`spec-030`: 0, `spec-036`: 0, `spec-037`: 0), while `spec-039`,
whose cycle has not run, still carries **113**. Slice 2 followed the established precedent, and
its brief authorized exactly that judgement. Restoring 88 labels to spec-038 would make it the
only completed spec carrying them.

**Rejected alternative:** restore the P-labels in the spec, a one-file edit against ~20 source
comments. Rejected because it reverses the precedent three prior cycles set and re-introduces
into a standing document the review-residue vocabulary `START.md` "Style Rio cares about" bars,
to preserve citations that `AGENTS.md` rule 27 says should never have been ordinals.

**Known and deliberately out of scope:** `orders/sets.py` cites `spec-030 … P1-B` twice against
a spec now carrying zero P-labels — the identical defect, left by that cycle. It is **not**
this round's, and neither is spec-039's live vocabulary. Round 1 fixes spec-038's citations
only; the `spec-030` pair goes to the deferred catalog so the class is recorded rather than
silently half-fixed.

## Artifact list

- `docs/builder/bld-038-slice-0-rationale_extraction.md`
- `docs/builder/bld-038-slice-1-code_conformance.md`
- `docs/builder/bld-038-slice-2-spec_reconciliation.md`
- `docs/builder/bld-038-integration.md`
- `docs/builder/bld-038-review-1-citation_residue.md`
- `docs/builder/bld-038-final.md`

## Checklist

- [x] Slice 0: extract the deliberative layer into `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` (pre-flight step 7; Worker 1 procedural pass, no source diff) -> `docs/builder/bld-038-slice-0-rationale_extraction.md`
- [x] Slice 1: code conformance — grade every Decision and Definition-of-done item against `HEAD` source and tests; dispatch Worker 2 / Worker 3 only if a real gap is proven -> `docs/builder/bld-038-slice-1-code_conformance.md`
- [x] Slice 2: spec reconciliation — rewrite every stale contract statement to the shipped shape, and record what changed and why as `**Post-ship:**` bullets in the rationale companion -> `docs/builder/bld-038-slice-2-spec_reconciliation.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-038-integration.md`
- [x] Review round 1: citation residue — the spec-038 ordinal citations Slice 2's rewrite falsified in package source -> `docs/builder/bld-038-review-1-citation_residue.md`
- [x] Final test-run gate -> `docs/builder/bld-038-final.md`
