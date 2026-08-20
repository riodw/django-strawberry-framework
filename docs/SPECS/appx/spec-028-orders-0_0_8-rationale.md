# Rationale companion: spec-028 (Ordering subsystem)

Companion to [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028]. It carries that spec's **deliberative layer** and nothing else: the review history that produced the contract, every Decision's justification, every alternative the Decision rejected and why it lost, and every claim a Decision once made and may no longer make. The spec carries the contract; this file carries how the contract was arrived at. Neither duplicates the other — the text here **left** the spec.

Read this when checking a finished implementation against the reasoning that produced it, or before re-opening a settled question. Worker 2 never reads it (`docs/builder/BUILD.md` `### Who reads it, and when`).

## Provenance of this record

Created by the `028` residual-reconciliation cycle's Slice 1 (`docs/builder/bld-slice-1-028-rationale_extraction.md`). `spec-028` was the last spec in `docs/SPECS/` with no `-rationale.md` sibling; `001` through `027` all had one.

Measured against the spec at `HEAD` before the move (289,080 bytes, 1,354 lines):

- the whole `Revision history (kept inline so the spec is self-contained)` block — its preamble plus seven `Revision N` entries, 70 lines. The preamble's own assertion that the history was kept inline moved out with it, because the assertion is no longer true.
- **13** `Justification:` blocks and **13** `Alternatives considered (and rejected):` blocks, one pair under each of Decisions 1-13, carrying **39** rejected alternatives in total (2 / 3 / 3 / 3 / 4 / 4 / 2 / 4 / 3 / 2 / 4 / 3 / 2).
- the review-round narration welded into the contract prose: **90** occurrences of `adversarial review`, **160** `rev-N` references, **89** `per <ID> of` citations, and **8** `Worker 1` references, spread across Decisions 2, 3, 5, 6, 8, 9, 11, 12, 13, the Slice checklist, Edge cases, the Test plan, Doc updates, and the Definition of done. All four counts read **0** in the spec afterwards.
- the `Status:` line's build-progress log — a single 4,300-character paragraph tracking Slices 1-6 as they landed, narrating two superseded maintainer-review corrections, quoting its own disproved diagnosis, attributing the full-suite gate to a named pass, and closing "Awaiting maintainer commit". Its four-piece closing narrative is preserved under `## Non-Decision deliberation`; the surviving shipped-state facts stayed in the spec.

**Deleted rather than moved**, because the current contract has falsified them and git preserves the history either way:

- the Status line's quoted round-1 diagnosis ("all nine lines are non-orders, sole-covered by the glossary tests, resolve when the kanban seed is fixed"), which the paragraph itself records as empirically disproved.
- the Status line's "Awaiting maintainer commit" — the card is `DONE-028-0.0.8`.
- Decision 3's "Prior revisions claimed `DjangoType.Meta.model` rejects abstract models at `_validate_meta` time" lead-in; the surviving sentence states what `_validate_meta` checks.
- the Edge-case note "a prior revision wrongly implied one" about the duplicate-field live test.
- Decision 11's "future drift back to the rev1 self-misuse", rewritten as "future drift to a list shape".
- the Decision 6 and DoD item 10 parentheticals asserting that the shipped subpass order was "NOT the inverted subpasses 3-and-4 prescribed by spec-027 rev8 H1"; the shipped order is stated positively and the correction is recorded under Decision 6 below.
- DoD items 26 and 28's narration of when and by whom the one full-suite run happened; both keep their rule.

**Not corrected here.** Slice 1 moved text; it did not fix the spec's factual drift. Findings D3-D16 of the build plan are Slice 3's, and the ones that belong to a Decision are recorded under that Decision's `### Claims this Decision may no longer make` so the Slice-3 pass can consume them per-Decision.

## Revision history

Seven revisions, verbatim as the spec carried them. Reproduced here because a decision's chronology is exactly what a reviewer needs and exactly what the contract must not narrate.

