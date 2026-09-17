# DRY review: `django_strawberry_framework/utils/querysets.py`

Status: verified
Run: 0.0.15 2026-09-17-1

Revision pass 1 (Worker 1, after Worker 2's `revision-needed`): see `## Iterations` at the
bottom. Two figures in `## System trace` were corrected in place; nothing else above was
rewritten, and two `## Findings` rows are superseded rather than edited.

Item kind: FILE (inventory backstop). No consolidation performed; every rule below is either
assigned to a named responsibility family for a later family item, or recorded file-local with
the challenge that proved it. Zero production edits; zero tracked files changed.

## System trace

4294 lines, read end to end. Inventory instrument: `ast.parse` over the pinned blob, counting
`ast.Module.body` members only — **102 top-level functions, 7 classes, 25 module-level
constants (134 names; 109 excluding constants), plus 6 nested methods**. (Revision 1 corrected
this line: it previously read "99 module-level symbols", a figure no instrument reproduces.
Revision 1 then re-derived the assignment name-by-name against the full 134-name enumeration
rather than trusting that the original pass had been complete; that re-derivation found two
unassigned rules, recorded as I-R3 and I-R5 in `## Iterations`.) The module is the package's neutral
query-source substrate and its hardened `get_queryset` security boundary. 22 package modules
import from it (`permissions.py`, `schema.py`, `relay.py`, `orders/sets.py`,
`forms/resolvers.py`, `list_field.py`, `auth/mutations.py`, `utils/execution_mode.py`,
`utils/permissions.py`, `utils/write_values.py`, `connection.py`, `filters/base.py`,
`filters/sets.py`, `mutations/permissions.py`, `mutations/resolvers.py`,
`optimizer/extension.py`, `optimizer/walker.py`, `resource_policy.py`,
`rest_framework/resolvers.py`, `types/relay.py`, `types/resolvers.py`, `utils/__init__.py`).
`SyncMisuseError` is re-exported from the package root and from `types/relay.py`.

Five responsibility clusters live here:

1. **Query-source seeding and coercion** — `model_for`, `base_queryset`, `initial_queryset`,
   `normalize_query_source`, `_coerced_manager_queryset`, `_captured_model`.
2. **Colored-boundary refusals** — `reject_async_in_sync_context`, `_disposed_awaitable`,
   `_dispose_sync_awaitable`, `reject_awaitable_sync_source`, `reject_residual_async_source`,
   `is_async_only_iterable`, `reject_async_iterable_in_sync_context`, the `_AsyncQuerySetRows`
   adapter trio, `run_in_one_sync_boundary`, `sync_pipeline_recourse`.
3. **The sealed-execution-queryset boundary** — lines 486-3330, roughly 65 symbols: state
   extraction without dispatch, genuineness-by-object-identity, exact-type inventories, the
   three-state graph walk, canonical reconstruction, prefetch sealing, deferred-filter baking,
   `_SealPolicy` and its seven policy constants, routing intent, defect codes.
4. **Visibility runners and their relation helpers** — `_prepared_visibility_source`,
   `_normalized_visibility_result`, `apply_type_visibility_sync` / `_async`,
   `visibility_scoped_related_queryset`, `related_visibility_queryset(_or_default)`,
   `visible_related_object(s)`, `_stringified`, `stringified_pks_present`, `pks_all_present`.
5. **Raw-list row-source ownership and the resolver-source head** — `normalized_row_source`,
   `materialized_rows`, `_readable_queryset_state`, `_row_source_model`,
   `_raw_list_source_message`, `prepared_resolver_source`,
   `post_process_queryset_result_sync` / `_async`.

Connected code read for judgment, outside the item: `connection.py`, `list_field.py`,
`relay.py`, `permissions.py`, `optimizer/walker.py`, `optimizer/nested_fetch.py`,
`types/resolvers.py`, `rest_framework/resolvers.py`, `utils/write_values.py`,
`utils/write_transaction.py`, `utils/permissions.py`, `mutations/permissions.py`,
`filters/base.py`, `filters/sets.py`, `auth/mutations.py`, `routers.py`, `exceptions.py`,
`resource_policy.py`, `tests/utils/test_querysets.py`, `docs/GLOSSARY.md`,
`docs/spec-050-list_field_arguments-0_0_15.md`, `docs/SPECS/spec-045-visibility_boundary-0_0_14.md`.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Searched every public surface for its own spelling of
this module's rules. `models.Manager` appears in exactly three places, all inside this file
(querysets.py:307, 3479, 3818) — no flavor coerces a Manager itself. `__django_strawberry_definition__.model`
is read at exactly one site (`model_for`, querysets.py:243); the only other mention package-wide
is a `types/relay.py` docstring. `reject_async_in_sync_context` is reached by all three sync
hook seams Decision 9/15 name (`relay.py` ×2, `utils/permissions.py`, `mutations/permissions.py`)
plus this module's own runner. `sync_pipeline_recourse` is composed by all three write flavors
(`mutations/resolvers.py:139`, `forms/resolvers.py:125`, `rest_framework/resolvers.py:201`).
`prepared_resolver_source` and `reject_async_iterable_in_sync_context` are each reached by both
collection flavors (list field and connection). Positive results: the **pre-sliced source**
rule has a second flavor-local definition in `connection.py::_guard_source_not_pre_sliced`
(F4), and the **related-object visibility re-check** has a second one in
`types/resolvers.py::_visible_related_object` (F5).

**2. Sync/async twins.** Four colored pairs touch this module: `apply_type_visibility_sync` /
`_async`, `post_process_queryset_result_sync` / `_async`, `reject_awaitable_sync_source` /
`reject_residual_async_source`, and the caller-side `_apply_orderset_sync` / `_async` in
`list_field.py`. Compared by behavior, not shape, and by signature parity:

```text
apply_type_visibility_sync (type_cls, queryset, info, async_recourse='...', *, model=None, render_error=None, policy=_SealPolicy(...))
apply_type_visibility_async(type_cls, queryset, info,                       *, model=None, render_error=None, policy=_SealPolicy(...))
```

Every seam a surface can vary (`model`, `render_error`, `policy`) is present on both colorings;
`async_recourse` is sync-only and correctly so (the async twin awaits rather than refuses). The
two bodies share `_prepared_visibility_source` and `_normalized_visibility_result` verbatim and
differ only at the await point and its nested-awaitable refusal — principle 5's "one body, named
adapters" shape, already recorded at the async runner (querysets.py:4120-4131). The
`_SealPolicy` docstring records the historical drift this closed ("which is how the async runner
came to reach none of them"), so the twin axis is a solved problem here, not an open one.
`post_process_queryset_result_*` differ only in the `async_guard` they pass and the `await`.
No behavioral divergence found.

**3. Derived rather than repeated knowledge.** Four facts in this file are reconstructed by a
second means rather than restated: `_RETAINED_LEAF_TYPES` is *derived* from `_INERT_VALUE_TYPES`
(querysets.py:1481); `_DIRECT_RHS_DATA_BASES` and `_DIRECT_RHS_TRUSTED_MRO` are derived from it
too (1079, 1083); `_BOUND_VALUE_NORMALIZERS` is a deliberately **hand-ordered mirror** of it
(1670-1692, order is semantic so it cannot be derived) whose agreement is pinned mechanically by
`tests/utils/test_querysets.py::test_bound_value_normalizers_mirror_the_inert_inventory`; and
`_PLAIN_CONTAINER_TYPES` is the prove-side inventory whose rebuild-side answer is pinned by
`::test_every_admitted_plain_container_has_a_rebuild_branch`. Both mirrors carry principle-9
gates, so neither is a second definition. The one *ungated* derived fact is the seal's defect-code
set (F3). Outside the file: `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
re-derives "is this queryset sliced / combined / values-shaped" from `query` attributes; contract
difference recorded in F4.

**4. Inverse / round-trip pairs.** Three pairs, all with both halves in this file:
`wrap_async_queryset_adapter` / `unwrap_async_queryset_adapter` (consumed across `list_field.py`
and `optimizer/extension.py`); `_rebuilt_prefetch_or_defect` (rebuild) against
`_sealed_prefetch_related_lookups` (validate); and the load-bearing one — the whole prove side
(`_expr_graph_defect`, `_container_defect`, `_direct_rhs_defect`, `_is_inert_value`) against the
whole rebuild side (`_reconstructed_value`, `_normalized_bound_value`, `_is_reconstructable_node`).
The dangerous direction (prover-accepted / rebuilder-unhandled) is named at
`_PLAIN_CONTAINER_TYPES` and gated for containers and for bound-value leaves; for AST nodes the
two halves compose the SAME predicate by name (`_type_is_genuinely_django`), so they cannot
disagree by construction. The adapter trio yielded F9 (a third member with no production reader).

**5. Contracts restated in another medium.** Five media carry this module's contracts: production
code; `tests/utils/test_querysets.py` (5760 lines, 309 tests — oracles, several of them
independent by DRY.md's definition, e.g. the two inventory-agreement tests above); the live tier;
`docs/GLOSSARY.md` anchors *Sealed execution queryset* (1891), *Visibility boundary* (2127),
*Prefetch alias threading* (1556), *Prove-then-clone AST trust*, *Callable shadow defect*; and
`docs/SPECS/spec-045-visibility_boundary-0_0_14.md` plus the in-flight
`docs/spec-050-list_field_arguments-0_0_15.md`. Counting the media a change must move surfaced
**D2**: the glossary projection still describes a keyword (`allow_sliced=True`) that
`_SealPolicy` replaced, and `docs/SPECS/spec-034-permissions-0_0_10.md:353` still pins the
retired call shape as a "verified dependency to protect".

**6. Enforcement by omission.** Three families enumerated member-by-member.
(a) *Child-alias inheritance*: `base_queryset`'s own docstring names three surfaces that seed
from a relation's target model — the cascade edge, a `RelatedFilter` child, and the optimizer
walker's prefetch child. Two pass `using=` (`permissions.py:692` `using=state.alias`;
`filters/sets.py:2592` `using=parent_db`); `optimizer/walker.py:443` does not, and seals under a
policy that does not set `require_shared_alias`. Contract sources establish the rule for that
member, so this is **D1**, a behavior defect, not a consolidation.
(b) *Post-`OrderSet` result validation*: `list_field.py` freezes routing intent and re-seals the
override's return; `connection.py:1828/1865` invokes the same public `OrderSet.apply_sync` /
`apply_async` with neither. The contract sources found (spec-050's Edge cases, the
`_SealPolicy.require_unevaluated` prose) both scope the rule to the list field, so the axis says
*ambiguous* — routed to Rio through Worker 0 (**D3**), not decided here.
(c) *Awaitable disposal*: enumerated every site that refuses an awaitable. The shared
`_dispose_sync_awaitable` covers this module, `list_field.py` and the two exported refusers;
`auth/mutations.py:505-511` (twice) and `routers.py:279-285` each spell detect-then-dispose
inline. That is duplication, not a gap — F1.

### Challenges

Each change posited against the rule's own variation axes; the count is authoritative
definitions only. Consumers, oracles and projections that also move are listed, never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | read the model registered to a `DjangoType` | definition attribute is renamed / becomes a method | **1** (`model_for`) | independent |
| C2 | seed a fresh base queryset for a model, optionally alias-pinned | seeds must pass `db_manager(alias)` instead of `.using(alias)` | **1** (`base_queryset`) | independent |
| C3 | coerce a `Manager` to a `QuerySet` | a Manager that returns an async iterable must fail closed | **1** (`_coerced_manager_queryset`) | independent |
| C4 | coerce a raw literal through a Django field, or nothing | add a per-field normalization step before validation | **1** (`coerce_field_value_or_none`); `canonical_pk` does NOT move | independent; F6 records why |
| C5 | dispose a refused awaitable so no "never awaited" warning escapes | async generators gain a disposal protocol | **3** (`_dispose_sync_awaitable`, `auth/mutations.py` inline, `routers.py` inline) | duplication — F1 |
| C6 | the "runs synchronously, cannot await" recourse sentence | the sentence must name the settings key that relaxes it | **4** (`sync_pipeline_recourse`, `_RELAY_ASYNC_RECOURSE`, `_PERMISSION_ASYNC_RECOURSE`, `_GATE_ASYNC_RECOURSE`) | 3 rejections already recorded at owners — F7 |
| C7 | run one consumer sync hook in exactly one off-loop worker | the boundary must also bind a ContextVar | **1** (`run_in_one_sync_boundary`) + 5 direct `sync_to_async(...)` sites with different subjects | F11 |
| C8 | "async-only iterable" | a new async-only shape must be recognized | **1** (`is_async_only_iterable`); `connection.py`'s `(AsyncIterator, AsyncIterable)` tests do NOT move | independent — F10 |
| C9 | prove an embedded node is genuine Django | provenance moves from `sys.modules` identity to an interpreter-level check | **1** (`_type_is_genuinely_django`), composed by name by `_is_reconstructable_node` | independent |
| C10 | admit a new inert query-parameter leaf type | one entry in `_INERT_VALUE_TYPES` + one normalizer | **2 declared inventories, mechanically pinned to agree** | independent by principle 9 |
| C11 | admit a new plain container type | prove side + rebuild side | **2, mechanically pinned** | independent by principle 9 |
| C12 | add a seal defect code | the seal's return + an arm at every message site that can reach it | **1 definition**, 6 message sites, **no gate** | gate-only — F3 |
| C13 | add a seal policy axis | one `_SealPolicy` field + one check in `_seal_or_defect` | **1** | independent (the worked-example shape) |
| C14 | relax "a pre-sliced source is rejected" for a new surface | `_SealPolicy.reject_sliced` + `connection.py::_guard_source_not_pre_sliced` | **2** | duplication — F4 |
| C15 | resolve one visible related object through the target's hook | the hook must also receive the relation descriptor | **2** (`visible_related_object`, `types/resolvers.py::_visible_related_object`) | duplication — F5 |
| C16 | the relation-membership pk comparison basis | a pk type whose `str()` is ambiguous | **2** (`_stringified`, `write_transaction.py::canonical_pk`) | rejected — F6 |
| C17 | a child queryset must stay on its parent's connection | a fourth child-seeding surface appears | **2** (`base_queryset(using=)`, `_SealPolicy.require_shared_alias`) + 1 member not enforced | F8 / D1 |
| C18 | re-seal a public `OrderSet.apply_*` return against frozen routing | the connection field must do it too | **1** (`_validate_post_orderset_result`) | independent; enforcement question is D3 |

**Experiments.**

```shell
uv run python docs/dry/temp-tests/dry-file-utils__querysets/probe_alias_policy.py
```

Read-only, zero SQL (the seal composes lazy query state only). Output:

```text
_DEFAULT_SEAL_POLICY: defect=None sealed_db='shard_b'
_UNRECOMPOSED_CHILD_POLICY: defect=None sealed_db='shard_b'
_PREFETCH_CHILD_POLICY: defect=('alias', 'shard_b') sealed_db=None
```

Proves the policy asymmetry D1 rests on: a queryset explicitly routed off the outer alias is
**accepted** under the policy `optimizer/walker.py::_build_child_queryset` seals with, and
**rejected** under the policy a `Prefetch` child gets. Status: `execution-verified`. Rejects the
wrong result "both child policies pin the alias".

```shell
uv run python docs/dry/temp-tests/dry-file-utils__querysets/probe_using_order.py
```

Read-only, zero SQL. Output: `default manager: shard_b shard_b True True` — for a default
manager, `manager.using(a).all()` and `manager.all().using(a)` produce the same `_db`, the same
SQL and the same type, i.e. the orders are indistinguishable at the seam `base_queryset` occupies.
Status: `execution-verified`. Rejects the wrong result "the two spellings differ for the seed this
function performs", which is what `base_queryset`'s docstring asserts (**D4**).

## Findings

No production edit is owed by a file item; each finding names the family that will own it.

### F1 — awaitable refusal and disposal has three definitions

- **Contract + variation.** A refused awaitable must be detected without awaiting it and then
  released (native coroutine closed, future cancelled) so no "coroutine was never awaited"
  RuntimeWarning escapes. Legitimate variation: what follows the disposal (raise
  `SyncMisuseError`, raise `ConfigurationError`, return a not-authenticated sentinel, append an
  error addendum) and whether disposal failures are suppressed.
- **Sites + roles.** *Definitions*: `utils/querysets.py::_dispose_sync_awaitable` (querysets.py:217,
  coroutine + future); `auth/mutations.py` #"is_authenticated.close()" (two inline copies at 505-511,
  coroutine only, wrapped in `contextlib.suppress(BaseException)`); `routers.py` #"application.close()"
  (279-285, coroutine only). *Consumers*: `reject_async_in_sync_context`, `_disposed_awaitable`,
  `apply_type_visibility_async`, `reject_awaitable_sync_source`, `reject_residual_async_source`,
  `list_field.py::_apply_orderset_sync` / `_apply_orderset_async`, `utils/permissions.py`,
  `mutations/permissions.py`, `relay.py` ×2. *Projection*: the `_disposed_awaitable` docstring,
  which already records "Four sites spelled this pair inline".
- **Challenges.** C5 → 3 definitions. Second axis: "futures must be awaited-with-timeout rather
  than cancelled" → the same 3.
- **Owner + lifetime.** Existing owner by responsibility: `utils/querysets.py::_dispose_sync_awaitable`.
  It is already the neutral cycle-safe substrate both `auth/` and the root import from
  (`auth/mutations.py` already imports `run_in_one_sync_boundary` from it), so no dependency is
  reversed. No stored derivation; no lifetime fields owed.
- **Distinct behavior to preserve.** `auth/mutations.py` suppresses `BaseException` from `.close()`
  because a hostile `is_authenticated` must classify as anonymous rather than raise; `routers.py`
  needs to know *whether* it disposed so it can append `_ASYNC_FACTORY_HINT`. `_disposed_awaitable`
  already returns that boolean. The suppression is the one genuine variation and would be an
  adapter, not a mode flag.
- **Behavioral proof.** `static-reviewed` — import moves and body composed by name; the refusal
  each site raises stays at the site. Rejects the wrong result "consolidating changes which
  exception a seam raises". An `execution-deferred` proof is NOT owed by this file item; the
  family item owes one for the `auth/` suppression arm.
- **Structural gate.** Owed by the family item, not here. Negative control it must survive: a
  behavior-preserving hand copy of `_dispose_sync_awaitable`'s two-branch body pasted back into
  `routers.py`. A name/existence assertion would pass that control, so the gate must be
  behavioral (assert no `RuntimeWarning` escapes with `filterwarnings = error` already armed).
- **Family.** `awaitable-refusal-and-disposal`.
- **Freshness.** `utils/querysets.py` `5907a1f72de42c71402886e7480ab559eb06a3af`,
  `auth/mutations.py` `dbe64995b87240b87a1d5119f46cc42c7cab646f`,
  `routers.py` `a18c5001471d4a937bb81d2ff41a2e442e7d2dad`.

### F2 — the sealed-execution-queryset boundary is one rule with one owner

- **Contract + variation.** A consumer-supplied or hook-returned queryset is untrusted query
  STATE: read it without dispatching consumer code, validate it, rebuild a framework-owned plain
  `QuerySet` from the validated state, never return the consumer object. Variation axes are
  declared, not branched: the five `_SealPolicy` fields and the seven policy constants.
- **Sites + roles.** *Definition*: `_seal_or_defect` and the ~60 helpers it composes — all in
  this file. *Consumers*: `_prepared_visibility_source`, `_normalized_visibility_result`,
  `_validate_post_orderset_result`, `normalized_row_source`, `_sealed_prefetch_related_lookups`
  (recursive), plus `permissions.py`, `list_field.py`, `optimizer/walker.py`, `connection.py`,
  `types/resolvers.py`, `resource_policy.py` through the runners. *Oracles*:
  `tests/utils/test_querysets.py`. *Projections*: the glossary anchors and spec-045.
- **Challenges.** C9, C10, C11, C13 — each forces exactly one definition (two mechanically-pinned
  inventories for C10/C11). No surface outside this file constructs a `models.QuerySet(...)` or
  touches `sql.Query` (searched package-wide: zero hits). `object.__getattribute__` /
  `type.__getattribute__` / `inspect.getattr_static` appear nowhere else in the package.
- **Distinct behavior.** The raw-list row-source rule (`normalized_row_source`,
  `_RAW_LIST_SOURCE_POLICY`) is deliberately a *different question* from visibility — it asks who
  owns the slice, not who may see the rows — and is recorded as its own policy constant rather
  than a branch. Kept.
- **Behavioral proof.** `static-reviewed` for the ownership claim (a package-wide search for the
  mechanism returned one definition). No edit, so no equivalence proof is owed.
- **Family.** `sealed-execution-queryset`. Named so a family item sweeps the whole package for the
  mechanism (`_meta.concrete_model` reads, `_iterable_class` / `_result_cache` / `is_sliced`
  reads, `Prefetch(` construction) rather than this file's neighbours; the four such readers
  found (`connection.py:1603`, `optimizer/nested_fetch.py:123,131,197`,
  `optimizer/predicates.py:165`, `optimizer/extension.py:1161`) all run on already-sealed
  framework-owned querysets and ask planning questions, which the family item should confirm
  independently.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `tests/utils/test_querysets.py`
  `c9a84d53f3e74e3f5274a6b5096ce1a17ceef292`.

### F3 — the seal's defect-code set is a rule with no gate (gate-only)

> **Revision 1 — the "Justified population for a gate" paragraph below is SUPERSEDED by I-R4.**
> This finding assumed the rule it proposes to gate currently holds. Measured, it does not: three
> sites in this file declare arms for codes their own call shape cannot produce. I-R4 restates the
> gate population against the tree as it is and routes the false-invariant docstring to `## Defects`
> as D5.

- **Contract + variation.** The seal's defect codes are a closed, canonically ordered set
  (`type` → `table` → `untrusted` → `routing` → `evaluated` → `sliced` → `combined` →
  `projection` → `alias`, stated at querysets.py:3039-3041). Every message-building site renders
  only the subset IT can reach, and "a new code takes a FIXED position in it, and owes an arm at
  every message-building site that can reach it".
- **Sites + roles.** *Definition*: the seal's own `return None, (code, detail)` statements — one
  definition, enacted by control flow. *Consumers*: six `_defect_message` call sites
  (`_validate_post_orderset_result`, `_raw_list_source_message`, `_visibility_result_error`,
  `_prepared_visibility_source`, `permissions.py:353`, `permissions.py:412`). *Projection*: the
  prose ordering in the `_seal_or_defect` docstring, and the per-site "which codes can reach me"
  paragraphs at querysets.py:2988-3005 and 3442-3446.
- **Challenges.** C12 → 1 definition, 6 sites that must be revisited by hand. `_defect_message`
  makes a missing arm *legible at runtime* (`tests/utils/test_querysets.py::test_unrendered_defect_code_says_so_instead_of_mislabelling`
  pins that) but nothing fails at build or test time. Per DRY.md this is a `gate-only` finding:
  owner already single, no gate.
- **Justified population for a gate.** The six `_defect_message` call sites, and the codes each
  reachable `_SealPolicy` can actually emit. Plausible bypass: a seventh site, or a new code whose
  author updates four of the six ladders. A bespoke existence test per helper is explicitly not
  what is wanted; the gate must enumerate the population independently.
- **Behavioral proof.** `static-reviewed`. No edit owed here.
- **Family.** `seal-defect-code-wording`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `permissions.py`
  `9e0236b3bbcfa9320a5d4e18e34b35c27adf233e`.

### F4 — "a pre-sliced source is rejected" has two definitions

- **Contract + variation.** A source a surface will recompose onto (reorder, refilter, window)
  may not arrive already sliced, because Django forbids reordering a sliced query and the next
  transform would raise a raw `TypeError` outside the typed contract. Legitimate variation:
  surfaces that do NOT recompose (a `Prefetch` child, the optimizer's nested-connection child)
  switch it off.
- **Sites + roles.** *Definitions*: `_SealPolicy.reject_sliced` + the `sliced` arm of
  `_seal_or_defect` (querysets.py:3291); `connection.py::_guard_source_not_pre_sliced`
  (connection.py:1602-1625), which reads `source.query.is_sliced` through ordinary attribute
  access on an untrusted consumer queryset and raises a `GraphQLError`. *Not a definition*:
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`, which classifies five shapes
  (`sliced`, `select_for_update`, `combined`, `distinct`, `values`) to **degrade a plan**, never
  to reject — a different contract with different reasons to change.
- **Challenges.** C14 → 2 definitions. Both give the same stated reason (recomposition is
  illegal on a sliced query); they differ in error class (`GraphQLError` vs
  `ConfigurationError`), in timing (before visibility vs during the seal) and in whether the read
  dispatches consumer code.
- **Owner + lifetime.** Candidate owner `utils/querysets.py::_SealPolicy` / `_seal_or_defect`.
  The family item must decide whether the connection's earlier, wire-flavored rejection is a
  legitimate adapter (it names the `resolver=` contract at the wire, which the seal's
  `ConfigurationError` does not) or a second definition to delete. Note the seal already rejects
  the same source one step later, so the guard is not load-bearing for fail-closed behaviour.
- **Coupling.** None. F4 and D3 both touch `connection.py`'s sidecar pipeline; they are
  independent decisions.
- **Behavioral proof.** `static-reviewed` (no edit). Any consolidation would owe an
  `execution-verified` proof that the error CLASS a client sees does not change, since
  `GraphQLError` and `ConfigurationError` surface differently at the boundary.
- **Family.** `recomposition-illegal-source-rejection`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `connection.py`
  `93e998f2c7ea1d7f18607a6e37e394466ac75ad4`, `optimizer/nested_fetch.py`
  `4d8d37a7f52cf94d2916f17db3a8a21393e28d57`.

### F5 — "resolve one visible related object" has two definitions

- **Contract + variation.** Given a related row and its target type, re-confirm the row is
  visible through the target's `get_queryset` hook before it crosses the boundary. Legitimate
  variation: the key (model vs registered type), the coloring (sync-only vs colored), and the
  tail (write-pipeline pin + lock vs `_state.db` pin).
- **Sites + roles.** *Definitions*: `utils/querysets.py::visible_related_object` (model-keyed,
  registry resolve, default-manager fallback, `pipeline_scoped_queryset`, sync-only);
  `types/resolvers.py::_visible_related_object` (type-keyed, `_state.db` pin, colored
  sync/async, no registry resolve, no pipeline scope). *Consumers*: `utils/write_values.py:226`,
  `types/resolvers.py` ×7. *Related, composed by name*: `visibility_scoped_related_queryset`,
  `related_visibility_queryset`, `related_visibility_queryset_or_default`,
  `rest_framework/resolvers.py:1447`.
- **Challenges.** C15 → 2 definitions. Second axis: "the visibility query must also be pinned to
  the write alias on the read path" → 2 again. Third axis: "the write decoder needs an async
  coloring" → 2.
- **Owner + lifetime.** Candidate owner `utils/querysets.py`. The shared kernel is
  `apply_type_visibility_*(target_type, initial_queryset(target_type).filter(pk=pk), info)`
  followed by `.first()` / `.afirst()`; what genuinely differs is the *seed pin* and the
  *coloring*, both of which are adapter-shaped. The family item must first try to disprove shared
  responsibility: the read-side re-check exists to confirm an already-prefetched row, the
  write-side decoder exists to admit a client-named row, and those may be two rules that agree
  today.
- **Behavioral proof.** `static-reviewed` (no edit). Any consolidation owes an
  `execution-verified` proof of query count and of the async coloring, since the read path
  returns a coroutine from a sync function.
- **Family.** `related-object-visibility-recheck`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `types/resolvers.py`
  `fc077f38a1f10db2a447c11b11bea1e82bcbb362`, `utils/write_values.py`
  `d28587c7c8d9f0d25e0a01bf289a63d9c3291728`, `rest_framework/resolvers.py`
  `8024703ec0fb09758daeec0585e0065de1c61fc3`.

### F6 — REJECTED: the two pk comparison bases are two rules

- **Shared form considered.** One canonical pk comparison primitive for the whole package,
  replacing both `utils/querysets.py::_stringified` (the `{str(pk) for pk in ...}` membership
  basis behind `stringified_pks_present` / `pks_all_present`) and
  `utils/write_transaction.py::canonical_pk` / `pks_match` (the `to_python`-both-sides equality
  behind `reject_substituted_row`).
- **Contract difference.** `_stringified` builds a *set membership basis* for a batched
  `pk__in` result, where both sides have ALREADY been canonicalized: the declared side passes
  through `type_check_relation_id` → `coerce_relation_pk_or_none` →
  `coerce_field_value_or_none` (`utils/write_values.py:302-309`) before
  `visible_related_objects` is called, and the present side comes back from the DB as the field's
  own Python type. Stringifying two already-canonical values is a *hashability* convenience, not
  a comparison rule. `canonical_pk` compares a consumer-supplied `save()` return against an
  authorization snapshot where NEITHER side is pre-coerced, which is exactly the case its comment
  warns about ("a UUID pk stringifies in more than one spelling of the SAME row"). It also raises
  rather than returning `None`, and deliberately skips `run_validators` (it is answering "same
  row?", not "may this literal enter a query?"). Merging them would either add validator
  rejection to an equality test or drop the fail-closed raise from an authorization check.
- **Reconsideration trigger.** If `stringified_pks_present` ever receives pks that have not
  passed `coerce_field_value_or_none` first — i.e. a caller reaches it without
  `type_check_relation_id` — the stringified basis stops being safe and the two collapse into one
  rule. Grep the callers of `stringified_pks_present` / `pks_all_present` for that.
- **Durable home for the rejection.** `utils/querysets.py::_stringified` (one plain clause noting
  the basis is valid only because both sides are pre-canonicalized). Not written by this item —
  a file item lands no edit; recorded here for the family item.
- **Related, also single-owned.** `coerce_field_value_or_none` has exactly one definition and
  three named consumers (`relay.py::_coerce_pk_or_none`, `utils/write_values.py::coerce_relation_pk_or_none`,
  `filters/base.py::_coerce_int_in_members`), each composing it by name against a different
  field — the "WHICH field stays at the caller" split is principle 2's "one owned translation",
  correctly applied. `keyset.py:384` uses `field.to_python` without validators for cursor decode:
  a third contract (round-trip re-serialization), not a copy.
- **Family.** `field-value-coercion`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `utils/write_transaction.py`
  `eca9ad4d3f765964df05884e080eb3ea63190ca8`, `utils/write_values.py` `d28587c7…`,
  `rest_framework/resolvers.py` `8024703e…`.

### F7 — REJECTED (re-verified): the two permission recourse sentences stay separate

- **Shared form considered.** Extending `sync_pipeline_recourse` to also generate
  `mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE` and
  `utils/permissions.py::_GATE_ASYNC_RECOURSE`.
- **Prior rejection re-derived, not inherited.** Both owners already record the rejection
  (`sync_pipeline_recourse` docstring declines them; `mutations/permissions.py:44-49` states
  "four of their clauses differ, so a template would take a parameter per clause and pin
  nothing"). Re-read both literals at this HEAD: the write recourse names
  `has_permission / check_permission`, requires a `bool` return, and names `user.has_perm` /
  auth backends; the gate recourse names `check_<field>_permission` and the FilterSet / OrderSet
  subject. They share one clause ("runs synchronously, so it cannot await"). Rejection stands.
- **Reconsideration trigger.** If either sentence is reworded so the two differ only in the
  subject noun — the exact shape `sync_pipeline_recourse` already solved for the three write
  flavors — they become one rule.
- **Also verified.** `_RELAY_ASYNC_RECOURSE` (querysets.py:349) stays separate for a stated
  reason that holds: async IS possible on the Relay branch, so its recourse offers a different
  remedy. `permissions.py::_ASYNC_RECOURSE` likewise (no async-native cascade walk exists).
- **Family.** `sync-boundary-recourse-wording`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `mutations/permissions.py`
  `54f770ae5aa1238327246cd2dcb141e8aac14965`, `utils/permissions.py`
  `9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec`, `permissions.py` `9e0236b3…`.

### F8 — child-queryset alias inheritance: one rule, two enforcement mechanisms, one unguarded member

- **Contract + variation.** A queryset seeded for a relation's target model must read on the same
  database connection as the parent that seeded it, so one GraphQL resolution never spans two
  connections. Two mechanisms encode it: `base_queryset(model, using=...)` pins the *seed*, and
  `_SealPolicy.require_shared_alias` rejects a *hook result* routed elsewhere.
- **Sites + roles.** *Definitions*: `base_queryset`'s `using` arm (querysets.py:265);
  `_seal_or_defect`'s `require_shared_alias` arm (querysets.py:3299-3304). *Enforcement sites*:
  `permissions.py:692` (`using=state.alias`), `filters/sets.py:2592` (`using=parent_db`),
  `_sealed_prefetch_related_lookups` (threads the outer effective alias into the child seal).
  *Unguarded member*: `optimizer/walker.py:443` seeds without `using=` and seals under
  `_UNRECOMPOSED_CHILD_POLICY`, which does not set `require_shared_alias` — see D1.
  *Projection*: `docs/GLOSSARY.md` *Prefetch alias threading*.
- **Challenges.** C17 → 2 definitions, which is the correct count: they answer different
  questions (what the seed routes to; what the hook may change it to) and would not move
  together for a seed-spelling change. Not a consolidation candidate.
- **Coupling.** D1 must be resolved before any consolidation here; an alias rule with an
  unguarded member is not a rule whose owner can be moved.
- **Behavioral proof.** `execution-verified` via `probe_alias_policy.py` above, for the policy
  asymmetry. `static-reviewed` for the seed-site enumeration.
- **Family.** `child-queryset-alias-inheritance`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `optimizer/walker.py`
  `054207017c3435ed1f6b7891683fed112c807d11`, `permissions.py` `9e0236b3…`,
  `filters/sets.py` `4ab65a26b0ccf56f7f40f4938282bba9690673d1`, `docs/GLOSSARY.md`
  `37a61802fbb2c257d12e33b34bc3ea1a08c4b3fa`.

### F9 — `is_async_queryset_adapter` has no production reader (principle 11)

- **Contract.** `_AsyncQuerySetRows` is the async-only completion adapter; three module-level
  functions surround it: `wrap_async_queryset_adapter`, `unwrap_async_queryset_adapter`,
  `is_async_queryset_adapter`.
- **Sites + roles.** *Definition*: querysets.py:414-416. *Production readers*: **none**, searched
  package-wide. `list_field.py` uses only `wrap_`; `optimizer/extension.py:1142-1145` uses
  `unwrap_` (which returns `(value, was_adapted)`) and `wrap_`. *Test readers only*:
  `tests/test_list_field.py` ×7, `tests/optimizer/test_extension.py` ×9. Not in any `__all__`,
  not re-exported from the package root.
- **Challenge.** "What breaks if it is removed and inlined?" Nothing in production. The 16 test
  assertions would spell `isinstance(x, _AsyncQuerySetRows)` or read the second element of
  `unwrap_async_queryset_adapter`. Note the current tests are NOT independent oracles for the
  adapter — they check the owner's own predicate against itself — so the deletion question is
  entangled with whether those assertions should name the class instead.
- **Owner + lifetime.** Decision (keep as a boundary name callers depend on, or delete and
  inline) belongs to the family item, which must also decide the oracle shape. DRY.md requires
  the keep-or-move outcome to be recorded at the owner so the question is not re-raised.
- **Behavioral proof.** `static-reviewed` (search for readers, whole repo minus `.git` and
  `docs/shadow`). Rejects the wrong result "it is used by the optimizer".
- **Family.** `async-only-queryset-row-adapter`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `list_field.py`
  `f357eded3d96fcffe17e6fd84bceb8cd12af98d5`, `resource_policy.py`
  `9205124f41814dbda5a7df0a4882e10b5f951b2f`.

### F10 — REJECTED: `connection.py`'s async-shape tests are not a second `is_async_only_iterable`

- **Shared form considered.** Routing `connection.py:1050`, `:1095` and `:1575` through
  `is_async_only_iterable`.
- **Contract difference.** `is_async_only_iterable` is `AsyncIterable and not Iterable`; the
  `not Iterable` half exists precisely so a `QuerySet` (both sync- and async-iterable) never
  classifies as async-only. `connection.py:1050` / `:1095` ask the OPPOSITE question — "may the
  async executor stream this?" — and must answer **yes** for a QuerySet, which is the branch they
  take. `connection.py:1575` is an admission test (`Iterable` OR `AsyncIterable` OR
  `__getitem__`), a union rather than a difference. Substituting the shared predicate would send
  every queryset down the sync branch under async execution.
- **Reconsideration trigger.** If the connection field ever needs to tell an async-only consumer
  source apart from a queryset — e.g. to apply the same sync-execution refusal the list field
  applies — that new site is the shared rule's, not a fourth spelling.
- **Confirmed consumers of the real predicate.** `reject_async_iterable_in_sync_context`
  (this file), `list_field.py:891/895`, `resource_policy.py`. All three composed by name.
- **Family.** `sealed-execution-queryset` is not the right home; recorded under
  `async-only-queryset-row-adapter`, which owns the async-shape vocabulary.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `connection.py` `93e998f2…`,
  `resource_policy.py` `9205124f…`, `list_field.py` `f357eded…`.

### F11 — the one-sync-boundary rule has one definition and five direct-call sites to classify

- **Contract + variation.** A consumer-overridable sync hook must run in exactly ONE
  `sync_to_async(thread_sensitive=True)` worker per resolution, never per-step hops.
- **Sites + roles.** *Definition*: `run_in_one_sync_boundary` (querysets.py:483). *Consumers
  composing it by name*: `schema.py:73`, `permissions.py:125`, `orders/sets.py:50`,
  `filters/sets.py`, `mutations/resolvers.py:104`, `auth/mutations.py:73`. *Direct
  `sync_to_async(...)` calls not routed through it*: `types/resolvers.py:616/689/760`
  (`sync_to_async(getattr, thread_sensitive=True)` — a relation attribute read, not a consumer
  hook) and `testing/client.py:471/475` (`force_login` / `logout`, no `thread_sensitive` argument
  at all, and the test client is not a resolver surface).
- **Challenge.** C7 → 1 definition. The five direct sites do not encode the rule (they are not
  wrapping a consumer-overridable hook), so they are neither definitions nor enforcement sites of
  it. Recorded so a family item does not re-derive the classification, and so the
  `testing/client.py` omission of `thread_sensitive=True` is looked at deliberately rather than
  swept in.
- **Behavioral proof.** `static-reviewed`. No edit owed.
- **Family.** `one-sync-boundary`.
- **Freshness.** `utils/querysets.py` `5907a1f7…`, `types/resolvers.py` `fc077f38…`.

### F12 — file-local rules (no second site after the matrix)

Each carries the challenge that proved it. None is assigned to a family; each stays owned here.

> **Revision 1 — two rows in this table are SUPERSEDED, and the table is incomplete.** The
> `_safe_class_name` row and the `_prefetch_relation_target_or_none` row both claim "no second
> site" for rules that have one; they are replaced by I-R1 and I-R2 in `## Iterations`, which
> record them as REJECTIONS with a contract difference and a reconsideration trigger. Two rules
> the original table omitted entirely are added as I-R3 and I-R5. The remaining rows stand as
> written and were re-checked in revision 1. Prior text is left intact per DRY.md.

| Rule | Owner | Challenge posited | Definitions |
|---|---|---|---|
| Render a class name without letting hostile metaclass metadata escape, STRICTER than the shared renderer (a non-`str` `__name__` degrades to the metaclass label rather than `repr(name)`) | `utils/querysets.py::_safe_class_name` | "the fallback must also strip control characters" | 1 here; `exceptions.py::_safe_class_name` is a separate, deliberately weaker rule for non-boundary messages, documented at querysets.py:142-150 |
| Format database routing intent without invoking consumer `__repr__` | `_safe_routing_repr` | "hint values must render their id in decimal" | 1 (readers: `_seal_or_defect`'s routing arm, `tests/utils/test_querysets.py`, `tests/test_list_field.py`) |
| Three-state identity bookkeeping distinguishing a shared diamond from a cycle | `_GraphWalk` / `_WalkState` / `_walk_short_circuit` | "a fourth state is needed for a partially-validated node" | 1 (7 in-module callers; no other recursive proof in the package) |
| Freeze a source's routing intent before consumer code receives it | `_snapshot_routing_intent` | "the snapshot must also capture `_for_write`" (it does) | 1 (sole external consumer `list_field.py`) |
| Compare routing hints by identity, never by equality | `_routing_hints_equal` | "absent vs empty hints must stop being distinguished" | 1 |
| The `(negate, args, kwargs)` deferred-filter bake onto a detached clone | `_bake_deferred_filter_or_defect` + `_deferred_value_defect` | "a fourth prohibited kwarg ships in Django" (the `PROHIBITED_FILTER_KWARGS` import + floor mirror at querysets.py:100-108 is the single site) | 1 |
| Resolve a prefetch path to its relation target, including the default `<model>_set` accessor spelling | `_prefetch_relation_target_or_none` + `_reverse_relation_by_accessor_or_none` | "a `GenericForeignKey` alias must resolve rather than fail open" | 1 |
| The list-field consumer-resolver head order: refuse the wrong async shape, THEN normalize, THEN per-branch guard | `prepared_resolver_source` | "a third per-branch guard is needed" | 1 (both collection flavors compose it) |

## Defects

Non-duplication defects found while tracing. None fixed here.

### D1 — the optimizer walker's prefetch child can be re-routed to another database by its own visibility hook

`optimizer/walker.py::_build_child_queryset` seeds `base_queryset(field.related_model)` with no
`using=`, so `_prepared_visibility_source` resolves `required_alias = queryset._db` = `None`, and
seals under `_UNRECOMPOSED_CHILD_POLICY`, which does not set `require_shared_alias`. A target type
whose `get_queryset` returns `qs.using("other")` therefore passes, and the result is installed as
`Prefetch(lookup_path, queryset=child_queryset)` at `optimizer/walker.py:916` — a prefetch child
on a different connection from its parent. The plan applies that prefetch after visibility, so it
never passes back through `_sealed_prefetch_related_lookups`, which is where
`require_shared_alias` would have caught it.

Proven by `docs/dry/temp-tests/dry-file-utils__querysets/probe_alias_policy.py` (output above):
the same explicitly-routed queryset is accepted under `_UNRECOMPOSED_CHILD_POLICY` and rejected
with `('alias', 'shard_b')` under `_PREFETCH_CHILD_POLICY`.

Contract sources establishing the rule for this member: `_SealPolicy.require_shared_alias`
("Set solely for a `Prefetch` child, so one GraphQL resolution never spans two database
connections", querysets.py:2750-2753); `base_queryset`'s `using` paragraph ("a sharded parent must
seed its children on the SAME connection", querysets.py:256-262), which names the optimizer
walker's prefetch child as one of the three surfaces that seed from a relation's target model; and
`docs/GLOSSARY.md` *Prefetch alias threading*. The two sibling members named alongside it
(`permissions.py:692`, `filters/sets.py:2592`) both thread the alias.

Adding the guard changes what is accepted, so it is never behavior-preserving and must not ride a
consolidation. **Routes to:** the sealed-execution-queryset / visibility-boundary owner —
`optimizer/walker.py::_build_child_queryset` and `_UNRECOMPOSED_CHILD_POLICY`. Needs a named
owning card. Behavior is only observable under `FAKESHOP_SHARDED=1` or a multi-database settings
fixture, which this run is not authorized to execute (see `## Pending execution`).

### D2 — the glossary describes a keyword that no longer exists

`docs/GLOSSARY.md:1556` (*Prefetch alias threading*) states "The child seal allows a sliced
top-N-per-parent prefetch queryset (`allow_sliced=True`)". `allow_sliced` occurs **zero** times
under `django_strawberry_framework/`; the `_SealPolicy` record replaced the threaded keyword, and
the current spelling is `_PREFETCH_CHILD_POLICY = _SealPolicy(reject_sliced=False,
require_shared_alias=True)`. The glossary is rendered from the fakeshop `glossary` app DB, so the
repair is a `GlossaryTerm` body edit plus a re-render, not a file edit.

`docs/SPECS/spec-034-permissions-0_0_10.md:353` carries the same retired call shape inside a
"**Verified dependency to protect**" clause —
`apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)` — which no longer
matches the code it pins. (The four occurrences in
`docs/SPECS/spec-045-visibility_boundary-0_0_14.md` and the rationale appendices are historical
records of the shipped design and read correctly as such.)

**Routes to:** whoever introduced `_SealPolicy` — the in-flight spec-050 card. Needs a named
owning card.

### D3 — ambiguous: the connection field runs `OrderSet.apply_*` with no post-apply result seal

`list_field.py::_apply_orderset_sync` / `_apply_orderset_async` freeze routing intent before the
public override runs and re-seal its return through `_validate_post_orderset_result`
(`_ORDERSET_RESULT_POLICY`: model rows, unevaluated, unsliced, uncombined, same route).
`connection.py:1828` / `:1865` invoke the same public `OrderSet.apply_sync` / `apply_async` on a
sealed queryset and pass the return straight to `_finalize_queryset` with neither the snapshot nor
the re-seal.

Per the axis-6 rule, sibling behaviour justifies the investigation but not the verdict. The two
contract sources found both scope the rule to the list field:
`docs/spec-050-list_field_arguments-0_0_15.md` Edge cases ("A custom `OrderSet.apply_*` result
must SEAL to a lazy, unsliced, model-row-shaped, non-combined, same-model, same-route plain
queryset") is a list-field spec, and `_SealPolicy.require_unevaluated`'s prose reasons from "the
list field invoked that ordering method one step earlier and takes its window on what comes back".
The connection field also windows what comes back (Relay cursor slicing via
`ListConnection`), which is why this is not simply out of scope. **Ambiguous or newly proposed →
routed to Rio** through Worker 0. No fix, and no consolidation depends on it.

### D4 — `base_queryset`'s docstring states a distinction its body's reason does not support

querysets.py:257-260 asserts the seed is spelled "`manager.using(alias).all()` (never
`.all().using(alias)`): a sharded parent must seed its children on the SAME connection". The
stated reason justifies passing `using` at all, not the ORDER. Measured
(`docs/dry/temp-tests/dry-file-utils__querysets/probe_using_order.py`): for a default manager the
two spellings produce the same `_db`, the same SQL and the same queryset type — they are
indistinguishable at the seam this function occupies. Two package sites already write the
"never" spelling (`rest_framework/resolvers.py:1849` and `:1955`,
`getattr(instance, source).all().using(alias)`), so the prohibition is also unenforced and
unenforceable as stated.

Per AGENTS.md style ("Removed attribution carried the WHY → restate as one plain clause from the
code"; a wrong stated reason is worse than none, because the next author honors it), the clause
should either be dropped or replaced with the real reason if one exists for a non-default manager.
**Routes to:** `utils/querysets.py::base_queryset`. Needs a named owning card, or folding into the
`child-queryset-alias-inheritance` family item alongside D1.

### D5 (revision 1) — three message sites declare arms for defect codes they cannot produce, and one asserts the opposite as fact

Raised by Worker 2 (its C1/R2), independently re-derived here from source rather than taken on
trust; full derivation and the one place I qualify Worker 2's instrument are in `## Iterations`
I-R4.

The rule is stated at its owner: `_defect_message`'s docstring ("each message-building site
renders only the subset IT can reach") and, more sharply, `_validate_post_orderset_result`'s
inline comment ("an arm for a code that cannot arrive would be wording no rejection can ever
quote"). Three sites in this file break it:

| site | dead arm(s) | why the code cannot arrive |
|---|---|---|
| `utils/querysets.py::_raw_list_source_message` | `combined` | its only caller passes `_RAW_LIST_SOURCE_POLICY`, which leaves `reject_combined` at its `False` default |
| `utils/querysets.py::_prepared_visibility_source` | `routing`, `evaluated` | it calls `_seal_or_defect(queryset, model, None, policy)` with no `expected_routing`; none of the four policies that can reach it sets `require_unevaluated` |
| `utils/querysets.py::_visibility_result_error` | `routing`, `evaluated` | reached only from `_normalized_visibility_result`, same two facts |

Both `permissions.py` sites are correct, which is what shows the comparison can tell a right site
from a wrong one.

The defect proper — the D4-class half — is `_raw_list_source_message`'s docstring, which asserts
the false state as fact: *"Only the defects `_RAW_LIST_SOURCE_POLICY` can actually reach have
arms: `evaluated`, `sliced` and `projection` are switched off by that policy, and `routing` /
`alias` need an expectation this surface never states."* Its own enumeration omits `combined`,
which that policy also switches off, and the `combined` arm sits four lines below the sentence.
Same class as D4: a wrong stated reason is worse than none, because the next author honors it.

`fail_under = 100` cannot see any of this — every arm is a value in one dict literal, so a dead
arm is "covered" by the statement that builds the mapping.

**Routes to:** `utils/querysets.py::_raw_list_source_message` (the docstring), with
`_prepared_visibility_source` and `_visibility_result_error` named as the two sibling sites
carrying dead arms. Family `seal-defect-code-wording`. Needs a named owning card. Deleting a dead
arm changes no observable behavior (no rejection can quote it), but it is still not a file-item
edit.

## Pending execution

Three commands this run is not authorized to issue. None blocks the item; all are listed so the
gate carries them.

1. `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query -k prefetch --no-cov`
   — discharges D1's observable half: that a nested-connection prefetch child whose target
   `get_queryset` returns `.using("shard_b")` actually reads the other shard at fetch time.
   Needs Rio's separate authorization for the sharded mode; until then D1's cross-connection
   *consequence* stays `unverified` (the policy asymmetry itself is already
   `execution-verified` by the read-only probe).

2. `uv run pytest tests/utils/test_querysets.py tests/test_list_field.py tests/optimizer/test_extension.py --no-cov`
   — the one focused shared-tree run this item is authorized for was not spent, because the item
   landed no edit and every finding's proof is either a package-wide search or the two read-only
   probes already run. Listed so the gate can confirm the three suites that own this file's
   oracles are green at the cycle's end, and so F9's claim (that only tests read
   `is_async_queryset_adapter`) is exercised rather than only searched.

3. *(revision 1)* `uv run python docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py`
   — re-runs D5's reachability measurement at gate time. It is read-only and I already ran it
   against the shared tree during this revision (output reproduced in `## Iterations` I-R4), so
   it is listed not as a deferred proof but as a **regression witness**: if a family item deletes
   the three dead arms, this probe is what shows the state changed, and if one is added back the
   probe is what catches it. The gate should expect `sites with a mismatch: 4/6` today and should
   read I-R4 before treating a change in that number as a pass or a fail — one of the four rows
   (`_validate_post_orderset_result`, `missing: ['alias']`) is a modelling artifact, not a defect.

## Judgment

`utils/querysets.py` is, by a wide margin, the most DRY-disciplined file in the package: the
mechanisms it owns (`object.__getattribute__` state extraction, genuineness-by-identity, the
seal, Manager coercion, the definition-model read) each have exactly one definition package-wide,
several of its type inventories carry real principle-9 agreement gates, and its two colored
runners share every pure decision. The `_SealPolicy` record is a textbook instance of the worked
example's shape — declare the variation, share the meaning — and it already closed a documented
sync/async drift.

What the matrix did surface is mostly *outside* the file, which is the point of tracing a rule
rather than a module: three inline copies of the awaitable-disposal pair, two definitions of the
pre-sliced refusal, two of the related-object visibility re-check, and one member of the
child-alias family with no guard at all. Twelve families are named for Worker 0; four of them
(`awaitable-refusal-and-disposal`, `recomposition-illegal-source-rejection`,
`related-object-visibility-recheck`, `child-queryset-alias-inheritance`) carry live consolidation
or defect work and should be dispatched before the `utils/` folder item. The remaining eight are
expected to close as zero-edit or gate-only, but each needs the package-wide mechanism sweep a
file item is not allowed to substitute for.

Four defects routed, none fixed. No file-local rule was left unassigned, and no production edit
was owed or made.

## Implementation (Worker 1)

No tracked changes. Zero production edits, zero test edits, zero new tracked files — a file item
never owes a production edit, and every candidate found is named for its holding family instead.

Untracked scratch created (outside the tracked tree's concern, to be removed by Worker 0 after
verification, by explicit path):

- `docs/dry/temp-tests/dry-file-utils__querysets/probe_alias_policy.py`
- `docs/dry/temp-tests/dry-file-utils__querysets/probe_using_order.py`

Both are read-only against the live package and execute zero SQL. No disposable workspace was
needed: nothing in this item mutates source, so `scripts/prove_failability.py` was never run and
`<scratch>/dry-ws/` was never created. `uv run ruff format .` / `uv run ruff check --fix .` were
not run, because no tracked file was edited.

Item-scoped diff versus `ITEM_BASELINE=b2ec17eea042873767e2e30ebcdffa9e7e1ecaca` for the paths
this item touches: empty. `django_strawberry_framework/utils/querysets.py` is clean at HEAD, blob
`5907a1f72de42c71402886e7480ab559eb06a3af`, unchanged from dispatch.

Concurrent work observed and left alone. These paths are dirty but absent from the plan's
`## Cycle baseline` block, and they grew during the item (the last three appeared between the
first and last `git status` of this pass):

```text
 M examples/fakeshop/test_query/README.md
 M examples/fakeshop/test_query/test_library_api.py
 M examples/fakeshop/test_query/test_products_api.py
 M tests/forms/test_converter.py
 M tests/forms/test_inputs.py
 M tests/forms/test_resolvers.py
 M tests/forms/test_sets.py
```

None is a path this item touches, so per DRY.md "dirt elsewhere is concurrent work to leave
alone, not a stop" — reported to Worker 0 for reconciliation rather than acted on.

## Independent verification (Worker 2)

Written BEFORE reading `## Findings` / `## Defects` / `## Pending execution` / `## Judgment` /
`## Implementation (Worker 1)`. Everything under "My own trace" below was derived from the target,
the package, the tests and the installed Django/asgiref sources alone.

### Workspace and freshness, recorded before any verdict

Fresh copy taken after Worker 1's pass:
`<scratch>/dry-ws/w2-file-utils__querysets`.

- `uv run --project "$WS" --directory "$WS" python -c "import django_strawberry_framework as p;
  print(p.__file__)"` -> `$WS/django_strawberry_framework/__init__.py` (the workspace copy, not the
  shared checkout). `__version__` = `0.0.15`.
- Database `NAME` resolved from inside `$WS` with `config.settings` ->
  `$WS/examples/fakeshop/db.sqlite3`. No shared-tree database is opened by anything below.
- `git hash-object $WS/django_strawberry_framework/utils/querysets.py` =
  `5907a1f72de42c71402886e7480ab559eb06a3af`, byte-identical to the shared tree AND to
  `git ls-tree HEAD` at `e9e4d45c`. The target is unmodified at HEAD.

Item-scoped diff verified empty for myself:

```shell
git diff b2ec17eea042873767e2e30ebcdffa9e7e1ecaca -- django_strawberry_framework/   # no output
git ls-files --others --exclude-standard django_strawberry_framework/               # no output
```

The whole package is clean against HEAD; `## Owned changes` is empty and needs no row. Two paths
went dirty during my pass that are in neither the plan's `## Cycle baseline` list nor the
dispatch's addendum — `docs/spec-050-list_field_arguments-0_0_15.md` and
`docs/spec-050-list_field_arguments-0_0_15-rationale.md`. Neither is a path this item touches and
neither is package source; reported to Worker 0, not acted on.

### My own trace

**Inventory, counted not estimated.** `ast` over the target at the fingerprint above: 102
module-level functions, 7 classes (`SyncMisuseError`, `_AsyncQuerySetRows`, `_WalkState`,
`_GraphWalk`, `_UntrustedBoundValueError`, `_SealPolicy`, `_RoutingIntent`), 25 module-level
constants. The plan's `## Responsibility index` assigns 20 rows to this file (12 families + 8
file-local). Every symbol above maps onto one of those 20 rows except the ones I name under
"Where I differ".

**Rules I traced, with the change I posited and the authoritative-definition count.**

1. *Awaitable refusal and disposal.* Posited change: "a rejected awaitable must also be reported to
   the operation-state extension before it is disposed." Definitions that must move: 1 —
   `_dispose_sync_awaitable`. `_disposed_awaitable`, `reject_async_in_sync_context`,
   `reject_awaitable_sync_source`, `reject_residual_async_source` and the async runner's nested
   rejection all call it. Consumers outside the file (`auth/mutations.py`, `routers.py`,
   `list_field.py`, `relay.py`, `utils/permissions.py`, `mutations/permissions.py`,
   `connection.py`) are enforcement sites, not definitions. Second posited change: "the refusal
   message gains a common prefix" — count 4 (the four raise sites keep their own prose by a stated
   hot-path reason). Owner I would choose: unchanged, `_dispose_sync_awaitable`. Family
   `awaitable-refusal-and-disposal` is the right holder.

2. *Sealed-execution queryset.* Posited change: "a new untrusted shape (a consumer `__class_getitem__`
   on an expression) must fail closed." Definitions forced: 1 — `_seal_or_defect`, reached from
   exactly 5 call sites, all inside this file (`_sealed_prefetch_related_lookups`,
   `_validate_post_orderset_result`, `normalized_row_source`, `_prepared_visibility_source`,
   `_normalized_visibility_result`). Grepped the package: no second `sql.Query`-rebuilding body
   exists. Second posited change: "every framework invocation of the `get_queryset` hook must log."
   `rg "\.get_queryset\(" django_strawberry_framework/` returns 4 hits: two in this file (the two
   colored runners) and two that are not the hook (`optimizer/plans.py` prose,
   `filters/base.py::super().get_queryset(request)`, a django-filter API). Count 2 — the sync/async
   twin, which principle 5 keeps as two colored bodies sharing `_prepared_visibility_source` +
   `_normalized_visibility_result`. Owner: unchanged. Family `sealed-execution-queryset`.

3. *Seal defect-code wording.* Posited change: "add a `locked` defect code to the seal." Definitions
   forced: 1 (`_seal_or_defect`) plus an arm at every message site that can reach it. `_defect_message`
   has ONE definition and 6 call sites (4 here, 2 in `permissions.py`), each owning its own prose —
   which is the correct shape. **But the invariant those sites state is false at three of them**; see
   "Candidates I raise" C1. Family `seal-defect-code-wording`.

4. *Recomposition-illegal source rejection.* Posited change: "a new axis — reject a queryset carrying
   `select_for_update`." Definitions forced: 1 — a field on `_SealPolicy` plus its check in
   `_seal_or_defect`. All 7 policy constants are declared in this file and each is consumed at exactly
   one boundary (`_DEFAULT`, `_CASCADE` -> `permissions.py`, `_UNRECOMPOSED_CHILD` ->
   `optimizer/walker.py`, `_PREFETCH_CHILD` -> the inner seal here, `_LIST_ARGUMENT_VISIBILITY` ->
   `list_field.py`, `_ORDERSET_RESULT` and `_RAW_LIST_SOURCE` -> here). This is principle 1 executed
   exactly: declaration, not method. Owner: unchanged. Family
   `recomposition-illegal-source-rejection`.

5. *Related-object visibility recheck.* Posited change: "a hidden relation target must raise instead
   of returning `None`." Definitions forced: 2 —
   `utils/querysets.py::related_visibility_queryset_or_default` (model-keyed, sync-only, registry
   resolve, default-manager fallback, write-pipeline pinned) and
   `types/resolvers.py::_visible_related_object` (type-keyed, already-fetched instance, reads
   `related._state.db`, colored async branch, `afirst()`, no fallback). Same NAME, different
   contract. The read-side one is the second definition a seed naming only `utils/` would miss.
   Family `related-object-visibility-recheck` already lists `types/resolvers.py` among its files, so
   the assignment is right; the family item owes the disprove attempt.

6. *Field-value coercion.* Posited change: "a coercion failure must carry the offending literal."
   Definitions forced: 1 — `coerce_field_value_or_none`. `relay.py`, `filters/base.py`,
   `utils/write_values.py` call it; WHICH field is a per-caller decision, recorded in the docstring.
   I independently reach the same rejection.

7. *Sync-boundary recourse wording.* Posited change: "the write-flavor recourse must name the
   settings key that relaxes it." Definitions forced: 1 — `sync_pipeline_recourse`. The Relay
   recourse (`_RELAY_ASYNC_RECOURSE`, async IS possible) and the permission recourse (about
   `has_permission`/`check_permission`, not `get_queryset`) do not move. Rejection stands; the
   contract difference is stated at the owner.

8. *Child-queryset alias inheritance.* Posited change: "a sharded parent must seed every child on the
   parent's connection." Definitions forced: 1 — `base_queryset(..., using=)`. Enforcement sites:
   `permissions.py` (`using=state.alias`), `filters/sets.py` (`using=parent_db`),
   `optimizer/walker.py` — which calls `base_queryset(field.related_model)` with **no** `using=`.
   That is axis 6 (enforcement by omission) with a contract source: `_PREFETCH_CHILD_POLICY`'s
   `require_shared_alias` states the one-resolution-one-connection rule in this file's own prose.
   I reach `defect-routed` independently.

9. *Async-only queryset row adapter.* Posited change: "the adapter must also expose `__len__`."
   Definitions forced: 1 — `_AsyncQuerySetRows`. `is_async_only_iterable` is the one spelling of the
   async-only predicate (3 consumers: `list_field.py`, `resource_policy.py`, and the local
   `reject_async_iterable_in_sync_context`). **`is_async_queryset_adapter` has no production reader
   at all** — `rg` across the tree outside `docs/` finds it only at its definition and in
   `tests/test_list_field.py` (5 asserts) / `tests/optimizer/test_extension.py` (6 asserts). It is a
   test-only accessor, i.e. principle 11. I reached this independently; see C3.

10. *Post-set-apply result validation.* Posited change: "the post-OrderSet seal must also pin the
    schema's read-replica choice." Definitions forced: 1 — `_snapshot_routing_intent` /
    `_RoutingIntent` / `_validate_post_orderset_result`, a round-trip pair (freeze -> compare) both
    halves of which live here. Consumers: `list_field.py`, `connection.py`.

11. *One sync boundary.* Posited change: "the boundary must carry an operation lease across the
    worker." Definitions forced: 1 — `run_in_one_sync_boundary`. Enforcement sites named by the
    index: `schema.py`, `permissions.py`, `orders/sets.py`, `filters/sets.py`,
    `mutations/resolvers.py`, `auth/mutations.py`. I swept `rg "sync_to_async\("` over the package
    and found the raw call still spelled inline at `types/resolvers.py` (three
    `sync_to_async(getattr, thread_sensitive=True)` sites) and `testing/client.py` (two bare
    `sync_to_async(...)` calls; asgiref's default for `thread_sensitive` is `True`, verified in
    `.venv/.../asgiref/sync.py`, so they are behaviorally the same boundary). Both files ARE in the
    family's "files covered" list, so the assignment is right and the family item owes the verdict
    on whether these five compose or restate.

12. *Queryset seed and model read.* Posited change: "a registered type may override its seed
    manager." Definitions forced: 2 — `model_for` (the definition read) and `base_queryset` (the
    manager read), which `initial_queryset` composes. `relay.py` deliberately takes the raw manager
    instead, and that separation is recorded at `base_queryset`. Nine consumer files.

**Matrix, discharged against the real surface.**

1. *Cross-flavor policy mirroring.* Searched. The file's rules cross into `types/`, `forms/`,
   `rest_framework/`, `mutations/`, `filters/`, `orders/`, `optimizer/`. Every relation-visibility
   flavor composes by name (`write_values.py` -> `visible_related_object` / `visible_related_objects`
   / `pks_all_present`; `rest_framework/resolvers.py` -> `related_visibility_queryset`;
   `forms/resolvers.py` -> `visibility_scoped_related_queryset`). The one flavor that does NOT is
   `types/resolvers.py::_visible_related_object` (rule 5 above).
2. *Sync/async twins.* Searched. Three pairs: `apply_type_visibility_sync`/`_async`,
   `post_process_queryset_result_sync`/`_async`, `reject_awaitable_sync_source`/
   `reject_residual_async_source`. All three share their pure decisions
   (`_prepared_visibility_source` + `_normalized_visibility_result`; `prepared_resolver_source`;
   `_disposed_awaitable`) and keep only the await point and the exception class apart. I checked the
   async runner reaches every `_SealPolicy` axis the sync one does (both take `policy=` and thread it
   to both seals) — the drift the policy record was introduced to close is in fact closed.
3. *Derived rather than repeated knowledge.* Searched. `__django_strawberry_definition__.model` is
   spelled once, inside `model_for`; the only other textual hit is prose in `types/relay.py`.
   `_default_manager` reaches an executable site only in `base_queryset` and the one recorded
   exception in `relay.py`. `_meta.concrete_model` is read through `_concrete_or_none`.
4. *Inverse / round-trip pairs.* Searched, four found, all with both halves in this file:
   `_INERT_VALUE_TYPES` <-> `_BOUND_VALUE_NORMALIZERS`; `_PLAIN_CONTAINER_TYPES` <->
   `_reconstructed_value`'s container branches; `wrap_async_queryset_adapter` <->
   `unwrap_async_queryset_adapter`; `_snapshot_routing_intent` <-> `_validate_post_orderset_result`.
   The first two are the dangerous direction (prover-accepted / rebuilder-unhandled) and both carry a
   real agreement test in `tests/utils/test_querysets.py` (`assert set(samples) ==
   set(_PLAIN_CONTAINER_TYPES)`; `assert set(_INERT_VALUE_TYPES) - {bool} == {base for base, _ in
   _BOUND_VALUE_NORMALIZERS}`). I confirmed both assertions exist in the test body rather than
   trusting the docstrings that claim them.
5. *Contracts restated in another medium.* Searched. Media: `tests/utils/test_querysets.py` (5760
   lines, oracle), `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` (projection, cited 38 times
   from this file — by Decision number, which `START.md` warns is an ordinal citation, but the spec
   is archived and its decisions are numbered contract items, so the ordinal is the contract's own
   identifier, not a heading position), `docs/TREE.md` (projection), the module docstring
   (projection). No test was found reading its expectation FROM the owner it checks.
6. *Enforcement by omission.* Searched, three members enumerated and checked. (a) Every `get_queryset`
   invocation routes through the two runners — proven by the 4-hit grep above, not assumed.
   (b) Every seal call site passes a `_SealPolicy` — all 5 do. (c) Every `base_queryset` child seed
   pins its alias — `optimizer/walker.py` does not (rule 8). This axis is the one that produced a
   real gap, so it was not discharged by assertion.

### Candidates I raise

**C1 — three message sites in this file declare arms for defect codes their own call shape cannot
produce, while the rule says they must not.** Owner of the rule: `_defect_message`'s docstring
("each message-building site renders only the subset IT can reach") and
`_validate_post_orderset_result`'s inline statement ("Each site renders the subset it can reach; an
arm for a code that cannot arrive would be wording no rejection can ever quote").
`_raw_list_source_message`'s docstring goes further and asserts the fact: "Only the defects
`_RAW_LIST_SOURCE_POLICY` can actually reach have arms". That sentence is false.

I proved it rather than argued it. Probe (read-only, run in `$WS`, saved at
`docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py`): for each site, derive the
reachable code set from the `_SealPolicy` values that actually reach it plus whether the site passes
`expected_routing` / a non-`None` `required_alias`, then diff against the arms the site declares
(read out of the AST, so the probe cannot be fooled by prose). Result:

| site | reachable | dead arms |
|---|---|---|
| `querysets.py::_raw_list_source_message` | `type`, `table`, `untrusted` | `combined` |
| `querysets.py::_prepared_visibility_source` | + `sliced`, `combined`, `projection` | `routing`, `evaluated` |
| `querysets.py::_visibility_result_error` | + `sliced`, `combined`, `projection`, `alias` | `routing`, `evaluated` |
| `permissions.py::_root_error_renderer` | `type`, `table`, `untrusted`, `sliced`, `combined` | none |
| `permissions.py::_edge_error_renderer` | + `alias` | none |

`_RAW_LIST_SOURCE_POLICY` leaves `reject_combined` at its `False` default, so the `combined` arm
cannot fire; `_prepared_visibility_source` never passes `expected_routing` and no policy reaching it
sets `require_unevaluated`, so `routing` and `evaluated` cannot fire there or at
`_visibility_result_error`. `_validate_post_orderset_result`'s one absent arm (`alias`) is the
opposite case and is argued correctly in its own comment — the seal reaches the alias check only
after `routing` admitted `candidate_db == intent.db`, and `_snapshot_routing_intent` pins
`effective_alias` to that same value.

Negative control inside the probe: it asserts `_RAW_LIST_SOURCE_POLICY` does NOT reach `sliced` /
`projection` / `combined`, so a reachability model that fell open (returning every code) fails the
control instead of printing a clean table. Both `permissions.py` sites coming back `OK` is the
positive control: the comparison can distinguish a correct site from an incorrect one.

Why this matters beyond tidiness: the invariant is stated at the owner and enforced by nobody, and
`fail_under = 100` cannot see it — every arm is a value in one dict literal, so the dead arms are
"covered" by the statement that builds the mapping. This is the shape `DRY.md` principle 9 exists
for. **Routing: family `seal-defect-code-wording`** (which already lists `utils/querysets.py` and
`permissions.py`, the two files involved). It is not a file-item edit and I do not ask for one.

**C2 — `_prefetch_relation_target_or_none` is recorded file-local, but a second definition of the
`LOOKUP_SEP` path walk exists.** `utils/relations.py::classify_path` (with
`_resolve_segment_field` / `_lenient_traverses_to_many`) is the package's authoritative
segment-by-segment walk through `Model._meta.get_field`; `connection.py`, `optimizer/plans.py` and
`utils/permissions.py` each run one too. `_prefetch_relation_target_or_none` is a fourth. The
contract difference is real and I would expect the rejection to survive — `classify_path` resolves
DECLARED field-map names and RAISES `PathResolutionError`, while the prefetch resolver must also
accept the `<model>_set` reverse-accessor spelling Django's prefetch traversal reaches (verified
against `_reverse_relation_by_accessor_or_none`, which scans `get_accessor_name()` over
`_meta.get_fields()`) and must fail OPEN with `None` so it never fail-closes a path Django supports.
But "file-local with no second site" is not the right record for it. It is a REJECTED candidate and
owes a contract difference plus a reconsideration trigger (my proposal for the trigger: *if
`classify_path` ever grows an accessor-name fallback or a non-raising mode, the two become one
rule*). **Routing: either a new family `orm-lookup-path-resolution` owned by
`utils/relations.py::classify_path`, or a rejection recorded at
`_prefetch_relation_target_or_none`.**

**C3 — `is_async_queryset_adapter` has no production reader.** Definition here; 11 assertions across
`tests/test_list_field.py` and `tests/optimizer/test_extension.py`; zero package callers. Under
principle 11 this is an indirection whose only job is being checked. Note the counter-argument
before deleting: it is the only spelling of "is this the async-only adapter" that a test can use
WITHOUT importing the private `_AsyncQuerySetRows`, so removing it pushes 11 oracles onto a private
name. Principle 11's own carve-out ("keep a one-caller wrapper only for a concrete responsibility it
carries: a boundary name callers depend on") arguably covers that. Either outcome is defensible; what
is not defensible is leaving it unrecorded. **Routing: family `async-only-queryset-row-adapter`,
which owns `_AsyncQuerySetRows`.**

**C4 — `_safe_class_name` is recorded file-local, but the package has two definitions of it.**
`exceptions.py::_safe_class_name` and `utils/querysets.py::_safe_class_name` are two independently
maintained bodies under one name. The contract difference is recorded at BOTH owners (exceptions'
docstring names the querysets variant as "a stricter local variant whose non-string fallback never
dispatches the name object at all"; the querysets docstring names exceptions' as the shared one),
which is exactly what `DRY.md` "Rejected candidates" asks for as a durable home — so the reasoning
is already right and already written. The index row is what is wrong: `file-local` claims "no second
site", and the row's "files covered" names only `utils/querysets.py`. It should read as a rejection
covering `utils/querysets.py` and `exceptions.py`. Missing from both docstrings: a reconsideration
trigger (proposal: *if `exceptions._safe_class_name` ever stops calling `_safe_arg_repr` on a
non-string name, the two collapse to one*). **Routing: a rejection row, files covered
`utils/querysets.py` + `exceptions.py`.**

C2 and C4 are the same defect of bookkeeping, not of reasoning: "file-local" is defined by `DRY.md`
as "no second site after the matrix", and both rows have one. Neither changes what the cycle should
DO with the rule; both change what a later run reading `## Outcomes` would believe about it.

### Things I checked and found sound

- The item-scoped diff is empty and I verified it myself at the ITEM_BASELINE, not from the
  dispatch's word.
- `_seal_or_defect` really is the single sealing primitive: 1 definition, 5 call sites, no second
  `sql.Query`-rebuilding body anywhere in the package.
- The two round-trip inventory gates (`_PLAIN_CONTAINER_TYPES`, `_INERT_VALUE_TYPES` /
  `_BOUND_VALUE_NORMALIZERS`) are real executable assertions, not docstring claims. Their negative
  control is structural: each asserts SET EQUALITY, so a member added to one inventory and not the
  other fails the assertion in both directions. A one-sided `<=` would have passed a
  prover-accepted / rebuilder-unhandled gap, which is the direction that fails the seal closed with
  no indication the inventories disagree; the test does not have that hole.
- No oracle in `tests/utils/test_querysets.py` was rewritten to read its expectation from the owner
  it checks.
- AGENTS.md prose rules over the (empty) diff: nothing to check in production source. The two
  untracked probe scripts Worker 1 left and the one I added are per-cycle scratch under
  `docs/dry/temp-tests/`, which the standing docs exempt.

### Commands I ran

```shell
uv run --project "$WS" --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --project "$WS" --directory "$WS" python -c "<django.setup(); print settings.DATABASES['default']['NAME']>"
uv run --project "$WS" --directory "$WS" python probe_defect_arms.py
git diff b2ec17eea042873767e2e30ebcdffa9e7e1ecaca -- django_strawberry_framework/
git hash-object django_strawberry_framework/utils/querysets.py
```

No source was mutated anywhere. No permanent test was run in the shared tree (nothing in this file
item needed one; the one claim I wanted execution for is answered by the read-only probe above).
`FAKESHOP_SHARDED=1` and the Postgres cells stay `unverified`.

### Reconciliation against Worker 1's findings (read after the trace above was on disk)

Worker 1's pass is strong and, on most axes, reaches further than mine: it found the inline
disposal copies in `auth/mutations.py` and `routers.py` (F1), the second pre-sliced refusal in
`connection.py::_guard_source_not_pre_sliced` (F4), `write_transaction.py::canonical_pk` as the
rejected second pk basis (F6), the retired `allow_sliced` keyword still live in the glossary and
in `spec-034` (D2), and the `base_queryset` `using`-order clause whose stated reason its own body
does not support (D4) — all of which my trace missed. Where we overlap we agree: F9 is my C3, F11
is my rule 11, F5 is my rule 5, F8/D1 is my rule 8, and the definition counts match on every
family I counted independently (1 for `_seal_or_defect`, 1 for `_dispose_sync_awaitable`, 1 for
`run_in_one_sync_boundary`, 1 for `model_for`, 2 for the related-object re-check, 2 for the
pre-sliced refusal). Owner choices and family granularity: no disagreement.

Three things do not survive the reconciliation.

**R1 — F12 records `_prefetch_relation_target_or_none` as file-local "no second site"; a mechanism
sweep falsifies that.** This is my C2, and reading F12 makes it sharper rather than softer, because
the challenge F12 posits for that row ("a `GenericForeignKey` alias must resolve rather than fail
open") exercises only this function's own fail-open tail — the "one convenient change" DRY.md's
change-challenge section warns against. Posit instead the change that exercises the rule's real
variation axis, *"a `pk` segment must resolve to the model's pk field at every hop"*, and count:

| body | separator | `pk` resolution | failure mode |
|---|---|---|---|
| `utils/relations.py::classify_path` (+ `_resolve_segment_field`) | `LOOKUP_SEP` | yes | raises `PathResolutionError` |
| `utils/relations.py::_lenient_traverses_to_many` | `LOOKUP_SEP` | no | `False` |
| `connection.py` (keyset terminal-column resolver) | literal `"__"` | yes, via `_meta.pk.name` | `None` |
| `optimizer/plans.py` (loaded-column probe) | literal `"__"` | no | `False` |
| `utils/querysets.py::_prefetch_relation_target_or_none` | `LOOKUP_SEP` | no | `None` |

Five independently maintained bodies of "walk a `__`-separated ORM path through
`Model._meta.get_field`, following `related_model` at each hop"; two of them do not even spell the
separator through `LOOKUP_SEP`. DRY.md's family rule is explicit that the sweep is for the rule's
MECHANISM, not the target's neighbours, and that the second definition is routinely in a module no
seed named — `utils/relations.py` is exactly that module here. The contract difference is real
(raise-vs-fail-open, and only the prefetch resolver accepts the `<model>_set` accessor spelling
Django's prefetch traversal reaches), so I expect this to end as a REJECTION rather than a
consolidation. But `DRY.md` gives a rejection a durable home, a contract difference and a
reconsideration trigger; it does not permit recording it as "file-local, no second site", which is
the one label that guarantees no later item looks again. A file item that ticks with this row as
written leaves the rule unhomed, and `utils/relations.py`'s own file item will see only its side
and reach the same local verdict.

**Owed:** either a new family row `orm-lookup-path-resolution`, owner
`utils/relations.py::classify_path`, files covered `utils/relations.py`, `connection.py`,
`optimizer/plans.py`, `utils/querysets.py` — or an F12 row rewritten as a rejection carrying the
contract difference above and a trigger (proposed: *if `classify_path` grows an accessor-name
fallback or a non-raising mode, the two collapse into one rule*).

**R2 — F3 designs a gate on a premise that is already false, and the docstring asserting it is a
D4-class defect nobody recorded.** F3 quotes the rule ("Every message-building site renders only
the subset IT can reach") and concludes `gate-only`: owner single, no gate. It never checks whether
the rule currently HOLDS. It does not, at three sites inside this very file. The probe under
"Candidates I raise" C1 above measures it: `_raw_list_source_message` declares a `combined` arm its
policy cannot produce (`_RAW_LIST_SOURCE_POLICY` leaves `reject_combined` at its `False` default),
and `_prepared_visibility_source` / `_visibility_result_error` each declare `routing` and
`evaluated` arms their call shape cannot produce (neither passes `expected_routing`; no policy
reaching them sets `require_unevaluated`). Both `permissions.py` sites are correct, which is the
positive control that the comparison can tell a right site from a wrong one.

Worse than the dead arms: `_raw_list_source_message`'s docstring states the false half as a fact —
"Only the defects `_RAW_LIST_SOURCE_POLICY` can actually reach have arms: `evaluated`, `sliced` and
`projection` are switched off by that policy, and `routing` / `alias` need an expectation this
surface never states." Its own enumeration omits `combined`, which is also switched off, and the
arm for it sits four lines below. That is precisely the class Worker 1 recorded as D4 for
`base_queryset` ("a wrong stated reason is worse than none, because the next author honors it") and
it belongs under `## Defects` with the same treatment, not only inside a finding that reads as if
the invariant held.

This is not cosmetic for the family item. F3's "justified population for a gate" is "the six
`_defect_message` call sites, and the codes each reachable `_SealPolicy` can actually emit". A gate
built from that population and run against today's tree goes red at three sites on its first run —
so whoever writes it will either discover R2 the hard way, or, the likelier failure, relax the gate
until the current state passes and thereby encode the opposite of the rule. `fail_under = 100`
cannot warn them: every arm is a value in one dict literal, so the dead arms are "covered" by the
statement that builds the mapping.

**Owed:** a `## Defects` row (owner `utils/querysets.py::_raw_list_source_message`, with the two
sibling sites named), and F3 restated so its gate population is described against the tree as it
is, not as the prose claims it is.

**R3 — challenge C3's rule lands in no family row and no file-local row.** Every other challenge in
the `### Challenges` table terminates somewhere: C1/C2 in `queryset-seed-and-model-read`, C4/C16 in
`field-value-coercion`, C5 in F1, C6 in F7, C7 in F11, C8 in F10, C9/C10/C11/C13 in F2, C12 in F3,
C14 in F4, C15 in F5, C17 in F8, C18 in `post-set-apply-result-validation`. C3 — "coerce a
`Manager` to a `QuerySet`", verdict "independent", 1 definition (`_coerced_manager_queryset`) — is
named in no `## Responsibility index` row and in no F12 row. The rule is not a minor one: it is a
visibility-bypass boundary whose own docstring says a degraded `Manager.all()` "must NEVER be
allowed to fall into the plain-iterable (`is_queryset=False`) bypass", it has a second entry point
(`normalize_query_source` for resolver returns, `_normalized_visibility_result` for hook returns),
and its consumers span `list_field.py`, `connection.py` and `optimizer/extension.py`. Under DRY.md
a file item discharges only when every rule is assigned OR recorded file-local; this one is
neither.

**Owed:** an F12 row for the Manager-coercion rule (with the challenge that proved it file-local),
or an index row naming the family that holds it.

Non-blocking, recorded so they are not re-derived:

- `## System trace` states "99 module-level symbols". Measured at the pinned blob: 102 top-level
  functions, 7 classes, 25 module-level constants (134); `funcs + classes` is 109 and
  `dir()` members whose `__module__` is this module is 116. No instrument yields 99. For an
  inventory backstop the inventory count is load-bearing — an undercount is exactly how a rule goes
  unassigned — so the figure should name its instrument or be corrected.
- F12's `_safe_class_name` row is sound on the substance (it names `exceptions.py` and gives the
  contract difference, and both docstrings already carry the separation at their own owners), but
  it carries no reconsideration trigger. DRY.md asks a rejection for one; "file-local" is the label
  that lets it skip the requirement. Proposed trigger: *if `exceptions._safe_class_name` stops
  routing a non-string name through `_safe_arg_repr`, the two collapse into one rule.*

### Verdict

`Status: revision-needed`. The plan item `- [ ] File \`utils/querysets.py\`` is NOT ticked.

The item-scoped diff is empty and correctly so — a file item owes no production edit and I demand
none. Nothing in R1/R2/R3 asks for one. What is owed is the file item's actual deliverable: an
assignment for every rule the file defines or enforces. Three rules are mis-assigned or
unassigned (R1, R3) or assigned on a false premise (R2), and each is the kind that dies unhomed
once the checkbox is ticked, because `DRY.md` reopens a verified item only when a freshness
fingerprint changes and nothing here will change one.

Everything else verified: matrix discharged against the real surface on all six axes with the one
gap-producing axis (6) enumerated member-by-member rather than asserted; definition counts
confirmed independently; site roles correct and no oracle rewritten to read from its owner; the
two round-trip inventory gates are real executable set-equality assertions; both `## Pending
execution` entries carry an exact command and what it discharges; F8's coupling to D1 is marked;
every finding carries blob-id freshness fingerprints and all of them still match the tree (I
re-hashed `utils/querysets.py`, `permissions.py`, `connection.py`, `types/resolvers.py`,
`optimizer/walker.py`, `list_field.py` and `tests/utils/test_querysets.py`). D1's negative control
is genuine: `probe_alias_policy.py` shows the same input ACCEPTED under one policy and REJECTED
under another, so the instrument can distinguish the two and did not merely print a pass.

Scratch left in place for Worker 0 to remove by explicit path after verification:
`docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py`.

### HEAD moved during this verification; no finding went stale

A concurrent session committed `5c62515a test(forms): move the form-mutation verdicts a request
can show to the live tier` between the start and the end of this pass, so HEAD advanced from
`e9e4d45c` (the plan's cycle-entry HEAD) to `5c62515a`. Re-hashed every file any finding
fingerprints, after the move:

```text
django_strawberry_framework/utils/querysets.py    5907a1f72de42c71402886e7480ab559eb06a3af
django_strawberry_framework/permissions.py        9e0236b3bbcfa9320a5d4e18e34b35c27adf233e
django_strawberry_framework/connection.py         93e998f2c7ea1d7f18607a6e37e394466ac75ad4
django_strawberry_framework/types/resolvers.py    fc077f38a1f10db2a447c11b11bea1e82bcbb362
django_strawberry_framework/optimizer/walker.py   054207017c3435ed1f6b7891683fed112c807d11
django_strawberry_framework/list_field.py         f357eded3d96fcffe17e6fd84bceb8cd12af98d5
django_strawberry_framework/auth/mutations.py     dbe64995b87240b87a1d5119f46cc42c7cab646f
django_strawberry_framework/routers.py            a18c5001471d4a937bb81d2ff41a2e442e7d2dad
tests/utils/test_querysets.py                     c9a84d53f3e74e3f5274a6b5096ce1a17ceef292
```

All nine match the values Worker 1 recorded, so every finding is still fresh and the revision
asked for above is the only thing owed. `django_strawberry_framework/` remains clean against the
new HEAD, and `ITEM_BASELINE=b2ec17ee` still produces an empty package diff. The plan's
`## Cycle baseline` dirty list has also drifted further (`AGENTS.md`, `GOAL.md`,
`docs/feedback.md`, `examples/fakeshop/tests/test_export_schema.py`,
`examples/fakeshop/tests/test_inspect_django_type.py` are now dirty; the `tests/forms/*` and
`examples/fakeshop/test_query/*` entries Worker 1 listed have landed in `5c62515a`). None is a
path this item touches; Worker 0 owns the reconciliation.

## Iterations

### Revision pass 1 — Worker 1, after Worker 2's `revision-needed`

Worker 2 raised three blocking candidates (R1, R2, R3) and two non-blocking points. I verified
each against source myself rather than accepting the report: DRY.md makes a round's self-reported
finding a claim to re-derive, and that cuts both ways. **All three blocking candidates are
upheld.** One of them (R3) turned out to be narrower than the real problem, which is recorded as
I-R5. I qualify one detail of Worker 2's instrument (I-R4) and correct one detail of its site
list (I-R2); neither changes its verdict.

Nothing above was rewritten. Two `## Findings` rows and one `## Findings` paragraph are marked
SUPERSEDED in place and replaced here; two figures in `## System trace` were corrected, with the
old figure quoted so the correction is legible. No production edit: a file item owes none, and
Worker 2 explicitly demanded none.

#### I-R1 (upholds R1, part 1) — `_prefetch_relation_target_or_none` is a REJECTION, not a file-local rule

Worker 2 is right and the mistake was mine in a way worth naming: the challenge I posited for that
F12 row — *"a `GenericForeignKey` alias must resolve rather than fail open"* — could only ever
return 1, because it exercises that function's own fail-open tail rather than the rule's shared
mechanism. DRY.md warns about exactly this ("Exercise the rule's variation axes, not one
convenient change"), and I wrote a convenient one.

Mechanism swept package-wide: *split an ORM lookup path and walk each segment through
`Model._meta.get_field`, following the relation at each hop*. Five independently maintained
bodies, each re-read at the current tree:

| body | separator | `pk` segment | failure mode | accessor-name fallback |
|---|---|---|---|---|
| `utils/relations.py::classify_path` (+ `_resolve_segment_field`) | `LOOKUP_SEP` | resolved to `_meta.pk` | raises `PathResolutionError` | no |
| `utils/relations.py::_lenient_traverses_to_many` | `LOOKUP_SEP` | not resolved | `False` | no |
| `connection.py::_resolve_order_path_field` | literal `"__"` | resolved via `current._meta.pk.name` | `None` | no |
| `optimizer/plans.py::_select_path_traversable` | literal `"__"` | not resolved | `False` | no |
| `utils/querysets.py::_prefetch_relation_target_or_none` | `LOOKUP_SEP` | not resolved | `None` | **yes** (`_reverse_relation_by_accessor_or_none`) |

Re-run challenges, on the rule's real variation axes:

- *"a `pk` segment must resolve to the pk field at every hop"* → **3 definitions move** (rows 2, 4,
  5 gain it), and rows 1 and 3 already implement it two different ways (`_meta.pk` vs
  `_meta.pk.name`). Worker 2's count confirmed.
- *"the separator stops being two underscores"* → **2 definitions** break silently (rows 3 and 4
  hardcode `"__"` while `LOOKUP_SEP` exists and is imported four modules over).
- *"a forward `GenericForeignKey` segment must be refused rather than silently traversed"* → **5**,
  because all five currently answer it differently.

**Verdict: REJECTED, not consolidated** — and I expect that to survive a family item. The contract
difference is real and load-bearing in both directions: `classify_path` resolves DECLARED
field-map names and RAISES, because a filter/order path that does not resolve is a schema-author
error the package must name; `_prefetch_relation_target_or_none` must additionally accept the
default `<model>_set` reverse-accessor spelling that Django's own prefetch traversal reaches by
attribute access, and must fail OPEN with `None` so it never fail-closes a prefetch path Django
supports. Merging them would either make the prefetch guard reject legal Django paths or make the
filter/order classifier silently accept unresolvable ones.

**Reconsideration trigger** (adopting Worker 2's, which is the right one): *if
`utils/relations.py::classify_path` grows an accessor-name fallback or a non-raising mode, the
two collapse into one rule.* Second trigger of my own: *if either literal-`"__"` body is ever
changed to import `LOOKUP_SEP`, the separator axis stops distinguishing them and the population
should be re-counted.*

**Durable home for the rejection:** `utils/querysets.py::_prefetch_relation_target_or_none`, one
plain docstring clause naming `classify_path` as the strict sibling and why this one fails open.
Not written by this item — a file item lands no edit; the family item owes it.

#### I-R2 (upholds R1, part 2) — new family, with one correction to Worker 2's site list

I take Worker 2's first routing option rather than its second, because a rejection recorded only
at `utils/querysets.py` still leaves `utils/relations.py`'s own file item free to reach the same
local verdict from its side — which is precisely the failure Worker 2 names.

**Family: `orm-lookup-path-resolution`**, owner `utils/relations.py::classify_path`, files covered
`utils/relations.py`, `connection.py`, `optimizer/plans.py`, `utils/querysets.py`. Status `open`.

Correction to Worker 2's C2, which lists `utils/permissions.py` as a member: it is not one. Its
walk (`utils/permissions.py` #"hops = source_path.split(LOOKUP_SEP)") matches path segments against
DECLARED `RelatedFilter` / `RelatedOrder` attributes and never touches `Model._meta.get_field`, so
it shares the separator but not the mechanism. Worker 2's own R1 table drops it, so the two halves
of its write-up disagree; the R1 table is the accurate one. Recorded so the family item does not
sweep a fifth module in and then have to argue it back out.

Also excluded, with the reason, so it is not re-derived: `filters/base.py`
#"segments = field_name.split(\"__\")" walks the REGISTRY graph
(`DjangoTypeDefinition.related_target_for`), resolving `pk` against `_meta.pk.name` but never
calling `get_field`. Adjacent, not a member. If the family item decides the rule is "resolve a
lookup path" rather than "resolve it through `_meta`", that judgement pulls this site in and the
count rises to 6 — worth stating, because the boundary of the population is the one thing a
rejection of this shape can get wrong.

#### I-R3 (upholds R3) — the Manager-coercion rule now has a record

Worker 2 is right that challenge C3 terminated nowhere. Adding it to the file-local table, with
challenges that exercise the rule's own axes rather than a convenient one:

| Rule | Owner | Challenges posited | Definitions |
|---|---|---|---|
| A `Manager` entering the visibility boundary is coerced to a `QuerySet` exactly once, preserving its explicit routing, and may NEVER fall into the plain-iterable (`is_queryset=False`) bypass | `utils/querysets.py::_coerced_manager_queryset`, with `normalize_query_source` owning the is-it-a-queryset verdict | (a) "a Manager whose `.all()` returns an async iterable must fail closed"; (b) "the coercion must preserve `_hints`, not only `_db`"; (c) "a Manager that self-routes an unrouted `.all()` must fail closed" (already the rule) | **1** for each challenge |

Population evidence: `models.Manager` appears at exactly three lines package-wide, all in this
file (querysets.py:307 the `normalize_query_source` test, :3479 the coercer's signature, :3818 the
hook-result arm). No other module coerces a Manager or decides "this is a plain iterable"; both
collection flavors reach the verdict through `prepared_resolver_source`. Two entry points, one
body — the boundary shape, not a duplication. **File-local.**

Worth flagging for the folder item rather than hiding in a table: this is the rule whose failure
mode is a *visibility bypass* (a degraded `Manager.all()` mistaken for the deliberate
plain-iterable escape skips `get_queryset` entirely). It is file-local today; it is also the rule
in this file with the least margin, so `utils/` integration should confirm no future surface grows
its own Manager test.

#### I-R4 (upholds R2, with one qualification) — F3's gate population, restated against the tree

I re-derived Worker 2's result from source before accepting it, because its probe's reachability
model is **asserted in a hand-written `SITES` table, not measured** — the probe reads the declared
arms from the AST (which is sound) but hardcodes which policies and which `expected_routing` reach
each site. The two facts that table rests on are checkable, and I checked them:

- `expected_routing` is passed at exactly **one** `_seal_or_defect` call site in the package —
  `_validate_post_orderset_result` (querysets.py:2984). The other four calls
  (querysets.py:2537, :3396, :3703, :3820) pass none. So `routing` is unreachable everywhere else.
- The complete set of `policy=` values that can reach `_prepared_visibility_source` /
  `_normalized_visibility_result` is four: `_DEFAULT_SEAL_POLICY` (the default),
  `_CASCADE_SEAL_POLICY` (`permissions.py:623`, `:705`), `_UNRECOMPOSED_CHILD_POLICY`
  (`optimizer/walker.py:458`), `_LIST_ARGUMENT_VISIBILITY_POLICY` (`list_field.py:1080`, `:1133`).
  None sets `require_unevaluated`; the only policy that does, `_ORDERSET_RESULT_POLICY`, reaches
  `_seal_or_defect` solely through `_validate_post_orderset_result`. So `evaluated` is unreachable
  at both sites.

With those two facts verified the `SITES` table is sound, and I re-ran the probe against the
**shared tree** (read-only, no SQL, no mutation — it imports the module and parses two files):

```text
querysets._validate_post_orderset_result: MISMATCH   dead: []                  missing: ['alias']
querysets._raw_list_source_message:       MISMATCH   dead: ['combined']        missing: []
querysets._prepared_visibility_source:    MISMATCH   dead: ['routing','evaluated']
querysets._visibility_result_error:       MISMATCH   dead: ['routing','evaluated']
permissions._root_error_renderer:         OK
permissions._edge_error_renderer:         OK
sites with a mismatch: 4/6
negative control: raw-list policy reaches ['type', 'table', 'untrusted']
```

**Qualification.** The probe reports 4 mismatches, not 3. The fourth
(`_validate_post_orderset_result`, `missing: ['alias']`) is **not** a defect: that site's own
comment argues the omission at length, and correctly — the seal reaches the alias check only after
`routing` admitted `candidate_db == intent.db`, and `_snapshot_routing_intent` pins
`effective_alias` to that same value, so an `alias` defect cannot arrive there. The probe's model
sets `required_alias_possible=True` for that site and therefore disagrees with a documented
subsumption. Worker 2's prose gets this right and its table reports dead arms only, so its
conclusion stands — but the *instrument* has a known false positive, and anyone building the real
gate from it must encode the subsumption or the gate will demand a wrong arm. That is exactly the
"relax the gate until the current state passes" failure Worker 2 warns about, arriving from the
other direction.

**F3's gate population, restated.** Not "the six `_defect_message` call sites and the codes each
reachable `_SealPolicy` can emit" — that population, run today, goes red at four sites, three
legitimately (D5) and one spuriously. The correct population for a family item to gate is:

> for each `_defect_message` call site, the code set reachable at that site, computed from
> (i) the policies that reach it, (ii) whether it passes `expected_routing`, (iii) whether its
> `required_alias` can be non-`None`, **and (iv) the documented subsumptions a site declares** —
> of which exactly one exists today, `routing` subsuming `alias` at
> `_validate_post_orderset_result`. A subsumption must be declared at the site in a form the gate
> reads, not in prose, or it is indistinguishable from a missing arm.

That fourth term is the part F3 did not have, and it is what makes the gate buildable rather than
merely desirable. It also raises the gate's cost estimate: a declared-subsumption mechanism is a
small production change at the sites, so this is no longer a pure `gate-only` finding — it is
gate-plus-declaration. Family `seal-defect-code-wording` inherits that.

The false-invariant docstring is recorded separately as **D5** under `## Defects`.

#### I-R5 (new, found by the re-derivation R3 prompted) — `SyncMisuseError` was also unassigned

Worker 2's R3 found one unassigned rule by walking the challenge table. I did not want to fix one
gap and leave the class of gap intact, so I re-derived the assignment name-by-name over the full
134-name AST enumeration (the same enumeration that corrected the `## System trace` figure). That
found a **second** unassigned rule that neither pass had noticed: `SyncMisuseError` itself —
name 1 of 134, the first symbol in the file.

| Rule | Owner | Challenge posited | Definitions |
|---|---|---|---|
| A sync-boundary misuse raises a marker that multiply-inherits the package base AND the foreign base a consumer's existing `except` already names, so neither catch stops matching | `utils/querysets.py::SyncMisuseError` | "a fourth catch shape must keep matching" → its own bases; "every package error must also match a wire error" → `exceptions.py`'s bases, not this class | **1** |

Sibling declarations of the same PATTERN, swept and excluded with the reason:
`list_field.py::ListArgumentError` and `resource_policy.py::ResourceLimitExceeded` both pair a
package base with `GraphQLError` for the same structural reason. They are three declarations, not
three definitions: a change to the pattern ("every package error must also inherit X") moves the
base classes in `exceptions.py`, and a change to any one marker's identity moves only that marker.
**File-local**, with the population recorded so `exceptions.py`'s file item does not re-derive it.

Every other name of the 134 resolves to an existing finding or family. The two rows I-R3 and I-R5
add are the complete remainder; the re-derivation is what lets me say "complete" rather than
"none that I noticed", which is the difference DRY.md's inventory backstop is actually asking for.

#### I-R6 (upholds the non-blocking point) — `_safe_class_name` is a rejection with a trigger

Worker 2 is right that the substance was sound and the label was not: `file-local` is defined as
"no second site after the matrix", and `exceptions.py::_safe_class_name` is a second site. The
reasoning was already correct and already written at both owners, which is what DRY.md asks a
rejection for; what was missing is the label, the covered-files list, and a trigger.

**REJECTED.** Contract difference: `exceptions.py::_safe_class_name` renders a non-string
`__name__` through `_safe_arg_repr`, which is the right trade for an ordinary configuration
message; `utils/querysets.py::_safe_class_name` degrades to `_safe_type_name` instead, because a
`repr` of the name object would dispatch a hostile dunder on the very object the sealed boundary
is rejecting. Files covered: `utils/querysets.py`, `exceptions.py`. **Trigger** (adopting Worker
2's): *if `exceptions._safe_class_name` stops routing a non-string name through `_safe_arg_repr`,
the two collapse into one rule.*

#### Where I disagree with Worker 2

Only on two details, neither affecting its verdict, both recorded above: `utils/permissions.py` is
not a member of the lookup-path family (I-R2), and its defect-arm probe carries a known false
positive at `_validate_post_orderset_result` (I-R4). I also think R3 was under-scoped — the gap it
found was a symptom of an enumeration I never did, not of one challenge losing its footing — which
is why I-R5 exists.

On everything else its reading is correct, and on two points it is sharper than mine: F12's
`GenericForeignKey` challenge really was the "one convenient change" DRY.md warns about, and F3
really did design a gate without checking whether the invariant it gates currently holds. Both are
the same mistake in different clothes — asserting a property of the tree from prose at the owner
instead of measuring it — which is the failure mode this whole method exists to catch, so it is
fitting that it took a second reader.

#### Freshness, re-recorded at the current tree

HEAD moved `e9e4d45c` → `5c62515a` during Worker 2's pass. Re-hashed at the start of this
revision; every file any finding fingerprints is unchanged, so no finding went stale and none is
reopened on freshness grounds:

```text
django_strawberry_framework/utils/querysets.py    5907a1f72de42c71402886e7480ab559eb06a3af
django_strawberry_framework/permissions.py        9e0236b3bbcfa9320a5d4e18e34b35c27adf233e
django_strawberry_framework/connection.py         93e998f2c7ea1d7f18607a6e37e394466ac75ad4
django_strawberry_framework/optimizer/walker.py   054207017c3435ed1f6b7891683fed112c807d11
django_strawberry_framework/list_field.py         f357eded3d96fcffe17e6fd84bceb8cd12af98d5
django_strawberry_framework/types/resolvers.py    fc077f38a1f10db2a447c11b11bea1e82bcbb362
django_strawberry_framework/auth/mutations.py     dbe64995b87240b87a1d5119f46cc42c7cab646f
django_strawberry_framework/routers.py            a18c5001471d4a937bb81d2ff41a2e442e7d2dad
tests/utils/test_querysets.py                     c9a84d53f3e74e3f5274a6b5096ce1a17ceef292
```

Newly fingerprinted by this revision (I-R1, I-R2, I-R5), recorded against the current tree:

```text
django_strawberry_framework/utils/relations.py    7662b0bb669c4dfba4a437f3b8f309357f718dca
django_strawberry_framework/optimizer/plans.py    cce985319c8833f3660653327d3003f1f03655a5
django_strawberry_framework/utils/permissions.py  9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec
django_strawberry_framework/exceptions.py         e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b
django_strawberry_framework/filters/base.py       ba52351c284425336262ae6c2b82b262f6586fc0
django_strawberry_framework/resource_policy.py    9205124f41814dbda5a7df0a4882e10b5f951b2f
```

All six are clean at the current HEAD (`git status --short django_strawberry_framework/` prints
nothing). `utils/permissions.py` and `filters/base.py` are fingerprinted because I-R2 EXCLUDES
them from the lookup-path family on the strength of their current bodies; an exclusion needs a
fingerprint as much as an inclusion does, or a later edit silently changes the population without
reopening anything.

#### Revision 1 — item state

No production edit. Item-scoped diff against `ITEM_BASELINE=b2ec17eea042873767e2e30ebcdffa9e7e1ecaca`
still empty; `django_strawberry_framework/utils/querysets.py` still blob
`5907a1f72de42c71402886e7480ab559eb06a3af`. `uv run ruff format .` / `ruff check --fix .` not run,
because no tracked file was edited. No workspace was built this pass (nothing mutates source), so
the `--project`/`--directory` hazard the dispatch flagged did not arise; the one command I ran
against the shared tree is read-only and its package root is printed in its own output
(`/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework`).

Concurrent dirt has grown again and is entirely another session's: `AGENTS.md`, `GOAL.md`,
`docs/TREE.md`, `docs/feedback.md`, `docs/spec-050-list_field_arguments-0_0_15.md` and its
`-rationale.md`, `examples/fakeshop/tests/test_export_schema.py`,
`examples/fakeshop/tests/test_inspect_django_type.py`, `tests/management/test_export_schema.py`,
`tests/management/test_imports.py`, `tests/management/test_inspect_django_type.py`, plus three
untracked repo-root files whose names are literal whitespace. None is a path this item touches;
untouched, and Worker 0 owns the `## Cycle baseline` reconciliation.

## Independent verification (Worker 2) — re-pass after revision 1

Re-verifying revision 1. My pass-1 section above is intact and nothing in it was erased; the two
SUPERSEDED markers are additive and point forward to `## Iterations`, which is the correct shape.

### Mechanical state, re-checked rather than taken from the dispatch

```text
HEAD                                              5c62515a  (unchanged since my pass-1 note)
git diff b2ec17ee -- django_strawberry_framework/ empty
git status --short django_strawberry_framework/   empty
git ls-files --others --exclude-standard <pkg>    empty
utils/querysets.py                                5907a1f72de42c71402886e7480ab559eb06a3af
$WS/.../utils/querysets.py                        5907a1f72de42c71402886e7480ab559eb06a3af
```

The workspace predates the revision but the revision landed zero source edits, so the copy is
still faithful — confirmed by the blob above rather than assumed, and I re-ran the probe inside it
rather than only in the shared tree. All nine pass-1 fingerprints and all six newly recorded ones
(`utils/relations.py` `7662b0bb…`, `optimizer/plans.py` `cce98531…`, `utils/permissions.py`
`9889d6fe…`, `exceptions.py` `e06b0b7f…`, `filters/base.py` `ba52351c…`, `resource_policy.py`
`9205124f…`) re-hash to exactly the values recorded. Fingerprinting the two EXCLUDED modules is
the right call and I would not have thought to ask for it: an exclusion rests on a body just as an
inclusion does.

### R1 — discharged

I re-derived the population with an instrument instead of re-reading the same five bodies: an AST
sweep over every function in the package, flagging bodies that split on `"__"`/`LOOKUP_SEP` and
bodies that call `_meta.get_field`. Result — 21 functions touch one of the two, and exactly **4**
do both in one body: `connection.py::_resolve_order_path_field`,
`optimizer/plans.py::_select_path_traversable`, `utils/querysets.py::_prefetch_relation_target_or_none`,
`utils/relations.py::_lenient_traverses_to_many`. `classify_path` splits and delegates the
`get_field` half to `_resolve_segment_field`, which is why it is one body with its helper and the
fifth member. That is I-R1's table, reproduced by a different method. Every symbol name I-R1 and
I-R2 cite resolves (`_resolve_order_path_field` connection.py:780,
`_select_path_traversable` plans.py:653, `classify_path` relations.py:323,
`_resolve_segment_field` :287, `_lenient_traverses_to_many` :487).

**Both corrections to my write-up are accepted, and the first one is a straight error of mine.**
`utils/permissions.py` contains **zero** occurrences of `_meta.` anywhere in the file, so
`_fire_flat_relation_path_gates` cannot be a member of a family defined by the `_meta` walk — it
matches segments against declared `RelatedFilter` / `RelatedOrder` attributes. My C2 prose listed
it and my R1 table did not; Worker 1 is right that the two halves disagreed and right about which
half was accurate. The `filters/base.py` exclusion is equally correct
(`resolve_globalid_target_definition` splits but resolves through
`DjangoTypeDefinition.related_target_for`, never `get_field`), and flagging that a "resolve a
lookup path" framing would pull it in and make the count 6 is exactly the boundary statement a
rejection of this shape needs.

One addition, non-blocking: my sweep finds a second split-only site in the same class,
`list_field.py::_is_deterministic_order_name`. It is excluded for the same reason as
`filters/base.py` and belongs in the same sentence, so the "count rises to 6" caveat is really
"rises to 7". Worth one clause when the family item opens; it changes nothing now.

Verdict REJECTED-not-consolidated is the right outcome and it is now recorded as a rejection with
a contract difference and two triggers, with a durable home named. That is what R1 asked for.

### R2 — discharged, and the qualification is correct

I verified I-R4's two load-bearing facts myself, mechanically, because they are what makes my own
probe's hand-written `SITES` table sound and Worker 1 is right to have challenged it:

- AST over every `_seal_or_defect` call: **5 sites, exactly 1 passes `expected_routing`**
  (querysets.py:2979, `_validate_post_orderset_result`); the other four (`:2537`, `:3396`,
  `:3703`, `:3820`) pass none.
- `require_unevaluated` read off the live policy objects: **`_ORDERSET_RESULT_POLICY` alone is
  `True`**, and the complete set of `policy=` arguments reaching the two runners package-wide is
  `_LIST_ARGUMENT_VISIBILITY_POLICY` (list_field.py:1080, :1133), `_CASCADE_SEAL_POLICY`
  (permissions.py:623, :705), `_UNRECOMPOSED_CHILD_POLICY` (optimizer/walker.py:458), plus the
  `_DEFAULT_SEAL_POLICY` default — four, none of them `require_unevaluated`.

So `routing` and `evaluated` are unreachable at both sites, and D5's table is right for reasons
now measured at both ends rather than asserted at one.

**The false-positive qualification is correct and I should have caught it myself.** My prose says
`_validate_post_orderset_result`'s absent `alias` arm "is the opposite case and is argued
correctly in its own comment", and my table reports dead arms only — but the probe I shipped
prints `MISMATCH … missing: ['alias']` for that site and a bare `4/6` summary line. Anyone reading
the instrument's output instead of my prose concludes four defects. That is a self-falsifying
instrument in the small: the probe measures declared-vs-reachable honestly and then reports a
documented subsumption in the same vocabulary as a real omission. I-R4's fourth population term —
*a declared subsumption must be machine-readable at the site or it is indistinguishable from a
missing arm* — is the right repair and is the part F3 did not have. Reclassifying the finding as
gate-plus-declaration follows from it, and the honesty about the added cost (a small production
change at the sites, inherited by the family item) is the correct way to record it rather than
quietly leaving it inside a "gate-only" label.

D5 is a proper defect record: rule quoted at its owner, the three sites tabulated with the reason
each code cannot arrive, the `permissions.py` pair named as the control that shows the comparison
discriminates, the D4-class docstring quoted verbatim, the coverage blind spot stated, an owner
and a family named, and the file-item boundary respected. Re-ran the probe in `$WS` at the current
tree: `4/6`, same rows, negative control intact, **exit status 0** — so it cannot fail a gate; its
only hazard is being misread, which entry 3 of `## Pending execution` now warns about explicitly.

### R3 — discharged, and I-R5 is a real find that my method would not have reached

I-R3 gives the Manager-coercion rule a row with three challenges on its own axes and population
evidence (`models.Manager` at exactly three lines, all in this file — I re-checked). Flagging it
to the folder item as the file-local rule with the least margin is a judgement I agree with: its
failure mode is a visibility bypass, not a drift.

Worker 1 is right that R3 was under-scoped. I found C3 by walking the `### Challenges` table for a
row that terminated nowhere — an instrument that can only find gaps in rules someone already
posed a challenge for. `SyncMisuseError` had no challenge row, so my method was blind to it by
construction. Re-deriving name-by-name over the full enumeration is the instrument that sees the
class of gap rather than one instance, and it is what an inventory backstop is actually for.

**I tested the completeness claim rather than accepting it**, with two instruments:

1. *Name-mention sweep.* For each of the 134 module-level names, count word-boundary occurrences
   in Worker 1's sections excluding `## System trace` (descriptive, not an assignment). 54 names
   are never mentioned. That number over-reports by design and I say so: F2 assigns the seal by
   composition — "`_seal_or_defect` and the ~60 helpers it composes" — so a helper is assigned
   without being named, and DRY.md's unit is the RULE, not the symbol.
2. *Call-graph closure.* Starting from the 38 owners Worker 1 names across the families, F-rows,
   F12 rows, I-R3 and I-R5, take the transitive closure over intra-module references. **113 of 134
   names are reachable; 21 are not.** Judging those 21 one at a time: the three exported
   `_SealPolicy` instances and the twelve `_normalized_*` primitives are reached only through
   module-level constants (`_BOUND_VALUE_NORMALIZERS`), which my closure does not traverse — an
   instrument blind spot, not a gap, and F2/F4 name "the seven policy constants" explicitly;
   `pks_all_present` is named in F6's text; `reject_awaitable_sync_source` /
   `reject_residual_async_source` are named in F1's consumer list;
   `post_process_queryset_result_sync` / `_async` are named in matrix axis 2 under the `_*` glob my
   regex could not match.

That leaves **one** marginal name, and it is not a blocker: `materialized_rows`, with its helpers
`_readable_queryset_state` and `_row_source_model`, is named only in `## System trace` cluster 5.
It is not an unassigned RULE — it shares `normalized_row_source`'s premise exactly (an exact
`models.QuerySet`'s slots are Django's; a subclass's are consumer code), the two shipped in one
commit and are called on adjacent lines at `types/resolvers.py:576-577`, and F2's "Distinct
behavior" paragraph assigns that rule. But `materialized_rows` is the one symbol in the cluster
with a package-external consumer AND its own oracle (`tests/test_resource_policy.py:2160`, `:2174`),
so naming it in F2's row would save the `utils/` folder item a re-derivation. **Recorded as a
precision note, not a revision condition.**

So: yes, `SyncMisuseError` plus Manager coercion closes the enumeration. I-R5's sibling sweep is
also sound — `list_field.py::ListArgumentError` and `resource_policy.py::ResourceLimitExceeded` are
both `(GraphQLError, DjangoStrawberryFrameworkError)` against this one's
`(ConfigurationError, RuntimeError)`, and the declarations-not-definitions reasoning holds: the
pattern's change moves `exceptions.py`'s bases, a marker's identity change moves only that marker.

### The `## System trace` figure

Corrected in place to 102 functions / 7 classes / 25 constants (134 names; 109 excluding
constants) plus 6 nested methods, instrument named (`ast.Module.body`), old figure quoted so the
correction is legible rather than silent. Every number matches my own measurement, including the 6
nested methods (`_AsyncQuerySetRows.__init__` / `.__aiter__`, `_GraphWalk.__init__` / `.enter` /
`.begin` / `.leave`). Discharged.

### Where I do not fully agree: `## Pending execution` entry 3

DRY.md defines that section narrowly — *"Each `execution-deferred` proof: exact command, what it
discharges. Absent when none."* Entry 3 is not a deferred proof; it already ran, twice, and
Worker 1 labels it honestly as a regression witness. Strictly it does not belong under that
heading. Two things stop me making it a revision condition:

- Entry 2 has the same character (a request that the gate confirm three suites are green) and I
  accepted it in pass 1. Rejecting entry 3 now would be inconsistent with my own prior verdict.
- The consequence of leaving it is bounded and Worker 1 already bounded it: the probe exits 0, so
  it cannot fail the gate, and the entry states the expected `4/6` and points at I-R4 before the
  number is read as pass or fail.

Accepted as written, with the taxonomy point recorded for Worker 0 and the gate: **entries 2 and 3
are gate requests, not `execution-deferred` proofs; only entry 1 is.** A gate worker should run all
three and treat only entry 1 as discharging a proof. The section being non-empty is what decides
the plan marking below, so the distinction costs nothing here — but DRY.md's `## Pending execution`
contract has no home for a regression witness, and that is a gap in the method, not in this
artifact.

### Verdict

`Status: verified`. `## Pending execution` is non-empty (three entries, one of them a genuine
`execution-deferred` proof gated on Rio's `FAKESHOP_SHARDED=1` authorization), so the plan item is
ticked as **`verified, pending execution`**.

R1, R2 and R3 are all discharged, each in a stronger form than I asked for: R1 as a rejection with
contract difference, two triggers and a named durable home plus a new family; R2 with the gate
population repaired by a term I had not identified and the defect split out as D5; R3 with the
gap's whole class closed by an enumeration rather than its one instance. Two corrections to my own
write-up are accepted — `utils/permissions.py` is not a family member, and my probe carries a
known false positive at `_validate_post_orderset_result`. The item-scoped diff is still empty,
which is correct: a file item owes no production edit, none was made, and nothing in this
verification asks for one.

Plan rows Worker 0 should now write, all of which I endorse as stated:

- New family `orm-lookup-path-resolution`, owner
  `django_strawberry_framework/utils/relations.py::classify_path`, files covered
  `utils/relations.py`, `connection.py`, `optimizer/plans.py`, `utils/querysets.py`, holding item
  `dry-rule-orm-lookup-path-resolution.md`, status `open`.
- Index row for `utils/querysets.py::_prefetch_relation_target_or_none` changed from `file-local`
  to `rejected` (currently plan line 310 still reads `file-local`), files covered
  `utils/querysets.py` + `utils/relations.py`.
- Index row for `utils/querysets.py::_safe_class_name` changed from `file-local` to `rejected`,
  files covered `utils/querysets.py` + `exceptions.py` (currently plan line 304).
- Two new `file-local` index rows: Manager coercion (owner
  `utils/querysets.py::_coerced_manager_queryset`) and the sync-misuse marker's catch-shape
  contract (owner `utils/querysets.py::SyncMisuseError`).
- `seal-defect-code-wording` now carries D5 as well as F3, and F3 is gate-plus-declaration rather
  than gate-only.
- The twelve pass-1 families otherwise unchanged.

Scratch for Worker 0 to remove by explicit path after this verification:
`docs/dry/temp-tests/dry-file-utils__querysets-w2/probe_defect_arms.py` and the two
`docs/dry/temp-tests/dry-file-utils__querysets/` probes.

Concurrent dirt grew again during this pass and none of it is this item's; left alone, Worker 0
owns the `## Cycle baseline` reconciliation.

## D1 fix (Worker 1)

Root-cause correction of `## Defects` D1 — the optimizer walker's prefetch child accepting its own
`.using(...)`. Scope: the walker's seal call only. `django_strawberry_framework/utils/querysets.py`
and `tests/utils/test_querysets.py` were dirty with another session's `carry_result_cache` work at
dispatch time and were NOT touched; the residue that leaves is listed under "Residue" below.

### Files changed

| Path | Symbol | Change |
|---|---|---|
| `django_strawberry_framework/optimizer/walker.py` | module imports | `_UNRECOMPOSED_CHILD_POLICY` → `_PREFETCH_CHILD_POLICY` (the module already imported the private policy constant from `utils/querysets.py`, so no new layering) |
| `django_strawberry_framework/optimizer/walker.py` | `_build_child_queryset` | seals the child under `_PREFETCH_CHILD_POLICY` (`reject_sliced=False, require_shared_alias=True`); docstring + comment state why the seed stays unrouted and what each policy field buys |
| `examples/fakeshop/test_query/test_products_visibility_api.py` | module docstring, `_child_routing_schema`, `_CHILD_ROUTING_QUERY`, 2 tests | non-sharded live rows |
| `examples/fakeshop/test_query/test_multi_db.py` | module docstring, `_prefetch_alias_schema`, `_PREFETCH_ALIAS_QUERY`, `_post_prefetch_alias_query`, 3 tests | sharded live rows |

No new files. Item-scoped diff = `git diff -- django_strawberry_framework/optimizer/walker.py
examples/fakeshop/test_query/test_products_visibility_api.py
examples/fakeshop/test_query/test_multi_db.py` → `3 files changed, 264 insertions(+), 5
deletions(-)`; no `git diff --no-index /dev/null <new>` row is owed. All three paths were CLEAN at
`git status --short` when the item opened and carry nothing but this item's hunks now.

### Why the alias threaded is `None`

D1's prescription was "thread the parent's effective alias". The walker never holds the parent
queryset: `_build_child_queryset` runs inside `_walk_selections`, and the plan it contributes to is
inserted into `DjangoOptimizerExtension._plan_cache` and REUSED across requests
(`optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`). A per-request alias baked
into a cached child queryset would be served to the next request on another connection, so the
child must be alias-agnostic — which is exactly what `require_shared_alias` against an unresolved
outer alias enforces. `_prepared_visibility_source` already derives `required_alias` from the seed
(`base_queryset(field.related_model)`, `_db is None`), so the one missing fact was the policy. This
matches the rule `utils/querysets.py::_sealed_prefetch_related_lookups` applies to a
consumer-supplied `Prefetch` child under an unrouted parent: an explicitly routed child fails
closed, an unrouted child inherits the parent's connection at fetch time.

### Tests added

Live tier (`examples/fakeshop/test_query/`), which AGENTS.md mandates for any line reachable from a
real query. Both modules already existed, so the live-tier README suite map needs no new row; each
module's docstring gained the new verdict. No new fakeshop model or relation shape was needed, so
DRY.md "Tests" fixture-gap clause does not fire.

| Node id | Tier | Gate |
|---|---|---|
| `examples/fakeshop/test_query/test_products_visibility_api.py::test_planned_prefetch_child_may_not_pin_its_own_connection` | live, single DB | child hook returns `qs.using("default")` → `data: null`, one error naming `RoutingItemType.get_queryset` and `routed to alias 'default'` |
| `examples/fakeshop/test_query/test_products_visibility_api.py::test_planned_prefetch_child_still_serves_rows_when_the_hook_only_narrows` | live, single DB | control: a hook that only narrows still scopes the planned child and serves its page |
| `examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_cannot_route_itself_to_the_other_shard` | live, `FAKESHOP_SHARDED=1` | child hook returns `qs.using("shard_b")` under a `default` parent → refused, and `library_book` SQL count is 0 on BOTH aliases |
| `examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_inherits_an_unrouted_parents_connection` | live, `FAKESHOP_SHARDED=1` | control: unrouted child under unrouted parent → `on-default` only, 1 `library_book` read on `default`, 0 on `shard_b` |
| `examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_follows_a_routed_parent_onto_its_shard` | live, `FAKESHOP_SHARDED=1` | control: same unrouted child under a `.using("shard_b")` parent → `on-shard-b` only, 1 `library_book` read on `shard_b`, 0 on `default` |

The sharded three sit under `test_multi_db.py`'s module-level
`pytest.skip(..., allow_module_level=True)` env gate, so they skip under the default `uv run
pytest` exactly like every other row in that module.

### Fail-without-fix proof

Workspace copy only (`$WS = <scratch>/dry-ws/d1-fix`, package `__file__` printed from inside it
before every verdict:
`.../scratchpad/dry-ws/d1-fix/django_strawberry_framework/__init__.py`). The production hunk was
reverted IN THE WORKSPACE (`policy=_PREFETCH_CHILD_POLICY` → `policy=_UNRECOMPOSED_CHILD_POLICY`
plus the import), never in the shared tree; the file was restored from a pre-revert copy afterwards
and `cmp` against the shared tree reported byte identity.

Reverted, single DB:

```
>       assert payload["data"] is None
E       AssertionError: assert {'categories': [{'name': 'address', 'items': [{'name': 'address_fcd07f08'}]}, ...]} is None
FAILED .../test_products_visibility_api.py::test_planned_prefetch_child_may_not_pin_its_own_connection
1 failed, 1 passed, 12 deselected
```

Reverted, `FAKESHOP_SHARDED=1` — the failure message IS the leak:

```
>       assert payload["data"] is None
E       AssertionError: assert {'shelves': [{'code': 'S-default-on-default', 'books': [{'title': 'on-shard-b'}]}]} is None
FAILED .../test_multi_db.py::test_planned_prefetch_child_cannot_route_itself_to_the_other_shard
1 failed, 2 passed, 15 deselected
```

A shelf read from `default` served a book row that exists only on `shard_b`. Each control passed
under the revert, which is what makes the two failures attributable to the seal policy and not to
the fixtures.

Restored, in the workspace:

```
examples/fakeshop/test_query/test_multi_db.py ...            [100%]
3 passed, 15 deselected in 5.99s          (FAKESHOP_SHARDED=1)

examples/fakeshop/test_query/test_products_visibility_api.py [100%]
14 passed in 8.44s
```

### Commands

Workspace (`uv run --directory "$WS"` throughout):

- `pytest tests/optimizer examples/fakeshop/test_query/test_products_visibility_api.py
  examples/fakeshop/test_query/test_optimizer_auto_api.py --no-cov -q` → `869 passed, 2 skipped`.
- `pytest --no-cov -q` → `8311 passed, 41 skipped`, plus 3 failures + 1 collection error that are
  artifacts of the workspace recipe's `--exclude docs/ --exclude .git`
  (`tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file`,
  `::test_the_git_oracle_enumerates_this_module`,
  `tests/test_pg_explain_artifact_footer.py::test_checked_in_artifact_passes_link_block_validation`,
  `tests/test_export_dry_review.py` import error). They reproduce on a pristine copy of the same
  recipe and touch nothing this item changed.
- `FAKESHOP_SHARDED=1 pytest --no-cov -q` → `8333 passed, 38 skipped` with the same four recipe
  artifacts.
- `python scripts/check_citations.py --check` → `OK: 1104 citations resolve`.

Shared tree (the authorized focused run, plus the AGENTS.md post-edit formatters):

- `uv run pytest examples/fakeshop/test_query/test_products_visibility_api.py -k prefetch_child
  --no-cov -n0 -q` → `2 passed, 12 deselected`.
- `uv run ruff format .` / `uv run ruff check --fix .` / `uv run python
  scripts/check_trailing_commas.py <the three edited .py files>` — run scoped to the edited paths
  so the repo-wide auto-fix default never rewrote another session's files.

### Residue (owner reads a path this item was not allowed to edit)

Both sit in `django_strawberry_framework/utils/querysets.py`, dirty with another session's work:

1. `_UNRECOMPOSED_CHILD_POLICY` now has NO production caller — the walker was its only one. Its
   remaining reader is `tests/utils/test_querysets.py` (also dirty). Either the constant is deleted
   and that assertion re-pointed at `_PREFETCH_CHILD_POLICY`, or it stays as a named alias with a
   reason; leaving it as-is publishes a policy nothing applies.
2. Two docstrings still name it as the walker's policy:
   `utils/querysets.py::apply_type_visibility_sync` (the `policy` paragraph) and
   `utils/querysets.py::apply_type_visibility_async` (its sibling paragraph).
   Neither is a `path::Symbol` citation, so no gate catches the drift.

Two more, outside this item's scope:

3. `docs/GLOSSARY.md` *Prefetch alias threading* describes the child seal; the walker-built child
   now meets the same rule as the consumer-supplied one. Glossary bodies are rendered from the
   fakeshop `glossary` app DB, so the repair is a `GlossaryTerm` edit plus a re-render — the same
   mechanism D2 already needs.
4. `examples/fakeshop/test_query/README.md`'s suite-map rows for `test_products_visibility_api.py`
   and `test_multi_db.py` do not mention the connection verdict. The README was dirty at dispatch
   and was left alone; the authoritative module docstrings were updated instead.

### Behavior change

Not behavior-preserving, as D1 stated. A consumer whose target type's `get_queryset` calls
`.using(...)` and whose relation the optimizer plans now gets a `ConfigurationError` naming the
alias, where before it silently got a prefetch on that connection. The recourse the existing error
text already gives ("Remove the `.using(...)` call") is the correct one: pinning the PARENT moves
the whole resolution, and the child follows.

## D1 independent verification (Worker 2)

Status: `revision-needed` — one AGENTS.md layout violation in the item's own diff. The substance
(fix, owner, proof, tests) is otherwise verified; the re-pass is a formatter run.

### Expectation, recorded before reading `## D1 fix (Worker 1)`

Read first: `utils/querysets.py::_SealPolicy` (`require_shared_alias` bullet),
`utils/querysets.py::base_queryset` (`using` paragraph),
`utils/querysets.py::_sealed_prefetch_related_lookups`,
`utils/querysets.py::_prepared_visibility_source` (required-alias priority: write-pipeline pin >
sealed source's `_db` > `None`), `utils/querysets.py::_seal_or_defect` #"policy.require_shared_alias",
`docs/GLOSSARY.md` *Prefetch alias threading*, then the production hunk of
`git diff -- django_strawberry_framework/optimizer/walker.py`.

`optimizer/walker.py::_build_child_queryset` seeds with `base_queryset(field.related_model)` and
passes no `using=`, so the source's `_db` is `None` and the resolved `required_alias` is `None`.
Under `require_shared_alias` the seal's rule is `db is not None and db != required_alias`:

| case | expected |
|---|---|
| routed child, unrouted parent | REFUSED — `("alias", <alias>)` → `ConfigurationError`; this is the fix |
| unrouted child, unrouted parent | ACCEPTED, stays unrouted (`using = None`) |
| unrouted child, ROUTED parent | ACCEPTED — the parent's alias never enters this call; the child leaves unrouted and Django resolves it against the parent rows' connection at fetch |
| child hook that only narrows | ACCEPTED unchanged; the filter survives onto the sealed rebuild |

Corollaries I expected and then tested: the `reject_sliced=False` licence survives; a routed child
under a parent routed to the SAME alias is ALSO refused, because the walker cannot know the
parent's alias at plan-build time; and the new docstring's unconditional claim "never pinned to a
database alias, so the child's effective alias entering the hook is `None`" is in tension with
`_prepared_visibility_source`'s priority-1 write-pipeline pin.

Reconciliation with `## D1 fix (Worker 1)`: all four rows agree, and W1's "Why the alias threaded
is `None`" gives the same reason I derived (the plan is cached and reused across requests, so a
baked-in alias would be served to the next request on another connection). Two differences.
(a) W1 records no case for a routed child under a parent routed to the SAME alias; that case is
refused, and probe E below is what shows the refusal is required rather than over-strict.
(b) the write-pipeline wrinkle is unaddressed; it is not reachable here (the optimizer plan is a
read path) so it is a docstring-precision note, not a defect.

### Workspace provenance

```
WS=<scratch>/dry-ws/d1-verify   (fresh rsync taken after Worker 1's edits)
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
-> <WS>/django_strawberry_framework/__init__.py
settings.DATABASES["default"]["NAME"] -> <WS>/examples/fakeshop/db.sqlite3
```

`md5` of `django_strawberry_framework/optimizer/walker.py` equal in `$WS` and the shared tree at
copy time. Every command below ran via `uv run --directory "$WS"`; nothing ran in the shared tree.

### Checks

**1. New tests, both modes, and the fail-without-fix control.**

| command (in `$WS`) | result |
|---|---|
| `pytest examples/fakeshop/test_query/test_products_visibility_api.py --no-cov -q -n0` | `14 passed` |
| `FAKESHOP_SHARDED=1 pytest examples/fakeshop/test_query/test_multi_db.py --no-cov -q -n0` | `18 passed` |
| `FAKESHOP_SHARDED=1 pytest examples/fakeshop/test_query/test_products_visibility_api.py --no-cov -q -n0` | `14 passed` |

Reverted in the workspace only
(`git show HEAD:django_strawberry_framework/optimizer/walker.py > $WS/.../walker.py`):

- `test_planned_prefetch_child_may_not_pin_its_own_connection` → `1 failed, 1 passed`, the failure
  being `assert {'categories': [...]} is None`; its control passed.
- `FAKESHOP_SHARDED=1 ... -k prefetch_child` → `1 failed, 2 passed`; the failure is the leak itself,
  `{'shelves': [{'code': 'S-default-on-default', 'books': [{'title': 'on-shard-b'}]}]}` — a shelf
  read on `default` serving a book row that exists only on `shard_b`. Both controls passed reverted,
  so the two failures are attributable to the policy and not to the fixtures.

Restored afterwards; `cmp` against the shared tree reports byte identity.

**2. Attacks.** Scratch module `$WS/examples/fakeshop/test_query/test_w2_d1_attack.py`, live
`/graphql/` HTTP, `library_book` SQL counted per alias.

| probe | shape | result |
|---|---|---|
| A | parent `.using("shard_b")` + child hook `.using("shard_b")` (SAME alias) | REFUSED, 0 reads on both aliases |
| B | child hook returns `Book.objects.db_manager("shard_b").all()` | REFUSED, 0 reads on both aliases |
| B2 | child hook returns a fresh UNROUTED `Book.objects.all()` | ACCEPTED, 1 read on `default`, `on-default` only |
| C | sliced child (`q.order_by("pk")[:1]`) on a plain list relation | raw Django `TypeError` "Cannot filter a query once a slice has been taken." — IDENTICAL at HEAD; see `## Defects` |
| C2 | sliced AND routed child | REFUSED on the alias, 0 reads — the slice licence opens no bypass |
| D | `branches { shelves { books } }`, routed grandchild hook | REFUSED, names `AliasBookType.get_queryset`, 0 reads |
| D2 | same query, routed MIDDLE hook | REFUSED, names `AliasShelfType.get_queryset`, 0 reads |
| D3 | control: no routing anywhere, parent `.using("shard_b")` | ACCEPTED two levels down, 1 read on `shard_b`, 0 on `default` |
| E | ONE schema object, two requests, parent unrouted then `.using("shard_b")` | req 1 → `on-default`, 1 read on `default`; req 2 → `on-shard-b`, 1 read on `shard_b` |

A is the case W1 did not record, and E is its justification: the SAME cached plan serves a
`default` parent and a `shard_b` parent in consecutive requests, so a child that carried any
explicit alias would be wrong for one of them. Refusing the same-alias pin is correct, not
over-strict. The error text carries the recourse ("Remove the `.using(...)` call"), though its
"pinned to alias None" wording reads oddly for this surface.

**3. Owner and the `utils/querysets.py` question.** Confirmed at the owner. `git show
HEAD:django_strawberry_framework/utils/querysets.py` already defines
`_PREFETCH_CHILD_POLICY = _SealPolicy(reject_sliced=False, require_shared_alias=True)` and
`_seal_or_defect` already implements the axis; the only production fact missing was which policy
the walker passes. The concurrent dirt in that file touches `_RAW_LIST_SOURCE_POLICY` alone
(`git diff -- django_strawberry_framework/utils/querysets.py | grep POLICY`), so the no-edit claim
is independent of the concurrent work.

Residue judgment: `_UNRECOMPOSED_CHILD_POLICY` now has no production caller
(`grep -rn "_UNRECOMPOSED_CHILD_POLICY"` → `utils/querysets.py` definition + two docstrings,
`tests/utils/test_querysets.py:4956`, nothing else), and the `apply_type_visibility_sync` /
`apply_type_visibility_async` `policy` paragraphs still name it as the walker's policy, which is
now false. ACCEPTABLE TO LEAVE for the maintainer; it does NOT block acceptance. It changes no
behavior, the only reader left is a test that still passes, and both sites sit in a file this item
was correctly forbidden to edit. It must be homed on a named card, not dropped — recorded under
`## Defects` below.

**4. AGENTS.md prose rules.** No process provenance in any added line (no spec-cycle, worker, pass
or review vocabulary; the one `spec-045-visibility_boundary-0_0_14` anchor is a pre-existing
context line). No `path:NN` refs; citations are `path::Symbol`
(`optimizer/walker.py::_build_child_queryset`, `nested_fetch.py::unwindowable_child_queryset_reason`,
`utils/querysets.py::_sealed_prefetch_related_lookups`) and
`python scripts/check_citations.py --check` → `OK: 1104 citations resolve`. Tier is correct: all
five rows are in `examples/fakeshop/test_query/`, all reach the changed line through a real
`/graphql/` POST (`post_graphql` / `graphql_payload` over `django.test.Client`), no mock, no
`execute_sync`. Each asserts the boundary it claims — the refusals assert `data is None`, exactly
one error, the hook's own type name and the alias, and (sharded) zero `library_book` SQL on BOTH
aliases; the controls assert the served rows and the per-alias read counts. The three sharded rows
inherit the module-level `FAKESHOP_SHARDED` skip. `ruff check` → `All checks passed!`;
`scripts/check_trailing_commas.py --check` on the three files → exit 0.

BLOCKING: `ruff format --check` fails on the item's own new code.

```
$ uv run --directory "$WS" ruff format --check <the three paths>
1458 |     shelf_type = make_django_type(
     -         "AliasShelfType", models.Shelf, ("id", "code", "books"), node=False,
1459 +         "AliasShelfType",
...
1 file would be reformatted, 2 files already formatted
```

`examples/fakeshop/test_query/test_multi_db.py::_prefetch_alias_schema` #"AliasShelfType" is a
four-argument call left on one line with a magic trailing comma, which AGENTS.md's
explode-at-threshold layout (threshold 4) and the mandatory post-edit `uv run ruff format .` both
forbid. The `### Commands` section states the formatters were run; on this file they were not.
Fix: `uv run ruff format examples/fakeshop/test_query/test_multi_db.py`, re-run
`FAKESHOP_SHARDED=1 pytest examples/fakeshop/test_query/test_multi_db.py`, resubmit. Nothing else
is owed.

**5. Coverage.**
`pytest tests/optimizer examples/fakeshop/test_query/test_products_visibility_api.py
--cov=django_strawberry_framework.optimizer.walker --cov-report=term-missing -q -n0` →
`django_strawberry_framework/optimizer/walker.py  374  0  100%`, `869 passed`. The changed code
stays fully covered by the non-sharded suite: the single-DB refusal row drives the defect arm and
its control drives the accept arm, so the `fail_under = 100` gate does not depend on
`FAKESHOP_SHARDED=1`.

### Defects (Worker 2)

- **D-W2-a `_UNRECOMPOSED_CHILD_POLICY` is a published policy nothing applies.** Owner
  `django_strawberry_framework/utils/querysets.py`. After this item the constant has no production
  caller; `utils/querysets.py::apply_type_visibility_sync` and
  `utils/querysets.py::apply_type_visibility_async` still tell the reader the optimizer walker
  passes it, which the walker no longer does. Docstring-contradicting-its-body, with a contract
  source. Not fixable inside this item (the file is dirty with another session's
  `carry_result_cache` work). Needs a named card: either delete the constant and re-point
  `tests/utils/test_querysets.py` #"_UNRECOMPOSED_CHILD_POLICY" at `_PREFETCH_CHILD_POLICY`, or keep
  it as a named alias with a stated reason. Non-blocking.
- **D-W2-b The `reject_sliced=False` licence's premise does not hold for a plain list relation.**
  Owner `django_strawberry_framework/utils/querysets.py::_SealPolicy` #"Off one edge down" plus
  `django_strawberry_framework/optimizer/walker.py::_build_child_queryset`. The bullet justifies the
  licence by "the optimizer walker's nested-connection child, whose own gate degrades a sliced
  child"; `unwindowable_child_queryset_reason` is consulted only on the nested-connection / lateral
  / single-parent paths, never for a plain planned list relation. A child `get_queryset` returning
  a sliced queryset on such a relation therefore reaches Django's own recomposition and surfaces a
  raw `TypeError` ("Cannot filter a query once a slice has been taken.") outside the typed defect
  contract. PRE-EXISTING: reproduced identically with the walker reverted to HEAD, and plain Django
  raises the same error for the same `Prefetch("books", queryset=Book.objects.order_by("pk")[:1])`
  without this framework, so it is a wording / guard-scope robustness row, not a leak and not a D1
  regression. Non-blocking.

### Scratch to remove by explicit path after this verification

`$WS` is left on disk as instructed. Inside it:
`examples/fakeshop/test_query/test_w2_d1_attack.py` and
`examples/fakeshop/test_query/test_w2_django_sliced.py` (workspace-only, never in the shared tree).

### Revision 1

Two corrections, both raised by Worker 2. No test was added, removed or reworded, and no production
behavior changed.

**1. `ruff format --check` failed on `examples/fakeshop/test_query/test_multi_db.py`.** The
`shelf_type = make_django_type(...)` call inside `_prefetch_alias_schema` sat on one line carrying a
magic trailing comma. Cause is the COM812-versus-formatter interaction ruff warns about on every
run: the first `ruff format` collapsed the call, the `ruff check --fix` that followed added the
trailing comma, and nothing re-formatted afterwards, so the file was left in a state the formatter
would change. Fixed by re-running the formatter, which explodes the call to one argument per line:

```
     shelf_type = make_django_type(
-        "AliasShelfType", models.Shelf, ("id", "code", "books"), node=False,
+        "AliasShelfType",
+        models.Shelf,
+        ("id", "code", "books"),
+        node=False,
     )
```

Ordering lesson for this cycle: when both run, `ruff format` must be LAST, or `--check` disagrees
with what `--fix` just wrote.

**2. The walker docstring overclaimed.** It said the seed "is never pinned to a database alias",
which reads as a property of `_prepared_visibility_source` in general; that function's
priority-1 write-pipeline pin can supply an alias ahead of any seed, it is just unreachable on a
plan walk. Narrowed to a claim about this path and nothing else:

```
-    - the prefetch child is keyed on ``field.related_model``).
+    - the prefetch child is keyed on ``field.related_model``) and carries no
+    explicit ``.using(...)``. A plan walk is a read with no write pipeline in
+    force, so nothing pins an alias ahead of that seed either: the child's
+    effective alias entering the hook is ``None`` on this path, and the hook
+    cannot pin one of its own.
```

**Commands.** Shared tree, scoped to the item's paths:

- `uv run ruff format examples/fakeshop/test_query/test_multi_db.py` → `1 file reformatted`.
- `uv run ruff check --fix examples/fakeshop/test_query/test_multi_db.py` → `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py examples/fakeshop/test_query/test_multi_db.py` →
  `Fixed 0 file(s).`
- Same three on `django_strawberry_framework/optimizer/walker.py` after the docstring edit →
  `1 file left unchanged` / `All checks passed!` / `Fixed 0 file(s).`
- `uv run ruff format --check` on all three item paths → `3 files already formatted`.

Fresh workspace (`<scratch>/dry-ws/d1-fix-2`, rsynced with the same recipe; package `__file__`
printed as `.../dry-ws/d1-fix-2/django_strawberry_framework/__init__.py`, and the resolved database
names read from inside it as `.../dry-ws/d1-fix-2/examples/fakeshop/db.sqlite3` and
`.../db_shard_b.sqlite3`):

- `FAKESHOP_SHARDED=1 uv run --directory "$WS" pytest examples/fakeshop/test_query/test_multi_db.py
  --no-cov -q` — the WHOLE module, no `-k`, under the default parallel `-n auto` — →
  **`18 passed in 11.09s`** (8 workers, 18 items collected). 15 pre-existing rows plus this item's
  3.

Item-scoped diff after revision 1: `3 files changed, 269 insertions(+), 5 deletions(-)` (was 264
insertions; +5 are the two corrections above). Still no new files, so no
`git diff --no-index /dev/null <new>` row is owed. Nothing outside the three item paths was
touched, and the residue list above stands unchanged.

### Re-pass 1

Status: `verified`. The sole blocker from pass 1 is cleared and nothing else moved.

**Delta is exactly the two declared hunks.** The pass-1 workspace still holds the bytes I verified,
so the delta is read directly off it rather than off Worker 1's account:
`diff -u <d1-verify>/<path> <shared>/<path>` for all three item paths →
`examples/fakeshop/test_query/test_products_visibility_api.py` identical; `test_multi_db.py`
differs only at `_prefetch_alias_schema` #"AliasShelfType" (the four arguments exploded one per
line); `optimizer/walker.py` differs only in the `_build_child_queryset` docstring sentence about
the seed's alias. No other hunk, no other file. Every pass-1 finding therefore stands unretested.

**Lint, in a fresh copy `<scratch>/dry-ws/d1-verify-2`** (package `__file__` printed from inside it
first: `<WS2>/django_strawberry_framework/__init__.py`):

| command (in `$WS2`, three item paths) | result |
|---|---|
| `ruff format --check` | `3 files already formatted`, exit 0 |
| `ruff check` | `All checks passed!` |
| `python scripts/check_trailing_commas.py --check` | exit 0 |

**Tests re-run in `$WS2`:** `pytest examples/fakeshop/test_query/test_products_visibility_api.py
--no-cov -q -n0` → `14 passed`; `FAKESHOP_SHARDED=1 ... test_multi_db.py` → `18 passed`;
`FAKESHOP_SHARDED=1 ... test_products_visibility_api.py` → `14 passed`.

**The new docstring sentence is precise.** It now claims two things: the seed carries no explicit
`.using(...)`, and a plan walk is a read with no write pipeline in force, so the effective alias
entering the hook is `None` on this path. Both hold against
`utils/querysets.py::_prepared_visibility_source`, whose only two ways to a non-`None`
`required_alias` are the source's own `_db` (the seed has none) and priority 1,
`current_write_pipeline()`. That contextvar is set only inside
`utils/write_transaction.py::open_write_pipeline`, which `mutations/resolvers.py` #"with
open_write_pipeline(mutation_cls) as using:" enters as a `with` block around the mutation's own
body; the block has exited by the time any payload sub-field resolves, which is the only place an
optimizer plan walk could run under a mutation. So the claim is true for a sharper reason than the
one the sentence gives — it is not merely that a plan walk "is a read", it is that the pipeline's
scope closes before the walk can happen. The sentence asserts the conclusion without that
mechanism, which is a legitimate docstring choice at this altitude; my pass-1 tension note is
discharged.

Both `## Defects` entries marked `(Worker 2)` stand as written: `D-W2-a` (the
`_UNRECOMPOSED_CHILD_POLICY` residue) and `D-W2-b` (the slice-licence premise) are unchanged by
this revision and remain non-blocking, each needing a named owning card.

Scratch: `<scratch>/dry-ws/d1-verify-2` joins `d1-verify` on disk; both are workspace copies and
neither holds anything the shared tree needs.
