"""``ErrorPolicy`` construction, precedence, and install position (spec-048).

The package tier of the production error policy: everything a live ``/graphql/``
request cannot reach. What a client actually reads out of a masked response - the
category matrix, the correlation id on the wire and in the log, the retained
``path``, sync/async parity, and both opt-outs - is pinned over real HTTP in
``examples/fakeshop/test_query/test_error_policy_api.py``, because that is where
it matters. What is left here is the surface a request cannot express:

- the dataclass's per-field validation, which fails at CONSTRUCTION and therefore
  never reaches a request at all;
- the precedence ladder (constructor argument > setting > package default) and
  the settings-shape rejections;
- the correlation id's format and its uniqueness, read directly rather than
  inferred from two sampled responses;
- the extension's INSTALL POSITION, which is a property of the extensions list
  rather than of any response, and the consumer-supplied suppression that keeps
  a consumer's own entry exactly where they put it;
- the standalone fallback a plain ``strawberry.Schema`` takes, which has no
  ``error_policy`` attribute to read, and the isinstance-guarded fallback a schema
  carrying a WRONG ``error_policy`` attribute takes;
- the two teardown no-ops (a ``None`` result, an error-free result) whose whole
  observable behavior is that nothing happened;
- the two fail-closed degrades, which need an error object and a result object no
  engine builds; and
- ``mask_execution_result``'s copy contract - the property that lets the
  subscription seam mask an event without disturbing the originals an extension
  reads. What that seam does on the wire is pinned at the consumer tier in
  ``tests/test_routers.py``, the only tier that can observe a subscription frame.
"""

from __future__ import annotations

import contextlib
import logging
from types import SimpleNamespace

import pytest
import strawberry
from graphql import GraphQLError
from graphql.execution import ExecutionResult as GraphQLExecutionResult
from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult

from django_strawberry_framework import DjangoSchema
from django_strawberry_framework.error_policy import (
    DEFAULT_ERROR_POLICY,
    ErrorPolicy,
    new_correlation_id,
    resolve_error_policy,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.debug import DjangoDebugExtension
from django_strawberry_framework.extensions.error_policy import (
    DjangoErrorPolicyExtension,
    mask_execution_result,
    schema_error_policy,
)
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.schema import _with_error_policy_extension

_SENSITIVE = "standalone schema secret /srv/private/standalone.key"


@strawberry.type
class _Query:
    """A schema-shaped query with one always-failing field."""

    @strawberry.field
    def ping(self) -> int:
        return 1

    @strawberry.field
    def boom(self) -> str | None:
        raise ValueError(_SENSITIVE)


# ---------------------------------------------------------------------------
# Construction and validation
# ---------------------------------------------------------------------------


def test_the_package_default_is_masking_on_with_the_documented_strings():
    """The fail-closed answer is the one a deployment gets by doing nothing."""
    assert DEFAULT_ERROR_POLICY.enabled is True
    assert DEFAULT_ERROR_POLICY.message == "An unexpected error occurred."
    assert DEFAULT_ERROR_POLICY.correlation_extension_key == "correlationId"


@pytest.mark.parametrize(
    "value",
    [
        1,
        0,
        "yes",
        None,
    ],
    ids=[
        "truthy-int",
        "falsy-int",
        "string",
        "none",
    ],
)
def test_a_non_bool_enabled_is_rejected_at_construction(value):
    """``enabled`` is a switch, not a truthiness test.

    ``1`` and ``"yes"`` would both silently work under a ``bool()`` coercion, and
    so would ``0`` - which is the dangerous one, because a deployment that meant
    to disable masking and a deployment that fat-fingered the type would be
    indistinguishable. The rejection names the field.
    """
    with pytest.raises(ConfigurationError, match="ErrorPolicy.enabled must be a bool"):
        ErrorPolicy(enabled=value)


@pytest.mark.parametrize(
    "value",
    ["", None, 42],
    ids=["empty", "none", "int"],
)
def test_a_non_string_or_empty_message_is_rejected_at_construction(value):
    """An empty mask is not a mask - the client would read a blank error."""
    with pytest.raises(ConfigurationError, match="ErrorPolicy.message must be a non-empty string"):
        ErrorPolicy(message=value)


@pytest.mark.parametrize(
    "value",
    ["", None, 42],
    ids=["empty", "none", "int"],
)
def test_a_non_string_or_empty_correlation_key_is_rejected_at_construction(value):
    """An unusable extensions key would publish the id where no client can find it."""
    with pytest.raises(
        ConfigurationError,
        match="ErrorPolicy.correlation_extension_key must be a non-empty string",
    ):
        ErrorPolicy(correlation_extension_key=value)


def test_the_policy_is_frozen_so_a_resolver_cannot_widen_its_own_request():
    """Frozen is the point: a request holding the policy cannot loosen it."""
    with pytest.raises(Exception, match="cannot assign to field"):
        DEFAULT_ERROR_POLICY.enabled = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# The precedence ladder
# ---------------------------------------------------------------------------


def test_an_explicit_instance_is_returned_unchanged():
    """An ``ErrorPolicy`` has already validated itself, so it is used as-is."""
    policy = ErrorPolicy(message="Nope.")
    assert resolve_error_policy(policy) is policy


def test_an_explicit_mapping_is_applied_over_the_package_defaults():
    """A deployment overrides only what it cares about."""
    policy = resolve_error_policy({"message": "Nope."})
    assert policy.message == "Nope."
    assert policy.enabled is True
    assert policy.correlation_extension_key == "correlationId"


def test_no_source_at_all_resolves_to_the_package_defaults():
    assert resolve_error_policy(None) is DEFAULT_ERROR_POLICY


def test_the_setting_supplies_the_policy_when_no_argument_does(settings):
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"ERROR_POLICY": {"message": "From settings."}}
    assert resolve_error_policy(None).message == "From settings."


