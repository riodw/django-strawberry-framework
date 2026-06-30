# Spec-039 implementation review — deeper pass

Date: 2026-06-29.

Scope: current `HEAD` (`19740bac`) after the newest fakeshop live-test additions. I
reviewed the inherited review in this file, the full [spec-039][spec-039], the live-test
lane rule in [test_query README][test-query-readme], the `rest_framework/` implementation,
and the new `library` serializer mutation surface/tests.

Method: static review plus two targeted `uv run python` probes. I did **not** run pytest,
per the repo instruction not to run it unless explicitly asked.

Bottom line: the newest commit fixed the previous live-placement gaps for unsupported
default-field recovery and hidden-branch serializer relation visibility. It also moved the
same-serializer hook-collision proof into the real fakeshop schema. One production
correctness bug remains: `allow_null`-only schema-hook variation still dedupes to the wrong
input shape. There are also two test/spec fidelity gaps worth fixing before merge.

## Findings

### High: `allow_null` is still missing from serializer input shape identity

The prior review's nullability finding is still valid.

Evidence:

- `django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields
  #"annotation_reprs.append(repr(annotation))"` records the base annotation before the
  nullable widening.
- The actual emitted GraphQL annotation is widened later at
  `django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields
  #"annotation = annotation | None"`.
- `django_strawberry_framework/rest_framework/inputs.py::SerializerInputShape` stores only
  `annotations` plus `required_state`; neither carries the post-widening nullable shape.
- `django_strawberry_framework/rest_framework/inputs.py::_shape_token` uses that same base
  annotation string, so generated names miss the same axis.

I verified the behavior with a direct probe using the same serializer class and two
schema-time field maps that differ only by `CharField(required=True, allow_null=False)` vs
`CharField(required=True, allow_null=True)`:

```text
BaseInput BaseInput
True ("<class 'str'>",) ("<class 'str'>",) (True,) (True,)
<class 'str'> str | None
```

So the two emitted input classes have different actual annotations (`str` vs `str | None`),
but their `SerializerInputShape` descriptors compare equal and both claim `BaseInput`.
Through `SerializerMutation.build_input`, the first built class would be returned from the
descriptor cache for the second declaration, silently giving one mutation the other's
GraphQL nullability and default behavior. That is exactly the "wrong nullability" case the
spec says the descriptor identity must prevent.

Required fix: make the descriptor and name token use the emitted annotation identity, not
the base annotation identity. The cleanest implementation is to append `repr(annotation)`
after nullable widening in `_walk_serializer_fields`, then let `_default_full_shape_identity`,
`SerializerInputShape.annotations`, and `_shape_token` all consume that post-widening value.
Add a regression that finalizes two mutations over the same serializer whose hooks return
same-name `required=True` fields differing only in `allow_null`, and assert distinct input
classes/names.

### Medium: the live same-serializer collision test proves naming, but not the differentiating relation decode

The new fakeshop collision surface is in the correct lane, but it currently proves less
than its prose says.

Evidence:

- `examples/fakeshop/apps/library/serializers.py::CollisionShelfSerializer` declares only
  `code` and `branch`.
- `examples/fakeshop/apps/library/serializers.py::shelf_collision_schema_field_map` adds a
  synthetic `target` relation on a throwaway serializer class.
- `examples/fakeshop/test_query/test_library_api.py::test_serializer_hook_same_serializer_different_targets_distinct_inputs_over_http`
  introspects the two generated input names and confirms both expose `targetId`, but both
  mutation writes omit `targetId`.

I also checked DRF behavior directly: `CollisionShelfSerializer(data={"code": ..., "branch":
..., "target": ...})` validates successfully and drops `target` from `validated_data`.
That means the live test's differentiating field is not actually owned by the runtime
serializer, and because the test omits it, the serializer relation decoder never has to use
the recorded `InputFieldSpec.related_model` for the field that made the two shapes differ.

Impact: the test would still pass if the divergent field were introspected correctly but
runtime decode for the `target` relation were broken, keyed to the wrong related model, or
never reached. This is not a production bug by itself, but it leaves the hardest part of
the same-serializer relation-target axis under-proven in the live lane.

Recommended correction: make the collision fixture a real runtime field, not schema-only.
For example, use one DRY serializer class/mixin that accepts `target_model` in its
constructor, builds a write-only `target = PrimaryKeyRelatedField(queryset=target_model...)`
in `get_fields()`, and pops or records `target` in `validate()`/`create()`. Then the two
mutations should override both `get_serializer_for_schema()` and `get_serializer_kwargs()`
with `Patron` vs `Loan`, post `targetId` in both live mutations, and include one wrong-model
or missing-target assertion. That would prove descriptor naming, bind-stashed
`related_model`, relation decode, and runtime serializer agreement in one fakeshop path.

### Medium: `allow_blank=True` is still not tested, despite the spec saying it is pinned

`rg "allow_blank|allowBlank" tests examples/fakeshop django_strawberry_framework` now finds
only documentation in
`django_strawberry_framework/rest_framework/serializer_converter.py::convert_serializer_field`;
there is no test.

