# Build: Slice 2 — the `SerializerMutation` base + `Meta` validation + the phase-2.5 bind

Spec reference: `docs/spec-039-serializer_mutations-0_0_13.md` (lines 749-873; Decision 5 1615-1668, Decision 6 1670-1761, Decision 10 2394-2447, Decision 11 2449-2473, Decision 12 2475-2591; Cross-flavor reuse P1.2/P1.6/P1.7/P2.5/P2.6/P2.7 + import manifest 2697-2899; Test plan `test_sets.py` 3223-3233 + DRF-absent guard 3276-3290; DoD item 3 3546-3571)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

This slice carries the heaviest DRY contract of the build. Centerpiece is the
`register_subsystem_clear` seam plus four other promotions. Verified at source.

**Existing patterns reused (cite file:line).**

- `mutations/sets.py::DjangoMutation` (`django_strawberry_framework/mutations/sets.py:438`)
  + its metaclass (`:408`) + `register_mutation` (`:208`) — `SerializerMutation`
  subclasses `DjangoMutation`, so it rides the SAME metaclass `__new__` (validate
  `Meta` → register in the model-flavor declaration registry) and the SAME
  `bind_mutations()` (`:1054`) phase-2.5 path. No new metaclass, no new registry, no
  new bind entry — the dividend of the `ModelSerializer`-rides-`DjangoMutation` choice
  (Decision 6).
- `mutations/sets.py::_validate_permission_classes` (`:352`) — reused verbatim by the
  serializer `_validate_meta` (defaults `[DjangoModelPermission]` when unset; the `036`
  write-auth seam inherited unchanged, Decision 11). No re-spell.
- `mutations/sets.py::_normalize_field_sequence` (`:335`) — the MODEL flavor's field
  normalize; the serializer follows the model precedent (P2.5). BUT the spec (P2.7)
  requires the serializer call `utils/inputs.py::normalize_field_name_sequence(...,
  flavor="SerializerMutation")` (`django_strawberry_framework/utils/inputs.py:186`)
  **directly** — no third re-binding wrapper. NOTE: `rest_framework/inputs.py` already
  exposes `normalize_serializer_field_sequence` (`:181`, a Slice-1 wrapper) used by the
  input-narrowing path; `sets.py::_validate_meta` consumes `resolve_effective_serializer_fields`
  (Slice 1, which already routes narrowing through that wrapper), so `sets.py` itself
  does NOT add a second wrapper — it reuses the Slice-1 effective-field resolver. See
  Implementation discretion item D1.
- `mutations/sets.py::_ValidatedMutationMeta` (`:287`) — the validated snapshot the
  serializer `_validate_meta` returns. It already carries a `form_class` slot (`:332`,
  net-new state for `038`); the serializer needs a `serializer_class` slot the same way
  the form added `form_class`. See D2 below — `_ValidatedMutationMeta` must grow a
  `serializer_class` (and the snapshot must carry `optional_fields`).
- `mutations/inputs.py::{CREATE, PARTIAL}` (`:76-77`) — the operation→input-kind
  sentinels; the serializer `build_input`/`input_type_name` map `create→CREATE`,
  `update→PARTIAL` exactly as the model/form flavors do.
- `forms/sets.py` is the structural twin (`django_strawberry_framework/forms/sets.py`):
  the EXACT override set (`_resolve_model`/`_validate_meta`/`build_input`/`input_type_name`/
  `input_module_path`/`resolve_sync`/`resolve_async`), the allowed-key frozenset KEEPING
  `permission_classes` (`_ALLOWED_MODELFORM_META_KEYS` `:83`), per-declaration
  guard-before-cache-lookup (`_cached_build_form_input` `:166`), the materialize-and-stash
  tail (`_build_and_stash_form_input` `:368`), and the waiver detection
  (`_form_kwargs_overridden` `:274`). The serializer mirrors this shape but rides the
  PROMOTED shared helpers, never a third byte-parallel copy.
- Slice-1 `rest_framework/inputs.py` is the input generator the serializer `build_input`
  CONSUMES: `build_serializer_inputs` (`:628`) / `build_serializer_input_class` (`:525`)
  return `(input_cls, SerializerInputShape)`; `guard_create_required_serializer_fields`
  (`:426`); `materialize_serializer_input_class` (`:88`); `serializer_input_type_name`
  (`:370`); `SERIALIZER_INPUTS_MODULE_PATH` (`:72`); `clear_serializer_input_namespace`
  (`:104`); and the ready-made `(_serializer_shape_build_cache, clear_serializer_shape_build_cache)`
  pair (`:680`, from `make_shape_build_cache()`). The serializer `build_input` cluster
  rides these — it does NOT re-roll a cache, a guard, or a name deriver.
- `mutations/inputs.py::{build_payload_type, payload_object_slot}` (`:555`/`:545`) — the
  payload builder is reused via the inherited `_bind_mutation` (`mutations/sets.py:1020`);
  the serializer ADDS NOTHING to the payload path (Decision 6: the `node`/`result` slot
  comes free from riding the base bind).
- `registry.py::_clear_if_importable` (`django_strawberry_framework/registry.py:34`) — the
  cycle-safe lazy-import-and-run helper the canonical clear list iterates. Already present.

**New helpers justified (single responsibility each — all promotions per the DRY mandate).**

- **P1.2 `NON_DELETE_WRITE_OPERATIONS: frozenset[str] = frozenset({"create", "update"})`**
  in `mutations/sets.py`. SR: the one create/update-only ops set both the form AND
  serializer `_validate_meta` import. Today `forms/sets.py::_VALID_FORM_OPERATIONS`
  (`:104`) is a byte-identical local copy and `mutations/sets.py::_VALID_OPERATIONS`
  (`:95`) is the `{create,update,delete}` superset. Slice 2 promotes the create/update
  set, re-points `forms/sets.py` to import it (deleting `_VALID_FORM_OPERATIONS` + its
  anchor at `forms/sets.py:106`), and the serializer imports it — NO
  `_VALID_SERIALIZER_OPERATIONS`. The "no serializer/form delete" reject message
  single-sites (a shared message builder taking the base label, OR each flavor builds the
  message naming its own base from the shared set — see D3).
- **P2.7 `reject_unknown_meta_keys(name, meta, allowed) -> None`** in `mutations/sets.py`.
  SR: the `unknown = sorted(declared - allowed)` typo-guard every `_validate_meta`
  computes inline today (model `:516`, modelform `:478`, plain-form `:749`). Promote it;
  every `_validate_meta` calls it with its own frozenset. The serializer's
  `_ALLOWED_SERIALIZER_META_KEYS` ADDS `serializer_class`/`optional_fields`, KEEPS
  `operation`/`fields`/`exclude`/`permission_classes`, DROPS `model`/`input_class`/
  `partial_input_class`. Re-point the model + both form `_validate_meta` to call it.
- **P2.6 `_hook_overridden(cls, base, name) -> bool`** in `mutations/sets.py`. SR: the
  `cls.<name> is not base.<name>` identity check generalizing `forms/sets.py::_form_kwargs_overridden`
  (`:274`). Slice 2 moves the identity comparison behind it; the form waiver re-points to
  `_hook_overridden(cls, base, "get_form_kwargs") or _hook_overridden(cls, base, "get_form")`
  (deleting `_form_kwargs_overridden` + its anchor `forms/sets.py:348`), and the serializer
  `build_input` waiver calls `_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")`.
- **P1.7 `cached_build_input(shape_key, *, guard, build_fn) -> (input_cls, field_specs)`**
  + **`build_and_stash_input(cls, *, build, materialize)`** in `mutations/sets.py` (or a
  new `mutations/bind_helpers.py` — D4). SR: the per-pass dedupe with the load-bearing
  **guard-before-cache-lookup** ordering (`cached_build_input`) + the materialize-then-stash-
  `_input_field_specs` tail (`build_and_stash_input`). Re-point `forms/sets.py::_cached_build_form_input`
  (`:166`) + `_build_and_stash_form_input` (`:368`) to ride these (deleting the form-local
  versions + the shape-cache anchor `forms/sets.py:147`); the serializer supplies only its
  generator (`build_serializer_inputs`), materialize fn (`materialize_serializer_input_class`),
  and shape descriptor (`SerializerInputShape`). NO `_cached_build_serializer_input` /
  `_build_and_stash_serializer_input` byte-parallel trio.
- **P1.6 `register_subsystem_clear(module_path, attr) -> None` + `iter_subsystem_clears() ->
  tuple[tuple[str,str], ...]`** in `registry.py` (the seam centerpiece — see below).

**The `register_subsystem_clear` seam (P1.6 / M4 — the centerpiece, MANDATORY).**

Today there are TWO hand-maintained ledger-clear sites:
1. The `finalize_django_types` pre-bind reset block (`types/finalizer.py:781-787`):
   direct `from ..forms.inputs import clear_form_input_namespace` +
   `from ..mutations.inputs import clear_mutation_input_namespace`, called
   unconditionally before `bind_mutations()`.
2. `registry.py::TypeRegistry.clear()` (`:531-570`): a run of `_clear_if_importable(...)`
   co-clear rows (mutation input + registry, form input + registry + shape cache, plus
   connection/relay/filter/order rows).

The serializer's `clear_serializer_input_namespace` (in `rest_framework/inputs.py`, behind
the DRF soft-import guard) needs to run from BOTH. Hand-adding it to both is a permanent
two-list sync hazard AND a soft-dep problem: site (1) runs on EVERY build (DRF-absent
included), where a direct `from ..rest_framework.inputs import …` would raise `ImportError`
and break schema construction for every DRF-absent consumer.

The seam removes both hazards. The design:

- `register_subsystem_clear(module_path, attr)` appends a STATIC `(module_path, attr)`
  STRING row to ONE module-level ordered list in `registry.py`. It imports NOTHING (so a
  DRF row is recorded without importing DRF — F10). `iter_subsystem_clears()` returns an
  immutable snapshot.
- BOTH sites iterate the canonical list via `_clear_if_importable(module_path, attr,
  lambda clear: clear())`. `_clear_if_importable` already tolerates an absent module
  (`ImportError → return`), so a DRF-absent build silently no-ops the serializer row — a
  CORRECT no-op (DRF absent ⇒ no `SerializerMutation` declared ⇒ the serializer ledger is
  empty). The import-guarded asymmetry the Decision-6/Slice-2 checklist would otherwise
  spell by hand collapses to a one-line registration.
- The EXISTING mutation + form INPUT-namespace clears move INTO the canonical list as
  static rows, so the finalizer pre-bind reset re-points to iterate it too. **Behavior
  must stay equivalent for the model/form paths**: the same two input ledgers clear, in a
  retry-idempotent way, immediately before the bind sequence. (The two `clear_*_registry`
  + `clear_form_shape_build_cache` rows in `registry.clear()` are DECLARATION-registry /
  shape-cache resets, NOT pre-bind input-ledger resets — they stay `registry.clear()`-only
  and are NOT part of the finalizer pre-bind set; see D5 for the precise membership.)
- Registration happens at import time of each `inputs` module (the module that owns the
  clear registers its own row when imported), so a subsystem with clearable state has by
  definition been imported and registered (the F10 invariant). The serializer row is the
  literal `("django_strawberry_framework.rest_framework.inputs",
  "clear_serializer_input_namespace")`.

**Decision 12 — the root `__getattr__` + `require_drf()` export (net-new public surface).**

- `rest_framework/__init__.py` gains `require_drf()`: imports `rest_framework` (the DRF
  package), returns it when present, wraps an absent import in an `ImportError` carrying
  the single install-hint string. The hint MUST name `djangorestframework>=3.17.0`
  (CARRY-FORWARD from Slice 0: place 2 of the three-places-that-must-agree; places 1
  (`pyproject.toml:42`) + 3 (spec Risks line 3444) both already say `>=3.17.0`). One hint
  string lives in this module; every `rest_framework/` module + the root `__getattr__`
  route through it. Generalizes the `types/converters.py` soft-import precedent
  (return-None) to a RAISING guard.
- `__init__.py` (root) gains a `def __getattr__(name)` (PEP 562): for
  `"SerializerMutation"`, call `require_drf()` then import + return
  `rest_framework.sets.SerializerMutation`; for any other name raise the normal
  `AttributeError`. It does NOT memoize (no `globals()[...] = …`), so each access re-fires
  the guard (test-isolation requirement, Decision 12). `SerializerMutation` is NOT added
  to `__all__` (F1 — star import stays DRF-free). The eager-import + explicit-`__all__`
  root style is otherwise untouched.

**Duplication risk avoided.** The naive implementation would copy `forms/sets.py`
line-for-line (a third `_VALID_*`, a third `_cached_build_*`, a third `_build_and_stash_*`,
a third `_*_overridden`, a hand-added clear in both finalizer + registry). The plan forbids
each: every shared mechanic is promoted to `mutations/sets.py` / `registry.py` and IMPORTED.
The serializer's only genuinely-new logic is (a) the `serializer_class`
is-a-`ModelSerializer`-with-resolvable-`Meta.model` check, (b) `optional_fields`
normalization (already done by Slice-1 `resolve_optional_fields`, consumed at build), and
(c) the soft-dep export plumbing. The `SerializerInputShape` descriptor identity stays
legitimately new (Slice 1 authored it). Import manifest for `rest_framework/sets.py` is the
DoD-checkable contract: imports `mutations/sets.py::{DjangoMutation,
_validate_permission_classes, _normalize_field_sequence, _ValidatedMutationMeta,
register_mutation}`, the shared non-delete ops constant (P1.2), `reject_unknown_meta_keys`
(P2.7), `mutations/inputs.py::{CREATE, PARTIAL}`, `_hook_overridden` (P2.6) — anything
outside that re-implementing a listed symbol is a finding.

### Implementation steps

Line numbers are pin-at-write-time hints; verify against current source.

