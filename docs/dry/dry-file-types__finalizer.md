# DRY review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## System trace

`finalize_django_types()` is the once-only build gate for collected `DjangoType`
classes. It owns phase orchestration and finalize-time audits; sibling modules
own the work each phase invokes.

| Phase | What runs | True owners of the work |
| --- | --- | --- |
| Entry | `registry.is_finalized()` short-circuit; materialize `multi_type_models` once; snapshot `RELAY_GLOBALID_STRATEGY` | `registry.py` (flag + generator); `types/relay.py::_validated_globalid_setting` |
| 1 (failure-atomic) | `_audit_primary_ambiguity`; classify pending relations; rewrite resolved annotations; `discard_pending` | Pending records: `types/relations.py` + `types/base.py::_build_annotations`; rewrite: `types/converters.py::resolved_relation_annotation` |
| 2 | `_attach_relation_resolvers` / `_attach_file_resolvers` | `types/resolvers.py` |
| 2.5 | `apply_interfaces` + Relay composite-PK / `resolve_*` / GlobalID install; `validate_cursor_field_columns`; no-Node check; `_synthesize_relation_connections`; model-label routing audit + secondary-collapse warn; pre-bind subsystem clears; `bind_auth_mutations` → `bind_mutations` → `bind_form_mutations` → `_bind_filtersets` → `_bind_ordersets`; `_audit_field_surface` | Interfaces/Relay: `types/relay.py`; cursor columns: `keyset.py`; connection builders: `connection.py`; auth/mutations/forms bind: their packages; filter/order bind driver: this file (`_bind_sidecar_sets`) |
| 3 | `strawberry.type(...)` + `definition.finalized = True`; `registry.mark_finalized()` | This file only for consumer `DjangoType` decoration |

Connected surfaces traced as evidence (still-open siblings not absorbed):

- `types/relations.py` — `PendingRelation` / sentinel; finalizer is the sole rewrite consumer.
- `types/relay.py` — interface injection, Relay gates, GlobalID strategy stamp; finalizer calls, does not reimplement.
- `types/resolvers.py` — Phase-2 attach loops; skip-set contract differs (assigned-relation vs full `consumer_authored_fields`).
- `types/base.py` / `types/definition.py` — class-creation Meta + definition slots; finalizer writes `relation_connections` / `finalized` only.
- `mutations.sets.bind_mutations` / `forms.sets.bind_form_mutations` / auth `bind_auth_mutations` / DRF riding `bind_mutations` — phase-2.5 sidecar bind order owned here; each binder owns its ledger.
- `registry.py` — `models_with_multiple_types`, pending discard, `before_bind` clears, finalize flag.
- `keyset.validate_cursor_field_columns` — column contract; class-creation shape already in `types/base.py::_validate_cursor_field` via shared `validate_cursor_field_references`.

Item-scoped baseline `fcfb43a19117a6b06c59fe969b1c8540b0050328`:
`git diff fcfb43a… -- django_strawberry_framework/types/finalizer.py` empty at
review start and after this item (proved zero-edit).

## Verification

Searches: `finalize_django_types`, `_synthesize_relation_connections`,
`_bind_sidecar_sets`, `_bind_set_owner_common`, `_audit_primary_ambiguity`,
`_audit_field_surface`, `apply_interfaces`, `strawberry.type(`,
`validate_cursor_field`, `bind_mutations` / `bind_form_mutations` /
`bind_auth_mutations`, `models_with_multiple_types`, `to_camel_case` /
`graphql_camel_name`, orphan / owner-mismatch formatters, field-surface name
union (`__annotations__` \| `selected_fields` \| `StrawberryField`).

Contract comparisons that disproved consolidation:

1. **Filter/Order bind loops** — Already single-sited in `_bind_sidecar_sets` +
   `_SidecarBindingSpec` and `_bind_set_owner_common`. Thin `_bind_filtersets` /
   `_bind_ordersets` wrappers exist only for cycle-safe local imports and
   family-specific audits (GlobalID encode-only + unregistered RelatedFilter).
   Further merging would need mode flags for filter-only axes. Rejected.

