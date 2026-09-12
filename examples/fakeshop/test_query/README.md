# Writing tests

The manual for writing tests in this repository: where a test goes, what it must prove, how a shortcut test becomes a real one, and what the fakeshop live tier owes every package line it can reach.

For agents. Binding. [AGENTS.md][agents] = law, one line each; this = long form w/ examples. [START.md][start] = cross-release hazards. [docs/TREE.md][tree-tests] = per-file layout. [CONTRIBUTING.md][contributing] = human mechanics. [Fakeshop tutorial][fakeshop-readme] = what the fixture demonstrates. This file vs a module docstring disagree → docstring describes one file, this describes the rule; fix the wrong one, same change.

## Contents

1. [The rule](#the-rule)
2. [Where a test goes](#where-a-test-goes)
3. [Anatomy of a live test](#anatomy-of-a-live-test)
4. [Before / after: promoting a shortcut test](#before--after-promoting-a-shortcut-test)
5. [Breaking a test up](#breaking-a-test-up)
6. [Shipped schema can't reach the subject](#shipped-schema-cant-reach-the-subject)
7. [Worked examples](#worked-examples)
8. [What legitimately stays package-side](#what-legitimately-stays-package-side)
9. [Isolation contract](#isolation-contract)
10. [Clients, transports, credentials](#clients-transports-credentials)
11. [Environment tiers](#environment-tiers)
12. [Prove the test can fail](#prove-the-test-can-fail)
13. [Test code style](#test-code-style)
14. [Checklist](#checklist)
15. [Suite map](#suite-map)

## The rule

**Real test > targeted test, even when slower to write and run.** Real = GraphQL doc over HTTP to fakeshop `/graphql/`, against the schema fakeshop composes, rows in DB, user on request. Targeted = throwaway type, private helper call, one branch via `SimpleNamespace`. Both turn a line green; only the first proves what a consumer sees.

Preference order, fixed:

1. Live request, fakeshop's shipped schema.
2. Live request, fakeshop surface added for the purpose. "Fixture can't reach it" = fixture gap, not unreachability → extend fixture.
3. Live request, test-local holder schema mounted beside fakeshop. Still HTTP.
4. In-process `schema.execute_sync` on the composed project schema.
5. Package tier, throwaway types.
6. Mock, only when real path impossible. Mock behaviour, never the class.

Speed never justifies skipping a rung. `pytest.ini` parallel default = the speed budget; a live row's extra ms is the price.

Two corollaries, enforced:

- **Live-first, both verdicts, and the must-not.** Any `django_strawberry_framework/` line a real fakeshop query reaches MUST be covered from this dir. Acceptance ≠ rejection: a plan can pin rejection live and leave acceptance package-only; rejection row covers nothing about acceptance. Check which VERDICT each live row proves. Claim = a behaviour is SCOPED (write-only exemption, an ordering, a one-surface opt-in) → row also owes the adjacent case that must NOT get it; positive alone proves the mechanism, not the boundary ([example 4](#4-the-must-not-only-a-real-session-can-phrase-isprivate-refetch)).
- **Promotion deletes the stand-in.** Package copy goes in the same change, after the live row is shown to fail w/ boundary removed ([Prove the test can fail](#prove-the-test-can-fail)). Two tests, one claim = debt, not safety.

Coverage = package only, `fail_under = 100`; live tests here are how it gets there. Example apps run every suite, never count. Don't add them to the gate.

## Where a test goes

Four trees, one `pytest.ini`, one command `uv run pytest`.

| Tree | SUT | Style | Package? |
|---|---|---|---|
| `examples/fakeshop/test_query/` | any package line a real query reaches | live `/graphql/` HTTP via [`graphql_client.py`][graphql-client] | no |
| `examples/fakeshop/apps/<app>/tests/` | one app's models/admin/services/commands | in-process: model methods, admin, services, `call_command`. NOT `execute_sync` on the composed schema; a query that reaches the claim → `test_query/` ([example 9](#9-wrong-tree-over-the-real-schema-composition-introspection)) | yes, `apps.<app>.tests` |
| `examples/fakeshop/tests/` | project/config only: urls, settings guard, schema export, project commands | in-process `Client`, `call_command` | no, never add `__init__.py` |
| `tests/` | package + repo tooling | in-process; throwaway `DjangoType`s; fakeshop models OK as fixtures | mirrors package layout |

Ask in order:

1. Real GraphQL doc against fakeshop can observe the claim? → here, in the suite owning the app/surface ([suite map](#suite-map)). No shipped field reaches it? Read [Shipped schema can't reach the subject](#shipped-schema-cant-reach-the-subject) BEFORE saying no.
2. Subject = one fakeshop app's own code (model method, admin action, service, command)? → `apps/<app>/tests/`. Each app owns its coverage; delete app = lose only its tests.
3. Subject = fakeshop as project (routing, `DEBUG` guard, schema export)? → `examples/fakeshop/tests/`.
4. Subject = package internal no request observes (registry lifecycle, construction-time validation, pure-function precedence, absence proof, repo tooling)? → `tests/`, file mirroring the module. `tests/base/` = exactly `test_init.py` + `test_conf.py`, may grow, no new files.

Landed in 2–4 while a real query could reach it = misplaced. Fix = move, not a live twin beside it.

## Anatomy of a live test

Seed → pick viewer → post doc → assert payload exactly → if claim is cost/shape, assert SQL.

```python
"""Live GraphQL HTTP tests for the library visibility hook: hidden rows never leave the row fetch."""

import pytest
from apps.library import models
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from graphql_client import assert_graphql_data, assert_graphql_success


def _seed_shelf_with_repair_book():
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="Fiction", branch=branch)
    models.Book.objects.create(title="Kindred", shelf=shelf)
    models.Book.objects.create(
        title="Dune",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.REPAIR,
    )


@pytest.mark.django_db
def test_anonymous_book_list_excludes_repair_rows_in_the_row_query():
    """``BookType.get_queryset`` drops ``repair`` rows for an anonymous viewer inside the one book query."""
    _seed_shelf_with_repair_book()

    with CaptureQueriesContext(connection) as captured:
        assert_graphql_data(
            "{ allLibraryBooks { title } }",
            {"allLibraryBooks": [{"title": "Kindred"}]},
        )

    book_queries = [q["sql"] for q in captured.captured_queries if "library_book" in q["sql"]]
    assert len(book_queries) == 1
    assert "repair" in book_queries[0]


@pytest.mark.django_db
def test_staff_book_list_keeps_repair_rows():
    """The same field returns every row once the viewer is staff."""
    create_users(1)
    _seed_shelf_with_repair_book()
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    data = assert_graphql_success("{ allLibraryBooks { title } }", client=client)

    assert sorted(book["title"] for book in data["allLibraryBooks"]) == ["Dune", "Kindred"]
```

- **Module docstring**: FIRST LINE = one period-terminated sentence naming the subject; later paragraphs free (`build_tree_md.py::assert_single_sentence` checks the extracted first line only). [TREE.md][tree-tests] renders that line; renderer fails on missing / multi-sentence first line; changing it → re-render, same change.
- **Capture helper per suite.** Every SQL-shape suite spells its own post-and-capture pair (`_capture` / `_capture_as_staff` in [`test_single_parent_fastpath_api.py`][test-single-parent-fastpath-api], `_library_sql` in [`test_library_api.py`][test-library-api]); [`graphql_client.py`][graphql-client] deliberately has none. Read the target file's helpers before writing a capture.
- **Seeding** per app. Products/auth: `seed_data(N)` / `create_users(N)` from [`apps/products/services.py`][products-services] first line; never hand-roll Category/Item/Property/Entry/User. Library: inline `Model.objects.create` (no services module). Seed the full non-null chain (Branch → Shelf → Book).
- **Viewer** = `django.test.Client`. Anonymous default. `force_login` a seeded user: `create_users` gives `staff_N` (`is_staff`), `regular_N`, `view_<model>_N` per products model, all `TEST_USER_PASSWORD`. Model-perm check → grant codename to a NON-superuser in-test; superuser short-circuits, proves nothing.
- **Request** via [`graphql_client.py`][graphql-client]. `assert_graphql_data` = 200 + no `errors` + exact `data`. `assert_graphql_success` → `data`. `graphql_payload` → whole envelope (rows about `errors`). `post_graphql` → raw `HttpResponse` (headers, status). JSON path routes through package [`TestClient`][glossary-testclient], so live rows exercise the consumer client too.
- **Payload** exact wherever data allows. Faker-seeded products → derive expected from the equivalent ORM query, never pin names.
- **SQL** = the instrument for optimizer / visibility / pagination claims. Filter `captured_queries` to the table under test, on `FROM "<table>"` when the selection touches a relation (M2M through-tables share the parent's prefix: `"library_book" in sql` also matches `library_book_genres`), assert count, then fragment (`LIMIT 2 OFFSET 1`, `EXISTS`, no `COUNT(`, no `DISTINCT`). Never assert bare total count; session / auth / content-type queries ride along the moment a viewer logs in. Plan-object attributes each translate to exactly one SQL fact (`select_related` → `JOIN`, `Prefetch` → second query on the target table, `only_fields` attname → column in root `SELECT`); an attribute w/ no translation was never a contract ([example 2](#2-sql-beats-the-plan-object-the-hint-pair)).
- **Identifiers minted, never pinned.** GlobalIDs via [`global_id_for`][testing-relay] over the real type; cursors from a prior `endCursor`. Package-owned encodings, may change.

## Before / after: promoting a shortcut test

Shortcut shape, condensed from the throwaway-type idiom in [`tests/test_connection.py`][tests-connection]. Claim: "connection w/o `total_count` opt-in exposes no `totalCount`":

```python
def _make_node_type(name, *, total_count):
    meta = {"model": Genre, "fields": ("id", "name"), "interfaces": (relay.Node,)}
    if total_count is not None:
        meta["connection"] = {"total_count": total_count}
    return type(name, (DjangoType,), {"Meta": type("Meta", (), meta)})


def test_total_count_absent_unless_opted_in():
    node_type = _make_node_type("BareGenre", total_count=None)

    @strawberry.type
    class Query:
        genres: DjangoConnection[node_type] = DjangoConnectionField(node_type)

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config())

    result = schema.execute_sync("{ genres(first: 2) { edges { node { name } } } }")

    assert result.errors is None
    assert "totalCount" not in str(schema)
```

Passes. Proves ~nothing a consumer cares about: type not shipped, schema not fakeshop's, no view, no visibility hook, "not in SDL string" says nothing about whether a `COUNT` ran.

Same claim as it lives in [`test_library_api.py`][test-library-api]:

```python
@pytest.mark.django_db
def test_genre_connection_total_count_omitted_no_count():
    """Omitting ``totalCount`` returns a correct count-less response and issues no count query."""
    _seed_genres("Alpha", "Beta", "Gamma")

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConnection(first: 2) {
                edges { node { id name } }
                pageInfo { hasNextPage }
              }
            }
            """,
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenresConnection"]
    names = [edge["node"]["name"] for edge in conn["edges"]]
    assert names == ["Alpha", "Beta"]
    assert "totalCount" not in conn
    assert not any("COUNT(" in query["sql"].upper() for query in captured.captured_queries)
```

What moved:

1. **Type = shipped `GenreType`** ([`apps/library/schema.py`][lib-schema], `connection = {"total_count": True}`). Proves selection gating on a type that opted in = the consumer contract; throwaway proved a weaker SDL fact about a type nobody ships.
2. **Schema = composed project schema**, reloaded by [`conftest.py`][conftest] autouse fixtures. Every app registered → a relation target that raises at finalize in prod raises here.
3. **Request crossed the view.** Middleware, optimizer extension, user on request. Resolver reading `info.context.request` exercised, not skipped.
4. **Assertion = wire + DB**, not a schema string. `"totalCount" not in conn` = what client sees; no `COUNT(` = what DB saw.
5. **Rows real.** Three genres, page of two, actionable `hasNextPage`.

What stayed: package tier keeps `test_connection_type_for_returns_concrete_subclass_without_opt_in` — generated connection is a concrete subclass, not the `DjangoConnection[T]` alias. Construction-time identity, no wire shape. Its docstring names this dir as home of the consumer round-trips. Package file says what it does NOT carry; live file says nothing about the package tier (consumer never sees it).

Promote → delete shortcut same change, then sweep what the shortcut alone kept alive: helpers, module constants, builder kwargs whose only caller was the deleted row (ruff sees unused imports, not an orphaned `def`; grep each name, count `1` = definition-only), the module docstring's bullets, and prose citations: `grep -rn -F '<name>' docs/ KANBAN.md` (bare name, not `::name`; prose rarely qualifies) plus `strings examples/fakeshop/db.sqlite3 | grep -F '<name>'` for a board row the next render would surface (a hit there may be freelist residue; confirm through the kanban app). The citation gate reads `.py` + `KANBAN.md` only. Run the live row w/ boundary removed first ([`prove_failability.py`][prove-failability]). Live row doesn't fail → one of two things, opposite fixes: the row isn't covering the claim yet (add assertions), OR the docstring you inherited names a boundary neither row pins (find the real one, rewrite the claim). Check the second first; a promoted docstring carries its author's belief, not a measurement ([example 7](#7-the-stand-ins-docstring-lied-corrupt-image)). Also: a green run can mean the MUTATION was absorbed (unreachable guard, a root the optimizer never plans, fail-open `fields=[]`); the script's `WEAKLY PINNED` verdict points at the test, check the mutation first.

## Breaking a test up

Shortcut tests carry several claims under one name. Split along claims BEFORE moving.

One claim per row. `test_title_filters` looping three lookups = one node id: failure in #2 hides #3; failability counts the loop as ONE row however many boundaries it crosses.

Before:

```python
@pytest.mark.django_db
def test_title_filters():
    _seed_books("Kindred", "Dune")
    for lookup, value, expected in [
        ("exact", '"Kindred"', ["Kindred"]),
        ("iContains", '"kin"', ["Kindred"]),
        ("in", '["Kindred", "Dune"]', ["Dune", "Kindred"]),
    ]:
        data = assert_graphql_success(
            "{ allLibraryBooks(filter: { title: { %s: %s } }, orderBy: [{ title: ASC }]) { title } }"
            % (lookup, value),
        )
        assert [b["title"] for b in data["allLibraryBooks"]] == expected
```

After:

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("lookup", "value", "expected"),
    [
        ("exact", '"Kindred"', ["Kindred"]),
        ("iContains", '"kin"', ["Kindred"]),
        ("in", '["Kindred", "Dune"]', ["Dune", "Kindred"]),
    ],
    ids=["exact", "icontains", "in"],
)
def test_book_title_lookup_returns_only_matching_rows(lookup, value, expected):
    """Each declared ``title`` lookup on ``BookFilter`` narrows ``allLibraryBooks`` to the matching rows."""
    _seed_books("Kindred", "Dune", "Neuromancer")
    query = (
        "{ allLibraryBooks(filter: { title: { %s: %s } }, orderBy: [{ title: ASC }]) { title } }"
        % (lookup, value)
    )

    data = assert_graphql_success(query)

    assert [b["title"] for b in data["allLibraryBooks"]] == expected
```

Rules applied:

- **Parametrize, don't loop.** Each case = own node id, readable `ids=`.
- **Seed a row that must NOT match.** `Neuromancer` → unfiltered result can't pass by accident. Assert the list, not `len == 2`; cardinality is satisfiable by wrong rows.
- **Split acceptance from rejection.** Declared lookup vs undeclared = two rows, two tests; rejection asserts the exact envelope error, never just "errors present".
- **Name = invariant**, not card / slice / bug number. Docstring may cite spec decision or glossary anchor; never how the test came to exist.
- **Explicit ordering.** Any list-order assertion carries `orderBy:`; no insertion-order flake.

Claims span two tiers → split by tier: consumer-visible live, construction-time package-side w/ docstring naming the live sibling.

## Shipped schema can't reach the subject

"No fakeshop field exposes this" = the most common misplacement. Three tools, in order, keep it live.

**1. Extend the fixture.** Fakeshop exists to be extended. `allLibraryBranchesViaListField` in [`apps/library/schema.py`][lib-schema] exists for ONE reason: give `DjangoListField` a live surface beside the connections. Feature w/o consumer surface in fakeshop → add one, in the app whose model fits, declared as a consumer would, field docstring naming it the acceptance surface.

**2. Settings flag read in the class body.** Permanent exposure would change fakeshop's public contract → gate it. `LoanType` reads `FAKESHOP_TEST_LOAN_CONNECTION` inside `Meta`, adds `relay.Node` + `connection = {"total_count": True}` under the flag only; `Query` reads the same flag for `allLibraryLoansConnection`. Test: `override_settings(FAKESHOP_TEST_LOAN_CONNECTION=True)` → `project_schema_override` fixture rebuilds → drive real `/graphql/` → autouse guard restores default on exit. Companion row asserts the field ABSENT by default; flag never leaks into shipped shape.

**3. Holder schema beside fakeshop.** Subject = consumer-declared class no fakeshop app would plausibly ship (hostile `OrderSet` override, counting converter, second view mount w/ different body cap) → build schema in the test module, mount on own URL:

```python
_CURRENT: dict[str, Any] = {"schema": None}


def _graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _graphql_view)]


def _post(schema, query, *, client=None, variables=None):
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return post_graphql(query, client=client, variables=variables, url="/graphql-test/")
    finally:
        _CURRENT["schema"] = None
```

Request still crosses the full HTTP pipeline. `override_settings(ROOT_URLCONF=...)` / `pytest.mark.urls` already clear resolver caches (Django's `setting_changed` receiver, both directions); call `clear_url_caches()` yourself only when the holder swaps its held schema WITHOUT changing `ROOT_URLCONF`. The reference impls below still call it inside their `override_settings` brackets; redundant, harmless, don't copy it into new mounts. What every holder mount DOES owe: resolve the schema at request time (`from config.schema import schema` INSIDE the view function, or the `_CURRENT` dict above). A schema captured at import is the pre-reload one and fails in a LATER module on the same worker, not yours. Holder types declared inside test body / fixture depending on the module reload, never at import; registry clear between modules would strand them (the autouse guard raises "Reloading the project schema shell mutated app registrations", naming the fixture, not your file). Mount path is the module's choice (`/graphql-test/`, `/graphql/` in own URLconf, `cap-misconfigured/`); function-level `@pytest.mark.urls("config.urls")` reaches the shipped endpoint from inside a holder module. Async mounts spelled longhand must carry `@_carrying_the_packages_csrf_mark(AsyncDjangoGraphQLView)` themselves. Reference impls: [`test_list_field_api.py`][test-list-field-api], [`test_products_visibility_api.py`][test-products-visibility-api], [`test_transport_api.py`][test-transport-api].

All three exhausted → `tests/`, and the docstring names the rung BY NUMBER, states the specific fakeshop change that would reach it, and why that change is unacceptable. "No shipped type declares this" disposes of rungs 1–2 and says nothing about rung 3; several package rows justified themselves that way and were promotable the same day.

## Worked examples

One promotion sweep, real rows. Each example = the package row as it stood (since deleted) → the live row that replaced it → what moved. Ordered by the lesson, widest range first; shapes already shown once get a line, not a block. Every live row here was proven to fail w/ its boundary removed before the stand-in went.

### 1. Wiring vs class: the plan cache

Package row proved the CLASS caches; fakeshop's whole `extensions=[lambda: _optimizer]` wiring in `config/schema.py` exists so the cache survives across REQUESTS, and nothing proved that.

Before (`tests/optimizer/test_extension.py::test_cache_hit_on_repeated_query`):

```python
@pytest.mark.django_db
def test_cache_hit_on_repeated_query(django_assert_num_queries):
    """B1: executing the same query twice produces a cache hit on the second call."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allItems { name category { name } } }"

    schema.execute_sync(query)
    assert ext.cache_info().misses == 1
    schema.execute_sync(query)
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1
```

After ([`test_library_api.py`][test-library-api]`::test_library_optimizer_plan_cache_is_reused_across_http_requests`):

```python
_PLAN_CACHE_DOCUMENT = """
query {
  allLibraryMembershipCards {
    barcode
    patron { name }
  }
}
"""


@pytest.mark.django_db
def test_library_optimizer_plan_cache_is_reused_across_http_requests():
    """The shipped optimizer plans one document once and reuses that plan next request.

    ``config/schema.py`` holds a single module-level ``DjangoOptimizerExtension``
    and hands the schema a ``lambda: _optimizer`` factory, so the instance-bound
    plan cache outlives a request. Two identical documents over ``/graphql/``
    therefore record a miss then a hit against ONE cache entry. A per-request
    extension would report two misses; a reused plan that had gone stale would
    change the emitted SQL, so the second request's library SQL must match the
    first's exactly.
    """
    _seed_library_graph()
    optimizer = sys.modules["config.schema"]._optimizer
    # The per-test schema rebuild is what makes the counters below absolute.
    assert optimizer.cache_info().size == 0, optimizer.cache_info()

    with CaptureQueriesContext(connection) as first_capture:
        first = _post_graphql(_PLAN_CACHE_DOCUMENT)
    assert optimizer.cache_info().misses == 1
    assert optimizer.cache_info().hits == 0

    with CaptureQueriesContext(connection) as second_capture:
        second = _post_graphql(_PLAN_CACHE_DOCUMENT)
    assert optimizer.cache_info().hits == 1
    assert optimizer.cache_info().misses == 1
    assert optimizer.cache_info().size == 1

    assert second.json()["data"] == first.json()["data"]
    assert _library_sql(second_capture) == _library_sql(first_capture)
```

What moved: the extension under test is the one `config.urls` serves, reached via `sys.modules["config.schema"]` at call time (the conftest rebuilds that module before every test; a module-level import binds a discarded instance and reads zeros forever, passing). The obvious document (`allLibraryBooks { shelf { code } }`) measured `misses=2, size=0`: `BookType` / `ShelfType` declare `get_queryset`, and a plan w/ a hook in the selection is `cacheable=False`. Throwaway types had no hooks so the package row never met this. SQL-identity clause added: a stale reused plan would change the emitted SQL.

Failability: `extensions=[lambda: _optimizer]` → fresh instance per request → row fails.

### 2. SQL beats the plan object: the hint pair

`LoanType.Meta.optimizer_hints = {"book": OptimizerHint.prefetch_related(), "patron": OptimizerHint.SKIP}` ships in [`apps/library/schema.py`][lib-schema]. Two package rows redeclared the same hints on a throwaway `ItemType` and read `ctx.dst_optimizer_plan`.

Before (`tests/optimizer/test_extension.py::test_optimizer_hint_force_prefetch`, trimmed):

```python
    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.prefetch_related()}

    ...
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allItems { name category { name } } }", context_value=ctx)
    plan = ctx.dst_optimizer_plan
    assert [lookup.prefetch_to for lookup in plan.prefetch_related] == ["category"]
    assert "category" not in plan.select_related
    assert "category_id" in plan.only_fields
```

After ([`test_library_api.py`][test-library-api]`::test_library_optimizer_hints_are_observable_over_http`, prefetch half):

```python
    with CaptureQueriesContext(connection) as captured_prefetch:
        prefetch_response = _post_graphql("query { allLibraryLoans { book { title } } }")
    ...
    # Two loan rows, two queries: the root read plus ONE batched book fetch.
    assert len(captured_prefetch) == 2
    assert "JOIN" not in captured_prefetch[0]["sql"]
    assert "library_loan" in captured_prefetch[0]["sql"]
    # The forced prefetch needs the FK column, so the root projection keeps it.
    assert "book_id" in captured_prefetch[0]["sql"]
    assert "library_book" in captured_prefetch[1]["sql"]
```

SKIP half: `library_patron` absent from the root SQL AND a patron query per row (index 1 and 2), i.e. lazy load, not a batched prefetch. That is the live spelling of "not planned".

What moved: every plan attribute became the SQL fact it implies. `prefetch_to == ["category"]` → second query against the target table; `"category" not in select_related` → no `JOIN` in root; `"category_id" in only_fields` → `book_id` in root SELECT. Translation table:

| Plan attribute | Wire / SQL fact |
|---|---|
| `select_related` contains X | `JOIN` on X's table in the root query |
| `prefetch_related` contains X | second query against X's table, none in root |
| `only_fields` contains attname | that column in root `SELECT` |
| `cacheable is False` | `cache_info().misses == 2` over two identical requests |
| hint `SKIP` on X | no X table anywhere planned; one lazy query per row on access |

An attribute w/ no translation was never a contract; drop it, don't promote it.

Failability: delete the `optimizer_hints` line on `LoanType` → row fails. Deleting the walker's elision guard for a hooked target changed NOTHING: `plan_relation` downgrades to `Prefetch` first, so that guard is unreachable on this path. The package row was pinning a dead guard.

### 3. Two green tests, contradictory contracts: the optimizer-less `1 + N`

`tests/test_relay_connection.py::test_synthesized_connection_per_parent_query_cost` asserted `1 + N` queries for a nested connection ("pre-033 posture"); `test_library_api.py::test_nested_books_connection_fixed_query_count` asserts the count is independent of N. Both green because `_schema_with_root` built a bare `strawberry.Schema` w/o the optimizer. An optimizer-less consumer is a real configuration, so the claim belongs on a holder mount WITHOUT the extension.

Before:

```python
@pytest.mark.django_db
def test_synthesized_connection_per_parent_query_cost(django_assert_num_queries):
    """Each parent row pays its own window query - the documented cost contract.

    Relation-seeded connections run per-parent (no
    cross-parent batching in the pre-``033`` posture), so ...
    """
    services.seed_data(2)
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))

    schema = _schema_with_root(category_type)
    parent_count = Category.objects.count()
    with django_assert_num_queries(1 + parent_count):
        result = schema.execute_sync(
            "{ objs { itemsConnection(first: 2) { edges { node { name } } } } }",
        )
```

After ([`test_products_visibility_api.py`][test-products-visibility-api]):

```python
def _nested_connection_item_queries(parent_count):
    """Post ``_NESTED_CONNECTION_QUERY`` at ``parent_count`` parents; return the item SQL.

    The holder schema installs NO ``DjangoOptimizerExtension``, so the nested
    connection runs off the relation manager rather than a planned window.
    """
    parent_pks = list(
        Category.objects.order_by("pk").values_list("pk", flat=True)[:parent_count],
    )

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return list(Category.objects.filter(pk__in=parent_pks).order_by("pk"))

    with CaptureQueriesContext(connection) as captured:
        payload = _post_visibility_query(strawberry.Schema(query=Query), _NESTED_CONNECTION_QUERY)
    assert payload.get("errors") is None, payload
    assert len(payload["data"]["categories"]) == parent_count
    return [entry["sql"] for entry in captured.captured_queries if "products_item" in entry["sql"]]


def test_nested_connection_costs_one_query_per_parent_without_the_optimizer(db):
    """With no optimizer installed a nested connection costs one window query per parent.

    ... measured at two cardinalities so a fixed count cannot satisfy it, and so a
    regression toward per-EDGE loading (which would overshoot N) is visible.
    """
    services.seed_data(1)

    assert len(_nested_connection_item_queries(2)) == 2
    assert len(_nested_connection_item_queries(5)) == 5
```

What moved: shipped `CategoryType` (imported inside the helper, after the reload), real HTTP through the file's existing holder, two cardinalities so `N` is load-bearing, SQL filtered to `products_item` so session reads don't count. Docstring states the contract; provenance gone. `seed_data(1)` gives 25 categories, hence the pk slice; taking them all pays 26 queries per cardinality.

Failability first attempt measured 0 rows: installing the optimizer on the holder changed nothing because the root returned a `list`, which the optimizer cannot plan. Mutation had to return a queryset too. Read a green run as "mutation absorbed" before "row weak".

### 4. The must-not only a real session can phrase: `isPrivate` refetch

Before (`tests/mutations/test_resolvers.py::test_refetch_skips_visibility_filter_after_authorized_write`, trimmed): a `_hide_private` classmethod, `CategoryT`, `ItemT` built via `type(...)`, `CreateItem(DjangoMutation)` w/ `permission_classes = [_AllowAll]`, `finalize_django_types()`, `execute_sync` of `createItem(data: {isPrivate: true})`, one assert: `node.name == "Hidden"`. Forty lines of declaration; "the caller" a fiction, so the must-not could not be phrased.

After ([`test_products_api.py`][test-products-api]):

```python
@pytest.mark.django_db(transaction=True)
def test_create_item_private_row_is_refetched_for_its_author_but_stays_hidden_from_reads():
    """A permitted caller writing a row their own reads hide still gets it back in the payload.

    `ItemType.get_queryset` hides `is_private` rows from a non-staff viewer, and
    `view_item_1` (granted `add_item`) is exactly such a viewer. The post-write
    re-fetch is by pk WITHOUT the visibility filter, so the payload `node` carries the
    row the caller just wrote. The must-not is the same caller's `allItems` read in
    the same session, which does NOT list it: the write-time re-fetch is an exemption
    for the actor's own write, never a hole in the read-side visibility rule.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login_with_perm("view_item_1", "add_item")

    data = _graphql_data(
        _CREATE_ITEM,
        client=client,
        variables={
            "d": {
                "name": "PrivateLiveWidget",
                "categoryId": _global_id("products.category", category.pk),
                "isPrivate": True,
            },
        },
    )
    result = data["createItem"]
    assert result["errors"] == []
    assert result["node"] == {"name": "PrivateLiveWidget", "category": {"name": category.name}}
    assert models.Item.objects.get(name="PrivateLiveWidget").is_private is True

    # The same caller's read does not see it: the re-fetch exemption is write-only.
    read = _graphql_data("{ allItems { edges { node { name } } } }", client=client)
    names = [edge["node"]["name"] for edge in read["allItems"]["edges"]]
    assert names, read
    assert "PrivateLiveWidget" not in names
```

What moved: shipped `ItemType.get_queryset` IS the hook the package row fabricated. The second half turns "re-fetch skips the filter" from a mechanism note into a security claim: exemption scoped to the write, provable only w/ a session that then reads. `allItems` is a connection (`edges { node }`); a verbatim `{ allItems { name } }` from the package row does not parse.

### 5. Settings override reaches a "misconfigured deployment": sessionless `login`

Before (`tests/auth/test_mutations.py::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares`): throwaway `_login_logout_schema()`, `RequestFactory().post()` w/o `SessionMiddleware`, `request.user = AnonymousUser()`, `execute_sync`. The module's "one declaration per process" exemption did not cover it: the throwaway passed no `permission_classes`, i.e. the `AllowAny` default fakeshop ships.

After ([`test_auth_api.py`][test-auth-api]):

```python
_SESSIONLESS_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [
        entry
        for entry in settings.MIDDLEWARE
        if not any(
            dropped in entry
            for dropped in (
                "debug_toolbar",
                "sessions.middleware",
                "auth.middleware",
                "messages.middleware",
            )
        )
    ],
}


@pytest.mark.django_db
def test_sessionless_login_refuses_with_the_error_naming_both_middleware_stacks():
    """A deployment with no session stack gets the package's actionable refusal, not an ``AttributeError``."""
    create_users(1)

    with override_settings(**_SESSIONLESS_PASS_THROUGH):
        response = _post_graphql(_LOGIN, client=Client(), variables={"u": "staff_1", "p": TEST_USER_PASSWORD})

    payload = response.json()
    assert payload["data"] is None
    message = payload["errors"][0]["message"]
    assert "SessionMiddleware" in message
    assert "AuthMiddlewareStack" in message
```

What moved: rung 2 via settings, real `/graphql/`. THREE middlewares dropped, not one: `AuthenticationMiddleware` and `MessageMiddleware` each `assert hasattr(request, "session")` and die inside Django before the view. Works because `require_session` runs before `authorize_or_raise`, so the missing `request.user` never matters. `Client()` constructed INSIDE the override: `ClientHandler` caches its middleware chain on first request. Pass-through needed to read the message. Logout twin identical.

Same file, same sweep: `login(username: 123, ...)` validation rejection (`test_non_string_login_username_fails_validation_before_the_resolver`, plus `{ me { username } }` still null on that client); backend `PermissionDenied` envelope byte-identical to wrong-password (`test_backend_raising_permission_denied_returns_the_same_envelope`), driven by a module-level `PermissionDeniedBackend` named via `AUTHENTICATION_BACKENDS=["test_auth_api.PermissionDeniedBackend", ...]`. `test_query/` is on `pythonpath`, so a live module's class is a valid settings string. Capture the CONTROL envelope (wrong password) before entering the backend override, else the comparison is vacuous.

### 6. Synthetic model buys nothing: storage degradation

Before (`tests/types/test_resolvers.py::test_per_subfield_guard_isolates_storage_failure`, trimmed): `_make_asset_model()` created via `schema_editor.create_model`, throwaway `_asset_type(model, filesystem_path_fields=("attachment",))`, `transaction=True`, `delete_model` in `finally`, THREE `execute_sync` calls selecting `path` / `url` / `name` one at a time.

After ([`test_uploads_api.py`][test-uploads-api]):

```python
@pytest.mark.django_db
def test_storage_without_absolute_paths_nulls_only_the_path_subfield_over_http(tmp_path, monkeypatch):
    """A backend that cannot produce a path nulls ``path`` alone; ``name`` / ``url`` resolve.

    All three are selected in one request, so a guard that sat on the parent
    would show up as ``attachment: null`` rather than a null ``path``.
    """
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        specimen = models.MediaSpecimen(label="unpathable")
        specimen.attachment.save("doc.txt", ContentFile(b"hello bytes"), save=False)
        specimen.save()

        def _no_absolute_path(self, name):
            raise NotImplementedError("This backend doesn't support absolute paths.")

        monkeypatch.setattr(FileSystemStorage, "path", _no_absolute_path)

        res = TestClient().query("{ allMediaSpecimensWithPath { attachment { name path url } } }")
        attachment = res.data["allMediaSpecimensWithPath"][0]["attachment"]

    assert attachment["path"] is None
    assert attachment["name"].endswith("doc.txt")
    assert attachment["url"].endswith("doc.txt")
```

What moved: shipped `MediaSpecimenWithPathType` already declares the `filesystem_path_fields` opt-in a consumer would; the fixture gap the package row worked around did not exist, so the synthetic model, DDL bracket and `transaction=True` all vanish. The three-request isolation argument inverted: ONE request selecting all subfields is the stronger instrument, because a parent-level guard is then directly observable. Seed BEFORE monkeypatching storage (`_save` calls `self.path`). Siblings promoted the same way: vanished file → `size` null (`os.remove(specimen.attachment.path)`), `SuspiciousFileOperation` propagates (pass-through to see it), plus a mixed row (populated file beside empty image) added before deleting the duplicate trio.

### 7. The stand-in's docstring lied: corrupt image

`test_corrupt_image_degrades_width_and_height_to_null` said `_safe_file_attr` degraded the dimensions. Django's `get_image_dimensions` returns `(None, None)` for unparseable bytes w/o raising; the guard never fires. Caught by failability: the promoted row survived removal of the boundary its docstring named. Real boundary = the nullability `DjangoImageType` declares on `width` / `height`; live row now says that, plus a second row pins the whole field-type map by introspection (`test_file_output_objects_publish_nullable_subfields_over_http`). Rule: verify the stand-in's claim against the code BEFORE copying it into the live row. Read which rows did NOT fail under each mutation; the silence is the finding.

### 8. The error policy masks validation errors too: `BigInt` literals

Before: `tests/types/test_converters.py` rejected `bool` / float literals for `BigInt` through a throwaway schema. Shipped `ScalarSpecimen.signed_big` / `unsigned_big` are filterable.

After ([`test_scalars_api.py`][test-scalars-api]):

```python
@pytest.mark.django_db
@override_settings(**_ERROR_POLICY_PASS_THROUGH)
@pytest.mark.parametrize("field", ["signedBig", "unsignedBig"], ids=["signed", "unsigned"])
@pytest.mark.parametrize(
    ("literal", "reason"),
    [("true", "BigInt does not accept boolean values"), ("1.9", "BigInt cannot parse float")],
    ids=["bool", "float"],
)
def test_filter_specimens_by_bigint_exact_rejects_non_integer_literal(field, literal, reason):
    ...
    assert body["data"] is None, body
    assert reason in body["errors"][0]["message"], body
```

First attempt asserted `"data" not in body` and `"BigInt" in message`, got `{'data': None, 'errors': [{'message': 'An unexpected error occurred.', 'extensions': {'correlationId': ...}}]}`. Two assumptions wrong: Strawberry emits `data: null`, not absent; graphql-core's `ValuesOfCorrectTypeRule` calls `parse_value`, so the scalar's `ValueError` becomes the validation error's `original_error` and the policy masks it. Must-not row: `exact: "9007199254740993"` selects exactly the seeded row. Decorator order: `override_settings` outside `parametrize`, inside `django_db`.

### 9. Wrong tree over the real schema: composition introspection

`apps/products/tests/test_schema.py` ran three queries against the REAL composed schema through `execute_sync`, w/ a 26-line conftest + module-scoped fixture whose only job was rebuilding the schema w/o HTTP (rung 4 while rung 1 was one import away). `apps/library/tests/test_schema.py::test_project_schema_includes_library_types` same shape.

Before:

```python
def test_project_schema_includes_products_types(project_schema):
    """The composed project schema exposes the products app's DjangoTypes."""
    result = project_schema.execute_sync(
        'query { __type(name: "ItemType") { name fields { name } } }',
    )
    assert result.errors is None
    assert {"name", "category", "entries"} <= {f["name"] for f in result.data["__type"]["fields"]}
```

After ([`test_schema_composition_api.py`][test-schema-composition-api]):

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("type_name", "expected_fields"),
    [
        ("ItemType", {"name", "category", "entries"}),
        ("CategoryType", {"name", "description", "items"}),
        ("BookType", {"title", "shelf", "genres"}),
    ],
    ids=["products-item", "products-category", "library-book"],
)
def test_the_composed_schema_publishes_each_apps_types(type_name, expected_fields):
    """One type per contributing app is on the shipped endpoint, with its relation fields.

    A type that never registered introspects as ``null`` here rather than failing
    the request, which is exactly why the absence has to be asserted rather than
    inferred from a green suite.
    """
    data = assert_graphql_success(_TYPE_FIELDS_QUERY, variables={"name": type_name})

    published = data["__type"]
    assert published is not None, type_name
    assert published["name"] == type_name
    assert expected_fields <= {field["name"] for field in published["fields"]}
```

What moved: the schema is the one `config.urls` serves; the bespoke conftest and fixture were deleted outright. `assert published is not None` is the clause the in-process row could not teach: `__type` on a missing name returns `null`, so an unregistered app reads as a passing row unless absence is asserted. Deleting both files changed the tracked set → kanban constants regenerate at commit; three archived specs name the deleted rows (docs prose is outside the citation gate).

### 10. Exception as the observable: misconfigured cap on GET

Before (`tests/test_views.py`): `view._enforce_request_body_limit(RequestFactory().get("/graphql/"))` on a hand-built instance, `pytest.raises(ConfigurationError)`. The docstring claim ("a bad value cannot hide behind a bodyless request") is deployment-observable; only the harness wasn't.

After ([`test_transport_api.py`][test-transport-api], new `cap-misconfigured/` mount w/ `max_request_body_bytes=0` on the file's holder):

```python
    with override_settings(ROOT_URLCONF=__name__):
        client = Client()
        with pytest.raises(ConfigurationError, match="positive int"):
            client.get("/cap-misconfigured/")
        with pytest.raises(ConfigurationError, match="positive int"):
            _post_bytes(client, json.dumps({"query": _TYPENAME}), path="/cap-misconfigured/")
```

What moved: `ConfigurationError` is not an `HTTPException`, upstream `dispatch` does not translate it, `django.test.Client` re-raises it → the live observable is a raised exception, not a status. Works identically on `AsyncClient`. This is RESOLUTION-time validation (per request), so the "construction-time stays package-side" exemption did not apply. Hand-spelled async mounts must carry `@_carrying_the_packages_csrf_mark(AsyncDjangoGraphQLView)` themselves or the CSRF exemption silently drops.

### 11. The manual's own before/after, finished: `totalCount` opt-in

`tests/test_connection.py::test_total_count_present_only_when_opted_in` asserted `"totalCount" in str(schema)` / `not in` on two throwaway types, plus `"A connection to a list of items." in str(bare_schema)`. [Before / after](#before--after-promoting-a-shortcut-test) above covers selection gating on an opted-in type; the ABSENT half on a bare type had no live row.

After ([`test_connection_pagination_api.py`][test-connection-pagination-api]):

```python
    not_opted = graphql_payload("{ allItems(first: 1) { totalCount } }")
    assert any("Cannot query field 'totalCount'" in e["message"] for e in not_opted["errors"])
    assert not_opted.get("data") is None

    opted = assert_graphql_success(
        "{ allLibraryGenresConnection(first: 1) { edges { node { name } } totalCount } }",
    )
    assert len(opted["allLibraryGenresConnection"]["edges"]) == 1
    assert opted["allLibraryGenresConnection"]["totalCount"] == 2
```

`totalCount == 2` beside a one-edge page proves the count is of the whole set, not the window; stronger than `== 0`. The SDL-description clause became its own live row via `__type(name: "ItemTypeConnection") { description }`: generated connection names come from `graphql_type_name`, and only the NON-opted shape keeps the inherited description. `graphql_payload` for the error half, `assert_graphql_success` for the other; one row, because the claim is the contrast.

### 12. The name said two, the body had one: two to-many `orderBy` terms

`tests/orders/test_sets.py::test_orderset_apply_sync_annotates_multiple_to_many_orders` declared throwaway `OrderSet`s, called `apply_sync` directly w/ a fabricated `_make_info()`, and asserted `any(isinstance(agg, Min) for agg in qs.query.annotations.values())`. Its body had ONE to-many term plus a scalar. Shipped `BookOrder` declares `genres` and `loans`, so the live row ([`test_library_api.py`][test-library-api]`::test_library_books_order_by_two_to_many_terms_each_get_their_own_aggregate`) is the first place two to-many terms are exercised:

```python
    titles = [row["title"] for row in data["data"]["allLibraryBooks"]]
    # genre-min ASC primary (Alpha, Alpha, Beta), loan-min ASC tiebreaker inside the Alpha group.
    assert titles == ["Second", "First", "Third"]
    assert len(titles) == len(set(titles))
    book_queries = [e["sql"] for e in captured.captured_queries if "library_book" in e["sql"]]
    assert len(book_queries) == 1, book_queries
    assert book_queries[0].count("MIN(") == 2, book_queries[0]
    assert "DISTINCT" not in book_queries[0].upper(), book_queries[0]
```

Seed makes both terms load-bearing (genre alone can't separate two titles; loan alone gives a different order). `"library_book" in sql` also matches the through-table `library_book_genres`; only safe here because the selection touches no relation. Selecting `genres` → filter on `FROM "library_book"`.

### 13. Direct call to a patch vs a real GET

`tests/test_strawberry_patches.py::test_patched_parse_query_params_parses_object_params` called `patches._patched_parse_query_params(BaseView(), {...})`. Fakeshop's `/graphql/` accepts GET, so ([`test_products_api.py`][test-products-api]):

```python
    response = Client().get("/graphql/", {"query": "{ __typename }", "variables": '{"n": 1}'})
    assert response.status_code == 200
    assert response.json()["data"] == {"__typename": "Query"}
```

Malformed twin: `variables='{not json'` → 400 w/ upstream's parse message. Patch-lifecycle rows (apply idempotence, signature drift) stay package-side; they have no wire shape.

### 14. Shorter promotions, one line each

Same procedure; listed so the shapes are known:

- **Form stale-field revalidation** → `updateItemViaForm` on a row named `REJECTED_ITEM_NAME`, partial update omitting `name`. Field key alone (`["name"]`) can't distinguish "reconstructed then revalidated" from "never bound"; assert the message `["This name is not allowed."]` too, else the boundary mutation leaves the row green.
- **Not-found before any auth signal** → anonymous `updateItem` on a private Item: no top-level error, one `FieldError` on `id`. The permitted-caller arm already existed; this is the anonymous arm, and the ordering claim.
- **Auth before relation decode** → anonymous `createItemViaForm` w/ a private Category's GlobalID: top-level "Not authorized", `data is None`, no in-band `categoryId` error. Mirrors the serializer twin that was already live.
- **Explicit `null` FK on a form update** → error keyed `category` (form field), never `categoryId`. **Omitted required form field** → coercion error, `data is None`, no row.
- **Dangling non-null FK** → `allItems` as staff after a raw-cursor delete under `connection.constraint_checks_disabled()`; message is graphql-core's `Cannot return null for non-nullable field ItemType.category.`, never a descriptor `AttributeError`. Pass-through required: completion errors are masked too. Keep children-before-parents cleanup in `finally`; teardown's `PRAGMA foreign_key_check` runs before rollback. `override_settings` INSIDE the constraint bracket so the PRAGMA is restored last.
- **Relation-seeded `pageInfo` / `last`+`before`** → `allLibraryGenres { booksConnection(...) }`. Root-pipeline twins existed; the per-parent relation-manager pipeline is a different code path, so not redundant. `first: 0` sibling WAS redundant once the live pin gained the missing `endCursor is None` clause.
- **`nodes(ids:)` hidden arm** → fold a `repair` Book into the existing mixed-batch row: same document anonymous → positional `null`; via `_post_graphql_as_staff` → resolves. Proves the null is visibility, not absence, in two lines.
- **Relay id-only projection** → staff `allCategories(first: 5) { edges { node { id } } }`: one `products_category` query, each id equals `global_id_for(CategoryType, pk)`.
- **Cascading-hook target blocks elision** → anonymous `allItems { ... category { id } }`: one `products_item` query, no `JOIN`, two total. Failability boundary = `walker.py::plan_relation`'s downgrade, not the elision guard (see 2).
- **Async multibyte body** → new `AsyncClient` row on `/async-graphql/`; the variable must be USED (`allItems(first: $value)`) or validation reports "never used" before coercion echoes the value. Spell the literal `"café_über"`: ASCII-only `.py` is enforced by the `source-layout` hook, not ruff.
- **List-field introspection** → two more `ofType` levels asserted on the shipped `allLibraryBranchesViaListField` row; needs one more nesting level IN THE DOCUMENT or the new asserts read `None`.

### 15. Deleting duplicates

Read the named live sibling, not its name. Every verdict the package row asserts must be there; missing clause → add it to the live row first (two-assert extension), then delete. Grep the asserted VALUE, not just the row name: a shared leaf (`FieldError` envelope, a codec) is usually re-asserted once per consuming flavour's package file (`tests/utils/test_errors.py` + `tests/mutations/test_resolvers.py` carried the same constraint-envelope claim). Sweep orphans the deletion strands: helpers, module constants, builder kwargs whose only caller was the deleted row (`_build_item_schema(with_entries_connection=...)`, `_DELETE_WITH_CONNECTION`, `_make_asset_model` + four friends). Ruff sees unused imports, not an orphaned `def`; grep each name, count `1` = definition-only. Make the module docstring truthful (drop bullets that named deleted rows; "X is pinned live" + a kept duplicate of X is a contradiction). Grep `docs/` for `::name`; the citation gate reads `.py` + `KANBAN.md` only.

Deleted this sweep, w/ the sibling that covered them: `tests/test_error_policy.py` opt-out + value-completion rows (→ `/ep-off/`, `/ep/` mounts in [`test_error_policy_api.py`][test-error-policy-api]); `tests/extensions/test_debug.py` empty-lists + fresh-per-operation rows; `tests/test_schema.py` four `execute_*` rows (success half everywhere; error half pinned exactly by the policy rows); `tests/test_relay_node_field.py` typed node / mismatch / duplicates / empty (zero-query clause folded into `test_nodes_duplicates_and_empty_live`); `tests/test_connection.py` negative / over-cap / malformed-cursor / first+last-through-schema (keep the classmethod-direct `test_first_and_last_raises_graphql_error`); `tests/test_strawberry_patches.py` two `parse_json` rows after folding `b"3.14"`, `b"false"`, `b'["not", "objects"]'` into the live parametrize lists; eight `tests/mutations/test_resolvers.py` rows, two `tests/mutations/test_permissions.py` rows, nine `tests/forms/test_resolvers.py` rows, one `tests/auth/test_queries.py` row, one `tests/auth/test_mutations.py` row (its non-redundant `PermissionDenied` arm went live, see 5); `tests/types/test_resolvers.py` file/image trio + many-side visibility row; `tests/test_scalars.py` two `strawberry_config` round-trips; `tests/test_list_field.py` non-nullable-outer row; `tests/test_permissions.py` nested-cascade row; `tests/test_relay_connection.py` `first_zero`.

Kept, on purpose: `tests/types/test_resolvers.py::test_async_relations_with_custom_visibility` is reverse-O2O, NOT the async twin of the many-side row it was paired with; deleting it drops a verdict. It is promotable (rung 3 holder w/ a test-local `MembershipCardType` hook) but not a duplicate.

### 16. Trim, don't delete, when one clause survives

`tests/extensions/test_debug.py::test_acknowledged_factory_publishes_the_payload_and_logs_no_warning` → payload half live; kept ONLY no-warning + coordinator-restore, renamed to what it now asserts (`..._restores_the_cursor_bracket_and_logs_no_warning`). `tests/test_relay_node_field.py::test_o1_make_relation_resolver_*` (next sweep): keep the `resolver.__name__` clause, drop the rest. Renaming a trimmed row is mandatory: a name asserting a payload the row no longer reads is a lie on the failure line.

### Gotchas the sweep surfaced

Grouped by where they bite. Each one cost an agent a round trip.

**Error policy**

- Masks exactly the errors whose `original_error` is a real exception: resolver exceptions, custom-scalar VALIDATION errors (`parse_value` runs inside `ValuesOfCorrectTypeRule`), graphql-core's own non-null COMPLETION messages. NOT masked (`original_error is None`): parse / syntax errors, structural validation (`Cannot query field 'totalCount'`, "never used"); those reach the wire verbatim w/o any override. Rule: asserting WHICH message → pass-through only when the error carries an exception; asserting THAT an error happened → never.
- Validation failure → `{"data": null, "errors": [...]}`; `data` is `None`, never absent.

**Optimizer / SQL**

- A plan w/ any `get_queryset` hook in the selection is `cacheable=False`; live cache rows need hook-free types (`allLibraryMembershipCards`), and the shipped instance via `sys.modules["config.schema"]._optimizer` at call time. Absolute `misses == 1` works only because the acceptance conftest rebuilds per test; say so in the docstring.
- Filter captured SQL on `FROM "<table>"` when the selection touches a relation; M2M through-tables share the parent's prefix. Never assert a bare total once a viewer is logged in; session + auth reads ride along.
- Failability mutations get absorbed: a `list`-returning root the optimizer can't plan either way; a guard unreachable behind an earlier downgrade; `model_to_dict(fields=[])` (empty = no filter, fail-open). Mutate at the level you mean to pin: deleting a `Meta` line proves the hint is load-bearing, not that the walker's dispatch is.

**Holder mounts / URLconf**

- Import `config.schema` INSIDE the view function. A schema captured at import is the pre-reload one; it fails in a LATER module on the same worker (`LazyType KeyError` / `DuplicatedTypeName`), not in yours.
- `override_settings(ROOT_URLCONF=...)` and `pytest.mark.urls` already clear resolver caches via `setting_changed`. `clear_url_caches()` only when swapping the held schema w/o changing `ROOT_URLCONF`.
- Function-level `@pytest.mark.urls("config.urls")` reaches the shipped endpoint from inside a holder module.
- `ConfigurationError` at resolution time → `pytest.raises` around `Client().get`; no status code exists for it.
- `_isolate_project_schema_for_acceptance_test` raises `"Reloading the project schema shell mutated app registrations"` when a live module declares a `DjangoType` at import; the message names the fixture, not your file.
- `project_schema_override` is for settings read at schema CONSTRUCTION (`Meta` body); `MEDIA_ROOT` / `DEBUG` / `MIDDLEWARE` are read per request and need only `override_settings`.

**Credentials / settings**

- `_login_with_perm(...)` does NOT seed (`User.objects.get` raises w/o a prior `create_users(N)`); `_staff_client()` seeds itself. Read the helper before assuming.
- `Client()` inside the `MIDDLEWARE` override; capture control envelopes BEFORE an `AUTHENTICATION_BACKENDS` override; sessionless = drop sessions + auth + messages middleware.
- `monkeypatch.setattr` unwinds at teardown, `override_settings` at block exit; put every assertion depending on both inside the `with`.

**Shapes**

- Connections are `edges { node }`; `__type` on a missing name is `null` not an error; introspection depth is a property of the document; generated connection type names via `graphql_type_name`; filter lookups camel-case (`iContains`), and `"__all__"` expands to ~18 lookups per field (dump `str(schema)` and grep the `...FilterInputType` block rather than guess).
- `TestClient().query()` asserts no errors by default; error rows pass `assert_no_errors=False` and read `res.errors` (list of dicts). `assert_graphql_success` asserts `"errors" not in payload`; `graphql_payload` for the envelope.
- A live module's one-sentence docstring feeds [TREE.md][tree-tests]; widening it → re-render, same change.

**Failability loop mechanics**

- Anchors must match exactly once; include leading indentation. Replacement replaces the WHOLE anchor (multi-line anchor → repeat unchanged lines w/ literal `\n`).
- Mutate to a different VALID statement (`raise`, `return int(value)`, `if False:`), never to nothing → `IndentationError` = collection error = invalid count.
- Non-zero exit ≠ proof; collection errors exit non-zero too. Assert exit 1 and expected node count collected.
- Read the per-boundary failing node-id LIST, diff against the rows you expected. The table's count can look healthy while the row you wanted is absent.
- Prove restore by hash (sha256 / `filecmp`), not by "tests pass again".
- Each entry runs the scope twice (baseline + mutated); six entries over two live files ≈ 90s. Don't narrow scope to one node id to save time; the recorded row set is the artifact.

### Second sweep: promotable rows spotted, not yet moved

Work queue, not doctrine: delete a row here when it moves; empty list → delete the heading. Each row was verified by reading and has a live surface today. Same procedure as above.

- `examples/fakeshop/apps/kanban/tests/test_mutations.py`, whole module (11 rows) → rung 4 over the composed schema w/ a `RequestFactory` context; [`test_kanban_mutations_api.py`][test-kanban-mutations-api] has a live twin for every row. Fold first: `card.transitions.filter(...).exists()`, `item.is_complete`, `attempt.outcome_id is None` after open, `attempt.ended_at`, `Decision(card__isnull=True)`, `errors[0]["field"] == "__all__"` on an unknown lookup. Deleting the module → kanban constants + TREE.md.
- `tests/test_routers.py` + `tests/test_consumers.py` (~8k lines, Channels router + WS consumer) → largest fixture gap: fakeshop has no `config/asgi.py`, no WS mount. One rung-2 change moves the whole surface onto a real transport.
- `tests/test_scalars.py` `_parse_bigint` string-rejection family (leading zeroes, empty, whitespace, non-decimal, underscore, leading `+`, unicode digits, `-0`, `None`) → `allScalarSpecimens(filter: {signedBig: {exact: "007"}})` under pass-through; only the bool / float literals are live (example 8).
- `tests/optimizer/test_definition_order.py::test_plan_relation_decisions_match_cardinality_after_finalization` reverse-O2O half → `allLibraryPatrons { card { barcode } }` = `JOIN` in root SQL.
- `tests/test_permissions.py::test_transitive_cascade_two_deep`, `::test_cascaded_traversal_adds_zero_queries`, `::test_cascade_excludes_rows_with_hidden_targets` → shipped `allEntries` / `allItems`; the products types already call `apply_cascade_permissions`.
- `tests/filters/test_inputs.py::test_range_input_type_name_is_scoped_per_filterset` → `ScalarSpecimenFilter` + `NullableScalarSpecimenFilter` already collide on `price`; `__type(name: "...RangeInputType")`. `::test_build_input_fields_hides_deep_multi_hop_flat_relational_when_true` / `::..._keeps_non_relatedfilter_flat_traversal_visible_when_true` → `HIDE_FLAT_FILTERS` rung 2 (`LoanFilterInputType.bookLoansPatronEmail`, `CategoryFilterInputType.itemsName`).
- `tests/types/test_converters.py::test_relation_resolves_to_primary_type_when_target_model_has_multiple` → `__type(name: "ShelfType")` `books: [BookType!]`, not the secondary type.
- `tests/extensions/test_debug.py::test_resolver_owned_atomic_emits_captured_transaction_rows`, `::test_enclosing_transaction_boundary_statements_are_not_captured` → probe mount + real `createItem`, second under `override_settings(ATOMIC_REQUESTS=True)`. `tests/test_resource_policy.py::test_only_the_named_operation_is_charged` → `rp-shape/` + `operationName`.
- `tests/forms/test_resolvers.py::test_explicit_null_m2m_on_update_clears_not_crashes` → `updateBookViaForm(data: {genres: null})`. `tests/orders/test_sets.py::test_resolve_order_expressions_uses_max_for_descending_to_many` → `MAX(` in SQL for a DESC to-many term; `::test_orderset_apply_async_annotates_to_many_order` → async `orderBy` on a to-many (every live async `orderBy` is scalar today).
- `tests/mutations/test_resolvers.py::test_m2m_clear_on_empty_and_unchanged_on_omit`, `::test_m2m_replace_on_provide`, `::test_choice_enum_create_saves_raw_choice_value` → `createBookViaCustomInput` / `updateBookViaCustomInput` create arms (live covers update only). `tests/rest_framework/test_resolvers.py::test_decode_relation_multi_uses_a_single_batched_visibility_query`, `::test_no_m2m_membership_query_runs_before_authorization` → nested serializer writes under `CaptureQueriesContext`.
- `tests/testing/test_relay.py::test_secondary_model_label_emitter_decodes_to_primary` → `global_id_for(PublicPatronType, pk)` into shipped `node(id:)`. `tests/test_connection.py::test_connection_resolver_composition_order` → `allLibraryGenresConnection(first: 1, filter:, orderBy:) { totalCount }` anon vs staff. `tests/middleware/test_debug_toolbar.py::test_get_payload_panel_title_only_when_has_content` → panels JSON over a real POST.
- Duplicates w/ a named stronger live twin, delete after reading: `tests/optimizer/test_definition_order.py::test_plan_relation_downgrades_custom_get_queryset_target_after_finalization`; `tests/optimizer/test_relay_id_projection.py::test_relay_resolve_id_uses_loaded_pk`; five `tests/optimizer/test_single_parent_fetch.py` spec rows (`_accepts_the_plain_first_page`, `_probe_overfetches_one_row`, `_rejects_a_through_table_join`, `test_fetch_returns_none_when_the_setting_is_disabled`, `test_refused_shape_falls_back_to_the_windowed_body`); `tests/optimizer/test_predicates.py::test_count_emits_no_distinct_wrapper`, `::test_row_preservation_direct_m2m`, `::test_same_table_inner_aliasing_from_loan_root`; `tests/test_resource_policy.py` variable-default / value-depth / scalar-byte rows; `tests/test_list_field.py` six `test_normalize_list_arguments_boundary_*`; `tests/test_keyset.py` tampered / foreign-prefix / fingerprint-mismatch / literal-`None` rows; `tests/middleware/test_debug_toolbar.py` two `Content-Length` refresh rows; `tests/test_relay_connection.py::test_synthesized_connection_carries_sidecar_args_and_total_count`; `tests/test_relay_node_field.py::test_node_malformed_id_graphql_error`, `::test_node_hidden_row_returns_null`, `::test_bare_node_field_resolves_model_label_id`; `tests/forms/test_resolvers.py` `perform_mutate` integrity / raw-pk hidden / `to_field_name` / preserves-M2M rows; `tests/orders/test_inputs.py::test_ordering_resolve_nulls_variants`; `tests/filters/test_sets.py::test_apply_sync_nested_related_gate_still_denies`, `::test_apply_sync_raises_graphql_error_on_invalid_input`; `tests/types/test_definition_order.py` two `_survives_strawberry_finalization` rows; `tests/types/test_relay_interfaces.py::test_resolve_nodes_preserves_order_and_missing`; `tests/test_keyset_connection.py::test_keyset_connection_validates_page_sizes_and_sync_count_only`, `::test_bare_keyset_connection_routes_through_keyset_slicer`.

- `tests/test_relay_node_field.py::test_nodes_batches_per_type`, `::test_node_null_paths_issue_equal_queries` → shipped `nodes(ids:)` over `GenreType` + `BookType` w/ per-table captures.
- `tests/test_relay_connection.py::test_synthesized_connection_paginates`, `::test_relation_connection_first_overrun`, `::test_relation_connection_stale_after_no_error`, `::test_relation_connection_first_and_last_rejected`, `::test_relation_connection_has_next_page_when_edges_unrequested` → `booksConnection`, exact root-pipeline twins exist; `::test_default_connection_only_drops_the_reverse_fk_list_sibling` and two siblings → `_introspect_type` instead of `str(schema)`.
- `tests/optimizer/test_extension.py::test_optimizer_hint_force_select_does_not_bypass_custom_get_queryset` → add a `select_related()` hint on `LoanType.book` (target `BookType` has a hook); `::test_optimizer_hint_skip_routes_through_hint_is_skip` → rung 2, second hint spelling on a library type; B5 `dst_optimizer_plan` rows asserting WHICH relations were planned → SQL. `tests/optimizer/test_relay_id_projection.py::test_relay_id_does_not_trigger_lazy_load` → holder w/ `strictness="raise"`.
- `tests/types/test_resolvers.py::test_reverse_one_to_one_scopes_custom_target_by_planned_relation`, `::test_async_relations_with_custom_visibility` → rung 3 holder on `/graphql-async/` w/ a test-local `MembershipCardType` hook; `::test_o1_make_relation_resolver_many_side` / `_forward_returns_attribute` → keep `__name__` clause only; `::test_forward_relation_is_scoped_when_strictness_leaves_it_unplanned` → holder; `::test_runtime_path_from_info_strips_list_indexes_and_keeps_aliases` → misfiled, belongs in `tests/optimizer/test_plans.py`. Four multi-claim rows there carry raw line-number comments (`# ... (lines 510, 548, 601)`), invisible to `check_citations` and banned.
- `tests/test_scalars.py::test_upload_field_resolves_under_strawberry_config_schema` → live `test_media_specimen_input_exposes_upload_over_http` already stronger. `tests/types/test_converters.py::test_big_auto_field_still_maps_to_int` → check `DEFAULT_AUTO_FIELD`; if `BigAutoField`, `ScalarSpecimenType.id` proves it in one introspection line.
- `tests/test_error_policy.py::test_a_malformed_debug_setting_does_not_disable_production_masking` ids `1` / `object()` → `/ep/` under `override_settings(DEBUG=1)`. `tests/extensions/test_debug.py::test_parse_and_validation_failures_have_no_debug_key` (first half live; also two claims), `::test_malformed_debug_setting_stays_fail_closed` (three ids on the existing probe bracket), `::test_sql_row_serializer_forms` (key set + `float` + no `%s` live; keep `> 10s` + executemany).
- `tests/test_schema.py::test_get_extensions_sync_and_async` (`>= 2` cardinality anti-pattern; claim pinned by name in the error-policy install-position row), `::test_get_extensions_with_custom_factory_dedup` (exact duplicate of `test_a_callable_policy_entry_suppresses_the_auto_policy_at_runtime`; the live-observable consequence, one correlation id not two, has no row anywhere).
- `tests/test_views.py::test_the_cap_is_a_no_op_on_get_even_with_a_hostile_content_length` verdict half (GET + `CONTENT_LENGTH: 999999` → 200 on `cap-tiny/`); `::test_a_multipart_request_under_the_declared_gate_is_never_materialized` second half → already live, split the row.
- `tests/mutations/test_resolvers.py::test_delete_snapshot_materializes_relation_before_delete`, `::test_partial_update_constraint_collision_keeps_unprovided_co_member`; `tests/mutations/test_permissions.py::test_under_privileged_create_denied`, `::test_permitted_create_succeeds`, `::test_permission_classes_override_allow_all_lets_anonymous_through` (→ `submitContact`); `tests/forms/test_resolvers.py::test_modelform_update_locates_writes_and_returns`, `::test_modelform_save_integrity_error_maps_to_envelope`, `::test_partial_update_preserves_unprovided_fk_and_validates_constraint`, `::test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`, `::test_decode_split_upload_lands_in_files_never_data`; `tests/test_strawberry_patches.py` null-param / scalar-param / deep-body / deep-param rows → all have named live twins in [`test_products_api.py`][test-products-api].
- `tests/auth/test_mutations.py` backend-order / inactive-via-custom-backend / crash-propagates / weird-credentials / password-never-logged rows → all reachable now that `AUTHENTICATION_BACKENDS` can name a live-module class; `::test_sync_django_http_login_leaves_session_modified_for_the_cookie` consequence half already live.

Fixture gaps (rung 2 work, one fakeshop change each): products `M2M` + a library write mutation (~15 rows in `tests/mutations/test_resolvers.py`); one `on_delete=PROTECT` FK (`test_delete_refused_by_protected_reference_is_envelope_not_graphql_error`); a plain form w/ an observable `perform_mutate` side effect; a custom-pk model (`test_relay_id_with_custom_pk_attname_avoids_lazy_load`); live-unpinned today: empty `name` through `createItem`, plain `{not json` POST body.


## What legitimately stays package-side

Claims w/ no wire shape. Accepted categories + the file showing the docstring discipline:

- **Absence proofs.** Package view imports w/o `channels` = claim about what isn't there; request can't make it. [`tests/test_views.py`][tests-views]; its docstring lists every request-shaped sibling living in [`test_transport_api.py`][test-transport-api].
- **Internal state a response can't show.** Wire `413` identical whether body cap cost one `seek` or a full allocation. Bound only assertable from inside → measurement rows stay in [`tests/test_views.py`][tests-views]; every status code / reason string live.
- **Class-creation-time validation.** `Meta` raising `ConfigurationError` at class creation never reaches a schema. Registry lifecycle, finalizer ordering, duplicate-name rejection, concrete-subclass identity in [`tests/test_connection.py`][tests-connection]. NOT resolution-time configuration: a `ConfigurationError` raised per request (`max_request_body_bytes=0`) is live, as `pytest.raises` around `Client().get` ([example 10](#10-exception-as-the-observable-misconfigured-cap-on-get)).
- **One-declaration-per-process.** `login` / `logout` / `register` declared once per process → permission-gated variant can't coexist w/ fakeshop's `AllowAny` default in one composed schema. [`tests/auth/test_mutations.py`][tests-auth-mutations] pins gated denial strings on isolated throwaway schemas; [`test_auth_api.py`][test-auth-api] owns every consumer-reachable behaviour.
- **Invisible-by-design matrices.** Nine rejected encodings share one status + message on purpose; per-encoding `__cause__` visible only package-side.
- **Soft-dep absence.** `cryptography`, `channels`, `django-debug-toolbar`, `djangorestframework` simulated absent via [`tests/_soft_dependency.py`][tests-soft-dep] (`sys.modules[name] = None`). Never patch `builtins.__import__`; guards use `importlib.import_module`, patched import silently passes.

Same discipline every case: package docstring says what it keeps, why no live request can express it, names the live sibling. Unsure whether a claim has a wire shape → try writing the live row. Don't argue.

## Isolation contract

`config/schema.py` composes every app's `Query`/`Mutation` into one `DjangoSchema`, `finalize_django_types()`, mounts a module-level `DjangoOptimizerExtension` singleton. `tests/` clears the global registry for its own isolation. Partial reload after a clear = classic order-dependent failure: reload one app → other apps' types gone → composed build raises `LazyType` `KeyError` or `DuplicatedTypeName` depending on what the previous worker left in `sys.modules`.

Single-sited in [`schema_reload.py`][schema-reload], applied by [`conftest.py`][conftest] at two levels:

- **Once per module per worker**: `_reload_project_schema_for_acceptance_tests` clears registry, reloads every `apps.<app>.schema` dependency-safe (`glossary` before `kanban`; `CardGlossaryTermType.term` FKs into glossary), then `config.schema` + `config.urls`.
- **Before every test**: `_isolate_project_schema_for_acceptance_test` rebuilds only `config.schema` + `config.urls` → fresh Strawberry schema, optimizer, URLconf; finalized types reused. Fingerprints every registry map + app module first; test mutated registration → teardown runs the full rebuild, incl. after assertion failure.
- **On request**: `project_schema_override` = the full-rebuild callable, for re-finalizing under `override_settings` when the setting is read at schema CONSTRUCTION (a `Meta` body, `FAKESHOP_TEST_LOAN_CONNECTION`); function guard restores default after. Settings read per request (`MEDIA_ROOT`, `DEBUG`, `MIDDLEWARE`, `AUTHENTICATION_BACKENDS`) need only `override_settings`; the per-test rebuild suffices.

No other tree rebuilds the aggregate. `apps/<app>/tests/` never composes the project schema; a test needing it is a live row here.

Adding an app → add to `_PROJECT_APP_SCHEMA_MODULES` in [`schema_reload.py`][schema-reload] + grep whole test tree for other private module lists. Order independence is a contract; invisible under `-n0` / single module; verify w/ full parallel sweep.

## Clients, transports, credentials

[`graphql_client.py`][graphql-client] helpers = default for every ordinary JSON row. Exemptions stated in the exempt module's docstring, never inferred.

- **Raw envelope.** `post_graphql_raw` = bare `client.post` for malformed bodies / content-type negotiation, where the body IS the subject and the client's builder would replace it. [`test_transport_api.py`][test-transport-api] = raw-envelope resident: hostile `Host`, `secure=` / `enforce_csrf_checks=` clients, in-process `ASGIHandler` for fragmented bodies, real multipart control fields.
- **Async.** [`test_list_field_async_api.py`][test-list-field-async-api], [`test_relations_async_api.py`][test-relations-async-api]: `django.test.AsyncClient` vs an `AsyncDjangoGraphQLView` mount. Async rows: `@pytest.mark.django_db(transaction=True)`, declare the helper exemption, rely on [`tests/conftest.py`][tests-conftest] to close per-task SQLite connections (else `ResourceWarning` = error here).
- **Multipart.** `TestClient().query(..., files={"data.attachment": SimpleUploadedFile(...)})`, path-keyed variables; [`test_uploads_api.py`][test-uploads-api] w/ `tmp_path` `MEDIA_ROOT`. GraphiQL can't; live tier = only end-to-end proof of the upload path.
- **Credentials.** `Client().force_login(user)` on a `create_users` user; `TestClient.login(user)` = bracket that logs out even on raise; `Client(enforce_csrf_checks=True)` when CSRF is the claim (Django test client skips CSRF by default). `login` mutation is a SUBJECT only in [`test_auth_api.py`][test-auth-api]; everywhere else `force_login`.
- **DEBUG-gated detail.** pytest-django forces `DEBUG=False`. The production policy replaces any message whose `original_error` is a real exception: resolver exceptions, custom-scalar validation errors (`parse_value` runs inside validation), graphql-core's own non-null completion messages. Parse / syntax / structural-validation errors carry none and travel verbatim. Row asserting one of the masked messages → override `DEBUG=True` AND drop toolbar middleware from `MIDDLEWARE` in the same override: fakeshop wires debug-toolbar behind `DEBUG`, toolbar would inject a panel against `djdt` routes the URLconf never computed. Copy `_ERROR_POLICY_PASS_THROUGH` from [`test_products_api.py`][test-products-api]. Row asserting only THAT an error happened → no override; assert `data is None` (never absent) + `errors` present.
- **Credential helpers differ.** `_login_with_perm(...)` does NOT seed (needs `create_users(N)` first); `_staff_client()` seeds itself. `Client()` constructed INSIDE a `MIDDLEWARE` override (handler caches its chain on first request); control envelope captured BEFORE an `AUTHENTICATION_BACKENDS` override; a live module's class is a valid settings string (`"test_auth_api.PermissionDeniedBackend"`, `test_query/` is on `pythonpath`).
- **Test client family** covered both sides: [`test_client_api.py`][test-client-api] posts real ops through `TestClient` / `AsyncTestClient` / `GraphQLTestCase` / `GraphQLTransactionTestCase`; DB-free mechanics in [`tests/testing/test_client.py`][tests-testing-client]. Consumer usage: [docs/README.md][docs-readme-testing].

## Environment tiers

Two knobs, mutually exclusive, un-skip their tiers. Neither runs under bare `uv run pytest`.

**Sharded.** `FAKESHOP_SHARDED=1` adds `shard_b` on `db_shard_b.sqlite3` beside `default`. Sharded module gates at import: `pytest.skip(..., allow_module_level=True)` on the env var, NEVER `pytest.mark.skipif` (var changes `DATABASES` at settings import; mark evaluates too late). Each test `@pytest.mark.django_db(databases=["default", "shard_b"])` or pytest-django blocks the alias. Seed the full non-null chain on each alias read. Reference: [`test_multi_db.py`][test-multi-db]: `.using("shard_b")` keeps its correlated `EXISTS` on `shard_b`, no `library_loan` SQL on `default`, proven by capturing both aliases.

**Postgres.** `FAKESHOP_PG_DSN=postgres://...` → `default` = Postgres, un-skips `@pytest.mark.pg` (registered in `pytest.ini`, auto-skipped elsewhere by repo-root `conftest.py`). Launch `uv run --group pg pytest` (group pinned for the run). PG surfaces pk-magnitude bugs SQLite hides: per-test SQLite pks stay single-digit forever, PG sequences never rewind. PG row failing order-dependently but passing alone = pk-magnitude bug before pollution; repro `ALTER SEQUENCE ... RESTART WITH <big>` in one test.

## Prove the test can fail

Passing suite = evidence only if it could have failed. Every new boundary owes one loop: remove boundary → run the rows claiming to pin it → record failing node ids → restore → prove restore by byte compare. [`prove_failability.py`][prove-failability] mechanizes it from a manifest; refuses `-x` / `--maxfail` (cut run can't fail rows after the cut); collection error or odd exit code = invalid count, never zero. Method + recording rules: [BUILD.md][build-failability].

- **Uncovered line = claim nobody tested.** Read the claim first. Line may be uncovered because its reasoning is wrong; a blessing test locks the defect in.
- **Never paper over**: no `pragma: no cover`, no test-only fix, no follow-up card. Line a real fakeshop query can't reach = smell in prod code (too-clever branch, wrong abstraction). Fix the abstraction. `pragma: no cover` only for branches the runner structurally cannot execute.
- **Statement coverage can't see fail-open expressions.** `max(x, 0)`, `getattr(obj, name, default)`, `x or fallback`, broad `except` read covered once the happy path runs. Find by reading; BUILD.md "Fail-open shapes" lists them.
- **Two outcomes are not verdicts.** GREEN after the mutation = the mutation did not remove the boundary (reachable through another surface, absorbed by an earlier branch, itself fail-open) → re-aim; says nothing about the row. Collection ERROR = the mutation broke the build, not the claim → invalid count. Smallest mutation that changes one published fact: `Meta.name` rename to unpublish a type; one scalar dropped from `Meta.fields` that no `FilterSet` / `OrderSet` / `relation_shapes` entry names; one operand in package source; always a different VALID statement, never nothing.
- **Read the failing node-id list, not the count.** Diff it against the rows you expected to fail; a healthy count can hide the one row that survived. The survivor's docstring is naming a boundary it doesn't pin ([example 7](#7-the-stand-ins-docstring-lied-corrupt-image)).
- **Guarded twice in series = no single-site mutation fails it.** A plan-time refusal plus a fetch-time fail-closed arm each hide the other's removal; `prove_failability.py` (one contiguous anchor per entry) can't express the conjunction. Record the pair by hand (both sites, one restore loop, hash-verified), name both sites in the live row's docstring, and KEEP the package unit row for the half w/ no independent wire shape; it is not a stand-in (`tests/optimizer/test_single_parent_fetch.py::test_spec_rejects_a_keyset_seek`).
- **Concurrently dirty tree.** The script snapshots a file at entry start and restores it at entry end; a concurrent edit to that file inside the window is silently reverted. `git status` the files you will mutate first; loop only over files nobody else is editing, or coordinate.

## Test code style

Production rules unchanged: ASCII-only `.py`, trailing-comma explosion at 4, `path::Symbol` never line numbers, line 99. Plus:

- **Docstring = invariant.** What must hold, and why when it helps. May cite spec decision (`spec-043 Decision 3`), glossary anchor, upstream ticket. Never process provenance: no severity labels, review-round / worker attribution, slice numbers, "previously", "as of 0.0.N". Removed provenance carried the WHY → restate as a clause about the code.
- **Name = observable claim.** `test_genre_connection_total_count_omitted_no_count` tells the reader from the failure line. `test_spec_030_case_4d` doesn't.
- **Failing assertion carries the payload.** `assert "errors" not in payload, payload`.
- **Seeding rules absolute.** `seed_data(N)` / `create_users(N)` first for products/auth; inline `Model.objects.create` for library; seed helpers' own tests = only exception.
- **Expected values derived, not memorized.** Faker → compute from ORM. Package-owned encodings (GlobalIDs, cursors) → mint w/ package helpers.
- **Format after every edit, stop.** `uv run ruff format .` then `uv run ruff check --fix .`. No `pytest` after edits unless asked; asked → `uv run pytest`; single test `uv run pytest -n0 path/to/test_file.py::test_name`.
- **New / deleted test file changes the tracked set.** After staging: `uv run python scripts/build_kanban_tracked_path_constants.py`, stage regenerated `examples/fakeshop/apps/kanban/constants.py` with it, else the hook rejects every later commit until a constants-only sync. Also re-render [TREE.md][tree-tests] (`uv run python scripts/build_tree_md.py`): one row per test module, a deleted module strands its row and the citation gate can't see it.
- **Removing code sweeps all four trees** for orphan imports / fixtures / helpers / builder kwargs, same change; ruff catches imports only. Then `grep -rn '::<name>' docs/` for stranded prose citations.
- **Trimmed row = renamed row.** Keep one clause of a multi-claim test → rename it to that clause; a name asserting a payload the row no longer reads lies on the failure line.

## Checklist

1. Claim covered from the highest reachable rung; any lower-rung test's docstring says why not higher + names live sibling.
2. Acceptance AND rejection each have a row.
3. No loop in a test body; every case own node id w/ `ids=`.
4. Seeding per app rule; a must-not-match row present; list assertions carry `orderBy:`.
5. Payload exact where data allows; SQL filtered to the table under test.
6. Identifiers / cursors minted, never pinned.
7. Promoted shortcut deleted; live row shown to fail w/ boundary removed; failing node ids read, not counted; orphans + `docs/` citations swept.
8. Scoped claim carries its must-not (same caller reads, adjacent surface, other verdict).
9. Async rows `django_db(transaction=True)`; sharded rows gate at module level + declare both aliases.
10. Module docstring one sentence (TREE.md re-rendered if changed); test docstrings no provenance; stand-in's claim verified against code before it was copied.
11. Message asserted → pass-through override present; error asserted → `data is None`, not absent.
12. `uv run ruff format .`, `uv run ruff check --fix .`, `uvx pre-commit run --files <paths>`; test file added / removed → kanban constants regenerated AND TREE.md re-rendered.

## Suite map

Module docstring = authoritative description; this = index. Read the docstring before adding a row: the suite owning the surface receives the case.

| Suite | Owns |
|---|---|
| [`test_library_api.py`][test-library-api] | Acceptance app end to end: FK / reverse FK / O2O / M2M traversal, choice enums, nullable scalars, optimizer SQL shape + hints, shipped plan cache reused across HTTP requests, consumer relation overrides, `filter:` / `orderBy:`, row-preserving correlated `EXISTS` for deep relational predicates, mixed direct/relational `OR` oracle over the seeded loan graph, flag-gated `allLibraryLoansConnection` proof, GlobalID rejection codes, genre-connection pagination + `totalCount` gating, relation-seeded `booksConnection` `pageInfo` + `last`/`before`, two to-many `orderBy` terms each w/ own aggregate. |
| [`test_products_api.py`][test-products-api] | Canonical consumer app: connection reads, all three mutation flavours, `DjangoModelPermission`, per-field filter permission gate, own-pk GlobalID filtering, `RelatedFilter` traversal, not-found-before-auth on hidden rows, private-row refetch after an authorized write, form stale-field revalidation, GET object / malformed `variables` params, dangling non-null FK, sync strict-UTF-8 rows, the DEBUG pass-through idiom. |
| [`test_products_visibility_api.py`][test-products-visibility-api] | Generated relations enforce target visibility themselves; sync + async mounts, holder schema; optimizer-less nested connection costs `1 + N`; Relay id-only page in one query; cascading-hook target blocks FK-id elision. |
| [`test_relations_async_api.py`][test-relations-async-api] | Generated relations lazy-load from async w/o `DJANGO_ALLOW_ASYNC_UNSAFE`. |
| [`test_scalars_api.py`][test-scalars-api], [`test_scalars_filter_api.py`][test-scalars-filter-api] | One specimen row per scalar wire format; scalar filtering / ordering / related querysets, out-of-range `__in` member drop, `BigInt` bool / float literal rejection. |
| [`test_uploads_api.py`][test-uploads-api] | `Upload` over multipart: file / image output objects, filesystem-path opt-in, model + form write paths, storage degradation (unpathable backend, vanished file, corrupt image, `SuspiciousFileOperation` not swallowed). |
| [`test_auth_api.py`][test-auth-api] | `login` / `logout` / `register` / `me` on the shipped `AllowAny` surface: session rotation branches, collapsed failure envelope incl. backend `PermissionDenied`, password validators, non-string `username` rejected at validation, sessionless middleware stack refused by name. |
| [`test_keyset_api.py`][test-keyset-api] | `Meta.cursor_field` keyset pagination: value cursors surviving inserts / deletes, nested uniform seeks, tamper rejection, permission-aware replay, cursor survives `SECRET_KEY` rotation via `SECRET_KEY_FALLBACKS`. |
| [`test_connection_pagination_api.py`][test-connection-pagination-api] | Pagination error containment on connections; `Meta.connection` `totalCount` opt-in gating + inherited connection SDL description. |
| [`test_list_field_api.py`][test-list-field-api] | Sync `DjangoListField` argument surface: ordered offset pages, visibility before order, cap + error matrix, converter naming, malformed post-`OrderSet` result matrix (each row = exact rejection + query cost), hostile normalized-term rejection, legacy-reference byte-parity oracle under the same field name, consumer-context isolation for list field + ordered connection. |
| [`test_list_field_async_api.py`][test-list-field-async-api] | Async colour of the same: safe queryset completion, optimizer preservation, iterable cleanup, async-only malformed shapes (non-awaitable result, residual awaitable), published-name reporting, post-`OrderSet` routing pin, consumer-context rows. |
| [`test_optimizer_auto_api.py`][test-optimizer-auto-api], [`test_single_parent_fastpath_api.py`][test-single-parent-fastpath-api] | Nested-fetch strategy selection; single-parent windowed-prefetch fast path incl. the keyset-seek page keeping its window. |
| [`test_multi_db.py`][test-multi-db] | Behind `FAKESHOP_SHARDED=1`: resolver isolation on `shard_b`, correlated `EXISTS` pinned to `queryset.db`, post-`OrderSet` routing attestation (four rejections + the accepted identity-preserving row), multi-DB debug capture. |
| [`test_transport_api.py`][test-transport-api] | Transport boundary: middleware, security headers, hostile `Host`, CSRF directions, `Vary`, exact routing, per-mount IDE / GET controls, cumulative request-body cap across sync / async / multipart, misconfigured cap fails on GET too, async + multipart strict-UTF-8 rows. |
| [`test_error_policy_api.py`][test-error-policy-api] | Production error policy over the wire. |
| [`test_schema_composition_api.py`][test-schema-composition-api] | Composed project schema over HTTP: one type per contributing app by introspection, reverse relation resolved under the anonymous cascade. |
| [`test_resource_policy_api.py`][test-resource-policy-api] | Every `ResourcePolicy` bound, against mounts each narrowing one family of bounds; malformed document keeps the parser's own diagnostic / is rejected on size first; sync/async parity row; streamed multipart rows. |
| [`test_debug_extension_api.py`][test-debug-extension-api], [`test_debug_toolbar_api.py`][test-debug-toolbar-api] | `DjangoDebugExtension` on a probe mount; `DebugToolbarMiddleware` across GraphQL / panel / pass-through routes under `DEBUG=True` override. |
| [`test_mutation_atomicity.py`][test-mutation-atomicity] | Generated mutation's transaction spans response completion: unserializable payload → rollback, not commit behind `data: null`. |
| [`test_client_api.py`][test-client-api] | Request-driving half of the `TestClient` family's coverage. |
| [`test_kanban_api.py`][test-kanban-api], [`test_kanban_mutations_api.py`][test-kanban-mutations-api], [`test_glossary_api.py`][test-glossary-api] | Docs-as-data apps' read + write surfaces. |

Outside this dir: [`../tests/`][fakeshop-tests] = project-level rows (urls, settings guard, schema export, `inspect_django_type`); `../apps/<app>/tests/` = that app's in-process rows; [`../../../tests/`][tests-dir] = package tier, one file per module.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[contributing]: ../../../CONTRIBUTING.md
[start]: ../../../START.md

<!-- docs/ -->
[docs-readme-testing]: ../../../docs/README.md#testing-graphql-endpoints
[glossary-testclient]: ../../../docs/GLOSSARY.md#testclient
[tree-tests]: ../../../docs/TREE.md#test-layout

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-failability]: ../../../docs/builder/BUILD.md#failability-proofs-prove-the-test-can-fail

<!-- django_strawberry_framework/ -->
[testing-relay]: ../../../django_strawberry_framework/testing/relay.py

<!-- tests/ -->
[tests-auth-mutations]: ../../../tests/auth/test_mutations.py
[tests-conftest]: ../../../tests/conftest.py
[tests-connection]: ../../../tests/test_connection.py
[tests-dir]: ../../../tests/
[tests-soft-dep]: ../../../tests/_soft_dependency.py
[tests-testing-client]: ../../../tests/testing/test_client.py
[tests-views]: ../../../tests/test_views.py

<!-- examples/ -->
[conftest]: conftest.py
[fakeshop-readme]: ../README.md
[fakeshop-tests]: ../tests/
[graphql-client]: ../graphql_client.py
[lib-schema]: ../apps/library/schema.py
[products-services]: ../apps/products/services.py
[schema-reload]: ../schema_reload.py
[test-auth-api]: test_auth_api.py
[test-client-api]: test_client_api.py
[test-connection-pagination-api]: test_connection_pagination_api.py
[test-debug-extension-api]: test_debug_extension_api.py
[test-debug-toolbar-api]: test_debug_toolbar_api.py
[test-error-policy-api]: test_error_policy_api.py
[test-glossary-api]: test_glossary_api.py
[test-kanban-api]: test_kanban_api.py
[test-kanban-mutations-api]: test_kanban_mutations_api.py
[test-keyset-api]: test_keyset_api.py
[test-library-api]: test_library_api.py
[test-list-field-api]: test_list_field_api.py
[test-list-field-async-api]: test_list_field_async_api.py
[test-multi-db]: test_multi_db.py
[test-mutation-atomicity]: test_mutation_atomicity.py
[test-optimizer-auto-api]: test_optimizer_auto_api.py
[test-products-api]: test_products_api.py
[test-products-visibility-api]: test_products_visibility_api.py
[test-relations-async-api]: test_relations_async_api.py
[test-resource-policy-api]: test_resource_policy_api.py
[test-scalars-api]: test_scalars_api.py
[test-scalars-filter-api]: test_scalars_filter_api.py
[test-schema-composition-api]: test_schema_composition_api.py
[test-single-parent-fastpath-api]: test_single_parent_fastpath_api.py
[test-transport-api]: test_transport_api.py
[test-uploads-api]: test_uploads_api.py

<!-- scripts/ -->
[prove-failability]: ../../../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->
