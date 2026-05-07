"""Unmanaged Django models covering relation cardinalities missing from fakeshop."""

from django.db import models


class User(models.Model):
    """One-to-one target model."""

    name = models.TextField()

    class Meta:
        app_label = "tests_cardinality"
        managed = False


class Profile(models.Model):
    """Forward OneToOne model pointing at ``User``."""

    user = models.OneToOneField(
        User,
        related_name="profile",
        on_delete=models.CASCADE,
    )
    bio = models.TextField()

    class Meta:
        app_label = "tests_cardinality"
        managed = False


class Author(models.Model):
    """Book author model."""

    name = models.TextField()

    class Meta:
        app_label = "tests_cardinality"
        managed = False


class Tag(models.Model):
    """Many-to-many target model."""

    name = models.TextField()

    class Meta:
        app_label = "tests_cardinality"
        managed = False


class Book(models.Model):
    """Book model with FK and M2M relations."""

    title = models.TextField()
    author = models.ForeignKey(
        Author,
        related_name="books",
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="books",
    )

    class Meta:
        app_label = "tests_cardinality"
        managed = False
