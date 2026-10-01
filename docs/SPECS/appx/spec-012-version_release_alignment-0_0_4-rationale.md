# Rationale: spec-012 — 0.0.4 version and release alignment (deliberation, rejected alternatives)

Deliberative companion to [`spec-012-version_release_alignment-0_0_4.md`][spec-012]. The spec is the
contract; this file records why it has the shape it has. The spec has no numbered Decisions, so each
entry is keyed to a spec section.

## Why the spec is a card snapshot

Bears on [Card snapshot][spec-012-card-snapshot].

The file is the card's `SpecDoc` target, which the kanban app requires of every `done` card
(`examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_spec`). The snapshot names only
the card: labels, priority, relative size, and item rows are rendered into [KANBAN.md][kanban] from
the Kanban database, and a hand copy drifts on the next board edit.

## Why the version has one source

Bears on [Scope][spec-012-scope].

`__version__` in `django_strawberry_framework/__init__.py` is the only version literal a release
edits. `pyproject.toml` declares the version dynamic and `[tool.hatch.version]` points hatchling at
the package init, so the distribution metadata is derived from the runtime value and the two cannot
disagree; the editable root entry in `uv.lock` carries no version to drift either.

- **Declare the version in both `pyproject.toml` and the init.** Rejected: two literals kept in
  lockstep by hand is a pairing nothing enforces, and a bump that edits one of them ships
  inconsistent metadata.
- **`tests/base/test_init.py::test_version` still pins a literal.** It reads `__version__` and
  compares it to the expected string, so a release cut edits the test in the same change; an
  accidental edit to the init literal fails the suite.

## Why the spec states an obligation rather than a version

Bears on [Scope][spec-012-scope].

The card cut `0.0.4`, but every later release moves the same surfaces. A spec that said "the package
is at `0.0.4`" would be false one release later, so `## Scope` states the release obligation (one
source, the test literal, the changelog entry) and confines `0.0.4`-specific facts to the `0.0.4`
changelog entry, which is unchanged since the cut.

- **Restate the versioning policy in the spec.** Rejected: [`CHANGELOG.md`][changelog]
  `## Versioning` owns it for every release (strict Semantic Versioning does not apply during
  `0.0.x`), and a per-release spec restating a repository-wide policy drifts from it.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-012]: ../spec-012-version_release_alignment-0_0_4.md
[spec-012-card-snapshot]: ../spec-012-version_release_alignment-0_0_4.md#card-snapshot
[spec-012-scope]: ../spec-012-version_release_alignment-0_0_4.md#scope

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
