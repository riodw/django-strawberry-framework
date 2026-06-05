"""TODO scaffold for the spec-029 inspect_django_type command.

Pseudo:
    Command.handle imports --schema with import_module_symbol(..., default_symbol_name="schema"),
    resolves dotted type arguments with import_string, resolves bare names through a unique
    registry.iter_types() match, verifies __django_strawberry_definition__ exists and is
    finalized, then prints rows from definition.selected_fields and origin.__annotations__,
    with a Relay-suppressed primary-key special case that reports the interface-supplied
    GlobalID row instead of indexing origin.__annotations__.
"""

from django.core.management.base import BaseCommand, CommandError, CommandParser


class Command(BaseCommand):
    """Fail-loud placeholder for the planned ``inspect_django_type`` command."""

    help = "Inspect DjangoType field-resolution metadata (planned by spec-029)"

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the future command's public argument shape."""
        parser.add_argument("type", type=str, help="DjangoType name or fully-dotted object path")
        parser.add_argument("--schema", type=str, help="Optional schema selector to import first")

    def handle(self, *args: object, **options: object) -> None:
        """Fail loudly until spec-029 Slice 2 implements the command."""
        raise CommandError(
            "inspect_django_type is planned by "
            "docs/spec-029-consumer_dx_cleanup-0_0_9.md Slice 2 and is not implemented yet.",
        )
