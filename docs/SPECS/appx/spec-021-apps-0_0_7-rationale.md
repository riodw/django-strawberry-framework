# Rationale: spec-021 — `apps.py` and Django `AppConfig` (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-021-apps-0_0_7.md`][spec-021]. The spec is the contract and states only what holds at `HEAD`; everything that explains **how it got there** lives here: six numbered revisions of review feedback, the alternatives each of the eight Decisions rejected, the four risks and how each resolved, and every claim the spec once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, run late — the card shipped in `0.0.7` and the extraction never ran at the time, so this file and the spec-vs-code reconciliation beside it were performed in one round.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** Spec-021 carried its whole deliberative layer inline: a 26-line `Revision history (kept inline so the spec is self-contained)` block enumerating six review rounds with their H / M / L sub-items and two "Informational" follow-ups, **53** `(revN Xn)` attribution parentheticals in the body outside that block (measured across 34 lines; `grep -oiE 'rev[0-9]+ [HML][0-9]+'` over lines 35-513 at `HEAD`), a standalone `Justification:` block under **all eight** Decisions, an `Alternatives considered (and rejected):` list under **seven** of them (Decision 5 has none), four inline `Justification:` clauses in `## Borrowing posture`, and a four-item `## Risks and open questions` section written as preferred-answer / fallback pairs.

**Measured byte counts.** Two corpora, both obtainable by a later reader: the spec at commit `51eb47ba` (`git show 51eb47ba:docs/SPECS/spec-021-apps-0_0_7.md | wc -c`) and both files as they stand at the end of this round (`wc -c docs/SPECS/spec-021-apps-0_0_7.md docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`).

| File | At `51eb47ba` | At the end of this round |
|---|---|---|
| `docs/SPECS/spec-021-apps-0_0_7.md` | 97,518 | 65,342 |
| `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` | 0 (did not exist) | 85,169 |

