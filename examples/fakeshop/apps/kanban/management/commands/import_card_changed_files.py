"""manage.py import_card_changed_files - DEPRECATED alias of import_card_files.

Deprecated: use ``import_card_files --kind changed`` instead. This alias is a
thin subclass that pins ``--kind changed`` and keeps the legacy ``changed_files``
JSON key so existing hooks and producers do not break. See
``import_card_files`` for the full schema and behaviour.
"""

from apps.kanban import models
from apps.kanban.management.commands.import_card_files import Command as _ImportCardFilesCommand


class Command(_ImportCardFilesCommand):
    """Replace changed-file links for existing kanban cards (deprecated alias)."""

    help = "Deprecated: use import_card_files --kind changed. Replace changed-file links."

    fixed_kind = models.CARD_PATH_LINK_CHANGED
    files_key = "changed_files"
