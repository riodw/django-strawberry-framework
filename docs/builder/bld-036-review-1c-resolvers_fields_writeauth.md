# Build: R1c — conformance audit: the write resolvers, the field factory, write authorization, the transaction boundary

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md` (Slice 3; Decisions 8, 9, 10, 15; Definition of done item 4; the named `## Edge cases and constraints` bullets)
Rationale companion: `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` (Decisions 8, 9, 10, 15 read in full)
Build plan: `docs/builder/build-036-mutations-0_0_11.md`
Status: final-accepted

---

## Review (Worker 3)

### Method, and which tree each statement measures

This is a conformance audit, not a build review. There is no Worker 2 pass and no builder-recorded failability proof in this cohort; the build plan declares every R1 cohort **read-only over source and tests**.

- **Every conformance grade below measures the read-only `HEAD` snapshot** at commit `7426e7e7d8aa447e89fee75088447d6a506dec12`, materialized outside the repo at
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4a12072-1e3a-4913-8249-dd800f1972ce/scratchpad/head-036/`.
  Source line numbers quoted inline are snapshot line numbers (per-cycle-artifact convenience, `START.md` "Temp artifact conventions"); every graded row cites the symbol-qualified form.
- **No `git stash` / `git checkout` / `git restore` / `git worktree` was run.** No source or test file was edited or reverted.
- **One test run was performed and it measured the LIVE (dirty) tree, not `HEAD`:**
  `uv run pytest tests/mutations/test_fields.py tests/mutations/test_permissions.py --no-cov -q` → `53 passed in 4.37s`, 8 xdist workers, Django 6.1, Python 3.14.2. It is evidence about the working tree only. It is also direct evidence the tree has diverged: those two files carry **37** `def test_` definitions at `HEAD` (14 in `test_fields.py`, 23 in `test_permissions.py`, measured `grep -n 'def test_'` on the snapshot) against **53** collected rows live.
- `scripts/review_inspect.py` was run with `--output-dir docs/shadow` over all five source files in territory. **Those runs read the LIVE file**, so their structural output is used only for DRY / import-boundary / repeated-literal signal, never for a conformance grade. Every finding traced back to a `HEAD` read before it was written down.
- **Every candidate SUPERSEDED row was checked against the ORIGINAL implementing commit before being graded.** `HEAD` differing from the spec does not by itself mean later work changed it — the spec may have been wrong on the day it shipped, which is STALE-DESCRIPTION and makes R2 write something different. The reference is `git show 4b26b94e:<path>` (`4b26b94e` "Finish docs/spec-036-mutations-0_0_11.md", the commit that shipped the pipeline; `git log --diff-filter=A -- django_strawberry_framework/mutations/resolvers.py` and the file's log establish it). That check re-graded one row (**E3**) and supplied real attribution for two others (**D8.4b**, **D8.5b**), so it earned its cost.

**Attribution finding worth carrying forward:** three rows were superseded **inside the `0.0.11` cut itself**, by the maintainer review-round commit `c09793ee` "Fix async-permission bypass, create-validation parity, explicit-null and naive-datetime handling" (2026-06-18; `__version__` still `0.0.10`, i.e. before the joint `0.0.11` bump; `git merge-base --is-ancestor c09793ee HEAD` → ancestor). Its changes never went back into the spec. So not every divergence in this territory is `0.0.14` work — some is `036`'s own review round, and R2's `**Post-ship:**` framing would misattribute it. Named per-row below.

### Failability proofs

**None performed, deliberately — recorded rather than skipped silently.**

`docs/builder/BUILD.md` `### Reading is necessary, not sufficient: the failability proof` computes Worker 3's mandatory re-run floor *from Worker 2's own records*. This cohort audits shipped code; there are no recorded proofs, so the floor is arithmetically empty and an empty re-run set is legal here.

Beyond the floor, `docs/builder/BUILD.md` `## Failability proofs` licenses a discretionary proof under the Worker 3 carve-out. **I judged it too risky and skipped it**, per that section's own instruction to say so rather than proceed carelessly. The reason is specific, not general caution: the mutation-proof loop takes its pre-mutation reference from the **live** file, and every file in this territory is being actively rewritten by a concurrent session (`utils/write_transaction.py` +237, `tests/mutations/test_permissions.py` +245, `tests/mutations/test_write_transaction.py` +92, `tests/mutations/test_fields.py` +81, per the build plan's baseline). A copy taken at T, a pytest run spanning tens of seconds, and a restore at T+n would **revert any write the concurrent session made inside that window** — the precise harm `AGENTS.md` rule 34 forbids, and unrecoverable. A proof measuring the live tree would also be evidence about the live tree, which is not what this cycle grades.

The one weakly-pinned finding below (**M1**) is therefore established by absence-of-any-test greps, stated with the population and the exact command, not by mutation. `docs/builder/worker-3.md` `### Suspect the fixture before accepting "untestable"` was applied to it: the fixture *can* express the missing case (see M1), so the gap is about the suite, not the harness.

### The headline: the shipped write pipeline has no owning spec, and `spec-036` is the only spec that describes it

Before the inventory, the structural fact that explains most of it. The `0.0.14` write-transaction / concurrency hardening — the completion-spanning `DjangoSchema` transaction, the `Meta.select_for_update` row lock, single-write-alias pinning, the `conflict` envelope, the immutable authorized-pk snapshot, the phased alias guard, the strict-bool authorization contract — **has no spec file at all**:

```shell
ls docs/SPECS/ | grep '0_0_14'
# spec-041-channels_router  spec-042-debug_toolbar  spec-043-test_client  spec-044-debug_extension
# spec-045-visibility_boundary  spec-046-transport_security  spec-047-resource_policy
# spec-048-secure_output_defaults  spec-049-dependency_ci_hardening
grep -rln 'DjangoMutationExecutionContext' docs/SPECS/
# docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md   (an unrelated 0.0.4 rationale)
```

Its only durable attribution is the `CHANGELOG.md` `## [0.0.14] - 2026-08-29` entry `CHANGELOG.md #"BREAKING: generated mutations require"`, plus `docs/README.md #"installs `DjangoMutationExecutionContext`"`. So the corpus's only *spec-level* description of the shipped write pipeline is `spec-036`, and `spec-036` describes the pre-`0.0.14` pipeline. Every `SUPERSEDED` row below inherits the same attribution problem, and I have written it once here rather than 12 times in the table.

Escalated to the maintainer under `### Notes for Worker 1 (spec reconciliation)`.

### High:

#### H1 — `spec-036` never mentions `DjangoSchema`, and actively instructs the construction that now fails

`grep -c 'DjangoSchema' docs/SPECS/spec-036-mutations-0_0_11.md` → **0**. `grep -on 'strawberry\.Schema' …` → **6 occurrences** (lines 25, 50, 59, 81, 86, 361).

At `HEAD` a generated mutation refuses to run under a plain `strawberry.Schema`, before any database work:

`django_strawberry_framework/utils/write_transaction.py::require_managed_write` — `raise ConfigurationError(_UNMANAGED_SCHEMA_MESSAGE.format(name=mutation_cls.__name__))`, reached from `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync #"with open_write_pipeline(mutation_cls) as using"` via `django_strawberry_framework/utils/write_transaction.py::open_write_pipeline`. Pinned live by `tests/mutations/test_write_transaction.py::test_plain_strawberry_schema_refuses_generated_mutations_before_writing`, and stated as `BREAKING` in the changelog.

Two of the six sites are load-bearing *instructions*, not incidental prose:

- `docs/SPECS/spec-036-mutations-0_0_11.md #"wires `mutation=Mutation` into"` (Slice 4) tells the implementer to wire `mutation=Mutation` into `strawberry.Schema(...)`. Following it today produces a schema on which every generated mutation raises `ConfigurationError`. The shipped fakeshop project does the opposite — `examples/fakeshop/test_query/README.md #"`DjangoSchema` rather than plain `strawberry.Schema`"` says so outright.
- `docs/SPECS/spec-036-mutations-0_0_11.md #"before `strawberry.Schema(...)` runs"` (Decision 12) is only about materialization ordering and stays true; it is listed so R2 does not over-rewrite it.

Why High: a spec contract the build does not deliver, on the schema-construction line every consumer of the write side must get right. Severity is not softened by the docs being correct — the spec is the contract.

**Cohort note:** the Slice 4 site is R1d's territory and the Decision 12 site is R1b's. The *pipeline* requirement is mine. R2 must fix all six in one pass; a partial fix leaves the spec contradicting itself.

#### H2 — Decision 8's transaction boundary is wrong in extent and in owner

Spec: `docs/SPECS/spec-036-mutations-0_0_11.md #"Steps 3–6 (authorize"` — "Steps 3–6 (authorize → validate → write → relation assignment → re-fetch / snapshot) run inside **one `transaction.atomic()`**", and the Slice 3 restatement `docs/SPECS/spec-036-mutations-0_0_11.md #"steps authorize"`, and DoD item 4's `#"steps 3-6 inside one"`.

`HEAD` differs on three counts:

1. **Extent.** The `atomic()` opens *before the locate* (step 2), not at authorize: `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync #"with open_write_pipeline(mutation_cls) as using"` wraps `coerce_lookup_id` → `locate_instance` → authorize → decode → write → re-fetch. It has to: the locate takes the row lock (`django_strawberry_framework/mutations/resolvers.py::locate_instance #"base_locked_queryset(model, alias, visible) if select_for_update else visible"`), and a lock outside the transaction is not a lock.
2. **Owner and lifetime.** The pipeline's `atomic()` is *nested inside* an outer transaction opened by the schema's execution context and held open through GraphQL response completion — `django_strawberry_framework/schema.py::DjangoMutationExecutionContext` / `django_strawberry_framework/utils/write_transaction.py::managed_write_transaction`. The spec's "one `transaction.atomic()`" is now the inner of two, and the outer is what makes an unserializable payload roll the write back.
3. **Failure surface.** The spec says a failure in relation assignment or the snapshot rolls the write back. At `HEAD` a *completion* failure does too, and every error-envelope return calls `transaction.set_rollback(True, using=using)` first — `django_strawberry_framework/mutations/resolvers.py::error_payload_builder #"transaction.set_rollback(True, using=using)"` — so a `FieldError` envelope can never commit a partial write. The spec states none of this.

