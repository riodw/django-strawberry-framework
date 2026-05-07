"""Expose unmanaged fixture models through Django's normal app-loading hook."""

from .cardinality_models import Author, Book, Profile, Tag, User

__all__ = ("Author", "Book", "Profile", "Tag", "User")
