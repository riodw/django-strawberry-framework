# Review: `django_strawberry_framework/management/commands/` (folder pass)

Status: verified

Fresh 0.0.9 folder pass superseding a stale single-command (0.0.7-era) artifact on disk that described `export_schema.py` as the folder's lone source sibling and referenced `review-0_0_7.md`. The folder now holds two `BaseCommand` siblings (`export_schema.py`, `inspect_django_type.py`) plus the subpackage `__init__.py`. Both per-file artifacts are `Status: verified` with their checkboxes marked (`review-0_0_9.md:86-87`); this pass synthesizes them and looks for cross-command duplication, naming/error-handling drift, the command-base responsibility boundary, `__init__.py` correctness, circular-import risk, and comment consistency. No new source findings, no edit warranted — see the shape judgment in the summary.

## DRY analysis

- **Defer-with-trigger — the dotted-path-symbol-import + `CommandError` idiom (`import_module_symbol(selector, default_symbol_name="schema")` → `except (ImportError, AttributeError) → CommandError(str(e)) from e`).** This is the one genuine cross-command duplication the folder pass exists to adjudicate, and it is a verbatim 2-site repeat: `export_schema.py::Command.handle` (`export_schema.py:34-40`) and `inspect_django_type.py::Command.handle` (`inspect_django_type.py:103-106`). Both pass the identical `default_symbol_name="schema"` and narrow to the identical `(ImportError, AttributeError)` envelope. **Stay deferred — do NOT act now.** The shared body is a 1-line strawberry call wrapped in Django's documented `CommandError`-from-`e` convention, and the two call sites diverge immediately after: `export_schema` *binds* the resolved symbol and type-guards it against `strawberry.Schema` (`export_schema.py:42-43`), whereas `inspect_django_type` *discards* the return value entirely (the import is a pure register-and-finalize side effect, `inspect_django_type.py:102-106`) and resolves its target through a separate `_resolve_type` path. Extracting a `_load_schema_symbol(selector)` helper into a new `commands/_common.py` would add a module + an import to each command to save one `except` clause whose surrounding context differs — net-negative at two sites, and exactly the "don't preemptively populate" anti-pattern `START.md` calls out. Re-extract when a **third** management command in `django_strawberry_framework/management/commands/` consumes `import_module_symbol` with the same `default_symbol_name="schema"` shape; at three sites a shared `commands/_common.py::load_schema_symbol(selector)` becomes worth the module. (Carried verbatim from `rev-management__commands__export_schema.md` DRY analysis; re-affirmed at the folder level with the divergent-epilogue evidence above.)

- **Defer-with-trigger — `inspect_django_type.py::Command._is_suppressed_relay_pk` re-spells the module-private `types/base.py::_is_relay_shaped` predicate.** `inspect_django_type.py:209-212` re-spells the exact relay-shaped body (`any(issubclass(i, relay.Node) for i in definition.interfaces) or issubclass(definition.origin, relay.Node)`); `_is_relay_shaped` is private to `types/base.py`. This is a **cross-folder** placement question, not a `commands/`-internal one (only one command consumes it, and the canonical home is the `types` package), so it is **forwarded to the project pass** rather than actioned here. Defer until a second consumer outside `types/base.py` needs the predicate; then promote `_is_relay_shaped` to a shared `types`-package helper and have both the synthesizer and this command import it. See `docs/review/rev-django_strawberry_framework.md`. (Carried from `rev-management__commands__inspect_django_type.md`; the inspect command is now that second consumer, so the trigger is effectively armed — the project pass decides the destination module.)

- **Defer-with-trigger — the `_render_annotation` / `_render_strawberry_type` rendering twin.** `inspect_django_type.py:451-467` (`typing` walk) and `inspect_django_type.py:373-386` (Strawberry-wrapper walk) share the `Name!` / `Name` / `[Inner!]!` shaping over structurally different inputs. This is intra-file to `inspect_django_type.py` (the only renderer in the folder), so it is **not a folder-level** consolidation surface and `export_schema.py` shares no rendering code with it. Recorded here only to confirm it stays deferred at folder scope. Defer until a third GraphQL-rendering surface lands; then lift the shaping rule into a shared `_graphql_shape(is_optional, is_list, leaf_name)`. (Carried from the `inspect_django_type` file pass; no folder-level action.)

## High:

