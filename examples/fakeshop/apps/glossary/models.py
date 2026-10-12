"""Relational source of truth for ``docs/GLOSSARY.md``.

The glossary app makes the repository vocabulary queryable in the same way the
kanban app makes ``KANBAN.md`` queryable: markdown remains the exported artifact,
while terms, aliases, categories, status, cross-term links, and spec mentions
live as rows.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, TypeVar

from django.db import models
from typing_extensions import override

if TYPE_CHECKING:
    from datetime import date, datetime

    from django.db.models.expressions import Combinable
    from django.db.models.fields.related_descriptors import RelatedManager

    _M = TypeVar("_M", bound=models.Model)

    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them;
    # ``null=True`` adds ``None`` to both.
    _DateTime: TypeAlias = models.DateTimeField[str | datetime | date | Combinable, datetime]
    _FK: TypeAlias = models.ForeignKey[_M | Combinable, _M]
    _PositiveInt: TypeAlias = models.PositiveIntegerField[float | int | str | Combinable, int]
    _Slug: TypeAlias = models.SlugField[str | int | Combinable, str]
    _Text: TypeAlias = models.TextField[str | Combinable, str]


class TimeStampedModel(models.Model):
    """Audit timestamps inherited by every glossary model."""

    created_date: _DateTime = models.DateTimeField(auto_now_add=True, editable=False)
    updated_date: _DateTime = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class LookupBase(TimeStampedModel):
    """Common shape for glossary lookup tables."""

    key: _Slug = models.SlugField(unique=True)
    label: _Text = models.TextField()
    order: _PositiveInt = models.PositiveIntegerField(default=0)
    description: _Text = models.TextField(blank=True, default="")

    class Meta(TimeStampedModel.Meta):
        abstract = True
        ordering = [
            "order",
            "label",
        ]

    @override
    def __str__(self) -> str:
        return self.label


class GlossaryStatus(LookupBase):
    """Lifecycle state for a glossary term: shipped, planned, deferred, etc."""

    class Meta(LookupBase.Meta):
        verbose_name = "glossary status"
        verbose_name_plural = "glossary statuses"


class GlossaryCategory(LookupBase):
    """Reader-facing grouping from the ``Browse by category`` section."""

    # Reverse accessor Django adds at class creation, declared for the type checker.
    memberships: RelatedManager[GlossaryCategoryMembership]

    class Meta(LookupBase.Meta):
        verbose_name = "glossary category"
        verbose_name_plural = "glossary categories"


class GlossaryTerm(TimeStampedModel):
    """One glossary entry with a stable markdown anchor."""

    title: _Text = models.TextField(unique=True)
    title_sort: _Text = models.TextField()
    anchor: _Slug = models.SlugField(max_length=200, unique=True)
    status: _FK[GlossaryStatus] = models.ForeignKey(
        GlossaryStatus,
        related_name="terms",
        on_delete=models.PROTECT,
    )
    status_text: _Text = models.TextField()
    body: _Text = models.TextField(blank=True, default="")
    entry_order: _PositiveInt = models.PositiveIntegerField(default=0)
    index_order: _PositiveInt = models.PositiveIntegerField(default=0)
    categories: models.ManyToManyField[GlossaryCategory, GlossaryCategoryMembership] = (
        models.ManyToManyField(
            GlossaryCategory,
            through="GlossaryCategoryMembership",
            related_name="terms",
            blank=True,
        )
    )
    related_terms: models.ManyToManyField[GlossaryTerm, GlossaryTermLink] = models.ManyToManyField(
        "self",
        through="GlossaryTermLink",
        symmetrical=False,
        related_name="related_from",
        blank=True,
    )

    # Key column Django adds beside ``status``, declared for the type checker;
    # ``None`` until assigned on an unsaved row.
    status_id: int | None
    # Reverse accessors Django adds at class creation, declared for the type checker.
    aliases: RelatedManager[GlossaryAlias]
    outgoing_links: RelatedManager[GlossaryTermLink]
    spec_mentions: RelatedManager[GlossarySpecMention]
    source_links: RelatedManager[GlossarySourceLink]

    class Meta(TimeStampedModel.Meta):
        ordering = [
            "entry_order",
            "title_sort",
        ]
        verbose_name = "glossary term"
        verbose_name_plural = "glossary terms"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""),
                name="glossary_term_title_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(title_sort=""),
                name="glossary_term_title_sort_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(anchor=""),
                name="glossary_term_anchor_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(status_text=""),
                name="glossary_term_status_text_required",
            ),
        ]
        indexes = [
            models.Index(fields=["title_sort"]),
            models.Index(
                fields=[
                    "status",
                    "entry_order",
                ],
            ),
        ]

    @override
    def __str__(self) -> str:
        return self.title


class GlossaryAlias(TimeStampedModel):
    """Alternate spelling or prose label that resolves to a canonical term."""

    term: _FK[GlossaryTerm] = models.ForeignKey(
        GlossaryTerm,
        related_name="aliases",
        on_delete=models.CASCADE,
    )
    # Key column Django adds beside ``term``, declared for the type checker;
    # ``None`` until assigned on an unsaved row.
    term_id: int | None
    label: _Text = models.TextField()
    normalized: _Text = models.TextField()

    class Meta(TimeStampedModel.Meta):
        ordering = [
            "term",
            "label",
        ]
        verbose_name = "glossary alias"
        verbose_name_plural = "glossary aliases"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "term",
                    "normalized",
                ],
                name="unique_glossary_alias_per_term",
            ),
            models.CheckConstraint(
                condition=~models.Q(label=""),
                name="glossary_alias_label_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(normalized=""),
                name="glossary_alias_normalized_required",
            ),
        ]
        indexes = [models.Index(fields=["normalized"])]

    @override
    def __str__(self) -> str:
        return f"{self.label} -> {self.term.title}"


class GlossaryTermLinkKind(LookupBase):
    """Why one glossary term points at another term."""

    class Meta(LookupBase.Meta):
        verbose_name = "glossary term link kind"
        verbose_name_plural = "glossary term link kinds"


class GlossaryTermLink(TimeStampedModel):
    """A normalized in-glossary edge such as a ``See also`` reference."""

    source_term: _FK[GlossaryTerm] = models.ForeignKey(
        GlossaryTerm,
        related_name="outgoing_links",
        on_delete=models.CASCADE,
    )
    target_term: _FK[GlossaryTerm] = models.ForeignKey(
        GlossaryTerm,
        related_name="incoming_links",
        on_delete=models.CASCADE,
    )
    # Key column Django adds beside ``target_term``, declared for the type checker;
    # ``None`` until assigned on an unsaved row.
    target_term_id: int | None
    kind: _FK[GlossaryTermLinkKind] = models.ForeignKey(
        GlossaryTermLinkKind,
        related_name="links",
        on_delete=models.PROTECT,
    )
    raw_label: _Text = models.TextField(blank=True, default="")
    order: _PositiveInt = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = [
            "source_term",
            "kind",
            "order",
        ]
        verbose_name = "glossary term link"
        verbose_name_plural = "glossary term links"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source_term",
                    "kind",
                    "order",
                ],
                name="unique_glossary_term_link_position",
            ),
        ]
        indexes = [
            models.Index(
                fields=[
                    "target_term",
                    "kind",
                ],
            ),
            models.Index(
                fields=[
                    "source_term",
                    "kind",
                ],
            ),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.source_term.title} -> {self.target_term.title} ({self.kind.key})"


class GlossaryCategoryMembership(TimeStampedModel):
    """Ordered membership of one term in one browse category."""

    category: _FK[GlossaryCategory] = models.ForeignKey(
        GlossaryCategory,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    term: _FK[GlossaryTerm] = models.ForeignKey(
        GlossaryTerm,
        related_name="category_memberships",
        on_delete=models.CASCADE,
    )
    # Key columns Django adds beside ``category`` and ``term``, declared for the type checker;
    # ``None`` until assigned on an unsaved row.
    category_id: int | None
    term_id: int | None
    order: _PositiveInt = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = [
            "category",
            "order",
        ]
        verbose_name = "glossary category membership"
        verbose_name_plural = "glossary category memberships"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "category",
                    "term",
                ],
                name="unique_glossary_term_per_category",
            ),
            models.UniqueConstraint(
                fields=[
                    "category",
                    "order",
                ],
                name="unique_glossary_category_position",
            ),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.category.label}: {self.term.title}"


class GlossarySpecMention(TimeStampedModel):
    """A spec terms-CSV row resolved to a canonical glossary term."""

    term: _FK[GlossaryTerm] = models.ForeignKey(
        GlossaryTerm,
        related_name="spec_mentions",
        on_delete=models.CASCADE,
    )
    # Key column Django adds beside ``term``, declared for the type checker;
    # ``None`` until assigned on an unsaved row.
    term_id: int | None
    spec_path: _Text = models.TextField()
    term_text: _Text = models.TextField()
    notes: _Text = models.TextField(blank=True, default="")
    order: _PositiveInt = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = [
            "spec_path",
            "order",
        ]
        verbose_name = "glossary spec mention"
        verbose_name_plural = "glossary spec mentions"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "spec_path",
                    "term",
                ],
                name="unique_glossary_term_per_spec",
            ),
            models.CheckConstraint(
                condition=~models.Q(spec_path=""),
                name="glossary_spec_mention_path_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(term_text=""),
                name="glossary_spec_mention_text_required",
            ),
        ]
        indexes = [models.Index(fields=["spec_path"])]

    @property
    def spec_name(self) -> str:
        """Return the basename of ``spec_path`` for compact GraphQL views."""
        return Path(self.spec_path).name

    @override
    def __str__(self) -> str:
        return f"{self.spec_path}: {self.term_text}"


class GlossarySourceLink(TimeStampedModel):
    """A non-glossary link embedded in a term body."""

    term: _FK[GlossaryTerm] = models.ForeignKey(
        GlossaryTerm,
        related_name="source_links",
        on_delete=models.CASCADE,
    )
    # Key column Django adds beside ``term``, declared for the type checker;
    # ``None`` until assigned on an unsaved row.
    term_id: int | None
    label: _Text = models.TextField()
    target: _Text = models.TextField()
    kind: _Text = models.TextField(blank=True, default="")
    order: _PositiveInt = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = [
            "term",
            "order",
        ]
        verbose_name = "glossary source link"
        verbose_name_plural = "glossary source links"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "term",
                    "order",
                ],
                name="unique_glossary_source_link_position",
            ),
            models.CheckConstraint(
                condition=~models.Q(label=""),
                name="glossary_source_link_label_required",
            ),
            models.CheckConstraint(
                condition=~models.Q(target=""),
                name="glossary_source_link_target_required",
            ),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.term.title}: {self.label}"
