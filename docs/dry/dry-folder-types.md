# DRY review: folder `django_strawberry_framework/types/`

Status: verified

## System trace

`types/` is the Meta-driven Django→Strawberry type component: collect a
consumer `DjangoType` subclass, park unresolved relations, finalize once,
then expose a narrow public facade.

Lifecycle (one pipeline, eight modules):

1. **Collect** (`base.py`) — `DjangoType.__init_subclass__` validates `Meta`,
   selects fields, builds four-corner consumer-override sets, synthesizes
   scalar annotations via `converters`, records every auto relation as
   `PendingRelation` + `PendingRelationAnnotation`, registers
   `DjangoTypeDefinition` on the registry, installs `is_type_of`.
2. **Define** (`definition.py`) — write-once metadata record + memoized
   `related_target_for` / `has_custom_id_resolver_for`.
3. **Pending relations** (`relations.py`) — frozen record + sentinel only.
4. **Convert** (`converters.py`) — scalar / file-output / choice-enum /
   `resolved_relation_annotation` ownership.
5. **Finalize phases** (`finalizer.py`) — ambiguity + pending resolve →
   attach resolvers → Relay / GlobalID / relation-connection synthesis →
   bind filter/order/mutation/form/auth sidecars → field-surface audit →
   `strawberry.type` + `mark_finalized`.
6. **Resolvers** (`resolvers.py`) — Phase-2 cardinality + file parent
   resolvers, N+1 probe, FK-id elision.
7. **Relay** (`relay.py`) — interface injection, node defaults, GlobalID
   encode/decode strategy helpers; `SyncMisuseError` re-export from
   `utils/querysets`.
8. **Facade** (`__init__.py`) — `DjangoType`, `SyncMisuseError`,
   `finalize_django_types` only.

Connected evidence (not remits to edit unless ownership landed here):
`registry.py` (pending / definitions / GlobalID setting snapshot);
`optimizer/` (field_map, walker relation-connection slot, custom id
resolver); `connection.py` / `list_field.py` / `resource_policy.py`
(connection synthesis + list bounds); `utils/relations.py` /
`utils/querysets.py` (accessor / visibility); mutations / forms / auth /
filters / orders bind calls from Phase 2.5.

Folder axes: policy split across modules, state ownership, competing
helpers, public flavors, lifecycle work repeated at several phases.
Assignment leads (registry docstring path; unoptimized many-side
visibility) evaluated independently from source, not from file artifacts.

## Verification

- Item baseline `cd34c425…`: after this revision, item-scoped
  `types/finalizer.py` matches baseline again (empty production diff).
  Concurrent dirt on `types/definition.py` (docstring-only
  `DEFAULT_RELATION_SHAPE` wording vs HEAD) left untouched. Plan checkbox
  not edited.
- Re-read all eight modules end-to-end. Grepped package for
  `_is_relay_shaped` / `implements_relay_node`, field-surface set
  construction, `consumer_authored` vs `consumer_assigned` skip sets,
  `resolved_relation_annotation`, `bounded_rows` / `apply_type_visibility`,
  `DEFAULT_RELATION_SHAPE` / GlobalID strategy vocabulary, and bind
  sidecars.
- Compared `_audit_field_surface` and
  `_synthesize_relation_connections` collision membership byte-for-byte:
  identical three-way union (annotations ∪ selected_fields ∪
  `StrawberryField` attrs), restored inline at both sites with the
  explicit mirror docstring on `_audit_field_surface`. Confirmed file-item
  reject evidence still holds (co-located three-line mirror; different
  collision policies; no third site; not a cross-module folder invariant).
- Confirmed `_is_relay_shaped(cls, interfaces)` is pre-base-injection
  (needs the validated interfaces tuple) while `implements_relay_node`
  is post-`apply_interfaces` MRO membership — same Relay contract, different
  lifecycle inputs; not one function with a mode flag.
