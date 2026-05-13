# Review: docs/diff-spec-relay_interfaces.diff
Status: revision-needed

## DRY analysis

- Existing patterns reused: `DjangoType.__init_subclass__` remains the collection point and now threads normalized interfaces into `DjangoTypeDefinition` (`django_strawberry_framework/types/base.py:73-132`); the existing finalizer registry loops are extended with Phase 2.5 instead of adding a second finalization entry point (`django_strawberry_framework/types/finalizer.py:83-106`); the reserved `DjangoTypeDefinition.interfaces` slot is used rather than adding parallel state (`django_strawberry_framework/types/definition.py:13-43`); registry-isolation fixtures and the library schema reload fixture are reused for package and HTTP coverage (`tests/types/test_relay_interfaces.py:25-39`, `examples/fakeshop/test_query/test_library_api.py:18-40`); scalar projection continues through the existing optimizer walker path (`django_strawberry_framework/optimizer/walker.py:122-134`).
- New helpers a fix might justify: one helper with the single responsibility “run `DjangoType.get_queryset` and return a concrete `QuerySet` in the current sync/async resolver context.” It would serve `_resolve_node_default` and `_resolve_nodes_default`; the async path should await an awaitable `get_queryset` result before applying `.filter(...)`, while the sync path should either bridge deliberately or raise a clear `ConfigurationError` if an async hook is used from sync execution.
- Duplication risk in the current file: Relay resolver method names are centralized in `_RELAY_RESOLVER_DEFAULTS`, so no issue there. The current duplication risk is stale shipped-slice TODO anchors that now repeat old 0.0.5 work in multiple places (`django_strawberry_framework/types/__init__.py:19-20`, `django_strawberry_framework/optimizer/walker.py:130-132`, `tests/optimizer/test_walker.py:35-37`) and can drift from the actual shipped state.

## High:

### Async `get_queryset` is not awaited in Relay node defaults

Decision 9 says the node resolvers must support async resolver contexts and notes that a consumer `DjangoType.get_queryset` may itself be sync or async. The implementation switches to async ORM execution with `in_async_context()`, but `_assemble_node_queryset` calls `cls.get_queryset(qs, info)` synchronously before that branch. If a consumer defines `async def get_queryset`, `qs` becomes a coroutine and the next `.filter(...)` call fails. I verified this with a minimal async `CategoryNode.get_queryset`, which produced `AttributeError: 'coroutine' object has no attribute 'filter'` plus an unawaited-coroutine warning.

Recommended change: split queryset assembly into sync and async helpers, or make `_assemble_node_queryset` await-aware. In async resolver context, await the result of `cls.get_queryset(qs, info)` when it is awaitable before filtering/executing. Add tests for async `get_queryset` with both `resolve_node` and `resolve_nodes`. In sync resolver context, decide explicitly whether an async `get_queryset` is bridged with `async_to_sync` or rejected with `ConfigurationError`.

```django_strawberry_framework/types/relay.py:198:207
model = cls.__django_strawberry_definition__.model
qs = model._default_manager.all()
qs = cls.get_queryset(qs, info)
if node_id is not None:
    coerced = node_id.node_id if isinstance(node_id, relay.GlobalID) else node_id
    qs = qs.filter(**{id_attr: coerced})
elif node_ids is not None:
    coerced_ids = [(nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids]
    qs = qs.filter(**{f"{id_attr}__in": coerced_ids})
return qs
```

```django_strawberry_framework/types/relay.py:270:314
id_attr = cls.resolve_id_attr()
qs = _assemble_node_queryset(cls, info, id_attr, node_id=node_id)
if in_async_context():
    return qs.aget() if required else qs.afirst()
return qs.get() if required else qs.first()

...

qs = _assemble_node_queryset(cls, info, id_attr, node_ids=node_ids_list)
if in_async_context():

    async def _materialize() -> list:
        results = [obj async for obj in qs]
        return _order_nodes(cls, results, coerced_keys, id_attr, required=required)

    return _materialize()
return _order_nodes(cls, list(qs), coerced_keys, id_attr, required=required)
```

