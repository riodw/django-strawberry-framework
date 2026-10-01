"""Gate every explicit ``typing.Any`` in the package against an exact allowlist.

``Any`` switches the type checker off for every value it touches, and it
spreads: a helper returning ``Any`` makes each caller's result ``Any`` too.
basedpyright runs in ``standard`` mode, which does not report ``Any``, and
ruff's ANN401 is off, so nothing else stops a new ``Any`` from landing. Every
``Any`` the package keeps is forced from outside it:
a stub generic with no truthful narrower argument, an override or wrapper that
forwards ``*args`` / ``**kwargs`` verbatim to an upstream signature, a PEP 562
module ``__getattr__``. ``ALLOWED_ANY`` names each of them with the reason.

What counts: every reference to ``typing.Any`` / ``typing_extensions.Any`` in a
package module, under whatever name the module imported it (``Any``, an ``as``
alias, or ``typing.Any`` through a module alias), wherever it appears, plus the
ones inside string annotations: parameter and return annotations, annotated
assignments, ``cast`` targets, ``TypeVar`` bounds, constraints and defaults.
The import statement itself is not a use.

Each use is attributed to a site, ``<path>::<QualifiedName>``: the innermost
enclosing ``def`` / ``class`` chain, and at module or class scope the name the
statement binds (``ConcreteField``, ``SerializerMutation.serializer_class``), so
every site is a citation ``scripts/check_citations.py`` can resolve. A use in a
function body is attributed to the function, since a local is not citable.

``ALLOWED_ANY`` pins each site's exact count of uses. The gate fails on a site
the allowlist does not name, on a count above the entry's (a new ``Any`` at an
allowed site), and on an entry whose site now holds fewer uses or none (stale:
the cause is gone or shrank, so the entry must shrink with it).

Usage::

    uv run python scripts/check_any.py            # the gate
    uv run python scripts/check_any.py --list     # every site and its count

Exit code ``0`` when the package's uses match ``ALLOWED_ANY`` exactly, ``1``
otherwise.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import Counter
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "django_strawberry_framework"
#: Modules whose ``Any`` is the typing special form.
TYPING_MODULES = frozenset({"typing", "typing_extensions"})
#: Calls whose leading arguments are type expressions, possibly strings.
_TYPE_ARGUMENT_CALLS = frozenset({"cast", "TypeVar"})


class AllowedAny(NamedTuple):
    """A site allowed to keep ``count`` uses of ``Any``, and why nothing narrower is true."""

    site: str
    count: int
    reason: str


#: Every site allowed to keep ``Any``. Matched on the site and the exact count.
ALLOWED_ANY: tuple[AllowedAny, ...] = (
    AllowedAny(
        "django_strawberry_framework/__init__.py::__getattr__",
        1,
        "PEP 562 module __getattr__: a lazy re-export's value is whatever the named attribute is.",
    ),
    AllowedAny(
        "django_strawberry_framework/_request_body.py::_measured_by_bounded_read",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/_request_body.py::_measured_remaining",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/_request_body.py::_position_restored",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/_strawberry_patches.py::_AnyAsyncView",
        6,
        "Universal self form of AsyncBaseHTTPView: its six non-Request type parameters are "
        "invariant, so no single argument covers every view.",
    ),
    AllowedAny(
        "django_strawberry_framework/_strawberry_patches.py::_AnySyncView",
        4,
        "Universal self form of SyncBaseHTTPView: its four non-Request type parameters are "
        "invariant, so no single argument covers every view.",
    ),
    AllowedAny(
        "django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params",
        1,
        "Source-pinned verbatim upstream body rebinds params from str values to parsed "
        "JSON; upstream type-checks only through parse_json returning Any.",
    ),
    AllowedAny(
        "django_strawberry_framework/auth/mutations.py::login_mutation",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/auth/mutations.py::logout_mutation",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/auth/mutations.py::register_mutation",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/auth/queries.py::current_user",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/connection.py::DjangoConnectionField",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/connection.py::_ConnectionT",
        1,
        "Bound DjangoConnection[Any]: Strawberry's NodeType is invariant and "
        "resolve_connection's type[Self] matches no concrete bound.",
    ),
    AllowedAny(
        "django_strawberry_framework/connection.py::_consume_fallback",
        2,
        "Forwards the resolver's value and slice keywords verbatim to "
        "ListConnection.resolve_connection, whose typed parameters object fails; the value "
        "admits shapes outside its union.",
    ),
    AllowedAny(
        "django_strawberry_framework/consumers.py::_StopAwareSchema.stream",
        2,
        "Forwards *args/**kwargs verbatim to BaseSchema.stream; the supported range is "
        "uncapped, so its parameters cannot be pinned.",
    ),
    AllowedAny(
        "django_strawberry_framework/consumers.py::_StopAwareSchema.subscribe",
        2,
        "Forwards *args/**kwargs verbatim to BaseSchema.subscribe; the supported range is "
        "uncapped, so its parameters cannot be pinned.",
    ),
    AllowedAny(
        "django_strawberry_framework/consumers.py::build_revalidating_consumer_class",
        4,
        "Class bases read off the consumer class at runtime; typed as type[object], the "
        "generated subclasses lose every upstream member they call.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner.on_stream_result",
        1,
        "Returns the package's _BoundScope, which is not the base's "
        "StreamResultContextManager; both checkers reject the truthful override.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner.operation",
        1,
        "Returns the package's _BoundScope, which is not the base's "
        "OperationContextManager; both checkers reject the truthful override.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::OperationState.__init__",
        1,
        "Holds ContextVars of different value types; ContextVar and Token are invariant, so "
        "ContextVar[object] rejects every typed variable.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::OperationState.resumed_bindings",
        1,
        "Holds ContextVars of different value types; ContextVar and Token are invariant, so "
        "ContextVar[object] rejects every typed variable.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::_Binding.token",
        1,
        "Holds ContextVars of different value types; ContextVar and Token are invariant, so "
        "ContextVar[object] rejects every typed variable.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::_Binding.variable",
        1,
        "Holds ContextVars of different value types; ContextVar and Token are invariant, so "
        "ContextVar[object] rejects every typed variable.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension.execution_context",
        1,
        "The truthful ExecutionContext | None fails the override check against "
        "SchemaExtension.execution_context: ExecutionContext.",
    ),
    AllowedAny(
        "django_strawberry_framework/extensions/operation_state.py::_ResumedStream.athrow",
        2,
        "Forwards verbatim to the overloaded AsyncGenerator.athrow; spelling the "
        "three-argument form passes a signature deprecated on Python 3.12+.",
    ),
    AllowedAny(
        "django_strawberry_framework/filters/base.py::_AbsentGlobalIDMultipleChoiceWidget.value_from_datadict",
        1,
        "django-stubs types files as MultiValueDict[str, UploadedFile[Any]], an invariant "
        "dict subclass, and the value is forwarded to super().",
    ),
    AllowedAny(
        "django_strawberry_framework/filters/base.py::_decode_and_validate_global_id",
        1,
        "The value reaches relay.GlobalID.from_id unchecked; object needs a str guard, a "
        "runtime change.",
    ),
    AllowedAny(
        "django_strawberry_framework/filters/inputs.py::normalize_input_value",
        1,
        "The list closures iterate a container the raising _require_list_container proves; "
        "object needs it to return the narrowed value, a runtime change.",
    ),
    AllowedAny(
        "django_strawberry_framework/forms/inputs.py::_form_field_basis",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/forms/sets.py::DjangoFormMutation.resolve_async",
        2,
        "Consumer-overridden hook: Info's type parameters are invariant, so any narrower "
        "base spelling rejects a consumer override taking its own typed Info.",
    ),
    AllowedAny(
        "django_strawberry_framework/forms/sets.py::DjangoFormMutation.resolve_sync",
        2,
        "Consumer-overridden hook: Info's type parameters are invariant, so any narrower "
        "base spelling rejects a consumer override taking its own typed Info.",
    ),
    AllowedAny(
        "django_strawberry_framework/forms/sets.py::DjangoModelFormMutation.get_form",
        1,
        "Consumer-overridden hook: ModelForm's model parameter is invariant, so "
        "ModelForm[Model] rejects an override returning ModelForm[Item].",
    ),
    AllowedAny(
        "django_strawberry_framework/forms/sets.py::_default_get_form_kwargs",
        1,
        "Consumer-overridden hook whose result is splatted into the consumer's form "
        "constructor; dict[str, object] rejects that splat and Mapping rejects item "
        "assignment.",
    ),
    AllowedAny(
        "django_strawberry_framework/list_field.py::DjangoListField",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/list_field.py::_is_deterministic_order_term",
        1,
        "Narrowed only through a stored type(term) alias, which neither checker follows; "
        "the F arm reads F.name, which django-stubs does not declare.",
    ),
    AllowedAny(
        "django_strawberry_framework/management/commands/export_schema.py::Command.handle",
        1,
        "Overrides BaseCommand.handle(**options: Any); call_command can bypass argparse, so "
        "object needs a str guard, a runtime change.",
    ),
    AllowedAny(
        "django_strawberry_framework/management/commands/inspect_django_type.py::Command.handle",
        1,
        "Overrides BaseCommand.handle(**options: Any); call_command can bypass argparse, so "
        "object needs a str guard, a runtime change.",
    ),
    AllowedAny(
        "django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view",
        1,
        "Holds an object() sentinel or the view's setup, called unchecked like "
        "View.as_view; no checker narrows an object() sentinel by identity.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/fields.py::DjangoMutationField",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/permissions.py::DjangoModelPermission.has_permission",
        2,
        "Consumer-overridden hook: a base parameter narrower than Any makes an override "
        "declaring its own narrower type a Liskov error under the consumer's checker.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/sets.py::DjangoMutation.check_permission",
        2,
        "Consumer-overridden hook: a base parameter narrower than Any makes an override "
        "declaring its own narrower type a Liskov error under the consumer's checker.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/sets.py::DjangoMutation.resolve_async",
        2,
        "Consumer-overridden hook: Info's type parameters are invariant, so any narrower "
        "base spelling rejects a consumer override taking its own typed Info.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/sets.py::DjangoMutation.resolve_sync",
        2,
        "Consumer-overridden hook: Info's type parameters are invariant, so any narrower "
        "base spelling rejects a consumer override taking its own typed Info.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/sets.py::_ValidatedMutationMeta.__init__",
        4,
        "One snapshot shared by three flavors whose form_class / serializer_class slots are "
        "set only on their own flavor; the truthful Optional types redden every flavor's "
        "reader.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/sets.py::_validate_permission_classes",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/mutations/sets.py::make_meta_validating_metaclass.MetaValidatingMetaclass.__new__",
        1,
        "Matches typeshed's type.__new__ namespace parameter, dict[str, Any].",
    ),
    AllowedAny(
        "django_strawberry_framework/optimizer/join_taxonomy.py::_generic_child_attname",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/optimizer/join_taxonomy.py::_parent_join_column",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/optimizer/join_taxonomy.py::_through_link_fields",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/optimizer/nested_planner.py::_coerce_pagination_int",
        2,
        "EAFP probe of a wire value through int(); the value is passed through to window "
        "bounds typed int | None, which narrowing would change at runtime.",
    ),
    AllowedAny(
        "django_strawberry_framework/relay.py::DjangoNodeField",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/relay.py::DjangoNodeField._resolve",
        1,
        "Strawberry reads this resolver's return annotation at runtime; Any lets the "
        "class-body annotation supply the schema type.",
    ),
    AllowedAny(
        "django_strawberry_framework/relay.py::DjangoNodesField",
        1,
        "Public field factory assigned in a class body: a consumer's `x: T = factory(...)` "
        "needs a return assignable to any annotation, as strawberry.field's own does.",
    ),
    AllowedAny(
        "django_strawberry_framework/relay.py::DjangoNodesField._resolve",
        1,
        "Strawberry reads this resolver's return annotation at runtime; Any lets the "
        "class-body annotation supply the schema type.",
    ),
    AllowedAny(
        "django_strawberry_framework/resource_policy.py::ResourcePolicy.narrowed",
        1,
        "Forwarded to dataclasses.replace, which mypy types per field; values are validated "
        "by __post_init__.",
    ),
    AllowedAny(
        "django_strawberry_framework/resource_policy.py::_windowed_rows",
        1,
        "A consumer resolver's return reaches islice/slicing unchecked; object needs an "
        "iterability check, a runtime change.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/resolvers.py::_RelationIntentLedger.consume",
        1,
        "Returns a snapshot or an object() sentinel; no checker narrows an object() "
        "sentinel by identity.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/resolvers.py::_decode_nested",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs",
        1,
        "Splatted into serializer_class(**kwargs), whose stub types every keyword; "
        "dict[str, object] rejects the splat.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/resolvers.py::_pin_validator_querysets",
        1,
        "Recursion passes ListSerializer.child and plain BaseSerializer values, while the "
        "body reads .fields, which only Serializer declares.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/resolvers.py::_pin_validator_querysets._pinned",
        2,
        "Assigns .queryset on a copied validator; drf-stubs' Validator declares no "
        "queryset, so any element type rejects the write.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/resolvers.py::_record_field_intent",
        1,
        "Replaces the bound method run_validation with an instance attribute, which mypy "
        "rejects on a typed field and on a Protocol.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/serializer_converter.py::DRFBaseSerializer",
        1,
        "drf-stubs' universal BaseSerializer form: its instance parameter is invariant.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/serializer_converter.py::DRFField",
        4,
        "drf-stubs' universal Field form: its four type parameters are invariant.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/serializer_converter.py::DRFModelSerializer",
        1,
        "drf-stubs' universal ModelSerializer form: its model parameter is invariant, so "
        "ModelSerializer[Model] rejects ModelSerializer[Item].",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/serializer_converter.py::DRFSerializer",
        1,
        "drf-stubs' universal Serializer form: its instance parameter is invariant.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/sets.py::SerializerMutation.Meta",
        1,
        "Consumer-declared Meta read by attribute before the validated snapshot exists.",
    ),
    AllowedAny(
        "django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_kwargs",
        1,
        "Consumer-overridden hook whose result becomes the serializer constructor's "
        "keywords; a narrower spelling breaks overrides and super() callers that mutate it.",
    ),
    AllowedAny(
        "django_strawberry_framework/routers.py::__getattr__",
        1,
        "PEP 562 module __getattr__: a lazy re-export's value is whatever the named attribute is.",
    ),
    AllowedAny(
        "django_strawberry_framework/scalars.py::strawberry_config",
        1,
        "Forwards *args/**kwargs verbatim to StrawberryConfig, whose dataclass fields vary "
        "across the supported strawberry range; the supported range is uncapped, so its "
        "parameters cannot be pinned.",
    ),
    AllowedAny(
        "django_strawberry_framework/schema.py::DjangoSchema.__init__",
        2,
        "Forwards *args/**kwargs verbatim to strawberry Schema.__init__; the supported "
        "range is uncapped, so its parameters cannot be pinned.",
    ),
    AllowedAny(
        "django_strawberry_framework/schema.py::DjangoSchema._stream",
        2,
        "Forwards *args/**kwargs verbatim to strawberry Schema._stream; the supported range "
        "is uncapped, so its parameters cannot be pinned.",
    ),
    AllowedAny(
        "django_strawberry_framework/schema.py::DjangoSchema.execute",
        2,
        "Forwards *args/**kwargs verbatim to strawberry Schema.execute; the supported range "
        "is uncapped, so its parameters cannot be pinned.",
    ),
    AllowedAny(
        "django_strawberry_framework/schema.py::DjangoSchema.execute_sync",
        2,
        "Forwards *args/**kwargs verbatim to strawberry Schema.execute_sync; the supported "
        "range is uncapped, so its parameters cannot be pinned.",
    ),
    AllowedAny(
        "django_strawberry_framework/schema.py::DjangoSchema.extensions",
        1,
        "The truthful tuple[object, ...] fails mypy's override check against the base "
        "attribute's extension tuple type.",
    ),
    AllowedAny(
        "django_strawberry_framework/testing/client.py::Response.response",
        1,
        "Public dataclass field defaulting to None: Optional breaks a consumer's "
        "res.response.status_code and the response union conflicts with the default.",
    ),
    AllowedAny(
        "django_strawberry_framework/types/base.py::DjangoType.__init_subclass__",
        1,
        "Meta.description reaches DjangoTypeDefinition.description: str | None unvalidated; "
        "object needs a runtime check.",
    ),
    AllowedAny(
        "django_strawberry_framework/types/base.py::DjangoType.get_queryset",
        6,
        "Consumer-overridden hook: an override must accept everything the base does, Info "
        "is invariant, and a TypeVar return forbids non-generic overrides.",
    ),
    AllowedAny(
        "django_strawberry_framework/types/resolvers.py::_PLAN_UNREAD",
        1,
        "object() sentinel defaulting an AbstractSet[str] | None parameter; no checker "
        "narrows it by identity.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/converters.py::convert_with_mro",
        1,
        "Each precheck handler takes the class its paired isinstance narrows to; Callable "
        "parameters are contravariant, so no common spelling exists.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/directives.py::validated_field_directives",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/errors.py::_validation_code",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/errors.py::_validation_messages",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/inputs.py::build_strawberry_input_class",
        1,
        "Field keywords forwarded into strawberry.field arrive as object from the spec "
        "triple's mapping; typing them needs casts or new checks.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/inputs.py::emit_set_input_field_triples",
        1,
        "Annotated[<str>, strawberry.lazy(...)] is a runtime form neither checker models as "
        "a type or as an object it can widen with | None.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/inputs.py::normalize_field_name_sequence",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/querysets.py::_BOUND_VALUE_NORMALIZERS",
        1,
        "Heterogeneous (base, normalizer) pairs whose normalizer takes its own base; a "
        "homogeneous Callable element type rejects each by contravariance.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/querysets.py::_reverse_relation_by_accessor_or_none",
        1,
        "Calls get_accessor_name() on any non-concrete relation; the stub union rejects "
        "that call, which needs a ForeignObjectRel guard, a runtime change.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/querysets.py::_safe_class_name",
        1,
        "EAFP: an arbitrary object read inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/typing.py::ConcreteField",
        1,
        "django-stubs' Field setter parameter is contravariant with no universal value: "
        "Never makes dataclass slots holding a field reject every write, object rejects "
        "every column.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/typing.py::ForeignKeyField",
        1,
        "django-stubs' ForeignKey setter parameter is contravariant with no universal "
        "value, as for ConcreteField.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/typing.py::unwrap_return_type",
        2,
        "Returns typing.Any itself as the element of a bare list annotation: a runtime "
        "value, not an annotation.",
    ),
    AllowedAny(
        "django_strawberry_framework/utils/write_values.py::materialize_relation_id_container",
        1,
        "EAFP: list(values) on wire input inside the surrounding try/except, which is the guard.",
    ),
    AllowedAny(
        "django_strawberry_framework/views.py::AsyncDjangoGraphQLView.run",
        1,
        "Upstream overloads run(HttpRequest) to two response types; HttpResponseBase is "
        "rejected against the second overload.",
    ),
    AllowedAny(
        "django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.as_view",
        2,
        "Sync or coroutine view callback depending on the concrete view; Django's path() "
        "overloads accept each but not their union.",
    ),
    AllowedAny(
        "django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.as_view.prepared_view",
        1,
        "The prepared view instance's dispatch is sync on one view and a coroutine on the "
        "other, which the shared mixin cannot spell.",
    ),
)


class Verdict(NamedTuple):
    """The gate's judgment of one census."""

    #: Sites carrying uses no entry allows: ``(site, found, allowed)``.
    failing: tuple[tuple[str, int, int], ...]
    #: Entries whose site now holds fewer uses than allowed: ``(entry, found)``.
    stale: tuple[tuple[AllowedAny, int], ...]

    @property
    def passing(self) -> bool:
        """Nothing unallowed found and no stale entry."""
        return not self.failing and not self.stale


