"""Live GraphQL HTTP tests for ``DjangoDebugExtension`` (spec-044 Test plan 1-7).

The request-visible half of the debug extension's coverage: every case posts a
real operation over HTTP to a debug-enabled probe schema mounted on this
module's URLconf (the ``test_multi_db.py`` holder plumbing precedent,
deliberately copied - not promoted - per spec-044 DRY D3), built over the
freshly-reloaded fakeshop apps, seeded through ``seed_data`` /
``create_users``, and posted through the package ``TestClient``.

Covered live here: happy-path SQL capture through the forced debug cursor, the
optimizer composition (the visibility-safe two-query prefetch shape as the
payload's demonstration surface), mutation capture, the resolver-exception row,
the validation-versus-execution boundary, the no-SQL operation's two empty
lists, the off-by-default posture, the fail-closed ``settings.DEBUG`` gate in
both directions (spec-048 Decision 5: a bare class entry withholds and warns,
the acknowledgement factory publishes), and the payload caps' end-to-end wiring
(spec-048 Decision 6). Fakeshop's shipped aggregate schema deliberately does
NOT enable the extension - asserted here against the project's real
``/graphql/`` - and the probe URLconf is the established way to exercise an
opt-in schema shape without changing every acceptance response.

Because the suite runs with ``settings.DEBUG`` false - now the extension's
fail-closed condition - every payload-expecting scenario here spells the
acknowledgement factory ``_acknowledged_debug`` rather than flipping the
setting. Flipping it is not available at this tier: fakeshop mounts the
package's debug-toolbar middleware behind ``DEBUG``, and the toolbar's
``djdt`` URL namespace lives on the project URLconf that the probe holder
replaces, so a ``DEBUG=True`` live request would fail on infrastructure
unrelated to the payload. The bare CLASS entry's own semantics (a
zero-argument construction defaulting to the safe answer, and per-operation
freshness) are pinned in ``tests/extensions/test_debug.py`` under
``override_settings(DEBUG=True)``; what this tier owns of the bare entry is its
REFUSAL, which is exactly what a ``DEBUG``-false request shows.

Serializer/coordinator, merge-precedence, async-overlap, masking-order, and
nested-reentrancy mechanics belong in ``tests/extensions/test_debug.py``.
"""

import logging

import pytest
import strawberry
from apps.products.models import Category, Item
from apps.products.services import create_users, seed_data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.test.utils import override_settings
from django.urls import path
from strawberry import relay
from strawberry.django.views import GraphQLView

from django_strawberry_framework import DjangoOptimizerExtension, DjangoSchema
from django_strawberry_framework.extensions import DjangoDebugExtension
from django_strawberry_framework.testing import TestClient

# One module-level URLconf activation covering every request-driving scenario
# (spec-044 DRY D3) - never per-test override_settings/clear_url_caches blocks.
pytestmark = pytest.mark.urls(__name__)

# ---------------------------------------------------------------------------
# Holder-pattern URLconf: ONE mutable schema holder, ONE view, ONE
# urlpatterns entry. Fixtures swap the held schema per scenario (debug-only,
# optimizer + debug, no-debug) rather than duplicating the plumbing.
# ---------------------------------------------------------------------------

_current: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    """Closure-bound view that reads ``_current['schema']`` per request."""
    schema = _current["schema"]
    assert schema is not None, "install_probe_schema must run before any /graphql/ request"
    return GraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view)]

# The one module-local optimizer singleton, exposed as ``lambda: _optimizer``
# beside the debug factory - the canonical consumer shape (the shipped
# ``config/schema.py`` wiring): both entries are callables, and the two
# deliberately different lifetimes live in what they RETURN (a shared cached
# optimizer every time, a fresh uncached debug instance per operation).
_optimizer = DjangoOptimizerExtension()

# The live mutation wire contract (the ``test_products_api.py`` shape).
_CREATE_ITEM = (
    "mutation($d: ItemInput!) { createItem(data: $d) { "
    "node { name category { name } } errors { field messages } } }"
)

