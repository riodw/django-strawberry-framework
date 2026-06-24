# Build: Slice 3 — the form resolver pipeline + `DjangoMutationField` exposure

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Slice 3 checklist lines 389-443; Decision 5 lines 975-1048; Decision 8 lines 1449-1640; Decision 9 lines 1642-1664; Edge cases lines 1898-1970; Test plan lines 2050-2079; Impl-plan Slice-3 row line 1872)
Status: final-accepted

## Plan (Worker 1)

This slice ships the genuinely behavior-rich heart of build 038: the form resolver pipeline (`forms/resolvers.py`, new), the **promotion of the reused `036` pipeline helpers to a shared importable surface** (`mutations/resolvers.py`), and the **`DjangoMutationField` three-axis generalization** (`mutations/fields.py`) that actually fires the form pipeline. It also fills the four `resolve_sync`/`resolve_async` stubs in `forms/sets.py`, removes their `TODO(spec-038 Slice 3)` anchors, wires the `get_form_kwargs` waiver into the create-required guard, and deletes the transient `mutations/fields.py::_input_type_name` twin.

**DRY-FIRST is the gate for this slice.** The pipeline must CALL the promoted `036` helpers, not re-implement them. The relation decoder reuses the `036` *primitives* (`decode_model_global_id`, `_coerce_relation_pk_or_none`) but adds the **visibility-on-every-branch** query (the genuinely net-new security code). The net-new code is named explicitly in the DRY analysis: the relation decoder's visibility-on-every-branch, the decode `kind`-split, and the partial-update reconstruction. Everything else is reuse-by-call.

**No-model-flavor-regression is preserved through `mutations/fields.py`.** Each of the three axes already has its model-flavor seam default defined in Slice 2 (`DjangoMutation.input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async`, and `DjangoMutation` is still a member of the generalized target family). The generalization swaps a hardcoded model-path call for a `mutation_cls.<seam>` dispatch whose default IS today's model path — a `DjangoMutation` target routes to `mutations/resolvers.py`, names `mutations.inputs`, and passes the model target check exactly as before. The DRY analysis cites file:line for each swap and the test plan re-pins the model dispatch unchanged.

### DRY analysis

**Existing patterns reused (cite file:line — pin-at-write-time):**

