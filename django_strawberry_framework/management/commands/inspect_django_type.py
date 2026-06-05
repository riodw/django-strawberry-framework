"""manage.py inspect_django_type — print a DjangoType's per-field GraphQL resolution table.

Diagnostic command that walks a finalized ``DjangoTypeDefinition`` and prints,
per selected field, the Django field name, the Django field type, the resolved
GraphQL type, its nullability, and which converter row fired. It is a strict
reader of the existing introspection surface — it reads the resolved GraphQL
annotation from ``origin.__annotations__`` (the authoritative post-finalize
record that already reflects ``Meta.nullable_overrides`` / ``required_overrides``
and consumer-authored annotations) rather than re-running ``convert_scalar``,
and re-walks ``SCALAR_MAP`` only to NAME which converter row fired.

The positional ``type`` argument dispatches by shape: a dotted object path
(``apps.library.schema.BookType``) resolves via Django's ``import_string`` and a
dotted import failure raises ``CommandError`` carrying the original error; a bare
name (``BookType``) resolves via a unique ``__name__`` registry lookup. The
optional ``--schema <selector>`` is imported first (via Strawberry's
``import_module_symbol``, mirroring ``export_schema``) to register and finalize
every type before resolution — required for a cold CLI process.
"""

import datetime
import decimal
import types as pytypes
import typing
import uuid

import strawberry
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import models
from django.utils.module_loading import import_string
from strawberry import relay
from strawberry.utils.importer import import_module_symbol

from django_strawberry_framework.registry import registry
from django_strawberry_framework.scalars import BigInt
from django_strawberry_framework.types.base import DjangoType
from django_strawberry_framework.types.converters import scalar_for_field
from django_strawberry_framework.utils.strings import snake_case

_GLOBAL_ID_GRAPHQL_TYPE = "GlobalID!"
_RELAY_PK_CONVERTER = "relay.Node id"
_UNFINALIZED_HINT = (
    "finalize_django_types() has not run — pass "
    "--schema <your project schema dotted path> so all types register and finalize"
)

# Python / Strawberry scalar -> GraphQL scalar name, mirroring the names
# Strawberry prints in the SDL. Types absent from this map (generated enums,
# resolved DjangoType relations, BigInt) render from their ``__name__``.
_GRAPHQL_SCALAR_NAMES: dict[object, str] = {
    int: "Int",
    str: "String",
    bool: "Boolean",
    float: "Float",
    decimal.Decimal: "Decimal",
    uuid.UUID: "UUID",
    datetime.date: "Date",
    datetime.datetime: "DateTime",
    datetime.time: "Time",
    strawberry.scalars.JSON: "JSON",
    BigInt: "BigInt",
}


