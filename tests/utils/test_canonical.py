"""Tests for the hostile-safe container read / ordering primitives (``utils/canonical.py``).

The module has two consumers - the generated-input metadata cache key
(``utils/inputs.py::make_hashable_meta_value``) and the write pipeline's pre-save
drift fingerprint (``utils/write_transaction.py::_field_fingerprint``) - and both
reach it only through their own gates. These tests exercise the primitives
DIRECTLY, because the properties that matter (a subclass's overridden iteration
never runs; a lying or raising ``__repr__`` never collapses or breaks an order)
are properties of the primitive, not of either walk that consumes it. A test that
could only reach them through a consumer would be testing the consumer's gate.
"""

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.canonical import (
    base_container_values,
    canonical_sort_key,
)


class _LyingDict(dict):
    """A ``dict`` subclass whose overridden views report contents it does not hold."""

    def items(self):
        return [("lied", "pair")]

    def keys(self):
        return ["lied"]

    def values(self):
        return ["pair"]

    def __iter__(self):
        return iter(["lied"])

    def __len__(self):
        return 99


class _LyingSet(set):
    def __iter__(self):
        return iter(["lied"])

    def __len__(self):
        return 99


class _LyingFrozenSet(frozenset):
    def __iter__(self):
        return iter(["lied"])

    def __len__(self):
        return 99


class _LyingList(list):
    def __iter__(self):
        return iter(["lied"])

    def __len__(self):
        return 99


class _LyingTuple(tuple):
    def __iter__(self):
        return iter(["lied"])

    def __len__(self):
        return 99


class _HostileIterable:
    """A non-base iterable whose ``__iter__`` detonates, recording that it ran."""

    def __init__(self):
        self.iter_calls = 0

    def __iter__(self):
        self.iter_calls += 1
        raise RuntimeError("hostile __iter__ detonated")


class _PlainIterable:
    """A well-behaved non-base iterable - still outside the readable domain."""

    def __iter__(self):
        return iter(["a", "b"])


class _ConstantRepr:
    """Distinct instances that all render identically, the collapse a bare key allows."""

    def __repr__(self):
        return "<same>"


class _RaisingRepr:
    def __repr__(self):
        raise RuntimeError("hostile __repr__ detonated")


class _HostileStr(str):
    """A ``str`` subclass that detonates the moment anything renders it."""

    def __str__(self):
        raise RuntimeError("hostile __str__ detonated")

    def __format__(self, spec):
        raise RuntimeError("hostile __format__ detonated")


class _LyingStr(str):
    """A ``str`` subclass whose ``__repr__`` hands back a hostile ``str`` subclass."""

    def __repr__(self):
        return _HostileStr("forged")


def test_base_container_values_reads_a_plain_dicts_items():
    assert base_container_values({"a": 1, "b": 2}) == (("a", 1), ("b", 2))


def test_base_container_values_reads_plain_members_for_the_other_four_containers():
    assert base_container_values({"only"}) == ("only",)
    assert base_container_values(frozenset({"only"})) == ("only",)
    assert base_container_values(["a", "b"]) == ("a", "b")
    assert base_container_values(("a", "b")) == ("a", "b")


def test_base_container_values_reads_a_dict_subclass_through_the_base_items_slot():
    """``dict.items`` is called unbound, so the override cannot decide what is seen."""
    value = _LyingDict({"real": 1})

    assert base_container_values(value) == (("real", 1),)
    # The overrides really are installed - the assertion above is not passing by
    # accident on a subclass that forgot to override anything.
    assert value.items() == [("lied", "pair")]
    assert list(iter(value)) == ["lied"]
    assert len(value) == 99


@pytest.mark.parametrize(
    ("factory", "expected"),
    [
        (lambda: _LyingSet({"real"}), ("real",)),
        (lambda: _LyingFrozenSet({"real"}), ("real",)),
        (lambda: _LyingList(["real"]), ("real",)),
        (lambda: _LyingTuple(("real",)), ("real",)),
    ],
    ids=[
        "set",
        "frozenset",
        "list",
        "tuple",
    ],
)
def test_base_container_values_reads_subclasses_through_the_base_iterator(factory, expected):
    """A subclass's ``__iter__`` / ``__len__`` override is bypassed on every shape."""
    value = factory()

    assert base_container_values(value) == expected
    assert list(iter(value)) == ["lied"]
    assert len(value) == 99


