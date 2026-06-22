"""Custom DB expression that keeps the UUIDModel one-hot constraint flat in migrations.

``UUIDModel`` enforces "exactly one of N one-to-one link fields is non-null" via a
``CheckConstraint`` whose condition is, historically,
``reduce(operator.add, [Case(When(<field>__isnull=False, then=1), default=0) ...]) == 1``.
Django's migration serializer renders that *evaluated* left-associative ``+`` chain as
one ``CombinedExpression`` per term -- an N-deep nesting tower that is regenerated in
full every time a link field is added or removed (one migration per change).

``OneHotLinkCount`` builds the identical ``Case``-sum at resolve time -- same SQL, same
DB constraint -- but ``deconstruct()``s to its flat field-name list, so the enclosing
constraint serializes as a single ``OneHotLinkCount("milestone", "status", ...)`` call
instead of the tower. The nesting becomes a runtime implementation detail.
"""

from __future__ import annotations

import operator
from functools import reduce
from typing import Any

from django.db import models
from django.utils.deconstruct import deconstructible


@deconstructible(path="apps.kanban.constraints.OneHotLinkCount")
class OneHotLinkCount(models.Expression):
    """Sum of ``1`` per non-null field among ``field_names`` (the one-hot link count).

    Resolves to ``SUM(CASE WHEN <field> IS NOT NULL THEN 1 ELSE 0 END)`` across the
    given fields -- the portable count Django's check constraint needs. The flat
    ``deconstruct`` (via ``@deconstructible``) is what keeps migrations a single line.
    """

    def __init__(self, *field_names: str) -> None:
        if not field_names:
            raise ValueError("OneHotLinkCount requires at least one field name.")
        self.field_names = field_names
        super().__init__(output_field=models.IntegerField())

    def resolve_expression(self, *args: Any, **kwargs: Any) -> Any:
        summed = reduce(
            operator.add,
            (
                models.Case(
                    models.When(**{f"{name}__isnull": False}, then=1),
                    default=0,
                    output_field=models.IntegerField(),
                )
                for name in self.field_names
            ),
        )
        return summed.resolve_expression(*args, **kwargs)
