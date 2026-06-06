"""manage.py inspect_django_type — print a DjangoType's per-field GraphQL resolution table.

Diagnostic command that walks a finalized ``DjangoTypeDefinition`` and prints,
per selected field, the Django field name, the Django field type, the resolved
GraphQL type, its nullability, and which converter row fired. It reads the
existing introspection surface rather than re-deriving types, and the
authoritative record differs by field origin:

- **Auto-synthesized fields** read the resolved GraphQL annotation from
  ``origin.__annotations__`` (the post-finalize record that already reflects
  ``Meta.nullable_overrides`` / ``required_overrides``) rather than re-running
  ``convert_scalar``, and re-walk ``SCALAR_MAP`` only to NAME which converter
  row fired.
- **Consumer-authored fields** (an annotation or ``strawberry.field`` override)
  read the resolved type from the finalized Strawberry field metadata
  (``origin.__strawberry_definition__``). That is authoritative for both override
  kinds and resolves forward references, whereas ``origin.__annotations__`` holds
  a ``StrawberryAnnotation`` for an assigned field and an unresolved forward-ref
  string for an annotated relation. A forward reference that ``finalize_django_types()``
  could not resolve surfaces as Strawberry's ``UNRESOLVED`` sentinel and raises
  ``CommandError`` rather than printing a bogus type.

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
from strawberry.types.base import StrawberryList, StrawberryOptional
from strawberry.types.field import UNRESOLVED
from strawberry.utils.importer import import_module_symbol

from django_strawberry_framework.registry import registry
from django_strawberry_framework.scalars import BigInt
from django_strawberry_framework.types.base import DjangoType
from django_strawberry_framework.types.converters import SCALAR_MAP
from django_strawberry_framework.utils.strings import snake_case

_GLOBAL_ID_GRAPHQL_TYPE = "GlobalID!"
_RELAY_PK_CONVERTER = "relay.Node id"

# Friendly converter-column labels for relation rows, mirroring the spec's
# illustrative output (``M2M`` / ``forward FK`` / ``reverse FK``).
# ``FieldMeta.relation_kind`` returns the internal cardinality token; this maps
# it to the consumer-facing name. Unmapped kinds fall back to the raw token.
_RELATION_KIND_LABELS: dict[str, str] = {
    "many": "M2M",
    "forward_single": "forward FK",
    "reverse_many_to_one": "reverse FK",
    "reverse_one_to_one": "reverse O2O",
}
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
        """Return ``(graphql_type, nullable, converter)`` for one selected field.

        Dispatch is most-specific first:

        1. A Relay-Node-suppressed pk wins over everything — its
           ``id: GlobalID!`` is interface-supplied, so it is absent from
           ``origin.__annotations__`` and must not be read there (a relation pk
           on a Relay type, e.g. ``OneToOneField(primary_key=True)``, would
           otherwise reach ``_relation_row`` and ``KeyError``).
        2. A consumer-authored field (``definition.consumer_authored_fields``)
           is next: ``_build_annotations`` deliberately skips auto-synthesis for
           it (the four-corner override contract in ``types/base.py``), so
           neither the relation auto-converter nor a ``SCALAR_MAP`` row produced
           it — the consumer's annotation / ``strawberry.field`` did.
        3. Only then do the auto-synthesized relation / scalar branches apply.
        """
        field_meta = definition.field_map[snake_case(field.name)]
        if self._is_suppressed_relay_pk(definition, field):
            return _GLOBAL_ID_GRAPHQL_TYPE, "no", _RELAY_PK_CONVERTER
        if field.name in definition.consumer_authored_fields:
            return self._consumer_authored_row(definition, field)
        if field_meta.is_relation:
            return self._relation_row(definition, field, field_meta)
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
        kind = field_meta.relation_kind
        converter = f"relation: {_RELATION_KIND_LABELS.get(kind, kind)}"
        nullable = "no (list)" if field_meta.is_many_side else _yes_no(field_meta.nullable)
        return graphql_type, nullable, converter

    @staticmethod
    def _scalar_row(definition: object, field: models.Field) -> tuple[str, str, str]:
        """Build the row for a scalar field, reading nullability from the annotation."""
        annotation = definition.origin.__annotations__[field.name]
        graphql_type = _render_annotation(annotation)
        nullable = _yes_no(_annotation_is_optional(annotation))
        # ``choice enum`` for a choice field; otherwise name the SCALAR_MAP row
        # that fired — the matched MRO ancestor (Decision 4) — so a consumer
        # subclass of a supported field reports the ancestor row (e.g.
        # ``TextField``) rather than its own concrete class name.
        converter = "choice enum" if field.choices else f"SCALAR_MAP[{_matched_scalar_key(field)}]"
        return graphql_type, nullable, converter

    @staticmethod
    def _consumer_authored_row(definition: object, field: models.Field) -> tuple[str, str, str]:
        """Build the row for a consumer-authored field (annotation / ``strawberry.field`` override).

        ``_build_annotations`` skips auto-synthesis for any name in
        ``definition.consumer_authored_fields``, so the resolved GraphQL type is
        read from the finalized Strawberry field metadata
        (``origin.__strawberry_definition__``) rather than ``origin.__annotations__``.
        The Strawberry field's ``.type`` is the single authoritative post-finalize
        record for BOTH override kinds and already resolves forward references,
        whereas ``origin.__annotations__`` holds a ``StrawberryAnnotation`` for an
        assigned field and an unresolved forward-reference string for an annotated
        relation — neither renderable here.

        An annotation-only relation whose forward reference is not resolvable from
        the type's module namespace stays Strawberry's ``UNRESOLVED`` sentinel after
        ``finalize_django_types()`` alone (``finalize`` does not force field-type
        resolution; building a ``strawberry.Schema`` does). Reporting the sentinel as
        a GraphQL type would be a lie — Strawberry itself raises on it at schema-build
        time — so it raises ``CommandError`` with a concrete recovery hint instead.
        """
        strawberry_fields = definition.origin.__strawberry_definition__.fields
        field_type = next(sf.type for sf in strawberry_fields if sf.python_name == field.name)
        if field_type is UNRESOLVED:
            raise CommandError(
                f"{definition.origin.__name__}.{field.name} is a consumer-authored field whose "
                "annotation is an unresolved Strawberry forward reference; "
                "finalize_django_types() does not force forward-reference resolution. Pass "
                "--schema <your project schema dotted path> so the schema is constructed (which "
                "resolves the reference), or make the referenced type importable at the "
                "annotation's module scope, then re-run.",
            )
        graphql_type = _render_strawberry_type(field_type)
        nullable = _consumer_nullable(field_type)
        converter = _consumer_converter_label(definition, field.name)
        return graphql_type, nullable, converter


def _yes_no(value: bool) -> str:
    """Render a boolean as the ``yes`` / ``no`` nullability-column token."""
    return "yes" if value else "no"


def _annotation_is_optional(annotation: object) -> bool:
    """Return whether ``annotation`` is a ``T | None`` union."""
    if typing.get_origin(annotation) in (typing.Union, pytypes.UnionType):
        return type(None) in typing.get_args(annotation)
    return False


def _matched_scalar_key(field: models.Field) -> str:
    """Name the ``SCALAR_MAP`` entry (the MRO ancestor) that fired for ``field``.

    ``convert_scalar`` resolves a scalar field by walking ``type(field).__mro__``
    against ``SCALAR_MAP``, so a consumer subclass of a supported field is
    converted by its nearest supported ancestor — ``MyTextField(TextField)``
    fires the ``TextField`` row, not a ``MyTextField`` row. Report that ancestor
    so the converter column names the row that actually fired. Falls back to the
    concrete class name, only reachable for a field with no ``SCALAR_MAP``
    ancestor — and this helper only ever sees an *auto-synthesized* scalar
    (``_resolve_row`` routes every consumer-authored field, including an
    annotation override of an unsupported column, to ``_consumer_authored_row``
    first), whose scalar necessarily resolved at construction. So the fallback is
    unreachable for a finalized type.
    """
    return next(
        (klass.__name__ for klass in type(field).__mro__ if klass in SCALAR_MAP),
        type(field).__name__,
    )


def _render_strawberry_type(field_type: object) -> str:
    """Render a finalized Strawberry field type as a GraphQL-shaped string.

    The Strawberry-wrapper analogue of ``_render_annotation`` (which renders
    Python typing annotations): ``StrawberryOptional`` is the nullable ``Name``
    form (strip the trailing ``!``), ``StrawberryList`` is ``[Inner!]!`` (a
    non-null list whose element keeps its own rendered nullability), and a
    concrete leaf scalar / type is ``Name!`` via ``_scalar_name``.
    """
    if isinstance(field_type, StrawberryOptional):
        return _render_strawberry_type(field_type.of_type).rstrip("!")
    if isinstance(field_type, StrawberryList):
        return f"[{_render_strawberry_type(field_type.of_type)}]!"
    return f"{_scalar_name(field_type)}!"


def _consumer_nullable(field_type: object) -> str:
    """Map a finalized Strawberry field type to the nullability-column token.

    A ``StrawberryOptional`` (including ``list[T] | None``, whose top wrapper is
    the optional) is nullable ``yes``; a non-optional ``StrawberryList`` is
    ``no (list)`` to match the relation-row convention; any other leaf is ``no``.
    """
    if isinstance(field_type, StrawberryOptional):
        return "yes"
    if isinstance(field_type, StrawberryList):
        return "no (list)"
    return "no"


def _consumer_converter_label(definition: object, name: str) -> str:
    """Name the override row that produced a consumer-authored field.

    ``annotation`` vs ``strawberry.field`` distinguishes the two authoring styles
    and the ``(scalar)`` / ``(relation)`` suffix names the column kind — both
    facts come straight from the four-corner override sets recorded on the
    definition (see ``types/base._consumer_assigned_fields``). This is the row
    that actually fired: NOT the relation auto-converter and NOT a ``SCALAR_MAP``
    entry, both of which ``_build_annotations`` skipped for this name.

    The two authoring styles are NOT mutually exclusive: the idiom
    ``name: str = strawberry.field(resolver=...)`` is recorded in BOTH the
    annotated and the assigned set (the annotation fixes the type, the
    ``strawberry.field`` supplies the resolver), so the overlap is labelled
    ``annotation + strawberry.field`` rather than hiding the assignment.
    """
    annotated = name in (
        definition.consumer_annotated_scalar_fields | definition.consumer_annotated_relation_fields
    )
    assigned = name in (
        definition.consumer_assigned_scalar_fields | definition.consumer_assigned_relation_fields
    )
    is_relation = name in (
        definition.consumer_annotated_relation_fields | definition.consumer_assigned_relation_fields
    )
    if annotated and assigned:
        source = "annotation + strawberry.field"
    elif annotated:
        source = "annotation"
    else:
        source = "strawberry.field"
    kind = "relation" if is_relation else "scalar"
    return f"consumer {source} ({kind})"


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
