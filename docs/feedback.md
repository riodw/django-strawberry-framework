# DRY review — `utils/` + `forms/` sweep (v0.0.12)

Prompted by skepticism that the 0.0.12 DRY cycle found **zero** real opportunities.
That result was an artifact of scope: the cycle asked "did the new spec-038 slice
reuse the helpers that already existed?" (answer: yes, thoroughly) rather than "does
the codebase still carry parallel logic the shared layer hasn't absorbed?" This
review asks the second question against `django_strawberry_framework/utils/` and
`django_strawberry_framework/forms/`.

**Framing that matters:**

- `utils/` is the package's designated DRY *sink* — where the 0.0.9 Major-1/3/4
  passes and the spec-038 I1 pass deposited their consolidations. So the wins
  *inside* it are mostly **cohesion / placement** issues, not raw copy-paste (the
  copy-paste already got hoisted here).
- `forms/` is built as a deliberate **structural sibling** of `mutations/` and
  already *calls* the promoted `036` helpers (`locate_instance`,
  `authorize_or_raise`, `save_or_field_errors`, `refetch_optimized`,
  `build_payload`, `validation_error_to_field_errors`, `raw_choice_value`) rather
  than re-implementing them. The residual duplication is (a) structural parallels
  with `mutations/` left as copies on purpose, and (b) the two form bases / two
  pipeline bodies re-spelling each other.

No code was changed in this review. Findings below are investigate-and-decide, not
applied. Severity is my estimate of consolidation value vs. risk.

---

## MAJOR

### M1 — The sync/async resolver entry pair + `sync_to_async` wrapper is duplicated *verbatim* across `forms/` and `mutations/`

`forms/resolvers.py::resolve_form_sync` / `resolve_form_async` and
`mutations/resolvers.py::resolve_mutation_sync` / `resolve_mutation_async` are
byte-for-byte identical except the wrapped body's name and the docstring:

```python
def resolve_<flavor>_sync(mutation_cls, info, *, data=UNSET, id=UNSET):
    return _run_<flavor>_pipeline_sync(mutation_cls, info, data, id)

async def resolve_<flavor>_async(mutation_cls, info, *, data=UNSET, id=UNSET):
    return await sync_to_async(_run_<flavor>_pipeline_sync, thread_sensitive=True)(
        mutation_cls, info, data, id,
    )
```

The same `UNSET`-normalizing positional hand-off and the same
`sync_to_async(..., thread_sensitive=True)` boundary. The forms docstring even
admits it: "the same boundary shape `036` set, a deliberate same-shape sibling."

- **Confidence:** high — confirmed by reading both files.
- **Fix:** one shared entry point — `run_pipeline_async(sync_body, mutation_cls, info, data, id)`
  (or a `make_resolver_entries(sync_body)` factory returning the sync+async pair).
  Both subsystems' entry pairs collapse to a call. This is the cleanest, lowest-risk
  extract in the codebase; it reaches into `mutations/` but the lever is small.

### M2 — The two form sync pipeline bodies share one skeleton with divergent payload returns

`forms/resolvers.py::_run_modelform_pipeline_sync` and `::_run_plain_form_pipeline_sync`
both run: open `transaction.atomic()` → authorize-before-decode →
`_decode_form_data` + short-circuit → `get_form(...)` → `is_valid()` + short-circuit
→ `save_or_field_errors(...)` + short-circuit → success. The model body adds locate +
refetch (the legitimate difference). The rest is parallel, with **7 hand-rolled
error-return sites** that differ only in envelope shape:

```python
build_payload(payload_cls, slot, None, [err])   # ModelForm body, 4×
payload_cls(ok=False, errors=[err])              # plain body, 3×
```

- **Confidence:** high, with one verified caveat. The obvious lever —
  routing the plain body through `build_payload` — **does not work**:
  `build_payload` is `payload_cls(**{slot: obj, "errors": errors})` (no `ok` flag),
  while the plain payload is the `{ ok errors }` shape with no object slot. I checked
  `mutations/resolvers.py::build_payload` directly.
- **Fix:** extract a shared **"decode → construct → validate → write"** core
  parameterized by (the save callable, an error-payload factory). The model factory
  closes over `build_payload(payload_cls, slot, None, errs)`; the plain one over
  `payload_cls(ok=False, errors=errs)`. The skeleton lives once; the two envelopes
  stay distinct.

### M3 — The two form bases re-spell their seam overrides (`build_input` / `input_type_name`)

In `forms/sets.py`, `DjangoModelFormMutation` and `DjangoFormMutation` carry
near-duplicate `build_input` and `input_type_name`.

`build_input` tails are byte-identical (differ only in `operation_kind` and the base
label handed to `_form_kwargs_overridden`):

```python
input_cls, field_specs = _cached_build_form_input(
    meta.form_class, operation_kind=..., fields=meta.fields, exclude=meta.exclude,
    guard_required=not _form_kwargs_overridden(cls, <base>),
)
materialize_form_input_class(input_cls.__name__, input_cls)
cls._input_field_specs = field_specs
return input_cls
```

