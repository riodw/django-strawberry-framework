"""Create permission-shaped products test users for admin and API access checks."""

from django.core.management.base import BaseCommand, CommandParser
from typing_extensions import override

from apps.products.services import TEST_USER_PASSWORD, create_users


class Command(BaseCommand):
    help = (
        "Create test users with individual model-view permissions. "
        "Each unit creates 5 users: 1 staff + 4 per-permission users."
    )

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "count",
            nargs="?",
            type=int,
            default=1,
            help="Number of user sets to create (default is 1 = 5 users)",
        )

    @override
    def handle(self, *args: object, count: int, **options: object) -> None:
        self.stdout.write(self.style.NOTICE(f"Creating {count} set(s) of test users..."))

        result = create_users(count)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {result['users']} users. Password for all: {TEST_USER_PASSWORD}",
            ),
        )
