# DRY review — the three-flavor write stack (model / form / serializer), utils-first — VERIFIED

**Scope:** `django_strawberry_framework/utils/` (the reuse inventory), then the three write
flavors (`mutations/`, `forms/`, `rest_framework/`) that now form a three-way mirror.
**Mode:** every finding below was re-verified against source after the first pass. Each
item now carries a **Verdict** (REAL / PARTIALLY REAL) and **Proof** (verbatim excerpts +
the exact symbols). Findings whose *premise* or *proposed lever* did not survive
verification were corrected in place, not silently kept. Nothing here is a behavior change.

**The headline:** spec-039 did its P-numbered DRY homework well — the pipeline skeleton,
the async boundary, the error-leaf ctors, the namespace/cache factories, and the MRO
converter dispatch are all genuinely single-sited now. But adding the THIRD sibling
changed the economics of everything left as a "tolerable pairwise parallel" in 038: what
was 2 copies is now 3 (sometimes 4, counting the plain-form base), and several
"deliberately deferred" items (P2.3, P2.7 notes in the code) now have enough consumers to
justify promotion. The pattern to hunt is no longer "X mirrors Y" — it is **the per-flavor
plumbing kit**: every new write flavor re-spells the same ~8 pieces of glue.

**Verification verdicts at a glance:**

| # | Finding | Verdict |
|---|---|---|
| M1(a) | resolver sync/async entry pair/trio | **PARTIALLY REAL** — async trio is an exact 3× win; the "sync entry" side is only 2 true parallels (serializer diverges). Miscount corrected below. |
| M1(b) | 8 `resolve_sync`/`resolve_async` classmethod seams | **REAL** |
| M2 | UNSET-strip walk + scalar decode tail ×3 | **REAL** (primitives already single-sourced; the *walk* is what recurs) |
| M3 | relation-id structural type-check, 3 ways | **REAL** |
| M4 | `resolve_effective_{form,serializer}_fields` | **REAL** (one factual fix: the read-only drop is *inside* the fn, not at the call site) |
| M5 | `_validate_meta` backing-class prologue | **REAL, but narrower** — 3 of the 8 clauses are already shared symbols |
| M6 | generated-input type-name skeleton ×3 | **REAL** |
| Md1 | `guard_create_required_*` | **REAL** |
| Md2 | five `*_ASYNC_RECOURSE` constants | **REAL** (3 identical modulo subject; 2 genuinely differ) |
| Md3 | "registry.get → visibility qs or default mgr" ×4 | **REAL** (shallow structural echo; per-site None-handling diverges) |
| Md4 | stringified-pk subset membership | **REAL** — one axis (model-home vs serializer-home), not four-way |
| Md5 | `_pascalize_token` promotion | **PARTIALLY REAL** — the 3-consumer duplication is real; the proposed destination (`pascal_case`) is **wrong**. Corrected. |
| Md6 | `graphql_camel_name` location | **PARTIALLY REAL** — the location fact is real; the "strings.py claims to be the single home" premise is **false**. Corrected. |
| Md7 | construction-kwargs hooks | **REAL** |
| Mn1 | three aliases of `relation_field_error` | **REAL** |
| Mn2 | `{create: CREATE, update: PARTIAL}` map ×3 | **REAL** |
| Mn3 | two field-sequence re-binding wrappers | **REAL** |
| Mn4 | `_reverse_map_for` / `_join_path` | **REAL** — only `_reverse_map_for` is inline-worthy (1 caller); `_join_path` earns its keep (5 callers) |
| Mn5 | `input_type_name` re-builds the shape | **REAL** |

---

## The utils/ reuse inventory (what already exists — route consolidations HERE)

Anything promoted should land in `utils/` (cycle-safe by construction) or
`mutations/` (the root flavor all others already import from). Existing homes:

- `utils/strings.py` — `snake_case`, `pascal_case`. Its docstring says only that a *new*
  case *style* (kebab, SCREAMING_SNAKE) should land here rather than be re-derived inline;
  it does **not** claim to be the single home for every case converter (relevant to the
  Md5/Md6 corrections below).
