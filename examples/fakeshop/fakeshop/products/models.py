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
                fields=["category", "name"],
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
                fields=["category", "name"],
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
    property = models.ForeignKey(  # noqa: A003
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
                fields=["item", "property"],
                name="unique_entry_per_item_property",
            ),
        ]

    def __str__(self):
        return self.value
