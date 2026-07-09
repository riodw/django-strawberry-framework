"""A relational rendering of this repository's own ``KANBAN.md`` board.

The app dogfoods the framework: every value that can recur across cards is its
own lookup model (no inline ``choices``/enums), so the board can be queried from
either side (``status(key:"done"){cards}`` or a ``CardFilter``), and the
resulting schema is the example tree's most FK-dense / O2O-dense graph.

Two foundations every model leans on:

* :class:`TimeStampedModel` -- an abstract base adding ``created_date`` /
  ``updated_date`` to every table (the products app inlines the same two
  fields; an abstract base is the DRY equivalent for this many models).
* :class:`UUIDModel` -- a single side-table whose UUID primary key is the
  stable, opaque identifier for whichever model row its (one non-null)
  one-to-one link points at. This is NOT a ``uuid`` column on each model; each
  domain row reaches its UUID via the reverse accessor ``instance.uuid.id``. A
  signal receiver creates the row automatically on first save.
"""

import uuid

from django.db import models
from django.db.models.lookups import Exact
from django.utils.text import slugify

from .constraints import OneHotLinkCount

DEPENDENCY_REFERENCE_KIND_KEYS = frozenset(
    {
        "blocked_by",
        "dependency",
    },
)
BLOCKING_REFERENCE_KIND_KEYS = frozenset({"blocked_by"})

# ---------------------------------------------------------------------------
# Abstract bases
# ---------------------------------------------------------------------------


class TimeStampedModel(models.Model):
    """Audit timestamps inherited by every kanban model."""

    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_date = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class LookupBase(TimeStampedModel):
    """Common shape for the option/lookup tables: ``key`` / ``label`` / ``order``.

    A two-level abstract chain (``LookupBase`` -> ``TimeStampedModel``) so the
    concrete lookups inherit both the audit timestamps and the lookup columns --
    which also exercises the framework's handling of fields flattened from more
    than one abstract ancestor.
    """

    key = models.SlugField(unique=True)
    label = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self):
        return self.label


# ---------------------------------------------------------------------------
# Lookup (option) models -- each row recurs across many cards
# ---------------------------------------------------------------------------


class Milestone(LookupBase):
    """The development phase: ``alpha`` / ``beta`` / ``stable``."""

    version_floor = models.TextField(blank=True, default="")
    version_ceiling = models.TextField(blank=True, default="")

    class Meta(LookupBase.Meta):
        verbose_name = "milestone"
        verbose_name_plural = "milestones"


class Status(LookupBase):
    """The card workflow state that drives board placement."""

    class Meta(LookupBase.Meta):
        verbose_name = "status"
        verbose_name_plural = "statuses"


class Priority(LookupBase):
    """``high`` / ``medium`` / ``low``."""

    class Meta(LookupBase.Meta):
        verbose_name = "priority"
        verbose_name_plural = "priorities"


class RelativeSize(LookupBase):
    """T-shirt size: ``xs`` / ``s`` / ``m`` / ``l`` / ``xl``."""

    rank = models.PositiveIntegerField(default=0)
    # The per-size effort blurb rendered as the ``## Relative size`` scale in
    # KANBAN.md / KANBAN.html, so the scale is derived from this table rather
    # than frozen in the board prose.
    description = models.TextField(blank=True, default="")

    class Meta(LookupBase.Meta):
        verbose_name = "relative size"
        verbose_name_plural = "relative sizes"


class PlanningState(LookupBase):
    """The planning keyword: ``planned`` / ``needs_spec`` / ``in_progress`` / ``shipped``."""

    class Meta(LookupBase.Meta):
        verbose_name = "planning state"
        verbose_name_plural = "planning states"


class Upstream(LookupBase):
    """A parity target: ``graphene_django`` (⚛️) / ``strawberry_django`` (🍓)."""

    emoji = models.TextField(blank=True, default="")

    class Meta(LookupBase.Meta):
        verbose_name = "upstream"
        verbose_name_plural = "upstreams"


class ParityLevel(LookupBase):
    """``required`` / ``adjacent``."""

    class Meta(LookupBase.Meta):
        verbose_name = "parity level"
        verbose_name_plural = "parity levels"


