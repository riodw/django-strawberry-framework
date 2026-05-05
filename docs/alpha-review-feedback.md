# Docs review feedback for 0.0.4 consolidation

Scope: read the in-flight diff (`KANBAN.md`, `README.md`, `docs/README.md`, `docs/TREE.md`, `docs/FEATURES.md`) as if I were a Django/DRF developer landing on this repo cold and deciding whether to adopt it. The behavior-consolidation pass already proposed in this file's previous version is solid — the README is much shorter, [`docs/FEATURES.md`](FEATURES.md) is honest about shipped/planned/deferred, [`docs/TREE.md`](TREE.md) is now scoped as the architecture reference. The miss is that the docs are still oriented around *describing the package* rather than *getting a user productive in the first three minutes*. This file lays out the gaps and the punchier language to close them.

The previous behavior-consolidation outline (sections "Proposed README shape", "Consolidations", "Spec references to remove or rewrite", "CHANGELOG condensation", "Spec archive/delete step") is still valid and not repeated here — apply both passes together.

## Top oversights

### 1. No code anywhere in user-facing docs

The whole pitch is "Meta classes, not decorators." Neither [`README.md`](../README.md), [`docs/README.md`](README.md), nor [`docs/FEATURES.md`](FEATURES.md) shows a single `class Meta` block. A user has to clone the repo and read [`examples/fakeshop/`](../examples/fakeshop/) to see what consumer code actually looks like.

Fix: add a code-first quickstart near the top of [`docs/README.md`](README.md). Suggested block:

````markdown
## Quick start

```python
import strawberry
from django_strawberry_framework import DjangoType, DjangoOptimizerExtension
from myapp.models import Category, Item

class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")

class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category")

@strawberry.type
class Query:
    @strawberry.field
    def all_items(self) -> list[ItemType]:
        return Item.objects.all()

schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
```

That's the whole surface. `class Meta` configures the type, the optimizer extension turns nested selections into one or two SQL queries instead of N+1.
````

This single block sells the package harder than every paragraph already in the docs. It is the first concrete change to make.

### 2. No quickstart path in the user journey

Five hops (root README → `docs/README.md` → `FEATURES.md` → `TREE.md` → `KANBAN.md`) and the user still hasn't seen "install + use." Add to the root [`README.md`](../README.md) a `## Quick start` that links into [`docs/README.md`](README.md)'s code block above, and to [`docs/README.md`](README.md) a "Quick start → Optimizer behavior → Status" path.

Three minutes from landing to a working schema, not three minutes navigating doc-routing.

### 3. "Pre-alpha" is unactionable

[`README.md:16`](../README.md:16) and [`docs/README.md:99`](README.md:99) both say public API changes are expected until `0.1.0`. As a user weighing risk I want: *what specifically is likely to change, and what is stable enough to bet on for an internal tool?*

Concrete replacement text:

> **Status: 0.0.3, single-maintainer.** Stable enough for internal tools and prototypes; not for production. Today's shipped names — `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto` — are intended to remain stable through 0.1.0. Expect the deferred `Meta` keys (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) to move from rejected to accepted as their subsystems ship; the registry will gain `Meta.primary` for multi-type-per-model. None of those changes break code that uses today's surface.

Now the user knows what's load-bearing and what's coming.

### 4. The optimizer is the headline feature and it's underplayed

[`docs/FEATURES.md:142-156`](FEATURES.md:142) lists optimizer cache and planning as flat bullets. None of them communicate the *value*. Compare:

> - AST-keyed plan cache for repeated GraphQL operations
> - cache keys based on selected operation AST, directive variables, target model, and root runtime path

vs. the same content sold to a user:

> - **Plan cache.** The same query 10,000×/sec walks the selection tree once, not 10,000 times. Cache keys ignore filter variables that don't affect selection shape, so a query with 10 filter combinations is still one cached plan, not 1,024.
> - **Multi-operation safety.** `query A {...} query B {...}` in one document never share a plan; named-fragment `@skip`/`@include` directives are tracked into the cache key.

Apply the same rewrite to [`docs/FEATURES.md:158-170`](FEATURES.md:158) ("Join avoidance and projection") and [`docs/FEATURES.md:210-220`](FEATURES.md:210) ("Queryset diffing"):

> - **FK-id elision.** `{ category { id } }` reads `category_id` off the parent row — no JOIN, no second query.
> - **Queryset cooperation.** If your resolver already calls `select_related("category")` or returns `Category.objects.prefetch_related(Prefetch("items", queryset=...))`, the optimizer doesn't reapply or override it. Subtree-aware: `prefetch_related("items", "items__entries")` cooperates with the optimizer's nested `Prefetch("items", ...)` instead of raising Django's "lookup already seen with a different queryset" error.
> - **Strictness mode.** `DjangoOptimizerExtension(strictness="raise")` fails tests on accidental N+1s.

Every one of those is shipped. Read like that, "built-in N+1 optimizer" stops being a generic checkbox and becomes a concrete reason to choose this package over the alternatives.

