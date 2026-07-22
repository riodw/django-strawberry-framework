# Spec: `Meta.search_fields` — declarative OR'd search on connection fields

Planned for `0.1.2` (card `TODO-BETA-049-0.1.2`); **`TODO-BETA-050-0.1.2`
(Postgres full-text search filter primitives) shares this patch version and
depends on this card, so the `0.1.2` version bump belongs to the joint cut
and this spec defers every release-state artifact to it**
([Decision 10](#decision-10--joint-cut-at-012--release-state-defers-to-card-050)).
The Strawberry analogue of `django-graphene-filters`' `Meta.search_fields`:
a `DjangoType` declares a tuple of model-field paths
(`search_fields = ("name", "description", "galaxy__name")`), and every
connection field serving that type gains a single nullable `search: String`
argument. A non-empty input fans out across every declared path as one OR'd
`icontains` predicate joined into the queryset by intersection — after
visibility, alongside `filter:`, before `orderBy:`
([Decision 6](#decision-6--pipeline-position-visibility--filter--search--orderby)).
Relation paths ride Django's standard `__` lookup traversal; no custom
resolver machinery. Paths that cross a to-many relation compile
row-preserving — a correlated `EXISTS` branch through the shared
row-preserving predicate compiler, never a search-driven `.distinct()`
([Decision 7](#decision-7--row-preserving-to-many-compilation-no-search-driven-distinct)).
Relational search is visibility-aware — a hidden related row can never
qualify a visible root
([Decision 12](#decision-12--visibility-aware-relational-search)) — and
search honors the declaring type's existing FilterSet permission gates
([Decision 13](#decision-13--search-honors-filterset-permission-gates)).
Both dependencies have shipped (`DONE-027-0.0.8`
Filtering, `DONE-030-0.0.9` `DjangoConnectionField`) and the landing seams
already exist in the tree: `filters/inputs.py::LOOKUP_PREFIXES` +
`construct_search` (landed by spec-027 Decision 3 Layer 5 under a broad
future-search reservation that Slice 1 retargets to card 050) and the
`connection.py::_synthesized_signature` docstring's "The `search:` argument
is NOT generated (search is `0.1.2`)" reservation.

Status: **PLANNED — no slice built yet.**
Five slices: Slice 1 (**`filters/search.py` core** — the runtime search
compiler, the strict path-plan builder, the shared active-search predicate,
unit tests), Slice 2 (**Meta surface** — declaration-time shape validation,
the `DjangoTypeDefinition.search_fields` slot, phase-2.5 frozen search path
plan, `DEFERRED_META_KEYS` promotion), Slice 3 (**connection wiring** — the
synthesized `search:` argument, the sync/async pipeline steps,
row-preserving to-many compilation, visibility/permission composition,
guards), Slice 4 (**live fakeshop activation + composability tests** —
products forward paths, the library to-many surface, the Category
permission-gate proof), Slice 5 (**card-local docs + card wrap — version
and release marketing deferred, GLOSSARY moves to a precise intermediate
status**).

This card consumes — and is gated on — the pre-card row-preserving
predicate groundwork landing on `main` ahead of it: the structured
path-classification walker plus lookup validator in `utils/relations.py`
and the shared correlated-`EXISTS` predicate compiler in
`optimizer/predicates.py`
(which also reroutes the generated to-many leaf filters off their
`distinct=True` stamping). Search wires the `search:` surface onto that
finished engine; it does not design a compilation strategy of its own.

That groundwork is formally **this spec's pre-card slice ("Slice 0")**,
planned in [`docs/row-preserving-predicates-part1-plan.md`][part1-plan]
(Rev 6), and **this card owns its completion bookkeeping**: the
`docs/GLOSSARY.md` / `docs/TREE.md` / `KANBAN.md` fold-in for the shipped
`FilterSet` multiset-contract change, the new `optimizer/predicates.py`
module, and the `OptimizerError` predicate-attachment raise-site
documentation all wrap under this card (second Part 1 review, findings
9–10). The groundwork ships no release-state artifacts of its own.

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
without explicit permission. This card does not touch `CHANGELOG.md`; card
050's joint-cut slice must carry the maintainer's explicit grant.

---

## Key glossary references

Every project-specific symbol below is anchored in
[`docs/GLOSSARY.md`][glossary]; the companion
[`spec-049-search_fields-0_1_2-terms.csv`][search-terms]
is the audit ledger. Load-bearing entries:

- [`Meta.search_fields`][glossary-metasearch_fields] — the surface this card
  implements (card 050's joint cut owns the final shipped-release status;
  this card moves the entry to a precise intermediate status,
  [Decision 10](#decision-10--joint-cut-at-012--release-state-defers-to-card-050)).
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — where the
  `search:` argument surfaces.
- [`FilterSet`][glossary-filterset] /
  [`Meta.filterset_class`][glossary-metafilterset_class] — the sibling
  sidecar `search` composes with by intersection, and the owner of the
  `check_<field>_permission` gates search honors
  ([Decision 13](#decision-13--search-honors-filterset-permission-gates)).
- [`OrderSet`][glossary-orderset] /
  [`Meta.orderset_class`][glossary-metaorderset_class] — the downstream
  pipeline neighbor.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] /
  [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — search
  runs strictly after root visibility narrowing
  ([Decision 6](#decision-6--pipeline-position-visibility--filter--search--orderby))
  AND composes related-type visibility into every to-many hop
  ([Decision 12](#decision-12--visibility-aware-relational-search)).
- [`ConfigurationError`][glossary-configurationerror] — the raise type for
  every new declaration-time and finalize-time validation.
- [`finalize_django_types`][glossary-finalize_django_types] — phase 2.5
  hosts the frozen search path plan build.
- [Joint version cut][glossary-joint-version-cut] — why Slice 5 does NOT
  bump the version.

## Slice checklist

- [ ] **Slice 1 — `filters/search.py` core.** `apply_search_sync` /
  `apply_search_async` (the runtime queryset compilers), the internal
  `build_direct_search_q` helper, `build_search_path_plan` (the single
  strict finalize-time plan builder over the `utils/relations.py`
  classifier + lookup validator), the shared `active_search` predicate, the
  `SEARCH_MAX_LENGTH` cap, explicit rejection of the `LOOKUP_PREFIXES`
  vocabulary reserved to card 050, and unit tests under
  `tests/filters/test_search_fields.py`.
- [ ] **Slice 2 — Meta surface.** Declaration-time shape validation
  (including duplicate-path and padded-path rejection) in `types/base.py`,
  the `DjangoTypeDefinition.search_fields` + frozen-plan slots, phase-2.5
  `build_search_path_plan` in `types/finalizer.py` (assigned only after
  every path succeeds — retry-safe), promote `search_fields` from
  `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`
  ([Decision 8](#decision-8--metasearch_fields-promotes-in-this-card)).
- [ ] **Slice 3 — connection wiring.** `CONNECTION_SEARCH_KWARG` in
  `utils/connections.py`, the synthesized nullable `search: String`
  argument in `connection.py::_synthesized_signature`, the sync/async
  search steps in `_pipeline_sync` / `_pipeline_async` (visibility-aware
  and permission-gated), row-preserving to-many compilation through
  `optimizer/predicates.py`
  ([Decision 7](#decision-7--row-preserving-to-many-compilation-no-search-driven-distinct)),
  the active-search non-queryset guard extension, the combined-queryset
  preflight.
- [ ] **Slice 4 — live activation + composability.** Uncomment all four
  `search_fields` declarations in `examples/fakeshop/apps/products/schema.py`
  (fixing their stale card-number comments), add the library to-many
  surface (`GenreType` `search_fields = ("name", "books__title")` over
  `allLibraryGenresConnection`) plus the reverse-FK acceptance surface
  (`LoanType.Meta.search_fields = ("note", "book__loans__patron__email")`
  over an acceptance-only `DjangoConnectionField(LoanType)` — the shared
  Medtrics reproduction fixture, Decision 7), live HTTP tests under
  `examples/fakeshop/test_query/` covering the required-live-case list in
  the Test plan (to-many row preservation, the Category permission gate,
  related-row visibility, phrase semantics, literals, cache isolation,
  nested-connection fallback), composability tests (`search` + `filter:`,
  `search` + visibility, `search` + `totalCount`, `search` + keyset
  cursors), and the non-gating PostgreSQL plan-evidence artifact.
- [ ] **Slice 5 — card-local docs + card wrap.** Regenerate `docs/TREE.md`
  for the new module, update
  `examples/fakeshop/test_query/README.md`'s suite descriptions for the
  new live search coverage, update the glossary DB so
  [`Meta.search_fields`][glossary-metasearch_fields] reads "implemented on
  `main`; release pending the joint `0.1.2` cut" and regenerate
  `docs/GLOSSARY.md`, flip card 049 + regenerate the board. Leave
  README/docs README shipped-surface wording, GOAL/TODAY release status,
  `CHANGELOG.md`, and the version quintet untouched — all are owned by the
  `TODO-BETA-050-0.1.2` joint cut
  ([Decision 10](#decision-10--joint-cut-at-012--release-state-defers-to-card-050)).

## Problem statement

`Meta.search_fields` is one of the five `django-graphene-filters` Layer-3
Meta keys [`GOAL.md`][goal] names alongside `filterset_class` /
`orderset_class` / `aggregate_class` / `fields_class`; without it the
package cannot claim full DGF parity at `1.0.0`. Today the key sits in
`types/base.py::DEFERRED_META_KEYS` and is rejected at declaration time
with a typed [`ConfigurationError`][glossary-configurationerror], so the
[`GOAL.md`][goal] astronomy cookbook's
`search_fields = ("name", "description", "galaxy__name", "galaxy__description")`
declaration — flat names AND relation-traversal paths in one tuple —
cannot be written — the fakeshop products schema stages four commented
`search_fields` tuples that this card's Slice 4 activates (card
`TODO-BETA-055-0.1.5`, recut to the `node` / `nodes` entry points plus
`totalCount`, no longer gates them). The consumer-facing promise is small and sharp: one
declarative tuple, one generated `search: String` argument, OR'd
case-insensitive containment across every declared path, composed with
every other read-side layer without leaking rows — root or related — the
viewer cannot see.

## Current state

- `types/base.py::DEFERRED_META_KEYS` contains
  `{"aggregate_class", "fields_class", "search_fields"}`; declaring
  `Meta.search_fields` today raises the reserved-key
  [`ConfigurationError`][glossary-configurationerror]
  (`exceptions.py` names `search_fields` in its reserved-key docstring).
- `filters/inputs.py::LOOKUP_PREFIXES` (`^` → `istartswith`, `=` → `iexact`,
  `@` → `search`, `$` → `iregex`) and `filters/inputs.py::construct_search`
  landed with spec-027 Decision 3 Layer 5 under a broad future-search
  reservation. Canonical card 049 subsequently narrowed this card to basic
  OR'd `icontains`; card 050 owns the shortcut parity decision and its
  Postgres guard. Slice 1 retargets the stale reservation wording.
- `filters/sets.py::FilterSet.get_filters` carries a
  `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)` comment at
  the point where prefix translation was originally imagined to wire in.
  This spec supersedes that placement
  ([Decision 1](#decision-1--search-support-lives-in-filterssearchpy-not-inside-filterset));
  Slice 1 removes the TODO.
- `connection.py::_synthesized_signature` generates `filter:` / `orderBy:`
  keyword-only params from the type's declared sidecars and explicitly
  documents "The `search:` argument is NOT generated (search is `0.1.2`)".
  `_pipeline_sync` / `_pipeline_async` run visibility → filter → orderBy →
  `_finalize_queryset` (deterministic total order + optimizer plan).
- `utils/connections.py` pins `CONNECTION_FILTER_KWARG = "filter"` /
  `CONNECTION_ORDER_KWARG = "order_by"` and the
  `CONNECTION_SIDECAR_KWARGS` tuple. Note the tuple is currently
  **inert documentation**: the guard chain does not iterate it —
  `connection_sidecar_inputs_from_kwargs` hardcodes `.get("filter")` /
  `.get("order_by")` and `has_connection_sidecar_input` takes two
  hardcoded keyword params (`filter_input`, `order_by_input`) compared
  with `is not None`; the tuple's only other reference is an exact-value
  assertion in `tests/utils/test_connections.py`. A naive third
  `is not None` slot would classify whitespace-only search as an active
  sidecar — the presence predicate for search must be the shared
  `active_search` gate ([Decision 11](#decision-11--input-hygiene-strip-check-only-literals-stay-literal)).
- `utils/relations.py::path_traverses_to_many` answers "does this
  `__`-separated path cross a to-many hop" from model metadata with a
  process-lifetime cache; filter generation and order resolution already
  share it. The pre-card predicate groundwork widens it into the structured
  path-classification walker (hops + terminal + a separate
  `validate_lookup_expr` lookup validator + first-many index) that this
  card's frozen search path plan is built from — the walker is the ONLY
  path-acceptance oracle
  ([Decision 2](#decision-2--declaration-time-shape-validation-finalize-time-path-validation)).
- `optimizer/predicates.py` (pre-card groundwork, landing ahead of this
  card) owns the row-preserving predicate compiler: correlated `EXISTS`
  branches rooted at the outer model's `_base_manager` on the queryset's
  own database alias, `_dst_`-reserved collision-checked aliases, no
  `.distinct()`. The generated to-many leaf filters route through it in
  the same groundwork, so search and filters share one compilation story.
- `filters/sets.py` already owns the related-visibility derivation and
  permission machinery this card composes with:
  `FilterSet._derive_related_visibility_querysets_sync` / `_async` run each
  active branch's target-type `get_queryset` via
  `utils/querysets.py::apply_type_visibility_sync` / `_async` (a sync/async
  derivation split, pre-collected for async), and
  `FilterSet._run_permission_checks` fires `check_<field>_permission`
  gates for active input fields through the shared `utils/permissions.py`
  helpers (single-sited with the order side).
- `types/definition.py::DjangoTypeDefinition` carries `filterset_class` /
  `orderset_class` / `fields_class` slots; there is **no** `search_fields`
  slot yet.
- `examples/fakeshop/apps/products/schema.py` carries four commented-out
  `search_fields` declarations (Category, Item, Property, Entry) gated on
  this card (their comments cite a stale pre-renumber card ID,
  `TODO-BETA-047-0.1.2`). **All four are local or forward-FK paths — none
  crosses a to-many relation**, so they cannot by themselves earn live
  coverage of the card's defining row-preserving behavior; Slice 4 adds
  the library to-many surface for that.
- `examples/fakeshop/apps/products/filters.py::CategoryFilter.check_name_permission`
  restricts filtering by `Category.name` to staff. Search over a declared
  `name` path must honor that gate, or an anonymous caller could probe
  category names through `search:` that `filter: {name: ...}` denies
  ([Decision 13](#decision-13--search-honors-filterset-permission-gates)).
- Upstream (`/Users/riordenweber/projects/django-graphene-filters`):
  `object_type.py` accepts `search_fields` in Meta;
  `connection_field.py::search_args` adds the `search` argument when the
  node type declares the tuple and threads it to the filterset;
  `filterset.py::build_search_conditions` whitespace-splits the input,
  ORs each term across `construct_search(field)` lookups, ANDs the terms,
  and `filterset.py::get_filter_fields` ALSO injects a `search` key into
  the advanced filter input type.

## Goals

1. `Meta.search_fields = (<path>, ...)` on a
   [`DjangoType`][glossary-djangotype] — tuple or list of `str`, flat field
   names and `__`-relation paths accepted identically, validated at
   declaration (shape, duplicates, padding) and finalize (strict path
   classification + `icontains` terminal validation).
2. A single nullable `search: String` argument on every
   [`DjangoConnectionField`][glossary-djangoconnectionfield] serving a
   declaring type. Absent from SDL when the type does not declare the key.
3. Active input (non-`None`, non-whitespace, within the documented length
   cap) → one search expression OR-ing `<path>__icontains=<input>` across
   every declared path, `.filter()`-joined into the queryset. Inactive
   input → the same queryset object back (no-op).
4. Composition by intersection with `filter:`; strictly post-visibility at
   the root AND visibility-aware inside every to-many hop, so hidden rows —
   root or related — cannot be discovered by probing field values
   ([Decision 12](#decision-12--visibility-aware-relational-search)).
5. Search honors the declaring type's FilterSet `check_<field>_permission`
   gates: active search fires every applicable gate, and `Meta.search_fields`
   is the grant for paths with no corresponding gate
   ([Decision 13](#decision-13--search-honors-filterset-permission-gates)).
6. Correct row cardinality, row-preserving: a declared path that traverses
   a to-many relation compiles as a correlated `EXISTS` branch OR'd with
   the direct-path predicates — one root model row stays one SQL row, and
   search adds no `.distinct()` and no outer fan-out (on a plain root
   queryset, `totalCount` stays a flat `COUNT(*)`).
7. Promotion of `search_fields` out of `DEFERRED_META_KEYS` — the pipeline
   applies the key end-to-end in this card.

## Non-goals

- **Ranked / weighted / similarity full-text search and search-field shortcut
  prefixes.** Those are
  `TODO-BETA-050-0.1.2` (Postgres `SearchQueryFilter` / `SearchRankFilter`
  / `TrigramFilter` primitives plus the `^` / `=` / `@` / `$` parity
  watch-item), explicitly distinct from this card's basic OR'd `icontains`
  surface and gated on it.
- **A `search` key inside the `filter:` input type.** Upstream injects one
  (`filterset.py::get_filter_fields`); rejected here
  ([Decision 9](#decision-9--no-search-key-inside-the-filter-input-type)).
- **`search:` on [`DjangoListField`][glossary-djangolistfield] or the Relay
  node fields.** The card scopes the argument to connection fields; the
  list-field question is tracked in Risks.
- **Whitespace term-splitting (multi-term AND semantics).** Upstream ANDs
  whitespace-split terms; the card pins whole-input phrase semantics
  ([Decision 4](#decision-4--whole-input-phrase-semantics-one-q-object-no-term-splitting)).
- **Schema-shape changes.** [`Meta.fields`][glossary-metafields] /
  [`Meta.exclude`][glossary-metaexclude] stay the only source of the
  surfaced field set; `search_fields` never adds output fields.
- **A search-specific permission hook** (`check_search_permission` or
  per-path variants). Search reuses the existing FilterSet gate family
  ([Decision 13](#decision-13--search-honors-filterset-permission-gates));
  a dedicated hook would be a second permission truth for the same fields
  and no card owns one.
- **Per-connection or request-time search-scope variation.** DRF's
  `SearchFilter.get_search_fields(view, request)` lets each view action
  expose a different field list; this card deliberately does not
  translate that dynamism —
  [Decision 14](#decision-14--search-scope-is-type-definition-wide-and-immutable)
  pins the declared tuple as immutable, type-definition-wide metadata.

## Borrowing posture

[Single-upstream parity][glossary-single-upstream-parity] surface: the only
upstream shipping this shape is `django-graphene-filters` (verified in
`object_type.py`, `connection_field.py`, `filterset.py`, and the cookbook's
`recipes/schema.py`), and the consumer-facing contract —
[Cookbook parity][glossary-cookbook-parity] — is that an unprefixed
graphene-era `search_fields` tuple carries over verbatim when the import line
changes. Prefix-bearing declarations belong to card 050.
Element classification:

- **Borrowed verbatim**: the Meta key name and tuple-of-paths shape; the
  single nullable `search: String` argument name and type; `icontains` as
  the sole lookup; Django `__` traversal for relation paths.
- **Engine-adapted**: argument generation moves from graphene's
  `Field.args` property merge to this package's synthesized-resolver
  signature (`connection.py::_synthesized_signature`, spec-030 Decision 6:
  the resolver signature IS the SDL contract); application moves from the
  filterset's `qs` property to dedicated sync/async pipeline steps
  ([Decision 1](#decision-1--search-support-lives-in-filterssearchpy-not-inside-filterset)),
  because this package's `FilterSet.apply_sync` / `apply_async` entry
  points are transactional form surfaces, not a form `qs` property —
  search shares their visibility and permission machinery through the
  single-sited helpers, not by riding their form pipeline.
- **Deliberately diverged**: no whitespace term-splitting
  ([Decision 4](#decision-4--whole-input-phrase-semantics-one-q-object-no-term-splitting));
  no request/action-dependent search scope — the declared tuple is
  immutable type-definition metadata, where DRF's `SearchFilter` offers
  `get_search_fields(view, request)` dynamism
  ([Decision 14](#decision-14--search-scope-is-type-definition-wide-and-immutable));
  no `search` key duplicated into the filter input type
  ([Decision 9](#decision-9--no-search-key-inside-the-filter-input-type));
  no `.distinct()` at all — upstream applies one unconditionally after
  filtering, this package compiles row-multiplying paths as correlated
  `EXISTS` branches so the fan-out never exists
  ([Decision 7](#decision-7--row-preserving-to-many-compilation-no-search-driven-distinct));
  relational search is visibility-aware and permission-gated — upstream
  traverses raw relations
  ([Decision 12](#decision-12--visibility-aware-relational-search),
  [Decision 13](#decision-13--search-honors-filterset-permission-gates));
  a documented input length cap with a typed error
  ([Decision 11](#decision-11--input-hygiene-strip-check-only-literals-stay-literal));
  typo'd paths fail loudly at finalize with
  [`ConfigurationError`][glossary-configurationerror] instead of upstream's
  silent runtime `FieldError`; shortcut-prefixed declarations fail loudly
  until card 050 resolves their parity and backend-safety contract.

## User-facing API

The [`GOAL.md`][goal] astronomy cookbook shape, verbatim:

```python
class CelestialBodyNode(DjangoType):
    class Meta:
        model = models.CelestialBody
        fields = "__all__"
        interfaces = (relay.Node,)
        filterset_class = filters.CelestialBodyFilter
        orderset_class = orders.CelestialBodyOrder
        search_fields = ("name", "description", "galaxy__name", "galaxy__description")
```

Generated SDL delta on every connection field serving the type:

```graphql
celestialBodies(
  filter: CelestialBodyFilterInput
  orderBy: [CelestialBodyOrderInput!]
  search: String          # new — present only when Meta.search_fields is declared
  first: Int
  after: String
  ...
): CelestialBodyNodeConnection!
```

Semantics:

- `search: null` or omitted → no effect.
- `search: "   "` (whitespace-only) → no effect (stripped check).
- `search: "red dwarf"` → `Q(name__icontains="red dwarf") |
  Q(description__icontains="red dwarf") | Q(galaxy__name__icontains="red
  dwarf") | Q(galaxy__description__icontains="red dwarf")` applied via
  `.filter(...)` — the whole input as one phrase (to-many paths compile as
  `EXISTS` branches instead of raw `Q` traversals).
- Input longer than `SEARCH_MAX_LENGTH` (256 characters) → typed GraphQL
  error naming the cap ([Decision 11](#decision-11--input-hygiene-strip-check-only-literals-stay-literal)).
- A declared path gated by a FilterSet `check_<field>_permission` method →
  the gate fires for every active search; a denied viewer gets the gate's
  own loud error, exactly as the equivalent `filter:` input would produce
  ([Decision 13](#decision-13--search-honors-filterset-permission-gates)).
- `search_fields = ("=code",)` (or any leading `^` / `@` / `$`) raises
  [`ConfigurationError`][glossary-configurationerror] at declaration time;
  card 050 owns those shortcuts and the non-Postgres behavior of `@`.
- `search_fields = ("name", "name")` (duplicates) or `(" name",)`
  (padding) raise at declaration time
  ([Decision 2](#decision-2--declaration-time-shape-validation-finalize-time-path-validation)).
- `filter:` and `search:` in the same query intersect — the result matches
  every filter predicate AND the search OR-clause.

## Architectural decisions

### Decision 1 — Search support lives in `filters/search.py`, not inside `FilterSet`

A new sibling module `django_strawberry_framework/filters/search.py` owns
the runtime and validation surface: `apply_search_sync(queryset,
path_plan, value, info)` / `apply_search_async(...)` (the runtime queryset
compilers, [Decision 6](#decision-6--pipeline-position-visibility--filter--search--orderby)
explains the color split), the internal `build_direct_search_q(paths,
value)` helper, and `build_search_path_plan(type_name, model, paths)`
(finalize-time strict plan construction). This satisfies the card's
"argument generation lives in
`django_strawberry_framework/filters/` and reuses the same DRF-style Meta
surface and argument-factory machinery as `filterset_class`" DoD line while
keeping [`FilterSet`][glossary-filterset] untouched: search needs no input
type and no form validation, and a type with no `filterset_class` at all
must still get a working `search:` argument. Search DOES need related
visibility and permission composition
([Decision 12](#decision-12--visibility-aware-relational-search),
[Decision 13](#decision-13--search-honors-filterset-permission-gates)) —
it takes both from the same single-sited helpers the FilterSet consumes
(`utils/querysets.py::apply_type_visibility_sync` / `_async`,
`utils/permissions.py`), not by routing through `FilterSet.apply_sync`'s
transactional form machinery, which would couple search to the presence
and shape of a filterset.

**`apply_search_*` is the complete runtime contract** — it receives the
current queryset, the frozen path plan, and the raw input, and returns a
queryset. It returns the original queryset **by identity** for inactive
input, builds direct `Q` branches via `build_direct_search_q`, builds and
attaches the to-many `EXISTS` branches through `optimizer/predicates.py`,
applies the final OR once, and contains no Strawberry or connection logic.
A `Q`-only signature (`build_search_q(search_fields, value)`, an earlier
revision of this spec) is rejected as the public contract: it cannot carry
the queryset/database alias the correlated inner root needs, cannot host
alias allocation, and if it emitted raw `Q(genres__name__icontains=v)`
traversals it would reintroduce the exact outer fan-out the card removes.
`build_direct_search_q` survives only as the internal direct-branch
helper and must never be presented as the search compiler.

Alternatives rejected:

- **Wire `construct_search(all_filters)` inside `FilterSet.get_filters`**
  (the placement the `filters/sets.py` TODO comment sketches): that seam
  translates prefixed *filter names*, but `search_fields` is a
  type-level Meta key, not a FilterSet declaration — a type with no
  `filterset_class` at all must still get a working `search:` argument.
  Slice 1 deletes the TODO and records the supersession in the module
  docstring.
- **A `SearchSet` sidecar class** mirroring `FilterSet` / `OrderSet`:
  over-engineering for a tuple of strings. There is no per-field
  declaration body, no input type, no inheritance story worth a class.
  Upstream agrees — `search_fields` is a bare Meta tuple there too.

### Decision 2 — Declaration-time shape validation, finalize-time path validation

`types/base.py` validates shape when the class body executes: the value
must be a tuple or list of non-empty `str`, an **empty tuple raises**
— declaring the key with zero paths is a misconfiguration, not a no-op
(the silent-degradation posture this package consistently rejects) — an
**exact duplicate path raises** (redundant predicates/aliases/parameters
are a declaration bug, not something to silently deduplicate), and a path
with **leading or trailing whitespace raises** with an immediate
corrective message (a padded model path must never be silently stripped
or allowed to fail later with a less useful resolution error). A
declaration beginning with any key in
`filters/inputs.py::LOOKUP_PREFIXES` raises at declaration time with a
message that assigns shortcut support to card 050; it must never be
treated as a literal model-field name or escape to a backend error. The
validated tuple lands on a new
`types/definition.py::DjangoTypeDefinition.search_fields` slot
(`tuple[str, ...] | None = None`, normalized from list input).

Path resolution — does `galaxy__name` actually reach a searchable field —
waits for [`finalize_django_types`][glossary-finalize_django_types] phase
2.5, after `apps.populate()` has resolved lazy FK strings
([Definition-order independence][glossary-definition-order-independence]).
**There is exactly one acceptance oracle**:
`build_search_path_plan(type_name, model, paths)` calls the strict
structured classifier in `utils/relations.py` exactly once per unique
path — classifying the model path, rejecting a relation-terminal path
(search needs a concrete field to apply `icontains` to), and validating
`icontains` against the classified terminal via the groundwork's
`validate_lookup_expr` (existence of a model field does not prove
`<field>__icontains` is portable; accepted terminal families are pinned
in Edge cases). Any failure raises
[`ConfigurationError`][glossary-configurationerror] naming the type, the
offending path, the failing segment, and the model — the typo-guard
message discipline every Meta-key gate in `types/base.py` follows. The
completed immutable plan is assigned to the definition **only after every
path succeeds**, keeping partial-finalization retry safe.
`django_filters.utils.get_model_field` is deliberately NOT used — a
second resolution oracle would disagree with the classifier on `pk`,
relation terminals, generic relations, transforms, and error shape, and
every declaration would be walked twice under two contracts.

Alternative rejected: **validate paths at declaration time** — breaks
string-lazy FK targets and duplicates the finalize-time app-registry
guarantee the filter converter already relies on.

### Decision 3 — The argument is synthesized, nullable, and gated on the declaration

`utils/connections.py` gains `CONNECTION_SEARCH_KWARG = "search"` and adds
it to `CONNECTION_SIDECAR_KWARGS`. `connection.py::_synthesized_signature`
appends a keyword-only `search: str | None = None` parameter exactly when
`definition.search_fields` is non-`None` — the same
declared-sidecar-only discipline `filter:` / `orderBy:` follow (spec-030
Decision 6: the synthesized resolver signature is the SDL contract). No
declaration → no argument in SDL, matching upstream's `search_args`
property gate. The stale "`search:` is NOT generated (search is `0.1.2`)"
docstring sentence is replaced by the real wiring.

The non-queryset-source guard does NOT extend automatically —
`CONNECTION_SIDECAR_KWARGS` is inert today (the guard chain hardcodes
`filter` / `order_by`; see Current state). Covering `search:` requires
real code changes in `utils/connections.py`: thread the search input
through `connection_sidecar_inputs_from_kwargs` (a third extracted
value) and `has_connection_sidecar_input` (a third keyword param), add
`CONNECTION_SEARCH_KWARG` to the tuple, and widen the hardcoded
"`filter:` / `orderBy:`" wording in
`connection.py::_guard_sidecar_input_against_non_queryset`'s error
message to include `search:`. **The search presence test is the shared
`active_search` predicate, NOT `is not None`** — the guard must reject a
non-queryset consumer resolver only for an ACTIVE search
(`search_input is not None and bool(search_input.strip())`), because
[Decision 11](#decision-11--input-hygiene-strip-check-only-literals-stay-literal)
pins empty/whitespace input as an unconditional no-op; a naive
`is not None` slot would turn `search: "  "` into an observable error.
The predicate is defined once in `filters/search.py` and imported by the
guard. The exact-value assertion in `tests/utils/test_connections.py`
(`== ("filter", "order_by")`) updates in the same slice. The outcome is
the same fail-loud posture `filter:` / `orderBy:` get — a consumer
resolver returning a plain iterable rejects an active `search:` loudly
rather than silently ignoring it.

### Decision 4 — Whole-input phrase semantics: one `Q` object, no term splitting

The card pins the contract twice ("a single Q-object that OR's
`<path>__icontains=<input>` across every declared path"): the entire input
string is one phrase. `search: "red dwarf"` matches rows containing the
contiguous substring `red dwarf` in at least one declared path. Upstream's
`build_search_conditions` instead whitespace-splits and ANDs terms
(DRF `SearchFilter` semantics): every term must match *some* field. The
two diverge exactly on multi-word input, and the divergence is
user-visible, so it must be pinned now: **this package ships phrase
semantics.** Rationale beyond card fidelity: phrase semantics are the
conservative subset (every phrase match is also a term-AND match), so a
later opt-in to term splitting (e.g. a `Meta.search_mode` key, or riding
`TODO-BETA-050-0.1.2`'s full-text surface where ranked term handling
belongs) widens results without breaking existing queries, whereas
launching with term-AND and narrowing later silently drops rows.
Term-splitting as the default is therefore rejected for `0.1.2`; the
open question is recorded in Risks with the fallback named.

Phrase semantics also enable a row-boundary oracle that makes aggregate
implementations observably wrong (cross-spec review): one parent with two
related rows valued `"red"` and `"dwarf"`, another parent with a single
related row valued `"red dwarf"` — `search: "red dwarf"` must match only
the second parent. A `StringAgg(..., delimiter=" ")` implementation can
manufacture the phrase across the first parent's two children regardless
of child order; a correctly correlated terminal predicate evaluated per
related row cannot. The Test plan runs this through the live GraphQL
surface (ordered edges + `totalCount`) and keeps the SQL-shape assertion
in package tests proving the implementation is `EXISTS`, not a scalar
aggregate that merely avoids outer fan-out. Because the existing
multi-word test data can pass under both phrase and term-AND contracts
when one value contains both words, the test plan retains a distinct
multi-field phrase case where separate words match different fields — so
the deliberate upstream divergence stays unmistakable.

### Decision 5 — Card 049 is `icontains`-only; shortcut prefixes fail loudly

Every entry is a model-field path and always becomes `<path>__icontains`.
The `^` / `=` / `@` / `$` vocabulary is not silently accepted: those leading
characters raise [`ConfigurationError`][glossary-configurationerror] during
declaration validation. Canonical card 049 pins the basic OR-of-`icontains`
contract, while card 050 explicitly owns the shortcut parity watch-item and
already requires a clear non-Postgres posture for its full-text surface.

This also keeps SQLite safe: `@` cannot become a late `__search` lookup and
fail at query execution before card 050 has specified and tested the backend
gate. Slice 1 retargets the stale `construct_search` docstring/TODO reservation
from this card to card 050 rather than deleting the shared
`LOOKUP_PREFIXES` constant. Automatically adopting the vocabulary here is
rejected because it expands the KANBAN contract and splits ownership of the
same public syntax across two cards.

### Decision 6 — Pipeline position: visibility → filter → search → orderBy

The search step slots into `_pipeline_sync` / `_pipeline_async` immediately
after the filterset step and before the orderset step:

1. `apply_type_visibility_*` — the
   [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook]
   composed with [`apply_cascade_permissions`][glossary-apply_cascade_permissions]
   narrows the ROOT rows first; related-row visibility is composed inside
   the search predicates themselves
   ([Decision 12](#decision-12--visibility-aware-relational-search)).
2. `FilterSet.apply_*` — unchanged.
3. **search** — the ordered runtime sequence inside `apply_search_*`:
   1. the `active_search` no-op gate — inactive input returns the same
      queryset object, before every other check;
   2. the `SEARCH_MAX_LENGTH` cap
      ([Decision 11](#decision-11--input-hygiene-strip-check-only-literals-stay-literal));
   3. the permission-gate pass
      ([Decision 13](#decision-13--search-honors-filterset-permission-gates));
   4. the combined-queryset preflight — an active search over a
      `union()` / `intersection()` / `difference()` result raises ONE
      typed, actionable error naming the combinator, for direct-only and
      to-many plans alike (a direct-only plan must not fall through to
      Django's raw `NotSupportedError` while a to-many plan gets the
      `optimizer/predicates.py` typed error);
   5. compilation — direct paths as plain `Q` predicates, to-many paths
      as correlated visibility-aware `EXISTS` branches, OR'd and
      `.filter()`-joined
      ([Decision 7](#decision-7--row-preserving-to-many-compilation-no-search-driven-distinct)).
4. `OrderSet.apply_*` — unchanged.
5. `_finalize_queryset` — deterministic total order + optimizer plan,
   unchanged; keyset-cursor connections compose because search mutates the
   queryset before any slicing or cursor fingerprinting.

Filter-then-search vs search-then-filter is commutative (both are
`.filter()` intersections on a lazy queryset); search goes after filter so
the step order reads as "declared sidecars in declaration-surface order".

**The step is NOT colorless.** Related-type visibility hooks may be
async-only, so the search step ships as sync/async twins —
`apply_search_sync` awaiting nothing (and surfacing the existing
`SyncMisuseError` when a hop's visibility hook is async-only, via
`apply_type_visibility_sync`), `apply_search_async` awaiting
`apply_type_visibility_async` per hop — mirroring the FilterSet's
existing `_derive_related_visibility_querysets_sync` / `_async` split.
Everything except visibility derivation (plan reading, `Q` construction,
`EXISTS` attachment, permission gates) remains shared, un-awaited helper
code so the twins stay thin. An earlier revision of this spec claimed one
colorless helper; that claim was only true under visibility-blind
relational traversal, which [Decision 12](#decision-12--visibility-aware-relational-search)
rejects.

Alternative rejected: **apply search inside `FilterSet.apply_*`**
(upstream's shape, where the filterset `qs` property reads
`data["search"]`) — couples search to the presence of a
`filterset_class` (a type may declare `search_fields` alone) and to the
form machinery search does not need.

### Decision 7 — Row-preserving to-many compilation; no search-driven `.distinct()`

An OR'd predicate across a row-multiplying join (reverse FK, M2M, generic)
duplicates parent rows, which corrupts `totalCount`, page sizes, and
cursor math. Upstream fixes this with a blanket `.distinct()`; the earlier
revision of this spec fixed it with a *conditional* `.distinct()`. Both
are rejected: correct rows do not imply an acceptable query. JOIN plus
DISTINCT keeps the membership fan-out in the root query, forces `LEFT
OUTER JOIN` promotion (the to-many arm is one arm of an OR), and turns
`totalCount` into `COUNT(*)` over a `SELECT DISTINCT` subquery wrapper.

This card instead compiles row-preserving through the shared predicate
compiler (`optimizer/predicates.py`, pre-card groundwork):

- At finalize time, the structured path walker classifies every declared
  path; the frozen search path plan on `DjangoTypeDefinition` records the
  direct paths and the to-many path groups (grouped by identical complete
  relation chain — for a same-value OR this grouping is a cost choice,
  never a correctness one, since `EXISTS` distributes over OR; when in
  doubt, one `EXISTS` per path is always correct). The plan replaces the
  earlier `search_requires_distinct` boolean and carries **no request
  data, no queryset, no database alias, and no router answer** — those
  bind at resolve time from the live queryset
  ([Decision 12](#decision-12--visibility-aware-relational-search) pins
  the same rule for visibility querysets).
- At resolve time, direct paths become ordinary `Q(<path>__icontains=v)`
  predicates; each to-many group becomes a correlated `EXISTS` branch —
  the outer model's `_base_manager` on `queryset.db`, correlated on the
  root primary key, the group's `icontains` predicates OR'd inside the
  subquery AND'd with the hop-visibility constraints of
  [Decision 12](#decision-12--visibility-aware-relational-search),
  attached under a `_dst_`-reserved alias. The direct predicates
  and `EXISTS` branches OR together into the one search expression;
  `.distinct()` is never applied.

Consequences: the root query keeps no membership join (the subquery owns
its own alias map), one root row stays one SQL row through counting and
pagination, and **search adds no distinct wrapper and no outer fan-out**.
On a plain root queryset that means `totalCount` is a flat `COUNT(*)`; a
consumer queryset that is already distinct, grouped, annotated, or
projected may legitimately require a count subquery for ITS OWN shape —
the invariant this card owns is only that search never introduces one.
`_base_manager` is deliberate — the outer queryset has already applied
visibility and the consumer manager; the inner row exists only to test
relation existence for an already-qualified outer pk (against the
composed hop-visibility constraints), so a filtered default manager could
only introduce false negatives.

Two to-many search-path categories are proven independently (cross-spec
review — neither test subsumes the other):

- **a reverse FK after a to-one prefix**, matching the Medtrics
  production topology — earned through the shared reproduction fixture
  the pre-card groundwork defines
  ([part1-plan][part1-plan] C.4: `Loan.book -> Book.loans ->
  Loan.patron -> Patron.email` with its four named loans and
  ordered-sequence oracle). This card's integration use: declare
  `LoanType.Meta.search_fields = ("note", "book__loans__patron__email")`
  on the **existing** `LoanType`
  (`examples/fakeshop/apps/library/schema.py` — declared before `Book` /
  `Patron` to exercise finalization order, with real `LoanFilter` /
  `LoanOrder` sidecars). Per
  [Decision 14](#decision-14--search-scope-is-type-definition-wide-and-immutable)
  that declaration is permanent, type-definition-wide public surface —
  NOT test-scoped — and attaches to every current and future connection
  serving `LoanType`. What is acceptance-only is the **connection
  exposure**: no loan connection exists today (the existing loan surface
  is a list field, which correctly gains nothing — `search:` is
  connection-only), so Slice 4 adds a `DjangoConnectionField(LoanType)`
  for the test schema. Issue the real `/graphql/` search request and
  assert the exact ordered IDs
  (`[relation_and_direct, relation_only, direct_only]`), `totalCount`
  of three, both two-edge page boundaries, and the mixed
  direct/relational OR behavior — a root matching the scalar branch
  with several matching related rows, a root matching only the related
  branch, and an unrelated root, pinning both boolean semantics and
  cardinality under the precise mixed-branch shape that caused the
  production issue; and
- **a direct or nested M2M path**, matching the library
  `GenreType.books__title` fixture.

Alternatives rejected: **blanket `.distinct()`** (upstream) and
**conditional `.distinct()`** (this spec's own earlier revision) — both
retain the fan-out and the distinct-wrapper count; **post-processing
`queryset.query`** to strip joins — a late private-API rewrite with
insufficient semantic information; **`StringAgg`-style aggregation** —
Postgres-specific and processes all child strings where `EXISTS` stops at
the first match; **`.distinct("pk")`** — Postgres-specific, collides with
ordering constraints, and still retains the fan-out.

### Decision 8 — `Meta.search_fields` promotes in this card

`search_fields` moves from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` in
Slice 2, because this card ships the key applied end-to-end (declaration →
definition slot → SDL argument → queryset mutation → live fakeshop
coverage) — the exact promotion criterion the DoD states ("only when the
pipeline applies it end-to-end"). The DoD's parenthetical "(per
`TODO-BETA-052-0.1.3`)" is read as pointing at card 052's *generalized
promotion machinery* for the remaining deferred keys
(`aggregate_class`), not as deferring this key's promotion to 052 — the
same reading spec-048 Decision 8 pinned for `fields_class`, and 052's own
title ("Layer 3 Meta key promotion") describes the sweep, not ownership of
each key. Ambiguity + fallback recorded in Risks. `aggregate_class`
remains the sole `DEFERRED_META_KEYS` member after this card and
`TODO-BETA-048-0.1.1` land.

### Decision 9 — No `search` key inside the `filter:` input type

Upstream's `AdvancedFilterSet.get_filter_fields` injects `search: String`
into the advanced filter input, so graphene consumers can write
`filter: { search: "..." }` *and* top-level `search: "..."`. Rejected:
one input, one spelling. A duplicated key inside
[`filter_input_type`][glossary-filter_input_type]-generated inputs would
create two divergence-prone code paths for the same semantics, bloat every
generated filter input with a field unrelated to its FilterSet's
declarations, and collide with a legitimate consumer filter on a model
field named `search`. The top-level argument is the entire wire surface.
This is a deliberate, documented upstream divergence (Borrowing posture);
migrating consumers who used the nested spelling rewrite it to the
top-level argument.

### Decision 10 — Joint cut at `0.1.2` — release state defers to card 050

Two non-Done cards share the `0.1.2` patch version: this card and
`TODO-BETA-050-0.1.2` (Postgres full-text primitives), and 050 explicitly
depends on 049 ("basic search lands first"). The
[Joint version cut][glossary-joint-version-cut] rule therefore assigns card
050 the release-cut artifacts: the version quintet, README/docs README
shipped-surface moves, GOAL/TODAY release wording, and the cumulative
`0.1.2` CHANGELOG entry covering both cards. Card 049 ships its
implementation, card-local spec/TREE updates, and card flip.

The generated GLOSSARY is NOT deferred wholesale: [`AGENTS.md`][agents]
requires shipped behavior to fold into `docs/GLOSSARY.md` in the
completing spec's Slice 5, so leaving
[`Meta.search_fields`][glossary-metasearch_fields] falsely at "planned"
after the implementation lands would make the source-of-truth lie. Slice
5 updates the glossary database and regenerates `docs/GLOSSARY.md` to the
precise intermediate status **"implemented on `main`; release pending the
joint `0.1.2` cut"**; card 050's cut rewords it to shipped. Writing
release notes or marking the surface *released* while the package still
reports `0.1.1` remains rejected. If the maintainer re-sequences and 050
is descoped or retargeted, the cut ownership returns here — recorded in
Risks.

### Decision 11 — Input hygiene: strip-check no-op, a documented length cap, literals stay literal

**Active-search predicate, defined once.** `filters/search.py` exports the
single definition
`active_search = search_input is not None and bool(search_input.strip())`;
the pipeline no-op gate, the non-queryset sidecar guard
([Decision 3](#decision-3--the-argument-is-synthesized-nullable-and-gated-on-the-declaration)),
and every other presence test import it. Inactive input (`None`, `""`,
whitespace-only) is an unconditional no-op that returns the same queryset
object — it runs before the length cap, the permission pass, the
combinator preflight, and the guard, so whitespace input can never become
an observable error. When the gate passes, the *applied* value is the raw
input, not the stripped one — an intentional phrase keeps its interior
spacing untouched.

**Length cap.** `filters/search.py` pins `SEARCH_MAX_LENGTH = 256`
(a module constant, not a setting — no consumer knob ships in `0.1.2`,
per the add-settings-only-when-needed rule). An active input longer than
the cap raises a typed GraphQL error naming the cap and the received
length. Rationale: a client-controlled string is duplicated across every
direct and `EXISTS` branch as a leading-wildcard `LIKE`; transport body
limits bound the request envelope, not a reasonable database pattern
size, and an unbounded public contract is far harder to narrow after
release than a generous cap is to widen. An abuse-case live test pins the
error shape.

**Literals.** Django's parameterized `contains`/`icontains` lookups escape
`%` and `_` themselves, so SQL-wildcard injection through the search
argument is structurally impossible — no additional sanitization layer is
added, and none must ever be (a hand-rolled escape pass would
double-escape). Quotes are literal characters (no phrase-quoting
mini-language), matching upstream's documented "quoted-phrase handling is
not implemented" posture.

### Decision 12 — Visibility-aware relational search

Root visibility does not imply related-row visibility: the pipeline's
step-1 narrowing covers rows of the connection's root model, and
[`apply_cascade_permissions`][glossary-apply_cascade_permissions]
intentionally covers forward single-valued edges — but a to-many search
path (`genres__name__icontains=v`) traverses the related tables as raw
ORM relations. Visibility-blind, a visible parent could qualify **only
because a related row hidden on its own GraphQL surface matched the
search** — a related-data existence oracle. This package's posture
rejects that: the contract is **search never qualifies a row, root or
related, through data the viewer's GraphQL surface hides**.

Mechanism — reusing the single-sited machinery the FilterSet already
consumes, never a parallel implementation:

- The frozen path plan records, for every relation hop in every declared
  path, the hop's target model and whether a `DjangoType` is registered
  for it. Type resolution follows the registry's primary-type rule (the
  same resolution the model registry already defines); the plan stores
  the resolved type reference, never a queryset.
- At resolve time, each hop whose target model has a registered type
  derives that type's visibility-scoped queryset via
  `utils/querysets.py::apply_type_visibility_sync` / `_async` (the same
  helpers behind `FilterSet._derive_related_visibility_querysets_*`),
  pinned to the live queryset's database alias, and composes it into the
  predicate as a membership constraint on the hop — inside the correlated
  `EXISTS` body for to-many groups, AND'd with the group's `icontains`
  OR. A hidden related row then simply does not exist for the subquery.
- **Direct relational branches carry per-branch visibility themselves**
  — never delegated to cascade. `apply_cascade_permissions` is an
  explicit helper a consumer may or may not call, search paths need not
  be exposed output fields, and a type's custom `get_queryset` may narrow
  only its own model, so "cascade covers the forward hops" is not a
  framework invariant. For `search_fields = ("title", "category__name")`,
  the `category__name` branch compiles as a structured
  `(hop visibility AND terminal icontains)` branch — never a bare lookup
  `Q` — with the registered Category type's visibility constraint AND'd
  **only into that relational OR arm** (applying it to the whole query
  would wrongly suppress an Item matching `title`). The same per-hop rule
  covers a chain of forward hops before the first to-many hop, and every
  hop inside the `EXISTS` body (cascade narrowing never reaches inside a
  subquery). A live forward-FK search test on a type that does **not**
  call cascade proves the claim holds beyond the staged fakeshop types.
- The per-hop rule **recurses onto the root model itself**: when a
  declared path re-enters the root model (the Decision 7 reverse-FK
  fixture does — `book__loans` from a `Loan` root makes the second hop's
  target `Loan` again), the root type's own visibility composes into the
  inner rows of the `EXISTS` body exactly like any other registered-type
  hop. This is a deliberate divergence from the pre-card groundwork's
  `filter:` adapter, which preserves the original filter invocation's
  raw traversal (no hop visibility) — the same path yields different
  inner constraints under `filter:` vs `search:`, by design, and the
  test plan pins the recursion case.
- A related model with **no registered type** has no GraphQL surface and
  therefore no visibility contract to honor; the hop traverses the raw
  relation. Declaring a search path across an unregistered model is the
  author's explicit grant over that table's data — documented as such.

Color: related `get_queryset` hooks may be async-only, which is exactly
why the search step ships as sync/async twins
([Decision 6](#decision-6--pipeline-position-visibility--filter--search--orderby)).

Alternative rejected: **declaration-as-authorization** (declaring a path
grants search access to those database paths regardless of related-type
visibility, with a security warning). Cheaper — no visibility derivation,
a colorless step — but it ships a documented related-data existence
oracle and narrows every "hidden rows" claim to "hidden ROOT rows".
[`AGENTS.md`][agents] rules the choice: the highest-quality fix wins even
when it costs more engineering time, and a documented weaker security
contract is a pragmatic shortcut, not an answer.

### Decision 13 — Search honors FilterSet permission gates

Search has a permission contract, and it reuses the EXISTING gates
without inventing new ones: **active search fires every applicable gate
exposed by the declaring type's FilterSet; `Meta.search_fields` is the
authorization grant for paths with no corresponding filter gate.**
("Exactly when they could filter by it" would overstate this — a type may
declare a search path absent from its FilterSet, or declare no FilterSet
at all, both explicitly supported; there the viewer cannot issue the
equivalent `filter:` input, and the declaration itself is the grant.)
The information disclosed by searching a path is a strict subset of what
`icontains`-filtering that path discloses, so a `check_<field>_permission`
gate that denies the filter must deny the search — anything else is a
permission bypass, and the fakeshop fixture proves it is a live one:
`CategoryFilter.check_name_permission` restricts `filter: {name: ...}` to
staff, and Slice 4 activates `search_fields = ("name", "description")` on
the same type, so a gate-blind search would let an anonymous caller probe
category names.

Mechanism:

- When the declaring type has a `filterset_class`, every **active** search
  (post the `active_search` gate, pre-compilation) fires the filterset's
  `check_<field>_permission` gates that cover the declared paths — gate
  matching keys on the filterset's declared filters whose `field_name`
  is a segment-prefix of the declared search path, recursing through
  declared `RelatedFilter` branches for relation paths exactly as
  `FilterSet._run_permission_checks` does for nested filter input, and
  firing each gate method at most once per request via the shared
  `utils/permissions.py` helpers (single-sited with the filter and order
  sides — never a reimplementation).
- A firing gate raises its own error (the same loud `GraphQLError` the
  equivalent `filter:` input produces); the whole search request fails.
  Per-viewer silent path narrowing (dropping gated paths and searching
  the rest) is rejected — different viewers silently receiving different
  result semantics for the same input is the silent-degradation posture
  this package refuses, and the filter side's precedent is a loud raise.
  An author who wants anonymous search on a type with a gated field
  declares only ungated paths.
- Edge semantics are pinned, not implied: when **several filter aliases
  map to one `field_name`**, they share one gate method and it fires at
  most once per request (the existing shared-helper rule); when **only a
  prefix relation is gated** (e.g. a gate on the `category` relation but
  none on `category__name`), the prefix gate is applicable to every
  declared path it prefixes and fires; when `HIDE_FLAT_FILTERS` hides an
  expanded child's public flat filter, the gate still applies — gate
  applicability follows the filterset's declared filters and their
  `field_name`s, never the public exposure of a flat alias.
- A declared search path with **no applicable gate** on a type that HAS a
  `filterset_class` is searchable: the declaration is the grant for that
  path (tested — not only the all-gated Category example and the
  no-FilterSet case).
- A type with **no** `filterset_class` has no gates; its search is gated
  by visibility alone. That is not a bypass — no permission surface
  exists to bypass — and is documented plainly.
- Gates are request-scoped predicates, not queryset transforms; the gate
  pass itself does no queryset work. If a consumer gate touches the
  database, it does so under the same contract the filter side already
  gives it.

Alternatives rejected: **a dedicated `check_search_permission` /
per-path search hook** — a second permission truth for the same fields
that can drift from the filter gates (and no card owns such a surface);
**declaration-as-public-grant** (search ignores filter gates, documented)
— a documented bypass of an existing gate, the exact
ship-it-today-defer-the-real-fix shape [`AGENTS.md`][agents] forbids.

### Decision 14 — Search scope is type-definition-wide and immutable

The Medtrics production reproduction (cross-spec review in
[`feedback.md`][feedback]) surfaces a second application concern beyond
cardinality: the same DRF viewset intentionally exposes group-name search
on one action and withholds it from three others, via
`SearchFilter.get_search_fields(view, request)` action/request dynamism.
That view/action distinction must **not** be translated into request-time
mutation of `DjangoType.Meta.search_fields` or a resolver-specific escape
hatch. The goal's public shape is one declarative `DjangoType.Meta`
sidecar, and this spec already assigns the frozen plan to the exact type
definition. The explicit contract:

- every connection serving the same `DjangoType` definition exposes the
  same static search capability;
- runtime request, resolver, and connection context never mutate or
  narrow the declared path tuple;
- viewer-dependent denial belongs to the existing visibility and
  FilterSet gates
  ([Decision 12](#decision-12--visibility-aware-relational-search),
  [Decision 13](#decision-13--search-honors-filterset-permission-gates));
- a report/custom GraphQL field that is not the model connection need
  not expose the generated search sidecar; and
- a genuinely different model-backed GraphQL surface uses a distinct
  `DjangoType` definition, whose exact-owner plan is already covered by
  the multi-type tests.

This is documented as intentional scope, not left as an accidental
limitation. A field-level override mechanism is rejected absent a
separately demonstrated GraphQL use case — adding one now would work
against the Meta-first, nothing-hand-rolled north star
([`GOAL.md`][goal]).

## Implementation plan

| Slice | Files touched | Delta |
| --- | --- | --- |
| 1 | `django_strawberry_framework/filters/search.py` (new), `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py`, `tests/filters/test_search_fields.py` (new) | `apply_search_sync` / `apply_search_async` / `build_direct_search_q` / `build_search_path_plan` / `active_search` / `SEARCH_MAX_LENGTH`; retarget the superseded `get_filters` TODO and `construct_search` reservation to card 050; unit tests for plan shape, prefix/duplicate/padding rejection, inactive-input identity, cap error, path-validation raises |
| 2 | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `tests/types/` | shape validation + `DEFERRED_META_KEYS` → `ALLOWED_META_KEYS` promotion; `search_fields` + frozen search-path-plan definition slots; phase-2.5 `build_search_path_plan` call (assign-after-success, retry-safe) |
| 3 | `django_strawberry_framework/utils/connections.py`, `django_strawberry_framework/connection.py`, `tests/filters/test_search_fields.py`, `tests/test_connection.py` | `CONNECTION_SEARCH_KWARG` + sidecar-tuple extension with the `active_search` presence predicate; synthesized `search:` param; sync/async pipeline steps (visibility-aware, permission-gated) calling the row-preserving predicate compiler; combined-queryset preflight; guard coverage |
| 4 | `examples/fakeshop/apps/products/schema.py`, the library schema module declaring `GenreType`, `examples/fakeshop/test_query/` | uncomment all four products `search_fields` tuples (fix stale `TODO-BETA-047` comment IDs → this card); add `GenreType.Meta.search_fields = ("name", "books__title")` and the acceptance-only `LoanType` reverse-FK search surface (Decision 7); live HTTP tests per the required-live-case list (products cases in `test_products_api.py` seeded via `seed_data(N)` / `create_users(N)`, library cases in `test_library_api.py` with inline creates); the non-gating PostgreSQL plan-evidence artifact |
| 5 | `docs/TREE.md`, `docs/GLOSSARY.md` (DB + regen), `KANBAN.md`/`KANBAN.html` (DB + regen) | card-local tree regeneration; glossary intermediate status ("implemented on `main`; release pending the joint `0.1.2` cut"); card wrap; version quintet / README marketing / CHANGELOG defer to card 050 (Decision 10) |

## Helper-reuse obligations (DRY)

- `filters/inputs.py::LOOKUP_PREFIXES` is the single prefix vocabulary;
  declaration validation reads it to reject reserved shortcut syntax,
  never redeclares it.
- The structured path-classification walker + `validate_lookup_expr` in
  `utils/relations.py` (the widened `path_traverses_to_many` machinery)
  are the ONLY path/lookup acceptance oracle — no
  `django_filters.utils.get_model_field` second oracle, no hand-rolled
  `_meta.get_field` walk, no third reimplementation of to-many detection.
- `optimizer/predicates.py` for the runtime `EXISTS` construction — search
  never builds its own correlated subqueries, alias allocation, or
  database-alias handling.
- `utils/querysets.py::apply_type_visibility_sync` / `_async` for every
  related-hop visibility derivation (Decision 12) — the same helpers the
  FilterSet's `_derive_related_visibility_querysets_*` consume.
- `utils/permissions.py` for the gate pass (Decision 13) — the same
  helpers behind `FilterSet._run_permission_checks`, single-sited with
  the filter and order sides.
- `utils/connections.py::connection_sidecar_inputs_from_kwargs` /
  `has_connection_sidecar_input` for the non-queryset guard — extend the
  existing extraction/guard pair with a third search slot using the
  shared `active_search` predicate (and keep `CONNECTION_SIDECAR_KWARGS`
  in sync), do not add a parallel guard (Decision 3 details the required
  threading; the tuple alone is inert).
- The `active_search` predicate is defined once in `filters/search.py`
  and imported everywhere a search-presence test is needed.
- The sync/async search steps share every un-awaited helper (plan
  reading, `Q` construction, gate pass, `EXISTS` attachment); only
  visibility derivation forks by color, per the FilterSet precedent.
- Typo-guard `ConfigurationError` messages follow the existing
  `types/base.py` Meta-gate message shape (type name + offending value +
  corrective hint).

## Edge cases and constraints

- **Whitespace-only input** — no-op; the same queryset object is returned
  (no gratuitous `.filter(Q())`), and the sidecar guard never fires
  (Decision 11 / Decision 3).
- **Over-cap input** — typed GraphQL error naming `SEARCH_MAX_LENGTH`
  and the received length (Decision 11).
- **Empty declaration** (`search_fields = ()`), **duplicate paths**, and
  **whitespace-padded paths** — declaration-time `ConfigurationError`
  (Decision 2).
- **Typo'd / unreachable path, relation-terminal path, or a terminal that
  cannot take `icontains`** — finalize-time `ConfigurationError` naming
  type/path/segment/model; never a runtime 500 on first search. The
  accepted terminal families are the text-backed fields
  (`CharField` / `TextField` and their subclasses); integers, UUIDs,
  JSON/HStore, arrays, files, binary fields, and relation descriptors are
  rejected at finalize — backend-dependent `icontains` casting is not a
  contract this card ships. Every accepted family gets execution tests on
  SQLite and PostgreSQL.
- **To-many path** (`search_fields = ("tags__name",)`) — compiled as a
  correlated `EXISTS` branch; a parent with two matching children yields
  one edge, `totalCount` and page cardinality stay correct with no
  `.distinct()` (Decision 7).
- **Hidden related row** — a root row whose only matching related row is
  hidden by the related type's visibility hook does NOT match
  (Decision 12).
- **Gated path** — a declared path covered by a
  `check_<field>_permission` gate raises loudly for denied viewers on any
  active search (Decision 13).
- **Combined queryset** (`union()` / `intersection()` / `difference()`) —
  an active search raises one typed error naming the combinator, for
  direct-only and to-many plans alike; inactive search returns first
  (Decision 6).
- **Multiple `DjangoType`s over one model** — each type's frozen plan is
  keyed to the exact type definition; a connection serving the secondary
  type uses the secondary's plan, visibility hook, and SDL argument, and
  plan caching never collapses them by model identity.
- **Nested connection fields** — `search` joins the sidecar family, so a
  search-bearing nested connection is unwindowable under the current
  optimizer and falls back per parent exactly as `filter:` / `orderBy:`
  sidecars do today; the walker recognizes `search` as a sidecar, creates
  no dead cached window, and strictness can report the per-parent access.
  This is a documented performance consequence, not a correctness one.
- **Shortcut prefix** — declaration-time `ConfigurationError` assigning the
  syntax to card 050; no backend-specific lookup reaches execution.
- **`%` / `_` / quotes in input** — literal characters (Decision 11).
- **Non-queryset consumer resolver + active `search:` input** — the
  extended sidecar guard raises, matching `filter:` / `orderBy:` behavior;
  inactive search values pass through (Decision 3).
- **Type declares `search_fields` but no `filterset_class`** — fully
  supported; no gates exist, search is gated by visibility alone
  (Decision 1, Decision 13).
- **Multi-database routing** — the runtime compiler binds `queryset.db`
  from the live routed queryset; no database alias, queryset, or router
  answer enters the frozen plan (Decision 7, Decision 12).
- **Keyset-cursor connections** (`Meta.cursor_field`-declared) — search
  applies before slicing/fingerprinting; cursors remain stable within a
  fixed search value; changing the search string between pages is the same
  consumer contract as changing `filter:` between pages.
- **Case sensitivity** — `icontains` is ASCII-case-insensitive on SQLite
  for non-ASCII codepoints (Django-documented SQLite limitation); tests
  assert portable ASCII behavior only.
- **Thread/async safety** — the definition slots are finalize-frozen
  metadata; the resolve-time step builds fresh predicates per call and
  mutates nothing shared.

## Test plan

Placement follows the
[Live-first coverage mandate][glossary-live-first-coverage-mandate]: every
behavior reachable through a real `/graphql/` request is earned in
`examples/fakeshop/test_query/`; package tests keep only what inspects
internal query objects or genuinely unreachable state. Live suites route
requests through the shared `examples/fakeshop/graphql_client.py`
helpers (the spec-043 `TestClient` path), never a bare
`django.test.Client`. Any schema rebuild — settings-dependent OR
registry/type-state-mutating (the Decision 12 visibility-hook fixture is
the latter) — uses the live tier's `project_schema_override` / shared
`schema_reload.py` machinery, never ad hoc module reloads.

Unit (`tests/filters/test_search_fields.py`):

- `build_search_path_plan`: flat path, relation path, to-many grouping by
  complete relation chain (same-chain terminals share a group; divergent
  later chains split, including paths sharing only their first to-many
  hop); typo / relation-terminal / non-text-terminal → raises with
  type/path/segment/model in the message; assign-after-success
  (a failing later path leaves no partial plan).
- Declaration validation: all four reserved prefixes, empty tuple,
  duplicates, padded paths → raise.
- `active_search` truth table; inactive input returns the queryset by
  identity through `apply_search_*`; over-cap input raises the typed
  error.
- `build_direct_search_q` output shape: OR across paths, whole input,
  `icontains`.

Integration (`tests/filters/`, `tests/test_connection.py` — internal
query-object inspection only):

- SQL-shape invariants (the load-bearing regression checks — a
  result-count test alone cannot distinguish `EXISTS` from
  JOIN-plus-DISTINCT), asserted on a PLAIN root queryset: the root
  query's `alias_map` excludes the membership and child tables,
  `queryset.query.distinct is False`, the compiled SQL contains `EXISTS`
  for a to-many declaration and none for a direct-only declaration, and
  the count SQL is a flat `COUNT(*)` with no distinct-wrapper subquery.
  A separate compatibility test proves search composes onto an
  already-distinct / annotated consumer queryset without corrupting its
  count (no flat-`COUNT(*)` assertion there — the invariant is only that
  search adds no wrapper).
- Combined-queryset preflight: direct-only and to-many plans both raise
  the one typed error naming the combinator; inactive search does not.
- Multi-database routing: an explicit non-default alias survives through
  direct-only and to-many compilation.
- Exact-owner (multi-type) coverage: primary/secondary types over one
  model where only the secondary declares a to-many path — each plan
  distinct, no registry fallback by model identity, plan caching keeps
  them apart.
- Visibility composition mechanics: hop-visibility constraints present
  inside the `EXISTS` body; unregistered-model hops traverse raw.
- Sidecar guard threading (`connection_sidecar_inputs_from_kwargs` /
  `has_connection_sidecar_input` third slot with `active_search`).

Live HTTP (`examples/fakeshop/test_query/` — products cases in
`test_products_api.py`, first lines `seed_data(N)` / `create_users(N)`;
library cases in `test_library_api.py`, inline creates):

- SDL introspection: `search: String` present exactly on declaring types,
  absent on a non-declaring control, no nested `filter.search` key.
- **The to-many proof** (library): one genre linked to two books whose
  titles both match, `allLibraryGenresConnection(search: ...)` → one edge
  and `totalCount == 1`; emitted count and page SQL contain `EXISTS` and
  no search-driven `SELECT DISTINCT`; a second page and `hasNextPage`
  operate on root rows.
- Direct-only, forward-relation (`category__name`-shaped), and to-many
  search; `filter:` + `search:` intersection; `search` + `orderBy` +
  `totalCount`, first and second page, and keyset mode.
- Null / empty / whitespace-only / raw leading-and-trailing-space input;
  multi-word phrase semantics (the deliberate upstream divergence,
  including the distinct multi-field case where separate words match
  different fields — a case term-AND would pass but phrase semantics
  reject); `%`, `_`, and quotes as literals; the over-cap abuse case and
  its typed error shape.
- **The reverse-FK Medtrics reproduction** (library, the shared
  groundwork fixture — Decision 7):
  `LoanType.Meta.search_fields = ("note", "book__loans__patron__email")`
  over an acceptance-only `DjangoConnectionField(LoanType)` — exact
  ordered edge IDs `[relation_and_direct, relation_only, direct_only]`,
  `totalCount == 3`, both two-edge page boundaries, mixed
  direct/relational OR behavior (a row matching both branches appears
  once), with the SQL-shape proof (correlated `EXISTS`, no membership or
  patron join in the root, no search-driven `DISTINCT`) kept in package
  tests. Ordered assertions compare against pks captured at fixture
  creation, never insertion-order faith about pk allocation.
- **The row-boundary phrase oracle** (Decision 4): one parent with two
  related rows `"red"` and `"dwarf"`, another with a single related row
  `"red dwarf"` — `search: "red dwarf"` matches only the second parent
  (ordered edges + `totalCount`), proving no phrase is manufactured
  across separate related rows.
- Permission: anonymous vs staff on the Category `name` gate — anonymous
  active search on categories fails loudly with the gate's error while
  staff search succeeds; the equivalent `filter: {name: ...}` control;
  an **ungated search-only path on a type that HAS a FilterSet** is
  searchable (the declaration is the grant — Decision 13); the
  no-FilterSet visibility-only case.
- Visibility: hidden ROOT rows never appear and never perturb
  `totalCount`; the Decision 12 related-row proof — a genre whose only
  matching book is hidden by the book surface's visibility hook does not
  match (fixture may add a visibility hook to an existing library type;
  no model/migration changes); a **forward-FK branch on a type that does
  not call `apply_cascade_permissions`** still carries the hop target's
  visibility, AND'd only into its own OR arm (Decision 12); the
  **root-model recursion case** — a hidden inner `Loan` row (hidden by
  `LoanType`'s own visibility) cannot qualify a visible root loan
  through the `book__loans` hop (Decision 12).
- Cache isolation: the same operation document executed twice with
  different `$search` variables, and two aliases with different search
  values in one operation — results and `totalCount` independent while
  the selection plan cache is reused.
- A non-queryset consumer resolver with inactive (passes) and active
  (guard raises) search values; an actual async consumer resolver earning
  `_pipeline_async`'s search step through HTTP if the line is reachable
  in the example schema.
- Nested-connection search: correct results under the per-parent
  fallback, no dead cached window, strictness reporting behavior.

Performance evidence (non-gating artifact, Slice 4): a PostgreSQL
before/after comparison of the `EXISTS` shape vs JOIN-plus-DISTINCT on
identical data and indexes — root cardinality and fan-out recorded, page
and count `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`, high- and
low-selectivity terms, direct-only / one to-many group / several
independent groups, warm/cold context and versions noted. No wall-clock
test gates — the artifact retains the evidence behind the permanent
compiler shape.

## Doc updates

- Update the glossary DB so
  [`Meta.search_fields`][glossary-metasearch_fields] reads "implemented on
  `main`; release pending the joint `0.1.2` cut" and regenerate
  `docs/GLOSSARY.md` (Decision 10); README/docs README, GOAL/TODAY, and
  `CHANGELOG.md` release status stay untouched for card 050's joint cut.
- The spec/public docs state the contracts explicitly: relational search
  honors related-type visibility (Decision 12); search honors FilterSet
  field-permission gates and a filterset-less type's search is
  visibility-gated only (Decision 13); declared paths need not be exposed
  output fields — a declaration over an unregistered related model is an
  explicit data-discovery grant; whole-phrase semantics and raw
  surrounding-whitespace behavior; the `SEARCH_MAX_LENGTH` cap; top-level
  `search:` only (no nested filter spelling) with migration guidance from
  django-graphene-filters; the borrowing/migration documentation states
  **both intentional DRF `SearchFilter` divergences together** —
  whole-input phrase semantics instead of whitespace-split term-AND
  (Decision 4), and static type-definition scope instead of
  `get_search_fields(view, request)` action/request dynamism
  (Decision 14) — so future maintainers cannot accidentally import DRF
  term splitting or dynamic scoping while pursuing "DRF first"
  ([`GOAL.md`][goal] promises a DRF-shaped, Meta-driven developer
  experience, not byte-for-byte `SearchFilter` parity); the
  nested-connection per-parent fallback and
  strictness behavior; leading-wildcard `icontains` generally needs a
  PostgreSQL trigram index for selective text lookup (row preservation
  and text-indexability are separate concerns).
- `docs/TREE.md`: regen after `filters/search.py` lands (module docstring
  required by the renderer).
- `examples/fakeshop/test_query/README.md`: update the suite
  descriptions for the new live search coverage (the products
  activations, the library to-many and loan reverse-FK surfaces) so the
  tier guide stays accurate.
- `KANBAN.md` / `KANBAN.html`: card flip via DB + regen only.

## Risks and open questions

- **Term-splitting divergence (Decision 4).** The card pins whole-input
  phrase semantics; upstream ships DRF-style term-AND. Preferred answer
  for `0.1.2`: phrase semantics (card-pinned, conservatively widenable).
  Fallback if the maintainer wants upstream fidelity: adopt term-AND
  before first release of the surface — it must be decided before `0.1.2`
  ships because the two differ user-visibly on multi-word input and
  switching later is a semantic break.
- **Prefix ownership (Decision 5).** Card 049 rejects shortcut-prefixed
  declarations. Card 050 must decide which shortcuts ship, pin the migration
  contract, and define the `@` backend guard before accepting any of them.
- **Promotion ownership (Decision 8).** The DoD's "(per
  `TODO-BETA-052-0.1.3`)" parenthetical is ambiguous, exactly as it was
  for `fields_class` in spec-048. Preferred: promote here (end-to-end
  criterion met). Fallback: leave in `DEFERRED_META_KEYS` and have 052
  promote — but then Slice 4's fakeshop activation cannot land, so the
  fallback effectively descopes Slice 4 to package-schema tests only.
- **Joint-cut re-sequencing (Decision 10).** If `TODO-BETA-050-0.1.2` is
  descoped/retargeted after this card ships, the `0.1.2` cut ownership
  returns to this card as a post-ship follow-up; the maintainer owns that
  call.
- **`EXISTS` vs JOIN-plus-DISTINCT performance regime (Decision 7).** N
  independent correlated `EXISTS` groups OR'd over a large, low-selectivity
  root set can lose to one N-way JOIN + DISTINCT on some planners. No
  escape hatch ships in `0.1.2` (a `Meta.search_strategy` key stays in
  reserve); the call is deferred until a real workload demonstrates the
  regime — but the Slice 4 PostgreSQL plan artifact retains the evidence
  either way. Tests gate SQL structure, never wall-clock.
- **Visibility-derivation cost (Decision 12).** Each visibility-bearing
  hop derives a related visibility queryset per active search request.
  The derivation is lazy queryset construction (no extra round trip when
  composed as a subquery constraint), but a consumer hook that does its
  own I/O pays that cost per request — the same contract the FilterSet's
  related-visibility derivation already carries. Documented, not gated.
- **Nested-connection fallback (Decision 6 / Edge cases).** Search-bearing
  nested connections fall back per parent under the current optimizer,
  inheriting the documented sidecar N+1. If strictness=`raise` makes
  nested search effectively unusable for a consumer, that is by design
  until the sidecar-window card (unowned) lands; documented explicitly.
- **List-field / node-field search.** The card scopes `search:` to
  connection fields. Whether [`DjangoListField`][glossary-djangolistfield]
  should grow the same argument is left open; nothing in this design
  precludes it (the step is field-agnostic), but it is not
  `0.1.2` work and no card currently owns it.
- **Stale card IDs in fakeshop comments.** The commented-out declarations
  in `examples/fakeshop/apps/products/schema.py` cite `TODO-BETA-047-0.1.2`
  (a pre-renumber ID; 047 is now the beta-release card). Slice 4 corrects
  the comments as part of activation — noted here per the card-vs-tree
  conflict rule rather than silently reconciled.

## Out of scope (explicitly tracked elsewhere)

- Ranked / weighted / trigram full-text search and the `^` / `=` / `@` / `$`
  shortcut parity decision — `TODO-BETA-050-0.1.2` (depends on this card;
  owns the `0.1.2` cut).
- The generalized deferred-key promotion sweep and
  [`Meta.aggregate_class`][glossary-metaaggregate_class] /
  [`AggregateSet`][glossary-aggregateset] — `TODO-BETA-052-0.1.3`.
- [`FieldSet`][glossary-fieldset] /
  [`Meta.fields_class`][glossary-metafields_class] composition — spec-048
  (`TODO-BETA-048-0.1.1`; ships before this card).
- The Relay `node` / `nodes` root entry points and the connection
  `totalCount` opt-in — `TODO-BETA-055-0.1.5` (the product-catalog root
  schema is already live; this card's Slice 4 owns only the
  `search_fields` activations).
- A dedicated search permission hook and any nested-connection search
  windowing — no owning cards; Decisions 13 and 6 pin the shipped
  contracts.
- [`Meta.choice_enum_names`][glossary-metachoice_enum_names] and the
  `0.1.4` line — untouched.

## Definition of done

- [ ] `docs/spec-049-search_fields-0_1_2.md` (this file) is the card's
  spec of record.
- [ ] `filters/search.py` ships `apply_search_sync` / `apply_search_async`
  / `build_search_path_plan` / `active_search` / `SEARCH_MAX_LENGTH`;
  prefix/duplicate/padded declarations fail loudly and the
  `filters/sets.py` / `construct_search` reservations are retargeted to
  card 050.
- [ ] `Meta.search_fields` validates at declaration (shape) and finalize
  (one strict plan builder, assign-after-success), lands on
  `DjangoTypeDefinition`, and is promoted to `ALLOWED_META_KEYS`.
- [ ] Every connection field serving a declaring type carries a nullable
  `search: String` argument that produces the OR'd predicate
  row-preserving — direct paths as plain `Q`s, to-many paths as correlated
  `EXISTS` branches, no search-driven `.distinct()` or outer fan-out, root
  `alias_map` free of membership joins — post-visibility, intersecting
  with `filter:`.
- [ ] Relational search is visibility-aware (Decision 12) and honors
  FilterSet permission gates (Decision 13), with live anonymous/staff and
  hidden-related-row proofs.
- [ ] Search scope is immutable and type-definition-wide (Decision 14);
  the reverse-FK Medtrics reproduction (shared groundwork fixture) and
  the row-boundary phrase oracle pass live with exact ordered IDs,
  `totalCount`, and page boundaries; the borrowing docs state both DRF
  `SearchFilter` divergences together.
- [ ] The `SEARCH_MAX_LENGTH` cap, combined-queryset preflight, and
  active-search guard threading are live-tested.
- [ ] `tests/filters/test_search_fields.py` + `tests/test_connection.py`
  cover the package-internal matrix (plan builder, SQL shape on a plain
  root, multi-DB, multi-type exact owner, guard threading); the live tier
  covers every reachable behavior per the Test plan, including the
  library to-many proof over `allLibraryGenresConnection`.
- [ ] The non-gating PostgreSQL plan-evidence artifact is retained.
- [ ] Slice 5 card-local docs updated; GLOSSARY moves to the precise
  intermediate status; no release-cut artifact is changed.
- [ ] **No release-cut edit** — the `0.1.2` quintet, README shipped-surface
  moves, and CHANGELOG entry belong to the
  `TODO-BETA-050-0.1.2` joint cut (Decision 10).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md

<!-- docs/ -->
[feedback]: feedback.md
[part1-plan]: row-preserving-predicates-part1-plan.md
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filter_input_type]: GLOSSARY.md#filter_input_type
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-metaaggregate_class]: GLOSSARY.md#metaaggregate_class
[glossary-metachoice_enum_names]: GLOSSARY.md#metachoice_enum_names
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary]: GLOSSARY.md
[search-terms]: spec-049-search_fields-0_1_2-terms.csv

<!-- docs/SPECS/ -->
[spec-027]: SPECS/spec-027-filters-0_0_8.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-043]: SPECS/spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
