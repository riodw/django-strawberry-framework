# Review: `django_strawberry_framework/types/base.py`

Status: verified

## DRY analysis

- **Defer until `Meta.orderset_class` lands (spec-028-orders-0_0_8 Slice 3).** Six TODO sites (`types/base.py:71-80`, `:109-116`, `:300-302`, `:587-590`, `:666-668`, `:677-678`) form a single coordinated landing — `ALLOWED_META_KEYS` promotion + `_validate_orderset_class` mirror helper + `_ValidatedMeta` slot + `DjangoTypeDefinition` slot + `_validate_meta` call + return tuple slot. Trigger condition is verbatim: "in the same change that wires order binding end to end" (`types/base.py:71-72`). The pseudocode comments already enumerate the consolidation shape; no DRY re-extraction needed before the trigger fires.
- **Defer until a third `consumer_*` set landing or a non-`fields`/`exclude` overlay vector lands.** The four-corner override sets at `types/base.py:223-238` (relation×annotation, relation×assigned, scalar×annotation, scalar×assigned) are computed in two adjacent passes — two `frozenset` comprehensions on `consumer_annotations` (`:223-232`) plus `_consumer_assigned_fields` (`:378-439`) — and then unioned at `:239-246`. Today the two-source split is the right factoring because the assigned branch needs `cls.__dict__` while the annotated branch needs `cls.__annotations__`; a `_collect_consumer_authored_fields(cls, fields) -> tuple[frozenset, ...]` consolidator would only earn its weight when a third source (e.g. method resolvers from `@strawberry.field def`) joins. Quote-able trigger: "a third consumer-authored source (e.g. resolver-method classifier) requires the same four-corner sets".
- **Defer until a second use of the synthesized-id-suppression predicate beyond H1 collision + pk-annotation drop.** `_is_relay_shaped(cls, interfaces)` (`types/base.py:179-190`) is already the act-now extraction's home — two call sites (`:247` and `:892`) reach it today. The next reviewer-attractor would be a third site (e.g. a finalizer-time second-pass audit on Relay shape) where the current two-line predicate `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` could fold into a richer "Relay context" snapshot dataclass. Quote-able trigger: "third caller of `_is_relay_shaped` lands at a different lifecycle phase (finalize-time or schema-build-time)".
- **Cross-folder DRY pair carried forward from `rev-optimizer__field_meta.md`'s act-now bullet.** The `field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}` build at `types/base.py:221` is the canonical site; the mirror at `types/resolvers.py::_field_meta_for_resolver:170-213` falls back to `FieldMeta.from_django_field(field)` for the same Django-field-shape input. Per `rev-optimizer.md` folder-pass calibration, the cross-folder pair belongs at the `rev-types.md` folder pass (second-closing folder) rather than the project pass. Listed here so the folder pass picks it up; do NOT re-extract at per-file scope — `types/base.py`'s caller is one of two consumers and the consolidation lives one layer down.

## High:

None.

## Medium:

### GLOSSARY drift on `DjangoType` and `get_queryset` visibility hook — interfaces validation contract + Relay-`id` collision guard + scalar-column override are not surfaced

The `DjangoType` GLOSSARY entry at `docs/GLOSSARY.md:375-409` enumerates the shipped capability surface but lags three behaviours shipped between `0.0.5` and `0.0.7` that consumers can encounter and that show up in `types/base.py`:

1. The `Meta.interfaces` validator (`types/base.py::_validate_interfaces:493-568`) rejects strings, sets, generators, dicts, `DjangoType` subclasses, duplicates, and non-Strawberry-interface classes with typed `ConfigurationError`s — the entry's bullet just points at the `Meta.interfaces` row and the Relay integration page, leaving the per-`ConfigurationError` shape undocumented.
2. The Relay-shaped `id`-collision guard at `types/base.py::DjangoType.__init_subclass__:247-272` raises two distinct typed `ConfigurationError`s — one for `id = strawberry.field(...)` assignment and one for non-`relay.NodeID[T]` annotations — and the consumer-visible remediation text names four escape hatches (`@classmethod resolve_id`, `id: relay.NodeID[<pk_type>]`, resolver-backed sibling field, or remove `relay.Node`). The entry does not surface this contract.
3. The scalar-column consumer-assignment branch (`types/base.py::_consumer_assigned_fields:378-439`, four-corner contract) lets consumers write `description = strawberry.field(resolver=...)` on a scalar column with the same override semantics as relation columns; the entry's "shipped capability" list still frames overrides through "relation annotation generation" only.

Why it matters: `DjangoType` is the package's primary public surface (the entry says so at `:379`) and these three branches are all consumer-visible `ConfigurationError`-shaped contracts — a consumer reading the GLOSSARY entry cannot tell that (a) declaring `interfaces = "Node"` raises a specific message, (b) overriding the Relay `id` field has four documented escape hatches, or (c) a `description = strawberry.field(...)` on a scalar column is supported with the same shape as the relation case.

Recommended change: append a "Validation contracts" sub-list to the `DjangoType` GLOSSARY entry naming the three contract surfaces with brief one-line citations. Verbatim replacement prose (Worker 2 lifts directly):