### 5. "Why this and not X" is buried in 100+ lines of comparison bullets

[`docs/FEATURES.md:244-303`](FEATURES.md:244) has two big "Enhancements over X" sections. They read like internal pitches — long, defensive, list-shaped. Replace with one comparison table at the top of the file:

| Concern | graphene-django | strawberry-graphql-django | this package |
| --- | --- | --- | --- |
| Configuration shape | `class Meta` | decorators | `class Meta` |
| Async resolvers | retrofitted | native | native |
| Modern typing | `graphene.String()` | type hints | type hints |
| Built-in N+1 optimizer | external | shipped | shipped + plan cache + FK-id elision + queryset diffing + strictness |
| Filter / order / aggregate | shipped | shipped | **planned** |
| Stable today | yes | yes | **alpha** |

Honest about what's missing, sharp on what differentiates. The current bullet sections can still exist below the table for readers who want detail, but the table is the headline.

### 6. Doc map is circular and `KANBAN.md` is not a user doc

Every file at the top says "Related docs: README, FEATURES, TREE, KANBAN." The user gets bounced around. Worse, [`KANBAN.md`](../KANBAN.md) is a project-management view (Done / Ready / Next up / Backlog / Blocked, sequencing options, evidence file lists) — not product info. A casual user clicking it from the root README expects a feature board and gets an internal sprint board.

Fix:

- Pick one canonical doc map (root [`README.md`](../README.md) "Project documentation" section is the right place) and keep the others minimal.
- Either drop [`KANBAN.md`](../KANBAN.md) from the user-visible doc map, or label it explicitly: `[KANBAN.md](KANBAN.md) — *contributor/maintainer board for shipped/planned/blocked work.*`
- Remove the duplicated "Related docs" block from the top of [`docs/README.md`](README.md), [`docs/FEATURES.md`](FEATURES.md), and [`docs/TREE.md`](TREE.md). One link back to the root suffices.

### 7. The current/target tree blocks in `docs/README.md` are noise

[`docs/README.md:49-86`](README.md:49) shows the current on-disk tree and the target tree. As a user evaluating the package, I do not care where `connection.py` will eventually live — that's maintainer concern. Cut both blocks from [`docs/README.md`](README.md) and leave them in [`docs/TREE.md`](TREE.md) where they already exist. The friendly landing page should sell the surface, not document the layout.

### 8. `Meta.optimizer_hints` is a sleeper feature that's underplayed

[`docs/FEATURES.md:171-185`](FEATURES.md:171) lists `OptimizerHint.SKIP / .select_related() / .prefetch_related() / .prefetch(Prefetch(...))`. Lead with the use case, not the type names:

> Override the optimizer per relation when you know better than it does — skip a relation entirely, force a join, or hand it your own `Prefetch` for filtered children. Configure it in the same `class Meta` you already declared the type with:
>
> ```python
> from django.db.models import Prefetch
> from django_strawberry_framework import OptimizerHint
>
> class CategoryType(DjangoType):
>     class Meta:
>         model = Category
>         fields = ("id", "name", "items")
>         optimizer_hints = {
>             "items": OptimizerHint.prefetch(
>                 Prefetch("items", queryset=Item.objects.filter(is_published=True)),
>             ),
>         }
> ```

That paragraph sells the hint API in one block. The current bullet list does not.

### 9. `get_queryset` is the right name and it's in the right place — say so

[`docs/FEATURES.md:110-123`](FEATURES.md:110) describes the visibility hook factually. As a Django/DRF user, I already know `get_queryset` from DRF's `GenericAPIView`. Lead with the familiarity:

> If you've used DRF, you already know this hook. `DjangoType.get_queryset(cls, queryset, info, **kwargs)` runs once per type, defaults to identity, and is where permission filters, tenant scoping, soft-delete, and request-user filters live. The optimizer reads `has_custom_get_queryset()` and downgrades a JOIN to a `Prefetch` when a target type defines one — your visibility filter survives the relation traversal.

That last sentence is the load-bearing claim. Surface it.

## Punchier language (specific before/after)

