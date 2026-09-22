"""Faker-shaped product catalog.

The four models mirror Faker's own structure so that ``seed_data`` can
walk Faker's providers and methods to populate the catalog:

* ``Category``  -- one row per Faker provider (e.g. ``bank``, ``person``).
* ``Property``  -- one row per Faker method on a provider (e.g. ``iban``,
                   ``first_name``).  Each property belongs to a category.
* ``Item``      -- one row per generated instance.  Each item belongs to a
                   category; many items per category.
* ``Entry``     -- one row per (item, property) pair.  An entry is the
                   value Faker produced for that property on that item.

``ItemHold`` sits outside the Faker walk: ``seed_data`` never creates one. It is
the catalog's guarded reference, a hold that keeps an item from being deleted
while it stands.
"""

from django.db import models


class Category(models.Model):
    """A Faker provider (e.g. ``bank``, ``person``, ``address``)."""

    name = models.TextField(unique=True)
    description = models.TextField(
        blank=True,
        default="",
    )
    is_private = models.BooleanField(default=False)
    created_date = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )
    updated_date = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Item(models.Model):
    """A generated instance produced from a category's Faker provider."""

    name = models.TextField()
    description = models.TextField(
        blank=True,
        default="",
    )
    category = models.ForeignKey(
        Category,
        related_name="items",
        on_delete=models.CASCADE,
    )
    # Optional file column for the form-mutation multipart ``Upload`` test surface
    # (spec-038). Nullable / blank so existing ``seed_data`` /
    # ``Item.objects.create`` calls are unaffected, and a plain ``FileField`` (not
    # ``ImageField``) since the routing proof needs no image dimensions / Pillow.
    # ``upload_to`` mirrors ``scalars/models.py::MediaSpecimen`` (SQLite-compatible -
    # the relative name stores as ``TEXT``).
    attachment = models.FileField(
        upload_to="product_media/",
        null=True,
        blank=True,
    )
    is_private = models.BooleanField(default=False)
    created_date = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )
    updated_date = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "category",
                    "name",
                ],
                name="unique_item_per_category",
            ),
        ]

    def __str__(self):
        return self.name


class Property(models.Model):
    """A Faker method on a category's provider (e.g. ``iban``, ``first_name``)."""

    name = models.TextField()
    description = models.TextField(
        blank=True,
        default="",
    )
    category = models.ForeignKey(
        Category,
        related_name="properties",
        on_delete=models.CASCADE,
    )
    is_private = models.BooleanField(default=False)
    created_date = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )
    updated_date = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "category",
                    "name",
                ],
                name="unique_property_per_category",
            ),
        ]

    def __str__(self):
        return self.name


class Entry(models.Model):
    """The value Faker produced for one ``(item, property)`` pair."""

    value = models.TextField()
    description = models.TextField(
        blank=True,
        default="",
    )
    property = models.ForeignKey(
        Property,
        related_name="entries",
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        Item,
        related_name="entries",
        on_delete=models.CASCADE,
    )
    is_private = models.BooleanField(default=False)
    created_date = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )
    updated_date = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Entry"
        verbose_name_plural = "Entries"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "item",
                    "property",
                ],
                name="unique_entry_per_item_property",
            ),
        ]

    def __str__(self):
        return self.value


class ItemHold(models.Model):
    """A hold on an item: while it stands, the held item cannot be deleted.

    ``item`` is ``on_delete=PROTECT`` and ``substitute`` is ``on_delete=RESTRICT``,
    so ``deleteItem`` on a held or substituting item is refused by Django's
    deletion collector. ``item`` is ``blank=True`` with ``null=False``: it may be
    left out of a submission, but a hold row cannot exist without one, so an
    explicit ``null`` is a field error rather than a silent skip past
    ``full_clean`` into a NOT NULL violation.
    """

    reason = models.TextField()
    item = models.ForeignKey(
        Item,
        related_name="holds",
        on_delete=models.PROTECT,
        blank=True,
    )
    substitute = models.ForeignKey(
        Item,
        related_name="substitute_holds",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Item hold"
        verbose_name_plural = "Item holds"

    def __str__(self):
        return self.reason
