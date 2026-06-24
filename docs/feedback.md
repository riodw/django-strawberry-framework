# Review feedback — spec-038 form-mutations, DRY pass

Focus: duplication / single-sourcing opportunities across the form-mutation
subsystem (`django_strawberry_framework/forms/`) and the `036` helpers it shares
(`mutations/resolvers.py`, `mutations/sets.py`). The prior round's fixes are in the
working tree (the `docs/feedback.md` "Finding N" comment citations were re-anchored
to `spec-038` Decisions, and the `_form_kwargs_overridden` waiver caveat is now
documented — both correct).

The implementation is already strongly DRY at the macro level: the pipeline
helpers (`locate_instance` / `coerce_lookup_id` / `authorize_or_raise` /
`refetch_optimized` / `build_payload` / `save_or_field_errors` /
`validation_error_to_field_errors` / `raw_choice_value`) are promoted `036` code
**called**, not re-implemented. The opportunities below are residual: a payload
helper that was *not* promoted and got re-spelled, an identical relation-membership
core duplicated 3×, and the two form bases carrying parallel `build_input` /
`input_type_name` bodies.

## Findings

### [High] `forms/resolvers.py::_form_payload_cls` re-implements `036`'s `_payload_cls_for` verbatim

`forms/resolvers.py::_form_payload_cls` is byte-identical logic to
`mutations/resolvers.py::_payload_cls_for`:

```python
# forms/resolvers.py::_form_payload_cls
from ..mutations import inputs
return getattr(inputs, mutation_cls._payload_type_name)

# mutations/resolvers.py::_payload_cls_for
from . import inputs
return getattr(inputs, mutation_cls._payload_type_name)
```

Both read the materialized `<Name>Payload` from `mutations.inputs` by
`_payload_type_name`, and `_form_payload_cls`'s own docstring states the form
payload is materialized into `mutations.inputs` for *both* flavors precisely so the
lookup is the same. This is the same "promote the `036` helper and reuse it" move
the spec already applied to nine pipeline helpers — `_payload_cls_for` was simply
missed.

- **Fix:** promote `_payload_cls_for` → `payload_cls_for` (underscore-dropped in
  place, exactly like the other promoted helpers), import it in
  `forms/resolvers.py`, and delete `_form_payload_cls`. Update the
  `AGENTS.md` `::OldName` rename-sweep refs.

### [High] The pk-membership-subset `_relation_error` core is duplicated across three functions

`mutations/resolvers.py::_relation_visibility_error`,
`::_raw_pk_relation_error`, and `::_relation_existence_error` each end with the
identical 5-line membership check:

```python
present = {str(pk) for pk in <queryset>.filter(pk__in=<query_pks>).values_list("pk", flat=True)}
if not {str(pk) for pk in <declared_pks>} <= present:
    return _relation_error(field_name)
return None
```

The only axes of variation are the queryset (the visibility-scoped
`apply_type_visibility_sync(initial_queryset(...))` for the two visibility checks,
the `_default_manager` for the existence check) and whether the queried pks were
pre-coerced. This is exactly the kind of "the same invariant spelled three times"
that drifts — and two of the three sites are new this cycle, so the duplication is
fresh.

- **Fix:** extract one helper, e.g.

  ```python
  def _relation_membership_error(field_name, queryset, declared_pks, query_pks):
      present = {str(pk) for pk in queryset.filter(pk__in=query_pks).values_list("pk", flat=True)}
      if not {str(pk) for pk in declared_pks} <= present:
          return _relation_error(field_name)
      return None
  ```

  and have all three call it (passing the visibility queryset or the default
  manager, and `declared_pks` / `query_pks` for the coercion split). The membership
  semantics then live in one place, which is where the no-existence-leak invariant
  belongs.

### [Medium] The visibility-scoped related queryset is built identically on the model and form paths

`mutations/resolvers.py::_relation_visibility_error` and `::_raw_pk_relation_error`
and `forms/resolvers.py::_visible_related_object` each build:

```python
apply_type_visibility_sync(related_type, initial_queryset(related_type), info, <recourse>)
```