- **Revision 1** — initial draft. Pinned the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)), the subpackage layout ([Decision 2](#decision-2--subpackage-layout-and-public-export-surface)), the six-layer lazy-resolution pipeline borrowed from `django-graphene-filters` with the same Strawberry-adapted Layer 5 the filter card pinned in [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3 ([Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6)), the upstream-primitives parity floor ([Decision 4](#decision-4--upstream-primitives-parity-floor)), the `Ordering` enum shape and the `orderBy: [<T>OrderInput!]` argument shape ([Decision 5](#decision-5--ordering-enum-and-argument-shape)), the finalizer-phase-2.5 wiring seam ([Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)), the `Meta.orderset_class` promotion gate ([Decision 7](#decision-7--metaorderset_class-promotion-gate)), the cooperation contract with the filter subsystem and the `get_queryset` visibility hook ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer)), the input-class-namespace lifecycle ([Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)), the then-planned joint-`0.0.8` release-cut posture that is now superseded by [Decision 10](#decision-10--version-bumps-are-maintainer-commanded), the `order_input_type(OrderSet)` consumer helper ([Decision 11](#decision-11--order_input_typeorderset-consumer-helper)), the Layer 6 + DISTINCT ON design questions ([Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface)), and the live-HTTP coverage strategy ([Decision 13](#decision-13--live-http-coverage-strategy)). Out of scope: aggregation ([`AggregateSet`][glossary-aggregateset]) — `0.1.3`; [`DjangoConnectionField`][glossary-djangoconnectionfield] — `0.0.9`; permission cascade ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`; [Meta.search_fields][glossary-metasearch_fields] — `0.1.2`. Dependencies on these surfaces are forward-only: this card composes when they arrive without retrofit.
- **Revision 2** — review pass over rev1 captured in the maintainer's adversarial review. Every Blocking / High / Medium / Nit / Out-of-scope finding applied in a single pass; foundational findings (B1-B3) drove the largest reshapes.
  - **B1 — subpass order corrected to match shipped filter code.** [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering) reshaped from `bind → expand → materialize → orphan-validate` (the spec-027 rev8 *prescription*) to the actual shipped order `bind → expand → orphan-validate → materialize` (the actual shipped *implementation* in [`finalize_django_types`][finalizer]'s `_bind_filtersets` pass). Orphan-validate before materialize is load-bearing — leaves no stale ledger entries when an orphan check raises, so a re-run after the consumer fixes the orphan starts clean. Slice 1 checklist, DoD item 10, and the test plan all updated.
  - **B2 + B3 — `registry.clear()` pseudocode rewritten against actual code.** [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) code block: replaced the phantom `_types_by_model` / `_primary_types` field names with the actual `_types` / `_primaries` / `_models` / `_enums` / `_definitions` / `_pending` / `_finalized` fields (verbatim from [`TypeRegistry`][registry]'s field declarations); fixed the `except ImportError: return` in the last block to `except ImportError: pass` + `else:` (M-core-4 footgun fix from the shipped filter side preserved). All four try/except blocks now use the same uniform shape.
  - **H1 — `OrderSet.apply(...)` dispatcher dropped (YAGNI).** Decision 2, Decision 8, Implementation plan table, and DoD item 4 all updated. The filter side's `apply(...)` exists for sync-misuse `RuntimeError` rewrap that the order side never triggers (no async-only `get_queryset` re-derivation per step 4 of the apply pipeline). Consumers call `apply_sync` / `apply_async` directly.
  - **H2 — optimizer projection claim retracted.** Verified per `grep` that no logic in [`optimizer/walker.py`][optimizer-walker] or [`optimizer/plans.py`][optimizer-plans] inspects `queryset.query.order_by`. The user-visible behavior is correct because Django's ORM extends column fetches as needed — but that is Django's cooperation, not the package's. Order-aware projection augmentation is **out of scope for `0.0.8`** and explicitly not promised; the `test_library_books_order_preserves_optimizer_cooperation` narrative updated to reflect what the test actually pins.
  - **H3 — `__all__` cookbook parity verified.** Read the cookbook's `AdvancedOrderSet.get_fields` (`~/projects/django-graphene-filters/django_graphene_filters/orderset.py`); confirmed it carries the `if meta_fields == "__all__":` branch that walks `get_concrete_field_names(model)`. The reviewer's claim of divergence was incorrect; the spec preserves the parity claim with the verifying line citation now inline in [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6).
  - **H4 — position-side-channel leak acknowledged.** [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4 expanded to name the leak explicitly: ordering by a hidden related column changes the *position* of visible parent rows based on data the user cannot read, so a determined consumer can infer the relative ordering of hidden rows by diff'ing two queries. The leak is intentionally accepted for `0.0.8` (low bandwidth, no value disclosure — only causal explanation of visible ordering); the closing-this design is deferred to the `0.0.9` cohort. The `OrderSet` and `RelatedOrder` GLOSSARY entries (Slice 5) call this out so consumers reaching for permission gates know the risk.
  - **M1 — pipeline step count corrected.** "The 7-step pipeline" → "The 8-step pipeline" (the steps were numbered 1-8 in the body).
  - **M2 + M5 + M6 + M7 — Slice 4 live HTTP coverage expanded from 10 to 13 tests.** Added: `test_library_books_order_by_flat_shorthand_path` (M2; pins `Meta.fields = ["shelf__code"]` → `shelfCode:` flat surface); reverse-FK multiplicity test redesigned to *assert* the multiplication (M5; the prior workaround of seeding one shelf was brittle); `test_order_check_permission_denies_for_active_field` AND `test_order_check_permission_quiet_for_inactive_field` (M6; split from a single combined test so regressions surface as named failures); `test_order_empty_list_passes_through` AND `test_order_null_direction_skips_field` (M7; pins the no-op contracts).
  - **M3 — `INPUTS_MODULE_PATH` constant + `_input_type_name_for` helper.** Decision 2 sets.py / inputs.py contents updated to hoist both symbols from the filter side's [`filters/inputs.py`][filters-inputs] (its `INPUTS_MODULE_PATH` + `_input_type_name_for`) verbatim — `INPUTS_MODULE_PATH` for the module-path string + `_input_type_name_for(orderset_class)` for the `<Name>InputType` formula.
  - **M4 — `Ordering.resolve()` example corrected.** Added the missing `from django.db.models.expressions import OrderBy` import; added a one-line comment explaining `None` is Django's sentinel for "no NULLS clause" (NOT `False`).
  - **M8 — "order on columns the `DjangoType` cannot select" documented.** The rev1 review asked for a test named `test_order_accepts_field_not_in_djangotype_meta_fields`; the behavior ships as documented behavior (see [Edge cases][spec-028-edge-cases]) and was NOT pinned by a dedicated test in `0.0.8` (corrected in rev7 — the named test was not shipped).
  - **M9 — `_helper_referenced_ordersets` location pinned to `orders/__init__.py`.** Decision 2 was previously ambiguous (listed it under `inputs.py`); now correctly pinned to the package `__init__.py` (matching the filter side's location, `django_strawberry_framework/filters/__init__.py::_helper_referenced_filtersets`). The two `registry.clear()` blocks per Decision 9 stay separate.
  - **M10 — duplicated KANBAN / CHANGELOG past-tense paragraph deduplicated.** The CHANGELOG bullet now references the KANBAN body as the single source of truth and carries only a one-line headline summary.
  - **N1 — link slugs renamed to match new spec filenames.** Every `[spec-NNN]` slug updated to the post-renumbering filename (`[spec-021]` → `[spec-027]`, `[spec-016]` → `[spec-020]`, etc.); the new spec slug is `[spec-028]`. The link defs at the bottom carry the canonical paths.
  - **N2 — `Verified in upstream` block inlined.** Decision 4 now carries the verbatim list of strawberry-django ordering symbols from the KANBAN card body, so the spec is self-contained.
  - **N3 — `_validate_orderset_class` import-cycle note added.** DoD item 9 now spells out the local in-function `from ..orders.sets import OrderSet` import requirement (mirroring the filter side's [`_validate_filterset_class`][base]).
  - **N4 — `tests/orders/` file count harmonized.** Decision 2 and Decision 13 both now say "7 files total" (1 shell + 4 mirror + `test_finalizer.py` + `test_composition.py`); DoD item 11 was already correct.
  - **N5 — `<DATE>` placeholder.** `YYYY-MM-DD` → `<DATE>` across Slice 5 / Decision 10 / DoD item 24 so the placeholder reads as "fill this in" instead of risking literal ship into the changelog.
  - **N6 — L5 contingency made deterministic.** Decision 10 and DoD item 24 now name a concrete `grep -E 'WIP-ALPHA-[0-9]+-0\.0\.8' KANBAN.md` command for the Slice-5 author to run at merge time.
  - **N7 — `apply_async` permission-hook dispatch.** Decision 8's sync/async-split subsection describes the shipped behavior: `apply_async` resolves the request synchronously, then dispatches `_run_permission_checks` through `sync_to_async(thread_sensitive=True)` so a consumer hook issuing a blocking ORM read runs in a worker thread and does NOT block the event loop; parsing and `queryset.order_by(...)` stay unwrapped (pure construction, no I/O). (An earlier draft of this note claimed the hooks were NOT wrapped; the shipped order code DOES wrap the permission pass — as does the filter side via its `_apply_common_finalize` wrapper — so Decision 8 and this note were corrected to match the code in rev7. Verified against [`django_strawberry_framework/orders/sets.py::OrderSet.apply_async`][orders] and `tests/orders/test_sets.py::test_orderset_apply_async_runs_check_permission_in_sync_to_async`.)
  - **N8 — proxy / MTI semantics documented.** Decision 3 now spells out the `"__all__"` behavior for proxy models, multi-table inheritance, and abstract models.
  - **N9 — `noqa: A002` convention note.** User-facing API resolver example now carries `# noqa: A002` on the `filter:` parameter, and the surrounding prose notes that `order_by` does not need the suppression (but `input:` would, for future cards).
  - **O1 + O2 — forward-compatibility previews added to Decision 12**, covering the then-open `Meta.distinct` shape choice and the then-open Layer 6 path choice.
  - Filename rebased from `spec-024-orders-0_0_8.md` to `spec-028-orders-0_0_8.md` and the archived filter spec to `docs/SPECS/spec-027-filters-0_0_8.md` per the maintainer's spec-renumbering pass between rev1 and rev2.
- **Revision 3** — sweep-residual pass over rev2 captured in the maintainer's adversarial review. Rev2 closed all 27 rev1 findings cleanly; rev3 closes the four sweep-residuals (R1-R4: count-update misses) and the three new observations (N-new-1 through N-new-3: phrasing tweaks) the rev2 review surfaced. None of these affect architecture or implementation plan; the spec is now internally consistent on every cited count.
  - **R1 — "seven-step pipeline" residual.** Decision 8's Justification list read "The seven-step pipeline reflects this simplification" even though Decision 8's body was already corrected to "8-step" in rev2's M1 fix. Updated to "The eight-step pipeline reflects this simplification."
  - **R2 — section header count.** Test plan's `examples/fakeshop/test_query/test_library_api.py` subsection header read "**Exactly 10 new live HTTP tests**" while the body listed 13 and every other count cite (DoD item 15, KANBAN past-tense body, CHANGELOG bullet) said 13. Updated to "**Exactly 13 new live HTTP tests**".
  - **R3 — Implementation plan table.** Slice 4 row had `New tests = 10` with the rev1 capability list of 10 items. Updated to `13` with the inline list extended to name the three new capabilities (flat-shorthand path / split-pair active-input-only permission / empty-list + null-direction no-ops). Line delta `+260 / -5` → `+330 / -5` to account for the three new test bodies.
  - **R4 — Decision 13 capability list.** The conceptual summary still enumerated the rev1 10 capabilities. Extended to 13 with the three rev1-feedback additions (flat-shorthand, split-pair permission, two-no-op-cases) so Decision 13 and Slice 4 carry the same shape.
  - **N-new-1 — H4 deferral decoupled from connection-aware optimizer planning.** Decision 8 step 4's "deferred — likely to land alongside the same `0.0.9` cohort that ships connection-aware optimizer planning" rephrased per the reviewer's recommendation. The leak-closing design and connection-aware optimizer planning are orthogonal; pinning them to the same cohort risked future readers thinking the deferral was already scheduled. Now reads "deferred — likely to a sibling `0.0.9` ordering-permissions card; the connection-field cohort is the natural integration point but the leak-closing work is independent of connection-field design."
  - **N-new-2 — `_helper_referenced_ordersets` placement rationale refined.** Decision 2's `__init__.py` bullet justified the ledger's location by the import-dependency-avoidance argument, but `orders/__init__.py` already imports `INPUTS_MODULE_PATH` and `_input_type_name_for` from `inputs.py` (per the bullet immediately above), so the import dependency exists either way. Rewrote the rationale as a locality argument: the ledger is co-located with its only writer (`order_input_type`), matching the filter side's arrangement at [`django_strawberry_framework/filters/__init__.py::_helper_referenced_filtersets`][filters-base]. Same outcome, honest rationale.
  - **N-new-3 — `DEFERRED_META_KEYS` staleness caveat.** Decision 12's O1 forward-compat preview asserted a `DEFERRED_META_KEYS` membership claim for `Meta.distinct` / `Meta.distinct_class` as a stable-state fact; rev3 named the then-current contents and added a staleness caveat.
- **Revision 4** — contract pass over rev3 captured in the maintainer's adversarial review. Rev3 closed every prior finding cleanly; rev4 closes the new contract issues the rev3 review surfaced — four Blocking (list-shape helper contract, clear lifecycle, NULLS-positioning test field, `"__all__"` cookbook parity), four High (shared-mixin home, owner/model validation, relation-level permission dispatch, enum casing), five Medium (materialization typing, duplicate-field test alignment, `Ordering` symbol list consistency, line-number → symbol-qualified refs, abstract-model claim correction), two Nits (`GraphQLError` link, `apply_async` annotation). The Blocking findings reshaped the helper contract and the clear lifecycle materially; the High findings tightened owner-binding and permission dispatch to match the shipped filter side exactly. The 14-test live HTTP plan reflects the H3 active-branch relation-level permission gate test added in this pass.
  - **B1 — `order_input_type` list-shape contract.** Helper returns the **element** type `Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]` (mirrors filter side); resolvers wrap as `list[order_input_type(OrderSet)] | None` to match the `orderBy: [<T>OrderInputType!]` list-shaped GraphQL argument. Decision 5, Decision 11, all User-facing API examples, DoD item 7, and the test plan all updated to use the list-wrap shape; the list-wrap SDL shape (`orderBy: [MyOrderInputType!]`) is exercised by the fakeshop schema's `list[order_input_type(...)]` resolver annotations and the live HTTP order tests (an earlier draft named a `test_order_input_type_resolver_wraps_as_list_under_strawberry_schema` unit test; it was not shipped — corrected in rev7).
  - **B2 — order namespace clear lifecycle matches filter side verbatim.** Decision 9 lifecycle contract rewritten: `clear_order_input_namespace()` clears `_materialized_names` + `OrderArgumentsFactory.input_object_types` + `OrderArgumentsFactory._type_orderset_registry` + every `OrderSet` subclass's `_owner_definition` / `_expanded_fields` / `_is_expanding_fields` — and **leaves already-materialized module globals parked** in `orders.inputs.__dict__`. Parking is load-bearing: `materialize_input_class` overwrites the global via `setattr` on the next finalize, so the parked class is replaced in place; `delattr` would break held `strawberry.lazy(...)` LazyTypes in consumer modules whose autouse-reload fixture did NOT also reload the holder. Test plan and DoD items 6 + 10 updated to assert the broader reset set AND to stop expecting module-global deletion.
  - **B3 — NULLS-positioning live test retargeted to `Book.subtitle`.** Earlier revisions used `description: DESC_NULLS_LAST` (`Book.description` does not exist on the current model) and `title: DESC_NULLS_LAST` (`Book.title = TextField()` is non-null and cannot satisfy NULLS-last). `Book.subtitle = TextField(blank=True, null=True)` is the only nullable text field; the test now seeds at least one `subtitle=None` row and asserts the non-null row appears first under `DESC_NULLS_LAST`. Slice 4 checklist, test plan, Decision 5 example, and the multi-field example all updated to consistent field names.
  - **B4 — `"__all__"` cookbook parity corrected to include forward FK / OneToOne column leaves.** Earlier revisions said `"__all__"` "excludes relations entirely" but the cookbook's [`get_concrete_field_names`][upstream-cookbook-mixins] uses `hasattr(f, "column")`, which INCLUDES forward FK / OneToOne columns (their underlying `<field>_id` lives on the model's own table). Only reverse relations and `ManyToManyField` managers are excluded. Decision 3 and the Edge cases entry now state the column-backed expansion explicitly: `BookOrder.Meta.fields = "__all__"` produces `id`, `title`, `subtitle`, `circulation_status`, AND `shelf` (forward FK column, sorts by `shelf_id`) — but NOT `genres` (M2M) or `loans` (reverse FK). Same-name `RelatedOrder(...)` overrides the column leaf for nested traversal. Package tests pin both shapes.
  - **H1 — shared mixin home refactored to `sets_mixins.py`.** The neutral set-family-shared module already exists at [`django_strawberry_framework/sets_mixins.py`][sets-mixins] carrying both `LazyRelatedClassMixin` and `ClassBasedTypeNameMixin`; `orders.base` imports `LazyRelatedClassMixin` from there (NOT from `filters.base`), `orders.sets.OrderSet` inherits `ClassBasedTypeNameMixin` for the `{cls.__name__}InputType` naming convention, and `orders.inputs._input_type_name_for()` delegates to `orderset_class.type_name_for()`. All `filters/base.py::LazyRelatedClassMixin` references in spec body replaced with `sets_mixins`; the rejected-alternative prose marked obsolete with a historical breadcrumb.
  - **H2 — `_bind_orderset_owner` model-compatibility check pinned non-optional.** Decision 6 subpass 1 expanded into three named checks: (a) first-bind model compatibility (`definition.model` must be the orderset's `Meta.model` OR derive from it, mirroring the filter side's [`_bind_filterset_owner`][finalizer] check); (b) related-target agreement for two-owner reuse; (c) idempotent re-bind. Without (a), a `BookOrder` wired onto `BranchType` would build a valid-looking `Book`-field input and apply those paths to a `Branch` queryset, producing a late `FieldError` instead of a finalize-time `ConfigurationError`. New finalizer test `test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` pins this.
  - **H3 — relation-level permission dispatch specified as active-branch double-dispatch.** Decision 8 step 6 expanded to mirror the filter side's [`_run_permission_checks`][filters-base] verbatim: for active `RelatedOrder` branch `shelves`, both `BranchOrder.check_shelves_permission(request)` (parent's per-branch gate — the consumer's defense for the position-side-channel leak named in step 4) AND `ShelfOrder.check_code_permission(request)` (child orderset's field gate) fire, deduped per `(OrderSet class, method name)` via a shared `_fired` map. Four new package tests and one new live HTTP test (`test_order_check_permission_denies_active_related_branch`) pin the double-dispatch contract; live test count bumped from 13 to 14.
  - **H4 — enum literal corrected to lower-case `available`.** Earlier revisions wrote `circulationStatus: { exact: AVAILABLE }` in the filter+order composition live HTTP test, but the current `BookTypeCirculationStatusEnum` exposes lower-case `available` / `checked_out` per the package's [Choice enum generation][glossary-choice-enum-generation] (stored DB values, not Python-attr casing). Verified against the shipped `test_library_books_filter_by_choice_enum` live test which uses the same shape.
  - **M1 — `_materialized_names` typing corrected to `dict[str, type]` storing input class.** Earlier revisions wrote `dict[str, type[OrderSet]]` storing the source `OrderSet`. The `materialize_input_class(name, input_cls)` signature passes the materialized input class as the second argument (that's what's `setattr`-ed to the module global); source-class collision detection lives separately in `OrderArgumentsFactory._type_orderset_registry` (mirrors the filter side's split). DoD item 6 and Decision 9 updated.
  - **M2 — duplicate-field edge case un-pinned to a live test.** Earlier revisions claimed a live HTTP test pinned the `orderBy: [{ name: ASC }, { name: DESC }]` behavior; the 13-test plan did not include one. Edge case rewritten as documented behavior covered by package-level parsing/queryset tests only.
  - **M3 — `Ordering` symbol added to every shipped-symbol sweep.** Slice 5 doc-update bullets for `docs/README.md` and `README.md` now include `Ordering` consistently alongside `OrderSet` / `RelatedOrder` / `order_input_type` / `Meta.orderset_class`.
  - **M4 — line-number refs converted to symbol-qualified.** Standing-doc body references that earlier revisions wrote as raw `path:NN` line numbers (in `finalizer.py`, `registry.py`, `filters/inputs.py`, `filters/__init__.py`, `types/base.py`, and `filters/sets.py`) were rewritten as `path::Symbol` forms (e.g., `django_strawberry_framework/types/finalizer.py::_bind_filtersets`). Per AGENTS.md, raw `path:NN` line refs are allowed only in per-cycle scratchpads; this card is a standing design doc. (This pass left the revision-history breadcrumbs raw; rev7 extended the conversion to them too, since the standard is not section-scoped — see Revision 7.)
  - **M5 — abstract-model claim corrected to "undefined for `0.0.8`".** Earlier revisions claimed `_validate_meta` rejects abstract models, but verified against [`django_strawberry_framework/types/base.py::_validate_meta`][base] — it only checks `Meta.model` is a Django model class; it does NOT inspect `model._meta.abstract`. Decision 3 rephrased to mark abstract-model `OrderSet` targets as explicitly out of scope / undefined for `0.0.8`. A future card that adds the abstract-model guard in `_validate_meta` can revisit; until then consumers should declare concrete subclasses.
  - **N1 — `GraphQLError` link fixed.** Decision 8 step 4 wrongly linked `GraphQLError` to the `configurationerror` glossary anchor. Re-phrased to drop the misleading link (GraphQLError lives in the `graphql` module, NOT the package's exception hierarchy, so a glossary link is not warranted) AND name the canonical import path inline (`from graphql import GraphQLError`, NOT `strawberry.exceptions`).
  - **N2 — `apply_async` return annotation corrected to `-> QuerySet`.** Earlier revisions wrote `apply_async(...) -> Awaitable[QuerySet]`. Since `apply_async` is an `async def` (mirrors the filter side at [`django_strawberry_framework/filters/sets.py::FilterSet.apply_async`][filters-base]), the function annotation is the coroutine's resolved value (`QuerySet`); the call expression IS the awaitable. Five locations updated (Slice 1 checklist, Decision 2 sets.py bullet, Decision 8 sync/async-split list, DoD item 4, the body comments around the example).
- **Revision 5** — version-bump command boundary. Maintainer clarification after the first Revision-5 wording: the ordering task ships in `0.0.8`; `0.0.9` references are proactive follow-up planning for the cards that can start after Ordering is Done. This card does **not** update `pyproject.toml`, [`django_strawberry_framework/__init__.py::__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or promote a release heading unless the maintainer explicitly gives the version-bump command. Spec-body amendments:
  - **Decision 10 — rewritten.** Historical joint-cut and rolling-patch prose is retired for this card. [Decision 10](#decision-10--version-bumps-are-maintainer-commanded) now records the maintainer-commanded release boundary.
  - **Slice 5 / DoD item 24 — version-field work removed.** Slice 5 owns docs, glossary, KANBAN, and allowed `CHANGELOG.md` content updates only. It does not own source version edits.
  - **KANBAN past-tense Done body — release sentence rewritten.** The Slice-5 [`KANBAN.md`][kanban] past-tense body says the ordering subsystem shipped in `0.0.8` and leaves `0.0.9` as follow-up-card planning.
  - **`CHANGELOG.md` promotion timing — command-gated.** This card may append Ordering bullets under the active heading, but release-heading promotion happens only with the explicit version-bump command. The CHANGELOG-edit permission for this card still comes from DoD item 23 per the explicit-instruction rule at [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told".
  - **No spec rename.** This card stays at `docs/spec-028-orders-0_0_8.md`; it was tagged `WIP-ALPHA-028-0.0.8` in KANBAN during implementation and moved to `DONE-028-0.0.8` at Slice 5 (the task ships in `0.0.8`).
- **Revision 6** — post-ship coherence pass over rev5 captured in the maintainer's adversarial review. The build had completed and the gate was green, but the spec still mixed build-plan voice ("does not exist on disk yet", unchecked checklist) with shipped-state claims (Status line, final gate). This revision commits the spec to a **single state model: the final implementation record.** No architecture or implementation changed; the edits are documentation-coherence only.
  - **B1 — one state model chosen.** The header now declares the spec the final implementation record (shipped in `0.0.8`); the [Slice checklist][spec-028-slice-checklist] is ticked with a completion banner; the former "Current state" section is renamed [Pre-implementation baseline (captured before Slice 1)][spec-028-baseline] with a banner marking it a pre-Slice-1 snapshot rather than a description of the repo today. Stale present-tense baseline claims (`orders/` "does not exist on disk yet"; the GLOSSARY symbols "planned for 0.0.8 status today") are dated to pre-Slice-1.
  - **B2 — version boundary stated explicitly.** Header + [Decision 10](#decision-10--version-bumps-are-maintainer-commanded) now say plainly: Ordering shipped *within* `0.0.8`, this card did NOT bump toward `0.0.9`, and the `0.0.8` version-file values (`pyproject.toml` / `__version__` / `test_version`) plus the `CHANGELOG.md` `__version__` note were set under the maintainer's separate explicit release command, not by this feature card. Resolves the apparent "stay on 0.0.7 vs bump to 0.0.9" ambiguity and reconciles the CHANGELOG finding (M6 of the rev5 review).
  - **H3 — raw line-number references converted (standing body).** The Status line's `TypeRegistry.clear` / `finalize_django_types` / `filters/sets.py` references, the `noqa: A002` note's fakeshop-schema ref, the Decision 2 `_helper_referenced_filtersets` ref, the upstream cookbook ref in "Explicitly do not borrow", and the test-plan's intra-document cross-references were all converted to symbol-qualified / test-name forms. (This pass exempted the revision-history breadcrumbs; rev7 removed that exemption and converted them too — see Revision 7.)
  - **H4 — export contract made precise and aligned to the filter twin.** [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) now classifies every order symbol into three tiers (public-in-`__all__`; advanced-in-`__all__`; advanced-via-submodule-only). The dead `from .factories import OrderArgumentsFactory` re-export was removed from [`orders/__init__.py`][orders] so the factory is reached via `django_strawberry_framework.orders.factories` exactly like the filter side's `FilterArgumentsFactory`; `OrderSetMetaclass` stays in `__all__` because the filter twin keeps `FilterSetMetaclass` in its `__all__` (one-for-one parity). Nothing imported the factory from the entry point, so the removal is non-breaking.
  - **H5 — final-gate owner and timing named.** The Status line now records that the green full-suite gate was the maintainer-directed assistant pass at the maintainer's explicit `run tests and coverage` request; [Definition of done][spec-028-dod] items 26 + 28 carry the same reconciliation so the no-local-pytest worker rule and the gate-green claim no longer read as contradictory.
- **Revision 7** — spec-vs-shipped-code accuracy pass over rev6 captured in the maintainer's adversarial review. The state-model and version-boundary work from rev6 held; rev7 closes the remaining places where the spec's prose drifted from the shipped ordering code/tests. Documentation-only; no architecture or implementation changed.
  - **B1 — Decision 8 async permission-hook contract corrected to match the shipped code.** Earlier prose (and the rev2 N7 note) claimed `apply_async` does NOT wrap `check_*_permission` hooks in `sync_to_async`. The shipped [`OrderSet.apply_async`][orders] resolves the request synchronously, then dispatches `_run_permission_checks` through `await sync_to_async(cls._run_permission_checks, thread_sensitive=True)(...)` — so a hook doing a blocking ORM read runs in a worker thread and does not block the event loop; parsing and `queryset.order_by(...)` stay unwrapped (pure construction). This mirrors the filter side, which runs its permission pass under `sync_to_async(thread_sensitive=True)` via `_apply_common_finalize`. Decision 8's sync/async-split subsection and the N7 breadcrumb were rewritten to the shipped behavior. Also corrected: the apply pipeline calls the classmethod `cls._run_permission_checks(input_value, request)`, while the instance method `check_permissions(self, request)` is a cookbook-compatible delegate reading `self._input_value` — Decision 8 step 6 now states the split.
  - **H2 — test-plan names reconciled to the shipped tests.** The Decision 8 "Tests pin the contract" list and the `tests/orders/test_sets.py` / `test_inputs.py` test-plan entries named tests that were renamed before ship (e.g., `test_check_permission_fires_parent_relation_gate_on_active_branch` → `test_orderset_check_permission_active_relatedorder_branch_fires_parent_gate`; `test_apply_extracts_request_from_info_context_request_attribute` → `test_orderset_request_from_info_reads_context_request_attribute`; the forwardref test → `test_order_input_type_returns_element_annotation_for_orderset_subclass`). Two named tests were never shipped: `test_order_accepts_field_not_in_djangotype_meta_fields` (the "order on columns the type cannot select" behavior ships as documented behavior, not pinned by a dedicated test) and `test_order_input_type_resolver_wraps_as_list_under_strawberry_schema` (the list-wrap SDL shape is exercised by the fakeshop schema's `list[order_input_type(...)]` annotations + the 14 live HTTP order tests). The spec now names only tests that exist and labels the two behaviors as documented-not-dedicated-test.
  - **H3 — revision-history line refs converted; the breadcrumb-exemption claim removed.** The rev4 M4 / rev6 H3 notes claimed revision-history breadcrumbs were exempt from the symbol-qualified-reference rule. The repo convention is not section-scoped, so every remaining raw `path:NN` ref in the revision history (in `finalizer.py`, `registry.py`, `filters/inputs.py`, `filters/__init__.py`, the cookbook `orderset.py`, and `types/base.py`) and the intra-document `line NNN` cross-refs in the rev3 R-bullets were converted to `path::Symbol` / section forms, and the exemption sentences were deleted.
  - **M4 — Slice 2 implementation-plan table corrected.** The table row said `clear_order_input_namespace` "clears module globals"; the shipped helper leaves module globals **parked** and clears the ledgers/caches (`_materialized_names`, `_field_specs`, the `OrderArgumentsFactory` class caches, per-subclass binding state). `_field_specs` was added to the clear list in DoD items 6 + 10 (the implementation clears it and Decision 9 documents it).
  - **M5 — Status line "three" → "four".** The first paragraph said "three INDEPENDENT pieces" then enumerated (a)–(d); corrected to "four".

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-028-d1].

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 and observed by every recent spec ([`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018], [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019], [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020], [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021], [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022], [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023], [`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][spec-025], [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027]) bakes the card's NNN and target patch into the filename.
- The card body's `docs/spec-orders.md` predates that convention.
- The topic slug is `orders` (matching the [`django_strawberry_framework/orders/`][orders] subpackage name, the cookbook's `orders.py` filename, and the filter side's `filters` precedent).
- The Slice-5 [`KANBAN.md`][kanban] rewrite updates the card body's stale reference to the canonical name, so the cross-reference resolves after archival per [Step 8 of NEXT.md][next-step-8].

### Alternatives considered (and rejected)

- **Honor the card body verbatim with `docs/spec-orders.md`.** Rejected: breaks the structured-filename convention and would land an unnumbered spec next to a numbered cohort.
- **Longer topic slug `ordering_subsystem`** (matching the card title "Ordering subsystem"). Rejected: `orders` already names the architectural intent, matches the subpackage name, and matches the filter side's `filters` precedent — symmetry across the two sibling Layer-3 subsystems makes future Aggregation-card naming (`aggregates`) self-consistent.

### Changes this Decision underwent

- **rev2 N1** — every `[spec-NNN]` link slug was rebased onto the post-renumbering filenames (`[spec-021]` -> `[spec-027]`, `[spec-016]` -> `[spec-020]`), and this spec's own slug became `[spec-028]`.
- **rev2, filename rebase** — the file itself moved from `spec-024-orders-0_0_8.md` to `spec-028-orders-0_0_8.md` under the maintainer's spec-renumbering pass between rev1 and rev2; the archived filter spec became `docs/SPECS/spec-027-filters-0_0_8.md` in the same pass.
- **rev5** — the maintainer confirmed no further rename: the card stayed at its `028` name and moved from `WIP-ALPHA-028-0.0.8` to `DONE-028-0.0.8` at Slice 5.

## Decision 2 — Subpackage layout and public export surface

Spec: [Decision 2 — Subpackage layout and public export surface][spec-028-d2].

### Justification (moved from the spec)

- The subsystem's surface is large enough (five `__all__` symbols plus the advanced/internal symbols enumerated in the three-tier contract above) that a flat module would be awkward to read; matches the filter side's five-file layout exactly so future maintainers see one shape across both subsystems.
- The target package layout in [`docs/TREE.md`][tree] already names the directory; this card flips it from `[alpha]` to on-disk without renaming.
- The mirror partner is `tests/orders/` (new tree) — **7 files total** per N4 of the rev-1 adversarial review: 1 `__init__.py` shell + 4 mirror test files (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`) + 1 phase-2.5-binding-pass test (`test_finalizer.py`) + 1 cross-card composition test (`test_composition.py`, Slice 6). Slice 1-3 land the shell + 4 mirror + `test_finalizer.py` (6 files); Slice 6 adds `test_composition.py` (7th).
- Subpackage-scoped re-export matches how `AggregateSet` will land at `django_strawberry_framework/aggregates/__init__.py` in `0.1.3`. The five sibling Layer-3 subpackages line up cleanly without each one bloating the top-level `__all__`.
- The shared `LazyRelatedClassMixin` lives in the neutral [`django_strawberry_framework/sets_mixins.py`][sets-mixins] (the set-family home it was extracted to per rev4 H1; it originally shipped under `filters/base.py` in `DONE-027-0.0.8`); duplicating it under `orders/base.py` would silently bifurcate the resolution behavior if a future maintainer fixes one copy and forgets the other. Sibling import keeps both subsystems honest to one resolution algorithm.

### Alternatives considered (and rejected)

- **Flat `django_strawberry_framework/orders.py` single-file module.** Rejected: the surface is too large; review legibility suffers; symmetry with the filter side's five-file layout breaks.
- **Top-level public re-export (`from django_strawberry_framework import OrderSet`).** Rejected: the surface is opt-in for consumers who actually use ordering; widening the top-level `__all__` for every consumer (including the optimizer-only ones) creates churn and a longer Index in `docs/GLOSSARY.md`.
- ~~**Move `LazyRelatedClassMixin` to a new `django_strawberry_framework/utils/lazy_class.py` shared module** as deferred work.~~ **Obsolete per H1 of the rev-3 adversarial review** — the move is already done: the neutral shared home is [`django_strawberry_framework/sets_mixins.py`][sets-mixins], which carries both [`LazyRelatedClassMixin`][sets-mixins] and [`ClassBasedTypeNameMixin`][sets-mixins] for the set family (filters / orders / aggregates / fieldsets). `orders.base` imports the mixin from `sets_mixins`, `orders.sets.OrderSet` inherits `ClassBasedTypeNameMixin` from `sets_mixins`, and `orders.inputs._input_type_name_for()` delegates to `orderset_class.type_name_for()` (which the mixin supplies). The rejected-alternative prose from earlier revisions is left here as a historical breadcrumb but no longer reflects the architecture.

### Changes this Decision underwent

- **rev2 H1** — the symmetric `OrderSet.apply(...)` dispatcher was dropped as YAGNI; the `sets.py` bullet, Decision 8, the implementation-plan table, and DoD item 4 were all updated together.
- **rev2 M3** — `INPUTS_MODULE_PATH` and `_input_type_name_for` were hoisted from the filter side verbatim into the `inputs.py` bullet.
- **rev2 M9** — `_helper_referenced_ordersets` was moved from the `inputs.py` bullet to `orders/__init__.py`, matching the filter side's `filters/__init__.py::_helper_referenced_filtersets`.
- **rev2 N4** — the `tests/orders/` file count was harmonized at seven across Decision 2, Decision 13, and DoD item 11.
- **rev3 N-new-2** — the ledger's placement rationale was rewritten from an import-dependency-avoidance argument to a locality argument, because `orders/__init__.py` already imports from `inputs.py`, so the import dependency exists either way. Same outcome, honest rationale.
- **rev4 H1** — `LazyRelatedClassMixin` was repointed from `filters/base.py` to the neutral `django_strawberry_framework/sets_mixins.py`, which also supplies `ClassBasedTypeNameMixin` for the `{cls.__name__}InputType` convention.
- **rev4 N2** — `apply_async`'s return annotation was corrected from `Awaitable[QuerySet]` to `QuerySet` in the `sets.py` bullet and four other sites.
- **rev6 H4** — the export contract was made precise as three tiers, and the dead `from .factories import OrderArgumentsFactory` re-export was removed from `orders/__init__.py` so the factory is reached through `django_strawberry_framework.orders.factories`, exactly as the filter side reaches `FilterArgumentsFactory`. `OrderSetMetaclass` stayed in `__all__` for one-for-one parity with `FilterSetMetaclass`. Nothing imported the factory from the entry point, so the removal was non-breaking.

### Claims this Decision may no longer make

Measured against `HEAD` by the `028` cycle's pre-dispatch verification. Each is Slice 3's to correct in the spec; none is corrected here.

- **`sets.py` ships `check_permissions` on `OrderSet`.** It shipped in `11d9fbe0` and was deliberately removed in `9e864f59`, which rewrote the module docstring from "the `check_permissions` instance method + the classmethod pipeline" to "the classmethod permission pipeline" in the same diff. At HEAD `grep -rn 'def check_permissions' django_strawberry_framework/` returns exactly one hit, `filters/sets.py::FilterSet.check_permissions`.
- **`RelatedOrder`'s direct base is `LazyRelatedClassMixin`.** At HEAD `RelatedOrder` derives from `sets_mixins.py::RelatedSetTargetMixin` (itself a `LazyRelatedClassMixin` subclass), which owns `_bind_owner` / `_resolved_target` / `_set_target`.

### Corrections this Decision received after ship

Written by the `028` cycle's Slice 3 (`docs/builder/bld-slice-3-028-spec_reconciliation.md`), which rewrote [Decision 2][spec-028-d2] to state `HEAD`'s contract. What the Decision used to claim, what it says now, and why the shipped shape is the right one:

- **`sets.py` ships a `check_permissions` instance method.** It shipped in `11d9fbe0` and was deleted in `9e864f59`; the same diff rewrote the module docstring from "the `check_permissions` instance method + the classmethod pipeline" to "the classmethod permission pipeline", so the deletion was deliberate, not an oversight. The Decision now names the inherited classmethod pipeline only. **Why the deletion is right:** the delegate existed for cookbook call-shape compatibility, reading an input parked on `self._input_value` and forwarding to the classmethod. It had no caller in the package, no test that exercised it through a real resolver, and it required the instance to carry mutable per-request state purely so a second spelling of the gate walk could exist. One entry point means the active-input-only scope cannot be bypassed by reaching for the other one.
- **`RelatedOrder`'s direct base is `LazyRelatedClassMixin`.** At `HEAD` it is [`sets_mixins.py::RelatedSetTargetMixin`][sets-mixins], itself a `LazyRelatedClassMixin` subclass, which owns `_bind_owner` / `_resolved_target` / `_set_target`. **Why:** the target-binding plumbing was identical on both set families and the intermediate class is where it became single-sited; the Decision's normative claim (the mixin is shared through the neutral module, never duplicated into `orders/base.py`) is unchanged and is in fact more true than when it was written.
- **`inputs.py`'s helpers are order-side mechanics.** `FieldSpec`, `build_input_class`, `_input_type_name_for`, and `_iter_orderset_subclasses` are one-line aliases of `utils/inputs.py::GeneratedInputFieldSpec` / `::build_strawberry_input_class` / `::set_input_type_name` / `::iter_set_subclasses`, and `materialize_input_class` / `clear_order_input_namespace` are thin wrappers over `::make_set_input_namespace`. **Why the aliases were kept rather than the call sites rewritten:** the order-side names ARE the contract — [Decision 9][spec-028-d9]'s lifecycle clauses, `registry.clear()`, and the test suite all address the subsystem through them — so keeping them as the addressable surface preserved every spec-named symbol while collapsing two implementations into one. That is why the relocation is not a compatibility break, and why the spec had to be corrected about *where the mechanics live* rather than about *what resolves*.
- **`registry.clear()` clears the two ledgers as two separate blocks, one per module.** The two-ledger separation survives; the mechanism is now two `register_subsystem_clear` rows (owners `orders.input_namespace` with `before_bind=True`, and `orders.helper_references`). See this file's Decision 9 entry for why the registration seam replaced the block layout.

## Decision 3 — Five-layer port plus a deferred Layer 6

Spec: [Decision 3 — Five-layer port plus a deferred Layer 6][spec-028-d3].

### Justification (moved from the spec)

- The cookbook's five-layer architecture is proven (the working reference per [`START.md`][start]); reinventing it would burn schedule for no architectural gain.
- The Strawberry adaptation at Layer 5 reuses the shipped filter subsystem's shape exactly — the lazy-resolution + module-globals materialization contract is one shape, not two.
- Leaving Layer 6 out of the pipeline is correct because no consumer surface needs an implicit `OrderSet`: every field that takes ordering resolves it from a declared `Meta.orderset_class` per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface). Designing an auto-generation path would invent machinery for a hypothetical caller.

### Alternatives considered (and rejected)

- **Design Layer 6 fresh mirroring the filter side's `_dynamic_filterset_cache`.** Rejected: no consumer surface needs it, and the connection field resolves ordering from the declared sidecar instead per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
- **Duplicate `LazyRelatedClassMixin` into `orders/base.py`.** Rejected per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) — silently bifurcating the resolution behavior is a maintenance hazard.
- **Borrow the cookbook's `OrderDirection` enum** (four-member: `ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT`) instead of strawberry-django's six-member `Ordering` enum. Rejected per [Decision 5](#decision-5--ordering-enum-and-argument-shape) — the `_DISTINCT` members conflate a direction with a partition, the to-many fan-out they addressed is prevented by row-preserving aggregate ordering per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface), and NULLS positioning is more broadly useful as a leaf-field direction.

### Changes this Decision underwent

- **rev2 H3** — the reviewer's claim that the package diverged from the cookbook on the `"__all__"` branch was checked against `AdvancedOrderSet.get_fields` and found incorrect; the parity claim was kept, with the verifying citation moved inline.
- **rev2 N8** — proxy-model and multi-table-inheritance semantics for `"__all__"` were spelled out.
- **rev4 B4** — `"__all__"` was corrected from "excludes relations entirely" to the column-backed expansion that INCLUDES forward FK / OneToOne columns, because the cookbook's `get_concrete_field_names` gates on `hasattr(f, "column")`.
- **rev4 M5** — the abstract-model claim was corrected: `_validate_meta` does not inspect `model._meta.abstract`, so abstract-model `OrderSet` targets are undefined for `0.0.8` rather than rejected.
- **rev4 H1** — Layer 2's home moved to the neutral `sets_mixins.py` (see Decision 2).

### Claims this Decision may no longer make

Measured against `HEAD` by the `028` cycle's pre-dispatch verification. Each is Slice 3's to correct in the spec; none is corrected here.

- **Layer 5's `OrderArgumentsFactory._ensure_built` and `_build_class_type` produce the input classes.** Both names have zero occurrences under `orders/` at HEAD: the BFS lives on the shared `GeneratedInputArgumentsFactory` base and the subclass declares `_build_input_triples` plus class-level configuration.
- **`FieldSpec`, `build_input_class`, and `_input_type_name_for` are order-side mechanics.** At HEAD they are one-line aliases of `utils/inputs.py::GeneratedInputFieldSpec` / `::build_strawberry_input_class` / `::set_input_type_name`; `materialize_input_class` and `clear_order_input_namespace` are thin wrappers over `utils/inputs.py::make_set_input_namespace`.
- **The metaclass collects declarations and guards expansion locally via `cls.__dict__`.** Collection is `sets_mixins.py::collect_related_declarations`; the Layer-4 cache and guard are `::expanded_once` / `::should_cache_expansion` plus a class-level `SetLifecycleAttrs`.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle.

- **Layers 2, 3 and 4 name local mechanisms that moved to the shared substrate.** Layer 2's resolution reaches `RelatedOrder` through `RelatedSetTargetMixin`; Layer 3's declaration collection is [`sets_mixins.py::collect_related_declarations`][sets-mixins] (MRO-respecting, current class overriding its bases); Layer 4's cache and re-entry guard are `::expanded_once` / `::should_cache_expansion` reading slots named by a class-level `SetLifecycleAttrs`. The slot NAMES `_expanded_fields` / `_is_expanding_fields` survive at `HEAD` and the Decision still names them; what changed is that the guard logic is one implementation addressed through each family's own slot names rather than a `cls.__dict__` idiom written twice. **Why that matters to the reader:** a future reviewer looking for the cycle-breaking logic in `orders/sets.py` will not find it there, and the old text sent them to the wrong file.
- **Layer 5 names `_ensure_built` and `_build_class_type` as the producers.** Both have **zero** occurrences under `orders/` at `HEAD`: the BFS lives on `utils/inputs.py::GeneratedInputArgumentsFactory` and `OrderArgumentsFactory` supplies `_build_input_triples` plus class-level configuration. These two are the only D5-class names that are **gone rather than relocated** — there is no `orders.*` alias for either, because they were internal to the walk that moved. The Decision now describes the subclass-plus-shared-base split, and additionally records that the shared base walks a FIFO queue where the cookbook's order factory used LIFO (same class set for a finite graph, deterministic order aligned with the filter side).
- **Layer 5's materialization attribution was wrong about which layer owns it.** The old text had the factory materializing each input class as a module global. At `HEAD` the factory deliberately does NOT: it caches built classes at class level and the finalizer's phase-2.5 subpass 4 reads `factory.input_object_types` and calls `materialize_input_class`. **Why the split is right:** materialization is a lifecycle event whose ordering relative to `strawberry.Schema(...)` is load-bearing ([Decision 6][spec-028-d6]), and a factory that wrote module globals as a side effect of being constructed would make that ordering depend on where a caller happened to instantiate it.
- **The quoted `Meta.fields = "__all__"` helper expression was the weaker of two guards.** The spec quoted `hasattr(f, "column") and not getattr(f, "many_to_many", False)`. `HEAD`'s `orders/inputs.py::_get_concrete_field_names_for_order` reads `getattr(f, "column", None) is not None and not getattr(f, "many_to_many", False)`. **Why the shipped version is stronger, and why this is a real correction rather than a cosmetic one:** Django's virtual `GenericRelation` and `GenericForeignKey` descriptors also expose `column`, set to `None`. Under `hasattr` they pass the test and become order leaves, producing an `OrderBy` against a field with no database column — the same class of malformed leaf the Decision already documents for the bare M2M case, arriving through a second door the Decision did not notice. Testing that the column is a real column shuts both. The code's own docstring carries the reason, so the spec was the only place stating the weaker rule. Worker 0's pre-dispatch verification confirmed the `many_to_many` clause and did not compare the first half, which is how a two-clause expression came back "verified" while one clause was wrong.

## Decision 4 — Upstream-primitives parity floor

Spec: [Decision 4 — Upstream-primitives parity floor][spec-028-d4].

### Justification (moved from the spec)

- The parity floor matches what both upstreams ship as `0.0.8`-equivalent surfaces; downgrading below it would leave the package unable to express a query the upstreams accept.
- Leaving DISTINCT ON, auto-generated ordersets, and the decorator surfaces out narrows the cut without compromising the parity argument.

### Alternatives considered (and rejected)

- **Ship `OrderSequence` for explicit tie-breaker control.** Rejected per [Decision 5](#decision-5--ordering-enum-and-argument-shape) — redundant with positional list-element ordering.
- **Ship DISTINCT ON via the cookbook's `apply_distinct` port.** Rejected per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface) — the to-many fan-out it addresses is prevented by row-preserving aggregate ordering, without a PostgreSQL-native partitioning surface.
- **Ship Layer 6 auto-generation.** Rejected — no consumer surface needs it.

### Changes this Decision underwent

- **rev2 N2** — the `Verified in upstream` block from the KANBAN card body was inlined verbatim so this Decision is self-contained.

## Decision 5 — `Ordering` enum and argument shape

Spec: [Decision 5 — `Ordering` enum and argument shape][spec-028-d5].

### Justification (moved from the spec)

- The six-member `Ordering` enum is the most useful surface for the package's `0.0.8` audience: `NULLS_FIRST` / `NULLS_LAST` positioning is broadly applicable across every backend Django supports, while the cookbook's `DISTINCT` modifiers are PostgreSQL-specific (the cookbook's [`_apply_distinct_emulated`][upstream-cookbook-orderset] Window-function fallback works on other backends but the `DISTINCT ON` mental model is PostgreSQL-native).
- The list-shaped argument (NOT a sibling singular `order:` argument like strawberry-django ships) is sufficient — a list with one element produces the same SQL as a singular variant, so two arguments would be redundant. The package's `0.0.8` audience expects one argument shape per capability.
- The Python attribute name on the resolver is `order_by` (Strawberry's auto-camel-case translates to `orderBy:` on the GraphQL surface); the module-level constant in `factories.py` is `ORDER_BY_ARG = "orderBy"` (the GraphQL surface name).
- `Ordering.resolve(field_path)` returns an `OrderBy` expression (via `F(...).asc/desc(nulls_first=...)`) rather than a bare string with `-` prefix because the bare-string form cannot express NULLS positioning. The `get_flat_orders` port from the cookbook is adapted to collect `OrderBy` expressions instead of bare strings; `queryset.order_by(*expressions)` accepts both forms, so the change is transparent to the queryset.

### Alternatives considered (and rejected)

- **Ship the cookbook's four-member `OrderDirection`** (`ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT`). Rejected per [Decision 4](#decision-4--upstream-primitives-parity-floor) — the `_DISTINCT` members are reference-only (see [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface)), and NULLS positioning is more broadly useful.
- **Ship both a singular `order:` argument AND a list `ordering:` argument** (matching strawberry-django's two-constant module). Rejected — redundant; a list with one element is the same SQL.
- **Ship `OrderSequence` for explicit tie-breaker control** (per strawberry-django's per-field sequence descriptor). Rejected — the list's element order IS the tie-breaker; positional control is more discoverable than a separate descriptor field.
- **Use bare-string Django ORM expressions (`["-name", "shelf__code"]`)** instead of `OrderBy` expressions from `F(...).asc/desc(nulls_first=...)`. Rejected — bare strings cannot express NULLS positioning; the `OrderBy` expression form is required.

### Changes this Decision underwent

- **rev2 M4** — the `Ordering.resolve()` example gained the missing `from django.db.models.expressions import OrderBy` import and a comment recording that Django's sentinel for "no NULLS clause" is `None`, not `False`.
- **rev4 B1** — the helper's contract became the *element* type, with resolvers wrapping as `list[order_input_type(OrderSet)] | None`; Decision 5, Decision 11, every User-facing API example, DoD item 7, and the test plan were updated together.
- **rev4 B3** — the NULLS-positioning example and live test were retargeted from `Book.description` (which does not exist) and `Book.title` (non-null) to `Book.subtitle`, the model's only `TextField(blank=True, null=True)`.
- **rev4 H4** — the composition example's enum literal was corrected to lower-case `available`, matching the `TextChoices` stored DB values the package's choice-enum generation exposes.

### Claims this Decision may no longer make

Measured against `HEAD` by the `028` cycle's pre-dispatch verification. Each is Slice 3's to correct in the spec; none is corrected here.

- **"the module-level constant in `factories.py` is `ORDER_BY_ARG = "orderBy"`".** The constant has never existed in any `.py` in this repository: `git log --oneline -S'ORDER_BY_ARG' --all` hits only the two spec-draft commits (`649a813a`, `c8be7ec9`) and checkpoint refs. Nothing needs it — Strawberry derives the `orderBy` GraphQL argument name from the resolver's `order_by` parameter. The spec's `## Borrowing posture` block still asserts it and is Slice 3's to correct.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle.

- **The `Ordering.resolve` code example diverged from `HEAD` twice.** The example branched on `if "ASC" in self.name` — a substring test — and carried a long comment about whether `F` and `OrderBy` should be imported locally or at module top, "showing both for copy-paste safety". At `HEAD` both imports are at module level and the discrimination is a property, `Ordering.is_ascending`, returning `self.name.startswith("ASC")`. **Why the prefix test is right and the substring test was a latent bug:** every current member happens to start with its direction, so the two agree today. A future member embedding `ASC` elsewhere in its name — `DESC_THEN_ASC`, a hypothetical collation variant — would classify as ascending under the substring test and produce the opposite ordering, silently. The property's own docstring states the reason; the spec's example would have taught a re-implementer the fragile form.
- **`is_ascending` has a second consumer the Decision named nowhere.** [`orders/sets.py::OrderSet._resolve_order_expressions`][orders-sets] reads it to choose `models.Min` for an ascending to-many term and `models.Max` for a descending one. **Why that is worth stating in the spec rather than left to the code:** it is the reason the discrimination is a property at all. Two copies of "is this ascending?" — one in `resolve`, one in the aggregate pick — could drift, and the failure mode of drift is not an error but a to-many term ordered by the wrong end of its child range, which no type checker and no smoke test would catch. The single source is a correctness decision, not a tidiness one.
- **The portability note the enum's docstring carries was not in the spec.** A bare `ASC` / `DESC` over a nullable column defers NULL placement to the backend (SQLite first on `ASC`, PostgreSQL / MySQL last), so the NULL partition and a connection's page boundaries over a nullable column differ across databases, while cursor stability within one backend is unaffected. Stated in the spec now because it changes which enum member a consumer should reach for.

## Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering

Spec: [Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering][spec-028-d6].

### Justification (moved from the spec)

- Same phase, same seam, same four-subpass discipline as the **shipped** filter side — symmetry across the two sibling Layer-3 subsystems makes the finalizer's intent legible. A future maintainer reading `finalize_django_types` sees `_bind_filtersets()` then `_bind_ordersets()` and understands the pattern; a future Aggregation card adds `_bind_aggregates()` at the same seam.
- The four-subpass ordering closes the same `_owner_definition` race the filter side closed in rev8: if `BookOrder.shelf = RelatedOrder("ShelfOrder")` and `BookType` is iterated before `ShelfType` in the binding loop, the naive single-subpass call to `BookOrder.get_fields()` would expand `ShelfOrder` before its `_owner_definition` is set. The four-subpass ordering binds every owner first, then expands.
- **The orphan-before-materialize ordering is load-bearing**, not arbitrary. Materializing first then orphan-validating would leave half-materialized input classes in the inputs-module namespace AND half-populated entries in `OrderArgumentsFactory.input_object_types` whenever the orphan check raises; the next `finalize_django_types()` call (after the consumer fixes the orphan) would then see stale ledger entries and either skip re-materialization for entries that should rebuild OR raise a name-collision error for the legitimate retry. Inverting the order keeps both ledgers empty until every gate has passed.
- The `registry.clear()` co-clear keeps the test-fixture reload pattern from [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`][fakeshop-test-library-reload] working unchanged.

### Alternatives considered (and rejected)

- **Single-subpass binding** (iterate `DjangoType`s once, calling `bind_owner` + `get_fields` + `materialize` in one loop body). Rejected per the rev8 H1 lesson — the `_owner_definition` race is real and the four-subpass discipline closes it.
- **Bind ordersets at type-creation time (in `DjangoType.__init_subclass__`)** instead of at finalize. Rejected — relation targets may not be registered yet at type-creation time (definition-order independence); finalize is the only point where every type is known.
- **Materialize BEFORE orphan-validate** (the order spec-027 rev8 H1 *prescribed* but the shipped code rejected). Rejected — leaves stale `_materialized_names` ledger entries and stale `OrderArgumentsFactory.input_object_types` entries on every orphan-validation failure, causing the next finalize attempt to mis-fire after the consumer fixes the orphan. The shipped filter side's choice (orphan-validate first) is the right shape; this card preserves it.
- **Skip the orphan-validation step.** Rejected — without it, an orphan `order_input_type(StandaloneOrder)` reference would surface as a cryptic `LazyType.resolve_type` `KeyError` at `strawberry.Schema(...)` time, well after the resolver-declaration site. Failing loud at finalize names the bug at the right location.

### Changes this Decision underwent

- **rev2 B1** — the subpass order was corrected from the prescribed `bind -> expand -> materialize -> orphan-validate` to the shipped `bind -> expand -> orphan-validate -> materialize`. Orphan-validate before materialize is load-bearing: it leaves no stale ledger entries when an orphan check raises, so a re-run after the consumer fixes the orphan starts clean. The Slice-1 checklist, DoD item 10, and the test plan were updated with it.
- **rev4 H2** — subpass 1 was expanded into three named checks, with first-bind model compatibility pinned non-optional. Without it a `BookOrder` wired onto `BranchType` would build a valid-looking `Book`-field input and apply those paths to a `Branch` queryset, producing a late `FieldError` instead of a finalize-time `ConfigurationError`. `test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` was added to pin it.

### Claims this Decision may no longer make

Measured against `HEAD` by the `028` cycle's pre-dispatch verification. Each is Slice 3's to correct in the spec; none is corrected here.

- **Subpass 4 calls `_ensure_built` / `_build_class_type`.** See Decision 3's entry: neither name exists under `orders/` at HEAD.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle.

- **`_bind_ordersets()` was described as a four-subpass helper mirroring `_bind_filtersets()`.** At `HEAD` both delegate to one shared driver, [`types/finalizer.py::_bind_sidecar_sets`][finalizer], configured by a `_SidecarBindingSpec` naming the family's `Meta` key, owner-bind function, expansion function, helper ledger, factory class, materializer, and orphan-error formatter. **Why the shared driver is the right shape and why the old wording was actively misleading:** the Decision's load-bearing claim is about subpass ORDER — owners bound before any expansion, orphan validation before materialization so a failure leaves no half-built ledger. "Mirroring the shipped implementation" is a claim that two implementations agree, which is exactly the claim that rots; a shared driver makes the order structurally identical instead. The old wording invited a maintainer to fix a subpass-order bug on one side only.
- **The shared driver carries a subpass the order side opts out of.** `_bind_sidecar_sets` has a filter-only subpass 2.5 (unregistered-related-target and GlobalID-strategy audits) that the order spec passes as `post_expand_audit=None`. **Why the order side genuinely does not need it:** the filter side's audit exists because a related branch's visibility scoping runs the target type's `get_queryset`, so an unregistered target makes the branch unfulfillable; ordering never re-derives a child visibility queryset ([Decision 8][spec-028-d8] step 4) and never consults Relay shape, so neither audit has anything to check. Recording the opt-out explicitly matters because "four subpasses" and "the driver runs five" would otherwise read as a contradiction.
- **The closing `registry.clear()` sentence described the retired shape** — see this file's Decision 9 entry.

## Decision 7 — `Meta.orderset_class` promotion gate

Spec: [Decision 7 — `Meta.orderset_class` promotion gate][spec-028-d7].

### Justification (moved from the spec)

- Cross-subsystem invariant pinned in [`docs/GLOSSARY.md`][glossary] ([Cross-subsystem invariants][glossary-cross-subsystem-invariants] — "Deferred `Meta` keys are accepted only when their subsystem applies them end-to-end. This rule resolves entirely at `1.0.0`."); applies to every Layer-3 sidecar.
- Half-promoting (accepting the key but no-oping on it) is the worst-of-both: consumers cannot tell whether their order declaration is doing anything; debug surface is hidden.
- The promotion is a one-line change at [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] (`"orderset_class"` moves to `ALLOWED_META_KEYS`); the validator at `_validate_meta` already gates on `ALLOWED_META_KEYS | DEFERRED_META_KEYS`.

### Alternatives considered (and rejected)

- **Promote `Meta.orderset_class` early in Slice 1 before binding is wired.** Rejected: silently accepting a key whose effect doesn't exist is a maintenance hazard.
- **Keep the key in `DEFERRED_META_KEYS` until `DjangoConnectionField` ships in `0.0.9`.** Rejected: the connection field is the second consumer; root-list resolvers can call `OrderSet.apply_sync(...)` themselves in the meantime, and the live HTTP coverage in Slice 4 exercises that path.

### Changes this Decision underwent

- **rev2 N3** — DoD item 9 grew the explicit requirement that `_validate_orderset_class` use a local in-function `from ..orders.sets import OrderSet` import, mirroring the filter side's `_validate_filterset_class`, to dodge the `types -> orders -> types` module-load cycle.

## Decision 8 — Cooperation with filtering, `get_queryset`, and the optimizer

Spec: [Decision 8 — Cooperation with filtering, `get_queryset`, and the optimizer][spec-028-d8].

### Justification (moved from the spec)

- Symmetry with the filter side's apply pipeline (sync/async split, `check_permissions` active-input-only scope, `info.context.request` extraction with `HttpRequest` fallback, `GraphQLError` import path) keeps the two subsystems on one shape. A future maintainer reading both subsystems' apply pipelines sees the same skeleton with minor adaptations.
- The order side's pipeline is genuinely simpler than the filter side's: no operator-bag (no `and_` / `or_` / `not_`), no form validation (no `BaseFilterSet.form.is_valid()` step — the cookbook's `AdvancedOrderSet` doesn't use forms), no related-queryset filter-scope constraint (no `RelatedOrder(queryset=...)` parameter — the cookbook's `RelatedOrder` accepts only `orderset` and `field_name`). The eight-step pipeline reflects this simplification.
- The filter-first-then-order resolver pattern is the canonical SQL shape — `WHERE` clauses narrow the row set, then `ORDER BY` arranges the result. Reversing the order would still produce the same SQL (PostgreSQL / SQLite / MySQL all reorder `WHERE` and `ORDER BY` in the same plan), but the consumer-readable shape (`filter` then `order_by`) makes the intent legible at the resolver site.

### Alternatives considered (and rejected)

- **Re-derive child visibility querysets for nested `RelatedOrder` branches** (mirroring the filter side's H1). Rejected — the order side does not have the see-through-to-hidden-rows vulnerability the filter side has. Ordering by a hidden relation's field does not expose the hidden row's data; it only affects which visible parent rows surface first. The shipped filter subsystem already covers the joinable visibility case via H1; the order side does not need a parallel guard.
- **Apply `OrderSet.apply_*` BEFORE the filter** (`get_queryset` → `Order.apply_*` → `Filter.apply_*`). Rejected — the produced SQL is identical (Postgres / SQLite / MySQL reorder `WHERE` / `ORDER BY` plan), but the resolver-readable shape suffers. The filter-first ordering matches the consumer's mental model.
- **Skip step 6 (`check_permissions`).** Rejected — the cookbook's [`AdvancedOrderSet.check_permissions`][upstream-cookbook-orderset] is a useful surface for consumers who want to gate ordering on user role (`order by name DESC` for staff only); the active-input-only narrowing makes the surface low-noise (gates fire only when relevant).
- **Use bare-string `order_by` arguments (`["-name", "shelf__code"]`)** instead of `OrderBy` expressions. Rejected per [Decision 5](#decision-5--ordering-enum-and-argument-shape) — bare strings cannot express NULLS positioning.

### Changes this Decision underwent

- **rev2 H1** — the `apply(...)` dispatcher was dropped (see Decision 2).
- **rev2 H2** — the optimizer-projection claim was retracted. Neither `optimizer/walker.py` nor `optimizer/plans.py` inspects `queryset.query.order_by`; the user-visible behavior is correct because Django's ORM extends column fetches as needed, which is Django's cooperation and not the package's. Order-aware projection augmentation was placed explicitly out of scope for `0.0.8`, and `test_library_books_order_preserves_optimizer_cooperation`'s narrative was rewritten to describe what the test actually pins.
- **rev2 H4** — the position-side-channel leak was acknowledged in step 4: ordering by a hidden related column changes the *position* of visible parent rows based on data the user cannot read, so a determined consumer can infer the relative ordering of hidden rows by diffing two queries. The leak was intentionally accepted for `0.0.8` (low bandwidth, no value disclosure) with the closing design deferred.
- **rev2 M1**, **rev3 R1** — the pipeline's step count was corrected from seven to eight in the body, then again in the justification list where the stale count survived the first sweep.
- **rev3 N-new-1** — the H4 deferral was decoupled from connection-aware optimizer planning: the two are orthogonal, and pinning them to one cohort risked a future reader believing the deferral was already scheduled.
- **rev4 H3** — relation-level permission dispatch was specified as active-branch double-dispatch mirroring the filter side's `_run_permission_checks` verbatim, deduped per `(OrderSet class, method name)`. Four package tests and one live HTTP test were added, and the live-test count went from 13 to 14.
- **rev4 N1** — `GraphQLError` was un-linked from the `configurationerror` glossary anchor and its canonical import path (`from graphql import GraphQLError`, NOT `strawberry.exceptions`) named inline.
- **rev4 N2** — `apply_async`'s annotation was corrected to `-> QuerySet` (see Decision 2).
- **rev2 N7**, then **rev7 B1** — the async permission-hook contract was written twice. The rev2 note claimed `apply_async` does NOT wrap `check_*_permission` hooks in `sync_to_async`; the shipped code DOES wrap the permission pass, so rev7 rewrote both the Decision and the note to the shipped behavior: the request resolves synchronously, `_run_permission_checks` dispatches through a thread-sensitive sync boundary so a hook issuing a blocking ORM read does not block the event loop, and parsing plus `queryset.order_by(...)` stay unwrapped as pure construction.
- **rev7 H2** — the "Tests pin the contract" list was reconciled to the tests that actually shipped, and two never-shipped test names were relabelled as documented-not-dedicated-test behaviors.

### Claims this Decision may no longer make

Measured against `HEAD` by the `028` cycle's pre-dispatch verification. Each is Slice 3's to correct in the spec; none is corrected here.

- **`await sync_to_async(cls._run_permission_checks, thread_sensitive=True)(input_value, request)` is the literal dispatch.** At HEAD `OrderSet.apply_async` calls `await run_in_one_sync_boundary(cls._run_permission_checks, input_value, request)` from `utils/querysets.py`. The behavioral claim (one thread-sensitive boundary around the permission pass) survives; the named mechanism does not.
- **`_run_permission_checks`, `_request_from_info`, `_active_permission_field_paths`, `_iter_active_related_branches`, `_invoke_permission_method`, `_extract_branch_value`, and the `_fired` dedup map are order-side members.** All live on `sets_mixins.py::ActiveInputPermissionMixin` (delegating to `utils/permissions.py::invoke_permission_method`); `OrderSet` inherits them and configures via a class-level `ActiveInputPermissionAttrs`.
- **The gate's only failure mode is a `GraphQLError` denial.** At HEAD `utils/permissions.py::invoke_permission_method` runs the gate's return through `reject_async_in_sync_context` and raises `SyncMisuseError` for an `async def check_<field>_permission`, because an un-awaited coroutine is truthy and an intended denial would otherwise become an authorization bypass. The spec names no such rejection.
- **`tests/orders/test_sets.py::test_orderset_check_permissions_instance_method_delegates` pins the instance-method delegate.** That test name has zero occurrences anywhere outside the spec.
- **Step 7 applies `queryset.order_by(*expressions)` over `Meta.model`-derived paths.** At HEAD `OrderSet._apply_orderings` calls `_resolve_order_expressions(flat_orders, model=queryset.model)`, so the path resolves against the queryset's model and a model-less `OrderSet` is legal (`test_modelless_orderset_uses_queryset_model_for_to_many_order`, `test_queryset_model_overrides_conflicting_orderset_meta_model`).
- **The `OrderSet` and `RelatedOrder` GLOSSARY entries call out the position side channel.** Neither entry mentions a side channel, a leak, or a position inference.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle. Decision 8 accumulated more post-ship drift than any other, because it is where the order side's runtime behavior is specified and the runtime is what later cards changed.

- **Step 4's GLOSSARY claim was false in exactly one of its two subjects.** It asserted that the `OrderSet` entry and the `RelatedOrder` entry "both call this out" about the position-side-channel leak. At `HEAD` the `RelatedOrder` entry **does** carry a `Position-side-channel note:` paragraph naming the parent-side `check_<branch>_permission` gate as the defense; the `OrderSet` entry carries nothing about it. The spec now names `RelatedOrder` alone. **Why that is the right half to keep:** the `RelatedOrder` declaration is what creates the exposure, so the warning sits where a consumer writes one. The `028` cycle's own pre-dispatch verification reported that *neither* entry mentions it, which is a reminder that a two-subject claim needs two measurements — the finding was half right and would have deleted a true sentence.
- **Step 6 named an instance-method delegate and cited a test that has never existed.** `tests/orders/test_sets.py::test_orderset_check_permissions_instance_method_delegates` had **zero** occurrences anywhere but inside the spec itself. See this file's Decision 2 entry for why the delegate's deletion was right; the phantom test citation is worse than the stale claim, because a reader who greps for it concludes the spec is describing a different repository.
- **Step 6 described only the `GraphQLError` denial path, and the gate now REJECTS an async hook.** [`utils/permissions.py::invoke_permission_method`][utils-permissions] runs the gate's return through `utils/querysets.py::reject_async_in_sync_context`, raising `SyncMisuseError`. **Why rejecting loudly is the only safe behavior, and why this is a security correction rather than an ergonomic one:** the whole ORM pipeline is synchronous — on the async surface it runs inside one `sync_to_async` worker — so an `async def check_<field>_permission` returns a coroutine that is never awaited. A coroutine object is truthy and its `raise` never executes, so a consumer's intended DENIAL becomes a silent ALLOW. That is an authorization **bypass**, not a missed error, and it fails in the direction that grants access. Every sibling authorization seam in the package applies the same guard, which is why the order side inherited it rather than inventing it.
- **Step 6's dedup machinery was attributed to the order side.** `_run_permission_checks`, `_active_permission_targets`, `_active_permission_field_paths`, `_iter_active_related_branches`, `_invoke_permission_method`, `_extract_branch_value`, `_request_from_info`, and the `_fired` map all live on [`sets_mixins.py::ActiveInputPermissionMixin`][sets-mixins]; `OrderSet` inherits them and configures the family's attribute names through a class-level `ActiveInputPermissionAttrs`.
- **Step 6's four cited package tests do not exist**, and their contracts moved with the mechanics. The family-neutral double-dispatch-plus-dedup walk is pinned once at `tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup`; the mixin wiring by `tests/test_sets_mixins.py`, including `::test_permission_facade_methods_are_single_sourced_on_the_mixin`; the order-side residue by `tests/orders/test_sets.py::test_orderset_check_permission_dedups_repeated_list_entries` and `::test_orderset_inactive_input_does_not_resolve_lazy_related_target`. **Why the tests moved and the spec should follow rather than resist:** a contract belongs in the tree that owns the code implementing it, so one test proves it for both families instead of two near-copies drifting. All three of the spec's **live** gate tests do exist and were left named.
- **Step 7 was wrong about the receiver, the metadata root, and the SQL shape.** It said "the instance applies `queryset.order_by(...)`" (it is a classmethod chain through `_apply_orderings`); it described paths derived from `Meta.model` (`HEAD` passes `model=queryset.model`); and it described a direct `order_by` for every term. **Why `queryset.model` is the right root:** `Meta.model` may be absent entirely for a related-only set, or may name a base model while a valid caller applies the set to a concrete descendant carrying additional relations. Inferring from class or binding metadata makes correctness depend on declaration history, and the specific failure it produces is missing a concrete to-many path — which silently reinstates the raw fan-out join the aggregate exists to prevent. Two tests pin it: `test_modelless_orderset_uses_queryset_model_for_to_many_order` and `test_queryset_model_overrides_conflicting_orderset_meta_model` (`ae6ac9ab`).
- **Step 7 gained the pre-validation and the aggregate.** `7000d920` added `utils/relations.py::classify_path` calls in `_expand_meta_fields` and `_resolve_order_expressions`; a path reported as to-many is annotated `Min` / `Max` and ordered by the alias.
- **The `apply_async` paragraph pinned a literal `sync_to_async(..., thread_sensitive=True)` call.** `HEAD` calls `utils/querysets.py::run_in_one_sync_boundary`. **Why the named mechanism matters even though the behavior is identical:** the helper is the package's generic one-boundary primitive, shared by every async surface that must keep a consumer-overridable sync hook off the event loop, so the discipline — ONE worker per resolution, `thread_sensitive=True`, never a per-step hop — cannot drift per subsystem. A spec pinning the literal call invites a maintainer to "optimize" one subsystem's boundary independently. The cited test `::test_orderset_apply_async_runs_check_permission_in_sync_to_async` exists and was left named.

## Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle

Spec: [Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle][spec-028-d9].

### Justification (moved from the spec)

- Per-subsystem module globals match Strawberry's `LazyType.resolve_type` semantics (module-path-only, not object-path) — verified during the filter side's rev2 H1.
- The two Layer-3 subsystems each own their own per-module namespace; collapsing both into the `TypeRegistry` would mix string-keyed input-class entries with model-keyed `DjangoType` entries, weakening the type contract.
- The shared `registry.clear()` entry point keeps the test-fixture reload pattern (the canonical `_reload_project_schema_for_acceptance_tests` fixture at [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`][fakeshop-test-library-reload]) working unchanged — one call clears all three subsystems.
- Sibling Aggregation subsystem (`0.1.3`) will reuse this exact lifecycle shape with `django_strawberry_framework.aggregates.inputs` as a fourth co-cleared namespace.

### Alternatives considered (and rejected)

- **Sidecar `_input_type_registry: dict[str, type]` in `orders.inputs`.** Rejected per the filter side's H1 — Strawberry's `LazyType.resolve_type` cannot reach into a dict.
- **Single shared `_input_type_registry: dict[str, type]` across filter + order subsystems.** Rejected — the namespaces are disjoint by module path; sharing one dict would force the same module path on both subsystems and either confuse `LazyType.resolve_type` (which reads `module.__dict__`) or require a wrapper module that re-exports both subsystems' classes.
- **Skip the `clear_order_input_namespace()` integration with `registry.clear()`.** Rejected — test-fixture reload patterns would leak between test runs.

### Changes this Decision underwent

- **rev2 B2 + B3** — the `registry.clear()` pseudocode was rewritten against the actual `TypeRegistry` field declarations: the phantom `_types_by_model` / `_primary_types` names were replaced by the real `_types` / `_primaries` / `_models` / `_enums` / `_definitions` / `_pending` / `_finalized`, and the last block's `except ImportError: return` became `except ImportError: pass` + `else:` so all four try/except blocks share one shape.
- **rev4 M1** — `_materialized_names` was retyped `dict[str, type]` storing the materialized *input class*, not the source `OrderSet`; source-class collision detection lives separately in `OrderArgumentsFactory._type_orderset_registry`, mirroring the filter side's split.
- **rev4 B2** — the clear lifecycle was rewritten to match the filter side verbatim, and the parking rule was made explicit: already-materialized module globals stay in `orders.inputs.__dict__` because `materialize_input_class` overwrites the global via `setattr` on the next finalize, while `delattr` would break held `strawberry.lazy(...)` LazyTypes in consumer modules whose autouse-reload fixture did not also reload the holder. The test plan and DoD items 6 + 10 were widened to assert the broader reset set and to stop expecting module-global deletion.
- **rev7 M4** — the Slice-2 implementation-plan row's "clears module globals" claim was corrected to the parked-globals contract, and `_field_specs` was added to the documented clear set.

### Claims this Decision may no longer make

Measured against `HEAD` by the `028` cycle's pre-dispatch verification. Each is Slice 3's to correct in the spec; none is corrected here.

- **`TypeRegistry.clear` carries `try: from .orders.inputs import clear_order_input_namespace / except ImportError: pass / else: ...` blocks.** At HEAD the seam is `registry.py::register_subsystem_clear` / `::iter_subsystem_clears`: `orders/inputs.py` registers `clear_order_input_namespace` (owner `orders.input_namespace`, `before_bind=True`) and `orders/__init__.py` registers `_clear_helper_referenced_ordersets` (owner `orders.helper_references`), both at import time, and `TypeRegistry.clear` replays `for clear in iter_subsystem_clears(): clear()` with no `except ImportError` guard for either subsystem. `orders/__init__.py`'s own comment records that the older shape predates the registration seam. The two-separate-blocks rationale is still right in intent — the helper ledger clears through its own row and `clear_order_input_namespace` does not touch it — and wrong in mechanism.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle.

- **The `Import-cycle-safe integration` bullet and its fenced ~59-line `registry.py` block described a shape that no longer exists.** The block pinned four `try: from … import … / except ImportError: pass / else: …` guards inside `TypeRegistry.clear`, two of them the order side's, with a comment explaining that `pass` + `else:` rather than `return` was the "latent-footgun fix" so a future fifth clear phase could not be skipped. At `HEAD` `registry.py` names no subsystem and carries **no** `except ImportError` for any of them: each subsystem announces its own callback at import time via `register_subsystem_clear(clear, *, owner, before_bind=False)` and `clear()` replays them through `iter_subsystem_clears()`.
- **Why the registration seam is right, stated as the three properties the guarded-import chain could not provide.** First, **a rename cannot silently drift**: importing the owner module must resolve the function object before registration succeeds, so renaming `clear_order_input_namespace` breaks at the owner's own import, where a stale reference in `registry.py` would have left the ledger uncleared with nothing failing — and stale generated state surviving a `clear()` is precisely the bug class the whole lifecycle contract exists to prevent. Second, **soft-dependency laziness becomes structural rather than tolerated**: only an imported owner can register, so an unimported subsystem contributes no callback and needs no tolerated-failure branch; the old shape achieved the same outcome by catching an error it expected, which is why it needed a comment explaining that the `except` was not hiding a real problem. Third, **the fifth-clear-phase footgun disappears instead of being defended against**: each phase is its own registered row, not a link in a chain, so nothing can short-circuit a later one and `registry.py` needs no edit at all when aggregates or fieldsets land. `orders/__init__.py`'s own comment records that the guarded-import shape "predates the registration seam".
- **`before_bind=True` is a distinction the old shape could not express.** The order-input namespace row carries it; the consumer-helper ledger row does not. It marks a generated-state reset the finalizer replays before every rebuild, as opposed to a full-lifecycle teardown — one flag where the block layout would have needed a second call site.
- **The subprobe test was placed in the wrong file.** `test_registry_clear_works_without_orders_imported` lives at `tests/orders/test_inputs.py`, not `tests/orders/test_finalizer.py` where the Test plan put it. Its assertion also shifted with the mechanism: it now pins that `registry.clear()` runs cleanly with no order-side callback registered, rather than that a local import inside `clear()` does not raise.
- **The `clear_order_input_namespace()` bullet's closing sentence** described local imports and symmetric `pass` + `else:` blocks inside the helper. `HEAD`'s helper is a thin family wrapper over the heavy clear `utils/inputs.py::make_set_input_namespace` builds for both set families; the partial-load case it defended against cannot arise, because the callback is registered only when `orders.inputs` imports.

## Decision 10 — Version bumps are maintainer-commanded

Spec: [Decision 10 — Version bumps are maintainer-commanded][spec-028-d10].

### Justification (moved from the spec)

- The maintainer clarified that Ordering is a `0.0.8` shipping task, and version bumps should be explicit release actions rather than implicit side effects of a feature card.
- Keeping version edits command-gated prevents a junior implementer from touching `pyproject.toml`, `__version__`, the pinned version test, or release headings while implementing Ordering.
- The historical release-cut postures are useful context in archived specs, but they are not executable instructions for this card.

### Alternatives considered (and rejected)

- **Implicitly bump when the card lands.** Rejected: contradicts the maintainer's command boundary and makes a feature-card checklist mutate release state.
- **Keep a deterministic "last `0.0.8` card owns the bump" check.** Rejected: still encodes an implicit bump. The only valid trigger is the maintainer's explicit version-bump command.

### Changes this Decision underwent

- **rev5** — Decision 10 was rewritten from the historical joint-cut and rolling-patch posture to the maintainer-commanded release boundary; Slice 5 and DoD item 24 lost their version-field work; the KANBAN past-tense body's release sentence was rewritten; and CHANGELOG release-heading promotion became command-gated.
- **rev6 B2** — the version boundary was stated explicitly in the header and here: Ordering shipped *within* `0.0.8` and did not bump toward `0.0.9`; the `0.0.8` version-file values and the `CHANGELOG.md` `__version__` note were set under the maintainer's separate release command, not by this feature card.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle.

- **Three sentences asserted a dated snapshot of files that keep moving.** The Decision said the package's version files "already read `0.0.8`" and that `CHANGELOG.md` carried an `__version__`-is-now-`0.0.8` note under `[Unreleased]`, and closed that release-heading promotion "had not happened as of this spec's writing". At `HEAD` all three are stale: `CHANGELOG.md` carries `## [0.0.8] - 2026-06-03` and no `[Unreleased]` heading at all, and `pyproject.toml` / `__version__` read `0.0.14`.
- **Why the fix is to stop asserting the state rather than to restate it.** The Decision's actual contract is a rule about who may bump — version work is never inferred from card completion — and that rule is timeless. Every sentence reconciling it against "the current repo" was a snapshot with a short half-life, and the `028` cycle found each one wrong in a different way three releases later. The corrected Decision states the boundary (this card shipped inside `0.0.8` and edited no version file; the `0.0.8` values and heading came from separate maintainer commands) and asserts nothing about today's `CHANGELOG.md` or `pyproject.toml`. The build plan flagged one stale sentence; re-derivation found three, which is the same lesson in miniature — a dated claim rots as a family, not one line at a time.

## Decision 11 — `order_input_type(OrderSet)` consumer helper

Spec: [Decision 11 — `order_input_type(OrderSet)` consumer helper][spec-028-d11].

### Justification (moved from the spec)

- Symmetry with the shipped `filter_input_type` is the load-bearing argument — the two helpers are intentionally the same shape so consumers using both subsystems see one mental model. A future maintainer reading the code finds two helpers with one design.
- Eager validation (`TypeError` at call time for a non-`OrderSet`) catches misuse at the resolver-declaration site instead of letting Strawberry surface a more cryptic schema-build-time error.
- The orphan-validation shape closes the same trap the filter side closed in rev5: without it, an `order_input_type(StandaloneOrder)` reference would surface as a `LazyType.resolve_type` `KeyError` at `strawberry.Schema(...)` time, well after the resolver-declaration site.

### Alternatives considered (and rejected)

- **No helper; consumers spell out `Annotated[...]` themselves.** Rejected: ties consumer code to the package's internal module path; bypasses validation; not the package's `Meta`-driven shape.
- **Helper returns `<Name>OrderInputType` directly (a class).** Rejected: the class doesn't exist yet at module-load time — it's materialized later by `finalize_django_types()`. Returning a class at module-load time would force the helper to eagerly run the finalizer, which contradicts definition-order independence.
- **Helper is a method on `OrderSet`: `GalaxyOrder.input_type()`.** Rejected: viable shape, but adds class-method surface to every `OrderSet` for the sake of one call site per resolver. The module-level function form is the smaller import and the more discoverable doc entry — and matches the filter side's helper shape.
- **Defer the helper to `0.0.9`** (let `DjangoConnectionField` accept `orderset_class=` directly). Rejected: `0.0.8` consumers cannot wait for `0.0.9` to expose a working `orderBy:` argument; this card's [Goals][spec-028-goals] item 5 requires a consumer-facing path now.

### Changes this Decision underwent

- **rev4 B1** — the helper's contract became the element type rather than the list type (see Decision 5).
- **rev7 H2** — `test_order_input_type_resolver_wraps_as_list_under_strawberry_schema` was named in an earlier draft and never shipped; the list-wrap SDL shape is exercised by the fakeshop schema's `list[order_input_type(...)]` resolver annotations and the live HTTP order tests instead.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle.

- **The fenced `order_input_type` body was a stale spelling.** The block showed a hand-written function performing its own `issubclass` validation, its own `_helper_referenced_ordersets.add(...)`, and its own `Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]` construction. At `HEAD` the body delegates to [`utils/inputs.py::build_lazy_input_annotation`][utils-inputs], shared with `filters/__init__.py::filter_input_type`, passing the family's expected base, labels, ledger, name formula, and module path. **Why the delegation is right:** the two consumer helpers differed only in five literals, and the parts that were identical are the parts that are subtle — the eager-validation timing, the ledger write for orphan detection, and the ForwardRef form. Two copies of a subtle body is two chances to fix a bug once.
- **Two clauses inside that body are implementation contract and stayed in the spec**, per `docs/builder/BUILD.md` `## Spec rationale extraction`'s carve-out for rationale that changes HOW a thing is built. The runtime-computed name must be passed as the first `Annotated[...]` argument rather than interpolated into a literal, because that is what wraps it as a `typing.ForwardRef` for `LazyType.resolve_type` to resolve against `module.__dict__`; and the ledger write is idempotent because the ledger is a `set` of classes, which is what makes repeated calls safe under PEP 563 re-evaluation. A re-implementer who never reads either sentence writes an annotation Strawberry cannot resolve, or a duplicate orphan record.
- This is the same finding class as Decision 2's relocated mechanics (build-plan finding D5), reaching a Decision that finding did not enumerate.

## Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface

Spec: [Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface][spec-028-d12].

### Justification (moved from the spec)

- Layer 6's machinery would serve a caller that does not exist; the explicit declaration covers every shipped consumer, and a second implicit way to acquire an `OrderSet` beside it is surface without demand.
- The row multiplication that motivated DISTINCT ON is solved by the aggregate ordering without a PostgreSQL-native construct, so no backend needs the cookbook's Window-function emulation path.
- `NULLS_FIRST` / `NULLS_LAST` positioning is the vocabulary a leaf-field direction enum actually needs, and six members is already at the edge of legibility.

### Alternatives considered (and rejected)

- **Ship Layer 6 auto-generation mirroring the filter side's [`django_graphene_filters/filterset_factories.py::_dynamic_filterset_cache`][upstream-cookbook-filterset-factories].** Rejected — no consumer needs it, and inventing the surface would put a second, implicit way to acquire an `OrderSet` beside the explicit declaration.
- **Ship the cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` plus the [`apply_distinct`][upstream-cookbook-orderset] port.** Rejected — the enum shape conflates a direction with a partition, and the row multiplication it was reached for is already prevented.
- **Ship a separate `Meta.distinct = ("category",)` declaration with a `distinct_on:` argument.** Rejected — it buys a PostgreSQL-native partitioning surface (the cookbook's non-PostgreSQL path is a Window-function emulation) for a problem the aggregate ordering already solves, and every `Meta` key is permanent public surface.

### Changes this Decision underwent

- **rev2 O1 + O2** — forward-compatibility previews were added for the then-open `Meta.distinct` shape choice and the then-open Layer 6 path choice.
- **rev3 N-new-3** — the O1 preview's `DEFERRED_META_KEYS` membership claim for `Meta.distinct` / `Meta.distinct_class` was stated as a stable fact; rev3 named the then-current contents and added a staleness caveat.

## Decision 13 — Live HTTP coverage strategy

Spec: [Decision 13 — Live HTTP coverage strategy][spec-028-d13].

### Justification (moved from the spec)

- Mirrors the shipped filter side's coverage strategy per [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 12 — same trees, same split, same coverage-priority rule.
- The live HTTP path exercises the most ORM cooperation (`order_by(...)` interacting with `select_related` / `prefetch_related`) — properties an in-process `schema.execute_sync(...)` test cannot easily capture without significant SQL-shape setup.
- The package-internal `tests/orders/` tree catches edge cases (cycle detection, error shapes, NULLS positioning) the live HTTP path cannot reach without contrived orderset declarations.

### Alternatives considered (and rejected)

- **Skip live HTTP coverage; cover everything via `tests/orders/`.** Rejected per the [`docs/TREE.md`][tree] coverage-priority rule.
- **Cover everything via live HTTP; skip package-internal tests.** Rejected — cycle-detection / error-surface paths are not reachable through normal consumer GraphQL queries.

### Changes this Decision underwent

- **rev2 M2 + M5 + M6 + M7** — Slice 4's live HTTP coverage grew from 10 tests to 13: a flat-shorthand path test (`Meta.fields = ["shelf__code"]` -> `shelfCode:`), a redesigned reverse-FK test that asserts the multiplication instead of seeding one shelf to dodge it, the split of the combined permission test into a denies-for-active / quiet-for-inactive pair so a regression in either half surfaces as a named failure, and the two no-op contract tests.
- **rev3 R2 + R3 + R4** — three count sites still said 10 after rev2's expansion: the Test-plan subsection header, the implementation-plan Slice-4 row (with its line-delta estimate), and Decision 13's own capability list. All three were updated to 13.
- **rev4 H3** — the active-branch relation-level permission gate test took the count from 13 to 14.
- **Slice-4 final verification** — the two no-op tests were combined into one function, `test_library_branches_order_empty_list_and_null_direction_no_op`, so the enumerated capabilities still summed to the pinned count; the quiet-half gate field was substituted from `name` to `city` to dodge a cross-test gate collision; and three tests were pinned as issued via the staff client so the contract under test is not entangled with the permission gate declared permanently on `BranchOrder`.
- **rev7 H2** — the test-plan names were reconciled to the shipped tests, and `test_order_accepts_field_not_in_djangotype_meta_fields` was relabelled as documented behavior rather than a shipped test (a correction rev2's M8 note had already anticipated).

### Claims this Decision may no longer make

Measured against `HEAD` by the `028` cycle's pre-dispatch verification. Each is Slice 3's to correct in the spec; none is corrected here.

- **"14 tests total".** At HEAD `test_library_api.py` carries 15 order tests: the 14 plus `test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication`, a live mixed scalar-plus-to-many-aggregate GROUP BY case the spec names nowhere.
- **`test_library_books_order_by_subtitle_desc_nulls_last`.** Zero occurrences. The NULLS-positioning contract ships parametrized as `test_library_books_order_by_subtitle_null_positioning` (four directions, `DESC_NULLS_LAST` among them), with a second nullable-subtitle contract test at `test_library_choice_enum_and_nullable_subtitle_are_deliberate_http_contracts`.
- **Reverse-FK relation order with denormalized multiplicity asserted.** Retired by `spec-030-connection_field-0_0_9` P1-B: `OrderSet` orders a to-many path by a `Min` / `Max` aggregate so the parent row is not multiplied, and the shipped test asserts `names == ["Alpha", "Beta"]`. The Slice-4 checklist, Decision 12, and the Non-goals bullet carry the correction; four sites still carry the retired contract and are Slice 3's.
- **`test_orderset_check_permission_active_relatedorder_branch_fires_parent_gate`, `..._fires_child_gate`, `test_orderset_check_permission_quiet_for_inactive_field`, and `test_orderset_check_permission_denies_for_active_field` as package tests.** All four return zero occurrences repo-wide. The double-dispatch-plus-dedup contract is pinned once, family-neutrally, at `tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup`; the family wiring at `tests/test_sets_mixins.py`; the order-side residue at `tests/orders/test_sets.py::test_orderset_check_permission_dedups_repeated_list_entries` and `::test_orderset_inactive_input_does_not_resolve_lazy_related_target`. All three live gate tests do exist.
- **`test_registry_clear_works_without_orders_imported` lives in `tests/orders/test_finalizer.py`.** It lives in `tests/orders/test_inputs.py`.

### Corrections this Decision received after ship

Written by Slice 3 of the `028` cycle.

- **The live-test capability list carried the retired JOIN-multiplicity contract** — "reverse-FK relation order with denormalized-multiplicity asserted" — one of the four sites the row-preserving correction never reached. See `## Claims the spec may no longer make` below for the full four-site inventory and why the cross-cohort seam is where this defect class survives review.
- **The bare `(14 tests total)` count.** The number was right for what this card planned and wrong as a description of the file, which had grown two functions and three parametrized rows. The Decision now states 14 as **this card's** functions and points at the [Test plan][spec-028-dod] for the section's 16 / 19. **Why the subject matters more than the digit:** a reader auditing coverage counts what is in the file, finds 16, and concludes the spec is stale — when in fact both numbers are true of different populations. This cycle mis-measured the same census three times for exactly that reason, so every restatement now carries its subject.
- **The `7 files total` claim for `tests/orders/` was correct at `HEAD`** and was left untouched. It was the Test-plan preamble's "Five files mirror the source layout" that disagreed with it, along with [Decision 2][spec-028-d2] and [DoD item 11][spec-028-dod] which both already said seven. Recorded because the build plan listed this as a contradiction without naming which side was right, and three of the four sites needed no edit.

## Non-Decision deliberation

Narration that lived outside the Decisions and left the spec with them.

### The spec's own state model

**rev6 B1** chose one state model. Before it the spec mixed build-plan voice ("does not exist on disk yet", an unchecked checklist) with shipped-state claims (the Status line, the final gate). rev6 declared the spec the final implementation record, ticked the Slice checklist with a completion banner, renamed the former "Current state" section to `Pre-implementation baseline (captured before Slice 1)` with a banner marking it a pre-Slice-1 snapshot, and dated the stale present-tense baseline claims.

**rev6 H3 and rev7 H3** converted raw `path:NN` line references to `path::Symbol` forms across the standing body. rev4 M4 had done the first sweep and rev6 H3 the second, both claiming the revision-history breadcrumbs were exempt; rev7 removed the exemption, converted the breadcrumbs too, and deleted the exemption sentences. The repo convention is not section-scoped.

**rev2 N5** replaced `YYYY-MM-DD` with `<DATE>` across Slice 5, Decision 10, and DoD item 24 so the placeholder reads as "fill this in" rather than risking a literal ship into the changelog. **rev2 N6** made the Slice-5 contingency deterministic by naming a concrete `grep -E 'WIP-ALPHA-[0-9]+-0\.0\.8' KANBAN.md` command.

### The final gate

**rev6 H5** recorded on the Status line that the green full-suite gate was the maintainer-directed assistant pass at the maintainer's explicit `run tests and coverage` request, and put the same reconciliation in DoD items 26 + 28 so the no-local-pytest worker rule and the gate-green claim stopped reading as contradictory. **rev7 M5** corrected that paragraph's "three INDEPENDENT pieces" to "four" after the enumeration had grown to (a)-(d).

The gate closed on the fourth attempt. Two earlier "gate closed" claims were wrong: the original claim, and the round-1 correction's causal diagnosis. The real close was four independent pieces:

- **(a)** the `orders/*` coverage shortfall, closed by 19 focused `tests/orders/` unit tests bringing all five modules to 100%.
- **(b)** five card-owned order-wiring lines with no order-side twin of a test the filter subsystem already had — the two `except ImportError: pass` guards in `TypeRegistry.clear()` and the subpass-2 `except ConfigurationError: raise` re-raise in `_bind_ordersets` — closed by `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules` and `tests/orders/test_finalizer.py::test_phase_2_5_configuration_error_during_expansion_propagates_by_identity`.
- **(c)** four filter async-path lines in `django_strawberry_framework/filters/sets.py`, unreachable from the sync live HTTP client and so earned as net-new unit tests in `tests/filters/` — a `spec-027` source-refactor coverage gap, not a regression from the deliberate filter-test relocation.
- **(d)** three `test_glossary_api.py` failures (`IntegrityError: UNIQUE constraint failed: kanban_boarddockind.key`) from the `_seed_glossary` fixture's plain `.create(key="glossary")` colliding with the glossary data migration's `get_or_create` seed, fixed by making the fixture idempotent.

Only (a) and (b) belonged to this card; (c) and (d) belonged to the filter and kanban/glossary workstreams.

**Both `TypeRegistry.clear()` guards named in (b) are gone at HEAD** — see Decision 9's `### Claims this Decision may no longer make`. The test that pinned them survives, and whether it still pins anything is a live question for the `028` cycle's Slice 2.

### Behaviors documented but deliberately not pinned by a dedicated test

- **rev2 M8, corrected in rev7** — the rev1 review asked for `test_order_accepts_field_not_in_djangotype_meta_fields`, covering an order on columns the `DjangoType` cannot select. The behavior ships as documented behavior in the spec's Edge cases; the test was never shipped. rev2's note claimed it was; rev7 corrected the claim.
- **rev4 M2** — an earlier revision claimed a live HTTP test pinned `orderBy: [{ name: ASC }, { name: DESC }]`. The 13-test plan did not include one, so the edge case became documented behavior covered by package-level parsing and queryset tests.
- **rev7 H2, second half** — `test_order_input_type_resolver_wraps_as_list_under_strawberry_schema` was named in a rev4 draft and never shipped; the list-wrap SDL shape is exercised by the fakeshop schema's `list[order_input_type(...)]` annotations plus the live HTTP order tests.

### Conventions documented for future cards

- **rev2 N9** — the `# noqa: A002` note. `order_by` does not shadow a builtin; `filter` does, hence the suppression on the filter side. `aggregate:`, `order:`, and `search:` will not need it; `input:` would. The note stayed in the spec because it is guidance a future card author would otherwise rediscover; only its provenance citation left.
- **rev4 M3** — `Ordering` was added to every shipped-symbol sweep bullet (`docs/README.md`, `README.md`) so the five public order symbols are listed consistently.
- **rev2 M10** — the duplicated KANBAN / CHANGELOG past-tense paragraph was deduplicated: the CHANGELOG bullet references the KANBAN body as the single source of truth and carries a one-line headline.

## Claims the spec may no longer make

Spec-wide findings that do not belong to one Decision. The bullets below record, per finding, what the spec used to claim and why the shipped shape is right; Slice 3 corrected all of them in the spec, so this is the record of the change, not a work list.

- **The `Status:` line was a build-progress log, not a state.** Rewritten by Slice 1 to state the shipped surface. Its stale "14 live HTTP order tests" count went with it, so the 14-site `14` census the build plan measured is a **13-site** census for Slice 3.
- **`OrderSet.check_permissions` is named in four places** — Decision 8 step 6's parenthetical, Decision 2's `sets.py` bullet, the Borrowing-posture "port verbatim" bullet, and DoD item 4(e). It was deleted post-ship (see Decision 2's entry).
- **`ORDER_BY_ARG = "orderBy"` is asserted in the Borrowing-posture strawberry-django bullet** as well as in Decision 5's justification (now above). It has never existed in any `.py`.
- **Order paths are pre-validated at HEAD.** `7000d920` added `utils/relations.py::classify_path` calls in `OrderSet._expand_meta_fields` (over every `Meta.fields` entry) and `::_resolve_order_expressions` (over every resolved path), each raising `ConfigurationError` naming the path and the model. Two spec claims are falsified: the Edge-case bullet "the framework does not pre-validate the backend's supported expressions", and the `Error shapes` bullet placing the invalid-`Meta.fields` raise at type-creation time — Decision 3 Layer 3 is explicit that the metaclass does not expand, so the raise lands at finalize phase-2.5 subpass 2.
- **The GLOSSARY claims are false in both directions.** Decision 8 step 4 and the Test plan assert GLOSSARY content that is not there (a position side channel; the reverse-FK multiplicity), while the shipped `OrderSet` entry documents three contracts the Doc-updates block does not name: the `Min` / `Max` row-preserving aggregate, the root connection's deterministic pk tiebreaker over the grouped queryset, and the deliberate nested-relation-connection `orderBy:` bypass of window/lateral planning.
- **fakeshop's order graph outgrew the spec.** `examples/fakeshop/apps/library/orders.py` ships seven ordersets (the five named plus `PeriodicalOrder` and `IssueOrder`, the keyset-cursor `orderBy:` substrate); `schema.py` carries eight `Meta.orderset_class` wirings against DoD item 14's six; `orders_genre.py::GenreOrder` declares a second absolute-import-path `RelatedOrder`; `BookOrder.loans` and `ShelfOrder.books` are unnamed by the spec.
- **Tail-section staleness.** The Slice-6 test count contradicts itself three ways (checklist "One", implementation-plan row "1", Status line "two"; HEAD has two); three Key-glossary-reference bullets still read `planned for 0.0.8` as present fact; the pre-archive path `docs/spec-028-orders-0_0_8.md` appears 12 times across 9 lines and DoD item 17's quoted `check_spec_glossary` command would fail as written; the `docs/TREE.md` Doc-updates bullet names a "Test layout going forward" section that no longer exists; the Pre-implementation-baseline `docs/TREE.md` bullet's five-file claim is four at HEAD; Decision 10's closing "had not happened as of this spec's writing" is a dated `CHANGELOG.md` claim a reader will read as current; the Test-plan preamble says five `tests/orders/` files where Decision 2, Decision 13, and DoD item 11 all say seven (seven is correct); and `[fakeshop-test-library-reload]` and `[fakeshop-test-library]` resolve to the same path while the fixture actually lives in `examples/fakeshop/test_query/conftest.py`.

Corrections Slice 3 landed that the pre-dispatch verification did not name, or named wrongly:

- **The row-preserving correction survived in FOUR sites, and this is the cycle's dominant defect class.** The `Min` / `Max` aggregate was stated correctly in the Slice-4 checklist bullet, [Decision 12][spec-028-d12], and the Non-goals DISTINCT-ON bullet — and the retired JOIN-multiplicity contract survived in the Test-plan `test_library_branches_order_by_reverse_fk_relation` bullet (three separate claims inside one bullet), [Decision 13][spec-028-d13]'s capability list, the Implementation-plan Slice-4 row, and the KANBAN past-tense body quoted under `## Doc updates`. **Why it survived where it did:** a later card's correction was applied at the two places that read as "the contract" — a checklist deliverable and a Decision — and never swept across the plan table, the coverage-strategy summary, the test description, or a quoted card body. Those four are the sites a reviewer of the *correcting* card would not open, because they belong to the *corrected* card. The cross-cohort seam is where this class survives review, and stating that is more useful than the four line numbers.
- **The Test plan's reverse-FK bullet carried a claim that must not be repointed, only deleted.** It asserted "The `RelatedOrder` GLOSSARY entry calls out this multiplicity". The entry does not, and **must not**, because the multiplicity no longer occurs — so the fix is to delete the claim rather than to make the GLOSSARY match it. Recorded because a mechanical "make the doc agree with the spec" pass would have gone the wrong way, and because the same bullet's other two claims (assert Alpha three times; pinning the multiplicity catches an accidental `.distinct()`) had to be replaced by the reason the *new* fixture shape is load-bearing: an uneven shelf count is what makes a regression to the raw fan-out observable, where one-shelf-per-branch could not tell the two implementations apart.
- **The `14` census was 11 sites over 10 lines at Slice 3's entry, and its subject had moved twice.** The build plan measured 14 sites; Slice 1 revised it to 13 after rewriting the `Status:` line; the measured population when Slice 3 opened the file was 11 occurrences over 10 lines, one of which was a cross-reference to *DoD item 14* rather than a test count. **Why the number kept moving:** every pass measured a population its own edits were about to change, and each reported a figure rather than a method. The lesson recorded here rather than the digit: a count restated in a spec carries its **subject** — "14 test functions from this card", not "14" — because the file has 16 and both statements are true of different populations.
- **The `docs/TREE.md` file count is a rendering convention, not a spec error.** [`scripts/build_tree_md.py`][tree] renders each entry from its module docstring and omits `__init__.py`, so a five-file subpackage renders as four described files. The spec claimed five in two places. Corrected to describe what the tree actually shows, with the reason, so the next subpackage spec does not re-introduce the same off-by-one.
- **The reload fixture's home was wrong.** The Test plan cited `test_library_api.py::_reload_project_schema_for_acceptance_tests`; the fixture is defined at `examples/fakeshop/test_query/conftest.py`, autouse across the whole `test_query/` tree. The spec's `[fakeshop-test-library-reload]` link definition also resolved to the same path as `[fakeshop-test-library]`, so two reference ids named one file — the same defect the `027` cycle found in its own spec, which is why it was verified before being repaired rather than assumed.
- **The Test-plan preamble counted trees where it should have named them.** "Tests live in two trees" was already wrong before the shared-substrate move (the card's own tests span `tests/orders/`, `tests/types/`, and `examples/fakeshop/test_query/`), and the move added two more homes for contracts the order side shares rather than owns (`tests/utils/test_permissions.py`, `tests/test_sets_mixins.py`). Naming them states the placement rule that actually governs — a contract is pinned in the tree that owns the code implementing it — where a count only invites another off-by-one.
- **Four spec-named package permission tests never existed**, and one existed in a different file. See the Decision 8 and Decision 9 entries above.
- **The pre-archive `docs/spec-028-orders-0_0_8.md` path appeared 12 times over 9 lines**, including inside DoD item 17's quoted `check_spec_glossary` command, which would have failed as written. All 12 are gone. [Decision 1][spec-028-d1] now states the archive layout positively — authored under `docs/` while in flight, moved to `docs/SPECS/` with its companions under `docs/SPECS/appx/` by the next spec author's `NEXT.md` Step-8 sweep — rather than asserting a path that the archive pass was always going to invalidate.

## Discharged by Slice 3

Slice 3 (`docs/builder/bld-slice-3-028-spec_reconciliation.md`) rewrote the spec so it reads as the current contract, discharging build-plan findings **D3-D16** plus five findings routed to it after the plan was written. Every correction is recorded above: keyed to its Decision under that Decision's `### Corrections this Decision received after ship`, or under `## Claims the spec may no longer make` when it belongs to no single Decision. The spec itself states only the corrected contract — no amendment block, no retraction paragraph, no chronology a reader must apply.

**Two findings came back negative and are recorded as re-derivations rather than edits**, because recording a negative is the only thing that stops the next pass re-opening it:

- **The position-side-channel GLOSSARY claim was half true.** The `RelatedOrder` entry does carry the note; only the `OrderSet` half was false. The spec now names `RelatedOrder` alone. A mechanical application of the finding as written would have deleted a true sentence.
- **The `14`-site census was 11 sites over 10 lines**, and one of those was a cross-reference to DoD item 14. The digit was never the point; the subject was.

**One thing Slice 3 looked for and did not find: a code finding.** The dispatch reserved one exception to "HEAD wins" — a place where HEAD looks like a genuine regression against a contract the spec intended, which would route to the maintainer rather than into a spec edit. There is none. Every divergence resolves the other way: HEAD is stricter (`getattr(f, "column", None) is not None` over `hasattr`; `startswith("ASC")` over substring membership; `classify_path` pre-validation where the spec promised none; the async-gate rejection closing an authorization bypass the spec never noticed), or single-sited (the relocated mechanics, `build_lazy_input_annotation`, `_bind_sidecar_sets`, `run_in_one_sync_boundary`, the registration seam), or a correction a later card landed deliberately (the row-preserving aggregate, `queryset.model`, the deleted cookbook-compat delegate). The ordering subsystem shipped in full and then grew; the spec's description of it was the only thing wrong.

**Three things Slice 1 or Slice 3 changed that a later reader must not re-derive as new rot:**

- **`[relay]` was already an unused link definition at `HEAD`** — not an orphan either slice created. Left in place; removing it is a judgement about whether [Decision 9][spec-028-d9]'s `orders.sets -> types.relay -> types.base` cycle discussion should link it.
- **Seven link definitions were removed by Slice 1** because the move took their only uses: `[next-step-8]`, `[spec-019]`, `[spec-021]`, `[spec-022]`, `[spec-023]`, `[spec-025]`, and `[upstream-cookbook-filterset-factories]`. All seven are defined in this file instead.
- **Nine link definitions were added or repointed by Slice 3** as the corrected prose acquired new citation targets: `[utils-inputs]`, `[utils-permissions]`, `[utils-querysets]`, `[utils-relations]`, `[orders-sets]`, `[test-orders-inputs]`, `[test-sets-mixins]`, `[test-utils-permissions]`, `[build-tree]`, plus `[fakeshop-test-conftest]` replacing the duplicate-target `[fakeshop-test-library-reload]`. Every path was disk-exists-checked.

**`KANBAN.md` and `docs/GLOSSARY.md` were out of this cycle's scope**, so the spec's corrected quotations of the KANBAN past-tense body now differ from the rendered card, and the `OrderSet` glossary entry still carries no position-side-channel note where its `RelatedOrder` sibling does. Both are routed to `docs/builder/bld-final-028.md`'s `### Deferred work catalog` as DB edits plus a regenerate, not as spec work.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-aggregateset]: ../../GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: ../../GLOSSARY.md#apply_cascade_permissions
[glossary-choice-enum-generation]: ../../GLOSSARY.md#choice-enum-generation
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangoconnectionfield]: ../../GLOSSARY.md#djangoconnectionfield
[glossary-metasearch_fields]: ../../GLOSSARY.md#metasearch_fields
[glossary]: ../../GLOSSARY.md
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next-step-8]: ../NEXT.md#step-8--archive-prior-specs-and-update-cross-references
[next]: ../NEXT.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-022]: ../spec-022-export_schema-0_0_7.md
[spec-023]: ../spec-023-multi_db-0_0_7.md
[spec-025]: ../spec-025-scalar_map_helper-0_0_7.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028-baseline]: ../spec-028-orders-0_0_8.md#pre-implementation-baseline-captured-before-slice-1
[spec-028-d10]: ../spec-028-orders-0_0_8.md#decision-10--version-bumps-are-maintainer-commanded
[spec-028-d11]: ../spec-028-orders-0_0_8.md#decision-11--order_input_typeorderset-consumer-helper
[spec-028-d12]: ../spec-028-orders-0_0_8.md#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface
[spec-028-d13]: ../spec-028-orders-0_0_8.md#decision-13--live-http-coverage-strategy
[spec-028-d1]: ../spec-028-orders-0_0_8.md#decision-1--spec-filename-and-canonical-naming
[spec-028-d2]: ../spec-028-orders-0_0_8.md#decision-2--subpackage-layout-and-public-export-surface
[spec-028-d3]: ../spec-028-orders-0_0_8.md#decision-3--five-layer-port-plus-a-deferred-layer-6
[spec-028-d4]: ../spec-028-orders-0_0_8.md#decision-4--upstream-primitives-parity-floor
[spec-028-d5]: ../spec-028-orders-0_0_8.md#decision-5--ordering-enum-and-argument-shape
[spec-028-d6]: ../spec-028-orders-0_0_8.md#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering
[spec-028-d7]: ../spec-028-orders-0_0_8.md#decision-7--metaorderset_class-promotion-gate
[spec-028-d8]: ../spec-028-orders-0_0_8.md#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer
[spec-028-d9]: ../spec-028-orders-0_0_8.md#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle
[spec-028-dod]: ../spec-028-orders-0_0_8.md#definition-of-done
[spec-028-edge-cases]: ../spec-028-orders-0_0_8.md#edge-cases-and-constraints
[spec-028-goals]: ../spec-028-orders-0_0_8.md#goals
[spec-028-slice-checklist]: ../spec-028-orders-0_0_8.md#slice-checklist
[spec-028]: ../spec-028-orders-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../../django_strawberry_framework/types/base.py
[filters-base]: ../../../django_strawberry_framework/filters/base.py
[filters-inputs]: ../../../django_strawberry_framework/filters/inputs.py
[finalizer]: ../../../django_strawberry_framework/types/finalizer.py
[optimizer-plans]: ../../../django_strawberry_framework/optimizer/plans.py
[optimizer-walker]: ../../../django_strawberry_framework/optimizer/walker.py
[orders]: ../../../django_strawberry_framework/orders/
[orders-sets]: ../../../django_strawberry_framework/orders/sets.py
[package-init]: ../../../django_strawberry_framework/__init__.py
[registry]: ../../../django_strawberry_framework/registry.py
[sets-mixins]: ../../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->
[test-base-init]: ../../../tests/base/test_init.py

<!-- examples/ -->
[fakeshop-test-library-reload]: ../../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-cookbook-filterset-factories]: https://github.com/riodw/django-graphene-filters
[upstream-cookbook-mixins]: https://github.com/riodw/django-graphene-filters
[upstream-cookbook-orderset]: https://github.com/riodw/django-graphene-filters
