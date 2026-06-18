# Spec 036 mutations — code review

Review of the implemented mutations subsystem (`django_strawberry_framework/mutations/` —
`inputs.py`, `sets.py`, `permissions.py`, `resolvers.py`, `fields.py`) against
`docs/spec-036-mutations-0_0_11.md`. Findings are tagged `CR-` (code review),
distinct from the spec's `AR-` / `Major-` / `Medium-` tags.

## Verdict

The implementation is high-quality and closely faithful to the spec. All five slices are
present, `143 passed, 1 skipped` across `tests/mutations/` + `tests/test_permissions.py`,
and the load-bearing wiring is confirmed live:

- The finalizer calls the bind at phase 2.5 (`types/finalizer.py:694-696` → `bind_mutations()`).
- `registry.clear()` co-clears the mutation declaration registry **and** the input/payload
  namespace ledger (`registry.py:520-532`).
- The AR-\* contract items have real, targeted tests (async surface, M2M replace/clear/omit/null,
  AR-H2 composite-constraint carve-out, AR-H4 wrong-type GlobalID, visibility-leak suppression,
  Decision-15 denial → top-level `GraphQLError`, shape-keyed naming + AR-M6 collision raise,
  the `IntegrityError` race fallback, the delete snapshot).

There is **one Major correctness/robustness bug** (reproduced live), **three Medium** contract
gaps, and a handful of Low/nits. Details below; verified-correct items I checked are listed last
so the review is honest about what is *not* broken.

---

## CR-1 (Major) — an uncoercible pk in a well-formed GlobalID crashes the pipeline instead of returning not-found

A `GlobalID` whose type slot resolves to the **correct** target model but whose `node_id` is
not a valid value for that model's pk column (e.g. `"abc"` for an integer pk) passes the
type-check and is then handed straight to the ORM as a bare pk. Django raises `ValueError`, which
is **not** caught — it surfaces as a top-level `GraphQLError` with `data: null`.

Reproduced (temporary test, now removed) on all three id paths:

```
UPDATE errors: [GraphQLError("Field 'id' expected a number but got 'abc'.", path=['updateItem'])]
UPDATE data:   None
DELETE errors: [GraphQLError("Field 'id' expected a number but got 'abc'.", path=['deleteItem'])]
DELETE data:   None
CREATE-REL errors: [GraphQLError("Field 'id' expected a number but got 'abc'.", path=['createItem'])]
CREATE-REL data:   None
```

(`global_id_for(ItemT, "abc")` for the top-level `id`; `global_id_for(CategoryT, "abc")` in
`data.categoryId`. M2M ids reach the ORM by the same path and fail identically.)

**Where:**
- `_coerce_lookup_id` (`resolvers.py:820-850`) decodes + type-checks the top-level `id` but
  returns `node_id` as an unvalidated string; `_locate_instance` (`resolvers.py:381-402`) then
  calls `queryset.get(pk=node_id)` catching only `model.DoesNotExist`.
- `_relation_visibility_error` (`resolvers.py:340-378`) runs `queryset.filter(pk__in=pks)` on the
  raw decoded ids — `pk__in=["abc"]` raises `ValueError` at query execution.

**Why it matters:**
1. It contradicts the spec: step 2 says "a miss returns a **not-found `FieldError` on `id`**"
   (`spec` line 371), and the relation-decode edge case promises "**never** a raw `DoesNotExist`"
   / a field-keyed `FieldError` with "the same no-existence-leak treatment" (`spec` line 504).
2. It contradicts the module's own docstrings — `_coerce_lookup_id` claims the id is decided
   "**without a DB read**… never coerced to a bare pk that would target the same-pk row of the
   right model" (`resolvers.py:836-839`). That claim only holds for the *wrong-model* case; the
   right-model-but-bad-pk case is exactly what is coerced to a bare pk and reaches `.get()`.
3. It diverges from the shipped node field, which handles the **identical** input cleanly:
   `relay.py::_coerce_pk_or_none` does `field.to_python(node_id)` inside
   `except (ValueError, ValidationError): return None`, so `node(id:)` returns `null` with **zero
   queries** (`tests/test_relay_node_field.py::test_node_uncoercible_pk_returns_null`). Two id
   surfaces, two behaviors, for the same client input.
4. The raw Django message (`"Field 'id' expected a number…"`) leaks the backend pk column type to
   the client.

**Fix:** coerce `node_id` through the target's pk field before the lookup, reusing the existing
`relay.py::_coerce_pk_or_none` (single-source it). A coercion failure maps to the existing
not-found `FieldError` on `id` (`_not_found_error`) for locate, and to `_relation_error(field_name)`
for the relation/M2M decode — i.e. an uncoercible pk becomes "not found", exactly like the node
field. Add a test for each path (none exists today — the Explore survey confirms `test_coerce_lookup_id_rejects_non_globalid` covers only raw/garbage strings, not a well-formed GlobalID with a bad pk literal).

