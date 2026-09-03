"""Tests for the shared request-context read / write / delete dispatch."""

from types import MappingProxyType, SimpleNamespace

import pytest

from django_strawberry_framework.utils.context import (
    MISSING,
    clear_context_key,
    get_context_value,
    restored_context_keys,
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


def test_context_none_short_circuits_and_skips_writes_and_clears():
    """None context returns default on read and silently skips write and clear."""
    assert get_context_value(None, "dst_context_test") is None
    assert get_context_value(None, "dst_context_test", "missing") == "missing"
    stash_on_context(None, "dst_context_test", 42)
    clear_context_key(None, "dst_context_test")


def test_context_distinguishes_explicit_none_from_missing_sentinel():
    """Stashing an explicit None value returns None rather than falling back to default."""
    obj_ctx = SimpleNamespace()
    dict_ctx = {}

    stash_on_context(obj_ctx, "dst_context_test", None)
    stash_on_context(dict_ctx, "dst_context_test", None)

    assert get_context_value(obj_ctx, "dst_context_test", "default") is None
    assert get_context_value(dict_ctx, "dst_context_test", "default") is None


def test_locked_dict_subclass_stash_and_clear_are_noops():
    """Immutable dict subclasses (e.g. locked QueryDict) silently skip stash and clear."""

    class LockedDict(dict):
        def __setitem__(self, key, value):
            raise AttributeError("This dict is immutable")

        def __delitem__(self, key):
            raise AttributeError("This dict is immutable")

    ctx = LockedDict({"dst_context_test": 42})
    stash_on_context(ctx, "dst_context_test", 99)
    clear_context_key(ctx, "dst_context_test")
    assert get_context_value(ctx, "dst_context_test") == 42


class SlotsMapping:
    """A non-dict mapping-only context: ``setattr`` is impossible, items work."""

    __slots__ = ("values",)

    def __init__(self):
        self.values = {}

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __delitem__(self, key):
        del self.values[key]


@pytest.mark.parametrize(
    "make",
    [SimpleNamespace, dict, SlotsMapping],
    ids=["object", "dict", "slots"],
)
def test_restored_context_keys_round_trips_absent_present_and_none(make):
    """The restore puts ABSENT keys back to absent and re-stashes found values.

    An explicit ``None`` snapshot is a VALUE: it is re-stashed, never cleared,
    on every writable context shape the helpers dispatch on.
    """
    for stashed in ("outer", None):
        context = make()
        stash_on_context(context, "dst_context_test", stashed)
        with restored_context_keys(context, "dst_context_test"):
            stash_on_context(context, "dst_context_test", "inner")
        if stashed is None:
            assert get_context_value(context, "dst_context_test", "absent") is None
        else:
            assert get_context_value(context, "dst_context_test") == stashed

    context = make()
    with restored_context_keys(context, "dst_context_test"):
        stash_on_context(context, "dst_context_test", "inner")
    assert get_context_value(context, "dst_context_test", "absent") == "absent"


def test_restored_context_keys_still_restores_when_the_body_raises():
    """Restoration runs in a ``finally``: a raising body leaves the context as found."""
    context = {}
    stash_on_context(context, "kept", "outer")
    with pytest.raises(RuntimeError, match="boom"):
        with restored_context_keys(context, "kept", "never-was"):
            stash_on_context(context, "kept", "inner")
            stash_on_context(context, "never-was", "transient")
            raise RuntimeError("boom")
    assert get_context_value(context, "kept") == "outer"
    assert get_context_value(context, "never-was", "absent") == "absent"


def test_restored_context_keys_on_a_none_context_is_inert():
    """No context means nothing to snapshot and nothing to restore."""
    with restored_context_keys(None, "dst_context_test"):
        stash_on_context(None, "dst_context_test", 42)
        assert get_context_value(None, "dst_context_test", "d") == "d"
    assert get_context_value(None, "dst_context_test", "d") == "d"


def test_restored_context_keys_snapshots_an_unreadable_key_as_absent():
    """A hostile read cannot be distinguished from absence: the restore clears."""

    class ReadGuarded(SlotsMapping):
        __slots__ = ("readable",)

        def __init__(self):
            super().__init__()
            self.readable = False

        def __getitem__(self, key):
            if not self.readable:
                raise RuntimeError("reads locked")
            return self.values[key]

    context = ReadGuarded()
    context.values["dst_context_test"] = "outer"
    with restored_context_keys(context, "dst_context_test"):
        context.readable = True
        stash_on_context(context, "dst_context_test", "inner")
    assert get_context_value(context, "dst_context_test", "absent") == "absent"


def test_the_public_missing_sentinel_is_the_round_trip_identity():
    """``MISSING`` is importable and is the exact sentinel the read dispatches on."""
    assert get_context_value({}, "dst_context_test", MISSING) is MISSING
    assert MISSING is not None
