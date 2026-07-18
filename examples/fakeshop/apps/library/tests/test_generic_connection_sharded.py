"""Sharded (``FAKESHOP_SHARDED=1``) GenericRelation connection alias-late morph test.

Pins the P1 fix: the GenericRelation content-type predicate is resolved
alias-LATE by Django's ``GenericRelatedObjectManager.get_prefetch_querysets``
at fetch time (against the parent instances' database), NEVER baked as a
plan-time constant. The old planner resolved ``ContentType`` on the unrouted
child queryset (``.db`` -> ``default``) and embedded that pk; when the parents
live on ``shard_b`` and ``shard_b``'s ``Branch`` content-type pk DIFFERS from
``default``'s, the baked constant contradicted Django's own fetch-time morph
predicate and the connection silently returned zero rows.

This test deliberately forces the two aliases' ``Branch`` content-type pks
apart (manipulating the ``django_content_type`` rows in setup, per the finding),
seeds the branch and its tags on ``shard_b`` under ``shard_b``'s pk, and proves
the generic connection returns the correct rows on the non-default alias.

Sharded-only: gated by a module-level skip (``pytest.mark.skipif`` cannot be
used - the env var reshapes ``config.settings.DATABASES`` at import time, before
mark evaluation), mirroring
``examples/fakeshop/test_query/test_multi_db.py``. Library acceptance tests use
inline ``Model.objects.create`` (the library app has no ``services.py``).
"""

import os

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip(
        "requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)",
        allow_module_level=True,
    )

import strawberry
from django.contrib.contenttypes.models import ContentType
from strawberry import relay

from apps.library.models import Branch, TaggedItem
from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the global registry and connection-type cache around each test."""
    registry.clear()
    _connection_type_cache.clear()
    ContentType.objects.clear_cache()
    yield
    registry.clear()
    _connection_type_cache.clear()
    ContentType.objects.clear_cache()


def _build_schema():
    """Build a schema whose ``branches`` root reads from ``shard_b``."""

    class TaggedItemNode(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")
            interfaces = (relay.Node,)
            connection = {"total_count": True}

    class BranchNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name", "tags")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def branches(self) -> list[BranchNode]:
            return Branch.objects.using("shard_b").order_by("id")

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    return strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_generic_connection_uses_shard_b_content_type_pk_not_default():
    """The GFK connection over ``shard_b`` parents returns rows under ``shard_b``'s ct pk.

    The default-alias ``Branch`` content-type pk and the ``shard_b`` one are
    forced apart. A plan-time constant (the old bug) would bake the default pk
    and, contradicting Django's fetch-time ``shard_b`` morph predicate, return
    zero rows; the alias-late design resolves the ct against ``shard_b`` and the
    branch's own three tags come back.
    """
    # Resolve the default-alias Branch content-type pk (what the removed
    # plan-time lookup on the unrouted child queryset would have baked).
    default_branch_ct = ContentType.objects.db_manager("default").get_for_model(Branch)

    # Force ``shard_b``'s Branch content-type onto a DIFFERENT pk. Migrations
    # (post_migrate) pre-create a ``library.branch`` row on each alias with a
    # matching pk, so delete it and recreate at an explicit, distinct pk. The
    # FK cascade only touches TaggedItems, which are seeded afterwards.
    shard_branch_ct_pk = default_branch_ct.pk + 500
    ContentType.objects.using("shard_b").filter(
        app_label="library",
        model="branch",
    ).delete()
    ContentType.objects.using("shard_b").create(
        pk=shard_branch_ct_pk,
        app_label="library",
        model="branch",
    )
    ContentType.objects.clear_cache()
    assert shard_branch_ct_pk != default_branch_ct.pk

    # Seed the branch and its tags on ``shard_b`` under ``shard_b``'s ct pk.
    branch = Branch.objects.using("shard_b").create(name="Central")
    for tag in ("a1", "a2", "a3"):
        TaggedItem.objects.using("shard_b").create(
            content_type_id=shard_branch_ct_pk,
            object_id=branch.pk,
            tag=tag,
        )

    schema = _build_schema()
    result = schema.execute_sync(
        """
        query {
          branches {
            tagsConnection(first: 2) {
              totalCount
              edges { node { tag } }
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )

    assert result.errors is None, result.errors
    conn = result.data["branches"][0]["tagsConnection"]
    # Non-empty rows prove the fetch used ``shard_b``'s ct pk, not the baked
    # default pk (which would have matched zero rows on ``shard_b``).
    assert [edge["node"]["tag"] for edge in conn["edges"]] == ["a1", "a2"]
    assert conn["totalCount"] == 3
    assert conn["pageInfo"]["hasNextPage"] is True