# spec-048 Decision 6's caps re-spelled as INDEPENDENT literals - never the
# production constants re-imported, so a silently widened cap fails this tier.
_EXCEPTION_MESSAGE_CAP = 4096
_TRUNCATION_MARKER = "... [truncated]"


def _acknowledged_debug():
    """The documented acknowledgement spelling (spec-048 Decision 5), as ONE named factory.

    Written as a factory, never a pre-built instance: the engine builds it once
    per operation, so the fresh-per-operation contract every scenario below
    relies on is unchanged from the bare class entry. A named function rather
    than a repeated lambda so the extensions lists stay readable - it is still
    a factory entry, not an instance entry.
    """
    return DjangoDebugExtension(allow_unsafe_production=True)


@pytest.fixture
def install_probe_schema(_reload_project_schema_for_acceptance_tests):
    """Return an installer that mounts a probe schema over the reloaded products types.

    Imported INSIDE the fixture body (never at module top) so the classes are
    the freshly-reloaded ones; the returned installer takes the ``extensions=``
    list verbatim and never sorts, normalizes, or deduplicates it - order is a
    tested contract. The probe ``Query`` adds the three execution-error fields a
    shipped products field cannot provide (a resolver raise, a non-null
    completion error, and an over-cap exception message).
    """
    from apps.products.schema import Mutation as ProductsMutation
    from apps.products.schema import Query as ProductsQuery

    from django_strawberry_framework import finalize_django_types, strawberry_config

    @strawberry.type
    class Query(ProductsQuery):
        @strawberry.field
        def boom(self) -> int:
            return 1 / 0  # ZeroDivisionError("division by zero")

        @strawberry.field
        def broken_non_null(self) -> int:
            return None  # a completion error: null for a non-nullable field

        @strawberry.field
        def huge_boom(self) -> int:
            # An exception message comfortably past the per-row character cap,
            # so a real operation proves the caps are wired into the payload.
            raise ValueError("x" * (_EXCEPTION_MESSAGE_CAP * 2))

    @strawberry.type
    class Mutation(ProductsMutation):
        """The products write surface, unchanged."""

    def _install(extensions):
        finalize_django_types()
        # DjangoSchema: the probe mounts the generated products write surface,
        # whose pipeline requires the completion-spanning transaction
        # (mutation atomicity, shipped 0.0.14).
        _current["schema"] = DjangoSchema(
            query=Query,
            mutation=Mutation,
            config=strawberry_config(),
            extensions=extensions,
        )

    yield _install
    _current["schema"] = None


def _debug(response):
    """Validate-and-return the debug payload for executed-operation happy paths.

    Never used by the absence scenarios (5's unknown-field half, 7, 8's
    withheld-payload half and 10) - those assert the missing key explicitly.
    """
    extensions = response.extensions or {}
    assert "debug" in extensions, extensions
    payload = extensions["debug"]
    assert set(payload) == {"sql", "exceptions"}  # both keys always present
    return payload


