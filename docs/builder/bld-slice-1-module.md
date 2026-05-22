# Build: Slice 1 — Module + `Command` subclass

Spec reference: `docs/spec-018-export_schema-0_0_7.md` (Slice 1 lines 55-66; Decision 1 lines 269-296; Decision 2 lines 298-365; Decision 3 lines 366-396; Decision 4 lines 398-417; Decision 5 referenced from Slice 1; Borrowing posture lines 132-192)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

The slice has near-zero DRY surface — three brand-new files, two of them empty markers — but the analysis walks the relevant prior shapes anyway so Worker 2 has the same anchors Worker 1 used.

- **Existing patterns reused.**
  - **`django_strawberry_framework/apps.py:1-11`** is the only prior management-shaped module in the package and the closest stylistic precedent for the new `Command`. It pins (a) a one-line module docstring (`D100` root-cause fix, e.g. `"""Django AppConfig — registers django-strawberry-framework with Django's app loader."""`), (b) a one-line class docstring (`D101`), (c) Django import grouped on its own line (`from django.apps import AppConfig`), (d) `name = "django_strawberry_framework"` as a class attribute. The new `Command` mirrors that shape: top-of-file module docstring, top-of-class class docstring, Django-then-third-party-then-no-first-party import order (the module has no first-party `django_strawberry_framework.*` imports), class attributes at the top of the class body, methods below.
  - **`strawberry-django` upstream at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/management/commands/export_schema.py:1-38`** is reproduced in the spec [Borrowing posture](docs/spec-018-export_schema-0_0_7.md) section (spec lines 142-181). The behavioral shape is borrowed verbatim — positional `schema` (`nargs=1`), `--path` (`nargs="?"`), `(ImportError, AttributeError) → CommandError` wrapper, `isinstance(schema_symbol, Schema)` check, `print_schema(schema_symbol)`, `pathlib.Path(path).write_text(..., encoding="utf-8")` on `--path` else `self.stdout.write(...)`. The only forced divergences are the two categories pinned in spec lines 187-191 (Borrowing posture) and lines 337-347 (Decision 2): the pydocstyle category (`D100` / `D101` / `D102` — four docstrings total) and the flake8-annotations category (`ANN001` / `ANN201` — `parser: CommandParser` plus two `-> None` returns). The `: object` narrows on `*args` / `**options` are documentation-quality only per rev4 I1 (spec line 345) — `ANN002` / `ANN003` are globally ignored at `pyproject.toml:93-94`.
  - **Top-level `__init__.py` shape at `django_strawberry_framework/__init__.py:1-4`** is the closest precedent for the new `management/__init__.py` and `management/commands/__init__.py` markers — a one-line module docstring satisfying `D100`, no imports (the new markers carry no public surface; spec Slice checklist sub-bullet rejecting the public-export per Decision 1 at spec lines 284-290).
- **New helpers justified.** None. The new module `export_schema.py` consists of exactly one `Command(BaseCommand)` subclass with two methods (`add_arguments`, `handle`); no helper extraction is justified at this size. Extracting a private helper like `_resolve_schema_symbol(dotted_path)` would (a) add a layer of indirection for a four-line body, (b) split the `(ImportError, AttributeError)` catch from its `raise CommandError(...) from e` re-raise, (c) split the `isinstance` check from its sibling `CommandError`. The two markers carry only a docstring — no helpers possible.
- **Duplication risk avoided.**
  - **Risk: a worker re-deriving the upstream body instead of copying it.** Mitigated by pinning the import block verbatim in `### Implementation steps` and copying the spec's `Method signatures` block verbatim into the artifact (below) so Worker 2 has a single source of truth in the artifact and does not have to reconcile spec-vs-implementation drift.
  - **Risk: stylistic re-litigation of the `help` string capitalization.** The upstream uses lowercase `"Export the graphql schema"`; the spec pins Title Case `"Export the GraphQL schema"` (Decision 2 spec line 302; Borrowing posture spec line 187). The plan calls out the literal string verbatim so Worker 2 does not "correct" it back to upstream casing.
  - **Risk: stylistic divergence on the `options["path"]` vs `options.get("path")` lookup.** The upstream uses `.get("path")` (spec lines 176-178 reproduce this). Pinned in `### Implementation discretion items` below — Worker 2 uses `.get("path")` to match the upstream verbatim; the spec also reads `options["schema"][0]` directly because `nargs=1` always populates the key.
  - **Risk: a worker silently adopting `...` (PEP 484 stub idiom) as the `handle` body.** Rev4 L2 already addressed this in the spec (spec lines 332, 335) by replacing the spec's pinned signatures' `...` with an explicit comment placeholder. The verbatim copy below preserves the explicit comment.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

**Working-tree note (carry-forward from pre-flight).** When Worker 0 created the build plan on 2026-05-22, `git status --short` showed only `M docs/feedback.md`. As of this planning pass, `ls` shows that `django_strawberry_framework/management/`, `django_strawberry_framework/management/commands/`, and `django_strawberry_framework/management/commands/export_schema.py` already exist on disk (plus `tests/management/__init__.py` and `tests/management/test_export_schema.py`, which belong to Slice 2 — Worker 2 does NOT touch them in this slice). Per `AGENTS.md` line 31, these are presumptively the maintainer's in-progress work and must not be auto-reverted. Worker 1 (planning) does not read the on-disk contents — planning is spec-driven, not implementation-driven. Worker 2 (build pass) reconciles the on-disk state against this plan: if the on-disk contents already match the contract pinned below verbatim, Worker 2 reports the no-op in `### Files touched` ("file already on disk in maintainer-baseline state matching the planned contract; no edit"); if the on-disk contents diverge from the contract, Worker 2 edits the file to match the contract and records the delta in `### Files touched`. Either way, the artifact's `Status: built` reflects "the contract has landed," not "Worker 2 typed every line."

1. **Create `django_strawberry_framework/management/__init__.py`** with exactly one line of content (the module docstring; `D100`-satisfying). Suggested wording (per spec Slice 1 sub-bullet at lines 66-67 and Decision 1 at spec line 275): `"""Django management entry points for django-strawberry-framework."""`. No imports, no other statements. Mirrors `django_strawberry_framework/__init__.py:1-4` shape minus the imports.

2. **Create `django_strawberry_framework/management/commands/__init__.py`** with exactly one line of content (the module docstring; `D100`-satisfying). Suggested wording (per spec Slice 1 sub-bullet at lines 66-67 and Decision 1 at spec line 276): `"""Management command implementations for django-strawberry-framework."""`. No imports, no other statements.