- `django_strawberry_framework/mutations/resolvers.py::_locate_instance` (lines 564-585) — the visibility-scoped `update` locate (`apply_type_visibility_sync(target_type, initial_queryset(target_type), info).get(pk=node_id)`, `DoesNotExist` → `None`). **Called by name** from `forms/resolvers.py`'s update branch (Decision 8 step 2 / helper-reuse paragraph lines 1583-1606). A security contract — must not be re-implemented.
- `django_strawberry_framework/mutations/resolvers.py::_coerce_lookup_id` (lines 1066-1100) — the server-side `id:` decode + type-check against the target model (`decode_model_global_id` → `(pk, None)` or `(None, FieldError)`), reused for the `ModelForm` update's top-level `id:` (Decision 8 step 2 lines 1475-1486). The `id:` arrives as a raw GlobalID **string** (the `node(id: ID!)` contract), distinct from a relation `data:` field's Strawberry-coerced `GlobalID`.
- `django_strawberry_framework/mutations/resolvers.py::_not_found_error` (lines 1103-1105) — the `id`-keyed not-found `FieldError` (no existence leak). Reused for both the `_coerce_lookup_id` UNCOERCIBLE_PK return shape and the `_locate_instance` miss.
- `django_strawberry_framework/mutations/resolvers.py::_authorize_or_raise` (lines 997-1032) — the write-auth gate (`check_permission` → `False` → top-level `GraphQLError`, async-in-sync rejected). Reused for both flavors (before validation for `create`, after the locate for `update`). NOTE: it constructs `mutation_cls()` and reads `mutation_cls._primary_type.__name__` for the denial message — for the **plain form** `_primary_type is None` (Slice 2 `DjangoFormMutation._primary_type = None`), so the form pipeline must call `_authorize_or_raise` only via a path that does not dereference `_primary_type` for the plain flavor, OR the plain pipeline supplies its own auth-denial message. See Implementation discretion item "plain-form auth message".
- `django_strawberry_framework/mutations/resolvers.py::_refetch_optimized` (lines 734-775) — the by-pk-without-visibility optimizer re-fetch (`force_load=False` for create/update; the G2 gate keeps `select_related`/`prefetch_related`, suppresses `.only(...)` because the op is a MUTATION; routes through `apply_connection_optimization` with `mutation_payload_child_selections(slot)`). Reused unchanged by the `ModelForm` re-fetch (Decision 9 lines 1642-1664). Decision 9 explicitly says this comes for free — do NOT add new optimizer code.
- `django_strawberry_framework/mutations/resolvers.py::_build_payload` (lines 778-792) + `mutations/inputs.py::payload_object_slot` (line 539) — the uniform-slot envelope return (`payload_cls(**{slot: obj, "errors": errors})`). Reused by the `ModelForm` flavor. The plain form has NO object slot (a `{ ok errors }` payload), so it does NOT call `_build_payload` (which keys on `slot`); it instantiates its pinned two-field payload directly with `ok=` + `errors=`. See Implementation discretion "plain-form payload instantiation".
- `django_strawberry_framework/mutations/resolvers.py::_validation_error_to_field_errors` (lines 673-691) — the `ValidationError` → `FieldError` envelope mapper (uses `exc.error_dict`, keys `NON_FIELD_ERRORS` → `NON_FIELD_ERROR_KEY` = `"__all__"`). **Reused per Decision 8 step 4 (lines 1545-1556)**: the form pipeline calls `_validation_error_to_field_errors(ValidationError(form.errors.as_data()))` — `form.errors.as_data()` yields the `{field: [ValidationError, …]}` shape the mapper's `error_dict` branch already consumes, so the form's `NON_FIELD_ERRORS` bucket lands on `"__all__"` byte-identically to a model `full_clean()` failure. No parallel mapper.
- `django_strawberry_framework/mutations/resolvers.py::_save_or_field_errors` (lines 1057-1063) — `save()` the instance; map a race `IntegrityError` to the `"__all__"` envelope else `None` (Major-2). **Reused per Decision 8 step 5 (lines 1564-1576, P1)**: the form `form.save()` (ModelForm) and the plain-form `perform_mutate` default-save path run through this so a post-validation `IntegrityError` returns the same null-object/`{ok:false}` `FieldError` envelope, never a top-level `GraphQLError`. NOTE: `_save_or_field_errors(instance)` calls `instance.save()` — the form pipeline needs to wrap `form.save()` (no `instance` until the form saves) / `perform_mutate`, so the promotion must expose a callable-wrapping form (see "New helpers justified" #2 / Implementation discretion).
- `django_strawberry_framework/mutations/resolvers.py::_run_pipeline_sync` (lines 795-829) + `resolve_mutation_sync`/`resolve_mutation_async` (lines 1133-1170) — the `with transaction.atomic():` body + the async `sync_to_async(_run_pipeline_sync, thread_sensitive=True)` wrapper. The form pipeline MIRRORS this exact boundary shape (one `transaction.atomic()`, async runs the sync body in one `sync_to_async(thread_sensitive=True)`, spec Decision 8 lines 1583-1626) — it is a structural parallel, NOT a call (the form body differs), so it is a deliberate same-shape sibling, not duplication to consolidate (the `036` body dispatches on `meta.operation` to model branches the form pipeline does not share).
- `django_strawberry_framework/mutations/resolvers.py::_coerce_relation_pk_or_none` (lines 492-517) — coerce a raw pk through the target's pk field (`to_python` then `run_validators`; uncoercible/out-of-range → `None`). **A primitive the form relation decoder reuses for the raw-pk branch** (Decision 7 lines 1296-1306 / Decision 8 step 1 lines 1456-1474), so an uncoercible raw pk never reaches the `pk__in` query as a raw backend error.
- `django_strawberry_framework/relay.py::decode_model_global_id` (lines 202-225) + `GlobalIDDecode` (lines 174-186) — decode + type-check a `GlobalID` against the expected model, returning `DecodeResult(status, pk, resolved_type)`. **The Relay-branch primitive the form relation decoder reuses** (Decision 7 lines 1296-1306): a non-`OK` status → field-keyed `FieldError`; an `OK` status yields the coerced pk the visibility query then resolves to the visible object.
- `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` (line 150) / `initial_queryset` (line 108) / `model_for` (line 94) / `reject_async_in_sync_context` (line 58) — the visibility-query + sync-misuse-discipline primitives. The form relation decoder runs `apply_type_visibility_sync(related_type, initial_queryset(related_type), info, <recourse>)` on **every** branch (the net-new code below); the same primitives `_relation_visibility_error` (resolvers.py lines 445-489) already uses, so the visibility query shape is identical — but the form decoder must return the **visible object** (to apply `to_field_name`), not just confirm membership, so it cannot call `_relation_visibility_error` directly (which returns only an error/None). See "New helpers justified" #3.
- `django_strawberry_framework/registry.py::registry.get` (line 221) — resolve the related model's primary `DjangoType` (`registry.get(related_model)`). The decode basis MUST AGREE with the Slice-1 input id basis (carry-forward + Decision 7 lines 1205-1218): `column.related_model` for a **model-backed** relation (the `ModelForm` path, `forms/inputs.py::_field_triple_and_spec` line 382), `field.queryset.model` for a **model-less** plain-`Form` relation (`forms/inputs.py::_model_less_relation_annotation` line 339). The decoder resolves the same related primary type by the same basis so the input id type and the decode visibility query agree.
- `django_strawberry_framework/forms/converter.py` — the four `kind` constants (`SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE`, lines 58-61) + the `FormInputFieldSpec(input_attr, graphql_name, form_field_name, kind)` reverse-map record (lines 64-87). **The decode `kind`-split addresses these constants as the single source of truth** (no bare-string `kind` literals in `forms/resolvers.py`).
- `django_strawberry_framework/forms/inputs.py::build_form_input_class` (lines 421-475) returns `(input_cls, field_specs)` where `field_specs: list[FormInputFieldSpec]` is the per-field reverse map. **Slice 2's bind discards `field_specs`** (`DjangoModelFormMutation.build_input` / `DjangoFormMutation.build_input` return only `input_cls`, `forms/sets.py` lines 330-366 / 579-602). The decode NEEDS the spec list keyed by input attr — so Slice 3 must **stash the `field_specs` on the bound mutation** (e.g. `mutation_cls._input_field_specs`) at bind time. See "New helpers justified" #4 (the bind-stash seam) — this is the load-bearing plumbing that lets the decode reach the reverse map.
- `django_strawberry_framework/mutations/fields.py::_resolve` (lines 217-222) / `_synthesized_mutation_signature` (lines 148-191) / `_validate_mutation_target` (lines 70-92) — the three generalization sites. Each already has its Slice-2 seam default: `DjangoMutation.input_type_name(meta)` (= the relocated `_input_type_name` body) + `DjangoMutation.input_module_path` (= `INPUTS_MODULE_PATH`) + `DjangoMutation.resolve_sync`/`resolve_async` (= delegate to `mutations/resolvers.py`). The generalization re-points `fields.py` at the seams; the model default is byte-behavior-identical.
- `tests/mutations/test_fields.py` (the `_Query` / `CategoryT` / `ItemT` / `CreateItem` / `UpdateItem` / `DeleteItem` fixtures, lines 50-104; the registry-isolation harness; `test_non_mutation_target_raises_at_construction` line 233) — extend with a `DjangoModelFormMutation` + plain `DjangoFormMutation` target-accept test. `tests/forms/test_resolvers.py` (new) reuses the Slice-1/Slice-2 form fixtures (the `ModelForm` over products `Item`, plain `Form`, `_make_relay_target`/`_make_non_relay_target`, kwarg-requiring form) + the `tests/mutations/test_resolvers.py` resolver-harness shape (the `info` stub, the `_AllowAll`/deny permission fixtures, the mocked-`save()` `IntegrityError` test at line 614).

**New helpers justified (single responsibility each):**

1. **The helper-promotion mechanism — CHOSEN: drop the leading underscore on the reused subset in `mutations/resolvers.py` (the lighter edit), NOT a `mutations/_pipeline.py` lift.** Decision 8 (lines 1596-1606) offers two: (a) the lighter edit — drop the `_` on exactly the reused subset in `mutations/resolvers.py`; (b) the cleaner edit — lift them to a neutral `mutations/_pipeline.py` both modules import (mirroring the `0.0.9` set-family `utils/` lift). **Recommendation and decision: the underscore-drop.** Rationale: (i) the reused subset (`_locate_instance`, `_coerce_lookup_id`, `_not_found_error`, `_authorize_or_raise`, `_refetch_optimized`, `_build_payload`, `_validation_error_to_field_errors`, `_save_or_field_errors`) ALL still live in `mutations/resolvers.py` and are still called by the `036` model pipeline IN THE SAME MODULE — a `_pipeline.py` lift would move them out from under their primary same-module callers (`_run_create` / `_run_update` / `_run_delete` / `_validate_save_assign_refetch_payload`), forcing `mutations/resolvers.py` to import its own extracted helpers back, which reads worse, not better; (ii) the `0.0.9` set-family lift moved shared scaffold that had NO single owning module (two sibling families both needed it equally) — here `mutations/resolvers.py` is the unambiguous owner and `forms/resolvers.py` is a clean downstream consumer (a one-way `forms → mutations` import edge that already exists via `forms/sets.py` importing `mutations/sets.py`), so the directional dependency is honest; (iii) the underscore-drop is a rename-only diff (no moved bodies, no new module, no new import cycle risk), so the no-model-flavor-regression audit is a trivial "same body, public name" check. The promoted public names: `locate_instance`, `coerce_lookup_id`, `not_found_error`, `authorize_or_raise`, `refetch_optimized`, `build_payload`, `validation_error_to_field_errors`, `save_or_field_errors` (Worker 2: rename in place, update the `036` same-module call sites, keep `payload_object_slot` already-public from `mutations/inputs.py`). The module-private helpers the `036` model pipeline alone uses (`_decode_relations`, `_run_create`, `_unprovided_exclude`, `_integrity_error_field_errors`, etc.) STAY underscore-private — only the cross-module-consumed subset is promoted. Single responsibility: expose the reused-by-call surface without a new module.

   **`_save_or_field_errors` promotion wrinkle (Implementation discretion, resolved in-plan).** `_save_or_field_errors(instance)` today calls `instance.save()`. The form pipeline must wrap `form.save()` (ModelForm) and the plain-form `perform_mutate` save — neither is `instance.save()`. Two clean options: (a) promote it as-is (`save_or_field_errors(instance)`) and have `forms/resolvers.py` pass the form's saved instance pathway through a thin local that catches `IntegrityError` around the `form.save()` / `perform_mutate` call and returns `_integrity_error_field_errors()` — but that re-implements the catch, the exact duplication Decision 8 forbids; (b) **generalize the promoted helper to wrap a zero-arg callable** — `save_or_field_errors(save_callable)` runs `save_callable()` and maps `IntegrityError`, with the `036` model call site passing `instance.save` and the form call sites passing `form.save` / a `perform_mutate` bound method. **Recommendation: (b)** — it keeps ONE `IntegrityError` → envelope catch (the `036` `_integrity_error_field_errors` message policy, single-sourced) reused by all three save paths, which is precisely the "share, do not re-implement" Decision 8 mandates. `_integrity_error_field_errors` itself need NOT be promoted (it stays private; only `save_or_field_errors` is the public seam). Worker 2: if generalizing to a callable reads as churn on the `036` call site, the fallback is (a) with a SHARED `integrity_error_field_errors` promotion so the form catch reuses the message builder — but (b) is preferred (one catch, not two). Recorded as a discretion item with a strong recommendation.

2. **`forms/resolvers.py::resolve_form_sync` / `resolve_form_async` (the public entry points)** — the sync + async pipeline entries the Slice-2 `forms/sets.py` `resolve_sync`/`resolve_async` overrides delegate to (the model resolver's `resolve_mutation_sync`/`resolve_mutation_async` parallel). Single responsibility: the `with transaction.atomic():` form body (sync) + the `sync_to_async(thread_sensitive=True)` wrapper (async). The `ModelForm` flavor's entry takes `(mutation_cls, info, *, data, id)`; the plain flavor's takes `(mutation_cls, info, *, data)` (no `id` — `forms/sets.py::DjangoFormMutation.resolve_sync(cls, info, *, data)` has no `id` param). Worker 2 decides one entry pair that branches on `mutation_cls._primary_type is None` (plain) vs not, or two entry pairs — see Implementation discretion. The form body: decode → (update only) locate → authorize → construct+validate-once → write → (ModelForm) re-fetch → return payload.

3. **`forms/resolvers.py::_decode_form_relation_single` / `_decode_form_relation_multi` (the dedicated form relation decoder — the genuinely NET-NEW security code)** — Decision 7 lines 1286-1319 / Decision 8 step 1 lines 1456-1474, P1. Single responsibility: given a relation id (or id list), the related primary type, and `info`, return the **form-key value** (the visible object's `to_field_name` value) or a field-keyed `FieldError`. The body for each id: (i) if `isinstance(value, relay.GlobalID)` → `decode_model_global_id(value, related_model)`; a non-`OK` status → `FieldError` on the field's GraphQL name (the `036` AR-H4 contract); else take `result.pk`; (ii) else (raw pk) → `_coerce_relation_pk_or_none(related_model, value)`; `None` → field-keyed `FieldError`; (iii) **for BOTH branches**, resolve the **visible object** through the related primary `DjangoType.get_queryset` — `apply_type_visibility_sync(related_type, initial_queryset(related_type), info, <recourse>).filter(pk=<coerced pk>).first()`; a `None` (hidden / unseeable) → the SAME field-keyed `FieldError`, no existence leak (this is the visibility-on-every-branch that closes the raw-pk gap `_decode_relation_id_set` leaves, Decision 7 lines 1286-1306); (iv) convert the object to the form key via `to_field_name`: `obj.serializable_value(field.to_field_name)` when the form field's `to_field_name` is set, else `obj.pk` (Decision 7 lines 1308-1319 / Edge case lines 1949-1954, P2). The multi decoder maps this per element and returns the list under the form field name. This is **NOT** `_decode_relation_id_set` (which skips visibility on the raw-pk branch); it reuses the `036` *primitives* (`decode_model_global_id`, `_coerce_relation_pk_or_none`, `apply_type_visibility_sync`/`initial_queryset`) but resolves the OBJECT and visibility-checks every branch. Resolve the related model by the Slice-1-agreeing basis: for a model-backed relation, `mutation_cls`'s form `form_class._meta.model._meta.get_field(form_field_name).related_model`; for a model-less relation, the form field's `field.queryset.model`. Worker 2: the form field is reachable via `get_form_fields(form_class)[form_field_name]`, which carries both the `to_field_name` and (for model-less) the `queryset.model` — single-source the related-model basis off the form field + the optional backing column, mirroring `forms/inputs.py::_model_column_for` / `_model_less_relation_annotation`. A `SyncMisuseError` from an `async def get_queryset` propagates (the same discipline the `036` `_relation_visibility_error` inherits via `apply_type_visibility_sync`).

4. **`forms/resolvers.py::_decode_form_data` (the decode `kind`-split — NET-NEW)** — Decision 8 step 1 lines 1456-1474. Single responsibility: walk the bound input dataclass's provided fields (`UNSET` stripped), and using the per-field `FormInputFieldSpec` reverse map (the bind-stashed `mutation_cls._input_field_specs`), produce TWO form-field-keyed dicts: `provided_data` (scalars with the choice-enum member unwrapped to its raw value via the reused `036` `_raw_choice_value` discipline — Edge case lines 1926-1929; and relation values from the decoder #3, landed under `form_field_name`) and `provided_files` (the `FILE`-kind uploaded value, NEVER in `data=`). The `kind`-split (`SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE`) is the single point routing form-field names, visibility-checked relation values, and file uploads each to the right place. Returns `(provided_data, provided_files, error)`; a relation decode `FieldError` short-circuits. This is net-new because the `036` `_decode_relations` keys on MODEL attrs (`<field>_id` → pk for `setattr`/`Model(**…)`) and never splits files out — the form decode keys on FORM-field names and a bound Django form reads files from `files=`, not `data=`.

   **The bind-stash seam (#4 plumbing).** `build_form_input_class` returns `(input_cls, field_specs)`. The Slice-2 `build_input` overrides discard `field_specs`. Slice 3 must thread them onto the mutation: either (a) `build_input` also stashes `mutation_cls._input_field_specs = field_specs` (cleaner — the bind already stashes `_input_class` / `_payload_type_name`), or (b) the resolver re-derives the spec list by re-calling `build_form_input_class` at resolve time (wasteful, re-builds a class). **Recommendation: (a)** — stash the specs at bind. Worker 2: thread the `field_specs` out of `_cached_build_form_input` / `build_input` and assign `mutation_cls._input_field_specs` in `_bind_mutation` (model-flavor path, for `DjangoModelFormMutation`) and `_bind_form_mutation` (plain path). NOTE: `_cached_build_form_input` (`forms/sets.py` lines 133-174) currently caches only `input_cls`, discarding specs — extend the cache value to `(input_cls, field_specs)` so the specs survive the dedupe. This is a `forms/sets.py` edit beyond the four stubs — flag it (it IS in the slice's spirit: the decode reverse map is the P1 contract).

5. **`forms/resolvers.py` partial-update reconstruction (NET-NEW)** — Decision 8 step 4 lines 1516-1544, P1. Single responsibility: for a `ModelForm` `update`, reconstruct the full bound payload from the located instance overlaid with the provided fields: `data = {**model_to_dict(instance, fields=<the form's non-file field names>), **provided_data}`, `files = provided_files` only. `model_to_dict` (from `django.forms.models`) supplies FK as pk under the form field name and M2M as `[pk]` — so an omitted scalar/FK/M2M is preserved; an omitted file is preserved via the bound `form_class(instance=…)`'s `initial` (never re-supplied, never cleared). The `<the form's non-file fields>` filter excludes file fields (a file column's `model_to_dict` value is not a re-bindable `data=` value). The required-extra-non-model-field rule (Edge case lines 1945-1948, P2) is already encoded in the Slice-1 `<FormClass>PartialInput` (a required non-model extra field stays required in the input), so a required extra is always in `provided_data`; an optional one may be omitted. This is net-new (the `036` update does `setattr` on the located instance, not a `model_to_dict` payload reconstruction).

6. **`forms/resolvers.py` form construction via `get_form_kwargs` / `get_form` + the plain-form `perform_mutate`** — Decision 8 step 4 lines 1496-1513 / Decision 6 lines 1114-1131. Single responsibility: the overridable `get_form_kwargs(self, info, *, data, files, instance=None) -> dict` hook (default `{"data": data, "files": files}` + `"instance": instance` when non-`None`) and the coarser `get_form(self, info, *, data, files, instance=None)` hook (default `form_class(**self.get_form_kwargs(...))`), plus `perform_mutate(self, form, info) -> None` (default calls `form.save()` when present, else no-op). **These hooks land on the form bases in `forms/sets.py`** (they are instance methods a consumer overrides), not in `forms/resolvers.py` — the resolver CALLS `mutation_cls().get_form(...)` / `mutation_cls().perform_mutate(...)`. Worker 2: add `get_form_kwargs` / `get_form` / `perform_mutate` to the appropriate bases (`get_form_kwargs` / `get_form` on both flavors; `perform_mutate` on `DjangoFormMutation` per Decision 6 — the `ModelForm` flavor writes via `form.save()` directly). This is a `forms/sets.py` addition beyond the four stubs — flag it (the spec names these hooks as the construction seam the pipeline uses).

**The `get_form_kwargs` waiver wiring (carry-forward (b)).** Slice 2 ships `build_input` passing `guard_required=True` always with two `TODO(spec-038 Slice 3)` anchors (`forms/sets.py` `DjangoModelFormMutation.build_input` lines 350-354, `DjangoFormMutation.build_input` lines 591-592). Slice 3 wires the waiver: `guard_required = not _get_form_kwargs_overridden(cls)` where `_get_form_kwargs_overridden` checks whether the concrete mutation overrides `get_form_kwargs` / `get_form` (Decision 7 lines 1388-1394 — the guard can't know which fields the override injects, so it trusts the override). Worker 2: a `cls.get_form_kwargs is not <base>.get_form_kwargs` (or `get_form`) identity check on the base default is the simplest detection; remove both `TODO(spec-038 Slice 3)` anchors when wired. The Slice-1 guard already takes the `guard_required` parameter, so this is a one-line flip per `build_input` plus the detection helper.

**Duplication risk avoided:**

- **Re-implementing the `036` locate / authorize / re-fetch / payload / validation-mapper / save-mapper.** The naive form pipeline would re-spell each. Prevented by promoting the subset to public names (#1) and calling them; the `036` model pipeline and the form pipeline share ONE copy. Worker 3 confirms `forms/resolvers.py` has no body that re-implements a promoted helper.
- **Re-implementing the relation visibility query.** The form decoder needs the visible OBJECT (for `to_field_name`), which `_relation_visibility_error` does not return, so it cannot call that helper — but it MUST reuse the same primitives (`apply_type_visibility_sync` / `initial_queryset` / `registry.get` / `decode_model_global_id` / `_coerce_relation_pk_or_none`) so the query shape and coercion are identical. Prevented: the decoder (#3) is keyed on those primitives, not a parallel query. The net-new part is genuinely net-new (object-returning + visibility-on-every-branch), NOT a copy.
- **A second `IntegrityError` → envelope catch.** Prevented by the callable-wrapping `save_or_field_errors` (#1 wrinkle, option b) — one catch, three save paths.
- **A parallel `kind` literal set.** Prevented: the decode addresses the `forms/converter.py` `SCALAR`/`RELATION_SINGLE`/`RELATION_MULTI`/`FILE` constants, not bare strings.
- **Re-deriving the form input name / module in `fields.py`.** The `fields.py` generalization consults `mutation_cls.input_type_name(meta)` / `input_module_path` (the Slice-2 seams), deleting the transient `_input_type_name` twin — so there is ONE name-derivation body (the model default on `DjangoMutation`, overridden by the form bases). Prevented: do NOT keep `_input_type_name` "just in case".
- **Re-building the input class to recover `field_specs`.** Prevented by the bind-stash seam (#4) — the specs are stashed once at bind, read at resolve.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before editing.

1. **`mutations/resolvers.py` — promote the reused subset to public names (the underscore-drop, #1).** Rename in place: `_locate_instance` → `locate_instance` (lines 564-585), `_coerce_lookup_id` → `coerce_lookup_id` (lines 1066-1100), `_not_found_error` → `not_found_error` (lines 1103-1105), `_authorize_or_raise` → `authorize_or_raise` (lines 997-1032), `_refetch_optimized` → `refetch_optimized` (lines 734-775), `_build_payload` → `build_payload` (lines 778-792), `_validation_error_to_field_errors` → `validation_error_to_field_errors` (lines 673-691), and generalize `_save_or_field_errors` → `save_or_field_errors(save_callable)` wrapping a zero-arg callable (lines 1057-1063). Update EVERY same-module call site (`_run_create` line 899/906-916, `_run_update` lines 930-948, `_run_delete` lines 983-994, `_validate_save_assign_refetch_payload` lines 858-873, `_coerce_lookup_id`'s internal `_not_found_error` use line 1099) to the new public names; for `save_or_field_errors` pass `instance.save` at the `036` call site (line 867). `_integrity_error_field_errors` (lines 694-718) stays private. **No-regression: this is a rename-only diff** — the bodies are byte-unchanged except `save_or_field_errors`'s one-line `instance.save()` → `save_callable()`.

2. **`forms/resolvers.py` (new) — the form pipeline.** Module docstring framing the pipeline (`decode → (update) locate → authorize → construct+validate-once → write → (ModelForm) re-fetch → payload`), the one-`transaction.atomic()` / one-`sync_to_async` boundary, the dedicated visibility-on-every-branch relation decoder, the partial-update reconstruction, and the helper-reuse-by-call posture (citing Decisions 8/9). Ship:
   - Imports: the promoted public helpers from `..mutations.resolvers` (`locate_instance`, `coerce_lookup_id`, `not_found_error`, `authorize_or_raise`, `refetch_optimized`, `build_payload`, `validation_error_to_field_errors`, `save_or_field_errors`, plus `_coerce_relation_pk_or_none` if Worker 2 keeps it private and re-exports, OR promote it too — see discretion); `payload_object_slot` from `..mutations.inputs`; `decode_model_global_id`, `GlobalIDDecode` from `..relay`; `apply_type_visibility_sync`, `initial_queryset`, `model_for` from `..utils.querysets`; `registry` from `..registry`; `SCALAR`/`RELATION_SINGLE`/`RELATION_MULTI`/`FILE` from `.converter`; `get_form_fields` from `.inputs`; `_raw_choice_value` (promote or re-call) from `..mutations.resolvers`; `model_to_dict` from `django.forms.models`; `ValidationError` from `django.core.exceptions`; `transaction` from `django.db`; `sync_to_async`; `strawberry`.
   - `_decode_form_relation_single` / `_decode_form_relation_multi` (#3) — the visibility-on-every-branch object resolver + `to_field_name` conversion. A `SyncMisuseError` propagates.
   - `_decode_form_data` (#4) — the `kind`-split producing `(provided_data, provided_files, error)`, consulting `mutation_cls._input_field_specs`.
   - The partial-update reconstruction (#5) — `model_to_dict(instance, fields=<non-file form fields>)` overlaid by `provided_data`.
   - `resolve_form_sync(mutation_cls, info, *, data, id=UNSET)` / `resolve_form_async(...)` (#2) — the `with transaction.atomic():` body + the `sync_to_async(thread_sensitive=True)` wrapper. Branch on `mutation_cls._primary_type is None` (plain) vs not (ModelForm). The ModelForm body: decode → (update) `coerce_lookup_id` + `locate_instance` (miss → `not_found_error` payload) → `authorize_or_raise` → build form via `mutation_cls().get_form(info, data=, files=, instance=)` → `form.is_valid()` (false → `build_payload(payload_cls, slot, None, validation_error_to_field_errors(ValidationError(form.errors.as_data())))`) → `save_or_field_errors(form.save)` (non-None → null-object payload) → `refetch_optimized(primary_type, saved.pk, info, force_load=False)` → `build_payload(payload_cls, slot, obj, [])`. The plain body: decode → `authorize_or_raise` (see plain-auth discretion) → build form → `is_valid()` (false → `{ok:false, errors}` payload) → `save_or_field_errors(<perform_mutate bound>)` (non-None → `{ok:false, errors}`) → `{ok:true, errors:[]}` payload. Both inside ONE `transaction.atomic()`; both async via `sync_to_async(_body, thread_sensitive=True)`.
   - The payload-class lookup: mirror `mutations/resolvers.py::_payload_cls_for` (lines 1119-1130) — `getattr(forms.inputs, mutation_cls._payload_type_name)` (the form payload materializes in `forms.inputs` for the ModelForm? — VERIFY: `_bind_form_mutation` materializes the plain payload via `materialize_mutation_input_class` into `mutations.inputs`, `forms/sets.py` line 651; the ModelForm payload rides `_bind_mutation` into `mutations.inputs`, `mutations/sets.py` line 1036). So BOTH payloads live in `mutations.inputs` — the form resolver reads the payload from `mutations.inputs`, not `forms.inputs`. Worker 2: confirm and read the payload from `mutations.inputs` (the `data:` INPUT is in `forms.inputs`; the PAYLOAD is in `mutations.inputs`). This is a real divergence the resolver must get right.

3. **`forms/sets.py` — fill the four `resolve_*` stubs + wire the waiver + add the construction hooks + stash specs.**
   - `DjangoModelFormMutation.resolve_sync(cls, info, *, data, id)` (lines 391-407) → `from .resolvers import resolve_form_sync; return resolve_form_sync(cls, info, data=data, id=id)`; `resolve_async` (lines 409-422) → the async mirror. Remove the two `TODO(spec-038 Slice 3)` anchors.
   - `DjangoFormMutation.resolve_sync(cls, info, *, data)` (lines 615-623) → `resolve_form_sync(cls, info, data=data)` (no `id`); `resolve_async` (lines 625-628) → the async mirror. Remove the two `TODO(spec-038 Slice 3)` anchors.
   - Add `get_form_kwargs(self, info, *, data, files, instance=None)` + `get_form(self, info, *, data, files, instance=None)` to both bases (default bodies per #6); add `perform_mutate(self, form, info) -> None` to `DjangoFormMutation` (default `form.save()` if present else no-op, Decision 6 lines 1123-1126).
   - Wire the waiver: in both `build_input` overrides, replace `guard_required=True` with `guard_required=not _get_form_kwargs_overridden(cls)` (add the detection helper). Remove the two `TODO(spec-038 Slice 3)` waiver anchors (lines 350-354, 591-592).
   - Stash the reverse-map specs (#4 plumbing): extend `_cached_build_form_input` (lines 133-174) to return `(input_cls, field_specs)`; both `build_input` overrides assign `cls._input_field_specs = field_specs` (or the bind does it — Worker 2 picks the single stash point; `_bind_form_mutation` line 643-655 for the plain path, the model path's `build_input` for the ModelForm). Add `_input_field_specs: list | None = None` class attr to both bases (forward-compat, mirroring `_input_class`).

4. **`mutations/fields.py` — the three-axis generalization (Decision 5 lines 994-1020).**
   - **Axis (a) target check.** `_validate_mutation_target` (lines 70-92): generalize from `issubclass(mutation_cls, DjangoMutation)` to "a concrete member of the mutation/form family". The cleanest duck-typed check (Decision 5 line 998): a class carrying a non-`None` `_mutation_meta` AND the `resolve_sync`/`resolve_async` + `input_type_name`/`input_module_path` seams (i.e. the mutation/form protocol). `DjangoModelFormMutation` IS a `DjangoMutation` subclass (passes the old check), but the plain `DjangoFormMutation` is NOT — so the new check must accept any class with `_mutation_meta` + the seams. Worker 2: import the form bases is a circular-import risk (`forms/sets.py` imports `mutations/sets.py`; `mutations/fields.py` importing `forms/sets.py` would close a cycle) — so prefer the DUCK-TYPED check (a `_mutation_meta` attr + callable `resolve_sync`/`resolve_async`), NOT an `issubclass(form base)` check. Keep the abstract-base guard (`_mutation_meta is None` → the abstract-base message). The model target's behavior is unchanged (it still passes).
   - **Axis (b) resolver dispatch.** `_resolve` (lines 217-222): replace `resolve_mutation_sync`/`resolve_mutation_async` (imported line 66) with `mutation_cls.resolve_async(info, data=data, id=node_id)` / `mutation_cls.resolve_sync(info, data=data, id=node_id)` (the Slice-2 seams). **NOTE the `id` arg shape divergence**: `DjangoFormMutation.resolve_sync(cls, info, *, data)` has NO `id` param. So `_resolve` must pass `id=` ONLY when the operation declares it (create on a ModelForm has no `id`; the plain form never has `id`). Worker 2: the synthesized signature already omits `id` for create / plain (so `kwargs.get("id")` is `UNSET` and not in the GraphQL args), but `resolve_sync(info, data=, id=UNSET)` would still fail for the plain base's no-`id` signature. Cleanest: the seam methods on the model base + ModelForm take `id=`; the plain base's take only `data=`. `_resolve` should call `mutation_cls.resolve_sync(info, **call_kwargs)` where `call_kwargs` includes `id` only when the signature has an `id` parameter (inspectable via the synthesized signature's params, OR via `meta.operation in ("update", "delete")` for the model/ModelForm flavors and never for the plain `"form"` sentinel). Recommendation: build `call_kwargs = {"data": data}` and add `"id": node_id` when `mutation_cls._mutation_meta.operation in ("update", "delete")` — the plain form's `"form"` sentinel never adds `id`. State this in discretion. Remove the now-unused `resolve_mutation_async`/`resolve_mutation_sync` import (line 66).
   - **Axis (c) `data:` lazy-ref.** `_synthesized_mutation_signature` (lines 148-191): replace `_lazy_ref(_input_type_name(meta))` (line 183) with `_lazy_ref(mutation_cls.input_type_name(meta), mutation_cls.input_module_path)` — consult the seams. `_lazy_ref` (lines 136-145) currently hardcodes `INPUTS_MODULE_PATH`; generalize it to take a `module_path` parameter. The model default (`DjangoMutation.input_module_path = INPUTS_MODULE_PATH`) keeps `mutations.inputs`; the form bases override to `forms.inputs` (Slice 2, `forms/sets.py` lines 328, 486) — so the form `data:` ref resolves the form-derived input. The plain form's signature has NO `id` and a `data:` ref to its `<FormClass>Input` (the `"form"` sentinel shape); `_synthesized_mutation_signature` builds `data` for `operation in ("create", "update")` (line 182) — the plain form's `operation` is the `"form"` sentinel, so Worker 2 must extend the `data:`-build condition to include the `"form"` sentinel (a plain form HAS a `data:` arg, no `id`). Recommendation: build `data` when `meta.operation != "delete"` (create/update/form all take `data:`), and build `id` when `meta.operation in ("update", "delete")`. Verify against the `036` delete (id-only, no data) — `"delete"` keeps id-only.
   - **DELETE the transient `_input_type_name` twin (lines 95-133)** + its now-unused `editable_input_fields` / `mutation_input_type_name` imports (lines 63-65) + the `TODO(spec-038 Slice 3)` anchor (lines 98-104). The body is now byte-identical to `DjangoMutation.input_type_name(meta)` (Slice 2 relocated it), so `_synthesized_mutation_signature` consulting the seam single-sources it. Keep `INPUTS_MODULE_PATH` import ONLY if `_lazy_ref`'s default still references it; cleaner to drop the default and always pass `mutation_cls.input_module_path` (verify no other caller of `_lazy_ref` for the payload-return ref — line 189 uses `_lazy_ref(f"{mutation_cls.__name__}Payload")` with the PAYLOAD module, which for both flavors is `mutations.inputs`). Worker 2: the payload-return ref must name `mutations.inputs` (where both payloads materialize), so `_lazy_ref` for the return annotation passes `INPUTS_MODULE_PATH` (or `DjangoMutation.input_module_path` for the model flavor — but the form payload is ALSO in `mutations.inputs`, so the return ref always uses `mutations.inputs`, NOT `mutation_cls.input_module_path`). This is the subtle divergence: the `data:` ref uses `mutation_cls.input_module_path` (form input in `forms.inputs`), the PAYLOAD ref uses `mutations.inputs` (both payloads there). Pin this explicitly.

5. **Discharge the staged anchors.** After steps 3-4, grep `grep -rn 'TODO(spec-038 Slice 3)' django_strawberry_framework/` must be EMPTY (the four `resolve_*` stubs, the two `build_input` waiver anchors in `forms/sets.py`, and the `fields.py::_input_type_name` anchor are all removed). Worker 2 confirms in the build report.

### Test additions / updates

Tests live under `tests/forms/test_resolvers.py` (new) per the AGENTS.md mirror rule, plus an extension to `tests/mutations/test_fields.py`. System-under-test: the form pipeline run against the products `Item`/`Category` FK fixtures + the Slice-1/Slice-2 package-local form fixtures (`ModelForm` over `Item` with a `clean_<field>` + the `unique_item_per_category` constraint, plain `Form`, M2M fixture form, non-Relay-target form, `Upload`-field form, `to_field_name` form, kwarg-requiring form). Reuse the `tests/mutations/test_resolvers.py` resolver harness (the `info` stub, `_AllowAll`/deny permission fixtures, the mocked-`save()` `IntegrityError` shape at line 614) + the registry-isolation autouse fixture. Resolver tests call the seam (`MutationCls.resolve_sync(info, data=…, id=…)`) directly at the unit tier; the live `/graphql/` coverage is Slice 4.

**`tests/forms/test_resolvers.py`** (Test plan lines 2050-2074; Slice 3 checklist lines 435-443):

- **create / update happy paths** (ModelForm): a `create` writes + returns the `node`/`result` object; an `update` locates + writes + returns.
- **`form.errors` → envelope:** a `clean_<field>` failure → field-keyed `FieldError` (null object); a `clean()` / `unique_item_per_category` `NON_FIELD_ERRORS` error → the `"__all__"` sentinel (asserting the reused `validation_error_to_field_errors(ValidationError(form.errors.as_data()))` path keys it identically to a model `full_clean()`).
- **the decode split (load-bearing):** assert `_decode_form_data` produces `categoryId` → `{"category": <pk>}` in `provided_data` (NOT `{"category_id": …}` — the P1 form-key contract), and an `Upload` field → `provided_files` (NEVER `provided_data`). A scalar choice-enum member is unwrapped to its raw value.
- **relation visibility on EVERY branch (load-bearing, P1):** a HIDDEN target → the same field-keyed `FieldError` BEFORE the form, for **both** a Relay-`GlobalID` primary AND a **non-Relay raw-pk** primary, and for **both** `ModelChoiceField` (`relation_single`) AND `ModelMultipleChoiceField` (`relation_multi`) — four assertions (Relay×single, Relay×multi, rawpk×single, rawpk×multi). This is the raw-pk gap `_decode_relation_id_set` left; the test must drive the raw-pk branch through a non-Relay primary and assert the hidden row is rejected (proving the visibility-on-every-branch, not just the Relay branch). A wrong-model / uncoercible relation id → `FieldError`.
- **`to_field_name` (P2 #6):** a `ModelChoiceField`/`ModelMultipleChoiceField` with `to_field_name` set (or a `ForeignKey(to_field="slug")`) validates the decoded value by the target field (`obj.serializable_value(to_field_name)`), not pk — assert a valid GlobalID does NOT fail form validation, and the bound form's `to_python` resolves it.
- **write-time `IntegrityError` (P1):** a valid `form.save()` mocked to raise `IntegrityError` (and the plain-form `perform_mutate` save path) → the `FieldError` envelope (null object / `{ok:false}`), NOT a top-level `GraphQLError` — proving `save_or_field_errors` wraps the form save (mirror `tests/mutations/test_resolvers.py:614`).
- **`get_form_kwargs` / `get_form` hooks (P2):** an override injecting `user=` drives a form whose `__init__` requires it (the kwarg-requiring fixture); an override scoping a `ModelChoiceField.queryset` does NOT change the generated input shape (assert the input fields are unchanged from the no-override case).
- **partial-update reconstruction (load-bearing, P1):** an omitted scalar / FK / M2M preserved from the located instance (assert the saved row keeps the unprovided values); an omitted file preserved via the bound form's `initial`; a **required extra non-model field OMITTED → required error** while an **optional** extra field may be omitted (P2); `unique_item_per_category` validates on a one-field `name`-only change (the unchanged `category` comes from `model_to_dict`).
- **plain-form `ok` + `errors` payload:** a valid plain-form `is_valid()` → `{ok: true, errors: []}`; a failure → `{ok: false, errors: [FieldError, …]}`. The `perform_mutate(self, form, info)` default (calls `form.save()` if present, else no-op) + a consumer override (asserts the override runs on success, not on failure).
- **visibility-scoped `update` locate (P1):** a caller who cannot see a private `Item` gets a not-found `FieldError` on `id` (via `locate_instance`), indistinguishable from missing — no existence leak. A malformed / wrong-model `id:` → `id`-keyed `FieldError` before any lookup (via `coerce_lookup_id`).
- **write-auth denial vs success:** a deny permission → top-level `GraphQLError` (NOT a payload); an allow permission → the success payload.
- **sync + async:** the same scenario under `resolve_sync` and `await resolve_async` (the async path runs the body in one `sync_to_async(thread_sensitive=True)` call); the `SyncMisuseError` async-`get_queryset`-from-sync path (a relation decode / locate meeting an `async def get_queryset` raises).
- **G2 plan-shape (load-bearing, pin the property NOT observability — BUILD.md "Query-shape tests"):** assert the `ModelForm` re-fetch routes through `refetch_optimized` and the captured optimizer plan KEEPS `select_related`/`prefetch_related` and applies NO `.only(...)` (inspect `dst_optimizer_plan.select_related` / `.prefetch_related` / `.only` per the `tests/optimizer/test_extension.py:261/307` shape — assert `select_related`/`prefetch_related` are non-empty for a relation-selecting response AND `.only` is empty/None because the op is a MUTATION). A wire-only "the relation came back" assertion is NON-DISTINGUISHING (the value is identical whether optimized or N+1) — so pin the plan's `select_related` membership + the `.only` suppression directly. (The behavioral query-count tier already exists in products `test_products_api.py:953` for the `036` mutation; Slice 4 adds the form-flavor behavioral test. This unit-tier assertion pins that the form re-fetch is the SAME `036` G2 path.)

**`tests/mutations/test_fields.py`** (extend — Test plan lines 2075-2079):

- **the generalized target check accepts the mutation/form family:** a `DjangoMutationField(SomeModelFormMutation)` and a `DjangoMutationField(SomePlainFormMutation)` construct WITHOUT raising (the duck-typed `_mutation_meta` + seam check), while a non-mutation target still raises naming `DjangoMutationField` (re-pin `test_non_mutation_target_raises_at_construction` line 233 still passes).
- **model-flavor dispatch unchanged (no-regression):** a `DjangoMutation` target still routes `_resolve` to `mutation_cls.resolve_sync`/`resolve_async` whose default delegates to `mutations/resolvers.py` (assert the model `data:` ref names `mutations.inputs` and the resolver is the model pipeline — re-pin one representative case so the generalization did not regress the model path). The synthesized signature for a model create/update/delete is unchanged (`id`/`data` args per operation).

No temp/scratch tests anticipated; these are permanent package tests Worker 2 writes in the same change as the code. (Worker 3 may use `docs/builder/temp-tests/slice-3/` for a focused decode-split or visibility scratch test during review.)

### Static-inspection helper disposition (planning pass)

**Run.** BUILD.md "When to run the helper during build" requires Worker 1 to run `scripts/review_inspect.py` during planning when the plan adds logic to an existing `.py` file ≥150 source lines. Slice 3 adds logic to `mutations/resolvers.py` (1171 lines — the helper-promotion renames + the `save_or_field_errors` callable generalization) and `mutations/fields.py` (233 lines — the three-axis generalization + the `_input_type_name` deletion). Both run with `--output-dir docs/shadow` (no `--cov*`):

- `python scripts/review_inspect.py django_strawberry_framework/mutations/resolvers.py --output-dir docs/shadow` → exit 0. Quick scan: 38 symbols, **7 control-flow hotspots**, 7 executable Django/ORM markers, 1 repeated string literal. The promotion subset are all named symbols (`mutations/resolvers.py::_locate_instance` lines 564-585, `::_coerce_lookup_id` lines 1066-1100, `::_not_found_error` lines 1103-1105, `::_authorize_or_raise` lines 997-1032, `::_refetch_optimized` lines 734-775, `::_build_payload` lines 778-792, `::_validation_error_to_field_errors` lines 673-691, `::_save_or_field_errors` lines 1057-1063). The Django/ORM markers in the reused subset (`_locate_instance`'s `apply_type_visibility_sync`/`initial_queryset`/`.get(pk=…)`; `_refetch_optimized`'s `initial_queryset`/`apply_connection_optimization`/`.filter(pk=…)`) are the security/optimizer contracts the form pipeline inherits by call — no new ORM logic in the promotion (rename-only). The `_decode_relation_id_set` (lines 323-379) is the helper the form decoder DOES NOT reuse (the raw-pk visibility gap, Decision 7 lines 1290-1296). `_coerce_relation_pk_or_none` (lines 492-517) is the raw-pk primitive the form decoder DOES reuse.
- `python scripts/review_inspect.py django_strawberry_framework/mutations/fields.py --output-dir docs/shadow` → exit 0. The three generalization sites are named symbols (`mutations/fields.py::_validate_mutation_target` lines 70-92, `::_resolve` lines 217-222 inside `DjangoMutationField`, `::_synthesized_mutation_signature` lines 148-191) and the deletion target (`::_input_type_name` lines 95-133, carrying the `TODO(spec-038 Slice 3)` anchor at lines 98-104). The `_lazy_ref` (lines 136-145) hardcodes `INPUTS_MODULE_PATH` — generalized to a `module_path` param. No Django/ORM markers (the file is signature-synthesis only).

`forms/resolvers.py` is a NEW logic-bearing file → Worker 3 owns its helper run at review time (not the pure-class-definition skip). Shadow files are gitignored, read-only, non-canonical line numbers; cite original source via symbol-qualified paths in source/review.

### Implementation discretion items

Genuinely Worker-2-discretion (the design is settled; these are equivalent-shape / naming choices):

- **`save_or_field_errors` shape** — callable-wrapping `save_or_field_errors(save_callable)` (strong recommendation, one catch) vs. keeping it `instance`-based + a promoted `integrity_error_field_errors` the form catch reuses. Pick the callable form unless it reads as churn on the `036` call site; either way there must be ONE `IntegrityError` → envelope catch, not two.
- **`_coerce_relation_pk_or_none` / `_raw_choice_value` promotion** — promote them public alongside the subset, OR keep them private and have `forms/resolvers.py` import the private name (a one-symbol cross-module reach the spec sanctions for primitives, Decision 7 lines 1296-1306). Recommendation: promote `_raw_choice_value` if the form decode unwraps choice enums (it does), and reuse `_coerce_relation_pk_or_none` (private import is acceptable for this pure primitive, OR promote it — Worker 2 picks, keep it ONE copy).
- **One `resolve_form_*` entry pair branching on `_primary_type is None` vs two pairs (ModelForm / plain)** — either is fine; the plain entry has no `id` param. Keep the two flavors' bodies readable; do not over-DRY the ModelForm re-fetch into the plain path (the plain form has no re-fetch / no slot).
- **plain-form auth message** — `authorize_or_raise` reads `mutation_cls._primary_type.__name__` for the denial message (`mutations/resolvers.py` line 1031), which is `None` for the plain form. Worker 2 either (a) generalizes the message in `authorize_or_raise` to fall back to `mutation_cls.__name__` when `_primary_type is None`, or (b) the plain pipeline supplies its own auth-denial. Recommendation: (a) — a one-line `getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)` keeps ONE auth gate. The `operation` arg passed for the plain form: the `"form"` sentinel (or a literal `"submit"` — Worker 2's wording choice for the message).
- **plain-form payload instantiation** — the `{ ok errors }` payload is NOT slot-keyed, so the plain pipeline instantiates `payload_cls(ok=…, errors=…)` directly (NOT via `build_payload`, which keys on `slot`). Confirm the field names on the materialized plain payload (`ok` / `errors`) match `build_payload_type(object_type=None)`'s emitted fields (`forms/sets.py` line 646 / `mutations/inputs.py` `build_payload_type` None branch).
- **target-check generalization shape** — a duck-typed `_mutation_meta` + `resolve_sync`/`resolve_async` callable check (recommended, avoids the `fields.py → forms/sets.py` import cycle) vs. a shared marker base. Use the duck-typed check; do NOT import the form bases into `fields.py`.
- **`_resolve` `id`-kwarg gating** — pass `id=` only when `mutation_cls._mutation_meta.operation in ("update", "delete")` (the plain `"form"` sentinel and the model/ModelForm `create` never take `id`). Either an explicit operation check or a signature-param inspection; the operation check is simpler.

Items NOT at discretion (escalated / resolved in-plan, flagged for Worker 1 final-verification):
- **The `_input_field_specs` bind-stash** — REQUIRED (the decode reverse map). The stash point (`build_input` vs `_bind_mutation` / `_bind_form_mutation`) is discretion, but the spec list MUST survive `_cached_build_form_input`'s dedupe (extend the cache value to `(input_cls, field_specs)`). Without it the decode cannot produce a form-field-keyed payload (the P1 contract). This is a `forms/sets.py` edit beyond the four stubs.
- **The `get_form_kwargs` / `get_form` / `perform_mutate` hooks land on the form bases in `forms/sets.py`** (instance methods a consumer overrides), NOT in `forms/resolvers.py`. The resolver calls them. This is a `forms/sets.py` addition the spec names (Decision 8 lines 1496-1513 / Decision 6 lines 1123-1126) but the Slice-3 file list (`forms/resolvers.py`, `mutations/resolvers.py`, `mutations/fields.py`) does not enumerate — flagged for spec reconciliation (the hooks are clearly Slice-3 form-construction surface; `forms/sets.py` is already being edited for the four stubs + waiver).
- **The payload lives in `mutations.inputs` for BOTH flavors** (the ModelForm via `_bind_mutation`, the plain via `_bind_form_mutation`'s `materialize_mutation_input_class`); the INPUT (`data:`) lives in `forms.inputs`. The `fields.py` `data:` ref uses `mutation_cls.input_module_path` (= `forms.inputs`); the PAYLOAD-return ref uses `mutations.inputs`. The resolver reads the payload class from `mutations.inputs`. Worker 2 must not conflate the two namespaces.

### Spec slice checklist (verbatim)

- [x] Slice 3: the form resolver pipeline + `DjangoMutationField` exposure (per
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload)
  /
  [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path))
  - [x] [`forms/resolvers.py`][forms-resolvers]: the sync + async pipeline —
    **decode** the `data:` input via the reverse map into a form-field-keyed
    `provided_data` and a `provided_files` (files kept out of `data`), using the
    **dedicated form relation decoder** (NOT `036`'s `_decode_relation_id_set`): each
    relation id — `GlobalID` *or* **raw pk** — is type-checked, resolved to the
    **visible** object through the related primary `DjangoType.get_queryset` (closing
    the raw-pk visibility gap, P1#1), and converted by `to_field_name`
    (`obj.serializable_value(field.to_field_name)` else `obj.pk`, P2#6) before landing
    under the form field name; a hidden target → field-keyed `FieldError`
    ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-refetch--payload));
    (`update`) **locate** the row through the target type's
    [`get_queryset`][glossary-get_queryset-visibility-hook] (not-found → a `FieldError`
    on `id`, no existence leak); **authorize** via the inherited `check_permission` /
    `Meta.permission_classes`; **construct** the form once via the overridable
    `get_form_kwargs(info, *, data, files, instance=None)` hook (P2#3) — create:
    `form_class(**get_form_kwargs(info, data=provided_data, files=provided_files))`;
    **update (partial):** reconstruct `data = {**model_to_dict(instance, non-file
    fields), **provided_data}`, `files = provided_files`, then
    `form_class(**get_form_kwargs(info, data=, files=, instance=<row>))` (omitted
    fields preserved, P1); **validate** via `form.is_valid()` — a failure maps
    `form.errors` onto the [`FieldError` envelope][glossary-fielderror-envelope] (the
    form's `NON_FIELD_ERRORS` bucket → the `"__all__"` sentinel `036` froze, via the
    reused `_validation_error_to_field_errors(ValidationError(form.errors.as_data()))`)
    and returns a null-object payload; **write** via `form.save()` (`ModelForm`) /
    `perform_mutate` (plain form), **wrapped by the `036` `_save_or_field_errors`
    `IntegrityError` → envelope mapper** (P1, no top-level error at write); **re-fetch**
    the saved object by pk + optimizer-plan (the `ModelForm` flavor); **return** the
    `<Name>Payload` (`node` / `result` for the `ModelForm`, the pinned `ok` + `errors`
    for the plain form). The whole pipeline runs inside one `transaction.atomic()`, and
    the async path runs the sync body in one `sync_to_async(thread_sensitive=True)`
    call — the same boundary `036` set.
  - [x] [`mutations/fields.py`][mutations-fields]: generalize
    [`DjangoMutationField`][glossary-djangomutationfield] along three axes
    ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)) —
    (a) the `_validate_mutation_target` check (accept the mutation/form family, not
    only `issubclass(DjangoMutation)`); (b) the `_resolve` dispatch (call
    `mutation_cls.resolve_sync` / `resolve_async` instead of the hardcoded
    [`mutations/resolvers.py`][mutations-resolvers] import, so a form flavor routes to
    [`forms/resolvers.py`][forms-resolvers]); (c) the synthesized `data:` lazy ref
    (consult `mutation_cls.input_type_name(meta)` + `input_module_path` instead of the
    hardcoded model-column `_input_type_name` + `INPUTS_MODULE_PATH`). All three keep
    today's behavior for a `DjangoMutation` target.
  - [x] Package coverage: [`tests/forms/test_resolvers.py`][test-forms] — create /
    update happy paths, the `form.errors` → envelope (incl. a `NON_FIELD_ERRORS`
    `clean()` error → `"__all__"`), the **decode split** (`categoryId` → `{"category":
    pk}` in `data=`, an `Upload` → `files=`), the **partial-update reconstruction**
    (omitted scalar / FK / M2M / file preserved; `unique_item_per_category` on a
    one-field change), the **plain-form `ok` + `errors` payload + `perform_mutate`
    default/override**, the visibility-scoped `update` locate (hidden row →
    not-found), write-auth denial vs success, sync + async, and the G2 plan-shape (the
    `ModelForm` re-fetch keeps `select_related` / `prefetch_related`, no `.only(...)`).

---

## Build report (Worker 2)

### Files touched (grounded in `git status --short`)

Slice-intended:

- `django_strawberry_framework/forms/resolvers.py` (NEW) — the sync + async form
  pipeline. Public entries `resolve_form_sync` / `resolve_form_async` wrap
  `_run_form_pipeline_sync` (one `transaction.atomic()` each, the async via one
  `sync_to_async(thread_sensitive=True)`), branching on `_primary_type is None`
  (plain) vs not (ModelForm). Net-new helpers: `_decode_form_data` (the kind-split
  producing `(provided_data, provided_files, error)`), `_decode_form_relation_single`
  / `_decode_form_relation_multi` + `_visible_related_object` (visibility-on-every-branch),
  `_reconstruct_partial_data` (`model_to_dict` overlay), `_to_form_key_value`
  (`to_field_name`). DRY: locate / authorize / id-decode / re-fetch / payload /
  validation-mapper / save-mapper are the promoted `036` helpers, called.
- `django_strawberry_framework/mutations/resolvers.py` — promoted the 8 reused
  helpers to public names (underscore-drop, rename-only): `locate_instance`,
  `coerce_lookup_id`, `not_found_error`, `authorize_or_raise`, `refetch_optimized`,
  `build_payload`, `validation_error_to_field_errors`, `save_or_field_errors`
  (generalized to wrap a zero-arg `save_callable`). Also promoted `raw_choice_value`
  (the form decode unwraps choice enums). `authorize_or_raise` denial message now
  falls back to `mutation_cls.__name__` when `_primary_type is None` (plain flavor).
  All same-module call sites updated; the model pipeline behavior is byte-identical
  (only `save_or_field_errors`'s `instance.save()` → `save_callable()` body line +
  the `036` call site now passing `instance.save`).
- `django_strawberry_framework/mutations/fields.py` — the three-axis generalization:
  (a) `_validate_mutation_target` → duck-typed `_has_mutation_protocol` check (no
  `issubclass(DjangoMutation)`, no form-base import → no cycle); (b) `_resolve` calls
  `mutation_cls.resolve_sync`/`resolve_async`, gating `id=` on `operation != "form"`;
  (c) `_synthesized_mutation_signature` consults `input_type_name(meta)` +
  `input_module_path` for the `data:` ref (payload-return ref stays `INPUTS_MODULE_PATH`),
  builds `data` for `operation != "delete"`. Deleted the transient `_input_type_name`
  twin + its now-unused imports (`editable_input_fields`, `mutation_input_type_name`,
  `_OPERATION_INPUT_KIND`, `DjangoMutation`, `resolve_mutation_async/sync`).
  `_lazy_ref` takes a `module_path` param.
- `django_strawberry_framework/forms/sets.py` — filled the four `resolve_*` stubs
  (delegate to `forms/resolvers.py`); added module-level `_default_get_form_kwargs`
  / `_default_get_form` + `_form_kwargs_overridden`; both bases carry
  `get_form_kwargs` / `get_form`; the plain base adds `perform_mutate` +
  `check_permission`; wired the `guard_required` waiver into both `build_input`s;
  extended `_cached_build_form_input` (and the `_form_shape_build_cache` value) to
  `(input_cls, field_specs)` and stashed `cls._input_field_specs` at bind; added the
  `_input_field_specs` class attr to both bases. (Edits beyond the four stubs —
  flagged below for Worker 1.)
- `django_strawberry_framework/mutations/sets.py`, `mutations/permissions.py`,
  `relay.py` — single-line docstring updates from the symbol-rename sweep
  (`::_coerce_lookup_id` → `::coerce_lookup_id`, `::_authorize_or_raise` →
  `::authorize_or_raise`) + two stale Slice-2 staging-note docstrings refreshed to
  reflect Slice 3 landing.
- `tests/forms/test_resolvers.py` (NEW, 31 tests) + `tests/mutations/test_fields.py`
  (+2 tests) + the rename sweep in `tests/mutations/test_resolvers.py`,
  `tests/mutations/test_permissions.py`, `examples/fakeshop/test_query/test_products_api.py`
  (call sites + docstrings updated to the public helper names).

Out-of-scope (NOT my edits — pre-existing uncommitted Slice-1/2 work or concurrent):
`__init__.py`, `registry.py`, `types/finalizer.py`, `mutations/inputs.py`,
`tests/mutations/test_sets.py` (Slice-1/2 form-subsystem + seam work, untracked
`forms/` package); `docs/SPECS/spec-038-...md` (NOT edited by me); `docs/feedback.md`
+ the `docs/builder/bld-*.md` / `build-037*.md` deletions and other `build-038`
artifacts (other workers / concurrent). Left untouched. No `examples/fakeshop/db.sqlite3`
/ `KANBAN.html` changes.

### Tests added

- `tests/forms/test_resolvers.py` (31): create/update happy paths; `clean_<field>` →
  field-keyed error; `unique_item_per_category` `NON_FIELD_ERRORS` → `"__all__"`;
  decode split (`categoryId` → `{"category": pk}` form-key, `Upload` → `files=`,
  choice-enum unwrap); relation visibility on EVERY branch (Relay×single, Relay×multi,
  rawpk×single, rawpk×multi — all hidden → field error) + wrong-model id;
  `to_field_name` validates by target field; write-time `IntegrityError` (ModelForm
  `form.save` + plain `perform_mutate`) → envelope; `get_form_kwargs` override injects
  a kwarg + waives the create-required guard; partial-update preserves unprovided FK
  (constraint validates on a one-field change) + unprovided M2M + required-extra
  omitted → error; plain-form `ok` true/false + `perform_mutate` runs only on success;
  visibility-scoped update locate (hidden → not-found, malformed id → `id` error);
  write-auth denial (top-level error, naming model OR the plain mutation class) vs
  success; async create; sync-meeting-async-`get_queryset` → `SyncMisuseError`; G2
  plan-shape (`select_related == ("category",)` AND `only_fields == ()`).
- `tests/mutations/test_fields.py` (+2): the generalized target check accepts both
  form flavors; model-flavor dispatch unchanged (model `data:` names `mutations.inputs`,
  per-op arg shapes unchanged, model seam routes the model pipeline).

### Validation run

1. `uv run ruff format .` — clean (reformatted my edited files only).
2. `uv run ruff check --fix .` — `All checks passed!` (fixed a few RUF059 unused-unpack
   in the new test, plus 2 docstring-length + 1 ARG001 fixed by hand).
3. `git status --short` — classified above; no tool churn to revert (every modified
   file is either my slice-intended edit or pre-existing concurrent/Slice-1/2 work).
4. Focused tests (no `--cov*`): `tests/forms/test_resolvers.py` (31) +
   `tests/mutations/test_fields.py` (10) → **41 passed**. Regression sweep:
   `tests/mutations/{test_resolvers,test_permissions}.py` + `tests/forms/{test_sets,test_converter,test_inputs}.py`
   → all green (the rename + the seam dispatch did not regress the model pipeline).

### Implementation notes

- **`save_or_field_errors` generalized to a callable** (the plan's option (b)): one
  `IntegrityError` catch serves `instance.save` (036), `form.save` (ModelForm), and a
  `lambda: instance.perform_mutate(form, info)` (plain). `_integrity_error_field_errors`
  stays private.
- **Related-model basis single-sourced off the form field** (`form_field.queryset.model`):
  a `ModelChoiceField` carries `.queryset.model` for BOTH the model-backed FK (Django's
  auto-generated field) and the model-less `ModelChoiceField`, so one basis covers both
  flavors — no `_meta.model._meta.get_field(...)` vs `field.queryset.model` branch.
- **`_resolve` id-kwarg gate is `operation != "form"`**, NOT `in ("update","delete")`:
  the model/ModelForm `resolve_sync` requires `id` (no default), and the `036` model
  dispatch always passed `id=UNSET` for create — gating on `!= "form"` preserves that
  exactly and omits `id` only for the plain `"form"` sentinel (whose seam has no `id`
  param). Keeps the model dispatch byte-identical.
- **`get_form_kwargs` / `get_form` defaults are module-level functions assigned as
  instance-method class attrs** (`get_form_kwargs = _default_get_form_kwargs`) so the
  waiver's identity check (`cls.get_form_kwargs is not base.get_form_kwargs`) is a clean
  function-object comparison.
- **`_coerce_relation_pk_or_none` imported private** from `mutations/resolvers.py` (a
  one-symbol cross-module reach the plan sanctions for a pure primitive); `raw_choice_value`
  was promoted public (the form decode genuinely consumes it).
- **Unit-tier relation decode** reconstructs `relay.GlobalID.from_id(global_id_for(...))`
  (the type's actual encoding strategy) since the decode runs below Strawberry's argument
  coercion (a plain base64 string would take the raw-pk branch).
- **G2 plan-shape test** drives a real `schema.execute_sync` with the optimizer extension
  and inspects `ctx.dst_optimizer_plan` (the re-fetch publishes its plan to context via
  `apply_to`): `select_related == ("category",)` (relation kept) AND `only_fields == ()`
  (`.only` suppressed under MUTATION) — pins the load-bearing property, not observability.

### Notes for Worker 3

- No shadow files / overview used (the plan's `scripts/review_inspect.py` runs were
  Worker 1's planning-pass; `forms/resolvers.py`'s helper run is Worker 3's at review).
- The relation decoder reuses the `036` primitives by call and resolves the visible
  OBJECT (for `to_field_name`); it does NOT call `_relation_visibility_error` (which
  returns only an error/None). Confirm `forms/resolvers.py` has no body re-implementing a
  promoted helper.
- `docs/builder/temp-tests/slice-3/` was not used.

### Notes for Worker 1 (spec reconciliation)

- **`forms/sets.py` edits beyond the four `resolve_*` stubs** (in-scope per the plan,
  re-flagged): the `get_form_kwargs` / `get_form` / `perform_mutate` construction hooks,
  the plain-base `check_permission`, the `guard_required` waiver wiring, the
  `_input_field_specs` bind-stash (+ the `_cached_build_form_input` cache-value extension
  to `(input_cls, field_specs)`), and the `_input_field_specs` class attrs. The Slice-3
  file list (`forms/resolvers.py`, `mutations/resolvers.py`, `mutations/fields.py`) does
  not enumerate `forms/sets.py`; the spec (Decision 8 lines 1496-1513 / Decision 6 lines
  1123-1126) names these hooks as the construction seam, so they are clearly Slice-3 form
  surface. Reconcile the file list.
- **`mutations/sets.py` + `mutations/permissions.py` + `relay.py` docstring touches**:
  the symbol-rename sweep updated `::OldName` references (AGENTS.md mandate) and refreshed
  two stale Slice-2 staging-note docstrings (`_input_type_name` is deleted; the form
  `resolve_*` stubs are filled). These are docstring-only, beyond the enumerated file list
  but required by the rename.
- **`_resolve` id-gate is `operation != "form"`** (a small mechanically-obvious deviation
  from the plan's literal "`in ("update","delete")`"): gating on update/delete would break
  model + ModelForm CREATE (whose `resolve_sync` requires `id`, passed `UNSET` as the `036`
  dispatch always did). `!= "form"` is the correct gate and keeps the model dispatch
  byte-identical. Recorded for verification.
- **The `"form"` string literal in `mutations/fields.py::DjangoMutationField`** (the
  id-gate) is a bare literal, not the `forms/inputs.py::FORM` constant — importing that
  into `fields.py` risks the form-bases import cycle the duck-typed check avoids. The model
  flavor never uses `"form"`, so the literal is safe; flagged in case Worker 1 prefers a
  shared sentinel reachable without a cycle.

---

## Review (Worker 3)

Reviewed the Slice-3 artifact + working-tree diff against spec-038 Decisions 5/7/8/9,
the Slice-3 checklist, the named Edge cases, and the `tests/forms/test_resolvers.py` /
`tests/mutations/test_fields.py` test-plan bullets. Disentangled the cumulative diff via
the artifact `### Files touched` filter (the `mutations/sets.py` `DeclarationRegistry`
NamedTuple refactor in the working tree is **Slice-2** content, out of Slice-3 scope —
Slice-3's only `mutations/sets.py` touch is the `_authorize_or_raise`→`authorize_or_raise`
docstring rename). Ran `scripts/review_inspect.py` on `forms/resolvers.py` (new),
`mutations/resolvers.py`, and `mutations/fields.py` (all `--output-dir docs/shadow`, no
`--cov*`). Ran the focused suite `tests/forms/test_resolvers.py` +
`tests/mutations/{test_fields,test_resolvers,test_permissions}.py --no-cov` → **104 passed**.

### High:

None.

### Medium:

None.

### Low:

#### The `"form"` operation sentinel is a bare literal in `mutations/fields.py`, not the canonical `forms/inputs.py::FORM`

`mutations/fields.py::DjangoMutationField #"!= \"form\""` (the `takes_id` id-gate) and
`_synthesized_mutation_signature` (`operation in ("update", "delete")` / `!= "delete"`)
address the operation vocabulary as bare string literals. The canonical `"form"` sentinel
is `forms/inputs.py::FORM = "form"`. Worker 2's note #4 flags this as an import-cycle
avoidance. I verified the cycle claim: `mutations/fields.py` → `..forms.inputs` →
`..mutations.inputs` does NOT close a cycle (`mutations.inputs` never imports
`mutations.fields`), so the cycle concern is overstated for `forms/inputs.py::FORM`
specifically — the plan's cycle risk is real only for the form *bases* (`forms/sets.py`),
which the duck-typed target check correctly avoids. That said, this is genuinely Low: the
ENTIRE operation vocabulary (`"create"`/`"update"`/`"delete"`/`"form"`) is bare-literal in
`fields.py` today (no `OPERATION_*` constant module exists), so singling out `"form"` for a
cross-package import would be asymmetric and arguably worse for readability. The model
flavor never produces `"form"`, so the literal cannot misfire. Recommend deferring to a
cross-slice integration decision: either introduce one shared operation-sentinel surface
reachable without a cycle for the whole vocabulary, or leave the literals. Not a Slice-3
blocker. No test expectation change (behavior is correct as shipped).

### DRY findings

- **None blocking.** `forms/resolvers.py` calls the promoted `036` helpers — the static
  overview confirms **0 Django/ORM marker lines** in the module itself (locate / authorize /
  id-decode / re-fetch / payload / validation-mapper / save-mapper all execute inside the
  imported helpers). The only ORM-shaped code in the file is the genuinely net-new
  `_visible_related_object` visibility query (`apply_type_visibility_sync(initial_queryset(
  related_type), …).filter(pk=pk).first()`), which reuses the same `036` primitives by call
  (not a parallel query) and is correctly a sibling of `_relation_visibility_error` (it must
  return the OBJECT for `to_field_name`, which that helper does not). The `IntegrityError`
  catch is single-sourced through the callable-generalized `save_or_field_errors` (one catch,
  three save paths: `instance.save` / `form.save` / a bound `perform_mutate`). The `"form"`
  decode `kind`-split addresses the `forms/converter.py` `SCALAR`/`RELATION_SINGLE`/
  `RELATION_MULTI`/`FILE` constants, not bare strings.
- **Integration-deferred twins (confirmed NOT Slice-3 blockers):**
  `forms/sets.py::_form_shape_build_cache` ↔ `mutations/sets.py::_shape_build_cache` are
  deliberate near-twins in separate modules; the form cache VALUE is `(input_cls, field_specs)`
  vs the model `type`, so the form needs to carry the Slice-1 reverse-map specs through the
  per-shape dedupe — a naive merge is not free. `forms/inputs.py::normalize_form_field_sequence`
  ↔ the model `_normalize_field_sequence` twin is the Slice-1-accepted near-twin already
  deferred to integration (per my Slice-1 memory). Both are correct integration-pass DRY
  candidates, not Slice-3 defects.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` DOES show two additions
(`DjangoFormMutation`, `DjangoModelFormMutation` to both the re-export list and `__all__`).
**This is NOT a Slice-3 contribution.** Spec-038's impl-plan Slice-2 row (line 1871)
explicitly assigns `[__init__.py][init] (two exports)` to **Slice 2** (already accepted),
authorized by Decision 5. Worker 2 correctly classified `__init__.py` as out-of-scope
pre-existing Slice-2 working-tree state and did not touch it. Slice-3's three enumerated
source files (`forms/resolvers.py`, `mutations/resolvers.py`, `mutations/fields.py`) plus the
`forms/sets.py` fill add **no** new public exports. `__version__` is `0.0.11` (UNCHANGED —
the bump is Slice 5 only, confirmed at `__init__.py:37`). Public-surface check passes.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The `examples/fakeshop/test_query/test_products_api.py` touch is a single-line docstring
rename (`_coerce_lookup_id`→`coerce_lookup_id`) — a behavior-neutral rename-sweep call-site
update per the AGENTS.md `::OldName` symbol-rename mandate, NOT the Slice-4 live form tests
(those are not in this diff). Confirmed behavior-neutral (docstring only; the test body and
assertions are untouched). The `mutations/sets.py`/`permissions.py`/`relay.py` Slice-3
touches are likewise single-line docstring/comment rename refs only. No KANBAN / GLOSSARY /
spec-archival surfaces touched by Slice 3.

### What looks solid

- **The relation-visibility security contract holds on EVERY branch.**
  `forms/resolvers.py::_decode_form_relation_single` resolves the visible object through
  `_visible_related_object` (the related primary `DjangoType.get_queryset` via
  `apply_type_visibility_sync(initial_queryset(...))`) for **both** the Relay-`GlobalID`
  branch (after `decode_model_global_id` type-check) AND the raw-pk branch (after
  `_coerce_relation_pk_or_none` coerce) — closing the gap `036`'s `_decode_relation_id_set`
  leaves on raw pk. `_decode_form_relation_multi` maps the single decoder per element, so
  every M2M member is visibility-checked on its own branch. A hidden / wrong-model /
  uncoercible id → the uniform field-keyed `_relation_field_error(graphql_name)` (no
  existence leak). The four right-path tests (`test_relation_visibility_{relay,raw_pk}_{single,
  multi}_hidden_rejected`) each create a **real** related row then hide it via `get_queryset`
  returning `qs.none()`, and the two raw-pk tests use a **non-Relay** (`primary=True`, no
  `relay.Node`) primary so the wire value is a genuine raw pk taking the raw-pk branch — they
  exercise the visibility query, not a fallback. `test_wrong_model_relation_id_yields_field_error`
  pins the AR-H4 wrong-model case.
- **No model-flavor regression.** The 8-helper promotion (`mutations/resolvers.py`) is a
  pure underscore-drop: every body is byte-unchanged except `save_or_field_errors`'s single
  `instance.save()`→`save_callable()` line, with the `036` call site now passing
  `instance.save`. The `authorize_or_raise` denial message gained a
  `getattr(_primary_type, "__name__", mutation_cls.__name__)` fallback (one auth gate serves
  both flavors). `test_model_flavor_dispatch_unchanged` pins the model `data:` ref names
  `mutations.inputs`, the per-op arg shapes are unchanged (`{data: ItemInput!}` /
  `{id: ID!, data: ItemPartialInput!}` / `{id: ID!}`), and the model seam `resolve_sync` is
  `DjangoMutation.resolve_sync` → the model pipeline.
- **Worker 2's note #3 (the `operation != "form"` id-gate) is CORRECT — verified.**
  `DjangoMutation.resolve_sync(cls, info, *, data, id)` (mutations/sets.py:631) declares `id`
  keyword-only with NO default; so does `DjangoModelFormMutation.resolve_sync`. Gating on
  `in ("update","delete")` would call `resolve_sync(info, data=…)` for a model/ModelForm
  CREATE → `TypeError: missing keyword-only argument 'id'`. `!= "form"` passes `id=UNSET` for
  every model/ModelForm op (byte-identical to the `036` model dispatch, which always passed
  `id=`) and omits `id` only for the plain `"form"` sentinel (whose seam has no `id` param).
- **The decode `kind`-split + file routing is correct.** `_decode_form_data` produces FORM-
  field-keyed `provided_data` (relations land under `form_field_name`, not `<attr>_id`;
  choice enums unwrapped via `raw_choice_value`) and `provided_files` (FILE kind → `files=`,
  never `data=`). `test_decode_split_relation_lands_under_form_key_not_id_attr` /
  `test_decode_split_upload_lands_in_files_never_data` / `test_decode_unwraps_choice_enum`
  pin all three. `to_field_name` is honored via `_to_form_key_value`
  (`obj.serializable_value(to_field_name)` else `obj.pk`) — `test_to_field_name_relation_validates_by_target_field`
  proves the bound `ModelChoiceField(to_field_name="name")` resolves the decoded value.
- **Partial-update reconstruction is correct.** `_reconstruct_partial_data` overlays
  `provided_data` on `model_to_dict(instance, fields=<non-file form fields>)`; FK preserved
  as pk, M2M as `[pk]`, file fields excluded (preserved via the bound `instance=` initial).
  `test_partial_update_preserves_unprovided_fk_and_validates_constraint` proves the unchanged
  `category` comes from `model_to_dict` and `unique_item_per_category` fires on `"__all__"`
  for a name-only change; `test_partial_update_preserves_unprovided_m2m` proves the omitted
  M2M survives; `test_required_extra_field_omitted_on_update_raises_field_error` proves a
  required non-model extra stays required.
- **IntegrityError → envelope, locate via get_queryset, write-auth, one atomic, async, SyncMisuseError.**
  `save_or_field_errors(form.save)` / `save_or_field_errors(lambda: instance.perform_mutate(form, info))`
  map a write-time `IntegrityError` to the field envelope (tests cover both flavors); the
  update locate runs through `locate_instance` (hidden → `id`-keyed not-found,
  `test_update_hidden_row_is_not_found_no_existence_leak`); a malformed `id:` → `id`-keyed
  error before lookup via `coerce_lookup_id`; write-auth denial raises a top-level
  `GraphQLError`; both bodies run inside one `transaction.atomic()`; `resolve_form_async`
  wraps the single sync body in one `sync_to_async(thread_sensitive=True)`; an async
  `get_queryset` met in a sync pipeline raises `SyncMisuseError`
  (`test_*_sync_meeting_async_get_queryset`).
- **The G2 plan-shape test pins the load-bearing property, not observability.**
  `test_modelform_refetch_keeps_select_related_and_suppresses_only` drives a real
  `schema.execute_sync` (selection `node{ id name category{ name } }`) through the optimizer
  extension, captures `ctx.dst_optimizer_plan`, and asserts BOTH `plan.select_related ==
  ("category",)` (the relation is KEPT) AND `plan.only_fields == ()` (`.only(...)` SUPPRESSED
  because the op is a MUTATION). It asserts the actual plan shape, not a wire-only "the
  relation came back" (which would be non-distinguishing). The re-fetch routes through the
  shared `refetch_optimized(force_load=False)` — the same `036` G2 path, no new optimizer code.
- **Duck-typed target generalization avoids the import cycle.** `_has_mutation_protocol`
  recognizes the family by `_mutation_meta` + callable `resolve_sync`/`resolve_async`/
  `input_type_name` + non-`None` `input_module_path` (no `issubclass(DjangoMutation)`, no
  form-base import). `test_generalized_target_accepts_modelform_and_plain_form_family`
  constructs both flavors without raising; `test_non_mutation_target_raises` /
  `test_non_class_target_raises` / `test_abstract_base_target_raises` still pass.
- **All four staged `TODO(spec-038 Slice 3)` anchor sites discharged** — grep is empty
  across `django_strawberry_framework/` + `tests/` (the four `resolve_*` stubs, the two
  `build_input` waiver anchors, the `fields.py::_input_type_name` twin). The rename sweep
  is complete across all three test trees (no stale `::_OldName` symbol refs, no bare
  private-name calls to the promoted helpers outside `mutations/resolvers.py`).

### Temp test verification

- No temp tests under `docs/builder/temp-tests/slice-3/` were needed. The shipped
  `tests/forms/test_resolvers.py` already drives the raw-pk visibility path through a
  non-Relay primary and the partial-update reconstruction directly via `schema.execute_sync`,
  and I confirmed both are right-path by reading the fixtures and running the focused suite
  (104 passed). No `db.sqlite3` / `KANBAN.html` dirtied.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low, optional): the `"form"` operation literal.** Worker 2's note #4 cites a
  form-bases import cycle as the reason for the bare `"form"` literal in `mutations/fields.py`.
  I verified the cycle does NOT exist for `forms/inputs.py::FORM` specifically (the cycle is
  real only for the form *bases*). The whole operation vocabulary is bare-literal in `fields.py`
  today, so this is a cross-slice consistency question, not a Slice-3 fix. Resolution paths for
  the integration pass: (1) leave the literals (the model flavor never emits `"form"`, behavior
  is correct); (2) introduce one shared operation-sentinel surface reachable without a cycle for
  the entire `create`/`update`/`delete`/`form` vocabulary. Recommend (1) unless the integration
  pass wants the whole vocabulary constant-ized. NOT a blocker.
- **Worker 2's notes #1 (`forms/sets.py` edits beyond the four stubs) and #2 (docstring
  rename-sweep touches) are confirmed in-scope/required.** The `get_form_kwargs`/`get_form`/
  `perform_mutate`/`check_permission` hooks + the `guard_required` waiver + the
  `_input_field_specs` bind-stash (+ `_cached_build_form_input` returning `(input_cls,
  field_specs)`) are the spec-named construction seam (Decision 8 step 4 / Decision 6) and the
  P1 reverse-map plumbing — Slice-3 cannot ship without them. The file-list reconciliation
  (`forms/sets.py` + the three docstring-touched modules absent from the enumerated Slice-3
  list) is a clean spec-LIST reconciliation for Worker 1, not a defect.
- **spec-038:1568 prose** references `mutations/resolvers.py::_save_or_field_errors` (the
  pre-promotion private name) inside the sentence describing the promotion itself. Harmless
  (the spec narrates the rename), but Worker 1 may optionally refresh it to the public
  `save_or_field_errors` for symbol-ref accuracy. Not a finding.

### Review outcome

`review-accepted`. The relation-visibility security contract holds on every branch
(Relay×{single,multi}, raw-pk×{single,multi}, all right-path-tested); the no-model-flavor-
regression gate holds (rename-only promotion + verified `!= "form"` id-gate + model-dispatch-
unchanged test); the G2 test pins the load-bearing property (`select_related` kept, `.only`
suppressed, real plan inspected); every verbatim checklist box matches the diff; the public
surface is unchanged by Slice 3 and `__version__` stays `0.0.11`. Zero High, zero Medium; one
Low (`"form"` literal) deferred to the integration pass, escalated to Worker 1 as optional.

---

## Final verification (Worker 1)

### Summary

`final-accepted`. Audited the Slice-3 diff (`forms/resolvers.py` NEW, `mutations/resolvers.py`
8-helper underscore-drop promotion + `save_or_field_errors` callable generalization,
`mutations/fields.py` 3-axis generalization + `_input_type_name` twin deletion, `forms/sets.py`
stub-fill/hooks/waiver/`_input_field_specs` stash, the `mutations/sets.py`/`permissions.py`/`relay.py`
docstring rename-sweep, `tests/forms/test_resolvers.py` NEW +31, `tests/mutations/test_fields.py` +2,
the call-site rename sweep) against spec-038 Decisions 5/7/8/9 and the verbatim checklist.

**Spec slice checklist audit — all `- [x]` truly landed, no over-ticks, no silent un-ticks.**
- Top-level Slice-3 box: the resolver pipeline + `DjangoMutationField` exposure both shipped.
- `forms/resolvers.py` box: the sync+async pipeline (`_run_modelform_pipeline_sync` /
  `_run_plain_form_pipeline_sync` under one `transaction.atomic()` each, `resolve_form_async` wrapping
  the single sync body in one `sync_to_async(thread_sensitive=True)`), the visibility-on-every-branch
  decoder (`_decode_form_relation_single`/`_multi` → `_visible_related_object`), the `kind`-split decode
  (`_decode_form_data`), `to_field_name` (`_to_form_key_value`), the partial-update reconstruction
  (`_reconstruct_partial_data`), the `form.errors` → `"__all__"` envelope via reused
  `validation_error_to_field_errors(ValidationError(form.errors.as_data()))`, the `save_or_field_errors`
  write wrap, and the `refetch_optimized` G2 re-fetch — all present and verified line-by-line.
- `mutations/fields.py` box: all three axes confirmed in the diff — (a) duck-typed `_has_mutation_protocol`
  (no `issubclass(DjangoMutation)`, no form-base import → no cycle); (b) `_resolve` calls
  `mutation_cls.resolve_sync`/`resolve_async`, gating `id=` on `operation != "form"`; (c) `data:` ref via
  `input_type_name(meta)` + `input_module_path`, payload-return ref stays `INPUTS_MODULE_PATH`. The
  transient `_input_type_name` twin + its now-unused imports deleted.
- Test-coverage box: 31 `test_*` in `tests/forms/test_resolvers.py` (incl. all four
  relation-visibility branches, the decode split, partial-update preservation, plain-form `ok`/`errors`,
  `perform_mutate` default/override, visibility locate, write-auth, sync+async, G2 plan-shape) + 2 in
  `tests/mutations/test_fields.py` (generalized target accepts both flavors; model-flavor dispatch
  unchanged). Every named contract has a matching test.

**Gate (a) — relation-visibility on EVERY branch (independently confirmed).** Read
`forms/resolvers.py::_decode_form_relation_single`: the Relay-`GlobalID` branch (`decode_model_global_id`
type-check → `result.pk`) AND the raw-pk branch (`_coerce_relation_pk_or_none` coerce) BOTH fall through
to `_visible_related_object(related_model, pk, info)`, which runs
`apply_type_visibility_sync(related_type, initial_queryset(related_type), info, _FORM_ASYNC_RECOURSE).filter(pk=pk).first()`
and returns `None` (→ uniform field-keyed `FieldError`, no existence leak) for a hidden/missing row.
`_decode_form_relation_multi` maps the single decoder per element, so every M2M member is checked on its
own branch. This closes the raw-pk gap `036`'s `_decode_relation_id_set` leaves. The four right-path
tests (`test_relation_visibility_{relay,raw_pk}_{single,multi}_hidden_rejected`) drive a real hidden row;
the raw-pk pair uses a non-Relay primary so the wire value genuinely takes the raw-pk branch. Security
contract holds on all four branches.

**Gate (b) — no-model-flavor-regression (independently confirmed).** The `mutations/resolvers.py`
promotion is a pure underscore-drop: `git diff` shows byte-unchanged bodies for the 8 helpers except
`save_or_field_errors`'s single `instance.save()` → `save_callable()` line (the `036` call site now
passes `instance.save`) and `authorize_or_raise`'s denial-message `getattr(_primary_type, "__name__",
mutation_cls.__name__)` fallback (one auth gate, both flavors). The `mutations/fields.py` `_resolve`
id-gate is `operation != "form"`, NOT `in ("update","delete")` — independently verified correct: model
`DjangoMutation.resolve_sync(cls, info, *, data, id)` declares `id` keyword-only with NO default
(`mutations/sets.py:631-637`), so `in ("update","delete")` would raise `TypeError` on model/ModelForm
CREATE; `!= "form"` passes `id=UNSET` for every model op (byte-identical to the `036` dispatch) and omits
`id` only for the plain `"form"` sentinel (whose seam has no `id` param). `test_model_flavor_dispatch_unchanged`
re-pins the model `data:` ref names `mutations.inputs`, per-op arg shapes unchanged, model seam routes the
model pipeline. The 3-axis generalization keeps today's `DjangoMutation` dispatch intact.

**DRY check (Slices 1–3).** `forms/resolvers.py` CALLS the promoted `036` helpers (imported from
`..mutations.resolvers`); the only ORM-shaped code in the module is the genuinely net-new
`_visible_related_object` visibility query (reuses `apply_type_visibility_sync`/`initial_queryset`
primitives by call, plus a `_default_manager.filter(pk=pk).first()` fallback for a no-primary-type raw-pk
relation) — no re-implementation of locate/authorize/refetch/payload/validation/save. The `IntegrityError`
catch is single-sourced through callable-`save_or_field_errors` (one catch, three save paths). The
integration-pass DRY candidates are correctly deferred, NOT Slice-3 blockers: `_form_shape_build_cache`
(value `(type, list)`, carries the Slice-1 reverse-map `field_specs`) ↔ `_shape_build_cache` (value
`type`) is a not-free merge in separate modules; `normalize_form_field_sequence` ↔
`mutations/sets.py::_normalize_field_sequence` is the Slice-1-accepted near-twin; the `"form"` literal is
a cross-slice operation-vocabulary consistency call (whole vocab is bare-literal in `fields.py`; model
flavor never emits `"form"`). None are new duplication introduced by Slice 3.

**Focused tests:** `uv run pytest tests/forms/ tests/mutations/ --no-cov` → **282 passed** (no `--cov*`).

**Staged-anchor sweep:** `grep -rn 'TODO(spec-038 Slice 3)' django_strawberry_framework/ tests/` → empty
(the four `resolve_*` stubs, the two `build_input` waiver anchors, the `fields.py::_input_type_name`
anchor all discharged). `__version__` is `0.0.11` (bump is Slice 5 only). No `db.sqlite3` / `KANBAN.html`
touched.

### Spec changes made (Worker 1 only)

All edits to `docs/SPECS/spec-038-form_mutations-0_0_12.md`; `scripts/check_spec_glossary.py` re-run after
edits → `OK: 31 terms` (exit 0).

1. **Lines 1568, 1578, 1585-1592 (Decision 8 helper-reuse prose) — refresh to public helper names.**
   Slice 3 (helper promotion). The pipeline now CALLS the public, underscore-dropped helpers; refreshed
   `::_save_or_field_errors` → `::save_or_field_errors` (line 1568), `` `036` `_refetch_optimized` `` →
   `refetch_optimized` (line 1578), and the "calls the shipped helpers by name" list
   (`_locate_instance`/`_coerce_lookup_id`/`_not_found_error`/`_authorize_or_raise`/`_refetch_optimized`/
   `_build_payload`/`_validation_error_to_field_errors`/`_save_or_field_errors`) → the public names, noting
   `save_or_field_errors` is generalized to wrap a zero-arg save callable (lines 1585-1592). Left the
   rationale narration at lines 1594-1606 ("module-private (`_`-prefixed) ... today", and the
   underscore-drop-vs-`_pipeline.py`-lift decision) intact — it correctly narrates the pre-promotion state
   and the chosen mechanism; Worker 3's escalated item 3 resolved.

2. **Line 1873 (impl-plan table, Slice-3 row) — file-list reconciliation + public-name refresh
   (Worker 3 escalated item 2).** Slice 3 (file-list audit). Added the in-scope `forms/sets.py` cell (fill
   the four `resolve_*` stubs; `get_form_kwargs`/`get_form`/`perform_mutate`/`check_permission` hooks;
   `guard_required` waiver; `_cached_build_form_input` → `(input_cls, field_specs)` + `_input_field_specs`
   bind-stash) and the docstring-rename-touched `mutations/sets.py` / `mutations/permissions.py` / `relay.py`
   cell, refreshed the promoted helper names to public (+ `raw_choice_value`, + the `authorize_or_raise`
   message fallback), corrected the misplaced "get_form_kwargs construction" note (the hooks land on the
   `forms/sets.py` bases, not `forms/resolvers.py`), described the `mutations/fields.py` generalization
   concretely (duck-typed `_has_mutation_protocol`, `!= "form"` id-gate, payload-return ref stays
   `mutations.inputs`, `_input_type_name` deletion), and added the test-tree rename-sweep note. These edits
   are file-list reconciliation only; they do not change the contract Worker 2 implemented against.

3. **Line ~2514 (link-definition block) — added `[relay]` def.** Slice 3. The Slice-3-row file-list edit
   references `relay.py`; added `[relay]: ../../django_strawberry_framework/relay.py` alphabetically in the
   `<!-- django_strawberry_framework/ -->` group (the existing `[mutations-permissions]` / `[mutations-sets]`
   / `[test-products-api]` defs were reused — the row uses `[test-products-api]`, not a new ref).

4. **`"form"` operation literal (Worker 3 escalated item 1) — DECISION: accept as-is for Slice 3, defer the
   cross-slice consistency question to the integration pass.** No spec edit. Rationale: the entire operation
   vocabulary (`create`/`update`/`delete`/`form`) is bare-literal in `mutations/fields.py` today; singling
   out `"form"` for a cross-package `forms/inputs.py::FORM` import would be asymmetric. Worker 3 verified the
   `forms/inputs.py::FORM` import would NOT close a cycle (only the form *bases* do), so the integration pass
   may, if it chooses, introduce ONE shared operation-sentinel surface reachable without a cycle for the
   whole vocabulary — recorded as an integration-pass DRY candidate, not a Slice-3 blocker. The model flavor
   never emits `"form"`, so the literal cannot misfire; behavior is correct as shipped.
