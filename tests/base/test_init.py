"""Tests for the django_strawberry_framework package init."""

from django_strawberry_framework import __version__


def test_version():
    assert __version__ == "0.0.3"
