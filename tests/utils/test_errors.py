"""Shared mutation-error constructors remain total over hostile metadata.

Hostile string subclasses, midway iterators, and lazy translation proxies never
arrive on the wire; the constructors must still return a FieldError. Consumer
envelopes (constraint ``codes``, ``__all__`` sentinel, relation ``not_found``)
live in ``examples/fakeshop/test_query/test_products_api.py``. The error key map
primitives (``build_error_key_map``, ``rekey_error_segment``,
``model_field_error_names``) are pinned here directly; the per-flavor keying matrix
is ``tests/utils/test_error_keys.py``.
"""

import ast
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from apps.library import models as library_models
from apps.products import models as product_models
from django.core.exceptions import ValidationError
from django.db.models import Model
from typing_extensions import override

from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY, FieldError
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
    build_error_key_map,
    coded_error_extensions,
    empty_validation_error,
    field_error,
    join_error_path,
    model_field_error_names,
    null_field_error,
    rekey_error_segment,
    relation_field_error,
    validation_error_to_field_errors,
)
from django_strawberry_framework.utils.inputs import RELATION_SINGLE, SCALAR, InputFieldSpec

if TYPE_CHECKING:
    from django_strawberry_framework.utils.errors import ErrorKeyMap


def _as_validation_error(stand_in: object) -> ValidationError:
    """Hand a duck-typed validation error to the mapper that takes a Django ValidationError."""
    # basedpyright: a stand-in validation error carrying only the slots the code under test reads;
    # validation_error_to_field_errors types the parameter as ValidationError
    return stand_in  # pyright: ignore[reportReturnType]


class _HostileString:
    @override
    def __str__(self):
        raise RuntimeError("hostile message string")

    @override
    def __repr__(self):
        raise RuntimeError("hostile message repr")


class _HostilePath(str):
    def __bool__(self):
        raise RuntimeError("hostile path truthiness")

    @override
    def __eq__(self, other: object):
        raise RuntimeError("hostile path equality")

    @override
    def split(self, *args: object, **kwargs: object):
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

    # basedpyright: the malformed error_dict is the hostile input under test; the stubs type it
    # as the dict a ValidationError builds itself
    exception.error_dict = _MalformedErrorDict()  # pyright: ignore[reportAttributeAccessIssue]
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

        @override
        def __str__(self):
            return "unreadable validation details"

    (error,) = validation_error_to_field_errors(_as_validation_error(_MalformedValidationError()))

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

        @override
        def __str__(self):
            return "unreadable field details"

    class _MalformedValidationError:
        error_dict = {"name": _UnreadableFieldErrors()}

    (error,) = validation_error_to_field_errors(_as_validation_error(_MalformedValidationError()))

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

    (error,) = validation_error_to_field_errors(_as_validation_error(_MalformedValidationError()))

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["invalid value"]
    assert error.codes == []


@pytest.mark.parametrize(
    ("payload", "field"),
    [({}, NON_FIELD_ERROR_KEY), ([], NON_FIELD_ERROR_KEY), ({"name": []}, "name")],
)
def test_validation_error_mapper_never_returns_an_empty_envelope(
    payload: dict[str, list[str]] | list[str],
    field: str,
):
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

    errors = validation_error_to_field_errors(_as_validation_error(_BareStringDictError()))
    assert len(errors) == 2
    by_field = {e.field: e for e in errors}
    assert by_field["title"].messages == ["This title is already taken"]
    assert by_field["code"].messages == ["b'invalid_code'"]


def test_validation_error_mapper_handles_leaf_with_string_messages_attribute():
    class _StringMessagesError:
        messages = "Single error message as string"

    (error,) = validation_error_to_field_errors(_as_validation_error(_StringMessagesError()))
    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["Single error message as string"]


def test_validation_error_mapper_extracts_code_from_leaf_without_error_list():
    class _CodeOnlyError:
        code = "permission_denied"
        message = "Permission denied for operation"

    (error,) = validation_error_to_field_errors(_as_validation_error(_CodeOnlyError()))
    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["Permission denied for operation"]
    assert error.codes == ["permission_denied"]


def test_field_error_and_join_path_survive_hostile_class_property():
    class _HostileClass:
        @property
        @override
        # basedpyright: deliberately a read-only ``__class__`` that raises: the hostile object is the guard's input
        def __class__(self):  # pyright: ignore[reportIncompatibleMethodOverride]
            raise RuntimeError("hostile __class__")

        @override
        def __str__(self):
            return "hostile_instance"

    bad = _HostileClass()
    # basedpyright: the object whose __class__ raises is the hostile input under test; field_error
    # types path and messages as str
    err = field_error(bad, bad, codes=bad)  # pyright: ignore[reportArgumentType]
    assert err.field == "<unprintable _HostileClass>"
    assert err.messages == ["<unprintable _HostileClass>"]
    assert err.codes == ["<unprintable _HostileClass>"]
    # basedpyright: the object whose __class__ raises is the hostile input under test;
    # join_error_path types the parameter as str
    assert join_error_path(bad, "child") == "<unprintable _HostileClass>.child"  # pyright: ignore[reportArgumentType]


