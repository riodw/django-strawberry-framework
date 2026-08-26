# Build: Slice 1 — `DjangoConnection[T]` base + per-target concrete connection classes + `Meta.connection` validated and stored + the `first` + `last` guard

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (as-audited lines 60-65 for the slice checklist; Decisions 3, 4, 8, 9; Test plan lines 464-472; DoD items 2-3)
Rationale companion: `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`, checklist Slice 1
Status: final-accepted

**Closure path taken: procedural closure (`BUILD.md` `### Procedural-closure slices`), one combined Plan + Final-verification block, `Status: final-accepted` in this single pass.** The reason, stated explicitly: **every one of Slice 1's six sub-checks is satisfied at `HEAD`** — verified body-by-body against the source, not by grepping for symbol names — so there is **no CODE GAP**, and the only work the slice owes is spec reconciliation, which is Worker 1's alone. No Worker 2 build and no Worker 3 review were dispatched, and none is owed: this pass ships no `.py` change (proved below by an inverse diff, not asserted).

- **Hot-path declaration: none.** This pass writes two `.md` files and no `.py` file, so no code runs differently and no number can move. The build plan's conditional hot-path clause (a change inside `connection.py::_pipeline_sync` / `::_resolve_from_window` / `::_finalize_queryset` or `optimizer/extension.py::apply_connection_optimization`) is not triggered. Stated rather than left to be read out of a silence.
- **Floor-verification scope: none.** The plan's conditional clause fires only on a `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or `optimizer/extension.py`. No floor venv was built and none is owed. The shared `.venv` was not mutated.
- **Static inspection helper: skipped, with the reason.** `BUILD.md` `### When to run the helper during build` requires it when the plan **adds logic** to a `.py` file of 150+ source lines or anything under `optimizer/` or `types/`. This plan adds no logic anywhere — the audit found no CODE GAP, so there is nothing for a builder to implement in `connection.py` or `types/base.py` and no `docs/shadow` output to cite. Had the audit found a gap in either file, the helper would have been mandatory.
- **Boundary count: 0.** No guard, cap, rejection path, or validation branch is added, so no failability proof is owed and the `### Slice splitting` question does not arise. The four boundaries this slice's contract covers (`first` + `last`, non-dict, unknown sub-key, non-bool `total_count`, non-Relay-Node) are all shipped and all pinned — see the checklist audit.
- **Environment.** `uv run` works on this tree again; the concurrent `pyproject.toml` dynamic-version migration that broke it during the rationale pass has resolved. Both `uv run` and `.venv/bin/python` were used and are noted per command.
- **No `ruff`.** Both `ruff format` and `ruff check` are no-ops against `.md`, and running them repo-wide would touch a concurrent session's dirty `.py` files. Not run, deliberately.

## Working-tree baseline re-read (`git status --short`, start of pass)

The build plan's baseline list is a snapshot and has moved again. Dirty-and-out-of-scope at this pass's start, never edited and never reverted (`AGENTS.md` rule 34):

`AGENTS.md`, `pyproject.toml`, `uv.lock`, `django_strawberry_framework/__init__.py`, `django_strawberry_framework/exceptions.py`, `django_strawberry_framework/scalars.py`, `scripts/bug_hunt.py`, `tests/base/test_init.py`, `tests/test_bug_hunt.py`, `tests/filters/test_base.py`, `tests/filters/test_factories.py`, `tests/filters/test_inputs.py`, `tests/test_exceptions.py`, `tests/test_resource_policy.py`, `tests/test_scalars.py`, `tests/test_schema.py`, `tests/test_sets_mixins.py`, `tests/mutations/test_operations.py` (untracked), `docs/review/**`, `docs/dry/**`, `docs/bug_hunt/**`.

**New since the plan's list and since the rationale pass:** `tests/forms/test_converter.py` (M) appeared mid-pass, and `docs/dry/dry-plan-0_0_14.md` was deleted by the concurrent session's commit `b99484b3` between the rationale pass and this one. Both out of scope. `docs/SPECS/spec-030-connection_field-0_0_9.md` shows dirty from the rationale pass, which is this cycle's own work.

---

## Plan (Worker 1)

### Spec status-line re-verification

Read on entry: spec lines 1-11 (title, shipped-in line, `Status:`, owner, predecessors, the rationale-companion pointer). All still describe the build's current state — the card is `DONE-030-0.0.9`, the spec is the final implementation record, the five-slice decomposition and the joint-`0.0.9`-cut version boundary hold, and no predecessor doc it names has been deleted. One clause in the Predecessors paragraph is false at `HEAD` (the `Connection-aware optimizer planning` glossary entry is `shipped (0.0.9)`, not left `planned`); that is a spec-reconciliation item owned by Slice 3 / Slice 5, already inventoried by the rationale pass, and is not a status-line falsification. **No status-line edit was needed or made.**

