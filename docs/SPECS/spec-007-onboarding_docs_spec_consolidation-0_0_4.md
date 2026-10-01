# Spec: 0.0.4 onboarding docs and spec consolidation

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-007-0.0.4`).
Status: shipped. A card-snapshot spec: the file is the card's `SpecDoc` target.
Owner: package maintainer.

Why the spec is a card snapshot, and why its scope states each file's role rather than its contents, lives in its companion [rationale file][spec-007-rationale].

## Card snapshot

- Card: `DONE-007-0.0.4`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

The onboarding documentation is divided by the question each file answers, so that no two files answer the same one.

- Root [`README.md`][root-readme] is the canonical documentation map: positioning, status, and the pointer set into the rest of this set.
- [`docs/README.md`][readme] is the entry point for *using* the package — installation, quick start, running the example project — and the place a consumer reads runtime behavior, [optimizer behavior][glossary-djangooptimizerextension] included.
- [`CONTRIBUTING.md`][contributing] is the entry point for *working on* the package: development setup, test suite, formatting, versioning, build, and publish.
- [`docs/GLOSSARY.md`][glossary] is the capability catalog — every catalogued capability gets one entry, and every entry a stable anchor, so the rest of the documentation links to it rather than re-explaining it.
- [`docs/TREE.md`][tree] is the detailed layout and test-tree reference.
- [`CHANGELOG.md`][changelog] is the release record.
- A completed spec's shipped behavior folds into [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], and [KANBAN.md][kanban]; the spec file itself is retained under `docs/SPECS/` and describes the current code ([`START.md`][start] "Reconciling a spec with the tree"). The lifecycle around it — filename pattern, fold-in targets, and archival — is owned by the [`AGENTS.md`][agents] design-docs rule and [`docs/builder/BUILD.md`][build] `## Spec and build-plan filename pattern`.
- The card shipped documentation only: no package surface and no upstream-parity change.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md
[root-readme]: ../../README.md
[start]: ../../START.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-007-rationale]: appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
