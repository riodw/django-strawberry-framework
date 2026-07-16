# DRY review: `django_strawberry_framework/mutations/sets.py`

Status: verified

## System trace

`mutations/sets.py` owns the write-side declarative surface (spec-036 Slice 2 +
promoted cross-flavor seams from 038/039):

1. **Shared write-flavor plumbing** — `make_declaration_registry`,
   `make_meta_validating_metaclass` (this pass), `reject_unknown_meta_keys`,
   `NON_DELETE_OPERATION_INPUT_KIND` / `NON_DELETE_WRITE_OPERATIONS` /
   `_VALID_OPERATIONS`, `non_delete_operation_error`, `cached_build_input` /
   `build_and_stash_input`, `construction_kwargs`, `require_backing_class` /
   `resolve_meta_model` / `resolve_backed_model_or_raise`, `_hook_overridden`,
   `resolver_seams`, `validate_select_for_update`, `_validate_permission_classes`,
   `_ValidatedMutationMeta`.
2. **Model flavor** — `DjangoMutation` + `DjangoMutationMetaclass`, Meta matrix
   (`_ALLOWED_MUTATION_META_KEYS`, input-class / fields / operation validation),
   declaration ledger (`register_mutation` / `iter_mutations`),
   `build_input` / `input_type_name` / `input_module_path` / `resolve_*` /
   `check_permission` seams, `_materialize_input_for` + merge + relation-override
   lock, `_bind_mutation` / `bind_mutations`.
3. **Phase-2.5 bind** — drains the model declaration registry (not
   `_bind_sidecar_sets`); form / serializer flavors that subclass
   `DjangoMutation` ride this pass; plain form keeps a disjoint bind.

Connected behavior examined:

- `forms/sets.py` — ModelForm rides model metaclass + ledger; plain form uses
  `make_declaration_registry` + (now) `make_meta_validating_metaclass` over a
  disjoint ledger / `bind_form_mutations`.
- `rest_framework/sets.py` — `SerializerMutation(DjangoMutation)` rides model
  metaclass / ledger / `bind_mutations` unchanged.
- `mutations/inputs.py` — `mutation_input_shape` / materialize / payload;
  `input_type_name` already routes through `mutation_input_shape(...).type_name`
  (inputs DRY; preserved).
- `mutations/fields.py` / `permissions.py` / `resolvers.py` — consume seams;
  operation vocabulary stays multi-axis (Meta allow-list here; perm action /
  pipeline branch / GraphQL args elsewhere).
- `auth/mutations.py` — `make_declaration_registry` for auth ledger; riders
  subclass `DjangoMutation`.
- `types/finalizer.py` / `registry.py` — phase-2.5 bind + co-clear.
- Tests — `tests/mutations/test_sets.py` (metaclass / Meta / bind); live product
  mutations under `examples/fakeshop/test_query/` (factory mechanics not
  earnable via GraphQL).

ITEM_BASELINE `b7bca69b39a1ee9c6e044c3d9be24890005667c1`: target matched baseline
at review start (concurrent WIP vs HEAD is the already-landed
`input_type_name` → `mutation_input_shape` routing from the inputs item —
preserved).

## Verification

Searches: `make_declaration_registry`, `attrs.get("Meta")`, `_mutation_meta`,
`DjangoMutationMetaclass`, `DjangoFormMutationMetaclass`, `_VALID_OPERATIONS`,
`NON_DELETE_WRITE_OPERATIONS`, `NON_DELETE_OPERATION_INPUT_KIND`,
`input_type_name`, `mutation_input_shape`, `bind_mutations`,
`bind_form_mutations`, `reject_unknown_meta_keys`, `resolver_seams` across
package + tests + prior forms deferral labels (search cues only).

Compared contracts:

- **`DjangoMutationMetaclass.__new__` ↔ `DjangoFormMutationMetaclass.__new__`** —
  after normalizing the register name: build → skip `Meta is None` →
  `_validate_meta` → register. Same lifecycle, disjoint ledgers via
  `register`. No third Meta-validating twin (Serializer / ModelForm inherit;
  FilterSet / OrderSet collect related declarations). **Confirmed** — true
  owner is this file beside `make_declaration_registry`.
- **`input_type_name` ↔ `mutation_input_shape(...).type_name`** — already
  single-sourced (inputs DRY). Preserve; do not re-walk
  `editable_input_fields`.
- **OPERATIONS vocabulary** — `_VALID_OPERATIONS` (model Meta allow-list),
  `NON_DELETE_WRITE_OPERATIONS` (form/serializer Meta),
  `NON_DELETE_OPERATION_INPUT_KIND` (generator kinds), permissions action map,
  resolver branches, fields arg shape are distinct change axes. Package-wide
  OPERATIONS module **rejected** (fields / permissions already proved).
  In-file derivation of the two Meta frozensets from the kind-map keys is the
  true-owner consolidation of the duplicated `create`/`update` spelling.
- **`bind_mutations` ↔ `bind_form_mutations`** — Decision 6: plain bind keeps
  `_primary_type=None`, different `build_input` arity, ok-payload. Reject fold.