### DRY analysis

- **Helper inventory checked — not applicable, and why.** The package-wide AST inventory exists to stop a builder writing a duplicate *code* shape. This pass writes no code and adds no helper, constant, validation branch, coercion utility, or test helper, so there is no candidate to inventory against. Recorded rather than skipped so a later pass does not read the absence as an omission. The `.py` surface is byte-unchanged (proof below). The audit did read the package-wide symbol surface it needed directly — `connection.py`, `types/base.py`, `types/definition.py`, `utils/querysets.py`, `optimizer/plans.py`, `keyset.py` — which is what the inventory would have indexed.
- **Existing patterns reused.** The reconciliation reuses the rationale companion's own documented append convention (a `**Post-ship:**` bullet under the owning Decision's `### Changes this Decision underwent`, stated at rationale line 7), rather than inventing a second shape for post-ship findings. Findings belonging to no single Decision go under `## Non-Decision deliberation`, as that same convention prescribes.
- **New helpers justified: none.**
- **Duplication risk avoided.** The one real duplication risk in a spec/rationale split is stating the same correction in both files, which then drift. It is prevented by rule: the spec carries only the **corrected contract**, in the present tense, with no trace of what it used to say; the companion carries only the **change record**. Verified mechanically after the edits — `bare`, `item 39`, `stable cursor`, `stable-cursor`, and `decision-9--opaque` each occur **0** times in the spec and are non-zero only in the companion (counts below).

### Slice 1's contract, audited against `HEAD`

Method note, because it decides what this audit is worth: **a grep proves the symbol, not the claim.** Every sub-check below was checked by reading the function or class body against the spec sentence, and every named test by reading its assertions. Where a name survived but its behavior widened, that is recorded as drift rather than waved through.

**Sub-check 1 — `DjangoConnection[NodeType]`.** `connection.py::DjangoConnection` subclasses `relay.ListConnection[NodeType]`, declares no `total_count` (the only class-level datum is `_resolves_total_count: ClassVar[bool]`, which `ClassVar` keeps out of the dataclass field set so Strawberry never surfaces it), and overrides `resolve_connection`, whose **first** statement after resolving the page-size ceiling is `_guard_first_and_last(first, last)` — raising `GraphQLError` before anything reads `info`. SATISFIED.

**Is the guard reached on every path that can slice?** Yes, and this was the audit's main risk. `_guard_first_and_last` has exactly **one** call site in the package (`connection.py::DjangoConnection.resolve_connection`), and every slicing path is downstream of it: `_consume_window` → either `_resolve_from_window` or `_consume_fallback`, and `_consume_fallback` → either `_resolve_keyset_connection` or `super(DjangoConnection, cls).resolve_connection`. None of those four is called from anywhere else in the package. The relation-connection resolver `_build_relation_connection_resolver::_resolve` does not slice at all — it returns either a `_WindowedConnectionRows` marker or a lazy queryset, both of which Strawberry feeds back through `resolve_connection` as the node iterable. So the keyset path, the windowed nested-connection path, and the synthesized relation-connection path all pass the guard. **No finding.**

**Sub-check 2 — cached `_connection_type_for`.** Present and cached on `target_type` identity in `_connection_type_cache`, with `clear_connection_type_cache` wired into `registry.clear()` via `register_subsystem_clear`. **The cache key is still `target_type` alone** — no later card added a dimension, so Decision 4's "exactly one connection shape per node type" holds and no spec sentence is contradicted there. SATISFIED as to the factory and the cache; **DRIFT as to what it returns** — see D1 below.

**Sub-check 3 — the count.** `_build_total_count_connection::total_count` reads `getattr(self, _TOTAL_COUNT_ATTR)`, a private **instance** attribute, never an `info.context` stash; `_set_total_count` is the single writer. Selection-gated: `want_count = cls._resolves_total_count and _total_count_requested(info)`, evaluated after the guard and after `prime_selected_fields`, and `_set_total_count` only calls its lazy `value` when `want_count`, so no `COUNT` query is issued otherwise. Pre-slice: `nodes` is the source as handed to `resolve_connection`, before any slicing. Async really does use `.acount()` — `_attach_count_async` awaits `nodes.acount()` (and awaits the queued connection coroutine *before* the countability guard can raise, so a raise never leaves it unawaited under `-W error`). SATISFIED; **DRIFT as to the mechanism being the only one** — see D3 below.

