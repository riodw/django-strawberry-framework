"""Live GraphQL HTTP tests for the kanban board docs-as-data API.

Mirrors ``test_products_api.py``'s harness. Seeds a small deterministic board
directly (not via the importer, so assertions stay independent of how the real
``KANBAN.md`` evolves) and drives the kanban schema end to end:

* ``RelatedFilter`` on a lookup ``key`` (the FK-dense filter surface) -- the
  central showcase of this app;
* own-PK Relay ``GlobalID`` filtering (``id: { in: [...] }``) on ``CardType``;
* plain-integer ``id: { in: [...] }`` on the non-Relay ``CardItemType``;
* M2M-through filtering + selection (``parity`` / ``parityClaims``);
* self-referential M2M filtering + selection (``dependencies``);
* normalized card-to-card references parsed out of prose
  (``outgoingReferences``);
* O2O selection (``spec``) plus the reverse ``uuid`` side-table and the
  inherited ``createdDate`` audit column;
* reverse-FK from a lookup (``status { cards }``).
"""

import pytest
from apps.glossary import models as glossary_models
from apps.kanban import models, services
from graphql_client import assert_graphql_data as _assert_graphql_data
from graphql_client import assert_graphql_success as _graphql_data
from graphql_client import post_graphql
from strawberry import relay


