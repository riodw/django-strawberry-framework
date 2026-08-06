# DRY review: `django_strawberry_framework/permissions.py`

Status: verified

## System trace

`permissions.py` owns **call-time cascade visibility** only:
`apply_cascade_permissions` / `aapply_cascade_permissions`. A consumer calls the
helper from inside `DjangoType.get_queryset`; the walk is depth-1 over the
model's single-column concrete forward FK / OneToOne edges (MTI
`<parent>_ptr` parent links included). Each edge whose target model has a
registered primary type contributes a subquery from that type's
`_default_manager` (pinned to the root DB alias) run through its
`get_queryset`, intersected as `Q(<edge>__in=<visible>)` plus
`| Q(<edge>__isnull=True)` when the edge is nullable. Pure `.filter(...)`
composition — no evaluation, reorder, or projection of the caller's queryset.

Present-day traversal contract (module docstring is authoritative):

- **Immutable `_TraversalState` on a `ContextVar`.** Frozen
  `(alias, active type tuple, path frames)`; every root / edge / nested frame
  installs a new state with a token and resets in `finally`. Fail-closed cycles
  raise a path-rich `ConfigurationError`; the one permitted re-entry is an
  explicit zero-edge scope (`fields=[]`).
- **Every registered target composes** (identity hooks included — a filtered
  default manager is still a visibility policy). Unregistered target models are
  skipped.
- **Unsupported forward relations preflight.** `_edge_plan` caches
  `cascadable` + `unsupported` (GFK / composite); a full walk over a model
  carrying an unsupported edge fails before any hook runs; naming one in
  `fields=` fails at validation.