`input_type_name` differs *only* in `operation_kind`:

```python
effective = _resolve_effective_form_field_names(meta.form_class, fields=meta.fields, exclude=meta.exclude)
full = tuple(get_form_fields(meta.form_class))
return form_input_type_name(meta.form_class, <operation_kind>, effective, full_field_names=full)
```

- **Confidence:** high.
- **Fix:** two module-level helpers — `_build_and_stash_form_input(cls, meta, *, operation_kind, base)`
  and `_form_input_type_name_for(meta, operation_kind)` — each base becomes a one-line
  call. Same pattern the file already uses for `_default_get_form_kwargs` /
  `_default_get_form`. The `CREATE if meta.operation == "create" else PARTIAL`
  mapping (currently repeated at both `ModelForm` sites) collapses into the helper.

### M4 — Case-conversion is fragmented across two `utils/` modules, with a shared core copy-pasted

`utils/strings.py` explicitly declares itself the single home for case conversion
("If a third style ever shows up we'll add it here rather than re-deriving inline").
Yet `graphql_camel_name` — a third style (camelCase) — shipped in `utils/inputs.py`
(re-exported as `_camel_case`). It is both misplaced *and* duplicative:
`graphql_camel_name(x)` is `lowercased_head + pascal_case(rest)`, and its
`"".join(part.capitalize() for part in ...)` tail is the body of
`utils/strings.py::pascal_case`. `forms/inputs.py` is its heaviest caller (5×).

- **Confidence:** high.
- **Fix:** move `graphql_camel_name` into `utils/strings.py` beside `pascal_case` /
  `snake_case`, and express it in terms of `pascal_case` so the
  capitalize-each-token core lives once. Update the `utils/inputs.py` re-export.

### M5 — The per-family "name the family in the error message" parameter is reinvented six ways

Across `utils/`, every shared helper that interpolates a family name into a
`ConfigurationError` / `TypeError` invented its own parameter shape:

| Helper | Parameter(s) |
| --- | --- |
| `utils/inputs.py::normalize_field_name_sequence` | `flavor` |
| `utils/inputs.py::materialize_generated_input_class` | `family_label` |
| `utils/permissions.py::request_from_info` | `family_label` |
| `utils/inputs.py::build_lazy_input_annotation` | `family_name` + `expected_label` |
| `utils/inputs.py::GeneratedInputArgumentsFactory` | `_factory_label` + `_family_label` + `_rename_noun` |

Same cross-cutting concern — "how do I refer to this set family in user-facing
errors" — solved with five incompatible shapes. Adding a third family means touching
every signature.

- **Confidence:** medium-high (this is a coherence finding, not raw line-dup).
- **Fix:** a small `FamilyLabels` / `SetFamilyIdentity` value object threaded through,
  or at minimum a single naming convention. Single-sites the contract.

### M6 — `utils/inputs.py`'s stated scope no longer matches its contents

The module docstring says it is "shared by the **filter and order** set families."
But it now hosts `normalize_field_name_sequence` (whose own docstring says it serves
**mutations and forms**) and `graphql_camel_name` (a pure string helper). Meanwhile
`utils/input_values.py` and `utils/permissions.py` are *both* about filter/order
input traversal and overlap so much that `permissions` re-exports `iter_input_items`
from `input_values` for back-compat.

This is plausibly **why the 0.0.12 cycle found nothing**: helpers are filed by the
spec that birthed them, so a reviewer scoped to "did the new slice reuse helpers"
never sees that the *organization* has drifted.

- **Confidence:** medium (judgment call; re-homing has churn cost).
- **Fix:** a deliberate re-home pass — string helpers → `strings.py`; the
  mutation/form field-sequence normalizer → a mutation-shared utils home or a
  renamed/rescoped module; reconcile the `input_values` / `permissions` split.

---

## MEDIUM

### Md1 — Sync/async colored twins in `utils/querysets.py`

`post_process_queryset_result_sync` / `_async` are structurally identical except the
visibility call; likewise `apply_type_visibility_sync` / `_async`. Real duplication —
but collapsing colored functions often hurts clarity. Look before leaping.

### Md2 — `forms/inputs.py::_field_triple_and_spec` repeats the scalar/file triple 5–6×

`python_attr = name; graphql_name = graphql_camel_name(name)` is spelled in five arms,
and the FILE arm (`annotation = Upload; kind = FILE`) is byte-identical in the
column-backed *and* column-less branches. A `_simple_triple(name, annotation, kind)`
flattens the if/elif ladder.

### Md3 — `forms/resolvers.py::_form_payload_cls` mirrors `mutations/resolvers.py::_payload_cls_for`

Both do "getattr a `<Name>Payload` off `mutations.inputs` by `_payload_type_name`",
and `_form_payload_cls`'s own docstring states both flavors materialize their payload
into `mutations.inputs` precisely so the lookup is the same. This is the same
"promote and reuse" move the spec applied to nine other helpers — `_payload_cls_for`
was simply missed.