> Validation contracts (errors surface as [`ConfigurationError`](#configurationerror) at type-creation time):
>
> - **`Meta.interfaces` shape and contents.** Tuple/list of Strawberry interface classes, or a single interface class. Strings, sets, dicts, generators, `DjangoType` subclasses, duplicates, and non-`@strawberry.interface` / non-`relay`-interface classes are rejected with messages naming the offending value.
> - **Relay-`id` collision guard.** When the type is Relay-Node-shaped (via `Meta.interfaces = (relay.Node,)` or direct inheritance), declaring `id = strawberry.field(...)` or an `id` annotation that is not `relay.NodeID[<pk_type>]` raises. Escape hatches: `@classmethod resolve_id` for a custom id resolver, `id: relay.NodeID[<pk_type>]` for a custom id annotation, a resolver-backed sibling field (e.g. `display_id`) for GraphQL field-level metadata, or remove `relay.Node` from `Meta.interfaces`.
> - **Consumer-override surface (scalar and relation, annotation and assignment).** A consumer-written annotation (`category: AdminCategoryType`, `description: int`) or `strawberry.field(...)` assignment (`category = strawberry.field(resolver=...)`, `description = strawberry.field(resolver=...)`) on either a relation column or a scalar column is preserved; the four cases collectively form the `consumer_authored_fields` short-circuit. Non-`StrawberryField` class attributes that shadow a Django field name raise with a message naming the field, the column kind, and the remediation.

A separate small forward applies to the `get_queryset` visibility hook entry at `docs/GLOSSARY.md:515-536`: the entry says "`has_custom_get_queryset()` reports whether a type or inherited intermediate base overrides the hook" but does not surface the `0.0.7` fix that **abstract bases without `Meta`** also flip the sentinel through inheritance (`types/base.py:201-208` comment + `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_abstract_base_without_meta:705-738`). The fix sentence already names "or inherited intermediate base", which is technically accurate, but a consumer reading the entry would not know that the abstract-base-without-`Meta` pattern works at all. Worker 2 may bundle this into the same edit by adding one sentence to that entry: "Inheritance through an abstract base that overrides `get_queryset` without declaring `Meta` is supported — the sentinel flip runs before the `meta is None` early-return so the abstract-shared-base pattern reports correctly on concrete subclasses."

```django_strawberry_framework/types/base.py:201-272
# (Excerpt — see source for full body)
# Lines 201-208: sentinel stamped BEFORE meta-is-None early return
# Lines 247-272: Relay-shaped id collision guard with four escape hatches
# Lines 493-568: _validate_interfaces — string / non-sequence / non-interface / DjangoType / duplicate rejections
```

### `_validate_optimizer_hints` second-branch error message understates the "field exists but is not a selected relation" case

`_validate_optimizer_hints` (`types/base.py:682-742`) runs two field-name guards in sequence: (1) unknown-on-model at `:717-726` (legitimate typo), then (2) excluded-or-scalar at `:727-736`. Both use `_format_unknown_fields_error(..., attr="optimizer_hints", unknown=…, available=…)`. The first error's `available` is `valid_field_names` (every model field name); the second's `available` is `selected_relation_names`. The resulting message for an excluded-relation OR selected-scalar hint reads:

> Category.Meta.optimizer_hints names unknown fields: ['name']. Available: ['items', 'properties'].

…where `'name'` is a real Django scalar field that the consumer correctly identified, but the error labels it "unknown fields" and surfaces an "Available" list that omits it. The consumer's mental model is "I know `name` exists; why is it unknown?" The message is technically truthful (the second pass treats `selected_relation_names` as the valid surface), but the diagnostic is misleading: a consumer who hint-keyed a real scalar reads "unknown fields" when the actual rejection reason is "not a selected relation".

Why it matters: this branch is exercised by two tests (`tests/types/test_base.py::test_meta_optimizer_hints_for_excluded_field_raises:349-362` and `:test_meta_optimizer_hints_for_selected_scalar_field_raises:365-372`) and both currently pin the misleading message via `match="optimizer_hints names unknown fields"`. The walker's contract ("hints only fire on relation branches" — docstring `:688-691`) is the actual rejection reason, but the consumer never sees it.

Recommended change: split the second branch into a dedicated error helper (or a third `attr` variant) so the message names the actual reason. Suggested shape:

```python
excluded_hint_fields = sorted(set(hints) - selected_relation_names)
if excluded_hint_fields:
    raise ConfigurationError(
        f"{model.__name__}.Meta.optimizer_hints names fields that are not selected "
        f"relations: {excluded_hint_fields}. Available selected relations: "
        f"{sorted(selected_relation_names)}. (Hints only fire on relation branches; "
        f"excluded fields and selected scalar fields are unreachable.)",
    )
```

Update the two pinning tests to `match=r"not selected relations"` (or a similarly specific substring) so the pin reflects the corrected diagnostic. Severity Medium because the error is consumer-visible at type-creation time and the misleading framing actively hides the contract the docstring already names.

```django_strawberry_framework/types/base.py:727-736
excluded_hint_fields = sorted(set(hints) - selected_relation_names)
if excluded_hint_fields:
    raise ConfigurationError(
        _format_unknown_fields_error(
            model=model,
            attr="optimizer_hints",
            unknown=excluded_hint_fields,
            available=selected_relation_names,
        ),
    )
```

## Low:

### Citation: `_id_annotation_is_relay_node_id` docstring history reference is unanchored

The `_id_annotation_is_relay_node_id` docstring at `types/base.py:137-172` includes the prose "`typing.get_type_hints` handles nested forward references differently across 3.10 vs 3.11+, which previously left a code branch reachable only on the newer interpreter — that divergence is gone." This is a historical comparison (interpreter-divergent branch) without a spec or test anchor. The reasoning is correct but the audit-trail surface (which test pins the divergence, which release fixed it) is implicit. Same calibration as the `OptimizerHint.__post_init__` historical-framing Low in `rev-optimizer__hints.md`.

Recommended change at comment-pass time: replace "that divergence is gone" with a specific anchor — either the test name (e.g. `Pinned by tests/types/test_base.py::test_id_annotation_via_get_type_hints_path_returns_true_for_string_annotation`-style) or the release identifier where the unification landed, so a future maintainer reading the docstring can grep for the test or release without code archaeology. Defer to comment pass.

### Citation: `_consumer_assigned_fields` docstring's four-corner enumeration is the canonical override-contract doc but is buried inside an internal helper

`_consumer_assigned_fields:382-419` carries a 37-line docstring that is the single canonical home for the four-corner override contract (relation×annotation, relation×assigned, scalar×annotation, scalar×assigned). The contract is what `_build_annotations:872-952` reads via `consumer_authored_fields`, but the docstring lives on the helper that produces only two of the four corners (the assigned pair). A consumer or future maintainer auditing the override contract would not find this docstring from `_build_annotations` or `DjangoType.__init_subclass__` — those reference the four-set union but not the contract itself.

Recommended change at comment-pass time: either (a) hoist a one-paragraph summary of the four-corner contract to a module-level constant docstring or to `DjangoType.__init_subclass__`'s docstring with a back-reference to `_consumer_assigned_fields` for the full contract, OR (b) cite `_consumer_assigned_fields` by `path::QualifiedName` from both the `__init_subclass__` site (`:233-238`) and the `_build_annotations` branch (`:904`, `:937`) so the four-corner contract is discoverable from every consumer of the union. Defer to comment pass; not behaviour-changing.

### Citation: `_validate_meta` docstring's "Decision 4" reference to `_validate_interfaces` is opaque

`_validate_meta:606-607` says "If `Meta.interfaces` is declared, validate it per `_validate_interfaces` (Decision 4)." The "(Decision 4)" anchor is not qualified by spec — a future maintainer can grep `docs/SPECS/` for "Decision 4" and hit dozens of matches across `spec-011`, `spec-018`, `spec-021`, etc. Same citation-hygiene calibration as the `spec-014 → spec-018` drift filed at `rev-optimizer__extension.md` and `rev-optimizer__walker.md` — the reasoning is correct but the pointer is too short.

The actual home is `docs/SPECS/spec-011-django_type-0_0_5.md` (Relay-Node integration spec). Confirmed by the `_validate_interfaces` docstring at `:498-501` which cites `spec-011 #"An empty tuple is the same as not declaring"` and `:501 spec-011 #"may be a tuple/list of interface classes"` — those are anchored correctly; only the `_validate_meta` docstring's parent-level "Decision 4" reference lacks the `spec-011` qualifier.

Recommended change at comment-pass time: replace "(Decision 4)" with "(spec-011 Decision 4)" so the citation is greppable. Defer to comment pass.

### Citation: `_NODEID_STRING_RE` regex docstring duplicates the rationale across two docstrings

`_NODEID_STRING_RE` (`types/base.py:119`) is named but undocumented at the module level; its full rationale (string vs resolved-object forms, the `(?:^|\.)` anchor purpose) lives in `_id_annotation_is_relay_node_id:138-172`. The regex itself is at module scope so a maintainer searching by symbol finds the bare pattern; the explanation lives one definition down. Two prose-of-truth sites for the same rule is a brittleness signal — same calibration as the `nullable` field docstring / inline-comment-block drift recorded in `rev-optimizer__field_meta.md`.

Recommended change at comment-pass time: add a one-line module-level comment (or a `# Regex notes:` block immediately above `_NODEID_STRING_RE`) pointing at `_id_annotation_is_relay_node_id` for the full rationale, OR move the regex inside the function so the only docstring covering it is the one that uses it. Defer to comment pass; the duplication is intentional sibling design today but the contract framing is one-sided.

### Forward-looking: `_validate_interfaces` runs O(N) `issubclass(entry, DjangoType)` over every entry — table-driven validation deferred until a second multi-rule entry-walker lands

`_validate_interfaces:535-563` runs five per-entry rules in sequence: string rejection, type check, `DjangoType` subclass rejection, `__strawberry_definition__.is_interface` check, duplicate detection. Each is a small `if` inside the loop; the structure mirrors `_validate_optimizer_hints`'s sequential-pass shape. Today the five-rule walk reads cleanly; a future addition (e.g. composite-pk interface gating from `finalize_django_types()`) would tip the loop body past the readable single-screen threshold.

Recommended change: defer until a sixth per-entry rule lands OR a second entry-walker with overlapping rules (e.g. `_validate_orderset_class` per-entry rules in spec-028 Slice 3) appears. At that point factor a `_validate_interface_entry(entry, meta, seen_ids)` helper that returns a `(name, is_duplicate)` tuple and lifts the rule body to a single-screen block. Trigger condition verbatim: "sixth per-entry rule lands in `_validate_interfaces` OR `_validate_orderset_class` adds a parallel per-entry validation loop with two-or-more shared rules". Defer.

### Forward-looking: `_consumer_assigned_fields` rejects non-`StrawberryField` class attributes that shadow a Django field, but the error message names the kind (relation/scalar) without surfacing the attribute's actual type — diagnostic could be richer when a third shadow-type lands

`_consumer_assigned_fields:432-438` raises a `ConfigurationError` with `f"{cls.__name__}.{field.name} shadows a Django {kind} field with an unsupported class attribute."` The error names the field, the kind, and the remediation, but does not surface `type(value).__name__` — so a consumer who accidentally wrote `name = "Bob"` (a string default) sees "unsupported class attribute" without a hint that `str` is the offending type.

Recommended change: defer until a third shadow-type pattern emerges in the wild (consumer reports, common-mistake bug reports) OR until a similar `type(value).__name__` enrichment lands elsewhere in the package. At that point append `f"got {type(value).__name__}"` to the message. Trigger condition verbatim: "third consumer report of `_consumer_assigned_fields` confusion lands in `docs/feedback*.md` OR a sibling validator (`_validate_filterset_class`, `_validate_interfaces`) adopts a `got {type(value).__name__}` pattern". Defer.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_format_unknown_fields_error` (`types/base.py:460-474`) is the single source of truth for "unknown fields … Available: …" error shape across `Meta.fields` (`:790-795`), `Meta.exclude` (`:802-806`), and `Meta.optimizer_hints` (twice — `:720-725` and `:730-735`); `_interfaces_shape_error` (`:483-490`) + `_INTERFACES_SHAPE_ERROR_LEAD_IN` (`:477-480`) consolidate the two interfaces-shape rejection sites at `:524` and `:530`; `_is_relay_shaped` (`:179-190`) is the single Relay-shape predicate consumed at the H1 collision guard (`:247`) and the pk-annotation suppression branch (`:892`); `_meta_optimizer_hints` (`:442-457`) is the single shape gate consumed by `_validate_meta:663`. `_ValidatedMeta` NamedTuple (`:571-590`) is the snapshot dataclass that prevents `__init_subclass__` from re-reading `getattr(meta, ...)` for the same keys and re-running the shape gates — pinned by `tests/types/test_base.py::test_select_fields_signature_accepts_validated_specs:250-269`.
- **New helpers considered.** A `_collect_consumer_authored_fields(cls, fields)` four-set consolidator was evaluated and rejected: the two-source split is the right factoring today because the assigned branch needs `cls.__dict__` and the annotated branch needs `cls.__annotations__`; folding them through a single helper would force the union into one walk and split the two cleanly-separated lookups across an internal dispatch. Deferred with explicit trigger in `## DRY analysis`. A table-driven `_validate_interface_entry` helper was evaluated and deferred — the five-rule sequential walk is single-screen-readable today; trigger noted in `## Low:` and `## DRY analysis`. A symbol-level `_NODEID_STRING_RE` rationale comment was considered to dedupe the rule-restatement across two prose sites; deferred to comment pass per `## Low:`.
- **Duplication risk in the current file.** `consumer_annotations = dict(cls.__annotations__)` (`:222`) and the subsequent `cls.__annotations__["id"]` read in `_id_annotation_is_relay_node_id:173` are two reads of the same dict but at different lifecycle phases (collection time vs guard time) — intentional sibling design because the H1 guard runs after `_validate_meta` but before annotation synthesis; folding through a shared cache would require threading `consumer_annotations` through `_id_annotation_is_relay_node_id` against the docstring contract that promises "Reads `cls.__annotations__` directly — no `typing.get_type_hints` call" (`:140-141`). `meta.__dict__` (`:633`) vs MRO-walking `getattr` (`:642-643`, `:647`, `:661-665`) is documented at `:626-632` as intentional counterpart-by-purpose ("do not 'unify' them"). Same calibration as the `apply_sync`/`apply_async` mirror calibration in `rev-filters__sets.md`.

### Other positives

- **Sentinel-before-early-return ordering.** The `_is_default_get_queryset` flip at `:207-208` runs BEFORE the `meta is None` early-return at `:209-211`, and the docstring at `:201-206` explains the load-bearing reason (abstract-shared-base pattern). Pinned by `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_abstract_base_without_meta:705-738`, which the test docstring explicitly identifies as "used to be a P1 bug" and ties to the fix.
- **Local-import-for-cycle-break shape.** `_validate_filterset_class:99` reads `from ..filters.sets import FilterSet` at function scope; the surrounding docstring at `:86-94` and the inline comment at `:97-98` both name the cycle (`types -> filters -> types`) the local import dodges, with explicit "Do NOT hoist to module top" guidance. The pseudocode comment at `:79-80` reaffirms the same shape will be reused for `_validate_orderset_class`.
- **Relay-`id` collision guard's four-escape-hatch error message.** The error at `:252-264` names every viable escape hatch (`@classmethod resolve_id`, `id: relay.NodeID[<pk_type>]`, resolver-backed sibling field, remove from `Meta.interfaces`) and warns about the metadata-only-sibling pitfall ("a metadata-only sibling without a resolver builds but fails at query time"). This is the kind of consumer-visible error message that pre-empts a support-ticket cluster.
- **`_validate_optimizer_hints` model-threading.** The Args block at `:706-710` explicitly documents that earlier shapes inferred the model from `fields[0].model` and `IndexError`'d when `Meta.exclude` covered every field; the fix threads `meta.model` through. Pinned by `tests/types/test_base.py::test_meta_optimizer_hints_with_empty_field_selection_raises_configuration_error:375-398`.
- **`_select_fields` separation of shape-gates from selection.** The function consumes the already-normalized `fields_spec` / `exclude_spec` from `_ValidatedMeta` so the shape gates run exactly once per class. The docstring at `:760-764` names the invariant explicitly; pinned by `tests/types/test_base.py::test_select_fields_signature_accepts_validated_specs:250-269`.
- **Six TODOs all reference the same spec slice (spec-028-orders-0_0_8 Slice 3) with full pseudocode bodies.** The TODOs at `:71-80`, `:109-116`, `:300-302`, `:587-590`, `:666-668`, `:677-678` are AGENTS.md-compliant TODO-anchored pseudo blocks (ERA001-exempt per AGENTS.md rule 18). The pseudocode bodies enumerate the consolidation surface (`_validate_orderset_class`, `_ValidatedMeta` slot, definition slot, validator call, return tuple slot) so a future author has the complete landing plan in-source. The `tests/types/test_base.py:224-231` test-side TODO pairs with `:71-80`'s source-side TODO.
- **Comment audit-trail tying source to test pin.** The 6-line comment at `:201-206` ends with `Pinned by ``test_has_custom_get_queryset_inherits_through_abstract_base_without_meta``.` — the test name is the load-bearing audit anchor, and the test file's docstring (`tests/types/test_base.py:705-718`) reciprocally documents "used to be a P1 bug". This bidirectional anchor is the gold-standard shape for non-obvious behaviour.
- **Static helper hotspots all justified.** `_validate_interfaces:493-568` (76/13) is dispatch-shaped (five sequential per-entry rules + the top-level shape rejection); `_build_annotations:814-952` (139/8) splits cleanly into the suppression-prelude + per-field dispatch loop with the two-branch (`is_relation` / scalar) body explicitly commented for both branches' consumer-override short-circuit; `DjangoType.__init_subclass__:198-309` (112/9) is the pipeline spine documented in the module docstring's five-step enumeration (`:13-25`). Each hotspot's branches are individually pinned by focused tests in `tests/types/test_base.py` and `tests/types/test_definition_order*.py`.
- **GLOSSARY drift quick-check.** `Meta.model` (`docs/GLOSSARY.md:650-656`), `Meta.fields` (`:598-604`), `Meta.exclude` (`:590-596`), `Meta.primary` (`:708-725`), `Meta.optimizer_hints` (`:666-689`), `Meta.filterset_class` (`:614-627`), `Meta.interfaces` (`:629-648`), `Meta.name` (`:658-664`), `Meta.description` (`:582-588`), and `Meta.orderset_class` (`:691-706`, `planned for 0.0.8`) all align with their per-`Meta`-key handling in `types/base.py`. Only the `DjangoType` umbrella entry (`:375-409`) lags on the three behaviours called out in `## Medium:` and the `get_queryset` entry (`:515-536`) lags one sentence on the abstract-base path. No additional Meta-key entries drift.

### Summary

`types/base.py` is the package's primary public surface and the file reads accordingly — a five-step pipeline in `DjangoType.__init_subclass__`, eight `_validate_*` / `_normalize_*` / `_select_*` / `_build_*` helpers that each own a single contract, a `_ValidatedMeta` NamedTuple that prevents shape-gate re-evaluation, and four canonical error-shape consolidators (`_format_unknown_fields_error`, `_interfaces_shape_error` + `_INTERFACES_SHAPE_ERROR_LEAD_IN`, `_meta_optimizer_hints`, `_is_relay_shaped`) that pin the consumer-visible error surface. Zero High; two Mediums (`DjangoType` + `get_queryset` GLOSSARY drift bundled per shape #4; misleading `_validate_optimizer_hints` second-branch error message); six Lows split across citation hygiene (`_id_annotation_is_relay_node_id` history reference, `_consumer_assigned_fields` docstring-discoverability, `_validate_meta`'s "Decision 4" pointer, `_NODEID_STRING_RE` rationale-duplication) and two forward-looking deferrals with explicit triggers (`_validate_interface_entry` extraction; richer `_consumer_assigned_fields` error). The cross-folder `FieldMeta._from_field_shape` DRY pair carried forward from `rev-optimizer__field_meta.md` is restated in `## DRY analysis` so the `rev-types.md` folder pass (the second-closing folder per the optimizer-pass calibration) picks it up. Six TODO blocks all wait on the same `spec-028-orders-0_0_8 Slice 3` trigger; the coordinated landing is the right scope for picking them up together. Standard three-spawn cycle (shape #4 collapse at Worker 2 because the Medium-GLOSSARY edit is paired with comment-pass Lows). `Status: under-review`.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/types/base.py::_validate_optimizer_hints #"excluded_hint_fields = sorted"` — replaced the `_format_unknown_fields_error` call in the second branch with a dedicated `ConfigurationError` message that names the actual rejection reason ("not selected relations") and surfaces the docstring-named contract ("Hints only fire on relation branches; excluded fields and selected scalar fields are unreachable."). The first branch (unknown-on-model typo guard) still routes through `_format_unknown_fields_error` so the shared `Meta.fields` / `Meta.exclude` shape is preserved for the typo case. Matches the artifact's suggested-shape verbatim.

### Tests added or updated
- `tests/types/test_base.py::test_meta_optimizer_hints_for_excluded_field_raises` — flipped `match=` from `"optimizer_hints names unknown fields"` to `"not selected relations"` to pin the corrected diagnostic.
- `tests/types/test_base.py::test_meta_optimizer_hints_for_selected_scalar_field_raises` — same flip.
- `tests/types/test_base.py::test_meta_optimizer_hints_with_empty_field_selection_raises_configuration_error` — same flip. This third test also exercises the second branch (`Meta.exclude` covers every field → `selected_relation_names` is empty → first branch passes because `items` is still in `valid_field_names`, second branch fires); the artifact's per-Medium text counted "two tests" but the empty-`fields` test at `:375-398` hits the same branch and its `match=` would have broken under the new message. Updated for consistency.

### Validation run
- `uv run ruff format .` — pass / 213 files unchanged
- `uv run ruff check --fix .` — pass / All checks passed
- Did not run pytest (Worker 2 hard rule). The three updated `match=` patterns are substrings of the new error string `"...names fields that are not selected relations: ..."` so the `pytest.raises(..., match=...)` regex check passes by construction.

### Notes for Worker 3
- Artifact's per-Medium text named only two tests (`:349-362` and `:365-372`); a third test (`:375-398`) also exercises the second branch and required the same `match=` flip. Contradicting evidence: with `Meta.exclude` covering every field on `Category`, `valid_field_names` still contains `"items"` (from `model._meta.get_fields()`), so `unknown_hint_fields` is empty → first branch skipped → second branch fires with the new "not selected relations" message. Updated the third test's `match=` for the same reason; this is not a false-premise rejection of the Medium, only a wider-than-named impact surface.
- M1 (GLOSSARY drift on `DjangoType` + `get_queryset`) intentionally untouched this pass per dispatch ("Logic-pass scope is M2 only; M1 will be picked up in comment pass").
- All Lows untouched this pass per dispatch (deferred to comment pass).
- `uv.lock` unchanged.
- Many sibling files dirty in the working tree (other `rev-*.md` artifacts, builder docs, `tests/orders/*`, etc.); presumptively concurrent maintainer work per `AGENTS.md` #33. Left untouched.

---

## Verification (Worker 3)

### Logic verification outcome

M2 addressed at `django_strawberry_framework/types/base.py::_validate_optimizer_hints #"excluded_hint_fields = sorted"`. The second branch now raises a dedicated `ConfigurationError` (not routed through `_format_unknown_fields_error`) with the verbatim message shape from the artifact's recommendation: `"{model.__name__}.Meta.optimizer_hints names fields that are not selected relations: {excluded_hint_fields}. Available selected relations: {sorted(selected_relation_names)}. (Hints only fire on relation branches; excluded fields and selected scalar fields are unreachable.)"`. The first branch at `:717-726` (`unknown_hint_fields` typo guard) remains unchanged and still calls `_format_unknown_fields_error(..., attr="optimizer_hints", unknown=unknown_hint_fields, available=valid_field_names)`, preserving the shared `Meta.fields` / `Meta.exclude` shape.

Three pinning tests updated in `tests/types/test_base.py` — `test_meta_optimizer_hints_for_excluded_field_raises:349-362`, `test_meta_optimizer_hints_for_selected_scalar_field_raises:365-372`, and `test_meta_optimizer_hints_with_empty_field_selection_raises_configuration_error:375-398` all flip `match="optimizer_hints names unknown fields"` → `match="not selected relations"`. Worker 2's note on the third test's wider-than-artifact-named impact is the correct call: with `Meta.exclude` covering every field on `Category`, `valid_field_names` still contains `"items"` so the first branch passes and the second branch fires under the new message — verified by reading `_validate_optimizer_hints` at `:712-734` and the test body's `fields = []` + `exclude = ()` shape. Not a false-premise rejection; legitimate widening of the artifact's named impact surface.

M1 (GLOSSARY drift) intentionally untouched this pass per dispatch scope ("M1 will be picked up in comment pass"). All Lows likewise deferred.

### DRY findings disposition

All four DRY items in the artifact are forward-looking deferrals or cross-folder forwards. None require in-cycle action. Carried forward as documented.

### Temp test verification

No temp tests created. Focused-run `uv run pytest tests/types/test_base.py -x -k "optimizer_hints"` returned `4 passed, 57 deselected` (the global coverage gate fires under the focused-k filter, which is expected and not a cycle signal). All three updated pinning tests passed under the new `match=` substring.

### Validation spot-checks

- `uv run ruff format --check django_strawberry_framework/types/base.py tests/types/test_base.py` — `2 files already formatted`
- `uv run ruff check django_strawberry_framework/types/base.py tests/types/test_base.py` — `All checks passed!`
- Diff scope is exactly the M2 hunk (one branch swap in `base.py`) plus three `match=` flips in `test_base.py`; no drive-by edits.

### Verification outcome

logic accepted; awaiting comment pass

### Verification (Worker 3, comment pass)

#### Comment/docstring outcome

M1 GLOSSARY edits land char-for-char per the artifact's verbatim replacement prose:

- `docs/GLOSSARY.md` `DjangoType` entry — the three-bullet "Validation contracts" sub-list (Meta.interfaces shape and contents; Relay-`id` collision guard with four escape hatches; consumer-override surface for all four corners) is appended after the `Meta` validation paragraph and before the `**See also:**` footer. Bullet text matches the artifact's preserved-verbatim block including punctuation, em-dashes, and the bold-lead-in formatting.
- `docs/GLOSSARY.md` `get_queryset` entry — the abstract-base-without-`Meta` sentinel-flip sentence is appended to the load-bearing paragraph per the artifact's small forward.

Cited as the comment-pass surfaces in Worker 2's `## Files touched`; both edits are visible in `git diff -- docs/GLOSSARY.md` at the cycle's claimed sites.

Four citation-hygiene Lows land cleanly:

- Low #1 (`_id_annotation_is_relay_node_id` history reference) — the "that divergence is gone" prose is replaced with both a load-bearing reason ("the no-`get_type_hints` rewrite eliminated the divergence") AND a grep-discoverable test citation. The cited test `tests/types/test_definition_order.py::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` grep-resolves at `tests/types/test_definition_order.py:751`.
- Low #2 (`_consumer_assigned_fields` four-corner discoverability) — a 5-line comment added at the `__init_subclass__` union site (`base.py:255-259`) names the four-corner contract and cites `_consumer_assigned_fields` as the canonical docstring. The cross-reference completes the discoverability path from the consuming site to the contract docstring.
- Low #3 (`_validate_meta`'s "Decision 4" citation opacity) — bare `(Decision 4)` at `base.py:623` is replaced with `(spec-011 Decision 4)`. The `spec-011` qualifier matches the existing `_validate_interfaces` docstring citations at `:517` and `:520`.
- Low #4 (`_NODEID_STRING_RE` rationale-duplication) — a 6-line module-level comment (`base.py:126-132`) names the qualified/unqualified split, the prefixed-substring rejection rationale, and points at `_id_annotation_is_relay_node_id` for the full string-vs-resolved contract. Worker 2 chose option (a) (module-level comment, keep regex at module scope) over (b) (move into function) to preserve the import-time-compile semantics — the right call for a frequently-compiled regex.

Lows #5 (`_validate_interface_entry` table-driven extraction) and #6 (richer `_consumer_assigned_fields` error) deferred per the artifact's own verbatim triggers ("sixth per-entry rule lands in `_validate_interfaces` OR `_validate_orderset_class` adds a parallel per-entry validation loop with two-or-more shared rules"; "third consumer report of `_consumer_assigned_fields` confusion lands in `docs/feedback*.md` OR a sibling validator adopts a `got {type(value).__name__}` pattern"). Both deferrals are pre-authorized by the artifact's forward-looking phrasing.

#### Concurrent maintainer work attribution

`django_strawberry_framework/types/base.py` carries additional hunks that are NOT this cycle's edits: the `_validate_orderset_class` helper at `:98-123`, the `orderset_class` promotion from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`, the removal of six TODO blocks (`:71-80`, `:109-116`, `:300-302`, `:587-590`, `:666-668`, `:677-678` per the artifact's pseudocode enumeration), the `validated.orderset_class` thread-through in `_validate_meta` and the `DjangoTypeDefinition` constructor call, and the `orderset_class: type | None` slot on `_ValidatedMeta`. Per AGENTS.md #33 this is presumptively a concurrent dev's spec-028 Slice 3 landing — the artifact's `## DRY analysis` "defer until ``Meta.orderset_class`` lands" coordinated-landing trigger is firing in someone else's branch. Worker 2 correctly left those hunks untouched and flagged them in `## Notes for Worker 3`. The cycle's edits are scoped exactly to the named comment-pass surfaces and do NOT overlap with the orderset-class landing.

#### Validation spot-checks

- `uv run ruff format --check docs/GLOSSARY.md django_strawberry_framework/types/base.py` — Worker 2 claims clean; ruff format does not touch GLOSSARY.md (markdown) but the `base.py` hunks are well-formatted on visual inspection (no trailing whitespace, blank-line separators, consistent indentation).
- `uv run ruff check django_strawberry_framework/types/base.py` — Worker 2 claims clean; the comment-only additions plus the verbatim docstring expansions do not introduce any lint surface (no new imports, no signature changes, no logic edits).

#### Verification outcome

comments accepted; awaiting changelog disposition

### Verification (Worker 3, terminal pass)

#### Changelog disposition outcome

`Warranted but deferred to maintainer`. `git diff -- CHANGELOG.md` is empty — no edit landed. The disposition's "real consumer-visible change" framing is honest: M2 changes the consumer-visible error message at a public-API validation site (`DjangoType.Meta.optimizer_hints`), and a consumer who asserted on the prior `"unknown fields"` substring for the excluded-or-scalar branch would need to update. The exception type and the first-branch (unknown-on-model typo) shape are unchanged; only the second-branch message text moves. This matches the `filters/base.py` (typed `TypeError` on `RelatedFilter(lookups=...)`) and `filters/sets.py` (`apply_async` bullets) precedents the disposition explicitly cites.

The `### Suggested CHANGELOG entry` block at the artifact's lines 643-659 is verbatim maintainer-ready text under a fenced `markdown` block, placed under `[Unreleased] ### Changed`, covering M2's message change at the error site — names the symbol (`DjangoType.Meta.optimizer_hints` validation, `types/base.py::_validate_optimizer_hints`), the two distinct rejection-reason shapes (legacy `"…names unknown fields: …"` for typos preserved, new `"…names fields that are not selected relations: …. Available selected relations: …. (Hints only fire on relation branches; excluded fields and selected scalar fields are unreachable.)"` for the excluded-or-scalar case), the consumer-action remediation ("update to `\"not selected relations\"`"), and cites all three pinning tests. The maintainer can lift the entry at release time without re-derivation.

The active plan does not authorize a `CHANGELOG.md` edit this cycle per `review-0_0_7.md` silence, and the package is pre-alpha (maintainer owns CHANGELOG cadence). Both citations for the deferral are present (worker-2.md three-state disposition rule + active-plan silence).

#### Validation spot-checks

- `uv run ruff format --check django_strawberry_framework/types/base.py tests/types/test_base.py` — `2 files already formatted`
- `uv run ruff check django_strawberry_framework/types/base.py tests/types/test_base.py` — `All checks passed!`
- `uv run pytest tests/types/test_base.py -x -k "optimizer_hints" --no-cov` — `4 passed, 57 deselected` (all three updated `match=` assertions plus the unchanged `must_be_mapping` test).
- `git diff -- CHANGELOG.md` — empty (matches the `Warranted but deferred to maintainer` requirement).

#### Concurrent maintainer work attribution

The `django_strawberry_framework/types/base.py` diff additionally carries the spec-028-orders-0_0_8 Slice 3 orderset_class landing (`_validate_orderset_class` helper, `ALLOWED_META_KEYS` promotion, six TODO removals, `_ValidatedMeta` and `DjangoTypeDefinition` slot threads). Per AGENTS.md #33 this is concurrent maintainer work in someone else's branch; the artifact's `## DRY analysis` "defer until ``Meta.orderset_class`` lands" coordinated-landing trigger is firing externally. The same concurrent work also touches `tests/types/test_base.py` (parametrize list trim + new `test_meta_orderset_class_is_promoted_to_allowed_meta_keys`). Worker 2 correctly left those hunks untouched at both passes; the cycle's edits remain scoped to (a) the M2 logic shift in `_validate_optimizer_hints` + three `match=` flips, (b) the M1 GLOSSARY append edits, and (c) the four Low citation-hygiene comment edits.

#### Verification outcome

cycle accepted; verified

---

## Comment/docstring pass

### Files touched
- `docs/GLOSSARY.md` `#"## ``DjangoType``"` — appended the verbatim "Validation contracts" sub-list (three bullets: `Meta.interfaces` shape and contents, Relay-`id` collision guard with four escape hatches, consumer-override surface for all four corners) to the `DjangoType` entry per the artifact's M1 replacement prose.
- `docs/GLOSSARY.md` `#"## ``get_queryset`` visibility hook"` — appended the abstract-base-without-`Meta` sentinel-flip sentence to the entry per the artifact's M1 small forward.
- `django_strawberry_framework/types/base.py::_id_annotation_is_relay_node_id #"that divergence"` — replaced "that divergence is gone" with a "no-`get_type_hints` rewrite eliminated the divergence" anchor and cited pinning test `tests/types/test_definition_order.py::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` so the audit trail is grep-discoverable (Low #1).
- `django_strawberry_framework/types/base.py #"_NODEID_STRING_RE = re.compile"` — added a 6-line module-level comment above the regex naming the qualified/unqualified split, the prefixed-substring rejection rationale, and pointing at `_id_annotation_is_relay_node_id` for the full string-vs-resolved contract (Low #4: `_NODEID_STRING_RE` rationale-duplication).
- `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"consumer_authored_fields = frozenset"` — added a 5-line comment above the union site naming the four-corner contract and pointing at `_consumer_assigned_fields` for the full enumeration (Low #2: four-corner discoverability).
- `django_strawberry_framework/types/base.py::_validate_meta #"validate it per"` — replaced bare `(Decision 4)` with `(spec-011 Decision 4)` so the citation is greppable (Low #3).

### Per-finding dispositions
- Medium 1 (GLOSSARY drift on `DjangoType` + `get_queryset`): edited per the verbatim replacement prose. `DjangoType` entry gains the three-bullet "Validation contracts" sub-list at the foot of its body block; `get_queryset` entry gains the one-sentence abstract-base note appended to its load-bearing paragraph.
- Medium 2 (`_validate_optimizer_hints` second-branch error message): logic pass already shipped; no comment-pass action needed.
- Low #1 (`_id_annotation_is_relay_node_id` history reference anchor): citation hygiene fix applied — test name now grep-discoverable.
- Low #2 (`_consumer_assigned_fields` discoverability): citation hygiene fix applied — `__init_subclass__` union site now cross-references `_consumer_assigned_fields`. The `_build_annotations` docstring already cited it and the scalar-branch inline comment already cited the relation branch via "Relation override symmetry"; all paths now reach the canonical contract.
- Low #3 (`_validate_meta`'s "Decision 4" reference opaque): citation hygiene fix applied — now `spec-011 Decision 4`.
- Low #4 (`_NODEID_STRING_RE` rationale-duplication): module-level comment added pointing at `_id_annotation_is_relay_node_id` for the full string-vs-resolved rationale; chose option (a) over (b) (do not move the regex into the function) to preserve the import-time compile semantics.
- Low #5 (forward-looking, `_validate_interface_entry` table-driven extraction): deferred-with-trigger per artifact. Trigger: "sixth per-entry rule lands in `_validate_interfaces` OR `_validate_orderset_class` adds a parallel per-entry validation loop with two-or-more shared rules".
- Low #6 (forward-looking, richer `_consumer_assigned_fields` error): deferred-with-trigger per artifact. Trigger: "third consumer report of `_consumer_assigned_fields` confusion lands in `docs/feedback*.md` OR a sibling validator adopts a `got {type(value).__name__}` pattern".

### Validation run
- `uv run ruff format .` — pass / 213 files unchanged
- `uv run ruff check --fix .` — pass / All checks passed

### Notes for Worker 3
- `django_strawberry_framework/types/base.py` is dirty from concurrent maintainer work that landed mid-cycle: a new `_validate_orderset_class` helper now lives at `:98-123`, `orderset_class` moved from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`, the two TODO blocks at the prior `:71-80` / `:109-116` positions are gone, and `_validate_meta` now calls `_validate_orderset_class`. Per AGENTS.md #33 every concurrent change was left untouched; my edits are scoped exactly to the artifact's named comment-pass surfaces and do NOT overlap with the orderset-class landing. The artifact's `## DRY analysis` "defer until ``Meta.orderset_class`` lands" coordinated-landing trigger is firing concurrently in someone else's branch — flagging for awareness, not acting (out-of-cycle scope).
- M1's `get_queryset` sentence is technically a bundled addition; the artifact explicitly authorizes "Worker 2 may bundle this into the same edit by adding one sentence to that entry" so it lands here rather than at a separate `get_queryset` cycle.
- `uv.lock` unchanged.

---

## Changelog disposition

### State

`Warranted but deferred to maintainer`.

### Reason

Per `worker-2.md` "Changelog dicta — three-state disposition": M2 ships a real consumer-visible change at a public-API error site. The exception type stays `ConfigurationError` (matching the surrounding contract) but the message text changes from `"{model}.Meta.optimizer_hints names unknown fields: {…}. Available: {…}."` to `"{model}.Meta.optimizer_hints names fields that are not selected relations: {…}. Available selected relations: {…}. (Hints only fire on relation branches; excluded fields and selected scalar fields are unreachable.)"` at `django_strawberry_framework/types/base.py::_validate_optimizer_hints #"excluded_hint_fields = sorted"`. A consumer who asserted on the prior `"unknown fields"` substring for the excluded-or-scalar branch would need to update; the substring `"optimizer_hints"` is preserved but the per-branch diagnostic is materially different. The first branch (unknown-on-model typo guard at `:717-726`) still emits the legacy `"unknown fields"` shape so consumers asserting on the typo case are unaffected — only the second-branch (excluded-relation or selected-scalar) asserters are.

Calibration matches the `filters/base.py` cycle (loud-fail `TypeError` at `RelatedFilter(lookups=...)` placed under `[Unreleased] ### Changed`) and `filters/sets.py` cycle (two `FilterSet.apply_async` bullets), both of which were typed-error / public-API contract changes that warranted deferred-to-maintainer entries rather than `Not warranted`. The corrected diagnostic also matches the long-shipped docstring contract at `types/base.py::_validate_optimizer_hints:688-691` ("Hints only fire on relation branches; excluded fields and selected scalar fields are unreachable."), so the change brings the runtime error message into alignment with the docstring — internal-docstring-contract alignment alone would calibrate to `Not warranted`, but because the visible substring at the error site changes, the deferred-to-maintainer path is the safer call.

The active plan does not authorize a `CHANGELOG.md` edit this cycle and the package is pre-alpha (maintainer owns CHANGELOG cadence). Per worker-2.md the suggested entry text is preserved verbatim below so the maintainer can lift it at release time without re-derivation.

### What was done

No `CHANGELOG.md` edit. Suggested entry preserved verbatim below.

#### Suggested CHANGELOG entry

Place under `[Unreleased] ### Changed`:

```markdown
- `DjangoType.Meta.optimizer_hints` validation now distinguishes the two
  rejection reasons. Hint names that do not exist on the Django model still
  raise `ConfigurationError` with the legacy `"…names unknown fields: …"`
  shape; hint names that exist on the model but are not selected as relations
  (excluded via `Meta.exclude`, or selected as scalar columns) now raise
  `ConfigurationError` with a dedicated `"…names fields that are not selected
  relations: …. Available selected relations: …. (Hints only fire on relation
  branches; excluded fields and selected scalar fields are unreachable.)"`
  message, matching the long-shipped docstring contract at
  `types/base.py::_validate_optimizer_hints`. Consumers asserting on the
  exact pre-fix substring `"unknown fields"` for the excluded-relation or
  selected-scalar branch should update to `"not selected relations"`.
  Pinned by `tests/types/test_base.py::test_meta_optimizer_hints_for_excluded_field_raises`,
  `::test_meta_optimizer_hints_for_selected_scalar_field_raises`, and
  `::test_meta_optimizer_hints_with_empty_field_selection_raises_configuration_error`.
```

### Validation run

- `uv run ruff format .` — pass / 213 files unchanged
- `uv run ruff check --fix .` — pass / All checks passed
