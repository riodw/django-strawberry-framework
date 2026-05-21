# Review feedback - `docs/spec-017-apps-0_0_7.md` rev2

Scope: re-reviewed the updated AppConfig spec after the rev1 feedback fixes. No source implementation was reviewed.

## Findings

### High - exact AppConfig shape omits the class docstring required by ruff

Location: `docs/spec-017-apps-0_0_7.md:38-41`, `docs/spec-017-apps-0_0_7.md:425-437`

The spec pins the implementation as `DjangoStrawberryFrameworkConfig(AppConfig)` with `name`, `verbose_name`, and a module docstring only, then gates the slice on `uv run ruff check --fix .`. In this repo, pydocstyle rules are enabled via `pyproject.toml:75-86`, and the ignore list at `pyproject.toml:92-98` does not ignore `D101` (missing docstring in public class). A public `DjangoStrawberryFrameworkConfig` class with no class docstring will therefore fail the required ruff gate even if the code follows the spec exactly.

This is not just cosmetic because the spec also frames the AppConfig body as “exactly” the pinned shape. An implementer has no spec-sanctioned way to satisfy both the “nothing else” AppConfig shape and the mandatory ruff gate.

Recommended fix: make the class docstring part of the pinned shape, e.g. add a one-line class docstring such as `"Register django-strawberry-framework with Django's app loader."` under the class definition. Update Slice 1, Goals / Definition of done, and the negative-shape test wording so “no extra AppConfig attributes” means no extra behavioral class attributes, not “no class docstring”. Avoid a `# noqa: D101` shortcut; this is a normal public class and the docstring is the root-cause fix.

### Low - Slice checklist still carries the pre-rev2 generic `docs/README.md` instruction

Location: `docs/spec-017-apps-0_0_7.md:47-49`

The detailed Doc updates section now correctly says to bump the shipped-list heading and remove only `, Django AppConfig` from the `Coming in 0.1.0` line. But the top Slice 3 checklist still has the older generic instruction to “move the Django AppConfig mention” and “surface it in Shipped today (0.0.7)”. That checklist is the implementation entry point, so it should reflect the surgical rev2 H1 behavior instead of relying on the later detailed section to override it.

Recommended fix: replace the Slice 3 `docs/README.md` checklist bullet with the same two concrete actions from the Doc updates section: bump the heading from `0.0.6` to `0.0.7`, and remove only `, Django AppConfig` while leaving `schema export management command` for `WIP-ALPHA-018-0.0.7`.

### Low - Django version citation is stale against `pyproject.toml`

Location: `docs/spec-017-apps-0_0_7.md:336`

The edge-case note says `pyproject.toml` pins `Django >= 4.2`, but the current dependency is `Django>=5.2` in `pyproject.toml:29`. The AppConfig discovery conclusion is still correct because Django 5.2 is above the 3.2 threshold, but the citation is stale and will send readers to verify the wrong constraint.

Recommended fix: change the sentence to cite `Django>=5.2` and drop the “Django 4.2+ venv” wording.

### Low - Decision 4 still references the old ready-only test shape

Location: `docs/spec-017-apps-0_0_7.md:254-256`

Rev2 consolidates the negative-shape test around all four forbidden keys, but Decision 4 still says the Slice 2 test is `assert "ready" not in DjangoStrawberryFrameworkConfig.__dict__`. The detailed Test plan is correct, so this is only stale prose, but it undercuts the rev2 cleanup and can make a future editor think the ready-only assertion still exists.

Recommended fix: update this paragraph to reference `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` and clarify that Decision 4's `ready` absence is one member of the consolidated class-body test.
