"""Django management entry points for django-strawberry-framework."""

# TODO spec-018 Slice 1: nothing else lives here. This file exists only so Django's
# `manage.py` command discovery can import `django_strawberry_framework.management`
# while walking `INSTALLED_APPS` per Decision 1 of `docs/spec-018-export_schema-0_0_7.md`.
# Do NOT add re-exports — the actual command lives in `commands/export_schema.py`
# and is reached via `manage.py export_schema`, not via Python imports.
