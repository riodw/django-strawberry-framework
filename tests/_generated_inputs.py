"""Shared keyword-constructor view of run-time-generated GraphQL input classes.

The package's GraphQL input factories build each input class with
``type(name, (), namespace)``, so its keyword fields exist only at run time and no static
signature lets a test call ``input_cls(name=...)``. ``keyword_constructor`` returns the
class typed as ``Callable[..., object]``, the honest static view of such a class, so test
modules construct generated inputs by keyword without a per-call suppression.
"""

from collections.abc import Callable


def keyword_constructor(input_cls: type[object]) -> Callable[..., object]:
    """``input_cls`` as a constructor: its factory generates its keyword fields at run time."""
    return input_cls
