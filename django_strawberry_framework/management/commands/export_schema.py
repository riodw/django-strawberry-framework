"""manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol."""

import pathlib

from django.core.management.base import BaseCommand, CommandError, CommandParser
from strawberry import Schema
from strawberry.printer import print_schema

from django_strawberry_framework.management.commands._imports import (
    import_module_symbol_or_command_error,
)


class Command(BaseCommand):
    """Export the GraphQL SDL for a strawberry.Schema symbol."""

    help = "Export the GraphQL schema"

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional schema argument and the optional --path flag."""
        parser.add_argument("schema", type=str, help="The schema location")
        parser.add_argument(
            "--path",
            type=str,
            help="Write UTF-8 SDL to this file, overwriting it without prompting",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Resolve the dotted-path schema symbol and emit SDL.

        Routes through three branches: ``--path`` omitted prints SDL to
        stdout (byte-identical to ``print_schema`` / ``--path`` file bytes,
        with Django's default trailing newline suppressed); ``--path`` with
        an empty or whitespace-only value raises ``CommandError`` with
        "--path requires a non-empty value"; ``--path <file>`` writes UTF-8
        SDL to the named path. A bare ``--path`` with no following value is
        rejected earlier by argparse, before ``handle`` runs. A non-empty
        target is encoded as UTF-8 and replaced without prompting.
        """
        schema_symbol = import_module_symbol_or_command_error(
            options["schema"],
            default_symbol_name="schema",
        )

        if not isinstance(schema_symbol, Schema):
            raise CommandError("The `schema` must be an instance of strawberry.Schema")

        schema_output = print_schema(schema_symbol)
        path = options.get("path")
        if path is None:
            # Match ``Path.write_text`` / ``print_schema`` bytes exactly: Django's
            # OutputWrapper defaults ``ending="\n"``, which would diverge stdout
            # from ``--path`` by a trailing newline and break redirect-vs-file diffs.
            self.stdout.write(schema_output, ending="")
            return
        if not isinstance(path, str) or not path.strip():
            raise CommandError("--path requires a non-empty value")
        try:
            pathlib.Path(path).write_text(schema_output, encoding="utf-8")
        except OSError as e:
            raise CommandError(str(e)) from e
        self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))
