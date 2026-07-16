# DRY review: folder `django_strawberry_framework/rest_framework/`

Status: verified

## System trace

`rest_framework/` is the DRF-`ModelSerializer` write component (spec-039): schema-time
serializer fields become GraphQL mutation inputs, bind through phase 2.5 on the
shared `DjangoMutation` metaclass, and run decode → construct → `is_valid()` →
save → payload under `run_write_pipeline_sync`. Soft-dep gated so a DRF-absent
build never imports DRF-importing siblings.

Folder shape after the five verified file reviews (+ evidence-only
`hook_context.py`, present on disk after plan freeze):

- `__init__.py` — `require_drf()` + import-time gate; install hint single-sited
  here.
- `serializer_converter.py` — `serializers.Field`-keyed fail-loud conversion +
  per-field `resolve_serializer_field` / source axis / choice-enum cache /
  nested detect helpers.
- `inputs.py` — Slice-1 generators, descriptor identity, nested opt-in
  recursion, fingerprint, writable/runtime field helpers, materialize + shape
  cache (clears `rest_framework.input_namespace` / `rest_framework.shape_cache`).
- `sets.py` — `SerializerMutation` Meta/bind/hooks; rides `DjangoMutation` +
  `bind_mutations()`; schema-time nested + source-ownership walkers.
- `resolvers.py` — serializer write runtime on the shared skeleton; freeze /
  merge / agreement / ownership / intent / DRF error flatten.
- `hook_context.py` — frozen `SerializerHookContext` + `UploadMetadata` (no
  DRF import; still behind the package gate as product boundary).

Connected behavior re-traced for this folder pass (not inherited as proven):
`forms/converter.py` / `forms/inputs.py` / `forms/sets.py` / `forms/resolvers.py`
(sibling Form/ModelForm flavor over the same `convert_with_mro` /
`FieldConversionBase` / `InputFieldSpec` / `run_write_pipeline_sync` /
`build_and_stash_input` / `construction_kwargs` / `resolver_seams` spine);
`mutations/sets.py` / `mutations/resolvers.py` (metaclass, write skeleton,
Meta helpers); `types/converters.py` (column-backed scalar / enum reuse);
`utils/inputs.py` / `utils/converters.py` / `utils/write_values.py`; root
`__getattr__` soft exports; live fakeshop serializer mutations under
`examples/fakeshop/test_query/`; package `tests/rest_framework/`.

Folder-level axes examined: duplicated policy across converter ↔ inputs ↔
sets ↔ resolvers; state ownership (input namespace, shape cache, choice enums);
competing helpers; public export flavor; lifecycle clears; assignment-named
deferrals from file passes (especially nested/`backing_model_field`
`source_attrs`); converter seams vs forms/types.

## Verification

- ITEM_BASELINE `7cdcd641b7d743c58faba872ccf8c9c17ebacf03`: item-scoped
  `git diff … -- django_strawberry_framework/rest_framework/` empty at pass
  start (folder matched baseline). Concurrent dirt vs HEAD outside this item
  left untouched. Plan checkbox not edited.
- Re-read all six modules end-to-end. Grepped package for `source_attrs`,
  `backing_model_field`, `require_one_segment` / dotted-source raises,
  `raise_writable_source_ownership_errors`, `_write_surface_specs`,
  `is_nested_serializer_field`, `register_subsystem_clear` owners under
  `rest_framework.`, and form/types converter parallels.
- Optional audit (`export_dry_review.py audit --target …/rest_framework
  --stdout`) for orientation only.
- Independently re-traced file-pass deferrals from source. Did not concatenate
  file artifacts; used deferred labels only as search flags.
- Focused proof (`--no-cov`, 4 passed):
  `test_dotted_source_on_model_column_field_raises`,
  `test_star_source_on_model_column_field_raises`,
  `test_require_one_segment_source_rejects_star_and_dotted`,
  `test_nested_dotted_source_rejected`. Schema-time configuration errors —
  not earnable via live `/graphql`.
- Ruff format + check on edited paths clean. No full pytest.

