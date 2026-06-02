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
        parser.add_argument("schema", type=str, help="The schema location")
        parser.add_argument(
            "--path",
            type=str,
            help="Optional file path to write the SDL to; rejects empty values",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Resolve the dotted-path schema symbol and emit SDL.

        Routes through three branches: ``--path`` omitted prints SDL to
        stdout; ``--path ""`` (empty-string value) raises ``CommandError``
        per the ``CHANGELOG.md`` ``[0.0.7] Changed`` "manage.py
        export_schema --path now requires a value when the flag is given"
        contract; ``--path <file>`` writes UTF-8 SDL to the named path.
        """
        try:
            schema_symbol = import_module_symbol(
                options["schema"],
                default_symbol_name="schema",
            )
        except (ImportError, AttributeError) as e:
            raise CommandError(str(e)) from e

        if not isinstance(schema_symbol, Schema):
            raise CommandError("The `schema` must be an instance of strawberry.Schema")

        schema_output = print_schema(schema_symbol)
        path = options.get("path")
        if path is None:
            self.stdout.write(schema_output)
            return
        if not path:
            raise CommandError("--path requires a non-empty value")
        try:
            pathlib.Path(path).write_text(schema_output, encoding="utf-8")
        except OSError as e:
            raise CommandError(str(e)) from e
        self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))
