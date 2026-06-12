"""String utility tests for snake_case, camelCase, and PascalCase conversion."""

from django_strawberry_framework.utils.strings import pascal_case, snake_case


def test_snake_case_round_trips_camel_case():
    assert snake_case("name") == "name"
    assert snake_case("isPrivate") == "is_private"
    assert snake_case("createdDate") == "created_date"


def test_pascal_case_handles_snake_case_inputs():
    assert pascal_case("status") == "Status"
    assert pascal_case("is_active") == "IsActive"
    assert pascal_case("payment_method") == "PaymentMethod"
    # Adjacent / leading / trailing underscores collapse to nothing.
    assert pascal_case("_leading") == "Leading"
    assert pascal_case("trailing_") == "Trailing"
    assert pascal_case("double__underscore") == "DoubleUnderscore"


def test_pascal_case_empty_output_edges():
    # Pin the silent-empty contract: every segment filtered out by ``if part``
    # collapses to ``""``.  Unreachable through the documented call chain
    # (Django field names are never empty and never ``"_"``); pinning prevents
    # a future filter "fix" from silently changing generated enum names.
    assert pascal_case("") == ""
    assert pascal_case("_") == ""
