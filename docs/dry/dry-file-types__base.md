# DRY review: `django_strawberry_framework/types/base.py`

Status: verified

## System trace

`types/base.py` owns the `DjangoType` Meta-class collection pipeline end-to-end at
class-creation time: Meta vocabulary (`ALLOWED_META_KEYS` / `DEFERRED_META_KEYS`),
shape + Relay-Node gates for every supported Meta key, field selection
(`_select_fields`), consumer-override / `auto` handling, annotation synthesis
(`_build_annotations` + pending relations), and registry registration of the
`DjangoTypeDefinition`. Finalization-time stamping and synthesis stay elsewhere
(`types/relay.py` for `effective_globalid_strategy`, `types/finalizer.py` for
relation-connection synthesis / sidecar bind / cursor column checks).

Pipeline owned here:

1. `__init_subclass__` — Meta detection, finalize-gate, `_validate_meta`, field
   selection, optimizer-hint target checks, four-corner consumer overrides +
   `auto` rules, stage-2 Meta-target validators, Relay `id` collision guard,
   `_build_annotations`, definition build, `registry.register_with_definition` /
   `add_pending_relation`, annotation merge, `install_is_type_of`.
2. Module vocabulary — `RELATION_SHAPE_VALUES` / `DEFAULT_RELATION_SHAPE`,
   `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY`, Relay-Node gate
   lead/tail strings, interfaces shape lead-in, non-interface helper table.
3. Shared validators exported for other sources — `_validate_globalid_strategy`
   (Meta + `RELAY_GLOBALID_STRATEGY`), `_is_relay_shaped` (list/connection/node
   factories, inspect command), constants imported by `testing/relay.py` and
   `types/finalizer.py`.

Connected surfaces traced as evidence (siblings still open — not absorbed):

- `types/definition.py` — single construction site for `DjangoTypeDefinition`
  is `__init_subclass__` here; slots are write-once mirrors of validated Meta.
- `types/converters.py` — scalar/file output conversion only; called from
  `_build_annotations`.
- `types/relations.py` — `PendingRelation` / `PendingRelationAnnotation` records.
- `types/relay.py` — GlobalID install / resolve / encode; reuses
  `_validate_globalid_strategy` + `DEFAULT_GLOBALID_STRATEGY`; stamps
  `effective_globalid_strategy` at finalize (not here).
- `types/finalizer.py` — Phase-2.5 synthesis reads `relation_shapes` /
  `cursor_field` / sidecars already validated here; imports
  `DEFAULT_RELATION_SHAPE`.
- `types/resolvers.py` — attaches resolvers using
  `consumer_authored_fields` / `selected_fields` from the definition.
- `registry.py` — registration API only; no Meta validation.
- `connection.py` / `list_field.py` / `relay.py` (package) — field factories
  call `_is_relay_shaped` via `_validate_relay_djangotype_target`; factory error
  wording is intentionally per-factory, not the Meta-key gate strings.
- `keyset.py` — owns cursor reference/column syntax; base calls
  `validate_cursor_field_references` at creation, finalizer calls
  `validate_cursor_field_columns` later.
- `optimizer/hints.py` + walker — consume stored `optimizer_hints`; value shape
  owned by `OptimizerHint`, key/target membership owned here.
- `filters` / `orders` Meta — django-filter-shaped field maps / `__all__`
  expansion; not the DjangoType fields/exclude selector.
- `utils/inputs.py::normalize_field_name_sequence` + mutation/form/serializer
  Meta — write-flavor field sequences (no `__all__`, duplicate rejection,
  flavor-labeled errors); deliberately disjoint from DjangoType collection.
- `mutations/sets.py::reject_unknown_meta_keys` — mutation-family typo guard
  with its own allowed-key sets and message shape; mirrors own-keys-only
  posture but does not share DjangoType's `DEFERRED_META_KEYS` layer.

Item-scoped baseline `8c95cd06f247f3ccc13c20f65e29b24df81023cc`: empty for
`types/base.py` at review start.

## Verification

Package searches covered Meta-key allow-lists, fields/exclude normalization,
`auto` / `StrawberryAuto`, `relation_shapes`, `optimizer_hints`,
`globalid_strategy` / `effective_globalid_strategy`, connection / cursor_field
gates, `_format_unknown_fields_error` / `_selected_meta_targets`, and
`normalize_field_name_sequence` call sites.

