"""Management command implementations for django-strawberry-framework."""

# TODO spec-018 Slice 1: nothing else lives here. Django's command-discovery
# walks `<app>.management.commands.*` for every installed app and imports each
# module by name. The actual `Command` lives in `export_schema.py`; this file
# only marks the directory as a Python package per Decision 1 of
# `docs/spec-018-export_schema-0_0_7.md`.
