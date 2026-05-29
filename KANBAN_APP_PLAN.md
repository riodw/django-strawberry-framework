# Plan — `kanban` example app (dogfood the framework on its own roadmap)

Status: **draft plan, pre-build.** Working document only.

## 1. Intent

Add a new app to the fakeshop example — `examples/fakeshop/apps/kanban/` — whose
models are a faithful, relational rendering of this repository's own
[`KANBAN.md`][kanban] board. Once the board lives as ORM data, the **framework
itself** (the same `DjangoType` + filter subsystem we ship) exposes it over
`/graphql/`, so the project's roadmap becomes a queryable GraphQL surface built
on the very thing the roadmap is tracking. It is the most on-mission example we
can ship: the framework demonstrates its read-side end-to-end by serving its
own project-management data.

The **full intention** has three phases:

1. **Models + schema** *(this plan's focus)* — model the board as Django models
   and wire them to GraphQL through `DjangoType`, filtersets, and a `Query`,
   exactly as the `library` / `products` / `scalars` apps already do.
2. **Import bridge** — a management command that parses `KANBAN.md` and
   populates the models, so the board-as-prose and the board-as-data stay in
   sync (idempotent re-import).
3. **Static dashboard** *(deferred — see §9)* — a pre-commit / CI step that
   queries the kanban schema through the framework, renders the result into a
   static HTML page, and publishes it via GitHub Pages so anyone can visualize
   the project's status. **Specifics intentionally omitted here; we will design
   phase 3 separately.**

This document concentrates on phases 1 and 2, and the overwhelming majority on
phase 1 (the model graph and its schema linkage).

## 2. Tracking & scope

Per the maintainer's direction, **this app is intentionally not tracked in
`KANBAN.md` or `docs/SPECS/`** — it gets no card and no formal spec. The only
durable record will be a brief `CHANGELOG.md` entry when it lands (and this
working plan, which can be deleted or relocated once we converge). It ships as
example/demo surface, not as part of the published `django_strawberry_framework`
package.

It also doubles as a deliberately broad **regression and demo bed**: the model
graph below is chosen to exercise every relation cardinality the framework
supports under an intentionally FK-dense, highly-normalized shape (now with a
heavy O2O fan-out and audit timestamps too), and to be the natural demo surface
for the subsystems still on the roadmap (ordering, aggregation, field-selection,
permissions, mutations) as each one ships.

---

## 3. Domain model (phase 1, part A — the core of this plan)

### 3.1 Design philosophy — fully normalized lookup tables

**Every value that can appear on more than one card is its own model, not an
inline `choices`/enum.** So each closed vocabulary the board uses for a card's
labelled lines — `Status`, `Priority`, `Severity`, `Relative size`, the
`Status:`-line keyword, the parity level, the milestone, the target version, and
the bullet-section kind — becomes a small lookup table that cards (or card items
/ parity edges) point at by foreign key.

Two consequences:

1. **Faithful + queryable from either side.** "All `DONE` cards" is
   `status(key: "done") { cards { … } }` *or*
   `cards(filter: {status: {key: {exact: "done"}}})` — the option owns its
   reverse-FK set of cards.
2. **A relation-density showcase.** Where the `library` app proves one of each
   relation kind and the `scalars` app proves the converter table, the `kanban`
   app proves the framework holds up under a **FK-heavy, highly-normalized**
   graph: roughly a dozen lookup tables, many forward FKs + reverse-FK
   collections, a self-referential M2M, an M2M-through with edge data, an O2O
   spec link, **a UUID side-table linked one-to-one to every model**, and audit
   timestamps everywhere. (Inline `choices`/enum conversion stays covered by
   `Book.circulation_status` in the `library` app; this app deliberately uses
   **zero** inline enums.)

### 3.2 Base classes — timestamps + the UUID side-table

Two pieces every model leans on.

**(a) `TimeStampedModel` — abstract audit base.** All kanban models inherit it,
so `created_date` / `updated_date` land on every table without repeating the
fields ~15 times (the products app inlines the same two fields; an abstract base
is the DRY equivalent for this many models).

```python
class TimeStampedModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_date = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
```

**(b) `UUIDModel` — a central UUID side-table (per the reference pattern).**
This is **not** an abstract mixin and **not** a `uuid` column on each model. It
is one concrete table whose **UUID primary key** is the stable, opaque
identifier for whichever single domain row its (non-null) one-to-one link points
at. Every domain model reaches its UUID through the reverse accessor
`instance.uuid.id`. A `post_save` signal creates the row automatically the first
time any linked model is saved.

```python
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # One nullable O2O per kanban model. Field names match
    # `sender._meta.model_name` (lowercase, no separators) so the signal below
    # needs no special-casing — e.g. `targetversion`, `parityclaim`, `carditem`.
    milestone     = models.OneToOneField("Milestone",     null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    status        = models.OneToOneField("Status",        null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    priority      = models.OneToOneField("Priority",      null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    severity      = models.OneToOneField("Severity",      null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    relativesize  = models.OneToOneField("RelativeSize",  null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    planningstate = models.OneToOneField("PlanningState", null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    upstream      = models.OneToOneField("Upstream",      null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    paritylevel   = models.OneToOneField("ParityLevel",   null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    section       = models.OneToOneField("Section",       null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    targetversion = models.OneToOneField("TargetVersion", null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    specdoc       = models.OneToOneField("SpecDoc",       null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    card          = models.OneToOneField("Card",          null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    parityclaim   = models.OneToOneField("ParityClaim",   null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    carditem      = models.OneToOneField("CardItem",      null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")
    label         = models.OneToOneField("Label",         null=True, blank=True, on_delete=models.CASCADE, related_name="uuid")

    def __str__(self):
        return str(self.id)


@receiver(post_save, sender=Milestone)
@receiver(post_save, sender=Status)
# ... one decorator per kanban model ...
@receiver(post_save, sender=Card)
def create_uuid_model(sender, instance, created, **kwargs):
    if created:
        UUIDModel.objects.create(**{sender._meta.model_name: instance})
```

Notes / consequences:

- **Two stable identifiers now coexist** — be intentional about which clients
  use. Relay-node domain types (e.g. `CardType`) expose a Relay global ID
  derived from the **integer** PK; the UUID is a *separate*, cross-system-stable
  handle reached via `card { uuid { id } }`. `UUIDModel` itself stays **non-Relay**.
- `UUIDModel` does **not** inherit `TimeStampedModel` necessarily — include it
  only if we want timestamps on the registry too (cheap; recommend yes for
  uniformity, its explicit UUID `id` still wins as PK over any base).
- This single model adds ~15 one-to-one relations resolving in one
  `finalize_django_types()` pass — the heaviest O2O finalization in the example
  tree, and the reason O2O becomes the most-exercised cardinality here.

### 3.3 Lookup (option) models

Each is a tiny reference table inheriting `TimeStampedModel` and sharing a common
shape — a canonical `key`, a human `label`, an `order` — plus a few extras.
**Each is its own model precisely because its rows recur across many cards.**

| Model | Rows | Extras | Reverse |
|---|---|---|---|
| `Milestone` | `alpha` / `beta` / `stable` | `version_floor`, `version_ceiling`, `description` | `cards`, `target_versions` |
| `Status` | `todo` / `wip` / `blocked` / `done` | — | `cards` (the board column) |
| `Priority` | `high` / `medium` / `low` | — | `cards` |
| `Severity` | `major` / `medium` / `low` | — | `cards` |
| `RelativeSize` | `xs` / `s` / `m` / `l` / `xl` | `rank` (XS=0 … XL=4) | `cards`, `cards_high` |
| `PlanningState` | `planned` / `needs_spec` / `in_progress` / `blocked` / `shipped` | — | `cards` |
| `Upstream` | `graphene_django` / `strawberry_django` | `emoji` (⚛️ / 🍓), `homepage` | `parity_claims` |
| `ParityLevel` | `required` / `adjacent` | — | `parity_claims` |
| `Section` | `scope` / `definition_of_done` / `foundation_seam` / `files_touched` / `verified_upstream` / `arch_posture` / `why_it_matters` / `dependencies_note` / `other` | — | `items` |

Common shape:

```python
class Status(TimeStampedModel):
    key = models.SlugField(unique=True)        # "done"
    label = models.TextField()                 # "Done"
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.label
    # created_date / updated_date inherited from TimeStampedModel
    # `.uuid` reverse accessor provided by UUIDModel.status
```

### 3.4 `TargetVersion` — the package version a card targets ("target_number")

The `X.Y.Z` a card ships / is planned to ship in. Its own model because a
version applies to many cards (lots share `0.0.8`, `0.0.11`, …). "target_number"
→ `TargetVersion.number`, reached from a card via `Card.target_version`.

| Field | Type | Notes |
|---|---|---|
| `number` | `TextField(unique=True)` | the dotted version, e.g. `0.0.8` |
| `milestone` | `ForeignKey(Milestone, related_name="target_versions")` | FK + reverse-FK |
| `shipped_on` | `DateField(null=True, blank=True)` | null ⇒ still planned; exercises the nullable `DateField` converter |
| `git_ref` | `TextField(blank=True, default="")` | tag / commit (e.g. `72f6cd9`) |

Inherits `TimeStampedModel`. Reverse: `cards` (FK from `Card.target_version`).

### 3.5 `SpecDoc` — the spec-file link

Per request: "just a name and link to the spec file in GitHub."

| Field | Type | Notes |
|---|---|---|
| `name` | `TextField` | e.g. `spec-021-filters-0_0_8` |
| `url` | `URLField` | GitHub link to the spec file |

Inherits `TimeStampedModel`. Linked **O2O** from `Card.spec` (§3.6).

### 3.6 `Card` — the central entity

Inherits `TimeStampedModel`. Every option line is a foreign key into a lookup
model above; the `uuid` and `dependents` accessors are reverse relations.

| Field | Type | Notes |
|---|---|---|
| `title` | `TextField(unique=True)` | **stable natural key** (the board says to reference cards by title, not `NNN`) |
| `number` | `PositiveIntegerField` | the `NNN`; explicitly **unstable** and per-card — a plain integer, never a key, never a lookup |
| `status` | `ForeignKey(Status, related_name="cards")` | the column |
| `milestone` | `ForeignKey(Milestone, null=True, blank=True, related_name="cards")` | nullable — dropped on `DONE` cards |
| `target_version` | `ForeignKey(TargetVersion, related_name="cards")` | the `X.Y.Z` it targets |
| `priority` | `ForeignKey(Priority, null=True, blank=True, related_name="cards")` | |
| `severity` | `ForeignKey(Severity, null=True, blank=True, related_name="cards")` | absent on some WIP cards |
| `relative_size` | `ForeignKey(RelativeSize, related_name="cards")` | |
| `relative_size_high` | `ForeignKey(RelativeSize, null=True, blank=True, related_name="cards_high")` | only set for ranges ("S–M"); a 2nd FK into the same lookup |
| `planning_state` | `ForeignKey(PlanningState, related_name="cards")` | the `Status:`-line keyword |
| `planning_note` | `TextField(blank=True, default="")` | rest of the `Status:` line |
| `summary` | `TextField(blank=True, default="")` | one-line gloss |
| `body` | `TextField(blank=True, default="")` | "Why it matters" / narrative prose |
| `spec` | `OneToOneField(SpecDoc, null=True, blank=True, related_name="card")` | **O2O** — `card.spec` / `specdoc.card` |
| `created_date` / `updated_date` | inherited | from `TimeStampedModel` |
| `dependencies` | `ManyToManyField("self", symmetrical=False, related_name="dependents", blank=True)` | **self-referential M2M** |
| `parity` | `ManyToManyField(Upstream, through="ParityClaim", related_name="cards", blank=True)` | **M2M-through** — level lives on the edge |
| `labels` | `ManyToManyField("Label", related_name="cards", blank=True)` | optional plain M2M |

Plus `Meta.ordering = ("number",)` and a `__str__` returning the title.
Reverse accessors: `items`, `parity_claims`, `dependents`, `uuid`.

### 3.7 `ParityClaim` — the parity edge (through model)

This is how "Parity" is modeled. Rather than one flat `Parity` lookup, parity is
decomposed into **two** reusable option models — `Upstream` (which project) and
`ParityLevel` (required vs adjacent) — joined per-card on a through model, so a
card can be "⚛️ required" **and** "🍓 parity-adjacent" at once and you can query
by either dimension independently. Inherits `TimeStampedModel`.

| Field | Type | Notes |
|---|---|---|
| `card` | `ForeignKey(Card, related_name="parity_claims")` | |
| `upstream` | `ForeignKey(Upstream, related_name="parity_claims")` | |
| `level` | `ForeignKey(ParityLevel, related_name="parity_claims")` | required / adjacent |
| `note` | `TextField(blank=True, default="")` | the parenthetical rationale |
| `Meta.constraints` | `UniqueConstraint(card, upstream)` | one claim per (card, upstream) |

> **Decision flag.** I read "Parity should be its own model" as promoting the
> parity *level* to the `ParityLevel` lookup (keeping `Upstream` + the
> `ParityClaim` edge) — the more-normalized reading. If you'd rather have a
> **single flat `Parity` lookup** (rows like `⚛️&🍓 required`, `🍓 adjacent`)
> with a plain `Card.parity` FK, say so and I'll collapse §3.7 to one model.

### 3.8 `CardItem` — the bulleted sections (reverse-FK list)

Inherits `TimeStampedModel`.

| Field | Type | Notes |
|---|---|---|
| `card` | `ForeignKey(Card, related_name="items")` | reverse-FK list |
| `section` | `ForeignKey(Section, related_name="items")` | which bullet list it belongs to |
| `text` | `TextField` | the bullet content |
| `order` | `PositiveIntegerField(default=0)` | preserves bullet order |
| `is_complete` | `BooleanField(default=False)` | only meaningful for `definition_of_done` |
| `Meta.ordering` | `("card", "section", "order")` | |

### 3.9 `Label` — optional tag (plain M2M)

`key` (`SlugField(unique=True)`) + `color` (`TextField`); inherits
`TimeStampedModel`. Cross-cutting tags (`security`, `dx`, `migration-aid`, …).
Optional; include only if we want the plain-M2M path represented separately from
the through-model one.

### 3.10 What each relation showcases

| Relation | Cardinality | Path exercised |
|---|---|---|
| `Card → {Status, Priority, Severity, RelativeSize ×2, PlanningState, Milestone, TargetVersion}` | FK | forward FK + a reverse `cards` collection on every lookup |
| `TargetVersion → Milestone` | FK | a second FK hop (`card.targetVersion.milestone`) |
| `CardItem → {Card, Section}` | FK | reverse-FK lists (`card.items`, `section.items`) |
| `ParityClaim → {Card, Upstream, ParityLevel}` | FK | through-model edges (`card.parityClaims`) |
| `Card ↔ SpecDoc` | O2O | forward + reverse one-to-one (`card.spec`) |
| **`UUIDModel → every model`** | **O2O × ~15** | forward O2O fan-out + a reverse `.uuid` accessor on every type + UUID PK — the heaviest O2O exercise in the tree |
| `Card.dependencies` | M2M (self, asymmetric) | self-referential M2M + reverse (`dependents`) |
| `Card.parity` ↔ `Upstream` | M2M (through) | explicit through model carrying edge data |
| `Card.labels` ↔ `Label` | M2M (plain) | mirrors `Book.genres` |

This is, deliberately, the broadest, most FK-dense, and most O2O-dense relation
graph in the example tree.

### 3.11 Open model decisions (resolve before building)

- **Parity shape** — decomposed (recommended) vs. single flat `Parity` lookup (§3.7).
- **Timestamps mechanism** — abstract `TimeStampedModel` base (recommended) vs.
  inline `created_date`/`updated_date` per model (matches the products app).
- **`UUIDModel` O2O scope** — link *all* models (per the directive, chosen) vs.
  only the content models (`Card` / `CardItem` / `ParityClaim` / `TargetVersion`
  / `SpecDoc`), skipping the tiny lookups.
- **Verify before relying on it** — (a) `UUIDField`-as-primary-key converts
  cleanly in `DjangoType`; (b) abstract-base-inherited fields
  (`created_date`/`updated_date`) convert; (c) `finalize_django_types()` handles
  ~15 simultaneous O2O relations; (d) `ManyToManyField(through=…)` converts
  cleanly (fallback: expose `ParityClaim` only via reverse-FK).
- **Relative-size ranges** — two FKs (chosen) vs. single FK + free-text note.
- **`SpecDoc` link** — O2O (chosen) vs. FK (one spec referenced by many cards).
- **Snapshot / narrative blocks** — model as an optional `BoardNote`, or leave
  out (recommend: leave out for v1).
- **Which types are Relay nodes** (see §4.2).

---

## 4. Schema layer (phase 1, part B — linking models to GraphQL via the framework)

Module: `examples/fakeshop/apps/kanban/schema.py`. A straight application of the
same pattern the other three apps use — one `DjangoType` per model, a `Query`
with resolvers, registered into the project schema.

### 4.1 One `DjangoType` per model

```python
import strawberry
from strawberry import relay
from strawberry.types import Info

from apps.kanban import filters, models
from django_strawberry_framework import DjangoType, OptimizerHint
from django_strawberry_framework.filters import filter_input_type


class CardType(DjangoType):
    class Meta:
        model = models.Card
        fields = (
            "id", "title", "number",
            "created_date", "updated_date",
            "planning_note", "summary", "body",
            "status", "priority", "severity",          # FK lookups
            "relative_size", "relative_size_high",      # FK lookups (range pair)
            "planning_state", "milestone", "target_version",
            "spec", "uuid",                             # O2O (forward + reverse from UUIDModel)
            "items", "parity_claims",                   # reverse FK
            "dependencies", "dependents",               # self-M2M (both directions)
            "parity", "labels",                         # M2M (through + plain)
        )
        interfaces = (relay.Node,)            # global IDs + own-PK GlobalID filter path
        filterset_class = filters.CardFilter
        optimizer_hints = {
            "items": OptimizerHint.prefetch_related(),
            "parity_claims": OptimizerHint.prefetch_related(),
        }


class UUIDModelType(DjangoType):
    """Non-Relay; exposes the UUID `id`. Forward O2O back-links available but
    mostly null (exactly one is set per row)."""
    class Meta:
        model = models.UUIDModel
        fields = ("id",)                      # the UUID; exercises UUIDField-as-PK
```

The lookup / supporting types — `MilestoneType`, `StatusType`, `PriorityType`,
`SeverityType`, `RelativeSizeType`, `PlanningStateType`, `UpstreamType`,
`ParityLevelType`, `SectionType`, `TargetVersionType`, `SpecDocType`,
`CardItemType`, `ParityClaimType` (and `LabelType`) — follow the same shape,
each selecting its `created_date` / `updated_date` / `uuid` plus its own fields,
with optional `interfaces = (relay.Node,)` and a `filterset_class`. Declaration
order can be intentionally shuffled (as the `library` app does) to keep
exercising pending-relation finalization through a real import path.

### 4.2 Filtersets — the payoff

Module: `examples/fakeshop/apps/kanban/filters.py`. This is *why* the app matters
as a demo. Because every option field is a foreign key, filtering "by status /
priority / size / milestone / version" is a `RelatedFilter` onto a small lookup
filterset that matches on `key` (or `label`). So the kanban filter surface is
**`RelatedFilter`-dense** — it exercises the cross-relation filter path from
`DONE-021-0.0.8` far harder than any other example app, while still meaning
something concrete ("all `DONE` cards in milestone `ALPHA` sized `XL` with a
🍓-required parity claim").

```python
from django_strawberry_framework.filters import FilterSet, RelatedFilter

from . import models


class StatusFilter(FilterSet):
    class Meta:
        model = models.Status
        fields = {"key": "__all__", "label": "__all__"}


class CardFilter(FilterSet):
    status = RelatedFilter("apps.kanban.filters.StatusFilter", field_name="status")
    priority = RelatedFilter("apps.kanban.filters.PriorityFilter", field_name="priority")
    severity = RelatedFilter("apps.kanban.filters.SeverityFilter", field_name="severity")
    relative_size = RelatedFilter("apps.kanban.filters.RelativeSizeFilter", field_name="relative_size")
    milestone = RelatedFilter("apps.kanban.filters.MilestoneFilter", field_name="milestone")
    target_version = RelatedFilter("apps.kanban.filters.TargetVersionFilter", field_name="target_version")
    parity = RelatedFilter("apps.kanban.filters.UpstreamFilter", field_name="parity")
    items = RelatedFilter("apps.kanban.filters.CardItemFilter", field_name="items")
    # self-referential RelatedFilter — exercises the cycle-safe expansion path
    dependencies = RelatedFilter("apps.kanban.filters.CardFilter", field_name="dependencies")

    class Meta:
        model = models.Card
        # The only direct scalar lookups left on Card; everything categorical is
        # a RelatedFilter above. Per-field "__all__" expands each to its full
        # concrete-lookup set (the 0.0.8 feature).
        fields = {"id": "__all__", "title": "__all__", "number": "__all__"}
```

> **Relay-node decision:** make at least `CardType` a Relay node so the own-PK
> `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` path (the `id: { in: [...] }`
> branch from `DONE-021-0.0.8`) is exercised with real global IDs, and keep one
> filterset non-Relay (e.g. `CardItemType`) so the plain-integer
> `BaseInFilter → list[int]` branch stays covered too.

### 4.3 `Query` + registration

`Query` follows the established resolver shape (queryset → optional `filter` arg
via `filter_input_type(...)` → `apply_sync`):

```python
@strawberry.type
class Query:
    @strawberry.field
    def all_cards(
        self,
        info: Info,
        filter: filter_input_type(filters.CardFilter) | None = None,  # noqa: A002
    ) -> list[CardType]:
        queryset = models.Card.objects.order_by("number")
        if filter is not None:
            queryset = filters.CardFilter.apply_sync(filter, queryset, info)
        return queryset

    @strawberry.field
    def all_statuses(self, info: Info, ...) -> list[StatusType]: ...
    # ... all_target_versions(), all_milestones(), board(), card_by_title(), etc.
```

A `board` resolver (cards grouped/orderable by `status`) is the natural shape the
phase-3 dashboard will consume.

Two wiring edits, mirroring how the other apps register:

- **`config/settings.py`** → add `"apps.kanban.apps.KanbanConfig"` to
  `INSTALLED_APPS`.
- **`config/schema.py`** → `class Query(LibraryQuery, ProductsQuery,
  ScalarsQuery, KanbanQuery): ...` (import `KanbanQuery`).
  `finalize_django_types()` and the `DjangoOptimizerExtension` schema
  construction stay unchanged.

Plus `makemigrations kanban` + `migrate`. The `post_save` UUID signal connects
via the app's `ready()` (or inline `@receiver` decorators in `models.py`, as the
reference does).

### 4.4 Forward-looking slots (mention only — do not build now)

The kanban dataset is the obvious demo bed for subsystems still on the roadmap;
the app should be *structured* so each slots in without reshaping the models:

- **`orderset_class`** (`WIP-ALPHA-022-0.0.8`) — order cards by `number`,
  `priority.order`, `relative_size.rank`, `target_version.number`, or
  `updated_date` (the timestamps make "recently touched" orderings trivial).
- **`aggregate_class`** (Layer 3) — counts per `status` / `milestone` /
  `relative_size`; exactly the data a dashboard renders.
- **`fields_class`** / **`DjangoConnectionField`** (`TODO-ALPHA-024-0.0.9`) —
  Relay pagination over `all_cards`.
- **permissions** (`TODO-ALPHA-027-0.0.10`) — hide `blocked` internals behind a
  `get_queryset` / per-field gate.
- **mutations** (`TODO-ALPHA-028-0.0.11`) — eventually, move a card between
  columns over GraphQL.

None are in scope for the initial build.

---

## 5. Data import bridge (phase 2)

Module: `examples/fakeshop/apps/kanban/management/commands/import_kanban.py`
(mirrors the `products` app's `seed_data` command convention).

- **Source:** the repo-root `KANBAN.md`.
- **Parser:** line-oriented state machine. Card headers match
  `^### (?P<id>(TODO|WIP|BLOCKED|DONE)(-(ALPHA|BETA|STABLE))?-\d{3}-\d+\.\d+\.\d+) — (?P<title>.+)$`,
  then labelled lines (`Priority:`, `Parity:`, …), then `<Section>:`-introduced
  bullet lists.
- **Load order (idempotent):**
  1. Upsert every **lookup table** (`Status`, `Priority`, `Severity`,
     `RelativeSize`, `PlanningState`, `Milestone`, `Upstream`, `ParityLevel`,
     `Section`) via `get_or_create` on each option's `key`.
  2. Upsert `TargetVersion` (split from the card ID) and `SpecDoc`.
  3. Create each `Card`, resolving its FK lookups and splitting the ID into
     `status` / `milestone` / `number` / `target_version`.
  4. Second pass: attach `CardItem`s per section; resolve `Dependencies` bullets
     + parity glyphs into the M2M / through edges (so forward references resolve).
- **Idempotency key:** **`Card.title`** (the board's own stable identifier).
- **UUID signal caveat:** the importer must create rows with `.save()` /
  `.objects.create()` (**not** `bulk_create`, which does not fire `post_save`),
  so each `UUIDModel` row is auto-created. Dataset is small (~50 cards), so
  per-instance creates are fine. `created_date` / `updated_date` populate
  automatically.
- **Scope note:** the parser is example-app code, not framework code; it stays
  simple and may skip the narrative Snapshot blocks.

Open decision: parse `KANBAN.md` live at import time vs. load a committed parsed
JSON/fixture snapshot (more deterministic for CI). Lean toward parsing directly.

---

## 6. File tree & wiring

```
examples/fakeshop/apps/kanban/
    __init__.py
    apps.py                       # KanbanConfig(name="apps.kanban"); ready() connects signals
    models.py                     # TimeStampedModel (abstract) + UUIDModel (+ post_save signal)
                                  # lookups: Milestone, Status, Priority, Severity,
                                  #   RelativeSize, PlanningState, Upstream, ParityLevel, Section
                                  # + TargetVersion, SpecDoc
                                  # + Card, ParityClaim, CardItem, (Label)
    filters.py                    # CardFilter + per-lookup FilterSets
    schema.py                     # *Type DjangoTypes + Query
    admin.py                      # register models so the board is browsable at /admin
    management/
        __init__.py
        commands/
            __init__.py
            import_kanban.py      # KANBAN.md -> DB (idempotent upsert by title)
    migrations/__init__.py
    tests/__init__.py

# edits to existing files
examples/fakeshop/config/settings.py   # + "apps.kanban.apps.KanbanConfig"
examples/fakeshop/config/schema.py     # + KanbanQuery in the composed Query
examples/fakeshop/test_query/test_kanban_api.py   # new live HTTP tests
```

---

## 7. Testing

- **Live HTTP** (`examples/fakeshop/test_query/test_kanban_api.py`):
  - filter cards by `status` / `milestone` / `relative_size` via `RelatedFilter`
    on the lookup `key`.
  - own-PK Relay `id: { in: [...] }` against `CardType`.
  - self-referential `dependencies` `RelatedFilter` traversal.
  - reverse-FK / M2M-through selection
    (`card { parityClaims { level { key } upstream { emoji } } }`).
  - O2O selection both ways: `card { spec { name url } }` and
    **`card { uuid { id } createdDate updatedDate }`** (UUID side-table + timestamps).
  - reverse-FK from a lookup (`status(key:"done") { cards { title } }`).
- **Unit** (`examples/fakeshop/apps/kanban/tests/`):
  - `import_kanban` parser round-trip on a small fixed `KANBAN.md` excerpt.
  - the `post_save` signal creates a `UUIDModel` row on `Card` create, and
    `card.uuid.id` is a stable UUID.

The package's coverage gate (`fail_under = 100`) applies to the
`django_strawberry_framework` package only.

---

## 8. Build order (suggested)

1. `models.py` (incl. `TimeStampedModel`, `UUIDModel`, signal) + `apps.py` +
   `makemigrations` / `migrate`.
2. `import_kanban` command + parser/signal tests; load the real board.
3. `filters.py` + `schema.py`; register in `settings.py` + `config/schema.py`.
4. Live `test_kanban_api.py`; run the full suite + ruff.
5. Brief `CHANGELOG.md` entry.

---

## 9. Phase 3 — static dashboard via CI + GitHub Pages (deferred)

The end goal is that a **pre-commit or CI step queries the kanban schema through
the framework and renders the result into a static HTML page published on GitHub
Pages**, so the project's live status is visible to anyone without running the
example. **The specifics — how the query runs headlessly, the HTML/templating
approach, and the Pages publish workflow — are intentionally left for a separate
discussion and are not designed in this plan.**

---

## 10. Summary of decisions to confirm before building

1. Keep this plan at repo root (`KANBAN_APP_PLAN.md`) — outside `KANBAN.md` /
   `docs/SPECS/`.
2. **Parity shape** — decomposed (recommended) vs. single flat `Parity` lookup (§3.7).
3. **Timestamps** — abstract `TimeStampedModel` base (recommended) vs. inline.
4. **`UUIDModel` O2O scope** — all models (chosen) vs. content models only.
5. **M2M-through / UUID-PK / abstract-base / 15-O2O finalization** — confirm via
   a spike, with fallbacks in §3.11.
6. **Relative-size ranges** — two FKs (recommended) vs. single FK + note.
7. **`SpecDoc` link** — O2O (recommended) vs. FK.
8. **Narrative Snapshot blocks** — leave out of the model (recommended).
9. **Relay nodes** — `CardType` yes (+ `UUIDModel` non-Relay); keep one lookup
   non-Relay (recommended).
10. **Import source** — parse `KANBAN.md` live (recommended) vs. snapshot fixture.

[kanban]: ./KANBAN.md