# ---------------------------------------------------------------------------
# Scenario 1 - happy-path SQL capture: the forced debug cursor is the capture
# MECHANISM, while settings.DEBUG (plus the acknowledgement) is the GATE.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_query_capture_uses_the_forced_debug_cursor_not_debug_query_logging(install_probe_schema):
    """The bracket - not Django's ``DEBUG`` query logging - produces the captured rows.

    Run deliberately under ``settings.DEBUG`` false, through the
    acknowledgement factory ``_acknowledged_debug``: Django logs no queries of its own in that posture, so every row in the
    payload was produced by the extension's own ``force_debug_cursor`` bracket.

    The mechanism's DEBUG-independence is NOT the extension's gate. Since
    spec-048 Decision 5 the extension fails closed under ``settings.DEBUG``
    false unless the deployment acknowledges the disclosure - which is exactly
    why this scenario has to spell the acknowledgement to see a payload at all.
    """
    assert settings.DEBUG is False  # proving the bracket did the work
    seed_data(1)
    # One deterministically anonymous-visible row (seed_data randomizes Item
    # privacy; the test_products_api precedent creates targeted rows after the
    # seed), so ``first: 1`` always has an edge to return.
    Item.objects.create(
        name="DebugVisibleWidget",
        category=Category.objects.filter(is_private=False).order_by("pk").first(),
        is_private=False,
    )
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    res = client.query("query { allItems(first: 1) { edges { node { name } } } }")

    assert len(res.data["allItems"]["edges"]) == 1  # the data is intact
    payload = _debug(res)
    # Filter by row semantics - never positional indexing or raw counts,
    # because transaction rows are in contract.
    select_rows = [row for row in payload["sql"] if row["isSelect"] is True]
    assert select_rows, payload["sql"]
    first_select = select_rows[0]
    assert first_select["vendor"] == connection.vendor
    assert first_select["alias"] == "default"
    assert "SELECT" in first_select["sql"].upper()
    # Interpolated per the spec: ``last_executed_query`` output carries the
    # bound values, so no placeholder survives (sqlite and postgres alike).
    assert "%s" not in first_select["sql"]
    assert isinstance(first_select["duration"], float)
    assert first_select["isSlow"] is False
    assert first_select["isSelect"] is True
    assert payload["exceptions"] == []


# ---------------------------------------------------------------------------
# Scenario 2 - optimizer composition: the payload demonstrates the planned
# visibility-safe two-query prefetch shape.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_composition_shows_the_two_query_prefetch_shape(install_probe_schema):
    """The captured rows show one item slice + one category prefetch, never N+1.

    ``CategoryType`` defines a custom ``get_queryset`` visibility hook, so the
    optimizer deliberately downgrades the forward FK to a ``Prefetch`` - the
    semantic row assertions the existing live proof
    ``test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http``
    already pins, re-read here through the debug payload instead of
    ``CaptureQueriesContext``. Run anonymously so no auth queries pollute the
    rows; the expected edge count derives from the equivalent post-cascade ORM
    query (API == ORM), robust across ``seed_data``'s random privacy.
    """
    seed_data(2)
    # One deterministically visible edge (scenario 1's idiom), created BEFORE
    # the derived count: guarantees a non-empty item slice so the category
    # Prefetch always executes and the two-SELECT assertion cannot flake on
    # ``seed_data``'s random Item privacy.
    Item.objects.create(
        name="DebugPrefetchWidget",
        category=Category.objects.filter(is_private=False).order_by("pk").first(),
        is_private=False,
    )
    visible_count = Item.objects.filter(is_private=False, category__is_private=False).count()
    install_probe_schema([lambda: _optimizer, _acknowledged_debug])
    client = TestClient()

    res = client.query("query { allItems { edges { node { name category { name } } } } }")

    assert len(res.data["allItems"]["edges"]) == visible_count
    select_statements = [row["sql"].lower() for row in _debug(res)["sql"] if row["isSelect"]]
    # Exactly the two-query shape: one item slice + one category prefetch.
    assert len(select_statements) == 2, select_statements
    item_slices = [s for s in select_statements if "products_item" in s]
    assert len(item_slices) == 1, select_statements
    assert any("products_category" in s for s in select_statements)
    # No inter-products JOIN: the visibility hook forces the Prefetch downgrade.
    assert not any(
        "products_item" in s and "products_category" in s and "join" in s
        for s in select_statements
    )
    # The item slice shows the optimizer's projected column list - the payload
    # as the optimizer's observability surface.
    assert '"products_item"."name"' in item_slices[0]