- `utils/inputs.py` — `GeneratedInputFieldSpec`, `InputFieldSpec` (the unified 039 spec),
  `make_input_namespace`, `make_shape_build_cache`, `graphql_camel_name`,
  `normalize_field_name_sequence(flavor=...)`, `build_strawberry_input_class`,
  `materialize_generated_input_class`, `build_lazy_input_annotation`,
  `iter_set_subclasses`, `clear_generated_input_namespace`,
  `GeneratedInputArgumentsFactory`.
- `utils/querysets.py` — `SyncMisuseError`, `reject_async_in_sync_context`, `model_for`,
  `initial_queryset`, `normalize_query_source`, `apply_type_visibility_sync/async`,
  `visibility_scoped_related_queryset`, `visible_related_object`,
  `visible_related_objects`, `post_process_queryset_result_sync/async`.
- `utils/converters.py` — `convert_with_mro` (the form + serializer converter skeleton).
- `utils/input_values.py` / `utils/permissions.py` — the set-family traversal +
  permission walk (filter/order side; not implicated below).
- `utils/relations.py` — `relation_kind`, `is_forward_many_to_many`, `instance_accessor`,
  `has_composite_pk`.
- `mutations/resolvers.py` (the de-facto shared write runtime) —
  `run_write_pipeline_sync`, `run_pipeline_async`, `field_error`,
  `relation_field_error`, `validation_error_to_field_errors`, `save_or_field_errors`,
  `raw_choice_value`, `_unencodable_text_error`, `_coerce_relation_pk_or_none`,
  `locate_instance`, `coerce_lookup_id`, `authorize_or_raise`, `refetch_optimized`,
  `build_payload`, `payload_cls_for`, `not_found_error`.
- `mutations/sets.py` (the de-facto shared bind runtime) — `reject_unknown_meta_keys`,
  `non_delete_operation_error`, `_hook_overridden`, `cached_build_input`,
  `build_and_stash_input`, `make_declaration_registry`,
  `_validate_permission_classes`, `_ValidatedMutationMeta`.

---

## MAJOR

### M1 — The per-flavor resolver plumbing stack — **verified, with one miscount corrected**

**(a) The module-level entry pair/trio.** **Verdict: PARTIALLY REAL.**

The **async trio is an exact 3× win** — three byte-parallel one-liners, body first, same arg
order:

```python
# mutations/resolvers.py::resolve_mutation_async
return await run_pipeline_async(_run_pipeline_sync, mutation_cls, info, data, id)
# forms/resolvers.py::resolve_form_async
return await run_pipeline_async(_run_form_pipeline_sync, mutation_cls, info, data, id)
# rest_framework/resolvers.py::resolve_serializer_async
return await run_pipeline_async(_run_serializer_pipeline_sync, mutation_cls, info, data, id)
```

The **sync side is only TWO true parallels**, not "three and a half." The finding
overcounted. `mutations/resolvers.py::resolve_mutation_sync` and
`forms/resolvers.py::resolve_form_sync` are the identical "UNSET-default kwargs → single
positional delegate" adapter:

```python
def resolve_mutation_sync(mutation_cls, info, *, data=strawberry.UNSET, id=strawberry.UNSET):
    return _run_pipeline_sync(mutation_cls, info, data, id)
def resolve_form_sync(mutation_cls, info, *, data=strawberry.UNSET, id=strawberry.UNSET):
    return _run_form_pipeline_sync(mutation_cls, info, data, id)
```

But `rest_framework/resolvers.py::resolve_serializer_sync` is a **different shape** — it does
not delegate to a `_run_*_pipeline_sync` dispatcher; it calls `run_write_pipeline_sync`
directly with `decode_step`/`write_step` lambdas (the serializer has no delete/plain-vs-
ModelForm branch to dispatch on, so entry and body are collapsed). And
`_run_serializer_pipeline_sync` — which the finding listed as a third "sync entry" — is
actually a *reverse-direction* positional adapter that lets the positional
`run_pipeline_async` boundary re-enter the kwargs-based `resolve_serializer_sync`. It is not
a peer of `resolve_mutation_sync`.

**Lever (corrected):** a `make_resolver_entries(sync_body)` factory in
`mutations/resolvers.py` cleanly collapses the **async trio** and the **model/form sync
pair**. The serializer's sync entry is genuinely a different shape and should stay as-is (or
be folded only if `run_write_pipeline_sync` grows a delegating overload). The win is real
but smaller than "15-ish defs → 3 calls."