- **`_ValidatedMutationMeta` / permission / select_for_update / resolver_seams /
  construction helpers** — already promoted; no second copy in this file.
- **OrderSet / FilterSet metaclasses** — related-declaration collection, not
  Meta-validate-and-register. Must not absorb.

No scratch under `docs/dry/temp-tests/`: structural identity of the two
`__new__` bodies + existing Meta/abstract-base tests + new factory probe
sufficed.

## Opportunities

### O1. `make_meta_validating_metaclass(register)` beside `make_declaration_registry`

- **Repeated responsibility:** class-creation lifecycle "if nested `Meta`,
  validate via `_validate_meta`, stash `_mutation_meta`, register for phase
  2.5"; only the register ledger differs.
- **Sites:** `mutations/sets.py::DjangoMutationMetaclass.__new__`,
  `forms/sets.py::DjangoFormMutationMetaclass.__new__`.
- **Evidence:** byte-identical after register rename; forms file + folder DRY
  deferred here as true owner; Serializer/ModelForm ride inheritance (no third
  twin); should change together if the abstract-base skip or stash contract
  moves.
- **Owner:** `mutations/sets.py::make_meta_validating_metaclass`.
- **Consolidation:** factory closes over `register` and takes keyword-only
  `name` / `module`; model + plain-form metaclasses become
  `make_meta_validating_metaclass(register_*, name="...", module=__name__)`
  assignments. The `name` / `module` pin restores each metaclass's public
  identity (`__name__` / `__qualname__` / `__module__`) so a function-local
  class does not leak into the public surface (addressability, introspection,
  reference pickling).
- **Proof:** `tests/mutations/test_sets.py::test_make_meta_validating_metaclass_validates_registers_and_skips_abstract`
  (disjoint ledgers + abstract skip + factory identity pin) and
  `test_public_metaclasses_pin_public_identity_and_pickle` (public
  name/qualname/module, module addressability, `pickle` round-trip); existing
  abstract-base / registration tests in `tests/mutations/test_sets.py` +
  `tests/forms/test_sets.py`.
- **Risks / non-goals:** do not fold FilterSet/OrderSet metaclasses; do not
  merge declaration ledgers.

### O2. Derive Meta operation frozensets from `NON_DELETE_OPERATION_INPUT_KIND`

- **Repeated responsibility:** the create/update verb set spelled independently
  in `NON_DELETE_WRITE_OPERATIONS` and `_VALID_OPERATIONS` (plus the kind map).
- **Sites:** the three module-level constants in this file.
- **Evidence:** non-delete Meta allow-list IS the set of ops that materialize
  an input; model allow-list IS that set plus `delete`. Same change axis when
  a new non-delete write verb lands.
- **Owner:** this file (not a package-wide OPERATIONS module).
- **Consolidation:**
  `NON_DELETE_WRITE_OPERATIONS = frozenset(NON_DELETE_OPERATION_INPUT_KIND)`;
  `_VALID_OPERATIONS = NON_DELETE_WRITE_OPERATIONS | frozenset({"delete"})`.
- **Proof:** existing Meta.operation reject tests for model / form /
  serializer flavors.
- **Risks / non-goals:** do not couple permissions action maps, resolver
  branches, or fields GraphQL-arg gating.

## Judgment

Deferred metaclass factory was warranted here as the true owner (Decision-13
twin of `make_declaration_registry`). In-file OPERATIONS derivation single-
sources create/update without inventing a cross-module vocabulary table.
`input_type_name` routing through `mutation_input_shape` preserved. Remaining
parallels (plain vs model bind, multi-axis operation verbs outside Meta) stay
intentionally separate. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** `mutations/sets.py::make_meta_validating_metaclass`;
  operation frozensets derived from `NON_DELETE_OPERATION_INPUT_KIND`.
- **Migrated sources:**
  - `django_strawberry_framework/mutations/sets.py` — factory (with keyword-only
    `name` / `module` identity pin); model metaclass assignment;
    `NON_DELETE_WRITE_OPERATIONS` / `_VALID_OPERATIONS` derivation; module
    docstring.
  - `django_strawberry_framework/forms/sets.py` — plain metaclass assignment
    via factory (`name` / `module` pinned); import + module docstring.
  - `tests/mutations/test_sets.py` — factory probe (abstract skip + disjoint
    ledgers + factory identity pin) and public-metaclass identity/pickle test.
    Package-internal tier: factory mechanics not earnable via live GraphQL.
- **Behavior kept separate:** declaration ledgers remain disjoint; FilterSet /
  OrderSet metaclasses untouched; permissions / resolvers / fields keep their
  own operation axes; `input_type_name` → `mutation_input_shape` left as
  baseline concurrent work.
- **Validation:** `uv run ruff format .` + `uv run ruff check --fix .` (pass).
  No full pytest. Worker 1 added the focused factory test without executing it;
  Worker 2 later ran it during independent verification (results below).