class Command(BaseCommand):
    """Print the per-field GraphQL resolution table for a finalized DjangoType."""

    help = "Inspect a DjangoType's resolved per-field GraphQL types"

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional ``type`` argument and the optional ``--schema`` flag."""
        parser.add_argument("type", type=str, help="DjangoType name or fully-dotted object path")
        parser.add_argument("--schema", type=str, help="Optional schema selector to import first")

    def handle(self, *args: object, **options: object) -> None:
        """Import the schema (if given), resolve the type, and print its field table."""
        schema = options.get("schema")
        if schema:
            try:
                import_module_symbol(schema, default_symbol_name="schema")
            except (ImportError, AttributeError) as e:
                raise CommandError(str(e)) from e

        target = self._resolve_type(options["type"])
        if not (isinstance(target, type) and issubclass(target, DjangoType)):
            raise CommandError(f"{options['type']} is not a DjangoType subclass")

        definition = getattr(target, "__django_strawberry_definition__", None)
        if definition is None:
            raise CommandError(
                f"{target.__name__} is not a registered DjangoType "
                "(an abstract or no-Meta base never registers a definition)",
            )
        if definition.finalized is False:
            raise CommandError(_UNFINALIZED_HINT)

        self._print_table(definition)

    def _resolve_type(self, arg: str) -> object:
        """Resolve the ``type`` argument by shape — dotted path vs bare registered name."""
        if "." in arg:
            try:
                return import_string(arg)
            except (ImportError, AttributeError) as e:
                raise CommandError(str(e)) from e
        return self._resolve_bare_name(arg)

    @staticmethod
    def _resolve_bare_name(name: str) -> type:
        """Resolve a bare type name via a unique ``__name__`` match in the registry."""
        matches = [
            type_cls for _model, type_cls in registry.iter_types() if type_cls.__name__ == name
        ]
        if not matches:
            raise CommandError(
                f"{name} is not a registered DjangoType. Import the project schema first "
                "(pass --schema <your project schema dotted path>) or use a fully-dotted path.",
            )
        if len(matches) > 1:
            candidates = ", ".join(
                f"{type_cls.__module__}.{type_cls.__qualname__} "
                f"(model {getattr(registry.model_for_type(type_cls), '__name__', '?')})"
                for type_cls in matches
            )
            raise CommandError(
                f"{name} is ambiguous — {len(matches)} registered types share this name: "
                f"{candidates}. Pass a fully-dotted object path to disambiguate.",
            )
        return matches[0]

    def _print_table(self, definition: object) -> None:
        """Print the header and one row per selected field, in selection order."""
        origin = definition.origin
        model = definition.model
        title = f"{origin.__name__}  (model: {model.__module__}.{model.__qualname__})"
        self.stdout.write(title)
        header = (
            f"  {'field':<20} {'django field type':<20} "
            f"{'graphql type':<32} {'nullable':<10} converter"
        )
        self.stdout.write(header)
        self.stdout.write(f"  {'-' * 20} {'-' * 20} {'-' * 32} {'-' * 10} {'-' * 20}")
        for field in definition.selected_fields:
            graphql_type, nullable, converter = self._resolve_row(definition, field)
            django_field_type = type(field).__name__
            self.stdout.write(
                f"  {field.name:<20} {django_field_type:<20} "
                f"{graphql_type:<32} {nullable:<10} {converter}",
            )

    def _resolve_row(self, definition: object, field: models.Field) -> tuple[str, str, str]:
        """Return ``(graphql_type, nullable, converter)`` for one selected field."""
        field_meta = definition.field_map[snake_case(field.name)]
        if field_meta.is_relation:
            return self._relation_row(definition, field, field_meta)
        if self._is_suppressed_relay_pk(definition, field):
            return _GLOBAL_ID_GRAPHQL_TYPE, "no", _RELAY_PK_CONVERTER
        return self._scalar_row(definition, field)

    @staticmethod
    def _is_suppressed_relay_pk(definition: object, field: models.Field) -> bool:
        """Return whether ``field`` is the Relay-Node-suppressed primary key.

        On a Relay-Node-shaped type the pk ``continue``s past ``convert_scalar``
        (the interface supplies ``id: GlobalID!``), so it is absent from
        ``origin.__annotations__`` and must not be indexed there.
        """
        relay_shaped = any(issubclass(i, relay.Node) for i in definition.interfaces) or issubclass(
            definition.origin,
            relay.Node,
        )
        if not relay_shaped:
            return False
        return field.name == definition.model._meta.pk.name

    @staticmethod
    def _relation_row(
        definition: object,
        field: models.Field,
        field_meta: object,
    ) -> tuple[str, str, str]:
        """Build the row for a relation field from its resolved annotation + cardinality."""
        graphql_type = _render_annotation(definition.origin.__annotations__[field.name])
        converter = f"relation: {field_meta.relation_kind}"
        nullable = "no (list)" if field_meta.is_many_side else _yes_no(field_meta.nullable)
        return graphql_type, nullable, converter

    @staticmethod
    def _scalar_row(definition: object, field: models.Field) -> tuple[str, str, str]:
        """Build the row for a scalar field, reading nullability from the annotation."""
        annotation = definition.origin.__annotations__[field.name]
        graphql_type = _render_annotation(annotation)
        nullable = _yes_no(_annotation_is_optional(annotation))
        if field.choices:
            converter = "choice enum"
        else:
            # Re-walk SCALAR_MAP only to NAME the row that fired (Decision 4):
            # ``scalar_for_field`` raises if the field is unsupported, so the
            # call doubles as a guard that the printed row is real.
            scalar_for_field(field)
            converter = f"SCALAR_MAP[{type(field).__name__}]"
        return graphql_type, nullable, converter


def _yes_no(value: bool) -> str:
    """Render a boolean as the ``yes`` / ``no`` nullability-column token."""
    return "yes" if value else "no"


def _annotation_is_optional(annotation: object) -> bool:
    """Return whether ``annotation`` is a ``T | None`` union."""
    if typing.get_origin(annotation) in (typing.Union, pytypes.UnionType):
        return type(None) in typing.get_args(annotation)
    return False


def _scalar_name(scalar: object) -> str:
    """Return the GraphQL name for a resolved scalar / type.

    Built-in scalars map to Strawberry's SDL names; generated enums, resolved
    ``DjangoType`` relations, and custom scalars fall back to ``__name__``.
    """
    mapped = _GRAPHQL_SCALAR_NAMES.get(scalar)
    if mapped is not None:
        return mapped
    return getattr(scalar, "__name__", None) or str(scalar)


def _render_annotation(annotation: object) -> str:
    """Render a resolved GraphQL annotation as a GraphQL-shaped string.

    Mirrors how Strawberry renders the SDL: a non-``None`` scalar / type is
    ``Name!``; a ``T | None`` union is ``Name``; a ``list[T]`` is ``[Inner!]!``
    (the many-side list itself is non-null and its elements are non-null).
    """
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, pytypes.UnionType):
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return _render_annotation(args[0]).rstrip("!")
        return " | ".join(_render_annotation(a).rstrip("!") for a in args)
    if origin is list:
        (inner,) = typing.get_args(annotation)
        return f"[{_render_annotation(inner)}]!"
    return f"{_scalar_name(annotation)}!"
