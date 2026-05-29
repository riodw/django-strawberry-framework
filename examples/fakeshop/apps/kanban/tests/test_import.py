"""Unit tests for the ``import_kanban`` parser + loader (phase 2).

Parser correctness and the ``UUIDModel`` ``post_save`` signal are not reachable
from a live ``/graphql/`` query, so they live here rather than under
``test_query/``. Pinned against a fixed two-card excerpt so the assertions stay
deterministic regardless of how the real ``KANBAN.md`` evolves.
"""

import uuid as uuid_module

import pytest

from apps.kanban import models, services

# Two cards: a shipped DONE card (no milestone segment, both-upstream parity,
# XL size) and a planned TODO card that depends on the first (parity-adjacent,
# an "S–M" size range using an en-dash).
EXCERPT = """## Board columns

### DONE-001-0.0.1 — First shipped thing

Priority: high

Parity: ⚛️&🍓 required

Severity: major

Status: shipped

Relative size: XL

Scope:

- alpha scope item
- beta scope item

Definition of done:

- did the thing

### TODO-ALPHA-002-0.0.2 — Second planned thing

Priority: medium

Parity: 🍓 parity-adjacent

Status: needs spec

Relative size: S–M

Dependencies:

- `First shipped thing` (`DONE-001-0.0.1`)

Scope:

- second scope item
"""


@pytest.mark.django_db
def test_import_board_counts():
    result = services.import_board(markdown=EXCERPT)
    assert result["cards"] == 2
    assert result["target_versions"] == 2
    assert result["items"] == 5  # 3 (scope×2 + dod) + 2 (deps + scope)
    assert result["parity_claims"] == 3  # 2 + 1
    assert result["dependency_edges"] == 1


@pytest.mark.django_db
def test_import_board_maps_lookup_fields():
    services.import_board(markdown=EXCERPT)

    first = models.Card.objects.get(title="First shipped thing")
    assert first.status.key == "done"
    assert first.milestone is None  # DONE drops the milestone segment in the ID
    assert first.target_version.number == "0.0.1"
    assert first.relative_size.key == "xl"
    assert first.relative_size_high is None
    assert first.priority.key == "high"
    assert first.severity.key == "major"
    assert first.planning_state.key == "shipped"
    assert first.parity_claims.count() == 2

    second = models.Card.objects.get(title="Second planned thing")
    assert second.status.key == "todo"
    assert second.milestone.key == "alpha"
    assert second.relative_size.key == "s"  # low bound of the "S–M" range
    assert second.relative_size_high.key == "m"  # high bound
    assert second.priority.key == "medium"
    assert second.severity is None
    assert second.planning_state.key == "needs_spec"


@pytest.mark.django_db
def test_import_board_resolves_self_referential_dependency():
    services.import_board(markdown=EXCERPT)
    first = models.Card.objects.get(title="First shipped thing")
    second = models.Card.objects.get(title="Second planned thing")
    # The "(`DONE-001-0.0.1`)" reference resolves to the first card by number.
    assert list(second.dependencies.all()) == [first]
    assert list(first.dependents.all()) == [second]


@pytest.mark.django_db
def test_import_board_parity_through_edge_carries_level():
    services.import_board(markdown=EXCERPT)
    second = models.Card.objects.get(title="Second planned thing")
    claim = second.parity_claims.get()
    assert claim.upstream.key == "strawberry_django"
    assert claim.level.key == "adjacent"


@pytest.mark.django_db
def test_uuid_signal_creates_side_row():
    services.import_board(markdown=EXCERPT)
    card = models.Card.objects.get(title="First shipped thing")
    # The post_save signal auto-created a UUIDModel side-row reachable via `.uuid`.
    assert isinstance(card.uuid.id, uuid_module.UUID)
    # Lookups carry one too (the signal is connected for every linked model).
    assert isinstance(models.Status.objects.get(key="done").uuid.id, uuid_module.UUID)
    # One UUID row per object created (2 cards + 5 items + lookups + versions).
    assert models.UUIDModel.objects.filter(card__isnull=False).count() == 2
    assert models.UUIDModel.objects.filter(carditem__isnull=False).count() == 5


@pytest.mark.django_db
def test_import_board_is_idempotent():
    services.import_board(markdown=EXCERPT)
    services.import_board(markdown=EXCERPT)
    assert models.Card.objects.count() == 2
    assert models.CardItem.objects.count() == 5
    # The (card, upstream) unique constraint keeps parity claims from duplicating.
    assert models.ParityClaim.objects.count() == 3
    # Dependency edges are cleared + re-added, not duplicated.
    second = models.Card.objects.get(title="Second planned thing")
    assert second.dependencies.count() == 1


@pytest.mark.django_db
def test_import_groups_items_by_section_in_order():
    services.import_board(markdown=EXCERPT)
    first = models.Card.objects.get(title="First shipped thing")
    scope_texts = list(
        first.items.filter(section__key="scope").order_by("order").values_list("text", flat=True),
    )
    assert scope_texts == ["alpha scope item", "beta scope item"]
    dod = first.items.filter(section__key="definition_of_done").get()
    assert dod.text == "did the thing"
    # A DONE card's checklist items are marked complete.
    assert dod.is_complete is True


