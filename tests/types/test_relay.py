"""Tests for Relay helper module import coverage."""

import importlib


def test_relay_module_imports_for_future_slice_anchor():
    """Import the Relay helper module so its deferred-slice anchor stays covered."""
    relay = importlib.import_module("django_strawberry_framework.types.relay")

    assert relay.__doc__ == "Internal Relay/interface helpers for the 0.0.5 Relay foundation slice."
