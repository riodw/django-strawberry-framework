"""Library schema tests for in-process GraphQL execution without HTTP.

Type exposure is checked through the composed project schema; the intentionally
cross-referenced declaration order is pinned against the library schema module
directly (self-contained). The live HTTP counterpart lives in
``examples/fakeshop/test_query``.
"""

from config.schema import schema as project_schema

from apps.library import schema as library_schema
from django_strawberry_framework import DjangoType


def test_project_schema_includes_library_types():
    """The composed project schema exposes the library app's DjangoTypes."""
    result = project_schema.execute_sync(
        """
        query {
          __type(name: "BookType") {
            name
            fields { name }
          }
        }
        """,
    )

    assert result.errors is None
    assert result.data["__type"]["name"] == "BookType"
    assert {"title", "shelf", "genres"} <= {
        field["name"] for field in result.data["__type"]["fields"]
    }


def test_library_djangotype_declaration_order_stays_awkward():
    """Pin the real app's intentionally cross-referenced declaration order."""
    declaration_order = [
        name
        for name, value in vars(library_schema).items()
        if isinstance(value, type) and issubclass(value, DjangoType) and value is not DjangoType
    ]

    assert declaration_order.index("LoanType") < declaration_order.index("BookType")
    assert declaration_order.index("LoanType") < declaration_order.index("PatronType")
    assert declaration_order.index("ShelfType") < declaration_order.index("BranchType")
    assert declaration_order.index("MembershipCardType") < declaration_order.index("PatronType")
