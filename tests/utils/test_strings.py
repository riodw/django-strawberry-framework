"""Tests for ``django_strawberry_framework.utils.strings``."""

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