---

## CR-2 (Medium) — `Meta.input_class` does wholesale replacement, not the documented spec-010 relation-override (merge)

The spec describes `Meta.input_class` as honoring the **relation-override contract from
spec-010**: "a consumer-authored input field is honored, **not clobbered** by a generated one"
(`spec` line 336 / DoD line 51), and the generator carries an `overrides` seam built for exactly
this. But the bind never uses it:

- `_materialize_input_for` (`sets.py:577-583`) materializes the consumer class **verbatim** and
  returns — it never calls `build_mutation_input(..., overrides=...)`.
- `overrides=` is therefore dead in production. The only call site is a Slice-1 unit test
  (`tests/mutations/test_inputs.py:408`). Yet `build_mutation_input`'s docstring asserts "In
  Slice 1 the seam is exercised directly; **Slice 2 wires it from `Meta.input_class`**"
  (`inputs.py:362-363`) — which is false.
- `_validate_input_class` (`sets.py:148-190`) only checks `supplied ⊆ expected`; it does **not**
  require completeness. So a consumer who supplies a *partial* `input_class` (a few field
  overrides) silently gets an input type **missing every other generated field**, rather than the
  generated fields merged in. (On `create` that degrades to a `full_clean` "field required"
  `FieldError` at request time; the input *type* is simply wrong.)

This may be intentional — line 336 also says "**substitute** a hand-written input **for** the
generated one" and the example comments "`overrides the generated ItemInput`" (`spec` line 231),
which read as wholesale replacement. If so, the merge contract is vacuous and the `overrides`
machinery + its docstring are stale. Either way the spec and code disagree with themselves.

**Recommendation:** pick one and make everything agree.
- If merge is intended: wire it — `build_mutation_input(model, …, overrides=frozenset(consumer field names))`
  and union the consumer's authored fields onto the generated remainder; add an end-to-end test
  declaring a partial `Meta.input_class` and asserting the generated fields survive.
- If replacement is intended (simpler, and matches "substitute for"): delete/quarantine the dead
  `overrides` param, fix `build_mutation_input`'s docstring, restate the spec's "relation-override
  contract holds / not clobbered" lines as "the whole input is consumer-owned", and either validate
  completeness in `_validate_input_class` or document that a partial `input_class` yields a partial
  input.

Note: there is no end-to-end test of `Meta.input_class` through the bind at all
(`test_meta_input_class_following_scheme_validates_clean` only checks class-creation validation).

---

## CR-3 (Medium) — `except IntegrityError` is over-broad and the message over-claims "uniqueness"

`_save_or_field_errors` (`resolvers.py:807-817`) catches **every** `IntegrityError` at `save()` and
routes it to `_integrity_error_field_errors`, which returns a single `FieldError` under `"__all__"`
reading **"A uniqueness constraint was violated."** (`resolvers.py:511-528`).

The spec scopes this strictly to the *`UniqueConstraint` race that beats `validate_constraints()`*
(`spec` line 374 / 500). But the catch also swallows `NOT NULL`, foreign-key, and `CHECK`
`IntegrityError`s and mislabels each of them as a uniqueness violation. `full_clean()` runs first
and catches most of these on the normal path, so the residual is rare — but when it fires, the
message is actively wrong.

Also: `_integrity_error_field_errors(model, provided_attrs)` ignores both parameters
(`del model, provided_attrs` at `resolvers.py:522`), and the two call sites compute
`set(scalar_and_fk_attrs)` / `provided` only to pass them into that no-op.

**Recommendation:** generalize the message to "A database constraint was violated." (or inspect
the error to distinguish unique vs. other), and either implement the promised per-constraint
refinement or drop the unused parameters.

---

## CR-4 (Medium / reconcile) — pipeline runs Authorize before Decode, deviating from the documented step order

The spec pipeline is **1 Decode → 2 Locate → 3 Authorize → 4 Validate** (`spec` lines 370-373).
The implementation defers relation decode past authorization:

- `create`: `_authorize_or_raise(...)` then `_decode_relations(...)` (`resolvers.py:652-654`).
- `update`: `_coerce_lookup_id` → `_locate_instance` → `_authorize_or_raise` → `_decode_relations`
  (`resolvers.py:688-697`).

The spec's **explicit** pins are both honored — authorize runs before validation for `create`
(`instance=None`) and after the visibility lookup for `update`/`delete` with the located instance.
And running authorize first is arguably **better**: an unauthorized caller triggers no relation
`get_queryset` visibility queries and gets no field-level decode feedback, so it neither does work
nor leaks relation visibility. The only observable change is error precedence — a request that is
*both* unauthorized *and* carries a malformed relation id now gets a top-level `GraphQLError`
(authorization) instead of a `FieldError` (decode).