def test_an_explicit_argument_outranks_the_setting(settings):
    """A process running a public schema and an internal one must be able to differ."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"ERROR_POLICY": {"message": "From settings."}}
    assert resolve_error_policy({"message": "From the argument."}).message == "From the argument."


def test_a_non_mapping_policy_setting_is_rejected(settings):
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"ERROR_POLICY": 12}
    with pytest.raises(ConfigurationError, match="must be an ErrorPolicy or a mapping"):
        resolve_error_policy(None)


def test_an_unknown_option_name_is_rejected_with_the_valid_vocabulary():
    """Naming the valid options in the message is what makes a typo self-correcting."""
    with pytest.raises(ConfigurationError, match=r"Unknown error-policy option\(s\): mesage"):
        resolve_error_policy({"mesage": "typo"})


# ---------------------------------------------------------------------------
# The correlation identifier
# ---------------------------------------------------------------------------


def test_a_correlation_id_is_thirty_two_lowercase_hex_characters():
    """The format is pinned so a log grep for one cannot match anything else."""
    value = new_correlation_id()
    assert len(value) == 32
    assert value == value.lower()
    assert all(character in "0123456789abcdef" for character in value)


def test_correlation_ids_do_not_repeat():
    """Random, not derived: a derived id would be an oracle over the masked text."""
    assert len({new_correlation_id() for _ in range(1000)}) == 1000


# ---------------------------------------------------------------------------
# Schema construction and install position
# ---------------------------------------------------------------------------


def test_the_schema_resolves_and_exposes_its_policy_once():
    """``schema.error_policy`` is the single resolved object the extension reads."""
    schema = DjangoSchema(query=_Query, error_policy={"message": "Nope."})
    assert isinstance(schema.error_policy, ErrorPolicy)
    assert schema.error_policy.message == "Nope."


def test_an_invalid_policy_fails_the_deployment_at_schema_construction():
    """Startup, not the first request that happens to raise."""
    with pytest.raises(ConfigurationError, match=r"Unknown error-policy option\(s\): nope"):
        DjangoSchema(query=_Query, error_policy={"nope": 1})


def test_the_error_policy_extension_is_installed_at_index_zero():
    """Position is the contract, not a detail (spec-048 Decision 10).

    ``on_operation`` teardowns unwind LIFO, so the FIRST-listed extension tears
    down LAST - and masking must be last, after every extension that reads
    ``original_error`` has had its turn. The resource policy's append is asserted
    alongside it, because the two directions are what make the rule ("put the
    extension where its own half of the lifecycle runs last") legible: a future
    refactor that tidies them into a symmetric append fails here rather than
    silently emptying the debug payload's exception rows.
    """
    schema = DjangoSchema(query=_Query)
    assert schema.extensions[0] is DjangoErrorPolicyExtension
    assert schema.extensions[-1] is DjangoResourcePolicyExtension


def test_a_callable_policy_entry_suppresses_the_auto_policy_at_runtime():
    """A factory-produced policy is the consumer's one explicit policy entry."""

    class _FactoryPolicy(DjangoErrorPolicyExtension):
        pass

    def factory():
        return _FactoryPolicy()

    schema = DjangoSchema(query=_Query, extensions=[factory])
    resolved = schema.get_extensions(sync=True)
    policies = [
        extension for extension in resolved if isinstance(extension, DjangoErrorPolicyExtension)
    ]

    assert len(policies) == 1
    assert isinstance(policies[0], _FactoryPolicy)


def test_callable_policy_and_debug_entries_preserve_debug_exception_capture():
    """A callable error policy must not duplicate and preempt debug teardown."""

    def error_factory():
        return DjangoErrorPolicyExtension()

    def debug_factory():
        return DjangoDebugExtension(allow_unsafe_production=True)

    schema = DjangoSchema(query=_Query, extensions=[error_factory, debug_factory])
    result = schema.execute_sync("{ boom }")

    assert len(result.extensions["debug"]["exceptions"]) == 1


def test_a_consumer_extension_is_prepended_behind_the_policy_not_in_front_of_it():
    """A consumer's own extension keeps its order relative to its peers."""

    class _ConsumerExtension(strawberry.extensions.SchemaExtension):
        """A consumer extension with no behavior, present only to hold a position."""

    schema = DjangoSchema(query=_Query, extensions=[_ConsumerExtension])
    assert list(schema.extensions) == [
        DjangoErrorPolicyExtension,
        _ConsumerExtension,
        DjangoResourcePolicyExtension,
    ]


def test_a_consumer_supplied_policy_entry_suppresses_the_prepend_and_keeps_its_position():
    """A consumer who placed the extension themselves gets exactly their entry.

    A second copy would mask an already-masked error and mint a SECOND
    correlation id for it, so the client's id would not be the one in the log
    that carries the traceback. The consumer's chosen index survives, which is
    the whole reason they supplied the entry.
    """

    class _ConsumerPolicyExtension(DjangoErrorPolicyExtension):
        """A consumer subclass, so the suppression check is by class not identity."""

    class _Other(strawberry.extensions.SchemaExtension):
        """A neighbour, so "kept its position" is a real claim."""

    schema = DjangoSchema(query=_Query, extensions=[_Other, _ConsumerPolicyExtension])
    assert list(schema.extensions) == [
        _Other,
        _ConsumerPolicyExtension,
        DjangoResourcePolicyExtension,
    ]
    resolved = schema.get_extensions(sync=True)
    assert sum(isinstance(item, DjangoErrorPolicyExtension) for item in resolved) == 1


def test_an_instance_entry_also_suppresses_the_prepend():
    """The suppression check reads an INSTANCE entry, not only a class entry.

    Called against ``_with_error_policy_extension`` directly rather than through
    ``DjangoSchema``: Strawberry deprecates instance entries in ``extensions=[...]``
    and this suite runs warnings as errors, so no schema can be built with one.
    The install helper is what decides suppression either way.
    """
    installed = DjangoErrorPolicyExtension()
    assert _with_error_policy_extension([installed]) == [installed]


def test_the_disabled_policy_leaves_the_original_message_on_the_wire(settings):
    """The ``{"enabled": False}`` opt-out, read on a real execution under ``DEBUG=False``."""
    assert settings.DEBUG is False
    schema = DjangoSchema(query=_Query, error_policy={"enabled": False})
    result = schema.execute_sync("{ boom }")
    assert _SENSITIVE in result.errors[0].message


@pytest.mark.parametrize("debug_value", ["False", 1, object()])
def test_a_malformed_debug_setting_does_not_disable_production_masking(settings, debug_value):
    """Only an explicit ``DEBUG=True`` opens the development pass-through gate."""
    settings.DEBUG = debug_value
    schema = DjangoSchema(query=_Query)

    result = schema.execute_sync("{ boom }")

    assert result.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in result.errors[0].message


# ---------------------------------------------------------------------------
# The standalone-schema fallback
# ---------------------------------------------------------------------------


def test_a_plain_schema_with_the_extension_installed_by_hand_falls_back_to_the_default(settings):
    """A hand-wired ``strawberry.Schema`` has no ``error_policy`` attribute to read.

    The fallback is the MASKING one on purpose: an extension whose whole job is to
    mask must not quietly become a no-op because it could not find its
    configuration. This is a supported standalone use, so it must not raise
    either.
    """
    assert settings.DEBUG is False
    schema = strawberry.Schema(query=_Query, extensions=[DjangoErrorPolicyExtension])
    assert not hasattr(schema, "error_policy")

    result = schema.execute_sync("{ boom }")
    error = result.errors[0]
    assert error.message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in error.message
    assert error.original_error is None
    assert len(error.extensions[DEFAULT_ERROR_POLICY.correlation_extension_key]) == 32


# ---------------------------------------------------------------------------
# The teardown no-ops
# ---------------------------------------------------------------------------


def _run_teardown(result):
    """Drive one ``on_operation`` teardown over ``result`` under the default policy.

    Built directly rather than through a schema because the two cases below are
    exactly the ones no request produces: a sync parse/validation early return
    leaves ``execution_context.result`` at ``None``, and Strawberry never hands
    the hook a result object it did not build.
    """
    extension = DjangoErrorPolicyExtension()
    # ``SchemaExtension.__init__`` accepts the argument but stores nothing; the
    # engine assigns the attribute, so the harness does the same.
    extension.execution_context = SimpleNamespace(
        schema=SimpleNamespace(error_policy=DEFAULT_ERROR_POLICY),
        result=result,
    )
    hook = extension.on_operation()
    next(hook)
    with pytest.raises(StopIteration):
        next(hook)


def test_a_none_result_is_a_no_op():
    """A parse or validation early return has nothing to mask."""
    _run_teardown(None)


def test_an_error_free_result_is_left_alone():
    """The happy path must not allocate a new error list or touch ``data``."""
    result = GraphQLExecutionResult(data={"ping": 1}, errors=None)
    _run_teardown(result)
    assert result.errors is None
    assert result.data == {"ping": 1}


def test_a_graphql_core_execution_result_is_rewritten_in_place_preserving_order(settings):
    """Both result shapes are served by the one implementation (spec-048 Decision 11).

    Arity and order are preserved whether an entry was masked or not, so a client
    matching errors to its document by index is unaffected - asserted here over a
    mixed list, which a single-error response cannot show.
    """
    assert settings.DEBUG is False
    deliberate = GraphQLError("Deliberate.", original_error=GraphQLError("Deliberate."))
    unexpected = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = GraphQLExecutionResult(data=None, errors=[deliberate, unexpected])

    _run_teardown(result)

    assert len(result.errors) == 2
    assert result.errors[0] is deliberate
    assert result.errors[1].message == DEFAULT_ERROR_POLICY.message
    assert result.errors[1].original_error is None


async def test_an_async_pre_execution_error_keeps_its_own_message(settings):
    """The ``original_error is None`` branch, reached the way a request reaches it.

    That branch is NOT reached by anything graphql-core builds during execution:
    every exception it surfaces from a field - including the value-completion
    ``TypeError`` for a non-nullable ``null`` - arrives ``located_error``-wrapped
    with ``original_error`` set. The branch's real traffic is the ASYNC
    pre-execution path: Strawberry assigns a ``PreExecutionError`` (which IS an
    ``ExecutionResult``, so it passes the teardown's shape gate) carrying the
    validation errors it built from the document itself, and those have nothing
    behind them.

    So the row runs a real async operation that fails validation and requires the
    client to keep reading graphql-core's own explanation of its own mistake -
    masking it would delete information without hiding any.
    """
    assert settings.DEBUG is False
    schema = DjangoSchema(query=_Query)

    result = await schema.execute("{ notAField }")

    assert result.data is None
    assert len(result.errors) == 1
    assert "notAField" in result.errors[0].message
    assert result.errors[0].original_error is None
    assert result.errors[0].extensions in (None, {})


def test_a_value_completion_failure_is_still_masked(settings):
    """A resolver exception surfaced through COMPLETION is unexpected too.

    graphql-core raises from two different phases and wraps both the same way: a
    resolver that raises, and a resolved value that fails to complete (non-null
    propagation, list-item completion, scalar serialization). The classifier reads
    ``original_error`` through that wrapping, so the phase makes no difference -
    which is the property that keeps a masked surface from having a hole shaped
    like the completion phase.

    Exercised through a real execution of a NON-NULL field, where the resolver's
    exception reaches the client via ``Query.explodes``'s completion propagation
    rather than as a nullable field's own entry.
    """
    assert settings.DEBUG is False

    @strawberry.type
    class _NonNullQuery:
        """One non-nullable field whose resolver raises."""

        @strawberry.field
        def explodes(self) -> str:
            raise ValueError(_SENSITIVE)

    schema = DjangoSchema(query=_NonNullQuery)

    result = schema.execute_sync("{ explodes }")

    assert result.data is None
    assert len(result.errors) == 1
    assert result.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in str(result.errors[0].message)
    assert result.errors[0].original_error is None


# ---------------------------------------------------------------------------
# The isinstance-guarded policy read
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "attribute",
    [
        "not a policy",
        {"enabled": False},
        None,
        0,
    ],
)
def test_a_schema_attribute_that_is_not_a_policy_falls_back_to_the_default(attribute):
    """A wrong ``schema.error_policy`` must not become a silent way to stop masking.

    ``getattr(schema, "error_policy", DEFAULT)`` alone answers the default only
    when the attribute is ABSENT; anything present is returned whatever it is, and
    a mapping or a string would then be asked ``policy.enabled`` (raising) or read
    for its truthiness (disabling masking). The fallback is therefore gated on
    ``isinstance``, and it lands on the MASKING default in every wrong-shape case -
    the fail-closed direction. ``DjangoSchema`` cannot produce any of these; a
    consumer subclass or a stray assignment can.
    """
    schema = SimpleNamespace(error_policy=attribute)
    assert schema_error_policy(schema) is DEFAULT_ERROR_POLICY