# ---------------------------------------------------------------------------
# Scenario 3 - mutation capture.
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_mutation_capture_includes_the_insert_row(install_probe_schema):
    """The write path is captured like the read path - INSERT beside the pipeline SELECTs.

    ``transaction=True`` because the assertions tolerate connection-level
    ``BEGIN`` / ``COMMIT`` rows, which the default savepoint-wrapped test
    transaction would suppress. The permitted writer follows the
    ``test_client_api.py`` precedent: the NON-staff ``view_item_1`` user is
    granted only the explicit ``add_item`` codename (never the superuser
    short-circuit) and re-fetched to drop the stale permission cache; the
    required ``categoryId`` derives from a category the writer can SEE.
    """
    create_users(1)
    seed_data(1)
    user_model = get_user_model()
    user = user_model.objects.get(username="view_item_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_item", content_type__app_label="products"),
    )
    user = user_model.objects.get(pk=user.pk)  # drop the stale perm cache
    visible_category = Category.objects.filter(is_private=False).order_by("pk").first()
    category_gid = str(
        relay.GlobalID(type_name="products.category", node_id=str(visible_category.pk)),
    )
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    with client.login(user):
        res = client.query(
            _CREATE_ITEM,
            variables={"d": {"name": "DebugWidget", "categoryId": category_gid}},
        )

    assert res.data["createItem"]["errors"] == []
    assert res.data["createItem"]["node"]["name"] == "DebugWidget"
    rows = _debug(res)["sql"]
    # Assert by statement prefix, never by position or raw total: pipeline
    # SELECTs and Django's own BEGIN / COMMIT accounting rows may interleave.
    insert_rows = [row for row in rows if row["sql"].upper().lstrip().startswith("INSERT")]
    assert insert_rows, [row["sql"] for row in rows]
    assert all(row["isSelect"] is False for row in insert_rows)
    assert any(row["isSelect"] is True for row in rows)  # the pipeline SELECTs ride along


# ---------------------------------------------------------------------------
# Scenario 4 - a resolver execution exception populates the second list.
# ---------------------------------------------------------------------------


def test_resolver_exception_produces_an_unmasked_exception_row(install_probe_schema):
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    res = client.query("query { boom }", assert_no_errors=False)

    assert res.errors  # the ordinary GraphQL error remains present
    payload = _debug(res)
    assert len(payload["exceptions"]) == 1
    row = payload["exceptions"][0]
    assert row["excType"] == "<class 'ZeroDivisionError'>"
    assert row["message"] == "division by zero"
    assert "Traceback" in row["stack"]
    # The two lists are independent: sql exists (empty or not) beside the row.
    assert isinstance(payload["sql"], list)


# ---------------------------------------------------------------------------
# Scenario 5 - the validation-versus-execution error boundary.
# ---------------------------------------------------------------------------


def test_validation_versus_execution_error_boundary(install_probe_schema):
    """No key for a validation failure; a completion error IS an execution row.

    The second half pins the documented result-level widening beyond
    graphene's resolver-only middleware: a non-null field resolving ``None``
    executes, graphql-core raises the completion error, and the row appears.
    """
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    unknown = client.query("query { definitelyNotAField }", assert_no_errors=False)
    assert unknown.errors
    assert "debug" not in (unknown.extensions or {})  # nothing executed

    broken = client.query("query { brokenNonNull }", assert_no_errors=False)
    assert broken.errors
    payload = _debug(broken)  # execution happened, so the key is present
    assert len(payload["exceptions"]) == 1
    assert "non-nullable" in payload["exceptions"][0]["message"].lower()


# ---------------------------------------------------------------------------
# Scenario 6 - a no-SQL operation carries both keys, both empty.
# ---------------------------------------------------------------------------


def test_no_sql_operation_carries_both_empty_lists(install_probe_schema):
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    res = client.query("query { __typename }")

    assert _debug(res) == {"sql": [], "exceptions": []}


# ---------------------------------------------------------------------------
# Scenario 7 - off by default.
# ---------------------------------------------------------------------------


