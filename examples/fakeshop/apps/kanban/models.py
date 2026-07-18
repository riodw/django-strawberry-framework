"""Relational source of truth for this repository's ``KANBAN.md`` and ``KANBAN.html`` exports.

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
from django.utils import timezone
from django.utils.text import slugify

from .constraints import OneHotLinkCount

DEPENDENCY_REFERENCE_KIND_KEYS = frozenset(
    {
        "blocked_by",
        "dependency",
    },
)
BLOCKING_REFERENCE_KIND_KEYS = frozenset({"blocked_by"})

# Card workflow status keys referenced by derived state (is_blocked / is_ready).
DONE_STATUS_KEY = "done"
TODO_STATUS_KEY = "todo"

# The GitHub blob prefix a SpecDoc URL is derived from. The DB stores the
# repo-relative ``path``; ``SpecDoc.url`` composes the full URL at read time so
# a repo rename or branch move is a one-line change here, not a data migration.
SPEC_URL_PREFIX = "https://github.com/riodw/django-strawberry-framework/blob/main"

# TrackedPath lifecycle states (replaces the earlier ``is_current`` boolean).
TRACKED_PATH_CURRENT = "current"
TRACKED_PATH_HISTORICAL = "historical"
TRACKED_PATH_PLANNED = "planned"
TRACKED_PATH_STATES = (
    (
        TRACKED_PATH_CURRENT,
        "Current",
    ),
    (
        TRACKED_PATH_HISTORICAL,
        "Historical",
    ),
    (
        TRACKED_PATH_PLANNED,
        "Planned",
    ),
)
TRACKED_PATH_STATE_KEYS = frozenset(state for state, _ in TRACKED_PATH_STATES)

# CardPathLink kinds: a done card records the files it ``changed``; a
# wip/todo card records the files it is ``predicted`` to touch.
CARD_PATH_LINK_CHANGED = "changed"
CARD_PATH_LINK_PREDICTED = "predicted"
CARD_PATH_LINK_KINDS = (
    (
        CARD_PATH_LINK_CHANGED,
        "Changed",
    ),
    (
        CARD_PATH_LINK_PREDICTED,
        "Predicted",
    ),
)
CARD_PATH_LINK_KIND_KEYS = frozenset(kind for kind, _ in CARD_PATH_LINK_KINDS)

# Actor kinds: who performed a tracked action -- a ``human`` maintainer or an
# ``agent`` session (matches the CardPathLink.kind CheckConstraint idiom).
ACTOR_HUMAN = "human"
ACTOR_AGENT = "agent"
ACTOR_KINDS = (
    (
        ACTOR_HUMAN,
        "Human",
    ),
    (
        ACTOR_AGENT,
        "Agent",
    ),
)
ACTOR_KIND_KEYS = frozenset(kind for kind, _ in ACTOR_KINDS)


def manager(
    model,
    using,
):
    """Return ``model.objects`` bound to ``using`` (or the default alias).

    The one shared home for the ``model.objects.using(alias)`` helper that
    ``services.py`` and ``signals.py`` both lean on, so the alias-aware manager
    lookup lives in exactly one place (models.py already hosts the shared
    ``DONE_STATUS_KEY`` constant; this follows that precedent).
    """
    return model.objects.using(using) if using else model.objects


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

    # The per-size effort blurb rendered as the ``## Relative size`` scale in
    # KANBAN.md / KANBAN.html, so the scale is derived from this table rather
    # than frozen in the board prose.
    description = models.TextField(blank=True, default="")

    class Meta(LookupBase.Meta):
        verbose_name = "relative size"
        verbose_name_plural = "relative sizes"


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


class AttemptOutcome(LookupBase):
    """How a :class:`WorkAttempt` ended (``succeeded`` / ``failed`` / ...).

    A null outcome on a WorkAttempt means the attempt is still in progress.
    """

    class Meta(LookupBase.Meta):
        verbose_name = "attempt outcome"
        verbose_name_plural = "attempt outcomes"


class VerificationKind(LookupBase):
    """How a :class:`CardItem` was verified (``test_run`` / ``coverage_gate`` / ...)."""

    class Meta(LookupBase.Meta):
        verbose_name = "verification kind"
        verbose_name_plural = "verification kinds"


class Actor(LookupBase):
    """Who performed a tracked action: a human maintainer or an agent session.

    ``LookupBase``-shaped (``key`` / ``label`` / ``order``) with an added
    ``kind`` slug constrained to ``human`` / ``agent`` (the CardPathLink.kind
    CheckConstraint idiom). Essential provenance given the confirmed parallel
    agent sessions writing the same board.
    """

    kind = models.SlugField(choices=ACTOR_KINDS, default=ACTOR_HUMAN)

    class Meta(LookupBase.Meta):
        verbose_name = "actor"
        verbose_name_plural = "actors"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=sorted(ACTOR_KIND_KEYS)),
                name="actor_kind_valid",
            ),
        ]


# ---------------------------------------------------------------------------
# Version + spec
# ---------------------------------------------------------------------------


class TargetVersion(TimeStampedModel):
    """The ``X.Y.Z`` a card ships / is planned to ship in (the "target number")."""

    number = models.TextField(unique=True)
    # Structured ``X.Y.Z`` components kept consistent with ``number`` in
    # ``save()``. ``number`` stays canonical (the display string); the triple
    # exists so ordering is numeric (0.0.9 < 0.0.16, which a lexicographic sort
    # of ``number`` gets wrong at patch >= 10).
    major = models.PositiveIntegerField(default=0)
    minor = models.PositiveIntegerField(default=0)
    patch = models.PositiveIntegerField(default=0)
    milestone = models.ForeignKey(
        Milestone,
        related_name="target_versions",
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = [
            "major",
            "minor",
            "patch",
        ]
        verbose_name = "target version"
        verbose_name_plural = "target versions"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(number=""),
                name="target_version_number_required",
            ),
        ]

    @staticmethod
    def parse_version(number: str) -> tuple[int, int, int]:
        """Parse the leading ``X.Y.Z`` triple from a version string.

        Tolerant of trailing suffixes (``"1.0.0 (stable)"`` -> ``(1, 0, 0)``);
        missing segments default to ``0``.
        """
        parts = [
            0,
            0,
            0,
        ]
        for index, segment in enumerate(number.split(".")[:3]):
            digits = "".join(ch for ch in segment if ch.isdigit())
            parts[index] = int(digits) if digits else 0
        return parts[0], parts[1], parts[2]

    def save(self, *args, **kwargs):
        """Keep the ``major``/``minor``/``patch`` triple in sync with ``number``."""
        self.major, self.minor, self.patch = self.parse_version(self.number or "")
        super().save(*args, **kwargs)

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
    # Repo-relative path to the spec file. The GitHub URL is derived from it at
    # read time (see :attr:`url`), so a repo rename never needs a data migration.
    path = models.TextField(default="")

    class Meta:
        verbose_name = "spec doc"
        verbose_name_plural = "spec docs"

    @property
    def url(self) -> str:
        """Full GitHub blob URL, derived from the repo-relative ``path``."""
        return f"{SPEC_URL_PREFIX}/{self.path}"

    def __str__(self):
        return self.name


class TrackedPath(TimeStampedModel):
    """A repo-relative package/test path that kanban cards may link to.

    ``state`` is one of ``current`` (exists in the working tree today),
    ``historical`` (linked from ``done`` cards; the file once existed), or
    ``planned`` (linked from ``wip``/``todo`` cards; does not exist yet).
    Directory paths end with ``/`` and carry ``is_directory=True``.
    """

    path = models.TextField(unique=True)
    state = models.SlugField(choices=TRACKED_PATH_STATES, default=TRACKED_PATH_CURRENT)
    is_directory = models.BooleanField(default=False)

    class Meta:
        ordering = ["path"]
        verbose_name = "tracked path"
        verbose_name_plural = "tracked paths"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(state__in=sorted(TRACKED_PATH_STATE_KEYS)),
                name="tracked_path_state_valid",
            ),
        ]

    @property
    def is_current(self) -> bool:
        """Whether this path exists in the working tree today (``state=current``)."""
        return self.state == TRACKED_PATH_CURRENT

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
    target_version = models.ForeignKey(
        TargetVersion,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    priority = models.ForeignKey(
        Priority,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    relative_size = models.ForeignKey(
        RelativeSize,
        related_name="cards",
        on_delete=models.PROTECT,
    )
    planning_note = models.TextField(blank=True, default="")

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
        through="CardPathLink",
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
    def milestone(self) -> Milestone:
        """The development phase, derived from the card's target version.

        A card's milestone is a pure function of its ``target_version`` (the
        version's ``milestone`` FK), so it is derived here rather than stored --
        removing a denormalized column that could drift out of sync.
        """
        return self.target_version.milestone

    @property
    def milestone_id(self) -> int | None:
        """The derived milestone's pk (mirrors the former FK's ``milestone_id``)."""
        return self.target_version.milestone_id if self.target_version_id else None

    @property
    def card_id(self) -> str:
        """Canonical card id (e.g. ``WIP-ALPHA-030-0.0.9``) without the title.

        Derived, never stored. Exposed as the ``cardId`` GraphQL field and read
        by the KANBAN.md / KANBAN.html exporters, so the id format lives in one
        place (``format_card_id``). The milestone segment is dropped on shipped
        (``done``) cards, mirroring the card-id convention in the board preamble.
        """
        milestone_key = (
            self.milestone.key if (self.status.key != "done" and self.target_version_id) else None
        )
        return format_card_id(
            status_key=self.status.key,
            milestone_key=milestone_key,
            number=self.number,
            version=self.target_version.number,
        )

    @property
    def dependency_cards(self) -> "models.QuerySet[Card]":
        """Cards this card depends on, over ``dependency``/``blocked_by`` references.

        Replaces the former ``dependencies`` M2M: ``CardReference`` is now the
        single source of truth for card-to-card edges.
        """
        return Card.objects.filter(
            incoming_references__source_card=self,
            incoming_references__kind__key__in=DEPENDENCY_REFERENCE_KIND_KEYS,
        ).distinct()

    @property
    def dependent_cards(self) -> "models.QuerySet[Card]":
        """Cards that depend on this card (the reverse of :attr:`dependency_cards`)."""
        return Card.objects.filter(
            outgoing_references__target_card=self,
            outgoing_references__kind__key__in=DEPENDENCY_REFERENCE_KIND_KEYS,
        ).distinct()

    # GraphQL-facing aliases (the ``dependencies`` / ``dependents`` fields on
    # CardType resolve from these) so existing queries keep their field names
    # after the ``dependencies`` M2M was replaced by CardReference edges.
    @property
    def dependencies(self) -> "models.QuerySet[Card]":
        """Alias of :attr:`dependency_cards` for the GraphQL ``dependencies`` field."""
        return self.dependency_cards

    @property
    def dependents(self) -> "models.QuerySet[Card]":
        """Alias of :attr:`dependent_cards` for the GraphQL ``dependents`` field."""
        return self.dependent_cards

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
        """Whether this card is waiting on an unfinished ``blocked_by`` reference.

        A ``blocked_by`` edge stops gating once it is ``resolved`` (its
        ``resolved_at`` is stamped when the target ships) or its target reaches
        ``done`` -- either condition clears the block.
        """
        if self.pk is None or self.status.key == DONE_STATUS_KEY:
            return False
        return (
            self.outgoing_references.filter(
                kind__key__in=BLOCKING_REFERENCE_KIND_KEYS,
                resolved_at__isnull=True,
            )
            .exclude(target_card__status__key=DONE_STATUS_KEY)
            .exists()
        )

    @property
    def is_ready(self) -> bool:
        """Whether this ``todo`` card can be started now.

        A card is ready when it is in ``todo``, is not blocked, and every card it
        depends on (``dependency`` / ``blocked_by`` outgoing edges) is ``done``.
        See ``Query.ready_cards`` for the annotated, N+1-free board query.
        """
        if self.pk is None or self.status.key != TODO_STATUS_KEY:
            return False
        return not (
            self.outgoing_references.filter(kind__key__in=DEPENDENCY_REFERENCE_KIND_KEYS)
            .exclude(target_card__status__key=DONE_STATUS_KEY)
            .exists()
        )


class CardReference(TimeStampedModel):
    """A normalized card-to-card reference parsed out of prose.

    The single source of truth for card-to-card edges. ``dependency`` /
    ``blocked_by`` kinds express dependency edges (surfaced via
    ``Card.dependency_cards`` / ``Card.dependent_cards``); other kinds are
    informational. Preserves the reference kind, the raw prose that contained
    it, and the position within the source card's reference list.

    Dependency semantics: a ``blocked_by`` edge *gates* the source card's
    :attr:`Card.is_blocked` until it is resolved, whereas a ``dependency`` edge
    is informational history. When the target card ships, the service layer
    stamps ``resolved_at`` on the incoming ``blocked_by`` edges (rather than
    retyping them) so the block clears while the edge history is preserved.
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
    # Stamped when a ``blocked_by`` edge stops gating because its target shipped
    # (set by ``services.set_card_status``). Null while the edge is still active.
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = [
            "source_card",
            "order",
        ]
        verbose_name = "card reference"
        verbose_name_plural = "card references"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "source_card",
                    "target_card",
                    "kind",
                ],
                name="unique_card_reference_edge",
            ),
            models.UniqueConstraint(
                fields=[
                    "source_card",
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


class CardPathLink(TimeStampedModel):
    """A ``Card`` <-> ``TrackedPath`` edge carrying the link ``kind``.

    The through model for ``Card.changed_files``. ``kind`` is ``changed`` on a
    done card (the files it actually changed) or ``predicted`` on a wip/todo
    card (the files it is predicted to touch), replacing the earlier
    reinterpretation of a bare M2M by the source card's status.
    """

    card = models.ForeignKey(Card, related_name="path_links", on_delete=models.CASCADE)
    path = models.ForeignKey(TrackedPath, related_name="card_links", on_delete=models.CASCADE)
    kind = models.SlugField(choices=CARD_PATH_LINK_KINDS, default=CARD_PATH_LINK_PREDICTED)

    class Meta:
        ordering = [
            "card",
            "path",
        ]
        verbose_name = "card path link"
        verbose_name_plural = "card path links"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "card",
                    "path",
                ],
                name="unique_card_path_link",
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=sorted(CARD_PATH_LINK_KIND_KEYS)),
                name="card_path_link_kind_valid",
            ),
        ]

    def __str__(self):
        return f"{self.card.title} -> {self.path.path} ({self.kind})"