## Opportunities

### 1. One-segment `source` policy at `require_one_segment_source` (accepted)

- **Repeated responsibility:** reject a bound serializer field whose
  `source_attrs` is not exactly one segment (`source='*'` → `[]`, dotted →
  multi-element) whenever the schema path needs a single write-back attribute.
- **Sites:** `serializer_converter.py::backing_model_field` (model-column
  resolve); `inputs.py::_resolve_nested_field` (opted-in nested write). File
  review of the converter explicitly deferred this to the folder pass.
- **Evidence:** identical `getattr(field, "source_attrs", None)` /
  `len(...) != 1` predicate; both docs claim the same Decision-7 / rev6 #17
  fail-loud policy; messages share one skeleton and differ only in nouns
  (column vs nested attribute). Nested path cannot call `backing_model_field`
  (no model column) but must obey the same detection.
- **Owner:** `serializer_converter.py::require_one_segment_source` (source-axis
  owner beside `backing_model_field`).
- **Consolidation:** extract the raise helper with `field_label` /
  `must_map_to` call-site nouns; migrate both sites; keep byte-stable wording.
- **Proof:** helper unit test + existing column / nested dotted-source tests
  (package-internal; bind-time config).
- **Risks / non-goals:** do not force nested through `backing_model_field`; do
  not change reverse-map source normalization
  (`source if source != declared else None`); do not reject dotted sources on
  model-less column-less scalars (still out of the one-segment write-back
  paths).

### Rejected / deferred (re-proved)

1. **Merge serializer ↔ form scalar converter tables / fallthrough factories.**
   Distinct key spaces (`serializers.Field` vs `forms.Field`) and capability
   matrices; shared mechanics already in `convert_with_mro` +
   `FieldConversionBase` + kinds. Reject.

2. **Merge `serializer_only_relation_annotation` ↔
   `forms/inputs._model_less_relation_annotation` (or extract narrow
   `relation_id_scalar`).** M3-required primary vs form raw-pk fallback,
   id-like-suffix vs always `_id`, queryset discovery differ. Narrow extract
   still needs a forms-clean migration of every form site — project pass when
   forms are clean. Defer.

3. **Move `resolve_serializer_field` into `inputs.py` (mirror forms ownership).**
   Reshuffle, not a second implementation; resolve is tightly coupled to
   source / type-override / choice-enum owned by the converter. Ownership is
   clear. Reject.

4. **Force serializer `build_input` through `cached_build_input`.** Wrong key
   timing (descriptor only known post-build; P1.7). Reject.

5. **Unify form / serializer Meta matrices, construction waiver, or nested
   validators.** Opposite Meta keys, `injected_fields` vs form hook waiver,
   DRF write-method override gate has no form twin. Mode flags. Reject.

6. **Fold schema ↔ runtime source-ownership walkers.** Same raise owner already
   (`raise_writable_source_ownership_errors`); walkers differ by phase (field_map
   + NestedSerializerConfig vs live serializer + bind specs). Reject merge of
   walkers.

7. **Generic nested walker for agreement / scope / intent / attest.** Same
   tree shape, distinct per-node rules; helper would obscure ownership.
   Reject.

8. **Triple clear owners (`rest_framework.input_namespace` /
   `rest_framework.shape_cache` / `rest_framework.choice_enums`).** Intentional
   lifecycle roles (lazy ledger + parked globals; per-pass shape cache;
   serializer-only enum name cache). Matches forms/mutations pattern. Reject.

9. **Fold `hook_context.py` into resolvers (or reverse).** Frozen public hook
   types vs runtime freeze/merge machinery; correct separation. Reject.

10. **Promote id-like-suffix / `serializer_field_description` to `utils`.** No
    second consumer outside this folder. Reject.

11. **Relocate `writable_*` / `runtime_validated_data_fields` out of `inputs.py`.**
    Reorganization, not duplicated responsibility; sets/resolvers correctly
    import the schema-time field-basis owner. Reject.

