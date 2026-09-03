"""Shared mutation-error constructors remain total over hostile metadata."""

import ast
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError

from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.utils import errors as errors_module
from django_strawberry_framework.utils.errors import (
    FIELD_ERROR_CODE_CONFLICT,
    FIELD_ERROR_CODE_CONSTRAINT,
    FIELD_ERROR_CODE_INVALID,
    FIELD_ERROR_CODE_NOT_FOUND,
    FIELD_ERROR_CODE_NULL,
    FIELD_ERROR_CODE_PROTECTED,
    FIELD_ERROR_CODE_TRUNCATED,
    FILTER_INVALID_ERROR_CODE,
    GLOBALID_INVALID_ERROR_CODE,
    GLOBALID_UNVALIDATABLE_ERROR_CODE,
    coded_error_extensions,
    empty_validation_error,
    field_error,
    integrity_error_field_errors,
    join_error_path,
    null_field_error,
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


@pytest.mark.parametrize(
    ("payload", "field"),
    [({}, NON_FIELD_ERROR_KEY), ([], NON_FIELD_ERROR_KEY), ({"name": []}, "name")],
)
def test_validation_error_mapper_never_returns_an_empty_envelope(payload, field):
    (error,) = validation_error_to_field_errors(ValidationError(payload))

    assert error.field == field
    assert error.messages == ["Validation failed without error details."]
    assert error.codes == ["invalid"]


def test_field_error_handles_scalar_integers_booleans_and_floats():
    error_int = field_error("count", 123, codes=456)
    assert error_int.field == "count"
    assert error_int.messages == ["123"]
    assert error_int.codes == ["456"]

    error_bool = field_error("active", False, codes=True)
    assert error_bool.field == "active"
    assert error_bool.messages == ["False"]
    assert error_bool.codes == ["True"]

    error_float = field_error("score", 98.6)
    assert error_float.field == "score"
    assert error_float.messages == ["98.6"]
    assert error_float.codes == []


def test_field_error_handles_byte_strings_without_splitting():
    error = field_error("token", b"invalid_token", codes=b"invalid")
    assert error.field == "token"
    assert error.messages == ["b'invalid_token'"]
    assert error.codes == ["b'invalid'"]


def test_validation_error_mapper_handles_bare_string_and_byte_values_in_error_dict():
    class _BareStringDictError:
        error_dict = {"title": "This title is already taken", "code": b"invalid_code"}

    errors = validation_error_to_field_errors(_BareStringDictError())
    assert len(errors) == 2
    by_field = {e.field: e for e in errors}
    assert by_field["title"].messages == ["This title is already taken"]
    assert by_field["code"].messages == ["b'invalid_code'"]


def test_validation_error_mapper_handles_leaf_with_string_messages_attribute():
    class _StringMessagesError:
        messages = "Single error message as string"

    (error,) = validation_error_to_field_errors(_StringMessagesError())
    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["Single error message as string"]


def test_validation_error_mapper_extracts_code_from_leaf_without_error_list():
    class _CodeOnlyError:
        code = "permission_denied"
        message = "Permission denied for operation"

    (error,) = validation_error_to_field_errors(_CodeOnlyError())
    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["Permission denied for operation"]
    assert error.codes == ["permission_denied"]


def test_field_error_and_join_path_survive_hostile_class_property():
    class _HostileClass:
        @property
        def __class__(self):
            raise RuntimeError("hostile __class__")

        def __str__(self):
            return "hostile_instance"

    bad = _HostileClass()
    err = field_error(bad, bad, codes=bad)
    assert err.field == "<unprintable _HostileClass>"
    assert err.messages == ["<unprintable _HostileClass>"]
    assert err.codes == ["<unprintable _HostileClass>"]
    assert join_error_path(bad, "child") == "<unprintable _HostileClass>.child"


def test_validation_error_mapper_handles_leaf_with_message_collection_when_messages_raises():
    class _CollectionMessageError:
        @property
        def messages(self):
            raise RuntimeError("hostile messages")

        message = ["First message", "Second message"]

    errors = validation_error_to_field_errors(_CollectionMessageError())
    assert len(errors) == 1
    assert errors[0].messages == ["First message", "Second message"]


def test_field_error_handles_lazy_translation_proxy_without_character_iteration():
    """Verify Django lazy translation proxies (Promise) are treated as atomic strings."""
    from django.utils.translation import gettext_lazy as _

    lazy_msg = _("This field is required.")
    lazy_code = _("required")
    error = field_error("title", lazy_msg, codes=lazy_code)

    assert error.field == "title"
    assert error.messages == ["This field is required."]
    assert error.codes == ["required"]


def test_validation_error_mapper_handles_lazy_translation_objects():
    """Verify ValidationError containing lazy translations formats cleanly into FieldError."""
    from django.utils.translation import gettext_lazy as _

    lazy_msg = _("Invalid choice selected.")
    ve_dict = ValidationError({"status": [lazy_msg]})
    errors = validation_error_to_field_errors(ve_dict)

    assert len(errors) == 1
    assert errors[0].field == "status"
    assert errors[0].messages == ["Invalid choice selected."]

    ve_scalar = ValidationError(_("Global model validation error."), code="invalid")
    (global_err,) = validation_error_to_field_errors(ve_scalar)
    assert global_err.field == NON_FIELD_ERROR_KEY
    assert global_err.messages == ["Global model validation error."]
    assert global_err.codes == ["invalid"]


def test_integrity_error_field_errors_shape_and_sentinel():
    """Verify integrity_error_field_errors returns standard constraint error envelope."""
    (error,) = integrity_error_field_errors()
    assert error.field == NON_FIELD_ERROR_KEY
    assert error.path == []
    assert error.messages == ["A database constraint was violated."]
    assert error.codes == ["constraint"]


@pytest.mark.parametrize(
    ("prefix", "segment", "expected"),
    [
        ("", "name", "name"),
        (None, "name", "name"),
        ("items", "0", "items.0"),
        ("items.0", "name", "items.0.name"),
        ("items.0", "__all__", "items.0.__all__"),
    ],
)
def test_join_error_path_variations(prefix, segment, expected):
    """Verify join_error_path joins prefixes and child segments correctly."""
    assert join_error_path(prefix, segment) == expected


# -------------------------------------------------------------------------
# The error-code vocabulary: public wire contract (bug-hunt batch 13 pins)
# -------------------------------------------------------------------------


def test_field_error_code_vocabulary_is_the_public_wire_contract():
    assert FIELD_ERROR_CODE_INVALID == "invalid"
    assert FIELD_ERROR_CODE_NULL == "null"
    assert FIELD_ERROR_CODE_CONSTRAINT == "constraint"
    assert FIELD_ERROR_CODE_NOT_FOUND == "not_found"
    assert FIELD_ERROR_CODE_PROTECTED == "protected"
    assert FIELD_ERROR_CODE_CONFLICT == "conflict"
    assert FIELD_ERROR_CODE_TRUNCATED == "truncated"
    assert GLOBALID_INVALID_ERROR_CODE == "GLOBALID_INVALID"
    assert GLOBALID_UNVALIDATABLE_ERROR_CODE == "GLOBALID_UNVALIDATABLE"
    assert FILTER_INVALID_ERROR_CODE == "FILTER_INVALID"
    for name in (
        "FIELD_ERROR_CODE_INVALID",
        "FIELD_ERROR_CODE_NULL",
        "FIELD_ERROR_CODE_CONSTRAINT",
        "FIELD_ERROR_CODE_NOT_FOUND",
        "FIELD_ERROR_CODE_PROTECTED",
        "FIELD_ERROR_CODE_CONFLICT",
        "FIELD_ERROR_CODE_TRUNCATED",
        "GLOBALID_INVALID_ERROR_CODE",
        "GLOBALID_UNVALIDATABLE_ERROR_CODE",
        "FILTER_INVALID_ERROR_CODE",
        "coded_error_extensions",
        "empty_validation_error",
        "null_field_error",
    ):
        assert name in errors_module.__all__


def test_coded_error_extensions_shape():
    assert coded_error_extensions("GLOBALID_INVALID") == {"code": "GLOBALID_INVALID"}
    assert coded_error_extensions("FILTER_INVALID", errors={"name": "bad"}) == {
        "code": "FILTER_INVALID",
        "errors": {"name": "bad"},
    }
    assert coded_error_extensions("X", bound=5, limit=3, charged=7) == {
        "code": "X",
        "bound": 5,
        "limit": 3,
        "charged": 7,
    }


def test_null_field_error_and_empty_validation_error_leaf_shapes():
    null_leaf = null_field_error("categoryId")
    assert null_leaf.field == "categoryId"
    assert null_leaf.messages == ["This field cannot be null."]
    assert null_leaf.codes == [FIELD_ERROR_CODE_NULL]
    assert null_leaf.path == ["categoryId"]

    root_empty = empty_validation_error()
    assert root_empty.field == NON_FIELD_ERROR_KEY
    assert root_empty.messages == ["Validation failed without error details."]
    assert root_empty.codes == [FIELD_ERROR_CODE_INVALID]
    assert root_empty.path == []

    named_empty = empty_validation_error("name")
    assert named_empty.field == "name"
    assert named_empty.path == ["name"]


def test_conflict_code_reaches_the_leaf_through_the_public_ctor():
    leaf = field_error(
        "id",
        "The row was changed or removed by a concurrent operation; retry.",
        codes=FIELD_ERROR_CODE_CONFLICT,
    )

    assert leaf.field == "id"
    assert leaf.codes == [FIELD_ERROR_CODE_CONFLICT]
    assert leaf.path == ["id"]


def test_validation_error_mapper_keys_django_non_field_bucket_to_sentinel():
    exception = ValidationError(
        {"__all__": [ValidationError("model wide", code="mw")], "name": [ValidationError("bad")]},
    )

    by_field = {error.field: error for error in validation_error_to_field_errors(exception)}

    assert by_field[NON_FIELD_ERROR_KEY].path == []
    assert by_field[NON_FIELD_ERROR_KEY].messages == ["model wide"]
    assert by_field[NON_FIELD_ERROR_KEY].codes == ["mw"]
    assert by_field["name"].messages == ["bad"]


def test_field_error_degrades_a_midway_raising_iterator_to_one_unprintable_leaf():
    class _MidwayIterator:
        consumed = 0

        def __iter__(self):
            return self

        def __next__(self):
            self.consumed += 1
            if self.consumed > 1:
                raise RuntimeError("midway iterator failure")
            return "first message"

    iterator = _MidwayIterator()
    error = field_error("name", iterator)

    assert iterator.consumed >= 1
    assert error.messages == ["<unprintable _MidwayIterator>"]


def test_validation_error_mapper_drops_a_hostile_truthiness_leaf_code():
    class _HostileBoolCode(int):
        def __bool__(self):
            raise RuntimeError("hostile code truthiness")

    class _Leaf:
        code = _HostileBoolCode(1)

    class _MalformedValidationError:
        error_dict = None
        error_list = (_Leaf(),)
        messages = ("msg",)

    (error,) = validation_error_to_field_errors(_MalformedValidationError())

    assert error.messages == ["msg"]
    assert error.codes == []


def test_errors_module_performs_no_settings_reads():
    """The error leaf module is configuration-free (layering pin)."""
    source = Path(errors_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, filename="errors.py")

    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ("DEBUG", "settings"):
            hits.append(f"attr {node.attr} @ line {node.lineno}")
        if isinstance(node, ast.Name) and node.id in ("settings", "conf"):
            hits.append(f"name {node.id} @ line {node.lineno}")

    assert hits == [], hits


@pytest.mark.parametrize(
    "atom",
    [
        "atom list",
        b"atom list",
        bytearray(b"atom list"),
        memoryview(b"atom list"),
    ],
)
def test_validation_error_mapper_treats_a_text_atom_error_list_as_one_leaf(atom):
    """A text atom planted in the ``error_list`` slot is ONE leaf, never iterated.

    The hostile slot shape would otherwise explode into per-character /
    per-byte leaves (and per-character code reads); ``_validation_leaves``
    returns the atom itself as the single leaf, whose own ``code`` read then
    fails contained.
    """

    class _TextAtomErrorList:
        error_dict = None
        error_list = atom
        messages = ("whole-object",)

    (error,) = validation_error_to_field_errors(_TextAtomErrorList())

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["whole-object"]
    assert error.codes == []
