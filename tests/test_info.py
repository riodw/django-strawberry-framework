"""Smoke tests proving the shared ``tests/_info.py`` builders hand out what they promise.

``unread_info`` is the instrument behind every "the path under test never reads
``info``" claim; a spy that silently answered a read would make each of those claims
pass vacuously, so this file proves it refuses one. ``make_info`` is proved by
reading back the slots tests vary through the real ``Info`` properties.
"""

import pytest
import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.nodes import SelectedField

from tests._info import make_info, response_path, unread_info


def test_unread_info_is_a_real_info_that_refuses_every_read():
    """A read of any ``Info`` slot fails with the slot's name."""
    info = unread_info()
    assert isinstance(info, strawberry.Info)
    with pytest.raises(AssertionError, match=r"read info\.context;"):
        _ = info.context
    with pytest.raises(AssertionError, match=r"read info\.schema;"):
        _ = info.schema


def test_make_info_reads_back_what_the_test_varied():
    """Context, field, selections, fragments, path, variables and config read back as given."""
    context = object()
    info = make_info(
        context=context,
        field_name="items",
        selections="{ edges ...Counted }",
        fragments="fragment Counted on Connection { totalCount }",
        path=response_path("parent", 0, "items"),
        variables={"first": 2},
        config=StrawberryConfig(relay_max_results=7),
    )
    assert info.context is context
    assert info.field_name == "items"
    assert info.python_name == "items"
    [selected] = info.selected_fields
    assert isinstance(selected, SelectedField)
    assert selected.name == "items"
    assert [type(child).__name__ for child in selected.selections] == [
        "SelectedField",
        "FragmentSpread",
    ]
    assert info.path.as_list() == ["parent", 0, "items"]
    assert info.variable_values == {"first": 2}
    assert info.schema.config.relay_max_results == 7
    assert make_info().schema.config.relay_max_results != 7