12. **Public flavor.** Root soft-exports `SerializerMutation`,
    `NestedSerializerConfig`, `register_serializer_field_converter`, etc.
    through `__getattr__` + `require_drf`; package `__init__` is the gate only
    (no `__all__` consumer bases). Soft-dep posture intentional vs forms'
    hard import. Consistent.

## Judgment

Folder ownership is layered correctly after the verified file passes:
converter owns DRF-field conversion + source-axis resolve; inputs owns
generation / fingerprint / nested recursion / field-basis helpers; sets owns
Meta/bind/hooks; resolvers own runtime on the shared skeleton; hook_context
owns frozen hook types; `__init__` owns the soft-dep gate. The only
folder-visible unfinished wiring was the deferred one-segment `source`
predicate split across converter and nested input resolve — now one owner.
Remaining form/types parallels and walker shape lookalikes are intentional
flavor or phase boundaries. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:**
  `serializer_converter.py::require_one_segment_source`.
- **Migrated sources / callers / tests:**
  - `backing_model_field` → calls helper with column nouns
  - `inputs.py::_resolve_nested_field` → calls helper with nested nouns
  - `tests/rest_framework/test_converter.py::test_require_one_segment_source_rejects_star_and_dotted`
    (new); existing dotted/star column + nested tests remain the end-to-end
    proofs
- **Kept separate:** reverse-map source normalization; model-less column-less
  dotted sources outside the write-back paths; schema vs runtime ownership
  walkers; form/types converter tables; resolve ownership in converter;
  `cached_build_input` timing; Meta matrices; clear owners; hook_context
  module.
- **Validation:** 4 focused tests passed (`--no-cov`); `uv run ruff format` +
  `ruff check --fix` on edited paths. No full pytest.
- **Changelog:** no — internal ownership completion; public error substrings
  (`dotted source`) unchanged.
- **Concurrent paths preserved:** only this folder's converter/inputs + the
  converter test + this artifact. Plan checkbox not touched. Other dirty
  packages left alone.

## Independent verification (Worker 2)

Re-traced folder ownership end-to-end (gate → converter/source axis → inputs
generation/nested → sets Meta/bind → resolvers write runtime → hook_context
frozen types). Challenged the accepted consolidation and the twelve rejected /
deferred folder findings against live source, not the file artifacts.

**Accepted consolidation — disposed verified**

1. `require_one_segment_source` is the sole `source_attrs` / `len != 1`
   predicate under `django_strawberry_framework/` (grep). Both write-back
   schema paths call it: `backing_model_field` (column nouns) and
   `_resolve_nested_field` (nested nouns). Nested correctly does not route
   through `backing_model_field`. Scratch proved byte-stable messages for both
   noun pairs; unbound (`source_attrs is None`) still no-ops. Focused proof
   re-ran green (`--no-cov`, 4 passed): column dotted/star, helper unit, nested
   dotted via `build_serializer_input_class`. Ownership is clearer than the
   prior twin predicates; site nouns stay at call sites without a mode flag.

**Rejected / deferred — disposed (re-proved separate)**

Converter↔form tables, relation-annotation project deferral, resolve ownership
in converter, `cached_build_input` timing, Meta/waiver/nested-validator
matrices, schema↔runtime ownership walkers (shared raise owner already),
generic nested walkers, triple clear owners, hook_context separation,
utils promotion of id-suffix/description, relocating writable helpers, and
soft-dep public flavor — each still differs by key space, phase, Meta contract,
or consumer count. No missed second one-segment detector in sets/resolvers
(ownership walkers compare sources; they do not re-implement the segment
count). `hook_context.py` remains evidence-only (not a plan row).

**Item scope / concurrent WIP**

ITEM_BASELINE-scoped diff is only converter + inputs +
`test_require_one_segment_source_rejects_star_and_dotted`. Working-tree dirt on
`sets.py` / `resolvers.py` / `test_inputs.py` / `test_resolvers.py` is empty vs
baseline (pre-existing concurrent WIP) and was not absorbed. Broader package
dirt outside this item left untouched. No commit. No full pytest.

Verdict: consolidation complete; folder ready to close.

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