**(b) The `resolve_sync` / `resolve_async` classmethod seams.** **Verdict: REAL.**

Exactly eight classmethods, every one the identical "function-local import (cycle guard) +
delegate with `data=`/`id=`" body:

```python
# DjangoMutation (mutations/sets.py)          from .resolvers import resolve_mutation_sync
#                                              return resolve_mutation_sync(cls, info, data=data, id=id)
# DjangoModelFormMutation (forms/sets.py)      resolve_form_sync(cls, info, data=data, id=id)
# SerializerMutation (rest_framework/sets.py)  resolve_serializer_sync(cls, info, data=data, id=id)
# DjangoFormMutation (forms/sets.py) — plain flavor, NO id:
def resolve_sync(cls, info, *, data):
    from .resolvers import resolve_form_sync
    return resolve_form_sync(cls, info, data=data)
```

The plain flavor's pair drops `id` from both signature and call exactly as the finding
predicted. **Lever:** a `resolver_seams(module, sync_name, async_name)` classmethod-pair
factory in `mutations/sets.py`. This is the cleaner half of M1 — eight defs → three factory
calls, no exceptions.

### M2 — The UNSET-strip input walk + the scalar decode tail, three copies — **Verdict: REAL**

The opening walk is **byte-identical** in `mutations/resolvers.py::_decode_relations`,
`forms/resolvers.py::_decode_form_data`, and `rest_framework/resolvers.py::_decode_input_object`
(the serializer's `_decode_serializer_data` is a one-line wrapper delegating to
`_decode_input_object`, so the attribution is correct):

```python
for field in data.__strawberry_definition__.fields:
    python_name = field.python_name
    value = getattr(data, python_name, strawberry.UNSET)
    if value is strawberry.UNSET:
        continue
```

The scalar tail — `_unencodable_text_error` preflight + `raw_choice_value` unwrap, short-
circuit on error — recurs in all three as a **call pattern**:

```python
# model
text_error = _unencodable_text_error(graphql_name, value)
if text_error is not None: return {}, [], text_error
scalar_and_fk_attrs[python_name] = _make_aware_if_naive(raw_choice_value(value))
# form
text_error = _unencodable_text_error(spec.graphql_name, value)
if text_error is not None: return {}, {}, text_error
provided_data[spec.form_field_name] = raw_choice_value(value)
# serializer
text_error = _unencodable_text_error(field_path, value)
if text_error is not None: return {}, text_error
provided_data[spec.target_name] = raw_choice_value(value)
```

**Nuance for the implementer:** the two primitives (`_unencodable_text_error`,
`raw_choice_value`) are already single-sourced in `mutations/resolvers.py` and imported by
the other two flavors — so what's duplicated is the *walk + the call sequence*, not the
primitives. The kind-handler tails genuinely diverge (model adds `_explicit_null_error` +
`_make_aware_if_naive`; form splits `files=`; serializer recurses nested) and the short-
circuit tuple arity differs (`{}, [], err` vs `{}, {}, err` vs `{}, err`). **Lever
(minimal):** an `iter_provided_input_fields(data)` generator in `utils/inputs.py` yielding
`(python_name, value, field)` — kills the 4-line preamble at all three sites. **Lever
(fuller):** a `decode_scalar_value(field_path, value) -> (decoded, error)` pairing the
preflight with the unwrap. Do NOT merge the kind handlers.

### M3 — The relation-id structural type-check is spelled three different ways — **Verdict: REAL**

The "GlobalID → `decode_model_global_id` (non-OK → uniform relation error) | raw pk →
`_coerce_relation_pk_or_none` (None → uniform relation error)" two-branch check:

```python
# rest_framework/resolvers.py::_type_check_relation_id — the cleanly-factored general one
if isinstance(value, relay.GlobalID):
    result = decode_model_global_id(value, related_model)
    if result.status is not GlobalIDDecode.OK: return None, _relation_field_error(graphql_name)
    return result.pk, None
pk = _coerce_relation_pk_or_none(related_model, value)
if pk is None: return None, _relation_field_error(graphql_name)
return pk, None
```

