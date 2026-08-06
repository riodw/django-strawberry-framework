# DRY review: `django_strawberry_framework/rest_framework/hook_context.py`

Status: verified

## System trace

`hook_context.py` owns exactly two public frozen value types for the serializer
hardening pass:

- `SerializerHookContext(operation, write_alias, instance_pk)` — the immutable
  substitute for the live located model instance that every consumer serializer
  hook receives (`get_serializer_kwargs` / `get_serializer_injected_data` /
  `get_serializer_save_kwargs`).
- `UploadMetadata(name, size, content_type)` — the immutable stand-in for an
  uploaded file inside the frozen hook data view (stateful streams stay on
  framework-built serializer `data`).

Construction / consumption (this file defines shapes only; runtime ownership
stays in the write pipeline):

- **Constructs `SerializerHookContext`:**
  `rest_framework/resolvers.py` write step (pins `operation` from mutation Meta,
  `write_alias` from the active write pipeline, `instance_pk` from
  `pipeline.authorized_pk` / locate fallback) and passes that one object into
  `_injected_serializer_data`, `_merged_serializer_kwargs`, and the save-kwargs
  hook.
- **Constructs `UploadMetadata`:** private `_upload_metadata` inside
  `rest_framework/resolvers.py`, invoked only by `_frozen_hook_view` when a leaf
  is a file-like upload.
- **Documents / receives the types:** `rest_framework/sets.py` hook method
  signatures (annotated `Any`; docstrings name both types). Defaults ignore the
  context; overrides may consult it.
- **Public soft-export:** package `__init__.py` lazy names
  `SerializerHookContext` / `UploadMetadata` (DRF package gate), even though this
  module itself has no DRF import.
- **Consumers / proof:** `tests/rest_framework/test_resolvers.py` (`_hook_ctx`,
  freeze + upload cases); example library mutations under
  `examples/fakeshop/apps/library/schema.py` that read
  `hook_context.write_alias` / `instance_pk`.

Connected surfaces examined and kept distinct:

- `utils/write_transaction.py::WriteAliasContext` — mutable pipeline state
  (`alias`, `authorized_pk`, `target_state`, phase flags). The hook context
  projects a frozen public slice (`write_alias` + `instance_pk`); it does not
  re-own pipeline storage.
- Forms flavor (`forms/sets.py`, `forms/resolvers.py`) — still passes live
  `instance` and a `files=` split into `get_form_kwargs` / `get_form`. No form
  hook-context or upload-metadata types exist; the forms contract intentionally
  differs (Django form binding vs DRF serializer hardening).
- Model / plain mutation write paths — compare saved results to
  `authorized_pk` but never expose a frozen consumer hook context of this shape.
- `scalars.Upload` — GraphQL wire scalar for upload values; different lifecycle
  phase from the post-decode hook descriptor.

Item-scoped baseline
(`9b5bc4a00e42750575096aea0adcdf3486537225`) diff for the target is empty; no
production edits in this pass.

## Verification

Searches (package-wide): `SerializerHookContext`, `UploadMetadata`,
`hook_context`, `instance_pk`, `authorized_pk`, `@dataclass(frozen=True)`,
upload `name`/`size`/`content_type` triples, forms `get_form_*` / `files=`,
mutations write-pipeline pk snapshots.

Findings checked by contract (inputs, mutability, consumers, change axis):

1. **Fold this module into `resolvers.py` (or reverse).** Same names appear
   densely in resolvers, but the module's job is the public frozen contract
   (soft-exported, DRF-free, slots + frozen). Resolvers own freeze/merge/
   construction policy. Folding would either bury the public types inside the
   largest runtime module or pull freeze machinery into a value-type file.
   Rejected: ownership split is intentional and already single-sited per role.
2. **Unify with `WriteAliasContext.authorized_pk` / `alias`.** Both carry a pk
   snapshot and an alias string, but one is mutable internal pipeline state with
   locks/phases/target drift; the other is a frozen, consumer-facing triple that
   also carries `operation`. Hooks must not receive the live pipeline object.
   Rejected: projection from pipeline → hook context is the hardening boundary,
   not duplicated storage of the same type.
3. **Invent / share a forms `FormHookContext` + upload freeze.** Superficial
   symmetry with serializer hooks; forms still bind `instance=` and read uploads
   from `files=`. Consolidating would invent a product hardening change for
   forms, not remove a shared rule that already exists twice. Rejected: distinct
   framework contracts.
4. **Move `_upload_metadata` onto `UploadMetadata` as a factory.** Only one
   builder exists (resolvers). Fail-soft `.size` / duck-typing is freeze-pipeline
   machinery; the dataclass is the public value shape. Moving it would not
   eliminate a second site. Rejected: no duplicated construction.
5. **Treat `scalars.Upload` as the same knowledge as `UploadMetadata`.** Wire
   scalar vs post-decode immutable descriptor for hooks. Rejected: different
   phases and consumers.
