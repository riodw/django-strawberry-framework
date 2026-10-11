# Rationale companion: spec-033 (Connection-aware optimizer planning)

This file carries each Decision's justification and the alternatives it rejected; [`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`][spec-033] carries the contract.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-033-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention ([`docs/SPECS/NEXT.md`][next]) bakes the card number and target patch into the filename: `033` and `0_0_9`.
- The topic slug `connection_optimizer` is the card's own suggested stem and names the subject precisely: the optimizer's connection awareness.

### Alternatives considered (and rejected)

- **The card's own `docs/spec-connection_optimizer.md`.** Rejected: it does not follow the structured convention.
- **Folding the plan into the connection-field spec ([`spec-030`][spec-030]).** Rejected: that spec owns a different card; one card, one spec.
- **Topic slug `connection_aware_planning` or `optimizer_connections`.** Rejected: longer without being more precise.

## Decision 2 — Card-scope boundary: what already shipped, what this card ships

Spec: [Decision 2 — Card-scope boundary: what already shipped, what this card ships][spec-033-d2].

### Justification

Root-connection `edges { node }` extraction (`optimizer/extension.py::apply_connection_optimization` with the `_connection_node_child_selections` extractor) predates this card, so the card's scope is the nested half: windowed relation-connection prefetches, pagination-aware cache keys, strictness wiring, and the live SQL-shape and products-conversion proof. Building the root half again would duplicate shipped, tested code, and every card bullet and DoD item is satisfiable under the narrowed reading.

### Alternatives considered (and rejected)

- **Treating the root-connection extraction as part of this card.** Rejected: that work predates the spec, so claiming it would make the slice checklist describe changes this card did not make.

## Decision 3 — Walker recognition is definition-metadata-driven, not name-pattern guessing

Spec: [Decision 3 — Walker recognition is definition-metadata-driven, not name-pattern guessing][spec-033-d3].

### Justification

- **The card's DoD demands it**: the walker recognizes connection shapes without reaching into `DjangoConnectionField` internals. A definition slot is the channel the walker already reads for `field_map`, `optimizer_hints`, and relation targets, so it adds no coupling.
- **One name-normalization path**: model fields and synthesized connections resolve through the same selection-name resolver (`optimizer/walker.py::_resolve_selection_target`): the exact `snake_case` reversal first, then forward maps built from Strawberry's authoritative field names through the active schema name converter, which covers lossy transforms (an underscore before a digit) and explicit GraphQL names.
- **Name-pattern guessing is wrong twice.** Stripping a `_connection` suffix misfires on a consumer field that merely ends in `_connection`, and fires for relations whose synthesis was suppressed (`"list"` narrowing, consumer-authored relation, non-Node target). The synthesis already computed the true mapping; recording it costs one dict.
- **Finalization is the right write point**: relation targets are settled before the relation-connection synthesis runs, and the definition is the per-type record every other synthesis product already writes to.
- **Nested recognition follows the primary-type contract.** Nested levels resolve their definition through `optimizer/walker.py::_resolve_field_map` with no `source_type`, so `registry.get(model)` returns the model's primary `DjangoType` and the walker reads the primary's `relation_connections` slot. That is correct by construction for `field_map`, but `relation_shapes` is a per-type opt-in, so a secondary `DjangoType` that shapes a relation differently from the primary would be recognized against the wrong slot. A divergent secondary type is therefore out of scope for windowed planning: it resolves per-parent and stays visible to strictness, pinned by `test_secondary_type_relation_shapes_nested_recognition`.

### Alternatives considered (and rejected)

- **Reading `connection.py`'s connection-type cache or the synthesized-field marker at plan time.** Rejected: the internals coupling the DoD forbids, and field objects are not reachable from the walker's `(model, field_map)` vocabulary.
- **Suffix-stripping with a field-map existence check.** Rejected: still misfires on suppressed synthesis. A `"list"`-narrowed relation has a real `books` entry but no connection sibling, so planning a window for it would do dead work and record wrong resolver keys.

## Decision 4 — Windowed-prefetch planning under a package-reserved `to_attr`

Spec: [Decision 4 — Windowed-prefetch planning under a package-reserved `to_attr`][spec-033-d4].

