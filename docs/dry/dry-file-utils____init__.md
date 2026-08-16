# DRY review: `django_strawberry_framework/utils/__init__.py`

Status: verified

## System trace

The target is the `utils/` package facade. It owns two contracts only:

1. A human-oriented package map in the module docstring (`Includes, among others:`) that
   orients readers to sibling substrates without claiming to be an export inventory.
2. A curated light-import `__all__` that re-exports seven names from three leaf owners —
   `relations` (`RelationKind`, `relation_kind`, `is_many_side_relation_kind`), `strings`
   (`snake_case`, `pascal_case`), and `typing` (`unwrap_graphql_type`, `unwrap_return_type`).

It does not own any helper implementation. Sibling modules keep their own public surfaces;
production call sites almost exclusively import those leaves by dotted path
(`from ..utils.relations import ...`, `from ..utils.strings import ...`,
`from ..utils.typing import ...`). The facade is exercised mainly as an identity pin in
`tests/utils/test_relations.py::test_utils_init_reexports_match_submodule` and as a short
import path for `unwrap_graphql_type` in `tests/utils/test_typing.py`.

Connected surfaces examined: package-root `__init__.py` (no overlap with the curated seven);
`types/__init__.py` (consumes the same leaf helpers but does not re-export them);
`utils/{relations,strings,typing}.py` (true owners); the remaining `utils/` siblings named in
the docstring map (`connections`, `sessions`, `inputs`/`permissions`, `input_values`,
`querysets`); and the on-disk modules absent from both the curated `__all__` and the plan file
list (`context.py`, `sessions.py`) — recorded only as folder-pass inventory evidence, not
expanded into sibling reviews.

Item-scoped baseline `65d699db7e9192a70f8d33d19756bc50ec11693e` diff for the target is empty.

## Verification

- Inventory: on-disk `utils/*.py` has 15 siblings + this facade. Curated `__all__` is the seven
  names above. Docstring ``symbols`` name many more (module labels plus leaf APIs such as
  `session_store_class`, `iter_active_fields`, `SyncMisuseError`, `is_async_callable`) under the
  explicit `among others` hedge — a package map, not a second `__all__`.
- Package-root `__all__` overlap with the curated seven: empty. An interpreter probe confirmed
  `hasattr(django_strawberry_framework, name)` is false for every curated name; star-import from
  `django_strawberry_framework.utils` binds exactly `__all__`; each curated name is identical to
  its leaf-module object.
- `SyncMisuseError` is defined in `utils/querysets.py` and already converges on one object via
  package root, `types`, and `permissions` re-exports. It is named in the docstring map under
  `querysets` and deliberately absent from this facade's `__all__`.
- Production importers of the curated concepts use dotted leaf paths; the facade is not a second
  implementation site.
- No pytest run (deferred per cycle policy). Permanent tests already pin facade/leaf identity for
  the relation trio.

Strongest rejected candidates:

- Widen `__all__` to match the docstring inventory (or add `is_async_callable`,
  `schema_config_from_info`, `SyncMisuseError`, `session_store_class`, …). The docstring is a
  navigational map; expanding the facade would eagerly couple light imports to heavy substrates
  (`querysets`, `permissions`, `connections`) and multiply supported public import paths for
  symbols that already have a leaf owner (and, for `SyncMisuseError`, existing consumer-facing
  re-exports). Export policy here is intentional curation, not incomplete mirroring.
- Delete the facade / shrink `__all__` to empty so every consumer must use dotted paths. The
  seven names are a stable convenience surface with an identity-pinning test; removing it is
  API churn without removing duplicated responsibility (there is none — only aliases).
- Lift the curated names to package root (or re-export them from `types/__init__.py`). Root and
  `types` facades already state distinct consumer contracts; root overlap is currently zero by
  design. Adding root aliases would duplicate export surfaces without a new owner of behavior.
- Treat docstring-vs-TREE / docstring-vs-disk incompleteness (`context`, `converters`, `errors`,
  `imports`, `write_*` absent from the bullets) as a consolidation. `Includes, among others`
  already admits partial coverage; TREE one-liners are generated from each sibling module
  docstring. Thinning or expanding the map is documentation taste for the folder pass, not an
  export-policy DRY fix at this facade.

## Opportunities

None — the facade aliases seven leaf symbols once; implementations live only in
`relations` / `strings` / `typing`. Apparent “missing” exports are intentional dotted-path
ownership, not duplicated policy.

## Judgment

Proved zero-edit. Curated `__all__` and the docstring package map are complementary contracts,
not competing inventories. No consolidation is warranted at this facade; sibling implementation
reviews and the later `utils/` folder pass own any leaf-level or inventory-gap questions
(`sessions.py` and `context.py` are on disk but absent from the plan file list — evidence for
that folder pass only).

## Implementation (Worker 1)

No tracked production or test edits. Item-scoped diff vs
`65d699db7e9192a70f8d33d19756bc50ec11693e` for
`django_strawberry_framework/utils/__init__.py` is empty; this artifact is the only new path for
the item. Deferred pytest: none required for a zero-edit facade result; existing
`test_utils_init_reexports_match_submodule` remains the standing identity pin. Changelog: no.
Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced the facade as export policy only (no helper bodies). Item-scoped
`git diff 65d699db7e9192a70f8d33d19756bc50ec11693e -- django_strawberry_framework/utils/__init__.py`
is empty. Interpreter probe: package-root `hasattr` is false for all seven curated
names; `from django_strawberry_framework.utils import *` binds exactly `__all__`;
each curated name is identical to its leaf-module object.

Production importers of the curated concepts use dotted leaves
(`..utils.relations` / `..utils.strings` / `..utils.typing`) across connection,
optimizer, types, mutations, filters, orders, forms, rest_framework, and
management. Facade imports appear only in tests (`test_relations` identity pin;
`test_typing` short path for `unwrap_graphql_type`). `types/__init__.py` documents
leaf consumption and re-exports only `DjangoType` / `SyncMisuseError` /
`finalize_django_types` — no overlap with the curated seven.

Rejected candidates challenged and upheld:

- Widen `__all__` (incl. light typing extras named in the docstring map such as
  `is_async_callable` / `schema_config_from_info`): those symbols already have a
  single leaf owner; production already imports them by dotted path. Adding them
  multiplies supported import paths without removing a second implementation.
  Docstring `Includes, among others` plus leaf API examples is a navigational map,
  not a competing export inventory. `SyncMisuseError` already converges via
  `utils/querysets.py` → `types.relay` / package root / `permissions` re-exports
  and is correctly absent from this facade.
- Delete facade / empty `__all__`: aliases are not duplicated responsibility; the
  standing identity pin and public convenience surface would be API churn only.
- Lift curated names to package root or `types/`: root overlap is currently zero by
  design; those facades state distinct consumer contracts.
- Docstring-vs-disk map gaps (`context`, `converters`, …): documentation taste for
  the folder pass under the existing `among others` hedge, not export-policy DRY.

Missed-consolidation search: no second implementation of the curated seven; no
competing package-root / `types` re-export set; `sessions.py` and `context.py` exist
on disk and are absent from `dry-0_0_13.md` utils file list — correctly deferred to
the `utils/` folder pass. No revision required.
