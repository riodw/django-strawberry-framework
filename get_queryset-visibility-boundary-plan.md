# `get_queryset` visibility boundary — historical review note

This file was the **first-round** adversarial code review of the `get_queryset`
visibility boundary, written against the pre-`80527a36` implementation. It
reported the boundary as not ready and listed several security-relevant defects
(async connection residual-awaitable bypass, cross-model combined-query
acceptance, and hook-selected alias drift on evaluated results).

Those findings were fixed and committed at `80527a36`. A subsequent
second-round adversarial review (`docs/feedback.md`) then drove the
**sealed execution queryset** rearchitecture that supersedes the
method-inventory approach described here: the hook/source object is treated as
untrusted query state, its validated SQL state is rebuilt into a framework-owned
plain `django.db.models.QuerySet`, and the consumer object's executable behavior
is never dispatched.

Status: the third-round adversarial review (`docs/feedback.md`, 2026-07-18) is
RESOLVED. Its four P1 findings (instance-level `Query.chain` / method shadows
riding through `sql.Query.clone`'s `__dict__` copy, the identity-hook fast path
bypassing result sealing, executable AST nodes nested inside an exact `sql.Query`
dispatching mid-seal, and `Prefetch` executable-wrapper survival + cross-alias
child hydration) and the P2 model-less-query escape were each already closed by
the sealed rearchitecture recorded in `docs/README.md`; the closing change proved
that by making the boundary's own regressions pass, fixing the two contradictory
tests the review flagged, threading `allow_sliced` for the optimizer walker's
degrade-to-unplanned path, and driving `utils/querysets.py` to 100% coverage. See
the `## Resolution` section at the end of `docs/feedback.md`.

This note is retained only for history. It does not describe current behavior
and should not be treated as an implementation plan.

Current sources of truth:

- `docs/feedback.md` — the second-round review that drove the rearchitecture.
- `docs/README.md` — the standing sealed-execution-queryset contract (see the
  `get_queryset` visibility-hook bullet).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
