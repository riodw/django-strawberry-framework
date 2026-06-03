"""OrderSet declarations for the glossary data app.

One ``OrderSet`` per ``FilterSet`` in ``apps.glossary.filters`` (1:1 with
the owning ``DjangoType``). Each uses the ``Meta.fields = "__all__"``
shorthand -- every column-backed field (the orderable scalars plus forward
FK columns such as ``status`` / ``term`` / ``category`` -> ``<field>_id``);
reverse relations and M2M managers are excluded. ``GlossaryDocumentOrder``
orders the shared ``kanban.BoardDoc`` model (the glossary namespace's view
of board docs), mirroring ``GlossaryDocumentType``. No per-field permission
gates -- ordering is a straight wiring of the ``Ordering`` surface.
"""

from __future__ import annotations

from apps.kanban import models as kanban_models
from django_strawberry_framework.orders import OrderSet

from . import models


class GlossaryStatusOrder(OrderSet):
    class Meta:
        model = models.GlossaryStatus
        fields = "__all__"


class GlossaryCategoryOrder(OrderSet):
    class Meta:
        model = models.GlossaryCategory
        fields = "__all__"


class GlossaryTermOrder(OrderSet):
    class Meta:
        model = models.GlossaryTerm
        fields = "__all__"


class GlossaryAliasOrder(OrderSet):
    class Meta:
        model = models.GlossaryAlias
        fields = "__all__"


class GlossaryTermLinkKindOrder(OrderSet):
    class Meta:
        model = models.GlossaryTermLinkKind
        fields = "__all__"


class GlossaryTermLinkOrder(OrderSet):
    class Meta:
        model = models.GlossaryTermLink
        fields = "__all__"


class GlossaryCategoryMembershipOrder(OrderSet):
    class Meta:
        model = models.GlossaryCategoryMembership
        fields = "__all__"


class GlossarySpecMentionOrder(OrderSet):
    class Meta:
        model = models.GlossarySpecMention
        fields = "__all__"


class GlossarySourceLinkOrder(OrderSet):
    class Meta:
        model = models.GlossarySourceLink
        fields = "__all__"


class GlossaryDocumentOrder(OrderSet):
    class Meta:
        model = kanban_models.BoardDoc
        fields = "__all__"


__all__ = (
    "GlossaryAliasOrder",
    "GlossaryCategoryMembershipOrder",
    "GlossaryCategoryOrder",
    "GlossaryDocumentOrder",
    "GlossarySourceLinkOrder",
    "GlossarySpecMentionOrder",
    "GlossaryStatusOrder",
    "GlossaryTermLinkKindOrder",
    "GlossaryTermLinkOrder",
    "GlossaryTermOrder",
)
