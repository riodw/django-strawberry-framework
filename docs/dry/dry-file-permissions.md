# DRY review: `django_strawberry_framework/permissions.py`

Status: verified

## System trace

`permissions.py` owns exactly one responsibility: **call-time cascade visibility**
(`apply_cascade_permissions` / `aapply_cascade_permissions`). It walks a
`DjangoType`'s model single-column forward FK/OneToOne edges
(`_is_cascadable_edge`, `_cascadable_edges`), resolves each edge's target type
through `registry.get` (primary lookup), and intersects
`Q(<edge>__in=<target-visible-pks>) | Q(<edge>__isnull=True)` into the caller's
queryset — narrowing without evaluating, reordering, or projecting. A
`ContextVar` seen-set (`_cascade_seen`) breaks cascade cycles; `_validate_fields`
validates an optional `fields=` scoping kwarg against the cascadable-edge set.
The async twin wraps the single sync walk in
`sync_to_async(thread_sensitive=True)`.

Confirmed against the baseline (`git diff 4ea3d68932a9a984204069606d85fa45b47e7e22
-- permissions.py` is empty): the file is unchanged this cycle, so this is a pure
fresh-eyes review, not a diff review.

Callers / connected surfaces traced:

- `examples/fakeshop/apps/products/schema.py` — the four products `DjangoType`s
  (`CategoryType`/`ItemType`/`PropertyType`/`EntryType`) call
  `apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` from
  their `get_queryset` hooks — the only real (non-test) consumer.
- `django_strawberry_framework/__init__.py` re-exports both public entry points.
- `django_strawberry_framework/utils/querysets.py` supplies the two primitives
  the walk reuses rather than re-deciding: `model_for` (model lookup) and
  `apply_type_visibility_sync` (the one sync `get_queryset`-invocation +
  `SyncMisuseError` site every read/write surface shares). `SyncMisuseError`
  itself is re-exported here, mirroring the established `types/relay.py`
  redundant-alias convention — an intentional, already-singly-sourced pattern,
  not new duplication.