**Sub-check 4 — `Meta.connection` validation.** `types/base.py::ALLOWED_META_KEYS` contains `"connection"`; `DEFERRED_META_KEYS` is `{"aggregate_class", "fields_class", "search_fields"}` and does not. `_validate_connection(meta, connection, relay_shaped)` is called from `_validate_meta`, which computes `relay_shaped = _is_relay_shaped(cls, interfaces)` once and threads the bool in. It rejects a non-dict, an unknown sub-key, a non-bool `total_count`, and a non-Relay-Node type, all with `ConfigurationError`. `_is_relay_shaped` ORs the `Meta.interfaces` disjunct with `issubclass(cls, relay.Node)`, so both spellings are accepted, and `list_field.py::_validate_relay_djangotype_target` routes the `DjangoConnectionField` construction-time guard through the same predicate. SATISFIED (the shipped surface is one rejection path **wider** than three of the spec's four enumerations claimed — see D5).

**Sub-check 5 — stored on the definition.** `types/definition.py::DjangoTypeDefinition` carries `connection: dict | None = None`, populated in `DjangoType.__init_subclass__` as `connection=validated.connection`, in the same call that sets `filterset_class` / `orderset_class`. `_connection_type_for` reads `definition.connection` and never re-parses `Meta`. SATISFIED.

**Sub-check 6 — package coverage.** Every assertion the sub-check names exists. In `tests/test_connection.py`: `test_django_connection_is_listconnection_subclass` (subclass + `"total_count" not in __annotations__`), `test_first_and_last_raises_graphql_error`, `test_first_and_last_guard_on_generated_subclass`, `test_first_and_last_guard_with_unset`, `test_connection_type_for_caches_per_target` (identity, not equality), `test_connection_type_for_generates_named_subclass_when_opted_in`, `test_generated_connection_name_uses_graphql_type_name_not_python_name`, `test_connection_type_for_returns_concrete_subclass_without_opt_in`, `test_connection_type_for_returns_concrete_subclass_when_total_count_false`, `test_total_count_present_only_when_opted_in`, the four `_total_count_requested` selection-gating rows, and `test_total_count_async_path_counts_via_acount`. In `tests/types/test_base.py`: `test_meta_connection_in_allowed_meta_keys` (membership **and** non-membership, both asserted), `test_meta_connection_non_dict_raises`, `test_meta_connection_unknown_subkey_raises`, `test_meta_connection_non_bool_total_count_raises`, `test_meta_connection_non_relay_type_raises`, `test_meta_connection_accepts_direct_relay_node_inheritance`, `test_meta_connection_stored_on_definition`, and `test_connection_key_requires_relay_node`. SATISFIED; the spec's **Test plan** named one test that does not exist by that name (`test_total_count_counted_only_when_selected`) — see D4.

**Decision 9 audit (opaque cursors / `Meta.cursor_field`).** Verified in both directions rather than assumed. Offset cursors **are still the default**: `_keyset_connection_context(cls)` returns `None` for a node type whose definition carries no `cursor_field`, and `_consume_fallback` then reaches `super(DjangoConnection, cls).resolve_connection`, i.e. Strawberry's `ListConnection` and its `b64("arrayconnection:N")` cursors — `keyset.py`'s own contract states it as "`cursor_field` unset keeps the shipped offset behavior byte-identical". What is false at `HEAD` is the **deferral**: `cursor_field` is in `ALLOWED_META_KEYS`, validated by `types/base.py::_validate_cursor_field` at class creation and `validate_cursor_field_columns` at finalization, and implemented in `django_strawberry_framework/keyset.py` (landed as `BACKLOG.md` item 39 sub-feature 3, `stable_cursor_field`, commit `51421e54`; it has no numbered spec of its own, so the spec now points at the module). See D2.

### CODE GAP list

**Empty.** No sub-check of Slice 1 is unimplemented, silently narrowed, or dropped. Nothing is dispatched to Worker 2, and nothing owes a failability proof.

Two shipped behaviors are **wider** than the spec's `0.0.9` text — the always-concrete connection class and the keyset-cursor dispatch — and one is **narrower in the spec's telling than in the code** (four rejection paths written as three). All three are spec drift in the reconciliation direction: the code does more or is more precise than the text, never less.

### Spec slice checklist (verbatim, as audited)

Quoted **as the spec stated them at the start of this pass**, before the reconciliation below — deliberately, so the boxes audit the shipped code against the contract as written when the card shipped, rather than against text this same pass rewrote to match the code. Each box's reconciliation, where there was one, is named in `### Spec changes made (Worker 1 only)`. Boxes are ticked here because the **shipped code satisfies the contract at `HEAD`** (this cycle's inversion of the usual tick discipline).

