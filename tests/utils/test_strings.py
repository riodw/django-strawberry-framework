"""String utility tests for snake/camel/Pascal case conversion and Django lookup-path flattening."""

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.strings import (
    flatten_lookup_path,
    graphql_camel_name,
    pascal_case,
    pascal_case_or_raise,
    snake_case,
)


class _HostileString(str):
    """A string subclass whose ordinary operations cannot be trusted."""

    def __hash__(self):
        raise RuntimeError("hostile hash")

    def split(self, *args, **kwargs):
        raise RuntimeError("hostile split")

    def replace(self, *args, **kwargs):
        raise RuntimeError("hostile replace")

    def __str__(self):
        raise RuntimeError("hostile string")


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
        "a_a_a",
        "trailing_",
        "__x_foo",
        "___x_foo",
        "__x_a",
        "__x_1",
        "__x_y_z",
        "a_x",
        "x_a",
        "a__x",
        "a__x_a",
        "a__xa",
        "a__b__c",
        "a__b_c",
        "a_b__c",
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
    """LOOKUP_SEP never survives into a generated identifier."""
    assert flatten_lookup_path("name") == "name"
    assert flatten_lookup_path("category__name") == "category_name"
    assert flatten_lookup_path("entries__property__category__name") == (
        "entries_property_category_name"
    )
    assert flatten_lookup_path("a____b") == "a_b"
    assert flatten_lookup_path("a____b") == flatten_lookup_path(flatten_lookup_path("a____b"))


def test_string_helpers_normalize_hostile_string_subclasses():
    """Hostile subclass overrides cannot escape through helper internals."""
    assert snake_case(_HostileString("isPrivate")) == "is_private"
    assert pascal_case(_HostileString("is_private")) == "IsPrivate"
    assert graphql_camel_name(_HostileString("is_private")) == "isPrivate"
    assert flatten_lookup_path(_HostileString("category__name")) == "category_name"


def test_graphql_camel_name_escapes_adjacent_uppercase_segments():
    """Adjacent one-letter snake segments keep a reversible separator marker."""
    assert graphql_camel_name("a_a_a") == "aA__xA"
    assert snake_case(graphql_camel_name("a_a_a")) == "a_a_a"
    assert snake_case("aA__xA") != snake_case("aAA")


def test_snake_case_distinguishes_x_token_from_adjacent_uppercase_escape():
    """__x only functions as an adjacent-segment escape after an uppercase character."""
    # After an uppercase segment, __x is the adjacent one-letter separator
    assert snake_case("aA__xA") == "a_a_a"
    assert snake_case("fooX__xBar") == "foo_x_bar"

    # At start or after leading underscores, __x is literal and not an escape
    assert snake_case("__xFoo") == "__x_foo"
    assert snake_case("___xFoo") == "___x_foo"
    assert snake_case("__xA") == "__x_a"


def test_pascal_case_or_raise_raises_on_empty_and_delegates_on_valid():
    """pascal_case_or_raise validates non-empty tokens and returns PascalCase."""
    assert (
        pascal_case_or_raise(
            "category_name",
            make_error=lambda n: ValueError(f"empty name: {n}"),
        )
        == "CategoryName"
    )

    with pytest.raises(ValueError, match="empty name: _"):
        pascal_case_or_raise(
            "_",
            make_error=lambda n: ValueError(f"empty name: {n}"),
        )


@pytest.mark.parametrize(
    "helper",
    [
        snake_case,
        pascal_case,
        graphql_camel_name,
        flatten_lookup_path,
    ],
)
def test_string_helpers_reject_non_string_inputs(helper):
    """Malformed helper inputs fail with the package's typed configuration error."""
    with pytest.raises(ConfigurationError, match="must be a string"):
        helper(42)


def test_snake_case_preserves_lru_cache_controls():
    """The normalization boundary keeps the historical cache-control surface."""
    snake_case.cache_clear()
    assert snake_case.cache_parameters() == {"maxsize": 2048, "typed": False}
    before = snake_case.cache_info()

    assert snake_case("isPrivate") == "is_private"
    after_miss = snake_case.cache_info()
    assert after_miss.misses == before.misses + 1

    assert snake_case("isPrivate") == "is_private"
    after_hit = snake_case.cache_info()
    assert after_hit.hits == after_miss.hits + 1
    assert snake_case.__wrapped__("isPrivate") == "is_private"