def _seed_board():
    """A tiny deterministic board: two cards + docs + lookups + edges."""
    done = models.Status.objects.create(key="done", label="Done", order=3)
    todo = models.Status.objects.create(key="todo", label="To Do", order=0)
    wip = models.Status.objects.create(key="wip", label="In Progress", order=2)
    alpha = models.Milestone.objects.create(key="alpha", label="Alpha", order=0)
    version = models.TargetVersion.objects.create(number="0.0.8", milestone=alpha)
    xl = models.RelativeSize.objects.create(key="xl", label="XL", order=4)
    size_m = models.RelativeSize.objects.create(key="m", label="M", order=2)
    high = models.Priority.objects.create(key="high", label="High", order=0)
    graphene = models.Upstream.objects.create(
        key="graphene_django",
        label="graphene-django",
        emoji="⚛️",
        order=0,
    )
    straw = models.Upstream.objects.create(
        key="strawberry_django",
        label="strawberry-graphql-django",
        emoji="🍓",
        order=1,
    )
    required = models.ParityLevel.objects.create(key="required", label="Required", order=0)
    adjacent = models.ParityLevel.objects.create(key="adjacent", label="Parity-adjacent", order=1)
    scope = models.Section.objects.create(key="scope", label="Scope", order=0)
    dependency = models.CardReferenceKind.objects.create(
        key="dependency",
        label="Dependency",
        order=0,
    )
    reference_doc = models.BoardDocKind.objects.create(
        key="reference",
        label="Reference",
        order=1,
    )
    glossary_status = glossary_models.GlossaryStatus.objects.create(
        key="shipped",
        label="Shipped",
        order=0,
    )
    filterset_term = glossary_models.GlossaryTerm.objects.create(
        title="`FilterSet`",
        title_sort="filterset",
        anchor="filterset",
        status=glossary_status,
        status_text="shipped (`0.0.8`)",
        body="Declarative filtering sidecar.",
        entry_order=1,
        index_order=1,
    )
    related_filter_term = glossary_models.GlossaryTerm.objects.create(
        title="`RelatedFilter`",
        title_sort="relatedfilter",
        anchor="relatedfilter",
        status=glossary_status,
        status_text="shipped (`0.0.8`)",
        body="Cross-relation filter helper.",
        entry_order=2,
        index_order=2,
    )
    filters_card = models.Card.objects.create(
        title="Filtering subsystem",
        number=21,
        status=todo,
        target_version=version,
        priority=high,
        relative_size=xl,
    )
    models.SpecDoc.objects.create(
        card=filters_card,
        name="spec-027-filters-0_0_8",
        path="docs/SPECS/spec-027-filters-0_0_8.md",
    )
    # A done card requires >=1 glossary link
    # (examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_glossary_link);
    # attach the links BEFORE flipping the card to ``done`` so the pre_save
    # validation is satisfied.
    glossary_link = models.CardGlossaryTerm.objects.create(
        card=filters_card,
        term=filterset_term,
        raw_text="FilterSet",
        order=0,
    )
    related_glossary_link = models.CardGlossaryTerm.objects.create(
        card=filters_card,
        term=related_filter_term,
        raw_text="RelatedFilter",
        order=1,
    )
    # The status state machine forbids todo -> done; bridge through wip.
    filters_card.status = wip
    filters_card.save(update_fields=["status"])
    filters_card.status = done
    filters_card.save(update_fields=["status"])
    current_tracked_path = models.TrackedPath.objects.create(
        path="django_strawberry_framework/filters/base.py",
        state=models.TRACKED_PATH_CURRENT,
    )
    historical_tracked_path = models.TrackedPath.objects.create(
        path="django_strawberry_framework/old_filters.py",
        state=models.TRACKED_PATH_HISTORICAL,
    )
    filters_card.changed_files.add(
        current_tracked_path,
        through_defaults={"kind": models.CARD_PATH_LINK_CHANGED},
    )
    conn_card = models.Card.objects.create(
        title="DjangoConnectionField",
        number=24,
        status=todo,
        target_version=version,
        priority=high,
        relative_size=size_m,
    )
    conn_card.changed_files.add(
        historical_tracked_path,
        through_defaults={"kind": models.CARD_PATH_LINK_PREDICTED},
    )
    reference = models.CardReference.objects.create(
        source_card=conn_card,
        target_card=filters_card,
        kind=dependency,
        raw_text="planned; gated on `DONE-021-0.0.8`",
        order=0,
    )
    models.ParityClaim.objects.create(card=filters_card, upstream=graphene, level=required)
    models.ParityClaim.objects.create(card=filters_card, upstream=straw, level=required)
    models.ParityClaim.objects.create(card=conn_card, upstream=straw, level=adjacent)

    board_doc = models.BoardDoc.objects.create(
        key="snapshot",
        kind=reference_doc,
        title="Snapshot",
        order=0,
        body="The active filter card is {{card_ref:0}}.",
    )
    board_doc_reference = models.BoardDocCardReference.objects.create(
        doc=board_doc,
        card=filters_card,
        raw_text="DONE-021-0.0.8",
        order=0,
    )

    item_filters = models.CardItem.objects.create(
        card=filters_card,
        section=scope,
        text="FilterSet",
        order=0,
    )
    item_conn = models.CardItem.objects.create(
        card=conn_card,
        section=scope,
        text="Relay connection field",
        order=0,
    )

    return {
        "filters": filters_card,
        "conn": conn_card,
        "item_filters": item_filters,
        "item_conn": item_conn,
        "reference": reference,
        "glossary_link": glossary_link,
        "related_glossary_link": related_glossary_link,
        "board_doc": board_doc,
        "board_doc_reference": board_doc_reference,
        "current_tracked_path": current_tracked_path,
        "historical_tracked_path": historical_tracked_path,
    }