`forms/resolvers.py::_decode_form_relation_single` inlines the **same two-branch body**, then
diverges (resolves the visible object + converts via `to_field_name`/`_to_form_key_value`).
`mutations/resolvers.py::_decode_relation_id_set`'s element loop implements only the
**GlobalID half** (non-GlobalID values are appended raw with `continue`); its raw-pk half is
deliberately deferred to `_raw_pk_relation_error`, which batches coercion + visibility over
the whole set — a real semantic difference (documented in-source), **not** a duplication
defect.

**Lever:** promote `_type_check_relation_id` (drop the underscore) to `mutations/resolvers.py`
next to `_coerce_relation_pk_or_none`; the form single-decoder calls it and keeps only its
`empty_values` + `to_field_name` reduction. Leave the model batched path alone. This is
security-adjacent — one implementation of "what counts as a well-formed relation id" beats
three. (Note: the leaf-error ctor is already single-sourced —
`mutations/resolvers.py::relation_field_error` — only the local aliases `_relation_error` /
`_relation_field_error` differ; see Mn1.)

### M4 — `resolve_effective_form_fields` vs `resolve_effective_serializer_fields` — **Verdict: REAL** (one factual fix)

`forms/inputs.py::resolve_effective_form_fields` and
`rest_framework/inputs.py::resolve_effective_serializer_fields` share the identical spine, in
order: normalize `fields` + `exclude` (both through `normalize_field_name_sequence(flavor=…)`)
→ mutual-exclusion raise → take the basis dict → `fields`-branch unknown-name raise →
`exclude`-branch unknown-name raise (identical `[name for name in fields if name not in
<basis>]` loop) → empty-effective-set raise. The messages match modulo the flavor label and
one adjective:

```
# mutual-exclusion (both):  "<Flavor> for {…} declares both `fields` and `exclude`; supply at most one."
# unknown-name (form):      "declares `fields` naming unknown form field(s): {sorted(unknown)!r}."
# unknown-name (serializer):"declares `fields` naming unknown or non-writable serializer field(s): {…}."
```

Real deltas: the flavor label + the `form field(s)` vs `unknown or non-writable serializer
field(s)` adjective, and the **basis** — forms uses `base_fields` verbatim; the serializer
takes a `field_map`/discovery result.

**Correction to the original finding:** it claimed "the read-only/HiddenField drop is a
serializer-side pre-step **at the call site**." That is wrong — the drop is performed
**inside** `resolve_effective_serializer_fields` itself (the `writable = {name: field … if
not field.read_only and not isinstance(field, serializers.HiddenField)}` comprehension). So
the divergence is intrinsic to the function.

**Lever:** `utils/inputs.py::resolve_effective_fields(basis: dict, *, fields, exclude,
flavor, unknown_noun) -> dict`. Each flavor keeps a thin wrapper that computes its basis —
the serializer wrapper applies the writable filter *before* passing the basis in, which
cleanly restores the "basis is the only divergence" shape.

### M5 — The `_validate_meta` backing-class prologue is a third copy now — **Verdict: REAL, but narrower**

`forms/sets.py::DjangoModelFormMutation._validate_meta` and
`rest_framework/sets.py::SerializerMutation._validate_meta` re-spell the prologue clause-for-
clause. The `_resolve_model` twins confirm the finding exactly — same three-level `getattr`
chain, `_meta`/`Meta` the only delta:

```python
# forms:      getattr(meta,"form_class",None) → getattr(form_class,"_meta",None) → getattr(form_meta,"model",None)
# serializer: getattr(meta,"serializer_class",None) → getattr(serializer_class,"Meta",None) → getattr(serializer_meta,"model",None)
```

…and the "resolves no model" raise is near-identical (`"… must set Meta.model so the mutation
has a model + a DjangoType to return."`).

**Important scoping correction:** three of the eight clauses the finding lists as
"re-spelled" are **already shared symbols** imported from `mutations/sets.py` —
`reject_unknown_meta_keys`, `non_delete_operation_error`, `_validate_permission_classes` —
as is the `_ValidatedMutationMeta` return. So the residual duplication is *narrower* than
"clause-for-clause": it is the **presence + type-gate** check (forms folds ModelForm-ness
into one gate; the serializer has two gates — `Serializer` and `ModelSerializer`), the
`_resolve_model` chain, and the "resolves no model" raise.

