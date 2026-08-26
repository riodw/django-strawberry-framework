"""Tests for canonical mutation operation descriptors (operations.py)."""

from __future__ import annotations

import dataclasses

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.inputs import CREATE, PARTIAL
from django_strawberry_framework.mutations.operations import (
    _OPERATION_INPUT_OVERRIDE_ATTR,
    _OPERATION_PERMISSION_ACTION,
    _VALID_OPERATIONS,
    NON_DELETE_OPERATION_INPUT_KIND,
    NON_DELETE_WRITE_OPERATIONS,
    OPERATION_CREATE,
    OPERATION_DELETE,
    OPERATION_FORM,
    OPERATION_UPDATE,
    MutationOperationDescriptor,
    get_operation_descriptor,
    non_delete_operation_error,
    operation_takes_data,
    operation_takes_id,
)


class _HostileRepr:
    def __repr__(self):
        raise RuntimeError("HostileRepr exploded")


def test_mutation_operation_descriptor_immutability():
    """MutationOperationDescriptor instances are frozen dataclasses."""
    desc = OPERATION_CREATE
    assert isinstance(desc, MutationOperationDescriptor)
    assert dataclasses.is_dataclass(desc)
    with pytest.raises(dataclasses.FrozenInstanceError):
        desc.name = "other"  # type: ignore[misc]


def test_operation_descriptors_invariants():
    """All standard operation descriptors match expected invariants."""
    assert OPERATION_CREATE.name == "create"
    assert OPERATION_CREATE.input_kind == CREATE
    assert OPERATION_CREATE.input_override_attr == "input_class"
    assert not OPERATION_CREATE.has_id_arg
    assert OPERATION_CREATE.has_data_arg
    assert OPERATION_CREATE.permission_action == "add"
    assert OPERATION_CREATE.supports_model_mutation
    assert OPERATION_CREATE.supports_form_mutation

    assert OPERATION_UPDATE.name == "update"
    assert OPERATION_UPDATE.input_kind == PARTIAL
    assert OPERATION_UPDATE.input_override_attr == "partial_input_class"
    assert OPERATION_UPDATE.has_id_arg
    assert OPERATION_UPDATE.has_data_arg
    assert OPERATION_UPDATE.permission_action == "change"
    assert OPERATION_UPDATE.supports_model_mutation
    assert OPERATION_UPDATE.supports_form_mutation

    assert OPERATION_DELETE.name == "delete"
    assert OPERATION_DELETE.input_kind is None
    assert OPERATION_DELETE.input_override_attr is None
    assert OPERATION_DELETE.has_id_arg
    assert not OPERATION_DELETE.has_data_arg
    assert OPERATION_DELETE.permission_action == "delete"
    assert OPERATION_DELETE.supports_model_mutation
    assert not OPERATION_DELETE.supports_form_mutation

    assert OPERATION_FORM.name == "form"
    assert OPERATION_FORM.input_kind is None
    assert OPERATION_FORM.input_override_attr is None
    assert not OPERATION_FORM.has_id_arg
    assert OPERATION_FORM.has_data_arg
    assert OPERATION_FORM.permission_action is None
    assert not OPERATION_FORM.supports_model_mutation
    assert OPERATION_FORM.supports_form_mutation


def test_get_operation_descriptor():
    """get_operation_descriptor resolves known operations and returns None for unknown."""
    assert get_operation_descriptor("create") is OPERATION_CREATE
    assert get_operation_descriptor("update") is OPERATION_UPDATE
    assert get_operation_descriptor("delete") is OPERATION_DELETE
    assert get_operation_descriptor("form") is OPERATION_FORM
    assert get_operation_descriptor("unknown") is None
    assert get_operation_descriptor("") is None


def test_operation_takes_id():
    """operation_takes_id returns True only for operations taking an id argument."""
    assert not operation_takes_id("create")
    assert operation_takes_id("update")
    assert operation_takes_id("delete")
    assert not operation_takes_id("form")
    assert not operation_takes_id("unknown")


def test_operation_takes_data():
    """operation_takes_data returns True only for operations taking a data argument."""
    assert operation_takes_data("create")
    assert operation_takes_data("update")
    assert not operation_takes_data("delete")
    assert operation_takes_data("form")
    assert not operation_takes_data("unknown")


def test_derived_mappings_and_sets():
    """Derived operation mappings and sets match expected values."""
    assert NON_DELETE_OPERATION_INPUT_KIND == {"create": CREATE, "update": PARTIAL}
    assert _OPERATION_INPUT_OVERRIDE_ATTR == {
        "create": "input_class",
        "update": "partial_input_class",
    }
    assert frozenset({"create", "update"}) == NON_DELETE_WRITE_OPERATIONS
    assert frozenset({"create", "update", "delete"}) == _VALID_OPERATIONS
    assert _OPERATION_PERMISSION_ACTION == {
        "create": "add",
        "update": "change",
        "delete": "delete",
    }


def test_non_delete_operation_error_formatting():
    """non_delete_operation_error formats ConfigurationError and contains hostile reprs."""
    err = non_delete_operation_error("DjangoModelFormMutation", "ItemMutation", "delete")
    assert isinstance(err, ConfigurationError)
    assert (
        "DjangoModelFormMutation ItemMutation.Meta.operation must be one of ['create', 'update']; got 'delete'."
        in str(err)
    )

    hostile_err = non_delete_operation_error("SerializerMutation", "OrderMutation", _HostileRepr())
    assert isinstance(hostile_err, ConfigurationError)
    assert "<unprintable _HostileRepr>" in str(hostile_err)
