"""Shared mutation-error constructors remain total over hostile metadata."""

from django.core.exceptions import ValidationError

from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.utils.errors import (
    field_error,
    join_error_path,
    relation_field_error,
    validation_error_to_field_errors,
)


class _HostileString:
    def __str__(self):
        raise RuntimeError("hostile message string")

    def __repr__(self):
        raise RuntimeError("hostile message repr")


class _HostilePath(str):
    def __bool__(self):
        raise RuntimeError("hostile path truthiness")

    def __eq__(self, other):
        raise RuntimeError("hostile path equality")

    def split(self, *args, **kwargs):
        raise RuntimeError("hostile path split")


class _HostileIterable:
    def __iter__(self):
        raise RuntimeError("hostile iterable")


def test_field_error_normalizes_hostile_string_subclass_paths_and_messages():
    error = field_error(_HostilePath("items.0.name"), [_HostileString()])

    assert error.field == "items.0.name"
    assert error.path == ["items", "0", "name"]
    assert error.messages == ["<unprintable _HostileString>"]


def test_relation_field_error_and_path_joining_normalize_hostile_string_subclasses():
    relation_error = relation_field_error(_HostilePath("categoryId"))

    assert relation_error.field == "categoryId"
    assert relation_error.messages == ["Invalid id for relation 'categoryId'."]
    assert join_error_path(_HostilePath("items.0"), _HostilePath("name")) == "items.0.name"


def test_validation_error_mapper_survives_hostile_message_objects():
    (error,) = validation_error_to_field_errors(
        ValidationError({"name": [_HostileString()]}),
    )

    assert error.field == "name"
    assert error.messages == ["<unprintable _HostileString>"]


def test_validation_error_mapper_keeps_normal_codes_and_non_field_shape():
    (error,) = validation_error_to_field_errors(
        ValidationError("whole-object", code="invalid"),
    )

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.path == []
    assert error.messages == ["whole-object"]
    assert error.codes == ["invalid"]


def test_validation_error_mapper_degrades_malformed_error_dict_entries():
    exception = ValidationError("whole-object")

    class _MalformedErrorDict:
        def items(self):
            return [("missing-value",)]

    exception.error_dict = _MalformedErrorDict()
    (error,) = validation_error_to_field_errors(exception)

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["Validation details could not be normalized."]
    assert error.codes == ["invalid"]


def test_field_error_degrades_an_unreadable_message_container():
    error = field_error("name", _HostileIterable())

    assert error.field == "name"
    assert error.messages == ["<unprintable _HostileIterable>"]


def test_validation_error_mapper_degrades_unreadable_dict_and_fallback_metadata():
    class _UnreadableErrorDict:
        def items(self):
            raise RuntimeError("hostile error items")

    class _MalformedValidationError:
        error_dict = _UnreadableErrorDict()

        @property
        def error_list(self):
            raise RuntimeError("hostile error list")

        @property
        def messages(self):
            raise RuntimeError("hostile messages")

        def __str__(self):
            return "unreadable validation details"

    (error,) = validation_error_to_field_errors(_MalformedValidationError())

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["unreadable validation details"]
    assert error.codes == []


def test_validation_error_mapper_degrades_unreadable_field_error_metadata():
    class _UnreadableFieldErrors:
        def __iter__(self):
            raise RuntimeError("hostile field errors")

        @property
        def messages(self):
            raise RuntimeError("hostile leaf messages")

        @property
        def message(self):
            raise RuntimeError("hostile leaf message")

        @property
        def error_list(self):
            raise RuntimeError("hostile leaf list")

        def __str__(self):
            return "unreadable field details"

    class _MalformedValidationError:
        error_dict = {"name": _UnreadableFieldErrors()}

    (error,) = validation_error_to_field_errors(_MalformedValidationError())

    assert error.field == "name"
    assert error.messages == ["unreadable field details"]
    assert error.codes == []


def test_validation_error_mapper_drops_an_unreadable_leaf_code():
    class _UnreadableCode:
        @property
        def code(self):
            raise RuntimeError("hostile code")

    class _MalformedValidationError:
        error_dict = None
        error_list = (_UnreadableCode(),)
        messages = ("invalid value",)

    (error,) = validation_error_to_field_errors(_MalformedValidationError())

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["invalid value"]
    assert error.codes == []
