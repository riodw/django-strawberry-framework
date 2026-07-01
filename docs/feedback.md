# DRY review — the three-flavor write stack (model / form / serializer), utils-first

**Scope:** `django_strawberry_framework/utils/` (the reuse inventory), then the three write
flavors (`mutations/`, `forms/`, `rest_framework/`) that now form a three-way mirror.
**Mode:** findings only — no code edited. Every item below names the duplication, the
evidence sites, and the consolidation lever. Verify before implementing.

**The headline:** spec-039 did its P-numbered DRY homework well — the pipeline skeleton,
the async boundary, the error-leaf ctors, the namespace/cache factories, and the MRO
converter dispatch are all genuinely single-sited now. But adding the THIRD sibling
changed the economics of everything that was left as a "tolerable pairwise parallel" in
038: what was 2 copies is now 3 (sometimes 4, counting the plain-form base), and several
"deliberately deferred" items (P2.3, P2.7 notes in the code) now have enough consumers to
justify promotion. The pattern to hunt is no longer "X mirrors Y" — it is **the per-flavor
plumbing kit**: every new write flavor re-spells the same ~8 pieces of glue. Single-site
the kit and flavor N+1 (a Pydantic flavor? an attrs flavor?) becomes ~half the code.

---

## The utils/ reuse inventory (what already exists — route consolidations HERE)

Anything promoted should land in `utils/` (cycle-safe by construction) or
`mutations/` (the root flavor all others already import from). Existing homes:

- `utils/strings.py` — `snake_case`, `pascal_case`. Docstring declares itself the single
  home for case conversion (relevant to Md5/Md6 below).
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

### M1 — The per-flavor resolver plumbing stack is re-spelled three (and a half) times

Each flavor hand-copies the SAME two layers of resolver glue:

**(a) The module-level entry pair/trio.**
`mutations/resolvers.py::resolve_mutation_sync` + `resolve_mutation_async`;
`forms/resolvers.py::resolve_form_sync` + `resolve_form_async`;
`rest_framework/resolvers.py::resolve_serializer_sync` + `resolve_serializer_async` +
`_run_serializer_pipeline_sync`. Every sync entry is the identical
"UNSET-default kwargs → positional body" adapter; every async entry is the identical
one-liner `await run_pipeline_async(<body>, mutation_cls, info, data, id)`. The bodies
differ; the entries are byte-parallel modulo names and docstring nouns.

**(b) The `resolve_sync` / `resolve_async` classmethod seams.**
`mutations/sets.py::DjangoMutation.resolve_sync/resolve_async`,
`forms/sets.py::DjangoModelFormMutation.resolve_sync/resolve_async`,
`forms/sets.py::DjangoFormMutation.resolve_sync/resolve_async`,
`rest_framework/sets.py::SerializerMutation.resolve_sync/resolve_async` — EIGHT
classmethods, each the identical "function-local import (cycle guard) + delegate with
`data=`/`id=`" body, differing only in the imported name (and the plain flavor's missing
`id`).

**Lever:** a `make_resolver_entries(sync_body)` factory in `mutations/resolvers.py`
returning the `(resolve_sync, resolve_async)` pair, and/or a
`resolver_seams(module, sync_name, async_name)` classmethod-pair factory in
`mutations/sets.py` for layer (b). Fifteen-ish near-identical defs collapse to three
factory calls; flavor N+1 gets both layers for free. This is the single biggest
line-count win in the review.

### M2 — The UNSET-strip input walk + the scalar decode tail, three copies

`mutations/resolvers.py::_decode_relations`, `forms/resolvers.py::_decode_form_data`, and
`rest_framework/resolvers.py::_decode_input_object` all open with the identical walk:

```
for field in data.__strawberry_definition__.fields:
    python_name = field.python_name
    value = getattr(data, python_name, strawberry.UNSET)
    if value is strawberry.UNSET:
        continue
```

