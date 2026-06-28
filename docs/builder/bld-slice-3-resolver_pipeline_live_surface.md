# Build: Slice 3 — serializer resolver pipeline + products live serializer surface (one commit)

Spec reference: `docs/spec-039-serializer_mutations-0_0_13.md` (Slice checklist lines 874-1027; Decision 8 lines 2094-2367; Decision 9 lines 2369-2392; Decision 13 lines 2593-2652; Decision 5 lines 1615-1668; Decision 10 lines 2394-2447; Decision 11 lines 2449-2473; Cross-flavor reuse P1.1/P1.5/P2.4 lines 2697-2899; Test plan lines 3104-3294; DoD items 4-6 lines 3573-3640)
Status: final-accepted

## Plan (Worker 1)

This is the largest, most coverage-sensitive slice. It lands **one commit** containing
(a) `rest_framework/resolvers.py` (sync + async serializer pipeline), (b) the
`SerializerMutation.resolve_sync`/`resolve_async` overrides in `rest_framework/sets.py`
(the Slice-2 D8 carry-forward), (c) the P1.5/P1.1/P2.4 DRY promotions in
`mutations/resolvers.py` + `utils/querysets.py` (re-pointing `forms/resolvers.py`),
(d) the products live serializer surface (`serializers.py` + `schema.py` + settings),
and (e) the live + package-internal + field-factory + config-grep tests. The
live-first mandate (`examples/fakeshop/test_query/README.md` #"Coverage rule.")
governs: every consumer-reachable resolver line is earned by a real `/graphql/`
request, and `tests/rest_framework/test_resolvers.py` holds ONLY the genuinely
unreachable residue — with NO overlap.

### DRY analysis

The card's heaviest DRY contract. Per Worker-1 DRY-analysis shape:

**Existing patterns reused (cite source):**
- **By call from `mutations/resolvers.py`** (verified present — Import manifest line 2892):
  `locate_instance` (`mutations/resolvers.py::locate_instance`), `coerce_lookup_id`,
  `authorize_or_raise`, `refetch_optimized`, `build_payload`, `not_found_error`,
  `save_or_field_errors`, `payload_cls_for`, `run_pipeline_async`,
  `_coerce_relation_pk_or_none`, `raw_choice_value`, and the flat Django mapper
  `validation_error_to_field_errors` (for the save-time **Django** `ValidationError`
  branch). The Relay decode primitive `relay.py::decode_model_global_id` +
  `GlobalIDDecode` (the `forms/resolvers.py::_decode_form_relation_single`
  precedent) — these key off the target type's **recorded**
  `effective_globalid_strategy` and never touch `conf.settings` on the query path
  (verified: `decode_model_global_id` takes `expected_model`; `_resolve_globalid_strategy`
  in `types/relay.py` reads `conf.settings` ONLY at finalization).
- **By call from `utils/`** (Import manifest line 2892):
  `utils/querysets.py::visibility_scoped_related_queryset`, `apply_type_visibility_async`;
  `utils/permissions.py::request_from_info(info, family_label="SerializerMutation")`
  (already consumed by `rest_framework/sets.py::SerializerMutation.get_serializer` —
  the resolver re-routes construction through the existing `get_serializer_kwargs`
  hook so this stays single-sited).
- **Conceptual contracts reused:** the `FieldError` envelope + `NON_FIELD_ERROR_KEY`
  sentinel (`mutations/inputs.py:69`), the `<Name>Payload` `node`/`result` slot
  (`mutations/inputs.py::payload_object_slot` / `build_payload_type`), the
  `resolve_sync`/`resolve_async` seams (the form precedent `forms/sets.py:577-610`),
  the `DjangoModelPermission` write-auth seam (inherited unchanged from `036`).
- **The Slice-1/2 reverse map** (`SerializerMutation._input_field_specs`, a list of
  `utils/inputs.py::InputFieldSpec` with `input_attr`/`graphql_name`/`target_name`/
  `kind`/`source`, stashed at bind by `mutations/sets.py::build_and_stash_input`) is
  the decode key source — the serializer analog of the form decoder reading
  `mutation_cls._input_field_specs` (`forms/resolvers.py::_decode_form_data`).
- **The `038`-generalized `DjangoMutationField`** (`mutations/fields.py`) — NO edit;
  duck-typed `_has_mutation_protocol` already accepts `SerializerMutation`. Slice 3
  VERIFIES only (Decision 5).

**New helpers justified (net-new this slice):**
- **P1.5 — `run_write_pipeline_sync(...)` skeleton** (NET-NEW; promoted into
  `mutations/resolvers.py`). Staged TODO anchor present at `mutations/resolvers.py`
  #"Promote the create/update write orchestration into a shared
  `run_write_pipeline_sync(...)` skeleton" (lines ~112-126). Single responsibility:
  own atomicity, the create-vs-update branch, the `coerce_lookup_id → locate_instance →
  not_found_error` preamble, **authorization before `decode_step`** (the security
  invariant), and the `refetch_optimized → build_payload` tail — **scoped to
  model-backed create/update only** (F6). Each flavor supplies `decode_step(ctx) ->
  decoded | list[FieldError]` and `write_step(ctx, decoded) -> saved | list[FieldError]`.
  See "P1.5 promotion plan" below for the byte-equivalence obligation.
- **P1.1 — `visible_related_object(...)`** (NET-NEW; promoted from
  `forms/resolvers.py::_visible_related_object` into `utils/querysets.py`). Staged TODO
  anchors at `utils/querysets.py` #"Promote the object-returning related-visibility
  helper" (lines ~208-220) AND `forms/resolvers.py` #"Move `_visible_related_object`
  to `utils/querysets.py::visible_related_object`" (lines ~175-185). Single
  responsibility: resolve the VISIBLE related object by pk through the related primary's
  `get_queryset` (registry lookup → `visibility_scoped_related_queryset(...).filter(pk=).first()`),
  else default-manager fallback when no primary. Re-keyed by the serializer relation
  decoder; the form decoder re-points to it.
- **`serializer_errors_to_field_errors(...)`** (NET-NEW, recursive; in
  `rest_framework/resolvers.py`). Single responsibility: depth-first flatten DRF's
  nested `serializer.errors` / DRF `ValidationError.detail` into one `FieldError` per
  leaf with a dotted path, normalizing `NON_FIELD_ERRORS_KEY` → `"__all__"` at every
  level and re-keying each leaf ROOT segment back through the reverse map to the GraphQL
  input name. It is the recursive analog of the flat
  `mutations/resolvers.py::validation_error_to_field_errors` — both terminate in the
  same envelope; P2.4 ties them together (below).
- **The dedicated serializer relation decoder** (NET-NEW; in
  `rest_framework/resolvers.py`). Serializer-field-keyed (mirrors the `038` form
  decoder, NOT the model-attr-keyed `036` `_decode_relation_id_set`). Re-keys over the
  promoted `visible_related_object` (P1.1) — does NOT fork a third object-returning
  decoder.

**P1.5 promotion plan (the highest-value, highest-risk DRY move — a security invariant):**
- Extract from `mutations/resolvers.py::_run_pipeline_sync`/`_run_create`/`_run_update`
  the shared orchestration: `with transaction.atomic():` → (update) `coerce_lookup_id →
  locate_instance → not_found_error` → `authorize_or_raise(... instance=instance)` →
  `decode_step` → `write_step` → `refetch_optimized → build_payload`. The existing
  `_validate_save_assign_refetch_payload` tail is extended into the full preamble + tail.
- **`delete` (no data, no decode, snapshot-before-delete) and the model-less plain form
  (no instance, no primary type, no re-fetch) are EXCLUDED** (F6) — `_run_delete` keeps
  its own body, and `forms/resolvers.py::_run_plain_form_pipeline_sync` is NOT folded in.
- **Re-point three sites:** the model `_run_create`/`_run_update` (model `decode_step` =
  `_decode_relations` + setattr/construct; `write_step` = `full_clean` → `save` → M2M),
  `forms/resolvers.py::_run_modelform_pipeline_sync` (form `decode_step` =
  `_decode_form_data` + partial reconstruction; `write_step` = `get_form` →
  `is_valid` → `form.save`), and this slice's serializer body.
- **Byte-equivalence obligation (P1.5 / F6):** the existing model `DjangoMutation` and
  `DjangoModelFormMutation` suites must stay green UNCHANGED — that is the regression
  proof the promotion did not alter the model/form paths. Worker 1 final verification
  will token-diff the relocated orchestration vs `git show HEAD:` and confirm the
  authorize-before-decode ordering is byte-identical (per the worker-1 "relocated/
  promoted" rule). If `_run_modelform_pipeline_sync` cannot re-express as
  `decode_step`/`write_step` without behavior drift (e.g. the partial-reconstruction
  step's placement relative to authorize), Worker 2 surfaces it for spec reconciliation
  rather than forcing a leaky callback shape.

**P2.4 — share the error-flattener leaf primitive:**
- HARD reuse: `serializer_errors_to_field_errors` IMPORTS `mutations/inputs.py::NON_FIELD_ERROR_KEY`
  (no re-spelled `"__all__"`). DoD-checkable.
- PROMOTION (the optional-but-ideal half, with a staged anchor): promote a small
  `field_error(path, messages)` leaf ctor that BOTH the flat
  `validation_error_to_field_errors` and the recursive
  `serializer_errors_to_field_errors` call, so the sentinel + leaf construction cannot
  drift. Staged TODO anchor present at `mutations/resolvers.py` #"promote the
  `FieldError(field=..., messages=...)` leaf construction into a small shared helper"
  (lines ~799-810). The anchor's pseudo-flow (normalize empty path → sentinel; coerce
  message containers to a list; return one shared leaf) is the contract. **Worker 2
  must land this promotion** (the anchor is shipped source carrying this build's spec
  id, so per AGENTS.md it must be discharged in the slice that ships its work — leaving
  it would be an integration-pass finding). It edits `mutations/resolvers.py`
  (re-point `validation_error_to_field_errors`'s leaf construction) and is imported by
  the serializer flattener; the form flat-mapper stays reused-by-call.

**Duplication risk avoided:**
- The naive implementation would (i) hand-copy the `transaction.atomic()` +
  authorize-before-decode ordering a THIRD time, (ii) fork a third object-returning
  relation decoder, and (iii) re-spell the `"__all__"` sentinel + leaf construction. The
  plan prevents each via P1.5 / P1.1 / P2.4 respectively. The import manifest (spec line
  2892) is the DoD grep contract: `rest_framework/resolvers.py` imports the listed
  symbols and re-implements none.
- **Do NOT re-fork `request_from_info` context injection** — the resolver routes
  construction through the existing `SerializerMutation.get_serializer_kwargs` hook +
  the framework merge (Decision 8 step 4 / H3), reusing `request_from_info` exactly once
  at the `get_serializer` seam already shipped in Slice 2.

### Import manifest (the per-module DRY contract — DoD-checkable, spec line 2882-2899)

`rest_framework/resolvers.py` MAY import (and must not re-implement):
- `mutations/resolvers.py::{locate_instance, coerce_lookup_id, authorize_or_raise,
  refetch_optimized, build_payload, not_found_error, save_or_field_errors,
  payload_cls_for, run_pipeline_async, _coerce_relation_pk_or_none, raw_choice_value}`
  + `validation_error_to_field_errors` (the Django save-time branch) + the promoted
  `run_write_pipeline_sync` (P1.5) + the promoted leaf ctor (P2.4)
- the promoted `utils/querysets.py::visible_related_object` (P1.1) +
  `utils/querysets.py::{visibility_scoped_related_queryset, apply_type_visibility_async}`
- `utils/permissions.py::request_from_info` (consumed via the `get_serializer_kwargs`
  hook seam already shipped)
- the shared leaf-error sentinel `mutations/inputs.py::NON_FIELD_ERROR_KEY` (P2.4)
- `relay.py::{decode_model_global_id, GlobalIDDecode}` (recorded-strategy decode)
- `mutations/inputs.py::{FieldError, payload_object_slot}`,
  `rest_framework/serializer_converter.py::{SCALAR, RELATION_SINGLE, RELATION_MULTI, FILE}`
  (the `kind` constants the reverse-map specs carry)

**Cross-module (not `rest_framework/`):** P1.5 edits `mutations/resolvers.py` (+ re-points
`forms/resolvers.py`); P1.1 edits `utils/querysets.py` (+ re-points `forms/resolvers.py`);
P2.4 edits `mutations/resolvers.py` (the leaf ctor, imported by the serializer flattener).

### Implementation steps

Line numbers are pin-at-write-time hints; verify against current source before editing.

1. **P1.1 — promote `visible_related_object` to `utils/querysets.py`.** Move the body of
   `forms/resolvers.py::_visible_related_object` (lines ~145-172) to a public
   `visible_related_object(related_model, pk, info, async_recourse=...)` in
   `utils/querysets.py` (beside `visibility_scoped_related_queryset`), discharging the
   staged anchor there (lines ~208-220). Keep the no-primary default-manager fallback
   byte-identical (it stays the FORM flavor's behavior; the serializer's stricter
   no-primary guard is at class creation in the Slice-1 converter, already shipped —
   `serializer_converter.py::_require_relation_primary`). Re-point `forms/resolvers.py`
   to import + call it (discharge the `forms/resolvers.py` anchor lines ~175-185); delete
   the local `_visible_related_object` and its forwarding comment. The
   `tests/forms/test_resolvers.py::test_visible_related_object_no_primary_uses_default_manager`
   test references `form_resolvers._visible_related_object` — Worker 2 must re-point that
   test to the promoted symbol (a name change is a test edit, not a behavior change). See
   "Naming reconciliation" note below: use the public `visible_related_object` (no
   leading underscore) since it now crosses a module boundary, even though the spec
   import manifest writes it `_visible_related_object`.
2. **P2.4 — promote the `field_error(path, messages)` leaf ctor** into
   `mutations/resolvers.py` (discharge the staged anchor lines ~799-810). Normalize an
   empty path to `NON_FIELD_ERROR_KEY`; coerce message containers to a `list[str]`;
   return one `FieldError`. Re-point `validation_error_to_field_errors`'s two
   `FieldError(...)` constructions through it. Keep `NON_FIELD_ERROR_KEY` imported.
3. **P1.5 — promote `run_write_pipeline_sync` to `mutations/resolvers.py`** (discharge
   the staged anchor lines ~112-126). Extract the orchestration per "P1.5 promotion plan"
   above; extend `_validate_save_assign_refetch_payload` into the preamble + tail. Re-point
   `_run_create`/`_run_update` (model) and `forms/resolvers.py::_run_modelform_pipeline_sync`
   onto it via `decode_step`/`write_step` callbacks. Leave `_run_delete` and
   `_run_plain_form_pipeline_sync` OUT (F6).
4. **`rest_framework/resolvers.py` — the serializer pipeline** (replace the TODO stub).
   In the **locate → authorize → decode → construct → validate → write → re-fetch** order:
   - **`resolve_serializer_sync(mutation_cls, info, *, data=UNSET, id=UNSET)`** — the thin
     entry (the `resolve_form_sync` parallel) that delegates to `run_write_pipeline_sync`
     with the serializer `decode_step` + `write_step`.
   - **decode_step** (runs AFTER authorize, inside the skeleton): walk `data`'s provided
     `__strawberry_definition__.fields` (UNSET stripped), use the bind-stashed
     `mutation_cls._input_field_specs` (keyed by `input_attr`) to route each value by
     `kind`: SCALAR → `provided_data[spec.target_name] = raw_choice_value(value)` (the
     declared serializer field name; reuse the `_unencodable_text_error` preflight like
     the form decoder); RELATION_SINGLE/RELATION_MULTI → the dedicated serializer relation
     decoder; FILE → `provided_data[spec.target_name] = value` (an `Upload` lands in
     `data`, NOT a `files=` split — the deliberate DRF contrast with the form flavor).
     Resolve each relation's **target model** the same way the converter recorded it: via
     the backing FK (resolved from the serializer field's `source`) or, for a
     serializer-only relation, `field.queryset.model` — by re-reading the schema-time
     serializer fields (`get_serializer_for_schema()` / the recorded spec) at decode time,
     mirroring how the form decoder reads `form_field.queryset.model`. Each id is decoded
     via `decode_model_global_id` (GlobalID branch) or `_coerce_relation_pk_or_none`
     (raw-pk branch), then resolved to the visible object through the promoted
     `visible_related_object` (P1.1), reduced to the pk DRF's `PrimaryKeyRelatedField`
     expects. Hidden/wrong-type → a field-keyed `FieldError` (key = `spec.graphql_name`).
     The generated input field exposes ONE strategy-dependent shape (GlobalID for a
     Relay target, else raw-pk scalar — Decision 7); the shared decode helper accepts
     BOTH only because package tests drive the raw-pk/non-Relay branch by direct call (M1).
   - **write_step** (construct → validate → save): construct via the overridable
     `mutation_cls().get_serializer_kwargs(info, data=provided_data, instance=<row|None>)`
     hook (Slice-2-shipped default), then the framework merge (Decision 8 step 4 / H3):
     inject `partial=True` for update (never for create); a hook returning `partial`
     itself → `ConfigurationError`; merge the override's `context` dict then set
     `context["request"] = request_from_info(info, family_label="SerializerMutation")`
     UNCONDITIONALLY (a different `context["request"]` object → `ConfigurationError`, the
     SAME object tolerated). Fill `data` with `provided_data` if the hook omits it.
     Instantiate `serializer_class(**merged_kwargs)`. `serializer.is_valid()` → on failure
     route `serializer.errors` through `serializer_errors_to_field_errors` and return
     `list[FieldError]` (the skeleton maps a `list[FieldError]` return to a null-object
     payload). On success: `saved = serializer.save()` captured via the value-preserving
     closure wrapped by `save_or_field_errors(_do_save)` (`serializer.save()` called
     EXACTLY ONCE via `nonlocal`), and route a save-time **DRF `ValidationError`**
     (`.detail` → `serializer_errors_to_field_errors`) vs **Django `ValidationError`**
     (`error_dict`/`messages` → flat `validation_error_to_field_errors`) vs
     `IntegrityError` (`save_or_field_errors`) as THREE separate `except` branches (DRF
     first). Return `saved` so the skeleton's `refetch_optimized(primary_type, saved.pk,
     info, force_load=False)` re-fetch + `build_payload` tail runs.
   - **`resolve_serializer_async(...)`** — delegates to the shared
     `run_pipeline_async(<sync body>, mutation_cls, info, data, id)` boundary (one
     `sync_to_async(thread_sensitive=True)`).
5. **`rest_framework/sets.py` — land the D8 carry-forward overrides** (the only deferred
   sub-part of Slice 2's Box 1). Add `resolve_sync` / `resolve_async` classmethods on
   `SerializerMutation` (mirroring `forms/sets.py:577-610`): local-import + delegate to
   `rest_framework/resolvers.py::resolve_serializer_sync` / `resolve_serializer_async`.
   Update the class docstring lines ~40-49 ("Slice 3 fills the resolver seams") to note
   the overrides now exist. Verify the existing `get_serializer_kwargs` / `get_serializer`
   default bodies need no edit — the resolver applies the framework merge / `partial`
   injection / H3 rules on top of `get_serializer_kwargs`'s return (the Slice-2 docstrings
   already say "the framework-merge + `partial` injection that wrap it are Slice 3").
   NOTE: the shipped `get_serializer` hook already sets `context["request"]`; the resolver
   should consume `get_serializer_kwargs` (the finer hook the spec D8 step 4 names) and
   own the merge itself, so the `get_serializer` coarse hook is NOT the construction path
   (see Implementation discretion item 1).
6. **`mutations/fields.py` — NO change.** Verify only (step in tests).
7. **Products live serializer surface (same commit):**
   - `examples/fakeshop/apps/products/serializers.py` (replace the TODO stub): `ItemSerializer`
     (`serializers.ModelSerializer` over `Item`) exposing `name`, `description`, `category`
     (`PrimaryKeyRelatedField` → `categoryId`, target visibility via `CategoryType`),
     `attachment` (FileField → `Upload`). A `validate_name(...)` rejecting a module-level
     rejected-name sentinel (field-level error → keyed to `name`). A cross-field/object
     `validate(self, attrs)` reading `self.context["request"].user` (the request-context
     PROOF — rejects an item `name` equal to the authenticated username → `"__all__"`).
     `unique_item_per_category` is the model `UniqueConstraint` DRF's
     `UniqueTogetherValidator` surfaces (the `"__all__"` partial-update fire). **The live
     request-context proof MUST be a `validate()` branch, NOT a
     `HiddenField(default=CurrentUserDefault())`** (F9).
   - `examples/fakeshop/apps/products/schema.py`: discharge the import anchor (lines ~55-66)
     — `from django_strawberry_framework import SerializerMutation` (by NAME, never star —
     the root `__all__` omits it while DRF is soft); discharge the mutations anchor (lines
     ~363-373) — `CreateItemViaSerializer` (Meta.serializer_class = `serializers.ItemSerializer`,
     `operation = "create"`) + `UpdateItemViaSerializer` (`operation = "update"`); add
     `create_item_via_serializer` / `update_item_via_serializer` `DjangoMutationField`s to
     `class Mutation` (after line ~404). Do NOT accept `model_operations` / `lookup_field`.
   - `examples/fakeshop/config/settings.py`: discharge the `rest_framework` anchor (lines
     ~42-46) — add `"rest_framework"` to `INSTALLED_APPS` **only if** `ItemSerializer`
     needs the app registry. A flat `ModelSerializer` over `Item` does NOT (Decision 13 /
     spec line 969). Default: do NOT add it; remove the TODO anchor either way (Worker 2
     records which). DRF being a dev-group dep keeps it importable in the test context.
8. **Config-assessment grep-guard** (DoD): assert `rest_framework/resolvers.py` contains
   neither `conf.settings` nor `_resolve_globalid_strategy` (a relation `GlobalID` is
   decoded against the target type's RECORDED `effective_globalid_strategy` via
   `decode_model_global_id`, resolved once at finalization). Backed by the
   post-finalization monkeypatch test (below).

### Test additions / updates

Live-first per the README "Coverage rule.": `test_products_api.py` is the PRIMARY
harness; `tests/rest_framework/test_resolvers.py` holds ONLY genuinely-unreachable
residue. NO reachable behavior duplicated across the two trees. First line of each
products test: `seed_data(N)` / `create_users(N)` per AGENTS.md.

**A) Live — `examples/fakeshop/test_query/test_products_api.py`** (discharge the anchor
lines ~140-158). Add live query strings (`createItemViaSerializer(data: ItemSerializerInput!)`,
`updateItemViaSerializer(id: ID!, data: ItemSerializerPartialInput!)`) and tests for every
consumer-reachable resolver branch (reuse `_login_with_perm`, `_staff_client`,
`_global_id`, `_post_graphql`):
- **create happy path** — `createItemViaSerializer` writes; payload `node` selecting
  `category { name }` renders (permitted caller via `_login_with_perm(..., "add_item")`).
- **update happy path** — `updateItemViaSerializer` with `change_item`.
- **`categoryId` reverse-map validate-and-write** — `categoryId` (GlobalID) resolves
  through the serializer's `category` `PrimaryKeyRelatedField`, item written under the
  resolved category.
- **field-level error envelope** — a `name` failing `validate_name` → `FieldError(field="name")`,
  `node: null`, no top-level error.
- **`"__all__"` cross-field error** — a `name` equal to the username trips the object
  `validate()` → `FieldError(field="__all__")` (proves request-context AND `"__all__"`).
- **renamed/relation field error keys to GraphQL input name (F5)** — a validation error
  on the relation reports `FieldError(field="categoryId")`, NOT `category` (locks the
  reverse-map error keying against decode + plain-`name` errors).
- **partial-update preservation** — a `name`-only `updateItemViaSerializer` preserves
  `description` + `category` (assert the stored row) via `partial=True`.
- **unique-together fires on a one-field change** — changing only `name` to a value
  already taken under the unchanged `category` → `"__all__"` envelope (DRF
  `UniqueTogetherValidator` backfilling `category` from `serializer.instance`; assertion
  tied to the verified DRF floor `>=3.17.0` per spec Risks).
- **visibility-scoped update** — a caller who cannot see a private `Item`
  (`is_private=True`) gets not-found (`FieldError(field="id")`).
- **write authorization** — anonymous denied (top-level `GraphQLError`, no write);
  a caller missing `add_item`/`change_item` denied; a permitted caller succeeds.
- **relation visibility** — a permitted writer submitting a HIDDEN `Category` GlobalID as
  `categoryId` → field-keyed `FieldError(field="categoryId")`.
- **authorize-before-decode** — an UNpermitted writer submitting that SAME hidden
  `categoryId` gets the AUTH denial (top-level `GraphQLError`), NOT the relation
  `FieldError` (the security-ordering proof — most observable on create).
- **multipart `Upload` → `Item.attachment`** — a real GraphQL multipart `/graphql/`
  request (the `test_uploads_api.py` `operations`/`map`/`SimpleUploadedFile` precedent)
  creates an `Item` with an uploaded `attachment`, proving `Upload`-into-`data` routing.
- **request-context `validate()` path** — covered by the `"__all__"` test above (the
  `validate()` reads `self.context["request"].user`); add an explicit assertion that the
  injected context lands.
- **G2 optimizer re-fetch query shape** — mirror
  `test_g2_mutation_response_keeps_relation_with_bounded_query_count` (lines ~953-1011):
  wrap a `createItemViaSerializer` selecting `node { name category { name } }` in
  `CaptureQueriesContext(connection)`. **Load-bearing property (BUILD.md):** assert the
  payload re-fetch keeps `select_related`/`prefetch_related` (exactly ONE
  `products_category` SELECT services the relation — no N+1, no lazy refetch) and emits
  NO `.only(...)` column deferral. Pin the absolute count with a per-query breakdown
  comment — **DERIVE the count from a real run, never guess** (the serializer count will
  differ from the model flavor: no `full_clean`, instead `is_valid()` runs the unique
  validator; Worker 2 derives + annotates). If a count-at-two-cardinalities form is
  cleaner, assert equal count across two seed sizes + the absolute small number.

**B) Package-internal residue — `tests/rest_framework/test_resolvers.py`** (replace the
TODO stub; the anchor's pseudo-cases are the contract). EXPLICITLY NON-OVERLAPPING with
the live suite (no create/update happy path, envelope, reverse-map, partial-update,
visibility, write-auth, authorize-before-decode, Upload, request-context, or G2 here):
- **recursive flattener shapes products doesn't emit** — a `ListField` /
  `MultipleChoiceField` indexed child error → dotted-path `FieldError(field="tags.2")`;
  a nested dict-shaped error → its joined path; a nested non-field error → `<path>.__all__`
  (no structure stringified, no leaf dropped). Direct-call the flattener with synthetic
  `serializer.errors`-shaped dicts.
- **non-Relay raw-pk + many-relation decode** — synthetic non-Relay primary `DjangoType`
  + a `ManyRelatedField`; a hidden target → field-keyed `FieldError` on both branches; a
  raw-pk wrong-model / uncoercible id → `FieldError` (products' `Category` is
  Relay-GlobalID + single, so these are unreachable live; drive the shared decode helper
  by direct call — M1).
- **value-preserving save** — `serializer.save()` called EXACTLY ONCE (a save spy) and the
  re-fetch uses the returned object (not a second save, not a stale `serializer.instance`).
- **save-time validation — DRF vs Django are SEPARATE branches (F2)** — a synthetic
  serializer whose custom `create()`/`update()`/`save()` raises a DRF
  `serializers.ValidationError` (`.detail` → recursive flattener); another raising a
  Django `django.core.exceptions.ValidationError` (`error_dict`/`messages` → flat `036`
  mapper, NOT `.detail`); both land in the envelope, never top-level; assert the Django
  error never hits `.detail` and the DRF error never hits the flat mapper.
- **write-time `IntegrityError`** → `"__all__"` envelope (a monkeypatched `save()` race).
- **`get_serializer_kwargs` precedence (F7/H3)** — an override adding a kwarg while
  preserving the request context constructs correctly; an override returning
  `partial=False` (or `partial=True` on create) → `ConfigurationError`; an override
  `context` dict is merged (non-`request` keys win, framework `request` always set); an
  override supplying a DIFFERENT `context["request"]` object → `ConfigurationError`, the
  SAME object tolerated; plus the bare-`HttpRequest` `info.context` fallback of
  `request_from_info`.
- **config assessment — recorded GlobalID strategy consumed, not the live setting** —
  monkeypatch `types/relay.py::_resolve_globalid_strategy` to fail AFTER finalization and
  assert a serializer relation mutation still resolves through the recorded
  `effective_globalid_strategy` (backs the grep-guard).
- **sync + async** — one `sync_to_async(thread_sensitive=True)`; and the `SyncMisuseError`
  async-`get_queryset`-from-sync path.

**C) Field-factory verification — `tests/mutations/test_fields.py`** (discharge the anchor
lines ~332-347): declare a minimal create `SerializerMutation` over `ItemSerializer`,
import `SerializerMutation` by NAME from the package root, wrap with `DjangoMutationField`,
finalize, inspect the generated `data:` argument (resolves the `ItemSerializerInput` lazy
ref), and assert the class routes `resolve_sync` to `rest_framework.resolvers`. VERIFICATION
only (no `mutations/fields.py` edit).

**D) Config-assessment grep-guard** — a package test (e.g. in `test_resolvers.py` or
`tests/base/`) reads `rest_framework/resolvers.py` source and asserts neither `conf.settings`
nor `_resolve_globalid_strategy` appears (the static DoD check; the monkeypatch test in (B)
is the behavioral backstop).

**E) Cross-tree regression sweep** — because P1.5/P1.1/P2.4 edit `mutations/resolvers.py`,
`forms/resolvers.py`, `utils/querysets.py`, the existing `036` model-mutation and `038`
form-mutation suites (`tests/mutations/`, `tests/forms/`) must stay green UNCHANGED (the
byte-equivalence regression proof). Worker 2 runs a full `tests/ --no-cov` sweep (NOT just
focused scope) before setting `built`, per worker-1 "Example-model field changes ripple"
guidance — the only test edit allowed in those trees is the mechanical
`_visible_related_object` → `visible_related_object` rename in
`tests/forms/test_resolvers.py::test_visible_related_object_no_primary_uses_default_manager`.

### Implementation discretion items

1. **Resolver construction path through `get_serializer_kwargs` vs `get_serializer`.** The
   spec D8 step 4 names `get_serializer_kwargs(info, *, data, instance=None)` as the hook
   the resolver constructs through, then applies the framework merge / `partial` / H3
   rules. The Slice-2 `SerializerMutation` ships BOTH `get_serializer_kwargs` (the finer
   hook) AND `get_serializer` (a coarser hook that already sets `context["request"]`).
   Worker 2 may either (a) have the resolver call `get_serializer_kwargs` and own the
   merge/partial/H3 itself (the spec's literal shape — recommended, since the H3
   `ConfigurationError` rules and `partial` injection are framework-owned and must not
   live in the consumer-overridable coarse hook), or (b) thread the merge through
   `get_serializer`. Either is acceptable IF the H3 "request is framework-owned / partial
   is framework-owned" invariants hold and the `_hook_overridden(get_serializer_kwargs)`
   waiver (already wired in `build_input`) stays the guard-waiver basis. Recommended: (a).
2. **`provided_data` key:** SCALAR/FILE values land under `spec.target_name` (the declared
   serializer field name DRF maps to `source` internally), relation values likewise — the
   exact dict-build order of the decode walk is at Worker 2's discretion as long as the
   serializer receives a `data` dict keyed by declared field names.
3. **G2 query-shape assertion form** (absolute-count-with-breakdown vs
   equal-count-at-two-cardinalities) is Worker 2's choice; both pin the load-bearing
   property. Either way derive numbers from a real run.

### Spec slice checklist (verbatim)

- [ ] Slice 3: the serializer resolver pipeline **+ the products live serializer
  surface, landed in one commit** (per
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-refetch--payload)
  /
  [Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path)
  /
  [Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)).
  **The resolver code and its consumer surface ship together** so every
  consumer-reachable resolver line is earned by a real `/graphql/` request the moment it
  lands — the [`examples/fakeshop/test_query/README.md`][test-query-readme]
  #"Coverage rule." live-first mandate; splitting them would force package tests to cover
  reachable lines at the resolver commit, the inverse of the rule.
  - [x] [`rest_framework/resolvers.py`][rf-resolvers]: the sync + async pipeline, in
    the **locate → authorize → decode → construct → validate → write → re-fetch** order
    (`036` / `038` security invariant — authorize **before** any relation decode) —
    (`update`) **locate** the row through the target type's
    [`get_queryset`][glossary-get_queryset-visibility-hook] (not-found → a `FieldError`
    on `id`, no existence leak; `create` has no locate); **authorize** via the inherited
    `check_permission` / `Meta.permission_classes` against the **raw** input payload
    (`create`: `instance=None`; `update`: the located instance) — denial → top-level
    `GraphQLError`, run **before** decode so an unauthorized caller cannot probe
    relation visibility by id; **decode** the `data:` input via the reverse map into a
    serializer-field-keyed `provided_data`, using a **dedicated serializer relation
    decoder** that mirrors the `038` form decoder (serializer-field-keyed, NOT the
    model-attr-keyed `036` `_decode_relation_id_set`). **The generated input field exposes
    exactly ONE strategy-dependent shape** (Decision 7): a `GlobalID` when the target primary
    [`DjangoType`][glossary-djangotype] is Relay-shaped, else the target's raw-pk scalar — so
    a live request can only deliver the one shape the annotation admits; the **shared decode
    helper** accepts both a `GlobalID` and a raw pk only because it is reused and package
    tests drive the raw-pk / non-Relay branch by direct call (M1). Each id the decoder sees
    is type-checked against the relation's **target model** — resolved from the backing FK
    via the serializer field's `source`, **or, for a serializer-only relation, from the DRF
    field's `queryset.model`** (Decision 7) —
    resolved to the **visible** object through the related primary
    `DjangoType.get_queryset` — the same per-branch raw-pk visibility check both
    `036`'s model-path decoder (`_decode_relation_id_set` → `_raw_pk_relation_error`)
    and the `038` form decoder (`_visible_related_object`) already enforce — and reduced
    to the pk DRF expects for a `PrimaryKeyRelatedField` before landing under the
    serializer field name; a hidden target → field-keyed `FieldError`; a serializer `FileField` /
    `ImageField` value (an [`Upload`][glossary-upload-scalar]) is routed into the
    serializer's `data` like any other value (DRF serializers read files from `data`,
    unlike Django forms which split `files=`); **construct** the serializer via the
    overridable `get_serializer_kwargs(info, *, data, instance=None)` hook (the graphene
    `get_serializer_kwargs` parity seam) — create:
    `serializer_class(**get_serializer_kwargs(info, data=provided_data))`; **update
    (partial):** `serializer_class(**get_serializer_kwargs(info, data=provided_data,
    instance=<row>))` with **`partial=True`** injected (DRF's native partial-update —
    no full-payload reconstruction needed, the divergence from `038`'s form
    reconstruction); inject `context={"request": request_from_info(info,
    family_label="SerializerMutation")}` (the package's shared request-extraction
    helper, [`utils/permissions.py`][utils-permissions]) so the serializer's own
    validators / `HiddenField(default=CurrentUserDefault())` resolve;
    **validate** via `serializer.is_valid()` — a failure maps the nested
    `serializer.errors` onto the [`FieldError` envelope][glossary-fielderror-envelope]
    via a **dedicated recursive flattener** (`serializer_errors_to_field_errors`, dotted
    path `items.0.name`, DRF's `non_field_errors` / `NON_FIELD_ERRORS_KEY` bucket → the
    `"__all__"` sentinel `036` froze at every level — NOT the one-level `036`
    `validation_error_to_field_errors`) and returns a null-object payload; **write** via
    `serializer.save()`, **wrapped by the `036` `save_or_field_errors` `IntegrityError`
    → envelope mapper** in a **value-preserving closure** (the wrapper discards its
    callable's return, so the resolver captures `saved = serializer.save()` via
    `nonlocal` — called exactly once); **re-fetch** the saved object by `saved.pk`
    + optimizer-plan; **return** the `<Name>Payload` (`node` / `result`). The whole
    pipeline runs inside one `transaction.atomic()`, and the async path runs the sync
    body in one `sync_to_async(thread_sensitive=True)` call — the same boundary
    `036` / `038` set.
  - [x] [`mutations/fields.py`][mutations-fields]: **no change** —
    [`DjangoMutationField`][glossary-djangomutationfield] was already generalized by
    [`spec-038`][spec-038] Slice 3 along its three model-hardwired axes (target check
    via the duck-typed `_has_mutation_protocol`, `_resolve` dispatch via
    `mutation_cls.resolve_sync` / `resolve_async`, the `data:` lazy-ref via
    `mutation_cls.input_type_name` + `input_module_path`), explicitly "for the
    `0.0.13` serializer flavor". Slice 3 **verifies** the generalization holds for
    `SerializerMutation` (a `tests/mutations/test_fields.py` extension); no field-factory
    edit is needed ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)).
  - [x] **Products live serializer surface (same commit).**
    [`examples/fakeshop/apps/products/serializers.py`][products-serializers] (new): an
    `ItemSerializer` (`serializers.ModelSerializer` over `Item`, with a
    `validate_<field>` and a cross-field `validate()`) and a second serializer mutation
    (or fields on `ItemSerializer`) exposing the two **shipped runtime branches** that
    are real `/graphql/` behavior, not future-`TestClient` work: the
    [`Item.attachment`][products-models] `FileField` as an [`Upload`][glossary-upload-scalar]
    input (a real multipart create — the [`test_uploads_api.py`][test-uploads-api]
    `MediaSpecimen` multipart precedent proves `django.test.Client` drives this today),
    and an **observable request-context path** — an explicit `validate()` /
    `validate_<field>()` that reads `self.context["request"].user`, proving the injected
    `context={"request": …}` lands. **The live proof must be a `validate()` branch, not a
    `HiddenField(default=CurrentUserDefault())`** (**F9**): DRF hidden-field defaults are
    subtle under `partial=True` (a hidden field's default behavior differs between full and
    partial validation), so they are not a stable way to prove update-time request context.
    `HiddenField` stays covered only as an input-generation / drop rule (and, if desired, a
    create-only behavior), never as the request-context proof.
    [`products/schema.py`][products-schema] gains the `SerializerMutation`(s)
    (create + update); `config/schema.py` already wires `mutation=Mutation`
    ([`spec-036`][spec-036] Slice 4). The example settings add `"rest_framework"` to
    `INSTALLED_APPS` only if a serializer needs the app registry (most flat
    `ModelSerializer`s do not). DRF being a dev-group dependency
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
    keeps it present in the test context (the [`spec-037`][spec-037] `pillow` /
    `MediaSpecimen` precedent).
  - [x] **Live coverage is the primary harness** ([`test_products_api.py`][test-products-api],
    seeded via `seed_data` / `create_users`): **every consumer-reachable resolver branch
    is earned here over real `/graphql/`** — create / update happy paths;
    field-level (`validate_<field>`) and `"__all__"` (cross-field `validate()` /
    `unique_item_per_category`) `serializer.errors` envelopes; `categoryId` reverse-map
    validate-and-write through the serializer's `category` `PrimaryKeyRelatedField`;
    **partial-update preservation** (`name`-only update preserves `category` /
    `description` via `partial=True`) and the unique-together fire on a one-field change;
    the **visibility-scoped `update`** (hidden row → not-found); **write authorization**
    (anonymous / missing-perm denied, permitted succeeds); **a hidden-`Category`
    `GlobalID` → field-keyed `FieldError`** (relation visibility) and
    **authorize-before-decode** (an unpermitted caller submitting that hidden id gets the
    auth denial, not the relation error); the **multipart `Upload` → `Item.attachment`**
    write; the **request-context** `validate()` path; and the **G2 optimizer re-fetch
    query shape** (assert the SQL keeps `select_related` / `prefetch_related`, no
    `.only(...)`).
  - [x] **Package-internal, genuinely-unreachable internals only**
    ([`tests/rest_framework/test_resolvers.py`][test-rest-framework]): the residue a live
    fakeshop query **cannot** drive — the **recursive flattener** shapes no products
    serializer emits (deeply nested `ListField` / dict child errors, `<path>.__all__`
    normalization); **raw-pk / non-Relay** relation decoding and **many-relation**
    decoding (products' `Category` is Relay-`GlobalID` and single, so these need a
    synthetic non-Relay / many fixture); the **call-once save capture** (a save spy);
    the **sync + async** boundary (`sync_to_async(thread_sensitive=True)`) and the
    [`SyncMisuseError`][glossary-syncmisuseerror] async-hook-from-sync path; and hermetic
    `get_serializer_kwargs` / constructor seams not observable over HTTP. **No
    create/update happy path, envelope, reverse-map, partial-update, visibility, or
    write-auth test is duplicated here** — those are owned by the live suite above
    (the [`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule.").
  - [x] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    the sync pipeline rides the promoted `run_write_pipeline_sync(...)` skeleton **scoped to
    model-backed create/update only** (delete + model-less plain form excluded, **F6**) —
    the serializer supplies only `decode_step` + `write_step` callbacks (construct /
    `is_valid()` / `save()`), and the `transaction.atomic()` boundary + the
    **authorize-before-decode security ordering** is single-sited across the three
    model-backed flavors, not hand-copied a third time, with the existing model / model-form
    suites staying byte-equivalent (**P1.5**); the relation decoder re-keys over the promoted `_visible_related_object`
    in [`utils/querysets.py`][utils-querysets] rather than forking a third object-returning
    decoder (**P1.1**); and `serializer_errors_to_field_errors` (recursive, legitimately new)
    imports the shared `mutations/inputs.py::NON_FIELD_ERROR_KEY` sentinel — and ideally a
    promoted `field_error(path, messages)` leaf ctor both flatteners call — so the DRF
    `non_field_errors` → `"__all__"` mapping cannot drift from the flat `036` mapper
    (**P2.4**). The promotions themselves edit `mutations/resolvers.py` / `utils/querysets.py`
    (with `forms/resolvers.py` re-pointed to the shared sites); the `036` leaf helpers stay
    reused-by-call.
  - [x] **Config-assessment grep-guard (query-path strategy).** A relation `GlobalID` is
    decoded against the target type's **recorded** `effective_globalid_strategy`
    ([`types/relay.py`][types-relay] / [`types/definition.py`][types-definition], resolved
    once at finalization). A Slice 3 DoD check **greps [`rest_framework/resolvers.py`][rf-resolvers]
    for `conf.settings` and `_resolve_globalid_strategy`** and asserts **neither appears** on
    the query path (no per-request setting re-read / re-validation), backed by the
    post-finalization monkeypatch test in the [Test plan](#test-plan) (fail
    `_resolve_globalid_strategy`, assert serializer relation decode still resolves from
    recorded state).

### Notes for Worker 1 (spec reconciliation)

No spec edit made at planning (none required). Flags carried for final verification:

1. **P1.1 helper name discrepancy (resolve at build, NOT a spec edit).** The spec import
   manifest (line 2892) and Decision 8 / P1.1 (lines 2360-2362) write the promoted helper
   as `_visible_related_object` (leading underscore) in `utils/querysets.py`, but the two
   staged source anchors (`utils/querysets.py` ~line 208 and `forms/resolvers.py` ~line 176)
   both name it `visible_related_object` (public, no underscore). The other promoted
   `utils/` helpers crossing module boundaries are public (`visibility_scoped_related_queryset`,
   `apply_type_visibility_sync`), so the **public `visible_related_object` is correct** and
   the spec's underscore form is a carry-over from when it was a `forms/`-local private. This
   is an implementation naming choice, not a contract change — recorded here so Worker 1
   final-verif does not read the underscore-vs-not as drift. NO spec edit (the prose names a
   reuse obligation, not a public-API contract). If Worker 3 flags it, point here.

2. **D8 carry-forward (the only deferred sub-part of Slice 2's Box 1).** Slice 2 left
   `SerializerMutation` WITHOUT `resolve_sync`/`resolve_async` overrides because
   `rest_framework/resolvers.py` did not exist (verified: `rest_framework/sets.py` has no
   `def resolve_sync`; an inert declaration inherited `DjangoMutation`'s callable pair, so
   `DjangoMutationField`'s target-check passed). Slice 3 MUST land BOTH the overrides in
   `rest_framework/sets.py` AND the `resolve_serializer_sync`/`resolve_serializer_async`
   bodies in `rest_framework/resolvers.py` — the same slice/resolver-existence pairing the
   form flavor used (`forms/sets.py:577-610` ride `forms/resolvers.py::resolve_form_sync`/
   `resolve_form_async`). Final-verif must confirm both landed (this closes Slice-2 Box 1).

3. **Stale spec Status header (carry-forward, NOT churned here).** Spec lines 1-12 still say
   "Planned for `0.0.13`" / describe the card as not-yet-built. Per the build-wide F8 split
   and prior-slice carry-forwards (worker-1 memory Slice 1/2), the implemented-on-main Status
   edit is **Slice-4-owned** (the doc-wrap slice), not churned per-slice mid-build. Worker 1
   re-verified the header this spawn and deliberately left it. No edit.

4. **L1 fold-in decision (Slice-1 carry).** A vacuous-tautology assertion at
   `tests/rest_framework/test_inputs.py:620` is deferred to the integration pass. Slice 3
   touches `tests/rest_framework/` (it adds `test_resolvers.py`). **Decision: LEAVE it for
   the integration pass**, NOT folded here — Slice 3 is already the largest slice and adds a
   new test file + a cross-tree regression sweep; bundling an unrelated one-line `test_inputs.py`
   cleanup into this commit dilutes the diff's reviewability for no coverage gain (the
   contract it fails to pin is pinned by `test_inputs.py:619`+`622`). Recorded for the
   integration-pass deferred catalog.

### Implementation discretion items

(See the three items under "Implementation discretion items" in the Plan section above —
resolver construction path through `get_serializer_kwargs` vs `get_serializer`; the
`provided_data` decode-walk dict-build order; the G2 query-shape assertion form. All three
are assessed-and-delegated, not architectural escape hatches.)

## Build report (Worker 2)

Status: built

### Files touched

Slice-intended (grounded in `git diff HEAD`; the broader `git status` includes
prior-slice uncommitted work — Slice 0/1/2 source — which I did NOT touch):

- `django_strawberry_framework/mutations/resolvers.py` — **P1.5** authored
  `run_write_pipeline_sync(...)` (the model-backed create/update skeleton: atomic
  boundary + locate preamble + authorize-before-decode + decode/write callbacks +
  optimizer re-fetch tail), re-pointed the model path onto it via
  `_model_decode_step` / `_model_write_step` (the prior `_run_create` /
  `_run_update` / `_validate_save_assign_refetch_payload` folded into callbacks;
  `_full_clean_or_payload` → `_full_clean_or_field_errors` returning a
  `list[FieldError]` so the payload build single-sites in the skeleton; `_run_delete`
  left out per F6). **P2.4** authored the shared `field_error(path, messages)` leaf
  ctor + re-pointed `validation_error_to_field_errors` through it.
- `django_strawberry_framework/forms/resolvers.py` — re-pointed
  `_run_modelform_pipeline_sync` onto `run_write_pipeline_sync` via
  `_modelform_decode_step` / `_modelform_write_step`; deleted the local
  `_visible_related_object` (P1.1 promotion) and re-pointed its call site to the
  promoted helper; trimmed the now-unused imports.
- `django_strawberry_framework/utils/querysets.py` — **P1.1** promoted the
  object-returning `visible_related_object(related_model, pk, info, async_recourse)`
  (the form + serializer relation decoders both call it).
- `django_strawberry_framework/rest_framework/resolvers.py` — the serializer
  pipeline: `resolve_serializer_sync` / `resolve_serializer_async` (delegating to the
  shared skeleton + `run_pipeline_async`), the serializer-field-keyed
  `_decode_serializer_data` + relation decoders (`Upload` → `data`), the recursive
  `serializer_errors_to_field_errors` flattener (re-keying root segments through the
  reverse map, normalizing DRF `non_field_errors` → `"__all__"` at every level), the
  `_merged_serializer_kwargs` H3 framework merge (`partial` injection +
  request-context ownership), and the write step's DRF-vs-Django save-time
  `ValidationError` split + `IntegrityError`.
- `django_strawberry_framework/rest_framework/sets.py` — landed the **D8
  carry-forward** `resolve_sync` / `resolve_async` overrides (delegating to the
  resolver bodies) + updated the class docstring.
- `examples/fakeshop/apps/products/serializers.py` — new `ItemSerializer`
  (`ModelSerializer` over `Item`, `validate_name` + a request-context object
  `validate()`, the `category` `PrimaryKeyRelatedField` + the `attachment`
  `FileField`; the `unique_item_per_category` `UniqueTogetherValidator` rides for
  free).
- `examples/fakeshop/apps/products/schema.py` — `CreateItemViaSerializer` /
  `UpdateItemViaSerializer` `SerializerMutation`s + their `DjangoMutationField`s;
  `SerializerMutation` imported by name; docstring updated.
- `examples/fakeshop/config/settings.py` — removed the `"rest_framework"` TODO
  anchor; recorded that it is intentionally NOT installed (Decision 13 — settled
  empirically: a flat `ModelSerializer` builds + validates without the app registry).
- `examples/fakeshop/test_query/test_products_api.py` — the live serializer suite
  (15 tests + the two query-string constants).
- `tests/rest_framework/test_resolvers.py` — the package-internal residue (25 tests).
- `tests/mutations/test_fields.py` — the `DjangoMutationField`-generalizes-to-
  `SerializerMutation` verification (no `mutations/fields.py` edit).
- `tests/forms/test_resolvers.py` — the mechanical
  `_visible_related_object` → `visible_related_object` rename (import + 2 call sites;
  a name change, not a behavior change — the byte-equivalence carve-out the plan
  licensed).

`docs/feedback.md` (modified at session start, NOT by me) and
`docs/spec-039-*.md` (prior-slice / Worker-1 work) were left untouched per the
contract.

### Tests added or updated

- **Live (primary harness)** — 15 new tests in `test_products_api.py`: create /
  update happy paths; `categoryId` reverse-map write; `validate_name` field-level
  envelope; the object-`validate()` `"__all__"` cross-field + request-context proof;
  the `unique_item_per_category` `"__all__"` envelope (create + partial-update
  one-field-change fire); partial-update preservation; visibility-scoped update
  (hidden row → not-found); anon / missing-perm / permitted write auth; hidden
  `Category` `categoryId` → field-keyed `FieldError`; authorize-before-decode
  (unpermitted caller submitting the hidden id gets the AUTH denial, not the relation
  error); multipart `Upload` → `Item.attachment`; the G2 re-fetch query shape.
- **Package residue** — 25 new tests in `tests/rest_framework/test_resolvers.py`:
  recursive-flattener shapes (list index, nested dict, nested + top-level non-field,
  root re-key); raw-pk / non-Relay single + many decode (hidden / visible / uncoercible
  / wrong-model / explicit-None); the call-once save spy; the save-time DRF-vs-Django
  split + `IntegrityError`; the `get_serializer_kwargs` H3 merge (partial inject,
  request unconditional, merged context, partial-return / different-request
  `ConfigurationError`, bare-`HttpRequest` fallback); the grep-guard + the
  post-finalize `_resolve_globalid_strategy` monkeypatch; the `SyncMisuseError`
  async-`get_queryset`-from-sync path; the async resolver boundary.
- **Field factory** — 1 test in `tests/mutations/test_fields.py` (verification only).
- No reachable behavior is duplicated across the live + residue trees.

### Validation run

- `uv run ruff format .` — **pass** (3 files reformatted on the first run: the three
  source files I had hand-edited; second run clean).
- `uv run ruff check --fix .` — **pass** (5 auto-fixed; I hand-fixed the remaining 3:
  dropped the unused `model` param on `_model_write_step`, renamed the serializer
  decode lambda's unused `instance` → `_instance`, inlined the `field_error` if/else
  ternary). Final `ruff check .` → **All checks passed!**.
- `git status --short` after both ruff runs — every file I touched is slice-intended
  (listed under Files touched); no tool churn into prior-slice files (ruff reformatted
  only my 3 hand-edited files). The broader `git status` modified set is the
  cumulative spec-039 working tree (prior slices uncommitted at HEAD); `docs/feedback.md`
  was dirty at session start and untouched by me. `examples/fakeshop/db.sqlite3` is
  NOT dirty (the live tests seed the test DB, not the example file).
- `uv run pytest examples/fakeshop/test_query/test_products_api.py tests/rest_framework
  tests/mutations tests/forms --no-cov` — **545 passed**. This confirms the new live
  + package serializer tests pass AND the `036` model + `038` form suites stay green
  = the P1.5 / P1.1 / P2.4 **byte-equivalence regression proof** (the promotions did
  not alter the model / form paths).

**Derived G2 absolute count = 12.** Derived from a real run (a finalized full-schema
build under a test DB, `CaptureQueriesContext` over a `createItemViaSerializer`
selecting `node { name category { name } }`), NOT guessed. Per-query breakdown
(annotated in the test): `BEGIN` + `COMMIT` (2) + session/auth_user/user_perms/
group_perms (4) + the relation-id visibility decode `products_category` (1) + DRF
`is_valid()`'s `PrimaryKeyRelatedField` FK re-fetch `products_category` (1) +
`UniqueTogetherValidator` `SELECT 1` EXISTS on `products_item` (1) + `INSERT
products_item` (1) + the optimizer-planned re-fetch `products_item` (1) + the
`select_related` `category` relation `products_category` (1) = 12. The load-bearing
asserts: exactly ONE `products_item` `SELECT *` re-fetch (the `SELECT 1` EXISTS
excluded — no lazy `.only(...)` refetch) and THREE `products_category` `SELECT *`
(decode + DRF FK validation + the re-fetch relation — no N+1). The serializer count
differs from the model flavor's 12-by-composition: no `full_clean`, instead DRF's
`is_valid()` runs the FK re-fetch + the unique validator.

### Implementation notes

- **P1.5 skeleton shape:** `run_write_pipeline_sync` owns the atomic boundary +
  locate + authorize-before-decode + the `refetch_optimized`/`build_payload` tail;
  `decode_step(instance) -> decoded | list[FieldError]` and `write_step(instance,
  decoded) -> saved | list[FieldError]` are the only per-flavor seams. A step
  returning a `list` short-circuits to a null-object payload; `write_step` returns the
  saved object so the tail re-fetches by `saved.pk`. The model flavor's decode step
  returns `(target, m2m_assignments, exclude)` (the constructed/located instance rides
  in the tuple, so create's fresh instance and update's located instance are uniform);
  the model write step's `instance` param is `del`'d (the target is in `decoded`).
- **P1.1 public name:** the promoted helper is `visible_related_object` (NO leading
  underscore — per the plan's flag #1, the public form is correct since it now crosses
  a module boundary; the spec import manifest's underscore form is a carry-over from
  when it was form-local). Worker 1 final-verif should keep this name.
- **Relation target-model resolution at decode:** `_relation_target_models` re-reads
  the serializer's schema-time fields and reads `field.queryset.model`
  (`field.child_relation.queryset.model` for a `ManyRelatedField`) — the SAME basis
  the converter typed the input over. A `ModelSerializer`'s auto-generated
  `PrimaryKeyRelatedField` carries a concrete `queryset`, so this resolves both
  model-backed and serializer-only relations without re-deriving the backing FK.
- **Recursive flattener non-field normalization:** the DRF `non_field_errors` key is
  mapped to the `NON_FIELD_ERROR_KEY` SEGMENT (joined like any other), so a top-level
  bucket → `"__all__"` and a nested one → `<path>.__all__` uniformly (no empty-segment
  special case). `_DRF_NON_FIELD_KEY` is read once from `serializers.api_settings`
  (not a hard-coded literal) so the flattener normalizes whatever key DRF is
  configured to use.
- **H3 construction path (discretion item 1, recommended option a):** the resolver
  consumes `get_serializer_kwargs` (the finer hook) and OWNS the merge / `partial` /
  request-context invariants in `_merged_serializer_kwargs`; the coarse `get_serializer`
  hook is NOT the construction path (the framework-owned invariants stay out of the
  consumer-overridable hook).
- **`"rest_framework"` NOT added to `INSTALLED_APPS`** (Decision 13 default): settled
  empirically — a finalized full-schema build + `ItemSerializer().fields` +
  `UniqueTogetherValidator` all work without the DRF app registry. The TODO anchor was
  removed and the decision recorded inline in `settings.py`.
- **G2 assertion form (discretion item 3):** chose absolute-count-with-breakdown
  (12), the same form the model G2 test uses, with the count derived from a real run.

### Notes for Worker 3

- No `scripts/review_inspect.py` shadow file was used.
- The live unique-together envelope keys to `"__all__"` (not `categoryId`): DRF's
  `UniqueTogetherValidator` raises under `non_field_errors`, not keyed to a
  constituent field — so the F5 relation-error-keys-to-`categoryId` reverse-map proof
  is the hidden-`Category` relation-decode test (where DRF DOES key to the field),
  while the unique-together case is the `"__all__"` cross-field envelope. Both
  intents are covered.
- The `tests/forms/test_resolvers.py` edit is the plan-licensed mechanical rename
  only; the form suite stays byte-equivalent in behavior (proven by the 545-test run).

### Notes for Worker 1 (spec reconciliation)

- **P1.1 helper name (plan flag #1, resolved at build):** landed as the PUBLIC
  `visible_related_object` (no leading underscore), per the plan's recommendation.
  The spec import manifest writes `_visible_related_object`; this is the
  carry-over-from-form-local naming the plan flagged, NOT drift. No spec edit made.
- **D8 carry-forward closed:** both the `rest_framework/sets.py` `resolve_sync` /
  `resolve_async` overrides AND the `rest_framework/resolvers.py` bodies landed in
  this slice (Slice-2 Box 1 is now closed).
- **`run_write_pipeline_sync` refactor scope (small, mechanically-obvious drift,
  recorded per worker-2 guidance):** P1.5 required folding the model's
  `_validate_save_assign_refetch_payload` tail + the `_run_create` / `_run_update`
  preambles into decode/write callbacks. The prior `_full_clean_or_payload` (which
  built a payload) became `_full_clean_or_field_errors` (returns a `list[FieldError]`)
  so the payload build single-sites in the skeleton. No public model/form symbol
  changed signature in a consumer-visible way; the model + form suites stay
  byte-equivalent (545-test proof). The model `_run_create` / `_run_update` /
  `_validate_save_assign_refetch_payload` helpers no longer exist as named functions
  (replaced by `_model_decode_step` / `_model_write_step` + the skeleton); no test
  referenced them by name (verified via grep).

---

## Review (Worker 3)

Reviewed the working-tree diff for Slice 3's contribution (filtered to Worker 2's
`### Files touched`; cumulative-diff prior-slice work and `docs/feedback.md` treated
out-of-scope). Static helper run on all four logic-bearing source files
(`rest_framework/resolvers.py`, `mutations/resolvers.py`, `forms/resolvers.py`,
`utils/querysets.py`) → `docs/shadow`. Focused suite
(`test_products_api.py tests/rest_framework tests/mutations tests/forms --no-cov`)
ran green: **545 passed** (no `--cov`).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **`_relation_field_error` near-copy across flavors (route to Worker 1 integration
  pass, NOT blocking).** `rest_framework/resolvers.py::_relation_field_error` is a
  byte-identical body to `forms/resolvers.py::_relation_field_error` (same docstring,
  same `FieldError(field=graphql_name, messages=[f"Invalid id for relation
  {graphql_name!r}."])`). The message literal `"Invalid id for relation {…!r}."` is
  now LIVE in three sites: `forms/resolvers.py` #"Invalid id for relation",
  `mutations/resolvers.py::_raw_pk_relation_error` #"Invalid id for relation"
  (pre-existing `036`), and `rest_framework/resolvers.py` #"Invalid id for relation".
  Verdict: **pre-existing two-site pattern (forms + mutations) at HEAD that Slice 3
  extends to a third site following the established shape, NOT novel divergence.** The
  spec import manifest (line 2892) does NOT list `_relation_field_error` for promotion
  (it promotes the leaf `field_error` ctor via P2.4, which IS done). A consolidation
  into a shared `relation_field_error(graphql_name)` ctor (beside `field_error`) is the
  natural cross-flavor DRY move, but it spans the `036` model path too, so it belongs in
  the cross-slice integration DRY scan, not this slice's diff. Recorded for the
  integration pass; not a blocker.
- **All spec-mandated promotions landed and are single-sited (verified by grep):**
  `run_write_pipeline_sync` (P1.5), `field_error` (P2.4), `visible_related_object`
  (P1.1), and the recursive `serializer_errors_to_field_errors` are each defined
  EXACTLY ONCE; no third decoder fork, no re-spelled `"__all__"`, no hand-copied
  atomic/authorize ordering. The import manifest is honored: `rest_framework/resolvers.py`
  imports the listed `036`/`utils`/`relay`/`inputs` symbols and re-implements none.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows a change, but it is the
**Slice-2-accepted** `__getattr__` lazy-export landing (the `TODO(spec-039 Slice 2)`
anchor → the PEP 562 `__getattr__`), NOT this slice's contribution — Worker 2's
`### Files touched` correctly omits `__init__.py`. `__all__` does NOT add
`SerializerMutation` (it stays absent — F1 preserved, `from … import *` stays DRF-free).
No Slice-3 public-surface change. PASS.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The slice touches example-app surface only (`products/serializers.py`,
`products/schema.py`, `config/settings.py`) — example code, not docs/release/KANBAN/archive.
No version strings, card IDs, or shipped/planned statuses changed. `config/settings.py`
change is the Decision-13 anchor removal: `"rest_framework"` is intentionally NOT added
to `INSTALLED_APPS` (a flat `ModelSerializer` + `UniqueTogetherValidator` needs no DRF
app registry — settled empirically; the 545-test green run confirms the build + validate
+ unique-together all work without it). Confirmed correct per Decision 13 / spec line 969.
No `version`/card claims to check.

### What looks solid

- **Authorize-before-decode security invariant (highest priority) — solid by both
  code-trace and live test.** `run_write_pipeline_sync` calls
  `authorize_or_raise(... instance=instance)` at step 3 BEFORE `decode_step(instance)` at
  step 4, single-sited across all three model-backed flavors. The skeleton's preamble is
  **byte-identical** to the HEAD `forms/resolvers.py::_run_modelform_pipeline_sync`
  preamble (verified via `git show HEAD:` token-diff: same `meta`/`primary_type`/`slot`/
  `payload_cls`/`is_update` setup, same `with transaction.atomic()`, same locate block,
  same `authorize_or_raise(mutation_cls, info, meta.operation, data, instance=instance)`
  call). The live test
  `test_create_item_via_serializer_authorize_before_decode_unpermitted_gets_auth_denial`
  proves the observable distinction over real `/graphql/`: an unpermitted caller
  submitting a hidden `categoryId` gets the top-level AUTH `GraphQLError` (data nulled),
  NOT the in-band relation `FieldError` — contrasted against the permitted-caller case
  (`..._hidden_category_id_is_field_keyed_relation_error`) that DOES see the relation
  `FieldError`. The two cases are distinct and prove the ordering.
- **Relation decode + visibility.** `_decode_relation_single` type-checks each id against
  the target model (`_relation_target_models` reads `field.queryset.model` /
  `field.child_relation.queryset.model` — the same basis the converter typed the input
  over), decodes a `GlobalID` via `decode_model_global_id` against the RECORDED strategy
  (wrong-model → field error, verified by `test_..._wrong_model_global_id_is_field_error`)
  or a raw pk via `_coerce_relation_pk_or_none`, resolves the VISIBLE object through the
  promoted `visible_related_object` (P1.1), reduces to pk. Hidden → field-keyed
  `FieldError`. An `Upload` lands in `provided_data` (FILE branch), NOT a `files=` split.
- **Recursive flattener `serializer_errors_to_field_errors`.** Depth-first; dotted paths
  (`items.0.name`); the DRF non-field key normalizes to `"__all__"` at EVERY level (top →
  bare `"__all__"`, nested → `<path>.__all__`), driven by `_DRF_NON_FIELD_KEY` read once
  from `serializers.api_settings.NON_FIELD_ERRORS_KEY` (not a hard-coded literal); root
  segment re-keyed through the reverse map (F5). Distinct from the one-level `036` mapper.
  Pinned by 5 direct-call package tests (list index, nested dict, nested + top-level
  non-field, root re-key).
- **Save closure value-preserving + called once.** `saved = serializer.save()` via
  `nonlocal` inside the closure wrapped by `save_or_field_errors(_do_save)`; the save-time
  `ValidationError` routes by exception CLASS in THREE separate `except` branches (DRF
  `serializers.ValidationError`.detail → recursive flattener FIRST; Django
  `ValidationError` → flat `036` mapper; `IntegrityError` → `save_or_field_errors`).
  Pinned by the save-spy (`..._called_exactly_once...`), the DRF-vs-Django split (asserts
  Django never hits `.detail`, DRF never hits the flat mapper), and the `IntegrityError`
  → `"__all__"` test.
- **G2 re-fetch query shape (Decision 9).** The serializer G2 live test mirrors the
  accepted model G2 test faithfully: absolute count **= 12 DERIVED from a real run** (per
  Worker 2's annotated per-query breakdown — BEGIN/COMMIT + auth machinery + decode
  visibility + DRF `is_valid()` FK re-fetch + `UniqueTogetherValidator` `SELECT 1` + INSERT
  + optimizer re-fetch + the `select_related` category), with the load-bearing asserts:
  exactly ONE `products_item` `SELECT *` re-fetch (the unique-validator `SELECT 1` EXISTS
  excluded — no lazy `.only(...)` refetch) and THREE `products_category` SELECTs (decode +
  DRF FK validation + re-fetch relation — no N+1). The "no `.only()`" is pinned the same
  way the slice-2-accepted model G2 test pins it (column-exact snapshot is the package
  mirror's job; the live tier pins behavior). The test exercises the intended fast path
  (minimal selection `node { name category { name } }`, no sidecar arg routing to a
  fallback). Real derivation, not a guess (the count differs from the model flavor's 12 by
  composition — no `full_clean`, DRF runs the FK re-fetch + unique validator instead;
  Worker 2 annotated the difference). PASS per BUILD.md "load-bearing property" rule.
- **LIVE-FIRST coverage (DoD 5 / Coverage rule.).** `test_products_api.py` is the PRIMARY
  harness (15 tests, first line `create_users`/`seed_data` per AGENTS.md): create/update
  happy, field + `"__all__"` envelopes, `categoryId` reverse-map, partial-preserve +
  partial unique-together fire, visibility-scoped update, anon/missing-perm/permitted
  write-auth, hidden-Category relation + authorize-before-decode, multipart `Upload`,
  request-context `validate()`, G2 shape. Walked `tests/rest_framework/test_resolvers.py`
  (25 tests): it holds ONLY genuinely-unreachable internals (recursive-flattener nested
  shapes, raw-pk/non-Relay single+many decode, save-spy, save-time DRF-vs-Django+Integrity
  split, hermetic `get_serializer_kwargs`/H3 seams, grep-guard + recorded-strategy
  monkeypatch, sync+async+`SyncMisuseError`). **No reachable behavior is duplicated** — the
  rule is not inverted.
- **Config-assessment grep-guard.** `rest_framework/resolvers.py` references NEITHER
  `conf.settings` NOR `_resolve_globalid_strategy` (greps clean; zero ORM markers in the
  shadow overview — the ORM work is all in the promoted skeleton + `visible_related_object`).
  Locked by both the static `..._grep_guard` test AND the behavioral
  `..._consumes_recorded_strategy_after_strategy_resolver_fails` monkeypatch (raises if
  `_resolve_globalid_strategy` runs on the query path; decode still resolves from recorded
  `effective_globalid_strategy`).
- **F9 request-context proof.** `ItemSerializer.validate()` reads
  `self.context["request"].user` (NOT a `HiddenField(default=CurrentUserDefault())`),
  proven live by `..._object_validate_all_sentinel_and_request_context`.
- **DRY P1.5 byte-equivalence.** The model+form suites (`tests/mutations/`, `tests/forms/`)
  stay green UNCHANGED save the plan-licensed mechanical `_visible_related_object` →
  `visible_related_object` rename in `tests/forms/test_resolvers.py` — the 545-test run is
  the regression proof the promotions did not alter the model/form paths. `field_error`
  (P2.4) preserves the flat mapper's behavior (traced: dict-branch messages were already
  `str`; `str(m)` coercion is identity; non-field fallback unchanged). `_run_delete` and
  `_run_plain_form_pipeline_sync` correctly excluded (F6).
- **`mutations/fields.py` unchanged** (verified via `git diff --stat` — empty). The
  `test_fields.py` extension verifies the `038`-generalized factory exposes the serializer
  flavor (routes `resolve_sync` to `SerializerMutation.resolve_sync.__func__`, generates
  `data: ItemSerializerInput!`).
- **D8 carry-forward closed.** Both the `rest_framework/sets.py` `resolve_sync`/
  `resolve_async` overrides AND the `rest_framework/resolvers.py` bodies landed (Slice-2
  Box 1 now closed). Overrides are local-import + delegate, mirroring `forms/sets.py`.
- **Spec slice checklist:** all 7 `- [x]` boxes verified to have matching implementation
  in the diff. No over-ticks; no silently-unaddressed sub-checks.

### Temp test verification

No temp tests created. The authorize-before-decode security invariant, the save-once
guarantee, the DRF-vs-Django save-time split, and the G2 shape are each already pinned by
permanent tests in the diff (live for the consumer-reachable ones, package for the
internals), and I verified the invariant additionally by code-tracing the skeleton +
`git show HEAD:` byte-diff of the relocated preamble. No suspicion required a probe beyond
the 545-test green run.

### Notes for Worker 1 (spec reconciliation)

1. **`_relation_field_error` cross-flavor near-copy (DRY, integration-pass candidate).**
   Identical-body private helper in `forms/resolvers.py` + `rest_framework/resolvers.py`,
   and the message literal is also live in `mutations/resolvers.py::_raw_pk_relation_error`
   (a pre-existing two-site `036`+`038` pattern Slice 3 extends to a third). Spec manifest
   did NOT list it for promotion; not blocking. Candidate for the cross-slice DRY scan: a
   shared `relation_field_error(graphql_name)` ctor beside `field_error` would single-site
   the message text across all three flavors. Routed here for the integration pass's
   repeated-literal comparison (BUILD.md integration step 3).
2. **P1.1 helper name `visible_related_object` (public, no underscore)** landed per the
   plan's flag #1 (the spec import manifest's `_visible_related_object` is the
   carry-over-from-form-local form). Confirmed correct (it now crosses a module boundary,
   like the sibling public `utils/` helpers). No spec edit needed — agreeing with Worker
   2's note.
3. **Stale spec Status header** (spec lines 1-12 "Planned for 0.0.13") is Slice-4-owned per
   the F8 split; deliberately not churned here. No action this slice.

### Review outcome

`review-accepted` — every consumer-reachable resolver branch is earned live, the
authorize-before-decode security ordering is single-sited + byte-equivalent to HEAD +
proven by a distinct live test, the G2 query-shape test pins the load-bearing property
with a real-derived count, the DRY promotions (P1.5/P1.1/P2.4) are single-sited with the
model/form suites byte-equivalent (545 green), the config grep-guard + recorded-strategy
behavioral backstop both hold, `mutations/fields.py` is unchanged, and the public surface
carries no Slice-3 change (F1 preserved). The one DRY near-copy (`_relation_field_error`)
is a pre-existing-pattern Low finding routed to Worker 1's integration pass, not a blocker.

---

## Final verification (Worker 1)

Status set: **final-accepted**.

### 1. Spec slice checklist audit (every `- [x]` re-audited against the working-tree diff)

Re-audited all 7 `- [x]` boxes against the diff of the named files (`rest_framework/resolvers.py`,
`rest_framework/sets.py`, `mutations/resolvers.py`, `forms/resolvers.py`, `utils/querysets.py`,
`examples/fakeshop/apps/products`, `tests/rest_framework/test_resolvers.py`, `tests/mutations/test_fields.py`,
`examples/fakeshop/test_query/test_products_api.py`). All seven landed; **no over-tick, no silent un-tick**.

- **Box: `rest_framework/resolvers.py` sync + async pipeline (locate → authorize → decode → construct → validate → write → re-fetch).** LANDED. `resolve_serializer_sync` (`resolvers.py:521`) + `resolve_serializer_async` (`:574`) delegate to the shared `run_write_pipeline_sync` (P1.5). Authorize-before-decode single-sited in the skeleton (`mutations/resolvers.py::run_write_pipeline_sync` — `authorize_or_raise(... instance=instance)` at line 180 BEFORE `decode_step(instance)` at line 182). Dedicated serializer-field-keyed relation decoder (`_decode_relation_single`/`_relation_target_models`), recursive `serializer_errors_to_field_errors` (`:327`), DRF-vs-Django save-time split + `IntegrityError` as three branches, value-preserving once-only save via `save_or_field_errors`, `partial=True` update injection, request-context ownership in `_merged_serializer_kwargs`. `Upload` → `data` (FILE branch), no `files=` split.
- **Box: `mutations/fields.py` no change.** VERIFIED — `git diff --stat` empty; the `test_fields.py` extension verifies the 038-generalized factory exposes the serializer flavor (`tests/mutations/test_fields.py:334` routes `resolve_sync` + generates `data: ItemSerializerInput!`).
- **Box: products live serializer surface (same commit).** LANDED. `products/serializers.py::ItemSerializer` (ModelSerializer over `Item`: `category` PrimaryKeyRelatedField, `attachment` FileField, `validate_name`, object `validate()` reading `self.context["request"].user` — **F9 honored: a `validate()` branch, NOT a `HiddenField(default=CurrentUserDefault())`**; HiddenField appears only in the module docstring as an input-gen note). `products/schema.py`: `CreateItemViaSerializer`/`UpdateItemViaSerializer` (`Meta.serializer_class = serializers.ItemSerializer`, `operation = "create"`/`"update"`) + `create_item_via_serializer`/`update_item_via_serializer` `DjangoMutationField`s; `SerializerMutation` imported BY NAME (`schema.py:54`, explicit import list — not star). `config/settings.py`: `"rest_framework"` intentionally NOT in `INSTALLED_APPS` (Decision 13; TODO anchor removed, `NOTE(spec-039 Slice 3)` provenance left).
- **Box: live coverage is the primary harness.** LANDED — 15 new live tests in `test_products_api.py` covering every consumer-reachable branch (create/update happy, field + `"__all__"` envelopes, `categoryId` reverse-map, partial-preserve + partial unique-together fire, visibility-scoped update, write-auth, hidden-Category relation + authorize-before-decode, multipart `Upload`, request-context `validate()`, G2 SQL-shape).
- **Box: package-internal unreachable internals only.** LANDED — 25 tests in `tests/rest_framework/test_resolvers.py` (recursive-flattener nested shapes, raw-pk/non-Relay single + many decode, call-once save spy, save-time DRF-vs-Django split + `IntegrityError`, `get_serializer_kwargs` H3 seams, grep-guard + recorded-strategy monkeypatch, sync+async+`SyncMisuseError`). No reachable behavior duplicated across the two trees.
- **Box: DRY / reuse.** LANDED — see check 2.
- **Box: config-assessment grep-guard.** LANDED — `rest_framework/resolvers.py` references neither `conf.settings` nor `_resolve_globalid_strategy` (confirmed by grep); pinned by the static `test_resolvers_source_has_no_live_strategy_reads_grep_guard` (`test_resolvers.py:669`) AND the behavioral `test_relation_decode_consumes_recorded_strategy_after_strategy_resolver_fails` monkeypatch (`:685`).

**D8 close confirmed explicitly.** BOTH halves of the only deferred sub-part of Slice-2's Box 1 landed in this slice:
(a) `rest_framework/sets.py::SerializerMutation.resolve_sync` (`:421`) + `resolve_async` (`:444`) — local-import + delegate, mirroring `forms/sets.py:577-610`; AND
(b) the resolver bodies they delegate to: `rest_framework/resolvers.py::resolve_serializer_sync` (`:521`) + `resolve_serializer_async` (`:574`).
Slice-2 Box 1 is now closed.

### 2. DRY check across Slice 3 + prior accepted slices (0,1,2)

The three spec-mandated promotions are each **defined EXACTLY ONCE** (grep-verified):
- **P1.5** `run_write_pipeline_sync` — single def at `mutations/resolvers.py:113`; model `_run_create`/`_run_update`, `forms/resolvers.py::_run_modelform_pipeline_sync`, and the serializer body all ride it via `decode_step`/`write_step`. `_run_delete` + `_run_plain_form_pipeline_sync` correctly excluded (F6). Authorize-before-decode ordering single-sited.
- **P1.1** `visible_related_object` — single def at `utils/querysets.py:208`; form + serializer relation decoders both call it (`forms/resolvers.py:199`, `rest_framework/resolvers.py:227`). The remaining `_visible_related_object` mentions in source are docstring/comment provenance (citing the form-local origin), not duplicate definitions.
- **P2.4** `field_error` leaf ctor — single def at `mutations/resolvers.py:843`; `validation_error_to_field_errors` re-points through it (`:879`, `:881`) and the recursive `serializer_errors_to_field_errors` calls it (`rest_framework/resolvers.py:387`). HARD reuse of `NON_FIELD_ERROR_KEY` (imported `resolvers.py:116`, consumed `:368`) — no re-spelled `"__all__"`.

**Byte-equivalence of the model/form re-points:** proven by the 545-test focused run staying green with the model (`tests/mutations/`) + form (`tests/forms/`) suites UNCHANGED save the plan-licensed mechanical `_visible_related_object → visible_related_object` rename in `tests/forms/test_resolvers.py`. The skeleton's authorize-before-decode preamble is byte-identical to the HEAD form preamble (Worker 3 confirmed via `git show HEAD:` token-diff).

**The Low DRY finding — routing confirmed correct for the integration pass.** Verified at source: the `"Invalid id for relation {…!r}."` message literal is LIVE in 3 flavors:
- `forms/resolvers.py::_relation_field_error` (`:138`),
- `rest_framework/resolvers.py::_relation_field_error` (`:159`) — byte-identical body to the forms helper,
- `mutations/resolvers.py::_raw_pk_relation_error` (the literal at `:515`) — pre-existing 036.

The natural fix — a shared `relation_field_error(graphql_name)` ctor beside `field_error` touching all three flavors — spans the 036 model path, so it is exactly a **cross-slice integration-pass consolidation, not a Slice-3 in-scope fix** (the spec import manifest at line 2892 promotes the leaf `field_error` ctor via P2.4, which IS done; it does NOT list `_relation_field_error` for promotion). I judge it does NOT need to be fixed in-slice. **NOT setting `revision-needed` for it.** Recorded as a deferred item for the integration pass below.

### 3. Existing tests still pass (focused scope, `--no-cov`)

`uv run pytest examples/fakeshop/test_query/test_products_api.py tests/rest_framework tests/mutations tests/forms --no-cov` → **545 passed in 105.20s**. Green. No `--cov*` flag used.

### 4. Spec reconciliation

- **Planning flag #1 (P1.1 helper name `_visible_related_object` vs `visible_related_object`):** Decided **NO spec edit**. The spec writes the underscore form across ~12 sites — most are reuse-obligation prose (P1.1 row line 2767, Decision 8 lines 1603/1917/2144, slice-checklist lines 910/1010) or historically-accurate references to the *pre-existing form-local* private helper (line 2710 "`forms/resolvers.py`'s `_visible_related_object` exists because…", which WAS its name at HEAD). The implemented public name (no underscore) is the correct choice for a helper that now crosses a module boundary, matching the sibling public `utils/` helpers (`visibility_scoped_related_queryset`, `apply_type_visibility_async`). The import manifest line 2892 names a *reuse obligation* in prose ("the promoted `_visible_related_object` (P1.1)"), not a literal grep token, and the DoD grep contract is satisfied by the symbol being imported once + re-implemented nowhere (confirmed). Editing one prose line would leave the rest inconsistent and churning all ~12 mid-build for a non-contract naming detail is unwarranted. Worker 2 and Worker 3 both independently agreed; no spec edit.
- **Stale spec `Status:` header / "Planned for 0.0.13" body:** STILL Slice-4-owned per the build-wide F8 split. Deliberately not churned this pass.

**No spec edit made this pass** → `scripts/check_spec_glossary.py` not re-run (per the contract, the re-run is only required if the spec is edited).

### 5. Constraints re-verified

- No version bump (Decision 14): `__init__.py:37` = `0.0.12`, `pyproject.toml:4` = `0.0.12`. CONFIRMED.
- `__all__` unchanged — `SerializerMutation` NOT added (F1); the `__init__.py` diff is the Slice-2-accepted `__getattr__` lazy-export landing, NOT a Slice-3 change. CONFIRMED.
- `mutations/fields.py` unchanged (`git diff --stat` empty). CONFIRMED.
- `"rest_framework"` NOT in `INSTALLED_APPS` (Decision 13). CONFIRMED.

### Summary

Slice 3 ships the serializer resolver pipeline (sync + async) + the products live serializer surface in one commit, riding the promoted `run_write_pipeline_sync` (P1.5) / `visible_related_object` (P1.1) / `field_error` leaf ctor (P2.4) shared sites. The authorize-before-decode security ordering is single-sited and byte-equivalent to HEAD; every consumer-reachable resolver branch is earned by a real `/graphql/` request in `test_products_api.py`, with only genuinely-unreachable internals in `tests/rest_framework/test_resolvers.py` (no overlap). The D8 carry-forward (the only deferred sub-part of Slice-2 Box 1) is closed: both the `rest_framework/sets.py` overrides and the `rest_framework/resolvers.py` bodies landed. The model + form suites stay byte-equivalent (545-test green). No version bump, `__all__` unchanged, `mutations/fields.py` unchanged, `"rest_framework"` not installed. One Low DRY finding (`_relation_field_error` 3-site near-copy) routed to the integration pass.

### Deferred work for the integration pass + bld-final

- **`_relation_field_error` / `"Invalid id for relation …"` 3-site near-copy** (Slice-3 Worker-3 DRY finding, confirmed this pass): a shared `relation_field_error(graphql_name)` ctor beside `field_error` consolidating `forms/resolvers.py::_relation_field_error` + `rest_framework/resolvers.py::_relation_field_error` + the literal in `mutations/resolvers.py::_raw_pk_relation_error`. Spans the 036 model path → integration-pass DRY scan (BUILD.md integration step 3, repeated-literal comparison) + bld-final deferred catalog.
- **L1 vacuous-tautology assertion `tests/rest_framework/test_inputs.py:620`** (Slice-1 carry, re-confirmed left this pass): one-line test cleanup → integration pass.
- **Stale spec `Status:` header / "Planned for 0.0.13" body** (build-wide F8 split): the implemented-on-main Status edit → Slice-4 doc-wrap.

### Spec changes made (Worker 1 only)

None. No spec edit was warranted this pass (see check 4).

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
