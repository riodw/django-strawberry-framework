"""In-process windowed GenericRelation connection acceptance tests (WS-B).

``Branch.tags = GenericRelation(TaggedItem)`` is the package's generic-relation
substrate; the public example schema deliberately does NOT expose it (a model
comment forbids exposing tags), so these tests build test-local Relay-Node
``BranchNode`` / ``TaggedItemNode`` types and drive them through
``schema.execute_sync`` with the optimizer extension - never over live
``/graphql`` (there is nothing to hit there). They pin the first-class
``"generic"`` relation kind: the alias-late content-type morph predicate
(Django's ``GenericRelatedObjectManager.get_prefetch_querysets`` adds it at
fetch time INSIDE the window subquery - the planner never injects it), the
scalar-only projection that includes both the ``object_id`` and
``content_type_id`` columns (the deferred-refetch N+1 fix), the count-free
``hasNextPage`` probe composition with WS-A, and the lateral strategy degrading
to the windowed body.

Library acceptance tests use inline ``Model.objects.create`` (the library app
has no ``services.py``), per AGENTS.md. Every generic ``DjangoType`` is declared
inside the schema factory so the autouse registry/connection-cache reset keeps
each test independent.
"""

import os
import traceback

import pytest
import strawberry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import SynchronousOnlyOperation
from django.db import connection as db_connection
from django.test.utils import CaptureQueriesContext
from strawberry import relay

from apps.library.models import Branch, Genre, ProxyBranch, TaggedItem
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
    """Reset the global registry and connection-type cache around each test.

    Every test declares fresh function-scope ``DjangoType`` classes; connection
    classes are cached on ``target_type`` identity, so a discarded class must
    not leak into a later test's identity check.
    """
    registry.clear()
    _connection_type_cache.clear()
    yield
    registry.clear()
    _connection_type_cache.clear()


def _build_schema(*, strategy=None, total_count=False):
    """Build a schema exposing ``branches`` with a windowed ``tagsConnection``.

    ``strategy`` selects the nested-connection strategy
    (``None`` -> windowed default, ``"lateral"`` -> auto/lateral). ``total_count``
    opts the target connection into a ``totalCount`` field.
    """
    if total_count:

        class TaggedItemNode(DjangoType):
            class Meta:
                model = TaggedItem
                fields = ("id", "tag")
                interfaces = (relay.Node,)
                connection = {"total_count": True}
    else:

        class TaggedItemNode(DjangoType):
            class Meta:
                model = TaggedItem
                fields = ("id", "tag")
                interfaces = (relay.Node,)

    class BranchNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name", "tags")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def branches(self) -> list[BranchNode]:
            return Branch.objects.order_by("id")

    finalize_django_types()
    ext = DjangoOptimizerExtension(nested_connection_strategy=strategy)
    return strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


def _window_sql(captured_queries):
    """Return the windowed child SQL (the ``ROW_NUMBER`` prefetch), asserting it ran.

    Its presence proves the generic connection took the WINDOWED path rather
    than degrading to a per-parent fallback.
    """
    for query in captured_queries:
        if "ROW_NUMBER" in query["sql"].upper():
            return query["sql"]
    raise AssertionError("no windowed (ROW_NUMBER) child query was captured")