1. **`mutations/sets.py` — promote the five shared helpers** (consumed by re-pointed
   `forms/sets.py` + new `rest_framework/sets.py`).
   - Add `NON_DELETE_WRITE_OPERATIONS = frozenset({"create", "update"})` (P1.2). Keep
     `_VALID_OPERATIONS` (the model `{create,update,delete}` superset) unchanged.
   - Add `reject_unknown_meta_keys(name, meta, allowed)` (P2.7): compute `declared = {k for
     k in vars(meta) if not k.startswith("_")}`, `unknown = sorted(declared - allowed)`,
     raise `ConfigurationError(f"{base_label?} {name}.Meta has unknown keys: {unknown}.")`.
     Resolve the base-label wording shape under D3. Re-point `DjangoMutation._validate_meta`
     (`:516`) to call it.
   - Add `_hook_overridden(cls, base, name)` (P2.6): `return getattr(cls, name) is not
     getattr(base, name)`.
   - Add `cached_build_input(shape_key, *, guard, build_fn) -> (input_cls, field_specs)`
     (P1.7): run `guard()` (the per-declaration create-required guard) FIRST, THEN the
     cache lookup keyed by `shape_key`; on miss call `build_fn()` and cache. Add
     `build_and_stash_input(cls, *, build, materialize) -> input_cls`: call `build()` →
     `(input_cls, field_specs)`, `materialize(input_cls.__name__, input_cls)`,
     `cls._input_field_specs = field_specs`, return `input_cls`. Home under D4.
   - Replace the `TODO(spec-039 Slice 2)` block at `mutations/sets.py:104-118` with the
     real helpers (discharge that anchor).
   - Grow `_ValidatedMutationMeta` (`:287`): add a `serializer_class` slot (mirroring the
     `038` `form_class` slot at `:332`) and an `optional_fields` slot if the serializer
     snapshot must carry it (see D2). The model/form paths leave the new slot(s) `None` →
     byte-unchanged.

2. **`registry.py` — add the `register_subsystem_clear` seam** (P1.6 centerpiece).
   - Add a module-level ordered list (e.g. `_subsystem_clears: list[tuple[str, str]] = []`)
     + `register_subsystem_clear(module_path, attr)` (append a static string row, import
     nothing) + `iter_subsystem_clears()` (immutable snapshot). Replace the
     `TODO(spec-039 Slice 2)` block at `registry.py:53-65` (discharge that anchor).
   - The mutation INPUT clear + form INPUT clear (the two PRE-BIND-reset members) register
     through this seam. The mutation/form modules register their own rows at import time.
     Membership: exactly the two input-namespace clears that the finalizer pre-bind block
     resets today, PLUS the serializer input clear. (D5 pins membership precisely.)
   - In `TypeRegistry.clear()` (`:481`): the input-namespace co-clear rows
     (`clear_mutation_input_namespace`, `clear_form_input_namespace`) now come from
     iterating `iter_subsystem_clears()` via `_clear_if_importable` — replacing those two
     hand-written `_clear_if_importable(...)` blocks (`:538-542`, `:556-560`). The
     declaration-registry resets (`clear_mutation_registry`, `clear_form_mutation_registry`),
     the form shape cache (`clear_form_shape_build_cache`), and the connection/relay/
     filter/order rows stay as-is in `clear()` (they are NOT pre-bind input clears). The
     serializer SHAPE-cache clear (`clear_serializer_shape_build_cache`) is added as a
     `registry.clear()`-only `_clear_if_importable` row (it parallels
     `clear_form_shape_build_cache:566-570`); it is NOT in the pre-bind set.

3. **`types/finalizer.py` — re-point the pre-bind reset block to the seam.**
   - Replace the hand-written `clear_mutation_input_namespace()` + `clear_form_input_namespace()`
     (`:785-786`) with a loop over `iter_subsystem_clears()` calling each via
     `_clear_if_importable`, BEFORE `bind_mutations()` (and `bind_form_mutations()`). The
     serializer row is iterated too — a DRF-absent build no-ops it. `bind_mutations()` /
     `bind_form_mutations()` remain unchanged (the serializer rides `bind_mutations()`).
   - Replace the `TODO(spec-039 Slice 2)` block at `types/finalizer.py:771-780` with the
     seam iteration (discharge that anchor).
   - Equivalence requirement: the model + form input ledgers must still clear once,
     immediately before the bind sequence, retry-idempotently.

4. **`rest_framework/inputs.py` — register the serializer clear row.** Add a module-level
   `register_subsystem_clear("django_strawberry_framework.rest_framework.inputs",
   "clear_serializer_input_namespace")` at import time (so importing this module — which
   only happens with DRF present — records the row). `clear_serializer_input_namespace`
   (`:104`) already exists; no body change. Also register the serializer SHAPE-cache clear
   row into `registry.clear()` (step 2). NOTE: this file is behind the DRF guard implicitly
   (it `import`s `rest_framework`), so registration is safe — the row is a static string
   either way, and the module only imports when DRF is present.