def _any_bindings(tree: ast.Module) -> tuple[frozenset[str], frozenset[str]]:
    """Return the names bound to ``Any`` and the names bound to a typing module."""
    names: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in TYPING_MODULES:
            names.update(alias.asname or alias.name for alias in node.names if alias.name == "Any")
        elif isinstance(node, ast.Import):
            modules.update(
                alias.asname or alias.name for alias in node.names if alias.name in TYPING_MODULES
            )
    return frozenset(names), frozenset(modules)


def _is_any(node: ast.AST, names: frozenset[str], modules: frozenset[str]) -> bool:
    """Whether ``node`` references ``Any`` under one of the module's bindings."""
    if isinstance(node, ast.Name):
        return node.id in names
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "Any"
        and isinstance(node.value, ast.Name)
        and node.value.id in modules
    )


def _type_expressions(tree: ast.Module) -> Iterator[ast.expr]:
    """Yield every expression the language or a typing call reads as a type."""
    for node in ast.walk(tree):
        if isinstance(node, ast.arg) and node.annotation is not None:
            yield node.annotation
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns:
            yield node.returns
        elif isinstance(node, ast.AnnAssign):
            yield node.annotation
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name == "cast" and node.args:
                yield node.args[0]
            elif name == "TypeVar":
                yield from node.args[1:]
                yield from (keyword.value for keyword in node.keywords)


