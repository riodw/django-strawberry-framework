# Rationale: spec-013 — Real M2M coverage (deliberation, rejected alternatives)

Deliberative companion to [`spec-013-real_m2m_coverage-0_0_4.md`][spec-013]. The spec is the
contract; this file records why it has the shape it has. The spec has no numbered Decisions, so each
entry is keyed to a spec section.

## Why the spec is a card snapshot

Bears on [Card snapshot][spec-013-card-snapshot].

The file is the card's `SpecDoc` target, which the kanban app requires of every `done` card
(`examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_spec`). The snapshot names only
the card: labels, priority, relative size, and item rows are rendered into [KANBAN.md][kanban] from
the Kanban database, and a hand copy drifts on the next board edit.

## Why the coverage runs against real managed models

Bears on [Scope][spec-013-scope].

An unmanaged fixture model has no table, so a relation edge on one can be asserted as annotation
shape but never resolved through a query, and the M2M join table that proves batched loading never
exists. Each cardinality is therefore carried by a migrated model in the `library` example app,
where the same edge can be pinned at the package tier and over the wire.

## Why `## Scope` names every edge and every test

Bears on [Scope][spec-013-scope].

A summary such as "added package-level and HTTP-level coverage" is true and uncheckable. The spec
names the six edges as a cardinality table and each pinning test by `path::QualifiedName`, so a
rename or deletion fails the citation gate instead of silently orphaning the claim.

- **State the coverage as a count.** Rejected: a count rots silently and cannot be grepped.
- **Name the models but not the tests.** Rejected: the card's deliverable is coverage, and the
  assertions are the half a later refactor can remove.
- **Pin M2M at the SQL level.** The live tests assert the `library_book_genres` join table appears in
  the prefetch query, which a per-row fallback could not produce; response data alone cannot tell a
  batched prefetch from N+1 loading.
- **Read the list shape from the served schema.**
  `examples/fakeshop/test_query/test_library_api.py::test_book_genres_m2m_renders_as_list_shape_live`
  reads `[GenreType!]!` by introspection over HTTP, which is stronger than reading a private type map
  of a locally constructed schema.
- **The forward FK is stated as a two-query `Prefetch`.** `ShelfType` declares a `get_queryset`
  visibility hook, and a join would surface shelf rows the hook excludes, so the `select_related`
  plan executes as a visibility-scoped `Prefetch`.

## Why the spec names `Book.genres` explicitly

Bears on [Scope][spec-013-scope], closing paragraph.

The `library` app is extended by many later cards (generic relations, a second `ManyToManyField` on
`Shelf`, scalar converters, keyset cursors, inheritance shapes). Naming this card's M2M edge and
putting the rest outside its scope keeps the claim checkable in a file other cards keep growing.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-013]: ../spec-013-real_m2m_coverage-0_0_4.md
[spec-013-card-snapshot]: ../spec-013-real_m2m_coverage-0_0_4.md#card-snapshot
[spec-013-scope]: ../spec-013-real_m2m_coverage-0_0_4.md#scope

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