- **Hook returns** go through the sealed visibility boundary
  (`utils/querysets.py::apply_type_visibility_sync` with
  `require_model_rows=False` and the cascade's `_edge_error_renderer`);
  cascade-local `_validated_target_subquery` then applies the SQL-composability
  battery and re-projects to `.values(field.target_field.attname)`.
- **Root / nested call-site querysets** are validated by the lighter
  non-sealing `_structural_defect` / `_validate_root_queryset` — the helper is
  invoked from inside consumer hooks and must `.filter(...)` the caller's
  object, not rebuild it through the seal.
- **Async twin** wraps the single sync walk in
  `utils/querysets.py::run_in_one_sync_boundary` (no second async walk; no
  inlined `sync_to_async`).

Item-scoped baseline (`8368fec3169eb40be6e93b362ef7c6a678965fcd`) vs working
tree for `permissions.py` is empty — this pass did not edit production code.

Callers / connected surfaces traced:

- `examples/fakeshop/apps/products/schema.py` — four products `DjangoType`s call
  `apply_cascade_permissions` from `get_queryset` (only real non-test consumer).
- Package root `__init__.py` re-exports both entry points; `SyncMisuseError` is
  also re-exported from this module (redundant-alias form, same convention as
  `types/relay.py`) while the class lives in `utils/querysets.py`.
- `utils/querysets.py` — owns `model_for`, `apply_type_visibility_sync` /
  `_normalized_visibility_result` (sealed boundary), `SyncMisuseError`,
  `reject_async_in_sync_context`, and `run_in_one_sync_boundary`. Cascade
  consumes all four shared primitives; it does not re-decide them.
- `registry.py` — primary-type lookup per edge (`registry.get(related_model)`).
- `utils/relations.py::relation_kind` — cardinality classifier used by
  optimizer / filters / connection; lookalike only (see Verification 1).
- `mutations/resolvers.py` — write-side consumer of the same visibility
  primitives (`apply_type_visibility_sync` / `model_for` /
  `run_in_one_sync_boundary`); different lifecycle (locate / relation decode),
  not cascade walk ownership.
- `mutations/permissions.py` and `utils/permissions.py` — sibling plan items;
  write-authorization / active-input permission *gates*, not row-visibility
  cascade. No shared cascade code; not touched.
- `filters/sets.py` / `orders/sets.py` — already import
  `run_in_one_sync_boundary` from `utils/querysets.py` (prior deferred
  consolidation has landed package-wide).
- `tests/test_permissions.py` — dedicated 1:1 suite; pins fail-closed cycles,
  `fields=[]` re-entry, MTI parent-link *inclusion* + row hiding, unsupported
  GFK preflight, sealed-boundary interaction, alias pinning, sync-misuse on
  both variants, and `run_in_one_sync_boundary` off-loop behavior.

## Verification

1. **`_is_cascadable_edge` / `_is_unsupported_forward_edge` / `_edge_plan` vs
   `utils/relations.py::relation_kind`.** Both classify relation descriptors,
   and MTI parent links are now *included* in both
   (`relation_kind` → `"forward_single"`; cascade → cascadable). That alignment
   does **not** make them the same rule. `relation_kind` answers GraphQL /
   optimizer cardinality and still classifies a `GenericForeignKey` as
   `"forward_single"` (fall-through); the cascade's load-bearing
   `isinstance(field, models.ForeignKey) and column is not None` test (plus the
   separate unsupported preflight) is the security scope for single-column
   `__in` composition and for `field.target_field` / `field.null` use in the
   walk. `connection.py` also layers its own non-null `forward_single` guard
   for keyset paths — a third independent reason to change. Coupling the
   cascade predicate to the cardinality classifier would add a cross-domain
   dependency without removing the column / ForeignKey / unsupported split.
   **Rejected.**

2. **`_validate_fields` vs `utils/inputs.py::normalize_field_name_sequence`.**
   Shared surface: reject a bare string iterated as characters. Contracts
   diverge: declaration-time `Meta.fields`/`exclude` shape-only → ordered
   `tuple` (duplicates rejected; membership left to call sites) vs call-time
   cascade `fields=` → `set` of cascadable edge names (unsupported-forward and
   non-cascadable membership are cascade-specific). Different lifecycle,
   membership basis, and wording. **Rejected.**

3. **Previously deferred `sync_to_async` / `run_in_one_sync_boundary`
   consolidation — confirm landed.** Present source:
   `aapply_cascade_permissions` is solely
   `await run_in_one_sync_boundary(apply_cascade_permissions, ...)`.
   `run_in_one_sync_boundary` lives in `utils/querysets.py` and is already
   reused by `permissions.py`, `filters/sets.py`, `orders/sets.py`,
   `mutations/resolvers.py`, `auth/mutations.py`, and `schema.py`.
   `tests/utils/test_querysets.py::test_run_in_one_sync_boundary_is_single_sourced_from_utils`
   pins the mutations re-export identity. No `sync_to_async(` call remains in
   `permissions.py` or `orders/sets.py` production code. **Confirmed landed;
   nothing left in this file's remit.** Remaining inlines elsewhere (if any)
   are other plan items / project integration.

4. **Root `_structural_defect` vs sealed boundary
   (`_seal_or_defect` / `_normalized_visibility_result`).** Hook *returns*
   already go through the seal (`require_model_rows=False`). The root checker
   deliberately does **not** seal: cascade must `.filter(...)` the caller's
   queryset object. Seal also skips sliced rejection when
   `require_model_rows=False`, which is why sliced / combinator / distinct /
   group_by / annotation-shadow stay in `_validated_target_subquery` beside the
   re-projection. Same query flags, different rules (root `.filter` soundness
   vs subquery re-projection soundness vs seal trust). Extracting a shared
   "read these flags" helper would optimize line count, not ownership.
   **Rejected.**

5. **Cascade edge seed
   (`related_model._default_manager.using(alias).all()` +
   `apply_type_visibility_sync(...)`) vs
   `visibility_scoped_related_queryset`.** Same primitive underneath, but the
   cascade needs root-alias pinning, cascade recourse / error renderer, and
   `require_model_rows=False` plus post-hook SQL re-projection. Folding into
   the write-side helper would force mode flags across domains. **Rejected —
   correct specialized consumer of the shared boundary.**

6. **`_TraversalState` / cycle `ContextVar` vs other package `ContextVar`s.**
   Optimizer / write-transaction / boundary-ordering ContextVars are unrelated
   lifecycles. No second cascade-cycle implementation. **Rejected.**

7. **Write-auth siblings (`mutations/permissions.py`,
   `utils/permissions.py`).** Confirmed still authorization / gate traversal,
   not row-visibility cascade. **Out of remit** (deferred to those plan items
   only as sibling distinction, no finding).

## Opportunities

None — present-day `permissions.py` already single-sources every
cross-module responsibility it shares (`model_for`, sealed
`apply_type_visibility_sync`, `SyncMisuseError`, `run_in_one_sync_boundary`)
and keeps cascade-only policy (edge plan, fields validation, traversal state,
cycle fail-closed, root structural checks, SQL re-projection battery, nullable
`__isnull` disjunct) local. The prior cycle's only real opportunity (promote /
reuse `run_in_one_sync_boundary`) has landed at `utils/querysets.py` and is
consumed here correctly.