**Lever:** promote `require_backing_class(name, meta, *, key, expected, base_label) -> type`
and `resolve_backed_model_or_raise(cls, meta, *, base_label, noun) -> model`. Do NOT template
the whole method — the serializer's tail (`get_serializer_for_schema`, `optional_fields`,
`injected_fields`, `select_for_update`, `nested_fields`, `schema_fingerprint`) is genuinely
flavor-shaped. Consolidate the two clauses, not the matrix.

### M6 — The generated-input type-name skeleton, three copies — **Verdict: REAL**

`mutations/inputs.py::mutation_input_type_name`, `forms/inputs.py::form_input_type_name`, and
`rest_framework/inputs.py::serializer_input_type_name` share the load-bearing skeleton:

```
base = <X>.__name__
suffix = "PartialInput" if <partial> else "Input"
if <full-shape>:  return f"{base}{suffix}"
return f"{base}{<token concat>}{suffix}"
```

The suffix rule is identical modulo spelling (mutation writes `"Input" if CREATE else
"PartialInput"`; form/serializer write `"PartialInput" if PARTIAL else "Input"` — same
partial-vs-not branch). Real per-flavor deltas: mutation + form derive the token as
`_pascalize_token` over `sorted(effective_field_names)` and compute the full-shape predicate
as `frozenset(effective) == frozenset(full)` in-function; the serializer takes
`is_full_shape` as a **parameter** and derives the token from `_shape_token(...)` (a sha1
descriptor digest, not just names).

**Lever:** `utils/inputs.py::generated_input_type_name(base_name, operation_kind, *,
is_full_shape, token) -> str` with the PARTIAL/Input suffix rule single-sited; each flavor
computes its own `token`. Pairs naturally with Md5 (`_pascalize_token` relocation, corrected
below) — do them together. The injective-token contract must not drift: within a flavor a
name collision is the AR-M6 raise (`_pascalize_token` is already single-sited in
`mutations/inputs.py` and imported by the other two, so the encoder itself is shared).

---

## MEDIUM

### Md1 — `guard_create_required_fields` vs `guard_create_required_serializer_fields` — **Verdict: REAL**

Same shape: required-names set − effective set (− injected, serializer only) → sorted →
raise. Wording near-identical: `"<Flavor> create input for {name} drops required … field(s)
{dropped!r} via Meta.fields / Meta.exclude"`. Real deltas (all as claimed): the bases differ
(`_required_form_field_names` over `base_fields`/`field.required` vs
`_required_writable_field_names` over the writable `field_map`); the serializer alone
subtracts `injected_fields` and threads a `field_map`. The form's partial column-less guard
(`guard_partial_required_column_less_fields`) is a **separate, load-bearing** function
(scoped to `_model_column_for(...) is None`, per its own docstring) — leave it. The
serializer docstring already cites the form function as its "per-declaration precedent," so
the parallel is acknowledged in-source. **Lever:** a shared
`guard_dropped_required(required, effective, *, waived, flavor, recourse)` core.

### Md2 — Five `*_ASYNC_RECOURSE` constants, one sentence — **Verdict: REAL**

The three pipeline constants are **byte-identical except the subject**:

> `_MUTATION_ASYNC_RECOURSE`: "A **DjangoMutation** runs its ORM pipeline synchronously … cannot await an async get_queryset hook; redefine the target type's get_queryset as a sync method."
> `_FORM_ASYNC_RECOURSE`: "A **form mutation** runs its ORM pipeline synchronously …" (identical tail)
> `_SERIALIZER_ASYNC_RECOURSE`: "A **serializer mutation** runs its ORM pipeline synchronously …" (identical tail)

The other two genuinely differ and must be left: `utils/querysets.py::_RELAY_ASYNC_RECOURSE`
offers a two-way "invoke from an async resolver, OR redefine" recourse (async IS possible on
the Relay path); `mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE` is about
`has_permission`/`check_permission`, not `get_queryset`. **Lever:**
`utils/querysets.py::sync_pipeline_recourse(flavor_noun: str)` template for the three pipeline
flavors only.