The composition is already over two single-sourced primitives (`initial_queryset`
+ `apply_type_visibility_sync`), so the literal dedup is small — but the spec's
whole cross-flavor security claim is that the form and model paths apply *the same*
related-type `get_queryset`. A shared
`visibility_scoped_related_queryset(related_type, info, recourse)` would make that
sameness structural rather than coincidental, and reads as the obvious companion to
the `_relation_membership_error` extraction above (one builds the queryset, the
other checks membership in it).

- **Fix (optional, judgment call):** extract the one-line builder if you want the
  invariant pinned in code; the `recourse` string stays a parameter
  (`_FORM_ASYNC_RECOURSE` vs `_MUTATION_ASYNC_RECOURSE`). Lower urgency than the two
  above since the underlying helpers are already shared.

### [Medium] `forms/sets.py` — the two bases carry parallel `build_input` / `input_type_name` bodies

`DjangoModelFormMutation.build_input` and `DjangoFormMutation.build_input` differ
only in the `operation_kind` and the waiver base; their tail is identical:

```python
input_cls, field_specs = _cached_build_form_input(meta.form_class, operation_kind=..., fields=meta.fields, exclude=meta.exclude, guard_required=not _form_kwargs_overridden(cls, <base>))
materialize_form_input_class(input_cls.__name__, input_cls)
cls._input_field_specs = field_specs
return input_cls
```

Likewise `DjangoModelFormMutation.input_type_name` and
`DjangoFormMutation.input_type_name` share the full body except `operation_kind`:

```python
effective = _resolve_effective_form_field_names(meta.form_class, fields=meta.fields, exclude=meta.exclude)
full = tuple(get_form_fields(meta.form_class))
return form_input_type_name(meta.form_class, <operation_kind>, effective, full_field_names=full)
```

- **Fix:** two module helpers — `_build_and_stash_form_input(cls, meta, *, operation_kind, base)`
  and `_form_input_type_name_for(meta, operation_kind)` — each base then becomes a
  one-line call. This keeps the materialize-and-stash sequence and the name
  derivation single-sited, so a future change to either (e.g. a new field-spec
  stash) touches one place.

### [Low] `CREATE if meta.operation == "create" else PARTIAL` repeated in the `ModelForm` base

The operation→kind mapping appears at both
`DjangoModelFormMutation.build_input` and `.input_type_name`. Minor, but if you
extract the helpers above it collapses naturally into a single
`_modelform_operation_kind(meta)` (or just an inline arg passed from one site).

## Considered and deliberately NOT recommended

To keep the DRY pass from forcing consolidation that would hurt clarity (per the
`AGENTS.md` "highest-quality fix, never a pragmatic shortcut" bar):

- **The two `_validate_meta` matrices** (`DjangoModelFormMutation` vs
  `DjangoFormMutation`) look parallel but are genuinely disjoint: different
  allowed-key sets, the plain base's targeted `ModelForm`-rejection and
  `operation`-rejection messages, and the deny-by-default permission default. Their
  shared atoms (`_require_form_class`, `_resolve_effective_form_field_names`,
  `_validate_permission_classes`) are *already* extracted. Merging the matrices
  would couple the targeted error messages — net negative. Leave split.
- **`resolve_sync` / `resolve_async` seam overrides on the two bases** are 2-line
  delegations to the already-single-sourced `resolve_form_sync` /
  `resolve_form_async`, differing by the `id` parameter (model) vs none (plain).
  Consolidating adds indirection for no real dedup. Leave.
- **The two pipeline bodies** (`_run_modelform_pipeline_sync` /
  `_run_plain_form_pipeline_sync`) share a short authorize→decode→validate prologue,
  but the payload construction (`build_payload(..., slot, ...)` vs
  `payload_cls(ok=..., errors=...)`) and the locate/refetch steps differ
  materially; the genuinely shared atoms (decode, error-mapping, save-mapping) are
  already helpers. Forcing a single body would obscure the two distinct envelopes.
  Leave as the two-branch dispatch they are.

## Checks run

- `uv run ruff check` / `ruff format --check` over the touched modules → clean
- `uv run python scripts/check_trailing_commas.py --check …` → clean
- Did **not** run `pytest` (per `AGENTS.md`); the extractions above are
  behavior-preserving and covered by the existing live + package suites.
