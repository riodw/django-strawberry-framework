"""Tests for the UUID side-table wiring and its one-hot link constraint.

Covers three surfaces that the signals/services suites do not:

* :func:`apps.kanban.constraints.OneHotLinkCount` -- the custom expression that
  keeps the ``UUIDModel`` check constraint flat in migrations: its
  ``deconstruct()`` shape and the zero-field ``ValueError`` guard.
* The DB-level one-hot invariant -- a ``UUIDModel`` row with zero links and one
  with two links both violate ``kanban_uuidmodel_exactly_one_link``.
* ``create_uuid_row`` -- every ``UUID_LINKED_MODELS`` member gets a side-row on
  first ``.objects.create()`` (parametrized over the whole registry), plus the
  ``m2m_changed`` path for ``CardPathLink`` rows added via ``.add()``.
"""

import pytest
from django.db import IntegrityError, transaction

from apps.kanban import factories as kf
from apps.kanban import models
from apps.kanban.constraints import OneHotLinkCount
from apps.kanban.signals import UUID_LINKED_MODELS

# ---------------------------------------------------------------------------
# OneHotLinkCount unit surface (no DB)
# ---------------------------------------------------------------------------


def test_one_hot_link_count_deconstruct_is_flat():
    """``deconstruct()`` returns the flat field-name list, not the nested Case tower."""
    expression = OneHotLinkCount("milestone", "status", "priority")

    path, args, kwargs = expression.deconstruct()

    assert path == "apps.kanban.constraints.OneHotLinkCount"
    assert args == ("milestone", "status", "priority")
    assert kwargs == {}


def test_one_hot_link_count_requires_at_least_one_field():
    with pytest.raises(ValueError, match="at least one field name"):
        OneHotLinkCount()


# ---------------------------------------------------------------------------
# DB-level one-hot invariant
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_uuid_row_with_zero_links_violates_constraint():
    with pytest.raises(IntegrityError), transaction.atomic():
        models.UUIDModel.objects.create()


@pytest.mark.django_db
def test_uuid_row_with_two_links_violates_constraint():
    milestone = kf.make_milestone("alpha")
    status = kf.make_status("todo")
    # Each domain row already owns an auto-created side-row (create_uuid_row).
    # Drop them so the two-link row below trips the one-hot check rather than the
    # per-field O2O uniqueness.
    milestone.uuid.delete()
    status.uuid.delete()

    with pytest.raises(IntegrityError), transaction.atomic():
        models.UUIDModel.objects.create(milestone=milestone, status=status)


# ---------------------------------------------------------------------------
# create_uuid_row: a side-row per linked model on create
# ---------------------------------------------------------------------------


def _make_instance(model):
    """Create one saved instance of ``model`` via the kanban factories."""
    builders = {
        models.Milestone: lambda: kf.make_milestone(f"ms-{kf._seq()}"),
        models.Status: lambda: kf.make_status(f"st-{kf._seq()}"),
        models.Priority: lambda: kf.make_priority(f"pr-{kf._seq()}"),
        models.RelativeSize: lambda: kf.make_relative_size(f"rs-{kf._seq()}"),
        models.Upstream: lambda: kf.make_upstream(f"up-{kf._seq()}"),
        models.ParityLevel: lambda: kf.make_parity_level(f"pl-{kf._seq()}"),
        models.Section: lambda: kf.make_section(f"se-{kf._seq()}"),
        models.CardReferenceKind: lambda: kf.make_card_reference_kind(f"rk-{kf._seq()}"),
        models.BoardDocKind: lambda: kf.make_board_doc_kind(f"bk-{kf._seq()}"),
        models.AttemptOutcome: lambda: kf.make_attempt_outcome(f"ao-{kf._seq()}"),
        models.VerificationKind: lambda: kf.make_verification_kind(f"vk-{kf._seq()}"),
        models.Actor: lambda: kf.make_actor(f"ac-{kf._seq()}"),
        models.TargetVersion: kf.make_target_version,
        models.SpecDoc: kf.make_spec_doc,
        models.TrackedPath: kf.make_tracked_path,
        models.Card: kf.make_card,
        models.CardReference: kf.make_card_reference,
        models.CardGlossaryTerm: kf.make_card_glossary_term,
        models.ParityClaim: kf.make_parity_claim,
        models.CardPathLink: kf.make_card_path_link,
        models.CardItem: kf.make_card_item,
        models.Label: kf.make_label,
        models.BoardDoc: kf.make_board_doc,
        models.BoardDocCardReference: kf.make_board_doc_card_reference,
        models.CardTransition: kf.make_card_transition,
        models.WorkAttempt: kf.make_work_attempt,
        models.Decision: kf.make_decision,
    }
    return builders[model]()


@pytest.mark.django_db
@pytest.mark.parametrize("model", UUID_LINKED_MODELS, ids=lambda m: m._meta.model_name)
def test_create_uuid_row_materializes_side_row_for_every_linked_model(model):
    instance = _make_instance(model)

    side_row = instance.uuid
    assert side_row is not None
    assert side_row.id is not None
    # The one non-null link on the side-row points back at this instance.
    assert getattr(side_row, model._meta.model_name) == instance


@pytest.mark.django_db
def test_cardpathlink_m2m_add_creates_uuid_side_row():
    """A raw M2M ``.add()`` inserts the through row via bulk_create (no post_save),

    so the ``m2m_changed`` receiver -- not ``create_uuid_row`` -- backfills the
    ``CardPathLink`` side-row.
    """
    card = kf.make_card()
    path = kf.make_tracked_path("django_strawberry_framework/types/base.py")

    card.changed_files.add(path, through_defaults={"kind": models.CARD_PATH_LINK_CHANGED})

    link = models.CardPathLink.objects.get(card=card, path=path)
    assert link.uuid is not None
    assert link.uuid.id is not None