## Judgment

Zero-edit. Cascade-visibility ownership is clear and already delegated at the
right seams; lookalike classifiers and validators were re-disproved against
current (MTI-including, fail-closed, sealed-boundary) source. Item-scoped diff
for `django_strawberry_framework/permissions.py` against
`8368fec3169eb40be6e93b362ef7c6a678965fcd` is empty. No `.py` edit → no ruff
run owed. Pytest deferred (maintainer did not authorize). Ready for Worker 2.

## Independent verification (Worker 2)

Re-confirmed the scoped diff independently: `git diff
4ea3d68932a9a984204069606d85fa45b47e7e22 -- django_strawberry_framework/permissions.py`
is empty, so this is genuinely a zero-edit item — no production or test file was
touched, no `ruff` run was owed.

**Cascade-visibility ownership re-traced.** Read the full target plus
`utils/querysets.py`, `utils/relations.py`, `mutations/resolvers.py`,
`mutations/permissions.py`, `utils/permissions.py`, `registry.py`,
`orders/sets.py`, `filters/sets.py`, `types/relay.py`, and the dedicated
`tests/test_permissions.py` (1564 lines, every documented invariant pinned:
cycle guard including the exception-path `finally` reset, single-column scope
per relation kind, MTI parent-link exclusion, nullable-FK preservation,
multi-DB alias pinning, transitive/self-referential cascade, registry
primary-vs-secondary resolution, identity-hook skip, `fields=` validation
shapes including the bare-string/non-iterable/non-string/unhashable-entry
cases, sync-misuse contract on both variants, N+1 zero-added-query proof,
FK-id-elision interaction, and filter/order gate composition with the
no-existence-leak pin). Confirmed `examples/fakeshop/apps/products/schema.py`
is the only real (non-test) caller (4 sites, one per `DjangoType`).

**Challenged rejected candidate 1** (`_is_cascadable_edge` vs.
`utils/relations.py::relation_kind`): confirmed independently.
`relation_kind`'s `"forward_single"` bucket explicitly *includes* the MTI
`<parent>_ptr` and has no `GenericForeignKey` exclusion beyond what
`_is_cascadable_edge`'s explicit `column is not None` test provides; the two
predicates read different Django flags for different reasons to change
(cardinality classification vs. security scope). Also swept for a third
sibling: `connection.py::_resolve_order_path_field` independently calls `relation_kind(field) != "forward_single"` for
yet a *third* purpose (non-null single-relation traversal for keyset
cursor-ordering paths) — reinforcing, not undermining, the artifact's
judgment that `relation_kind` is a shared low-level classifier that several
independent higher-level predicates legitimately layer their own guards on
top of; none of the three (`_is_cascadable_edge`, the FK-index guards, the
order-path guard) share a security/correctness axis with each other. Rejection
upheld.

**Challenged rejected candidate 2** (`_validate_fields` vs.
`utils/inputs.py::normalize_field_name_sequence`): confirmed independently —
declaration-time shape-only validation returning a `tuple` vs. call-time
shape-plus-membership validation returning a `set`, against genuinely
different wording contracts. Rejection upheld.