### Md3 — "Resolve the related primary → visibility queryset or default manager", four spellings — **Verdict: REAL (shallow echo)**

The `related_type = registry.get(related_model)` → None-branch-vs-
`visibility_scoped_related_queryset` skeleton appears at all four sites, with **divergent
None-handling** at each:

- `utils/querysets.py::visible_related_object` — None → `_default_manager.filter(pk=pk).first()`
- `utils/querysets.py::visible_related_objects` — None → `_default_manager.all()`
- `mutations/resolvers.py::_raw_pk_relation_error` — None → M2M existence check, FK → skip (`return None`)
- `rest_framework/resolvers.py::_scope_specs_over_serializer` — None → `continue` (skip)

Because the None-branch is different at every site, this is a **shallow structural echo**,
not a copy that collapses trivially. **Lever:** a
`related_visibility_queryset(related_model, info, recourse) -> QuerySet | None` primitive in
`utils/querysets.py` (None = "no contract"); each site keeps its own None-handling explicit.
This is the visibility contract — the one place a drift is a data-leak bug class.

### Md4 — The stringified-pk subset membership check — **Verdict: REAL (one axis, not four-way)**

The `{str(pk) …} <= present` subset-membership contract has **two homes**:

```python
# Home 1 — mutations/resolvers.py::_relation_membership_error
present = {str(pk) for pk in queryset.filter(pk__in=query_pks).values_list("pk", flat=True)}
if not {str(pk) for pk in declared_pks} <= present: return _relation_error(field_name)
# Home 2 — utils/querysets.py::visible_related_objects returns the stringified visible set:
return {str(pk) for pk in queryset.filter(pk__in=list(pks)).values_list("pk", flat=True)}
#         …and rest_framework/resolvers.py::_decode_relation_multi does the compare inline:
if not {str(pk) for pk in pks} <= visible: return None, _relation_field_error(graphql_name)
```

**Scoping note:** on the model side `_relation_membership_error` is *already* single-sited
across its three callers (`_relation_visibility_error`, `_raw_pk_relation_error`,
`_relation_existence_error`), per its own docstring. So the true duplication is **one axis**
— model-home vs serializer-home — not the four-way spread a naive read suggests. **Lever:**
fold the serializer's inline subset test into a promoted membership primitive next to
`visible_related_objects` so the coercion-compare rule is written once.

### Md5 — `_pascalize_token` has three consumers — **Verdict: PARTIALLY REAL (destination corrected)**

The duplication is **real**: `_pascalize_token` is defined once in `mutations/inputs.py` and
imported by private name from **both** `forms/inputs.py` AND `rest_framework/inputs.py` — a
cross-subsystem private-name import ×2, three consumers total.

**But the proposed lever was wrong and is retracted.** The finding said "move it next to
`pascal_case`" in `utils/strings.py`. Source refutes this: `mutations/inputs.py` carries an
explicit deliberate-siting comment stating `_pascalize_token` is intentionally **NOT**
`pascal_case` — they produce different output (`is_private` → `Isprivate` vs `IsPrivate`),
and that difference is **injectivity-critical** for the generated-name contract. Co-locating
it beside `pascal_case` invites exactly the wrong-function substitution the comment guards
against. The maintainer's own in-source flag (`forms/inputs.py::form_input_type_name`
docstring) points the consolidation at **`utils/inputs.py`**, not `utils/strings.py`.

**Corrected lever:** promote `_pascalize_token` to `utils/inputs.py` (rename public,
`pascalize_token`), where it sits with the other input-name machinery it's part of, and keep
it visibly distinct from `pascal_case`. Do this together with M6.

### Md6 — `graphql_camel_name` location — **Verdict: PARTIALLY REAL (premise corrected)**

The **location fact is real**: `graphql_camel_name` is defined in `utils/inputs.py`, re-
exported as `_camel_case` by `filters/inputs.py` and `orders/inputs.py`, and imported
directly by `mutations/resolvers.py`, `forms/inputs.py`, `mutations/inputs.py`,
`rest_framework/inputs.py`, and `rest_framework/serializer_converter.py`.

