# Build: Slice 1c — audit of `spec-039` Slice 3 (resolver pipeline + products live surface)

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
Rationale companion: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`
Status: review-accepted

This artifact replaces the build/review split with **one combined audit section**: this pass
is read-only (`spec-039` shipped; nothing is being built), so there is no Worker 2 diff and
no Worker 2 build report. Nothing in this pass mutated any file outside this artifact.

Graded against `HEAD` = `89ee8ac55730dca6964cb6d158cab6df628dbd05`. Of the files in scope
only `django_strawberry_framework/utils/querysets.py` was dirty (`git status --short`); its
pristine version was obtained read-only as `git show HEAD:… > /tmp/dsf-039-head/utils_querysets.py`
(3904 lines vs 3959 in the tree) and that copy is what was graded. `git stash` / `checkout` /
`restore` / `worktree` were not used. The tests under `tests/` that `git status` reports
modified (`test_conf.py`, `test_list_field.py`, `test_resource_policy.py`, …) are the
concurrent `spec-050` cycle's and are not in this population.

---

## Combined audit (Worker 3)

### Population enumerated

**50 contract rows**, from the five spec homes this slice's contracts live in.
Every row is graded below; the counts under "Grade summary" are the `len()` of the
graded rows, not an asserted number.

**Group A — `## Slice checklist` → the whole `Slice 3` block (17 rows).**
The block has seven bullets; the first (the `rest_framework/resolvers.py` pipeline bullet)
carries eleven separable contract clauses, so it is graded clause by clause.

| id | contract |
| --- | --- |
| A1a | (`update`) locate through the target type's `get_queryset`; miss/hidden → `FieldError` on `id`, no existence leak; `create` has no locate |
| A1b | authorize via inherited `check_permission` / `Meta.permission_classes` against the **raw** payload, **before** any relation decode; denial → top-level `GraphQLError` |
| A1c | decode `data:` via the reverse map into a **serializer-field-keyed** `provided_data` through a dedicated serializer relation decoder (not the model-attr-keyed `036` decoder) |
| A1d | the generated input field exposes exactly ONE strategy-dependent shape; the shared decode helper accepts both a `GlobalID` and a raw pk only for reused / package-only branches (M1) |
| A1e | each id type-checked against the relation's target model (backing FK via `source`, else `field.queryset.model`), resolved to the **visible** object via the related primary `DjangoType.get_queryset`, reduced to the pk under the serializer field name; hidden target → field-keyed `FieldError` |
| A1f | a serializer `FileField`/`ImageField` (`Upload`) is routed into the serializer's `data` like any other value (the DRF contrast with the `038` `files=` split) |
| A1g | construct via `get_serializer_kwargs(info, *, data, instance=None)`; create/update shapes; `partial=True` injected on update; `context={"request": request_from_info(...)}` — **plus the bracketed `[superseded by the 2026-07-15 hardening revision …]` clause** |
| A1h | validate via `serializer.is_valid()`; failure → the dedicated **recursive** `serializer_errors_to_field_errors` (dotted `items.0.name`, `non_field_errors` → `"__all__"` at every level); null-object payload |
| A1i | write via `serializer.save()` **wrapped by the `036` `save_or_field_errors` mapper** in a value-preserving closure (`nonlocal`, called exactly once) |
| A1j | re-fetch by `saved.pk` + optimizer-plan; return the `<Name>Payload` (`node` / `result`) |
| A1k | one `transaction.atomic()`; the async path runs the sync body in one `sync_to_async(thread_sensitive=True)` call |
| A2 | `mutations/fields.py`: **no change**; the `038` generalization verified for `SerializerMutation` by a `tests/mutations/test_fields.py` extension |
| A3 | **Products live serializer surface (same commit)**: `products/serializers.py` `ItemSerializer` (+ `validate_<field>` + cross-field `validate()`), the `Item.attachment` `Upload` branch, the request-context `validate()` branch (**not** a `HiddenField`, F9); `products/schema.py` gains create + update |
| A4 | **Live coverage is the primary harness** — the twelve enumerated live rows in `test_products_api.py` |
| A5 | **Package-internal, genuinely-unreachable internals only** in `tests/rest_framework/test_resolvers.py`; no reachable behavior duplicated |
| A6 | **DRY / reuse** — `run_write_pipeline_sync` (P1.5) scoped to model-backed create/update only, `_visible_related_object` (P1.1), `NON_FIELD_ERROR_KEY` + a promoted `field_error` leaf ctor (P2.4) |
| A7 | **Config-assessment grep-guard** — neither `conf.settings` nor `_resolve_globalid_strategy` on the query path, backed by a post-finalization monkeypatch test |

**Group B — the three Decisions (16 rows).**

| id | contract |
| --- | --- |
| B1.1 | Decision 8 step 1 — Locate (update only); the only decode preceding authorization, and it is the mutation's own `id:` |
| B1.2 | Decision 8 step 2 — Authorize before any relation decoding; the ordering is a package security invariant, not an incidental step |
| B1.3 | Decision 8 step 3 — Decode; one annotation per relation input; the recorded `effective_globalid_strategy`, never a live setting read |
| B1.4 | Decision 8 step 4 — Construct; the hook + framework precedence "pinned exactly" (default return shape, framework merge, `partial` non-overridable, `context["request"]` non-overridable, `data` filled if omitted) |
| B1.5 | Decision 8 step 5 — Validate; the recursive flattener, not the flat `036` mapper |
| B1.6 | Decision 8 step 6 — Write; `save_or_field_errors` value-preserving closure + the DRF/Django/`IntegrityError` three-way class routing |
| B1.7 | Decision 8 step 7 — Re-fetch by `saved.pk` + return the payload |
| B1.8 | Decision 8 — the flattener's pinned dotted-path encoding + `"__all__"` normalization at every level, one `FieldError` per leaf, nothing dropped, nothing stringified |
| B1.9 | Decision 8 — error field names keyed to the **GraphQL input path** via the reverse map; the serializer name kept when no input field exists |
| B1.10 | Decision 8 — `update` is DRF-native partial, not a `038`-style reconstruction |
| B1.11 | Decision 8 — the cross-flavor DRY paragraph (the skeleton **scoped to the three model-backed create/update flavors**, delete + model-less plain form **excluded**, F6) |
| B2.1 | Decision 9 — the re-fetch rides the `036` `refetch_optimized` G2 path |
| B2.2 | Decision 9 — G2 keeps `select_related` / `prefetch_related` and suppresses all `.only(...)` |
| B2.3 | Decision 9 — re-fetch by pk **without** the visibility filter (the `036` Medium-1 exception); this card writes **no** new optimizer code |
| B3.1 | Decision 13 — the products live matrix ships in the SAME slice as the resolver |
| B3.2 | Decision 13 — `tests/rest_framework/test_resolvers.py` keeps **only** the residue a live query cannot drive |

**Group C — `## Cross-flavor reuse and DRY obligations` rows landing in `resolvers.py` (4 rows).**

| id | contract |
| --- | --- |
| C1 | P1.1 — `_visible_related_object(related_model, pk, info) -> obj \| None` promoted to `utils/querysets.py`; the serializer re-keys over it, does not fork a third object-returning decoder; the form's default-manager fallback stays byte-unchanged |
| C2 | P1.5 — `run_write_pipeline_sync(...)` promoted to `mutations/resolvers.py`, owning atomicity + locate + **authorize-before-decode** + the re-fetch/payload tail; the serializer supplies only `decode_step` / `write_step` |
| C3 | P2.4 — `serializer_errors_to_field_errors` imports the shared `mutations/inputs.py::NON_FIELD_ERROR_KEY`; ideally a promoted `field_error(path, messages)` leaf ctor both flatteners call |
| C4 | `### Import manifest` — the `resolvers.py` row's allowed-import list |

**Group D — `## Definition of done` (2 rows).** D4 (item 4, the resolver contract restated) and
D5 (item 5, the products live surface + the no-duplication rule).

**Group E — `## Edge cases and constraints` rows bearing on the resolver pipeline (11 rows).**

