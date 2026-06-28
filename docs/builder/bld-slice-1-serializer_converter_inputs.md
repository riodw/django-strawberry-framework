# Build: Slice 1 — DRF-field → Strawberry input mapping + the serializer-derived input generator

Spec reference: `docs/spec-039-serializer_mutations-0_0_13.md` (Slice checklist lines 624-748;
governing design Decision 7 lines 1763-2092, Decision 12 lines 2475-2591, Cross-flavor reuse /
DRY obligations lines 2697-2899, Test plan lines 3104-3222, Definition of done item 2 lines
3514-3544)
Status: final-accepted

## Plan (Worker 1)

### Scope summary (what this slice ships, and the cross-slice boundary it must not cross)

Slice 1 ships **two new package-internal modules** plus **four net-new shared-helper promotions**
into existing modules:

- `rest_framework/serializer_converter.py` — `convert_serializer_field(field, *, is_input=True)`
  (fail-loud MRO-walk dispatch + raising fallthrough; NOT `singledispatch` + `Field → String`),
  the `input_attr → (serializer_field_name, source, kind)` reverse map with the `source` axis and
  the id-like-suffix rule.
- `rest_framework/inputs.py` — `<Serializer>Input` (create) + `<Serializer>PartialInput` (update)
  from the serializer's **schema-time field set** (`get_serializer_for_schema()` hook), under a
  `SerializerInputShape` descriptor identity, with `guard_create_required_serializer_fields`.
- **Promotions authored this slice** (the Slice-1-labeled anchors): P1.4 (`utils/converters.py::convert_with_mro`
  + re-point `forms/converter.py`), P2.1 (`utils/inputs.py::InputFieldSpec`), P2.2
  (`utils/inputs.py::make_input_namespace` + re-point `forms/inputs.py` and `mutations/inputs.py`),
  P1.3 (`utils/inputs.py::make_shape_build_cache`). P2.3 (`_pascalize_token`) is reused by import.

**Cross-slice boundary (load-bearing — see Notes for Worker 1, flag SR-1).** The Slice 1 DRY/reuse
bullet (spec line 744) names P1.3 (`make_shape_build_cache`) as a Slice-1 reuse for the serializer
shape cache. But the cache **consumer** for the serializer flavor (`cached_build_input` /
`build_and_stash_input`, P1.7) and the bind that drives it (`rest_framework/sets.py`) are
**Slice 2** (spec lines 856-873; staged anchors `mutations/sets.py:104`, `forms/sets.py:147`,
`registry.py:53` all carry `Slice 2` labels). So in Slice 1:

- `rest_framework/inputs.py` exposes **callable, finalizer-free generators** (the `forms/inputs.py`
  shape: `build_serializer_inputs(...)`, `build_serializer_input_class(...)`,
  `guard_create_required_serializer_fields(...)`, `materialize_serializer_input_class(...)`,
  `clear_serializer_input_namespace()`, the `SerializerInputShape` descriptor + its name
  derivation) — exactly the role `forms/inputs.py` plays (its docstring: "No metaclass, no
  resolver, no finalizer wiring lives here … the generators here are callable and unit-testable in
  isolation; Slice 2 calls them from the bind").
- Slice 1 **authors `make_shape_build_cache()`** in `utils/inputs.py` (the P1.3 helper) because the
  `utils/inputs.py:53` anchor is Slice-1-labeled, but **does not** wire a serializer
  `cached_build_input` consumer or re-point `forms/sets.py` — that is Slice 2's `_form_shape_build_cache`
  re-point (anchor `forms/sets.py:147`, `Slice 2`). The serializer shape cache is *consumed* in
  Slice 2's `sets.py`. Slice 1 ships the helper + a unit test that it returns a dict + a clear
  callback; it does **not** register the clear (registration is `register_subsystem_clear`, P1.6,
  Slice 2).

This split matches the form precedent exactly: `forms/inputs.py` (Slice-1 of spec-038) shipped the
generators; `forms/sets.py` (Slice-2 of spec-038) shipped `_cached_build_form_input`.

### DRY analysis

This slice's whole risk is being **the third divergent copy** of the converter + input generator.
The spec pins six DRY obligations touching Slice 1 (P1.3, P1.4, P2.1, P2.2, P2.3, plus P3 named
import obligations). Each is resolved below: whether it **exists today** (reuse) or is a **net-new
promotion this slice authors**, the single owning module, how the new modules import-not-redefine,
and the grep-guard DoD check.

#### Existing patterns reused (cite source)

- **`mutations/inputs.py::_pascalize_token`** (`mutations/inputs.py` lines 304-323) — the injective
  single-leading-capital token encoder for divergent-shape suffixes. **Exists today; reuse by
  import (P2.3).** `forms/inputs.py:57` already imports it; `rest_framework/inputs.py` imports it
  the same way for the `SerializerInputShape`-derived name. The `mutations/inputs.py:326` anchor
  ("Keep serializer divergent-shape naming on this token helper, or promote it to `utils.inputs`")
  is satisfied by *keeping* it on `mutations/inputs.py` (the form flavor already imports it from
  there; no third encoder, no premature move). **Do not** add a PascalCase encoder under
  `rest_framework/`.
- **`utils/inputs.py::build_strawberry_input_class`** (lines 126-184) and
  **`materialize_generated_input_class`** (lines 187-223) — the build + materialize-ledger core
  (the latter's ledger gives the collision raise for free). **Exist today; reuse by import.**
- **`utils/inputs.py::graphql_camel_name`** (lines 67-77) and **`normalize_field_name_sequence`**
  (lines 80-123, keyword-only `flavor=`) — camel-name + `Meta.fields`/`exclude` shape normalization.
  **Exist today; reuse by import** (P3 named import obligations; the serializer calls
  `normalize_field_name_sequence(..., flavor="SerializerMutation")` directly — no third re-binding
  wrapper).
- **Read-side converters `types/converters.py::{scalar_for_field, convert_scalar,
  convert_choices_to_enum}`** (lines 249, 272, 493). **Exist today; reuse by import**, keyed on the
  **backing `models.Field` resolved via `source`** for a `ModelSerializer` column (the symmetric
  wire contract), exactly the `forms/inputs.py::_field_triple_and_spec` discipline (lines 384-451).
- **`mutations/inputs.py::relation_input_annotation`** (lines 249-286) — the
  `(python_attr, graphql_name, annotation)` Relay-`GlobalID`-vs-raw-pk relation id triple for a
  model-column-backed relation. **Exists today; reuse by import** for the `ModelSerializer`
  FK-backed relation. The **serializer-only relation** (`field.queryset.model`, F4) follows the
  `forms/inputs.py::_model_less_relation_annotation` precedent (lines 328-369) — but that is a
  `forms`-local helper, so the serializer flavor writes its own thin `queryset.model`-keyed
  analog (genuinely-new; see "New helpers justified").
- **`utils/relations.py::{relation_kind, is_forward_many_to_many, is_many_side_relation_kind}`**
  (lines 38, 88, 83) — for the **backing** model-relation read the converter does via `source`,
  not re-derived from DRF's `many` / `source` flags (P3). **Exist today; reuse by import.**
- **`scalars.Upload`** + **`exceptions.ConfigurationError`** — reuse by import.
- **`types/relay.py::implements_relay_node`** — the Relay-shape check both
  `relation_input_annotation` and `_model_less_relation_annotation` already use. Reuse by import for
  the serializer-only relation id-type decision.

#### Net-new promotions this slice authors (the P-obligations; each is a staged Slice-1 anchor)

| P | Helper | Exists today? | Single owning module | How the new modules import-not-redefine |
| --- | --- | --- | --- | --- |
| **P1.4** | the fail-loud dispatch **skeleton** `convert_with_mro(field, *, isinstance_prechecks, scalar_registry, fallthrough_error_factory) → conversion` | **No** — net-new. `utils/converters.py` is a 17-line stub holding only the `TODO(spec-039 Slice 1)` anchor; `forms/converter.py::convert_form_field` (lines 160-246) is a free-standing skeleton importing nothing from `utils/`. | `utils/converters.py` (the anchor names this home; Decision 4 confirms). | `serializer_converter.py` and `forms/converter.py` BOTH call `convert_with_mro(...)`, supplying only their precheck table + scalar registry + `ConfigurationError` fallthrough factory. The GOAL-mandated no-silent-`String`-catch-all contract single-sites here. |
| **P2.1** | the unified `InputFieldSpec` (`input_attr`, `graphql_name`, `target_name`, `kind`, optional `source`) + a shared conversion-result shape | **No** — net-new. Today `utils/inputs.py::GeneratedInputFieldSpec` (lines 39-50, set-family, `django_source_path`), `forms/converter.py::FormInputFieldSpec` (lines 65-87, `form_field_name` + `kind`) + `FormFieldConversion` (lines 90-113, `__slots__`) are three separate shapes. | `utils/inputs.py` (the `utils/inputs.py:53` anchor). | The serializer reverse-map spec **is** the promoted `InputFieldSpec` (the `038` `FormInputFieldSpec` analog + the `source` axis). Minimal-blast-radius choice (see discretion D1): define `InputFieldSpec` in `utils/inputs.py` and have the serializer reverse-map use it directly; the form flavor's `FormInputFieldSpec` re-point is permitted but its byte-equivalent test suite must stay green (the spec's P2.1 floor is "at minimum **site the serializer spec in `utils/inputs.py`**"). |
| **P2.2** | the input-namespace **one-ledger** trio `make_input_namespace(module_path, family_label) → (ledger, materialize_fn, clear_fn)` | **No** — net-new. Today `mutations/inputs.py` (lines 97-147) and `forms/inputs.py` (lines 105-167) hand-mirror the four-part lifecycle. | `utils/inputs.py` (the `utils/inputs.py:53` + `forms/inputs.py:112` anchors). | `rest_framework/inputs.py` gets its `(_materialized_names, materialize_serializer_input_class, clear_serializer_input_namespace)` from `make_input_namespace(SERIALIZER_INPUTS_MODULE_PATH, "SerializerMutation")`. **MUST be the one-ledger form/mutation shape, NOT the heavier `clear_generated_input_namespace`** (lines 299-358, which resets a factory cache + per-set `_lifecycle` the serializer has none of — explicitly called out at spec line 2792). `forms/inputs.py` + `mutations/inputs.py` re-point to the same helper (their `materialize_*` / `clear_*` public names unchanged), keeping their suites byte-equivalent. |
| **P1.3** | `make_shape_build_cache() → (cache_dict, clear_fn)` | **No** — net-new. Today `mutations/sets.py::_shape_build_cache` (line 134) and `forms/sets.py::_form_shape_build_cache` + `clear_form_shape_build_cache` (lines 145-163, commented "twin of") are hand-mirrored. | `utils/inputs.py` (the `utils/inputs.py:53` anchor lists it). | **Authored** in Slice 1 (helper + a unit test that it returns a dict + clear). The serializer cache *consumer* is Slice 2 (`rest_framework/sets.py`); the `forms/sets.py:147` re-point is Slice 2 (anchor-labeled). Slice 1's only obligation is that the helper exists and the `SerializerInputShape` descriptor identity (legitimately new) is shaped so a future `cached_build_input` keys on it. See SR-1. |
| **P2.3** | `_pascalize_token` | **Yes** — `mutations/inputs.py:304`. | `mutations/inputs.py`. | Reuse by import (above). |

#### New helpers justified (genuinely new, not a promotion)

- **`SerializerInputShape` descriptor** (`rest_framework/inputs.py`) — the ordered tuple of each
  emitted field's `(input_attr, GraphQL annotation, required/default state, serializer_field_name,
  source, kind)` + the normalized `optional_fields` set for create. **Legitimately new** (spec line
  2083): the `036`/`038` name-only `(class, op, frozenset(names))` identity is insufficient because
  (1) `optional_fields` changes requiredness without changing the name set, and (2) the schema-time
  hook can return same-named fields with different classes/`source`/kind. Single responsibility:
  drive the per-shape cache key, the generated-name derivation, and the materialize collision check
  from one source of truth. Its *cache+clear plumbing* is P1.3 (shared); the *descriptor* is new.
- **`get_serializer_for_schema()` default discovery** (`rest_framework/inputs.py` module-level
  function; the classmethod hook on the base is Slice 2) — default no-arg `serializer_class()` then
  read `.fields`, with the **loud-rejection guard wrapping the `.fields` materialization, not the
  constructor** (Decision 7 lines 1771-1796: DRF builds `.fields` lazily, so a context-requiring
  serializer raises at first `.fields` access, not at construction). Single responsibility: the
  `forms/inputs.py::get_form_fields` (lines 170-183) analog adapted to DRF's lazy `.fields`. New
  because DRF's lazy-`.fields` semantics differ from Django forms' eager `base_fields`.
- **`guard_create_required_serializer_fields(...)`** (`rest_framework/inputs.py`) — the DRF-adapted
  analog of `forms/inputs.py::guard_create_required_fields` (lines 568-597). New body (DRF's
  `field.required` + `field.default` + `read_only`/`HiddenField` exemption differ from Django form
  fields) but the **same per-declaration-before-cache-lookup discipline**.
- **serializer-only relation id-type resolver** (`rest_framework/serializer_converter.py`) — the
  `field.queryset.model` (F4) analog of `forms/inputs.py::_model_less_relation_annotation` (lines
  328-369). New because the form helper is keyed on `forms.ModelChoiceField.queryset`; the DRF field
  exposes `queryset.model` / `child_relation`. Reuses `implements_relay_node` + `scalar_for_field`.
- **`_guard_serializer_input_attr_collisions(...)`** (`rest_framework/inputs.py`) — the serializer
  analog of `forms/inputs.py::_guard_input_attr_collisions` (lines 454-496): two declared fields
  colliding on one generated GraphQL name (`category`→`categoryId` vs literal `category_id`→`categoryId`;
  `foo_bar`+`fooBar`→`fooBar`) raise **before materialization**, AND two **writable** fields sharing
  one one-segment `source` raise (no double-write of one model attr; a `read_only` field sharing a
  `source` with a writable one is accepted because read-only is dropped). The DRF `source`-collision
  arm is new (forms have no `source` axis).

#### Duplication risk avoided

- **Risk: a fourth divergent dispatch skeleton.** Naive impl would copy `convert_form_field`'s
  isinstance-prechecks → MRO-walk → raise into `serializer_converter.py`. Avoided by P1.4: both
  converters call `convert_with_mro`. DoD grep guard below.
- **Risk: a third hand-mirrored input namespace.** Avoided by P2.2 `make_input_namespace`; the
  serializer never spells its own `_materialized_names` + `materialize_*` + `clear_*` quartet.
- **Risk: reaching for `clear_generated_input_namespace` (the heavy set-family clear).** Avoided
  explicitly (spec line 2792); the serializer clear is the one-ledger `.clear()` shape.
- **Risk: a third reverse-map dataclass.** Avoided by P2.1 `InputFieldSpec`.
- **Risk: re-deriving the relation kind from DRF's `many`/`source` flags for a backing model
  relation.** Avoided by reusing `utils/relations.py` keyed on the resolved `models.Field`.

#### DoD grep guards (the import-not-redefine contract; Slice 1 DoD line 735-748, import manifest
lines 2887-2893)

A passing slice satisfies all of:

```shell
# P1.4: both converters call the shared skeleton; the serializer converter does NOT
#        re-spell an MRO walk or a raising fallthrough.
grep -n 'convert_with_mro' django_strawberry_framework/rest_framework/serializer_converter.py   # >=1 hit
grep -n 'convert_with_mro' django_strawberry_framework/forms/converter.py                       # >=1 hit
grep -nE '__mro__' django_strawberry_framework/rest_framework/serializer_converter.py           # 0 hits
# P2.2 / P2.1: the serializer input module imports the promoted trio + spec, redefines neither.
grep -nE 'make_input_namespace|materialize_generated_input_class|build_strawberry_input_class|InputFieldSpec|make_shape_build_cache|graphql_camel_name|normalize_field_name_sequence' \
  django_strawberry_framework/rest_framework/inputs.py                                            # imports present