The spec shed 32,176 bytes (`97518 - 65342`). **This file is larger than that, by 52,993 bytes** (`85169 - 32176`), and the surplus is not padding: this file is not only a destination. It also carries what no passage in the spec ever contained — the 31-site reconciliation table and its population derivation under [Decision 4](#decision-4--ready-applies-the-upstream-patches), the four-commit chronology behind that inversion, the count corrections the round measured against its own build plan, the citation sweep above, and the [`## Claims the spec may no longer make`](#claims-the-spec-may-no-longer-make) / [`## Left open by this pass`](#left-open-by-this-pass) apparatus.

The move alone does **not** account for the shed, and in the opposite direction: some of the 32,176 bytes went nowhere. The `(revN Xn)` attributions are attributions, not arguments — an entry recording *what* a round changed carries that round once, not once per touched sentence — and sentences that only repeated a contract stated elsewhere in the spec, and passages the shipped code falsifies, were **deleted** rather than moved, per [`worker-1.md`][worker-1] rule 2. Every figure in this section is a `wc -c` reading taken after the last edit of the round that wrote it, and the shed appears twice in this section by design — a byte count of a file the pass is still writing is a guess, and a corrected figure whose twin two lines away is left alone is worse than either.

`HEAD` at the time of the pass is `51eb47ba`. The package is at `0.0.14`; this card shipped at `0.0.7` on 2026-05-27.

**The card shipped as `017`, not `021`.** The spec was authored as `docs/spec-017-apps-0_0_7.md`; the 2026-07-30 board renumber moved the card from `017` to `021` and renamed the spec. `CHANGELOG.md`'s tracking label still reads `017-appspy_and_django_app_config-0.0.7`, and the spec's own link-definition block still carried a `[spec-016]` ref-id pointing at the post-renumber `spec-020-list_field-0_0_7.md` filename (see [`## Renumber residue`](#-renumber-residue)). Both numbers name one card.

**Moved** — cut from the spec by this pass, and now only here:

- the whole `Revision history (kept inline so the spec is self-contained)` block, all six revisions with their H / M / L sub-items and the two "Informational" entries under revision 4;
- every `(revN Hx)` / `(revN Mx)` / `(revN Lx)` attribution parenthetical in the spec body — 53 of them, and the change each one records is now in this file under the decision or section it touched;
- the standalone `Justification:` block under Decisions 1, 2, 3, 4, 5, 6, 7 and 8;
- the `Alternatives considered (and rejected):` list under Decisions 1, 2, 3, 4, 6, 7 and 8;
- the whole `## Risks and open questions` section and its four items.

**Reconciled in place** — the contract sentence stays in the spec and only its chronology, or a superseded claim, was rewritten:

- **`## Borrowing posture`'s four inline `Justification:` clauses.** The reasoning is the borrowing decision itself — why this package copies strawberry-django's shape and declines graphene-django's absence — so it stays in the spec; only the `Justification:` label and the round attributions were cut. The "No `ready()`" bullet is the one whose content changed; see [Decision 4](#decision-4--ready-applies-the-upstream-patches).
- **The positive arguments under each Decision.** Where a `Justification:` block argued *for* the decision rather than against an alternative, its bullets were re-set as plain body prose under the Decision. A reader of the spec still gets the reason; what left is the label, the chronology and the rejected side.
- **`## Doc updates`' four "No edits to X. Justification: …" clauses were KEPT with their label.** They are build obligations — a builder must know which files not to touch and why — not deliberation about the decision.

**Kept in the spec deliberately, against the pull of this move.** [`worker-1.md`][worker-1]'s carve-out for implementation-relevant rationale is load-bearing in three places here:

- **Why the `APPLY_UPSTREAM_PATCHES` gate lives inside each `apply()` rather than in `ready()`.** A reader of `ready()` sees three unguarded calls; without the sentence saying the gate is per dependency, the obvious "cleanup" is to hoist an all-or-nothing gate into the dispatcher and silently retire the mapping form.
- **Why `ready()` is the wrong home for `finalize_django_types`.** The ordering argument (registry populated, consumer schema module not necessarily imported) is what stops the next author adding the call; without it the Non-goal reads as taste.
- **Why the `ready()` dispatch test must revert the patched slots before driving `ready()`.** An assertion that the patches are installed, made without the revert, is satisfied by any earlier direct `apply()` on the same worker and pins nothing. That is a test-construction instruction, not deliberation.

**In-page anchors in this file slug the heading's rendered text, not its source.** The Decision headings here are reference-style — a bracketed link label followed by its ref-id — so the rendered heading, and therefore the anchor, is the link text alone. Two shapes the whole-file sweep exists to catch: a heading whose text ends in a ref-id, whose slug would then cover the label only; and a heading whose text is a code span beginning with `##`, whose slug keeps a leading hyphen (`#-doc-updates`). The sweep is run over **this** file as well as the spec, and it is a postcondition, not a precondition — the spec carried three anchors that never resolved before this pass (below).

**Glossary anchors: twelve terms, twelve anchors, all still linked** (`scripts/check_spec_glossary.py` exits 0 before and after). One term lost its only carrier to this move and was re-homed in reconciled prose:

- **[`DjangoListField`][glossary-djangolistfield]** was carried only by Decision 3's rejected alternative "Re-export anyway for consistency with other `0.0.7` cards". Re-homed as a normative bullet in Decision 3: the two sibling cards take opposite export decisions from the same rule, and the discriminator is whether consumers write the symbol into their own code by hand.

**Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the shipped code or the current tree falsifies them:

- `Status: draft (revision 6, post-rev5 build-readiness audit).` — the card shipped in `0.0.7` and the spec is archived under `docs/SPECS/`. Replaced with the shipped status line.
- **Everything asserting that `apps.py` ships no `ready()`.** That is the whole of [Decision 4](#decision-4--ready-applies-the-upstream-patches) below, and it reached 30 further sites — the population is defined and enumerated in that entry's table. A false sentence belongs in neither file; the chronology of how it became false is recorded here instead.
- **The `docs/README.md` heading-bump and surgical-removal instructions.** They prescribed edits against a file structure that no longer exists: `docs/README.md`'s shipped list is now headed `(0.0.14)` and the `Coming in 0.1.0` bullet is gone entirely, retired by later cards. The obligation itself was satisfied — the `Django AppConfig` bullet is present at `docs/README.md #"`Django AppConfig` — `django_strawberry_framework/apps.py` ships"` — so the spec now states the obligation and not the vanished mechanics.
- **`docs/TREE.md`'s `[alpha]`-tag removal instruction and the `apps.py # Django AppConfig` citation behind it.** The tag is gone and the line now reads `apps.py                       # Django ``AppConfig`` - registers the package and applies its upstream patches at app load.`, so the `#"apps.py                  # Django AppConfig"` substring citation resolved nowhere. The bullets now name the two `docs/TREE.md` section headings, which do resolve.
- **Three further citations that no longer resolved**, all rewritten to resolving forms: `django_strawberry_framework/conf.py #"Library settings."` (the module docstring's first line is now `Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.`); `docs/TREE.md #"single-file Layer-3 module tests"` and `docs/TREE.md #"once it earns 3+ files"` (neither string survives in the regenerated `docs/TREE.md`; both now cite `## Test layout` / `## django_strawberry_framework (current on-disk layout)`).
- **The `Django>=5.2` pin restatement.** `pyproject.toml` pins `Django>=5.2.16`. The `#"Django>=5.2"` citation still resolves as a substring, so it was kept; the prose that repeated the pin as `Django>=5.2` was corrected to the real floor.

**Citation sweep over the whole spec, all forms — including the bracketed-path form a bare-path sweep skips.** Two corpora, stated because a citation count is meaningless without one, and both obtainable by a later reader. **At `51eb47ba` the spec carried 68 `#"substring"` occurrences** (`git show 51eb47ba:docs/SPECS/spec-021-apps-0_0_7.md | grep -o '#"' | wc -l` -> 68; 53 of them outside the `Revision history` block this round moved, by the same command through `sed -n '34,513p'`), **of which 23 resolved and 45 did not.** **At the end of this round the spec carries 36 occurrences, 29 resolving and 7 not** (same command on the current file -> 36). Each occurrence was resolved against the cited file on disk across all three syntactic shapes in use: bare path, a backtick span wrapping the whole citation, and a reference-style link to the file followed by the citation, which a pattern anchored on a literal path never matches. The population fell because the move took the deliberative layer and its citations with it, and what left was overwhelmingly broken: failures went 45 -> 7 while resolving citations went 23 -> 29. The 7 survivors, and the 7 repaired inside this file, are the two classes below.

- **Seven were `AGENTS.md` paraphrase citations — a repo-wide convention, repaired repo-wide at the maintainer's direction after this round's final gate.** `AGENTS.md` is written without periods and is reworded freely, so specs cite its *rules* rather than its bytes: `#"Add settings keys only when the feature that needs them lands"` (x3), `#"Do not update CHANGELOG.md unless explicitly instructed"` (x2), `#"Test placement: three test trees with no overlap"`, and `#"always recommend the root-cause fix over the surface patch"`. The class is repo-wide, and its size depends entirely on how the corpus is drawn, so what is published here is the **corpus rule**, not a size. **Corpus: every `.md` file under `docs/SPECS/`, `appx/` included; every `#"…"` occurrence whose target — taken from the preceding bare path, or from the ref-id resolved through that file's own link-definition block — is `AGENTS.md`; occurrences and distinct substrings counted separately; "resolves" means the substring occurs verbatim in `AGENTS.md`.** Run it and the class turns up in most of the archived specs, a majority of the occurrences concentrated in a handful of `0.0.7` and `0.0.8` files. No digit is published with it, and the omission is deliberate: four independent sweeps in this round's review chain, run within a day of each other, returned four different occurrence-and-file pairs, because two `docs/SPECS/` files are being rewritten by a concurrent session while the corpus is counted and because line-wrapped citations fold differently under different extractors. A digit measured over a corpus somebody else is editing rots on their commit; the rule survives it. What the class is **not** is uniformly broken: at least the ruff-gate spelling this round introduced as a repair below occurs in `AGENTS.md` verbatim, so "not one of them resolves" is false and must not be restated. Defining the class as "the citations that fail" would make its own non-resolution true by construction; it is defined here by target instead. Every file in it but this cohort's two was outside this cohort; the maintainer authorized the repo-wide repair after the final gate, and every `AGENTS.md`-targeted anchor in the corpus now resolves verbatim (re-run the corpus rule above to verify — the postcondition is zero non-resolving occurrences, not a count).
- **Seven were genuinely stale inside this file, and are repaired.** `#"The spec's nested sub-bullets for this slice from `## Slice checklist`, copied verbatim"` cited the right text at the wrong file — it lives in `docs/builder/ARTIFACT.md`, and is now cited there. The two ruff-gate citations named an `ARTIFACT.md` line since rewritten to `<files this pass touched>`; both now cite `AGENTS.md #"`uv run ruff format .` and `uv run ruff check --fix .` after every edit"`, which carries the commands literally. `KANBAN.md #"### DONE-021-0.0.7 — `apps.py` and Django app config"` (x2) missed because the rendered heading is bracketed and hyphenated, not em-dashed; the substring is now `DONE-021-0.0.7 - `apps.py` and Django app config`. `KANBAN.md #"`0.0.7` is the active patch"` was version-scoped prose that rots every release — the board reads `0.0.14` now — and cites the stable `#"### In progress"` heading instead. The seventh, `KANBAN.md #"The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10"`, quoted a sentence that is not in `KANBAN.md` and never was; the policy belongs to [`spec-020`][spec-020]'s Decision 10, which Decision 6 now links directly instead of quoting a `KANBAN.md` string.

The same sweep over **this** file finds its `#"…"` occurrences to be overwhelmingly *quotations* of the spec's citations rather than citations of its own — that is what a change record does — so no resolve/fail ratio over this file is quoted here: it would measure quotation, not citation, and the digits would say nothing about this file's own claims. It makes exactly **three** citations in its own voice — `docs/README.md #"`Django AppConfig` — `django_strawberry_framework/apps.py` ships"`, `KANBAN.md #"`0.0.7` shipped 2026-05-27 with seven cards"` and `pyproject.toml #"Django>=5.2"` — and all three resolve, each verified directly (`grep -c` on `docs/README.md`, `KANBAN.md` and `pyproject.toml` returns 1 for its substring). Every other `#"…"` here is a quotation of a citation the spec once carried or still carries.

## Entries keyed to the spec

Every entry below names the spec section or Decision it belongs to. An entry that names no decision cannot be looked up.

### The `Status:` line

Shipped as `Status: draft (revision 6, post-rev5 build-readiness audit).` and stayed that way through archival, through the `0.0.7` release on 2026-05-27, and through seven further releases. Revision 6 was itself a "build-readiness audit" — a pass whose stated purpose was to confirm the spec was ready to hand to Worker 0 — which is the strongest available evidence that a status line narrating a revision number is a line nobody re-reads as a claim. The replacement names the release, the date, the archival and the card, and carries no revision number.

### `Revision history`, revisions 1-6

The spec's own framing was "kept inline so the spec is self-contained". Six rounds, each an adversarial review of the prior draft.

**Revision 1 — initial draft.** Pinned module location (`django_strawberry_framework/apps.py`), the AppConfig subclass shape (`DjangoStrawberryFrameworkConfig`; `name`, `verbose_name`, no `label` override, no `default_auto_field`), **the deliberate omission of `ready()`** (no side effects until a shipped feature needs one — appealing to the `conf.py` posture in [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands"), test placement at `tests/test_apps.py`, a four-test plan (importable / subclass / attribute pinning / registry pickup), the policy that consumers add the package to `INSTALLED_APPS` by its dotted package name, the live-fakeshop coverage path (the example already lists the package; this card lands the explicit `AppConfig` underneath that entry without changing the entry text), the explicit deferral of the version bump to the last `0.0.7` card to ship, and the doc-updates list across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md` and `CHANGELOG.md` (no `README.md` / `GOAL.md` / `TODAY.md` updates).

**Revision 2 (post-rev1 review)** — two high, one low:

1. **H1** — rev1's Slice 3 `docs/README.md` instructions had two defects against the file as it then stood. (a) Rev1 said "add a bullet to the **Shipped today** (`0.0.7`) list", but the heading still read `(0.0.6)` because `DONE-020-0.0.7` had shipped its bullet with an inline "(new in `0.0.7`)" instead of bumping the heading — so the instruction named a heading that did not exist. (b) Rev1's removal instruction quoted a long `Coming in 0.1.0` bullet, but the real bullet was `- schema export management command, Django `AppConfig``, and the schema-export card was explicitly out of scope; following rev1 literally would have removed the schema-export half early and falsified the docs while that feature was still planned. Fix: split the bullet into (1) bump the heading `(0.0.6)` → `(0.0.7)`, distinct from the version-string bump owned by Decision 6, and (2) surgically remove only `, Django `AppConfig``. Both halves are now historical — see the **Deleted outright** list above.
2. **H2** — rev1's Slice 2 test plan named one negative-shape test (`does_not_define_ready`), while Decisions 2 / 4 / 5 / 8 forbade four distinct class-body keys and three of those absences had no test behind them. A drive-by `label = "dsf"`, `default_auto_field = …` or `default = True` would have passed the planned suite. Fix: rename the test to `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` and consolidate `{"ready", "label", "default_auto_field", "default"}` into one iteration with a fail message naming the offending key and its Decision. Collapsed three Definition-of-done items into one and renumbered the rest.
3. **L1** — the `docs/TREE.md` bullet placed `tests/test_apps.py` "between `test_list_field.py` and `test_registry.py` (alphabetical)", which is not alphabetical. Corrected to "before `test_list_field.py`".

**Revision 3 (post-rev2 review)** — one high, three low:

1. **H1** — the pinned shape said `name`, `verbose_name` and a module docstring, "nothing else", but the slice's own `uv run ruff check --fix .` gate enables pydocstyle's `D` family and does not ignore `D101` ("Missing docstring in public class"). A public class with no class docstring would have failed the required gate while following the spec exactly: the "exactly this shape" framing and the gate were mutually unsatisfiable. Fix: make a one-line class docstring part of the pinned shape, and forbid `# noqa: D101` as a workaround. Also clarified that the implicit `__doc__` is deliberately outside the negative-shape iteration set — documentation is not behavior.
2. **L1** — rev2 H1's surgical `docs/README.md` wording landed in `## Doc updates` but not in the Slice 3 checklist, which still carried rev1's generic "move the mention". An implementer reading the checklist top-down (the canonical entry point) would have over-removed. Fix: make the checklist and the detailed section say the same thing.
3. **L2** — the Edge-cases "Django 3.2+ AppConfig discovery" bullet cited `Django >= 4.2` as the pinned floor. The real pin was `Django>=5.2`. The conclusion was unaffected (5.2 is well above 3.2) but the citation would have sent a reader to verify the wrong constraint.
4. **L3** — Decision 4's justification still cited the rev1 single-key assertion `assert "ready" not in DjangoStrawberryFrameworkConfig.__dict__` after rev2 H2 had consolidated four keys into one test. Purely stale prose, but it could have convinced a future editor the single-key assertion still existed.

**Revision 4 (post-rev3 review)** — four low, plus two "Informational" follow-ups the rev3 reviewer flagged as non-findings. The Informational entries are numbered **#2 and #3 with no #1**; the numbering was inherited from the reviewer's own list and never re-based.

1. **L1** — Decision 2's justification claimed "Three pieces of state is the entire surface strawberry-django ships". Both halves were wrong: rev3 H1 had already bumped the spec's own pinned shape to four artifacts, and upstream `strawberry_django/apps.py` ships **two** attributes with no docstrings at all. Rewritten to "two behavioral attributes is the entire surface strawberry-django ships … the docstrings here are additive, forced by this repo's stricter pydocstyle gate."
2. **L2** — rev3's "four pieces of state" framing mixed class-scope artifacts (`name`, `verbose_name`, `__doc__`) with a module-scope one (the module docstring). Calling the module docstring "a piece of the class's state" was a category error, and the bundling undercut the documentation-vs-behavior distinction the negative-shape test relies on. Replaced everywhere with "two class-level behavioral attributes plus two docstrings".
3. **L3** — rev3 H1 cited `D101` for the class docstring but never named the symmetric `D100` for the module docstring, which is equally gate-forced. A maintainer reading the asymmetry could have deleted the module docstring believing it was preference, hit `D100`, and reached for `# noqa`. Fix: name `D100` beside `D101` at every site, forbid both suppressions, and bump the Borrowing posture's "one forced divergence" to two.
4. **L4** — Decision 8 (then titled "No `default = True` marker") forbade only the truthy value while the consolidated test asserted `"default" not in __dict__`, which catches any value. The test was broader than the Decision permitted, breaking the symmetry with Decisions 2 / 4 / 5. Fix: retitle to "No `default` attribute", forbid it at any value, and retarget every `#decision-8--no-default--true-marker` link.
- **Informational #2 (pytest idiom commitment)** — the consolidated test was described as "iterating four keys" with no idiom pinned. `pytest.mark.parametrize` would fan out to four pytest items (8 total); a plain loop stays one item (5 total). The Implementation-plan table and Definition of done both said "5 tests", so an implementer choosing `parametrize` would have made the spec's own count wrong. Fix: pin the single-test loop.
- **Informational #3 (Risks `ready()` entry stale)** — the Risks "Future-card `ready()` body adoption" entry still described the enforcement mechanism as "the `"ready" not in __dict__` assertion", the rev1 single-key shape superseded by rev2 H2. The rev3 reviewer called it a non-finding because a future author would adapt the consolidated pattern anyway; fixed as propagation hygiene.

**Revision 5 (post-rev4 review)** — one medium, two low:

1. **M1** — the `## Current state` `conf.py` bullet and Decision 4's `conf.py` justification both said the `setting_changed`-vs-`AppConfig.ready()` rationale lived "in `conf.py`'s module docstring", citing a line range that actually pointed inside `django_strawberry_framework/conf.py::reload_settings`'s docstring. Verified against the file: the module docstring does not mention `AppConfig.ready()` at all; the quoted rationale lives as `#`-prefixed **inline comments** immediately above the `setting_changed.connect(...)` call. A reader following the citation would have opened the file, read the header, and found nothing. Load-bearing, because "Slice 1's AppConfig has no settings-related wiring to subsume" rested on `conf.py`'s own documented reasoning. Fix: correct both citations to the call-site comment block. (This pass corrected the same citation a second time: the module docstring's first line has since been rewritten, so the `#"Library settings."` anchor rev5 M1 introduced no longer resolved either.)
2. **L1** — rev4 L4's Decision 8 broadening never reached the Edge-cases "Multiple AppConfigs in `apps.py`" bullet, which still read "the explicit `default = True` marker becomes load-bearing". The propagation surfaced a substantive gap: a future card adding a second AppConfig must ALSO remove `"default"` from the iterated forbidden-key set, or the consolidated test fails. Fix: state the dual edit.
3. **L2** — rev4 L3's symmetric `D100` citation landed in the Slice 1 checklist, Decision 2 and Borrowing posture but missed the `## Problem statement`, the spec's narrative entry point, where the class docstring carried a rule citation and the module docstring read as taste — exactly the asymmetry rev4 L3 existed to eliminate.

**Revision 6 (post-rev5 build-readiness audit against [`docs/builder/BUILD.md`][build])** — two low, both closing gaps a build pass would have hit:

1. **L1** — rev4 L4 broadened Decision 8 to any value and propagated to five sites, but the Slice 1 checklist's "Do NOT" sub-bullet still enumerated only `ready()`, `default_auto_field` and `label`. Since Worker 0 copies those sub-bullets **verbatim** into the build artifact and Worker 3 walks the boxes during review, a builder reading top-down would never have seen "do not declare `default`" written down. Fix: add it, with the both-values note and the Decision 8 citation.
2. **L2** — the Slice 3 "Final gates" sub-bullet said `uv run pytest passes with 100% package coverage (fail_under = 100)`, which conflicts with `BUILD.md` twice over: plain `uv run pytest` auto-applies `--cov` via `pytest.ini` and is forbidden to workers, and asserting coverage is the CI / maintainer's gate rather than a worker's. Fix: `uv run pytest --no-cov`, drop the coverage assertion, and annotate each per-pass gate with the `BUILD.md` clause that owns it.

### [Decision 1 — Module location & public export][spec-021-d1]

**Rejected alternatives.**

- **`django_strawberry_framework/django/apps.py`, mimicking `strawberry/django/apps.py`'s nested shape.** Rejected: the `strawberry/django/` nesting reflects Strawberry's broader layout, where Django integration is one of many adapter targets. This package's entire purpose is Django integration; an extra `django/` subdirectory would be redundant.
- **A `django_strawberry_framework/apps/__init__.py` subpackage.** Rejected: a single AppConfig class does not need a subpackage; `docs/TREE.md` reserves subpackages for Layer-3 subsystems with three or more modules.

**Changes, with the round that caused each.** None — the placement was pinned in revision 1 and no round touched it. This pass corrected only the `docs/TREE.md` citation behind it, which pointed at a line the TREE regenerate has since rewritten.

**Claims this decision may no longer make:** that `docs/TREE.md` carries `apps.py # [alpha] Django AppConfig`; that `apps.py` is reserved rather than landed.

### [Decision 2 — `name` / `label` / `verbose_name` pinning][spec-021-d2]

**Rejected alternatives.**

- **`verbose_name = "django-strawberry-framework"`** (kebab-case, matching the PyPI distribution name). Rejected: the Django admin's "Apps" listing renders `verbose_name` directly, and kebab-case is unergonomic as a UI string.
- **`verbose_name = _("Django Strawberry Framework")` with `gettext_lazy`.** Rejected: the package declares no translation surface, and adding `gettext_lazy` here would pull `django.utils.translation` into the import graph for no benefit. If the package ever exposes localized strings, a follow-up card does it consistently across every site.
- **A `label = "dsf"` shortcut.** Rejected: aliasing is gratuitous when the default is already unique, and consumers benefit from the label matching the package name 1:1 with no "what is the label vs the name?" friction.
- **"Three pieces of state" as the pinned surface** (rev1-rev3's framing). Retired by rev4 L1 and rev4 L2: it misstated the spec's own shape after rev3 H1 added the class docstring, and overstated the upstream's, which ships two attributes and no docstrings.

**The positive arguments** (the moved `Justification:` block) are body prose under the Decision in the spec and are not restated here — a rationale entry that repeats an argument the spec still carries makes the move a copy. Nothing in the block was left behind.

**Changes, with the round that caused each.** rev3 H1 added the class docstring as gate-forced (`D101`). rev4 L1 rewrote the stale "three pieces of state" justification. rev4 L2 replaced the "four pieces of state" framing with "two behavioral attributes plus two docstrings". rev4 L3 added the symmetric `D100` citation for the module docstring.

**Changed by R1 (rationale extraction + spec-vs-code reconciliation round, 2026-08-18) (F1).** The decision's lead-in said the class declares two behavioral attributes "plus its inherited base behavior". At `HEAD` it also overrides `ready()`, so the lead-in now names the override and points at Decision 4. Nothing about the two attributes moved.

**Claims this decision may no longer make:** that three pieces of state are pinned; that upstream `strawberry_django/apps.py` ships three attributes; that the class body is exhausted by two attributes and two docstrings.

### [Decision 3 — No public export][spec-021-d3]

**Rejected alternatives.**

- **Re-export anyway, for consistency with the other `0.0.7` cards.** Rejected: [`spec-020`][spec-020]'s [`DjangoListField`][glossary-djangolistfield] is re-exported because consumers `import` it directly into their schema code; the AppConfig is not in that category. This is the alternative whose glossary link the move re-homed — the discriminator ("does the consumer write the symbol by hand?") is now a normative bullet in the spec, because it is the rule the next card applies rather than a rejection.
- **Re-export under a friendlier name like `Config`.** Rejected: a top-level `Config` symbol in a Django GraphQL framework would be ambiguous with a dozen other "Config" concepts (Django settings, Strawberry config, and so on).

**Changes, with the round that caused each.** None; pinned in revision 1 and untouched by every later round. The decision is also the one the shipped code most straightforwardly confirms: `grep` over `django_strawberry_framework/__init__.py` finds no `apps` / `AppConfig` / `DjangoStrawberryFrameworkConfig` reference, and `__all__` is unwidened.

**Claims this decision may no longer make:** none.

### [Decision 4 — `ready()` applies the upstream patches][spec-021-d4]

**This decision was inverted by the shipped code, inside its own release, and the spec was never reconciled.** It is the single largest change this pass made.

**What the spec said.** `### Decision 4 — No `ready()` hook in `0.0.7`` opened "`DjangoStrawberryFrameworkConfig.__dict__` MUST NOT contain a `ready` key. The class inherits `AppConfig.ready` (a no-op on the base) and does not override it." Its argument was that [`AGENTS.md`][agents]'s "add settings keys only when the feature that needs them lands" generalizes to AppConfig hooks, and that no shipped `0.0.7` feature needed a `ready()` body.

**What holds at `HEAD`.** `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` exists and dispatches three appliers — `_django_patches.apply()`, `_strawberry_patches.apply()`, `_cross_web_patches.apply()` — from function-local imports, each self-gated on `APPLY_UPSTREAM_PATCHES` (`django_strawberry_framework/conf.py::upstream_patches_enabled`).

**Why the later contract is the correct one, and why nothing was skipped.** The generalization from the settings rule was sound in revision 1 and stopped applying the moment a shipped feature needed the hook. `300e2811` ("Ship Django Trac #37064 fix as package-level AppConfig.ready() patch", 2026-05-23) landed exactly that feature — sibling card `DONE-024-0.0.7`, **the same `0.0.7` release**, four days before the release date. The rule was never violated; the antecedent came true. What went wrong is that a sibling card added a hook the sibling spec forbade, and neither spec noticed.

**The chronology.**

| Commit | Date | What it did |
|---|---|---|
| `300e2811` | 2026-05-23 | Shipped the Django Trac #37064 fix as a package-level `AppConfig.ready()` patch — the `ready()` override's first form, one applier |
| `7014125a` | 2026-05-26 | Hardened it: `SimpleTestCase` retarget, defensive imports, callable guard |
| `c7cb5f5c` | 2026-06-18 | Broadened the dispatch to the Strawberry and `cross_web` appliers — three modules, one per patched dependency |
| `136c5476` | 2026-07-13 | Pinned the dispatch itself with a package test, after the patch modules' own suites proved non-distinguishing |

**Rejected while reconciling it (the resolution direction was the maintainer's, recorded in the round's build plan: "the spec states the current contract; how it got there goes in the rationale file").**

- **Leave Decision 4 as written and add an amendment block naming the sibling card.** Rejected: the spec never narrates its own history, and an amendment block is precisely the shape [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` forbids. A reader would have had to apply a chronology to learn what is true.
- **Delete Decision 4 and let `apps.py`'s own docstrings carry the contract.** Rejected: the spec is the contract for this module, and the Decision numbering is cited from the test file, the checklist and the Definition of done. Deleting it would strand those references and leave the one genuinely subtle part — the gate's placement inside each `apply()` rather than in `ready()` — documented nowhere a spec reader looks.
- **Restate the decision as "`ready()` exists" and stop there.** Rejected: the negative half is still load-bearing and is what the Non-goals, the three forbidden keys and the `finalize_django_types` argument all rest on. The Decision now carries an explicit "what `ready()` does NOT do" list so the discipline survives the inversion.
- **Enumerate in the Decision which upstream bug each patch module fixes.** Rejected: `ready()`'s own docstring deliberately repeats none of that inventory, on the grounds that each patch module's docstring is its single source of truth. A spec-side copy would be a second thing to keep true, and this whole round exists because a spec-side copy went stale.
- **Call the dispatch sequence a *dependency order*.** Rejected, and the phrase was struck from both spec sites and from the table row above after it was written into them: nothing in the source supports it. `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` names the three modules and asserts no ordering constraint; `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely` asserts that all three are installed, never the sequence; the three appliers replace disjoint targets (`SimpleTestCase._remove_databases_failures`, the Strawberry `BaseView` / `SyncBaseHTTPView` / `AsyncBaseHTTPView` slots, `DjangoHTTPRequestAdapter.body`), so no order is forced. The one layering statement that exists runs the other way — `django_strawberry_framework/_cross_web_patches.py` #"request/response abstraction Strawberry's Django view is built on" — which would put `cross_web` *before* `strawberry`, the reverse of what ships. The spec now says **"in this order"**: the sequence stated as the fact it is, with no reason claimed. Substituting a different reason was rejected for the same cause — an unsupported claim swapped for another unsupported claim is the same defect. The rendered [`docs/GLOSSARY.md`][glossary] `## Django AppConfig` entry carries the identical wording, so spec and glossary say one thing.

**Everywhere the falsification reached, and how each site was reconciled.** A partial claim fix is this cycle's dominant defect, so the population is defined before it is counted, its two instruments are stated with what each does and does not reach, and the rows the instruments miss are named individually. The table below carries the members that definition, those instruments and a section-by-section reading of the file at `51eb47ba` produced; it is not claimed to be closed against readings nobody has performed.

**Population.** A *site* is a spec passage at commit `51eb47ba` that does one of three things: asserts `apps.py` ships no `ready()` body; enumerates `"ready"` among the negative-shape test's forbidden keys; or states a count that the shipped `ready()` and its three tests falsify. The corpus is that one file, obtainable as `git show 51eb47ba:docs/SPECS/spec-021-apps-0_0_7.md`, and every line number below is a line in it. Two instruments were run over it and their union was then completed by reading the file section by section:

- **(a) the 37 body lines outside the moved `Revision history` block that carry a genuine `ready` token** — `sed -n '34,513p' … | grep 'ready' | sed 's/already//g' | grep -c 'ready'` -> 37, against 52 lines before the `already` strip and 63 whole-file. The 37 lines are 40, 41, 62, 66, 87, 91, 96, 106, 107, 113, 115, 118, 142, 150, 272, 274, 278, 279, 280, 281, 283, 287, 288, 289, 335, 366, 367, 370, 391, 401, 415, 419, 435, 443, 454, 457, 459.
- **(b) the 9 lines carrying a falsified count with no `ready` token at all** — `grep -n 'four forbidden\|the 5 tests\|four-test plan\| 5 (4 positive'` -> lines 10, 13, 19, 66, 106, 356, 372, 391, 457.

**What each instrument reaches, mapped onto the rows rather than described.** Instrument (a)'s 37 lines account as: 32 lines landing on **23** of the 31 rows below (row 15 alone absorbs ten of them, lines 272-289, because Decision 4's own body is one site), plus the four declared non-sites at lines 40, 41, 115 and 118, plus the moved `## Risks and open questions` item at line 435. Instrument (b) adds exactly **two** rows — row 17 (`## Implementation plan` Slice 2 cell, line 356) and row 22 (`## Edge cases` coverage bullet, line 372); its lines 10, 13 and 19 fall inside the moved `Revision history` block and are not sites, and its other four lines are already in (a).

**Six rows are reached by neither instrument.** They are named, not counted, because the whole point of publishing a derivation is that a reader can run it and land where it says: row 6 (`## Goals` item 1, line 105 — the closing `Nothing else.`), row 10 (`### From strawberry_django` heading, line 126), row 13 (`## User-facing API` `INSTALLED_APPS` walkthrough, line 176), row 14 (`## User-facing API` registry-lookup closing sentence, line 205), row 21 (`## Edge cases` re-import bullet, line 371) and row 31 (`## Definition of done` item 9, line 462). None carries a `ready` token or a falsified count; each was found by reading its section. A finding's grep vocabulary is not its population, and this is the measured size of the gap: **23 + 2 + 6 = 31 sites**, listed below in spec order. Every one is reconciled. The count is the table's own row count and the mapping above was re-run against the table after the last edit to it.

Four passages carrying the `ready` token are deliberately **not** sites, because the shipped `ready()` leaves their claims true and only the Decision-4 link label changed: `## Key glossary references`' `finalize_django_types` and `DjangoType` bullets, and `## Non-goals`' `finalize_django_types`-auto-invocation and settings-bootstrap bullets. One further passage left the spec entirely rather than being reconciled in place — `## Risks and open questions` item 3, recorded under [`## Risks and open questions`](#-risks-and-open-questions) below.

| # | Site | Was | Now |
|---|---|---|---|
| 1 | `## Problem statement` — third defect of the implicit AppConfig | "gives the package no hook for future Django-integration work (a `ready()` site for a check, a signal handler, or … schema-export bootstrap)" | "no hook for Django-integration work that must run once the app registry is populated" — the hook is no longer hypothetical |
| 2 | `## Problem statement` — shipping-bar paragraph | the discipline is "what NOT to put in it: **no `ready()` body**, no preemptive settings, …" | the AppConfig is the two attributes, two docstrings and one `ready()` override whose entire body is the patch dispatch; the discipline list keeps its other four members and gains "no Django system checks" |
| 3 | `## Current state` — `conf.py` bullet | the settings wiring is installed at import time, NOT in `ready()`, because `ready()` is not a viable home — read as a general argument | unchanged, plus one sentence saying the constraint is specific to the settings singleton and does **not** generalize, since the patch dispatch has the opposite requirement |
| 4 | `## Slice checklist` — Slice 1 fourth sub-bullet | "Do NOT implement `ready()`" bundled with the three attribute forbiddances | split in two: a positive sub-bullet requiring the three-applier dispatch in the order the shipped `ready()` makes the calls, and a separate sub-bullet for the three forbidden attributes |
| 5 | `## Slice checklist` — Slice 2 negative-shape sub-bullet | four-key set `{"ready", "label", "default_auto_field", "default"}` | three-key set; a new sub-bullet requires the three `ready()` tests |
| 6 | `## Goals` item 1 | the class body is "[t]wo class-level behavioral attributes plus a one-line module docstring … plus a one-line class docstring …", closed by **"Nothing else."** | the same four members, with the closing absolute dropped: the class body also carries the `ready()` override |
| 7 | `## Goals` item 2 | "the four-test plan … plus the one consolidated negative-shape test" asserting the four-key set | the four positive contracts, the three-key negative-shape test, and the three tests pinning `ready()` and its dispatch |
| 8 | `## Goals` item 3 | "preserve the `AGENTS.md` posture **by omitting `ready()`**, `default_auto_field`, and any signal / check / management-command wiring" | "give the package the one app-load hook it needs and no more"; the `AGENTS.md` rule restated in the form that survives — a hook lands with the shipped feature that needs it, never ahead of one |
| 9 | `## Non-goals` item 1 | "`ready()` body — checks, signals, management-command auto-registration, or `finalize_django_types` invocation" | "a `ready()` body **beyond the upstream-patch dispatch**" — the same four exclusions, scoped |
| 10 | `## Borrowing posture` — `### From strawberry_django` heading | "borrow the AppConfig shape **verbatim**" | "borrow the AppConfig shape"; with `ready()` and two docstrings the shape is no longer verbatim, and the sub-bullets already name each divergence |
| 11 | `## Borrowing posture` — "No `ready()`" bullet | "strawberry-django does not implement one; we do not either." | "One deliberate behavioral divergence: `ready()`" — what diverges, why (the package ships defensive upstream patches a consumer must not install by hand), and that the divergence is scoped to that dispatch |
| 12 | `## Borrowing posture` — "We do not borrow this" bullet | the argument closed on "the future-card seam (a `ready()` site reserved for later cards)" | closes on the app-load hook the package needs **now** for its upstream patches |
| 13 | `## User-facing API` — `INSTALLED_APPS` walkthrough | the entry is what makes Django pick up the explicit class | also the whole opt-in for the upstream patches, since that is a consumer's first question about Decision 4 |
| 14 | `## User-facing API` — registry-lookup closing sentence | the lookup is "the path future cards will use" | also the path `tests/test_apps.py` uses to drive `ready()` deterministically |
| 15 | `### Decision 4` — heading and body | "No `ready()` hook in `0.0.7`"; `__dict__` MUST NOT contain a `ready` key | "`ready()` applies the upstream patches"; the dispatch, the gate's placement inside each `apply()`, idempotence, reload behavior, and the four things `ready()` still does not do |
| 16 | `### Decision 8` — symmetry clause | `default`'s any-value scope is "symmetric with Decision 2 / **Decision 4** / Decision 5, every other forbidden-key Decision" | symmetric with Decision 2 and Decision 5; Decision 4 is no longer a forbidden-key Decision |
| 17 | `## Implementation plan` — Slice 2 table cell | "5 (4 positive + 1 consolidated negative-shape covering four forbidden keys)", `+60 / -0` | 8 tests (4 positive + 1 three-key negative-shape + 3 pinning `ready()`), `+184 / -0`; Slice 1 `+43 / -0`, both `wc -l` readings |
| 18 | `## Edge cases` — `INSTALLED_APPS` ordering | "Because this card adds no `ready()` body, ordering is irrelevant" | ordering is still irrelevant, for the real reason: the dispatch installs process-global replacements, reads no other app's state, and every `apply()` is idempotent |
| 19 | `## Edge cases` — Multiple AppConfigs in `apps.py` | the future card "removes `"default"` from the iterated forbidden-key set `{"ready", "label", "default_auto_field", "default"}`" | the same instruction against the three-key set; the cross-reference to the moved Risks entry became a direct statement of the same rule |
| 20 | `## Edge cases` — `AppConfig.ready` is called during `django.setup()` | "Because this card defines no `ready()`, Django's inherited no-op runs … No timing concerns." | the three patch sets are installed before any test row runs, which is why an observing test must revert the patched slots first and restore them in a `finally` |
| 21 | `## Edge cases` — re-importing outside Django | "the module just defines a class" | still legal, and now says why: the three patch-module imports are function-local, so the import alone pulls in none of them |
| 22 | `## Edge cases` — coverage under `fail_under = 100` | "the class body has two attribute assignments and a docstring"; the four positive tests earn its coverage | the `ready()` override too, covered by the three `ready()` tests including a re-fire and a post-reload fire |
| 23 | `## Test plan` — count and negative-shape description | five tests; the negative-shape test iterates the four forbidden keys | eight tests; the three-key negative-shape test with `"ready"` called out as deliberately absent, and three `ready()` descriptions each stating what its test *distinguishes* |
| 24 | `## Doc updates` — GLOSSARY entry body | "no `ready()` body in `0.0.7`" | the three-applier dispatch and the `APPLY_UPSTREAM_PATCHES` gate, with an explicit instruction that the entry names the dispatch and not the patch inventory |
| 25 | `## Doc updates` — KANBAN Done body | "no `ready()` body in `0.0.7` (deferred to the card that needs one)" | "plus a `ready()` body that dispatches the package's three upstream-patch appliers" |
| 26 | `## Doc updates` — CHANGELOG entry | "No `ready()` body in `0.0.7`." | the `ready()` body applies the package's upstream patches at app-load time |
| 27 | `## Out of scope` — future Django checks | "a future card would land its own AppConfig `ready()` body" | "would extend `ready()`" |
| 28 | `## Definition of done` item 1 | the absence list opens with "no `ready()` body" | the four remaining absences; the `ready()` requirement moved to item 6 |
| 29 | `## Definition of done` item 4 | "the 5 tests … 4 positive + 1 consolidated negative-shape" asserting the four-key set | the 8 tests; three forbidden keys; the three `ready()` tests named by what each pins |
| 30 | `## Definition of done` item 6 | four absences, all pinned by the consolidated test | three absences pinned by the consolidated test; the `ready()` override and its behavior pinned by the three `ready()` tests |
| 31 | `## Definition of done` item 9 | doc surfaces reflect the shipped state | unchanged in substance, with "`ready()` included" made explicit, because two of those surfaces still describe a one-applier or no-applier `ready()` |

**Rejected alternatives the original decision carried** (still valid as rejections, and all still true of the shipped `ready()`, which does none of them):

- **Define `ready()` as an explicit `pass` body for "future flexibility".** Rejected: a `pass`-body method is the canonical preemptive-surface anti-pattern; a card adds the body when it needs it. The shipped `ready()` is the same rule with the antecedent satisfied — it has a real body because a real feature needed one.
- **Define `ready()` to call `finalize_django_types()`.** Rejected: it contradicts the documented synchronization-point contract and would break consumers whose `config/schema.py` imports relation modules in an order different from Django's app loader. Still normative in the spec, because it is the thing the next author will try.
- **Define `ready()` to register a `django.core.checks` check validating `DjangoType` declarations.** Rejected: even a useful check has its own design surface — what it warns about, the message, whether it gates `manage.py runserver` — and needs its own spec.

**Claims this decision may no longer make:** that `DjangoStrawberryFrameworkConfig.__dict__` must not contain a `ready` key; that the class does not override `ready()`; that no shipped `0.0.7` feature needs a `ready()` body; that `"ready"` is in the negative-shape test's iterated set; that the AppConfig has no side effects at app load; that the dispatch sequence is a *dependency order*.

### [Decision 5 — No `default_auto_field` and no models][spec-021-d5]

The only Decision with no `Alternatives considered (and rejected):` list — there was no alternative to weigh, since the package declares no `models.py` anywhere in its tree.

**The positive arguments** (the moved `Justification:` block) are the Decision's three bullets in the spec and are not restated here. Nothing in the block was left behind.

**Changes, with the round that caused each.** None.

**Claims this decision may no longer make:** none.

### [Decision 6 — Joint `0.0.7` cut][spec-021-d6]

**Rejected alternatives.**

- **This card bumps `0.0.7` because it ships earlier than its siblings.** Rejected: ship order is determined by which card a maintainer picks up next, not by card number; pinning the bump to a specific card creates a sequencing constraint with no engineering justification.
- **Add a separate release-cut card to `KANBAN.md` that owns the bump.** Rejected: out of scope for this spec, whose boundary forbids `KANBAN.md` edits beyond the Slice 3 column move. The "last card to ship" policy is workable as-is.

**The positive arguments** (the moved `Justification:` block) are the ones the Decision's own bullets now carry in the spec — restate the policy rather than cross-reference it, and let the bundle's cards share one `[0.0.7]` `### Added` section — and are not repeated here. One argument did not survive into the spec and is recorded only here: `KANBAN.md` already pinned the same policy, so the Decision was never its only carrier.

**Changes, with the round that caused each.** None to the policy. The card ids in the Decision were rewritten by the 2026-07-30 board renumber.

**Claims this decision may no longer make:** none — but note that `KANBAN.md`'s release line records `0.0.7` as having shipped **seven** cards (`DONE-020` through `DONE-026`), not the four this Decision bundles. The Decision's four is the WIP set at authoring time, excluding the already-shipped `DONE-020-0.0.7`; `DONE-024-0.0.7` and `DONE-026-0.0.7` joined the release after it was written. The version-bump policy is unaffected.

### [Decision 7 — No fakeshop `INSTALLED_APPS` entry change][spec-021-d7]

**Rejected alternatives.**

- **Switch fakeshop to the dotted-path form to demonstrate the explicit pattern.** Rejected: the User-facing API section already names the dotted-path form as an equivalent option, which is documentation enough; cluttering the example settings is unnecessary, and the example should match the form the docs recommend.
- **Add a test in `examples/fakeshop/tests/` asserting the resolved AppConfig is `DjangoStrawberryFrameworkConfig`.** Rejected: the assertion belongs in `tests/test_apps.py`, where the system-under-test is the package itself. An example-project test would be a coverage detour through fakeshop's Django machinery when the package's own test pins the contract directly.

**The positive arguments** (the moved `Justification:` block) are the Decision's three bullets in the spec and are not restated here. Nothing in the block was left behind.

**Changes, with the round that caused each.** None.

**Claims this decision may no longer make:** none.

### [Decision 8 — No `default` attribute][spec-021-d8]

**Rejected alternatives.**

- **Set `default = True` defensively, in case a future Django version changes the implicit-default behavior.** Rejected: Django's `AppConfig` discovery rules have been stable since 3.2 (2021), and Django's deprecation policy would announce any change with multi-version warning. Defending against an unannounced change is over-engineering.
- **Narrow the Decision to `default = True` only** (the rev1-rev3 wording). Rejected by rev4 L4: the consolidated negative-shape test catches `default` at any value, so either the Decision widened to match the test or the test narrowed to match the Decision. Widening was the lower-friction fix and is consistent with the surrounding forbid-the-attribute-outright Decisions.

**The positive arguments** (the moved `Justification:` block) are the Decision's four bullets in the spec and are not restated here. Nothing in the block was left behind.

**Changes, with the round that caused each.** rev4 L4 retitled the Decision from "No `default = True` marker" to "No `default` attribute", broadened the body, and retargeted every `#decision-8--no-default--true-marker` link. rev5 L1 propagated the broadening to the Edge-cases "Multiple AppConfigs" bullet, which surfaced the dual-edit requirement a multi-AppConfig future carries. rev6 L1 propagated it to the Slice 1 checklist sub-bullet, the last site rev4 L4 missed.

**Claims this decision may no longer make:** none. The one thing that changed is the iterated set the Decision points at, which lost `"ready"` and is now three keys — see [Decision 4](#decision-4--ready-applies-the-upstream-patches).

### `## Problem statement` and `## Current state`

Moved: the rev5 L2 attribution on the two-attributes-plus-docstrings sentence, and the rev3 L2 / rev5 M1 attributions on the `Current state` bullets.

**Changed by R1 (F1).** The Problem statement's third defect of the implicit AppConfig read "gives the package no hook for future Django-integration work (a `ready()` site for a check, a signal handler, or — in a future card — schema-export bootstrap)". The hook is no longer hypothetical, so it now reads "no hook for Django-integration work that must run once the app registry is populated" — which is what the shipped `ready()` uses it for. The final paragraph gained the `ready()` clause.

`## Current state`'s `conf.py` bullet keeps the rev5 M1 correction (the rationale is in inline comments, not the module docstring) and gained one sentence the reconciliation forced: the import-time constraint is specific to the settings singleton and does **not** generalize, because the patch dispatch has the opposite requirement. Without it the bullet reads as an argument against any `ready()` work at all, which is how the original Decision 4 used it.

The bullet asserting `apps.py` "already appears in the target layout with the `[alpha]` tag" was rewritten: the regenerated `docs/TREE.md` carries `apps.py` in both layouts with no tag.

### `## Goals` and `## Non-goals`

Moved: the rev2 H2, rev3 H1, rev4 L2 and rev4 L3 attributions on Goals 1 and 2.

**Changed by R1 (F1, F2).** Goal 1 lost its closing `Nothing else.` — an absolute over the class body, written when the body was two attributes and two docstrings, which the `ready()` override falsifies; the four members it enumerates are unchanged and the sentence now ends at the docstring exemption. Goal 2's test enumeration was rewritten from "the four-test plan plus the one consolidated negative-shape test" to the eight tests that shipped. Goal 3 was rewritten from "preserve the AGENTS.md posture **by omitting `ready()`**" to "give the package the one app-load hook it needs and no more", with the AGENTS.md rule restated in the form that survives: a hook lands with the shipped feature that needs it, never ahead of one. Non-goals item 1 was scoped rather than deleted — the four exclusions it named (checks, signals, management-command auto-registration, `finalize_django_types`) are all still true of the shipped `ready()`. A new Non-goal was added for the patch content itself, since Decision 4 now points at three modules this card does not own.

### `## Borrowing posture`

Moved: the four inline `Justification:` labels and the rev4 L3 / rev4 L4 attributions.

**Changed by R1 (F1).** The "**No `ready()`**" bullet was the borrowing posture's cleanest statement of the falsified claim: "strawberry-django does not implement one; we do not either." Replaced with "**One deliberate behavioral divergence: `ready()`**", which says what diverges, why (the package ships defensive upstream patches a consumer must not have to install by hand), and that the divergence is scoped to exactly that dispatch. The heading "borrow the AppConfig shape verbatim" lost "verbatim" for the same reason — with `ready()` and two docstrings, the shape is no longer verbatim, and the sub-bullets already say precisely which parts diverge.

### `## User-facing API`

No round touched this section. **Changed by R1 (F1)** in two places: the `INSTALLED_APPS` walkthrough now says the entry is also the whole opt-in for the upstream patches, since a consumer's most likely question about Decision 4 is "what do I have to do?"; and the registry-lookup subsection, which said the path is what "future cards will use", now also names it as the path `tests/test_apps.py` uses to drive `ready()` deterministically.

### `## Implementation plan` — the slice table's estimates

Moved: the rev2 H2 attribution on the Slice 2 test-count cell.

**Changed by R1 (F2).** The table said Slice 2 lands **5** tests (`+60 / -0`) and Slice 1 `+10 / -0`. Measured on the shipped files (`wc -l django_strawberry_framework/apps.py tests/test_apps.py` -> 43 and 184), with **8** collected tests (`uv run pytest tests/test_apps.py --no-cov --collect-only -q` → `8 tests collected`). The cells now carry those measurements — `+43 / -0`, 8 tests and `+184 / -0` — rather than a rounded third number: the column header still reads "Approx. line delta", but a shipped spec whose whole reconciliation is estimate-replaced-by-measurement has no reason to round the measurement it is holding. Slice 3's `+25 / -8` is left as the authoring-time forecast, since its five doc files carry later cards' edits too and no delta measurable today is that slice's. The "Total expected delta: ~95 lines" sentence was deleted rather than re-estimated: it was the sum of three estimates, one of which the slice table already states, and a spec that shipped does not need a forecast of its own size.

**A count correction the round itself produced.** The build plan's F2 recorded the `HEAD` file as carrying **7** test functions. It carries **8** (`grep -c '^def test_' tests/test_apps.py` → 8; `--collect-only` agrees). F2's other half — "three tests exist that the spec does not describe" — is right; 8 minus the spec's 4 positive and 1 negative is 3. The total was wrong while the delta was right, which is the shape a count-by-subtraction takes when the subtrahend is measured and the minuend is not.

### `## Slice checklist`

Moved: the rev3 L1, rev4 L2, rev6 L1 and rev6 L2 attributions, and the rev6 L2 explanation of why the final-gates bullet changed shape.

**Changed by R1 (F1, F2).** Slice 1's fourth sub-bullet was split in two: a positive requirement for the `ready()` dispatch, and the three-attribute forbiddance that survives from rev6 L1. Slice 2 gained a third sub-bullet for the `ready()` tests and lost `"ready"` from the forbidden-key set. Slice 3's `docs/README.md` and `docs/TREE.md` bullets were restated to the landed obligation, their vanished mechanics recorded under [Provenance](#provenance-of-this-record).

The boxes stay `- [ ]`. They are the record of a shipped card's slice plan, and the `Status:` line is the source of truth for completion — ticking them retroactively would assert an audit this pass did not perform.

### `## Edge cases and constraints`

Moved: the rev3 L2, rev4 L4, rev5 L1 and rev2 H2 attributions.

**Changed by R1 (F1).** The section carries **eight** bullets at `HEAD` and eight now (`awk '/^## Edge cases/,/^## Test plan/' … | grep -c '^- \*\*'` -> 8 against both the `HEAD` copy and the rewritten spec). **Five** of the eight asserted or assumed the absence of `ready()` — `INSTALLED_APPS` ordering, Multiple AppConfigs, `ready` during `django.setup()`, re-importing outside Django, and coverage under `fail_under = 100` — and all five are rows 17-21 of the table under [Decision 4](#decision-4--ready-applies-the-upstream-patches). The `django.setup()` bullet is the one that gained substance rather than losing a false clause: it now carries the reason the dispatch test must revert the patched slots before driving `ready()`, and restore them in a `finally`, which is the single most transferable thing in this spec for any later card testing an app-load side effect.

The `Django >= 5.2` prose was corrected to the real pin, `Django>=5.2.16`.

### `## Test plan`

Moved: the rev2 H2, rev3 H1 and rev4 L4 attributions, and the sentence "Rev1 of this spec had a single-key `does_not_define_ready` test that pinned only one of the four; rev2 H2 folded the other three into the same test".

**Changed by R1 (F1, F2).** The section described five tests; eight shipped. The four positive descriptions were kept verbatim, since all four are accurate. The negative-shape description lost `"ready"` and gained the reason the file carries an in-place comment about it: "no extra AppConfig attributes" is exactly the sentence a later reader would cite to justify deleting the override. Three new descriptions were added, each stating what its test *distinguishes* rather than what it asserts — the dispatch test's revert-first construction, and the reload test's second reload and paired restore.

**Rejected while writing it:** describing the three `ready()` tests by their assertions alone. The dispatch test's assertion (`all three patches installed`) is satisfied by any earlier `apply()` in the worker, so an assertion-only description would read as a test that pins nothing, and the next author to "simplify" it would delete the revert and keep the assertion.

### `## Doc updates`

Moved: the rev2 H1 attributions on the `docs/README.md` bullets and the rev2 L1 attribution on the `docs/TREE.md` bullet.

**Changed by R1 (F1).** Three of the five doc targets carried the false `ready()` claim in the text they prescribed — the GLOSSARY entry body, the KANBAN Done body and the CHANGELOG entry — and all three now prescribe the shipped contract. Two of those three are **DB-backed** and are not this file's or the spec's to fix: `docs/GLOSSARY.md`'s entry renders from `GlossaryTerm.body` and `KANBAN.md`'s card note from `CardItem.text`, so the fix is an ORM edit plus a regenerate. They are the round's R2 cohort. `CHANGELOG.md` at `HEAD` already describes the `ready()` body, so only the spec's prescription was stale there — but it describes **one** applier, not three, which is the same understatement `docs/GLOSSARY.md` carries.

**Corrected at the cross-cohort integration pass — two of those three rewrites overshot.** Replacing a false absence with an unscoped presence is the same defect in the other direction, and the two prescriptions that name a *release* rather than the package's current state are where it landed.

- The **KANBAN Done body** prescription came out of R1 reading "plus a `ready()` body that dispatches the package's three upstream-patch appliers" — a body attributed to *this card*. Both halves are false: this card's own diff carries no `ready()` at all (`git show 300e2811^:django_strawberry_framework/apps.py` and the commit that first added the module both hold two attributes, two docstrings and no `ready`), and the three-applier dispatch is not `0.0.7` content (`git show 0.0.7:django_strawberry_framework/apps.py` carries the Django applier alone; `git show 0.0.11:…` is the first tag carrying all three). It also contradicted `## Out of scope` in the same file, which already assigns the Django half to `DONE-024-0.0.7` and the other two halves to later cards. The prescription now scopes the absence to this card's diff and names where the release's `ready()` came from. R2's landed `CardItem` text had already reached the correct scoping independently; the spec was the surface still asserting the unscoped version, and the two surfaces disagreed until this pass.
- The **CHANGELOG** prescription read "the `ready()` body applies the package's upstream patches at app-load time", which is not what `CHANGELOG.md`'s `[0.0.7]` entry says and is looser than what `0.0.7` shipped. That entry is **correct as history** and must not be edited — the release carries one applier — so a prescription diverging from it is a standing invitation to falsify it. The bullet now states the entry as it shipped, and says explicitly that the Strawberry and `cross_web` appliers are not `0.0.7` content.

Neither correction touches a DB row, so neither owes a regenerate; the GLOSSARY prescription is untouched, because a glossary entry describes the package's **current** state and the three-applier dispatch is current.

The `docs/README.md` and `docs/TREE.md` bullets were restated to the landed obligation; see [Provenance](#provenance-of-this-record) for what was deleted and why.

### `## Renumber residue`

Not a spec section — a defect class that ran through several of them, recorded here once.

The spec's link-definition block carried `[spec-016]: spec-020-list_field-0_0_7.md`: a ref-id naming the **pre**-renumber number with a target naming the **post**-renumber file. The definition resolved, so nothing was broken and nothing was going to be noticed; the body then used that ref-id, with `spec-016` as its visible label, in **six** places while the `Predecessors:` line named `spec-020`, so a reader met two names for one document in the same file. Three further bare-prose mentions ("smaller than `spec-016`", "spec-016's `DjangoListField`", "identical to spec-016") brought the token count to **17 occurrences across 10 lines** — a spread `grep -c` reports as 10, which is the count-lines-not-occurrences trap this repo has been bitten by before. All 17 are gone: the ref-id is now `[spec-020]` and every prose mention names `spec-020`.

The same `[spec-016]` ref-id, and a companion `[spec-017]` pointing at this spec's own post-renumber filename, survive in `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/SPECS/spec-023-multi_db-0_0_7.md`, `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, `docs/SPECS/spec-027-filters-0_0_8.md` and `KANBAN.md`. None is this cycle's to edit; they are recorded for whoever owns those specs next, with the population stated as what it is rather than as what a token grep reports.

**The residue is link-definition lines, not the ~100 tokens a grep finds.** A definition is residue only when its ref-id and its target disagree. Instrument, run as `git grep -E '^\[spec-01[67][a-z0-9-]*\]:' 51eb47ba -- docs/SPECS KANBAN.md` and then comparing each ref-id's number against its target: **at `51eb47ba` the corpus holds 32 such definitions, 16 of which disagree and 16 of which agree.** One of the 16 disagreeing is this spec's own `[spec-016]`, repaired by this round, so **15 sit in siblings — 7 in `spec-022`, 3 in `spec-023`, 2 in `spec-025`, 2 in `spec-027`, 1 in `KANBAN.md`.** The 16 that agree are not two: 9 in `appx/spec-016-…-rationale.md`, 2 in `appx/spec-017-…-rationale.md`, and one each in `appx/spec-004-…-rationale.md`, `spec-016-fieldmeta_consolidation-0_0_6.md`, `spec-017-deferred_scalars-0_0_6.md`, `spec-018-meta_primary-0_0_6.md` and `spec-037-upload_file_image_mapping-0_0_11.md` — a reader who runs the instrument meets all sixteen and should not be told to expect two. A raw `grep -o 'spec-01[67]'` over the five sibling files reports **104** occurrences, because `spec-016-fieldmeta_consolidation-0_0_6.md` and `spec-017-deferred_scalars-0_0_6.md` are real current filenames and most hits are legitimate references to those two other specs. The token is not the population.

**The sibling half of that population is already moving.** In the working tree at the end of this round the same command returns 24 definitions, 8 disagreeing — `spec-022`'s 7 are gone, removed by a concurrent session running `spec-022`'s own rationale-extraction round, and this spec's own is repaired. Whoever acts on the residue re-derives it at that moment; the figures here are pinned to `51eb47ba` precisely because the live tree is not a stable corpus.

**The spec's own `## Out of scope` carried the residue too, in a third spelling, and contradicted itself.** Four bullets named `TODO-ALPHA-029` / `031` / `032` / `033` "for `0.0.12`", and `## Borrowing posture`'s "Explicitly do not borrow" bullet named `TODO-ALPHA-029` as the debug-toolbar card while the `## Out of scope` bullet gave `029` to the Channels ASGI router and `031` to the debug toolbar — one file, two attributions, one id. Re-derived against `KANBAN.md` by **feature**, never by number: the four ids as numbers now name `DONE-029-0.0.9` (`DjangoType` consumer-DX cleanup), `DONE-031-0.0.9` (GlobalID encoding), `DONE-032-0.0.9` (full Relay) and `DONE-033-0.0.9` (connection-aware optimizer), none of which is the feature its bullet describes. The four features are `DONE-041-0.0.14` (Channels ASGI router), `DONE-042-0.0.14` (debug-toolbar middleware), `DONE-043-0.0.14` (test-client helpers) and `DONE-044-0.0.14` (response-extensions debug middleware) — the four cards of the joint `0.0.14` cut, all four recorded as `shipped (`0.0.14`)` in `docs/GLOSSARY.md`. So the version was wrong on all four bullets, not two: none shipped in `0.0.12`. Each bullet now names its current card id and the version it actually shipped in, the list is in card order, and the Borrowing-posture mention names `DONE-042-0.0.14`, which closes the intra-file contradiction. A shipped spec's forward pointers were **not** frozen at authoring time; the alternative was considered and rejected, because a bullet that names shipped work as future work under another card's id misinforms every reader who follows it, and `ARTIFACT.md`'s documentation-sanity rule requires card IDs and shipped statuses to match the current board.

The Risks section carried the same residue in one more spelling: "the four remaining `0.0.7` WIP cards (017, 018, 019, 045)". Re-derived against `KANBAN.md` rather than translated from memory — the release line at `KANBAN.md #"`0.0.7` shipped 2026-05-27 with seven cards"` and the Done-column spec table give `017 → DONE-021-0.0.7`, `018 → DONE-022-0.0.7`, `019 → DONE-023-0.0.7`, `045 → DONE-025-0.0.7`, which is exactly the set Decision 6 in the same spec already named post-renumber. The corrected ids are carried into the moved Risks item below.

### `## Risks and open questions`

The whole section moved. It was written as preferred-answer / fallback pairs, and by the time the card shipped three of the four had resolved and the fourth had been falsified by a sibling card. The four:

1. **Django's implicit single-AppConfig discovery edge cases.** Preferred answer: Django 3.2+'s "exactly one `AppConfig` subclass in `apps.py` becomes the default" behavior is stable, so `"django_strawberry_framework"` in `INSTALLED_APPS` resolves to `DjangoStrawberryFrameworkConfig` with no further declaration. Fallback: if a real configuration is found where discovery picks a different class (a consumer installing both this package and a fork with overlapping app names), document the explicit-dotted-path form as the disambiguation recipe. **Resolved as preferred** — the fallback was already documented as an equivalent option, and `tests/test_apps.py::test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` pins the resolution.
2. **`verbose_name` cosmetic drift.** Preferred answer: `"Django Strawberry Framework"` matches the `README.md` H1 and is pinned by `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name`. Fallback: a rebrand changes the AppConfig and the test in one edit; nothing in the public surface depends on the string. **Resolved as preferred**; the string is unchanged at `HEAD`.
3. **Future-card `ready()` body adoption.** Preferred answer: "no card needs `ready()` in the current roadmap; the no-`ready()` test stays." Fallback: a card that needs `ready()` removes `"ready"` from the iterated forbidden-key set AND adds a positive test for whatever the body does, both in the same change. **The preferred answer was falsified four days before the release** and the fallback is what happened — and it happened correctly: `tests/test_apps.py` has `"ready"` out of the iterated set, an in-file comment naming the supersession, and three positive tests for the body. The risk register called the shape right and the timing wrong. (This item had itself been corrected once, by revision 4's Informational #3, for describing the enforcement mechanism in the retired single-key form.)
4. **Last-card-to-ship version bump policy.** Preferred answer: the last of the four remaining `0.0.7` WIP cards — `DONE-021-0.0.7` (this card), `DONE-022-0.0.7`, `DONE-023-0.0.7` and `DONE-025-0.0.7`, re-derived from `KANBAN.md`; the section as shipped named them by their pre-renumber ids `017, 018, 019, 045` — owns the bump, per [`spec-020`][spec-020] Decision 10. Fallback: identical to spec-020's — if merge sequencing turns out unclear, a separate `KANBAN.md` edit adds an explicit release-cut card, an edit this spec deliberately does not author. **Resolved as preferred**; `0.0.7` shipped on 2026-05-27.

### `## Definition of done`

Moved: the round attributions on items 1, 4, 6, 9 and 13.

**Changed by R1 (F1, F2).** Four items were false as written and are now statements of what shipped: item 1 (dropped "no `ready()` body" from the absence list), item 4 (8 tests, not 5; three forbidden keys, not four; the three `ready()` tests named), item 6 (the `ready()` override is now a positive requirement, and the three absences are pinned by the consolidated test while the override is pinned by its own three) and item 9 (`ready()` named explicitly, because two of the five doc surfaces still understate it).

Item 8 ("package coverage stays at 100%") was **kept unchanged**, and deliberately: it states the repository's standing CI gate, which is a true completion criterion, and it is not in tension with item 13's rule that a *worker* does not assert coverage. The two were read together before either was touched.

## Claims the spec may no longer make

An index of the retractions above, for a reviewer checking the implementation against the reasoning that produced it. Every row is a claim some revision of this spec asserted and a later revision, the ship, or a sibling card falsified.

| Claim once made | Where it lived | What holds instead | Retired by |
|---|---|---|---|
| `DjangoStrawberryFrameworkConfig.__dict__` MUST NOT contain a `ready` key | Decision 4, Slice 1, Slice 2, Goals 1 and 3, Non-goals 1, Borrowing posture, Test plan, Edge cases (2 bullets), Definition of done 1 and 6 | `ready()` is overridden and dispatches three self-gated upstream-patch appliers | `300e2811` (card `DONE-024-0.0.7`, same `0.0.7` release), broadened by `c7cb5f5c` |
| no shipped `0.0.7` feature needs a `ready()` body | Decision 4 | the Django Trac #37064 hardening shipped in `0.0.7` and needs exactly that hook | `300e2811` |
| the negative-shape test iterates four forbidden keys, `"ready"` among them | Slice 2, Decision 4, Decision 8, Test plan, Edge cases, Definition of done 6 | three keys — `label`, `default_auto_field`, `default`; `"ready"` is required and positively pinned | the ship; the test file carries an in-file comment naming the supersession |
| `tests/test_apps.py` contains 5 tests (4 positive + 1 negative) | Implementation plan, Test plan, Definition of done 4, Goals 2 | 8 tests; three of them pin `ready()` and its dispatch | R1 (F2), measured at `HEAD` |
| the AppConfig performs no side effects at app load | Problem statement, Edge cases, Borrowing posture | it installs three sets of upstream patches, idempotently, before any test row runs | `300e2811`, `c7cb5f5c` |
| this card's own diff shipped a `ready()` body dispatching three upstream-patch appliers | Doc updates — the KANBAN Done-body and CHANGELOG prescriptions R1 rewrote | this card's diff carries no `ready()` override; the `0.0.7` release's `ready()` arrives with `DONE-024-0.0.7` and dispatches the Django applier alone; all three first ship together at `0.0.11` | the cross-cohort integration pass, against tag content |
| `Status: draft (revision 6, post-rev5 build-readiness audit)` | preamble | shipped in `0.0.7` on 2026-05-27; archived under `docs/SPECS/` | the ship (F3) |
| the four remaining `0.0.7` WIP cards are 017, 018, 019, 045 | Risks | `DONE-021`, `DONE-022`, `DONE-023`, `DONE-025`, per `KANBAN.md` | the 2026-07-30 board renumber (F4) |
| `spec-016` is the predecessor spec's identity | link definitions and six body uses, plus three bare-prose mentions | `spec-020-list_field-0_0_7.md`; 17 token occurrences corrected | the 2026-07-30 board renumber (F4) |
| the package pins `Django>=5.2` | Edge cases | `Django>=5.2.16` | a later floor bump |
| `docs/TREE.md` carries `apps.py # [alpha] Django AppConfig` in the target layout | Key glossary references, Current state, Decision 1, Doc updates | both layouts carry `apps.py` untagged, with a description naming the patch dispatch | the `docs/TREE.md` regenerate |
| `conf.py`'s module docstring begins `Library settings.` | Current state, Decision 4 | `Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.` | a later `conf.py` docstring rewrite |
| `docs/TREE.md` says "single-file Layer-3 module tests" / "once it earns 3+ files" | Key glossary references, Current state, Decision 1 | neither string survives the regenerate; the section headings are the citable anchors | the `docs/TREE.md` regenerate |
| `docs/README.md` has a `Shipped today` (`0.0.6`) heading and a `Coming in 0.1.0` bullet to edit | Slice 3, Doc updates, Definition of done 9 | the heading reads `(0.0.14)` and the `Coming in 0.1.0` bullet is gone; the AppConfig bullet is present | later cards; R1 restated the obligation (F1) |

## Left open by this pass

Three items, recorded so the next pass does not have to re-derive them. Two this round did not close; the third it closed in its second cohort, after this section was written, and is kept as the record of a closed routing rather than as open work. None is a defect in this spec.

- **The `[spec-016]` / `[spec-017]` ref-id residue in five sibling files** — 15 mismatched definition lines at `51eb47ba`: 7 in `spec-022`, 3 in `spec-023`, 2 in `spec-025`, 2 in `spec-027`, 1 in `KANBAN.md`, derived by the instrument stated under [`## Renumber residue`](#-renumber-residue), which also records how many definitions agree and what the live tree returns. Every definition resolves, so for four of the five files the residue is a naming inconsistency each file's own next cycle owns. Correcting them from here would mean editing four specs this round has no mandate over.
- **`docs/SPECS/spec-022-export_schema-0_0_7.md` asserted the claim this round retired, about this very spec — the fifth file was not merely a naming inconsistency.** At `51eb47ba`, `grep -n 'ready()'` on that file returns four passages. Three assert the retired claim: the `## Problem statement` predecessor paragraph ("deliberately deferred any `Django AppConfig` `ready()` body"), the `## Non-goals` command-hook bullet ("the `ready()`-body deferral, **which is preserved here**"), and the `## Edge cases and constraints` command-discovery bullet ("it has no `ready()` body and does not need one"). The fourth, Decision 3's `finalize_django_types` anti-pattern paragraph, cites Decision 4 for a rule the inversion leaves intact and is not false. `300e2811` falsified the other three inside the same `0.0.7` release, so at `51eb47ba` the two specs of one release contradict each other in writing. Its ref-id `[spec-017-decision-4--no-readyhook-in-0-0-7]` also targets `#decision-4--no-readyhook-in-0_0_7`, an anchor that never resolved — the real slug at `51eb47ba` was `decision-4--no-ready-hook-in-007` — so this pass did not break it, though a reader diffing the two files will assume it did. **In the working tree at the end of this round the file carries zero `ready()` occurrences**: a concurrent session's `spec-022` rationale-extraction round removed all four. The item is recorded, not actioned — `spec-022` is outside this cohort's writable set in either state.
- **The two DB-backed doc bodies that understated the shipped `ready()` — closed in the same round, by its R2 cohort.** `docs/GLOSSARY.md`'s `## Django AppConfig` entry described a one-applier `ready()` and `KANBAN.md`'s `DONE-021-0.0.7` `#### Note` denied one entirely; both are `examples/fakeshop/db.sqlite3` rows (`GlossaryTerm.body`, `CardItem.text`) and were fixed by an ORM edit plus a regenerate, never a file edit. The entry now names the three-applier dispatch and the `APPLY_UPSTREAM_PATCHES` gate; the note scopes the absence to this card's own diff and dates the other two appliers to `0.0.11`. **`CHANGELOG.md`'s `[0.0.7]` entry is not part of this item and is not understated**: it describes the `0.0.7` release, which carries the Django applier and no other, so naming one applier is what makes it accurate — "correcting" it to three would falsify it, and [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" forbids the edit independently.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield

<!-- docs/SPECS/ -->
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-021-d1]: ../spec-021-apps-0_0_7.md#decision-1--module-location--public-export
[spec-021-d2]: ../spec-021-apps-0_0_7.md#decision-2--name--label--verbose_name-pinning
[spec-021-d3]: ../spec-021-apps-0_0_7.md#decision-3--no-public-export
[spec-021-d4]: ../spec-021-apps-0_0_7.md#decision-4--ready-applies-the-upstream-patches
[spec-021-d5]: ../spec-021-apps-0_0_7.md#decision-5--no-default_auto_field-and-no-models
[spec-021-d6]: ../spec-021-apps-0_0_7.md#decision-6--joint-007-cut
[spec-021-d7]: ../spec-021-apps-0_0_7.md#decision-7--no-fakeshop-installed_apps-entry-change
[spec-021-d8]: ../spec-021-apps-0_0_7.md#decision-8--no-default-attribute

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
