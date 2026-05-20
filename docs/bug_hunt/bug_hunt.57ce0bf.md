# Bug-hunt dicta — `django_strawberry_framework`

You are the hunter. Your job is to **find** things, not to write polished code. Be exploratory. Touch things. Make scratch files if it helps; pollute the working tree if it surfaces a bug. Cleanup is downstream.

The questions below are **probing prompts**, not checklist items — each is a thread to pull on, not a box to tick. When a question doesn't apply to a file, move on; don't force findings.

Severity is a **priority signal** for how loudly to surface a find, not a gate. Anything you find gets recorded; the priority just tells the maintainer how fast to act.

## Package context

`django_strawberry_framework` is a Django integration for Strawberry GraphQL, shaped DRF-style. Pre-alpha, one maintainer. Package surface:

- **`optimizer/`** — query optimizer that walks GraphQL selections to build prefetch / select_related plans. Files: `walker.py`, `extension.py`, `field_meta.py`, `plans.py`, `hints.py`, `_context.py`.
- **`types/`** — DjangoType machinery: Meta-class processing, relay nodes, finalizer pipeline, converters. Files: `base.py`, `relay.py`, `finalizer.py`, `relations.py`, `converters.py`, `resolvers.py`, `definition.py`.
- **`registry.py`** — model → DjangoType registry with rollback semantics.
- **`scalars.py`** — custom GraphQL scalars (BigInt landed; Upload deferred).
- **`utils/`** — pure leaf modules (`relations.py`, `strings.py`, `typing.py`).
- **`conf.py`** — settings shim; intentionally minimal (per START.md, do NOT preemptively populate it with future-feature settings).

The package deliberately defers filters, orders, aggregates, permissions, and the full connection field. The Meta-class consumer API is the explicit reason this package exists — stacked Strawberry decorators on consumer surfaces are the wrong shape and should be flagged.

## Probing questions by category

### Silent dead branches & guards

- Does this guard cover every input class it appears to cover, or does some realistic input slip past silently?
- Where the code validates A, does it also validate the intersection of A and B that downstream code assumes? (Pattern: validates "is a real Django field" but downstream assumes "is a real Django field AND is selected".)
- Is there a branch whose precondition can never be true in production but a test exercises it anyway? Conversely: a branch whose precondition the author believed unreachable but a realistic call site reaches?
- For every `raise`: is there a code path that should raise this but currently returns silently? A code path that raises this but should return a structured error?
- Where a default value is "obviously unreachable" — try to reach it. Defaults marked dead are often load-bearing under one input shape.

### Public-API surface shape

- Does this change something a consumer sees — error type, error message wording (beyond additive substring), public symbol presence, return shape, GraphQL schema output?
- If this raises, can a consumer grep the error message back to the specific model / field / site that caused it? Error messages without a model name make stack traces hard to triage.
- Is the Meta-class consumer API preserved? Stacked Strawberry decorators on consumer surfaces are explicitly the wrong shape for this package.
- Public exports: does each module's `__init__.py` export match what's actually exported, with no dead names and no quietly-renamed symbols?

### Refactor leftovers

- Did a refactor change a signature or return shape but leave the docstring describing the old contract?
- Did a refactor remove a helper but leave imports, comments, or test mocks referencing it?
- Did a refactor rename a Meta key but leave the old key in error messages, docstrings, or example apps?
- TODO / phase / slice labels: does the label point at an active KANBAN slice, or is it orphaned (grep `KANBAN.md` for the slice keyword — if no match, the label is stale)?

### Django / ORM specificity

- For every `cls.__django_strawberry_definition__.model` and adjacent attribute access: is the attribute guaranteed present at this call site (the class was registered through `__init_subclass__`), or can a not-yet-registered class reach here?
- Reflective attribute access (`getattr`, `setattr`, `hasattr`) with a string literal that mirrors a Meta key: is the string spelled the same everywhere? Misspellings fail silently — `getattr` returns the default and the bug is invisible until production.
- `_default_manager` vs `objects`: is the right manager used at every queryset entry point? Consumers can override `_default_manager`; using `objects` silently bypasses their override.
- For every `model._meta.<X>` read: does the code handle the proxy-model, abstract-model, and composite-pk cases Django can throw at it?
- Pre/post-save signal hooks, `__init_subclass__` ordering, `apps.get_model`: any of these are likely sources of "works in tests, breaks in user code" bugs.
- Manager / queryset usage: any `.all()` that should be `.get_queryset()`? Any place a user's overridden manager is silently bypassed?

### Optimizer correctness

