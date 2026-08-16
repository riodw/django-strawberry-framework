# DRY review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## System trace

This module owns **generated DjangoType field resolvers** attached at
`finalize_django_types()` Phase 2:

| Surface | Role |
| --- | --- |
| `_make_relation_resolver` / `_attach_relation_resolvers` | Cardinality-aware relation resolvers (many / reverse O2O / forward) |
| `_make_file_resolver` / `_attach_file_resolvers` | Parent file/image resolvers (empty `FieldFile` → `None`) |
| `_check_n1` + `_will_lazy_load_*` | Shared optimizer N+1 / strictness probe (also used by relation connections) |
| `_build_fk_id_stub` / `_fk_attname_is_deferred` | FK-id elision stub + deferred-column safety (spec-035 Decision 5) |
| `_name_resolver` / `_field_meta_for_resolver` | Trace naming + registered `FieldMeta` lookup |

Lifecycle: `types/finalizer.py` Phase 2 calls both attachers after pending
relation annotations resolve and before Phase 2.5 / Phase 3. Relation skip set
is `consumer_assigned_relation_fields`; file skip set is the broader
`consumer_authored_fields` (spec-037 Decision 3). Callers pre-select
`definition.selected_fields`; this module never re-runs `Meta.fields` selection.

Connected contracts examined (evidence only; siblings not absorbed):

- **Finalizer Phase 2:** attach order + skip-set asymmetry
  (`finalizer.py` Phase-2 loop).
- **File output types:** `converters._field_output_type_for` /
  `FIELD_OUTPUT_TYPE_MAP` decide which columns get a file parent resolver;
  subfield storage guard stays in `converters._safe_file_attr`.
- **Prefetch-cache contract:** many-side reads
  `_prefetched_objects_cache[accessor]` (same key as `_will_lazy_load_many`);
  optimizer walker plans under `instance_accessor` / `resolver_key` vocabulary.
- **Relation connections:** `connection._build_relation_connection_resolver`
  seeds from the same `instance_accessor`, reuses `_check_n1` with
  `kind="connection_to_attr"`, then runs the Relay pipeline / windowed
  `to_attr` path — not the bounded list path.
- **Root lists:** `list_field.py` owns root `DjangoListField` sync/async +
  visibility post-process; no nested-relation twin here.
- **Relay node resolvers:** `types/relay.py` GlobalID / `resolve_node*` —
  different concern.
- **Visibility:** nested planned Prefetch applies
  `utils/querysets.apply_type_visibility_sync` in the walker; generated
  relation resolvers do not re-implement that hook.

Item-scoped baseline `50df7d48bf6b9b06b7ddbc2489a77f1e5761dbcf`:
`git diff … -- django_strawberry_framework/types/resolvers.py` empty; no
production or artifact-path edits beyond this review file.

## Verification

Searches (package-wide): `_attach_relation_resolvers`, `_attach_file_resolvers`,
`_make_relation_resolver`, `_check_n1`, `_will_lazy_load_*`,
`_prefetched_objects_cache`, `_safe_file_attr`, `_make_file_resolver`,
`bounded_rows`, `instance_accessor`, `fields_cache`, `get_deferred_fields`,
`value if value else None`, sync/async resolver twins around relation lists.

Optional `export_dry_review.py audit --target …/types/resolvers.py`: inventory +
reverse imports (finalizer attachers; `connection` → `_check_n1`; tests). No
exact duplicate bodies involving this module's definitions. Orientation only.

Contract comparisons that disproved consolidation:

1. **`_attach_relation_resolvers` vs `_attach_file_resolvers`** — same loop
   shape, different predicates and skip sets. Merging into one parameterized
   attacher would hide the load-bearing
   `consumer_assigned_relation_fields` vs `consumer_authored_fields`
   asymmetry (annotation-only file opt-out must not get a generated parent
   resolver).

2. **Prefetch presence (`_will_lazy_load_many`) vs prefetch materialization
   (`many_resolver`)** — same cache key, different jobs (bool probe vs return
   rows / `_result_cache` / `bounded_rows`). A shared helper needs a mode flag
   or awkward Optional API; ownership of the N+1 rule is already single-sited
   in `_check_n1`.

3. **`_fk_attname_is_deferred` vs `_will_lazy_load_single`** — both short-circuit
   on `__dict__`, then diverge: deferred *column* attname vs relation
   `fields_cache`. Unifying would couple FK-elision safety to relation lazy
   detection.

4. **File parent falsy → `None` vs `_safe_file_attr`** — intentional layers:
   parent owns object nullability; converters own per-subfield storage
   degradation after a truthy `FieldFile` is returned. Moving either guard
   across the boundary breaks Decision 4's "parent has no try/except" contract.

5. **`many_resolver` vs relation-connection `_resolve`** — already share
   `instance_accessor` and `_check_n1`. List path is
   prefetch-or-`list(bounded_rows(...))`; connection path is windowed
   `to_attr` or full Relay pipeline. Collapsing them would smuggle pagination /
   sidecar semantics into list fields (or strip them from connections).

