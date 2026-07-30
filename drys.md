These are the six file pairs I’d reopen first — ranked by remaining **logical overlap** (same job, parallel helpers), not by “already rejected as intentional flavor boundary.”

1. `mutations/resolvers.py` ↔ `forms/resolvers.py`  
   Highest leftover twin: `_run_plain_form_pipeline_sync` vs `run_write_pipeline_sync` (spec-046 C2), plus `_run_delete` / `tail_step`. Phase helpers already shared; the orchestration bodies still largely mirror each other.

2. `filters/sets.py` ↔ `orders/sets.py`  
   Strongest structural twin in the package: permission/visibility apply loops, `_normalize_input`, active-permission helpers, metaclass/build shape. Decision-9 packaging and apply-pipeline merge were explicitly deferred.

3. `filters/inputs.py` ↔ `orders/inputs.py`  
   Parallel Decision-9 surfaces: `materialize_input_class`, `normalize_input_value`, `_build_input_fields`, `_input_type_name_for`, `_leaf_of`. Substrate is partly shared; the remaining wrappers still look like colored copies of one rule.

4. `forms/inputs.py` ↔ `rest_framework/inputs.py`  
   Same write-input job across flavors: model-less relation annotation (`_model_less_relation_annotation` ↔ `serializer_only_relation_annotation`), nested resolve / `source` policy, Meta field-selection / ownership. Deferred waiting on a forms-clean pass.

5. `forms/converter.py` ↔ `rest_framework/serializer_converter.py`  
   Same conversion pipeline over different key spaces. Shared owners already exist (`convert_with_mro`, `FieldConversionBase`), but relation-id / one-segment-source / scalar-table edges still look extractable without merging the tables themselves.

6. `filters/factories.py` ↔ `orders/factories.py`  
   Layer-5 factory twins; filters already has `_make_hashable` / `get_filterset_class`, orders still has the TODO twin for `get_orderset_class`. Clearest “one hashing/cache owner, two thin callers” opportunity once orders’ dynamic cache lands.

**Honorable near-miss** (if you want a 7th): `forms/sets.py` ↔ `rest_framework/sets.py` — Meta validate / `build_input` / construction-hook shape — but more of that already rode `mutations/sets.py` helpers than the pairs above.

7. `forms/sets.py` ↔ `rest_framework/sets.py`  
   Parallel Meta validate / `build_input` / `_resolve_model` / construction-hook surfaces. A lot already rides mutations helpers; what’s left is flavor-local Meta matrices and bind/register twins that still read like the same class-creation story twice.

8. `mutations/sets.py` ↔ `forms/sets.py`  
   Structural metaclass twins (`make_meta_validating_metaclass` already shared): `_validate_meta` → register → `build_input` / `input_type_name`. Remaining condensation is the remaining Meta-rule tables and permission/default wiring that still diverge by Decision flags rather than by truly different jobs.

9. `mutations/resolvers.py` ↔ `rest_framework/resolvers.py`  
   Serializer already rides `run_write_pipeline_sync`, but decode/write lambdas, M2M / relation coercion, and error-envelope shaping still mirror model/form resolver helpers. Best second pass after the plain-form C2 fold (#1), so the skeleton seams aren’t redesigned twice.

10. `forms/resolvers.py` ↔ `rest_framework/resolvers.py`  
    Same decode vocabulary (`_scalar` / `_relation` / `_file`) and write-step glue over different backends (Django form vs DRF serializer). After #1/#9, this is where leftover decode/write micro-helpers should collapse.

11. `forms/inputs.py` ↔ `rest_framework/serializer_converter.py`  
    Cross-file twin already named in artifacts: `_model_less_relation_annotation` ↔ `serializer_only_relation_annotation`. Same “relation field, no backing model column” annotation job — currently split across inputs vs converter ownership.

12. `mutations/inputs.py` ↔ `forms/inputs.py`  
    `build_mutation_input` ↔ `build_form_input_class`: field materialize, optional/required, dropped-required guards, shape naming. Shared substrate in `utils/inputs.py` already; remaining builder bodies still look like two recipes for one input-shape meal.

13. `mutations/inputs.py` ↔ `rest_framework/inputs.py`  
    Same as #12 on the serializer leg: shape descriptors (`MutationInputShape` vs `SerializerInputShape`), nested build, cache keys. Descriptor-vs-name-set timing differs, but field-spec assembly and nested recursion still overlap hard.

14. `filters/factories.py` ↔ `filters/sets.py`  
    Intra-filters: dynamic FilterSet cache / hashing vs runtime FilterSet apply. Worth revisiting whether `_make_hashable` / meta canonicalization and set-side field-path normalization should share one “meta fingerprint” owner before orders copies it (#6).

15. `orders/factories.py` ↔ `orders/sets.py`  
    Same intra-family cut as #14 once `get_orderset_class` exists. Listing it now so the filters and orders factory/set pairs stay symmetric when Layer-6 lands.

16. `optimizer/lateral_fetch.py` ↔ `keyset.py`  
    Direction / seek SQL vs ORM `Q` were kept as separate backends on purpose — but the “lateral twin of `keyset_seek_*`” comments still point at a real shared plan shape (`KeysetSeekPlan` / direction rule). Highest-value optimizer↔keyset condensation left.

17. `optimizer/lateral_fetch.py` ↔ `optimizer/nested_fetch.py`  
    Same folder, same “plan then fetch children” job; nested vs lateral backends. Shared plan/`__post_init__` edges and fragment/prefix threading were only partly collapsed.

18. `connection.py` ↔ `utils/connections.py`  
    Field orchestration vs window/bounds/relay-max helpers. A lot already extracted; remaining overlap is cursor-parity argument handling and keyset/offset twin entry points that still sit half in the field, half in utils.

If you want a third tranche after this, the next tier is mostly `types/*` ↔ write-flavor converters/relations and `utils/inputs.py` as the gravity well those builders should keep sinking into — lower urgency than #7–#13 because the shared owners already exist.

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