then per-field: resolve the spec, branch on kind (relation single/multi → pick a decoder;
FILE → route to the flavor slot; scalar → the SAME `_unencodable_text_error` preflight +
`raw_choice_value` unwrap), first error short-circuits to `({}, error)`. The three tails
genuinely diverge (model adds `_explicit_null_error` / `_make_aware_if_naive`; form splits
`files=`; serializer recurses nested with `path_prefix`) — do NOT merge the kind handlers.
But the walk itself, the spec lookup, the short-circuit protocol, and the scalar
preflight+unwrap sequence are mechanics, re-spelled 3×.

**Lever (minimal):** an `iter_provided_input_fields(data)` generator in `utils/inputs.py`
yielding `(python_name, value, field)` — kills the 4-line preamble at all three sites and
gives future flavors the one blessed way to read a bound input. **Lever (fuller):** also
promote a `decode_scalar_value(field_path, value) -> (decoded, error)` pairing the
preflight with `raw_choice_value`, since that exact two-step appears verbatim in all
three decoders (the model flavor wraps it with its two extra checks).

### M3 — The relation-id structural type-check is spelled three different ways

The "GlobalID → `decode_model_global_id` (non-OK → uniform relation error) | raw pk →
`_coerce_relation_pk_or_none` (None → uniform relation error)" two-branch check exists as:

- `rest_framework/resolvers.py::_type_check_relation_id` — cleanly factored (the 039
  batched-multi refactor forced it out);
- `forms/resolvers.py::_decode_form_relation_single` steps (i)+(ii) — the SAME body
  inlined (then diverges: form-key conversion via `to_field_name`);
- `mutations/resolvers.py::_decode_relation_id_set`'s element loop — the GlobalID half of
  the same check (its raw-pk half is deferred to `_raw_pk_relation_error`, a real
  semantic difference).

The serializer version is the general one. **Lever:** promote
`_type_check_relation_id` (drop the underscore) to `mutations/resolvers.py` next to
`_coerce_relation_pk_or_none` / `relation_field_error`; the form single-decoder calls it
and keeps only its `empty_values` pass-through + `to_field_name` reduction. The model
path can adopt it for its GlobalID branch or be left alone (its raw-pk semantics
deliberately differ) — verify which before touching. This is security-adjacent code:
one implementation of "what counts as a well-formed relation id" beats three.

### M4 — `resolve_effective_form_fields` vs `resolve_effective_serializer_fields`: one spine, two ~60-line copies