2. **Mutation / form / auth / DRF bind** — Deliberate non-consumers of
   `_bind_sidecar_sets` (mutation docs: placement sibling, not driver consumer).
   Different ledgers, materialization, and error shapes. Finalizer owns call
   order + one `before_bind` clear pass; each package owns its binder. Rejected.

3. **Primary-ambiguity messaging** — Phase-1 `_audit_primary_ambiguity` /
   `_format_ambiguity_error` is the registry-wide owner (tests pin the fix
   sentence). `mutations/sets.py::_resolve_primary_type` and
   `auth/mutations.py` raise *bind-surface* messages (mutation name / auth
   factories + zero-type vs multi-type split) that fire in phase 2.5 after the
   audit already guaranteed a primary for multi-type models. Same vocabulary
   fragment, different contract and change axis. Rejected.

4. **Relation-shape synthesis vs connection builders** — Synthesis decides
   eligibility / shape / collision / list suppression / definition mapping;
   `connection.py` owns `_connection_type_for` and
   `_build_relation_connection_resolver`. Pulling either side across the
   boundary would mix orchestration with connection machinery. Rejected.

5. **Field-surface name union** (two sites in this file: `_audit_field_surface`
   and `_synthesize_relation_connections`) — Identical three-set union; docstring
   already states they must mirror. Collision *policies* differ (group-by-camel
   empty/collision audit vs generated-`*_connection` name check). Extracting a
   three-line helper would not move a cross-module invariant and would only
   optimize co-located lines. Rejected as intentional local clarity with an
   explicit mirror contract.

6. **Camel collision vs write-input guards** —
   `utils/inputs.py::iter_input_field_collisions` / form / serializer / filter
   generated-input guards are intentional *parity siblings* of
   `_audit_field_surface` (read-type vs write-input specs, different nouns and
   lifecycle). Unifying would couple unrelated materialization paths. Rejected.

7. **`strawberry.type` wrapping** — Phase 3 is the sole decoration of consumer
   `DjangoType` classes. `connection.py` / `mutations/inputs.py` decorate
   *generated* sidecar classes at materialize time under their owners. Rejected.

8. **`cursor_field` validation** — Already layered correctly: reference syntax
   in `keyset.validate_cursor_field_references` (shared by class-creation and
   finalize); column contract in `validate_cursor_field_columns` (finalize-only
   call from this file); Meta shape in `types/base.py::_validate_cursor_field`.
   Rejected further merge.

9. **`to_camel_case` vs `graphql_camel_name`** — Finalizer uses Strawberry's
   `to_camel_case` because that is what the default `NameConverter` applies
   under `auto_camel_case=True` at schema build. `graphql_camel_name` is a
   different injective transform for generated input attrs. Rejected.

10. **Interface injection** — Owned by `types/relay.py::apply_interfaces`;
    finalizer only schedules it in the Phase-2.5 window. Rejected.

11. **Orphan / owner-mismatch Filter vs Order formatters** — Parallel wording
    with family-pinned nouns (`FilterSet` / `filter_input_type` /
    `filterset_class` vs Order equivalents). Spec/tests pin strings;
    `_SidecarBindingSpec.format_orphans` already parameterizes the hook.
    Parameterizing message bodies would trade grep-stable family text for a
    mode-flagged template. Rejected.

## Opportunities

None — phase orchestration and the Filter/Order sidecar driver are already at
their true owners; remaining structural parallels are intentional
family/parity siblings or co-located three-line mirrors, not shared rules that
should change behind one helper.

## Judgment

Proved zero-edit. `types/finalizer.py` is the finalize lifecycle owner: it
sequences phases, runs registry-wide audits, synthesizes relation connections,
drives Filter/Order binding through one shared sidecar driver, and is the only
site that applies `strawberry.type` to consumer `DjangoType` classes. Connected
binders, Relay helpers, resolvers, keyset column checks, and connection
builders correctly remain outside this file. Strongest rejected candidates were
further Filter/Order/mutation bind merging, primary-ambiguity message
unification, field-surface name-set extraction, and read/write camel-collision
unification.

