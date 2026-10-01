"""Seed Faker-backed products catalog rows up to a requested per-provider count."""

from django.core.management.base import BaseCommand, CommandParser
from typing_extensions import override

from apps.products.services import seed_data


class Command(BaseCommand):
    help = "Ensures at least N items exist per Faker provider (only creates the shortfall)"

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "count",
            nargs="?",
            type=int,
            default=5,
            help="Desired number of items per provider (default is 5)",
        )

    @override
    def handle(self, *args: object, count: int, **options: object) -> None:
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