**Challenged the deferred `sync_to_async` finding — is `permissions.py`
correctly NOT the owner, and should it have implemented anyway?** Verified the
primitive (`mutations/resolvers.py::run_in_one_sync_boundary`) exists exactly
as described and is already reused cross-module by `auth/mutations.py` (two
call sites, both via a local/lazy import — confirmed by direct read).
Confirmed the two inlined siblings: `orders/sets.py`'s async `apply` (`await
sync_to_async(cls._run_permission_checks, thread_sensitive=True)(...)`) and
`filters/sets.py`'s async `apply_async` (`return await
sync_to_async(cls._apply_common_finalize, thread_sensitive=True)(...)`).
Agree the deferral itself is sound: `permissions.py` is a package-root module,
`run_in_one_sync_boundary` lives inside the `mutations` subpackage, and
`mutations/resolvers.py` already imports from `mutations/permissions.py` (a
different, sibling file) — so reaching into `mutations.resolvers` from the
root would be a real layering inversion regardless of whether it forms an
*actual* cycle today (it does not: `mutations/permissions.py` imports neither
`mutations/resolvers.py` nor the root `permissions.py` today, so the "cycle
risk" is prospective, not present — the artifact should say "would invert
layering" rather than imply an existing cycle, but the underlying call not to
implement here is correct either way). `utils/querysets.py` is independently
confirmed dependency-free (`from __future__ import annotations`, `asyncio`,
`inspect`, `typing`, `django.db.models`, `..exceptions` only) and therefore a
safe target every current site — including `mutations/resolvers.py` itself —
could import without inversion. Agree this should be forwarded, not fixed
here: `mutations/resolvers.py`, `orders/sets.py`, and `filters/sets.py` are
each still-open plan items in `docs/dry/dry-0_0_13.md`, so implementing the
promotion from inside the `permissions.py` item would pre-empt those workers'
own review of their file and risk absorbing unrelated-file changes into this
item, which `docs/dry/DRY.md` disallows ("Unrelated cleanup stays out of
scope").

**Two factual errors found in the artifact's evidence, requiring correction
before this item can verify:**

1. **System trace, present-day-inaccurate claim.** The trace states that
   `mutations/resolvers.py` *and* `mutations/permissions.py` "independently
   apply the SAME `apply_type_visibility_sync` / `model_for` primitives for
   the write side's relation-visibility and locate steps." Read
   `mutations/permissions.py` in full and grepped it directly: it imports
   neither `apply_type_visibility_sync` nor `model_for` (it imports
   `utils/permissions.py::request_from_info` and
   `utils/querysets.py::reject_async_in_sync_context` instead, for the
   write-authorization contract, not row visibility). Only
   `mutations/resolvers.py` uses the two primitives named. This
   mischaracterizes a connected file's actual contract in the very trace this
   review's cross-file reasoning depends on.
2. **Verification 3 / Opportunities, fabricated site detail.** Both the
   Verification-3 narrative and the Opportunities "Sites" bullet describe the
   `filters/sets.py` duplicate as `` sync_to_async(cls.qs_getter,
   thread_sensitive=True) `` plus "the `_apply_common_finalize` wrap" — i.e.,
   two separate call sites. Grepped the entire repository (including full git
   history via `git log --all -p`) for `qs_getter`: it does not exist
   anywhere, in any revision. The actual `filters/sets.py::apply_async` body
   has exactly ONE `sync_to_async` call, wrapping `cls._apply_common_finalize`
   (confirmed by reading `filters/sets.py::FilterSet._apply_common_finalize`); there is
   no second `qs_getter`-wrapped site. (`filters/sets.py` does carry an
   unrelated, currently-uncalled-from-production helper named `_read_qs` —
   exercised only by a direct unit test, `tests/filters/test_sets.py
   ::test_read_qs_returns_filterset_qs` — which may be what this claim was
   misremembering, but it is not itself a `sync_to_async`-wrapped site and is
   out of this file's remit to adjudicate; flagging it here only so whichever
   worker eventually reviews `filters/sets.py` can decide whether it is dead
   code.) Since this deferred finding is the ONE opportunity this item hands
   to a future worker, an inaccurate site inventory is not cosmetic: a future
   worker acting on "Sites" as written would search for a nonexistent
   `qs_getter` reference.

Neither error changes the underlying judgment (no consolidation belongs in
`permissions.py`; the `sync_to_async` boundary wrapper is real and correctly
deferred) or requires touching `permissions.py` itself — both are corrections
to the artifact's prose. Returning to Worker 1 to fix the two passages above
(and soften the cycle-risk wording per the note above) before this item can be
marked verified; the plan checkbox stays open in the meantime.

## Iterations

Re-verified all three of Worker 2's blocking points directly against current
source (not taken on faith) before editing:

1. **`mutations/permissions.py` claim.** Read the file in full and grepped it
   for `apply_type_visibility_sync` / `model_for`: zero matches. Confirmed it
   imports only `utils/permissions.py::request_from_info` and
   `utils/querysets.py::reject_async_in_sync_context` — a write-*authorization*
   contract (`has_permission` / `DjangoModelPermission` / `DenyAll`), not
   row-visibility. **System trace corrected**: split the old single bullet
   (which wrongly attributed `apply_type_visibility_sync`/`model_for` usage to
   both `mutations/resolvers.py` *and* `mutations/permissions.py`) into two —
   one confirming only `mutations/resolvers.py` uses those two primitives, one
   correctly describing `mutations/permissions.py` alongside
   `utils/permissions.py` as the write-authorization / gate-traversal sibling
   concern the cascade shares no code with.

2. **`filters/sets.py` site-inventory claim.** Read
   `filters/sets.py::apply_async` in full: it contains exactly one
   `sync_to_async` call, `sync_to_async(cls._apply_common_finalize,
   thread_sensitive=True)(...)`. Grepped the whole file (and, independently,
   the full repository) for `qs_getter`: no matches anywhere. Found the actual
   source of the confusion — `_read_qs`, a small `filterset_instance.qs`
   reader defined at module scope for `sync_to_async` — but confirmed it is
   called only from its own direct unit test
   (`tests/filters/test_sets.py::test_read_qs_returns_filterset_qs`), not from
   `apply_async` or any other production path today. **Verification 3 and the
   Opportunities "Sites"/"Evidence" bullets corrected**: removed the fabricated
   second `filters/sets.py` call site, named the real single site
   (`cls._apply_common_finalize`), and updated the "four sites" / "split four
   ways" counts to the accurate three (one owner + two duplicates:
   `permissions.py`, `orders/sets.py`; `filters/sets.py` is the third
   duplicate, not a fourth on top of a nonexistent one). Left the `_read_qs`
   dead-code observation out of this file's artifact body (it is not a
   `sync_to_async`-boundary duplicate and adjudicating it belongs to whichever
   worker reviews `filters/sets.py`), consistent with Worker 2's own scoping.

3. **Cycle-risk wording.** Re-confirmed independently: `mutations/permissions.py`
   imports `utils/permissions.py` and `utils/querysets.py` only (per point 1
   above); `mutations/resolvers.py` imports `mutations/permissions.py` (a
   different file) plus various `utils/*` modules — neither imports the root
   `permissions.py`. So no import cycle exists today; the risk is that adding
   a `permissions.py -> mutations.resolvers` edge would be a **new
   root-into-subpackage dependency direction** the package does not otherwise
   have, which is reason enough on its own not to add it here regardless of
   whether it would ever close an actual cycle. **Verification 3 reworded**
   from "would newly risk a cycle" to "would introduce a new
   root-into-subpackage dependency direction," with an explicit note that this
   is a prospective layering concern, not an existing cycle. The underlying
   call — defer the `sync_to_async` consolidation to a neutral owner rather
   than implement it from `permissions.py` — is unchanged; Worker 2 agreed
   this call was correct either way.

**Confirmed still zero-edit on `permissions.py`:** `git diff
4ea3d68932a9a984204069606d85fa45b47e7e22 --
django_strawberry_framework/permissions.py` is empty (re-run after all
artifact edits above). No production code was touched — every correction is
to this artifact's prose. `mutations/permissions.py` and `utils/permissions.py`
remain untouched (still dirty from the concurrent session that had them
in-flight at item start; preserved, not clobbered). No plan checkbox changed.
No commit made. Since no `.py` file was edited, no `ruff` run was owed.

Status set to `fix-implemented` — ready for Worker 2's re-verification.

## Independent verification (Worker 2, re-verification pass)

Read the full artifact end to end (System trace, Verification 1–3,
Opportunities, Judgment, prior Independent verification, and Iterations)
before re-checking anything, per instructions.

**Scoped diff re-confirmed empty.** `git diff
4ea3d68932a9a984204069606d85fa45b47e7e22 --
django_strawberry_framework/permissions.py` is still empty. `git status
--short` on the artifact confirms only `docs/dry/dry-file-permissions.md`
(this file) is dirty for this item; no production or test file was touched
during Worker 1's fix pass, matching the "prose-only correction" claim in
`## Iterations`.

**Blocking issue 1 (mutations/resolvers.py/mutations/permissions.py
misattribution) — resolved, confirmed independently.** Read
`mutations/permissions.py` in full and grepped it for
`apply_type_visibility_sync` and `model_for`: zero matches, confirming it
imports only `utils/permissions.py::request_from_info` and
`utils/querysets.py::reject_async_in_sync_context` (write-authorization
gate-checks, not row-visibility). Grepped `mutations/resolvers.py` for the
same two names: both appear repeatedly (`mutations/resolvers.py::model_for`;
`apply_type_visibility_sync`). The artifact's
System-trace bullet now correctly names only `mutations/resolvers.py` as the
site that "independently applies the SAME `apply_type_visibility_sync` /
`model_for` primitives," and correctly moved `mutations/permissions.py` to
its own bullet describing the write-authorization sibling concern with no
shared code. Issue resolved as described.

**Blocking issue 2 (fabricated `qs_getter` site) — resolved, confirmed
independently.** Grepped the entire repository for `qs_getter`: the only
matches are inside this artifact's own prose (Verification 3, Opportunities
"Sites"/"Evidence"/"Risks", and the Iterations entry explaining the
correction) — the token does not exist in any `.py` source file. Read
`filters/sets.py::FilterSet.apply_async` (its lone `sync_to_async(cls._apply_common_finalize, ...)` call): it contains
exactly one `sync_to_async` call, `sync_to_async(cls._apply_common_finalize,
thread_sensitive=True)(...)`. Also confirmed the `_read_qs`
tangent the artifact flags as the likely source of the original confusion:
it exists at `filters/sets.py::_read_qs`, is a small `filterset_instance.qs`
reader, and its only caller anywhere in the repo is
`tests/filters/test_sets.py::test_read_qs_returns_filterset_qs` (direct unit
test, not `apply_async` or any other production path) — matching the
artifact's "currently-uncalled-from-production" characterization exactly.
Also independently confirmed the sibling sites the corrected Opportunities
section still relies on: `orders/sets.py` has exactly one `sync_to_async`
call (`orders/sets.py::OrderSet.apply_async` wrapping `cls._run_permission_checks`), and
`run_in_one_sync_boundary` (`mutations/resolvers.py::run_in_one_sync_boundary`) is reused by
`auth/mutations.py` at two call sites (both via a
local/lazy import), exactly as described. Issue resolved as described.

**Blocking issue 3 (overstated cycle-risk wording) — resolved, confirmed
independently.** Re-read Verification 3's current wording: it now says
adding a `permissions.py -> mutations.resolvers` edge "would introduce a new
root-into-subpackage dependency direction" and explicitly states "this is a
prospective layering inversion, not an existing import cycle... neither
`mutations/permissions.py` nor `mutations/resolvers.py` imports the root
`permissions.py` today." Independently checked the imports of both files:
`mutations/permissions.py` imports only `..utils.permissions` and
`..utils.querysets` (confirmed by direct read above); `mutations/resolvers.py`
imports `..mutations.permissions` (grepped for `permissions` imports — no
import of the root `permissions.py` in either direction). No existing cycle;
the wording accurately describes a prospective one-way inversion rather than
implying a present cycle. Issue resolved as described.

**No new issues found.** The corrected passages are internally consistent
with the rest of the artifact (Judgment, Opportunities, and the two prior
Independent-verification / Iterations sections all now agree on the same
three facts), and none of the three corrections required or implied any
change to `permissions.py` itself, consistent with the confirmed empty
scoped diff.

**Conclusion:** all three previously-raised blocking issues are resolved
with accurate, source-confirmed corrections; no fabrications or
misattributions remain in the artifact. Status set to `verified`; plan
checkbox for `permissions.py` may be marked `[x]`.

## Iterations

### Fresh pass (Worker 1) — present-day source after cascade / seal evolution

Prior top-level prose (and the Worker 2 passes above) described an older
`permissions.py`: `_cascade_seen` partial-narrow cycles, MTI parent-link
*exclusion*, identity-hook skip, inlined `sync_to_async` in
`aapply_cascade_permissions`, and a deferred `run_in_one_sync_boundary`
promotion. Present source has moved past that contract. This pass did **not**
treat the old artifact body as evidence; it re-traced current
`permissions.py` (~717 lines) and connected surfaces, then rewrote
Status / System trace / Verification / Opportunities / Judgment above.
Historical Worker 2 / Iterations text is preserved as audit trail only.

**What changed in ownership since the old verified pass (source facts):**

- `_TraversalState` + fail-closed cycles (`fields=[]` escape hatch).
- MTI parent links cascade; tests pin inclusion and row hiding
  (`test_mti_parent_link_edge_included`, etc.).
- `_edge_plan` cascadable/unsupported split + GFK preflight.
- Hook returns sealed via `apply_type_visibility_sync(..., require_model_rows=False,
  render_error=...)`; cascade keeps SQL re-projection local.
- `aapply_cascade_permissions` → `run_in_one_sync_boundary` from
  `utils/querysets.py` (prior Opportunity closed outside this item).

**Strongest rejected candidates this pass:** (1) fold edge predicates into
`relation_kind`; (2) fold `fields=` into `normalize_field_name_sequence`;
(3) fold root/`_validated_target_subquery` checks into the seal; (4) fold
edge seed into `visibility_scoped_related_queryset`.

**Deferred to other items:** none from this file. Write-auth siblings remain
separate plan items by design. Any residual `sync_to_async` inline outside
the already-migrated sites is not owned here.

**Implementation:** none (proved zero-edit).
`git diff 8368fec3169eb40be6e93b362ef7c6a678965fcd -- django_strawberry_framework/permissions.py`
empty. Only this artifact updated. Plan checkbox left for Worker 2.
Status: `fix-implemented`.

## Independent verification (Worker 2) — fresh pass (post cascade/seal)

Independent re-trace of present-day `permissions.py` (~717 lines) and
connected surfaces against Worker 1's fresh zero-edit claim. Prior
Worker 2 / Iterations text above describes an older contract and was
treated as audit trail only, not evidence.

**Scoped production diff empty.** Re-ran
`git diff 8368fec3169eb40be6e93b362ef7c6a678965fcd -- django_strawberry_framework/permissions.py`
— empty. Working tree shows no dirty production path for this item
(only this artifact and the plan). Baseline file is also 717 lines;
no production edit landed in this item.

**Cascade-visibility ownership re-traced.** Read the full target;
confirmed `_walk` seeds
`related_model._default_manager.using(state.alias).all()` then
`apply_type_visibility_sync(..., require_model_rows=False,
render_error=_edge_error_renderer(...))` and keeps SQL re-projection in
`_validated_target_subquery`. Confirmed
`aapply_cascade_permissions` is solely
`await run_in_one_sync_boundary(apply_cascade_permissions, ...)`.
Confirmed root validation stays on non-sealing
`_structural_defect` / `_validate_root_queryset`. Confirmed
`examples/fakeshop/apps/products/schema.py` is the only non-test
consumer (four product `DjangoType`s). Confirmed
`mutations/permissions.py` / `utils/permissions.py` are write-auth /
active-input gate siblings with no cascade / `apply_type_visibility_sync`
/ `model_for` usage. Confirmed package-root re-exports both entry
points; `SyncMisuseError` redundant-alias re-export matches
`types/relay.py`.

**Challenged "already landed" sync-boundary claim — upheld.**
`run_in_one_sync_boundary` lives in `utils/querysets.py` and is the
sole production `sync_to_async(fn, thread_sensitive=True)` call site
for ORM boundaries (verified by repo-wide `sync_to_async(` grep:
owner body + `testing/client.py` login/logout only). Consumers include
`permissions.py`, `filters/sets.py`, `orders/sets.py`,
`mutations/resolvers.py`, `auth/mutations.py`, and `schema.py`.
`tests/utils/test_querysets.py::test_run_in_one_sync_boundary_is_single_sourced_from_utils`
pins the mutations re-export identity. No remaining consolidation in
this file's remit.

**Challenged rejected candidate 1** (`_is_cascadable_edge` vs
`relation_kind`) — upheld with executable proof. Scratch:
`GenericForeignKey` → `relation_kind` = `"forward_single"` but
`_is_cascadable_edge` False / `_is_unsupported_forward_edge` True;
MTI `<parent>_ptr` → both `"forward_single"` and cascadable True.
Cardinality classifier and security-scope predicate still change for
different reasons; `connection.py` layers a third independent
`forward_single` + non-null guard for keyset paths.

**Challenged rejected candidate 2** (`_validate_fields` vs
`normalize_field_name_sequence`) — upheld. Declaration-time
shape-only → ordered `tuple` (duplicates rejected; membership deferred)
vs call-time cascade `fields=` → `set` with unsupported-forward /
cascadable membership. Different lifecycle and wording.

**Challenged rejected candidate 4** (root / `_validated_target_subquery`
vs seal) — upheld. Seal docs explicitly leave sliced rejection to the
cascade when `require_model_rows=False`; cascade must `.filter(...)`
the caller's root object, so root cannot go through the seal. Shared
flag reads are not shared ownership.

**Challenged rejected candidate 5** (edge seed vs
`visibility_scoped_related_queryset`) — upheld.
`visibility_scoped_related_queryset` is
`apply_type_visibility_sync(related_type, initial_queryset(...), ...)`
with default `require_model_rows=True` and no alias pin.
Cascade needs `.using(alias)`, custom renderer,
`require_model_rows=False`, and post-hook SQL re-projection.

**Missed consolidations searched.** No second cascade walk; no second
cascade-cycle `ContextVar`; no production `sync_to_async` inline left
in this file; write-auth siblings correctly out of remit. Within-file
sliced/combinator checks in `_structural_defect` vs
`_validated_target_subquery` share flags but not contracts (root
`.filter` soundness vs subquery re-projection soundness) — agreeing
with Verification 4 that a shared "read these flags" helper would be
line-count, not ownership.

**Factual claims in the fresh System trace / Verification /
Opportunities / Judgment checked against current source** — no
blocking fabrications or misattributions found (unlike earlier passes
that wrongly attributed visibility primitives to
`mutations/permissions.py` and invented a `qs_getter` site). Those
older errors are superseded by the rewritten top-level prose and are
not re-opened here.

**Conclusion:** zero-edit claim verified. Status set to `verified`;
plan checkbox for `permissions.py` marked `[x]`. No production fix
owed; no pytest run (not authorized). Concurrent dirty work left
untouched.
