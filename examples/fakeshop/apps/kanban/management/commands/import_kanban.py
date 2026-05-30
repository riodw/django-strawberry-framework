from django.core.management.base import BaseCommand

from apps.kanban.services import import_board


class Command(BaseCommand):
    help = "Parse the repo-root KANBAN.md into the kanban models (idempotent upsert by card title)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            dest="path",
            default=None,
            help="Path to a KANBAN.md to import (defaults to the repo-root board).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Importing KANBAN.md into the kanban app..."))
        result = import_board(path=options["path"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Done! {result['cards']} cards, "
                f"{result['target_versions']} versions, "
                f"{result['items']} items, "
                f"{result['parity_claims']} parity claims, "
                f"{result['card_references']} card references, "
                f"{result['dependency_edges']} dependency edges.",
            ),
        )
