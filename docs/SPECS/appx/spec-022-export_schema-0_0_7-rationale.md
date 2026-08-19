# Rationale: spec-022 — `export_schema` management command (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-022-export_schema-0_0_7.md`][spec-022]. The spec is the contract and states only what holds at `HEAD`; everything that explains **how it got there** lives here: five numbered revisions of pre-ship review feedback, the alternatives each of the ten Decisions rejected, the seven risks the spec used to carry, and every claim the spec once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, run late — as a residual-completion cycle rather than at the card's own pre-flight, because the original `018` cycle never performed step 7.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** Every passage below was cut from the spec by this pass; none was written from memory. What the spec carried immediately before the cut, measured 2026-08-18 at this working tree:

| Population | Measured | Instrument |
|---|---|---|
| `Revision history` entries, inline | 5 | `grep -cE '^\- \*\*Revision [0-9]+\*\*'` |
| `Justification:` / `Justification for shape:` blocks at line start | 11 | `grep -c '^Justification'` |
| `Justification:` occurrences **anywhere**, line-start blocks included | 17 | `grep -oE 'Justification[a-z ]*:' \| wc -l` |
| `Alternatives considered (and rejected):` lists | 10 (one under every Decision) | `grep -oE 'Alternatives considered' \| wc -l` |
| `## Risks and open questions` bullets | 7 | section-scoped `grep -c '^- \*\*'` |
| `(revN Xn)` attribution parentheticals | 40 | `grep -oE '\(rev[0-9]+ [A-Z][0-9]+' \| wc -l` |
| bare `rev[0-9]` token occurrences | 148 | `grep -oE 'rev[0-9]' \| wc -l` |

**The 11-vs-17 gap is the load-bearing correction to the incoming catalog.** The build plan's F8 recorded the `^Justification` count of **11** and stopped there. Six further `Justification:` clauses sit mid-bullet, invisible to a line-anchored grep: three in `## Borrowing posture`'s "From `strawberry-django`" list, one in the Slice 3 checklist's "No edits to `README.md` / `GOAL.md` / `TODAY.md`" bullet, and three in `## Doc updates`' parallel no-edit bullets (`README.md`, `GOAL.md`, `TODAY.md`). A population is not its grep vocabulary; all 17 were resolved.

**Measured byte counts, `wc -c` at this working tree:**

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-022-export_schema-0_0_7.md` | 139,523 | 84,446 |
| `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md` | 0 (did not exist) | 74,218 |

**The spec's change is a NET -55,077 bytes, and this file is larger than that figure.** Net is the only honest word for it: one pass both cut the deliberative layer and added contract text the spec had never carried — [Decision 5][spec-022-d5]'s eight failure shapes, [Decision 4][spec-022-d4]'s byte-identity contract, [Decision 3][spec-022-d3]'s shared-helper description, and a `## Test plan` rewritten against three test modules instead of two. The bytes actually cut therefore exceed the net figure by however much was added, and a single `wc -c` pair cannot separate the two halves. Anyone quoting the net figure as "what the move removed" is over-reading it.

This file exceeds the net figure for a second, independent reason: a substantial part of it is **new material this pass produced rather than text lifted out of the spec** — every per-Decision `Changes since ship` record, the whole of `## Claims the spec may no longer make`, and `## Verified against the shipped code`. None of that existed anywhere before; the original cycle never wrote a change record because it never ran this pass. What *was* lifted is smaller than it looks, because the 40 `(revN Xn)` attributions collapse to one mention per round rather than one per touched sentence, and because the passages the shipped code falsifies were **deleted** rather than moved, per [`worker-1.md`][worker-1] `### Performing the rationale move` rule 2 — with each claim recorded under `## Claims the spec may no longer make` so a reader can still see it was once asserted.

The byte figures above were produced by writing these paragraphs with fixed-width placeholders, running `wc -c` on both files, then substituting equal-width digits, so the substitution cannot move the number it reports. They are the **After** state as of the last edit either file has received, re-measured whenever one of them moves; several passes of this round have written to both, so any earlier reading in the round's own artifacts is superseded rather than merely restated.

`HEAD` at the time of the pass is `51eb47ba`. The package is at `0.0.14`; this card shipped at `0.0.7` on 2026-05-27 (`CHANGELOG.md #"## [0.0.7] - 2026-05-27"`).

**The card shipped as `018`, not `022`.** The spec was authored as `docs/spec-018-export_schema-0_0_7.md` and its build plan as `docs/builder/build-018-export_schema-0_0_7.md`; the build finished in `d780726f` ("Finish docs/builder/build-018-export_schema-0_0_7.md", 2026-05-22). The 2026-07-30 board renumber moved the card from `018` to `022` and renamed the spec. `CHANGELOG.md`'s `[0.0.7] ### Changed` tracking labels still read `018-schema_export_management_command-0.0.7`, and the spec itself carried four `WIP-ALPHA-018-0.0.7` references until this pass. Both numbers name one card; do not chase `git log` for "spec-022".

**The spec's own sibling references were pre-renumber too.** Until this pass the spec used reference ids `[spec-016]` and `[spec-017]` (40 occurrences across seven distinct ids) whose definitions already pointed at the post-renumber filenames `spec-020-list_field-0_0_7.md` and `spec-021-apps-0_0_7.md`. Nothing was broken — the definitions resolved — so the residue was uniformly rather than divergently stale. This pass renamed every id to `spec-020` / `spec-021` and disk-exists-checked each rewritten path.

**Moved** — cut from the spec by this pass, and now only here:

- the whole `Revision history (kept inline so the spec is self-contained)` block, all five revisions with their H / M / L / I sub-items;
- every `(revN Hx)` / `(revN Mx)` / `(revN Lx)` / `(revN Ix)` attribution parenthetical in the spec body — the change each one records is now in this file under the decision it touched;
- all 17 `Justification:` / `Justification for shape:` passages: the 11 line-start blocks under Decisions 1-10 (`Justification for shape:` under Decision 2) and the six inline clauses named above;
- the `Alternatives considered (and rejected):` list under every one of the ten Decisions;
- the whole seven-bullet `## Risks and open questions` section;
- `## Problem statement`'s reference-package line-count comparison and its "asymmetry is small but real" migration-story argument;
- `## Borrowing posture`'s "two categories of forced divergence" enumeration and the `graphene-django` non-borrow ledger's per-item reasoning;
- Decision 2's provenance list for each docstring and annotation rule, and its `Deliberately NOT declared` weighing;
- `## User-facing API`'s rev2 M2 note explaining why the non-`Schema` example uses `config.urls:urlpatterns`;
- `## Implementation plan`'s per-slice line-delta estimates and their revision-by-revision adjustments;
- `## Test plan`'s `Negative-shape test (none in 0.0.7)` bullet, which authored no test and existed only to explain the absence.

**Reconciled in place** — the contract sentence stays in the spec and only its chronology or its falsified half was cut:

- **The `--path` fixture-cleanup contract.** *Why* `monkeypatch.setitem(sys.modules, ...)` is required — a bare assignment leaves the synthesized `test_module` in the import cache and makes the suite order-dependent — changes how a test is written, so it stays in the spec under [`worker-1.md`][worker-1]'s implementation-relevant carve-out. The "rev3 L4 surfaced this" framing is gone.
- **Why `self.stdout.write` rather than `print(...)`.** `call_command(..., stdout=captured)` redirects `self.stdout` and not `sys.stdout`; a builder who does not read that writes the untestable form. Stays.
- **Why `call_command` and never a direct `Command().handle(...)`.** The mechanism (`CommandParser.error()` raising `CommandError` directly on the `called_from_command_line=False` branch) is what makes two of the command's eight failure shapes reachable at all. Stays; the four-revision chronology of how that sentence reached its current wording is here.
- **Why the SDL bytes must not be newline-translated.** Django's `OutputWrapper` defaults `ending="\n"` and `Path.write_text` defaults to platform newline translation; both are suppressed deliberately, and a maintainer who deletes either breaks the byte-identity contract. Stays.

## Entries keyed to the spec

Every entry names the spec decision or section it belongs to by heading and anchor. An entry naming no decision cannot be looked up.

### The `Status:` line

