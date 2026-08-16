# DRY review: folder `django_strawberry_framework/rest_framework/`

Status: verified

## System trace

`rest_framework/` is the DRF-`ModelSerializer` write component (spec-039):
schema-time serializer fields become GraphQL mutation inputs, bind through
phase 2.5 on the shared `DjangoMutation` metaclass, and run decode →
construct → `is_valid()` → save → payload under `run_write_pipeline_sync`.
Soft-dep gated so a DRF-absent build never imports DRF-importing siblings.

Present-day folder (~5930 lines; fresh integration of current source, not a
recap of file artifacts):

| Phase | Owner | Symbols |
| --- | --- | --- |
| Soft DRF gate | `__init__.py` | `require_drf` |
| Hook freeze types | `hook_context.py` | `SerializerHookContext`, `UploadMetadata` |
| Field→annotation / one-segment `source` / choice enums | `serializer_converter.py` | `convert_serializer_field`, `resolve_serializer_field`, `require_one_segment_source`, `backing_model_field`, `clear_serializer_choice_enums` |
| Writable basis / ownership raise / fingerprint / nested input build / materialize / shape cache | `inputs.py` | `writable_*`, `raise_writable_source_ownership_errors`, `serializer_schema_fingerprint`, `NestedSerializerConfig`, `build_serializer_input_class`, `dedupe_serializer_input_shape`, `materialize_serializer_input_class` |
| Meta / bind / schema ownership walk / seams | `sets.py` | `SerializerMutation`, `_validate_serializer_nested_fields`, `_assert_schema_source_ownership`, `_serializer_input_shape_for` → `dedupe_serializer_input_shape`, `build_and_stash_input`, `resolver_seams` |
| Decode / construct / validate / save / payload | `resolvers.py` | `_decode_*`, `_frozen_hook_view`, agreement / runtime ownership / intent / attest, `run_write_pipeline_sync` |

Connected evidence (not rewritten unless this folder owns the rule):
`forms/` (verified sibling flavor), `mutations/sets.py` /
`mutations/resolvers.py` (shared substrate: `build_and_stash_input`,
`construction_kwargs`, `resolver_seams`, `run_write_pipeline_sync`),
`utils/inputs.py` / `utils/write_values.py`, root `__getattr__` soft exports,
`tests/rest_framework/`, live fakeshop serializer mutations.

Folder axes: policy split across converter ↔ inputs ↔ sets ↔ resolvers;
state ownership (three clears); competing helpers; public soft-dep flavor;
lifecycle work at several phases; vs forms/mutations when RF is true owner.

## Verification

- ITEM_BASELINE `77f9ec646f71da07fef6f7243e922d43524579ba`: folder matched
  baseline at pass start (empty item-scoped diff). Concurrent dirt outside
  this item left untouched. Plan checkbox not edited.
- Re-read all six modules end-to-end. Grepped
  `require_one_segment_source` / `source_attrs`, ownership raise + schema vs
  runtime walkers, nested validators, shape-cache writers, clears,
  `cached_build_input` usage, form/mutation parallels, error flatten,
  relation-annotation twins.
- Did not seed findings from the prior verified artifact; used it only to
  preserve the audit trail under Iterations.
- Confirmed sole `source_attrs` / `len != 1` predicate remains
  `require_one_segment_source` (prior folder consolidation still holds).
- Confirmed sole ownership raise remains
  `raise_writable_source_ownership_errors`; schema/runtime walkers correctly
  differ by tree (NestedSerializerConfig vs live serializer + client data).
- Found post-build shape-cache get-or-store duplicated across
  `sets._serializer_input_shape_for` (poking private
  `_serializer_shape_build_cache`) and `inputs._dedupe_and_materialize_nested`
  — same key/value contract, cache owned by inputs.
- Ruff format + check on edited paths clean. No pytest (deferred:
  `test_dedupe_serializer_input_shape_is_sole_cache_protocol`,
  `test_identical_nested_shape_dedupes_to_one_class`,
  `test_build_input_runs_required_guard_per_declaration`).

## Opportunities

### 1. Post-build shape-cache protocol at `dedupe_serializer_input_shape` (accepted)

- **Repeated responsibility:** descriptor-keyed get-or-store on
  `_serializer_shape_build_cache` after `build_serializer_input_class`.
- **Sites:** `sets._serializer_input_shape_for` (top-level bind);
  `inputs._dedupe_and_materialize_nested` (nested opt-in; then materializes).
- **Evidence:** identical `cache.get(shape.cache_key)` / store `(cls, shape)`
  protocol; cache and clear owner already live in `inputs.py`
  (`rest_framework.shape_cache`); sets was reaching into a private ledger.
  Materialize timing correctly differs (nested always; top via
  `build_and_stash_input`) so a shared dedupe+materialize helper would need a
  mode flag — reject that shape; share get-or-store only.