@pytest.mark.django_db
def test_import_updates_in_place_by_title():
    services.import_board(markdown=EXCERPT)
    first = models.Card.objects.get(title="First shipped thing")
    original_pk = first.pk
    original_uuid = first.uuid.id

    # Re-import a variant where the first card's priority changed high -> low.
    modified = EXCERPT.replace("Priority: high", "Priority: low", 1)
    services.import_board(markdown=modified)

    reloaded = models.Card.objects.get(title="First shipped thing")
    assert models.Card.objects.count() == 2  # updated, not duplicated
    assert reloaded.pk == original_pk  # same row
    assert reloaded.priority.key == "low"  # field updated in place
    assert reloaded.uuid.id == original_uuid  # no new UUID side-row on update


def test_parse_size_variants():
    """``parse_cards`` handles a single size and an en-dash range (no DB)."""
    md = (
        "### TODO-ALPHA-010-0.0.9 — Single size card\n\n"
        "Relative size: XS\n\n"
        "### TODO-ALPHA-011-0.0.9 — Range size card\n\n"
        "Relative size: S–M\n"
    )
    cards = {c["title"]: c for c in services.parse_cards(md)}
    assert (cards["Single size card"]["size_low"], cards["Single size card"]["size_high"]) == (
        "xs",
        None,
    )
    assert (cards["Range size card"]["size_low"], cards["Range size card"]["size_high"]) == (
        "s",
        "m",
    )


@pytest.mark.django_db
def test_import_card_without_parity_has_no_claims():
    md = (
        "### TODO-ALPHA-012-0.0.9 — No parity card\n\n"
        "Priority: low\n\n"
        "Status: planned\n\n"
        "Relative size: S\n\n"
        "Scope:\n\n"
        "- something\n"
    )
    result = services.import_board(markdown=md)
    assert result["cards"] == 1
    assert result["parity_claims"] == 0
    card = models.Card.objects.get(title="No parity card")
    assert card.parity_claims.count() == 0
    assert list(card.parity.all()) == []


@pytest.mark.django_db
def test_import_real_board_end_to_end():
    """Import the actual repo-root ``KANBAN.md`` (loose, change-tolerant assertions).

    Also guards the NNN-collision fix: the board reuses NNN across DONE/TODO
    sequences, so cards are keyed by ``(status, number, version)`` -- the row
    count must therefore match the reported card count exactly.
    """
    result = services.import_board()  # default path -> repo-root KANBAN.md
    assert result["cards"] >= 40
    # One row per distinct card id, and one UUID side-row per card (signal fired).
    assert models.Card.objects.count() == result["cards"]
    assert models.UUIDModel.objects.filter(card__isnull=False).count() == result["cards"]

    # The shipped Filtering subsystem card is stable: done, XL, both upstreams.
    filtering = models.Card.objects.get(title="Filtering subsystem")
    assert filtering.status.key == "done"
    assert filtering.relative_size.key == "xl"
    assert set(filtering.parity_claims.values_list("upstream__key", flat=True)) == {
        "graphene_django",
        "strawberry_django",
    }
    # The board's real spec links are imported (H3), not left null.
    assert filtering.spec is not None
    assert filtering.spec.url.startswith("https://github.com/")


# ---------------------------------------------------------------------------
# Review follow-ups (docs/feedback.md)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_import_resolves_dependencies_by_full_id_not_just_number():
    """NNN is not unique across the board; dependencies resolve by full card id.

    Two cards share NNN ``046`` (a DONE-0.0.7 and a TODO-1.0.0). A dependency
    naming the TODO card by full id must link the TODO card -- not collide with
    or overwrite the DONE card.
    """
    md = (
        "### DONE-046-0.0.7 — Old shipped card\n\n"
        "Status: shipped\n\n"
        "Relative size: S\n\n"
        "### TODO-STABLE-046-1.0.0 — Future release card\n\n"
        "Status: planned\n\n"
        "Relative size: L\n\n"
        "### TODO-ALPHA-050-0.0.9 — Dependent card\n\n"
        "Status: planned\n\n"
        "Relative size: M\n\n"
        "Dependencies:\n\n"
        "- blocked on `TODO-STABLE-046-1.0.0`\n"
    )
    result = services.import_board(markdown=md)
    assert result["cards"] == 3  # the NNN-046 collision did not drop a card
    dependent = models.Card.objects.get(title="Dependent card")
    target = models.Card.objects.get(title="Future release card")
    assert list(dependent.dependencies.all()) == [target]
    # Resolved to the 1.0.0 card, not the same-NNN 0.0.7 card.
    assert dependent.dependencies.get().target_version.number == "1.0.0"