- Confirmed relation-attacher skip
  (`consumer_assigned_relation_fields`) vs file-attacher skip
  (`consumer_authored_fields`) is the intentional annotation-only file
  opt-out (spec-037 Decision 3), not drift.
- Confirmed many-side `manager.all()` path in `resolvers.py` does not call
  `apply_type_visibility_*` while optimizer Prefetch planning does — same
  visibility concept, different owners (visibility boundary / planning), not
  a second attach-resolver implementation.
- Confirmed `registry.py` module docstring still names
  `types.finalizer.resolved_relation_annotation`; the function lives in
  `types/converters.py`. True docstring owner is `registry.py` (already
  verified plan item); not fixed here.
- No tests were added solely to pin `_field_surface_names` (none to
  revert). Standing coverage remains under
  `tests/types/test_definition_order.py` and relation-connection collision
  tests. Deferred pytest: not authorized this pass.

## Opportunities

None.

## Rejected / deferred

1. **Extract `_field_surface_names` from the co-located three-set union.**
   Sites: `finalizer.py::_audit_field_surface` and the collision guard in
   `finalizer.py::_synthesize_relation_connections`. The unions match and
   the audit docstring already says they must mirror, but the verified
   `types/finalizer.py` FILE item already rejected extraction
   ([dry-file-types__finalizer.md][dry-file-finalizer]): co-located
   three-line mirror, different collision *policies* (empty/all-pairs
   camel audit vs single generated `*_connection` probe), no third site,
   not a cross-module / folder invariant. Folder pass confirms that
   evidence; does not overturn it. Line-count DRY alone is not clearer
   ownership. Reject (and reverted after a prior over-consolidation).

2. **Unify `_is_relay_shaped` and `implements_relay_node`.** Pre-injection
   needs `(cls, interfaces)`; post-injection is `issubclass(cls, relay.Node)`.
   One helper with a phase flag would obscure the base-injection boundary.
   Reject.

3. **Unify relation vs file Phase-2 skip sets.** Assigned-only vs full
   authored union is load-bearing for annotation-only `attachment: str`.
   Reject (re-proved at folder boundary).

4. **Fold many-side list resolve into connection resolve / add visibility
   inside `many_resolver`.** List path is prefetch-or-bounded `manager.all()`;
   connection path is windowed `to_attr` / Relay pipeline. Missing visibility
   on the unoptimized list path is a visibility/security question for
   `utils/querysets` / optimizer planning, not duplicated attach policy.
   Defer outside this folder.

5. **Fix stale `registry.py` docstring path for
   `resolved_relation_annotation`.** True owner of the symbol is
   `types/converters.py`; the wrong path string lives on already-verified
   `registry.py`. Defer to a registry touch or project pass — not a types/
   production-rule change.

6. **Collapse `_emits_model_label` / `_accepts_model_label_decode`.** Already
   share `MODEL_LABEL_STRATEGIES`; distinct names encode encode vs decode
   audit predicates. Reject.

7. **Hoist two-stage Meta target validators further.**
   `_selected_meta_targets` / `_normalize_sequence_spec` / Relay-gate lead-ins
   already own the shared halves; per-key domain checks differ. Further
   abstraction needs mode flags. Reject.

8. **PendingRelation snapshot `nullable` / `relation_kind` vs live
   `field_map`.** Snapshots are introspection; production finalize reads
   `FieldMeta`. Intentional. Reject.

9. **Public facade inconsistency (`SyncMisuseError` via `types.relay`).**
   Error lives in `utils/querysets`; re-export preserves the historical
   import path. Not competing flavors of one type API. Reject.

## Judgment

Folder ownership is already phased cleanly (collect → convert → pending →
finalize → resolvers / Relay → facade). No production consolidation is
warranted at the folder boundary on this pass. The co-located field-surface
three-set union stays inline (file-item reject upheld). Remaining
similarities are intentional lifecycle or skip-set differences, or owned
outside `types/`.