@pytest.mark.django_db
def test_filter_cards_by_status_key_via_related_filter():
    """The FK-dense surface: filter cards by the related ``status.key``."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "done" } } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}]},
    )


@pytest.mark.django_db
def test_filter_cards_by_own_pk_relay_global_id_in():
    """Own-PK Relay ``id: { in: [...] }`` accepts a list of GlobalIDs."""
    seed = _seed_board()
    gid_filters = str(
        relay.GlobalID(type_name=models.Card._meta.label_lower, node_id=str(seed["filters"].pk)),
    )
    gid_conn = str(
        relay.GlobalID(type_name=models.Card._meta.label_lower, node_id=str(seed["conn"].pk)),
    )
    _assert_graphql_data(
        f"""
        query {{
          allCards(filter: {{ id: {{ in: ["{gid_filters}", "{gid_conn}"] }} }}) {{
            title
          }}
        }}
        """,
        {"allCards": [{"title": "Filtering subsystem"}, {"title": "DjangoConnectionField"}]},
    )


@pytest.mark.django_db
def test_filter_non_relay_card_items_by_plain_integer_id_in():
    """``CardItemType`` is non-Relay, so ``id: { in: [...] }`` takes plain ints."""
    seed = _seed_board()
    _assert_graphql_data(
        f"""
        query {{
          allKanbanCardItems(filter: {{ id: {{ in: [{seed["item_filters"].pk}, {seed["item_conn"].pk}] }} }}) {{
            text
          }}
        }}
        """,
        {"allKanbanCardItems": [{"text": "FilterSet"}, {"text": "Relay connection field"}]},
    )


@pytest.mark.django_db
def test_select_card_glossary_terms_and_filter_by_term_anchor():
    """Kanban cards expose ordered glossary-term links through the live API."""
    seed = _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(
            filter: {
              glossaryLinks: {
                term: { anchor: { exact: "filterset" } }
              }
            }
          ) {
            title
            glossaryLinks {
              uuid { id }
              rawText
              order
              term {
                title
                anchor
                statusText
              }
            }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "Filtering subsystem",
                    "glossaryLinks": [
                        {
                            "uuid": {"id": str(seed["glossary_link"].uuid.id)},
                            "rawText": "FilterSet",
                            "order": 0,
                            "term": {
                                "title": "`FilterSet`",
                                "anchor": "filterset",
                                "statusText": "shipped (`0.0.8`)",
                            },
                        },
                        {
                            "uuid": {"id": str(seed["related_glossary_link"].uuid.id)},
                            "rawText": "RelatedFilter",
                            "order": 1,
                            "term": {
                                "title": "`RelatedFilter`",
                                "anchor": "relatedfilter",
                                "statusText": "shipped (`0.0.8`)",
                            },
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_select_and_filter_cards_by_changed_tracked_paths():
    """Kanban cards expose linked tracked paths through the live API."""
    seed = _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(
            filter: {
              changedFiles: {
                path: { exact: "django_strawberry_framework/filters/base.py" }
              }
            }
          ) {
            title
            changedFiles {
              uuid { id }
              path
              isCurrent
              isDirectory
            }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "Filtering subsystem",
                    "changedFiles": [
                        {
                            "uuid": {"id": str(seed["current_tracked_path"].uuid.id)},
                            "path": "django_strawberry_framework/filters/base.py",
                            "isCurrent": True,
                            "isDirectory": False,
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_filter_cards_by_own_pk_relay_id_isnull_coerces_boolean():
    """Spec-021 H1: own-PK Relay ``id: { isNull: ... }`` coerces a Boolean.

    Regression for forcing every non-``in`` lookup on a Relay PK to
    ``GlobalIDFilter``, which typed ``isNull`` as ``String`` so
    ``id: { isNull: true }`` failed coercion ("String cannot represent a non
    string value: true"). A PK is never null: ``isNull: false`` matches every
    card and ``isNull: true`` matches none. (Ordering / pattern lookups are now
    dropped from a Relay PK's surface rather than emitted as corrupt strings.)
    """
    _seed_board()
    _assert_graphql_data(
        """
        query {
          present: allCards(filter: { id: { isNull: false } }) { title }
          absent: allCards(filter: { id: { isNull: true } }) { title }
        }
        """,
        {
            "present": [{"title": "Filtering subsystem"}, {"title": "DjangoConnectionField"}],
            "absent": [],
        },
    )


@pytest.mark.django_db
def test_filter_non_relay_card_items_by_plain_integer_id_exact():
    """Spec-021 H2: non-Relay int PK ``id: { exact: <int> }`` accepts an Int.

    Companion to the ``id: { in: [...] }`` case: the scalar catch-all now uses
    the ``AutoField`` model field (-> ``Int``) as the source of truth instead
    of django-filter's ``NumberFilter`` form field (a ``DecimalField`` ->
    ``Decimal``). Filtering by a plain integer returns the matching item.
    """
    seed = _seed_board()
    _assert_graphql_data(
        f"""
        query {{
          allKanbanCardItems(filter: {{ id: {{ exact: {seed["item_filters"].pk} }} }}) {{
            text
          }}
        }}
        """,
        {"allKanbanCardItems": [{"text": "FilterSet"}]},
    )


@pytest.mark.django_db
def test_filter_cards_by_m2m_through_parity_key():
    """M2M-through traversal: only the card with a graphene parity claim matches."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { parity: { key: { exact: "graphene_django" } } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}]},
    )


