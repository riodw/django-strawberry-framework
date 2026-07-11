"""Planning anchors for spec-044 live DjangoDebugExtension HTTP tests."""

# TODO(spec-044 Slice 1): Replace these anchors only after the production
# extension and Strawberry >=0.316.0 floor land. Do not run pytest unless the
# maintainer explicitly asks.
#
# Module/probe URLconf pseudocode:
# - Apply pytestmark = pytest.mark.urls(__name__) once for the whole module.
# - Keep exactly one mutable schema holder, one Strawberry Django view, and
#   one module-level urlpatterns entry for /graphql/.
# - The view reads the current schema from the holder so fixtures can swap
#   debug-only, optimizer+debug, no-debug, and raising-field schemas without
#   duplicating URLconf plumbing.
# - Depend on the acceptance suite's
#   _reload_project_schema_for_acceptance_tests fixture. Import fakeshop app
#   Query/Mutation types inside the schema fixture only after reload.
# - Run finalize_django_types() before each probe strawberry.Schema build.
# - Keep one module-local DjangoOptimizerExtension() singleton and expose it
#   as lambda: _optimizer beside DjangoDebugExtension as the class. Never sort
#   or normalize the extensions list: order is a tested contract.
# - Post through django_strawberry_framework.testing.TestClient. Use
#   assert_no_errors=False only in expected-error scenarios.
# - A small _debug(response) accessor may validate and return
#   (response.extensions or {})["debug"] for executed-operation happy paths;
#   absence tests inspect the envelope directly.
#
# Live HTTP behavior pseudocode:
# 1. DEBUG-independent query capture:
#    - assert settings.DEBUG is False before setup
#    - seed_data(1) as the first domain-setup action
#    - post a products connection selection
#    - assert response data remains correct
#    - find the first row whose literal "isSelect" is True
#    - assert vendor == connection.vendor, alias == "default", SQL contains
#      SELECT, duration is float, isSlow is False, isSelect is True
#    - assert exceptions == []
#    - filter by row semantics; never assert raw count or positional index
#      because transaction rows are in contract
# 2. Optimizer composition:
#    - seed_data(2)
#    - build extensions=[lambda: _optimizer, DjangoDebugExtension]
#    - select nested item/category fields through the products connection
#    - filter captured rows to SELECT rows and assert the optimizer's joined
#      single-query shape rather than N+1
#    - assert SQL shows the projected/joined columns that make the debug
#      payload an optimizer observability surface
# 3. Mutation capture:
#    - create_users(1), choose only the user with the required add permission,
#      and authenticate via `with client.login(user):`
#    - post createItem
#    - assert an INSERT row with isSelect False is present
#    - tolerate/select by prefix around pipeline SELECT and transaction rows
# 4. Resolver execution exception:
#    - add one probe field that raises ZeroDivisionError
#    - post with assert_no_errors=False
#    - assert the ordinary GraphQL errors remain present
#    - assert exactly one debug exception with the literal excType,
#      message, and a stack containing "Traceback"
#    - assert sql exists independently and may be empty
# 5. Validation versus execution boundary:
#    - unknown field: errors present and "debug" absent from extensions
#    - non-null probe returning None: execution happened, so "debug" is
#      present and the completion error contributes an exception row
# 6. No-SQL operation:
#    - post `{ __typename }`
#    - assert debug equals exactly {"sql": [], "exceptions": []}
# 7. Off by default:
#    - swap in the otherwise-equivalent schema without the debug class
#    - post the same operation
#    - assert no "debug" key and no unrelated envelope widening
#
# DRY/test-placement constraints:
# - Reuse seed_data/create_users; do not hand-build product or auth rows.
# - Reuse the shared schema reload fixture; no local registry clearing or
#   copied module-reload list.
# - This file owns only request-visible behavior. Serializer/coordinator,
#   merge-precedence, async overlap, masking order, and nested-reentrancy
#   mechanics belong in tests/extensions/test_debug.py.
