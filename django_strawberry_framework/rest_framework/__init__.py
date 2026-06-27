# ruff: noqa: D104

# TODO(spec-039 Slice 2): Replace this placeholder with the DRF soft-dependency
# guard shared by every serializer-mutation module.
# Pseudo flow:
#   - Keep one DRF install hint string in this module.
#   - `require_drf()` imports `rest_framework`, returns it when present, and wraps
#     an absent dependency in the guarded install-hint `ImportError`.
#   - All serializer-mutation modules call this guard before importing DRF classes.
#   - This package may guard on import, but the root public name is resolved by
#     `django_strawberry_framework.__getattr__`; do not add a root `__all__` name.
#
# Import contract:
#   - `import django_strawberry_framework` succeeds without DRF.
#   - `from django_strawberry_framework import SerializerMutation` raises this
#     guarded `ImportError` when DRF is absent.
#   - `import django_strawberry_framework.rest_framework` also raises the same
#     guarded `ImportError` when DRF is absent.
#   - `from django_strawberry_framework import *` succeeds without DRF and binds
#     no `SerializerMutation`.