class Section(LookupBase):
    """The kind of a card's bulleted section (``scope`` / ``definition_of_done`` / ...)."""

    class Meta(LookupBase.Meta):
        verbose_name = "section"
        verbose_name_plural = "sections"


class CardReferenceKind(LookupBase):
    """Why one card points at another card."""

    class Meta(LookupBase.Meta):
        verbose_name = "card reference kind"
        verbose_name_plural = "card reference kinds"


class BoardDocKind(LookupBase):
    """The role a :class:`BoardDoc` section plays in the rendered board.

    ``preamble`` (the title + intro), ``reference`` (legend / scale / snapshot),
    ``column`` (a card-bearing column's heading + intro), or ``footer`` (release
    checklist / maintenance notes / link definitions).
    """

    class Meta(LookupBase.Meta):
        verbose_name = "board doc kind"
        verbose_name_plural = "board doc kinds"


# ---------------------------------------------------------------------------
# Version + spec
# ---------------------------------------------------------------------------


class TargetVersion(TimeStampedModel):
    """The ``X.Y.Z`` a card ships / is planned to ship in (the "target number")."""

    number = models.TextField(unique=True)
    milestone = models.ForeignKey(
        Milestone,
        related_name="target_versions",
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ["number"]
        verbose_name = "target version"
        verbose_name_plural = "target versions"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(number=""),
                name="target_version_number_required",
            ),
        ]

    def __str__(self):
        return f"{self.number} ({self.milestone.key})"


class SpecDoc(TimeStampedModel):
    """A spec file owned by exactly one kanban card."""

    card = models.OneToOneField(
        "Card",
        related_name="spec",
        on_delete=models.CASCADE,
    )
    name = models.TextField(unique=True)
    url = models.URLField(max_length=500)

    class Meta:
        verbose_name = "spec doc"
        verbose_name_plural = "spec docs"

    def __str__(self):
        return self.name


class TrackedPath(TimeStampedModel):
    """A repo-relative package/test path that kanban cards may link to.

    ``is_current`` marks paths that exist in the working tree today; rows with
    ``is_current=False`` are either historical (linked from ``done`` cards) or
    planned (linked from ``wip``/``todo`` cards). Directory paths end with
    ``/`` and carry ``is_directory=True``.
    """

    path = models.TextField(unique=True)
    is_current = models.BooleanField(default=True)
    is_directory = models.BooleanField(default=False)

    class Meta:
        ordering = ["path"]
        verbose_name = "tracked path"
        verbose_name_plural = "tracked paths"

    def __str__(self):
        return self.path


# ---------------------------------------------------------------------------
# Card + its edges
# ---------------------------------------------------------------------------


def format_card_id(
    *,
    status_key: str,
    milestone_key: str | None,
    number: int,
    version: str,
) -> str:
    """Render the canonical ``<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`` card id.

    Single source of truth for the id format. ``Card.card_id`` (and through it
    ``Card.__str__`` and the ``cardId`` GraphQL field) is the only caller; the
    KANBAN.md / KANBAN.html exporters read the rendered ``cardId`` field rather
    than recomputing the format, so the shape lives in exactly one place. The
    caller decides whether a milestone segment applies (pass ``None`` to omit).
    """
    parts = [status_key.upper()]
    if milestone_key:
        parts.append(milestone_key.upper())
    return f"{'-'.join(parts)}-{number:03d}-{version}"


