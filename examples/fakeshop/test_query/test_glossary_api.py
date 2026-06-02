"""Live GraphQL HTTP tests for the glossary data app."""

import importlib
import sys

import pytest
from apps.glossary import models
from django.test import Client
from django.urls import clear_url_caches


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate imported DjangoType classes if package tests cleared the registry."""
    from django_strawberry_framework.registry import registry

    registry.clear()
    glossary_schema = sys.modules.get("apps.glossary.schema")
    if glossary_schema is None:
        importlib.import_module("apps.glossary.schema")
    else:
        importlib.reload(glossary_schema)

    project_schema = sys.modules.get("config.schema")
    if project_schema is None:
        importlib.import_module("config.schema")
    else:
        importlib.reload(project_schema)

    urls = sys.modules.get("config.urls")
    if urls is not None:
        importlib.reload(urls)
        clear_url_caches()


def _seed_glossary():
    shipped = models.GlossaryStatus.objects.create(key="shipped", label="Shipped", order=0)
    planned = models.GlossaryStatus.objects.create(key="planned", label="Planned", order=1)
    filtering = models.GlossaryCategory.objects.create(
        key="filtering",
        label="Filtering",
        order=0,
    )
    ordering = models.GlossaryCategory.objects.create(
        key="ordering",
        label="Ordering",
        order=1,
    )
    filterset = models.GlossaryTerm.objects.create(
        title="`FilterSet`",
        title_sort="filterset",
        anchor="filterset",
        status=shipped,
        status_text="shipped (`0.0.8`)",
        body="Declarative filtering sidecar.",
        entry_order=1,
        index_order=1,
    )
    orderset = models.GlossaryTerm.objects.create(
        title="`OrderSet`",
        title_sort="orderset",
        anchor="orderset",
        status=planned,
        status_text="planned for `0.0.8`",
        body="Declarative ordering sidecar.",
        entry_order=2,
        index_order=2,
    )
    kind = models.GlossaryTermLinkKind.objects.create(
        key="see-also",
        label="See also",
        order=0,
    )
    models.GlossaryCategoryMembership.objects.create(
        category=filtering,
        term=filterset,
        order=0,
    )
    models.GlossaryCategoryMembership.objects.create(
        category=ordering,
        term=orderset,
        order=0,
    )
    models.GlossaryTermLink.objects.create(
        source_term=orderset,
        target_term=filterset,
        kind=kind,
        raw_label="`FilterSet`",
        order=0,
    )
    models.GlossarySpecMention.objects.create(
        term=orderset,
        spec_path="docs/spec-028-orders-0_0_8.md",
        term_text="OrderSet",
        notes="Primary ordering sidecar.",
        order=0,
    )


def _post_graphql(query: str):
    return Client().post("/graphql/", data={"query": query}, content_type="application/json")


def _graphql_data(query: str):
    response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    return payload["data"]


@pytest.mark.django_db
def test_filter_glossary_terms_by_status_key():
    _seed_glossary()

    assert _graphql_data(
        """
        query {
          allGlossaryTerms(filter: { status: { key: { exact: "shipped" } } }) {
            title
            status { key }
          }
        }
        """,
    ) == {
        "allGlossaryTerms": [
            {
                "title": "`FilterSet`",
                "status": {"key": "shipped"},
            },
        ],
    }


@pytest.mark.django_db
def test_filter_glossary_terms_by_spec_mention_and_select_edges():
    _seed_glossary()

    assert _graphql_data(
        """
        query {
          allGlossaryTerms(
            filter: {
              specMentions: {
                specPath: { exact: "docs/spec-028-orders-0_0_8.md" }
              }
            }
          ) {
            title
            categories { label }
            outgoingLinks {
              rawLabel
              targetTerm { title }
            }
            specMentions {
              specName
              notes
            }
          }
        }
        """,
    ) == {
        "allGlossaryTerms": [
            {
                "title": "`OrderSet`",
                "categories": [{"label": "Ordering"}],
                "outgoingLinks": [
                    {
                        "rawLabel": "`FilterSet`",
                        "targetTerm": {"title": "`FilterSet`"},
                    },
                ],
                "specMentions": [
                    {
                        "specName": "spec-028-orders-0_0_8.md",
                        "notes": "Primary ordering sidecar.",
                    },
                ],
            },
        ],
    }
