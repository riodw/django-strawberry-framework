import pytest

from apps.glossary import models


@pytest.mark.django_db
def test_glossary_term_edges_and_spec_name():
    status = models.GlossaryStatus.objects.create(
        key="shipped",
        label="Shipped",
        order=0,
    )
    category = models.GlossaryCategory.objects.create(
        key="filtering",
        label="Filtering",
        order=0,
    )
    term = models.GlossaryTerm.objects.create(
        title="`FilterSet`",
        title_sort="filterset",
        anchor="filterset",
        status=status,
        status_text="shipped (`0.0.8`)",
        body="Declarative filtering sidecar.",
        entry_order=1,
        index_order=1,
    )
    models.GlossaryAlias.objects.create(
        term=term,
        label="FilterSet",
        normalized="filterset",
    )
    models.GlossaryCategoryMembership.objects.create(
        category=category,
        term=term,
        order=0,
    )
    mention = models.GlossarySpecMention.objects.create(
        term=term,
        spec_path="docs/SPECS/spec-027-filters-0_0_8.md",
        term_text="FilterSet",
        order=0,
    )

    assert str(term) == "`FilterSet`"
    assert list(term.categories.values_list("key", flat=True)) == ["filtering"]
    assert list(term.aliases.values_list("normalized", flat=True)) == ["filterset"]
    assert mention.spec_name == "spec-027-filters-0_0_8.md"