def test_base_container_values_refuses_a_non_base_iterable():
    """Outside the five built-ins there is no base slot to read, so the answer is typed.

    The refusal is the contract both callers already assume: each gates on the
    five built-in container types before calling in, so no reachable path relies
    on an arbitrary ``__iter__`` being walked.
    """
    with pytest.raises(ConfigurationError, match="Cannot canonically read a _PlainIterable"):
        base_container_values(_PlainIterable())


def test_base_container_values_refuses_a_hostile_iterable_without_running_its_iter():
    """A detonating ``__iter__`` never runs: the refusal precedes the dispatch.

    Containing the ``RuntimeError`` would be the weaker fix - an ``__iter__`` that
    returns different members per call lies without raising at all, and only a
    refusal answers that.
    """
    value = _HostileIterable()

    with pytest.raises(ConfigurationError, match="Cannot canonically read a _HostileIterable"):
        base_container_values(value)

    assert value.iter_calls == 0


def test_base_container_values_refusal_is_not_chained_to_a_consumer_error():
    """No ``__cause__``: nothing of the consumer's ran, so there is no cause to chain."""
    with pytest.raises(ConfigurationError) as exc_info:
        base_container_values(_HostileIterable())

    assert exc_info.value.__cause__ is None


def test_canonical_sort_key_totally_orders_mutually_unorderable_types():
    """Eight types that ``<`` cannot compare pairwise still sort deterministically."""
    values = [
        1,
        2.5,
        "text",
        b"bytes",
        None,
        True,
        (1, 2),
        object(),
        _LyingStr("real"),
    ]

    # Sorting a ROTATED permutation as well proves the order is a property of the
    # key, not of the input sequence: a key that failed to separate two of these
    # values would let the two runs disagree on their relative position.
    rotated = values[4:] + values[:4]
    first = sorted(values, key=canonical_sort_key)
    second = sorted(rotated, key=canonical_sort_key)

    assert [id(item) for item in first] == [id(item) for item in second]
    assert len(first) == len(values)


def test_canonical_sort_key_keeps_identical_reprs_distinct():
    """A constant ``__repr__`` cannot collapse two values onto one key.

    That collapse is the fail-open the key exists to prevent: on the drift path
    two structurally different values sharing a key share a fingerprint.
    """
    left = _ConstantRepr()
    right = _ConstantRepr()

    assert repr(left) == repr(right)
    assert canonical_sort_key(left) != canonical_sort_key(right)


def test_canonical_sort_key_guards_a_raising_repr():
    """A detonating ``__repr__`` yields a key instead of breaking the walk."""
    value = _RaisingRepr()

    key = canonical_sort_key(value)

    assert isinstance(key, tuple)
    assert key[0] == "<unprintable _RaisingRepr>"
    assert key[1:] == (id(type(value)), id(value))


def test_canonical_sort_key_flattens_a_str_subclass_repr_to_the_base_str():
    """A ``__repr__`` returning a ``str`` SUBCLASS is stripped to base ``str``.

    CPython hands a ``tp_repr`` result back unchanged when it is a ``str``
    subclass. Carrying that object into the key would arm every later render of
    the key - a sort comparison, an f-string in a diagnostic - with the
    subclass's overridden ``__str__`` / ``__format__``. The key element is base
    ``str``, so nothing of the consumer's runs after the guarded repr returns.
    """
    lying = _LyingStr("real")
    assert isinstance(lying.__repr__(), _HostileStr)

    rendered = canonical_sort_key(lying)[0]

    assert type(rendered) is str
    assert rendered == "forged"
    # The proof the strip happened: rendering the key element is inert, while
    # rendering what ``__repr__`` returned would detonate.
    assert f"{rendered}" == "forged"