The spec read `Status: draft (revision 5, post-rev4 feedback).` from its authoring until this pass — on a card that shipped in `0.0.7` on 2026-05-27, whose spec has been archived under `docs/SPECS/` since, and whose `KANBAN.md` card has read `DONE-022-0.0.7` since the 2026-07-30 renumber. Three independent facts contradicted the line and none of them updated it, because nothing in the original cycle owned the header after merge. The line now states the shipped-and-archived state; [`worker-1.md`][worker-1] `## Spec status-line re-verification (every Worker 1 spawn)` is the standing guard against the recurrence.

### `Revision history`, revisions 1-5

The spec carried this block inline under the banner "kept inline so the spec is self-contained". It is reproduced here in full because it is the record of five review rounds, and deleted from the spec because a contract does not narrate its own history.

**Revision 1 — initial draft.** Pinned: the module location (`django_strawberry_framework/management/commands/export_schema.py` with `__init__.py` markers at `management/` and `management/commands/`); the command class shape (`Command(BaseCommand)`, `help = "Export the GraphQL schema"`, positional `schema` dotted path, optional `--path`); symbol resolution via `strawberry.utils.importer.import_module_symbol(..., default_symbol_name="schema")`; SDL output via `strawberry.printer.print_schema`; `CommandError` for three failure modes (unimportable dotted path, resolved symbol is not a `strawberry.Schema`, missing positional argument); test placement at `tests/management/test_export_schema.py` with a sibling `tests/management/__init__.py`; live fakeshop coverage in `examples/fakeshop/tests/test_commands.py` rather than `examples/fakeshop/test_query/`; `call_command`-only tests; the deliberate omissions of JSON output, `--watch`, `--indent`, settings-backed defaults, a `dump_schema` alias, and `default_auto_field`; the joint-`0.0.7` cut policy; zero new public exports; and the doc-updates list across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md`.

**Revision 2 (post-rev1 review)** — one high, two medium, one low:

1. **H1 — the ruff gates.** Rev1's [Decision 2][spec-022-d2], Slice 1 checklist, and Definition of done required only module + class docstrings and showed unannotated public methods (`def add_arguments(self, parser):`, `def handle(self, *args, **options):`). Verified against `pyproject.toml #"[tool.ruff.lint]"`: `select` carries both `ANN` and `D`, and `[tool.ruff.lint.per-file-ignores]` covers only `__init__.py`, `tests/**`, `examples/**`, `**/migrations/*.py`, `**/views.py`, `**/urls.py`, and `**/admin.py` — there is no `django_strawberry_framework/**` ignore for `D102`, `ANN001`, or `ANN201`. The rev1 shape would have failed `uv run ruff check --fix .`. Rev1's `## Edge cases and constraints` also claimed "`D102` is in the per-file-ignores for `django_strawberry_framework/**`" — verified false; no such ignore exists. Fixed by pinning the root-cause shape (method docstrings, `parser: CommandParser`, `-> None` on both methods) rather than `# noqa` suppressions, which [`AGENTS.md`][agents] forbids.
2. **M1 — the test count.** Rev1's `## Test plan` listed five tests while the Slice 2 checklist named "the three failure modes", [Decision 5][spec-022-d5] listed the missing-positional argument as failure mode 3, and the `CHANGELOG.md` wording named it too. Fixed by bumping to **seven**: adding an explicit missing-positional test and splitting the single "unimportable" test into `ImportError` and `AttributeError` halves so both branches of the `(ImportError, AttributeError)` catch are pinned. The `## Implementation plan` Slice 2 row went `5` → `7` tests and `+120` → `+150` lines.
3. **M2 — the non-`Schema` example was not a non-`Schema` example.** Rev1's `## User-facing API` "Error shapes" block used `config.urls` as the selector that should fail the isinstance check. Verified at `examples/fakeshop/config/urls.py #"from config.schema import schema"` that `config/urls.py` declares `from config.schema import schema`, so `import_module_symbol("config.urls", default_symbol_name="schema")` resolves the real `strawberry.Schema` and **succeeds**. The rev1 `## Test plan` had the parallel ambiguity: `test_module.not_a_schema` reads as "import the module `test_module.not_a_schema`, then take its `schema` attribute", not "import `test_module` and read `not_a_schema`". Fixed by switching the doc example to `config.urls:urlpatterns` (verified a list at `examples/fakeshop/config/urls.py #"urlpatterns = ["`) and every package-internal test selector to the explicit `:symbol` form.
4. **L1 — a `docs/TREE.md` sentence that would contradict itself.** The prose at `docs/TREE.md` #"Every other module shown in the target package layout below" listed "and the management command" among the modules "not on disk yet". After Slice 3 it is on disk. Fixed by adding the surgical fragment removal to the `docs/TREE.md` doc-update item.

**Revision 3 (post-rev2 review)** — one medium, four low:

1. **M1 — rev2 L1 propagated everywhere except the section a worker actually follows.** The `docs/TREE.md` fragment removal reached the `Revision history` entry, the Slice 3 checklist sub-bullet (c), and DoD item 9, but not the dedicated `## Doc updates` → `docs/TREE.md` bullet, which is the implementer-facing list Worker 2 walks top-down. Fixed by appending the third concrete action there.
2. **L1 — `## Goals` item 3 kept rev1's "four contracts" framing** after rev2 M1 bumped the test plan to seven. Fixed by naming the seven by group (2 happy + 4 failure-mode + 1 fallback).
3. **L2 — `## Borrowing posture` kept rev1's "two forced divergences / we add one of each"** wording after rev2 H1 added method docstrings and annotations. Read in isolation it would invite a maintainer to delete them as stylistic. Fixed by reframing as **two categories** of forced divergence (pydocstyle `D100`/`D101`/`D102`; flake8-annotations `ANN001`/`ANN201`), and [Decision 2][spec-022-d2]'s trailing "four forced divergences" claim — which over-counted by treating each per-rule line as its own divergence — was collapsed to match.
4. **L3 — [Decision 5][spec-022-d5]'s opening sentence contradicted its own body.** It read "`handle()` raises Django's `CommandError` … in three shapes" while failure mode 3's body correctly explained that argparse intercepts the missing-positional case before `handle()` runs. Fixed by rephrasing the opening to "the command surfaces `CommandError`" and splitting the pre-`handle()` case out explicitly.
5. **L4 — the seven tests were order-dependent.** Rev2 named `sys.modules["test_module"]` as the fixture home but specified no cleanup, so a bare assignment leaves the module cached and the next test sees the previous test's `schema` attribute. Fixed by pinning `monkeypatch.setitem(sys.modules, "test_module", module)`. This contract survives in the spec; it is implementation-relevant.

**Revision 4 (post-rev3 review)** — one medium, four low, one informational:

1. **M1 — the live test asserted a GraphQL type that does not exist.** Rev1-rev3 pinned the SDL assertion as `"type Branch"`. Verified at `examples/fakeshop/apps/library/schema.py::BranchType` that the class is `class BranchType(DjangoType):` and Strawberry emits the class name unchanged, so the SDL contains `type BranchType {`. The bare substring would have passed by prefix coincidence while telling every reader that a type named `Branch` exists. Fixed at both sites (Slice 2 checklist, `## Test plan`).
2. **L1 — a header promising a test the body declined to author.** `## Test plan` carried `Negative-shape test (one):` above a bullet whose body said the test was `INTENTIONALLY OMITTED for 0.0.7`. Fixed by renaming the header to `(none in 0.0.7)`. This pass deleted the bullet outright: a section that authors nothing is deliberation, and its content is preserved below under `## Test plan`.
3. **L2 — the `Method signatures` block showed `handle` with a stub-file body.** Rev2 H1's code block ended `handle` with `...`, the `.pyi` idiom for "body intentionally elided"; a reader skimming the most-scanned artifact in the spec could ship a `Command` whose `handle` does nothing. Fixed by replacing `...` with a comment pointing at Decisions 3 / 4 / 5.
4. **L3 — the missing-positional mechanism was described as a code path that does not exist.** Rev1-rev3 said "Django wraps argparse's `SystemExit(2)` into `CommandError` only when invoked via `call_command(...)`". Verified against `.venv/lib/python3.10/site-packages/django/core/management/base.py::CommandParser` that `CommandParser.error()` raises `CommandError` **directly** when `self.called_from_command_line` is False, and that the `super().error(message)` → `SystemExit(2)` branch is taken only from a real shell invocation. The behavior the test asserts was always right; the stated mechanism was not, and a worker searching Django's source for a `SystemExit` → `CommandError` conversion would never find one.
5. **L4 — DoD items 8 and 13 disagreed about who enforces coverage.** Item 8 named the 100% gate as a card-complete condition; item 13 disclaimed that the worker enforces it. Settled in favor of item 13's posture (CI's gate, not the worker's) with a clarifying clause on item 8.
6. **I1 — author's call on the `: object` narrows.** Rev3 L2's "two categories of forced divergence" framing is about gate-forced deltas, and `*args: object, **options: object` is not gate-forced: `ANN002` / `ANN003` are globally ignored at `pyproject.toml #"ANN002"`, so the upstream's bare `*args, **options` would also pass. Settled: keep the narrows with an explicit one-sentence note that they are documentation-quality (`mypy --strict`-friendliness) and deleting them is acceptable — the lowest-edit option, and it preserves the two-category framing for the deltas that really are forced.