def test_validation_error_mapper_handles_leaf_with_message_collection_when_messages_raises():
    class _CollectionMessageError:
        @property
        def messages(self):
            raise RuntimeError("hostile messages")

        message = ["First message", "Second message"]

    errors = validation_error_to_field_errors(_as_validation_error(_CollectionMessageError()))
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


@pytest.mark.parametrize(
    ("prefix", "segment", "expected"),
    [
        ("", "name", "name"),
        ("items", "0", "items.0"),
        ("items.0", "name", "items.0.name"),
        ("items.0", "__all__", "items.0.__all__"),
    ],
)
def test_join_error_path_variations(prefix: str, segment: str, expected: str):
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
        @override
        def __bool__(self):
            raise RuntimeError("hostile code truthiness")

    class _Leaf:
        code = _HostileBoolCode(1)

    class _MalformedValidationError:
        error_dict = None
        error_list = (_Leaf(),)
        messages = ("msg",)

    (error,) = validation_error_to_field_errors(_as_validation_error(_MalformedValidationError()))

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
def test_validation_error_mapper_treats_a_text_atom_error_list_as_one_leaf(atom: object):
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

    (error,) = validation_error_to_field_errors(_as_validation_error(_TextAtomErrorList()))

    assert error.field == NON_FIELD_ERROR_KEY
    assert error.messages == ["whole-object"]
    assert error.codes == []


# ---------------------------------------------------------------------------
# Error keying: validator-side name -> GraphQL input name
# ---------------------------------------------------------------------------


def _keys(errors: list[FieldError]) -> list[tuple[str, list[str], list[str]]]:
    """``(field, path, messages)`` per leaf, in envelope order."""
    return [(fe.field, fe.path, fe.messages) for fe in errors]


def test_rekey_error_segment_never_rekeys_the_non_field_sentinel():
    """``"__all__"`` is checked before the map, so even a map entry for it is ignored."""
    key_map: ErrorKeyMap = {NON_FIELD_ERROR_KEY: ("hijacked", {"x": ("y", None)})}

    assert rekey_error_segment(NON_FIELD_ERROR_KEY, key_map) == (NON_FIELD_ERROR_KEY, {})
    (error,) = validation_error_to_field_errors(
        ValidationError({NON_FIELD_ERROR_KEY: ["model-wide"]}),
        key_map,
    )
    assert (error.field, error.path) == (NON_FIELD_ERROR_KEY, [])


def test_rekey_error_segment_keeps_an_unmapped_name_verbatim():
    """A name with no map entry (a field the input does not expose) keeps its own name."""
    key_map: ErrorKeyMap = {"category": ("categoryId", None)}

    assert rekey_error_segment("is_private", key_map) == ("is_private", {})
    assert rekey_error_segment("category", key_map) == ("categoryId", {})
    errors = validation_error_to_field_errors(
        ValidationError({"category": ["bad"], "is_private": ["hidden"]}),
        key_map,
    )
    assert _keys(errors) == [
        ("categoryId", ["categoryId"], ["bad"]),
        ("is_private", ["is_private"], ["hidden"]),
    ]


def test_validation_error_mapper_without_a_map_keys_every_name_verbatim():
    """``key_map=None`` (and an omitted map) keeps each ``error_dict`` name as raised."""
    exc = ValidationError({"category": ["bad"], NON_FIELD_ERROR_KEY: ["whole"]})

    assert _keys(validation_error_to_field_errors(exc, None)) == [
        ("category", ["category"], ["bad"]),
        (NON_FIELD_ERROR_KEY, [], ["whole"]),
    ]
    assert _keys(validation_error_to_field_errors(exc)) == _keys(
        validation_error_to_field_errors(exc, None),
    )


def test_validation_error_mapper_resolves_swapped_names_in_one_lookup():
    """Two inputs renamed onto each other's names each re-key exactly once."""
    key_map: ErrorKeyMap = {"name": ("description", None), "description": ("name", None)}
    errors = validation_error_to_field_errors(
        ValidationError({"name": ["on name"], "description": ["on description"]}),
        key_map,
    )
    assert _keys(errors) == [
        ("description", ["description"], ["on name"]),
        ("name", ["name"], ["on description"]),
    ]