@pytest.mark.django_db
def test_reimport_preserves_item_uuids():
    """Re-import updates items in place, so their side-table UUIDs stay stable."""
    services.import_board(markdown=EXCERPT)
    first = models.Card.objects.get(title="First shipped thing")
    before = {(it.section_id, it.order): it.uuid.id for it in first.items.all()}
    assert before  # non-empty

    services.import_board(markdown=EXCERPT)
    after = {(it.section_id, it.order): it.uuid.id for it in first.items.all()}
    assert after == before


@pytest.mark.django_db
def test_reimport_removes_cards_absent_from_board():
    """A card dropped from the source board is removed on the next import (sync)."""
    services.import_board(markdown=EXCERPT)
    assert models.Card.objects.count() == 2

    only_first = EXCERPT.split("### TODO-ALPHA-002")[0]
    result = services.import_board(markdown=only_first)
    assert result["cards"] == 1
    assert models.Card.objects.count() == 1
    assert not models.Card.objects.filter(title="Second planned thing").exists()
    # The removed card's parity claim cascaded away too.
    assert models.ParityClaim.objects.filter(card__title="Second planned thing").count() == 0


@pytest.mark.django_db
def test_reimport_removes_stale_parity_claims_and_counts_the_graph():
    """A parity claim dropped from a card is removed; the count reports the graph."""
    services.import_board(markdown=EXCERPT)
    first = models.Card.objects.get(title="First shipped thing")
    assert first.parity_claims.count() == 2  # ⚛️ & 🍓

    reduced = EXCERPT.replace("Parity: ⚛️&🍓 required", "Parity: 🍓 required", 1)
    result = services.import_board(markdown=reduced)

    first.refresh_from_db()
    assert first.parity_claims.count() == 1
    assert first.parity_claims.get().upstream.key == "strawberry_django"
    # Return value reflects the resulting graph (1 + 1), not just newly-created rows.
    assert result["parity_claims"] == 2


SPEC_EXCERPT = (
    "### DONE-016-0.0.7 — Backtick spec card\n\n"
    "Status: shipped\n\n"
    "Relative size: M\n\n"
    "Spec: `docs/SPECS/spec-016-list_field-0_0_7.md`. Build plan: `docs/builder/build-016.md`.\n\n"
    "### DONE-021-0.0.8 — Reference spec card\n\n"
    "Status: shipped\n\n"
    "Relative size: XL\n\n"
    "Spec: [`docs/spec-021-filters-0_0_8.md`][spec-021]\n"
)


@pytest.mark.django_db
def test_import_parses_spec_lines_both_formats():
    """Both the bare-backtick and reference-style ``Spec:`` lines populate SpecDoc."""
    services.import_board(markdown=SPEC_EXCERPT)

    backtick = models.Card.objects.get(title="Backtick spec card")
    assert backtick.spec is not None
    assert backtick.spec.name == "spec-016-list_field-0_0_7"
    # First .md path on the line (the spec, not the build plan), as a GitHub URL.
    assert backtick.spec.url.endswith("/blob/main/docs/SPECS/spec-016-list_field-0_0_7.md")

    ref = models.Card.objects.get(title="Reference spec card")
    assert ref.spec.name == "spec-021-filters-0_0_8"
    assert ref.spec.url.endswith("/blob/main/docs/spec-021-filters-0_0_8.md")


@pytest.mark.django_db
def test_import_clears_spec_when_line_removed():
    """Removing the ``Spec:`` line clears the card's spec and reaps the orphan row."""
    services.import_board(markdown=SPEC_EXCERPT)
    without_spec = SPEC_EXCERPT.replace(
        "Spec: `docs/SPECS/spec-016-list_field-0_0_7.md`. Build plan: `docs/builder/build-016.md`.\n\n",
        "",
        1,
    )
    services.import_board(markdown=without_spec)

    backtick = models.Card.objects.get(title="Backtick spec card")
    assert backtick.spec is None
    assert not models.SpecDoc.objects.filter(name="spec-016-list_field-0_0_7").exists()


@pytest.mark.django_db
def test_import_maps_extended_priority_and_emphasized_severity():
    """Real board label shapes: critical / medium-high / low-medium + **emphasis**."""
    md = (
        "### TODO-ALPHA-060-0.0.9 — Critical card\n\n"
        "Priority: critical — release card\n\n"
        "Severity: **major**\n\n"
        "Relative size: M\n\n"
        "### TODO-ALPHA-061-0.0.9 — Medium-high card\n\n"
        "Priority: medium-high\n\n"
        "Severity: **medium**\n\n"
        "Relative size: S\n\n"
        "### TODO-ALPHA-062-0.0.9 — Low-medium card\n\n"
        "Priority: low-medium\n\n"
        "Relative size: S\n\n"
    )
    services.import_board(markdown=md)

    critical = models.Card.objects.get(title="Critical card")
    assert critical.priority.key == "critical"
    assert critical.severity.key == "major"  # stripped of ** emphasis
    assert models.Card.objects.get(title="Medium-high card").priority.key == "medium-high"
    assert models.Card.objects.get(title="Medium-high card").severity.key == "medium"
    assert models.Card.objects.get(title="Low-medium card").priority.key == "low-medium"