6. **Sync/async twins** — no async generated relation/file resolvers exist.
   Root `DjangoListField` / connection async posture is a different surface;
   nested connection docs require sync pipeline until a later async connection
   slice. Nothing to merge.

7. **`types/relay.py` node resolvers** — GlobalID encode/decode and
   `resolve_nodes`; not cardinality/`getattr` relation resolution.

## Opportunities

None — generated relation and file resolvers, the shared N+1 probe, and FK-id
elision already sit at their true owners. Apparent twins differ by skip set,
cache-probe vs materialization, parent-null vs storage-guard, or list vs Relay
pipeline. Cross-package reuse that matters (`_check_n1`, `instance_accessor`,
`_field_output_type_for`, `bounded_rows`) is already single-sourced.

## Judgment

Proved zero-edit. `types/resolvers.py` is the right owner for Phase-2 generated
resolvers and the resolver-side N+1 / FK-elision contract; connected surfaces
consume those hooks rather than re-implementing them.

### Deferred findings (not DRY consolidations)

- Unoptimized many-side `manager.all()` does not apply type visibility; the
  optimizer Prefetch path does via `apply_type_visibility_sync`. Asymmetry is a
  visibility/security question owned by the visibility boundary / optimizer
  planning, not a second copy of resolver attach logic.
- `connection._build_relation_connection_resolver` docstring wording equates
  accessor vocabulary to `field.name`; production code correctly passes
  `instance_accessor(field)` to match `many_resolver`. Docs nit on
  `connection.py`, out of this item's edit scope.

### Scoped diff statement

```text
git diff 50df7d48bf6b9b06b7ddbc2489a77f1e5761dbcf -- \
  django_strawberry_framework/types/resolvers.py \
  docs/dry/dry-file-types__resolvers.md
```

Production target unchanged; only this artifact is new. Ready for Worker 2.
No pytest run (not authorized); none deferred for production edits because
none were made.

## Independent verification (Worker 2)

**Outcome: verified** (zero-edit).

**Scoped diff:**
`git diff 50df7d48bf6b9b06b7ddbc2489a77f1e5761dbcf -- django_strawberry_framework/types/resolvers.py`
is empty. Artifact is new/untracked only; production target untouched.

**Re-trace:** Phase-2 attachers in `finalizer.py` (relation skip =
`consumer_assigned_relation_fields`; file skip = broader
`consumer_authored_fields`); cardinality resolvers + `_check_n1` /
FK-elision in this module; connection reuses `_check_n1` with
`kind="connection_to_attr"` and seeds via `instance_accessor(field)` from
the Phase-2.5 synthesizer; file parent nullability vs
`converters._safe_file_attr` storage guard; `types/relay.py` node /
GlobalID path separate.

**Challenges to rejected candidates (all hold):**

1. **Merge attachers** — finalizer intentionally threads different skip
   sets; file attacher also filters via `_field_output_type_for`. A shared
   loop would need flags that hide the annotation-only file opt-out
   (spec-037 Decision 3).

2. **Shared prefetch helper (probe vs materialize)** — `_will_lazy_load_many`
   is membership-only; `many_resolver` materializes with `_result_cache` +
   `bounded_rows`. Same Django key, different contracts / change axes;
   N+1 ownership already single-sited in `_check_n1`.

3. **Unify `_fk_attname_is_deferred` + `_will_lazy_load_single`** — shared
   `__dict__` short-circuit, then `get_deferred_fields()` (column) vs
   `_state.fields_cache` (relation). Coupling would mix FK-elision safety
   with relation lazy detection.

4. **Empty-file None into `_safe_file_attr`** — parent owns falsy
   `FieldFile` → `None` with no try/except; subfields own storage
   degradation after a truthy file. Crossing the boundary breaks Decision 4.

5. **Collapse `many_resolver` into connection `_resolve`** — already share
   `instance_accessor` + `_check_n1`. List path is prefetch-or-bounded
   `manager.all()`; connection path is windowed `to_attr` / Relay pipeline.
   Connection docstring still loosely equates accessor vocabulary to
   `field.name` while production correctly passes `instance_accessor` —
   docs nit on `connection.py`, not a DRY owner here.

6. **Sync/async twins / absorb `types/relay.py`** — no async generated
   relation/file resolvers; root list/connection async is another surface;
   relay helpers are GlobalID / `resolve_nodes`, not cardinality getattr.

**Missed consolidations searched:** package-wide uses of attachers,
`_check_n1`, prefetch-cache reads, `_safe_file_attr`, FK-elision stubs,
`_name_resolver`, and resolver-attach `setattr` patterns. No second owner
of the generated-resolver / resolver-side N+1 / FK-elision contract;
cross-package reuse is already single-sourced.

**Deferred (agree, not DRY for this owner):** unoptimized many-side
`manager.all()` skipping type visibility vs walker Prefetch
`apply_type_visibility_sync` — visibility/security boundary, not
resolver-attach duplication.

Plan checkbox marked `[x]`.