- **Fix:** promote `_payload_cls_for` → `payload_cls_for` (underscore-dropped in
  place), import it in `forms/resolvers.py`, delete `_form_payload_cls`. Update any
  `AGENTS.md` `::OldName` rename-sweep refs.

### Md4 — The visibility-scoped related queryset is built identically on three paths

`mutations/resolvers.py::_relation_visibility_error` /  `::_raw_pk_relation_error`
and `forms/resolvers.py::_visible_related_object` each build
`apply_type_visibility_sync(related_type, initial_queryset(related_type), info, <recourse>)`.
The composition is over two single-sourced primitives, so the literal dedup is small —
but the spec's cross-flavor security claim is that the form and model paths apply *the
same* related-type `get_queryset`. A `visibility_scoped_related_queryset(related_type,
info, recourse)` makes that sameness structural rather than coincidental (`recourse`
stays a parameter).

### Md5 — The two `_validate_meta` matrices in `forms/sets.py` share a spine

`DjangoModelFormMutation._validate_meta` and `DjangoFormMutation._validate_meta`
share: unknown-key guard → `_require_form_class` → type gate →
`_resolve_effective_form_field_names` → `_validate_permission_classes` → build
`_ValidatedMutationMeta`. The divergence (operation handling, ModelForm-vs-Form gate
ordering, model resolution) is the *point* of the two-base split, so only the
narrowing-validate + permission-validate + snapshot-build tail is safely shareable.
**Look, but don't over-merge** — coupling the targeted error messages would be a net
negative. The shared atoms are already extracted.

### Md6 — Two single-field input readers in `utils/`

`utils/permissions.py::extract_branch_value` re-implements the dict-vs-`getattr`
discrimination that `utils/input_values.py::iter_input_items` already owns for the
all-fields case. One "read field N off a dict-or-dataclass input" primitive could back
both.

---

## MINOR

### Mn1 — Four `resolve_sync` / `resolve_async` seams on the two form bases

`forms/sets.py` carries four 2-line local-import-and-delegate methods differing only
in whether `id` is threaded. Thin, but it feeds M1's shared entry — fold together
there.

### Mn2 — Cycle-breaking local imports repeated in `forms/resolvers.py`

Five imports are deferred inside helper bodies (`FieldError`, `registry`,
`mutations.inputs`, `validation_error_to_field_errors`, `payload_object_slot`). Each is
the "avoid load cycle" idiom; consider one documented lazy-accessor block so the cycle
contract is stated once rather than five times.

### Mn3 — The bind-stashed reverse map is re-indexed per resolve

`forms/resolvers.py::_decode_form_data` builds `spec_by_attr` from `_input_field_specs`
and `_non_file_form_field_names` re-walks the same list each resolve. Index once at
bind (alongside the existing stash).

### Mn4 — Defensive relation-flag reads in `utils/relations.py`

`getattr(field, "many_to_many"/"auto_created"/"concrete", False)` is spelled in both
`relation_kind` and `is_forward_many_to_many`. Tiny; a `_flag(field, name)` helper is
probably overkill but note the repeated read contract.

### Mn5 — Two BFS-with-seen-set traversals in `utils/inputs.py`

`iter_set_subclasses` and `GeneratedInputArgumentsFactory._ensure_built` both hand-roll
"walk a graph, dedup by identity, FIFO/LIFO." The bodies diverge (one builds +
collision-checks), so a generic extraction may not pay — confirm before acting.

---

## Considered and deliberately NOT recommended

Per the `AGENTS.md` "highest-quality fix, never a pragmatic shortcut" bar — these look
like duplication but consolidating would hurt clarity:

- **Merging the two `forms/sets.py::_validate_meta` matrices** beyond their already-
  extracted atoms — see Md5. The divergence carries the targeted, edge-case error
  messages that are the whole reason for the two-base split.
- **The thin-wrapper trio in `utils/permissions.py`** (`active_related_branches` /
  `active_permission_field_paths` both delegating to `active_permission_targets`) —
  this is *already* good DRY; the wrappers keep the classification single-sited.
- **`utils/querysets.py::model_for` / `initial_queryset` indirection** — already
  centralized; the layering is intentional.

---

## Method / caveats

- Read in full: all of `utils/` (8 modules) and all of `forms/` (4 modules), plus the
  `mutations/resolvers.py` helpers `forms/` reuses (`build_payload`,
  `resolve_mutation_sync` / `_async`, the `sync_to_async` wrapper) to size M1 / M2 / Md3.
- **Not** read exhaustively: the rest of `mutations/`, `filters/`, `orders/`. M1, Md3,
  and Md4 reach into `mutations/`; sizing their twins fully needs a `mutations/` pass.
- **No code changed.** No tests run (per `AGENTS.md`). Severities are review estimates,
  not measured.
