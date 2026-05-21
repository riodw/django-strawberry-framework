# Review feedback - package Python diff from `6adbe630287c3ce890384a573634db4513dd8eab`

Scope: generated stripped diffs with `scripts/review_diff_from_commit.py 6adbe630287c3ce890384a573634db4513dd8eab`, then reviewed only `.py` changes under `django_strawberry_framework/`. The package files in scope were `django_strawberry_framework/list_field.py` and `django_strawberry_framework/types/base.py`; the generated example-app diff was intentionally ignored.

## High

### `DjangoListField` accepts unregistered subclasses through inherited framework metadata

Location: `django_strawberry_framework/list_field.py:75`.

The registered-target guard uses `hasattr(target_type, "__django_strawberry_definition__")`. `hasattr` walks the MRO, so a subclass of a concrete `DjangoType` that omits its own `Meta` inherits the parent's `__django_strawberry_definition__` and passes validation even though that subclass was never registered as its own framework type.

Concrete failure shape:

- `class CategoryType(DjangoType): class Meta: model = Category`
- `class ChildCategoryType(CategoryType): pass`
- `DjangoListField(ChildCategoryType)` passes the constructor guard because the parent definition is visible through inheritance.

That leaves the field bound to a target whose definition, selected fields, optimizer metadata, `Meta.primary` state, and model all belong to the parent class. Depending on when schema construction/finalization happens, the failure can surface as a confusing Strawberry type error, or worse, as a field that queries and applies hooks through the wrong definition.

Recommendation: make target registration an own-class invariant instead of an inherited-attribute check. For example, read `target_type.__dict__.get("__django_strawberry_definition__")` and reject when it is missing or when `definition.origin is not target_type`. Add a regression test that defines a concrete `DjangoType`, subclasses it without `Meta`, and asserts `DjangoListField(Subclass)` raises the same registered-target `ConfigurationError`.

### Awaitable-returning callable resolvers can bypass `get_queryset`

Location: `django_strawberry_framework/list_field.py:107-125`.

The consumer resolver branch decides sync vs async once with `inspect.iscoroutinefunction(user_resolver)`. The constructor accepts any callable, but not every callable that returns an awaitable is itself detected by `inspect.iscoroutinefunction`; callable instances with `async __call__` are the clearest public shape. Those resolvers land in the sync `_wrap` branch, where `user_resolver(root, info)` returns a coroutine. `_post_process_consumer_sync` sees a coroutine, not a `Manager` or `QuerySet`, and returns it unchanged.

Under async schema execution, Strawberry may still await that coroutine, so the field can appear to work, but any awaited `Manager` / `QuerySet` result has already skipped `_post_process_consumer_async` and therefore skipped `target_type.get_queryset(...)`. That violates the visibility-hook contract for queryset-shaped consumer resolver returns.

Recommendation: do not rely solely on `inspect.iscoroutinefunction(user_resolver)` for a public `Callable` API. Either normalize async-callable objects at construction time, or add a runtime awaitable branch that awaits the result before post-processing on async execution paths and raises a targeted `ConfigurationError` on sync execution paths. Add coverage with a callable object whose `async __call__` returns a `QuerySet` and whose target type filters rows in `get_queryset`; the filtered rows should be absent from the GraphQL result.

## Notes

I did not find a blocking issue in the `django_strawberry_framework/types/base.py` change. The new direct `cls.__annotations__["id"]` read is consistent with the existing call-site precondition and the tests already cover the accepted direct and string `relay.NodeID[...]` forms plus the rejected lookalikes.
