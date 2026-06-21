# Parity review — `django-strawberry-framework` vs. `django-graphene-filters`

Scope: not a single-spec review. This checks whether the package is on track to
recreate the **feature set** of the released, feature-complete reference
`django-graphene-filters` (DGF) `1.0.0`, per `GOAL.md` ("Working reference"),
on the custom Strawberry foundation. ALPHA — many cards are still unbuilt; that
is expected and not flagged here. Below are only points that **contradict** the
stated goal of recreating DGF's feature set.

## Verdict

On track. Every public symbol in DGF's `__all__`
(`django_graphene_filters/__init__.py`) is either shipped or has a dedicated
beta card:

| DGF public surface | This package | Status |
| --- | --- | --- |
| `AdvancedFilterSet`, `RelatedFilter` / `BaseRelatedFilter` | `FilterSet`, `RelatedFilter` (collapsed to one symbol, spec-027 D2) | shipped `DONE-027-0.0.8` |
| `AdvancedOrderSet`, `RelatedOrder` / `BaseRelatedOrder` | `OrderSet`, `RelatedOrder` | shipped `DONE-028-0.0.8` |
| `AdvancedDjangoFilterConnectionField` | `DjangoConnectionField` | shipped `DONE-030-0.0.9` |
| `apply_cascade_permissions` | `apply_cascade_permissions` + async `aapply_cascade_permissions` | shipped `DONE-034-0.0.10` |
| `AdvancedDjangoObjectType` | `DjangoType` | shipped — **except node-sentinel redaction (see F1)** |
| `AdvancedFieldSet` | `FieldSet` (`Meta.fields_class`) | planned `TODO-BETA-046-0.1.1` |
| `Meta.search_fields` (basic OR'd `icontains`) | `search_fields` | planned `TODO-BETA-047-0.1.2` |
| `AnnotatedFilter`, `SearchQueryFilter`, `SearchRankFilter`, `TrigramFilter` (+ input types) | same names | planned `TODO-BETA-048-0.1.2` |
| `AdvancedAggregateSet`, `RelatedAggregate` | `AggregateSet`, `RelatedAggregate` (`Meta.aggregate_class`) | planned `TODO-BETA-049-0.1.3` |

The architecture also reproduces DGF's *enabling* properties named in `GOAL.md`:
declarative `Meta` sidecars, lazy related-class references, generated types with
stable class-derived names, layered/cascade permissions, sync+async paths, and
Relay-node output. Plus net-new value DGF lacks (selection-aware N+1 optimizer,
mutations, `Upload`/file-image, model-anchored GlobalID). No DGF public capability
is silently missing from the roadmap.

The only points that conflict with "recreate the same feature set":

## Findings

### [P2] Node-sentinel redaction (`isRedacted`) is a public DGF surface deliberately dropped

DGF's `AdvancedDjangoObjectType` ships a first-class, SDL-visible redaction tier:
`is_redacted = graphene.Boolean(...)` (`django_graphene_filters/object_type.py:137`),
backed by `_make_sentinel` (`:200`) and a `get_node` (`:251`) that returns a
`pk=0` sentinel **in place of** a hidden row so a non-null FK to a hidden target
still resolves (the sentinel chain). This is consumer-visible API, not an internal.

This package consciously chose the opposite model — row exclusion via
`get_queryset` + `apply_cascade_permissions` (spec-034 Decision 6) — and the
`FieldSet` card explicitly lists node-sentinel redaction as a **Non-goal**
(`KANBAN.md`, `TODO-BETA-046-0.1.1` notes: *"The package deliberately did not
adopt this tier… Revisit only if strict django-graphene-filters node-sentinel
parity is explicitly wanted, and note it conflicts with the row-narrowing
model."*).

Why it's flagged: the goal is to recreate DGF's feature set, and this is the one
public DGF behavior with **no equivalent and no card** — it's intentionally
excluded. That is a defensible design call (row-narrowing avoids the existence-leak
and pk=0 footguns), but it means a DGF consumer relying on `isRedacted` / sentinel
masking cannot port verbatim. Needs a conscious owner decision: either (a) accept
the divergence and state it as an explicit, documented exception to "feature
parity" in `GOAL.md` / a migration guide, or (b) add a card to recreate the
sentinel tier behind an opt-in. Today it sits as a non-goal buried in a card note,
which contradicts the top-level parity promise without surfacing the trade-off.

### [P3] DGF's configurable filter/logic key namespace is not reproduced

DGF lets the schema author rename the filter-tree keys via settings:
`DJANGO_GRAPHENE_FILTERS = {"FILTER_KEY": ..., "AND_KEY": ..., "OR_KEY": ...,
"NOT_KEY": ...}` (`django_graphene_filters/conf.py:13-16`, defaults
`filter`/`and`/`or`/`not`).

This package hardcodes the GraphQL names: `_LOGIC_KEYS = (("and_", "and"),
("or_", "or"), ("not_", "not"))` (`django_strawberry_framework/filters/inputs.py:130`),
and the settings namespace `DJANGO_STRAWBERRY_FRAMEWORK` carries only
`APPLY_UPSTREAM_PATCHES` (`conf.py`). There is no way to rename the operator keys
or the `filter` argument.

Low severity and possibly intentional (fixed names are simpler and arguably
better), but it is a real DGF capability with no analogue and no card. Either add
it to a beta card's scope or note it as an accepted, out-of-parity simplification.

## Notes / parity watch items (not yet actionable — for the beta specs)

- **Aggregation config surface (`TODO-BETA-049`).** DGF's aggregate subsystem
  ships tunable safety limits and an async opt-in as settings: `AGGREGATE_MAX_VALUES`,
  `AGGREGATE_MAX_UNIQUES`, `ASYNC_AGGREGATES` (`django_graphene_filters/conf.py`).
  The card captures the `compute`/`acompute` split and stat surface but not these
  config knobs — confirm they're in scope when `spec-aggregates` is authored, or
  consciously drop them.
- **Postgres FTS search shortcuts (`TODO-BETA-048`).** Verify whether DGF's
  prefix-shortcut search operators (e.g. `^ = @ $`) are part of the surface being
  ported, or intentionally left out; the card describes the
  `SearchQuery`/`SearchRank`/`Trigram` classes but not the shortcut syntax.

These are reminders for spec time, not gaps to fix now.