@pytest.mark.django_db
def test_filter_cards_by_self_referential_dependency():
    """Self-referential M2M: cards depending on card #21."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { dependencies: { number: { exact: 21 } } }) {
            title
            dependencies { title }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "DjangoConnectionField",
                    "dependencies": [{"title": "Filtering subsystem"}],
                },
            ],
        },
    )


def _nested_dependency_filter(depth: int) -> str:
    """Build a ``dependencies``-nested filter literal ``depth`` levels deep."""
    body = "number: { exact: 21 }"
    for _ in range(depth):
        body = f"dependencies: {{ {body} }}"
    return body


@pytest.mark.django_db
def test_deeply_nested_self_referential_dependency_filter_is_capped():
    """A pathologically deep self-referential ``dependencies`` filter raises a
    typed depth-cap error, not a raw ``RecursionError`` (report Defect 5).

    ``CardFilter.dependencies`` is a real self-referential ``RelatedFilter``, so a
    client can nest the same branch arbitrarily deep. Before the fix the
    input-driven visibility derivation recursed once per level and blew the
    Python stack (a 500). The shared traversal budget now caps it at
    ``_MAX_LOGIC_DEPTH`` and surfaces a catchable ``ConfigurationError``.
    """
    _seed_board()
    query = "query { allCards(filter: { " + _nested_dependency_filter(10) + " }) { title } }"
    response = post_graphql(query)
    # A typed cap error is a normal GraphQL error (HTTP 200 + ``errors``), never a
    # 500 stack overflow.
    assert response.status_code == 200
    payload = response.json()
    # A top-level resolver error nulls ``data`` and reports under ``errors``.
    assert payload["data"] is None
    messages = " ".join(error["message"] for error in payload["errors"]).lower()
    assert "recursion" not in messages
    assert "nesting" in messages or "depth" in messages


@pytest.mark.django_db
def test_filter_and_select_normalized_card_references():
    """Card references expose the parsed kind instead of only prose."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { outgoingReferences: { kind: { key: { exact: "dependency" } } } }) {
            title
            outgoingReferences {
              targetCard { title }
              kind { key }
              rawText
              order
            }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "DjangoConnectionField",
                    "outgoingReferences": [
                        {
                            "targetCard": {"title": "Filtering subsystem"},
                            "kind": {"key": "dependency"},
                            "rawText": "planned; gated on `DONE-021-0.0.8`",
                            "order": 0,
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_select_m2m_through_parity_claims_with_edge_level():
    """Select the through-edge data (level + upstream) off a card."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "todo" } } }) {
            title
            parityClaims {
              level { key }
              upstream { key emoji }
            }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "DjangoConnectionField",
                    "parityClaims": [
                        {
                            "level": {"key": "adjacent"},
                            "upstream": {"key": "strawberry_django", "emoji": "🍓"},
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_select_o2o_spec_uuid_side_table_and_timestamps():
    """O2O spec link, the reverse ``uuid`` side-table, and inherited timestamps."""
    _seed_board()
    data = _graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "done" } } }) {
            title
            createdDate
            spec { name url }
            uuid { id }
          }
        }
        """,
    )
    (card,) = data["allCards"]
    assert card["title"] == "Filtering subsystem"
    assert card["spec"] == {
        "name": "spec-027-filters-0_0_8",
        "url": (
            "https://github.com/riodw/django-strawberry-framework/blob/main/"
            "docs/SPECS/spec-027-filters-0_0_8.md"
        ),
    }
    assert card["createdDate"] is not None
    # The UUID side-table row exists and exposes a UUID scalar (a UUIDField PK).
    assert len(card["uuid"]["id"]) == 36


@pytest.mark.django_db
def test_reverse_fk_from_lookup_status_to_cards():
    """Query the board from the option side: ``status { cards }`` reverse-FK."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allKanbanStatuses(filter: { key: { exact: "done" } }) {
            key
            cards { title }
          }
        }
        """,
        {"allKanbanStatuses": [{"key": "done", "cards": [{"title": "Filtering subsystem"}]}]},
    )