5. **`rest_framework/sets.py` — author `SerializerMutation`** (new module, the structural
   twin of `forms/sets.py::DjangoModelFormMutation`).
   - Module-level: `_ALLOWED_SERIALIZER_META_KEYS = frozenset({"serializer_class",
     "optional_fields", "operation", "fields", "exclude", "permission_classes"})`.
   - `class SerializerMutation(DjangoMutation)`:
     - `_resolve_model(cls, meta)` → `Meta.serializer_class.Meta.model` (tolerant getattr
       chain returning `None`, mirroring `DjangoModelFormMutation._resolve_model:436`).
     - `_validate_meta(cls, meta)`:
       1. `reject_unknown_meta_keys(name, meta, _ALLOWED_SERIALIZER_META_KEYS)` (P2.7).
       2. require `serializer_class` (a clean `ConfigurationError` naming the key if
          unset/None) — BEFORE `_resolve_model`.
       3. type-check: must be a DRF `serializers.Serializer` subclass; for the
          ModelSerializer-driven contract must be a `serializers.ModelSerializer` with a
          resolvable `Meta.model` (a non-`ModelSerializer`, or a `ModelSerializer` with no
          `Meta.model`, → targeted `ConfigurationError`). Runs BEFORE `_resolve_model` so a
          wrong-type serializer is a clean error not a raw `AttributeError`.
       4. `operation` in `NON_DELETE_WRITE_OPERATIONS` (P1.2) — `"delete"` rejected with the
          shared message; missing operation rejected.
       5. `fields`/`exclude` mutual exclusion + narrowing fail-loud via the Slice-1
          `resolve_effective_serializer_fields` (which also validates `optional_fields`
          bare-string `"__all__"` reject via `resolve_optional_fields`). D1.
       6. `_validate_permission_classes(name, getattr(meta,"permission_classes",None))`.
       7. return `_ValidatedMutationMeta(model=…, operation=…, input_class=None,
          partial_input_class=None, fields=…, exclude=…, permission_classes=…,
          serializer_class=…[, optional_fields=…])`.
     - `input_module_path: str = SERIALIZER_INPUTS_MODULE_PATH` (class attr override).
     - `_input_field_specs: list | None = None` (stash slot, mirroring forms `:539`).
     - `build_input(cls, meta, primary_type)`: ride `build_and_stash_input` + `cached_build_input`
       (P1.7) with `shape_key` = the `SerializerInputShape` (from
       `build_serializer_input_class`), `guard` = a closure over
       `guard_create_required_serializer_fields` waived when
       `_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")`, `build_fn` =
       `build_serializer_input_class(meta.serializer_class, operation_kind=…,
       fields=meta.fields, exclude=meta.exclude)` (mapping `create→CREATE`,
       `update→PARTIAL`), `materialize` = `materialize_serializer_input_class`. NOTE the
       serializer shape-build cache to key on is the Slice-1
       `_serializer_shape_build_cache`. Reconcile `cached_build_input`'s signature against
       the Slice-1 `build_serializer_input_class` return `(input_cls, shape)` — see D6.
     - `input_type_name(cls, meta)` → `serializer_input_type_name(...)` for the operation's
       shape (single-sourced with `build_input`'s name choice, mirroring forms `:580`).
     - `get_serializer_kwargs` / `get_serializer` default method bodies (the waiver-detection
       base targets — D7). The bodies' request-context/`partial` logic is CONSUMED by the
       Slice-3 resolver; Slice 2 ships the default methods so the waiver has a base to
       compare against (the `forms/sets.py` `get_form_kwargs`/`get_form` precedent
       `:576-577`).
     - `resolve_sync` / `resolve_async` seam overrides: function-local import +
       delegate to `rest_framework/resolvers.py::resolve_serializer_{sync,async}`
       (Slice 3). In Slice 2 these are present-but-inert (mirroring `DjangoMutation`'s
       Slice-2 inert resolvers); the resolver module is Slice 3 — D8 on whether to land a
       NotImplementedError stub or the function-local-import-of-a-Slice-3-module shape.
   - The whole module imports `rest_framework.serializers` at top (behind the DRF dev-dep,
     present in tests — same as Slice-1 `rest_framework/inputs.py:54`).

6. **`rest_framework/__init__.py` — author `require_drf()`** (replace the `TODO(spec-039
   Slice 2)` placeholder at `:3-20`, discharge that anchor). One install-hint string naming
   `djangorestframework>=3.17.0`; `require_drf()` raises `ImportError` with the hint when
   DRF absent, else returns the module. The package `__init__` runs `require_drf()` as its
   guard so `import django_strawberry_framework.rest_framework` raises when DRF absent.

7. **`__init__.py` (root) — author `__getattr__`** (replace the `TODO(spec-039 Slice 2)`
   placeholder at `:39-54`, discharge that anchor). `def __getattr__(name)`: for
   `"SerializerMutation"`, `require_drf()` then return `rest_framework.sets.SerializerMutation`;
   else `raise AttributeError(...)`. No memoization. `__all__` UNCHANGED (no
   `SerializerMutation`).

8. **`forms/sets.py` — re-point onto the promotions** (the equivalence-preserving DRY
   discharge; anchors `:106`, `:147`, `:348`):
   - import `NON_DELETE_WRITE_OPERATIONS`; delete `_VALID_FORM_OPERATIONS` (`:104`); update
     the form delete-reject to use the shared set + message (D3).
   - re-point `_cached_build_form_input` / `_build_and_stash_form_input` onto
     `cached_build_input` / `build_and_stash_input` (P1.7); delete the form shape cache +
     `clear_form_shape_build_cache` ONLY IF the promotion subsumes them — but
     `registry.clear()` co-clears `clear_form_shape_build_cache` (`:566`) and the form shape
     cache may go through `make_shape_build_cache()` (the TODO at `:147` says "create the
     form cache through `make_shape_build_cache()`"). Reconcile under D4/D5: the form shape
     cache becomes a `make_shape_build_cache()` pair (like the serializer's), registered the
     same way. Confirm `_cached_build_form_input`'s existing per-declaration test
     (`tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration`)
     still passes byte-equivalently.
   - re-point `_form_kwargs_overridden` (`:274`) onto `_hook_overridden` (P2.6); delete the
     local helper.
   - **Equivalence gate**: the form + model suites (`tests/forms/`, `tests/mutations/`) must
     stay green UNCHANGED. Token-diff the moved bodies vs HEAD at final verification (the
     relocated/promoted rule).

9. **Tests** — see Test additions / updates.

### Test additions / updates

`tests/rest_framework/test_sets.py` (today a Slice-1 TODO stub) — the `Meta` validation
matrix + registration + bind + retry-idempotence + no-primary + base-unregressed. Mirror
`tests/forms/test_sets.py` fixture posture (autouse `registry.clear()`; products `Item`/
`Category` fixtures via the `_declare_products_primaries` shape; a `ModelSerializer` over
`Item` fixture, a plain `Serializer`, a `ModelSerializer` with no `Meta.model`). Use a
per-test `serializers.ModelSerializer` subclass. Assertion shapes:

- **public surface**: `from django_strawberry_framework import SerializerMutation` resolves
  through `__getattr__` to `rest_framework.sets.SerializerMutation`; `"SerializerMutation"
  not in django_strawberry_framework.__all__` (F1).
- **Meta matrix** (`pytest.raises(ConfigurationError, match=…)`):
  - missing `serializer_class` → match a "declares no serializer_class" / "serializer_class"
    message.
  - a non-`Serializer` value (e.g. a plain class) → "must be a .*Serializer".
  - a plain `serializers.Serializer` (no model) rejected → the targeted not-a-ModelSerializer
    / no-model message.
  - a `serializers.ModelSerializer` with no `Meta.model` → "resolves no model" style message.
  - `operation = "delete"` rejected → the shared non-delete message (matches the form
    flavor's "operation must be one of" / "no delete pipeline" shape).
  - missing `operation` rejected.
  - valid declaration: `serializer_class` accepted, snapshot stamped
    (`Cls._mutation_meta.serializer_class is …`, `.model is Item`, `.operation == "create"`).
  - `permission_classes` accepted as a known key; unset → `[DjangoModelPermission]`.
  - `fields` + `exclude` both set → "both `fields` and `exclude`".
  - `optional_fields = "__all__"` (bare string) rejected.
  - unknown key (e.g. `widget = "nope"`) → "unknown keys".
- **registration**: a concrete `SerializerMutation` IS in `iter_mutations()` (rides the
  model registry, like `DjangoModelFormMutation`), NOT in `iter_form_mutations()`; the
  abstract `SerializerMutation` base registers nowhere; late declaration after
  `finalize_django_types()` raises naming the flavor.
- **phase-2.5 binding via `bind_mutations()`**: declare products primaries + a
  `SerializerMutation create` over `Item`; `finalize_django_types()`; assert the
  serializer-derived input (`ItemSerializerInput`) materialized into
  `rest_framework.inputs` (NOT `mutations.inputs`/`forms.inputs`), `Cls._input_class is`
  that class, `Cls._payload_type_name == "<Name>Payload"` in `mutations.inputs` with
  `errors` + `node` slots, `Cls._primary_type is not None`, and `Cls._input_field_specs`
  is the Slice-1 reverse map (non-None).
- **retry-idempotence (the seam lock)**: declare a `SerializerMutation` + a primary;
  monkeypatch a later finalize step to raise (e.g.
  `types.finalizer._bind_ordersets`, mirroring `tests/forms/test_sets.py:641`); first
  `finalize_django_types()` raises, the serializer input IS materialized + registry not
  finalized; `monkeypatch.undo()`; second `finalize_django_types()` succeeds with NO stale
  serializer-input collision (proving `clear_serializer_input_namespace()` runs in the
  pre-bind reset via the seam, not a per-pass clear). Assert `registry.is_finalized()` flips
  True and `Cls._input_class` resolves to the (re-materialized) ledger entry.
- **no-registered-primary-type error**: a `SerializerMutation` over `Item` with no `Item`
  `DjangoType` this build → `finalize_django_types()` raises the reused
  `_resolve_primary_type` "no registered DjangoType | no type to return" error.
- **base-unregressed**: a model-flavor `DjangoMutation` declaration still validates +
  binds; `_ALLOWED_MUTATION_META_KEYS` unchanged; `DEFERRED_META_KEYS`/`ALLOWED_META_KEYS`
  (in `types/base.py`) byte-unchanged (assert by a targeted import/equality or leave to the
  existing `tests/mutations`/`tests/types` suites staying green).

`tests/rest_framework/test_soft_dependency.py` (today a Slice-1 TODO stub) — the DRF-absent
import guard (Decision 12, Test plan 3276-3290). DRF is INSTALLED in the test env, so
simulate absence: monkeypatch `builtins.__import__` so a guarded `import rest_framework`
raises; evict `sys.modules` for BOTH `rest_framework*` AND
`django_strawberry_framework.rest_framework*`; delete the root
`django_strawberry_framework.SerializerMutation` attribute (if bound). Then assert:
- `import django_strawberry_framework` still succeeds.
- the root `__getattr__("SerializerMutation")`, an `import …rest_framework`, and an
  `import …rest_framework.sets` ALL raise `ImportError` with the install hint (match the
  `djangorestframework>=3.17.0` hint substring).
- `from django_strawberry_framework import *` under simulated absence succeeds and binds NO
  `SerializerMutation` (F1).
- non-memoization: a SUCCESSFUL `SerializerMutation` access (DRF present) does not bind the
  name into the root module globals (`"SerializerMutation" not in
  vars(django_strawberry_framework)` after access).
NOTE the strict eviction discipline — this test is `--no-cov`-runnable in isolation but
mutates `sys.modules`; use careful teardown so it does not poison sibling tests (the
spec-037 `pillow` absent-path precedent).

`tests/mutations/test_fields.py` (extend, NOT this slice's owner — verification only): the
`038`-generalized `DjangoMutationField` target-check + dispatch + `data:` ref accept a
`SerializerMutation` unchanged (Decision 5). PER THE SPEC this verification belongs with
the field-factory tests; flag to Worker 2 as an optional add if a `SerializerMutation` is
declarable inert at this slice (it is — Slice 2 ships the base + bind). If the
`data:`-ref/dispatch verification needs the resolver (Slice 3), defer the dispatch half to
Slice 3 and land only the target-check half here. See D8.

Temp/scratch tests: a scratch `tests/rest_framework/` run under `docs/builder/temp-tests/`
is appropriate for Worker 3 to exercise the retry-idempotence + soft-dep eviction without
polluting the committed suite during review.

Coverage rule reminder: NO `pytest --cov*`. `--no-cov` only. The `test_sets.py` matrix is
package-internal (build-time invalid configs never reach a resolver — Test plan 3116-3127),
correctly owned here, not live.

### Implementation discretion items

Genuinely-discretionary choices I have assessed and delegate to Worker 2:

- **D1 — `_validate_meta` narrowing reuse path.** The serializer `_validate_meta` validates
  `fields`/`exclude`/`optional_fields` by calling the Slice-1
  `rest_framework/inputs.py::resolve_effective_serializer_fields` (+ `resolve_optional_fields`),
  which already route through `normalize_serializer_field_sequence` →
  `normalize_field_name_sequence(flavor="SerializerMutation")`. This satisfies P2.7's "call
  `normalize_field_name_sequence(..., flavor="SerializerMutation")` directly — no third
  re-binding wrapper" because the Slice-1 wrapper is the serializer flavor's single entry,
  not a NEW wrapper Slice 2 adds. Worker 2 picks whether `_validate_meta` calls the
  effective-field resolver directly or just normalizes the raw sequences and lets
  `build_input` re-resolve (the form flavor stores RAW declarations and re-normalizes in
  `build_input`, `forms/sets.py:512-513` — mirror that: validate-then-store-raw).
- **D3 — the shared "no delete" reject message shape.** P1.2 says the message single-sites
  "too". Worker 2 picks: a shared message builder `non_delete_operation_error(base_label,
  name, got)` in `mutations/sets.py`, OR each flavor formats inline from
  `sorted(NON_DELETE_WRITE_OPERATIONS)` + its own base label. Either keeps the SET
  single-sited; the message-string single-siting is the softer half. Prefer the shared
  builder if the two messages would otherwise be byte-identical modulo the base label.
- **D4 — home of `cached_build_input`/`build_and_stash_input`.** Spec offers
  `mutations/sets.py` OR a new `mutations/bind_helpers.py`. Default to `mutations/sets.py`
  (no new module) unless the additions push it past readability; a new module is justified
  only if `mutations/sets.py` grows unwieldy. Worker 2 decides.
- **D6 — `cached_build_input` signature vs the Slice-1 generator's `(cls, shape)` return.**
  The Slice-1 `build_serializer_input_class` returns `(input_cls, SerializerInputShape)`
  (shape carries `field_specs` + `type_name` + the `cache_key`), whereas the form
  `_cached_build_form_input` returns `(input_cls, field_specs)`. Worker 2 reconciles the
  promoted `cached_build_input` signature so it serves BOTH: e.g. `build_fn` returns
  `(input_cls, payload)` where `payload` is the per-flavor "stash thing" (form: field_specs;
  serializer: the shape, from which `build_and_stash_input` extracts
  `shape.field_specs`). Keep the guard-before-cache-lookup ordering load-bearing and
  single-sited regardless. This is a shape choice within the promotion, not an architecture
  question.
- **D8 — `resolve_sync`/`resolve_async` in Slice 2 (resolver is Slice 3).** The model base
  ships present-but-inert resolvers in its Slice 2 (function-local import of the Slice-3
  resolver module). For the serializer, `rest_framework/resolvers.py` does not exist until
  Slice 3. Worker 2 picks: (a) land `resolve_sync`/`resolve_async` overrides with a
  function-local `from .resolvers import …` that will resolve once Slice 3 lands (a forward
  import that is never CALLED in Slice 2 — a declared `SerializerMutation` is inert at this
  slice, like `DjangoMutation` in spec-036 Slice 2), or (b) omit the resolver overrides
  this slice and add them in Slice 3. Prefer (a) IFF it does not import `resolvers` at
  module-load (function-local only) AND does not break collection; otherwise (b). The
  `DjangoMutationField` target-check (`_has_mutation_protocol`) wants callable
  `resolve_sync`/`resolve_async` — `SerializerMutation` inherits `DjangoMutation`'s, which
  delegate to `mutations/resolvers.py`; an override is only needed to route to the
  serializer pipeline (Slice 3). So (b) is acceptable and keeps Slice 2 from carrying a
  forward-ref to a non-existent module. Worker 2 decides; record the choice in build notes.

### Spec slice checklist (verbatim)

- [x] Slice 2: the `SerializerMutation` base + `Meta` validation + the phase-2.5 bind
  (per
  [Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused)
  /
  [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven))
  - [x] [`rest_framework/sets.py`][rf-sets]: `SerializerMutation` (subclasses
    [`DjangoMutation`][glossary-djangomutation], overriding [`_resolve_model`][spec-036]
    → `Meta.serializer_class.Meta.model`, plus the `_validate_meta` / `build_input` /
    `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async` seams —
    the **exact** override set [`DjangoModelFormMutation`][glossary-djangomodelformmutation]
    uses in [`forms/sets.py`][forms-sets]). The serializer-flavor `_validate_meta`
    override: `Meta.serializer_class` is required and must be a DRF
    `serializers.Serializer` subclass; for the `ModelSerializer`-driven contract it
    must be a `serializers.ModelSerializer` with a resolvable `Meta.model`
    (a non-`ModelSerializer` or a `ModelSerializer` with no `Meta.model` raises a
    targeted [`ConfigurationError`][glossary-configurationerror]). The check runs
    **before** `_resolve_model` (so a missing / wrong-type `serializer_class` is a
    clean `ConfigurationError`, never a raw `AttributeError`). **`operation` is
    `create` / `update` only** (a `"delete"` serializer mutation is **rejected** —
    DRF serializers do not delete, [Decision 10](#decision-10--operations-create--update-no-serializer-delete)),
    and its shape-identity operation component is that value. The serializer
    allowed-key set **adds** `serializer_class` / `optional_fields`, **keeps**
    `operation` / `fields` / `exclude` / `permission_classes` (the `036` write-auth seam
    is inherited unchanged, [Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer);
    matching the form flavor's [`forms/sets.py`][forms-sets] allowed-key set, which also
    keeps `permission_classes`), and **drops** `model` / `input_class` /
    `partial_input_class`; `Meta.fields` / `Meta.exclude` are mutually exclusive. The
    whole module is behind the DRF soft-import guard
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [x] No change to [`DEFERRED_META_KEYS`][types-base] / `ALLOWED_META_KEYS`: a
    serializer-mutation `Meta` is its own validation namespace
    ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
  - [x] [`types/finalizer.py`][types-finalizer] / [`registry.py`][registry]: because
    `SerializerMutation` subclasses [`DjangoMutation`][glossary-djangomutation] it
    **rides the existing `bind_mutations()`** (the same way
    [`DjangoModelFormMutation`][glossary-djangomodelformmutation] does — finalizer
    comment "the ModelForm flavor rides bind_mutations yet writes the FORM ledger");
    its `build_input` override materializes into a `rest_framework` input namespace, so
    it needs a `clear_serializer_input_namespace()` ledger-clear ([`rest_framework/inputs.py`][rf-inputs],
    the [`forms/inputs.py`][forms-inputs] `clear_form_input_namespace` precedent) run from
    **two clear sites** — the [`forms/inputs.py`][forms-inputs] / [`mutations/inputs.py`][mutations-inputs]
    co-clear precedent **in full**:
    1. **The `finalize_django_types` pre-bind reset block.**
       [`finalize_django_types`][glossary-finalize_django_types] clears the
       `mutations.inputs` **and** `forms.inputs` ledgers **once, immediately before**
       the bind sequence (`clear_mutation_input_namespace()` /
       `clear_form_input_namespace()` → `bind_mutations()`) so a finalize that **fails
       on a later type is retry-idempotent** — the ledgers persist across passes, so no
       single pass can soundly clear them itself. The serializer input ledger has the
       **identical** retry-idempotence problem (it materializes during `bind_mutations()`
       yet survives a later-type failure), so `clear_serializer_input_namespace()` joins
       that same pre-bind reset, not a per-pass clear.
    2. **`TypeRegistry.clear()`** — a full registry reset must wipe serializer inputs too,
       alongside the existing mutation / form co-clears.

    **The clear is wired through the mandatory `register_subsystem_clear` seam (P1.6, F10,
    M4 — NOT two hand-edits).** Rather than hand-add the serializer's clear to **both** sites
    above (a permanent two-list synchronization hazard — and adding the serializer would make
    it a *third* subsystem relying on manually-mirrored clears, exactly the debt this card
    removes), Slice 2 promotes a `register_subsystem_clear(module_path, attr)` seam feeding
    **one canonical list** that **both** the finalizer pre-bind reset and `TypeRegistry.clear()`
    iterate via `_clear_if_importable`. **This is a Slice 2 requirement, not a
    budget-dependent option.** The list holds **static `(module_path, attr)` STRING rows
    only** — it does **not** import the target module at registration time (the serializer row
    is the literal `("…rest_framework.inputs", "clear_serializer_input_namespace")`, resolved
    lazily by `_clear_if_importable`, which already tolerates an absent module). Two
    consequences follow, both load-bearing:
    - **The soft-dep asymmetry vanishes.** Because every entry routes through
      `_clear_if_importable` **by construction**, the special-case the direct mutation / form
      clears would otherwise need for the DRF-behind-soft-import serializer ledger
      (`finalize_django_types` runs on **every** build, including DRF-absent ones, where a
      direct `from ..rest_framework.inputs import …` would raise `ImportError` and break
      schema construction for everyone without DRF) collapses to a **one-line registration**.
      It is also semantically exact: DRF absent ⇒ no
      [`SerializerMutation`][glossary-serializermutation] declared ⇒ the serializer ledger is
      empty ⇒ a skipped clear is a correct no-op.
    - **The import-timing edge is a non-issue (F10).** Storing **strings**, not imported
      callables, means registration never forces a DRF import; the backstop invariant is **a
      subsystem that has created clearable state has, by definition, been imported and
      registered its clear** (stale serializer ledger state implies `rest_framework.inputs`
      was imported in a prior failed bind), so a registered-but-not-yet-imported gap cannot
      leave dirty state.

    A **retry-idempotence test** (materialize serializer input, fail a later type, rerun
    finalization, assert the serializer ledger was cleared) locks it.

    **No new bind entry point** (no `bind_serializer_mutations()`) — that is the dividend
    of the `ModelSerializer`-rides-`DjangoMutation` choice
    ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)).
  - [x] [`__init__.py`][init]: export `SerializerMutation` (one net-new public symbol)
    via a **root-level `__getattr__`** (PEP 562) — `SerializerMutation` is resolvable by
    **name** (`from django_strawberry_framework import SerializerMutation`) through the
    shared `require_drf()` guard (DRF absent → `ImportError` with the install hint), but is
    **NOT added to `__all__`** while DRF is soft, so `from django_strawberry_framework
    import *` stays DRF-free and never trips the guard (**F1** — a star import consults
    `__all__` and would otherwise break for DRF-absent consumers). `import
    django_strawberry_framework` succeeds without DRF (the root never eagerly imports
    `rest_framework/`). This is the one root edit; the eager-import + explicit-`__all__`
    style of the existing root is otherwise preserved
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [x] Package coverage: [`tests/rest_framework/test_sets.py`][test-rest-framework] —
    the `Meta` validation matrix (missing / wrong-type `serializer_class`, a plain
    `Serializer` with no model rejected, `ModelSerializer`-with-no-model,
    `operation = "delete"` rejected, `serializer_class` accepted as a known key,
    `fields` + `exclude` both set, unknown key), registration, finalizer binding (the
    `bind_mutations()` path), the no-registered-primary-type error, and — proving the
    base is unregressed — the model-flavor seam defaults unchanged.
  - [x] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    `_validate_meta` reuses `mutations/sets.py::_validate_permission_classes`, the shared
    non-delete ops set (a promoted `NON_DELETE_WRITE_OPERATIONS` both flavors import — NOT a
    new `_VALID_SERIALIZER_OPERATIONS`, **P1.2**), and the promoted
    `reject_unknown_meta_keys(name, meta, allowed)` typo-guard called with
    `_ALLOWED_SERIALIZER_META_KEYS`, then returns a `_ValidatedMutationMeta` (**P2.5** /
    **P2.7**); the field-sequence call is
    `utils/inputs.py::normalize_field_name_sequence(..., flavor="SerializerMutation")`
    **directly** — no third re-binding wrapper (**P2.7**); the `build_input` /
    `input_type_name` cluster rides the promoted `cached_build_input` +
    `build_and_stash_input` core (guard-before-cache-lookup ordering single-sited — NOT a
    byte-parallel `_cached_build_serializer_input` / `_build_and_stash_serializer_input`,
    **P1.7**); the `get_serializer_kwargs` waiver reuses the generalized
    `_hook_overridden(cls, base, name)` (**P2.6**); and the input-ledger clear registers
    through `register_subsystem_clear` (**P1.6**, the finalizer item above). The serializer's
    only genuinely-new `_validate_meta` logic is the `serializer_class`
    is-a-`ModelSerializer` (+ resolvable `Meta.model`) check and `optional_fields`
    normalization.

### Notes for Worker 1 (spec reconciliation)

No spec gaps requiring an edit were found at planning time. Items flagged for the
final-verification spawn:

- **Spec status header (line 55) is stale** ("IN PROGRESS … no slice built yet"): Slices 0
  + 1 are final-accepted. Per the Slice-1 carry-forward, the stale header is deliberately
  NOT churned per-slice mid-build; Slice 4 (doc-wrap) owns the implemented-on-main edit.
  Recording here so it is not re-flagged as a new finding; no edit this slice.
- **`get_serializer_kwargs`/`get_serializer` slice boundary (D7/D8).** The hook BODIES
  (request-context injection, `partial=True`, the H3 framework-merge) are CONSUMED by the
  Slice-3 resolver (spec lines 916-919, 2162-2184). Slice 2 must ship at minimum a default
  `get_serializer_kwargs` (and `get_serializer`) METHOD on `SerializerMutation` so the
  `build_input` waiver's `_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")`
  has a base to compare against — the `forms/sets.py` precedent ships `get_form_kwargs`/
  `get_form` defaults in its Slice 2 and the resolver consumes them in Slice 3. The bodies'
  resolver-side logic can be minimal/forward-looking this slice (or fully landed — Worker 2
  may land the default body since it has no resolver dependency at definition time). This is
  a slice-boundary clarification, not a spec conflict; if Worker 2 finds the spec text reads
  as "hook lands in Slice 3", flag it back and Worker 1 reconciles at final verification.
- **`_ValidatedMutationMeta.optional_fields` (D2).** The serializer needs its
  `Meta.optional_fields` available at `build_input` time. Slice-1 `build_serializer_input_class`
  re-reads `optional_fields` off the serializer's own `Meta` via `resolve_optional_fields`,
  so the snapshot may NOT need an `optional_fields` slot (the serializer carries it). Worker
  2 confirms whether the snapshot needs the slot or the generator's own re-read suffices;
  prefer NOT adding a snapshot slot if the generator already owns it (minimal blast radius,
  matching how the form `fields`/`exclude` are stored raw and re-normalized in `build_input`).
- **`register_subsystem_clear` pre-bind membership (D5) must preserve model/form behavior.**
  The seam re-points the finalizer pre-bind reset (`types/finalizer.py:785-786`) and the
  `registry.clear()` input-namespace rows. Final verification must confirm the model + form
  retry-idempotence tests (`tests/mutations`, `tests/forms/test_sets.py::test_form_bind_is_retry_idempotent…`)
  stay green UNCHANGED — the equivalence proof that the promotion did not alter the
  model/form pre-bind reset semantics. Token-diff the moved-into-the-canonical-list clears
  vs HEAD.

### Static inspection helper

Run (Slice 2 adds logic to `types/finalizer.py` + `registry.py` + `mutations/sets.py`, all
under the BUILD.md must-run rule for `types/` and ≥30-line package additions):
- `uv run python scripts/review_inspect.py django_strawberry_framework/types/finalizer.py --output-dir docs/shadow` — ran. Quick scan: 33 imports, 31 symbols, 10 hotspots, 1 TODO (the Slice-2 anchor at `:771`), 15 repeated literals. The pre-bind reset block (`:771-800`) is the edit site; no new hotspot risk (the seam loop is a 2-3-line iteration replacing two direct calls).
- `uv run python scripts/review_inspect.py django_strawberry_framework/registry.py --output-dir docs/shadow` — ran. `TypeRegistry.clear` is a 100-line / 0-branch hotspot (the co-clear block, `:481`); the seam re-points two of its `_clear_if_importable` rows to iterate the canonical list and adds the serializer shape-cache row. Medium-tier attention: keep the iteration deterministic + the declaration-registry/shape-cache rows distinct from the pre-bind input rows.
- `uv run python scripts/review_inspect.py django_strawberry_framework/mutations/sets.py --output-dir docs/shadow` — ran. `DjangoMutation._validate_meta` is a 106-line / 10-branch hotspot (`:482`); the P2.7 re-point (call `reject_unknown_meta_keys`) trims it slightly. The five promotions are net-new small helpers, not hotspot growth.

Shadow files under `docs/shadow/` (gitignored, line numbers non-canonical).

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/mutations/sets.py` — promoted the five shared helpers (discharging the `:104` TODO anchor): `NON_DELETE_WRITE_OPERATIONS` (P1.2), `non_delete_operation_error(base_label, name, got)` (the shared "no delete" message builder, D3), `reject_unknown_meta_keys(name, meta, allowed)` (P2.7), `_hook_overridden(cls, base, name)` (P2.6), `cached_build_input(cache, shape_key, *, guard, build_fn)` + `build_and_stash_input(cls, *, build, materialize, specs_of)` (P1.7). Re-pointed `DjangoMutation._validate_meta`'s typo guard onto `reject_unknown_meta_keys`. Grew `_ValidatedMutationMeta` with a `serializer_class` slot (D2; model/form leave it `None` → byte-unchanged). Added `from collections.abc import Callable`.
- `django_strawberry_framework/registry.py` — added the `register_subsystem_clear(module_path, attr)` + `iter_subsystem_clears()` seam over one module-level `_subsystem_clears` list of static `(module_path, attr)` STRING rows (P1.6, discharging the `:53` anchor). `TypeRegistry.clear()` now iterates `iter_subsystem_clears()` via `_clear_if_importable` for the input-namespace clears (replacing the two hand-written mutation/form input blocks), keeps the declaration-registry + form shape-cache resets `clear()`-only, and adds a `clear()`-only serializer shape-cache row (`clear_serializer_shape_build_cache`, DRF-guarded via `_clear_if_importable`).
- `django_strawberry_framework/mutations/inputs.py` — registered the mutation input clear via `register_subsystem_clear(INPUTS_MODULE_PATH, "clear_mutation_input_namespace")` at import time; imported `register_subsystem_clear`.
- `django_strawberry_framework/forms/inputs.py` — registered the form input clear the same way; imported `register_subsystem_clear`.
- `django_strawberry_framework/rest_framework/inputs.py` — registered the serializer input clear (the literal `("…rest_framework.inputs", "clear_serializer_input_namespace")` row) at import time (only runs with DRF present); imported `register_subsystem_clear`.
- `django_strawberry_framework/types/finalizer.py` — re-pointed the pre-bind reset block to iterate `iter_subsystem_clears()` via `_clear_if_importable` before `bind_mutations()` (discharging the `:771` anchor), replacing the two hand-written `clear_mutation_input_namespace()` / `clear_form_input_namespace()` calls.
- `django_strawberry_framework/rest_framework/sets.py` — authored `SerializerMutation(DjangoMutation)` (discharging the TODO stub): `_resolve_model` → `Meta.serializer_class.Meta.model`; `_validate_meta` (the serializer matrix: required `serializer_class`, `Serializer`-then-`ModelSerializer`-then-resolvable-`Meta.model` checks all BEFORE `_resolve_model`, `NON_DELETE_WRITE_OPERATIONS` operation gate via `non_delete_operation_error`, `fields`/`exclude` validation via the Slice-1 `resolve_effective_serializer_fields`, `_validate_permission_classes`); `build_input` (rides `cached_build_input` + `build_and_stash_input` + the `_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")` waiver, keyed on `_serializer_shape_build_cache`); `input_type_name` (re-builds the shape, reads `shape.type_name`); `input_module_path = SERIALIZER_INPUTS_MODULE_PATH`; `_input_field_specs` slot; default `get_serializer_kwargs` / `get_serializer` construction hooks (the waiver base; bodies forward-looking for Slice 3). Module behind the top-level `from rest_framework import serializers` DRF guard.
- `django_strawberry_framework/rest_framework/__init__.py` — authored `require_drf()` + the single `_DRF_INSTALL_HINT` naming `djangorestframework>=3.17.0` (discharging the TODO; place 2 of three-places-that-must-agree, confirmed against `pyproject.toml:42` + spec Risks ~3444); runs `require_drf()` as the package import guard.
- `django_strawberry_framework/__init__.py` — authored the non-memoizing root `__getattr__` routing `SerializerMutation` through `require_drf()` (discharging the TODO). `__all__` UNCHANGED (F1 — `SerializerMutation` not added). `import django_strawberry_framework` succeeds without DRF.
- `django_strawberry_framework/forms/sets.py` — re-pointed onto the promotions (equivalence-preserving): deleted `_VALID_FORM_OPERATIONS` + its anchor (now imports `NON_DELETE_WRITE_OPERATIONS`); the ModelForm operation reject uses `non_delete_operation_error`; both flavors' typo guards use `reject_unknown_meta_keys`; the form shape cache rides `make_shape_build_cache()` (anchor discharged); `_cached_build_form_input` + `_build_and_stash_form_input` ride `cached_build_input` + `build_and_stash_input`; `_form_kwargs_overridden` rides `_hook_overridden` for each hook (anchor discharged).
- `tests/rest_framework/test_sets.py` — the Meta validation matrix + public surface + registration + bind + retry-idempotence + no-primary + base-unregressed (discharged the test stub).
- `tests/rest_framework/test_soft_dependency.py` — the DRF-absent guard tests (discharged the test stub).

### Tests added or updated

- `tests/rest_framework/test_sets.py` — 24 tests: public surface (`__getattr__` resolve, not in `__all__`); Meta matrix (missing/non-Serializer/plain-Serializer-no-model/ModelSerializer-no-model `serializer_class`, `delete`/missing `operation` rejected, `serializer_class` accepted, unset/explicit `permission_classes`, `fields`+`exclude`, bare-string `optional_fields`, unknown key, `model` key unknown); registration (rides `iter_mutations()`, not `iter_form_mutations()`; abstract base nowhere; post-finalize reject); bind (`ItemSerializerInput` into `rest_framework.inputs`, `CreateItemPayload` into `mutations.inputs` with `errors`+`node`, `_primary_type`/`_input_field_specs` non-None; update → `ItemSerializerPartialInput`); retry-idempotence (`_bind_ordersets` monkeypatch-boom, ledger persists, rerun clean); no-primary finalize error; base-unregressed (`_ALLOWED_MUTATION_META_KEYS` byte-equal, model `delete` still accepted, `serializer_class` slot `None`, `ALLOWED_META_KEYS` untouched).
- `tests/rest_framework/test_soft_dependency.py` — 7 tests: root import succeeds without DRF; root lookup / `…rest_framework` / `…rest_framework.sets` all raise the hint; star import DRF-free + no `SerializerMutation`; non-`SerializerMutation` miss → `AttributeError`; non-memoization. DRF absence simulated by a `level==0`-only `__import__` block + strict `sys.modules` eviction/restore.

### Validation run

- `uv run ruff format .` — pass (reformatted my new files; whole tree formatted).
- `uv run ruff check --fix .` — pass (auto-fixed import sorting; one manual fix: `__getattr__` return annotation `-> type`). `uv run ruff check .` final: All checks passed.
- `uv run python scripts/check_trailing_commas.py --fix` — fixed layout in my files; my 12 touched files clean afterward. (Remaining non-ASCII `…` flags are in `rest_framework/serializer_converter.py`, a prior-accepted Slice-1 file I did NOT touch — out of scope.)
- `git status --short` — modified by me (slice-intended): `__init__.py`, `forms/inputs.py`, `forms/sets.py`, `mutations/inputs.py`, `mutations/sets.py`, `registry.py`, `rest_framework/__init__.py`, `rest_framework/inputs.py`, `rest_framework/sets.py`, `types/finalizer.py`, `tests/rest_framework/test_sets.py`, `tests/rest_framework/test_soft_dependency.py`. Out-of-scope / not my churn (prior accepted Slice-0/1 source + baseline-dirty, left untouched per the task contract): `forms/converter.py`, `rest_framework/serializer_converter.py`, `utils/converters.py`, `utils/inputs.py`, `tests/rest_framework/test_converter.py`, `tests/rest_framework/test_inputs.py`, `tests/utils/test_inputs.py` (Slice 1), `pyproject.toml` + `uv.lock` (Slice 0), `docs/spec-039-...md` (Worker 1), `docs/feedback.md` (baseline-dirty). No tool churn reverted (ruff/comma fixes landed only on slice-intended files).
- Focused tests (no `--cov*`): `uv run pytest tests/rest_framework tests/forms tests/mutations tests/base --no-cov` — **452 passed**. Also ran `tests/types tests/utils tests/test_registry.py --no-cov` — **557 passed, 2 skipped** (the registry-clear seam + `make_shape_build_cache` re-point touch shared infra, so I swept these too; no regressions).

### Implementation notes

- **D1 (narrowing reuse)** — `_validate_meta` calls the Slice-1 `resolve_effective_serializer_fields` for validation and stores RAW `fields`/`exclude` on the snapshot; `build_input` re-resolves. Matches the form flavor's validate-then-store-raw precedent.
- **D2 (`optional_fields` slot)** — NO snapshot slot added; the generator (`build_serializer_input_class` → `resolve_optional_fields`) re-reads `optional_fields` off the serializer's own `Meta`. Minimal blast radius (matches Worker 1's D2 preference). Consequence: the bare-string `optional_fields` reject surfaces at `finalize_django_types()` (bind time), not class creation — the test asserts at finalize accordingly.
- **D3 (shared message)** — chose the shared message builder `non_delete_operation_error(base_label, name, got)` in `mutations/sets.py` (the two flavors' messages were byte-identical modulo base label). Both form + serializer raise it; preserves the `"operation must be one of"` substring the existing form test matches.
- **D4 (home)** — `cached_build_input`/`build_and_stash_input` live in `mutations/sets.py` (no new module).
- **D6 (signature)** — `cached_build_input(cache, shape_key, *, guard, build_fn)` takes the flavor's own per-pass cache dict as a parameter (NOT a module-level dispatch dict) so the mutation/form/serializer caches stay disjoint. `build_fn` returns `(input_cls, payload)`; `build_and_stash_input` takes a `specs_of(payload)` callable to extract the reverse map (form: identity on the `field_specs` list; serializer: `list(shape.field_specs)`). The serializer `shape_key` is a cheap pre-build identity tuple `(serializer_class, operation_kind, frozenset(effective))` (the `SerializerInputShape` descriptor is only known post-build); deterministic for a declaration, so same-shape declarations dedupe.
- **D8 (resolvers)** — chose option (b): did NOT override `resolve_sync`/`resolve_async` this slice (the Slice-3 `rest_framework/resolvers.py` does not exist; a forward function-local import would be a never-called ref to a non-existent module). A declared `SerializerMutation` is inert at this slice (registered + bound, never resolved), inheriting `DjangoMutation`'s resolver seams. **The first spec-checklist box names `resolve_sync`/`resolve_async` in the "exact override set"; those two overrides are the only sub-part deferred to Slice 3** — see Notes for Worker 1.
- **`_form_kwargs_overridden` kept as a thin two-hook adapter** (not fully inlined): the form waiver needs the `get_form_kwargs` OR `get_form` composition; the identity comparison is single-sited in the promoted `_hook_overridden`, and `_form_kwargs_overridden` composes two calls of it. The serializer waiver calls `_hook_overridden` directly (it waives on `get_serializer_kwargs` only). No duplicated identity check remains.
- **`get_serializer_kwargs`/`get_serializer` default bodies** — shipped per Worker 1's D7 note (the waiver needs a base). `get_serializer_kwargs` returns `{"data": data}` (+ `instance` on update); `get_serializer` constructs `serializer_class(**kwargs)` with a framework `context["request"]` via `request_from_info`. The full framework-merge + `partial` injection (spec H3) is Slice 3's resolver; these are the forward-looking defaults.
- **Pre-bind reset equivalence** — verified the model + form retry-idempotence tests (`tests/mutations`, `tests/forms/test_sets.py::test_form_bind_is_retry_idempotent…`) pass unchanged. The seam iteration produces the same three (mutation, form, serializer) input-ledger clears in registration order; a DRF-absent build never imports `rest_framework.inputs`, never registers its row, so the serializer clear is correctly absent (and `_clear_if_importable` would no-op it anyway). Confirmed registration order via a live import probe: `(mutations.inputs, clear_mutation_input_namespace), (forms.inputs, clear_form_input_namespace), (rest_framework.inputs, clear_serializer_input_namespace)`.

### Notes for Worker 3

- The soft-dependency test's `_block_drf_import` shim blocks ONLY `level == 0` (absolute) `rest_framework` imports — a relative `from .rest_framework import require_drf` (`level == 1`, the framework's own subpackage) must pass through so the guard is reachable. Initial pass blocked all → raw ImportError before the hint; fixed by gating on `level`.
- `tests/rest_framework/test_soft_dependency.py` mutates `sys.modules`; the fixture evicts AND restores both `rest_framework*` and `django_strawberry_framework.rest_framework*` (strict teardown) so it does not poison sibling DRF tests. `test_successful_lookup_does_not_memoize` runs WITHOUT the absence fixture (DRF present).
- No shadow files were used during this build pass (the plan's `review_inspect` runs were Worker 1's planning runs).
- `_serializer_shape_build_cache` is NOT cleared per-pass at the start of `bind_mutations()` (the serializer rides it; coupling `mutations/sets.py` to the DRF cache would break the soft-dep). This is equivalence-correct: the ModelForm flavor's `_form_shape_build_cache` is likewise not cleared before `bind_mutations()` (only at the start of `bind_form_mutations()` and in `registry.clear()`), and retry-idempotence is provided by the pre-bind NAMESPACE-ledger clear, not the per-pass build cache (a leaked-but-identical cached class re-materializes idempotently). `clear_serializer_shape_build_cache` is co-cleared from `registry.clear()`.

### Notes for Worker 1 (spec reconciliation)

- **`resolve_sync`/`resolve_async` deferred to Slice 3 (D8 option b).** The first spec-checklist sub-check bundles `resolve_sync` / `resolve_async` into the "exact override set". I ticked that box because the substantive Slice-2 contract (the `_resolve_model` / `_validate_meta` / `build_input` / `input_type_name` / `input_module_path` seam set + the full validation/operation/allowed-key matrix + the DRF guard) landed, and D8 explicitly authorizes omitting the resolver overrides this slice (the Slice-3 `rest_framework/resolvers.py` does not yet exist; a forward-ref would be a never-called import of a missing module). If you read the box as requiring `resolve_sync`/`resolve_async` overrides to land THIS slice, un-tick it and record the Slice-3 deferral — flagging per the ticking discipline.
- **Stale spec status header** (Worker 1's planning note): unchanged this slice (Slice 4 owns the implemented-on-main edit), not re-flagged as new.
- **`optional_fields` bare-string reject is bind-time, not class-creation** (D2 consequence): because the snapshot carries no `optional_fields` slot and the generator re-reads it, an invalid `Meta.optional_fields` raises at `finalize_django_types()` rather than at class creation. This is consistent with the spec's "generator owns the re-read" but differs from the `fields`/`exclude` reject (which IS class-creation, via `resolve_effective_serializer_fields`). If the spec intends `optional_fields` to fail at class creation too, that would need a snapshot slot + a class-creation `resolve_optional_fields` call (larger blast radius). Flagging for your judgment; no spec conflict found.

---

## Review (Worker 3)

Reviewed Worker 2's working-tree diff against the slice artifact (Plan + Build report),
spec-039 Decisions 5/6/10/11/12, the cross-flavor DRY obligations (P1.2/P1.6/P1.7/P2.6/P2.7),
and DoD item 3. Used the artifact's `### Files touched` as the cumulative-diff filter; the
Slice-0 (`pyproject.toml`/`uv.lock`/spec) and Slice-1 (`utils/`, `forms/converter.py`,
`rest_framework/serializer_converter.py`, Slice-1 test files) churn and `docs/feedback.md`
were excluded from review per the task contract. The large `rest_framework/inputs.py` diff is
Slice-1's accepted body; the Slice-2 contribution there is only the import +
`register_subsystem_clear(SERIALIZER_INPUTS_MODULE_PATH, "clear_serializer_input_namespace")`
row, which was reviewed.

### High

None.

### Medium

- **Serializer `build_input` create-required guard + `get_serializer_kwargs` waiver are
  untested at the `sets.py` integration level** (`rest_framework/sets.py::SerializerMutation.build_input`,
  src lines 294-302; the `_hook_overridden` waiver + `_guard` closure). The Slice-1
  `tests/rest_framework/test_inputs.py` pins `guard_create_required_serializer_fields` and its
  waiver at the GENERATOR level (its lines 19, 381-387), but the genuinely-new Slice-2 wiring —
  the per-declaration `_guard` running through `cached_build_input` and the
  `_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")` waiver that suppresses it
  — has no exercising assertion in the permanent suite. The form flavor HAS the twin integration
  test (`tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration`,
  its line 421); the serializer flavor does not. This is a net-new branch without an exercising
  assertion (the reading-discipline Medium), not a behavior bug — I verified the behavior is
  CORRECT with a temp test (see Temp test verification): the guard fires at `finalize_django_types()`
  when a required writable field is narrowed away on create, and a `get_serializer_kwargs`
  override correctly waives it. Why it matters: the waiver is the load-bearing
  guard-before-cache-lookup contract (spec-039 Decision 7 / the Finding-5 per-declaration
  discipline the form test locks); a future refactor of `build_input` could silently break the
  waiver or the per-declaration guard and the Slice-2 suite would stay green.
  - Recommended change: promote `docs/builder/temp-tests/slice-2/test_waiver_and_guard.py`
    (two tests) into `tests/rest_framework/test_sets.py` — the serializer twin of the form
    `test_cached_build_form_input_runs_required_guard_per_declaration`. Test expectation: a create
    `SerializerMutation` over a serializer with a required column-less writable field, narrowed
    away via `Meta.fields`, raises `ConfigurationError` at `finalize_django_types()`; the same
    declaration with a `get_serializer_kwargs` override binds without raising.

### Low

None.

### DRY findings

All five DRY promotions land as planned and the form/model re-points are equivalence-preserving:

- **P1.2 `NON_DELETE_WRITE_OPERATIONS`** (`mutations/sets.py`) — one promoted frozenset
  `{create, update}`; `forms/sets.py` deletes `_VALID_FORM_OPERATIONS` and imports it; the
  serializer imports it. NO `_VALID_SERIALIZER_OPERATIONS`. The shared message single-sites
  through `non_delete_operation_error(base_label, name, got)` (D3 — shared builder chosen).
  Verified the reject preserves the `"operation must be one of"` substring the existing form
  tests (`tests/forms/test_sets.py:239,250`) and the new serializer tests
  (`tests/rest_framework/test_sets.py:189,200`) match — the only wording change is "A form
  mutation has no delete pipeline" → "This flavor has no delete pipeline", which no test asserts.
- **P2.7 `reject_unknown_meta_keys(name, meta, allowed)`** (`mutations/sets.py`) — the inline
  `unknown = sorted(declared - allowed)` typo guard promoted; model, ModelForm, plain-form, AND
  serializer `_validate_meta` all call it with their own frozenset. Relocation verified
  byte-identical: `git show HEAD:.../mutations/sets.py` rendered
  `f"DjangoMutation {name}.Meta has unknown keys: {unknown}."`; the new path passes
  `name="DjangoMutation {clsname}"` into `f"{name}.Meta has unknown keys: {unknown}."` — same
  rendered string. The plain-form `DjangoFormMutation` correctly passes
  `_ALLOWED_PLAIN_FORM_META_KEYS | {"operation"}` (matching the old `declared - allowed -
  {"operation"}`) and keeps the FIRST key-presence `"operation"` reject.
- **P2.6 `_hook_overridden(cls, base, name)`** (`mutations/sets.py`) — the identity check promoted;
  `forms/sets.py::_form_kwargs_overridden` kept as a thin two-hook adapter
  (`_hook_overridden(...,"get_form_kwargs") or _hook_overridden(...,"get_form")`) with the
  identity comparison single-sited in `_hook_overridden`; the serializer waiver calls it directly
  for `get_serializer_kwargs`. No duplicated identity check remains. Verified the classmethod/
  instance-method semantics live: a plain `SerializerMutation` subclass is NOT flagged
  (`_hook_overridden(SM, SM, "get_serializer_kwargs") is False`).
- **P1.7 `cached_build_input(cache, shape_key, *, guard, build_fn)` + `build_and_stash_input(cls,
  *, build, materialize, specs_of)`** (`mutations/sets.py`) — the guard-before-cache-lookup core
  and materialize-then-stash tail promoted; `forms/sets.py` re-points
  `_cached_build_form_input`/`_build_and_stash_form_input` onto them (`specs_of` = identity for the
  form). NO byte-parallel `_cached_build_serializer_input`. The D6 signature reconciliation is
  clean: each flavor passes its own disjoint cache dict; `build_fn` returns `(input_cls, payload)`
  and `specs_of` extracts the reverse map (form: the `field_specs` list; serializer:
  `list(shape.field_specs)`). The guard-before-cache-lookup ordering is single-sited in
  `cached_build_input` (`guard()` then `cache.get`).
- **P1.6 `register_subsystem_clear` / `iter_subsystem_clears`** (`registry.py`) — see Seam verdict.
- **`make_shape_build_cache()` (P1.3, Slice-1)** — `forms/sets.py` re-points its hand-rolled
  `_form_shape_build_cache = {}` + `clear_form_shape_build_cache` onto the
  `(cache, clear) = make_shape_build_cache()` pair. Verified behavior-equivalent: the factory
  returns `({}, clear_fn)` where `clear_fn` empties the dict — identical to the deleted hand-rolled
  pair.
- **`normalize_field_name_sequence(..., flavor="SerializerMutation")` (P2.7)** — `_validate_meta`
  routes field validation through the Slice-1 `resolve_effective_serializer_fields`, which already
  routes through `normalize_serializer_field_sequence` → `normalize_field_name_sequence(flavor=
  "SerializerMutation")`. No third wrapper added (D1 — the Slice-1 wrapper is the serializer
  flavor's single entry). Stores RAW `fields`/`exclude`; `build_input` re-resolves (form precedent).

`DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` (`types/base.py`) unchanged (asserted by
`test_deferred_and_allowed_meta_keys_unchanged`); no version bump.

### Seam verdict (`register_subsystem_clear` — CENTRAL, F10/P1.6/M4)

Correct and complete. ONE canonical `_subsystem_clears` list of static `(module_path, attr)` STRING
rows; `register_subsystem_clear` appends (idempotent by value, imports nothing); `iter_subsystem_clears`
returns a tuple snapshot. BOTH the finalizer pre-bind reset (`types/finalizer.py`, replacing the two
direct `clear_*_input_namespace()` calls) and `TypeRegistry.clear()` (replacing the two hand-written
input-namespace `_clear_if_importable` blocks) iterate it via `_clear_if_importable`. The two existing
mutation/form input clears were MOVED into the list (registered at import time by `mutations/inputs.py`
and `forms/inputs.py`), not left as a parallel hand-edit. The declaration-registry resets
(`clear_mutation_registry`, `clear_form_mutation_registry`) and shape-cache resets
(`clear_form_shape_build_cache`, the net-new `clear_serializer_shape_build_cache`) correctly stay
`registry.clear()`-only and are NOT in the pre-bind set (D5 membership exactly: mutation/form/serializer
INPUT namespaces). Registration never imports DRF (string row); a DRF-absent build never imports
`rest_framework.inputs`, never registers the serializer row, so the pre-bind loop has only the two
model/form rows — verified live: bare package import registers exactly
`(mutations.inputs,...), (forms.inputs,...)`; after a `SerializerMutation` access the third
`(rest_framework.inputs, clear_serializer_input_namespace)` row appears. Model/form equivalence holds:
the root package eagerly imports `.mutations`+`.forms` (so both rows are always registered whenever the
package loads), so `finalize_django_types()` always clears both — same as the old unconditional direct
calls. The retry-idempotence test (`test_bind_is_retry_idempotent_after_fixable_later_phase_failure`)
genuinely exercises the lock: materialize `ItemSerializerInput` → `_bind_ordersets` monkeypatch-boom
→ assert ledger persists + registry not finalized → `monkeypatch.undo()` → rerun finalize → assert
clean (no stale-input collision) + `is_finalized()` True.

### Export verdict (Decision 12 / F1 / DoD 8)

Correct. PEP-562 `__getattr__` on the root resolves `SerializerMutation` BY NAME through
`require_drf()`; every other miss raises the normal `AttributeError`. Non-memoizing — verified live
that a successful access leaves `"SerializerMutation" not in vars(django_strawberry_framework)`
(`test_successful_lookup_does_not_memoize` pins it). NOT in `__all__` — verified live (`False`); the
star-import test confirms `from … import *` stays DRF-free and binds no `SerializerMutation`.
`import django_strawberry_framework` succeeds without DRF (the root never eagerly imports
`rest_framework/`). The install hint names `djangorestframework>=3.17.0` — matches the `pyproject.toml`
dev pin (place 1) and spec Risks note (place 3), the three-places-that-must-agree; the
`test_soft_dependency.py` `_HINT_SUBSTRING` asserts it. The `_block_drf_import` `level`-gating
(block absolute `import rest_framework` only, pass relative `from .rest_framework import …`) is the
correct shim for reaching the guard; all three raise sites (root lookup, `…rest_framework`,
`…rest_framework.sets`) assert the hint.

### D8 box-ticking verdict

Accept the partial-tick with the deferral recorded. Worker 2 ticked the first `### Spec slice
checklist (verbatim)` box (which names `resolve_sync`/`resolve_async` in the "exact override set")
but deferred those two overrides to Slice 3, transparently recorded in Build-report D8 + Notes for
Worker 1. This is the correct build order, not an over-tick: the resolver bodies those overrides
delegate to live in `rest_framework/resolvers.py`, which is verified to exist at HEAD only as a
`TODO(spec-039 Slice 3)` stub (no `resolve_serializer_sync`/`resolve_serializer_async` defined). The
`forms/sets.py` precedent confirms the build-ordering split: `DjangoModelFormMutation.resolve_sync`/
`resolve_async` (its src 577-608) do `from .resolvers import resolve_form_sync` and `forms/resolvers.py`
EXISTS with the real bodies — i.e., the form flavor landed its resolver overrides in the same slice
the resolver existed. Landing serializer overrides now would be a never-called function-local import of
a not-yet-defined name. A declared `SerializerMutation` is inert this slice (registered + bound, never
resolved) and inherits `DjangoMutation`'s `resolve_sync`/`resolve_async` classmethods — verified live:
`SerializerMutation` has no `resolve_sync` in its own `__dict__`, inherits the same `__func__` as
`DjangoMutation`, and both are callable, so the Decision-5 `DjangoMutationField` target-check
(`_has_mutation_protocol`) still sees a callable resolver pair. Recommendation to Worker 1: keep the
box ticked but confirm at final verification that the serializer `resolve_sync`/`resolve_async`
overrides land in Slice 3 (they are the only sub-part of the named override set deferred).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py`: the `__all__` tuple and the eager re-export
list are UNCHANGED. The only edits are (1) removing the Slice-2 TODO comment block and (2) adding the
PEP-562 `__getattr__`. `SerializerMutation` appears only inside `__getattr__` and its docstring, never
in `__all__` — verified live (`"SerializerMutation" in __all__` → False). The `__getattr__` addition
(a named lazy export NOT in `__all__`) is authorized by the active spec: Decision 12 + F1 + DoD 8 (the
spec-checklist `__init__.py` box, src 565-575, names this exact root-`__getattr__` contract). The DoD
"no new public exports while DRF is soft" contract holds (the name is reachable but not exported via
`__all__`).

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- The `_validate_meta` ordering: `reject_unknown_meta_keys` → require `serializer_class` →
  `isinstance(type) and issubclass(Serializer)` → `issubclass(ModelSerializer)` → `_resolve_model`
  non-None — all the serializer-type checks run BEFORE `_resolve_model`, so a missing / wrong-type /
  model-less `serializer_class` is a clean `ConfigurationError` naming the offending key, never a raw
  `AttributeError`. Pinned by the four matrix tests (missing / non-Serializer / plain-Serializer /
  ModelSerializer-no-model). Verified `_resolve_model` is a tolerant getattr chain returning `None`.
- The bind path: `build_input` rides the promoted `cached_build_input` + `build_and_stash_input`,
  materializes into `rest_framework.inputs` (NOT `mutations.inputs`), stashes `_input_field_specs`,
  and the model-backed `<Name>Payload` rides the inherited `_bind_mutation` into `mutations.inputs`
  with `errors`+`node` slots. Pinned by `test_bind_materializes_…` + `test_update_binds_partial_input`.
- The forward-looking `get_serializer_kwargs`/`get_serializer` hooks ship as the waiver base
  (Worker 1's D7 note) and are signature-correct (`request_from_info(info, family_label=
  "SerializerMutation")` matches the keyword-only `family_label` param) even though inert this slice.
- The static helper found 0 Django/ORM markers in `rest_framework/sets.py` and `mutations/sets.py`
  (pure validation/helpers); the registry/finalizer markers are all pre-existing `DjangoTypeDefinition`/
  `_meta` references outside the seam edits. Repeated literals in `sets.py` are all spec-meaningful
  Meta key names.

### Temp test verification

`docs/builder/temp-tests/slice-2/test_waiver_and_guard.py` (2 tests, both PASS):
`test_create_guard_fires_through_build_input` (a create over a serializer with a required column-less
writable field, narrowed away via `Meta.fields`, raises `ConfigurationError` at
`finalize_django_types()`) and `test_waiver_when_get_serializer_kwargs_overridden` (the same declaration
with a `get_serializer_kwargs` override binds without raising). Disposition: caught a real
missing-coverage gap (the Medium above) — recommended for promotion into
`tests/rest_framework/test_sets.py` as the serializer twin of the form's per-declaration guard test.
Not a behavior bug; the implementation is correct. Temp file is gitignored.

### Static inspection helper

Re-ran (all under `--output-dir docs/shadow`, gitignored, line numbers non-canonical):
- `rest_framework/sets.py` — 2 hotspots (`_validate_meta` 104 lines / 6 branches = the validation
  matrix, justified; `build_input` 73 lines / 0 branches), 0 Django/ORM markers, 5 repeated literals
  (all spec-meaningful Meta key names). No finding.
- `registry.py` — `TypeRegistry.clear` 108 lines / 1 branch (absorbed the 2-line seam loop;
  deterministic iteration); ORM markers all pre-existing `DjangoTypeDefinition` refs outside the seam
  edits. No finding.
- `types/finalizer.py` — ORM markers all pre-existing; the pre-bind reset edit is a 2-line loop
  replacing two direct calls, no new hotspot. No finding.
- `mutations/sets.py` — 0 Django/ORM markers; the five promotions are net-new small helpers, not
  hotspot growth; `_validate_meta` re-point trims it. No finding.

### Notes for Worker 1 (spec reconciliation)

- D8 resolver deferral confirmed correct (see D8 verdict); recommend confirming the serializer
  `resolve_sync`/`resolve_async` overrides land in Slice 3 at final verification.
- The three Worker-1 items already recorded in the Plan's `### Notes for Worker 1` (stale spec status
  header → Slice 4; `optional_fields` bind-time vs class-creation reject → Worker-1 judgment, no spec
  conflict; D2 no-snapshot-slot) are accurate and need no new escalation — reviewed and concur.

### Review outcome

review-accepted. One Medium (missing serializer guard/waiver integration test) recorded with the temp
test recommended for promotion; the underlying behavior is verified correct, so this is a coverage gap
Worker 2 should close by promoting the temp test, not a behavior defect. All DRY promotions, the
`register_subsystem_clear` seam, the root `__getattr__` export, and the D8 deferral verified. Focused
suites green without `--cov`: `tests/rest_framework tests/forms tests/mutations tests/base tests/types`
= 853 passed / 2 skipped; `tests/test_registry.py tests/utils` = 156 passed.

---

## Final verification (Worker 1)

**Outcome: `revision-needed`** — one tightly-scoped test-promotion fix back to Worker 2 (the
Medium below). Everything else (DRY, the seam, the export, the D8 deferral, the focused suite)
verifies clean; the slice's source is correct and unchanged-worthy. The only blocker is a
missing exercising test for genuinely-new Slice-2 wiring, which `fail_under = 100` +
`AGENTS.md` "Add tests in the same change as code" do not permit to ship untested.

### Spec slice checklist audit (re-audited against the working-tree diff)

Every `- [x]` re-checked against `git diff` of the eleven slice files + `tests/rest_framework`.
All six boxes' contracts landed in the diff — confirmed at source, not on prose:

- **Box 1 (`rest_framework/sets.py` `SerializerMutation` + the exact override set).** Landed:
  `SerializerMutation(DjangoMutation)` at `rest_framework/sets.py` overrides `_resolve_model`
  (→ `Meta.serializer_class.Meta.model`, tolerant getattr chain), `_validate_meta` (the full
  matrix), `build_input`, `input_type_name`, `input_module_path`. The validation ordering is
  verified: `reject_unknown_meta_keys` → require `serializer_class` → `issubclass(Serializer)`
  → `issubclass(ModelSerializer)` → resolvable `Meta.model`, ALL before `_resolve_model`
  (`build_input` at src 260-332; `_validate_meta` matrix pinned by `test_sets.py:132-311`).
  `operation` gated through `NON_DELETE_WRITE_OPERATIONS` (`sets.py:228`). Allowed-key set
  ADDS `serializer_class`/`optional_fields`, KEEPS `operation`/`fields`/`exclude`/
  `permission_classes`, DROPS `model`/`input_class`/`partial_input_class`. Module behind the
  top-level `from rest_framework import serializers` DRF guard. **D8 partial-tick resolved
  below** (the box also names `resolve_sync`/`resolve_async`; those two are deferred to
  Slice 3 — accepted-with-deferral, box stays `- [x]`).
- **Box 2 (no change to `DEFERRED_META_KEYS`/`ALLOWED_META_KEYS`).** Confirmed: `types/base.py`
  not in the diff; pinned live by `test_deferred_and_allowed_meta_keys_unchanged`
  (`test_sets.py:518`).
- **Box 3 (`types/finalizer.py`/`registry.py` ride `bind_mutations()` + the two-site clear via
  the `register_subsystem_clear` seam).** Landed: `register_subsystem_clear`/
  `iter_subsystem_clears` defined once in `registry.py:72/88`; the finalizer pre-bind reset
  and `TypeRegistry.clear()` both iterate it via `_clear_if_importable`; the mutation/form
  input clears MOVED into the canonical list (registered at import time by their own modules),
  the serializer row registered by `rest_framework/inputs.py`. Retry-idempotence locked by
  `test_bind_is_retry_idempotent_after_fixable_later_phase_failure` (`test_sets.py:440`). No
  `bind_serializer_mutations()`. Model/form pre-bind equivalence holds (the focused
  `tests/forms`/`tests/mutations` retry-idempotence tests stay green unchanged — 853 passed).
- **Box 4 (`__init__.py` root `__getattr__` export, NOT in `__all__`).** Landed: PEP-562
  `__getattr__` resolves `SerializerMutation` by name through `require_drf()`, non-memoizing;
  `__all__` byte-unchanged (the diff only removes the TODO block and adds `__getattr__`).
  Pinned by `test_serializer_mutation_resolves_through_root_getattr` /
  `test_serializer_mutation_not_in_all` (`test_sets.py:113/122`) + the soft-dep suite.
- **Box 5 (`tests/rest_framework/test_sets.py` Meta matrix + registration + bind + no-primary
  + base-unregressed).** Landed: 24 tests covering the matrix, registration, the
  `bind_mutations()` path, the no-primary finalize error, and base-unregressed. **See the
  Medium below — this box's contract landed as worded, but it does NOT enumerate the
  guard/waiver integration test; that gap is the revision blocker (a missing test for new
  Slice-2 source wiring), recorded as a finding rather than an un-tick of a box whose stated
  contract did land.**
- **Box 6 (DRY/reuse).** Landed and verified single-sited — see DRY check below.

No box was over-ticked (every ticked contract has matching implementation in the diff) and no
box is silently un-ticked. The Medium is a missing-test finding against new source, not a
checklist box whose stated contract is absent.

### D8 partial-tick — DECISION: accept the partial-tick, deferral recorded

**Accepted.** Box 1's "exact override set" names `resolve_sync`/`resolve_async`, but Worker 2
deferred those two overrides to Slice 3 (D8 option b). This is correct build order, proved
mechanically:

- `rest_framework/resolvers.py` exists at HEAD only as a `TODO(spec-039 Slice 3)` comment stub
  — no `resolve_serializer_sync`/`resolve_serializer_async` defined. A `resolve_sync` override
  delegating to it would be a never-called function-local import of a non-existent name.
- `SerializerMutation` defines NO `resolve_sync`/`resolve_async` in its own body (verified:
  only docstring mentions; no `def resolve_sync`), so it inherits `DjangoMutation`'s callable
  classmethods — the Decision-5 `DjangoMutationField` target-check (`_has_mutation_protocol`)
  still sees a callable resolver pair, and a declared `SerializerMutation` is inert this slice
  (registered + bound, never resolved).
- The form precedent confirms the split: `forms/sets.py:577/591` DOES override
  `resolve_sync`/`resolve_async` with `from .resolvers import resolve_form_sync` — and
  `forms/resolvers.py:591` EXISTS with the real `resolve_form_sync` body. The form flavor
  landed its resolver overrides in the same slice the resolver module existed. The serializer
  must do the same in Slice 3.

Box 1 stays `- [x]`; the `resolve_sync`/`resolve_async` serializer overrides are recorded as a
Slice-3 deferral under `### Spec changes made (Worker 1 only)`.

### THE MEDIUM FINDING — DECISION: `revision-needed` (promote the temp test)

**`revision-needed`.** Worker 3's Medium is correct and I am NOT accepting it as-is.

The genuinely-new Slice-2 wiring in `rest_framework/sets.py::SerializerMutation.build_input`
(src 298-332) — the `guard_waived = _hook_overridden(cls, SerializerMutation,
"get_serializer_kwargs")` waiver, the `_guard()` closure that runs
`guard_create_required_serializer_fields` only on `CREATE` and only when not waived, and the
routing of that `_guard` through the promoted `cached_build_input` (guard-before-cache-lookup)
— has **no exercising assertion** in the permanent `tests/rest_framework/test_sets.py` suite. I
grepped the file: zero matches for `get_serializer_kwargs`, `guard`, `waiver`, or `narrow`. The
Slice-1 `test_inputs.py` pins `guard_create_required_serializer_fields` only at the
**generator** level, not the `sets.py` `build_input` wiring. The form flavor HAS the twin
integration test (`tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration`,
src 421) — the serializer flavor must not ship without its parallel.

Why this is `revision-needed` and not `review-accepted`-with-escalation: per BUILD.md, the
escalated-Medium path is reserved for findings needing spec context Worker 2 cannot provide.
This is not one — it is a missing test for source that already exists and is verified correct.
The repo gates at `fail_under = 100` and `AGENTS.md:13` mandates "Add tests in the same change
as code"; an untested new branch is a real gap. I confirmed it is NOT covered elsewhere:
Slice 3's products `ItemSerializer` (per `rest_framework/resolvers.py`'s Slice-3 TODO) is a
real, functioning live serializer surface — it will not narrow a required field away on create
(that would be a broken schema) and will not override `get_serializer_kwargs` for its own sake,
so it cannot incidentally exercise either the guard-fires or the waiver branch. The gap is real
and durable.

**Instruction to Worker 2 (tightly scoped):** Promote Worker 3's temp test
`docs/builder/temp-tests/slice-2/test_waiver_and_guard.py` (two tests) into
`tests/rest_framework/test_sets.py` as the serializer twin of the form's
`test_cached_build_form_input_runs_required_guard_per_declaration`, then delete the temp file.
The two cases: (1) a create `SerializerMutation` over a serializer with a required column-less
writable field narrowed away via `Meta.fields` raises `ConfigurationError` at
`finalize_django_types()`; (2) the same declaration with a `get_serializer_kwargs` override
binds without raising. **Strongly consider strengthening case (1) to the form test's actual
load-bearing shape** — the per-declaration cache-poisoning property: a WAIVING declaration that
materializes the narrowed shape FIRST must not poison the per-shape build cache for a later
NON-waiving declaration over the same `(serializer_class, operation_kind, effective set)` (the
guard-before-cache-lookup contract, spec-039 Finding 5 / Decision 7). The form test
(`test_sets.py:421-461`) drives `_cached_build_form_input` directly with `guard_required=False`
then `guard_required=True` over the same shape; the serializer equivalent can drive two
declarations (one with a `get_serializer_kwargs` override, one without) over the same
serializer + effective set and assert the second still raises. The promoted temp test pins
guard-fires + waiver-suppresses but NOT the cache-poisoning angle, which is the property the
`cached_build_input` ordering actually protects. No source change is required; this is a
test-only revision.

### DRY check across Slice 2 + prior accepted slices (0, 1)

Clean. The five promotions are single-sited and the form re-points introduced no duplication or
drift (verified at source):

- **P1.2 `NON_DELETE_WRITE_OPERATIONS`** — defined once (`mutations/sets.py:112`), imported by
  `forms/sets.py:57` and `rest_framework/sets.py:61`. NO `_VALID_FORM_OPERATIONS` /
  `_VALID_SERIALIZER_OPERATIONS` anywhere in the package (grep returned nothing). The shared
  "no delete" message single-sites through `non_delete_operation_error` (D3, builder chosen).
- **P2.7 `reject_unknown_meta_keys`** — defined once (`mutations/sets.py:134`); model, both
  form bases, and the serializer call it with their own frozenset.
- **P2.6 `_hook_overridden`** — defined once (`mutations/sets.py:151`); `forms/sets.py::_form_kwargs_overridden`
  (`:263`) kept as a thin two-hook adapter composing it (no duplicated identity check); the
  serializer waiver calls `_hook_overridden` directly. No `_cached_build_serializer_input` /
  `_build_and_stash_serializer_input` (grep returned nothing).
- **P1.7 `cached_build_input` + `build_and_stash_input`** — defined once (`mutations/sets.py:165/200`);
  both flavors ride them; the guard-before-cache-lookup ordering is single-sited.
- **P1.6 `register_subsystem_clear` + `iter_subsystem_clears`** — defined once
  (`registry.py:72/88`); the seam membership is exactly the three input-namespace clears in the
  pre-bind set, with declaration-registry + shape-cache resets correctly `registry.clear()`-only.

No version bump (Decision 14): `pyproject.toml:4` and `__init__.py:37` both `0.0.12`.
`require_drf()` install hint names `djangorestframework>=3.17.0` (`rest_framework/__init__.py:29`).
Root `__getattr__` is the spec-authorized named-lazy export (Decision 12 / F1 / DoD 8);
`SerializerMutation` not in `__all__`.

### Existing tests still pass (focused scope, no coverage flags)

`uv run pytest tests/rest_framework tests/forms tests/mutations tests/base tests/types --no-cov`
→ **853 passed, 2 skipped**. (This is the pre-fix baseline; the revision adds the
guard/waiver test, which will raise the count.)

### Spec reconciliation

No spec edit this pass. The stale `Status: **IN PROGRESS** … no slice built yet` header
(spec line ~54) is intentionally Slice-4-owned (the doc-wrap slice lands the implemented-on-main
header edit; per the Slice-1 carry-forward it is not churned per-slice mid-build) — recorded in
the Plan's `### Notes for Worker 1` and not re-flagged as a new finding. The Medium is a
test-only fix needing no spec context. `check_spec_glossary.py` not re-run (no spec edit).

### Summary

Slice 2 ships the `SerializerMutation` base correctly: the `Meta` validation matrix, the
`bind_mutations()` phase-2.5 ride, the five DRY promotions single-sited, the
`register_subsystem_clear` seam (retry-idempotent, soft-dep-safe), and the soft-DRF root
`__getattr__` export (not in `__all__`). The source is correct and the focused suite is green
(853 passed). The one blocker is a missing permanent test for the new `build_input`
guard/waiver wiring — a `fail_under = 100` / "tests in the same change" gap that the form
flavor's twin test does not let the serializer skip. Returning to Worker 2 for a test-only
promotion (with a recommendation to strengthen to the cache-poisoning shape). The D8
`resolve_sync`/`resolve_async` partial-tick is accepted with the Slice-3 deferral recorded.

### Spec changes made (Worker 1 only)

None. No spec edit was warranted this pass.

Deferral recorded (for the Slice-3 carry-forward, not a spec edit): the Box-1 "exact override
set" names `resolve_sync`/`resolve_async`; those two serializer overrides are deferred to
Slice 3 (D8 option b), where `rest_framework/resolvers.py` gains `resolve_serializer_sync`/
`resolve_serializer_async` and `SerializerMutation` gains the function-local-import overrides
delegating to them — the same slice/resolver-existence pairing the form flavor used
(`forms/sets.py:577/591` ride `forms/resolvers.py:591`).

---

## Build report (Worker 2, pass 2)

Apply-changes pass after Worker 1's `revision-needed`. Test-only fix per the Medium finding
(Worker 3) + Worker 1's strengthening instruction. NO source change (Worker 1 confirmed the
Slice-2 `build_input` guard/waiver behavior is correct; this is a missing-coverage fix).

### Files touched

- `tests/rest_framework/test_sets.py` — added a new `build_input` create-required guard +
  `get_serializer_kwargs` waiver section (one local fixture + three tests). Extended the module
  docstring's coverage list with the guard/waiver/per-declaration bullet. The promoted temp
  test's two cases plus the strengthened per-declaration cache-poisoning case land here as the
  serializer twin of the form's `test_cached_build_form_input_runs_required_guard_per_declaration`.
- `docs/builder/temp-tests/slice-2/test_waiver_and_guard.py` — DELETED (the file was untracked,
  so it does not appear in `git status`; the now-empty `docs/builder/temp-tests/` tree was
  removed with it). Promoted into `tests/rest_framework/test_sets.py` per Worker 1's instruction.

### Tests added or updated

- `tests/rest_framework/test_sets.py::test_create_required_guard_fires_through_build_input` —
  promoted temp case 1. A create `SerializerMutation` over `_item_serializer_with_required_extra()`
  (a `ModelSerializer` with a required column-less `confirm` field) narrowing `confirm` away via
  `Meta.fields=("name","category")` raises `ConfigurationError` (match `"confirm"`) at
  `finalize_django_types()` — the `_guard()` closure firing through `cached_build_input`.
- `tests/rest_framework/test_sets.py::test_get_serializer_kwargs_override_waives_create_required_guard` —
  promoted temp case 2. The same narrowed declaration WITH a `get_serializer_kwargs` override
  binds without raising (`_input_class is not None`) — the `_hook_overridden(cls,
  SerializerMutation, "get_serializer_kwargs")` waiver suppresses the guard.
- `tests/rest_framework/test_sets.py::test_build_input_runs_required_guard_per_declaration` —
  the strengthened per-declaration cache-poisoning test (Worker 1's instruction; the serializer
  twin of `tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration`).
  Two declarations over the SAME `(serializer_class, operation="create", effective set)` in one
  build: a WAIVING `WaivedCreateItem` (overrides `get_serializer_kwargs`) materializes the
  narrowed `ItemSerializerInput` shape FIRST (populating `_serializer_shape_build_cache`), then a
  NON-waiving `GuardedCreateItem` over the same shape must STILL raise (match `"confirm"`) at
  `finalize_django_types()`. Pins the guard-before-cache-lookup contract (spec-039 Finding 5 /
  Decision 7): the waived shape in the cache must not suppress a later declaration's guard.

### Validation run

- `uv run ruff format .` — pass (295 files left unchanged; the `COM812` warning is the
  pre-existing formatter-config note, not a change).
- `uv run ruff check --fix .` — pass (Found 2 errors, 2 fixed, 0 remaining). The two fixes were
  `RUF100` unused-`noqa` removals on the two `get_serializer_kwargs` override signatures I added
  (the `# noqa: ARG002` I had placed on `info` is unnecessary in the test ruleset). Both fixes
  landed only on `tests/rest_framework/test_sets.py` (my slice-intended file).
- `git status --short` after both ruff runs — the only file I modified this pass is
  `tests/rest_framework/test_sets.py` (slice-intended). The temp-test deletion is invisible in
  `git status` (untracked file). All other `M`/`??` entries are prior-accepted Slice-0/1/2 bodies
  + Worker 1's spec edit + baseline-dirty `docs/feedback.md` — NOT touched this pass (left as-is
  per the task contract; `docs/feedback.md` untouched). No tool churn to revert (ruff modified
  only my file).
- `uv run pytest tests/rest_framework/test_sets.py --no-cov` — **27 passed** (the three new tests
  + the prior 24).
- `uv run pytest tests/rest_framework tests/forms tests/mutations --no-cov` — **430 passed** (no
  regression; the form twin `test_cached_build_form_input_runs_required_guard_per_declaration`
  and the model/form retry-idempotence tests stay green).

### Implementation notes

- **Integration-level drive (not a direct helper call).** The form twin drives
  `_cached_build_form_input` directly with `guard_required=False` then `True`. The serializer
  flavor has NO per-flavor `_cached_build_*` wrapper (it rides the promoted `cached_build_input`
  directly inside `build_input`), so there is no equivalent function to call with a `guard_required`
  toggle. I drove the property at the `finalize_django_types()` integration level instead — exactly
  Worker 1's recommended shape ("drive two declarations … over the same serializer + effective set
  and assert the second still raises"). Both declarations live in one build so they share the
  per-shape cache; the waiver/non-waiver distinction is the `get_serializer_kwargs` override
  presence, mirroring the form test's `guard_required` toggle.
- **Local fixture `_item_serializer_with_required_extra()`** — distinct from the existing
  `_item_serializer()` (which has no required column-less field, so it never triggers the guard).
  The `confirm = serializers.CharField()` field is required-writable with no model column, so
  narrowing to model columns drops a still-required field — the guard's exact trigger
  (`_required_writable_field_names` minus the effective set is non-empty). Carried over from the
  temp test's `_serializer_with_extra_required` shape.
- **`match="confirm"`** — `guard_create_required_serializer_fields` raises
  `... drops required serializer field(s) ['confirm'] ...` (the dropped names via `{dropped!r}`),
  so matching the bare field name is stable against message-wording churn.

### Notes for Worker 3

- The three new tests sit in their own section (`build_input create-required guard +
  get_serializer_kwargs waiver`) between the retry-idempotence and base-unregressed sections.
  No source was touched this pass — the diff is purely `tests/rest_framework/test_sets.py` (plus
  the temp-file deletion). No shadow files used.
- The strengthened test's value is the cache-poisoning angle: `test_create_required_guard_fires_through_build_input`
  alone proves the guard fires; the per-declaration test additionally proves a FIRST waiving
  declaration that materializes + caches the narrowed shape does not let a LATER non-waiving
  declaration skip the guard. The guard runs before the cache lookup in `cached_build_input`, so
  the cached waived shape is irrelevant to the second declaration's guard.

### Notes for Worker 1 (spec reconciliation)

- No spec edit this pass; no new spec gap found. The `resolve_sync`/`resolve_async` Slice-3
  deferral (D8 option b) recorded in the prior report's notes is unchanged and not re-broadened —
  the new tests do NOT add those overrides (per the task scope: they are an accepted Slice-3
  deferral).
- The strengthening instruction is satisfied at the integration level rather than by a direct
  `cached_build_input(guard=...)` toggle (the serializer has no per-flavor wrapper to drive); see
  the Implementation note. If you prefer a unit-level drive of `cached_build_input` directly
  (passing a waived vs guarded closure over the same `_serializer_shape_build_cache` + `shape_key`),
  flag it — but the integration drive matches your recommended "two declarations over the same
  shape" shape and exercises the full `build_input` → `cached_build_input` path the source actually
  runs.

---

## Review (Worker 3, pass 2)

Re-review of Worker 2's pass-2 (test-only) apply-changes after Worker 1 escalated my pass-1
Medium to `revision-needed`. Scope per the task: confirm the Medium is resolved. Reviewed
`git diff -- tests/rest_framework/test_sets.py` (the only file Worker 2 changed this pass) and
traced the three new tests against the source wiring in
`django_strawberry_framework/rest_framework/sets.py::SerializerMutation.build_input`
(src 260-332), `mutations/sets.py::cached_build_input` (src 165-197), and
`rest_framework/inputs.py::guard_create_required_serializer_fields` (src 439-471). Read the prior
review, Worker 1's Medium decision, and the pass-2 build report. Did NOT read worker-0/1/2 memory
(read-isolation honored). Did NOT run `--cov*`.

### No-source-change confirmation

`git diff --stat -- tests/` shows the pass-2 contribution is in `tests/rest_framework/test_sets.py`
(the other test files are prior-accepted Slice-1/2 bodies). The three net-new tests + one local
fixture + the docstring extension are the only pass-2 additions; the rest of the `test_sets.py`
diff is the pass-1 matrix already reviewed under `## Review (Worker 3)`. `django_strawberry_framework/`
carries no NEW pass-2 change: the serializer `build_input` guard/waiver wiring (src 298-332), the
`cached_build_input` guard-before-cache-lookup core, and the root `__getattr__` are byte-for-byte
the pass-1-accepted bodies. Confirmed there is no `resolve_sync` / `resolve_async` OVERRIDE method
added this pass — the only occurrence of those names in `sets.py` is the line-42 docstring prose
recording the accepted Slice-3 deferral (D8 option b). No scope creep.

### High

None.

### Medium

None. **The pass-1 Medium is RESOLVED.** The `sets.py`-level guard/waiver wiring now has three
exercising tests in the permanent suite:

1. `test_create_required_guard_fires_through_build_input` (diff) — a create `SerializerMutation`
   over `_item_serializer_with_required_extra()` (a `ModelSerializer` with a required column-less
   `confirm`) narrowing `confirm` away via `Meta.fields=("name","category")` raises at
   `finalize_django_types()`. This fires the `_guard()` closure (`build_input` src 300-302) through
   the promoted `cached_build_input` — the genuinely-new Slice-2 wiring, not the Slice-1
   generator-level `test_inputs.py`. Non-vacuous: asserts the SPECIFIC `ConfigurationError`
   (`pytest.raises(ConfigurationError, match="confirm")`) and `guard_create_required_serializer_fields`
   (src 466-471) is the only thing that raises naming a dropped field, so the match is targeted, not
   an incidental any-error catch.
2. `test_get_serializer_kwargs_override_waives_create_required_guard` (diff) — the SAME narrowed
   declaration WITH a `get_serializer_kwargs` override binds (`_input_class is not None`). This pins
   the `guard_waived = _hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")` waiver
   (`build_input` src 298): with the guard fired in test 1 and waived in test 2 over an identical
   `Meta`, the override is provably the load-bearing difference.
3. `test_build_input_runs_required_guard_per_declaration` (diff) — the cache-poisoning property
   Worker 1 asked for. TWO declarations over the SAME shape in ONE build: `WaivedCreateItem`
   (overrides `get_serializer_kwargs`, narrows `confirm` away) materializes the narrowed
   `ItemSerializerInput` shape FIRST, populating `_serializer_shape_build_cache`; then a non-waiving
   `GuardedCreateItem` over the SAME `serializer_class` + SAME `fields=("name","category")` must
   STILL raise at finalize. This is the genuine two-declarations-over-one-shape drive (not a weaker
   vacuous shape): both produce the identical `shape_key = (serializer_class, CREATE,
   frozenset({"name","category"}))` (`build_input` src 320), so the waived shape IS in the cache when
   the second declaration's guard runs. Asserts the specific `ConfigurationError` (`match="confirm"`).

   I PROVED this test is non-vacuous with a temp test (now deleted; see Temp test verification):
   monkeypatching `cached_build_input` to a POISONABLE variant (cache lookup BEFORE guard) makes the
   exact two-declaration scenario `finalize` cleanly with `registry.is_finalized() is True` — i.e.
   the second guard is suppressed. The committed test raises ONLY because the real
   `cached_build_input` runs `guard()` before `cache.get(shape_key)` (src 191-192). The test therefore
   genuinely pins the guard-before-cache-lookup ordering — the load-bearing contract the form twin
   `tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration`
   (src 421-461) locks. The serializer twin drives it at the `finalize_django_types()` integration
   level (correct: the serializer flavor rides the promoted `cached_build_input` directly inside
   `build_input` with no per-flavor `_cached_build_*` wrapper to call with a `guard_required` toggle).

### Low

None.

### DRY findings

Clean. The three new tests reuse the existing module fixtures sensibly: `_declare_products_primaries()`
(shared with the bind / retry-idempotence tests) and the autouse `_isolate_registry` fixture. The
one new fixture `_item_serializer_with_required_extra()` is justified, not duplication — the existing
`_item_serializer()` has no required column-less field, so it can NEVER trigger the create-required
guard; a distinct serializer with a required writable `confirm` field (no model column) is the guard's
exact trigger. Mirrors the form twin's local `_RequiredExtraForm` shape. No repeated literals worth
hoisting; the `match="confirm"` substring is stable against message-wording churn (matches the dropped
field name via `{dropped!r}`).

### Static inspection helper

Skipped — no source `.py` changed this pass (test-only). No new `django_strawberry_framework/` logic,
no `optimizer/` or `types/` touch, < the line thresholds for a non-source file's logic count that would
trigger a re-run for evidence. The pass-1 helper run on the four source files stands.

### Public-surface check

Unchanged since pass 1 (no source change this pass). Confirmed live: `SerializerMutation` not in
`django_strawberry_framework.__all__` (`False`); the root `__getattr__` body is byte-identical to the
pass-1-accepted export. `git diff -- django_strawberry_framework/__init__.py` is the accepted Slice-2
`__getattr__`, not a pass-2 change.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable.

### Temp test verification

Wrote one temp test (`docs/builder/temp-tests/slice-2/test_vacuity.py`, since DELETED) that
monkeypatched `cached_build_input` to a poisonable cache-lookup-before-guard variant and re-ran the
committed test 3's exact two-declaration scenario: under the inverted ordering `finalize_django_types()`
SUCCEEDS (`registry.is_finalized() is True`) — the second declaration's guard is silently skipped.
This proves the committed `test_build_input_runs_required_guard_per_declaration` is non-vacuous: it
catches a regression of the guard-before-cache-lookup ordering. The three permanent tests pass
(`uv run pytest tests/rest_framework/test_sets.py -k "guard or waive or per_declaration" --no-cov` →
3 passed). The temp file was removed after verification (no temp test left as the only proof — all
three behaviors are pinned by permanent tests).

### What looks solid

- Worker 1's strengthening instruction is fully discharged: test 3 drives the cache-poisoning angle
  with two declarations over one shape in one finalize, not a weaker shape that passes vacuously.
- All three assertions are specific (`ConfigurationError` with a targeted `match`), not bare `raises`.
- The integration-level drive is the right choice — it exercises the full
  `build_input` → `cached_build_input` → `guard` path the source actually runs at bind, rather than a
  synthetic direct helper call (the serializer has no `_cached_build_*` wrapper to toggle).
- Focused suite green: `uv run pytest tests/rest_framework tests/forms tests/mutations --no-cov`
  → 430 passed (the form twin and model/form retry-idempotence tests stay green; no regression).

### Notes for Worker 1 (spec reconciliation)

None. No spec context needed; this was a test-only coverage fix. The `resolve_sync`/`resolve_async`
Slice-3 deferral (D8 option b) is unchanged and not re-broadened by this pass.

### Review outcome

`review-accepted`. The pass-1 Medium is resolved: the serializer `build_input` create-required guard,
the `get_serializer_kwargs` waiver, and the per-declaration cache-poisoning property are now pinned by
three non-vacuous permanent tests in `tests/rest_framework/test_sets.py`, the serializer twin of the
form flavor's locked contract. No source change this pass (verified); no scope creep; no new findings.

---

## Final verification (Worker 1, re-pass)

**Outcome: `final-accepted`.** The Medium I set `revision-needed` over (a missing exercising
test for the genuinely-new `build_input` guard/waiver wiring) is RESOLVED test-only, with the
cache-poisoning property landed at the strength I requested. Source is byte-unchanged from the
pass-1-accepted bodies, the focused suite is green, and every prior-pass verdict re-confirms.
This re-pass does NOT edit the prior `## Final verification (Worker 1)` section above; it
confirms-and-closes.

### 1. The Medium is resolved (test-only, no pass-2 source change)

- **The three tests are present and non-vacuous** (`tests/rest_framework/test_sets.py`,
  verified at source, not on the report):
  - `test_create_required_guard_fires_through_build_input` (src 507) — a create
    `SerializerMutation` over `_item_serializer_with_required_extra()` (a `ModelSerializer`
    with a required column-less `confirm`) narrowing `confirm` away via
    `Meta.fields=("name","category")` → `pytest.raises(ConfigurationError, match="confirm")` at
    `finalize_django_types()`. Fires the `_guard()` closure through the promoted
    `cached_build_input` — the new Slice-2 wiring, not the Slice-1 generator-level pin. Targeted
    `match=` (the dropped field name), not a bare `raises`.
  - `test_get_serializer_kwargs_override_waives_create_required_guard` (src 528) — the SAME
    narrowed declaration WITH a `get_serializer_kwargs` override binds (`_input_class is not
    None`). With the guard fired in the first test and waived here over an identical `Meta`, the
    override is the provable load-bearing difference (the
    `_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")` waiver, `sets.py` src
    298).
  - `test_build_input_runs_required_guard_per_declaration` (src 553) — the per-declaration
    cache-poisoning property I asked for, at the strength of the form twin
    (`tests/forms/test_sets.py::test_cached_build_form_input_runs_required_guard_per_declaration`).
    TWO declarations over the SAME `(serializer_class, operation="create", effective set)` in ONE
    build: a WAIVING `WaivedCreateItem` (overrides `get_serializer_kwargs`) materializes the
    narrowed `ItemSerializerInput` shape FIRST (populating `_serializer_shape_build_cache`), then
    a NON-waiving `GuardedCreateItem` over the same shape STILL raises
    (`match="confirm"`). This is the genuine two-declarations-over-one-shape drive — not the
    weaker guard-fires-once shape the promoted temp test had.
- **The property is real at source.** `mutations/sets.py::cached_build_input` (src 165) runs
  `guard()` (src 191) BEFORE `cache.get(shape_key)` (src 192). The waived shape in the cache is
  therefore irrelevant to a later declaration's guard — the contract test 3 pins. Worker 3
  additionally proved test 3 non-vacuous with a now-deleted poisonable-ordering temp test (cache
  lookup before guard → the two-declaration scenario finalizes cleanly), recorded under their
  `### Temp test verification`. I accept that proof; the ordering is single-sited and verified.
- **No pass-2 source change.** `git diff --stat -- django_strawberry_framework/` is the cumulative
  Slice-2 diff (HEAD predates the slice); the pass-2 contribution is confined to
  `tests/rest_framework/test_sets.py` (one fixture + three tests + a docstring bullet) plus the
  untracked temp-file deletion. Spot-confirmed the wiring is the pass-1-accepted body: no
  `def resolve_sync` / `def resolve_async` in `rest_framework/sets.py` (the only occurrence is the
  line-42 docstring recording the D8 deferral), and `cached_build_input`'s guard-before-cache
  ordering is intact. No scope creep.

### 2. Focused suite green (no coverage flags)

`uv run pytest tests/rest_framework tests/forms tests/mutations tests/base tests/types --no-cov`
→ **856 passed, 2 skipped** (explicit `--no-cov`; no `--cov*`). Exactly +3 over the pre-fix 853
baseline — the three new guard/waiver tests, no regression. The form twin
`test_cached_build_form_input_runs_required_guard_per_declaration` and the model/form
retry-idempotence tests stay green (model/form pre-bind equivalence preserved by the
`register_subsystem_clear` seam).

### 3. Prior-pass verdicts re-confirmed (nothing regressed)

- **D8 partial-tick deferral recorded and intact** — `resolve_sync`/`resolve_async` serializer
  overrides remain deferred to Slice 3 (D8 option b); `rest_framework/sets.py` carries only the
  docstring note, no override `def`. Box 1 stays `- [x]` (the carry-forward already recorded under
  `### Spec changes made (Worker 1 only)`).
- **5 DRY promotions single-sited** — `NON_DELETE_WRITE_OPERATIONS` (`mutations/sets.py:112`),
  `reject_unknown_meta_keys` (`:134`), `_hook_overridden` (`:151`), `cached_build_input` (`:165`),
  `build_and_stash_input` (`:200`); `register_subsystem_clear`/`iter_subsystem_clears`
  (`registry.py:72/88`). Grep for `_VALID_FORM_OPERATIONS` / `_VALID_SERIALIZER_OPERATIONS` /
  `_cached_build_serializer_input` / `_build_and_stash_serializer_input` returns nothing — no
  byte-parallel flavor copies.
- **No version bump** (Decision 14) — `0.0.12` in `pyproject.toml:4` + `__init__.py:37`.
- **`__all__` unchanged** — `SerializerMutation` resolved via root `__getattr__` (`__init__.py:58`),
  deliberately absent from `__all__`.
- **`require_drf()` hint names `djangorestframework>=3.17.0`** (`rest_framework/__init__.py:29`) —
  place 2 of the three-places-that-must-agree, matching pyproject (place 1) + spec Risks (place 3).

### Summary

Slice 2 is complete. The serializer `build_input` create-required guard, the
`get_serializer_kwargs` waiver, and the per-declaration cache-poisoning property are now pinned by
three non-vacuous permanent tests (`tests/rest_framework/test_sets.py`, the serializer twin of the
form flavor's locked contract), resolving the single Medium that blocked pass 1. The fix was
test-only — source is byte-unchanged from the pass-1-accepted bodies. The focused suite is green
(856 passed, 2 skipped, `--no-cov`), the five DRY promotions stay single-sited, no version bump,
`__all__` unchanged, the `require_drf()` hint names `>=3.17.0`, and the D8
`resolve_sync`/`resolve_async` partial-tick is accepted with the Slice-3 deferral recorded.
**`Status: final-accepted`.** No spec edit this pass (the stale spec Status header remains
Slice-4-owned per the carry-forward; `check_spec_glossary.py` not re-run — no spec edit).

### Spec changes made (Worker 1 only)

None this re-pass. The Slice-3 deferral of the serializer `resolve_sync`/`resolve_async` overrides
(D8 option b) recorded in the prior final-verification section is unchanged.