- **Owner:** `inputs.py::dedupe_serializer_input_shape`.
- **Consolidation:** extract helper; both sites call it; sets stops importing
  `_serializer_shape_build_cache`.
- **Proof:** new
  `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`;
  existing nested + guard-per-declaration tests remain end-to-end proofs.
- **Risks / non-goals:** do not force serializer through
  `mutations.sets.cached_build_input` (pre-build key timing still wrong);
  do not merge materialize into the helper.

### Rejected / deferred (re-proved this pass)

1. **Merge schema + runtime ownership walkers.** Raise already single-sited.
   Walkers take different trees (config vs live+data); runtime exists because
   schema cannot see `get_fields()` dynamism. Reject.

2. **Fold `_validate_nested_config_keys` into
   `_validate_serializer_nested_fields`.** Different timing (every build depth
   vs class Meta), field set (effective vs full map), and only sets owns the
   create/update override gate. Reject.

3. **Force serializer `build_input` through `cached_build_input`.** Descriptor
   key only known post-build; would double-build. Reject. (Note:
   `mutations.sets.cached_build_input` docstring still says form+serializer
   "share" it — docstring drift on mutations substrate; project/mutations
   cleanup, not an RF consolidation.)

4. **Merge converter ↔ form scalar tables / resolve ownership.** Distinct key
   spaces and capability matrices; shared mechanics already in
   `convert_with_mro` / `FieldConversionBase`. Reject.

5. **Merge `serializer_only_relation_annotation` ↔ form
   `_model_less_relation_annotation`.** M3-required primary vs form raw-pk
   fallback differ. Defer to project pass when forms stay clean.

6. **Unify Meta matrices / construction waiver / nested validators with
   forms.** Opposite Meta keys; `injected_fields` vs form hook waiver; DRF
   write-method override has no form twin. Reject.

7. **Generic nested walker for agreement / scope / intent / attest.** Same
   tree shape, distinct per-node rules. Reject.

8. **Triple clears (`input_namespace` / `shape_cache` / `choice_enums`).**
   Intentional lifecycle roles. Reject.

9. **Fold `hook_context.py` into resolvers.** Frozen public types vs runtime
   freeze/merge machinery. Reject.

10. **Share decode / error flatten with forms.** Destination policy differs;
    spine already in `utils.write_values`. Reject.

11. **Treat `_resolve_nested_field` vs `resolve_serializer_field` as competing
    layers.** Opt-in recursive build vs fail-loud default. Reject.

12. **Public soft-dep flavor.** Gate-only package `__init__`; soft exports via
    root `__getattr__` + `require_drf`. Intentional vs forms' hard import.
    Consistent.

## Judgment

Folder ownership is layered correctly. Prior one-segment `source` ownership
still holds. The only fresh folder-visible unfinished wiring was the
post-build shape-cache protocol split across sets (private-cache poke) and
inputs (nested dedupe) — now one owner beside the cache. Remaining
form/mutations parallels correctly live above this folder or are intentional
flavor/phase boundaries. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** `inputs.py::dedupe_serializer_input_shape`.
- **Migrated sources / callers / tests:**
  - `_dedupe_and_materialize_nested` → calls helper then materializes
  - `sets._serializer_input_shape_for` → calls helper; drops
    `_serializer_shape_build_cache` import
  - `SerializerMutation.build_input` docstring updated to name the helper
  - `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`
    (new)
- **Kept separate:** `cached_build_input` timing; materialize at call sites;
  schema vs runtime ownership walkers; nested Meta vs build-depth validators;
  form/types converter tables; triple clears; hook_context; soft-dep flavor.
- **Deferred finding:** `mutations.sets.cached_build_input` docstring claims
  serializer shares the helper; present-day serializer deliberately does not
  (post-build key). Out of RF remit.
- **Validation:** sole `_serializer_shape_build_cache[` writer is the helper
  (grep). `uv run ruff format` + `ruff check --fix` clean on edited paths.
  Pytest deferred (maintainer gate).
- **Changelog:** no — internal ownership; no public API change.
- **Scoped diff statement:** item-scoped changes are
  `rest_framework/inputs.py`, `rest_framework/sets.py`,
  `tests/rest_framework/test_inputs.py`, and this artifact. Plan checkbox not
  touched. Concurrent paths left alone. No commit.

## Independent verification (Worker 2)

Re-traced `rest_framework/` as one component (gate → converter/source →
inputs generation/nested/cache → sets Meta/bind → resolvers runtime →
hook_context). Challenged the accepted cache-protocol consolidation and the
twelve rejected / deferred findings against live source + ITEM_BASELINE-scoped
diff (`77f9ec646f71da07fef6f7243e922d43524579ba`). Did not seed from prior
file artifacts beyond the shared folder artifact.

**Accepted consolidation — disposed verified**

