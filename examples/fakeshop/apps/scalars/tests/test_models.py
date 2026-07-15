"""Scalars model tests for string rendering, relation traversal, and tag-label uniqueness.

Mirrors the other apps' model tests: __str__ rendering (including the nullable
fallback), self-referential + FK relation traversal, and a uniqueness rule.
"""

import datetime
import uuid

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.scalars.models import NullableScalarSpecimen, ScalarSpecimen, ScalarSpecimenTag


@pytest.mark.django_db
def test_str_representations_and_relations():
    tag = ScalarSpecimenTag.objects.create(label="alpha")
    parent = ScalarSpecimen.objects.create(
        label="root",
        occurred_on=datetime.date(2024, 1, 1),
        occurred_at=timezone.now(),
        occurred_time=datetime.time(12, 0),
        external_id=uuid.uuid4(),
        tag=tag,
    )
    child = ScalarSpecimen.objects.create(
        label="leaf",
        occurred_on=datetime.date(2024, 1, 2),
        occurred_at=timezone.now(),
        occurred_time=datetime.time(13, 0),
        external_id=uuid.uuid4(),
        parent=parent,
    )
    labelled = NullableScalarSpecimen.objects.create(label="n1", partner=parent)
    blank = NullableScalarSpecimen.objects.create()

    assert str(tag) == "alpha"
    assert str(parent) == "root"
    assert str(labelled) == "n1"
    assert str(blank) == f"NullableScalarSpecimen#{blank.pk}"

    # Self-referential FK, lookup FK, and the nullable cross-FK all traverse.
    assert list(parent.children.all()) == [child]
    assert list(tag.tagged_specimens.all()) == [parent]
    assert list(parent.nullable_partners.all()) == [labelled]


@pytest.mark.django_db
def test_tag_label_unique():
    ScalarSpecimenTag.objects.create(label="dup")
    with pytest.raises(IntegrityError), transaction.atomic():
        ScalarSpecimenTag.objects.create(label="dup")