grep -nE '_materialized_names *[:=] *\{\}' django_strawberry_framework/rest_framework/inputs.py  # 0 hits (no hand-rolled ledger literal)
# P2.3: the divergent-shape suffix reuses _pascalize_token, no new encoder.
grep -n '_pascalize_token' django_strawberry_framework/rest_framework/inputs.py                  # >=1 hit
grep -niE 'def .*pascal|\.capitalize\(\)' django_strawberry_framework/rest_framework/inputs.py   # 0 hits
# import manifest: serializer_converter.py imports only the listed reuse surface.
grep -nE '^from|^import' django_strawberry_framework/rest_framework/serializer_converter.py
```

The form + mutation suites must stay byte-equivalent after the P1.4 / P2.1 / P2.2 re-points
(behavior-preserving promotion; spec lines 3295-3302). Verification step in Test additions.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing.

1. **P1.4 — author `utils/converters.py::convert_with_mro`** (replaces the stub + anchor at
   `utils/converters.py:1-17`). Signature `convert_with_mro(field, *, isinstance_prechecks:
   list[tuple[type | tuple[type,...], Callable]], scalar_registry: dict[type, Any],
   fallthrough_error_factory: Callable[[object], Exception]) → <conversion>`. Body: run prechecks in
   order (first non-`None` wins), then `type(field).__mro__` walk over `scalar_registry`, then raise
   `fallthrough_error_factory(field)`. Pure; no DRF, no Django-forms import. Match the exact
   ordered-precheck → MRO-walk → raise control flow of `forms/converter.py::convert_form_field`
   (lines 192-246) so behavior is identical.

2. **P1.4 re-point — `forms/converter.py::convert_form_field`** (re-point block at lines 116-126;
   the function at 160-246). Delegate to `convert_with_mro(...)` after the form-specific extraction:
   pass `[ (forms.ModelMultipleChoiceField, …RELATION_MULTI…), (forms.ModelChoiceField, …RELATION_SINGLE…),
   (forms.FileField, …FILE…), (forms.MultipleChoiceField, …list[str]…) ]` as prechecks,
   `_SCALAR_FORM_FIELDS` as the registry, and `_unsupported_form_field` as the fallthrough. **Keep
   the exact current behavior:** base `forms.Field` stays an exact-type special case → `str`
   (precheck or post-walk, whichever keeps byte-equivalence), unsupported custom subclasses still
   raise `ConfigurationError` with the same message. (This is a P1.4 re-point Worker 2 may sequence
   inside Slice 1; if it grows the diff too large it is a candidate to defer to the integration pass
   per the spec's "re-point the forms copy" language — see discretion D2.)

3. **P2.1 — author `utils/inputs.py::InputFieldSpec`** (at the `utils/inputs.py:53` anchor). Frozen
   dataclass: `input_attr: str`, `graphql_name: str`, `target_name: str`, `kind: str`, `source: str
   | None = None`. Docstring: the `038` `FormInputFieldSpec` analog generalized — `target_name` is
   the per-flavor write-back key (form field name for forms, declared serializer field name for the
   serializer); `source` is the serializer-only extra axis (None for forms). Also unify the
   conversion result into one shared shape (the `FormFieldConversion` analog: `annotation` + `kind`
   + `required`), or reuse `FormFieldConversion` — see discretion D1.

4. **P2.2 — author `utils/inputs.py::make_input_namespace`** (at the `utils/inputs.py:53` anchor).
   `make_input_namespace(module_path, family_label) → (ledger: dict[str,type], materialize_fn,
   clear_fn)`. `materialize_fn(name, cls)` calls `materialize_generated_input_class(name, cls,
   module_path=module_path, family_label=family_label, ledger=ledger)`; `clear_fn()` does
   `ledger.clear()` (the one-ledger shape, NOT `clear_generated_input_namespace`).

5. **P2.2 re-point — `forms/inputs.py` (lines 105-167) and `mutations/inputs.py` (lines 97-147)** to
   `make_input_namespace`. Public names (`materialize_form_input_class` /
   `clear_form_input_namespace`; `materialize_mutation_input_class` /
   `clear_mutation_input_namespace`) unchanged — they become thin wrappers over the returned
   callbacks. Form + mutation suites stay green unchanged.

6. **P1.3 — author `utils/inputs.py::make_shape_build_cache`** (at the `utils/inputs.py:53` anchor).
   `make_shape_build_cache() → (cache: dict, clear_fn)`. Pure plumbing; no registration. (Slice 2
   re-points `forms/sets.py::_form_shape_build_cache` and adds the serializer consumer; Slice 1 only
   authors the helper + a unit test.)

7. **`rest_framework/serializer_converter.py`** (replace stub + anchor at lines 1-31). Guard DRF
   import first (Slice 0 added the dev dep; the `require_drf()` guard itself is Slice 2, so Slice 1
   imports DRF directly under a module-top `from rest_framework import serializers` — DRF is present
   in the test env; the soft-import guard wiring is Slice 2, anchor `rest_framework/__init__.py:3`).
   Implement `convert_serializer_field(field, *, is_input=True)`:
   - `is_input` is **accepted-and-ignored** — threaded for graphene-parity, **no `if not is_input:`
     branch** (spec lines 1976-1988; a dead branch would gate-fail `fail_under=100`).
   - isinstance prechecks (relation first, then file): `PrimaryKeyRelatedField`(`many=True`) /
     `ManyRelatedField` → `relation_multi`; `PrimaryKeyRelatedField` → `relation_single`;
     `FileField`/`ImageField` → `file`. Reject nested `ModelSerializer`/`ListSerializer` (the `036`
     nested-write non-goal). `ListField`: scalar child → `list[<scalar>]` recursively through the
     same scalar registry; relation/nested child → `ConfigurationError`. `MultipleChoiceField` →
     `list[str]`.
   - scalar registry MRO walk via `convert_with_mro`: `CharField`/`EmailField`/`SlugField`/`URLField`/
     `RegexField` → `str`; `ChoiceField` → `str`; `IntegerField` → `int`; `FloatField` → `float`;
     `DecimalField` → `Decimal`; `BooleanField` → `bool`; `UUIDField` → `uuid.UUID`;
     `DateField`/`DateTimeField`/`TimeField` → python-native; `JSONField` →
     `strawberry.scalars.JSON`.
   - raising fallthrough: an unmapped `serializers.Field` subclass → `ConfigurationError` naming the
     field + class.
   - **Nullability (M2):** annotation nullability follows `field.allow_null` (orthogonal to
     requiredness); the converter does not fabricate a GraphQL default for a `required=False`+`default`
     field. `allow_blank` is not encoded.
   - **Reverse map + `source` (Decision 7 lines 1855-1924):** GraphQL name from the **declared field
     name** via the id-like-suffix rule (`category`→`categoryId`, `category_id`→`categoryId`,
     `category_pk`→`categoryPk` — no doubled `…IdId`/`…PkId`; non-relation scalar camel-cased with no
     suffix via `graphql_camel_name`). Backing `models.Field` resolved by **`source`** (one-segment
     or omitted). Dotted `source`/`source="*"` on a model-column-converting field →
     `ConfigurationError`. Serializer-only relation resolves target from `field.queryset.model`; a
     relation with neither backing column nor concrete `queryset.model` → `ConfigurationError`. A
     relation target with no registered primary `DjangoType` → class-creation `ConfigurationError`
     naming field + target model (M3; stricter than the form fallback, which is left byte-unchanged).
     Reverse map preserves the **declared serializer field name** as the write-back key.

8. **`rest_framework/inputs.py`** (replace stub + anchor at lines 1-28). Module-level
   `SERIALIZER_INPUTS_MODULE_PATH = "django_strawberry_framework.rest_framework.inputs"`. Get the
   namespace trio from `make_input_namespace(...)`. Implement, mirroring `forms/inputs.py`:
   - `get_serializer_for_schema(serializer_class)` — default no-arg discovery; **the guard wraps the
     `.fields` read** (a `serializer_class()` with no args does not raise; a context-requiring
     serializer raises at `.fields` access). Materializing `.fields` raising → `ConfigurationError`
     pointing at the `get_serializer_for_schema()` override contract.
   - `resolve_effective_serializer_fields(...)` — normalize+fail-loud `Meta.fields`/`exclude` via
     `normalize_field_name_sequence(flavor="SerializerMutation")`; mutual exclusion; unknown-name;
     empty-effective-set guard (the `036`/`038` precedent). Drop `read_only`/`HiddenField` from the
     input. `optional_fields` normalized (bare string incl. `"__all__"` rejected — no `"__all__"`
     sentinel for field selectors).
   - `SerializerInputShape` descriptor + `serializer_input_type_name(...)` (canonical
     `<Serializer>Input`/`<Serializer>PartialInput` for the default full shape; descriptor-derived
     deterministic name via `_pascalize_token` for any divergent shape).
   - `build_serializer_input_class(...)` (one `@strawberry.input` via `build_strawberry_input_class`)
     + `_guard_serializer_input_attr_collisions(...)` before build; `build_serializer_inputs(...)`
     (both create+partial; `guard_create_required_serializer_fields` when `guard_required=True`;
     `partial` widens every field optional).
   - `guard_create_required_serializer_fields(...)` — raise if a create narrowing drops a writeable
     `field.required`-no-default field; `read_only`/`HiddenField` exempt; waived via
     `guard_required=False` (the `get_serializer_kwargs` override precedent — Slice 2 passes the flag).
   - Each generated relation field carries **exactly one** strategy-dependent id annotation (Relay
     `GlobalID` if the target primary `DjangoType` is Relay-shaped, else raw-pk scalar) decided at
     this build site.

9. **TODO-anchor discharge.** Remove the Slice-1-labeled anchors as their work lands: `utils/converters.py:1-17`,
   `utils/inputs.py:53-66`, `forms/converter.py:116-126`, `forms/inputs.py:112-122`,
   `mutations/inputs.py:326-335` (the last replaced with non-TODO `spec-039` provenance noting the
   token helper stays sited on `mutations/inputs.py`). Leave the Slice-2 / Slice-3 anchors intact
   (`registry.py:53`, `types/finalizer.py:771`, `forms/sets.py:106/147/348`, `mutations/sets.py:104`,
   `__init__.py:39`, `forms/resolvers.py:175`, `utils/querysets.py:208`, `mutations/resolvers.py:112/799`,
   `rest_framework/{__init__,sets,resolvers}.py`).

10. **ruff** — `uv run ruff format .` then `uv run ruff check --fix .` (Worker 2's boundary;
    trailing-comma layout per `scripts/check_trailing_commas.py`).

### Test additions / updates

Package-internal tests only (Slice 1 ships no live surface — that is Slice 3). The live-first
mandate does **not** apply: the converter field-class matrix and the build-time invalid
configurations are exactly the residue `tests/rest_framework/` owns (spec lines 3113-3127).

- **`tests/rest_framework/test_converter.py`** (replace stub) — mirror `tests/forms/test_converter.py`'s
  parametrized shape:
  - every supported serializer-field class → its annotation + required-ness (`CharField`/`ChoiceField`
    →`str`, `IntegerField`→`int`, `BooleanField`→`bool`, `FloatField`→`float`, `DecimalField`→`Decimal`,
    `Date`/`DateTime`/`TimeField`→python-native, `UUIDField`→`uuid.UUID`, `JSONField`→`JSON`,
    `EmailField`/`SlugField`/`URLField`/`RegexField`→`str` via MRO);
  - `ListField(child=IntegerField())`→`list[int]`; `ListField` with a relation/nested-serializer
    child raises `ConfigurationError`; `MultipleChoiceField`→`list[str]`; a nested
    `ModelSerializer`/`ListSerializer` field raises;
  - `PrimaryKeyRelatedField`/`ManyRelatedField` id mapping (Relay-`GlobalID` vs raw-pk by the
    target's primary `DjangoType`; `many=True`→`list[<id>]`); `FileField`/`ImageField`→`Upload`;
  - **fail-loud dispatch** — a known field maps, but `class CustomField(serializers.Field)` raises
    `ConfigurationError` (the catch-all-shadowing regression assertion); assert no `String` fallback;
  - **renamed fields** — `category_pk = PrimaryKeyRelatedField(source="category")` and
    `full_name = CharField(source="name")`: GraphQL name from the **declared** name, backing
    `models.Field` resolved via `source`, declared name preserved in the reverse map;
  - **id-like suffix rule** — `category`→`categoryId`, `category_id`→`categoryId`,
    `category_pk`→`categoryPk` (no doubled `…IdId`/`…PkId`);
  - dotted `source`/`source="*"` on a model-column-converting field raises `ConfigurationError`;
  - **serializer-only relation** resolves target from `field.queryset.model` (F4); a relation with
    no backing column **and** no concrete `queryset.model` raises;
  - a relation whose **target model has no registered primary `DjangoType`** raises a class-creation
    `ConfigurationError` naming field + target model (M3).
  Assertion shape: `pytest.raises(ConfigurationError, match=<substring>)` for the raises;
  annotation equality on the conversion result's `annotation`/`kind`/`required`; reverse-map equality
  on `(input_attr, graphql_name, target_name=declared name, source, kind)`. Uses real fakeshop
  models (`Item`/`Category`) as fixtures per `AGENTS.md`.

- **`tests/rest_framework/test_inputs.py`** (replace stub) — mirror `tests/forms/test_inputs.py`:
  - the two generated inputs (`<Serializer>Input` with `field.required` requiredness for create;
    `<Serializer>PartialInput` all-optional); fields from the **schema-time field set**;
    `read_only`/`HiddenField` dropped; `Meta.fields`/`exclude` narrowing; `optional_fields`
    force-optional; a serializer-only (non-model) field included; materialized as a module global;
  - **schema-time hook** — a kwargs-requiring serializer **and** one whose `get_fields()` reads
    `self.context` (raising at **`.fields` access**, not construction — proving the guard wraps
    `.fields`) both rejected loudly under default no-arg discovery; a `get_serializer_for_schema()`
    override supplying a stable field map generates the input;
  - `optional_fields = "__all__"` (bare string) rejected;
  - **`SerializerInputShape` descriptor identity** — two create mutations over the same serializer +
    effective fields but different `Meta.optional_fields` get **distinct** deterministic names (not
    silent reuse); two schema hooks returning same-named fields with different annotations/`source`/
    relation kind diverge (or raise `ConfigurationError` on a name collision); identical descriptors
    dedupe (idempotent `materialize_serializer_input_class` re-call, no raise); two **distinct**
    descriptors on one generated name → `ConfigurationError`;
  - **create-required narrowing guard** — excluding a required scalar / required serializer-only
    field / required relation raises `ConfigurationError`; `read_only`/`HiddenField` exclusions do
    **not**; the `guard_required=False` waiver suppresses it; the guard fires **per declaration**
    (a waiving build of a shape first does not suppress it for a later non-waiving build of the same
    shape — assert by calling `guard_create_required_serializer_fields` directly, the form
    precedent at `tests/forms/test_inputs.py:480-531`);
  - **nullability/defaults (M2)** — `allow_null=True` → nullable annotation while
    `required=True, allow_null=True` leaves the key omittable-as-missing; `required=False, default=…`
    omittable (no fabricated GraphQL default); `allow_blank=True` absent from the generated SDL;
  - **input-attr / GraphQL-name collisions** — `category`→`categoryId` clashing with literal
    `category_id`→`categoryId`, and `foo_bar`+`fooBar`→`fooBar`, raise `ConfigurationError` **before
    materialization**; two **writable** fields sharing one one-segment `source` raise; a `read_only`
    field sharing a `source` with a writable one is **accepted**;
  - empty effective field set → `ConfigurationError`.

- **`tests/utils/test_inputs.py`** (extend, or add a focused module) — unit tests for the
  three Slice-1 promotions in isolation: `make_input_namespace` returns a `(ledger, materialize,
  clear)` trio whose `clear()` empties the ledger and whose `materialize` writes a module global;
  `make_shape_build_cache` returns a `(dict, clear)` pair whose `clear()` empties the dict;
  `InputFieldSpec` carries the five+optional axes. (Confirm the existing test module path; if none,
  pin under `tests/utils/`.)

- **`tests/utils/test_converters.py`** (new or extend) — `convert_with_mro` in isolation: a precheck
  match wins; an MRO-registry match resolves the most-specific class; an unhandled field calls the
  `fallthrough_error_factory` and raises.

- **Regression (behavior-preserving promotion)** — Worker 3 / final verification run the **existing**
  `tests/forms/` and `tests/mutations/` suites focused-scope (no `--cov*`) after the P1.4 / P2.1 /
  P2.2 re-points to confirm the form + model paths stay byte-equivalent (spec lines 3295-3302).
  Mechanically prove the `convert_form_field` re-point is behavior-preserving per the worker-1.md
  "relocated/promoted/unchanged" rule (token-diff the delegated body vs `git show HEAD`).

Temp/scratch tests: Worker 3 may add `docs/builder/temp-tests/slice-1/` probes for the
`.fields`-lazy-materialization timing (proving the guard fires at `.fields`, not construction) and
the `_pascalize_token` injectivity on a same-name-set divergent-shape pair; note disposition.

### Implementation discretion items

- **D1 — `InputFieldSpec` unification depth (P2.1).** The spec floor is "at minimum site the
  serializer spec in `utils/inputs.py`" (line 2783); a fuller "define one generic `InputFieldSpec`
  and re-point `FormInputFieldSpec`" is offered as a stronger option. **Assessed:** either is
  spec-conformant. Worker 2's discretion is whether to (a) define `InputFieldSpec` in `utils/inputs.py`
  and have only the serializer use it (form keeps `FormInputFieldSpec`, lowest blast radius), or (b)
  also re-point `forms/converter.py::FormInputFieldSpec` to subclass/alias it. Either is fine **so
  long as the form suite stays byte-equivalent**. Likewise whether the shared conversion-result shape
  reuses `FormFieldConversion` or a new neutral class — Worker 2's call.
- **D2 — P1.4 `forms/converter.py` re-point sequencing.** The skeleton (`convert_with_mro`) MUST be
  authored in Slice 1 (the serializer converter imports it). The `forms/converter.py` *re-point* to
  call it is also Slice-1-anchored (line 116) and should land here; but if Worker 2 finds the
  re-point inflates the diff past sensible review, it may be sequenced as the last step / flagged for
  the integration pass — the load-bearing requirement is that `serializer_converter.py` imports the
  shared skeleton and the form behavior is byte-equivalent. Worker 2's call on ordering; not a
  license to leave `forms/converter.py` forking the skeleton at slice end.
- **D3 — private helper names** under `rest_framework/inputs.py` /
  `serializer_converter.py` (e.g. `_serializer_input_attr_collisions` vs
  `_guard_serializer_input_attr_collisions`, the descriptor field order beyond the spec-pinned tuple)
  are Worker 2's, provided they mirror the `forms/` sibling naming so the module-for-module mirror
  holds.

### Spec slice checklist (verbatim)

- [ ] Slice 1: DRF-field → Strawberry input mapping + the serializer-derived input
  generator (per
  [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
  / [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
  - [x] [`rest_framework/serializer_converter.py`][rf-converter]: a
    `convert_serializer_field(field)` registry (the graphene-django
    [`convert_serializer_field`][upstream-serializer-converter] parity shape)
    returning the Strawberry annotation + required-ness for each supported DRF
    serializer-field class (`CharField` / `ChoiceField` → `str`, `IntegerField` →
    `int`, `BooleanField` → `bool`, `FloatField` → `float`, `DecimalField` →
    `Decimal`, `DateField` / `DateTimeField` / `TimeField` → Python-native,
    `UUIDField` → `uuid.UUID`, `JSONField` → `strawberry.scalars.JSON`, `ListField` →
    `list[<scalar child>]` (scalar `child` only — a relation / nested-serializer `child`
    raises [`ConfigurationError`][glossary-configurationerror]),
    `PrimaryKeyRelatedField` → the target's id,
    `PrimaryKeyRelatedField(many=True)` / `ManyRelatedField` → `list[<id>]`,
    `FileField` / `ImageField` → [`Upload`][glossary-upload-scalar]). **Fail-loud
    dispatch (mirroring [`forms/converter.py`][forms-converter]):** the registry is an
    MRO-walk over individually-registered classes with a **raising fallthrough** —
    **NOT** `functools.singledispatch` with the graphene-django
    `serializers.Field → String` catch-all, which would shadow the raise so every
    custom field silently became `String`; an unmapped `serializers.Field` subclass
    raises [`ConfigurationError`][glossary-configurationerror] naming the field and
    class. Where a serializer field maps to a Django column type the read side already
    converts (a `ModelSerializer` field over a `choices` column), reuse the
    [Scalar field conversion][glossary-scalar-field-conversion] /
    [Choice enum generation][glossary-choice-enum-generation] registry at the build
    site — keyed on the **backing `models.Field` resolved via the serializer field's
    `source`**, not its declared name — rather than re-deriving the scalar. Record, per
    generated input field, the `input_attr → (serializer_field_name, source, kind)`
    reverse map (`kind ∈ {scalar, relation_single, relation_multi, file}`) the resolver
    needs to build a payload keyed by the declared serializer field name —
    `categoryId` → `category`, a renamed `category_pk` (`source="category"`) → input
    `categoryPk` decoded back to `category_pk` (the `038` `FormInputFieldSpec` analog
    **plus the `source` axis**,
    [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
    **Renamed fields**: omitted / one-segment `source` supported, dotted `source` /
    `source="*"` rejected for a model-column-converting field). The whole module is
    behind the DRF soft-import guard
    ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  - [x] [`rest_framework/inputs.py`][rf-inputs]: build **two** `@strawberry.input`
    classes from the **serializer's schema-time field set** — discovered via the
    overridable `get_serializer_for_schema()` classmethod (default: no-arg
    `serializer_class()`, read `.fields`; a serializer requiring constructor context
    overrides it to return a stable, request-independent field shape; a serializer whose
    field set varies per request is rejected loudly —
    [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)) —
    narrowed by [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude], with `read_only` / `HiddenField`
    fields dropped from the input and `Meta.optional_fields` forced optional —
    graphene's `fields_for_serializer(is_input=True)` parity) — `<Serializer>Input`
    (create; each field's requiredness from `field.required` minus the
    `optional_fields` override) and `<Serializer>PartialInput` (update; every field
    optional) — under a **`SerializerInputShape` descriptor identity** (NOT the
    name-only `036` / `038` key): the ordered tuple of each emitted field's
    `(input_attr, GraphQL annotation, required/default, serializer_field_name, source,
    kind)` plus the normalized `optional_fields` set for create, so two same-name-set
    inputs that differ in requiredness (`optional_fields`) or hook-returned field specs
    get **distinct** deterministic names, never silent reuse
    ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
    Canonical `<Serializer>Input` / `<Serializer>PartialInput` for the default full
    shape, descriptor-derived names for any divergent shape, identical descriptors
    dedupe, two distinct descriptors on one generated name → finalize-time
    [`ConfigurationError`][glossary-configurationerror]. **Run the create-required
    narrowing guard (`guard_create_required_serializer_fields`) PER declaration, BEFORE
    the descriptor cache lookup** — raise if `Meta.fields` / `Meta.exclude` drops a
    writeable (`read_only` / `HiddenField` exempt) `field.required`-with-no-default
    serializer field; waived (`guard_required=False`) when the mutation overrides
    `get_serializer_kwargs` to inject the values (the [`forms/inputs.py`][forms-inputs]
    `guard_create_required_fields` + [`forms/sets.py`][forms-sets] per-declaration
    precedent). Reuse [`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class`
    + `materialize_generated_input_class` core (the latter's ledger gives the collision
    raise for free) and materialize as module globals of the `rest_framework` input
    namespace for the [`strawberry.lazy`][glossary-djangomutationfield] forward-ref.
    Normalize + fail-loud `Meta.fields` / `Meta.exclude` against the serializer's
    field set (bare string, duplicates, unknown names, empty effective set →
    `ConfigurationError`, mirroring `036`'s `_normalize_field_sequence` and `038`'s
    form normalization).
  - [x] Package coverage: [`tests/rest_framework/test_converter.py`][test-rest-framework]
    — each supported serializer-field class → its annotation + required-ness; the
    `PrimaryKeyRelatedField` / `ManyRelatedField` id mapping (Relay-`GlobalID` vs raw
    pk by the target's primary [`DjangoType`][glossary-djangotype]); the serializer
    `FileField` → [`Upload`][glossary-upload-scalar] mapping; **renamed fields** — a
    `source="category"` relation and a `source="name"` scalar derive the GraphQL name
    from the **declared** field name, resolve the backing `models.Field` via `source`,
    and preserve the declared name in the reverse map; **the id-like suffix rule** —
    `category` → `categoryId`, `category_id` → `categoryId`, `category_pk` →
    `categoryPk` (no doubled `…IdId` / `…PkId`); a **dotted `source`** / `source="*"` on
    a model-column-converting field raises
    [`ConfigurationError`][glossary-configurationerror]; the unknown serializer-field
    [`ConfigurationError`][glossary-configurationerror]. And
    [`tests/rest_framework/test_inputs.py`][test-rest-framework] — the serializer-derived
    input shape (fields from the schema-time set, required-ness from `field.required`,
    `read_only` dropped, `Meta.fields` / `Meta.exclude` narrowing,
    `Meta.optional_fields` force-optional, `optional_fields = "__all__"` bare-string
    rejected), materialized as a module global; **the schema-time hook** — a serializer
    whose `__init__` requires kwargs **and** one whose `get_fields()` reads `self.context`
    (so it raises at **`.fields` access**, not at construction — proving the guard wraps
    `.fields`, not `serializer_class()`) are both rejected loudly under the default no-arg
    discovery, and an override of `get_serializer_for_schema()` supplying a stable field
    map generates the input; **`SerializerInputShape` descriptor identity** — two create
    mutations over the **same** serializer + effective fields but **different**
    `Meta.optional_fields` get distinct deterministic names (not silent reuse), and two
    schema hooks returning same-named fields with **different annotations / `source` /
    relation kind** likewise diverge (or raise `ConfigurationError` on a name collision),
    identical descriptors dedupe; **the create-required narrowing guard** — excluding a
    required scalar, a required serializer-only field, or a required relation raises
    [`ConfigurationError`][glossary-configurationerror], `read_only` / `HiddenField`
    exclusions do **not**, and the `get_serializer_kwargs` waiver
    (`guard_required=False`) suppresses it; the guard runs **per declaration** (a waiving
    mutation materializing a shape first does not suppress it for a later non-waiving
    mutation on the same shape).
  - [x] **DRY / reuse** ([Cross-flavor reuse and DRY obligations](#cross-flavor-reuse-and-dry-obligations)):
    `convert_serializer_field` rides the shared fail-loud dispatch **skeleton** promoted to
    `utils/converters.py` (supplying only its precheck table + scalar registry — the
    no-silent-`String`-catch-all contract single-sited with
    [`forms/converter.py`][forms-converter], **P1.4**); the reverse-map field spec is the
    unified `InputFieldSpec` sited in [`utils/inputs.py`][utils-inputs] (the `038`
    `FormInputFieldSpec` analog + the `source` axis, with the conversion result a shared
    shape too — **P2.1**); the input namespace is the promoted `make_input_namespace(...)`
    **one-ledger** trio (the form/mutation clear shape, NOT the heavier
    `clear_generated_input_namespace` — **P2.2**); the `SerializerInputShape` cache + clear is
    the promoted `make_shape_build_cache()` plumbing (**P1.3**); and the divergent-shape
    suffix reuses `mutations/inputs.py::_pascalize_token` (**P2.3**). A grep guard that
    `rest_framework/serializer_converter.py` + `rest_framework/inputs.py` **import** these
    and do not redefine them is the DoD check.

### Notes for Worker 1 (spec reconciliation)

These are flagged now (Worker 1 only edits the spec during a final-verification pass per the role
contract). None blocks the build; each is a clarity/boundary note for the Worker-1 final-verification
spawn to decide whether a spec edit is warranted.

- **SR-1 — P1.3 cache CONSUMER is Slice 2, not Slice 1 (boundary clarity, not a conflict).** The
  Slice 1 DRY/reuse bullet (spec line 744) lists P1.3 (`make_shape_build_cache`) as a Slice-1 reuse
  for the serializer shape cache, and the `utils/inputs.py:53` anchor is Slice-1-labeled (so the
  helper is authored here). But the serializer flavor's cache **consumer** — `cached_build_input` /
  `build_and_stash_input` (P1.7) and the bind in `rest_framework/sets.py` — is unambiguously **Slice
  2** (spec lines 856-873; staged anchors `mutations/sets.py:104`, `forms/sets.py:147`, all
  `Slice 2`). This matches the spec-038 precedent (generators in the inputs slice, cache consumer in
  the sets slice). **Resolution (in-plan, no spec edit needed):** Slice 1 authors the `make_shape_build_cache`
  helper + a unit test; the serializer cache is consumed in Slice 2. The plan is written to this
  split. If the final-verification reviewer judges the spec's Slice-1 P1.3 phrasing misleading
  enough to mislead a future reader, a one-line spec clarification ("the cache helper is authored in
  Slice 1; the serializer cache consumer is Slice 2") would be the edit — but it is not required for
  a correct build.

- **SR-2 — Slice 1 imports DRF directly; the `require_drf()` soft-import guard is Slice 2.** Decision
  12 / the Slice 1 sub-bullet say "the whole module is behind the DRF soft-import guard," but
  `require_drf()` lives in `rest_framework/__init__.py` and is authored in **Slice 2** (anchor
  `rest_framework/__init__.py:3`, `Slice 2`; the soft-dep import-simulation test is also Slice 2 per
  spec lines 3276-3290). In Slice 1 the new modules import DRF directly (`from rest_framework import
  serializers`); DRF is present in the test env (Slice 0 dev-dep). This is consistent: the soft-dep
  *guard wiring* (the `__getattr__` export, the three raising entry points, the absent-path test) is
  the Slice 2 contract; Slice 1's modules are simply DRF-importing package internals. No spec edit
  needed — flagged so the final-verification reviewer does not read the Slice-1 "behind the guard"
  phrasing as requiring `require_drf()` to land early.

- **SR-3 — `is_input` parameter on `convert_serializer_field`.** Decision 7 (lines 1976-1988)
  mandates the parameter is carried on the signature for graphene-parity but **accepted-and-ignored**
  (no `if not is_input:` branch — a dead branch would gate-fail `fail_under=100`). The Slice-1
  sub-bullet text writes `convert_serializer_field(field)` without the parameter (line 629). Not a
  conflict (Decision 7 governs the signature), but the verbatim sub-check omits it. Worker 2 should
  implement the Decision-7 signature `convert_serializer_field(field, *, is_input=True)`. Flagged so
  the final-verification audit does not flag the parameter as out-of-contract.

### Spec changes made (Worker 1 only)

None this pass (planning). Any edit deferred to the final-verification spawn per the SR notes above.

## Build report (Worker 2)

Status: built

### Files touched

Slice-intended source (all grounded in `git status --short`):

- `django_strawberry_framework/utils/converters.py` — **P1.4**: replaced the stub +
  Slice-1 anchor with `convert_with_mro(field, *, isinstance_prechecks, scalar_registry,
  fallthrough_error_factory)` — the shared ordered-precheck → MRO-walk → raising-fallthrough
  skeleton. Pure; imports neither `django.forms` nor `rest_framework`.
- `django_strawberry_framework/forms/converter.py` — **P1.4 re-point**: `convert_form_field`
  now delegates to `convert_with_mro` (prechecks = relation-multi / relation-single / file /
  multiple-choice / bare-`Field`; registry = `_SCALAR_FORM_FIELDS`; fallthrough =
  new `_unsupported_form_field` factory). Behavior byte-equivalent (forms suite green).
- `django_strawberry_framework/utils/inputs.py` — **P2.1** `InputFieldSpec` (frozen, the `038`
  `FormInputFieldSpec` + the `source` axis), **P2.2** `make_input_namespace(module_path,
  family_label) → (ledger, materialize, clear)` (one-ledger trio, NOT the heavy
  `clear_generated_input_namespace`), **P1.3** `make_shape_build_cache() → (cache, clear)`.
- `django_strawberry_framework/mutations/inputs.py` — **P2.2 re-point** (`_materialized_names`
  trio now from `make_input_namespace`; public `materialize_*`/`clear_*` unchanged) +
  discharged the `_pascalize_token` Slice-1 TODO anchor (replaced with non-TODO spec-039
  provenance keeping the token helper sited here, P2.3).
- `django_strawberry_framework/forms/inputs.py` — **P2.2 re-point** (same trio; public names
  unchanged) + discharged its Slice-1 TODO anchor.
- `django_strawberry_framework/rest_framework/serializer_converter.py` — net-new: imports DRF
  directly (SR-2), `convert_serializer_field(field, *, is_input=True)` riding `convert_with_mro`,
  the `source`-axis reverse map (`resolve_serializer_field` → `InputFieldSpec`), id-like-suffix
  rule, dotted/`*` source rejection, serializer-only relation (`queryset.model`, F4), M3 guard.
- `django_strawberry_framework/rest_framework/inputs.py` — net-new: `SERIALIZER_INPUTS_MODULE_PATH`,
  `make_input_namespace` trio, `get_serializer_for_schema` (guard wraps `.fields`),
  `resolve_effective_serializer_fields` (drop read_only/Hidden, normalize fields/exclude,
  optional_fields), `SerializerInputShape` descriptor + descriptor-derived naming,
  `build_serializer_input_class` / `build_serializer_inputs`, the collision guard (attr /
  graphql-name / writable-source), `guard_create_required_serializer_fields`, the P1.3 cache pair.

Slice-intended tests:

- `tests/rest_framework/test_converter.py` (replaced stub) — converter field-class matrix,
  fail-loud dispatch, id-like suffix, renamed-field source axis, dotted/`*` source, serializer-only
  relation + Relay/raw-pk + M3.
- `tests/rest_framework/test_inputs.py` (replaced stub) — the two inputs, schema-hook failure
  modes (kwarg-requiring + `.fields`-lazy context), read_only/Hidden drop, fields/exclude narrowing,
  optional_fields + `"__all__"` reject, descriptor identity, create-required guard + per-declaration,
  M2 nullability, collisions, module-global materialization.
- `tests/utils/test_inputs.py` (extended) — `InputFieldSpec` axes, `make_input_namespace` trio,
  `make_shape_build_cache` pair.
- `tests/utils/test_converters.py` (new) — `convert_with_mro` in isolation (precheck-wins,
  ordered prechecks, None-continues, most-specific MRO, unregistered-subclass-to-parent, raise).

Out-of-scope dirty files NOT touched (verified not my churn): `docs/feedback.md` (baseline-dirty,
instructed not to touch); `pyproject.toml` / `uv.lock` / `docs/spec-039-*.md` (Slice 0's
uncommitted DRF dev-dep gate — prior-slice working-tree state, not Slice 1 churn).

### Tests added or updated

See above. Focused run (no `--cov`): `tests/rest_framework/test_converter.py
tests/rest_framework/test_inputs.py tests/utils/test_inputs.py tests/utils/test_converters.py`
→ **97 passed**. Re-point regression: `tests/forms tests/mutations` → **318 passed** (byte-equivalent).
Combined broader sanity (utils substrate + filters/orders share-test included via tests/forms +
tests/mutations + new tests) → **415 passed**.

### Validation run

- `uv run ruff format .` — **pass** (295 files unchanged on the final run).
- `uv run ruff check .` — **pass** (`All checks passed!`).
- `git status --short` after both — classified above; all slice-intended, no tool churn to revert.
- DoD grep guards — all pass: `convert_with_mro` ≥1 in both converters; `__mro__` = 0 in
  `serializer_converter.py`; `make_input_namespace|build_strawberry_input_class|InputFieldSpec|
  make_shape_build_cache|graphql_camel_name|normalize_field_name_sequence` imports present in
  `inputs.py`; hand-rolled ledger literal = 0; `_pascalize_token` ≥1; `def .*pascal|\.capitalize\(\)`
  = 0.

### Implementation notes (deltas the plan did not pin)

- **`convert_with_mro` return contract**: the skeleton returns the registry value AS-IS; both
  flavors' scalar registries store BARE annotations and the caller wraps the result into its
  `*FieldConversion` (form/serializer). Prechecks return the finished conversion object; the caller
  distinguishes via `isinstance(result, <Conversion>)`. This keeps the skeleton flavor-free (one
  registry value type, no per-call conversion-object allocation in the registry) — the form
  exact-type `forms.Field`→`str` case is a precheck returning `None` for non-exact matches so the
  walk continues (preserving the prior "walk-then-exact-type" order, byte-equivalent).
- **D1 (InputFieldSpec unification depth)**: chose option (a) — defined neutral `InputFieldSpec` in
  `utils/inputs.py`, the serializer uses it directly, the form keeps `FormInputFieldSpec` untouched
  (lowest blast radius; form suite stays byte-equivalent). Used a serializer-local
  `SerializerFieldConversion` (not a shared conversion class) to keep the form's `FormFieldConversion`
  byte-unchanged.
- **D2 (P1.4 forms re-point sequencing)**: landed the `forms/converter.py` re-point in this slice
  (not deferred) — the diff stays reviewable and the forms suite proves byte-equivalence.
- **D3 (private helper names)**: mirrored the `forms/` siblings —
  `_guard_serializer_input_attr_collisions`, `resolve_serializer_field`,
  `serializer_only_relation_annotation`, `_unsupported_serializer_field`.
- **`SerializerInputShape` is a frozen dataclass that IS its own `cache_key`** (a `@property`
  returning `self`) — it is hashable, so the Slice-2 `make_shape_build_cache` keys on it directly
  with no separate key tuple, and the materialize-ledger dedupe / distinct-descriptor raise come
  from the deterministic `type_name`.
- **Descriptor-derived divergent name uses `hashlib.sha1` (NOT builtin `hash`)** — see Notes for
  Worker 1 (drift note D-1). The digest is appended lowercase to the `_pascalize_token` field token
  so the combined token keeps the single-leading-capital / underscore-free injective shape (no
  `.capitalize()` on the digest — that would introduce an interior boundary and trip both
  injectivity and the DoD `\.capitalize\(\)` = 0 guard).
- **M2 nullability**: annotation widened `T | None` once via `allow_null OR not required`; a
  required+`allow_null` field is nullable WITHOUT an UNSET default (must be provided, value may be
  null); a `required=False, default=…` DRF field is omittable (UNSET), no fabricated GraphQL default.
- **`get_serializer_for_schema` guard wraps `serializer_class()` AND `.fields`** in one `try` —
  a kwarg-requiring serializer raises at construction, a `self.context`-reading `get_fields()`
  raises at `.fields` access; both surface as the same `ConfigurationError`. Test
  `test_context_reading_get_fields_rejected_at_fields_access` first calls `CtxSer()` (no raise) to
  prove the guard is not on the constructor.
- **`source` axis on `InputFieldSpec`** is `None` when the field's `source` equals its declared name
  (form-symmetric, terse reverse map); the resolved one-segment source otherwise. The writable-source
  collision guard keys on `spec.source or spec.target_name`.

### Notes for Worker 1 (spec reconciliation)

- **D-1 (small, mechanically-obvious drift — descriptor-name digest)**: the plan's
  `serializer_input_type_name` says "descriptor-derived deterministic name via `_pascalize_token`
  for any divergent shape". `_pascalize_token` alone encodes only the field NAME; to make two
  same-name-set shapes differing in annotation / requiredness / source / kind produce DISTINCT names
  (Decision 7's descriptor identity), I fold those axes into the per-field token via a short
  `hashlib.sha1` hex digest appended after `_pascalize_token(name)`. `hashlib` (not the
  process-salted builtin `hash`) is load-bearing for cross-process determinism of the generated
  name. This stays within the slice contract (descriptor drives the name) and reuses
  `_pascalize_token` for the name component; flagged for your confirmation that the digest approach
  is acceptable vs. a fuller stable-serialization scheme.
- **SR-1 / SR-2 / SR-3 (Worker 1's plan flags) handled as planned**: P1.3 helper authored here, its
  serializer cache CONSUMER left to Slice 2 (`rest_framework/sets.py`); Slice 1 imports DRF directly
  (`require_drf()` is Slice 2); `convert_serializer_field(field, *, is_input=True)` accepts-and-ignores
  `is_input` (no dead branch) — test `test_is_input_parameter_is_accepted_and_ignored` pins it.
- **M3 strictness applied in BOTH relation paths**: a serializer relation whose target model has no
  registered primary `DjangoType` raises a class-creation `ConfigurationError` (stricter than the
  form / `relation_input_annotation` raw-pk fallback) — `_require_relation_primary` enforces it for
  the model-backed AND the serializer-only relation. A NON-Relay target still legitimately uses the
  raw pk (M3 forbids a MISSING primary, not a non-Relay one).

### Notes for Worker 3

- No `scripts/review_inspect.py` / shadow files were used this pass.
- The serializer flavor's choice-enum reuse builds the enum off the CANONICAL provisional name
  (`<Serializer>Input`); the read `DjangoType`'s enum is cached per `(model, field)`, so the name is
  stable regardless of the divergent type name — `test_choices_modelserializer_field_resolves_to_read_side_enum`
  asserts the IDENTICAL enum object.
- `tests/rest_framework/__init__.py` already existed (Slice-0 scaffolding); no new package marker
  needed. The forms/mutations regression (318) + the new 97 + the combined 415-test run are the
  byte-equivalence + new-behavior evidence.

---

## Review (Worker 3)

Status: review-accepted

Reviewed the Slice-1 working-tree diff (`utils/converters.py`, `utils/inputs.py`,
`forms/converter.py`, `forms/inputs.py`, `mutations/inputs.py`,
`rest_framework/serializer_converter.py`, `rest_framework/inputs.py`, and the four test files)
against spec-039 Decision 7 / Decision 12, the DRY obligations (P1.3/P1.4/P2.1/P2.2/P2.3), and
DoD item 2. Cumulative-diff filter applied via `### Files touched`; `docs/feedback.md`,
`pyproject.toml`, `uv.lock`, `docs/spec-039-*.md` treated as baseline/Slice-0 out-of-scope per the
dispatch contract.