def _string_uses(
    expression: ast.expr,
    names: frozenset[str],
    modules: frozenset[str],
) -> Iterator[ast.Constant]:
    """Yield the string constant once per ``Any`` use it spells, parsing nested strings."""
    for node in ast.walk(expression):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        try:
            parsed = ast.parse(node.value.strip(), mode="eval")
        except SyntaxError:
            continue
        for inner in ast.walk(parsed):
            if _is_any(inner, names, modules):
                yield node
        for _ in _string_uses(parsed.body, names, modules):
            yield node


def _bound_name(statement: ast.stmt) -> str | None:
    """The single name an assignment statement binds, else ``None``."""
    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        return statement.target.id
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        return statement.targets[0].id
    return None


def _site(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    """The qualified name a use at ``node`` is attributed to.

    The enclosing ``def`` / ``class`` chain, plus, when the use sits in an
    assignment at module or class scope, the name that assignment binds.
    """
    chain: list[str] = []
    binding: str | None = None
    in_function = False
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not chain and isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                in_function = True
            chain.append(current.name)
        elif not chain and binding is None and isinstance(current, (ast.Assign, ast.AnnAssign)):
            binding = _bound_name(current)
        current = parents.get(current)
    chain.reverse()
    if binding is not None and not in_function:
        chain.append(binding)
    return ".".join(chain) or "<module>"


def module_uses(source: str) -> list[tuple[str, int]]:
    """Return ``(qualified site, line)`` for every ``Any`` use in one module's source."""
    tree = ast.parse(source)
    names, modules = _any_bindings(tree)
    if not names and not modules:
        return []
    parents = {
        child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
    }
    uses: list[ast.AST] = [node for node in ast.walk(tree) if _is_any(node, names, modules)]
    for expression in _type_expressions(tree):
        uses.extend(_string_uses(expression, names, modules))
    return sorted((_site(node, parents), getattr(node, "lineno", 0)) for node in uses)


def census(root: Path) -> dict[str, list[int]]:
    """Map every ``<path>::<site>`` under ``root``'s package to the lines of its uses."""
    found: dict[str, list[int]] = {}
    for path in sorted((root / PACKAGE).rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        for site, line in module_uses(path.read_text(encoding="utf-8")):
            found.setdefault(f"{relative}::{site}", []).append(line)
    return found


def judge(found: dict[str, list[int]], allowed: Sequence[AllowedAny]) -> Verdict:
    """Compare a census with the allowlist."""
    limits = Counter({entry.site: entry.count for entry in allowed})
    failing = tuple(
        (site, len(lines), limits[site])
        for site, lines in sorted(found.items())
        if len(lines) > limits[site]
    )
    stale = tuple(
        (entry, len(found.get(entry.site, ())))
        for entry in allowed
        if len(found.get(entry.site, ())) < entry.count
    )
    return Verdict(failing, stale)


def render(verdict: Verdict, found: dict[str, list[int]]) -> str:
    """The failure report: each unallowed site with its lines, then each stale entry."""
    lines = []
    for site, count, limit in verdict.failing:
        where = ", ".join(str(line) for line in found[site])
        lines.append(f"{site}: {count} use(s) of Any, {limit} allowed (lines {where})")
    for entry, count in verdict.stale:
        lines.append(f"{entry.site}: stale allowlist entry, {entry.count} allowed, {count} found")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--list",
        action="store_true",
        help="print every site and its use count instead of judging them",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None, *, root: Path = REPO_ROOT) -> int:
    """Run the census under ``root`` and judge it, or list it with ``--list``."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    found = census(root)
    if args.list:
        for site, lines in sorted(found.items()):
            print(f"{len(lines):3d} {site}")
        print(f"{sum(map(len, found.values()))} uses at {len(found)} sites", file=sys.stderr)
        return 0
    verdict = judge(found, ALLOWED_ANY)
    if verdict.passing:
        total = sum(map(len, found.values()))
        print(f"check_any: {total} allowed use(s) of Any at {len(found)} site(s)")
        return 0
    print(render(verdict, found))
    return 1


if __name__ == "__main__":
    sys.exit(main())
