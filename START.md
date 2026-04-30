# START.md

Hey, future me. You're walking into `django-strawberry-framework`. Read this once, then read `AGENTS.md`. Then go.

This file is advice from past me to future me about how to keep Rio happy and how to actually move the package forward. Treat it as living context, not law — but don't ignore it.

## What this repo is

DRF-shaped Django integration for Strawberry GraphQL. The differentiator vs `strawberry-graphql-django` is the API surface: we configure types via nested `Meta` classes, never via stacked decorators on consumer-facing classes. The differentiator vs `graphene-django` is everything else: async-native, modern Python typing, active upstream. Pre-alpha, single maintainer, rapid iteration. See `docs/README.md` for the full positioning argument and `AGENTS.md` for the day-to-day conventions.

## How Rio communicates

Rio is direct and decisive. They iterate fast, they reverse course without ceremony, and they expect the same from you. Specifically:

- Short messages, often imperative. "Now do X." "Scratch that, do Y instead." Don't read tone where there isn't any. Just do the thing.
- They will reverse a decision they made one or two turns ago. This already happened in this conversation around test placement — they had me put example tests inside the example app to mirror `django-graphene-filters`, then immediately had me move them all back. Both decisions were correct in their moment. Roll with the reversal; don't argue old reasoning back at them.
- They appreciate honest pushback when their question contains a hidden flaw, but only once. Surface the flaw, suggest the better path, then defer if they push past it. Don't lecture.
- They dislike preamble, sycophancy, over-explanation. They have 12 years of experience in Django and Vue.js

## Workflow rules they've set

These are the rules I most often forgot in past sessions and they had to remind me. Encode them now.

- **Do not run `pytest` after every change.** Run formatting only. They will explicitly say "run tests" or "run the full pipeline" when they want it. Coverage gating means tests will fail loud the moment they run.
- They commit themselves most of the time. Don't auto-commit unless they explicitly ask. When they do ask, include the `Co-Authored-By: Oz <oz-agent@warp.dev>` line.
- When you make changes, run `uv run ruff format .` (and `ruff check --fix .` if there were edits) and stop there. No `pytest`. No `manage.py check`. No `uv build`.

## Style they care about

- **Trailing commas on multi-arg calls.** This is enforced by ruff's `COM812` and they care a lot. Adding a trailing comma after the last arg of a multi-arg call expands it across lines and locks the layout in. Don't remove these to "tidy up". Personal preference, encoded in lint.
- **Line length 110.**
- **Meta classes everywhere on consumer surfaces.** If you find yourself writing stacked Strawberry decorators on a consumer-facing class, stop. That is the strawberry-graphql-django API and the explicit reason this package exists. Strawberry is the engine; DRF is the shape. This is point #1 in `AGENTS.md` for a reason!
- They prefer keeping all model text fields as `TextField`, not `CharField`, even for short strings. Personal preference; codified in the example models.

## AGENTS.md

If updating this file Keep this document as dense as possible, don't even use blank lines or periods. No code blocks.

## Tests they care deeply about

Re-read the relevant `AGENTS.md` section before touching tests. Three rules they care about most:

- **`tests/base/` is frozen** at `test_init.py` and `test_conf.py`. Do not add files there, `test_conf.py` may grow, but no new ones.
- **First line of every test: seed via `services`.** `services.seed_data(1)` for catalog state, `services.create_users(1)` for auth state. Never hand-roll `Category`/`Item`/`Property`/`Entry`/`User`. The only exceptions are the tests *of* the seed helpers themselves.

The package has 100% coverage and CI gates it. The example app does NOT count toward coverage — that's intentional. Don't widen the coverage source back to include `examples/`.

## Past mistakes to not repeat

These are real mistakes I made this conversation. Don't repeat them.

- **Don't preemptively populate `conf.py` with future-feature settings.** I did that on the first pass and Rio aggressively trimmed it. The rule: add a settings key only when the feature that needs it lands.
- **Don't restore deleted files because you assume they belong.** When a file disappears, ask first. I once restored a `schema.py` and `test_schema_smoke.py` that Rio had intentionally removed.
- **Don't add coverage of the example app to the gate.** I expanded the coverage source once and Rio rolled it back. The package gets 100%; the example exists to exercise the package via real flows, not to gate the build.
- **Don't run `pytest` "to be sure".** The standing rule is formatting only. Run tests when explicitly asked.
- **Don't second-guess `field_name` patterns** in the aspirational `filters.py`/`orders.py`/`aggregates.py`. I spent too long trying to deduce the original author's intent in `django-graphene-filters`. The aspirational files are mechanical translations from the old project. When in doubt, mirror the old shape.

## Strategic advice

- The package is rebuilding the overlap between `graphene-django` and `strawberry-graphql-django`, DRF-shaped. When in doubt about whether a feature belongs, ask: do both libraries provide it? If yes, it's foundational and we need it. If only one does, it's optional and probably belongs in a later spec.
- Behaviorally we copy `strawberry-graphql-django`'s good ideas (especially the optimizer's downgrade-to-`Prefetch` rule when the target type has a custom `get_queryset`). Surface-wise we copy `django-graphene-filters` (Meta-class API). Be honest about which side of that line a decision falls on.
- Build in slices. Each slice ships with tests in the same change. The DjangoType spec broke itself into seven slices (1–4 and 7 shipped; 5–6 forked into `docs/spec-optimizer.md` as slices O1–O6 when per-resolver optimization proved architecturally wrong). Future specs should follow the same shape, and don't be afraid to fork a sub-system into its own spec mid-stream when a slice grows past ~one module.
- TODO anchors. When a spec slice is staged but not yet implemented, drop a `TODO(spec-<doc>.md <slice-id>)` comment at the exact source site the slice will land in, and pair it with `NotImplementedError` if the call path needs to fail loudly. The optimizer rebuild already uses this — `types/base.py`, `optimizer/extension.py`, `optimizer/walker.py`, and `optimizer/plans.py` carry anchors for every `spec-optimizer.md` O-slice. Update or remove the anchor in the same change that ships the slice.
- Resist scope creep. The DjangoType spec deliberately defers filters, orders, aggregates, permissions, and the full connection field. That's correct. Don't quietly mix in "while I'm here" extras that bloat the slice and complicate review.
- Coverage is a feature, not a chore. If a line can't be covered by exercising the example, that's a smell — it usually means the code is too clever or the wrong abstraction.