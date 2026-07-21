# Spec: `Meta.search_fields` — declarative OR'd search on connection fields

Planned for `0.1.2` (card `TODO-BETA-049-0.1.2`); **`TODO-BETA-050-0.1.2`
(Postgres full-text search filter primitives) shares this patch version and
depends on this card, so the `0.1.2` version bump belongs to the joint cut
and this spec defers it**
([Decision 10](#decision-10--joint-cut-at-012--the-version-bump-defers-to-card-050)).
The Strawberry analogue of `django-graphene-filters`' `Meta.search_fields`:
a `DjangoType` declares a tuple of model-field paths
(`search_fields = ("name", "description", "galaxy__name")`), and every
connection field serving that type gains a single nullable `search: String`
argument. A non-empty input fans out across every declared path as one OR'd
`icontains` `Q` object joined into the queryset by intersection — after
visibility, alongside `filter:`, before `orderBy:`
([Decision 6](#decision-6--pipeline-position-visibility--filter--search--orderby)).
Relation paths ride Django's standard `__` lookup traversal; no custom
resolver machinery. Both dependencies have shipped (`DONE-027-0.0.8`
Filtering, `DONE-030-0.0.9` `DjangoConnectionField`) and the landing seams
already exist in the tree: `filters/inputs.py::LOOKUP_PREFIXES` +
`construct_search` (landed by spec-027 Decision 3 Layer 5 explicitly "for
the future `Meta.search_fields` card") and the
`connection.py::_synthesized_signature` docstring's "The `search:` argument
is NOT generated (search is `0.1.2`)" reservation.

Status: **PLANNED — no slice built yet.**
Five slices: Slice 1 (**`filters/search.py` core** — the `Q`-builder, prefix
translation, path validation, unit tests), Slice 2 (**Meta surface** —
declaration-time shape validation, the `DjangoTypeDefinition.search_fields`
slot, phase-2.5 path validation, `DEFERRED_META_KEYS` promotion), Slice 3
(**connection wiring** — the synthesized `search:` argument, the pipeline
step, to-many `.distinct()`, guards), Slice 4 (**live fakeshop activation +
composability tests**), Slice 5 (**docs + card wrap — NO version bump**).

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
without explicit permission; this spec's Slice 5 grants that permission for
the `0.1.2`-line entry, and no earlier slice touches it.

---

## Key glossary references

Every project-specific symbol below is anchored in
[`docs/GLOSSARY.md`][glossary]; the companion
[`spec-049-search_fields-0_1_2-terms.csv`](spec-049-search_fields-0_1_2-terms.csv)
is the audit ledger. Load-bearing entries:

- [`Meta.search_fields`][glossary-metasearch_fields] — the surface this card
  ships ("planned for `0.1.2`"; Slice 5 flips it to shipped).
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — where the
  `search:` argument surfaces.
- [`FilterSet`][glossary-filterset] /
  [`Meta.filterset_class`][glossary-metafilterset_class] — the sibling
  sidecar `search` composes with by intersection.
- [`OrderSet`][glossary-orderset] /
  [`Meta.orderset_class`][glossary-metaorderset_class] — the downstream
  pipeline neighbor.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] /
  [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — search
  runs strictly after visibility narrowing
  ([Decision 6](#decision-6--pipeline-position-visibility--filter--search--orderby)).
- [`ConfigurationError`][glossary-configurationerror] — the raise type for
  every new declaration-time and finalize-time validation.
- [`finalize_django_types`][glossary-finalize_django_types] — phase 2.5
  hosts the path validation.
- [Joint version cut][glossary-joint-version-cut] — why Slice 5 does NOT
  bump the version.

## Slice checklist

- [ ] **Slice 1 — `filters/search.py` core.** `build_search_q` (whole-input
  OR'd `Q` across declared paths), per-path prefix translation on top of
  `filters/inputs.py::LOOKUP_PREFIXES`, `validate_search_fields` (path
  resolution via `django_filters.utils.get_model_field`), unit tests under
  `tests/filters/test_search_fields.py`.
- [ ] **Slice 2 — Meta surface.** Declaration-time shape validation in
  `types/base.py`, the `DjangoTypeDefinition.search_fields` slot, phase-2.5
  path validation + to-many precomputation in `types/finalizer.py`, promote
  `search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`
  ([Decision 8](#decision-8--metasearch_fields-promotes-in-this-card)).
- [ ] **Slice 3 — connection wiring.** `CONNECTION_SEARCH_KWARG` in
  `utils/connections.py`, the synthesized nullable `search: String`
  argument in `connection.py::_synthesized_signature`, the colorless search
  step in `_pipeline_sync` / `_pipeline_async`, conditional `.distinct()`
  ([Decision 7](#decision-7--conditional-distinct-only-when-a-declared-path-traverses-to-many)),
  non-queryset-source guard extension.
- [ ] **Slice 4 — live activation + composability.** Uncomment all four
  `search_fields` declarations in `examples/fakeshop/apps/products/schema.py`
  (fixing their stale card-number comments), live HTTP tests under
  `examples/fakeshop/test_query/` including at least one relation path,
  composability tests (`search` + `filter:`, `search` + visibility,
  `search` + `totalCount`, `search` + keyset cursors).
- [ ] **Slice 5 — docs + card wrap.** `docs/GLOSSARY.md` status flip (DB +
  regen), `README.md` / `GOAL.md` / `TODAY.md` surface mentions,
  `CHANGELOG.md` `0.1.2`-line entry (permission granted above),
  `docs/TREE.md` regen, KANBAN card flip + board regen. **NO
  `pyproject.toml` / `__version__` / `tests/base/test_init.py` bump** —
  deferred to the `TODO-BETA-050-0.1.2` joint cut
  ([Decision 10](#decision-10--joint-cut-at-012--the-version-bump-defers-to-card-050)).

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
every other read-side layer without leaking rows the viewer cannot see.

## Current state

- `types/base.py::DEFERRED_META_KEYS` contains
  `{"aggregate_class", "fields_class", "search_fields"}`; declaring
  `Meta.search_fields` today raises the reserved-key
  [`ConfigurationError`][glossary-configurationerror]
  (`exceptions.py` names `search_fields` in its reserved-key docstring).
- `filters/inputs.py::LOOKUP_PREFIXES` (`^` → `istartswith`, `=` → `iexact`,
  `@` → `search`, `$` → `iregex`) and `filters/inputs.py::construct_search`
  landed with spec-027 Decision 3 Layer 5 explicitly reserved for this card;
  `construct_search`'s docstring says so, and
  `tests/filters/test_inputs.py` exercises the translation directly.
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
  hardcoded keyword params (`filter_input`, `order_by_input`); the
  tuple's only other reference is an exact-value assertion in
  `tests/utils/test_connections.py`.
- `utils/relations.py::path_traverses_to_many` answers "does this
  `__`-separated path cross a to-many hop" from model metadata with a
  process-lifetime cache; filter generation and order resolution already
  share it.
- `types/definition.py::DjangoTypeDefinition` carries `filterset_class` /
  `orderset_class` / `fields_class` slots; there is **no** `search_fields`
  slot yet.
- `examples/fakeshop/apps/products/schema.py` carries four commented-out
  `search_fields` declarations (Category, Item, Property, Entry) gated on
  this card (their comments cite a stale pre-renumber card ID,
  `TODO-BETA-047-0.1.2`).
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
   declaration (shape) and finalize (path resolution).
2. A single nullable `search: String` argument on every
   [`DjangoConnectionField`][glossary-djangoconnectionfield] serving a
   declaring type. Absent from SDL when the type does not declare the key.
3. Non-empty input → one `Q` OR-ing `<path>__icontains=<input>` across
   every declared path, `.filter()`-joined into the queryset.
   Empty / null / whitespace-only input → no-op.
4. Composition by intersection with `filter:`; strictly post-visibility so
   hidden rows cannot be discovered by probing field values.
5. Correct row cardinality: `.distinct()` exactly when a declared path
   traverses a to-many relation, never otherwise.
6. Promotion of `search_fields` out of `DEFERRED_META_KEYS` — the pipeline
   applies the key end-to-end in this card.

## Non-goals

- **Ranked / weighted / similarity full-text search.** That is
  `TODO-BETA-050-0.1.2` (Postgres `SearchQueryFilter` / `SearchRankFilter`
  / `TrigramFilter` primitives), explicitly distinct from this card's
  basic OR'd `icontains` surface and gated on it.
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

## Borrowing posture

[Single-upstream parity][glossary-single-upstream-parity] surface: the only
upstream shipping this shape is `django-graphene-filters` (verified in
`object_type.py`, `connection_field.py`, `filterset.py`, and the cookbook's
`recipes/schema.py`), and the consumer-facing contract —
[Cookbook parity][glossary-cookbook-parity] — is that a graphene-era
`search_fields` tuple carries over verbatim when the import line changes.
Element classification:

- **Borrowed verbatim**: the Meta key name and tuple-of-paths shape; the
  single nullable `search: String` argument name and type; `icontains` as
  the default lookup; Django `__` traversal for relation paths; the DRF
  prefix vocabulary (`^`, `=`, `@`, `$`) — upstream's
  `construct_search(field_name)` strips a leading prefix character and
  falls back to `icontains`, exactly the `LOOKUP_PREFIXES` seam this
  package landed in `0.0.8`.
- **Engine-adapted**: argument generation moves from graphene's
  `Field.args` property merge to this package's synthesized-resolver
  signature (`connection.py::_synthesized_signature`, spec-030 Decision 6:
  the resolver signature IS the SDL contract); application moves from the
  filterset's `qs` property to a dedicated colorless pipeline step
  ([Decision 1](#decision-1--search-support-lives-in-filterssearchpy-not-inside-filterset)),
  because this package's `FilterSet.apply_sync` / `apply_async` entry
  points are transactional permission-checked surfaces, not a form `qs`
  property.
- **Deliberately diverged**: no whitespace term-splitting
  ([Decision 4](#decision-4--whole-input-phrase-semantics-one-q-object-no-term-splitting));
  no `search` key duplicated into the filter input type
  ([Decision 9](#decision-9--no-search-key-inside-the-filter-input-type));
  no blanket `.distinct()` — upstream applies one unconditionally after
  filtering, this package applies it only when a declared path is
  row-multiplying
  ([Decision 7](#decision-7--conditional-distinct-only-when-a-declared-path-traverses-to-many));
  typo'd paths fail loudly at finalize with
  [`ConfigurationError`][glossary-configurationerror] instead of upstream's
  silent runtime `FieldError`.

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
  `.filter(...)` — the whole input as one phrase.
- Prefixed entries opt into other lookups per path:
  `search_fields = ("=code", "^name", "description")` →
  `code__iexact` / `name__istartswith` / `description__icontains`.
  `@` maps to `__search` (requires `django.contrib.postgres`; documented
  Postgres-only, exactly as in DRF's `SearchFilter`).
- `filter:` and `search:` in the same query intersect — the result matches
  every filter predicate AND the search OR-clause.

## Architectural decisions

### Decision 1 — Search support lives in `filters/search.py`, not inside `FilterSet`

A new sibling module `django_strawberry_framework/filters/search.py` owns
the runtime and validation surface: `build_search_q(search_fields, value)`
(the whole-input OR'd `Q` builder), `search_lookup_for_path(path)` (prefix
translation over `filters/inputs.py::LOOKUP_PREFIXES`), and
`validate_search_fields(model, search_fields)` (finalize-time path
resolution). This satisfies the card's "argument generation lives in
`django_strawberry_framework/filters/` and reuses the same DRF-style Meta
surface and argument-factory machinery as `filterset_class`" DoD line while
keeping [`FilterSet`][glossary-filterset] untouched: search needs no input
type, no form validation, no permission gates, and no related-visibility
derivation — routing it through `FilterSet.apply_sync`'s transactional
machinery (upstream's placement, via the filterset `qs` property) would
buy nothing and would couple a pure `Q` construction to the heaviest
entry point in the package.

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
must be a tuple or list of non-empty `str`, and an **empty tuple raises**
— declaring the key with zero paths is a misconfiguration, not a no-op
(the silent-degradation posture this package consistently rejects). The
validated tuple lands on a new
`types/definition.py::DjangoTypeDefinition.search_fields` slot
(`tuple[str, ...] | None = None`, normalized from list input).

Path resolution — does `galaxy__name` actually reach a field — waits for
[`finalize_django_types`][glossary-finalize_django_types] phase 2.5:
`filters/inputs.py::_model_field_for_filter` already pins the precedent
that `django_filters.utils.get_model_field` may only run after
`apps.populate()` has resolved lazy FK strings, so declaration-time path
walking would crash legitimate declaration orders
([Definition-order independence][glossary-definition-order-independence]).
Each declared path (prefix stripped first) must resolve via
`get_model_field(model, path)`; a `None` return raises
[`ConfigurationError`][glossary-configurationerror] naming the type, the
offending path, and the model — the typo-guard message discipline every
Meta-key gate in `types/base.py` follows. The `@` prefix's `__search`
lookup is exempt from *lookup* validation (it is a Postgres-registered
lookup, invisible to `get_model_field`'s field walk, which validates only
the path portion).

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
message to include `search:`. The exact-value assertion in
`tests/utils/test_connections.py` (`== ("filter", "order_by")`) updates
in the same slice. The outcome is the same fail-loud posture `filter:` /
`orderBy:` get — a consumer resolver returning a plain iterable rejects
`search:` loudly rather than silently ignoring it.

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

### Decision 5 — The DRF prefix vocabulary ships, defaulting to `icontains`

`search_fields` entries accept the four-character prefix vocabulary
`LOOKUP_PREFIXES` pins (`^` → `istartswith`, `=` → `iexact`, `@` →
`search`, `$` → `iregex`); an unprefixed entry gets `icontains`. The card's
prose names only the `icontains` fan-out, but the prefix seam was landed in
`0.0.8` *explicitly reserved for this card* (the `LOOKUP_PREFIXES` and
`construct_search` docstrings both say so), upstream's
`construct_search(field_name)` implements exactly this vocabulary, and DRF
consumers migrating a `search_fields` tuple may already carry prefixes —
rejecting them would break the verbatim-carry-over
[Cookbook parity][glossary-cookbook-parity] promise. The per-path
translation is a thin `search_lookup_for_path(path) -> tuple[str, str]`
(stripped path, lookup name) beside the existing dict-shaped
`construct_search(all_filters)` helper; both read the one
`LOOKUP_PREFIXES` constant. `@`/`__search` is documented Postgres-only
(consumer responsibility, as in DRF); the other three lookups are
portable. The card-text-vs-seam tension is recorded in Risks.

### Decision 6 — Pipeline position: visibility → filter → search → orderBy

The search step slots into `_pipeline_sync` / `_pipeline_async` immediately
after the filterset step and before the orderset step:

1. `apply_type_visibility_*` — the
   [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook]
   composed with [`apply_cascade_permissions`][glossary-apply_cascade_permissions]
   narrows first, so search never sees (and can never confirm the existence
   of) hidden rows — the card's non-negotiable ordering.
2. `FilterSet.apply_*` — unchanged.
3. **search** — `qs.filter(build_search_q(...))` (+ conditional
   `.distinct()`, [Decision 7](#decision-7--conditional-distinct-only-when-a-declared-path-traverses-to-many)).
4. `OrderSet.apply_*` — unchanged.
5. `_finalize_queryset` — deterministic total order + optimizer plan,
   unchanged; keyset-cursor connections compose because search mutates the
   queryset before any slicing or cursor fingerprinting.

Filter-then-search vs search-then-filter is commutative (both are
`.filter()` intersections on a lazy queryset); search goes after filter so
the step order reads as "declared sidecars in declaration-surface order"
and the `.distinct()` (when applied) lands after both row-multiplying
joins. The step is **colorless** — building a `Q` and calling
`.filter()` on a lazy queryset does no I/O — so one shared helper serves
both pipelines with no maybe-await wrapper, the same single-siting
argument `_finalize_queryset` already makes for steps 5–6.

Alternative rejected: **apply search inside `FilterSet.apply_*`**
(upstream's shape, where the filterset `qs` property reads
`data["search"]`) — couples search to the presence of a
`filterset_class` (a type may declare `search_fields` alone) and to the
transactional permission machinery search does not need.

### Decision 7 — Conditional `.distinct()`, only when a declared path traverses to-many

An OR'd predicate across a row-multiplying join (reverse FK, M2M)
duplicates parent rows, which corrupts `totalCount`, page sizes, and
cursor math. Upstream fixes this with a blanket `.distinct()` after every
filtered query; this package instead computes, once at finalize time,
whether ANY declared path crosses a to-many hop — reusing
`utils/relations.py::path_traverses_to_many`, the exact helper filter
generation (`distinct=True` marking) and order resolution already share —
and stores the boolean alongside the definition slot
(`search_requires_distinct`). At resolve time the search step appends
`.distinct()` exactly when the flag is set AND the input is non-empty.
Blanket distinct is rejected because it silently rewrites consumer-visible
SQL for the all-forward-paths common case (the `filters/sets.py` comment
at the RelatedFilter constraint site pins the same "no `.distinct()`
mutation of consumer-visible querysets" posture); per-request metadata
walking is rejected because the answer depends only on model metadata,
which is immutable after finalize.

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

### Decision 10 — Joint cut at `0.1.2` — the version bump defers to card 050

Two non-Done cards share the `0.1.2` patch version: this card and
`TODO-BETA-050-0.1.2` (Postgres full-text primitives), and 050 explicitly
depends on 049 ("basic search lands first"). The
[Joint version cut][glossary-joint-version-cut] rule therefore assigns the
`pyproject.toml` / `__version__` / `tests/base/test_init.py` / GLOSSARY
package-version-row / `uv.lock` quintet to the LAST `0.1.2` card to land —
card 050. This spec's Slice 5 must NOT bump the version (mirroring
spec-043 Decision 12's deferral shape, the most recent joint-cut
precedent); it ships docs and the card flip only. If the maintainer
re-sequences and 050 is descoped or retargeted, the cut ownership returns
here — recorded in Risks.

### Decision 11 — Input hygiene: strip-check only, literals stay literal

The no-op gate is `value is None or not value.strip()`; when the gate
passes, the *applied* value is the raw input, not the stripped one — an
intentional phrase keeps its interior spacing untouched. Django's
parameterized `contains`/`icontains` lookups escape `%` and `_`
themselves, so SQL-wildcard injection through the search argument is
structurally impossible — no additional sanitization layer is added, and
none must ever be (a hand-rolled escape pass would double-escape). Quotes
are literal characters (no phrase-quoting mini-language), matching
upstream's documented "quoted-phrase handling is not implemented" posture.
There is no length cap in `0.1.2`; a pathological input costs one LIKE
per declared path, the same order of work as any filter predicate.

## Implementation plan

| Slice | Files touched | Delta |
| --- | --- | --- |
| 1 | `django_strawberry_framework/filters/search.py` (new), `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py`, `tests/filters/test_search_fields.py` (new) | `build_search_q` / `search_lookup_for_path` / `validate_search_fields`; remove the superseded `get_filters` TODO; unit tests for Q shape, prefixes, empty-input no-op, path validation raises |
| 2 | `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `tests/types/` | shape validation + `DEFERRED_META_KEYS` → `ALLOWED_META_KEYS` promotion; `search_fields` + `search_requires_distinct` definition slots; phase-2.5 `validate_search_fields` call + to-many precompute |
| 3 | `django_strawberry_framework/utils/connections.py`, `django_strawberry_framework/connection.py`, `tests/filters/test_search_fields.py`, `tests/connection/` | `CONNECTION_SEARCH_KWARG` + sidecar-tuple extension; synthesized `search:` param; colorless pipeline step + conditional `.distinct()`; guard coverage |
| 4 | `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/` | uncomment all four `search_fields` tuples (fix stale `TODO-BETA-047` comment IDs → this card); live HTTP tests incl. relation path, `filter:`+`search:` intersection, visibility composition, `totalCount` under distinct |
| 5 | `docs/GLOSSARY.md` (DB + regen), `docs/TREE.md`, `README.md`, `GOAL.md`, `TODAY.md`, `CHANGELOG.md`, `KANBAN.md`/`KANBAN.html` (DB + regen) | status flips, surface mentions, `0.1.2`-line changelog entry, card wrap. NO version bump (Decision 10) |

## Helper-reuse obligations (DRY)

- `filters/inputs.py::LOOKUP_PREFIXES` is the single prefix vocabulary;
  `search_lookup_for_path` reads it, never redeclares it.
- `django_filters.utils.get_model_field` via the
  `filters/inputs.py::_model_field_for_filter` precedent for path
  resolution — no hand-rolled `_meta.get_field` walk.
- `utils/relations.py::path_traverses_to_many` for the distinct decision —
  no third reimplementation of to-many detection.
- `utils/connections.py::connection_sidecar_inputs_from_kwargs` /
  `has_connection_sidecar_input` for the non-queryset guard — extend the
  existing extraction/guard pair with a third search slot (and keep
  `CONNECTION_SIDECAR_KWARGS` in sync), do not add a parallel guard
  (Decision 3 details the required threading; the tuple alone is inert).
- The colorless search step is one function shared by `_pipeline_sync` and
  `_pipeline_async`, per the `_finalize_queryset` single-siting precedent.
- Typo-guard `ConfigurationError` messages follow the existing
  `types/base.py` Meta-gate message shape (type name + offending value +
  corrective hint).

## Edge cases and constraints

- **Whitespace-only input** — no-op; the queryset object may still be
  returned unchanged (no gratuitous `.filter(Q())`).
- **Empty declaration** (`search_fields = ()`) — declaration-time
  `ConfigurationError` (Decision 2).
- **Typo'd / unreachable path** — finalize-time `ConfigurationError`; never
  a runtime 500 on first search.
- **To-many path** (`search_fields = ("tags__name",)`) — `.distinct()`
  applied; `totalCount` and page cardinality stay correct (Decision 7).
- **`@` prefix on a non-Postgres database** — path validates, execution
  raises the database's unsupported-lookup error; documented Postgres-only
  constraint, mirroring DRF.
- **`%` / `_` / quotes in input** — literal characters (Decision 11).
- **Non-queryset consumer resolver + `search:` input** — the extended
  sidecar guard raises, matching `filter:` / `orderBy:` behavior
  (Decision 3).
- **Type declares `search_fields` but no `filterset_class`** — fully
  supported; the search step is independent of the filterset step
  (Decision 1).
- **Keyset-cursor connections** (`Meta.cursor_field`-declared) — search
  applies before slicing/fingerprinting; cursors remain stable within a
  fixed search value; changing the search string between pages is the same
  consumer contract as changing `filter:` between pages.
- **Case sensitivity** — `icontains` is ASCII-case-insensitive on SQLite
  for non-ASCII codepoints (Django-documented SQLite limitation); tests
  assert portable ASCII behavior only.
- **Thread/async safety** — the definition slots are finalize-frozen
  metadata; the resolve-time step builds a fresh `Q` per call and mutates
  nothing shared.

## Test plan

Unit (`tests/filters/test_search_fields.py`):

- `build_search_q` output shape: OR across paths, whole input, default
  `icontains`, prefix translation per entry, mixed prefixed/unprefixed.
- Empty / `None` / whitespace-only → no-op (queryset identity preserved).
- `validate_search_fields`: flat path, relation path, typo → raises with
  type/path/model in the message; empty tuple → declaration raise.
- Distinct precompute: forward-only tuple → `False`; any to-many entry →
  `True`.

Integration (`tests/filters/`, `tests/connection/`):

- SDL: `search: String` present exactly when declared; absent otherwise.
- Single-field, relation-path, and combined-with-`filterset_class` queries
  (the card's three named cases) against the package test schema.
- Post-visibility composition: a row matching the search but hidden by
  `get_queryset` never appears and never perturbs `totalCount`.
- Distinct correctness: to-many search path, one parent with two matching
  children → one edge, `totalCount == 1`.
- Sync and async pipelines both exercised (the colorless step under both
  colors).
- Non-queryset source + `search:` → guard raise.

Live HTTP (`examples/fakeshop/test_query/`, per the
[Live-first coverage mandate][glossary-live-first-coverage-mandate]):

- A search across at least one relation path
  (`category__name`-shaped) through the real `/graphql/` endpoint —
  the card's explicit DoD line.
- `filter:` + `search:` intersection live.
- Anonymous-vs-staff visibility composition live (search cannot reveal
  cascade-hidden products).

## Doc updates

- `docs/GLOSSARY.md` (via the glossary DB + `build_glossary_md.py`,
  never hand-edited): flip
  [`Meta.search_fields`][glossary-metasearch_fields] to shipped `0.1.2`;
  cross-link the new `filters/search.py` surface; fold in the spec's
  glossary terms per the shipping-slice fold-in rule.
- `README.md` / `GOAL.md` / `TODAY.md`: move search from
  "still waiting for" to shipped surface lists; GOAL's astronomy example
  needs no edit (it already declares the tuple).
- `CHANGELOG.md`: `0.1.2`-line entry (Slice 5 permission).
- `docs/TREE.md`: regen after `filters/search.py` lands (module docstring
  required by the renderer).
- `KANBAN.md` / `KANBAN.html`: card flip via DB + regen only.

## Risks and open questions

- **Term-splitting divergence (Decision 4).** The card pins whole-input
  phrase semantics; upstream ships DRF-style term-AND. Preferred answer
  for `0.1.2`: phrase semantics (card-pinned, conservatively widenable).
  Fallback if the maintainer wants upstream fidelity: adopt term-AND
  before first release of the surface — it must be decided before `0.1.2`
  ships because the two differ user-visibly on multi-word input and
  switching later is a semantic break.
- **Prefix vocabulary vs card prose (Decision 5).** The card's text names
  only `icontains`; the landed `LOOKUP_PREFIXES` seam and upstream both
  carry the DRF prefixes. Preferred: ship prefixes (seam was reserved for
  this card; verbatim-migration promise). Fallback: reject prefixed
  entries with a `ConfigurationError` naming the vocabulary as `0.1.x`
  future work — never silently treat `^name` as a literal field name.
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
- **List-field / node-field search.** The card scopes `search:` to
  connection fields. Whether [`DjangoListField`][glossary-djangolistfield]
  should grow the same argument is left open; nothing in this design
  precludes it (the colorless step is field-agnostic), but it is not
  `0.1.2` work and no card currently owns it.
- **Stale card IDs in fakeshop comments.** The commented-out declarations
  in `examples/fakeshop/apps/products/schema.py` cite `TODO-BETA-047-0.1.2`
  (a pre-renumber ID; 047 is now the beta-release card). Slice 4 corrects
  the comments as part of activation — noted here per the card-vs-tree
  conflict rule rather than silently reconciled.
- **`@`/`__search` portability.** Accepting the prefix everywhere but
  failing at execution on non-Postgres is upstream/DRF behavior, kept for
  parity. If the maintainer prefers fail-at-finalize, the validator can
  gate `@` on `django.contrib.postgres` presence — deferred as a
  follow-up question, not pinned.

## Out of scope (explicitly tracked elsewhere)

- Ranked / weighted / trigram full-text search —
  `TODO-BETA-050-0.1.2` (depends on this card; owns the `0.1.2` cut).
- The generalized deferred-key promotion sweep and
  [`Meta.aggregate_class`][glossary-metaaggregate_class] /
  [`AggregateSet`][glossary-aggregateset] — `TODO-BETA-052-0.1.3`.
- [`FieldSet`][glossary-fieldset] /
  [`Meta.fields_class`][glossary-metafields_class] composition — spec-048
  (`TODO-BETA-048-0.1.1`; ships before this card).
- The Relay `node` / `nodes` root entry points and the connection
  `totalCount` opt-in — `TODO-BETA-055-0.1.5` (the product-catalog root
  schema is already live; this card's Slice 4 owns only the four
  `search_fields` activations).
- [`Meta.choice_enum_names`][glossary-metachoice_enum_names] and the
  `0.1.4` line — untouched.

## Definition of done

- [ ] `docs/spec-049-search_fields-0_1_2.md` (this file) is the card's
  spec of record.
- [ ] `filters/search.py` ships `build_search_q` /
  `search_lookup_for_path` / `validate_search_fields`; the
  `filters/sets.py` TODO seam is removed.
- [ ] `Meta.search_fields` validates at declaration (shape) and finalize
  (paths), lands on `DjangoTypeDefinition`, and is promoted to
  `ALLOWED_META_KEYS`.
- [ ] Every connection field serving a declaring type carries a nullable
  `search: String` argument that produces the OR'd fan-out with correct
  distinct behavior, post-visibility, intersecting with `filter:`.
- [ ] `tests/filters/test_search_fields.py` covers single-field,
  relation-path, and combined-with-filterset cases; sync and async.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercises a
  search across at least one relation path.
- [ ] Slice 5 doc set updated; `CHANGELOG.md` `0.1.2`-line entry written.
- [ ] **No version bump** — the `0.1.2` quintet belongs to the
  `TODO-BETA-050-0.1.2` joint cut (Decision 10).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-filter_input_type]: GLOSSARY.md#filter_input_type
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-metaaggregate_class]: GLOSSARY.md#metaaggregate_class
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metachoice_enum_names]: GLOSSARY.md#metachoice_enum_names

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
