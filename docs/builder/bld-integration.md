# Cross-slice integration: export_schema / 0.0.7 (018)

Spec source: `docs/spec-018-export_schema-0_0_7.md`
Build plan: `docs/builder/build-018-export_schema-0_0_7.md`
Status: final-accepted

## Spec slice checklist (verbatim)

No spec-level checklist for integration; the build plan's "Cross-slice integration pass" checkbox is the contract. The integration audit below walks the BUILD.md "Cross-slice integration pass" checklist (lines 511-531) end-to-end.

## Audit walkthrough

### 1. Slice artifacts read

Walked all three per-slice artifacts in slice order, as required by `docs/builder/BUILD.md` lines 513-515. No "as needed" — every artifact is required context for the cross-slice DRY scan:

- `docs/builder/bld-slice-1-module.md` — Slice 1 (module + `Command` subclass). Status: `final-accepted`. Shipped `django_strawberry_framework/management/{__init__.py, commands/__init__.py, commands/export_schema.py}`. Worker 3 ran the static helper on `export_schema.py`; reported 0 repeated string literals, 0 control-flow hotspots, 0 Django/ORM markers, 1 call of interest (`isinstance` at line 36).
- `docs/builder/bld-slice-2-tests.md` — Slice 2 (tests). Status: `final-accepted`. Shipped `tests/management/{__init__.py, test_export_schema.py}` plus one new function in `examples/fakeshop/tests/test_commands.py`. Worker 3 ran the static helper on `test_export_schema.py`; reported 4 repeated string literals, 0 control-flow hotspots, 0 Django/ORM markers, 1 call of interest (`setattr` at line 25 inside `_make_test_module`). All four repeated literals noted by Worker 3 as "spec-pinned and not extractable."
- `docs/builder/bld-slice-3-promotion_docs.md` — Slice 3 (promotion + docs). Status: `final-accepted`. Shipped doc-only updates across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`. Maintainer commit `216e6ba` landed the KANBAN column move and CHANGELOG bullet ahead of Worker 2's build pass; Worker 2's residual contribution was a single-line `KANBAN.md:62` cleanup of the stale "Still not implemented" entry. Static helper not applicable (no `.py` files in scope).

### 2. Static inspection helper coverage

Per BUILD.md lines 516-517, every `.py` file with review-worthy logic touched by the build was either covered by a helper run or has a recorded skip with reason. Audit:

- `django_strawberry_framework/management/__init__.py` — marker module, one-line docstring, no logic. Skipped at review (recorded in Slice 1 artifact's "Static inspection helper disposition" sub-section under Worker 3's review).
- `django_strawberry_framework/management/commands/__init__.py` — marker module, one-line docstring, no logic. Skipped at review (recorded in Slice 1 artifact).
- `django_strawberry_framework/management/commands/export_schema.py` — review-worthy logic (`handle` body with try/except, isinstance guard, branching write). Helper run at review (Slice 1). Shadow at `docs/shadow/django_strawberry_framework__management__commands__export_schema.overview.md`.
- `tests/management/__init__.py` — marker module, one-line docstring, no logic. Skipped at review (recorded in Slice 2 artifact).
- `tests/management/test_export_schema.py` — review-worthy logic (7 test bodies + 2 module-level helpers). Helper run at review (Slice 2). Shadow at `docs/shadow/tests__management__test_export_schema.overview.md`.
- `examples/fakeshop/tests/test_commands.py` — existing file extended by one 4-line test function plus a 3-line dash-banner. Under BUILD.md's 50-line outside-package threshold; helper skipped at Slice 2 review with recorded reason.
- `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` — Markdown / changelog surfaces, not `.py` files. Helper does not apply (recorded in Slice 3 artifact's "Static inspection helper disposition" sub-section).

Coverage audit clean.

### 3. Repeated string literals comparison

Walked the **Repeated string literals** sections across every shadow overview produced by the build (BUILD.md lines 517-518):

- `docs/shadow/django_strawberry_framework__management__commands__export_schema.overview.md` reports **0 repeated string literals**.
- `docs/shadow/tests__management__test_export_schema.overview.md` reports **4 repeated string literals**: `"export_schema"` (7x), `"test_module"` (3x), `"type Query"` (3x), `"test_module:schema"` (2x).

Cross-file analysis: the four literals in the test file all repeat **only within the test file**; none of them appear in `export_schema.py`. The non-`Schema` `CommandError` message `"The \`schema\` must be an instance of strawberry.Schema"` appears once in `export_schema.py` (the raise site at line 37) and once in `test_export_schema.py` (line 76, as the `match=` regex pattern). Confirmed both forms are consistent — the test uses `match=r"must be an instance of strawberry\.Schema"` where `\.` is the regex escape for the literal `.` in `strawberry.Schema`. The regex substring matches the raise-site message exactly; the `\.` escape is correct (without it, `.` would match any character — still functionally pass, but the escaped form is the precise intent and is what the spec pins at line 608).

No cross-slice repeated literal warrants extraction into a shared constant. Each repeated literal is local to a distinct test contract pinned by the spec; promoting any of them to a module-level constant would obscure the pinned-by-spec status at the call site.

### 4. Imports comparison

Walked the **Imports** sections across every shadow overview (BUILD.md lines 518-519). One-way dependency direction confirmed:

- `export_schema.py` imports: `pathlib` (stdlib), `BaseCommand` / `CommandError` / `CommandParser` from `django.core.management.base` (django), `Schema` from `strawberry` (strawberry), `print_schema` from `strawberry.printer` (strawberry), `import_module_symbol` from `strawberry.utils.importer` (strawberry). **Zero first-party `django_strawberry_framework.*` imports** — the management command is a leaf module that depends only on Django and Strawberry. This is correct: the command resolves consumer schemas through string dotted paths via `import_module_symbol`, not via `from django_strawberry_framework.something import ...`.
- `test_export_schema.py` imports: `sys` (stdlib), `types` (stdlib), `StringIO` from `io` (stdlib), `pytest` (third-party), `strawberry` (strawberry), `CommandError` / `call_command` from `django.core.management` (django). **Zero first-party `django_strawberry_framework.*` imports** — and crucially **does not import the `Command` class directly**. The test invokes the command via `call_command(...)` exclusively, per Decision 8. Confirmed by Worker 3's review of Slice 2 (artifact line 280: "`Command` is not imported anywhere in `tests/management/test_export_schema.py` or in the fakeshop test extension").

Sibling-import check (BUILD.md line 518): no sibling outside `django_strawberry_framework/` has started importing from `django_strawberry_framework/management/*`. The management commands are not a consumer API; the only "consumer" of the command is Django's `manage.py` machinery, which resolves it through `INSTALLED_APPS` directory walking — not through a Python import statement. `grep` of `tests/`, `examples/`, and `django_strawberry_framework/` for `from django_strawberry_framework.management` or `import django_strawberry_framework.management` returns zero hits outside the build's own tests directory (and even those tests do not import `Command` — they use `call_command`). Layering invariant holds.

### 5. Deferred follow-up scan

Walked every accepted slice artifact's `What looks solid` and `DRY findings` sections, plus `Notes for Worker 1` reconciliation notes, for deferred follow-up (BUILD.md line 519):

- **Slice 1 DRY findings**: explicit "No duplicated literals, no repeated key/tuple shapes, no near-copies of existing helpers. ... Nothing to flag for the cross-slice integration pass from this slice's surface." No deferral.
- **Slice 2 DRY findings**: explicit walkthrough of the four repeated literals (`export_schema`, `test_module`, `type Query`, `test_module:schema`) — each is local to a distinct test contract pinned by the spec; no centralization warranted. The `_make_test_module` / `_make_schema` helper extractions are spec-authorized DRY consolidation (spec lines 600-602) and are module-level plain functions, not `@pytest.fixture`-decorated, so the "use inline per test, not a session fixture" rule is honored literally. No deferral.
- **Slice 3 DRY findings**: cross-document verbatim wording at five sites (GLOSSARY entry body, README "Shipped today" bullet, CHANGELOG `### Added` bullet, KANBAN Done body lead sentence, GLOSSARY Index row) — Worker 3 confirmed character-for-character match against the spec source at all four prose sites. No paraphrase drift. No deferral.
- **Slice 3 `Notes for Worker 1 (spec reconciliation)`** (Worker 3): three notes, all intentionally deferred to the build's closeout or accepted as out-of-scope cleanup that does not warrant a rev6:
  - Note 1 (maintainer commit `216e6ba` landed the column move ahead of Worker 2's build pass): no spec edit needed; build plan's "Mid-build baseline drift addendum" already records this.
  - Note 2 (spec line citations drifting against live line numbers): pin-at-write-time hints per BUILD.md, not load-bearing contracts. Worker 1 Slice 3 final verification correctly deferred a refresh — touching the spec for non-load-bearing cleanup would force a rev6 and misalign the revision history.
  - Note 3 (spec status line still reads `draft (revision 5, ...)`): deferred to Worker 0's closeout / the joint-cut last-card-to-ship. WIP-ALPHA-019-0.0.7 and WIP-ALPHA-020-0.0.7 are still queued; the joint cut isn't complete yet.

None of these deferrals require an integration-pass consolidation; all are correctly routed to either Worker 0 closeout (status-line flip) or "no action" (line-citation drift, maintainer commit acknowledgement).

## DRY findings

### Integration-checklist sub-items walked (BUILD.md lines 521-529)

- **Duplicated helpers across slices.** None. Slice 1's `Command(BaseCommand)` is a leaf class with no extracted helpers; Slice 2's `_make_test_module` and `_make_schema` are local to the test file (module-level plain functions, not exported); Slice 3 ships zero `.py` code. No helper duplication possible.
- **Inconsistent naming or error handling between slices.** None. The non-`Schema` `CommandError` message at `export_schema.py:37` (`"The \`schema\` must be an instance of strawberry.Schema"`) is matched by the test at `test_export_schema.py:76` (`match=r"must be an instance of strawberry\.Schema"`); the regex form correctly escapes the literal `.`. The `(ImportError, AttributeError)` catch tuple at `export_schema.py:33` is exercised by two separate tests (c) and (d) — one per arm — per the spec's rev2 M1 split. No naming or error-handling inconsistency.
- **Repeated ORM/queryset patterns that should be centralized.** Not applicable. The shadow overview for `export_schema.py` reports `executable marker lines: 0` Django/ORM markers; the command does not touch the ORM. The shadow overview for `test_export_schema.py` also reports zero ORM markers. No ORM patterns to centralize.
- **Misplaced responsibilities between modules touched by different slices.** None. Slice 1 owns the source module; Slice 2 owns the package-internal tests and the one-test fakeshop extension; Slice 3 owns the documentation surface. The boundaries are crisp: Slice 1 has no test imports; Slice 2 has no source imports (uses `call_command` string dispatch); Slice 3 ships no `.py` code.
- **Missing or too-broad exports introduced by the build.** None. `git diff -- django_strawberry_framework/__init__.py` returns empty (verified at audit time); `__all__` is unchanged at the 8-entry tuple from before the build. The Slice 1 / Slice 2 / Slice 3 spec checklists all explicitly forbade adding `Command` to `__all__`; each slice's Worker 3 review confirmed the public-surface invariant via the same empty-diff check.
- **Repeated string literals / dictionary keys / tuple shapes across slices.** None across slices (within-file repetitions in Slice 2 are local to distinct test contracts and not extractable — see "Repeated string literals comparison" above). The one literal that spans two files — the non-`Schema` `CommandError` message — is correctly matched (raise site + regex `match=` pattern with proper `\.` escape) and pinned by the spec for regression safety.
- **Whether comments now tell one coherent story across the new code.** Yes. Slice 1's `export_schema.py` carries one module docstring + one class docstring + two method docstrings (`D100` / `D101` / `D102` root-cause fixes, no `# noqa` suppressions). Slice 2's `test_export_schema.py` carries one module docstring plus three dash-banner section comments (`Shared fixture pattern (use inline per test, not a session fixture)`, `Happy paths`, `Failure modes`, `Default-symbol-name fallback`) that visually anchor the spec's (a)-(g) test grouping. Slice 3's documentation edits reproduce the spec's pinned wording verbatim at four prose sites — no paraphrase drift, no contradiction between the GLOSSARY entry body, the README "Shipped today" bullet, the CHANGELOG `### Added` bullet, and the KANBAN DONE-018 lead sentence. The comments and docs are mutually consistent and reference one another correctly (the README bullet links to `GLOSSARY.md#schema-export-management-command`; the GLOSSARY heading anchor still resolves).

### Cross-slice DRY findings

None. The build is small-surface (one ~45-line source module, one ~95-line test file, one 4-line fakeshop test extension, doc-only Slice 3) and the inter-slice boundaries are crisp by design — Slice 1's source has no first-party imports; Slice 2's tests do not import `Command` directly (Decision 8); Slice 3 ships zero `.py` code. No cross-slice duplication to consolidate.

## What looks solid

- **Layering is one-way and tight.** `export_schema.py` imports from Django + Strawberry only (zero first-party imports); `test_export_schema.py` invokes via `call_command` only (zero `Command` imports); no sibling outside `django_strawberry_framework/` has started importing from `management/*`. The management commands are correctly modeled as import-time plumbing discovered through `INSTALLED_APPS`, not a consumer API.
- **The non-`Schema` `CommandError` message is consistently pinned across the source/test boundary.** Raise site at `export_schema.py:37` carries the spec-verbatim `"The \`schema\` must be an instance of strawberry.Schema"` (backticks around `schema` preserved per the upstream wording); the test at `test_export_schema.py:76` uses `match=r"must be an instance of strawberry\.Schema"` with the literal `.` correctly escaped as `\.`. A future paraphrase-drift on either side would fail the regex; the test pin is durable.
- **Public-surface invariant held across all three slices.** `git diff -- django_strawberry_framework/__init__.py` is empty after Slice 3 final-acceptance; `__all__` is the same 8-entry tuple it was before the build started. No new public exports introduced. Slice 1 / Slice 2 / Slice 3 each explicitly verified this independently; the cross-slice re-check at the integration pass confirms the same. Zero divergence between the spec's "no new public exports" contract (Decision 1, Slice 3 sub-bullet at spec line 81, DoD item 12) and the shipped state.

## Notes for Worker 0

- **No consolidation loop needed.** The integration pass is clean — zero High/Medium/Low findings, zero cross-slice DRY opportunities. Worker 0 should dispatch directly to the final test-run gate (Worker 1, `docs/builder/bld-final.md`); no Worker 2 / Worker 3 second loop is warranted.
- **Spec status-line flip is still deferred to the joint-cut last-card-to-ship.** Per Worker 3's Slice 3 reconciliation note 3 and Worker 1's Slice 3 final-verification disposition, the spec's `Status: draft (revision 5, ...)` line at `docs/spec-018-export_schema-0_0_7.md:4` stays at `draft` until the joint `0.0.7` cut completes (WIP-ALPHA-019-0.0.7 and WIP-ALPHA-020-0.0.7 are still queued). The final test-run gate (Worker 1 again) is not the right point to flip it either — that gate verifies the test suite passes, not the spec lifecycle. The flip belongs to whichever Worker 1 spawn closes out the joint bundle once 019 and 020 have shipped.
- **Maintainer concurrent activity recorded in the build plan.** The build plan's two "Mid-build baseline drift" notes at `docs/builder/build-018-export_schema-0_0_7.md:8-15` accurately describe (a) the KANBAN NNN renumbering that landed mid-build, (b) the maintainer commits `d2a10de remove 017 artifacts` and `216e6ba update card names` that landed between Slice 2 final-acceptance and the Slice 3 build pass. The final test-run gate should not be surprised by these; they are out-of-scope build noise per `AGENTS.md` line 31, not build issues.
- **Out-of-scope modified files at integration time.** `git status --short` at integration time shows the same out-of-scope baseline-maintenance files the build plan recorded: `M django_strawberry_framework/scalars.py`, `M docs/review/rev-django_strawberry_framework.md`, `M docs/review/rev-scalars.md`. None are in 018's scope; the final test-run gate should record them as out-of-scope and not flag them as build issues.

## Final status

`final-accepted`. The integration pass surfaces no cross-slice duplication, no naming or error-handling inconsistency, no layering violation, no missing or too-broad exports, no repeated cross-file literals warranting consolidation, and no incoherence between the comments and docs the three slices shipped. The small-surface card landed exactly as the spec described it; no second loop is needed. Worker 0 dispatches the final test-run gate next.