| Where | Current | Suggested |
| --- | --- | --- |
| [`README.md:14`](../README.md:14) | *"DRF-inspired Django integration framework for Strawberry GraphQL — `Meta`-class-driven type generation and N+1 optimization today, with filtering, ordering, aggregation, and permissions on the roadmap."* | *"Meta classes, not decorators. Strawberry GraphQL on Django, with an N+1 optimizer that cooperates with your existing querysets. Filters / orders / aggregates / permissions are on the roadmap."* |
| [`README.md:16`](../README.md:16) | *"Status: pre-alpha. The shipped surface is `DjangoType` plus the N+1 optimizer."* | *"Status: 0.0.3, single-maintainer. Today: `DjangoType` (Meta-driven model→type generation) and an N+1 optimizer with plan cache, FK-id elision, and consumer-queryset diffing. Coming: filters, orders, aggregates, connections, permissions — none of these ship yet. Don't run this in prod."* |
| [`docs/README.md:3`](README.md:3) | *"`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL. It lets Django teams build GraphQL APIs from Django models using the familiar `class Meta` style instead of a decorator-heavy surface."* | (keep, but follow with the Quick start code block from §1 immediately) |
| [`docs/README.md:42-47`](README.md:42) | *"Layer 1: shared infrastructure / Layer 2: model-backed types and query optimization / Layer 3: GraphQL query surfaces planned on top of Layer 2"* | *"Today: types and the optimizer. Coming: filters, orders, aggregates, connection fields, permissions. The package is built on Strawberry directly — there is no dependency on `strawberry-graphql-django`."* |
| [`docs/FEATURES.md:13-17`](FEATURES.md:13) status legend | (factual, fine) | Also add: *"Most users only care about `shipped` and `planned`. The other two are for contributors deciding what to work on next."* |
| Anywhere "Layer 1 / Layer 2 / Layer 3" appears in user docs | Internal vocabulary | Replace with concrete capability names. Maintainer docs (KANBAN, TREE) can keep the layer terms. |
| Anywhere O1-O6 / B1-B8 appears in user docs | Slice shorthand | Drop. Behavior, not slice numbers. Keep slice labels in source comments and KANBAN as release shorthand. |

## Notes on the previous consolidation plan

The behavior-consolidation outline (proposed README shape, "Consolidations" sections, spec-reference removal, CHANGELOG condensation, archive/delete step) was correct and most of it is already in flight in the current diff. Three additions worth folding in:

1. **The plan never says "add a code example."** Add a `Quick start` section to the proposed README outline. It is the single highest-impact change in the consolidation pass. Without it, archiving the specs trades a documented-internal package for an undocumented-external one.
2. **Open question #2 — should O1-O6 / B1-B8 stay in the README as shorthand?** Drop them from user-facing docs. Keep them in [`KANBAN.md`](../KANBAN.md), source comments, and commit messages where they are useful release shorthand. They mean nothing outside this repo and are pure cognitive load for a new user.
3. **Open question #3 — where does future design work go?** [`KANBAN.md`](../KANBAN.md) "Ready / Next up / Backlog" cards already capture future scope at the right granularity. Keep `docs/spec-<topic>.md` as the convention for new in-flight design (the current docs/README.md:94 already says this), but stop accumulating them after a slice ships — fold the shipped behavior into [`docs/FEATURES.md`](FEATURES.md) and delete the spec.

One process note for the archive step itself: before deleting completed design docs, grep for archived design-doc filenames and legacy TODO anchors, then chase every hit. Those anchors should be gone after recent optimizer work shipped, but the grep is cheap insurance and the alternative is dangling references in source after archive.

## Pre-commit notes on the current diff

The actual diff is fine. Two small things worth touching before commit:

1. The root README's new "Project documentation" section ([`README.md:24-31`](../README.md:24)) lists [`KANBAN.md`](../KANBAN.md) without framing — a casual user clicking it expects a polished feature board and gets a sprint board. Either add `*— contributor/maintainer board*` after the link, or drop the bullet entirely and reference KANBAN only from CONTRIBUTING.
2. Every doc has its own "Related docs:" header block at the top ([`docs/README.md:11-14`](README.md:11), [`docs/FEATURES.md:7-11`](FEATURES.md:7), [`docs/TREE.md:5-9`](TREE.md:5)). Pick one canonical place (root README) and let the others stay short — currently each file repeats a near-identical link list, which is heavy and brittle (every rename touches four files).

## Concrete additions to make

In priority order, before the next docs commit:

1. **Quick start with code in [`docs/README.md`](README.md).** Section §1 above. ~15 lines.
2. **Concrete value-led optimizer rewrite in [`docs/FEATURES.md`](FEATURES.md).** Sections §4 above. Replace flat-bullet behavior with use-case framing for the cache, FK-id elision, queryset cooperation, and strictness mode.
3. **Comparison table in [`docs/FEATURES.md`](FEATURES.md).** Section §5 above. Demote the long "Enhancements over X" sections below the table.
4. **Sharper status block in root [`README.md`](../README.md) and [`docs/README.md`](README.md).** Section §3 above. Tell the user what's load-bearing and what's coming.
5. **Cut current/target tree from [`docs/README.md`](README.md).** Section §7 above. Move (or delete; they already exist) into [`docs/TREE.md`](TREE.md).
6. **`Meta.optimizer_hints` use-case rewrite.** Section §8 above. One concrete code block beats five bullets.
7. **Frame `get_queryset` for DRF users.** Section §9 above. Two sentences.
8. **De-circular the doc map.** Section §6 above. Remove repeated "Related docs" blocks from the three sub-docs; demote KANBAN.

The first three changes (quickstart, optimizer rewrite, comparison table) close most of the gap on their own. The rest is polish.

## Net

The 0.0.4 archive consolidation cleans up a real mess and the diff is going in the right direction. The remaining miss is that the docs still describe the package rather than onboard the user. One code block, one comparison table, and a sharper status line fix the bulk of that. None of the changes above require touching source code — pure docs work.
