# DRY review — `django_strawberry_framework/utils/` and every consumer surface

Reviewed 2026-07-10. Scope: all 13 `utils/` modules read in full (~3,100 lines), then a
package-wide sweep for (a) parallel code still spelled per-family that belongs in `utils/`,
(b) inline respellings of patterns a `utils/` helper already owns, (c) duplication inside
`utils/` itself, and (d) a reuse map so **eventually implemented code reaches for the existing
helper instead of re-spelling it**. Every finding below was verified against source, not
docstrings. Ordered most-impactful first within each part.

Legend: **[P]** promote new shared helper · **[R]** re-seat onto an existing helper ·
**[T]** tighten in place · **[G]** guidance for future code. Effort: S / M / L.

---

## Part A — Cross-family parallels to PROMOTE into `utils/`

### A1. [P/M] The form + serializer relation decoders are one helper spelled twice
`forms/resolvers.py::_decode_form_relation_single` / `::_decode_form_relation_multi` and
`rest_framework/resolvers.py::_decode_relation_single` / `::_decode_relation_multi` share an
identical spine: skip-value early-out → `type_check_relation_id` → error short-circuit →
`visible_related_object` → `None` → `relation_field_error(graphql_name)` → project the result.
~45 lines per single copy, ~43 per multi copy (~176 total). This is the largest remaining
write-flavor duplication, and it guards the **cross-flavor security invariant** (a writer must
not attach a row they cannot see) — exactly the class of contract `utils/` exists to
single-site.

Promote a `utils/write_values.py::decode_visible_relation(value, *, graphql_name,
related_model, info, skip=, project=, async_recourse=)`:
- `skip` — form passes `value in form_field.empty_values`, serializer `value is None`;
- `related_model` — form reads `form_field.queryset.model`, serializer `spec.related_model`;
- `project` — form's `_to_form_key_value(obj, form_field)`, serializer's `obj.pk`;
- `async_recourse` — each flavor's existing constant.

