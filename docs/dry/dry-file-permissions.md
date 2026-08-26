# DRY review: `django_strawberry_framework/permissions.py`

Status: verified

## System trace

The file owns **call-time cascade visibility**: `apply_cascade_permissions`
(sync walk) and `aapply_cascade_permissions` (its async wrapper). A consumer
calls the helper inside its own `DjangoType.get_queryset`; the helper walks the
type's model single-column concrete forward FK / OneToOne edges (MTI parent
links included), resolves each edge target's registered primary type through
the registry, runs that target's `get_queryset` against its
`_default_manager.using(root_alias)` rows, and intersects
`Q(<edge>__in=<subquery>)` (plus `| Q(<edge>__isnull=True)` only for nullable
edges). Transitive cascade emerges because each target hook may itself call the
helper — the walk itself is depth-1.

Rules it owns end to end:

- **Edge classification** — `_is_cascadable_edge` is the single predicate;
  `lru_cache`d `_edge_plan` slices `model._meta.get_fields()` once into
  cascadable vs unsupported-forward (GFK / composite) tuples. Every consumer —
  the full-walk loop in `_walk`, the `fields=` validator `_validate_fields`,
  the unsupported preflight in `apply_cascade_permissions`, and the
  `_cascadable_edge_names` / `_cascadable_edges` helpers — keys off that one
  cached plan.
- **Traversal-state isolation** — frozen `_TraversalState` (root alias, active
  type tuple, path frames) in a module-level `ContextVar`; every root, edge,
  and nested application installs under a token and resets in a `finally`.
  Cycles fail closed with the path-rich `_cycle_error`; the sole permitted
  re-entry is an explicit zero-edge scope (`fields=[]`).
- **Root contract** — `_prepared_visibility_source` seals the untrusted root
  (cascade prose via `_root_error_renderer`, `require_model_rows=False` so a
  `.values()` root is legal), then `_validate_root_queryset` rejects sliced /
  combined roots the walk cannot `.filter(...)`.
- **Per-edge contract** — the hook invocation is delegated to
  `utils/querysets.py::apply_type_visibility_sync` (ONE sync-misuse site,
  cascade recourse `_ASYNC_RECOURSE`, path-rich `_edge_error_renderer`),
  after which the cascade-local `_validated_target_subquery` applies the
  SQL-composability battery (sliced / combined / field-distinct / grouped /
  annotation-or-extra alias shadowing the target column) and re-projects to
  `.values(field.target_field.attname)` so the membership test always binds
  the FK's actual target column.
- **Async color** — `aapply_cascade_permissions` wraps the single sync walk in
  `run_in_one_sync_boundary`; there is no second walk body and no
  async-native hook await (Decision 10).

Consumers: package-root export (`__init__.py::apply_cascade_permissions` /
`aapply_cascade_permissions`); the fakeshop schema's four `get_queryset` hooks
(`examples/fakeshop/apps/products/schema.py` CategoryType / ItemType /
PropertyType / EntryType); execution inside every read surface's visibility
call (`connection.py::_pipeline_sync` / `_pipeline_async`,
`list_field.py`, `types/resolvers.py`, `types/relay.py` node defaults — each
invokes the consumer hook through the shared boundary, and the hook cascades);
optimizer interplay (custom-get_queryset targets downgrade to `Prefetch`,
FK-id elision disabled); mutation-side authorization is a separate contract
(`mutations/permissions.py`). Tests: `tests/test_permissions.py` (foundation +
N+1 + gate-composition pins), composition pins in `tests/test_list_field.py`,
`tests/test_connection.py`, `tests/test_relay_node_field.py`,
`tests/optimizer/test_extension.py`; gate-mechanics tests in
`tests/utils/test_permissions.py`; live HTTP coverage in
`examples/fakeshop/test_query/test_products_visibility_api.py` and
`test_products_api.py`; standing prose in `docs/GLOSSARY.md`.
Lockstep partners: a change to the hook-running boundary or its defect codes
moves `utils/querysets.py` first and this file's renderers/recourse with it;
nothing else re-implements the walk.

## Verification

