# Bug-hunt dicta — django_strawberry_framework

Distilled from `docs/review/worker-{0,1,2,3}.md`. These are the recurring
pitfalls, severity calibrations, and review-order priorities to keep in
mind as you walk each per-file prompt below.

## Review order (logic first, comments second)

1. **Logic pass.** Correctness, public API behavior, Django ORM
   correctness, optimizer behavior / N+1, cache and request-scope
   state, async/sync hazards, perf / memory, DRY, module responsibility,
   import-time side effects, typing, and the tests needed to prove a
   recommended change. Do not recommend comment polish before the
   logic is right.
2. **Comment / docstring pass.** Only after logic is approved. Catch
   stale comments, comments that restate obvious code, missing
   explanations for non-obvious Django / optimizer / public-API
   constraints, obsolete TODOs and deleted-spec references, and
   docstrings that promise behavior the implementation does not
   provide.

## Pitfalls that recur in this package

### Django / ORM and the optimizer
- N+1 risk and unnecessary relation loading; `select_related` vs
  `prefetch_related` correctness.
- Field-map keying (`name` vs `attname`) and primary-key shape
  (default `id`, custom scalar pk, relation pk such as
  `OneToOneField(primary_key=True)` where `name != attname`).
- Cache / request-scope state mutation that crosses requests.
- Reflective access (`getattr`, `hasattr`, `isinstance`) on Django
  descriptors — defaults must match the upstream contract.
  `ForeignObjectRel.null = True` (proxying the forward FK) is the
  canonical surprise; reverse-FK / M2M descriptors inherit it.
- `_meta.pk.name` vs `_meta.pk.attname` are different concepts; mixing
  them silently lazy-loads the related row when the pk is a relation.

### Validation and config
- "Validates A but does not validate the intersection of A and B"
  patterns. A guard that almost catches a misconfiguration but lets a
  real edge case slip through is **Medium, not Low** — silent dead code
  is the bug, not a polish item.
- `ConfigurationError` messages must cite the model name. Consumers
  grep stack traces by model; listing only unknown keys / field names
  pushes a Low into Medium.
- Falsy / empty values silently coerced to defaults: prefer loud
  rejection over silent passthrough for consumer-supplied input.
  (Defensive `or {}` is appropriate on reflective shape reads off
  upstream Strawberry / graphql-core / Django descriptors where the
  attribute is legitimately absent; do not unify the two stances.)

### Public API and shape contracts
- Backward compatibility on shipped names (`DjangoType`,
  `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`,
  `auto`, `__version__`).
- Re-exports in package `__init__.py` are part of the public surface.
- Annotation suppression / synthesis (the Relay-Node `id` case) is
  load-bearing for schema construction; drift between collection-time
  checks (`__init_subclass__` / `_build_annotations`) and
  finalization-time checks (`finalize_django_types`) is a High-tier
  hazard. The collection-time check sees pre-`apply_interfaces`
  bases; the finalization-time check sees the resolved MRO.

### Async / sync hazards
- A consumer's `get_queryset` may be sync or async; resolver paths
  must handle both without hanging the event loop.
- Strawberry's async-resolution path differs from a bare
  `asyncio.run` wrapper — assertions that "the async branch fires"
  need to exercise the same event-loop shape Strawberry uses in
  production.

### Tests and validation
- High-severity fixes require a test pinning the corrected behavior.
  A High-severity fix without a test must be rejected unless the
  artifact explicitly justifies why a test is impossible or
  inappropriate.
- Test placement per `AGENTS.md`: three trees (`tests/`,
  `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`),
  `tests/base/` is frozen, no new files added there.
- Speculative defects do not ship. Only confirmed issues with cited
  source lines. Cross-file concerns go to a folder or project pass.

### DRY / structural
- Repeated literals across sibling modules drive the folder-pass DRY
  check. The static helper's "Repeated string literals" section is
  the audit list.
- Near-copies of existing helpers should be consolidated; a new
  helper must justify its single responsibility.
- Two Scoops of Django: small focused modules, explicit queryset
  boundaries, minimal magic, reusable utilities only when genuinely
  shared.

## Severity calibration

- **High**: confirmed correctness bug; spec-contract violation; API
  breakage on shipped `0.0.x` surface; DRY violation that entrenches
  duplicated logic across the package; Django ORM behavior that can
  return wrong data; security / data-isolation regression; crash of a
  normal consumer path.
- **Medium**: likely performance regression; N+1 risk or unnecessary
  database work; redundant implementation that should be consolidated;
  unclear ownership between modules; brittle edge-case behavior;
  missing tests for important branches; repeated literal / key /
  tuple that should be a named constant; "validates A but not A∩B"
  silent-dead-code guard.
- **Low**: small maintainability issue; naming clarity; minor typing
  or API polish; localized simplification; comment / docstring stale
  but not load-bearing.

## Static helper usage

- Run `scripts/review_inspect.py --output-dir docs/bug_hunt/shadow`
  before reviewing any `.py` file ≥150 lines, any file under
  `optimizer/` or `types/`, or at any folder-level pass (which needs
  an overview for every sibling, including the folder's `__init__.py`).
- Skip the helper for pure-class-definition modules like
  `exceptions.py`; state the skip and the reason in the artifact's
  "What looks solid" section.
- The overview's **Django / ORM markers** section is the audit list
  for ORM-heavy files. **Control-flow hotspots** flag branchy
  functions for Medium-tier complexity attention. **Calls of
  interest** surfaces reflective-access sites (typical sites of
  shape-contract bugs). **Repeated string literals** drives the
  folder-pass DRY check.
- The shadow file strips comments and may strip docstrings — its
  line numbers do not match the original source. Always cite
  **original source-file line numbers** in the artifact.