- [x] Ship [`django_strawberry_framework/connection.py`][connection] with a generic `DjangoConnection[NodeType]` subclass of [`strawberry.relay.ListConnection`][strawberry-relay] that has **no** `totalCount` field and overrides `resolve_connection` to raise a `GraphQLError` when both `first` and `last` are supplied, then delegates to `super().resolve_connection(...)` (the guard Strawberry's `SliceMetadata.from_arguments` does NOT provide).
- [x] A cached factory `_connection_type_for(target_type)` that returns the connection class for a node type: the bare `DjangoConnection[target_type]` when the type does not opt into `totalCount`, or a generated concrete subclass named `<TypeName>Connection` (e.g. `GenreTypeConnection`) declaring `total_count: int` and overriding `resolve_connection` to selection-gate + capture the count when it does. Cache keyed on `target_type` (one connection shape per node type — no per-field override, per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation), so no naming/caching ambiguity).
- [x] The `total_count` resolver reads a private instance attribute set by `resolve_connection`; `resolve_connection` counts the **post-filter pre-slice** `nodes` queryset (sync `.count()` / async `.acount()`) **only when `totalCount` is in the selection set** (per [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)), attaches it to the connection instance, then delegates to super for slicing.
- [x] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"connection"` (net-new public key — NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-029`][spec-029] [Decision 6][spec-029]). A `_validate_connection` helper (called from [`_validate_meta`][base], structurally modeled on `_validate_filterset_class`) shape-checks the dict (`{"total_count": bool}` only; unknown sub-keys and non-dict values raise) and gates `Meta.connection` to a Relay-Node-shaped type via the `relay_shaped` bool ([`_is_relay_shaped`][base], computed once in [`_validate_meta`][base] from `cls` + the validated interfaces) — accepting both `relay.Node` in `Meta.interfaces` and direct `relay.Node` inheritance, the same single predicate the field guard uses. The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a `connection` slot) so the factory and the connection-class generator can read it (per [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)).
- [x] Package coverage: [`tests/test_connection.py`][test-connection] (the `DjangoConnection[T]` shape; the `first` + `last` `GraphQLError` guard; `<TypeName>Connection` generation + caching; `totalCount` present-only-when-opted-in and counted-only-when-selected). [`tests/types/test_base.py`][test-types-base] gains the `"connection"`-in-`ALLOWED_META_KEYS` / not-in-`DEFERRED_META_KEYS` assertion, the `_validate_connection` failure modes, and the `definition.connection` storage assertion.

Ticks 1, 2, and 3 carry a caveat that is recorded rather than hidden: each contract **landed**, and each was subsequently **widened** by a later card (concrete-always, keyset dispatch, count mechanisms). A tick means the sub-check's obligation was discharged and is still discharged, not that the spec sentence describing it was still exact — that is what the reconciliation below fixes.

### Implementation steps

None. No `.py` step exists to plan: the audit closed with an empty CODE GAP list, so this artifact's work is the reconciliation recorded under `### Spec changes made (Worker 1 only)`.

### Test additions / updates

None. No executable surface changed, and every assertion Slice 1's contract needs already exists (sub-check 6 above). No temp test was written; none would have anything to demonstrate.

### Implementation discretion items