| id | contract |
| --- | --- |
| E1 | Serializer-only RELATION fields (F4) — target from `field.queryset.model`, declared name preserved in `provided_data` |
| E2 | Relation target with no registered primary `DjangoType` (M3) — class-creation `ConfigurationError`, **not** a silent runtime default-manager fallback |
| E3 | `get_serializer_kwargs` cannot swap the request actor (H3) |
| E4 | `read_only` / `HiddenField` dropped from the input; the live request-context proof is a `validate()` branch, never a `HiddenField` (F9) |
| E5 | Serializer `validate()` / `non_field_errors` → the `"__all__"` sentinel |
| E6 | `update` partial preservation via `partial=True`; a hidden row is not-found before the serializer runs |
| E7 | File / image serializer fields → `Upload`, value lands in `data`; **"Full multipart HTTP ergonomics still await the `0.0.14` `TestClient`; the scalar + serializer-field typing ship here"** |
| E8 | Relation visibility is **not** delegated to the serializer's queryset — the decode type/visibility-checks the id before the serializer sees it |
| E9 | `many=True` is a `ManyRelatedField` wrapper — the relation target is read off `field.child_relation`, not `field` |
| E10 | Write-time `IntegrityError` → the envelope via the reused `036` `save_or_field_errors` mapper, never a top-level `GraphQLError` |
| E11 | Write-time `ValidationError` — DRF and Django shapes routed by exception class, never one branch (F2/H2) |

### Grade summary

| grade | count | rows |
| --- | --- | --- |
| BUILT-CONFORMANT | 33 | A1a A1b A1c A1d A1e A1f A1h A1j A1k A2 A3 A5 A7 B1.1 B1.2 B1.3 B1.5 B1.7 B1.8 B1.9 B1.10 B2.1 B2.3 B3.1 B3.2 C1 C2 C3 E1 E2 E5 E6 E9 |
| SPEC-STALE | 8 | A1g B1.4 C4 D4 E3 E4 E7 E8 |
| DEVIATED | 3 | A1i B1.11 E10 |
| SUPERSEDED | 3 | B1.6 D5 E11 |
| DROPPED | 0 | — |
| PARTIAL (behavior built, contract not pinned by a distinguishing test) | 3 | A4 B2.2 A6 |

**No row graded DROPPED.** Every behavior `spec-039` Slice 3 planned exists at `HEAD`;
what has moved is the spec's description of it, plus one contract (B2.2 / A4's G2 row)
whose *behavior* is right and whose *test* is non-distinguishing.

### Row-by-row grades

**A1a — BUILT-CONFORMANT.** `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`
#"if needs_locate:" runs `coerce_lookup_id` → `locate_instance(..., select_for_update=meta.select_for_update)`
→ `_error_payload([not_found_error()])`. `needs_locate` is `primary_type is not None and
operation_takes_id(meta.operation)`, so `create` has no locate. Live:
`examples/fakeshop/test_query/test_products_api.py::test_update_item_via_serializer_visibility_scoped_hidden_row_is_not_found`.

**A1b — BUILT-CONFORMANT.** `mutations/resolvers.py::run_write_pipeline_sync`
#"with authorization_phase(auth_aliases):" calls `authorize_or_raise(mutation_cls, info,
meta.operation, data, instance=instance)` with the **raw** `data` argument, and `decode_step`
is not called until after the `authorization_phase` context exits. Live:
`test_products_api.py::test_create_item_via_serializer_authorize_before_decode_unpermitted_gets_auth_denial`
(asserts the top-level `Not authorized` `GraphQLError`, `data is None`, and contrasts against
the permitted-caller relation `FieldError` row). Verified green in this pass.

**A1c — BUILT-CONFORMANT.** `rest_framework/resolvers.py::_decode_serializer_data` →
`_decode_input_object`, which routes each value to `result[spec.target_name]` (the declared
serializer field name) via the bind-stashed `mutation_cls._input_field_specs`. The model-attr
keying of the `036` decoder is not used.

**A1d — BUILT-CONFORMANT.** `rest_framework/resolvers.py::_decode_relation_single` docstring
#"this helper accepts BOTH a ``GlobalID``"; the both-shapes branch is driven only by direct
call in `tests/rest_framework/test_resolvers.py::test_decode_relation_single_raw_pk_visible_reduces_to_pk`.
Live, the one-shape rule is pinned by
`test_products_api.py::test_create_item_malformed_category_id_is_top_level_coercion_error`.

**A1e — BUILT-CONFORMANT.** `_decode_relation_single` / `_decode_relation_multi` delegate to
`utils/write_values.py::decode_visible_relation` / `::decode_visible_relation_ids`, which call
`utils/querysets.py::visible_related_object` / `::visible_related_objects`; the serializer
supplies `project=lambda obj: obj.pk`. `InputFieldSpec.related_model` is recorded at build from
the backing FK's `source` or `field.queryset.model`
(`rest_framework/serializer_converter.py::serializer_only_relation_annotation`). Live:
`test_products_api.py::test_create_item_via_serializer_hidden_category_id_is_field_keyed_relation_error`.

**A1f — BUILT-CONFORMANT.** `_decode_input_object` #"FILE lands in ``data``" — the FILE
handler stores into the same `provided_data` dict every other kind stores into; there is no
`files=` split. Live:
`test_products_api.py::test_create_item_via_serializer_multipart_upload_to_attachment`.

**A1g — SPEC-STALE.** The behavior at `HEAD` is the hardened contract; the checklist text is
not. The shipped signature is `get_serializer_kwargs(self, info, *, data, hook_context)`
(`rest_framework/sets.py::SerializerMutation.get_serializer_kwargs`), and
`rest_framework/resolvers.py::_merged_serializer_kwargs` rejects any returned `data` that is
not the exact frozen object, **any** returned `instance`, and any returned `partial`. The
checklist's own bracketed `[superseded by the 2026-07-15 hardening revision …]` clause is the
chronology `docs/builder/BUILD.md` `## Spec rationale extraction` forbids in the spec — the
fix is to rewrite the clause as the current contract and move the "what it replaced and why"
into the rationale companion. See `### Notes for Worker 1`, item 1.

**A1h — BUILT-CONFORMANT.** `rest_framework/resolvers.py::serializer_errors_to_field_errors`
plus `::_error_node_children` / `::_error_leaf` / `::_rekey_segment`. The `"__all__"`
normalization reads `_DRF_NON_FIELD_KEY = serializers.api_settings.NON_FIELD_ERRORS_KEY`, so it
normalizes whatever key DRF is configured to use rather than a hard-coded literal — stronger
than the spec asks. Package rows: `test_resolvers.py::test_flattener_list_index_child_error_becomes_dotted_path`,
`::test_flattener_nested_non_field_error_normalizes_to_path_all`.

**A1i — DEVIATED.** The value-preserving closure is exactly as specified
(`rest_framework/resolvers.py::_guarded_serializer_write` #"nonlocal saved", pinned by
`test_resolvers.py::test_serializer_save_is_called_exactly_once_and_refetch_uses_returned_object`),
but the save is **not** wrapped by `mutations/resolvers.py::save_or_field_errors`. It runs
inside `with transaction.atomic(using=alias):` with three sibling `except` branches outside the
block, the `IntegrityError` arm calling `utils/errors.py::integrity_error_field_errors` directly
— the same leaf `save_or_field_errors` itself calls, so the envelope message policy stays
single-sited. The deviation is deliberate and documented in the code: `_guarded_serializer_write`
#"escaping ``save_base``'s savepoint-less inner atomic flags the connection" explains that
catching inside the block (which is what `save_or_field_errors` does) would leave the
transaction refusing every subsequent statement. Filed under `### Medium:` — the remedy is a
spec edit, not a code change.

**A1j — BUILT-CONFORMANT.** `run_write_pipeline_sync` #"obj = refetch_optimized(primary_type,
saved.pk, info, alias=using, force_load=False)" → `build_payload(payload_cls, slot, obj, [])`,
with `slot = payload_object_slot(primary_type)`.