class Card(TimeStampedModel):
    """One board card. Every categorical line is a foreign key into a lookup."""

    title = models.TextField(unique=True)
    # The NNN sequence number is intentionally unstable and recomputed when cards
    # reorder, but it is still globally unique on a board snapshot. Card
    # references should use ``title`` / ``slug``; the number exists for ordering.
    number = models.PositiveIntegerField(unique=True)

    status = models.ForeignKey(Status, related_name="cards", on_delete=models.PROTECT)
    milestone = models.ForeignKey(
        Milestone,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    target_version = models.ForeignKey(
        TargetVersion,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    priority = models.ForeignKey(
        Priority,
        null=True,
        blank=True,
        related_name="cards",
        on_delete=models.SET_NULL,
    )
    relative_size = models.ForeignKey(
        RelativeSize,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    planning_state = models.ForeignKey(
        PlanningState,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    planning_note = models.TextField(blank=True, default="")

    dependencies = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="dependents",
        blank=True,
    )
    parity = models.ManyToManyField(
        Upstream,
        through="ParityClaim",
        related_name="cards",
        blank=True,
    )
    labels = models.ManyToManyField(
        "Label",
        related_name="cards",
        blank=True,
    )
    glossary_terms = models.ManyToManyField(
        "glossary.GlossaryTerm",
        through="CardGlossaryTerm",
        related_name="kanban_cards",
        blank=True,
    )
    changed_files = models.ManyToManyField(
        TrackedPath,
        related_name="cards",
        blank=True,
    )

    class Meta:
        ordering = ["number"]
        verbose_name = "card"
        verbose_name_plural = "cards"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(number__gte=1),
                name="card_number_required",
            ),
        ]

    def __str__(self):
        return f"{self.card_id} - {self.title}"

    @property
    def card_id(self) -> str:
        """Canonical card id (e.g. ``WIP-ALPHA-030-0.0.9``) without the title.

        Derived, never stored. Exposed as the ``cardId`` GraphQL field and read
        by the KANBAN.md / KANBAN.html exporters, so the id format lives in one
        place (``format_card_id``). The milestone segment is dropped on shipped
        (``done``) cards, mirroring the card-id convention in the board preamble.
        """
        milestone_key = (
            self.milestone.key if (self.status.key != "done" and self.milestone_id) else None
        )
        return format_card_id(
            status_key=self.status.key,
            milestone_key=milestone_key,
            number=self.number,
            version=self.target_version.number,
        )

    @property
    def slug(self) -> str:
        """Stable, link-friendly id derived from the unique ``title``.

        Deep links into the dashboard use ``KANBAN.html#<slug>`` so a
        reference survives card reordering -- unlike the volatile ``number``.
        Not stored: it is a pure function of ``title`` (which is already unique),
        so there is nothing to keep in sync and no second column to migrate.
        """
        return slugify(self.title).replace("-", "_")

    @property
    def is_blocked(self) -> bool:
        """Whether this card is waiting on an unfinished ``blocked_by`` reference."""
        if self.pk is None or self.status.key == "done":
            return False
        return (
            self.outgoing_references.filter(kind__key__in=BLOCKING_REFERENCE_KIND_KEYS)
            .exclude(target_card__status__key="done")
            .exists()
        )


class CardReference(TimeStampedModel):
    """A normalized card-to-card reference parsed out of prose.

    ``Card.dependencies`` remains the compatibility/convenience M2M. This model
    preserves the richer data: the reference kind, the raw prose that contained
    it, and the position within the source card's reference list.
    """

    source_card = models.ForeignKey(
        Card,
        related_name="outgoing_references",
        on_delete=models.CASCADE,
    )
    target_card = models.ForeignKey(
        Card,
        related_name="incoming_references",
        on_delete=models.CASCADE,
    )
    kind = models.ForeignKey(
        CardReferenceKind,
        related_name="card_references",
        on_delete=models.PROTECT,
    )
    raw_text = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = [
            "source_card",
            "order",
        ]
        verbose_name = "card reference"
        verbose_name_plural = "card references"
        indexes = [
            models.Index(
                fields=[
                    "target_card",
                    "kind",
                ],
            ),
            models.Index(
                fields=[
                    "source_card",
                    "kind",
                ],
            ),
        ]

    def save(self, *args, **kwargs):
        """Assign a per-``source_card`` sequential ``order`` on insert.

        Replaces the former ``(source_card, source, order)`` DB unique
        constraint with app-level logic: ``order`` stays unique within a card
        by construction, so references keep a stable, collision-free display
        order without a database constraint (and without a per-card renumber
        migration when ``source`` was dropped).
        """
        if self._state.adding:
            manager = CardReference.objects
            if kwargs.get("using"):
                manager = manager.db_manager(kwargs["using"])
            last = manager.filter(source_card=self.source_card).aggregate(
                models.Max("order"),
            )["order__max"]
            self.order = 0 if last is None else last + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.source_card.title} -> {self.target_card.title} ({self.kind.key})"


