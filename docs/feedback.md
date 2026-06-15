# spec-034 Permissions - Deeper Implementation Review

Assumption for this pass: the findings from `docs/feedback2.md` are treated as
already fixed. I am not repeating version-boundary, test-placement, multi-DB
assertion, no-op gate-test, or stale-doc issues here unless they expose a deeper
remaining behavior problem.

No `pytest` run was performed; `AGENTS.md` says not to run pytest unless
explicitly asked. I did run source review and a rollback-only local probe for the
highest-severity runtime path.

## Findings

### H1 - Permission-user branches can return rows whose selected non-null FK target errors

The current product hooks make per-model view permissions bypass cascade on that
model. For example,
`examples/fakeshop/apps/products/schema.py::EntryType.get_queryset #"products.view_entry"`
returns `queryset.filter(is_private=False)` for a `view_entry` user, and
`examples/fakeshop/apps/products/schema.py::ItemType.get_queryset #"products.view_item"`
does the same for `view_item`. That means a root `Entry` can be visible because
the entry itself is non-private while its non-null `item` target is still hidden
by `ItemType`'s own target visibility when the query selects `item { ... }`.

This is not just the previous docs/test wording drift. It is a runtime GraphQL
failure on a valid selection. The optimizer correctly downgrades the hidden
target relation to a `Prefetch` because the target type has a custom hook, and
the child queryset applies that target hook. Then
`django_strawberry_framework/types/resolvers.py::_make_relation_resolver #"return getattr(root, field_name)"`
reads the forward FK. Because the filtered prefetch did not populate the related
object for a non-null FK, Django raises the model descriptor's
`RelatedObjectDoesNotExist`. A rollback probe over a `view_entry` user produced
the GraphQL error `Entry has no item.` at `allEntries.edges.0.node.item`.

The high-quality fix is to make the non-staff product branches preserve
relation-visible row coherence, not to catch the resolver error and return
`None`. These FK fields are non-null in the Django model and GraphQL type, so
returning `None` only changes the failure shape. For `ItemType`, `PropertyType`,
and `EntryType`, the per-model permission branch should apply the cascade after
the model's own private-row filter:

```python
return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

`CategoryType` has no cascadable forward edge, so the same shape is a no-op
there but keeps the policy uniform. After that production fix, update the live
HTTP coverage that currently documents the failure as orthogonal:
`examples/fakeshop/test_query/test_products_api.py::test_cascade_view_item_user_matrix #"A surviving entry's item can sit under a hidden category"`.
The replacement coverage should assert permission users through real fakeshop
requests, including `view_entry` selecting `item { name category { name } }` and
`view_item` selecting `category { name }`, with hidden-target rows dropped rather
than returned as resolver errors.

### M1 - The async cascade recourse text points consumers at a path that still cannot await targets

The implementation is internally consistent that cascade is a sync walk wrapped
by `sync_to_async`:
`django_strawberry_framework/permissions.py::aapply_cascade_permissions #"async-hooked edge"`
still raises `SyncMisuseError` for an async target hook. That matches
`docs/spec-034-permissions-0_0_10.md::Decision 10 #"raises SyncMisuseError from both variants"`.

The public error guidance is not equally clear.
`django_strawberry_framework/permissions.py::apply_cascade_permissions #"aapply_cascade_permissions or rewrite the hook sync"`
says to use `aapply_cascade_permissions`, but the async twin still calls the
same sync helper.
`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync #"The Relay node defaults only await async"`
also emits Relay-specific guidance even when the caller is cascade, where no
async branch awaits target hooks.

This matters because a consumer following the message can move from
`apply_cascade_permissions` to `aapply_cascade_permissions` and hit the same
exception again. The root fix is to make the shared sync-misuse message
surface-aware, or to use cascade-specific wrapping text at the call site. For
cascade, the valid recourses in `0.0.10` are: make the target hook sync, or
scope `fields=` so the async-hooked edge is not walked. `aapply_cascade_permissions`
only keeps blocking sync work off the event loop; it does not provide an
async-native per-edge walk.

### M2 - Malformed `fields=` values can escape as raw `TypeError`

`django_strawberry_framework/permissions.py::_validate_fields #"requested = set(fields)"`
correctly rejects a bare string and raises `ConfigurationError` for unknown or
non-cascadable names, but malformed non-string values still fall through the raw
`set(fields)` conversion. Examples include a non-iterable such as `fields=1` and
an iterable with unhashable entries such as `fields=[["item"]]`.

This is a public security-facing helper, and the spec's error posture is loud,
typed configuration failure:
`docs/spec-034-permissions-0_0_10.md::Error shapes #"fields= naming an unknown"`.
A raw `TypeError` is harder for consumers to catch consistently and does not name
the expected field-name iterable contract.

The fix is to normalize `fields` inside a small `try` block and rethrow
`ConfigurationError` for any invalid shape. It should also validate that every
entry is a string before computing `unknown`, so values like `fields=[1]` do not
produce a confusing sorted-name error. Keep the existing contracts intact:
`fields=None` means all cascadable edges, `fields=[]` means no edges, and a bare
string gets the dedicated "wrap it in a list" message.

## Notes

The core cascade walk remains coherent: one `_is_cascadable_edge` predicate,
registry primary lookup, `has_custom_get_queryset()` skip, nullable-FK-preserving
`Q(__in) | Q(__isnull)` shape, alias pinning through `queryset.db`, and a single
sync-misuse utility. The highest-risk issue is now above that layer: the example
permission policy lets root visibility and nested non-null relation visibility
disagree, which turns ordinary relation selections into runtime errors.
