# DRY review: `django_strawberry_framework/utils/typing.py`

Status: verified

## System trace

`utils/typing.py` owns three cross-cutting contracts used by optimizer, field
factories, mutations, and GlobalID validation:

| Symbol | Rule | Primary consumers |
| --- | --- | --- |
| `unwrap_graphql_type` | Peel all `of_type` layers (graphql-core / Strawberry), Power-of-Ten capped | `optimizer/extension.py` schema walk + return-type → model |
| `unwrap_container_type` | Peel `StrawberryContainer` only (leaf with incidental `of_type` stays) | `connection.py::_window_edge_class` |
| `unwrap_return_type` | Peel **one** list / Strawberry-list layer | `mutations/sets.py::_annotation_core_is_global_id` |
| `is_async_callable` | Partial/staticmethod/`__call__`-aware coroutine predicate | `list_field.py`, `connection.py`, `types/base.py::_validate_globalid_callable` |
| `is_async_generator_callable` | Same unwrap, async-**generator** predicate | `list_field.py`, `connection.py` (was duplicated; now owned here) |
| `strawberry_schema_from_schema` / `_from_info` | Private `_strawberry_schema` dig | `optimizer/extension.py` |
| `schema_config_from_info` | Plan-time wrapped config, then bare `schema.config` | walker name converter, nested planner `relay_max_results`, `utils/connections.py::resolve_relay_max_results` |

Public re-exports from `utils/__init__.py`: only `unwrap_graphql_type` /
`unwrap_return_type`. Async predicates and schema digs are imported from
`utils.typing` directly.

