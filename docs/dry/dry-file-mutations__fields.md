# DRY review: `django_strawberry_framework/mutations/fields.py`

Status: verified

## System trace

`mutations/fields.py` owns the write-side root-field factory and the shared
lazy-signature machinery consumers of that idiom reuse:

1. **`DjangoMutationField(mutation_cls, ...)`** — construction-time target
   guard, per-operation GraphQL argument synthesis (`id` / `data`),
   `strawberry.lazy` payload return-ref, runtime `in_async_context()`
   sync/async dispatch into `mutation_cls.resolve_*`, and the
   `MUTATION_CLASS_MARKER` stamp `schema.py::DjangoMutationExecutionContext`
   reads for the completion-spanning write transaction.
2. **`_lazy_ref` / `build_lazy_field_signature`** — the promoted field-factory
   helpers (spec-040) that inject `inspect.Signature` + `__annotations__` with
   lazy forward-refs when the return type only materializes at phase 2.5.
3. **Duck-typed target protocol** — `_has_mutation_protocol` + own-snapshot +
   current-ledger checks (`iter_mutations` ∪ `iter_form_mutations`), so the
   model / ModelForm / plain-form / serializer flavors all pass without
   importing form bases (load-cycle guard).

Connected behavior examined:

- **Name / module seams (not owned here):**
  `mutation_cls.input_type_name(meta)` + `mutation_cls.input_module_path`.
  Model default lives on `mutations/sets.py::DjangoMutation.input_type_name`
  (delegates to `mutations/inputs.py::mutation_input_type_name`); form flavors
  override via `forms/inputs.py::form_input_type_name` + `FORMS_INPUTS_MODULE_PATH`.
  Payload return-ref always names `mutations.inputs.INPUTS_MODULE_PATH`
  (spec-038 Decision 5 namespace divergence).
- **Bind / materialize:** `mutations/sets.py::_bind_mutation` +
  `mutations/inputs.py::build_payload_type` / `materialize_mutation_input_class`
  create the classes the lazy refs resolve after finalize.
- **Auth reuse:** `auth/mutations.py::_make_auth_field` and
  `auth/queries.py` call `_lazy_ref` + `build_lazy_field_signature` (and
  `register_mutation` rides `DjangoMutationField`); no parallel lazy-signature
  spelling remains in `auth/`.
- **Transaction marker:** `schema.py` is the sole `MUTATION_CLASS_MARKER`
  consumer outside this file.
- **Tests:** `tests/mutations/test_fields.py` pins signature shapes, target
  guards (abstract / unregistered / Meta-inherit / form duck-type / serializer),
  and no-annotation schema build. Live `/graphql` mutation coverage already
  exists under `examples/fakeshop/test_query/` for the factory's consumers;
  this pass adds no new earnable line.

Baseline `git diff 95c5a836609234f8c124bf9918aa7ddac5ae4ee1 --
django_strawberry_framework/mutations/fields.py` was empty before and after
this pass.

## Verification

Searches and checks against current source (not prior DRY judgments):

- `rg 'def _input_type_name|_input_type_name\(' django_strawberry_framework/` —
  no `_input_type_name` twin remains. Field construction builds `data:` via
  `_lazy_ref(mutation_cls.input_type_name(meta), mutation_cls.input_module_path)`
  only.
- Compared that seam call to `mutations/inputs.py::mutation_input_shape(...).type_name`
  and to `DjangoMutation.input_type_name` in `sets.py`. The **field** no longer
  derives names; the model seam body still walks `editable_input_fields` and
  calls `mutation_input_type_name` (the same primitive `mutation_input_shape`
  uses for `type_name`). Whether the seam should *delegate through* the shape
  descriptor is a `sets.py` / `inputs.py` ownership question — this file is
  already the consumer, not a second derivation site.
- `rg 'Annotated\[.*strawberry.lazy|strawberry.lazy\('` — generation-time
  self-refs in filters/orders/utils input builders, and Decision-11
  `utils/inputs.py::build_lazy_input_annotation` (set validation + ledger),
  are different contracts from the field-factory `_lazy_ref` (bare name +
  module). Auth already imports this file's helpers; no second field-factory
  copy.
- Operation verb literals (`"create"` / `"update"` / `"delete"` / `"form"`)
  appear in `sets.py` (Meta validation), `permissions.py` (Django perm map),
  `resolvers.py` (pipeline branch), and here (GraphQL arg + `id=` kwarg
  gating). Compared contracts: validation set, auth action map, write
  pipeline steps, and SDL argument shape are four change axes that happen to
  share string vocabulary. This file is the true owner of **which GraphQL
  args / kwargs the field exposes**; it is not the owner of the Meta
  vocabulary or the permission/resolver maps.
- Payload name formula `f"{name}Payload"` appears at field construction
  (pre-bind lazy ref) and in `inputs.py::build_payload_type` (bind-time
  `type(...)`). Field construction cannot read `_payload_type_name` (bind
  output; documented). The formula is a one-token convention; extracting a
  helper would not remove a second policy — only wrap an f-string.
- In-file `id`/`data` gating vs `takes_id = operation != "form"`: intentionally
  asymmetric (create has no `id` GraphQL arg but passes `id=UNSET` into the
  model seam; plain `"form"` omits `id` entirely). Not one rule to collapse.

No scratch under `docs/dry/temp-tests/`: import graph + source comparison were
sufficient.

Rejected / deferred candidates:

1. **Fold field-local name derivation into `mutation_input_shape(...).type_name`.**
   Disproved for *this* file: there is no local `_input_type_name`; the factory
   already consults the overridable seam. Remaining seam-vs-shape walk
   duplication (if any) belongs to `mutations/sets.py` /
   `mutations/inputs.py` — forward to those file items / the `mutations/`
   folder pass. Do not pull sets changes into this item.
2. **Shared OPERATIONS vocabulary module across sets / permissions /
   resolvers / fields.** Disproved as a *fields.py* consolidation: the four
   sites encode different responsibilities (Meta allow-list, Django perm
   action, pipeline branch, GraphQL arg shape). Coupling them behind one
   constant table would force lockstep changes for independent axes. This
   file keeps the arg-shape literals local. Folder/project may still inventory
   the vocabulary; do not invent a shared owner from this file alone.
3. **Lift `_lazy_ref` into `utils/inputs.py` beside `build_lazy_input_annotation`.**
   Disproved: Decision-11 helper owns set validation + ledger recording; this
   helper is the field-factory forward-ref primitive already shared with auth.
   Merging would add mode flags or unused validation to one of the call sites.
4. **`payload_type_name(name) -> f"{name}Payload"` helper in `inputs.py`.**
   Rejected as over-abstraction for a trivial naming formula (`DRY.md`: do not
   optimize for fewer lines). Drift is caught by schema-build tests. Revisit
   only if a third independent spelling appears.
5. **In-file helper unifying signature arg gates with `takes_id`.** Rejected:
   the two gates are deliberately different (GraphQL args vs resolver kwargs);
   a combined helper would need flags for the asymmetry it exists to express.

## Opportunities

None — every candidate either is already single-sourced through seams this
file correctly consumes (`input_type_name` / `input_module_path` / `resolve_*`),
is shared machinery this file already owns for auth (`_lazy_ref` /
`build_lazy_field_signature` / `MUTATION_CLASS_MARKER`), or encodes a distinct
contract that must not collapse (operation vocabulary across Meta / perms /
pipeline / SDL args; pre-bind payload name vs bind-time class construction;
signature `id` vs runtime `takes_id`).

## Judgment

Well-proved zero-edit review. `mutations/fields.py` is the single owner of
write-field construction and the promoted lazy-signature helpers; input naming
and payload materialization live behind seams and bind outputs it does not
re-implement. Strongest deferred items (seam body vs `mutation_input_shape`,
package-wide operation vocabulary) are correctly out of this file's ownership.
Item-scoped diff empty. Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced `mutations/fields.py` end-to-end (target guards → signature synthesis →
`_resolve` dispatch → marker stamp) and the connected seams/consumers
(`sets.py::input_type_name`, `inputs.py::build_payload_type`,
`auth/mutations.py::_make_auth_field`, `auth/queries.py`,
`schema.py::DjangoMutationExecutionContext`, `tests/mutations/test_fields.py`).

**Scoped diff:** `git diff 95c5a836609234f8c124bf9918aa7ddac5ae4ee1 --
django_strawberry_framework/mutations/fields.py` is empty. Zero-edit claim holds.

**Challenged rejected / deferred candidates:**

1. **`_input_type_name` twin** — Confirmed absent from this file (`rg` finds no
   `_input_type_name` here). Construction uses only
   `mutation_cls.input_type_name(meta)` + `input_module_path`. Remaining
   seam-body vs `mutation_input_shape(...).type_name` walk duplication (if any)
   is owned by `sets.py` / `inputs.py`, not a fields consolidation.
2. **Shared OPERATIONS table** — Confirmed four distinct change axes:
   `sets.py::_VALID_OPERATIONS` (Meta allow-list),
   `mutations/permissions.py::_OPERATION_PERMISSION_ACTION` (Django perm
   action map — Worker 1's "permissions.py" cite is this module, not the
   top-level cascade helper), `resolvers.py` pipeline branches, and this
   file's GraphQL arg / `takes_id` gating. Coupling them would force lockstep
   on independent policies. Folder/project may still inventory vocabulary;
   no fields-owned shared constant is warranted.
3. **Lift `_lazy_ref` beside `build_lazy_input_annotation`** — Confirmed
   different contracts: Decision-11 helper owns set validation + ledger;
   `_lazy_ref` is bare name+module for field factories. Auth already imports
   from here; filters/orders generation-time self-refs stay local. Merge would
   need mode flags.
4. **`payload_type_name` helper** — Confirmed only two spellings of the
   one-token `f"{name}Payload"` formula (pre-bind lazy return ref here;
   bind-time `type(...)` in `inputs.py::build_payload_type`). Field
   construction cannot read `_payload_type_name`. Over-abstraction rejected.
5. **Unify signature `id` gates with `takes_id`** — Confirmed intentional
   asymmetry: GraphQL args gate on `("update","delete")` / `!= "delete"`;
   resolver kwargs gate on `!= "form"` (create still passes `id=UNSET`).
   Not one rule.

**Missed consolidations searched:** no second field-factory lazy-signature
spelling in `auth/`; `connection.py` signature injection is a different
sidecar-arg contract; `rest_framework` `_input_type_name` is a bind-time
cache attribute, not a twin of the deleted fields helper; `MUTATION_CLASS_MARKER`
has a single external reader in `schema.py`.

**Disposition:** All material candidates disposed. No revision required.
Status → verified; plan item checked.