None. Every judgement call in this pass is decided and recorded below — including the two that could have gone either way (whether to rename Decision 9's heading, and whether the `## Current state` bullets count as drift).

---

## Final verification (Worker 1)

### Populations swept, instruments used, and counts

`BUILD.md` `## Claims are proven mechanically`: every number below is re-derivable by running the named token against the named file, and each population was confirmed with a **second instrument of disjoint vocabulary** — because a sweep keyed on one known instance's wording finds a fraction of its population. Counts are **occurrences**, not matching lines, so a claim wrapped across two lines cannot hide.

| Population | Instrument A (pre-edit) | Instrument B, disjoint (pre-edit) | Union of sites | Post-edit |
|---|---|---|---|---|
| The bare-alias / always-concrete claim | `bare` — 3 occ, spec lines 62, 468, 551 | `DjangoConnection[target_type]` 2 occ (62, 311) + `DjangoConnection[GenreType]` 5 occ (94, 158, 206, 225, 310) + `_connection_type_for` 10 occ (62, 67, 311, 334, 375, 433, 468, 551, 556) | **5 sites**: 62, 225, 310-311, 468, 551 | `bare` = **0** occ in the spec; 3 occ in the companion (the change record) |
| Decision 9 / `Meta.cursor_field` | `cursor_field` — 10 occ, lines 131, 171, 379, 381, 446, 536, 657 | `item 39` 3 occ (131, 446, 536) + `stable cursor`/`stable-cursor` + the anchor slug `decision-9--opaque` 5 occ (131, 171, 446, 536, 657) | **8 spec sites** (131, 171, 379, 381, 383, 446, 536, 657) + **3 companion sites** (44, 169, 380) | `item 39` = **0**, `stable cursor` = **0**, `decision-9--opaque` = **0** in the spec; non-zero only in the companion |
| Relay-foundation symbol renames | `_initial_queryset` 4 occ (69, 104, 354, 447); `_apply_get_queryset*` 15 occ over 7 lines (69, 103, 104, 362, 387, 389, 557); `_ends_in_unique_column` 2 occ (71, 358) | the NEW names — `apply_type_visibility` **0** occ, `initial_queryset(` only as a substring of the private name — plus the path `types/relay.py` 3 occ (104, 387, 677) | **9 distinct lines** | mine fixed (69, 71); **7 lines handed to Slice 2** — see below |
| `_validate_connection` rejection-path enumerations | `three` / `the three` in the spec | the shipped guard bodies read directly in `types/base.py::_validate_connection` (4 raises) | **3 sites**: checklist 64, Test plan 471, DoD 552 | all three now say four |

The third row is where the instruments mattered most: **`_apply_get_queryset_sync` alone is 8 occurrences and `_apply_get_queryset_async` 7, over the same 7 lines** — counting lines would have understated the population by half, and counting either spelling alone would have missed the other.

### The `## Current state` licence, applied explicitly

The `## Current state` section is licensed by the spec's own opener as "a true description of the repo as of this writing", so a bullet that merely describes the pre-build repo is not drift. **That licence covers dated observations, not predictions the build falsified**, so I resolved each candidate by asking whether the sentence observes or promises:

- **Lines 103 and 104 are observations, and they are TRUE observations — left as written.** They describe `list_field.py`'s default resolver dispatching `_apply_get_queryset_sync` vs `_apply_get_queryset_async`, and `types/relay.py` shipping `_apply_get_queryset_sync` / `_apply_get_queryset_async` / `_initial_queryset`. I did not assume this: reading `django_strawberry_framework/types/relay.py` **at the spec's own authoring commit** (`eaaf1385`, obtained read-only) shows all three symbols defined there. So the bullets are accurate about the repo they describe, and the later relocation to `utils/querysets.py` does not falsify them. **The handed-forward inventory graded `:103` and `:104` as drift; that grading is wrong, and correcting it is the substantive half of this item.**
- **Lines 69 and 71 are contract statements — fixed.** A `## Slice checklist` sub-bullet says what the code must do, in the present tense, and names symbols a reader is expected to find. `_initial_queryset` and `_apply_get_queryset_*` are not findable, so those citations are drift regardless of which slice's sub-bullet carries them.
- No `## Current state` bullet in this slice's scope asserts what the build *will* do, and none names a symbol by a spelling that never existed.

### Spec changes made (Worker 1 only)

Line numbers are **post-edit**. Cause for every entry: the Slice 1 audit above, `docs/builder/build-030-connection_field-0_0_9.md` Slice 1. Every "what changed and why" record went to the rationale companion; the spec carries only the corrected contract, in the present tense, with no chronology, no amendment block, and no "as of `033`" hedge.

**D1 — the bare `DjangoConnection[target_type]` alias path no longer exists; every node type gets a generated concrete class.** 5 sites: the Slice-1 checklist sub-bullet 2 (`:62`), the User-facing API resolution paragraph (`:225`), Decision 4's two bullets plus two new paragraphs (`:310`-`:315`), the Test plan's factory row (`:474`), and DoD item 2 (`:557`). The spec now states that `_connection_type_for` always generates a concrete `<TypeName>Connection` and that the generic alias may **not** be handed to the schema, with the reason that changes how it is built (Strawberry's generic specialization copies an alias into a plain specialized class whose `resolve_connection` is `ListConnection`'s, dropping the `first` + `last` guard for every through-schema query) — that clause stays in the spec under `worker-1.md`'s implementation-relevant-rationale carve-out, because a builder who never reads it re-introduces the alias. Decision 4 also now records that the opted variant flips a `ClassVar` flag rather than re-declaring `resolve_connection`, and that the generated name comes from the node type's canonical GraphQL type name.

**D2 — Decision 9's `Meta.cursor_field` deferral closed; the Decision's subject is now the dispatch seam.** 8 sites: the Decision's heading and body (`:385`-`:389`), the Non-goals bullet (`:131`), the do-not-borrow bullet (`:171`), the `after:`-under-concurrent-mutation edge case (`:452`), the Out-of-scope bullet (`:542`), and the `[rationale-d9]` link definition (`:663`). The spec now states the offset default (still true and still the shipped default for a type declaring no `cursor_field`), points the keyset half at `django_strawberry_framework/keyset.py`, and says that `connection.py` owns the dispatch seam rather than the codec. **The heading changed** — `Opaque cursor delegated to Strawberry; Meta.cursor_field deferred` → `Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in` — so all 8 anchors and link definitions naming the old slug were repointed in the same change; a tree-wide sweep confirmed the old slug is cited from nowhere outside these two files, so nothing else needed touching. Two false forward pointers went with it: `BACKLOG.md` item 39 sub-feature 3 is discharged, and `Meta.cursor_field` is not out of scope for the package.

**D3 — the count's mechanism is no longer only `.count()` / `.acount()`.** 3 sites: the Slice-1 checklist sub-bullet 3 (`:63`), Decision 4's `(c)` clause (`:311`), and DoD item 2 (`:557`). The contract is now stated as the **post-filter pre-slice cardinality**, with `.count()` / `.acount()` named as the ordinary offset path's means and a source that already carries its own count read rather than re-counted. The counted value and the selection gate are unchanged.

**D4 — the Slice-1 Test plan named tests that do not exist and omitted tests that do.** 3 rows rewritten (`:473`-`:477`). `test_total_count_counted_only_when_selected` has no such test at `HEAD`; the contract is pinned instead by the four `_total_count_requested` rows plus `test_total_count_async_path_counts_via_acount`, which the plan did not name. Added: the two extra `first` + `last` rows (generated-subclass, `UNSET`), the three extra `_connection_type_for` rows, and `test_meta_connection_non_bool_total_count_raises`. Every test name now in the Test plan was confirmed present by reading its body.

**D5 — `_validate_connection` has four rejection paths, and three places said three.** 3 sites: the checklist sub-bullet 4 (`:64`), the Test plan row (`:477`), DoD item 3 (`:558`). Decision 8 itself always listed all four, so this was a stale enumeration, not a missing guard — `tests/types/test_base.py::test_meta_connection_non_bool_total_count_raises` has pinned the non-bool path since the slice landed.

**D6 — Decision 3's guard condition and dispatch tail.** 1 site (`:302`, plus the checklist sub-bullet 1 at `:61`). The condition is now "supplied — non-`None` and not `strawberry.UNSET`", which is what `_guard_first_and_last` tests and what `test_first_and_last_guard_with_unset` pins; under the old "non-`None`" spelling an omitted `last` arriving as `UNSET` would have counted as supplied. The tail no longer implies a single unconditional `super()` delegation: it states that the guard runs first, before anything reads `info`, and that a well-formed request goes on to the override's source dispatch whose ordinary offset path is `super().resolve_connection(...)`.

**D7 — two stale symbol citations in the Slice-2 checklist, the two sites this slice was assigned.** `:69` `_initial_queryset(target_type)` → `initial_queryset(target_type)` and `_apply_get_queryset_sync` / `_apply_get_queryset_async` → `apply_type_visibility_sync` / `apply_type_visibility_async`; `:71` `_ends_in_unique_column` → `[optimizer/plans.py::ends_in_unique_column][optimizer-plans]`, re-exported into `connection.py` as `_ends_in_unique_column`. The `_ends_in_unique_column` case is worth its own sentence: it was **imprecise, not broken** — the name still resolves at the cited module because `connection.py` keeps it as a deliberate alias and `tests/test_connection.py` imports it by that private name, so the fix names the canonical implementation without pretending the alias is gone.

**D8 — two new link definitions.** `[keyset]: ../../django_strawberry_framework/keyset.py` and `[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py`, both under the existing `<!-- django_strawberry_framework/ -->` group in alphabetical order. Both paths disk-exist-checked.

**Not changed, deliberately.** No status line (nothing the build falsified). No `## Current state` bullet (the licence applies — see above). Nothing under Decisions 5, 6, 7, 10-14 or their checklist / Test plan / DoD text: those are Slices 2-5's, and the handed-forward inventory below keeps them visible.

### Rationale companion appends (Worker 1 only)

The companion is append-only during the build, and every append used its own documented convention — a `**Post-ship:**` bullet under the owning Decision's `### Changes this Decision underwent`. No moved text was rewritten, including the two passages that read as stale claims but are historical by design (the revision-history P3 bullet at companion `:44` and Decision 7's justification at `:175`, both of which mention the "deferred" keyset work: they are chronology sitting in the chronology file).