@pytest.mark.django_db
def test_windowed_generic_connection_first_page_excludes_poison_row():
    """first:N page + cursors + totalCount are correct with a poison row present.

    The poison ``TaggedItem`` shares ``object_id`` with the branch but carries a
    DIFFERENT content type, so it lands in the same ``object_id`` partition. The
    alias-late content-type WHERE Django's generic prefetch adds at fetch time
    (inside the window subquery) excludes it - the recon's wrong-data scare,
    pinned forever.
    """
    branch = Branch.objects.create(name="Central")
    other = Branch.objects.create(name="Annex")
    for tag in ("a1", "a2", "a3"):
        TaggedItem.objects.create(content_object=branch, tag=tag)
    TaggedItem.objects.create(content_object=other, tag="b1")
    # Poison: same object_id as ``branch`` but a Genre content type.
    genre_ct = ContentType.objects.get_for_model(Genre)
    TaggedItem.objects.create(content_type=genre_ct, object_id=branch.pk, tag="poison")

    schema = _build_schema(total_count=True)
    result = schema.execute_sync(
        """
        query {
          branches {
            tagsConnection(first: 2) {
              totalCount
              edges { cursor node { tag } }
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )

    assert result.errors is None, result.errors
    central = result.data["branches"][0]
    conn = central["tagsConnection"]
    assert [edge["node"]["tag"] for edge in conn["edges"]] == ["a1", "a2"]
    assert all(edge["cursor"] for edge in conn["edges"])
    # totalCount counts only the branch's own three tags - the poison row and
    # the other branch's tag are excluded by the morph WHERE / object_id partition.
    assert conn["totalCount"] == 3
    assert conn["pageInfo"]["hasNextPage"] is True


@pytest.mark.django_db
def test_generic_connection_has_next_page_probe_composes_with_ws_a():
    """A hasNextPage-only generic page takes the count-free probe (WS-A composition).

    No ``totalCount`` selected on a bounded first page -> the window overfetches
    a sentinel row instead of paying a ``Count(1) OVER`` scan; the sentinel's
    presence answers ``hasNextPage``.
    """
    branch = Branch.objects.create(name="Central")
    for index in range(3):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")

    schema = _build_schema()

    with CaptureQueriesContext(db_connection) as ctx:
        result = schema.execute_sync(
            "{ branches { tagsConnection(first: 2) {"
            " edges { node { tag } } pageInfo { hasNextPage } } } }",
        )
    assert result.errors is None, result.errors
    conn = result.data["branches"][0]["tagsConnection"]
    assert [edge["node"]["tag"] for edge in conn["edges"]] == ["t0", "t1"]
    assert conn["pageInfo"]["hasNextPage"] is True
    # Windowed path taken, and count-free: the probe replaces the partition count.
    window_sql = _window_sql(ctx.captured_queries)
    assert "COUNT(" not in window_sql.upper()

    # Boundary: the page ending exactly at the partition tail -> hasNextPage False.
    exact = schema.execute_sync(
        "{ branches { tagsConnection(first: 3) { pageInfo { hasNextPage } } } }",
    )
    assert exact.errors is None, exact.errors
    assert exact.data["branches"][0]["tagsConnection"]["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_scalar_only_generic_connection_has_no_per_row_refetch():
    """A pageInfo-only generic window loads object_id + content_type_id, so no N+1.

    The projection includes BOTH the ``object_id`` connector and the
    ``content_type_id`` that Django's generic-prefetch attach reads off each
    child (its attach key is ``(object_id, content_type_id)``), so a scalar-only
    window never deferred-refetches either column once per row - the WS-B N+1
    fix. The query count must not scale with the number of tags.
    """
    schema = _build_schema()
    query = "{ branches { tagsConnection { pageInfo { hasNextPage } } } }"

    branch = Branch.objects.create(name="Central")
    for index in range(2):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")
    with CaptureQueriesContext(db_connection) as small:
        assert schema.execute_sync(query).errors is None

    for index in range(2, 8):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")
    with CaptureQueriesContext(db_connection) as large:
        assert schema.execute_sync(query).errors is None

    # No per-row deferred refetch: adding six tags does not add six queries.
    assert len(large.captured_queries) == len(small.captured_queries)
    # The scalar-only window explicitly loads both morph columns.
    window_sql = _window_sql(large.captured_queries).lower()
    assert "object_id" in window_sql
    assert "content_type_id" in window_sql


@pytest.mark.django_db
def test_lateral_strategy_generic_connection_degrades_to_windowed():
    """A generic connection under the lateral strategy degrades to the windowed body.

    ``parent_link_field`` is ``None`` for the generic join, so the lateral
    backend refuses at ``_build_lateral_spec`` and the auto strategy runs the
    already-windowed ORM query - no error, correct rows.
    """
    branch = Branch.objects.create(name="Central")
    for index in range(3):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")

    schema = _build_schema(strategy="lateral")
    result = schema.execute_sync(
        "{ branches { tagsConnection(first: 2) { edges { node { tag } } } } }",
    )

    assert result.errors is None, result.errors
    conn = result.data["branches"][0]["tagsConnection"]
    assert [edge["node"]["tag"] for edge in conn["edges"]] == ["t0", "t1"]


_OPTIMIZER_PATH_MARKER = os.sep + "optimizer" + os.sep


def _sync_only_optimizer_frames(error):
    """Return ``(original_error, optimizer_frame_filenames)`` for a GraphQL error.

    The GraphQL layer wraps the raised exception; ``original_error`` is the real
    ``SynchronousOnlyOperation``. Its traceback filenames tell WHERE the sync
    boundary was crossed - any frame under ``.../optimizer/...`` means the
    optimizer's plan build (not Django's own row fetch) performed the ORM work.
    """
    original = getattr(error, "original_error", None) or error
    frames = traceback.extract_tb(original.__traceback__)
    optimizer_frames = [f.filename for f in frames if _OPTIMIZER_PATH_MARKER in f.filename]
    return original, optimizer_frames


@pytest.mark.django_db
async def test_generic_connection_planning_does_no_sync_orm_work_under_async():
    """Async ``schema.execute`` of a generic connection plans without touching the DB.

    Runs the optimizer through the REAL async GraphQL execution path
    (``await schema.execute``) on the event-loop thread with a cold
    ``ContentType`` cache. Planning of the generic ``tagsConnection`` happens
    inside ``DjangoOptimizerExtension._optimize`` on that loop thread; the
    alias-late design resolves the content-type morph predicate at fetch time
    (Django's ``GenericRelatedObjectManager``), so planning performs ZERO
    synchronous ORM work and never raises ``SynchronousOnlyOperation``.

    A full async ``/graphql`` cannot complete here without
    ``DJANGO_ALLOW_ASYNC_UNSAFE``: iterating the parent ``branches`` list on the
    loop thread is normal Django async behavior that raises
    ``SynchronousOnlyOperation`` at row-fetch time, and that flag would ALSO mask
    the very plan-time DB lookup under test. So the assertion stays at the level
    that genuinely protects the boundary: the expected async-boundary error must
    originate from Django's own queryset fetch (``QuerySet._fetch_all`` ->
    ``execute_sql``), NOT from any optimizer plan-build frame. If the removed
    plan-time ``ContentType`` lookup were reintroduced, the
    ``SynchronousOnlyOperation`` would instead be raised from inside the walker /
    ``nested_planner`` on the loop thread and its traceback would carry an
    ``.../optimizer/...`` frame - which this test forbids. The package-tier
    sibling ``tests/optimizer/test_walker.py::``
    ``test_generic_connection_planning_does_no_sync_db_io_under_async`` drives the
    planner directly; this is its live acceptance twin.
    """
    schema = _build_schema()
    # Cold cache: a plan-time ``ContentType.objects.get_for_model`` would have to
    # hit the DB (sync I/O) during the loop-thread plan build.
    ContentType.objects.clear_cache()

    result = await schema.execute(
        "{ branches { tagsConnection(first: 2) { edges { node { tag } } } } }",
    )

    # The only permitted sync-boundary crossing is Django's parent-row fetch,
    # which raises ``SynchronousOnlyOperation`` at the top-level ``branches``
    # field (expected flag-free async behavior, not our bug).
    assert result.errors, "expected the async-boundary error from the parent-row fetch"
    assert result.errors[0].path == ["branches"]
    original, optimizer_frames = _sync_only_optimizer_frames(result.errors[0])
    assert isinstance(original, SynchronousOnlyOperation), original
    # Planning did no synchronous ORM work: the boundary crossing carries no
    # optimizer plan-build frame. This is the assertion that bites if the
    # plan-time content-type lookup returns.
    assert optimizer_frames == [], optimizer_frames


def _build_proxy_schema():
    """Build a schema exposing ``proxyBranches`` with a ``proxyTagsConnection``.

    ``ProxyBranch`` is a proxy of ``Branch`` whose ``proxy_tags`` generic
    relation is declared with ``for_concrete_model=False``, so the reverse tag
    manager filters ``TaggedItem`` rows by the PROXY content type rather than
    ``Branch``'s concrete content type.
    """

    class TaggedItemNode(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")
            interfaces = (relay.Node,)
            connection = {"total_count": True}

    class ProxyBranchNode(DjangoType):
        class Meta:
            model = ProxyBranch
            fields = ("id", "name", "proxy_tags")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def proxy_branches(self) -> list[ProxyBranchNode]:
            return ProxyBranch.objects.order_by("id")

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    return strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


@pytest.mark.django_db
def test_generic_connection_honors_non_default_for_concrete_model():
    """A ``for_concrete_model=False`` generic connection morphs to the PROXY content type.

    ``ProxyBranch.proxy_tags`` is declared ``for_concrete_model=False``, so its
    alias-late morph predicate must select the ``ProxyBranch`` content type, not
    ``Branch``'s concrete content type. The two content types are forced apart by
    construction (a proxy model gets its own ``django_content_type`` row). The
    branch's real tags are seeded under the PROXY content type; a decoy tag is
    seeded under the CONCRETE ``Branch`` content type with the SAME
    ``object_id``.

    The connection must return only the proxy-content-type rows and exclude the
    decoy. If a future change discarded the ``GenericRelation`` field's
    ``for_concrete_model`` semantics - or re-baked a concrete-default
    content-type constant at plan time - the connection would instead return the
    concrete decoy (or empty), and these assertions bite.
    """
    proxy_ct = ContentType.objects.get_for_model(ProxyBranch, for_concrete_model=False)
    concrete_ct = ContentType.objects.get_for_model(Branch)
    # A proxy model carries its own content type, distinct from the concrete
    # parent's - the whole point of ``for_concrete_model=False``.
    assert proxy_ct.pk != concrete_ct.pk

    branch = Branch.objects.create(name="Central")
    for tag in ("p1", "p2", "p3"):
        TaggedItem.objects.create(content_type=proxy_ct, object_id=branch.pk, tag=tag)
    # Decoy: same ``object_id`` but the CONCRETE ``Branch`` content type. A plan
    # that discarded ``for_concrete_model=False`` would return THIS row.
    TaggedItem.objects.create(content_type=concrete_ct, object_id=branch.pk, tag="decoy")

    schema = _build_proxy_schema()
    result = schema.execute_sync(
        """
        query {
          proxyBranches {
            proxyTagsConnection(first: 2) {
              totalCount
              edges { node { tag } }
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )

    assert result.errors is None, result.errors
    conn = result.data["proxyBranches"][0]["proxyTagsConnection"]
    # Only the proxy-content-type rows come back; the concrete decoy is excluded.
    assert [edge["node"]["tag"] for edge in conn["edges"]] == ["p1", "p2"]
    assert conn["totalCount"] == 3
    assert conn["pageInfo"]["hasNextPage"] is True