@pytest.mark.django_db
def test_select_board_docs_and_lookup_roots_for_static_dashboard():
    """The static dashboard can fetch board docs and FK options directly."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allKanbanBoardDocs {
            key
            title
            body
            kind { key }
            cardReferences {
              rawText
              order
              card { title number slug }
            }
          }
          allKanbanPriorities { key }
          allKanbanParityLevels { key }
          allKanbanSections { key }
          allKanbanReferenceKinds { key }
          allKanbanBoardDocKinds { key docs { key } }
        }
        """,
        {
            "allKanbanBoardDocs": [
                {
                    "key": "snapshot",
                    "title": "Snapshot",
                    "body": "The active filter card is {{card_ref:0}}.",
                    "kind": {"key": "reference"},
                    "cardReferences": [
                        {
                            "rawText": "DONE-021-0.0.8",
                            "order": 0,
                            "card": {
                                "title": "Filtering subsystem",
                                "number": 21,
                                "slug": "filtering_subsystem",
                            },
                        },
                    ],
                },
            ],
            "allKanbanPriorities": [{"key": "high"}],
            "allKanbanParityLevels": [{"key": "required"}, {"key": "adjacent"}],
            "allKanbanSections": [{"key": "scope"}],
            "allKanbanReferenceKinds": [{"key": "dependency"}],
            "allKanbanBoardDocKinds": [{"key": "reference", "docs": [{"key": "snapshot"}]}],
        },
    )


# ---------------------------------------------------------------------------
# Logical composition (and / or / not)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_filter_cards_logical_or_across_statuses():
    """``or: [...]`` unions two status branches (ordered by number)."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: {
            or: [
              { status: { key: { exact: "done" } } },
              { status: { key: { exact: "todo" } } }
            ]
          }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}, {"title": "DjangoConnectionField"}]},
    )


@pytest.mark.django_db
def test_filter_cards_logical_not_scalar():
    """``not: {...}`` negates a scalar branch -- every card whose number isn't 21.

    (Negation is exercised over a direct scalar field; ``not`` over a
    *RelatedFilter* traversal is a separate, narrower path in the filter
    subsystem and is not asserted here.)
    """
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { not: { number: { exact: 21 } } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "DjangoConnectionField"}]},
    )


@pytest.mark.django_db
def test_filter_cards_logical_and_number_range():
    """``and: [...]`` intersects two number-range branches."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: {
            and: [{ number: { gte: 20 } }, { number: { lt: 24 } }]
          }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}]},
    )


