# DRY review: folder `django_strawberry_framework/utils/`

Status: verified

## System trace

`utils/` is the package's cross-cutting infrastructure folder (~8930 lines,
16 modules). It is not a pipeline component: each module owns one cycle-safe
substrate that two or more subsystems must share without importing each other.
Present-day inventory (fresh pass; includes two modules absent from the plan
file list):

| Role | Owner | Notes |
| --- | --- | --- |
| Facade | `__init__.py` | Narrow re-exports: relation classifiers + case helpers + type unwrap. Docstring maps major concerns; `among others` hedge. |
| Query source + visibility seal | `querysets.py` (~3285) | `initial_queryset` / `normalize_query_source` / sealed `apply_type_visibility_*` / `SyncMisuseError` / `reject_async_in_sync_context` / field coercion / sync-boundary runner. |
| Write DB discipline | `write_transaction.py` (~957) | Managed-alias ContextVars, `write_pipeline` / `authorization_phase` / pin / lock / conflict / target-state snapshot. |
| Write value decode | `write_values.py` (~250) | Text preflight, choice unwrap, relation-id type-check, visible-relation spine, kind-routed provided-field walk. |
| Write error envelope leaves | `errors.py` (~135) | `field_error` / `relation_field_error` / Django `ValidationError` mapper / dotted-path join. |
| Generated-input construction | `inputs.py` (~1163) | Namespace / shape cache / Meta fields resolve / `iter_provided_input_fields` / strawberry input class builders. |
| Set-input traversal | `input_values.py` (~195) | Dict/dataclass walk, inactive-value rule, `iter_active_fields` classifier. |
| Active-input permission walk + request decode | `permissions.py` (~661) | `request_from_info` / `ChannelsRequestAdapter` / auth-alias resolve / gate fire + related recursion. |
| Connection window contracts | `connections.py` (~734) | Sidecar kwargs, `FetchMode`, window bounds / range plan shared by planner + resolver. |
| Relation taxonomy | `relations.py` (~486) | `relation_kind` / `classify_path` / `path_traverses_to_many` / accessor / composite-pk / forward-M2M. |
| Naming | `strings.py` (~163) | snake / pascal / camel / lookup flatten. |
| Type / async / schema digs | `typing.py` (~232) | Unwrap helpers, async predicates, `_strawberry_schema` / config digs. |
| Optional import family | `imports.py` (~99) | Best-effort / loaded-only / strict / raising optional. |
| Converter MRO skeleton | `converters.py` (~78) | Ordered precheck → MRO → raise (form + serializer). |
| **Session engine + connection actor lease** | **`sessions.py` (~251)** | **Plan-absent.** `session_store_class`; `ConnectionActorState` / `actor_lease` / `actor_transition` / provenance latch. |
| **`info.context` stash dispatch** | **`context.py` (~193)** | **Plan-absent.** `get_context_value` / `stash_on_context` / `clear_context_key`. |

Folder axes for this pass: policy split across utils modules; unclear state
ownership; competing helper layers; inconsistent public flavors; lifecycle
work repeated at several phases — especially involving the two extra modules.

Connected surfaces re-traced as evidence (not remits unless ownership lands
here): `auth/sessions.py` + `auth/mutations.py` (scope session lock OUTER,
actor lease INNER); `consumers.py` (revalidation under lease +
`session_store_class` reload); `optimizer/_context.py` +
`resource_policy.py` (context stash keys); `mutations` / `forms` /
`rest_framework` write riders; filter / order normalizers and permission
gates; `connection.py` / `optimizer/walker.py` window consumers.

Assignment project-wide leftovers (MODULE_PATH literals, multipart
operations/map, wontfix→invalid, mutations `cached_build_input` docstring,
form/serializer relation-annotation twins, registry
`resolved_relation_annotation` docstring, `predicates.py` placement) left for
the project pass.

## Verification

- ITEM_BASELINE `75fdfc9d750490c3363e2dcfbbe51cc3c95193a8`:
  `git diff 75fdfc9d… -- django_strawberry_framework/utils/` empty at pass
  start and after this review. This pass creates only
  `docs/dry/dry-folder-utils.md`. Concurrent dirt outside the item left
  untouched. Plan checkbox not edited (Worker 2).
- Re-read all 16 modules end-to-end (~8930 lines), including first-class
  review of `sessions.py` and `context.py`. Grepped package for
  `session_store_class` / `actor_lease` / `actor_transition` /
  `connection_actor_state` / `scope_session_lock`, `get_context_value` /
  `stash_on_context` / `clear_context_key`, `iter_input_items` /
  `iter_provided_input_fields` / `is_inactive_value`, `request_from_info` /
  `ChannelsRequestAdapter`, `apply_type_visibility_*` / `SyncMisuseError`,
  `field_error` / `relation_field_error` / `conflict_error`,
  `resolve_write_alias` / `authorization_phase` / `pin_write_queryset`, and
  scope-key literals.
