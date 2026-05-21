# Review feedback — fixes for prior `feedback.md` Highs

Scope: reviewed the `.py` changes in `f2aba83` (HEAD) vs `c6888ad` — specifically the `django_strawberry_framework/list_field.py` fixes for the two High findings in the prior `feedback.md`, plus the regression tests in `tests/test_list_field.py`. The example-app schema and earlier `types/base.py` deltas were intentionally out of scope.

## Resolved

### High #1: own-class registration check

`list_field.py:101-107` replaces the inherited-attribute `hasattr` check with `getattr(target_type, "__django_strawberry_definition__", None)` plus `getattr(definition, "origin", None) is not target_type`. `DjangoTypeDefinition.origin` is assigned exactly once at `types/base.py:229` (`origin=cls`) inside `DjangoType.__init_subclass__`, so `origin is target_type` is the correct own-class invariant. The new guard rejects both the abstract-base case (where `definition is None`) and the bare-subclass case (where the inherited `definition.origin` is the parent class). The updated error string names the inheritance failure shape explicitly. Regression pinned at `tests/test_list_field.py:126-150` (`test_djangolistfield_rejects_djangotype_subclass_without_own_meta` constructs `ChildCategoryType(ParentCategoryType): pass` and asserts the `ConfigurationError`).

### High #2: async-callable detection

`list_field.py:47-63` introduces `_is_async_callable(fn)`; the consumer-resolver dispatch at `list_field.py:133` now routes through it. The helper checks both `inspect.iscoroutinefunction(fn)` and `inspect.iscoroutinefunction(fn.__call__)`, covering callable instances whose `__call__` is `async def`. The docstring is explicit that `functools.partial(async_fn, ...)` is deliberately undetected per rev5 H1 YAGNI — the gap is documented, not silent. Regression pinned at `tests/test_list_field.py:551-595` (`test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied` uses an instance with `async def __call__`, defines a filtering `get_queryset`, and asserts the filter still applies).

## Notes

No blocking issues in either fix. Two small observations, neither blocking:

### Stale comment block above the registration guard

`list_field.py:79-85` still describes the OLD discriminator:

```
# ``__django_strawberry_definition__`` is
# assigned at ``types/base.py:245`` only for concrete ``DjangoType``
# subclasses with a ``Meta`` carrying ``model``; ``hasattr(...)`` is a
# sufficient discriminator for "registered concrete ``DjangoType``".
```

The line anchor is stale (`:245` → `:251`) and the "`hasattr(...)` is a sufficient discriminator" claim is exactly what High #1 disproved. The newer comment block at `list_field.py:94-100` carries the correct rationale; the older block should either be deleted or rewritten so the file does not document two contradictory discriminators in adjacent paragraphs.

### `functools.partial(async_fn, ...)` gap matches the High #2 failure shape

`_is_async_callable`'s docstring honestly flags this gap and points at rev5 H1 YAGNI. The gap is real: a `partial`-wrapped async resolver lands in the sync wrapper, `user_resolver(root, info)` returns a coroutine, `_post_process_consumer_sync` sees neither a `Manager` nor a `QuerySet` and passes the coroutine through; under async execution Strawberry awaits the result and the awaited `QuerySet` silently skips `target_type.get_queryset(...)` — the same shape High #2 closed for `async __call__`. Two reasonable dispositions: keep the YAGNI posture and let the next real-consumer report drive the fix, OR add a two-line unwrap (`if hasattr(fn, "func") and inspect.iscoroutinefunction(fn.func): return True`) and a parallel regression test. The current state is internally consistent — flagging only because the rationale is "no one has needed it yet" rather than "it can't fail."
