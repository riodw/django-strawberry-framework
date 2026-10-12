"""A choice entry is unpacked as a pair only once it is proven iterable.

``types/converters.py::_unpack_choice_entry`` reads one consumer-declared choice
entry as its ``(value, label)`` pair. An entry that is not iterable at all is the
same malformed declaration as a short or long pair and gets the same typed
refusal, raised before any unpacking is attempted.
"""

from __future__ import annotations

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.types.converters import build_enum_from_choices


def test_non_iterable_choice_entry_is_a_malformed_choice():
    """A bare integer entry is refused as a malformed choice."""
    with pytest.raises(ConfigurationError, match="declares a malformed choice 1;"):
        build_enum_from_choices([1], "ChoiceEntryShapeEnum", source_label="probe")


def test_pair_choice_entry_builds_its_member():
    """A ``(value, label)`` pair still builds the enum member it declares."""
    enum_cls = build_enum_from_choices([("a", "A")], "ChoiceEntryShapeEnum", source_label="probe")

    assert [member.value for member in enum_cls] == ["a"]