Strongest rejected candidates:

1. **`_normalize_fields_spec` / `_normalize_sequence_spec` vs
   `utils/inputs.py::normalize_field_name_sequence`** — same English words
   (`fields` / `exclude`), different contracts. DjangoType accepts
   `"__all__"`, allows sets for set-valued Meta keys, and defers unknown-name /
   duplicate policy to `_select_fields` / later validators. Write flavors reject
   bare strings (including `"__all__"`), require string entries, reject
   duplicates, and use flavor-prefixed messages. Tests pin both shapes
   (`tests/types/test_base.py` vs mutation/form/serializer suites). Unifying
   would need mode flags or behavior change. Rejected.

2. **`_validate_meta` unknown-key scan vs
   `mutations/sets.py::reject_unknown_meta_keys`** — same own-keys-only scan
   idea, different domains. DjangoType also splits `DEFERRED_META_KEYS` before
   unknown keys and raises `"Unknown Meta keys: …"` (pinned). Mutations use
   disjoint allow-lists and `"{name}.Meta has unknown keys: …"`. Folding into
   one helper couples type Meta to write Meta and fights pinned wording.
   Rejected.

3. **`fields`/`exclude` mutual-exclusion messages** (DjangoType vs
   `resolve_effective_fields` / mutation `_validate_meta`) — same invariant,
   different subjects and pinned strings (`"Meta.fields and Meta.exclude are
   mutually exclusive"` vs `"… declares both \`fields\` and \`exclude\`…"`).
   Not one consumer-facing contract. Rejected.

4. **`_validate_filterset_class` / `_validate_orderset_class` near-copies** —
   same subclass-check skeleton, but each wrapper exists to keep a
   cycle-safe local import (`filters.sets` / `orders.sets`). A parameterized
   core would save little and obscure that isolation. No third DjangoType Meta
   sidecar of this shape yet. Rejected as premature / ownership-obscuring.

5. **Meta Relay-Node gate strings vs connection/list/node factory messages** —
   `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` are already shared
   by Meta.connection / cursor_field / globalid_strategy and
   `testing/relay.py::global_id_for`. Factory messages in `connection.py` /
   `list_field.py` are intentionally caller-supplied full strings naming the
   *field* (`DjangoConnectionField`, etc.). Comments already document the
   byte-shape split. Rejected.

6. **`globalid_strategy` validation vs finalize stamping** — already split
   correctly: raw Meta/setting validation is single-sited in
   `_validate_globalid_strategy`; `effective_globalid_strategy` is stamped only
   in `types/relay.py::install_globalid_typename_resolver`. No second validator.
   Rejected (already consolidated).

7. **`optimizer_hints` shape vs `OptimizerHint` construction** — mapping +
   relation-key membership live here; flag/combination legality lives in
   `OptimizerHint.__post_init__`. Two layers of one feature, different change
   axes. Rejected.

8. **Recomputing `_is_relay_shaped` in `_validate_meta` and again in
   `__init_subclass__`** — same single predicate; dual call sites at different
   pipeline stages. Threading a bool through `_ValidatedMeta` would be
   micro-plumbing, not a second rule. Rejected.

9. **Filter/Order Meta `"__all__"` expansion** — django-filter / OrderSet field
   maps, not DjangoType GraphQL field selection. Rejected.

Prior DRY/build/review artifacts were not used as seed; present-day source and
tests only.

## Opportunities

None — Meta collection, vocabulary constants, two-stage Meta-target validation
(`_selected_meta_targets` + family checks), GlobalID strategy validation, and
Relay-shape predicate are already single-sourced at this owner. Apparent
siblings encode different contracts (write-flavor field sequences, mutation Meta
allow-lists, finalize-time stamping) and should keep changing on their own axes.

## Judgment

Zero-edit. `types/base.py` is already the true owner of DjangoType Meta
collection policy; cross-package lookalikes were disproved as intentional
domain splits. Ready for Worker 2.

Deferred (not consolidations; hand to sibling items / maintainer):

- `types/definition.py` class docstring still says absent `relation_shapes`
  keys default to `"both"`; code + `DEFAULT_RELATION_SHAPE` + finalizer use
  `"connection"` (spec-047 Decision 5). Docstring drift on the open
  `definition.py` item — do not “fix” via a helper here.
