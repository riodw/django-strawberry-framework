# Review feedback - `docs/spec-017-apps-0_0_7.md` rev3

Scope: re-reviewed the updated AppConfig spec after the rev2 feedback fixes. Verified the rev3 claims against `pyproject.toml`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `CHANGELOG.md`, `examples/fakeshop/config/settings.py`, `django_strawberry_framework/conf.py`, and `AGENTS.md`. No source implementation was reviewed.

## Rev2 follow-ups — confirmed addressed

- **Rev2 H1 (class docstring vs. `D101` gate)** — addressed. The pinned shape now names a class docstring; verified against `pyproject.toml:75-98` that `"D"` is in `[tool.ruff.lint] select` and that `D101` is not in `ignore`, and that the per-file-ignores at lines 100-107 do not exempt `django_strawberry_framework/apps.py`. The "no `# noqa: D101` shortcut" instruction is consistent with [`AGENTS.md`](../AGENTS.md) line 4.
- **Rev2 L1 (Slice 3 `docs/README.md` checklist still carrying rev1 generic wording)** — addressed. The Slice 3 checklist at `docs/spec-017-apps-0_0_7.md:55` now carries the same three-part action (heading bump, add bullet, surgical removal) as the detailed Doc updates section.
- **Rev2 L2 (stale `Django >= 4.2` citation)** — addressed. The Edge-cases Django-version sentence at `docs/spec-017-apps-0_0_7.md:343` now cites `Django>=5.2`, matching the actual pin at `pyproject.toml:29`.
- **Rev2 L3 (Decision 4 still referencing the rev1 single-key `ready`-only assertion)** — addressed. Decision 4's justification block at `docs/spec-017-apps-0_0_7.md:261` now names `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` and describes the `ready` absence as one of the four keys exercised by the consolidated test.

## New findings

### Low - Decision 2 justification is stale against rev3 H1 and misrepresents the upstream

Location: `docs/spec-017-apps-0_0_7.md:227`

The Decision 2 justification line still reads: "Three pieces of state is the entire surface strawberry-django ships; the borrowing posture is to match that surface." Two problems:

1. Rev3 H1 bumped the spec's own pinned shape from "three pieces of state" to "four pieces of state" by adding the class docstring (called out explicitly in the rev3 changelog at `docs/spec-017-apps-0_0_7.md:16`). The "three" number here was not propagated.
2. The upstream `strawberry_django/apps.py` actually ships only two attributes (`name`, `verbose_name`) with NO module docstring and NO class docstring — the spec's own Borrowing-posture section at line 127 acknowledges this ("the upstream `strawberry_django/apps.py` has none"). So "three" is wrong against both rev3's framing and the upstream's actual shape.

Recommended fix: rewrite the justification to "Two behavioral attributes is the entire surface strawberry-django ships; the borrowing posture matches that. The docstrings here are additive, forced by this repo's stricter pydocstyle gate (rev3 H1) — the documentation shape diverges from the upstream as the Borrowing posture section calls out, but the behavioral shape is identical."

### Low - "Pieces of state" framing mixes class-scope and module-scope artifacts and contradicts the spec's own behavior/documentation distinction

Location: `docs/spec-017-apps-0_0_7.md:43` (Slice 1 checklist), `docs/spec-017-apps-0_0_7.md:214` (Decision 2 lead-in), `docs/spec-017-apps-0_0_7.md:91` (Goal 1)

Slice 1 says "Implement `DjangoStrawberryFrameworkConfig(AppConfig)` with exactly four pieces of state" and then enumerates a module docstring as one of the four. Two issues:

1. The module docstring is at module scope (`django_strawberry_framework.apps.__doc__`), NOT a class attribute. Calling it a piece of `DjangoStrawberryFrameworkConfig`'s state is a category error — the class itself has three pieces (name, verbose_name, `__doc__`).
2. More importantly, the spec's Slice 2 negative-shape test wording and the Test-plan entry both explicitly distinguish behavior from documentation when justifying the exclusion of `__doc__` from the iteration set: "documentation is not behavior" (`docs/spec-017-apps-0_0_7.md:52`, `docs/spec-017-apps-0_0_7.md:369`). Treating module + class docstrings as "state" alongside `name` and `verbose_name` undercuts that distinction in the Slice 1 framing.

This is purely cosmetic — the code that satisfies "two attributes plus two docstrings" is identical to the code that satisfies "four pieces of state" — but the wording inconsistency is the sort of thing a future spec-revision reviewer will trip over.

Recommended fix: in Slice 1, Goal 1, and Decision 2, replace "four pieces of state" with "two class-level behavioral attributes (`name`, `verbose_name`) plus a module docstring (D100) and a class docstring (D101); the two docstrings are documentation, not behavior, and are exempt from the negative-shape iteration accordingly." Keeps the documentation-vs-behavior distinction load-bearing across every section of the spec.

### Low - Module docstring's lint-gate provenance (D100) is silent while the class docstring's (D101) is loudly cited

Location: `docs/spec-017-apps-0_0_7.md:16` (rev3 changelog), `docs/spec-017-apps-0_0_7.md:43-47` (Slice 1 checklist), `docs/spec-017-apps-0_0_7.md:218` (Decision 2), `docs/spec-017-apps-0_0_7.md:127` (Borrowing posture)