### High:

None.

### Medium:

None.

### Low:

#### L1 — Vacuous assertion in the M2 `allow_null` test

`tests/rest_framework/test_inputs.py::test_allow_null_field_is_nullable_even_when_required`
line 620 reads `assert field.default is UNSET.__class__() or field.default is not UNSET`. I
verified `UNSET.__class__() is UNSET` is True (UNSET is a singleton), so the line reduces to
`(field.default is UNSET) or (field.default is not UNSET)` — a tautology that passes for ANY
value and pins nothing. Not a correctness problem: the load-bearing contract (a
`required=True, allow_null=True` field is nullable WITHOUT an UNSET default, so it must be
provided) IS pinned by the adjacent line 622 `assert field.default is not UNSET` plus the line
619 `_is_optional` check. L1 is dead clutter, not a coverage gap. Recommended change: delete
line 620 (line 619 + 622 already pin the contract), or rewrite it to assert the actual default
identity. Severity Low (no behavior unpinned).

### DRY findings

None outstanding. The grep-guard DoD (below) is the central DRY contract and passes in full:
both converters import and call the promoted `convert_with_mro` (no second MRO-walk skeleton;
`__mro__` appears in `serializer_converter.py` 0 times, and the 2 hits in `forms/converter.py`
are comment/docstring references to the registry idiom, NOT a re-spelled inline walk — verified);
`rest_framework/inputs.py` imports `make_input_namespace` / `make_shape_build_cache` /
`InputFieldSpec` / `build_strawberry_input_class` / `normalize_field_name_sequence` and spells no
hand-rolled `_materialized_names = {}` ledger literal (0 hits); `_pascalize_token` is reused by
import with no new PascalCase / `.capitalize()` encoder under `rest_framework/` (0 hits). The
`forms/inputs.py` + `mutations/inputs.py` P2.2 re-points and the `forms/converter.py` P1.4
re-point keep their public names and are behavior-preserving (suites green; fallthrough message
byte-identical to `git show HEAD`).

