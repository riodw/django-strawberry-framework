# Review feedback - `docs/spec-017-apps-0_0_7.md` rev4

Scope: re-reviewed the updated AppConfig spec after the rev3 feedback fixes. Verified the rev4 claims and the full spec against `pyproject.toml`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `CHANGELOG.md`, `examples/fakeshop/config/settings.py`, `django_strawberry_framework/conf.py`, `tests/base/test_init.py`, and `AGENTS.md`. Also reviewed against the scaffold I drafted into `django_strawberry_framework/apps.py` and `tests/test_apps.py` for cross-consistency. No production source was reviewed.

## Rev3 follow-ups — confirmed addressed

- **Rev3 L1 (Decision 2 justification stale / misrepresenting upstream)** — addressed. The justification at `docs/spec-017-apps-0_0_7.md:231-232` now reads "Two behavioral attributes is the entire surface strawberry-django ships … the documentation shape diverges from the upstream … but the behavioral shape is identical." Both halves of the rev3 finding (the "three pieces" stale propagation AND the upstream-count overstatement) are resolved.
- **Rev3 L2 ("Pieces of state" framing)** — addressed. Slice 1 checklist (`docs/spec-017-apps-0_0_7.md:50`), Goal 1 (`docs/spec-017-apps-0_0_7.md:98`), and Decision 2 lead-in (`docs/spec-017-apps-0_0_7.md:223-228`) all now use the "two class-level behavioral attributes plus two docstrings" / "documentation is not behavior" framing. The category error between module-scope and class-scope artifacts is resolved.
- **Rev3 L3 (D100 silent while D101 cited)** — addressed. Slice 1 checklist (`docs/spec-017-apps-0_0_7.md:53-54`), Decision 2 (`docs/spec-017-apps-0_0_7.md:226-227`), and Borrowing posture's "two forced divergences" sentence (`docs/spec-017-apps-0_0_7.md:128`) all now cite `D100` symmetrically with `D101`. The `# noqa: D100` suppression is forbidden alongside `# noqa: D101`. **Two propagation gaps remain — see new findings below.**
- **Rev3 L4 (Decision 8's `default = True` narrower than test)** — addressed in the central locations. Decision 8 is renamed to "No `default` attribute" (`docs/spec-017-apps-0_0_7.md:319`), the body broadens to "neither `default = True` nor `default = False`" (`docs/spec-017-apps-0_0_7.md:321`), the Borrowing posture bullet at `docs/spec-017-apps-0_0_7.md:149` widens, the Test plan example list at `docs/spec-017-apps-0_0_7.md:384` adds `default = False`, and DoD items 1 and 6 (`docs/spec-017-apps-0_0_7.md:446`, `docs/spec-017-apps-0_0_7.md:452`) drop the "no `default = True`" wording. **One propagation gap remains — see new findings below.**
- **Rev3 informational #2 (pytest idiom commitment)** — addressed. The Slice 2 checklist (`docs/spec-017-apps-0_0_7.md:59`) explicitly pins "a single test function (one pytest item, NOT a `pytest.mark.parametrize` four-way fan-out)" so the "5 tests" count in the Implementation-plan table and DoD item 4 is unambiguous against pytest's collection output.
- **Rev3 informational #3 (Risks `ready()` entry stale)** — addressed. The Risks entry at `docs/spec-017-apps-0_0_7.md:428` now names the consolidated test and describes the pattern as "removes `\"ready\"` from the iterated forbidden-key set" rather than "removes the `\"ready\" not in __dict__` assertion."

## New findings

### Medium - `conf.py` citation is wrong: lines 163-168 are inline comments, not the module docstring

Location: `docs/spec-017-apps-0_0_7.md:89` (Current state, conf.py bullet)

The spec says:

> `django_strawberry_framework/conf.py` ships the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader. It documents (in its **module docstring lines 163-168**) that `setting_changed` signal wiring is installed at **import time**, NOT in `AppConfig.ready()`, because "consumers may import `conf` before app loading during test bootstrap, so AppConfig.ready() is not a viable home for this wiring."

Verified against the actual file:

- `django_strawberry_framework/conf.py:1-36` contains the **actual** module docstring (`"""Library settings. … """`). It covers settings access, the defensive-`None` stance, and how `setting_changed` mutates the singleton in place — but does **not** mention `AppConfig.ready()` as a non-viable home.
- `django_strawberry_framework/conf.py:163-167` contains the quoted rationale, but as a block of **inline comments** (`#` prefix) immediately above the `setting_changed.connect(...)` call at line 168 — NOT in the module docstring.

The quoted prose is in the file, but at a structurally different location than the spec claims. A reader following the citation will open conf.py, look for the module docstring near the top of the file, and find one that says nothing about `AppConfig.ready()`. They will then either (a) conclude the spec is wrong about what conf.py documents, or (b) hunt through the file until they find the inline comments at line 163, which costs time and signals the spec was sloppily authored.

This is also load-bearing for the spec's own reasoning: the "Slice 1's AppConfig has no settings-related wiring to subsume" claim is justified by appealing to conf.py's own documented rationale. If the citation is wrong, the rationale itself is weaker.

Recommended fix: change the parenthetical from "in its module docstring lines 163-168" to one of:

- "in inline comments at `django_strawberry_framework/conf.py:163-167`, immediately above the `setting_changed.connect(...)` call at line 168", or
- "in inline comments at `django_strawberry_framework/conf.py:163-167` (NOT in the module docstring, which is at lines 1-36)".

The second form is more useful because a future maintainer who has read the spec before opening conf.py will know to look at the call-site comment block rather than the file header.

### Low - rev4 L4 propagation miss: Edge cases "Multiple AppConfigs" bullet still cites `default = True`

Location: `docs/spec-017-apps-0_0_7.md:360`

The bullet reads:

> **Multiple AppConfigs in `apps.py`.** Not a concern in `0.0.7` (only one class is declared) but worth noting for future cards: if a second AppConfig is ever added (for some reason), the explicit **`default = True`** marker becomes load-bearing. Future-card-author beware.

This is a rev4 L4 propagation gap. Rev4 L4 enumerates the places it touches (Borrowing posture at line 149 ✓, Decision 8 itself ✓, DoD items 1 and 6 ✓, Test plan example list at line 384 ✓) but does not name the Edge-cases "Multiple AppConfigs" bullet. The wording "`default = True` marker becomes load-bearing" survived from rev1-rev3 untouched.

Beyond stale wording, there is a substantive contradiction the propagation surfaces: rev4 L4 broadened Decision 8 to forbid `default` at any value (`True`, `False`, or other), and the consolidated negative-shape test asserts `"default" not in __dict__`. The hypothetical the Edge-cases bullet describes ("a second AppConfig is ever added") is precisely the scenario where a future card would need to remove `"default"` from the iterated forbidden-key set AND add `default = True` to one of the classes — the same pattern the [Risks and open questions](#risks-and-open-questions) "Future-card `ready()` body adoption" entry at line 428 documents for `ready()`. The Edge-cases bullet currently reads as if a future card could just "add `default = True`" without touching the test, which would fail.

Recommended fix: rewrite to acknowledge both the broadening and the test-update requirement, e.g. "if a second AppConfig is ever added (for some reason), the future card's spec removes `\"default\"` from the iterated forbidden-key set in `tests/test_apps.py` AND adds `default = True` to one of the AppConfig classes in the same change — the same pattern documented for `ready()` adoption in the Risks section. Decision 8's rev4 L4 broadening to forbid `default` at any value pins the current test scope; a multi-AppConfig future explicitly relaxes that pin."

### Low - rev4 L3 propagation miss: Problem statement cites D101 without D100

Location: `docs/spec-017-apps-0_0_7.md:84`

The Problem statement closes with:

> The shipping bar is intentionally low — the AppConfig is two behavioral attributes (`name`, `verbose_name`) plus a class docstring (required by **`D101`**) plus a module docstring.

Rev4 L3's stated goal was to "name `D100` alongside `D101` so the lint-gate provenance is symmetric." The fix enumerates Slice 1, Decision 2, and the Borrowing-posture "forced divergence" sentence — but does not name the Problem statement. The result: D101 is cited for the class docstring, but the module docstring is presented as a stylistic addition with no rule citation.

This is the exact propagation pattern rev4 L3 was supposed to eliminate. A maintainer skimming the Problem statement and only the Problem statement could come away thinking the class docstring is gate-forced and the module docstring is taste. The Slice 1 checklist disambiguates, but the Problem statement is the spec's narrative entry point and is the first place a reader looks to understand the shipping bar.

Recommended fix: insert the symmetric D100 citation, e.g. "plus a module docstring (required by `D100`) plus a class docstring (required by `D101`)" — same two-rule framing as Slice 1 line 53-54 and DoD item 1.

## Other observations (not findings — informational)

- The inline revision history at the top of the spec is now ~37 lines for rev4 alone (lines 20-26 are the four L-findings, lines 25-26 are two informational follow-ups), bringing the total revision-history block to roughly 190 lines before any of the substantive content starts. Each individual narrative is auditable and load-bearing, but the cumulative weight continues to push the spec's actual decisions further down the file. I flagged this in the rev3 review as well; raising it again here in case a rev5 (or a maintainer-initiated cleanup pass) wants to compress prior-rev narratives into one-paragraph summaries with links to the archived `docs/feedback.md` files. The decision is purely stylistic — the content is correct.
- The Slice 1 checklist's lead-in at `docs/spec-017-apps-0_0_7.md:50` says "exactly **two class-level behavioral attributes** plus **two docstrings**." The bullet sub-points immediately below disambiguate (one docstring is at module scope, one at class scope), so a careful reader will not be misled. But the lead-in summary on its own is slightly fuzzy — "two docstrings on the class" is a plausible misreading. The rev3 review's recommended phrasing was "a module docstring and a class docstring" (which is explicit about scope); the spec adopted "two docstrings" instead, which is shorter but loses the scope signal. Not a finding because the disambiguation is right below, but a future maintainer editing the lead-in for any other reason might consider tightening this.
- I noticed during the scaffold work that creating `django_strawberry_framework/apps.py` as an empty-of-classes stub (just module docstring + TODO) interacts cleanly with Django's discovery: Django imports the module, finds zero AppConfig subclasses, and falls back to the synthetic AppConfig — the same pre-`0.0.7` behavior consumers run under today. This is consistent with the spec's claim at `docs/spec-017-apps-0_0_7.md:90` ("the implicit fallback applies only when no `AppConfig` subclass is defined in the package"). Not a finding; just confirmation that the staged-scaffold pattern under AGENTS.md line 26 is compatible with Slice 1's eventual landing. Worth noting because a reader could otherwise wonder whether the file's existence (sans class) would trip Django's discovery; it does not.
- The Edge cases "Coverage of the AppConfig under `fail_under = 100`" bullet at `docs/spec-017-apps-0_0_7.md:367` says "the class body has **two attribute assignments and a docstring**." This is technically accurate — the class body itself has exactly those three statements (name, verbose_name, class docstring). The module docstring lives at module scope and is covered separately by any import. Not a finding (the wording is precise about scope, unlike the L2-flagged "four pieces of state" framing that was fixed), but worth noting that this is the only place in the spec where the class-body-scope distinction is implicitly made without being explicitly called out. A reader who skipped Slice 1 might briefly wonder whether "a docstring" includes the module docstring or just the class docstring; the answer is "just the class docstring," consistent with class-body scope.
