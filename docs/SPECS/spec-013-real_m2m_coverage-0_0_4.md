# Spec: Real M2M coverage

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-013-0.0.4`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

Deliberation and this spec's change record live in its companion [rationale file][spec-013-rationale]: what the card's three commits actually did, why unmanaged fixtures could not carry the contract, where the card's schema-shape test went and what replaced it, how the `library` app grew afterwards, and every claim this spec once made and may no longer make.

## Card snapshot

- Card: `DONE-013-0.0.4`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

Relation-cardinality coverage runs against real managed models in a real example app, never against a test-only fixture app.

**The retired fixtures.** `tests/fixtures/` held an unmanaged `tests_cardinality` app — five `managed = False` models (`User`, `Profile`, `Author`, `Tag`, `Book`) carrying six relation edges. Because the app was unmanaged it had no table, so those edges could only ever be asserted as annotation shape and never resolved through a query. The directory does not exist, no source file or test references `tests_cardinality` or `cardinality_models`, and no substitute fixture app replaces it.

**The six edges, on real models.** Each cardinality the fixtures carried is carried by a managed model in the [`library`][library-models] example app, and the six together are the [M2M traversal][glossary-relation-handling] and adjacent-cardinality surface this card owns:

| Cardinality | `library` edge |
|---|---|
| forward `OneToOneField` | `MembershipCard.patron` |
| reverse `OneToOneField` | `Patron.card` |
| forward `ForeignKey` | `Book.shelf` |
| reverse `ForeignKey` | `Shelf.books` |
| forward `ManyToManyField` | `Book.genres` |
| reverse `ManyToManyField` | `Genre.books` |

**Package-tier coverage** pins annotation shape and optimizer planning for those edges:

- [`tests/types/test_definition_order.py`][test-types-definition-order] `::test_many_to_many_forward_and_reverse_relations_resolve` — `BookType.genres` and `GenreType.books` resolve to `list[…]` of the peer type, `ShelfType.books` to `list[BookType]`, and `BookType.shelf` to `ShelfType`.
- [`tests/types/test_definition_order.py`][test-types-definition-order] `::test_one_to_one_forward_and_reverse_relations_resolve` — `MembershipCardType.patron` is `PatronType`; `PatronType.card` is `MembershipCardType | None`.
- [`tests/optimizer/test_definition_order.py`][test-optimizer-definition-order] `::test_plan_relation_decisions_match_cardinality_after_finalization` — `plan_relation` returns `("prefetch", "default")` for `Book.genres` and `Genre.books`, and `("select", "default")` for both halves of the one-to-one pair.

**HTTP-tier coverage** pins the same edges through the live `/graphql/` endpoint, in [`examples/fakeshop/test_query/test_library_api.py`][test-library-api]:

- `::test_library_branch_shelf_book_loan_graph_over_http` and `::test_library_patron_card_and_genre_reverse_paths_over_http` — the traversal graph and the reverse one-to-one / reverse M2M paths in a real response body.
- `::test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http` and `::test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http` — the M2M is pinned at the SQL level, by asserting the `library_book_genres` join table appears in the prefetch query. A per-row fallback could not produce it.
- `::test_library_optimizer_selects_book_shelf_in_http_query` — the forward FK is planned as `select_related` in a served query and, because `ShelfType` declares a `get_queryset` visibility hook, that plan is downgraded to a visibility-scoped `Prefetch`: two queries, the first over `library_book` and the second over `library_shelf`.
- `::test_book_genres_m2m_renders_as_list_shape_live` — `BookType.genres` renders as `[GenreType!]!`, read from the served schema by introspection rather than from a locally constructed one.

**Example-app schema coverage** lives with the app, in [`examples/fakeshop/apps/library/tests/test_schema.py`][test-library-schema] `::test_project_schema_includes_library_types` (the project schema exposes `BookType` with `title`, `shelf`, and `genres`) and `::test_library_djangotype_declaration_order_stays_awkward`.

The `library` app carries more than these six edges — a generic relation and its proxy-model variant, a second `ManyToManyField` (`Shelf.alt_branches`) for write-side raw-pk input, a `BigIntegerField`, and the keyset-cursor models. Those belong to the cards that added them. This card's many-to-many edge is `Book.genres` / `Genre.books`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling

<!-- docs/SPECS/ -->
[spec-013-rationale]: appx/spec-013-real_m2m_coverage-0_0_4-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->
[test-optimizer-definition-order]: ../../tests/optimizer/test_definition_order.py
[test-types-definition-order]: ../../tests/types/test_definition_order.py

<!-- examples/ -->
[library-models]: ../../examples/fakeshop/apps/library/models.py
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py
[test-library-schema]: ../../examples/fakeshop/apps/library/tests/test_schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