The rev3 H1 fix correctly cites `D101` as the forcing function for the class docstring. The same logic applies to the module docstring: `D100` ("Missing docstring in public module") is in ruff's `D` selector at `pyproject.toml:75-90` and is NOT in the ignore list at `pyproject.toml:92-98`. None of the per-file-ignores at lines 100-107 exempt `django_strawberry_framework/apps.py`. The module docstring is therefore also gate-forced, not a stylistic choice.

The module docstring was already in rev1's spec, so this is a propagation gap, not a missing requirement. But the way the spec presents it ("a one-line module docstring naming the module's purpose") reads as if it were a chosen-not-forced piece, while the class docstring is presented as forced. A future maintainer reading "two pieces of state plus two docstrings" might delete the module docstring under the misapprehension that it was a stylistic preference, then hit the `D100` gate and revert — or, worse, drop it through `# noqa: D100`. The "no noqa shortcut" rule from rev3 H1 only mentions `D101`.

Recommended fix: in Decision 2, Slice 1, and the Borrowing-posture section, name `D100` alongside `D101` so the lint-gate provenance is symmetric. Add to the "no `# noqa: D101`" instruction the analogous "no `# noqa: D100`" — both docstrings are root-cause-fix sites, not workaround sites. Adjust the Borrowing-posture's "one forced divergence" sentence to "two forced divergences: this repo's pydocstyle gate requires both a module docstring (D100) and a class docstring (D101); upstream `strawberry_django/apps.py` has neither."

### Low - Decision 8's `default = True` wording is narrower than the consolidated test it relies on

Location: `docs/spec-017-apps-0_0_7.md:313-321` (Decision 8), `docs/spec-017-apps-0_0_7.md:52` (Slice 2 checklist), `docs/spec-017-apps-0_0_7.md:369` (Test plan)

Decision 8 forbids `default = True` specifically — the heading is "No `default = True` marker" and the body says "`DjangoStrawberryFrameworkConfig` does NOT set `default = True`." The consolidated negative-shape test asserts `"default" not in DjangoStrawberryFrameworkConfig.__dict__`, which catches BOTH `default = True` AND `default = False` (and any other value).

`default = False` would be a self-defeating consumer declaration in this context (Django 3.2+'s implicit-default-resolution does not need it), but it is conceptually distinct from `default = True`: the latter declares the class IS the default, the former declares it ISN'T. The test is broader than the Decision permits; either the Decision should tighten to match the test, or the test should narrow to match the Decision.

Tightening the Decision is the lower-friction fix and more consistent with the "exactly two behavioral attributes" posture of the surrounding Decisions 2 / 4 / 5 — every other forbidden-key Decision forbids the attribute outright, not a specific value.

Recommended fix: rename Decision 8's heading from "No `default = True` marker" to "No `default` attribute"; rewrite the body to "`DjangoStrawberryFrameworkConfig` does NOT declare `default` at all (neither `default = True` nor `default = False`)." Add one sentence to the justification: "The negative-shape test enforces this by asserting `\"default\" not in __dict__`; that scope matches `default = True`, `default = False`, and any other value." Also adjust the [Borrowing posture](#borrowing-posture) "Django's `default = True` class attribute" bullet at `docs/spec-017-apps-0_0_7.md:142` for symmetry.

## Other observations (not findings — informational)

- The rev3 changelog narrative is well-structured and cites every prior-revision artifact it supersedes, but it is now ~150 lines of inline history at the top of the spec. Each individual revision narrative is load-bearing for the reader who wants to audit "what was wrong before, what is correct now," but at rev3 the cumulative weight is starting to push the substantive content of the spec down the file. Not a finding because the inline-history convention has clear value, but worth a maintainer's note: at some point (rev4? rev5?) the history may want to compress to one paragraph per revision with a link to the prior `docs/feedback.md` for full detail.
- The Test-plan section's negative-shape test is described as a single test "iterating" four keys. The pytest idiom for this is either `pytest.mark.parametrize` (which produces four pytest items) or a plain loop with four asserts inside one test (which produces one pytest item). The spec is agnostic about which idiom — both are defensible — but the implementation-plan table at `docs/spec-017-apps-0_0_7.md:334` says "5 tests" and DoD item 4 at line 435 also says "5 tests". The parametrize idiom would yield 8 pytest items (4 positive + 4 parametrized negatives). Not a finding, but a Slice 2 implementer reading the spec would benefit from one sentence pinning the chosen idiom so the "5 tests" count is unambiguous against pytest's collection output.
- The Risks-and-open-questions "Future-card `ready()` body adoption" entry at `docs/spec-017-apps-0_0_7.md:413` still describes the pattern as "removes the `\"ready\" not in __dict__` assertion AND adds a positive test" — the single-key shape from rev1, not the consolidated four-key shape from rev2 H2. This is the same kind of stale prose as the rev2 L3 finding (Decision 4) but at a lower fidelity bar because the risks section is forward-looking guidance rather than a Decision rationale. A future-card author will read the consolidated test and adapt the pattern; the risks-section wording is unlikely to mislead. Not flagging as a finding, but if a rev4 is authored for any other reason, this paragraph would benefit from the same propagation.