- Does the optimizer downgrade to `Prefetch` when the target type has a custom `get_queryset`? (The strawberry-graphql-django behavior this package explicitly copies.)
- Walker traversal: when a relation has a custom queryset hook, is the prefetch path correctly diverted? When it doesn't, is `select_related` used?
- Field-meta classification (`many`, `reverse_many_to_one`, `forward_one_to_one`, etc.): does the classifier handle every Django relation shape, including the unusual ones (`GenericRelation`, `OneToOneRel`, self-referential FKs)?
- Origin resolution: does `extension.py`'s `get_type_by_name` resolve every Strawberry type it can encounter, or are there fragment / interface / union shapes that fall through?
- Plan-context lifetime: does the optimizer's per-request context get torn down cleanly when the request errors mid-walk?
- Fragment / inline-fragment traversal: are both visited the same way, or is one path quietly broken?

### Type system / finalizer / relations

- `__init_subclass__`: are all Meta keys validated against the actual model fields at registration time, or is some validation deferred to first use (where it surfaces as a confusing runtime error)?
- Pending-relation resolution: when a forward reference resolves to a class that no longer exists (e.g., circular import collapsed), does the error name the unresolved symbol?
- Relay node composite-pk handling: does the node-id encoder / decoder round-trip every realistic primary-key shape, including `UUIDField`, `TextField` PKs, composite PKs?
- Interface dispatch (`install_is_type_of`): when two types share a model, does the dispatch pick the right one? When a type's model is a proxy of another type's model, what happens?
- Registry rollback: if a registration fails partway through, is every side effect undone, or does the registry leak partial state for the next registration attempt?

### DRY at the boundary

- Two helpers with near-identical bodies: are they intentionally siblings (each tail diverges meaningfully) or accidentally duplicated?
- A repeated string literal across N≥3 sites: is the literal a dispatch key (must be named once) or consumer-readable prose (each site OK as-is)?
- An "extract me" helper at N=2: would extraction force an awkward signature or hide divergence? At N=2, prefer not — but flag if the divergence is shrinking.

### Tests

- Are tests in the right tree per `AGENTS.md` test-placement rules? `tests/base/` is frozen; new tests must not land there.
- For every High-priority bug suspected: is there a test that pins the corrected behavior, or does the bug live in untested territory?
- Coverage-gate vs test failure: a non-zero pytest exit driven by `--cov-fail-under` is NOT a test failure for this gate. Parse the `=== N passed, M skipped ===` summary line, not the exit code.
- Are tests using `services.seed_data` first (per `START.md`), or rolling fixtures inline?
- Are there assertions that look like they pin behavior but actually only pin the test's own setup?

### Folder/project-scope patterns

- Cross-folder duplicate helpers: does `optimizer/` reach for a shape `types/` already owns, or vice versa?
- Naming drift: is the same concept spelled differently in different folders (e.g., `relation_kind` vs `relation_type` vs `rel_kind`)?
- Misplaced responsibility: does a file in `utils/` do Django-specific work that belongs in `types/`? Does a file in `types/` reach into `optimizer/` internals?
- Circular-import risk: is anything in `optimizer/` importing from `types/` at module top-level rather than inside a function?

## Severity calibration (priorities, not gates)

- **Highest priority to surface.** Confirmed bug that changes observable behavior at a public API surface; silent dead code reachable in production; invariant violated by a realistic input class; security-shape issue (raw input flowing into eval / raw SQL / unsafe serialization); a `raise` that can't be triaged because the message names no model / field / site.
- **Medium priority.** Branchy control flow that misses a realistic input class; refactor leftovers (stale docstrings, dead imports, orphaned TODO / phase labels); error messages without model / field names; tests in the wrong tree; a comment that contradicts the code it labels.
- **Low priority.** Stylistic drift; repeated literals that could be named once; near-duplicate helpers at N=2 not yet worth extracting; comment polish.

Surface everything; let the maintainer triage. The priority just tells them how loud to be in the findings note.

## Review order & file-shape rules

- **Logic first, comments second.** A docstring describing wrong behavior is a noise finding; fix the wrong behavior first.
- **Run the static helper** (`scripts/review_inspect.py`) on files ≥150 lines, all of `optimizer/`, all of `types/`. The overview at `docs/shadow/<stem>.overview.md` enumerates Django/ORM markers, control-flow hotspots, calls-of-interest, and repeated literals — use it as a probing checklist.
- **Skip pure-class-definition modules** like `exceptions.py` — state the skip in the findings note ("nothing executable to probe") and move on.
- **Cite original source line numbers**, never shadow file line numbers. The shadow strips comments and replaces string literals; line counts shift.

## What "no issues" looks like

