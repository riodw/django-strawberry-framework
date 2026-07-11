"""Managed models for library acceptance coverage."""

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class TaggedItem(models.Model):
    """A generic tag attached to any library-domain object."""

    tag = models.SlugField()
    content_type = models.ForeignKey(
        ContentType,
        related_name="library_tagged_items",
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "content_type",
                    "object_id",
                ],
                name="library_tagged_lookup_idx",
            ),
        ]

    def __str__(self):
        return self.tag


class Branch(models.Model):
    """A physical library branch that owns shelves."""

    name = models.TextField(unique=True)
    city = models.TextField(blank=True, default="")
    # Test substrate: package tests use this virtual relation to pin
    # GenericRelation support without exposing it in the public example schema.
    tags = GenericRelation(
        TaggedItem,
    )

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return self.name


class Shelf(models.Model):
    """A shelf inside a branch."""

    code = models.TextField()
    topic = models.TextField(blank=True, default="")
    branch = models.ForeignKey(
        Branch,
        related_name="shelves",
        on_delete=models.CASCADE,
    )
    # A shelf's additional/alternate branches. Exists to exercise a raw-pk M2M
    # relation input over a LIVE /graphql request: the M2M target is the non-Relay
    # ``BranchType`` primary, so the generated input is a raw pk list (not a
    # GlobalID), and the form/model mutations decode it through the same
    # visibility-scoped get_queryset path the single FK uses. Optional.
    alt_branches = models.ManyToManyField(
        Branch,
        blank=True,
        related_name="alt_shelves",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "branch",
                    "code",
                ],
                name="unique_shelf_code_per_branch",
            ),
        ]

    def __str__(self):
        return self.code


class Genre(models.Model):
    """A genre used to group books."""

    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    """A shelved book with circulation state and genres."""

    class CirculationStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        CHECKED_OUT = "checked_out", "Checked out"
        REPAIR = "repair", "Repair"

    title = models.TextField()
    subtitle = models.TextField(blank=True, null=True)
    circulation_status = models.CharField(
        max_length=20,
        choices=CirculationStatus.choices,
        default=CirculationStatus.AVAILABLE,
    )
    shelf = models.ForeignKey(
        Shelf,
        related_name="books",
        on_delete=models.CASCADE,
    )
    genres = models.ManyToManyField(
        Genre,
        related_name="books",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "shelf",
                    "title",
                ],
                name="unique_book_title_per_shelf",
            ),
        ]

    def __str__(self):
        return self.title


class Patron(models.Model):
    """A library patron who can borrow books."""

    name = models.TextField(unique=True)
    email = models.TextField(blank=True, default="")
    # Signed 64-bit counter exercising the package's ``BigIntegerField -> BigInt``
    # converter entry end-to-end. Cents so values past 2^31-1 are realistic
    # for a long-running patron (>$21M in lifetime fines is plausible only as
    # a stress value, which is exactly the point - proves the wire format
    # survives values outside JSON's safe-integer range).
    lifetime_fines_cents = models.BigIntegerField(default=0)

    def __str__(self):
        return self.name


class MembershipCard(models.Model):
    """One-to-one membership card for a patron."""

    patron = models.OneToOneField(
        Patron,
        related_name="card",
        on_delete=models.CASCADE,
    )
    barcode = models.TextField(unique=True)

    def __str__(self):
        return self.barcode


class Periodical(models.Model):
    """A periodical whose issues paginate with keyset (value) cursors."""

    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Issue(models.Model):
    """One issue of a periodical - the ``Meta.cursor_field`` acceptance substrate.

    ``number`` is the non-nullable ordering column ``IssueType.Meta.cursor_field``
    anchors (``("-number", "id")`` - newest-first with the pk tiebreak, the
    canonical keyset feed shape and the mixed-direction seek arm); numbers
    repeat ACROSS periodicals so the uniform value-position semantics of a
    nested ``after:`` cursor are observable. ``embargoed`` drives the
    ``IssueType.get_queryset`` visibility hook (the permission-aware
    cursor-decode coverage: a cursor minted under staff visibility replays
    for anonymous viewers without leaking embargoed rows).
    """

    periodical = models.ForeignKey(
        Periodical,
        related_name="issues",
        on_delete=models.CASCADE,
    )
    number = models.IntegerField()
    title = models.TextField()
    embargoed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "periodical",
                    "number",
                ],
                name="unique_issue_number_per_periodical",
            ),
        ]

    def __str__(self):
        return self.title


class Loan(models.Model):
    """A checkout record connecting a patron to a book."""

    book = models.ForeignKey(
        Book,
        related_name="loans",
        on_delete=models.CASCADE,
    )
    patron = models.ForeignKey(
        Patron,
        related_name="loans",
        on_delete=models.CASCADE,
    )
    note = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "book",
                    "patron",
                ],
                name="unique_open_loan_per_book_patron",
            ),
        ]

    def __str__(self):
        return f"{self.book} to {self.patron}"
