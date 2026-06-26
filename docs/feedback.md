# Spec 039 Review Feedback - Pass 2

Review target: `docs/spec-039-serializer_mutations-0_0_13.md`.

The major first-pass issues are now addressed on paper: authorize-before-relation-decode,
schema-time serializer discovery, renamed-field `source`, recursive DRF error flattening,
serializer input ledger clearing, lazy DRF imports, and `uv.lock` handling all have explicit
contracts and tests. The remaining findings below are narrower, but they still affect correctness
or the public API shape.

## Findings

### [P1] Serializer input identity ignores nullability and generated field signatures

`docs/spec-039-serializer_mutations-0_0_13.md #"Reverse map + shape identity + naming"` defines
serializer input identity as `(serializer_class, operation kind, frozenset(effective field names))`.
That is too weak for serializer-derived inputs.

Unlike the model and form generators, two serializer inputs can have the same field-name set but
different GraphQL shapes. The most direct case is `Meta.optional_fields`: it changes create-input
requiredness without changing `effective field names`. The schema-time hook can also return the
same field names with different field classes, `source`, child type, choices, relation kind, or
requiredness. With the current identity, the first declaration can win the shape cache and silently
give a later mutation the wrong nullability, annotation, or reverse map.

Root fix: make serializer input shape identity derive from the generated field specs, not only the
names. At minimum include the normalized `optional_fields` set for create inputs; the stronger
version is a `SerializerInputShape` descriptor keyed by each emitted field's input attr, GraphQL
annotation, required/default state, serializer field name, `source`, and `kind`. Use the same
descriptor for the bind cache, generated-name derivation, and materialization collision checks.

Add tests where two create mutations use the same serializer and effective fields but different
`Meta.optional_fields`, and where two schema hooks produce same-named fields with different
annotations or relation/source specs. The result should be distinct deterministic input names or a
clear `ConfigurationError`, never silent reuse.

### [P1] Create narrowing can drop serializer-required fields and finalize an unwritable mutation

The spec validates `Meta.fields` / `Meta.exclude` against the serializer field set, but it does not
guard the create path against narrowing away a field that `serializer.is_valid()` will still require.
That creates a schema that finalizes cleanly but can never satisfy the serializer because the client
has no way to provide the omitted required field.

The form flavor already has the precedent:
`django_strawberry_framework/forms/inputs.py::guard_create_required_fields` and
`django_strawberry_framework/forms/sets.py::_cached_build_form_input #"Run the create-required-narrowing guard PER declaration"`.
Serializer mutations need the same class of guard, adapted to DRF fields.

Root fix: for create inputs, fail at bind time when mutation-level `Meta.fields` / `Meta.exclude`
drops a writeable serializer field with `field.required` and no serializer default. `read_only` and
`HiddenField` are already not client inputs; those should not count as dropped client-required
fields. If the intended escape hatch is `get_serializer_kwargs(...)` injecting the missing values,
make that waiver explicit and run it per declaration before any shape-cache lookup, matching the
form guard's cache discipline.

Add tests for excluding a required scalar, excluding a required serializer-only field, excluding a
required relation, and the documented waiver if one is supported.

### [P2] The save wrapper drops the saved instance the serializer pipeline needs

`docs/spec-039-serializer_mutations-0_0_13.md #"Decision 8 - Resolver pipeline"` says to write via
`serializer.save()`, wrap it with the existing `save_or_field_errors`, and then re-fetch the saved
object by pk. The existing helper
`django_strawberry_framework/mutations/resolvers.py::save_or_field_errors` intentionally returns
only `list[FieldError] | None`; it discards the callable's return value.

That is fine for the model and form paths, but the serializer path needs the object returned by
`serializer.save()` or a pinned guarantee that `serializer.instance` is the source of truth after
the wrapped call. Leaving this implicit invites either a double `serializer.save()` call to recover
the object or a re-fetch from a stale / missing instance.

Root fix: specify a value-preserving pattern. Either add a small shared helper that returns
`(result, errors)`, or require the serializer resolver to capture the result in the wrapped closure
and re-fetch by that result's pk:

```python
saved = None

def do_save():
    nonlocal saved
    saved = serializer.save()

errors = save_or_field_errors(do_save)
```

Add a resolver test proving `serializer.save()` is called exactly once and the payload re-fetch uses
the object returned by that call.

### [P2] Id-like renamed relation fields need an explicit suffix rule

The spec now defines renamed relation fields, but the naming rule still implies a double suffix for
common DRF serializer names. It explicitly maps
`category_pk = PrimaryKeyRelatedField(source="category", ...)` to GraphQL `categoryPkId`; the more
common `category_id = PrimaryKeyRelatedField(source="category", ...)` would therefore become
`categoryIdId`.

That may be intentional, but it should not be accidental. DRF users often name write-only related-id
fields with an `_id` suffix already, and this package's existing relation convention exists to make
model field `category` appear as `categoryId`, not to append `Id` forever.

Root fix: define a normalization rule for id-like declared serializer field names. A reasonable rule:
append the relation id suffix only when the declared serializer field name is not already id-like
(`*_id`, `*_pk`, `*Id`, `*Pk`). Then `category` becomes `categoryId`, while `category_id` becomes
`categoryId` and `category_pk` becomes `categoryPk`. If the double suffix is deliberate, state that
explicitly and add tests for `category_id -> categoryIdId` so the API cost is conscious.

### [P3] The DRF-absent test should define root attribute cache behavior

`docs/spec-039-serializer_mutations-0_0_13.md #"Decision 12 - Soft"` requires absent-DRF tests to
evict `rest_framework*` and `django_strawberry_framework.rest_framework*` modules. That is necessary,
but the root lazy export has one more possible cache: `django_strawberry_framework.SerializerMutation`
itself if `__getattr__` chooses to memoize the imported class into module globals.

Root fix: either specify that root `__getattr__` does not cache `SerializerMutation`, or require the
absent-path test to delete the root module attribute / reload the root package before asserting the
missing-dependency branch. This keeps the soft-dependency test from passing only because an earlier
DRF-present import left the root symbol bound.

## Checks

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-039-serializer_mutations-0_0_13.md`
  passed: `OK: 30 terms - all have glossary entries and at least one spec link.`
