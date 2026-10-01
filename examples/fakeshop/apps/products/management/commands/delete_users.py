"""Delete generated products test users without touching superusers."""

from django.core.management.base import BaseCommand, CommandParser
from typing_extensions import override

from apps.products.services import delete_users


class Command(BaseCommand):
    help = (
        "Delete test users (never deletes superusers). "
        "Pass an integer to delete the first N users, "
        'or "all" to delete all non-superusers.'
    )

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "target",
            type=str,
            help='Number of users to delete or "all"',
        )

    @override
    def handle(self, *args: object, target: str, **options: object) -> None:

        if target != "all":
            try:
                count = int(target)
                if count < 1:
                    self.stderr.write(self.style.ERROR("Count must be a positive integer."))
                    return
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(
                        f'Invalid target "{target}". Use a positive integer or "all".',
                    ),
                )
                return

        self.stdout.write(self.style.NOTICE(f"Deleting users (target={target})..."))

        result = delete_users(target)

        if result["users"]:
            self.stdout.write(self.style.SUCCESS(f"Deleted {result['users']} users."))
        else:
            self.stdout.write(self.style.WARNING("Nothing to delete."))