If a file genuinely has no bugs, the hunt note still gets written. State the skip reason in one sentence ("Pure class definitions; nothing executable to probe" or "Reviewed every branch listed above against current source; no concerns surfaced") and move on. An empty hunt note is clearer than silence in the directory listing.

## How to review a single file
Each prompt below targets exactly one source file. Treat it as a focused
review pass, not a tour:

- Read the `.overview.md` shadow first. It is a structural index —
  quick-scan counts, imports, symbols, control-flow hotspots, executable
  Django/ORM marker lines, calls of interest, and repeated executable
  string literals — pulled from the AST without executing the file. Use
  it to plan the read, not as the source of truth.
- Read the `.stripped.py` shadow next. Comments and docstring statements
  are removed, and other string literals are replaced, so the executable
  structure is easier to scan. **Line numbers in the stripped file are
  not canonical.** Cite original source-file line numbers in every
  finding and every fix.
- Open the original source file alongside (named in the prompt) and
  reconcile the shadow view against the real code before declaring a
  defect.
- Confirm every defect against the actual source. No speculation, no
  "this might be wrong". If you cannot reproduce the failure shape
  mentally or with a quick read, drop the finding and move on. Silence
  on a marker line is acceptable; speculative defects pollute the
  checklist.

For each confirmed defect:

- Classify severity using the criteria in the dicta header above.
- Edit the original source file directly. Stay within the file the
  prompt names — if the fix needs sibling changes, surface that as a
  question rather than expanding the diff unilaterally.
- For **High**-severity fixes, add or update a test that pins the
  corrected behavior under the correct test tree per AGENTS.md
  "Test placement is mandatory". Do not rely on validation alone.
- For **Medium** / **Low** fixes that change a documented contract,
  update the relevant docstring or comment in the same pass so the
  prose matches the final behavior.
- Run `uv run ruff format <file>` and `uv run ruff check <file>` on
  any source file you touched.

When the file is done, tick its checkbox `- [x]` so the next prompt is
obvious.

## Per-file prompts

- [x] django_strawberry_framework/conf.py
    - docs/shadow/django_strawberry_framework__conf.stripped.py
    - docs/shadow/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__conf.stripped.py and docs/shadow/django_strawberry_framework__conf.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/conf.py
    - Result: Reviewed every branch listed against current source; no concerns surfaced.

- [x] django_strawberry_framework/exceptions.py
    - docs/shadow/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__exceptions.stripped.py and docs/shadow/django_strawberry_framework__exceptions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/exceptions.py
    - Result: Pure class definitions; nothing executable to probe.

- [x] django_strawberry_framework/optimizer/_context.py
    - docs/shadow/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/django_strawberry_framework__optimizer___context.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/_context.py
    - Result: Reviewed every branch and exception handler against the current source; the context dispatch logic accurately handles dicts, objects, frozen instances, and QueryDicts symmetrically, and no concerns surfaced.

- [x] django_strawberry_framework/optimizer/extension.py
    - docs/shadow/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/django_strawberry_framework__optimizer__extension.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/extension.py
    - Result: Reviewed every branch, cache lifecycle, and schema-audit path against the current source; no concerns surfaced.

- [x] django_strawberry_framework/optimizer/field_meta.py
    - docs/shadow/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/django_strawberry_framework__optimizer__field_meta.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/field_meta.py
    - Result: Reviewed the current source and shadow files; no active bugs or concerns surfaced.

- [x] django_strawberry_framework/optimizer/hints.py
    - docs/shadow/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/django_strawberry_framework__optimizer__hints.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/hints.py
    - Result: Reviewed every branch listed against current source; no concerns surfaced.

- [x] django_strawberry_framework/optimizer/plans.py
    - docs/shadow/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/django_strawberry_framework__optimizer__plans.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/plans.py
    - Result: Reviewed every branch listed against current source; no concerns surfaced.

- [x] django_strawberry_framework/optimizer/walker.py
    - docs/shadow/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/django_strawberry_framework__optimizer__walker.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/walker.py
    - Result: High-priority triage defect fixed in `django_strawberry_framework/optimizer/walker.py`: `ConfigurationError` messages for invalid `OptimizerHint` usage now include the Django type name as well as the field name (original source lines 441-447, 491-506). Validation: `uv run ruff format django_strawberry_framework/optimizer/walker.py` and `uv run ruff check --fix django_strawberry_framework/optimizer/walker.py` passed after line-length cleanup.

