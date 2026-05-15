# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## DRY analysis

- Existing patterns reused: `install_is_type_of()` is installed during `DjangoType.__init_subclass__` in `django_strawberry_framework/types/base.py:76-139`; `apply_interfaces()`, `implements_relay_node()`, `_check_composite_pk_for_relay_node()`, and `install_relay_node_resolvers()` are sequenced by finalization Phase 2.5 in `django_strawberry_framework/types/finalizer.py:96-110`; the resolver paths reuse Django's default manager through `_initial_queryset()` in `django_strawberry_framework/types/relay.py:257-264` and the shared visibility hook through `_apply_get_queryset_sync()` / `_apply_get_queryset_async()` in `django_strawberry_framework/types/relay.py:192-230`.
- New helpers a fix might justify: a single `node_ids` coercion helper for Relay bulk lookup would serve `_apply_node_filter()`, `_resolve_nodes_default()`, and `_resolve_nodes_async()` by materializing any iterable once and converting `relay.GlobalID` values in one place.
- Duplication risk in the current file: Relay ID coercion is repeated in `django_strawberry_framework/types/relay.py:248-253`, `django_strawberry_framework/types/relay.py:399`, and `django_strawberry_framework/types/relay.py:423`; that duplication already creates an iterable-consumption bug in the plural resolver paths.

## High:

None.

## Medium:

### One-shot `node_ids` iterables are consumed before result ordering

`_resolve_nodes_default()` and `_resolve_nodes_async()` pass `node_ids` into `_apply_node_filter()`, which iterates it to build `coerced_ids`, and then iterate the same `node_ids` object again to build `coerced_keys` for order-preserving output. That works for lists, but a generator or other one-shot iterable is exhausted by the filter step, so the resolver can return an empty ordered list even though the queryset was filtered with the requested ids. The fix should materialize/coerce `node_ids` exactly once before both the filter and ordering steps use it, preferably through a shared helper that also removes the repeated `relay.GlobalID` coercion. Add a focused regression test with a generator-shaped `node_ids` input.

```django_strawberry_framework/types/relay.py:248:253
    if node_ids is not None:
        coerced_ids = [(nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids]
        return qs.filter(**{f"{id_attr}__in": coerced_ids})
```

```django_strawberry_framework/types/relay.py:392:400
    id_attr = cls.resolve_id_attr()
    if in_async_context():
        return _resolve_nodes_async(cls, id_attr, node_ids, info=info, required=required)
    qs = _apply_get_queryset_sync(cls, _initial_queryset(cls), info)
    qs = _apply_node_filter(qs, id_attr, node_ids=node_ids)
    if node_ids is None:
        return qs
    coerced_keys = [str(nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids]
    return _order_nodes(cls, list(qs), coerced_keys, id_attr, required=required)
```

```django_strawberry_framework/types/relay.py:419:425
    qs = await _apply_get_queryset_async(cls, _initial_queryset(cls), info)
    qs = _apply_node_filter(qs, id_attr, node_ids=node_ids)
    if node_ids is None:
        return qs
    coerced_keys = [str(nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids]
    results = [obj async for obj in qs]
    return _order_nodes(cls, results, coerced_keys, id_attr, required=required)
```

## Low:

None.

## What looks solid

- The mandatory static helper was run for this types file: `python scripts/review_inspect.py django_strawberry_framework/types/relay.py --output-dir docs/review/shadow --stdout`.
- Interface injection, composite-primary-key gating, and resolver installation are kept in focused helpers and are called from one finalizer phase.
- Sync and async `get_queryset` handling is split clearly, with the sync path rejecting coroutine results instead of letting them fail later as queryset operations.
- The resolver installation table centralizes the four Relay method names, and consumer overrides are preserved through the `__func__` identity check.
- Existing tests cover Relay interface validation, id suppression, resolver injection, custom `get_queryset`, sync/async node lookup, custom resolver preservation, and direct `relay.Node` inheritance.

### Summary