- **Decision 3** — 2 bullets: the `UNSET` condition, and why "otherwise delegate to super" is no longer the whole tail.
- **Decision 4** — 4 bullets: the removed bare-alias path and the through-schema guard loss that closed it (with the surviving SDL description asymmetry named as shipped surface), the flag-not-a-second-override shape, the count mechanisms forking while the value and the gate did not, and the `graphql_type_name`-not-`__name__` naming rule.
- **Decision 8** — 1 bullet: four rejection paths, three stale enumerations, no missing guard.
- **Decision 9** — 2 bullets: why the deferral was a real `0.0.9` scope boundary, what closed it, the two claims the Decision may no longer make, what survives unchanged, and the heading/anchor repoint; plus the concurrent-mutation edge case now having a recourse.
- **`## Non-Decision deliberation`** — a new `### Post-ship: symbol citations the Relay-foundation relocations invalidated` subsection carrying the three renames with their occurrence counts **and** the `## Current state` licence judgement, including that two of the sites the inventory graded as drift are true dated observations verified against the spec's authoring commit.

### Postcondition proofs

**1. `check_spec_glossary` holds.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md
OK: 50 terms - all have glossary entries and at least one spec link.
EXIT=0
```

**2. Link scaffold and paths, both files.**

```
$ .venv/bin/python scripts/check_trailing_commas.py --check docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
EXIT=0