Axis 1 — cross-flavor policy mirroring (searched). Grepped the sibling
permission surfaces: write authorization (`mutations/permissions.py`
`DjangoModelPermission` / `run_permission_classes`), filter/order input gates
(`utils/permissions.py::run_active_input_permission_checks` +
`invoke_permission_method`), write relation-target visibility
(`utils/querysets.py::visible_related_object` / `visible_related_objects`),
and filter related-branch scoping (`filters/sets.py` around
`_collect_nested_visibility_querysets*`). All four answer different questions
(may see this row / may write this row / may attach this target / may supply
this input) and compose WITH the cascade rather than re-spelling it
(composition order pinned in `tests/test_permissions.py::
test_cascade_then_filter_gate_composition` and the order/gate twins). Shared
mechanics are already single-sited (`reject_async_in_sync_context`,
`request_from_info`). Read-vs-write "mirroring" is rejected: intentional
contract separation, documented at both sites ("can view" is never "can
write"). Second search — relation-path traversal re-derived elsewhere: grep
`models.ForeignKey)` / `_meta.get_fields()` / `parent_link` across the package
found no other site classifying single-column concrete forward edges for
visibility; the optimizer's predicates/walker classify relations for SQL
planning (join taxonomy, prefetch windows — different reason to change), and
`mutations/inputs.py` scans columns for write-input mapping. Rejected.

Axis 2 — sync and async twins (searched; compared by behavior). Exactly one
walk body exists (`_walk`, reached only from `apply_cascade_permissions`);
`aapply_cascade_permissions` is a three-line delegation through
`run_in_one_sync_boundary`. Behavior parity is pinned, not assumed: the async
variant raises `SyncMisuseError` on an `async def` target hook with the same
cascade-specific recourse (`_ASYNC_RECOURSE` threaded through
`apply_type_visibility_async`'s absence — the wrapped sync runner carries it),
worker-thread traversal state never leaks into the awaiting task
(asgiref-copied context), and gathered calls restore task contexts —
`tests/test_permissions.py::test_aapply_runs_walk_off_event_loop`,
`test_aapply_async_target_hook_still_raises`,
`test_aapply_gather_restores_task_contexts`. Genuine colored twins elsewhere
(`connection.py::_pipeline_sync` / `_pipeline_async`,
`types/relay.py` node defaults) route through
`apply_type_visibility_async`, which AWAITS async hooks; the cascade
deliberately never does. This file IS the consolidated shape — a twin pair
whose second half is a boundary wrapper, not a mirrored implementation.
Nothing to merge.

Axis 3 — derived rather than repeated knowledge (searched). The "which edges
exist" fact is authored once (`_is_cascadable_edge` → cached `_edge_plan`) and
all five in-module consumers project it. Two micro-repetitions found inside
the module: `_validate_fields` spells `frozenset(field.name for field in
plan.cascadable)` where `_cascadable_edge_names(model)` computes the same set,
and `_walk` iterates `_edge_plan(model).cascadable` where
`_cascadable_edges(model)` wraps the same tuple. Both projections consume the
identical cached tuple — the knowledge has one author; only a one-line
comprehension repeats, and rerouting `_validate_fields` (which also reads
`plan.unsupported` from the same slice) through a second lookup would split
one plan read for zero drift protection. Below threshold — rejected.
Recourse wordings: five `SyncMisuseError` recourses exist package-wide
(`_RELAY_ASYNC_RECOURSE`; the `sync_pipeline_recourse(flavor_noun)` template
already shared by the three write flavors; `_PERMISSION_ASYNC_RECOURSE`;
`_GATE_ASYNC_RECOURSE`; the cascade's `_ASYNC_RECOURSE`). Each names a
different owner/method/recourse; the ones that ARE byte-identical already
share the template function, and the cascade's differs materially (no
async-native walk exists; the recourse is "sync hook or `fields=`"). The
guard mechanics are one function (`reject_async_in_sync_context`). Rejected.
Root-vs-edge sealing: the cascade re-seals its root through
`_prepared_visibility_source` even when reached from inside an
already-sealed hook call — different contract point (`require_model_rows=False`
admits `.values()` roots; the argument is untrusted precisely because the
consumer invokes the helper directly), not duplicated policy. Rejected.

Axis 4 — inverse and round-trip pairs (ruled inapplicable). The module only
composes predicates; nothing decodes its own output. The one paired lifecycle
is the token install/reset bracket inside `apply_cascade_permissions`
(root frame) and `_walk` (per-edge frame) — symmetric resource brackets
co-located in their owners, not an encode/decode grammar split across modules.

Axis 5 — contracts restated in another medium (searched). The module
docstring, the `docs/GLOSSARY.md` `apply_cascade_permissions` section
(clause-level mirror: MTI parent links, GFK preflight, `fields=` validation,
hook-return battery, sync/async pair, composition order), roughly fifty
behavioral pins in `tests/test_permissions.py`, and the fakeshop live HTTP
tests all restate the contract. A policy or wording change forces code +
tests + GLOSSARY to move (occasionally KANBAN/TODAY references too). These
are the intentional media: GLOSSARY is the mandated fold-out of shipped
behavior, and the test pins keep behaviors independently legible. No parallel
implementation hides in any medium. Rejected as consolidation targets;
recorded as the lockstep set.

Single-edit-site counts:

- Posited change A — "a future composite/multi-column forward relation kind
  must join the fail-closed set": 1 production site
  (`_is_unsupported_forward_edge`); the cached plan, the preflight, the
  `fields=` validator, and the walk all follow automatically. Count = 1.
- Posited change B — "the cycle-error message format changes": 1 production
  site (`_cycle_error`); tests assert path strings and GLOSSARY shows the
  `AType.b -> BType.a -> AType` example — intentional pin/prose media, not
  competing implementations. Production count = 1.
- Posited change C — "make the async twin await async target hooks natively":
  would require an entire second walk implementation (colored per-edge hook
  dispatch). That is a deliberately rejected feature (Decision 10, encoded in
  `_ASYNC_RECOURSE`), not latent duplication waiting to be unified.
- Strongest rejected candidate — merging `_root_error_renderer` and
  `_edge_error_renderer`: parallel structures over the same shared-boundary
  defect codes, but different attribution (the consumer's own call vs the
  target type's hook return), different recourse sentences, different
  reachable code sets (root: type/table/untrusted; edge adds alias), and
  different interpolation variables. One parameterized renderer would need a
  mode flag per difference — the DRY.md anti-pattern. Kept separate.
- Second rejected candidate — sharing the sliced/combinator checks between
  `_validate_root_queryset` and `_validated_target_subquery`: different
  premises (root `.filter(...)` composability vs re-projection soundness;
  distinct/grouped/shadow have no root analogue). Verified against
  `utils/querysets.py::_seal_or_defect`: the `sliced` and `projection` defects
  fire only under `require_model_rows` (the seal documents that the cascade
  keeps its own slice rejection), so these cascade-local checks ARE the only
  slice rejections on both root and edge — hoisting them behind a boundary
  knob would express two different reasons as one flag. Kept separate.

No scratch experiments were warranted: every behavior whose ownership looked
ambiguous (sliced-return routing, async parity, renderer reachability) was
decided by reading the single code path plus the existing pins; nothing
remained uncertain enough to need an executable probe.

## Opportunities

None — proved. All five axes discharged (axes 1, 2, 3, 5 searched with the
greps and readings above; axis 4 ruled inapplicable on this surface). The
file's genuinely shared mechanics (hook running, sealing, async-hook
rejection, request resolution, the one-sync-boundary primitive) are already
delegated to their root owners in `utils/querysets.py` / `utils/permissions.py`,
and its own rule set (edge classification, cycle policy, per-edge validation)
is authored once inside the module. Posited changes A and B each came back
with a production count of one; the apparent duplications (twin variants,
renderer pair, root/edge check pairs, read/write permission surfaces,
five recourse wordings) were each disproved as intentional divergence backed
by a single-sited shared core.

## Judgment

This file is a consolidation endpoint, not a duplication site: the expensive
contracts it touches were already promoted to their root owners (sealed
visibility boundary, colored runners, sync-misuse guard, off-loop primitive),
and what remains local is exactly the part with no analogue elsewhere — the
edge grammar, the cycle policy, and the re-projection battery. The sync/async
pair is the model shape for the package: one walk, one boundary wrap,
behavior-parity pins instead of a mirrored implementation. Zero-edit result.
Deferred: `uv run pytest` (not authorized for this item).

## Independent verification (Worker 2)

Confirmed against the cycle baseline `525125b`: the item-scoped diff is empty
(`git diff 525125b -- django_strawberry_framework/permissions.py`). Re-traced
independently, not from this artifact:

- **One walk body.** `_walk` is reached only from `apply_cascade_permissions`
  (permissions.py:666); `aapply_cascade_permissions` is a single delegation
  through `run_in_one_sync_boundary`. Reading both entry points fully, the only
  behavioral divergences are the boundary itself: worker-thread execution
  (`thread_sensitive=True`) and the asgiref-copied context scoping the
  `ContextVar` install/reset away from the awaiting task. Argument pass-through
  is verbatim; no second walk, no async-native hook await anywhere in the file.
  Parity is pinned by `tests/test_permissions.py::test_aapply_runs_walk_off_event_loop`,
  `test_aapply_async_target_hook_still_raises`, and
  `test_aapply_gather_restores_task_contexts`.
- **Shared mechanics are genuinely at the root owners.** The per-edge hook run,
  sync-misuse rejection with the cascade's recourse (`async_recourse=
  _ASYNC_RECOURSE`), root sealing via `_prepared_visibility_source` with the
  cascade renderer and `require_model_rows=False`, and result sealing all live
  in `utils/querysets.py`. Verified inside `_seal_or_defect` that the `sliced`
  and `projection` defects fire only under `require_model_rows=True`, so the
  cascade-local slice/combinator checks on both root and edge ARE load-bearing
  rejections, not re-spelled boundary policy - the second rejected candidate's
  premise holds.
- **No call site re-derives visibility filtering.** `connection.py::_pipeline_sync` /
  `_pipeline_async`, `list_field.py`, `types/resolvers.py`, and `types/relay.py`
  node defaults each invoke the consumer hook through the shared colored
  runners; the cascade enters through consumer hooks (all four fakeshop products
  hooks confirmed calling it inside their own `get_queryset`). The package's
  other `pk__in` composers (`rest_framework/resolvers.py`, `utils/write_transaction.py`,
  `filters/sets.py` related branches) consume already-visible querysets for
  write-side locking / FK assignment / user-requested filter composition -
  different responsibilities, none walks edges or resolves registry targets.
- **Axis probes repeated.** Axis 1: additionally probed
  `orders/inputs.py::_get_concrete_field_names_for_order` (column-backed-field
  enumeration for order inputs - includes scalar columns, answers
  orderability, not visibility-edge composition) and found no second site
  classifying single-column concrete forward relations for visibility. Recourse
  population recounted: exactly five; the three write flavors already share the
  `sync_pipeline_recourse` template; Relay / permission / gate / cascade
  wordings are materially distinct. Cycle error recounted: one producer
  (`_cycle_error`), one raise site, path strings pinned by
  `test_mutual_cycle_fails_closed_with_path` and siblings. Axis 3 micro-repetition
  rejection stands: `_cascadable_edges` / `_cascadable_edge_names` project the
  identical cached tuple (production consumers inline it; the helpers serve as
  a test assertion lens), so rerouting buys zero drift protection while
  splitting `_validate_fields`'s single plan read.
- **Own count-of-one recount.** Posited change D - "flip the nullable-edge
  disjunct policy" (drop `| Q(<edge>__isnull=True)` or extend it to non-null
  edges): the package's ONLY production composer of that disjunct is
  permissions.py:713-716 in `_walk`; behavior pins
  (`test_isnull_disjunct_only_on_nullable_edges`,
  `test_nullable_fk_rows_preserved`, `test_nullable_chain_preserves_null_links_and_drops_hidden_tails`)
  and the GLOSSARY clause follow. Production count = 1. Posited change E -
  "add one more forbidden shape to the re-projection battery": sole site
  `_validated_target_subquery`. Both recount to one.

Matrix discharged on the real surface (axes 1, 2, 3, 5 searched; axis 4 ruled
inapplicable - the module composes predicates and never decodes its own output;
the token brackets are co-located resource management). Verdict: proved
zero-edit stands. Pytest remains deferred per cycle rules.
