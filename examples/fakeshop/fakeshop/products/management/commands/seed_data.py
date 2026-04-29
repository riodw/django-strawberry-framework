from django.core.management.base import BaseCommand
from fakeshop.products.services import seed_data


class Command(BaseCommand):
    help = "Ensures at least N items exist per Faker provider (only creates the shortfall)"

    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            nargs="?",
            type=int,
            default=5,
            help="Desired number of items per provider (default is 5)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        self.stdout.write(self.style.NOTICE(f"Ensuring {count} items per Faker provider..."))

        result = seed_data(count)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {result['categories']} categories, "
                f"{result['properties']} properties, "
                f"{result['items']} items, "
                f"{result['entries']} entries.",
            ),
        )
