# Build: Slice 4 — live `/graphql/` HTTP coverage (model-anchored emit, the emitted-ID filter round-trip, the deterministic `type` opt-out, and the model-label migration of every pre-`0.0.9` `GlobalID` assertion)

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (Slice checklist lines 73-76; `## Current state` line 111; Goals item 5 line 119; Decision 13 lines 404-412; Implementation plan Slice-4 row line 419; Test plan lines 518-532; Definition of done item 6 line 589)
Status: final-accepted

**Procedural closure** (`docs/builder/BUILD.md` `### Procedural-closure slices`, and the build plan's `## Dispatch rule for this cycle`): the CODE GAP list is empty and no test edit is judged worth a build cycle, so this is one combined Plan + Final-verification block. No Worker 2, no Worker 3.

This is a **residual reconciliation cycle** over already-shipped work (`DONE-031-0.0.9`, package now at `0.0.14`). Slice 4 is the only slice whose deliverable is entirely **test** code — the live `/graphql/` HTTP acceptance tier — so its CODE GAP audit is an audit of tests, not of production surface. Code is the truth.

---

## Plan (Worker 1) + Final verification (Worker 1)

### DRY analysis

**Helper inventory checked.** Refreshed over the **whole package** (`django_strawberry_framework/`, not just `utils/`) by grepping the shapes this slice touches — `resolve_typename`, `label_lower`, `graphql_type_name`, `_accepted_globalid_type_names`, `_decode_and_validate_global_id`, `from_id`, `strategy` — and opening every hit. This slice writes no package source, so the inventory is read as a check that the live tier is exercising shipped single-sitings rather than re-implementing them:

- `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver` and the four encoders — what `test_emitted_globalid_is_model_anchored` and `test_type_strategy_opt_out_reproduces_type_name` observe from the wire. Neither test reaches into the package; both decode the emitted string with `strawberry.relay.GlobalID.from_id`, which is the consumer's own instrument.
- `django_strawberry_framework/filters/base.py::_decode_and_validate_global_id` / `::_accepted_globalid_type_names` / `::resolve_globalid_target_definition` — what `test_globalid_filter_round_trip` and the migrated filter-input rows exercise, all three through a real `filter:` argument rather than a direct call.
- `examples/fakeshop/schema_reload.py::reload_all_project_schemas` — the single-sited reload discipline. The live tier's `project_schema_override` fixture is a thin `return` of that callable, so the opt-out test reuses the project's one reload seam instead of a suite-local copy. This is the DRY-relevant shape of the slice and it is already correct.
- `examples/fakeshop/test_query/test_products_api.py::_global_id` / `test_library_api.py::_decode_global_id` — the two per-suite encode/decode conveniences. They are near-twins in intent but not in shape (one encodes via `relay.GlobalID`, one decodes via raw `base64` deliberately, "so the HTTP path stays Strawberry-agnostic on the assert side"). Left as-is: consolidating them would delete the library suite's deliberate Strawberry-independence.

**New helpers justified:** none. This pass writes no source and no tests.

**Duplication risk avoided:** none introduced; the pass touches two Markdown files.

### Implementation steps

This pass performs the audit and the reconciliation only. No source, no tests.

1. Confirm each of the three tests Worker 0 pre-verified exists **and asserts what the spec says it asserts** — in particular that `test_globalid_filter_round_trip` feeds back the API-emitted string rather than a reconstructed one (`docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability`).
2. Establish what `project_schema_override` actually is, and whether the `RELAY_GLOBALID_STRATEGY = "type"` override really precedes the schema reload rather than the test passing for the wrong reason.
3. Sweep **all three** test trees for surviving type-anchored `GlobalID` payloads, not the two files the spec names (`docs/builder/BUILD.md` `### Test staleness a focused run cannot see`).
4. Establish which of the two contracted `type`-opt-out shapes shipped, and whether `examples/fakeshop/apps/*/schema.py` was touched.
5. Grade the Slice-4-owned `## Current state` sentence with the three-case stale-sentence test, reading the authoring commit rather than today's tree.
6. Enumerate shipped live `GlobalID` coverage with **no** owning `## Test plan` bullet, and decide per case.
7. Rewrite the spec to state the current contract directly; append the reasoning to the rationale companion under the owning Decision.
8. Run the live suites focused, without `--cov*` flags, and run the closing verification checks.

### Test additions / updates

None. `### Final verification checks run` records the runs confirming the contracted rows are green at HEAD.

### Implementation discretion items

None; no Worker 2 pass.

### Spec slice checklist (verbatim)

Copied verbatim from `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` `## Slice checklist`, Slice 4, **as it read at the start of this pass** (pre-edit, so the audit is legible against what the slice was dispatched with). Boxes are ticked because the slice **shipped** — each tick is the CODE GAP audit's verdict, evidenced below.

- [x] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type (per the card DoD)
  - [x] Update the existing live `GlobalID` assertions in [`examples/fakeshop/test_query/`][fakeshop-test-products] (and [`test_library_api.py`][fakeshop-test-library]) for the new model-label payload — the default-flip changes every **emitted** `GlobalID`, so the response-shape assertions that pin `id` (the `_global_id("ItemType"/"CategoryType"/"EntryType", …)` expectations in [`test_products_api.py`][fakeshop-test-products] and the `assert type_name == "GenreType"` round-trip in [`test_library_api.py`][fakeshop-test-library]) move to `products.item:<pk>` / `library.genre:<pk>`. **The existing filter-input tests must ALSO move to the model-label form** — under the default `model` strategy the strategy-aware filter ([Decision 13](#decision-13--globalid-filter-validation-is-strategy-aware)) accepts `products.category:<pk>` and **rejects** the old `CategoryType:<pk>` input those tests build, so they are not unchanged. (The [`TODAY.md`][today] own-PK `GlobalID` filtering-example correction is **owned by Slice 5** — see Slice 5 line below and the [Doc updates](#doc-updates) section — so Slice 4 stays purely the `examples/fakeshop/test_query/` suite plus any test fixture helper; the standing-doc edits, including the `TODAY.md` filtering examples, the breaking-wire-format note, and the `type+model`-first upgrade sequence, all land together in Slice 5 to avoid a double-edit of the same lines.)
  - [x] Add live tests: (a) an emitted `node { id }` decodes to the model-label payload (base64 of `"app_label.modelname:<pk>"`); (b) **the `0.0.9` headline workflow — a `filter: { id: { exact: "<emitted model-label GlobalID>" } }` round-trips to the right row through the real products API** (proving the strategy-aware filter accepts the model-label payload it now emits, [Decision 13](#decision-13--globalid-filter-validation-is-strategy-aware)); (c) the `type`-strategy opt-out reproduces the GraphQL-type-name payload, set up deterministically (see below).
  - [x] **Deterministic `type`-opt-out setup.** The fakeshop acceptance fixtures reload schemas at import/finalization, so a `RELAY_GLOBALID_STRATEGY = "type"` override must be active *before* the reload or the test silently exercises the default schema; and permanently flipping an existing products type to `"type"` would churn unrelated expected IDs and weaken the default-flip coverage. Preferred shape: factor the products schema-reload into a callable fixture helper (the [`library`][fakeshop-test-library] suite already has one), then drive the opt-out test with a test-local `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"})` + `registry.clear()` + reload inside the test. Alternative: a dedicated opt-out type / root field whose IDs are intentionally type-anchored. The implementation plan names this so Slice 4 is not a brittle import-order exercise.

### CODE GAP audit

**Verdict: the CODE GAP list is EMPTY.** Every surface Slice 4 contracts exists at HEAD in the shape the spec specifies. Sixteen contracted items were re-derived; none is missing, and one contracted-but-conditional item (`examples/fakeshop/apps/*/schema.py`) resolved to the branch the spec named as preferred.

Worker 0's pre-verification handed three test names. All three held this time. Six divergences surfaced beyond them, five of which are the spec under-describing what shipped and one of which is a false sentence in `## Current state`.

| # | Contracted item | Verdict | Evidence |
| --- | --- | --- | --- |
| G1 | `test_emitted_globalid_is_model_anchored` exists in the live tier | **present** | `examples/fakeshop/test_query/test_products_api.py::test_emitted_globalid_is_model_anchored` |
| G2 | …and asserts the model-label payload, not merely "some GlobalID" | **holds** | asserts `parsed.type_name == models.Item._meta.label_lower` **and** `parsed.node_id == str(item.pk)`; the expected value is derived from the ORM, so the pin tracks the model rather than a literal that a rename would silently keep green |
| G3 | …reached through the real `/graphql/` HTTP stack | **holds** | drives `_post_graphql(...)` with a `django.test.Client`; the emitted string is decoded with `strawberry.relay.GlobalID.from_id`, i.e. from the wire, not from a package call |
| G4 | `test_globalid_filter_round_trip` exists | **present** | `::test_globalid_filter_round_trip` |
| G5 | …**is** the round trip: it feeds back the id the API just emitted, not a reconstructed one | **holds** | two requests. The first (`allItems { edges { node { id name } } }`) captures `emitted_id = emitted["id"]`; the second interpolates that exact string into `filter: { id: { exact: "…" } }`. Nothing between them re-encodes. This is the load-bearing property `docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability` demands — a hand-built `_global_id("products.item", pk)` filter input would pin "the filter accepts model labels", which is strictly weaker than emit → filter symmetry |
| G6 | …returns the **right row**, not merely a non-error | **holds** | `_assert_graphql_data` compares the whole `data` payload against `{"allItems": {"edges": [{"node": {"id": emitted_id, "name": target.name}}]}}` — exactly one edge, and its `id` is asserted to be the same string that was fed in, closing the loop in both directions |
| G7 | `test_type_strategy_opt_out_reproduces_type_name` exists and takes `project_schema_override` | **present** | `::test_type_strategy_opt_out_reproduces_type_name(project_schema_override)` |
| G8 | The override is active **before** the schema reload | **holds** | `project_schema_override` is `examples/fakeshop/test_query/conftest.py::project_schema_override`, which `return`s `schema_reload.reload_all_project_schemas` (via the module-scoped `reload_all_project_app_schemas` fixture). The test calls it **inside** the `with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"})` block, so the clear-and-refinalize runs under the override |
| G9 | The reload really re-finalizes under the new setting (the snapshot is not sticky) | **holds** | `examples/fakeshop/schema_reload.py::reload_all_project_schemas` calls `registry.clear()` first, and `django_strawberry_framework/registry.py::TypeRegistry.clear` #"self._globalid_setting_snapshot = GLOBALID_SETTING_UNSET" resets the Slice-1 snapshot to the sentinel, so the next `finalize_django_types()` re-reads `RELAY_GLOBALID_STRATEGY` rather than reusing the default-strategy snapshot |
| G10 | The test is not a "right-path test" that passes for the wrong reason | **holds** | the assertion is `parsed.type_name == "ItemType"`. Under the default schema the same query emits `products.item`, so a passing run is only reachable if the `type` strategy was in force at finalization. The expected value **is** the path proof; no separate setup assertion is needed |
| G11 | The opt-out does not leak into sibling tests | **holds** | `conftest.py::_isolate_project_schema_for_acceptance_test` fingerprints every registry map plus the contributing module identities before the test and, on teardown, runs the full `reload_all_project_app_schemas()` under ambient settings whenever the fingerprint moved — which a `registry.clear()` + reload guarantees. Confirmed empirically: the full 122-test products module passes in declaration order under `-n0` |
| G12 | Existing **emitted-ID** assertions migrated to the model label | **holds** | no `_global_id("[A-Z]…` call and no `assert type_name == "<Name>Type"` survives anywhere under `examples/`. `test_products_api.py` line 1180 asserts `models.Item._meta.label_lower`; `test_library_api.py` lines 830 and 2802 assert `models.Genre._meta.label_lower`; line 3212 asserts the literal `"library.loan"` |
| G13 | Existing **filter-input** assertions migrated (the spec's own "easily-missed half") | **holds** | every `relay.GlobalID(type_name=…)` construction under `examples/` now passes a model label: 39 `"products.category"`, 24 `"products.item"`, plus `models.Item._meta.label_lower`, `models.Entry._meta.label_lower`, `models.Genre._meta.label_lower`, `models.Book._meta.label_lower`, `models.Loan._meta.label_lower`, `models.Card._meta.label_lower`, `"library.book"` / `"library.genre"`, and one deliberate `"nope.nonexistent"` negative |
| G14 | No type-anchored spelling survives in the live tier | **holds** | the single remaining literal GraphQL type name in a `GlobalID` position is `test_products_api.py` line 1253's `assert parsed.type_name == "ItemType"` — the `type`-opt-out test's own expected value. Everything else matching `ItemType` / `CategoryType` / `GenreType` / `EntryType` across the three test trees is a GraphQL fragment condition, an introspection name, a docstring, or a `class …Type:` definition in `tests/test_registry.py` |
| G15 | The deterministic-setup contract is satisfied by one of the two named shapes | **holds** | the **preferred** shape shipped (`override_settings` + a callable reload fixture); the **alternative** (a dedicated opt-out type / root field) was not taken — `grep -rn "globalid_strategy\|RELAY_GLOBALID_STRATEGY" examples/` matches only the opt-out test's own docstring and `override_settings` call |
| G16 | `examples/fakeshop/apps/*/schema.py` — "only if a dedicated opt-out type is chosen" | **resolved, and the file WAS touched** | the shipping commit `7d892d6f` deletes seven lines from `examples/fakeshop/apps/products/schema.py`: the staged `# TODO(spec-031-globalid_encoding-0_0_9 Slice 4)` anchor on `ItemType.Meta` plus its `# Pseudocode: globalid_strategy = "type"` block. That is `AGENTS.md` rule 26's staged-anchor removal, not the alternative being taken. No `globalid_strategy` key exists in any fakeshop schema at HEAD |

**Not a CODE GAP, recorded so the next reader does not re-open it.** The `## Test plan` names one live filter round-trip, but Decision 13 contracts three filter paths (`GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, `RelatedFilter`-expanded children). All three are live-covered at HEAD — the other two by pre-existing tests the migration re-pointed at the model label (D5 below). Coverage exists; only the spec's claim on it was missing.

**Not a CODE GAP, recorded so the next reader does not re-open it (2).** The spec's `Status:` line credits Slice 4 with "the multiple-`DjangoType`-per-model routing assertion" and no such live test exists. It is not a gap: the routing behavior is covered in the package tier by Slice 2's finalization audit (`tests/types/test_relay_interfaces.py::test_model_label_routing_audit_rejects_type_primary_with_model_secondary`, `::test_model_label_routing_audit_passes_model_primary_with_type_secondary`) and Slice 3's primary-routing decode, and no Slice-4 sub-bullet, Test-plan bullet, plan row, or DoD item ever asked for a live one. D1 below.

### Divergences found (spec vs. shipped)

1. **D1 — the `Status:` line promises Slice 4 a fourth deliverable its own contract never carries.** "plus the multiple-`DjangoType`-per-model routing assertion" was present at the authoring commit `b1f82f0e` (verified read-only via `git show b1f82f0e:docs/spec-031-globalid_encoding-0_0_9.md`) and was never propagated into the Slice-4 checklist, the Test plan, the plan table, or DoD item 6. One home against four, and shipped code agrees with the four. S1.
2. **D2 — a `## Current state` sentence that was false on its own date.** "Live HTTP suites … assert concrete `GlobalID` values (own-PK filtering, `node(id:)` refetch shape per `TODAY.md`)". The three-case stale-sentence test was applied and returns none of its three answers, because all three presume the observation was *true* when written. `git archive b1f82f0e examples/fakeshop/test_query` yields **zero** occurrences of `node(id` — root `node(id:)` did not exist until `DONE-032-0.0.9`, which the same section states three bullets above. The sentence had borrowed `TODAY.md` line 14's wording (verified at the same commit), where the phrase names the Relay *capability surface*, and re-attributed it to the live tier's assertion set. S2.
3. **D3 — the migration population was three live suites, not two.** At `b1f82f0e` the type-anchored inventory was fifteen live sites: `test_products_api.py` (three emitted-`id` expectations at the `EntryType` / `ItemType` / `CategoryType` nested payload, three filter inputs — one own-PK `in`, two relation), `test_library_api.py` (two `assert type_name == "GenreType"` round-trips, five filter inputs), and **`test_kanban_api.py`** (two `relay.GlobalID(type_name="CardType", …)` filter inputs in `::test_filter_cards_by_own_pk_relay_global_id_in`). The kanban suite is named nowhere in the spec; the shipping commit migrated it to `models.Card._meta.label_lower` anyway. The Slice-4 checklist also says "the `assert type_name == "GenreType"` round-trip" in the singular where there were two. S3/S5/S6/S8.
4. **D4 — one package-tier site migrated with them, owned by no spec sentence.** `tests/optimizer/test_relay_id_projection.py::test_relay_id_with_custom_pk_attname_avoids_lazy_load` asserted `node_id.type_name == "CustomPKItemNode"` and became `CustomPKItem._meta.label_lower` in the same commit. No slice's Test plan lists that file. This is exactly the shape `docs/builder/BUILD.md` `### Test staleness a focused run cannot see` calls a wire-shape conversion, whose population is a cross-tree grep and not the files a slice names. S3/S5/S6/S8.
5. **D5 — two of Decision 13's three filter paths are live-covered by the migration bullet, not by a named test.** After migration, `test_products_api.py::test_products_items_filter_by_related_category_global_id` is the live `RelatedFilter` relation-branch round-trip; `::test_products_categories_filter_by_relay_own_pk_global_id_in` and `test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_list` are the live `GlobalIDMultipleChoiceFilter` multi-value round-trips; and `test_library_api.py::test_relay_global_id_filter_rejects_wrong_type_name` pins that the retained wrong-target rejection now reports **model labels** in its message. Shipped live coverage no Test-plan bullet claimed. S6.
6. **D6 — the reload seam is project-wide, and the spec still describes the products-scoped one.** The checklist's "factor the products schema-reload into a callable fixture helper" describes what shipped in `7d892d6f` (a `_reload_products_project_schema()` local to the products suite). At HEAD the seam is the shared `examples/fakeshop/schema_reload.py::reload_all_project_schemas`, exposed as `conftest.py::project_schema_override`, generalized by `dbe8e77e` because a products-scoped reload after `registry.clear()` strands the other five apps and the aggregate build then raises an order-dependent `LazyType` `KeyError` / `DuplicatedTypeName`. S4.

**Deliberately NOT written into the spec.** The two per-suite `GlobalID` conveniences (`test_products_api.py::_global_id`, `test_library_api.py::_decode_global_id`) stay unnamed: they are test-local ergonomics, and the library suite's raw-`base64` decode is a deliberate Strawberry-independence choice its own docstring records. The spec contracts assertions, not the helpers that spell them.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`; line numbers are post-edit. Every change is triggered by Slice 4.

| # | Line(s) | Change | Reason |
| --- | --- | --- | --- |
| S1 | 5 | `Status:` line, Slice-4 clause: dropped the never-built "plus the multiple-`DjangoType`-per-model routing assertion", added the `type`-opt-out test and the live-tier migration that Slice 4 actually shipped, and pointed the routing coverage at its real owners (Slice 2's audit, Slice 3's decode) | D1 |
| S2 | 111 | `## Current state`, live-tier bullet: replaced the impossible `node(id:)`-refetch attribution with the measured pre-build inventory (fifteen sites, three files, split emitted-value vs filter-input), stated why no live suite could have asserted a root `node(id:)` refetch, and added the one package-tier site | D2, D3, D4 |
| S3 | 74 | Slice-4 checklist, migration bullet: named all three live suites, corrected the library round-trip count to two, enumerated the filter-input split per suite, and added the package-tier `test_relay_id_projection.py` site | D3, D4 |
| S4 | 76 | Slice-4 checklist, deterministic-setup bullet: replaced the "preferred shape / alternative" pair with the shipped shape (`project_schema_override` → `reload_all_project_schemas`, which owns the `registry.clear()`), stated why the reload is project-wide, recorded that the alternative was not taken and that the staged TODO anchor was removed, and stated why the assertion is self-proving | D6, G15, G16 |
| S5 | 419 | Implementation plan Slice-4 row: files replaced by the four actually touched with per-file counts; the `~6` new-tests estimate replaced by the measured **3 net-new + 16 migrated**; the `apps/*/schema.py` conditional resolved to the staged-anchor deletion | D3, D4, G16 |
| S6 | 522-532 | `## Test plan` Slice-4 block: restructured into the three net-new tests (each with the property that makes it distinguishing) and the migration bullet, and named the four migrated tests that carry Decision 13's relation / multi-value / wrong-target live coverage | D5, D3 |
| S7 | 532 | `## Test plan`, the closing "check before declaring the suites undisturbed": scope widened from "the products suite" to the `grep -rn` across all three test trees, naming the third live suite and the package-tier suite a focused run cannot see, and citing `AGENTS.md`'s three-tree definition | D3, D4 |
| S8 | 589 | DoD item 6: each of the three tests named by symbol; the round-trip's "verbatim, never reconstructed" property stated; the migration scoped to "all three affected live suites and the one affected package-tier suite"; added the closing invariant that no type-anchored payload survives in the live tier apart from the opt-out test's deliberate `"ItemType"` | D3, D4, D5, G5 |
| S9 | 687, 694, 695, 698 | Link definitions: four added — `[test-optimizer-relay-id-projection]`, `[fakeshop-schema-reload]`, `[fakeshop-test-kanban]`, `[fakeshop-test-query-conftest]` — each in alphabetical position within its group header. `[glossary-relatedfilter]` (line 634) was already defined and is now additionally used from the Test plan | required by S2-S7 |

No spec sub-check is left `- [ ]`; no deferral reason is owed.

### Rationale companion entries appended

All in `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`, append-only, in the `**Post-ship:**` convention Slices 1-3 established, keyed to the Decision they belong to.

- **Decision 9 → `### Changes this Decision underwent`** (line 286), one bullet: the flip's test-side blast radius was two files larger than the spec's census — the measured sixteen-site population, the two unnamed files, and the generalization that *a wire-format flip's affected population is defined by a grep across all three test trees, never by the files the slice text names*.
- **Decision 13 → `### Changes this Decision underwent`** (line 377), one bullet: two of the Decision's three filter paths are live-covered by the migration bullet rather than by a named test, with the four tests named — *when a conversion re-points an existing test at a new contract, that test has become the new contract's coverage and the spec must claim it by name*.
- **`## Non-Decision deliberation`** (lines 407-409), three bullets: (a) a dated observation that was false at its own date, and the fourth case the three-case test does not have — *grading against today's repo cannot distinguish "was true, then rotted" from "was never true", and the two need opposite fixes*; (b) the deterministic `type`-opt-out setup as it actually shipped and was later generalized, the not-taken alternative, the removed TODO anchor, and *a right-path test is best made unfalsifiable-by-accident through its expected value, not through a second assertion about the setup*; (c) the `Status:`-line over-promise — *a summary line is the one place in a spec with no downstream reader obliged to implement it, which is exactly why an unpropagated promise survives there*.

Eight link definitions were added to the companion (`[glossary-relatedfilter]`, `[test-optimizer-relay-id-projection]`, `[fakeshop-products-schema]`, `[fakeshop-schema-reload]`, `[fakeshop-test-kanban]`, `[fakeshop-test-library]`, `[fakeshop-test-products]`, `[fakeshop-test-query-conftest]`), each in alphabetical position within its group header; the previously empty `<!-- examples/ -->` group is now populated.

### Static inspection helper

**Not run, recorded skip.** `docs/builder/BUILD.md` `### When to run the helper during build` triggers it when the plan adds logic to a file under `types/`. This plan adds no logic anywhere: it writes two Markdown files and no `.py`. (Worker 0's pre-flight step 2 already exercised it against `types/relay.py`, exit 0.)

### Plan declarations

- **Hot-path declaration:** `none` as planned. This slice's deliverable is test code and this pass writes no production code. Recorded for the next pass that does: the seams these tests exercise **are** hot — `types/relay.py`'s installed `resolve_typename` closure runs once per emitted node `id`, and `filters/base.py::_decode_and_validate_global_id` once per filter value (per element for the `in` lookup) — so a Worker 2 pass landing in either owes a before/after wall-clock median over a stated iteration count. Deliberate, not silence.
- **Floor-verification scope:** `none` as planned. No production code changes and no `.py` file is written, so there is no version-sensitive behavior to re-run at the floor. Had a Worker 2 pass landed on the live tier's request/response or schema-reload plumbing, the declared scope would have been focused `examples/fakeshop/test_query/test_products_api.py` at the floor in an isolated venv outside the repo, owned by that pass. Deliberate, not silence.
- **Ownership partition:** `none; sequential slices`.
- **Boundary count (split trigger):** zero new boundaries. No split question to answer beyond recording the count.

### Final verification checks run

Test scopes run, all without `--cov*` flags:

- `uv run pytest examples/fakeshop/test_query/test_products_api.py --no-cov -n0 -q -k "globalid or global_id"` → **8 passed**, 114 deselected, 3.90s. The three contracted Slice-4 tests plus the five sibling GlobalID rows in the products suite.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_kanban_api.py --no-cov -n0 -q -k "globalid or global_id or relay"` → **18 passed**, 219 deselected, 4.58s. The migrated library rows and the migrated kanban row.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py --no-cov -n0 -q` → **122 passed**, 22.38s. Single-worker, declaration order: proves the `type`-opt-out test's schema mutation is fully restored for its siblings within the module.
- `uv run pytest examples/fakeshop/test_query/ --no-cov -q` → **672 passed, 1 skipped**, 52.49s. The **whole live tier** under the default parallel `-n auto --dist loadscope`, which is what the fakeshop schema-registry cross-test pollution class needs (`docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list`); a focused green run alone would not have been proof. This is a live-tier sweep, not the full-suite sweep — the package `tests/` tree and the per-app trees are the final gate's.

Doc checks:

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` → **`OK: 31 terms`**, unchanged from pre-flight.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-031-globalid_encoding-0_0_9.md docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` → exit 0 (the `.md` link-def scaffold and group ordering, including the twelve new definitions across the two files).
- In-page anchors and reference-style link definitions, both files, after the edits: no undefined reference, no unused definition, no dangling in-page anchor. Every one of the twelve new cross-file definitions was disk-checked from its own file's directory and resolves to an existing path.
- Byte counts: spec `175,092` (from `169,444`); rationale companion `112,389` (from `104,080`).
- Post-edit sweep for the reconciled claims: no `node(id:) refetch shape` attribution and no `multiple-`DjangoType`-per-model routing assertion` remains in the spec.

Tree hygiene:

- `git status --short` re-read at the start of this pass: only this cycle's own files (`docs/SPECS/spec-031-globalid_encoding-0_0_9.md` modified; the rationale companion, build plan, and five slice artifacts untracked). HEAD `5ebcfe9c`. The concurrent session's four baseline-dirty paths from the plan preamble were absorbed by its mid-cycle commit; none was edited or reverted.
- `examples/fakeshop/db.sqlite3` was **not** written by this pass and is not dirty after the four test runs. Never reset, never `git checkout`-ed.
- No `git stash` / `git checkout` / `git restore` / `git worktree` was used. The four HEAD-history reads (`git show 7d892d6f …`, `git show b1f82f0e:…`, `git archive b1f82f0e examples/fakeshop/test_query`, `git log -S`) are read-only; the `git archive` extraction landed in the session scratchpad **outside** the repo.

### Worker 2 dispatch

**Not owed.** The CODE GAP list is empty and no test edit is judged necessary. Specifically, the case the maintainer flagged as most likely to justify a dispatch — a genuinely missing or non-distinguishing live test — was checked directly and does not hold: all three contracted tests exist, each pins the load-bearing property rather than an observable side effect (G2, G5, G6, G10), and the `type`-opt-out test is self-proving because its expected value is unreachable on the default path. Every divergence found is the spec under-describing or over-promising against shipped tests, which is Worker 1's own to fix.

### Deferred to `### Deferred work catalog` (for `bld-031-final.md`)

- **The stale `.py` comment batch is unchanged at four clauses.** Slice 4 adds none: the live-tier test files carry no falsified spec-031 claim in a comment. Every migrated row's comment was rewritten in the shipping commit to state the model-label contract (e.g. `test_library_api.py` #"Under the 0.0.9 model-label default the GlobalID carries the Django model", `tests/optimizer/test_relay_id_projection.py` #"derive it from the ORM rather than hardcoding so the assertion tracks the model, not a literal").
- **Still unclaimed after four slices** (raised by Slice 0, not taken by Slices 1-4, outside every functional slice's contract): the pre-archival `docs/spec-031-globalid_encoding-0_0_9.md` path is still asserted at spec lines 250 (Decision 1), 567 (DoD item 1), and 84 / 542 / 589-adjacent (the Slice-5 doc-wrap text), and DoD item 1's claim that the two net-new terms are absent from the terms CSV is still standing and still false. Slice 5 of this cycle is audit-only, so the integration pass must take these or record them as a maintainer follow-up.
- **Audit-only, for Slice 5's report.** `TODAY.md` and `docs/GLOSSARY.md` are out of fence this cycle; Slice 4's reconciliation makes one `TODAY.md` observation concrete for that audit: line 14's "own-PK GlobalID filtering, `node(id:)` refetch shape" phrasing is what the spec's `## Current state` mis-borrowed, and it is now accurate on its own terms (both surfaces shipped), so no `TODAY.md` change is implied — recorded so Slice 5 does not read S2 as a doc obligation.

### Summary

Slice 4 shipped complete. All three contracted live tests exist in `examples/fakeshop/test_query/test_products_api.py`, reach the real `/graphql/` stack, and assert what the spec says: the emitted `GlobalID` decodes to `models.Item._meta.label_lower`, the headline round-trip feeds the API-emitted string back verbatim into `filter: { id: { exact: … } }` and gets exactly the one right row, and the `type` opt-out applies `override_settings` **around** the `project_schema_override` reload so the override is in force when the schema re-finalizes — self-proving, because `"ItemType"` is unreachable under the default schema. The pre-`0.0.9` migration landed across a wider population than the spec described: fifteen live sites in three suites (products, library, **kanban**) plus one package-tier site in `tests/optimizer/test_relay_id_projection.py`, and no type-anchored `GlobalID` payload survives anywhere in the three test trees apart from the opt-out test's deliberate expected value. `examples/fakeshop/apps/products/schema.py` was touched, but to delete the staged Slice-4 TODO anchor, not to add the not-taken dedicated opt-out type. **CODE GAP list empty.** Nine spec changes reconcile the spec to the shipped tests: one summary line that promised a deliverable four other homes never contracted, one `## Current state` sentence that was false on its own date (a case the three-case test does not have), a migration census short by two files, and Decision 13's relation / multi-value / wrong-target live coverage claimed by name for the first time. Six rationale bullets appended. All three of Worker 0's handed items held; six further divergences surfaced beyond them.

### Final status

`final-accepted`. Procedural closure: no Worker 2, no Worker 3.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[today]: ../../TODAY.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-products]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
