from django.core.management.base import BaseCommand
from fakeshop.products.services import delete_data


class Command(BaseCommand):
    help = (
        "Delete data from the database. "
        "Pass an integer to delete the first N items, "
        '"all" to delete all items and entries, '
        'or "everything" to wipe all four tables.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "target",
            type=str,
            help='Number of items to delete, "all", or "everything"',
        )

    def handle(self, *args, **options):
        target = options["target"]

        # Validate: must be a positive int, "all", or "everything"
        if target not in ("all", "everything"):
            try:
                count = int(target)
                if count < 1:
                    self.stderr.write(self.style.ERROR("Count must be a positive integer."))
                    return
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(
                        f'Invalid target "{target}". Use a positive integer, "all", or "everything".',
                    ),
                )
                return

        self.stdout.write(self.style.NOTICE(f"Deleting data (target={target})..."))

        result = delete_data(target)

        parts = []
        if result["categories"]:
            parts.append(f"{result['categories']} categories")
        if result["properties"]:
            parts.append(f"{result['properties']} properties")
        if result["items"]:
            parts.append(f"{result['items']} items")
        if result["entries"]:
            parts.append(f"{result['entries']} entries")

        if parts:
            self.stdout.write(self.style.SUCCESS(f"Deleted {', '.join(parts)}."))
        else:
            self.stdout.write(self.style.WARNING("Nothing to delete."))