- Deferred pytest: none run (autonomous DRY item; no production edit).

Scoped diff vs `ITEM_BASELINE` `8c95cd06…`: empty for `types/base.py` and for
this artifact’s production edits (artifact-only create under `docs/dry/`).

## Independent verification (Worker 2)

Re-traced present-day `types/base.py` end-to-end (`__init_subclass__`,
vocabulary, stage-1/2 Meta validators, `_select_fields` / `_build_annotations`)
and independently compared write-flavor field sequences, mutation Meta typo
guards, factory Relay messages, GlobalID validation, and `definition.py` /
finalizer relation-shape defaults. Did not rely on Worker 1’s private notes
beyond this artifact.

**Scoped diff:**
`git diff 8c95cd06f247f3ccc13c20f65e29b24df81023cc -- django_strawberry_framework/types/base.py`
is empty. Zero-edit claim holds for the item target.

**Challenges to rejected candidates (source evidence):**

1. **`_normalize_fields_spec` / `_normalize_sequence_spec` vs
   `utils/inputs.py::normalize_field_name_sequence`** — Confirmed distinct.
   DjangoType accepts `"__all__"`, allows sets on set-valued keys, and defers
   duplicate/unknown policy. Write flavors reject bare strings (incl.
   `"__all__"`), require string entries, reject duplicates, and prefix
   flavor labels. Unifying would need mode flags or behavior change.

2. **`_validate_meta` unknown-key scan vs
   `mutations/sets.py::reject_unknown_meta_keys`** — Same own-keys-only idea;
   DjangoType splits `DEFERRED_META_KEYS` and raises `"Unknown Meta keys: …"`
   (pinned in `tests/types/test_base.py` and the mutation-key-on-DjangoType
   guard in `tests/mutations/test_sets.py`). Mutations raise
   `"{name}.Meta has unknown keys: …"` with disjoint allow-lists. Rejected.

3. **fields/exclude mutual-exclusion messages** — Confirmed different subjects
   and pinned strings (`"Meta.fields and Meta.exclude are mutually exclusive"`
   vs `"… declares both \`fields\` and \`exclude\`…"`). Rejected.

4. **filterset/orderset wrapper pair** — Near-copy subclass checks; each keeps
   a cycle-safe local import (`filters.sets` / `orders.sets`). Parameterizing
   would obscure that isolation for little gain. Rejected.

5. **Meta Relay-Node gate strings vs factory messages** — Meta +
   `testing/relay.py::global_id_for` share `_RELAY_NODE_GATE_LEAD` /
   `_RELAY_NODE_GATE_INHERIT_TAIL`. Factories pass full caller strings naming
   the field (`DjangoConnectionField` / `DjangoNodeField`), with different
   byte shape (`"DjangoType"` / `"DjangoType target"`, parenthesized inherit
   tail). `list_field.py::_validate_relay_djangotype_target` documents the
   intentional split; predicate `_is_relay_shaped` is already shared. Rejected.

6–9. GlobalID single validator, optimizer_hints layering, dual
`_is_relay_shaped` call sites, and Filter/Order `"__all__"` expansion —
re-confirmed as already consolidated or intentionally separate domains.

**Independent consolidation search:** No additional same-contract / same-change-
axis opportunity found. Vocabulary constants
(`ALLOWED_META_KEYS` / `DEFERRED_META_KEYS` / `RELATION_SHAPE_*` /
`STRING_GLOBALID_*` / gate leads) have no second production owner; consumers
import from here. Stage-2 target guards already share
`_selected_meta_targets` + `_format_unknown_fields_error`.

**Deferred docstring:** Confirmed belongs to open `types/definition.py` item.
`DjangoTypeDefinition` docstring still says absent `relation_shapes` keys
default to `"both"`; `DEFAULT_RELATION_SHAPE = "connection"` in `base.py` and
`finalizer.py::_synthesize_relation_connections` (`shapes.get(name,
DEFAULT_RELATION_SHAPE)`) are the live rule (spec-047 Decision 5). Not a
`base.py` consolidation.

**Outcome:** verified. Plan checkbox marked `[x]`. No production edits. No
commit.
