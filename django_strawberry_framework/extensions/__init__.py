"""Strawberry schema extensions supplied by django-strawberry-framework."""

# TODO(spec-044 Slice 1): Re-export DjangoDebugExtension eagerly from
# ``.debug`` and list only that symbol in ``__all__`` once the implementation
# replaces the leaf's fail-loud planning stub. Keep the extension off the
# package root: the specialized, development-only opt-in is
# ``from django_strawberry_framework.extensions import DjangoDebugExtension``.
