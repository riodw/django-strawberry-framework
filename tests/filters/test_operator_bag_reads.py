"""A dict operator bag is classified and read through one base read of its pairs.

``filters/sets.py::FilterSet._operator_bag_items`` decides whether a dict is a
per-field operator bag (every key a lookup attr) and returns its pairs. The pairs
are read once through the base ``dict.items`` slot, so a dict subclass cannot
report one set of pairs to the classification and another to the normalizer, and
each key is reduced to an exact ``str`` before it is matched.
"""

from __future__ import annotations

from _collections_abc import dict_items

from typing_extensions import override

from django_strawberry_framework.filters.sets import FilterSet


class _LyingBag(dict[object, object]):
    """A dict whose ``items`` override reports pairs it does not hold."""

    @override
    def items(self) -> dict_items[object, object]:
        return {"exact": "lie"}.items()


class _LookupName(str):
    """A ``str`` subclass key spelling a lookup attr."""

    __slots__ = ()


def test_bag_pairs_come_from_the_dict_contents_not_its_items_override():
    """The pairs returned are the ones the dict holds, whatever ``items`` reports."""
    assert FilterSet._operator_bag_items(_LyingBag({"exact": "held"})) == [("exact", "held")]


def test_str_subclass_key_is_reduced_to_an_exact_str():
    """A ``str`` subclass key is matched and returned as the exact lookup name."""
    pairs = FilterSet._operator_bag_items({_LookupName("exact"): "x"})

    assert pairs == [("exact", "x")]
    assert pairs is not None
    assert type(pairs[0][0]) is str


def test_non_string_key_makes_the_dict_no_bag():
    """A key that is not a string names no lookup, so the dict is not an operator bag."""
    assert FilterSet._operator_bag_items({1: "x"}) is None


def test_empty_dict_is_no_bag():
    """An empty dict carries no lookup, so it is not an operator bag."""
    assert FilterSet._operator_bag_items({}) is None