$ .venv/bin/python   # undefined refs / unused defs / def paths not on disk / def anchors that do not resolve / dangling in-page anchors / inline cross-file links
== docs/SPECS/spec-030-connection_field-0_0_9.md
 undefined refs: []
 unused defs: ['goal']        # pre-existing before this cycle; verified against the pre-move copy by the rationale pass
 missing paths: []
 def anchors not resolving: []
 dangling in-page anchors: []
 inline cross-file links: []
== docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
 undefined refs: []
 unused defs: []
 missing paths: []
 def anchors not resolving: []
 dangling in-page anchors: []
 inline cross-file links: []
```

The Decision-9 rename is the one that made this check load-bearing: the companion's `## Decision 9 — …` heading and the spec's `### Decision 9 — …` heading slug identically, so `[rationale-d9]` (spec → companion) and `[spec-030-d9]` (companion → spec) had to move together with the two in-companion in-page anchors. All four resolve.

**3. `.py` surface unchanged — the inverse proof.** The claim is that no executable byte moved, so the proof is a diff empty by construction, not a green suite.

```
$ git status --short -- '*.py'
 M django_strawberry_framework/__init__.py       # all 16 pre-existing; see the baseline re-read above
 M django_strawberry_framework/exceptions.py
 M django_strawberry_framework/scalars.py
 M scripts/bug_hunt.py
 M tests/base/test_init.py
 M tests/filters/test_base.py
 M tests/filters/test_factories.py
 M tests/filters/test_inputs.py
 M tests/forms/test_converter.py
 M tests/test_bug_hunt.py
 M tests/test_exceptions.py
 M tests/test_resource_policy.py
 M tests/test_scalars.py
 M tests/test_schema.py
 M tests/test_sets_mixins.py
?? tests/mutations/test_operations.py
$ git status --short docs/SPECS/
 M docs/SPECS/spec-030-connection_field-0_0_9.md
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
```

Every dirty `.py` was already dirty at pass start and belongs to the concurrent session. The only version-controlled paths this pass wrote are the spec, the companion, and this artifact; `docs/builder/worker-memory/worker-1.md` is the fourth write and is gitignored.

**4. Focused tests run (no `--cov*` flag in any form).**

```
$ uv run pytest tests/test_connection.py tests/types/test_base.py --no-cov -q
8 workers [235 items]
235 passed in 6.67s
```

Recorded as run-and-passing, per `worker-1.md` step 5. This is a sanity confirmation, not evidence for any claim above: nothing executable changed, so a green run here could not have failed differently.

**5. Byte counts (measured, `wc -c` / `wc -l`).**

| File | Before this pass | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 119,551 B / 698 lines | 124,482 B / 706 lines | **+4,931** B / +8 lines |
| `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` | 52,311 B / 406 lines | 61,742 B / 425 lines | **+9,431** B / +19 lines |

The spec grew because two corrections are genuinely longer than the claims they replace — the always-concrete contract has to carry *why* the alias may not be used (or a later reader re-introduces the bug), and Decision 9 now describes two cursor modes where it described one and a deferral. The corpus ratchet in `BUILD.md` governs the six workflow documents, none of which this pass touched.

### Handed forward to Slices 2-5

Verified at `HEAD` by this pass and **deliberately not fixed** — each belongs to a later slice of this same cycle. Line numbers are post-edit.

**To Slice 2 (`bld-slice-2-030-connection_field.md`) — the rest of the symbol-rename population, 7 lines:**

