"""Django app config for unmanaged cardinality fixture models."""

from django.apps import AppConfig


class TestsCardinalityConfig(AppConfig):
    """Test-only app that lets Django expose reverse fixture relations."""

    name = "tests.fixtures"
    label = "tests_cardinality"
    verbose_name = "Tests Cardinality Fixtures"