6. **Type `sets.py` hooks as `SerializerHookContext` instead of `Any`.** Typing
   polish / import-edge choice, not a repeated rule with two implementations.
   Left as a deferred non-DRY note (below).

No scratch experiment required: every construction site and consumer is
reachable by static trace; no second body of either dataclass exists.

## Opportunities

None — the file is already the single owner of the two frozen public value
types; construction and freeze policy live once in `rest_framework/resolvers.py`;
pipeline pk/alias state lives once in `WriteAliasContext`; forms and model
mutations intentionally use different hook contracts. Apparent similarity is
projection across a hardening boundary, not duplicated responsibility.

## Judgment

Zero-edit. `hook_context.py` is a narrow, correctly placed public contract
module. System-wide search found no second implementation of either shape that
should change with this file. Strongest lookalikes (pipeline `authorized_pk`,
forms live `instance`/`files=`, `Upload` scalar) fail the shared-contract test.

### Deferred (non-blocking, not DRY consolidations)

- `rest_framework/sets.py` documents `SerializerHookContext` /
  `UploadMetadata` but annotates `hook_context: Any` (avoids a load-time edge
  to this module). Revisit only if typed public hooks become a product goal —
  not a duplicated-rule fix.
- Forms flavor remains unhardened relative to serializer hooks; that is a
  product/security design question for a future spec, not a DRY merge of an
  existing shared owner.

### Scoped diff summary

- Target `hook_context.py`: unchanged vs item baseline
  `9b5bc4a00e42750575096aea0adcdf3486537225`.
- Artifact created: `docs/dry/dry-file-rest_framework__hook_context.md`.
- No `.py` edits; no ruff run; no pytest (none deferred for production changes).
- Plan checkbox left for Worker 2.
- Concurrent dirty files under `docs/dry/` and elsewhere left untouched.

## Independent verification (Worker 2)

Outcome: **verified** (zero-edit claim holds).

Scoped diff vs `9b5bc4a00e42750575096aea0adcdf3486537225` for
`django_strawberry_framework/rest_framework/hook_context.py` is empty.

Independent re-trace (source, not artifact trust):

- **Shapes only here.** Two frozen slotted dataclasses; no construction helpers,
  no freeze walk, no pipeline I/O. Sole production constructors:
  `SerializerHookContext(...)` once in `rest_framework/resolvers.py` write step
  (from `_mutation_meta.operation`, `pipeline.alias`, `pipeline.authorized_pk` /
  locate fallback); `UploadMetadata(...)` only via private `_upload_metadata`,
  called only from `_frozen_hook_view`'s file leaf. Package soft-export of both
  names in `__init__.py` `_DRF_SOFT_EXPORTS` confirmed; module itself imports no
  DRF.
- **Consumers.** `sets.py` three hooks take `hook_context: Any` and document
  both types; defaults `del` the arg. Library example mutations read
  `hook_context.write_alias` / `instance_pk`. Tests construct via `_hook_ctx` /
  assert `_upload_metadata` / freeze upload leaves — proof of contract, not a
  second owner.
- **Rejected #1 fold into resolvers.** Resolvers already own freeze/merge/
  construction; folding would bury the soft-exported public types inside the
  runtime module or drag freeze machinery into a value-type file. Ownership
  split is single-sited per role — keep.
- **Rejected #2 unify with `WriteAliasContext`.** `WriteAliasContext` is mutable
  pipeline state (`alias`, `authorized_pk`, `target_state`, phase flags/locks).
  Hook context is a frozen consumer triple that also carries `operation`. Passing
  the live pipeline object into hooks would erase the hardening boundary.
  Projection ≠ duplicated storage.
- **Rejected #3 invent forms `FormHookContext`.** `forms/sets.py` /
  `forms/resolvers.py` still pass live `instance=` and split uploads into
  `files=`. No parallel frozen types exist; inventing them would be a product
  hardening change, not removal of a rule already stated twice.
- **Rejected #4 move `_upload_metadata` onto the dataclass.** One builder, one
  call site; fail-soft `.size` / duck-typing is freeze-pipeline policy. No
  second construction site to eliminate.
- **Rejected #5 equate `scalars.Upload` with `UploadMetadata`.** `scalars.Upload`
  is a Strawberry wire `NewType` re-export; `UploadMetadata` is the post-decode
  immutable hook descriptor. Different phase and consumers.
- **Deferred `Any` annotations.** Typing polish / import-edge choice on
  `sets.py`; not two implementations of one rule. Correctly non-blocking.
- **Missed consolidations searched.** Package-wide only one production site each
  for both constructors. Other `@dataclass(frozen=True)` types are unrelated
  domains. `extensions/resource_policy.py::_charge_upload` also reads upload
  `.size`, but for request budget enforcement (fail-closed), not hook descriptors
  (fail-soft `None`) — distinct contract and change axis; not DRY merge fodder.

No revision blockers. Plan checkbox marked `[x]`. No production edits; concurrent
dirty work preserved; no commit; no pytest.