- Did not seed findings from prior file DRY artifacts as truth. Used
  present-day source + connected callers. File-pass deferred items treated
  only as leads when they looked folder-level (none overturned ownership).
- Confirmed `session_store_class` is the sole `SESSION_ENGINE` →
  `SessionStore` expression; callers are only `auth/sessions.py` (capability)
  and `consumers.py::_refreshed_actor` (instantiate). Placement in utils is
  load-bearing: importing `auth.sessions` would execute `auth/__init__.py`
  and register the opt-in auth subsystem on the first authenticated
  WebSocket revalidation.
- Confirmed actor-lease state ownership is single-sited in
  `utils/sessions.py` (`ConnectionActorState` under one scope key). Auth
  holds a *different* lock (`auth/sessions.py::_SCOPE_LOCK_KEY`); consumers
  hold a *different* timestamp key (`_REVALIDATED_AT_SCOPE_KEY`). Three keys,
  three owners, one documented lock order at the dual-hold site
  (`_channels_logout`: session lock OUTER, actor lease INNER).
- Confirmed `info.context` dict/object/frozen dispatch lives only in
  `utils/context.py`. Optimizer key vocabulary + clear loop stay in
  `optimizer/_context.py`; resource-policy keys stay in `resource_policy.py`.
  Re-exports from `optimizer/_context` are a historical import path, not a
  second dispatch.
- Confirmed set-input traversal (`input_values`) and write provided-field walk
  (`inputs.iter_provided_input_fields`) remain distinct contracts: configurable
  inactive sentinel over dict/dataclass vs strawberry-definition `UNSET` strip
  over bound write inputs.
- Confirmed `permissions.request_from_info` (fail-loud request decode +
  Channels adapter) does not compete with `context` stash helpers (defensive
  key R/W with silent frozen skip). Different layers of the context stack.
- No production `.py` edit → ruff not required. No pytest (not the gate;
  deferred). Permanent coverage for sessions/context already lives under
  `tests/auth/`, `tests/optimizer/`, resource-policy / consumer suites.

## Opportunities

None — present-day folder already single-sites each shared invariant at a
clear owner; the two plan-absent modules are intentional opt-in / hand-off
seams, not unfinished extractions. Cross-module candidates examined below
were disproved.

## Rejected / deferred

1. **Extract a shared lazy scope get-or-create helper** for
   `connection_actor_state` and `auth/sessions.py::scope_session_lock`.
   Sites share a four-line `scope.get` / create / store pattern with no
   `await` between read and store, but they create *different* values
   (`ConnectionActorState` vs bare `asyncio.Lock`), live on opposite sides of
   the auth opt-in boundary, and must remain independently named security
   contracts. A utils micro-helper would obscure ownership without a third
   site. Same lesson as the types folder's co-located three-line mirror:
   line-count DRY is not clearer ownership. Reject.

2. **Merge `utils/sessions` actor lease into `auth/sessions` (or into
   `consumers`).** Either move re-introduces the opt-in import hazard the
   module docstring exists to prevent, or forces auth to import the transport
   layer. Dual-subject cohabitation (engine resolver + lease) is deliberate:
   both facts must agree across the forbidden import edge. Reject.

3. **Fold `context.py` into `optimizer/_context.py` or
   `permissions.py`.** Two unrelated subsystems (optimizer plan stash +
   resource policy) already share the dispatch; permissions owns fail-loud
   *request* decoding, not defensive key R/W. Centralizing in utils is the
   correct owner. Reject.

4. **Unify `get_context_value` / `stash_on_context` / `clear_context_key`
   behind one mode-flagged accessor.** Within-module intentional mirror with
   distinct exception sets (read catches `KeyError`; write does not treat
   assignment `KeyError` as frozen; delete does). Extraction needs mode flags
   and obscures the read/write/clear symmetry the docstrings pin. Reject
   (types-folder lesson applies inside one module too).

5. **Route `request_from_info` through `get_context_value(..., "request")`.**
   Fail-loud `ConfigurationError` + Channels adapter recognition vs silent
   default / frozen skip. Same word ("context"), different contracts. Reject.

6. **Merge `input_values.is_inactive_value` / `iter_input_items` with
   `inputs.iter_provided_input_fields`.** Filter/order active-input (dict or
   dataclass, family sentinel) vs write-flavor provided-field walk
   (strawberry definition fields, always `strawberry.UNSET`, keeps explicit
   `None`). Unifying would hide the omit-vs-null distinction write flavors
   depend on. Reject.