### Worker 2's D-1 decision (descriptor divergent-name digest) — scrutinized

`rest_framework/inputs.py::_shape_token` builds a divergent-shape field token as
`f"{_pascalize_token(spec.target_name)}{sha1(annotation|required|kind|source)[:6]}"`. Verdict:
sound on all three axes I was asked to check.
- **Deterministic cross-process:** uses `hashlib.sha1` over a UTF-8 encode of the discriminant
  string, NOT the builtin process-salted `hash()` — confirmed by reading the body and the
  comment rationale. The generated name is stable across processes, which the
  materialize-ledger dedupe (`materialize_generated_input_class` `(name, cls)` idempotency)
  depends on.
- **Decomposability preserved:** `_pascalize_token` emits a single-leading-capital,
  underscore-free, interior-capital-free token; the appended 6-char lowercase-hex digest adds
  no interior uppercase and no underscore, so the bare concatenation of per-field tokens stays
  uniquely decomposable at uppercase boundaries (the injectivity invariant `_pascalize_token`'s
  own docstring guards). A theoretical break would need a digit-leading field name
  (`"2x".capitalize()` stays lowercase), which is not a legal Python/GraphQL identifier and so
  unreachable.
- **Collision resistance:** 24 bits over the per-field discriminant, folded per field into a
  whole-shape suffix; the discriminant also carries `kind`/`source`, and the descriptor itself
  (not the name) is the cache key, with the materialize ledger raising on any genuine
  distinct-class-same-name collision. Adequate for a build-time generated-name disambiguator.
  Readable: the long comment block earns its length given the subtlety.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty — no change to `__all__` or the
