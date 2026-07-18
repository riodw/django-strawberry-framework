"""manage.py import_card_predicted_files - DEPRECATED alias of import_card_files.

Deprecated: use ``import_card_files --kind predicted`` instead. This alias is a
thin subclass that pins ``--kind predicted`` and keeps the legacy
``predicted_files`` JSON key so existing hooks and producers do not break. See
``import_card_files`` for the full schema and behaviour (including planned-row
creation and DONE-card rejection).
"""

from apps.kanban import models
from apps.kanban.management.commands.import_card_files import Command as _ImportCardFilesCommand


class Command(_ImportCardFilesCommand):
    """Replace predicted-path links for non-DONE kanban cards (deprecated alias)."""

    help = "Deprecated: use import_card_files --kind predicted. Replace predicted-path links."

    fixed_kind = models.CARD_PATH_LINK_PREDICTED
    files_key = "predicted_files"