7. **Treat `permissions` re-export of `iter_input_items` as competing public
   flavor.** Compat import path for existing `from ..utils.permissions import
   iter_input_items` consumers; single body remains in `input_values`. Same
   pattern as optimizer re-exporting context helpers. Reject.

8. **Compete `errors.field_error` with `write_transaction.conflict_error`.**
   Conflict is a one-line specialization (`codes="conflict"`) over the shared
   leaf ctor — composition, not a second envelope. Reject.

9. **Compete `write_transaction` alias pinning with `querysets` visibility
   seal.** Querysets *consumes* `pin_write_queryset` /
   `pipeline_scoped_queryset` when a write pipeline is open; seal ownership
   stays in querysets, alias/lock ownership in write_transaction. Reject.

10. **Expand `__init__.py` docstring / `__all__` to export `sessions` /
    `context`.** Facade deliberately keeps a narrow consumer leaf set;
    sessions/context are infrastructure reached by dotted imports from auth /
    consumers / optimizer / resource_policy. Docstring already uses `among
    others` and documents sessions for the opt-in rationale; omitting
    `context` from the prose map is inventory taste, not duplicated policy.
    Reject as a DRY consolidation (no behavior/ownership change).

11. **Project-pass leftovers** (explicitly out of this item): MODULE_PATH
    literals; multipart `operations`/`map`; wontfix→invalid; mutations
    `cached_build_input` docstring; form/serializer relation-annotation
    twins; registry `resolved_relation_annotation` docstring;
    `predicates.py` placement. Not utils-folder ownership.

## Judgment

`utils/` is already the package's shared-substrate layer with sharp module
boundaries. The two modules missing from the original plan file list are
first-class and correctly placed: `sessions.py` keeps engine resolution and
the connection actor lease off the auth opt-in import path; `context.py`
single-sites `info.context` shape dispatch for optimizer and resource policy.
No folder-level consolidation is warranted. Proved zero-edit.

## Implementation (Worker 1)

Zero-edit. No production, test, or export changes. Item-scoped diff vs
`75fdfc9d750490c3363e2dcfbbe51cc3c95193a8` for
`django_strawberry_framework/utils/` remains empty; only this artifact is
new under `docs/dry/`. Ready for Worker 2.

## Independent verification (Worker 2)

**Outcome: verified.** Zero-edit upheld; plan checkbox marked `[x]`.

- Reconfirmed item-scoped diff empty:
  `git diff 75fdfc9d750490c3363e2dcfbbe51cc3c95193a8 -- django_strawberry_framework/utils/`
  produces no output. Working-tree dirt under `utils/` vs HEAD matches the
  baseline (concurrent / pre-item) and was not part of this item.
- Independently re-traced `sessions.py` end-to-end and its callers:
  `session_store_class` has exactly two sites (`auth/sessions.py` capability
  check; `consumers.py::_refreshed_actor` instantiate). `auth/__init__.py`
  eagerly imports `.mutations` / `.queries`, so hosting the resolver in
  `auth.sessions` would register the opt-in subsystem on first WebSocket
  revalidation — placement in utils is load-bearing, not inventory taste.
  Actor lease / provenance / `actor_transition` are single-sited under one
  scope key; auth's `_SCOPE_LOCK_KEY` and consumers' `_REVALIDATED_AT_SCOPE_KEY`
  are distinct contracts. Dual-hold order at `_channels_logout` (session lock
  OUTER, actor lease INNER) is the only cross-owner coupling and does not
  justify merging modules.
- Independently re-traced `context.py` end-to-end: sole dict/object/frozen
  dispatch. Optimizer owns key vocabulary + clear loop
  (`optimizer/_context.py`); resource policy owns its keys
  (`resource_policy.py`); both import the dispatch from utils. Optimizer
  re-exports are a historical import path, not a second body.
- Challenged Rejected #1 (shared lazy scope get-or-create): only two
  await-free get-or-create sites, creating different values across the auth
  opt-in boundary — co-located-mirror lesson from types folder applies; no
  third site. Rejected #2–#6 re-checked against present-day callers
  (`request_from_info` fail-loud + Channels adapter vs silent stash;
  `input_values` family-sentinel walk vs `iter_provided_input_fields` UNSET
  strip keeping explicit `None`). No overturn.
- Independent folder-level search for missed consolidations involving the
  extra modules (scope-key literals, alternate stash/getattr paths, moving
  provenance into consumers-only, splitting `session_store_class` from the
  lease): none warranted. Dual-subject cohabitation in `sessions.py` remains
  the correct seam across the forbidden auth↔consumers import edge.
- Project-pass leftovers left open (correct). No production edit; no pytest;
  concurrent dirt outside this item untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