Why High: the spec asserts an atomicity guarantee whose actual extent, owner, and failure surface all differ. A reader reasoning about where a rollback boundary sits gets the wrong answer in three places at once.

#### H3 — Decision 8 step 5's M2M "target model's default manager" clause is superseded by a visibility check, and the spec contradicts itself about it

Spec: `docs/SPECS/spec-036-mutations-0_0_11.md #"the target model.s default manager"` — "related objects are looked up through the **target model's default manager** (no per-mutation queryset hook in `0.0.11`)". DoD item 4 and the M2M edge case repeat it.

At `HEAD` every relation id — FK, OneToOne, and each M2M member — is type-checked and then **visibility-checked through the related model's primary `DjangoType`'s `get_queryset`**, with the default manager only as the no-registered-primary fallback:

`django_strawberry_framework/utils/write_values.py::decode_visible_relation_ids #"confirms the whole set"` → `visible_related_objects`, reached from `django_strawberry_framework/mutations/resolvers.py::_decode_relation_id_list` and `::_decode_single_relation_id`. Pinned by `tests/mutations/test_resolvers.py::test_m2m_hidden_related_id_is_field_error`, `::test_create_raw_pk_m2m_hidden_member_is_field_error_no_visibility_leak`, `::test_create_raw_pk_fk_hidden_target_is_field_error_no_visibility_leak`, and the fallback by `::test_raw_pk_relations_with_no_registered_primary_use_default_manager_existence`.

The spec already states the *correct* contract elsewhere — `docs/SPECS/spec-036-mutations-0_0_11.md #"a permitted writer can never attach a row they could not see"` in `## User-facing API`, and the relation-decode edge case's "a well-formed id for a row the caller cannot see … surfaces a `FieldError`". So the spec asserts both contracts and they are incompatible: a default-manager lookup cannot produce the no-visibility-leak guarantee the same document promises.

Why High: a security-relevant contract (can a permitted writer attach a row they cannot see?) that the spec answers two different ways. A reader who lands on Decision 8 step 5 first concludes the visibility check does not exist.

### Medium:

#### M1 — The AR-M5 delete-snapshot **connection-child** half is implemented and pinned by nothing

Spec: `docs/SPECS/spec-036-mutations-0_0_11.md #"including nested selected relations and connection children"` (Decision 8 step 6 and the delete-snapshot edge case, 2 occurrences) — the delete snapshot must cover the complete response selection **including nested selected relations and connection children**, fully evaluated before `delete()`.

The implementation exists and is reachable: `django_strawberry_framework/mutations/resolvers.py::refetch_optimized #"force_load"` evaluates the planned queryset (`rows = list(queryset)`), populating `_prefetched_objects_cache`, and the selection extractor `django_strawberry_framework/optimizer/extension.py::mutation_payload_child_selections` navigates the payload slot the way the connection extractor navigates `edges { node }`.

**Nothing in any test tree exercises the connection-child branch of that guarantee.** What I searched, at `HEAD`:

- `grep -rn 'only_fields\|deferred_loading' tests/mutations/` → **0 occurrences**.
- Every file containing a delete-mutation document, cross-checked for `edges`: `tests/mutations/test_resolvers.py` → 0; `examples/fakeshop/test_query/test_mutation_atomicity.py` → 0; `examples/fakeshop/test_query/test_products_api.py` → 81 `edges` occurrences, none in a delete document (its delete document is `#"mutation($id: ID!) { deleteItem(id: $id) { "`, selecting `node { id name category { name } }`).
- The only pinning rows are the **plain-relation** half: `tests/mutations/test_resolvers.py::test_delete_snapshot_materializes_relation_before_delete` (a forward FK, `node { category { name } }`) and `examples/fakeshop/test_query/test_products_api.py::test_delete_item_happy_path`.

This is the **weakly-pinned** case, not SKIPPED (`docs/builder/BUILD.md` `### Acceptance rule: weakly pinned is revision-needed`): the connection-child branch could stop populating `_prefetched_objects_cache` before `delete()` and the suite would stay green.

The fixture is not the obstacle — `examples/fakeshop/apps/products/schema.py::ItemType #"\"entries\": \"both\""` gives `ItemType` an `entriesConnection`, so `deleteItem { node { entriesConnection { edges { node { id } } } } }` is expressible live today. The missing test is one live row asserting that selection returns its edges after the row is gone.