**Revision 5 (post-rev4 review)** — one medium, one low:

1. **M1 — rev4 L3's mechanism correction skipped two parallel sites.** It landed on [Decision 5][spec-022-d5] failure mode 3 and the `## Test plan` test (f) paragraph but missed [Decision 8][spec-022-d8]'s bullet — which is the load-bearing justification for the `call_command`-only rule, so a worker reading it for context would internalize the mechanism that [Decision 5][spec-022-d5] had just corrected — and `## Risks and open questions` #3, whose title and body both asserted a wrapping that does not exist. Fixed at both. **This is the fourth instance of one pattern in five revisions**: rev2 L1, rev3 M1, rev3 L2, and rev5 M1 are all a wording fix landing at the primary site and skipping parallel references. It is why this pass's own reconciliation swept `## Slice checklist`, every Decision, `## Edge cases and constraints`, `## Test plan`, `## Implementation plan`, `## Doc updates`, `## Goals`, `## Non-goals`, `## Borrowing posture`, and `## Definition of done` per finding rather than per site.
2. **L1 — a documented signature that did not match the source.** `## Risks` #1 gave `import_module_symbol`'s signature as `(name: str, *, default_symbol_name: str | None = None) -> Any`. Verified at `.venv/lib/python3.10/site-packages/strawberry/utils/importer.py::import_module_symbol`: the first parameter is `selector`, `default_symbol_name` is positional-or-keyword with no `*` separator, and the return type is `object`. None of the three affects implementation, but the `## Risks` section's job is to anchor future-maintenance assumptions.

### [Decision 1 — Module location & no public export][spec-022-d1]

**Justification, moved.** Django's `manage.py` walks `<app>.management.commands.*` for every `<app>` in `INSTALLED_APPS`, so both `management` and `management.commands` must be importable packages — the `__init__.py` files are not optional. `docs/TREE.md`'s target layout already reserved `management/` with the `[alpha]` tag, and Slice 3 removed it. On the public-export half: Django's discovery resolves the command through its dotted module path, so consumers never write `from django_strawberry_framework.management.commands.export_schema import Command`; adding a name to `__all__` for something nobody imports is noise-only API widening; and the posture is symmetric with [`spec-021`][spec-021]'s [Decision 3][spec-021-decision-3--no-public-export] and with strawberry-django, which does not re-export its `Command` either.

**Alternatives rejected:**

- **`django_strawberry_framework/commands.py`, a flat module.** Lost: Django's discovery walks `management/commands/`, not arbitrary module names. A flat `commands.py` would never be found. The convention is load-bearing, not cosmetic.
- **`django_strawberry_framework/cli.py`, a Click-based standalone CLI.** Lost: `manage.py` is the canonical entry point for Django commands; a parallel CLI doubles the surface and forces consumers to learn a second convention.
- **Re-export `Command` from `__init__.py` for testing convenience.** Lost: tests resolve the class through `call_command` per [Decision 8][spec-022-d8]; the re-export would invite exactly the testing pattern that Decision forbids.

**Changes since ship:** none to this Decision's contract. `management/commands/__init__.py`'s docstring now names both shipped commands (`export_schema` and `inspect_django_type`) rather than the single-command wording the spec suggested — the spec offered that text as a suggestion, not a pin, and the second command landed under `DONE-029-0.0.9`.

### [Decision 2 — `Command` class shape][spec-022-d2]

**`Justification for shape:`, moved.** Two attributes and one method is the entire surface strawberry-django ships behaviorally, and the card's job was parity. Every attribute the spec adds is one the test plan has to pin; every attribute that does not ship is one the spec does not have to defend.

**Documentation and annotation rule provenance, moved.** [Decision 2][spec-022-d2] names the five ruff gates that apply and says the `: object` narrows on `*args` / `**options` stay; the derivation behind both statements is here. `ANN002` / `ANN003` / `ANN401` / `D107` / `D417` are globally ignored at `pyproject.toml #"ANN002"`, which is *why* the narrows are documentation-quality rather than gate-forced — deleting them to match the upstream's bare form would have no ruff impact (rev4 I1). The `ANN001` annotation's type was verified to exist at `.venv/lib/python3.10/site-packages/django/core/management/base.py::CommandParser` before the Decision pinned it.

**`Deliberately NOT declared`, moved.** No `requires_system_checks` override — the default `("__all__",)` runs Django's system checks before `handle()`, which is fine, and a future card needing a checks-free mode can override then. No `requires_migrations_checks` override — the command does not touch the database, so the default `False` is correct. No `stealth_options` — every option the command takes is documented.

**Alternatives rejected:**

- **`help = "Export the graphql schema"`, lowercase and upstream-verbatim.** Lost: the repo's prose Title-Cases `GraphQL`, the divergence is one line, and the test plan pins the string so the choice is durable.
- **A named `--schema` flag instead of the positional argument.** Lost: strawberry-django's shape is positional, migrants expect positional, and argparse's error message for a missing positional argument is clearer than for a missing named one.
- **`nargs=None` on the positional `schema` (a scalar rather than a one-element list).** Lost at authoring time on the grounds that "the upstream uses `nargs=1` and reads `options["schema"][0]`; we keep that shape so the test can verify the upstream-shape resolution". **This rejection has since lost.** Commit `9e11eb30` (2026-05-22) dropped `nargs` from the positional argument and replaced `options["schema"][0]` with a direct `options["schema"]` read — that is, it shipped the rejected alternative. The reason the original argument failed is that upstream-shape fidelity was never the contract worth keeping: the consumer-visible invocation is identical either way (`manage.py export_schema config.schema`), and `nargs=1`'s always-a-list semantics buy nothing but an index. `CHANGELOG.md`'s `[0.0.7] ### Changed` publishes the flip. The spec no longer argues for the shape it does not ship.

**Changes since ship:**

- `9e11eb30` (2026-05-22) dropped `nargs=1` from `schema` and `nargs="?"` from `--path`. The `--path` half is a behavior change, not a refactor: `nargs="?"` silently accepted a bare `--path` with no following value and set `options["path"]` to `None`, indistinguishable from omitting the flag. Without `nargs`, argparse raises at parse time. Both halves are published in `CHANGELOG.md`'s `[0.0.7] ### Changed` as post-ship polish.
- `f6238256` (2026-05-22) rewrote `--path`'s `help` text from the upstream's `"Optional path to export"` to `"Write UTF-8 SDL to this file, overwriting it without prompting"`, making the destructive-overwrite contract visible at `manage.py export_schema --help`. `tests/management/test_export_schema.py::test_export_schema_path_help_documents_destructive_utf8_write` pins the exact string, so the help text is now a contract rather than prose.
- `handle`'s docstring grew from the spec's suggested one-liner into a multi-line Google-style docstring enumerating the three output branches. The spec's "one-line method docstring on `handle`" pin is superseded; `D102` is satisfied by any docstring, and the branch inventory is worth more than brevity here.

### [Decision 3 — Symbol resolution through the shared `_imports` command helper][spec-022-d3]

The heading was `Decision 3 — Symbol resolution via strawberry.utils.importer.import_module_symbol` until this pass. It was renamed because the command no longer calls that function: a reader grepping `export_schema.py` for `import_module_symbol` finds nothing. The upstream importer still performs the resolution, one level down.

**Justification, moved.** Reusing the upstream importer keeps the command body trivial; Strawberry already documents the `module.path:symbol_name` shape and migrants know it. The `default_symbol_name="schema"` fallback matches the conventional layout where `config/schema.py` exposes a top-level `schema = strawberry.Schema(...)`. A hand-rolled dotted-path parser would have to handle the same edge cases for no benefit.