# ---------------------------------------------------------------------------
# Per-field "__all__" lookups on Card's own scalar fields
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_filter_cards_by_title_icontains():
    """``title: { iContains }`` -- a lookup that exists only via per-field "__all__"."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { title: { iContains: "subsystem" } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}]},
    )


@pytest.mark.django_db
def test_filter_cards_by_number_gt():
    """``number: { gt }`` numeric lookup on the card's own integer field."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { number: { gt: 21 } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "DjangoConnectionField"}]},
    )


# ---------------------------------------------------------------------------
# More RelatedFilter traversals
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_filter_cards_by_milestone_key():
    """Filter by the related ``milestone.key``.

    Both cards target version ``0.0.8``, whose milestone is ``alpha``; the
    ``milestone`` field is derived from ``target_version`` on save, so both
    resolve to ``alpha`` and match.
    """
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { milestone: { key: { exact: "alpha" } } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}, {"title": "DjangoConnectionField"}]},
    )


@pytest.mark.django_db
def test_filter_cards_by_related_size_order_numeric_lookup():
    """A numeric lookup (``order: { gte }``) reached through the size RelatedFilter."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { relativeSize: { order: { gte: 4 } } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}]},
    )


@pytest.mark.django_db
def test_filter_cards_by_items_text_reverse_fk_related_filter():
    """Reverse-FK RelatedFilter: filter cards by a child ``CardItem.text``."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { items: { text: { iContains: "connection" } } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "DjangoConnectionField"}]},
    )


@pytest.mark.django_db
def test_filter_cards_combined_related_and_scalar():
    """Top-level fields AND together: a RelatedFilter plus a scalar lookup."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "done" } }, number: { gte: 21 } }) {
            title
          }
        }
        """,
        {"allCards": [{"title": "Filtering subsystem"}]},
    )


@pytest.mark.django_db
def test_filter_cards_empty_result():
    """A filter matching nothing returns an empty list, not an error."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { title: { exact: "Nonexistent Card" } }) {
            title
          }
        }
        """,
        {"allCards": []},
    )


