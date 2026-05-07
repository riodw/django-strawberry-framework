"""Managed models for library acceptance coverage."""

from django.db import models


class Branch(models.Model):
    """A physical library branch that owns shelves."""

    name = models.TextField(unique=True)
    city = models.TextField(blank=True, default="")

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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "code"],
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
                fields=["shelf", "title"],
                name="unique_book_title_per_shelf",
            ),
        ]

    def __str__(self):
        return self.title


class Patron(models.Model):
    """A library patron who can borrow books."""

    name = models.TextField(unique=True)

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
                fields=["book", "patron"],
                name="unique_open_loan_per_book_patron",
            ),
        ]

    def __str__(self):
        return f"{self.book} to {self.patron}"