def test_an_absent_attribute_and_a_real_policy_are_both_read_correctly():
    """The two shapes that are not failures: no attribute at all, and a real policy."""
    assert schema_error_policy(SimpleNamespace()) is DEFAULT_ERROR_POLICY
    policy = ErrorPolicy(message="Mine.")
    assert schema_error_policy(SimpleNamespace(error_policy=policy)) is policy


def test_a_raising_schema_error_policy_property_falls_back_to_the_default():
    """A descriptor or property on schema that raises falls back to the masking default."""

    class _RaisingSchema:
        @property
        def error_policy(self):
            raise RuntimeError("Hostile error_policy read")

    assert schema_error_policy(_RaisingSchema()) is DEFAULT_ERROR_POLICY


# ---------------------------------------------------------------------------
# Masking degrades CLOSED
# ---------------------------------------------------------------------------


class _HostileError:
    """An error-shaped object whose ``original_error`` raises when read.

    Not reachable through a request - graphql-core builds every error on a result
    - but reachable through a consumer extension that put its own object in
    ``result.errors``, and the point of a fail-closed degrade is that it does not
    depend on the object being well behaved.
    """

    message = _SENSITIVE

    @property
    def original_error(self):
        raise RuntimeError(_SENSITIVE)


class _HostileResult:
    """A result-shaped object whose ``errors`` cannot be read at all."""

    data = {"ping": 1}

    @property
    def errors(self):
        raise RuntimeError(_SENSITIVE)


