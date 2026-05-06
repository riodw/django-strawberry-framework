# Review: `django_strawberry_framework/types/resolvers.py`

## High:

None.

## Medium:

### Third copy of `logging.getLogger("django_strawberry_framework")` literal

`_resolver_logger = logging.getLogger("django_strawberry_framework")` is the same string-literal logger that the optimizer folder pass just consolidated for `extension.py` and `walker.py`. The fix is the same shape: import `logger` from `optimizer/__init__.py` (where it now lives as the framework-wide singleton). This avoids a third literal that would drift on a package rename.

```django_strawberry_framework/types/resolvers.py:32:32
_resolver_logger = logging.getLogger("django_strawberry_framework")
```

## Low:

### `_check_n1` reads `info.context` three times per call

`_check_n1` calls `_get_context_value(getattr(info, "context", None), ...)` three times for `dst_optimizer_planned`, `dst_optimizer_strictness`, plus the surrounding `getattr(info, "context", None)`. The cost is small per call but multiplied across every relation field on every row. A single `context = getattr(info, "context", None)` at the top, reused for the rest, would tighten the hot path and read less cleanly only by one line. Defer to a future perf-pass.

```django_strawberry_framework/types/resolvers.py:96:109
planned = _get_context_value(getattr(info, "context", None), "dst_optimizer_planned")
if planned is None:
    return
key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
if key in planned:
    return
if not _will_lazy_load(root, field_name):
    return
strictness = _get_context_value(getattr(info, "context", None), "dst_optimizer_strictness", "off")
```

### Closure captures `field` rather than `field.attname` in the forward resolver

`forward_resolver` reads `field.attname` on every call. Since `field.attname` is set at class-creation time and does not change, hoisting it to a local outside the closure (`attname = field.attname`) and capturing the local would save one attribute lookup per resolver call. Negligible but consistent with `field_name = field.name` already at line 132.

```django_strawberry_framework/types/resolvers.py:156:160
def forward_resolver(root: Any, info: Info) -> Any:
    if field.attname is not None and _is_fk_id_elided(info, field_name, parent_type):
        return _build_fk_id_stub(root, field)
    _check_n1(info, root, field_name, parent_type)
    return getattr(root, field_name)
```

### `_will_lazy_load` relies on Django private attributes

`_will_lazy_load` checks `root.__dict__` (forward FK / OneToOne caching location) and `root._prefetched_objects_cache` (many-side cache). Both are documented Django internals but not part of the public ORM contract. If Django renames these, the strictness check breaks silently. The function docstring already acknowledges the caches; keep an eye on the upstream Django code if the strictness path becomes load-bearing.

```django_strawberry_framework/types/resolvers.py:69:84
def _will_lazy_load(root: Any, field_name: str) -> bool:
    """Return ``True`` if accessing ``field_name`` on ``root`` would trigger a query.
    ...
```

## What looks solid

- File-level docstring pins the responsibility split and the dependency direction: `base` imports from `resolvers`, never the reverse — exactly the structure that lets `_attach_relation_resolvers` accept a pre-computed field list rather than re-running `_select_fields(meta)` here.
- Cardinality dispatch in `_make_relation_resolver` covers every Django relation shape (forward FK, forward OneToOne, reverse OneToOne with `DoesNotExist` swallow, reverse FK / M2M list materialization) and the docstring documents each branch.
- B2 FK-id elision: `forward_resolver` short-circuits to `_build_fk_id_stub` when the optimizer marked the resolver key as elided, returning a target-model instance keyed only on the FK id. The stub correctly sets `_state.adding=False` and `_state.db` via `router.db_for_read` so the result behaves like a fetched row, not a freshly-constructed one.
- B3 strictness: `_check_n1` reads the planned-set sentinel from `info.context`, returns early when no sentinel is present (so the resolver is a no-op outside strictness mode), and only warns/raises when both unplanned *and* would-actually-lazy-load.
- The reverse OneToOne resolver captures `field.related_model.DoesNotExist` at closure-creation time so the `try/except` does not pay an MRO walk per call.
- `__name__` is set on every generated resolver (`f"resolve_{field_name}"`), which makes Strawberry-generated tracebacks readable.
- `_attach_relation_resolvers` uses `setattr(cls, field.name, strawberry.field(resolver=resolver))`, matching the consumer-facing override surface so a future spec can re-attach without disrupting existing tests.
- 18% line coverage in this file's own tests; full coverage via integration tests across the suite.

---

### Summary:

The resolver module is small, well-bounded, and gets all five Django relation shapes right with explicit cardinality dispatch and a documented dependency direction relative to `types.base`. The single Medium item is the third hand-rolled `logging.getLogger("django_strawberry_framework")` literal — drop it and import from the optimizer subpackage's framework-wide logger. Low items are minor hot-path tightening (single `context` read, `attname` hoist) and a private-API reliance note for `_will_lazy_load`.

---

### Worker 3 verification

- Medium fix: `import logging` removed; `_resolver_logger` is now imported as `from ..optimizer import logger as _resolver_logger`. The third literal is gone; the framework-wide logger now has a single source of truth in `optimizer/__init__.py`.
- Low items: not addressed. The two hot-path micro-optimizations (single context read, `attname` local hoist) and the `_will_lazy_load` private-API note are all monitor-only follow-ups; no consumer-visible benefit large enough to act on this cycle.
- Validation: `uv run ruff format` and `uv run ruff check` clean; `uv run pytest -q` -> 353 passed, 4 skipped, 100% coverage.
- CHANGELOG: not updated. Internal refactor; no consumer-visible change.
- Scope: changes confined to `django_strawberry_framework/types/resolvers.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
