"""String utility tests for snake/camel/Pascal case conversion and Django lookup-path flattening."""

import pytest

from django_strawberry_framework.utils.strings import (
    flatten_lookup_path,
    graphql_camel_name,
    pascal_case,
    snake_case,
)


def test_snake_case_round_trips_camel_case():
    assert snake_case("name") == "name"
    assert snake_case("isPrivate") == "is_private"
    assert snake_case("createdDate") == "created_date"


@pytest.mark.parametrize(
    ("camel", "snake"),
    [
        ("HTTPServer", "http_server"),
        ("HTTPServer2API", "http_server2_api"),
        ("field2Value", "field2_value"),
        ("_legacyId", "_legacy_id"),
        ("double_Underscore", "double__underscore"),
        ("trailing_", "trailing_"),
    ],
)
def test_snake_case_pins_acronym_digit_and_underscore_edges(camel, snake):
    assert snake_case(camel) == snake


@pytest.mark.parametrize(
    "name",
    [
        "http_server",
        "field2",
        "field2_value",
        "field_2",
        "version_2_value",
        "_legacy_id",
        "double__underscore",
        "trailing_",
    ],
)
def test_graphql_camel_name_round_trips_normalized_snake_case(name):
    assert snake_case(graphql_camel_name(name)) == name


def test_pascal_case_handles_snake_case_inputs():
    assert pascal_case("status") == "Status"
    assert pascal_case("is_active") == "IsActive"
    assert pascal_case("payment_method") == "PaymentMethod"
    assert pascal_case("http_server") == "HttpServer"
    assert pascal_case("http2_server") == "Http2Server"
    assert pascal_case("field2") == "Field2"
    # Underscore-before-digit is retained so ``field_2`` / ``field2`` stay distinct
    # GraphQL type-name stems (operator bags, range inputs, choice enums).
    assert pascal_case("field_2") == "Field_2"
    assert pascal_case("my_HTTP_response") == "MyHttpResponse"
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


def test_flatten_lookup_path_flattens_every_lookup_sep():
    """LOOKUP_SEP never survives into a generated identifier (DRY review A9)."""
    assert flatten_lookup_path("name") == "name"
    assert flatten_lookup_path("category__name") == "category_name"
    assert flatten_lookup_path("entries__property__category__name") == (
        "entries_property_category_name"
    )