class _HostileStrawberryResult(StrawberryExecutionResult):
    """An admitted result whose error list raises when read but accepts replacement."""

    @property
    def errors(self):
        raise RuntimeError(_SENSITIVE)

    @errors.setter
    def errors(self, value):
        self._replacement_errors = value


class _WriteRejectingStrawberryResult(StrawberryExecutionResult):
    """A stock-shape subclass that rejects adoption after construction."""

    def __setattr__(self, name, value):
        if name == "data" and name in self.__dict__:
            raise RuntimeError("result is frozen")
        super().__setattr__(name, value)


def test_one_error_that_cannot_be_masked_degrades_to_the_policy_message(caplog):
    """A masking failure is a disclosure risk, so it fails CLOSED, not open.

    The tempting degrade - leave the entry as it was found - publishes exactly the
    text the policy exists to withhold, and it publishes it on the one path nobody
    tested. So the entry becomes the policy message with no location and no
    correlation id (nothing may be read off the error that just failed to be
    read), the failure is logged with its traceback, and every OTHER entry in the
    same result is masked normally.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    fine = GraphQLError("Deliberate.", original_error=GraphQLError("Deliberate."))
    result = GraphQLExecutionResult(data=None, errors=[_HostileError(), fine])

    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked is not result
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert masked.errors[0].extensions in (None, {})
    assert masked.errors[1] is fine
    assert _SENSITIVE not in "".join(str(error.message) for error in masked.errors)
    assert any(record.exc_info for record in caplog.records)


def test_a_result_whose_errors_cannot_be_read_degrades_to_one_policy_message(caplog):
    """The outer floor: an unreadable error list still answers something safe.

    One policy-message error and no ``data``. Dropping ``data`` is deliberate - a
    result this module could not read is a result it cannot vouch for - and it is
    the only degrade that changes arity, which is why the per-entry degrade above
    exists to keep the common case faithful.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")

    masked = mask_execution_result(_HostileResult(), DEFAULT_ERROR_POLICY)

    assert masked.data is None
    assert len(masked.errors) == 1
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert any(record.exc_info for record in caplog.records)