## Implementation (Worker 1)

- **Revision:** reverted the prior `_field_surface_names` extract in
  `django_strawberry_framework/types/finalizer.py` — restored both inline
  three-set unions and `_audit_field_surface`'s mirror docstring.
- **Tests:** none added solely for the extract; nothing to revert under
  `tests/`.
- **Opportunities:** `None` (no new cross-module folder finding proved).
- **Validation:** `uv run ruff format .` + `ruff check --fix .` after the
  `.py` revert. Pytest deferred (not authorized).
- **Changelog:** no.
- **Plan checkbox:** left open for Worker 2 re-verification.

### Scoped diff statement

```text
git diff cd34c425c07fd57cdb404b32b98fa2ad370b9040 -- \
  django_strawberry_framework/types/finalizer.py \
  docs/dry/dry-folder-types.md
```

Production change vs baseline: empty (`finalizer.py` restored). Concurrent
`types/definition.py` dirt ignored. Artifact records Rejected #1 +
Iterations. Ready for Worker 2 re-verification.

## Independent verification (Worker 2)

**Outcome:** revision-needed. Plan checkbox left open. No production
edits by Worker 2. No pytest. Concurrent `types/definition.py` dirt
left untouched.

**Scoped diff check:**
`git diff cd34c425c07fd57cdb404b32b98fa2ad370b9040 -- django_strawberry_framework/types/`
shows the `_field_surface_names` extract in `finalizer.py` only as the
folder item's production change (plus this artifact). No tests touched.
No unrelated absorption into the claimed fix.

**Challenge — `_field_surface_names` vs just-verified file reject: (B)**

The just-verified `types/finalizer.py` file item
([dry-file-types__finalizer.md][dry-file-finalizer]) rejected extracting
this exact three-set union with evidence that still holds on present-day
source:

1. **Co-located three-line mirror** — both sites live in
   `finalizer.py`; the pre-extract docstring already stated they must
   mirror. That is intentional local clarity, not a missing owner.
2. **Different collision policies** — `_audit_field_surface` does
   empty-surface + all-pairs `to_camel_case` grouping;
   `_synthesize_relation_connections` probes one generated
   `*_connection` name. Membership expressions matched; the *questions*
   differ. Extracting membership alone does not create a clearer
   ownership boundary — it only shortens co-located lines.
3. **No third site** — package-wide grep still finds only these two
   call sites (now via the helper). No cross-module consumer.
4. **Not a folder / cross-module invariant** — folder integration looks
   for policy split across modules, competing helpers, lifecycle work
   repeated at several phases, inconsistent public flavors
   ([DRY.md][dry] Integration passes). Re-implementing a same-file
   micro-extract that file Worker 2 already rejected (and marked
   verified) is out of remit; it does not become warranted merely by
   sitting in a folder pass.

Under DRY.md ("do not optimize for fewer lines"; consolidate only when
sites share one responsibility *and* a clearer owner), the file-item
rejection stands. Folder Worker 1 over-consolidated. **(A) is wrong;
(B) is the disposition.**

**Concrete blockers for Worker 1 (do not implement here):**

1. Revert `_field_surface_names`: restore the two inline three-set
   unions and restore `_audit_field_surface`'s explicit mirror-docstring
   wording (pre-extract contract).
2. Drop Opportunity 1 / Implementation as an accepted folder finding;
   record the field-surface union under Rejected with the file-item
   evidence above (folder pass confirms, does not overturn).
3. Set Opportunities to `None` for production edits **unless** a true
   cross-module folder finding is proved on a fresh pass. Do not re-land
   this extract without new evidence that overturns (1)–(4) — e.g. a
   third site or a cross-module membership consumer.

**Rejected / deferred candidates (independent re-check — hold):**

1. `_is_relay_shaped` vs `implements_relay_node` — pre-injection
   `(cls, interfaces)` vs post-`apply_interfaces` MRO. Reject stands.