Recommended: one live row in `examples/fakeshop/test_query/test_products_api.py` selecting a connection child on the deleted node, plus one package row asserting `_prefetched_objects_cache` is populated on the detached snapshot. Routes to R3 as a **test-only** repair (so the plan's conditional hot-path and floor-verification declarations both resolve to `none`).

#### M2 — `_full_clean_or_field_errors`'s docstring states a `create` contract the module's own caller contradicts

`django_strawberry_framework/mutations/resolvers.py::_full_clean_or_field_errors` documents `#"exclude=None"` — "``exclude=None`` for create (validate all fields); the exclude-aware exclude list for update." That is the only `exclude=None` occurrence in the module (`grep -on 'exclude=None'` → 1 at snapshot line 1145; the live file has the same single occurrence at 1150).

Its only caller passes a computed list for create as well: `django_strawberry_framework/mutations/resolvers.py::_model_decode_step #"for BOTH create and update"` returns `exclude = _unprovided_exclude(model, provided)` on both branches, and `::_model_write_step` forwards it unconditionally. So the two docstrings in one module state opposite things, and the one describing the boundary's own parameter is the wrong one.

The behavior itself is defensible and deliberate (`_model_decode_step` explains it: create excludes unprovided fields so model defaults are not validated, mirroring `Model.objects.create()`), so the code is right and the comment is wrong. Spec-side, Decision 8 step 4 scopes `exclude` to `update` only — `docs/SPECS/spec-036-mutations-0_0_11.md #"exclude` is the set of fields"` — which reads as "create validates everything" and is superseded (row `D8.4b` below).

**The docstring is a survivor, not a fresh error, and that is why it matters.** `git show 4b26b94e:django_strawberry_framework/mutations/resolvers.py` shows create genuinely passing `exclude=None` when `036` shipped, so the sentence was *true* then. `c09793ee` ("Empty-value defaults un-omittable: `_run_create` now excludes unprovided fields from `full_clean` (the AR-H2-aware set, like update)") changed the caller and left the callee's docstring behind. The spec sentence and the docstring are therefore the same defect with two homes, and fixing one without the other leaves a reader able to find the wrong answer.

Why Medium: a stale comment directly on a validation boundary's parameter, which a future reader will trust over the caller. Routes to R3 with the spec edit (N8).

#### M3 — Decision 10 pins a literal lookup expression that is not what runs

Spec: `docs/SPECS/spec-036-mutations-0_0_11.md #"_default_manager.all(), info).get(pk="` — the lookup is spelled as `target_type.get_queryset(target_type.model._default_manager.all(), info).get(pk=<decoded id>)`.

`HEAD`'s `django_strawberry_framework/mutations/resolvers.py::locate_instance` composes four helpers instead: `initial_queryset(target_type)` → `apply_type_visibility_sync(...)` (which is also what supplies the `SyncMisuseError` discipline) → `pin_write_queryset(..., alias)` → `base_locked_queryset(model, alias, visible)` when `Meta.select_for_update`, then `.get(pk=node_id)`.

The *contract* holds exactly (visibility-only, `DoesNotExist` → not-found, no existence leak — pinned by `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` and `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`). Only the spelling is wrong, and it is wrong in a way that hides the alias pinning and the row lock. STALE-DESCRIPTION; the fix is to describe the composition rather than paste an expression.

#### M5 — A live `TODO(spec-036 Slice 3)` staged anchor for work that shipped in `0.0.11`

`tests/test_permissions.py #"TODO(spec-036 Slice 3)"` at `HEAD` (`git grep -n 'TODO(spec-036' $(git rev-parse HEAD)`, snapshot line 43):

```
# TODO(spec-036 Slice 3): add the package-level permission pin for mutation
# update/delete lookups.
# Pseudocode: declare a mutation target type whose get_queryset hides a real
# row through apply_cascade_permissions, run the mutation lookup helper against
# that row, and assert the resolver receives the same not-found FieldError shape
# as a genuinely missing id with no existence-leak branch.
```

This is my cohort's slice, and **the work it stages has landed** — in a different file. The contract it describes is pinned by `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` and `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`, both asserting exactly the not-found-shape-with-no-existence-leak property the pseudocode names. So the anchor is pure residue: it advertises Slice 3 as unbuilt five patch versions after `0.0.11` shipped.

`AGENTS.md` #"removed in the change that ships the slice" makes removal an obligation of the shipping change, and `docs/builder/BUILD.md`'s integration-pass step 6 makes an undischarged anchor a finding regardless of whether the spec's `## Slice checklist` named the file — which it did not, which is exactly how it survived. The `TODO(` grammar also has no gate: `grep -rln 'TODO(spec-' scripts/` finds nothing, so nothing in CI or pre-commit would ever have caught it.

Recommended for R3: delete the six comment lines. The behavior needs no new test — it has two. If the maintainer wants provenance preserved, replace with a non-TODO pointer naming the two rows that discharge it, per `AGENTS.md`'s "replace with non-TODO provenance such as `spec-<NNN>` / `DONE-<NNN>`" allowance.

The full `TODO(spec-036` population at `HEAD` is **5 occurrences**, and only two are live source residue: `tests/test_permissions.py:43` (mine, above) and `tests/mutations/__init__.py:3` (R1a's, already recorded by that cohort). The other three are the spec's and `spec-037`'s own *descriptions* of the anchor discipline, which are prose about anchors rather than anchors, and must not be swept.

#### M4 — Decision 15's `has_permission` arity: verified against `docs/README.md` and **not** a defect

Raised in the dispatch brief as a suspected High-severity documentation defect; I checked it and it does not hold, so it is recorded here rather than dropped (`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`, same principle).

- Spec, Decision 15 first bullet: each permission class has `has_permission(info, mutation, operation, data, instance)`.
- Spec, Decision 15 second bullet: `check_permission(self, info, operation, data, instance=None)`.
- `HEAD`: `django_strawberry_framework/mutations/permissions.py::DjangoModelPermission.has_permission` is `(self, info, mutation, operation, data, instance=None)`; `django_strawberry_framework/mutations/sets.py::DjangoMutation.check_permission` is `(self, info, operation, data, instance=None)`.
- `docs/README.md #"def has_permission(self, info, mutation, operation, data, instance=None)"` matches the first.

These are two different seams with two different arities, and all three sources agree on both. **No edit needed.** Recorded so a later pass does not re-raise it; the two arities differing is the design, not drift.

### Low:

#### L1 — `mutations/resolvers.py` is the shared substrate for three non-mutation flavors, while its sibling substrate was deliberately moved to `utils/`

`django_strawberry_framework/utils/write_transaction.py`'s module docstring states its own placement rule: `#"so the shared queryset helpers can consult the write context"` — it lives in `utils/`, not `mutations/`, to avoid a `utils` → `mutations` layering inversion.

The pipeline skeleton did not get the same treatment. `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync` and `::make_resolver_entries` are imported by `forms/resolvers.py`, `rest_framework/resolvers.py`, and `auth/mutations.py` (measured at `HEAD`: `grep -rn 'run_write_pipeline_sync' django_strawberry_framework/` → call sites in all three plus `mutations/resolvers.py`; `make_resolver_entries` → three flavors). So `mutations/` is a de-facto shared write substrate that three sibling subpackages depend on, which the module's own name does not advertise.

Not a correctness problem and not something to change in this cycle — the consolidation is unambiguously right, only its home is arguable. Escalated as an ownership question, not a demand.

#### L2 — `is_read_only_sql` is lexical and says so; recorded as a bounded limitation, not a fail-open finding

`django_strawberry_framework/utils/write_transaction.py::is_read_only_sql` classifies a statement read-only when its first comment-stripped token is `SELECT` or a savepoint verb — an **allow-list**, so an unrecognized statement is treated as a write and rejected (fail-closed). Its docstring names the residual itself: "a write-capable function invoked through ``SELECT`` passes", and bounds it correctly — on the pinned alias this is a phase-ordering check, and a statement that slips through still runs inside the pinned transaction and rolls back with it; cross-alias enforcement never uses it and rejects every statement outright.

I flag it only so the next reader does not mistake the lexical test for the security boundary. No change recommended.

#### L3 — The `pk`-drift diagnostic message is spelled twice

`grep -c 'pk changed from' django_strawberry_framework/mutations/resolvers.py` → **2** at `HEAD` (the whole package has exactly those 2: snapshot lines 284 and 1031). The update-path message in `::run_write_pipeline_sync` and the delete-path message in `::_delete_write_step` share a 14-word prefix and diverge only in the trailing clause ("an update must write the row that was authorized" / "a delete must remove the row that was located and authorized"). `review_inspect.py` surfaces it as the file's only repeated string literal: `2x ": the located instance's pk changed from"`.

`::reject_substituted_row` already takes `message=` precisely so callers keep operation-specific wording, so this is a deliberate trade, not an oversight. A shared prefix builder taking the tail clause would remove the duplication without losing the per-operation wording; worth doing only if that message is edited again.

### Graded contract inventory

Every row measures the `HEAD` snapshot. Grades use the build plan's vocabulary verbatim. Rows prefixed `X` are contracts `HEAD` implements that the spec states **nowhere** — the `0.0.14` divergence class.

| # | Contract (spec territory) | Grade | `HEAD` evidence |
|---|---|---|---|
| S3.1 | Slice 3: decode the `data:` input, and `id:` for update / delete | CONFORMS | `mutations/resolvers.py::_decode_relations`; `::coerce_lookup_id` |
| S3.2 | Slice 3: relation `GlobalID` type-checked against the target model; wrong-type → `FieldError` (AR-H4) | CONFORMS | `utils/write_values.py::decode_visible_relation_ids`; `tests/mutations/test_resolvers.py::test_wrong_type_globalid_yields_field_error_no_cross_model_lookup` |
| S3.3 | Slice 3: authorize via `check_permission` / `Meta.permission_classes` — before validation for create, after the visibility lookup for update / delete, denial → top-level `GraphQLError` | CONFORMS | `mutations/resolvers.py::authorize_or_raise`; `tests/mutations/test_permissions.py::test_denial_raises_top_level_not_field_error_envelope` |
| S3.4 | Slice 3: `full_clean()`; on update `exclude=<unprovided>` minus fields co-constrained with a provided field (AR-H2) | CONFORMS | `mutations/resolvers.py::_unprovided_exclude`; `::_unique_constraint_groups`; `tests/mutations/test_resolvers.py::test_partial_update_constraint_collision_keeps_unprovided_co_member` |
| S3.5 | Slice 3: write + assign M2M — replace-on-provide / clear-on-empty / unchanged-on-omit (AR-M1) | CONFORMS | `mutations/resolvers.py::_assign_m2m`; `tests/mutations/test_resolvers.py::test_m2m_replace_on_provide`, `::test_m2m_clear_on_empty_and_unchanged_on_omit` |
| S3.6 | Slice 3: re-fetch / snapshot through the optimizer, return the payload | CONFORMS | `mutations/resolvers.py::refetch_optimized`; `::build_payload` |
| S3.7 | Slice 3: **steps authorize→snapshot inside one `transaction.atomic()`** | SUPERSEDED | H2. `mutations/resolvers.py::run_write_pipeline_sync #"with open_write_pipeline(mutation_cls) as using"` opens before the locate and nests inside `schema.py::DjangoMutationExecutionContext` |
| S3.8 | Slice 3: async path in a single `sync_to_async(thread_sensitive=True)` call (AR-M4) | CONFORMS | `mutations/resolvers.py::run_pipeline_async` → `utils/querysets.py::run_in_one_sync_boundary` (one `sync_to_async(fn, thread_sensitive=True)`) |
| S3.9 | Slice 3: `validate_constraints()` `UniqueConstraint` violation caught as `ValidationError` before `save()` (Major-2) | CONFORMS | `mutations/resolvers.py::_full_clean_or_field_errors`; `tests/mutations/test_resolvers.py::test_unique_constraint_caught_by_validate_constraints_keys_all_sentinel` |
| S3.10 | Slice 3: multi-field constraints keyed to the `"__all__"` sentinel (AR-M3) | CONFORMS | `utils/errors.py::validation_error_to_field_errors`; same test as S3.9 |
| S3.11 | Slice 3: concurrent-race `IntegrityError` maps to the same envelope | CONFORMS | `mutations/resolvers.py::save_or_field_errors`; `::forced_save_or_field_errors`; `tests/mutations/test_resolvers.py::test_integrity_error_race_fallback_via_mocked_save` |
| S3.12 | Slice 3: `DjangoMutationField(MutationClass)` synthesizes `data:` + `id:` per operation and returns a `strawberry.field(...)` | CONFORMS | `mutations/fields.py::_synthesized_mutation_signature`; `::DjangoMutationField`; `tests/mutations/test_fields.py::test_per_operation_argument_signatures` |
| S3.13 | Slice 3: sync / async chosen by the same `is_async_callable` (construction-time) / `in_async_context()` (runtime) **asymmetry** `DjangoListField` uses | STALE-DESCRIPTION | Only the runtime half exists. `mutations/fields.py #"Runtime ``in_async_context()`` dispatch only"` states there is no consumer `resolver=` seam to inspect; `::DjangoMutationField` dispatches per call |
| S3.14 | Slice 3: `update` / `delete` lookups run through `target_type.get_queryset(...)` for **visibility only**; hidden row is not-found | CONFORMS | `mutations/resolvers.py::locate_instance`; `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` |
| S3.15 | Slice 3: `delete` fully materializes nested / connection-child relations before `delete()` in the same transaction (AR-M5) | CONFORMS | `mutations/resolvers.py::_delete_write_step`; `::refetch_optimized #"force_load"`. **Weakly pinned on the connection-child half — M1** |
| S3.16 | Slice 3: the post-write re-fetch keeps `select_related` / `prefetch_related` with no `.only(...)` under the mutation operation | CONFORMS | `mutations/resolvers.py::refetch_optimized` → `optimizer/extension.py::apply_connection_optimization`; walker-side gate is R1d's |
| S3.17 | Slice 3 package coverage: `tests/mutations/test_resolvers.py` … "the plan-shape pin (mutation re-fetch carries select/prefetch, no deferred loading)" | STALE-DESCRIPTION | `grep -rn 'only_fields\|deferred_loading' tests/mutations/` → 0. The `## Test plan`'s own AR-M7 split homes the exact-state pin in `tests/optimizer/test_walker.py`; the checklist bullet names the wrong file and contradicts it |
| D8.1 | Decision 8 step 1: decode incl. the AR-H4 wrong-model rejection before any pk lookup | CONFORMS | `relay.py::decode_model_global_id`; `mutations/resolvers.py::coerce_lookup_id` (`WRONG_MODEL` → invalid-id, pre-lookup) |
| D8.2 | Decision 8 step 2: locate through `get_queryset`; a miss returns a not-found `FieldError` on `id` | CONFORMS | `mutations/resolvers.py::locate_instance`; `::not_found_error` |
| D8.3 | Decision 8 step 3: authorize once; create before step 4 with `instance=None`; update / delete after step 2 with the located `instance` | CONFORMS | `mutations/resolvers.py::run_write_pipeline_sync #"authorize_or_raise("`; `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak` |
| D8.4a | Decision 8 step 4: update `exclude` carve-out; the loaded row supplies unchanged members; `exclude` governs re-validation, never which constraints are skipped | CONFORMS | `mutations/resolvers.py::_unprovided_exclude`; `tests/mutations/test_resolvers.py::test_unprovided_exclude_keeps_constrained_co_member_drops_unrelated` |
| D8.4b | Decision 8 step 4: `exclude` is scoped to `update` (so `create` validates every field) | SUPERSEDED | M2. `mutations/resolvers.py::_model_decode_step #"for BOTH create and update"` computes an exclude list for create too. **Day-one check: the spec was right at ship** — `git show 4b26b94e:django_strawberry_framework/mutations/resolvers.py` passes `exclude=None` on the create branch. Attribution: `c09793ee` ("create-validation parity" — create now excludes unprovided fields so a `JSONField(default=dict)` omitted on create is not validated against its own empty default), inside the `0.0.11` cut |
| D8.5a | Decision 8 step 5: `save()` / `delete()`, then assign relations, inside the transaction | CONFORMS | `mutations/resolvers.py::_model_write_step`; `::_delete_write_step` |
| D8.5b | Decision 8 step 5: related objects looked up through the **target model's default manager** (no per-mutation queryset hook) | SUPERSEDED | H3. `utils/write_values.py::decode_visible_relation_ids` routes through the related primary's visibility `get_queryset`; default manager is the no-primary fallback. **Day-one check: the spec was right at ship** — `git show 4b26b94e:…/resolvers.py` `::_assign_m2m` reads "Related objects resolve through the target model's default manager". Attribution: `DONE-038-0.0.12`, per `CHANGELOG.md #"closing the raw-pk visibility gap"` under `## [0.0.12]` |
| D8.6a | Decision 8 step 6: create / update re-read by pk as an optimizer-planned queryset | CONFORMS | `mutations/resolvers.py::refetch_optimized` |
| D8.6b | Decision 8 step 6: delete's planned load is fully materialized **before** step 5's `delete()`, returning a detached instance whose `pk` survives | CONFORMS | `mutations/resolvers.py::_delete_write_step` (snapshot, then `pipeline_write_phase()` + `_delete_or_field_errors(instance)` — deletes via the *located* instance so the snapshot keeps its pk) |
| D8.6c | Decision 8 step 6: the create / update re-fetch is by pk **without** the visibility filter | CONFORMS | `mutations/resolvers.py::refetch_optimized #"WITHOUT the"`; `tests/mutations/test_resolvers.py::test_refetch_skips_visibility_filter_after_authorized_write` |
| D8.7 | Decision 8 step 7: return the `<Name>Payload` | CONFORMS | `mutations/resolvers.py::build_payload`; `::payload_cls_for` |
| D8.CR4 | Decision 8 CR-4: relation decode runs **after** Authorize (create: authorize→decode; update: locate→authorize→decode), so an unauthorized caller triggers no relation visibility query | CONFORMS | `mutations/resolvers.py::run_write_pipeline_sync` — `authorize_or_raise` precedes `decode_step(instance)`; the ordering is restated as the module's security invariant, and `docs/README.md #"before relation decoding"` agrees |
| D8.T1 | Decision 8 AR-M4: steps 3–6 inside one `transaction.atomic()` | SUPERSEDED | H2 (duplicate statement of S3.7 in Decision-8 prose; graded separately because R2 edits two sites) |
| D8.T2 | Decision 8 AR-M4: the async path never interleaves ORM calls with `await`s; one `sync_to_async(thread_sensitive=True)` | CONFORMS | `utils/querysets.py::run_in_one_sync_boundary` |
| D8.A | Decision 8 opening parenthetical: `DjangoMutationField` mirrors `DjangoListField`'s `is_async_callable` construction-time / `in_async_context()` runtime asymmetry | STALE-DESCRIPTION | Same as S3.13; the parenthetical is the second site |
| D8.S | Decision 8 / `## Error shapes`: a sync path meeting an `async def get_queryset` raises `SyncMisuseError`, coroutine closed first, no `RuntimeWarning` | CONFORMS | `utils/querysets.py::apply_type_visibility_sync` via `mutations/resolvers.py::locate_instance`; `tests/mutations/test_resolvers.py::test_sync_misuse_async_get_queryset_from_sync_path` |
| D9.1 | Decision 9: the post-write re-fetch routes through `DjangoOptimizerExtension` for the response selection | CONFORMS | `mutations/resolvers.py::refetch_optimized` → `optimizer/extension.py::apply_connection_optimization` |
| D9.2 | Decision 9: G2 keeps `select_related` / `prefetch_related` and suppresses all `.only(...)` at plan-build because the operation is a mutation | CONFORMS | `optimizer/walker.py::_enable_only_for_operation` (exact-state mirror is R1d's) |
| D9.3 | Decision 9: FK-id elision stays enabled under G2's consumer-`.only()` loaded-check | CONFORMS | Optimizer-side; no resolver-side override exists in territory. Exact-state verification delegated to R1d |
| D9.4 | Decision 9 Medium-1: re-fetch by pk without the `get_queryset` visibility filter, as a documented GOAL crit-4 exception | CONFORMS | `mutations/resolvers.py::refetch_optimized`; `tests/mutations/test_resolvers.py::test_refetch_skips_visibility_filter_after_authorized_write` |
| D9.5 | Decision 9: `update` / `delete` *lookup* still runs through `get_queryset`; only the response re-fetch skips it | CONFORMS | `mutations/resolvers.py::locate_instance` vs `::refetch_optimized` |
| D9.6 | Decision 9 AR-M7: the handoff is discharged at two tiers (live behavioral, package exact-state) | CONFORMS | Both tiers exist; R1d owns their content. See S3.17 for the checklist's wrong file name |
| D10.1 | Decision 10: the lookup is `target_type.get_queryset(target_type.model._default_manager.all(), info).get(pk=<decoded id>)` | STALE-DESCRIPTION | M3. `mutations/resolvers.py::locate_instance` composes `initial_queryset` + `apply_type_visibility_sync` + `pin_write_queryset` + `base_locked_queryset` |
| D10.2 | Decision 10: a hidden row raises `DoesNotExist`, mapped to a not-found `FieldError` on `id`, indistinguishable from a missing row | CONFORMS | `mutations/resolvers.py::locate_instance`; `::not_found_error`; `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` |
| D10.3 | Decision 10 AR-H3: `get_queryset` scopes visibility, never write permission; write auth is the separate Decision 15 seam | CONFORMS | `mutations/permissions.py` module docstring + `::DjangoModelPermission`; the two seams are distinct call sites in `::run_write_pipeline_sync` |
| D15.1 | Decision 15: `Meta.permission_classes: list[...]`, each entry with `has_permission(info, mutation, operation, data, instance)` | CONFORMS | `mutations/permissions.py::run_permission_classes`; `::DjangoModelPermission.has_permission`. See M4 |
| D15.2 | Decision 15: default is a single `DjangoModelPermission` enforcing `add` / `change` / `delete` against `info.context.request.user` | CONFORMS | `mutations/permissions.py::DjangoModelPermission.has_permission`; `mutations/operations.py::_OPERATION_PERMISSION_ACTION`; `tests/mutations/test_permissions.py::test_operation_action_map_is_pinned` |
| D15.3 | Decision 15: an unauthenticated or under-privileged caller is denied by default | CONFORMS | `tests/mutations/test_permissions.py::test_anonymous_user_is_denied`, `::test_user_lacking_perm_is_denied`, `::test_anonymous_create_denied_top_level_error_no_write` |
| D15.4 | Decision 15: `check_permission(self, info, operation, data, instance=None)` is the overridable imperative seam; the default runs `Meta.permission_classes` | CONFORMS | `mutations/sets.py::DjangoMutation.check_permission` → `mutations/permissions.py::run_permission_classes` |
| D15.5 | Decision 15: for `create`, the check runs **before** decode / `full_clean()` / `save()` | CONFORMS | `mutations/resolvers.py::run_write_pipeline_sync`; `tests/mutations/test_permissions.py::test_under_privileged_create_denied` |
| D15.6 | Decision 15: for `update` / `delete`, it runs **after** the visibility lookup with the located `instance` | CONFORMS | `mutations/resolvers.py::run_write_pipeline_sync #"authorize_or_raise("` (`instance=instance`); `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak` |
| D15.7 | Decision 15: a denial **raises** a `GraphQLError` surfacing in top-level `errors`, never a `FieldError` envelope entry | CONFORMS | `mutations/resolvers.py::authorize_or_raise #"raise GraphQLError("`; `tests/mutations/test_permissions.py::test_denial_raises_top_level_not_field_error_envelope` |
| D15.8 | Decision 15 CR-7: argless construction — `mutation_cls()` once, each `permission_class()` argless | CONFORMS | `mutations/resolvers.py::authorize_or_raise #"mutation_cls().check_permission"`; `mutations/permissions.py::run_permission_classes #"permission_class().has_permission"` |
| DoD4.a | DoD 4: "steps 3-6 inside one `transaction.atomic()`" | SUPERSEDED | H2 (third site; R2 edits it separately) |
| DoD4.b | DoD 4: `DjangoMutationField` assigned with no class-attribute annotation, payload typed via a `strawberry.lazy` forward-ref (Major-3) | CONFORMS | `mutations/fields.py::_lazy_ref`; `::_synthesized_mutation_signature`; `tests/mutations/test_fields.py::test_no_class_attribute_annotation_builds_and_types_payload`, `::test_payload_lazy_ref_resolves_to_materialized_payload_after_bind` |
| DoD4.c | DoD 4: M2M assignment is replace / clear / unchanged **via the target default manager** | SUPERSEDED | H3 (second site of the default-manager clause) |
| DoD4.d | DoD 4: the `IntegrityError` fallback is covered by a mocked-`save()` test so the gate is met without a real race | CONFORMS | `tests/mutations/test_resolvers.py::test_integrity_error_race_fallback_via_mocked_save` |
| E3 | Edge case, `UNSET`-vs-`null` partial update: `UNSET` leaves the column unchanged and joins the `exclude` set; explicit `null` sets `None` if nullable, "else surfaces a `full_clean()` `FieldError`" | SUPERSEDED | The `UNSET` half CONFORMS. The explicit-`null` rejection happens at **decode**, not in `full_clean()`: `mutations/resolvers.py::_explicit_null_error` exists precisely because Django's `clean_fields` skips a `blank=True` empty value. **Day-one check re-graded this row from STALE-DESCRIPTION**: the spec's `full_clean()` claim was *also* never true — at `4b26b94e` such a value slipped past `full_clean` and failed at `save()` as an unattributed `"__all__"` NOT NULL error — and `c09793ee` ("Explicit null on a non-nullable column … now rejected at decode as a field-keyed FieldError naming the column, before any DB work") then made a *different* thing true. So the contract genuinely moved, inside the `0.0.11` cut. Pinned by `tests/mutations/test_resolvers.py::test_single_fk_explicit_null_on_required_is_field_keyed_null_error`, `::test_create_blank_true_null_false_fk_explicit_null_is_field_error`, `::test_explicit_null_error_allows_null_on_nullable_column` |
| E5 | Edge case, relation id decode failure: malformed, wrong-target-model (rejected before any pk lookup, never coerced cross-model), and hidden-row all surface a `FieldError` on the relation field, never a raw `DoesNotExist` | CONFORMS | `mutations/resolvers.py::_decode_single_relation_id`; `tests/mutations/test_resolvers.py::test_wrong_type_globalid_yields_field_error_no_cross_model_lookup`, `::test_relation_unresolvable_type_global_id_yields_field_error`, `::test_create_relation_uncoercible_pk_is_field_error_no_crash` |
| E7 | Edge case, unauthorized / anonymous write: denied before any write, top-level `GraphQLError`, not a payload | CONFORMS | `tests/mutations/test_permissions.py::test_anonymous_create_denied_top_level_error_no_write` |
| E9 | Edge case, async mutation with a sync `get_queryset`: the whole sync ORM pipeline in one `sync_to_async(thread_sensitive=True)` call | CONFORMS | `utils/querysets.py::run_in_one_sync_boundary`; `tests/mutations/test_resolvers.py::test_async_pipeline_create_happy_path` |
| X1 | `HEAD`: generated mutations **require** `DjangoSchema`; a plain `strawberry.Schema` raises `ConfigurationError` before any database work | SUPERSEDED | H1. `utils/write_transaction.py::require_managed_write`; `tests/mutations/test_write_transaction.py::test_plain_strawberry_schema_refuses_generated_mutations_before_writing`. Attribution: `CHANGELOG.md #"BREAKING: generated mutations require"` (`0.0.14`); **no owning spec exists** |
| X2 | `HEAD`: the mutation transaction spans **GraphQL response completion**, so an unserializable payload rolls the write back; serial top-level mutation fields get independent transactions | SUPERSEDED | `schema.py::DjangoMutationExecutionContext`; `tests/mutations/test_write_transaction.py::test_async_update_completion_failure_rolls_back`, `::test_async_update_success_commits`; `examples/fakeshop/test_query/test_mutation_atomicity.py` |
| X3 | `HEAD`: `Meta.select_for_update` defaults to `True` — a base-manager `SELECT … FOR UPDATE` constrained by the visibility queryset reduced to a pk subquery, never attached to the consumer's queryset; `False` opts out | SUPERSEDED | `mutations/resolvers.py::locate_instance`; `utils/write_transaction.py::base_locked_queryset`; `tests/mutations/test_resolvers.py::test_locate_instance_locks_through_base_manager_subquery_by_default`, `::test_locate_instance_opt_out_skips_the_lock` |
| X4 | `HEAD`: one router write alias is resolved once and pinned across the whole operation; a `get_queryset` hook re-routing to another alias fails closed | SUPERSEDED | `utils/write_transaction.py::resolve_write_alias`; `::pin_write_queryset`; `::check_instance_write_alias`; `tests/mutations/test_write_transaction.py::test_visibility_hook_switching_aliases_fails_closed` |
| X5 | `HEAD`: a retryable in-band `conflict` `FieldError` on `id` for a disappearing row — zero-row forced update, zero-target-row delete, and a vanished post-write re-fetch | SUPERSEDED | `utils/write_transaction.py::conflict_error`; `::forced_update_conflict_errors`; `mutations/resolvers.py::_delete_or_field_errors`; `tests/mutations/test_write_transaction.py::test_update_of_concurrently_deleted_row_returns_conflict_envelope`, `::test_delete_of_concurrently_deleted_row_returns_conflict_envelope`, `::test_missing_post_write_refetch_returns_conflict_envelope` |
| X6 | `HEAD`: a direct model `update` saves with `force_update=True` inside its own savepoint, so `save()`'s update-else-insert fallback cannot silently re-INSERT a concurrently deleted row | SUPERSEDED | `mutations/resolvers.py::forced_save_or_field_errors` |
| X7 | `HEAD`: an immutable authorized-pk snapshot is captured right after the locate, before the first consumer-controlled code, and every downstream claim compares against it through the pk field's own `to_python` | SUPERSEDED | `mutations/resolvers.py::run_write_pipeline_sync #"authorized_pk = None if instance is None"`; `utils/write_transaction.py::reject_substituted_row`; `::canonical_pk`; `tests/mutations/test_resolvers.py::test_pipeline_snapshots_authorized_pk_before_permission_hook`, `::test_delete_pipeline_rejects_pk_drift_during_authorization` |
| X8 | `HEAD`: the pipeline is database-read-only outside the write step; a transactionally-contained authorization phase is the one narrow non-pinned exception | SUPERSEDED | `utils/write_transaction.py::pipeline_alias_guard`; `::pipeline_write_phase`; `::authorization_phase`; `tests/mutations/test_write_transaction.py::test_pinned_alias_guard_rejects_writes_outside_the_write_phase` |
| X9 | `HEAD`: authorization results must be an actual `bool`; an `async def` hook's truthy coroutine is closed and raised as `SyncMisuseError`, and any non-bool is a `ConfigurationError` — never coerced from truthiness | SUPERSEDED | `mutations/permissions.py::_require_sync_bool_auth_result`; `tests/mutations/test_permissions.py::test_async_has_permission_is_rejected_not_bypassed`, `::test_awaitable_has_perm_is_rejected_not_bypassed`, `::test_hostile_non_bool_permission_result_keeps_configuration_error`. **Split attribution:** the coroutine-close half landed inside the `0.0.11` cut at `c09793ee` ("Async permission bypass (security): a coroutine return is truthy, so `if not check_permission(...)` never denied"); the strict-`bool` half and the `user.has_perm` seam are `0.0.14` |
| X10 | `HEAD`: authorization is **point-in-time** — a permission revoked by a concurrent transaction after the check is not re-observed; an explicit `Meta.permission_classes = []` is the AllowAny opt-out and resolves no auth state at all | SUPERSEDED | `docs/README.md #"The decision is point-in-time"`; `utils/permissions.py::auth_aliases_for_permission_classes`; `tests/mutations/test_permissions.py::test_empty_permission_classes_never_resolves_request_auth` |
| X11 | `HEAD`: a `PROTECT` / `RESTRICT` delete refusal returns the `FieldError` envelope instead of leaking Django's model and relation names in a top-level `GraphQLError` | SUPERSEDED | `mutations/resolvers.py::_delete_or_field_errors`; `tests/mutations/test_resolvers.py::test_delete_refused_by_protected_reference_is_envelope_not_graphql_error` |
| X12 | `HEAD`: the cooperative resource-policy deadline is checked **before** the transaction opens, so a refusal never has a partial transaction to unwind | SUPERSEDED | `mutations/resolvers.py::run_write_pipeline_sync #"check_deadline(info)"`; owned by `spec-047` (`DONE-047-0.0.14`) |
| X13 | `HEAD`: the pipeline skeleton and the resolver-entry pair are promoted shared machinery that the `ModelForm`, plain-form, serializer, and register flavors all ride | SUPERSEDED | `mutations/resolvers.py::run_write_pipeline_sync`; `::make_resolver_entries`; call sites in `forms/resolvers.py`, `rest_framework/resolvers.py`, `auth/mutations.py`. Attribution: `spec-038` / `spec-039` DRY promotions |
| R1 | Rationale companion, Decision 8 Revision 5: the create / update write-finalization tail is `_validate_save_assign_refetch_payload` | RENAMED | That symbol does not exist at `HEAD`. The tail is `mutations/resolvers.py::_model_write_step` plus the shared `::run_write_pipeline_sync` skeleton, and `::_model_write_step #"the prior ``_validate_save_assign_refetch_payload``"` records the rename itself |

### Summary count

Re-derived by tallying the Grade column of the table above, not asserted. The commands, run against this artifact so the reader can repeat them:

```shell
F=docs/builder/bld-036-review-1c-resolvers_fields_writeauth.md
awk '/^\| (S3|D8|D9|D10|D15|DoD4|E[0-9]|X[0-9]|R1)/' $F | wc -l          # 72
awk -F'|' '/^\| (S3|D8|D9|D10|D15|DoD4|E[0-9]|X[0-9]|R1)/ {g=$4; gsub(/ /,"",g); print g}' $F | sort | uniq -c
awk -F'|' '/^\| (S3|D8|D9|D10|D15|DoD4|E[0-9]|X[0-9]|R1)/ {print $2}' $F | tr -d ' ' | sort | uniq -d   # empty: no duplicate row id
```

| Metric | Count |
|---|---|
| Rows | 72 |
| CONFORMS | 47 |
| SUPERSEDED | 20 |
| STALE-DESCRIPTION | 4 |
| RENAMED | 1 |
| **SKIPPED** | **0** |

`47 + 20 + 4 + 1 = 72`. No row carries more than one grade, and no row id repeats.

Of the 20 SUPERSEDED, **13** are the `X` rows — contracts `HEAD` implements that the spec states nowhere — and **7** are spec text `HEAD` contradicts (`S3.7`, `D8.4b`, `D8.5b`, `D8.T1`, `DoD4.a`, `DoD4.c`, `E3`). By attribution: **13 + 2** are `0.0.14` or later card work, **3** landed inside the `0.0.11` cut itself at `c09793ee` (`D8.4b`, `E3`, and the coroutine-close half of `X9`), **1** is `DONE-038-0.0.12` (`D8.5b`), and **1** is `spec-047` (`X12`). Only the `X1` / `X2` / `X3` / `X5` / `X8` group is genuinely unattributable to a card, for the reason in the headline section.

**No SKIPPED contract.** Every contract in this cohort's spec territory is implemented at `HEAD`; the divergence is entirely spec-side (20 SUPERSEDED + 4 STALE-DESCRIPTION + 1 RENAMED = **25 rows routing to R2**, 0 routing to R3 as a code repair). The three code-side items are **M1** (a weakly-pinned branch — a missing *test*, not a missing implementation), **M2** (a stale docstring), and **M5** (a stale staged anchor). All three are test/comment repairs, so the build plan's conditional hot-path and floor-verification declarations for R3 both resolve to `none`.

### DRY findings

`scripts/review_inspect.py --output-dir docs/shadow` was run over all five territory source files (`mutations/resolvers.py`, `mutations/fields.py`, `mutations/permissions.py`, `utils/write_transaction.py`, `schema.py`), all exit 0. **The runs read the live tree**, so they are used for structural signal only. No file was skipped.

**Repeated string literals** (the DRY section), all files:

- `mutations/resolvers.py` — `2x ": the located instance's pk changed from"`. The only repeat in the file. Finding **L3**.
- `utils/write_transaction.py` — `2x "postgresql"`, both inside `_enforce_read_only_barrier`'s backend dispatch (a vendor test and its statement). Justified: they are two different uses of one vendor name in one function, and pinned by `tests/mutations/test_write_transaction.py::test_enforce_read_only_barrier_postgresql_sets_transaction_read_only`.
- `mutations/fields.py` — `2x "_mutation_meta"`, in `_validate_mutation_target`'s `hasattr` probe and its `__dict__.get` concreteness check. Justified: the two reads are deliberately different (MRO-visible vs own-attribute), and the docstring explains why an MRO lookup would be wrong.
- `mutations/permissions.py` — none.
- `schema.py` — `3x "extensions"`, `2x "execution_context_class"`, all in the `DjangoSchema.__init__` / `get_extensions` kwargs plumbing. Justified: they are Strawberry's own kwarg names, and a constant would obscure rather than help.

**Django / ORM markers** — every entry walked:

- `mutations/resolvers.py`: 5 `_meta` reads. `::_unprovided_exclude #"hasattr(field, \"column\")"` and `::_unique_constraint_groups` (`_meta.constraints`, `_meta.unique_together`, `_meta.get_fields()`) are the AR-H2 constraint-group derivation and have to read `_meta`; `::_delete_or_field_errors #"instance._meta.label"` keys `Model.delete()`'s per-model row count. All four justified, all pinned (`test_unprovided_exclude_*`, `test_delete_of_concurrently_deleted_row_returns_conflict_envelope`).
- `utils/write_transaction.py`: 2 `_meta` reads. `::canonical_pk #"model._meta.pk.to_python(value)"` is the canonical pk comparison that stops a `UUID` pk spelling the same row two ways (pinned by `tests/mutations/test_write_transaction.py::test_pks_match_canonicalizes_through_the_pk_field`); `::snapshot_target_state #"instance._meta.concrete_fields"` is the drift snapshot. Both justified.
- `mutations/fields.py`, `mutations/permissions.py`, `schema.py`: none.

**Control-flow hotspots** — Medium-tier attention applied to every entry:

- `mutations/resolvers.py::run_write_pipeline_sync` — 196 lines / 19 branch nodes, the largest in territory. It is large **because** it is the single-sited security ordering four flavors ride, and its 19 branches are almost entirely short-circuit returns on the error-envelope path. I do not recommend splitting it: `docs/builder/BUILD.md`'s DRY-first rule and the module's own docstring both make "the order is the `036` / `038` security invariant, in ONE place" the point, and decomposing it would put the ordering in two files. Recorded so a future pass does not "simplify" it back into a fork.
- `utils/write_transaction.py::pipeline_alias_guard` (120/4), `::authorization_phase` (73/7), `::_field_fingerprint` (79/11), `::_sql_statement_token` (30/11), `::_enforce_read_only_barrier` (55/6) — all are exhaustive type/backend dispatches with a fail-closed default arm, and each has a dedicated test row. No finding.
- `mutations/resolvers.py` remainder (`_decode_relations` 80/1, `locate_instance` 43/3, `refetch_optimized` 48/2, `_model_decode_step` 62/4, `_model_write_step` 52/6, `_delete_write_step` 47/2, `coerce_lookup_id` 47/2) — all dominated by docstring lines; branch counts are low. No finding.

**Imports** — cross-folder direction checked:

- `mutations/resolvers.py` imports from `..optimizer.extension`, `..relay`, `..resource_policy`, `..utils.{errors,inputs,permissions,querysets,write_transaction,write_values}`, `..exceptions`. All one-way (subpackage → root / utils / sibling subpackage), none inverted.
- `utils/write_transaction.py` imports only `..exceptions`, `..utils.errors`, `.canonical` — **no** `mutations` import, which is the placement rule its own docstring states. Confirmed held.
- `mutations/fields.py::_is_registered_mutation_target` imports `..forms.sets` **inside the function**, deliberately, to avoid a load cycle (`forms/sets.py` imports `mutations/sets.py`). Documented in `::_validate_mutation_target`. Justified.
- The one direction worth naming is **L1**: `forms/`, `rest_framework/`, and `auth/` all import the pipeline skeleton from `mutations/resolvers.py`, making `mutations/` a shared substrate. That is a home question, not a cycle.

**Cross-flavor duplication (the live risk the dispatch named):** measured and **absent**. `grep -rn 'run_write_pipeline_sync' django_strawberry_framework/` at `HEAD` finds the definition plus call sites in `forms/resolvers.py`, `rest_framework/resolvers.py`, `auth/mutations.py`, and `mutations/resolvers.py` itself (create/update and delete) — four flavors, one skeleton, no near-copy of the transaction/authorize ordering anywhere. `make_resolver_entries` is shared by three flavors the same way, and `open_write_pipeline` has exactly one call site because the skeleton is the only entry. This is the opposite of the failure mode the plan anticipated, and it is worth stating positively so a later pass does not un-share it.

**Existence challenge** (`docs/builder/worker-3.md` `### The existence challenge`): raised on nothing. The three candidates I weighed each have real multi-caller justification — `run_write_pipeline_sync` (four flavors), `make_resolver_entries` (three), `error_payload_builder` (four return paths inside one function, and it exists so `set_rollback` cannot be forgotten on one of them). None is a one-caller indirection.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. This cohort wrote no source file, and the file is not in the concurrent session's dirty set for this territory.

Note for R1d, which owns the export surface: the spec's Decision 5 names four public symbols, while `HEAD` additionally exports `DjangoSchema` and `DjangoMutationExecutionContext` per `docs/README.md #"are exported from the package root"`. That is R1d's row to grade against `__all__`; recorded here only because it is the same `0.0.14` divergence class as H1.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (`docs/README.md`, `CHANGELOG.md`, and `KANBAN.md` were **read** as `HEAD` evidence for attribution; none was edited, and the maintainer-set scope forbids it.)

### What looks solid

- **The security ordering is single-sited and correct.** `mutations/resolvers.py::run_write_pipeline_sync` is the one place locate → authorize → decode is expressed, for four write flavors. The spec's CR-4 guarantee — an unauthorized caller triggers no relation visibility query and gets no field-level decode feedback — holds exactly, and `docs/README.md #"before relation decoding"` states the same order. This is the single highest-value property in the territory and it is intact.
- **Every fail-open shape I hunted for is absent, and the near-misses fail closed.** Hunted specifically in the authorization path, the visibility lookup, and the relation-decode rejection, per `docs/builder/BUILD.md` `### Fail-open shapes`. Findings, all in the safe direction: `DjangoModelPermission.has_permission #"if user is None"` → deny; `_decode_single_relation_id #"getattr(relation_field, \"null\", False)"` → a missing `null` attribute reads as non-nullable, so the explicit `null` is rejected; `_has_mutation_protocol`'s four `getattr(..., None)` probes → a missing attr means "not a mutation", rejected; `_delete_or_field_errors #"per_model.get(instance._meta.label, 0)"` → an absent key defaults to 0, i.e. `conflict`; `forced_update_conflict_errors` → the probe's own `DatabaseError` re-raises the original rather than returning the retryable envelope; `is_read_only_sql` → an allow-list, so an unrecognized statement is a write. No clamp, no `or` fallback, no bare `except`, and no truthiness test on a possibly-absent value on any decision path in territory.
- **The authorization-result contract closes a real bypass class.** `mutations/permissions.py::_require_sync_bool_auth_result` refuses to coerce authorization from truthiness across all three seams (`has_permission`, `check_permission`, `user.has_perm`) — an `async def` deny-check returns a truthy coroutine and would otherwise read as allow. Six test rows pin it from both directions. The spec does not mention it, which is exactly why it is row X9.
- **The relation-decode rejection is uniform across FK, OneToOne, and M2M**, in one query per set, through one primitive (`utils/write_values.py::decode_visible_relation_ids`), with hidden and missing indistinguishable. Nine `test_resolvers.py` rows cover the matrix (wrong-type, unresolvable type, uncoercible pk, hidden member, raw-pk variants of each).
- **The delete payload's cache-eviction contract is protected by construction.** `_delete_write_step` deletes via the *located* instance, not the snapshot, because `Model.delete()` nulls the pk on the object it is called on. The reasoning is written down at the site, and a future refactor that "simplifies" it to delete the snapshot would break the payload silently — which is why the comment is load-bearing rather than decorative.

### Temp test verification

No temp tests written. The one absence claim (**M1**) is established by grep populations stated inline with their commands, and the one behavioral question I could not settle by reading (whether the connection-child selection is even expressible on the fakeshop fixture) was settled by reading `examples/fakeshop/apps/products/schema.py::ItemType` rather than by writing a test.

Disposition: n/a — nothing created under `docs/builder/temp-tests/036/`.

### Notes for Worker 1 (spec reconciliation)

R2 authors the spec edit from this section. Every SUPERSEDED / STALE-DESCRIPTION / RENAMED row appears below with the exact wrong text and what it should say. Per `docs/builder/BUILD.md` `## Spec rationale extraction`, the spec states the corrected contract **directly, without chronology**, and the history goes to the rationale companion as a `**Post-ship:**` bullet under the owning Decision.

**Escalated: the `0.0.14` write-pipeline hardening has no owning spec.** Nine `0.0.14` specs exist and none of them is it (`ls docs/SPECS/ | grep '0_0_14'`); `grep -rln 'DjangoMutationExecutionContext' docs/SPECS/` returns only an unrelated `spec-008` rationale. Its only attribution is `CHANGELOG.md #"BREAKING: generated mutations require"` and `docs/README.md`. Consequence: `spec-036` is the corpus's only spec-level description of the shipped write pipeline, so rows X1–X13 have nowhere to be *homed* — R2 can only fold them into `spec-036`'s Decisions, which makes `spec-036` retroactively the spec for work it did not scope. Resolution paths for the maintainer: (a) fold into `spec-036` as the pragmatic single home and say so in the rationale companion; (b) author a retrospective `spec-0NN-…-0_0_14` for the write hardening and have `spec-036` point at it; (c) leave `spec-036` scoped to `0.0.11` with a single forward pointer per Decision. This is a contract-level call, not a worker's (`docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`). **R2 should not pick one silently.**

---

**N1 — `DjangoSchema` is absent from the spec, and the spec instructs the construction that now fails (H1, row X1 / X2).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"wires `mutation=Mutation` into"` (Slice 4):

> `config/schema.py` wires `mutation=Mutation` into `strawberry.Schema(...)`.

Should say: `config/schema.py` wires `mutation=Mutation` into `DjangoSchema(...)` — a generated mutation refuses to run under a plain `strawberry.Schema`, because its transaction must span GraphQL response completion.

Also needed — a new clause in Decision 8's transaction paragraph and in `## Error shapes` stating: a generated mutation executed through a plain `strawberry.Schema` raises `ConfigurationError` before any database work, naming `DjangoSchema` as the fix (`utils/write_transaction.py::require_managed_write`).

`strawberry.Schema` has **6** occurrences in the spec (lines 25, 50, 59, 81, 86, 361). Grade them individually — the Decision 12 site `#"before `strawberry.Schema(...)` runs"` is about materialization ordering and stays correct. Lines 25, 50, 81, 86 fall in R1b's and R1d's territory; coordinate so the six are fixed in one pass, because a partial fix leaves the spec contradicting itself.

**N2 — Decision 8's transaction boundary, three sites (H2, rows S3.7 / D8.T1 / DoD4.a).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"Steps 3–6 (authorize"`:

> **Transaction and async boundary (AR-M4).** Steps 3–6 (authorize → validate → write → relation assignment → re-fetch / snapshot) run inside **one `transaction.atomic()`** — the write, its relation `.set(...)` calls, and the payload snapshot are atomic, so a failure in relation assignment or the snapshot rolls the write back and a successful payload reflects a committed row.

Should say: the pipeline opens **one `transaction.atomic()` spanning locate → authorize → decode → validate → write → relation assignment → re-fetch / snapshot** (the locate is inside it because it takes the row lock), and that block is itself **nested inside the completion-spanning transaction `DjangoSchema`'s execution context opened for this mutation field** — so a failure in relation assignment, the snapshot, **or GraphQL response completion** rolls the write back, and every `FieldError` envelope return marks the transaction for rollback before building the payload, so an error envelope never commits a partial write.

Same correction at the two sibling sites: `#"steps authorize"` (Slice 3 checklist) and `#"steps 3-6 inside one"` (DoD item 4).

**N3 — Decision 8 step 5's M2M default-manager clause contradicts the spec's own no-visibility-leak guarantee (H3, rows D8.5b / DoD4.c, and the M2M edge case).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"the target model.s default manager"`:

> related objects are looked up through the **target model's default manager** (no per-mutation queryset hook in `0.0.11`)

Should say: related objects are resolved through the **related model's primary `DjangoType` visibility `get_queryset`**, confirming the whole provided set in one `pk__in` query — the target model's default manager only when the related model has no registered primary type. A hidden or missing member is the same field-keyed `FieldError`, indistinguishable, so a permitted writer can never attach a row they could not see.

This makes Decision 8 step 5 agree with the spec's existing `## User-facing API` guarantee `#"a permitted writer can never attach a row they could not see"`, which is currently the *other* half of a self-contradiction. Repeat the correction at DoD item 4's M2M clause and at the `## Edge cases and constraints` many-to-many bullet.

**N4 — The `is_async_callable` asymmetry claim, two sites (rows S3.13 / D8.A).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"is_async_callable` detection"` (Decision 8's opening parenthetical) and `#"construction-time, consumer resolver"` (Slice 3 checklist) both assert `DjangoMutationField` mirrors `DjangoListField`'s two-half asymmetry.

Should say: `DjangoMutationField` uses the **runtime half only** — the single synthesized resolver dispatches per call via `in_async_context()`, so one factory output serves both `schema.execute_sync` and `await schema.execute`. The construction-time `is_async_callable` half does not apply because the mutation pipeline is package-owned and there is no consumer `resolver=` seam to inspect. (`mutations/fields.py #"Runtime ``in_async_context()`` dispatch only"` states this at the source.)

**N5 — The `## Test plan`'s "at construction" claim (same root cause as N4).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"sync vs async resolver selection at construction"`:

> `test_fields.py` — … sync vs async resolver selection at construction.

Should say: sync vs async resolver selection **at runtime**. `HEAD`'s row is `tests/mutations/test_fields.py::test_sync_and_async_resolver_selection`, whose own docstring reads "(runtime dispatch)", paired with `::test_async_resolver_selection_works`.

**N6 — The Slice 3 checklist homes the G2 plan-shape pin in the wrong file (row S3.17).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"the plan-shape pin"`:

> Package coverage: `tests/mutations/test_resolvers.py` … and the plan-shape pin (mutation re-fetch carries select/prefetch, no deferred loading).

Should say: the exact `only_fields` / `deferred_loading` plan state is pinned in the `tests/optimizer/test_walker.py` mirror, per this spec's own AR-M7 two-tier split; `tests/mutations/test_resolvers.py` owns the pipeline behavior. Measured: `grep -rn 'only_fields\|deferred_loading' tests/mutations/` → **0 occurrences** at `HEAD`, and `tests/mutations/test_resolvers.py`'s module docstring says the `CaptureQueriesContext` assertion lives in the fakeshop suite. The checklist bullet currently contradicts the `## Test plan` in the same document; the Test plan is the correct one.

**N7 — Decision 10 pastes a lookup expression that is not what runs (row D10.1, M3).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"_default_manager.all(), info).get(pk="`:

> The `update` / `delete` row lookup is `target_type.get_queryset(target_type.model._default_manager.all(), info).get(pk=<decoded id>)` — the same visibility queryset every read surface uses …

Should say: the lookup runs the target type's visibility `get_queryset` (including any `apply_cascade_permissions` its hook calls) over the type's initial queryset, **pinned to the operation's write alias**, and — when `Meta.select_for_update` is on — locked through the model's base manager with that visibility queryset reduced to a pk subquery, then fetched by pk. Describe the composition rather than pasting an expression; the current spelling hides both the alias pinning and the row lock. (`mutations/resolvers.py::locate_instance`.)

**N8 — Decision 8 step 4 implies `create` validates every field (row D8.4b, M2).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"exclude` is the set of fields"` scopes `exclude` to `update` only.

Should say: `exclude` is computed for **both** operations — `create` excludes unprovided fields so their model defaults are not validated (mirroring `Model.objects.create()`), `update` excludes unprovided fields so an unsent column keeps its stored value — and **both** keep validating any unprovided field co-participating in a uniqueness check with a provided one (the AR-H2 carve-out is not update-only). (`mutations/resolvers.py::_model_decode_step #"for BOTH create and update"`.)

Paired code repair for R3: `mutations/resolvers.py::_full_clean_or_field_errors`'s docstring still says `#"exclude=None"` for create, which its only caller contradicts. Fix the docstring, not the behavior.

**N9 — The `UNSET`-vs-`null` edge case attributes the explicit-`null` rejection to `full_clean()` (row E3).**

Wrong text, `docs/SPECS/spec-036-mutations-0_0_11.md #"else surfaces a `full_clean()`"`:

> explicitly passing `null` sets it `None` only if the column is nullable, else surfaces a `full_clean()` `FieldError`

Should say: an explicit `null` on a nullable column clears it; on a `null=False` column it is rejected **at decode** as a field-keyed `FieldError`, because Django's `clean_fields` skips a `blank=True` field whose value is empty and `None` is empty — so a `blank=True, null=False` column would slip past `full_clean()` and fail at `save()` as an unattributed `"__all__"` NOT NULL constraint error, after a write was attempted. (`mutations/resolvers.py::_explicit_null_error`; the same guard on the relation side in `::_decode_single_relation_id`.) The `UNSET` half of the bullet is correct as written.

Attribution for the rationale companion: `c09793ee`, **inside the `0.0.11` cut**, not later work. Note for the `**Post-ship:**` bullet: the spec's original `full_clean()` claim was never true either — at `4b26b94e` the value fell through to a `save()`-time `IntegrityError` — so the companion should record that the sentence was wrong at ship *and* that the contract subsequently moved. Framing it as purely post-ship supersession would preserve the false premise.

**N10 — Rows X3–X13: contracts `HEAD` implements that the spec states nowhere.** Each needs a new clause in the owning Decision, subject to the escalated homing question above. Grouped by owner so R2 can work Decision by Decision:

- **Decision 8** (the pipeline): X3 `Meta.select_for_update` default `True` and its base-manager / pk-subquery lock shape; X5 the retryable in-band `conflict` `FieldError` on `id` (zero-row forced update, zero-target-row delete, vanished post-write re-fetch); X6 the update's `force_update=True` save in its own savepoint; X7 the immutable authorized-pk snapshot taken before the first consumer-controlled code, plus canonical-`to_python` pk comparison and the pk-drift backstop; X11 the `PROTECT` / `RESTRICT` refusal returning the envelope rather than leaking model and relation names; X12 the cooperative deadline checked before the transaction opens (`spec-047` owns the mechanism — a pointer, not a restatement); X13 the pipeline skeleton and resolver-entry pair as promoted shared machinery four flavors ride (`spec-038` / `spec-039` own the promotions).
- **Decision 10** (visibility / alias): X4 one router write alias resolved once and pinned across the operation, with a re-routing `get_queryset` hook failing closed; X8 the pipeline being database-read-only outside the write step, with a transactionally-contained authorization phase as the one narrow exception.
- **Decision 15** (write auth): X9 the strict-`bool` authorization-result contract across `has_permission` / `check_permission` / `user.has_perm`, with an async hook's truthy coroutine closed and raised rather than read as allow; X10 the point-in-time authorization rule (a concurrently revoked permission is not re-observed; a custom policy needing revocation-linearizable behavior must lock or re-read its own rows) **and** the explicit `Meta.permission_classes = []` AllowAny opt-out, which the spec never names and which resolves no auth state at all.
- **Decision 9** stays correct as written — X1 / X2 touch it only insofar as the re-fetch now runs on the pinned write alias.

**N11 — Rationale companion, Decision 8 Revision 5 (row R1, RENAMED).** The bullet cites `_validate_save_assign_refetch_payload` as the extracted create / update tail. That symbol does not exist at `HEAD`; the tail is `mutations/resolvers.py::_model_write_step` plus the shared `::run_write_pipeline_sync` skeleton. `::_model_write_step`'s docstring records the rename ("the prior `_validate_save_assign_refetch_payload`"), so the history is recoverable — update the citation to the live symbols and keep the old name as the parenthetical it already is in the source.

**N15 — A live `TODO(spec-036 Slice 3)` anchor is R3 work, not a spec edit (M5).** `tests/test_permissions.py #"TODO(spec-036 Slice 3)"` stages a package-level permission pin for the mutation update/delete lookup that has since shipped — pinned by `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` and `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`. Delete the anchor (or replace with non-TODO provenance). No spec text is wrong; the spec's own `#"Staged-but-not-implemented seams follow"` paragraph correctly *describes* the discipline that was not followed. Worker 1 should confirm this is in R3's dispatch, since `docs/builder/BUILD.md`'s integration-pass step 6 would otherwise catch it only at the very end of the cycle.

**N12 — Verified and rejected: do not re-raise.** The suspected `has_permission` / `check_permission` arity mismatch between the spec and `docs/README.md` **does not hold** (M4). They are two different seams with two deliberately different arities, and the spec's Decision 15, `docs/README.md #"def has_permission(self, info, mutation, operation, data, instance=None)"`, `mutations/permissions.py::DjangoModelPermission.has_permission`, and `mutations/sets.py::DjangoMutation.check_permission` all agree. No spec edit.

**N13 — Ownership note, not a spec edit (L1).** `mutations/resolvers.py::run_write_pipeline_sync` and `::make_resolver_entries` are imported by `forms/`, `rest_framework/`, and `auth/`, making `mutations/` a shared write substrate — while its sibling `utils/write_transaction.py` was deliberately placed in `utils/` for exactly the layering reason its docstring gives. The consolidation is right; only its home is arguable. Worth one sentence in whichever Decision R2 uses to home X13, so the next reader is not surprised that three non-mutation flavors import from `mutations/`.

**N14 — Out of my territory, routed to the owning cohort.** `HEAD` exports `DjangoSchema` and `DjangoMutationExecutionContext` from the package root (`docs/README.md #"are exported from the package root"`), against Decision 5's four named public symbols and DoD item 8's export claim. **R1d owns this** (`__init__.py` / `tests/base/test_init.py`); recorded here only because it is the same `0.0.14` divergence class as H1 and should be reconciled in the same R2 pass.

### Review outcome

`review-accepted`.

The audit is complete over its declared territory: 72 graded contract rows, **0 SKIPPED**, 25 rows routing to R2 as spec edits, and 3 code-side items (M1 a weakly-pinned test gap, M2 a stale docstring, M5 a stale staged anchor) routing to R3 as test-and-comment repairs only.

Findings escalated to Worker 1 rather than blocking, per `docs/builder/worker-3.md` `### Acceptance gate` (resolution needs spec context and a maintainer decision this cohort cannot supply):

- **Escalated:** the `0.0.14` write-pipeline hardening has no owning spec, so rows X1–X13 have no natural home and folding them into `spec-036` makes it retroactively the spec for work it did not scope. Three resolution paths are stated under `### Notes for Worker 1`; the choice is the maintainer's.
- **Escalated:** H1's six `strawberry.Schema` sites span three cohorts' territories (R1b, R1c, R1d) and must be fixed in one R2 pass.
- **Escalated:** M1 is a `revision-needed`-shaped finding under `docs/builder/BUILD.md` `### Acceptance rule: weakly pinned is revision-needed`, but this cohort is read-only and has no builder to reject. It is carried as R3 work, and Worker 1 should confirm at final verification that R3 is dispatched for it — plus the plan's live-tree re-check, since the concurrent session may already have added the row.

Per the build plan, **R3 must re-check all three code-side items against the live working tree before repairing anything**: the concurrent session is `+237 / +245 / +92 / +81` lines into exactly these files and may already have closed any of them.

---

### Cohort boundary respected

Not audited, and why: R1a owns the `FieldError` / payload constructors (`utils/errors.py`, `mutations/inputs.py`); R1b owns `Meta` validation (`mutations/sets.py`, `types/finalizer.py`) — read only for the `check_permission` / `select_for_update` / `permission_classes` seams Decision 15 pins; R1d owns the live `/graphql/` products suite, `tests/optimizer/test_walker.py`'s G2 mirror, and the public export surface. `utils/querysets.py` and `utils/permissions.py` were read only as the visibility and request-context-decode boundary, as the partition allows. Items falling outside are routed by name in N1, N6, and N14.

---

## Final verification (Worker 1)

Performed in the R2 pass, `docs/builder/bld-036-review-2-spec_reconciliation.md`, which combines spec
reconciliation with this cohort's final verification — the same combined role the precedent cycle's R2
performed. The audit's own contract is `docs/builder/build-036-mutations-0_0_11.md` `## Conformance
grading vocabulary`; there is no `### Spec slice checklist (verbatim)` and no diff to audit, because
every R1 cohort is read-only over source and tests.

**Counts re-derived, not accepted.** Each cohort's grade tally was recomputed by parsing this file's
own inventory table row by row (row-id pattern per cohort, grade cell normalized), off the rendered
table rather than from the summary paragraph:

```
rows=72  CONFORMS=47  SUPERSEDED=20  STALE-DESCRIPTION=4  RENAMED=1  SKIPPED=0
```

Matches this file's stated table exactly, and 47+20+4+1 = 72 = the row count. No row id repeats.

**The cohort's distinguishing move — checking every candidate SUPERSEDED row against the original
implementing commit rather than only against `HEAD`** — is what made this cycle's attributions
survivable, and it is accepted without qualification. It re-graded `E3`, and it supplied the day-one
evidence for `D8.4b` and `D8.5b` that stopped three rows being misattributed as post-ship supersession
when they are in-cut review-round work (`c09793ee`, 2026-06-18, `__version__` still `0.0.10`, before the
2026-06-19 release). Those three are recorded in the companion under a distinct
`**Corrected inside the \`0.0.11\` cut:**` label and are excluded from the `**Post-ship:**` census on
purpose.

**All three High findings hold and are closed at every site**, including sites this cohort's notes could
not list because they sit in R1b's and R1d's territory: `H1` at 8 graded sites (6 rewritten, 2 correctly
left alone as materialization-ordering claims — the Decision 12 site this cohort flagged as
must-not-over-rewrite included), `H2` at 3 sites plus a fourth (the `## Edge cases` async bullet's stale
`(steps 3–6)` extent), `H3` at 4 sites.

**The escalation was the right call and the maintainer answered it: CORRECT CLAIMS ONLY.** Rows `X1`
and `X2` are discharged because they falsify `036` claims; `X3` is discharged at the enumeration and
deferred at the semantics; `X13` is partially discharged (Decision 4 now says where the shared substrate
lives); `X4`–`X12` are deferred with a per-row reason. Folding them in would have made `spec-036`
retroactively the spec for a pipeline it never scoped, which is exactly what this cohort warned against
and exactly what the maintainer declined.

**`M4` is verified-and-rejected and I did not re-raise it** — two seams, two deliberate arities, four
sources agreeing. **`M1`** (the weakly-pinned AR-M5 connection-child branch), **`M2`** (the
`_full_clean_or_field_errors` docstring), and **`M5`** (the stale anchor) are code-side and route to R3;
`M1` and `M5` are in R3's declared file list, `M2` is not and is recorded in R2's deferred-work notes as
needing its own dispatch. All 25 routable rows are accounted for: 15 discharged, 10 deferred.


**Method audited and accepted.** Every grade cites the read-only `HEAD` snapshot at
`7426e7e7d8aa447e89fee75088447d6a506dec12` or a `git show HEAD:<path>` read; no `git stash` /
`git checkout` / `git restore` / `git worktree` appears anywhere in the pass; the decision to decline a
failability mutation on baseline-dirty territory files is recorded with its reason rather than skipped
silently, and is the right call under `AGENTS.md` rule 34 — a `cp`-and-restore round trip spanning a
pytest run would have reverted any concurrent write landing inside the window.

**Every routable row reached R2 on disk** under `### Notes for Worker 1 (spec reconciliation)`, with the
pre-fix spec text and a recommended replacement — which is the obligation
`docs/builder/BUILD.md` `### Cohorting, naming, and closure` records two prior builders as having
missed. Nothing had to be re-derived from a return report.

Final status: `final-accepted`.

