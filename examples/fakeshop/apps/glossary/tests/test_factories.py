"""Tests for the glossary test-data factories."""

import pytest

from apps.glossary import factories, models


@pytest.mark.django_db
def test_lookup_factory_reuses_canonical_row():
    first = factories.make_glossary_status()
    second = factories.make_glossary_status()
    assert first.pk == second.pk
    assert models.GlossaryStatus.objects.count() == 1


@pytest.mark.django_db
def test_make_glossary_term_unique_identity_fields():
    one = factories.make_glossary_term()
    two = factories.make_glossary_term()
    assert one.pk is not None
    assert one.status_id is not None
    # title / title_sort / anchor are all unique-constrained.
    assert {one.title, two.title} != {one.title}
    assert one.anchor != two.anchor


@pytest.mark.django_db
def test_make_glossary_term_accepts_overrides():
    term = factories.make_glossary_term(title="`FilterSet`", anchor="filterset")
    assert term.title == "`FilterSet`"
    assert term.anchor == "filterset"


@pytest.mark.django_db
def test_make_alias_and_source_link_attach_to_term():
    term = factories.make_glossary_term()
    alias = factories.make_glossary_alias(term=term)
    assert alias.term_id == term.pk
    assert alias.normalized == alias.label.lower()
    link = factories.make_glossary_source_link(term=term)
    assert link.term_id == term.pk
    assert link.target


@pytest.mark.django_db
def test_make_term_link_orders_within_source_and_kind():
    source = factories.make_glossary_term()
    kind = factories.make_glossary_term_link_kind()
    first = factories.make_glossary_term_link(source_term=source, kind=kind)
    second = factories.make_glossary_term_link(source_term=source, kind=kind)
    assert (first.order, second.order) == (0, 1)
    assert first.target_term_id != source.pk


@pytest.mark.django_db
def test_make_category_membership_and_spec_mention():
    membership = factories.make_glossary_category_membership()
    assert membership.category_id is not None
    assert membership.term_id is not None
    mention = factories.make_glossary_spec_mention()
    assert mention.spec_path.endswith(".md")
    assert mention.term_id is not None
