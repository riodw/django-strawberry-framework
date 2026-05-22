# Spec: `apps.py` and Django `AppConfig`

Target release: `0.0.7`.
Status: draft (revision 6, post-rev5 build-readiness audit).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`](GLOSSARY.md) (entries [`Django AppConfig`](GLOSSARY.md#django-appconfig), [`finalize_django_types`](GLOSSARY.md#finalize_django_types), [`DjangoType`](GLOSSARY.md#djangotype)), [`KANBAN.md`](../KANBAN.md) card `DONE-017-0.0.7`, predecessor spec [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) (Decision 10 — joint `0.0.7` cut policy reused verbatim here).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pins module location (`django_strawberry_framework/apps.py`), AppConfig subclass shape (`DjangoStrawberryFrameworkConfig`, three attributes: `name`, `verbose_name`, no `label` override, no `default_auto_field`), the deliberate omission of `ready()` (no side effects until a shipped feature needs one — matches the `conf.py` posture in [`AGENTS.md`](../AGENTS.md) line 20), test placement at `tests/test_apps.py`, the four-test plan (importable / subclass / attribute pinning / registry pickup), the policy that consumers add the package to `INSTALLED_APPS` by its dotted package name (Django's implicit single-AppConfig discovery handles the rest), the live-fakeshop coverage path (the example project already lists `"django_strawberry_framework"` in `INSTALLED_APPS`; this card lands the explicit `AppConfig` underneath that entry without changing the entry text), the explicit deferral of the version bump to the last `0.0.7` card to ship (per [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10), and the doc-updates list across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` (no `README.md` / `GOAL.md` / `TODAY.md` updates — the AppConfig is not a consumer-visible surface change in those documents' framing).
- **Revision 2** (post-rev1 review against [`docs/feedback.md`](feedback.md)) — two high-severity corrections plus one low cleanup; all surfaced by the rev1 reviewer:
  1. **H1**: rev1's Slice 3 [`docs/README.md`](README.md) instructions had two defects against the current file state. (a) Rev1 told the editor to "Add a bullet to the 'Shipped today (`0.0.7`)' list" — but the current `docs/README.md:89` heading still says `**Shipped today** (`0.0.6`)` because `DONE-016-0.0.7` shipped its bullet without bumping the heading (the `DjangoListField` entry carries "(new in `0.0.7`)" inline instead). Following rev1 literally would mean editing a heading that doesn't yet exist. (b) Rev1's removal instruction at line 112 said "Remove `Channels ASGI router, debug-toolbar middleware, test client helper, response-extensions debug, schema export management command, Django `AppConfig`` from the `Coming in 0.1.0` bullet" — but the current file's line 112 is just `- schema export management command, Django `AppConfig``, and `WIP-ALPHA-018-0.0.7` (the schema-export card) is explicitly out of scope here. Following rev1 literally would remove the schema-export half too early, falsifying the docs while the feature is still planned. Fix: rewrite the [`docs/README.md`](README.md) bullet in [Doc updates](#doc-updates) into two sub-bullets — (1) bump the heading from `(0.0.6)` to `(0.0.7)` (catch-up against the post-`DONE-016` drift; distinct from the version-string bump in [Decision 6](#decision-6--joint-0_0_7-cut) which still belongs to the last `0.0.7` card); (2) surgically remove only `, Django `AppConfig`` from the `Coming in 0.1.0` line, leaving `- schema export management command` for `WIP-ALPHA-018-0.0.7` to remove. Also updates Definition of done item 9 to mention both edits explicitly.
  2. **H2**: rev1's Slice 2 test plan named only one negative-shape test (`does_not_define_ready`). But the spec's Decisions 2 / 4 / 5 / 8 forbid four distinct class-body keys (`label`, `ready`, `default_auto_field`, `default`) and the Definition of done items 6 / 7 / 8 (rev1 numbering) asserted three of those absences with no test backing. A future drive-by edit could add `label = "dsf"`, `default_auto_field = "django.db.models.BigAutoField"`, or `default = True` and pass the planned suite — the "what NOT to put in AppConfig" discipline was partly review-only. Fix: rename `test_djangostrawberryframeworkconfig_does_not_define_ready` to `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` and consolidate the four forbidden keys into the same test (iterate `{"ready", "label", "default_auto_field", "default"}`, assert each is absent from `__dict__`, fail message names the offending key plus the Decision that forbids it). Collapse rev1's three separate Definition-of-done items (6, 7, 8) into one item 6 that names all four Decisions and the consolidated test; renumber items 9-15 → 7-13. Update the Slice 2 implementation-plan-table row, the [Edge cases](#edge-cases-and-constraints) `__dict__` coverage paragraph, and Slice 2's negative-shape checklist sub-bullet to match.
  3. **L1**: rev1's [`docs/TREE.md`](TREE.md) doc-update bullet said `tests/test_apps.py` slots "between `test_list_field.py` and `test_registry.py` (alphabetical)" — but `test_apps.py` sorts BEFORE `test_list_field.py` alphabetically, not between it and `test_registry.py`. Fix: change the placement to "before `test_list_field.py`" and label the change as rev2 L1 inline.
- **Revision 3** (post-rev2 review against [`docs/feedback.md`](feedback.md)) — one high-severity correction plus three low cleanups; all surfaced by the rev2 reviewer:
  1. **H1**: rev1/rev2's pinned AppConfig shape said `name`, `verbose_name`, and a one-line module docstring — "nothing else" — but the slice's own `uv run ruff check --fix .` gate enables pydocstyle's `D` family (`pyproject.toml [tool.ruff.lint] select = [..., "D", ...]`) and the ignore list (`pyproject.toml [tool.ruff.lint] ignore = [...]`) does NOT exclude `D101` (Missing docstring in public class). A public `DjangoStrawberryFrameworkConfig` class with no class docstring would fail the required ruff gate even if the code follows the spec exactly. The "exactly this shape" framing and the gate were mutually unsatisfiable. Fix: make a one-line class docstring (e.g. `"""Register django-strawberry-framework with Django's app loader."""`) part of the pinned shape — bumped from "three pieces of state" (name, verbose_name, module docstring) to "four pieces of state" (name, verbose_name, module docstring, class docstring); updated [Decision 2](#decision-2--name--label--verbose_name-pinning), [Borrowing posture](#borrowing-posture) (noted the forced divergence from `strawberry_django/apps.py` which has no class docstring), the [Problem statement](#problem-statement) prose, Goal 1, DoD item 1, and the Slice 1 checklist. Also clarified the consolidated negative-shape test (Slice 2 checklist + [Test plan](#test-plan)) so "no extra AppConfig attributes" reads as "no extra **behavioral** class attributes" — the implicit `__doc__` populated by the class docstring is intentionally NOT in the four-key iteration set; documentation is not behavior, and the iteration set is `{"ready", "label", "default_auto_field", "default"}`, none of which collide with `__doc__`. Explicitly forbade `# noqa: D101` as a workaround per [`AGENTS.md`](../AGENTS.md) line 4's "always recommend the root-cause fix over the surface patch" posture.
  2. **L1**: the rev2 H1 fix updated the detailed [Doc updates](#doc-updates) section's `docs/README.md` bullet to do the heading bump and the surgical `, Django AppConfig` removal, but did NOT propagate that surgical wording into the entry-point Slice 3 [Slice checklist](#slice-checklist) `docs/README.md` bullet, which still carried the rev1 generic "move the mention" instruction. An implementer reading the checklist top-down (the canonical entry point) would follow the generic wording, hit the detailed section only after the edit, and potentially over-remove the `schema export management command` half. Fix: replace the Slice 3 `docs/README.md` checklist bullet with the same three-part concrete actions ((a) bump heading `(0.0.6)` → `(0.0.7)`, (b) add the AppConfig bullet, (c) surgically remove only `, Django `AppConfig`` from line 112 leaving `schema export management command` for `WIP-ALPHA-018-0.0.7`) so the checklist and the detailed section say the same thing.
  3. **L2**: the [Edge cases](#edge-cases-and-constraints) "Django 3.2+ AppConfig discovery" bullet cited `Django >= 4.2` as the package's pinned floor and the "Django 4.2+ venv" as the install observation; the actual pin in `pyproject.toml:29` is `Django>=5.2`. The discovery conclusion (Django 3.2+ behavior is in place) is unaffected — 5.2 is well above 3.2 — but the citation was stale and would send a reader to verify the wrong constraint. Fix: change the citation to `pyproject.toml:29` with `Django>=5.2`; drop the "Django 4.2+ venv" parenthetical.
  4. **L3**: [Decision 4](#decision-4--no-readyhook-in-0_0_7)'s justification block still cited "The Slice 2 negative test (`assert "ready" not in DjangoStrawberryFrameworkConfig.__dict__`)" — the rev1 single-key shape. Rev2 H2 consolidated the four forbidden keys into one test (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) but the propagation missed this paragraph. The detailed [Test plan](#test-plan) is correct; this is purely stale prose, but it could mislead a future editor into believing the single-key assertion still exists. Fix: update Decision 4's paragraph to name the consolidated test and clarify that the `ready` absence is one of four keys exercised by it.
- **Revision 4** (post-rev3 review against [`docs/feedback.md`](feedback.md)) — four low-severity corrections, all propagation / consistency cleanups against rev3's H1 docstring landing; no architectural change. Plus two informational follow-ups the rev3 reviewer flagged as non-findings but worth fixing for hygiene:
  1. **L1**: [Decision 2](#decision-2--name--label--verbose_name-pinning)'s justification block still claimed "Three pieces of state is the entire surface strawberry-django ships; the borrowing posture is to match that surface." Both halves were stale: (a) rev3 H1 already bumped the spec's pinned shape from "three pieces of state" (rev1/rev2) to "four pieces of state" (rev3) by adding the class docstring, and (b) the upstream `strawberry_django/apps.py` actually ships **only two attributes** (`name`, `verbose_name`) with no module docstring and no class docstring — the spec's own [Borrowing posture](#borrowing-posture) section explicitly acknowledges this. So "three" was wrong against both the spec's own framing AND the upstream's actual shape. Fix: rewrite the justification line to "Two behavioral attributes is the entire surface strawberry-django ships … the docstrings here are additive, forced by this repo's stricter pydocstyle gate per rev3 H1 / rev4 L3 — the documentation shape diverges, but the behavioral shape is identical."
  2. **L2**: rev3's "four pieces of state" framing (in Slice 1 checklist, Goal 1, and Decision 2 lead-in) mixed class-scope artifacts (`name`, `verbose_name`, `__doc__` from the class docstring) with the module-scope artifact (the module docstring at `django_strawberry_framework.apps.__doc__`). Calling the module docstring "a piece of `DjangoStrawberryFrameworkConfig`'s state" was a category error, and the bundling undercut the documentation-vs-behavior distinction that rev3 H1 / rev2 H2 themselves rely on (the consolidated negative-shape test wording says explicitly "documentation is not behavior" when justifying why `__doc__` is excluded from the iteration set). Fix: replace "four pieces of state" everywhere with "**two class-level behavioral attributes** plus **two docstrings** (a module docstring required by `D100` and a class docstring required by `D101`); the two docstrings are documentation, not behavior, and are exempt from the negative-shape iteration accordingly." Applied to [Slice 1 checklist](#slice-checklist), [Goal 1](#goals), and [Decision 2](#decision-2--name--label--verbose_name-pinning) lead-in. Keeps the documentation/behavior split load-bearing across every section of the spec.
  3. **L3**: rev3 H1 correctly cited `D101` ("Missing docstring in public class") as the forcing function for the class docstring but did NOT name the symmetric `D100` ("Missing docstring in public module") for the module docstring. `D100` is also in `pyproject.toml`'s `[tool.ruff.lint] select = [..., "D", ...]`, also not in the ignore list, and the per-file-ignores at `pyproject.toml:100-107` do not exempt `django_strawberry_framework/apps.py`. The module docstring is therefore also gate-forced, not a stylistic choice — a future maintainer reading the rev3 framing might delete the module docstring under the misapprehension that it was preference, hit `D100`, and revert (or, worse, suppress with `# noqa: D100`). The rev3 H1 "no `# noqa` workaround" instruction only named `D101`. Fix: name `D100` alongside `D101` in [Slice 1 checklist](#slice-checklist), [Decision 2](#decision-2--name--label--verbose_name-pinning), and the [Borrowing posture](#borrowing-posture) "forced divergence" sentence (which bumps from "one forced divergence" to "two forced divergences"). Forbid `# noqa: D100` alongside `# noqa: D101`. Symmetric lint-gate provenance throughout.
  4. **L4**: [Decision 8](#decision-8--no-default-attribute) (was titled "No `default = True` marker" in rev1-rev3) forbid `default = True` specifically, but the consolidated negative-shape test asserts `"default" not in DjangoStrawberryFrameworkConfig.__dict__`, which catches `default = True` AND `default = False` AND any other value. The test was broader than the Decision permitted, breaking the symmetry with [Decision 2](#decision-2--name--label--verbose_name-pinning) / [Decision 4](#decision-4--no-readyhook-in-0_0_7) / [Decision 5](#decision-5--no-default_auto_field-and-no-models), each of which forbids the attribute outright at any value. Fix: rename Decision 8 from "No `default = True` marker" to "No `default` attribute"; rewrite the body to "`DjangoStrawberryFrameworkConfig` does NOT declare `default` at all (neither `default = True` nor `default = False`)"; add a sentence pinning that the negative-shape test catches the attribute at any value. Update the [Borrowing posture](#borrowing-posture) "Django's `default = True` class attribute" bullet to "Django's `default` class attribute (at any value — `True`, `False`, or other)" for symmetry. Update every link to `#decision-8--no-default--true-marker` to the new anchor `#decision-8--no-default-attribute`. Update DoD items 1 and 6 to drop the "no `default = True` marker" wording in favor of "no `default` attribute at any value." Update the Test plan example list to include `default = False` as an additional example of an edit the test would catch.
  - **Informational #2 (pytest idiom commitment)**: the rev3 Test plan described the consolidated negative-shape test as "iterating four keys" without committing to a pytest idiom. `pytest.mark.parametrize` would fan out to four pytest items (yielding 8 total: 4 positive + 4 parametrized negatives); a plain loop inside one test stays at one pytest item (yielding 5 total: 4 positive + 1 looped negative). The Implementation-plan table and DoD item 4 both say "5 tests." Without a pinned idiom, an implementer could choose `parametrize` and have the spec's "5 tests" count contradict pytest's collection output. Fix: add one sentence to the consolidated negative-shape test's mechanism description pinning the single-test loop idiom (one pytest item, NOT a `parametrize` fan-out) so the count is unambiguous.
  - **Informational #3 (Risks `ready()` adoption entry stale)**: the [Risks and open questions](#risks-and-open-questions) "Future-card `ready()` body adoption" entry still described the no-`ready()` enforcement mechanism as "the `\"ready\" not in __dict__` assertion" — the rev1 single-key shape, superseded by rev2 H2's consolidated four-key test. The rev3 reviewer flagged this as "not a finding" because risks-section guidance is forward-looking and a future-card author would adapt the pattern from the consolidated test anyway. Propagation-hygiene fix: update the Risks entry to name the consolidated test and describe the pattern as "removes `\"ready\"` from the iterated forbidden-key set" rather than "removes the `\"ready\" not in __dict__` assertion."
- **Revision 5** (post-rev4 review against [`docs/feedback.md`](feedback.md)) — one medium-severity correction plus two low-severity propagation cleanups against rev4's L3 (D100 citation) and L4 (Decision 8 broadening) landings; no architectural change:
  1. **M1**: the [Current state](#current-state) `conf.py` bullet at line 89 and the [Decision 4](#decision-4--no-readyhook-in-0_0_7) justification at line 273 both cited the `setting_changed`-vs-`AppConfig.ready()` rationale as living "in `conf.py`'s module docstring lines 163-168." Verified against the actual file: `conf.py:1-36` IS the module docstring and does not mention `AppConfig.ready()`; the cited rationale lives as `#`-prefixed **inline comments** at `conf.py:163-167`, immediately above the `setting_changed.connect(...)` call at line 168. The quoted prose is present in the file but at a structurally different location than the spec claimed. A reader following the citation would open `conf.py`, look for the module docstring near the top of the file, and find one that says nothing about `ready()`. This is also load-bearing for the spec's own reasoning: "Slice 1's AppConfig has no settings-related wiring to subsume" is justified by appealing to `conf.py`'s own documented rationale. Fix: correct both citation sites to "inline comments at `django_strawberry_framework/conf.py:163-167` (NOT in the module docstring, which is at lines 1-36)" so future maintainers know to look at the call-site comment block rather than the file header.
  2. **L1**: rev4 L4 broadened [Decision 8](#decision-8--no-default-attribute) from "no `default = True`" to "no `default` attribute at any value," updated the Borrowing-posture bullet, the Test plan example list, and DoD items 1 and 6 — but did NOT touch the [Edge cases](#edge-cases-and-constraints) "Multiple AppConfigs in `apps.py`" bullet at line 360, which still read "the explicit `default = True` marker becomes load-bearing." Beyond the stale wording, the rev4 L4 broadening introduced a substantive contradiction the propagation surfaces: a future card that adds a second `AppConfig` and sets `default = True` on one of them would not just declare the marker; it would ALSO need to remove `"default"` from the iterated forbidden-key set in `tests/test_apps.py`, otherwise the consolidated test fails. The Edge-cases bullet read as if only the marker declaration was required. Fix: rewrite the bullet to acknowledge the dual edit (declare `default = True` on one class AND remove `"default"` from the iterated set), mirroring the pattern the [Risks and open questions](#risks-and-open-questions) "Future-card `ready()` body adoption" entry already documents for `ready()`. Decision 8's rev4 L4 broadening pins the current test scope; a multi-AppConfig future explicitly relaxes that pin.
  3. **L2**: rev4 L3 named `D100` alongside `D101` in [Slice 1 checklist](#slice-checklist), [Decision 2](#decision-2--name--label--verbose_name-pinning), and the [Borrowing posture](#borrowing-posture) "forced divergences" sentence — but missed the [Problem statement](#problem-statement) prose at line 84, which still cited only `D101` ("plus a class docstring (required by `D101`) plus a module docstring"). The module docstring was presented as a stylistic addition with no rule citation while the class docstring carried the rule citation — exactly the asymmetry rev4 L3 was supposed to eliminate. A maintainer skimming the Problem statement (the spec's narrative entry point) could come away thinking the class docstring is gate-forced and the module docstring is taste, then "clean up" by deleting the module docstring and hitting `D100`. Fix: insert the symmetric `D100` citation — "plus a module docstring (required by `D100`) plus a class docstring (required by `D101`)" — to match the two-rule framing at Slice 1 lines 53-54, Decision 2 lines 226-227, and DoD item 1.
- **Revision 6** (post-rev5 build-readiness audit against [`docs/builder/BUILD.md`](builder/BUILD.md)) — two low-severity corrections surfaced while reading the spec end-to-end with the build pipeline in mind. The spec is otherwise ready to hand to Worker 0; these two fixes close the last propagation gap (rev4 L4 missed the Slice 1 checklist sub-bullet) and the only contradiction with BUILD.md's coverage policy (the rev1-rev5 Slice 3 final-gates wording would either run a forbidden coverage flag or invite a worker to assert coverage that is the CI's gate, not the worker's).
  1. **L1**: rev4 L4 broadened [Decision 8](#decision-8--no-default-attribute) to forbid `default` at any value (the consolidated negative-shape test asserts `"default" not in __dict__`, catching `True` / `False` / any value) and propagated the broadening to the Borrowing posture bullet, the Test plan example list, DoD items 1 and 6, and (via rev5 L1) the Edge cases "Multiple AppConfigs" bullet. But the [Slice 1 checklist](#slice-checklist)'s "Do NOT" sub-bullet at line 59 still enumerated only `ready()`, `default_auto_field`, and `label` — `default` was missing. Per [`docs/builder/BUILD.md`](builder/BUILD.md) line 225, Worker 0 copies the Slice checklist's sub-bullets **verbatim** into the build artifact's `### Spec slice checklist (verbatim)` section, and Worker 3 walks those boxes during review (a silently un-addressed sub-check is a Medium finding); a Worker 2 reading the checklist top-down would not see "do not declare default" written down. Fix: add `default` to the Slice 1 "Do NOT" sub-bullet alongside `ready()`, `default_auto_field`, and `label`, with an explicit note that it covers both `True` and `False` (per rev4 L4's broadening) and a [Decision 8](#decision-8--no-default-attribute) citation.
  2. **L2**: the [Slice 3 checklist](#slice-checklist) "Final gates" sub-bullet at line 72-76 said `uv run pytest passes with 100% package coverage (fail_under = 100)`, which conflicts with [`docs/builder/BUILD.md`](builder/BUILD.md) on two counts. (a) BUILD.md lines 98-111 ("Coverage is the maintainer's gate, not a worker's tool") explicitly forbids workers from running `pytest` with coverage flags; plain `uv run pytest` auto-applies `--cov` via `pytest.ini`, so Worker 2 / Worker 1 final verification running the bare command would trigger forbidden coverage. (b) BUILD.md line 549 says "the only `pytest`-side requirement is that the existing suite passes. Do NOT inspect or assert line coverage at this stage." Asserting "100% package coverage" is the CI / maintainer's gate (`pyproject.toml [tool.coverage.report] fail_under = 100`), not Worker 2's. Fix: change the bullet to `uv run pytest --no-cov` (matching BUILD.md line 539's final-test-run-gate shape), drop the "100% package coverage" assertion, and add an explicit one-liner noting that coverage enforcement is CI's job. Also annotated each per-pass gate (`ruff format`, `ruff check`) with the BUILD.md line that owns it (line 247) so a worker auditing the checklist can verify "is this the right gate at the right pass?" without cross-referencing.

## Key glossary references

Skim these [`docs/GLOSSARY.md`](GLOSSARY.md) entries first — they anchor the vocabulary used throughout the spec:

- [`Django AppConfig`](GLOSSARY.md#django-appconfig) — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 3](#slice-3--promotion--docs).
- [`finalize_django_types`](GLOSSARY.md#finalize_django_types) — the consumer-owned synchronization point that resolves pending relations; this card does NOT move that responsibility into `AppConfig.ready()` (see [Decision 4](#decision-4--no-readyhook-in-0_0_7)).
- [`DjangoType`](GLOSSARY.md#djangotype) — the package's primary public surface; consumer modules that declare `DjangoType`s are imported by the consumer's project, not by the `AppConfig` (see [Decision 4](#decision-4--no-readyhook-in-0_0_7)).
- [`ConfigurationError`](GLOSSARY.md#configurationerror) — not raised by anything in this card; mentioned here only so future-spec authors can see that `apps.py` is intentionally validation-free.

Project conventions to follow:

- [`AGENTS.md`](../AGENTS.md) — line 20 ("Add settings keys only when the feature that needs them lands; do not preemptively populate"); test placement at `tests/test_apps.py` per line 6's "tests/ (package tests, system-under-test is django_strawberry_framework itself)" rule paired with [`docs/TREE.md`](TREE.md) line 453's "`tests/test_<module>.py` (flat, at the root) — single-file Layer-3 module tests" mirror rule. **Note:** `AGENTS.md` line 21 prohibits `CHANGELOG.md` edits without explicit permission; [Slice 3](#slice-3--promotion--docs) grants that permission for this card's `[0.0.7]` `### Added` append.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — 100% coverage target.
- [`KANBAN.md`](../KANBAN.md) — card-ID format; column movement at Slice 3.
- [`docs/TREE.md`](TREE.md) — package layout; tests mirror source one-to-one; `apps.py` already appears in the target layout with the `[alpha]` tag (`docs/TREE.md:236`).

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total; this card is smaller than `spec-016` because there is no consumer-resolver dispatch matrix to test and no example-app boilerplate to remove.

- [ ] Slice 1: Module + `AppConfig` subclass
  - [ ] New flat module `django_strawberry_framework/apps.py` (placement decision: see [Decision 1](#decision-1--module-location--public-export)) housing `DjangoStrawberryFrameworkConfig`.
  - [ ] Implement `DjangoStrawberryFrameworkConfig(AppConfig)` with exactly **two class-level behavioral attributes** plus **two docstrings** (rev4 L2 — clarified from rev3's "four pieces of state" framing, which conflated module-scope and class-scope artifacts and undercut the documentation-vs-behavior distinction the negative-shape test relies on; the docstrings are documentation, not class state):
    - `name = "django_strawberry_framework"` — Django app-label source; matches the package directory name so `django.apps.apps.get_app_config(...)` resolves through the same string consumers type into `INSTALLED_APPS`.
    - `verbose_name = "Django Strawberry Framework"` — display name in the Django admin's "Sites" / "Apps" listings; matches the `README.md` title.
    - module docstring (one line) naming the module's purpose, e.g. `"""Django AppConfig — registers the package with Django's app loader so consumers can list it in INSTALLED_APPS and Django's check / signal hooks resolve against it."""` at the top of `apps.py`. **Required by ruff's `D100` rule** (rev4 L3 — `D100` "Missing docstring in public module" is in `pyproject.toml`'s `[tool.ruff.lint] select = [..., "D", ...]` and NOT in the `ignore` list; the per-file-ignores at `pyproject.toml:100-107` do not exempt `django_strawberry_framework/apps.py`). Do NOT suppress with `# noqa: D100` — the docstring IS the root-cause fix per [`AGENTS.md`](../AGENTS.md) line 4.
    - class docstring (one line) naming the class's purpose, e.g. `"""Register django-strawberry-framework with Django's app loader."""` directly under the `class DjangoStrawberryFrameworkConfig(AppConfig):` line. **Required by ruff's `D101` rule** (rev3 H1 — symmetric with `D100`; `D101` "Missing docstring in public class" is also in `select` and not ignored). Do NOT suppress with `# noqa: D101` — same root-cause posture as `D100`.
  - [ ] Do NOT implement `ready()` (per [Decision 4](#decision-4--no-readyhook-in-0_0_7)); do NOT set `default_auto_field` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)); do NOT set `label` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)); do NOT set `default` at any value — neither `default = True` nor `default = False` — per [Decision 8](#decision-8--no-default-attribute) (rev6 L1 — added to close the rev4 L4 propagation gap; the consolidated negative-shape test in Slice 2 catches `default` at any value, but this checklist sub-bullet — which Worker 0 copies verbatim into the build artifact per [`docs/builder/BUILD.md`](builder/BUILD.md) line 225 — must name the forbiddance directly so Worker 2 sees it when reading top-down).
  - [ ] Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py` (per [Decision 3](#decision-3--no-public-export)). The class is accessible at `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` for consumers who want to name it explicitly in `INSTALLED_APPS`, but Django's implicit single-AppConfig discovery means consumers writing `"django_strawberry_framework"` in `INSTALLED_APPS` get the explicit config without naming it.
- [ ] Slice 2: Tests
  - [ ] New test module `tests/test_apps.py` covering the four contracts pinned in [Test plan](#test-plan): importable from `django_strawberry_framework.apps`, subclass of `django.apps.AppConfig`, `name` / `verbose_name` attribute values, and Django registry pickup (`django.apps.apps.get_app_config("django_strawberry_framework")` returns an instance of `DjangoStrawberryFrameworkConfig`).
  - [ ] One **consolidated** negative-shape test (rev2 H2): assert that `DjangoStrawberryFrameworkConfig.__dict__` contains none of the four **behavioral** keys this spec forbids — `"ready"` (per [Decision 4](#decision-4--no-readyhook-in-0_0_7)), `"label"` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)), `"default_auto_field"` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)), and `"default"` (per [Decision 8](#decision-8--no-default-attribute)). Mechanism: a single test function (one pytest item, NOT a `pytest.mark.parametrize` four-way fan-out — pinning this here so the "5 tests" count in [Implementation plan](#implementation-plan) and [Definition of done](#definition-of-done) matches pytest's collection output) that loops over `{"ready", "label", "default_auto_field", "default"}` and asserts `key not in DjangoStrawberryFrameworkConfig.__dict__` for each, with a fail message naming the offending key and the Decision that forbids it. Checks the class body explicitly, not the inherited base attributes which are always present. **The implicit `__doc__` key (populated by the class docstring required per rev3 H1) is NOT in the forbidden set** — "no extra AppConfig attributes" means no extra **behavioral** class attributes, not "no class docstring"; `__doc__` is documentation, not behavior, and is mandated by ruff's `D101`. If a future card relaxes any of the four forbidden keys, that card's spec updates this test in the same slice. Folding all four forbidden keys into one test (rather than four separate tests) keeps Slice 2's count compact and means the test name (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) names the contract — "exactly the two behavioral attributes pinned in Decision 2 plus the class / module docstrings required by D101; nothing more" — instead of the failure mode.
- [ ] Slice 3: Promotion + docs
  - [ ] Flip [`Django AppConfig`](GLOSSARY.md#django-appconfig) from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`](GLOSSARY.md); update the Index table's status column.
  - [ ] Update [`docs/README.md`](README.md) (rev3 L1 — replaced the rev1 generic "move the mention" wording with the surgical rev2 H1 actions; the entry-point checklist must match the [Doc updates](#doc-updates) section instead of relying on it to override): (a) **bump the shipped-list heading** at line 89 from `**Shipped today** (`0.0.6`):` to `**Shipped today** (`0.0.7`):` (catch-up against `DONE-016`'s heading-drift; distinct from the version-string bump deferred to [Decision 6](#decision-6--joint-0_0_7-cut)); (b) add the `Django AppConfig` bullet to that section with the wording in [Doc updates](#doc-updates); (c) **surgically remove only `, Django `AppConfig`** from the existing `Coming in 0.1.0` bullet at line 112, leaving `- schema export management command` intact for `WIP-ALPHA-018-0.0.7` to remove later (do NOT remove the whole line; do NOT remove the schema-export half).
  - [ ] Update [`docs/TREE.md`](TREE.md) — add `apps.py # AppConfig` to the **current on-disk layout** section under the `django_strawberry_framework/` tree (alphabetical position between `__init__.py` and `conf.py`). Remove the `[alpha]` tag from the existing `apps.py # [alpha] Django AppConfig` line in the **target package layout** section (line `docs/TREE.md:236`); the tag means "lands before `0.1.0`", and the bullet has now landed. Add `tests/test_apps.py` to the current test-tree section under the `tests/` listing.
  - [ ] Update [`KANBAN.md`](../KANBAN.md) — move `DONE-017-0.0.7` to the Done column with the next `DONE-NNN-0.0.7` id; rewrite the body in past tense per the existing Done-column convention.
  - [ ] Update [`CHANGELOG.md`](../CHANGELOG.md) — **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10 — every `0.0.7` card under the joint cut appends to the same shared section): `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through the package's AppConfig.
  - [ ] No edits to [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md). Justification: the AppConfig is plumbing, not a consumer-visible API surface. `README.md`'s status section names features consumers write code against; `GOAL.md`'s six-file example does not exercise `INSTALLED_APPS`; `TODAY.md`'s capability snapshot is about what GraphQL queries work — none of those framings is touched by the AppConfig landing.
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 6](#decision-6--joint-0_0_7-cut)): see [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion.
  - [ ] Final gates (rev6 L2 — aligned with [`docs/builder/BUILD.md`](builder/BUILD.md)'s "Coverage is the maintainer's gate, not a worker's tool" rule at BUILD.md lines 98-111 and the final test-run gate's `uv run pytest --no-cov` shape at BUILD.md line 539; rev1-rev5 prose said plain `uv run pytest` with "100% package coverage" assertion, which would either auto-apply `--cov` via `pytest.ini` and run forbidden coverage, or invite a worker to assert coverage that is the CI / maintainer's gate, not the worker's):
    - [ ] `uv run ruff format .` passes (Worker 2's per-pass gate per BUILD.md line 247).
    - [ ] `uv run ruff check --fix .` passes (Worker 2's per-pass gate per BUILD.md line 247).
    - [ ] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per BUILD.md line 109's "the only permitted coverage-shaped flag." Coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's; workers verify the suite passes, not that coverage stays at 100%.
    - [ ] Zero new public exports (the AppConfig is import-time plumbing, not a public symbol); `__all__` in `django_strawberry_framework/__init__.py` is unchanged.

## Problem statement

`django_strawberry_framework` does not ship an [`apps.py`](../django_strawberry_framework/) today. The example project's `examples/fakeshop/config/settings.py:48` already lists `"django_strawberry_framework"` in `INSTALLED_APPS`, and the example runs — but only because Django falls back to an implicit `AppConfig` synthesized from the package name when no explicit `apps.py` is found. That implicit `AppConfig`:

- carries the package's directory name as the `name` and `label`, with the same string as `verbose_name` — capitalized via Django's title-cased default ("Django Strawberry Framework"-ish but driven by Django's heuristic, not by the package),
- cannot be referenced by an explicit dotted path in `INSTALLED_APPS` (consumers who want the canonical Django pattern `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"` cannot type it),
- gives the package no hook for future Django-integration work (a `ready()` site for a check, a signal handler, or — in a future card — schema-export bootstrap).

The asymmetry is small but real: `strawberry_django` ships an [`apps.py`](/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py) (verified to be a four-line `class StrawberryDjangoConfig(AppConfig)` with `name` and `verbose_name`); the upstream `graphene_django` does NOT ship one (verified via `find` against `~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/` — no `apps.py`). The package's positioning argument in [`README.md`](../README.md) — "feels like `graphene-django` evolved onto a modern engine" — would currently match graphene-django's absence; the package's other half — "Strawberry stays as the engine" — would currently miss the parity with `strawberry-django`. This card ships the AppConfig so the parity is symmetric.

The shipping bar is intentionally low — the AppConfig is two behavioral attributes (`name`, `verbose_name`) plus a module docstring (required by `D100`) plus a class docstring (required by `D101`) (rev5 L2 — rev4 L3's symmetric-citation goal landed in Slice 1, Decision 2, and Borrowing posture but missed the Problem statement; both docstrings are gate-forced, not stylistic, and the symmetric `D100` / `D101` framing belongs at the spec's narrative entry point too). The discipline the card needs to enforce is **what NOT to put in it**: no `ready()` body, no preemptive settings, no eager imports of `DjangoType` modules, no auto-call to [`finalize_django_types`](GLOSSARY.md#finalize_django_types). Each of those is a future-spec home (or, for `finalize_django_types`, an explicit anti-pattern — the consumer owns the synchronization point per [`docs/README.md`](README.md)'s "Schema setup boundary" section).

## Current state

- `django_strawberry_framework/` ships the modules listed in [`docs/TREE.md`](TREE.md) lines 188-224 (`__init__.py`, `conf.py`, `exceptions.py`, `list_field.py`, `registry.py`, `scalars.py`, the `optimizer/`, `types/`, and `utils/` subpackages) and `py.typed`. There is no `apps.py` on disk today; the target layout at `docs/TREE.md:236` lists `apps.py # [alpha] Django AppConfig` with the `[alpha]` tag meaning "lands before `0.1.0`".
- `django_strawberry_framework/conf.py` ships the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader. It documents (in **inline comments** at `django_strawberry_framework/conf.py:163-167`, NOT in the module docstring — the module docstring at lines 1-36 covers settings access, the defensive-`None` stance, and the `setting_changed` signal contract, but does not mention `AppConfig.ready()` as a non-viable home; the rationale lives as `#`-prefixed comments immediately above the `setting_changed.connect(...)` call at line 168) that `setting_changed` signal wiring is installed at **import time**, NOT in `AppConfig.ready()`, because "consumers may import `conf` before app loading during test bootstrap, so AppConfig.ready() is not a viable home for this wiring." Slice 1's `AppConfig` therefore has no settings-related wiring to subsume — the signal hook is intentionally outside `ready()` and stays there.
- `examples/fakeshop/config/settings.py:48` already declares `"django_strawberry_framework"` in `INSTALLED_APPS`. Django currently synthesizes an implicit `AppConfig` because no `apps.py` is found. Once Slice 1 lands, Django picks up the explicit `DjangoStrawberryFrameworkConfig` automatically (the implicit fallback applies only when no `AppConfig` subclass is defined in the package; Django 3.2+ resolves a single explicit AppConfig as the default without requiring `default = True`).
- `tests/base/test_init.py:35-44` pins the package's `__all__` tuple. The AppConfig is NOT a public export (see [Decision 3](#decision-3--no-public-export)); this assertion stays unchanged in `0.0.7`.
- `tests/test_list_field.py` is the existing model for a flat single-file Layer-3 module's test home. `tests/test_apps.py` follows the same convention per [`docs/TREE.md:453`](TREE.md).
- `examples/fakeshop/test_query/test_library_api.py` exercises the live `/graphql/` endpoint with the package installed via `INSTALLED_APPS`. The test suite already proves the implicit `AppConfig` works end-to-end; once Slice 1 lands, the same tests exercise the explicit `AppConfig` without code changes (the test file imports `from django.test import Client` and posts JSON to `/graphql/`, which has no AppConfig-specific assertions).
- `DONE-017-0.0.7`'s `KANBAN.md` card body (lines 78-88) is intentionally sparse — three Definition-of-done bullets and no "Why it matters" narrative. The narrative this spec carries (parity with `strawberry-django`, asymmetry with `graphene-django`, future-card seam) is fleshed out here so the spec can stand on its own.

## Goals

1. Ship `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Two class-level behavioral attributes plus a one-line module docstring (required by `D100`, rev4 L3) and a one-line class docstring (required by `D101`, rev3 H1); the docstrings are documentation, not behavior, and are exempt from the negative-shape iteration accordingly (rev4 L2). Nothing else.
2. Ship `tests/test_apps.py` containing the four-test plan in [Test plan](#test-plan) — importability, subclass, attribute pinning, Django registry pickup — plus the one consolidated negative-shape test (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) asserting that none of `{"ready", "label", "default_auto_field", "default"}` are defined on the class (rev2 H2 — rev1 had a single-key `ready`-only test; rev2 folds in `label`, `default_auto_field`, and `default` so the "what NOT to put in AppConfig" discipline is enforced, not review-only).
3. Preserve [`AGENTS.md`](../AGENTS.md) line 20's "Add settings keys only when the feature that needs them lands; do not preemptively populate" by omitting `ready()`, `default_auto_field`, and any signal / check / management-command wiring. Future cards add what they need; this card adds the bare AppConfig.
4. Preserve the consumer's import order — the AppConfig must NOT eagerly import `DjangoType` modules or call [`finalize_django_types`](GLOSSARY.md#finalize_django_types). The synchronization-point contract documented in [`docs/README.md`](README.md)'s "Schema setup boundary" stays with the consumer.
5. Keep `__all__` unchanged. The AppConfig is import-time plumbing; consumers reach it via Django's app-loader machinery, not via `from django_strawberry_framework import ...`.

## Non-goals

- `ready()` body — checks, signals, management-command auto-registration, or `finalize_django_types` invocation. See [Decision 4](#decision-4--no-readyhook-in-0_0_7).
- A `default_auto_field` declaration. The package ships zero Django models; the attribute is meaningless here. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).
- Auto-invocation of [`finalize_django_types`](GLOSSARY.md#finalize_django_types) from `AppConfig.ready()`. The consumer's `config/schema.py` (or equivalent) owns the call; `ready()` fires before the consumer's schema module is necessarily imported, so a `ready()`-side call would either finalize too early (relations from yet-to-import modules unresolved) or be silently ineffective.
- A re-export of `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py`. Django's app-loader resolves the class through its dotted module path; consumers never write `from django_strawberry_framework import DjangoStrawberryFrameworkConfig`. See [Decision 3](#decision-3--no-public-export).
- A custom `label` shorter than `"django_strawberry_framework"`. The Django default (the last segment of `name`) is already unique. See [Decision 2](#decision-2--name--label--verbose_name-pinning).
- A bootstrap helper for `DJANGO_STRAWBERRY_FRAMEWORK` settings defaults. `conf.py` already handles missing-key and `None` cases; no `ready()`-side initialization is needed. AGENTS.md line 20 explicitly forbids preemptive settings.
- A Django management command surface. Tracked under `WIP-ALPHA-018-0.0.7` (the `export_schema` command), which has its own `management/commands/export_schema.py` module and does NOT need this card's AppConfig to do any wiring (Django discovers management commands by directory convention, not by AppConfig method).
- An update to `examples/fakeshop/config/settings.py:48`'s `INSTALLED_APPS` entry — current text is `"django_strawberry_framework"` (the dotted package name). Django's implicit single-AppConfig discovery means this entry continues to work unchanged; no need to tighten to `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"`. See [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change).

## Borrowing posture

The two reference packages at the paths given in [`docs/TREE.md`](TREE.md) take opposite stances on shipping an `apps.py`. The slice borrows the shape from the one that ships it.

### From `strawberry_django` — borrow the AppConfig shape verbatim

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py` (referenced from [`docs/TREE.md:78-158`](TREE.md)).

Verified contents (four lines plus blank):

```python
from django.apps import AppConfig


class StrawberryDjangoConfig(AppConfig):
    name = "strawberry_django"
    verbose_name = "Strawberry django"
```

- **AppConfig subclass with two attributes.** Same shape adopted here: `name` (the package directory) and `verbose_name` (a human-readable label). Justification: strawberry-django's shape is the minimal Django-correct surface for an installable package; the upstream has shipped this for years without needing more. Borrowing the shape verbatim avoids inventing complexity that the ecosystem has not asked for. **Two forced divergences** (rev4 L3 — bumped from "one" to "two" after auditing both pydocstyle rules): this repo's pydocstyle gate (`pyproject.toml [tool.ruff.lint] select = [..., "D", ...]`) enables both `D100` ("Missing docstring in public module") and `D101` ("Missing docstring in public class"); neither is in the ignore list. The upstream `strawberry_django/apps.py` has neither a module docstring nor a class docstring. We add one of each; see [Decision 2](#decision-2--name--label--verbose_name-pinning).
- **No `ready()`.** strawberry-django does not implement one; we do not either. Justification: `ready()` is the place where Django expects side effects (signal connections, model checks); strawberry-django has none that need `ready()`, and neither does this package at `0.0.7`. AGENTS.md line 20 makes this explicit on the settings side; the same posture applies to AppConfig hooks.
- **No `default_auto_field`.** strawberry-django does not declare one; neither do we. Justification: both packages ship zero Django models; the attribute is irrelevant.

### From `graphene_django` — explicitly do not borrow the absence

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/` (referenced from [`docs/TREE.md:13-76`](TREE.md)).

- **graphene-django ships NO `apps.py`** (verified by `find … -name apps.py` over the installed package directory; no result). Consumers add `"graphene_django"` to `INSTALLED_APPS` and rely on Django's implicit AppConfig fallback.
- **We do not borrow this.** Justification: graphene-django's implicit-only stance is a historical artifact of the package predating Django 3.2's AppConfig-discovery improvements. Modern Django convention is to ship an explicit `AppConfig`; the parity story consumers expect coming from `strawberry-django` is on the explicit-AppConfig side; and the future-card seam (a `ready()` site reserved for later cards) only opens with an explicit class.

### Explicitly do not borrow

- strawberry-django's broader `apps/` / `extensions/` / `middleware/` structure that surrounds its `apps.py`. We ship just the AppConfig in `0.0.7`; the surrounding modules land card-by-card under their own specs ([`KANBAN.md`](../KANBAN.md) — `TODO-ALPHA-029` debug-toolbar, etc.).
- Any `verbose_name` translation infrastructure (`from django.utils.translation import gettext_lazy as _`). strawberry-django does not localize its string; we do not either. Translation is a separate concern; deferring it costs nothing.
- Django's `default` class attribute (at any value — `True`, `False`, or other). Django 3.2+ resolves a single explicit AppConfig in a package as the default without the marker; declaring it at any value would be either redundant (`True`) or self-defeating (`False`). See [Decision 8](#decision-8--no-default-attribute) (rev4 L4 — broadened from the rev1-rev3 "`default = True` class attribute" naming).

## User-facing API

The shipped consumer surface in `0.0.7` adds exactly one new module (`django_strawberry_framework/apps.py`) containing one new class (`DjangoStrawberryFrameworkConfig`). The class is NOT added to `__all__`; consumers reach it through Django's app-loader, not through the package's import surface.

### Default usage — `INSTALLED_APPS` by package name

```python path=null start=null
# Consumer's Django settings module
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    # ... other Django apps ...
    "django_strawberry_framework",
    # Consumer's own apps:
    "apps.my_app",
]
```

Django's app loader scans `django_strawberry_framework/apps.py`, finds exactly one `AppConfig` subclass (`DjangoStrawberryFrameworkConfig`), and uses it as the package's `AppConfig` automatically. No change to consumer code is required compared to the implicit-AppConfig behavior they had under `0.0.6`; the explicit class is what changes.

### Explicit dotted path (optional, equivalent)

Consumers who prefer to be explicit can name the AppConfig directly:

```python path=null start=null
INSTALLED_APPS = [
    "django.contrib.admin",
    # ...
    "django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig",
]
```

Equivalent to the package-name form above. The package documentation recommends the package-name form in [`docs/README.md`](README.md) for brevity, but both work.

### `django.apps.apps.get_app_config("django_strawberry_framework")`

After Django finishes app-loading, the AppConfig is reachable through Django's registry under the `name` value `"django_strawberry_framework"`:

```python path=null start=null
from django.apps import apps

config = apps.get_app_config("django_strawberry_framework")
# -> <DjangoStrawberryFrameworkConfig: django_strawberry_framework>
config.verbose_name
# -> "Django Strawberry Framework"
```

This is the path future cards will use when they need to attach behavior to the package's AppConfig (e.g., the schema-export management command in `WIP-ALPHA-018-0.0.7` could resolve here, though Django's command discovery does not require it). Pinning the resolution path now means future cards do not have to re-litigate the lookup string.

## Architectural decisions

### Decision 1 — Module location & public export

**Module location.** `DjangoStrawberryFrameworkConfig` lives in **`django_strawberry_framework/apps.py`** (new flat single-file module at the package root, matching the [`docs/TREE.md`](TREE.md) target layout at line 236).

Justification:

- The card's KANBAN body (lines 78-88) names `django_strawberry_framework/apps.py` as the single new source file.
- [`docs/TREE.md:236`](TREE.md) already reserves this path with the `[alpha]` tag — Slice 3 removes the tag once the file lands.
- Django's app-loader expects `apps.py` at the package root by convention. Putting it anywhere else (`apps/config.py`, `_apps.py`, etc.) breaks the convention without benefit.

**Public-export surface.** `django_strawberry_framework/__init__.py` is NOT modified. See [Decision 3](#decision-3--no-public-export).

Alternatives considered (and rejected):

- **`django_strawberry_framework/django/apps.py` mimicking `strawberry/django/apps.py`'s nested shape.** Rejected: the `strawberry/django/` nesting reflects Strawberry's broader package layout where Django integration is one of many transport / adapter targets. This package's entire purpose is Django integration; an extra `django/` subdirectory would be redundant.
- **A `django_strawberry_framework/apps/__init__.py` subpackage.** Rejected: a single AppConfig class does not need a subpackage. [`docs/TREE.md:230`](TREE.md) reserves subpackages for Layer-3 subsystems with three-plus modules.

### Decision 2 — `name` / `label` / `verbose_name` pinning

The class declares exactly **two class-level behavioral attributes** plus its inherited base behavior; the module and class docstrings are documentation (not behavior) and are accordingly exempt from the negative-shape iteration set (rev4 L2):

- `name = "django_strawberry_framework"` — matches the package directory; matches the `INSTALLED_APPS` entry consumers already type; matches the string `examples/fakeshop/config/settings.py:48` already declares.
- `verbose_name = "Django Strawberry Framework"` — Title Case with spaces; matches the `README.md` H1; matches the human-readable form a consumer would type if asked "what is this package called?".

Documentation (gate-forced, not behavioral):

- Module docstring (one line) at the top of `apps.py` — required by ruff's `D100` rule (rev4 L3; same `pyproject.toml [tool.ruff.lint] select = [..., "D", ...]` gate as `D101`; not in the ignore list).
- Class docstring `"""Register django-strawberry-framework with Django's app loader."""` (or equivalent one-liner) directly under the class statement — required by ruff's `D101` rule (rev3 H1).

Both docstrings diverge from strawberry-django's `apps.py` (which has neither) because this repo's pydocstyle gate is stricter than the upstream's; both divergences are forced by the gate, not chosen for stylistic reasons.

Deliberately NOT declared:

- `label = "..."` — Django's default `label` is the last segment of `name` (here, `"django_strawberry_framework"`). The default is unique within any conceivable consumer project and matches the lookup string in `django.apps.apps.get_app_config(...)`. Declaring a custom `label` (e.g., `"dsf"`) would (a) introduce a second lookup string consumers have to learn, and (b) silently invalidate any future `manage.py` command that the package or a third party writes against the `django_strawberry_framework` label. Symmetric with strawberry-django's choice to omit `label`.
- `default_auto_field = "..."` — see [Decision 5](#decision-5--no-default_auto_field-and-no-models).

Justification:

- Two behavioral attributes is the entire surface strawberry-django ships (the upstream `apps.py` has no module docstring and no class docstring — see [Borrowing posture](#borrowing-posture)); the borrowing posture matches the upstream's **behavioral** shape exactly. The two docstrings here are additive, forced by this repo's stricter pydocstyle gate per rev3 H1 / rev4 L3 — the **documentation** shape diverges from the upstream as the [Borrowing posture](#borrowing-posture) section calls out, but the **behavioral** shape is identical (rev4 L1 — rewrote from rev3's stale "Three pieces of state" claim, which both misstated rev3's own pinned shape and overstated the upstream's surface).
- Every attribute the spec adds is one the test plan has to pin; every attribute that doesn't ship is one the spec doesn't have to defend.
- The `verbose_name` value diverges from strawberry-django's `"Strawberry django"` (lowercase second word) because the `README.md` and consumer-facing prose uses Title Case throughout. The string is cosmetic and would be the source of a future cosmetic fix if we got it wrong; the test plan pins it so the choice is durable.

Alternatives considered (and rejected):

- **`verbose_name = "django-strawberry-framework"` (kebab-case to match the PyPI distribution name).** Rejected: the Django admin's "Apps" listing renders the `verbose_name` directly; kebab-case is unergonomic for a UI string.
- **`verbose_name = _("Django Strawberry Framework")` with `gettext_lazy`.** Rejected: the package does not declare a translation surface; adding `gettext_lazy` here would pull `django.utils.translation` into the import graph for no benefit. If the package ever exposes localized strings, a follow-up card does this consistently across every site.
- **Add a `label = "dsf"` shortcut.** Rejected: aliasing is gratuitous when the default is already unique; consumers benefit from the longer label matching the package name 1:1 (no "wait, what's the label vs the name?" friction).

### Decision 3 — No public export

`django_strawberry_framework/__init__.py` is NOT modified. The class is reachable at the dotted path `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig`; consumers never write `from django_strawberry_framework import DjangoStrawberryFrameworkConfig`.

Justification:

- Django's app-loader resolves AppConfigs through their dotted module path, not through any `__init__.py` re-export. The class never appears in consumer code that isn't `INSTALLED_APPS`.
- `tests/base/test_init.py:35-44` pins `__all__`; adding a name to `__all__` for something consumers never `import` would be a noise-only API widening.
- Symmetric with strawberry-django, which also does not re-export its `StrawberryDjangoConfig`.

Alternatives considered (and rejected):

- **Re-export anyway for consistency with other `0.0.7` cards.** Rejected: spec-016's [`DjangoListField`](GLOSSARY.md#djangolistfield) is re-exported because consumers `import` it directly into their schema code; the AppConfig is not in that category.
- **Re-export under a friendlier name like `Config`.** Rejected: a top-level `Config` symbol in a Django GraphQL framework would be ambiguous with a dozen other "Config" concepts (Django settings, Strawberry config, etc.).

### Decision 4 — No `ready()` hook in `0.0.7`

`DjangoStrawberryFrameworkConfig.__dict__` MUST NOT contain a `ready` key. The class inherits `AppConfig.ready` (a no-op on the base) and does not override it.

Justification:

- [`AGENTS.md`](../AGENTS.md) line 20 — "Add settings keys only when the feature that needs them lands; do not preemptively populate" — generalizes naturally to AppConfig hooks. There is no shipped feature in `0.0.7` that needs a `ready()` body.
- `finalize_django_types` is the only obvious candidate for a `ready()`-side call, and the consumer-owned synchronization-point contract documented in [`docs/README.md`](README.md)'s "Schema setup boundary" section makes that explicitly the wrong place for it. `ready()` fires after Django's app registry is populated but **before** the consumer's `config/schema.py` (or equivalent) is necessarily imported; calling `finalize_django_types` from `ready()` would either finalize too early (relations from not-yet-imported modules unresolved → `ConfigurationError`) or — if Django happened to import the schema module first via signal cascades — be silently redundant with the consumer's explicit call. Both shapes are footguns.
- The `conf.py` signal-receiver hookup is **already** outside `ready()` and the inline comments at `conf.py:163-167` (rev5 M1 — the rev1-rev4 wording said "module docstring (lines 163-168)" which was wrong on two counts: the module docstring is actually at lines 1-36 and doesn't mention `ready()`; the cited rationale lives as `#`-prefixed comments immediately above the `setting_changed.connect(...)` call at line 168) document the rationale: "consumers may import `conf` before app loading during test bootstrap, so AppConfig.ready() is not a viable home for this wiring." The settings-side anti-pattern is pinned; the same logic applies here.
- Future cards that need `ready()` (e.g., a Django check that validates a `DjangoType` declaration constraint, a signal handler for model deletion that flushes a registry cache) add the hook in the same change as the feature that needs it. The Slice 2 consolidated negative-shape test (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) iterates `{"ready", "label", "default_auto_field", "default"}` and asserts each is absent from `DjangoStrawberryFrameworkConfig.__dict__`; Decision 4's `"ready"` absence is one of the four keys exercised by that test (rev3 L3 — updated from the rev1/rev2 prose that still cited a single-key `assert "ready" not in ... __dict__` assertion, which was superseded by the rev2 H2 consolidation but not propagated here).

The negative-shape test is the load-bearing part of this Decision; without it, a future drive-by edit could add `def ready(self): pass` (a "harmless" placeholder) and the package would silently develop a side-effect surface no card sanctioned.

Alternatives considered (and rejected):

- **Define `ready()` as an explicit `pass` body for "future flexibility."** Rejected: `pass`-body methods are the canonical anti-pattern AGENTS.md line 20 warns against. Future cards add the body when they need it; until then, the inherited no-op is fine.
- **Define `ready()` to call `finalize_django_types()`.** Rejected: contradicts the documented synchronization-point contract; would break consumers whose `config/schema.py` imports relation modules in a different order than Django's app loader does.
- **Define `ready()` to register a `django.core.checks` check that validates `DjangoType` declarations.** Rejected: even if a useful check existed, this card is not the home for it. The check has its own design surface (what does it warn about? what's the error message? does it gate `manage.py runserver`?) that needs its own spec.

### Decision 5 — No `default_auto_field` and no models

`DjangoStrawberryFrameworkConfig` does NOT declare `default_auto_field`. The package ships zero Django models; the attribute is meaningless.

Justification:

- `default_auto_field` controls the auto PK type for models declared *inside* the AppConfig's package. `django_strawberry_framework/` declares no `models.py`; no model anywhere in the package directory tree.
- Future cards that add models (none on the current roadmap; `BACKLOG.md` does not propose any either) would revisit this attribute alongside that decision.
- Symmetric with strawberry-django, which also does not declare it.

### Decision 6 — Joint `0.0.7` cut

`0.0.7` ships four WIP cards as a bundle per [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10 (excluding the already-shipped `DONE-016-0.0.7`): `DONE-017-0.0.7` (this card), `WIP-ALPHA-018-0.0.7` (schema-export management command), `WIP-ALPHA-019-0.0.7` (multi-db cooperation contract), and `WIP-ALPHA-020-0.0.7` (warning-free scalar registration). The version bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

Justification:

- Restates [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10 verbatim so this card's reader does not have to chase the cross-spec reference.
- Per [`KANBAN.md`](../KANBAN.md) line 50: "The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`." The cross-card policy is already pinned in the KANBAN; this Decision pulls it into the spec so Slice 3's checklist can reference it.
- The CHANGELOG `[0.0.7]` `### Added` entries accumulate across the four remaining cards' Slice 3-equivalents; each card writes its own Added line under the same `[0.0.7]` heading.

The Slice 3 doc-updates list explicitly excludes the version bump.

Alternatives considered (and rejected):

- **This card bumps `0.0.7` because it ships earlier than 018/019/045.** Rejected: ship order is determined by which card a maintainer picks up next, not by card NNN; pinning the bump to a specific card creates a sequencing constraint that has no engineering justification.
- **Add a separate `TODO-ALPHA-XXX-0.0.7 — 0.0.7 release cut` card to KANBAN that owns the bump.** Rejected: out of scope for this spec (the spec's boundary forbids editing `KANBAN.md` outside the column move in Slice 3); the "last card to ship" policy is workable as-is.

### Decision 7 — No fakeshop `INSTALLED_APPS` entry change

`examples/fakeshop/config/settings.py:48` currently declares `"django_strawberry_framework"` (the dotted package name, not the AppConfig dotted path). Slice 1 does NOT change this entry.

Justification:

- Django's implicit single-AppConfig discovery (Django 3.2+) resolves the package-name form to the explicit `DjangoStrawberryFrameworkConfig` automatically once `apps.py` ships.
- Changing the fakeshop entry to `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"` would (a) churn a settings file that has no other reason to change in this slice, and (b) advertise the explicit-dotted-path form as the recommended one — but the User-facing API section recommends the package-name form for brevity, and the example should match the recommendation.
- The existing live `/graphql/` HTTP tests in `examples/fakeshop/test_query/test_library_api.py` continue to exercise the package's `INSTALLED_APPS` path; once `apps.py` lands, those tests are the end-to-end evidence that the explicit AppConfig works through the same entry string the implicit one did.

Alternatives considered (and rejected):

- **Switch fakeshop to the dotted-path form to demonstrate the explicit pattern.** Rejected per the rationale above; the spec User-facing API already mentions the dotted-path form as an equivalent option, which is enough documentation. Cluttering the example settings is unnecessary.
- **Add a new test in `examples/fakeshop/tests/` that asserts the resolved AppConfig is `DjangoStrawberryFrameworkConfig`.** Rejected: the assertion belongs in `tests/test_apps.py` (package-internal, system-under-test is the package itself). An example-project test would be a coverage detour through fakeshop's Django machinery when the package's own test can pin the contract directly.

### Decision 8 — No `default` attribute

`DjangoStrawberryFrameworkConfig` does NOT declare `default` at all (neither `default = True` nor `default = False`). The consolidated negative-shape test enforces this by asserting `"default" not in DjangoStrawberryFrameworkConfig.__dict__`; that scope matches `default = True`, `default = False`, and any other value (rev4 L4 — broadened from the rev1-rev3 "No `default = True` marker" framing, which named only the truthy value while the test caught the attribute at any value; the broader Decision now matches the test's actual scope and is symmetric with [Decision 2](#decision-2--name--label--verbose_name-pinning) / [Decision 4](#decision-4--no-readyhook-in-0_0_7) / [Decision 5](#decision-5--no-default_auto_field-and-no-models), every other forbidden-key Decision of which forbids the attribute outright rather than a specific value).

Justification:

- Django 3.2+ resolves a single explicit `AppConfig` subclass in a package's `apps.py` as the default automatically, without requiring the marker (the `True` case).
- `default = False` would be self-defeating in this context — declaring "this AppConfig is NOT the default" while shipping the only AppConfig in the package contradicts Django's implicit resolution. Forbidding both prevents the self-defeating shape from creeping in defensively.
- The package will only ever declare one `AppConfig` (there is no use case for two within the same package directory), so the disambiguation that an explicit `default` provides is irrelevant.
- Symmetric with strawberry-django, which does not declare `default` either (any value).

Alternatives considered (and rejected):

- **Set `default = True` defensively in case a future Django version changes the implicit-default behavior.** Rejected: Django's `AppConfig` discovery rules have been stable since 3.2 (2021) and Django's deprecation policy would announce any change with multi-version warning. Defending against an unannounced change is over-engineering.
- **Narrow the Decision to `default = True` only (rev1-rev3 wording).** Rejected by rev4 L4: the consolidated negative-shape test catches `default` at any value, so the Decision either had to widen to match the test or the test had to narrow to match the Decision. Widening the Decision is the lower-friction fix and is consistent with the surrounding "forbid the attribute outright" Decisions.

## Implementation plan

The slice ships as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all three into a single PR is acceptable given the small surface.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Module + `AppConfig` subclass | `django_strawberry_framework/apps.py` (new) | 0 (tests land in Slice 2) | `+10 / -0` |
| 2 — Tests | `tests/test_apps.py` (new) | 5 (4 positive + 1 consolidated negative-shape covering four forbidden keys per rev2 H2; see [Test plan](#test-plan)) | `+60 / -0` |
| 3 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` | 0 | `+25 / -8` |

Total expected delta: ~95 lines across the three slices.

The three slices must be authored in order. Slice 2 depends on Slice 1 (the class must exist before tests can import it); Slice 3 depends on Slice 2 (the CHANGELOG `### Added` line and `KANBAN.md` Done body must describe a shipped, tested module, not a half-landed one).

## Edge cases and constraints

- **Django 3.2+ AppConfig discovery.** The package's `pyproject.toml:29` already pins `Django>=5.2` (rev3 L2 — corrected from the rev1/rev2 stale `>= 4.2` citation); Django's "explicit single AppConfig becomes the default" behavior has been in place since 3.2, well below the floor. The spec assumes this and does not include a fallback for older Django versions.
- **`INSTALLED_APPS` ordering.** Django processes `INSTALLED_APPS` top-to-bottom for `ready()` dispatch. Because this card adds no `ready()` body, ordering relative to other apps in the consumer's `INSTALLED_APPS` is irrelevant; any position works.
- **Multiple AppConfigs in `apps.py`.** Not a concern in `0.0.7` (only one class is declared) but worth noting for future cards: if a second AppConfig is ever added (for some reason), the explicit `default = True` marker on one of the classes becomes load-bearing, AND the consolidated negative-shape test in `tests/test_apps.py` must be updated in the same change — the future card's spec removes `"default"` from the iterated forbidden-key set `{"ready", "label", "default_auto_field", "default"}` (the rev4 L4 broadening of [Decision 8](#decision-8--no-default-attribute) forbids `default` at any value, which is the right pin for the single-AppConfig present but blocks the multi-AppConfig future) AND adds `default = True` to one of the AppConfig classes. This mirrors the pattern documented in the [Risks and open questions](#risks-and-open-questions) "Future-card `ready()` body adoption" entry: a future card that needs to declare a currently-forbidden attribute removes the key from the iterated set in the same change it adds the attribute. Decision 8's rev4 L4 broadening pins the current test scope; a multi-AppConfig future explicitly relaxes that pin (rev5 L1 — rev1-rev4 wording named only the `default = True` half without acknowledging the test-update requirement that rev4 L4's broadening introduced).
- **`django.apps.apps.get_app_config("dsf")` (or any other label shortcut).** Returns `LookupError` — the resolution string is `"django_strawberry_framework"` (the value of `name` / `label`), not an alias. Pinned in the test plan so a future drive-by `label = "dsf"` edit fails the test.
- **AppConfig instantiation under `pytest-django`.** `pytest-django` sets up Django's app registry once per session via `django.setup()`; the AppConfig is instantiated as part of that bootstrap. Tests in `tests/test_apps.py` can rely on the registry being populated and use `apps.get_app_config(...)` directly.
- **`AppConfig.ready` is called during `django.setup()`.** Because this card defines no `ready()`, Django's inherited no-op runs and the test session proceeds. No timing concerns.
- **Re-importing `django_strawberry_framework.apps` outside Django.** A pure-Python `import django_strawberry_framework.apps` is legal — the module just defines a class. `django.apps.AppConfig` is the only Django dependency (already present because the package's other modules import Django ORM types). No new dependency surface.
- **Coverage of the AppConfig under `fail_under = 100`.** The class body has two attribute assignments and a docstring; the test plan's importability + attribute pinning + registry pickup covers every line. The consolidated negative-shape test (four forbidden keys absent from `__dict__`, per rev2 H2) is a class-level assertion, not a body-line coverage assertion, so the class body's coverage is earned by the four positive tests.

## Test plan

Tests live in one tree, matching the rules in [`docs/TREE.md`](TREE.md) and [`AGENTS.md`](../AGENTS.md). Test-tree placement is mandatory.

### `tests/test_apps.py` (new)

Package tests; system-under-test is `django_strawberry_framework`. The file is the flat single-file module's mirror per [`docs/TREE.md:453`](TREE.md).

Positive tests (Slice 2):

- `test_djangostrawberryframeworkconfig_importable_from_apps_module` — `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig` resolves without `ImportError`. Pins the module path so a future move to `django_strawberry_framework/django/apps.py` or similar fails this test (and is caught before merging).
- `test_djangostrawberryframeworkconfig_is_appconfig_subclass` — `issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)` is `True`. Pins the inheritance so a refactor that accidentally inherits from a different base (e.g., `django.apps.config.AppConfig` via direct import, or a custom intermediate) is caught.
- `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name` — asserts `DjangoStrawberryFrameworkConfig.name == "django_strawberry_framework"` and `DjangoStrawberryFrameworkConfig.verbose_name == "Django Strawberry Framework"`. Pins both attribute values; a cosmetic edit to either is caught at test time.
- `test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` — calls `django.apps.apps.get_app_config("django_strawberry_framework")` and asserts the returned instance `isinstance(...)` of `DjangoStrawberryFrameworkConfig`. This is the load-bearing assertion that Django actually picked up the explicit class (not the implicit fallback). Without this test, the explicit AppConfig could silently fail to register and the implicit one could stand in.

Negative-shape test (Slice 2):

- `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` (rev2 H2) — iterates the four forbidden **behavioral** keys `{"ready", "label", "default_auto_field", "default"}` and asserts `key not in DjangoStrawberryFrameworkConfig.__dict__` for each, with a fail message naming the offending key and the Decision that forbids it. Pins the consolidated "exactly the two behavioral attributes pinned in Decision 2 plus the class / module docstrings required by `D101`; nothing more" contract — covering `ready` ([Decision 4](#decision-4--no-readyhook-in-0_0_7)), `label` ([Decision 2](#decision-2--name--label--verbose_name-pinning)), `default_auto_field` ([Decision 5](#decision-5--no-default_auto_field-and-no-models)), and `default` ([Decision 8](#decision-8--no-default-attribute)) in a single class-body contract assertion. The implicit `__doc__` key (populated by the class docstring required per rev3 H1) is intentionally NOT in the iterated set — "no extra AppConfig attributes" means no extra **behavioral** class attributes, not "no class docstring"; documentation is not behavior. If a future drive-by edit adds `def ready(self): pass`, `label = "dsf"`, `default_auto_field = "django.db.models.BigAutoField"`, or `default = True` (or `default = False`, per rev4 L4 — the test catches `default` at any value) — each violating its corresponding Decision — this test fails and the edit is caught before merge. Rev1 of this spec had a single-key `does_not_define_ready` test that pinned only one of the four; rev2 H2 folded the other three into the same test so the "what NOT to put in AppConfig" discipline is exercised, not review-only.

No live `/graphql/` HTTP test is required. The `examples/fakeshop/test_query/test_library_api.py` suite already exercises the package through `INSTALLED_APPS` end-to-end; once `apps.py` lands, those tests continue to pass through the explicit AppConfig with zero modifications. Adding an HTTP test specifically for the AppConfig would be a coverage detour — the AppConfig's job is to register; the registry test above pins that contract directly.

No example-project test is required either. The system-under-test is the package's AppConfig; the package-internal test home is canonical.

## Doc updates

- [`docs/GLOSSARY.md`](GLOSSARY.md)
  - Flip [`Django AppConfig`](GLOSSARY.md#django-appconfig) from `planned for 0.0.7` to `shipped (0.0.7)`.
  - Update the entry body to describe the shipped contract: `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; no `ready()` body in `0.0.7`; consumers list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's implicit single-AppConfig discovery resolves the explicit class.
  - Update the Index table's status column for the row at line 52.

- [`docs/README.md`](README.md)
  - **Bump the shipped-list heading** at line 89 from `**Shipped today** (`0.0.6`):` to `**Shipped today** (`0.0.7`):` (rev2 H1). The current file still carries the `0.0.6` heading even though `DONE-016-0.0.7` shipped (it annotated the new `DjangoListField` bullet inline with "(new in `0.0.7`)" without bumping the section heading); this card bumps the heading to reflect that the section now covers `0.0.7` content. The heading bump is a documentation-state catch-up, distinct from the version-string bump in [Decision 6](#decision-6--joint-0_0_7-cut) which still belongs to the last `0.0.7` card to ship — the `pyproject.toml` / `__version__` / `tests/base/test_init.py` values stay at `0.0.6` after this card's Slice 3.
  - Add a bullet to that section: "`Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`)."
  - **Surgically remove only `, Django `AppConfig`` from the existing `Coming in 0.1.0` bullet at line 112** so the line becomes `- schema export management command` (rev2 H1). Do NOT remove the entire line and do NOT remove the `schema export management command` half — `WIP-ALPHA-018-0.0.7` is the card that owns the schema-export removal, and is explicitly out of scope here (see [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)). When `WIP-ALPHA-018-0.0.7` ships, its Slice 3 removes the remaining `schema export management command` text from that bullet (deleting the whole bullet at that point if nothing else remains).

- [`docs/TREE.md`](TREE.md)
  - Add `apps.py # AppConfig` to the **current on-disk layout** section under the `django_strawberry_framework/` tree (lines 192-224 of the current file). Alphabetical position: between `__init__.py` and `conf.py`.
  - Remove the `[alpha]` tag from the existing `apps.py # [alpha] Django AppConfig` line in the **target package layout** section (line 236) — the tag means "lands before `0.1.0`", and the bullet has now landed.
  - Add `tests/test_apps.py` to the current test-tree section (lines 329-360 of the current file). Position: **before `test_list_field.py`** (alphabetical — `test_apps.py` sorts before `test_list_field.py`; rev2 L1 corrected the rev1 wording which incorrectly said "between `test_list_field.py` and `test_registry.py`").

- [`KANBAN.md`](../KANBAN.md)
  - Move `DONE-017-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope: "Shipped `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; no `ready()` body in `0.0.7` (deferred to the card that needs one); package-internal tests at `tests/test_apps.py`."
  - Update the `### In progress` summary paragraph (line 50) to remove `DONE-017-0.0.7` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`](../CHANGELOG.md)
  - **Append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading — the repo's `CHANGELOG.md` already has a `[0.0.7]` section from `DONE-016-0.0.7` and other prior `0.0.7` commits; every `0.0.7` card under the joint cut appends to the same shared section per [Decision 6](#decision-6--joint-0_0_7-cut)): `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`. Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`; Django's check / signal hooks resolve through the package's AppConfig. No `ready()` body in `0.0.7`.
  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 6](#decision-6--joint-0_0_7-cut), NOT this slice.
  - [`AGENTS.md`](../AGENTS.md) line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`](../README.md). Justification: the README's status section is consumer-prose ("public names are stable; correctness and edge-case behavior are still hardening"); the AppConfig is plumbing, not a consumer-name surface change. The features the README does name (`DjangoListField`, the optimizer, `DjangoType`) are the user-facing primitives; the AppConfig is the registration plumbing underneath. If a future maintainer disagrees, the change is one-line and can be added later without revising this spec.

- No edits to [`GOAL.md`](../GOAL.md). Justification: `GOAL.md`'s `astronomy` showcase walks through model definitions, schema, filters, orders, aggregates, fieldsets — none of which exercises `INSTALLED_APPS` directly. The example project does declare `INSTALLED_APPS`, but `GOAL.md` is the framing document, not the example.

- No edits to [`TODAY.md`](../TODAY.md). Justification: `TODAY.md` is a query-shape-and-capability snapshot ("what GraphQL queries work in fakeshop today?"). The AppConfig is not a query-shape change; the fakeshop schema is unchanged by this card.

## Risks and open questions

Each item names a preferred answer for `0.0.7` and a fallback if implementation reveals the preferred answer is wrong.

- **Django's implicit single-AppConfig discovery edge cases.** Preferred answer: Django 3.2+'s "exactly one `AppConfig` subclass in `apps.py` becomes the default" behavior is stable; the consumer's `INSTALLED_APPS` entry `"django_strawberry_framework"` resolves to `DjangoStrawberryFrameworkConfig` without any further declaration. Fallback: if a real-world Django configuration is found where the discovery silently picks a different class (e.g., a consumer who installs both this package and a fork in the same project, with overlapping app names), document the explicit-dotted-path form (`"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"`) as the disambiguation recipe in `docs/README.md`. The User-facing API section already names this form as an equivalent option, so the fallback is already documented; the risk is purely whether the package-name form continues to work as the recommended shape.
- **`verbose_name` cosmetic drift.** Preferred answer: `"Django Strawberry Framework"` matches the `README.md` H1 and is pinned by `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name`. Fallback: if a future rebrand changes the project's display name (unlikely on the road to `1.0.0`), the test and the AppConfig change in the same edit; nothing in the package's public surface depends on the verbose_name string.
- **Future-card `ready()` body adoption.** Preferred answer: no card needs `ready()` in the current roadmap; the no-`ready()` test stays. Fallback: when a future card needs `ready()` (e.g., a check that warns when `DjangoType`s are declared after `finalize_django_types()` and surfaces it through `manage.py check`), the consolidated negative-shape test in `tests/test_apps.py` (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) is updated in that card's spec. The pattern: a card adding `ready()` removes `"ready"` from the iterated forbidden-key set `{"ready", "label", "default_auto_field", "default"}` (per rev2 H2 / rev4 — the test catches four keys, not just `ready`) AND adds a positive test for whatever the new `ready()` body does. Both edits are in the same change. (Updated from the rev1-rev3 wording "removes the `\"ready\" not in __dict__` assertion AND adds a positive test" — the single-key shape that wording described was superseded by the consolidated test in rev2 H2; informational item 3 of the rev3 review flagged the propagation gap.)
- **Last-card-to-ship version bump policy.** Preferred answer: the last of the four remaining `0.0.7` WIP cards (017, 018, 019, 045) to merge owns the bump, per [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10. Fallback: identical to spec-016 — if real merge sequencing is unclear, a separate `KANBAN.md` edit (out of scope here per the spec boundary) adds an explicit release-cut card; this spec does not author that edit.

## Out of scope (explicitly tracked elsewhere)

- [Schema export management command](GLOSSARY.md#schema-export-management-command) (`manage.py export_schema`): `WIP-ALPHA-018-0.0.7` in [`KANBAN.md`](../KANBAN.md). The command's discovery happens through Django's `management/commands/` directory convention, not through this card's AppConfig; the two cards are independent.
- [Multi-database cooperation](GLOSSARY.md#multi-database-cooperation) contract: `WIP-ALPHA-019-0.0.7` in [`KANBAN.md`](../KANBAN.md). The cooperation is in `types/resolvers.py`, not in `apps.py`; the two cards are independent.
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `WIP-ALPHA-020-0.0.7` in [`KANBAN.md`](../KANBAN.md). The scalar map is consumer-facing schema-construction shape, not AppConfig surface.
- Django checks for `DjangoType` declaration invariants (e.g., warn when a relation target is unimported at finalization time). Not on the current roadmap; a future card would land its own AppConfig `ready()` body in tandem with the check's implementation.
- Channels ASGI router ([`DjangoGraphQLProtocolRouter`](GLOSSARY.md#djangographqlprotocolrouter)): `TODO-ALPHA-029` for `0.0.12`.
- [Debug-toolbar middleware](GLOSSARY.md#debug-toolbar-middleware): `TODO-ALPHA-031` for `0.0.12`.
- [Response-extensions debug middleware](GLOSSARY.md#response-extensions-debug-middleware): `TODO-ALPHA-032` for `0.0.12`.
- Test-client helpers ([`TestClient`](GLOSSARY.md#testclient), [`GraphQLTestCase`](GLOSSARY.md#graphqltestcase)): `TODO-ALPHA-033` for `0.0.12`.
- `default_auto_field` declaration: not on the roadmap; the package ships no Django models. See [Decision 5](#decision-5--no-default_auto_field-and-no-models).

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/apps.py` exists and defines `DjangoStrawberryFrameworkConfig(AppConfig)` per [Decision 1](#decision-1--module-location--public-export) and [Decision 2](#decision-2--name--label--verbose_name-pinning) — `name = "django_strawberry_framework"`, `verbose_name = "Django Strawberry Framework"`, a one-line **module docstring** (required by ruff's `D100` per rev4 L3), a one-line **class docstring** (required by ruff's `D101` per rev3 H1), no `label` override, no `default_auto_field`, no `ready()` body, no `default` attribute at any value (rev4 L4).
2. `django_strawberry_framework/__init__.py` is NOT modified (per [Decision 3](#decision-3--no-public-export)). `__all__` is unchanged.
3. `tests/base/test_init.py`'s `__all__` assertion is unchanged (per [Decision 3](#decision-3--no-public-export)).
4. `tests/test_apps.py` exists and contains the 5 tests listed in the [Test plan](#test-plan) — 4 positive (importable, subclass, attribute pinning, registry pickup) + 1 consolidated negative-shape (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) asserting `{"ready", "label", "default_auto_field", "default"}` are all absent from `DjangoStrawberryFrameworkConfig.__dict__` per rev2 H2.
5. `examples/fakeshop/config/settings.py:48` is NOT modified (per [Decision 7](#decision-7--no-fakeshop-installed_apps-entry-change)). The existing `"django_strawberry_framework"` entry continues to work through Django's implicit single-AppConfig discovery, now resolving to the explicit class.
6. The class does not implement `ready()`, does not declare `label`, does not declare `default_auto_field`, and does not declare `default` at any value (per [Decision 2](#decision-2--name--label--verbose_name-pinning), [Decision 4](#decision-4--no-readyhook-in-0_0_7), [Decision 5](#decision-5--no-default_auto_field-and-no-models), [Decision 8](#decision-8--no-default-attribute) respectively; rev4 L4 broadened Decision 8 from "no `default = True`" to "no `default` attribute" to match the test's actual scope). All four absences are pinned by the consolidated `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` in `tests/test_apps.py` (rev2 H2 — rev1 only tested the `ready` absence; the other three were review-only until rev2 folded them into the same test).
7. The fakeshop live `/graphql/` HTTP tests at `examples/fakeshop/test_query/test_library_api.py` continue to pass unmodified — the explicit AppConfig is exercised through the existing `INSTALLED_APPS` entry without code changes elsewhere.
8. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
9. `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the [Doc updates](#doc-updates) section. `docs/README.md`'s shipped-list heading is bumped from `(0.0.6)` to `(0.0.7)` per rev2 H1; only `, Django `AppConfig`` is removed from the `Coming in 0.1.0` bullet at line 112 (the `schema export management command` half stays until `WIP-ALPHA-018-0.0.7` ships). `README.md`, `GOAL.md`, and `TODAY.md` are NOT edited.
10. `KANBAN.md` moves `DONE-017-0.0.7` to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope.
11. The version bump is NOT in this card per [Decision 6](#decision-6--joint-0_0_7-cut); the last `0.0.7` card to ship owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion.
12. Zero new public exports — `__all__` is unchanged.
13. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest --no-cov` passes (rev6 L2 — explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per [`docs/builder/BUILD.md`](builder/BUILD.md) line 109; coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`, not this slice's; workers verify the suite passes, not that coverage stays at 100%).