Deferred pytest: none owed (no production edits). Existing coverage in
`tests/test_registry.py`, `tests/test_relay_connection.py`,
`tests/types/test_definition_order.py`, and sidecar bind suites remains the
permanent proof surface for Worker 2.

Ready for Worker 2.

## Independent verification (Worker 2)

**Scoped diff:** `git diff fcfb43a19117a6b06c59fe969b1c8540b0050328 -- django_strawberry_framework/types/finalizer.py` empty. Zero-edit claim holds.

**Re-trace:** Read complete `types/finalizer.py` (~1821 lines). Phase ownership matches the artifact table: Phase 1 owns ambiguity + pending rewrite; Phase 2 attaches resolvers with distinct skip sets; Phase 2.5 schedules Relay/keyset/synthesis/`before_bind` clears then `bind_auth_mutations` → `bind_mutations` → `bind_form_mutations` → `_bind_filtersets` → `_bind_ordersets` → `_audit_field_surface`; Phase 3 alone applies `strawberry.type` to consumer `DjangoType` classes. Filter/Order already share `_bind_sidecar_sets` + `_bind_set_owner_common`; mutation/form/auth binders remain deliberate non-consumers (`mutations/sets.py` module docstring: placement sibling, not driver consumer).

**Challenges to rejected candidates (source evidence):**

1. **Further Filter/Order/mutation bind merging** — Confirmed reject. `_SidecarBindingSpec` already carries family hooks (`post_expand_audit`, `before_second_owner_check`, formatters). Mutation bind iterates a declaration registry with different materialization/error shapes (`mutations/sets.py` #"Deliberate divergence from `_bind_sidecar_sets`"). Auth must precede mutations for surface-keyed messaging (`auth/mutations.py::bind_auth_mutations`). Folding mutations into the sidecar driver would need mode flags across ledgers.

2. **Primary-ambiguity message unification** — Confirmed reject. Phase-1 `_format_ambiguity_error` is the registry-wide multi-type/no-primary owner (tests pin `"Declare Meta.primary = True..."`). `mutations/sets.py::_resolve_primary_type` and `auth/mutations.py::_resolve_user_primary_or_raise` are bind-surface messages that also cover the *zero-type* case and name mutation/auth factories; they fire after Phase 1 already guaranteed a primary for multi-type models. Same vocabulary fragment, different contract and change axis.

3. **Field-surface name-set extraction** — Challenged then upheld. The three-set union (`__annotations__` | `selected_fields` | `StrawberryField`) appears only at `_audit_field_surface` and `_synthesize_relation_connections`, with an explicit mirror docstring. Collision *policies* differ (empty/group-by-camel audit vs generated `*_connection` name check). No third site package-wide. A private three-line helper would not move a cross-module invariant; under DRY.md (do not optimize for fewer lines / co-located mirror with explicit contract) extraction is not warranted.

4. **Read-type camel audit vs `iter_input_field_collisions`** — Confirmed reject. `_audit_field_surface` uses Strawberry `to_camel_case` on the pre-Phase-3 read surface. Write-input guards use injective `graphql_camel_name` plus input-attr / source axes via `utils/inputs.py::iter_input_field_collisions` (forms/mutations/DRF). Docs already call them parity siblings; unifying would couple materialization paths that must stay distinct.

**Independent missed-consolidation search:** Grepped bind drivers, primary-ambiguity phrases, field-surface unions, `to_camel_case` / `graphql_camel_name`, orphan/owner formatters, cursor validation layering, `strawberry.type` call sites, teardown markers. No additional same-contract / same-change-axis duplication that should consolidate behind a clearer owner. Filter/Order orphan and owner-mismatch formatters remain intentional family-pinned text behind existing hooks.

**Outcome:** verified. Plan checkbox marked `[x]`. No production edits. No pytest.

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