def test_off_by_default_publishes_no_debug_key(install_probe_schema):
    """Without any debug entry in ``extensions=``, no key appears and no envelope widens.

    Distinct from scenario 8's withheld payload: there the extension IS listed
    and refuses; here it was never installed, so nothing runs at all.

    Asserted on the envelope keys - the honest claim; the release-wide
    Strawberry-floor raise means "byte-identical to 0.0.13" is deliberately
    NOT this scenario's contract.
    """
    install_probe_schema([lambda: _optimizer])  # the otherwise-equivalent schema
    client = TestClient()

    res = client.query("query { __typename }")

    assert res.data == {"__typename": "Query"}
    assert "debug" not in (res.extensions or {})
    assert set(res.response.json()) == {"data"}  # no unrelated envelope widening


# ---------------------------------------------------------------------------
# Scenario 8 (spec-048 Decision 5) - the fail-closed gate over a real request.
# ---------------------------------------------------------------------------


@override_settings(DEBUG=False)
def test_debug_false_bare_class_entry_withholds_the_payload_and_warns(
    install_probe_schema,
    caplog,
):
    """A production schema that lists the class gets NO payload and ONE warning.

    The ubiquitous spelling ``extensions=[DjangoDebugExtension]`` is what a
    deployment copies out of a tutorial; under ``settings.DEBUG`` false it must
    publish nothing while leaving the operation's own ``data`` intact, and it
    must say so in the log rather than only through an absent key.
    """
    install_probe_schema([DjangoDebugExtension])
    client = TestClient()

    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        res = client.query("query { __typename }")

    assert res.data == {"__typename": "Query"}  # the operation is unaffected
    assert "debug" not in (res.extensions or {})
    warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING and record.name == "django_strawberry_framework"
    ]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "allow_unsafe_production" in message
    assert "withheld" in message


@override_settings(DEBUG=False)
def test_acknowledged_factory_publishes_the_payload_under_debug_false(
    install_probe_schema,
    caplog,
):
    """The acknowledgement factory is the deliberate opt-out - payload published, no warning."""
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        res = client.query("query { __typename }")

    assert _debug(res) == {"sql": [], "exceptions": []}
    assert [
        record for record in caplog.records if record.name == "django_strawberry_framework"
    ] == []


@override_settings(DEBUG=False)
def test_acknowledged_factory_keeps_one_instance_per_operation(install_probe_schema):
    """A factory entry is still fresh per operation: no payload leaks into the next request."""
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    failing = client.query("query { boom }", assert_no_errors=False)
    clean = client.query("query { __typename }")

    assert [row["message"] for row in _debug(failing)["exceptions"]] == ["division by zero"]
    # The second operation's payload is its own - not the first operation's stash.
    assert _debug(clean) == {"sql": [], "exceptions": []}


# ---------------------------------------------------------------------------
# Scenario 9 (spec-048 Decision 6) - the caps are wired into a real operation's
# published payload, not merely available as a helper.
# ---------------------------------------------------------------------------


def test_over_cap_exception_message_is_truncated_in_the_published_payload(install_probe_schema):
    """A real resolver raise past the message cap reaches the wire cut and marked."""
    install_probe_schema([_acknowledged_debug])
    client = TestClient()

    res = client.query("query { hugeBoom }", assert_no_errors=False)

    assert res.errors
    rows = _debug(res)["exceptions"]
    assert len(rows) == 1
    message = rows[0]["message"]
    assert message == "x" * _EXCEPTION_MESSAGE_CAP + _TRUNCATION_MARKER
    assert message.endswith(_TRUNCATION_MARKER)
    assert rows[0]["excType"] == "<class 'ValueError'>"


# ---------------------------------------------------------------------------
# Scenario 10 - the shipped aggregate fakeshop schema stays debug-free.
# ---------------------------------------------------------------------------


@pytest.mark.urls("config.urls")
def test_project_graphql_endpoint_publishes_no_debug_key():
    """The real ``/graphql/`` must never carry the diagnostic - the probe URLconf owns it.

    The function-level ``urls`` mark overrides this module's, so the request
    reaches the project's own shipped schema rather than the probe holder.
    """
    client = TestClient()

    res = client.query("query { __typename }")

    assert res.data == {"__typename": "Query"}
    assert "debug" not in (res.extensions or {})