## Medium:

### `DONE-011` is still under the Kanban “In progress” column

The spec checklist says to move the Relay card to Done. The snapshot says no slice is active, but the detailed board still has `DONE-011` under `## In progress`, which keeps the board structurally inconsistent.

Recommended change: move the whole `DONE-011` card above the `## In progress` heading into the Done column, or rename/remove the `## In progress` heading so it no longer contains a completed card.

```KANBAN.md:326:332
## In progress

### DONE-011 — 0.0.5 Relay interfaces and Node foundation

Priority: completed Relay Node foundation

Status: complete.
```

## Low:

### Shipped 0.0.5 TODO anchors remain in source and tests

Project rules say spec TODO anchors for a future slice should be removed in the same change that ships the slice. Relay support has shipped, but source/test comments still carry `TODO(0.0.5 relay interfaces...)` anchors. These no longer represent future work: the public-surface decision is implemented, and the optimizer coverage now lives in `tests/optimizer/test_relay_id_projection.py`.

Recommended change: delete these TODO blocks or convert any still-useful statement into a non-TODO explanatory comment.

```django_strawberry_framework/types/__init__.py:19:20
# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# keep ``types.relay`` internal; do not re-export Relay helper functions.
```

```django_strawberry_framework/optimizer/walker.py:130:132
# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# selecting Relay ``id`` on a Relay-declared DjangoType must still
# project the concrete pk attname so ``resolve_id`` can read the
```

```tests/optimizer/test_walker.py:35:37
# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# extend optimizer coverage for Relay id projection, no avoidable lazy loads,
# unchanged relation planning across Relay targets, and loaded-pk resolve_id.
```

### Unrelated `.gitignore` hunk is in the review diff

The Relay spec does not call for packaging-ignore changes, but the review diff starts with a `.gitignore` hunk removing `/build/`. The working tree currently shows this as a change from `/build/` to `build/`; either way it is unrelated to Relay interfaces and should not ride along unless there is a separate packaging reason.

Recommended change: revert the `.gitignore` hunk from this slice, or document the packaging rationale separately.

```docs/diff-spec-relay_interfaces.diff:1:10
diff --git a/.gitignore b/.gitignore
index bed0eb9..fb04949 100644
--- a/.gitignore
+++ b/.gitignore
@@ -17,7 +17,6 @@ __pycache__/

 # Distribution / packaging
 .Python
-/build/
```

## What looks solid

- `Meta.interfaces` is promoted, validated, normalized, stored on `DjangoTypeDefinition`, and covered by package tests.
- Interface base injection happens before `strawberry.type(...)`, and direct `relay.Node` inheritance is also handled by MRO checks.
- Relay `id` suppression keeps the primary key in `field_map`, and optimizer projection tests cover Relay `id`, lazy-load avoidance, and relation planning across Relay targets.
- Resolver signatures match Strawberry’s positional/keyword call shapes, and consumer overrides for `resolve_id_attr`, `resolve_id`, `resolve_node`, and `resolve_nodes` are preserved.
- The example library HTTP test exercises a real `GenreType` with `interfaces = (relay.Node,)` and validates GlobalID round-trip behavior.
- Version bumps and public-export discipline are in place: `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock` agree on `0.0.5`, and `__all__` did not widen.
- Validation commands: the full `uv run pytest` gate passed with `520 passed, 1 skipped` and `100.00%` package coverage; `uv run ruff format --check . && uv run ruff check .` also passed. The targeted Relay/schema/HTTP subset itself passed (`102 passed`) but exits nonzero under the global coverage threshold when run alone, which is expected for a subset.

### Summary

Most of the Relay interfaces checklist is implemented and covered. The remaining revision blocker is async `get_queryset` support in the Relay node defaults, because the current implementation supports async ORM execution only after a synchronous `get_queryset` call. The remaining Medium/Low items are documentation/cleanup issues around Kanban placement, shipped-slice TODO anchors, and an unrelated `.gitignore` hunk.