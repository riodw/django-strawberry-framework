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

import operator
import uuid
from functools import reduce

from django.db import models
from django.db.models.lookups import Exact
from django.utils.text import slugify

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
    """The card workflow state that drives board placement: ``todo`` / ``wip`` / ``done``."""

    class Meta(LookupBase.Meta):
        verbose_name = "status"
        verbose_name_plural = "statuses"


class Priority(LookupBase):
    """``high`` / ``medium`` / ``low``."""

    class Meta(LookupBase.Meta):
        verbose_name = "priority"
        verbose_name_plural = "priorities"


class Severity(LookupBase):
    """``major`` / ``medium`` / ``low``."""

    class Meta(LookupBase.Meta):
        verbose_name = "severity"
        verbose_name_plural = "severities"


class RelativeSize(LookupBase):
    """T-shirt size: ``xs`` / ``s`` / ``m`` / ``l`` / ``xl``."""

    rank = models.PositiveIntegerField(default=0)

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


class CardReferenceSource(LookupBase):
    """Where the importer found a card-to-card reference in the board source."""

    class Meta(LookupBase.Meta):
        verbose_name = "card reference source"
        verbose_name_plural = "card reference sources"


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
    """A spec file: just a name and a link to it on GitHub."""

    # Unique: the importer upserts a spec by name, and a spec maps to one card.
    name = models.TextField(unique=True)
    url = models.URLField(max_length=500)

    class Meta:
        verbose_name = "spec doc"
        verbose_name_plural = "spec docs"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Card + its edges
# ---------------------------------------------------------------------------


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
    severity = models.ForeignKey(
        Severity,
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
    # Only set for ranges ("S–M"); a second FK into the same lookup.
    relative_size_high = models.ForeignKey(
        RelativeSize,
        null=True,
        blank=True,
        related_name="cards_high",
        on_delete=models.SET_NULL,
    )
    planning_state = models.ForeignKey(
        PlanningState,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    planning_note = models.TextField(blank=True, default="")

    spec = models.OneToOneField(
        SpecDoc,
        null=True,
        blank=True,
        related_name="card",
        on_delete=models.SET_NULL,
    )

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
        milestone = ""
        if self.status.key != "done" and self.milestone_id:
            milestone = f"-{self.milestone.key.upper()}"
        return f"{self.status.key.upper()}{milestone}-{self.number:03d}-{self.target_version.number} — {self.title}"

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
    preserves the richer source data: the reference kind, where it came from,
    the raw prose that contained it, and the position within that source.
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
    source = models.ForeignKey(
        CardReferenceSource,
        related_name="card_references",
        on_delete=models.PROTECT,
    )
    raw_text = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = [
            "source_card",
            "source",
            "order",
        ]
        verbose_name = "card reference"
        verbose_name_plural = "card references"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source_card",
                    "source",
                    "order",
                ],
                name="unique_card_reference_position",
            ),
        ]
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

    def __str__(self):
        return f"{self.source_card.title} -> {self.target_card.title} ({self.kind.key})"


class ParityClaim(TimeStampedModel):
    """A ``Card`` ↔ ``Upstream`` edge carrying the parity ``level``."""

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
        return f"{self.card.title} · {self.section.label}: {self.text[:40]}"


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
    """One ordered prose section of the board document -- everything in the
    board that is not a card.

    The card-ID-format legend, the relative-size scale, the snapshot narrative,
    each column's intro, the release checklist, and the maintenance notes all
    live here as ordered markdown. Storing them in the DB lets the same data
    drive the HTML dashboard and regenerate a ``KANBAN.md`` file from the board.
    """

    key = models.SlugField(unique=True)
    kind = models.ForeignKey(
        BoardDocKind,
        related_name="docs",
        on_delete=models.PROTECT,
    )
    title = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    body = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["order"]
        verbose_name = "board doc"
        verbose_name_plural = "board docs"

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
    "severity",
    "relativesize",
    "planningstate",
    "upstream",
    "paritylevel",
    "section",
    "cardreferencekind",
    "cardreferencesource",
    "boarddockind",
    "targetversion",
    "specdoc",
    "card",
    "cardreference",
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
    non_null_count = reduce(
        operator.add,
        (
            models.Case(
                models.When(**{f"{name}__isnull": False}, then=1),
                default=0,
                output_field=models.IntegerField(),
            )
            for name in _UUID_LINK_NAMES
        ),
    )
    return models.CheckConstraint(
        condition=Exact(non_null_count, models.Value(1)),
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
    severity = models.OneToOneField(
        "Severity",
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
    cardreferencesource = models.OneToOneField(
        "CardReferenceSource",
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