**A1k — BUILT-CONFORMANT.** `run_write_pipeline_sync` #"with open_write_pipeline(mutation_cls) as using:"
is the single `transaction.atomic()`; the async entry is
`rest_framework/resolvers.py` #"resolve_serializer_sync, resolve_serializer_async = make_resolver_entries("
→ `mutations/resolvers.py::make_resolver_entries` #"Run ``sync_body`` in one ``sync_to_async(thread_sensitive=True)`` call."

**A2 — BUILT-CONFORMANT (both halves).** `grep -c serializer django_strawberry_framework/mutations/fields.py`
→ **0**; the file's protocol check is the duck-typed
`mutations/fields.py::_has_mutation_protocol`. `git log --oneline -- django_strawberry_framework/mutations/fields.py`
shows the last pre-`0.0.13` touch is `731fecd8` ("Finish spec-038…"), with no `spec-039` commit
between it and `3a294082` ("Release 0.0.13") — consistent with "no change", and the HEAD content
is the checkable half. The extension exists:
`tests/mutations/test_fields.py::test_django_mutation_field_generalizes_to_serializer_mutation`,
asserting `data: ItemSerializerInput!`, materialization in `rest_framework.inputs`, and that
`CreateItemViaSerializer.resolve_sync.__func__` is `SerializerMutation.resolve_sync.__func__`
and **not** `DjangoMutation.resolve_sync.__func__`. Verified green.

**A3 — BUILT-CONFORMANT.** `examples/fakeshop/apps/products/serializers.py::ItemSerializer`
(`Meta.fields = ("name", "description", "category", "attachment")`,
`::ItemSerializer.validate_name`, `::ItemSerializer.validate`), and
`examples/fakeshop/apps/products/schema.py::CreateItemViaSerializer` / `::UpdateItemViaSerializer`.
The F9 constraint is honoured exactly: the request-context proof is
`ItemSerializer.validate` #"request = self.context.get(\"request\")", not a
`HiddenField(default=CurrentUserDefault())`.

**A4 — PARTIAL.** Eleven of the twelve enumerated live rows exist and are named in
`### What looks solid`. The twelfth — "the **G2 optimizer re-fetch query shape** (assert the SQL
keeps `select_related` / `prefetch_related`, no `.only(...)`)" — is only half pinned. See
finding **High-1**.

**A5 — BUILT-CONFORMANT.** `tests/rest_framework/test_resolvers.py` holds 164 rows; walking the
node-id list, none is a create/update happy path, envelope, reverse-map, partial-update,
visibility, or write-auth row. The two that read closest — `::test_decode_relation_multi_uses_a_single_batched_visibility_query`
and `::test_decode_relation_multi_hidden_member_is_field_error_via_batch` — are **direct calls**
into `serializer_resolvers._decode_relation_multi` with raw pks against a synthetic non-Relay
`Genre` primary, which is exactly the "raw-pk / non-Relay + many-relation" residue the checklist
assigns to this tier. The tolerant unregistered-relation branch is likewise reached only by a
synthetic fake mutation class (`::test_relation_queryset_scope_pins_unregistered_raw_pk_relation_without_visibility`),
so it is genuinely unreachable in production (M3 blocks it at class creation). Checked in the
other direction too: the reachable half of the hardening mechanisms is live-covered in
`examples/fakeshop/test_query/test_library_api.py` (`::test_serializer_save_kwargs_naming_a_model_field_is_rejected_over_http`,
`::test_serializer_m2m_relation_visibility_over_http`,
`::test_serializer_update_substituted_instance_is_rejected_without_writes_over_http`, and 25 more).

**A6 — PARTIAL.** P1.1 and P2.4 are BUILT-CONFORMANT (rows C1, C3). P1.5 landed but with a
scope deviation (row B1.11 / finding **High-2**). The "existing model / model-form suites
staying byte-equivalent" half is a build-time obligation of the original slice and is not
verifiable from `HEAD` alone; recorded as not-HEAD-checkable rather than graded.

**A7 — BUILT-CONFORMANT.** Population measured, not asserted:
`grep -c 'conf\.settings' django_strawberry_framework/rest_framework/resolvers.py` → **0**;
`grep -c '_resolve_globalid_strategy' …` → **0**. Both halves of the backing are present:
the source grep test `tests/rest_framework/test_resolvers.py::test_resolvers_source_has_no_live_strategy_reads_grep_guard`
and the post-finalization monkeypatch test
`::test_relation_decode_consumes_recorded_strategy_after_strategy_resolver_fails`, which
replaces `types/relay.py::_resolve_globalid_strategy` with a raising `_boom` and asserts the
decode still resolves. Both verified green in this pass. The only `settings` token left in the
file is `serializers.api_settings.NON_FIELD_ERRORS_KEY`, a DRF module-level read, not a
per-request package setting re-read.

**B1.1 — BUILT-CONFORMANT** (same evidence as A1a; the docstring of `run_write_pipeline_sync`
states the "only decode preceding authorization is the mutation's own `id:`" contract in its
step 2).

**B1.2 — BUILT-CONFORMANT** (same evidence as A1b). The security invariant is single-sited:
all four write flavors reach `authorize_or_raise` only through this one call site.

**B1.3 — BUILT-CONFORMANT** (see A1d/A1e/A7).

**B1.4 — SPEC-STALE, and it is the largest stale block in this population.** Decision 8 step 4
still spells out the pre-hardening contract *in full* — "**Default hook return shape:**
`{"data": provided_data}` on `create`; `{"data": provided_data, "instance": <row>}` on
`update`", "**The hook does not own the whole kwargs dict — the framework merges over it.**",
"A hook that omits `data` is filled with `provided_data`" — none of which is true at `HEAD`.
Unlike the Slice-3 checklist it carries **no** superseded marker at all, so a reader who lands
on Decision 8 first has nothing telling them it is stale. What `HEAD` does:
`rest_framework/resolvers.py::_merged_serializer_kwargs` — `data` must be omitted or the exact
frozen object (identity via `_OMITTED` sentinel), **any** `instance` key is refused, **any**
`partial` key is refused, `context["request"]` and `context["write_alias"]` are set
unconditionally after the merge. See `### Notes for Worker 1`, item 1.

**B1.5 — BUILT-CONFORMANT** (see A1h).