- `django_strawberry_framework/mutations/resolvers.py` independently applies
  the SAME `apply_type_visibility_sync` / `model_for` primitives for the write
  side's relation-visibility and locate steps — confirms these two primitives
  are already the single owner of "run a target's `get_queryset` safely"; the
  cascade does not duplicate that contract, it consumes it. (Corrected per
  Worker 2 — see `## Iterations`: `mutations/permissions.py`, a *different*,
  still-open sibling plan item, does NOT use either primitive; it is a
  write-*authorization* module, not a row-visibility one — see the next
  bullet's distinction.)
- `django_strawberry_framework/mutations/permissions.py` and
  `django_strawberry_framework/utils/permissions.py` (both sibling plan items,
  not consolidated here) own a structurally different concern from the
  cascade — write-authorization / active-input permission-*gate* checks
  (`has_permission`, `check_<field>_permission`) — not row-visibility
  narrowing. `mutations/permissions.py` imports
  `utils/permissions.py::request_from_info` and
  `utils/querysets.py::reject_async_in_sync_context` only; it never touches
  `apply_type_visibility_sync` or `model_for`. No shared code with the
  cascade; traced only as siblings, not touched.
- `tests/test_permissions.py` is the dedicated 1:1 test file (per Decision 3)
  and pins every documented invariant (cycle guard, single-column scope, MTI
  parent-link exclusion, nullable-FK preservation, multi-DB alias pinning,
  `fields=` validation shapes, sync-misuse contract, N+1 / FK-id-elision
  interaction, gate composition). No gaps found; not edited.

## Verification

Searched for parallel or overlapping implementations of each piece of the
cascade's contract:

1. **`_is_cascadable_edge`'s "forward single-column edge, minus M2M / GFK /
   reverse / MTI-parent-link" predicate vs.
   `utils/relations.py::relation_kind` + `optimizer/field_meta.py::FieldMeta`.**
   Both classify Django relation descriptors by shape, and `relation_kind`'s
   `"forward_single"` bucket documents that it explicitly *includes* the MTI
   `<parent>_ptr` (`"MTI <parent>_ptr-like -> "forward_single""`), whereas the
   cascade must explicitly *exclude* it (a child row must not be narrowed by
   its MTI-parent type's hook — pinned by
   `test_mti_parent_link_edge_excluded`). Substituting
   `relation_kind(field) == "forward_single"` would not remove any of
   `_is_cascadable_edge`'s other guards: `GenericForeignKey` sets none of
   `many_to_many`/`one_to_many`/`one_to_one`, so `relation_kind` would
   misclassify it as `"forward_single"` too — the explicit
   `getattr(field, "column", None) is not None` test is what actually excludes
   it, and that test is not part of `relation_kind`'s contract at all. The two
   predicates answer different questions for different reasons to change:
   `relation_kind` classifies GraphQL/optimizer *cardinality* (list vs. single
   object; changes with query-shape/elision work), `_is_cascadable_edge`
   classifies a *security* scope (which edges may narrow visibility; changes
   with the cascade's own contract, already tightened across 8 spec revisions
   per `docs/SPECS/spec-034-permissions-0_0_10.md`). Coupling the two would add
   a cross-domain optimizer dependency to a security-critical predicate while
   saving nothing (every other guard stays). **Rejected** — no shared
   responsibility, only coincidental surface similarity.

2. **`_validate_fields`'s bare-string-iterable-of-names validation vs.
   `utils/inputs.py::normalize_field_name_sequence` and
   `types/base.py::_format_unknown_fields_error`.** Both guard against a bare
   string being iterated character-by-character, but the surrounding contract
   diverges completely: `normalize_field_name_sequence` validates a
   **declaration-time** `Meta.fields`/`Meta.exclude` sequence (shape only —
   duplicate-name rejection, no membership check; the model-membership check is
   explicitly left to each of the three write-flavor call sites per its own
   docstring) and returns a `tuple`, preserving order. `_validate_fields`
   validates a **call-time** `fields=` keyword argument against a computed
   per-model set (the cascadable edges), rejects non-string entries
   individually (a check `normalize_field_name_sequence` does not perform), and
   returns a `set`. `_format_unknown_fields_error`'s message shape
   (`"{model}.Meta.{attr} names unknown fields: ... Available: ..."`) is
   likewise scoped to `Meta.*` declaration typo-guards by its own docstring;
   the cascade's unknown-name message ("`fields=[...] on {model} are not
   cascadable`") answers a narrower question — not "unknown to the model" but
   "known to the model, not cascadable" — and is not a `Meta.*` construct at
   all. **Rejected** — different lifecycle (class-creation vs. per-call),
   different validation scope (shape-only vs. shape-plus-membership), different
   wording contract; sites do not change together.

3. **`aapply_cascade_permissions`'s inlined `sync_to_async(fn,
   thread_sensitive=True)(*args)` bridge vs. the established generic primitive
   `mutations/resolvers.py::run_in_one_sync_boundary`.** This IS a genuine
   repeated responsibility — "run a sync callable in exactly one
   `sync_to_async(thread_sensitive=True)` worker call" — with real evidence
   that the package already treats it as a single-sourceable primitive:
   `run_in_one_sync_boundary(fn, *args, **kwargs)` already exists in
   `mutations/resolvers.py` (spec-040 D17/P3) and is already reused
   **cross-module** by `auth/mutations.py` (`from ..mutations.resolvers import
   run_in_one_sync_boundary`, called twice, via a local/lazy import). Two
   other sites independently inline the identical shape instead of calling it:
   `permissions.py::aapply_cascade_permissions` (`return await
   sync_to_async(apply_cascade_permissions, thread_sensitive=True)(cls,
   queryset, info, fields)`) and `orders/sets.py`'s async `apply` (`await
   sync_to_async(cls._run_permission_checks, thread_sensitive=True)(...)`).
   Corrected per Worker 2 (see `## Iterations`): `filters/sets.py::apply_async`
   has exactly ONE `sync_to_async` call, wrapping `cls._apply_common_finalize`
   (`return await sync_to_async(cls._apply_common_finalize,
   thread_sensitive=True)(...)`) — there is no second, `qs_getter`-wrapped
   site (`qs_getter` does not exist anywhere in the repository, in any
   revision). All three sites' docstrings independently cite the SAME
   rationale (off-event-loop consumer-hook safety) — a real single-changeable
   rule split three ways.
   **Verified as real, but forwarded rather than fixed here** (see
   Opportunities below): `permissions.py` is not this rule's true owner, and
   `mutations/resolvers.py`, `orders/sets.py`, and `filters/sets.py` are each
   still-open sibling plan items. Reusing `run_in_one_sync_boundary` from the
   root `permissions.py` would also invert the package's layering (a root file
   importing from the `mutations` subpackage — `mutations/resolvers.py`
   already imports `mutations/permissions.py`, a *different* file, so a root
   `permissions.py -> mutations.resolvers` edge would introduce a new
   root-into-subpackage dependency direction). Softened per Worker 2 (see
   `## Iterations`): this is a **prospective layering inversion**, not an
   existing import cycle — neither `mutations/permissions.py` nor
   `mutations/resolvers.py` imports the root `permissions.py` today; the
   concern is that adding this one edge would be the wrong direction for a
   root-level module to depend on a subpackage, not that a cycle already
   exists. The true owner is a neutral, dependency-free home (most naturally
   `utils/querysets.py`, which already owns the sibling
   `reject_async_in_sync_context` primitive and is documented as "cycle-safe by
   construction") that every current site — including `mutations/resolvers.py`
   itself — could import without inverting any direction.

## Opportunities

- **Repeated responsibility:** run a sync callable in exactly one
  `sync_to_async(thread_sensitive=True)` worker call (the off-event-loop
  boundary every consumer-overridable sync hook needs).
- **Sites:** `mutations/resolvers.py::run_in_one_sync_boundary` (existing
  owner, already reused by `auth/mutations.py`); `permissions.py::aapply_cascade_permissions`
  (inlined duplicate); `orders/sets.py` async `apply` (inlined duplicate);
  `filters/sets.py::apply_async` (inlined duplicate, wrapping
  `cls._apply_common_finalize` — corrected per Worker 2, see `## Iterations`;
  there is no separate `qs_getter` site).
- **Evidence:** all three duplicate sites wrap a single callable in the
  byte-identical `sync_to_async(fn, thread_sensitive=True)(*args)` shape for
  the identical reason (keep a consumer's blocking sync hook off the event
  loop); the fourth site (`mutations/resolvers.py`) already promoted it to a
  named primitive and reused it cross-module.
- **Owner:** NOT `permissions.py` — a neutral, dependency-free utils module
  (`utils/querysets.py` is the natural fit: cycle-safe by construction, already
  hosts the sibling `reject_async_in_sync_context` primitive). NOT implemented
  here: `mutations/resolvers.py`, `orders/sets.py`, and `filters/sets.py` are
  each still-open plan items for other workers, and moving the primitive
  is their call to make (or the project-integration pass's, since it spans
  four modules across three still-open folders).
- **Consolidation (deferred):** promote `run_in_one_sync_boundary` to
  `utils/querysets.py` (or a dedicated neutral module), update
  `mutations/resolvers.py` to import it instead of defining it, then migrate
  `permissions.py`, `orders/sets.py`, `filters/sets.py`, and `auth/mutations.py`
  to the new import path.
- **Proof:** none created here — deferred to whichever worker implements the
  move; a permanent test would assert the promoted primitive's identity is
  reused by all sites (no re-inlining) plus the existing per-site off-loop
  behavioral pins (`test_aapply_runs_walk_off_event_loop` here) keep passing
  unchanged.
- **Risks / non-goals:** do not fold `filters/sets.py::FilterSet._apply_common_finalize` into the generic primitive if its call shape needs filter-specific handling preserved - confirm at the folder pass, not assumed here.

None else — `_is_cascadable_edge`/`relation_kind` and `_validate_fields`
/`normalize_field_name_sequence` were traced and disproved (Verification 1–2);
`SyncMisuseError`'s re-export, `model_for`, and `apply_type_visibility_sync`
are already correctly single-sourced through `utils/querysets.py` and consumed
identically by every read/write surface, including this one.

## Judgment

`permissions.py` is a small, mature, single-purpose module whose own contract
(the cascade walk, its scope predicate, its `fields=` validator) is already
singly owned and heavily spec-reviewed; it correctly delegates the two
primitives it shares with every other visibility/write surface
(`model_for`, `apply_type_visibility_sync`) to `utils/querysets.py` rather than
re-deriving them. The one real repeated responsibility found — the generic
sync-to-async worker-boundary wrapper — belongs to a neutral owner outside this
file's remit; recorded above with full evidence for the worker whose item
actually owns it (or the project-integration pass). Item-scoped diff to
`permissions.py` is empty; ruff was not run because no source file was edited.

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