**But the finding's premise is false and is retracted.** It claimed "`utils/strings.py`
declares itself the single home for case conversion," making `graphql_camel_name`'s location
a violation. The actual `utils/strings.py` docstring says only that a *new case style*
(kebab, SCREAMING_SNAKE) should be added there rather than re-derived inline — it makes **no
single-home claim**, and `to_camel_case` is used directly from `strawberry.utils` elsewhere
(`types/finalizer.py`). So there is no invariant being violated.

**Downgraded recommendation:** this is a **judgment call, not a defect.** `graphql_camel_name`
is a GraphQL-naming concern with five in-package consumers; leaving it in `utils/inputs.py`
(the input-naming module) is defensible. If it moves, move it *with* Md5 to keep the naming
primitives together — but there is no correctness or stated-invariant reason to. Consider
this the weakest item in the review.

### Md7 — The default construction-kwargs hooks are the same three lines — **Verdict: REAL**

```python
# forms/sets.py::_default_get_form_kwargs
kwargs = {"data": data, "files": files}
if instance is not None: kwargs["instance"] = instance
return kwargs
# rest_framework/sets.py::SerializerMutation.get_serializer_kwargs
kwargs = {"data": data}
if instance is not None: kwargs["instance"] = instance
return kwargs
```

The `if instance is not None: kwargs["instance"] = instance` clause is byte-identical; the
only delta is the `"files": files` entry (serializers have no files kwarg). **Lever:** a tiny
`construction_kwargs(instance=None, **base) -> dict`. Low value alone; belongs to the M1
"flavor plumbing kit."

---

## MINOR

### Mn1 — Three one-line aliases of `relation_field_error` — **Verdict: REAL**

`mutations/resolvers.py::_relation_error`, `forms/resolvers.py::_relation_field_error`, and
`rest_framework/resolvers.py::_relation_field_error` are each a single `return
relation_field_error(...)` body carrying a ~7–10-line docstring. Delete all three; call
`relation_field_error` directly (fold the provenance content into the shared ctor).

### Mn2 — The `{"create": CREATE, "update": PARTIAL}` map, three spellings — **Verdict: REAL**

`mutations/sets.py::_OPERATION_INPUT_KIND` and
`rest_framework/sets.py::_SERIALIZER_OPERATION_INPUT_KIND` are identical dict literals
(`{"create": CREATE, "update": PARTIAL}`); `forms/sets.py::_modelform_operation_kind` is the
function form (`return CREATE if meta.operation == "create" else PARTIAL`). One
`NON_DELETE_OPERATION_INPUT_KIND` map exported from `mutations/sets.py` serves all three.

### Mn3 — The two field-sequence re-binding wrappers P2.7 argued against — **Verdict: REAL**

`mutations/sets.py::_normalize_field_sequence` and
`forms/inputs.py::normalize_form_field_sequence` are thin flavor-label re-bindings of
`utils/inputs.py::normalize_field_name_sequence`. The serializer flavor deliberately added
**no** third wrapper, and says so in three separate P2.7 in-source notes (two in
`rest_framework/inputs.py`, two in `rest_framework/sets.py`) holding up "no per-flavor
wrapper" as the correct style. Inline the flavor arg at the model/form call sites and delete
both wrappers (check the suite doesn't address them by module path first).

### Mn4 — `_reverse_map_for` and `_join_path` micro-wrappers (serializer) — **Verdict: REAL (split)**

`rest_framework/resolvers.py::_reverse_map_for` is a one-liner over
`_build_reverse_map(mutation_cls._input_field_specs)` with **exactly one** call site — a fair
inline candidate. `_join_path` is **not** — it carries real branching (`f"{prefix}.{segment}"
if prefix else segment`) and has **five** callers; it earns its keep. Fold `_reverse_map_for`
on contact; leave `_join_path`.

### Mn5 — `input_type_name` re-builds the whole serializer shape — **Verdict: REAL**

`rest_framework/sets.py::SerializerMutation.input_type_name` calls
`build_serializer_input_class(...)` a **second time** (after `build_input` already built the
identical shape) purely to `return shape.type_name` — the docstring admits it. The shape
cache makes it near-free, so it is not *wrong*, just a re-derivation two seams apart. The form
flavor solved the same seam more cheaply: `forms/sets.py::input_type_name` calls
`_form_input_type_name_for(...)` → the pure `form_input_type_name(...)` deriver, without
rebuilding the class. **Lever:** stash the built shape's `type_name` at bind (like
`_input_field_specs`) so the name seam reads, not rebuilds. Efficiency/clarity more than DRY.

