"""Model-level invariants for the kanban app (not reachable from a live query).

Covers the ``UUIDModel`` one-hot check constraint (docs/feedback.md M1): exactly
one of its O2O link fields must be non-null.
"""

import uuid as uuid_module

import pytest
from django.db import IntegrityError, transaction

from apps.kanban import models


@pytest.mark.django_db
def test_uuidmodel_accepts_exactly_one_link():
    """The normal path: creating a linked model yields a valid one-hot UUID row."""
    status = models.Status.objects.create(key="z", label="Z")
    row = status.uuid
    assert isinstance(row.id, uuid_module.UUID)
    set_links = [name for name in models._UUID_LINK_NAMES if getattr(row, f"{name}_id") is not None]
    assert set_links == ["status"]


@pytest.mark.django_db
def test_uuidmodel_rejects_zero_links():
    """A registry row with no link violates the one-hot constraint."""
    with pytest.raises(IntegrityError), transaction.atomic():
        models.UUIDModel.objects.create()


@pytest.mark.django_db
def test_uuidmodel_rejects_multiple_links():
    """A registry row linked to two domain rows violates the one-hot constraint."""
    status = models.Status.objects.create(key="x", label="X")
    label = models.Label.objects.create(key="y")
    # Free the O2O slots the signal auto-filled so the failure below is the
    # one-hot check (two non-null links), not O2O uniqueness.
    models.UUIDModel.objects.filter(status=status).delete()
    models.UUIDModel.objects.filter(label=label).delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        models.UUIDModel.objects.create(status=status, label=label)
