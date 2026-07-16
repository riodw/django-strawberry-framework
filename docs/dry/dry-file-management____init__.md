# DRY review: `django_strawberry_framework/management/__init__.py`

Status: verified

## System trace

The target is a one-line module docstring that marks
`django_strawberry_framework.management` as a Python package. It defines no
symbols, imports, re-exports, literals, settings keys, or runtime policy.

Owned responsibility:

- satisfy Django's `management/` package convention so
  `INSTALLED_APPS` discovery can find `management/commands/*.py`;
- satisfy `D100` (module docstring) and feed `docs/TREE.md`'s module-docstring
  renderer for the `management/` folder line.

Connected behavior examined:

- `management/commands/__init__.py` — sibling marker naming the command modules
  (`export_schema`, `inspect_django_type`); still an open plan item; traced only
  as the nested discovery package Django requires under `management/`.
- `management/commands/_imports.py`, `export_schema.py`, `inspect_django_type.py`
  — own import-error translation and command behavior. Nothing in those modules
  imports or configures this `__init__`.
- Package root / `apps.py` — `django_strawberry_framework` is on
  `INSTALLED_APPS`; command discovery is directory convention, not AppConfig
  wiring or a root re-export (spec-022 Decision 1: no public `Command` export).
- Consumers and tests import leaf command modules
  (`…management.commands.export_schema`, `…_imports`, `…inspect_django_type`) or
  invoke via `call_command`. Grep finds zero
  `from django_strawberry_framework.management import …` / bare package imports
  outside import of the package object itself.
- Example markers (`examples/fakeshop/apps/{glossary,kanban,products}/management/`)
  — same Django packaging shape, each describing that app's own commands.
- `tests/management/__init__.py` — test-package shell docstring; not a production
  surface duplicate.
- Baseline
  `git diff 5fa89acb7c321c51e04b315047e68aeff59c6bb0 -- …/management/__init__.py`
  is empty; working tree matches baseline byte-for-byte.

## Verification

Searches:

- Import graph for `django_strawberry_framework.management` (no leaf-path suffix)
  — no production or test consumer binds symbols from this module.
- Package `__init__.py` inventory — this file is the thinnest marker in the
  package (1 line / 78 bytes). Contrast: eager-export packages (`auth`,
  `extensions`, …) and the soft-dep empty marker (`middleware/__init__.py`, which
  documents why it stays import-clean). Management has no optional dependency
  story and no consumer import API at this level.
- Concept search for “management namespace marker” / “Django management
  namespace for …” — phrasing recurs in fakeshop app markers and in TREE
  comments because those strings are the TREE docstring source, not a second
  policy implementation.
- Scratch import: `import django_strawberry_framework.management` exposes only
  the module docstring (no public attrs). Confirms the file carries no API.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Unify docstring text with fakeshop `*/management/__init__.py` markers.**
   Disproved: shared packaging idiom and near-parallel wording, but each string
   names a different app's command domain (framework SDL/inspect tools vs
   glossary/kanban/products fixtures). They do not change together; a shared
   constant or helper would invent a false coupling and fight TREE's
   per-module docstring convention.
2. **Re-export `Command` classes (or `_imports`) from this `__init__`.**
   Disproved: Django discovers commands by module path under
   `management/commands/`; the public contract is `manage.py <name>`, not a
   Python import from `django_strawberry_framework.management`. Adding re-exports
   would create a second public surface the package explicitly refuses
   (spec-022: no root/`management` Command export) and pull command import
   graphs into every walker that imports the package marker.
3. **Collapse `management/__init__.py` into `management/commands/__init__.py`
   (or delete one marker).** Disproved: Django requires both package directories
   with `__init__.py` for discovery. Removing either breaks the convention; they
   are not duplicate owners of one rule — they are two required namespace
   layers with distinct docstrings (parent namespace vs command implementations).
4. **Empty the file (no docstring) or treat it as dead weight.** Disproved:
   `D100` and the TREE renderer both require the module docstring; an empty file
   would fail lint and erase the folder annotation in `docs/TREE.md`.
5. **Hoist `_imports.import_or_command_error` (or other command policy) into this
   `__init__`.** Deferred to sibling file / folder items — that helper is owned
   by `management/commands/`, not by this marker. Moving it here would make the
   package marker import command plumbing and invert the discovery-only role.

No further scratch experiment required beyond the import probe: the file has no
executable body to equate across sites.

## Opportunities

None — the target is already the single, correctly thin Django management
package marker for the framework. It owns no duplicated rule, transformation,
or lifecycle. Sibling `commands/` modules and the upcoming
`management/commands/` / `management/` folder passes own any cross-command DRY
work.

## Judgment

Zero-edit. Proved empty item-scoped source diff. Ready for Worker 2.

## Implementation (Worker 1)

No tracked source edits. Item-scoped diff vs `ITEM_BASELINE`
(`5fa89acb7c321c51e04b315047e68aeff59c6bb0`) remains empty for
`django_strawberry_framework/management/__init__.py`. Artifact only.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE`
(`5fa89acb7c321c51e04b315047e68aeff59c6bb0`) is empty; `cmp` confirms the
working tree matches the baseline blob byte-for-byte for
`django_strawberry_framework/management/__init__.py`. No production edits in
this pass.

Re-traced independently:

- Target is still a one-line module docstring with no symbols, imports,
  `__all__`, or runtime policy.
- `uv run python` import of `django_strawberry_framework.management` exposes
  only the docstring (`public []`, no `__all__`, empty non-dunder `vars`).
- Production/test consumers bind leaf modules
  (`…commands.export_schema`, `…_imports`, `…inspect_django_type`) or use
  `call_command`; grep finds no `from django_strawberry_framework.management
  import …` consumer.
- Sibling `management/commands/__init__.py` remains a distinct required
  namespace layer (names the command modules). `apps.py` does not wire
  commands. Soft-dep contrast `middleware/__init__.py` documents
  import-clean optional deps; management has none.

Challenges to rejected candidates (all stand):

1. **Unify docstring text with fakeshop `*/management/__init__.py`.**
   Parallel packaging idiom only. Framework / glossary / kanban / products
   each name a different command domain; products even uses a different
   lead phrase (`Management-command namespace…`). They must not share a
   constant — TREE renders each module docstring as that folder's annotation.
2. **Re-export `Command` / `_imports` here.** Still wrong. Spec-022 Decision 1
   primarily forbids root `__all__` widening; the same discovery contract
   also forbids inventing a Python import API on this marker. Commands are
   `manage.py` surfaces, not package imports. Re-export would pull command
   import graphs into every walker that imports the package marker.
3. **Collapse parent vs `commands/` markers.** Django requires both
   importable packages; they are two namespace layers, not two owners of one
   rule.
4. **Empty the file / drop the docstring.** `D100` + TREE renderer still
   require it.
5. **Hoist `_imports.import_or_command_error` here.** Still deferred to
   `management/commands/` ownership; moving it would invert the
   discovery-only role of this marker.

Missed consolidation search: no second policy copy, no stale dual marker
contract, no consumer bypass that should move into this file, no settings /
registry / export table attached to this package. Spec-022's suggested
docstring wording differs from the shipped TREE-sourced line — documentation
drift, not duplicated responsibility. Zero-edit stands.

**Disposition:** verified. Plan item checked.
