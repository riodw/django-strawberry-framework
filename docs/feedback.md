Spec-039 full review against fakeshop live-test rules
=====================================================

Review scope: current `HEAD` (`1f7e5d70`) after the latest serializer-input naming
fixes, checked against `examples/fakeshop/test_query/README.md`. I reviewed the
implementation diff from `7511949c..HEAD`, the new package tests, and the fakeshop
live-test requirements.

Overall assessment: the latest commit fixes the two issues from the previous
feedback in the common path: hook-varied relation targets no longer collide on the
same input name, and subclass validation no longer reads an inherited parent
`_mutation_meta`. There are still two blockers. One is an implementation bug in
the new canonical-name gate; the other is a test-placement violation of the
fakeshop live-query README.

Findings
--------

### High: schema-hook overrides can still be rejected by the default serializer shape

The new canonical-name guard re-walks the serializer's default full shape so the
canonical `<Serializer>Input` name is reserved for the default descriptor:

- `django_strawberry_framework/rest_framework/inputs.py::_default_full_shape_identity`
- `django_strawberry_framework/rest_framework/inputs.py::build_serializer_input_class`

That helper catches `ConfigurationError` from
`resolve_effective_serializer_fields(serializer_class)`, but it does not catch
`ConfigurationError` raised while converting the default fields in
`_walk_serializer_fields`. This breaks a valid use of the public
`get_serializer_for_schema()` hook: a consumer can supply a stable, supported
schema field map while the serializer's default no-arg field map is unsupported or
intentionally different.

I verified this with a local probe:

```python
class BadDefaultSer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="name", queryset=Category.objects.all())

    class Meta:
        model = Item
        fields = ("name", "category")

class CreateItem(SerializerMutation):
    class Meta:
        serializer_class = BadDefaultSer
        operation = "create"

    @classmethod
    def get_serializer_for_schema(cls):
        return {
            "name": bound(serializers.CharField(), "name"),
            "category": bound(
                serializers.PrimaryKeyRelatedField(queryset=Category.objects.all()),
                "category",
            ),
        }
```

`finalize_django_types()` still fails by converting the default `SlugRelatedField`,
even though the hook-returned schema field is a supported `PrimaryKeyRelatedField`.
The error is:

```text
ConfigurationError Serializer relation field 'category' is a SlugRelatedField; only PrimaryKeyRelatedField is supported
```

Required correction: `_default_full_shape_identity` should treat any
`ConfigurationError` from default identity construction as "no usable default
full shape" and return `None`, not reject a hook-provided shape. That includes
errors from `resolve_effective_serializer_fields`, `_walk_serializer_fields`,
relation-primary lookup, unsupported field conversion, dotted-source rejection,
and collision checks if they are added to the default identity path.

Add a regression test where the default no-arg serializer field map contains an
unsupported field, the hook returns a supported replacement map, and finalization
succeeds with a descriptor-derived input name.

### High: the latest fixes do not comply with `examples/fakeshop/test_query/README.md`

The README's coverage rule is explicit: any `django_strawberry_framework/` line
that can be earned by a real fakeshop `/graphql/` request must be tested in
`examples/fakeshop/test_query/` first, with package-internal tests only for
genuinely unreachable paths.

The latest commit changes consumer-visible schema behavior in:

- `django_strawberry_framework/rest_framework/inputs.py::_shape_token`
- `django_strawberry_framework/rest_framework/inputs.py::_default_full_shape_identity`
- `django_strawberry_framework/rest_framework/inputs.py::build_serializer_input_class`
- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_for_schema`

But it adds tests only under `tests/rest_framework/`:

- `tests/rest_framework/test_inputs.py::test_descriptor_name_distinguishes_relation_target_model`
- `tests/rest_framework/test_sets.py::test_hook_varied_relation_targets_bind_to_distinct_input_names`
- `tests/rest_framework/test_sets.py::test_subclass_redefining_serializer_validates_against_child_serializer`

These paths are not inherently unreachable from fakeshop live HTTP tests. The
fakeshop schema reload fixture in `examples/fakeshop/test_query/README.md`
already rebuilds the full project schema before live API tests; adding fakeshop
serializer mutations that use the schema hook and then issuing real `/graphql/`
mutations would exercise the same bind/materialization/name paths through the
consumer-visible stack. This is exactly the kind of package behavior the README
says belongs in `examples/fakeshop/test_query/`.

There is also a quality issue with the current package-only hook-varied test:
`tests/rest_framework/test_sets.py::test_hook_varied_relation_targets_bind_to_distinct_input_names`
proves finalization, but not that the generated input can execute through the
runtime serializer. A live fakeshop test would force the schema-time hook and
`get_serializer_kwargs`/runtime serializer construction to agree.

Required correction: add live fakeshop coverage in
`examples/fakeshop/test_query/test_products_api.py` for at least one schema-hook
serializer mutation that executes over HTTP. The test surface should use the real
project schema and `django.test.Client` `/graphql/` request path, not direct
`finalize_django_types()` package setup. Keep the package tests for genuinely
internal edge cases if useful, but do not rely on them as the only coverage for
consumer-visible hook naming and subclass validation behavior.

Resolved items verified
-----------------------

- Hook-varied relation target descriptors now fold `related_model` into the
  descriptor-derived name token.
- The canonical name is no longer granted to every hook-returned "full" shape in
  the common path.
- `SerializerMutation.get_serializer_for_schema()` now reads only the class's own
  `_mutation_meta`, avoiding inherited parent snapshots during child validation.
- The new tests cover the two previously reported edge cases at package level.

Validation notes
----------------

I ran targeted local `uv run python` probes to verify the remaining schema-hook
failure. I did not run pytest because the repository instructions say not to run
pytest unless explicitly asked.