**The no-auto-`finalize_django_types()` argument, kept in the spec** — it is implementation-relevant, and a builder who does not read it adds the call. Only its cross-spec chronology moved here: the spec used to close the paragraph by asserting that "the same anti-pattern is pinned in `spec-021` Decision 4 for `AppConfig.ready()`". That cross-reference no longer describes anything true (see `## Claims the spec may no longer make`), and the argument stands on its own without it.

**Alternatives rejected:**

- **Hand-roll dotted-path resolution with `importlib.import_module` + `getattr`.** Lost: the upstream importer already handles `module.path:symbol_name`, and rewriting it would force the test plan to re-pin the edge cases the upstream's own tests cover. **Still correct as written, and it is worth being precise about why** — the shipped `_imports.py` does add pre-import validation of the *selector's shape* (see below), which reads at a glance like the hand-rolling this bullet rejected. It is not: resolution itself is delegated unchanged to `import_module_symbol`, and the validation exists to replace an unrelated downstream exception with an attributable message.
- **Use `django.utils.module_loading.import_string`.** Lost: Django's helper does not understand the `module.path:symbol_name` shape, so using it would diverge from strawberry-django's contract and force consumers to learn different syntax. Note that `_imports.py` now offers `import_string_or_command_error` alongside — for the *other* command, `inspect_django_type`, whose positional argument is a Django dotted object path. The two coexist because they resolve different input languages, which is the distinction this rejection drew.
- **Call `finalize_django_types()` defensively in `handle()` before resolving.** Lost: it would either be a no-op (the consumer's module chain already ran it) or would finalize an empty registry (if the consumer's schema module is the first thing to import the `DjangoType` modules). Neither shape is useful.

**Changes since ship:**

- `79e2d117` (2026-07-11) extracted the `try` / `except (ImportError, AttributeError)` wrapper out of `handle()` into `django_strawberry_framework/management/commands/_imports.py` so `inspect_django_type` (card `DONE-029-0.0.9`) could share the identical translation. **The trigger was a second consumer, not a speculative abstraction** — which is the direction [`docs/builder/BUILD.md`][build]'s DRY-first rule mandates, and the reason the extraction is recorded here rather than treated as drift.
- `61f6726c` (2026-07-13) added `_validate_absolute_module_path`, which rejects two selector shapes before the importer runs: an empty module path (`""` and `":schema"`) and a relative module path (a leading `.`). Both produce their own `CommandError` naming the offending value and the reason. Without them, `""` reaches `importlib` and surfaces as an unrelated internal error, and `.config.schema` surfaces as an attempted relative import with no package context — neither message tells the operator what they typed wrong.
- The helper module now carries three public functions (`import_or_command_error`, `import_module_symbol_or_command_error`, `import_string_or_command_error`) plus the private validator, pinned by 15 test functions / 19 collected items in `tests/management/test_imports.py`.

### [Decision 4 — SDL output via `strawberry.printer.print_schema`][spec-022-d4]

**Justification, moved.** `print_schema` is Strawberry's canonical SDL serializer and handles directives, custom scalars, federation extensions, descriptions, and deprecation reasons; re-implementing it would re-walk the type graph for nothing. SDL is the Strawberry-native serialization, and consumers needing JSON pipe through downstream tools — `strawberry export-schema` takes the same posture. UTF-8 on the file write matches the upstream and avoids locale surprises.

**Why `self.stdout.write` and not `print(...)`, kept in the spec.** `call_command(..., stdout=captured)` redirects `self.stdout` but not `sys.stdout`, so `print(...)` would be uncapturable without monkey-patching. That changes how the code is written and stays.

**Alternatives rejected:**

- **A JSON introspection mode behind `--json`.** Lost: graphene-django's JSON-by-default surface is a historical artifact of older codegen tools. Modern tools prefer SDL or accept both, and the flag would double the test surface for no current consumer.
- **Pretty-printed SDL behind `--indent`.** Lost: SDL is whitespace-agnostic and formatting is a downstream concern (`prettier --parser graphql`).
- **`print(schema_output)` instead of `self.stdout.write`.** Lost for the capture reason above.

**Changes since ship — the output contract is now strictly stronger than what shipped:**

- `f6238256` (2026-05-22) wrapped the file write in `except OSError` → `CommandError` and added a `self.style.SUCCESS(f"Wrote schema to {path}")` line after a successful write. Before it, a missing parent directory or a permission denial produced a raw traceback for what is a user-input error, while the schema-resolution half of the same command already translated cleanly; and a successful write printed nothing at all.
- `f274b2a4` (2026-05-26) split the `path is None` branch from the `not path` branch and added the empty-string rejection. The two cases had been conflated by a single `if path:`, so `--path ""` silently fell through to stdout instead of failing.
- `7f04c5b2` (2026-07-15) did two things. It widened the `--path` rejection from empty-string to empty-**or-whitespace** via `.strip()`. And it added `ending=""` to the stdout write: Django's `OutputWrapper` defaults `ending="\n"`, which made stdout diverge from the `--path` file by exactly one byte and broke `manage.py export_schema … > out.graphql` versus `--path out.graphql` diffs.
- `fd3825a2` (2026-08-16) added `newline=""` to `write_text`, so a platform with non-LF native newlines cannot translate the SDL bytes, and widened the write-failure catch from `OSError` to `(OSError, ValueError)` — a path `pathlib` itself rejects (an embedded null byte) raises `ValueError`, which is the same class of user-input error and should report the same way.

Together these four commits produce the three-way byte-identity contract the spec now states: `stdout` output, the `--path` file's bytes, and `print_schema(schema)`'s return value are identical. `tests/management/test_export_schema.py::test_export_schema_stdout_matches_path_file_and_print_schema` asserts all three in one test, and `::test_export_schema_file_write_disables_newline_translation` pins the `newline=""` kwarg at the `write_text` call.

**A claim this Decision may no longer make.** The spec's `## Edge cases and constraints` carried, until this pass, the bullet: "`self.stdout.write(schema_output)` appends a trailing newline by default; the test plan accounts for the newline in the captured-string assertions." That is now the opposite of the contract — the trailing newline is suppressed precisely so it cannot appear. Deleted rather than moved, and recorded below.

**Why the Decision now marks the two suppressions' scope.** The Decision's `ending=""` bullet is framed on the shell-redirect form and the `newline=""` bullet immediately below it on the file form; read together and with nothing marking the change of scope, they read as one cross-platform guarantee about `… > out.graphql` versus `--path out.graphql`, which is not what the command offers. `ending=""` only removes an appended byte from the string handed to `self.stdout`; the interpreter's own `sys.stdout` newline translation still applies to whatever a shell then redirects, so the redirect form matches the `--path` file only where the native line separator is LF. The Decision now states that scope explicitly and carries the derived-doc obligation with it.

**Alternative rejected:** leave the two bullets unqualified and treat a cross-platform over-reading as a one-off to be corrected wherever it appears. Lost: this paragraph is the source text every derived doc quotes, so the correction cost recurs once per derived doc while the scope sentence is written once. A second consideration weighed and set aside: stating the scope adds a sentence about a platform the project's own CI does not run, which is exactly the condition under which an unqualified claim survives unchallenged.

### [Decision 5 — `CommandError` is the command's only failure surface][spec-022-d5]