re-export list this slice. The `SerializerMutation` export is Slice 2; correctly absent here.
Confirmed.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The Slice-1 TODO
anchors named in the plan — `utils/converters.py`, `utils/inputs.py:53`, `forms/converter.py`,
`forms/inputs.py`, `mutations/inputs.py:326` — are all discharged in the diff: the
`mutations/inputs.py` one replaced with non-TODO `spec-039` provenance, the rest removed; the
inspector reports 0 TODO comments in both new modules.)

### Spec slice checklist walk

All four `- [x]` boxes in the Plan's verbatim checklist have matching implementation in the diff:
(1) `convert_serializer_field` registry + fail-loud MRO dispatch + reverse map + source axis —
`serializer_converter.py`; (2) the two `@strawberry.input` classes from the schema-time field
set + `SerializerInputShape` descriptor identity + per-declaration create-required guard —
`inputs.py`; (3) `tests/rest_framework/test_converter.py` + `test_inputs.py` cover every named
behavior (scalar matrix, fail-loud no-`String`-catch-all, id-like suffix, renamed-field source
axis, dotted/`*` source reject, serializer-only relation, M3, schema-hook lazy-`.fields` guard,
descriptor identity, create-required per-declaration, M2 nullability, collisions); (4) DRY/reuse
grep guard. No over-tick, no silently un-addressed sub-check.