**Recommendation:** keep the behavior, reconcile the prose — note in Decision 8 that relation
decode is intentionally deferred past Authorize for `create`/`update` (no relation work for
unauthorized callers). If strict step ordering is a contract, reorder instead. Flagging so the
spec↔code mismatch is a conscious decision, not drift.

---

## Low / nits

- **CR-5 (Low)** — `request_from_info` message doesn't fit the mutation seam. With the default
  `DjangoModelPermission` and no request in context, `request_from_info(info, family_label="DjangoMutation")`
  raises `"DjangoMutation.apply requires \`info.context\`…"` (`utils/permissions.py`) — but a
  mutation has no `.apply` method (the seam is `check_permission`). Cosmetic; the template assumes
  the filter/order `.apply` shape. Consider a family-neutral message or a mutation-specific label.

- **CR-6 (Low)** — file/image-column rejection precedes the consumer-override skip. In
  `build_mutation_input`, the `FileField`/`ImageField` `NotImplementedError`
  (`inputs.py:398-405`) is raised *before* the `if python_attr in overrides: continue` guard
  (`inputs.py:410`), so a consumer cannot supply a custom field for a file column via an
  `input_class` override — only `Meta.exclude` removes it. This is consistent with Upload being
  deferred to 037 and is documented as "exclude via `Meta.exclude`", but it interacts with the
  AR-M2 override story (CR-2); worth a one-line spec note.

- **CR-7 (Low)** — argless construction is an implicit contract. `_authorize_or_raise` does
  `mutation_cls()` (`resolvers.py:779`) and `check_permission` does `permission_class()`
  (`sets.py:509`); a consumer mutation or permission class with a required-arg `__init__` breaks at
  request time. This matches DRF (permission classes are instantiated argless) and is reasonable,
  but is currently undocumented.

- **CR-8 (Low / coverage)** — beyond the two gaps already noted (CR-1 uncoercible pk; CR-2 partial
  `input_class` through the bind), coverage is strong. The async surface, M2M semantics, the AR-H2
  carve-out, AR-H4, visibility-leak suppression, Decision-15 denial, naming/collision, the
  `IntegrityError` fallback, and the delete snapshot all have direct tests.

---

## Verified correct (checked, not broken)

Called out so the review is honest about scope:

- **Finalizer/registry wiring** — phase-2.5 bind is invoked (`finalizer.py:694-696`) and
  `registry.clear()` co-clears both ledgers (`registry.py:520-532`).
- **Choices-enum symmetry** — `_scalar_input_annotation` passes the *input* type name to
  `convert_choices_to_enum`, but that helper caches on `(field.model, field.name)`
  (`converters.py:353-355`), so the input **reuses the read type's enum** rather than minting a
  second, divergent one. No enum duplication or wire asymmetry. (`library.Book.circulation_status`
  is a real editable choices column that exercises this.)
- **Async boundary (AR-M4)** — `resolve_mutation_async` wraps the whole sync body in one
  `sync_to_async(_run_pipeline_sync, thread_sensitive=True)` (`resolvers.py:899-920`), and the
  transaction wraps the pipeline. No ORM/`await` interleaving. Tested
  (`test_async_pipeline_create_happy_path`, plus the no-leak-into-later-read test).
- **Delete snapshot (AR-M5)** — `force_load=True` fully materializes the optimizer-planned
  queryset before `delete()`, and the deletion runs against the **located** instance so the
  snapshot keeps its pk/id (`resolvers.py:724-759`). Tested.
- **`_provided_attr_names` reverse mapping (M3-1)** — `<field>_id` → field name goes through the
  relation index, not a blind suffix strip, so a scalar column literally named `*_id` (e.g.
  `object_id`) is not mangled into the `full_clean(exclude=…)` set. Tested.
- **GenericForeignKey exclusion (L3-1)** — `_is_forward_concrete_relation` requires a real DB
  column + non-`None` `related_model`, so a virtual relation is never indexed as a decodable FK.
  Tested.
- **Shape-keyed dedup + AR-M6** — identical effective shapes dedupe via `_shape_build_cache`
  (keyed on `(model, operation kind, frozenset(effective names))`); distinct shapes colliding on
  one generated name raise `ConfigurationError` at finalize. Tested end-to-end.
- **AR-H2 carve-out** — `_unprovided_exclude` keeps an unprovided field that co-participates in a
  `UniqueConstraint` / `unique_together` / single-field `unique` with a provided field. Tested
  (name-only update still validates `unique_item_per_category`).

---

*Note: nothing was committed; this review only writes `docs/feedback.md`. The one Major (CR-1) is
the priority — it is reproducible from client input and breaks a contract the code explicitly
claims to honor.*
