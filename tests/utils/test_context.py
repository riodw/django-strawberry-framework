"""Tests for the shared request-context read / write / delete dispatch."""

from types import MappingProxyType, SimpleNamespace

from django_strawberry_framework.utils.context import (
    clear_context_key,
    get_context_value,
    stash_on_context,
)


def test_context_stash_round_trips_and_clears_object_dict_and_slots_mapping():
    """Each supported writable shape uses the same read and clear contract."""

    class SlotsMapping:
        __slots__ = ("values",)

        def __init__(self):
            self.values = {}

        def __getitem__(self, key):
            return self.values[key]

        def __setitem__(self, key, value):
            self.values[key] = value

        def __delitem__(self, key):
            del self.values[key]

    for context in (SimpleNamespace(), {}, SlotsMapping()):
        stash_on_context(context, "dst_context_test", 42)
        assert get_context_value(context, "dst_context_test") == 42
        clear_context_key(context, "dst_context_test")
        assert get_context_value(context, "dst_context_test", "missing") == "missing"


def test_context_read_fails_closed_for_hostile_attribute_and_mapping_access():
    """A broken consumer context cannot abort the resource/optimizer read path."""

    class HostileAttribute:
        @property
        def dst_context_test(self):
            raise RuntimeError("descriptor failed")

    class HostileMapping(dict):
        def get(self, key, default=None):
            raise RuntimeError("mapping read failed")

    assert get_context_value(HostileAttribute(), "dst_context_test", "missing") == "missing"
    assert get_context_value(HostileMapping(), "dst_context_test", "missing") == "missing"


def test_context_read_tries_mapping_after_hostile_attribute():
    """A mapping value remains reachable when an object's attribute descriptor fails."""

    class HostileAttributeMapping:
        def __init__(self):
            self.values = {"dst_context_test": 42}

        def __getattribute__(self, name):
            if name == "dst_context_test":
                raise RuntimeError("descriptor failed")
            return object.__getattribute__(self, name)

        def __getitem__(self, key):
            return self.values[key]

    context = HostileAttributeMapping()
    assert get_context_value(context, "dst_context_test", "missing") == 42


def test_frozen_context_stash_and_clear_are_noops():
    """Read-only mappings keep their original value; the write and clear are silently skipped."""
    context = MappingProxyType({"dst_context_test": 42})
    stash_on_context(context, "dst_context_test", 99)
    clear_context_key(context, "dst_context_test")
    assert get_context_value(context, "dst_context_test") == 42