3. **Create `django_strawberry_framework/management/commands/export_schema.py`** matching the spec's pinned `Method signatures` code block verbatim plus the `handle` body per Decision 3 (symbol resolution), Decision 4 (SDL output), Decision 5 (errors), all reproduced verbatim from the spec below. The full pinned source for the module follows.

**Pinned imports (verbatim per spec Decision 2 lines 308-312):**

```python
import pathlib

from django.core.management.base import BaseCommand, CommandError, CommandParser
from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol
```

Note: `pathlib` is added to the upstream's import block (it is in the upstream — see spec line 143) and is needed for the `--path` branch per Decision 4 (spec lines 405-406). `CommandParser` is added relative to the upstream because of the `ANN001` annotation on `add_arguments`'s `parser: CommandParser` parameter (rev2 H1; spec line 343 verified `CommandParser` exists at `.venv/lib/python3.10/site-packages/django/core/management/base.py:49`).

**Pinned method signatures and class shape (copied verbatim from spec Decision 2 lines 308-333):**

```python
from django.core.management.base import BaseCommand, CommandError, CommandParser
from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol


class Command(BaseCommand):
    """Export the GraphQL SDL for a strawberry.Schema symbol."""

    help = "Export the GraphQL schema"

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional schema argument and the optional --path flag."""
        parser.add_argument("schema", nargs=1, type=str, help="The schema location")
        parser.add_argument(
            "--path",
            nargs="?",
            type=str,
            help="Optional path to export",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""
        # Body per Decision 3 (symbol resolution) / Decision 4 (SDL output) / Decision 5 (errors).
```

**`handle` body (composed verbatim from spec Decisions 3 / 4 / 5):** Worker 2 fills the body comment placeholder above with the contract below, derived directly from spec lines 370-374 (Decision 3), lines 402-409 (Decision 4), and the upstream behavioral shape at spec lines 163-181 (Borrowing posture). The pinned body is:

```python
        try:
            schema_symbol = import_module_symbol(
                options["schema"][0],
                default_symbol_name="schema",
            )
        except (ImportError, AttributeError) as e:
            raise CommandError(str(e)) from e

        if not isinstance(schema_symbol, Schema):
            raise CommandError("The `schema` must be an instance of strawberry.Schema")

        schema_output = print_schema(schema_symbol)
        path = options.get("path")
        if path:
            pathlib.Path(path).write_text(schema_output, encoding="utf-8")
        else:
            self.stdout.write(schema_output)
```

Body provenance, one bullet per spec citation Worker 2 should keep in view:

- `options["schema"][0]` direct subscript (not `.get`): spec line 372 and spec line 176 (upstream verbatim). `nargs=1` always populates the key with a one-element list; `.get` would obscure the contract.
- `default_symbol_name="schema"` keyword arg: spec lines 373, 379-380 (Decision 3 behavior bullets) and spec line 167 (upstream verbatim).
- `(ImportError, AttributeError)` catch with `from e` chaining and `str(e)` message: spec line 384 and spec line 169-170 (upstream verbatim). Both branches of the tuple are pinned independently by Slice 2 tests (c) and (d) per spec Slice 2 checklist.
- Non-`Schema` `CommandError` message string `"The \`schema\` must be an instance of strawberry.Schema"`: spec line 173 (upstream verbatim) and spec line 256 ([User-facing API](docs/spec-018-export_schema-0_0_7.md) Error shapes). Backticks around `schema` are kept verbatim (the upstream uses backticks; the spec pins the wording).
- `print_schema(schema_symbol)` (no kwargs): spec line 403 (Decision 4) and spec line 175 (upstream verbatim).
- `options.get("path")` (NOT `options["path"]`): spec line 404 (Decision 4) and spec line 176 (upstream verbatim). `--path` is optional and defaults to `None`; `.get` returns `None` cleanly. See `### Implementation discretion items` below for why this is pinned, not discretionary.
- `pathlib.Path(path).write_text(schema_output, encoding="utf-8")`: spec line 406 (Decision 4) and spec line 178 (upstream verbatim).
- `self.stdout.write(schema_output)` for the no-`--path` branch: spec line 408 (Decision 4) and spec line 180 (upstream verbatim). Decision 4 spec line 416 pins `self.stdout.write` (NOT `print`) so `call_command(..., stdout=StringIO())` test capture works — Slice 2 test (a) depends on this.

4. **Public-surface invariant.** Do NOT touch `django_strawberry_framework/__init__.py`. Verified at `django_strawberry_framework/__init__.py:28-37` that `__all__` does not contain `Command` and the spec [Decision 1](docs/spec-018-export_schema-0_0_7.md) at spec lines 284-290 forbids adding it. The Slice 1 checklist sub-bullet at spec line 64 also pins this. `tests/base/test_init.py` pins `__all__` (per spec [Current state](docs/spec-018-export_schema-0_0_7.md) at spec line 107); the test will continue to pass without change in this slice.