- `_initial_queryset` at `:358` (Decision 7 step 1) and `:453` (Edge cases, "a fully-unordered `_initial_queryset`") → `utils/querysets.py::initial_queryset`.
- `_apply_get_queryset_sync` / `_apply_get_queryset_async` at `:366` (Decision 7's consumer-resolver paragraph), `:393` and `:395` (Decision 10, which also cites the path `types/relay.py`), and `:563` (DoD item 5) → `utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async`.
- `_ends_in_unique_column` at `:362` (Decision 7 step 5) → `optimizer/plans.py::ends_in_unique_column`.
- Also in the companion, and Slice 2's because Decision 7 owns it: `:175` calls the keyset work "the deferred `Meta.cursor_field` keyset-cursor work" and `:186` cites `_initial_queryset`. Both sit inside **moved justification text**, which is append-only, so the right move is a `**Post-ship:**` bullet under Decision 7 rather than an edit.

**Ownership note, stated rather than left implicit:** fixing 2 of 9 lines of one rename mid-cycle leaves the spec briefly inconsistent in symbol spelling, which `worker-1.md` `## Review-round custody` warns about. I honored the assigned partition anyway, for one reason: the partition is explicit, this cycle is sequential, and Slice 2 is the very next pass, so the inconsistency cannot outlive the cycle. If Slice 2 does not close all 7, the integration pass must — a half-renamed spec is not an acceptable end state, only an acceptable mid-state.

**To Slice 3 (`bld-slice-3-030-optimizer_cooperation.md`):**

- The `Connection-aware optimizer planning` `planned` claim at `:9` (Predecessors), `:27` ("the deferred sibling slice"), `:111` (Current state glossary bullet — note the licence question applies here too: `:111` observes what the glossary said at authoring time, so grade it before fixing it), `:514` (Doc updates), and DoD item 8.
- The "derived plan is **empty** for every connection field" bound at `:405` (Decision 11 `Scope honesty`), `:73` (Slice-3 checklist), `:494` (Test plan `test_root_connection_field_queryset_is_planned`), and DoD item 6 (`:567`). Note for that pass: `tests/test_connection.py::test_root_connection_field_queryset_prefetches_node_many_relation` exists at `HEAD` and is direct evidence the bound is gone.

**To Slice 5 (audit-only under the cycle's scope fence):**

- `docs/GLOSSARY.md` carries no `Meta.cursor_field` heading, while its `DjangoConnection` and `Connection-aware optimizer planning` entry bodies both reference `Meta.cursor_field`. A public `Meta` key with no glossary entry is a documentation gap to **record** for the maintainer, not to fix here — and it is why Decision 9's new text cites the module path rather than a glossary anchor.
- `CHANGELOG.md` has no entry for the keyset-cursor / `Meta.cursor_field` feature (`grep -c` over `cursor_field` / `keyset` in that file returns 0), although it is shipped public surface. Record only; `CHANGELOG.md` is fenced out of this cycle.

**To the integration pass:**

- `:544` "**Auto-trigger of `finalize_django_types()`** — deferred to `032`" (Decision 12's Out-of-scope twin). Not in Slice 1's governing Decision set and not audited here; confirm against `032`'s shipped surface before the cycle closes.
- The unused `[goal]` link definition in the spec — pre-existing, harmless, and named here only so a later sweep does not attribute it to this pass.

### Summary

Slice 1's whole contract is satisfied at `HEAD`: the `DjangoConnection[T]` base with no `totalCount` and the package-owned `first` + `last` guard, the cached `_connection_type_for` keyed on `target_type` alone, the selection-gated pre-slice count on the connection instance with a real `.acount()` on the async path, `"connection"` in `ALLOWED_META_KEYS` and out of `DEFERRED_META_KEYS` with a four-path `_validate_connection` gated on the canonical `_is_relay_shaped`, the `connection` slot on `DjangoTypeDefinition` populated in `__init_subclass__`, and every named test present with the assertions it claims. The `first` + `last` guard is reached on every path that can slice — the keyset, windowed, and relation-connection paths included — because it has exactly one call site and all of them are downstream of it.

**CODE GAP list: empty.** Eight reconciliation items landed in the spec (the removed bare-alias path across 5 sites, Decision 9's closed deferral across 8, the count-mechanism fork across 3, a Test plan naming a test that does not exist, three enumerations saying three rejection paths where there are four, Decision 3's `UNSET` condition and dispatch tail, the two assigned symbol citations, and two new link definitions), each with its "what changed and why" in the rationale companion and none of it in the spec. `check_spec_glossary` holds at `OK: 50 terms`, both link scaffolds validate, every in-page anchor and cross-file def anchor resolves across the renamed Decision 9, the `.py` surface is byte-unchanged, and the focused 235-row scope passes.

### Spec changes made (Worker 1 only) — deferral reasons for unticked boxes

None. Every box in `### Spec slice checklist (verbatim, as audited)` is ticked because the shipped code satisfies it at `HEAD`. No box is deferred and none is un-ticked, so there is nothing to record here beyond that statement.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[connection]: ../../django_strawberry_framework/connection.py
[definition]: ../../django_strawberry_framework/types/definition.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py

<!-- tests/ -->
[test-connection]: ../../tests/test_connection.py
[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[strawberry-relay]: https://strawberry.rocks/docs/guides/relay