`types/relay.py` is generally well factored and heavily covered. The only confirmed defect I found is in the plural Relay lookup path: bulk `node_ids` are coerced in multiple places, and that duplicate iteration breaks one-shot iterables. Consolidating that coercion should fix the bug and improve the file's DRY shape at the same time.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/relay.py` — added shared Relay node-id coercion helpers; plural
  `resolve_nodes` paths now materialize/coerce `node_ids` once and reuse that list for both filtering and
  order-preserving output.
- `tests/types/test_relay_interfaces.py` — added a generator-shaped `node_ids` regression test using
  `relay.GlobalID` values.
- `docs/review/rev-types__relay.md` — recorded Worker 2 fix report and disposition notes.
- `docs/review/worker-memory/worker-2.md` — appended Worker 2 implementation memory.

### Tests added or updated

- `tests/types/test_relay_interfaces.py::test_resolve_nodes_accepts_generator_node_ids` — pins that a
  one-shot iterable of `relay.GlobalID` ids is filtered and ordered correctly instead of being exhausted
  after the filter step.

### Validation run

- `uv run ruff format django_strawberry_framework/types/relay.py tests/types/test_relay_interfaces.py` —
  pass; reformatted `tests/types/test_relay_interfaces.py`.
- `uv run ruff check --fix django_strawberry_framework/types/relay.py tests/types/test_relay_interfaces.py`
  — pass.
- `uv run pytest tests/types/test_relay_interfaces.py -k 'resolve_nodes' --no-cov` — pass; 11 passed,
  51 deselected.

### Notes for Worker 3

- DRY disposition: `_coerce_node_id()` now centralizes singular `relay.GlobalID` coercion, and
  `_coerce_node_ids()` is the single materialization/coercion point for plural ids. `_apply_node_filter()`
  still owns the ORM filter shape, but plural callers pass the already-materialized list so generators are
  consumed once.
- Comment/docstring disposition: narrow private-helper docstring cleanup was included because
  `_apply_node_filter()` no longer owns plural `GlobalID` coercion; no broader comment/docstring pass was
  needed.
- Changelog disposition: changelog-worthy because this fixes consumer-visible Relay bulk lookup behavior
  for one-shot iterables, but `CHANGELOG.md` edits were not authorized in this Worker 2 scope, so no
  changelog edit was made.
- Shadow helper disposition: no `docs/review/shadow/` Relay overview file was present to re-read during
  implementation, and no new shadow helper output was generated.

---

## Verification (Worker 3)

### Logic verification outcome

Accepted. `_resolve_nodes_default()` and `_resolve_nodes_async()` now call `_coerce_node_ids()` once before
filtering, pass the materialized list into `_apply_node_filter()`, and derive `coerced_keys` from that same
list for order preservation. One-shot iterables therefore feed both the ORM `__in` filter and `_order_nodes()`
without a second iteration. The single-id path remains intact through `_coerce_node_id()` inside
`_apply_node_filter(node_id=...)`.

### DRY findings disposition

Accepted. The repeated `relay.GlobalID` coercion was consolidated into `_coerce_node_id()` for singular ids
and `_coerce_node_ids()` for plural ids. `_apply_node_filter()` still owns only the ORM filter shape, which
keeps the plural materialization responsibility in the resolver assembly paths where ordering also needs the
same values.

### Temp test verification

- No temp tests were needed. Permanent coverage was added in
  `tests/types/test_relay_interfaces.py::test_resolve_nodes_accepts_generator_node_ids` and passed in the
  scoped validation run.

### Verification outcome

Accepted. Worker 2's fix report covers logic, DRY disposition, comment/docstring disposition, changelog
disposition, and validation notes. `CHANGELOG.md` remains untouched because this Worker 2/3 cycle did not
authorize changelog edits.

Validation run:

- `uv run pytest tests/types/test_relay_interfaces.py -k 'resolve_nodes' --no-cov` — pass; 11 passed,
  51 deselected.
- `uv run ruff format --check django_strawberry_framework/types/relay.py tests/types/test_relay_interfaces.py`
  — pass; 2 files already formatted.
- `uv run ruff check django_strawberry_framework/types/relay.py tests/types/test_relay_interfaces.py` — pass.