### Justification

- **The mechanism is upstream's**, adapted to the package's two structural differences: the plan cache (which forces the cacheability and key-hygiene rules of [Decision 7](#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not)) and the `"both"` relation shape (which forces the `to_attr`).
- **Window functions need no capability branch.** Every database backend Django ships supports them at the package's Django floor. A third-party backend without them raises its own `NotSupportedError` inside the optimized query; `relation_shapes = {"<field>": "list"}` or running without the optimizer is the recourse.
- **The deterministic order is a cursor-parity invariant.** The window's `ORDER BY` comes from the same `optimizer/plans.py::deterministic_order` helper the resolve-time pipeline uses, and `optimizer/plans.py::apply_window_pagination` also applies `order_by` to the queryset, because the window sets only the row-number values, not the order Django hands instances to `to_attr`. If plan-time and resolve-time order diverge, a fast-path `endCursor` stops round-tripping to an optimizer-less `after:`, a silent, data-dependent failure.
- **The count is conditional.** `_dst_total_count` is annotated only when the page's selection can observe a count; a plain `first: N` page that selects `pageInfo { hasNextPage }` without `totalCount` answers it from an n+1 sentinel row instead, and an edges-only page needs neither. One `utils/connections.py::FetchMode` value per window, derived at plan time and consumed at resolve time, keeps planner and resolver agreeing about which annotations exist.
- **Unwindowable child querysets are classified once, on the base queryset** (`optimizer/nested_fetch.py::unwindowable_child_queryset_reason`). SQL evaluates window functions before `DISTINCT`, so `Count(1) OVER (PARTITION BY ...)` over-counts a de-duplicated child queryset, and a visibility `get_queryset` that joins and de-duplicates is a normal shape. Leaving such a relation unplanned keeps `totalCount` right; a per-parent re-count would reintroduce the N+1. Classifying the base queryset makes the gate strategy-independent, so no fetch backend needs its own post-build re-check.
- **The partition comes from the raw Django relation field.** The forward-M2M reverse query name lives only on `field.remote_field`, which `FieldMeta` does not carry, so the planner hands the live field to `optimizer/join_taxonomy.py::classify_relation_join`. The classifier returns `windowable=False` rather than raising, so an unsupported relation kind, or a reverse `ForeignObject` whose link spans more than one carrier column (no single partition expression exists), is left unplanned instead of guessed at.
- **The `to_attr` grammar avoids `__`.** The per-response-key form `_dst_<field>$<key>_connection` uses `$` because Django splits `prefetch_to` on `LOOKUP_SEP`. Django accepts several `Prefetch`es on one accessor as long as their `to_attr`s differ, which is what lets divergent aliases plan one window each.
- **The cap is one number.** The plan-time and resolve-time caps both come from `utils/connections.py::resolve_relay_max_results` (`relay_max_results`, lowered by the request policy's `max_page_size` when smaller), so the window and the pipeline cannot disagree about the page ceiling.

### Alternatives considered (and rejected)

- **A plain (unwindowed) `Prefetch` plus in-Python slicing.** Rejected: fetches every related row for every parent to serve a `first: 3` page, an over-fetch that grows with the data.
- **Prefetching onto the relation accessor (no `to_attr`).** Rejected: collides with the list sibling under `"both"`, Django's duplicate-lookup error at best and silently windowed list data at worst.
- **Porting upstream's `SliceMetadata` arithmetic by hand.** Rejected: `strawberry.relay.utils.SliceMetadata` is the engine's own helper, already a dependency of the connection field; a copy invites drift. Only the keyset vocabulary derives its own bounds (`utils/connections.py::derive_keyset_window_bounds`), because `SliceMetadata` cannot parse a value cursor.

## Decision 5 — Connection-class fast path with annotation-presence detection and a per-parent fallback

Spec: [Decision 5 — Connection-class fast path with annotation-presence detection and a per-parent fallback][spec-033-d5].

### Justification

- **Annotation presence is upstream's own integrity check** (its `resolve_optimized_connection_by_prefetch` falls back on a missing annotation). Paired with the package-reserved `to_attr`, it needs no queryset-attached optimization flag and no `QuerySet._clone` monkeypatch: the rows themselves say whether a window served them.
- **The probe reads the row number only** (`connection.py::_window_rows_are_annotated`). The count is conditional ([Decision 4](#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr)), so demanding it would refuse every count-free page and every strategy that synthesizes row numbers without a count.
- **The fast path skips visibility, filter, and order by construction**: visibility is baked into the windowed child queryset at plan time like every generated prefetch child, and sidecar-carrying selections are never window-planned ([Decision 6](#decision-6--refusal-arms-divergent-aliases-hints-and-scalar-only-connections)). The resolver's sidecar-kwargs guard is a belt against a planner/argument desync: it refuses the window rather than serve unfiltered rows.
- **Cursor parity is recomputed, not trusted.** Strawberry's `ConnectionExtension.resolve` consumes `first` / `last` / `before` / `after` and forwards them only to `resolve_connection`, so the resolver cannot classify its rows. `resolve_connection` re-derives the bounds through the same `utils/connections.py` helper the walker planned with, and `_dst_row_number` stays the forward row number for every window, so the offset cursor is `_dst_row_number - 1` throughout and matches `ListConnection`'s cursors directly.
- **The marker carries a `fallback` callable** because `resolve_connection` cannot rebuild the per-parent relation manager the resolver holds.
- **Marker rows keep the ambiguous-empty shapes in one query.** Keeping each partition's row 1 lets `first: 0` and an overshot `after:` distinguish an empty page from a childless parent without a per-parent fallback, and makes an empty rows list proof that the parent has no children.
- **`last: 0` is rewritten to `first: 0`** (`utils/connections.py::page_arguments`) because Strawberry's `edges[-0:]` slices to the whole set, which would serve every edge past the page cap.
- **One `resolve_connection`.** `connection.py::DjangoConnection.resolve_connection` is the single override every generated connection class inherits, and the `totalCount` opt-in is a class attribute, so the count handling cannot drift away from the window handling.

### Alternatives considered (and rejected)

- **A context-stash handshake** (the walker records windowed paths on `info.context`; the resolver checks the stash instead of the rows). Rejected: a second source of truth that can desynchronize from what Django actually prefetched, for example when a consumer prefetch wins; the rows are the ground truth.
- **Carrying slice metadata on the `_WindowedConnectionRows` marker.** Rejected: the resolver never receives the pagination arguments, and recomputing the bounds at resolve time through the plan-time helper is the stronger parity guarantee.
- **Building the connection in `_build_relation_connection_resolver`.** Rejected: Strawberry wraps `relay.connection(...)` fields with `ConnectionExtension`, which feeds the resolver's return value to `resolve_connection` as the node iterable; a prebuilt connection would be treated as nodes.
- **Re-running the pipeline over the prefetched rows.** Rejected: `FilterSet` and queryset operations on a materialized list need a re-query, which is the N+1 again.
- **Raising when annotations are missing.** Rejected: missing annotations are a cooperation outcome (a consumer prefetch won, or no optimizer ran), not an error. The package falls back silently and leaves the policy voice to strictness ([Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)).

## Decision 6 — Refusal arms, divergent aliases, hints, and scalar-only connections

Spec: [Decision 6 — Refusal arms, divergent aliases, hints, and scalar-only connections][spec-033-d6].

### Justification

- **Every refusal arm resolves through the per-parent pipeline**, which is correct for every shape, so planning is a performance layer and correctness never depends on it firing.
- **A whole-relation refusal stays visible to strictness on purpose**: an unplanned per-parent access is an N+1 whatever the reason, and strictness already treats deliberate skips (`OptimizerHint.SKIP`) as flaggable. The flag's message carries the fallback reason so it reads as actionable.
- **Two granularities**: a per-response-key refusal (sidecar input, a window the slice arithmetic cannot express) leaves one alias unplanned while its siblings keep their windows. A whole-relation refusal applies where no key can be served safely, for example two argument payloads merged onto one response key, which have no single correct window.
- **A refusal leaks nothing into the parent plan.** The child plan is built against a throwaway `sub_plan` and absorbed only once at least one key planned, so a refused relation records no resolver key, FK-id elision, or `cacheable` flip.
- **Scalar-only connections are planned.** A `pageInfo`-only or `totalCount`-only selection needs the per-parent row-number and count metadata but no node columns, so the window is projected to pk, connector (every attach column), and deterministic-order columns (`optimizer/nested_planner.py::_project_scalar_only_window`), and `"raise"` does not turn harmless connection metadata into a per-parent error.
- **A `to_attr`-bearing prefetch hint on a generated relation is refused at plan time** with a `ConfigurationError`: Django lands `to_attr` rows on that attribute instead of the prefetch cache the generated resolver reads, so accepting the hint would mark the relation planned while every row still lazy-loads. A consumer-assigned resolver owns the attribute contract and may hint one.

### Alternatives considered (and rejected)

- **Exempting fallback shapes from strictness** (recording them as pseudo-planned). Rejected: `"raise"` would lie about a real per-parent pattern; the consumer's recourses (drop the nested filter, restructure, lower strictness in that test) are all visible ones.
- **Windowing sidecar-filtered connections in `cacheable = False` plans.** Rejected: it still needs `FilterSet` application at walk time with a request context, input normalization and permission gates, a design surface a cache flag does not cover.

## Decision 7 — Plan-cache key hygiene: nested pagination variables hash, root pagination arguments do not

Spec: [Decision 7 — Plan-cache key hygiene: nested pagination variables hash, root pagination arguments do not][spec-033-d7].

### Justification

The smallest change that makes windowed plans cache-safe while keeping variables that cannot affect the plan out of the key. The key stays static-shaped (one more frozenset contribution), so the memoized printed-AST path is untouched. Paginating a nested connection changes `after:` on every page, so each page is its own cache entry; that is correctness, and the LRU bounds the memory.

### Alternatives considered (and rejected)

- **Marking every windowed plan `cacheable = False`.** Rejected: nested connections are the hot path the card optimizes, and uncacheable plans re-walk per request. Plans whose child querysets bake a request-scoped `get_queryset` are already uncacheable for that orthogonal reason.
- **Resolving which non-root fields are connections before collecting.** Rejected: needs model and registry context inside the AST walk, and the key must be computable before the walker runs; the syntactic superset over-collects safely (duplicate entries for identical plans) where under-collection would serve wrong data.
- **Normalizing root pagination literals out of the printed AST.** Rejected: inline root `first: 2` and `first: 3` produce distinct keys for identical plans, which is harmless, while rewriting the printed document for key purposes risks collapsing genuinely distinct operations.

## Decision 8 — Strictness-mode wiring for connection paths

Spec: [Decision 8 — Strictness-mode wiring for connection paths][spec-033-d8].

### Justification

- **The synthesized connection resolver is the only place the access happens**, so without this wiring a per-parent nested-connection access goes unflagged while the same query shaped as a list relation fails under `"raise"`.
- **The three conditions reproduce list-relation semantics**: planned is silent, window-served is silent (no query happens), unplanned-and-will-query is flagged. False positives are excluded the same way `_check_n1`'s cache probes exclude them.
- **Strictness is read from the per-execution `ContextVar` first.** The `DST_OPTIMIZER_STRICTNESS` stash is unavailable to an execution without a `context_value` and is written only when a plan publishes, so an operation whose root the walker cannot plan never writes it; reading only the stash would leave a configured guard silently disarmed. "Planned" likewise accepts the stash or the per-execution scoped-relations set that every execution publishes.
- **The key uses the relation field name and the declaring type.** The resolve-time `resolver_key(declaring_type, relation_field_name, runtime_path)` must match the walker's emission, and the message names the `books` relation a consumer can act on, byte-uniform with the list-relation message. The finalizer passes the iterated type, not the model's primary, so a divergent secondary type's never-planned connection stays flagged ([Decision 3](#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing)).
- **Union publication preserves the parent's sentinels.** Nested fallback pipelines are real optimizer runs; overwriting `DST_OPTIMIZER_PLANNED` or `DST_OPTIMIZER_FK_ID_ELISIONS` would break the parent's strictness and FK-id elision after the nested connection returns, which matters most under `"warn"`, where execution continues.
- **Root connections need nothing**: with an optimizer installed they are always planned, and without one there is no strictness to consult.

### Alternatives considered (and rejected)

- **Strictness in `_pipeline_sync` for every connection, root included.** Rejected: the root check could never fire, so it would be dead code with per-request cost.
- **A separate `connection.py`-local checker.** Rejected: two implementations of one contract drift; `types/resolvers.py::_check_n1` already carries the probe, flag, and raise shape, and the parameterization is mechanical.

## Decision 9 — The `edges { node }` selection helpers consolidate into one module both consumers import

Spec: [Decision 9 — The `edges { node }` selection helpers consolidate into one module both consumers import][spec-033-d9].

### Justification

The nested planner must unwrap a connection selection's `edges { node }` with the same fragment-aware, directive-aware, runtime-prefix-carrying semantics as the root seam: one implementation or two drifting ones. The helpers belong to neither consumer, so `optimizer/selections.py` imports neither `walker.py` nor `extension.py` and both import from it, which removes the import-direction constraint instead of working around it. `_connection_node_child_selections` stays in `extension.py` as a thin composition supplying the root response path.

### Alternatives considered (and rejected)

- **Hosting the helpers in `extension.py`.** Rejected: `extension.py` imports `walker.py`, so the walker importing them back is a cycle.
- **Hosting them in `walker.py`.** Rejected: the AST seam in `extension.py` would depend on the planner module for selection vocabulary, coupling two consumers that need only the shared primitives.

## Decision 10 — The products connections-only conversion lands with this card

Spec: [Decision 10 — The products connections-only conversion lands with this card][spec-033-d10].

### Justification

- **Converting earlier would have regressed the optimizer dogfooding**, and the card binds the conversion to itself. The boundary with the Fakeshop GraphQL schema activation card ([`KANBAN.md`][kanban]): this card takes exactly the root-field shape change and its test re-pinning; that card keeps the root `node(id:)` / `nodes(ids:)` entry points and the `totalCount` opt-in.
- **It is the strongest live proof**: products is the optimizer-dogfooding surface, so the `test_products_optimizer_*` SQL-shape pins holding through `edges { node }` demonstrates the no-regression DoD against the package's most adversarial example, and the cookbook mirror (connections only, no list resolvers) is literally true in the example project.
- **Minimal shape**: no [`Meta.connection`][glossary-metaconnection] additions (products connections ship without `totalCount`), no root [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield], no model or sidecar changes. The four types' relation-connection siblings already exist and simply start planning.
- **The re-pin is not purely mechanical.** A list resolver returns every row; a connection with no `first` / `last` returns at most `relay_max_results` (default 100) and gains the deterministic `ORDER BY pk`. `relay_max_results` is a hard ceiling: Strawberry's `SliceMetadata.from_arguments` raises for any `first:` above it, so for a larger collection the only faithful assertion is the capped page in pk order. The failure mode is a silently truncated result that still parses, which is why the products pins assert the visible set stays under the cap.

### Alternatives considered (and rejected)

- **Deferring the conversion to the fakeshop activation card.** Rejected: contradicts the card's sequencing, and leaves the live SQL-shape proof confined to the library graph's M2M shapes; products adds the reverse-FK depth-2 shapes the dogfooding tests pin.
- **Keeping the list resolvers beside the connections.** Rejected: the cookbook mirror is connections-only, and carrying both doubles the live surface while the example stops modeling a real consumer choice.

## Decision 11 — Module and test-file locations

Spec: [Decision 11 — Module and test-file locations][spec-033-d11].

### Justification

Each change lands where its subsystem lives and is tested where that subsystem tests. Plan vocabulary (`apply_window_pagination`, the `_dst_*` annotation names, the deterministic-order rule) lives in `optimizer/plans.py`, which `connection.py` imports. Everything the plan side and the resolve side must agree on lives in `utils/connections.py`, a neutral module neither side owns: no optimizer module imports `connection.py` (`connection.py` imports the optimizer), so no existing module could host the shared contract without a cycle. Nested-connection planning lives in `optimizer/nested_planner.py`, which builds a private result plan and returns it only once orchestration completes, so a refusal or exception cannot leak partial directives into the walker's parent plan.

### Alternatives considered (and rejected)

- **`optimizer/window.py` for the pagination helpers.** Rejected: `plans.py` is the plan-application module, and the window is plan application.

## Decision 12 — Version bumps are owned by the joint `0.0.9` cut

Spec: [Decision 12 — Version bumps are owned by the joint `0.0.9` cut][spec-033-d12].

### Justification

`0.0.9` released this card together with the rest of its Relay cohort ([`spec-029`][spec-029], [`spec-030`][spec-030], [`spec-031`][spec-031], [`spec-032`][spec-032]), and [`docs/SPECS/NEXT.md`][next] requires this Decision when several cards share a target patch. Cutting is the maintainer's release act; the version is single-sourced in `django_strawberry_framework/__init__.py` `__version__`.

### Alternatives considered (and rejected)

- **Bumping in this card's last slice.** Rejected: the cut is a release act with its own checklist (version, lock, CHANGELOG heading, tag); folding it into a slice would couple the release to a PR merge.

## Risks and open questions

- **The strictness probe answers "the `to_attr` is present", not "the window was consumed".** [Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths)'s third condition is implemented by `types/resolvers.py::_check_n1` as `getattr(root, to_attr, None) is None`. The resolver reaches that call only after deciding not to consume what sits under the `to_attr`, which happens when the value is not a list, when its rows carry no `_dst_row_number`, or when the resolver's own sidecar kwargs are present. In those three cases the per-parent pipeline queries while the probe reads "present" as "served", so `"raise"` stays silent. Reaching it needs a consumer write into the package-reserved `_dst_` namespace (declared unsupported) or a planner/resolver sidecar desync, and no data is wrong; only the diagnostic is silent. Closing it means passing the resolver's own consume decision into `_check_n1` instead of re-probing the attribute.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../../KANBAN.md

<!-- docs/ -->
[glossary-djangonodefield]: ../../GLOSSARY.md#djangonodefield
[glossary-djangonodesfield]: ../../GLOSSARY.md#djangonodesfield
[glossary-metaconnection]: ../../GLOSSARY.md#metaconnection

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: ../spec-030-connection_field-0_0_9.md
[spec-031]: ../spec-031-globalid_encoding-0_0_9.md
[spec-032]: ../spec-032-full_relay-0_0_9.md
[spec-033-d10]: ../spec-033-connection_optimizer-0_0_9.md#decision-10--the-products-connections-only-conversion-lands-with-this-card
[spec-033-d11]: ../spec-033-connection_optimizer-0_0_9.md#decision-11--module-and-test-file-locations
[spec-033-d12]: ../spec-033-connection_optimizer-0_0_9.md#decision-12--version-bumps-are-owned-by-the-joint-009-cut
[spec-033-d1]: ../spec-033-connection_optimizer-0_0_9.md#decision-1--spec-filename-and-canonical-naming
[spec-033-d2]: ../spec-033-connection_optimizer-0_0_9.md#decision-2--card-scope-boundary-what-already-shipped-what-this-card-ships
[spec-033-d3]: ../spec-033-connection_optimizer-0_0_9.md#decision-3--walker-recognition-is-definition-metadata-driven-not-name-pattern-guessing
[spec-033-d4]: ../spec-033-connection_optimizer-0_0_9.md#decision-4--windowed-prefetch-planning-under-a-package-reserved-to_attr
[spec-033-d5]: ../spec-033-connection_optimizer-0_0_9.md#decision-5--connection-class-fast-path-with-annotation-presence-detection-and-a-per-parent-fallback
[spec-033-d6]: ../spec-033-connection_optimizer-0_0_9.md#decision-6--refusal-arms-divergent-aliases-hints-and-scalar-only-connections
[spec-033-d7]: ../spec-033-connection_optimizer-0_0_9.md#decision-7--plan-cache-key-hygiene-nested-pagination-variables-hash-root-pagination-arguments-do-not
[spec-033-d8]: ../spec-033-connection_optimizer-0_0_9.md#decision-8--strictness-mode-wiring-for-connection-paths
[spec-033-d9]: ../spec-033-connection_optimizer-0_0_9.md#decision-9--the-edges--node--selection-helpers-consolidate-into-one-module-both-consumers-import
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