**B1.6 — SUPERSEDED.** The three-way exception-class routing landed exactly as specified
(`_guarded_serializer_write` #"except DRFValidationError as exc:" → the recursive flattener,
#"except DjangoValidationError as exc:" → `utils/errors.py::validation_error_to_field_errors`,
#"except IntegrityError:" → `utils/errors.py::integrity_error_field_errors`, DRF first). What
superseded the step is its `save_or_field_errors` wrapper: the hardening revision's savepoint
requirement (blockquote #"``serializer.save()`` runs inside its own nested-``atomic``
**savepoint**") forces the catches **outside** the atomic block, which `save_or_field_errors`
structurally cannot provide. Superseding code: `_guarded_serializer_write`
#"with transaction.atomic(using=alias):". Pinned by
`test_resolvers.py::test_save_time_drf_validation_error_uses_recursive_flattener_not_flat_mapper`,
`::test_save_time_django_validation_error_uses_flat_mapper_not_detail`,
`::test_save_time_integrity_error_maps_to_all_sentinel_envelope`,
`::test_save_time_validation_after_partial_write_is_rolled_back`.

**B1.7 — BUILT-CONFORMANT** (see A1j).

**B1.8 — BUILT-CONFORMANT.** `serializer_errors_to_field_errors` emits one `field_error` per
leaf path, joins with `utils/errors.py::join_error_path`, and drops nothing. It is additionally
**iterative, cycle-rejecting, and budget-capped** (`_ERROR_FLATTEN_NODE_BUDGET = 10_000`) —
mechanisms the hardening blockquote covers.

**B1.9 — BUILT-CONFORMANT, and stronger than specified.** `_rekey_segment` re-keys **at every
descent level** using the recursive map from `_build_reverse_map`, where the Decision only
promises the **root** segment ("The flattener maps each leaf path's **root segment** back
through the reverse map"; "Nested sub-paths below the root segment … keep DRF's structure").
The unmapped-key case keeps the key verbatim, which satisfies the Decision's "the serializer
field name is kept" clause. Live: `test_products_api.py::test_renamed_serializer_scalar_validation_error_keys_to_graphql_wire_name`,
`::test_renamed_serializer_relation_error_keys_to_graphql_wire_name`. The Decision's
nested-paths sentence is now an understatement rather than a falsehood; flagged to Worker 1
as a wording upgrade, not a defect.

**B1.10 — BUILT-CONFORMANT.** `_merged_serializer_kwargs` #"kwargs[\"partial\"] = True" fires
only when `instance is not None`; no `model_to_dict` reconstruction exists anywhere in the
serializer flavor. Live: `test_products_api.py::test_update_item_via_serializer_partial_update_preserves_other_fields`,
`::test_update_item_via_serializer_partial_unique_together_fires_on_name_only_change`.

**B1.11 — DEVIATED. This is finding High-2.** See below.

**B2.1 — BUILT-CONFORMANT.** The serializer never calls the optimizer; the re-fetch is the
skeleton's `refetch_optimized(primary_type, saved.pk, info, alias=using, force_load=False)`.

**B2.2 — PARTIAL. This is finding High-1.** The behavior is right (it is the shared `036` path,
so it cannot diverge); the assertion is not.

**B2.3 — BUILT-CONFORMANT.** `mutations/resolvers.py::refetch_optimized` docstring
#"by pk, WITHOUT the visibility ``get_queryset`` filter". `rest_framework/resolvers.py`
contains no optimizer import or plan construction.

**B3.1 — BUILT-CONFORMANT.** `products/serializers.py`, `products/schema.py`, and the
`test_products_api.py` serializer block all exist at `HEAD` alongside `rest_framework/resolvers.py`.

**B3.2 — BUILT-CONFORMANT** (see A5).

**C1 — BUILT-CONFORMANT, and the "better" option in the spec's own row landed.**
`utils/querysets.py::visible_related_object` and `::visible_related_objects` exist at `HEAD`
(verified against the pristine `/tmp/dsf-039-head/utils_querysets.py`, not the dirty tree).
The spec's stretch goal — "better, the whole one-id *decode-or-coerce → visible-object →
no-leak `FieldError`* shape into a shared core taking a small per-flavor descriptor" — also
landed, as `utils/write_values.py::decode_visible_relation(…, skip=…, project=…)`: the form
passes `skip=_is_empty_form_value` / `project=_to_form_key_value`
(`forms/resolvers.py::_decode_form_relation_single`), the serializer passes
`skip=lambda candidate: candidate is None` / `project=lambda obj: obj.pk`
(`rest_framework/resolvers.py::_decode_relation_single`). The form's default-manager fallback
is preserved and single-sited in `utils/querysets.py::related_visibility_queryset_or_default`.
**Symbol-name caveat:** the promoted symbol is `visible_related_object` (public), not
`_visible_related_object` (private) as the spec spells it in eight places — see
`### Notes for Worker 1`, item 3.

**C2 — BUILT-CONFORMANT on the promotion itself.** `mutations/resolvers.py::run_write_pipeline_sync`
exists and owns atomicity, the locate preamble, authorize-before-decode, and the
`refetch_optimized` → `build_payload` tail; the serializer supplies only two lambdas
(`rest_framework/resolvers.py::_run_serializer_pipeline_sync`). The **scope** half of the row is
graded separately at B1.11.

**C3 — BUILT-CONFORMANT, including the optional half.** `rest_framework/resolvers.py` imports
`NON_FIELD_ERROR_KEY` from `..mutations.inputs` and `field_error` from `..utils.errors`; the
flat `036` mapper `utils/errors.py::validation_error_to_field_errors` and the recursive
`serializer_errors_to_field_errors` both terminate in the same
`utils/errors.py::field_error` leaf ctor, so the sentinel convention cannot drift. The spec
recorded this as a *proposal* ("no `field_error(...)` constructor exists yet"); it shipped.

**C4 — SPEC-STALE.** The manifest's `resolvers.py` row lists eleven `mutations/resolvers.py`
symbols as direct imports. At `HEAD` the file imports exactly two from that module
(`make_resolver_entries`, `run_write_pipeline_sync`) — the other nine are now called **by the
shared skeleton** or by `utils/write_values.py`, which is strictly more DRY than the manifest
asks. The manifest also omits four modules the file legitimately imports today
(`utils/write_values.py`, `utils/write_transaction.py`, `utils/errors.py`, `rest_framework/hook_context.py`)
and names `utils/querysets.py::{visibility_scoped_related_queryset, apply_type_visibility_async}`,
which the file no longer imports (it imports `related_visibility_queryset` and
`sync_pipeline_recourse`). Full evidence: `docs/shadow/django_strawberry_framework__rest_framework__resolvers.overview.md`
`## Imports`.

**D4 — SPEC-STALE.** DoD item 4 restates Decision 8, so it carries the same two stale clauses
(`get_serializer_kwargs(info, *, data, instance=None)`; "the write is wrapped by the `036`
`save_or_field_errors` mapper"). Its remaining clauses agree with `HEAD`. This is the
five-homes cross-check `START.md` #"Five homes per contract" prescribes: A1g carries a
superseded marker, B1.4 and D4 carry none, and all three describe the same contract — the
divergence between the three homes is itself the defect.

**D5 — SUPERSEDED (in its scope, not its content).** Every live row DoD 5 enumerates exists in
`test_products_api.py`, and the package-tier residue list matches. What superseded it is the
scope sentence "`tests/rest_framework/test_resolvers.py` holds **only** the genuinely-unreachable
internals … **no reachable behavior is duplicated across the two trees**": there are now **three**
trees carrying serializer coverage, because `examples/fakeshop/apps/library/serializers.py`
and `examples/fakeshop/test_query/test_library_api.py` grew a large serializer surface
(28 live rows) that neither DoD 5 nor Decision 13 mentions. Superseding code:
`examples/fakeshop/apps/library/serializers.py` (16 serializer classes) +
`examples/fakeshop/apps/library/schema.py`. Not a defect — it is the live home for the
many-relation, injected-fields, save-kwargs, schema-hook, and select-for-update surfaces —
but the spec says products is the whole live story, and it is not.

**E1 — BUILT-CONFORMANT.** `rest_framework/serializer_converter.py::serializer_only_relation_annotation`
resolves from `field.queryset.model` / `field.child_relation.queryset.model`; the resolver's
attestation skips such fields explicitly (`rest_framework/resolvers.py::_attestable_m2m_fields`
#"except FieldDoesNotExist:" and `::_attest_saved_relations` #"# A serializer-only relation: nothing on the row to attest."),
pinned by `test_resolvers.py::test_attestation_skips_serializer_only_and_non_matching_sources`.

**E2 — BUILT-CONFORMANT.** `rest_framework/serializer_converter.py::_require_relation_primary`
raises at class creation; the form fallback is untouched. The resolver's runtime tolerance
(`rest_framework/resolvers.py::_scope_specs_over_serializer` #"``None`` = raw-pk relation with")
is therefore defensive only. See finding **Low-1**.

**E3 — SPEC-STALE (chronology).** The contract is correct at `HEAD`
(`_merged_serializer_kwargs` #"set a different " raises on a different request object,
tolerates the same one), pinned by
`test_resolvers.py::test_merged_kwargs_override_different_request_object_is_configuration_error`
and `::test_merged_kwargs_sets_framework_request_unconditionally`. The row's parenthetical
"(the 2026-07-15 hardening revision made `data`, `instance`, `partial`, `context["request"]`,
and `context["write_alias"]` framework-owned)" is spec-narrating-its-own-history and must move
to the rationale.

**E4 — SPEC-STALE.** The F9 half is exactly right and shipped. The row's leading clause is
now understated: `read_only` / `HiddenField` are dropped from the input, but the shipped
`_assert_save_kwargs_no_shadow` also covers a `HiddenField`'s **validated-data** key
(`test_resolvers.py::test_save_kwargs_shadowing_renamed_defaulted_and_hidden_keys_raises`),
a contract the row does not mention.

**E5 — BUILT-CONFORMANT.** `_rekey_segment` #"if key == _DRF_NON_FIELD_KEY:". Live:
`test_products_api.py::test_create_item_via_serializer_object_validate_all_sentinel_and_request_context`,
`::test_create_item_via_serializer_unique_together_error_uses_all_sentinel`.

**E6 — BUILT-CONFORMANT** (see B1.10 and A1a).

**E7 — SPEC-STALE, and it contradicts the Slice-3 checklist.** The sentence "Full multipart HTTP
ergonomics still await the `0.0.14` [`TestClient`]; the scalar + serializer-field typing ship
here" is false on its own terms at `HEAD` **and** was false when written: the same slice's own
checklist requires "the **multipart `Upload` → `Item.attachment`** write" live, and
`test_products_api.py::test_create_item_via_serializer_multipart_upload_to_attachment` ships it
over a bare `django.test.Client` multipart post. Two spec homes state opposite things about
the same contract.

**E8 — SPEC-STALE (understated).** The decode-first contract holds
(`_serializer_decode_step` runs before `_serializer_write_step` constructs the serializer), but
`HEAD` adds a second layer the row does not mention:
`rest_framework/resolvers.py::_scope_relation_querysets_to_visibility` composes each runtime
relation field's queryset with the visibility queryset (`author ∩ visibility`, pinned to the
write alias, locked when `Meta.select_for_update` locks) so DRF's own `is_valid()` lookup is
the visibility lookup. rev6 #3 describes this; the edge-case row still reads as though the
decode is the only gate.

**E9 — BUILT-CONFORMANT.** `rest_framework/resolvers.py::_relation_model_of`
#"field.child_relation if isinstance(field, serializers.ManyRelatedField) else field" and
`::_assert_relation_agreement`, pinned by
`test_resolvers.py::test_relation_queryset_scope_handles_many_related_field`. The spec's
"(Asserted from DRF's API; verify against the installed DRF when Slice 1 lands.)" hedge is
discharged and should be dropped.

**E10 — DEVIATED** (same evidence as A1i / B1.6).

**E11 — SUPERSEDED** (same evidence as B1.6 — the routing is conformant, the wrapper is not).

### High:

#### High-1 — the G2 "no `.only(...)`" contract has no distinguishing assertion anywhere

`spec-039` states the no-`.only(...)` half of G2 in three homes (Slice 3 checklist #"the **G2
optimizer re-fetch query shape** (assert the SQL keeps", Decision 9, DoD item 4 #"no
[`.only(...)`]"). The only test claiming to pin it is
`examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`,
whose `.only(...)` assertion is:

```examples/fakeshop/test_query/test_products_api.py:4420:4423
    # G2 NO `.only(...)` projection: the post-write re-fetch selects the full item
    # row (no SQL names a strict deferred column subset), so the row reads back whole.
    assert "SerG2Widget" in models.Item.objects.values_list("name", flat=True)
```

That line issues a fresh ORM query against the database and never reads `captured` or `sql`.
It passes identically whether the re-fetch applied `.only(...)` or not — it only proves the row
was written. This is `docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing
property, not observability` exactly: the wire result is identical either way. The neighbouring
`len(captured) == 17` and the `products_item`/`products_category` `SELECT` counts do **not**
rescue it either: the operation selects `node { name category { name } }`, so a `.only(…)`
projection would *include* both selected fields and fire no deferred-field lazy refetch — the
counts are the same with the G2 gate on or off.

The test's own comment says the column-exact snapshot is "the package mirror's job" — **there is
no package mirror.** `grep -n "G2\|only(\|select_related" tests/rest_framework/test_resolvers.py`
returns no plan-shape row; the phrase points at a test that does not exist. The `038` flavor has
the distinguishing version and is the model to copy:
`tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_suppresses_only`
asserts `plan.select_related == ("category",)` and `plan.only_fields == ()` off a captured
`ctx.dst_optimizer_plan`.

Why it matters: G2 suppression is what stops a mutation payload re-fetch shipping a
deferred-field set, which turns every unselected attribute a downstream resolver or a consumer
`@property` touches into an extra query inside the write transaction. A regression here is
silent — the wire response is byte-identical.

Recommended change (Worker 1 to route): add a serializer-flavor plan-shape row asserting
`plan.only_fields == ()` and `plan.select_related == ("category",)`, and delete or rewrite the
non-distinguishing live line and the comment that points at a non-existent mirror. Tier: the
`038` precedent puts the plan-shape assertion in the package tier
(`tests/rest_framework/test_resolvers.py`) because `optimizer_plan` capture is not observable
over `/graphql/`; that placement is consistent with the checklist's "hermetic … seams not
observable over HTTP" clause and does not duplicate reachable behavior.

Rows affected: **A4**, **B2.2**, **D4**.

#### High-2 — `run_write_pipeline_sync` is a universal write skeleton; the spec forbids that in three places

The spec pins the skeleton's scope emphatically and repeatedly:

- P1.5: "`run_write_pipeline_sync(...)` to `mutations/resolvers.py`, **scoped to model-backed
  create/update only** … **Exclude `delete`** (no data / no decode / snapshot payload) **and the
  model-less plain form** (no instance / no primary type / no re-fetch) — not a universal
  skeleton (**F6**)";
- Decision 8's DRY paragraph: "**not** a universal write skeleton … folding them in would make
  the skeleton a leaky generic framework instead of a small create/update helper";
- the Slice-3 checklist DRY bullet: "scoped to model-backed create/update only (delete +
  model-less plain form excluded, **F6**)".

At `HEAD` all four flavors ride it. `mutations/resolvers.py::run_write_pipeline_sync` docstring
#"The single-sited skeleton the model (create / update / delete), the" names all four, and the
signature carries a third seam `tail_step: Any = None` documented as #"the delete seam". Call
sites: `mutations/resolvers.py` #"return run_write_pipeline_sync(" appears at the model
create/update rider and again at the delete rider (#"Delete rider of ``run_write_pipeline_sync``: snapshot-before-delete via ``tail_step``."),
and `forms/resolvers.py::_run_form_pipeline_sync` #"ONE skeleton call serves both bases" routes
the model-less plain `DjangoFormMutation` through it too, with the skeleton's
`if slot is None: return payload_cls(ok=True, errors=[])` arm serving the model-less payload.

The build is deliberate (a named `tail_step` seam, a documented `slot is None` arm, and a form
docstring that explains the branch), which grades it DEVIATED rather than DROPPED. It is filed
High because it is a spec contract violation in `docs/builder/BUILD.md` `## Severity definitions`
terms: the spec says the skeleton excludes two flavors and it does not.

**The recommended resolution is a spec edit, not a code revert.** The security invariant P1.5
exists to protect — authorize-before-decode — is now single-sited across *four* flavors instead
of three, which is strictly better, and the excluded flavors were folded in through explicit
seams rather than by widening the middle. Worker 1 should rewrite P1.5, Decision 8's DRY
paragraph, and the Slice-3 DRY bullet to state the current contract (universal skeleton, three
seams: `decode_step` / `write_step` / `tail_step`; the `slot is None` model-less tail) with no
chronology, and record the F6 reversal — what F6 argued and why it lost — in the rationale
companion under Decision 8.

Rows affected: **B1.11**, **A6**, **C2**.

### Medium:

#### Medium-1 — `_assert_field_agreement` fails **open** when `_mutation_meta` is absent

```django_strawberry_framework/rest_framework/resolvers.py:1164:1170
    if spec.required is None and spec.annotation_repr is None:
        return
    meta = getattr(mutation_cls, "_mutation_meta", None)
    if meta is None:
        return
```

A `getattr` default on a decision path converting "cannot determine" into "permit" —
`docs/builder/BUILD.md` `### Fail-open shapes`, third bullet. When `_mutation_meta` is missing,
the requiredness-drift and annotation-`repr` drift checks are silently skipped and the field is
treated as agreeing. The present / writable / `source` / kind / relation-model checks above it
run unconditionally, so the security half of the guard is unaffected; what is skipped is the
schema-shape half. There is a row acknowledging the branch
(`tests/rest_framework/test_resolvers.py::test_agreement_guard_stops_when_mutation_meta_absent`)
— it pins that the guard *permits*, which is the wrong direction for a boundary.

Every production `SerializerMutation` gets `_mutation_meta` from the base metaclass, so this is
defensive-only today. But the shape is the one the fail-open section exists to catch, and the
fix is one line: raise, or drop the branch and let the `AttributeError` surface, since a
mutation class reaching `_assert_field_agreement` without `_mutation_meta` is a framework
invariant violation, not a supported configuration. Guard the **answer** ("I cannot determine
whether this field agrees") rather than the input spelling.

Test expectation if changed: `::test_agreement_guard_stops_when_mutation_meta_absent` inverts to
assert a `ConfigurationError`.

#### Medium-2 — `A1i` / `E10` / `B1.6`: the `save_or_field_errors` wrapper contract is false in three spec homes

Recorded as a finding rather than only a grade because it is stated in the Slice-3 checklist,
Decision 8 step 6, DoD item 4, and the `## Edge cases` write-time-`IntegrityError` row — four
homes, all saying the write is "wrapped by the `036` `save_or_field_errors` … mapper", and none
true at `HEAD`. `grep -rn save_or_field_errors django_strawberry_framework/` shows call sites
only in `mutations/resolvers.py` (the model flavor) and `forms/resolvers.py` (both form
flavors); `rest_framework/resolvers.py` does not import it. Behaviorally nothing is lost — the
serializer reaches the identical envelope through `utils/errors.py::integrity_error_field_errors`,
the same leaf `save_or_field_errors` calls — and the deviation is what makes the savepoint
containment possible. Spec edit owed in all four homes plus a rationale entry.

#### Medium-3 — `_assert_runtime_write_source_ownership` and `_pin_validator_querysets` are shipped mechanisms the spec describes nowhere

Both run on the consumer-reachable write path and neither appears in any Decision, edge case,
rev6 item, or the hardening blockquote:

- `rest_framework/resolvers.py::_assert_runtime_write_source_ownership` — walks the
  **instantiated** serializer (and every opted-in nested serializer) immediately before
  validation and rejects two runtime fields that would overwrite each other in
  `validated_data`. The blockquote's nearest sentence is "A writable serializer `source` must be
  **unique across the whole write surface** … rejected **at class creation**" — the runtime
  half, which exists precisely because schema discovery cannot see context-dependent
  `get_fields()` output, is undocumented. Rows:
  `test_resolvers.py::test_runtime_context_field_source_collision_fails_before_validation`,
  `::test_runtime_context_star_source_field_is_rejected_before_validation`.
- `rest_framework/resolvers.py::_pin_validator_querysets` — recursively shallow-copies and
  alias-pins every queryset-backed DRF validator (`UniqueValidator`, unique-together, nested,
  `ListSerializer` children) before `is_valid()`. The blockquote covers relation-field querysets
  only; validators are not relation fields, and DRF *shares* validator objects across serializer
  instances, which is the concurrency hazard this closes. Rows:
  `::test_validator_querysets_are_recursively_pinned_to_write_alias`,
  `::test_validator_queryset_pinning_replaces_shared_validator_per_serializer_instance`,
  `::test_list_field_child_validator_querysets_are_pinned_and_isolated`,
  `::test_validator_queryset_explicitly_routed_elsewhere_fails_closed`.

Both belong under Decision 8 (the construct/validate steps). See `### Notes for Worker 1`, item 2.

### Low:

#### Low-1 — the serializer's relation-visibility gate rests on a class-creation guard over a permissive runtime default

`utils/querysets.py::visible_related_object` (which the serializer decode reaches through
`utils/write_values.py::decode_visible_relation`) resolves its base through
`::related_visibility_queryset_or_default`, whose documented fallback for a model with no
registered primary is `base_queryset(related_model)` — the plain default manager, no visibility
contract. The serializer never reaches that fallback because
`rest_framework/serializer_converter.py::_require_relation_primary` raises at class creation
(M3). The runtime scoping helper makes the same accommodation explicitly
(`::_scope_specs_over_serializer` #"``None`` = raw-pk relation with").

This is correct as shipped and the spec sanctions it (P1.1: "that fallback stays the **form
flavor's** behavior, byte-unchanged"). Recorded because the invariant is load-bearing and lives
in a different module from the guard that enforces it: if a future change ever relaxes
`_require_relation_primary`, the serializer's relation decode silently degrades from
visibility-scoped to existence-only, with no test failing. A one-line comment at
`_require_relation_primary` naming what depends on it would make the coupling visible.

#### Low-2 — `_upload_metadata`'s three broad `except Exception` arms

`rest_framework/resolvers.py::_upload_metadata` wraps each of `name` / `size` / `content_type`
in a bare `except Exception` returning `None`. Not a decision path (the descriptor is
hook-facing only; the authoritative upload goes to the serializer untouched), so this is
polish, not a fail-open. Pinned by `::test_upload_metadata_tolerates_raising_name_and_content_type`
and `::test_upload_metadata_tolerates_a_sizeless_file`.

### DRY findings

1. **40 repeated `"SerializerMutation "` error-message prefixes.**
   `docs/shadow/django_strawberry_framework__rest_framework__resolvers.overview.md`
   `## Repeated string literals` reports `40x SerializerMutation`, plus `3x at runtime but`,
   `2x , but the mutation's transaction is pinned to`, `2x , but the runtime serializer`,
   `2x : relation field`, `2x .save() returned a`. Every `ConfigurationError` in the file opens
   `f"SerializerMutation {mutation_cls.__name__}…"`. A one-line
   `_config_error(mutation_cls, body)` helper (or a module-level prefix builder) would
   single-site the family label and the punctuation, and would stop the label drifting from
   `utils/permissions.py::request_from_info(family_label="SerializerMutation")`, which spells
   the same string a fourth way. `docs/builder/BUILD.md` `## Severity definitions` puts a
   "repeated literal / key / tuple that should be a named constant" at Medium; recording it
   here rather than as a numbered Medium because the fix is cosmetic and touches ~30 message
   strings, which is a spec-independent cleanup the maintainer should schedule, not this cycle
   (fence: `.py` files are in scope, but this cycle's `.py` mandate is the label-vocabulary
   citer sweep, not message refactoring).

2. **`_write_surface_specs` is the right shape and is used consistently.** Six per-field
   disciplines (agreement, source ownership, queryset scoping, intent ledger, M2M snapshot,
   attestation) all walk the one `rest_framework/resolvers.py::_write_surface_specs` list rather
   than each concatenating `_input_field_specs` + `_injected_field_specs` itself. No finding —
   recorded because it is the pattern the next flavor should copy.

3. **No third relation-decoder fork exists.** The existence challenge worth asking here —
   should `utils/write_values.py` exist at all, or should the form and serializer each keep
   their own decoder? — answers itself: it has two real callers with genuinely different
   `skip` / `project` tails, and the alternative is the third copy of a visibility check, which
   P1.1 identifies as a data-leak risk class. Keep.

4. **`_error_leaf`'s membership test.** `errors in (None, "", [], {})` relies on `==` semantics
   across four container literals rebuilt on every leaf. `not errors` plus an explicit
   `leaf_codes` check reads the same and allocates nothing. Cosmetic.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty** (0 lines). `__all__` and the
re-export list are unchanged by this pass, which writes no source. `SerializerMutation` resolves
through the root `__getattr__` lazy-export table (`django_strawberry_framework/__init__.py`
#"\"SerializerMutation\": (\".rest_framework.sets\", \"SerializerMutation\")") and is **not** in
`__all__`, which is what DoD item 8 (**F1**) requires — verified as part of this audit rather
than as a change check.

### CHANGELOG sanity

Not applicable; this pass modified no files other than this artifact.

### Documentation / release sanity

Not applicable; this pass modified no docs, release metadata, KANBAN, or archived specs. The
spec edits this audit routes are Worker 1's, in Slice 2.

### What looks solid

- **The security ordering is single-sited and the live test is a real discriminator.**
  `mutations/resolvers.py::run_write_pipeline_sync` is the only call site of
  `authorize_or_raise` for all four write flavors, and
  `test_products_api.py::test_create_item_via_serializer_authorize_before_decode_unpermitted_gets_auth_denial`
  distinguishes the two outcomes by *kind* (a top-level `GraphQLError` with `data: null` versus
  an in-band relation `FieldError`), with the permitted-caller row immediately above it as the
  contrast. That is the shape a discriminating security test needs; it would fail if the decode
  ever moved ahead of the authorize.
- **The config-assessment grep-guard is doubly backed.** A source grep test *and* a
  behavioral monkeypatch that makes `_resolve_globalid_strategy` raise. Either alone would be
  weak; together the source grep catches a re-introduction and the monkeypatch catches an
  indirect re-read the grep's vocabulary would miss.
- **The eleven live rows that did land.** `test_products_api.py`: create / update happy paths
  (`::test_create_item_via_serializer_happy_path`, `::test_update_item_via_serializer_happy_path`),
  the field-level envelope (`::test_create_item_via_serializer_validate_field_error_is_field_keyed`),
  the `"__all__"` envelopes (`::test_create_item_via_serializer_object_validate_all_sentinel_and_request_context`,
  `::test_create_item_via_serializer_unique_together_error_uses_all_sentinel`), the reverse-map
  write (`::test_create_item_via_serializer_category_id_reverse_map_writes`), partial-update
  preservation and the one-field unique-together fire
  (`::test_update_item_via_serializer_partial_update_preserves_other_fields`,
  `::test_update_item_via_serializer_partial_unique_together_fires_on_name_only_change`), the
  visibility-scoped update (`::test_update_item_via_serializer_visibility_scoped_hidden_row_is_not_found`),
  write auth (`::test_create_item_via_serializer_anonymous_is_denied_top_level_error_no_write`,
  `::test_create_item_via_serializer_missing_model_perm_is_denied_no_write`), the relation
  `FieldError` (`::test_create_item_via_serializer_hidden_category_id_is_field_keyed_relation_error`),
  authorize-before-decode, the multipart upload
  (`::test_create_item_via_serializer_multipart_upload_to_attachment`), and the request-context
  `validate()` branch.
- **P1.1 exceeded its own spec row.** The spec offered the object-returning helper as the
  minimum and "a shared core taking a small per-flavor descriptor" as the stretch; the stretch
  shipped as `utils/write_values.py::decode_visible_relation`, so the form and serializer
  decoders differ by two lambdas and nothing else.
- **The `"__all__"` normalization reads DRF's configured key.**
  `_DRF_NON_FIELD_KEY = serializers.api_settings.NON_FIELD_ERRORS_KEY` rather than the literal
  `"non_field_errors"`, so a consumer who reconfigures DRF's bucket key still gets the package
  sentinel. The spec only asked for the mapping.
- **Test-tier discipline holds in both directions.** 164 package rows, none duplicating a live
  contract; and the hardening mechanisms that *are* reachable (save-kwargs model-field
  rejection, M2M visibility, substituted-instance rejection, select-for-update) are earned live
  in `test_library_api.py`, not left package-only.

### Temp test verification

- **No temp tests were created.** `docs/builder/temp-tests/039-audit-3/` was not written to and
  does not exist. Finding High-1 is a reading proof, not a mutation proof: the assertion at
  `test_products_api.py:4423` issues its own ORM query and never touches the captured SQL list,
  so it is non-distinguishing by inspection — no mutant is needed to establish that, and this
  pass is forbidden from producing one.
- **Failability re-runs: none, and the empty set is legal here.** This dispatch is a read-only
  audit that explicitly withdraws Worker 3's failability-proof source carve-out, and the pass
  reviews no diff, so it introduces no boundary that meets the mandatory floor in
  `docs/builder/worker-3.md` #"The independent re-run has a mandatory floor". Recorded
  explicitly so a later reader does not read the absence as a skipped obligation.
- **Focused verification runs (read-only, no `--cov*`).**
  `uv run pytest -n0 --no-cov -q test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count
  test_products_api.py::test_create_item_via_serializer_authorize_before_decode_unpermitted_gets_auth_denial
  tests/rest_framework/test_resolvers.py::test_resolvers_source_has_no_live_strategy_reads_grep_guard
  tests/rest_framework/test_resolvers.py::test_relation_decode_consumes_recorded_strategy_after_strategy_resolver_fails
  tests/mutations/test_fields.py::test_django_mutation_field_generalizes_to_serializer_mutation`
  → **5 passed in 3.17s** (shared `.venv`: Python 3.14.2, Django 6.1 — not the floor; no floor
  run was in this slice's declared scope, which the plan sets to `none` for Slices 0–1d).
- **Scratch disposition.** `/tmp/dsf-039-head/utils_querysets.py` — the read-only `git show HEAD:`
  copy used to grade the dirty file; outside the repo, delete at cycle close.
  `docs/shadow/django_strawberry_framework__rest_framework__resolvers.{overview.md,stripped.py}`
  — written by the mandatory static-helper run below; gitignored, regenerable, never cited by
  line number.

### Static helper use

`uv run python scripts/review_inspect.py django_strawberry_framework/rest_framework/resolvers.py --output-dir docs/shadow`
— run (required: an existing file well past the 150-line and 30-line thresholds, and the
repeated-literal section is the mechanical half of the DRY review). No skips. The other files in
scope were read directly rather than through the helper, because this pass grades contracts
against source rather than reviewing a diff, and the helper's value here is the repeated-literal
and import sections, which only `resolvers.py` needed.

### Notes for Worker 1 (spec reconciliation)

**The top three sentences to rewrite, in priority order.**

1. **Decision 8 step 4, the whole "Construct" body** (`### Decision 8 …` #"**Construct** the
   serializer via the overridable"). It still spells out the pre-hardening hook contract in
   full — the default return shape `{"data": provided_data, "instance": <row>}`, "The hook does
   not own the whole kwargs dict — the framework merges over it", "A hook that omits `data` is
   filled with `provided_data`" — with **no** superseded marker, while the Slice-3 checklist's
   parallel clause carries a bracketed one and DoD item 4 carries none. Three homes, three
   different states. Rewrite all three to the shipped contract, stated directly and with no
   chronology: `get_serializer_kwargs(info, *, data, hook_context)` is **constructor-only**; the
   framework builds `data` itself from decoded client input plus the exact-match
   `Meta.injected_fields` injection via `get_serializer_injected_data`; a returned `data` must be
   omitted or the exact frozen object (identity, omission sentinel — an explicit `None` and a
   rebuilt-equal copy are both refused); **any** returned `instance` or `partial` key is a
   `ConfigurationError`; `context["request"]` and `context["write_alias"]` are set
   unconditionally after the merge. Then **delete the bracketed `[superseded by the 2026-07-15
   hardening revision …]` clause** and the `> Post-ship hardening revision (2026-07-15…)`
   blockquote entirely, folding each of their bullets into the Decision it belongs to (mapping
   below) and moving the "what changed, why, what it replaced" into
   `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` under Decision 8.

2. **P1.5's scope sentence** (`### Promotions to single-site now (P1 — third-copy forks)`,
   row P1.5) — "**Exclude `delete`** … **and the model-less plain form** … not a universal
   skeleton (**F6**)" — together with its two echoes in Decision 8's DRY paragraph ("**not** a
   universal write skeleton") and the Slice-3 DRY bullet ("scoped to model-backed create/update
   only (delete + model-less plain form excluded, **F6**)"). All three are false at `HEAD`
   (finding High-2). Rewrite to: `run_write_pipeline_sync` is the one write skeleton every
   flavor rides, with three seams — `decode_step`, `write_step`, and `tail_step` (the delete
   snapshot payload) — and a `slot is None` tail for the model-less plain form. Record the F6
   reversal (what F6 argued, why it lost) in the rationale.

3. **The `## Edge cases and constraints` file/image row's closing sentence** — "Full multipart
   HTTP ergonomics still await the `0.0.14` [`TestClient`]; the scalar + serializer-field typing
   ship here." This directly contradicts the same slice's own checklist, which requires the
   multipart `Upload` → `Item.attachment` write **live** in Slice 3, and it shipped
   (`test_products_api.py::test_create_item_via_serializer_multipart_upload_to_attachment`, a bare
   `django.test.Client` multipart post). Replace with the shipped contract: an `Upload` value
   lands in the serializer's `data` and is written over a real multipart `/graphql/` request.

**Shipped mechanisms mapped back to the Decision they belong under.** Every one of these is
live at `HEAD`; where it is described only in the blockquote it needs a home in a Decision body
before the blockquote is deleted, and where it is described nowhere it needs one written.

| shipped mechanism (`rest_framework/resolvers.py` unless noted) | belongs under | currently described |
| --- | --- | --- |
| `SerializerHookContext` / `UploadMetadata` (`rest_framework/hook_context.py`) | Decision 8 step 4 | blockquote only |
| `_frozen_hook_view` — recursive, iterative, cycle-rejecting freeze; fails closed on an opaque leaf | Decision 8 step 4 | blockquote only |
| `_injected_serializer_data` + `Meta.injected_fields` exact-match | Decision 8 step 4 | rev6 #2 (with a **stale signature**: `get_serializer_injected_data(info, *, data, instance=None)`; `HEAD` takes `hook_context`) |
| `_merged_serializer_kwargs` reserved-key checks (omission sentinel + identity) | Decision 8 step 4 | blockquote only |
| `_assert_schema_runtime_agreement` / `_assert_field_agreement` / `_assert_relation_agreement` / `_assert_nested_agreement` | Decision 8 step 4 (post-construct, pre-validate) | rev6 #1, but it omits the **requiredness-drift** and **annotation-`repr` drift** arms `HEAD` carries, and cites `_assert_injected_field_agreement`, **a symbol that does not exist** |
| `_assert_runtime_write_source_ownership` (runtime, context-dependent `get_fields()`) | Decision 8 step 4 | **nowhere** — finding Medium-3 |
| `_scope_relation_querysets_to_visibility` / `_scope_specs_over_serializer` (author ∩ visibility, alias-pinned, locked) | Decision 8 step 3 or 4 | rev6 #3 |
| `_pin_validator_querysets` (recursive validator alias pinning, per-instance copy) | Decision 8 step 5 | **nowhere** — finding Medium-3 |
| `_RelationIntentLedger` / `_instrument_relation_intent` / `_assert_relation_intent` | Decision 8 step 5 | blockquote only |
| `_m2m_membership_snapshot` + `_attest_saved_relations` | Decision 8 step 6 | blockquote only |
| `_write_witness` (`pre_save` cross-alias block + `post_save` pk-snapshot recorder) | Decision 8 step 6 | blockquote only |
| `_checked_saved_result` (model / `serializer.instance` identity / pk / alias / witnessed insert) | Decision 8 step 6 | blockquote only |
| `assert_no_target_drift` + `WriteAliasContext.authorized_pk` / `.target_state` (`utils/write_transaction.py`) | Decision 8 step 2 (snapshot) + step 6 (enforcement) | blockquote only |
| `pipeline_alias_guard` / `authorization_phase` / `pipeline_write_phase` / `_enforce_read_only_barrier` (`utils/write_transaction.py`) | Decision 8 preamble (the transaction boundary) | blockquote only |
| `_hook_mapping` — non-mapping / unmaterializable / non-string-key rejection at every hook boundary | Decision 8 step 4 | **nowhere** |
| flattener iterative walk + `_ERROR_FLATTEN_NODE_BUDGET` truncation marker + cycle rejection | Decision 8 step 5 | blockquote only |
| `_error_detail_codes` (DRF `ErrorDetail.code` preservation) | Decision 8 step 5 | rev6 #4 |
| nested opt-in decode (`_decode_nested`, `NESTED_SINGLE` / `NESTED_MULTI`) | Decision 7 / Decision 8 step 3 | rev6 #17 |
| `utils/write_values.py` — the entire shared decode module (`decode_visible_relation`, `decode_visible_relation_ids`, `decode_provided_fields`, `decode_field_handlers`, `decoded_into`) | Decision 8 step 3 + the DRY section (P1.1) | **nowhere** — `grep -c write_values` over the spec → **0** |
| `utils/errors.py` — the shared leaf-error module (`field_error`, `integrity_error_field_errors`, `validation_error_to_field_errors`, `join_error_path`) | the DRY section (P2.4) + Decision 8 steps 5/6 | **nowhere** — `grep -c 'utils/errors'` over the spec → **0** |

**Stale symbol names the citation gate cannot see.** `scripts/check_citations.py` is
`path::Symbol`-only, and every one of these is prose/backtick spelling, so nothing fails:

- `_visible_related_object` — **8 spec sites** (lines 809, 916, 1431, 1711, 1921, 2120, 2399,
  2456, plus the import-manifest row at 2585). The shipped symbol is the **public**
  `utils/querysets.py::visible_related_object`, with a batched sibling `::visible_related_objects`
  the spec never names.
- `_assert_injected_field_agreement` (rev6 #2) — no such symbol at `HEAD`; the injected-field
  agreement rides the shared `_write_surface_specs` walk through `_assert_field_agreement`.
- `_type_check_relation_id` (rev6 #3) — no such symbol at `HEAD`; the type-check moved into
  `utils/write_values.py`, whose docstring still credits "the serializer's cleanly-factored
  `_type_check_relation_id`".

**Escalated: the import manifest row for `resolvers.py` (C4) needs re-derivation, not editing.**
The row's eleven-symbol allow-list is now wrong in three ways at once (nine symbols moved behind
the shared skeleton, two named `utils/querysets.py` symbols are no longer imported, four
legitimately-imported modules are missing). Rewriting it by hand risks a second stale manifest;
the `## Imports` section of
`docs/shadow/django_strawberry_framework__rest_framework__resolvers.overview.md` is the measured
population and should be the source. Resolution paths: (a) re-derive the row from the shadow
overview and keep the manifest as a DoD-checkable list; (b) narrow the manifest to *module*
granularity (which modules `rest_framework/` may import) so a DRY-driven symbol move inside a
permitted module no longer falsifies it; (c) retire the per-symbol manifest and keep only the
"do not re-implement" prose. Worker 1 owns the choice.

**Two smaller reconciliations.**

- Decision 8's "Error field names are keyed to the GraphQL input path" paragraph says only the
  **root segment** is re-keyed and that "Nested sub-paths below the root segment … keep DRF's
  structure". `HEAD` re-keys at **every** depth (`_rekey_segment` + `_build_reverse_map`'s
  recursive child maps), which is better; the sentence is an understatement, not a falsehood,
  and should be upgraded.
- The `## Edge cases` `many=True` row closes "(Asserted from DRF's API; verify against the
  installed DRF when Slice 1 lands.)" — a build-time note in a shipped spec. The verification
  happened (`_relation_model_of`, `_assert_relation_agreement`, and
  `::test_relation_queryset_scope_handles_many_related_field`); drop the hedge.

**Deferred to the maintainer, outside this cycle's fence-relevant work:** the 40-site
`"SerializerMutation "` message-prefix duplication (DRY finding 1). It is a `.py` change and so
technically inside the fence, but it is a cosmetic refactor of ~30 error strings unrelated to
the label-vocabulary strip Slice 2 owns. Route it to a card rather than folding it into this
cycle.

### Review outcome

`review-accepted`. Zero rows graded DROPPED, so this audit escalates no work to the conditional
Slice 3 code pass on its own account. Both High findings and all three Mediums are escalated to
Worker 1: **High-2**, **Medium-2**, and the eight SPEC-STALE / three DEVIATED / three SUPERSEDED
rows are spec-reconciliation work (Slice 2) with no code change owed. **High-1** (the
non-distinguishing G2 `.only(...)` assertion) and **Medium-1** (the `_mutation_meta` fail-open)
are the only two that need a `.py` edit; both are test/guard changes inside the fence, and
Worker 1 should decide at Slice 2 whether they open `bld-039-slice-3-code_gaps.md` or route to a
follow-up card, since neither is a DROPPED spec contract.