---

## Consolidation strategy (if/when implemented)

Order matters — do the utils/ landings first so the flavor edits are pure deletions:

1. **Relocation** (Md5, corrected): move `_pascalize_token` into `utils/inputs.py` (public
   `pascalize_token`, kept distinct from `pascal_case`); keep an import-path alias. Md6 is a
   judgment call — bundle only if Md5 moves.
2. **New utils primitives**: M2's `iter_provided_input_fields`, M4's
   `resolve_effective_fields`, M6's `generated_input_type_name`, Md3's
   `related_visibility_queryset`, Md2's `sync_pipeline_recourse`, Md4's membership primitive.
3. **Promotions inside `mutations/`**: M1's async-entry + classmethod-seam factories (the
   model/form sync pair; leave the serializer sync entry), M3's `type_check_relation_id`,
   M5's `require_backing_class` + `resolve_backed_model_or_raise`, Md1's guard core, Mn2's
   operation-kind map.
4. **Flavor rewires + deletions** (forms, rest_framework, then the model call sites; Mn1/Mn3/
   Mn4-`_reverse_map_for` fold in here).
5. Each step is independently shippable; suite must stay green (byte-identical error messages
   where tests pin wording — the flavor-label parameterization pattern preserves that).

## Considered and deliberately NOT recommended

- **Merging the three decode kind-handlers into one dispatch table** (beyond M2's walk): the
  model's null/naive-datetime checks, the form's `files=`/`empty_values`/`to_field_name`
  semantics, and the serializer's nested recursion are flavor CONTRACTS, not mechanics.
- **A whole-`_validate_meta` template method** (see M5): clause ordering is flavor-semantic;
  the serializer appends a fingerprint tail. Consolidate the two prologue clauses, not the
  matrix.
- **Unifying the plain-form `{ ok errors }` body into `run_write_pipeline_sync`**: F6 in the
  skeleton's own docstring scopes it out (no instance, no slot, no re-fetch).
- **Collapsing the serializer sync entry into the M1 factory**: verified — it is a genuinely
  different shape (direct `run_write_pipeline_sync` with lambdas, no dispatcher). Only the
  async trio + the model/form sync pair are safe to factor.
- **`_decode_relation_id_set` (model) vs the form/serializer decoders**: the model path's
  raw-pk-set semantics (batched all-or-nothing visibility) are deliberately different; only
  the GlobalID structural half (M3) is shared mechanics.
- **The `materialize_*_input_class` / `clear_*_namespace` thin wrappers ×3**: they already
  ride `make_input_namespace`; the wrappers are documented docstring carriers the tests
  address by name. Keeping them is the documented pattern.
- **Md6 as a defect**: retracted — no stated single-home invariant exists; it is a judgment
  call, not a violation.
- **`utils/querysets.py::initial_queryset` as a FilterSet seed**: verified-and-rejected in a
  prior cycle (owner model may be a subclass) — do not re-flag.

## Method / caveats

- Every finding above was re-verified against source after the first pass by reading the
  named symbols directly. Verdicts and proof excerpts are quoted from the actual code.
- Corrections applied this pass: M1(a) sync-entry miscount (only 2 true parallels); M4 read-
  only drop is inside the fn, not at the call site; M5 three clauses already shared (residual
  duplication is narrower); Md4 is one axis, not four-way; **Md5 destination corrected**
  (`utils/inputs.py`, not `pascal_case` — the two encoders are deliberately, injectivity-
  critically distinct); **Md6 premise retracted** (`utils/strings.py` makes no single-home
  claim; downgraded to a judgment call).
- Nothing here is a behavior change; every surviving lever is a relocation/parameterization
  of code whose divergences are named strings or basis dicts. Where a divergence is semantic
  (M3 model raw-pk path, Md1 partial guard, the decode tails) it is called out as NOT to be
  merged.
- Error-message wording is test-pinned in places — the flavor-label parameter pattern
  (`normalize_field_name_sequence`) is the template for preserving byte-identical messages
  through consolidation.