2. Relation skip (`consumer_assigned_relation_fields`) vs file skip
   (`consumer_authored_fields`) — annotation-only file opt-out
   (spec-037 Decision 3). Reject stands.
3. Many-side `manager.all()` visibility vs optimizer Prefetch
   visibility — different owners; defer outside folder. Holds.
4. Stale `registry.py` docstring path for
   `resolved_relation_annotation` — true symbol in
   `types/converters.py`; wrong string on already-verified
   `registry.py`. Defer stands (not a types/ production-rule fix).
5–8. Model-label encode/decode predicates; Meta target validators;
   PendingRelation snapshot vs live `field_map`; `SyncMisuseError`
   re-export — reject stands.

**Independent missed folder-level search:** Re-read all eight `types/`
modules; grepped Relay predicates, skip sets, field-surface unions,
`resolved_relation_annotation`, visibility helpers, GlobalID strategy
vocabulary, bind sidecars, facade exports. No additional same-contract
/ same-change-axis duplication across modules that should consolidate
behind a clearer folder owner in this pass. Component phasing
(collect → convert → pending → finalize → resolvers/Relay → facade)
remains clean without the `_field_surface_names` extract.

## Iterations

### Iteration 2026-08-15 (Worker 1 — revision after W2 disposition B)

Worker 2 marked `revision-needed` (disposition B): `_field_surface_names`
over-consolidated a co-located three-line mirror that the verified
`types/finalizer.py` FILE item already rejected.

**Reverted:**

- Removed `django_strawberry_framework/types/finalizer.py::_field_surface_names`.
- Restored inline three-set unions in `_audit_field_surface` and
  `_synthesize_relation_connections`.
- Restored `_audit_field_surface` mirror docstring ("The surface set
  mirrors the connection guard's…").

**Tests:** none existed solely to pin `_field_surface_names` as sole owner;
no test revert.

**Artifact:** Opportunity 1 moved to Rejected #1 with file-item evidence
(confirm, do not overturn). Opportunities set to `None`. No new
cross-module folder finding proved. Status → `fix-implemented` for
Worker 2 re-verification. Plan checkbox left open.

## Independent verification (Worker 2) — re-verification

**Outcome:** verified. Plan checkbox marked `[x]`. No production edits by
Worker 2. No pytest. Concurrent `types/definition.py` dirt left untouched.

**Confirmations (independent):**

1. **`_field_surface_names` gone; inline unions restored.** Package-wide
   grep finds the helper name only in this artifact / prior DRY notes —
   not under `django_strawberry_framework/` or `tests/`. Both
   `_audit_field_surface` and `_synthesize_relation_connections` again
   carry the inline three-set union (`__annotations__` ∪
   `selected_fields` ∪ `StrawberryField` attrs). Mirror docstring on
   `_audit_field_surface` restored ("The surface set mirrors the
   connection guard's…").
2. **Production `types/` diff vs baseline empty.**
   `git diff cd34c425c07fd57cdb404b32b98fa2ad370b9040 -- django_strawberry_framework/types/`
   is empty (including `finalizer.py`).
3. **Opportunities = None; extract rejected with file-item evidence.**
   Rejected #1 records the co-located three-line mirror / different
   collision policies / no third site / not a folder invariant evidence
   from [dry-file-types__finalizer.md][dry-file-finalizer]; folder pass
   confirms, does not overturn.
4. **No leftover extract-only tests.** No `_field_surface_names` /
   `field_surface_names` pins under `tests/`.
5. **No new issues.** Revert restored baseline production; no fresh
   cross-module folder consolidation warranted this pass. Prior W2
   reject/defer holds (Relay predicates, skip sets, visibility ownership,
   stale `registry.py` docstring path, model-label predicates, Meta
   validators, PendingRelation snapshots, `SyncMisuseError` re-export)
   remain documented under Rejected / deferred — not blockers for verify.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[dry-file-finalizer]: dry-file-types__finalizer.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