# ---------------------------------------------------------------------------
# Deeper selections
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_select_multi_fk_fanout_and_second_hop():
    """Select every FK lookup off a card, plus the second hop targetVersion -> milestone."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "todo" } } }) {
            title
            status { key }
            priority { key }
            relativeSize { key order }
            milestone { key }
            targetVersion { number major minor patch milestone { key } }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "DjangoConnectionField",
                    "status": {"key": "todo"},
                    "priority": {"key": "high"},
                    "relativeSize": {"key": "m", "order": 2},
                    "milestone": {"key": "alpha"},
                    "targetVersion": {
                        "number": "0.0.8",
                        "major": 0,
                        "minor": 0,
                        "patch": 8,
                        "milestone": {"key": "alpha"},
                    },
                },
            ],
        },
    )


@pytest.mark.django_db
def test_select_self_referential_dependents_reverse():
    """The reverse side of the self-M2M: ``dependents`` off the depended-on card."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "done" } } }) {
            title
            dependents { title }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "Filtering subsystem",
                    "dependents": [{"title": "DjangoConnectionField"}],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_reverse_m2m_from_upstream_to_cards():
    """M2M-through reverse: an ``Upstream`` lists the cards that claim it."""
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allKanbanUpstreams(filter: { key: { exact: "strawberry_django" } }) {
            key
            cards { title }
          }
        }
        """,
        {
            "allKanbanUpstreams": [
                {
                    "key": "strawberry_django",
                    "cards": [
                        {"title": "Filtering subsystem"},
                        {"title": "DjangoConnectionField"},
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_select_lookup_uuid_side_table():
    """Lookups carry a UUID side-row too (the signal is connected for every model)."""
    _seed_board()
    data = _graphql_data(
        """
        query {
          allKanbanStatuses(filter: { key: { exact: "done" } }) {
            key
            uuid { id }
          }
        }
        """,
    )
    (status,) = data["allKanbanStatuses"]
    assert status["key"] == "done"
    assert len(status["uuid"]["id"]) == 36


@pytest.mark.django_db
def test_select_labels_m2m():
    """Plain M2M selection: a card's labels."""
    _seed_board()
    filters_card = models.Card.objects.get(title="Filtering subsystem")
    filters_card.labels.add(models.Label.objects.create(key="security", color="#f00"))
    _assert_graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "done" } } }) {
            title
            labels { key }
          }
        }
        """,
        {
            "allCards": [
                {"title": "Filtering subsystem", "labels": [{"key": "security"}]},
            ],
        },
    )


@pytest.mark.django_db
def test_order_kanban_statuses_by_key_desc():
    """``orderBy: [{ key: DESC }]`` reorders the statuses list (DONE-028 order wiring)."""
    _seed_board()
    expected = [
        {"key": key}
        for key in models.Status.objects.order_by("-key").values_list("key", flat=True)
    ]
    _assert_graphql_data(
        "query { allKanbanStatuses(orderBy: [{ key: DESC }]) { key } }",
        {"allKanbanStatuses": expected},
    )


# ---------------------------------------------------------------------------
# Phase 2: work-tracking dimension (transitions / attempts / decisions / ready)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ready_cards_over_http_excludes_done_and_blocked():
    """``readyCards`` returns unblocked ``todo`` cards whose dependencies are done.

    The seeded board's ``DjangoConnectionField`` (todo) depends only on the
    shipped ``Filtering subsystem`` (done), so it is ready; the done card itself
    is not ``todo`` and is excluded.
    """
    _seed_board()
    _assert_graphql_data(
        "query { readyCards { title } }",
        {"readyCards": [{"title": "DjangoConnectionField"}]},
    )


@pytest.mark.django_db
def test_set_card_status_transition_selectable_from_card():
    """A ``CardTransition`` written by the service is selectable off its card."""
    seed = _seed_board()
    services.set_card_status(seed["conn"], "wip", actor="maintainer")
    _assert_graphql_data(
        """
        query {
          allCards(filter: { status: { key: { exact: "wip" } } }) {
            title
            transitions {
              fromStatus { key }
              toStatus { key }
              actor { key kind }
            }
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "DjangoConnectionField",
                    "transitions": [
                        {
                            "fromStatus": {"key": "todo"},
                            "toStatus": {"key": "wip"},
                            "actor": {"key": "maintainer", "kind": "human"},
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_query_seeded_actor_and_attempt_outcome_lookups_with_filter():
    """The migration-seeded worklog lookups are queryable with a RelatedFilter."""
    _assert_graphql_data(
        """
        query {
          maintainers: allKanbanActors(filter: { kind: { exact: human } }) { key kind }
          succeeded: allKanbanAttemptOutcomes(filter: { key: { exact: "succeeded" } }) { key }
          coverage: allKanbanVerificationKinds(filter: { key: { exact: "coverage_gate" } }) { key }
        }
        """,
        {
            "maintainers": [{"key": "maintainer", "kind": "human"}],
            "succeeded": [{"key": "succeeded"}],
            "coverage": [{"key": "coverage_gate"}],
        },
    )


@pytest.mark.django_db
def test_query_work_attempts_and_decisions_root_fields():
    """Root list fields for WorkAttempt and Decision expose their rows + filters."""
    seed = _seed_board()
    actor = models.Actor.objects.get(key="maintainer")
    models.WorkAttempt.objects.create(
        card=seed["conn"],
        actor=actor,
        summary="first attempt",
        outcome=models.AttemptOutcome.objects.get(key="succeeded"),
    )
    models.Decision.objects.create(
        card=seed["conn"],
        actor=actor,
        question="Ship now?",
        choice="Yes",
    )
    _assert_graphql_data(
        """
        query {
          allKanbanWorkAttempts(filter: { outcome: { key: { exact: "succeeded" } } }) {
            summary
            outcome { key }
            card { title }
          }
          allKanbanDecisions {
            question
            choice
            card { title }
          }
        }
        """,
        {
            "allKanbanWorkAttempts": [
                {
                    "summary": "first attempt",
                    "outcome": {"key": "succeeded"},
                    "card": {"title": "DjangoConnectionField"},
                },
            ],
            "allKanbanDecisions": [
                {
                    "question": "Ship now?",
                    "choice": "Yes",
                    "card": {"title": "DjangoConnectionField"},
                },
            ],
        },
    )


def test_kanban_card_order_input_type_exposes_only_column_backed_all_fields():
    """``Meta.fields = "__all__"`` exposes FK columns but not reverse/M2M managers."""
    data = _graphql_data(
        """
        query {
          __type(name: "CardOrderInputType") {
            inputFields {
              name
              type {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
        """,
    )
    fields = {field["name"]: field for field in data["__type"]["inputFields"]}

    for name in (
        "status",
        "targetVersion",
        "priority",
        "relativeSize",
    ):
        field_type = fields[name]["type"]
        while field_type.get("ofType") is not None:
            field_type = field_type["ofType"]
        assert field_type["name"] == "Ordering"

    # ``milestone`` is now a derived property (no column), so it is absent from
    # the order-input surface alongside the reverse/M2M/property fields.
    assert {
        "milestone",
        "dependencies",
        "dependents",
        "parity",
        "labels",
        "glossaryTerms",
        "items",
        "uuid",
    }.isdisjoint(fields)


@pytest.mark.django_db
def test_select_derived_card_id_slug_blocked_and_ready_fields():
    """The derived ``cardId`` / ``slug`` / ``isBlocked`` / ``isReady`` fields resolve.

    The seeded board's ``Filtering subsystem`` is ``done`` (its card id drops the
    milestone segment and it is neither blocked nor ready); ``DjangoConnectionField``
    is ``todo`` and depends only on that shipped card, so it is ready and unblocked.
    """
    _seed_board()
    _assert_graphql_data(
        """
        query {
          allCards(orderBy: [{ number: ASC }]) {
            title
            cardId
            slug
            isBlocked
            isReady
          }
        }
        """,
        {
            "allCards": [
                {
                    "title": "Filtering subsystem",
                    "cardId": "DONE-021-0.0.8",
                    "slug": "filtering_subsystem",
                    "isBlocked": False,
                    "isReady": False,
                },
                {
                    "title": "DjangoConnectionField",
                    "cardId": "TODO-ALPHA-024-0.0.8",
                    "slug": "djangoconnectionfield",
                    "isBlocked": False,
                    "isReady": True,
                },
            ],
        },
    )


@pytest.mark.django_db
def test_ready_cards_excludes_a_blocked_todo_card():
    """A ``todo`` card gated by an unfinished ``blocked_by`` edge is not ``ready``."""
    _seed_board()
    blocked_by = models.CardReferenceKind.objects.create(
        key="blocked_by",
        label="Blocked by",
        order=1,
    )
    blocker = models.Card.objects.get(number=24)  # DjangoConnectionField, still todo
    blocked = models.Card.objects.create(
        title="Blocked feature",
        number=25,
        status=models.Status.objects.get(key="todo"),
        target_version=models.TargetVersion.objects.get(number="0.0.8"),
        priority=models.Priority.objects.get(key="high"),
        relative_size=models.RelativeSize.objects.get(key="m"),
    )
    models.CardReference.objects.create(
        source_card=blocked,
        target_card=blocker,
        kind=blocked_by,
    )

    # ``Blocked feature`` is todo but blocked, so it stays out of ``readyCards``;
    # ``DjangoConnectionField`` (todo, dependency done) remains ready.
    _assert_graphql_data(
        "query { readyCards { title } }",
        {"readyCards": [{"title": "DjangoConnectionField"}]},
    )
    blocked.refresh_from_db()
    assert blocked.is_blocked is True
    assert blocked.is_ready is False
