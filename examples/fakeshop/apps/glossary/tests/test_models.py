import pytest

from apps.glossary import factories as gf


@pytest.mark.django_db
def test_glossary_term_edges_and_spec_name():
    term = gf.make_glossary_term(title="`FilterSet`", title_sort="filterset", anchor="filterset")
    category = gf.make_glossary_category("filtering")
    gf.make_glossary_alias(term=term, label="FilterSet", normalized="filterset")
    gf.make_glossary_category_membership(category=category, term=term)
    mention = gf.make_glossary_spec_mention(
        term=term,
        spec_path="docs/SPECS/spec-027-filters-0_0_8.md",
        term_text="FilterSet",
    )

    assert str(term) == "`FilterSet`"
    assert list(term.categories.values_list("key", flat=True)) == [category.key]
    assert list(term.aliases.values_list("normalized", flat=True)) == ["filterset"]
    assert mention.spec_name == "spec-027-filters-0_0_8.md"
