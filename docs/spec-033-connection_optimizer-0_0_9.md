# Spec: Connection-aware optimizer planning — windowed nested-connection prefetches, pagination-aware plan-cache keys, strictness wiring for connection paths, and the products connections-only conversion

Planned for `0.0.9` (card [`WIP-ALPHA-033-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The card is the only card in the `## In progress` column and the **last open member of the `0.0.9` Relay cohort**: it closes the performance gap the cohort deliberately left open — [`DONE-030-0.0.9`][kanban] shipped [`DjangoConnectionField`][glossary-djangoconnectionfield] with its own optimizer cooperation seam, [`DONE-032-0.0.9`][kanban] shipped the relation-as-Connection upgrade with the explicit caveat that every synthesized `<field>Connection` lazy-loads per parent until this card lands. The [Slice checklist](#slice-checklist) below stays unticked as the contract record (build progress is tracked in the build plan, not here); the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with the shipped [`DONE-029-0.0.9`][kanban] / [`DONE-030-0.0.9`][kanban] / [`DONE-031-0.0.9`][kanban] / [`DONE-032-0.0.9`][kanban]; the `pyproject.toml` / `__version__` / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves (the on-disk version is still `0.0.8` at spec-authoring time).

Status: planned — no slice has started. Seven slices: Slice 1 (the **plan-side foundation** — selection-helper consolidation into the walker, the synthesis-metadata slot on [`DjangoTypeDefinition`][definition], walker recognition of synthesized relation connections, and windowed-`Prefetch` planning under a package-reserved `to_attr` — [Decision 3](#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing) / [Decision 4](#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr) / [Decision 9](#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker)), Slice 2 (the **resolver-side fast path** — the synthesized relation connection resolver consumes the windowed prefetch from the `to_attr`, deriving `edges` / cursors / `pageInfo` / `totalCount` from the window annotations with a per-parent fallback — [Decision 5](#decision-5--resolver-side-fast-path-with-annotation-presence-detection-and-a-per-parent-fallback)), Slice 3 (**plan-cache key hygiene** — nested-connection pagination *variables* are hashed into the plan-cache key; root pagination variables stay out — [Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not)), Slice 4 (**strictness wiring** — the connection pipeline consults the strictness sentinels so an unplanned, unserved nested-connection access finally surfaces under `"warn"` / `"raise"` — [Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)), Slice 5 (**live library SQL-shape coverage** — the nested `booksConnection` / `genresConnection` queries that [`spec-032`][spec-032] pinned behavior-only gain the deferred SQL-shape assertions), Slice 6 (**products connections-only conversion** — the four products list resolvers become `DjangoConnectionField`s, the cookbook mirror, with the `test_products_optimizer_*` dogfooding re-pinned through `edges { node }` — [Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card)), and Slice 7 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slices 1–2 are foundation-first; 3 and 4 build on 1–2; 5 builds on 2; 6 builds on 2–5; 7 lands last.

Owner: package maintainer.

Predecessors: [`spec-032-full_relay-0_0_9.md`][spec-032] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its Decision 6 synthesized the relation connections this card teaches the optimizer to plan, its Decision 12 pinned the pre-`033` posture this card retires — behavior-only live assertions, strictness-blind connection pipeline, products conversion fenced off — and its `_build_relation_connection_resolver` docstring names this card as the owner of the window-pagination cooperation seam); [`spec-030-connection_field-0_0_9.md`][spec-030] (its Decision 11 extracted `apply_connection_optimization` — the connection field's own optimizer cooperation point this card's root-connection planning already flows through — and its Decision 7 pipeline is what the fast path must reproduce from annotations); [`spec-004-optimizer_beyond-0_0_3.md`][spec-004] (the B1 plan cache whose key this card extends, the B3 strictness contract this card wires into connections, and the B8 queryset-diff reconciliation that must not regress); [`spec-002-optimizer-0_0_2.md`][spec-002] (the O2 walker this card extends and the O3 root gate that explains why the connection field owns its own seam). [`docs/GLOSSARY.md`][glossary] carries [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] as `planned for 0.0.9`; Slice 7 flips it to `shipped (0.0.9)` and sweeps the pre-`033` caveats out of the [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`Meta.relation_shapes`][glossary-metarelation_shapes] / [Strictness mode][glossary-strictness-mode] entries (see [Doc updates](#doc-updates)).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-033-0.0.9`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-12). Pinned the canonical spec filename (the card's `docs/spec-connection_optimizer.md` name predates the structured convention), the **card-premise staleness** ([Current state](#current-state) / [Decision 2](#decision-2--card-scope-boundary-what-already-shipped-what-this-card-ships)): the card's "a `0.0.9` `DjangoConnectionField` derives an empty plan (the flat walker is connection-unaware)" was true when the card was written but is no longer true on disk — the post-`032` hardening pass (commits `7b40d644` through `08da9664`, 2026-06-11/12) landed root-connection `edges { node }` extraction (`_connection_node_child_selections` + the `apply_to(..., selection_extractor=...)` seam) with package coverage, so this card's remaining scope is the **nested**-connection half: windowed relation-connection prefetches, pagination-aware cache keys, strictness wiring, and the live SQL-shape + products-conversion proof. Also pinned: the definition-metadata recognition mechanism (no name-pattern guessing, no `connection.py` internals in the walker), the `to_attr`-isolated window borrowed from `strawberry-graphql-django`'s `apply_window_pagination` with package-prefixed `_dst_row_number` / `_dst_total_count` annotations, the annotation-presence fast path with per-parent fallback, the fallback matrix (sidecar input / divergent aliases / `OptimizerHint.SKIP` / `pageInfo`-only), the nested-pagination-variables cache-key rule, the strictness contract (unplanned-and-unserved flags; the sidecar-input fallback flags too, consistently with the shipped unplanned-access posture), the products connections-only conversion landing with this card per the card's own sequencing note (the [`TODO-BETA-051-0.1.5`][kanban] ownership tension recorded in [Risks and open questions](#risks-and-open-questions)), and the joint-cut version boundary.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] — this card. The entry's "nested connections fall back to per-row queries" sentence is the problem statement; Slice 7 flips the status and rewrites the body to describe the shipped mechanism.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoConnection`][glossary-djangoconnection] — the shipped [`DONE-030-0.0.9`][kanban] connection surface. Its entry's "in `0.0.9` the derived plan is **empty**" caveat is already stale for *root* connections ([Current state](#current-state)) and goes away entirely with this card.
- [`Meta.relation_shapes`][glossary-metarelation_shapes] — the [`DONE-032-0.0.9`][kanban] key whose synthesized `<field>Connection` siblings are this card's planning target; the entry's `SyncMisuseError`-until-`033` caveat survives (the async connection pipeline stays out of scope, [Non-goals](#non-goals)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the schema extension whose `apply_to` seam, plan cache, and strictness constructor this card extends; no constructor or public-surface change.
- [Plan cache][glossary-plan-cache] — the B1 cache whose key gains the nested-pagination-variable component ([Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not)); the entry's "variable filtering" property is refined, not broken — variables that do not affect the plan stay out of the key.
- [Strictness mode][glossary-strictness-mode] — the B3 contract this card wires into the connection pipeline; today `_check_n1` fires only from the generated list-relation resolvers ([`types/resolvers.py::_check_n1`][resolvers]).
- [Queryset diffing][glossary-queryset-diffing] — the B8 reconciliation that must not regress (card DoD); the windowed prefetch rides `append_prefetch_unique` / `diff_plan_for_queryset` like every generated `Prefetch`.
- [FK-id elision][glossary-fk-id-elision] / [`only()` projection][glossary-only-projection] — shipped plan vocabulary the windowed child plans reuse unchanged; the window adds *annotations*, which compose with `.only()`.
- [`OptimizerHint`][glossary-optimizerhint] / [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] — the per-relation override surface; `SKIP` suppresses window planning for the relation's connection sibling, the other hint shapes do not affect it in `0.0.9` ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)).
- [`Meta.connection`][glossary-metaconnection] — the target-type `total_count` opt-in; a windowed nested connection serves `totalCount` from the `_dst_total_count` annotation instead of a per-parent `COUNT` ([Decision 4](#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr) / [Decision 5](#decision-5--resolver-side-fast-path-with-annotation-presence-detection-and-a-per-parent-fallback)).
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — baked into windowed child querysets exactly as into every generated `Prefetch` child queryset (and with the same consequence: the plan goes `cacheable = False`).
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] / [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] — the sidecars whose `filter:` / `orderBy:` arguments a nested connection may carry; a nested connection with sidecar input is **not** window-planned in `0.0.9` and falls back per-parent ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)).
- [`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] — the helpers behind the products root resolvers' current `filter:` / `orderBy:` arguments; the conversion replaces those hand-written signatures with [`DjangoConnectionField`][glossary-djangoconnectionfield]'s synthesized equivalents.
- [`DjangoType`][glossary-djangotype] / [Relay Node integration][glossary-relay-node-integration] / [`Meta.interfaces`][glossary-metainterfaces] — all four products types are already Relay-Node-shaped, which is why their relations already synthesize connection siblings today.
- [Definition-order independence][glossary-definition-order-independence] / [`finalize_django_types`][glossary-finalize_django_types] — the synthesis metadata this card's walker reads is recorded at finalization Phase 2.5, after relation targets settle.
- [Relation handling][glossary-relation-handling] — the shipped list-shaped relation planning is untouched; the windowed prefetch is an *additional* plan entry under a `to_attr`, never a replacement for the list field's accessor-keyed prefetch.
- [`DjangoListField`][glossary-djangolistfield] — root-gated list planning is untouched; the products conversion removes the products *resolvers*, not any `DjangoListField` usage (products never used it).
- [`SyncMisuseError`][glossary-syncmisuseerror] — the async-`get_queryset`-through-a-synthesized-connection contract is unchanged ([Non-goals](#non-goals)).
- [Multi-database cooperation][glossary-multi-database-cooperation] — windowed child querysets follow the shipped generated-`Prefetch` alias rules (they do NOT inherit the root alias); the window adds annotations only.
- [Schema audit][glossary-schema-audit] — unchanged; the audit walks relation fields, and synthesized connection siblings resolve through the same targets.
- [`Meta.search_fields`][glossary-metasearch_fields] — the `search:` argument stays absent from every connection until `0.1.2` ([`TODO-BETA-046-0.1.2`][kanban]); reaffirmed.
- [`ConfigurationError`][glossary-configurationerror] — no new validation surface; this card adds no `Meta` key and no public symbol.
- [`strawberry_config`][glossary-strawberry_config] — its `relay_max_results` passthrough is the page-size cap the plan-time window math must honor ([Decision 4](#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr)).
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — "filters, orders, … and connection fields all compose with `DjangoOptimizerExtension`" is the `1.0.0` invariant this card completes for the connection half.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — Slice 7's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slices 5–6) and package-internal `tests/` where the path is unreachable from a live query.
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; this card adds **no new source module** ([Decision 11](#decision-11--module-and-test-file-locations)), so no mirror tension arises — every edit lands in an existing module with an existing test twin.
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers); the "behaviorally we copy `strawberry-graphql-django`'s good ideas" rule — the window-pagination mechanism is exactly such an idea, borrowed at the mechanism level while the consumer surface stays `Meta`-declarative.

## Slice checklist

Each top-level item maps to one commit / PR. **Seven slices: six functional (1→2, then 3 and 4 on 1–2, 5 on 2, 6 on 2–5) plus a doc + card-completion wrap (7).** Boxes are unticked because the work has not started.

- [ ] Slice 1: plan-side foundation — synthesis metadata, walker recognition, windowed-`Prefetch` planning (per [Decision 3](#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing) / [Decision 4](#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr) / [Decision 9](#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker))
  - [ ] The `edges { node }` selection-unwrap helpers (`_named_children`, `_node_children_with_runtime_prefix`, `_with_runtime_prefix`, `_converted_selection_included`) move from [`optimizer/extension.py`][extension] into [`optimizer/walker.py`][walker]; `extension.py` imports them (the established import direction — `extension` already imports from `walker`; the reverse would cycle). `_connection_node_child_selections` stays in `extension.py` (it is the root-seam entry point) but becomes a thin composition over the moved helpers. No behavior change; pure consolidation so the walker can unwrap nested connection selections without an import cycle.
  - [ ] [`types/finalizer.py::_synthesize_relation_connections`][finalizer] records, on the declaring type's [`DjangoTypeDefinition`][definition], a `relation_connections: dict[str, str]` slot mapping each generated Python attribute name (`"books_connection"`) to its underlying relation field name (`"books"`). The walker reads this slot — never the `_dst_synthesized_relation_connection` marker on field objects, never `connection.py` internals — to recognize a nested connection selection (card DoD: "without reaching into `DjangoConnectionField` internals").
  - [ ] [`optimizer/walker.py::_walk_selections`][walker] gains a branch before the `django_field is None → continue` guard: when `snake_case(sel.name)` matches a `relation_connections` key, dispatch to a new `_plan_connection_relation(...)` that (a) unwraps the selection's `edges { node { ... } }` children via the consolidated helpers, (b) builds the child plan over the relation target exactly as `_build_prefetch_child_queryset` does (visibility hook baked when the target overrides [`get_queryset`][glossary-get_queryset-visibility-hook], flipping `cacheable = False`; connector columns ensured; child-plan metadata merged), (c) appends the deterministic total order (the [`spec-030`][spec-030] pipeline rule: pk appended unless the effective ordering already ends in a unique column — the shared helper is hoisted per [Decision 11](#decision-11--module-and-test-file-locations)), (d) computes the slice window from the selection's resolved `first` / `last` / `before` / `after` argument values (converted selections resolve variable references through `info.variable_values` — source-verified against the locked Strawberry `0.316.0`, `strawberry/types/nodes.py` #"info.variable_values.get(name)") mirroring `SliceMetadata.from_arguments` with `relay_max_results` read from the schema config, (e) applies the window via the new `plans.py` helper, and (f) appends `Prefetch(<accessor>, queryset=<windowed child qs>, to_attr="_dst_<field>_connection")` plus the connection field's resolver identities to `plan.planned_resolver_keys`.
  - [ ] [`optimizer/plans.py`][plans] gains the window helper — `apply_window_pagination(queryset, *, partition_by, order_by, offset, limit, reverse)` annotating `_dst_row_number` (`RowNumber()` partitioned by the relation connector column) and `_dst_total_count` (`Count(1)` partitioned the same way) and filtering the row-number range — the mechanism port of `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/pagination.py::apply_window_pagination` (itself based on Django's own approach in <https://github.com/django/django/pull/15957>).
  - [ ] Fallback shapes per [Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only): a nested connection selection carrying `filter:` / `orderBy:` arguments, aliased duplicates with divergent pagination arguments, a relation whose hint is [`OptimizerHint.SKIP`][glossary-optimizerhint], and a `pageInfo`-only selection (no `edges { node }` children) are all left **unplanned** — no window prefetch, no `planned_resolver_keys` entry — so Slice 4's strictness contract can see them.
  - [ ] Package coverage: [`tests/optimizer/test_walker.py`][test-opt-walker] + [`tests/optimizer/test_plans.py`][test-opt-plans] per the [Test plan](#test-plan). Interim posture: until Slice 2 lands, the windowed prefetch is planned but unconsumed (the synthesized resolver still re-queries per parent); Slice 1's tests assert **plan content only**, and the cross-slice seam carries a `TODO(spec-033 Slice 2)` anchor per the [`AGENTS.md`][agents] design-doc discipline.
- [ ] Slice 2: resolver-side fast path (per [Decision 5](#decision-5--resolver-side-fast-path-with-annotation-presence-detection-and-a-per-parent-fallback))
  - [ ] [`connection.py::_build_relation_connection_resolver`][connection] gains the consumption branch: when `getattr(root, "_dst_<field>_connection", None)` is a list whose members carry `_dst_row_number` / `_dst_total_count`, resolve the connection **directly from the prefetched rows** — edges with Strawberry-format offset cursors derived from `_dst_row_number - 1`, `pageInfo` from the first/last row numbers against `_dst_total_count`, and `totalCount` (when the target's [`Meta.connection`][glossary-metaconnection] opted in and the field is selected) from the same annotation — skipping the per-parent pipeline entirely (visibility was baked at plan time; sidecar input cannot be present on the fast path by construction, [Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)). Rows absent or annotations missing → the shipped per-parent pipeline runs unchanged (the fallback is the pre-card behavior, never an error).
  - [ ] The fast-path connection instance is built through the same generated `<TypeName>Connection` class (`_connection_type_for`) the pipeline path uses, so SDL shape, the `first`+`last` guard, and the `totalCount` member are identical on both paths.
  - [ ] Package coverage: [`tests/test_relay_connection.py`][test-relay-connection] per the [Test plan](#test-plan) — including the parity matrix (fast path vs. pipeline path produce identical wire results) and the query-count pins (one windowed query per relation per request, zero per-parent queries).
- [ ] Slice 3: plan-cache key hygiene (per [Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not))
  - [ ] [`optimizer/extension.py::_build_cache_key`][extension] extends its variable collection: alongside the `@skip` / `@include` directive variables, collect the values of variables referenced in `first` / `last` / `before` / `after` arguments of **non-root** field nodes (the root field's own pagination arguments never affect plan content — slicing happens post-plan in `ConnectionExtension`; nested pagination values are baked into windowed prefetches and therefore must key the cache). Two requests differing only in a nested `first: $n` value get distinct cached plans; two requests differing only in a root `first: $n` value share one.
  - [ ] Package coverage: [`tests/optimizer/test_extension.py`][test-opt-extension] per the [Test plan](#test-plan).
- [ ] Slice 4: strictness wiring for connection paths (per [Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths))
  - [ ] [`connection.py::_build_relation_connection_resolver`][connection] consults the [`_context.py`][context] sentinels before running the per-parent pipeline: when `DST_OPTIMIZER_PLANNED` is stashed (an optimizer ran with strictness active), the connection field's resolver key is absent from it, and the fast-path `to_attr` is absent on `root`, fire the strictness contract — `OptimizerError` under `"raise"`, a logged warning under `"warn"` — reusing the [`types/resolvers.py::_check_n1`][resolvers] machinery (parameterized for the `to_attr` probe and the generated field name) rather than duplicating it. The deliberately-ABSENT comment block in the resolver docstring (the [`spec-032`][spec-032] pre-`033` posture) is removed in the same change.
  - [ ] Root [`DjangoConnectionField`][glossary-djangoconnectionfield]s need no strictness change: when the optimizer is installed, `apply_connection_optimization` plans them (Current state); when it is not installed, no sentinel is stashed and the check is a no-op — the same contract every list relation already has.
  - [ ] Package coverage: [`tests/test_relay_connection.py`][test-relay-connection] + [`tests/optimizer/test_extension.py`][test-opt-extension] per the [Test plan](#test-plan).
- [ ] Slice 5: live library nested-connection SQL-shape coverage
  - [ ] [`examples/fakeshop/test_query/test_library_api.py`][test-library]: the [`spec-032`][spec-032] Slice-6 nested-connection tests (`test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`) asserted **behavior only** with the explicit note that SQL-shape assertions are this card's deliverable. Slice 5 adds the deferred pins: a two-level `allLibraryGenresConnection { edges { node { booksConnection(first: N) { edges { node } totalCount } } } }` query (the cookbook-equivalent nested-connection shape the card's DoD names) executes in a **fixed query count** independent of the number of parent genres, and the nested `totalCount` adds no per-parent `COUNT`.
  - [ ] Per the [`test_query/README.md`][test-query-readme] coverage rule, the live suite is the primary home; the package mirrors in [`tests/test_relay_connection.py`][test-relay-connection] cover the shapes the fakeshop graph lacks (reverse-FK relation connections, the narrowed `"connection"` shape, divergent-alias fallback).
- [ ] Slice 6: products connections-only conversion (per [Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card))
  - [ ] [`examples/fakeshop/apps/products/schema.py`][products-schema]: the four `@strawberry.field` list resolvers (`all_categories` / `all_items` / `all_properties` / `all_entries`) are replaced by four `DjangoConnectionField` class attributes (`all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)`, …) — the 1-to-1 `django-graphene-filters` cookbook mirror (the cookbook Query is `all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)` with **no** list resolvers). The hand-written `filter:` / `orderBy:` arguments disappear; the synthesized signatures derive the same arguments from the same sidecars. The root `node(id:)` / `nodes(ids:)` entry points are NOT added here — they remain [`TODO-BETA-051-0.1.5`][kanban]'s fakeshop-activation scope.
  - [ ] [`examples/fakeshop/test_query/test_products_api.py`][test-products]: every list-shaped assertion rewrites to the `edges { node }` shape; the three `test_products_optimizer_*` SQL-shape tests (root-node merge, nested reverse-FK prefetch depth-2, nested forward-FK `select_related` depth-2) are re-pinned **through the connection wrapper** with their query-count assertions intact — the regression fence the card exists to keep honest. The `check_name_permission` filter/order denial-gate tests re-pin against the synthesized arguments.
  - [ ] The four products types gain no `Meta.connection` opt-in (no `totalCount` — minimal conversion, root-field shape only); their relation-connection siblings (`itemsConnection`, `entriesConnection`, …) already exist live via the [`DONE-032-0.0.9`][kanban] implicit `"both"` default and now plan through Slices 1–2.
- [ ] Slice 7: doc updates + card-completion wrap (per [Doc updates](#doc-updates))
  - [ ] [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog] (the explicit permission grant), [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render). No version-file edits ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Problem statement

The `0.0.9` Relay cohort shipped a complete, correct, and **partially unoptimized** connection surface. Root connections are now planned — the post-`032` hardening pass landed `edges { node }` extraction for the root seam, so a root `DjangoConnectionField`'s pre-slice queryset receives `select_related` / `prefetch_related` / `only()` like any list resolver. But the **nested** half is untouched: every `<field>Connection` sibling that [`DONE-032-0.0.9`][kanban]'s relation-as-Connection upgrade synthesizes resolves through a per-parent pipeline — `getattr(root, accessor).all()` per parent row, then visibility, ordering, optimizer, and cursor slice per parent row. A cookbook-shaped two-level query (`{ allObjects { edges { node { values { edges { node { value } } } } } } }`, the `django-graphene-filters` recipes shape the card names) issues one query per parent: the textbook N+1, shipped knowingly under [`spec-032`][spec-032] Decision 12's joint-cut sequencing argument — *both cards ship in the same `0.0.9` cut, so no released version carries the gap*. This card is the second half of that argument.

The gap is wider than latency. The parent's selection walker skips nested connection selections entirely (`books_connection` matches no model field; the unknown-name guard `continue`s), so the plan never records them — which means [Strictness mode][glossary-strictness-mode] cannot flag them either: `"raise"` runs sail silently past a per-parent access pattern that the same query expressed as a plain list relation would have failed loudly. And the [Plan cache][glossary-plan-cache] has a latent correctness boundary: once pagination *values* are baked into prefetch querysets, two requests differing only in a variable-supplied `first:` must not share a cached plan — a key-hygiene rule the current `@skip` / `@include`-only variable collection cannot express.

The upstream proof that the mechanism works at scale is direct: `strawberry-graphql-django` detects a connection on a nested field inside its prefetch builder, computes the slice window via Strawberry's own `SliceMetadata.from_arguments`, and pushes the window into the prefetch as `RowNumber()` / `Count(1)` window functions partitioned by the relation's connector column (`/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py::_optimize_prefetch_queryset`, `pagination.py::apply_window_pagination`); its connection class then resolves edges, `pageInfo`, and `totalCount` straight from the prefetched rows' annotations (`relay/list_connection.py::DjangoListConnection.resolve_connection` #"resolve_optimized_connection_by_prefetch"). Each parent's page costs one window-function query for the whole batch, and `totalCount` rides the same query. graphene-django ships no native equivalent — the card's parity claim is correctly `strawberry-graphql-django`-only and **Required**.

Finally, the card unblocks the dogfooding surface that was deliberately fenced off: the products connections-only conversion. The products live optimizer tests (`test_products_optimizer_*`) pin the package's SQL shapes through real HTTP queries; converting the products Query to connections before nested planning existed would have regressed exactly those pins, so [`DONE-032-0.0.9`][kanban] and the card both sequenced the conversion behind this card — "Land the products list->connection replacement together with this card."

## Current state

A true description of the repo as of this writing (the plan is written against it), source-verified against the locked Strawberry `0.316.0` and Django `>= 5.2`:

- **Root-connection planning already works — the card's central premise is stale.** The card body (and [`spec-032`][spec-032]'s Current state, accurate when written) say a `0.0.9` connection "derives an empty plan". On disk today: [`optimizer/extension.py::apply_connection_optimization`][extension] discovers the active extension instance from the `_active_optimizer` `ContextVar` published by `on_execute`, and calls `apply_to(..., selection_extractor=_connection_node_child_selections)`; `_connection_node_child_selections` unwraps `edges { node { ... } }` (recursing through fragment wrappers via `_named_children`) and clones node children carrying `_optimizer_runtime_prefixes` so resolver keys and FK-id elisions stay branch-correct under the connection's runtime path. The walker's `_merge_aliased_selections` honors those carried prefixes. This landed in the post-`032` hardening pass (commit `7b40d644`, "implement connection-aware selection extraction and optimize planning for edges.node queries", folded and refined through `08da9664`) with package coverage: [`tests/test_connection.py`][test-connection] pins a root connection planning `select_related("category")` for `edges { node { category } }` and a `Prefetch` for a many-side node relation (#"test_root_connection_field_queryset_prefetches_node_many_relation"); [`tests/optimizer/test_extension.py`][test-opt-extension] pins the shared-plan-cache contract (#"test_apply_connection_optimization_uses_active_optimizer_cache") and the runtime-prefix merge. **This card does not re-ship any of it**; its scope is the remainder ([Decision 2](#decision-2--card-scope-boundary-what-already-shipped-what-this-card-ships)).
- **Nested connections are unplanned and per-parent.** [`types/finalizer.py::_synthesize_relation_connections`][finalizer] synthesizes `<field>_connection` siblings for eligible many-side relations (declaring type Relay-shaped, target Relay-shaped, per [`Meta.relation_shapes`][glossary-metarelation_shapes]); the synthesized resolver ([`connection.py::_build_relation_connection_resolver`][connection]) seeds from `getattr(root, accessor_name).all()` and runs the full pipeline per parent — its docstring documents both the seam ("the cooperation seam `WIP-ALPHA-033-0.0.9`'s window-pagination planning will use") and the deliberate strictness blindness ("Deliberately ABSENT: any `DST_OPTIMIZER_STRICTNESS` / `DST_OPTIMIZER_PLANNED` consultation … until `033` wires it"). The parent walker never sees these selections: [`optimizer/walker.py::_walk_selections`][walker] looks `snake_case(sel.name)` up in the model `field_map`, finds nothing for `books_connection`, and `continue`s.
- **The synthesis records no walker-readable metadata.** The finalizer marks synthesized fields with the module constant `_SYNTHESIZED_RELATION_CONNECTION_MARKER` (idempotent-recovery bookkeeping), but [`DjangoTypeDefinition`][definition] has no slot mapping generated connection names to their underlying relations — the walker has nothing definition-shaped to consult, which is the gap [Decision 3](#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing) fills.
- **The selection-unwrap helpers live on the extension side.** `_named_children` / `_node_children_with_runtime_prefix` / `_with_runtime_prefix` / `_converted_selection_included` sit in [`optimizer/extension.py`][extension]; `extension` imports from `walker`, so the walker cannot import them back without a cycle ([Decision 9](#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker)). [`TODO-ALPHA-035-0.0.10`][kanban]'s G3 note independently flags these helpers as a shared seam.
- **The plan cache keys on printed AST + directive variables only.** [`optimizer/extension.py::_build_cache_key`][extension] hashes the printed operation (+ reachable fragments), the values of variables referenced in `@skip` / `@include`, the target model, the root runtime path, and the origin type. Pagination argument *literals* enter the key via the printed AST (each distinct inline `first:` fragments the cache — pre-existing, harmless for correctness); pagination *variables* do not enter the key at all — harmless today (no plan content depends on them), wrong the moment Slice 1 bakes windows into prefetches ([Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not)). Converted selections resolve variable references to concrete values through `info.variable_values` (locked Strawberry `strawberry/types/nodes.py` #"info.variable_values.get(name)"), so the walker can read the values; the cache key just doesn't know about them yet.
- **Strictness fires from list-relation resolvers only.** [`types/resolvers.py::_check_n1`][resolvers] is called from the three generated relation-resolver shapes; it probes the plan's `DST_OPTIMIZER_PLANNED` sentinel and the instance caches (`_prefetched_objects_cache` for many-side). Nothing in [`connection.py`][connection] consults any sentinel.
- **Total ordering and totalCount are pipeline-owned.** [`connection.py::_finalize_queryset`][connection] appends the pk as a terminal tiebreaker unless the effective ordering already ends in a unique column (`_ends_in_unique_column`); the generated `<TypeName>Connection`'s `resolve_connection` counts the post-filter pre-slice queryset (selection-gated, `_total_count_requested` checking the connection's **direct** children — deliberately not recursing into `edges { node }`, exactly so a nested connection's `totalCount` cannot fire the outer predicate). Both contracts are load-bearing inputs to the window design: the window's `order_by` must reproduce the pipeline's deterministic order, and the nested `totalCount` must come from the window annotation, not a per-parent `COUNT`.
- **Fakeshop:** the library app's live Relay surface ([`spec-032`][spec-032] Slice 6) includes the nested `booksConnection` (reverse M2M, `GenreType` → promoted Relay-shaped `BookType` with a `get_queryset` visibility filter) and `genresConnection` (forward M2M, target `GenreType` declares [`Meta.connection`][glossary-metaconnection] `total_count`), live-tested **behavior-only** with the SQL-shape assertions explicitly deferred to this card. The products app's four types are all Relay-Node-shaped with both sidecars wired — so their many-side relations *already* synthesize live connection siblings under the implicit `"both"` default — but the products `Query` is list-resolver-shaped ([`apps/products/schema.py`][products-schema] carries the commented connections-only future shape in its `Query` docstring block), and [`test_products_api.py`][test-products] pins the optimizer dogfooding through those list roots.
- **Dependency floors cover window functions.** `pyproject.toml` pins `Django>=5.2` (window-function filtering in `QuerySet.filter` is supported since Django 4.2; the bundled SQLite in every supported CPython ≥ 3.10 is ≥ 3.25, where window functions landed), so the window mechanism needs no conditional backend path.
- The card's hard gate (`DONE-030-0.0.9` / "Relay decisions") is satisfied — the entire `0.0.9` Relay cohort except this card is shipped.

## Goals

1. **Plan nested connections.** The walker recognizes synthesized relation-connection selections through definition metadata and plans a windowed `Prefetch` for each — child plan over the target (visibility, projections, nested relations, deeper nested connections recursively), deterministic total order matching the pipeline's rule, slice window from the selection's resolved pagination arguments capped by `relay_max_results`, landed under a package-reserved `to_attr` so the list sibling's accessor-keyed prefetch and the window never collide (Slice 1, [Decision 3](#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing) / [Decision 4](#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr)).
2. **Consume the window.** The synthesized relation connection resolver serves `edges` (offset cursors from `_dst_row_number`), `pageInfo`, and `totalCount` (from `_dst_total_count`, when the target opted in) directly from the prefetched rows — one window query per relation per request, zero per-parent queries — falling back to the shipped per-parent pipeline whenever the window is absent (Slice 2, [Decision 5](#decision-5--resolver-side-fast-path-with-annotation-presence-detection-and-a-per-parent-fallback)).
3. **Keep the plan cache honest.** Variables feeding **nested** pagination arguments are hashed into the plan-cache key (their values are baked into plans); variables feeding **root** pagination arguments stay out (their values never affect plan content) — the card's "skip pagination args that do not affect selection shape, hash the ones that do" (Slice 3, [Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not)).
4. **Wire strictness into connections.** An unplanned, unserved nested-connection access fires the [Strictness mode][glossary-strictness-mode] contract (`warn` / `raise`) through the same resolver-key vocabulary list relations use, closing the silent-N+1 hole [`spec-032`][spec-032] documented (Slice 4, [Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)).
5. **Prove it live, then dogfood it.** The library suite gains the deferred fixed-query-count SQL-shape assertions for the cookbook-equivalent nested-connection shape; the products Query converts to connections-only (the cookbook mirror) with the `test_products_optimizer_*` SQL-shape dogfooding re-pinned through `edges { node }` (Slices 5–6, [Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card)).
6. **No B1–B8 regression.** The plan cache, queryset diffing, FK-id elision, `only()` projection, hints, multi-DB rules, and the root-connection planning that already shipped all keep their existing coverage green (card DoD).
7. **Keep package version state command-gated and owned by the joint `0.0.9` cut**: no slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` (Slice 7, [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Async connection pipeline.** A Relay target whose `get_queryset` is `async def` still raises [`SyncMisuseError`][glossary-syncmisuseerror] through its synthesized `<field>Connection` (the [`Meta.relation_shapes`][glossary-metarelation_shapes] `"list"` narrowing remains the recourse). The window planning below is sync-pipeline planning; the async story is untouched.
- **Windowed planning for sidecar-filtered nested connections.** A nested connection carrying `filter:` / `orderBy:` input falls back to per-parent resolution in `0.0.9` ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)) — baking [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] application into plan-time child querysets needs request-scoped input threading through the walker, a follow-up with its own design surface.
- **Root `totalCount` window folding.** The shipped root contract — selection-gated `.count()` / `.acount()` on the pre-slice queryset — stays. One `COUNT` per root connection is not an N+1; folding it into the main query via a partition-less window (upstream's `DjangoListConnection.resolve_connection` annotation) is a micro-optimization that would churn a shipped, tested contract mid-cohort. Recorded as a possible follow-up in [Risks and open questions](#risks-and-open-questions).
- **Keyset / column-anchored cursors.** `Meta.cursor_field` and positional-stability-under-mutation guarantees stay in [`BACKLOG.md`][backlog] item 39; the window math below inherits Strawberry's offset-cursor semantics verbatim.
- **The G1–G3 robustness guards** (evaluated-queryset guard, operation-type `only()` gating, fragment `type_condition` narrowing) — [`TODO-ALPHA-035-0.0.10`][kanban], which deliberately lands *after* this card to avoid concurrent walker churn (its own dependency note).
- **The rest of the fakeshop products activation.** Root `node(id:)` / `nodes(ids:)` entry points on products and any further Relay reshaping stay with [`TODO-BETA-051-0.1.5`][kanban]; this card takes exactly the list→connection root-field replacement the card text binds to it ([Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card)).
- **The permissions subsystem** — [`TODO-ALPHA-034-0.0.10`][kanban]; cascade visibility composes with connections when it lands ([`apply_cascade_permissions`][glossary-apply_cascade_permissions] runs inside `get_queryset`, which both the pipeline and the windowed child queryset already honor).
- **`search:` argument** — [`Meta.search_fields`][glossary-metasearch_fields] is `0.1.2`.
- **A version bump.** Owned by the joint `0.0.9` cut ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test, connection-aware planning is a **one-upstream Required parity**: `strawberry-graphql-django` plans nested connection selections natively; graphene-django has only rudimentary connection-aware optimization (the card tags it ⚛️ parity-adjacent). The behavioral mechanism is borrowed from the strawberry side wholesale — exactly the [`START.md`][start] rule ("behaviorally we copy strawberry-graphql-django's good ideas") — while the consumer surface stays the package's own: nothing new to declare, no decorators, no per-field opt-ins; the optimization applies to the `Meta`-declared relation connections automatically.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| strawberry-graphql-django: `optimizer.py::_optimize_prefetch_queryset` detects a nested connection, computes `SliceMetadata.from_arguments`, pushes the slice into the prefetch via `apply_window_pagination` (`RowNumber` window partitioned by the relation field) | walker recognizes synthesized relation connections via definition metadata and plans the windowed `Prefetch` ([Decision 3](#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing) / [Decision 4](#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr)) | **this card (`0.0.9`) — required parity** |
| strawberry-graphql-django: `DjangoListConnection.resolve_connection` resolves edges / `pageInfo` from prefetched rows' `_strawberry_row_number` and reads `totalCount` from `_strawberry_total_count` instead of a second `COUNT` | the synthesized relation connection resolver's annotation fast path ([Decision 5](#decision-5--resolver-side-fast-path-with-annotation-presence-detection-and-a-per-parent-fallback)) | **this card (`0.0.9`) — required parity** |
| graphene-django: no native connection-aware optimizer | — | ⚛️ parity-adjacent (nothing to borrow) |
| (no plan cache upstream — strawberry-django re-walks per request) | pagination-aware plan-cache keys so windowed plans cache safely ([Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not)) | this card — consequence of the package's B1 plan cache, beyond parity |
| (no strictness mode upstream) | strictness wiring for connection paths ([Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)) | this card — consequence of the package's B3 strictness, beyond parity |

### From `strawberry-graphql-django` — borrow the runtime mechanism

The window-pagination prefetch is ported at the mechanism level: `RowNumber()` and `Count(1)` window functions partitioned by the relation's connector column, row-number range filters for the slice, reversed row-number for backward (`last`-only) pagination, and prefetch-cache connection resolution reading the annotations (`/Users/riordenweber/projects/strawberry-django-main/strawberry_django/pagination.py::apply_window_pagination`, itself based on Django's own approach in <https://github.com/django/django/pull/15957>; `relay/list_connection.py` #"resolve_optimized_connection_by_prefetch"). The slice arithmetic reuses the engine: Strawberry's `strawberry/relay/utils.py::SliceMetadata.from_arguments` is the same helper upstream calls.

### Explicitly do not borrow

- **The queryset-config marker system.** Upstream threads an `is_optimized_by_prefetching` flag through a `QuerySet`-attached config and monkeypatches `QuerySet._clone` to carry it. The package detects the window by **annotation presence on the prefetched rows** (upstream's own fallback probe) plus the package-reserved `to_attr` — no global state, no monkeypatching, the same posture that rejected the `resolve_type` patch in the `031` cycle.
- **Plan-time `field_kwargs` application.** Upstream applies the nested field's *full* argument set (filters included) inside the prefetch builder. The package's plan cache makes request-scoped values in plans a correctness hazard, so `0.0.9` windows only the argument family whose values it can hash into the key (pagination), and falls back per-parent for sidecar input ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)).
- **The `_strawberry_*` annotation names.** The package namespaces its annotations `_dst_*` (matching the `DST_*` context keys and the `_dst_` marker convention) so a consumer running both libraries in one process can never collide.
- **Upstream's per-field-node `Info` reconstruction.** The walker reads resolved argument values off converted selections (the engine resolves variables during conversion); no synthesized `Info` objects.

## User-facing API

**This card adds no public symbol, no `Meta` key, and no constructor argument.** The consumer-visible changes are behavioral:

```graphql
{
  allLibraryGenresConnection(
    first: 10
  ) {
    edges {
      node {
        name
        booksConnection(
          first: 3
        ) {
          edges {
            node {
              title
            }
          }
          totalCount
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
  }
}
```

- **Before this card**: 1 query for the genres page, then *per genre* one query for its books page (plus one `COUNT` per genre when `totalCount` is selected and the target opted in).
- **After this card**: 1 query for the genres page + **1 window-function query** covering every genre's books page and every `totalCount` — a fixed count regardless of how many genres the first page returns. Wire results are byte-identical.
- [Strictness mode][glossary-strictness-mode] `"raise"` now flags a nested-connection access the plan does not cover (previously silent), with the same planned-key exemption semantics as list relations.

The products example reshapes to the cookbook mirror (Slice 6):

```python
from django_strawberry_framework import DjangoConnection, DjangoConnectionField


@strawberry.type
class Query:
    all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)
    all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)
    all_properties: DjangoConnection[PropertyType] = DjangoConnectionField(PropertyType)
    all_entries: DjangoConnection[EntryType] = DjangoConnectionField(EntryType)
```

The hand-written resolvers (and their `filter_input_type(...)` / `order_input_type(...)` parameter declarations) disappear; the synthesized signatures expose the same `filter:` / `orderBy:` arguments from the same [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] sidecars, and the pipeline applies the same visibility → filter → order → deterministic-order → optimizer composition the resolvers spelled by hand.

### Error shapes

- No new error surface. The `first` + `last` guard, the sidecar-input-over-non-queryset guard, the `totalCount`-over-non-queryset guard, and the [`SyncMisuseError`][glossary-syncmisuseerror] contract are all inherited unchanged on both the fast path and the fallback.
- [Strictness mode][glossary-strictness-mode] `"raise"` surfaces `OptimizerError(f"Unplanned N+1: <field>_connection")` for an unplanned, unserved nested-connection access — the same exception class and vocabulary list relations use ([Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-033-connection_optimizer-0_0_9.md`** (this document).

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `WIP-ALPHA-033-0.0.9`, so `<NNN>` is `033` and `<0_0_X>` is `0_0_9`.
- The topic slug is `connection_optimizer` — the card's own suggested filename stem, kept because it names the subject precisely (the optimizer's connection awareness).

Alternatives considered (and rejected):

- **The card's own `docs/spec-connection_optimizer.md`.** Rejected: predates the structured-filename convention; [`spec-032`][spec-032] Decision 1 set the precedent of preferring the convention and recording the card's older name.
- **"Folded into `docs/spec-connection.md`"** (the card's parenthetical). Rejected: the connection field shipped under its own spec ([`spec-030`][spec-030], already archived); folding a new card's plan into a shipped spec would break the one-card-one-spec record the WIP/DONE spec map maintains.
- **Topic slug `connection_aware_planning` or `optimizer_connections`.** Rejected: longer without being more precise; the card's own stem wins ties.

### Decision 2 — Card-scope boundary: what already shipped, what this card ships

The card enumerates four work bullets; the repo has moved since the card was written, and this spec pins the boundary against **today's** source rather than the card's snapshot:

- **"Selection-tree walker awareness of Relay `edges { node }`" — half shipped.** The ROOT half (a connection field's own `edges { node }` unwrapped so the pre-slice queryset plans) landed in the post-`032` hardening pass with package coverage ([Current state](#current-state)). This card ships the NESTED half: recognition of `<field>_connection` selections inside a parent's walk, which no shipped code attempts.
- **"Connection-pagination-aware queryset planning (`Prefetch` downgrade, `total_count` aggregate cooperation, slice-aware projections)" — this card**, Slices 1–2: the windowed `Prefetch` under a `to_attr`, the `_dst_total_count` annotation serving nested `totalCount`, and child-plan `only()` projections that keep the window's partition and ordering columns loaded.
- **"Plan-cache key hygiene for paginated selections" — this card**, Slice 3.
- **"Strictness-mode interaction with connection paths" — this card**, Slice 4.
- **The products list→connection replacement — this card**, Slice 6, per the card's own sequencing note; the rest of the products/fakeshop activation stays with [`TODO-BETA-051-0.1.5`][kanban] ([Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card)).
- **[`TODO-ALPHA-035-0.0.10`][kanban]'s G1–G3 guards — not this card**; that card's own planning note assigns the "two big performance findings" (windowed nested-prefetch pagination, `totalCount` window reuse) here and keeps the robustness guards there, landing after this card to avoid concurrent walker churn.

Justification: the [`docs/SPECS/NEXT.md`][next] boundary rule says prefer the card and flag conflicts — but the "empty plan" premise is not a *design* conflict to defer to, it is a factual snapshot the repo has outrun; building the root half again would duplicate shipped, tested code. The card's four bullets and DoD are all still satisfiable, and are satisfied, under the narrowed reading; the staleness is recorded here and in [Risks and open questions](#risks-and-open-questions) rather than silently reconciled.

Alternatives considered (and rejected): **Treat the root-connection extraction as part of this card and fold its (already-merged) commits into the slice record.** Rejected: the work is on `main` with green coverage and predates this spec; claiming it would make the slice checklist a fiction and the per-slice diffs unreviewable.

### Decision 3 — Walker recognition is definition-metadata-driven, not name-pattern guessing

[`types/finalizer.py::_synthesize_relation_connections`][finalizer] records a `relation_connections: dict[str, str]` slot on the declaring type's [`DjangoTypeDefinition`][definition] — generated Python attribute name → underlying relation field name (`{"books_connection": "books"}`) — at the moment it synthesizes each sibling. The walker consults that slot (via the `definition` it already resolves per level) to recognize a nested connection selection and to find the relation it paginates.

Justification:

- **The card's DoD demands it**: "Walker recognizes connection edge/node shapes without reaching into `DjangoConnectionField` internals." A definition slot is the same channel the walker already uses for `field_map`, `optimizer_hints`, and relation targets — zero new coupling.
- **Name-pattern guessing is wrong twice.** Stripping a `_connection` suffix would misfire on a consumer-authored field that merely *ends* in `_connection`, and would fire for relations whose synthesis was suppressed (`"list"` narrowing, consumer-authored relation, non-Node target). The synthesis already computed the true mapping; recording it costs one dict.
- **Finalization is the right write point**: relation targets are settled (Phase 1), the synthesis runs in Phase 2.5, and the definition is the canonical per-type record every other Phase-2.5 product (sidecar bindings, strategy stamps) already writes to.

Alternatives considered (and rejected):

- **Reaching into `connection.py`'s `_connection_type_cache` or the field marker at plan time.** Rejected: exactly the internals-coupling the DoD forbids, and field objects are not reachable from the walker's `(model, field_map)` vocabulary.
- **Suffix-stripping with a field-map existence check.** Rejected: still misfires on suppressed synthesis (the `"list"`-narrowed relation has a real `books` in the field map but no connection sibling — planning a window for a field that does not exist would do dead work and stash wrong resolver keys).

### Decision 4 — Windowed-prefetch planning under a package-reserved `to_attr`

`_plan_connection_relation` plans each recognized nested connection as `Prefetch(<accessor>, queryset=<windowed child queryset>, to_attr="_dst_<field>_connection")`:

- **Child queryset**: built exactly like every generated prefetch child — `related_model._default_manager.all()`, target [`get_queryset`][glossary-get_queryset-visibility-hook] applied when overridden (flipping `plan.cacheable = False`, the shipped request-scope rule), the nested `edges { node { ... } }` child plan applied (projections, `select_related`, deeper prefetches — **including deeper windowed connections recursively**), connector columns ensured so Django can attach rows and the window can partition.
- **Deterministic order**: the same rule the pipeline applies — the effective ordering (queryset, else model `Meta.ordering`) with the pk appended unless it already ends in a unique column — hoisted to a shared helper so the plan-time window and the resolve-time pipeline can never disagree ([Decision 11](#decision-11--module-and-test-file-locations)); a disagreement would make window row numbers inconsistent with fallback-path cursors.
- **Window**: `_dst_row_number = RowNumber() OVER (PARTITION BY <connector> ORDER BY <deterministic order>)` and `_dst_total_count = Count(1) OVER (PARTITION BY <connector>)`, with row-number range filters for the slice — the `plans.py` helper ported from upstream's `apply_window_pagination`, including the reversed-row-number branch for `last`-only backward pagination.
- **Slice arithmetic**: Strawberry's `SliceMetadata.from_arguments` over the selection's **resolved** argument values (literals and variables alike — converted selections resolve variables), `max_results` read from the schema config's `relay_max_results` (default 100) so the plan-time cap and the resolve-time cap are the same number.
- **`to_attr` isolation**: the window lands on `_dst_<field>_connection`, never the relation accessor. The `"both"` shape means the list sibling and the connection can be selected together; two `Prefetch`es on one accessor with different querysets is Django's "lookup already seen" error, and a windowed result would silently corrupt the list field's semantics. The `to_attr` gives the window its own slot; the list field's accessor-keyed prefetch (when its selection plans one) is untouched. The `_dst_` prefix is the package's reserved namespace (consistent with `_dst_optimizer_*` context keys and the `_dst_synthesized_relation_connection` marker).
- **Resolver keys**: the connection field's resolver identities (declaring type + generated field name + runtime paths, the same `resolver_key` vocabulary) are appended to `plan.planned_resolver_keys` so strictness ([Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)) sees the field as planned.

Justification: this is the proven upstream mechanism (parity table) adapted to the package's two structural differences — the plan cache (which forces the cacheability and key-hygiene rules) and the `"both"`-sibling shape (which forces the `to_attr`). Window functions are fully supported at the package's dependency floor ([Current state](#current-state)).

Alternatives considered (and rejected):

- **A plain (unwindowed) `Prefetch` + in-Python slicing.** Rejected: fetches every related row for every parent to serve a `first: 3` page — unbounded over-fetch that gets *worse* as data grows; the window is the entire point of the upstream design.
- **Prefetch onto the relation accessor (no `to_attr`).** Rejected: collides with the list sibling under `"both"` (Django's duplicate-lookup error at best, silently windowed list data at worst).
- **Per-alias windows for aliased nested connections with divergent pagination.** Rejected for `0.0.9`: each alias would need its own `to_attr` and the resolver has no per-alias dispatch; the divergent-alias shape falls back per-parent ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)).
- **Porting upstream's `SliceMetadata` arithmetic by hand.** Rejected: the helper is the engine's own (`strawberry.relay.utils`), already a load-bearing dependency of the shipped connection field; re-implementing it invites drift.

### Decision 5 — Resolver-side fast path with annotation-presence detection and a per-parent fallback

`_build_relation_connection_resolver`'s resolver body gains one branch ahead of the pipeline: probe `getattr(root, "_dst_<field>_connection", None)`. When it is a list whose rows carry `_dst_row_number` / `_dst_total_count`, build the connection **from the rows**:

- edges via the generated connection class's edge type, cursors `to_base64(<prefix>, _dst_row_number - 1)` — byte-compatible with Strawberry's offset cursors, so a client can hand a fast-path `endCursor` to a fallback-path `after:` and vice versa;
- `pageInfo.hasPreviousPage = first_row._dst_row_number > 1`, `pageInfo.hasNextPage = last_row._dst_row_number < last_row._dst_total_count` (empty list → both `False`, cursors `None`);
- `totalCount` (when the target's [`Meta.connection`][glossary-metaconnection] opted in and the field is selected) from `_dst_total_count` — read row-side, no `COUNT` query; an empty window with `totalCount` selected resolves `0` without a query (the parent had no related rows);
- the instance is constructed through the same `_connection_type_for(target_type)` class as the pipeline path, so SDL identity, the `first`+`last` guard, and the `totalCount` member shape are shared.

When the attribute is absent, or present without the annotations, the shipped per-parent pipeline runs unchanged — correctness never depends on the plan having fired (no optimizer installed, strictness off, a fallback shape from [Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only), a consumer's own prefetch: all degrade to today's behavior).

Justification:

- Annotation-presence probing is upstream's own integrity check (its `resolve_optimized_connection_by_prefetch` falls back on `AttributeError`); pairing it with the package-reserved `to_attr` removes the need for upstream's queryset-config flag and `_clone` monkeypatch entirely.
- The fast path skips visibility / filter / order **by construction, not by trust**: visibility is baked into the windowed child queryset at plan time (same as every generated prefetch child), and sidecar input can never reach the fast path because sidecar-carrying selections are never window-planned ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)).
- Pagination-argument consistency is structural: the window was computed from the *same selection's* resolved arguments the resolver receives, so cursors and `pageInfo` derived from row numbers agree with what the pipeline would have produced.

Alternatives considered (and rejected):

- **A context-stash handshake** (the walker records windowed paths on `info.context`; the resolver checks the stash instead of the rows). Rejected: a second source of truth that can desynchronize from what Django actually prefetched (e.g. a consumer-stripped prefetch); the rows themselves are the ground truth.
- **Re-running the pipeline over the prefetched rows.** Rejected: `FilterSet` / queryset operations on a materialized list are impossible without re-querying — which is the N+1 again; the fallback exists for exactly the shapes that need the pipeline.
- **Raising when annotations are missing.** Rejected: missing annotations are a *cooperation* outcome (consumer prefetch won, optimizer absent), not an error; upstream warns-and-falls-back, the package falls back silently and lets strictness ([Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)) be the policy voice.

### Decision 6 — Fallback shapes: sidecar input, divergent aliases, hints, `pageInfo`-only

Four nested-connection shapes are deliberately **not** window-planned in `0.0.9`; each resolves per-parent through the shipped pipeline (and is therefore visible to strictness as unplanned):

1. **Sidecar input** (`filter:` / `orderBy:` arguments on the nested selection). Baking sidecar application into plan-time child querysets means request-scoped input values inside cached plans and `FilterSet.apply_sync`'s `info`-dependence at walk time — a real design surface (input normalization, permission gates, cache-key explosion) deferred whole. The fallback is functionally identical to the shipped behavior.
2. **Aliased duplicates with divergent pagination arguments** (`a: booksConnection(first: 2)` + `b: booksConnection(first: 5)`). One `to_attr` cannot serve two windows; per-alias windows are a follow-up. Identical-argument aliases merge fine (the walker's alias merge already unions response keys) and ARE window-planned.
3. **[`OptimizerHint.SKIP`][glossary-optimizerhint] on the underlying relation.** SKIP means "the optimizer leaves this relation alone"; that contract extends to the relation's connection sibling. The other hint shapes (`select_related()` is invalid for many-side anyway; `prefetch_related()` / `prefetch(obj)`) apply to the **list-shaped** planning only and neither suppress nor shape the window — a consumer `Prefetch(obj)` hint targets the accessor, the window targets the `to_attr`, no collision.
4. **`pageInfo`-only selections** (no `edges { node }` children). Rare, and the window's value is mostly the node rows; planning a row-less window for `pageInfo` alone is dead weight against its test surface. Falls back.

Justification: every fallback is the *shipped* behavior — this card strictly adds planned shapes, never changes unplanned ones — so the matrix is monotonic: no query that works today changes results or stops working. Strictness visibility of the fallbacks is deliberate and consistent: an unplanned per-parent access **is** an N+1, whatever the reason, and the shipped strictness contract already treats deliberate skips (e.g. `SKIP`-hinted relations) as flaggable. The remediation story for sidecar-input fallbacks under `"raise"` is recorded in [Risks and open questions](#risks-and-open-questions).

Alternatives considered (and rejected):

- **Exempting fallback shapes from strictness** (stash them as pseudo-planned). Rejected: would make `"raise"` lie about a real per-parent pattern; strictness exists to surface exactly this, and the consumer's recourses (drop the nested filter, restructure, lower strictness in that test) are all visible ones.
- **Windowing sidecar-filtered connections with `cacheable = False` plans.** Rejected for `0.0.9`: still requires `apply_sync` at walk time with a synthesized request context — the deferred design surface, not just a cache flag.

### Decision 7 — Plan-cache key hygiene: nested pagination variables hash, root pagination arguments do not

[`_build_cache_key`][extension] gains a second variable-collection pass: walk the operation (and reachable fragments) for `first` / `last` / `before` / `after` arguments whose value is a variable reference **on non-root field nodes**, and fold those variables' values into the existing `relevant_vars` frozenset.

- **Why nested values must key the cache**: Slice 1 bakes the resolved values into windowed prefetch querysets. Two requests sharing a printed AST (`booksConnection(first: $n)`) but differing in `$n` would otherwise share one cached plan — and serve one request's page size to the other. This is a correctness rule, not an optimization.
- **Why root values must not**: a root connection's pagination happens post-plan in `ConnectionExtension`; plan content is invariant in them. Hashing them would fragment B1's cache across every page of every consumer pagination loop — the card's "skip pagination args that do not affect selection shape".
- **The collection is a syntactic superset by design**: any non-root field's pagination-named variable is collected, including on fields that are not connections (a custom resolver with a `first:` arg). Over-collection costs duplicate cache entries for identical plans (cheap, bounded by the LRU); under-collection serves wrong data. The same asymmetry argument the directive-variable collection already encodes.
- **Inline literals** already key the cache via the printed AST — for nested windows that is now load-bearing (two literal `first:` values genuinely need two plans); for root arguments it remains a pre-existing, harmless fragmentation, recorded in [Risks and open questions](#risks-and-open-questions).

Justification: the smallest change that makes windowed plans cache-safe while preserving B1's "variable filtering" property (variables that cannot affect the plan stay out of the key). The cache-key function stays static-shaped (one more frozenset contribution), so the memoized printed-AST fast path is untouched.

Alternatives considered (and rejected):

- **Mark every windowed plan `cacheable = False`.** Rejected: nested connections are the hot path this card exists to optimize; uncacheable plans re-walk per request and forfeit B1 exactly where it matters most. (Plans whose child querysets bake a request-scoped `get_queryset` are *already* uncacheable — that shipped rule is untouched and orthogonal.)
- **Resolve which non-root fields are genuinely connections before collecting.** Rejected: requires model/registry context inside the AST walk (the key must be computable before the walker runs); the superset rule is strictly safer and simpler.
- **Normalize root pagination literals out of the printed AST** (de-fragment the cache). Rejected: rewriting the printed document for key purposes risks collapsing genuinely distinct operations; recorded as a possible future refinement, not scoped.

### Decision 8 — Strictness-mode wiring for connection paths

The synthesized relation connection resolver fires the B3 contract when **all three** hold: a strictness sentinel is stashed (`DST_OPTIMIZER_PLANNED` present — an optimizer ran with `strictness != "off"`), the field's resolver key (declaring type + generated field name + runtime path, the shared `resolver_key` vocabulary) is not in the planned set, and the fast-path `to_attr` is absent on `root` (the access will actually query). Then: `OptimizerError` under `"raise"`, logged warning under `"warn"` — by parameterizing [`types/resolvers.py::_check_n1`][resolvers] (the probe attribute and probe semantics become arguments) rather than duplicating its logic in `connection.py`.

Justification:

- **Closes the documented hole**: [`spec-032`][spec-032] Revision 6 P2 established that nothing implements strictness for connections and assigned the wiring here; the `_build_relation_connection_resolver` docstring's "Deliberately ABSENT" block names this card.
- **The three-condition guard reproduces the list-relation semantics exactly**: planned → silent; prefetch-served → silent (no lazy load happens); unplanned-and-will-query → flag. False positives are structurally excluded the same way `_check_n1`'s cache probes exclude them.
- **Root connections need nothing**: planned whenever an optimizer is installed (Current state); sentinel absent otherwise.

Alternatives considered (and rejected):

- **Wiring strictness into `_pipeline_sync` for ALL connections (root included).** Rejected: a root connection with no optimizer installed has no sentinel (no-op), and with one installed is always planned — the root check could never fire; adding it is dead code with per-request cost.
- **A separate `connection.py`-local checker.** Rejected: two implementations of one contract drift; `_check_n1` already carries the exact probe/flag/raise shape and the parameterization is mechanical.

### Decision 9 — The `edges { node }` selection helpers consolidate into the walker

`_named_children`, `_node_children_with_runtime_prefix`, `_with_runtime_prefix`, and `_converted_selection_included` move from [`optimizer/extension.py`][extension] to [`optimizer/walker.py`][walker]; `extension.py` imports them from the walker, and `_connection_node_child_selections` (the root-seam `selection_extractor` entry point) stays in `extension.py` as a thin composition.

Justification: Slice 1's `_plan_connection_relation` must unwrap a nested connection selection's `edges { node }` with the same fragment-aware, directive-aware, runtime-prefix-carrying semantics the root seam uses — one implementation or two drifting ones. The import direction is forced: `extension` already imports from `walker`; the reverse is a cycle. [`TODO-ALPHA-035-0.0.10`][kanban]'s G3 (fragment `type_condition` narrowing) names these same helpers as the seam it will extend — consolidating now means G3 patches one site, and is part of why that card sequences itself after this one.

Alternatives considered (and rejected): **A third module (`optimizer/selections.py`).** Rejected: the card pins the bounded-extension posture ("No new subpackage; touches `walker.py` / `plans.py` / `extension.py`"); the walker is the selection-normalization home (its `_should_include` / `_included_field_selections` / `_merge_aliased_selections` already live there) and the helpers are walker vocabulary.

### Decision 10 — The products connections-only conversion lands with this card

Slice 6 replaces the four products root list resolvers with `DjangoConnectionField`s (the cookbook mirror) and re-pins the live products suite, including the three `test_products_optimizer_*` SQL-shape dogfooding tests, through the connection shape.

Justification:

- **The card pins it twice**: "Land the products list->connection replacement together with this card", and the deferral rationale (converting earlier would have regressed the optimizer dogfooding) dissolves the moment Slices 1–2 land. Per the [`docs/SPECS/NEXT.md`][next] prefer-the-card rule, the conversion is in scope here even though [`TODO-BETA-051-0.1.5`][kanban] (fakeshop activation) also names it — the boundary: **this card takes exactly the root-field shape change and its test re-pinning; `051` keeps everything else** (root `node(id:)` / `nodes(ids:)` entry points, any `Meta.connection` opt-ins, further Layer-3 activation). The overlap is recorded in [Risks and open questions](#risks-and-open-questions) for the maintainer to reconcile on the `051` card body.
- **It is the strongest live proof this card can have**: products is the optimizer-dogfooding surface; if the conversion lands with the SQL-shape pins intact (same query counts through `edges { node }`), the card's "no regression" DoD is demonstrated against the package's own most adversarial example, and the cookbook parity story (`all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)`, no list resolvers) becomes literally true in the example project.
- **Minimal shape**: no `Meta.connection` additions (products connections ship without `totalCount`, like the cookbook), no root Node fields, no model or sidecar changes. The four types' relation-connection siblings already exist live (the `032` implicit default) and simply start planning.

Alternatives considered (and rejected):

- **Defer the conversion to `051` entirely.** Rejected: contradicts the card's explicit sequencing note, and would leave this card's live SQL-shape proof confined to the library graph (M2M-only nested shapes; products adds the reverse-FK depth-2 shapes the dogfooding tests pin).
- **Keep the list resolvers alongside the connections** (additive, no churn). Rejected: the cookbook mirror is connections-only and the card says "replacement"; carrying both indefinitely doubles the live surface and the example stops modeling a real consumer choice. Recorded as the fallback if the test churn proves larger than estimated.

### Decision 11 — Module and test-file locations

- **Source:** no new module. [`optimizer/walker.py`][walker] gains the recognition branch, `_plan_connection_relation`, and the consolidated selection helpers ([Decision 9](#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker)); [`optimizer/plans.py`][plans] gains `apply_window_pagination` and the hoisted deterministic-order helper (`_ends_in_unique_column` + the pk-append rule move from [`connection.py`][connection], which imports them back — plan vocabulary lives in `plans.py`, and the walker must not import from `connection.py`); [`optimizer/extension.py`][extension] gains the cache-key pagination-variable collection; [`connection.py`][connection] gains the fast path and the strictness consultation; [`types/definition.py`][definition] gains the `relation_connections` slot; [`types/finalizer.py`][finalizer] writes it. This satisfies the card's bounded-extension pin ("No new subpackage; touches `walker.py` / `plans.py` / `extension.py` + mirrored tests") with the two additions the card's file list already implies (`connection.py` is on the card's list as "future `django_strawberry_framework/connection.py`" — it now exists; the definition/finalizer touch is the metadata recording without which the DoD's no-internals rule is unsatisfiable).
- **Tests:** mirrored per [`docs/TREE.md`][tree] — [`tests/optimizer/test_walker.py`][test-opt-walker] (recognition + planning), [`tests/optimizer/test_plans.py`][test-opt-plans] (window helper + order hoist), [`tests/optimizer/test_extension.py`][test-opt-extension] (cache key + no-regression), [`tests/test_relay_connection.py`][test-relay-connection] (fast path, fallbacks, strictness — the relation-connection surface file [`spec-032`][spec-032] established), [`tests/test_connection.py`][test-connection] (root-connection no-regression), live: [`test_library_api.py`][test-library] (Slice 5) and [`test_products_api.py`][test-products] (Slice 6). No new test file.

Justification: every change lands where its subsystem already lives and tests where that subsystem already tests; the card's file list is honored and merely completed with the metadata seam.

Alternatives considered (and rejected): **`optimizer/window.py` for the pagination helpers.** Rejected per the bounded-extension pin; `plans.py` is the plan-application module and the window is plan application.

### Decision 12 — Version bumps are owned by the joint `0.0.9` cut

No slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. CHANGELOG bullets land under `[Unreleased]`. The `0.0.8` → `0.0.9` bump is owned by the **joint cut** releasing this card together with the shipped [`DONE-029-0.0.9`][kanban] / [`DONE-030-0.0.9`][kanban] / [`DONE-031-0.0.9`][kanban] / [`DONE-032-0.0.9`][kanban]. As the cohort's last open card, this card's completion is what *makes the cut cuttable* — but cutting is the maintainer's act, not a slice.

Justification: the exact precedent [`spec-032`][spec-032] Decision 13, [`spec-031`][spec-031] Decision 12, [`spec-030`][spec-030] Decision 13, and [`spec-029`][spec-029] Decision 11 set; [`docs/SPECS/NEXT.md`][next] Step 6 mandates this Decision when multiple cards share the target patch version. The on-disk version is still `0.0.8`; the `0.0.9`-tagged surfaces ship under `[Unreleased]` against the unchanged version.

Alternatives considered (and rejected): **Bump in Slice 7 since this is the cohort's last card.** Rejected: the cut is a maintainer release act (version files, lock, CHANGELOG heading promotion, tag) with its own checklist; folding it into a card slice would couple the release to a PR merge.

## Implementation plan

The card ships as **six functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; 1→2 are foundation-first, 3 and 4 build on 1–2, 5 on 2, 6 on 2–5. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — plan-side foundation: helpers consolidation, synthesis metadata, walker recognition, windowed `Prefetch` | [`optimizer/walker.py`][walker] (helpers in + `_plan_connection_relation`), [`optimizer/plans.py`][plans] (`apply_window_pagination` + order-rule hoist), [`optimizer/extension.py`][extension] (import shuffle only), [`connection.py`][connection] (order-rule import-back), [`types/definition.py`][definition] (`relation_connections` slot), [`types/finalizer.py`][finalizer] (slot write), [`tests/optimizer/test_walker.py`][test-opt-walker] + [`tests/optimizer/test_plans.py`][test-opt-plans] (extend) | ~16 (recognition via definition slot; windowed-prefetch plan content incl. `to_attr` / annotations / slice filters / deterministic order; first/after, last-only reverse, literal + variable args; recursion two-level; fallback non-planning ×4; connector + ordering columns in `only()`; helper-move no-regression) | `+420 / -60` |
| 2 — resolver fast path | [`connection.py`][connection] (fast-path branch + row-derived connection build), [`tests/test_relay_connection.py`][test-relay-connection] (extend) | ~12 (fast-path single-query pin; wire parity vs pipeline path — edges/cursors/pageInfo/totalCount; cursor cross-path round-trip; empty window; totalCount-0-no-query; annotations-missing fallback; consumer-prefetch fallback; optimizer-absent fallback) | `+180 / -20` |
| 3 — plan-cache key hygiene | [`optimizer/extension.py`][extension] (`_build_cache_key` pagination-variable collection), [`tests/optimizer/test_extension.py`][test-opt-extension] (extend) | ~6 (nested `first: $n` distinct plans per value; root `first: $n` shared plan; mixed; fragment-carried nested args; superset rule pin; B1 hit-path no-regression) | `+90 / -5` |
| 4 — strictness wiring | [`connection.py`][connection] (sentinel consultation), [`types/resolvers.py`][resolvers] (`_check_n1` parameterization), [`tests/test_relay_connection.py`][test-relay-connection] + [`tests/optimizer/test_extension.py`][test-opt-extension] (extend) | ~7 (planned→silent; window-served→silent; unplanned `"raise"`→`OptimizerError`; `"warn"`→log; `"off"`/no-optimizer→no-op; sidecar-fallback flags; list-relation `_check_n1` no-regression) | `+80 / -15` |
| 5 — live library SQL-shape coverage | [`test_library_api.py`][test-library] (extend) | ~4 (two-level nested fixed query count independent of parent count; nested `totalCount` no per-parent COUNT; visibility-filtered nested window honors `BookType.get_queryset`; wire parity with the shipped behavior pins) | `+120 / -10` |
| 6 — products connections-only conversion | [`products-schema`][products-schema] (Query rewrite), [`test_products_api.py`][test-products] (suite re-pin) | ~0 new / ~all re-pinned (every list assertion → `edges { node }`; the three `test_products_optimizer_*` query-count pins intact through connections; filter/order denial gates re-pinned on synthesized args; nested relation-connection shapes on the products graph) | `+260 / -240` |
| 7 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+120 / -60` |

Total expected delta: ~1,100 lines net-positive across six functional slices plus the wrap — at the top of the card's M sizing; the size pressure and its fallback (Slice 6 splits into a same-cut fast-follow) are recorded in [Risks and open questions](#risks-and-open-questions). No version-file edits ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

Staged-but-not-implemented seams follow the [`AGENTS.md`][agents] design-doc anchor discipline: a source-site `TODO(spec-033 Slice N)` comment naming this spec and the owning slice (e.g. Slice 1's planned-but-unconsumed window carries `TODO(spec-033 Slice 2)` at the resolver seam), paired with `NotImplementedError` where a call path must fail loudly, removed in the change that ships the slice.

## Edge cases and constraints

- **`"both"` shape with both siblings selected** — the list field's accessor-keyed prefetch and the connection's `to_attr` window coexist on one relation with no Django duplicate-lookup error; the list field returns the **full** related set, the connection returns the windowed page. Pinned by a dedicated test.
- **Identical-argument aliases merge; divergent ones fall back.** The walker's alias merge already unions response keys and runtime prefixes; the planner compares resolved pagination arguments across merged aliases and windows only when they agree ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)).
- **Recursion terminates structurally.** A windowed child plan may itself contain a windowed prefetch (the two-level cookbook shape); depth is bounded by the validated query depth, the same bound the walker already rides.
- **`first: 0`** — a zero-limit window (`row_number <= 0` matches nothing); the fast path serves empty edges with `totalCount` still correct only when rows exist to carry the annotation — and with zero rows prefetched the count is `0` by construction either way. Pinned.
- **Parents with no related rows** — empty `to_attr` list; empty-window semantics above. No fallback triggered (the empty list IS the window result).
- **`last`-only backward pagination** — the reversed-row-number window (upstream's `reverse` branch); `before` + `last` combinations that the offset arithmetic cannot push down fall back per-parent rather than approximating. The exact supported set follows `SliceMetadata`'s arithmetic and is pinned by tests, not prose.
- **`relay_max_results` agreement** — the plan-time cap is read from the schema config (available at request time; the walker runs per-request) so a window can never be narrower or wider than the resolve-time cap; a consumer raising the cap via [`strawberry_config`][glossary-strawberry_config]`(relay_max_results=...)` affects both sides through the one config object.
- **Visibility-filtered targets** — the windowed child queryset bakes the target's [`get_queryset`][glossary-get_queryset-visibility-hook] (plan `cacheable = False`, the shipped request-scope rule); row numbers and `_dst_total_count` are computed **post-visibility**, so a nested `totalCount` counts visible rows only — identical to the pipeline path's post-`get_queryset` count. The live Slice-5 test pins this through `BookType`'s `circulation_status="repair"` filter.
- **Consumer cooperation (B8)** — a consumer `Prefetch` on the relation accessor and the window's `to_attr` prefetch are distinct lookups; `diff_plan_for_queryset`'s exact-match and absorption rules see different keys and never merge them. A consumer who prefetches **the `to_attr` name itself** is writing into the package-reserved `_dst_` namespace — explicitly unsupported, documented, not guarded.
- **FK-id elision and `only()` inside windows** — child plans are ordinary plans: nested forward-FK `{ id }`-only selections elide, scalar projections apply, connector and ordering columns are force-included so the partition and `ORDER BY` never hit deferred-field refetches. Window annotations are annotations — they compose with `.only()`.
- **Multi-database** — the windowed child queryset follows the shipped generated-`Prefetch` alias rule (it does NOT inherit the root alias; [Multi-database cooperation][glossary-multi-database-cooperation] axis 3); window functions execute on whatever alias the child queryset resolves to.
- **Plan immutability** — the windowed `Prefetch` rides `append_prefetch_unique` and the finalize-to-tuple discipline; cached windowed plans are copied before diffing like every plan (B1 cache-immutability property, re-affirmed by the Slice-3 tests).
- **Backend floor** — window functions with `QuerySet.filter` against them require Django ≥ 4.2 and a window-capable backend; the package floor is `Django>=5.2` and every supported CPython bundles SQLite ≥ 3.25, so no conditional path ships. A consumer on an exotic backend without window support gets that backend's `NotSupportedError` — surfaced, not swallowed; recorded in [Risks and open questions](#risks-and-open-questions).
- **The outer `totalCount` predicate stays direct-children-scoped** — a nested connection's `totalCount` must not fire the outer connection's count (`_total_count_requested` already checks direct children only; re-affirmed by a Slice-2 test now that nested `totalCount` is common).
- **No existence/behavior change for unplanned shapes** — every fallback resolves byte-identically to today's pipeline output; the fallback tests assert wire parity, not just non-error.

## Test plan

Tests live across the package-internal `tests/` tree and the `examples/fakeshop/test_query/` tree, per [`docs/TREE.md`][tree], [`AGENTS.md`][agents], and the coverage rule in [`examples/fakeshop/test_query/README.md`][test-query-readme]: **any package coverage line reachable by a real GraphQL query against the fakeshop schema MUST be earned in `test_query/`, the first place to add a test** — fall back to the package tree only when the path is genuinely unreachable from a live `/graphql/` request. Concretely for this card:

- **Live-first (Slices 5–6).** The fixed-query-count nested-connection pins, the nested-`totalCount` no-extra-COUNT pin, the visibility-filtered window, and the entire re-pinned products suite run live over `django.test.Client.post("/graphql/", ...)`, riding the `_reload_project_schema_for_acceptance_tests` fixture pattern (clear the global registry, reload app schemas, reload `config.schema` / `config.urls`).
- **Package-only where live is genuinely unreachable**, with the reason pinned per family: plan-content assertions (plans are package-internal objects); the fallback non-planning matrix (divergent aliases / `SKIP` hints / `pageInfo`-only need synthetic shapes the fakeshop graph and suite don't carry); cache-key identity assertions (cache internals); strictness `"raise"` / `"warn"` (the fakeshop project schema runs strictness-off); reverse-FK and `"connection"`-narrowed relation-connection variants (cardinality fixtures); the `_check_n1` parameterization (deliberately unplanned synthetic types).
- **No-regression gates.** The existing B1–B8 suites in [`tests/optimizer/`][test-opt-extension], the root-connection planning pins in [`tests/test_connection.py`][test-connection], and the [`spec-032`][spec-032] behavior pins in [`tests/test_relay_connection.py`][test-relay-connection] / [`test_library_api.py`][test-library] all stay green untouched except where a pin's premise legitimately changes (the products list-shape pins, Slice 6) — each such change is a re-pin, never a deletion.

### Slice 1 — `tests/optimizer/test_walker.py` + `tests/optimizer/test_plans.py` (extend)

- `test_relation_connections_slot_recorded` — synthesis writes `{"books_connection": "books"}` onto the declaring definition; suppressed shapes (`"list"`, non-Node target, consumer-authored) record nothing.
- `test_nested_connection_planned_as_windowed_prefetch` — plan contains `Prefetch(accessor, to_attr="_dst_books_connection")` whose queryset carries `_dst_row_number` / `_dst_total_count` annotations, the slice filters, and the deterministic order (pk-terminal).
- `test_window_slice_from_first_after_literals` / `..._from_variables` — resolved values drive offset/limit; variables resolve through `info.variable_values`.
- `test_window_last_only_uses_reversed_row_number` — the reverse branch.
- `test_window_respects_relay_max_results`.
- `test_nested_connection_two_level_recursion` — a window inside a window (the cookbook shape) plans both levels.
- `test_child_plan_projections_include_connector_and_ordering_columns`.
- `test_fallback_not_planned_sidecar_input` / `..._divergent_aliases` / `..._skip_hint` / `..._pageinfo_only` — no window, no `planned_resolver_keys` entry.
- `test_identical_alias_args_merge_and_plan`.
- `test_visibility_target_window_flips_cacheable_false`.
- `test_planned_resolver_keys_include_connection_field`.
- `test_apply_window_pagination_unit` (plans.py) — annotation names, partition, range filters, reverse; `test_deterministic_order_helper_hoist_parity` — the hoisted rule answers identically to the previous `connection.py` implementation.
- Helper-move no-regression: the existing root-extraction tests in [`tests/optimizer/test_extension.py`][test-opt-extension] pass unmodified after the consolidation.

### Slice 2 — `tests/test_relay_connection.py` (extend)

- `test_fast_path_single_query` — parent page + one window query, zero per-parent queries (query-count pin over a multi-parent fixture).
- `test_fast_path_wire_parity_with_pipeline` — identical `edges` / cursors / `pageInfo` / `totalCount` for the same data resolved with and without the optimizer installed.
- `test_fast_path_cursor_round_trips_to_fallback_after` — a fast-path `endCursor` fed to `after:` on an optimizer-less execution continues correctly (offset-format compatibility).
- `test_fast_path_total_count_from_annotation_no_query` / `test_fast_path_empty_window_total_count_zero`.
- `test_fallback_when_annotations_missing` — a consumer's own accessor prefetch (no `_dst_` attr) → pipeline path, correct results.
- `test_fallback_when_no_optimizer_installed` — pre-card behavior byte-identical.
- `test_outer_total_count_predicate_ignores_nested_total_count` (re-affirmation, now that nested `totalCount` is common).

### Slice 3 — `tests/optimizer/test_extension.py` (extend)

- `test_nested_pagination_variable_keys_cache` — same document, `$n=2` vs `$n=5` → two plans, two windows.
- `test_root_pagination_variable_shares_cache` — root `first: $n` varying → one cached plan.
- `test_mixed_root_and_nested_pagination_variables` — only the nested one keys.
- `test_fragment_carried_nested_pagination_variable_collected`.
- `test_pagination_var_collection_is_syntactic_superset` — a non-connection nested field with `first: $n` also keys (the documented over-collection).
- B1 no-regression: hit/miss counters, LRU promotion, immutability — existing tests untouched.

### Slice 4 — `tests/test_relay_connection.py` + `tests/optimizer/test_extension.py` (extend)

- `test_strictness_raise_unplanned_nested_connection` — strictness `"raise"`, optimizer installed, fallback shape → `OptimizerError` naming the generated field.
- `test_strictness_warn_logs_once_per_occurrence`.
- `test_strictness_silent_when_window_served` / `..._when_planned` / `..._when_off` / `..._no_optimizer`.
- `test_sidecar_fallback_is_flagged` — the [Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only) consistency pin.
- `_check_n1` parameterization no-regression: the existing list-relation strictness suite passes unmodified.

### Slice 5 — `examples/fakeshop/test_query/test_library_api.py` (extend; live)

- `test_nested_books_connection_fixed_query_count` — the two-level genres→books query executes in a fixed query count with 3 genres and with 10 genres (the per-parent independence pin).
- `test_nested_total_count_no_per_parent_count` — selecting nested `totalCount` adds zero queries over the same selection without it.
- `test_nested_window_respects_book_visibility` — `circulation_status="repair"` books excluded from non-staff nested pages AND nested `totalCount`; staff sees them.
- The shipped behavior pins (`test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`) stay green unmodified — wire results must not change.

### Slice 6 — `examples/fakeshop/test_query/test_products_api.py` (re-pin; live)

- Every root-field assertion rewrites list-shape → `edges { node }`; semantic expectations (rows, ordering, filter/order narrowing, the `check_name_permission` denial gates on the synthesized `filter:` / `orderBy:` arguments) carry over one-to-one.
- `test_products_optimizer_merges_duplicate_root_field_nodes_over_http` / `..._prefetches_nested_reverse_fk_depth_2_over_http` / `..._selects_nested_forward_fk_depth_2_over_http` — re-pinned through the connection wrapper with their query-count assertions intact (the card's regression fence).
- New: one nested relation-connection shape on the products graph (`allCategories { edges { node { itemsConnection(first: N) { edges { node } } } } }`) with the fixed-query-count pin — the reverse-FK windowed shape the library graph (M2M-only) cannot express live.

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 7's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 7 grants that permission**; the Slice 7 maintainer prompt must name the `CHANGELOG.md` edits explicitly so an agent does not infer permission from a standing document.

- **Slice 7 — GLOSSARY**
  - [`docs/GLOSSARY.md`][glossary]: flip [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] to `shipped (0.0.9)` and rewrite its body (the windowed-prefetch mechanism, the fast path, the fallback matrix, the strictness contract); sweep the pre-`033` caveats out of [`DjangoConnectionField`][glossary-djangoconnectionfield] ("the derived plan is **empty**" / "strictness does not flag" sentences), [`Meta.relation_shapes`][glossary-metarelation_shapes] (the per-parent caveat; the `SyncMisuseError` async caveat **stays** — async pipeline is still out of scope), [Strictness mode][glossary-strictness-mode] (connections now participate), and [Plan cache][glossary-plan-cache] (the variable-filtering property gains the nested-pagination clause). **No net-new entries** — this card ships no new public symbol or `Meta` key, so the terms CSV needs no entry this flow cannot anchor.
- **Slice 7 — package docs**
  - [`docs/README.md`][docs-readme]: the "Coming next" `0.0.9` line empties (the in-progress remainder was this card); the optimizer shipped-surface bullet gains the connection-aware clause.
  - [`docs/TREE.md`][tree]: refresh the `walker.py` / `plans.py` / `extension.py` / `connection.py` one-line descriptions for the moved helpers and the window planning.
  - [`TODAY.md`][today]: the products-centric sections rewrite for the connections-only Query (the "What's in `products/schema.py` today" sample, the optimized-queries section's root shape, the filtering/ordering examples' argument site) — products remains the canonical demonstration vehicle, now in its cookbook-mirror shape; the "what products is still waiting for" list stays scoped to permissions / Layer-3 keys.
  - [`README.md`][readme]: update the status paragraph's newest-shipped-surface line (connection-aware optimizer planning closes the `0.0.9` story).
  - [`CHANGELOG.md`][changelog]: `### Added` bullets under `[Unreleased]` for connection-aware planning (windowed nested-connection prefetches + the annotation fast path), strictness coverage of connection paths, and the pagination-aware plan-cache keys; a `### Changed` bullet for the products example's connections-only conversion. No version-heading promotion (per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).
- **Slice 7 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`WIP-ALPHA-033-0.0.9`][kanban] to Done with the next `DONE-NNN-0.0.9` id; confirm the spec reference points at `docs/spec-033-connection_optimizer-0_0_9.md` (a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`, not a hand edit); reconcile the [`TODO-BETA-051-0.1.5`][kanban] card body's products-conversion sentence (now landed here) per [Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card). No version-file edits.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **Card-premise staleness (root-connection planning already shipped).** The card body and the [`DjangoConnectionField`][glossary-djangoconnectionfield] glossary entry both still say a `0.0.9` connection derives an empty plan; on disk the root half is implemented and tested ([Current state](#current-state)). Preferred answer ([Decision 2](#decision-2--card-scope-boundary-what-already-shipped-what-this-card-ships)): scope this card to the nested remainder and let Slice 7 sweep the stale prose. Fallback: none needed — the DoD items are all satisfiable under the narrowed reading; this item exists so the conflict is called out rather than silently reconciled (the [`docs/SPECS/NEXT.md`][next] boundary rule).
- **Products-conversion ownership overlap with [`TODO-BETA-051-0.1.5`][kanban].** Both the card ("land together with this card") and `051`'s body (the fakeshop-activation deferral note) name the products list→connection conversion. Preferred answer ([Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card)): this card takes exactly the root-field replacement + test re-pin; Slice 7's wrap updates `051`'s body to drop the conversion sentence and keep the rest (root Node fields, further activation). Fallback: if the maintainer prefers `051` to keep the conversion, Slice 6 is cleanly severable — Slices 1–5 satisfy the card's other three DoD items, and the library + cardinality fixtures still cover the DoD's "fakeshop or the cardinality fixture" disjunction.
- **Size pressure on an M card.** Six functional slices and a ~1,100-line delta sit at the top of M. Preferred answer: hold the card together — Slices 1–2 are one mechanism split for reviewability, 3–4 are small, and 6 is churn-not-design. Fallback: split Slice 6 into a fast-follow PR landing in the same joint cut (the cut, not the card, is the user-visible boundary — [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).
- **Strictness `"raise"` vs. sidecar-filtered nested connections.** A consumer who legitimately filters a nested connection gets a per-parent fallback that strictness flags, and the in-`0.0.9` remediations are query-side (drop the nested filter, restructure) or strictness-side (lower the mode in that test) — there is no per-field exemption knob. Preferred answer ([Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only)): keep the honest flag; an [`OptimizerHint.SKIP`][glossary-optimizerhint] on the relation suppresses planning *and* is a deliberate consumer signal, but it does not exempt strictness today and this card does not change that. Fallback: if dogfooding shows the flag is unbearable, a `SKIP`-exempts-strictness amendment is a two-line, separately-decidable change — record it on the `035` hardening card rather than rushing it here.
- **Window-function backend support.** The mechanism assumes a window-capable backend; the package floor (`Django>=5.2`, bundled SQLite ≥ 3.25) covers every supported configuration, but an exotic third-party backend without window support will raise its own `NotSupportedError` inside an optimized query. Preferred answer: document in the GLOSSARY entry (Slice 7) and let the error surface — the consumer's recourse is `relation_shapes = {"<field>": "list"}` or running without the optimizer. Fallback: a capability probe (`connection.features.supports_over_clause`) that skips window planning per-alias — deferred until a real consumer hits it (tested-usage discipline).
- **Root pagination literals still fragment the plan cache.** Inline `first: 2` vs `first: 3` at the root produce distinct printed-AST keys for identical plans — pre-existing, harmless, and unfixed by this card (variables, the pagination-loop case that matters, are already key-invariant at the root and stay so). Preferred answer: accept and record. Fallback: printed-AST normalization of root pagination literals — a separate, riskier change ([Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not) records why it was rejected here).
- **Root `totalCount` stays a second query.** The nested `totalCount` rides the window; the root one keeps the shipped selection-gated `.count()`. Preferred answer ([Non-goals](#non-goals)): one `COUNT` per root connection is not an N+1; don't churn a shipped contract mid-cohort. Fallback: a partition-less `Count` window on the root path (upstream's shape) as a post-`0.0.9` micro-optimization — BACKLOG-worthy, not cut-blocking.
- **`before`/`last` combinations the offset arithmetic cannot push down.** The reversed-window branch covers `last`-only; some `before`+`last` shapes may not map cleanly onto a pushed-down window. Preferred answer: window what `SliceMetadata`'s arithmetic expresses; fall back per-parent for the rest (monotonic-safety — fallbacks are today's behavior), with tests pinning the exact supported set. Fallback: none needed — the fallback IS the safety net.
- **Estimated products test churn.** [`test_products_api.py`][test-products] is the largest live suite; the list→connection rewrite touches most of it mechanically. Preferred answer: accept (the assertions are shape rewrites, not semantic changes; the [`spec-031`][spec-031]/[`spec-032`][spec-032] Slice-4/6 churn precedent). Fallback: the Slice-6 severability above.

## Out of scope (explicitly tracked elsewhere)

- **Optimizer robustness hardening (G1–G3)** — evaluated-queryset guard, operation-type `only()` gating, fragment `type_condition` narrowing: [`TODO-ALPHA-035-0.0.10`][kanban], sequenced after this card on the same walker seams.
- **Permissions subsystem** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions] / [Per-field permission hooks][glossary-per-field-permission-hooks]) — [`TODO-ALPHA-034-0.0.10`][kanban].
- **The rest of the fakeshop products / Relay activation** (root `node(id:)` / `nodes(ids:)` on products, `Meta.connection` opt-ins, Layer-3 keys) — [`TODO-BETA-051-0.1.5`][kanban].
- **Windowed planning for sidecar-filtered nested connections and per-alias windows** — follow-up design surfaces named in [Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only); no card yet, surfaced for the maintainer at wrap time.
- **`Meta.cursor_field` keyset cursors and the "Relay magic" differentiators** — [`BACKLOG.md`][backlog] item 39.
- **`search:` argument** — [`Meta.search_fields`][glossary-metasearch_fields], `0.1.2` ([`TODO-BETA-046-0.1.2`][kanban]).
- **Async connection pipeline** — unowned beyond the [`Meta.relation_shapes`][glossary-metarelation_shapes] caveat; the [`SyncMisuseError`][glossary-syncmisuseerror] contract is unchanged by this card.
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all six functional slices' items plus the wrap are satisfied. The card's own four DoD bullets map onto items 1 (spec), 2–4 (walker recognition without internals), 8–10 (cookbook-shape tests against fakeshop and the cardinality fixtures), and 12 (no B1–B8 regression).

**Spec + companion CSV**

1. `docs/spec-033-connection_optimizer-0_0_9.md` (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion `spec-033-connection_optimizer-0_0_9-terms.csv` anchoring every project-specific term that has a [`docs/GLOSSARY.md`][glossary] heading; `uv run python scripts/check_spec_glossary.py --spec docs/spec-033-connection_optimizer-0_0_9.md` reports `OK: <N> terms`. This card introduces no net-new glossary symbol, so no term is intentionally absent.

**Slice 1 — plan-side foundation**

2. The `edges { node }` selection helpers live in [`optimizer/walker.py`][walker] with `extension.py` importing them; the root-extraction suite passes unmodified ([Decision 9](#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker)).
3. [`DjangoTypeDefinition`][definition] carries `relation_connections`, written by the Phase-2.5 synthesis; suppressed shapes record nothing ([Decision 3](#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing)).
4. The walker plans every recognized nested connection as a windowed `Prefetch` under `_dst_<field>_connection` — child plan with visibility / projections / recursion, deterministic order shared with the pipeline via the hoisted helper, slice window from resolved arguments capped by `relay_max_results`, `_dst_row_number` / `_dst_total_count` annotations, resolver keys recorded — and leaves the four [Decision 6](#decision-6--fallback-shapes-sidecar-input-divergent-aliases-hints-pageinfo-only) fallback shapes unplanned. [`tests/optimizer/test_walker.py`][test-opt-walker] / [`test_plans.py`][test-opt-plans] cover the slice.

**Slice 2 — fast path**

5. The synthesized relation connection resolver serves edges / cursors / `pageInfo` / `totalCount` from the window annotations through the same generated connection class, with wire parity against the pipeline path, cursor cross-path compatibility, and silent fallback when the window is absent ([Decision 5](#decision-5--resolver-side-fast-path-with-annotation-presence-detection-and-a-per-parent-fallback)). One window query per relation per request; zero per-parent queries on the fast path. [`tests/test_relay_connection.py`][test-relay-connection] covers the slice.

**Slice 3 — cache keys**

6. Nested pagination variables key the plan cache; root pagination variables do not; the superset collection rule and the B1 properties (hit/miss, LRU, immutability) are pinned ([Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not)). [`tests/optimizer/test_extension.py`][test-opt-extension] covers the slice.

**Slice 4 — strictness**

7. An unplanned, unserved nested-connection access fires `OptimizerError` / a warning per the mode through the parameterized `_check_n1`; planned, window-served, strictness-off, and optimizer-absent paths are silent; the list-relation strictness suite passes unmodified ([Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)).

**Slice 5 — live library coverage**

8. The library suite pins the two-level nested-connection fixed query count (parent-count-independent), the nested-`totalCount` zero-extra-queries property, and the visibility-filtered window — with the shipped behavior pins unmodified.

**Slice 6 — products conversion**

9. The products `Query` is connections-only (the cookbook mirror); the synthesized `filter:` / `orderBy:` arguments carry the existing denial-gate semantics; no root Node fields are added ([Decision 10](#decision-10--the-products-connections-only-conversion-lands-with-this-card)).
10. The three `test_products_optimizer_*` SQL-shape pins hold through `edges { node }` with their query counts intact, and the products graph gains a live reverse-FK nested-connection fixed-count pin.

**Slice 7 — doc + card-completion wrap**

11. [`docs/GLOSSARY.md`][glossary] flips [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] to shipped and sweeps the pre-`033` caveats; [`docs/README.md`][docs-readme] / [`docs/TREE.md`][tree] / [`TODAY.md`][today] / [`README.md`][readme] reflect the shipped surface and the reshaped products example; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the bullets (the explicit per-card permission grant named in the Slice 7 maintainer prompt); [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.9` with the spec reference pointing at this file (kanban DB + re-render) and `051`'s body reconciled.
12. **No version bump lands in this card** per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut): `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.9` cut owns the bump). No regression in the B1–B8 plan-cache and queryset-diff coverage, the root-connection planning coverage, or the shipped `spec-032` behavior pins.
13. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; worker-local validation is `uv run ruff format .` and `uv run ruff check --fix .`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoconnection]: GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-filter_input_type]: GLOSSARY.md#filter_input_type
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-metaconnection]: GLOSSARY.md#metaconnection
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metaoptimizer_hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metarelation_shapes]: GLOSSARY.md#metarelation_shapes
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-optimizerhint]: GLOSSARY.md#optimizerhint
[glossary-order_input_type]: GLOSSARY.md#order_input_type
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-queryset-diffing]: GLOSSARY.md#queryset-diffing
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-schema-audit]: GLOSSARY.md#schema-audit
[glossary-strawberry_config]: GLOSSARY.md#strawberry_config
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-002]: SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-029]: SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-031]: SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-032]: SPECS/spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py
[context]: ../django_strawberry_framework/optimizer/_context.py
[definition]: ../django_strawberry_framework/types/definition.py
[extension]: ../django_strawberry_framework/optimizer/extension.py
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[plans]: ../django_strawberry_framework/optimizer/plans.py
[resolvers]: ../django_strawberry_framework/types/resolvers.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-connection]: ../tests/test_connection.py
[test-opt-extension]: ../tests/optimizer/test_extension.py
[test-opt-plans]: ../tests/optimizer/test_plans.py
[test-opt-walker]: ../tests/optimizer/test_walker.py
[test-relay-connection]: ../tests/test_relay_connection.py

<!-- examples/ -->
[products-schema]: ../examples/fakeshop/apps/products/schema.py
[test-library]: ../examples/fakeshop/test_query/test_library_api.py
[test-products]: ../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
