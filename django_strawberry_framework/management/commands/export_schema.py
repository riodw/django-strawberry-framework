"""manage.py export_schema — print or write the GraphQL SDL for a Strawberry schema symbol."""

import pathlib

from django.core.management.base import BaseCommand, CommandError, CommandParser
from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol


class Command(BaseCommand):
    """Export the GraphQL SDL for a strawberry.Schema symbol."""

    help = "Export the GraphQL schema"

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional schema argument and the optional --path flag."""
        parser.add_argument("schema", nargs=1, type=str, help="The schema location")
        parser.add_argument(
            "--path",
            nargs="?",
            type=str,
            help="Optional path to export",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""
        try:
            schema_symbol = import_module_symbol(
                options["schema"][0],
                default_symbol_name="schema",
            )
        except (ImportError, AttributeError) as e:
            raise CommandError(str(e)) from e

        if not isinstance(schema_symbol, Schema):
            raise CommandError("The `schema` must be an instance of strawberry.Schema")

        schema_output = print_schema(schema_symbol)
        path = options.get("path")
        if path:
            pathlib.Path(path).write_text(schema_output, encoding="utf-8")
        else:
            self.stdout.write(schema_output)