5. **No edits to `django_strawberry_framework/apps.py`.** The [`Django AppConfig`](docs/GLOSSARY.md#django-appconfig) is the shipped `0.0.7` predecessor; Decision 1 (spec lines 280-282) and the [No-goals](docs/spec-018-export_schema-0_0_7.md) at spec line 130 explicitly carry the `ready()`-body deferral from `docs/SPECS/spec-017-apps-0_0_7.md` Decision 4 forward into this card. Django's `INSTALLED_APPS`-driven `management/commands/` directory walk does not require an AppConfig hook.

6. **No edits to `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s pinned version assertion.** Per spec Slice 3 checklist at spec line 80 (joint `0.0.7` cut Decision 9) and spec [Goals](docs/spec-018-export_schema-0_0_7.md) item 6, this card does NOT bump the version unless it ships last; the version bump is deferred to whichever `0.0.7` card lands last under the joint-cut policy.

7. **No doc edits in Slice 1.** All doc updates ([`docs/GLOSSARY.md`](docs/GLOSSARY.md), [`docs/README.md`](docs/README.md), [`docs/TREE.md`](docs/TREE.md), [`KANBAN.md`](../KANBAN.md), [`CHANGELOG.md`](../CHANGELOG.md)) ship in Slice 3 per spec Slice checklist at spec lines 73-79.

### Test additions / updates

**No tests in Slice 1; tests land in Slice 2.** The Slice 1 contract is exactly three new files (one source module plus two markers); no test additions or updates ship in this slice. Slice 2 of the spec (spec checklist lines 67-72) lands `tests/management/__init__.py` and `tests/management/test_export_schema.py` (seven tests) plus the live `examples/fakeshop/tests/test_commands.py` extension. The Worker 0 build plan reserves `docs/builder/bld-slice-2-tests.md` for that cycle.

For completeness, the seven Slice 2 tests pin (per spec Slice 2 checklist sub-bullet at spec line 69) the following branches of the Slice 1 module — Worker 2 of Slice 2 will use these as the contract for the test file, not Worker 2 of Slice 1:

- (a) happy-path stdout output (pins `self.stdout.write` branch — Slice 1 step 3 body bullet 7).
- (b) happy-path `--path` file write (pins `pathlib.Path(path).write_text(..., encoding="utf-8")` branch — Slice 1 step 3 body bullet 7).
- (c) `CommandError` for unimportable module (pins the `ImportError` arm of the tuple catch — Slice 1 step 3 body bullet 3).
- (d) `CommandError` for missing attribute on a module that does import (pins the `AttributeError` arm of the tuple catch — Slice 1 step 3 body bullet 3).
- (e) `CommandError` for resolved symbol that is not a `strawberry.Schema` instance (pins the `isinstance` check + exact error string — Slice 1 step 3 body bullet 4).
- (f) `CommandError` for missing positional argument (pins `CommandParser.error()` raising `CommandError` directly on `called_from_command_line=False`; not a Slice 1 module behavior but a Django-side contract that the spec's [Decision 5](docs/spec-018-export_schema-0_0_7.md) failure mode 3 and Decision 8 explicitly anchor on — verified by spec rev4 L3 / rev5 M1 against `.venv/lib/python3.10/site-packages/django/core/management/base.py:49-78`).
- (g) default-symbol-name fallback positive test (pins the `default_symbol_name="schema"` keyword arg — Slice 1 step 3 body bullet 2).

Temp/scratch tests are not appropriate for Slice 1 (no logic shipped). Worker 3 reviews Slice 1's diff for the module shape; the seven tests above land in Slice 2 and are reviewed there.

### Implementation discretion items

Items where Worker 1 has assessed the design and decided the choice belongs to Worker 2. Architectural questions are NOT delegated here; the spec pins everything load-bearing.

- **Module docstring exact wording.** The spec suggests `"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""` (spec line 339); the Slice 1 checklist (spec line 65) also suggests that wording. Worker 2 may use the suggested wording verbatim or substitute an equivalent `D100`-satisfying one-liner that names the command's purpose (e.g. `"""Export the GraphQL SDL for a strawberry.Schema symbol via manage.py export_schema."""`). Either passes `ruff check`; either is durable across the test pin (Slice 2 does not assert the module docstring text).
- **`management/__init__.py` and `management/commands/__init__.py` docstring exact wording.** The spec Slice 1 checklist (spec line 66-67) suggests `"""Django management entry points for django-strawberry-framework."""` and `"""Management command implementations for django-strawberry-framework."""`. Worker 2 may use the suggested wording verbatim or substitute equivalent `D100`-satisfying one-liners. Same durability rationale as the module docstring.
- **Class docstring exact wording.** The spec pins one of two suggestions: `"""Export the GraphQL SDL for a strawberry.Schema symbol."""` (spec line 65 and spec line 316 in the `Method signatures` block) or "equivalent one-liner" (spec line 65). Worker 2 should use the verbatim suggested wording so the spec's `Method signatures` code block at spec lines 314-333 stays a faithful pin.
- **Method docstring exact wording.** The spec pins suggested one-liners for both methods (spec lines 60-61 in the Slice 1 checklist; spec lines 321 and 331 in the `Method signatures` block): `"""Register the positional schema argument and the optional --path flag."""` for `add_arguments` and `"""Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""` for `handle`. Worker 2 should use the verbatim suggested wording for the same `Method signatures`-block-fidelity reason.
- **`*args` / `**options` annotation shape.** Rev4 I1 (spec lines 28, 345) explicitly settles the author's call: the `: object` narrows in the pinned `Method signatures` code block are pinned for `mypy --strict`-friendliness, but `ANN002` / `ANN003` are globally ignored at `pyproject.toml:93-94`, so a bare `*args, **options` would also pass `ruff check`. Worker 2's discretion: use the pinned `: object` narrow (matches the spec's `Method signatures` block verbatim — recommended for `Method signatures`-block-fidelity) or the bare `*args, **options` (matches the upstream verbatim — also accepted by spec rev4 I1). Either passes `ruff check`. Worker 2 should pick one and apply it to both methods uniformly (i.e. not narrow one and leave the other bare).

NOT discretionary (pinned by the spec; Worker 2 must NOT vary these):

- The `help = "Export the GraphQL schema"` string (Title Case `GraphQL`; spec line 302; Slice 2 test pins this).
- The import block (six imports in the exact order shown above; spec lines 308-312).
- The `(ImportError, AttributeError)` catch tuple, `from e` chaining, `str(e)` message (spec lines 169-170 upstream verbatim).
- The non-`Schema` `CommandError` string `"The \`schema\` must be an instance of strawberry.Schema"` (spec line 173 upstream verbatim; Slice 2 test (e) pins this).
- `options["schema"][0]` direct subscript (NOT `.get`) for the positional argument (spec line 372; `nargs=1` always populates).
- `options.get("path")` for the optional flag (NOT `options["path"]`; spec line 404 and upstream verbatim at spec line 176). The `Method signatures` block at spec lines 308-333 only pins the comment placeholder, not the body — but the spec's [Decision 4](docs/spec-018-export_schema-0_0_7.md) pinned code at spec lines 402-409 pins `.get("path")` explicitly. Worker 2 uses `.get("path")`.
- The `pathlib.Path(path).write_text(..., encoding="utf-8")` call (spec line 406; UTF-8 is pinned).
- The `self.stdout.write(...)` call for the no-`--path` branch (spec line 408; NOT `print(...)`; Decision 4 spec line 416 pins this for `call_command(..., stdout=StringIO())` capture).
- The `# Body per Decision 3 ... Decision 5 (errors).` comment placeholder shown in spec line 332 is the spec's source-of-truth code block; Worker 2 replaces that comment with the actual body (above), preserving the spec's contract.

### Static inspection helper disposition

Static inspection helper skipped at planning — `export_schema.py` is a new file outside `django_strawberry_framework/optimizer/` and `django_strawberry_framework/types/` and well under 150 lines (the upstream is 38 lines; the slice's added shape is ~45 lines after docstrings and annotations land). Per `BUILD.md` "When to run the helper during build" (Worker 1 planning), neither the 150-line trigger nor the `optimizer/` / `types/` trigger fires. Worker 3 will run the helper during review per `BUILD.md` "Worker 3 must run the helper during review when the slice adds a new `.py` file of any size, unless it is a pure-class-definition module" — Worker 3 will decide at review time whether the `Command` class plus its `handle` body qualifies as pure-class-definition or carries enough logic to warrant the helper; Worker 1 makes no preemptive call here.

### Spec slice checklist (verbatim)

The spec's Slice 1 sub-bullets at `docs/spec-018-export_schema-0_0_7.md` lines 55-67, copied verbatim. Worker 1 ticks each `- [x]` during final verification as the contract lands. An unticked box at final verification is either deferred with a one-line reason under `### Spec changes made (Worker 1 only)` or the slice goes `revision-needed`.

- [x] New flat package `django_strawberry_framework/management/` with a one-line module docstring `__init__.py` (empty marker).
- [x] New flat package `django_strawberry_framework/management/commands/` with a one-line module docstring `__init__.py` (empty marker).
- [x] New module `django_strawberry_framework/management/commands/export_schema.py` housing `Command(BaseCommand)` per [Decision 2](#decision-2--command-class-shape) — `help = "Export the GraphQL schema"`, positional `schema` (single value, dotted path), optional `--path`, `handle(self, *args: object, **options: object) -> None` body (rev2 H1 — return annotation required by `ANN201`; `*args` / `**options` may stay un-narrowed because `ANN002` and `ANN003` are globally ignored at `pyproject.toml:93-94`) that (a) resolves the symbol via `strawberry.utils.importer.import_module_symbol(options["schema"][0], default_symbol_name="schema")` per [Decision 3](#decision-3--symbol-resolution-via-strawberryutilsimporterimport_module_symbol), (b) raises `CommandError` on `ImportError` / `AttributeError` per [Decision 5](#decision-5--commanderror-for-three-failure-modes), (c) raises `CommandError` when the resolved symbol is not a `strawberry.Schema` instance per [Decision 5](#decision-5--commanderror-for-three-failure-modes), (d) writes SDL via `strawberry.printer.print_schema(schema_symbol)` per [Decision 4](#decision-4--sdl-output-via-strawberryprinterprint_schema), (e) routes to `pathlib.Path(path).write_text(..., encoding="utf-8")` when `--path` is set, otherwise to `self.stdout.write(...)`.
- [x] `add_arguments` signed as `def add_arguments(self, parser: CommandParser) -> None:` (rev2 H1 — `parser: CommandParser` covers `ANN001`; `-> None` covers `ANN201`; `CommandParser` imported from `django.core.management.base`, verified to exist at `.venv/lib/python3.10/site-packages/django/core/management/base.py:49`).
- [x] One-line method docstring on `add_arguments` (required by `D102`, rev2 H1; pydocstyle convention is google per `pyproject.toml:113`). Suggested: `"""Register the positional schema argument and the optional --path flag."""`. Do NOT suppress with `# noqa: D102` — the docstring IS the root-cause fix per [`AGENTS.md`](../AGENTS.md) line 4.
- [x] One-line method docstring on `handle` (required by `D102`, rev2 H1). Suggested: `"""Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""`. Do NOT suppress with `# noqa: D102`.
- [x] Do NOT implement a settings-backed default for `schema` (per [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).
- [x] Do NOT implement `--watch`, `--indent`, `--json`, a `dump_schema` / `print_schema` alias, or a JSON-introspection mode (per [Decision 6](#decision-6--no-watch--indent--json--settings-backed-defaults--alias)).
- [x] Do NOT re-export `Command` from `django_strawberry_framework/__init__.py` (per [Decision 1](#decision-1--module-location--no-public-export)). The class is import-time plumbing Django's command-discovery resolves through `INSTALLED_APPS`; consumers never write `from django_strawberry_framework.management.commands.export_schema import Command`.
- [x] One-line module docstring on `export_schema.py` (required by `D100`); one-line class docstring on `Command` (required by `D101`). Module docstring: `"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""`. Class docstring: `"""Export the GraphQL SDL for a strawberry.Schema symbol."""` (or equivalent one-liner). Do NOT suppress with `# noqa: D100` / `# noqa: D101` — the docstrings are the root-cause fix per [`AGENTS.md`](../AGENTS.md) line 4. Same posture as [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) rev3 H1 / rev4 L3.
- [x] `management/__init__.py` and `management/commands/__init__.py` each carry a one-line module docstring (required by `D100`). Suggested: `"""Django management entry points for django-strawberry-framework."""` and `"""Management command implementations for django-strawberry-framework."""`.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/management/__init__.py` — replaced the pre-staged TODO scaffold (one-line docstring + TODO comment block from commit `d35385c`) with the final shape: a single one-line module docstring `"""Django management entry points for django-strawberry-framework."""` (verbatim from the spec Slice 1 sub-bullet at spec line 66 and Decision 1 at spec line 275). No imports, no other statements. Removed the TODO comment block per the artifact's `### Implementation steps` step 1. The diff is a delete-then-write (pre-staged scaffold → final shape), not a pure new-file creation.
- `django_strawberry_framework/management/commands/__init__.py` — replaced the pre-staged TODO scaffold with the final shape: a single one-line module docstring `"""Management command implementations for django-strawberry-framework."""` (verbatim from the spec Slice 1 sub-bullet at spec line 67 and Decision 1 at spec line 276). Same delete-then-write disposition as the parent `__init__.py`.
- `django_strawberry_framework/management/commands/export_schema.py` — replaced the pre-staged TODO scaffold (module docstring + 60-line pseudo-code comment block from commit `d35385c`) with the final implementation per the artifact's `### Implementation steps` step 3: module docstring `"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""` (spec line 339); import block exactly per the pinned six imports (spec lines 308-312, plus `import pathlib` at the top per spec line 143 upstream verbatim); `class Command(BaseCommand)` with the spec's pinned class docstring `"""Export the GraphQL SDL for a strawberry.Schema symbol."""` (spec line 316); `help = "Export the GraphQL schema"` Title Case per Decision 2 spec line 302; `add_arguments(self, parser: CommandParser) -> None` with its pinned method docstring (spec line 321) plus the two `parser.add_argument` calls verbatim per Decision 2 spec lines 322-328; `handle(self, *args: object, **options: object) -> None` with its pinned method docstring (spec line 331) and the body composed verbatim from spec Decision 3 / 4 / 5 per the artifact's "handle body" pinned block — `import_module_symbol(options["schema"][0], default_symbol_name="schema")` wrapped in `(ImportError, AttributeError)` catch re-raising `CommandError(str(e)) from e`, then the `isinstance(schema_symbol, Schema)` check raising `CommandError("The \`schema\` must be an instance of strawberry.Schema")` (backticks preserved), then `print_schema(schema_symbol)` and the `options.get("path")` split between `pathlib.Path(path).write_text(schema_output, encoding="utf-8")` and `self.stdout.write(schema_output)`. The pseudo-code TODO comment block is fully removed.

### Tests added or updated

None; tests land in Slice 2.

### Validation run

- `uv run ruff format .` — pass; 110 files left unchanged (no files reformatted by the three new edits). The pre-existing `COM812`-vs-formatter warning is unchanged from the repo baseline; not introduced by this slice.
- `uv run ruff check --fix .` — pass; `All checks passed!`. No auto-fixes applied. The docstrings (`D100` / `D101` / `D102`) and annotations (`ANN001` / `ANN201`) are root-cause-fixed in the source per [`AGENTS.md`](../AGENTS.md) line 4 — no `# noqa` suppressions added.
- `git status --short` after both ruff invocations:
  - `M django_strawberry_framework/management/__init__.py` — slice-intended (this slice's contract).
  - `M django_strawberry_framework/management/commands/__init__.py` — slice-intended (this slice's contract).
  - `M django_strawberry_framework/management/commands/export_schema.py` — slice-intended (this slice's contract).
  - `?? docs/builder/build-018-export_schema-0_0_7.md` — out-of-scope for this slice; it is the build plan Worker 0 created (artifact-list `Pre-flight: passed on 2026-05-22` preamble at line 8 of the artifact). Untracked because the build plan files are gitignored until the maintainer commits them alongside the slice. Not reverted because the maintainer/Worker 0 owns it; Worker 2 does not touch the build plan per `worker-2.md` "Scope".
  - The pre-flight-baseline `M docs/feedback.md` recorded at build-plan creation (line 8) no longer appears modified — the maintainer's working file presumably cleaned up between pre-flight and the build pass. Per `AGENTS.md` line 31, not Worker 2's concern.
- No focused `pytest` runs (Slice 1 ships no tests; Worker 1 owns the final test gate per `BUILD.md` "Coverage is the maintainer's gate, not a worker's tool"; `AGENTS.md` line 14 also pins "Do not run pytest after edits").

### Implementation notes

The artifact's `Pinned imports` / `Pinned method signatures and class shape` / `handle body` blocks plus the `### Implementation discretion items` section pinned every load-bearing line of the implementation; nothing was left to ad-hoc decision-making during the build. The notes below cover only the small choices the plan left to discretion.

- **Suggested-verbatim docstrings used at every site.** The plan offered Worker 2 latitude on the module / class / method docstrings under `### Implementation discretion items` (all four were "use the suggested wording verbatim or substitute an equivalent one-liner"). I used the suggested wording verbatim at every site so the spec's `Method signatures` code block at spec lines 314-333 stays a faithful pin to the shipped source — a future maintainer diffing the spec against the implementation should see character-for-character identity, not "equivalent rephrase." This is the choice Worker 1's discretion section explicitly preferred ("recommended for `Method signatures`-block-fidelity").
- **`*args: object, **options: object` narrows kept.** The plan and spec rev4 I1 both explicitly allow either the bare `*args, **options` (upstream-verbatim, `ANN002`/`ANN003` globally ignored) or the `: object` narrows (documentation-quality, matches the spec's `Method signatures` block verbatim). I kept the narrows for the same `Method signatures`-block-fidelity reason as the docstrings.
- **`options.get("path")` (NOT `options["path"]`).** Pinned by the plan's "NOT discretionary" list and confirmed at spec line 404 / spec line 176 (upstream verbatim). Used as pinned; recorded here only because the plan called it out as a common stylistic re-litigation point worth surfacing.
- **No `Slice 2`/`Slice 3` scope creep.** The three Slice 1 sources changed; no edits to `django_strawberry_framework/__init__.py`, `__version__`, `pyproject.toml`, `tests/`, `docs/`, `CHANGELOG.md`, or `KANBAN.md`. The artifact's spec slice checklist box "Do NOT re-export `Command` from `django_strawberry_framework/__init__.py`" was honored by leaving that file untouched.

### Notes for Worker 3

- **The diff is a delete-then-write, not a pure new-file creation.** Per the artifact's "Working-tree note" (line 27), the three Slice 1 files were pre-staged by the maintainer in commit `d35385c` as TODO scaffolds (one-line docstrings plus pseudo-code TODO comment blocks) per the `AGENTS.md` line 26 staged-but-not-implemented convention. This build pass replaced those scaffolds with the final implementation. When reviewing, expect `git diff HEAD` against each file to show TODO-comment-block removals plus the real implementation added, rather than a clean "new file added" diff. The final-state contents are the source of truth; the TODO blocks were authored-but-not-implemented placeholders by design.
- **Static inspection helper skipped at planning per `BUILD.md` Worker 1 thresholds (artifact `### Static inspection helper disposition`).** Per `BUILD.md` "Worker 3 must run the helper during review when the slice adds a new `.py` file of any size, unless it is a pure-class-definition module," Worker 3 owns the review-time decision on whether the `Command` class plus its `handle` body qualifies as a pure-class-definition module (debatable — the class has logic in `handle`) or carries enough logic to warrant the helper. Worker 1's planning artifact explicitly deferred this choice to Worker 3; recording here so Worker 3 sees it without re-reading the planning section.
- **`__all__` invariant preserved.** Verified at `django_strawberry_framework/__init__.py:28-37` that `__all__` does not contain `Command` and was not touched in this slice; the Decision 1 / Slice 1 sub-bullet contract holds. The `### Public-surface check` in Worker 3's review section should confirm `git diff -- django_strawberry_framework/__init__.py` is empty.
- **No shadow files used during this build.** Worker 2's static-helper option (per `worker-2.md` "Static helper use") was not exercised — the artifact's pinned imports / method signatures / handle body blocks were sufficient; no shadow-file inspection was needed.
- **No focused `pytest` runs.** Per `AGENTS.md` line 14 and `BUILD.md` "Coverage is the maintainer's gate, not a worker's tool"; the artifact did not require a focused test run during the build pass either.

### Notes for Worker 1 (spec reconciliation)

None.


---

## Review (Worker 3)

### Static inspection helper disposition

Worker 1 deferred the helper-run decision to Worker 3 (`### Static inspection helper disposition` in the plan; `### Notes for Worker 3` bullet 2 in the build report). `export_schema.py` is a new file with logic in `handle` (try/except, isinstance check, conditional write branching) — it is NOT a pure-class-definition module, so per `BUILD.md` "Worker 3 must run the helper during review when the slice adds a new `.py` file of any size, unless it is a pure-class-definition module," the helper was run.

Helper invocation: `uv run python scripts/review_inspect.py django_strawberry_framework/management/commands/export_schema.py --output-dir docs/shadow --stdout`.

Shadow file written: `docs/shadow/django_strawberry_framework__management__commands__export_schema.stripped.py`.

Key observations from the helper output:

- **5 imports** in the documented order — `pathlib` (standard/third-party), `BaseCommand` / `CommandError` / `CommandParser` from `django.core.management.base` (django), `Schema` from `strawberry` (strawberry), `print_schema` from `strawberry.printer` (strawberry), `import_module_symbol` from `strawberry.utils.importer` (strawberry). Matches the spec Decision 2 lines 308-312 pinned import block plus the `import pathlib` line at the top (upstream verbatim, spec line 143).
- **3 symbols** — `class Command` (lines 11-44), `add_arguments` (lines 16-24), `handle` (lines 26-44). Class+two-method shape per Decision 2.
- **0 control-flow hotspots.** `handle`'s body is ~17 source lines with one try/except, one if-not-isinstance, and one if/else — well under the default 40-line / 8-branch hotspot thresholds. No complexity attention required.
- **0 Django/ORM markers.** The command does not touch the ORM (Decision 4 / 5 / Edge cases line 580 — idempotent reads; no DB access). Expected.
- **1 call of interest** — `isinstance()` at line 36, which is the Decision 5 failure mode 2 `isinstance(schema_symbol, Schema)` guard. Pinned by spec line 173 / Decision 5 line 431; one of the load-bearing checks Slice 2 test (e) will assert.
- **0 TODO comments** — confirms the pre-staged TODO pseudo-code blocks were fully removed per the artifact's `### Files touched` bullets.
- **0 repeated string literals** — nothing to flag at the integration pass.
- **4 docstrings** — module (line 1), `Command` class (line 12), `add_arguments` (line 17), `handle` (line 27). All four `D100` / `D101` / `D102` requirements verifiably satisfied.

For the two `__init__.py` markers (`management/__init__.py`, `management/commands/__init__.py`) the helper was skipped. Reason: pure marker module, single one-line docstring, no executable logic, no class/function bodies — `BUILD.md` "Worker 3 must run the helper during review when the slice adds a new `.py` file of any size, **unless** it is a pure-class-definition module" includes the no-logic carve-out for marker files. Recording the skip explicitly per `worker-3.md` "Static helper use".

### Spec slice checklist walkthrough

Walked the Plan's `### Spec slice checklist (verbatim)` against the on-disk diff. Each sub-bullet is matched to its implementation site below; every box is addressed by the diff.

- New flat package `django_strawberry_framework/management/` with a one-line module docstring `__init__.py` (empty marker). **Addressed.** `django_strawberry_framework/management/__init__.py:1` — `"""Django management entry points for django-strawberry-framework."""`; no imports, no other content. Diff removes the pre-staged TODO comment block from commit `d35385c`.
- New flat package `django_strawberry_framework/management/commands/` with a one-line module docstring `__init__.py` (empty marker). **Addressed.** `django_strawberry_framework/management/commands/__init__.py:1` — `"""Management command implementations for django-strawberry-framework."""`; no imports. TODO block removed.
- New module `django_strawberry_framework/management/commands/export_schema.py` housing `Command(BaseCommand)` per Decision 2 — `help`, positional `schema`, optional `--path`, `handle(...) -> None` body with the five behavior sub-bullets. **Addressed.** `export_schema.py:11-44`. `help = "Export the GraphQL schema"` at line 14; positional `schema` (`nargs=1, type=str`) at line 18; optional `--path` (`nargs="?", type=str`) at lines 19-24; `handle(self, *args: object, **options: object) -> None` at line 26 with (a) `import_module_symbol(options["schema"][0], default_symbol_name="schema")` at lines 29-32, (b) `CommandError` on `(ImportError, AttributeError)` at lines 33-34, (c) `CommandError` for non-`Schema` symbol at lines 36-37, (d) `print_schema(schema_symbol)` at line 39, (e) `pathlib.Path(path).write_text(..., encoding="utf-8")` vs `self.stdout.write(...)` at lines 41-44.
- `add_arguments` signed as `def add_arguments(self, parser: CommandParser) -> None:`. **Addressed.** `export_schema.py:16`. `CommandParser` imported from `django.core.management.base` at line 5.
- One-line method docstring on `add_arguments`. **Addressed.** `export_schema.py:17` — `"""Register the positional schema argument and the optional --path flag."""` — verbatim from the spec's suggested wording.
- One-line method docstring on `handle`. **Addressed.** `export_schema.py:27` — `"""Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""` — verbatim from the spec's suggested wording.
- Do NOT implement a settings-backed default for `schema`. **Addressed.** No `django_strawberry_framework.conf` import in the module; no settings lookup anywhere in `handle`.
- Do NOT implement `--watch`, `--indent`, `--json`, a `dump_schema` / `print_schema` alias, or a JSON-introspection mode. **Addressed.** `add_arguments` registers exactly two args (`schema` positional, `--path` optional); no other flags, no alternate output modes, no alias module.
- Do NOT re-export `Command` from `django_strawberry_framework/__init__.py`. **Addressed.** `git diff -- django_strawberry_framework/__init__.py` is empty (see public-surface check below).
- One-line module docstring on `export_schema.py` (`D100`); one-line class docstring on `Command` (`D101`). **Addressed.** Module docstring at `export_schema.py:1` — `"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""` (spec line 339 verbatim). Class docstring at `export_schema.py:12` — `"""Export the GraphQL SDL for a strawberry.Schema symbol."""` (spec line 316 verbatim).
- `management/__init__.py` and `management/commands/__init__.py` each carry a one-line module docstring (`D100`). **Addressed.** Both files carry the spec-suggested wording verbatim (see first two bullets).

No silently-unaddressed sub-checks. No Medium finding under "silently-unaddressed spec slice sub-check" applies.

### Spec contract pin verification

- **Pinned imports (6 imports, exact order, spec lines 308-312 + `import pathlib` line 143).** Verified at `export_schema.py:3-8`. Order: `pathlib` (line 3), blank, `BaseCommand, CommandError, CommandParser` from `django.core.management.base` (line 5), `Schema` from `strawberry` (line 6), `print_schema` from `strawberry.printer` (line 7), `import_module_symbol` from `strawberry.utils.importer` (line 8). Match.
- **Pinned method signatures and class shape (spec Decision 2 lines 308-333).** Verified character-for-character at `export_schema.py:11-27`: class declaration, class docstring, `help` attribute, `add_arguments` signature + docstring + body, `handle` signature + docstring. The handle body fills the comment placeholder per the plan; the signature itself matches the spec's `Method signatures` block verbatim.
- **`handle` body (spec Decisions 3 / 4 / 5).** Verified at `export_schema.py:28-44`:
  - lines 29-32: `import_module_symbol(options["schema"][0], default_symbol_name="schema")` — matches spec lines 370-374.
  - lines 33-34: `except (ImportError, AttributeError) as e: raise CommandError(str(e)) from e` — matches spec line 384 / upstream lines 169-170.
  - lines 36-37: `if not isinstance(schema_symbol, Schema): raise CommandError("The \`schema\` must be an instance of strawberry.Schema")` — matches spec line 431 / upstream line 173. Backticks around `schema` preserved.
  - line 39: `schema_output = print_schema(schema_symbol)` — matches spec line 403.
  - lines 40-44: `path = options.get("path")` (not `options["path"]`), `pathlib.Path(path).write_text(schema_output, encoding="utf-8")` vs `self.stdout.write(schema_output)` — matches spec lines 404-409.
- **Class docstring (`D101`).** `"""Export the GraphQL SDL for a strawberry.Schema symbol."""` at line 12 — matches spec line 316 / spec line 65 suggestion verbatim.
- **Module docstring (`D100`).** `"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""` at line 1 — matches spec line 339 suggestion verbatim.
- **Method docstrings (`D102`).** Both methods carry the spec-suggested wording verbatim (`add_arguments` at line 17; `handle` at line 27).
- **`parser: CommandParser` (`ANN001`).** Verified at `export_schema.py:16`. `CommandParser` imported at line 5 from `django.core.management.base` — the spec-pinned source at line 343.
- **`-> None` returns (`ANN201`).** Verified at `export_schema.py:16` (add_arguments) and line 26 (handle). Both methods explicitly annotate the `None` return.
- **`help = "Export the GraphQL schema"` Title Case.** Verified at `export_schema.py:14`. Title-Case `GraphQL` per spec line 302; the Slice 2 test pin (per spec [Test plan](#test-plan)) depends on this exact string. The upstream's lowercase `"Export the graphql schema"` is correctly diverged from.
- **Non-`Schema` `CommandError` exact string `"The \`schema\` must be an instance of strawberry.Schema"`.** Verified at `export_schema.py:37`. Backticks around `schema` deliberate (spec lines 173, 431, 456). Slice 2 test (e) will pin this string.
- **`options["schema"][0]` direct subscript (NOT `.get`).** Verified at `export_schema.py:30`. `nargs=1` always populates the key; direct subscript matches upstream verbatim and spec line 372.
- **`options.get("path")` (NOT `options["path"]`).** Verified at `export_schema.py:40`. `--path` is optional; `.get` returns `None` cleanly when omitted. Matches upstream and spec line 404.
- **`pathlib.Path(path).write_text(schema_output, encoding="utf-8")`.** Verified at `export_schema.py:42`. UTF-8 pinned per spec line 406 / Edge cases line 583.
- **`self.stdout.write(schema_output)`.** Verified at `export_schema.py:44`. NOT `print(...)`; Decision 4 spec line 416 pins this so `call_command(..., stdout=StringIO())` test capture works in Slice 2 test (a).

Every spec contract point holds.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- No duplicated literals, no repeated key/tuple shapes, no near-copies of existing helpers. The `Command` subclass is the canonical management-command shape; `apps.py` is the only stylistic precedent in the package (module docstring + class docstring + simple class body) and the new module follows that shape without copying any code from it. The helper's "Repeated string literals" section reports zero. Nothing to flag for the cross-slice integration pass from this slice's surface.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty. `__all__` at `django_strawberry_framework/__init__.py:28-37` is unchanged — the existing 8-entry tuple (`BigInt`, `DjangoListField`, `DjangoOptimizerExtension`, `DjangoType`, `OptimizerHint`, `__version__`, `auto`, `finalize_django_types`) is preserved verbatim and `Command` is not added. Matches Decision 1 (spec lines 284-290) and the Slice 1 checklist sub-bullet at spec line 64. The "no new public exports" invariant of the Definition of Done holds.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Implementation is character-for-character faithful to the spec's pinned blocks.** The Plan's `Pinned imports` / `Pinned method signatures and class shape` / `handle body` triplet was the source of truth; every block lands in the diff exactly as pinned, including the deliberate divergences from the upstream (Title Case `GraphQL` in `help`, `parser: CommandParser` annotation, `-> None` returns, four added docstrings, `: object` narrows on `*args` / `**options`). Worker 2's `### Implementation notes` explicitly chose "suggested-verbatim" wording at every docstring site for `Method signatures`-block-fidelity — that choice paid off; the source matches the spec verbatim and a future maintainer diffing the spec against the implementation sees character-for-character identity.
- **`handle` body composition is precise.** Five distinct behaviors (symbol resolution, `(ImportError, AttributeError)` wrap, `isinstance` guard, SDL serialization, output branching) ship in 17 source lines with no scope creep — no defensive `finalize_django_types()` call, no broad-except wrapping, no settings lookups, no auto-resolve, no JSON branch. The TODO pseudo-code blocks from commit `d35385c` were fully removed (helper confirms 0 TODO comments).
- **Public-surface and version invariants preserved.** `__init__.py` and `__version__` untouched; `tests/base/test_init.py` will continue to pass unchanged. The joint-`0.0.7`-cut policy (Decision 9) is honored — no version bump in this slice.

### Temp test verification

No temp tests created during review; Slice 1 has no test surface (tests land in Slice 2 per the spec and the Plan's `### Test additions / updates`).

### Notes for Worker 3

- Static helper was run on `export_schema.py` and skipped on the two `__init__.py` markers per the carve-out for pure marker modules. Shadow file at `docs/shadow/django_strawberry_framework__management__commands__export_schema.stripped.py`.
- Optional smoke check passed: `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop uv run python -c "from django_strawberry_framework.management.commands.export_schema import Command; print(Command.__doc__); print('help:', Command.help)"` prints `Export the GraphQL SDL for a strawberry.Schema symbol.` and `help: Export the GraphQL schema`. Confirms the module imports cleanly, the class is constructed, the class docstring is present, and the `help` attribute is Title Case `GraphQL`. No focused `pytest` runs (Slice 1 ships no tests).

### Notes for Worker 1 (spec reconciliation)

- None. The spec's pinned blocks landed verbatim; no spec ambiguity or gap surfaced during review. The seven Slice 2 tests previewed in the Plan's `### Test additions / updates` (a)-(g) map cleanly to the shipped branches of `handle`; Slice 2 has the contract it needs.

### Review outcome

`review-accepted`. Every spec contract point holds; the diff is a faithful delete-then-write replacement of the pre-staged TODO scaffolds (commit `d35385c`) with the final implementation. No High / Medium / Low findings.

---

## Final verification (Worker 1)

### Spec status-line re-verification

Read `docs/spec-018-export_schema-0_0_7.md` lines 1-6. Status line at line 4 reads `Status: draft (revision 5, post-rev4 feedback against [docs/feedback.md](feedback.md)).` and is still accurate post-Slice 1: not every slice has shipped yet (Slices 2 and 3 are still pending), so `draft` remains the right state. Predecessors at line 6 cite `docs/SPECS/spec-017-apps-0_0_7.md` and `docs/SPECS/spec-016-list_field-0_0_7.md`; both are unchanged shipped predecessors and remain on disk. No status-line edit required.

### Spec slice checklist verification

Walked every `- [ ]` under the artifact's `### Spec slice checklist (verbatim)` against the diff and the shipped source (`django_strawberry_framework/management/__init__.py`, `django_strawberry_framework/management/commands/__init__.py`, `django_strawberry_framework/management/commands/export_schema.py`). Every sub-check's contract landed in the diff; ticked all 11 boxes `- [x]` above. Cross-references:

- `management/__init__.py` and `management/commands/__init__.py` exist with their pinned one-line docstrings — confirmed (sub-checks 1, 2, 11).
- `export_schema.py` lines 11-44 ship `Command(BaseCommand)` with the spec's pinned `help`, `add_arguments`, and `handle` shape (sub-check 3); body branches (a)-(e) all present at lines 28-44.
- `add_arguments(self, parser: CommandParser) -> None` at `export_schema.py:16` (sub-check 4); `CommandParser` imported from `django.core.management.base` at line 5.
- `add_arguments` and `handle` method docstrings at lines 17 and 27 — verbatim spec-suggested wording (sub-checks 5, 6).
- No settings lookup; no `django_strawberry_framework.conf` import in the module (sub-check 7).
- `add_arguments` registers exactly two args (`schema` positional, `--path` optional); no `--watch` / `--indent` / `--json` / alias (sub-check 8).
- `django_strawberry_framework/__init__.py` unchanged; `__all__` (lines 28-37) does not contain `Command` (sub-check 9).
- Module docstring at `export_schema.py:1` and class docstring at `export_schema.py:12` — verbatim spec-suggested wording (sub-check 10).

No silently un-ticked boxes. No deferrals required.

### DRY check across this slice and prior accepted slices

Slice 1 is the first accepted slice in this build; no prior slices exist. Within the slice, Worker 3's review section confirmed zero repeated string literals, zero duplicated helpers, and no near-copies of existing code. The `Command` subclass borrows the upstream's behavioral shape verbatim — the two forced divergence categories (pydocstyle + flake8-annotations) are gate-anchored, not stylistic, so they do not constitute duplication risk. None.

### Existing tests still pass (focused scope)

Per the task prompt's focused scope:

- `uv run pytest tests/base/test_init.py --no-cov` — pass; 4 passed in 0.05s. Pins the `__all__` invariant per Decision 1 / Slice 1 sub-bullet 9.
- `uv run pytest tests/base/ --no-cov` — pass; 19 passed in 0.05s. Covers both `test_init.py` and `test_conf.py` (the only two files in `tests/base/` per `AGENTS.md` line 6).

Both runs used `--no-cov` per `BUILD.md` "Coverage is the maintainer's gate, not a worker's tool" (the `pytest.ini` auto-applies `--cov`; `--no-cov` opts out). No coverage-shaped flags used.

### Spec reconciliation

The spec is rev5-stable for Slice 1; the implementation landed every pinned contract verbatim. No spec gap, conflict, or unstated assumption surfaced during the build or review passes (Worker 2's `### Notes for Worker 1 (spec reconciliation)` is `None`; Worker 3's is `None`). No spec edit required.

### Slice splitting check

Not applicable. Slice 1 landed as a single coherent diff (three new files; one source module plus two marker `__init__.py` files; ~45 source lines of logic). No need to split into sub-slices.

### Summary

Slice 1 ships the `export_schema` management command module and its two `__init__.py` markers under `django_strawberry_framework/management/`. The `Command(BaseCommand)` subclass at `django_strawberry_framework/management/commands/export_schema.py` matches the spec's pinned `Method signatures` block verbatim — positional `schema` (`nargs=1`), optional `--path`, `import_module_symbol` symbol resolution with `default_symbol_name="schema"`, `(ImportError, AttributeError) → CommandError` wrapping, `isinstance(schema_symbol, Schema)` guard, `print_schema(schema_symbol)` SDL output, and the `pathlib.Path(...).write_text(..., encoding="utf-8")` vs `self.stdout.write(...)` branch on `--path`. Module / class / two method docstrings (`D100` / `D101` / `D102`) and `parser: CommandParser` / `-> None` annotations (`ANN001` / `ANN201`) are all root-cause-fixed in source — no `# noqa` suppressions. `__all__` unchanged; zero new public exports. No tests in this slice (they land in Slice 2). No doc edits (they land in Slice 3). No version bump (deferred to the last `0.0.7` card under the joint-cut policy of Decision 9).

### Spec changes made (Worker 1 only)

None.
