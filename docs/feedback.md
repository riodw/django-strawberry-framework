# Docs review feedback — post-consolidation pass

Reviewed commit `5e934c1`. The bulk of the previous feedback landed: quickstart code in [`docs/README.md`](README.md), comparison table at the top of [`docs/FEATURES.md`](FEATURES.md), value-led optimizer/hints/cooperation rewrites, sharper status block, repeated "Related docs" headers gone, slice labels and Layer 1/2/3 jargon mostly stripped from user docs. Big improvement — a user can now land, see code, and understand the surface in under three minutes.

A handful of small things are worth a follow-up pass.

## Smaller items worth tightening

1. **`Three-minute path` duplicates the quickstart.** [`docs/README.md:38-44`](README.md:38) lists "1. Define `DjangoType` classes / 2. Return a Django `QuerySet` / …" — that's just narrating the code block right above it. Either delete the section, or repurpose it as *"What just happened?"* with one-line pointers (e.g. *"`class Meta` registers the type. The extension walks selections, builds an ORM plan, and applies it once at the root."*). The current shape is filler.

2. **Root README's `Quick start` redirects without value.** [`README.md:32-34`](../README.md:32) is one sentence pointing back to [`docs/README.md`](docs/README.md). Either inline the same code snippet (the user is already on the README — give them the payoff), or drop the section and let the doc-map bullet handle it.

3. **`Optimizer behavior` in [`docs/README.md`](README.md) regresses to flat bullets.** [`docs/README.md:84-92`](README.md:84) reverts to bullet-list shape after [`FEATURES.md`](FEATURES.md) committed to the **bold-led / value-first** style. Mirror it: *"**Forward relations** use `select_related`. **Many-side** uses `prefetch_related`. **`{ category { id } }`** reads `category_id` off the parent — no JOIN."* Eight punchy lines instead of eight bullet points. Keep it consistent across the two main user-facing docs.

4. **`Enhancements over X` sections in [`FEATURES.md`](FEATURES.md) now duplicate the comparison table.** [`FEATURES.md:259-318`](FEATURES.md:259) has two big "Enhancements over strawberry-graphql-django / graphene-django" blocks that predate the new comparison table at [`FEATURES.md:18-27`](FEATURES.md:18). With the table doing the headline comparison, demote these two sections to one short paragraph each — *"For teams migrating from strawberry-graphql-django: …"* — or drop them entirely and let the planned migration guides ([`KANBAN.md` BACKLOG-009](../KANBAN.md)) carry that load.

5. **Status text has a small internal tension.** [`README.md:16`](../README.md:16) and [`docs/README.md:96`](README.md:96) both say *"stable enough for internal tools and prototypes; not for production"* and then *"shipped names are intended to remain stable through 0.1.0."* Those are different stability promises (not-for-prod vs. names-stable). Worth one clarifying sentence: *"API names stable through 0.1.0; correctness and edge-case behavior are still hardening, hence the not-for-production disclaimer."*

6. **`Why this package exists` is still four generic bullets.** [`docs/README.md:48-52`](README.md:48). Fold into one sharper paragraph: *"Django teams already think in `Meta.model`, `fields`, `exclude`, querysets, and DRF idioms. Strawberry is the modern Python GraphQL engine but its Django ecosystem leans on decorators. This package keeps Strawberry as the engine and the configuration shape consumers already know."* Then drop the bullets

7. **`Today and coming next` lists nine "today" items but no link to the comparison table.** [`docs/README.md:57-74`](README.md:57). A user weighing adoption wants the comparison right there. Add a one-line: *"How this stacks up against the alternatives: see the [comparison table in FEATURES.md](FEATURES.md#quick-comparison)."*

## Net

The diff lands 80% of the previous feedback well. Remaining work is consistency (`docs/README.md` optimizer section should match `FEATURES.md` punchy style), de-duplication (`Three-minute path` and `Enhancements over X` are now redundant), and one stability-claim clarification. Maybe 30 minutes of polish