`forms/inputs.py::resolve_effective_form_fields` and
`rest_framework/inputs.py::resolve_effective_serializer_fields` are the same function:
normalize `fields` + `exclude` → mutual-exclusion raise → take the basis dict →
fields-branch unknown-name raise → exclude-branch unknown-name raise (identical loop,
identical message template) → empty-effective-set raise. The only real deltas: the flavor
label in the four messages, the basis (`base_fields` vs the writable-filtered
`field_map`), and one adjective ("unknown form field(s)" vs "unknown or non-writable
serializer field(s)"). The read-only/HiddenField drop is a serializer-side pre-step that
can stay at the call site.

**Lever:** `utils/inputs.py::resolve_effective_fields(basis: dict, *, fields, exclude,
flavor: str, unknown_noun: str) -> dict` — the same "hoist the one divergent string"
move `normalize_field_name_sequence(flavor=...)` already made. Each flavor keeps a thin
wrapper that supplies its basis. ~120 lines → ~60 + 2 small wrappers.

### M5 — The `_validate_meta` backing-class prologue is a third copy now

`forms/sets.py::DjangoModelFormMutation._validate_meta` and
`rest_framework/sets.py::SerializerMutation._validate_meta` re-spell, clause for clause:
`reject_unknown_meta_keys` → require the backing class (`form_class` /
`serializer_class`: presence raise, type-gate raise) → `_resolve_model` (the same
three-level `getattr` chain, `_meta`/`Meta` being the only delta) → the near-identical
"resolves no model; a Model{Form,Serializer} must set Meta.model so the mutation has a
model + a DjangoType to return" raise → `non_delete_operation_error` gate →
fields/exclude validate-then-store-raw → `_validate_permission_classes` →
`_ValidatedMutationMeta(...)`. The 038 review judged this "one spine, don't over-merge"
at two copies; at three (plus the plain-form base sharing half the spine) the spine has
proven stable across two spec generations and the serializer flavor added its extras
(optional/injected/nested/select_for_update) BETWEEN spine clauses without bending them.

**Lever:** promote to `mutations/sets.py` a
`require_backing_class(name, meta, *, key, expected, base_label) -> type` (presence +
type-gate + the targeted messages) and a
`resolve_backed_model_or_raise(cls, meta, *, base_label, noun) -> model` (the
resolve + no-model raise). The per-flavor matrices keep their own extra clauses and
ordering. Do NOT attempt a whole-`_validate_meta` template — the plain-form flavor's
operation-rejected-first ordering and the serializer's fingerprint tail are genuinely
flavor-shaped; consolidate the clauses, not the function.

### M6 — The generated-input type-name skeleton, three copies

`mutations/inputs.py::mutation_input_type_name`,
`forms/inputs.py::form_input_type_name`, and
`rest_framework/inputs.py::serializer_input_type_name` share the load-bearing skeleton:
`base = X.__name__` → `suffix = "PartialInput" if operation_kind == PARTIAL else
"Input"` → full shape → `f"{base}{suffix}"`, else `f"{base}{<token concat>}{suffix}"`.
The full-shape predicate and the token derivation differ per flavor (name-set equality
vs the serializer's descriptor digest) — those stay. But the suffix rule + the
full-vs-derived branching + the injective-token concatenation contract is the part that
must NOT drift (two flavors materialize into disjoint namespaces, but within a flavor a
name collision is the AR-M6 raise), and it is spelled 3×.

**Lever:** `utils/inputs.py::generated_input_type_name(base_name, operation_kind, *,
is_full_shape, token: str) -> str` with the PARTIAL/Input suffix rule single-sited;
each flavor computes its own `token`. Pairs naturally with Md5 (`_pascalize_token`
relocation) — do them together.

---

## MEDIUM

### Md1 — `guard_create_required_fields` vs `guard_create_required_serializer_fields`

Same shape: required-names set − effective set (− injected, serializer only) → sorted →
raise naming the dropped fields with near-identical wording
(`forms/inputs.py::guard_create_required_fields`,
`rest_framework/inputs.py::guard_create_required_serializer_fields`). The bases differ
(`field.required` over `base_fields` vs the writable field_map). Lever: a shared
`guard_dropped_required(required: set, effective, *, waived: set, flavor, recourse)`
core; the form's partial column-less guard stays separate (its scoping is load-bearing).

### Md2 — Five `*_ASYNC_RECOURSE` constants, one sentence

`mutations/resolvers.py::_MUTATION_ASYNC_RECOURSE`,
`forms/resolvers.py::_FORM_ASYNC_RECOURSE`,
`rest_framework/resolvers.py::_SERIALIZER_ASYNC_RECOURSE` are the SAME sentence with the
subject swapped ("A DjangoMutation" / "A form mutation" / "A serializer mutation");
`utils/querysets.py::_RELAY_ASYNC_RECOURSE` and
`mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE` are genuinely different wordings
(leave those). Lever: `utils/querysets.py::sync_pipeline_recourse(flavor_noun: str)`
template for the three pipeline flavors. Small, but it is the exact "hoist the one
divergent word" move the codebase already canonized in
`normalize_field_name_sequence(flavor=...)`.

### Md3 — "Resolve the related primary → visibility queryset or default manager", four spellings

The branch `related_type = registry.get(related_model); if None → default-manager /
skip (no visibility contract); else → visibility_scoped_related_queryset(...)` appears in
`utils/querysets.py::visible_related_object`, `utils/querysets.py::visible_related_objects`,
`mutations/resolvers.py::_raw_pk_relation_error`, and
`rest_framework/resolvers.py::_scope_specs_over_serializer`. Lever: a
`related_visibility_queryset(related_model, info, recourse) -> QuerySet | None` primitive
in `utils/querysets.py` (None = "no contract"); the four sites keep their divergent
None-handling (skip vs default-manager) explicit. This is the visibility contract — the
one place a drift is a data-leak bug class, per the module's own docstring.

### Md4 — The stringified-pk subset membership check, two implementations

`mutations/resolvers.py::_relation_membership_error` (queryset + declared vs queried pks
→ `{str(pk)...} <= present` → uniform relation error) and the serializer pair
`utils/querysets.py::visible_related_objects` (returns the stringified visible set) +
`rest_framework/resolvers.py::_decode_relation_multi`'s inline
`if not {str(pk) for pk in pks} <= visible`. Same no-existence-leak contract, same
str-coercion trick, two homes. Lever: either have the serializer multi-decoder call a
promoted membership primitive, or fold `_relation_membership_error`'s subset logic into
`utils/querysets.py` next to `visible_related_objects` so the coercion-compare rule is
written once.

### Md5 — `_pascalize_token` now has three consumers; move it next to `pascal_case`

`mutations/inputs.py::_pascalize_token` is imported cross-subsystem by
`forms/inputs.py` AND `rest_framework/inputs.py` (a private-name import ×2), and
`forms/inputs.py::form_input_type_name`'s own docstring says "the consolidation of the
token primitive into utils/inputs.py is flagged for the integration pass". Spec-039 P2.3
deliberately kept it sited at two consumers; at three, promote it —
`utils/strings.py` is the natural home (its docstring: "if a third style ever shows up
we'll add it here"). Rename public (`pascalize_token`), keep a deprecated alias if the
test suite addresses the old path.

### Md6 — `graphql_camel_name` still lives in `utils/inputs.py`, not `utils/strings.py`

Carried from the previous review (utils M4): `utils/strings.py` declares itself the
single home for case conversion, yet the third case converter sits in `utils/inputs.py`
(re-exported as `_camel_case` by the filter/order inputs modules, imported directly by
`mutations/resolvers.py`). Same move as Md5, same landing zone, one relocation + alias.

### Md7 — The default construction-kwargs hooks are the same three lines

`forms/sets.py::_default_get_form_kwargs` (`{"data":…, "files":…}` +
`if instance is not None: kwargs["instance"] = instance`) and
`rest_framework/sets.py::SerializerMutation.get_serializer_kwargs` (`{"data":…}` + the
same instance clause). Lever: a tiny shared
`construction_kwargs(instance=None, **base) -> dict` — low value alone, but it belongs
to the M1 "flavor plumbing kit" and a fourth flavor would copy it again.

---

## MINOR

### Mn1 — Three one-line aliases of `relation_field_error`

`mutations/resolvers.py::_relation_error`, `forms/resolvers.py::_relation_field_error`,
`rest_framework/resolvers.py::_relation_field_error` — each a one-line alias of the
shared ctor, each carrying a ~10-line docstring asserting the shape is single-sourced.
Delete all three; call `relation_field_error` directly. (The docstrings' provenance
content can move to the shared ctor, which already says most of it.)

### Mn2 — The `{"create": CREATE, "update": PARTIAL}` map, three spellings

`mutations/sets.py::_OPERATION_INPUT_KIND`, `forms/sets.py::_modelform_operation_kind`
(a function form of the same map), `rest_framework/sets.py::_SERIALIZER_OPERATION_INPUT_KIND`.
One `NON_DELETE_OPERATION_INPUT_KIND` map exported from `mutations/sets.py` (or
`mutations/inputs.py` next to CREATE/PARTIAL) serves all three.

### Mn3 — The two field-sequence re-binding wrappers P2.7 argued against

`mutations/sets.py::_normalize_field_sequence` and
`forms/inputs.py::normalize_form_field_sequence` are thin flavor-label re-bindings of
`utils/inputs.py::normalize_field_name_sequence`; the serializer flavor's own comments
(three separate P2.7 notes) hold up "no third wrapper" as the correct style. Inline the
flavor arg at the model/form call sites and delete both wrappers (check the test suite
addresses them by the module path first).

### Mn4 — `_reverse_map_for` and `_join_path` micro-wrappers (serializer)

`rest_framework/resolvers.py::_reverse_map_for` is a one-liner over
`_build_reverse_map(mutation_cls._input_field_specs)` used once-ish; `_join_path` is fine
but would come along free if M2's fuller lever lands. Fold on contact, not as a
standalone change.

### Mn5 — `input_type_name` re-builds the whole serializer shape

`rest_framework/sets.py::SerializerMutation.input_type_name` calls
`build_serializer_input_class` a second time (after `build_input` already built the
identical shape) to read `shape.type_name`. The shape cache makes it near-free at
runtime, but it is a re-derivation of the same value two seams apart; consider stashing
the built shape's `type_name` at bind (like `_input_field_specs`) so the name seam reads,
not rebuilds. (Efficiency/clarity more than DRY; flagged because the form flavor solved
the same problem with the cheaper `_form_input_type_name_for` re-derivation — a THIRD
strategy for the same seam.)

---

## Consolidation strategy (if/when implemented)

Order matters — do the utils/ landings first so the flavor edits are pure deletions:

1. **Relocations with aliases** (Md5, Md6): move `_pascalize_token` +
   `graphql_camel_name` into `utils/strings.py`; keep import-path aliases.
2. **New utils primitives** (M2's `iter_provided_input_fields`, M4's
   `resolve_effective_fields`, M6's `generated_input_type_name`, Md3's
   `related_visibility_queryset`, Md2's recourse template).
3. **Promotions inside `mutations/`** (M1's entry/seam factories, M3's
   `type_check_relation_id`, M5's `_validate_meta` clause helpers, Md1's guard core,
   Md4's membership primitive, Mn2's operation-kind map).
4. **Flavor rewires + deletions** (forms, rest_framework, then the model flavor's own
   call sites; Mn1/Mn3/Mn4 fold in here).
5. Each step is independently shippable; suite must stay green (byte-identical error
   messages where tests pin wording — the flavor-label parameterization pattern exists
   precisely to preserve that).

## Considered and deliberately NOT recommended

- **Merging the three decode kind-handlers into one dispatch table** (beyond M2's walk):
  the model's null/naive-datetime checks, the form's `files=`/`empty_values`/
  `to_field_name` semantics, and the serializer's nested recursion are flavor CONTRACTS,
  not mechanics. M2 stops at the walk + scalar tail on purpose.
- **A whole-`_validate_meta` template method** (see M5): clause ordering is
  flavor-semantic (plain form rejects `operation` FIRST by key-presence; serializer
  appends a fingerprint). Consolidate clauses, not the matrix.
- **Unifying the plain-form `{ ok errors }` body into `run_write_pipeline_sync`**: F6 in
  the skeleton's own docstring already scopes it out correctly (no instance, no slot, no
  re-fetch); the payload shape genuinely differs. Still true.
- **`_decode_relation_id_set` (model) vs the form/serializer decoders**: the model path's
  raw-pk-set semantics (all-or-nothing visibility, existence-only fallback for
  no-primary M2M) are deliberately different; only the GlobalID structural half (M3)
  is shared mechanics.
- **The `materialize_*_input_class` / `clear_*_namespace` thin wrappers ×3**: they
  already ride `make_input_namespace`; the wrappers are docstring carriers the tests
  address by name. Keeping them is the documented pattern — fine.
- **`utils/querysets.py::initial_queryset` as a FilterSet seed** (`filters/sets.py`):
  verified-and-rejected in a prior cycle (owner model may be a subclass) — do not
  re-flag.

## Method / caveats

- Read in full: `utils/` (all modules), `mutations/resolvers.py`, `forms/resolvers.py`,
  `rest_framework/resolvers.py`, `forms/sets.py`, `rest_framework/sets.py`, plus the
  seam-relevant regions of `mutations/sets.py`, `forms/inputs.py`,
  `rest_framework/inputs.py`, `mutations/inputs.py` (structure-verified), and the
  converter pair (already sharing `convert_with_mro`).
- Nothing here is a behavior change; every lever is a relocation/parameterization of
  code whose divergences are named strings or basis dicts. Where a divergence looked
  semantic (M3 model raw-pk path, Md1 partial guard, the decode tails) it is called out
  as NOT to be merged.
- Error-message wording is test-pinned in places — the flavor-label parameter pattern
  (`normalize_field_name_sequence`) is the template for preserving byte-identical
  messages through consolidation.
