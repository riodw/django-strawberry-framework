# Review - `django_strawberry_framework/types/` diff for spec-031

## Findings

### P2 - `functools.partial` can still hide an async callable strategy

The updated `django_strawberry_framework/types/base.py::_validate_globalid_callable` now checks both `inspect.iscoroutinefunction(value)` and `inspect.iscoroutinefunction(value.__call__)`, which fixes plain `async def` functions and callable instances with `async def __call__`. It still misses a realistic wrapper shape: `functools.partial` around an async callable instance.

Example:

```python
import functools


class Encoder:
    async def __call__(self, type_cls, model, root, info):
        return "custom.label"


strategy = functools.partial(Encoder())
```

For that `strategy`, `inspect.iscoroutinefunction(strategy)` is `False`, `inspect.iscoroutinefunction(strategy.__call__)` is also `False`, and `inspect.signature(strategy).bind(type_cls, model, root, info)` succeeds. The value therefore passes validation, but invoking it in `types/relay.py::encode_typename` returns a coroutine object, triggering the non-string guard at request time and leaking an unawaited-coroutine warning. That is the same failure class the validator is meant to move to build time.

Update the async detection to unwrap `functools.partial` before checking coroutine-ness, or add a small recursive helper that follows `.func` for partials and then checks both the function and `__call__`. Add coverage for `functools.partial(AsyncCallable())` on at least the shared validator path so both `Meta.globalid_strategy` and `RELAY_GLOBALID_STRATEGY` inherit the fix.