class CardItem(TimeStampedModel):
    """One bullet from a card's section (Scope / Definition of done / ...)."""

    card = models.ForeignKey(Card, related_name="items", on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name="items", on_delete=models.PROTECT)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    # A general per-bullet checkbox: whether this bullet is done. Meaningful for
    # any section, not only ``definition_of_done`` items (the board tracks
    # completion of scope, test-plan, and other bullets the same way).
    is_complete = models.BooleanField(default=False)
    # Auditable verification state layered over the bare ``is_complete`` bool:
    # when a bullet was verified, by which actor, and how (test run / coverage
    # gate / manual / live query). Null until the bullet is verified.
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "Actor",
        related_name="verified_items",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    verification_kind = models.ForeignKey(
        "VerificationKind",
        related_name="card_items",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

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
# Work-tracking dimension (transitions / attempts / decisions)
# ---------------------------------------------------------------------------


class CardTransition(TimeStampedModel):
    """A durable record of a card moving from one status to another.

    Written atomically by ``services.set_card_status``: the single
    highest-value work-tracking addition, a history of when work moved and who
    moved it. ``from_status`` is null for a card's first recorded transition.
    """

    card = models.ForeignKey(Card, related_name="transitions", on_delete=models.CASCADE)
    from_status = models.ForeignKey(
        Status,
        related_name="transitions_from",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    to_status = models.ForeignKey(
        Status,
        related_name="transitions_to",
        on_delete=models.PROTECT,
    )
    actor = models.ForeignKey(Actor, related_name="transitions", on_delete=models.PROTECT)
    note = models.TextField(blank=True, default="")
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = [
            "card",
            "occurred_at",
        ]
        verbose_name = "card transition"
        verbose_name_plural = "card transitions"

    def __str__(self):
        origin = self.from_status.key if self.from_status_id else "(new)"
        return f"{self.card.title}: {origin} -> {self.to_status.key}"


class WorkAttempt(TimeStampedModel):
    """One try at making progress on a card, across a session boundary.

    Lets an agent record tries, failures, and retries durably. A null
    ``outcome`` means the attempt is still in progress; ``ended_at`` is null
    until it finishes.
    """

    card = models.ForeignKey(Card, related_name="work_attempts", on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, related_name="work_attempts", on_delete=models.PROTECT)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    outcome = models.ForeignKey(
        AttemptOutcome,
        related_name="work_attempts",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    summary = models.TextField(blank=True, default="")
    evidence = models.TextField(blank=True, default="")

    class Meta:
        ordering = [
            "card",
            "started_at",
        ]
        verbose_name = "work attempt"
        verbose_name_plural = "work attempts"

    def __str__(self):
        outcome = self.outcome.key if self.outcome_id else "in-progress"
        return f"{self.card.title} attempt ({outcome})"


class Decision(TimeStampedModel):
    """A recorded design decision, board-level or scoped to a card.

    Replaces decisions rotting in ``planning_note`` / ``other`` bullets. ``card``
    is null for board-level decisions; ``supersedes`` links a decision to the
    earlier one it replaces (surfaced in reverse as ``superseded_by_set``).
    """

    card = models.ForeignKey(
        Card,
        related_name="decisions",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    actor = models.ForeignKey(Actor, related_name="decisions", on_delete=models.PROTECT)
    question = models.TextField()
    choice = models.TextField()
    rationale = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(default=timezone.now)
    supersedes = models.ForeignKey(
        "self",
        related_name="superseded_by_set",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = [
            "decided_at",
        ]
        verbose_name = "decision"
        verbose_name_plural = "decisions"

    def __str__(self):
        return f"{self.question[:40]} -> {self.choice[:40]}"


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
    "cardpathlink",
    "carditem",
    "label",
    "boarddoc",
    "boarddoccardreference",
    "attemptoutcome",
    "verificationkind",
    "actor",
    "cardtransition",
    "workattempt",
    "decision",
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
    cardpathlink = models.OneToOneField(
        "CardPathLink",
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
    attemptoutcome = models.OneToOneField(
        "AttemptOutcome",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    verificationkind = models.OneToOneField(
        "VerificationKind",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    actor = models.OneToOneField(
        "Actor",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    cardtransition = models.OneToOneField(
        "CardTransition",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    workattempt = models.OneToOneField(
        "WorkAttempt",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uuid",
    )
    decision = models.OneToOneField(
        "Decision",
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
