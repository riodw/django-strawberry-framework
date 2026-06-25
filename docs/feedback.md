# Focused review — GOAL / cookbook / spec-038 alignment
Scope: focused review of the spec-038 form-mutation implementation against `GOAL.md` and the released cookbook reference at `/Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py`.

## Verdict
Spec-038 is aligned with `GOAL.md` and does not conflict with the cookbook-reference direction.

The cookbook schema is primarily the read-side north star: `AdvancedDjangoObjectType`, nested `class Meta`, sidecars, connection fields, `get_queryset`, and cascade visibility. Spec-038 is write-side work, so it does not directly recreate that schema file, but it fits the same framework philosophy: declarative `class Meta`, generated inputs, shared permission/visibility seams, and no Strawberry decorator-first consumer API.

## Strong alignment
- `DjangoModelFormMutation` and `DjangoFormMutation` are declared through nested `Meta.form_class`, matching the DRF / Graphene-Django mental model described in `GOAL.md`.
- `DjangoModelFormMutation` rides the existing `DjangoMutation` foundation instead of creating a parallel write system:
  - same `DjangoMutationField`
  - same generated payload lifecycle
  - same `FieldError` envelope
  - same `DjangoModelPermission` default
  - same primary `DjangoType` lookup
  - same optimizer re-fetch path
- Form-derived inputs come from `form_class.base_fields`, which matches the goal of “nothing hand-rolled that the package can generate.”
- Relation form fields are handled in the right architectural place:
  - `categoryId` / relation input is reverse-mapped back to the form field name
  - relation targets are visibility-checked through the related `DjangoType.get_queryset`
  - raw-pk and Relay `GlobalID` branches are both covered
  - `to_field_name` is respected before binding the Django form
- File uploads align with the goal’s criterion 6: form `FileField` / `ImageField` routes to `Upload` and is passed through `files=`, not `data=`.
- The fakeshop examples test this through real `/graphql/` requests, which is the right proof level for this project.

## Cookbook-schema alignment
The reference cookbook schema’s important shape is:

- one node type per model
- `class Meta`
- sidecar classes named in `Meta`
- `get_queryset` visibility
- `apply_cascade_permissions`
- root fields exposed through the package field factory

The current fakeshop product schema follows that same shape for the shipped read-side features, and spec-038 adds mutations without weakening it. It does not introduce a competing consumer style.

This is the right direction: the write-side API now feels like the same package as the read-side API.

## Focused actionable issue
### Low — Example schemas hand-roll allow-all permission classes
`examples/fakeshop/apps/products/schema.py` defines `AllowAny`, and `examples/fakeshop/apps/library/schema.py` defines `_AllowAnyWrite`.

That works, but it slightly fights `GOAL.md`’s “nothing is hand-rolled that the package can generate” principle. The framework already treats explicit `permission_classes = []` as the allow-any opt-out, and `DjangoModelPermission` docs describe that posture.

Action:

- In example schemas, prefer `permission_classes = []` when the example’s intent is simply “public write.”
- Keep custom permission-class examples only where the test is specifically proving custom permission behavior.
- Alternatively, if the named style is preferred, add a public package-level `AllowAny` permission class and use that consistently.

This is not a blocker, but it would make the examples closer to the goal: short, declarative, and free of local boilerplate.

## Non-blockers / things not to change
- The plain `DjangoFormMutation` payload being `{ ok, errors }` is correct. It is model-less, so returning no `node` is the right split.
- Rejecting `Meta.operation` on plain forms is correct. It keeps the model-less form separate from model operations.
- Deny-by-default for plain forms is correct. A plain form has no model for `DjangoModelPermission`, so the safe default must be closed.
- Not adopting Graphene’s `return_field_name` is correct. The shared `node` / `result` / `errors` contract is more consistent with this package.

## Bottom line
No high-severity alignment problems found.

Spec-038 supports `GOAL.md` criterion 6 and preserves the cookbook-style architecture: declarative `Meta`, generated schema machinery, visibility-aware writes, and a shared error envelope. The only cleanup recommendation is the allow-any example boilerplate so the examples teach the shortest framework-native surface.