### Behavioral-claim verification

- **Fail-loud dispatch (no `String` catch-all):** traced `convert_with_mro` — prechecks, then
  MRO walk over `_SCALAR_SERIALIZER_FIELDS` (no base-`serializers.Field` entry), then
  `raise fallthrough_error_factory(field)`. No prior branch swallows the unmapped path;
  `test_unknown_custom_field_subclass_raises` pins the raise + asserts no String fallback.
- **`is_input` accepted-and-ignored:** `del is_input` then no `if not is_input:` branch anywhere
  — no dead branch to gate-fail `fail_under=100`; `test_is_input_parameter_is_accepted_and_ignored`
  pins both arms produce identical conversions.
- **`.fields`-wrapping guard:** `get_serializer_for_schema` wraps both `serializer_class()` AND
  `serializer.fields` in one `try`; `test_context_reading_get_fields_rejected_at_fields_access`
  first calls `CtxSer()` (no raise) THEN asserts the discovery raises, proving the guard is on
  `.fields`, not the constructor. Kwarg-requiring serializer also pinned.
- **create-required guard per-declaration:** `build_serializer_inputs` runs
  `guard_create_required_serializer_fields` BEFORE any build/cache step and only when
  `guard_required=True`; the guard reads `_required_writable_field_names` (live, off the
  serializer) not a cached shape, so a waiving build cannot poison a later non-waiving one —
  `test_guard_runs_per_declaration` pins it via the direct-call form. `read_only`/`HiddenField`
  exempt (dropped before the guard's set difference); pinned.

### What looks solid

- The `convert_with_mro` skeleton is genuinely flavor-free (imports neither `django.forms` nor
  `rest_framework`); the registry-value-returned-as-is contract lets each flavor keep its own
  conversion wrapper without leaking types into the shared module. Clean single-siting of the
  GOAL-mandated fail-loud contract.
- The `source`-axis reverse map is carefully separated from the GraphQL name: declared name
  always drives the input attr / GraphQL name (id-like-suffix rule), `source` resolves only the
  backing `models.Field`. The renamed-field tests (`full_name`→`fullName` source=`name`;
  `category_pk`→`categoryPk` source=`category`) pin both halves.
- M3 strictness is applied symmetrically in BOTH relation paths via `_require_relation_primary`,
  and correctly forbids only a MISSING primary (a non-Relay primary still uses the raw pk) —
  matching the spec's "stricter than the form fallback, form left byte-unchanged" contract.
- Three-way collision guard (input_attr / graphql_name / writable-source) with the read-only
  source-share accepted case is exactly the spec contract and well-tested.

### Temp test verification

No temp-test files created. The one behavioral suspicion that needed runtime confirmation (the
L1 `UNSET.__class__()` identity) was resolved with a one-line `uv run python -c` probe
(`UNSET.__class__() is UNSET` → True), not a kept test file. The static helper was run on all
four required files; shadow output under `docs/shadow/` (gitignored). Django/ORM markers in
`serializer_converter.py` (2: `model._meta.get_field(source)` for backing-column resolution,
`scalar_for_field(related_model._meta.pk)` for the raw-pk scalar) are both justified; `inputs.py`
reports zero ORM markers. Control-flow hotspots (`resolve_serializer_field` 10 branches,
`build_serializer_input_class` 9 branches, `resolve_effective_serializer_fields` 8 branches) were
walked — each branch maps to a documented Decision-7 axis and is test-covered.

### Notes for Worker 1 (spec reconciliation)

- Worker 2's flagged D-1 (descriptor-name `sha1` digest) is **accepted** by this review as
  spec-conformant (the descriptor drives the name; `_pascalize_token` supplies the name
  component; the digest is the deterministic, decomposition-safe discriminant). No spec edit
  needed in my judgment; Worker 1 owns the final call but I see no ambiguity to reconcile.
- SR-1 (P1.3 cache CONSUMER is Slice 2), SR-2 (`require_drf()` is Slice 2; Slice 1 imports DRF
  directly), SR-3 (`is_input` accepted-and-ignored) are all handled exactly as the plan flagged —
  no premature `require_drf()`, the cache helper authored + unit-tested without a serializer
  consumer, the `is_input` signature present with no dead branch. Confirmed, no reconciliation
  needed.

### Review outcome

`review-accepted`. One Low finding (L1, vacuous test assertion) recorded; it pins no behavior
that the adjacent live assertion does not already pin, so it does not block acceptance. No High
or Medium findings. The DRY grep-guard DoD passes in full; the form/mutation re-points are
behavior-preserving (suites green, messages byte-identical to HEAD); the public surface is
unchanged.

---

## Final verification (Worker 1)

Final-verification pass on 2026-06-27. Read the full artifact (plan / build report / D-1 drift note
/ Worker 3 review), the working-tree diff for the eight scoped source files + the four test files,
the spec header (status-line check) and Decision 7 / DRY-obligation lines, and the build plan.
`docs/feedback.md` (baseline-dirty), and `pyproject.toml` / `uv.lock` / `docs/spec-039-*.md`
(Slice 0's accepted uncommitted state) treated as out-of-scope per the dispatch contract — not
inspected as Slice-1 regressions.

### 1. Spec slice checklist audit (the four verbatim sub-checks)

Re-audited every `- [x]` in `### Spec slice checklist (verbatim)` against the diff. All four landed;
no over-tick, no silently un-ticked box.

- **`- [x]` sub-check 1 (`serializer_converter.py`):** LANDED. `convert_serializer_field(field, *,
  is_input=True)` rides `convert_with_mro` (no re-spelled `__mro__` walk — 0 hits in the module;
  `convert_with_mro` imported from `..utils.converters` and called once). The scalar registry, the
  relation/file/list/multi-choice prechecks, the raising fallthrough (`_unsupported_serializer_field`,
  no base-`serializers.Field` catch-all), the `source`-axis reverse map → `InputFieldSpec`, the
  id-like-suffix rule, the dotted/`*`-source rejection, the serializer-only `queryset.model` relation
  (F4), and the M3 missing-primary raise are all present in the diff and test-covered.
- **`- [x]` sub-check 2 (`inputs.py`):** LANDED. Two `@strawberry.input` classes from the
  schema-time field set via `get_serializer_for_schema` (the guard wraps both `serializer_class()`
  AND `.fields` in one `try` — verified in source), `read_only`/`HiddenField` dropped,
  `Meta.fields`/`exclude`/`optional_fields` narrowing, the `SerializerInputShape` descriptor identity
  (frozen dataclass that IS its own cache key), descriptor-derived divergent names, identical-dedupe /
  distinct-descriptor-collision raise, and `guard_create_required_serializer_fields` run
  per-declaration BEFORE the cache lookup with the `guard_required=False` waiver.
- **`- [x]` sub-check 3 (package coverage):** LANDED. `tests/rest_framework/test_converter.py` and
  `test_inputs.py` cover every named behavior; `tests/utils/test_inputs.py` extended and
  `tests/utils/test_converters.py` added for the promotions in isolation.
- **`- [x]` sub-check 4 (DRY / reuse):** LANDED. Verified mechanically (see check 2 below). The
  import-not-redefine grep-guard DoD passes in full.

No remaining `- [ ]` sub-checks; no deferral needed. (The parent Slice-1 header box at the top of the
verbatim block stays `- [ ]` — that is the build-plan slice box Worker 0 marks, not a Worker-2 sub-check.)

### 2. DRY check across Slice 1 AND prior accepted Slice 0

No new cross-slice duplication. Mechanically confirmed the four promotions are single-sited:

- `InputFieldSpec` (P2.1), `make_input_namespace` (P2.2), `make_shape_build_cache` (P1.3) all defined
  exactly once, in `utils/inputs.py` (lines 54 / 91 / 144). `convert_with_mro` (P1.4) defined once in
  `utils/converters.py`.
- `forms/inputs.py` + `mutations/inputs.py` re-point to `make_input_namespace` (their public
  `materialize_*` / `clear_*` are thin wrappers); **zero** hand-rolled `_materialized_names = {}`
  ledger literals in either re-pointed file or in `rest_framework/inputs.py`.
- `rest_framework/inputs.py` imports `InputFieldSpec` / `make_input_namespace` / `make_shape_build_cache`
  / `build_strawberry_input_class` / `normalize_field_name_sequence` from `..utils.inputs` and
  `_pascalize_token` (P2.3) from `..mutations.inputs`; spells **no** PascalCase encoder / `.capitalize()`
  (0 hits) and **no** second MRO walk.
- `serializer_converter.py` imports + calls `convert_with_mro`; `__mro__` appears 0 times.
- **Relocation/promotion proof (per worker-1.md "Verifying relocated/promoted/unchanged claims"):**
  token-diffed the re-pointed `convert_form_field` against `git show HEAD`. The body now delegates to
  `convert_with_mro` with prechecks `[ModelMultipleChoiceField, ModelChoiceField, FileField,
  MultipleChoiceField, Field→_bare_field]`, the same `_SCALAR_FORM_FIELDS` registry, and
  `_unsupported_form_field` (message string byte-identical to HEAD). The one structural subtlety — HEAD
  ran the scalar walk BEFORE the exact-type `type(field) is forms.Field → str` check, the re-point puts
  `_bare_field` as the LAST precheck (which runs before the walk) — is behavior-preserving because
  `_bare_field` returns `None` for any non-exact match (letting the walk proceed) and `forms.Field` is
  never in the scalar registry, so an exact `forms.Field` produces `str` and every registered subclass
  resolves through the walk identically. Confirmed byte-equivalent.

### 3. Existing tests still pass (focused scope, no coverage flags)

`uv run pytest tests/rest_framework tests/forms tests/mutations tests/utils --no-cov` → **481 passed
in 3.24s** (8 xdist workers). The explicit `--no-cov` opted out of `pytest.ini`'s auto-applied `--cov`;
no `--cov*` flag used. The forms + mutations suites passing inside this run is the behavior-preserving
evidence for the P1.4 / P2.1 / P2.2 re-points.

### 4. L1 Low finding — decision: **(b) accept the slice, explicitly defer the cleanup**

Worker 3's L1: `tests/rest_framework/test_inputs.py::test_allow_null_field_is_nullable_even_when_required`
line 620 — `assert field.default is UNSET.__class__() or field.default is not UNSET` — is a tautology
(`UNSET` is a singleton, so `UNSET.__class__() is UNSET`, reducing the line to `X or not X`), pinning
nothing. I confirmed the read: line 619 (`assert _is_optional(field)`) and line 622
(`assert field.default is not UNSET`) already fully pin the load-bearing M2 contract (a
`required=True, allow_null=True` field is nullable WITHOUT an UNSET default → must be provided).

**Decision (b): accept, defer the one-line cleanup.** Rationale: the line is dead clutter, not a
coverage gap or an unpinned contract — no production behavior and no abstraction is at stake, and the
adjacent live assertions pin the exact contract. `AGENTS.md`'s "highest standard / root-cause-not-patch"
mandate governs **shipped behavior and the production abstraction**; a redundant test assertion that
misleads no reader of the production code is not that class of defect. A `revision-needed` re-loop costs
a full Worker 2 + Worker 3 cycle for a one-line test edit that pins nothing — disproportionate to the
defect. Slice 2 and Slice 3 both touch `tests/rest_framework/`, and the integration pass re-reads this
artifact's findings; the cleanup folds in there at zero marginal cost. Recorded in this build's deferred
catalog (see carry-forward) so it is not lost: **delete `test_inputs.py:620` (or rewrite it to assert the
actual `field.default` identity) — the M2 contract stays pinned by lines 619 + 622.**

### 5. Spec reconciliation (SR-1, SR-3) — no spec edit this pass

- **SR-1 (P1.3 cache consumer is Slice 2):** No edit. Spec line 745 ("the `SerializerInputShape`
  cache + clear is the promoted `make_shape_build_cache()` plumbing — **P1.3**") sits in the Slice-1
  DRY/reuse sub-bullet and states a *reuse obligation* (the cache plumbing is shared, not re-forked),
  which Slice 1 satisfies by authoring `make_shape_build_cache` + unit-testing it. It does NOT assert
  the serializer cache *consumer* lands in Slice 1 — and the Slice 2 checklist (spec line 749+) owns
  `rest_framework/sets.py` + the cache bind, matching the spec-038 precedent (generators in the inputs
  slice, consumer in the sets slice). The phrasing is not misleading enough to misdirect a future
  reader; a clarification would be cosmetic. Left as-is.
- **SR-3 (`is_input` signature):** No edit. Spec line 629 writes the shorthand
  `convert_serializer_field(field)`, but the governing Decision 7 (linked at the head of the same
  bullet, line 626) mandates `convert_serializer_field(field, *, is_input=True)` accepted-and-ignored
  (lines 1976-1988). Worker 2 implemented the Decision-7 signature exactly (`def convert_serializer_field(
  field, *, is_input: bool = True)`; `del is_input`; no `if not is_input:` branch;
  `test_is_input_parameter_is_accepted_and_ignored` pins both arms identical). The Decision governs
  and is cited inline, so the shorthand is harmless — not worth a spec edit that would only restate the
  linked Decision. Left as-is.
- **SR-2 (`require_drf()` is Slice 2):** No reconciliation needed — Slice 1 imports DRF directly as a
  package internal (dev-dep present from Slice 0); the soft-import guard wiring is the Slice 2 contract,
  exactly as planned.
- **Spec status/header lines (per-spawn re-verify):** spec lines 1-60 read `Status: **IN PROGRESS**
  … no slice built yet`. This is now stale (Slice 0 + Slice 1 have shipped on the working tree), but
  the build is uncommitted and the maintainer's first touch point is after the final gate; the
  package version + all predecessor references remain accurate. I am **not** editing the status line
  this pass — flagging it as a carry-forward for the Slice 4 doc-wrap (which owns the implemented-on-main
  status edits) and the integration/final-gate spawns to fold in, rather than churning the spec header
  per-slice mid-build. No predecessor doc referenced by the spec was deleted by this slice.

No version bump (Decision 14) — verified: `pyproject.toml` version, `__init__.py __version__`, and
`tests/base/test_init.py::test_version` all read `0.0.12`; `tests/base/test_init.py` not in the slice
diff. Slice-1 TODO anchors all discharged (`utils/converters.py`, `utils/inputs.py`, `forms/converter.py`,
`forms/inputs.py`, `mutations/inputs.py` — the last replaced with non-TODO `spec-039` provenance, the
rest removed); all surviving `TODO(spec-039 …)` anchors are Slice-2 / Slice-3-labeled (correctly intact).

### Summary

Slice 1 ships the two net-new DRF input modules — `rest_framework/serializer_converter.py`
(`convert_serializer_field(field, *, is_input=True)`: fail-loud MRO dispatch on the shared
`convert_with_mro` skeleton, the `source`-axis reverse map → `InputFieldSpec`, id-like-suffix rule,
serializer-only relation, M3 strictness) and `rest_framework/inputs.py` (the `<Serializer>Input` /
`<Serializer>PartialInput` generators from the schema-time field set under the `SerializerInputShape`
descriptor identity, the `.fields`-wrapping discovery guard, and the per-declaration create-required
guard) — plus the four DRY promotions (P1.4 `convert_with_mro`, P2.1 `InputFieldSpec`, P2.2
`make_input_namespace`, P1.3 `make_shape_build_cache`) authored single-sited in `utils/` with the
form/mutation flavors re-pointed byte-equivalently. The import-not-redefine grep-guard DoD passes; the
fail-loud no-silent-`String` contract is single-sited; 481 focused tests pass. One Low finding (a
vacuous test assertion) is accepted-and-deferred. `Status: final-accepted`.

### Spec changes made (Worker 1 only)

None this pass. SR-1 and SR-3 evaluated and judged not to warrant a spec edit (each is governed by a
linked Decision the build implemented correctly; the sub-check phrasing is harmless shorthand). The
stale `Status: IN PROGRESS` header line is carried forward to the Slice 4 doc-wrap / integration / final
gate rather than churned per-slice mid-build. No deferral of an un-ticked sub-check (all four landed).
`check_spec_glossary.py` not re-run (no spec edit made this pass).