The heading was `Decision 5 — CommandError for three failure modes` until this pass. **The title was as falsified as the body**, and because it is also the anchor every cross-reference in the spec resolves through, renaming it meant sweeping `#decision-5--commanderror-for-three-failure-modes` across the spec, this file, and the repo. (A repo-wide grep found the anchor cited nowhere outside spec-022 and the round's own build plan.)

**Justification, moved.** `CommandError` is Django's documented escape hatch for "the command cannot proceed and it is the user's fault, not a bug"; `manage.py` prints the message and exits non-zero, which is what CI tooling needs, and both reference packages use it. `ConfigurationError` is reserved for `DjangoType` / `Meta` validation at class-definition and finalize time; using it for runtime command failures would muddy the hierarchy. A custom `ExportSchemaError` would force every test to import it and buy nothing.

**Alternatives rejected:**

- **Catch `Exception` and wrap it.** Lost: a broad except masks real bugs — a `KeyError` inside the consumer's `Schema(...)` constructor would surface as a confusing `CommandError`. The narrow catch matches the upstream and matches `import_module_symbol`'s actual failure modes. **This rejection is still live and load-bearing at `HEAD`**, where the write-failure catch is `(OSError, ValueError)` rather than `Exception` for the same reason, and `tests/management/test_imports.py::test_import_or_command_error_does_not_swallow_other_exceptions` and `::test_import_module_symbol_or_command_error_does_not_mask_module_body_valueerror` pin it: a `ValueError` raised by the consumer's *module body* must not be translated, even though a `ValueError` raised by `pathlib` must be.
- **Distinguish "module not found" from "attribute not found" with different messages.** Lost: the upstream does not, and `__cause__` carries the distinction for anyone who wants it.
- **Let the isinstance failure fall through to a `TypeError` inside `print_schema`.** Lost: the explicit check produces an attributable `CommandError` instead of a deep Strawberry-internal traceback.

**Changes since ship — three shapes became eight.** The Decision shipped enumerating three (unimportable dotted path; non-`Schema` resolved symbol; missing positional argument). Five more accreted, each with a commit and a live test:

| Shape | Added by | Pinned by |
|---|---|---|
| `--path` given with no following value (argparse) | `9e11eb30` dropping `nargs="?"` | `tests/management/test_export_schema.py::test_export_schema_raises_command_error_when_path_flag_has_no_value` |
| file-write failure wrapped from `OSError` | `f6238256` | `examples/fakeshop/tests/test_export_schema.py::test_export_schema_raises_command_error_when_path_directory_missing` |
| `--path` empty-string | `f274b2a4` | `examples/fakeshop/tests/test_export_schema.py::test_export_schema_raises_command_error_when_path_flag_is_empty_string` |
| `--path` whitespace-only (widened from empty-string) | `7f04c5b2` | `tests/management/test_export_schema.py::test_export_schema_raises_command_error_when_path_flag_is_whitespace_only` |
| file-write failure widened to `ValueError` | `fd3825a2` | `examples/fakeshop/tests/test_export_schema.py::test_export_schema_raises_command_error_when_path_contains_embedded_null` |
| selector with an empty module path | `61f6726c` | `tests/management/test_export_schema.py::test_export_schema_raises_command_error_for_malformed_selector` (cases `""` and `":schema"`) |
| selector with a relative module path | `61f6726c` | the same test's `".config.schema"` case |

That is seven rows for five accreted shapes because two rows widen an existing shape rather than adding one, and two selector shapes arrived in one commit. The count in the spec is **eight** total, grouped by the layer that raises them rather than by commit.

**The word "three" propagated further than the Decision.** Before this pass it appeared in the Decision's title, its opening sentence, the Slice 1 checklist sub-bullets (b) and (c), the `## Doc updates` → `docs/GLOSSARY.md` body text, the `## Doc updates` → `KANBAN.md` card body, the `## Doc updates` → `CHANGELOG.md` entry text, and DoD item 5's failure-mode breakdown. The `## Doc updates` → `CHANGELOG.md` text is a verbatim quotation of the shipped `[0.0.7]` `### Added` entry and stays one; every other site now states eight.

The `## Doc updates` → `KANBAN.md` text was **not** a quotation. It was 496 characters of three-shape prose that appears nowhere in `KANBAN.md` — the board's Done body for `DONE-022-0.0.7` is the card's one-line `#### Note`, "one management command (positional `schema`, `--path`, SDL via `print_schema`, `CommandError` paths) + tests." The bullet now quotes that, which is both true and free of the three-shape enumeration; the enumeration's only warrant had been a quotation status it never had. Note that the enumeration carries no numeral, so the `three failure modes` sweep that cleared the rest of the spec could not see either site — the two were reached only by matching the enumeration itself.

### [Decision 6 — No watch, indent, JSON, settings-backed defaults, or alias][spec-022-d6]

The heading was `Decision 6 — No --watch / --indent / --json / settings-backed defaults / alias` until this pass. It was reworded for one mechanical reason: the leading double-hyphens and slashes slugged to `decision-6--no---watch---indent---json--settings-backed-defaults--alias`, while all **17** in-page links spelled it `#decision-6--no-watch--indent--json--settings-backed-defaults--alias`. Every one of those 17 links had been dead since the spec was authored. The rewording removes the hyphen-collapse hazard rather than patching 17 links against a fragile slug.

**Justification, moved.** Each non-shipped feature is a real pain point in some workflow, but none surfaced as repeated friction in the migration story this card serves; `0.0.7`'s job was parity with strawberry-django. The follow-up path is clean because each feature has its own design surface to settle (what does `--watch` do under `runserver`? what JSON shape does `--json` emit?), and folding three of them in here would have bloated the slice.

**Alternatives rejected:**

- **Ship `--watch` because graphene-django ships it.** Lost: `--watch` earns its keep for the JSON-introspection workflow (regenerate `schema.json` on every Python change); for SDL output consumers already have `entr`, `watchexec`, and `make`. Its value is also tied to whether the consumer is iterating under `runserver`, which needs its own design pass.
- **Ship a settings-backed default for the positional argument** (`DJANGO_STRAWBERRY_FRAMEWORK = {"SCHEMA_PATH": "config.schema"}`). Lost per [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands". The consumer's substitute is a one-line `Makefile` target, visible at the repo root.
- **Ship `--json` because it is "free".** Lost: it is not free. The JSON shape graphene-django emits is the GraphQL introspection *query result*, not a `print_schema` round-trip, so emitting it correctly means executing the schema — with the consumer's `DjangoOptimizerExtension` and any request-context dependencies in play.

**Changes since ship:** none. All five omissions hold at `HEAD`; `add_arguments` still registers exactly `schema` and `--path`.

### [Decision 7 — Test placement: `tests/management/__init__.py` ships][spec-022-d7]

**Justification, moved.** [`AGENTS.md`][agents]'s "do not add `__init__.py`" rule is scoped to the two `examples/fakeshop/` test trees and says so explicitly ("collides on the tests package name once `examples/fakeshop` is on pythonpath"); package-test subdirectories under `tests/` are outside it. `docs/TREE.md` #"Subdirectories carry an `__init__.py` shell to match the existing" states the positive convention, and `tests/optimizer/__init__.py` and `tests/types/__init__.py` were already on disk.

**Alternatives rejected:**

- **A flat `tests/test_export_schema.py` with no subdirectory.** Lost: the source lives under a subpackage, `docs/TREE.md`'s mirror rule pairs source subpackages with test subdirectories, and a flat file would force a future second command's tests to either re-flatten or migrate. Vindicated: `tests/management/` now holds `test_export_schema.py`, `test_imports.py`, and `test_inspect_django_type.py`.
- **Omit `tests/management/__init__.py`, treating it like the `examples/fakeshop/` rule.** Lost per the scoping above.

**Changes since ship:** none to the Decision. The directory has since gained the two further modules named above.

### [Decision 8 — Tests go through `call_command`, NOT direct `handle()`][spec-022-d8]

**Justification, moved.** The card body pinned it: direct `handle()` calls bypass Django's argument parsing and let dev errors slip past the test contract. `call_command` runs the full argparse layer, so the test catches type-coercion and `nargs` mismatches a direct call would accept silently, and it captures `self.stdout` / `self.stderr` through the `stdout=` / `stderr=` kwargs without monkey-patching.

**The `CommandParser.error()` mechanism stays in the spec.** It is what makes two of the eight failure shapes reachable at all, so a maintainer who relaxes the rule silently deletes two contracts. Its four-revision chronology is above under revisions 4 and 5.

**Alternatives rejected:**

- **Allow direct `Command().handle(...)` for "unit" tests and `call_command` for "integration" tests.** Lost: the distinction is illusory for a Django command. `handle()` without argparse is not the production path, so the unit half would test code nobody runs.
- **Use `pytest.mark.django_db` instead of `call_command`.** Lost: the mark handles database setup and does not invoke commands. The two are orthogonal and coexist.

**Changes since ship:** the rule holds. All 10 package test functions and all 5 live test functions go through `call_command`. One test — `::test_export_schema_path_help_documents_destructive_utf8_write` — instantiates `Command()` to read the parser it builds, which is not a `handle()` call and does not exercise the command; the spec now says so explicitly rather than leaving a reader to reconcile the import against the rule.

### [Decision 9 — Joint `0.0.7` cut][spec-022-d9]

The heading is unchanged, but all **6** in-page links to it spelled the anchor `#decision-9--joint-0_0_7-cut` while the heading slugs to `decision-9--joint-007-cut` — dotted versions lose their dots, they do not gain underscores. Dead since authoring; repaired by this pass.

**Justification, moved.** The Decision restates [`spec-020`][spec-020]'s [Decision 10][spec-020-decision-10--joint-007-cut] verbatim so this card's reader does not have to chase a cross-spec reference, and `KANBAN.md` #"The last `0.0.7` card to ship owns the version bump from `0.0.6`" already pinned the policy at board level. At authoring time the `[0.0.7]` `### Added` section already carried `DONE-020-0.0.7`'s `DjangoListField` entry and `DONE-021-0.0.7`'s `Django AppConfig` entry; this card appended the third.

**Alternatives rejected:**

- **This card bumps `0.0.7` because it ships fourth.** Lost: ship order is whichever card a maintainer picks up next, not card `NNN`. Pinning the bump to a specific card creates a sequencing constraint with no engineering justification.
- **Add a separate release-cut card to `KANBAN.md` owning the bump.** Lost: out of scope for a spec whose only authorized `KANBAN.md` edit is its own column move, and the "last card to ship" policy works as-is.

**Changes since ship:** the policy executed as designed. `0.0.7` shipped 2026-05-27 with seven cards; this card did not carry the bump.

### [Decision 10 — Live coverage belongs in `examples/fakeshop/tests/`, NOT `test_query/`][spec-022-d10]

**The ruling survives; two of its four justification bullets cited a file that no longer exists.**

**Justification, moved — the two bullets that still hold.** `examples/fakeshop/test_query/README.md` scopes that tree to tests that "exercise the full Django + Strawberry HTTP stack end-to-end by sending requests to `/graphql/`", and an SDL-export command is not an HTTP-shaped surface: it does not hit `/graphql/` and does not exercise the request pipeline. `docs/TREE.md` #"`examples/fakeshop/tests/` — **Example-project tests, no HTTP `/graphql/`**" names that tree as the home for "management commands via `django.core.management.call_command`". [`AGENTS.md`][agents]'s coverage-priority rule is satisfied rather than waived: the fall-back tier is correct only because the lines are genuinely unreachable from a live query, which they are.

**Justification, moved — the two bullets that no longer hold.** The Decision also argued from the *file*: that `examples/fakeshop/tests/test_commands.py` "already covers the example project's other commands (`seed_data`, `delete_data`, `seed_shards`, `create_users`, `delete_users`) via `call_command`", so adding one test "extends the file in place"; and it quoted the card body's "a fakeshop test under `examples/fakeshop/test_query/` (or `examples/fakeshop/tests/` if not HTTP-shaped)" as the "or" this Decision settles. `31642c9c` (2026-05-29, "tests: relocate example app tests into per-app folders") deleted `examples/fakeshop/tests/test_commands.py`, moving the example project's own command tests to `examples/fakeshop/apps/<app>/tests/`. The extend-in-place argument is therefore historical: the live coverage now lives in a dedicated `examples/fakeshop/tests/test_export_schema.py`, added by `35e3c26d` (2026-06-01). **The tier the Decision chose is unchanged — only the file inside it moved.**

**Alternatives rejected:**

- **Put the live test under `examples/fakeshop/test_query/test_export_schema.py`.** Lost: it violates that tree's declared scope and would be the only non-HTTP test in it. Still correct; no such file exists at `HEAD`.
- **Skip the live test and rely on the package tests for everything.** Lost: the package tests use a synthesized fixture schema, not the consumer's real one. The live test is what proves the command works against the consumer's real schema — a `DjangoSchema` (a `strawberry.Schema` subclass) built through `finalize_django_types()`, which is also the only place the isinstance guard's subclass tolerance is exercised. **This rejection has gained force since ship.** Three of the five live tests are failure-branch tests that the package tier used to own and deliberately gave up: `::test_export_schema_raises_command_error_when_path_directory_missing` says so in its own docstring — the `OSError` branch "is reached only after the real `config.schema` is imported, finalized, and rendered to SDL, so this carries stronger contract pressure than the prior synthetic `test_module:schema` package test". A trailing comment in `tests/management/test_export_schema.py` records the same migration from the package side.

### `## Problem statement` and `## Current state`

**Moved.** The reference-package comparison (strawberry-django's 38-line `export_schema.py` versus graphene-django's 111-line `graphql_schema.py`, with each one's flag inventory) and the migration-story framing: migrants from strawberry-django know the command as `manage.py export_schema`, migrants from graphene-django know it as `manage.py graphql_schema`, and the card borrows the former's name and shape. Also moved: the observation that the shipping bar is deliberately low and the discipline the card needed to enforce was *what not to put in the command*.

**Deleted as falsified.** `## Current state` described a pre-ship tree — no `management/` subdirectory on disk, the `[alpha]` tag still on `docs/TREE.md`'s target-layout entry, `examples/fakeshop/tests/test_commands.py` present as the extension target. All three statements are false at `HEAD` and none is worth preserving as a claim; the section now describes the shipped tree.

### `## Goals` and `## Non-goals`

**Moved.** `## Goals` item 5's argument for omitting settings-backed defaults, and `## Non-goals`' per-item reasoning where it duplicated [Decision 4][spec-022-d4] and [Decision 6][spec-022-d6]. The `## Non-goals` bullet on `finalize_django_types()` keeps its normative half in the spec.

**Superseded counts.** `## Goals` item 3 pinned "the **seven tests**" with a 2 + 4 + 1 breakdown, and item 4 pinned the live test as an extension of `examples/fakeshop/tests/test_commands.py`. Both are restated in the spec against `HEAD` (10 package test functions / 12 collected items; a dedicated live module with 5).

### `## Borrowing posture`

**Moved.** The three inline `Justification:` clauses under the "From `strawberry-django`" list (why the positional-plus-`--path`-plus-`print_schema` shape is the minimal Django-correct surface; why `CommandError` is the right class for both upstreams; why the non-`Schema` message is adopted verbatim). The whole "**Two categories of forced divergence**" enumeration with its per-rule provenance — it is the same content as [Decision 2][spec-022-d2]'s moved provenance list, narrated twice, and it collapses to one telling here. And the `graphene-django` non-borrow ledger's per-item reasoning, which restates [Decision 6][spec-022-d6].

**Kept in the spec.** The upstream's verbatim 38-line source block, because it is the artifact the borrowing is measured against, and the one-line statement of what was borrowed versus what was not.

**A claim this section may no longer make.** The "Verified contents (38 lines)" code block is a faithful quotation of the upstream and stays. But the spec used to close the section by asserting that "the behavioral shape … matches the upstream verbatim; only the documentation + annotation shape diverges". Four post-ship commits have moved the shipped command away from the upstream behaviorally: no `nargs` on either argument, a rewritten `--path` help string, suppressed stdout newline, disabled newline translation on the file write, an empty-value `--path` rejection, a wrapped write failure, a success message, and selector validation. The spec now states the divergence rather than denying it.

### `## User-facing API`

**Moved — the chronology only.** The `(rev2 M2)` attribution and the account of what the example used to be (bare `config.urls`) and which round changed it are recorded above under revision 2. The note itself **stays in the spec**: why the example must be `config.urls:urlpatterns` and not bare `config.urls` is implementation-relevant under [`worker-1.md`][worker-1]'s carve-out — a reader who "simplifies" it back reintroduces an example that succeeds instead of failing, which is the exact defect rev2 M2 found.

**Reconciled in place.** The usage examples themselves are unchanged and correct at `HEAD`. The "Error shapes" block gained the shapes the command has since grown.

**Deleted as falsified.** The stdout section's "Shell redirection therefore produces a file byte-identical to the `--path` form" sentence — recorded under [Decision 4][spec-022-d4] above and under `## Claims the spec may no longer make` below. The section now states the emitted-bytes guarantee and names the interpreter's `sys.stdout` translation as what a redirect is still subject to, which is the obligation [Decision 4][spec-022-d4] places on doc text quoting the contract.

### The `## Implementation plan` section

**Moved.** The per-slice line-delta estimates (`+55 / -0`, `+150 / -0`, `+36 / -11`, "~230 lines total") and the revision-by-revision adjustments that produced them (rev2 H1 bumped Slice 1 from `+50`; rev2 M1 bumped Slice 2 from `+120`; rev2 L1 bumped Slice 3 by one removed prose fragment). Estimates of a diff that shipped fifteen months of commits ago are archaeology, not contract.

### `## Edge cases and constraints`

**Moved.** The `pyproject.toml [tool.ruff.lint.per-file-ignores]` bullet's full derivation, which is the same material as [Decision 2][spec-022-d2]'s provenance list. The "Coverage of the command body" bullet's statement-by-statement accounting, which described a six-statement `handle()` that now has more.

**Deleted as falsified.** The `call_command` and `stdout` bullet's second half — the trailing-newline claim recorded under [Decision 4][spec-022-d4] above and under `## Claims the spec may no longer make` below.

### The `## Test plan` section

**Moved.** The whole `Negative-shape test (none in 0.0.7):` bullet. It named a test (`test_export_schema_command_does_not_define_forbidden_attributes`), authored nothing, and existed to explain why: the sibling AppConfig spec's consolidated negative-shape test exists because that card has four documented decisions about what *not* to add, whereas every Decision here is about what to add or how the existing surface behaves, so there is no forbidden-key list for `Command` to assert against. If a future card adds a "do not ship `--watch`" enforcement it authors the negative test then. Correct reasoning, zero contract; it belongs here.

**Moved.** Each test's per-revision provenance parenthetical (which revision split it, renamed it, or changed its selector).

**Superseded.** The seven pinned names, the "single pytest item per test, NOT `pytest.mark.parametrize`" prohibition, and the `examples/fakeshop/tests/test_commands.py (extend)` heading. See `## Claims the spec may no longer make`.

### `## Doc updates`

**Moved.** The four inline `Justification:` clauses on the no-edit bullets — why the command is not a `README.md` consumer-name-surface change, why `GOAL.md`'s `astronomy` showcase never touches `manage.py`, and why `TODAY.md`'s query-shape snapshot is unaffected. Re-verified during this pass: `grep -n 'export_schema\|management command' GOAL.md` returns nothing, so the `GOAL.md` reasoning still holds at `HEAD`. The normative "no edits to these three files" statements stay in the spec.

**Moved.** The rev3 M1 explanation of why the `docs/TREE.md` fragment removal had to be repeated in this section as well as in the Slice 3 checklist.

### `## Risks and open questions`

The whole seven-bullet section moved. Each was written as a preferred-answer / fallback pair; each is now resolved by fifteen months of shipped history, so none is an open question and none belongs in a contract.

1. **`import_module_symbol` signature stability.** Preferred answer: `(selector: str, default_symbol_name: str | None = None) -> object` has been stable since strawberry-graphql 0.x. Fallback: a rename would break at import time and the fix is the import path. **Resolved:** the symbol is unchanged at `HEAD`, though the command now reaches it through `_imports.py` rather than importing it directly (see [Decision 3][spec-022-d3]).
2. **`print_schema` output stability.** Preferred answer: stable for years; consumers rely on byte-for-byte stability for CI SDL-diffing. Fallback: a whitespace or ordering change is strawberry-graphql's concern, and the test plan asserts content rather than byte equality. **Partly overtaken:** `tests/management/test_export_schema.py::test_export_schema_stdout_matches_path_file_and_print_schema` now *does* assert byte equality — but against `print_schema`'s own return value in the same process, so it pins the command's fidelity to the printer rather than the printer's stability across releases. The distinction is what makes the assertion safe.
3. **`CommandParser.error()` raising `CommandError` for a missing positional argument.** Preferred answer: it raises directly on the `called_from_command_line=False` branch, which `call_command` constructs by default, so `pytest.raises(CommandError)` catches it with no `SystemExit` involved. Fallback: if Django changed the override, the test re-asserts and no production code moves. **Resolved:** unchanged, and the same mechanism now also carries the bare-`--path` rejection.
4. **Schema-module side effects at import time.** Preferred answer: resolving the dotted path runs the consumer's module body, which calls `finalize_django_types()` and constructs the schema; `pytest-django`'s session setup covers the Django-must-be-ready case. Fallback: a consumer whose schema construction needs per-request context is a theoretical risk, and the fix would be upstream. **Resolved in practice:** five live tests drive the real `config.schema` through the command with no such trouble.
5. **No `__init__.py.py` typo regression.** Preferred answer: a misnamed marker would fail pytest collection before any test body runs. **Resolved:** both markers exist and carry docstrings.
6. **`docs/TREE.md` `[alpha]` tag drift.** Preferred answer: Slice 3 removes the tag in the same pass that adds the current-on-disk block. **Resolved:** `grep -n "\[alpha\]" docs/TREE.md` returns nothing.
7. **Future-card surface accretions.** Preferred answer: none of `--watch` / `--indent` / JSON / settings is scheduled, and the minimal surface does not preclude them. **Resolved:** none has shipped; [Decision 6][spec-022-d6] holds at `HEAD`.

### `## Out of scope (explicitly tracked elsewhere)`

**Superseded card ids and versions.** Four bullets forward-referenced `TODO-ALPHA-029` / `031` / `032` / `033` "for `0.0.12`". Every one of the four features shipped, and all four references were wrong in *both* halves:

| Feature | Spec said | Shipped as |
|---|---|---|
| Channels ASGI router (`DjangoGraphQLProtocolRouter`) | `TODO-ALPHA-029` for `0.0.12` | `DONE-041-0.0.14` |
| Debug-toolbar middleware | `TODO-ALPHA-031` for `0.0.12` | `DONE-042-0.0.14` |
| Response-extensions debug middleware | `TODO-ALPHA-032` for `0.0.12` | `DONE-044-0.0.14` |
| Test-client helpers (`TestClient`, `GraphQLTestCase`) | `TODO-ALPHA-033` for `0.0.12` | `DONE-043-0.0.14` |

**Re-derive a card by feature, never by number.** The 2026-07-30 renumber left the numbers `029` / `031` / `032` / `033` in use, and at `HEAD` they name `DONE-029-0.0.9` (`DjangoType` consumer-DX cleanup), `DONE-031-0.0.9` (Django-model-based GlobalID encoding), `DONE-032-0.0.9` (full Relay story), and `DONE-033-0.0.9` (connection-aware optimizer planning) — four real, shipped, entirely unrelated cards. A number-preserving rewrite would have produced four confidently-wrong citations that grep clean. Each was resolved by matching the feature description against `KANBAN.md`'s Done card titles.

### `## Definition of done`

**Moved.** DoD item 8's clarifying clause about who verifies the 100% coverage gate carries the rev4 L4 chronology; the resolved posture (CI's gate, not the worker's) stays in the spec without it.

**Superseded counts.** Item 2's `nargs` declarations, item 5's "**7 tests**" with its (a)-(g) breakdown and its `parametrize` prohibition, item 6's `examples/fakeshop/tests/test_commands.py` file name, and item 10's `WIP-ALPHA-018-0.0.7` card id. All restated in the spec against `HEAD`.

## Claims the spec may no longer make

Deleted from the spec rather than moved, and recorded here so a reader can see they were once asserted. Each is false at `HEAD`.

1. **"`parser.add_argument("schema", nargs=1, …)`" and "`options["schema"][0]`."** Superseded by `9e11eb30`. The positional argument carries no `nargs` and `handle` reads `options["schema"]` directly.
2. **"`parser.add_argument("--path", nargs="?", …)`" with `help="Optional path to export"`.** Superseded by `9e11eb30` (the `nargs`) and `f6238256` (the help text). A bare `--path` is now an argparse error, and the help string is `"Write UTF-8 SDL to this file, overwriting it without prompting"`, pinned by a test.
3. **"Default `nargs=None` … Rejected: the upstream uses `nargs=1`."** The rejected alternative is what ships. Recorded under [Decision 2][spec-022-d2] above as a rejection that lost.
4. **"`self.stdout.write(schema_output)` appends a trailing newline by default; the test plan accounts for the newline in the captured-string assertions."** The exact opposite of the shipped contract: `ending=""` suppresses it so stdout bytes equal the file's bytes equal `print_schema`'s return value.
5. **"`CommandError` … in three shapes."** Eight at `HEAD`, enumerated in [Decision 5][spec-022-d5]. The claim appeared in the Decision's title, its opening, the Slice 1 checklist, `## Doc updates`, and DoD item 5.
6. **"`handle()` … `if path: pathlib.Path(path).write_text(...)` / `else: self.stdout.write(...)`."** The shipped body routes on three output branches, not two, and tests `path is None` before any truthiness test — the conflation this pinned body encodes is precisely the defect `f274b2a4` fixed.
7. **"[the command] resolves the symbol via `strawberry.utils.importer.import_module_symbol(options["schema"][0], …)` [inline in `handle()`]."** Resolution is delegated to `import_module_symbol_or_command_error` in `_imports.py`, which validates the selector's shape before delegating.
8. **"`tests/management/test_export_schema.py` contain[s] **seven** tests" and "single pytest item per test, NOT `pytest.mark.parametrize`."** Ten test functions / 12 collected items at `HEAD` (`uv run pytest tests/management/test_export_schema.py --collect-only -q --no-cov`), one of which — `::test_export_schema_raises_command_error_for_malformed_selector` — is a deliberate three-case `parametrize`. Of the seven pinned names four survive verbatim; `::test_export_schema_writes_sdl_to_stdout_by_default` and `::test_export_schema_writes_sdl_to_path_when_path_set` were merged into the strictly stronger `::test_export_schema_stdout_matches_path_file_and_print_schema`, and `::test_export_schema_falls_back_to_default_symbol_name_schema` was retired.
9. **"the resolved symbol's default-name fallback … [is pinned by exactly one test]."** The named test no longer exists, but nothing was lost: four of the five live tests drive the bare `"config.schema"` selector with no `:schema` suffix, and `tests/management/test_imports.py::test_import_module_symbol_or_command_error_applies_default_symbol_name` pins the fallback at the helper. The contract is pinned five times, not once.
10. **"Extend `examples/fakeshop/tests/test_commands.py`."** The file was deleted by `31642c9c` (2026-05-29). The live coverage is `examples/fakeshop/tests/test_export_schema.py` (5 tests, added by `35e3c26d`, 2026-06-01). [Decision 10][spec-022-d10]'s tier ruling is unaffected.
11. **"`WIP-ALPHA-018-0.0.7`."** Four occurrences. The card is `DONE-022-0.0.7` at `KANBAN.md:3971`; `018` was its pre-renumber number.
12. **"`DONE-016`" / "`DONE-017`."** Four occurrences across three lines, naming the sibling `0.0.7` cards by their pre-renumber numbers. They are `DONE-020-0.0.7` and `DONE-021-0.0.7`.
13. **"`TODO-ALPHA-029` / `031` / `032` / `033` for `0.0.12`."** Wrong in both card id and version; see `## Out of scope` above.
14. **"The predecessor [`spec-021`]'s Decision 4 deliberately deferred any `Django AppConfig` `ready()` body … which is preserved here."** Asserted in `## Problem statement`, `## Non-goals`, [Decision 3][spec-022-d3], [Decision 6][spec-022-d6], and `## Edge cases and constraints`. False at `HEAD`: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` applies three upstream patch modules (`_django_patches`, `_strawberry_patches`, `_cross_web_patches`), gated by the `APPLY_UPSTREAM_PATCHES` setting. Nothing this card ships depends on the claim — Django's command discovery walks `management/commands/` directories and involves no `AppConfig` method at all. Three of the five sites (`## Problem statement`, `## Non-goals`, `## Edge cases and constraints`) now state that self-contained fact instead; [Decision 3][spec-022-d3]'s paragraph survives with the `ready()` clause struck; [Decision 6][spec-022-d6]'s "mirrors spec-021 Decision 4/5's posture" bullet was dropped outright, being a rationale item rather than a contract. The `[spec-017-decision-4--no-readyhook-in-0-0-7]` reference definition — **4 uses plus its one definition line**, and an anchor that did not resolve at `HEAD` either — was removed with the claim.
15. **"The behavioral shape … matches the upstream verbatim; only the documentation + annotation shape diverges."** See `## Borrowing posture` above.
16. **"`pyproject.toml` pins `strawberry-graphql>=0.262.0`."** True at authoring, false at `HEAD`: the floor is `>=0.316.0`, so the accompanying `#"strawberry-graphql>=0.262.0"` citation did not resolve either. `## Current state` now names the `HEAD` floor and says explicitly that the command never depended on where in the range it sits — the bullet's load-bearing half (both symbols are already in the dependency tree; the command adds no dependency) is unaffected.
17. **"`examples/fakeshop/config/schema.py` exposes a top-level `schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`."** Asserted in `## Current state` and restated in the `## Test plan`'s live-tier stdout bullet. At `HEAD` the fixture is `schema = DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])`. The correction is load-bearing rather than cosmetic: `DjangoSchema` subclasses `strawberry.Schema` (`django_strawberry_framework/schema.py::DjangoSchema`), so the live tier is what makes `## Edge cases and constraints`' "subclasses pass" bullet an exercised contract instead of a hypothetical, and narrowing the guard to an exact-type check would fail the live tier. Both sites and the edge-case bullet now say so.
18. **"`tests/management/__init__.py` … module docstring `\"\"\"Package tests for django_strawberry_framework.management.*.\"\"\"`."** Pinned as exact text in the Slice 2 checklist and in the `## Test plan`; the shipped docstring is `"""Package tests for django-strawberry-framework management commands."""`. Same shape as the `management/commands/__init__.py` drift recorded under [Decision 1][spec-022-d1] above, except that this one was written as a pin rather than a suggestion. Both sites now state the shipped text.
19. **"Shell redirection therefore produces a file byte-identical to the `--path` form."** Asserted in `## User-facing API`, directly above the `> schema.graphql` example, and implied by the `ending=""` bullet's counterfactual under [Decision 4][spec-022-d4] ("`manage.py export_schema … > out.graphql` differs from `--path out.graphql` by exactly one byte"). False wherever the native line separator is not LF: `ending=""` removes an appended byte from the string handed to `self.stdout`, and the interpreter's own `sys.stdout` translation then applies to whatever a shell redirects, while `newline=""` makes only the `--path` file platform-stable. Both sites now state the equality at the emitted-bytes level, and `## User-facing API` names the translation and points a consumer who needs LF on disk at `--path`. This is the same over-read that [Decision 4][spec-022-d4]'s scope paragraph exists to prevent, standing three pages earlier in the same document; that paragraph's closing obligation on doc text quoting the contract is what made the two irreconcilable.

## Verified against the shipped code

Everything in this file was checked against the working tree on 2026-08-18, not against the spec's own prose.

- **The code shipped the spec exactly — as the spec read at authoring time.** `git show d780726f:django_strawberry_framework/management/commands/export_schema.py` is byte-for-byte the shape the spec then pinned, `nargs=1` on the positional and `nargs="?"` on `--path` included; those two declarations are what [Decision 2][spec-022-d2] now excludes, and their removal is catalogued under `## Claims the spec may no longer make` items 1 and 2. `git show d780726f:tests/management/test_export_schema.py | grep '^def test_'` lists all seven names the `## Test plan` then pinned, verbatim and in order. Every divergence catalogued above post-dates the ship commit. Nothing was skipped, dropped, or forgotten at build time — which is why this cycle changed no code and no tests.
- **Every commit cited above was confirmed to exist** with the stated date and subject via `git log -1 --format='%ad %s' --date=short <sha>`.
- **Every count stated above was measured at the time of writing**, with the instrument named. The incoming catalog's `Justification:` population (11) was re-derived as 17; its live-tier bare-selector count (3) was re-derived as 4.
- **Every rewritten card id was re-derived by feature against `KANBAN.md`'s Done card titles**, never by preserving the number.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-020-decision-10--joint-007-cut]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021-decision-3--no-public-export]: ../spec-021-apps-0_0_7.md#decision-3--no-public-export
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-022-d1]: ../spec-022-export_schema-0_0_7.md#decision-1--module-location--no-public-export
[spec-022-d10]: ../spec-022-export_schema-0_0_7.md#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query
[spec-022-d2]: ../spec-022-export_schema-0_0_7.md#decision-2--command-class-shape
[spec-022-d3]: ../spec-022-export_schema-0_0_7.md#decision-3--symbol-resolution-through-the-shared-_imports-command-helper
[spec-022-d4]: ../spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema
[spec-022-d5]: ../spec-022-export_schema-0_0_7.md#decision-5--commanderror-is-the-commands-only-failure-surface
[spec-022-d6]: ../spec-022-export_schema-0_0_7.md#decision-6--no-watch-indent-json-settings-backed-defaults-or-alias
[spec-022-d7]: ../spec-022-export_schema-0_0_7.md#decision-7--test-placement-testsmanagement__init__py-ships
[spec-022-d8]: ../spec-022-export_schema-0_0_7.md#decision-8--tests-go-through-call_command-not-direct-handle
[spec-022-d9]: ../spec-022-export_schema-0_0_7.md#decision-9--joint-007-cut
[spec-022]: ../spec-022-export_schema-0_0_7.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
