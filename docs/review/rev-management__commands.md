# Review: `django_strawberry_framework/management/commands/` (folder pass)

Status: verified

## DRY analysis

- None — the folder is a minimal two-file package (`__init__.py` is one-line module docstring with zero imports, zero symbols, zero exec code; `export_schema.py` is the single 55-line `BaseCommand` sibling). With exactly one source sibling there is no cross-file duplication surface to consolidate: no shared helpers to extract, no naming convention to align across siblings, no repeated string literals or constants that would benefit from a per-folder module. The per-file artifact `rev-management__commands__export_schema.md` already enumerated and rejected every intra-file DRY opportunity (the two `except → CommandError(str(e)) from e` arms catch disjoint exception families across separated call sites; the three-branch `--path` ladder shares no common epilogue), and explicitly recorded a defer-with-trigger Low gating the `*args` collapse on a "second management command lands in `django_strawberry_framework/management/commands/`" condition. Revisit folder-level DRY only when that trigger fires — at which point this folder pass would re-grep for cross-command shared shapes (a `_load_schema_symbol` helper, a shared positional/argparse convention, repeated `CommandError` message phrasings) and decide whether a `_common.py` sibling is warranted.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The folder's single non-`__init__` sibling (`export_schema.py`) routes through Strawberry's first-party helpers (`import_module_symbol`, `print_schema`) and Django's first-party `BaseCommand` + `CommandError` + `CommandParser` + `self.style.SUCCESS` rather than re-implementing dotted-path resolution, SDL serialization, or terminal styling. The folder's `__init__.py` does nothing beyond carrying the one-line `"""Management command implementations for django-strawberry-framework."""` module docstring — the canonical empty-namespace shape for a Django `management/commands/` package, mirroring Django's own `django/core/management/commands/__init__.py`. Auto-discovery is driven by `django.core.management.find_commands` walking the folder for non-private `.py` files, so the `__init__.py` deliberately exposes no `__all__` and no re-exports.
- **New helpers considered.** A folder-level `_common.py` (shared `CommandError`-wrap helper, shared positional-`schema` argparse convention, shared SDL-emit branch ladder) was considered for the case where a second management command lands. Rejected at this pass because: (a) there is no second consumer today; (b) the per-file artifact already records the defer-with-trigger Low ("revisit when a **second** management command lands ... and either commits to `*args` or drops it"); (c) speculating a shared shape against a single concrete command is exactly the "preemptively populate" anti-pattern called out in `START.md` ("Don't preemptively populate `conf.py` with future-feature settings. ... add a settings key only when the feature that needs them lands"). The same rule applies to a `management/commands/_common.py` module: extract when the second consumer arrives, not before.
- **Duplication risk in the current folder.** None — with exactly one source file there is no cross-file repeated-literal surface (`scripts/review_inspect.py`'s folder-pass repeated-literals check returned zero hits; `__init__.py` carries zero literals). The single sibling carries three distinct `CommandError(...)` messages that the per-file artifact already confirmed are deliberately non-shared.

### Other positives

- **`__init__.py` is the canonical empty namespace.** `django_strawberry_framework/management/commands/__init__.py` (one line: the module docstring) qualifies as a structural skip (shape #2 in `REVIEW.md`'s "No-op / skip / consolidated single-spawn cycles" list — module contains only a docstring; zero imports, zero symbols, zero executable code outside class bodies, zero first-party imports). The shadow overview confirms: "imports: 0; symbols: 0; control-flow hotspots: 0; executable marker lines: 0; calls of interest: 0; TODO comments: 0; repeated string literals: 0." Django's auto-discovery mechanism (`django.core.management.find_commands`) reads the folder via `os.listdir` and does not import `__init__.py` for command enumeration, so no re-export is required and adding one would obscure the auto-discovery contract.
- **Naming convention matches Django.** The single command file is `export_schema.py` (lowercase + underscore, matches Django's own `loaddata.py` / `migrate.py` / `runserver.py` casing); `manage.py export_schema` is the resulting subcommand name. No naming drift to flag.
- **Import direction is downward.** `export_schema.py` imports only from `django.core.management.base`, `strawberry`, `strawberry.printer`, and `strawberry.utils.importer` — no first-party `django_strawberry_framework.*` imports, so the folder has zero exposure to circular-import risk from sibling packages (`registry`, `conf`, `_django_patches`, `optimizer`, `types`, `filters`, `utils`, `testing`, `sets_mixins`, `list_field`, `scalars`, `exceptions`). A future management command that needs to introspect a registered type would route through `django_strawberry_framework.registry` lazily inside `handle()` (deferred import) to keep `manage.py help` cheap, but no such command exists today.
- **Test discipline already inventoried.** The per-file artifact's "Test discipline (split across two trees)" bullet enumerates the two-tree split: `tests/management/test_export_schema.py` carries the seven failure-mode pins (package-internal tree per `AGENTS.md`); `examples/fakeshop/tests/test_export_schema.py` carries the live `call_command` success-path coverage for stdout and `--path <file>` branches. The split honors the `AGENTS.md` real-usage rule and is the canonical shape carried forward in the per-file artifact's "Carry forward" note ("If a future management command's success-path tests live only in `tests/`, that's a real-usage-rule miss worth flagging").
- **GLOSSARY coverage for the folder is appropriate.** The per-file artifact already closed the GLOSSARY-drift Medium on `Schema export management command` (`docs/GLOSSARY.md:1011`); no separate folder-level entry is warranted for the folder or for the `__init__.py` (there is no consumer-visible folder-level symbol — the `commands/` directory is a Django convention enforced by `find_commands`, not a re-exported namespace). The folder-pass GLOSSARY drift quick-check confirms: zero backticked symbols in `__init__.py`, single sibling already documented.

### Summary

The folder is a minimal `management/commands/` Django namespace with exactly one source sibling (`export_schema.py`, reviewed and verified in `rev-management__commands__export_schema.md`) plus a one-line module-docstring `__init__.py`. The `__init__.py` qualifies as a skip artifact (shape #2 by structure: docstring-only, zero imports, zero symbols, zero executable code, no `__all__`, no first-party imports — confirmed via the shadow overview) and the folder pass has no cross-file surface to find issues against. No High, no Medium, no Low at folder scope; no DRY opportunity until the defer-with-trigger from the per-file artifact fires (second management command landing). The folder pass qualifies for shape #5 (no-source-edit cycle, skip Worker 2) per `worker-1.md`: zero edits to any tracked file, no High / no behaviour-changing Medium, no GLOSSARY-only fix in scope, both ruff runs clean. Worker 1 fills the Worker 2 sections inline; Worker 0 dispatches Worker 3 directly for terminal verification.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched

None — no-source-edit cycle.

### Tests added or updated

None — no-source-edit cycle.

### Validation run

- `uv run ruff format --check django_strawberry_framework/management/commands/` — pass ("2 files already formatted"; harmless `COM812`-vs-formatter conflict warning is a global config notice, not a folder-specific issue).
- `uv run ruff check django_strawberry_framework/management/commands/` — pass ("All checks passed!").

### Notes for Worker 3

- Folder pass over a two-file namespace (`__init__.py` skip-shape + `export_schema.py` already verified in `rev-management__commands__export_schema.md`). With only one source sibling there is no cross-file naming drift, no shared helper candidate, no repeated literal, and no import-direction concern to flag — these checks all returned zero hits.
- `__init__.py` is structurally shape #2 (skip artifact: docstring-only module, zero imports/symbols/exec-code, no `__all__`, no first-party imports). The shadow overview at `docs/shadow/django_strawberry_framework__management__commands____init__.overview.md` confirms every counter is zero.
- No GLOSSARY-only fix in scope — the per-file artifact already closed the only GLOSSARY drift in this subtree (`docs/GLOSSARY.md:1011`, `Schema export management command`); the folder has no consumer-visible folder-level symbol (Django's `find_commands` enumeration is convention-driven, not via `__all__`), so no folder-level GLOSSARY entry is warranted.
- Defer-with-trigger carry-forward from `rev-management__commands__export_schema.md`'s Low (b): "revisit when a **second** management command lands in `django_strawberry_framework/management/commands/` and either commits to `*args` (collecting nargs positionals) or drops it." That same trigger gates the folder-level DRY recap above — when the second command lands, this folder pass should re-grep for cross-command shared shapes (`_load_schema_symbol`, shared positional/argparse convention, repeated `CommandError` phrasings) and decide whether a `_common.py` sibling is warranted.
- No shadow file regeneration required — the existing `docs/shadow/django_strawberry_framework__management__commands____init__.overview.md` (referenced above) was the plan-time `--all` sweep output and the `__init__.py` source has not changed since.
- Out-of-scope dirty paths at dispatch are presumptively concurrent maintainer work per `AGENTS.md` rule 33 and ignored.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched

None — no-source-edit cycle.

### Per-finding dispositions

- No High / Medium / Low at folder scope — every finding the per-file pass produced was resolved or deferred-with-trigger in `rev-management__commands__export_schema.md`. No comment/docstring text to adjust at the `__init__.py` layer: the existing one-line module docstring (`"""Management command implementations for django-strawberry-framework."""`) is accurate, terse, and idiomatic for a Django `management/commands/` namespace.

### Validation run

- Shared with the logic pass above; both ruff commands pass.

### Notes for Worker 3

Per-finding dispositions above cover the full set; consolidated no-source-edit shape means the validation run is shared with the logic pass.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

### State

`Not warranted`.

### Reason

No source / test / GLOSSARY / CHANGELOG edits this cycle — folder pass produced zero findings at folder scope. Per `AGENTS.md` rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan's silence on changelog authorization for this cycle item (`docs/review/review-0_0_7.md` lists the folder-pass artifact at line 24 with no changelog notation), no CHANGELOG entry is warranted.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- Shared with the logic / comment pass above; both ruff commands pass.

---

## Verification (Worker 3)

<!-- Worker 3 fills below. -->

### Logic verification outcome

Shape #5 no-source-edit folder pass over the two-file `management/commands/` namespace. The artifact carries zero High / Medium / Low findings at folder scope; the per-file sibling artifact (`rev-management__commands__export_schema.md`, `Status: verified`) closed every actionable issue on `export_schema.py`. All five shape #5 checks pass:

1. Scoped diff stat — the working tree shows two dirty hunks in scope (`django_strawberry_framework/management/commands/export_schema.py` docstring citation + `docs/GLOSSARY.md:1011` schema-export entry rewrite). Both belong to the immediately-preceding per-file sibling cycle (`rev-management__commands__export_schema.md`) whose `Status: verified` and `review-0_0_7.md:69` checkbox `[x]` are already landed; the hunks are uncommitted-but-accepted prior-cycle output, not folder-pass contributions. The folder pass itself contributed zero edits per its own "Files touched: None" record. Scoping the dirty paths to the sibling cycle is deliberate — recording it here so the audit trail shows the attribution rather than mis-flagging as out-of-scope concurrent maintainer work.
2. All three Worker 2 sections (`## Fix report (Worker 2)`, `## Comment/docstring pass`, `## Changelog disposition`) open with `Filled by Worker 1 per no-source-edit cycle pattern.` verbatim (grep count: 3).
3. No GLOSSARY-only fix in scope — the `docs/GLOSSARY.md:1011` rewrite was authored under the per-file sibling cycle's Medium and is closed there; no folder-level GLOSSARY entry is warranted (Django's `find_commands` enumeration is convention-driven, not `__all__`-driven).
4. Changelog disposition cites both AGENTS.md rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") AND `docs/review/review-0_0_7.md:24` plan silence on changelog authorization for this cycle item. `git diff -- CHANGELOG.md` is empty.
5. Ruff outcomes recorded by Worker 1 match a fresh run: `uv run ruff format --check django_strawberry_framework/management/commands/` → "2 files already formatted" (with the harmless global `COM812`-vs-formatter notice); `uv run ruff check django_strawberry_framework/management/commands/` → "All checks passed!".

Spot-checks against the "What looks solid" claims:

- `django_strawberry_framework/management/commands/__init__.py` is the canonical one-line module docstring (`"""Management command implementations for django-strawberry-framework."""`) with zero imports, zero symbols, zero executable code — confirms shape #2 skip-shape framing.
- `django_strawberry_framework/management/commands/` directory listing shows exactly two source files (`__init__.py`, `export_schema.py`) plus `__pycache__/` — confirms the "exactly one source sibling" premise underpinning the "no cross-file DRY surface" rejection.
- The defer-with-trigger carry-forward from the per-file artifact's Low (b) is verbatim in the artifact's `Notes for Worker 3` block and gates folder-level DRY rework on a second management command landing — correct shape per the AGENTS.md "don't preemptively populate" rule cited in the artifact.

### DRY findings disposition

Single `None — …` bullet in the artifact's DRY analysis, justified by the one-source-sibling structure (no cross-file duplication surface to consolidate; the per-file artifact already rejected every intra-file DRY opportunity). The deferral is gated on the same explicit trigger as the per-file artifact's Low (b) ("revisit when a **second** management command lands"). Accepted as written.

### Temp test verification

None — no-source-edit cycle, no behavioural change to verify with a temp test.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` and marks the `review-0_0_7.md:70` folder-pass checkbox `[x]`.

---

## Iteration log