- [x] django_strawberry_framework/registry.py
    - docs/shadow/django_strawberry_framework__registry.stripped.py
    - docs/shadow/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__registry.stripped.py and docs/shadow/django_strawberry_framework__registry.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/registry.py
    - Result: Highest-priority triage defect fixed in `django_strawberry_framework/registry.py`: duplicate-primary `ConfigurationError` messages now include the model name and clearer type context (original source lines 134-136). Validation: `uv run ruff format django_strawberry_framework/registry.py` and `uv run ruff check --fix django_strawberry_framework/registry.py` passed.

- [x] django_strawberry_framework/scalars.py
    - docs/shadow/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__scalars.stripped.py and docs/shadow/django_strawberry_framework__scalars.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/scalars.py
    - Result: Reviewed every branch listed against current source; no concerns surfaced.

- [x] django_strawberry_framework/types/base.py
    - docs/shadow/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__base.stripped.py and docs/shadow/django_strawberry_framework__types__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/base.py
    - Result: Fixed two high-severity validation bugs and one medium-severity triage issue in `django_strawberry_framework/types/base.py`: inherited `Meta.fields`/`Meta.exclude` are now treated as mutually exclusive, optimizer-hint validation receives the target model explicitly instead of deriving it from the first selected field, and shadowing errors cite the `DjangoType` subclass where the invalid assignment occurred. Validation: scratch inheritance repro raised the expected `ConfigurationError`; `uv run ruff format` and `uv run ruff check` passed.

- [x] django_strawberry_framework/types/converters.py
    - docs/shadow/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__converters.stripped.py and docs/shadow/django_strawberry_framework__types__converters.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/converters.py
    - Result: Highest-priority schema-generation bug fixed in `django_strawberry_framework/types/converters.py`: `DurationField` and `BinaryField` were removed from `SCALAR_MAP` because Strawberry has no built-in scalar for `datetime.timedelta` or `bytes`, so these fields now raise `ConfigurationError` and require a custom scalar or exclusion. Validation reported: `tests/types/test_converters.py` passed, quick schema repro confirmed the crash shape, and ruff format/check passed.

- [x] django_strawberry_framework/types/definition.py
    - docs/shadow/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__definition.stripped.py and docs/shadow/django_strawberry_framework__types__definition.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/definition.py
    - Result: Pure dataclass definition with no executable logic to probe; no concerns surfaced.

- [x] django_strawberry_framework/types/finalizer.py
    - docs/shadow/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/django_strawberry_framework__types__finalizer.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/finalizer.py
    - Result: Reviewed every branch and finalization phase listed against the current source; the failure-atomic Phase 1 resolution, Phase 2 resolver attachment, Phase 2.5 interface base-injection/Relay defaults, and Phase 3 decoration order are fully robust, and no concerns surfaced.

- [x] django_strawberry_framework/types/relations.py
    - docs/shadow/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__relations.stripped.py and docs/shadow/django_strawberry_framework__types__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relations.py
    - Result: Reviewed current source and confirmed the `PendingRelation` identity-hash behavior and related documentation/test coverage are already implemented; no new concerns surfaced. Validation reported: `uv run pytest tests/types/test_relations.py` passed and `uv run ruff check django_strawberry_framework/types/relations.py` passed.

- [x] django_strawberry_framework/types/relay.py
    - docs/shadow/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__relay.stripped.py and docs/shadow/django_strawberry_framework__types__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relay.py
    - Result: Reviewed every branch and check listed in the dicta against the current source; no concerns surfaced.

- [x] django_strawberry_framework/types/resolvers.py
    - docs/shadow/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/django_strawberry_framework__types__resolvers.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/resolvers.py
    - Result: Reviewed every branch and helper function listed in the dicta against current source; no active bugs or concerns surfaced.

- [x] django_strawberry_framework/utils/relations.py
    - docs/shadow/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/django_strawberry_framework__utils__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/relations.py
    - Result: Reviewed every branch listed against current source; no concerns surfaced.

- [x] django_strawberry_framework/utils/strings.py
    - docs/shadow/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/django_strawberry_framework__utils__strings.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/strings.py
    - Result: Reviewed every branch listed above against current source; no concerns surfaced.

- [x] django_strawberry_framework/utils/typing.py
    - docs/shadow/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/django_strawberry_framework__utils__typing.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/typing.py
    - Result: High-severity public API defect fixed in `django_strawberry_framework/utils/typing.py`: `unwrap_return_type` now handles bare `typing.List` and built-in `list` annotations by returning `typing.Any` instead of crashing with `IndexError` or returning the unpeeled list type. Validation: `uv run ruff format django_strawberry_framework/utils/typing.py`, `uv run ruff check --fix django_strawberry_framework/utils/typing.py`, and `uv run pytest tests/utils/test_typing.py` passed.