def test_validation_error_mapper_lets_a_rename_share_an_unexposed_name():
    """A rename onto an unexposed field's name yields two errors on one key, never merged."""
    key_map: ErrorKeyMap = {"name": ("category", None)}
    errors = validation_error_to_field_errors(
        ValidationError({"name": ["on name"], "category": ["on the unexposed FK"]}),
        key_map,
    )
    assert _keys(errors) == [
        ("category", ["category"], ["on name"]),
        ("category", ["category"], ["on the unexposed FK"]),
    ]


def test_build_error_key_map_recurses_into_nested_specs():
    """A nested field carries its own level's map; a flat field carries ``None``."""
    child = (
        InputFieldSpec(
            input_attr="alt_branches",
            graphql_name="altBranches",
            target_name="alt_branches",
            kind=SCALAR,
        ),
    )
    specs = [
        InputFieldSpec(
            input_attr="category_id",
            graphql_name="categoryId",
            target_name="category",
            kind=RELATION_SINGLE,
        ),
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            # The map reads only ``nested_specs``; the serializer's nested kinds live
            # behind the DRF soft dependency, so a plain kind stands in.
            kind=SCALAR,
            nested_specs=child,
        ),
    ]
    key_map = build_error_key_map(specs)

    assert key_map == {
        "category": ("categoryId", None),
        "shelves": ("shelves", {"alt_branches": ("altBranches", None)}),
    }
    segment, child_map = rekey_error_segment("shelves", key_map)
    assert segment == "shelves"
    assert rekey_error_segment("alt_branches", child_map) == ("altBranches", {})


def test_build_error_key_map_keys_by_keys_of_at_every_depth():
    """``keys_of`` replaces ``target_name`` as the validator-side names, nested levels included."""
    child = (
        InputFieldSpec(
            input_attr="code",
            graphql_name="shelfCode",
            target_name="shelf_code",
            kind=SCALAR,
            source="code",
        ),
    )
    specs = [
        InputFieldSpec(
            input_attr="full_name",
            graphql_name="fullName",
            target_name="full_name",
            kind=SCALAR,
            source="name",
        ),
        InputFieldSpec(
            input_attr="is_private",
            graphql_name="isPrivate",
            target_name="is_private",
            kind=SCALAR,
        ),
        InputFieldSpec(
            input_attr="category_id",
            graphql_name="categoryId",
            target_name="category",
            kind=RELATION_SINGLE,
        ),
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            # The map reads only ``nested_specs``; the serializer's nested kinds live
            # behind the DRF soft dependency, so a plain kind stands in.
            kind=SCALAR,
            nested_specs=child,
        ),
    ]

    def model_names(spec: InputFieldSpec) -> tuple[str, ...]:
        name = spec.source or spec.target_name
        return (name, f"{name}_id") if spec.kind == RELATION_SINGLE else (name,)

    by_source = build_error_key_map(specs, keys_of=model_names)

    assert by_source == {
        "name": ("fullName", None),
        "is_private": ("isPrivate", None),
        "category": ("categoryId", None),
        "category_id": ("categoryId", None),
        "shelves": ("shelves", {"code": ("shelfCode", None)}),
    }
    assert "full_name" not in by_source


def test_build_error_key_map_never_lets_an_alias_displace_a_primary_name():
    """Every primary name is entered before any alias; an alias fills only an unclaimed name."""
    specs = [
        InputFieldSpec(
            input_attr="category",
            graphql_name="categoryId",
            target_name="category",
            kind=RELATION_SINGLE,
        ),
        InputFieldSpec(
            input_attr="category_ref",
            graphql_name="categoryRefId",
            target_name="category_ref",
            kind=RELATION_SINGLE,
            source="category_id",
        ),
    ]
    names = {"category": ("category", "category_id"), "category_ref": ("category_id", "category")}

    key_map = build_error_key_map(specs, keys_of=lambda spec: names[spec.target_name])

    assert key_map == {"category": ("categoryId", None), "category_id": ("categoryRefId", None)}


@pytest.mark.parametrize(
    ("model", "name", "expected"),
    [
        pytest.param(
            product_models.Item,
            "category",
            ("category", "category_id"),
            id="forward-fk",
        ),
        pytest.param(product_models.Item, "is_private", ("is_private",), id="scalar"),
        pytest.param(library_models.Shelf, "alt_branches", ("alt_branches",), id="m2m"),
        pytest.param(product_models.Category, "items", ("items",), id="reverse-relation"),
    ],
)
def test_model_field_error_names_add_a_forward_relation_attname(
    model: type[Model],
    name: str,
    expected: tuple[str, ...],
):
    """A forward relation answers to its ``attname`` too; every other field to its name alone."""
    assert model_field_error_names(model._meta.get_field(name)) == expected