Item-scoped baseline `006231fe…` for `utils/typing.py` at review start: empty
(199 lines unchanged vs baseline before this item's edits).

## Verification

Searches: all imports of `utils.typing`; package-wide `_strawberry_schema`,
`of_type` loops, `iscoroutinefunction` / `isasyncgenfunction`,
`unwrap_*` call sites.

Scratch (`uv run python`): compared connection-style vs list-field-style
async-gen predicates on `agen`, `partial(agen)`, async-gen instance, and
`partial(instance)`:

| Shape | connection-local | list-field / shared |
| --- | --- | --- |
| `async def` + `yield` | True | True |
| `partial(async_gen_fn)` | True (`inspect` unwraps) | True |
| async-gen callable instance | True (`__call__`) | True |
| `partial(async-gen instance)` | **False** | **True** |

**Rejected — fold `unwrap_graphql_type` / `unwrap_container_type` /
`unwrap_return_type` into one helper.** Distinct contracts: full `hasattr`
peel vs `isinstance(StrawberryContainer)` gate (Edge leaf with incidental
`of_type` must not descend) vs one-layer list/annotation peel. A mode flag
would obscure ownership; call sites need different stop conditions.

**Rejected — replace resource_policy NonNull `while isinstance(...,
GraphQLNonNull): .of_type` with `unwrap_graphql_type`.** Those loops must stop
at `GraphQLList` to classify collections; full peel would erase the list layer.
`get_named_type` is used when the named leaf is what they want.

**Rejected — migrate `mutations/sets.py::_strawberry_field_shape` onto typing
unwraps.** It counts `StrawberryList` depth while ignoring optionals and uses
identity-seen cycle detection; unwrap helpers return a leaf or one layer, not
`(depth, core)`.

**Rejected — `inspect_django_type` `of_type` recursion.** Structural GraphQL
string rendering that preserves Optional/List shape, not leaf peel.

**Rejected — middleware / views `asgiref`/`csrf_protect` `iscoroutinefunction`.**
Django middleware ASGI capability marking and CSRF decorator await branching;
not field-factory / GlobalID async-callable detection.

**Rejected — merge `strawberry_schema_from_schema` with `_from_info`.**
Different fallbacks: identity when already unwrapped (test fixtures) vs `None`
when any step missing (resolver path). `schema_config_from_info` already
composes on the info dig.

**Rejected — merge `is_async_callable` with `is_async_generator_callable`.**
GraphQL list/connection completion accepts `AsyncIterable`; the coroutine
predicate must stay False for `async def` + `yield` so dispatch routes
correctly. Kept as siblings sharing `_callable_inspection_target`.

## Opportunities

### 1. Own `is_async_generator_callable` beside `is_async_callable`

- **Repeated responsibility:** Partial/staticmethod/`__call__`-aware
  async-generator detection for field-factory sync/async dispatch.
- **Sites:** `list_field.py::_is_async_generator_callable` (full unwrap) and
  `connection.py::_is_async_generator_callable` (thinner; missed
  `partial(async-gen instance)`).
- **Evidence:** Same consumers as `is_async_callable`; executable comparison
  proved the connection gap; list_field already had
  `test_djangolistfield_partial_async_generator_resolver_is_bounded`.
- **Owner:** `utils/typing.py` (async-callable inspection owner).
- **Consolidation:** Add `_callable_inspection_target` + public
  `is_async_generator_callable`; delete both locals; import at call sites.
- **Proof:** `tests/utils/test_typing.py` parametrized wrapper matrix;
  `tests/test_connection.py::test_connection_partial_async_generator_resolver_raises_sync_misuse`;
  existing list_field partial async-gen test.
- **Risks / non-goals:** Do not teach `is_async_callable` to claim async gens;
  do not change Django middleware `iscoroutinefunction` usage.

## Judgment

Unwrap helpers and `_strawberry_schema` digs were already single-sited. The one
warranted consolidation was the async-generator sibling of `is_async_callable`:
two field factories had drifted predicates, and connection's thinner form was a
real miss on `partial(async-gen instance)`.

## Implementation (Worker 1)

- Owner: `django_strawberry_framework/utils/typing.py`
  (`_callable_inspection_target`, `is_async_generator_callable`;
  `is_async_callable` refactored onto the shared unwrap).
- Migrated: `list_field.py`, `connection.py` (deleted local helpers);
  `utils/__init__.py` docstring mention.
- Tests: `tests/utils/test_typing.py` matrix;
  `tests/test_connection.py` partial async-gen SyncMisuse pin.
- Behavior kept separate: coroutine vs async-generator predicates;
  three unwrap helpers; schema digs; resource_policy / mutation shape /
  middleware async checks.
- Validation: `uv run ruff format .` and `uv run ruff check --fix .` (pass).
- Changelog: not edited (no maintainer authorization).

Item-scoped diff vs `006231fe47e5264b22f2426e4c9f0b5805d7d22a` touches:
`utils/typing.py`, `utils/__init__.py`, `list_field.py`, `connection.py`,
`tests/utils/test_typing.py`, `tests/test_connection.py`, and this artifact.

Deferred pytest: `tests/utils/test_typing.py`,
`tests/test_list_field.py` (partial async-gen),
`tests/test_connection.py` (sync + partial async-gen SyncMisuse). Ready for
Worker 2.

## Independent verification (Worker 2)

Re-traced `utils/typing.py` ownership and both former async-gen call sites
without relying on Worker 1's private reasoning. Confirmed:

- **Consolidation holds.** Package-wide search: no leftover
  `_is_async_generator_callable`; only production call sites are
  `list_field.py` and `connection.py`, both importing the shared owner.
  `_callable_inspection_target` is the single unwrap for both predicates.
- **Behavioral gap was real.** Scratch comparison of the old connection-local
  predicate vs shared: `partial(async-gen instance)` is False under
  connection-local / True under shared; coroutine vs async-gen predicates
  partition (shared True ⇒ `is_async_callable` False). Matches the claimed
  drift and the new connection SyncMisuse pin.
- **Rejected candidates hold (source).**
  - Three unwrap helpers: different stop conditions (`hasattr` full peel /
    `StrawberryContainer` gate / one-layer list); call sites need each.
  - `resource_policy` NonNull `while` loops: must stop before `GraphQLList`
    to classify collections (`_collection_rows` / `_is_connection_type`).
  - `mutations/sets._strawberry_field_shape`: returns `(depth, core)` with
    identity-seen cycle detection — not a leaf/one-layer unwrap.
  - `inspect_django_type` `of_type` recursion: GraphQL string rendering that
    preserves Optional/List shape.
  - Middleware/views `iscoroutinefunction`: ASGI capability marking /
    `csrf_protect` await branching — not field-factory async-callable
    detection.
  - Schema digs already single-sited (`getattr(..., "_strawberry_schema", …)`
    only in `typing.py`); distinct fallbacks for schema vs info paths.
  - Merging the two async predicates would break dispatch ordering
    (async-gen branch before coroutine branch).
- **Missed consolidations:** none found. No other `isasyncgenfunction` /
  raw `_strawberry_schema` getattr / parallel unwrap loops with the same
  contract.
- **Scope clean** vs `006231fe…`: only typing owner, both field factories,
  `utils/__init__.py` docstring, typing matrix + connection pin, artifact.
  No unrelated absorption.
- **Proof credibility:** permanent tests present; pytest deferred per cycle
  (not run by Worker 2).

Outcome: verified. Plan checkbox marked.
