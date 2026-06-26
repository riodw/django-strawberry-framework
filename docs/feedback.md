# Spec 039 Review Feedback

Review target: `docs/spec-039-serializer_mutations-0_0_13.md`.

## Findings

### [P1] Relation decoding is specified before write authorization

`docs/spec-039-serializer_mutations-0_0_13.md #"Decision 8 - Resolver pipeline"` and the
Slice 3 checklist put serializer relation-id decoding before write authorization. That regresses
the security invariant established by the form mutation pipeline in
`django_strawberry_framework/forms/resolvers.py::_run_modelform_pipeline_sync #"Authorize BEFORE decoding relations"`.

Relation decoding performs visibility-scoped object lookups. If it runs before write auth, an
unauthorized caller can observe `FieldError` differences for missing, hidden, malformed, or
wrong-type related ids instead of receiving the same authorization failure they would get for any
other denied write. This is especially visible for create mutations, where no instance lookup is
needed before authorization.

Root fix: specify the serializer pipeline as:

- create: authorize against the raw input payload first, then decode relation ids, then validate and
  save through the serializer;
- update: decode only the top-level mutation `id`, locate the target object through the mutation
  visibility rules, authorize against that instance and raw input payload, then decode relation ids,
  validate, and save;
- only delete may stay unsupported for this card.

Add tests where a denied caller submits invalid or hidden relation ids and still receives the
authorization failure, not relation-specific payload errors.

### [P1] Schema-time serializer field discovery assumes no-arg serializers

The spec repeatedly bases generated input construction on `serializer_class().fields`. Real DRF
serializers often require construction context, override `get_fields()`, or derive fields from
tenant/request state. The runtime `get_serializer_kwargs(...)` hook does not solve schema-time input
generation because finalization happens before a request exists.

The existing form design avoided this class of bug by using class-level form metadata instead of
instantiating request-shaped objects. Serializer mutations need an equivalent explicit contract.
Without it, the feature will fail for serializers that are valid DRF code but cannot be no-arg
constructed during schema finalization.

Root fix: add a schema-time hook, for example `get_serializer_for_schema()` or
`get_serializer_fields_for_schema()`, with a stable-shape requirement. The default may instantiate
the serializer with no arguments, but the spec should document that dynamic serializers must
override the schema hook and that request-dependent schema shape is rejected loudly. Add tests for a
serializer whose normal `__init__` requires kwargs and whose schema hook supplies stable fields.

### [P1] Renamed DRF fields are promised but not designed

The problem statement says serializer mutations should support serializers that rename fields, but
the conversion and reverse-map sections are still written mostly as if serializer field names and
model field names are identical. In DRF, a serializer field can use `source="category"`,
`source="category_id"`, a dotted source path, or `source="*"`.

That matters for model-backed conversion and relation handling. For example, a serializer field
`category_pk = PrimaryKeyRelatedField(source="category", queryset=Category.objects.all())` needs a
clear GraphQL input name, a clear relation-id suffix rule, a backing model field lookup based on
`source`, and a reverse map that writes back the serializer field name expected by DRF. If the spec
looks up model fields by serializer field name, renamed scalar and relation fields will either lose
read-side enum/upload/relation parity or silently map the wrong field.

Root fix: define the supported `source` scope. A defensible first card could support only omitted
source and simple one-segment source values, while rejecting dotted source and `source="*"` for
model-column conversion unless a custom serializer-only mapping is used. For supported renamed
fields, resolve the backing Django model field from `serializer_field.source`, derive GraphQL names
from the serializer field name by a documented rule, and preserve the serializer field name in the
reverse map passed to DRF. Add renamed scalar and renamed FK tests.

### [P1] DRF error flattening is underspecified for supported field shapes

The spec says serializer errors should map to the frozen `FieldError` payload shape, but it only
describes the simple `field -> [messages]` case. DRF validation errors can contain `ErrorDetail`,
lists, dicts, `ReturnDict`, `ReturnList`, indexed child errors from `ListField`, and
`api_settings.NON_FIELD_ERRORS_KEY`. This is not only a nested-serializer concern; the spec itself
supports `ListField`, `MultipleChoiceField`, and `JSONField`.