The spec explicitly says the M2 test plan pins `allow_blank=True` as "not reflected in the
SDL, enforced by the serializer." The current suite covers `required=True, allow_null=True`
and DRF defaults, but not this third axis.

Required correction: add a test. Because this is a consumer-visible SDL/runtime behavior,
the best fit under [test_query README][test-query-readme] is a small fakeshop live mutation:
introspect that an `allow_blank=True` `CharField` is still a non-null `String` when required,
then post an empty string and prove the serializer accepts it. A package-level
`build_serializer_inputs()` test is still useful as a narrow unit backstop, but it should not
be the only proof if the behavior is reachable over `/graphql/`.

### Medium: `SerializerMutation.build_input` still bypasses the promoted `cached_build_input` helper

The code preserves the guard-before-cache ordering, but it does not comply with the DRY
obligation the spec calls out.

Evidence:

- `django_strawberry_framework/mutations/sets.py::cached_build_input` is the promoted helper
  that owns "run guard, then cache lookup."
- `django_strawberry_framework/forms/sets.py` calls that helper.
- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.build_input`
  reimplements the cache lookup inline inside `_build` instead.

I do not see a current correctness failure: `build_and_stash_input()` calls `_build()` for
every declaration, so the create-required guard still runs per declaration before the local
cache lookup. The issue is architectural drift. P1.7 says this procedure is shared, and the
serializer path is now a third spelling of the exact sequencing the helper was created to
single-site.

Recommended correction: either adapt `cached_build_input` to support the serializer's
descriptor-after-build key cleanly, or add a short source comment plus a spec note explaining
why the descriptor-keyed serializer cache cannot use the helper without building twice. Do
not leave the current code claiming P1.7 while bypassing the P1.7 helper.

### Low: generated divergent-name tokens use a short probabilistic digest while documenting an injective token

`django_strawberry_framework/rest_framework/inputs.py::_shape_token` appends only six hex
characters of SHA-1 for each field discriminant. The docstring says the token is injective
and the spec promises distinct deterministic names for distinct descriptors. A six-hex
digest is deterministic, but it is not injective and is small enough that a large consumer
schema or generated hook matrix can hit a collision. The materialization ledger would catch
that as a finalize-time `ConfigurationError`, but it would still reject two otherwise valid
distinct shapes.

Recommended correction: use a longer digest, at least 12 to 16 hex chars. If the contract
must be truly "distinct", add a deterministic collision-resolution suffix at materialization
time rather than relying on any truncated hash.

### Low: field-sequence normalization still has the wrapper the spec says not to add

`django_strawberry_framework/rest_framework/inputs.py::normalize_serializer_field_sequence`
is a thin wrapper over `normalize_field_name_sequence(..., flavor="SerializerMutation")`.
The implementation is harmless, but the spec says the serializer should call the shared
helper directly with no third rebinding wrapper. `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._validate_meta`
even says it routes through the direct helper, which is not what the code does.

Recommended correction: either inline the calls and remove the wrapper, or update the spec
and comments to say the serializer intentionally follows the model/form wrapper precedent.

### Low: read-only exclusion prose and test naming are misleading

`django_strawberry_framework/rest_framework/inputs.py::resolve_effective_serializer_fields`
says excluding a `read_only` field is a no-op because the field was already dropped. The
implementation actually validates `Meta.exclude` against the post-drop writable set, so
explicitly excluding a read-only field raises "unknown or non-writable." The nearby test
`tests/rest_framework/test_inputs.py::test_read_only_exclusion_does_not_trip_guard` does not
pass `exclude=("ro",)`; it only proves the default drop path does not trip the create guard.

This may be an acceptable behavior choice, but the prose and test name should match it.
Either add the explicit exclude test the name implies and decide whether it should raise, or
rename/reword the test and docstring to "read-only fields are dropped before the guard."

## Resolved since the previous review

- `examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_hook_narrowed_serializer_recovers_unsupported_default_field`
  now earns the unsupported-default-field recovery through real `/graphql/`.
- `examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_serializer_hidden_branch_is_relation_field_error`
  and
  `examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_schema_hook_serializer_hidden_branch_is_relation_field_error`
  now earn serializer relation visibility through real `/graphql/`.
- `examples/fakeshop/test_query/test_library_api.py::test_serializer_hook_same_serializer_different_targets_distinct_inputs_over_http`
  now proves the materialization/name collision no longer breaks the composed fakeshop
  schema; it just needs the stronger runtime decode assertion described above.

## Validation notes

I ran two targeted `uv run python` probes:

- one confirmed the `allow_null` descriptor collision (`shape_a == shape_b` while emitted
  annotations differ);
- one confirmed the collision fixture's synthetic `target` input is ignored by
  `CollisionShelfSerializer` at DRF validation time.

I restored the tracked fakeshop SQLite fixture after the DRF probe touched it. I did not run
pytest.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-039]: spec-039-serializer_mutations-0_0_13.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
