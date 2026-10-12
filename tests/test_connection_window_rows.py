"""The windowed-prefetch hand-off accepts only model rows as a connection window.

``connection.py::_window_rows_are_annotated`` decides whether a ``to_attr`` list
is the walker's window and so may be served as the page's nodes. The row-number
annotation alone does not make a row a node: an object a consumer wrote under the
reserved attribute that carries the annotation but is not a model instance
disqualifies the list, as a missing annotation does.
"""

from __future__ import annotations

from apps.library.models import Branch

from django_strawberry_framework.connection import _window_rows_are_annotated
from django_strawberry_framework.optimizer.plans import WINDOW_ROW_NUMBER


class _AnnotatedObject:
    """A non-model object carrying the window's row-number annotation."""


def _annotated(row: object) -> object:
    setattr(row, WINDOW_ROW_NUMBER, 1)
    return row


def test_annotated_model_rows_are_a_window():
    """Model instances carrying the row number are the walker's window."""
    assert _window_rows_are_annotated([_annotated(Branch(name="north"))]) is True


def test_annotated_non_model_row_is_not_a_window():
    """A non-model row disqualifies the list even when it carries the row number."""
    rows = [_annotated(Branch(name="north")), _annotated(_AnnotatedObject())]

    assert _window_rows_are_annotated(rows) is False