class CardGlossaryTerm(TimeStampedModel):
    """A kanban card's ordered link to a canonical glossary term."""

    card = models.ForeignKey(
        Card,
        related_name="glossary_links",
        on_delete=models.CASCADE,
    )
    term = models.ForeignKey(
        "glossary.GlossaryTerm",
        related_name="kanban_card_links",
        on_delete=models.CASCADE,
    )
    raw_text = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = [
            "card",
            "order",
        ]
        verbose_name = "card glossary term"
        verbose_name_plural = "card glossary terms"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "card",
                    "term",
                ],
                name="unique_glossary_term_per_card",
            ),
            models.UniqueConstraint(
                fields=[
                    "card",
                    "order",
                ],
                name="unique_card_glossary_term_position",
            ),
        ]
        indexes = [
            models.Index(fields=["term"]),
            models.Index(
                fields=[
                    "card",
                    "order",
                ],
            ),
        ]

    def __str__(self):
        return f"{self.card.title} -> {self.term.title}"


class ParityClaim(TimeStampedModel):
    """A ``Card`` <-> ``Upstream`` edge carrying the parity ``level``."""

    card = models.ForeignKey(Card, related_name="parity_claims", on_delete=models.CASCADE)
    upstream = models.ForeignKey(Upstream, related_name="parity_claims", on_delete=models.PROTECT)
    level = models.ForeignKey(ParityLevel, related_name="parity_claims", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "parity claim"
        verbose_name_plural = "parity claims"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "card",
                    "upstream",
                ],
                name="unique_parity_per_card_upstream",
            ),
        ]

    def __str__(self):
        return f"{self.card.title} / {self.upstream.key} ({self.level.key})"


class CardItem(TimeStampedModel):
    """One bullet from a card's section (Scope / Definition of done / ...)."""

    card = models.ForeignKey(Card, related_name="items", on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name="items", on_delete=models.PROTECT)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    # Only meaningful for ``definition_of_done`` items.
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = [
            "card",
            "section",
            "order",
        ]
        verbose_name = "card item"
        verbose_name_plural = "card items"
        constraints = [
            # One bullet per (card, section, order). The importer's reconcile
            # step matches existing items on exactly this key.
            models.UniqueConstraint(
                fields=[
                    "card",
                    "section",
                    "order",
                ],
                name="unique_item_position_per_card",
            ),
        ]

    def __str__(self):
        return f"{self.card.title} \u00b7 {self.section.label}: {self.text[:40]}"


class Label(TimeStampedModel):
    """An optional cross-cutting tag (``security`` / ``dx`` / ...)."""

    key = models.SlugField(unique=True)
    color = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "label"
        verbose_name_plural = "labels"

    def __str__(self):
        return self.key


# ---------------------------------------------------------------------------
# Board document (the prose around the cards)
# ---------------------------------------------------------------------------


class BoardDoc(TimeStampedModel):
    """One ordered prose section of a repository document export.

    ``namespace`` partitions document exports such as ``kanban`` and
    ``glossary`` so both flows share one model instead of each app carrying a
    bespoke prose-section table. The kanban exporter also uses
    ``BoardDocCardReference`` for FK-backed card placeholders.
    """

    namespace = models.SlugField(default="kanban")
    key = models.SlugField()
    kind = models.ForeignKey(
        BoardDocKind,
        related_name="docs",
        on_delete=models.PROTECT,
    )
    title = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    body = models.TextField(blank=True, default="")
    include_heading = models.BooleanField(default=True)

    class Meta:
        ordering = [
            "namespace",
            "order",
        ]
        verbose_name = "board doc"
        verbose_name_plural = "board docs"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "namespace",
                    "key",
                ],
                name="unique_board_doc_key_per_namespace",
            ),
        ]

    def __str__(self):
        return self.title or self.key