1. `inputs.dedupe_serializer_input_shape` is the sole production writer of
   `_serializer_shape_build_cache[` (grep under package + tests: only the
   helper writes; tests assert). Callers:
   - `sets._serializer_input_shape_for` (top-level bind / `input_type_name`)
   - `inputs._dedupe_and_materialize_nested` (nested opt-in; then
     `materialize_serializer_input_class`)
   `sets` no longer imports `_serializer_shape_build_cache`. Materialize stays
   at call sites (nested always; top via `build_and_stash_input`) — shared
   get-or-store without a mode flag is the right boundary. New
   `test_dedupe_serializer_input_shape_is_sole_cache_protocol` encodes the
   protocol; existing nested-dedupe + guard-per-declaration tests remain
   end-to-end proofs (pytest deferred). Ownership is clearer than the prior
   twin inline get-or-store with sets poking a private inputs ledger.

**Rejected / deferred — disposed (re-proved separate)**

1. Schema vs runtime ownership walkers: both raise through
   `raise_writable_source_ownership_errors`; trees differ
   (`NestedSerializerConfig` + schema field_map vs live serializer + client
   data / nested specs). Runtime needed for `get_fields()` dynamism. Reject.
2. `_validate_nested_config_keys` vs `_validate_serializer_nested_fields`:
   every build depth / effective set vs class Meta / full map + create/update
   override gate only in sets. Reject.
3. Force serializer through `mutations.sets.cached_build_input`: pre-build key
   vs post-build `SerializerInputShape`; would double-build. Docstring drift
   on `cached_build_input` ("form + serializer share") is mutations/project
   cleanup, not RF. Reject / defer as claimed.
4–6. Converter↔form tables, relation-annotation twins
   (`serializer_only_relation_annotation` ↔ `_model_less_relation_annotation`:
   M3-required primary vs form raw-pk fallback), Meta/waiver matrices — flavor
   / phase boundaries. Relation twin stays project-deferred.
7–12. Generic nested walkers, triple clears, `hook_context` freeze types,
   decode/error-flatten destination policy, `_resolve_nested_field` vs
   `resolve_serializer_field` (opt-in vs fail-loud), soft-dep public flavor —
   each still differs by contract or lifecycle role.

**Missed consolidations / bypasses**

No second shape-cache writer or private-cache poke. Production
`build_serializer_input_class` callers that must share GraphQL type identity
route through the helper (top via `_serializer_input_shape_for`; nested via
`_dedupe_and_materialize_nested`). Isolated `build_serializer_inputs` is a
dual create/partial test/convenience builder and correctly does not own bind
dedupe. Prior one-segment `require_one_segment_source` remains sole
`source_attrs` / `len != 1` predicate.

**Item scope / concurrent WIP**

ITEM_BASELINE-scoped paths are only `rest_framework/inputs.py`,
`rest_framework/sets.py`, `tests/rest_framework/test_inputs.py`, and this
artifact. Broader working-tree dirt (other packages; plan checkboxes for
auth/mutations/optimizer) left untouched except marking this folder item
`[x]`. No commit. No pytest.

Verdict: consolidation complete; folder ready to close.

## Iterations

### Prior pass (verified) — one-segment `source` consolidation

Status was `verified` after Worker 2; plan checkbox remained OPEN (reason for
this fresh folder pass). Summary only; full disposition preserved below.

**Accepted then:** `serializer_converter.require_one_segment_source` as the
sole `source_attrs` / `len != 1` predicate; call sites
`backing_model_field` + `inputs._resolve_nested_field`. Re-confirmed still
sole predicate on this fresh pass.

**Rejected then (still hold):** converter↔form tables; relation-annotation
project deferral; resolve ownership in converter; `cached_build_input`
timing; Meta/waiver matrices; schema↔runtime ownership walkers; generic
nested walkers; triple clears; hook_context separation; utils promotion of
id-suffix/description; relocating writable helpers; soft-dep public flavor.

#### Prior System trace (abridged)

`rest_framework/` DRF-`ModelSerializer` write component. Six modules:
`__init__` gate, `serializer_converter`, `inputs`, `sets`, `resolvers`,
`hook_context`. Connected forms/mutations/utils as evidence.

#### Prior Opportunities (accepted)

One-segment `source` policy at `require_one_segment_source` — extracted
helper with `field_label` / `must_map_to` nouns; byte-stable messages.

#### Prior Implementation (Worker 1)

Owner `serializer_converter.py::require_one_segment_source`. Migrated
`backing_model_field` + `_resolve_nested_field` + unit test
`test_require_one_segment_source_rejects_star_and_dotted`. Focused proof 4
passed (`--no-cov`). Changelog no.

#### Prior Independent verification (Worker 2)

Re-traced folder end-to-end. Consolidation disposed verified: sole
`source_attrs` predicate; both write-back paths call it; nested does not
route through `backing_model_field`. Twelve rejected/deferred re-proved
separate. ITEM_BASELINE then was
`7cdcd641b7d743c58faba872ccf8c9c17ebacf03`. Verdict: consolidation complete;
folder ready to close — but plan checkbox left open, triggering this fresh
pass.

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
