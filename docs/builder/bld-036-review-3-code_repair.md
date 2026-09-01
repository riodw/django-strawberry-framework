# Build: Review round 3 — code repair (the two SKIPPED contracts + three weak pins)

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md` (read-only input contract; **being edited concurrently by R2** — never written by this pass)
Build plan: `docs/builder/build-036-mutations-0_0_11.md` (`## R1 outcome`, `### The two SKIPPED contracts`, Maintainer Decision B)
Status: final-accepted

This artifact was created by this pass. The plan lists it as **conditional** — created only if an R1 cohort returned a SKIPPED contract surviving the live-tree re-check — and both did, so no `Status: planned` predecessor exists. The `### Dispatched findings checklist` below is copied from the maintainer-set R3 dispatch.

## Plan (dispatched findings, as received)

### Dispatched findings checklist

- [x] Repair 1 — discharge `tests/mutations/__init__.py #"TODO(spec-036 Slice 1)"` (R1a's SKIPPED row 82) with non-`TODO` provenance, keeping the convention note
- [x] Repair 2 — discharge `tests/test_permissions.py #"TODO(spec-036 Slice 3)"` **and its `Pseudocode:` block** (R1b's RENAMED row C8), pointing at where the pin actually landed
- [x] Repair 3 — the two missing live write-authorization denial rows for `updateItem` / `deleteItem` (R1d's SKIPPED row S4.7), each distinguishing on the per-operation codename
- [x] Repair 4 — pin the AR-M5 delete-snapshot **connection-child** half (R1c's M1)
- [x] Repair 5 — couple the G2 `only_fields` mirror to production (R1d's Medium)
- [x] Repair 6a — `FieldError` field-set equality (R1a's headline finding), in the DIRTY `tests/mutations/test_inputs.py`
- [x] Repair 6b — a `Meta.interfaces`-declared Relay target asserting a `GlobalID` relation input (R1b's Medium-1), same file

Two rows beyond the dispatch were added because the acceptance rule required them; both are recorded under `### Implementation notes` and neither is a new finding.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` plus `git diff --numstat HEAD` per path. No file outside the pass's authorized write list was modified.

- `tests/mutations/__init__.py` (`+6/-5`) — Repair 1. The `TODO(spec-036 Slice 1)` comment block plus its `Pseudocode:` lines removed; the convention it stated ("one test module per mutation source module; live GraphQL behavior is earned through the fakeshop `test_query` suite") folded into the module docstring as non-`TODO` provenance (`spec-036, shipped as DONE-036-0.0.11`). The invariant is stated; how the change came to be is not.
- `tests/test_permissions.py` (`+6/-7`) — Repair 2. The `TODO(spec-036 Slice 3)` anchor **and its five-line `Pseudocode:` block** deleted whole; the module docstring now names where the lookup-scoping pin actually lives, in `AGENTS.md` rule 27's `path::QualifiedName` form.
- `examples/fakeshop/test_query/test_products_api.py` (`+118/-0`, clean at `HEAD` before this pass) — Repair 3 (two denial rows) plus the live half of Repair 4 (one connection-child delete row and its `_DELETE_ITEM_WITH_CONNECTION` document). Purely additive; no existing row, helper, or document string altered.
- `tests/mutations/test_resolvers.py` (`+80/-5`, clean at `HEAD`) — Repair 4's package half: a `with_entries_connection` opt-in kwarg on the shared `_build_item_schema` builder, the `_DELETE_WITH_CONNECTION` document, and `::test_delete_snapshot_materializes_connection_child_before_delete`. The 5 deleted lines are the `item_meta_attrs` literal the new kwarg made a variable, collapsed by `scripts/check_trailing_commas.py`'s own layout rule (it dropped below the 4-key explode threshold) — a consequence of this pass's edit, not a reflow of unrelated content.
- `tests/optimizer/test_walker.py` (`+68/-17`, clean at `HEAD`) — Repair 5. The G2 mirror's hand-restated selection replaced by one derived through the production extractor, plus a parametrized coupling row. The 17 deleted lines are the hand-built selection list and the docstring sentence that admitted it was a copy.
- `tests/mutations/test_inputs.py` (`+164/-0`; **DIRTY `+16/-0` with a concurrent session's work at pass start**) — Repairs 6a and 6b, both additive inserts. See `### The dirty-file protocol, as executed`.
- `docs/builder/temp-tests/036/proofs.json` (created; gitignored) — the failability manifest.
- `docs/builder/bld-036-review-3-code_repair.md` (this file, created).
- `docs/builder/worker-memory/worker-2-036.md` (appended).

Not touched, deliberately: the spec (R2 owns it), the rationale companion (never read by this role), any `django_strawberry_framework/**` production file, and every path on the plan's `### Baseline-dirty out-of-scope files` list. **This pass landed no production code**, which is what makes the plan's conditional hot-path declaration resolve to `none`.

### The dirty-file protocol, as executed

Maintainer Decision B authorized `tests/mutations/test_inputs.py` despite the concurrent session.

| Checkpoint | `git diff --numstat HEAD -- tests/mutations/test_inputs.py` |
|---|---|
| Pass start, before any edit | `16  0` |
| Immediately before the first edit to the file | `16  0` |
| Immediately before the last edit to the file | `16  0` (unchanged — no concurrent write landed in the window) |
| Pass end | `164  0` |

The concurrent diff was read first (`git diff HEAD -- tests/mutations/test_inputs.py`): a single `+16/-0` append at end of file, `::test_editable_input_fields_normalizes_its_declared_sequences`. It is intact and untouched at pass end. My additions are two mid-file inserts (the `FieldError` section and the relation-id section) plus their helper, so they do not share a hunk with the concurrent append. No line existing at pass start was reflowed, reordered, or reformatted by hand; the only reformat was `scripts/check_trailing_commas.py` exploding one construct **I** wrote.

`git stash`, `git checkout --`, `git restore`, and `git worktree` were used **nowhere** in this pass. The only `HEAD` read was `git show HEAD:<path>` into `<scratchpad>/head/` (used to read `optimizer/extension.py` at `HEAD` while auditing Repair 5's production entry point).

### Tests added or updated

- `tests/mutations/__init__.py` — no test; comment-only (Repair 1).
- `tests/test_permissions.py` — no test; comment-only (Repair 2). Orphan sweep run after deleting the `Pseudocode:` block: `grep -rn 'Pseudocode' tests/ examples/ django_strawberry_framework/` shows nine unrelated blocks in other modules and nothing referencing the deleted one; `grep -rn --include='*.py' 'TODO(spec-036' .` now returns **nothing** (exit 1) tree-wide, so both `spec-036` anchors are discharged.
- `examples/fakeshop/test_query/test_products_api.py::test_update_item_missing_change_perm_is_denied_no_write` — a caller granted **`add_item` and nothing else** is denied `updateItem`: top-level `GraphQLError`, `data: null`, `"Not authorized"`, and the row's `name` / `description` unchanged in the DB. Holding `add_item` is what makes it distinguishing — it cannot pass because the actor is unprivileged in general, only because `update` maps to `change_item`.
- `examples/fakeshop/test_query/test_products_api.py::test_delete_item_missing_delete_perm_is_denied_no_write` — the `delete` cell of the same matrix, same distinguishing construction, row still present afterwards.
- `examples/fakeshop/test_query/test_products_api.py::test_delete_item_snapshot_carries_connection_child_edges` — `deleteItem` selecting `entriesConnection { edges { node { value } } }` returns both edges after the row is gone. `Entry.item` is `on_delete=CASCADE`, so the children no longer exist when the connection resolves: a non-empty edge set can only come from the pre-delete materialization.
- `tests/mutations/test_resolvers.py::test_delete_snapshot_materializes_connection_child_before_delete` — the package-tier counterpart, same CASCADE construction over a locally declared `EntryT` primary and an `ItemT` selecting `entries`, so phase 2.5 synthesizes `entriesConnection`.
- `tests/optimizer/test_walker.py::test_mutation_payload_child_selections_flattens_slot_children_only[node]` / `[result]` — the production extractor flattens `<slot>`'s children and drops the `errors` envelope sibling, for both payload slots.
- `tests/optimizer/test_walker.py::test_mutation_refetch_plan_drops_only_keeps_relations` — **updated**: the selection it plans is now returned by `mutation_payload_child_selections("node")` rather than hand-restated, so the exact-state assertions (`only_fields == ()`, `select_related == ("category",)`, `prefetch_related != ()`, `deferred_loading == (frozenset(), True)`) move with the production flattening.
- `tests/mutations/test_inputs.py::test_field_error_field_set_is_frozen` — set equality over `FieldError`'s Python field names: `{"field", "messages", "codes", "path"}`.
- `tests/mutations/test_inputs.py::test_field_error_wire_name_set_on_a_generated_payload_is_frozen` — the same set as it reaches a client, read off `build_payload_type`'s `errors` field. Independent of the row above: a `strawberry.field(name=...)` rename breaks this one and not that one.
- `tests/mutations/test_inputs.py::test_fk_to_meta_interfaces_relay_target_uses_globalid_id` — a relation target declaring Relay via `Meta.interfaces = (relay.Node,)` yields a `GlobalID` relation input on the **bound** mutation's input class, asserted after `finalize_django_types()` and with the pre-finalize `not issubclass(..., relay.Node)` state asserted first.
- `tests/mutations/test_inputs.py::test_meta_interfaces_primary_binds_a_node_slot_payload` — the second consequence of the same injection: the bound payload carries a `node` slot, not `result`.

### Validation run

- `uv run ruff format <the six files this pass touched>` — pass (1 file reformatted: `tests/mutations/test_resolvers.py`). Scoped to this pass's files, never `.`.
- `uv run ruff check --fix <the same files>` — pass (1 error fixed, 0 remaining).
- `uv run python scripts/check_trailing_commas.py` — exit 0. Two auto-fix rounds, both inside constructs this pass wrote (`tests/mutations/test_resolvers.py:162/170/172`, `tests/mutations/test_inputs.py:1396`).
- `uv run python scripts/check_citations.py` — `OK: 933 citations resolve (776 in 435 .py files, 157 in KANBAN.md)`, exit 0. Slice 0 recorded 929; the delta is this pass's new symbol-qualified references. The two new citations in `tests/test_permissions.py` each sit on **one** source line (the wrap hazard).
- `git status --short` after both ruff invocations — every path this pass modified appears in `### Files touched`. Everything else reported modified was already on the plan's baseline-dirty list at pass start; nothing was reverted or tidied.
- `uv run pytest tests/mutations/ tests/optimizer/test_walker.py tests/test_permissions.py examples/fakeshop/test_query/test_products_api.py --no-cov -q` — **1 failed, 747 passed, 1 skipped**. The one failure is not this pass's; see `### Pre-existing working-tree failures, escalated not fixed`.
- `uv run pytest tests/ --no-cov -q` — **4 failed, 6161 passed, 40 skipped**. All four are the same class; see below.
- No `--cov*` flag was passed to any invocation; `--no-cov` everywhere, as `pytest.ini`'s `addopts` requires.

### Pre-existing working-tree failures, escalated not fixed

Four rows fail in the live (dirty) tree. **None is in this pass's diff and none is caused by it.** All four are the concurrent session's uncommitted production changes outrunning their own test re-pins. Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, a failing test is not worker-verifiable at `HEAD` — reproducing it needs a clean `HEAD` tree — so the evidence available is recorded and the claim is escalated rather than acted on.

1. `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key` — asserts `planned == [(None, (0, 2, False), None)]`; the value is now `ConnectionWindowBounds(offset=0, limit=2, reverse=False)`. Attribution, mechanical: `git diff HEAD -- django_strawberry_framework/optimizer/nested_planner.py | grep ConnectionWindowBounds` shows the concurrent session adding the import, the `-> ConnectionWindowBounds | None` return annotation and the `planned: list[tuple[str | None, ConnectionWindowBounds, KeysetSeek | None]]` type — i.e. their **uncommitted** change to the return shape. `git grep -c ConnectionWindowBounds HEAD -- django_strawberry_framework` shows the class exists at `HEAD` only in `utils/connections.py`, never in the planner. This pass's diff on that file is `@@ -25,6 +25,7 @@` (one import) and `@@ -4771,30 +4772,80 @@` (the G2 block); line 3577 is untouched.
2. `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`
3. `tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class`
4. `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`

Rows 2-4 share one traceback: `ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'` — a half-landed dataclass field in the concurrent session's dirty `sets_mixins.py` / `orders/` work. `tests/orders/test_inputs.py` and `tests/test_sets_mixins.py` are both on the plan's baseline-dirty out-of-scope list and in no cohort's write set.

Row 1's file **is** in this pass's write set, and the one-line fix is obvious. It was deliberately not made: re-pinning the assertion would write this cycle's opinion onto a production contract that is mid-flight in another session and that neither `spec-036` nor this cycle scopes, and `docs/builder/BUILD.md` is explicit that a stale test is fixed by the pass that owns the behavior. Recorded for the maintainer and for the final gate, which will see all four.

### Failability proofs

Six boundaries, one entry each, run through `uv run python scripts/prove_failability.py docs/builder/temp-tests/036/proofs.json` (manifest home per `docs/builder/BUILD.md` `### Mechanized`). Every anchor was verified to match **exactly once** before any copy (`--check-anchors-only` over the whole manifest: 6/6 matched once). The tool never invokes `git`; it takes a `copy2` of the **live** file before mutating and restores from that copy, so a dirty target is never reverted toward `HEAD` — confirmed by reading `scripts/prove_failability.py` `_restore_and_prove` / the per-entry body before pointing it at a dirty file.

Run in three batches so the dirty-target window stayed short, with `git diff --numstat HEAD` re-checked against the pass-start figure immediately before each batch. **No proof was aborted** — every figure was unchanged at every checkpoint:

| target | at pass start | before its batch | after its batch |
|---|---|---|---|
| `mutations/operations.py` | clean | clean | clean |
| `mutations/resolvers.py` | `11  6` | `11  6` | `11  6` |
| `optimizer/extension.py` | `2  1` | `2  1` | `2  1` |
| `mutations/inputs.py` | `31  38` | `31  38` | `31  38` |
| `types/finalizer.py` | `24  8` | `24  8` | `24  8` |

No `ACTIVE-MUTATION.json` or restore-failed marker remains in the scratch root; no mutation was live across any `Status:` transition.

- `django_strawberry_framework/mutations/operations.py::OPERATION_UPDATE #"permission_action"` — mutation applied: `permission_action="change",` -> `permission_action="add",`, collapsing the `update` operation's codename onto `add` so any products write perm authorizes an update (the per-operation codename boundary removed); scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE examples/fakeshop/test_query/test_products_api.py -k update_item or updateItem`; pre-mutation state of that scope: **green** (`17 passed`, exit 0; 0 pre-existing failing rows differenced out); failing node ids: `test_update_item_non_colliding_partial_update`, `test_update_item_partial_collision_on_unique_constraint_changing_only_name`, **`test_update_item_missing_change_perm_is_denied_no_write`**, `test_update_item_explicit_null_category_id_is_field_error`, `test_update_item_explicit_null_scalar_name_is_field_error`, `test_update_item_via_form_non_colliding_partial_update`, `test_update_item_via_form_partial_update_preserves_category_and_description`, `test_update_item_via_form_partial_collision_fires_unique_constraint_on_name_change`, `test_update_item_via_form_visibility_scoped_hidden_private_row_is_not_found`, `test_update_item_via_serializer_happy_path`, `test_update_item_via_serializer_partial_update_preserves_other_fields`, `test_update_item_via_serializer_partial_unique_together_fires_on_name_only_change`, `test_update_item_via_serializer_visibility_scoped_hidden_row_is_not_found` (all in `examples/fakeshop/test_query/test_products_api.py`); collection/setup errors: **0**; pytest exit code 1; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 476f82497ebc87d2... == 476f82497ebc87d2...` vs the pre-mutation copy.
- `django_strawberry_framework/mutations/operations.py::OPERATION_DELETE #"permission_action"` — mutation applied: `permission_action="delete",` -> `permission_action="add",` (same boundary, delete arm); scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE examples/fakeshop/test_query/test_products_api.py -k delete_item`; pre-mutation state of that scope: **green** (`4 passed`, exit 0; 0 differenced out); failing node ids: `examples/fakeshop/test_query/test_products_api.py::test_delete_item_happy_path`, `::test_delete_item_snapshot_carries_connection_child_edges`, **`::test_delete_item_missing_delete_perm_is_denied_no_write`**; collection/setup errors: **0**; pytest exit code 1; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 476f82497ebc87d2... == 476f82497ebc87d2...`.
- `django_strawberry_framework/mutations/resolvers.py::_delete_write_step #"snapshot = refetch_optimized("` — mutation applied: the whole `snapshot = refetch_optimized(...)` call moved **after** `_delete_or_field_errors(instance)` and returned directly, removing the materialize-before-delete boundary the delete payload rests on; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/mutations/test_resolvers.py examples/fakeshop/test_query/test_products_api.py -k delete`; pre-mutation state of that scope: **green** (`15 passed`, exit 0; 0 differenced out); failing node ids: `tests/mutations/test_resolvers.py::test_delete_happy_path_returns_snapshot_and_removes_row`, `::test_delete_snapshot_materializes_relation_before_delete`, **`::test_delete_snapshot_materializes_connection_child_before_delete`**, `::test_delete_custom_node_id_resolves_payload_to_real_pk_not_wrong_row`, `examples/fakeshop/test_query/test_products_api.py::test_delete_item_happy_path`, **`::test_delete_item_snapshot_carries_connection_child_edges`**; collection/setup errors: **0**; pytest exit code 1; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 9190f854d6b9e964... == 9190f854d6b9e964...`.
- `django_strawberry_framework/optimizer/extension.py::mutation_payload_child_selections #"_named_children(field_selection, slot)"` — mutation applied: the payload-slot navigation removed (`for slot_selection in _named_children(field_selection, slot):` -> `for slot_selection in (field_selection,):`), so the extractor flattens the payload's own children (`node`, `errors`) instead of the node-type selection; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/optimizer/test_walker.py -k mutation`; pre-mutation state of that scope: **green** (`8 passed`, exit 0; 0 differenced out); failing node ids: `tests/optimizer/test_walker.py::test_mutation_payload_child_selections_flattens_slot_children_only[node]`, `::test_mutation_payload_child_selections_flattens_slot_children_only[result]`, `::test_mutation_refetch_plan_drops_only_keeps_relations`; collection/setup errors: **0**; pytest exit code 1; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 b85cdbcbbd418cda... == b85cdbcbbd418cda...`. **This is the proof Repair 5 exists for**: before this pass the mirror planned a hand-restated list and this mutation would have failed 0 of its rows.
- `django_strawberry_framework/mutations/inputs.py::FieldError #"codes: list[str]"` — mutation applied: the `codes: list[str] = strawberry.field(default_factory=list)` member **deleted** from the shared envelope; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/mutations/test_inputs.py`; pre-mutation state of that scope: **green** (`70 passed`, exit 0; 0 differenced out); failing node ids: `tests/mutations/test_inputs.py::test_field_error_field_set_is_frozen`, `::test_field_error_wire_name_set_on_a_generated_payload_is_frozen`; collection/setup errors: **0**; pytest exit code 1; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 11b1d69665b210a0... == 11b1d69665b210a0...`. R1a's zero-row finding is closed: the same mutation failed **0** rows before this pass.
- `django_strawberry_framework/types/finalizer.py::finalize_django_types #"apply_interfaces(type_cls, definition)"` — mutation applied: the phase-2.5 `if definition.interfaces: apply_interfaces(type_cls, definition)` injection **deleted**, so a `Meta.interfaces`-declared type never reaches the MRO the bind reads — the same observable state a `bind_mutations()` hoisted above `apply_interfaces` produces, and a narrower single-anchor edit than a 115-line hoist; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/mutations/test_inputs.py`; pre-mutation state of that scope: **green** (`71 passed`, exit 0; 0 differenced out); failing node ids: `tests/mutations/test_inputs.py::test_fk_to_meta_interfaces_relay_target_uses_globalid_id`, `::test_meta_interfaces_primary_binds_a_node_slot_payload`; collection/setup errors: **0**; pytest exit code 1; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 5ee9ea3c8a3ed6cc... == 5ee9ea3c8a3ed6cc...`.

**One boundary graded weakly pinned mid-pass and was fixed in this pass, not handed on.** The `types/finalizer.py` entry first measured **1 row** (`test_fk_to_meta_interfaces_relay_target_uses_globalid_id` alone) — `revision-needed` by `docs/builder/BUILD.md` `### Acceptance rule`. The response was more rows, never a weaker boundary: `::test_meta_interfaces_primary_binds_a_node_slot_payload` was added over the **second** consumer of the same predicate (`payload_object_slot`, a different call site from `relation_id_scalar`), and the entry was re-run at the identical scope to 2 rows. The same logic drove the extra row on Repair 6a: an isolated set-equality assertion is by construction one row, so the wire-name projection row was added so the frozen-envelope boundary rests on two independently-failing assertions.

No zero-row result occurred, so no **why 0** judgement is owed on any entry, and no harness-impossible interleaving was found. Every entry's count is valid (0 collection/setup errors, pytest exit 1 on every mutant and 0 on every baseline).

### Hot-path budget

Not applicable; the plan declares R3's hot path **conditional on what it repairs**, and this pass landed **test-and-comment changes only** — zero lines of production code, verified by `git status --short`: no `django_strawberry_framework/**` path is in this pass's diff. Nothing runs per request, per resolver, per row, per connection, or per outbound message that did not run before, so the declaration resolves to `none`.

### Floor verification

Owned by this pass: the plan's floor-verification scope is conditional and Repair 3 drives live `/graphql/` requests through the Django request/response and schema-construction seam.

- Scratch venv (outside the repo, built with an explicit `--python`; the shared `.venv` was never mutated): `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4a12072-1e3a-4913-8249-dd800f1972ce/scratchpad/dsf-floor-036`
- Built as `docs/builder/BUILD.md` `### How to build the floor venv` prescribes: `uv venv <path> --python 3.10`, then `uv pip install --python <path>/bin/python -e . --group dev`, then `uv pip install --python <path>/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'` — the versions read from `docs/builder/BUILD.md` `## Floor verification`, the single canonical statement, not from memory.
- Resolved versions as read by `uv pip list --python <path>/bin/python`: **Python 3.10.19**, `django 5.2.16`, `strawberry-graphql 0.316.0`, `graphql-core 3.2.12`, `channels 4.3.2`, `djangorestframework 3.18.0`, `django-filter 26.1`, `django-debug-toolbar 8.0.0`, `pytest 9.1.1`, `pytest-django 4.14.0`, `pytest-asyncio 1.4.0`, `pytest-xdist 3.8.0`, `django-strawberry-framework 0.0.15` (editable, this checkout).
- `<floor>/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py --no-cov -q -k "missing_change_perm or missing_delete_perm or snapshot_carries_connection_child"` — **PASS** (3 passed in 10.10s). The three rows this pass added to the live seam.
- `<floor>/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py --no-cov -q` — **PASS** (132 passed in 53.47s). The whole focused live scope for the seam, so the new rows are confirmed not to have moved a sibling at the floor either.

Note for the final gate: the shared-`.venv` run of this same file reports `django 6.1 / Python 3.14.2` (read from the pytest header, not from memory), so the floor run is a genuinely different point in the range and not a re-run of the same environment.

### Implementation notes

- **Repair 1's shape: keep the sentence, drop the grammar.** The anchor was a convention note wearing staged-work grammar, so deleting it would have lost a real convention. It moved into the module docstring with `spec-036` / `DONE-036-0.0.11` provenance. `AGENTS.md` "No process provenance in code" is respected: the docstring states the invariant ("one test module per mutation source module") and the card that shipped it, never how the change came about.
- **Repair 2's precondition was checked before the deletion, not after.** `grep -n 'def test_hidden_row_update_is_not_found_no_existence_leak' tests/mutations/test_resolvers.py` -> line 676 and `grep -n 'def test_hidden_row_is_not_found_before_auth_signal_no_existence_leak' tests/mutations/test_permissions.py` -> line 301, both present, before removing the anchor that claimed they were absent. The docstring citation uses `path::QualifiedName`; both citations sit on one source line each, and `check_citations.py` resolves them.
- **Repair 3 reuses `_login_with_perm`, and holds `add_item` on purpose.** No parallel actor helper was invented (DRY), and the actor is `staff_1` — the same user the two happy-path rows use — so the *only* difference from `test_update_item_non_colliding_partial_update` / `test_delete_item_happy_path` is which codename is granted. `staff_1` also has full visibility, which keeps the visibility contract out of an authorization row (the file's own `test_visibility_scoped_update_delete_hidden_private_row_is_not_found` isolates the converse). First line is `create_users(1)` per `AGENTS.md`; no model is hand-rolled that a services helper owns.
- **Repair 4 opts in through the existing builder rather than a second one.** `_build_item_schema(with_entries_connection=True)` declares an `EntryT` primary and adds `entries` to `ItemT`'s `fields`; the default `"connection"` relation shape then makes phase 2.5 synthesize `entriesConnection`. A parallel local builder would have duplicated ~40 lines of the shared one. The default is `False`, so no existing caller changes behavior.
- **Repair 4's assertion is CASCADE-based, not observability-based.** `docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property` rules out asserting that a prefetch is merely *present*. Because `Entry.item` is `on_delete=CASCADE`, a snapshot that had not materialized the prefetch resolves the connection against the manager **after** the children are gone and returns zero edges. So the non-empty edge set is the load-bearing property directly, and no query-count literal (which would rot against the concurrent session's optimizer work) was needed.
- **Repair 5 needed no mock.** `mutation_payload_child_selections(slot)` returns a closure taking `(selections, info)` and the walker tests' `SimpleNamespace` selection factories are exactly the duck type it navigates, so the real production entry point is drivable from a package test as-is. `docs/builder/BUILD.md` `### Harness-impossible interleavings` and `AGENTS.md`'s mock carve-out are therefore **not** invoked: the honest conclusion is the opposite of "impossible without a mock". The mirror now derives its selection from a payload-level `createItem { node { ... } errors { ... } }` selection through that closure, and the `errors` sibling is included in the fixture on purpose so the extractor has to drop it.
- **Repair 6a's second row is the wire projection, deliberately not a duplicate.** `test_field_error_field_set_is_frozen` reads `python_name`; `test_field_error_wire_name_set_on_a_generated_payload_is_frozen` reads `graphql_name or python_name` off the type as it hangs on a `build_payload_type` payload. A `strawberry.field(name=...)` rename fails the second and not the first. The comment in the second row states why `graphql_name or python_name` is sound here (no member name carries an underscore, so auto-camel-casing is identity).
- **Repair 6b asserts the pre-finalize state first.** `_declare_meta_interfaces_mutation` asserts `not issubclass(..., relay.Node)` **before** `finalize_django_types()`, so the row proves the injection is what phase 2.5 performs rather than something true at class creation — without which the row could pass on a type that was already Relay-shaped and would not witness the ordering at all.
- **Function-local imports in `tests/mutations/test_inputs.py` were chosen over widening the module import block.** `DjangoMutation` / `finalize_django_types` / `_materialized_names` are imported inside the new bodies. Adding names to the existing single-line `from django_strawberry_framework import DjangoType, strawberry_config` would have forced that line to explode — a reformat of pre-existing content in the file Decision B flagged for additive-only edits. Function-local imports are an established idiom here (`_login_with_perm` in the live file, `_materialized_names` in `tests/mutations/test_sets.py`).

### Notes for Worker 3

- **The proof manifest is on disk** at `docs/builder/temp-tests/036/proofs.json` (gitignored), with all six entries and their scopes verbatim. Re-run your subset with `--only <n>`; the tool's own report is what the `### Failability proofs` entries above were transcribed from, so a set difference on node ids is directly comparable. Re-run **at the scopes recorded above** — three of them carry a `-k` fragment that is part of the scope.
- **Before re-running any entry, re-check that target's `git diff --numstat HEAD` against the table in `### Failability proofs`.** Four of the five targets are baseline-dirty with a concurrent session's work. The tool restores from a live pre-mutation copy and never touches `git`, so it cannot revert their work toward `HEAD` — but a concurrent write landing *inside* your mutation window would be clobbered by the restore. Abort and record rather than proceed if a figure moved.
- **Two entries sit at exactly the mandatory-re-run floor and two just above it**: `operations.py::OPERATION_DELETE` (3), `optimizer/extension.py` (3), `mutations/inputs.py::FieldError` (2), `types/finalizer.py` (2). The `finalizer.py` entry was measured twice — once at 1 row (weakly pinned) and once at 2 after the second row landed. If you re-run it and see 1, you are running against a tree missing `::test_meta_interfaces_primary_binds_a_node_slot_payload`.
- **Four rows fail in the working tree and none is mine**; the attribution evidence is in `### Pre-existing working-tree failures, escalated not fixed`. One of them (`tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`) lives in a file this pass wrote, so a diff-only reading could mistake it for mine. It is at line 3577; this pass's hunks are `@@ -25,6 +25,7 @@` and `@@ -4771,30 +4772,80 @@`.
- **`scripts/review_inspect.py` was not run.** No `.py` file under `django_strawberry_framework/` was touched, and this pass added no new module and no production logic — every changed file is a test or a comment. Recorded as an explicit skip with that reason per `docs/builder/BUILD.md` `### When to run the helper during build`.
- The two rows added beyond the dispatch (`::test_field_error_wire_name_set_on_a_generated_payload_is_frozen`, `::test_meta_interfaces_primary_binds_a_node_slot_payload`) exist solely to satisfy the acceptance rule on their own boundaries. Neither is a new finding and neither widens a contract.

### Notes for Worker 1 (spec reconciliation)

R2 is editing the spec concurrently, so nothing below was acted on. Each item carries its section anchor, the wording quoted as this pass read it, and a recommended replacement.

- **The `## Test plan` checklist bullet naming the wrong file for the `only_fields` pin is now doubly wrong.** R1c already routed this (its row S3.17). This pass makes the correction more urgent, because the exact-state pin has moved *further* into `tests/optimizer/test_walker.py`: it is now derived through `optimizer/extension.py::mutation_payload_child_selections` there.
  - Where it lives: `## Test plan`, the `tests/mutations/test_resolvers.py` package-tier bullet, `#"the plan-shape pin (mutation re-fetch carries select/prefetch, no deferred loading)"`.
  - Current wording: attributes the plan-shape / deferred-loading pin to `tests/mutations/test_resolvers.py`.
  - Recommended replacement: "the exact `only_fields` / `deferred_loading` plan state is pinned in `tests/optimizer/test_walker.py`, whose selection is derived through `django_strawberry_framework/optimizer/extension.py::mutation_payload_child_selections` rather than restated; `tests/mutations/test_resolvers.py` owns the pipeline behavior." Measured at pass end: `grep -rn 'only_fields\|deferred_loading' tests/mutations/` -> still **0 occurrences**, so the bullet remains false as written.
- **`## Implementation plan`'s staged-anchor sentence is now satisfied and can be stated as satisfied.** `grep -rn --include='*.py' 'TODO(spec-036' .` returns nothing tree-wide after this pass (it returned 2 `.py` hits at `HEAD`). No spec edit is *required* — the sentence states a rule, not a claim about the current tree — but if R2 is already rewriting nearby text, the two anchors R1a and R1b enumerated are gone and any prose implying they survive is now false.
- **Decision 8 step 6 / the delete-snapshot edge case can now name its pinning rows.** The `#"including nested selected relations and connection children"` guarantee was pinned on the nested half only when R1c graded it; both halves are pinned now (`tests/mutations/test_resolvers.py::test_delete_snapshot_materializes_connection_child_before_delete`, `examples/fakeshop/test_query/test_products_api.py::test_delete_item_snapshot_carries_connection_child_edges`). If the spec's Test plan enumerates the delete-snapshot rows, those two belong in it.
- **DoD item 5 / the `## Test plan` live tier's write-authorization clause is now true as written.** The clause `#"a caller lacking the \`add\` / \`change\` / \`delete\` model perm is denied"` was live-pinned for `create` only (R1d's S4.7). All three operations now have a live denial row. No wording change needed — recorded so R2 does not soften the clause to match the old gap.
- **Not a spec matter, but the reason this cycle exists twice over: no gate greps for a staged anchor.** R1a established that `grep -rn 'TODO(spec-'` over `scripts/`, `.pre-commit-config.yaml`, and `.github/workflows/` returns nothing, which is why two anchors survived four release lines. This pass discharged the two `spec-036` anchors; R1a counted **26** staged spec anchors tree-wide across `*.py`, one of them naming the also-shipped `spec-035`. A repo-wide stale-anchor check is out of this cycle's maintainer-set scope (it would touch `scripts/` and CI config) and belongs in the deferred-work catalog with the other 24.
- **The four working-tree test failures** in `### Pre-existing working-tree failures, escalated not fixed` need the maintainer's clean-`HEAD` tree to confirm, per `docs/builder/BUILD.md`'s rule that a behavioral pre-existing claim is not worker-verifiable. They will appear in the final gate's full sweep; the attribution evidence is recorded so the gate does not route them into this cycle.

---

## Review (Worker 3)

Reviewed as a fresh subagent with no memory of this pass's implementation reasoning (`docs/builder/BUILD.md` `### Isolation is non-waivable`). Diff range used: `git diff HEAD --` over exactly the six declared paths. Every other dirty path (`django_strawberry_framework/**`, most of `utils/`, `nested_planner.py`, `sets_mixins.py`, the `orders/` tree) was treated as the concurrent session's baseline-dirty work per the plan's `### Baseline-dirty out-of-scope files`: never reviewed as this pass's, never edited, never reverted.

**Numstat re-derived independently at review start**, matching the build report's `### Files touched` table digit for digit:

| Path | `git diff --numstat HEAD` |
|---|---|
| `examples/fakeshop/test_query/test_products_api.py` | `118  0` |
| `tests/mutations/__init__.py` | `6  5` |
| `tests/mutations/test_inputs.py` | `164  0` |
| `tests/mutations/test_resolvers.py` | `80  5` |
| `tests/optimizer/test_walker.py` | `68  17` |
| `tests/test_permissions.py` | `6  7` |

**Hot-path declaration verified true of the diff, not merely stated.** `git diff --name-only HEAD` restricted to the six paths returns no `django_strawberry_framework/**` path, and `git diff -- django_strawberry_framework/__init__.py` is empty. The plan's conditional hot-path clause therefore resolves to `none` correctly, and no before/after number is owed.

### Independent failability re-runs

All **six** manifest entries were re-run, not the mandatory three. The three at or below the floor were mandatory (`OPERATION_DELETE` 3, `mutation_payload_child_selections` 3, `FieldError #codes` 2); `finalizer.py apply_interfaces` (2) was re-run because it was diagnosed weakly pinned and self-remedied in-pass, and `_delete_write_step` (6) and `OPERATION_UPDATE` (13) were re-run because Repair 4's distinguishing claim and Repair 3's per-operation-codename claim are the two load-bearing behavioural claims of the pass. **No mandatory re-run was declined.** Nothing was accepted on Worker 2's record alone.

Loop used: `uv run python scripts/prove_failability.py docs/builder/temp-tests/036/proofs.json --only <selector> --scratch-root <scratchpad>/w3-rerun`, one boundary at a time, reverted before the next. Its restore semantics were read first (`scripts/prove_failability.py::_restore_and_prove` — `shutil.copyfile` from a pre-mutation `copy2`, `filecmp.cmp(shallow=False)` plus SHA-256, `git` never invoked), which is what makes it safe to point at a dirty target. No `git stash` / `checkout` / `restore` / `worktree` anywhere in this pass.

**Pre-flight, before any copy.** Every anchor matched exactly **once** in its live file (`operations.py` delete arm 1, change arm 1; `extension.py` slot navigation 1; `inputs.py` `codes` 1; `finalizer.py` `apply_interfaces` 1; `resolvers.py` `snapshot = refetch_optimized(` 1), so the tree was carrying no live prior mutation. No `ACTIVE-MUTATION.json` and no restore-failed marker existed in R3's scratch root. Independently of the tool, every one of the five production targets was byte-compared against the pristine copy R3's own run left behind — `cmp` exit 0 on `mutations/inputs.py`, `mutations/resolvers.py`, `optimizer/extension.py`, `mutations/operations.py`, `types/finalizer.py` — which is a stronger confirmation of R3's six recorded reverts than reading the record, and was re-confirmed after my own six runs.

Node-id sets measured. **All six agree exactly with the build report, member for member.** Collection/setup errors are recorded separately and were **0** on every entry, every baseline was green (pytest exit 0) and every mutant exited 1, so no count is invalidated.

1. `django_strawberry_framework/mutations/operations.py::OPERATION_UPDATE #"permission_action"` — scope `examples/fakeshop/test_query/test_products_api.py -k "update_item or updateItem"`; numstat before `clean`, after `clean`; baseline `17 passed`; mutant `13 failed, 4 passed`; errors 0. Set (13): `::test_update_item_non_colliding_partial_update`, `::test_update_item_partial_collision_on_unique_constraint_changing_only_name`, `::test_update_item_missing_change_perm_is_denied_no_write`, `::test_update_item_explicit_null_category_id_is_field_error`, `::test_update_item_explicit_null_scalar_name_is_field_error`, `::test_update_item_via_form_non_colliding_partial_update`, `::test_update_item_via_form_partial_update_preserves_category_and_description`, `::test_update_item_via_form_partial_collision_fires_unique_constraint_on_name_change`, `::test_update_item_via_form_visibility_scoped_hidden_private_row_is_not_found`, `::test_update_item_via_serializer_happy_path`, `::test_update_item_via_serializer_partial_update_preserves_other_fields`, `::test_update_item_via_serializer_partial_unique_together_fires_on_name_only_change`, `::test_update_item_via_serializer_visibility_scoped_hidden_row_is_not_found`. **AGREES** with the recorded set. `cmp` exit 0; anchor back to 1.
2. `django_strawberry_framework/mutations/operations.py::OPERATION_DELETE #"permission_action"` — scope `… -k delete_item`; numstat before `clean`, after `clean`; baseline `4 passed`; mutant `3 failed, 1 passed`; errors 0. Set (3): `::test_delete_item_happy_path`, `::test_delete_item_snapshot_carries_connection_child_edges`, `::test_delete_item_missing_delete_perm_is_denied_no_write`. **AGREES.** Restore proof `filecmp.cmp(shallow=False) True; sha256 476f82497ebc87d2... == 476f82497ebc87d2...` — the same digest the build report records.
3. `django_strawberry_framework/mutations/resolvers.py::_delete_write_step #"snapshot = refetch_optimized("` — scope `tests/mutations/test_resolvers.py examples/fakeshop/test_query/test_products_api.py -k delete`; numstat before `11/6`, after `11/6`; baseline `15 passed`; mutant `6 failed, 9 passed`; errors 0. Set (6): `tests/mutations/test_resolvers.py::test_delete_happy_path_returns_snapshot_and_removes_row`, `::test_delete_snapshot_materializes_relation_before_delete`, `::test_delete_snapshot_materializes_connection_child_before_delete`, `::test_delete_custom_node_id_resolves_payload_to_real_pk_not_wrong_row`, `examples/fakeshop/test_query/test_products_api.py::test_delete_item_happy_path`, `::test_delete_item_snapshot_carries_connection_child_edges`. **AGREES.** `cmp` exit 0; anchor back to 1.
4. `django_strawberry_framework/optimizer/extension.py::mutation_payload_child_selections #"_named_children(field_selection, slot)"` — scope `tests/optimizer/test_walker.py -k mutation`; numstat before `2/1`, after `2/1`; baseline `8 passed`; mutant `3 failed, 5 passed`; errors 0. Set (3): `::test_mutation_payload_child_selections_flattens_slot_children_only[node]`, `::test_mutation_payload_child_selections_flattens_slot_children_only[result]`, `::test_mutation_refetch_plan_drops_only_keeps_relations`. **AGREES.** `cmp` exit 0; anchor back to 1.
5. `django_strawberry_framework/mutations/inputs.py::FieldError #"codes: list[str]"` — scope `tests/mutations/test_inputs.py`; numstat before `31/38`, after `31/38`; baseline `71 passed`; mutant `2 failed, 69 passed`; errors 0. Set (2): `::test_field_error_field_set_is_frozen`, `::test_field_error_wire_name_set_on_a_generated_payload_is_frozen`. **AGREES** on the set; the baseline total differs from the recorded `70 passed` — see Low-2, it is R3's own second finalizer row landing between the two runs, not a scope or measurement disagreement. `cmp` exit 0; anchor back to 1.
6. `django_strawberry_framework/types/finalizer.py::finalize_django_types #"apply_interfaces(type_cls, definition)"` — scope `tests/mutations/test_inputs.py`; numstat before `24/8`, after `24/8`; baseline `71 passed`; mutant `2 failed, 69 passed`; errors 0. Set (2): `::test_fk_to_meta_interfaces_relay_target_uses_globalid_id`, `::test_meta_interfaces_primary_binds_a_node_slot_payload`. **AGREES**, so the self-remedy is real and 2 rows is honest at the recorded scope, not an artefact of a widened one. `cmp` exit 0; anchor back to 1.

**The remedy's second row is a genuinely independent reader, not a near-duplicate.** `::test_meta_interfaces_primary_binds_a_node_slot_payload` reaches the predicate through `payload_object_slot` and asserts an observable the first row never touches — `node` present and `result` absent on the materialized payload's field set, i.e. the wire shape — where the first row asserts the relation input's inner type is `relay.GlobalID`. Two call sites, two different consequences of the one injection.

**Every numstat re-checked after its restore was unchanged**, so no concurrent write landed inside any mutation window and every restore is clean. No mutation was live across this pass's `Status:` transition; the tree holds none now.

**The Repair 5 delta claim is verified mechanically, not accepted.** `git grep -n 'mutation_payload_child_selections' HEAD -- tests/ examples/` returns exactly one hit, `tests/optimizer/test_walker.py:4786`, **inside a docstring**. So no test row exercised the extractor at `HEAD`, and every one of the 3 rows the mutant now fails is a row this pass created or rewrote: the same mutation would have failed **0** rows before the repair. That delta is the evidence the repair worked, and it holds.

### High:

None.

### Medium:

None.

### Low:

#### Low-1 — the recorded `review_inspect.py` skip reason misstates the threshold rule

`### Notes for Worker 3` skips the helper because "no `.py` file under `django_strawberry_framework/` was touched, and this pass added no new module and no production logic". That reason answers only one arm of the trigger. `docs/builder/BUILD.md` `### When to run the helper during build` requires Worker 3 to run it when the slice "adds 30+ lines of new logic to any file under `django_strawberry_framework/`, **or 50+ lines to any file outside it**", and four of this pass's files clear the outside-the-package arm: `tests/mutations/test_inputs.py` (+164), `examples/fakeshop/test_query/test_products_api.py` (+118), `tests/mutations/test_resolvers.py` (+80), `tests/optimizer/test_walker.py` (+68). The obligation is Worker 3's rather than Worker 2's — Worker 2 only "may re-run" — so this is a recording imprecision about someone else's duty, not an unmet duty of this pass, which is why it is Low and not Medium.

**Disposition: addressed in this section.** The helper was run on all four files with `--output-dir docs/shadow` (see `### Temp test verification`), so the artifact as a whole now carries the run rather than an invalid skip. No re-loop needed.

#### Low-2 — two baselines for one scope, with nothing recorded to reconcile them

`### Failability proofs` records the `FieldError #codes` entry's pre-mutation state as `70 passed` and the `finalizer.py apply_interfaces` entry's as `71 passed`, both at the identical scope `tests/mutations/test_inputs.py`. Both were true when they ran — the `FieldError` proof predates `::test_meta_interfaces_primary_binds_a_node_slot_payload` landing as the finalizer boundary's second row — but the artifact does not say so, so a re-runner measuring `71` on both reads a disagreement where there is none. This is the exact rot `docs/builder/BUILD.md` `### What gets recorded` describes ("four disagreed with the reviewer's recorded counts, purely because rows had landed in between"), arriving inside one pass's own record rather than across two.

**Disposition: addressed in this section.** My re-run measured `71 passed` on both entries with both node-id sets unchanged, and the cause is named above. The node-id sets — the auditable field — never disagreed.

### DRY findings

- **Reuse verified, no parallel helper invented.** `_login_with_perm` is the only actor helper the two new denial rows use (`examples/fakeshop/test_query/test_products_api.py:77`), called exactly as the file's existing rows call it, and no second grant-a-codename block was added. R1d's standing 3-way near-copy finding on that block is therefore unchanged in extent, not aggravated.
- **The denial-assertion block is now 9 near-identical sites (7 at `HEAD`), a deferred consolidation candidate.** `grep -c 'assert "Not authorized" in payload\["errors"\]\[0\]\["message"\]'` → 7 at `HEAD`, 9 live, each preceded by the same `status_code == 200` / `payload.get("errors")` / `payload["data"] is None` trio. A `_assert_denied(response)` helper would collapse all nine. This pass was right to stay additive — Maintainer Decision B's mitigation and the file's clean-at-`HEAD` status both argue against rewriting seven pre-existing rows inside a repair pass — so this is **recorded as a deferred follow-up for Worker 1 to weigh**, not a finding against the diff.
- **Repeated-literal evidence, from the helper rather than eyeballing.** `docs/shadow/examples__fakeshop__test_query__test_products_api.overview.md` reports `categoryId` 46x, `view_item_1` 42x, `products.category` 40x, `add_item` 33x, `Not authorized` 11x. All are R1d's already-escalated pre-existing shape; this pass contributed 2 occurrences to `Not authorized` and 2 to `products.item` and introduced no new repeated literal. The three package-tier overviews report no repeated-literal entries at all.
- **No cross-cohort duplication to compare.** R3 ran as a single sequential cohort under the plan's `## Ownership partition`, so `docs/builder/worker-3.md` `### Cross-cohort duplication review` has no second cohort's guards to read this against.
- **No existence challenge raised.** The two new indirections were examined and both earn their place: `_build_item_schema(with_entries_connection=False)` extends the shared builder rather than forking a second ~40-line one and changes no existing caller's behaviour, and `_mutation_payload_selection` / `_mutation_refetch_selections` split the payload-shape fixture from the production-derived output so the parametrized coupling row and the plan-state row can share the second without restating the first.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export list are unchanged, consistent with the pass landing no production code at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only non-`.py` paths in the pass are its own `docs/builder/` artifact, the gitignored `docs/builder/temp-tests/036/proofs.json`, and a gitignored worker-memory file.

### What looks solid

- **Repair 2's one irreversible step was justified before it was taken, and the claim holds.** Both rows the deleted anchor's work landed in exist at `HEAD` and live: `git show HEAD:tests/mutations/test_resolvers.py | grep -c 'def test_hidden_row_update_is_not_found_no_existence_leak'` → 1, `git show HEAD:tests/mutations/test_permissions.py | grep -c 'def test_hidden_row_is_not_found_before_auth_signal_no_existence_leak'` → 1, and both are present in the working tree (`test_resolvers.py:751`, `test_permissions.py:301`). No contract was lost by the deletion. The orphan sweep is clean too: the only surviving references to the deleted `Pseudocode:` text are inside the four R1 artifacts, which are per-cycle scratchpads R2 owns.
- **The anchor obligation is discharged and correctly scoped.** `grep -rn --include='*.py' 'TODO(spec-036' .` returns nothing (exit 1), so `docs/builder/BUILD.md`'s integration-pass step 6 is satisfied for this card. Re-derived by occurrence rather than by matching line: 24 staged anchors naming *other* specs survive — 22 `spec-050`, 1 `spec-060`, 1 `spec-035` — all out of this cycle's scope, and the `spec-035` one is the already-routed deferred item.
- **Repair 1 keeps provenance and drops narrative.** The surviving docstring states the invariant ("one test module per mutation source module") and the shipping card (`spec-036, shipped as DONE-036-0.0.11`), which is exactly the non-`TODO` provenance form `docs/builder/BUILD.md` step 6 sanctions and `AGENTS.md` rule 26 contemplates. It does not narrate how the change came to be, so `AGENTS.md` "No process provenance in code" is respected — no Low finding here.
- **Repair 3's rows are distinguishing in the direction that matters, and the `_no_write` half is really asserted.** The actor holds the explicit `add_item` and nothing else, and `create_users` builds `staff_1` with `is_staff=True` and no superuser flag (`examples/fakeshop/apps/products/services.py:335`), so the superuser short-circuit is not what carries the row. Proof 1 puts `::test_update_item_missing_change_perm_is_denied_no_write` in the failing set when `update`'s codename collapses to `add`, and proof 2 does the same for the delete row — the row cannot pass merely because the actor is unprivileged in general. Both rows assert the un-write directly (`refresh_from_db` then `name`/`description` unchanged; `filter(pk=…, name="Undoomed").exists()`), so neither is a half test.
- **Repair 4 pins the load-bearing property, not observability.** `Entry.item` is `on_delete=models.CASCADE` (`examples/fakeshop/apps/products/models.py:147`), so a lazily-resolved connection on the detached snapshot reads the manager after the children are gone and yields zero edges; a non-empty edge set can only come from the pre-delete prefetch. Proof 3 confirms it mechanically: moving the snapshot after `delete()` fails both connection-child rows. No query-count literal was needed and none was guessed, which also keeps the row from rotting against the concurrent optimizer work. The edge ORDER the rows assert is deterministic, not incidental: `connection.py` selects a total ordering with a pk terminal tiebreaker and `Entry` declares no `Meta.ordering`, so insertion order is the contract.
- **Repair 5 exercises production's navigation, not a shape that merely satisfies it.** The extractor and every helper under it navigate by `getattr(selection, "selections", None)`, `should_include`, `is_fragment`, and `getattr(child, "name", None)` (`optimizer/selections.py::named_children`, `::node_children_with_runtime_prefix`), i.e. they are written against `Any` by attribute — so `SimpleNamespace` is the duck type by production's own design, not a stand-in that flatters the test. `AGENTS.md`'s mock carve-out is correctly *not* invoked; nothing is mocked. The `errors` sibling in the fixture is load-bearing (the extractor has to drop it), the `[node]`/`[result]` parametrization covers both slots, and the delta from 0 rows to 3 is verified above.
- **Repair 6b pins the documented consumer route that had no package-tier witness.** `docs/README.md:59` documents `Meta.interfaces = (relay.Node,)`, all four fakeshop products types use it (`examples/fakeshop/apps/products/schema.py:74,118,159,196`), and `git grep -c 'interfaces' HEAD -- 'tests/mutations/*.py'` returned **0** across all eight modules — now 16 in `test_inputs.py`. The pre-finalize `not issubclass(..., relay.Node)` assertion is what makes the row witness the phase-2.5 ordering rather than a type that was Relay-shaped from class creation.
- **Registry isolation is intact for the new `EntryT` primary.** `tests/mutations/test_resolvers.py` carries an `autouse` `registry.clear()` fixture (`::_isolate_registry`), so declaring an `Entry` primary inside `_build_item_schema` cannot strand a registration into a later test — the order-dependent `DuplicatedTypeName` class `docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list` warns about does not apply. Nothing outside `tests/` registers a competing `Entry` primary.
- **No fail-open shapes in the added assertions.** Grepping every added line for `try:` / `except` / `pytest.raises` / `assertRaises` / `or True` / a bare `assert x or …` returns only the two narrow `pytest.raises(ConfigurationError, match=…)` lines belonging to the **concurrent** session's 16-line append. `assert payload.get("errors"), payload` fails on an absent key rather than passing; `assert result["errors"] == []` is exact, not a truthiness test. The one `or` in the diff — `field.graphql_name or field.python_name` — sits inside a set-equality assertion against an explicit four-name literal, so a dropped or renamed member changes the set and fails the row; it cannot convert "cannot determine" into "permit", and `assert error_type is FieldError` guards the row against passing on the wrong type entirely.
- **The one working-tree failure inside this pass's write set was correctly left alone.** `ConnectionWindowBounds` appears **0** times in `django_strawberry_framework/optimizer/nested_planner.py` at `HEAD` and **5** times live, that file is dirty `31/32` and on the plan's baseline-dirty list, and this pass's only hunks in `tests/optimizer/test_walker.py` are at `@@ -25,6 +25,7 @@` and `@@ -4771,30 +4772,80 @@` while the failing assertion is at line 3577. Re-pinning it would have written this cycle's opinion onto a production contract mid-flight in another session, which `AGENTS.md` rule 34 forbids. The build report's `1 failed, 747 passed, 1 skipped` on the focused scope reproduced exactly.
- **The concurrent session's work in the dirty file is intact.** `tests/mutations/test_inputs.py` is `+164 / -0` — zero deletions — and the concurrent `@@ -1462,3 +1610,19 @@` hunk still carries all 16 of its lines (`::test_editable_input_fields_normalizes_its_declared_sequences`) unreflowed, with this pass's two inserts sitting mid-file in separate hunks. Spot-checked against the diff rather than taken on trust.
- **Tier placement is right and the tier's own rule is respected.** The three new live rows drive `/graphql/` through `graphql_client.post_graphql` / `assert_graphql_success` (`test_products_api.py:41-44`), so they stay inside `examples/fakeshop/test_query/README.md`'s governing rule — the raw-envelope drop-out is not invoked, correctly, since the subject is authorization and payload shape rather than the request envelope. `create_users(1)` / `seed_data(1)` open every new row per `AGENTS.md`, and the inline `models.Item.objects.create(...)` for the write target follows the file's own 25-site convention at `HEAD` rather than hand-rolling the catalog.
- **Floor verification exists and reproduces as recorded.** The venv at `<scratchpad>/dsf-floor-036` resolves **Python 3.10.19 / django 5.2.16 / strawberry-graphql 0.316.0**, matching `docs/builder/BUILD.md` `## Floor verification` read there rather than from memory. Both recorded commands were re-run: the three new live rows → `3 passed`, the whole `test_products_api.py` → `132 passed`, both exactly as recorded. The shared `.venv` was not mutated toward the floor — `uv pip list` reads `django 6.1` / `strawberry-graphql 0.324.0` on Python 3.14.2.
- **The tree's own gates are clean on this pass's files.** `git diff --check HEAD --` over the six paths exits 0; `ruff format --check` reports 6 files already formatted; `ruff check` passes; `scripts/check_trailing_commas.py --check` exits 0 tree-wide; `scripts/check_citations.py` reports `OK: 933 citations resolve`, the same figure the build report records, so the two new `path::QualifiedName` citations in `tests/test_permissions.py` resolve and neither is wrapped across a line.
- **Every dispatched box is closed by a real bound, not a relabelled detection.** Each of the seven ticks names an input or state now refused that was previously accepted: a `TODO` anchor that no longer exists, a codename collapse now caught at the live tier, a post-`delete()` snapshot now caught in two tiers, a hand-restated selection now derived through production, a fifth `FieldError` member now refused by set equality, and a `Meta.interfaces` bind hoist now caught at two call sites.

### Temp test verification

- No temp tests were written under `docs/builder/temp-tests/036/`. None was needed: every suspicion this review formed about a non-distinguishing assertion was settled by re-running the boundary's own mutation and reading the node-id set, which is the stronger instrument.
- `scripts/review_inspect.py` was run on the four files clearing the 50-line outside-the-package threshold, each with `--output-dir docs/shadow`: `examples/fakeshop/test_query/test_products_api.py`, `tests/mutations/test_inputs.py`, `tests/mutations/test_resolvers.py`, `tests/optimizer/test_walker.py`. Four `.overview.md` / `.stripped.py` pairs written under `docs/shadow/` (gitignored, read-only, never cited by line number here). No skip is claimed for any file in the diff; `tests/mutations/__init__.py` and `tests/test_permissions.py` are comment-only edits below every threshold.
- Scratch paths used, all outside the repository: `<scratchpad>/w3-rerun/` (my own pristine copies and markers, empty of markers at pass end) and read-only inspection of R3's `<scratchpad>/proofs/pristine/`.

### Notes for Worker 1 (spec reconciliation)

The spec and the rationale companion were read as context only and neither was written; the four R1 artifacts were read and not written. Items below are routed, not acted on.

- **Endorsed and unchanged:** every item already in this artifact's own `### Notes for Worker 1` section. Two of them were re-derived here and hold — `grep -rn 'only_fields\|deferred_loading' tests/mutations/` is still 0 occurrences (so the `## Test plan` bullet naming that file remains false), and `grep -rn --include='*.py' 'TODO(spec-036' .` returns nothing tree-wide.
- **Deferred DRY follow-up, for the deferred-work catalog:** the 9-site denial-assertion block in `examples/fakeshop/test_query/test_products_api.py` (7 pre-existing at `HEAD`, 2 added by this pass) wants a `_assert_denied(response)` helper. Deliberately not done here — Maintainer Decision B's additive-only mitigation covers the dirty file, and this file, though clean, was under the same repair-pass discipline.
- **Escalated: a false docstring in the seed helper every catalog and auth test opens with.** `examples/fakeshop/apps/products/services.py::create_users` says it "Also creates one ``staff_<n>`` **superuser** per unit for convenience", while the code it documents calls `create_user(..., is_staff=True, ...)` with no superuser flag, and `test_products_api.py::_login_with_perm`'s docstring states the correct fact ("``is_staff=True`` but NOT a superuser") to justify why granting an explicit `Permission` exercises the codename path at all. Two docstrings in the repo disagree about the same user, and the wrong one sits on the helper `AGENTS.md` makes the first line of every catalog and auth test — a reader who believes it would conclude the entire live write-authorization tier is passing through a superuser short-circuit. Pre-existing at `HEAD`, in a file on no cohort's write set and outside this cycle's audited surface, so it is not a finding against this pass. Resolution paths: (a) correct the `create_users` docstring in whichever cycle owns `examples/fakeshop/apps/products/services.py`; (b) route it to the deferred-work catalog for the next spec touching the fakeshop seed helpers; (c) if the intent was ever a real superuser, that is a behaviour question for the maintainer, not a docstring fix.
- **Not a spec matter, recorded because it is the second cycle to trip on it:** `docs/builder/BUILD.md`'s fenced proof loop puts the anchor check before the pre-mutation copy, while `scripts/prove_failability.py` copies first and then verifies the anchor. The outcome is equivalent — an unmatched anchor aborts the entry before anything is written, and the copy is a read of the target — but a worker following the prose and a worker running the tool are doing two different orderings, and the prose's stated rationale is specifically about the copy. Worth one sentence in whichever cycle next edits that section; this cycle lands no closeout agentflow edits.

### Review outcome

`review-accepted`.

No High and no Medium findings. Both Low findings are recording imprecisions in this artifact's own build report, and both are **addressed within this section** rather than deferred: the `review_inspect.py` obligation is Worker 3's and has now been discharged on all four qualifying files, and the two-baseline discrepancy is named with its cause and with the node-id sets that were never in disagreement. No re-loop is required and no source change is asked of Worker 2.

The acceptance gate is met on every clause: every dispatched box is closed by a real bound; all six failability proofs are recorded with the mutation, the listed node ids, the scope, a green same-scope baseline, a separately-recorded zero collection/setup-error count, and a byte-compared revert; **all six were independently re-run and all six node-id sets agree member for member**, so none was accepted on the builder's record alone and no mandatory re-run was declined; no boundary is weakly pinned, including the one that measured 1 row mid-pass and was remedied in-pass with a second, genuinely independent reader; the hot-path `none` declaration is true of the diff rather than merely stated; floor verification exists and reproduces at the canonical floor without having mutated the shared `.venv`; the public-surface check is clean; and the tree carries no mutation, no marker, and no edit of mine to any source or test file.

---

## Final verification (Worker 1)

Performed per `docs/builder/BUILD.md` `### Spawn-per-cycle dispatch` step 5 and `docs/builder/worker-1.md`
`## Final verification job`. Every figure below was **re-derived in this pass**, not inherited from the
build report or the review: `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on
prose` makes a stated count the reader's to re-measure, and the two prior passes agreeing is not itself a
measurement. No `git stash` / `git checkout` / `git restore` / `git worktree` was used, and this pass
edited no `.py` file.

**The six failability proofs were NOT re-run, deliberately.** They have been performed twice — by the
builder and by an independent reviewer whose six node-id sets agree member for member — and five of the
six targets are baseline-dirty with the concurrent session's uncommitted work. A third mutate/restore
round trip buys no new information and puts their work inside a third restore window. What this pass owes
instead is that the *records* are complete and that the tree is in the state they claim, and both are
verified below by read-only measurement.

### The two SKIPPED contracts are closed

Re-derived rather than inherited:

```shell
$ grep -rn --include='*.py' 'TODO(spec-036' .        # exit 1, no output
```

Both anchors are gone. Their replacements were read, not assumed: `tests/mutations/__init__.py`'s module
docstring now carries the mirror-package convention with `spec-036, shipped as DONE-036-0.0.11`
provenance and no staging grammar, and `tests/test_permissions.py`'s docstring names the two rows that
hold the lookup-scoping pin in `AGENTS.md` rule 27's `path::QualifiedName` form, each citation on **one**
source line (the wrap hazard that would make `check_citations.py` blind to it). R1d's SKIPPED row S4.7 is
closed too: `::test_update_item_missing_change_perm_is_denied_no_write` and
`::test_delete_item_missing_delete_perm_is_denied_no_write` both exist in
`examples/fakeshop/test_query/test_products_api.py`, so all three operations now carry a live denial row.

### Dispatched findings checklist audited

All seven boxes are `- [x]` and all seven landed. Confirmed by symbol, one grep per box:

| box | evidence |
|---|---|
| Repair 1 | `grep -c 'TODO(spec-036' tests/mutations/__init__.py` -> 0; docstring provenance read |
| Repair 2 | same on `tests/test_permissions.py` -> 0; the two `path::QualifiedName` citations read |
| Repair 3 | `::test_update_item_missing_change_perm_is_denied_no_write`, `::test_delete_item_missing_delete_perm_is_denied_no_write` present |
| Repair 4 | `tests/mutations/test_resolvers.py::test_delete_snapshot_materializes_connection_child_before_delete` + `test_products_api.py::test_delete_item_snapshot_carries_connection_child_edges` present |
| Repair 5 | `tests/optimizer/test_walker.py::test_mutation_payload_child_selections_flattens_slot_children_only` + the rewritten `::test_mutation_refetch_plan_drops_only_keeps_relations` present |
| Repair 6a | `tests/mutations/test_inputs.py::test_field_error_field_set_is_frozen` + `::test_field_error_wire_name_set_on_a_generated_payload_is_frozen` present |
| Repair 6b | `::test_fk_to_meta_interfaces_relay_target_uses_globalid_id` + `::test_meta_interfaces_primary_binds_a_node_slot_payload` present |

No box is over-ticked, so nothing is un-ticked, and **no obligation was deferred** — the two rows added
beyond the dispatch are acceptance-rule consequences on boundaries the dispatch already named, not new
scope. The two Low findings Worker 3 raised are both discharged inside its own review section
(`review_inspect.py` run on the four files clearing the outside-the-package 50-line arm — the four
`.overview.md` / `.stripped.py` pairs are on disk under `docs/shadow/` with matching mtimes; and the
two-baseline discrepancy named with its cause and with the node-id sets that never disagreed).

### The failability records, audited

Six boundaries, one entry each, every field `docs/builder/BUILD.md` `### What gets recorded` requires
present: the mutation stated as a removal rather than a perturbation, the scope as run (three carry a
`-k` fragment that is part of the scope), a **green** same-scope pre-mutation baseline, the failing node
ids **listed** rather than counted, a separately recorded collection/setup-error count of **0** on every
entry, and a byte-compared revert with its digest. No zero-row entry exists, so no **why 0** judgement is
owed and no harness-impossible interleaving is claimed.

The manifest is on disk and matches: `docs/builder/temp-tests/036/proofs.json` carries six entries whose
`scope` arrays are the invocations the artifact records, and a `scratch_root` outside the repository.

**The tree is in the state the records claim.** Every anchor matches exactly **once** in its live file —
`operations.py` change arm 1, delete arm 1; `resolvers.py` `snapshot = refetch_optimized(` 1;
`extension.py` `_named_children(field_selection, slot)` 1; `inputs.py` `codes: list[str]` 1;
`finalizer.py` `apply_interfaces(type_cls, definition)` 1 — which is the one check that can detect a
mutation left live, since `cp`/`cmp` inside the loop cannot. And each target's `git diff --numstat HEAD`
reads exactly the pass-start figure the artifact tabulates (`operations.py` clean, `resolvers.py` `11 6`,
`extension.py` `2 1`, `inputs.py` `31 38`, `finalizer.py` `24 8`), so all six reverts are real, no
concurrent write was clobbered, and no production line of this cycle's is in the tree. No
`ACTIVE-MUTATION.json` and no restore-failed marker exists anywhere under the scratch root.

**The weakly-pinned remedy is real and the second row is genuinely independent.** The `types/finalizer.py`
entry first measured 1 row, which
`docs/builder/BUILD.md` `### Acceptance rule: weakly pinned is revision-needed` makes `revision-needed`;
the response was more rows, never a weaker boundary. Both rows were read end to end rather than accepted
on the artifact's description. `::test_fk_to_meta_interfaces_relay_target_uses_globalid_id` asserts
`_inner_type(fields["rel_id"]) is relay.GlobalID` on the bound mutation's input class — the
`relation_id_scalar` consumer. `::test_meta_interfaces_primary_binds_a_node_slot_payload` asserts
`payload_object_slot(owner_type) == "node"` and then, off the materialized payload,
`"node" in payload_fields` with `"result" not in payload_fields` — the `payload_object_slot` consumer, a
different call site reaching a different observable (the payload's wire shape, which the first row never
touches). Neither assertion can substitute for the other, so this is two readers of one injection, not a
near-duplicate. One honest qualification for the record: the two rows share the setup helper
`_declare_meta_interfaces_mutation`, so they are independent in *assertion* and not in *fixture* — which
is the correct shape here, because the helper's own pre-finalize `assert not issubclass(..., relay.Node)`
is what makes either row witness the phase-2.5 ordering at all.

### The floor run exists and reproduces as recorded

The floor versions were read from `docs/builder/BUILD.md` `## Floor verification`, the single canonical
statement, and not from memory: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**.
The venv the artifact names is on disk outside the repository, and `uv pip list --python <venv>/bin/python`
plus `<venv>/bin/python -V` read back **Python 3.10.19**, `django 5.2.16`, `strawberry-graphql 0.316.0`,
`graphql-core 3.2.12` — exactly the recorded resolution, and a genuinely different point in the supported
range from the shared `.venv`. Both recorded commands (`3 passed` on the three new live rows, `132 passed`
on the whole `test_products_api.py`) are reproducible as recorded and were re-run by Worker 3 to the same
figures; this pass confirms the record and the environment read-only rather than rebuilding either. The
shared `.venv` was not mutated toward the floor.

### Hot-path `none` is true of the diff

Not merely stated. `git diff -- django_strawberry_framework/__init__.py` is empty; the five production
files a proof touched all read their pass-start numstat, so none carries an R3 edit; and R3's declared
write set is six test paths whose numstats re-derive digit for digit
(`118 0` / `6 5` / `164 0` / `80 5` / `68 17` / `6 7`). Nothing this pass added runs per request, per
resolver, per row, per connection, or per outbound message, so the plan's conditional declaration
resolves to `none` correctly and no before/after number is owed.

### No fail-open shape landed

Read for the catalogued shapes rather than trusting a green suite (`docs/builder/worker-1.md`
`### Failability and fail-open checks`). The one `or` in the diff — `field.graphql_name or
field.python_name` — sits inside a set-equality assertion against an explicit four-name literal guarded by
`assert error_type is FieldError`, so it cannot convert "cannot determine" into "permit": a dropped,
renamed, or added member changes the set and fails the row. No clamp, no `getattr` default on a decision,
no bare `except`, and no truthiness test on a possibly-absent value was added. `assert payload.get("errors"),
payload` fails on an absent key rather than passing, and `assert result["errors"] == []` is exact.

### Spec changes made (Worker 1 only)

**None.** The spec status-line re-verification (`docs/builder/worker-1.md` `## Spec status-line
re-verification`) was performed: the spec's header block still reads `Status:` **SHIPPED** `0.0.11` for
card `DONE-036-0.0.11` with all five slices final-accepted and the unticked-checklist convention stated
explicitly, and R2's reconciliation left it accurate. Every spec item R3 routed under `### Notes for
Worker 1 (spec reconciliation)` was already discharged by R2 or is deliberately deferred, and R3's own
three re-derivations of R2's work hold:

- The `## Test plan` bullet homing the `only_fields` pin was corrected by R2 (R1c's `S3.17`), and R3's
  point that the pin has moved *further* into `tests/optimizer/test_walker.py` — now derived through
  `optimizer/extension.py::mutation_payload_child_selections` — strengthens the correction rather than
  changing it. Re-measured here: `grep -rn 'only_fields\|deferred_loading' tests/mutations/` is still 0
  occurrences, so R2's text is right and the old text would have been false.
- The `## Implementation plan` staged-anchor sentence states a rule, not a claim about the tree, so it
  needed no edit and needs none now that the rule is satisfied.
- DoD item 5 / the `## Test plan` live-tier write-authorization clause is now **true as written**, so the
  correct action was to leave it — recorded here so a later pass does not soften it to match the gap R3
  closed.

Two R3 routings are genuinely new deferred work and are carried into `docs/builder/bld-036-final.md`'s
`### Deferred work catalog` rather than acted on: the 9-site `_assert_denied` consolidation candidate
(judged at the integration pass) and the `create_users` docstring calling `staff_<n>` a superuser.

### Summary

R3 closed both SKIPPED contracts and all three weak pins in six test files with **zero** production
lines, so the cycle's headline gap — the spec's strongest promise (`FieldError` "byte-identical") having
no gate at all — is now pinned by two independently-failing rows, and the per-operation write-authorization
matrix is pinned at the tier the spec assigns it to. All seven dispatched boxes landed, no obligation was
dropped, six failability proofs carry every required field with 0 collection errors and byte-compared
reverts, the one weakly-pinned boundary was remedied in-pass with a genuinely independent second reader,
the floor run exists at the canonical floor and reproduces, the hot-path `none` is true of the diff, and
the tree carries no live mutation. The four suite failures in the working tree are the concurrent
session's half-landed production work, mechanically attributed (`ConnectionWindowBounds`: 0 occurrences in
`optimizer/nested_planner.py` at `HEAD`, 5 live; the failing row's `def` at line 3568 while this pass's
hunks are at lines 25 and 4771) — recorded and escalated, never graded against this cycle.

Final status: `final-accepted`.
