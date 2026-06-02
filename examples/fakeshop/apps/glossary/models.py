"""Relational source of truth for ``docs/GLOSSARY.md``.

The glossary app makes the repository vocabulary queryable in the same way the
kanban app makes ``KANBAN.md`` queryable: markdown remains the exported artifact,
while terms, aliases, categories, status, cross-term links, and spec mentions
live as rows.
"""

from __future__ import annotations

from pathlib import Path

from django.db import models


class TimeStampedModel(models.Model):
    """Audit timestamps inherited by every glossary model."""

    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_date = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class LookupBase(TimeStampedModel):
    """Common shape for glossary lookup tables."""

    key = models.SlugField(unique=True)
    label = models.TextField()
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, default="")

    class Meta:
        abstract = True
        ordering = [
            "order",
            "label",
        ]

    def __str__(self):
        return self.label


class GlossaryStatus(LookupBase):
    """Lifecycle state for a glossary term: shipped, planned, deferred, etc."""

    class Meta(LookupBase.Meta):
        verbose_name = "glossary status"
        verbose_name_plural = "glossary statuses"


class GlossaryCategory(LookupBase):
    """Reader-facing grouping from the ``Browse by category`` section."""

    class Meta(LookupBase.Meta):
        verbose_name = "glossary category"
        verbose_name_plural = "glossary categories"


class GlossaryTerm(TimeStampedModel):
    """One glossary entry with a stable markdown anchor."""

    title = models.TextField(unique=True)
    title_sort = models.TextField()
    anchor = models.SlugField(max_length=200, unique=True)
    status = models.ForeignKey(
        GlossaryStatus,
        related_name="terms",
        on_delete=models.PROTECT,
    )
    status_text = models.TextField()
    body = models.TextField(blank=True, default="")
    entry_order = models.PositiveIntegerField(default=0)
    index_order = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(
        GlossaryCategory,
        through="GlossaryCategoryMembership",
        related_name="terms",
        blank=True,
    )
    related_terms = models.ManyToManyField(
        "self",
        through="GlossaryTermLink",
        symmetrical=False,
        related_name="related_from",
        blank=True,
    )

    class Meta:
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

    def __str__(self):
        return self.title


class GlossaryAlias(TimeStampedModel):
    """Alternate spelling or prose label that resolves to a canonical term."""

    term = models.ForeignKey(
        GlossaryTerm,
        related_name="aliases",
        on_delete=models.CASCADE,
    )
    label = models.TextField()
    normalized = models.TextField()

    class Meta:
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

    def __str__(self):
        return f"{self.label} -> {self.term.title}"


class GlossaryTermLinkKind(LookupBase):
    """Why one glossary term points at another term."""

    class Meta(LookupBase.Meta):
        verbose_name = "glossary term link kind"
        verbose_name_plural = "glossary term link kinds"


class GlossaryTermLink(TimeStampedModel):
    """A normalized in-glossary edge such as a ``See also`` reference."""

    source_term = models.ForeignKey(
        GlossaryTerm,
        related_name="outgoing_links",
        on_delete=models.CASCADE,
    )
    target_term = models.ForeignKey(
        GlossaryTerm,
        related_name="incoming_links",
        on_delete=models.CASCADE,
    )
    kind = models.ForeignKey(
        GlossaryTermLinkKind,
        related_name="links",
        on_delete=models.PROTECT,
    )
    raw_label = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
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

    def __str__(self):
        return f"{self.source_term.title} -> {self.target_term.title} ({self.kind.key})"


class GlossaryCategoryMembership(TimeStampedModel):
    """Ordered membership of one term in one browse category."""

    category = models.ForeignKey(
        GlossaryCategory,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    term = models.ForeignKey(
        GlossaryTerm,
        related_name="category_memberships",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
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

    def __str__(self):
        return f"{self.category.label}: {self.term.title}"


class GlossarySpecMention(TimeStampedModel):
    """A spec terms-CSV row resolved to a canonical glossary term."""

    term = models.ForeignKey(
        GlossaryTerm,
        related_name="spec_mentions",
        on_delete=models.CASCADE,
    )
    spec_path = models.TextField()
    term_text = models.TextField()
    notes = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
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

    def __str__(self):
        return f"{self.spec_path}: {self.term_text}"


class GlossarySourceLink(TimeStampedModel):
    """A non-glossary link embedded in a term body."""

    term = models.ForeignKey(
        GlossaryTerm,
        related_name="source_links",
        on_delete=models.CASCADE,
    )
    label = models.TextField()
    target = models.TextField()
    kind = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
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

    def __str__(self):
        return f"{self.term.title}: {self.label}"
