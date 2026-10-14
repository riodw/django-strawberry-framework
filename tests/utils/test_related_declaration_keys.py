"""The permission walk's related-declaration read holds a collection to attribute-name keys.

``utils/permissions.py::_related_declarations`` materializes a set's related
collection for the flat-path walk; a key becomes the hop's declared attribute
name, so a hand-assigned collection keyed by anything but a string is refused
with a typed error rather than walked.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.permissions import walk_declared_relation_path


class _Target:
    """A declaration target with no further related declarations."""


class _Declaration:
    """A related declaration naming the ``category`` relation."""

    field_name = "category"
    target = _Target


def test_non_string_related_declaration_key_is_refused() -> None:
    """A non-string key in the related collection raises the typed walk error."""

    class _Owner:
        related_filters: ClassVar[dict[object, object]] = {1: _Declaration()}

    with pytest.raises(ConfigurationError, match="must be keyed by attribute name strings"):
        walk_declared_relation_path(
            _Owner,
            "category__name",
            related_attr="related_filters",
            target_attr="target",
        )


def test_string_related_declaration_key_is_walked() -> None:
    """A string-keyed collection still walks to its declared hop."""

    class _Owner:
        related_filters: ClassVar[dict[object, object]] = {"category": _Declaration()}

    hops, remainder = walk_declared_relation_path(
        _Owner,
        "category__name",
        related_attr="related_filters",
        target_attr="target",
    )

    assert [hop.declared_attr for hop in hops] == ["category"]
    assert remainder == ("name",)
