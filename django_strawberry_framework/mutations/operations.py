"""Canonical mutation operation descriptors (spec-036, spec-038, spec-039).

Single authoritative home for the write-side operation vocabulary (``create``,
``update``, ``delete``, plus the plain form ``form`` sentinel). Centralizes:
- input generator kinds (``CREATE``, ``PARTIAL``);
- consumer input override attributes (``input_class``, ``partial_input_class``);
- GraphQL argument structure (``id``, ``data``);
- Django model permission action codenames (``add``, ``change``, ``delete``);
- flavor support and argument structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..exceptions import ConfigurationError, _safe_arg_repr
from .inputs import CREATE, PARTIAL


@dataclass(frozen=True, slots=True)
class MutationOperationDescriptor:
    """Authoritative descriptor for a single mutation operation kind."""

    name: str
    input_kind: str | None
    input_override_attr: str | None
    has_id_arg: bool
    has_data_arg: bool
    permission_action: str | None
    supports_model_mutation: bool
    supports_form_mutation: bool


OPERATION_CREATE = MutationOperationDescriptor(
    name="create",
    input_kind=CREATE,
    input_override_attr="input_class",
    has_id_arg=False,
    has_data_arg=True,
    permission_action="add",
    supports_model_mutation=True,
    supports_form_mutation=True,
)

OPERATION_UPDATE = MutationOperationDescriptor(
    name="update",
    input_kind=PARTIAL,
    input_override_attr="partial_input_class",
    has_id_arg=True,
    has_data_arg=True,
    permission_action="change",
    supports_model_mutation=True,
    supports_form_mutation=True,
)

OPERATION_DELETE = MutationOperationDescriptor(
    name="delete",
    input_kind=None,
    input_override_attr=None,
    has_id_arg=True,
    has_data_arg=False,
    permission_action="delete",
    supports_model_mutation=True,
    supports_form_mutation=False,
)

OPERATION_FORM = MutationOperationDescriptor(
    name="form",
    input_kind=None,
    input_override_attr=None,
    has_id_arg=False,
    has_data_arg=True,
    permission_action=None,
    supports_model_mutation=False,
    supports_form_mutation=True,
)

_OPERATIONS_BY_NAME: dict[str, MutationOperationDescriptor] = {
    op.name: op
    for op in (
        OPERATION_CREATE,
        OPERATION_UPDATE,
        OPERATION_DELETE,
        OPERATION_FORM,
    )
}


def get_operation_descriptor(name: str) -> MutationOperationDescriptor | None:
    """Return the descriptor for a named mutation operation, or ``None``."""
    return _OPERATIONS_BY_NAME.get(name)


def operation_takes_id(name: str) -> bool:
    """Return whether an operation takes a root ``id: ID!`` argument."""
    desc = get_operation_descriptor(name)
    return desc.has_id_arg if desc is not None else False


def operation_takes_data(name: str) -> bool:
    """Return whether an operation takes a root ``data: ...`` argument."""
    desc = get_operation_descriptor(name)
    return desc.has_data_arg if desc is not None else False


#: Mapping of operation name to input generator kind (``CREATE`` / ``PARTIAL``)
#: for operations that materialize an input class.
NON_DELETE_OPERATION_INPUT_KIND: dict[str, str] = {
    op.name: op.input_kind for op in _OPERATIONS_BY_NAME.values() if op.input_kind is not None
}

#: Consumer override attribute each non-delete model operation honors.
_OPERATION_INPUT_OVERRIDE_ATTR: dict[str, str] = {
    op.name: op.input_override_attr
    for op in _OPERATIONS_BY_NAME.values()
    if op.input_override_attr is not None
}

#: The create/update-only write operations shared across model, form, and serializer flavors.
NON_DELETE_WRITE_OPERATIONS: frozenset[str] = frozenset(
    op.name
    for op in _OPERATIONS_BY_NAME.values()
    if op.supports_form_mutation and op.name != "form"
)

#: The three valid model-flavor ``Meta.operation`` values (``create``, ``update``, ``delete``).
_VALID_OPERATIONS: frozenset[str] = frozenset(
    op.name for op in _OPERATIONS_BY_NAME.values() if op.supports_model_mutation
)

#: Mapping of operation name to Django model permission action codename (``add``, ``change``, ``delete``).
_OPERATION_PERMISSION_ACTION: dict[str, str] = {
    op.name: op.permission_action
    for op in _OPERATIONS_BY_NAME.values()
    if op.permission_action is not None
}


def non_delete_operation_error(base_label: str, name: str, got: Any) -> ConfigurationError:
    """Build the shared "operation must be create/update" reject.

    Single-sites the create/update-only operation reject message both the form and
    serializer ``_validate_meta`` raise for a bad / ``"delete"`` ``Meta.operation``:
    the SET (``NON_DELETE_WRITE_OPERATIONS``) is single-sourced AND the message
    string is too, so the two flavors cannot drift on the wording. ``base_label``
    names the offending base (``"DjangoModelFormMutation"`` /
    ``"SerializerMutation"``); ``got`` is the rejected value. Names the no-delete
    reason so a consumer who copied a ``036`` ``Meta.operation = "delete"`` gets a
    clear redirect rather than a bare allowed-values list.
    """
    return ConfigurationError(
        f"{base_label} {name}.Meta.operation must be one of "
        f"{sorted(NON_DELETE_WRITE_OPERATIONS)}; got {_safe_arg_repr(got)}. "
        "(This flavor has no delete pipeline - declare a 036 DjangoMutation with "
        "operation='delete' instead.)",
    )
