# Pre-BETA review: extensions/

Scope: `debug.py` -- the `DjangoDebugExtension` (graphene-debug-style capture of
Django query-log SQL + execution exceptions into `extensions["debug"]`).

Method: this module just completed a full spec-conformance + logic review
(recorded in `docs/feedback.md` against spec-044); this file is a fresh
pre-BETA pass, not a re-derivation. Read-only; no tests run. Per the prior
review's discipline, nothing is re-flagged here unless a concrete failing input
was identified that the earlier pass plausibly missed -- and none was.

Bottom line: no correctness defect. The extension is off by default (opt-in by
passing the class in `extensions=[...]`), uses a reference-counted
cursor-capture coordinator keyed by connection object identity, and degrades
diagnostics-gathering failures without ever replacing the result. Ship it as-is
for BETA; the outstanding items are the spec's own later slices, not code.

## P0 -- correctness suspicions

None found (consistent with the spec-044 review).

## P1 -- fix before BETA

None in this module. The one live P0 from the spec-044 review is *outside* this
folder: the CI Strawberry-floor step in `.github/workflows/django.yml` calls
`strawberry.__version__`, which does not exist at the 0.316.0 floor. That is
tracked in `docs/feedback.md`; noted here only so it is not lost.

## P2 -- polish / hardening

### `debug.py` -- multi-DB capture breadth is a documentation point
Confidence: low. Capture acquires a bracket per connection seen during the
operation and restores saved values on release. Confirm the docs state which
connections are covered when an operation spans multiple databases (each
distinct `BaseDatabaseWrapper` gets its own bracket), so consumers reading the
`sql` payload know it aggregates across aliases.

## API & consistency notes

- The payload wire names mirror graphene-django (`vendor`/`alias`/`sql`/
  `duration`/`isSlow`/`isSelect`, `excType`/`message`/`stack`). Keeping the
  graphene vocabulary is the right call for drop-in familiarity; freeze it for
  BETA.
- Opt-in is by passing the class (not an instance) in `extensions=[...]`; the
  0.316 engine instantiates per operation with zero args. Document this so
  consumers do not pass a pre-constructed instance and get surprised by the
  per-operation lifecycle.

## Verified sound (do not re-flag)

- Two-phase failure policy: pre-yield acquisition failures fail loud and unwind
  acquired brackets via the `ExitStack`; post-execution diagnostics failures are
  caught as `Exception` (never `BaseException`), logged, and degrade the payload
  without replacing the operation result.
- The cursor-capture coordinator is lock-protected, keyed by concrete connection
  object identity (never the alias string), and restores saved values on release
  -- reference-counted so nested/overlapping operations do not clobber each other.
- `get_results` is pure and idempotent, returning `{}` or `{"debug": payload}`.
- Cycle-safe original-error walking (identity set + local hop ceiling).

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