The current public error type has `field: str`, so the spec must define a deterministic path
encoding. Otherwise implementers can accidentally stringify nested structures, drop child errors, or
raise while building the payload.

Root fix: specify a recursive error flattener with a path convention such as `items.0.name` or
`items[0].name`, normalize DRF's non-field key to the package's existing non-field sentinel, and
preserve all leaf messages as strings. Add tests for list child errors, nested dict-shaped errors,
and non-field serializer errors.

### [P2] Serializer input ledgers must clear before every finalization bind

The spec adds a `registry.clear()` co-clear row for serializer input namespace state, but that is
not enough. `django_strawberry_framework/types/finalizer.py::finalize_django_types #"clear_mutation_input_namespace()"`
already clears mutation and form generated-input ledgers immediately before binding so a failed
finalization can be retried deterministically in the same process.

Serializer-generated inputs will have the same retry-idempotence problem. If a later type fails
after serializer inputs have been materialized, `registry.clear()` may never run before the next
`finalize_django_types()` attempt.

Root fix: add a `clear_serializer_input_namespace()` function and call it from the same pre-bind
reset block as mutation and form inputs, as well as from `TypeRegistry.clear()`. Add a retry test
where serializer input materialization succeeds, a later type fails finalization, the missing type is
registered, and a second finalization succeeds without stale serializer input attributes.

### [P2] The soft DRF import contract needs an exact root-export design

The spec requires `import django_strawberry_framework` to work without DRF installed, while importing
`SerializerMutation` raises an actionable `ImportError`. The current package root uses eager imports
and an explicit `__all__`, so this cannot be treated as a small import-line addition in
`django_strawberry_framework/__init__.py #"__all__ = ("`.

Root fix: specify the exact import behavior for:

- `import django_strawberry_framework`;
- `from django_strawberry_framework import SerializerMutation`;
- `import django_strawberry_framework.rest_framework`;
- `from django_strawberry_framework import *`.

The implementation likely needs a root-level `__getattr__` or a deliberately lazy compatibility
module, plus one shared `require_drf()` helper that owns the install message. The absent-DRF tests
should isolate module caches for both `django_strawberry_framework.rest_framework*` and
`rest_framework*`; otherwise an earlier import in the test process can mask the missing-dependency
path.

### [P2] The dependency plan contradicts the lockfile policy

Slice 5 says to add `djangorestframework` to `[dependency-groups].dev`, but the definition of done
says `uv.lock` is unchanged. This repository has a committed `uv.lock`, and changing dev
dependencies without updating the lockfile leaves the declared environment and locked environment
out of sync.

Root fix: either allow the lockfile update in this card, or do not change `pyproject.toml` and make
the DRF test dependency come from some already-locked source. The clean version is to update
`pyproject.toml` and `uv.lock` together while still leaving package version files unchanged.

### [P3] Smaller specification gaps

- `Meta.optional_fields` adopts the graphene-django-rest-framework concept but does not decide
  whether the `"__all__"` sentinel is supported. Support it with tests or reject it with a clear
  configuration error.
- The serializer `Meta` allowed-key text says to add `serializer_class` and `optional_fields` while
  dropping form/model input keys, but it should explicitly keep `permission_classes` if serializer
  mutations inherit the same auth hook as `DjangoMutation`.
- Runtime serializer context should either reuse the package's request extraction helper or document
  the exact fallback behavior when `info.context` is already the request object rather than an
  object with a `.request` attribute.

## Non-Issues

The deliberate divergences from graphene-django-rest-framework look correct: keeping a single
operation per mutation class, requiring Relay-style `id` for update, using the registered
`DjangoType` as the payload shape, rejecting plain `serializers.Serializer`, and refusing the
`serializers.Field -> String` catch-all all fit this package's DRF-first, typed-GraphQL direction.