The **single** decoders fold verbatim. The **multi** decoders share the contract but not the
query strategy (form: per-element visibility query, needs the object for `to_field_name`;
serializer: batched `visible_related_objects` + `pks_all_present` per rev6 #3) — promote the
multi only with the strategy as an explicit parameter, or fold just the per-member
error-short-circuit loop and keep the strategy at each site. A fourth write flavor then gets
the visibility-on-every-branch decode for free instead of forking copy #3.

### A2. [P/M] The kind-dispatch decode loop (form + serializer)
`forms/resolvers.py::_decode_form_data` and `rest_framework/resolvers.py::_decode_input_object`
both build `{spec.input_attr: spec}`, iterate `iter_provided_input_fields(data)` (already
shared), then branch on `spec.kind` into relation/file/scalar arms, keying results into
per-flavor dicts and short-circuiting on the first `FieldError` (~55–60 lines each).
Divergences a promoted walker would thread: the destination key (`form_field_name` vs
`target_name`), the FILE destination (form splits a `provided_files` dict for Django's
`files=`; serializer routes into `data` — deliberate, see F7), and the serializer-only
`NESTED_*` recursion with `join_error_path`. Promote as a routing-table walk
(`kind → handler`) in `utils/write_values.py`; each flavor supplies its handler map and
destination policy. The model flavor's `mutations/resolvers.py::_decode_relations` is a
*near*-parallel with a genuinely different key space (model attrs, batched id-set contract) —
leave it out (see F5).

### A3. [P/M] One collision-message family, currently five spellings
The "two distinct X claim one name … Rename one …" contract is spelled at:
- `utils/inputs.py::materialize_generated_input_class` ("is materialized by two distinct
  {family_label} input classes: A vs B. Rename one …");
- `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built` ("is claimed by two distinct
  {family_label} classes: A vs B. Rename one {rename_noun} …");
- `forms/inputs.py::_guard_input_attr_collisions` (attr + graphql-name arms, raises first);
- `rest_framework/inputs.py::_collect_input_attr_collision_messages` (attr + graphql-name +
  source arms, collects for aggregation per rev6 #5).

Promote (i) a message builder `utils/inputs.py::duplicate_name_message(noun, name, existing,
claimant, family_label, rename_noun)` that the two `utils/inputs.py` raisers and both flavor
guards format through, and (ii) an `iter_input_field_collisions(field_specs, *, subject,
attr_of, name_of, source_of=None)` generator yielding messages — the form wraps the first in a
raise, the serializer aggregates. The wording stays byte-stable per flavor via the threaded
nouns; the *skeleton* (seen-dict walk + the two/three collision arms) lands once.

### A4. [P/M] The filter/order `_build_input_fields` triple-emission scaffold
`filters/inputs.py::_build_input_fields` and `orders/inputs.py::_build_input_fields` still
spell the same per-field core (~35 lines each): `python_attr = top_name.replace("__", "_")` →
`graphql_name = _camel_case(python_attr)` → `{"default": None}` + conditional `name=` alias →
related-branch `Annotated[target_name, strawberry.lazy(INPUTS_MODULE_PATH)]` with the
`target is None → skip` placeholder rule → `triples.append(...)` +
`_field_specs[(set_cls, python_attr)] = FieldSpec(...)`. A promoted emitter needs: the
field iterator, `related_target_of`, `leaf_annotation_of`, `django_source_path_of`,
`field_specs`, `module_path`, `input_type_name_for` — the same parameterization shape
`GeneratedInputArgumentsFactory` already proved out for the BFS.

Two sub-pieces are independently worthwhile even if the full emitter is deferred (but do not
ship the sub-piece *as* the fix and defer the emitter without a real reason — prefer the full
promotion):
- **`_optional_field_kwargs(python_attr, graphql_name)`** — the `{"default": None}` +
  conditional `name=` micro-pattern appears **five times** (3× in `filters/inputs.py`
  including the operator-bag loop, 1× in `orders/inputs.py`, and the related arm);
- **the lookup-path flattening** `top_name.replace("__", "_")` — see A9.

### A5. [P/S] `check_permission` body duplicated because plain forms are not `DjangoMutation`
`mutations/sets.py::DjangoMutation.check_permission` and
`forms/sets.py::DjangoFormMutation.check_permission` are functionally byte-identical
(~18 lines): iterate `meta.permission_classes`, run `has_permission` through
`reject_async_in_sync_context(..., recourse=_PERMISSION_ASYNC_RECOURSE)`, AND the results.
The serializer flavor inherits the model's, so this is the only fork. Promote a module-level
`run_permission_classes(mutation_self, info, operation, data, instance)` next to the
already-shared `authorize_or_raise`; both `check_permission` methods delegate. An
authorization-seam fork is the exact "fix one side, miss the other" bug class the utils
permission walk was created to close.

### A6. [P/S] The scalar leaf-decode compose is hand-spelled three times
`unencodable_text_error(...)` → short-circuit → `raw_choice_value(value)` is spelled in
`mutations/resolvers.py::_decode_relations` (scalar tail), `forms/resolvers.py::_decode_form_data`,
and `rest_framework/resolvers.py::_decode_input_object`. The primitives are shared; the
two-step compose is not. Promote `utils/write_values.py::decode_scalar_leaf(graphql_name,
value) -> tuple[Any, FieldError | None]`; form + serializer adopt verbatim, the model composes
it *before* its flavor-specific `_explicit_null_error` / `_make_aware_if_naive` steps (which
stay put — see F6).

### A7. [P/S] Decode-kind constants + `*FieldConversion` value objects declared twice
`forms/converter.py` and `rest_framework/serializer_converter.py` each declare
`SCALAR/RELATION_SINGLE/RELATION_MULTI/FILE` string constants (serializer adds `NESTED_*`) and
a near-identical `__slots__ = ("annotation", "kind", "required")` conversion value class. The
dispatchers already share `utils/converters.py::convert_with_mro`; the kinds are one
conceptual enum spelled twice — and `utils/inputs.py::InputFieldSpec.kind` documents these
same kind strings a third time in prose. Single-source the kind constants in `utils/` (next to
`InputFieldSpec`, which is their type-level consumer) and let the serializer extend with its
`NESTED_*` pair; optionally share a conversion base class.

### A8. [P/S] The `get_filters`/`get_fields` cache-write gate
`filters/sets.py::FilterSet.get_filters._build` and `orders/sets.py::OrderSet.get_fields._build`
both end with the identical two-condition write gate: cache only when the related collection
is declared in `cls.__dict__` AND no related entry still holds an unresolved string lazy
target. The surrounding `expanded_once` skeleton is already shared; promote the gate as
`should_cache_expansion(cls, *, related_attr, target_slot)` so the string-lazy-target rule
(a correctness rule: caching too early pins a half-resolved expansion) has one owner.

### A9. [P/S] Lookup-path flattening has no owner
`top_name.replace("__", "_")` / `field_path.replace("__", "_")` appears in
`filters/inputs.py::_build_input_fields`, `orders/inputs.py::_build_input_fields`,
`utils/permissions.py::_check_method_name`, and `orders/sets.py` (the `_dst_order_` alias
builder). Same transform, two purposes (python-attr derivation; identifier mangling). Given the
prefetch `to_attr` memory (LOOKUP_SEP must never survive into generated attrs), this transform
is load-bearing enough to deserve a named owner:
`utils/strings.py::flatten_lookup_path(name)`. Future code then greps to one symbol when the
escaping rules change (as they already did once for the `$`-delimiter sidecar work).

### A10. [P/S] The optional-widening tail in the input-build loops
`forms/inputs.py::build_form_input_class` and `rest_framework/inputs.py::_walk_serializer_fields`
both end each field with: `if not required: annotation = annotation | None;
kwargs["default"] = strawberry.UNSET` plus the `name=` alias when
`python_attr != graphql_name`. Promote `optional_input_field(annotation, *, python_attr,
graphql_name, required)` → `(annotation, kwargs)` in `utils/inputs.py`, next to
`build_strawberry_input_class` whose required-vs-optional contract (presence of `default`)
this tail exists to satisfy — putting the widening rule beside the contract it feeds.

---

## Part B — Respellings to RE-SEAT onto existing `utils/` helpers

### B1. [R/S] `types/finalizer.py` re-spells `loaded_attr`
The phase-2.5 auth bind does `sys.modules.get("django_strawberry_framework.auth.mutations")`
then calls `bind_auth_mutations()` — behavior-identical to
`utils/imports.py::loaded_attr(module_path, attr_name)`, whose docstring states the exact
opt-in rationale the finalizer's inline comment re-derives. `registry.py::_clear_if_loaded`
already routes the SAME module's already-loaded lookup through `loaded_attr`, so the finalizer
is the one inconsistent site. Replace with
`bind = loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")`.

### B2. [R/S] `mutations/sets.py::resolver_seams` — 4× inline strict import-attr
`getattr(importlib.import_module(module_path), name)(...)` is spelled four times inside the
generated `resolve_sync`/`resolve_async` bodies. None of the three `utils/imports.py` owners
fit (best-effort would mask a broken internal import; `loaded_attr` only reads loaded modules;
`require_optional_module` returns the module and reframes the error). This is a genuine gap in
the import-handling family `utils/imports.py` is chartered to own ("new optional-import
handling … belongs here, not inline at a fourth call site" — its own docstring). Add the
strict `import_attr(module_path, attr_name)` primitive there and collapse the four spellings.

### B3. [R/S] `connection.py::_window_edge_class` — unbounded `of_type` peel
`while isinstance(edge_type, StrawberryContainer): edge_type = edge_type.of_type` is the exact
unbounded-loop hazard `utils/typing.py::unwrap_graphql_type` was written to eliminate (bounded
by `_MAX_TYPE_WRAPPER_DEPTH`, loud on a cyclic chain). For `list[Edge[Node]]` the
`StrawberryContainer` stop and the no-`of_type` stop land on the same leaf. Either call the
shared helper, or — if the `isinstance` gate is judged load-bearing — add a bounded
container-scoped variant *in `utils/typing.py`* so the Power-of-Ten cap has one owner. Do not
leave the raw loop.

### B4. [R/S] `testing/client.py` — the sync/async `query()` twin tail
`TestClient.query` and `AsyncTestClient.query` share a byte-identical un-colored tail:
`_decode(...)` → construct `Response(..., response=resp)` → the explicit
`assert_no_errors`-raise. The head (`_build_body`) is already shared; only the
`await self.request(...)` line is colored. Factor a `_finish_response(resp, *, files,
assert_no_errors) -> Response` both call, so the spec-043 Decision-5 guard (the explicit raise
that survives `python -O`) is written once. Not calling `super().query()` stays correct — this
factors below that decision, not around it.

---

## Part C — Duplication INSIDE `utils/` itself

### C1. [T/S] `utils/errors.py::field_error` — the str-or-iterable coercion twice
`messages` and `codes` each inline the same "bare str → one-element list; iterable →
`[str(x) …]`" coercion on adjacent lines. Extract a module-private `_str_list(value)` used by
both, so the coercion rule (the one the DRF `ErrorDetail` flattener depends on) has one body.

### C2. [T/S] `utils/inputs.py::resolve_effective_fields` — the unknown-name check twice
The `fields` branch and the `exclude` branch spell the identical
`unknown = [name for name in seq if name not in basis]` + `ConfigurationError` raise, differing
only in the `fields`/`exclude` literal. Hoist a closure `_reject_unknown(seq, key)`; the pinned
message stays byte-identical via the threaded key.

### C3. [T/S] `utils/inputs.py` — two collision raises, one skeleton
`materialize_generated_input_class` and `GeneratedInputArgumentsFactory._ensure_built` raise
near-identical "two distinct … A vs B. Rename one …" messages with independently-spelled
`__module__`.`__qualname__` interpolations. Fold both through the A3 `duplicate_name_message`
builder (this is the intra-utils half of that family).

### C4. [T/S] `utils/querysets.py` — the visibility-or-default fallback twice
`visible_related_object` and `visible_related_objects` both open with
`related_visibility_queryset(...)` then a `None → _default_manager` fallback (`.filter(pk=pk)`
vs `.all()`). Extract `related_visibility_queryset_or_default(related_model, info,
async_recourse)` returning the base queryset; each caller keeps its own tail. The
"no primary type ⇒ default-manager, no visibility contract" rule then has one body — it is a
security-adjacent rule and currently two.

### C5. [T/S] `utils/querysets.py` — pk stringification twice
`stringified_pks_present` and `pks_all_present` each spell `{str(pk) for pk in …}`. A private
`_stringified(pks)` makes the type-agnostic comparison basis (the GlobalID-in-filter
string-explosion class from the PG-tier work) single-bodied.

### C6. [T/S] `utils/permissions.py::extract_branch_value` re-spells the dict-vs-dataclass read
Its `isinstance(dict) → .get` / else `getattr` branch duplicates the shape
`utils/input_values.py::iter_input_items` owns for iteration. Add the missing single-field
primitive `input_values.py::input_field_value(input_value, name)` and have
`extract_branch_value` compose it with `is_inactive_value` — then the dict-vs-dataclass sniff
lives in exactly one module, matching that module's charter.

### C7. [T/S] `utils/inputs.py::make_input_namespace` — micro
Its `(ledger, clear_fn)` pair re-spells what `make_shape_build_cache` returns. Compose
(`ledger, clear_fn = make_shape_build_cache()`) or accept as-is; note only for completeness.

---

## Part D — Family-internal duplication surfaced by the sweep

### D1. [T/S] `orders/sets.py::OrderSet.apply_sync` / `::apply_async` — unfactored shared tail
Both spell the identical ~10-line tail (`_normalize_input` → empty-out → `get_flat_orders` →
`_resolve_order_expressions` → conditional `annotate` → `order_by`). The filter side already
extracted its analogue (`_apply_common_prelude` / `_apply_common_finalize`); mirror it with an
order-local `_apply_orderings(queryset, input_value)` so the sync/async pair differs only in
the permission-check coloring.

### D2. [G/–] The one-line delegate boilerplate is acceptable — but stop growing it
`_invoke_permission_method`, `_active_permission_field_paths`, `_input_type_name_for`,
`_request_from_info`, `_extract_branch_value` exist as verbatim twin one-line delegates on both
`FilterSet` and `OrderSet` (~13–18 lines each including docstrings). The bodies are already
single-sited in `utils/`; what is duplicated is wrapper + docstring. Two root-cause options if
this is worth closing: a shared mixin parameterized by the family config
(`related_attr`/`logic_keys`/`unset_sentinel`/`family_label` as class attrs — the same shape
`GeneratedInputArgumentsFactory` uses), or accept them as documented seams. **Rule for future
families: new delegates of this shape must be class-attr config consumed by a shared mixin
method, not a third copied wrapper.**

---

## Part E — Reuse map: which helper owns which pattern (for all future code)

Any new code that needs one of these MUST call the owner, never re-spell:

| Pattern | Owner |
|---|---|
| Resolve Django request from `info.context` (incl. Channels) | `utils/permissions.py::request_from_info` |
| Walk dict-or-dataclass input items / single field | `utils/input_values.py::iter_input_items` (+ C6's `input_field_value`) |
| "Is this input value supplied?" (`None`/`UNSET`) | `utils/input_values.py::is_inactive_value` |
| Classify supplied top-level set-input fields | `utils/input_values.py::iter_active_fields` |
| Walk PROVIDED fields of a bound write input (UNSET-strip) | `utils/inputs.py::iter_provided_input_fields` |
| Build a Strawberry input class / required-vs-optional rule | `utils/inputs.py::build_strawberry_input_class` |
| Pin a generated input as a module global / ledger / clear | `utils/inputs.py::materialize_generated_input_class` + `make_input_namespace` |
| Generated input-name derivation | `utils/inputs.py::generated_input_type_name` + `pascalize_token` |
| `Meta.fields`/`exclude` shape + narrowing + dropped-required | `utils/inputs.py::normalize_field_name_sequence` / `resolve_effective_fields` / `guard_dropped_required` |
| Converter dispatch (precheck → MRO → raise) | `utils/converters.py::convert_with_mro` |
| Write-error leaves / Django `ValidationError` mapping / path join | `utils/errors.py` |
| Per-value write checks (surrogates, choices, relation-id shape) | `utils/write_values.py` |
| Relation visibility (object / batched / queryset seed) | `utils/querysets.py::visible_related_object(s)` / `related_visibility_queryset` |
| Manager coercion, visibility hooks sync/async, model/queryset seed | `utils/querysets.py::normalize_query_source` / `apply_type_visibility_*` / `model_for` / `initial_queryset` |
| Reject `async def` hook in a sync seam | `utils/querysets.py::reject_async_in_sync_context` (message template lives THERE) |
| Sync-pipeline recourse wording | `utils/querysets.py::sync_pipeline_recourse` |
| Optional/soft imports (best-effort, already-loaded, raising) | `utils/imports.py` (add B2's strict `import_attr` as the fourth) |
| Relation-shape classification / accessor / composite-pk | `utils/relations.py` |
| Case conversion (snake/pascal/camel; add A9's lookup-flatten) | `utils/strings.py` |
| Type unwrapping (`of_type` stacks, list layers), async-callable | `utils/typing.py` |
| Connection windows, sidecar kwargs, marker/probe arithmetic | `utils/connections.py` |
| Permission-gate dispatch (`check_<field>_permission`, dedup) | `utils/permissions.py::invoke_permission_method` + `run_active_input_permission_checks` |

And the general rules the codebase already demonstrates, restated for future slices:
1. **Second copy = promote.** The moment a second family/flavor needs a mechanic, it moves to
   `utils/` with the divergence as parameters (the `family_label`/`flavor` message-knob shape) —
   never hand-mirrored "for now" (AGENTS.md: no ship-it-today-defer-the-real-fix sequencing).
2. **Promote mechanics, keep semantics at the call site.** Every successful utils module
   (`input_values`, `converters`, `connections`) owns traversal/dispatch/arithmetic and threads
   leaf semantics in as config. New helpers should match that split, not absorb flavor logic.
3. **Byte-stable messages via threaded nouns.** Pinned error wording survives promotion when
   the flavor noun is a parameter (`normalize_field_name_sequence`, `resolve_effective_fields`
   prove this) — "the message would change" is not a reason to keep a copy.
4. **Cycle-safety by depending on neither family** (duck-typed `set_cls` + config), and
   function-local imports only at the established cross-package seams.
5. **One vocabulary owner per name transform** — plan-time GraphQL spellings vs Python kwargs
   (`CONNECTION_ORDER_KWARG_GRAPHQL`) showed why: when a transform has two readers, the twin
   spelling must live next to the primary or drift hides real fallbacks.

---

## Part F — Verified NON-findings (deliberate divergence; do not "fix")

1. `filters/sets.py` related-visibility child seed uses
   `child_model._default_manager.all()`, NOT `initial_queryset(target_type)` — the owner model
   may be a subclass; previously verified and rejected as a DRY win.
2. `optimizer/walker.py::_plan_connection_relation` seeds from
   `field.related_model._default_manager.all()` by documented design (its comment explicitly
   contrasts with `initial_queryset`).
3. `permissions.py` cascade walk pins `.using(queryset.db)` — alias pinning is a ported
   invariant `initial_queryset` deliberately lacks; not worth an alias-parameterized seed for
   one caller.
4. `types/finalizer.py` uses Strawberry's `to_camel_case`, not `graphql_camel_name` — the
   collision check must match Strawberry's actual default converter, and the two algorithms
   differ.
5. `mutations/resolvers.py::_decode_relation_id_set` does not use `type_check_relation_id` —
   its raw-pk half is a set-level all-or-nothing existence/visibility contract
   (documented in `utils/write_values.py::type_check_relation_id`).
6. The model scalar tail's `_explicit_null_error` + `_make_aware_if_naive` stay model-only —
   form/serializer delegate null/datetime handling to the bound form / DRF field.
7. Form FILE decode routes into `files=`, serializer into `data` — Django-forms vs DRF read
   contracts; blocks (and correctly bounds) a fully-shared decode-loop destination (A2).
8. `rest_framework/sets.py::SerializerMutation.build_input` does not use `cached_build_input` —
   its cache key is the post-build descriptor; forcing the shared path would build twice (P1.7).
9. `utils/typing.py::unwrap_return_type` (one layer) vs `unwrap_graphql_type` (full stack) —
   different contracts, both documented.
10. The sync/async twins in `utils/querysets.py` (`post_process_queryset_result_*`) and the
    filter/order `apply_*` split are inherent function-color, not duplication (D1 targets only
    the un-colored tail).
11. The per-family `materialize_input_class` / `clear_*_input_namespace` wrappers stay
    module-local on purpose — each pins its own module's `__dict__` identity for the
    parked-globals lifecycle; the mechanics are already single-sited.
12. `filters/inputs.py::normalize_input_value` vs `orders/inputs.py::normalize_input_value` —
    different return contracts (form-data vs `(path, direction)` tuples); the shared traversal
    already lives in `iter_active_fields`.
13. `FilterArgumentsFactory` / `OrderArgumentsFactory` subclass bodies ARE the per-family
    config; the BFS is already shared. Irreducible.
14. `RelatedFilter.filterset` / `RelatedOrder.orderset` property trios — public API nouns over
    the shared `RelatedSetTargetMixin`; correctly not merged.
15. `optimizer/_context.py` context read/write is plan-stashing, not request resolution — not a
    `request_from_info` duplicate.
16. BigAutoField→Int mapping and the duplicate-graphql-name tolerance are intentional and
    load-bearing (the real gap, same-type camelCase collision, is already fixed via
    `_audit_field_surface`).

---

## Suggested landing order

1. **A1 + A2 + A6** (one slice: the write-flavor decode substrate — biggest win, one test
   surface, and the security-invariant single-siting).
2. **A3 + C3** (the collision-message family, intra- and cross-flavor halves together).
3. **A5** (permission-seam fork — small, authorization-critical).
4. **B1–B4** (mechanical re-seats; each is minutes of work and closes a documented hazard —
   B3 removes an unbounded loop).
5. **A4 + A8 + A9 + A10 + D1** (the filter/order/forms input-build scaffolding).
6. **C1–C6** (intra-utils polish; fold into whichever slice touches the file).

All promotions must land with tests in the same change (AGENTS.md), keep pinned error wording
byte-identical via threaded nouns, and follow the live-first mandate for any newly reachable
line.