def test_the_extension_adopts_all_fields_of_the_outer_fail_closed_degrade(caplog):
    """An unreadable result retains neither data nor extensions after the floor applies.

    The degrade drops all three fields, so the adoption must overwrite the
    populated ``extensions`` map too -- leaving it in place would publish
    whatever the failed result carried there.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    result = _HostileStrawberryResult(
        data={"secret": _SENSITIVE},
        errors=[],
        extensions={"leak": _SENSITIVE},
    )
    extension = DjangoErrorPolicyExtension()
    extension.execution_context = SimpleNamespace(
        schema=SimpleNamespace(error_policy=DEFAULT_ERROR_POLICY),
        result=result,
    )

    extension._process_result(result, DEFAULT_ERROR_POLICY)

    assert result.data is None
    assert result._replacement_errors[0].message == DEFAULT_ERROR_POLICY.message
    assert result.extensions is None
    assert any(record.exc_info for record in caplog.records)


def test_the_extension_replaces_a_result_that_rejects_safe_field_adoption(caplog):
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    result = _WriteRejectingStrawberryResult(
        data={"secret": _SENSITIVE},
        errors=[GraphQLError(_SENSITIVE, original_error=RuntimeError(_SENSITIVE))],
    )
    extension = DjangoErrorPolicyExtension()
    context = SimpleNamespace(
        schema=SimpleNamespace(error_policy=DEFAULT_ERROR_POLICY),
        result=result,
    )
    extension.execution_context = context

    extension._process_result(result, DEFAULT_ERROR_POLICY)

    assert context.result is not result
    assert context.result.data is None
    assert context.result.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert any(record.exc_info for record in caplog.records)


def test_a_non_graphql_error_with_none_original_error_is_masked_as_unexpected():
    """Any non-GraphQLError object in errors is classified as unexpected and masked."""

    class _CustomError:
        message = _SENSITIVE
        original_error = None

    error = _CustomError()
    result = StrawberryExecutionResult(data={"data": 123}, errors=[error])
    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked.data == {"data": 123}
    assert len(masked.errors) == 1
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in str(masked.errors[0].message)


def test_a_generator_or_iterator_error_list_is_masked_preserving_data():
    """An iterator or generator on result.errors is consumed safely without crashing zip."""
    original = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = StrawberryExecutionResult(
        data={"safe_field": 42},
        errors=(err for err in [original]),
    )
    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked.data == {"safe_field": 42}
    assert len(masked.errors) == 1
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message


def test_the_extension_teardown_fails_closed_when_context_schema_raises(caplog):
    """If extension teardown encounters a hostile schema or context, it degrades safely."""
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    extension = DjangoErrorPolicyExtension()

    class _HostileContext:
        @property
        def schema(self):
            raise RuntimeError("Hostile schema lookup")

        @property
        def result(self):
            return StrawberryExecutionResult(
                data={"leak": _SENSITIVE},
                errors=[GraphQLError(_SENSITIVE, original_error=RuntimeError(_SENSITIVE))],
            )

        @result.setter
        def result(self, val):
            self._result = val

    ctx = _HostileContext()
    extension.execution_context = ctx

    gen = extension.on_operation()
    next(gen)
    with contextlib.suppress(StopIteration):
        next(gen)

    assert hasattr(ctx, "_result")
    assert ctx._result.data is None
    assert ctx._result.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert any(
        "The error policy encountered an unhandled exception during teardown" in r.message
        for r in caplog.records
    )


# ---------------------------------------------------------------------------
# The per-event seam's contract with the extensions that read originals
# ---------------------------------------------------------------------------


def test_masking_returns_the_same_object_when_nothing_needed_masking():
    """Identity, so the caller can tell "nothing happened" without comparing lists."""
    deliberate = GraphQLError("Deliberate.", original_error=GraphQLError("Deliberate."))
    result = GraphQLExecutionResult(data=None, errors=[deliberate])

    assert mask_execution_result(result, DEFAULT_ERROR_POLICY) is result
    assert (
        mask_execution_result(
            GraphQLExecutionResult(data={"ping": 1}, errors=None),
            DEFAULT_ERROR_POLICY,
        ).errors
        is None
    )


def test_masking_leaves_the_original_result_holding_its_originals():
    """The COPY is what makes the per-event seam safe for the debug extension.

    The subscription seam masks each event before delivery, and the engine's own
    result object is the one an extension reading ``GraphQLError.original_error``
    sees at teardown. Masking a copy is what keeps the LIFO ordering promise true
    on the subscription path as well as the query path - an in-place rewrite here
    would empty the debug payload's exception rows for every subscription.
    """
    original = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = GraphQLExecutionResult(data={"leaky": None}, errors=[original])

    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked is not result
    assert result.errors == [original]
    assert isinstance(result.errors[0].original_error, ValueError)
    assert masked.data == {"leaky": None}
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message


def test_error_policy_extension_on_operation_exploding_execution_context():
    """Execution context with exploding result setter is safely ignored during exception handling."""
    from django_strawberry_framework.extensions.error_policy import (
        DjangoErrorPolicyExtension,
    )

    ext = DjangoErrorPolicyExtension()

    call_count = 0

    def _exploding_policy():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("first policy call explodes")
        return DEFAULT_ERROR_POLICY

    ext._policy = _exploding_policy

    class ExplodingExecutionContext:
        @property
        def result(self):
            return None

        @result.setter
        def result(self, val):
            raise RuntimeError("cannot set result")

    ext.execution_context = ExplodingExecutionContext()
    gen = ext.on_operation()
    next(gen)
    with contextlib.suppress(StopIteration):
        next(gen)
