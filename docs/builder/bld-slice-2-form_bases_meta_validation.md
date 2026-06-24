# Build: Slice 2 — the `DjangoFormMutation` / `DjangoModelFormMutation` bases + `Meta` validation + the phase-2.5 bind

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Slice 2 checklist lines 323-385; Decision 5 lines 972-1045; Decision 6 lines 1047-1177; Decision 13 lines 1750-1820; Edge cases lines 1926-1933; Test plan lines 2028-2038; DoD item 3 lines 2315-2342)
Status: final-accepted

## Plan (Worker 1)

This slice does the **036-surface generalization**: it refactors the shipped model-driven mutation surface in `mutations/sets.py` into overridable seams (`_validate_meta`, `build_input`, `input_type_name`, `input_module_path`, `resolve_sync`, `resolve_async`) **each defaulting to today's exact model behavior**, then ships the two new form-mutation bases in a net-new `forms/sets.py` on top of those seams. It also adds the `make_declaration_registry(label)` shared helper (single-sourcing the register/clear/iter/reject quad), wires `bind_form_mutations()` into the phase-2.5 finalizer window, co-clears the plain-form registry from `registry.clear()`, and exports the two bases from the package root `__init__.py` (NOT bumping `__version__` — that is Slice 5).

**Scope discipline for Worker 2.** The seam *bodies* land here only where the spec puts them: `_validate_meta`, `build_input`, `input_type_name`, `input_module_path`, and the two bases land in this slice. `resolve_sync` / `resolve_async` get a **defined seam** in `mutations/sets.py` here (the model base delegates to today's `mutations/resolvers.py::resolve_mutation_sync` / `resolve_mutation_async`), but the **form resolver pipeline body** (`forms/resolvers.py`) is **Slice 3** — so `forms/sets.py`'s `resolve_sync` / `resolve_async` overrides land here as `TODO(spec-038 Slice 3)`-anchored stubs that raise `NotImplementedError` (per AGENTS.md staged-anchor discipline + the build-plan 036-generalization flag). The `DjangoMutationField` generalization (target-check / `_resolve` dispatch / `data:` lazy-ref derivation in `mutations/fields.py`) is **Slice 3** (spec Slice 3 sub-bullet 2) — do NOT touch `mutations/fields.py` here. Do NOT write `get_form_kwargs`, `perform_mutate` bodies, or any decode/locate/validate/save logic — Slice 3.

**No-model-flavor-regression is the gate (DoD item 6, build-plan flag).** Every seam default must be byte-behavior-identical to today's path: `_validate_meta` is literally the existing `_validate_mutation_meta` body relocated to a classmethod; `build_input` is literally the existing `_materialize_input_for` call; `input_type_name` / `input_module_path` are literally the existing `fields.py::_input_type_name` / `INPUTS_MODULE_PATH` (consulted by Slice 3, defined here); `resolve_sync` / `resolve_async` delegate to the existing resolver functions. The DRY analysis below cites file:line for each extraction and confirms the model path is unchanged.

### DRY analysis

**Existing patterns reused (cite file:line — pin-at-write-time):**

- `django_strawberry_framework/mutations/sets.py::_validate_mutation_meta` (lines 347-443) — the 97-line class-creation validator (the helper's flagged hotspot at line 347, 10 branches). The refactor **moves this body verbatim** into a `DjangoMutation._validate_meta(cls, meta)` classmethod (the model base keeps every line, incl. its `"DjangoMutation {name}.Meta..."` wording — the shadow's `13x DjangoMutation` literal stays in the model path). The module-level `_validate_mutation_meta` becomes a thin shim `return cls._validate_meta(meta)` OR the metaclass calls `new_class._validate_meta(meta)` directly — see Implementation discretion. This is the seam: the form override supplies its own body.
- `django_strawberry_framework/mutations/sets.py::DjangoMutationMetaclass.__new__` (lines 457-473) — the metaclass calls `_validate_mutation_meta(new_class, meta)` (line 471) and `register_mutation(new_class)` (line 472). The refactor changes line 471 to `new_class._validate_meta(meta)` (dispatching to the overridable classmethod), so the **same metaclass** validates a `DjangoModelFormMutation` (a `DjangoMutation` subclass) through the form override — no second metaclass needed for the ModelForm flavor. The plain `DjangoFormMutation` needs its OWN metaclass (it is not a `DjangoMutation` subclass) — modeled on this one.
- `django_strawberry_framework/mutations/sets.py::register_mutation` / `clear_mutation_registry` / `iter_mutations` (lines 126-156) + the module-global `_mutation_registry: list[type]` (line 107) — the four-part declaration-registry quad (identity-dedup append, post-`mark_finalized()` reject, `.clear()`, ordered `tuple(...)` snapshot). Decision 13 (lines 1779-1793) mandates factoring the **shared mechanics** into `make_declaration_registry(label)` that BOTH `mutations/sets.py` and `forms/sets.py` instantiate, **keeping the two ledgers disjoint** (different `bind_*` bodies, different `registry.clear()` rows). Verified mechanically identical to what the plain-form registry needs.
- `django_strawberry_framework/mutations/sets.py::_materialize_input_for` (lines 603-669) — builds the model-column `<Model>Input` / `<Model>PartialInput` (or merges a consumer `input_class`), routing through `mutation_input_shape` + `build_mutation_input` + `materialize_mutation_input_class`, caching by shape identity in `_shape_build_cache` (line 123). This becomes the **default body of `DjangoMutation.build_input(meta, primary_type)`** (the model flavor's seam default), called from `_bind_mutation` (line 869) instead of the direct function call. The form override calls the `forms/inputs.py` generator instead.
- `django_strawberry_framework/mutations/sets.py::_bind_mutation` (lines 857-885) — resolves the primary type (`_resolve_primary_type`, line 867), materializes the input (line 869 → now `mutation_cls.build_input(meta, primary_type)`), builds + materializes the `<Name>Payload` (lines 871-881), stashes `_primary_type` / `_input_class` / `_payload_type_name` (lines 883-885). For the `DjangoModelFormMutation` flavor this binds **unchanged except** the input-materialization step routes through the `build_input` seam (Decision 13 lines 1752-1765). `bind_mutations()` (lines 888-899) drains the `DjangoMutation` registry and clears `_shape_build_cache` — the ModelForm flavor rides it for free.
- `django_strawberry_framework/mutations/fields.py::_input_type_name` (lines 95-124) + `_lazy_ref` (lines 127-136) + `INPUTS_MODULE_PATH` import (line 62) — the model-column `data:` lazy-ref derivation. Decision 5 axis 3 (lines 1008-1017) makes the name + module overridable seams `input_type_name(meta)` / `input_module_path` the factory consults. **This slice defines those seam classmethods on `DjangoMutation` (model defaults = today's `_input_type_name` body + `INPUTS_MODULE_PATH`)**; the *fields.py rewiring to consult them* is Slice 3 (spec Slice 3 sub-bullet 2). So the model default `DjangoMutation.input_type_name(meta)` returns exactly what `fields.py::_input_type_name(meta)` returns today, and `DjangoMutation.input_module_path` is exactly `mutations.inputs.INPUTS_MODULE_PATH` — keep them single-sourced (see Duplication risk avoided).
- `django_strawberry_framework/mutations/resolvers.py::resolve_mutation_sync` (line 1133) / `resolve_mutation_async` (line 1149) — the model resolver entry points `fields.py::_resolve` calls today (fields.py lines 211-213). The `DjangoMutation.resolve_sync` / `resolve_async` classmethod defaults delegate to these (so the model dispatch is unchanged when Slice 3 rewires `fields.py::_resolve` to call `mutation_cls.resolve_sync`).
- `django_strawberry_framework/forms/inputs.py::build_form_inputs` (lines 483-535) + `clear_form_input_namespace` (lines 136-154) + `FORM` (line 93) + `materialize_form_input_class` (lines 112-133) + `INPUTS_MODULE_PATH` (line 84) — the Slice-1 form-input generator + ledger. `forms/sets.py`'s `build_input` overrides (both flavors) call `build_form_inputs(form_class, operation_kind=..., fields=, exclude=, guard_required=...)` and `materialize_form_input_class`; `bind_form_mutations()` drains the plain-form registry and calls each plain form's `build_input` + a model-less payload build. The Slice-1 `clear_form_input_namespace()` is wired into `registry.clear()` **this slice** (Slice 1 left the `# wired into registry.clear() in Slice 2` note, `forms/inputs.py` lines 105-106 / 152).
- `django_strawberry_framework/registry.py::clear` (lines 468-544) — the `_clear_if_importable(module_path, attr_name, action)` co-clear idiom (lines 34-50). The two new co-clear rows (`forms.inputs::clear_form_input_namespace` and `forms.sets::clear_form_mutation_registry`) append after the existing mutation co-clears (lines 518-534), byte-identical shape to lines 525-534.
- `django_strawberry_framework/types/finalizer.py::finalize_django_types` (lines 695-712) — the phase-2.5 bind window: the function-local `from ..mutations.sets import bind_mutations` (line 708) then `bind_mutations()` / `_bind_filtersets()` / `_bind_ordersets()` (lines 710-712). `bind_form_mutations()` is added with the **same function-local-import + call** shape, alongside `bind_mutations()` (Decision 13 lines 1773-1777 — a single named finalizer edit, no new public entry point). Placement: after `bind_mutations()` (the plain-form bind is independent of the model bind; both run before Phase 3 / `strawberry.type`).
- `django_strawberry_framework/__init__.py` (lines 19-24, 38-62) — the `from .mutations import (...)` re-export block + `__all__` tuple. Add `DjangoFormMutation` / `DjangoModelFormMutation` from `.forms` (a new `from .forms import (...)` line, mirroring the mutations block) and two `__all__` entries (alphabetical). Do NOT touch `__version__` (line 36) — Slice 5.
- `django_strawberry_framework/types/base.py` `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` — **read-only, byte-unchanged** (Decision 13 lines 1795-1800; DoD item 3). A form-mutation `Meta` is its own namespace; do not import or extend these sets.
- Test-shape precedent: `tests/mutations/test_sets.py` (the `Meta`-validation matrix shape, the registry-isolation autouse fixture, the `pytest.raises(ConfigurationError, match=...)` assertions, the `bind_mutations()` + finalize harness). `tests/forms/test_sets.py` mirrors these. `tests/forms/test_inputs.py` (Slice 1) already carries the form fixtures (`ModelForm` over products `Item`, plain `Form`, kwarg-requiring form, `_make_relay_target` / `_make_non_relay_target`).

**New helpers justified (single responsibility each):**

1. `mutations/sets.py::make_declaration_registry(label)` — the Decision-13 shared-mechanics factory. Single responsibility: given a human label (`"DjangoMutation"` / `"DjangoFormMutation"`), create a **fresh private `list[type]`** and return the bound `(register, clear, iter)` callables over it (identity-dedup append + post-`mark_finalized()` reject in `register`, `.clear()` in `clear`, ordered `tuple(...)` in `iter`). The `label` is interpolated into the post-finalize reject message (`f"Cannot declare {label} {cls.__name__} after finalization; ..."`). `mutations/sets.py` instantiates it for `register_mutation` / `clear_mutation_registry` / `iter_mutations` (replacing the three hand-written functions + `_mutation_registry`); `forms/sets.py` instantiates a **second, disjoint** one for `register_form_mutation` / `clear_form_mutation_registry` / `iter_form_mutations`. Single-sources the dedup/reject/clear logic without merging the storage (the over-DRY trap Decision 13 names). Lives in `mutations/sets.py` (the existing owner of the quad); `forms/sets.py` imports it. Return shape at W2 discretion (a small frozen tuple, a tiny dataclass, or a namedtuple — see discretion items); `mutations/fields.py` imports `iter_mutations` today only transitively, but the public names `register_mutation` / `clear_mutation_registry` / `iter_mutations` must survive (registry.py line 531 + the metaclass + tests reference them), so the factory's returned callables are **assigned to those module-level names**.

2. `forms/sets.py::DjangoModelFormMutation` — the `ModelForm` base subclassing `DjangoMutation`. Single responsibility: supply the four form seam overrides (`_resolve_model` → `Meta.form_class._meta.model`; `_validate_meta` → the form-flavor validator; `build_input` → the `forms/inputs.py` generator + `materialize_form_input_class`; `input_type_name` / `input_module_path` → the form name + `forms.inputs.INPUTS_MODULE_PATH`; `resolve_sync` / `resolve_async` → the Slice-3-anchored stubs). It inherits the metaclass, `register_mutation`, `_bind_mutation`, `check_permission`, and the `DjangoModelPermission` default unchanged.

3. `forms/sets.py::DjangoFormMutation` + `DjangoFormMutationMetaclass` — the model-less plain-`Form` sibling (its OWN metaclass + declaration registry + bind). Single responsibility: a lighter base that shares the form pipeline (Slice 3) and converter but carries no model / no `DjangoType` object slot. Its metaclass validates `Meta` via the plain-form `_validate_meta` and calls `register_form_mutation`. Its `build_input` materializes the model-less input; `bind_form_mutations()` drains its registry and builds each plain form's input + the pinned `ok`/`errors` payload.

4. `forms/sets.py::bind_form_mutations()` — the phase-2.5 entry point for the plain-form registry. Single responsibility: drain `iter_form_mutations()`, and for each materialize its form-derived input (via the flavor `build_input`) + its **pinned two-field payload** (`ok: Boolean!` + `errors: [FieldError!]!` — no DjangoType object slot, Decision 6 lines 1111-1128). NOTE: the payload *builder* for the model-less `ok`/`errors` shape — does the plain-form payload reuse `build_payload_type(object_type=None)` or a dedicated model-less builder? See Implementation steps + the spec-reconciliation note: `build_payload_type` (mutations/inputs.py line 549) takes `object_type` + `object_slot`; a model-less payload has neither. This slice needs a model-less payload build path. Resolve in-plan (below).

5. `forms/sets.py::_validate_form_mutation_meta` (or two flavor classmethod bodies) — the form-flavor `_validate_meta`. Single responsibility: the form allowed-key validation matrix (Decision 6 / spec Slice 2 lines 344-370). A shared core (presence of `form_class`, `fields`/`exclude` normalize + mutual exclusion via the Slice-1 `resolve_effective_form_fields` machinery or `normalize_form_field_sequence`) plus the two per-base divergences (plain: `issubclass(ModelForm)` reject FIRST → require `forms.Form`, reject ANY `operation`, `"form"` sentinel; modelform: require `forms.ModelForm`, `operation ∈ {"create","update"}`, reject `"delete"`). W2 decides one shared helper with a flag vs two classmethod bodies (see discretion).

**Duplication risk avoided:**

- **A second copy of the 97-line `_validate_mutation_meta` body.** The model `_validate_meta` MUST be the relocated body, not a re-typed near-copy — the no-regression gate depends on byte-identity. The form override is a genuinely different matrix (different keys, different `operation` rule, the `form_class`-before-`_resolve_model` ordering), so it is a *new* body, not a near-copy of the model one. Prevent: relocate (cut/paste) the model body into the classmethod; do not retype it. Worker 3 diffs the relocated body against the pre-refactor `_validate_mutation_meta` to confirm the model path is unchanged.
- **Re-spelling the declaration-registry quad.** The plain-form registry's four functions are mechanically identical to `register_mutation` & co. Prevent: `make_declaration_registry(label)` single-sources them (Decision 13). Do NOT clone the four bodies into `forms/sets.py`; instantiate the factory.
- **Re-deriving the form input name / module in two places.** Slice 3's `fields.py` will consult `mutation_cls.input_type_name(meta)` / `input_module_path`. The model default must be single-sourced with today's `fields.py::_input_type_name`: rather than copy that body into `DjangoMutation.input_type_name`, **move** the `_input_type_name` body to the `DjangoMutation.input_type_name` classmethod (model default) and have `fields.py` call the classmethod in Slice 3 (so there is one body). For THIS slice, the cleanest move is: define `DjangoMutation.input_type_name(meta)` with the `_input_type_name` body and `input_module_path = mutations.inputs.INPUTS_MODULE_PATH`; leave `fields.py::_input_type_name` in place (Slice 3 removes it when it rewires `_synthesized_mutation_signature` to consult the seam). Flag the transient duplication (`_input_type_name` body exists in both `fields.py` and the new classmethod between Slice 2 and Slice 3) as a **staged, Slice-3-resolved** item — do NOT leave it permanently. Worker 2 anchors the `fields.py::_input_type_name` with a `TODO(spec-038 Slice 3)` note that Slice 3 deletes. (See Implementation discretion — W2 may instead have the Slice-2 classmethod *delegate* to `fields.py::_input_type_name` to avoid the copy, but that creates a `sets.py → fields.py` import edge that does not exist today and that `fields.py` imports `sets.py` already, risking a cycle; recommended: relocate the body to `sets.py` and have Slice 3 point `fields.py` at it.)
- **A model-less branch leaking into `_bind_mutation`.** Decision 6 (lines 1163-1174) explicitly rejects relaxing the model requirement to fold the plain form into `bind_mutations`. Prevent: the plain form gets its OWN `bind_form_mutations()`; `_bind_mutation` stays model-only (no `if model is None` branch).
- **The form `_validate_meta` re-implementing the Slice-1 narrowing validation.** `Meta.fields`/`Meta.exclude` mutual-exclusion + bare-string/duplicate/unknown-name fail-loud already lives in `forms/inputs.py::resolve_effective_form_fields` / `normalize_form_field_sequence` (Slice 1, lines 173-268). The form `_validate_meta` reuses those (it validates `form_class.base_fields`), not a re-spelled copy.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before editing.

1. **`mutations/sets.py` — extract `make_declaration_registry(label)` and re-base the quad.** Add `make_declaration_registry(label: str)` returning bound `(register, clear, iter)` callables over a fresh private `list[type]` (the `register` body = `register_mutation`'s identity-dedup + `registry.is_finalized()` reject at lines 135-141, with `label` in the message; `clear` = `.clear()`; `iter` = `tuple(...)`). Replace the module-level `_mutation_registry` (line 107) + the three functions (lines 126-156) by instantiating `register_mutation, clear_mutation_registry, iter_mutations = make_declaration_registry("DjangoMutation")` (assigning to the SAME public names registry.py line 531 / the metaclass / tests reference). Keep the docstrings' contract intact (move the prose into the factory's docstring + a one-line note at the assignment).

2. **`mutations/sets.py` — relocate `_validate_mutation_meta` into `DjangoMutation._validate_meta(cls, meta)`.** Move the body of `_validate_mutation_meta` (lines 347-443) into a `@classmethod def _validate_meta(cls, meta) -> _ValidatedMutationMeta` on `DjangoMutation` (placed near `_resolve_model`, line 507). Keep the body byte-identical (it already calls `cls._resolve_model(meta)` via `mutation_cls._resolve_model` at line 377 — rename the local `mutation_cls`→`cls`, `name = cls.__name__`). The metaclass (`__new__`, line 471) changes `new_class._mutation_meta = _validate_mutation_meta(new_class, meta)` → `new_class._mutation_meta = new_class._validate_meta(meta)`. The module-level `_validate_mutation_meta` is removed (its only caller was the metaclass) OR kept as a one-line shim — W2 discretion; removal is cleaner. The helper-flagged `_validate_input_class` / `_expected_input_attr_names` / `_normalize_field_sequence` / `_validate_permission_classes` stay module-level (the model `_validate_meta` calls them; the form override does not need them) — no change.

3. **`mutations/sets.py` — add the `build_input` / `input_type_name` / `input_module_path` seams on `DjangoMutation`.** 
   - `@classmethod def build_input(cls, meta, primary_type) -> type | None`: body = the current `_materialize_input_for(cls.__name__, meta, primary_type)` call (the model default). Either move `_materialize_input_for`'s body into the classmethod or keep `_materialize_input_for` module-level and have `build_input` delegate (recommended: delegate — `_materialize_input_for` + `_materialize_merged_input` + `_shape_build_cache` are a tight cluster; keep them module-level, have `build_input` call `_materialize_input_for(cls.__name__, meta, primary_type)`).
   - `@classmethod def input_type_name(cls, meta) -> str`: the model default = the relocated `fields.py::_input_type_name` body (lines 95-124) — `editable_input_fields(meta.model, ...)` → `mutation_input_type_name(...)`. (Slice 3 points `fields.py` at this; this slice leaves `fields.py::_input_type_name` in place with a `TODO(spec-038 Slice 3)` anchor — see Duplication risk avoided.)
   - `input_module_path: str = INPUTS_MODULE_PATH` (a class attribute, the `mutations.inputs` path). The form flavors override it to `forms.inputs.INPUTS_MODULE_PATH`.
   - `_bind_mutation` (line 869): change `input_cls = _materialize_input_for(mutation_cls.__name__, meta, primary_type)` → `input_cls = mutation_cls.build_input(meta, primary_type)`.

4. **`mutations/sets.py` — add the `resolve_sync` / `resolve_async` seams on `DjangoMutation`.** Two classmethods delegating to the model resolver entry points: `@classmethod def resolve_sync(cls, info, *, data, id)` → `from .resolvers import resolve_mutation_sync; return resolve_mutation_sync(cls, info, data=data, id=id)` (and the `async` mirror → `resolve_mutation_async`). Use a **function-local import** of `mutations.resolvers` to avoid a module-load cycle (`resolvers.py` imports from `sets.py`? verify — if `sets.py` importing `resolvers` at module top is clean today via `fields.py`, a top import is fine; recommended local import to be safe, mirroring `fields.py` line 66's top import only because `fields.py` is leaf). Worker 2 verifies the import direction; if `resolvers.py` does not import `sets.py` at module top, a top-level import in `sets.py` is acceptable. These are the **defined seams** Slice 3's `fields.py::_resolve` rewiring will call; the model bodies are today's behavior. (`fields.py` keeps calling `resolve_mutation_sync` directly until Slice 3 — so no `fields.py` edit here.)

5. **`forms/sets.py` (new) — the two bases.** Module docstring (the form-mutation bases + metaclass + the two-flavor `_validate_meta` + the plain-form registry/bind, citing Decisions 5/6/13). Ship:
   - Import `make_declaration_registry` from `..mutations.sets`; `DjangoMutation`, `DjangoMutationMetaclass` from `..mutations.sets`; the Slice-1 `build_form_inputs`, `materialize_form_input_class`, `FORM`, `INPUTS_MODULE_PATH as FORMS_INPUTS_MODULE_PATH`, `resolve_effective_form_fields` (or `normalize_form_field_sequence`) from `.inputs`; `from .converter import ...` if a spec is needed; `ConfigurationError`; `from django import forms`; the form-input-name helper `form_input_type_name` from `.inputs`.
   - `register_form_mutation, clear_form_mutation_registry, iter_form_mutations = make_declaration_registry("DjangoFormMutation")` — the disjoint plain-form ledger.
   - **`DjangoModelFormMutation(DjangoMutation)`** with:
     - `@classmethod def _resolve_model(cls, meta)` → `form_class = getattr(meta, "form_class", None); return getattr(getattr(form_class, "_meta", None), "model", None)` (returns `None` for missing/no-`_meta`/no-model — the base validation's `_resolve_model is None → raise` handles the "ModelForm with no resolvable model" case; the form `_validate_meta` already validated `form_class` presence + `ModelForm`-subclass BEFORE calling `_resolve_model`, so a missing-model ModelForm reaches `_resolve_model` returning `None`).
     - `@classmethod def _validate_meta(cls, meta)` → the **modelform-flavor** body (allowed keys `{form_class, operation, fields, exclude, permission_classes}` — adds `form_class`, drops `model`/`input_class`/`partial_input_class`; require `form_class` is a `forms.ModelForm` subclass BEFORE `_resolve_model`; `operation ∈ {"create","update"}` reject `"delete"`; `_resolve_model is None → raise` for the no-model ModelForm; `fields`/`exclude` mutual-exclusion + fail-loud via the Slice-1 narrowing helpers against `form_class.base_fields`; `permission_classes` via the existing `_validate_permission_classes`). Returns a validated-meta snapshot. NOTE the snapshot shape: the existing `_ValidatedMutationMeta` (sets.py lines 232-268) has `model`/`operation`/`input_class`/`partial_input_class`/`fields`/`exclude`/`permission_classes` slots but NO `form_class` slot — the form snapshot needs `form_class` (and the resolved `model`). Resolve: either add a `form_class` slot to `_ValidatedMutationMeta` (a None-defaulted optional slot the model path leaves None) OR a form-local validated-meta record. See Implementation discretion + spec-reconciliation note (recommended: extend `_ValidatedMutationMeta` with an optional `form_class` slot — the bind/resolver read one snapshot shape; the model path sets it None).
     - `@classmethod def build_input(cls, meta, primary_type)` → call `build_form_inputs(meta.form_class, operation_kind=<CREATE if meta.operation=="create" else PARTIAL>, fields=meta.fields, exclude=meta.exclude, guard_required=<not get_form_kwargs overridden>)`, then `materialize_form_input_class(...)` for the operation's input, and cache by the form shape identity. **Wrinkle:** the model `build_input` returns ONE input per operation (create→Input, update→PartialInput); `build_form_inputs` returns BOTH. For a ModelFormMutation `operation` is create XOR update, so build_input materializes only the matching one. W2 decides whether to call `build_form_input_class` (single) or `build_form_inputs` (pair, materialize one). Recommended: call the single `build_form_input_class` for the operation's kind to mirror `_materialize_input_for`'s one-input-per-op shape, applying the create-required guard inline for `create`. The `guard_required` waiver (`get_form_kwargs` overridden) — the hook does not exist until Slice 3, so for THIS slice pass `guard_required=True` always and anchor the waiver wiring `TODO(spec-038 Slice 3)` (the Slice-1 test already proves the parameter mechanically). State this deferral.
     - `input_module_path = FORMS_INPUTS_MODULE_PATH`; `@classmethod def input_type_name(cls, meta)` → `form_input_type_name(meta.form_class, <kind>, <effective names>, full_field_names=...)`.
     - `resolve_sync` / `resolve_async` → `TODO(spec-038 Slice 3)`-anchored `raise NotImplementedError("form resolver pipeline lands in spec-038 Slice 3")` (the seam is defined; the body is Slice 3's `forms/resolvers.py`). The model base's defaults are NOT inherited usefully (they call the model resolver) — the override must exist so Slice 3 fills it; until then it raises loud. Anchor removed when Slice 3 ships `forms/resolvers.py`.
   - **`DjangoFormMutationMetaclass(type)`** mirroring `DjangoMutationMetaclass.__new__` (lines 457-473): build the class, skip if no `Meta` (abstract base guard), else `new_class._mutation_meta = new_class._validate_meta(meta)` + `register_form_mutation(new_class)`.
   - **`DjangoFormMutation(metaclass=DjangoFormMutationMetaclass)`** with the **plain-form** `_validate_meta` (allowed keys `{form_class, fields, exclude, permission_classes}` — NO `operation`, NO `model`): require `form_class`; **check `issubclass(form_class, forms.ModelForm)` FIRST** → `ConfigurationError` naming `DjangoModelFormMutation` as the correct base (Edge case lines 1926-1933); then require `issubclass(form_class, forms.Form)`; **reject ANY `Meta.operation`** (create/update/delete alike, Decision 10 lines 1669-1674); `fields`/`exclude` fail-loud + mutual-exclusion against `form_class.base_fields`; `permission_classes` validated (Decision 11 plain-form posture — an UNSET `permission_classes` is the `DjangoModelPermission` default which, with no model, denies; the explicit `[]` opt-out is AllowAny). Snapshot carries `form_class` + the `"form"` sentinel as the operation component (Decision 7 P2). `build_input` → `build_form_inputs(form_class, operation_kind=FORM, ...)`; `input_type_name` / `input_module_path` → the form names. The plain form has NO `_resolve_model` (model-less) and NO model payload; its bind builds the pinned `ok`/`errors` payload.
   - Module-level `bind_form_mutations()`: drain `iter_form_mutations()`; per plain mutation, build + materialize its input (via `build_input`) and its pinned two-field payload, stash the refs (`_input_class`, `_payload_type_name`, and `_primary_type = None` for the model-less case) for Slice 3's `DjangoMutationField`. The payload builder for `ok`/`errors`: see step 7.

6. **`mutations/inputs.py` — model-less payload builder (if needed).** `build_payload_type(mutation_name, *, object_type, object_slot)` (line 549) builds the `<Name>Payload` with a DjangoType object slot. The plain form needs a model-less `<Name>Payload` with ONLY `ok: bool` + `errors: list[FieldError]`. **Decide where this lives.** Options: (a) extend `build_payload_type` to accept `object_type=None` → emit the two-field model-less payload (single-sources the payload builder, the `errors` field is identical); (b) a dedicated `build_form_payload_type(mutation_name)` in `forms/sets.py` or `forms/inputs.py`. Recommended (a) — `build_payload_type(object_type=None, object_slot=None)` emits `{ok: bool, errors: [FieldError]}`, reusing the frozen `FieldError` field shape; the model path passes a non-None `object_type` and is byte-unchanged (no-regression: the None branch is net-new, never hit by the model flavor). This keeps ONE payload builder + ONE `materialize_*` ledger. **Surface this as a spec-reconciliation note** (Decision 6 pins the plain-form payload shape but does not name the builder; the spec says `bind_form_mutations()` "materializes each plain form's model-less input + payload" without pinning the builder — confirm `build_payload_type(object_type=None)` is the intended single-source). If `build_payload_type` cannot cleanly take None (e.g. `payload_object_slot` requires a type), fall back to a dedicated builder + route it through the form `materialize_form_input_class` ledger. **NOTE: this is a `mutations/inputs.py` edit not in the spec's Slice-2 file list — flag it.** It is required for the plain-form payload and is the DRY choice; alternatively the dedicated builder lives entirely in `forms/`. W2 + W1-reconciliation decide; recommended (a) with the spec note.

7. **`registry.py` — co-clear the form ledgers.** In `TypeRegistry.clear` (after the mutation co-clears, lines 525-534), append two `_clear_if_importable` rows: `("django_strawberry_framework.forms.inputs", "clear_form_input_namespace", lambda clear: clear())` and `("django_strawberry_framework.forms.sets", "clear_form_mutation_registry", lambda clear: clear())` — byte-identical shape to the existing mutation rows. (The Slice-1 `clear_form_input_namespace` is finally wired here.)

8. **`types/finalizer.py` — wire `bind_form_mutations()` into phase 2.5.** After `bind_mutations()` (line 710), add a function-local `from ..forms.sets import bind_form_mutations` + `bind_form_mutations()` call, in the same window as `bind_mutations()` / `_bind_filtersets()` / `_bind_ordersets()` (before Phase 3). Mirror the existing comment block (lines 695-708) noting the cycle-safe local import + the materialize-before-`Schema` reason. Placement: immediately after `bind_mutations()` (independent; the ModelForm flavor already bound via `bind_mutations`, the plain forms bind here).

9. **`__init__.py` — export the two bases.** Add `from .forms import DjangoFormMutation, DjangoModelFormMutation` (a new `# noqa: E402` block after the `.mutations` import, lines 19-24) and add `"DjangoFormMutation"` + `"DjangoModelFormMutation"` to `__all__` (alphabetical: after `DjangoConnectionField`/before `DjangoImageType`... — exact ordering per the existing tuple). This requires `forms/__init__.py` to re-export the two bases — add `from .sets import DjangoFormMutation, DjangoModelFormMutation` + an `__all__` to `forms/__init__.py` (Slice 1 left it docstring-only; this slice adds the re-exports). **Do NOT bump `__version__` (line 36).**

### Test additions / updates

Tests live under `tests/forms/test_sets.py` (new) per the AGENTS.md mirror rule, plus a small extension to `tests/mutations/test_sets.py` for the no-model-flavor-regression assertions. System-under-test: the bases run against the products `Item`/`Category` fixtures + the Slice-1 package-local form fixtures (`ModelForm` over `Item`, plain `Form`, a `ModelForm` with no resolvable model, a kwarg-requiring form). Reuse the registry-isolation autouse fixture + the `bind_mutations()`/`finalize_django_types()` harness shape from `tests/mutations/test_sets.py`. Create `tests/forms/test_sets.py` (the `tests/forms/__init__.py` package marker exists from Slice 1).

**`tests/forms/test_sets.py`** (spec Test plan lines 2028-2038; Slice 2 checklist lines 374-385):

- **`Meta` validation matrix:**
  - missing `Meta.form_class` (both bases) → `ConfigurationError` naming `form_class`.
  - a `ModelForm` on the plain `DjangoFormMutation` base → `ConfigurationError` **naming `DjangoModelFormMutation`** (the targeted message; assert the message names the model base, proving the `issubclass(ModelForm)`-first check, Edge case P2).
  - a non-`ModelForm` (a plain `forms.Form`) on `DjangoModelFormMutation` → `ConfigurationError`.
  - a `ModelForm` with no resolvable `_meta.model` on `DjangoModelFormMutation` → `ConfigurationError` (a clean config error, NOT a raw `AttributeError`).
  - `DjangoModelFormMutation` `operation = "delete"` → `ConfigurationError` (rejected; the form flavor has no delete pipeline).
  - **any `Meta.operation` on the plain base** (`"create"`, `"update"`, `"delete"`, an arbitrary string) → `ConfigurationError` (P2 — the plain base rejects `operation` outright).
  - `form_class` accepted as a known key (a valid `DjangoModelFormMutation` / `DjangoFormMutation` class-creation does NOT raise).
  - `fields` + `exclude` both set → `ConfigurationError` (both bases).
  - an unknown `Meta` key → `ConfigurationError`.
  - (`fields` bare-string / duplicate / unknown-name against `form.base_fields` is Slice-1-covered via `resolve_effective_form_fields`; assert the base routes through it for at least one case — e.g. an unknown-name `fields` on a base → `ConfigurationError`.)
- **plain-form input dedupe via the `"form"` sentinel:** two plain `DjangoFormMutation` classes over the SAME form + same effective set → the materialize ledger dedupes to one input class (idempotent); assert via the `forms.inputs` module-global + the ledger (mirroring the Slice-1 dedupe test).
- **registration:** a concrete `DjangoModelFormMutation` appears in `iter_mutations()` (the DjangoMutation registry); a concrete `DjangoFormMutation` appears in `iter_form_mutations()` (the disjoint plain-form registry) and NOT in `iter_mutations()`; the abstract bases register nowhere.
- **finalizer binding — both paths:** after `finalize_django_types()`, a `DjangoModelFormMutation`'s `_primary_type` / `_input_class` / `_payload_type_name` are set (the `bind_mutations()` path through the `build_input` seam — the form-derived input materialized in `forms.inputs`, NOT `mutations.inputs`); a `DjangoFormMutation`'s input + pinned `ok`/`errors` payload are materialized (the `bind_form_mutations()` path). Assert the plain-form payload has exactly `ok` + `errors` fields (no object slot).
- **the no-registered-primary-type error for `DjangoModelFormMutation`:** a `DjangoModelFormMutation` over a `ModelForm` whose model has NO registered `DjangoType` → `ConfigurationError` at finalize (the reused `_resolve_primary_type` path — "no type to return").
- **post-finalize declaration reject:** declaring a `DjangoFormMutation` after `registry.mark_finalized()` → `ConfigurationError` (the `make_declaration_registry` reject body, mirroring the `register_mutation` post-finalize test).

**`tests/mutations/test_sets.py`** (extend — the no-model-flavor-regression gate, spec Test plan line 2069-2071 / DoD item 6):

- the model-flavor seam defaults unchanged: a `DjangoMutation` (model `create`/`update`/`delete`) still validates its `Meta` exactly as before (the relocated `_validate_meta` body behaves identically — re-pin one representative validation case + one bind case if not already covered), and still materializes its model-column `<Model>Input` in `mutations.inputs` (NOT touched by the refactor). If the existing `test_sets.py` already exhaustively covers this, add a focused assertion that `DjangoMutation.build_input` / `input_type_name` / `input_module_path` produce the model defaults (the seam exists and defaults correctly).
- `make_declaration_registry`: assert the `DjangoMutation` registry still dedupes by identity + rejects post-finalize (the refactored quad behaves as the old one).

No temp/scratch tests anticipated; these are permanent package tests Worker 2 writes in the same change as the code.

### Static-inspection helper disposition (planning pass)

**Run.** BUILD.md "When to run the helper during build" requires Worker 1 to run `scripts/review_inspect.py` during planning when the plan adds logic to an existing `.py` file ≥150 source lines. Slice 2 adds logic to `mutations/sets.py` (899 source lines, well over 150) — the trigger fires — and to `types/finalizer.py` (1390 lines). Both were run with `--output-dir docs/shadow` (no `--cov*`):

- `python scripts/review_inspect.py django_strawberry_framework/mutations/sets.py --output-dir docs/shadow` → exit 0. Quick scan: 23 symbols, 7 control-flow hotspots, 0 executable Django/ORM markers, **8 repeated string literals** (notably `13x DjangoMutation`, `5x input_class`, `5x partial_input_class`, `3x operation`, `3x permission_classes`). The `13x DjangoMutation` literal is the model-flavor error-message wording that MUST stay in the relocated `_validate_meta` body (the form override has its own `DjangoFormMutation` / `DjangoModelFormMutation` wording — the disjoint validation namespaces). The hotspot `_validate_mutation_meta` (line 347, 97 lines / 10 branches) is the body being relocated to the classmethod seam — Worker 3 confirms it is moved, not re-typed. `_materialize_input_for` (line 603, 67 lines) is the `build_input` default. The `make_declaration_registry` extraction reduces the three quad functions to one factory.
- `python scripts/review_inspect.py django_strawberry_framework/types/finalizer.py --output-dir docs/shadow` → exit 0. Slice 2's finalizer edit is a single local-import + `bind_form_mutations()` call in the existing phase-2.5 window (lines 695-712) — minimal added logic; no new hotspot. Recorded for completeness.

Shadow files are gitignored, read-only, non-canonical line numbers; cite original source via symbol-qualified paths in source/review.

### Implementation discretion items

Genuinely Worker-2-discretion (the design is settled; these are equivalent-shape / naming choices):

- **`make_declaration_registry` return shape** — a 3-tuple `(register, clear, iter)`, a small namedtuple, or a tiny frozen dataclass. All satisfy the assign-to-public-names contract. Pick whichever reads cleanest; the names `register_mutation` / `clear_mutation_registry` / `iter_mutations` (and the form trio) must remain importable module-level symbols.
- **`_validate_mutation_meta` shim vs removal** — after relocating the body into `DjangoMutation._validate_meta`, remove the module-level `_validate_mutation_meta` (cleaner — its only caller was the metaclass) or keep a one-line shim. Removal recommended; if a test imports `_validate_mutation_meta` directly, keep the shim.
- **Form `_validate_meta`: one shared helper-with-flag vs two classmethod bodies** — the plain and modelform validators share the `form_class`-presence + `fields`/`exclude` core but diverge on the `issubclass` order, the `operation` rule, and the allowed-key set. W2 may write a shared `_validate_form_meta_core(...)` + two thin per-base classmethods, or two full classmethod bodies. Keep the two divergences (the `ModelForm`-first reject on the plain base; the `operation` split) explicit and tested; do not over-DRY them into an indistinguishable branch.
- **`build_input` for the ModelForm flavor: `build_form_input_class` (single) vs `build_form_inputs` (pair, use one)** — the model `_materialize_input_for` builds one input per operation; mirror that with `build_form_input_class` for the operation's kind, applying the create-required guard inline for `create`. Either is acceptable as long as only the operation's input is materialized and the create-required guard fires for `create`.
- **`resolve_sync` / `resolve_async` import placement in `mutations/sets.py`** — top-level `from .resolvers import ...` if the import direction is acyclic (verify `resolvers.py` does not import `sets.py` at module top), else a function-local import. Either is fine; prefer the one that does not introduce a cycle.
- **Co-clear row order in `registry.clear`** — the two form rows append after the mutation rows; order among them is immaterial (independent best-effort blocks), matching the existing pattern's documented order-independence.

Items NOT at discretion (escalated / resolved in-plan, flagged for Worker 1 final-verification + spec reconciliation):
- **The validated-meta snapshot's `form_class` slot** (extend `_ValidatedMutationMeta` with an optional `form_class` slot vs a form-local record) — recommended: extend `_ValidatedMutationMeta` (one snapshot shape the bind/resolver read; the model path leaves `form_class=None`). This is a structural choice the plan resolves; W2 implements the recommended path unless it reveals a conflict, in which case surface to W1.
- **The model-less payload builder** (`build_payload_type(object_type=None)` vs a dedicated `forms/` builder) — recommended `build_payload_type(object_type=None)` for single-sourcing, but this is a `mutations/inputs.py` edit outside the spec's Slice-2 file list; W1 reconciles (see spec-reconciliation note). If `build_payload_type` cannot cleanly take None, a dedicated form payload builder is the fallback.

### Spec slice checklist (verbatim)

- [x] Slice 2: the `DjangoFormMutation` / `DjangoModelFormMutation` bases + `Meta`
  validation + the phase-2.5 bind (per
  [Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
  /
  [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling))
  - [x] [`mutations/sets.py`][mutations-sets]: refactor the class-creation
    validation into an overridable `DjangoMutation._validate_meta(meta)` classmethod
    the metaclass invokes (the model base keeps today's `_validate_mutation_meta`
    body), and add the overridable `build_input(meta, primary_type)` bind hook +
    `input_type_name(meta)` / `input_module_path` + `resolve_sync` / `resolve_async`
    seams ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)
    / [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
    each defaulting to today's model behavior (no model-flavor regression).
  - [x] [`forms/sets.py`][forms-sets]: `DjangoModelFormMutation` (subclasses
    [`DjangoMutation`][glossary-djangomutation], overriding [`_resolve_model`][spec-036]
    → `Meta.form_class._meta.model`, plus the `_validate_meta` / `build_input` /
    `input_type_name` / `input_module_path` / `resolve_*` seams above) and
    `DjangoFormMutation` (the model-less sibling — its own metaclass + declaration
    registry + `bind_form_mutations()` wired into [`types/finalizer.py`][types-finalizer],
    [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
    / [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).
    The form-flavor `_validate_meta` override: `Meta.form_class` is required. In
    Django, **`forms.ModelForm` is NOT a subclass of `forms.Form`** — both are
    siblings under `forms.BaseForm` (`issubclass(ModelForm, Form)` is `False`;
    `ModelForm` → `BaseModelForm` → `BaseForm`, `Form` → `BaseForm`). So the plain
    `DjangoFormMutation` **checks `issubclass(form_class, forms.ModelForm)` first** and
    raises a `ConfigurationError` naming `DjangoModelFormMutation` as the correct base
    (a *targeted* message — without this explicit check a bare `issubclass(…,
    forms.Form)` gate would still reject a `ModelForm`, but with a confusing generic
    "not a `Form`" message; and the targeting matters because, were a `ModelForm` let
    through, it would silently write via `form.save()` and return only `{ ok errors }`
    with no object slot, no `DjangoModelPermission` default, and no optimizer re-fetch,
    defeating the two-base split, P2). It then requires a `forms.Form` subclass.
    `DjangoModelFormMutation` requires a `forms.ModelForm` subclass. The check runs
    **before** `_resolve_model` (so a missing / wrong-type `form_class` is a clean
    [`ConfigurationError`][glossary-configurationerror], never a raw `AttributeError`
    from `form_class._meta.model`); a `ModelForm` with no resolvable `_meta.model`
    raises. **`operation` is split by base (P2):** `DjangoModelFormMutation` requires
    `Meta.operation ∈ {"create", "update"}` (a `"delete"` form mutation is **rejected**
    — the form flavor has no delete pipeline,
    [Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete)),
    and its shape-identity operation component is that value; the plain
    `DjangoFormMutation` **rejects any `Meta.operation`** as unsupported (a model-less
    mutation has no model operation — Decision 10) and uses the fixed identity
    sentinel **`"form"`** for its input-shape cache key
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)).
    The form allowed-key set adds `form_class` and drops `model` / `input_class` /
    `partial_input_class`; `Meta.fields` / `Meta.exclude` are mutually exclusive.
  - [x] No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`: a
    form-mutation `Meta` is its own validation namespace
    ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)).
  - [x] Package coverage: [`tests/forms/test_sets.py`][test-forms] — the `Meta`
    validation matrix (missing / wrong-type `form_class`, a `ModelForm` on the plain
    base rejected naming `DjangoModelFormMutation`, `ModelForm`-with-no-model,
    `DjangoModelFormMutation` `operation = "delete"` rejected, **any `Meta.operation`
    on the plain base rejected** (P2), `form_class` accepted as a known key,
    `fields` + `exclude` both set, unknown key), **plain-form input dedupe** (the
    `"form"` sentinel — two plain mutations over one form + effective set dedupe),
    registration, finalizer binding (both the `DjangoMutation`-path bind and the
    `bind_form_mutations()` path), the no-registered-primary-type error for
    `DjangoModelFormMutation`, and the
    model-flavor seam defaults unchanged (a `DjangoMutation` still validates +
    materializes its model-column input exactly as before).

---

## Build report (Worker 2)

### Files touched

Slice-intended (all in my diff, confirmed via `git status --short`):

- `django_strawberry_framework/mutations/sets.py` — added `make_declaration_registry(label)` + the `DeclarationRegistry` NamedTuple; re-based the model-flavor quad onto it (`register_mutation` / `clear_mutation_registry` / `iter_mutations` / `_mutation_registry` now the factory's bound names); relocated the `_validate_mutation_meta` body verbatim into `DjangoMutation._validate_meta(cls, meta)` (module-level function removed; metaclass calls `new_class._validate_meta(meta)`); added the `build_input` / `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async` seams (each defaulting to today's model behavior); extended `_ValidatedMutationMeta` with an optional `form_class` slot (None on the model path); `_bind_mutation` now routes the input through `mutation_cls.build_input(meta, primary_type)`.
- `django_strawberry_framework/forms/sets.py` (new) — `DjangoModelFormMutation` (rides `DjangoMutation`; overrides `_resolve_model` → `form_class._meta.model`, `_validate_meta`, `build_input`, `input_type_name`, `input_module_path`, `resolve_*` stubs); `DjangoFormMutation` + `DjangoFormMutationMetaclass` (model-less; own declaration registry via `make_declaration_registry`); `bind_form_mutations()`; the two allowed-key sets; the `_cached_build_form_input` shape cache + `clear_form_shape_build_cache`.
- `django_strawberry_framework/mutations/inputs.py` — `build_payload_type` now accepts `object_type=None` → emits the model-less `{ ok errors }` payload (the model branch is byte-unchanged).
- `django_strawberry_framework/mutations/fields.py` — added a `TODO(spec-038 Slice 3)` anchor on `_input_type_name` documenting the transient duplication with the new `input_type_name` seam (Slice 3 deletes the helper).
- `django_strawberry_framework/registry.py` — three new `_clear_if_importable` co-clear rows (`forms.inputs::clear_form_input_namespace`, `forms.sets::clear_form_mutation_registry`, `forms.sets::clear_form_shape_build_cache`).
- `django_strawberry_framework/types/finalizer.py` — wired a function-local `bind_form_mutations()` into the phase-2.5 window after `bind_mutations()`.
- `django_strawberry_framework/forms/__init__.py` — re-exports the two bases + `__all__`.
- `django_strawberry_framework/__init__.py` — `.forms` import + the two `__all__` entries (alphabetical). `__version__` NOT touched.
- `tests/forms/test_sets.py` (new) + `tests/mutations/test_sets.py` (extended) — see Tests added.

### Tests added

- `tests/forms/test_sets.py` (new, 31 tests): the full `Meta` validation matrix (missing/wrong-type `form_class`; `ModelForm` on the plain base rejected naming `DjangoModelFormMutation`; non-`ModelForm` on the `ModelForm` base; `ModelForm`-with-no-model raising a clean `ConfigurationError`; `operation="delete"` and missing-operation rejected on the `ModelForm` base; ANY `operation` rejected on the plain base, parametrized create/update/delete/upsert; `form_class` accepted on both flavors with snapshot assertions incl. the `"form"` sentinel; unknown key on both; `model` is unknown on the plain base; `fields`+`exclude` both set on both; unknown-name narrowing routed through the Slice-1 machinery), permission default + plain `[]` opt-out, registration (disjoint ledgers, abstract bases nowhere, idempotency, post-finalize reject), both bind paths (the `ModelForm` ride materializing into `forms.inputs` + a model-backed `node` payload; the plain bind with the `{ ok errors }` payload), plain-form `"form"`-sentinel dedupe, the no-registered-primary-type finalize error, and the package-root export check.
- `tests/mutations/test_sets.py` (4 new tests at the end): `_validate_meta` is the relocated classmethod seam (module-level `_validate_mutation_meta` gone; `form_class` slot None on the model flavor); the model-flavor input seams produce today's defaults (`input_module_path == mutations.inputs`, `input_type_name == "ItemInput"`, the bind materializes the model-column input with `name`/`category_id`); `resolve_sync`/`resolve_async` exist + delegate to the resolver entry points; `make_declaration_registry` dedupes + rejects post-finalize.

### Validation run

1. `uv run ruff format .` → 273 files unchanged (clean after edits).
2. `uv run ruff check --fix .` → All checks passed (the only manual fixes: `# noqa: A002` on the four `id:` seam params; `scripts/check_trailing_commas.py --fix` applied layout to the three edited source files + the new test).
3. `git status --short` — slice-intended files listed under **Files touched** above (the 6 tracked `M` files + `tests/mutations/test_sets.py`, plus the untracked `django_strawberry_framework/forms/` and `tests/forms/` dirs containing the Slice-1 + Slice-2 files). **Out-of-scope concurrent / not-mine, left untouched:** `docs/feedback.md` (dirty at task start), the deleted `docs/builder/bld-*.md` + `docs/builder/build-037-*.md` (spec-037 concurrent cleanup). No `examples/fakeshop/db.sqlite3` or `KANBAN.html` churn appeared.
4. Focused tests (no `--cov*`): `tests/forms/test_sets.py tests/mutations/test_sets.py` → 82 passed; full `tests/forms/ tests/mutations/` → 249 passed (confirms no model-flavor regression across the mutation surface).

### Implementation notes

- **`make_declaration_registry` return shape**: a `DeclarationRegistry(NamedTuple)` with `(register, clear, iter_, store)`. The `store` handle is exposed (not just the three callables) so `_mutation_registry` / `_form_mutation_registry` stay introspectable by the idempotency tests (`.count(...)`), matching the existing test contract. The model quad assigns the three callables to the same public names `registry.py` / the metaclass / `fields.py` / tests reference.
- **`_validate_mutation_meta` removed (not shimmed)**: its only caller was the metaclass, now calling `new_class._validate_meta(meta)`. A test asserts the module-level name is gone. The body was cut/pasted into the classmethod (`mutation_cls`→`cls`, `name = cls.__name__`) — Worker 3 can diff it against the pre-refactor body for byte-identity.
- **`_ValidatedMutationMeta.form_class` slot** (the flagged structural choice): implemented the plan's recommended path — one snapshot shape, `form_class` defaulted None so the model path is byte-unchanged. The model `_validate_meta` does not set it; the form overrides do.
- **Model-less payload builder** (the flagged `mutations/inputs.py` edit): implemented `build_payload_type(object_type=None)` → `{ ok: bool, errors: list[FieldError] }`, routed through the SAME `materialize_mutation_input_class` ledger as the model payloads (one ledger, one collision raise, one co-clear). The model (`object_type` non-None) branch is byte-unchanged. This is the single-source DRY choice; it IS a `mutations/inputs.py` edit outside the spec's Slice-2 file list — see Notes for Worker 1.
- **Form `_validate_meta`: two classmethod bodies + a shared `_require_form_class` / `_resolve_effective_form_field_names` core** (not one flag-driven body), keeping the two divergences (the plain base's `ModelForm`-first reject; the `operation` split) explicit. `permission_classes` / narrowing reuse the existing `_validate_permission_classes` + the Slice-1 `resolve_effective_form_fields` rather than re-spelling them.
- **Plain-base `operation` reject ordering** (drift; see Notes for Worker 1): the plain base checks `Meta.operation is not None` FIRST with a targeted "operation is not supported" message, THEN runs the unknown-key guard over the remainder minus `operation`. Without this, the unknown-key guard fired first and produced a generic `unknown keys: ['operation']` message — the plan/spec explicitly wants the targeted reject. `operation` is recognized-but-rejected, not merely unknown.
- **Form input shape cache** (drift; see Notes for Worker 1): the plan's `build_input` overrides called `build_form_input_class` directly, which builds a FRESH class each call — so two mutations over one form-shape handed the materialize ledger two distinct same-named classes and tripped the AR-M6 collision instead of deduping (caught by the `"form"`-sentinel dedupe test). Added `_form_shape_build_cache` keyed on `(form_class, operation_kind, frozenset(effective))` — the exact twin of the model's `_shape_build_cache` — consulted by `_cached_build_form_input`, cleared at `bind_form_mutations()` start and co-cleared from `registry.clear()`. Both flavors' `build_input` route through it.
- **`build_input` create path uses `build_form_inputs`** (not the single `build_form_input_class`) for the `CREATE` / `FORM` kinds so the Slice-1 create-required-narrowing guard fires; the discarded partial is the cost of reusing the guarded entry point. `PARTIAL` builds the partial directly (no create guard). `guard_required=True` always for now — the `get_form_kwargs` waiver is `TODO(spec-038 Slice 3)`-anchored.
- **`resolve_sync` / `resolve_async` import placement**: the model seams use a function-local `from .resolvers import ...` (the plan's recommended cycle-safe choice; verified `resolvers.py` does not import `sets.py` at module top, so a top import would also be acyclic — local kept for safety). The form `resolve_*` are `TODO(spec-038 Slice 3)`-anchored `NotImplementedError` stubs.

### Notes for Worker 3

- No `scripts/review_inspect.py` shadow files were consulted during the build (Worker 1's planning pass already ran them; the diff is the source of truth).
- The byte-identity check for the no-regression gate: diff `DjangoMutation._validate_meta`'s body against the pre-refactor module-level `_validate_mutation_meta` (only `mutation_cls`→`cls` + the `name =` line changed). The model `build_input` default = `_materialize_input_for(cls.__name__, meta, primary_type)` (unchanged helper); `input_type_name` default = the relocated `fields.py::_input_type_name` body; `resolve_*` defaults = the resolver entry points.
- The two drift items (plain-base `operation`-reject ordering; the form shape cache) are also flagged under Notes for Worker 1 — both are small, within-contract, and tested.

### Notes for Worker 1 (spec reconciliation)

1. **`mutations/inputs.py::build_payload_type(object_type=None)`** — this IS a `mutations/inputs.py` edit outside the spec's Slice-2 file list (Decision 6 pins the plain-form `{ ok errors }` payload SHAPE but does not name the builder). I implemented the plan's recommended single-source path (the model branch byte-unchanged, the None branch net-new). Confirm this is the intended single-source rather than a dedicated `forms/` builder, and reconcile the Slice-2 file list to include `mutations/inputs.py`.
2. **`_ValidatedMutationMeta.form_class` slot** — implemented the plan's recommended extend-the-snapshot path (one shape; model path leaves it None). Confirm.
3. **Plain-base `operation`-reject ordering (drift)** — the plain `_validate_meta` rejects `Meta.operation` with a TARGETED "operation is not supported" message BEFORE the unknown-key guard (and excludes `operation` from the unknown set). The spec/plan wants the targeted reject; the natural unknown-key-guard-first ordering would have produced a generic `unknown keys: ['operation']` instead. Small, within-contract, tested — flagging for your final-verification audit.
4. **Form input shape cache (drift)** — added `_form_shape_build_cache` (the twin of the model's `_shape_build_cache`) because the plan's direct `build_form_input_class` call in `build_input` would have built a fresh class per call and tripped the materialize collision raise instead of deduping (the spec's `"form"`-sentinel dedupe requirement). Co-cleared from `registry.clear()` (a third form co-clear row beyond the two the plan named) and at `bind_form_mutations()` start. Small, within-contract, tested. Reconcile the Slice-2 registry-co-clear count (3 form rows, not 2) and note the cache in the spec if desired.

---

## Review (Worker 3)

Scope filter: I weighed only the Slice-2 contribution per `### Files touched` — the
tracked `M` files (`mutations/sets.py`, `mutations/inputs.py`, `mutations/fields.py`,
`registry.py`, `types/finalizer.py`, `__init__.py`, `tests/mutations/test_sets.py`),
the new `forms/sets.py` + `tests/forms/test_sets.py` + `forms/__init__.py` re-export.
The deleted `docs/builder/bld-*.md` + `build-037-*.md` and the dirty `docs/feedback.md`
are out-of-scope baseline-resolved drift (spec-037 cleanup + the maintainer's feedback
edit), left untouched. No `db.sqlite3` / `KANBAN.html` churn appeared from my focused
test run.

### High:

None.

### Medium:

None.

### Low:

#### `mutations/fields.py::_input_type_name` docstring has a double blank line after the TODO anchor

Severity: Low (cosmetic; not load-bearing).
Source: `django_strawberry_framework/mutations/fields.py::_input_type_name` (the
`TODO(spec-038 Slice 3)` anchor block, just before the `"Mirrors the bind's name
choice"` paragraph).
Why it matters: the inserted Slice-3 TODO-anchor paragraph left two consecutive blank
lines inside the docstring before the original prose. Purely stylistic; ruff does not
flag blank lines inside a docstring, and the whole helper + its body are deleted in
Slice 3 (the anchor says so), so this self-resolves. No behavior impact.
Recommended change: collapse to a single blank line if Worker 2 re-touches the file;
otherwise leave — Slice 3 deletes the helper wholesale.
Test expectation: none (no behavior change).

### DRY findings

- **`make_declaration_registry(label)` correctly single-sources the registry quad with
  DISJOINT ledgers.** Verified the over-DRY trap Decision 13 names is avoided: the model
  flavor instantiates `make_declaration_registry("DjangoMutation")` over its own
  `store` list (`mutations/sets.py` lines 191-195) and the plain-form flavor instantiates
  a SECOND `make_declaration_registry("DjangoFormMutation")` over a separate `store`
  (`forms/sets.py` lines 106-110). The dedup-by-identity / post-`mark_finalized()` reject
  / `.clear()` / ordered-`tuple()` mechanics are one body; the storage is two lists. The
  `DeclarationRegistry` NamedTuple exposes `store` so the idempotency tests introspect
  `.count(...)`. Clean — no clone of the four bodies into `forms/sets.py`.
- **Form `_validate_meta` reuses the Slice-1 narrowing machinery, not a re-spell.** Both
  flavor validators route field narrowing through
  `_resolve_effective_form_field_names` → Slice-1 `resolve_effective_form_fields`
  (mutual-exclusion / bare-string / duplicate / unknown-name / empty-set fail-loud), and
  `permission_classes` through the shared `mutations/sets.py::_validate_permission_classes`.
  No copy of the `036` matrix.
- **`build_payload_type(object_type=None)` single-sources the payload builder.** The
  model branch (`else`) is byte-unchanged; the model-less `{ok, errors}` branch is
  net-new and routes through the SAME `materialize_mutation_input_class` ledger (one
  ledger, one AR-M6 collision raise, one co-clear). Confirmed the `"ok"` literal appears
  only in the new None branch (`mutations/inputs.py` lines 581-582).
- **`_form_shape_build_cache` is the deliberate twin of the model `_shape_build_cache`.**
  Not a DRY violation: the two caches key on different identity tuples (model vs
  form_class) and live in their own modules; the cache *pattern* is intentionally
  mirrored (and documented as such). The form one is required so two mutations over one
  form-shape dedupe instead of tripping the materialize collision (Worker 2 reconciliation
  item 4). Verified live: the `test_plain_form_input_dedupes_via_form_sentinel` test
  proves two plain mutations over one form reuse one class object.
- **Minor, transient (no action):** the `"form resolver pipeline lands in spec-038 Slice
  3"` `NotImplementedError` string repeats 4x across the resolver stubs, and the
  `mutations/fields.py::_input_type_name` body is byte-identical to the new
  `DjangoMutation.input_type_name` seam. Both are Slice-3-removed (the stubs become the
  real pipeline; the helper is deleted), TODO-anchored, and explicitly flagged. Not a
  standing DRY defect — do not extract a constant for a string the next slice deletes.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` adds exactly two re-exports and two
`__all__` entries: `from .forms import DjangoFormMutation, DjangoModelFormMutation` (with
`# noqa: E402`) and `"DjangoFormMutation"` + `"DjangoModelFormMutation"` inserted
alphabetically (after `DjangoFileType` / before `DjangoImageType`, and after
`DjangoListField` / before `DjangoModelPermission`). `__version__` is unchanged at
`"0.0.11"` (line 37) — the Slice-5 bump is correctly NOT taken here. This public-surface
change is AUTHORIZED by spec Decision 5 (lines 972-978: "Two net-new public symbols,
re-exported from `__init__.py` and added to `__all__`") and the build-plan flag (Slice 2
adds the two exports WITHOUT bumping `__version__`). `forms/__init__.py` re-exports the
two bases + an `__all__` tuple. Confirmed correct and authorized.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The only public-surface/release-adjacent change is `__init__.py`'s `__all__` + re-export
block, which IS a public-surface change AUTHORIZED by spec Decision 5 / DoD item 8.
Confirmed: it adds exactly `DjangoFormMutation` + `DjangoModelFormMutation` (no other
symbol), inserts both alphabetically, and does NOT bump `__version__` (stays `"0.0.11"`;
the version quintet alignment is Slice 5 per the build-plan flag). No KANBAN / GLOSSARY /
spec-archive surfaces touched this slice (those are Slice 5). No obsolete
"coming soon" / version wording introduced.

### What looks solid

- **No-model-flavor-regression gate HOLDS (the highest-risk axis).** Verified
  `DjangoMutation._validate_meta` is the RELOCATED `_validate_mutation_meta` body, not a
  re-implementation: an executable-token diff against pristine HEAD
  (`git show HEAD:…/mutations/sets.py`) — whitespace + comments stripped, `mutation_cls`
  normalized to `cls` — is byte-identical. The only deltas are (a) +4-space indent
  (module fn → classmethod), (b) the `delete` comment re-wrapped at a different column by
  the formatter (word-for-word identical prose), (c) `mutation_cls` → `cls`. The metaclass
  now calls `new_class._validate_meta(meta)` (line 420) dispatching to the overridable
  classmethod. `_ALLOWED_MUTATION_META_KEYS` / `_VALID_OPERATIONS` are byte-unchanged.
  `types/base.py` is byte-unchanged → `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS`
  untouched.
- **The seam DEFAULTS reproduce today's model behavior.** `build_input` delegates to the
  unchanged `_materialize_input_for(cls.__name__, meta, primary_type)`; `input_type_name`
  is the relocated `fields.py::_input_type_name` body; `input_module_path = INPUTS_MODULE_PATH`
  (the `mutations.inputs` path); `resolve_sync`/`resolve_async` delegate to
  `resolvers.py::resolve_mutation_sync`/`resolve_mutation_async` via cycle-safe
  function-local imports (verified `resolvers.py` does NOT import `sets.py` at module top,
  so the local import is a safety choice, not a necessity). `_bind_mutation` routes input
  materialization through `mutation_cls.build_input(meta, primary_type)` — the model
  default rebuilds the model-column input identically. Tests
  (`test_model_flavor_input_seams_produce_today_defaults`,
  `test_validate_meta_is_the_relocated_classmethod_seam`,
  `test_model_flavor_resolve_seams_delegate_to_resolver_entry_points`) pin each. The
  plan's byte-identity assertion exists and is meaningful.
- **The form `_validate_meta` matrix is complete and correctly ordered.** Both flavors
  require `form_class` (clean `ConfigurationError`, no raw `AttributeError`). The plain
  base checks `issubclass(form_class, forms.ModelForm)` FIRST → rejects naming
  `DjangoModelFormMutation` (targeted Edge-case message), THEN requires `forms.Form`;
  rejects ANY `Meta.operation` (checked first, targeted message); allowed-key set
  `{form_class, fields, exclude, permission_classes}` (no `operation`, no `model`);
  snapshot uses `operation=FORM` ("form" sentinel) + `model=None`. The ModelForm base
  requires `forms.ModelForm` BEFORE `_resolve_model` (so wrong-type / missing model is a
  clean error, never `AttributeError`); `operation ∈ {"create","update"}` rejecting
  `"delete"`; ModelForm-with-no-model raises ("resolves no model"); allowed-key set adds
  `form_class`, drops `model`/`input_class`/`partial_input_class`. `fields`/`exclude`
  mutual exclusion via Slice-1 machinery. Every matrix branch has a pinning test in
  `tests/forms/test_sets.py` (31 tests; I walked each branch against a test).
- **`bind_form_mutations()` is wired into the SINGLE phase-2.5 window** in
  `finalize_django_types()` (after `bind_mutations()`, function-local import, mirroring
  the existing idiom) — no second public finalize entry point (Decision 13). The
  `registry.clear()` co-clear adds three form rows (the two the plan named +
  `clear_form_shape_build_cache`), byte-shape-identical to the existing mutation co-clear
  rows.
- **The `resolve_*` stubs are the ONLY deferred piece** and all four carry the
  `TODO(spec-038 Slice 3)` anchor naming the spec + slice per AGENTS.md. Grep confirms no
  other `NotImplementedError` / un-anchored deferral in the slice. The plain-form stubs
  correctly drop the `id:` param (model-less — no instance to locate); the ModelForm
  stubs keep it.
- **Worker 2's 4 reconciliation items assessed (see Notes for Worker 1).** All four are
  clean, within-contract, tested implementation choices — I escalate two for Worker 1's
  spec-list reconciliation (file-list + co-clear-count) but none is a defect.
- 82 focused tests pass (`tests/forms/test_sets.py` 31 + `tests/mutations/test_sets.py`
  51), no coverage flags, no `db.sqlite3`/`KANBAN.html` churn.

### Temp test verification

No temp tests were needed. The artifact's permanent tests already pin every branch I
wanted to verify (the byte-identity, both bind paths, the plain-form dedupe, the
no-primary-type finalize error, the post-finalize reject). I additionally ran a manual
executable-token diff of the relocated `_validate_meta` body against pristine HEAD
(documented under `What looks solid`) — a one-off shell diff, no temp test file created.
Disposition: none created; nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated (file-list reconciliation): `mutations/inputs.py::build_payload_type(object_type=None)`
   is outside the spec's Slice-2 file list.** This is the clean single-source choice the
   plan recommended (model `else` branch byte-unchanged; model-less None branch net-new,
   one ledger). It is correct and tested. Worker 2 already flagged it (build-report
   reconciliation item 1). Resolution paths: (a) reconcile the Slice-2 file list to
   include `mutations/inputs.py` (recommended — confirms `build_payload_type(object_type=None)`
   as the intended single-source per Decision 6's pinned `{ok, errors}` shape), or (b)
   move the model-less builder into `forms/` (rejected by the plan's DRY analysis; would
   fork the payload builder + the materialize ledger). Not a defect either way.

2. **Escalated (co-clear-count reconciliation): `registry.clear()` adds THREE form rows,
   not two.** The plan named two (`clear_form_input_namespace` + `clear_form_mutation_registry`);
   Worker 2 added a third (`clear_form_shape_build_cache`) because the form-input build
   cache needs the same per-pass reset the model `_shape_build_cache` gets (cleared at
   `bind_form_mutations()` start AND co-cleared from `registry.clear()` so a stale class
   from a failed/re-run finalize cannot leak). Correct and necessary (the dedupe test
   depends on it). Worker 2 flagged it (reconciliation item 4). Resolution: confirm the
   third co-clear row + note the form shape cache in the spec/Decision-13 if desired. Not
   a defect.

3. **`_ValidatedMutationMeta.form_class` slot (reconciliation item 2)** — clean. The plan's
   recommended one-snapshot-shape path; the model path leaves it `None` (verified by
   `test_validate_meta_is_the_relocated_classmethod_seam`), so the model bind/resolver
   never read it. No reconciliation needed beyond confirming the plan's recommendation
   landed.

4. **Plain-base `operation`-reject ordering (reconciliation item 3)** — clean and within
   contract. The plain `_validate_meta` checks `Meta.operation is not None` FIRST with a
   targeted "operation is not supported" message, then runs the unknown-key guard over
   `declared - _ALLOWED_PLAIN_FORM_META_KEYS - {"operation"}`. This produces the targeted
   reject the spec/plan want (Decision 10: `operation` is recognized-but-rejected, not
   merely unknown). The `- {"operation"}` is defensive (operation is already rejected
   above), harmless. Tested by `test_plain_base_rejects_any_operation` (parametrized
   create/update/delete/upsert). No spec edit required; flagged for your final-verification
   audit only.

5. **(Low-priority, NOT a defect) The spec test-plan line 2032-2034 lists a `create`
   narrowing dropping a required form field → `ConfigurationError` under `test_sets.py`.**
   The Slice-2 verbatim checklist (build-artifact lines 196-207) does NOT enumerate this
   sub-case, and the guard's raise path IS covered at the Slice-1 level
   (`tests/forms/test_inputs.py::test_create_guard_rejects_dropping_required_field_via_fields`
   / `_via_exclude`). Architecturally the guard fires at `build_input` (the bind), not at
   `_validate_meta` (class creation), and the `guard_required` waiver is `TODO(spec-038
   Slice 3)`-anchored (the `get_form_kwargs` hook does not exist yet). So the spec's
   "rejected at class creation" framing for this case is a Slice-3-era contract once the
   waiver wires in. Not blocking Slice 2 (the behavior is covered; the verbatim checklist
   does not require it here). Worth weighing at the integration pass / Slice 3 whether the
   Meta-level raise test belongs in `test_sets.py` per the spec test plan.

### Review outcome

`review-accepted`. The no-model-flavor-regression gate holds (executable-byte-identical
relocated validator + seam defaults reproducing today's model behavior, all pinned by
tests). The form `_validate_meta` matrix, the disjoint-ledger `make_declaration_registry`,
the single phase-2.5 `bind_form_mutations()` wiring, and the TODO-anchored Slice-3 stubs
all match the spec. Zero High, zero Medium findings; one cosmetic Low (a docstring
double-blank-line that Slice 3 deletes wholesale). The verbatim Slice-2 checklist boxes
match the diff. Two Medium-adjacent items (the `mutations/inputs.py` file-list addition
and the 3rd co-clear row) are transparently escalated to Worker 1 for spec-list
reconciliation — both are clean, tested, within-contract implementation choices, not
defects, so they do not block acceptance.

---

## Final verification (Worker 1)

Status: **final-accepted**.

### Summary

Slice 2 delivers its contract: the `036` model-driven mutation surface is refactored
into overridable seams (`_validate_meta`, `build_input`, `input_type_name`,
`input_module_path`, `resolve_sync`, `resolve_async`) **each defaulting to today's
exact model behavior**, and the two form-mutation bases ship on top —
`DjangoModelFormMutation` (rides `DjangoMutation` via the `_resolve_model` override)
and the model-less plain `DjangoFormMutation` (own metaclass + disjoint declaration
registry + `bind_form_mutations()`). The `make_declaration_registry(label)` factory
single-sources the register/clear/iter/reject quad while keeping the two ledgers
disjoint (Decision 13, over-DRY trap avoided). `bind_form_mutations()` is wired into
the single phase-2.5 finalizer window; `registry.clear()` co-clears three form rows;
the two bases export from the package root (`__version__` NOT bumped — Slice 5). The
form resolver pipeline (`resolve_*` bodies, `get_form_kwargs`, `mutations/fields.py`
generalization) is correctly staged to Slice 3 via `TODO(spec-038 Slice 3)` anchors.

**Spec slice checklist audit:** all 5 boxes (1 top-level + 4 nested) verified `- [x]`
against the diff. No over-ticks, no silent un-ticks. Each contract landed:
`mutations/sets.py` seams (✓ source lines 469/581/584/598/633/654 + the metaclass
dispatch at 420 + `_bind_mutation` routing at 1024); `forms/sets.py` both bases (✓
classes at 213/456 + `DjangoFormMutationMetaclass` at 425 + `bind_form_mutations()` at
658); no `DEFERRED_META_KEYS`/`ALLOWED_META_KEYS` change (✓ `types/base.py` byte-zero
diff); `tests/forms/test_sets.py` matrix (✓ 31 tests, the full Meta matrix +
both-bind-paths + dedupe + no-primary-type error).

**No-model-flavor-regression — independently re-confirmed (the load-bearing gate):**
- `DjangoMutation._validate_meta` is the RELOCATED `_validate_mutation_meta` body, not
  a re-implementation. I ran an independent executable-token diff (Python `tokenize`,
  comments/docstrings/whitespace stripped, `mutation_cls`→`cls` normalized) of the
  current classmethod body against pristine `HEAD`: **334 tokens each, identical.**
- `_ALLOWED_MUTATION_META_KEYS` / `_VALID_OPERATIONS` frozensets byte-unchanged (the
  diff only moves their *references* into the relocated classmethod).
- Seam defaults reproduce today's behavior: `build_input` → unchanged
  `_materialize_input_for`; `input_type_name` → the relocated `fields.py` body
  single-sourced via `mutation_input_type_name`; `input_module_path = INPUTS_MODULE_PATH`;
  `resolve_sync`/`resolve_async` → `resolvers.py::resolve_mutation_sync`/`_async`.
- `mutations/inputs.py::build_payload_type`: the model branch (`else`) is byte-identical
  to HEAD; only the signature widened (`object_type: type | None`) and a net-new
  `if object_type is None:` branch (the `{ ok errors }` model-less payload) was added,
  never reached by the model flavor. Routed through the SAME `materialize_mutation_input_class`
  ledger (one ledger, one collision raise, one co-clear).
- `mutations/fields.py`: TODO-anchor docstring only, zero logic change (verified via
  `git diff`). Acceptable staging — the generalization is Slice 3 (spec Implementation
  plan table, Slice 3 row).

**DRY check across Slice 1 + Slice 2:** no new standing duplication. The integration-pass
candidates from my memory are all confirmed present-at-both-sites and correctly DEFERRED,
NOT Slice-2 blockers: (a) `make_declaration_registry` already single-sources the quad
(both sites verified disjoint); (b) `_form_shape_build_cache` is the deliberate, documented
twin of `_shape_build_cache` (different identity tuples, different modules) — a Slice-3/
integration lift candidate at best, not a defect; (c) `_pascalize_token` is imported
(forms/inputs.py + mutations/inputs.py), not re-spelled; (d) `normalize_form_field_sequence`
vs `mutations/sets.py::_normalize_field_sequence` near-twin stays an INTEGRATION-pass lift
candidate (do NOT re-flag as a Slice-2 blocker). The transient
`fields.py::_input_type_name` ↔ `DjangoMutation.input_type_name` duplication and the 4x
`NotImplementedError` string are TODO-anchored and Slice-3-removed — not standing defects.

**Existing tests:** `uv run pytest tests/forms/ tests/mutations/ --no-cov` → **249 passed**
(no coverage flags). Confirms no model-flavor regression across the mutation surface.

**`mutations/fields.py` TODO-anchor staging:** confirmed acceptable. The diff is the
`TODO(spec-038 Slice 3)` anchor only; the generalization (target-check, `_resolve`
dispatch, `data:` lazy-ref derivation) is the spec's Slice-3 contract. Worker 3's Low
(a docstring double-blank-line) is cosmetic, ruff-clean, and self-resolves when Slice 3
deletes the helper wholesale — not a blocker.

**Worker 3's 3 escalated items resolved (see Spec changes below):** (1) `mutations/inputs.py`
file-list reconciliation → spec edited; (2) the 3rd `registry.clear()` co-clear row + the
form shape cache → noted in Decision 13; (3) the create-narrowing-drops-required timing
(fires at `build_input`/bind, not class creation, with the `guard_required` waiver still
`TODO(spec-038 Slice 3)`) → carried to Slice 3 / integration, the raise path is already
Slice-1-covered, no Slice-2 spec edit needed.

### Spec changes made (Worker 1 only)

`docs/SPECS/spec-038-form_mutations-0_0_12.md`:

1. **Line 42 (status/header line)** — `Status: **PLANNED** … not yet implemented` →
   `Status: **IN PROGRESS** … Slices 1–2 built and accepted …, Slices 3–5 remain. Slice
   5 flips this line to shipped at the 0.0.12 cut`. Reason: the per-spawn status-line
   re-verification rule — "not yet implemented" was stale now that Slices 1–2 are built;
   the flip to "shipped" stays Slice 5's job (the version cut).
2. **Implementation plan table, Slice 2 row (line 1860)** — added `mutations/inputs.py`
   (`build_payload_type(object_type=None)` single-source for the model-less `{ ok errors }`
   payload, model branch byte-unchanged) and `mutations/fields.py` (TODO-anchor-only
   staging) to the file list; updated the `registry.py` cell to name THREE form co-clear
   rows. Reason: Worker 3 escalation 1 — the shipped diff touches two files the Slice-2
   file list omitted; both are the plan's recommended single-source / staging choices,
   confirmed correct and tested. (Resolves Worker 2 reconciliation item 1 + Worker 3 note 1.)
3. **Decision 13 (after the `bind_form_mutations()` machinery sentence, ~line 1772)** —
   added a sentence pinning that `registry.clear()` co-clears THREE form rows
   (`clear_form_input_namespace` + `clear_form_mutation_registry` + `clear_form_shape_build_cache`)
   and explaining the form-input build cache is the deliberate twin of the model
   `_shape_build_cache` (needed for plain-form dedupe; cleared at `bind_form_mutations()`
   start AND co-cleared so a stale class from a failed/re-run finalize cannot leak).
   Reason: Worker 3 escalation 2 — the spec/plan implied two co-clear rows; the third is
   necessary and within-contract. (Resolves Worker 2 reconciliation item 4 + Worker 3 note 2.)

No edit needed for Worker 2 reconciliation items 2 (the `_ValidatedMutationMeta.form_class`
slot — the plan's recommended one-snapshot-shape path landed; model path leaves it None,
verified by test) and 3 (the plain-base `operation`-reject ordering — produces the targeted
reject Decision 10 wants, within contract, tested). Worker 3 escalation 3 (create-narrowing
timing) is carried to Slice 3, not a Slice-2 spec change.

`check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md` → exit 0
(31 terms) after the edits; no link-rot introduced (`[mutations-inputs]` / `[mutations-fields]`
link defs already present).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->
[test-forms]: ../../tests/forms/

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