None. The one High in the folder (the `_relation_row` `KeyError` on a `"connection"`-shaped relation) was raised, root-cause-fixed, and verified in `rev-management__commands__inspect_django_type.md` (`Status: verified`); re-confirmed against current source — `_relation_row` (`inspect_django_type.py:217-244`) short-circuits through `_suppressed_connection_name` → `_connection_only_relation_row` and no longer unconditionally indexes the deleted annotation. No folder-level High introduced.

## Medium:

None. No cross-command responsibility-boundary defect, no folder-level naming drift, no missing-branch coverage gap surfaced by comparing the two siblings. (The `inspect_django_type` GLOSSARY Medium was resolved in its file cycle; it was a single-entry documentation fix, not a cross-command pattern, so it does NOT promote to a folder Medium — contrast the `filters/` folder pass where a Low recurred across two parallel public-contract GLOSSARY entries and warranted folder-level promotion. Here there is exactly one GLOSSARY entry per command and both are accurate vs current source.)

## Low:

None at the folder level. Both file-pass Lows are forward-looking and command-local, not cross-command drift:

- `export_schema.py::Command.handle` `*args` defer-trigger ("second command lands") fired and re-triaged to **keep the canonical Django `BaseCommand.handle(self, *args, **options)` shape** — and the folder pass independently confirms the resolution: `inspect_django_type.py::Command.handle` (`inspect_django_type.py:99`) uses the byte-identical signature, so the two commands are *consistent*, not drifted. Consistency across the only two siblings IS the resolution; no folder-level inconsistency to flag.
- `inspect_django_type` Low 1 (the `--schema` docstring is less specific than the GLOSSARY's `default_symbol_name="schema"` naming) and Low 2 (the unreachable `'?'` defensive default in `_resolve_bare_name`) are both intra-file, no-action/recorded, and unaffected by folder-level comparison.

## What looks solid

### DRY recap

- **Existing patterns reused.** Both commands route every consumer-input failure through Django's `CommandError(...) from e` convention (`export_schema.py:40,55`; `inspect_django_type.py:106,110,114-117,119,129,139-152,326-333`), preserving the original traceback. Both resolve a schema selector through Strawberry's first-party `import_module_symbol(..., default_symbol_name="schema")` rather than re-implementing a dotted-path splitter (`export_schema.py:35-38`; `inspect_django_type.py:104`). Both declare the canonical Django `handle(self, *args: object, **options: object) -> None` override and read scalars from `options[...]`. `inspect_django_type` further consumes the existing introspection surface (`definition.field_map` keyed by `snake_case(field.name)`, `definition.relation_connections`, `definition.consumer_authored_fields`, `FieldMeta`) rather than re-deriving types — the command is a reader over `types/`-owned state, never a parallel deriver.
- **New helpers considered.** A `commands/_common.py::load_schema_symbol(selector)` collapsing the two `import_module_symbol → CommandError` arms was evaluated and **rejected for now** — only two sites, divergent epilogues (bind-and-type-guard vs discard-side-effect), and a new module to save one `except` clause is net-negative (see DRY analysis bullet 1, with the concrete 3rd-consumer re-trigger). Promoting `_is_relay_shaped` out of `types/base.py` was evaluated and **forwarded to the project pass** as a cross-folder placement question, not actioned locally.
- **Duplication risk in the current folder.** The verbatim `import_module_symbol(..., default_symbol_name="schema")` + `(ImportError, AttributeError)` + `CommandError(str(e)) from e` shape across the two `handle` bodies is the only real cross-file near-copy, and it is correctly deferred (Django-convention boilerplate over a 1-line call, divergent continuations). The intra-`inspect_django_type` repeated literals — `2x __name__` and `2x "no (list)"` (shadow overview) — are intentional sibling-output vocabulary across the annotation vs Strawberry-wrapper rendering paths, not constant candidates; centralizing them would couple two independent walkers. `export_schema.py`'s shadow overview reports `Repeated string literals: 0`, and there are **zero string literals shared *across* the two command files** (the `"schema"` `default_symbol_name` is a strawberry-API keyword value, not a folder-owned constant) — so there is no cross-file literal to hoist into a folder constant.

### Other positives

- **`commands/__init__.py` is correct and now accurate.** One-line module docstring, zero imports, zero symbols, zero executable code (shadow overview confirms — shape #2 skip-shape by structure). It correctly names *both* shipped commands — `"Implementations of the framework's manage.py commands (export_schema, inspect_django_type)."` — so the subpackage `__init__.py` is no longer the stale single-command doc the prior folder artifact implicitly assumed. No `__all__` is needed: Django discovers command modules by filesystem convention (`management/commands/<name>.py` via `django.core.management.find_commands`), never by package export, so there is nothing to re-export.
- **No circular-import risk; clean one-way dependency direction.** `export_schema.py` imports only stdlib (`pathlib`), Django, and Strawberry — zero first-party imports. `inspect_django_type.py` adds first-party imports of `registry`, `types.base`, `types.converters`, `scalars`, and `utils.strings` — all *downstream* leaf consumption, no back-edge (grep confirms no `management.commands` import anywhere in the package). Django imports each command module lazily at `call_command`/CLI-dispatch time, so even the first-party imports in `inspect_django_type` carry no import-time package-load cycle. The two commands do not import each other.
- **Command-base responsibility boundary is coherent and consistent.** Both subclass `BaseCommand`, both implement `add_arguments` + `handle`, both surface every operator-facing failure as `CommandError` (Django → clean stderr + non-zero exit, no traceback) and reserve raw exceptions only for genuine bugs. `export_schema` is a thin emit pipeline (resolve → type-guard → branch on `--path`); `inspect_django_type` is a deeper diagnostic (resolve → finalize-guard → per-field table) with its row logic factored into module-level helpers below the class. Neither command reaches into the other's concern; neither holds request/process state across invocations.
- **Error-handling vocabulary is consistent across siblings, not drifted.** Both use `CommandError(str(e)) from e` for wrapped third-party failures and distinct hand-authored `CommandError(...)` messages for the command's own guards. The message *strings* differ by command (as they must — different failure surfaces), but the *shape* is uniform, so a maintainer reading one command predicts the other.
- **Test discipline split across the AGENTS.md trees is consistent across both commands.** Each command pins its failure modes in the package tree (`tests/management/test_export_schema.py`, `tests/management/test_inspect_django_type.py`) and earns its success path through real `call_command` usage in the example tree (`examples/fakeshop/tests/`), per AGENTS.md "earn it through real usage." The `inspect_django_type` High fix is pinned by a real-model, real-finalize, real-`call_command`, no-mock package test, with the documented placement rationale (no example type declares `relation_shapes`).

### Summary

A clean two-command folder. The two `BaseCommand` siblings share exactly one real idiom — the `import_module_symbol(..., default_symbol_name="schema") → (ImportError, AttributeError) → CommandError(str(e)) from e` resolve-with-wrap — and at folder level that stays a **defer-with-trigger** (2 sites, divergent epilogues, Django-convention boilerplate over a 1-line call; re-extract a `commands/_common.py` helper only at a 3rd `default_symbol_name="schema"` consumer). The `handle(self, *args, **options)` shape is identical across both, so the prior cycle's `*args` defer-trigger resolves to "consistent, keep the canonical Django shape." The subpackage `__init__.py` is correct and accurately names both commands; there is no circular-import risk and a clean one-way dependency direction (`export_schema` first-party-free, `inspect_django_type` a downstream leaf consumer of `registry`/`types`/`scalars`/`utils`). Both file-level findings are command-local and forward-looking, and the one folder High (`inspect_django_type` `KeyError`) was already root-cause-fixed and verified in its file cycle. The `_render_*` twin is intra-file to one command and the `_is_relay_shaped` re-spell is a cross-folder placement question forwarded to `rev-django_strawberry_framework.md`. **No new source findings, no High, no Medium, no folder-level Low, and zero edits to any tracked file — a no-findings folder pass (shape #3) that additionally qualifies as a no-source-edit cycle (shape #5): Worker 1 fills the Worker 2 sections inline, runs both ruff commands, and sets bare `Status: fix-implemented`.**

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle. (The `rev-management__commands.md` artifact on disk was a stale single-command 0.0.7-era folder pass referencing `review-0_0_7.md`; it is superseded by this fresh 0.0.9 folder pass per the recurring stale-artifact-replacement pattern. The active plan box `review-0_0_9.md:88` was unchecked, confirming the replacement.)

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/management/commands/` — "3 files already formatted" (the `COM812`-vs-formatter notice is the standing global config warning, harmless).
- `uv run ruff check django_strawberry_framework/management/commands/` — "All checks passed!".

### Notes for Worker 3
- Folder pass over two `BaseCommand` siblings + the subpackage `__init__.py`. No High/Medium/Low at the folder level; all severities `None.`
- The two carried DRY items (the `import_module_symbol → CommandError` 2-site idiom; the `_render_*` twin) are correctly **deferred** at folder scope — re-affirmed with the divergent-epilogue and single-renderer evidence in the DRY analysis. Neither is act-now.
- One cross-folder concern (the `_is_relay_shaped` re-spell at `inspect_django_type.py:209-212` vs the module-private `types/base.py::_is_relay_shaped`) is **forwarded to the project pass** `docs/review/rev-django_strawberry_framework.md`, not actioned here.
- No GLOSSARY-only fix in scope. The two command GLOSSARY entries were resolved/verified in their respective file cycles and are accurate vs current source; the folder pass introduces no GLOSSARY drift.
- No shadow file regenerated — the plan-time `--all` overviews for `export_schema.py`, `inspect_django_type.py`, and `commands/__init__.py` are current (source unchanged since the file cycles closed).
- Out-of-scope dirty paths at dispatch are presumptively concurrent maintainer / closed-sibling-cycle work per `AGENTS.md` rule 33 and left untouched.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. Both command docstrings and the subpackage `__init__.py` docstring are accurate against current behaviour and consistent with each other in vocabulary; the `inspect_django_type` connection-only nuance was already documented at the method-docstring altitude and in the GLOSSARY during its file cycle. No cross-command comment drift surfaced by the folder comparison.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

`Not warranted`. No source/test/GLOSSARY/CHANGELOG edits this cycle. Cited per the "Not warranted" gate: (1) `AGENTS.md` rule 21 — "Do not update CHANGELOG.md unless explicitly instructed"; (2) the active plan (`review-0_0_9.md`) records no changelog authorization for this folder-pass item, and the dispatch prompt forbids touching `CHANGELOG.md` (folder pass = review only; cross-folder concerns forward to the project pass).

---

## Verification (Worker 3)

**Pass scope: TERMINAL** (incoming bare `fix-implemented`; no-findings folder pass / shape #5). No-findings folder pass — no defect to address, so verification is: (a) confirm no folder-level defect was missed, (b) confirm the two sibling file cycles' High/Medium were correctly NOT re-promoted to folder findings, (c) confirm zero NEW tracked edits this cycle.

### Logic verification outcome — no folder-level defect missed
- **Shared `import_module_symbol → CommandError` idiom is consistent, not drifted.** Both `handle` bodies wrap `import_module_symbol(..., default_symbol_name="schema")` in `except (ImportError, AttributeError) → CommandError(str(e)) from e` (`export_schema.py:34-40`; `inspect_django_type.py:103-106`, grep-confirmed). Identical envelope, identical `default_symbol_name`, then divergent epilogues (export binds + type-guards `strawberry.Schema`; inspect discards the return as a register-and-finalize side effect). Correctly deferred — Django-convention boilerplate over a 1-line call at 2 sites with divergent continuations; the 3rd-`default_symbol_name="schema"`-consumer re-trigger is concrete and recorded. No error-handling drift.
- **`handle(self, *args, **options)` shape identical across both siblings.** `grep "def handle"` → both at `def handle(self, *args: object, **options: object) -> None:` (`export_schema.py:25`, `inspect_django_type.py:99`). The prior-cycle `*args` defer-trigger ("second command lands") resolves to "consistent, keep the canonical Django override shape" — confirmed, no inconsistency to flag.
- **`commands/__init__.py` correct.** One-line module docstring naming BOTH shipped commands (`export_schema`, `inspect_django_type`), zero imports, zero symbols, zero executable code (read in full). No `__all__` needed — Django discovers command modules by filesystem convention, never by package export. Accurate, no longer the stale single-command doc.
- **No circular-import risk; clean one-way dependency.** `grep -rn "management.commands" django_strawberry_framework/ | grep import` → NONE. No back-edge into `management.commands` anywhere in the package; the two commands do not import each other; `inspect_django_type`'s first-party imports (`registry`/`types`/`scalars`/`utils`) are downstream leaf consumption loaded lazily at CLI-dispatch time.
- **The 3 DRY bullets correctly deferred-with-trigger / forwarded.** (1) the `import_module_symbol → CommandError` idiom — deferred (above). (2) `inspect_django_type.py::_is_suppressed_relay_pk` (`:209-212`) re-spells `types/base.py::_is_relay_shaped` — confirmed at source a genuine body re-spell: `_is_suppressed_relay_pk` inlines `any(issubclass(i, relay.Node) for i in definition.interfaces) or issubclass(definition.origin, relay.Node)`, the exact predicate `_is_relay_shaped(cls, interfaces)` returns at `base.py:454` (`any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`). Correctly **forwarded to the project pass** `docs/review/rev-django_strawberry_framework.md` as a cross-folder placement question (the canonical home is the `types` package, `_is_relay_shaped` is `types/base.py`-private, only one command consumes it) — NOT a `commands/`-internal defect. The forward is recorded in this artifact (DRY bullet 2 + Notes-for-Worker-3 bullet 3, both naming the destination). (3) the `_render_annotation`/`_render_strawberry_type` twin — intra-`inspect_django_type.py`, not a folder-level surface; `export_schema.py` shares no rendering code. Correctly deferred. None act-now.

### Sibling High/Medium NOT re-promoted — correct
- The folder's one High (`_relation_row` KeyError on a `"connection"`-shaped relation) was root-cause-fixed and verified in `rev-management__commands__inspect_django_type.md` (`Status: verified`, `[x]` at review-0_0_9.md:87). Re-confirmed current source short-circuits via `_suppressed_connection_name` (`:202`+) → `_connection_only_relation_row` and no longer unconditionally indexes the popped annotation. No folder-level High introduced — correct not to re-promote a closed-cycle finding.
- The inspect GLOSSARY Medium was a single-entry doc fix resolved in its file cycle, not a cross-command pattern → correctly NOT promoted to a folder Medium (contrast the `filters/` folder pass where a Low recurred across two parallel public-contract GLOSSARY entries). Each command has exactly one GLOSSARY entry, both accurate vs source.

### Zero NEW tracked edits this cycle (shape #5 / no-findings folder pass)
- **Owned-path diff NOT empty but fully attributes to a CLOSED sibling cycle.** `git diff --stat 0872a20f -- django_strawberry_framework/management/commands/` shows `inspect_django_type.py +61/-2` — this is the closed sibling cycle `rev-management__commands__inspect_django_type.md`'s High fix (`Status: verified`, `[x]` at review-0_0_9.md:87), NOT this folder pass's work. Per the sibling-cycle-attribution rule, a hunk owned by a closed sibling (verified + [x]) is NOT a rejection trigger. `export_schema.py` cycle diff is empty.
- The folder pass's own "Files touched: None" claim holds — this cycle authored zero source/test edits.
- Broader diff-stat dirty source (`conf.py`, `exceptions.py`, `filters/factories.py`, `filters/sets.py`, `list_field.py`) + `docs/GLOSSARY.md` three hunks (286 `DjangoConnection`→rev-connection.md; 991/1001 `RelatedFilter`/`RelatedOrder`→rev-filters.md) all attribute to CLOSED sibling cycles (verified + [x]). `feedback2.md`/`feedback3.md` deletions = AGENTS.md #33 concurrent-maintainer work. Untracked `rev-connection.md`/`rev-relay.md`/`rev-management__commands__inspect_django_type.md`/`review-0_0_9.md` are concurrent-cycle artifacts. All left untouched.

### DRY findings disposition
All three DRY items defer-with-trigger / forwarded (above). One forward-target note: the project-pass artifact `docs/review/rev-django_strawberry_framework.md` does not yet carry the `_is_relay_shaped` shared-home decision (grep returns nothing), but its plan box at review-0_0_9.md:128 is unchecked — the project pass has NOT yet run for 0.0.9 (its `Status: verified` at line 3 is a stale carried value; file is git-clean). This folder pass's duty is record+route, which it satisfies. The destination gap is prose debt for the project-pass cycle to pick up, NOT a rejection trigger for this folder pass.

### Changelog disposition verification
`Not warranted`. `git diff -- CHANGELOG.md` EMPTY (confirmed). Both citations present: AGENTS.md rule 21 + active-plan silence / dispatch-prompt prohibition. Internal-only framing honest — zero source/test/GLOSSARY/CHANGELOG edits this cycle. Correct state.

### Temp test verification
None created — a no-findings folder pass with no defect to reproduce. The folder-level invariants (consistent idiom, identical `handle` shape, `__init__.py` correctness, no circular import) are verified by direct source read + grep, no behavior to exercise.

### Validation
- `uv run ruff check django_strawberry_framework/management/commands/` → All checks passed.
- `uv run ruff format --check django_strawberry_framework/management/commands/` → 3 files already formatted (standing COM812 formatter-conflict warning only).

### Verification outcome
`cycle accepted; verified` — set top-level `Status: verified` AND marked the management/commands/ folder-pass box `[x]` at `docs/review/review-0_0_9.md:88`. The `_is_relay_shaped` shared-home decision is correctly forwarded to the project pass `rev-django_strawberry_framework.md` (recorded here; destination cycle not yet run).

---

## Iteration log
