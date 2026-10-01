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

from typing import TYPE_CHECKING

from django.db import models
from django.utils.deconstruct import deconstructible
from typing_extensions import override

if TYPE_CHECKING:
    from django.db.models.sql.query import Query


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

    @override
    def resolve_expression(
        self,
        query: Query | None = None,
        allow_joins: bool = True,
        reuse: set[str] | None = None,
        summarize: bool = False,
        for_save: bool = False,
    ) -> models.Expression:
        cases = [
            models.Case(
                models.When(**{f"{name}__isnull": False}, then=1),
                default=0,
                output_field=models.IntegerField(),
            )
            for name in self.field_names
        ]
        # Left-associative ``+`` fold: ``((case_1 + case_2) + case_3) + ...``.
        summed: models.Expression = cases[0]
        for case in cases[1:]:
            summed = summed + case
        return summed.resolve_expression(query, allow_joins, reuse, summarize, for_save)