- **Changelog:** no (no maintainer authorization).
- **Concurrent paths preserved:** only cycle paths above edited. Pre-existing
  WIP under other packages / plan checkbox not touched. Item-scoped diff vs
  ITEM_BASELINE covers the three files above (+ this artifact).

## Independent verification (Worker 2)

Re-traced `mutations/sets.py` as the write-side declarative surface, then
compared the factory + frozenset changes against `forms/sets.py`,
`rest_framework/sets.py`, `auth/mutations.py`, FilterSet/OrderSet metaclasses,
`mutations/fields.py` / `permissions.py` / `resolvers.py`, and the focused
tests. Item-scoped diff vs `b7bca69b39a1ee9c6e044c3d9be24890005667c1` is only
the three claimed production/test files.

### Challenges (disposed)

1. **Shared factory contract (O1).** Pre-diff, both `__new__` bodies were
   build → skip when `attrs.get("Meta") is None` → `_validate_meta` → stash
   `_mutation_meta` → `register_*`. Only the register closed over a different
   ledger. That is one lifecycle with a parameterized owner, not two policies.
   `DjangoMutationMetaclass = make_meta_validating_metaclass(register_mutation)`
   and
   `DjangoFormMutationMetaclass = make_meta_validating_metaclass(register_form_mutation)`
   are both migrated; `DjangoMutationMetaclass is not DjangoFormMutationMetaclass`
   (distinct class objects, distinct closures). Serializer / ModelForm still
   ride the model metaclass via inheritance; auth riders likewise — no third
   Meta-validating twin. FilterSet / OrderSet `__new__` collect related
   declarations (and FilterSet aliases `filter_fields`) — different contract;
   correctly left out.

2. **Frozenset derivation (O2).**
   `frozenset(NON_DELETE_OPERATION_INPUT_KIND)` is the key set
   `{"create", "update"}`;
   `_VALID_OPERATIONS = NON_DELETE_WRITE_OPERATIONS | frozenset({"delete"})`
   restores the model triple. Meta allow-list membership for non-delete verbs
   *is* "ops that materialize an input," so deriving from the kind-map keys is
   the right owner axis. Runtime assert: sets equal the former literals.

3. **Package-wide OPERATIONS (rejected).** Permissions map verbs → Django
   actions (`add`/`change`/`delete`); fields gate GraphQL args
   (`id` / `data` / `"form"` sentinel); resolvers branch on verb literals.
   Those are distinct change axes — folding them into one vocabulary module
   would couple unrelated reasons to change. Rejection stands.

4. **`bind_mutations` ↔ `bind_form_mutations` (rejected).** Plain bind keeps
   `_primary_type=None`, calls `build_input(meta)` (no primary), and builds the
   pinned `{ok errors}` payload. Model bind resolves primary + object-slot
   payload. Folding would need mode flags that obscure Decision 6. Rejection
   stands.

5. **`_OPERATION_INPUT_OVERRIDE_ATTR` still spells create/update.** Different
   responsibility (op → consumer override attr name); values are not kind-map
   values. Leaving it independent is correct — not a revision gap for this item.

6. **Metaclass identity must be pinned, not left function-local.** The first
   cut of the factory returned a bare `class MetaValidatingMetaclass`, so both
   `DjangoMutationMetaclass` and `DjangoFormMutationMetaclass` reported
   `__name__ == "MetaValidatingMetaclass"` and a
   `make_meta_validating_metaclass.<locals>.MetaValidatingMetaclass`
   `__qualname__`. That is not cosmetic: it breaks module addressability,
   `repr`/introspection, and reference-based pickling of the public metaclasses
   (`pickle` resolves a class from `__module__` + `__qualname__`, which no longer
   pointed at the bound object). Resolved at the owner: the factory now takes
   keyword-only `name` / `module` and pins `__name__` / `__qualname__` /
   `__module__` on the produced class; each consumer passes its own public symbol
   and `module=__name__`. Pinned by
   `test_public_metaclasses_pin_public_identity_and_pickle` (name/qualname/module,
   `getattr(module, name) is metaclass`, `pickle` round-trip) and by the probe
   assertions in `test_make_meta_validating_metaclass_...`.

### Proof

- `uv run pytest tests/mutations/test_sets.py::test_make_meta_validating_metaclass_validates_registers_and_skips_abstract`
  plus `-k "operation or abstract or register or bind or Meta"` over
  `tests/mutations/test_sets.py`: **50 passed** (coverage gate fails on the
  subset run; expected).
- Existing Meta.operation reject tests remain the permanent guard for
  frozenset membership (`test_meta_bad_operation_raises`, form/serializer
  delete rejects).

### Outcome

Both consolidations are complete, ledgers stay disjoint, rejected candidates
remain correctly separate. One production revision followed from challenge 6:
the factory now pins the produced metaclass's `__name__` / `__qualname__` /
`__module__` to each consumer's public symbol (keyword-only `name` / `module`),
so `DjangoMutationMetaclass` / `DjangoFormMutationMetaclass` keep addressable,
introspectable, reference-picklable identities instead of a shared
function-local class.

**Status: verified.** Plan item checked.