class BoardDocCardReference(TimeStampedModel):
    """A card mention embedded in a board-prose document.

    ``BoardDoc.body`` stores placeholders such as ``{{card_ref:0}}`` instead of
    live card-id strings. The FK on this edge is the canonical source of truth,
    so prose references survive card renumbering and status/version moves.
    """

    doc = models.ForeignKey(
        BoardDoc,
        related_name="card_references",
        on_delete=models.CASCADE,
    )
    card = models.ForeignKey(
        Card,
        related_name="board_doc_references",
        on_delete=models.CASCADE,
    )
    raw_text = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = [
            "doc",
            "order",
        ]
        verbose_name = "board doc card reference"
        verbose_name_plural = "board doc card references"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "doc",
                    "order",
                ],
                name="unique_board_doc_card_reference_position",
            ),
        ]
        indexes = [
            models.Index(fields=["card"]),
        ]

    def __str__(self):
        return f"{self.doc} -> {self.card} ({self.order})"


# ---------------------------------------------------------------------------
# UUID side-table
# ---------------------------------------------------------------------------


# The O2O link field names on UUIDModel -- one per linked model. Kept in sync
# with ``_UUID_LINKED_MODELS`` (below): these names equal each model's
# ``_meta.model_name``.
_UUID_LINK_NAMES = (
    "milestone",
    "status",
    "priority",
    "relativesize",
    "planningstate",
    "upstream",
    "paritylevel",
    "section",
    "cardreferencekind",
    "boarddockind",
    "targetversion",
    "specdoc",
    "trackedpath",
    "card",
    "cardreference",
    "cardglossaryterm",
    "parityclaim",
    "carditem",
    "label",
    "boarddoc",
    "boarddoccardreference",
)


def _exactly_one_link_constraint() -> models.CheckConstraint:
    """Enforce the one-hot invariant: exactly one O2O link field is non-null.

    Makes the registry invariant real at the DB level rather than advisory, so
    admin / fixtures / future code cannot create empty or multi-linked rows that
    the ``post_save`` signal would never produce.
    """
    return models.CheckConstraint(
        condition=Exact(OneHotLinkCount(*_UUID_LINK_NAMES), models.Value(1)),
        name="kanban_uuidmodel_exactly_one_link",
    )


class UUIDModel(TimeStampedModel):
    """Central UUID registry: one row per object, linked O2O to every model.

    NOT an abstract mixin and NOT a ``uuid`` column on each model. The UUID
    primary key here is the stable identifier for whichever single domain row
    the (one non-null) one-to-one link points at; each domain row reaches it via
    the reverse accessor ``instance.uuid.id``. Field names match
    ``sender._meta.model_name`` so :func:`_create_uuid_row` needs no special
    casing. The one-hot invariant is enforced by a check constraint (see
    :func:`_exactly_one_link_constraint`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    milestone = models.OneToOneField(
        "Milestone",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    status = models.OneToOneField(
        "Status",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    priority = models.OneToOneField(
        "Priority",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    relativesize = models.OneToOneField(
        "RelativeSize",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    planningstate = models.OneToOneField(
        "PlanningState",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    upstream = models.OneToOneField(
        "Upstream",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    paritylevel = models.OneToOneField(
        "ParityLevel",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    section = models.OneToOneField(
        "Section",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    cardreferencekind = models.OneToOneField(
        "CardReferenceKind",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    boarddockind = models.OneToOneField(
        "BoardDocKind",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    targetversion = models.OneToOneField(
        "TargetVersion",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    specdoc = models.OneToOneField(
        "SpecDoc",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    trackedpath = models.OneToOneField(
        "TrackedPath",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    card = models.OneToOneField(
        "Card",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    cardreference = models.OneToOneField(
        "CardReference",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    cardglossaryterm = models.OneToOneField(
        "CardGlossaryTerm",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    parityclaim = models.OneToOneField(
        "ParityClaim",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    carditem = models.OneToOneField(
        "CardItem",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    label = models.OneToOneField(
        "Label",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    boarddoc = models.OneToOneField(
        "BoardDoc",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    boarddoccardreference = models.OneToOneField(
        "BoardDocCardReference",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )

    class Meta:
        verbose_name = "UUID"
        verbose_name_plural = "UUIDs"
        constraints = [_exactly_one_link_constraint()]

    def __str__(self):
        # Reference the single linked domain row (the one non-null O2O), if any.
        for name in _UUID_LINK_NAMES:
            if getattr(self, f"{name}_id") is not None:
                return f"{getattr(self, name)} <{self.id}>"
        return str(self.id)
