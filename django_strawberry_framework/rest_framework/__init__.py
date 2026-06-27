# ruff: noqa: D104

# TODO(spec-039 Slice 2): Replace this placeholder with the DRF soft-dependency
# guard and lazy serializer-mutation export.
# Pseudo flow:
#   - Keep one DRF install hint string in this module.
#   - `require_drf()` imports `rest_framework`, returns it when present, and wraps
#     an absent dependency in the guarded install-hint `ImportError`.
#   - All serializer-mutation modules call this guard before importing DRF classes.
#
# Import contract:
#   - `import django_strawberry_framework` succeeds without DRF.
#   - `from django_strawberry_framework import SerializerMutation` raises this
#     guarded `ImportError` when DRF is absent.
#   - `import django_strawberry_framework.rest_framework` also raises the same
#     guarded `ImportError` when DRF is absent.
